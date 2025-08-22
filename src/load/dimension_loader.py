from src.utils.rejected_data_handler import save_rejected_dimension_data
from src.utils.logger import get_logger
import pandas as pd
import traceback

logger = get_logger("DIMENSION_LOADER")


def load_dimension_table(db, df, table_name, key_column, batch_size=1000):
    if df is None or df.empty:
        logger.warning(
            f"No data to load for {table_name} (DataFrame is None or empty)")
        return True

    logger.info(f"Loading {len(df)} records into {table_name}")

    if key_column not in df.columns:
        logger.error(
            f"Key column '{key_column}' not found in DataFrame for table '{table_name}'")
        logger.error(f"Available columns: {list(df.columns)}")
        return False

    total_loaded = load_in_batches(db, df, table_name, batch_size)

    if total_loaded > 0:
        logger.data_summary(table_name, total_loaded, "loaded")
    else:
        logger.info(f"No records loaded for {table_name}")

    return True


def load_in_batches(db, df, table_name, batch_size):
    total_loaded = 0
    duplicate_batches = 0

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
            # Clean error message without SQL parameter dump
            if "Duplicate entry" in str(e):
                duplicate_batches += 1
                batch_error_reason = "Duplicate key constraint violation"
            else:
                error_type = type(e).__name__
                logger.error(
                    f"Batch {i//batch_size + 1} into {table_name}: {error_type}")
                batch_error_reason = f"Database insertion failed: {error_type}"

            save_rejected_dimension_data(batch, table_name, batch_error_reason)
            continue

    # Log summary instead of each duplicate batch
    if duplicate_batches > 0:
        logger.warning(
            f"{table_name}: {duplicate_batches} batches skipped (duplicate keys - expected)")

    return total_loaded


def load_all_dimensions(db, transformed_data):
    logger.info("Loading dimension tables")

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
    if not handle_promotions(db, transformed_data):
        return False

    return True


def handle_promotions(db, transformed_data):
    if 'promotions' in transformed_data and transformed_data['promotions'] is not None and not transformed_data['promotions'].empty:
        if not load_dimension_table(db, transformed_data['promotions'], 'dimpromotion', 'promotion_key'):
            logger.error("Failed to load promotions data")
            return False
    else:
        # Check if default promotion exists
        existing_promos = db.query(
            "SELECT COUNT(*) as count FROM dimpromotion")
        if existing_promos is None or existing_promos['count'].iloc[0] == 0:
            default_promotion_sql = """
                INSERT INTO dimpromotion (promotion_name, type, discount) 
                VALUES ('No Promotion', 'None', 0.00)
            """
            if not db.query(default_promotion_sql, fetch_data=False):
                logger.error("Failed to create default promotion")
                return False
            logger.info("Created default promotion record")

    return True
