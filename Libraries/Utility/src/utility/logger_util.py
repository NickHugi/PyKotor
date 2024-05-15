from __future__ import annotations

import json
import logging
import multiprocessing
import os
import re
import shutil
import sys
import threading
import time
import uuid

from contextlib import contextmanager, suppress
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from utility.error_handling import format_exception_with_variables

if TYPE_CHECKING:
    import datetime

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

    def isatty(self):
        return True


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

    def _safe_log(self, level: int, msg: object, *args, **kwargs):
        try:
            # Encode to UTF-8 and decode back with 'replace' to handle unencodable chars
            safe_msg = str(msg).encode("utf-8", "replace").decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            safe_msg = f"SafeEncodingLogger: Failed to encode message: {e}"
        super()._log(level, safe_msg, args, **kwargs)

    def debug(self, msg: object, *args, **kwargs):
        if self.isEnabledFor(logging.DEBUG):
            self._safe_log(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg: object, *args, **kwargs):
        if self.isEnabledFor(logging.INFO):
            self._safe_log(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg: object, *args, **kwargs):
        if self.isEnabledFor(logging.WARNING):
            self._safe_log(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg: object, *args, **kwargs):
        if self.isEnabledFor(logging.ERROR):
            self._safe_log(logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg: object, *args, **kwargs):
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


def dir_requires_admin(
    dirpath: os.PathLike | str,
    *,
    ignore_errors: bool = True,
) -> bool:  # pragma: no cover
    """Check if a dir required admin permissions to write.

    If dir is a file test it's directory.
    """
    _dirpath = Path(dirpath)
    dummy_filepath = _dirpath / str(uuid.uuid4())
    try:
        with dummy_filepath.open("w"):
            ...
        remove_any(dummy_filepath, ignore_errors=False, missing_ok=False)
    except OSError:
        if ignore_errors:
            return True
        raise
    else:
        return False


def remove_any(
    path: os.PathLike | str,
    *,
    ignore_errors: bool = True,
    missing_ok: bool = True
):
    path_obj = Path(path)
    def safe_isdir(x: Path):
        with suppress(OSError, ValueError):
            return x.is_dir()
        return None
    def safe_isfile(x: Path):
        with suppress(OSError, ValueError):
            return x.is_file()
        return None
    isdir_func = safe_isdir if ignore_errors else Path.is_dir
    exists_func = safe_isfile if ignore_errors else Path.exists
    if not exists_func(path_obj):
        if missing_ok:
            return
        import errno
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(path_obj))

    def _remove_any(x: Path):
        if isdir_func(x):
            shutil.rmtree(str(x), ignore_errors=ignore_errors)
        else:
            x.unlink(missing_ok=missing_ok)

    if sys.platform != "win32":
        _remove_any(path_obj)
    else:
        for i in range(100):
            try:
                _remove_any(path_obj)
            except Exception:  # noqa: PERF203, BLE001
                if not ignore_errors:
                    raise
                time.sleep(0.01)
            else:
                if not exists_func(path_obj):
                    return
                print(f"File/folder {path_obj} still exists after {i} iterations! (remove_any)", file=sys.stderr)
        if not ignore_errors:  # should raise at this point.
            _remove_any(path_obj)


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

def safe_isfile(path: Path):
    with suppress(Exception):
        return path.is_file()
    return False

def safe_isdir(path: Path):
    with suppress(Exception):
        return path.is_dir()
    return False

