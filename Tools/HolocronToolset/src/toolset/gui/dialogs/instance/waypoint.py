from __future__ import annotations

import math

from typing import TYPE_CHECKING

import qtpy

from qtpy import QtCore
from qtpy.QtGui import QIcon, QPixmap
from qtpy.QtWidgets import QDialog

from pykotor.common.misc import ResRef

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget

    from pykotor.resource.generics.git import GITWaypoint
    from toolset.data.installation import HTInstallation


class WaypointDialog(QDialog):
    def __init__(self, parent: QWidget, waypoint: GITWaypoint, installation: HTInstallation):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint & ~QtCore.Qt.WindowContextHelpButtonHint & ~QtCore.Qt.WindowMinimizeButtonHint)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.dialogs.instance.waypoint import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.dialogs.instance.waypoint import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.dialogs.instance.waypoint import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.dialogs.instance.waypoint import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.nameEdit.setInstallation(installation)
        self.ui.mapNoteEdit.setInstallation(installation)

        self.setWindowTitle("Edit Waypoint")
        self.setWindowIcon(QIcon(QPixmap(":/images/icons/k1/waypoint.png")))

        self.ui.resrefEdit.setText(str(waypoint.resref))
        self.ui.tagEdit.setText(waypoint.tag)
        self.ui.nameEdit.setLocstring(waypoint.name)
        self.ui.xPosSpin.setValue(waypoint.position.x)
        self.ui.yPosSpin.setValue(waypoint.position.y)
        self.ui.zPosSpin.setValue(waypoint.position.z)
        self.ui.bearingSpin.setValue(math.degrees(waypoint.bearing))

        self.ui.mapNoteEdit.setLocstring(waypoint.map_note)  # FIXME: map_note is typed as Locstring | None
        self.ui.hasMapNoteCheck.setChecked(waypoint.has_map_note)
        self.ui.mapNoteEnableCheck.setChecked(waypoint.map_note_enabled)

        self.waypoint: GITWaypoint = waypoint

    def accept(self):
        super().accept()
        self.waypoint.resref = ResRef(self.ui.resrefEdit.text())
        self.waypoint.tag = self.ui.tagEdit.text()
        self.waypoint.position.x = self.ui.xPosSpin.value()
        self.waypoint.position.y = self.ui.yPosSpin.value()
        self.waypoint.position.z = self.ui.zPosSpin.value()
        self.waypoint.bearing = math.radians(self.ui.bearingSpin.value())
        self.waypoint.map_note_enabled = self.ui.mapNoteEnableCheck.isChecked()
        self.waypoint.has_map_note = self.ui.hasMapNoteCheck.isChecked()
        self.waypoint.map_note = self.ui.mapNoteEdit.locstring()
