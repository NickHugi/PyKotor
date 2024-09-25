from __future__ import annotations

from typing import Any

import qtpy


def sip_enum_to_int(obj: Any) -> int:
    return int(obj) if qtpy.QT5 else int(obj.value)
