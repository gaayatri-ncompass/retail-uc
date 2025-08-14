import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.utils.config import get_staging_db_connector, get_warehouse_db_connector
from src.utils.exceptions import TransformationError, DatabaseError


def clean_customer_data(df):

    if df.empty:
        return df

    df = df.drop_duplicates(subset=['customer_id'])

    df.loc[:, 'email'] = df['email'].str.lower().str.strip()
    df.loc[:, 'phone'] = df['phone'].str.replace(r'[^\d+]', '', regex=True)
    df.loc[:, 'address'] = df['address'].str.strip()
    df.loc[:, 'signup_date'] = pd.to_datetime(
        df['signup_date'], errors='coerce')

    df = df.dropna(subset=['signup_date'])

    return df


def clean_product_data(df):

    if df.empty:
        return df

    df = df.drop_duplicates(subset=['product_id'])

    df.loc[:, 'product_name'] = df['product_name'].str.strip()
    df.loc[:, 'category'] = df['category'].str.strip()
    df.loc[:, 'price'] = pd.to_numeric(df['price'], errors='coerce')

    df = df.dropna(subset=['price'])

    return df


def clean_store_data(df):

    if df.empty:
        return df

    df = df.drop_duplicates(subset=['store_id'])

    df.loc[:, 'store_name'] = df['store_name'].str.strip()
    df.loc[:, 'location'] = df['location'].str.strip()

    return df


def clean_supplier_data(df):

    if df.empty:
        return df

    df = df.drop_duplicates(subset=['supplier_id'])

    df.loc[:, 'supplier_name'] = df['supplier_name'].str.strip()
    df.loc[:, 'contact_name'] = df['contact_name'].str.strip()

    return df


