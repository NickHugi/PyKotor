from __future__ import annotations

import json
import logging
import multiprocessing
import os
import sys
import threading

from contextlib import contextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from utility.error_handling import format_exception_with_variables

if TYPE_CHECKING:
    from io import TextIOWrapper
    from types import TracebackType

    from typing_extensions import Literal


class UTF8StreamWrapper:
    def __init__(self, original_stream):
        self.original_stream = original_stream

    def write(self, message):
        # Ensure message is a string, encode to UTF-8 with errors replaced,
        # then write to the original stream's buffer directly.
        if self.original_stream is None:  # windowed mode PyInstaller
            return
        if isinstance(message, str):
            message = message.encode("utf-8", errors="replace")
        self.original_stream.buffer.write(message)

    def flush(self):
        if self.original_stream is None:  # windowed mode PyInstaller
            return
        self.original_stream.flush()

    def __getattr__(self, attr):
        # Delegate any other method calls to the original stream
        return getattr(self.original_stream, attr)


# region threading

# Global lock for thread-safe operations
LOGGING_LOCK = threading.Lock()
THREAD_LOCAL = threading.local()
THREAD_LOCAL.is_logging = False


@contextmanager
def logging_context():
    global LOGGING_LOCK  # noqa: PLW0602
    with LOGGING_LOCK:
        prev_state = getattr(THREAD_LOCAL, "is_logging", False)
        THREAD_LOCAL.is_logging = True

    try:
        yield
    finally:
        with LOGGING_LOCK:
            THREAD_LOCAL.is_logging = prev_state


# endregion
def get_this_child_pid() -> None | int:
    """Get our pid, if we're main process return None."""
    cur_process = multiprocessing.current_process()
    return None if cur_process.name == "MainProcess" else cur_process.pid


class CustomPrintToLogger:
    def __init__(
        self,
        logger: logging.Logger,
        original: TextIOWrapper,
        log_type: Literal["stdout", "stderr"],
    ):
        self.original_out: TextIOWrapper = original
        self.log_type: Literal["stdout", "stderr"] = log_type
        self.logger: logging.Logger = logger
        self.configure_logger_stream()


    def configure_logger_stream(self):
        utf8_wrapper = UTF8StreamWrapper(self.original_out)
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setStream(utf8_wrapper)

    def write(
        self,
        message: str,
    ):
        if getattr(THREAD_LOCAL, "is_logging", False):
            self.original_out.write(message)
        elif message.strip():
            # Use the logging_context to prevent recursive calls
            with logging_context():
                if self.log_type == "stderr":
                    self.logger.error(message.strip())
                else:
                    self.logger.info(message.strip())

    def flush(self): ...


