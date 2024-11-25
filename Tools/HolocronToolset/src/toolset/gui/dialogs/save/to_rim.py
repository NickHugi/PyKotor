from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget


class RimSaveOption(IntEnum):
    Nothing = 0
    MOD = 1
    Override = 2


class RimSaveDialog(QDialog):
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
            & ~Qt.WindowType.WindowMinMaxButtonsHint
        )

        from toolset.uic.qtpy.dialogs.save_in_rim import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.cancelButton.clicked.connect(self.reject)
        self.ui.modSaveButton.clicked.connect(self.save_as_mod)
        self.ui.overrideSaveButton.clicked.connect(self.save_as_override)

        self.option: RimSaveOption = RimSaveOption.Nothing

    def save_as_mod(self):
        self.option = RimSaveOption.MOD
        self.accept()

    def save_as_override(self):
        self.option = RimSaveOption.Override
        self.accept()
