from __future__ import annotations

import os
import sys

from typing import Any


def sip_enum_to_int(obj: Any) -> int:
    import qtpy
    if isinstance(obj, int):
        return obj
    if qtpy.QT5:
        return int(obj.value) if hasattr(obj, "value") else int(obj)
    nxt_obj = obj.value
    if hasattr(nxt_obj, "value"):
        return int(nxt_obj.value)
    return int(nxt_obj)


if __name__ == "__main__":
    api_name = "PySide6"
    os.environ["QT_API"] = api_name
    import qtpy
    if api_name != qtpy.API_NAME:
        print(f"Failed to set API to {api_name}")
        sys.exit(1)
    print(f"Testing with API: {api_name}")
    from qtpy.QtWidgets import QApplication
    app = QApplication(sys.argv)

    from qtpy.QtCore import Qt
    from qtpy.QtWidgets import QApplication, QFileDialog
    print(f"Testing enums with API: {qtpy.API_NAME}")
    for enum_group in [
        (QFileDialog.Option.ShowDirsOnly, QFileDialog.Option, 1),
        (QFileDialog.FileMode.ExistingFiles, QFileDialog.FileMode, 3),
        (QFileDialog.DialogLabel.LookIn, QFileDialog.DialogLabel, 0),
        (Qt.Key.Key_Escape, Qt.Key, 16777216),
    ]:
        e1, e2, value = enum_group
        some_enum1 = e1
        e1_int: int | None = sip_enum_to_int(some_enum1)
        assert isinstance(e1_int, int), f"e1_int is not an int was {e1_int!r}"
        some_enum2 = e2(value)
        e2_int: int | None = sip_enum_to_int(some_enum2)
        assert isinstance(e2_int, int), f"e2_int is not an int was {e2_int!r}"
        print(f"e1_int: {e1_int!r}")
        print(f"e2_int: {e2_int!r}")
        assert e1_int == e2_int, f"{e1_int!r} == {e2_int!r}"
        assert e1_int.__class__ == e2_int.__class__, f"{e1_int.__class__!r} == {e2_int.__class__!r}"
    print(f"Finished testing with API: {api_name}")
