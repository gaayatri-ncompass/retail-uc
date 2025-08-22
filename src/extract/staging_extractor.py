import pandas as pd
from configs.db_config import get_staging_db_connector
from configs.metadata_config import get_id_columns
from src.utils.logger import get_logger

logger = get_logger("STAGING_EXTRACTOR")


def extract_new_staging_data():

    staging_db = get_staging_db_connector()
    staging_db.connect()

    try:

        tables_query = """
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME LIKE 'stg_%'
            AND TABLE_TYPE = 'BASE TABLE'
        """
        tables_result = staging_db.run_query(tables_query)

        if tables_result is None or tables_result.empty:
            logger.warning("No staging tables found")
            return {}

        id_columns = get_id_columns()

        staging_data = {}

        for _, row in tables_result.iterrows():
            staging_table = row['TABLE_NAME']
            table_name = staging_table.replace('stg_', '')

            try:

                last_id_query = """
                    SELECT last_processed_id 
                    FROM etl_process_log 
                    WHERE table_name = :table_name
                """
                last_id_result = staging_db.run_query_with_params(
                    last_id_query, {"table_name": table_name})

                if last_id_result is not None and not last_id_result.empty and table_name in id_columns:
                    last_processed_id = last_id_result['last_processed_id'].iloc[0]
                    id_column = id_columns[table_name]

                    query = f"""
                        SELECT * FROM {staging_table} 
                        WHERE {id_column} > :last_id 
                        ORDER BY {id_column}
                    """
                    df = staging_db.run_query_with_params(
                        query, {"last_id": last_processed_id})
                    logger.info(
                        f"Extracting {table_name} where {id_column} > {last_processed_id}")
                else:

                    query = f"SELECT * FROM {staging_table}"
                    df = staging_db.run_query(query)
                    logger.info(
                        f"No tracking for {table_name}, extracting all data")

                if df is not None and not df.empty:
                    staging_data[table_name] = df
                    logger.info(f"Found {len(df)} new records in {table_name}")

            except Exception as e:
                logger.error(f"Failed to extract from {table_name}: {e}")
                continue

        total_records = sum(len(df) for df in staging_data.values())
        if total_records > 0:
            logger.success(
                f"Extracted {total_records} new records from {len(staging_data)} tables")

        return staging_data

    except Exception as e:
        logger.error(f"Staging extraction failed: {e}")
        return {}
    finally:
        staging_db.disconnect()


def run_staging_extraction():
    return extract_new_staging_data()
