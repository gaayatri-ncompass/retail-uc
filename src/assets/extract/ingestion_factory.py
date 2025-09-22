from dagster import asset, AssetIn
from typing import Dict
import pandas as pd

def create_db_ingestion_assets(table_names, primary_keys):
    assets = []

    for table_name in table_names:
        pk = primary_keys.get(table_name, "id")

        def make_ingest_asset(table_name=table_name, pk=pk):
            @asset(
                name=f"ingest_{table_name}",
                ins={"fetch_metadata": AssetIn("fetch_metadata")},
                compute_kind="database",
                required_resource_keys={"db"},
            )
            def ingest_table(context, fetch_metadata: Dict[str, int]) -> pd.DataFrame:
                db = context.resources.db
                last_id = fetch_metadata.get(table_name, 0)

                context.log.info(f"Ingesting {table_name} from {pk} > {last_id}")
                df = db.query_df(f"SELECT * FROM {table_name} WHERE {pk} > {last_id}")

                context.log.info(f"{table_name} shape: {df.shape}")
                if not df.empty:
                    context.log.info(f"{table_name} preview:\n{df.head().to_string(index=False)}")
                    new_max_id = int(df[pk].max())
                    db.update_last_processed_id("ingestion", source_table=table_name, target_table="", new_id=new_max_id)
                else:
                    context.log.info(f"{table_name} returned no new rows.")

                return df

            return ingest_table

        assets.append(make_ingest_asset())

    return assets
