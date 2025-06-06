from neo4j import GraphDatabase
from typing import Dict, Any
import logging
from datetime import datetime
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Neo4jConnection:
    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "testtest"):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self.database = "neo4j"  # Using the default database name shown in screenshot

    def connect(self):
        if not self.driver:
            try:
                self.driver = GraphDatabase.driver(
                    self.uri,
                    auth=(self.user, self.password)
                )
                # Test the connection and database existence
                with self.driver.session(database=self.database) as session:
                    result = session.run("RETURN 1 as test")
                    result.single()  # Consume the result
                logger.info(f"Successfully connected to Neo4j database '{self.database}' in project 'Data Lineage DBMS'")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j database '{self.database}': {str(e)}")
                raise
        return self.driver

    def close(self):
        if self.driver:
            self.driver.close()
            self.driver = None
            logger.info("Neo4j connection closed")

    def execute_query(self, query: str, parameters: Dict = None) -> Dict[str, Any]:
        """Execute a Cypher query and return the results"""
        if parameters is None:
            parameters = {}
            
        driver = self.connect()
        try:
            with driver.session(database=self.database) as session:
                result = session.run(query, parameters)
                records = [dict(record) for record in result]  # Convert records to dictionaries
                logger.info(f"Query executed successfully. Returned {len(records)} records.")
                return records
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            logger.error(f"Query was: {query}")
            raise

    def validate_query(self, query: str) -> bool:
        """Basic validation of Cypher query including variable scoping"""
        # Add basic validation rules
        if not query.strip():
            return False
        
        dangerous_keywords = ["DELETE", "DETACH DELETE", "DROP", "REMOVE"]
        if any(keyword in query.upper() for keyword in dangerous_keywords):
            # Log warning but don't block - these are valid operations in our context
            logger.warning(f"Query contains potentially dangerous operations: {query}")
        
        # Check for potential variable scoping issues
        if "WITH" in query.upper() and "DELETE" in query.upper():
            logger.warning("Query contains WITH and DELETE - check variable scoping carefully")
            
            # Look for common patterns that cause variable scoping issues
            if re.search(r'WITH.*collect\([^)]+\).*DELETE.*[^,\s]+', query, re.IGNORECASE):
                logger.warning("Potential variable scoping issue: variables collected in WITH may not be available for DELETE")
                
        return True

    def list_all_dq_rules(self) -> Dict[str, Any]:
        """Debug method to list all DQ rules in the database"""
        query = "MATCH (dqRule:DQRule) RETURN dqRule.id as id, dqRule.description as description, dqRule.ruleType as ruleType ORDER BY dqRule.id"
        try:
            results = self.execute_query(query)
            logger.info(f"Found {len(results)} DQ rules in database")
            for rule in results:
                logger.info(f"  - ID: {rule.get('id')}, Description: '{rule.get('description')}', Type: {rule.get('ruleType')}")
            return results
        except Exception as e:
            logger.error(f"Failed to list DQ rules: {str(e)}")
            return []

    def generate_unique_dq_rule_id(self, base_name: str = "DQ_rule") -> str:
        """Generate a unique ID for a DQRule based on existing IDs"""
        try:
            existing_rules = self.list_all_dq_rules()
            existing_ids = {rule.get('id') for rule in existing_rules}
            
            # Try descriptive name first
            if base_name not in existing_ids:
                return base_name
            
            # Try with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            timestamp_id = f"{base_name}_{timestamp}"
            if timestamp_id not in existing_ids:
                return timestamp_id
            
            # Fall back to numbered sequence
            counter = 1
            while f"{base_name}_{counter}" in existing_ids:
                counter += 1
            
            return f"{base_name}_{counter}"
            
        except Exception as e:
            logger.error(f"Failed to generate unique ID: {str(e)}")
            # Fallback to timestamp-based ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"{base_name}_{timestamp}"

    def fix_cde_deletion_query(self, cde_name: str) -> str:
        """Generate a corrected CDE deletion query with proper variable scoping"""
        return f"""
        MATCH (cde:CDE {{name: '{cde_name}'}})
        OPTIONAL MATCH (cde)-[:HAS_RULE]->(dqRule:DQRule)
        WITH cde.name as deletedCDEName, collect(dqRule.id) as deletedDQRuleIds
        MATCH (cde:CDE {{name: '{cde_name}'}})
        OPTIONAL MATCH (cde)-[:HAS_RULE]->(dqRule:DQRule)
        DETACH DELETE cde, dqRule
        RETURN deletedCDEName, deletedDQRuleIds, 'DELETED' as status
        """.strip() 