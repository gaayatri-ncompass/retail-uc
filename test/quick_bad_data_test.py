"""
Quick Bad Data Test

This script creates a small set of bad data and runs the ETL to verify rejection handling.
"""

import pandas as pd
import os
import shutil
from datetime import datetime
from logger import get_logger

logger = get_logger("QUICK_BAD_DATA_TEST")


def create_bad_test_data():
    """Create a small set of bad data for testing"""

    # Create bad customers data
    bad_customers = pd.DataFrame([
        # Valid customer for references
        {
            'customer_id': 'VALID_CUST_001',
            'customer_name': 'Valid Customer',
            'email': 'valid@test.com',
            'phone': '1234567890',
            'address': '123 Test St',
            'signup_date': '2024-01-01'
        },
        # Bad customers
        {
            'customer_id': 'BAD_CUST_001',
            'customer_name': 'Bad Email Customer',
            'email': 'invalid-email-format',  # Bad email
            'phone': '1234567890',
            'address': '456 Test Ave',
            'signup_date': '2024-01-01'
        },
        {
            'customer_id': '',  # Missing ID
            'customer_name': 'Missing ID Customer',
            'email': 'missing@test.com',
            'phone': '1234567890',
            'address': '789 Test Blvd',
            'signup_date': '2024-01-01'
        }
    ])

    # Create bad products data
    bad_products = pd.DataFrame([
        # Valid product for references
        {
            'product_id': 'VALID_PROD_001',
            'product_name': 'Valid Product',
            'category': 'Test',
            'price': '10.99'
        },
        # Bad products
        {
            'product_id': 'BAD_PROD_001',
            'product_name': 'Bad Price Product',
            'category': 'Test',
            'price': 'not-a-number'  # Invalid price
        },
        {
            'product_id': '',  # Missing ID
            'product_name': 'Missing ID Product',
            'category': 'Test',
            'price': '15.99'
        }
    ])

    # Create bad stores data
    bad_stores = pd.DataFrame([
        # Valid store for references
        {
            'store_id': 'VALID_STORE_001',
            'store_name': 'Valid Store',
            'location': 'Test City',
            'manager': 'Test Manager'
        },
        # Bad store
        {
            'store_id': '',  # Missing ID
            'store_name': 'Missing ID Store',
            'location': 'Test City',
            'manager': 'Test Manager'
        }
    ])

    # Create bad suppliers data
    bad_suppliers = pd.DataFrame([
        # Valid supplier for references
        {
            'supplier_id': 'VALID_SUP_001',
            'supplier_name': 'Valid Supplier',
            'contact_name': 'Test Contact',
            'contact_email': 'contact@supplier.com'
        },
        # Bad supplier
        {
            'supplier_id': 'BAD_SUP_001',
            'supplier_name': 'Bad Email Supplier',
            'contact_name': 'Bad Contact',
            'contact_email': 'invalid-email'  # Bad email
        }
    ])

    # Create bad sales data
    bad_sales = pd.DataFrame([
        # Valid sale
        {
            'sale_id': 'VALID_SALE_001',
            'customer_id': 'VALID_CUST_001',
            'product_id': 'VALID_PROD_001',
            'store_id': 'VALID_STORE_001',
            'sale_date': '2024-01-01',
            'quantity': '1',
            'total_amount': '10.99'
        },
        # Bad sales with foreign key violations
        {
            'sale_id': 'BAD_SALE_001',
            'customer_id': 'NONEXISTENT_CUSTOMER',  # FK violation
            'product_id': 'VALID_PROD_001',
            'store_id': 'VALID_STORE_001',
            'sale_date': '2024-01-01',
            'quantity': '1',
            'total_amount': '10.99'
        },
        {
            'sale_id': 'BAD_SALE_002',
            'customer_id': 'VALID_CUST_001',
            'product_id': 'NONEXISTENT_PRODUCT',  # FK violation
            'store_id': 'VALID_STORE_001',
            'sale_date': '2024-01-01',
            'quantity': '1',
            'total_amount': '10.99'
        },
        {
            'sale_id': 'BAD_SALE_003',
            'customer_id': 'VALID_CUST_001',
            'product_id': 'VALID_PROD_001',
            'store_id': 'NONEXISTENT_STORE',  # FK violation
            'sale_date': '2024-01-01',
            'quantity': '1',
            'total_amount': '10.99'
        },
        {
            'sale_id': 'BAD_SALE_004',
            'customer_id': 'VALID_CUST_001',
            'product_id': 'VALID_PROD_001',
            'store_id': 'VALID_STORE_001',
            'sale_date': 'invalid-date',  # Bad date
            'quantity': '1',
            'total_amount': '10.99'
        },
        {
            'sale_id': 'BAD_SALE_005',
            'customer_id': 'VALID_CUST_001',
            'product_id': 'VALID_PROD_001',
            'store_id': 'VALID_STORE_001',
            'sale_date': '2024-01-01',
            'quantity': 'abc',  # Bad quantity
            'total_amount': '10.99'
        }
    ])

    # Create bad inventory data
    bad_inventory = pd.DataFrame([
        # Valid inventory
        {
            'product_id': 'VALID_PROD_001',
            'store_id': 'VALID_STORE_001',
            'stock_level': '100',
            'last_updated': '2024-01-01 10:00:00',
            'supplier_id': 'VALID_SUP_001'
        },
        # Bad inventory with FK violations
        {
            'product_id': 'NONEXISTENT_PRODUCT',  # FK violation
            'store_id': 'VALID_STORE_001',
            'stock_level': '50',
            'last_updated': '2024-01-01 10:00:00',
            'supplier_id': 'VALID_SUP_001'
        },
        {
            'product_id': 'VALID_PROD_001',
            'store_id': 'NONEXISTENT_STORE',  # FK violation
            'stock_level': '50',
            'last_updated': '2024-01-01 10:00:00',
            'supplier_id': 'VALID_SUP_001'
        },
        {
            'product_id': 'VALID_PROD_001',
            'store_id': 'VALID_STORE_001',
            'stock_level': 'abc',  # Bad stock level
            'last_updated': '2024-01-01 10:00:00',
            'supplier_id': 'VALID_SUP_001'
        }
    ])

    return {
        'customers': bad_customers,
        'products': bad_products,
        'stores': bad_stores,
        'suppliers': bad_suppliers,
        'sales': bad_sales,
        'inventory': bad_inventory
    }


