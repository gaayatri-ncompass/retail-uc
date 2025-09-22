from dagster import asset, AssetIn

@asset(
    name="load_dim_customer",
    ins={"transform_dim_customer": AssetIn("transform_dim_customer")},
    required_resource_keys={"warehouse"},
    compute_kind="warehouse",
)
def load_dim_customer(context, transform_dim_customer):
    context.log.info("Loading dim_customer into warehouse...")
    context.log.info(f"Loading {len(transform_dim_customer)} rows into dim_customer")
    context.log.info(f"Preview:\n{transform_dim_customer.head().to_string(index=False)}")

    context.resources.warehouse.df_to_sql(
        df=transform_dim_customer,
        table_name="dim_customer",
        index=False
    )

    loaded_df = context.resources.warehouse.query_df("SELECT * FROM dim_customer")
    context.log.info(f"Loaded dim_customer shape: {loaded_df.shape}")
    context.log.info(f"Loaded preview:\n{loaded_df.head().to_string(index=False)}")

    return loaded_df

@asset(
    name="load_dim_product",
    ins={"transform_dim_product": AssetIn("transform_dim_product")},
    required_resource_keys={"warehouse"},
    compute_kind="warehouse",
)
def load_dim_product(context, transform_dim_product):
    context.log.info("Loading dim_product into warehouse...")
    context.log.info(f"Loading {len(transform_dim_product)} rows into dim_product")
    context.log.info(f"Preview:\n{transform_dim_product.head().to_string(index=False)}")
    context.resources.warehouse.df_to_sql(
        df=transform_dim_product,
        table_name="dim_product",
        index=False
    )
    loaded_df = context.resources.warehouse.query_df("SELECT * FROM dim_product")
    context.log.info(f"Loaded dim_product shape: {loaded_df.shape}")
    context.log.info(f"Loaded preview:\n{loaded_df.head().to_string(index=False)}")
    return loaded_df
