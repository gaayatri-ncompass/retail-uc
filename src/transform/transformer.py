import pandas as pd
import numpy as np
from datetime import datetime
from src.utils.exceptions import TransformationError
from src.utils.logger import get_logger
from configs.db_config import get_warehouse_db_connector
from configs.metadata_config import get_table_mapping
from src.transform.fact_transformer import transform_sales_fact, transform_inventory_fact

logger = get_logger("TRANSFORMER")


def get_schema_and_clean_data(df, table_name):
    """Get schema and clean data based on warehouse schema"""
    table_mapping = get_table_mapping()
    warehouse_table = table_mapping.get(table_name, table_name)
    warehouse_db = get_warehouse_db_connector()
    warehouse_db.connect()

    try:
        schema_query = """SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS 
                         WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :table_name"""
        schema_df = warehouse_db.query(
            schema_query, {"table_name": warehouse_table})

        if schema_df is not None and not schema_df.empty:
            schema_types = dict(
                zip(schema_df['COLUMN_NAME'], schema_df['DATA_TYPE']))

            # Clean columns based on schema types
            for column in df.columns:
                if column in schema_types:
                    data_type = schema_types[column]
                    try:
                        if data_type in ['varchar', 'text', 'char']:
                            df[column] = df[column].astype(str).str.strip()
                            if 'email' in column.lower():
                                df[column] = df[column].str.lower()
                        elif data_type in ['int', 'bigint', 'decimal', 'float', 'double']:
                            df[column] = pd.to_numeric(
                                df[column], errors='coerce')
                        elif data_type in ['date', 'datetime', 'timestamp']:
                            df[column] = pd.to_datetime(
                                df[column], errors='coerce')
                    except Exception as e:
                        logger.warning(f"Failed to clean column {column}: {e}")
        return df
    except Exception as e:
        logger.warning(f"Could not get schema for {warehouse_table}: {e}")
        return df
    finally:
        warehouse_db.disconnect()


def clean_and_deduplicate(df, table_name):
    """Clean data and remove duplicates with date key handling"""
    if df.empty:
        return df

    logger.info(f"Transforming {table_name} with {len(df)} records")

    # Get schema and clean data
    df = get_schema_and_clean_data(df, table_name)

    # Add date keys and defaults for sales
    if table_name == 'sales':
        # Add date keys for any date columns
        for col in df.columns:
            if 'date' in col.lower() and not col.endswith('_key'):
                try:
                    date_series = pd.to_datetime(df[col], errors='coerce')
                    df[f"{col}_key"] = date_series.dt.strftime(
                        '%Y%m%d').astype('Int64')
                    logger.info(f"Added {col}_key column for {table_name}")
                except Exception as e:
                    logger.warning(f"Failed to create date key for {col}: {e}")

        # Add default values
        for col, default in [('payment_type', 'Credit Card'), ('channel', 'InStore')]:
            if col not in df.columns:
                df[col] = default

    # Remove duplicates and nulls
    pk_columns = [col for col in df.columns if col.endswith('_id')]
    if pk_columns:
        primary_key = pk_columns[0]
        initial_count = len(df)

        # Remove nulls for dimension tables
        if table_name in ['customers', 'products', 'stores', 'suppliers']:
            df = df[df[primary_key].notna()]
            null_removed = initial_count - len(df)
            if null_removed > 0:
                logger.info(
                    f"Removed {null_removed} records with NULL {primary_key}")

        # Remove duplicates
        df = df.drop_duplicates(subset=[primary_key])
        duplicates_removed = initial_count - len(df)
        if duplicates_removed > 0:
            logger.info(
                f"Removed {duplicates_removed} duplicates from {table_name}")

    logger.info(f"Transformed {table_name}: {len(df)} records")
    return df


def transform_staging_data(staging_data):
    """Transform dimension tables - basic transformations only"""
    logger.info("Starting data transformation")
    if not staging_data:
        return {}

    try:
        transformed_data = {}
        for table_name, df in staging_data.items():
            transformed_data[table_name] = clean_and_deduplicate(
                df, table_name)

        total_records = sum(len(df) for df in transformed_data.values())
        logger.success(
            f"Transformation completed: {total_records} records across {len(transformed_data)} tables")
        return transformed_data

    except Exception as e:
        logger.error(f"Transformation failed: {e}")
        raise TransformationError(f"Transformation failed: {e}")


def transform_facts_after_dimensions(staging_data, db):
    """Transform fact tables after dimensions are loaded - with dimension key mapping"""
    logger.info("Starting fact transformations with dimension key mapping")

    try:
        fact_data = {}

        # Transform facts with dimension keys
        if 'sales' in staging_data:
            sales_fact_df = transform_sales_fact(db, staging_data['sales'])
            if not sales_fact_df.empty:
                fact_data['sales_fact'] = sales_fact_df
                logger.info(
                    f"Sales fact transformation: {len(sales_fact_df)} records")

        if 'inventory' in staging_data:
            inventory_fact_df = transform_inventory_fact(
                db, staging_data['inventory'])
            if not inventory_fact_df.empty:
                fact_data['inventory_fact'] = inventory_fact_df
                logger.info(
                    f"Inventory fact transformation: {len(inventory_fact_df)} records")

        return fact_data

    except Exception as e:
        logger.error(f"Fact transformation failed: {e}")
        raise TransformationError(f"Fact transformation failed: {e}")
