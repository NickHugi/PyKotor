from enum import IntEnum

from PyQt5.QtWidgets import QDialog, QWidget


class RimSaveOption(IntEnum):
    Nothing = 0
    MOD = 1
    Override = 2


class RimSaveDialog(QDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        from toolset.uic.dialogs import save_in_rim

        self.ui = save_in_rim.Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.cancelButton.clicked.connect(self.reject)
        self.ui.modSaveButton.clicked.connect(self.saveAsMod)
        self.ui.overrideSaveButton.clicked.connect(self.saveAsOverride)

        self.option: RimSaveOption = RimSaveOption.Nothing

    def saveAsMod(self) -> None:
        self.option = RimSaveOption.MOD
        self.accept()

    def saveAsOverride(self) -> None:
        self.option = RimSaveOption.Override
        self.accept()
