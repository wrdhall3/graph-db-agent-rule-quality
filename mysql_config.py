"""
MySQL Database Configuration
Update these settings according to your actual MySQL database configurations
"""

# Database configurations for the three systems
MYSQL_CONFIGS = {
    'Trade System': {
        'host': 'localhost',
        'port': 3306,
        'database': 'trade_system',
        'user': 'root',
        'password': 'Ridgewood2024'
    },
    'Settlement System': {
        'host': 'localhost',
        'port': 3306,
        'database': 'settlement_system',
        'user': 'root',
        'password': 'Ridgewood2024'
    },
    'Reporting System': {
        'host': 'localhost',
        'port': 3306,
        'database': 'reporting_system',
        'user': 'root',
        'password': 'Ridgewood2024'
    }
}

# Table name containing trade data (same across all systems)
TRADE_TABLE_NAME = 'trade'

# Column mappings for CDEs (MySQL column names)
# Note: Some columns have different names across systems
CDE_COLUMN_MAPPINGS = {
    'Trade Date': {  # Available in all systems
        'Trade System': 'trade_date',
        'Settlement System': 'trade_date',  # Available in settlement system
        'Reporting System': 'trade_date'
    },
    'Settlement Date': {  # Different column names per system
        'Trade System': 'settle_date',
        'Settlement System': 'settlement_date', 
        'Reporting System': 'settlement_date'
    },
    'Trade Amount': 'price',  # Using price field (same across all systems)
    'Net Amount': {  # Different column names per system
        'Trade System': 'net_amount',
        'Settlement System': 'net_amount',
        'Reporting System': 'notional_value'
    },
    'Trade Side': 'side',  # Same across all systems (ENUM: BUY/SELL)
    'Trade Currency': 'trade_currency',  # Same across all systems
    'Settlement Currency': 'settlement_currency',  # Same across all systems
    'Quantity': 'quantity',  # Same across all systems
    'UITID': 'uitid',  # Same across all systems
    'Symbol': {  # Different column names per system
        'Trade System': 'symbol',
        'Settlement System': 'symbol',
        'Reporting System': 'instrument_symbol'
    },
    'CUSIP': 'cusip',  # Same in trade_system and settlement_system
    'Counterparty': {  # Only in settlement and reporting systems
        'Trade System': None,  # Not available
        'Settlement System': 'counterparty_name',
        'Reporting System': 'counterparty_name'
    }
}

# Sample UITIDs for testing (can be overridden by user input)
SAMPLE_UITIDS = ['1', '2', '3', '4', '5']

# Default settings
DEFAULT_LIMIT = 10
DEFAULT_REPORT_FORMAT = 'table' 