from __future__ import annotations

from typing import TYPE_CHECKING

import qtpy

from qtpy import QtCore
from qtpy.QtGui import QIcon, QPixmap
from qtpy.QtWidgets import QDialog

from pykotor.common.misc import ResRef

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget

    from pykotor.resource.generics.git import GITSound


class SoundDialog(QDialog):
    def __init__(self, parent: QWidget, sound: GITSound):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint & ~QtCore.Qt.WindowContextHelpButtonHint & ~QtCore.Qt.WindowMinimizeButtonHint)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.dialogs.instance.sound import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.dialogs.instance.sound import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.dialogs.instance.sound import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.dialogs.instance.sound import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowTitle("Edit Sound")
        self.setWindowIcon(QIcon(QPixmap(":/images/icons/k1/sound.png")))

        self.ui.resrefEdit.setText(str(sound.resref))
        self.ui.xPosSpin.setValue(sound.position.x)
        self.ui.yPosSpin.setValue(sound.position.y)
        self.ui.zPosSpin.setValue(sound.position.z)

        self.sound: GITSound = sound

    def accept(self):
        super().accept()
        self.sound.resref = ResRef(self.ui.resrefEdit.text())
        self.sound.position.x = self.ui.xPosSpin.value()
        self.sound.position.y = self.ui.yPosSpin.value()
        self.sound.position.z = self.ui.zPosSpin.value()
