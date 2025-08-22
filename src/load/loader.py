
import traceback
import pandas as pd
from src.utils.exceptions import LoadingError
from configs.db_config import get_warehouse_db_connector
from src.load.table_creator import create_warehouse_tables
from src.load.dimension_loader import load_all_dimensions
from src.transform.transformer import transform_facts_after_dimensions
from src.load.simplified_fact_loaders import load_fact_sales, load_fact_inventory
from src.utils.logger import get_logger

pd.set_option('future.no_silent_downcasting', True)
logger = get_logger("LOADER")


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

    # Load pre-transformed sales fact data
    if 'sales_fact' in transformed_data:
        if not load_fact_sales(db, transformed_data['sales_fact']):
            raise LoadingError("Failed to load sales fact data", "LOAD005")

    # Load pre-transformed inventory fact data
    if 'inventory_fact' in transformed_data:
        if not load_fact_inventory(db, transformed_data['inventory_fact']):
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

        # Load dimension tables first
        _load_dimensions(db, transformed_data)

        # Transform facts with dimension keys using warehouse dimension data
        fact_data = transform_facts_after_dimensions(transformed_data, db)

        # Load fact tables
        if fact_data:
            _load_facts(db, fact_data)

        logger.success("Data warehouse loading completed successfully")

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
            result = db.query(f"SELECT COUNT(*) as count FROM {table}")
            if result is not None and not result.empty:
                stats[table] = result['count'].iloc[0]
            else:
                stats[table] = 0

        # Get fact table counts
        fact_tables = ['factsales', 'factinventorysnapshot']
        for table in fact_tables:
            result = db.query(f"SELECT COUNT(*) as count FROM {table}")
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
