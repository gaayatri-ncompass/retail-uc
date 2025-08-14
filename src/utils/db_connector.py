import pandas as pd
from sqlalchemy import create_engine, text
from .exceptions import DatabaseError
from logger import get_logger
logger = get_logger("DB")


class DBConnector:

    def __init__(self, host, user, password, database):
        self.host = host or 'localhost'
        self.user = user or 'root'
        self.password = password or 'deva'
        self.database = database or 'stagingdb'
        self.engine = None
        logger.debug(f"Initialized DBConnector for database: {self.database}")

    def connect(self):

        if not self.engine:
            try:
                conn_str = f"mysql+pymysql://{self.user}:{self.password}@{self.host}/{self.database}"
                self.engine = create_engine(conn_str)
                logger.info(
                    f"Connection successful to database '{self.database}'")
            except Exception as e:
                error_msg = f"Failed to connect to database '{self.database}': {str(e)}"
                logger.error(error_msg)
                raise DatabaseError(error_msg, "DB_CONN_001")

    def disconnect(self):

        if self.engine:
            self.engine.dispose()
            self.engine = None
            logger.info("Database connection closed.")

    def run_query(self, sql_query):

        self.connect()
        if not self.engine:
            logger.error("Query aborted. No database connection.")
            return None
        try:
            logger.debug(f"Executing query: {sql_query[:100]}...")
            result = pd.read_sql_query(text(sql_query), self.engine)
            logger.debug(
                f"Query executed successfully, returned {len(result)} rows")
            return result
        except Exception as e:
            error_msg = f"Query failed: {e}"
            logger.error(error_msg)
            return None

    def execute_query(self, sql_query):

        self.connect()
        if not self.engine:
            logger.error("Query aborted. No database connection.")
            return False
        try:
            logger.debug(f"Executing command: {sql_query[:100]}...")
            with self.engine.connect() as connection:
                connection.execute(text(sql_query))
                connection.commit()
            logger.debug("Command executed successfully")
            return True
        except Exception as e:
            error_msg = f"Query execution failed: {e}"
            logger.error(error_msg)
            return False
