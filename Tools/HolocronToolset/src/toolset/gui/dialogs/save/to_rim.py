from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from qtpy.QtWidgets import QDialog

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget


class RimSaveOption(IntEnum):
    Nothing = 0
    MOD = 1
    Override = 2


class RimSaveDialog(QDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        from toolset.uic.pyqt5.dialogs import save_in_rim  # pylint: disable=C0415  # noqa: PLC0415

        self.ui = save_in_rim.Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.cancelButton.clicked.connect(self.reject)
        self.ui.modSaveButton.clicked.connect(self.saveAsMod)
        self.ui.overrideSaveButton.clicked.connect(self.saveAsOverride)

        self.option: RimSaveOption = RimSaveOption.Nothing

    def saveAsMod(self):
        self.option = RimSaveOption.MOD
        self.accept()

    def saveAsOverride(self):
        self.option = RimSaveOption.Override
        self.accept()
