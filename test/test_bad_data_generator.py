"""
Bad Data Generator Test Script

This script generates various types of bad data to test the ETL pipeline's
data validation and rejection handling capabilities.

Tests include:
1. Missing required fields
2. Invalid data types
3. Non-existent foreign keys
4. Invalid date formats
5. Negative values where not allowed
6. Email format violations
7. Phone number format issues
8. Extremely long strings
9. NULL values in required fields
10. Duplicate records with same primary key
"""

import pandas as pd
import os
import csv
import random
import string
from datetime import datetime, timedelta
from src.utils.config import get_staging_db_connector
from logger import get_logger

logger = get_logger("BAD_DATA_TEST")


def create_bad_customers_data():
    """Generate bad customer data with various validation issues"""
    logger.info("Generating bad customer data...")

    bad_customers = [
        # Missing required customer_id
        {
            'customer_id': '',
            'customer_name': 'John Doe',
            'email': 'john@example.com',
            'phone': '1234567890',
            'address': '123 Main St',
            'signup_date': '2024-01-01'
        },

        # Invalid email format
        {
            'customer_id': 'BAD_CUST_001',
            'customer_name': 'Jane Smith',
            'email': 'invalid-email-format',
            'phone': '1234567890',
            'address': '456 Oak Ave',
            'signup_date': '2024-01-02'
        },

        # NULL customer_name
        {
            'customer_id': 'BAD_CUST_002',
            'customer_name': None,
            'email': 'null.name@example.com',
            'phone': '1234567890',
            'address': '789 Pine St',
            'signup_date': '2024-01-03'
        },

        # Invalid phone format (contains letters)
        {
            'customer_id': 'BAD_CUST_003',
            'customer_name': 'Bob Johnson',
            'email': 'bob@example.com',
            'phone': 'ABC-DEF-GHIJ',
            'address': '321 Elm St',
            'signup_date': '2024-01-04'
        },

        # Extremely long address (>500 chars)
        {
            'customer_id': 'BAD_CUST_004',
            'customer_name': 'Alice Brown',
            'email': 'alice@example.com',
            'phone': '5551234567',
            'address': 'A' * 600,  # Too long
            'signup_date': '2024-01-05'
        },

        # Invalid date format
        {
            'customer_id': 'BAD_CUST_005',
            'customer_name': 'Charlie Wilson',
            'email': 'charlie@example.com',
            'phone': '5551234567',
            'address': '654 Maple Dr',
            'signup_date': 'not-a-date'
        },

        # Duplicate customer_id
        {
            'customer_id': 'BAD_CUST_001',  # Duplicate
            'customer_name': 'Duplicate Customer',
            'email': 'duplicate@example.com',
            'phone': '5551234567',
            'address': '999 Duplicate St',
            'signup_date': '2024-01-06'
        }
    ]

    return pd.DataFrame(bad_customers)


def create_bad_products_data():
    """Generate bad product data with various validation issues"""
    logger.info("Generating bad product data...")

    bad_products = [
        # Missing required product_id
        {
            'product_id': '',
            'product_name': 'Test Product',
            'category': 'Electronics',
            'price': '99.99'
        },

        # Invalid price format (letters)
        {
            'product_id': 'BAD_PROD_001',
            'product_name': 'Bad Price Product',
            'category': 'Electronics',
            'price': 'not-a-number'
        },

        # Negative price
        {
            'product_id': 'BAD_PROD_002',
            'product_name': 'Negative Price Product',
            'category': 'Electronics',
            'price': '-50.00'
        },

        # NULL product_name
        {
            'product_id': 'BAD_PROD_003',
            'product_name': None,
            'category': 'Electronics',
            'price': '25.99'
        },

        # Extremely high price (potential outlier)
        {
            'product_id': 'BAD_PROD_004',
            'product_name': 'Expensive Product',
            'category': 'Luxury',
            'price': '999999.99'
        },

        # Empty category
        {
            'product_id': 'BAD_PROD_005',
            'product_name': 'No Category Product',
            'category': '',
            'price': '15.99'
        }
    ]

    return pd.DataFrame(bad_products)


