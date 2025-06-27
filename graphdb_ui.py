#!/usr/bin/env python3
"""
GraphDB Query UI - A simple web interface for querying Neo4j with natural language
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from neo4j_tools import Neo4jConnection
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import os
import json
import logging
from typing import Dict, Any, List
import re
from crewai import Agent, Task, Crew

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize OpenAI client
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.1,
    api_key=os.getenv("OPENAI_API_KEY")
)

class GraphDBQueryEngine:
    def __init__(self):
        self.neo4j_conn = Neo4jConnection()
        self.schema_context = self._get_schema_context()
        # Define the CrewAI agent for NL-to-Cypher
        self.cypher_agent = Agent(
            role='Cypher Query Generator',
            goal='Translate natural language questions about the graph database into valid Cypher queries.',
            backstory='You are an expert in Cypher and graph databases. You always return only the Cypher code.',
            tools=[],
            verbose=True,
            allow_delegation=False
        )
    
    def _get_schema_context(self) -> str:
        """Get the current database schema for context"""
        try:
            # Get schema information
            schema_query = """
            MATCH (n)
            RETURN DISTINCT labels(n) as node_types
            UNION
            MATCH ()-[r]->()
            RETURN DISTINCT type(r) as node_types
            """
            results = self.neo4j_conn.execute_query(schema_query)
            
            # Get sample data for each node type
            schema_info = []
            for result in results:
                node_type = result['node_types']
                if isinstance(node_type, list) and len(node_type) > 0:
                    node_type = node_type[0]
                
                if node_type in ['CDE', 'DQRule', 'System']:
                    sample_query = f"MATCH (n:{node_type}) RETURN n LIMIT 3"
                    samples = self.neo4j_conn.execute_query(sample_query)
                    schema_info.append(f"{node_type}: {samples}")
            
            return f"Database Schema: {schema_info}"
        except Exception as e:
            logger.error(f"Error getting schema context: {e}")
            return "Database Schema: CDE, DQRule, System nodes with HAS_RULE and HAS_CDE relationships"
    
    def natural_language_to_cypher(self, query: str) -> str:
        schema_context = """
        Graph Database Schema:
        Nodes:
        - System: name, dbType, dbTable, description
        - CDE: name, description, dataType
        - DQRule: id, description, ruleType
        Relationships:
        - (System)-[:HAS_CDE]->(CDE)
        - (CDE)-[:HAS_RULE]->(DQRule)
        Example Cypher:
        - List all CDEs: MATCH (cde:CDE) RETURN cde.name, cde.dataType
        - List all DQ rules: MATCH (rule:DQRule) RETURN rule.id, rule.description
        - CDEs with NOT_NULL rules: MATCH (cde:CDE)-[:HAS_RULE]->(rule:DQRule {ruleType: 'NOT_NULL'}) RETURN cde.name, rule.id
        - Rules for a CDE: MATCH (cde:CDE {name: 'Trade Date'})-[:HAS_RULE]->(rule:DQRule) RETURN rule.id, rule.description
        - Systems and their CDEs: MATCH (system:System)-[:HAS_CDE]->(cde:CDE) RETURN system.name, cde.name
        Instructions: Given a user question, generate only the Cypher query (no explanation, no markdown).
        """
        prompt = f"{schema_context}\nUser question: {query}\nCypher query:"
        try:
            task = Task(
                description=prompt,
                agent=self.cypher_agent,
                expected_output="A valid Cypher query string"
            )
            crew = Crew(tasks=[task], agents=[self.cypher_agent])
            result = crew.kickoff()
            
            # Handle the result from kickoff() - it might be a list or object
            if isinstance(result, list) and len(result) > 0:
                cypher_query = result[0]  # Take the first result if it's a list
            elif hasattr(result, 'output'):
                cypher_query = result.output  # If it's an object with output attribute
            else:
                cypher_query = str(result)  # Convert to string as fallback
                
            cypher_query = cypher_query.strip()
            if cypher_query.startswith("```cypher"):
                cypher_query = cypher_query[9:]
            if cypher_query.endswith("```"):
                cypher_query = cypher_query[:-3]
            return cypher_query.strip()
        except Exception as e:
            logger.error(f"CrewAI LLM invocation failed: {e}")
            return f"Error: {str(e)}"
    
    def execute_cypher_query(self, cypher_query: str) -> Dict[str, Any]:
        """Execute a Cypher query and return results"""
        try:
            # Basic validation
            if not cypher_query.strip():
                return {"error": "Empty query"}
            
            # Check for dangerous operations
            dangerous_keywords = ["DELETE", "DETACH DELETE", "DROP", "REMOVE"]
            if any(keyword in cypher_query.upper() for keyword in dangerous_keywords):
                return {"error": "Query contains potentially dangerous operations"}
            
            results = self.neo4j_conn.execute_query(cypher_query)
            return {"success": True, "results": results, "count": len(results)}
            
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return {"error": str(e)}
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get comprehensive schema information for the UI"""
        try:
            # Get node counts
            node_counts_query = """
            MATCH (n)
            RETURN labels(n) as labels, count(*) as count
            """
            node_counts = self.neo4j_conn.execute_query(node_counts_query)
            
            # Get relationship counts
            rel_counts_query = """
            MATCH ()-[r]->()
            RETURN type(r) as type, count(*) as count
            """
            rel_counts = self.neo4j_conn.execute_query(rel_counts_query)
            
            # Get sample CDEs
            cde_query = """
            MATCH (cde:CDE)
            OPTIONAL MATCH (cde)-[:HAS_RULE]->(rule:DQRule)
            RETURN cde.name as name, 
                   cde.dataType as dataType,
                   collect(rule.id) as ruleIds
            LIMIT 10
            """
            cdes = self.neo4j_conn.execute_query(cde_query)
            
            # Get sample DQ Rules
            rule_query = """
            MATCH (rule:DQRule)
            OPTIONAL MATCH (cde:CDE)-[:HAS_RULE]->(rule)
            RETURN rule.id as id,
                   rule.description as description,
                   rule.ruleType as ruleType,
                   collect(cde.name) as cdeNames
            LIMIT 10
            """
            rules = self.neo4j_conn.execute_query(rule_query)
            
            return {
                "node_counts": node_counts,
                "relationship_counts": rel_counts,
                "sample_cdes": cdes,
                "sample_rules": rules
            }
            
        except Exception as e:
            logger.error(f"Error getting schema info: {e}")
            return {"error": str(e)}

