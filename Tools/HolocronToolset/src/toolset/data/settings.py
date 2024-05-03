from __future__ import annotations

import sys

from json import JSONDecodeError
from typing import Any

import jsonpickle

from qtpy.QtCore import QSettings, Qt

# Full mapping of Qt.MouseButton values to integers
mouseButtonMap: dict[Qt.MouseButton, int] = {
    Qt.MouseButton.NoButton: 0,
    Qt.MouseButton.LeftButton: 1,
    Qt.MouseButton.RightButton: 2,
    Qt.MouseButton.MiddleButton: 4,
    Qt.MouseButton.BackButton: 8,
    Qt.MouseButton.ForwardButton: 16,
    Qt.MouseButton.TaskButton: 32,
    Qt.MouseButton.ExtraButton4: 64,
    Qt.MouseButton.ExtraButton5: 128,
    Qt.MouseButton.ExtraButton6: 256,
    Qt.MouseButton.ExtraButton7: 512,
    Qt.MouseButton.ExtraButton8: 1024,
    Qt.MouseButton.ExtraButton9: 2048,
    Qt.MouseButton.ExtraButton10: 4096,
    Qt.MouseButton.ExtraButton11: 8192,
    Qt.MouseButton.ExtraButton12: 16384,
    Qt.MouseButton.ExtraButton13: 32768,
    Qt.MouseButton.ExtraButton14: 65536,
    Qt.MouseButton.ExtraButton15: 131072,
    Qt.MouseButton.ExtraButton16: 262144,
    Qt.MouseButton.ExtraButton17: 524288,
    Qt.MouseButton.ExtraButton18: 1048576,
    Qt.MouseButton.ExtraButton19: 2097152,
    Qt.MouseButton.ExtraButton20: 4194304,
    Qt.MouseButton.ExtraButton21: 8388608,
    Qt.MouseButton.ExtraButton22: 16777216,
    Qt.MouseButton.ExtraButton23: 33554432,
    Qt.MouseButton.ExtraButton24: 67108864,
    # Qt defines up to ExtraButton24. Add more if your version of Qt supports them.
}
mouseButtonMapReverse = {v: k for k, v in mouseButtonMap.items()}


class QtTypeWrapper:
    def __init__(self, value: Any, type_str: str):
        self.value: Any = value
        self.type_str: str = type_str

    def reconstruct(self):
        if self.type_str == "Qt.Key":
            return Qt.Key(self.value)
        if self.type_str == "Qt.MouseButton":
            return mouseButtonMapReverse[self.value]
        return self.value

class Settings:
    def __init__(self, scope: str):
        self.settings = QSettings("HolocronToolset", scope)

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
                value = jsonpickle.decode(raw_value)  # noqa: S301
                return reconstruct_value(value)
            except (TypeError, JSONDecodeError) as e:
                print(f"Exception in settings getter while acquiring setting '{name}' with default of {default} ({l_default}): {e}", file=sys.stderr)
                this.settings.setValue(name, serialized_default)
                return this.settings.value(name, serialized_default, serialized_default.__class__)

        def setter(this: Settings, value: Any):
            this.settings.setValue(name, jsonpickle.encode(convert_value(value)))

        return property(getter, setter)