def clean_sales_data(df):

    if df.empty:
        return df

    df = df.drop_duplicates(subset=['sale_id'])

    df.loc[:, 'quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
    df.loc[:, 'total_amount'] = pd.to_numeric(
        df['total_amount'], errors='coerce')
    df.loc[:, 'sale_date'] = pd.to_datetime(df['sale_date'], errors='coerce')

    df = df.dropna(subset=['quantity', 'total_amount', 'sale_date'])

    df.loc[:, 'payment_type'] = 'Credit Card'
    df.loc[:, 'channel'] = 'In-Store'

    return df


def clean_inventory_data(df):

    if df.empty:
        return df

    df = df.drop_duplicates(subset=['product_id', 'store_id', 'last_updated'])

    df.loc[:, 'stock_level'] = pd.to_numeric(
        df['stock_level'], errors='coerce')
    df.loc[:, 'last_updated'] = pd.to_datetime(
        df['last_updated'], errors='coerce')

    df = df.dropna(subset=['stock_level', 'last_updated'])

    return df


def create_date_dimension(start_date, end_date):

    date_range = pd.date_range(start=start_date, end=end_date, freq='D')

    date_dim = pd.DataFrame({
        'full_date': date_range,
        'year': date_range.year,
        'month': date_range.month,
        'day': date_range.day,
        'quarter': date_range.quarter,
        'week': date_range.isocalendar().week
    })

    date_dim['date_key'] = date_dim['full_date'].dt.strftime(
        '%Y%m%d').astype(int)

    return date_dim


def create_promotion_dimension():
    pass


def transform_data():
    """Transform staging data to warehouse-ready format using incremental processing"""

    print("Starting incremental data transformation using metadata watermarks...")

    staging_db = get_staging_db_connector()
    warehouse_db = get_warehouse_db_connector()

    try:
        staging_db.connect()
        warehouse_db.connect()

        try:
            print("Reading incremental data from staging tables using metadata...")

            # Get watermarks from ETL metadata table
            customers_watermark = staging_db.run_query(
                "SELECT last_processed_id FROM etl_process_log WHERE table_name = 'stg_customers'"
            )
            products_watermark = staging_db.run_query(
                "SELECT last_processed_id FROM etl_process_log WHERE table_name = 'stg_products'"
            )
            stores_watermark = staging_db.run_query(
                "SELECT last_processed_id FROM etl_process_log WHERE table_name = 'stg_stores'"
            )
            suppliers_watermark = staging_db.run_query(
                "SELECT last_processed_id FROM etl_process_log WHERE table_name = 'stg_suppliers'"
            )
            sales_watermark = staging_db.run_query(
                "SELECT last_processed_id FROM etl_process_log WHERE table_name = 'stg_sales'"
            )
            inventory_watermark = staging_db.run_query(
                "SELECT last_processed_id FROM etl_process_log WHERE table_name = 'stg_inventory'"
            )

            customer_last_id = customers_watermark.iloc[0][
                'last_processed_id'] if customers_watermark is not None and not customers_watermark.empty else 'CUST0'
            product_last_id = products_watermark.iloc[0][
                'last_processed_id'] if products_watermark is not None and not products_watermark.empty else 'PROD0'
            store_last_id = stores_watermark.iloc[0][
                'last_processed_id'] if stores_watermark is not None and not stores_watermark.empty else 'STORE0'
            supplier_last_id = suppliers_watermark.iloc[0][
                'last_processed_id'] if suppliers_watermark is not None and not suppliers_watermark.empty else 'SUP0'
            sales_last_id = sales_watermark.iloc[0]['last_processed_id'] if sales_watermark is not None and not sales_watermark.empty else 'SALE0'
            inventory_last_id = inventory_watermark.iloc[0][
                'last_processed_id'] if inventory_watermark is not None and not inventory_watermark.empty else '1900-01-01'

            print(
                f"Metadata watermarks - Customer: {customer_last_id}, Product: {product_last_id}, Store: {store_last_id}, Supplier: {supplier_last_id}, Sales: {sales_last_id}, Inventory: {inventory_last_id}")

            customers_df = staging_db.run_query(
                f"SELECT * FROM stg_customers WHERE customer_id > '{customer_last_id}' ORDER BY customer_id")
            products_df = staging_db.run_query(
                f"SELECT * FROM stg_products WHERE product_id > '{product_last_id}' ORDER BY product_id")
            stores_df = staging_db.run_query(
                f"SELECT * FROM stg_stores WHERE store_id > '{store_last_id}' ORDER BY store_id")
            suppliers_df = staging_db.run_query(
                f"SELECT * FROM stg_suppliers WHERE supplier_id > '{supplier_last_id}' ORDER BY supplier_id")
            sales_df = staging_db.run_query(
                f"SELECT * FROM stg_sales WHERE sale_id > '{sales_last_id}' ORDER BY sale_id")
            inventory_df = staging_db.run_query(
                f"SELECT * FROM stg_inventory WHERE last_updated > '{inventory_last_id}' ORDER BY last_updated")

            # Handle None results
            if customers_df is None:
                customers_df = pd.DataFrame()
            if products_df is None:
                products_df = pd.DataFrame()
            if stores_df is None:
                stores_df = pd.DataFrame()
            if suppliers_df is None:
                suppliers_df = pd.DataFrame()
            if sales_df is None:
                sales_df = pd.DataFrame()
            if inventory_df is None:
                inventory_df = pd.DataFrame()

            print(
                f"Incremental data found: customers={len(customers_df)}, products={len(products_df)}, stores={len(stores_df)}, suppliers={len(suppliers_df)}, sales={len(sales_df)}, inventory={len(inventory_df)}")

        except Exception as e:
            raise DatabaseError(
                f"Failed to extract data from staging: {str(e)}", "DB004")

        try:
            print("Cleaning customer data...")
            customers_clean = clean_customer_data(customers_df)

            print("Cleaning product data...")
            products_clean = clean_product_data(products_df)

            print("Cleaning store data...")
            stores_clean = clean_store_data(stores_df)

            print("Cleaning supplier data...")
            suppliers_clean = clean_supplier_data(suppliers_df)

            print("Cleaning sales data...")
            sales_clean = clean_sales_data(sales_df)

            print("Cleaning inventory data...")
            inventory_clean = clean_inventory_data(inventory_df)
        except Exception as e:
            raise TransformationError(
                f"Data cleaning failed: {str(e)}", "TRF001")

        try:
            print("Creating date dimension...")
            if not sales_clean.empty and not inventory_clean.empty:
                min_date = min(sales_clean['sale_date'].min(
                ), inventory_clean['last_updated'].min())
                max_date = max(sales_clean['sale_date'].max(
                ), inventory_clean['last_updated'].max())
            elif not sales_clean.empty:
                min_date = sales_clean['sale_date'].min()
                max_date = sales_clean['sale_date'].max()
            elif not inventory_clean.empty:
                min_date = inventory_clean['last_updated'].min()
                max_date = inventory_clean['last_updated'].max()
            else:
                min_date = pd.Timestamp('2020-01-01')
                max_date = pd.Timestamp('2030-12-31')

            min_date = min_date - pd.DateOffset(years=1)

            max_date = max_date + pd.DateOffset(years=2)

            print(
                f"Creating date dimension from {min_date.date()} to {max_date.date()}")
            date_dim = create_date_dimension(min_date, max_date)

            print("Creating promotion dimension...")
            promotion_dim = create_promotion_dimension()
        except Exception as e:
            raise TransformationError(
                f"Dimension creation failed: {str(e)}", "TRF002")

        transformed_data = {
            'customers': customers_clean,
            'products': products_clean,
            'stores': stores_clean,
            'suppliers': suppliers_clean,
            'sales': sales_clean,
            'inventory': inventory_clean,
            'dates': date_dim,
            'promotions': promotion_dim
        }

        try:
            print("Updating ETL metadata watermarks...")

            if not customers_clean.empty:
                latest_customer = customers_clean['customer_id'].max()
                staging_db.execute_query(
                    f"INSERT INTO etl_process_log (table_name, last_processed_id, last_updated) "
                    f"VALUES ('stg_customers', '{latest_customer}', NOW()) "
                    f"ON DUPLICATE KEY UPDATE last_processed_id = '{latest_customer}', last_updated = NOW()"
                )
                print(f"Updated customer watermark to: {latest_customer}")

            if not products_clean.empty:
                latest_product = products_clean['product_id'].max()
                staging_db.execute_query(
                    f"INSERT INTO etl_process_log (table_name, last_processed_id, last_updated) "
                    f"VALUES ('stg_products', '{latest_product}', NOW()) "
                    f"ON DUPLICATE KEY UPDATE last_processed_id = '{latest_product}', last_updated = NOW()"
                )
                print(f"Updated product watermark to: {latest_product}")

            if not stores_clean.empty:
                latest_store = stores_clean['store_id'].max()
                staging_db.execute_query(
                    f"INSERT INTO etl_process_log (table_name, last_processed_id, last_updated) "
                    f"VALUES ('stg_stores', '{latest_store}', NOW()) "
                    f"ON DUPLICATE KEY UPDATE last_processed_id = '{latest_store}', last_updated = NOW()"
                )
                print(f"Updated store watermark to: {latest_store}")

            if not suppliers_clean.empty:
                latest_supplier = suppliers_clean['supplier_id'].max()
                staging_db.execute_query(
                    f"INSERT INTO etl_process_log (table_name, last_processed_id, last_updated) "
                    f"VALUES ('stg_suppliers', '{latest_supplier}', NOW()) "
                    f"ON DUPLICATE KEY UPDATE last_processed_id = '{latest_supplier}', last_updated = NOW()"
                )
                print(f"Updated supplier watermark to: {latest_supplier}")

            if not sales_clean.empty:
                latest_sale = sales_clean['sale_id'].max()
                staging_db.execute_query(
                    f"INSERT INTO etl_process_log (table_name, last_processed_id, last_updated) "
                    f"VALUES ('stg_sales', '{latest_sale}', NOW()) "
                    f"ON DUPLICATE KEY UPDATE last_processed_id = '{latest_sale}', last_updated = NOW()"
                )
                print(f"Updated sales watermark to: {latest_sale}")

            if not inventory_clean.empty:
                latest_inventory = inventory_clean['last_updated'].max().strftime(
                    '%Y-%m-%d %H:%M:%S')
                staging_db.execute_query(
                    f"INSERT INTO etl_process_log (table_name, last_processed_id, last_updated) "
                    f"VALUES ('stg_inventory', '{latest_inventory}', NOW()) "
                    f"ON DUPLICATE KEY UPDATE last_processed_id = '{latest_inventory}', last_updated = NOW()"
                )
                print(f"Updated inventory watermark to: {latest_inventory}")

        except Exception as e:
            print(f"Warning: Failed to update ETL metadata: {e}")

        print("Data transformation completed successfully!")
        return transformed_data

    except (TransformationError, DatabaseError):
        raise
    except Exception as e:
        raise TransformationError(
            f"Transformation process failed: {str(e)}", "TRF003")
    finally:
        staging_db.disconnect()
        warehouse_db.disconnect()


def run_transformation():
    return transform_data()
