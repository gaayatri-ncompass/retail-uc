from src.utils.logger import logger
from src.utils.error_handler import handle_error
from transform import df_cleaning, phone_cleanup, split_address

def transform_dim_table(staging_db, table_name, column_mapping_dict):
    try:
        df = staging_db.read_table(table_name)
        df = df_cleaning.clean_dataframe(df)

        original_columns = set(df.columns)

        if table_name == 'customers':
            df = split_address.split_address(df)
            df = phone_cleanup.clean_phone_numbers(df)

        column_mapping = column_mapping_dict.get(table_name)
        if not column_mapping:
            raise ValueError(f"No column mapping defined for table: {table_name}")
        df.rename(columns=column_mapping, inplace=True)
        renamed_columns = set(column_mapping.values())

        current_columns = set(df.columns)
        new_columns = current_columns - renamed_columns - original_columns

        final_columns = list(renamed_columns) + list(new_columns)
        df = df[final_columns]
        logger.info("Table Transformations applied...")

        return df
    except Exception as e:
        handle_error("Failed to apply table transformations")

def transform_fact_sales(staging_db, warehouse_db, column_mapping_dict):
    try:
        df_sales = staging_db.read_table('sales')
        df_sales = df_cleaning.clean_dataframe(df_sales)

        dim_customer = warehouse_db.read_table('dim_customer')[['customer_id', 'customer_key']]
        dim_product = warehouse_db.read_table('dim_product')[['product_id', 'product_key']]
        dim_store = warehouse_db.read_table('dim_store')[['store_id', 'store_key']]
        dim_date = warehouse_db.read_table('dim_date')[['date', 'date_key']]

        df_sales = df_sales.merge(dim_customer, on='customer_id', how='left')
        df_sales = df_sales.merge(dim_product, on='product_id', how='left')
        df_sales = df_sales.merge(dim_store, on='store_id', how='left')
        df_sales = df_sales.merge(dim_date, left_on='sale_date', right_on='date', how='left')

        column_mapping = column_mapping_dict.get('sales')
        if not column_mapping:
            raise ValueError("No column mapping defined for 'sales'")
        df_sales.rename(columns=column_mapping, inplace=True)

        final_columns = list(column_mapping.values())
        df_sales = df_sales[final_columns]

        logger.info("Fact Sales transformation complete with surrogate keys.")
        return df_sales
    except:
        handle_error("Failed to transform table")
