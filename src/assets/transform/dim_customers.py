from dagster import asset, AssetIn
import duckdb
import pandas as pd

@asset(
    name="transform_dim_customer",
    ins={
        "ingest_customers": AssetIn("ingest_customers"),
        "ingest_customer_locations": AssetIn("ingest_customer_locations"),
        "ingest_customer_birthdates": AssetIn("ingest_customer_birthdates"),
    },
    compute_kind="duckdb",
)
def transform_dim_customer(
    context,
    ingest_customers: pd.DataFrame,
    ingest_customer_locations: pd.DataFrame,
    ingest_customer_birthdates: pd.DataFrame,
) -> pd.DataFrame:
    con = duckdb.connect()

    # Register DataFrames
    con.register("customers", ingest_customers)
    con.register("customer_locations", ingest_customer_locations)
    con.register("customer_birthdates", ingest_customer_birthdates)

    query = """
        SELECT
            c.customer_id,
            c.first_name,
            c.last_name,
            CASE
                WHEN LOWER(c.gender) = 'f' THEN 'Female'
                WHEN LOWER(c.gender) = 'm' THEN 'Male'
                WHEN LOWER(b.gender) = 'females' THEN 'Female'
                WHEN LOWER(b.gender) = 'males' THEN 'Male'
                ELSE 'Unknown'
            END AS gender,
            c.marital_status,
            l.country,
            b.birthdate AS birth_date,
            c.created_date AS customer_created_date
        FROM customers c
        LEFT JOIN customer_locations l ON c.customer_id = l.customer_id
        LEFT JOIN customer_birthdates b ON c.customer_id = b.customer_id;
    """

    dim_customer = con.execute(query).fetchdf()
    context.log.info(f"transform_dim_customer shape: {dim_customer.shape}")
    context.log.info(f"transform_dim_customer preview:\n{dim_customer.head().to_string(index=False)}")
    con.close()

    return dim_customer
