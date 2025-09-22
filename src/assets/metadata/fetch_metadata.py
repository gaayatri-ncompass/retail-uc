from dagster import asset
from typing import Dict
import pandas as pd

@asset(name="fetch_metadata", compute_kind="database", required_resource_keys={"db"})
def fetch_metadata(context) -> Dict[str, int]:
    db = context.resources.db
    context.log.info("Fetching last processed IDs from asset_metadata for ingestion")

    sql = """
        SELECT source_table, last_processed_id
        FROM asset_metadata
        WHERE asset_name = 'ingestion'
    """
    df = db.query_df(sql)

    if df is None or df.empty:
        return {}

    return dict(zip(df["source_table"], df["last_processed_id"]))
