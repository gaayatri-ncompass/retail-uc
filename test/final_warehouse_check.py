#!/usr/bin/env python3
"""Check warehouse table counts"""

import mysql.connector

try:
    # Connect to warehouse database
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='deva',
        database='warehouseDb'
    )
    cursor = conn.cursor()

    print("WAREHOUSE TABLE COUNTS")
    print("=" * 25)

    # Check dimension tables
    dimension_tables = ['dimcustomer', 'dimproduct',
                        'dimstore', 'dimsupplier', 'dimdate']

    print("DIMENSION TABLES:")
    for table in dimension_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count:,} records")
        except Exception as e:
            print(f"  {table}: Error - {e}")

    print("\nFACT TABLES:")
    # Check fact tables
    fact_tables = ['factsales', 'factinventorysnapshot']

    for table in fact_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count:,} records")
        except Exception as e:
            print(f"  {table}: Error - {e}")

    # Sample sales data
    print("\nSAMPLE SALES DATA:")
    try:
        cursor.execute("SELECT * FROM factsales LIMIT 3")
        rows = cursor.fetchall()
        if rows:
            print("Sample records found:")
            for row in rows:
                print(
                    f"  Sale ID: {row[0]}, Customer: {row[1]}, Product: {row[2]}, Store: {row[3]}")
        else:
            print("No records found in factsales")
    except Exception as e:
        print(f"Error checking sample data: {e}")

    conn.close()

except Exception as e:
    print(f"Connection error: {e}")
    print(f"Error type: {type(e)}")
    import traceback
    traceback.print_exc()
