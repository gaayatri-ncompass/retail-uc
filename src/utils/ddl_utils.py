from src.utils.logger import logger
from src.utils.error_handler import handle_error

def create_tables(db,sql_commands):
    for table_name, sql in sql_commands.items():
        try:
            logger.info(f"Creating Table: {table_name}")
            db.execute_query(sql)
            logger.info(f"{table_name} created")
        except Exception as e:
            handle_error(f"Table creation failed for {table_name}: {str(e)}")
    logger.info("All tables created")

def drop_tables(db, drop_commands):
    for name, sql in drop_commands.items():
        try:
            logger.info(f"Dropping table via: {name}")
            db.execute_query(sql)
        except Exception as e:
            handle_error("Could not Drop Table")
    logger.info("All tables dropped.")
