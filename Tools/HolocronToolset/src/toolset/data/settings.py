from __future__ import annotations

from json import JSONDecodeError
from typing import Any

import jsonpickle

from PyQt5.QtCore import QSettings, Qt

from utility.error_handling import format_exception_with_variables

# Full mapping of Qt.MouseButton values to integers
mouseButtonMap: dict[Qt.MouseButton, int] = {
    Qt.NoButton: 0,
    Qt.LeftButton: 1,
    Qt.RightButton: 2,
    Qt.MiddleButton: 4,
    Qt.BackButton: 8,
    Qt.ForwardButton: 16,
    Qt.TaskButton: 32,
    Qt.ExtraButton4: 64,
    Qt.ExtraButton5: 128,
    Qt.ExtraButton6: 256,
    Qt.ExtraButton7: 512,
    Qt.ExtraButton8: 1024,
    Qt.ExtraButton9: 2048,
    Qt.ExtraButton10: 4096,
    Qt.ExtraButton11: 8192,
    Qt.ExtraButton12: 16384,
    Qt.ExtraButton13: 32768,
    Qt.ExtraButton14: 65536,
    Qt.ExtraButton15: 131072,
    Qt.ExtraButton16: 262144,
    Qt.ExtraButton17: 524288,
    Qt.ExtraButton18: 1048576,
    Qt.ExtraButton19: 2097152,
    Qt.ExtraButton20: 4194304,
    Qt.ExtraButton21: 8388608,
    Qt.ExtraButton22: 16777216,
    Qt.ExtraButton23: 33554432,
    Qt.ExtraButton24: 67108864,
    # Qt defines up to ExtraButton24. Add more if your version of Qt supports them.
}
mouseButtonMapReverse = {v: k for k, v in mouseButtonMap.items()}


class QtTypeWrapper:
    def __init__(self, value: Any, type_str: str):
        self.value = value
        self.type_str = type_str

    def reconstruct(self):
        if self.type_str == "Qt.Key":
            return Qt.Key(self.value)
        if self.type_str == "Qt.MouseButton":
            return mouseButtonMapReverse[self.value]
        return self.value

class Settings:
    def __init__(self, scope: str):
        self.settings = QSettings("HolocronToolsetBeta", scope)

    @staticmethod
    def addSetting(name: str, default: Any) -> property:  # noqa: C901
        def convert_value(value):
            """Recursively converts values, including Qt.Key and nested structures, for serialization.
            Encapsulates special Qt types in QtTypeWrapper.
            """
            if isinstance(value, Qt.Key):
                return QtTypeWrapper(int(value), "Qt.Key")
            if isinstance(value, Qt.MouseButton):
                return QtTypeWrapper(mouseButtonMap[value], "Qt.MouseButton")
            if isinstance(value, set):
                return {convert_value(item) for item in value}  # type: ignore[reportUnhashable]
            if isinstance(value, tuple):
                return tuple(convert_value(item) for item in value)
            if isinstance(value, list):
                return [convert_value(item) for item in value]
            if isinstance(value, dict):
                return {key: convert_value(val) for key, val in value.items()}
            return value

        def reconstruct_value(value: Any):  # noqa: ANN202
            """Reconstructs the value from the serialized form, handling QtTypeWrapper instances."""
            if isinstance(value, QtTypeWrapper):
                return value.reconstruct()
            if isinstance(value, set):
                return {reconstruct_value(item) for item in value}  # type: ignore[reportUnhashable]
            if isinstance(value, tuple):
                return tuple(reconstruct_value(item) for item in value)
            if isinstance(value, list):
                return [reconstruct_value(item) for item in value]
            if isinstance(value, dict):
                return {key: reconstruct_value(val) for key, val in value.items()}
            return value

        def getter(this: Settings) -> Any:
            l_default = convert_value(default)
            serialized_default = jsonpickle.encode(l_default)
            try:
                raw_value = this.settings.value(name, serialized_default, str)
                value = jsonpickle.decode(raw_value)
                return reconstruct_value(value)
            except JSONDecodeError as e:
                print(f"Exception in settings getter: {e}")
                return this.settings.value(name, l_default, l_default.__class__)

        def setter(this: Settings, value: Any):
            #serialized_value = jsonpickle.encode(value, warn=True)
            this.settings.setValue(name, jsonpickle.encode(convert_value(value)))

        return property(getter, setter)
