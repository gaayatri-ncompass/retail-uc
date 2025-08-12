import pandas as pd
from src.utils.validator import DataValidator
from src.utils.validation_schema import schemas
from src.utils.logger import logger
from src.utils.error_handler import handle_error
from src.extract import csv_loader


TABLE_METADATA_CONFIG = {
    "customers": {
        "incremental_column": "customer_id",
        "key_type": "id"
    },
    "inventory": {
        "incremental_column": "last_updated",
        "key_type": "timestamp"
    },
    "sales": {
        "incremental_column": "sale_id",
        "key_type": "id"
    },
    "stores": {
        "incremental_column": "store_id",
        "key_type": "id"
    },
    "suppliers": {
        "incremental_column": "supplier_id",
        "key_type": "id"
    },
    "products": {
        "incremental_column": "product_id",
        "key_type": "id"
    },
    "dimdate": {
        "incremental_column": "date",
        "key_type": "timestamp"
    }
}


def get_max_key(df, column, key_type):
    if key_type == "id":
        numeric_series = df[column].str.extract(r'(\d+)', expand=False).astype(int)
        max_index = numeric_series.idxmax()
        return df.loc[max_index, column]
    elif key_type == "timestamp":
        return df[column].max()
    else:
        raise ValueError(f"Unsupported key type: {key_type}")
    

def get_last_key(db, table_name):
    sql = "SELECT last_loaded_key FROM metadata WHERE table_name = :table_name"
    result = db.query_df(sql, {"table_name": table_name})
    if result is not None and not result.empty:
        return str(result.iloc[0]["last_loaded_key"])
    return None


def update_last_key(db, table_name, last_key):
    exists_sql = "SELECT COUNT(*) AS count FROM metadata WHERE table_name = :table_name"
    result = db.query_df(exists_sql, {"table_name": table_name})
    if result.iloc[0]["count"] > 0:
        update_sql = """
            UPDATE metadata SET last_loaded_key = :last_key
            WHERE table_name = :table_name
        """
        db.execute_query(update_sql, {"table_name": table_name, "last_key": str(last_key)})
    else:
        insert_sql = """
            INSERT INTO metadata (table_name, last_loaded_key)
            VALUES (:table_name, :last_key)
        """
        db.execute_query(insert_sql, {"table_name": table_name, "last_key": str(last_key)})


def load_csv_full(db, df, table_name):
    try:
        config = TABLE_METADATA_CONFIG.get(table_name)
        if not config:
            raise ValueError(f"No metadata found for table: {table_name}")

        pk_column = config["incremental_column"]
        key_type = config["key_type"]

        df[pk_column] = df[pk_column].astype(str)

        if key_type == "id":
            df["num_id"] = df[pk_column].str.extract(r'(\d+)').astype(int)
            df = df.sort_values(by="num_id").drop(columns="num_id")
        else:
            df = df.sort_values(by=pk_column)

        db.df_to_sql(df, table_name)
        last_key = get_max_key(df, pk_column, key_type)
        update_last_key(db, table_name, last_key)
        logger.info(f"Full load complete. Loaded {len(df)} rows into {table_name}")
    except Exception as e:
        handle_error(f'Full load failed for {table_name} : {e}')


def load_csv_incremental(db,df,table_name):
    try:
        if table_name not in TABLE_METADATA_CONFIG:
            logger.warning(f"No metadata config found for {table_name}")
            return
        config = TABLE_METADATA_CONFIG[table_name]
        column = config["incremental_column"]
        key_type = config["key_type"]
        last_key = get_last_key(db, table_name)
        if key_type == "id":
            df[column] = df[column].astype(str)
            if last_key is not None:
                df = df[df[column].str.extract(r'(\d+)', expand=False).astype(int) > int(last_key)]
        elif key_type == "timestamp":
            df[column] = pd.to_datetime(df[column])
            if last_key is not None:
                last_key_dt = pd.to_datetime(last_key)
                df = df[df[column] > last_key_dt]
        else:
            raise ValueError(f"Unsupported key type: {key_type}")
        df = df.sort_values(by=column)
        if df.empty:
            logger.info(f"No new rows to insert for {table_name}")
            return
        
        max_key = get_max_key(df, column, key_type)
        db.df_to_sql(df, table_name)
        update_last_key(db, table_name, max_key)
        logger.info(f"Loaded {len(df)} new rows into {table_name}")
    except Exception as e:
        handle_error(f"Incremental Loading failed for {table_name} : {e}")


def load_csv(db, csv_path, table_name):
    try:
        print(f"\nStarting Extraction for table: {table_name}")

        if table_name not in TABLE_METADATA_CONFIG:
            raise ValueError(f"No metadata config found for table: {table_name}")
        
        df = csv_loader.extract_csv(csv_path)

        validator = DataValidator(schemas[table_name])
        validator.validate(df)
        validator.summary()

        if validator.has_errors():
            error_df = validator.get_error_dataframe()
            error_df.to_csv(f"{table_name}_validation_errors.csv", index=False)
            handle_error(f"Validation failed for {table_name}. Errors saved to CSV.")
            return
        
        print("Validation Successful!")
        print(f"\n Starting load for table: {table_name}")

        last_key = get_last_key(db, table_name)

        if last_key is None:
            print("No previous load detected. Performing full load...")
            load_csv_full(db, df, table_name)
        else:
            print(f"Last loaded key found: {last_key}. Performing incremental load...")
            load_csv_incremental(db, df, table_name)

        print(f"Load complete for table: {table_name}")
    except Exception as e:
        handle_error(f"Loading failed for table: {table_name}",e)