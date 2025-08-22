from src.utils.logger import get_logger
import pandas as pd

logger = get_logger("FACT_LOADER")


def load_data_in_batches(db, fact_df, table_name, batch_size=1000):

    total_records = len(fact_df)

    try:
        for i in range(0, total_records, batch_size):
            batch_end = min(i + batch_size, total_records)
            batch_df = fact_df.iloc[i:batch_end]

            batch_df.to_sql(
                name=table_name,
                con=db.engine,
                if_exists='append',
                index=False
            )

            logger.loading_progress(
                batch_end, total_records, f"{table_name} records")

        logger.success(f"Loaded {total_records} new {table_name} records")
        return True

    except Exception as e:
        logger.error(f"Error loading {table_name} in batches: {e}")
        return False


def load_fact_sales(db, sales_fact_df, batch_size=1000):
    """Load pre-transformed sales fact data to the warehouse"""
    if sales_fact_df is None or sales_fact_df.empty:
        logger.info("No sales fact data to load (DataFrame is empty)")
        return True

    logger.info(
        f"Loading {len(sales_fact_df)} pre-transformed sales fact records")

    # Data is already transformed, just load it
    return load_data_in_batches(db, sales_fact_df, 'factsales', batch_size)


def load_fact_inventory(db, inventory_fact_df, batch_size=1000):
    """Load pre-transformed inventory fact data to the warehouse"""
    if inventory_fact_df is None or inventory_fact_df.empty:
        logger.info("No inventory fact data to load (DataFrame is empty)")
        return True

    logger.info(
        f"Loading {len(inventory_fact_df)} pre-transformed inventory fact records")

    # Data is already transformed, just load it
    return load_data_in_batches(db, inventory_fact_df, 'factinventorysnapshot', batch_size)
