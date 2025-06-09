# Updated import for newer CrewAI versions  
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from typing import Dict, List, Any, Optional
import json
from mysql_connections import MySQLConnectionManager
from neo4j_tools import Neo4jConnection
from mysql_config import CDE_COLUMN_MAPPINGS
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@tool("graph_data_retriever")
def graph_data_retriever_tool(query_type: str = "all_cdes_and_rules") -> str:
    """
    Retrieve data from Neo4j graph database
    Args:
        query_type: Type of query ("all_cdes_and_rules", "cdes_only", "rules_only")
    """
    neo4j_conn = Neo4jConnection()
    
    try:
        if query_type == "all_cdes_and_rules":
            # Get all CDEs with their associated DQ rules and systems
            cypher_query = """
            MATCH (cde:CDE)
            OPTIONAL MATCH (cde)-[:HAS_RULE]->(dqRule:DQRule)
            OPTIONAL MATCH (system:System)-[:HAS_CDE]->(cde)
            RETURN cde.name as cde_name, 
                   cde.dataType as cde_data_type,
                   cde.columnName as cde_column_name,
                   collect(DISTINCT {
                       id: dqRule.id, 
                       description: dqRule.description, 
                       ruleType: dqRule.ruleType
                   }) as dq_rules,
                   collect(DISTINCT system.name) as systems
            ORDER BY cde_name
            """
        elif query_type == "cdes_only":
            cypher_query = """
            MATCH (cde:CDE)
            OPTIONAL MATCH (system:System)-[:HAS_CDE]->(cde)
            RETURN cde.name as cde_name, 
                   cde.dataType as cde_data_type,
                   cde.columnName as cde_column_name,
                   collect(DISTINCT system.name) as systems
            ORDER BY cde_name
            """
        elif query_type == "rules_only":
            cypher_query = """
            MATCH (dqRule:DQRule)
            MATCH (cde:CDE)-[:HAS_RULE]->(dqRule)
            RETURN dqRule.id as rule_id,
                   dqRule.description as rule_description,
                   dqRule.ruleType as rule_type,
                   cde.name as cde_name,
                   cde.columnName as cde_column_name
            ORDER BY cde_name, rule_id
            """
        
        result = neo4j_conn.execute_query(cypher_query)
        logger.info(f"Retrieved graph data with query type: {query_type}")
        
        # Convert result to string format for consistency
        return json.dumps(result, indent=2, default=str)
        
    except Exception as e:
        error_msg = f"Error retrieving graph data: {str(e)}"
        logger.error(error_msg)
        return error_msg
    finally:
        # Close the connection
        try:
            neo4j_conn.close()
        except:
            pass

@tool("mysql_validation")
def mysql_validation_tool(cde_name: str, cde_column: str, rule_type: str, rule_description: str, 
                         uitids: str = "", limit: int = 10) -> str:
    """
    Validate a DQ rule across all MySQL systems
    Args:
        cde_name: Name of the CDE
        cde_column: Column name in MySQL tables or CDE name for mapping
        rule_type: Type of DQ rule (NOT_NULL, POSITIVE_VALUE, etc.)
        rule_description: Description of the rule
        uitids: Comma-separated list of specific uitids to check, or empty for random sample
        limit: Maximum number of uitids to check if uitids not specified
    """
    mysql_manager = MySQLConnectionManager()
    
    try:
        # Get uitids to check
        if uitids and uitids.strip():
            uitid_list = [uid.strip() for uid in uitids.split(',')]
        else:
            uitid_list = mysql_manager.get_all_uitids(limit=limit)
        
        if not uitid_list:
            return "No uitids found in any system"
        
        # Map CDE name to actual column name(s)
        # Handle common mappings and system-specific differences
        actual_column_mapping = None
        
        # Try to find the column mapping based on CDE name
        if cde_name == "Price":
            actual_column_mapping = "price"
        elif cde_name == "Quantity":
            actual_column_mapping = "quantity"
        elif cde_name == "Side":
            actual_column_mapping = "side"
        elif cde_name == "Symbol":
            # Symbol has different column names per system
            actual_column_mapping = {
                'Trade System': 'symbol',
                'Settlement System': 'symbol', 
                'Reporting System': 'instrument_symbol'
            }
        elif cde_name == "Trade Date":
            # Trade Date is available in all systems
            actual_column_mapping = {
                'Trade System': 'trade_date',
                'Settlement System': 'trade_date',  # Available in settlement system
                'Reporting System': 'trade_date'
            }
        elif cde_name == "uitid":
            actual_column_mapping = "uitid"
        else:
            # Use the provided column name as fallback
            actual_column_mapping = cde_column
        
        # Initialize results structure
        validation_results = []
        systems = ['Trade System', 'Settlement System', 'Reporting System']
        
        # Validate each uitid across all systems
        for uitid in uitid_list:
            uitid_result = {
                'uitid': uitid,
                'cde_name': cde_name,
                'rule_description': rule_description,
                'systems': {}
            }
            
            for system_name in systems:
                validation = mysql_manager.validate_dq_rule(
                    system_name=system_name,
                    uitid=uitid,
                    cde_column_name=actual_column_mapping,
                    rule_type=rule_type,
                    rule_description=rule_description
                )
                
                # Handle cases where column is not available
                if validation.get('column_available', True) == False:
                    uitid_result['systems'][system_name] = {
                        'has_violation': None,  # Not available
                        'value': None,
                        'available': False
                    }
                else:
                    uitid_result['systems'][system_name] = {
                        'has_violation': validation['violation'],
                        'value': validation['value'],
                        'available': True
                    }
            
            validation_results.append(uitid_result)
        
        # Format results as JSON for easy parsing
        result = {
            'cde_name': cde_name,
            'rule_description': rule_description,
            'total_uitids_checked': len(uitid_list),
            'validation_results': validation_results
        }
        
        logger.info(f"Validated DQ rule for {cde_name} across {len(uitid_list)} uitids")
        return json.dumps(result, indent=2, default=str)
        
    except Exception as e:
        error_msg = f"Error during MySQL validation: {str(e)}"
        logger.error(error_msg)
        return error_msg

