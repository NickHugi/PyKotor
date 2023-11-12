import sys

if sys.version_info < (3, 8):  # noqa: UP036
    msg = "pykotor requires Python 3.8 or higher. Please upgrade your Python version."
    raise ImportError(msg)
