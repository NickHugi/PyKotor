from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import suppress
from enum import Enum
from typing import Optional, Set, Dict

import chardet
from PyQt5 import QtCore
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QIcon, QPixmap, QColor, QKeySequence, QKeyEvent
from PyQt5.QtWidgets import QWidget, QMessageBox, QMenu, QListWidgetItem
from pykotor.common.geometry import Vector2, SurfaceMaterial, Vector3
from pykotor.extract.installation import Installation, SearchLocation
from pykotor.resource.formats.bwm import read_bwm
from pykotor.resource.formats.lyt import LYT, read_lyt
from pykotor.resource.generics.git import read_git, GIT, GITInstance, GITCreature, GITTrigger, GITEncounter, GITCamera, \
    GITWaypoint, GITSound, GITStore, GITPlaceable, GITDoor, bytes_git
from pykotor.resource.type import ResourceType

from editors.editor import Editor
from editors.git.git_dialogs import openInstanceDialog


class GITEditor(Editor):
    def __init__(self, parent: QWidget, installation: Optional[Installation] = None):
        supported = [ResourceType.GIT]
        super().__init__(parent, "GIT Editor", "git", supported, supported, installation)

        from editors.git import git_editor_ui
        self.ui = git_editor_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()
        self._setupHotkeys()

        self._git: GIT = GIT()
        self._mode: _Mode = _InstanceMode(self)
        self._geomInstance: Optional[GITInstance] = None  # Used to track which trigger/encounter you are editing

        self.materialColors: Dict[SurfaceMaterial, QColor] = {
            SurfaceMaterial.UNDEFINED: QColor(255, 0, 0, 40),
            SurfaceMaterial.OBSCURING: QColor(255, 0, 0, 40),
            SurfaceMaterial.DIRT: QColor(0x444444),
            SurfaceMaterial.GRASS: QColor(0x444444),
            SurfaceMaterial.STONE: QColor(0x444444),
            SurfaceMaterial.WOOD: QColor(0x444444),
            SurfaceMaterial.WATER: QColor(0x444444),
            SurfaceMaterial.NON_WALK: QColor(255, 0, 0, 40),
            SurfaceMaterial.TRANSPARENT: QColor(255, 0, 0, 40),
            SurfaceMaterial.CARPET: QColor(0x444444),
            SurfaceMaterial.METAL: QColor(0x444444),
            SurfaceMaterial.PUDDLES: QColor(0x444444),
            SurfaceMaterial.SWAMP: QColor(0x444444),
            SurfaceMaterial.MUD: QColor(0x444444),
            SurfaceMaterial.LEAVES: QColor(0x444444),
            SurfaceMaterial.LAVA: QColor(255, 0, 0, 40),
            SurfaceMaterial.BOTTOMLESS_PIT: QColor(255, 0, 0, 40),
            SurfaceMaterial.DEEP_WATER: QColor(255, 0, 0, 40),
            SurfaceMaterial.DOOR: QColor(0x444444),
            SurfaceMaterial.NON_WALK_GRASS: QColor(255, 0, 0, 40),
            SurfaceMaterial.TRIGGER: QColor(0x999900)
        }

        self.ui.renderArea.materialColors = self.materialColors
        self.ui.renderArea.hideWalkmeshEdges = True

        self.new()

    def _setupHotkeys(self) -> None:
        self.ui.actionDeleteSelected.setShortcut(QKeySequence("Del"))
        self.ui.actionZoomIn.setShortcut(QKeySequence("+"))
        self.ui.actionZoomOut.setShortcut(QKeySequence("-"))

    def _setupSignals(self) -> None:
        self.ui.renderArea.mousePressed.connect(self.onMousePressed)
        self.ui.renderArea.mouseMoved.connect(self.onMouseMoved)
        self.ui.renderArea.mouseScrolled.connect(self.onMouseScrolled)
        self.ui.renderArea.customContextMenuRequested.connect(self.onContextMenu)

        self.ui.listWidget.itemSelectionChanged.connect(self.onItemSelectionChanged)

        self.ui.viewCreatureCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewPlaceableCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewDoorCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewSoundCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewTriggerCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewEncounterCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewWaypointCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewCameraCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewStoreCheck.toggled.connect(self.updateInstanceVisibility)

        self.ui.actionDeleteSelected.triggered.connect(lambda: self._mode.removeSelected())
        self.ui.actionZoomIn.triggered.connect(lambda: self.ui.renderArea.zoomInCamera(1))
        self.ui.actionZoomOut.triggered.connect(lambda: self.ui.renderArea.zoomInCamera(-1))
        self.ui.actionRecentreCamera.triggered.connect(lambda: self.ui.renderArea.centerCamera())

    def load(self, filepath: str, resref: str, restype: ResourceType, data: bytes) -> None:
        super().load(filepath, resref, restype, data)

        order = [SearchLocation.OVERRIDE, SearchLocation.CHITIN, SearchLocation.MODULES]
        result = self._installation.resource(resref, ResourceType.LYT, order)
        if result:
            m = QMessageBox(QMessageBox.Information,
                            "Found the corresponding LYT file.",
                            "Would you like to load it?\n" + result.filepath,
                            QMessageBox.Yes | QMessageBox.No,
                            self)
            if m.exec():
                self.loadLayout(read_lyt(result.data))

        self._git = read_git(data)
        self.ui.renderArea.setGit(self._git)
        self.updateInstanceVisibility()
        self.ui.renderArea.centerCamera()

    def build(self) -> bytes:
        return bytes_git(self._git)

    def new(self) -> None:
        super().new()

    def loadLayout(self, layout: LYT) -> None:
        walkmeshes = []
        for room in layout.rooms:
            order = [SearchLocation.OVERRIDE, SearchLocation.CHITIN, SearchLocation.MODULES]
            bwmData = self._installation.resource(room.model, ResourceType.WOK, order).data
            walkmeshes.append(read_bwm(bwmData))

        self.ui.renderArea.setWalkmeshes(walkmeshes)

    def git(self) -> GIT:
        return self._git

    def setMode(self, mode: _Mode) -> None:
        self._mode = mode

    def removeSelected(self) -> None:
        self._mode.removeSelected()

    def updateStatusBar(self) -> None:
        self._mode.updateStatusBar()

    def updateInstanceVisibility(self) -> None:
        self._mode.updateInstanceVisibility()

    def onMouseMoved(self, screen: Vector2, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        self._mode.onMouseMoved(screen, delta, buttons, keys)

    def onMouseScrolled(self, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        self._mode.onMouseScrolled(delta, buttons, keys)

    def onMousePressed(self, screen: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        self._mode.onMousePressed(screen, buttons, keys)

    def onContextMenu(self, point: QPoint) -> None:
        self._mode.onContextMenu(point)

    def onItemSelectionChanged(self) -> None:
        self._mode.onItemSelectionChanged()

    def keyPressEvent(self, e: QKeyEvent) -> None:
        super().keyPressEvent(e)
        self.ui.renderArea.keyPressEvent(e)

    def keyReleaseEvent(self, e: QKeyEvent) -> None:
        super().keyPressEvent(e)
        self.ui.renderArea.keyReleaseEvent(e)


class _Mode(ABC):
    def __init__(self, editor: GITEditor):
        self._editor: GITEditor = editor
        from editors.git import git_editor_ui
        self._ui: git_editor_ui = editor.ui

    @abstractmethod
    def removeSelected(self) -> None:
        ...

    @abstractmethod
    def updateStatusBar(self) -> None:
        ...

    @abstractmethod
    def updateInstanceVisibility(self) -> None:
        ...

    @abstractmethod
    def onMouseMoved(self, screen: Vector2, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        ...

    @abstractmethod
    def onMousePressed(self, screen: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        ...

    @abstractmethod
    def onMouseScrolled(self, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        ...

    @abstractmethod
    def onContextMenu(self, point: QPoint) -> None:
        ...

    @abstractmethod
    def onItemSelectionChanged(self) -> None:
        ...


class _InstanceMode(_Mode):
    def __init__(self, editor: GITEditor):
        super(_InstanceMode, self).__init__(editor)
        self._ui.renderArea.hideGeomPoints = True
        self.updateInstanceVisibility()

    def updateStatusBar(self) -> None:
        screen = self._ui.renderArea.mapFromGlobal(self._editor.cursor().pos())
        world = self._ui.renderArea.toWorldCoords(screen.x(), screen.y())

        reference = ""
        if self._ui.renderArea.instancesUnderMouse():
            instance = self._ui.renderArea.instancesUnderMouse()[0]
            reference = "" if instance.reference() is None else instance.reference()

        statusFormat = "Mode: Instance Mode, X: {:.2f}, Y: {:.2f}, Z: {:.2f}, ResRef: {}"
        status = statusFormat.format(world.x, world.y, world.z, reference)

        self._editor.statusBar().showMessage(status)

    def updateInstanceVisibility(self):
        self._ui.renderArea.hideCreatures = not self._ui.viewCreatureCheck.isChecked()
        self._ui.renderArea.hidePlaceables = not self._ui.viewPlaceableCheck.isChecked()
        self._ui.renderArea.hideDoors = not self._ui.viewDoorCheck.isChecked()
        self._ui.renderArea.hideTriggers = not self._ui.viewTriggerCheck.isChecked()
        self._ui.renderArea.hideEncounters = not self._ui.viewEncounterCheck.isChecked()
        self._ui.renderArea.hideWaypoints = not self._ui.viewWaypointCheck.isChecked()
        self._ui.renderArea.hideSounds = not self._ui.viewSoundCheck.isChecked()
        self._ui.renderArea.hideStores = not self._ui.viewStoreCheck.isChecked()
        self._ui.renderArea.hideCameras = not self._ui.viewCameraCheck.isChecked()
        self.rebuildInstanceList()

    def rebuildInstanceList(self) -> None:
        self._ui.listWidget.clear()
        for instance in self._editor.git().instances():
            if self._ui.renderArea.isInstanceVisible(instance):
                icon = QIcon(self._ui.renderArea.instancePixmap(instance))
                reference = "" if instance.reference() is None else instance.reference().get()
                text = "[{}] {}".format(self._editor.git().index(instance), reference)
                item = QListWidgetItem(icon, text)
                item.setData(QtCore.Qt.UserRole, instance)
                self._ui.listWidget.addItem(item)

    def selectInstanceItem(self, instance: GITInstance) -> None:
        # Block signals to prevent the camera from snapping to the instance every time the player clicks on an instance
        # see: onItemSelectionChanged()
        self._ui.listWidget.blockSignals(True)
        for i in range(self._ui.listWidget.count()):
            item = self._ui.listWidget.item(i)
            if item.data(QtCore.Qt.UserRole) is instance:
                self._ui.listWidget.setCurrentItem(item)
        self._ui.listWidget.blockSignals(False)

    def removeSelected(self) -> None:
        for instance in self._ui.renderArea.selectedInstances():
            self._editor.git().remove(instance)
        self._ui.renderArea.clearSelectedInstances()
        self.rebuildInstanceList()

    def addInstance(self, instance: GITInstance):
        self._editor.git().add(instance)
        self.rebuildInstanceList()

    def editSelectedInstance(self) -> None:
        instance = self._ui.renderArea.selectedInstances()[0]
        openInstanceDialog(self._editor, instance)
        self.rebuildInstanceList()

    def onMouseMoved(self, screen: Vector2, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        worldDelta = self._ui.renderArea.toWorldDelta(delta.x, delta.y)

        if QtCore.Qt.LeftButton in buttons and QtCore.Qt.Key_Control in keys:
            self._ui.renderArea.panCamera(-worldDelta.x, -worldDelta.y)
        elif QtCore.Qt.MiddleButton in buttons and QtCore.Qt.Key_Control in keys:
            self._ui.renderArea.rotateCamera(delta.x / 50)
        elif QtCore.Qt.LeftButton in buttons and not QtCore.Qt.Key_Control in keys:
            for instance in self._ui.renderArea.selectedInstances():
                instance.move(worldDelta.x, worldDelta.y, 0.0)
                # Snap the instance on top of the walkmesh, if there is no walkmesh underneath it will snap Z to 0
                getZ = self._ui.renderArea.getZCoord(instance.position.x, instance.position.y)
                instance.position.z = getZ if getZ != 0.0 else instance.position.z

        self.updateStatusBar()

    def onMousePressed(self, screen: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        underMouse = self._ui.renderArea.instancesUnderMouse()
        currentSelecton = self._ui.renderArea.selectedInstances()

        # Do not change the selection if the selected instance if its still underneath the mouse
        if currentSelecton and currentSelecton[0] in underMouse:
            return

        self._ui.renderArea.clearSelectedInstances()
        if self._ui.renderArea.instancesUnderMouse():
            instance = self._ui.renderArea.instancesUnderMouse()[0]
            self._ui.renderArea.selectInstances([instance])
            self.selectInstanceItem(instance)

    def onMouseScrolled(self, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        if QtCore.Qt.Key_Control in keys:
            self._ui.renderArea.zoomInCamera(delta.y / 50)

    def onContextMenu(self, point: QPoint) -> None:
        menu = QMenu(self._editor)
        world = self._ui.renderArea.toWorldCoords(point.x(), point.y())

        if self._ui.renderArea.selectedInstances():
            menu.addAction("Remove").triggered.connect(self.removeSelected)

        if len(self._ui.renderArea.selectedInstances()) == 1:
            menu.addAction("Edit Instance").triggered.connect(self.editSelectedInstance)
            instance = self._ui.renderArea.selectedInstances()[0]
            if isinstance(instance, GITEncounter) or isinstance(instance, GITTrigger):
                menu.addAction("Edit Geometry").triggered.connect(lambda: self._editor.setMode(_GeometryMode(self._editor, instance)))

        if len(self._ui.renderArea.selectedInstances()) == 0:
            menu.addAction("Insert Creature").triggered.connect(lambda: self.addInstance(GITCreature(world.x, world.y)))
            menu.addAction("Insert Door").triggered.connect(lambda: self.addInstance(GITDoor(world.x, world.y)))
            menu.addAction("Insert Placeable").triggered.connect(lambda: self.addInstance(GITPlaceable(world.x, world.y)))
            menu.addAction("Insert Store").triggered.connect(lambda: self.addInstance(GITStore(world.x, world.y)))
            menu.addAction("Insert Sound").triggered.connect(lambda: self.addInstance(GITSound(world.x, world.y)))
            menu.addAction("Insert Waypoint").triggered.connect(lambda: self.addInstance(GITWaypoint(world.x, world.y)))
            menu.addAction("Insert Camera").triggered.connect(lambda: self.addInstance(GITCamera(world.x, world.y)))
            menu.addAction("Insert Encounter").triggered.connect(lambda: self.addInstance(GITEncounter(world.x, world.y)))
            menu.addAction("Insert Trigger").triggered.connect(lambda: self.addInstance(GITTrigger(world.x, world.y)))

        menu.addSeparator()
        for instance in self._ui.renderArea.instancesUnderMouse():
            icon = QIcon(self._ui.renderArea.instancePixmap(instance))
            reference = "" if instance.reference() is None else instance.reference().get()
            index = self._editor.git().index(instance)
            onTriggered = lambda checked, inst=instance: self._ui.renderArea.selectInstance(inst)
            menu.addAction(icon, "[{}] {}".format(index, reference)).triggered.connect(onTriggered)

        menu.popup(self._ui.renderArea.mapToGlobal(point))

    def onItemSelectionChanged(self) -> None:
        if self._ui.listWidget.selectedItems():
            item = self._ui.listWidget.selectedItems()[0]
            instance = item.data(QtCore.Qt.UserRole)
            self._ui.renderArea.setCameraPosition(instance.position.x, instance.position.y)
            self._ui.renderArea.selectInstance(instance)


class _GeometryMode(_Mode):
    def __init__(self, editor: GITEditor, instance: GITInstance):
        super(_GeometryMode, self).__init__(editor)

        self._ui.renderArea.hideCreatures = True
        self._ui.renderArea.hideDoors = True
        self._ui.renderArea.hidePlaceables = True
        self._ui.renderArea.hideSounds = True
        self._ui.renderArea.hideStores = True
        self._ui.renderArea.hideCameras = True
        self._ui.renderArea.hideTriggers = True
        self._ui.renderArea.hideEncounters = True
        self._ui.renderArea.hideWaypoints = True
        self._ui.renderArea.hideGeomPoints = False

    def removeSelected(self) -> None:
        geomPoints = self._ui.renderArea.selectedGeomPoints()
        for geomPoint in geomPoints:
            geomPoint.instance.geometry.remove(geomPoint.point)

    def insertPointAtMouse(self) -> None:
        screen = self._ui.renderArea.mapFromGlobal(self._editor.cursor().pos())
        world = self._ui.renderArea.toWorldCoords(screen.x(), screen.y())

        instance = self._ui.renderArea.selectedInstances()[0]
        point = world - instance.position
        instance.geometry.points.append(point)

    def editSelectedPoint(self) -> None:
        raise NotImplementedError()

    def updateStatusBar(self) -> None:
        screen = self._ui.renderArea.mapFromGlobal(self._editor.cursor().pos())
        world = self._ui.renderArea.toWorldCoords(screen.x(), screen.y())

        pointIndex = ""
        if self._ui.renderArea.geomPointsUnderMouse():
            with suppress(ValueError):
                instance = self._ui.renderArea.selectedInstances()[0]
                pointIndex = instance.geometry.points.index(self._ui.renderArea.geomPointsUnderMouse()[0].point)

        statusFormat = "Mode: Geometry Mode, X: {:.2f}, Y: {:.2f}, Z: {:.2f}, Point: {}"
        status = statusFormat.format(world.x, world.y, world.z, pointIndex)

        self._editor.statusBar().showMessage(status)

    def updateInstanceVisibility(self) -> None:
        ...

    def onMouseMoved(self, screen: Vector2, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        worldDelta = self._ui.renderArea.toWorldDelta(delta.x, delta.y)

        if QtCore.Qt.LeftButton in buttons and QtCore.Qt.Key_Control in keys:
            self._ui.renderArea.panCamera(-worldDelta.x, -worldDelta.y)
        elif QtCore.Qt.MiddleButton in buttons and QtCore.Qt.Key_Control in keys:
            self._ui.renderArea.rotateCamera(delta.x / 50)
        elif QtCore.Qt.LeftButton in buttons and not QtCore.Qt.Key_Control in keys and self._ui.renderArea.selectedGeomPoints():
            instance, point = self._ui.renderArea.selectedGeomPoints()[0]
            point.x += worldDelta.x
            point.y += worldDelta.y
            point.z = self._ui.renderArea.toWorldCoords(instance.position.x, instance.position.y).z

        self.updateStatusBar()

    def onMousePressed(self, screen: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        if self._ui.renderArea.geomPointsUnderMouse():
            point = self._ui.renderArea.geomPointsUnderMouse()[0]
            self._ui.renderArea.selectGeomPoint(point)
        else:
            self._ui.renderArea.clearSelectedGeomPoints()

    def onMouseScrolled(self, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        if QtCore.Qt.Key_Control in keys:
            self._ui.renderArea.zoomInCamera(delta.y / 50)

    def onContextMenu(self, point: QPoint) -> None:
        menu = QMenu(self._editor)

        if self._ui.renderArea.selectedGeomPoints():
            menu.addAction("Remove").triggered.connect(self.removeSelected)

        if len(self._ui.renderArea.selectedGeomPoints()) == 1:
            menu.addAction("Edit").triggered.connect(self.editSelectedPoint)

        if len(self._ui.renderArea.selectedGeomPoints()) == 0:
            menu.addAction("Insert").triggered.connect(self.insertPointAtMouse)

        menu.addSeparator()
        menu.addAction("Finish Editing").triggered.connect(lambda: self._editor.setMode(_InstanceMode(self._editor)))

        menu.popup(self._ui.renderArea.mapToGlobal(point))

    def onItemSelectionChanged(self) -> None:
        ...
