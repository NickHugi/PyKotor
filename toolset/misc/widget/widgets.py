from typing import Optional

from PyQt5.QtGui import QColor, QPixmap, QImage
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QColorDialog, QLabel
from pykotor.common.language import LocalizedString
from pykotor.common.misc import Color

from data.installation import HTInstallation
from editors.editor import LocalizedStringDialog
from misc.longspinbox import LongSpinBox
from misc.widget import locstringlineedit_ui, coloredit_ui


class LocalizedStringLineEdit(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.ui = locstringlineedit_ui.Ui_Form()
        self.ui.setupUi(self)

        self._installation: Optional[HTInstallation] = None
        self._locstring: LocalizedString = LocalizedString.from_invalid()

        self.ui.editButton.clicked.connect(self.editLocstring)
        self.ui.locstringText.mouseDoubleClickEvent = lambda: self.editLocstring()

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

    def locstring(self) -> LocalizedString:
        return self._locstring


class ColorEdit(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.ui = coloredit_ui.Ui_Form()
        self.ui.setupUi(self)

        self._color: Color = Color(255, 255, 255)

        self.ui.editButton.clicked.connect(self.openColorDialog)
        self.ui.colorSpin.valueChanged.connect(self._onColorChange)

    def openColorDialog(self) -> None:
        qcolor = QColorDialog.getColor(QColor(self.ui.colorSpin.value()))
        color = Color(qcolor.red()/255, qcolor.green()/255, qcolor.blue()/255)
        self.ui.colorSpin.setValue(color.rgb_integer())

    def _onColorChange(self, value: int) -> None:
        color = Color.from_bgr_integer(value)
        self._color.r, self._color.g, self._color.b = color.r, color.g, color.b
        r, g, b = int(color.r * 255), int(color.g * 255), int(color.b * 255)
        data = bytes([b, g, r] * 16 * 16)
        pixmap = QPixmap.fromImage(QImage(data, 16, 16, QImage.Format_RGB888))
        self.ui.colorLabel.setPixmap(pixmap)

    def setColor(self, color: Color) -> None:
        self._color: Color = color
        self.ui.colorSpin.setValue(color.rgb_integer())

    def color(self) -> Color:
        return self._color
