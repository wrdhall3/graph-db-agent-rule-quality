from neo4j import GraphDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connection details
URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "testtest"

def test_connection():
    try:
        # Connect without specifying database
        driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
        
        # Test connection
        driver.verify_connectivity()
        logger.info("Successfully connected to Neo4j server")
        
        # List available databases
        with driver.session(database="system") as session:
            result = session.run("SHOW DATABASES")
            print("\nAvailable databases:")
            for record in result:
                print(f"- {record['name']}: {record['currentStatus']}")
                
        driver.close()
        return True
        
    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("\nTesting Neo4j connection and listing databases...")
    success = test_connection()
    if not success:
        print("\nConnection test failed! ✗") 