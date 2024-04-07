from __future__ import annotations

import json
import logging
import sys
import threading

from contextlib import contextmanager
from logging.handlers import RotatingFileHandler
from typing import TYPE_CHECKING, ClassVar

from utility.error_handling import format_exception_with_variables

if TYPE_CHECKING:
    from io import TextIOWrapper

    from typing_extensions import Literal

thread_local = threading.local()
thread_local.is_logging = False

@contextmanager
def logging_context():
    thread_local.is_logging = True
    try:
        yield
    finally:
        thread_local.is_logging = False


class CustomPrintToLogger:
    def __init__(
        self,
        original: TextIOWrapper,
        logger: logging.Logger,
        log_type: Literal["stdout", "stderr"],
    ):
        self.original_out: TextIOWrapper = original
        self.logger: logging.Logger = logger
        self.log_type: Literal["stdout", "stderr"] = log_type

    def write(self, message: str):
        if getattr(thread_local, "is_logging", False):
            self.original_out.write(message)
        elif message.strip():
            if self.log_type == "stderr":
                self.logger.error(message.strip())
            else:
                self.logger.info(message.strip())

    def flush(self): ...


class CustomExceptionFormatter(logging.Formatter):
    sep = "\n----------------------------------------------------------------\n"
    def formatException(self, ei: logging._SysExcInfoType) -> str:
        etype, value, tb = ei
        if value is None:
            return self.sep + super().formatException(ei) + self.sep
        return self.sep + format_exception_with_variables(value, etype=etype, tb=tb) + self.sep

    def format(self, record: logging.LogRecord) -> str:
        result = super().format(record)
        if record.exc_info:
            result += f"\n{self.formatException(record.exc_info)}"
        return result


class ColoredConsoleHandler(logging.StreamHandler, CustomExceptionFormatter):
    try:
        import colorama  # type: ignore[import-untyped, reportMissingModuleSource]
        colorama.init()
        USING_COLORAMA = True
    except ImportError:
        USING_COLORAMA = False

    RESET_CODE: str = colorama.Style.RESET_ALL if USING_COLORAMA else "\033[0m"
    COLOR_CODES: ClassVar[dict[int, str]] = {
        logging.DEBUG: colorama.Fore.CYAN if USING_COLORAMA else "\033[0;36m",  # Cyan
        logging.INFO: colorama.Fore.WHITE if USING_COLORAMA else "\033[0;37m",  # White
        logging.WARNING: colorama.Fore.YELLOW if USING_COLORAMA else "\033[0;33m",  # Yellow
        logging.ERROR: colorama.Fore.RED if USING_COLORAMA else "\033[0;31m",  # Red
        logging.CRITICAL: colorama.Back.RED if USING_COLORAMA else "\033[1;41m",  # Red background
    }

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        if record.exc_info:
            msg += f"\n{self.formatException(record.exc_info)}"
        return f"{self.COLOR_CODES.get(record.levelno, '')}{msg}{self.RESET_CODE}"


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record: dict[str, str] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exception"] = super().formatException(record.exc_info)
        return json.dumps(log_record)


class LogLevelFilter(logging.Filter):
    """Filters (allows) all the log messages at or above a specific level."""
    def __init__(self, passlevel: int, reject: bool = False):  # noqa: FBT001, FBT002
        super().__init__()
        self.passlevel: int = passlevel
        self.reject: bool = reject

    def filter(self, record: logging.LogRecord) -> bool:
        if self.reject:
            return record.levelno < self.passlevel
        return record.levelno >= self.passlevel


def get_root_logger() -> logging.Logger:
    """Parameters:
        - None
    Returns:
        - logging.Logger: The root logger with the specified handlers and formatters.
    Processing Logic:
        - If root logger already configured, return it. Otherwise:
            - Sets the root logger level to DEBUG.
            - Adds a console handler with a custom formatter.
            - Redirects stdout and stderr to the logger.
            - Adds rotating file handlers for different log levels.
            - Excludes lower level logs for handlers above DEBUG.
    """
    logger = logging.getLogger()
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        log_levels = {
            logging.DEBUG: "debug_pykotor.log",
            logging.INFO: "info_pykotor.log",
            logging.WARNING: "warning_pykotor.log",
            logging.ERROR: "error_pykotor.log",
            logging.CRITICAL: "critical_pykotor.log",
        }
        console_handler = ColoredConsoleHandler()
        formatter = logging.Formatter("%(levelname)s(%(name)s): %(message)s")
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Redirect stdout and stderr
        sys.stdout = CustomPrintToLogger(sys.__stdout__, logger, log_type="stdout")
        sys.stderr = CustomPrintToLogger(sys.__stderr__, logger, log_type="stderr")

        for level, filename in log_levels.items():
            handler = RotatingFileHandler(filename, maxBytes=1048576, backupCount=3)
            handler.setLevel(level)
            handler.setFormatter(CustomExceptionFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

            # Exclude lower level logs for handlers above DEBUG
            if level > logging.DEBUG:
                handler.addFilter(LogLevelFilter(level))

            logger.addHandler(handler)

    return logger


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
