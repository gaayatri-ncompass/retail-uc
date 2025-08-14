from src.extract.extractor import run_extraction
from src.transform.transformer import run_transformation
from src.load.loader import run_loading
from src.utils.exceptions import ETLError, ExtractionError, TransformationError, LoadingError
from logger import get_logger

# Initialize simple logger
logger = get_logger("MAIN")


def main():
    """Main ETL process function"""
    logger.info("ETL process started...")

    try:
        logger.info("=" * 50)
        logger.info("STEP 1: EXTRACTION")
        logger.info("=" * 50)
        extracted_data = run_extraction()
        logger.info("Extraction phase completed successfully")

        logger.info("=" * 50)
        logger.info("STEP 2: TRANSFORMATION")
        logger.info("=" * 50)
        transformed_data = run_transformation()
        logger.info("Transformation phase completed successfully")

        logger.info("=" * 50)
        logger.info("STEP 3: LOADING")
        logger.info("=" * 50)
        if transformed_data:
            run_loading(transformed_data)
            logger.info("Loading phase completed successfully")
        else:
            raise LoadingError("No transformed data to load", "LOAD001")

        logger.info("=" * 50)
        logger.info("ETL process finished successfully.")
        logger.info("=" * 50)

    except ExtractionError as e:
        logger.error(f"ETL process failed during extraction phase: {e}")
        logger.error("ETL process failed during extraction phase.")

    except TransformationError as e:
        logger.error(f"ETL process failed during transformation phase: {e}")
        logger.error("ETL process failed during transformation phase.")

    except LoadingError as e:
        logger.error(f"ETL process failed during loading phase: {e}")
        logger.error("ETL process failed during loading phase.")

    except ETLError as e:
        logger.error(f"ETL process failed with a general error: {e}")
        logger.error("ETL process failed with a general error.")

    except Exception as e:
        logger.critical(
            f"ETL process failed with an unexpected error: {str(e)}")
        logger.critical("ETL process failed with an unexpected error.")


if __name__ == "__main__":
    main()
