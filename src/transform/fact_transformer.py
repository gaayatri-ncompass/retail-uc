import pandas as pd
from src.utils.logger import get_logger
from src.transform.transform_utils import (
    get_all_dimension_keys, apply_incremental_logic, map_fact_dimensions,
    validate_fact_data, prepare_fact_columns, validate_required_columns, remove_fact_duplicates
)

logger = get_logger("FACT_TRANSFORMER")


def transform_sales_fact(db, sales_df):
    """Transform sales data to fact format using consolidated utilities"""
    if sales_df is None or sales_df.empty:
        logger.info("No sales data to transform")
        return pd.DataFrame()

    logger.info(f"Transforming {len(sales_df)} sales records to fact format")

    # Validate required columns
    required_cols = ['customer_id', 'product_id',
                     'store_id', 'sale_date', 'sale_id']
    if not validate_required_columns(sales_df, required_cols, 'sales'):
        return pd.DataFrame()

    # Get dimension keys
    dimension_keys = get_all_dimension_keys(db)
    if not dimension_keys:
        return pd.DataFrame()

    # Apply incremental filter
    sales_df = apply_incremental_logic(db, sales_df, 'sales', 'sale_id')
    if sales_df.empty:
        logger.info("No new sales records after incremental filtering")
        return pd.DataFrame()

    # Map dimension keys
    fact_df = map_fact_dimensions(sales_df, dimension_keys, 'sales')

    # Validate dimension keys exist
    if not all([dimension_keys['customers'], dimension_keys['products'], dimension_keys['stores']]):
        logger.error("Dimension tables are empty. Load dimensions first.")
        return pd.DataFrame()

    # Validate and clean fact data
    fact_df = validate_fact_data(
        fact_df, ['customer_key', 'product_key', 'store_key', 'date_key'], 'sales')
    if fact_df.empty:
        logger.warning("No valid sales records after validation")
        return pd.DataFrame()

    # Prepare final format
    final_df = prepare_fact_columns(fact_df, 'sales')
    logger.info(
        f"Sales fact transformation complete: {len(final_df)} records ready")
    return final_df


def transform_inventory_fact(db, inventory_df):
    """Transform inventory data to fact format using consolidated utilities"""
    if inventory_df is None or inventory_df.empty:
        logger.info("No inventory data to transform")
        return pd.DataFrame()

    logger.info(
        f"Transforming {len(inventory_df)} inventory records to fact format")

    # Validate required columns
    required_cols = ['product_id', 'store_id', 'supplier_id', 'last_updated']
    if not validate_required_columns(inventory_df, required_cols, 'inventory'):
        return pd.DataFrame()

    # Remove duplicates and get dimension keys
    inventory_df = remove_fact_duplicates(inventory_df, 'inventory')
    dimension_keys = get_all_dimension_keys(db)
    if not dimension_keys:
        return pd.DataFrame()

    # Map dimension keys
    fact_df = map_fact_dimensions(inventory_df, dimension_keys, 'inventory')

    # Validate and clean fact data
    fact_df = validate_fact_data(
        fact_df, ['product_key', 'store_key', 'supplier_key'], 'inventory')

    # Apply incremental filter
    fact_df = apply_incremental_logic(db, fact_df, 'inventory', 'inventory_id')
    if fact_df.empty:
        logger.info("No new inventory records after processing")
        return pd.DataFrame()

    # Prepare final format
    final_df = prepare_fact_columns(fact_df, 'inventory')
    logger.info(
        f"Inventory fact transformation complete: {len(final_df)} records ready")
    return final_df
