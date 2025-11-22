"""Logging utilities for KOTORNasher."""
from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from logging import Logger


# ANSI color codes
class Colors:
    """ANSI color codes for terminal output."""

    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log output."""

    COLORS: ClassVar[dict[int, str]] = {
        logging.DEBUG: Colors.DIM,
        logging.INFO: Colors.CYAN,
        logging.WARNING: Colors.YELLOW,
        logging.ERROR: Colors.RED,
        logging.CRITICAL: f"{Colors.BOLD}{Colors.RED}",
    }

    def __init__(self, use_color: bool = True):
        super().__init__()
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        if self.use_color and record.levelno in self.COLORS:
            levelname = f"{self.COLORS[record.levelno]}{record.levelname}{Colors.RESET}"
        else:
            levelname = record.levelname

        return f"[{levelname}] {record.getMessage()}"


def setup_logger(level: str = "INFO", use_color: bool = True) -> Logger:
    """Setup and configure the logger.

    Args:
    ----
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_color: Whether to use colored output

    Returns:
    -------
        Configured logger instance
    """
    logger = logging.getLogger("kotornasher")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColoredFormatter(use_color))
    logger.addHandler(handler)

    return logger



