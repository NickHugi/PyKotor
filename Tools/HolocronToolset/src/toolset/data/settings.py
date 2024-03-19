from __future__ import annotations

from json import JSONDecodeError
from typing import Any

import jsonpickle

from qtpy.QtCore import QSettings, Qt


class Settings:
    def __init__(self, scope: str):
        self.settings = QSettings("HolocronToolset", scope)

    @staticmethod
    def addSetting(name: str, default: Any) -> property:
        # sourcery skip: remove-unnecessary-cast
        def convert_value(value):
            """Recursively converts values, including Qt.Key and nested structures, for serialization."""
            if isinstance(value, (Qt.Key, Qt.MouseButton)):
                return int(value)  # Convert Qt.Key to int
            elif isinstance(value, set):
                return {convert_value(item) for item in value}  # Convert each item in a set
            elif isinstance(value, tuple):
                return tuple(convert_value(item) for item in value)  # Convert each item in a tuple
            elif isinstance(value, list):
                return [convert_value(item) for item in value]  # Convert each item in a list
            elif isinstance(value, dict):
                return {key: convert_value(val) for key, val in value.items()}  # Convert each value in a dict
            else:
                return value

        def getter(this: Settings) -> Any:
            l_default = convert_value(default)
            serialized_default = jsonpickle.encode(l_default)
            try:
                return jsonpickle.decode(this.settings.value(name, serialized_default, serialized_default.__class__))  # noqa: S301
            except JSONDecodeError as e:
                return this.settings.value(name, l_default, l_default.__class__)

        def setter(this: Settings, value: Any):
            #serialized_value = jsonpickle.encode(value, warn=True)
            this.settings.setValue(name, jsonpickle.encode(convert_value(value)))

        return property(getter, setter)
