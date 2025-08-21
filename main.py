from src.extract.extractor import run_extraction
from src.transform.transformer import run_transformation
from src.load.loader import run_loading
from src.utils.exceptions import ETLError, ExtractionError, TransformationError, LoadingError
from src.utils.logger import get_logger

logger = get_logger("MAIN")


def main():
    logger.process_start("ETL Process")

    try:
        # Step 1: Extraction
        logger.process_start("Extraction")
        run_extraction()
        logger.process_end("Extraction")

        # Step 2: Transformation
        logger.process_start("Transformation")
        transform_result = run_transformation()
        logger.process_end("Transformation")

        # Step 3: Loading
        logger.process_start("Loading")
        if not transform_result:
            raise LoadingError("No transformed data to load", "LOAD001")

        run_loading(transform_result)
        logger.process_end("Loading")

        logger.success("ETL process completed successfully")

    except (ExtractionError, TransformationError, LoadingError, ETLError) as e:
        logger.error(f"ETL process failed: {e}")
        raise
    except Exception as e:
        logger.critical(f"ETL process failed with unexpected error: {str(e)}")
        raise ETLError(f"Unexpected error: {str(e)}", "ETL001")


if __name__ == "__main__":
    main()
