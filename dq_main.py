#!/usr/bin/env python3
"""
Data Quality Rule Validation System
Uses CrewAI with 3 specialized agents to validate DQ rules across MySQL systems
"""

import os
import sys
from crewai import Crew, Process
from validation_agents import (
    create_graph_data_retriever_agent,
    create_dq_rule_validator_agent, 
    create_report_generator_agent
)
from validation_tasks import (
    create_graph_data_retrieval_task,
    create_dq_validation_task,
    create_report_generation_task,
    create_mysql_connection_test_task
)
import logging

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")
    print("Or set OPENAI_API_KEY environment variable manually")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_environment():
    """Setup environment variables and check dependencies"""
    # Set OpenAI API key if not already set
    if not os.getenv('OPENAI_API_KEY'):
        print("Warning: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key for LLM functionality")
    
    # Check for required modules
    try:
        import mysql.connector
        logger.info("MySQL connector available")
    except ImportError:
        logger.error("mysql-connector-python not installed. Install with: pip install mysql-connector-python")
        return False
    
    try:
        import neo4j
        logger.info("Neo4j driver available")
    except ImportError:
        logger.error("neo4j driver not installed. Install with: pip install neo4j")
        return False
    
    return True

def run_dq_validation_workflow(uitids=None, limit=10, report_format="table"):
    """
    Run the complete DQ validation workflow
    
    Args:
        uitids: Comma-separated string of specific uitids to check
        limit: Maximum number of uitids to check if uitids not specified
        report_format: Format for the final report ("table", "summary", "csv")
    """
    logger.info("Starting DQ Rule Validation Workflow")
    
    # Create agents
    logger.info("Creating specialized agents...")
    graph_retriever_agent = create_graph_data_retriever_agent()
    dq_validator_agent = create_dq_rule_validator_agent()
    report_generator_agent = create_report_generator_agent()
    
    # Create tasks
    logger.info("Creating workflow tasks...")
    
    # Task 1: Retrieve graph data
    graph_retrieval_task = create_graph_data_retrieval_task(graph_retriever_agent)
    
    # Task 2: Test MySQL connections first
    connection_test_task = create_mysql_connection_test_task(dq_validator_agent)
    
    # Task 3: Validate DQ rules (will use context from graph retrieval)
    dq_validation_task = create_dq_validation_task(
        agent=dq_validator_agent,
        graph_data_context="{{graph_data_retrieval_task}}"
    )
    
    # Task 4: Generate report (will use context from validation)
    report_generation_task = create_report_generation_task(
        agent=report_generator_agent,
        validation_context="{{dq_validation_task}}"
    )
    
    # Create and configure crew
    logger.info("Assembling crew and starting execution...")
    crew = Crew(
        agents=[graph_retriever_agent, dq_validator_agent, report_generator_agent],
        tasks=[graph_retrieval_task, connection_test_task, dq_validation_task, report_generation_task],
        process=Process.sequential,
        verbose=True
    )
    
    # Execute the workflow
    try:
        logger.info("Executing DQ validation workflow...")
        result = crew.kickoff()
        
        logger.info("Workflow completed successfully!")
        return result
        
    except Exception as e:
        logger.error(f"Error during workflow execution: {str(e)}")
        return None

def run_connection_test_only():
    """Run only the MySQL connection test"""
    logger.info("Running MySQL connection test only...")
    
    dq_validator_agent = create_dq_rule_validator_agent()
    connection_test_task = create_mysql_connection_test_task(dq_validator_agent)
    
    crew = Crew(
        agents=[dq_validator_agent],
        tasks=[connection_test_task],
        process=Process.sequential,
        verbose=True
    )
    
    try:
        result = crew.kickoff()
        logger.info("Connection test completed!")
        return result
    except Exception as e:
        logger.error(f"Error during connection test: {str(e)}")
        return None

def run_graph_data_retrieval_only():
    """Run only the graph data retrieval"""
    logger.info("Running graph data retrieval only...")
    
    graph_retriever_agent = create_graph_data_retriever_agent()
    graph_retrieval_task = create_graph_data_retrieval_task(graph_retriever_agent)
    
    crew = Crew(
        agents=[graph_retriever_agent],
        tasks=[graph_retrieval_task],
        process=Process.sequential,
        verbose=True
    )
    
    try:
        result = crew.kickoff()
        logger.info("Graph data retrieval completed!")
        return result
    except Exception as e:
        logger.error(f"Error during graph data retrieval: {str(e)}")
        return None

