from dagster import Definitions
from src.assets.metadata.fetch_metadata import fetch_metadata
from src.assets.extract.ingestion_factory import create_db_ingestion_assets
from src.assets.transform.dim_customers import transform_dim_customer
from src.assets.transform.dim_products import transform_dim_product
from src.assets.transform.fact_sales import transform_fact_sales
from src.assets.load.load_dimensions import load_dim_customer, load_dim_product
from src.assets.load.load_facts import load_fact_sales
from src.resources.databases import db_resource,warehouse_resource
from src.utils.db_connection import get_db
from src.utils.tables import get_tables, get_primary_key
import os
from dotenv import load_dotenv

load_dotenv()

db = get_db("SOURCE_DB")
db.connect_to_engine()

schema = os.getenv("SOURCE_DB")
table_names = get_tables(db, schema)
table_names = [table for table in table_names if table != 'asset_metadata']

primary_keys = {
    table: (
        "surrogate_id" if table == "products" else
        "surrogate_id" if table == "product_categories" else
        get_primary_key(db, schema, table)
    )
    for table in table_names
    if table != "asset_metadata"
}

ingestion_assets = create_db_ingestion_assets(table_names, primary_keys)


defs = Definitions(
    assets=[
        fetch_metadata,
        *ingestion_assets,
        transform_dim_customer,
        transform_dim_product,
        transform_fact_sales,
        load_dim_customer,
        load_dim_product,
        load_fact_sales
    ],
    resources={"db": db_resource, "warehouse": warehouse_resource}
)