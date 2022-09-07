from typing import Optional

from PyQt5 import QtCore
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QColor, QPixmap, QImage
from PyQt5.QtWidgets import QWidget, QColorDialog, QComboBox, QMenu, QDialog
from pykotor.common.language import LocalizedString
from pykotor.common.misc import Color

from data.installation import HTInstallation
from gui.editor import LocalizedStringDialog


class ModdedValueSpinboxDialog(QDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        from toolset.uic.widgets.modded_value_spinbox import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

    def value(self) -> int:
        return self.ui.spinBox.value()

