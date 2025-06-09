#!/usr/bin/env python3
"""
Test script to check what CDEs and DQ rules are available in the Neo4j database
"""

from neo4j_tools import Neo4jConnection
import json

def test_graph_data():
    """Test what CDEs and DQ rules are available in Neo4j"""
    
    print("="*80)
    print("NEO4J GRAPH DATA TEST")
    print("="*80)
    
    neo4j_conn = Neo4jConnection()
    
    try:
        print("\n1. ALL CDEs IN THE DATABASE:")
        print("-" * 40)
        
        # Get all CDEs
        cde_query = """
        MATCH (cde:CDE)
        RETURN cde.name as cde_name, 
               cde.dataType as cde_data_type,
               cde.columnName as cde_column_name
        ORDER BY cde_name
        """
        
        cdes = neo4j_conn.execute_query(cde_query)
        if cdes:
            for cde in cdes:
                print(f"   - {cde['cde_name']} (type: {cde['cde_data_type']}, column: {cde['cde_column_name']})")
        else:
            print("   No CDEs found!")
        
        print(f"\n   Total CDEs found: {len(cdes)}")
        
        print("\n2. ALL DQ RULES IN THE DATABASE:")
        print("-" * 40)
        
        # Get all DQ rules
        rule_query = """
        MATCH (rule:DQRule)
        RETURN rule.id as rule_id,
               rule.description as rule_description,
               rule.ruleType as rule_type
        ORDER BY rule_id
        """
        
        rules = neo4j_conn.execute_query(rule_query)
        if rules:
            for rule in rules:
                print(f"   - {rule['rule_id']}: {rule['rule_description']} (type: {rule['rule_type']})")
        else:
            print("   No DQ Rules found!")
        
        print(f"\n   Total DQ Rules found: {len(rules)}")
        
        print("\n3. CDE-RULE RELATIONSHIPS:")
        print("-" * 40)
        
        # Get CDE-Rule relationships
        relationship_query = """
        MATCH (cde:CDE)-[:HAS_RULE]->(rule:DQRule)
        RETURN cde.name as cde_name,
               rule.id as rule_id,
               rule.description as rule_description,
               rule.ruleType as rule_type
        ORDER BY cde_name, rule_id
        """
        
        relationships = neo4j_conn.execute_query(relationship_query)
        if relationships:
            current_cde = None
            for rel in relationships:
                if rel['cde_name'] != current_cde:
                    current_cde = rel['cde_name']
                    print(f"\n   CDE: {current_cde}")
                print(f"     - {rel['rule_id']}: {rel['rule_description']} ({rel['rule_type']})")
        else:
            print("   No CDE-Rule relationships found!")
        
        print(f"\n   Total CDE-Rule relationships: {len(relationships)}")
        
        print("\n4. SYSTEM-CDE RELATIONSHIPS:")
        print("-" * 40)
        
        # Get System-CDE relationships
        system_query = """
        MATCH (system:System)-[:HAS_CDE]->(cde:CDE)
        RETURN system.name as system_name,
               cde.name as cde_name
        ORDER BY system_name, cde_name
        """
        
        system_relationships = neo4j_conn.execute_query(system_query)
        if system_relationships:
            current_system = None
            for rel in system_relationships:
                if rel['system_name'] != current_system:
                    current_system = rel['system_name']
                    print(f"\n   System: {current_system}")
                print(f"     - {rel['cde_name']}")
        else:
            print("   No System-CDE relationships found!")
        
        print(f"\n   Total System-CDE relationships: {len(system_relationships)}")
        
        print("\n5. COMPLETE GRAPH DATA (as used by workflow):")
        print("-" * 40)
        
        # This is the same query used by the graph_data_retriever_tool
        complete_query = """
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
        
        complete_data = neo4j_conn.execute_query(complete_query)
        if complete_data:
            for cde_data in complete_data:
                print(f"\n   CDE: {cde_data['cde_name']}")
                print(f"     Data Type: {cde_data['cde_data_type']}")
                print(f"     Column Name: {cde_data['cde_column_name']}")
                print(f"     Systems: {cde_data['systems']}")
                print(f"     DQ Rules: {len(cde_data['dq_rules'])}")
                for rule in cde_data['dq_rules']:
                    if rule['id']:  # Filter out null rules
                        print(f"       - {rule['id']}: {rule['description']} ({rule['ruleType']})")
        else:
            print("   No complete graph data found!")
        
        print(f"\n   Total complete CDE records: {len(complete_data)}")
        
        print("\n" + "="*80)
        print("ANALYSIS:")
        print("="*80)
        
        # Expected CDEs for the workflow
        expected_cdes = ['uitid', 'Price', 'Quantity', 'Side', 'Symbol', 'Trade Date']
        
        print(f"\nExpected CDEs: {expected_cdes}")
        actual_cdes = [cde['cde_name'] for cde in complete_data] if complete_data else []
        print(f"Actual CDEs: {actual_cdes}")
        
        missing_cdes = [cde for cde in expected_cdes if cde not in actual_cdes]
        if missing_cdes:
            print(f"⚠️  MISSING CDEs: {missing_cdes}")
        else:
            print("✓ All expected CDEs found")
        
        # Check for CDEs with no rules
        cdes_without_rules = []
        if complete_data:
            for cde_data in complete_data:
                has_valid_rules = any(rule['id'] for rule in cde_data['dq_rules'])
                if not has_valid_rules:
                    cdes_without_rules.append(cde_data['cde_name'])
        
        if cdes_without_rules:
            print(f"⚠️  CDEs WITHOUT RULES: {cdes_without_rules}")
        else:
            print("✓ All CDEs have associated DQ rules")
        
        print("="*80)
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        
    finally:
        neo4j_conn.close()

if __name__ == "__main__":
    test_graph_data() 