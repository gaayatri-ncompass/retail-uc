import os
from dotenv import load_dotenv
from src.utils.db_connector import DBConnector


load_dotenv()


def get_staging_db_connector():
    
    return DBConnector(
        host=os.getenv('STAGING_DB_HOST', 'localhost'),
        user=os.getenv('STAGING_DB_USER', 'root'),
        password=os.getenv('STAGING_DB_PASSWORD', 'deva'),
        database=os.getenv('STAGING_DB_NAME', 'stagingdb')
    )


def get_warehouse_db_connector():
    
    return DBConnector(
        host=os.getenv('WAREHOUSE_DB_HOST', 'localhost'),
        user=os.getenv('WAREHOUSE_DB_USER', 'root'),
        password=os.getenv('WAREHOUSE_DB_PASSWORD', 'deva'),
        database=os.getenv('WAREHOUSE_DB_NAME', 'warehousedb')
    )
