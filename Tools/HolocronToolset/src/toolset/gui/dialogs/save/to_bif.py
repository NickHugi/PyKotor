from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget


class BifSaveOption(IntEnum):
    Nothing = 0
    MOD = 1
    Override = 2


class BifSaveDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
    ):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Dialog  # pyright: ignore[reportArgumentType]
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowStaysOnTopHint
            & ~Qt.WindowType.WindowContextHelpButtonHint
            & ~Qt.WindowType.WindowMinimizeButtonHint
        )

        from toolset.uic.qtpy.dialogs.save_in_bif import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

        self.ui.cancelButton.clicked.connect(self.reject)
        self.ui.modSaveButton.clicked.connect(self.save_as_mod)
        self.ui.overrideSaveButton.clicked.connect(self.save_as_override)

        self.option: BifSaveOption = BifSaveOption.Nothing

    def save_as_mod(self):
        self.option = BifSaveOption.MOD
        self.accept()

    def save_as_override(self):
        self.option = BifSaveOption.Override
        self.accept()
