import math
from typing import Optional, Set

from PyQt5 import QtCore
from PyQt5.QtCore import QPoint, QTimer
from PyQt5.QtGui import QPixmap, QIcon, QWheelEvent, QMouseEvent, QKeyEvent
from PyQt5.QtWidgets import QMainWindow, QWidget, QOpenGLWidget, QTreeWidgetItem, QMenu, QAction, QListWidgetItem
from pykotor.common.geometry import Vector3, Vector2
from pykotor.common.module import Module, ModuleResource
from pykotor.common.stream import BinaryWriter
from pykotor.resource.generics.git import GITCreature, GITPlaceable, GITDoor, GITTrigger, GITEncounter, GITWaypoint, \
    GITSound, GITStore, GITCamera, GITInstance
from pykotor.resource.type import ResourceType

from data.installation import HTInstallation
from pykotor.gl.scene import Scene, RenderObject
from tools.module import moduleeditor_ui


class ModuleEditor(QMainWindow):
    def __init__(self, parent: QWidget, installation: HTInstallation, module: Module):
        super().__init__(parent)

        self._installation: HTInstallation = installation
        self._module: Module = module

        self.ui = moduleeditor_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupSignals()

        self.ui.mainRenderer.init(installation, module)

        self.hideCreatures = False
        self.hidePlaceables = False
        self.hideDoors = False
        self.hideTriggers = False
        self.hideEncounters = False
        self.hideWaypoints = False
        self.hideSounds = False
        self.hideStores = False
        self.hideCameras = False

        self.rebuildResourceTree()
        self.rebuildInstanceList()

    def _setupSignals(self) -> None:
        self.ui.resourceTree.customContextMenuRequested.connect(self.onResourceTreeContextMenu)

        self.ui.viewCreatureCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewPlaceableCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewDoorCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewSoundCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewTriggerCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewEncounterCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewWaypointCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewCameraCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewStoreCheck.toggled.connect(self.updateInstanceVisibility)

        self.ui.instanceList.doubleClicked.connect(self.onInstanceListDoubleClicked)

        self.ui.mainRenderer.mousePressed.connect(self.onRendererMousePressed)
        self.ui.mainRenderer.mouseMoved.connect(self.onRendererMouseMoved)
        self.ui.mainRenderer.mouseScrolled.connect(self.onRendererMouseScrolled)
        self.ui.mainRenderer.objectSelected.connect(self.onRendererObjectSelected)

    def rebuildResourceTree(self) -> None:
        self.ui.resourceTree.clear()
        categories = {
            ResourceType.UTC: QTreeWidgetItem(["Creatures"]),
            ResourceType.UTP: QTreeWidgetItem(["Placeables"]),
            ResourceType.UTD: QTreeWidgetItem(["Doors"]),
            ResourceType.UTI: QTreeWidgetItem(["Items"]),
            ResourceType.UTE: QTreeWidgetItem(["Encounters"]),
            ResourceType.UTT: QTreeWidgetItem(["Triggers"]),
            ResourceType.UTW: QTreeWidgetItem(["Waypoints"]),
            ResourceType.UTS: QTreeWidgetItem(["Sounds"]),
            ResourceType.UTM: QTreeWidgetItem(["Merchants"]),
            ResourceType.DLG: QTreeWidgetItem(["Dialogs"]),
            ResourceType.FAC: QTreeWidgetItem(["Factions"]),
            ResourceType.MDL: QTreeWidgetItem(["Models"]),
            ResourceType.TGA: QTreeWidgetItem(["Textures"]),
            ResourceType.NCS: QTreeWidgetItem(["Scripts"]),
            ResourceType.IFO: QTreeWidgetItem(["Module Data"]),
            ResourceType.INVALID: QTreeWidgetItem(["Other"])
        }
        categories[ResourceType.MDX] = categories[ResourceType.MDL]
        categories[ResourceType.WOK] = categories[ResourceType.MDL]
        categories[ResourceType.TPC] = categories[ResourceType.TGA]
        categories[ResourceType.IFO] = categories[ResourceType.IFO]
        categories[ResourceType.ARE] = categories[ResourceType.IFO]
        categories[ResourceType.GIT] = categories[ResourceType.IFO]
        categories[ResourceType.LYT] = categories[ResourceType.IFO]
        categories[ResourceType.VIS] = categories[ResourceType.IFO]
        categories[ResourceType.PTH] = categories[ResourceType.IFO]
        categories[ResourceType.NSS] = categories[ResourceType.NCS]

        for category in categories:
            self.ui.resourceTree.addTopLevelItem(categories[category])

        for resource in self._module.resources.values():
            item = QTreeWidgetItem([resource.resname() + "." + resource.restype().extension])
            item.setData(0, QtCore.Qt.UserRole, resource)
            category = categories[resource.restype()] if resource.restype() in categories else categories[ResourceType.INVALID]
            category.addChild(item)

        self.ui.resourceTree.sortByColumn(0, QtCore.Qt.AscendingOrder)
        self.ui.resourceTree.setSortingEnabled(True)

    def openModuleResource(self, resource: ModuleResource) -> None:
        self.parent().openResourceEditor(resource.active(), resource.resname(), resource.restype(), resource.data())

    def copyResourceToOverride(self, resource: ModuleResource) -> None:
        location = "{}/{}.{}".format(self._installation.override_path(), resource.resname(), resource.restype().extension)
        BinaryWriter.dump(location, resource.data())
        resource.add_locations([location])
        resource.activate(location)

    def onResourceTreeContextMenu(self, point: QPoint) -> None:
        menu = QMenu(self)

        data = self.ui.resourceTree.currentItem().data(0, QtCore.Qt.UserRole)
        if isinstance(data, ModuleResource):
            copyToOverrideAction = QAction("Copy To Override", self)
            copyToOverrideAction.triggered.connect(lambda _, r=data: self.copyResourceToOverride(r))

            menu.addAction("Edit Active File").triggered.connect(lambda _, r=data: self.openModuleResource(r))
            menu.addAction(copyToOverrideAction)
            menu.addSeparator()
            for location in data.locations():
                locationAciton = QAction(location, self)
                locationAciton.triggered.connect(lambda _, l=location: data.activate(l))
                if location == data.active():
                    locationAciton.setEnabled(False)
                if "override" in location.lower():
                    copyToOverrideAction.setEnabled(False)
                menu.addAction(locationAciton)

        menu.exec_(self.ui.resourceTree.mapToGlobal(point))

    def rebuildInstanceList(self) -> None:
        visibleMapping = {
            GITCreature: self.hideCreatures,
            GITPlaceable: self.hidePlaceables,
            GITDoor: self.hideDoors,
            GITTrigger: self.hideTriggers,
            GITEncounter: self.hideEncounters,
            GITWaypoint: self.hideWaypoints,
            GITSound: self.hideSounds,
            GITStore: self.hideStores,
            GITCamera: self.hideCameras,
            GITInstance: False
        }

        iconMapping = {
            GITCreature: QPixmap(":/images/icons/k1/creature.png"),
            GITPlaceable: QPixmap(":/images/icons/k1/placeable.png"),
            GITDoor: QPixmap(":/images/icons/k1/door.png"),
            GITSound: QPixmap(":/images/icons/k1/sound.png"),
            GITTrigger: QPixmap(":/images/icons/k1/trigger.png"),
            GITEncounter: QPixmap(":/images/icons/k1/encounter.png"),
            GITWaypoint: QPixmap(":/images/icons/k1/waypoint.png"),
            GITCamera: QPixmap(":/images/icons/k1/camera.png"),
            GITStore: QPixmap(":/images/icons/k1/merchant.png"),
            GITInstance: QPixmap(32, 32)
        }

        self.ui.instanceList.clear()
        for instance in self._module.git().resource().instances():
            if visibleMapping[type(instance)]:
                continue

            if instance.reference():
                resource = self._module.resource(instance.reference().get(), instance.extension())
                text = resource.localized_name()
                if text is None or text.isspace():
                    text = "[{}]".format(resource.resname())
            else:
                text = "Camera #{}".format(self._module.git().resource().index(instance))

            icon = QIcon(iconMapping[type(instance)])
            item = QListWidgetItem(icon, text)
            item.setToolTip("" if instance.reference() is None else instance.reference().get())
            item.setData(QtCore.Qt.UserRole, instance)
            self.ui.instanceList.addItem(item)

    def selectInstanceItemOnList(self, instance: GITInstance) -> None:
        self.ui.instanceList.clearSelection()
        for i in range(self.ui.instanceList.count()):
            item = self.ui.instanceList.item(i)
            data: GITInstance = item.data(QtCore.Qt.UserRole)
            if data is instance:
                item.setSelected(True)

    def updateInstanceVisibility(self) -> None:
        self.hideCreatures = self.ui.mainRenderer.scene.hide_creatures = not self.ui.viewCreatureCheck.isChecked()
        self.hidePlaceables = self.ui.mainRenderer.scene.hide_placeables = not self.ui.viewPlaceableCheck.isChecked()
        self.hideDoors = self.ui.mainRenderer.scene.hide_doors = not self.ui.viewDoorCheck.isChecked()
        self.hideTriggers = self.ui.mainRenderer.scene.hide_triggers = not self.ui.viewTriggerCheck.isChecked()
        self.hideEncounters = self.ui.mainRenderer.scene.hide_encounters = not self.ui.viewEncounterCheck.isChecked()
        self.hideWaypoints = self.ui.mainRenderer.scene.hide_waypoints = not self.ui.viewWaypointCheck.isChecked()
        self.hideSounds = self.ui.mainRenderer.scene.hide_sounds = not self.ui.viewSoundCheck.isChecked()
        self.hideStores = self.ui.mainRenderer.scene.hide_stores = not self.ui.viewStoreCheck.isChecked()
        self.hideCameras = self.ui.mainRenderer.scene.hide_cameras = not self.ui.viewCameraCheck.isChecked()
        self.rebuildInstanceList()

    def onInstanceListDoubleClicked(self) -> None:
        if self.ui.instanceList.selectedItems():
            item = self.ui.instanceList.selectedItems()[0]
            instance: GITInstance = item.data(QtCore.Qt.UserRole)
            self.ui.mainRenderer.scene.select(instance)

            camera = self.ui.mainRenderer.scene.camera
            newCamPos = Vector3.from_vector3(instance.position)

            ax = -math.cos(camera.yaw)*math.sin(camera.pitch)*math.sin(0) - math.sin(camera.yaw)*math.cos(0)
            ay = -math.sin(camera.yaw)*math.sin(camera.pitch)*math.sin(0) + math.cos(camera.yaw)*math.cos(0)
            az = math.cos(camera.pitch)*math.sin(0)
            angleVec3 = Vector3(ax, ay, az).normal()

            newCamPos -= angleVec3*2
            camera.x, camera.y, camera.z = newCamPos.x, newCamPos.y, newCamPos.z+1

    def onRendererMouseMoved(self, screen: Vector2, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        if QtCore.Qt.LeftButton in buttons and QtCore.Qt.Key_Control in keys:
            self.ui.mainRenderer.panCamera(delta.x / 30, delta.y / 30, 0)
        elif QtCore.Qt.MiddleButton in buttons and QtCore.Qt.Key_Control in keys:
            self.ui.mainRenderer.rotateCamera(delta.x / 200, delta.y / 200)
        ...

    def onRendererMouseScrolled(self, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        if QtCore.Qt.Key_Control in keys:
            self.ui.mainRenderer.panCamera(0, 0, delta.y / 50)

    def onRendererMousePressed(self, screen: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        if QtCore.Qt.LeftButton in buttons and QtCore.Qt.Key_Control not in keys:
            self.ui.mainRenderer.doSelect = True

    def onRendererObjectSelected(self, object: RenderObject) -> None:
        data = object.data
        if isinstance(data, GITInstance):
            self.selectInstanceItemOnList(data)


class ModuleRenderer(QOpenGLWidget):
    mouseMoved = QtCore.pyqtSignal(object, object, object, object)  # screen coords, screen delta, mouse, keys
    """Signal emitted when mouse is moved over the widget."""

    mouseScrolled = QtCore.pyqtSignal(object, object, object)  # screen delta, mouse, keys
    """Signal emitted when mouse is scrolled over the widget."""

    mouseReleased = QtCore.pyqtSignal(object, object, object)  # screen coords, mouse, keys
    """Signal emitted when a mouse button is released after being pressed on the widget."""

    mousePressed = QtCore.pyqtSignal(object, object, object)  # screen coords, mouse, keys
    """Signal emitted when a mouse button is pressed on the widget."""

    objectSelected = QtCore.pyqtSignal(object)
    """Signal emitted when an object has been selected through the renderer."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.scene: Optional[Scene] = None
        self._module: Optional[Module] = None
        self._installation: Optional[HTInstallation] = None
        self._init = False

        self._keysDown: Set[int] = set()
        self._mouseDown: Set[int] = set()
        self._mousePrev: Vector2 = Vector2(self.cursor().pos().x(), self.cursor().pos().y())

        self.doSelect: bool = False  # Set to true to select object at mouse pointer

    def init(self, installation: HTInstallation, module: Module) -> None:
        self._installation = installation
        self._module = module

        QTimer.singleShot(33, self.loop)

    def loop(self) -> None:
        self.repaint()
        QTimer.singleShot(33, self.loop)

    def paintGL(self) -> None:
        if not self._init:
            self._init = True
            self.scene = Scene(self._module, self._installation)

        if self.doSelect:
            self.doSelect = False
            obj = self.scene.pick(self._mousePrev.x, self.height() - self._mousePrev.y)
            self.scene.select(obj)
            self.objectSelected.emit(obj)

        self.scene.render()

    # region Camera Transformations
    def panCamera(self, x: float, y: float, z: float) -> None:
        """
        Moves the camera by the specified amount. The movement takes into account both the rotation and zoom of the
        camera on the x/y plane.

        Args:
            x: Units to move the x coordinate.
            y: Units to move the y coordinate.
            z: Units to move the z coordinate.
        """
        forward = y * self.scene.camera.forward()
        sideward = x * self.scene.camera.sideward()

        self.scene.camera.x += (forward.x + sideward.x)
        self.scene.camera.y += (forward.y + sideward.y)
        self.scene.camera.z += z

    def rotateCamera(self, yaw: float, pitch: float) -> None:
        """
        Rotates the camera by the angles (radians) specified.

        Args:
            yaw:
            pitch:
        """
        self.scene.camera.rotate(yaw, pitch)


    # endregion

    # region Events
    def wheelEvent(self, e: QWheelEvent) -> None:
        self.mouseScrolled.emit(Vector2(e.angleDelta().x(), e.angleDelta().y()), e.buttons(), self._keysDown)

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        coords = Vector2(e.x(), e.y())
        coordsDelta = Vector2(coords.x - self._mousePrev.x, coords.y - self._mousePrev.y)
        self._mousePrev = coords
        self.mouseMoved.emit(coords, coordsDelta, self._mouseDown, self._keysDown)

    def mousePressEvent(self, e: QMouseEvent) -> None:
        self._mouseDown.add(e.button())
        coords = Vector2(e.x(), e.y())
        self.mousePressed.emit(coords, self._mouseDown, self._keysDown)

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        self._mouseDown.discard(e.button())

        coords = Vector2(e.x(), e.y())
        self.mouseReleased.emit(coords, e.buttons(), self._keysDown)

    def keyPressEvent(self, e: QKeyEvent) -> None:
        self._keysDown.add(e.key())

    def keyReleaseEvent(self, e: QKeyEvent) -> None:
        self._keysDown.discard(e.key())
    # endregion
