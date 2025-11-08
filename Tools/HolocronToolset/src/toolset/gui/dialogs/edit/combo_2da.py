from __future__ import annotations

from typing import TYPE_CHECKING

import qtpy

from qtpy import QtCore
from qtpy.QtWidgets import QDialog

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget


class ModdedValueSpinboxDialog(QDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint & ~QtCore.Qt.WindowContextHelpButtonHint & ~QtCore.Qt.WindowMinMaxButtonsHint)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.widgets.modded_value_spinbox import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.widgets.modded_value_spinbox import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.widgets.modded_value_spinbox import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.widgets.modded_value_spinbox import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

    def value(self) -> int:
        return self.ui.spinBox.value()
