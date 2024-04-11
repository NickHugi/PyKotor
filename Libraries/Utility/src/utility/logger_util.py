from __future__ import annotations

import json
import logging
import multiprocessing
import sys
import threading

from contextlib import contextmanager
from logging.handlers import RotatingFileHandler
from queue import Empty
from typing import TYPE_CHECKING, ClassVar

from utility.error_handling import format_exception_with_variables

if TYPE_CHECKING:
    from io import TextIOWrapper
    from types import TracebackType

    from typing_extensions import Literal

# region threading

# Global lock for thread-safe operations
logging_lock = threading.Lock()
THREAD_LOCAL = threading.local()
THREAD_LOCAL.is_logging = False

@contextmanager
def logging_context():
    global logging_lock
    with logging_lock:
        prev_state = getattr(THREAD_LOCAL, "is_logging", False)
        THREAD_LOCAL.is_logging = True

    try:
        yield
    finally:
        with logging_lock:
            THREAD_LOCAL.is_logging = prev_state

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
# endregion

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


# region multiprocessing

LISTENER_THREAD: threading.Thread | None = None
LOG_QUEUE = multiprocessing.Queue()


def setup_main_listener():
    import atexit
    global LISTENER_THREAD
    LISTENER_THREAD = threading.Thread(target=listener_thread_function, args=(LOG_QUEUE,))
    LISTENER_THREAD.daemon = True
    LISTENER_THREAD.start()
    atexit.register(stop_listener)


def listener_thread_function(queue: multiprocessing.Queue):
    """Function run by the listener thread to process log messages."""
    while True:
        try:
            record: logging.LogRecord = queue.get(timeout=2)
            if record == "STOP":
                break
            logger = logging.getLogger(record.name)
            logger.handle(record)
        except Empty:  # noqa: S112
            continue


def stop_listener():
    LOG_QUEUE.put("STOP")
    if LISTENER_THREAD is not None:
        LISTENER_THREAD.join()

class QueueLogHandler(logging.Handler):
    """A handler that writes logs to a shared multiprocessing queue."""

    def __init__(
        self,
        log_queue: multiprocessing.Queue,
    ):
        super().__init__()
        self.log_queue: multiprocessing.Queue = log_queue

    def emit(
        self,
        record: logging.LogRecord,
    ):
        self.log_queue.put(record)
# endregion


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


def get_root_logger(
    use_level: int = logging.DEBUG,
) -> logging.Logger:
    """Setup a logger with some standard features.

    Args:
    ----
        use_level(int): Logging level to setup for this application.

    Returns:
    -------
        logging.Logger: The root logger with the specified handlers and formatters.
    """
    logger = logging.getLogger()
    if multiprocessing.current_process().name == "MainProcess":
        if not logger.handlers:
            setup_main_listener()
    else:
        logger.setLevel(use_level)
        handler = QueueLogHandler(LOG_QUEUE)
        logger.addHandler(handler)
        return logger

    if not logger.handlers:
        logger.setLevel(use_level)

        everything_log_file = "debug_pykotor.log"
        info_warning_log_file = "pykotor.log"
        error_critical_log_file = "errors_pykotor.log"

        console_handler = ColoredConsoleHandler()
        formatter = logging.Formatter("%(levelname)s(%(name)s): %(message)s")
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
