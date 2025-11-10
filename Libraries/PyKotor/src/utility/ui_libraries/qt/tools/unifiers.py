from __future__ import annotations

from typing import Any

import qtpy


def sip_enum_to_int(obj: Any) -> int:
    # First check if it's already an int
    if isinstance(obj, int):
        return obj
    # Check if it has a value attribute (Python Enum or Qt6 enum)
    if hasattr(obj, "value"):
        return sip_enum_to_int(obj.value)
    # For Qt5 SIP enums, try to convert directly
    if qtpy.QT5:
        return int(obj)
    # Last resort: try to convert to int
    return int(obj)
