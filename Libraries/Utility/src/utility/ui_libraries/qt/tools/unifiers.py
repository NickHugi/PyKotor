from __future__ import annotations

from typing import Any

import qtpy


def sip_enum_to_int(obj: Any) -> int:
    if qtpy.QT5:
        return int(obj)
    if isinstance(obj, int):
        return obj
    if hasattr(obj, "value"):
        return sip_enum_to_int(obj.value)
    return int(obj)
