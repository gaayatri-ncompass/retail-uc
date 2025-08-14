import logging
from datetime import datetime
import os


class SimpleLogger:
    def __init__(self, name="ETL"):
        self.name = name

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = f"logs/etl_app_{timestamp}.log"

    def _log(self, level, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{self.name}] [{level}] {message}"

        print(log_message)

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_message + "\n")
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")

    def info(self, message):
        self._log("INFO", message)

    def error(self, message):
        self._log("ERROR", message)

    def warning(self, message):
        self._log("WARNING", message)

    def debug(self, message):
        self._log("DEBUG", message)

    def critical(self, message):
        self._log("CRITICAL", message)


def get_logger(name="ETL"):
    return SimpleLogger(name)
