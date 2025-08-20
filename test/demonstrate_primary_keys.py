#!/usr/bin/env python3
"""
Demonstrate different ways to get primary keys dynamically from database
"""

import mysql.connector
import pandas as pd
from src.utils.config import get_staging_db_connector


def get_primary_keys_using_information_schema(db_connection):
    """Method 1: Using INFORMATION_SCHEMA (Cross-database compatible)"""

    query = """
    SELECT 
        TABLE_NAME,
        COLUMN_NAME,
        CONSTRAINT_NAME
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = DATABASE()
    AND CONSTRAINT_NAME = 'PRIMARY'
    ORDER BY TABLE_NAME
    """

    result = db_connection.run_query(query)

    print("=== METHOD 1: INFORMATION_SCHEMA.KEY_COLUMN_USAGE ===")
    if result is not None and not result.empty:
        for _, row in result.iterrows():
            print(
                f"Table: {row['TABLE_NAME']:<20} Primary Key: {row['COLUMN_NAME']}")
    else:
        print("No primary keys found")

    return result


def get_primary_keys_using_describe(db_connection):
    """Method 2: Using DESCRIBE/SHOW COLUMNS (MySQL specific)"""

    # First get all table names
    tables_query = """
    SELECT TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_TYPE = 'BASE TABLE'
    """

    tables = db_connection.run_query(tables_query)

    print("\n=== METHOD 2: DESCRIBE TABLE (MySQL specific) ===")

    primary_keys = {}

    if tables is not None and not tables.empty:
        for _, table_row in tables.iterrows():
            table_name = table_row['TABLE_NAME']

            # Use DESCRIBE to get table structure
            describe_query = f"DESCRIBE {table_name}"
            columns = db_connection.run_query(describe_query)

            if columns is not None and not columns.empty:
                # Find primary key column
                primary_key_cols = columns[columns['Key']
                                           == 'PRI']['Field'].tolist()

                if primary_key_cols:
                    # Take first if composite
                    primary_keys[table_name] = primary_key_cols[0]
                    print(
                        f"Table: {table_name:<20} Primary Key: {primary_key_cols[0]}")

    return primary_keys


def get_primary_keys_using_show_columns(db_connection):
    """Method 3: Using SHOW COLUMNS (MySQL specific, alternative syntax)"""

    # Get all table names
    tables_query = """
    SELECT TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_TYPE = 'BASE TABLE'
    """

    tables = db_connection.run_query(tables_query)

    print("\n=== METHOD 3: SHOW COLUMNS (MySQL specific) ===")

    primary_keys = {}

    if tables is not None and not tables.empty:
        for _, table_row in tables.iterrows():
            table_name = table_row['TABLE_NAME']

            # Use SHOW COLUMNS to get table structure
            show_query = f"SHOW COLUMNS FROM {table_name}"
            columns = db_connection.run_query(show_query)

            if columns is not None and not columns.empty:
                # Find primary key column
                primary_key_cols = columns[columns['Key']
                                           == 'PRI']['Field'].tolist()

                if primary_key_cols:
                    primary_keys[table_name] = primary_key_cols[0]
                    print(
                        f"Table: {table_name:<20} Primary Key: {primary_key_cols[0]}")

    return primary_keys


def get_all_constraints_information_schema(db_connection):
    """Method 4: Get all constraint information (comprehensive)"""

    query = """
    SELECT 
        kcu.TABLE_NAME,
        kcu.COLUMN_NAME,
        kcu.CONSTRAINT_NAME,
        tc.CONSTRAINT_TYPE
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
    JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc 
        ON kcu.CONSTRAINT_NAME = tc.CONSTRAINT_NAME 
        AND kcu.TABLE_SCHEMA = tc.TABLE_SCHEMA
    WHERE kcu.TABLE_SCHEMA = DATABASE()
    ORDER BY kcu.TABLE_NAME, tc.CONSTRAINT_TYPE
    """

    result = db_connection.run_query(query)

    print("\n=== METHOD 4: ALL CONSTRAINTS (Comprehensive) ===")
    if result is not None and not result.empty:
        current_table = None
        for _, row in result.iterrows():
            if current_table != row['TABLE_NAME']:
                current_table = row['TABLE_NAME']
                print(f"\nTable: {current_table}")

            print(
                f"  {row['CONSTRAINT_TYPE']:<15} {row['COLUMN_NAME']:<20} ({row['CONSTRAINT_NAME']})")

    return result


def demonstrate_dynamic_primary_key_detection():
    """Demonstrate all methods of getting primary keys"""

    print("Dynamic Primary Key Detection Methods")
    print("=" * 60)

    # Connect to staging database
    staging_db = get_staging_db_connector()
    staging_db.connect()

    try:
        # Method 1: INFORMATION_SCHEMA (Recommended - Cross-database)
        method1_result = get_primary_keys_using_information_schema(staging_db)

        # Method 2: DESCRIBE (MySQL specific)
        method2_result = get_primary_keys_using_describe(staging_db)

        # Method 3: SHOW COLUMNS (MySQL specific alternative)
        method3_result = get_primary_keys_using_show_columns(staging_db)

        # Method 4: All constraints (Comprehensive)
        method4_result = get_all_constraints_information_schema(staging_db)

        print("\n" + "=" * 60)
        print("RECOMMENDATION:")
        print("Use INFORMATION_SCHEMA.KEY_COLUMN_USAGE (Method 1)")
        print("- Works across different database systems")
        print("- Standard SQL approach")
        print("- Most reliable and portable")

    finally:
        staging_db.disconnect()


if __name__ == "__main__":
    demonstrate_dynamic_primary_key_detection()
