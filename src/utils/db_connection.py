import os
from dotenv import load_dotenv
from src.utils.db import DB

load_dotenv()

def get_db(db_name_env_var):
    return DB(
        host=os.getenv('HOST'),
        user=os.getenv('USER'),
        password=os.getenv('PASSWORD'),
        database=os.getenv(db_name_env_var),
        port=os.getenv('PORT')
    )
