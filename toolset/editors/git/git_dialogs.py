from PyQt5.QtGui import QColor, QPixmap, QImage, QIcon
from PyQt5.QtWidgets import QDialog, QWidget, QColorDialog, QLabel
from pykotor.common.geometry import Vector3
from pykotor.common.misc import Color, ResRef
from pykotor.resource.generics.git import GITCreature, GITPlaceable, GITDoor, GITEncounter, GITTrigger, GITSound, \
    GITStore, GITWaypoint, GITCamera, GITInstance

from editors.git import ui_instance1_dialog, ui_instance2_dialog, ui_instance4_dialog, ui_instance3_dialog
from misc.longspinbox import LongSpinBox


def openInstanceDialog(parent: QWidget, instance: GITInstance):
    dialog = QDialog()

    if isinstance(instance, GITCreature):
        dialog = CreatureDialog(parent, instance)
    elif isinstance(instance, GITDoor):
        dialog = DoorDialog(parent, instance)
    elif isinstance(instance, GITPlaceable):
        dialog = PlaceableDialog(parent, instance)
    elif isinstance(instance, GITTrigger):
        dialog = TriggerDialog(parent, instance)
    elif isinstance(instance, GITCamera):
        dialog = CameraDialog(parent, instance)
    elif isinstance(instance, GITEncounter):
        dialog = EncounterDialog(parent, instance)
    elif isinstance(instance, GITSound):
        dialog = SoundDialog(parent, instance)
    elif isinstance(instance, GITWaypoint):
        dialog = WaypointDialog(parent, instance)
    elif isinstance(instance, GITStore):
        dialog = StoreDialog(parent, instance)

    dialog.exec_()
    return dialog


class CreatureDialog(QDialog):
    def __init__(self, parent: QWidget, creature: GITCreature):
        super().__init__(parent)

        self.ui = ui_instance1_dialog.Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowTitle("Edit Creature")
        self.setWindowIcon(QIcon(QPixmap(":/images/icons/k1/creature.png")))

        self.ui.resrefEdit.setText(creature.resref.get())
        self.ui.xPosSpin.setValue(creature.position.x)
        self.ui.yPosSpin.setValue(creature.position.y)
        self.ui.zPosSpin.setValue(creature.position.y)
        self.ui.bearingSpin.setValue(creature.bearing)

        self.creature: GITCreature = creature

    def accept(self) -> None:
        super().accept()
        self.creature.resref = ResRef(self.ui.resrefEdit.text())
        self.creature.position.x = self.ui.xPosSpin.value()
        self.creature.position.y = self.ui.yPosSpin.value()
        self.creature.position.z = self.ui.zPosSpin.value()
        self.creature.bearing = self.ui.bearingSpin.value()


class PlaceableDialog(QDialog):
    def __init__(self, parent: QWidget, placeable: GITPlaceable):
        super().__init__(parent)

        self.ui = ui_instance2_dialog.Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowTitle("Edit Placeable")
        self.setWindowIcon(QIcon(QPixmap(":/images/icons/k1/placeable.png")))

        self.ui.colorButton.clicked.connect(lambda: self.changeColor(self.ui.colorSpin))
        self.ui.colorSpin.valueChanged.connect(lambda value: self.redoColorImage(value, self.ui.color))

        self.ui.resrefEdit.setText(placeable.resref.get())
        self.ui.xPosSpin.setValue(placeable.position.x)
        self.ui.yPosSpin.setValue(placeable.position.y)
        self.ui.zPosSpin.setValue(placeable.position.z)
        self.ui.bearingSpin.setValue(placeable.bearing)
        self.ui.colorSpin.setValue(0 if placeable.tweak_color is None else placeable.tweak_color.rgb_integer())

        self.placeable: GITPlaceable = placeable

    def accept(self) -> None:
        super().accept()
        self.placeable.resref = ResRef(self.ui.resrefEdit.text())
        self.placeable.position.x = self.ui.xPosSpin.value()
        self.placeable.position.y = self.ui.yPosSpin.value()
        self.placeable.position.z = self.ui.zPosSpin.value()
        self.placeable.bearing = self.ui.bearingSpin.value()
        self.door.tweak_color = Color.from_rgb_integer(self.ui.colorSpin.value()) if self.ui.colorSpin.value() != 0 else None

    def changeColor(self, colorSpin: LongSpinBox) -> None:
        qcolor = QColorDialog.getColor(QColor(colorSpin.value()))
        color = Color.from_rgb_integer(qcolor.rgb())
        colorSpin.setValue(color.rgb_integer())

    def redoColorImage(self, value: int, colorLabel: QLabel) -> None:
        color = Color.from_bgr_integer(value)
        r, g, b = int(color.r * 255), int(color.g * 255), int(color.b * 255)
        data = bytes([r, g, b] * 16 * 16)
        pixmap = QPixmap.fromImage(QImage(data, 16, 16, QImage.Format_RGB888))
        colorLabel.setPixmap(pixmap)


