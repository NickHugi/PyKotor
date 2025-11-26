from __future__ import annotations

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog

from pykotor.resource.type import ResourceType


class SaveToModuleDialog(QDialog):
    """SaveToModuleDialog lets the user specify a ResRef and a resource type when saving to a module."""

    def __init__(
        self,
        resname: str,
        restype: ResourceType,
        supported: list[ResourceType],
    ):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.Dialog  # pyright: ignore[reportArgumentType]
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowStaysOnTopHint
            & ~Qt.WindowType.WindowContextHelpButtonHint
            & ~Qt.WindowType.WindowMinMaxButtonsHint
        )

        from toolset.uic.qtpy.dialogs.save_to_module import Ui_Dialog

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

        self.ui.resrefEdit.setText(resname)
        self.ui.typeCombo.addItems([restype.extension.upper() for restype in supported])
        self.ui.typeCombo.setCurrentIndex(supported.index(restype))

    def resname(self) -> str:  # resref filename stem
        return self.ui.resrefEdit.text()

    def restype(self) -> ResourceType:
        return ResourceType.from_extension(self.ui.typeCombo.currentText().lower())
