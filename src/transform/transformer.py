import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.utils.config import get_staging_db_connector, get_warehouse_db_connector


def clean_customer_data(df):

    if df.empty:
        return df

    df = df.drop_duplicates(subset=['customer_id'])

    df['email'] = df['email'].str.lower().str.strip()

    df['phone'] = df['phone'].str.replace(r'[^\d+]', '', regex=True)

    df['address'] = df['address'].str.strip()
    df['signup_date'] = pd.to_datetime(df['signup_date'], errors='coerce')

    df = df.dropna(subset=['signup_date'])

    return df


def clean_product_data(df):

    if df.empty:
        return df

    df = df.drop_duplicates(subset=['product_id'])

    df['product_name'] = df['product_name'].str.strip()

    df['category'] = df['category'].str.strip()

    df['price'] = pd.to_numeric(df['price'], errors='coerce')

    df = df.dropna(subset=['price'])

    return df


def clean_store_data(df):

    if df.empty:
        return df

    df = df.drop_duplicates(subset=['store_id'])

    df['store_name'] = df['store_name'].str.strip()

    df['location'] = df['location'].str.strip()

    return df


def clean_supplier_data(df):

    if df.empty:
        return df

    df = df.drop_duplicates(subset=['supplier_id'])

    df['supplier_name'] = df['supplier_name'].str.strip()

    df['contact_name'] = df['contact_name'].str.strip()

    return df


def clean_sales_data(df):

    if df.empty:
        return df

    df = df.drop_duplicates(subset=['sale_id'])

    df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')

    df['total_amount'] = pd.to_numeric(df['total_amount'], errors='coerce')

    df['sale_date'] = pd.to_datetime(df['sale_date'], errors='coerce')

    df = df.dropna(subset=['quantity', 'total_amount', 'sale_date'])

    df['payment_type'] = 'Credit Card'
    df['channel'] = 'In-Store'

    return df


def clean_inventory_data(df):

    if df.empty:
        return df

    df = df.drop_duplicates(subset=['product_id', 'store_id', 'last_updated'])

    df['stock_level'] = pd.to_numeric(df['stock_level'], errors='coerce')

    df['last_updated'] = pd.to_datetime(df['last_updated'], errors='coerce')

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

    print("Starting data transformation...")

    staging_db = get_staging_db_connector()
    staging_db.connect()

    warehouse_db = get_warehouse_db_connector()
    warehouse_db.connect()

    try:

        customers_df = staging_db.run_query("SELECT * FROM stg_customers")
        products_df = staging_db.run_query("SELECT * FROM stg_products")
        stores_df = staging_db.run_query("SELECT * FROM stg_stores")
        suppliers_df = staging_db.run_query("SELECT * FROM stg_suppliers")
        sales_df = staging_db.run_query("SELECT * FROM stg_sales")
        inventory_df = staging_db.run_query("SELECT * FROM stg_inventory")

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
            max_date = pd.Timestamp('2025-12-31')

        date_dim = create_date_dimension(min_date, max_date)

        print("Creating promotion dimension...")
        promotion_dim = create_promotion_dimension()

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

        print("Data transformation completed successfully!")
        return transformed_data

    except Exception as e:
        print(f"Error during transformation: {str(e)}")
        return None
    finally:
        staging_db.disconnect()
        warehouse_db.disconnect()


def run_transformation():
    return transform_data()
