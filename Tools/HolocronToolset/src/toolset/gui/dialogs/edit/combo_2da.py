from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtWidgets import QDialog

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget


class ModdedValueSpinboxDialog(QDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        from toolset.uic.pyqt5.widgets.modded_value_spinbox import Ui_Dialog  # pylint: disable=C0415  # noqa: PLC0415
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

    def value(self) -> int:
        return self.ui.spinBox.value()

