from __future__ import annotations

from typing import TYPE_CHECKING

import qtpy

from qtpy import QtCore
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog, QListWidgetItem

if TYPE_CHECKING:
    from pykotor.extract.capsule import Capsule
    from pykotor.extract.file import FileResource
    from pykotor.resource.type import ResourceType


class LoadFromModuleDialog(QDialog):
    """LoadFromModuleDialog lets the user select a resource from a ERF or RIM."""

    def __init__(self, capsule: Capsule, supported: list[ResourceType]):
        """Initialize a dialog to load resources from a capsule.

        Args:
        ----
            capsule: Capsule - The capsule to load resources from
            supported: list - Supported resource types

        Processing Logic:
        ----------------
            - Loops through each resource in the capsule
            - Checks if the resource type is supported
            - Adds supported resources to the list widget with the filename
            - Associates the original resource with each list item.
        """
        super().__init__()
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.WindowMinMaxButtonsHint & ~QtCore.Qt.WindowContextHelpButtonHint)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.dialogs.load_from_module import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.dialogs.load_from_module import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.dialogs.load_from_module import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.dialogs.load_from_module import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        for resource in capsule:
            if resource.restype() not in supported:
                continue
            filename = resource.filename()
            item = QListWidgetItem(filename)
            item.setData(Qt.ItemDataRole.UserRole, resource)
            self.ui.resourceList.addItem(item)

    def resname(self) -> str | None:
        currentItem: QListWidgetItem | None = self.ui.resourceList.currentItem()
        if currentItem:
            resource: FileResource = currentItem.data(Qt.ItemDataRole.UserRole)
            if resource:
                return resource.resname()
        return None

    def restype(self) -> ResourceType | None:
        currentItem: QListWidgetItem | None = self.ui.resourceList.currentItem()
        if currentItem:
            resource: FileResource = currentItem.data(Qt.ItemDataRole.UserRole)
            if resource:
                return resource.restype()
        return None

    def data(self) -> bytes | None:
        currentItem: QListWidgetItem | None = self.ui.resourceList.currentItem()
        if currentItem:
            resource: FileResource = currentItem.data(Qt.ItemDataRole.UserRole)
            if resource:
                return resource.data()
        return None
