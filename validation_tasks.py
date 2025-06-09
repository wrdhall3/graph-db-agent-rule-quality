from crewai import Task

def create_graph_data_retrieval_task(agent):
    """Create task for retrieving CDEs and DQ rules from Neo4j"""
    return Task(
        description="""Retrieve all Critical Data Elements (CDEs) and their associated Data Quality Rules 
        from the Neo4j graph database. Include the following information:
        
        1. CDE names and their corresponding MySQL column names
        2. Associated DQ rules with their types and descriptions
        3. Systems where each CDE is used (Trade System, Settlement System, Reporting System)
        
        Focus on CDEs that have DQ rules associated with them. Return the data in a structured format 
        that can be easily processed by the validation agent.""",
        agent=agent,
        expected_output="""A structured list of CDEs with their DQ rules and system associations. 
        Each CDE should include:
        - CDE name
        - MySQL column name
        - List of associated DQ rules (ID, description, type)
        - List of systems where the CDE is used"""
    )

def create_dq_validation_task(agent, graph_data_context):
    """Create task for validating DQ rules against MySQL databases"""
    return Task(
        description=f"""CRITICAL MISSION: Validate EVERY SINGLE DQ rule for ALL CDEs against MySQL databases.

        Graph data context: {graph_data_context}

        MANDATORY REQUIREMENTS:
        1. You MUST validate ALL CDEs found in the graph data - DO NOT skip any
        2. You MUST use these specific UITIDs: UIT-0001-ABC, UIT-0002-XYZ, UIT-0003-DEF
        3. You MUST check each CDE against all three systems: Trade System, Settlement System, Reporting System

        STEP-BY-STEP EXECUTION (FOLLOW EXACTLY):
        
        Step 1: Parse the graph data and identify ALL CDEs
        Expected CDEs: Price, Quantity, Side, Symbol, Trade Date, uitid (verify you see all 6)
        
        Step 2: For EACH of the 6 CDEs, make an individual mysql_validation tool call:
        
        CDE 1 - uitid:
        mysql_validation(cde_name="uitid", cde_column="uitid", rule_type="NOT_NULL", rule_description="uitid cannot be null", uitids="UIT-0001-ABC,UIT-0002-XYZ,UIT-0003-DEF")
        
        CDE 2 - Price:
        mysql_validation(cde_name="Price", cde_column="price", rule_type="POSITIVE_VALUE", rule_description="Price must be positive", uitids="UIT-0001-ABC,UIT-0002-XYZ,UIT-0003-DEF")
        
        CDE 3 - Quantity:
        mysql_validation(cde_name="Quantity", cde_column="quantity", rule_type="POSITIVE_VALUE", rule_description="Quantity must be positive", uitids="UIT-0001-ABC,UIT-0002-XYZ,UIT-0003-DEF")
        
        CDE 4 - Side:
        mysql_validation(cde_name="Side", cde_column="side", rule_type="ENUM_VALUE", rule_description="Side must be either BUY or SELL", uitids="UIT-0001-ABC,UIT-0002-XYZ,UIT-0003-DEF")
        
        CDE 5 - Symbol:
        mysql_validation(cde_name="Symbol", cde_column="symbol", rule_type="NOT_NULL", rule_description="Symbol must not be null", uitids="UIT-0001-ABC,UIT-0002-XYZ,UIT-0003-DEF")
        
        CDE 6 - Trade Date:
        mysql_validation(cde_name="Trade Date", cde_column="trade_date", rule_type="NOT_NULL", rule_description="Trade Date cannot be null", uitids="UIT-0001-ABC,UIT-0002-XYZ,UIT-0003-DEF")
        
        Step 3: Compile ALL 6 validation results into your final response

        EXPECTED VIOLATIONS (verify you find EXACTLY these 3):
        1. UIT-0002-XYZ: Quantity = -15 (negative) in Trade System ONLY
        2. UIT-0003-DEF: Symbol = null in Settlement System ONLY  
        3. UIT-0001-ABC: Trade Date = null in Reporting System ONLY
        
        CRITICAL: Each violation should occur in exactly ONE system, not multiple systems

        CRITICAL VALIDATION CHECKS:
        - You MUST call mysql_validation exactly 6 times (once per CDE)
        - You MUST include results for all 6 CDEs in your final response
        - You MUST find exactly 3 violations total
        - If you don't find 3 violations, something is wrong - investigate and retry
        
        DEBUGGING:
        - Start your response with: "EXECUTING VALIDATION FOR 6 CDEs..."
        - After each mysql_validation call, state: "CDE [name] validation completed"
        - End with: "ALL 6 CDEs VALIDATED SUCCESSFULLY"
        
        FAILURE CONDITIONS:
        - If you validate fewer than 6 CDEs, you have FAILED
        - If you only return results for the last CDE, you have FAILED  
        - If you don't find the expected 3 violations, you have FAILED""",
        agent=agent,
        expected_output="""COMPLETE validation results for ALL 6 CDEs.

        Your response MUST start with: "EXECUTING VALIDATION FOR 6 CDEs..."

        **VALIDATION SUMMARY**
        - Total CDEs validated: 6
        - Total violations found: 3 (must be exactly 3)
        - UITIDs checked: UIT-0001-ABC, UIT-0002-XYZ, UIT-0003-DEF

        **DETAILED RESULTS BY CDE**
        For each of the 6 CDEs (Price, Quantity, Side, Symbol, Trade Date, uitid):
        1. CDE Name: [name]
        2. DQ Rule: [description]  
        3. Validation Results:
           - UIT-0001-ABC: Trade System [OK/VIOLATION], Settlement System [OK/VIOLATION], Reporting System [OK/VIOLATION]
           - UIT-0002-XYZ: Trade System [OK/VIOLATION], Settlement System [OK/VIOLATION], Reporting System [OK/VIOLATION]
           - UIT-0003-DEF: Trade System [OK/VIOLATION], Settlement System [OK/VIOLATION], Reporting System [OK/VIOLATION]

        **VIOLATIONS FOUND**
        Must list exactly 3 violations:
        - Quantity: UIT-0002-XYZ - Trade System - negative value (-15)
        - Symbol: UIT-0003-DEF - Settlement System - null value
        - Trade Date: UIT-0001-ABC - Reporting System - null value

        Your response MUST end with: "ALL 6 CDEs VALIDATED SUCCESSFULLY"

        CRITICAL: Your response must include results for ALL 6 CDEs, not just the last one processed."""
    )

