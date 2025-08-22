from src.extract.extractor import run_extraction
from src.extract.staging_extractor import run_staging_extraction
from src.transform.transformer import transform_staging_data
from src.load.loader import run_loading
from src.utils.exceptions import ETLError, ExtractionError, TransformationError, LoadingError
from src.utils.logger import get_logger

logger = get_logger("MAIN")


def main():
    logger.info("Starting ETL Process")

    try:

        logger.info("Running extraction...")
        run_extraction()

        logger.info("Extracting new data from staging...")
        staging_data = run_staging_extraction()

        if not staging_data:
            logger.info("No new data found - ETL process complete")
            return True

        # Step 3: Transformation (In-Memory) - dimensions only
        logger.info("Transforming data...")
        transform_result = transform_staging_data(staging_data)

        # Step 4: Loading (to Warehouse) - facts will be transformed during loading
        logger.info("Loading to warehouse...")
        if not transform_result:
            raise LoadingError("No transformed data to load", "LOAD001")

        # Pass staging data through for fact transformation after dimension loading
        transform_result['staging_data'] = staging_data
        run_loading(transform_result)
        logger.success("ETL process completed successfully")

    except (ExtractionError, TransformationError, LoadingError, ETLError) as e:
        logger.error(f"ETL process failed: {e}")
        raise
    except Exception as e:
        logger.critical(f"ETL process failed with unexpected error: {str(e)}")
        raise ETLError(f"Unexpected error: {str(e)}", "ETL001")


if __name__ == "__main__":
    main()
