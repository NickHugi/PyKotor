from __future__ import annotations

from pykotor.common.misc import ResRef
from pykotor.resource.generics.git import GITSound
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QDialog, QWidget


class SoundDialog(QDialog):
    def __init__(self, parent: QWidget, sound: GITSound):
        super().__init__(parent)

        from toolset.uic.dialogs.instance.sound import Ui_Dialog

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowTitle("Edit Sound")
        self.setWindowIcon(QIcon(QPixmap(":/images/icons/k1/sound.png")))

        self.ui.resrefEdit.setText(sound.resref.get())
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
