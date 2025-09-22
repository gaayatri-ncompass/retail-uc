from dagster import asset, AssetIn

@asset(
    name="load_fact_sales",
    ins={"transform_fact_sales": AssetIn("transform_fact_sales")},
    required_resource_keys={"warehouse"},
    compute_kind="warehouse",
)
def load_fact_sales(context, transform_fact_sales):
    context.log.info("Loading fact sales into warehouse...")
    context.log.info(f"Loading {len(transform_fact_sales)} rows into fact_sales")
    context.log.info(f"Preview:\n{transform_fact_sales.head().to_string(index=False)}")

    try:
        context.resources.warehouse.df_to_sql(
            df=transform_fact_sales,
            table_name="fact_sales",
            index=False
        )
        context.log.info("fact_sales successfully written to warehouse.")
    except Exception as e:
        context.log.error(f"Error loading fact_sales: {e}")
        raise

    row_count = context.resources.warehouse.query_df("SELECT COUNT(*) FROM fact_sales")
    context.log.info(f"Row count in fact_sales: {row_count.iloc[0, 0]}")


    return "fact_sales loaded"