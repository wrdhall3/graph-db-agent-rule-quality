from crewai import Crew
from agents import create_agents
from tasks import create_translation_task, create_execution_task
import os
from dotenv import load_dotenv
import logging
from neo4j_tools import Neo4jConnection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def process_request(user_request: str, temperature: float = 0.5):
    """
    Process a natural language request to modify the Neo4j graph database.
    
    Args:
        user_request (str): Natural language request to modify or query the database
        temperature (float): Temperature setting for the LLM (0.0 to 1.0)
    
    Returns:
        dict: Results of the operation
    """
    try:
        # Create agents
        translator_agent, executor_agent = create_agents(temperature=temperature)
        
        # Create crew
        crew = Crew(
            agents=[translator_agent, executor_agent],
            tasks=[
                create_translation_task(translator_agent, user_request),
                create_execution_task(executor_agent, "{{ task_output }}")
            ],
            verbose=True
        )
        
        # Execute the crew's tasks
        result = crew.kickoff()
        return result
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {"error": str(e)}
    
def test_connection():
    """Test the Neo4j connection"""
    try:
        conn = Neo4jConnection()
        conn.connect()
        logger.info("Successfully connected to Neo4j")
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {str(e)}")
        return False

if __name__ == "__main__":
    # First test the connection
    if not test_connection():
        logger.error("Failed to connect to Neo4j. Please check your connection settings.")
        exit(1)
        
    # Example requests to test the system
    example_requests = [
        "Add a new CDE called 'Settlement Date' with data type DATE and connect it to all systems",
        "Create a new DQ rule that says Settlement Date must be after Trade Date and connect it to Settlement Date CDE",
        "Delete the DQ rule that checks if Settlement Date is after Trade Date",
        "Show me all DQ rules for Settlement Date",
        "Add a new CDE called 'Broker ID' with data type STRING and make it required for Trade System only"
    ]
    
    print("\nWelcome to the Graph DB Management System!")
    print("----------------------------------------")
    print("1. Use example requests")
    print("2. Enter your own request")
    choice = input("Enter your choice (1 or 2): ")
    
    if choice == "1":
        print("\nAvailable example requests:")
        for i, req in enumerate(example_requests, 1):
            print(f"{i}. {req}")
        req_num = int(input("\nEnter the number of the request you want to try: "))
        if 1 <= req_num <= len(example_requests):
            request = example_requests[req_num - 1]
        else:
            print("Invalid choice. Using first example.")
            request = example_requests[0]
    else:
        request = input("\nEnter your request: ")
    
    print(f"\nProcessing request: {request}")
    print("-" * 50)
    
    result = process_request(request)
    
    print("\nResult:")
    print("-" * 50)
    print(result) 