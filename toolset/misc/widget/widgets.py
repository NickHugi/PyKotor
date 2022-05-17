from typing import Optional

from PyQt5 import QtCore
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QColor, QPixmap, QImage
from PyQt5.QtWidgets import QWidget, QColorDialog, QComboBox, QMenu, QDialog
from pykotor.common.language import LocalizedString
from pykotor.common.misc import Color

from data.installation import HTInstallation
from editors.editor import LocalizedStringDialog


class LocalizedStringLineEdit(QWidget):
    editingFinished = QtCore.pyqtSignal()

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        from misc.widget import ui_locstringlineedit
        self.ui = ui_locstringlineedit.Ui_Form()
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


class ColorEdit(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        from misc.widget import ui_coloredit
        self.ui = ui_coloredit.Ui_Form()
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


class ComboBox2DA(QComboBox):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.onContextMenu)

    def addItem(self, text: str, row: int = None) -> None:
        """
        Adds the 2DA row into the combobox. If the row index is not specified, then the value will be set to the number
        of items in the combobox.

        Args:
            text: Text to display.
            row: The row index into the 2DA table.
        """
        if row is None:
            row = self.count()
        super().addItem(text, row)

    def setCurrentIndex(self, rowIn2DA: int) -> None:
        """
        Selects the item with the specified row index: This is NOT the index into the combobox like it would be with a
        normal QCombobox. If the index cannot be found, it will create an item with the matching index.

        Args:
            rowIn2DA: The row index to select.
        """
        index = None
        for i in range(self.count()):
            if self.itemData(i) == rowIn2DA:
                index = i

        if index is None:
            self.addItem("[Modded Entry #{}]".format(rowIn2DA), rowIn2DA)
            index = self.count() - 1

        super().setCurrentIndex(index)

    def currentIndex(self) -> int:
        """
        Returns the row index from the currently selected item.

        Returns:
            Row index into the 2DA file.
        """
        return self.currentData()

    def onContextMenu(self, point: QPoint) -> None:
        menu = QMenu(self)
        menu.addAction("Set Modded Value").triggered.connect(self.openModdedValueDialog)
        menu.popup(self.mapToGlobal(point))

    def openModdedValueDialog(self) -> None:
        """
        Opens a dialog where the player can manually set the index into the 2DA file.
        """
        dialog = ModdedValueSpinboxDialog(self)
        if dialog.exec_():
            self.setCurrentIndex(dialog.value())


class ModdedValueSpinboxDialog(QDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        from misc.widget import modded_value_spinbox_ui
        self.ui = modded_value_spinbox_ui.Ui_Dialog()
        self.ui.setupUi(self)

    def value(self) -> int:
        return self.ui.spinBox.value()

