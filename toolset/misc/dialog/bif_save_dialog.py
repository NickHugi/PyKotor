from enum import IntEnum

from PyQt5.QtWidgets import QDialog, QWidget


class BifSaveOption(IntEnum):
    Nothing = 0
    MOD = 1
    Override = 2


class BifSaveDialog(QDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        from misc.dialog import ui_bifsavedialog
        self.ui = ui_bifsavedialog.Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.cancelButton.clicked.connect(self.reject)
        self.ui.modSaveButton.clicked.connect(self.saveAsMod)
        self.ui.overrideSaveButton.clicked.connect(self.saveAsOverride)

        self.option: BifSaveOption = BifSaveOption.Nothing

    def saveAsMod(self) -> None:
        self.option = BifSaveOption.MOD
        self.accept()

    def saveAsOverride(self) -> None:
        self.option = BifSaveOption.Override
        self.accept()
