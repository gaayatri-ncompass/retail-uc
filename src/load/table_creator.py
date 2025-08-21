from src.utils.logger import get_logger

logger = get_logger("TABLE_CREATOR")


def create_warehouse_tables(db):

    logger.info("Checking and creating warehouse tables if needed...")

    # Define all warehouse tables to check
    warehouse_table_names = [
        'dimcustomer', 'dimproduct', 'dimstore', 'dimsupplier',
        'dimdate', 'dimpromotion', 'factsales', 'factinventorysnapshot'
    ]

    # Check which tables exist
    existing_tables = db.check_multiple_tables_exist(warehouse_table_names)

    warehouse_tables = {
        'dimcustomer': '''
            CREATE TABLE IF NOT EXISTS dimcustomer (
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
        'dimproduct': '''
            CREATE TABLE IF NOT EXISTS dimproduct (
                product_key INT AUTO_INCREMENT PRIMARY KEY,
                product_id VARCHAR(255) UNIQUE,
                product_name VARCHAR(255),
                category VARCHAR(255),
                price DECIMAL(10,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ''',
        'dimstore': '''
            CREATE TABLE IF NOT EXISTS dimstore (
                store_key INT AUTO_INCREMENT PRIMARY KEY,
                store_id VARCHAR(255) UNIQUE,
                store_name VARCHAR(255),
                location VARCHAR(255),
                manager VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ''',
        'dimsupplier': '''
            CREATE TABLE IF NOT EXISTS dimsupplier (
                supplier_key INT AUTO_INCREMENT PRIMARY KEY,
                supplier_id VARCHAR(255) UNIQUE,
                supplier_name VARCHAR(255),
                contact_name VARCHAR(255),
                contact_email VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ''',
        'dimdate': '''
            CREATE TABLE IF NOT EXISTS dimdate (
                date_key INT PRIMARY KEY,
                full_date DATE,
                year INT,
                quarter INT,
                month INT,
                week INT,
                day INT
            )
        ''',
        'dimpromotion': '''
            CREATE TABLE IF NOT EXISTS dimpromotion (
                promotion_key INT AUTO_INCREMENT PRIMARY KEY,
                promotion_name VARCHAR(255),
                type VARCHAR(100),
                discount DECIMAL(5,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''',
        'factsales': '''
            CREATE TABLE IF NOT EXISTS factsales (
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
                FOREIGN KEY (customer_key) REFERENCES dimcustomer(customer_key),
                FOREIGN KEY (product_key) REFERENCES dimproduct(product_key),
                FOREIGN KEY (store_key) REFERENCES dimstore(store_key),
                FOREIGN KEY (date_key) REFERENCES dimdate(date_key),
                FOREIGN KEY (promotion_key) REFERENCES dimpromotion(promotion_key)
            )
        ''',
        'factinventorysnapshot': '''
            CREATE TABLE IF NOT EXISTS factinventorysnapshot (
                inventory_snapshot_key INT AUTO_INCREMENT PRIMARY KEY,
                inventory_id VARCHAR(255) UNIQUE,
                product_key INT,
                store_key INT,
                date_key INT,
                supplier_key INT,
                stock_level INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_key) REFERENCES dimproduct(product_key),
                FOREIGN KEY (store_key) REFERENCES dimstore(store_key),
                FOREIGN KEY (date_key) REFERENCES dimdate(date_key),
                FOREIGN KEY (supplier_key) REFERENCES dimsupplier(supplier_key)
            )
        '''
    }

    tables_created = 0
    tables_skipped = 0

    try:
        for table_name, query in warehouse_tables.items():
            if existing_tables.get(table_name, False):
                logger.info(
                    f"Table {table_name} already exists, skipping creation")
                tables_skipped += 1
            else:
                logger.info(f"Creating warehouse table {table_name}...")
                result = db.execute_query(query)
                if not result:
                    logger.error(f"Failed to create table {table_name}")
                    return False
                tables_created += 1

        logger.info(
            f"Warehouse tables check completed - Created: {tables_created}, Skipped: {tables_skipped}")
        return True
    except Exception as e:
        logger.error(f"Error creating warehouse tables: {str(e)}")
        return False
