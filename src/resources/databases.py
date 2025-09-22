from dagster import resource
from src.utils.db_connection import get_db

@resource
def db_resource():
    db = get_db('SOURCE_DB')
    db.connect_to_engine()
    return db

@resource
def warehouse_resource():
    dwh = get_db('TARGET_DB')
    dwh.connect_to_engine()
    return dwh