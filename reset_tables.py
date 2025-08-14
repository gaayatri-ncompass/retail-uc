from src.utils.config import get_warehouse_db_connector, get_staging_db_connector


def reset_etl_metadata():

    print("Resetting ETL metadata in staging database...")

    staging_db = get_staging_db_connector()
    staging_db.connect()

    try:

        if staging_db.execute_query("TRUNCATE TABLE etl_process_log"):
            print("Cleared ETL process log (watermarks)")
        else:
            print("Failed to clear ETL process log")

        staging_tables = [
            "stg_customers",
            "stg_products",
            "stg_stores",
            "stg_sales",
            "stg_inventory",
            "stg_suppliers"
        ]

        for table in staging_tables:
            if staging_db.execute_query(f"TRUNCATE TABLE {table}"):
                print(f"Cleared {table}")
            else:
                print(f"Failed to clear {table}")

    except Exception as e:
        print(f"Error resetting ETL metadata: {e}")
    finally:
        staging_db.disconnect()


def drop_and_recreate_tables():

    print("Dropping and recreating warehouse tables...")

    db = get_warehouse_db_connector()
    db.connect()

    drop_queries = [
        "DROP TABLE IF EXISTS FactSales",
        "DROP TABLE IF EXISTS FactInventorySnapshot",
        "DROP TABLE IF EXISTS DimCustomer",
        "DROP TABLE IF EXISTS DimProduct",
        "DROP TABLE IF EXISTS DimStore",
        "DROP TABLE IF EXISTS DimSupplier",
        "DROP TABLE IF EXISTS DimDate",
        "DROP TABLE IF EXISTS DimPromotion"
    ]

    try:

        db.execute_query("SET FOREIGN_KEY_CHECKS = 0")

        for query in drop_queries:
            if db.execute_query(query):
                print("Dropped table")
            else:
                print("Failed to drop table")

        db.execute_query("SET FOREIGN_KEY_CHECKS = 1")

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
            'DimDate': '''
                CREATE TABLE DimDate (
                    date_key INT PRIMARY KEY,
                    full_date DATE,
                    year INT,
                    quarter INT,
                    month INT,
                    week INT,
                    day INT
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
            if db.execute_query(query):
                print(f"Created table {table_name}")
            else:
                print(f"Failed to create table {table_name}")

        print("Warehouse reset complete!")

    except Exception as e:
        print(f"Error during table recreation: {e}")

    finally:
        db.disconnect()


def main():
    """Main function to reset both warehouse and ETL metadata"""
    print("Starting complete ETL reset...")
    print("=" * 50)

    # Step 1: Reset warehouse tables
    drop_and_recreate_tables()

    print("=" * 50)

    # Step 2: Reset ETL metadata
    reset_etl_metadata()

    print("=" * 50)
    print("Complete ETL reset finished!")


if __name__ == "__main__":
    main()
