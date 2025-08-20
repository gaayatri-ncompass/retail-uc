import pandas as pd
import os
from datetime import datetime


def inject_bad_data():

    print("Adding bad data to test rejection handling...")

    try:
        customers_df = pd.read_csv('data/customers.csv')

        bad_customers = pd.DataFrame([
            {
                'customer_id': '',
                'customer_name': 'Bad Customer 1',
                'email': 'invalid-email-format',  # Bad email
                'phone': '1234567890',
                'address': '123 Bad St',
                'signup_date': '2024-01-01'
            },
            {
                'customer_id': 'BAD_CUST_001',
                'customer_name': 'Bad Customer 2',
                'email': 'another-bad-email',  # Bad email
                'phone': 'ABC-DEF-GHIJ',  # Bad phone
                'address': '456 Bad Ave',
                'signup_date': 'invalid-date'  # Bad date
            }
        ])

        updated_customers = pd.concat(
            [customers_df, bad_customers], ignore_index=True)
        updated_customers.to_csv('data/customers.csv', index=False)
        print(f"Added {len(bad_customers)} bad customers")

    except Exception as e:
        print(f"✗ Error with customers: {e}")

    # Bad products - add to existing products.csv
    try:
        products_df = pd.read_csv('data/products.csv')

        bad_products = pd.DataFrame([
            {
                'product_id': '',  # Missing ID
                'product_name': 'Bad Product 1',
                'category': 'Test',
                'price': 'not-a-number'  # Bad price
            },
            {
                'product_id': 'BAD_PROD_001',
                'product_name': 'Bad Product 2',
                'category': '',  # Empty category
                'price': '-50.00'  # Negative price
            }
        ])

        updated_products = pd.concat(
            [products_df, bad_products], ignore_index=True)
        updated_products.to_csv('data/products.csv', index=False)
        print(f"✓ Added {len(bad_products)} bad products")

    except Exception as e:
        print(f"✗ Error with products: {e}")

    # Bad sales - add to existing sales.csv
    try:
        sales_df = pd.read_csv('data/sales.csv')

        bad_sales = pd.DataFrame([
            {
                'sale_id': 'BAD_SALE_001',
                'customer_id': 'NONEXISTENT_CUSTOMER',  # FK violation
                'product_id': 'NONEXISTENT_PRODUCT',    # FK violation
                'store_id': 'NONEXISTENT_STORE',        # FK violation
                'sale_date': '2024-01-01',
                'quantity': '1',
                'total_amount': '100.00'
            },
            {
                'sale_id': 'BAD_SALE_002',
                'customer_id': 'CUST1000',  # Valid customer (Existing data)
                'product_id': 'PROD1000',   # Valid product (Existing data)
                'store_id': 'STORE100',     # Valid store (Existing data)
                'sale_date': 'bad-date',    # Bad date format
                'quantity': 'abc',          # Bad quantity
                'total_amount': 'xyz'       # Bad amount
            }
        ])

        updated_sales = pd.concat([sales_df, bad_sales], ignore_index=True)
        updated_sales.to_csv('data/sales.csv', index=False)
        print(f"Added {len(bad_sales)} bad sales")

    except Exception as e:
        print(f"Error with sales: {e}")

    print("\nBad data injection complete!")


if __name__ == "__main__":
    print("=" * 50)
    print("BAD DATA INJECTOR")
    print("=" * 50)
    inject_bad_data()
