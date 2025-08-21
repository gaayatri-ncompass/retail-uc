"""
Fact Table Loaders
==================
Consolidated module for loading all fact tables to the data warehouse.
"""

from src.utils.rejected_data_handler import save_rejected_sales_data, save_rejected_inventory_data
from src.utils.logger import get_logger
import pandas as pd

logger = get_logger("FACT_LOADER")


# ==========================================
# Common Utilities for Fact Table Loading
# ==========================================

def _get_dimension_keys(db):
    """Get all dimension keys for fact table loading"""
    dimension_keys = {}

    try:
        # Customer dimension keys
        customer_df = db.run_query(
            "SELECT customer_key, customer_id FROM dimcustomer")
        if customer_df is not None and not customer_df.empty:
            dimension_keys['customers'] = dict(
                zip(customer_df['customer_id'], customer_df['customer_key']))
        else:
            dimension_keys['customers'] = {}

        # Product dimension keys
        product_df = db.run_query(
            "SELECT product_key, product_id FROM dimproduct")
        if product_df is not None and not product_df.empty:
            dimension_keys['products'] = dict(
                zip(product_df['product_id'], product_df['product_key']))
        else:
            dimension_keys['products'] = {}

        # Store dimension keys
        store_df = db.run_query("SELECT store_key, store_id FROM dimstore")
        if store_df is not None and not store_df.empty:
            dimension_keys['stores'] = dict(
                zip(store_df['store_id'], store_df['store_key']))
        else:
            dimension_keys['stores'] = {}

        # Supplier dimension keys (for inventory)
        supplier_df = db.run_query(
            "SELECT supplier_key, supplier_id FROM dimsupplier")
        if supplier_df is not None and not supplier_df.empty:
            dimension_keys['suppliers'] = dict(
                zip(supplier_df['supplier_id'], supplier_df['supplier_key']))
        else:
            dimension_keys['suppliers'] = {}

        # Date dimension keys
        date_df = db.run_query("SELECT date_key FROM dimdate")
        if date_df is not None and not date_df.empty:
            dimension_keys['dates'] = set(date_df['date_key'].tolist())
        else:
            dimension_keys['dates'] = set()

        # Promotion dimension key (default)
        promotion_df = db.run_query(
            "SELECT promotion_key FROM dimpromotion LIMIT 1")
        if promotion_df is not None and not promotion_df.empty:
            dimension_keys['default_promotion'] = promotion_df['promotion_key'].iloc[0]
        else:
            dimension_keys['default_promotion'] = 1

        logger.debug(f"Retrieved dimension keys: customers={len(dimension_keys['customers'])}, "
                     f"products={len(dimension_keys['products'])}, stores={len(dimension_keys['stores'])}, "
                     f"suppliers={len(dimension_keys['suppliers'])}, dates={len(dimension_keys['dates'])}")

        return dimension_keys

    except Exception as e:
        logger.error(f"Error retrieving dimension keys: {e}")
        return None


def _load_data_in_batches(db, fact_df, table_name, batch_size=1000):
    """Load fact data in batches with progress tracking"""
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


# ==========================================
# Sales Fact Table Loading
# ==========================================

def _apply_sales_incremental_filter(db, sales_df):
    """Apply incremental filter for sales data"""
    try:
        existing_sales_query = "SELECT COUNT(*) as count FROM factsales"
        result = db.run_query(existing_sales_query)

        if result is not None and not result.empty and result['count'].iloc[0] > 0:
            max_sale_id_query = "SELECT MAX(sale_id) as max_sale_id FROM factsales"
            max_result = db.run_query(max_sale_id_query)

            if max_result is not None and not max_result.empty:
                max_sale_id = max_result['max_sale_id'].iloc[0]
                if max_sale_id:
                    sales_df = sales_df[sales_df['sale_id'] > max_sale_id]
                    logger.info(
                        f"Applied incremental filter: sale_id > {max_sale_id}")
        else:
            logger.info(
                "No existing sales in warehouse, loading all sales data")

        return sales_df

    except Exception as e:
        logger.error(f"Error applying sales incremental filter: {e}")
        return sales_df


def _prepare_sales_fact_data(sales_df, dimension_keys):
    """Prepare sales data for fact table loading"""
    fact_df = sales_df.copy()

    # Map dimension keys
    fact_df['customer_key'] = fact_df['customer_id'].map(
        dimension_keys['customers'])
    fact_df['product_key'] = fact_df['product_id'].map(
        dimension_keys['products'])
    fact_df['store_key'] = fact_df['store_id'].map(dimension_keys['stores'])
    fact_df['promotion_key'] = dimension_keys['default_promotion']

    # Validate date keys
    if 'sale_date_key' in fact_df.columns:
        fact_df['date_key'] = fact_df['sale_date_key']
        fact_df = fact_df[fact_df['date_key'].isin(dimension_keys['dates'])]
    else:
        logger.warning("Missing sale_date_key column")

    # Track missing keys
    missing_keys = {}
    for key_col in ['customer_key', 'product_key', 'store_key', 'date_key']:
        missing_count = fact_df[key_col].isna().sum()
        if missing_count > 0:
            missing_keys[key_col] = missing_count
            logger.warning(
                f"Found {missing_count} records with missing {key_col}")

    # Save rejected records
    rejected_df = fact_df[fact_df[[
        'customer_key', 'product_key', 'store_key', 'date_key']].isna().any(axis=1)]
    if not rejected_df.empty:
        save_rejected_sales_data(
            rejected_df, "Missing dimension keys", missing_keys)
        logger.warning(
            f"Dropped {len(rejected_df)} records due to missing dimension keys")

    # Keep only valid records
    fact_df = fact_df.dropna(
        subset=['customer_key', 'product_key', 'store_key', 'date_key'])

    # Select final columns
    final_columns = ['sale_id', 'customer_key', 'product_key', 'store_key',
                     'date_key', 'promotion_key', 'quantity', 'total_amount',
                     'payment_type', 'channel']
    fact_df = fact_df[final_columns]

    logger.info(
        f"Final validation passed. Ready to load {len(fact_df)} records")
    return fact_df


