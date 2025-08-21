import pandas as pd
from src.utils.exceptions import ExtractionError
from src.load.data_loader import DataLoader
from logger import get_logger

logger = get_logger("EXTRACT")

EXPECTED_COLUMNS = {
    'customers': ['customer_id', 'customer_name', 'email', 'phone', 'address', 'signup_date'],
    'products': ['product_id', 'product_name', 'category', 'price'],
    'stores': ['store_id', 'store_name', 'location', 'manager'],
    'sales': ['sale_id', 'customer_id', 'product_id', 'store_id', 'sale_date', 'quantity', 'total_amount'],
    'inventory': ['product_id', 'store_id', 'stock_level', 'last_updated', 'supplier_id'],
    'suppliers': ['supplier_id', 'supplier_name', 'contact_name', 'contact_email']
}


def extract_csv_data(file_name, table_name, chunk_size=1000):
    logger.info(f"Extracting data from {file_name}")
    try:
        for chunk_num, df_chunk in enumerate(pd.read_csv(f'data/{file_name}', dtype=str, chunksize=chunk_size), 1):
            if chunk_num == 1:
                expected_cols = EXPECTED_COLUMNS.get(table_name, [])
                if expected_cols:
                    missing_cols = []
                    for col in expected_cols:
                        if col not in df_chunk.columns:
                            missing_cols.append(col)
                    if missing_cols:
                        logger.error(
                            f"Missing expected columns in {file_name}: {missing_cols}")
                        raise ExtractionError(
                            f"Missing expected columns in {file_name}: {missing_cols}")
            # Select expected columns
            expected_cols = EXPECTED_COLUMNS.get(table_name, [])
            if expected_cols:
                df_chunk = df_chunk[expected_cols]
            # Remove duplicates
            df_chunk.drop_duplicates(inplace=True)
            yield chunk_num, df_chunk
    except FileNotFoundError:
        logger.error(f"CSV file not found: data/{file_name}")
        raise ExtractionError(f"CSV file not found: data/{file_name}")
    except pd.errors.EmptyDataError:
        logger.error(f"CSV file is empty: data/{file_name}")
        raise ExtractionError(f"CSV file is empty: data/{file_name}")
    except Exception as e:
        logger.error(f"Error extracting {file_name}: {str(e)}")
        raise ExtractionError(f"Error extracting {file_name}: {str(e)}")


def run_extraction():

    logger.info("Starting extraction process")

    extraction_config = [
        ('customers.csv', 'customers', 'customer_id'),
        ('products.csv', 'products', 'product_id'),
        ('stores.csv', 'stores', 'store_id'),
        ('sales.csv', 'sales', 'sale_id'),
        ('inventory.csv', 'inventory', 'product_id'),
        ('suppliers.csv', 'suppliers', 'supplier_id')
    ]

    # Initialize the data loader
    data_loader = DataLoader()

    try:
        for file_name, table_name, pk_column in extraction_config:
            logger.info(f"Processing {file_name} -> {table_name}")

            # Extract data chunks from CSV
            data_chunks = extract_csv_data(file_name, table_name)

            # Load chunks to staging table
            data_loader.load_chunks_to_staging(
                data_chunks, file_name, table_name, pk_column)

            logger.info(f"Successfully processed {file_name}")

        logger.info("Extraction process completed successfully")
        return True

    except Exception as e:
        logger.error(f"Extraction process failed: {str(e)}")
        raise ExtractionError(f"Extraction process failed: {str(e)}")
