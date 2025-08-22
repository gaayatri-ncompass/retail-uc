from configs.db_config import get_staging_db_connector
from src.utils.exceptions import DatabaseError
from src.utils.validator import validate_dataframe
from src.utils.logger import get_logger

logger = get_logger("DATA_LOADER")


class DataLoader:
    def __init__(self):
        self.db = get_staging_db_connector()
        self.db.connect()

    def _get_last_processed_id(self, table_name):
        log_query = "SELECT last_processed_id FROM etl_process_log WHERE table_name = :table_name"
        last_id_df = self.db.run_query_with_params(
            log_query, {'table_name': table_name})

        if last_id_df is not None and not last_id_df.empty:
            return last_id_df['last_processed_id'].iloc[0]
        return None

    def _filter_incremental_data(self, df, pk_column, last_processed_id):
        if last_processed_id:
            return df[df[pk_column] > last_processed_id]
        return df

    def load_to_staging(self, df, file_name, table_name, pk_column):
        if df.empty:
            return True

        last_processed_id = self._get_last_processed_id(table_name)
        df_to_insert = self._filter_incremental_data(
            df, pk_column, last_processed_id)

        if df_to_insert.empty:
            logger.info(f"No new data for {table_name}")
            return True

        is_valid = validate_dataframe(df_to_insert, table_name)
        if not is_valid:
            logger.warning(f"Data validation issues for {table_name}")

        table_full_name = f'stg_{table_name}'
        try:
            df_to_insert.to_sql(
                name=table_full_name,
                con=self.db.engine,
                if_exists='append',
                index=False
            )
            logger.info(f"Loaded {len(df_to_insert)} records to {table_name}")
        except Exception as e:
            logger.error(f"Failed to load data to {table_full_name}: {str(e)}")
            raise DatabaseError(
                f"Failed to load data to staging table: {str(e)}")

        return True
