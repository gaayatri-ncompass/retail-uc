import logging
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv(override=True)


def get_log_level():
    return os.getenv('ETL_LOG_LEVEL', 'INFO').upper()


class SimpleLogger:
    def __init__(self, name="ETL", log_level="INFO"):
        self.name = name
        self.log_level = log_level.upper()

        self.levels = {
            "DEBUG": 0,
            "INFO": 1,
            "WARNING": 2,
            "ERROR": 3,
            "CRITICAL": 4
        }

        self.current_level = self.levels.get(self.log_level, 1)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = f"logs/etl_app_{timestamp}.log"

    def _log(self, level, message):
        level_value = self.levels.get(level, 1)
        if level_value < self.current_level:
            return

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

    def success(self, message):
        """Log success messages with green checkmark"""
        self._log("INFO", f"✅ {message}")

    def process_start(self, process_name):
        """Log process start with formatted banner"""
        self._log("INFO", f"{'='*50}")
        self._log("INFO", f"STARTING: {process_name.upper()}")
        self._log("INFO", f"{'='*50}")

    def process_end(self, process_name):
        """Log process completion with formatted banner"""
        self._log("INFO", f"✅ COMPLETED: {process_name.upper()}")
        self._log("INFO", f"{'='*50}")

    def loading_progress(self, current, total, entity):
        """Log loading progress"""
        percentage = (current / total) * 100 if total > 0 else 0
        self._log(
            "INFO", f"Loading {entity}: {current}/{total} ({percentage:.1f}%)")

    def data_summary(self, entity, count, action="processed"):
        """Log data processing summary"""
        self._log("INFO", f"{entity.title()}: {count} records {action}")

    def set_level(self, level):
        self.log_level = level.upper()
        self.current_level = self.levels.get(self.log_level, 1)


def get_logger(name="ETL", log_level="INFO"):
    return SimpleLogger(name, log_level)
