from __future__ import annotations

from typing import Any

import qtpy

from qtpy.QtCore import QSettings

from utility.ui_libraries.qt.widgets.itemviews.treeview import RobustTreeView as _RobustTreeView

# For backwards compatibility.
RobustTreeView = _RobustTreeView



class TreeSettings:
    def __init__(self, settings_name: str = "RobustTreeView"):
        self.robust_tree_settings: QSettings = QSettings("HolocronToolsetV3", "RobustTreeView")
        self.settings: QSettings = self.robust_tree_settings if settings_name == "RobustTreeView" else QSettings("HolocronToolsetV3", settings_name)

    def get(self, key: str, default: Any) -> Any:
        # sourcery skip: assign-if-exp, reintroduce-else
        if qtpy.API_NAME in ("PyQt5", "PySide2"):
            default_val = self.robust_tree_settings.value(key, default, default.__class__)
            return self.settings.value(
                key,
                default_val,
                default.__class__,
            )
        default_val = self.robust_tree_settings.value(key, default)
        result = self.settings.value(key, default_val)
        if result == "true":
            return True
        if result == "false":
            return False
        return result

    def set(self, key: str, value: Any):
        self.settings.setValue(key, value)

    def textElideMode(self, default: int) -> int:
        return self.get("textElideMode", default)

    def setTextElideMode(self, value: int):
        self.set("textElideMode", value)

    def focusPolicy(self, default: int) -> int:
        return self.get("focusPolicy", default)

    def setFocusPolicy(self, value: int):
        self.set("focusPolicy", value)

    def layoutDirection(self, default: int) -> int:
        return self.get("layoutDirection", default)

    def setLayoutDirection(self, value: int):  # noqa: FBT001
        self.set("layoutDirection", value)

    def verticalScrollMode(self, default: int) -> int:  # noqa: FBT001
        return self.get("verticalScrollMode", default)

    def setVerticalScrollMode(self, value: int):  # noqa: FBT001
        self.set("verticalScrollMode", value)

    def uniformRowHeights(self, default: bool) -> bool:  # noqa: FBT001
        return self.get("uniformRowHeights", default)

    def setUniformRowHeights(self, value: bool):  # noqa: FBT001
        self.set("uniformRowHeights", value)

    def animations(self, default: bool) -> bool:  # noqa: FBT001
        return self.get("animations", default)

    def setAnimations(self, value: bool):  # noqa: FBT001
        self.set("animations", value)

    def autoScroll(self, default: bool) -> bool:  # noqa: FBT001
        return self.get("autoScroll", default)

    def setAutoScroll(self, value: bool):  # noqa: FBT001
        self.set("autoScroll", value)

    def expandsOnDoubleClick(self, default: bool) -> bool:  # noqa: FBT001
        return self.get("expandsOnDoubleClick", default)

    def setExpandsOnDoubleClick(self, value: bool):  # noqa: FBT001
        self.set("expandsOnDoubleClick", value)

    def autoFillBackground(self, default: bool) -> bool:  # noqa: FBT001
        return self.get("autoFillBackground", default)

    def setAutoFillBackground(self, value: bool):  # noqa: FBT001
        self.set("autoFillBackground", value)

    def alternatingRowColors(self, default: bool) -> bool:  # noqa: FBT001
        return self.get("alternatingRowColors", default)

    def setAlternatingRowColors(self, value: bool):  # noqa: FBT001
        self.set("alternatingRowColors", value)

    def indentation(self, default: int) -> int:
        return self.get("indentation", default)

    def setIndentation(self, value: int):
        self.set("indentation", value)

    def fontSize(self, default: int) -> int:
        return self.get("fontSize", default)

    def setFontSize(self, value: int):
        self.set("fontSize", value)
