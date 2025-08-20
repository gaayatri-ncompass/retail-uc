import subprocess
import sys
import time


def main():
    print("Starting ETL Scheduler (interval: 10s)")
    while True:
        print("Triggering ETL run...")
        subprocess.run([sys.executable, "main.py"])
        time.sleep(10)


if __name__ == "__main__":
    main()
