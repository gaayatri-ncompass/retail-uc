from src.utils.exceptions import LoadingError, DatabaseError
from src.utils.config import get_warehouse_db_connector
from sqlalchemy import text
import logging
import traceback
import pandas as pd
pd.set_option('future.no_silent_downcasting', True)


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_warehouse_tables(db):

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

    try:
        for table_name, query in warehouse_tables.items():
            result = db.execute_query(query)
            if not result:
                logger.error(f"Failed to create table {table_name}")
                return False
        logger.info("✅ Warehouse tables ready")
        return True
    except Exception as e:
        logger.error(f"Error creating warehouse tables: {str(e)}")
        return False


def load_dimension_table(db, df, table_name, key_column, batch_size=1000):

    try:

        if df is None:
            logger.warning(
                f"No data to load for {table_name} (DataFrame is None)")
            return True

        if df.empty:
            logger.warning(
                f"No data to load for {table_name} (DataFrame is empty)")
            return True

        print(f"Loading {len(df)} records into {table_name}...")

        if key_column not in df.columns:
            logger.error(
                f"Key column '{key_column}' not found in DataFrame for table '{table_name}'")
            logger.error(f"Available columns: {list(df.columns)}")
            return False

        total_loaded = 0
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]

            existing_keys = []
            if not batch.empty:
                try:
                    key_values = batch[key_column].tolist()

                    key_values = [
                        str(val) for val in key_values if val is not None and pd.notna(val)]

                    if key_values:
                        quoted_values = ','.join(
                            [f"'{val}'" for val in key_values])
                        check_query = f"SELECT {key_column} FROM {table_name} WHERE {key_column} IN ({quoted_values})"

                        existing_df = db.run_query(check_query)
                        if existing_df is not None and not existing_df.empty:
                            existing_keys = existing_df[key_column].tolist()
                except Exception as e:
                    logger.error(
                        f"Error checking existing records for batch {i//batch_size + 1}: {e}")
                    continue

            new_batch = batch[~batch[key_column].isin(existing_keys)]

            if new_batch.empty:
                continue  # Skip logging for empty batches

            try:

                new_batch = new_batch.copy()

                object_cols = new_batch.select_dtypes(
                    include=['object']).columns
                new_batch[object_cols] = new_batch[object_cols].fillna(
                    '').infer_objects(copy=False)

                small_batch_size = min(len(new_batch), 50)

                for j in range(0, len(new_batch), small_batch_size):
                    mini_batch = new_batch.iloc[j:j+small_batch_size]
                    mini_batch.to_sql(
                        name=table_name,
                        con=db.engine,
                        if_exists='append',
                        index=False,
                        method=None
                    )

                total_loaded += len(new_batch)  # Add to total
            except Exception as e:
                logger.error(
                    f"Error inserting batch {i//batch_size + 1} into {table_name}: {e}")

                for idx, row in new_batch.iterrows():
                    try:
                        row_df = pd.DataFrame([row])
                        row_df = row_df.fillna('')
                        row_df.to_sql(
                            name=table_name,
                            con=db.engine,
                            if_exists='append',
                            index=False,
                            method=None
                        )
                    except Exception as row_error:
                        logger.error(
                            f"Failed to insert individual record for {key_column}={row[key_column]}: {row_error}")
                        continue

        # Summary message
        if total_loaded > 0:
            logger.info(
                f"Successfully loaded {total_loaded} new records into {table_name}")
        else:
            logger.info(f"No new records to load for {table_name}")

        return True
    except Exception as e:
        logger.error(
            f"Unexpected error in load_dimension_table for {table_name}: {str(e)}")
        logger.error(traceback.format_exc())
        return False


