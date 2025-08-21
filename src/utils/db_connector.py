import pandas as pd
from sqlalchemy import create_engine, text
from .exceptions import DatabaseError
from src.utils.logger import get_logger

logger = get_logger("DB")


class DBConnector:
    """Database connector class for handling MySQL connections and operations"""

    def __init__(self, host, user, password, database):
        """Initialize database connection parameters"""
        self.host = host or 'localhost'
        self.user = user or 'root'
        self.password = password or 'deva'
        self.database = database or 'stagingdb'
        self.engine = None

    # Connection Management Methods
    def connect(self):
        """Establish database connection"""
        if not self.engine:
            try:
                # Add port and connection parameters for better compatibility
                conn_str = f"mysql+pymysql://{self.user}:{self.password}@{self.host}:3306/{self.database}?charset=utf8mb4"
                self.engine = create_engine(conn_str, echo=False)

                # Test the connection
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

    # Query Execution Methods
    def run_query(self, sql_query):
        """Execute a SELECT query and return pandas DataFrame"""
        self.connect()
        if not self.engine:
            logger.error("Query aborted. No database connection.")
            return None
        try:
            result = pd.read_sql_query(text(sql_query), self.engine)
            return result
        except Exception as e:
            error_msg = f"Query failed: {e}"
            logger.error(error_msg)
            return None

    def run_query_with_params(self, sql_query, params=None):
        """Execute a parameterized SELECT query and return pandas DataFrame"""
        self.connect()
        if not self.engine:
            logger.error("Query aborted. No database connection.")
            return None
        try:
            result = pd.read_sql_query(
                text(sql_query), self.engine, params=params)
            return result
        except Exception as e:
            error_msg = f"Parameterized query failed: {e}"
            logger.error(error_msg)
            return None

    def execute_query(self, sql_query):
        """Execute an INSERT/UPDATE/DELETE query"""
        self.connect()
        if not self.engine:
            logger.error("Query aborted. No database connection.")
            return False
        try:
            with self.engine.connect() as connection:
                connection.execute(text(sql_query))
                connection.commit()
            return True
        except Exception as e:
            error_msg = f"Query execution failed: {e}"
            logger.error(error_msg)
            return False

    def execute_query_with_params(self, sql_query, params=None):
        """Execute a parameterized INSERT/UPDATE/DELETE query"""
        self.connect()
        if not self.engine:
            logger.error("Query aborted. No database connection.")
            return False
        try:
            with self.engine.connect() as connection:
                connection.execute(text(sql_query), params)
                connection.commit()
            return True
        except Exception as e:
            error_msg = f"Parameterized query execution failed: {e}"
            logger.error(error_msg)
            return False

    # Table Management Methods
    def table_exists(self, table_name):
        """Check if a table exists in the database"""
        self.connect()
        if not self.engine:
            logger.error("Query aborted. No database connection.")
            return False
        try:
            query = """
                SELECT COUNT(*) as table_count 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = :table_name
            """
            result = pd.read_sql_query(text(query), self.engine, params={
                                       'table_name': table_name})
            return result['table_count'].iloc[0] > 0
        except Exception as e:
            logger.error(
                f"Error checking table existence for {table_name}: {e}")
            return False

    def check_multiple_tables_exist(self, table_names):
        """Check existence of multiple tables"""
        self.connect()
        if not self.engine:
            logger.error("Query aborted. No database connection.")
            return {}

        result = {}
        try:
            for table_name in table_names:
                result[table_name] = self.table_exists(table_name)
            return result
        except Exception as e:
            logger.error(f"Error checking multiple tables existence: {e}")
            return {table_name: False for table_name in table_names}
