"""
Test Runner for Bad Data Validation

This script provides a simple interface to run different bad data tests.
"""

import sys
import os
from logger import get_logger

logger = get_logger("TEST_RUNNER")


def print_menu():
    """Print the test menu"""
    print("\n" + "="*60)
    print("BAD DATA VALIDATION TEST SUITE")
    print("="*60)
    print("1. Quick Bad Data Test (recommended)")
    print("2. Comprehensive Bad Data Test")
    print("3. Data Quality Scenarios Test")
    print("4. View Recent Rejected Data")
    print("5. Clean Rejected Data Folder")
    print("0. Exit")
    print("="*60)


def view_rejected_data():
    """View information about rejected data files"""
    rejected_dir = "rejected_data"

    if not os.path.exists(rejected_dir):
        print("No rejected_data directory found.")
        return

    files = [f for f in os.listdir(rejected_dir) if f.endswith('.csv')]

    if not files:
        print("No rejected data files found.")
        return

    print(f"\nFound {len(files)} rejected data files:")

    for file in files:
        file_path = os.path.join(rejected_dir, file)
        file_size = os.path.getsize(file_path)

        # Get file creation time
        import time
        creation_time = time.ctime(os.path.getctime(file_path))

        print(f"  - {file}")
        print(f"    Size: {file_size} bytes")
        print(f"    Created: {creation_time}")

        # Try to read and show summary
        try:
            import pandas as pd
            df = pd.read_csv(file_path)
            print(f"    Records: {len(df)}")

            if 'rejection_reason' in df.columns:
                reasons = df['rejection_reason'].value_counts()
                print(
                    f"    Top rejection reason: {reasons.index[0]} ({reasons.iloc[0]} records)")
        except Exception as e:
            print(f"    Error reading file: {e}")

        print()


def clean_rejected_data():
    """Clean the rejected data folder"""
    rejected_dir = "rejected_data"

    if not os.path.exists(rejected_dir):
        print("No rejected_data directory found.")
        return

    files = [f for f in os.listdir(rejected_dir) if f.endswith('.csv')]

    if not files:
        print("No rejected data files to clean.")
        return

    print(f"Found {len(files)} rejected data files.")
    confirm = input(
        "Are you sure you want to delete all rejected data files? (y/N): ")

    if confirm.lower() == 'y':
        for file in files:
            file_path = os.path.join(rejected_dir, file)
            os.remove(file_path)
            print(f"Deleted {file}")
        print("All rejected data files have been cleaned.")
    else:
        print("Cleanup cancelled.")


def run_quick_test():
    """Run the quick bad data test"""
    print("\nRunning Quick Bad Data Test...")
    print("This will temporarily replace your data files with test data.")

    confirm = input("Continue? (y/N): ")
    if confirm.lower() != 'y':
        print("Test cancelled.")
        return

    try:
        import sys
        import os
        sys.path.append(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))

        from test.quick_bad_data_test import main as quick_test_main
        quick_test_main()
    except Exception as e:
        logger.error(f"Quick test failed: {e}")
        print(f"Test failed: {e}")


def run_comprehensive_test():
    """Run the comprehensive bad data test"""
    print("\nRunning Comprehensive Bad Data Test...")
    print("This will temporarily replace your data files with test data.")
    print("This test is more thorough but takes longer to run.")

    confirm = input("Continue? (y/N): ")
    if confirm.lower() != 'y':
        print("Test cancelled.")
        return

    try:
        from test.test_bad_data_generator import run_bad_data_test
        success = run_bad_data_test()
        if success:
            print("✅ Comprehensive test completed successfully!")
        else:
            print("❌ Comprehensive test failed!")
    except Exception as e:
        logger.error(f"Comprehensive test failed: {e}")
        print(f"Test failed: {e}")


def run_data_quality_test():
    """Run the data quality scenarios test"""
    print("\nRunning Data Quality Scenarios Test...")
    print("This will test specific data quality validation scenarios.")

    confirm = input("Continue? (y/N): ")
    if confirm.lower() != 'y':
        print("Test cancelled.")
        return

    try:
        from test.test_data_quality import main
        main()
    except Exception as e:
        logger.error(f"Data quality test failed: {e}")
        print(f"Test failed: {e}")


def main():
    """Main menu loop"""
    while True:
        print_menu()

        try:
            choice = input("Enter your choice (0-5): ").strip()

            if choice == '0':
                print("Goodbye!")
                break
            elif choice == '1':
                run_quick_test()
            elif choice == '2':
                run_comprehensive_test()
            elif choice == '3':
                run_data_quality_test()
            elif choice == '4':
                view_rejected_data()
            elif choice == '5':
                clean_rejected_data()
            else:
                print("Invalid choice. Please enter a number between 0-5.")

        except KeyboardInterrupt:
            print("\n\nTest runner interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

        input("\nPress Enter to continue...")


if __name__ == "__main__":
    print("Bad Data Validation Test Suite")
    print("This tool helps you test how your ETL pipeline handles bad data.")
    main()
