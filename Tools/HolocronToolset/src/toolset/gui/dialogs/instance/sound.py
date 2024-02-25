from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QDialog

from pykotor.common.misc import ResRef

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget

    from pykotor.resource.generics.git import GITSound


class SoundDialog(QDialog):
    def __init__(self, parent: QWidget, sound: GITSound):
        super().__init__(parent)

        from toolset.uic.dialogs.instance.sound import Ui_Dialog  # pylint: disable=C0415  # noqa: PLC0415

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
