from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

import qtpy

from qtpy import QtCore
from qtpy.QtWidgets import QDialog

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget


class BifSaveOption(IntEnum):
    Nothing = 0
    MOD = 1
    Override = 2


class BifSaveDialog(QDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint & ~QtCore.Qt.WindowContextHelpButtonHint & ~QtCore.Qt.WindowMinimizeButtonHint)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.dialogs import save_in_bif  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.dialogs import save_in_bif  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.dialogs import save_in_bif  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.dialogs import save_in_bif  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

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
