#!/usr/bin/env python3

from neo4j_tools import Neo4jConnection
import json

def debug_neo4j_database():
    """Debug script to explore Neo4j database structure"""
    neo4j_conn = Neo4jConnection()
    
    try:
        print("="*80)
        print("NEO4J DATABASE STRUCTURE DEBUG")
        print("="*80)
        
        # 1. Check what node types exist
        print("\n1. NODE TYPES IN DATABASE:")
        print("-" * 40)
        query = "MATCH (n) RETURN DISTINCT labels(n) as node_types, count(*) as count ORDER BY count DESC"
        results = neo4j_conn.execute_query(query)
        for result in results:
            print(f"  {result['node_types']}: {result['count']} nodes")
        
        # 2. Check what relationship types exist
        print("\n2. RELATIONSHIP TYPES IN DATABASE:")
        print("-" * 40)
        query = "MATCH ()-[r]->() RETURN DISTINCT type(r) as relationship_type, count(*) as count ORDER BY count DESC"
        results = neo4j_conn.execute_query(query)
        for result in results:
            print(f"  {result['relationship_type']}: {result['count']} relationships")
        
        # 3. Show all CDEs and their properties
        print("\n3. ALL CDEs IN DATABASE:")
        print("-" * 40)
        query = "MATCH (cde:CDE) RETURN cde ORDER BY cde.name"
        results = neo4j_conn.execute_query(query)
        for result in results:
            cde = result['cde']
            print(f"  CDE: {cde.get('name', 'N/A')}")
            print(f"    Data Type: {cde.get('dataType', 'N/A')}")
            print(f"    Column Name: {cde.get('columnName', 'N/A')}")
            print()
        
        # 4. Show all DQ Rules
        print("\n4. ALL DQ RULES IN DATABASE:")
        print("-" * 40)
        query = "MATCH (dq:DQRule) RETURN dq ORDER BY dq.id"
        results = neo4j_conn.execute_query(query)
        for result in results:
            dq = result['dq']
            print(f"  Rule ID: {dq.get('id', 'N/A')}")
            print(f"    Type: {dq.get('ruleType', 'N/A')}")
            print(f"    Description: {dq.get('description', 'N/A')}")
            print()
        
        # 5. Show any System nodes if they exist
        print("\n5. SYSTEM NODES (if any):")
        print("-" * 40)
        query = "MATCH (s:System) RETURN s ORDER BY s.name"
        results = neo4j_conn.execute_query(query)
        if results:
            for result in results:
                system = result['s']
                print(f"  System: {system.get('name', 'N/A')}")
        else:
            print("  No System nodes found in database")
        
        # 6. Show CDE-DQRule relationships
        print("\n6. CDE-DQRULE RELATIONSHIPS:")
        print("-" * 40)
        query = """
        MATCH (cde:CDE)-[r:HAS_RULE]->(dq:DQRule) 
        RETURN cde.name as cde_name, dq.id as rule_id, dq.description as rule_desc
        ORDER BY cde_name, rule_id
        """
        results = neo4j_conn.execute_query(query)
        for result in results:
            print(f"  {result['cde_name']} -> {result['rule_id']}: {result['rule_desc']}")
        
        # 7. Check for any relationships between CDEs and other nodes
        print("\n7. ALL RELATIONSHIPS FROM CDEs:")
        print("-" * 40)
        query = """
        MATCH (cde:CDE)-[r]->(other) 
        RETURN cde.name as cde_name, type(r) as relationship_type, labels(other) as target_labels, 
               other.name as target_name, other.id as target_id
        ORDER BY cde_name, relationship_type
        """
        results = neo4j_conn.execute_query(query)
        for result in results:
            print(f"  {result['cde_name']} -[{result['relationship_type']}]-> {result['target_labels']} ({result['target_name'] or result['target_id']})")
        
        print("\n" + "="*80)
        print("DEBUG COMPLETED")
        print("="*80)
        
    except Exception as e:
        print(f"Error during debug: {str(e)}")
    finally:
        neo4j_conn.close()

if __name__ == "__main__":
    debug_neo4j_database() 