def load_fact_sales(db, sales_df, batch_size=1000):

    try:

        if sales_df is None:
            logger.warning("No sales data to load (DataFrame is None)")
            return True

        if sales_df.empty:
            logger.warning("No sales data to load (DataFrame is empty)")
            return True

        logger.info(f"Preparing to load {len(sales_df)} sales records...")

        required_columns = ['customer_id', 'product_id',
                            'store_id', 'sale_date', 'sale_id']
        missing_columns = [
            col for col in required_columns if col not in sales_df.columns]
        if missing_columns:
            logger.error(
                f"Missing required columns in sales data: {missing_columns}")
            logger.error(f"Available columns: {list(sales_df.columns)}")
            return False

        try:
            customer_keys = db.run_query(
                "SELECT customer_key, customer_id FROM dimcustomer")
            product_keys = db.run_query(
                "SELECT product_key, product_id FROM dimproduct")
            store_keys = db.run_query(
                "SELECT store_key, store_id FROM dimstore")
            date_keys = db.run_query("SELECT date_key, full_date FROM dimdate")

            if any(df is None or df.empty for df in [customer_keys, product_keys, store_keys, date_keys]):
                logger.error(
                    "One or more dimension tables are empty or could not be retrieved")
                return False

        except Exception as e:
            logger.error(f"Error retrieving dimension keys: {e}")
            return False

        try:
            promo_key_df = db.run_query(
                "SELECT promotion_key FROM dimpromotion LIMIT 1")
            if promo_key_df is not None and not promo_key_df.empty:
                default_promotion_key = promo_key_df['promotion_key'].iloc[0]
                logger.info(
                    f"Using existing promotion key: {default_promotion_key}")
            else:

                logger.warning(
                    "No promotions found, creating default promotion")
                default_promotion_data = pd.DataFrame([{
                    'promotion_name': 'No Promotion',
                    'type': 'None',
                    'discount': 0.00
                }])
                default_promotion_data.to_sql(
                    name='dimpromotion',
                    con=db.engine,
                    if_exists='append',
                    index=False,
                    method=None
                )

                promo_key_df = db.run_query(
                    "SELECT promotion_key FROM dimpromotion WHERE promotion_name = 'No Promotion' LIMIT 1")
                default_promotion_key = promo_key_df['promotion_key'].iloc[0]
                logger.info(
                    f"Created default promotion with key: {default_promotion_key}")
        except Exception as e:
            logger.error(f"Error handling promotion key: {e}")
            return False

        try:
            # Get existing sale IDs from warehouse for incremental loading
            existing_sales_query = "SELECT sale_id FROM factsales"
            existing_sales_df = db.run_query(existing_sales_query)
            existing_sale_ids = set()
            if existing_sales_df is not None and not existing_sales_df.empty:
                existing_sale_ids = set(existing_sales_df['sale_id'].tolist())
                logger.info(
                    f"Found {len(existing_sale_ids)} existing sales in warehouse")
        except Exception as e:
            logger.warning(
                f"Could not get existing sale IDs, proceeding with full load: {e}")
            existing_sale_ids = set()

        try:
            sales_df = sales_df.copy()
            sales_df['sale_date_dt'] = pd.to_datetime(sales_df['sale_date'])

            # Filter for new sales records based on sale_id (not date)
            if existing_sale_ids:
                initial_count = len(sales_df)
                sales_df = sales_df[~sales_df['sale_id'].isin(
                    existing_sale_ids)]
                logger.info(
                    f"Filtered sales data from {initial_count} to {len(sales_df)} records based on sale_id check.")

            if sales_df.empty:
                logger.info(
                    "No new sales records to process after incremental filtering.")
                return True

            sales_df['sale_date'] = sales_df['sale_date_dt'].dt.date
            date_keys['full_date'] = pd.to_datetime(
                date_keys['full_date']).dt.date
        except Exception as e:
            logger.error(f"Error processing dates: {e}")
            return False

        try:
            fact_df = sales_df.merge(
                customer_keys, on='customer_id', how='left')
            fact_df = fact_df.merge(product_keys, on='product_id', how='left')
            fact_df = fact_df.merge(store_keys, on='store_id', how='left')
            fact_df = fact_df.merge(
                date_keys, left_on='sale_date', right_on='full_date', how='left')

            key_columns = ['customer_key',
                           'product_key', 'store_key', 'date_key']
            for col in key_columns:
                null_count = fact_df[col].isnull().sum()
                if null_count > 0:
                    logger.warning(
                        f"Found {null_count} records with missing {col}")

                    missing_data = fact_df[fact_df[col].isnull()]
                    if col == 'customer_key':
                        missing_ids = missing_data['customer_id'].unique()[:5]
                        logger.warning(
                            f"Sample missing customer_ids: {missing_ids}")
                    elif col == 'product_key':
                        missing_ids = missing_data['product_id'].unique()[:5]
                        logger.warning(
                            f"Sample missing product_ids: {missing_ids}")
                    elif col == 'store_key':
                        missing_ids = missing_data['store_id'].unique()[:5]
                        logger.warning(
                            f"Sample missing store_ids: {missing_ids}")
                    elif col == 'date_key':
                        missing_dates = missing_data['sale_date'].unique()[:5]
                        logger.warning(
                            f"Sample missing sale_dates: {missing_dates}")

            initial_count = len(fact_df)
            fact_df.dropna(subset=key_columns, inplace=True)
            dropped_count = initial_count - len(fact_df)
            if dropped_count > 0:
                logger.warning(
                    f"Dropped {dropped_count} records due to missing dimension keys")

            if fact_df.empty:
                logger.info(
                    "No new valid sales records to load after dimension key lookup.")
                return True

        except Exception as e:
            logger.error(f"Error merging with dimension tables: {e}")
            return False

        try:
            fact_df['promotion_key'] = default_promotion_key
            key_cols = ['customer_key', 'product_key',
                        'store_key', 'date_key', 'promotion_key']

            logger.info("Validating foreign key relationships...")

            valid_customers = set(customer_keys['customer_key'].tolist())
            invalid_customers = fact_df[~fact_df['customer_key'].isin(
                valid_customers)]
            if not invalid_customers.empty:
                logger.error(
                    f"Found {len(invalid_customers)} records with invalid customer_key")
                fact_df = fact_df[fact_df['customer_key'].isin(
                    valid_customers)]

            valid_products = set(product_keys['product_key'].tolist())
            invalid_products = fact_df[~fact_df['product_key'].isin(
                valid_products)]
            if not invalid_products.empty:
                logger.error(
                    f"Found {len(invalid_products)} records with invalid product_key")
                fact_df = fact_df[fact_df['product_key'].isin(valid_products)]

            valid_stores = set(store_keys['store_key'].tolist())
            invalid_stores = fact_df[~fact_df['store_key'].isin(valid_stores)]
            if not invalid_stores.empty:
                logger.error(
                    f"Found {len(invalid_stores)} records with invalid store_key")
                fact_df = fact_df[fact_df['store_key'].isin(valid_stores)]

            valid_dates = set(date_keys['date_key'].tolist())
            invalid_dates = fact_df[~fact_df['date_key'].isin(valid_dates)]
            if not invalid_dates.empty:
                logger.error(
                    f"Found {len(invalid_dates)} records with invalid date_key")
                fact_df = fact_df[fact_df['date_key'].isin(valid_dates)]

            promo_check = db.run_query(
                f"SELECT COUNT(*) as count FROM dimpromotion WHERE promotion_key = {default_promotion_key}")
            if promo_check is None or promo_check['count'].iloc[0] == 0:
                logger.error(
                    f"Promotion key {default_promotion_key} does not exist in dimpromotion table")
                return False

            if fact_df.empty:
                logger.warning("No records left after foreign key validation")
                return True

            fact_df[key_cols] = fact_df[key_cols].astype(int)

            required_fact_cols = key_cols + \
                ['sale_id', 'quantity', 'total_amount', 'payment_type', 'channel']
            missing_fact_cols = [
                col for col in required_fact_cols if col not in fact_df.columns]
            if missing_fact_cols:
                logger.error(
                    f"Missing columns for fact table: {missing_fact_cols}")
                return False

            fact_df = fact_df[required_fact_cols]

            int_columns = ['customer_key', 'product_key',
                           'store_key', 'date_key', 'promotion_key', 'quantity']
            for col in int_columns:
                if col in fact_df.columns:
                    fact_df[col] = pd.to_numeric(
                        fact_df[col], errors='coerce').fillna(0).astype(int)

            numeric_columns = ['total_amount']
            for col in numeric_columns:
                if col in fact_df.columns:
                    fact_df[col] = pd.to_numeric(
                        fact_df[col], errors='coerce').fillna(0.0)

            logger.info(
                f"Final validation passed. Ready to load {len(fact_df)} records")

        except Exception as e:
            logger.error(f"Error preparing fact DataFrame: {e}")
            logger.error(f"DataFrame info: {fact_df.info()}")
            return False

        try:
            logger.info(
                f"Loading {len(fact_df)} new sales records in batches of {batch_size}")

            actual_batch_size = min(batch_size, 100)

            total_loaded = 0
            for i in range(0, len(fact_df), actual_batch_size):
                batch = fact_df.iloc[i:i+actual_batch_size]
                try:
                    batch.to_sql(
                        name='factsales',
                        con=db.engine,
                        if_exists='append',
                        index=False,
                        method=None
                    )
                    total_loaded += len(batch)
                    # Show progress every 10 batches
                    if (i // actual_batch_size + 1) % 10 == 0:
                        logger.info(
                            f"Loaded {total_loaded}/{len(fact_df)} sales records...")
                except Exception as batch_error:
                    logger.error(
                        f"Error loading batch {i//actual_batch_size + 1}: {batch_error}")

                    for idx, row in batch.iterrows():
                        try:
                            row_df = pd.DataFrame([row])
                            row_df.to_sql(
                                name='factsales',
                                con=db.engine,
                                if_exists='append',
                                index=False,
                                method=None
                            )
                            total_loaded += 1
                        except Exception as row_error:
                            logger.error(
                                f"Failed to insert individual record: {row['sale_id']} - {row_error}")
                            continue

            logger.info(
                f"Successfully loaded {total_loaded} sales records to warehouse")
            return True
        except Exception as e:
            logger.error(f"Error loading fact sales data: {e}")
            logger.error(f"Sample data: {fact_df.head()}")
            logger.error(traceback.format_exc())
            return False

    except Exception as e:
        logger.error(f"Unexpected error in load_fact_sales: {str(e)}")
        logger.error(traceback.format_exc())
        return False


def load_fact_inventory(db, inventory_df, batch_size=1000):
    """Load fact inventory table with improved error handling"""

    try:

        if inventory_df is None:
            logger.warning("No inventory data to load (DataFrame is None)")
            return True

        if inventory_df.empty:
            logger.warning("No inventory data to load (DataFrame is empty)")
            return True

        logger.info(
            f"Preparing to load {len(inventory_df)} inventory records...")

        required_columns = ['product_id', 'store_id',
                            'supplier_id', 'last_updated']
        missing_columns = [
            col for col in required_columns if col not in inventory_df.columns]
        if missing_columns:
            logger.error(
                f"Missing required columns in inventory data: {missing_columns}")
            logger.error(f"Available columns: {list(inventory_df.columns)}")
            return False

        try:
            product_keys = db.run_query(
                "SELECT product_key, product_id FROM dimproduct")
            store_keys = db.run_query(
                "SELECT store_key, store_id FROM dimstore")
            date_keys = db.run_query("SELECT date_key, full_date FROM dimdate")
            supplier_keys = db.run_query(
                "SELECT supplier_key, supplier_id FROM dimsupplier")

            if any(df is None or df.empty for df in [product_keys, store_keys, date_keys, supplier_keys]):
                logger.error(
                    "One or more dimension tables are empty or could not be retrieved")
                return False

        except Exception as e:
            logger.error(f"Error retrieving dimension keys: {e}")
            return False

        try:
            # Get existing inventory IDs from warehouse for incremental loading
            existing_inventory_query = "SELECT inventory_id FROM factinventorysnapshot"
            existing_inventory_df = db.run_query(existing_inventory_query)
            existing_inventory_ids = set()
            if existing_inventory_df is not None and not existing_inventory_df.empty:
                existing_inventory_ids = set(
                    existing_inventory_df['inventory_id'].tolist())
                logger.info(
                    f"Found {len(existing_inventory_ids)} existing inventory records in warehouse")
        except Exception as e:
            logger.warning(
                f"Could not get existing inventory IDs, proceeding with full load: {e}")
            existing_inventory_ids = set()

        try:
            inventory_df = inventory_df.copy()
            inventory_df['last_updated_dt'] = pd.to_datetime(
                inventory_df['last_updated'])

            # Create inventory_id first for comparison
            inventory_df['inventory_id'] = (
                inventory_df['product_id'].astype(str) + '_' +
                inventory_df['store_id'].astype(str) + '_' +
                inventory_df['last_updated_dt'].dt.strftime('%Y%m%d%H%M%S')
            )

            # Filter for new inventory records based on inventory_id
            if existing_inventory_ids:
                initial_count = len(inventory_df)
                inventory_df = inventory_df[~inventory_df['inventory_id'].isin(
                    existing_inventory_ids)]
                logger.info(
                    f"Filtered inventory data from {initial_count} to {len(inventory_df)} records based on inventory_id check.")

            if inventory_df.empty:
                logger.info(
                    "No new inventory records to process after incremental filtering.")
                return True

            inventory_df['last_updated_date'] = inventory_df['last_updated_dt'].dt.date
            date_keys['full_date'] = pd.to_datetime(
                date_keys['full_date']).dt.date
        except Exception as e:
            logger.error(f"Error processing dates: {e}")
            return False

        try:
            fact_df = inventory_df.merge(
                product_keys, on='product_id', how='left')
            fact_df = fact_df.merge(store_keys, on='store_id', how='left')
            fact_df = fact_df.merge(
                supplier_keys, on='supplier_id', how='left')
            fact_df = fact_df.merge(
                date_keys, left_on='last_updated_date', right_on='full_date', how='left')

            key_cols = ['product_key', 'store_key', 'date_key', 'supplier_key']

            null_counts = fact_df[key_cols].isnull().sum()
            if null_counts.sum() > 0:
                logger.warning(
                    f"Some inventory records have missing dimension keys: {null_counts.to_dict()}")

            initial_count = len(fact_df)
            fact_df.dropna(subset=key_cols, inplace=True)
            dropped_count = initial_count - len(fact_df)
            if dropped_count > 0:
                logger.warning(
                    f"Dropped {dropped_count} inventory records due to missing dimension keys")

            if fact_df.empty:
                logger.warning(
                    "No inventory records with valid dimension keys.")
                return True

        except Exception as e:
            logger.error(f"Error merging inventory with dimension tables: {e}")
            return False

        try:
            # inventory_id was already created earlier, no need to recreate

            if fact_df.empty:
                logger.info(
                    "No new valid inventory records to load after dimension key lookup.")
                return True

        except Exception as e:
            logger.error(f"Error creating inventory IDs: {e}")
            return False

        try:
            fact_df[key_cols] = fact_df[key_cols].astype(int)
            final_cols = ['inventory_id', 'stock_level'] + key_cols

            if 'stock_level' not in fact_df.columns:
                logger.error(
                    "'stock_level' column not found in inventory data")
                return False

            fact_df = fact_df[final_cols]

            int_columns = ['product_key', 'store_key',
                           'date_key', 'supplier_key', 'stock_level']
            for col in int_columns:
                if col in fact_df.columns:
                    fact_df[col] = pd.to_numeric(
                        fact_df[col], errors='coerce').fillna(0).astype(int)

        except Exception as e:
            logger.error(f"Error preparing inventory DataFrame: {e}")
            return False

        try:
            logger.info(
                f"Loading {len(fact_df)} new inventory records in batches of {batch_size}")

            actual_batch_size = min(batch_size, 100)

            total_loaded = 0
            for i in range(0, len(fact_df), actual_batch_size):
                batch = fact_df.iloc[i:i+actual_batch_size]
                try:
                    batch.to_sql(
                        name='factinventorysnapshot',
                        con=db.engine,
                        if_exists='append',
                        index=False,
                        method=None
                    )
                    total_loaded += len(batch)
                    if (i // actual_batch_size + 1) % 20 == 0:  # Reduced frequency
                        print(
                            f"  Loading inventory: {total_loaded}/{len(fact_df)} records...")
                except Exception as batch_error:
                    logger.error(
                        f"Error loading inventory batch {i//actual_batch_size + 1}: {batch_error}")

                    for idx, row in batch.iterrows():
                        try:
                            row_df = pd.DataFrame([row])
                            row_df.to_sql(
                                name='FactInventorySnapshot',
                                con=db.engine,
                                if_exists='append',
                                index=False,
                                method=None
                            )
                            total_loaded += 1
                        except Exception as row_error:
                            logger.error(
                                f"Failed to insert individual inventory record: {row['inventory_id']} - {row_error}")
                            continue

            print(f"  ✅ Loaded {total_loaded} new inventory records")
            return True
        except Exception as e:
            logger.error(f"Error loading fact inventory data: {e}")
            logger.error(f"Sample data: {fact_df.head()}")
            logger.error(traceback.format_exc())
            return False

    except Exception as e:
        logger.error(f"Unexpected error in load_fact_inventory: {str(e)}")
        logger.error(traceback.format_exc())
        return False


def load_data_to_warehouse(transformed_data):

    print("Loading data to warehouse...")

    if not transformed_data:
        logger.error("No transformed data provided")
        return False

    try:
        db = get_warehouse_db_connector()
        if not db:
            logger.error("Failed to get database connector")
            return False

        db.connect()

        if not create_warehouse_tables(db):
            logger.error("Failed to create warehouse tables")
            return False

        logger.info("Loading dimension tables...")

        dimension_tables = [
            ('customers', 'dimcustomer', 'customer_id'),
            ('products', 'dimproduct', 'product_id'),
            ('stores', 'dimstore', 'store_id'),
            ('suppliers', 'dimsupplier', 'supplier_id'),
            ('dates', 'dimdate', 'date_key')
        ]

        for data_key, table_name, key_column in dimension_tables:
            if data_key in transformed_data:
                if not load_dimension_table(db, transformed_data[data_key], table_name, key_column):
                    logger.error(f"Failed to load {data_key} data")
                    return False

        # Handle promotions
        if 'promotions' in transformed_data and transformed_data['promotions'] is not None and not transformed_data['promotions'].empty:
            if not load_dimension_table(db, transformed_data['promotions'], 'dimpromotion', 'promotion_key'):
                logger.error("Failed to load promotions data")
                return False
        else:
            existing_promos = db.run_query(
                "SELECT COUNT(*) as count FROM dimpromotion")
            if existing_promos is None or existing_promos['count'].iloc[0] == 0:
                default_promotion_data = pd.DataFrame([{
                    'promotion_name': 'No Promotion',
                    'type': 'None',
                    'discount': 0.00
                }])
                if not load_dimension_table(db, default_promotion_data, 'dimpromotion', 'promotion_name'):
                    logger.error("Failed to create default promotion")
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
