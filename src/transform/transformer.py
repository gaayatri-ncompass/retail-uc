import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.utils.config import get_staging_db_connector, get_warehouse_db_connector
from src.utils.exceptions import TransformationError, DatabaseError
from logger import get_logger

logger = get_logger("TRANSFORMER")


def get_staging_tables_schema(staging_db):

    tables_query = """
    SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME LIKE 'stg_%'
    ORDER BY TABLE_NAME, ORDINAL_POSITION
    """

    primary_keys_query = """
    SELECT TABLE_NAME, COLUMN_NAME
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = DATABASE()
    AND CONSTRAINT_NAME = 'PRIMARY'
    AND TABLE_NAME LIKE 'stg_%'
    """

    schema_info = staging_db.run_query(tables_query)
    primary_keys_info = staging_db.run_query(primary_keys_query)

    primary_keys_map = {}
    if primary_keys_info is not None and not primary_keys_info.empty:
        for _, row in primary_keys_info.iterrows():
            primary_keys_map[row['TABLE_NAME']] = row['COLUMN_NAME']

    tables_config = {}

    for _, row in schema_info.iterrows():
        table_name = row['TABLE_NAME']
        column_name = row['COLUMN_NAME']
        data_type = row['DATA_TYPE'].lower()

        business_table = table_name.replace('stg_', '')

        if business_table not in tables_config:
            tables_config[business_table] = {
                'staging_table': table_name,
                'columns': {},
                'key_column': None,
                'watermark_column': None
            }

        tables_config[business_table]['columns'][column_name] = {
            'data_type': data_type,
            'is_nullable': row['IS_NULLABLE']
        }

        if table_name in primary_keys_map and primary_keys_map[table_name] == column_name:
            tables_config[business_table]['key_column'] = column_name
            tables_config[business_table]['watermark_column'] = column_name
            logger.info(
                f"Found primary key for {business_table}: {column_name}")

        elif column_name in ['last_updated', 'updated_at', 'modified_date', 'created_at']:
            if not tables_config[business_table]['watermark_column']:
                tables_config[business_table]['watermark_column'] = column_name
                logger.info(
                    f"Found timestamp watermark for {business_table}: {column_name}")

    # Fallback: if no primary key or timestamp found, use first _id column as watermark
    for business_table, config in tables_config.items():
        if not config['watermark_column']:
            # Look for any column ending with _id as fallback
            for column_name in config['columns'].keys():
                if column_name.endswith('_id'):
                    config['watermark_column'] = column_name
                    config['key_column'] = column_name
                    logger.info(
                        f"Using fallback watermark for {business_table}: {column_name}")
                    break

            if not config['watermark_column']:
                logger.warning(
                    f"No suitable watermark column found for {business_table}")

    return tables_config


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

            # For sales table, also create a date_key column for easier joins with dimdate
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

            # handling for email
            if 'email' in column.lower():
                df.loc[:, column] = df[column].str.lower()

            #  handling for phone
            if 'phone' in column.lower():
                df.loc[:, column] = df[column].str.replace(
                    r'[^\d+]', '', regex=True)

        # Numeric columns
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


def get_watermark(staging_db, table_name, schema_config):

    staging_table = schema_config['staging_table']
    watermark_column = schema_config['watermark_column']

    watermark = staging_db.run_query(
        f"SELECT last_processed_id FROM etl_process_log WHERE table_name = '{staging_table}'"
    )

    if watermark is not None and not watermark.empty:
        return watermark.iloc[0]['last_processed_id']
    else:

        if watermark_column in ['last_updated', 'updated_at', 'modified_date', 'created_at']:
            return '1900-01-01 00:00:00'
        else:
            return ''


def extract_incremental_data(staging_db, table_name, schema_config):

    staging_table = schema_config['staging_table']
    watermark_column = schema_config['watermark_column']
    last_value = get_watermark(staging_db, table_name, schema_config)

    query = f"SELECT * FROM {staging_table} WHERE {watermark_column} > :watermark ORDER BY {watermark_column}"

    df = staging_db.run_query_with_params(query, {'watermark': last_value})
    return df if df is not None else pd.DataFrame()