def create_report_generation_task(agent, validation_context):
    """Create task for generating DQ validation reports"""
    return Task(
        description=f"""Generate a comprehensive Data Quality validation report in TABLE FORMAT based on the 
        validation results provided.

        Validation context: {validation_context}
        
        CRITICAL REQUIREMENTS:
        - The validation context should contain results for ALL 6 CDEs: uitid, Price, Quantity, Side, Symbol, Trade Date
        - There should be exactly 3 violations found across all CDEs
        - DO NOT use any tools - create the report directly in your response
        - Output MUST be in TABLE FORMAT, NOT JSON format
        
        EXPECTED VIOLATIONS TO PROCESS:
        1. Quantity: UIT-0002-XYZ in Trade System (negative value)
        2. Symbol: UIT-0003-DEF in Settlement System (null value)  
        3. Trade Date: UIT-0001-ABC in Reporting System (null value)
        
        Create a final report with this EXACT structure:

        ## EXECUTIVE SUMMARY
        - Total CDEs validated: 6
        - Total violations found: 3
        - Overall violation rate: 16.7% (3 violations out of 18 total validations)

        ## DETAILED VALIDATION RESULTS
        
        | CDE | DQ Rule Description | uitid | Trade System | Settlement System | Reporting System |
        |-----|---------------------|-------|--------------|-------------------|------------------|
        [Create 18 rows: 6 CDEs × 3 UITIDs each]
        
        Where system columns show:
        - "VIOLATION" if rule is violated  
        - "OK" if rule is satisfied
        - Never show "N/A" - all CDEs should be validated in all systems
        
        ## VIOLATIONS SUMMARY
        Exactly 3 violations:
        - Quantity: UIT-0002-XYZ - Trade System - negative value (-15)
        - Symbol: UIT-0003-DEF - Settlement System - null value
        - Trade Date: UIT-0001-ABC - Reporting System - null value
        
        ## SYSTEM ANALYSIS  
        - Trade System: 1/3 (33%) - UIT-0002-XYZ Quantity violation
        - Settlement System: 1/3 (33%) - UIT-0003-DEF Symbol violation
        - Reporting System: 1/3 (33%) - UIT-0001-ABC Trade Date violation
        
        VALIDATION CHECKS:
        - Verify your table has exactly 18 rows (6 CDEs × 3 UITIDs)
        - Verify you show exactly 3 VIOLATION entries and 15 OK entries
        - Verify no N/A entries appear in the table
        - Verify system analysis shows 1 violation per system
        
        CRITICAL VIOLATION MAPPING CHECK - MUST BE EXACT:
        The table must show EXACTLY these 3 VIOLATION entries and 15 OK entries:
        
        1. Row "Quantity | Quantity must be positive | UIT-0002-XYZ": VIOLATION | OK | OK
        2. Row "Symbol | Symbol must not be null | UIT-0003-DEF": OK | VIOLATION | OK  
        3. Row "Trade Date | Trade Date cannot be null | UIT-0001-ABC": OK | OK | VIOLATION
        
        ALL other 15 rows must show: OK | OK | OK
        
        COMMON ERROR TO AVOID:
        - Do NOT show Symbol violation in Trade System for UIT-0003-DEF
        - Do NOT show multiple violations for the same CDE-UITID combination
        - Each violation should appear in exactly ONE system column""",
        agent=agent,
        expected_output="""A properly formatted table-based report containing:
        1. Executive summary showing 6 CDEs validated, 3 violations found
        2. Detailed table with 18 rows (6 CDEs × 3 UITIDs) showing validation results
        3. Violations summary listing exactly 3 violations
        4. System analysis showing 1 violation per system (33% each)
        5. NO N/A values in the detailed results table"""
    )

def create_mysql_connection_test_task(agent):
    """Create task for testing MySQL connections"""
    return Task(
        description="""Test connectivity to all three MySQL database systems:
        - Trade System
        - Settlement System  
        - Reporting System
        
        Verify that connections can be established and basic queries can be executed.
        Report any connection issues that need to be resolved before proceeding with validation.""",
        agent=agent,
        expected_output="""Connection test results showing:
        - Status of each system connection (Success/Failed)
        - Any error messages for failed connections
        - Recommendations for resolving connection issues"""
    ) 