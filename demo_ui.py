#!/usr/bin/env python3
"""
Demo script for GraphDB Query UI
Shows how to use the UI programmatically and provides example queries
"""

import requests
import json
import time

class GraphDBUIDemo:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        
    def test_connection(self):
        """Test if the UI is running"""
        try:
            response = requests.get(f"{self.base_url}/api/schema", timeout=5)
            if response.status_code == 200:
                print("✅ GraphDB UI is running!")
                return True
            else:
                print(f"❌ UI returned status code: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to GraphDB UI. Make sure it's running on http://localhost:5000")
            return False
        except Exception as e:
            print(f"❌ Error connecting to UI: {e}")
            return False
    
    def get_schema(self):
        """Get database schema information"""
        try:
            response = requests.get(f"{self.base_url}/api/schema")
            if response.status_code == 200:
                schema = response.json()
                print("📊 Database Schema:")
                print(f"   Node types: {len(schema.get('node_counts', []))}")
                print(f"   Relationship types: {len(schema.get('relationship_counts', []))}")
                print(f"   Sample CDEs: {len(schema.get('sample_cdes', []))}")
                print(f"   Sample Rules: {len(schema.get('sample_rules', []))}")
                return schema
            else:
                print(f"❌ Error getting schema: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def natural_language_query(self, query):
        """Execute a natural language query"""
        try:
            print(f"🤖 Natural Language Query: '{query}'")
            response = requests.post(
                f"{self.base_url}/api/query",
                json={"query": query},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"⚡ Generated Cypher: {result['cypher_query']}")
                
                if 'results' in result and 'error' in result['results']:
                    print(f"❌ Query Error: {result['results']['error']}")
                elif 'results' in result and 'success' in result['results']:
                    print(f"✅ Results: {result['results']['count']} records returned")
                    # Show first few results
                    results = result['results']['results']
                    if results:
                        print("📋 Sample Results:")
                        for i, record in enumerate(results[:3]):
                            print(f"   {i+1}. {record}")
                        if len(results) > 3:
                            print(f"   ... and {len(results) - 3} more records")
                return result
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def cypher_query(self, query):
        """Execute a direct Cypher query"""
        try:
            print(f"⚡ Cypher Query: '{query}'")
            response = requests.post(
                f"{self.base_url}/api/cypher",
                json={"query": query},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'error' in result:
                    print(f"❌ Query Error: {result['error']}")
                elif 'success' in result:
                    print(f"✅ Results: {result['count']} records returned")
                    # Show first few results
                    results = result['results']
                    if results:
                        print("📋 Sample Results:")
                        for i, record in enumerate(results[:3]):
                            print(f"   {i+1}. {record}")
                        if len(results) > 3:
                            print(f"   ... and {len(results) - 3} more records")
                return result
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def run_demo(self):
        """Run a complete demo of the UI functionality"""
        print("🚀 GraphDB Query UI Demo")
        print("=" * 60)
        
        # Test connection
        if not self.test_connection():
            return
        
        print()
        
        # Get schema
        schema = self.get_schema()
        if not schema:
            return
        
        print()
        
        # Example natural language queries
        natural_queries = [
            "Show me all CDEs",
            "Find all data quality rules",
            "What rules are associated with Trade Date?",
            "Show me all systems and their CDEs",
            "Find CDEs that have NOT_NULL rules"
        ]
        
        print("🤖 Natural Language Query Examples:")
        print("-" * 40)
        
        for query in natural_queries:
            self.natural_language_query(query)
            print()
            time.sleep(1)  # Small delay between queries
        
        # Example Cypher queries
        cypher_queries = [
            "MATCH (cde:CDE) RETURN cde.name, cde.dataType LIMIT 5",
            "MATCH (rule:DQRule) RETURN rule.id, rule.description LIMIT 5",
            "MATCH (cde:CDE)-[:HAS_RULE]->(rule:DQRule) RETURN cde.name, rule.id LIMIT 5"
        ]
        
        print("⚡ Direct Cypher Query Examples:")
        print("-" * 40)
        
        for query in cypher_queries:
            self.cypher_query(query)
            print()
            time.sleep(1)
        
        print("🎉 Demo completed!")
        print("=" * 60)
        print("💡 To use the web interface, open: http://localhost:5000")
        print("📚 For more examples, see the UI's example queries section")

def main():
    demo = GraphDBUIDemo()
    demo.run_demo()

if __name__ == "__main__":
    main() 