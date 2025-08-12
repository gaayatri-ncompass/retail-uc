from src.utils.logger import logger
from src.utils.error_handler import handle_error

import pandas as pd
import os

def extract_csv(file_path):
    logger.info("Extracting the data from csv")
    if not os.path.exists(file_path):
        logger.warning(f"Could not find the file: {file_path}")
        return None
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Extracted Data from {file_path}")
        return df
    except Exception as e:
        handle_error(f"Failed to extract from {file_path}")
        return None
    