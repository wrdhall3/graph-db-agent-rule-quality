#!/usr/bin/env python3
"""
Direct test of the mysql validation logic to verify it can detect the expected violations
"""

from mysql_connections import MySQLConnectionManager
import json

def test_validation_direct():
    """Test the mysql validation logic directly with the expected violations"""
    
    print("="*80)
    print("DIRECT MYSQL VALIDATION LOGIC TEST")
    print("="*80)
    
    mysql_manager = MySQLConnectionManager()
    
    # Test cases based on the database debug output
    test_cases = [
        {
            'cde_name': 'uitid',
            'cde_column': 'uitid', 
            'rule_type': 'NOT_NULL',
            'rule_description': 'uitid cannot be null',
            'expected_violations': 0  # All uitids should be present
        },
        {
            'cde_name': 'Price',
            'cde_column': 'price',
            'rule_type': 'POSITIVE_VALUE', 
            'rule_description': 'Price must be positive',
            'expected_violations': 0  # All prices are positive
        },
        {
            'cde_name': 'Quantity',
            'cde_column': 'quantity',
            'rule_type': 'POSITIVE_VALUE',
            'rule_description': 'Quantity must be positive', 
            'expected_violations': 1  # UIT-0002-XYZ has quantity = -15 in Trade System
        },
        {
            'cde_name': 'Side',
            'cde_column': 'side',
            'rule_type': 'ENUM_VALUE',
            'rule_description': 'Side must be either BUY or SELL',
            'expected_violations': 0  # All sides are BUY or SELL
        },
        {
            'cde_name': 'Symbol',
            'cde_column': {
                'Trade System': 'symbol',
                'Settlement System': 'symbol', 
                'Reporting System': 'instrument_symbol'
            },
            'rule_type': 'NOT_NULL',
            'rule_description': 'Symbol must not be null',
            'expected_violations': 1  # UIT-0003-DEF has NULL symbol in Settlement System
        },
        {
            'cde_name': 'Trade Date',
            'cde_column': 'trade_date', 
            'rule_type': 'NOT_NULL',
            'rule_description': 'Trade Date cannot be null',
            'expected_violations': 1  # UIT-0001-ABC has NULL trade_date in Reporting System
        }
    ]
    
    uitids = ['UIT-0001-ABC', 'UIT-0002-XYZ', 'UIT-0003-DEF']
    systems = ['Trade System', 'Settlement System', 'Reporting System']
    
    total_expected_violations = 3
    total_actual_violations = 0
    
    try:
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. Testing {test_case['cde_name']} - {test_case['rule_description']}")
            print("-" * 60)
            
            violations_found = 0
            violation_details = []
            
            # Test each UITID across all systems
            for uitid in uitids:
                print(f"   Testing UITID: {uitid}")
                
                for system_name in systems:
                    try:
                        # Call the validation method directly
                        validation_result = mysql_manager.validate_dq_rule(
                            system_name=system_name,
                            uitid=uitid,
                            cde_column_name=test_case['cde_column'],
                            rule_type=test_case['rule_type'],
                            rule_description=test_case['rule_description']
                        )
                        
                        if validation_result.get('column_available', True) == False:
                            print(f"     {system_name}: Column not available")
                        elif validation_result.get('violation', False):
                            violations_found += 1
                            value = validation_result.get('value', 'N/A')
                            violation_details.append(f"     ✗ {system_name}: {value} (VIOLATION)")
                            print(f"     ✗ {system_name}: {value} (VIOLATION)")
                        else:
                            value = validation_result.get('value', 'N/A')
                            print(f"     ✓ {system_name}: {value} (OK)")
                            
                    except Exception as e:
                        print(f"     ✗ {system_name}: ERROR - {str(e)}")
            
            print(f"\n   Violations found: {violations_found} (expected: {test_case['expected_violations']})")
            
            # Check if results match expectations
            if violations_found == test_case['expected_violations']:
                print("   ✓ PASS - Expected violations found")
            else:
                print("   ✗ FAIL - Violation count mismatch")
            
            total_actual_violations += violations_found
        
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Total expected violations: {total_expected_violations}")
        print(f"Total actual violations found: {total_actual_violations}")
        
        if total_actual_violations == total_expected_violations:
            print("✓ OVERALL PASS - All expected violations detected")
        else:
            print("✗ OVERALL FAIL - Violation detection issue")
        
        print("="*80)
        
    except Exception as e:
        print(f"OVERALL ERROR: {str(e)}")
        
    finally:
        mysql_manager.close_all_connections()

if __name__ == "__main__":
    test_validation_direct() 