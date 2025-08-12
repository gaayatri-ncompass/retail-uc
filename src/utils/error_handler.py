from src.utils.logger import logger

def handle_error(context: str, exception: Exception, raise_error=True):
    logger.error(f"[{context}] Error: {exception}")
    if raise_error:
        raise exception