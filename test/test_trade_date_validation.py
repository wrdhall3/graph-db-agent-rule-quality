#!/usr/bin/env python3
"""
Test script to isolate Trade Date validation issue
"""

from mysql_connections import MySQLConnectionManager
import json

def test_trade_date_validation():
    """Test Trade Date validation specifically"""
    mysql_manager = MySQLConnectionManager()
    
    # Use CORRECTED Trade Date mapping
    trade_date_mapping = {
        'Trade System': 'trade_date',
        'Settlement System': 'trade_date',  # Fixed: Available in settlement system
        'Reporting System': 'trade_date'
    }
    
    uitid = 'UIT-0001-ABC'
    
    print("="*80)
    print("CORRECTED TRADE DATE VALIDATION TEST")
    print("="*80)
    
    for system_name in ['Trade System', 'Settlement System', 'Reporting System']:
        print(f"\n--- {system_name} ---")
        
        print(f"Column mapping: {trade_date_mapping.get(system_name)}")
        
        validation = mysql_manager.validate_dq_rule(
            system_name=system_name,
            uitid=uitid,
            cde_column_name=trade_date_mapping,
            rule_type='NOT_NULL',
            rule_description='Trade Date cannot be null'
        )
        
        print(f"Value: {validation['value']}")
        print(f"Violation: {validation['violation']}")
        print(f"Available: {validation['column_available']}")
        
        print("-" * 40)
    
    mysql_manager.close_all_connections()

if __name__ == "__main__":
    test_trade_date_validation() 