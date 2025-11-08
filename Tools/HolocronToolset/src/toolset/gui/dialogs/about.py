from __future__ import annotations

from typing import TYPE_CHECKING

import qtpy

from qtpy import QtCore
from qtpy.QtWidgets import QDialog

from toolset.config import LOCAL_PROGRAM_INFO

if TYPE_CHECKING:
    from qtpy.QtGui import QShowEvent
    from qtpy.QtWidgets import QWidget


class About(QDialog):
    def __init__(self, parent: QWidget):
        """Initializes the About dialog box.

        Args:
        ----
            parent: The parent QWidget.

        Processing Logic:
        ----------------
            - Sets up the UI from the about.py UI file
            - Connects the closeButton clicked signal to close the dialog
            - Replaces the version placeholder in the about text with the actual version.
        """
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint & ~QtCore.Qt.WindowContextHelpButtonHint & ~QtCore.Qt.WindowMinMaxButtonsHint)


        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.dialogs import about  # pylint: disable=C0415  # noqa: PLC0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.dialogs import about  # pylint: disable=C0415  # noqa: PLC0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.dialogs import about  # pylint: disable=C0415  # noqa: PLC0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.dialogs import about  # pylint: disable=C0415  # noqa: PLC0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = about.Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.closeButton.clicked.connect(self.close)

        self.ui.aboutLabel.setText(self.ui.aboutLabel.text().replace("X.X.X", LOCAL_PROGRAM_INFO["currentVersion"]))

    def showEvent(self, event: QShowEvent):
        self.setFixedSize(self.size())
