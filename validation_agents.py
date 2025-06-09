from crewai import Agent
from dq_validation_tools import (
    graph_data_retriever_tool, 
    mysql_validation_tool, 
    mysql_connection_test_tool,
    dq_report_generator_tool
)

def create_graph_data_retriever_agent():
    """Create the Graph Data Retriever Agent"""
    return Agent(
        role='Graph Database Data Retriever',
        goal='Retrieve Critical Data Elements (CDEs) and Data Quality Rules from Neo4j graph database',
        backstory="""You are a specialized data analyst focused on extracting structured information 
        from graph databases. Your expertise lies in understanding the relationships between CDEs, 
        DQ rules, and systems stored in Neo4j. You can efficiently query the graph database to 
        gather all necessary information for data quality validation processes.""",
        tools=[graph_data_retriever_tool],
        verbose=True,
        allow_delegation=False
    )

def create_dq_rule_validator_agent():
    """Create the DQ Rule Validator Agent"""
    return Agent(
        role='Data Quality Rule Validator',
        goal='Validate data quality rules against MySQL databases across Trade, Settlement, and Reporting systems',
        backstory="""You are a data quality specialist with deep expertise in validating business 
        rules across multiple database systems. You understand various types of data quality checks 
        including null validations, range checks, and format validations. You can efficiently 
        connect to multiple MySQL databases and perform systematic validation of data quality rules 
        across different trade processing systems.""",
        tools=[mysql_validation_tool, mysql_connection_test_tool],
        verbose=True,
        allow_delegation=False
    )

def create_report_generator_agent():
    """Create the Report Generator Agent"""
    return Agent(
        role='Data Quality Report Generator',
        goal='Generate comprehensive, well-formatted reports of data quality validation results',
        backstory="""You are a business intelligence specialist who excels at transforming complex 
        data validation results into clear, actionable reports. You understand the needs of both 
        technical teams and business stakeholders, and can format information in various ways 
        including tables, summaries, and CSV exports for further analysis.""",
        tools=[],
        verbose=True,
        allow_delegation=False
    ) 