class DirectoryRotatingFileHandler(TimedRotatingFileHandler, RotatingFileHandler):
    """Handler for logging into daily directories with a static filename."""
    def __init__(
        self,
        base_log_dir: os.PathLike | str,
        filename: os.PathLike | str,
        mode: str = "a",
        maxBytes: int = 1048576,  # noqa: N803
        when: Literal["s", "m", "h", "d", "w", "S", "M", "H", "D", "W", "W0", "W1", "W2", "W3", "W4", "W5", "W6", "w0", "w1", "w2", "w3", "w4", "w5", "w6", "MIDNIGHT", "midnight"] = "h",
        interval: int = 1,
        backupCount: int = 0,  # noqa: N803
        encoding: str | None = None,
        delay: bool = False,  # noqa: FBT001, FBT002
        utc: bool = False,  # noqa: FBT001, FBT002
        atTime: datetime.time | None = None,  # noqa: N803
    ):
        self._base_dir = Path(base_log_dir)
        self._filename = Path(filename).name

        # Initialize both Timed and Rotating handlers
        TimedRotatingFileHandler.__init__(
            self, filename=self.baseFilename, when=when, interval=interval,
            backupCount=backupCount, encoding=encoding, delay=delay, utc=utc, atTime=atTime)
        RotatingFileHandler.__init__(
            self, filename=self.baseFilename, mode=mode, maxBytes=maxBytes,
            backupCount=backupCount, encoding=encoding, delay=delay)

        self.maxBytes: int = maxBytes
        self.rotator = self._rotate

    @property
    def baseFilename(self) -> str:
        if not hasattr(self, "rolloverAt"):
            # Temporarily assign the base filename
            return str(self._base_dir / self._filename)  # Use a direct path for initial setup
        return str(self._get_cur_directory() / self._filename)

    @baseFilename.setter
    def baseFilename(self, value):
        ...  # Override to do nothing

    def _get_timestamp_folder_name(self):
        """Get the time that this sequence started at and make it a TimeTuple."""
        currentTime = int(time.time())
        dstNow = time.localtime(currentTime)[-1]
        t = self.rolloverAt - self.interval
        if self.utc:
            timeTuple = time.gmtime(t)
        else:
            timeTuple = time.localtime(t)
            dstThen = timeTuple[-1]
            if dstNow != dstThen:
                addend = 3600 if dstNow else -3600
                timeTuple = time.localtime(t + addend)
        return self.rotation_filename(time.strftime(self.suffix, timeTuple))

    def _get_cur_directory(self) -> Path:
        """Generate the directory path based on the current date or interval."""
        return get_log_directory(self._base_dir / self._get_timestamp_folder_name())

    def shouldRollover(
        self,
        record: logging.LogRecord,
    ) -> Literal[1, 0]:
        """Check for rollover based on both size and time."""
        return RotatingFileHandler.shouldRollover(self, record)

    def _rotate(
        self,
        source: os.PathLike | str,
        dest: os.PathLike | str,
    ):
        """Custom rotate method that handles file rotation."""
        src_path = Path(source)
        if src_path.exists():
            src_path.rename(Path(dest))

    def doRollover(self):
        """Perform a rollover.
        In this version, old files are never deleted.
        """
        if self.stream:
            self.stream.close()
            self.stream = None

        current_path = Path(self.baseFilename)
        root = current_path.stem
        ext = current_path.suffix
        directory = current_path.parent

        # Regex to match files that follow the naming pattern 'root.number.ext'
        pattern = re.compile(rf"^{re.escape(root)}\.(\d+){re.escape(ext)}$")

        # Collect and parse existing log files to determine the next file number
        files: list[int] = []
        for f in directory.iterdir():
            if not safe_isfile(f):
                continue
            match = pattern.match(f.name)
            if match:
                files.append(int(match.group(1)))

        next_file_number = max(files) + 1 if files else 1
        new_name = directory / f"{root}.{next_file_number}{ext}"
        self.rotate(self.baseFilename, str(new_name))

        if not self.delay:
            self.stream = self._open()


