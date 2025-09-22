from dagster import asset, AssetIn
import duckdb
import pandas as pd

@asset(
    name="transform_dim_product",
    ins={
        "ingest_products": AssetIn("ingest_products"),
        "ingest_product_categories": AssetIn("ingest_product_categories"),
    },
    compute_kind="duckdb",
)
def transform_dim_product(
    context,
    ingest_products: pd.DataFrame,
    ingest_product_categories: pd.DataFrame,
) -> pd.DataFrame:
    con = duckdb.connect()

    con.register("products", ingest_products)
    con.register("product_categories", ingest_product_categories)

    query = """
   WITH cleaned_products AS (
    SELECT
        product_id,
        product_name,
        product_cost,
        start_date,
        end_date,
        -- Extract category from first two segments
        REPLACE(
            split_part(product_id, '-', 1) || '_' || split_part(product_id, '-', 2),
            '-', '_'
        ) AS category,
        -- Extract last three segments as sales_product_id
        split_part(product_id, '-', 3) || '-' || 
        split_part(product_id, '-', 4) || '-' || 
        split_part(product_id, '-', 5) AS sales_product_id
    FROM products
)
SELECT
    cp.product_id,
    cp.sales_product_id,
    cp.product_name,
    cp.product_cost,
    cp.start_date,
    cp.end_date,
    pc.category AS category_name,
    pc.subcategory,
    pc.maintenance
FROM cleaned_products cp
LEFT JOIN product_categories pc
    ON cp.category = pc.category_id;
    """

    dim_product = con.execute(query).fetchdf()
    context.log.info(f"transform_dim_product shape: {dim_product.shape}")
    context.log.info(f"transform_dim_product preview:\n{dim_product.head().to_string(index=False)}")
    print(dim_product.head())
    con.close()

    return dim_product