class DoorDialog(QDialog):
    def __init__(self, parent: QWidget, door: GITDoor):
        super().__init__(parent)

        self.ui = ui_instance2_dialog.Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowTitle("Edit Door")
        self.setWindowIcon(QIcon(QPixmap(":/images/icons/k1/door.png")))

        self.ui.colorButton.clicked.connect(lambda: self.changeColor(self.ui.colorSpin))
        self.ui.colorSpin.valueChanged.connect(lambda value: self.redoColorImage(value, self.ui.color))

        self.ui.resrefEdit.setText(door.resref.get())
        self.ui.xPosSpin.setValue(door.position.x)
        self.ui.yPosSpin.setValue(door.position.y)
        self.ui.zPosSpin.setValue(door.position.z)
        self.ui.bearingSpin.setValue(door.bearing)
        self.ui.colorSpin.setValue(0 if door.tweak_color is None else door.tweak_color.rgb_integer())

        self.door: GITDoor = door

    def accept(self) -> None:
        super().accept()
        self.door.resref = ResRef(self.ui.resrefEdit.text())
        self.door.position.x = self.ui.xPosSpin.value()
        self.door.position.y = self.ui.yPosSpin.value()
        self.door.position.z = self.ui.zPosSpin.value()
        self.door.bearing = self.ui.bearingSpin.value()
        self.door.tweak_color = Color.from_rgb_integer(self.ui.colorSpin.value()) if self.ui.colorSpin.value() != 0 else None

    def changeColor(self, colorSpin: LongSpinBox) -> None:
        qcolor = QColorDialog.getColor(QColor(colorSpin.value()))
        color = Color.from_rgb_integer(qcolor.rgb())
        colorSpin.setValue(color.rgb_integer())

    def redoColorImage(self, value: int, colorLabel: QLabel) -> None:
        color = Color.from_bgr_integer(value)
        r, g, b = int(color.r * 255), int(color.g * 255), int(color.b * 255)
        data = bytes([r, g, b] * 16 * 16)
        pixmap = QPixmap.fromImage(QImage(data, 16, 16, QImage.Format_RGB888))
        colorLabel.setPixmap(pixmap)


class EncounterDialog(QDialog):
    def __init__(self, parent: QWidget, encounter: GITEncounter):
        super().__init__(parent)

        self.ui = ui_instance4_dialog.Ui_Dialog()
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


class TriggerDialog(QDialog):
    def __init__(self, parent: QWidget, trigger: GITTrigger):
        super().__init__(parent)

        self.ui = ui_instance4_dialog.Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowTitle("Edit Trigger")
        self.setWindowIcon(QIcon(QPixmap(":/images/icons/k1/trigger.png")))

        self.ui.resrefEdit.setText(trigger.resref.get())
        self.ui.xPosSpin.setValue(trigger.position.x)
        self.ui.yPosSpin.setValue(trigger.position.y)
        self.ui.zPosSpin.setValue(trigger.position.z)

        self.trigger: GITTrigger = trigger

    def accept(self) -> None:
        super().accept()
        self.trigger.resref = ResRef(self.ui.resrefEdit.text())
        self.trigger.position.x = self.ui.xPosSpin.value()
        self.trigger.position.y = self.ui.yPosSpin.value()
        self.trigger.position.z = self.ui.zPosSpin.value()