class RootLoggerWrapper:
    """Setup a logger with some standard features.

    The goal is to have this be callable anywhere anytime regardless of whether a logger is setup yet.

    Args:
    ----
        use_level(int): Logging level to setup for this application.

    Returns:
    -------
        logging.Logger: The root logger with the specified handlers and formatters.
    """
    _logger = None

    def __init__(self, use_level=logging.DEBUG):
        self._logger: logging.Logger = self._setup_logger(use_level) if self._logger is None else self._logger

    def _setup_logger(
        self,
        use_level: logging._Level = logging.DEBUG,
    ) -> logging.Logger:
        self._logger = logger = logging.getLogger()
        if not logger.handlers:
            logger.setLevel(use_level)

            cur_process = multiprocessing.current_process()
            console_format_str = "%(levelname)s(%(name)s): %(message)s"
            if cur_process.name == "MainProcess":
                log_dir = get_log_directory(subdir="logs")
                everything_log_file = "debug_pykotor.log"
                info_warning_log_file = "pykotor.log"
                error_critical_log_file = "errors_pykotor.log"
                exception_log_file = "exception_pykotor.log"
            else:
                log_dir = get_log_directory(subdir=f"logs/{cur_process.pid}")
                everything_log_file = f"debug_pykotor_{cur_process.pid}.log"
                info_warning_log_file = f"pykotor_{cur_process.pid}.log"
                error_critical_log_file = f"errors_pykotor_{cur_process.pid}.log"
                exception_log_file = f"exception_pykotor_{cur_process.pid}.log"
                console_format_str = f"PID={cur_process.pid} - {console_format_str}"

            console_handler = ColoredConsoleHandler()
            formatter = logging.Formatter(console_format_str)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

            # Redirect stdout and stderr
            sys.stdout = CustomPrintToLogger(logger, sys.__stdout__, log_type="stdout")
            sys.stderr = CustomPrintToLogger(logger, sys.__stderr__, log_type="stderr")

            default_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            exception_formatter = CustomExceptionFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

            # Handler for everything (DEBUG and above)
            everything_handler = DirectoryRotatingFileHandler(log_dir, everything_log_file, maxBytes=20485760, backupCount=10000, delay=True, encoding="utf8")
            everything_handler.setLevel(logging.DEBUG)
            everything_handler.setFormatter(default_formatter)
            logger.addHandler(everything_handler)

            # Handler for INFO and WARNING
            info_warning_handler = DirectoryRotatingFileHandler(log_dir, info_warning_log_file, maxBytes=20485760, backupCount=10000, delay=True, encoding="utf8")
            info_warning_handler.setLevel(logging.INFO)
            info_warning_handler.setFormatter(default_formatter)
            info_warning_handler.addFilter(LogLevelFilter(logging.ERROR, reject=True))
            logger.addHandler(info_warning_handler)

            # Handler for ERROR and CRITICAL
            error_critical_handler = DirectoryRotatingFileHandler(log_dir, error_critical_log_file, maxBytes=20485760, backupCount=10000, delay=True, encoding="utf8")
            error_critical_handler.setLevel(logging.ERROR)
            error_critical_handler.addFilter(LogLevelFilter(logging.ERROR))
            error_critical_handler.setFormatter(exception_formatter)
            logger.addHandler(error_critical_handler)

            # Handler for EXCEPTIONS ONLY (using CustomExceptionFormatter)
            exception_handler = DirectoryRotatingFileHandler(log_dir, exception_log_file, maxBytes=20485760, backupCount=10000, delay=True, encoding="utf8")
            exception_handler.setLevel(logging.ERROR)
            exception_handler.setFormatter(exception_formatter)
            exception_handler.addFilter(LogLevelFilter(logging.ERROR))  # Only log ERROR and CRITICAL levels
            logger.addHandler(exception_handler)

        return logger

    def __call__(self) -> logging.Logger:
        return self._setup_logger() if self._logger is None else self._logger

    def __getattr__(self, attr):
        return getattr(self._setup_logger() if self._logger is None else self._logger, attr)


get_root_logger = RootLoggerWrapper()


# Example usage
if __name__ == "__main__":
    get_root_logger.debug("This is a debug message.")
    logger = get_root_logger()
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical message.")

    # Uncomment to test uncaught exception logging
    raise RuntimeError("Test uncaught exception")
