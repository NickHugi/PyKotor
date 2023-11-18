import math

from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QDialog, QWidget

from pykotor.common.misc import ResRef
from pykotor.resource.generics.git import GITWaypoint
from toolset.data.installation import HTInstallation


class WaypointDialog(QDialog):
    def __init__(self, parent: QWidget, waypoint: GITWaypoint, installation: HTInstallation):
        super().__init__(parent)

        from toolset.uic.dialogs.instance.waypoint import Ui_Dialog

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.nameEdit.setInstallation(installation)
        self.ui.mapNoteEdit.setInstallation(installation)

        self.setWindowTitle("Edit Waypoint")
        self.setWindowIcon(QIcon(QPixmap(":/images/icons/k1/waypoint.png")))

        self.ui.resrefEdit.setText(waypoint.resref.get())
        self.ui.tagEdit.setText(waypoint.tag)
        self.ui.nameEdit.setLocstring(waypoint.name)
        self.ui.xPosSpin.setValue(waypoint.position.x)
        self.ui.yPosSpin.setValue(waypoint.position.y)
        self.ui.zPosSpin.setValue(waypoint.position.z)
        self.ui.bearingSpin.setValue(math.degrees(waypoint.bearing))

        self.ui.mapNoteEdit.setLocstring(waypoint.map_note)
        self.ui.hasMapNoteCheck.setChecked(waypoint.has_map_note)
        self.ui.mapNoteEnableCheck.setChecked(waypoint.map_note_enabled)

        self.waypoint: GITWaypoint = waypoint

    def accept(self) -> None:
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
