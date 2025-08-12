from src.utils.logger import logger
from src.utils.error_handler import handle_error
def load_to_data_warehouse(target_db, df, table_name, if_exists='replace'):
    if df.empty:
        logger.info(f"Skipping load: DataFrame for '{table_name}' is empty.")
        return

    try:
        target_db.df_to_sql(df,table_name)
        logger.info(f"Loaded '{table_name}' to data warehouse with {len(df)} rows.")
    except Exception as e:
        handle_error(f"Failed to load '{table_name}")