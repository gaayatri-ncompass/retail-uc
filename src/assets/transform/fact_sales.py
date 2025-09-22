from dagster import asset, AssetIn
import duckdb
import pandas as pd

@asset(
    name="transform_fact_sales",
    ins={
        "ingest_sales": AssetIn("ingest_sales"),
        "load_dim_customer": AssetIn("load_dim_customer"),
        "load_dim_product": AssetIn("load_dim_product"),
    },
    compute_kind="duckdb",
)
def transform_fact_sales(
    context,
    ingest_sales: pd.DataFrame,
    load_dim_customer: pd.DataFrame,
    load_dim_product: pd.DataFrame,
) -> pd.DataFrame:
    con = duckdb.connect()
    con.register("sales", ingest_sales)
    con.register("dim_customer", load_dim_customer)
    con.register("dim_product", load_dim_product)

    query = """
    SELECT
        s.order_id,
        dc.customer_key,
        dp.product_key,
        s.order_date AS order_date_key,
        s.ship_date AS ship_date_key,
        s.due_date AS due_date_key,
        s.sales_amount,
        s.quantity,
        s.price
    FROM sales s
    LEFT JOIN dim_customer dc ON s.customer_id = dc.customer_id
    LEFT JOIN dim_product dp ON s.product_id = dp.sales_product_id
    WHERE s.order_id IS NOT NULL
    """

    fact_sales = con.execute(query).fetchdf()
    con.close()

    context.log.info(f"Fact sales shape: {fact_sales.shape}")
    context.log.info(f"Fact sales preview:\n{fact_sales.head().to_string(index=False)}")
    context.log.info(f"Fact sales duplicates:\n{fact_sales.duplicated().sum()}")

    return fact_sales