class SoundDialog(QDialog):
    def __init__(self, parent: QWidget, sound: GITSound):
        super().__init__(parent)

        self.ui = ui_instance4_dialog.Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowTitle("Edit Sound")
        self.setWindowIcon(QIcon(QPixmap(":/images/icons/k1/sound.png")))

        self.ui.resrefEdit.setText(sound.resref.get())
        self.ui.xPosSpin.setValue(sound.position.x)
        self.ui.yPosSpin.setValue(sound.position.y)
        self.ui.zPosSpin.setValue(sound.position.z)

        self.sound: GITSound = sound

    def accept(self) -> None:
        super().accept()
        self.sound.resref = ResRef(self.ui.resrefEdit.text())
        self.sound.position.x = self.ui.xPosSpin.value()
        self.sound.position.y = self.ui.yPosSpin.value()
        self.sound.position.z = self.ui.zPosSpin.value()


class StoreDialog(QDialog):
    def __init__(self, parent: QWidget, store: GITStore):
        super().__init__(parent)

        self.ui = ui_instance4_dialog.Ui_Dialog()
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


class WaypointDialog(QDialog):
    def __init__(self, parent: QWidget, waypoint: GITWaypoint):
        super().__init__(parent)

        self.ui = ui_instance4_dialog.Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowTitle("Edit Waypoint")
        self.setWindowIcon(QIcon(QPixmap(":/images/icons/k1/waypoint.png")))

        self.ui.resrefEdit.setText(waypoint.resref.get())
        self.ui.xPosSpin.setValue(waypoint.position.x)
        self.ui.yPosSpin.setValue(waypoint.position.y)
        self.ui.zPosSpin.setValue(waypoint.position.z)

        self.waypoint: GITWaypoint = waypoint

    def accept(self) -> None:
        super().accept()
        self.waypoint.resref = ResRef(self.ui.resrefEdit.text())
        self.waypoint.position.x = self.ui.xPosSpin.value()
        self.waypoint.position.y = self.ui.yPosSpin.value()
        self.waypoint.position.z = self.ui.zPosSpin.value()


class CameraDialog(QDialog):
    def __init__(self, parent: QWidget, camera: GITCamera):
        super().__init__(parent)

        self.ui = ui_instance3_dialog.Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowTitle("Edit Camera")
        self.setWindowIcon(QIcon(QPixmap(":/images/icons/k1/camera.png")))

        self.ui.xPosSpin.setValue(camera.position.x)
        self.ui.yPosSpin.setValue(camera.position.y)
        self.ui.zPosSpin.setValue(camera.position.z)
        self.ui.xOrientSpin.setValue(camera.orientation.x)
        self.ui.yOrientSpin.setValue(camera.orientation.y)
        self.ui.zOrientSpin.setValue(camera.orientation.z)
        self.ui.wOrientSpin.setValue(camera.orientation.w)
        self.ui.cameraIdSpin.setValue(camera.camera_id)
        self.ui.fovSpin.setValue(camera.fov)
        self.ui.heightSpin.setValue(camera.height)
        self.ui.micRangeSpin.setValue(camera.mic_range)
        self.ui.pitchSpin.setValue(camera.pitch)

        self.camera: GITCamera = camera

    def accept(self) -> None:
        super().accept()
        self.camera.position = Vector3(self.ui.xPosSpin.value(), self.ui.xPosSpin.value(), self.ui.zPosSpin.value())
        self.camera.orientation.x = self.ui.xOrientSpin.value()
        self.camera.orientation.y = self.ui.yOrientSpin.value()
        self.camera.orientation.z = self.ui.wOrientSpin.value()
        self.camera.orientation.w = self.ui.zOrientSpin.value()
        self.camera.camera_id = self.ui.cameraIdSpin.value()
        self.camera.fov = self.ui.fovSpin.value()
        self.camera.height = self.ui.heightSpin.value()
        self.camera.mic_range = self.ui.micRangeSpin.value()
        self.camera.pitch = self.ui.pitchSpin.value()
