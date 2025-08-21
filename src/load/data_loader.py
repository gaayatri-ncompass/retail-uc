from src.utils.config import get_staging_db_connector
from src.utils.exceptions import DatabaseError
from src.utils.validator import validate_dataframe
from logger import get_logger

logger = get_logger("DATA_LOADER")


class DataLoader:
    def __init__(self):
        self.db = get_staging_db_connector()

    def load_chunks_to_staging(self, data_chunks, file_name, table_name, pk_column):

        logger.info(f"Loading {file_name} to staging table {table_name}")

        try:
            total_processed = 0
            chunks_validated = 0
            validation_passed = 0

            # Get last processed ID
            log_query = "SELECT last_processed_id FROM etl_process_log WHERE table_name = :table_name"
            last_id_df = self.db.run_query_with_params(
                log_query, {'table_name': table_name})

            last_processed_id = None
            if last_id_df is not None and not last_id_df.empty:
                last_processed_id = last_id_df['last_processed_id'].iloc[0]

            # Process each chunk
            for chunk_num, df_chunk in data_chunks:

                # Filter based on last processed ID
                if last_processed_id:
                    df_to_insert = df_chunk[df_chunk[pk_column]
                                            > last_processed_id]
                else:
                    df_to_insert = df_chunk

                if df_to_insert.empty:
                    continue

                # Validate data
                chunks_validated += 1
                is_valid = validate_dataframe(df_to_insert, table_name)
                if is_valid:
                    validation_passed += 1
                else:
                    logger.warning(
                        f"Data validation issues found for {table_name} chunk {chunk_num}")

                # Load to staging table
                table_full_name = f'stg_{table_name}'
                df_to_insert.to_sql(name=table_full_name,
                                    con=self.db.engine, if_exists='append', index=False)

                chunk_processed = len(df_to_insert)
                total_processed += chunk_processed

            # Log validation summary
            if chunks_validated > 0:
                logger.info(
                    f"Validation summary for {table_name}: {validation_passed}/{chunks_validated} chunks passed validation")

            logger.info(
                f"Total new records processed for {table_name}: {total_processed}")

            # Update process log
            if total_processed > 0:
                max_id_query = f"SELECT MAX({pk_column}) as max_id FROM stg_{table_name}"
                max_id_df = self.db.run_query(max_id_query)
                if max_id_df is not None and not max_id_df.empty:
                    max_id = max_id_df['max_id'].iloc[0]

                    update_query = """
                        INSERT INTO etl_process_log (table_name, last_processed_id, last_updated)
                        VALUES (:table_name, :max_id, CURRENT_TIMESTAMP)
                        ON DUPLICATE KEY UPDATE last_processed_id = :max_id, last_updated = CURRENT_TIMESTAMP
                    """
                    self.db.execute_query_with_params(update_query, {
                        'table_name': table_name,
                        'max_id': max_id
                    })

            return True

        except Exception as e:
            logger.error(f"Error loading {file_name}: {str(e)}")
            raise DatabaseError(f"Error loading {file_name}: {str(e)}")
