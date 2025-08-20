
from src.utils.exceptions import LoadingError, DatabaseError
from src.utils.config import get_warehouse_db_connector
from src.load.table_creator import create_warehouse_tables
from src.load.dimension_loader import load_all_dimensions
from src.load.fact_sales_loader import load_fact_sales
from src.load.fact_inventory_loader import load_fact_inventory
import traceback
import pandas as pd
from logger import get_logger

pd.set_option('future.no_silent_downcasting', True)

logger = get_logger("LOADER")


def load_data_to_warehouse(transformed_data):

    print("Loading data to warehouse...")

    if not transformed_data:
        logger.error("No transformed data provided")
        return False

    try:
        # Get database connection
        db = get_warehouse_db_connector()
        if not db:
            logger.error("Failed to get database connector")
            return False

        db.connect()

        if not create_warehouse_tables(db):
            logger.error("Failed to create warehouse tables")
            return False

        logger.info("Loading dimension tables...")
        if not load_all_dimensions(db, transformed_data):
            logger.error("Failed to load dimension tables")
            return False

        logger.info("Loading fact tables...")

        if 'sales' in transformed_data:
            if not load_fact_sales(db, transformed_data['sales']):
                logger.error("Failed to load sales fact data")
                return False

        if 'inventory' in transformed_data:
            if not load_fact_inventory(db, transformed_data['inventory']):
                logger.error("Failed to load inventory fact data")
                return False

        logger.info("✅ Data warehouse loading completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Error during loading: {str(e)}")
        logger.error(traceback.format_exc())
        return False
    finally:
        try:
            db.disconnect()
            logger.info("Disconnected from warehouse database")
        except:
            pass


def run_loading(transformed_data):

    try:
        logger.info("Starting ETL loading process...")
        result = load_data_to_warehouse(transformed_data)
        if result:
            logger.info("ETL loading process completed successfully")
        else:
            raise LoadingError("Loading process returned False", "LOAD002")
        return result
    except LoadingError:
        raise
    except Exception as e:
        raise LoadingError(
            f"Critical error in run_loading: {str(e)}", "LOAD003")


def get_loading_statistics(db=None):

    stats = {}

    try:
        if db is None:
            db = get_warehouse_db_connector()
            db.connect()
            should_disconnect = True
        else:
            should_disconnect = False

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
            try:
                result = db.run_query(f"SELECT COUNT(*) as count FROM {table}")
                if result is not None and not result.empty:
                    stats[table] = result['count'].iloc[0]
                else:
                    stats[table] = 0
            except:
                stats[table] = 0

        logger.info(f"Loading statistics: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Error getting loading statistics: {e}")
        return {}
    finally:
        if should_disconnect:
            try:
                db.disconnect()
            except:
                pass


def validate_warehouse_integrity(db=None):

    validation_results = {
        'valid': True,
        'issues': [],
        'warnings': []
    }

    try:
        if db is None:
            db = get_warehouse_db_connector()
            db.connect()
            should_disconnect = True
        else:
            should_disconnect = False

        # Check for orphaned records in fact tables
        orphan_checks = [
            {
                'name': 'Sales with invalid customer keys',
                'query': '''
                    SELECT COUNT(*) as count 
                    FROM factsales fs 
                    LEFT JOIN dimcustomer dc ON fs.customer_key = dc.customer_key 
                    WHERE dc.customer_key IS NULL
                '''
            },
            {
                'name': 'Sales with invalid product keys',
                'query': '''
                    SELECT COUNT(*) as count 
                    FROM factsales fs 
                    LEFT JOIN dimproduct dp ON fs.product_key = dp.product_key 
                    WHERE dp.product_key IS NULL
                '''
            },
            {
                'name': 'Inventory with invalid product keys',
                'query': '''
                    SELECT COUNT(*) as count 
                    FROM factinventorysnapshot fi 
                    LEFT JOIN dimproduct dp ON fi.product_key = dp.product_key 
                    WHERE dp.product_key IS NULL
                '''
            }
        ]

        for check in orphan_checks:
            try:
                result = db.run_query(check['query'])
                if result is not None and not result.empty:
                    count = result['count'].iloc[0]
                    if count > 0:
                        validation_results['valid'] = False
                        validation_results['issues'].append(
                            f"{check['name']}: {count} records")
            except Exception as e:
                validation_results['warnings'].append(
                    f"Could not check {check['name']}: {e}")

        logger.info(
            f"Warehouse integrity validation completed. Valid: {validation_results['valid']}")
        return validation_results

    except Exception as e:
        logger.error(f"Error during warehouse integrity validation: {e}")
        validation_results['valid'] = False
        validation_results['issues'].append(f"Validation error: {e}")
        return validation_results
    finally:
        if should_disconnect:
            try:
                db.disconnect()
            except:
                pass


if __name__ == "__main__":
    logger.info("Loader module ready - use run_loading() to process data")
