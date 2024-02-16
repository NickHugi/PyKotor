from __future__ import annotations

from enum import IntEnum

from PyQt5.QtWidgets import QDialog
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget


class BifSaveOption(IntEnum):
    Nothing = 0
    MOD = 1
    Override = 2


class BifSaveDialog(QDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        from toolset.uic.dialogs import save_in_bif

        self.ui = save_in_bif.Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.cancelButton.clicked.connect(self.reject)
        self.ui.modSaveButton.clicked.connect(self.saveAsMod)
        self.ui.overrideSaveButton.clicked.connect(self.saveAsOverride)

        self.option: BifSaveOption = BifSaveOption.Nothing

    def saveAsMod(self):
        self.option = BifSaveOption.MOD
        self.accept()

    def saveAsOverride(self):
        self.option = BifSaveOption.Override
        self.accept()
