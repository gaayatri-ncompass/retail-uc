import pandas as pd
from sqlalchemy import create_engine, text
from .exceptions import DatabaseError
from src.utils.logger import get_logger

logger = get_logger("DB")


class DBConnector:
    """Simplified database connector with unified query methods"""

    def __init__(self, host, user, password, database):
        self.host = host or 'localhost'
        self.user = user or 'root'
        self.password = password or 'deva'
        self.database = database or 'stagingdb'
        self.engine = None

    def connect(self):
        """Establish database connection"""
        if not self.engine:
            try:
                conn_str = f"mysql+pymysql://{self.user}:{self.password}@{self.host}:3306/{self.database}?charset=utf8mb4"
                self.engine = create_engine(conn_str, echo=False)

                # Test connection
                with self.engine.connect() as connection:
                    connection.execute(text("SELECT 1"))

                logger.info(
                    f"Connection successful to database '{self.database}'")
            except Exception as e:
                error_msg = f"Failed to connect to database '{self.database}': {str(e)}"
                logger.error(error_msg)
                raise DatabaseError(error_msg, "DB_CONN_001")

    def disconnect(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            logger.info("Database connection closed.")

    def query(self, sql_query, params=None, fetch_data=True):
        """
        Unified query method for all database operations

        Args:
            sql_query: SQL query string
            params: Query parameters (optional)
            fetch_data: True for SELECT queries, False for INSERT/UPDATE/DELETE

        Returns:
            DataFrame for SELECT queries, Boolean for DML queries
        """
        self.connect()
        try:
            if fetch_data:
                # SELECT queries - return DataFrame
                return pd.read_sql_query(text(sql_query), self.engine, params=params)
            else:
                # INSERT/UPDATE/DELETE queries - return success status
                with self.engine.connect() as connection:
                    connection.execute(text(sql_query), params or {})
                    connection.commit()
                return True
        except Exception as e:
            operation = "Query" if fetch_data else "Execution"
            logger.error(f"{operation} failed: {e}")
            return None if fetch_data else False

    def table_exists(self, table_name):
        """Check if table exists"""
        try:
            result = self.query(
                "SELECT COUNT(*) as table_count FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :table_name",
                {'table_name': table_name}
            )
            return result['table_count'].iloc[0] > 0 if result is not None else False
        except Exception as e:
            logger.error(
                f"Error checking table existence for {table_name}: {e}")
            return False

    # Backward compatibility methods
    def run_query(self, sql_query):
        """Backward compatibility for SELECT queries"""
        return self.query(sql_query, fetch_data=True)

    def run_query_with_params(self, sql_query, params=None):
        """Backward compatibility for parameterized SELECT queries"""
        return self.query(sql_query, params, fetch_data=True)

    def execute_query(self, sql_query):
        """Backward compatibility for DML queries"""
        return self.query(sql_query, fetch_data=False)

    def execute_query_with_params(self, sql_query, params=None):
        """Backward compatibility for parameterized DML queries"""
        return self.query(sql_query, params, fetch_data=False)

    def check_multiple_tables_exist(self, table_names):
        """Check existence of multiple tables"""
        try:
            return {table_name: self.table_exists(table_name) for table_name in table_names}
        except Exception as e:
            logger.error(f"Error checking multiple tables existence: {e}")
            return {table_name: False for table_name in table_names}
