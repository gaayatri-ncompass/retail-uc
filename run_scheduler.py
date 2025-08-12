import subprocess
import sys
import time
from datetime import datetime


def main():
    """Enhanced scheduler with clean output options"""

    print("🔄 Starting ETL Scheduler")
    print("📅 Interval: 10 seconds")
    print("💡 Use 'simple_etl.py' for cleaner output")
    print("=" * 40)

    try:
        while True:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{ts}] 🚀 Triggering ETL run...")

            try:
                # Use simple_etl.py for cleaner output
                result = subprocess.run([sys.executable, "simple_etl.py"],
                                        capture_output=True, text=True, check=True)

                # Only show the result line
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

            # Delay
            time.sleep(10)

    except KeyboardInterrupt:
        print("\n⏹️  Scheduler stopped by user.")


if __name__ == "__main__":
    main()
