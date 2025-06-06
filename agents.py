from crewai import Agent
from neo4j_tools import Neo4jConnection
from langchain_openai import ChatOpenAI
from crewai.tools import BaseTool
import os
from dotenv import load_dotenv
from typing import Any
from pydantic import Field

# Load environment variables
load_dotenv()

class ExecuteQueryTool(BaseTool):
    name: str = "execute_query"
    description: str = "Execute a Cypher query on the Neo4j database"
    neo4j_conn: Neo4jConnection = Field(description="Neo4j connection instance")
    
    class Config:
        arbitrary_types_allowed = True
    
    def _run(self, query: str) -> Any:
        """Execute the provided Cypher query"""
        return self.neo4j_conn.execute_query(query)

class ValidateQueryTool(BaseTool):
    name: str = "validate_query"
    description: str = "Validate a Cypher query before execution"
    neo4j_conn: Neo4jConnection = Field(description="Neo4j connection instance")
    
    class Config:
        arbitrary_types_allowed = True
    
    def _run(self, query: str) -> bool:
        """Validate the provided Cypher query"""
        return self.neo4j_conn.validate_query(query)

class ListDQRulesTool(BaseTool):
    name: str = "list_dq_rules"
    description: str = "List all DQ rules in the database for debugging purposes"
    neo4j_conn: Neo4jConnection = Field(description="Neo4j connection instance")
    
    class Config:
        arbitrary_types_allowed = True
    
    def _run(self) -> Any:
        """List all DQ rules in the database"""
        return self.neo4j_conn.list_all_dq_rules()

class GenerateUniqueDQRuleIdTool(BaseTool):
    name: str = "generate_unique_id"
    description: str = "Generate a unique ID for a DQRule based on a base name"
    neo4j_conn: Neo4jConnection = Field(description="Neo4j connection instance")
    
    class Config:
        arbitrary_types_allowed = True
    
    def _run(self, base_name: str = "DQ_rule") -> str:
        """Generate a unique ID for a DQRule"""
        return self.neo4j_conn.generate_unique_dq_rule_id(base_name)

class FixCDEDeletionQueryTool(BaseTool):
    name: str = "fix_cde_deletion_query"
    description: str = "Generate a corrected CDE deletion query with proper variable scoping"
    neo4j_conn: Neo4jConnection = Field(description="Neo4j connection instance")
    
    class Config:
        arbitrary_types_allowed = True
    
    def _run(self, cde_name: str) -> str:
        """Generate a corrected CDE deletion query"""
        return self.neo4j_conn.fix_cde_deletion_query(cde_name)

def create_agents(temperature=0.5):
    # Initialize OpenAI LLM
    llm = ChatOpenAI(
        model="gpt-4-turbo-preview",
        temperature=temperature,
        api_key=os.getenv("OPENAI_API_KEY")
    )

    # Initialize Neo4j connection
    neo4j_conn = Neo4jConnection()

    # Create tools
    execute_tool = ExecuteQueryTool(neo4j_conn=neo4j_conn)
    validate_tool = ValidateQueryTool(neo4j_conn=neo4j_conn)
    list_rules_tool = ListDQRulesTool(neo4j_conn=neo4j_conn)
    generate_id_tool = GenerateUniqueDQRuleIdTool(neo4j_conn=neo4j_conn)
    fix_cde_deletion_tool = FixCDEDeletionQueryTool(neo4j_conn=neo4j_conn)

    translator = Agent(
        role="Natural Language to Cypher Translator",
        goal="Translate natural language requests into precise Neo4j Cypher queries",
        backstory="""You are an expert in translating natural language into Neo4j Cypher queries.
        You understand the graph database schema for Critical Data Elements (CDEs), Data Quality Rules (DQRules),
        and Systems. You create precise, safe, and efficient Cypher queries.""",
        llm=llm,
        tools=[validate_tool],  # Translator only needs to validate queries
        verbose=True,
        allow_delegation=False
    )

    executor = Agent(
        role="Cypher Query Executor",
        goal="Execute Cypher queries safely and provide clear feedback",
        backstory="""You are a Neo4j database expert responsible for executing Cypher queries.
        You validate queries before execution, handle errors gracefully, and provide clear feedback
        about the results. You understand the importance of data integrity and safe database operations.
        When deletion queries return no results, you investigate by listing existing data to help with troubleshooting.
        When ID conflicts occur during creation, you generate new unique IDs and retry the operation.
        When syntax errors occur, especially variable scoping issues, you can fix and retry the queries.""",
        llm=llm,
        tools=[execute_tool, validate_tool, list_rules_tool, generate_id_tool, fix_cde_deletion_tool],  # Executor needs all tools
        verbose=True,
        allow_delegation=False
    )

    return translator, executor

def get_schema_context():
    return """
    Graph Database Schema:
    
    Nodes:
    1. System
       - Properties: name (unique), dbType, dbTable, description
       - Example: {name: 'Trade System', dbType: 'MySQL', dbTable: 'trades', description: 'Origin system for trades'}
    
    2. CDE (Critical Data Element)
       - Properties: name (unique), description, dataType
       - Example: {name: 'Trade Date', description: 'Date when trade was executed', dataType: 'DATE'}
    
    3. DQRule (Data Quality Rule)
       - Properties: id (unique), description, ruleType
       - Example: {id: 'R1', description: 'Trade Date cannot be null', ruleType: 'NOT_NULL'}
    
    Relationships:
    1. HAS_CDE (System -> CDE)
       - Properties: columnName, isRequired
       - Example: (System)-[:HAS_CDE {columnName: 'trade_date', isRequired: true}]->(CDE)
    
    2. HAS_RULE (CDE -> DQRule)
       - No properties
       - Example: (CDE)-[:HAS_RULE]->(DQRule)
    """ 