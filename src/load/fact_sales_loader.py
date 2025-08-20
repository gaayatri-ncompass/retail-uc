
from src.utils.rejected_data_handler import save_rejected_sales_data
from logger import get_logger
import pandas as pd
import traceback

logger = get_logger("FACT_SALES_LOADER")


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
        missing_columns = []
        for col in required_columns:
            if col not in sales_df.columns:
                missing_columns.append(col)
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

                promo_key_df = db.run_query_with_params(
                    "SELECT promotion_key FROM dimpromotion WHERE promotion_name = :promotion_name LIMIT 1",
                    {'promotion_name': 'No Promotion'}
                )
                default_promotion_key = promo_key_df['promotion_key'].iloc[0]
                logger.info(
                    f"Created default promotion with key: {default_promotion_key}")
        except Exception as e:
            logger.error(f"Error handling promotion key: {e}")
            return False

        try:

            latest_query = "SELECT sale_id FROM factsales ORDER BY sale_id DESC LIMIT 1"
            latest_result = db.run_query(latest_query)

            if latest_result is not None and not latest_result.empty:
                latest_sale_id = latest_result['sale_id'].iloc[0]
                logger.info(
                    f"Found latest sale_id in warehouse: {latest_sale_id}")

                initial_count = len(sales_df)
                sales_df = sales_df[sales_df['sale_id'] > latest_sale_id]
                logger.info(
                    f"Filtered sales data from {initial_count} to {len(sales_df)} records (only new data)")
            else:
                logger.info(
                    "No existing sales in warehouse, loading all sales data")
        except Exception as e:
            logger.warning(
                f"Could not get latest sale_id, proceeding with full load: {e}")

        try:
            sales_df = sales_df.copy()
            sales_df['sale_date_dt'] = pd.to_datetime(sales_df['sale_date'])

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

            # Save rejected records before dropping them
            rejected_records = fact_df[fact_df[key_columns].isnull().any(
                axis=1)]
            if not rejected_records.empty:
                # Collect information about missing keys
                missing_keys_info = {}
                for col in key_columns:
                    null_count = rejected_records[col].isnull().sum()
                    if null_count > 0:
                        missing_keys_info[col] = null_count

                # Save rejected data to CSV
                save_rejected_sales_data(
                    rejected_records,
                    "Missing dimension keys",
                    missing_keys_info
                )

            fact_df.dropna(subset=key_columns, inplace=True)
            dropped_count = initial_count - len(fact_df)
            if dropped_count > 0:
                logger.warning(
                    f"Dropped {dropped_count} records due to missing dimension keys")
                logger.warning(
                    f"Rejected records saved to rejected_data folder")

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

            promo_check = db.run_query_with_params(
                "SELECT COUNT(*) as count FROM dimpromotion WHERE promotion_key = :promotion_key",
                {'promotion_key': default_promotion_key}
            )
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
            missing_fact_cols = []
            for col in required_fact_cols:
                if col not in fact_df.columns:
                    missing_fact_cols.append(col)
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

                    if (i // actual_batch_size + 1) % 10 == 0:
                        logger.info(
                            f"Loaded {total_loaded}/{len(fact_df)} sales records...")
                except Exception as batch_error:
                    logger.error(
                        f"Error loading batch {i//actual_batch_size + 1}: {batch_error}")

                    # Save failed batch to rejected data folder
                    failed_batch = batch.copy()
                    batch_error_reason = f"Database insertion failed: {str(batch_error)}"
                    save_rejected_sales_data(failed_batch, batch_error_reason)
            logger.info(
                f"Successfully loaded {total_loaded} sales records to warehouse")
            return True
        except Exception as e:
            logger.error(f"Error loading fact sales data: {e}")
            logger.error(f"Sample data: {fact_df.head()}")

            return False

    except Exception as e:
        logger.error(f"Unexpected error in load_fact_sales: {str(e)}")
        return False
