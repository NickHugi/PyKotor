from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtCore import QVariant, Qt
from PyQt5.QtWidgets import QDialog, QListWidgetItem

if TYPE_CHECKING:
    from pykotor.extract.capsule import Capsule
    from pykotor.extract.file import FileResource
    from pykotor.resource.type import ResourceType


class LoadFromModuleDialog(QDialog):
    """LoadFromModuleDialog lets the user select a resource from a ERF or RIM."""

    def __init__(self, capsule: Capsule, supported):
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

        from toolset.uic.dialogs.load_from_module import Ui_Dialog

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        for resource in capsule:
            if resource.restype() not in supported:
                continue
            filename = resource.filename()
            item = QListWidgetItem(filename)
            item.setData(Qt.UserRole, QVariant(resource))
            self.ui.resourceList.addItem(item)

    def resname(self) -> str | None:
        currentItem: QListWidgetItem | None = self.ui.resourceList.currentItem()
        if currentItem:
            resource: FileResource = currentItem.data(Qt.UserRole)
            if resource:
                return resource.resname()
        return None

    def restype(self) -> ResourceType | None:
        currentItem: QListWidgetItem | None = self.ui.resourceList.currentItem()
        if currentItem:
            resource: FileResource = currentItem.data(Qt.UserRole)
            if resource:
                return resource.restype()
        return None

    def data(self) -> bytes | None:
        currentItem: QListWidgetItem | None = self.ui.resourceList.currentItem()
        if currentItem:
            resource: FileResource = currentItem.data(Qt.UserRole)
            if resource:
                return resource.data()
        return None
