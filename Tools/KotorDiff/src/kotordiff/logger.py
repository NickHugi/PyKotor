#!/usr/bin/env python3
"""Enhanced logging system for KotorDiff with colorama support and configurable levels."""
from __future__ import annotations

import logging
import sys

from enum import Enum
from io import StringIO
from typing import ClassVar, TextIO

try:
    import colorama  # type: ignore[import-untyped]

    from colorama import Fore, Style
    colorama.init(autoreset=True)
    HAS_COLORAMA = True
except ImportError:
    # Fallback if colorama is not available
    HAS_COLORAMA = False

    class _FakeFore:
        RED = ""
        GREEN = ""
        YELLOW = ""
        BLUE = ""
        MAGENTA = ""
        CYAN = ""
        WHITE = ""
        RESET = ""

    class _FakeStyle:
        BRIGHT = ""
        DIM = ""
        RESET_ALL = ""

    Fore = _FakeFore()
    Style = _FakeStyle()


class LogLevel(Enum):
    """Logging levels for KotorDiff."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class OutputMode(Enum):
    """Output modes for KotorDiff."""
    FULL = "full"  # Include all logging output
    DIFF_ONLY = "diff_only"  # Only diff results
    QUIET = "quiet"  # Minimal output


class DiffLogger:
    """Enhanced logger for KotorDiff with color support and configurable output modes."""

    def __init__(
        self,
        level: LogLevel = LogLevel.INFO,
        output_mode: OutputMode = OutputMode.FULL,
        *,
        use_colors: bool = True,
        output_file: TextIO | None = None,
    ):
        self.level: LogLevel = level
        self.output_mode: OutputMode = output_mode
        self.use_colors: bool = use_colors and HAS_COLORAMA
        self.output_file: TextIO | None = output_file

        # Set up the underlying logger
        self._logger: logging.Logger = logging.getLogger("kotordiff")
        self._logger.setLevel(level.value)

        # Clear any existing handlers
        self._logger.handlers.clear()

        # Add console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level.value)

        # Create formatter
        if self.use_colors:
            console_handler.setFormatter(ColoredFormatter())
        else:
            console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        self._logger.addHandler(console_handler)

        # Add file handler if specified
        if output_file:
            file_handler = logging.StreamHandler(output_file)
            file_handler.setLevel(level.value)
            file_formatter = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")
            file_handler.setFormatter(file_formatter)
            self._logger.addHandler(file_handler)

    def debug(self, message: str, *args, **kwargs):
        """Log a debug message."""
        if self.output_mode != OutputMode.DIFF_ONLY:
            self._logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        """Log an info message."""
        if self.output_mode != OutputMode.DIFF_ONLY:
            self._logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        """Log a warning message."""
        if self.output_mode != OutputMode.QUIET:
            self._logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        """Log an error message."""
        self._logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        """Log a critical message."""
        self._logger.critical(message, *args, **kwargs)

    def diff_output(self, message: str, *args, **kwargs):
        """Output diff-specific content that should always be shown."""
        # Always output diff content, regardless of mode
        print(message, *args, **kwargs)
        if self.output_file:
            print(message, *args, file=self.output_file, **kwargs)

    def separator(
        self,
        message: str,
        char: str = "-",
        *,
        above: bool = False,
        below: bool = True,
    ):
        """Output a separator line."""
        separator_line = char * len(message)
        if above:
            self.diff_output(separator_line)
        self.diff_output(message)
        if below:
            self.diff_output(separator_line)


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support."""

    COLORS: ClassVar[dict[int, str]] = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.MAGENTA + Style.BRIGHT,
    }

    def format(self, record):
        if record.levelno in self.COLORS:
            color = self.COLORS[record.levelno]
            record.levelname = f"{color}{record.levelname}{Style.RESET_ALL}"
            record.msg = f"{color}{record.msg}{Style.RESET_ALL}"
        return super().format(record)


# Global logger instance
_logger: DiffLogger | None = None


def setup_logger(
    level: LogLevel = LogLevel.INFO,
    output_mode: OutputMode = OutputMode.FULL,
    *,
    use_colors: bool = True,
    output_file: TextIO | None = None,
) -> DiffLogger:
    """Set up the global logger instance."""
    global _logger  # noqa: PLW0603
    _logger = DiffLogger(level, output_mode, use_colors=use_colors, output_file=output_file)
    return _logger


def get_logger() -> DiffLogger:
    """Get the global logger instance."""
    if _logger is None:
        return setup_logger()
    return _logger


# Convenience functions
def debug(message: str, *args, **kwargs):
    """Log a debug message."""
    get_logger().debug(message, *args, **kwargs)


def info(message: str, *args, **kwargs):
    """Log an info message."""
    get_logger().info(message, *args, **kwargs)


def warning(message: str, *args, **kwargs):
    """Log a warning message."""
    get_logger().warning(message, *args, **kwargs)


def error(message: str, *args, **kwargs):
    """Log an error message."""
    get_logger().error(message, *args, **kwargs)


def critical(message: str, *args, **kwargs):
    """Log a critical message."""
    get_logger().critical(message, *args, **kwargs)


def diff_output(message: str, *args, **kwargs):
    """Output diff-specific content."""
    get_logger().diff_output(message, *args, **kwargs)


def separator(message: str, char: str = "-", *, above: bool = False, below: bool = True):
    """Output a separator line."""
    get_logger().separator(message, char=char, above=above, below=below)


# ---------------------------------------------------------------------------
# Legacy log_output functions for backwards compatibility with __main__.py
# ---------------------------------------------------------------------------

def log_output_basic(*args, **kwargs):
    """Basic logging output without file handling (used when global config not set)."""
    buffer = StringIO()
    print(*args, file=buffer, **kwargs)
    msg = buffer.getvalue()

    # Print the captured output to console with Unicode error handling
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Fallback: encode with error handling for Windows console
        try:
            safe_msg = msg.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8")
            print(safe_msg, **kwargs)
        except Exception:  # noqa: BLE001
            # Last resort: use ASCII with backslashreplace
            safe_msg = msg.encode("ascii", errors="backslashreplace").decode("ascii")
            print(safe_msg, **kwargs)

    return msg
