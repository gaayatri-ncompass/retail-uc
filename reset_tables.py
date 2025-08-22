from configs.db_config import get_warehouse_db_connector, get_staging_db_connector
from src.utils.logger import get_logger

logger = get_logger("RESET_TABLES")


def reset_etl_metadata():
    logger.info("Resetting ETL metadata in staging database...")

    staging_db = get_staging_db_connector()
    staging_db.connect()

    try:
        if staging_db.query("TRUNCATE TABLE etl_process_log", fetch_data=False):
            logger.info("Cleared ETL process log (watermarks)")
        else:
            logger.error("Failed to clear ETL process log")

        staging_tables = [
            "stg_customers",
            "stg_products",
            "stg_stores",
            "stg_sales",
            "stg_inventory",
            "stg_suppliers"
        ]

        for table in staging_tables:
            if staging_db.query(f"TRUNCATE TABLE {table}", fetch_data=False):
                logger.info(f"Cleared {table}")
            else:
                logger.error(f"Failed to clear {table}")

    except Exception as e:
        logger.error(f"Error resetting ETL metadata: {e}")
    finally:
        staging_db.disconnect()


def drop_and_recreate_tables():

    logger.info("Dropping and recreating warehouse tables...")

    db = get_warehouse_db_connector()
    db.connect()

    drop_queries = [
        "DROP TABLE IF EXISTS FactSales",
        "DROP TABLE IF EXISTS FactInventorySnapshot",
        "DROP TABLE IF EXISTS DimCustomer",
        "DROP TABLE IF EXISTS DimProduct",
        "DROP TABLE IF EXISTS DimStore",
        "DROP TABLE IF EXISTS DimSupplier",
        # DimDate is preserved
        "DROP TABLE IF EXISTS DimPromotion"
    ]

    try:

        db.query("SET FOREIGN_KEY_CHECKS = 0", fetch_data=False)

        for query in drop_queries:
            if db.query(query, fetch_data=False):
                logger.debug(f"Dropped table: {query}")
            else:
                logger.error(f"Failed to drop table: {query}")

        db.query("SET FOREIGN_KEY_CHECKS = 1", fetch_data=False)

        create_tables_queries = {
            'DimCustomer': '''
                CREATE TABLE DimCustomer (
                    customer_key INT AUTO_INCREMENT PRIMARY KEY,
                    customer_id VARCHAR(255) UNIQUE,
                    customer_name VARCHAR(255),
                    email VARCHAR(255),
                    phone VARCHAR(255),
                    address VARCHAR(500),
                    signup_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            ''',
            'DimProduct': '''
                CREATE TABLE DimProduct (
                    product_key INT AUTO_INCREMENT PRIMARY KEY,
                    product_id VARCHAR(255) UNIQUE,
                    product_name VARCHAR(255),
                    category VARCHAR(255),
                    price DECIMAL(10,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            ''',
            'DimStore': '''
                CREATE TABLE DimStore (
                    store_key INT AUTO_INCREMENT PRIMARY KEY,
                    store_id VARCHAR(255) UNIQUE,
                    store_name VARCHAR(255),
                    location VARCHAR(255),
                    manager VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            ''',
            'DimSupplier': '''
                CREATE TABLE DimSupplier (
                    supplier_key INT AUTO_INCREMENT PRIMARY KEY,
                    supplier_id VARCHAR(255) UNIQUE,
                    supplier_name VARCHAR(255),
                    contact_name VARCHAR(255),
                    contact_email VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            ''',

            'DimPromotion': '''
                CREATE TABLE DimPromotion (
                    promotion_key INT AUTO_INCREMENT PRIMARY KEY,
                    promotion_name VARCHAR(255),
                    type VARCHAR(100),
                    discount DECIMAL(5,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'FactSales': '''
                CREATE TABLE FactSales (
                    sale_key INT AUTO_INCREMENT PRIMARY KEY,
                    sale_id VARCHAR(255) UNIQUE,
                    customer_key INT,
                    product_key INT,
                    store_key INT,
                    date_key INT,
                    promotion_key INT,
                    quantity INT,
                    total_amount DECIMAL(10,2),
                    payment_type VARCHAR(100),
                    channel VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_key) REFERENCES DimCustomer(customer_key),
                    FOREIGN KEY (product_key) REFERENCES DimProduct(product_key),
                    FOREIGN KEY (store_key) REFERENCES DimStore(store_key),
                    FOREIGN KEY (date_key) REFERENCES DimDate(date_key),
                    FOREIGN KEY (promotion_key) REFERENCES DimPromotion(promotion_key)
                )
            ''',
            'FactInventorySnapshot': '''
                CREATE TABLE FactInventorySnapshot (
                    inventory_snapshot_key INT AUTO_INCREMENT PRIMARY KEY,
                    inventory_id VARCHAR(255) UNIQUE,
                    product_key INT,
                    store_key INT,
                    date_key INT,
                    supplier_key INT,
                    stock_level INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_key) REFERENCES DimProduct(product_key),
                    FOREIGN KEY (store_key) REFERENCES DimStore(store_key),
                    FOREIGN KEY (date_key) REFERENCES DimDate(date_key),
                    FOREIGN KEY (supplier_key) REFERENCES DimSupplier(supplier_key)
                )
            '''
        }

        for table_name, query in create_tables_queries.items():
            if db.query(query, fetch_data=False):
                logger.info(f"Created table {table_name}")
            else:
                logger.error(f"Failed to create table {table_name}")

        logger.info("Warehouse reset complete!")

    except Exception as e:
        logger.error(f"Error during table recreation: {e}")

    finally:
        db.disconnect()


def main():

    logger.info("Starting complete ETL reset...")
    logger.info("=" * 50)

    drop_and_recreate_tables()

    logger.info("=" * 50)

    reset_etl_metadata()

    logger.info("=" * 50)
    logger.info("Complete ETL reset finished!")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
