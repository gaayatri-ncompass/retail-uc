
from src.utils.config import get_staging_db_connector
import sys
sys.path.append('.')


def clear_watermarks():
    print('Clearing all watermarks...')
    db = get_staging_db_connector()
    db.connect()

    # Show current watermarks
    current = db.run_query('SELECT * FROM etl_process_log')
    if current is not None and not current.empty:
        print(f'Found {len(current)} watermarks to clear')

    # Clear all watermarks
    result = db.execute_query('DELETE FROM etl_process_log')
    print(f'Watermarks cleared: {result}')

    # Verify
    after = db.run_query('SELECT COUNT(*) as count FROM etl_process_log')
    print(
        f'Remaining watermarks: {after.iloc[0]["count"] if after is not None else "unknown"}')

    db.disconnect()
    print('Watermarks cleared successfully')


if __name__ == '__main__':
    clear_watermarks()
