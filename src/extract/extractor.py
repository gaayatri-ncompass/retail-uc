import pandas as pd
from src.utils.exceptions import ExtractionError
from src.load.data_loader import DataLoader
from src.utils.logger import get_logger
from configs.metadata_config import get_expected_columns, get_extraction_config

logger = get_logger("EXTRACT")


def extract_csv_data(file_name, table_name):
    try:
        dataframe = pd.read_csv(f'data/{file_name}', dtype=str)

        expected_columns_dict = get_expected_columns()
        expected_columns = expected_columns_dict.get(table_name, [])
        if expected_columns:
            missing_columns = [
                col for col in expected_columns
                if col not in dataframe.columns
            ]
            if missing_columns:
                raise ExtractionError(
                    f"Missing expected columns in {file_name}: {missing_columns}"
                )

            dataframe = dataframe[expected_columns]

        dataframe = dataframe.drop_duplicates()
        return dataframe

    except Exception as e:
        raise ExtractionError(f"Error extracting {file_name}: {str(e)}")


def run_extraction():
    extraction_config = get_extraction_config()
    data_loader = DataLoader()

    for file_name, table_name, primary_key_column in extraction_config:
        extracted_data = extract_csv_data(file_name, table_name)
        data_loader.load_to_staging(
            extracted_data, file_name, table_name, primary_key_column
        )

    logger.success("Extraction completed")
    return True
