from __future__ import annotations

from typing import TYPE_CHECKING

import qtpy

from qtpy import QtCore
from qtpy.QtGui import QIcon, QPixmap
from qtpy.QtWidgets import QDialog

from pykotor.common.misc import ResRef

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget

    from pykotor.resource.generics.git import GITStore


class StoreDialog(QDialog):
    def __init__(self, parent: QWidget, store: GITStore):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint & ~QtCore.Qt.WindowContextHelpButtonHint & ~QtCore.Qt.WindowMinimizeButtonHint)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.dialogs.instance.store import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.dialogs.instance.store import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.dialogs.instance.store import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.dialogs.instance.store import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowTitle("Edit Store")
        self.setWindowIcon(QIcon(QPixmap(":/images/icons/k1/merchant.png")))

        self.ui.resrefEdit.setText(str(store.resref))
        self.ui.xPosSpin.setValue(store.position.x)
        self.ui.yPosSpin.setValue(store.position.y)
        self.ui.zPosSpin.setValue(store.position.z)

        self.store: GITStore = store

    def accept(self):
        super().accept()
        self.store.resref = ResRef(self.ui.resrefEdit.text())
        self.store.position.x = self.ui.xPosSpin.value()
        self.store.position.y = self.ui.yPosSpin.value()
        self.store.position.z = self.ui.zPosSpin.value()
