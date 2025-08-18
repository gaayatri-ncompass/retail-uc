import pandas as pd
from src.utils.config import get_staging_db_connector
from src.utils.exceptions import ExtractionError, DatabaseError
from src.utils.validator import validate_dataframe
from logger import get_logger


logger = get_logger("EXTRACT")

EXPECTED_COLUMNS = {
    'customers': ['customer_id', 'customer_name', 'email', 'phone', 'address', 'signup_date'],
    'products': ['product_id', 'product_name', 'category', 'price'],
    'stores': ['store_id', 'store_name', 'location', 'manager'],
    'sales': ['sale_id', 'customer_id', 'product_id', 'store_id', 'sale_date', 'quantity', 'total_amount'],
    'inventory': ['product_id', 'store_id', 'stock_level', 'last_updated', 'supplier_id'],
    'suppliers': ['supplier_id', 'supplier_name', 'contact_name', 'contact_email']
}


def create_etl_tables(db):

    logger.info("Creating ETL tables...")

    log_table_query = '''
        CREATE TABLE IF NOT EXISTS etl_process_log (
            table_name VARCHAR(255) PRIMARY KEY,
            last_processed_id VARCHAR(255),
            last_updated TIMESTAMP
        )
    '''
    if not db.execute_query(log_table_query):
        logger.error("Failed to create etl_process_log table")
        raise DatabaseError("Failed to create etl_process_log table", "DB001")

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
            logger.error(f"Failed to create staging table for {table}")
            raise DatabaseError(
                f"Failed to create staging table for {table}", "DB002")

    logger.info("ETL tables created successfully")
    return True


def load_csv_to_staging(db, file_name, table_name, pk_column):

    logger.info(f"Loading {file_name} to staging table {table_name}")

    try:
        chunk_size = 1000
        total_processed = 0

        for chunk_num, df_chunk in enumerate(pd.read_csv(f'data/{file_name}', dtype=str, chunksize=chunk_size), 1):
            logger.debug(
                f"Processing chunk {chunk_num} ({len(df_chunk)} records)...")

            if chunk_num == 1:
                expected_cols = EXPECTED_COLUMNS.get(table_name, [])
                if expected_cols:
                    missing_cols = []
                    for col in expected_cols:
                        if col not in df_chunk.columns:
                            missing_cols.append(col)
                    if missing_cols:
                        logger.error(
                            f"Missing expected columns in {file_name}: {missing_cols}")
                        raise ExtractionError(
                            f"Missing expected columns in {file_name}: {missing_cols}")
                    logger.debug(
                        f"Filtered CSV to expected columns: {expected_cols}")

            expected_cols = EXPECTED_COLUMNS.get(table_name, [])
            if expected_cols:
                df_chunk = df_chunk[expected_cols]

            df_chunk.drop_duplicates(inplace=True)

            log_query = "SELECT last_processed_id FROM etl_process_log WHERE table_name = :table_name"
            last_id_df = db.run_query_with_params(
                log_query, {'table_name': table_name})

            last_processed_id = None
            if last_id_df is not None and not last_id_df.empty:
                last_processed_id = last_id_df['last_processed_id'].iloc[0]

            if last_processed_id:
                df_to_insert = df_chunk[df_chunk[pk_column]
                                        > last_processed_id]
            else:
                df_to_insert = df_chunk

            if df_to_insert.empty:
                logger.debug(f"No new records in chunk {chunk_num}")
                continue

            logger.debug(f"Validating {len(df_to_insert)} new records...")
            is_valid = validate_dataframe(df_to_insert, table_name)
            if not is_valid:
                logger.warning(
                    f"Data validation issues found for {table_name}")

            table_full_name = f'stg_{table_name}'
            df_to_insert.to_sql(name=table_full_name,
                                con=db.engine, if_exists='append', index=False)

            chunk_processed = len(df_to_insert)
            total_processed += chunk_processed
            logger.debug(
                f"Inserted {chunk_processed} records from chunk {chunk_num}")

        logger.info(
            f"Total new records processed for {table_name}: {total_processed}")

        if total_processed > 0:

            max_id_query = f"SELECT MAX({pk_column}) as max_id FROM stg_{table_name}"
            max_id_df = db.run_query(max_id_query)
            if max_id_df is not None and not max_id_df.empty:
                max_id = max_id_df['max_id'].iloc[0]

                update_query = """
                    INSERT INTO etl_process_log (table_name, last_processed_id, last_updated)
                    VALUES (:table_name, :max_id, CURRENT_TIMESTAMP)
                    ON DUPLICATE KEY UPDATE last_processed_id = :max_id, last_updated = CURRENT_TIMESTAMP
                """
                db.execute_query_with_params(update_query, {
                    'table_name': table_name,
                    'max_id': max_id
                })
                logger.debug(f"Updated ETL log with max ID: {max_id}")

        return True

    except FileNotFoundError:
        logger.error(f"CSV file not found: data/{file_name}")
        raise ExtractionError(
            f"CSV file not found: data/{file_name}")
    except pd.errors.EmptyDataError:
        logger.error(f"CSV file is empty: data/{file_name}")
        raise ExtractionError(f"CSV file is empty: data/{file_name}")
    except Exception as e:
        logger.error(f"Error loading {file_name}: {str(e)}")
        raise ExtractionError(f"Error loading {file_name}: {str(e)}")


def run_extraction():

    logger.info("Extraction process started...")
    db = get_staging_db_connector()

    try:
        db.connect()

        if not create_etl_tables(db):
            logger.error("Failed to create ETL tables")
            raise DatabaseError("Failed to create ETL tables")

        files_to_load = {
            'customers.csv': ('customers', 'customer_id'),
            'products.csv': ('products', 'product_id'),
            'stores.csv': ('stores', 'store_id'),
            'sales.csv': ('sales', 'sale_id'),
            'inventory.csv': ('inventory', 'last_updated'),
            'suppliers.csv': ('suppliers', 'supplier_id')
        }

        for file_name, (table_name, pk_column) in files_to_load.items():
            try:
                logger.info(f"Processing {file_name}...")
                if not load_csv_to_staging(db, file_name, table_name, pk_column):
                    logger.error(f"Failed to load {file_name}")
                    raise ExtractionError(f"Failed to load {file_name}")
            except (ExtractionError, DatabaseError):
                raise
            except Exception as e:
                logger.error(f"Unexpected error loading {file_name}: {str(e)}")
                raise ExtractionError(
                    f"Unexpected error loading {file_name}: {str(e)}", "EXT005")

        logger.info("Extraction process completed successfully")

    except (ExtractionError, DatabaseError):
        raise
    except Exception as e:
        logger.critical(f"Extraction process failed: {str(e)}")
        raise ExtractionError(f"Extraction process failed: {str(e)}", "EXT006")
    finally:
        db.disconnect()
