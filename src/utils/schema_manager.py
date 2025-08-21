"""
Schema Manager Module
Handles schema extraction and configuration management for staging tables
"""
from configs.db_config import get_staging_db_connector
from src.utils.logger import get_logger

logger = get_logger("SCHEMA_MANAGER")


def extract_staging_tables_schema():
    """Extract schema configuration from staging database tables"""
    staging_db = get_staging_db_connector()
    staging_db.connect()

    try:
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

        if schema_info is None or schema_info.empty:
            logger.warning("No staging tables found in database")
            return {}

        return build_tables_configuration(schema_info, primary_keys_info)

    finally:
        staging_db.disconnect()


def build_tables_configuration(schema_info, primary_keys_info):
    """Build table configuration from schema information"""
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
                'metadata_column': None
            }

        tables_config[business_table]['columns'][column_name] = {
            'data_type': data_type,
            'is_nullable': row['IS_NULLABLE']
        }

        # Set primary key and metadata column
        if table_name in primary_keys_map and primary_keys_map[table_name] == column_name:
            tables_config[business_table]['key_column'] = column_name
            tables_config[business_table]['metadata_column'] = column_name
            logger.debug(
                f"Found primary key for {business_table}: {column_name}")

        elif column_name in ['last_updated', 'updated_at', 'modified_date', 'created_at']:
            if not tables_config[business_table]['metadata_column']:
                tables_config[business_table]['metadata_column'] = column_name
                logger.debug(
                    f"Found timestamp metadata for {business_table}: {column_name}")

    # Apply fallback metadata logic
    apply_fallback_metadata(tables_config)

    logger.info(
        f"Built configuration for {len(tables_config)} tables: {list(tables_config.keys())}")
    return tables_config


def apply_fallback_metadata(tables_config):
    """Apply fallback metadata logic for tables without metadata"""
    for business_table, config in tables_config.items():
        if not config['metadata_column']:
            for column_name in config['columns'].keys():
                if column_name.endswith('_id'):
                    config['metadata_column'] = column_name
                    config['key_column'] = column_name
                    logger.debug(
                        f"Using fallback metadata for {business_table}: {column_name}")
                    break

            if not config['metadata_column']:
                logger.warning(
                    f"No suitable metadata column found for {business_table}")


def get_metadata_value(staging_db, table_name, schema_config):
    """Get the current metadata value for incremental processing"""
    staging_table = schema_config['staging_table']
    metadata_column = schema_config['metadata_column']

    metadata = staging_db.run_query(
        f"SELECT last_processed_id FROM etl_process_log WHERE table_name = '{staging_table}'"
    )

    if metadata is not None and not metadata.empty:
        return metadata.iloc[0]['last_processed_id']
    else:
        if metadata_column in ['last_updated', 'updated_at', 'modified_date', 'created_at']:
            return '1900-01-01 00:00:00'
        else:
            return ''