def create_bad_stores_data():
    """Generate bad store data with various validation issues"""
    logger.info("Generating bad store data...")

    bad_stores = [
        # Missing required store_id
        {
            'store_id': '',
            'store_name': 'Test Store',
            'location': 'Test City',
            'manager': 'Test Manager'
        },

        # NULL store_name
        {
            'store_id': 'BAD_STORE_001',
            'store_name': None,
            'location': 'Unknown City',
            'manager': 'John Manager'
        },

        # Empty location
        {
            'store_id': 'BAD_STORE_002',
            'store_name': 'No Location Store',
            'location': '',
            'manager': 'Jane Manager'
        }
    ]

    return pd.DataFrame(bad_stores)


def create_bad_suppliers_data():
    """Generate bad supplier data with various validation issues"""
    logger.info("Generating bad supplier data...")

    bad_suppliers = [
        # Missing required supplier_id
        {
            'supplier_id': '',
            'supplier_name': 'Test Supplier',
            'contact_name': 'Test Contact',
            'contact_email': 'test@supplier.com'
        },

        # Invalid email format
        {
            'supplier_id': 'BAD_SUP_001',
            'supplier_name': 'Bad Email Supplier',
            'contact_name': 'Bad Contact',
            'contact_email': 'invalid-email'
        },

        # NULL supplier_name
        {
            'supplier_id': 'BAD_SUP_002',
            'supplier_name': None,
            'contact_name': 'Valid Contact',
            'contact_email': 'valid@supplier.com'
        }
    ]

    return pd.DataFrame(bad_suppliers)


def create_bad_sales_data():
    """Generate bad sales data with various validation issues"""
    logger.info("Generating bad sales data...")

    bad_sales = [
        # Missing required sale_id
        {
            'sale_id': '',
            'customer_id': 'CUST1000',
            'product_id': 'PROD1000',
            'store_id': 'STORE100',
            'sale_date': '2024-01-01',
            'quantity': '1',
            'total_amount': '100.00'
        },

        # Non-existent customer_id
        {
            'sale_id': 'BAD_SALE_001',
            'customer_id': 'NONEXISTENT_CUSTOMER',
            'product_id': 'PROD1000',
            'store_id': 'STORE100',
            'sale_date': '2024-01-01',
            'quantity': '1',
            'total_amount': '100.00'
        },

        # Non-existent product_id
        {
            'sale_id': 'BAD_SALE_002',
            'customer_id': 'CUST1000',
            'product_id': 'NONEXISTENT_PRODUCT',
            'store_id': 'STORE100',
            'sale_date': '2024-01-01',
            'quantity': '1',
            'total_amount': '100.00'
        },

        # Non-existent store_id
        {
            'sale_id': 'BAD_SALE_003',
            'customer_id': 'CUST1000',
            'product_id': 'PROD1000',
            'store_id': 'NONEXISTENT_STORE',
            'sale_date': '2024-01-01',
            'quantity': '1',
            'total_amount': '100.00'
        },

        # Invalid date format
        {
            'sale_id': 'BAD_SALE_004',
            'customer_id': 'CUST1000',
            'product_id': 'PROD1000',
            'store_id': 'STORE100',
            'sale_date': 'invalid-date',
            'quantity': '1',
            'total_amount': '100.00'
        },

        # Negative quantity
        {
            'sale_id': 'BAD_SALE_005',
            'customer_id': 'CUST1000',
            'product_id': 'PROD1000',
            'store_id': 'STORE100',
            'sale_date': '2024-01-01',
            'quantity': '-5',
            'total_amount': '100.00'
        },

        # Invalid quantity format (letters)
        {
            'sale_id': 'BAD_SALE_006',
            'customer_id': 'CUST1000',
            'product_id': 'PROD1000',
            'store_id': 'STORE100',
            'sale_date': '2024-01-01',
            'quantity': 'not-a-number',
            'total_amount': '100.00'
        },

        # Negative total_amount
        {
            'sale_id': 'BAD_SALE_007',
            'customer_id': 'CUST1000',
            'product_id': 'PROD1000',
            'store_id': 'STORE100',
            'sale_date': '2024-01-01',
            'quantity': '1',
            'total_amount': '-100.00'
        },

        # Invalid total_amount format
        {
            'sale_id': 'BAD_SALE_008',
            'customer_id': 'CUST1000',
            'product_id': 'PROD1000',
            'store_id': 'STORE100',
            'sale_date': '2024-01-01',
            'quantity': '1',
            'total_amount': 'invalid-amount'
        },

        # Future date (might be invalid business rule)
        {
            'sale_id': 'BAD_SALE_009',
            'customer_id': 'CUST1000',
            'product_id': 'PROD1000',
            'store_id': 'STORE100',
            'sale_date': '2030-12-31',
            'quantity': '1',
            'total_amount': '100.00'
        },

        # Multiple foreign key violations
        {
            'sale_id': 'BAD_SALE_010',
            'customer_id': 'NONEXISTENT_CUSTOMER',
            'product_id': 'NONEXISTENT_PRODUCT',
            'store_id': 'NONEXISTENT_STORE',
            'sale_date': '2024-01-01',
            'quantity': '1',
            'total_amount': '100.00'
        },

        # NULL values in required fields
        {
            'sale_id': 'BAD_SALE_011',
            'customer_id': None,
            'product_id': None,
            'store_id': None,
            'sale_date': '2024-01-01',
            'quantity': '1',
            'total_amount': '100.00'
        }
    ]

    return pd.DataFrame(bad_sales)