def backup_original_data():
    """Backup original data files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup_{timestamp}"

    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    data_files = ['customers.csv', 'products.csv', 'stores.csv',
                  'suppliers.csv', 'sales.csv', 'inventory.csv']

    for file in data_files:
        src = f"data/{file}"
        dst = f"{backup_dir}/{file}"
        if os.path.exists(src):
            shutil.copy2(src, dst)
            logger.info(f"Backed up {file}")

    return backup_dir


def save_test_data(test_data):
    """Save test data to CSV files"""
    for table_name, df in test_data.items():
        filename = f"data/{table_name}.csv"
        df.to_csv(filename, index=False)
        logger.info(f"Saved {len(df)} test records to {filename}")


def restore_original_data(backup_dir):
    """Restore original data from backup"""
    data_files = ['customers.csv', 'products.csv', 'stores.csv',
                  'suppliers.csv', 'sales.csv', 'inventory.csv']

    for file in data_files:
        src = f"{backup_dir}/{file}"
        dst = f"data/{file}"
        if os.path.exists(src):
            shutil.copy2(src, dst)

    # Remove backup directory
    shutil.rmtree(backup_dir)
    logger.info("Original data restored and backup cleaned up")


def count_rejected_files():
    """Count rejected data files"""
    rejected_dir = "rejected_data"
    if not os.path.exists(rejected_dir):
        return 0
    return len([f for f in os.listdir(rejected_dir) if f.endswith('.csv')])


def analyze_rejection_results():
    """Analyze the rejected data files"""
    rejected_dir = "rejected_data"
    if not os.path.exists(rejected_dir):
        logger.warning("No rejected_data directory found")
        return

    rejected_files = [f for f in os.listdir(
        rejected_dir) if f.endswith('.csv')]
    logger.info(f"\nFound {len(rejected_files)} rejected data files:")

    for file in rejected_files:
        file_path = os.path.join(rejected_dir, file)
        try:
            df = pd.read_csv(file_path)
            logger.info(f"\n--- {file} ---")
            logger.info(f"Rejected records: {len(df)}")

            if 'rejection_reason' in df.columns:
                reasons = df['rejection_reason'].value_counts()
                for reason, count in reasons.items():
                    logger.info(f"  - {reason}: {count} records")
        except Exception as e:
            logger.error(f"Error reading {file}: {e}")


def main():
    """Run the quick bad data test"""
    logger.info("="*60)
    logger.info("QUICK BAD DATA TEST")
    logger.info("="*60)

    # Count initial rejected files
    initial_rejected = count_rejected_files()
    logger.info(f"Initial rejected files: {initial_rejected}")

    # Backup original data
    backup_dir = backup_original_data()

    try:
        # Create and save test data
        test_data = create_bad_test_data()
        save_test_data(test_data)

        # Run ETL
        logger.info("\nRunning ETL with bad test data...")
        from main import main as run_etl
        run_etl()

        # Check results
        final_rejected = count_rejected_files()
        new_rejected = final_rejected - initial_rejected

        logger.info("\n" + "="*60)
        logger.info("TEST RESULTS")
        logger.info("="*60)
        logger.info(f"New rejected files created: {new_rejected}")

        if new_rejected > 0:
            logger.info("✅ SUCCESS: Bad data was properly rejected!")
            analyze_rejection_results()
        else:
            logger.warning(
                "⚠️  WARNING: No new rejected files created. Check if validation is working.")

    except Exception as e:
        logger.error(f"Test failed: {str(e)}")

    finally:
        # Always restore original data
        restore_original_data(backup_dir)
        logger.info("\nTest completed and original data restored.")


if __name__ == "__main__":
    main()
