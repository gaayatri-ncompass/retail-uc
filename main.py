import os
import sys

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.append(SRC_DIR)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

from utils.ddl_utils import create_tables, drop_tables
from utils.connections import get_staging_db, get_target_db
from models.staging_sql import staging_sql_commands, drop_staging_sql_commands
from models.warehouse_sql import warehouse_sql_commands, drop_warehouse_sql_commands

from load import load_staging, load_warehouse
from transform import transformation
from config import column_mappings
from utils.logger import logger
from utils.error_handler import handle_error

def run_etl():
    try:
        logger.info("Starting ETL pipline....")
        staging_db = get_staging_db()
        staging_db.connect()
        target_db = get_target_db()
        target_db.connect()

        print("Resetting Tables...")

        drop_tables(staging_db, drop_staging_sql_commands)
        drop_tables(target_db, drop_warehouse_sql_commands)

        print("All Tables Dropped..")

        create_tables(staging_db, staging_sql_commands)
        create_tables(target_db, warehouse_sql_commands)

        print("All Tables Created")

        dim_tables = [
            (os.path.join(DATA_DIR, 'customers.csv'), 'customers', 'dim_customer'),
            (os.path.join(DATA_DIR, 'dim_date.csv'), 'dimdate', 'dim_date'),
            (os.path.join(DATA_DIR, 'products.csv'), 'products', 'dim_product'),
            (os.path.join(DATA_DIR, 'suppliers.csv'), 'suppliers', 'dim_supplier'),
            (os.path.join(DATA_DIR, 'stores.csv'), 'stores', 'dim_store'),
        ]

        for csv_path, staging_name, warehouse_name in dim_tables:
            load_staging.load_csv(staging_db, csv_path, staging_name)
            print("Applying transformations...")
            transformed = transformation.transform_dim_table(
                staging_db, staging_name, column_mappings.staging_to_dimension_map
            )
            load_warehouse.load_to_data_warehouse(target_db, transformed, warehouse_name)

        sales_csv_path = os.path.join(DATA_DIR, 'sales.csv')
        load_staging.load_csv(staging_db, sales_csv_path, 'sales')
        print("Applying Transformations...")
        sales = transformation.transform_fact_sales(
            staging_db, target_db, column_mappings.staging_to_dimension_map
        )
        load_warehouse.load_to_data_warehouse(target_db, sales, 'fact_sales')
        print("ETL pipeline execution complete. The data has been successfully loaded to the data warehouse.")
        logger.info("ETL pipeline completed successfully.")
    except Exception as e:
        handle_error("ETL Pipeline Execution Failed")
        

if __name__ == "__main__":
    run_etl()