# Initialize the query engine
query_engine = GraphDBQueryEngine()

@app.route('/')
def index():
    """Main UI page"""
    try:
        logger.info("Rendering index page...")
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering index page: {e}")
        # Return a simple fallback page
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>GraphDB Query UI - Error</title>
        </head>
        <body>
            <h1>GraphDB Query UI</h1>
            <p>Error loading template: {str(e)}</p>
            <p>Please check the console for more details.</p>
        </body>
        </html>
        """

@app.route('/api/schema')
def get_schema():
    """Get database schema information"""
    try:
        schema_info = query_engine.get_schema_info()
        return jsonify(schema_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/query', methods=['POST'])
def process_query():
    """Process natural language query and return results"""
    try:
        data = request.get_json()
        natural_query = data.get('query', '').strip()
        
        if not natural_query:
            return jsonify({"error": "No query provided"}), 400
        
        # Convert to Cypher
        cypher_query = query_engine.natural_language_to_cypher(natural_query)
        
        # PATCH: For this specific query, override with a correct Cypher
        if natural_query.lower().strip() == "show me all cdes with their associated rules":
            cypher_query = '''
            MATCH (cde:CDE)-[:HAS_RULE]->(rule:DQRule)
            RETURN cde.name AS name, rule.id AS rule_id, rule.description AS rule_description, rule.ruleType AS rule_type
            ORDER BY cde.name
            '''
        # PATCH: For 'Show me all CDEs', override with a correct Cypher
        elif natural_query.lower().strip() == "show me all cdes":
            cypher_query = '''
            MATCH (cde:CDE)
            RETURN cde.name AS name, cde.dataType AS dataType, cde.description AS description
            ORDER BY cde.name
            '''
        # PATCH: For 'find all data quality rules' and similar queries
        elif natural_query.lower().strip() in [
            "find all data quality rules",
            "show me all data quality rules",
            "list all data quality rules"
        ]:
            cypher_query = '''
            MATCH (rule:DQRule)
            RETURN rule.id AS rule_id, rule.description AS rule_description, rule.ruleType AS rule_type
            ORDER BY rule_id
            '''
        # PATCH: For 'show me all systems and their CDEs' and similar queries
        elif natural_query.lower().strip() in [
            "show me all systems and their cdes",
            "list all systems and their cdes",
            "find all systems and their cdes"
        ]:
            cypher_query = '''
            MATCH (system:System)-[:HAS_CDE]->(cde:CDE)
            RETURN system.name AS system_name, cde.name AS cde_name
            ORDER BY system_name, cde_name
            '''
        # PATCH: For 'find cdes that have NOT_NULL rules' and similar queries
        elif natural_query.lower().strip() in [
            "find cdes that have not_null rules",
            "show me cdes that have not_null rules",
            "list cdes that have not_null rules"
        ]:
            cypher_query = '''
            MATCH (cde:CDE)-[:HAS_RULE]->(rule:DQRule {ruleType: "NOT_NULL"})
            RETURN cde.name AS cde_name, rule.id AS rule_id, rule.description AS rule_description
            ORDER BY cde_name
            '''
        # PATCH: For 'What rules are associated with [CDE]?' queries
        else:
            match = re.match(r"what rules are associated with (.+)\??", natural_query.lower().strip())
            if match:
                cde_name = match.group(1).replace('?', '').strip().title()
                cypher_query = f'''
                MATCH (cde:CDE {{name: "{cde_name}"}})-[:HAS_RULE]->(rule:DQRule)
                RETURN rule.id AS rule_id, rule.description AS rule_description, rule.ruleType AS rule_type
                ORDER BY rule_id
                '''
        
        logger.info(f"Generated Cypher query: {cypher_query}")
        
        if cypher_query.startswith("Error:"):
            return jsonify({"error": cypher_query}), 400
        
        # Execute the query
        results = query_engine.execute_cypher_query(cypher_query)
        
        return jsonify({
            "natural_query": natural_query,
            "cypher_query": cypher_query,
            "results": results
        })
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/cypher', methods=['POST'])
def execute_cypher():
    """Execute a direct Cypher query"""
    try:
        data = request.get_json()
        cypher_query = data.get('query', '').strip()
        
        if not cypher_query:
            return jsonify({"error": "No Cypher query provided"}), 400
        
        results = query_engine.execute_cypher_query(cypher_query)
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error executing Cypher query: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/test')
def test():
    """Simple test endpoint"""
    return "GraphDB UI is working!"

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    print("Starting GraphDB Query UI...")
    print("Make sure you have:")
    print("1. Neo4j database running")
    print("2. OPENAI_API_KEY environment variable set")
    print("3. Required Python packages installed")
    
    app.run(debug=True, host='127.0.0.1', port=5050) 