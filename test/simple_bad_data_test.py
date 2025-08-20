"""
Simple Bad Data Test

Run this script to test if your ETL pipeline properly rejects bad data.
"""

import pandas as pd
import os
import shutil
from datetime import datetime

# Setup basic logging


def log(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")


def create_bad_test_data():
    """Create test data with known bad records"""
    log("Creating test data with intentional data quality issues...")

    # Bad customers data
    customers_data = [
        # Valid customer
        {'customer_id': 'TEST_CUST_001', 'customer_name': 'Valid Customer', 'email': 'valid@test.com',
            'phone': '1234567890', 'address': '123 Test St', 'signup_date': '2024-01-01'},
        # Bad customers
        {'customer_id': '', 'customer_name': 'Missing ID', 'email': 'missing@test.com',
            'phone': '1234567890', 'address': '123 Test St', 'signup_date': '2024-01-01'},
        {'customer_id': 'TEST_CUST_002', 'customer_name': 'Bad Email', 'email': 'invalid-email',
            'phone': '1234567890', 'address': '123 Test St', 'signup_date': '2024-01-01'},
    ]

    # Bad products data
    products_data = [
        # Valid product
        {'product_id': 'TEST_PROD_001', 'product_name': 'Valid Product',
            'category': 'Test', 'price': '10.99'},
        # Bad products
        {'product_id': '', 'product_name': 'Missing ID Product',
            'category': 'Test', 'price': '10.99'},
        {'product_id': 'TEST_PROD_002', 'product_name': 'Bad Price Product',
            'category': 'Test', 'price': 'not-a-number'},
    ]

    # Bad stores data
    stores_data = [
        # Valid store
        {'store_id': 'TEST_STORE_001', 'store_name': 'Valid Store',
            'location': 'Test City', 'manager': 'Test Manager'},
        # Bad store
        {'store_id': '', 'store_name': 'Missing ID Store',
            'location': 'Test City', 'manager': 'Test Manager'},
    ]

    # Bad suppliers data
    suppliers_data = [
        # Valid supplier
        {'supplier_id': 'TEST_SUP_001', 'supplier_name': 'Valid Supplier',
            'contact_name': 'Test Contact', 'contact_email': 'contact@supplier.com'},
        # Bad supplier
        {'supplier_id': 'TEST_SUP_002', 'supplier_name': 'Bad Email Supplier',
            'contact_name': 'Bad Contact', 'contact_email': 'invalid-email'},
    ]

    # Bad sales data
    sales_data = [
        # Valid sale
        {'sale_id': 'TEST_SALE_001', 'customer_id': 'TEST_CUST_001', 'product_id': 'TEST_PROD_001',
            'store_id': 'TEST_STORE_001', 'sale_date': '2024-01-01', 'quantity': '1', 'total_amount': '10.99'},
        # Bad sales with foreign key violations
        {'sale_id': 'TEST_SALE_002', 'customer_id': 'NONEXISTENT_CUSTOMER', 'product_id': 'TEST_PROD_001',
            'store_id': 'TEST_STORE_001', 'sale_date': '2024-01-01', 'quantity': '1', 'total_amount': '10.99'},
        {'sale_id': 'TEST_SALE_003', 'customer_id': 'TEST_CUST_001', 'product_id': 'NONEXISTENT_PRODUCT',
            'store_id': 'TEST_STORE_001', 'sale_date': '2024-01-01', 'quantity': '1', 'total_amount': '10.99'},
        {'sale_id': 'TEST_SALE_004', 'customer_id': 'TEST_CUST_001', 'product_id': 'TEST_PROD_001',
            'store_id': 'NONEXISTENT_STORE', 'sale_date': '2024-01-01', 'quantity': '1', 'total_amount': '10.99'},
        # Bad data types
        {'sale_id': 'TEST_SALE_005', 'customer_id': 'TEST_CUST_001', 'product_id': 'TEST_PROD_001',
            'store_id': 'TEST_STORE_001', 'sale_date': 'invalid-date', 'quantity': '1', 'total_amount': '10.99'},
        {'sale_id': 'TEST_SALE_006', 'customer_id': 'TEST_CUST_001', 'product_id': 'TEST_PROD_001',
            'store_id': 'TEST_STORE_001', 'sale_date': '2024-01-01', 'quantity': 'abc', 'total_amount': '10.99'},
    ]

    # Bad inventory data
    inventory_data = [
        # Valid inventory
        {'product_id': 'TEST_PROD_001', 'store_id': 'TEST_STORE_001', 'stock_level': '100',
            'last_updated': '2024-01-01 10:00:00', 'supplier_id': 'TEST_SUP_001'},
        # Bad inventory
        {'product_id': 'NONEXISTENT_PRODUCT', 'store_id': 'TEST_STORE_001', 'stock_level': '50',
            'last_updated': '2024-01-01 10:00:00', 'supplier_id': 'TEST_SUP_001'},
        {'product_id': 'TEST_PROD_001', 'store_id': 'NONEXISTENT_STORE', 'stock_level': '50',
            'last_updated': '2024-01-01 10:00:00', 'supplier_id': 'TEST_SUP_001'},
        {'product_id': 'TEST_PROD_001', 'store_id': 'TEST_STORE_001', 'stock_level': 'abc',
            'last_updated': '2024-01-01 10:00:00', 'supplier_id': 'TEST_SUP_001'},
    ]

    return {
        'customers': pd.DataFrame(customers_data),
        'products': pd.DataFrame(products_data),
        'stores': pd.DataFrame(stores_data),
        'suppliers': pd.DataFrame(suppliers_data),
        'sales': pd.DataFrame(sales_data),
        'inventory': pd.DataFrame(inventory_data)
    }


def backup_data():
    """Backup current data files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"test_backup_{timestamp}"

    os.makedirs(backup_dir, exist_ok=True)

    files = ['customers.csv', 'products.csv', 'stores.csv',
             'suppliers.csv', 'sales.csv', 'inventory.csv']

    for file in files:
        src = f"data/{file}"
        dst = f"{backup_dir}/{file}"
        if os.path.exists(src):
            shutil.copy2(src, dst)

    log(f"Data backed up to {backup_dir}")
    return backup_dir


def save_test_data(test_data):
    """Save test data to CSV files"""
    for table, df in test_data.items():
        filename = f"data/{table}.csv"
        df.to_csv(filename, index=False)
        log(f"Saved {len(df)} test records to {filename}")


def restore_data(backup_dir):
    """Restore original data"""
    files = ['customers.csv', 'products.csv', 'stores.csv',
             'suppliers.csv', 'sales.csv', 'inventory.csv']

    for file in files:
        src = f"{backup_dir}/{file}"
        dst = f"data/{file}"
        if os.path.exists(src):
            shutil.copy2(src, dst)

    shutil.rmtree(backup_dir)
    log("Original data restored")


def count_rejected_files():
    """Count files in rejected_data directory"""
    rejected_dir = "rejected_data"
    if not os.path.exists(rejected_dir):
        return 0
    return len([f for f in os.listdir(rejected_dir) if f.endswith('.csv')])


def analyze_results():
    """Analyze rejected data files"""
    rejected_dir = "rejected_data"
    if not os.path.exists(rejected_dir):
        log("No rejected_data directory found")
        return

    files = [f for f in os.listdir(rejected_dir) if f.endswith('.csv')]
    log(f"Found {len(files)} rejected data files")

    for file in files[-3:]:  # Show last 3 files
        file_path = os.path.join(rejected_dir, file)
        try:
            df = pd.read_csv(file_path)
            log(f"  {file}: {len(df)} rejected records")

            if 'rejection_reason' in df.columns:
                reasons = df['rejection_reason'].value_counts().head(2)
                for reason, count in reasons.items():
                    log(f"    - {reason}: {count}")
        except Exception as e:
            log(f"  Error reading {file}: {e}")


def main():
    """Run the bad data test"""
    print("="*60)
    print("BAD DATA VALIDATION TEST")
    print("="*60)
    print("This test will:")
    print("1. Backup your current data")
    print("2. Replace it with test data containing known bad records")
    print("3. Run your ETL pipeline")
    print("4. Check if bad data was properly rejected")
    print("5. Restore your original data")
    print("="*60)

    confirm = input("Continue with the test? (y/N): ")
    if confirm.lower() != 'y':
        print("Test cancelled.")
        return

    try:
        # Count initial rejected files
        initial_rejected = count_rejected_files()
        log(f"Initial rejected files: {initial_rejected}")

        # Backup data
        backup_dir = backup_data()

        # Create and save test data
        test_data = create_bad_test_data()
        save_test_data(test_data)

        # Run ETL
        log("Running ETL pipeline...")
        os.system("python main.py")

        # Check results
        final_rejected = count_rejected_files()
        new_rejected = final_rejected - initial_rejected

        print("\n" + "="*60)
        print("TEST RESULTS")
        print("="*60)
        log(f"New rejected files created: {new_rejected}")

        if new_rejected > 0:
            print("✅ SUCCESS: Bad data was properly rejected!")
            analyze_results()
        else:
            print("⚠️  WARNING: No rejected files created. Check validation logic.")

    except Exception as e:
        log(f"Test failed: {e}")

    finally:
        # Always restore data
        restore_data(backup_dir)
        log("Test completed")


if __name__ == "__main__":
    main()