def create_bad_inventory_data():
    """Generate bad inventory data with various validation issues"""
    logger.info("Generating bad inventory data...")

    bad_inventory = [
        # Non-existent product_id
        {
            'product_id': 'NONEXISTENT_PRODUCT',
            'store_id': 'STORE100',
            'stock_level': '50',
            'last_updated': '2024-01-01 10:00:00',
            'supplier_id': 'SUP001'
        },

        # Non-existent store_id
        {
            'product_id': 'PROD1000',
            'store_id': 'NONEXISTENT_STORE',
            'stock_level': '50',
            'last_updated': '2024-01-01 10:00:00',
            'supplier_id': 'SUP001'
        },

        # Non-existent supplier_id
        {
            'product_id': 'PROD1000',
            'store_id': 'STORE100',
            'stock_level': '50',
            'last_updated': '2024-01-01 10:00:00',
            'supplier_id': 'NONEXISTENT_SUPPLIER'
        },

        # Negative stock_level
        {
            'product_id': 'PROD1000',
            'store_id': 'STORE100',
            'stock_level': '-10',
            'last_updated': '2024-01-01 10:00:00',
            'supplier_id': 'SUP001'
        },

        # Invalid stock_level format
        {
            'product_id': 'PROD1000',
            'store_id': 'STORE100',
            'stock_level': 'not-a-number',
            'last_updated': '2024-01-01 10:00:00',
            'supplier_id': 'SUP001'
        },

        # Invalid date format
        {
            'product_id': 'PROD1000',
            'store_id': 'STORE100',
            'stock_level': '50',
            'last_updated': 'invalid-date',
            'supplier_id': 'SUP001'
        },

        # NULL values
        {
            'product_id': None,
            'store_id': None,
            'stock_level': '50',
            'last_updated': '2024-01-01 10:00:00',
            'supplier_id': None
        }
    ]

    return pd.DataFrame(bad_inventory)


def save_bad_data_to_csv():
    """Save all bad data to CSV files in the data directory"""
    logger.info("Saving bad data to CSV files...")

    # Create backup of original data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"data_backup_{timestamp}"

    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        logger.info(f"Created backup directory: {backup_dir}")

    # Backup original files
    original_files = [
        'data/customers.csv',
        'data/products.csv',
        'data/stores.csv',
        'data/suppliers.csv',
        'data/sales.csv',
        'data/inventory.csv'
    ]

    for file in original_files:
        if os.path.exists(file):
            backup_file = file.replace('data/', f'{backup_dir}/')
            os.rename(file, backup_file)
            logger.info(f"Backed up {file} to {backup_file}")

    # Generate and save bad data
    bad_data_sets = [
        (create_bad_customers_data(), 'data/customers.csv'),
        (create_bad_products_data(), 'data/products.csv'),
        (create_bad_stores_data(), 'data/stores.csv'),
        (create_bad_suppliers_data(), 'data/suppliers.csv'),
        (create_bad_sales_data(), 'data/sales.csv'),
        (create_bad_inventory_data(), 'data/inventory.csv')
    ]

    for df, filename in bad_data_sets:
        df.to_csv(filename, index=False, na_rep='')
        logger.info(f"Saved bad data to {filename} ({len(df)} records)")

    return backup_dir


