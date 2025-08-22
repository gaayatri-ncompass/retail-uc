import os
import pandas as pd
from datetime import datetime
from src.utils.logger import get_logger

logger = get_logger("REJECTED_DATA")


REJECTED_FOLDER_PATH = "rejected_data"


def save_rejected_data(df, table_name, reason, additional_info=None):

    if df is None or df.empty:
        return

    try:

        folder = REJECTED_FOLDER_PATH

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        filename = f"{table_name}_rejected_{timestamp}.csv"
        filepath = os.path.join(folder, filename)

        df_with_metadata = df.copy()
        df_with_metadata['rejection_reason'] = reason
        df_with_metadata['rejection_timestamp'] = datetime.now()
        if additional_info:
            df_with_metadata['additional_info'] = additional_info

        df_with_metadata.to_csv(filepath, index=False)

        # Only log once per batch/table, not for every duplicate error
        if "Duplicate" not in reason:
            logger.warning(
                f"Saved {len(df)} rejected {table_name} records to: {filepath}")
            logger.warning(f"Rejection reason: {reason}")

        return filepath

    except Exception as e:
        logger.error(f"Failed to save rejected data for {table_name}: {e}")
        return None


def save_rejected_sales_data(rejected_df, reason, missing_keys_info=None):

    additional_info = None
    if missing_keys_info:
        additional_info = f"Missing keys: {missing_keys_info}"

    return save_rejected_data(rejected_df, "factsales", reason, additional_info)


def save_rejected_inventory_data(rejected_df, reason, missing_keys_info=None):

    additional_info = None
    if missing_keys_info:
        additional_info = f"Missing keys: {missing_keys_info}"

    return save_rejected_data(rejected_df, "factinventorysnapshot", reason, additional_info)


def save_rejected_dimension_data(rejected_df, table_name, reason):

    return save_rejected_data(rejected_df, table_name, reason)