class SafeEncodingLogger(logging.Logger):
    """A custom logger that safely handles log messages containing characters
    that cannot be represented in the default system encoding. It overrides
    the standard log methods to encode and decode messages with a safe
    handling for unmappable characters.
    """

    def __init__(
        self,
        name: str,
        *args,
        **kwargs,
    ):
        super().__init__(name, *args, **kwargs)

    def _safe_log(self, level: int, msg: str, *args, **kwargs):
        try:
            # Encode to UTF-8 and decode back with 'replace' to handle unencodable chars
            safe_msg = msg.encode("utf-8", "replace").decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            safe_msg = f"Failed to encode message: {e}"
        super()._log(level, safe_msg, args, **kwargs)

    def debug(self, msg: str, *args, **kwargs):
        if self.isEnabledFor(logging.DEBUG):
            self._safe_log(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        if self.isEnabledFor(logging.INFO):
            self._safe_log(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        if self.isEnabledFor(logging.WARNING):
            self._safe_log(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        if self.isEnabledFor(logging.ERROR):
            self._safe_log(logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        if self.isEnabledFor(logging.CRITICAL):
            self._safe_log(logging.CRITICAL, msg, *args, **kwargs)


logging.setLoggerClass(SafeEncodingLogger)


class CustomExceptionFormatter(logging.Formatter):
    sep = "\n----------------------------------------------------------------\n"

    def formatException(
        self,
        ei: tuple[type[BaseException], BaseException, TracebackType | None] | tuple[None, None, None],
    ) -> str:
        etype, value, tb = ei
        if value is None:
            return self.sep + super().formatException(ei) + self.sep
        return self.sep + format_exception_with_variables(value, etype=etype, tb=tb) + self.sep

    def format(
        self,
        record: logging.LogRecord,
    ) -> str:
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

    def __init__(
        self,
        passlevel: int,
        *,
        reject: bool = False,
    ):  # noqa: FBT001, FBT002
        super().__init__()
        self.passlevel: int = passlevel
        self.reject: bool = reject

    def filter(
        self,
        record: logging.LogRecord,
    ) -> bool:
        if self.reject:
            return record.levelno < self.passlevel
        return record.levelno >= self.passlevel


def get_fallback_log_dir() -> Path:
    """Determine a known good location based on the platform."""
    if sys.platform.startswith("win"):  # Use ProgramData for Windows, which is typically for application data for all users
        return Path(os.environ.get("PROGRAMDATA", "C:/ProgramData")) / "PyUtility"
    return Path.home() / ".pyutility"


def get_log_directory(subdir: os.PathLike | str | None = None) -> Path:
    """Determine the best directory for logs based on availability and permissions."""
    def check(path: Path) -> Path:
        if not path.exists() or not path.is_dir():
            path.unlink(missing_ok=True)
            path.mkdir(parents=True, exist_ok=True)  # Attempt to create the fallback directory
        from utility.system.os_helper import dir_requires_admin
        if dir_requires_admin(path, ignore_errors=False):
            raise PermissionError(f"Directory '{path}' requires admin.")
        return path

    cwd = Path.cwd()
    subdir = Path("logs") if subdir is None else Path(subdir)
    try:
        return check(subdir)
    except Exception as e:
        print(f"Failed to init 'logs' dir in cwd '{cwd}': {e}")
        try:
            return check(cwd)
        except Exception as e2:  # noqa: BLE001
            print(f"Failed to init cwd fallback '{cwd}' as log directory: {e2}\noriginal: {e}")
            return check(get_fallback_log_dir())


def get_root_logger(
    use_level: int = logging.DEBUG,
) -> logging.Logger:
    """Setup a logger with some standard features.

    The goal is to have this be able to be called anywhere anytime regardless of whether a logger is setup yet.

    Args:
    ----
        use_level(int): Logging level to setup for this application.

    Returns:
    -------
        logging.Logger: The root logger with the specified handlers and formatters.
    """
    logger = logging.getLogger()
    if not logger.handlers:
        logger.setLevel(use_level)

        cur_process = multiprocessing.current_process()
        console_format_str = "%(levelname)s(%(name)s): %(message)s"
        if cur_process.name == "MainProcess":
            log_dir = get_log_directory(subdir="logs")
            everything_log_file = log_dir / "debug_pykotor.log"
            info_warning_log_file = log_dir / "pykotor.log"
            error_critical_log_file = log_dir / "errors_pykotor.log"
        else:
            log_dir = get_log_directory(subdir=f"logs/{cur_process.pid}")
            everything_log_file = log_dir / f"debug_pykotor_{cur_process.pid}.log"
            info_warning_log_file = log_dir / f"pykotor_{cur_process.pid}.log"
            error_critical_log_file = log_dir / f"errors_pykotor_{cur_process.pid}.log"
            console_format_str = f"PID={cur_process.pid} - {console_format_str}"

        console_handler = ColoredConsoleHandler()
        formatter = logging.Formatter(console_format_str)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Redirect stdout and stderr
        sys.stdout = CustomPrintToLogger(logger, sys.__stdout__, log_type="stdout")
        sys.stderr = CustomPrintToLogger(logger, sys.__stderr__, log_type="stderr")

        # Handler for everything (DEBUG and above)
        everything_handler = RotatingFileHandler(everything_log_file, maxBytes=1048576, backupCount=3, delay=True, encoding="utf8")
        everything_handler.setLevel(logging.DEBUG)
        everything_handler.setFormatter(CustomExceptionFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        logger.addHandler(everything_handler)

        # Handler for INFO and WARNING
        info_warning_handler = RotatingFileHandler(info_warning_log_file, maxBytes=1048576, backupCount=3, delay=True, encoding="utf8")
        info_warning_handler.setLevel(logging.INFO)
        info_warning_handler.setFormatter(CustomExceptionFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        info_warning_handler.addFilter(LogLevelFilter(logging.ERROR, reject=True))
        logger.addHandler(info_warning_handler)

        # Handler for ERROR and CRITICAL
        error_critical_handler = RotatingFileHandler(error_critical_log_file, maxBytes=1048576, backupCount=3, delay=True, encoding="utf8")
        error_critical_handler.setLevel(logging.ERROR)
        error_critical_handler.addFilter(LogLevelFilter(logging.ERROR))
        error_critical_handler.setFormatter(CustomExceptionFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        logger.addHandler(error_critical_handler)

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
    raise RuntimeError("Test uncaught exception")
