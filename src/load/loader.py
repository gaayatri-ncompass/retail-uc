
import traceback
import pandas as pd
from src.utils.exceptions import LoadingError, DatabaseError
from configs.db_config import get_warehouse_db_connector, get_staging_db_connector
from src.load.table_creator import create_warehouse_tables
from src.load.dimension_loader import load_all_dimensions
from src.load.fact_loaders import load_fact_sales, load_fact_inventory
from src.utils.logger import get_logger

pd.set_option('future.no_silent_downcasting', True)
logger = get_logger("LOADER")


def _update_metadata(staging_db, table_name, schema_config, df):
    """Update metadata for a table after successful loading"""
    if df.empty:
        logger.debug(f"No data to update metadata for {table_name}")
        return

    staging_table = schema_config['staging_table']
    metadata_column = schema_config['metadata_column']

    latest_value = df[metadata_column].max()

    if metadata_column in ['last_updated', 'updated_at', 'modified_date', 'created_at']:
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
            f"Failed to update metadata for {table_name}", f"DB_{table_name}")

    logger.debug(f"Updated metadata for {table_name}: {latest_value}")


def _update_all_metadata(transformed_data, tables_config):
    """Update metadata for all tables after successful loading"""
    logger.info("Updating ETL metadata")

    staging_db = get_staging_db_connector()
    staging_db.connect()

    try:
        for table_name, schema_config in tables_config.items():
            if table_name in transformed_data and not transformed_data[table_name].empty:
                _update_metadata(staging_db, table_name,
                                 schema_config, transformed_data[table_name])

        logger.success("ETL metadata updated successfully")

    except Exception as e:
        logger.critical(
            f"CRITICAL: Failed to update ETL metadata - {str(e)}")
        logger.critical("This failure will cause data duplication on next run")
        raise DatabaseError(
            f"Critical failure updating ETL metadata: {str(e)}", "DB011")
    finally:
        staging_db.disconnect()


def _validate_transform_result(transform_result):
    """Validate and extract data from transform result"""
    if isinstance(transform_result, dict) and 'data' in transform_result:
        transformed_data = transform_result['data']
        tables_config = transform_result.get('tables_config', {})
    else:
        transformed_data = transform_result
        tables_config = {}

    if not transformed_data:
        raise LoadingError("No transformed data provided", "LOAD001")

    return transformed_data, tables_config


def _load_dimensions(db, transformed_data):
    """Load all dimension tables to the warehouse"""
    logger.info("Loading dimension tables")
    if not load_all_dimensions(db, transformed_data):
        raise LoadingError("Failed to load dimension tables", "LOAD004")


def _load_facts(db, transformed_data):
    """Load all fact tables to the warehouse"""
    logger.info("Loading fact tables")

    if 'sales' in transformed_data:
        if not load_fact_sales(db, transformed_data['sales']):
            raise LoadingError("Failed to load sales fact data", "LOAD005")

    if 'inventory' in transformed_data:
        if not load_fact_inventory(db, transformed_data['inventory']):
            raise LoadingError("Failed to load inventory fact data", "LOAD006")


def load_data_to_warehouse(transform_result):
    """Main function to load transformed data to the data warehouse"""
    # Validate and extract data
    transformed_data, tables_config = _validate_transform_result(
        transform_result)

    # Get database connection
    db = get_warehouse_db_connector()
    if not db:
        raise LoadingError("Failed to get database connector", "LOAD002")

    db.connect()

    try:
        # Create warehouse tables if they don't exist
        if not create_warehouse_tables(db):
            raise LoadingError("Failed to create warehouse tables", "LOAD003")

        # Load dimension tables
        _load_dimensions(db, transformed_data)

        # Load fact tables
        _load_facts(db, transformed_data)

        logger.success("Data warehouse loading completed successfully")

        # Update metadata AFTER successful loading
        if tables_config:
            _update_all_metadata(transformed_data, tables_config)

        return True

    except Exception as e:
        logger.error(f"Error during loading: {str(e)}")
        logger.error(traceback.format_exc())
        raise LoadingError(f"Loading failed: {str(e)}", "LOAD007")
    finally:
        db.disconnect()
        logger.info("Disconnected from warehouse database")


def get_loading_statistics():
    """Get loading statistics for monitoring purposes"""
    stats = {}
    db = get_warehouse_db_connector()
    db.connect()

    try:
        # Get dimension table counts
        dimension_tables = ['dimcustomer', 'dimproduct',
                            'dimstore', 'dimsupplier', 'dimpromotion']
        for table in dimension_tables:
            result = db.run_query(f"SELECT COUNT(*) as count FROM {table}")
            if result is not None and not result.empty:
                stats[table] = result['count'].iloc[0]
            else:
                stats[table] = 0

        # Get fact table counts
        fact_tables = ['factsales', 'factinventorysnapshot']
        for table in fact_tables:
            result = db.run_query(f"SELECT COUNT(*) as count FROM {table}")
            if result is not None and not result.empty:
                stats[table] = result['count'].iloc[0]
            else:
                stats[table] = 0

        logger.info(f"Loading statistics: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Error getting loading statistics: {e}")
        return {}
    finally:
        db.disconnect()


def run_loading(transform_result):
    """Entry point for the loading process"""
    logger.info("Starting ETL loading process")
    result = load_data_to_warehouse(transform_result)
    if result:
        logger.success("ETL loading process completed successfully")
    return result


if __name__ == "__main__":
    logger.info("Loader module ready")