def load_fact_sales(db, sales_df, batch_size=1000):
    """Load sales fact data to the warehouse"""
    if sales_df is None or sales_df.empty:
        logger.warning("No sales data to load (DataFrame is empty)")
        return True

    logger.info(f"Preparing to load {len(sales_df)} sales records")

    # Validate required columns
    required_columns = ['customer_id', 'product_id',
                        'store_id', 'sale_date', 'sale_id']
    missing_columns = [
        col for col in required_columns if col not in sales_df.columns]
    if missing_columns:
        logger.error(
            f"Missing required columns in sales data: {missing_columns}")
        return False

    # Get dimension keys
    dimension_keys = _get_dimension_keys(db)
    if not dimension_keys:
        return False

    # Apply incremental filter
    sales_df = _apply_sales_incremental_filter(db, sales_df)
    if sales_df.empty:
        logger.info(
            "No new sales records to process after incremental filtering")
        return True

    # Prepare fact data
    fact_df = _prepare_sales_fact_data(sales_df, dimension_keys)
    if fact_df.empty:
        logger.info("No valid sales records to load after dimension key lookup")
        return True

    # Load data in batches
    return _load_data_in_batches(db, fact_df, 'factsales', batch_size)


# ==========================================
# Inventory Fact Table Loading
# ==========================================

def _prepare_inventory_data(db, inventory_df):
    """Prepare and apply incremental filter for inventory data"""
    try:
        existing_inventory_query = "SELECT COUNT(*) as count FROM factinventorysnapshot"
        result = db.run_query(existing_inventory_query)

        if result is not None and not result.empty and result['count'].iloc[0] > 0:
            logger.info(
                "Existing inventory data found, applying incremental logic")
            # For inventory, we might want to keep all records or apply date-based filtering
        else:
            logger.info(
                "No existing inventory in warehouse, loading all inventory data")

        # Create inventory_id if it doesn't exist
        if 'inventory_id' not in inventory_df.columns:
            inventory_df['inventory_id'] = (
                inventory_df['product_id'].astype(str) + '_' +
                inventory_df['store_id'].astype(str) + '_' +
                inventory_df['last_updated'].astype(str)
            )

        return inventory_df

    except Exception as e:
        logger.error(f"Error preparing inventory data: {e}")
        return inventory_df


def _prepare_inventory_fact_data(inventory_df, dimension_keys):
    """Prepare inventory data for fact table loading"""
    fact_df = inventory_df.copy()

    # Map dimension keys
    fact_df['product_key'] = fact_df['product_id'].map(
        dimension_keys['products'])
    fact_df['store_key'] = fact_df['store_id'].map(dimension_keys['stores'])
    fact_df['supplier_key'] = fact_df['supplier_id'].map(
        dimension_keys['suppliers'])

    # Handle date key for inventory
    if 'last_updated' in fact_df.columns:
        fact_df['date_key'] = pd.to_datetime(
            fact_df['last_updated']).dt.strftime('%Y%m%d').astype(int)

    # Keep only valid records
    fact_df = fact_df.dropna(
        subset=['product_key', 'store_key', 'supplier_key'])

    # Select final columns
    final_columns = ['inventory_id', 'product_key', 'store_key', 'date_key',
                     'supplier_key', 'stock_level']
    fact_df = fact_df[final_columns]

    logger.info(f"Prepared {len(fact_df)} inventory records for loading")
    return fact_df


def load_fact_inventory(db, inventory_df, batch_size=1000):
    """Load inventory fact data to the warehouse"""
    if inventory_df is None or inventory_df.empty:
        logger.warning("No inventory data to load (DataFrame is empty)")
        return True

    logger.info(f"Preparing to load {len(inventory_df)} inventory records")

    # Validate required columns
    required_columns = ['product_id', 'store_id',
                        'supplier_id', 'last_updated']
    missing_columns = [
        col for col in required_columns if col not in inventory_df.columns]
    if missing_columns:
        logger.error(
            f"Missing required columns in inventory data: {missing_columns}")
        return False

    # Get dimension keys
    dimension_keys = _get_dimension_keys(db)
    if not dimension_keys:
        return False

    # Prepare inventory data
    inventory_df = _prepare_inventory_data(db, inventory_df)
    if inventory_df.empty:
        logger.info("No inventory records to process after preparation")
        return True

    # Prepare fact data
    fact_df = _prepare_inventory_fact_data(inventory_df, dimension_keys)
    if fact_df.empty:
        logger.info(
            "No valid inventory records to load after dimension key lookup")
        return True

    # Load data in batches
    return _load_data_in_batches(db, fact_df, 'factinventorysnapshot', batch_size)
