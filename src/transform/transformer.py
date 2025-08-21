import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from configs.db_config import get_staging_db_connector
from src.utils.exceptions import TransformationError, DatabaseError
from src.utils.schema_manager import extract_staging_tables_schema, get_metadata_value
from src.utils.logger import get_logger

logger = get_logger("TRANSFORMER")


def extract_incremental_data(staging_db, table_name, schema_config):
    staging_table = schema_config['staging_table']
    metadata_column = schema_config['metadata_column']
    last_value = get_metadata_value(staging_db, table_name, schema_config)

    query = f"SELECT * FROM {staging_table} WHERE {metadata_column} > :metadata ORDER BY {metadata_column}"
    df = staging_db.run_query_with_params(query, {'metadata': last_value})
    return df if df is not None else pd.DataFrame()


def get_date_key_from_date(date_value):
    if pd.isna(date_value):
        return None

    if isinstance(date_value, str):
        date_value = pd.to_datetime(date_value, errors='coerce')

    if pd.isna(date_value):
        return None

    return int(date_value.strftime('%Y%m%d'))


def clean_data_by_schema(df, table_name, schema_config):
    if df.empty:
        return df

    columns_info = schema_config['columns']
    key_column = schema_config['key_column']

    if key_column and key_column in df.columns:
        df = df.drop_duplicates(subset=[key_column])

    for column, col_info in columns_info.items():
        if column not in df.columns:
            continue

        data_type = col_info['data_type']

        if data_type in ['date', 'datetime', 'timestamp'] or 'date' in column.lower():
            df[column] = pd.to_datetime(df[column], errors='coerce')

            if df[column].dtype == 'object':
                df[column] = pd.to_datetime(df[column])

            # For sales table, create a date_key column for easier joins with dimdate
            if table_name == 'sales' and column == 'sale_date':
                df['sale_date_key'] = df[column].apply(get_date_key_from_date)

            if col_info['is_nullable'] == 'NO':
                initial_count = len(df)
                df = df.dropna(subset=[column])
                dropped = initial_count - len(df)
                if dropped > 0:
                    logger.warning(
                        f"Dropped {dropped} records with invalid {column} in {table_name}")

        elif data_type in ['varchar', 'char', 'text', 'string']:
            df.loc[:, column] = df[column].astype(str).str.strip()

            if 'email' in column.lower():
                df.loc[:, column] = df[column].str.lower()

            if 'phone' in column.lower():
                df.loc[:, column] = df[column].str.replace(
                    r'[^\d+]', '', regex=True)

        elif data_type in ['int', 'bigint', 'decimal', 'float', 'double', 'numeric']:
            df.loc[:, column] = pd.to_numeric(df[column], errors='coerce')

            if col_info['is_nullable'] == 'NO' and column != key_column:
                initial_count = len(df)
                df = df.dropna(subset=[column])
                dropped = initial_count - len(df)
                if dropped > 0:
                    logger.warning(
                        f"Dropped {dropped} records with invalid {column} in {table_name}")

    if table_name == 'sales':
        if 'payment_type' not in df.columns:
            df['payment_type'] = 'Credit Card'
        else:
            df.loc[:, 'payment_type'] = df['payment_type'].fillna(
                'Credit Card')

        if 'channel' not in df.columns:
            df['channel'] = 'In-Store'
        else:
            df.loc[:, 'channel'] = df['channel'].fillna('In-Store')

    return df


def create_promotion_dimension():
    return pd.DataFrame()


def transform_data():
    logger.info(
        "Starting incremental data transformation using metadata")

    staging_db = get_staging_db_connector()
    staging_db.connect()

    try:
        logger.info("Extracting table schema from staging database")
        tables_config = extract_staging_tables_schema()
        logger.info(
            f"Found {len(tables_config)} staging tables: {list(tables_config.keys())}")

        logger.info(
            "Reading incremental data from staging tables using metadata")
        transformed_data = {}

        for table_name, schema_config in tables_config.items():
            logger.info(f"Processing {table_name} data")

            raw_df = extract_incremental_data(
                staging_db, table_name, schema_config)
            cleaned_df = clean_data_by_schema(
                raw_df, table_name, schema_config)
            transformed_data[table_name] = cleaned_df

            logger.data_summary(table_name, len(cleaned_df), "transformed")

        logger.info("Creating dimensions")
        transformed_data['promotions'] = create_promotion_dimension()
        logger.success("Promotion dimension created")

        logger.success("Data transformation completed")
        return {
            'data': transformed_data,
            'tables_config': tables_config
        }

    except Exception as e:
        logger.error(f"Transformation process failed: {str(e)}")
        raise TransformationError(
            f"Transformation process failed: {str(e)}", "TRF003")
    finally:
        staging_db.disconnect()


def run_transformation():
    return transform_data()
