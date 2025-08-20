
from src.utils.rejected_data_handler import save_rejected_inventory_data
from logger import get_logger
import pandas as pd
import traceback

logger = get_logger("FACT_INVENTORY_LOADER")


def load_fact_inventory(db, inventory_df, batch_size=1000):

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
        missing_columns = []
        for col in required_columns:
            if col not in inventory_df.columns:
                missing_columns.append(col)
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

            inventory_df = inventory_df.copy()
            inventory_df['last_updated_dt'] = pd.to_datetime(
                inventory_df['last_updated'])

            latest_query = "SELECT inventory_id FROM factinventorysnapshot ORDER BY inventory_id DESC LIMIT 1"
            latest_result = db.run_query(latest_query)

            if latest_result is not None and not latest_result.empty:
                latest_inventory_id = latest_result['inventory_id'].iloc[0]
                logger.info(
                    f"Found latest inventory_id in warehouse: {latest_inventory_id}")

                inventory_df['inventory_id'] = (
                    inventory_df['product_id'].astype(str) + '_' +
                    inventory_df['store_id'].astype(str) + '_' +
                    inventory_df['last_updated_dt'].dt.strftime('%Y%m%d%H%M%S')
                )

                initial_count = len(inventory_df)
                inventory_df = inventory_df[inventory_df['inventory_id']
                                            > latest_inventory_id]
                logger.info(
                    f"Filtered inventory data from {initial_count} to {len(inventory_df)} records (only new data)")
            else:
                logger.info(
                    "No existing inventory in warehouse, loading all inventory data")

                inventory_df['inventory_id'] = (
                    inventory_df['product_id'].astype(str) + '_' +
                    inventory_df['store_id'].astype(str) + '_' +
                    inventory_df['last_updated_dt'].dt.strftime('%Y%m%d%H%M%S')
                )
        except Exception as e:
            logger.warning(
                f"Could not get latest inventory_id, proceeding with full load: {e}")

            if 'last_updated_dt' not in inventory_df.columns:
                inventory_df['last_updated_dt'] = pd.to_datetime(
                    inventory_df['last_updated'])
            inventory_df['inventory_id'] = (
                inventory_df['product_id'].astype(str) + '_' +
                inventory_df['store_id'].astype(str) + '_' +
                inventory_df['last_updated_dt'].dt.strftime('%Y%m%d%H%M%S')
            )

        try:
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

            # Save rejected records before dropping them
            rejected_records = fact_df[fact_df[key_cols].isnull().any(axis=1)]
            if not rejected_records.empty:
                # Collect information about missing keys
                missing_keys_info = {}
                for col in key_cols:
                    null_count = rejected_records[col].isnull().sum()
                    if null_count > 0:
                        missing_keys_info[col] = null_count

                # Save rejected data to CSV
                save_rejected_inventory_data(
                    rejected_records,
                    "Missing dimension keys",
                    missing_keys_info
                )

            fact_df.dropna(subset=key_cols, inplace=True)
            dropped_count = initial_count - len(fact_df)
            if dropped_count > 0:
                logger.warning(
                    f"Dropped {dropped_count} inventory records due to missing dimension keys")
                logger.warning(
                    f"Rejected records saved to rejected_data folder")

            if fact_df.empty:
                logger.warning(
                    "No inventory records with valid dimension keys.")
                return True

        except Exception as e:
            logger.error(f"Error merging inventory with dimension tables: {e}")
            return False

        try:
            if fact_df.empty:
                logger.info(
                    "No new valid inventory records to load after dimension key lookup.")
                return True
        except Exception as e:
            logger.error(f"Error validating inventory records: {e}")
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
                    if (i // actual_batch_size + 1) % 20 == 0:
                        print(
                            f"  Loading inventory: {total_loaded}/{len(fact_df)} records...")
                except Exception as batch_error:
                    logger.error(
                        f"Error loading inventory batch {i//actual_batch_size + 1}: {batch_error}")

                    # Save failed batch to rejected data folder
                    failed_batch = batch.copy()
                    batch_error_reason = f"Database insertion failed: {str(batch_error)}"
                    save_rejected_inventory_data(
                        failed_batch, batch_error_reason)

                    # Try individual record insertion as fallback
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

            print(f"Loaded {total_loaded} new inventory records")
            return True
        except Exception as e:
            logger.error(f"Error loading fact inventory data: {e}")
            logger.error(f"Sample data: {fact_df.head()}")
            return False

    except Exception as e:
        logger.error(f"Unexpected error in load_fact_inventory: {str(e)}")
        return False
