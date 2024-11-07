from __future__ import annotations

from typing import Any

import qtpy

from qtpy.QtCore import QSettings


class DLGSettings:
    def __init__(
        self,
        settings_name: str = "RobustTreeView",
    ):
        self.settings: QSettings = QSettings("HolocronToolsetV3", settings_name)

    def get(
        self,
        key: str,
        default: Any,
    ) -> Any:
        # sourcery skip: assign-if-exp, reintroduce-else
        if qtpy.QT5:
            result = self.settings.value(key, default, default.__class__)
        else:
            result = self.settings.value(key, default)
        if result == "true":
            return True
        if result == "false":
            return False
        return result

    def set(
        self,
        key: str,
        value: Any,
    ):
        self.settings.setValue(key, value)

    def tsl_widget_handling(
        self,
        default: str,
    ) -> str:
        return self.get("tsl_widget_handling", default)

    def set_tsl_widget_handling(
        self,
        value: str,
    ):
        self.set("tsl_widget_handling", value)