def restore_original_data(backup_dir):
    """Restore original data from backup"""
    logger.info(f"Restoring original data from {backup_dir}...")

    backup_files = [
        f'{backup_dir}/customers.csv',
        f'{backup_dir}/products.csv',
        f'{backup_dir}/stores.csv',
        f'{backup_dir}/suppliers.csv',
        f'{backup_dir}/sales.csv',
        f'{backup_dir}/inventory.csv'
    ]

    for backup_file in backup_files:
        if os.path.exists(backup_file):
            original_file = backup_file.replace(f'{backup_dir}/', 'data/')
            os.rename(backup_file, original_file)
            logger.info(f"Restored {original_file}")

    # Remove backup directory
    try:
        os.rmdir(backup_dir)
        logger.info(f"Removed backup directory: {backup_dir}")
    except:
        logger.warning(f"Could not remove backup directory: {backup_dir}")


def count_rejected_files_before():
    """Count existing rejected files before test"""
    rejected_dir = "rejected_data"
    if not os.path.exists(rejected_dir):
        return 0

    return len([f for f in os.listdir(rejected_dir) if f.endswith('.csv')])


def count_rejected_files_after():
    """Count rejected files after test"""
    rejected_dir = "rejected_data"
    if not os.path.exists(rejected_dir):
        return 0

    files = [f for f in os.listdir(rejected_dir) if f.endswith('.csv')]
    logger.info(f"Rejected data files found: {files}")
    return len(files)


def analyze_rejected_data():
    """Analyze the rejected data files generated"""
    logger.info("Analyzing rejected data files...")

    rejected_dir = "rejected_data"
    if not os.path.exists(rejected_dir):
        logger.warning("No rejected_data directory found")
        return

    rejected_files = [f for f in os.listdir(
        rejected_dir) if f.endswith('.csv')]

    for file in rejected_files:
        file_path = os.path.join(rejected_dir, file)
        try:
            df = pd.read_csv(file_path)
            logger.info(f"\n--- Analysis of {file} ---")
            logger.info(f"Records rejected: {len(df)}")

            if 'rejection_reason' in df.columns:
                reason_counts = df['rejection_reason'].value_counts()
                logger.info("Rejection reasons:")
                for reason, count in reason_counts.items():
                    logger.info(f"  - {reason}: {count} records")

            if 'additional_info' in df.columns:
                logger.info(
                    f"Sample additional info: {df['additional_info'].iloc[0] if len(df) > 0 else 'N/A'}")

        except Exception as e:
            logger.error(f"Error analyzing {file}: {e}")


def run_bad_data_test():
    """Main function to run the bad data test"""
    logger.info("=" * 60)
    logger.info("STARTING BAD DATA GENERATION TEST")
    logger.info("=" * 60)

    try:
        # Count existing rejected files
        initial_rejected_count = count_rejected_files_before()
        logger.info(f"Initial rejected files count: {initial_rejected_count}")

        # Generate and save bad data
        backup_dir = save_bad_data_to_csv()

        # Import and run the ETL pipeline
        logger.info("Running ETL pipeline with bad data...")
        from main import main

        # Run the ETL process
        main()

        # Count new rejected files
        final_rejected_count = count_rejected_files_after()
        new_rejected_files = final_rejected_count - initial_rejected_count

        logger.info("=" * 60)
        logger.info("BAD DATA TEST RESULTS")
        logger.info("=" * 60)
        logger.info(f"New rejected files created: {new_rejected_files}")
        logger.info(f"Total rejected files: {final_rejected_count}")

        # Analyze rejected data
        analyze_rejected_data()

        # Restore original data
        restore_original_data(backup_dir)

        logger.info("=" * 60)
        logger.info("BAD DATA TEST COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"Bad data test failed: {str(e)}")
        logger.error("Attempting to restore original data...")

        try:
            restore_original_data(backup_dir)
            logger.info("Original data restored successfully")
        except:
            logger.error("Failed to restore original data")

        return False


if __name__ == "__main__":
    success = run_bad_data_test()
    if success:
        print("\n✅ Bad data test completed successfully!")
        print("Check the logs and rejected_data folder for detailed results.")
    else:
        print("\n❌ Bad data test failed!")
        print("Check the logs for error details.")