@tool("mysql_connection_test")
def mysql_connection_test_tool() -> str:
    """Test connections to all MySQL systems"""
    mysql_manager = MySQLConnectionManager()
    
    try:
        test_results = mysql_manager.test_connections()
        
        result = {
            'connection_tests': test_results,
            'total_systems': len(test_results),
            'successful_connections': sum(test_results.values()),
            'failed_connections': len(test_results) - sum(test_results.values())
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_msg = f"Error testing MySQL connections: {str(e)}"
        logger.error(error_msg)
        return error_msg

@tool("dq_report_generator")
def dq_report_generator_tool(validation_results: str, format_type: str = "table") -> str:
    """
    Generate formatted report from validation results
    Args:
        validation_results: JSON string of validation results
        format_type: Format type ("table", "csv", "summary")
    """
    try:
        # Parse validation results
        if isinstance(validation_results, str):
            try:
                data = json.loads(validation_results)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse validation results JSON: {str(e)}")
                logger.error(f"Raw validation_results: {validation_results[:500]}...")
                return f"Error parsing validation results: {str(e)}"
        else:
            data = validation_results
        
        if format_type == "table":
            return _generate_table_report(data)
        elif format_type == "csv":
            return _generate_csv_report(data)
        elif format_type == "summary":
            return _generate_summary_report(data)
        else:
            return "Invalid format type specified"
            
    except Exception as e:
        error_msg = f"Error generating report: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Raw validation_results input: {validation_results}")
        
        # Return a basic error report instead of just an error message
        return f"""
================================================================================
DQ VALIDATION REPORT - ERROR
================================================================================
An error occurred while generating the report: {str(e)}

Raw input received: {str(validation_results)[:200]}...

Please check the validation results format and try again.
================================================================================
"""

