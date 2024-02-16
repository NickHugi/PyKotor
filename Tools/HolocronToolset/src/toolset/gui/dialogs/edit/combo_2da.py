from __future__ import annotations

from PyQt5.QtWidgets import QDialog
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget


class ModdedValueSpinboxDialog(QDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        from toolset.uic.widgets.modded_value_spinbox import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

    def value(self) -> int:
        return self.ui.spinBox.value()

