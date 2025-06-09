#!/usr/bin/env python3
"""
Script to add missing System nodes and USED_IN_SYSTEM relationships to Neo4j database
"""

from neo4j_tools import Neo4jConnection

def fix_neo4j_systems():
    """Add System nodes and relationships to Neo4j database"""
    neo4j_conn = Neo4jConnection()
    
    try:
        print("="*80)
        print("FIXING NEO4J SYSTEM RELATIONSHIPS")
        print("="*80)
        
        # 1. Create System nodes
        print("\n1. Creating System nodes...")
        systems = [
            {"name": "Trade System", "description": "Trade processing system"},
            {"name": "Settlement System", "description": "Settlement processing system"}, 
            {"name": "Reporting System", "description": "Reporting and analytics system"}
        ]
        
        for system in systems:
            query = """
            MERGE (s:System {name: $name})
            SET s.description = $description
            RETURN s.name as system_name
            """
            result = neo4j_conn.execute_query(query, system)
            print(f"  ✓ Created/Updated system: {system['name']}")
        
        # 2. Create USED_IN_SYSTEM relationships for all CDEs
        print("\n2. Creating USED_IN_SYSTEM relationships...")
        
        # All CDEs are used in all three systems for this use case
        cde_system_mappings = [
            ("Price", ["Trade System", "Settlement System", "Reporting System"]),
            ("Quantity", ["Trade System", "Settlement System", "Reporting System"]),
            ("Side", ["Trade System", "Settlement System", "Reporting System"]),
            ("Symbol", ["Trade System", "Settlement System", "Reporting System"]),
            ("Trade Date", ["Trade System", "Reporting System"]),  # Not in Settlement System
            ("uitid", ["Trade System", "Settlement System", "Reporting System"])
        ]
        
        for cde_name, system_names in cde_system_mappings:
            for system_name in system_names:
                query = """
                MATCH (cde:CDE {name: $cde_name})
                MATCH (s:System {name: $system_name})
                MERGE (cde)-[:USED_IN_SYSTEM]->(s)
                RETURN cde.name as cde_name, s.name as system_name
                """
                result = neo4j_conn.execute_query(query, {
                    "cde_name": cde_name,
                    "system_name": system_name
                })
                if result:
                    print(f"  ✓ Linked {cde_name} -> {system_name}")
                else:
                    print(f"  ✗ Failed to link {cde_name} -> {system_name}")
        
        # 3. Verify the relationships were created
        print("\n3. Verifying relationships...")
        query = """
        MATCH (cde:CDE)-[:USED_IN_SYSTEM]->(s:System)
        RETURN cde.name as cde_name, collect(s.name) as systems
        ORDER BY cde_name
        """
        results = neo4j_conn.execute_query(query)
        
        for result in results:
            systems_list = ", ".join(result['systems'])
            print(f"  {result['cde_name']}: {systems_list}")
        
        print("\n" + "="*80)
        print("NEO4J SYSTEM RELATIONSHIPS FIXED!")
        print("="*80)
        print("\nYou can now run the DQ validation workflow again.")
        
    except Exception as e:
        print(f"Error fixing Neo4j systems: {str(e)}")
    finally:
        neo4j_conn.close()

if __name__ == "__main__":
    fix_neo4j_systems() 