from src.extract.extractor import run_extraction
from src.transform.transformer import run_transformation
from src.load.loader import run_loading
import logging


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s')


def main():

    print("ETL process started...")

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
        print("No transformed data to load")

    print("=" * 50)
    print("ETL process finished successfully.")
    print("=" * 50)


# Run the main function
if __name__ == "__main__":
    main()
