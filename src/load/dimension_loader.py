from src.utils.rejected_data_handler import save_rejected_dimension_data
from logger import get_logger
import pandas as pd
import traceback

logger = get_logger("DIMENSION_LOADER")


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

        # Apply incremental loading filter
        df = _apply_incremental_filter(db, df, table_name, key_column)

        if df.empty:
            logger.info(f"No new records to load for {table_name}")
            return True

        # Load in batches
        total_loaded = _load_in_batches(db, df, table_name, batch_size)

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


def _apply_incremental_filter(db, df, table_name, key_column):

    try:
        # Validate inputs
        valid_tables = ['dimcustomer', 'dimproduct',
                        'dimstore', 'dimsupplier', 'dimdate', 'dimpromotion']
        valid_key_columns = ['customer_id', 'product_id',
                             'store_id', 'supplier_id', 'date_key', 'promotion_key']

        if table_name not in valid_tables:
            logger.error(f"Invalid table name: {table_name}")
            return df

        if key_column not in valid_key_columns:
            logger.error(f"Invalid key column: {key_column}")
            return df

        if key_column == 'date_key':
            latest_query = f"SELECT MAX({key_column}) as latest_value FROM {table_name}"
        else:
            latest_query = f"SELECT {key_column} as latest_value FROM {table_name} ORDER BY {key_column} DESC LIMIT 1"

        latest_result = db.run_query(latest_query)

        if latest_result is not None and not latest_result.empty and latest_result['latest_value'].iloc[0] is not None:
            latest_value = latest_result['latest_value'].iloc[0]
            logger.info(
                f"Found latest {key_column} in {table_name}: {latest_value}")

            if key_column == 'date_key':
                filtered_df = df[df[key_column] > latest_value]
            else:
                filtered_df = df[df[key_column] > str(latest_value)]

            logger.info(
                f"Filtered {table_name} from {len(df)} to {len(filtered_df)} records (only new data)")
            return filtered_df
        else:
            logger.info(
                f"No existing data in {table_name}, loading all {len(df)} records")
            return df

    except Exception as e:
        logger.warning(
            f"Could not get latest value from {table_name}, loading all data: {e}")
        return df


def _load_in_batches(db, df, table_name, batch_size):

    total_loaded = 0

    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size].copy()

        try:

            object_cols = batch.select_dtypes(include=['object']).columns
            batch[object_cols] = batch[object_cols].fillna(
                '').infer_objects(copy=False)

            batch.to_sql(
                name=table_name,
                con=db.engine,
                if_exists='append',
                index=False,
                method=None
            )
            total_loaded += len(batch)

        except Exception as e:
            logger.error(
                f"Error inserting batch {i//batch_size + 1} into {table_name}: {e}")

            batch_error_reason = f"Database insertion failed: {str(e)}"
            save_rejected_dimension_data(batch, table_name, batch_error_reason)
            continue

    return total_loaded


def load_all_dimensions(db, transformed_data):

    logger.info("Loading dimension tables...")

    dimension_tables = [
        ('customers', 'dimcustomer', 'customer_id'),
        ('products', 'dimproduct', 'product_id'),
        ('stores', 'dimstore', 'store_id'),
        ('suppliers', 'dimsupplier', 'supplier_id')
    ]

    # Load standard dimensions
    for data_key, table_name, key_column in dimension_tables:
        if data_key in transformed_data:
            if not load_dimension_table(db, transformed_data[data_key], table_name, key_column):
                logger.error(f"Failed to load {data_key} data")
                return False

    # Handle promotions
    if not _handle_promotions(db, transformed_data):
        return False

    return True


def _handle_promotions(db, transformed_data):

    if 'promotions' in transformed_data and transformed_data['promotions'] is not None and not transformed_data['promotions'].empty:
        if not load_dimension_table(db, transformed_data['promotions'], 'dimpromotion', 'promotion_key'):
            logger.error("Failed to load promotions data")
            return False
    else:
        # Check if default promotion exists
        existing_promos = db.run_query(
            "SELECT COUNT(*) as count FROM dimpromotion")
        if existing_promos is None or existing_promos['count'].iloc[0] == 0:
            default_promotion_sql = """
                INSERT INTO dimpromotion (promotion_name, type, discount) 
                VALUES ('No Promotion', 'None', 0.00)
            """
            if not db.execute_query(default_promotion_sql):
                logger.error("Failed to create default promotion")
                return False
            logger.info("Created default promotion record")

    return True