def update_watermark(staging_db, table_name, schema_config, df):

    if df.empty:
        return

    staging_table = schema_config['staging_table']
    watermark_column = schema_config['watermark_column']

    latest_value = df[watermark_column].max()

    if watermark_column in ['last_updated', 'updated_at', 'modified_date', 'created_at']:

        if isinstance(latest_value, str):
            latest_value = pd.to_datetime(latest_value)

        latest_value = latest_value.strftime('%Y-%m-%d %H:%M:%S')

    result = staging_db.execute_query_with_params(
        "INSERT INTO etl_process_log (table_name, last_processed_id, last_updated) "
        "VALUES (:table_name, :latest_value, NOW()) "
        "ON DUPLICATE KEY UPDATE last_processed_id = :latest_value, last_updated = NOW()",
        {'table_name': staging_table, 'latest_value': latest_value}
    )

    if not result:
        raise DatabaseError(
            f"Failed to update watermark for {table_name}", f"DB_{table_name}")


def get_date_key_from_date(date_value):

    if pd.isna(date_value):
        return None

    if isinstance(date_value, str):
        date_value = pd.to_datetime(date_value, errors='coerce')

    if pd.isna(date_value):
        return None

    return int(date_value.strftime('%Y%m%d'))


def create_promotion_dimension():

    return pd.DataFrame()


def transform_data():

    logger.info(
        "Starting incremental data transformation using metadata watermarks...")

    staging_db = get_staging_db_connector()
    warehouse_db = get_warehouse_db_connector()

    try:
        staging_db.connect()
        warehouse_db.connect()

        logger.info("Extracting table schema from staging database...")
        tables_config = get_staging_tables_schema(staging_db)

        logger.info(
            f"Found {len(tables_config)} staging tables: {list(tables_config.keys())}")

        logger.info(
            "Reading incremental data from staging tables using metadata...")

        transformed_data = {}

        for table_name, schema_config in tables_config.items():
            try:
                logger.info(f"Processing {table_name} data...")

                raw_df = extract_incremental_data(
                    staging_db, table_name, schema_config)

                cleaned_df = clean_data_by_schema(
                    raw_df, table_name, schema_config)

                transformed_data[table_name] = cleaned_df
                logger.info(
                    f"Processed {len(cleaned_df)} records for {table_name}")

            except Exception as e:
                logger.error(f"Failed to process {table_name}: {str(e)}")
                raise DatabaseError(
                    f"Failed to extract {table_name} data: {str(e)}", "DB004")

        logger.info("Creating dimensions...")
        try:

            transformed_data['promotions'] = create_promotion_dimension()
            logger.info("Promotion dimension created successfully")
        except Exception as e:
            logger.error(f"Dimension creation failed: {str(e)}")
            raise TransformationError(
                f"Dimension creation failed: {str(e)}", "TRF002")

        # Update watermarks for all tables
        logger.info("Updating ETL metadata watermarks...")
        try:
            for table_name, schema_config in tables_config.items():
                if not transformed_data[table_name].empty:
                    update_watermark(staging_db, table_name,
                                     schema_config, transformed_data[table_name])

            logger.info("ETL metadata watermarks updated successfully")

        except Exception as e:
            logger.critical(
                f"CRITICAL: Failed to update ETL metadata watermarks - {str(e)}")
            logger.critical(
                "This failure will cause data duplication on next run. Process terminated.")
            raise DatabaseError(
                f"Critical failure updating ETL watermarks: {str(e)}", "DB011")

        logger.info("Data transformation completed successfully!")
        return transformed_data

    except (TransformationError, DatabaseError):
        raise
    except Exception as e:
        logger.critical(f"Transformation process failed: {str(e)}")
        raise TransformationError(
            f"Transformation process failed: {str(e)}", "TRF003")
    finally:
        staging_db.disconnect()
        warehouse_db.disconnect()


def run_transformation():
    return transform_data()
