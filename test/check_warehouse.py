#!/usr/bin/env python3
"""Check warehouse data counts"""

import mysql.connector


def check_warehouse_data():
    """Check record counts in warehouse tables"""
    try:
        # Connect to warehouse
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='deva',
            database='warehouseDb'
        )
        cursor = conn.cursor()

        print("WAREHOUSE DATA COUNTS")
        print("=" * 25)

        tables = [
            'dimcustomer', 'dimproduct', 'dimstore', 'dimsupplier',
            'dimdate', 'dimpromotion', 'factsales', 'factinventorysnapshot'
        ]

        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"{table}: {count:,} records")
            except Exception as e:
                print(f"{table}: Error - {e}")

        conn.close()

    except Exception as e:
        print(f"Error checking warehouse: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_warehouse_data()
