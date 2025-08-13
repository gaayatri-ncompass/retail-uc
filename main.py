from src.extract.extractor import run_extraction
from src.transform.transformer import run_transformation
from src.load.loader import run_loading
from src.utils.exceptions import ETLError, ExtractionError, TransformationError, LoadingError
import logging


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s')


def main():

    print("ETL process started...")

    try:
        print("=" * 50)
        print("STEP 1: EXTRACTION")
        print("=" * 50)
        extracted_data = run_extraction()

        # 2. Transform
        print("=" * 50)
        print("STEP 2: TRANSFORMATION")
        print("=" * 50)
        transformed_data = run_transformation()

        # 3. Load
        print("=" * 50)
        print("STEP 3: LOADING")
        print("=" * 50)
        if transformed_data:
            run_loading(transformed_data)
        else:
            raise LoadingError("No transformed data to load", "LOAD001")

        print("=" * 50)
        print("ETL process finished successfully.")
        print("=" * 50)

    except ExtractionError as e:
        print(f" {e}")
        print("ETL process failed during extraction phase.")

    except TransformationError as e:
        print(f" {e}")
        print("ETL process failed during transformation phase.")

    except LoadingError as e:
        print(f" {e}")
        print("ETL process failed during loading phase.")

    except ETLError as e:
        print(f" {e}")
        print("ETL process failed with a general error.")

    except Exception as e:
        print(f" Unexpected error: {str(e)}")
        print("ETL process failed with an unexpected error.")


if __name__ == "__main__":
    main()
