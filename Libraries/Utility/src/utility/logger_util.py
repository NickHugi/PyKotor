from __future__ import annotations

import atexit
import logging
import multiprocessing
import os
import shutil
import sys
import threading
import time
import uuid

from contextlib import contextmanager, suppress
from logging.handlers import RotatingFileHandler
from pathlib import Path
from queue import Queue
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Tuple, Union, cast

from utility.error_handling import format_exception_with_variables

if TYPE_CHECKING:
    import queue

    from contextlib import _GeneratorContextManager
    from io import TextIOWrapper
    from logging.handlers import QueueListener
    from multiprocessing.process import BaseProcess
    from types import TracebackType

    from typing_extensions import Literal, Self


class UTF8StreamWrapper:
    def __init__(self, original_stream: TextIOWrapper[str]):
        self.original_stream: TextIOWrapper[str] = original_stream

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
        self.buffer = ""

    def isatty(self) -> Literal[False]:
        return False

    def configure_logger_stream(self):
        utf8_wrapper = UTF8StreamWrapper(self.original_out)
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setStream(utf8_wrapper)  # type: ignore[arg-type]

    def write(self, message: str):
        if getattr(THREAD_LOCAL, "is_logging", False):
            self.original_out.write(message)
        else:
            self.buffer += message
            while "\n" in self.buffer:
                line, self.buffer = self.buffer.split("\n", 1)
                self._log_message(line)

    def flush(self):
        if self.buffer:
            self._log_message(self.buffer)
            self.buffer = ""

    def _log_message(self, message: str):
        if message and message.strip():
            with logging_context():
                if self.log_type == "stderr":
                    self.logger.error(message.strip())
                else:
                    self.logger.debug(message.strip())


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
    finally:
        remove_any(dummy_filepath, ignore_errors=True, missing_ok=True)


def remove_any(
    path: os.PathLike | str,
    *,
    ignore_errors: bool = True,
    missing_ok: bool = True
):
    path_obj = Path(path)
    isdir_func = safe_isdir if ignore_errors else Path.is_dir
    isfile_func = safe_isfile if ignore_errors else Path.exists
    if not isfile_func(path_obj):
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
                if not isfile_func(path_obj):
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
    except Exception as e:  # noqa: BLE001
        print(f"Failed to init 'logs' dir in cwd '{cwd}': {e}")
        try:
            return check(cwd)
        except Exception as e2:  # noqa: BLE001
            print(f"Failed to init cwd fallback '{cwd}' as log directory: {e2}\noriginal: {e}")
            return check(get_fallback_log_dir())


def safe_isfile(path: Path) -> bool:
    with suppress(Exception):
        return path.is_file()
    return False


def safe_isdir(path: Path) -> bool:
    with suppress(Exception):
        return path.is_dir()
    return False


class MetaLogger(type):
    def _create_instance(cls: type[RobustRootLogger]) -> RobustRootLogger:  # type: ignore[misc]
        instance = object.__new__(cls)
        object.__getattribute__(instance, "__new__")(cls)
        object.__getattribute__(instance, "__init__")()
        type.__setattr__(cls, "_instance", instance)
        return instance
    def __getattribute__(cls: type[RobustRootLogger], attr_name: str):  # type: ignore[misc]
        if attr_name.startswith("__") and attr_name.endswith("__"):
            return super().__getattribute__(attr_name)  # type: ignore[misc]
        instance: RobustRootLogger | None = type.__getattribute__(RobustRootLogger, "_instance")
        if instance is None:
            instance = MetaLogger._create_instance(cls)
        return getattr(instance, attr_name)

    def __call__(cls, *args, **kwargs) -> RobustRootLogger:
        # sourcery skip: assign-if-exp, merge-duplicate-blocks, reintroduce-else, remove-redundant-if, split-or-ifs
        instance: RobustRootLogger | None = type.__getattribute__(RobustRootLogger, "_instance")
        if instance is None:
            instance = MetaLogger._create_instance(cls)  # type: ignore[arg-type]
        if args or kwargs:
            instance.info(*args, **kwargs)
        return instance


