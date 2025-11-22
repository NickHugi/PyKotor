from __future__ import annotations

from typing import Any

import qtpy

from toolset.gui.common.widgets.tree import TreeSettings


class DLGSettings(TreeSettings):
    def __init__(
        self,
        settings_name: str = "DLGEditor",
    ):
        super().__init__(settings_name)

    def get(
        self,
        key: str,
        default: Any,
    ) -> Any:
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

    def tsl_widget_preference(
        self,
        default: str,
    ) -> str:
        return self.get("tsl_widget_preference", default)

    def set_tsl_widget_preference(
        self,
        value: str,
    ):
        self.set("tsl_widget_preference", value)

    def show_verbose_hover_hints(self, default: bool) -> bool:
        return self.get("show_verbose_hover_hints", default)

    def set_show_verbose_hover_hints(self, value: bool):
        self.set("show_verbose_hover_hints", value)
