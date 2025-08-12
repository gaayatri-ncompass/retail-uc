import os
from dotenv import load_dotenv
from src.utils.db import DB

load_dotenv()

def get_staging_db():
    return DB(
            host=os.getenv('HOST'),
            user=os.getenv('USER'),
            password=os.getenv('PASSWORD'),
            database=os.getenv('STAGING_DB'),
            port=os.getenv('PORT')
    )

def get_target_db():
    return DB(
        host=os.getenv('HOST'),
        user=os.getenv('USER'),
        password=os.getenv('PASSWORD'),
        database=os.getenv('TARGET_DB'),
        port=os.getenv('PORT')
    )