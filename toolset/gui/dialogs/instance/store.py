from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QDialog, QWidget

from pykotor.common.misc import ResRef
from pykotor.resource.generics.git import GITStore


class StoreDialog(QDialog):
    def __init__(self, parent: QWidget, store: GITStore):
        super().__init__(parent)

        from toolset.uic.dialogs.instance.store import Ui_Dialog

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowTitle("Edit Store")
        self.setWindowIcon(QIcon(QPixmap(":/images/icons/k1/merchant.png")))

        self.ui.resrefEdit.setText(store.resref.get())
        self.ui.xPosSpin.setValue(store.position.x)
        self.ui.yPosSpin.setValue(store.position.y)
        self.ui.zPosSpin.setValue(store.position.z)

        self.store: GITStore = store

    def accept(self) -> None:
        super().accept()
        self.store.resref = ResRef(self.ui.resrefEdit.text())
        self.store.position.x = self.ui.xPosSpin.value()
        self.store.position.y = self.ui.yPosSpin.value()
        self.store.position.z = self.ui.zPosSpin.value()
