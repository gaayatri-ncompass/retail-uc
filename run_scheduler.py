import subprocess
import sys
import time
from datetime import datetime
from logger import get_logger


logger = get_logger("SCHEDULER")


def main():

    logger.info("Starting ETL Scheduler")
    logger.info("Interval: 10 seconds")
    logger.info("=" * 40)

    try:
        while True:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"[{ts}] Triggering ETL run...")

            try:

                result = subprocess.run([sys.executable, "main.py"],
                                        capture_output=True, text=True, check=True)

                output_lines = result.stdout.strip().split('\n')
                if output_lines:
                    last_line = output_lines[-1]
                    logger.info(f"[{ts}] {last_line}")
                else:
                    logger.info(f"[{ts}] ETL Completed")

            except FileNotFoundError:
                logger.error(f"[{ts}] ERROR: 'main.py' not found")
                break
            except subprocess.CalledProcessError as e:
                logger.error(
                    f"[{ts}] ETL failed with exit code {e.returncode}")

            time.sleep(10)

    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user.")


if __name__ == "__main__":
    main()
