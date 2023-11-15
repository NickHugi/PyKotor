
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QDialog, QWidget

from pykotor.common.misc import ResRef
from pykotor.resource.generics.git import GITEncounter


class EncounterDialog(QDialog):
    def __init__(self, parent: QWidget, encounter: GITEncounter):
        super().__init__(parent)

        from toolset.uic.dialogs.instance.encounter import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowTitle("Edit Encounter")
        self.setWindowIcon(QIcon(QPixmap(":/images/icons/k1/encounter.png")))

        self.ui.resrefEdit.setText(encounter.resref.get())
        self.ui.xPosSpin.setValue(encounter.position.x)
        self.ui.yPosSpin.setValue(encounter.position.y)
        self.ui.zPosSpin.setValue(encounter.position.z)

        self.encounter: GITEncounter = encounter

    def accept(self) -> None:
        super().accept()
        self.encounter.resref = ResRef(self.ui.resrefEdit.text())
        self.encounter.position.x = self.ui.xPosSpin.value()
        self.encounter.position.y = self.ui.yPosSpin.value()
        self.encounter.position.z = self.ui.zPosSpin.value()
