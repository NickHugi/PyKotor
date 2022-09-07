from typing import Optional

from PyQt5 import QtCore
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QColor, QPixmap, QImage
from PyQt5.QtWidgets import QWidget, QColorDialog, QComboBox, QMenu, QDialog
from pykotor.common.language import LocalizedString
from pykotor.common.misc import Color

from data.installation import HTInstallation
from gui.editor import LocalizedStringDialog


class LocalizedStringLineEdit(QWidget):
    editingFinished = QtCore.pyqtSignal()

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        from toolset.uic.widgets.locstring_edit import Ui_Form
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self._installation: Optional[HTInstallation] = None
        self._locstring: LocalizedString = LocalizedString.from_invalid()

        self.ui.editButton.clicked.connect(self.editLocstring)
        self.ui.locstringText.mouseDoubleClickEvent = lambda _: self.editLocstring()

    def setInstallation(self, installation: HTInstallation) -> None:
        self._installation = installation

    def setLocstring(self, locstring: LocalizedString) -> None:
        self._locstring = locstring
        if locstring.stringref == -1:
            text = str(locstring)
            self.ui.locstringText.setText(text if text != "-1" else "")
            self.ui.locstringText.setStyleSheet("QLineEdit {background-color: white;}")
        else:
            self.ui.locstringText.setText(self._installation.talktable().string(locstring.stringref))
            self.ui.locstringText.setStyleSheet("QLineEdit {background-color: #fffded;}")

    def editLocstring(self) -> None:
        dialog = LocalizedStringDialog(self, self._installation, self._locstring)
        if dialog.exec_():
            self.setLocstring(dialog.locstring)
            self.editingFinished.emit()

    def locstring(self) -> LocalizedString:
        return self._locstring