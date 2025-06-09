#!/usr/bin/env python3
"""
Debug script to check actual MySQL data for specific UITIDs
"""

from mysql_connections import MySQLConnectionManager
from mysql_config import TRADE_TABLE_NAME

def debug_mysql_data():
    """Check actual data in MySQL databases for specific UITIDs"""
    mysql_manager = MySQLConnectionManager()
    
    # UITIDs mentioned by user with expected violations
    test_uitids = ['UIT-0001-ABC', 'UIT-0002-XYZ', 'UIT-0003-DEF']
    
    # Columns to check
    columns_to_check = ['uitid', 'trade_date', 'quantity', 'symbol', 'instrument_symbol', 'price', 'side']
    
    try:
        print("="*100)
        print("MYSQL DATABASE DATA DEBUG")
        print("="*100)
        
        for system_name in ['Trade System', 'Settlement System', 'Reporting System']:
            print(f"\n{'='*20} {system_name.upper()} {'='*20}")
            
            # First, let's see what columns actually exist in this table
            print(f"\n1. TABLE STRUCTURE:")
            describe_query = f"DESCRIBE {TRADE_TABLE_NAME}"
            columns = mysql_manager.execute_query(system_name, describe_query)
            if columns:
                print("   Available columns:")
                for col in columns:
                    print(f"     - {col['Field']} ({col['Type']}) - Null: {col['Null']}, Default: {col['Default']}")
            else:
                print("   Could not retrieve table structure")
            
            # Now check data for each UITID
            print(f"\n2. DATA FOR SPECIFIC UITIDs:")
            for uitid in test_uitids:
                print(f"\n   UITID: {uitid}")
                
                # Get all data for this UITID
                query = f"SELECT * FROM {TRADE_TABLE_NAME} WHERE uitid = %s"
                results = mysql_manager.execute_query(system_name, query, (uitid,))
                
                if results:
                    row = results[0]
                    print(f"     Found record:")
                    for key, value in row.items():
                        if value is None:
                            print(f"       {key}: NULL")
                        else:
                            print(f"       {key}: {value}")
                else:
                    print(f"     No record found for UITID {uitid}")
            
            print("\n" + "-"*60)
        
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

if __name__ == "__main__":
    debug_mysql_data() 