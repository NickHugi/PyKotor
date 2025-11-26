from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog, QListWidgetItem

if TYPE_CHECKING:
    from pykotor.extract.capsule import Capsule
    from pykotor.extract.file import FileResource
    from pykotor.resource.type import ResourceType


class LoadFromModuleDialog(QDialog):
    """LoadFromModuleDialog lets the user select a resource from a ERF or RIM."""

    def __init__(
        self,
        capsule: Capsule,
        supported: list[ResourceType],
    ):
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
        self.setWindowFlags(
            Qt.WindowType.Dialog  # pyright: ignore[reportArgumentType]
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowMinMaxButtonsHint
            & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        from toolset.uic.qtpy.dialogs.load_from_module import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

        for resource in capsule:
            if resource.restype() not in supported:
                continue
            filename = resource.filename()
            item = QListWidgetItem(filename)
            item.setData(Qt.ItemDataRole.UserRole, resource)
            self.ui.resourceList.addItem(item)

    def resname(self) -> str | None:
        cur_item: QListWidgetItem | None = self.ui.resourceList.currentItem()
        if cur_item:
            resource: FileResource = cur_item.data(Qt.ItemDataRole.UserRole)
            if resource:
                return resource.resname()
        return None

    def restype(self) -> ResourceType | None:
        cur_item: QListWidgetItem | None = self.ui.resourceList.currentItem()
        if cur_item:
            resource: FileResource = cur_item.data(Qt.ItemDataRole.UserRole)
            if resource:
                return resource.restype()
        return None

    def data(self) -> bytes | None:
        cur_item: QListWidgetItem | None = self.ui.resourceList.currentItem()
        if cur_item:
            resource: FileResource = cur_item.data(Qt.ItemDataRole.UserRole)
            if resource:
                return resource.data()
        return None
