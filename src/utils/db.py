from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
import pandas as pd
import logging

class DB:
    def __init__(self, host, user, password, database, port):
        self.__host = host
        self.user = user
        self.__password = password
        self.__database = database
        self.__port = port
        self.engine = None

    def connect_to_engine(self):
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
            print("Database connection established.")
        except Exception as e:
            print(f"Connection failed: {e}")

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
                        print(f"Executed query: {sql} with params: {params}")
                        return result
            except Exception as e:
                print(f"Query execution failed: {e}")
                return None
        else:
            logging.warning("No active connection to execute query.")
            return None

    def query_df(self, sql, params=None):
        if self.engine:
            try:
                with self.engine.connect() as conn:
                    with conn.begin():
                        df = pd.read_sql_query(text(sql), con=self.engine, params=params)
                        print(f"Fetched {len(df)} rows from query: {sql}")
                        return df
            except Exception as e:
                print(f"Fetch failed: {e}")
                return None
        else:
            print("No active connection to fetch data.")
            return None

    def insert_to_table(self, table_name, data):
        try:
            columns = ", ".join(data.keys())
            placeholders = ", ".join([f":{key}" for key in data])
            sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            result = self.execute_query(sql, data)
            if result and result.rowcount > 0:
                print(f"Inserted row into {table_name}: {data}")
                return "Row Inserted"
            else:
                print(f"No rows inserted into {table_name}.")
                return None
        except Exception as e:
            print(f"Insert failed for {table_name}: {e}")
            return None

    def update_table(self, table_name, data, conditions):
        try:
            set_clause = ", ".join([f"{col} = :{col}" for col in data])
            where_clause = " AND ".join([f"{col} = :{col}" for col in conditions])
            sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
            params = {**data, **conditions}
            result = self.execute_query(sql, params)
            if result:
                print(f"Updated {result.rowcount} rows in {table_name} with {data}")
                return result.rowcount
            else:
                print(f"No rows updated in {table_name}.")
                return None
        except Exception as e:
            print(f"Update failed for {table_name}: {e}")
            return None

    def delete_table(self, table_name, conditions):
        try:
            where_clause = " AND ".join([f"{col} = :{col}" for col in conditions])
            sql = f"DELETE FROM {table_name} WHERE {where_clause}"
            result = self.execute_query(sql, conditions)
            if result:
                print(f"Deleted {result.rowcount} rows from {table_name} with conditions: {conditions}")
                return result.rowcount
            else:
                print(f"No rows deleted from {table_name}.")
                return None
        except Exception as e:
            print(f"Delete failed for {table_name}: {e}")
            return None

    def read_table(self, table_name):
        if self.engine:
            try:
                df = pd.read_sql_table(table_name, con=self.engine)
                print(f"Read {len(df)} rows from table {table_name}.")
                return df
            except Exception as e:
                print(f"Read failed for table {table_name}: {e}")
                return None
        else:
            print("Connection not found for reading table.")
            return None

    def df_to_sql(self, df, table_name, index=False):
        if self.engine:
            try:
                with self.engine.connect() as connection:
                    df.to_sql(name=table_name, con=connection, if_exists='append', index=index)
                    print(f"Inserted {len(df)} rows into table '{table_name}'.")
                return True
            except Exception as e:
                print(f"to_sql failed for table {table_name}: {e}")
                return False
        else:
            print("No active connection to write data.")
            return False
        
    def get_last_processed_id(self, asset_name: str, source_table: str, target_table: str) -> int:
        """Get the last processed ID for a given asset and table pair."""
        sql = '''
            SELECT last_processed_id FROM asset_metadata
            WHERE asset_name = :asset_name
            AND source_table = :source_table
            AND target_table = :target_table
        '''
        params = {
            "asset_name": asset_name,
            "source_table": source_table,
            "target_table": target_table
        }
        result = self.query_df(sql, params)
        if result is not None and not result.empty:
            return result.iloc[0]["last_processed_id"] or 0
        return 0

    def update_last_processed_id(self, asset_name: str, source_table: str, target_table: str, new_id: int):
        check_sql = '''
            SELECT COUNT(*) as count FROM asset_metadata
            WHERE asset_name = :asset_name
            AND source_table = :source_table
            AND target_table = :target_table
        '''
        params = {
            "asset_name": asset_name,
            "source_table": source_table,
            "target_table": target_table
        }
        result = self.query_df(check_sql, params)

        if result.iloc[0]["count"] == 0:
            # Insert new row
            insert_sql = '''
                INSERT INTO asset_metadata (asset_name, source_table, target_table, last_processed_id, last_updated)
                VALUES (:asset_name, :source_table, :target_table, :last_processed_id, CURRENT_TIMESTAMP)
            '''
            params["last_processed_id"] = new_id
            self.execute_query(insert_sql, params)
        else:
            # Update existing row
            update_sql = '''
                UPDATE asset_metadata
                SET last_processed_id = :last_processed_id,
                    last_updated = CURRENT_TIMESTAMP
                WHERE asset_name = :asset_name
                AND source_table = :source_table
                AND target_table = :target_table
            '''
            params["last_processed_id"] = new_id
            self.execute_query(update_sql, params)


    def update_metadata(self, asset_name: str, source_table: str, target_table: str, last_id: int):
        """Update metadata for a given asset and table pair."""
        sql = '''
            UPDATE asset_metadata
            SET last_processed_id = :last_processed_id,
                last_updated = CURRENT_TIMESTAMP
            WHERE asset_name = :asset_name
            AND source_table = :source_table
            AND target_table = :target_table
        '''
        params = {
            "asset_name": asset_name,
            "source_table": source_table,
            "target_table": target_table,
            "last_processed_id": last_id
        }
        self.execute_query(sql, params)

