from src.utils.logger import logger

def clean_dataframe(df, drop_nulls=True, drop_duplicates=True, verbose=True):
    print("Cleaning Data....")
    if drop_nulls:
        df = df.dropna()
        if verbose:
            logger.info("Dropped nulls. New shape:")

    if drop_duplicates:
        df = df.drop_duplicates()
        if verbose:
            logger.info("Dropped duplicates")
    return df
