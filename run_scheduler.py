import subprocess
import sys
import time
from datetime import datetime


def main():

    print("Starting  ETL scheduler")
    print("Interval: 10 seconds")

    try:
        while True:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{ts}] Triggering run...")

            try:

                subprocess.run([sys.executable, "main.py"], check=True)
                print(f"[{ts}] Run completed successfully.")
            except FileNotFoundError:
                print(f"[{ts}] ERROR: 'main.py' not found")
                break
            except subprocess.CalledProcessError as e:
                print(f"[{ts}] Run failed with exit code {e.returncode}.")

            # Delay
            time.sleep(10)

    except KeyboardInterrupt:
        print("\nScheduler stopped by user.")


if __name__ == "__main__":
    main()
