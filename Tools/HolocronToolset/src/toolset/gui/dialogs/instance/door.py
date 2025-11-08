from __future__ import annotations

import math

from typing import TYPE_CHECKING

import qtpy

from qtpy import QtCore
from qtpy.QtGui import QColor, QIcon, QImage, QPixmap
from qtpy.QtWidgets import QColorDialog, QDialog

from pykotor.common.misc import Color, ResRef
from pykotor.resource.generics.git import GITModuleLink

if TYPE_CHECKING:
    from qtpy.QtWidgets import QLabel, QWidget

    from pykotor.resource.generics.git import GITDoor
    from toolset.data.installation import HTInstallation
    from toolset.gui.widgets.long_spinbox import LongSpinBox


class DoorDialog(QDialog):
    def __init__(self, parent: QWidget, door: GITDoor, installation: HTInstallation):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint & ~QtCore.Qt.WindowContextHelpButtonHint & ~QtCore.Qt.WindowMinimizeButtonHint)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.dialogs.instance.door import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.dialogs.instance.door import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.dialogs.instance.door import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.dialogs.instance.door import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowTitle("Edit Door")
        self.setWindowIcon(QIcon(QPixmap(":/images/icons/k1/door.png")))

        self.ui.transNameEdit.setInstallation(installation)

        self.ui.colorButton.clicked.connect(lambda: self.changeColor(self.ui.colorSpin))
        self.ui.colorSpin.valueChanged.connect(lambda value: self.redoColorImage(value, self.ui.color))
        self.ui.noTransCheck.toggled.connect(self.doorCheckboxesChanged)
        self.ui.toDoorCheck.toggled.connect(self.doorCheckboxesChanged)
        self.ui.toWaypointCheck.toggled.connect(self.doorCheckboxesChanged)

        self.ui.resrefEdit.setText(str(door.resref))
        self.ui.tagEdit.setText(door.tag)
        self.ui.xPosSpin.setValue(door.position.x)
        self.ui.yPosSpin.setValue(door.position.y)
        self.ui.zPosSpin.setValue(door.position.z)
        self.ui.bearingSpin.setValue(math.degrees(door.bearing))
        self.ui.colorSpin.setValue(0 if door.tweak_color is None else door.tweak_color.rgb_integer())
        self.ui.linkToTagEdit.setText(door.linked_to)
        self.ui.linkToModuleEdit.setText(str(door.linked_to_module))
        self.ui.noTransCheck.setChecked(door.linked_to_flags == 0)
        self.ui.toDoorCheck.setChecked(door.linked_to_flags == 1)
        self.ui.toWaypointCheck.setChecked(door.linked_to_flags == 2)
        self.ui.transNameEdit.setLocstring(door.transition_destination)

        self.door: GITDoor = door

    def accept(self):
        super().accept()
        self.door.resref = ResRef(self.ui.resrefEdit.text())
        self.door.tag = self.ui.tagEdit.text()
        self.door.position.x = self.ui.xPosSpin.value()
        self.door.position.y = self.ui.yPosSpin.value()
        self.door.position.z = self.ui.zPosSpin.value()
        self.door.bearing = math.radians(self.ui.bearingSpin.value())
        self.door.tweak_color = Color.from_rgb_integer(self.ui.colorSpin.value()) if self.ui.colorSpin.value() != 0 else None
        self.door.linked_to = self.ui.linkToTagEdit.text()
        self.door.linked_to_module = ResRef(self.ui.linkToModuleEdit.text())
        self.door.linked_to_flags = GITModuleLink(
            0 if self.ui.noTransCheck.isChecked() else 1 if self.ui.toDoorCheck.isChecked() else 2,
        )
        self.door.transition_destination = self.ui.transNameEdit.locstring()

    def doorCheckboxesChanged(self, state: bool):  # noqa: FBT001
        self.ui.linkToTagEdit.setEnabled(state)
        self.ui.linkToModuleEdit.setEnabled(state)
        self.ui.transNameEdit.setEnabled(state)

    def changeColor(self, colorSpin: LongSpinBox):
        qcolor = QColorDialog.getColor(QColor(colorSpin.value()))
        color = Color.from_rgb_integer(qcolor.rgb())
        colorSpin.setValue(color.rgb_integer())

    def redoColorImage(self, value: int, colorLabel: QLabel):
        color = Color.from_bgr_integer(value)
        r, g, b = int(color.r * 255), int(color.g * 255), int(color.b * 255)
        data = bytes([r, g, b] * 16 * 16)
        pixmap = QPixmap.fromImage(QImage(data, 16, 16, QImage.Format_RGB888))
        colorLabel.setPixmap(pixmap)
