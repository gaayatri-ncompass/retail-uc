"""
Simple Bad Data Quality Tester

This script creates specific data quality issues to test validation rules.
Run this to verify that your ETL pipeline properly handles and rejects bad data.
"""

import pandas as pd
import os
from datetime import datetime
from logger import get_logger

logger = get_logger("DATA_QUALITY_TEST")


def create_test_scenarios():
    """Create specific test scenarios for data quality validation"""

    test_scenarios = {
        'missing_required_fields': {
            'description': 'Records with missing required fields',
            'data': {
                'customers': [
                    {'customer_id': '', 'customer_name': 'Test',
                        'email': 'test@test.com'},
                    {'customer_id': 'CUST_TEST', 'customer_name': '',
                        'email': 'test2@test.com'}
                ],
                'sales': [
                    {'sale_id': '', 'customer_id': 'CUST1000',
                        'product_id': 'PROD1000'},
                    {'sale_id': 'SALE_TEST', 'customer_id': '',
                        'product_id': 'PROD1000'}
                ]
            }
        },

        'invalid_data_types': {
            'description': 'Invalid data types and formats',
            'data': {
                'products': [
                    {'product_id': 'PROD_TEST',
                        'price': 'not_a_number', 'category': 'Test'},
                    {'product_id': 'PROD_TEST2', 'price': '-100', 'category': 'Test'}
                ],
                'sales': [
                    {'sale_id': 'SALE_TEST', 'quantity': 'abc', 'total_amount': 'xyz'},
                    {'sale_id': 'SALE_TEST2', 'quantity': '-5', 'total_amount': '-100'}
                ]
            }
        },

        'foreign_key_violations': {
            'description': 'References to non-existent records',
            'data': {
                'sales': [
                    {
                        'sale_id': 'FK_TEST_001',
                        'customer_id': 'NONEXISTENT_CUSTOMER',
                        'product_id': 'PROD1000',
                        'store_id': 'STORE100',
                        'sale_date': '2024-01-01',
                        'quantity': '1',
                        'total_amount': '100.00'
                    },
                    {
                        'sale_id': 'FK_TEST_002',
                        'customer_id': 'CUST1000',
                        'product_id': 'NONEXISTENT_PRODUCT',
                        'store_id': 'STORE100',
                        'sale_date': '2024-01-01',
                        'quantity': '1',
                        'total_amount': '100.00'
                    }
                ]
            }
        },

        'format_violations': {
            'description': 'Format validation failures',
            'data': {
                'customers': [
                    {
                        'customer_id': 'EMAIL_TEST',
                        'customer_name': 'Email Test',
                        'email': 'invalid-email-format',
                        'phone': '1234567890'
                    },
                    {
                        'customer_id': 'PHONE_TEST',
                        'customer_name': 'Phone Test',
                        'email': 'phone@test.com',
                        'phone': 'ABC-DEF-GHIJ'
                    }
                ]
            }
        },

        'date_violations': {
            'description': 'Invalid date formats and values',
            'data': {
                'customers': [
                    {
                        'customer_id': 'DATE_TEST',
                        'customer_name': 'Date Test',
                        'email': 'date@test.com',
                        'signup_date': 'invalid-date'
                    }
                ],
                'sales': [
                    {
                        'sale_id': 'DATE_SALE_TEST',
                        'customer_id': 'CUST1000',
                        'product_id': 'PROD1000',
                        'store_id': 'STORE100',
                        'sale_date': 'not-a-date',
                        'quantity': '1',
                        'total_amount': '100.00'
                    }
                ]
            }
        }
    }

    return test_scenarios


