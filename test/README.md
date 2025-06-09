# Test and Debug Scripts

This folder contains test and debug scripts for the DQ Validation System. These tools help verify system functionality, troubleshoot issues, and test individual components.

## Test Scripts

### `debug_mysql_data.py`
**Purpose**: Verify actual data content in MySQL databases  
**Usage**: `python test/debug_mysql_data.py`  
**What it does**:
- Shows table structure for all three systems (Trade, Settlement, Reporting)
- Displays actual data for specific UITIDs (UIT-0001-ABC, UIT-0002-XYZ, UIT-0003-DEF)
- Performs specific violation checks to verify expected data conditions
- Useful for understanding what data exists and what violations should be detected

### `test_validation_direct.py`
**Purpose**: Test validation logic directly without CrewAI workflow  
**Usage**: `python test/test_validation_direct.py`  
**What it does**:
- Tests the underlying MySQL validation logic for all 6 CDEs
- Calls `MySQLConnectionManager.validate_dq_rule()` directly
- Verifies that exactly 3 violations are detected for test data
- Useful for isolating validation logic issues from workflow problems

### `test_graph_data.py`
**Purpose**: Verify Neo4j graph database structure and content  
**Usage**: `python test/test_graph_data.py`  
**What it does**:
- Lists all CDEs, DQ Rules, and relationships in Neo4j
- Verifies that all expected CDEs and rules are present
- Shows the complete graph data structure used by the workflow
- Useful for troubleshooting graph database configuration issues

### `debug_neo4j.py`
**Purpose**: Debug Neo4j database connectivity and basic structure  
**Usage**: `python test/debug_neo4j.py`  
**What it does**:
- Tests Neo4j connection
- Shows basic database statistics and node/relationship counts
- Legacy debug script for initial setup verification

## Additional Test Scripts

### `test_connection.py`
**Purpose**: Basic database connection testing  
**Usage**: `python test/test_connection.py`  
**What it does**:
- Tests basic connectivity to MySQL and Neo4j databases
- Simple connection verification script

### `test_trade_date_validation.py`
**Purpose**: Specific test for Trade Date validation logic  
**Usage**: `python test/test_trade_date_validation.py`  
**What it does**:
- Tests Trade Date specific validation scenarios
- Legacy test script for development

### `simple_test.py`
**Purpose**: Basic system functionality test  
**Usage**: `python test/simple_test.py`  
**What it does**:
- Simple test script for basic system verification
- Minimal test for development purposes

### `run_tests.sh`
**Purpose**: Shell script to run multiple tests  
**Usage**: `bash test/run_tests.sh` or `./test/run_tests.sh`  
**What it does**:
- Executes multiple test scripts in sequence
- Provides automated testing workflow
- Useful for continuous integration or batch testing

## Recommended Testing Workflow

When troubleshooting the DQ Validation System, use these scripts in this order:

### 1. Database Connectivity
```bash
python test/test_connection.py
```
Verify that all databases are accessible.

### 2. Graph Data Verification
```bash
python test/test_graph_data.py
```
Ensure Neo4j has all required CDEs and DQ rules.

### 3. MySQL Data Verification
```bash
python test/debug_mysql_data.py
```
Check that MySQL databases contain expected test data.

### 4. Validation Logic Testing
```bash
python test/test_validation_direct.py
```
Verify that validation logic correctly detects violations.

### 5. Full Workflow Testing
```bash
python dq_main.py --uitids="UIT-0001-ABC,UIT-0002-XYZ,UIT-0003-DEF"
```
Test the complete CrewAI workflow.

## Expected Results

For the test UITIDs (UIT-0001-ABC, UIT-0002-XYZ, UIT-0003-DEF), the system should detect exactly **3 violations**:

1. **UIT-0002-XYZ**: Quantity = -15 (negative) in Trade System
2. **UIT-0003-DEF**: Symbol = NULL in Settlement System  
3. **UIT-0001-ABC**: Trade Date = NULL in Reporting System

If any debug script doesn't show these expected results, there's a configuration or data issue that needs to be resolved before the main workflow will function correctly.

## Notes

- All debug scripts include detailed output to help identify issues
- Scripts are designed to be run independently without affecting the main system
- Use these tools whenever making changes to database configurations or validation logic
- The test folder keeps testing tools organized and separate from production code 