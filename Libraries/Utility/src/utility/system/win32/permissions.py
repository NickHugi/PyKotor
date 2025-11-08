from __future__ import annotations

import sys
import traceback

from ctypes import windll


def is_admin() -> bool:
    try:  # sourcery skip: do-not-use-bare-except
        return windll.shell32.IsUserAnAdmin()
    except OSError:  # noqa: E722
        print(f"An error occurred while determining user permissions:\n{traceback.format_exc()}", file=sys.stderr)
        return False
