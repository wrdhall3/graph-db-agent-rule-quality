from crewai import Task
from typing import List
from agents import get_schema_context

def create_translation_task(translator_agent, user_request: str) -> Task:
    return Task(
        description=f"""
        Translate the following natural language request into a Neo4j Cypher query:
        
        USER REQUEST:
        {user_request}
        
        SCHEMA INFORMATION:
        {get_schema_context()}
        
        REQUIREMENTS:
        1. If the request involves deletion:
           - Use flexible pattern matching (CONTAINS, starts with, etc.) to find nodes
           - For deletion queries, first capture the nodes to be deleted, then delete them
           - Return information about what was deleted for verification
           - Handle variable scoping properly when using WITH clauses
        2. For new nodes, ensure unique constraints are respected:
           - For DQRule nodes, use timestamp-based IDs like 'DQ_YYYYMMDD_HHMMSS' format
           - Or use descriptive IDs that are unlikely to conflict
        3. For relationships, ensure they follow the schema
        4. Return a SINGLE complete Cypher query that accomplishes the entire request
        
        IMPORTANT:
        - For deletions, use flexible text matching to find nodes first
        - Use DETACH DELETE when deleting nodes that might have relationships
        - For DQRule deletion requests involving "Settlement Date" and "Trade Date", use this pattern:
          MATCH (dqRule:DQRule) WHERE dqRule.description CONTAINS 'Settlement Date' AND dqRule.description CONTAINS 'Trade Date'
          WITH dqRule, dqRule.id as deletedId, dqRule.description as deletedDesc, dqRule.ruleType as deletedType
          DETACH DELETE dqRule
          RETURN deletedId, deletedDesc, deletedType, 'DELETED' as status
        - For CDE deletion requests, use this pattern:
          MATCH (cde:CDE {{name: 'CDE Name'}})
          OPTIONAL MATCH (cde)-[:HAS_RULE]->(dqRule:DQRule)
          WITH cde.name as deletedCDEName, collect(dqRule.id) as deletedDQRuleIds
          MATCH (cde:CDE {{name: 'CDE Name'}})
          OPTIONAL MATCH (cde)-[:HAS_RULE]->(dqRule:DQRule)
          DETACH DELETE cde, dqRule
          RETURN deletedCDEName, deletedDQRuleIds, 'DELETED' as status
        - For creation operations, use a single query with proper variable scoping
        - When creating nodes and relationships together, do it in one query
        - For DQRule creation, use unique IDs like 'DQ_settlement_after_trade' or similar descriptive names
        - Example for creating DQRule and connecting to CDE:
          MATCH (cde:CDE {{name: 'Settlement Date'}})
          CREATE (dqRule:DQRule {{id: 'DQ_settlement_after_trade', description: 'Settlement Date must be after Trade Date', ruleType: 'DATE_COMPARISON'}})
          CREATE (cde)-[:HAS_RULE]->(dqRule)
          RETURN dqRule, cde
        """,
        agent=translator_agent,
        expected_output="A single complete Cypher query that safely accomplishes the user's request"
    )

def create_execution_task(executor_agent, cypher_query: str) -> Task:
    return Task(
        description=f"""
        Execute and validate the following Cypher query:
        
        QUERY:
        {cypher_query}
        
        SCHEMA INFORMATION:
        {get_schema_context()}
        
        REQUIREMENTS:
        1. Validate the query before execution
        2. Execute the query safely
        3. Handle constraint validation failures by:
           - If ID conflict occurs, list existing DQ rules to understand the conflict
           - Suggest alternative unique IDs for the new rule
           - Attempt execution with a corrected unique ID
        4. Handle syntax errors by:
           - Identify the specific issue (e.g., variable scoping, syntax problems)
           - Provide a corrected query if possible
           - Re-execute with the corrected query
        5. For deletion queries:
           - If the query returns results with 'DELETED' status, report successful deletion
           - If the query returns empty results, investigate what rules actually exist
           - Use the list_dq_rules tool to show existing rules when deletion finds nothing
        6. Provide a clear summary of:
           - What changes were made
           - Any errors encountered
           - Verification of the changes
        
        If there are constraint validation errors:
        1. Use list_dq_rules tool to see existing IDs
        2. Generate a new unique ID and retry the operation
        3. Report both the error and the successful retry
        
        If there are syntax errors:
        1. Analyze the error message to understand the issue
        2. Provide a corrected query
        3. Execute the corrected query
        4. Report the correction that was made
        
        If there are other errors:
        1. Explain the error in clear terms
        2. Suggest how to fix the error
        3. If possible, provide a corrected query
        
        If successful:
        1. For deletions: Report exactly what was deleted based on the returned data
        2. For creations: Verify the changes with a follow-up query
        3. Provide a summary of the affected nodes/relationships
        4. Show the final state of what was created/modified
        
        If deletion returns no results:
        1. Use the list_dq_rules tool to show what rules actually exist
        2. Suggest the correct description patterns to use for deletion
        """,
        agent=executor_agent,
        expected_output="A dictionary containing the execution results, any errors encountered, and verification of changes"
    ) 