def backup_current_data():
    """Backup current data files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"test_backup_{timestamp}"

    os.makedirs(backup_dir, exist_ok=True)

    data_files = ['customers.csv', 'products.csv', 'stores.csv',
                  'suppliers.csv', 'sales.csv', 'inventory.csv']

    for file in data_files:
        src = f"data/{file}"
        dst = f"{backup_dir}/{file}"
        if os.path.exists(src):
            import shutil
            shutil.copy2(src, dst)
            logger.info(f"Backed up {src} to {dst}")

    return backup_dir


def create_minimal_valid_data():
    """Create minimal valid data for tables that need references"""

    # Create minimal valid customers
    customers = pd.DataFrame([
        {
            'customer_id': 'CUST1000',
            'customer_name': 'Valid Customer',
            'email': 'valid@customer.com',
            'phone': '1234567890',
            'address': '123 Valid St',
            'signup_date': '2024-01-01'
        }
    ])

    # Create minimal valid products
    products = pd.DataFrame([
        {
            'product_id': 'PROD1000',
            'product_name': 'Valid Product',
            'category': 'Test',
            'price': '10.00'
        }
    ])

    # Create minimal valid stores
    stores = pd.DataFrame([
        {
            'store_id': 'STORE100',
            'store_name': 'Valid Store',
            'location': 'Test City',
            'manager': 'Test Manager'
        }
    ])

    # Create minimal valid suppliers
    suppliers = pd.DataFrame([
        {
            'supplier_id': 'SUP001',
            'supplier_name': 'Valid Supplier',
            'contact_name': 'Test Contact',
            'contact_email': 'contact@supplier.com'
        }
    ])

    return {
        'customers': customers,
        'products': products,
        'stores': stores,
        'suppliers': suppliers
    }


def run_test_scenario(scenario_name, scenario_data):
    """Run a specific test scenario"""
    logger.info(f"\n{'='*50}")
    logger.info(f"TESTING: {scenario_name}")
    logger.info(f"Description: {scenario_data['description']}")
    logger.info(f"{'='*50}")

    # Get valid base data
    base_data = create_minimal_valid_data()

    # Add bad data to the mix
    for table_name, bad_records in scenario_data['data'].items():
        if table_name in base_data:
            # Convert bad records to DataFrame
            bad_df = pd.DataFrame(bad_records)
            # Append to base data
            base_data[table_name] = pd.concat(
                [base_data[table_name], bad_df], ignore_index=True)
        else:
            # Create new table with just bad data
            base_data[table_name] = pd.DataFrame(bad_records)

    # Save test data to CSV files
    for table_name, df in base_data.items():
        df.to_csv(f"data/{table_name}.csv", index=False)
        logger.info(f"Created test data for {table_name}: {len(df)} records")

    # Count rejected files before
    rejected_before = count_rejected_files()

    # Run ETL
    try:
        from main import main
        logger.info("Running ETL with test data...")
        main()

        # Count rejected files after
        rejected_after = count_rejected_files()
        new_rejections = rejected_after - rejected_before

        logger.info(f"New rejected files created: {new_rejections}")
        return new_rejections > 0

    except Exception as e:
        logger.error(f"ETL failed during {scenario_name}: {str(e)}")
        return False


def count_rejected_files():
    """Count files in rejected_data directory"""
    rejected_dir = "rejected_data"
    if not os.path.exists(rejected_dir):
        return 0
    return len([f for f in os.listdir(rejected_dir) if f.endswith('.csv')])


def restore_data(backup_dir):
    """Restore original data"""
    data_files = ['customers.csv', 'products.csv', 'stores.csv',
                  'suppliers.csv', 'sales.csv', 'inventory.csv']

    for file in data_files:
        src = f"{backup_dir}/{file}"
        dst = f"data/{file}"
        if os.path.exists(src):
            import shutil
            shutil.copy2(src, dst)

    logger.info("Original data restored")


def main():
    """Run all data quality tests"""
    logger.info("Starting Data Quality Tests...")

    # Backup original data
    backup_dir = backup_current_data()

    test_scenarios = create_test_scenarios()
    results = {}

    try:
        for scenario_name, scenario_data in test_scenarios.items():
            success = run_test_scenario(scenario_name, scenario_data)
            results[scenario_name] = success

            # Small delay between tests
            import time
            time.sleep(2)

        # Print summary
        logger.info("\n" + "="*60)
        logger.info("DATA QUALITY TEST SUMMARY")
        logger.info("="*60)

        for scenario, success in results.items():
            status = "✅ PASSED" if success else "❌ FAILED"
            logger.info(f"{scenario}: {status}")

        passed_tests = sum(results.values())
        total_tests = len(results)
        logger.info(f"\nOverall: {passed_tests}/{total_tests} tests passed")

    finally:
        # Always restore original data
        restore_data(backup_dir)

        # Clean up backup
        import shutil
        shutil.rmtree(backup_dir)
        logger.info("Cleanup completed")


if __name__ == "__main__":
    main()
