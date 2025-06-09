from neo4j_tools import Neo4jConnection
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_connection():
    try:
        # Create connection
        conn = Neo4jConnection()
        
        # Test basic connectivity
        conn.connect()
        logger.info("Basic connection test successful")
        
        # Test database access with a simple query
        result = conn.execute_query("MATCH (n) RETURN count(n) as nodeCount")
        count = result[0]['nodeCount'] if result else 0
        logger.info(f"Database query successful. Total nodes in database: {count}")
        
        # Test database metadata
        version_result = conn.execute_query("CALL dbms.components() YIELD name, versions RETURN name, versions")
        if version_result:
            version_info = version_result[0]
            logger.info(f"Neo4j version: {version_info['versions'][0]}")
        
        # Close connection
        conn.close()
        logger.info("Connection test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("\nTesting connection to 'Data Lineage DBMS' database...")
    success = test_connection()
    if success:
        print("\nConnection test passed! ✓")
        sys.exit(0)
    else:
        print("\nConnection test failed! ✗")
        sys.exit(1) 