def debug_neo4j_database():
    """Debug Neo4j database structure"""
    from neo4j_tools import Neo4jConnection
    
    neo4j_conn = Neo4jConnection()
    
    try:
        print("\n" + "="*80)
        print("NEO4J DATABASE STRUCTURE DEBUG")
        print("="*80)
        
        # Check what node types exist
        print("\n1. NODE TYPES IN DATABASE:")
        print("-" * 40)
        query = "MATCH (n) RETURN DISTINCT labels(n) as node_types, count(*) as count ORDER BY count DESC"
        results = neo4j_conn.execute_query(query)
        for result in results:
            print(f"  {result['node_types']}: {result['count']} nodes")
        
        # Check what relationship types exist
        print("\n2. RELATIONSHIP TYPES IN DATABASE:")
        print("-" * 40)
        query = "MATCH ()-[r]->() RETURN DISTINCT type(r) as relationship_type, count(*) as count ORDER BY count DESC"
        results = neo4j_conn.execute_query(query)
        for result in results:
            print(f"  {result['relationship_type']}: {result['count']} relationships")
        
        # Show any System nodes if they exist
        print("\n3. SYSTEM NODES (if any):")
        print("-" * 40)
        query = "MATCH (s:System) RETURN s ORDER BY s.name"
        results = neo4j_conn.execute_query(query)
        if results:
            for result in results:
                system = result['s']
                print(f"  System: {system.get('name', 'N/A')}")
        else:
            print("  No System nodes found in database")
        
        # Show CDE-DQRule relationships
        print("\n4. CDE-DQRULE RELATIONSHIPS:")
        print("-" * 40)
        query = """
        MATCH (cde:CDE)-[r:HAS_RULE]->(dq:DQRule) 
        RETURN cde.name as cde_name, dq.id as rule_id, dq.description as rule_desc
        ORDER BY cde_name, rule_id
        """
        results = neo4j_conn.execute_query(query)
        for result in results:
            print(f"  {result['cde_name']} -> {result['rule_id']}: {result['rule_desc']}")
        
        print("\n" + "="*80)
        print("DEBUG COMPLETED")
        print("="*80)
        
    except Exception as e:
        print(f"Error during debug: {str(e)}")
    finally:
        neo4j_conn.close()

def debug_mysql_data():
    """Debug MySQL database data"""
    from mysql_connections import MySQLConnectionManager
    from mysql_config import TRADE_TABLE_NAME
    
    mysql_manager = MySQLConnectionManager()
    
    # UITIDs mentioned by user with expected violations
    test_uitids = ['UIT-0001-ABC', 'UIT-0002-XYZ', 'UIT-0003-DEF']
    
    try:
        print("\n" + "="*100)
        print("MYSQL DATABASE DATA DEBUG")
        print("="*100)
        
        # Specific checks for the violations mentioned by user
        print(f"\n{'='*20} SPECIFIC VIOLATION CHECKS {'='*20}")
        
        print("\n1. UIT-0002-XYZ quantity in Trade System (should be -15):")
        result = mysql_manager.execute_query('Trade System', 
                                          f"SELECT uitid, quantity FROM {TRADE_TABLE_NAME} WHERE uitid = %s",
                                          ('UIT-0002-XYZ',))
        if result:
            print(f"   Found: quantity = {result[0]['quantity']}")
        else:
            print("   No record found")
        
        print("\n2. UIT-0003-DEF symbol in Settlement System (should be null):")
        result = mysql_manager.execute_query('Settlement System',
                                          f"SELECT uitid, symbol FROM {TRADE_TABLE_NAME} WHERE uitid = %s",
                                          ('UIT-0003-DEF',))
        if result:
            print(f"   Found: symbol = {result[0]['symbol']}")
        else:
            print("   No record found")
        
        print("\n3. UIT-0001-ABC trade_date in Reporting System (should be null):")
        result = mysql_manager.execute_query('Reporting System',
                                          f"SELECT uitid, trade_date FROM {TRADE_TABLE_NAME} WHERE uitid = %s",
                                          ('UIT-0001-ABC',))
        if result:
            print(f"   Found: trade_date = {result[0]['trade_date']}")
        else:
            print("   No record found")
        
        print("\n" + "="*100)
        print("MYSQL DATA DEBUG COMPLETED")
        print("="*100)
        
    except Exception as e:
        print(f"Error during MySQL debug: {str(e)}")
    finally:
        mysql_manager.close_all_connections()

def main():
    """Main function with command line interface"""
    if not setup_environment():
        sys.exit(1)
    
    print("\n" + "="*80)
    print("DATA QUALITY RULE VALIDATION SYSTEM")
    print("="*80)
    print("Choose an option:")
    print("1. Run full DQ validation workflow")
    print("2. Test MySQL connections only")
    print("3. Retrieve Neo4j graph data only")
    print("4. Exit")
    print("="*80)
    
    while True:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            print("\nRunning full DQ validation workflow...")
            
            # Get optional parameters
            uitids_input = input("Enter specific UITIDs (comma-separated) or press Enter for random sample: ").strip()
            uitids = uitids_input if uitids_input else None
            
            limit_input = input("Enter maximum number of UITIDs to check (default 10): ").strip()
            limit = int(limit_input) if limit_input.isdigit() else 10
            
            format_input = input("Enter report format (table/summary/csv, default table): ").strip().lower()
            report_format = format_input if format_input in ['table', 'summary', 'csv'] else 'table'
            
            result = run_dq_validation_workflow(uitids=uitids, limit=limit, report_format=report_format)
            
            if result:
                print("\n" + "="*80)
                print("WORKFLOW COMPLETED SUCCESSFULLY")
                print("="*80)
                print(result)
            else:
                print("\nWorkflow failed. Check logs for details.")
            break
            
        elif choice == '2':
            print("\nTesting MySQL connections...")
            result = run_connection_test_only()
            
            if result:
                print("\n" + "="*80)
                print("CONNECTION TEST COMPLETED")
                print("="*80)
                print(result)
            else:
                print("\nConnection test failed. Check logs for details.")
            break
            
        elif choice == '3':
            print("\nRetrieving Neo4j graph data...")
            result = run_graph_data_retrieval_only()
            
            if result:
                print("\n" + "="*80)
                print("GRAPH DATA RETRIEVAL COMPLETED")
                print("="*80)
                print(result)
            else:
                print("\nGraph data retrieval failed. Check logs for details.")
            break
            
        elif choice == '4':
            print("\nExiting...")
            break
            
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")

if __name__ == "__main__":
    main() 