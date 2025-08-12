import pandas as pd
from sqlalchemy import create_engine, text
from .exceptions import DatabaseError


class DBConnector:

    def __init__(self, host, user, password, database):
        self.host = host or 'localhost'
        self.user = user or 'root'
        self.password = password or 'deva'
        self.database = database or 'stagingdb'
        self.engine = None

    def connect(self):

        if not self.engine:
            try:
                conn_str = f"mysql+pymysql://{self.user}:{self.password}@{self.host}/{self.database}"
                self.engine = create_engine(conn_str)
                print(f"Connection successful to database '{self.database}'")
            except Exception as e:
                raise DatabaseError(
                    f"Failed to connect to database '{self.database}': {str(e)}", "DB_CONN_001")

    def disconnect(self):

        if self.engine:
            self.engine.dispose()
            self.engine = None
            print("Connection closed.")

    def run_query(self, sql_query):

        self.connect()
        if not self.engine:
            print("ERROR: Query aborted. No database connection.")
            return None
        try:
            return pd.read_sql_query(text(sql_query), self.engine)
        except Exception as e:
            print(f"ERROR: Query failed: {e}")
            return None

    def execute_query(self, sql_query):

        self.connect()
        if not self.engine:
            print("ERROR: Query aborted. No database connection.")
            return False
        try:
            with self.engine.connect() as connection:
                connection.execute(text(sql_query))
                connection.commit()
            return True
        except Exception as e:
            print(f"ERROR: Query failed: {e}")
            return False
