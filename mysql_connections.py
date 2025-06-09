import mysql.connector
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass
from mysql_config import MYSQL_CONFIGS, TRADE_TABLE_NAME, CDE_COLUMN_MAPPINGS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    host: str
    port: int
    database: str
    user: str
    password: str
    system_name: str

class MySQLConnectionManager:
    def __init__(self):
        # Load configurations from config file
        self.db_configs = {}
        for system_name, config in MYSQL_CONFIGS.items():
            self.db_configs[system_name] = DatabaseConfig(
                host=config['host'],
                port=config['port'],
                database=config['database'],
                user=config['user'],
                password=config['password'],
                system_name=system_name
            )
        self.connections = {}

    def update_config(self, system_name: str, config: DatabaseConfig):
        """Update database configuration for a specific system"""
        self.db_configs[system_name] = config

    def connect_to_system(self, system_name: str) -> Optional[mysql.connector.MySQLConnection]:
        """Connect to a specific system's MySQL database"""
        if system_name not in self.db_configs:
            logger.error(f"No configuration found for system: {system_name}")
            return None

        config = self.db_configs[system_name]
        try:
            connection = mysql.connector.connect(
                host=config.host,
                port=config.port,
                database=config.database,
                user=config.user,
                password=config.password
            )
            self.connections[system_name] = connection
            logger.info(f"Successfully connected to {system_name} database")
            return connection
        except mysql.connector.Error as e:
            logger.error(f"Failed to connect to {system_name}: {str(e)}")
            return None

    def connect_all_systems(self) -> Dict[str, mysql.connector.MySQLConnection]:
        """Connect to all three systems and return active connections"""
        active_connections = {}
        for system_name in self.db_configs.keys():
            connection = self.connect_to_system(system_name)
            if connection:
                active_connections[system_name] = connection
        return active_connections

    def execute_query(self, system_name: str, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a query on a specific system's database"""
        connection = self.connections.get(system_name)
        if not connection:
            connection = self.connect_to_system(system_name)
            if not connection:
                return []

        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            results = cursor.fetchall()
            cursor.close()
            return results
        except mysql.connector.Error as e:
            logger.error(f"Query execution failed on {system_name}: {str(e)}")
            logger.error(f"Query was: {query}")
            return []

    def get_all_uitids(self, limit: int = None) -> List[str]:
        """Get all unique uitids across all systems"""
        all_uitids = set()
        
        for system_name in self.db_configs.keys():
            query = f"SELECT DISTINCT uitid FROM {TRADE_TABLE_NAME} WHERE uitid IS NOT NULL"
            if limit:
                query += f" LIMIT {limit}"
            
            results = self.execute_query(system_name, query)
            for row in results:
                all_uitids.add(str(row['uitid']))
        
        return sorted(list(all_uitids))

    def get_cde_value(self, system_name: str, uitid: str, cde_column_name: str) -> Any:
        """Get the value of a specific CDE for a given uitid in a system"""
        # Handle column mappings that differ per system
        actual_column = cde_column_name
        if isinstance(cde_column_name, dict):
            actual_column = cde_column_name.get(system_name)
            if actual_column is None:
                logger.warning(f"Column not available in {system_name}")
                return None
        
        query = f"SELECT {actual_column} FROM {TRADE_TABLE_NAME} WHERE uitid = %s"
        results = self.execute_query(system_name, query, (uitid,))
        
        if results:
            return results[0].get(actual_column)
        return None

    def validate_dq_rule(self, system_name: str, uitid: str, cde_column_name: str, 
                        rule_type: str, rule_description: str) -> Dict[str, Any]:
        """Validate a specific DQ rule for a given uitid and CDE in a system"""
        # Check if column is available in this system
        if isinstance(cde_column_name, dict):
            actual_column = cde_column_name.get(system_name)
            if actual_column is None:
                # Column not available in this system
                return {
                    'system_name': system_name,
                    'uitid': uitid,
                    'cde_column': cde_column_name,
                    'value': None,
                    'violation': None,  # Special marker for "not available"
                    'rule_type': rule_type,
                    'rule_description': rule_description,
                    'column_available': False
                }
        
        value = self.get_cde_value(system_name, uitid, cde_column_name)
        
        violation = False
        
        if rule_type == 'NOT_NULL':
            violation = value is None or (isinstance(value, str) and value.strip() == '')
        elif rule_type == 'POSITIVE_VALUE':
            if value is None:
                violation = True
            else:
                try:
                    num_value = float(value)
                    violation = num_value <= 0
                except (ValueError, TypeError):
                    violation = True
        elif rule_type == 'ENUM_VALUE':
            if value is None:
                violation = True
            elif 'BUY or SELL' in rule_description:
                violation = str(value).upper() not in ['BUY', 'SELL']
        
        return {
            'system_name': system_name,
            'uitid': uitid,
            'cde_column': cde_column_name,
            'value': value,
            'violation': violation,
            'rule_type': rule_type,
            'rule_description': rule_description,
            'column_available': True
        }

    def close_all_connections(self):
        """Close all database connections"""
        for system_name, connection in self.connections.items():
            try:
                if connection.is_connected():
                    connection.close()
                    logger.info(f"Closed connection to {system_name}")
            except Exception as e:
                logger.error(f"Error closing connection to {system_name}: {str(e)}")
        self.connections.clear()

    def test_connections(self) -> Dict[str, bool]:
        """Test connectivity to all systems"""
        test_results = {}
        for system_name in self.db_configs.keys():
            connection = self.connect_to_system(system_name)
            if connection:
                try:
                    cursor = connection.cursor()
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                    cursor.close()
                    test_results[system_name] = True
                    logger.info(f"Connection test passed for {system_name}")
                except Exception as e:
                    test_results[system_name] = False
                    logger.error(f"Connection test failed for {system_name}: {str(e)}")
            else:
                test_results[system_name] = False
        
        return test_results 