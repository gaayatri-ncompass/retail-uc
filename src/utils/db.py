from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
import pandas as pd
import logging

logging.basicConfig(
    filename='db_operations.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DB:
    def __init__(self, host, user, password, database, port):
        self.__host = host
        self.user = user
        self.__password = password
        self.__database = database
        self.__port = port
        self.engine = None

    def connect(self):
        try:
            url = URL.create(
                drivername="mysql+mysqlconnector",
                username=self.user,
                password=self.__password,
                host=self.__host,
                port=self.__port,
                database=self.__database
            )
            self.engine = create_engine(url)
            logging.info("Database connection established.")
        except Exception as e:
            logging.error(f"Connection failed: {e}")

    def disconnect(self):
        if self.engine:
            self.engine.dispose()
            logging.info("Database connection closed.")
        else:
            logging.warning("No active connection to disconnect.")

    def execute_query(self, sql, params=None):
        if self.engine:
            try:
                with self.engine.connect() as conn:
                    with conn.begin():
                        result = conn.execute(text(sql), params or {})
                        logging.info(f"Executed query: {sql} with params: {params}")
                        return result
            except Exception as e:
                logging.error(f"Query execution failed: {e}")
                return None
        else:
            logging.warning("No active connection to execute query.")
            return None

    def query_df(self, sql, params=None):
        if self.engine:
            try:
                df = pd.read_sql_query(text(sql), con=self.engine, params=params)
                logging.info(f"Fetched {len(df)} rows from query: {sql}")
                return df
            except Exception as e:
                logging.error(f"Fetch failed: {e}")
                return None
        else:
            logging.warning("No active connection to fetch data.")
            return None

    def insert_to_table(self, table_name, data):
        try:
            columns = ", ".join(data.keys())
            placeholders = ", ".join([f":{key}" for key in data])
            sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            result = self.execute_query(sql, data)
            if result and result.rowcount > 0:
                logging.info(f"Inserted row into {table_name}: {data}")
                return "Row Inserted"
            else:
                logging.warning(f"No rows inserted into {table_name}.")
                return None
        except Exception as e:
            logging.error(f"Insert failed for {table_name}: {e}")
            return None

    def update_table(self, table_name, data, conditions):
        try:
            set_clause = ", ".join([f"{col} = :{col}" for col in data])
            where_clause = " AND ".join([f"{col} = :{col}" for col in conditions])
            sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
            params = {**data, **conditions}
            result = self.execute_query(sql, params)
            if result:
                logging.info(f"Updated {result.rowcount} rows in {table_name} with {data}")
                return result.rowcount
            else:
                logging.warning(f"No rows updated in {table_name}.")
                return None
        except Exception as e:
            logging.error(f"Update failed for {table_name}: {e}")
            return None

    def delete_table(self, table_name, conditions):
        try:
            where_clause = " AND ".join([f"{col} = :{col}" for col in conditions])
            sql = f"DELETE FROM {table_name} WHERE {where_clause}"
            result = self.execute_query(sql, conditions)
            if result:
                logging.info(f"Deleted {result.rowcount} rows from {table_name} with conditions: {conditions}")
                return result.rowcount
            else:
                logging.warning(f"No rows deleted from {table_name}.")
                return None
        except Exception as e:
            logging.error(f"Delete failed for {table_name}: {e}")
            return None

    def read_table(self, table_name):
        if self.engine:
            try:
                df = pd.read_sql_table(table_name, con=self.engine)
                logging.info(f"Read {len(df)} rows from table {table_name}.")
                return df
            except Exception as e:
                logging.error(f"Read failed for table {table_name}: {e}")
                return None
        else:
            logging.warning("Connection not found for reading table.")
            return None

    def df_to_sql(self, df, table_name, index=False):
        if self.engine:
            try:
                df.to_sql(name=table_name, con=self.engine, if_exists='append', index=index)
                logging.info(f"Inserted {len(df)} rows into table '{table_name}'.")
                return True
            except Exception as e:
                logging.error(f"to_sql failed for table {table_name}: {e}")
                return False
        else:
            logging.warning("No active connection to write data.")
            return False