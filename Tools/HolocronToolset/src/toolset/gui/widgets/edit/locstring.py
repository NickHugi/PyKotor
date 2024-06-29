from __future__ import annotations

from typing import TYPE_CHECKING

import qtpy

from qtpy import QtCore
from qtpy.QtWidgets import QAction, QApplication, QWidget

from pykotor.common.language import LocalizedString
from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog
from toolset.gui.widgets.settings.installations import GlobalSettings

if TYPE_CHECKING:
    from toolset.data.installation import HTInstallation


class LocalizedStringLineEdit(QWidget):
    editingFinished: QtCore.Signal = QtCore.Signal()

    def __init__(self, parent: QWidget):
        """Initialize a locstring edit widget.

        Args:
        ----
            parent: QWidget - Parent widget

        Processing Logic:
        ----------------
            - Initialize UI from designer file
            - Set initial locstring to invalid
            - Connect edit button to editLocstring method
            - Connect double click on text to editLocstring.
        """
        super().__init__(parent)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.widgets.locstring_edit import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.widgets.locstring_edit import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.widgets.locstring_edit import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.widgets.locstring_edit import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self._installation: HTInstallation | None = None
        self._locstring: LocalizedString = LocalizedString.from_invalid()

        self.ui.editButton.clicked.connect(self.editLocstring)
        self.ui.locstringText.mouseDoubleClickEvent = lambda a0: self.editLocstring()  # noqa: ARG005

    def setInstallation(self, installation: HTInstallation):
        self._installation = installation

    def showContextMenu(self, pos: QtCore.QPoint):
        menu = self.ui.locstringText.createStandardContextMenu()

        edit_action = QAction("Edit with TLK", self)
        edit_action.triggered.connect(self.editLocstring)
        menu.addAction(edit_action)

        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(self.copyText)
        menu.addAction(copy_action)

        menu.exec_(self.ui.locstringText.mapToGlobal(pos))

    def copyText(self):
        """Copies the current text to the clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.ui.locstringText.text())

    def setLocstring(self, locstring: LocalizedString):
        """Sets the localized string for a UI element.

        Args:
        ----
            locstring: {Localized string object to set}

        Processing Logic:
        ----------------
            - Sets the internal locstring property to the passed in value
            - Checks if the stringref is -1
            - If so, sets the text directly from the string and uses white background
            - If not, looks up the string from the talktable and uses a yellow background
        """
        self._locstring = locstring
        theme = GlobalSettings().selectedTheme
        if locstring.stringref == -1:
            text = str(locstring)
            self.ui.locstringText.setText(text if text != "-1" else "")
            # Check theme condition for setting stylesheet
            if theme in ("Native", "Fusion (Light)"):
                self.ui.locstringText.setStyleSheet(f"{self.ui.locstringText.styleSheet()} QLineEdit {{background-color: white;}}")
            else:
                self.ui.locstringText.setStyleSheet(f"{self.ui.locstringText.styleSheet()} QLineEdit {{background-color: white; color: black;}}")
        else:
            self.ui.locstringText.setText(self._installation.talktable().string(locstring.stringref))
            # Check theme condition for setting stylesheet
            if theme in ("Native", "Fusion (Light)"):
                self.ui.locstringText.setStyleSheet(f"{self.ui.locstringText.styleSheet()} QLineEdit {{background-color: #fffded;}}")
            else:
                self.ui.locstringText.setStyleSheet(f"{self.ui.locstringText.styleSheet()} QLineEdit {{background-color: #fffded; color: black;}}")

    def editLocstring(self):
        dialog = LocalizedStringDialog(self, self._installation, self._locstring)
        if dialog.exec_():
            self.setLocstring(dialog.locstring)
            self.editingFinished.emit()

    def locstring(self) -> LocalizedString:
        return self._locstring