def _generate_table_report(data: Dict) -> str:
    """Generate table format report"""
    # Handle different data formats
    if isinstance(data, list):
        # If data is a list, convert to expected format
        validation_results = data
        cde_name = "Multiple CDEs"
        rule_description = "Various rules"
        total_checked = len(data)
    elif isinstance(data, dict) and data.get('validation_results'):
        # Handle nested validation results structure
        if isinstance(data['validation_results'], list) and len(data['validation_results']) > 0:
            # Check if it's a list of CDE validation results
            first_item = data['validation_results'][0]
            if isinstance(first_item, dict) and 'validation_results' in first_item:
                # This is a list of CDEs, each with their own validation results
                # Flatten the structure for the table
                all_results = []
                for cde_validation in data['validation_results']:
                    cde_results = cde_validation.get('validation_results', [])
                    for result in cde_results:
                        result['cde_name'] = cde_validation.get('cde_name', 'Unknown')
                        result['rule_description'] = cde_validation.get('rule_description', 'Unknown')
                        all_results.append(result)
                validation_results = all_results
                cde_name = "Multiple CDEs"
                rule_description = "Various rules"
                total_checked = len(all_results)
            else:
                # This is a direct list of validation results
                validation_results = data['validation_results']
                cde_name = data.get('cde_name', 'Unknown CDE')
                rule_description = data.get('rule_description', 'Unknown rule')
                total_checked = data.get('total_uitids_checked', len(validation_results))
        else:
            validation_results = data['validation_results']
            cde_name = data.get('cde_name', 'Unknown CDE')
            rule_description = data.get('rule_description', 'Unknown rule')
            total_checked = data.get('total_uitids_checked', len(validation_results))
    else:
        return "No validation results to format"
    
    # Header
    report = f"\n{'='*80}\n"
    report += f"DQ RULE VALIDATION REPORT\n"
    report += f"{'='*80}\n"
    report += f"CDE: {cde_name}\n"
    report += f"Rule: {rule_description}\n"
    report += f"Total UITIDs Checked: {total_checked}\n"
    report += f"{'='*80}\n\n"
    
    # Table header - dynamic format for multiple CDEs
    if cde_name == "Multiple CDEs":
        report += f"{'CDE':<15} {'DQ Rule Desc.':<35} {'uitid':<15} {'Trade System':<15} {'Settlement System':<20} {'Reporting System':<18}\n"
        report += f"{'-'*15} {'-'*35} {'-'*15} {'-'*15} {'-'*20} {'-'*18}\n"
    else:
        report += f"{'UITID':<10} {'Trade System':<15} {'Settlement System':<20} {'Reporting System':<18}\n"
        report += f"{'-'*10} {'-'*15} {'-'*20} {'-'*18}\n"
    
    # Table rows
    for result in validation_results:
        uitid = result['uitid']
        result_cde_name = result.get('cde_name', cde_name)
        result_rule_desc = result.get('rule_description', rule_description)
        
        # Handle Trade System status
        if result['systems']['Trade System'].get('available', True) == False:
            trade_status = "-"
        elif result['systems']['Trade System']['has_violation']:
            trade_status = "Violation"
        else:
            trade_status = "OK"
        
        # Handle Settlement System status
        if result['systems']['Settlement System'].get('available', True) == False:
            settlement_status = "-"
        elif result['systems']['Settlement System']['has_violation']:
            settlement_status = "Violation"
        else:
            settlement_status = "OK"
        
        # Handle Reporting System status
        if result['systems']['Reporting System'].get('available', True) == False:
            reporting_status = "-"
        elif result['systems']['Reporting System']['has_violation']:
            reporting_status = "Violation"
        else:
            reporting_status = "OK"
        
        # Format row based on whether we have multiple CDEs
        if cde_name == "Multiple CDEs":
            short_cde = result_cde_name[:14] if len(result_cde_name) > 14 else result_cde_name
            short_rule = result_rule_desc[:34] if len(result_rule_desc) > 34 else result_rule_desc
            report += f"{short_cde:<15} {short_rule:<35} {uitid:<15} {trade_status:<15} {settlement_status:<20} {reporting_status:<18}\n"
        else:
            report += f"{uitid:<10} {trade_status:<15} {settlement_status:<20} {reporting_status:<18}\n"
    
    return report

def _generate_csv_report(data: Dict) -> str:
    """Generate CSV format report"""
    # Handle different data formats - same logic as table report
    if isinstance(data, list):
        validation_results = data
        cde_name = "Multiple CDEs"
        rule_description = "Various rules"
    elif isinstance(data, dict) and data.get('validation_results'):
        # Handle nested validation results structure
        if isinstance(data['validation_results'], list) and len(data['validation_results']) > 0:
            first_item = data['validation_results'][0]
            if isinstance(first_item, dict) and 'validation_results' in first_item:
                # Flatten the structure for CSV
                all_results = []
                for cde_validation in data['validation_results']:
                    cde_results = cde_validation.get('validation_results', [])
                    for result in cde_results:
                        result['cde_name'] = cde_validation.get('cde_name', 'Unknown')
                        result['rule_description'] = cde_validation.get('rule_description', 'Unknown')
                        all_results.append(result)
                validation_results = all_results
                cde_name = "Multiple CDEs"
                rule_description = "Various rules"
            else:
                validation_results = data['validation_results']
                cde_name = data.get('cde_name', 'Unknown CDE')
                rule_description = data.get('rule_description', 'Unknown rule')
        else:
            validation_results = data['validation_results']
            cde_name = data.get('cde_name', 'Unknown CDE')
            rule_description = data.get('rule_description', 'Unknown rule')
    else:
        return "No validation results to format"
    
    csv_lines = []
    csv_lines.append("CDE,DQ Rule Description,UITID,Trade System,Settlement System,Reporting System")
    
    for result in validation_results:
        uitid = result['uitid']
        result_cde_name = result.get('cde_name', cde_name)
        result_rule_desc = result.get('rule_description', rule_description)
        
        # Handle Trade System status
        if result['systems']['Trade System'].get('available', True) == False:
            trade_status = "-"
        elif result['systems']['Trade System']['has_violation']:
            trade_status = "Violation"
        else:
            trade_status = "OK"
        
        # Handle Settlement System status
        if result['systems']['Settlement System'].get('available', True) == False:
            settlement_status = "-"
        elif result['systems']['Settlement System']['has_violation']:
            settlement_status = "Violation"
        else:
            settlement_status = "OK"
        
        # Handle Reporting System status
        if result['systems']['Reporting System'].get('available', True) == False:
            reporting_status = "-"
        elif result['systems']['Reporting System']['has_violation']:
            reporting_status = "Violation"
        else:
            reporting_status = "OK"
        
        csv_lines.append(f"{result_cde_name},{result_rule_desc},{uitid},{trade_status},{settlement_status},{reporting_status}")
    
    return "\n".join(csv_lines)

