from __future__ import annotations

import json
import logging
import sys

from logging.handlers import RotatingFileHandler
from typing import ClassVar

from utility.error_handling import format_exception_with_variables


class ColoredConsoleHandler(logging.StreamHandler):
    try:
        import colorama  # type: ignore[import-untyped, reportMissingModuleSource]
        colorama.init()
        USING_COLORAMA = True
    except ImportError:
        USING_COLORAMA = False

    COLOR_CODES: ClassVar[dict[int, str]] = {
        logging.DEBUG: colorama.Fore.CYAN if USING_COLORAMA else "\033[0;36m",  # Cyan
        logging.INFO: colorama.Fore.WHITE if USING_COLORAMA else "\033[0;37m",  # White
        logging.WARNING: colorama.Fore.YELLOW if USING_COLORAMA else "\033[0;33m",  # Yellow
        logging.ERROR: colorama.Fore.RED if USING_COLORAMA else "\033[0;31m",  # Red
        logging.CRITICAL: colorama.Back.RED if USING_COLORAMA else "\033[1;41m",  # Red background
    }

    RESET_CODE = colorama.Style.RESET_ALL if USING_COLORAMA else "\033[0m"

    def format(self, record):
        msg = super().format(record)
        return f"{self.COLOR_CODES.get(record.levelno, '')}{msg}{self.RESET_CODE}"

class CustomExceptionFormatter(logging.Formatter):
    def formatException(self, ei):
        etype, value, tb = ei
        return format_exception_with_variables(value, etype=etype, tb=tb)

    def format(self, record):
        result = super().format(record)
        if record.exc_info:
            # Here we use our custom exception formatting
            result += "\n" + self.formatException(record.exc_info)
        return result

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            # Your custom exception formatting is called here
            formatted_exception = super().formatException(record.exc_info)  # Adjust this call as necessary
            log_record["exception"] = formatted_exception
        return json.dumps(log_record)

class LogLevelFilter(logging.Filter):
    """Filters (allows) all the log messages at or above a specific level."""
    def __init__(self, passlevel: int, reject: bool = False):  # noqa: FBT001, FBT002
        super().__init__()
        self.passlevel: int = passlevel
        self.reject: bool = reject

    def filter(self, record):
        if self.reject:
            return record.levelno < self.passlevel
        return record.levelno >= self.passlevel

def get_root_logger() -> logging.Logger:
    logger = logging.getLogger()
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        log_levels = {
            logging.DEBUG: "pykotor_debug.log",
            logging.INFO: "pykotor_info.log",
            logging.WARNING: "pykotor_warning.log",
            logging.ERROR: "pykotor_error.log",
            logging.CRITICAL: "pykotor_critical.log",
        }
        # Replacing StreamHandler with ColoredConsoleHandler
        console_handler = ColoredConsoleHandler()
        formatter = logging.Formatter("%(levelname)s(%(name)s): %(message)s")
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        for level, filename in log_levels.items():
            handler = RotatingFileHandler(filename, maxBytes=1048576, backupCount=5)
            handler.setLevel(level)

            # Apply JSON formatting for DEBUG, CustomExceptionFormatter for others
            if level == logging.DEBUG:
                handler.setFormatter(JSONFormatter())
            else:
                handler.setFormatter(CustomExceptionFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

            # Exclude lower level logs for handlers above DEBUG
            if level > logging.DEBUG:
                handler.addFilter(LogLevelFilter(level))

            logger.addHandler(handler)

    return logger

# Modify the handle_exception function if necessary
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger = get_root_logger()
    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

# Example usage
if __name__ == "__main__":
    logger = get_root_logger()
    logger.debug("This is a debug message.")
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical message.")

    # Uncomment to test uncaught exception logging
    # raise RuntimeError("Test uncaught exception")
