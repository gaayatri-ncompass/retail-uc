import os
from io import StringIO
import pandas as pd
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
        """Get last processed ID from ETL metadata."""
        query = "SELECT last_processed_id FROM etl_process_log WHERE table_name = :table_name"
        result = self.db.run_query_with_params(
            query, {'table_name': table_name})
        return result['last_processed_id'].iloc[0] if result is not None and not result.empty else None

    def _get_id_from_line(self, line, pk_column_index=0):
        """Extract ID from a CSV line."""
        try:
            parts = line.strip().split(',')
            if len(parts) > pk_column_index:
                return int(parts[pk_column_index].strip('"').strip("'"))
        except (ValueError, IndexError):
            pass
        return None

    def _get_pk_column_index(self, file_path, pk_column):
        """Get the index of primary key column in CSV."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                headers = [col.strip().strip('"').strip("'")
                           for col in f.readline().strip().split(',')]
            return headers.index(pk_column) if pk_column in headers else 0
        except Exception as e:
            logger.warning(f"Could not determine PK column index: {e}")
            return 0

    def _binary_search_start_position(self, file_path, target_id, pk_column_index=0):
        """Use binary search to find the byte position where ID > target_id starts."""
        if target_id is None:
            return 0

        logger.info(f"Binary searching for position where ID > {target_id}")

        with open(file_path, 'rb') as f:
            f.seek(0, os.SEEK_END)
            file_size = f.tell()
            f.seek(0)
            f.readline()
            start_pos = f.tell()

            if start_pos >= file_size:
                return file_size

            low, high, result_pos = start_pos, file_size, file_size

            while low < high:
                mid = (low + high) // 2
                f.seek(mid)
                if mid > start_pos:
                    f.readline()

                line_pos = f.tell()
                line = f.readline()

                if not line:
                    high = mid
                    continue

                try:
                    line_str = line.decode('utf-8', errors='ignore')
                    record_id = self._get_id_from_line(
                        line_str, pk_column_index)

                    if record_id is None:
                        low = f.tell()
                    elif record_id <= target_id:
                        low = f.tell()
                    else:
                        result_pos = line_pos
                        high = mid
                except UnicodeDecodeError:
                    low = f.tell()

            logger.info(
                f"Binary search found start position at byte {result_pos}")
            return result_pos

    def _read_from_byte_position(self, file_path, start_byte_pos):
        """Read CSV data starting from a specific byte position."""
        try:
            if start_byte_pos == 0:
                logger.info("Reading entire CSV file")
                return pd.read_csv(file_path, dtype=str)

            file_size = os.path.getsize(file_path)
            if start_byte_pos >= file_size:
                logger.info("Start position is at end of file - no new data")
                return pd.DataFrame()

            with open(file_path, 'rb') as f:
                f.seek(start_byte_pos)
                remaining_data = f.read()

            if not remaining_data:
                logger.info("No new data to read")
                return pd.DataFrame()

            data_str = remaining_data.decode('utf-8', errors='ignore')
            column_names = pd.read_csv(file_path, nrows=0).columns.tolist()
            new_data = pd.read_csv(StringIO(data_str), header=None, dtype=str)

            if not new_data.empty:
                new_data.columns = column_names
                logger.info(f"Read {len(new_data)} new records from CSV")

            return new_data

        except Exception as e:
            logger.error(
                f"Error reading from byte position {start_byte_pos}: {e}")
            raise DatabaseError(f"Error reading CSV: {e}")

    def _update_process_log(self, table_name, pk_column):
        """Update ETL process log with latest processed ID."""
        max_id_query = f"SELECT MAX({pk_column}) as max_id FROM stg_{table_name}"
        max_id_df = self.db.run_query(max_id_query)

        if max_id_df is not None and not max_id_df.empty:
            max_id = max_id_df['max_id'].iloc[0]
            update_query = """
                INSERT INTO etl_process_log (table_name, last_processed_id, last_updated)
                VALUES (:table_name, :max_id, CURRENT_TIMESTAMP)
                ON DUPLICATE KEY UPDATE last_processed_id = :max_id, last_updated = CURRENT_TIMESTAMP
            """
            self.db.execute_query_with_params(
                update_query, {'table_name': table_name, 'max_id': max_id})
            logger.info(
                f"Updated ETL metadata: {table_name} max_id = {max_id}")

    def load_to_staging(self, file_path, file_name, table_name, pk_column):
        """Load only new data using binary search optimization."""
        logger.info(
            f"Loading {file_name} to staging table {table_name} using binary search")

        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False

        last_processed_id = self._get_last_processed_id(table_name)
        logger.info(f"Last processed ID for {table_name}: {last_processed_id}")

        pk_column_index = self._get_pk_column_index(file_path, pk_column)
        start_byte_pos = self._binary_search_start_position(
            file_path, last_processed_id, pk_column_index)
        new_data = self._read_from_byte_position(file_path, start_byte_pos)

        if new_data.empty:
            logger.info(f"No new data to load for {table_name}")
            return True

        # Filter out already processed records
        if last_processed_id is not None and pk_column in new_data.columns:
            new_data[pk_column] = pd.to_numeric(
                new_data[pk_column], errors='coerce')
            new_data = new_data[new_data[pk_column] > last_processed_id]

        if new_data.empty:
            logger.info(f"No new records after filtering for {table_name}")
            return True

        # Validate and load data
        is_valid = validate_dataframe(new_data, table_name)
        if not is_valid:
            logger.warning(f"Data validation issues found for {table_name}")

        try:
            new_data.to_sql(
                name=f'stg_{table_name}',
                con=self.db.engine,
                if_exists='append',
                index=False,
                method='multi'
            )
            self._update_process_log(table_name, pk_column)
            logger.data_summary(table_name, len(new_data), "loaded to staging")
            return True

        except Exception as e:
            logger.error(f"Failed to load data to stg_{table_name}: {e}")
            raise DatabaseError(f"Failed to load data to staging table: {e}")