class RobustRootLogger(logging.Logger, metaclass=MetaLogger):  # noqa: N801
    """Setup a logger with some standard features.

    The goal is to have this be callable anywhere anytime regardless of whether a logger is setup yet.

    Args:
    ----
        use_level(int): Logging level to setup for this application.

    Returns:
    -------
        logging.Logger: The root logger with the specified handlers and formatters.
    """
    _instance: Self | None = None
    _queue: Queue = Queue()
    _logger: logging.Logger = None  # type: ignore[assignment]

    def __reduce__(self) -> tuple[type[Self], tuple[()]]:
        return self.__class__, ()

    def _safe_print(self, message: str):
        print(message, file=sys.__stderr__)

    def __getattribute__(self, attr_name: str) -> Any:
        our_type: type[Self] = object.__getattribute__(self, "__class__")
        try:
            attr_value = super().__getattribute__(attr_name)
            if attr_name == "_robust_root_lock":
                return attr_value
            if object.__getattribute__(self, "_robust_root_lock"):  # noqa: FBT003
                return attr_value
            if attr_value is not our_type and not isinstance(attr_value, our_type) and callable(attr_value):
                def wrapped(*args, **kwargs):
                    try:
                        object.__setattr__(self, "_robust_root_lock", True)
                        return attr_value(*args, **kwargs)
                    except Exception as e:  # noqa: BLE001
                        print(f"Exception when accessing attribute {attr_name}: {e}", file=sys.__stderr__)
                        #print(traceback.format_exc(), file=sys.__stderr__)
                        print(f"{e.__class__.__name__}: {e}", file=sys.__stderr__)
                    finally:
                        object.__setattr__(self, "_robust_root_lock", False)
                return wrapped
        except AttributeError:
            raise
        except Exception as e:  # noqa: BLE001
            #if isinstance(e, AttributeError) and type.__getattribute__(our_type, "__getattr__") is not None:
            #    raise  # python's logger module doesn't define this, but might as well future proof our code.

            print(f"(Caught by RobustRootLogger!) Exception when accessing attribute '{attr_name}': {e}", file=sys.__stderr__)
            print(f"{e.__class__.__name__}: {e}", file=sys.__stderr__)
            return ""
        else:
            return attr_value

    def __getattr__(self, attr_name: str):
        logger = object.__getattribute__(self, "_logger")
        if logger is None:
            object.__setattr__(self, "_instance", None)
            object.__getattribute__(self, "__init__")()
            logger = object.__getattribute__(self, "_logger")
        assert logger is not None
        return object.__getattribute__(logger, attr_name)

    def __init__(self):
        self.listener: QueueListener
        cls = object.__getattribute__(self, "__class__")
        if not object.__getattribute__(cls, "_logger"):
            type.__setattr__(cls, "_logger", object.__getattribute__(self, "_setup_logger")())
            listener_thread = threading.Thread(target=object.__getattribute__(self, "_start_listener"))
            listener_thread.daemon = True
            self.listener_thread = listener_thread

    def _setup_logger(
        self,
    ) -> logging.Logger:
        logger = logging.getLogger()
        if not logger.handlers:
            from utility.misc import is_debug_mode
            use_level = logging.DEBUG if is_debug_mode() else logging.INFO
            logger.setLevel(use_level)

            cur_process: BaseProcess = multiprocessing.current_process()
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

            #our_queue = type.__getattribute__(object.__getattribute__(self, "__class__"), "_queue")
            #queue_handler = QueueHandler(our_queue)
            #logger.addHandler(queue_handler)

            console_handler = ColoredConsoleHandler()
            formatter = logging.Formatter(console_format_str)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

            # Redirect stdout and stderr
            sys.stdout = CustomPrintToLogger(logger, sys.__stdout__, log_type="stdout")  # type: ignore[assignment]
            sys.stderr = CustomPrintToLogger(logger, sys.__stderr__, log_type="stderr")  # type: ignore[assignment]

            default_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            exception_formatter = CustomExceptionFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

            # Handler for everything (DEBUG and above)
            if use_level == logging.DEBUG:
                everything_handler = RotatingFileHandler(str(log_dir / everything_log_file), maxBytes=20*1024*1024, backupCount=5, encoding="utf8")
                everything_handler.setLevel(logging.DEBUG)
                everything_handler.setFormatter(default_formatter)
                logger.addHandler(everything_handler)

            # Handler for INFO and WARNING
            info_warning_handler = RotatingFileHandler(str(log_dir / info_warning_log_file), maxBytes=20*1024*1024, backupCount=5, encoding="utf8")
            info_warning_handler.setLevel(logging.INFO)
            info_warning_handler.setFormatter(default_formatter)
            info_warning_handler.addFilter(LogLevelFilter(logging.ERROR, reject=True))
            logger.addHandler(info_warning_handler)

            # Handler for ERROR and CRITICAL
            error_critical_handler = RotatingFileHandler(str(log_dir / error_critical_log_file), maxBytes=20*1024*1024, backupCount=5, encoding="utf8")
            error_critical_handler.setLevel(logging.ERROR)
            error_critical_handler.addFilter(LogLevelFilter(logging.ERROR))
            error_critical_handler.setFormatter(exception_formatter)
            logger.addHandler(error_critical_handler)

            # Handler for EXCEPTIONS (using CustomExceptionFormatter)
            exception_handler = RotatingFileHandler(str(log_dir / exception_log_file), maxBytes=20*1024*1024, backupCount=5, encoding="utf8")
            exception_handler.setLevel(logging.ERROR)
            exception_handler.setFormatter(exception_formatter)
            exception_handler.addFilter(LogLevelFilter(logging.ERROR))
            logger.addHandler(exception_handler)
            object.__setattr__(self, "_orig_log_func", logger._log)
            logger._log = object.__getattribute__(self, "_log")  # doesn't properly work

            # Adding handlers to the queue listener
            #object.__setattr__(self, "listener", QueueListener(object.__getattribute__(self, "_queue"), console_handler, everything_handler, info_warning_handler, error_critical_handler, exception_handler))

        return logger

    def _start_listener(self):
        if not hasattr(self, "listener"):
            object.__getattribute__(self, "_setup_logger")()
        try:
            object.__getattribute__(self, "listener_thread").start()
        except AttributeError:
            logging.getLogger().handlers = []
            object.__setattr__(object.__getattribute__(self, "__class__"), "_logger", self._setup_logger())
            object.__getattribute__(self, "listener_thread").start()

    def __call__(self, *args, **kwargs) -> RobustRootLogger:
        _actual_logger: logging.Logger | None = object.__getattribute__(self, "_logger")
        if _actual_logger is None:
            object.__getattribute__(self, "__class__")()
        return self

    def _log(self, level: int, msg: str, *args, **kwargs) -> None:  # type: ignore[override]
        our_queue: queue.Queue = object.__getattribute__(self, "_queue")
        try:
            logging_thread_func = object.__getattribute__(self, "logging_thread_func")
        except AttributeError:
            # Custom logic to prevent encoding issues
            def logging_thread_func(
                queue: queue.Queue,
                logging_context: Callable[..., _GeneratorContextManager[None]],
            ):
                while True:
                    task = cast(Union[Tuple[int, str, tuple, dict], None], queue.get())
                    if task is None:
                        break  # Stop signal
                    level, msg, args, kwargs = task
                    orig_log_func = object.__getattribute__(self, "_orig_log_func")
                    with logging_context():
                        orig_log_func(level, msg.encode(encoding="utf-8", errors="replace").decode(), *args, **kwargs)  # noqa: SLF001
                    queue.task_done()

            logging_thread = threading.Thread(target=logging_thread_func, args=(our_queue,logging_context))
            logging_thread.start()
            atexit.register(our_queue.put, None)
            object.__setattr__(self, "logging_thread_func", logging_thread_func)

        our_queue.put((level, msg, args, kwargs))


get_root_logger = RobustRootLogger  # deprecated, provided for backwards compatibility.


# Example usage
if __name__ == "__main__":
    RobustRootLogger.debug("This is a debug message.")
    logger = RobustRootLogger()
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical message.")

    # Test various edge case
    RobustRootLogger("This is a test of __call__")

    # Uncomment to test uncaught exception logging
    raise RuntimeError("Test uncaught exception")
