import pandas as pd
from src.utils.config import get_staging_db_connector


def create_etl_tables(db):

    # Create etl_process_log table
    log_table_query = '''
        CREATE TABLE IF NOT EXISTS etl_process_log (
            table_name VARCHAR(255) PRIMARY KEY,
            last_processed_id VARCHAR(255),
            last_updated TIMESTAMP
        )
    '''
    if not db.execute_query(log_table_query):
        print("Failed to create etl_process_log table")
        return False


    create_tables_queries = {
        'customers': '''
            CREATE TABLE IF NOT EXISTS stg_customers (
                customer_id VARCHAR(255),
                customer_name VARCHAR(255),
                email VARCHAR(255),
                phone VARCHAR(255),
                address VARCHAR(255),
                signup_date VARCHAR(255)
            )
        ''',
        'products': '''
            CREATE TABLE IF NOT EXISTS stg_products (
                product_id VARCHAR(255),
                product_name VARCHAR(255),
                category VARCHAR(255),
                price VARCHAR(255)
            )
        ''',
        'stores': '''
            CREATE TABLE IF NOT EXISTS stg_stores (
                store_id VARCHAR(255),
                store_name VARCHAR(255),
                location VARCHAR(255),
                manager VARCHAR(255)
            )
        ''',
        'sales': '''
            CREATE TABLE IF NOT EXISTS stg_sales (
                sale_id VARCHAR(255),
                customer_id VARCHAR(255),
                product_id VARCHAR(255),
                store_id VARCHAR(255),
                sale_date VARCHAR(255),
                quantity VARCHAR(255),
                total_amount VARCHAR(255)
            )
        ''',
        'inventory': '''
            CREATE TABLE IF NOT EXISTS stg_inventory (
                product_id VARCHAR(255),
                store_id VARCHAR(255),
                stock_level VARCHAR(255),
                last_updated VARCHAR(255),
                supplier_id VARCHAR(255)
            )
        ''',
        'suppliers': '''
            CREATE TABLE IF NOT EXISTS stg_suppliers (
                supplier_id VARCHAR(255),
                supplier_name VARCHAR(255),
                contact_name VARCHAR(255),
                contact_email VARCHAR(255)
            )
        '''
    }

    for table, query in create_tables_queries.items():
        if not db.execute_query(query):
            print(f"Failed to create staging table for {table}")
            return False
    return True


def load_csv_to_staging(db, file_name, table_name, pk_column):

    try:

        df_new = pd.read_csv(f'data/{file_name}', dtype=str)
        df_new.drop_duplicates(inplace=True)

        # Get the last processed ID from the log table
        log_query = f"SELECT last_processed_id FROM etl_process_log WHERE table_name = '{table_name}'"
        last_id_df = db.run_query(log_query)
        
        last_processed_id = None
        if last_id_df is not None and not last_id_df.empty:
            last_processed_id = last_id_df['last_processed_id'].iloc[0]

        if last_processed_id:
            # Filter for new records based on the primary key
            # This assumes the PK can be sorted lexicographically or numerically
            df_to_insert = df_new[df_new[pk_column] > last_processed_id]
        else:
            df_to_insert = df_new

        table_full_name = f'stg_{table_name}'

        if df_to_insert.empty:
            print(f"No new rows to insert into {table_full_name}")
            return True

        df_to_insert.to_sql(
            name=table_full_name,
            con=db.engine,
            if_exists='append',
            index=False
        )

        print(f"Inserted {len(df_to_insert)} new rows into {table_full_name}")

        # Update the log table with the new max ID
        if not df_to_insert.empty:
            max_id = df_to_insert[pk_column].max()
            update_query = f"""
                INSERT INTO etl_process_log (table_name, last_processed_id, last_updated)
                VALUES ('{table_name}', '{max_id}', CURRENT_TIMESTAMP)
                ON DUPLICATE KEY UPDATE last_processed_id = '{max_id}', last_updated = CURRENT_TIMESTAMP
            """
            db.execute_query(update_query)

        return True

    except Exception as e:
        print(f"Error loading {file_name}: {str(e)}")
        return False


def run_extraction():

    print("Extraction process started...")
    db = get_staging_db_connector()

    db.connect()

    if not create_etl_tables(db):
        print("Failed to create ETL tables")
        db.disconnect()
        return

    files_to_load = {
        'customers.csv': ('customers', 'customer_id'),
        'products.csv': ('products', 'product_id'),
        'stores.csv': ('stores', 'store_id'),
        'sales.csv': ('sales', 'sale_id'),
        'inventory.csv': ('inventory', 'last_updated'),
        'suppliers.csv': ('suppliers', 'supplier_id')
    }

    for file_name, (table_name, pk_column) in files_to_load.items():
        if not load_csv_to_staging(db, file_name, table_name, pk_column):
            print(f"Failed to load {file_name}")

    db.disconnect()