def _generate_summary_report(data: Dict) -> str:
    """Generate summary format report"""
    # Handle different data formats - same logic as table report
    if isinstance(data, list):
        validation_results = data
        cde_name = "Multiple CDEs"
        rule_description = "Various rules"
    elif isinstance(data, dict) and data.get('validation_results'):
        # Handle nested validation results structure
        if isinstance(data['validation_results'], list) and len(data['validation_results']) > 0:
            first_item = data['validation_results'][0]
            if isinstance(first_item, dict) and 'validation_results' in first_item:
                # Flatten the structure for summary
                all_results = []
                for cde_validation in data['validation_results']:
                    cde_results = cde_validation.get('validation_results', [])
                    for result in cde_results:
                        result['cde_name'] = cde_validation.get('cde_name', 'Unknown')
                        result['rule_description'] = cde_validation.get('rule_description', 'Unknown')
                        all_results.append(result)
                validation_results = all_results
                cde_name = "Multiple CDEs"
                rule_description = "Various rules"
            else:
                validation_results = data['validation_results']
                cde_name = data.get('cde_name', 'Unknown CDE')
                rule_description = data.get('rule_description', 'Unknown rule')
        else:
            validation_results = data['validation_results']
            cde_name = data.get('cde_name', 'Unknown CDE')
            rule_description = data.get('rule_description', 'Unknown rule')
    else:
        return "No validation results to format"
    
    # Get unique UITIDs and CDEs for proper counting
    unique_uitids = set()
    unique_cdes = set()
    
    # Count violations per system (unique UITIDs that have violations)
    system_violations = {
        'Trade System': set(),
        'Settlement System': set(),
        'Reporting System': set()
    }
    
    # Track total violations found
    total_violations = 0
    violation_details = []
    
    for result in validation_results:
        uitid = result['uitid']
        cde_name_result = result.get('cde_name', 'Unknown')
        unique_uitids.add(uitid)
        unique_cdes.add(cde_name_result)
        
        for system_name in system_violations.keys():
            # Check if there's a violation in this system for this uitid-cde combination
            if (result['systems'][system_name].get('available', True) == True and 
                result['systems'][system_name]['has_violation']):
                system_violations[system_name].add(uitid)
                total_violations += 1
                violation_details.append(f"- {cde_name_result}: {uitid} - {system_name}")
    
    total_unique_uitids = len(unique_uitids)
    total_unique_cdes = len(unique_cdes)
    
    # Generate summary
    summary = f"\n{'='*60}\n"
    summary += f"DQ RULE VALIDATION SUMMARY\n"
    summary += f"{'='*60}\n"
    
    if cde_name == "Multiple CDEs":
        summary += f"CDEs Validated: {total_unique_cdes}\n"
        summary += f"UITIDs Checked: {total_unique_uitids}\n"
        summary += f"Total Violations Found: {total_violations}\n"
    else:
        summary += f"CDE: {cde_name}\n"
        summary += f"Rule: {rule_description}\n"
        summary += f"UITIDs Checked: {total_unique_uitids}\n"
        summary += f"Total Violations Found: {total_violations}\n"
    
    summary += f"{'='*60}\n\n"
    
    # Violations details
    if violation_details:
        summary += "VIOLATIONS FOUND:\n"
        summary += f"{'-'*40}\n"
        for violation in violation_details:
            summary += f"{violation}\n"
        summary += f"\n"
    
    summary += "VIOLATION SUMMARY BY SYSTEM:\n"
    summary += f"{'-'*40}\n"
    
    for system_name, violated_uitids in system_violations.items():
        violation_count = len(violated_uitids)
        violation_rate = (violation_count / total_unique_uitids) * 100 if total_unique_uitids > 0 else 0
        summary += f"{system_name:<20}: {violation_count:>3}/{total_unique_uitids} ({violation_rate:.2f}%)\n"
    
    return summary 