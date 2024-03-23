from __future__ import annotations

import logging
import sys

from utility.system.path import Path

IGNORABLE_LOGGERS: set[str] = {"charset_normalizer", "concurrent.futures", "concurrent", "PIL.Image", "PIL", "urllib3.util.retry"}

def is_internal_logger(logger_name: str, project_root: str) -> bool:
    """Check if a logger is an internal logger by seeing if the module that created
    the logger is within the project's root directory.
    """
    # Iterate through all modules and match their logger names
    for module in sys.modules.values():
        # Try to get the __file__ attribute of the module
        module_file = getattr(module, "__file__", None)
        if module_file is None:
            continue
        if not isinstance(module_file, str):
            continue
        if module_file.startswith(project_root):
            module_logger_name = module.__name__
            if logger_name.startswith(module_logger_name):
                return True
    return False

def get_first_available_logger() -> logging.Logger:
    project_root = Path(__file__).parents[4]
    logger_dict = logging.root.manager.loggerDict
    for logger_name, logger_obj in logger_dict.items():
        if logger_name in IGNORABLE_LOGGERS or not isinstance(logger_obj, logging.PlaceHolder):
            continue
        if is_internal_logger(logger_name, str(project_root)):
            continue
        print(f"Found logger: {logger_name}")
        return logging.getLogger(logger_name)
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler("output.txt")
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)
    return log
