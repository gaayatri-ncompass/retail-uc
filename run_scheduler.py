import subprocess
import sys
import time
from datetime import datetime


def main():

    print(" Starting ETL Scheduler")
    print("Interval: 10 seconds")
    print("=" * 40)

    try:
        while True:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{ts}]  Triggering ETL run...")

            try:

                result = subprocess.run([sys.executable, "simple_etl.py"],
                                        capture_output=True, text=True, check=True)

                output_lines = result.stdout.strip().split('\n')
                if output_lines:
                    last_line = output_lines[-1]
                    print(f"[{ts}] {last_line}")
                else:
                    print(f"[{ts}] ✅ ETL Completed")

            except FileNotFoundError:
                print(f"[{ts}] ❌ ERROR: 'simple_etl.py' not found")
                break
            except subprocess.CalledProcessError as e:
                print(f"[{ts}] ❌ ETL failed with exit code {e.returncode}")

            time.sleep(10)

    except KeyboardInterrupt:
        print("\nScheduler stopped by user.")


if __name__ == "__main__":
    main()
