"""
Transform Utilities - Consolidated Helper Functions
=================================================
All reusable transformation utilities in one modular file.
"""

import pandas as pd
from src.utils.logger import get_logger
from src.utils.rejected_data_handler import save_rejected_sales_data, save_rejected_inventory_data

logger = get_logger("TRANSFORM_UTILS")


def get_all_dimension_keys(db):
    """Get all dimension keys in a single optimized function"""
    try:
        keys = {}

        # Single query approach for better performance
        queries = {
            'customers': "SELECT customer_key, customer_id FROM dimcustomer",
            'products': "SELECT product_key, product_id FROM dimproduct",
            'stores': "SELECT store_key, store_id FROM dimstore",
            'suppliers': "SELECT supplier_key, supplier_id FROM dimsupplier",
            'dates': "SELECT date_key FROM dimdate",
            'default_promotion': "SELECT promotion_key FROM dimpromotion LIMIT 1"
        }

        for dim_name, query in queries.items():
            result = db.query(query)
            if result is not None and not result.empty:
                if dim_name == 'dates':
                    keys[dim_name] = set(result['date_key'].tolist())
                elif dim_name == 'default_promotion':
                    keys[dim_name] = result['promotion_key'].iloc[0]
                else:
                    id_col = f"{dim_name[:-1]}_id"
                    key_col = f"{dim_name[:-1]}_key"
                    keys[dim_name] = dict(zip(result[id_col], result[key_col]))
            else:
                keys[dim_name] = {} if dim_name not in [
                    'dates', 'default_promotion'] else (set() if dim_name == 'dates' else 1)

        logger.debug(
            f"Retrieved keys: {len(keys['customers'])} customers, {len(keys['products'])} products")
        return keys
    except Exception as e:
        logger.error(f"Error retrieving dimension keys: {e}")
        return None


def apply_incremental_logic(db, df, fact_type, id_column):
    """Generic incremental processing for any fact table"""
    try:
        table_name = 'factsales' if fact_type == 'sales' else 'factinventorysnapshot'
        count_result = db.query(f"SELECT COUNT(*) as count FROM {table_name}")

        if count_result is not None and not count_result.empty and count_result['count'].iloc[0] > 0:
            if fact_type == 'sales':
                max_result = db.query(
                    f"SELECT MAX({id_column}) as max_id FROM {table_name}")
                if max_result is not None and not max_result.empty and max_result['max_id'].iloc[0]:
                    max_id = max_result['max_id'].iloc[0]
                    df = df[df[id_column] > max_id]
                    logger.info(f"Incremental filter: {id_column} > {max_id}")
            else:
                existing_ids = db.query(
                    f"SELECT DISTINCT inventory_id FROM {table_name}")
                if existing_ids is not None and not existing_ids.empty:
                    df = df[~df['inventory_id'].isin(
                        existing_ids['inventory_id'].tolist())]
                    logger.info("Filtered out existing inventory records")
        else:
            logger.info(
                f"No existing {fact_type} data, processing all records")

        return df
    except Exception as e:
        logger.error(f"Error in incremental logic for {fact_type}: {e}")
        return df


def map_fact_dimensions(df, dimension_keys, fact_type):
    """Generic dimension key mapping for fact tables"""
    fact_df = df.copy()

    if fact_type == 'sales':
        # Sales dimension mapping
        fact_df['customer_key'] = fact_df['customer_id'].map(
            dimension_keys['customers'])
        fact_df['product_key'] = fact_df['product_id'].map(
            dimension_keys['products'])
        fact_df['store_key'] = fact_df['store_id'].map(
            dimension_keys['stores'])
        fact_df['promotion_key'] = dimension_keys['default_promotion']

        # Date key handling
        if 'sale_date' in fact_df.columns:
            fact_df['date_key'] = pd.to_datetime(
                fact_df['sale_date']).dt.strftime('%Y%m%d').astype(int)
            logger.info("Created date_key from sale_date")

    elif fact_type == 'inventory':
        # Inventory dimension mapping
        fact_df['product_key'] = fact_df['product_id'].map(
            dimension_keys['products'])
        fact_df['store_key'] = fact_df['store_id'].map(
            dimension_keys['stores'])
        fact_df['supplier_key'] = fact_df['supplier_id'].map(
            dimension_keys['suppliers'])

        # Create inventory_id if missing
        if 'inventory_id' not in fact_df.columns:
            fact_df['inventory_id'] = (fact_df['product_id'].astype(str) + '_' +
                                       fact_df['store_id'].astype(str) + '_' +
                                       fact_df['last_updated'].astype(str))

        # Date key from last_updated
        if 'last_updated' in fact_df.columns:
            fact_df['date_key'] = pd.to_datetime(
                fact_df['last_updated']).dt.strftime('%Y%m%d').astype(int)

    return fact_df


def validate_fact_data(df, required_keys, fact_type):
    """Generic validation and rejection handling for fact data"""
    # Check missing keys
    missing_counts = {key: df[key].isna().sum() for key in required_keys}
    for key, count in missing_counts.items():
        if count > 0:
            logger.warning(f"Found {count} records with missing {key}")

    # Save rejected records
    rejected_df = df[df[required_keys].isna().any(axis=1)]
    if not rejected_df.empty:
        if fact_type == 'sales':
            save_rejected_sales_data(
                rejected_df, "Missing dimension keys", missing_counts)
        else:
            save_rejected_inventory_data(
                rejected_df, "Missing dimension keys", missing_counts)
        logger.warning(
            f"Rejected {len(rejected_df)} records due to missing keys")

    # Return only valid records
    return df.dropna(subset=required_keys)


def prepare_fact_columns(df, fact_type):
    """Prepare final columns for fact tables"""
    if fact_type == 'sales':
        # Add defaults and timestamp
        for col, default in [('payment_type', 'Credit Card'), ('channel', 'InStore')]:
            if col not in df.columns:
                df[col] = default
        df['created_at'] = pd.Timestamp.now()

        return df[['sale_id', 'customer_key', 'product_key', 'store_key', 'date_key',
                  'promotion_key', 'quantity', 'total_amount', 'payment_type', 'channel', 'created_at']]

    elif fact_type == 'inventory':
        return df[['inventory_id', 'product_key', 'store_key', 'date_key', 'supplier_key', 'stock_level']]


def validate_required_columns(df, required_cols, fact_type):
    """Validate that required columns exist in the DataFrame"""
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(
            f"Missing required columns in {fact_type} data: {missing_cols}")
        return False
    return True


def remove_fact_duplicates(df, fact_type):
    """Remove duplicates from fact data"""
    if fact_type == 'inventory' and 'inventory_id' in df.columns:
        initial_count = len(df)
        df = df.drop_duplicates(subset=['inventory_id'], keep='last')
        if len(df) != initial_count:
            logger.info(
                f"Removed {initial_count - len(df)} duplicate inventory records")
    return df
