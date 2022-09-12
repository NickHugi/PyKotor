from __future__ import annotations

import ast
import math
from abc import ABC, abstractmethod
from contextlib import suppress
from copy import deepcopy
from typing import Optional, Set, Dict, List, Callable, Tuple

from PyQt5 import QtCore
from PyQt5.QtCore import QPoint, QSettings
from PyQt5.QtGui import QIcon, QColor, QKeySequence, QKeyEvent
from PyQt5.QtWidgets import QWidget, QMenu, QListWidgetItem, QCheckBox, QDialog

from data.misc import Bind
from pykotor.common.misc import Color

from gui.dialogs.instance.camera import CameraDialog
from gui.dialogs.instance.creature import CreatureDialog
from gui.dialogs.instance.door import DoorDialog
from gui.dialogs.instance.encounter import EncounterDialog
from gui.dialogs.instance.placeable import PlaceableDialog
from gui.dialogs.instance.sound import SoundDialog
from gui.dialogs.instance.store import StoreDialog
from gui.dialogs.instance.trigger import TriggerDialog
from gui.dialogs.instance.waypoint import WaypointDialog
from pykotor.extract.file import ResourceIdentifier

from pykotor.common.geometry import Vector2, SurfaceMaterial, Vector3
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.bwm import read_bwm
from pykotor.resource.formats.lyt import LYT, read_lyt
from pykotor.resource.generics.git import read_git, GIT, GITInstance, GITCreature, GITTrigger, GITEncounter, GITCamera, \
    GITWaypoint, GITSound, GITStore, GITPlaceable, GITDoor, bytes_git
from pykotor.resource.type import ResourceType

from data.installation import HTInstallation
from gui.editor import Editor
from pykotor.tools.template import extract_name, extract_tag
from utils.window import openResourceEditor


def openInstanceDialog(parent: QWidget, instance: GITInstance, installation: HTInstallation):
    dialog = QDialog()

    if isinstance(instance, GITCreature):
        dialog = CreatureDialog(parent, instance)
    elif isinstance(instance, GITDoor):
        dialog = DoorDialog(parent, instance, installation)
    elif isinstance(instance, GITPlaceable):
        dialog = PlaceableDialog(parent, instance)
    elif isinstance(instance, GITTrigger):
        dialog = TriggerDialog(parent, instance, installation)
    elif isinstance(instance, GITCamera):
        dialog = CameraDialog(parent, instance)
    elif isinstance(instance, GITEncounter):
        dialog = EncounterDialog(parent, instance)
    elif isinstance(instance, GITSound):
        dialog = SoundDialog(parent, instance)
    elif isinstance(instance, GITWaypoint):
        dialog = WaypointDialog(parent, instance, installation)
    elif isinstance(instance, GITStore):
        dialog = StoreDialog(parent, instance)

    return dialog.exec_()


class GITEditor(Editor):
    settingsUpdated = QtCore.pyqtSignal(object)

    def __init__(self, parent: Optional[QWidget], installation: Optional[HTInstallation] = None):
        supported = [ResourceType.GIT]
        super().__init__(parent, "GIT Editor", "git", supported, supported, installation)

        from toolset.uic.editors.git import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()
        self._setupHotkeys()

        self._git: GIT = GIT()
        self._mode: _Mode = _InstanceMode(self, installation, self._git)
        self._controls: GITControlScheme = GITControlScheme(self)
        self._geomInstance: Optional[GITInstance] = None  # Used to track which trigger/encounter you are editing

        self.settings = GITSettings()

        def intColorToQColor(intvalue):
            color = Color.from_rgba_integer(intvalue)
            return QColor(int(color.r*255), int(color.g*255), int(color.b*255), int(color.a*255))
        self.materialColors: Dict[SurfaceMaterial, QColor] = {
            SurfaceMaterial.UNDEFINED: intColorToQColor(self.settings.undefinedMaterialColour),
            SurfaceMaterial.OBSCURING: intColorToQColor(self.settings.obscuringMaterialColour),
            SurfaceMaterial.DIRT: intColorToQColor(self.settings.dirtMaterialColour),
            SurfaceMaterial.GRASS: intColorToQColor(self.settings.grassMaterialColour),
            SurfaceMaterial.STONE: intColorToQColor(self.settings.stoneMaterialColour),
            SurfaceMaterial.WOOD: intColorToQColor(self.settings.woodMaterialColour),
            SurfaceMaterial.WATER: intColorToQColor(self.settings.waterMaterialColour),
            SurfaceMaterial.NON_WALK: intColorToQColor(self.settings.nonWalkMaterialColour),
            SurfaceMaterial.TRANSPARENT: intColorToQColor(self.settings.transparentMaterialColour),
            SurfaceMaterial.CARPET: intColorToQColor(self.settings.carpetMaterialColour),
            SurfaceMaterial.METAL: intColorToQColor(self.settings.metalMaterialColour),
            SurfaceMaterial.PUDDLES: intColorToQColor(self.settings.puddlesMaterialColour),
            SurfaceMaterial.SWAMP: intColorToQColor(self.settings.swampMaterialColour),
            SurfaceMaterial.MUD: intColorToQColor(self.settings.mudMaterialColour),
            SurfaceMaterial.LEAVES: intColorToQColor(self.settings.leavesMaterialColour),
            SurfaceMaterial.LAVA: intColorToQColor(self.settings.lavaMaterialColour),
            SurfaceMaterial.BOTTOMLESS_PIT: intColorToQColor(self.settings.bottomlessPitMaterialColour),
            SurfaceMaterial.DEEP_WATER: intColorToQColor(self.settings.deepWaterMaterialColour),
            SurfaceMaterial.DOOR: intColorToQColor(self.settings.doorMaterialColour),
            SurfaceMaterial.NON_WALK_GRASS: intColorToQColor(self.settings.nonWalkGrassMaterialColour),
            SurfaceMaterial.TRIGGER: intColorToQColor(self.settings.nonWalkGrassMaterialColour)
        }
        self.nameBuffer: Dict[ResourceIdentifier, str] = {}
        self.tagBuffer: Dict[ResourceIdentifier, str] = {}

        self.ui.renderArea.materialColors = self.materialColors
        self.ui.renderArea.hideWalkmeshEdges = True
        self.ui.renderArea.highlightBoundaries = False

        self.new()

    def _setupHotkeys(self) -> None:
        self.ui.actionDeleteSelected.setShortcut(QKeySequence("Del"))
        self.ui.actionZoomIn.setShortcut(QKeySequence("+"))
        self.ui.actionZoomOut.setShortcut(QKeySequence("-"))

    def _setupSignals(self) -> None:
        self.ui.renderArea.mousePressed.connect(self.onMousePressed)
        self.ui.renderArea.mouseMoved.connect(self.onMouseMoved)
        self.ui.renderArea.mouseScrolled.connect(self.onMouseScrolled)
        self.ui.renderArea.mouseReleased.connect(self.onMouseReleased)
        self.ui.renderArea.customContextMenuRequested.connect(self.onContextMenu)
        self.ui.renderArea.keyPressed.connect(self.onKeyPressed)

        self.ui.filterEdit.textEdited.connect(self.onFilterEdited)
        self.ui.listWidget.itemSelectionChanged.connect(self.onItemSelectionChanged)
        self.ui.listWidget.customContextMenuRequested.connect(self.onItemContextMenu)

        self.ui.viewCreatureCheck.toggled.connect(self.updateVisibility)
        self.ui.viewPlaceableCheck.toggled.connect(self.updateVisibility)
        self.ui.viewDoorCheck.toggled.connect(self.updateVisibility)
        self.ui.viewSoundCheck.toggled.connect(self.updateVisibility)
        self.ui.viewTriggerCheck.toggled.connect(self.updateVisibility)
        self.ui.viewEncounterCheck.toggled.connect(self.updateVisibility)
        self.ui.viewWaypointCheck.toggled.connect(self.updateVisibility)
        self.ui.viewCameraCheck.toggled.connect(self.updateVisibility)
        self.ui.viewStoreCheck.toggled.connect(self.updateVisibility)

        self.ui.viewCreatureCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick(self.ui.viewCreatureCheck)
        self.ui.viewPlaceableCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick(self.ui.viewPlaceableCheck)
        self.ui.viewDoorCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick(self.ui.viewDoorCheck)
        self.ui.viewSoundCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick(self.ui.viewSoundCheck)
        self.ui.viewTriggerCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick(self.ui.viewTriggerCheck)
        self.ui.viewEncounterCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick(self.ui.viewEncounterCheck)
        self.ui.viewWaypointCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick(self.ui.viewWaypointCheck)
        self.ui.viewCameraCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick(self.ui.viewCameraCheck)
        self.ui.viewStoreCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick(self.ui.viewStoreCheck)

        # View
        self.ui.actionZoomIn.triggered.connect(lambda: self.ui.renderArea.camera.nudgeZoom(1))
        self.ui.actionZoomOut.triggered.connect(lambda: self.ui.renderArea.camera.nudgeZoom(-1))
        self.ui.actionRecentreCamera.triggered.connect(lambda: self.ui.renderArea.centerCamera())
        # View -> Creature Labels
        self.ui.actionUseCreatureResRef.triggered.connect(lambda: setattr(self.settings, "creatureLabel", "resref"))
        self.ui.actionUseCreatureResRef.triggered.connect(self.updateVisibility)
        self.ui.actionUseCreatureTag.triggered.connect(lambda: setattr(self.settings, "creatureLabel", "tag"))
        self.ui.actionUseCreatureTag.triggered.connect(self.updateVisibility)
        self.ui.actionUseCreatureName.triggered.connect(lambda: setattr(self.settings, "creatureLabel", "name"))
        self.ui.actionUseCreatureName.triggered.connect(self.updateVisibility)
        # View -> Door Labels
        self.ui.actionUseDoorResRef.triggered.connect(lambda: setattr(self.settings, "doorLabel", "resref"))
        self.ui.actionUseDoorResRef.triggered.connect(self.updateVisibility)
        self.ui.actionUseDoorTag.triggered.connect(lambda: setattr(self.settings, "doorLabel", "tag"))
        self.ui.actionUseDoorTag.triggered.connect(self.updateVisibility)
        self.ui.actionUseDoorName.triggered.connect(lambda: setattr(self.settings, "doorLabel", "name"))
        self.ui.actionUseDoorName.triggered.connect(self.updateVisibility)
        # View -> Placeable Labels
        self.ui.actionUsePlaceableResRef.triggered.connect(lambda: setattr(self.settings, "placeableLabel", "resref"))
        self.ui.actionUsePlaceableResRef.triggered.connect(self.updateVisibility)
        self.ui.actionUsePlaceableName.triggered.connect(lambda: setattr(self.settings, "placeableLabel", "name"))
        self.ui.actionUsePlaceableName.triggered.connect(self.updateVisibility)
        self.ui.actionUsePlaceableTag.triggered.connect(lambda: setattr(self.settings, "placeableLabel", "tag"))
        self.ui.actionUsePlaceableTag.triggered.connect(self.updateVisibility)
        # View -> Merchant Labels
        self.ui.actionUseMerchantResRef.triggered.connect(lambda: setattr(self.settings, "storeLabel", "resref"))
        self.ui.actionUseMerchantResRef.triggered.connect(self.updateVisibility)
        self.ui.actionUseMerchantName.triggered.connect(lambda: setattr(self.settings, "storeLabel", "name"))
        self.ui.actionUseMerchantName.triggered.connect(self.updateVisibility)
        self.ui.actionUseMerchantTag.triggered.connect(lambda: setattr(self.settings, "storeLabel", "tag"))
        self.ui.actionUseMerchantTag.triggered.connect(self.updateVisibility)
        # View -> Sound Labels
        self.ui.actionUseSoundResRef.triggered.connect(lambda: setattr(self.settings, "soundLabel", "resref"))
        self.ui.actionUseSoundResRef.triggered.connect(self.updateVisibility)
        self.ui.actionUseSoundName.triggered.connect(lambda: setattr(self.settings, "soundLabel", "name"))
        self.ui.actionUseSoundName.triggered.connect(self.updateVisibility)
        self.ui.actionUseSoundTag.triggered.connect(lambda: setattr(self.settings, "soundLabel", "tag"))
        self.ui.actionUseSoundTag.triggered.connect(self.updateVisibility)
        # View -> Waypoint Labels
        self.ui.actionUseWaypointResRef.triggered.connect(lambda: setattr(self.settings, "waypointLabel", "resref"))
        self.ui.actionUseWaypointResRef.triggered.connect(self.updateVisibility)
        self.ui.actionUseWaypointName.triggered.connect(lambda: setattr(self.settings, "waypointLabel", "name"))
        self.ui.actionUseWaypointName.triggered.connect(self.updateVisibility)
        self.ui.actionUseWaypointTag.triggered.connect(lambda: setattr(self.settings, "waypointLabel", "tag"))
        self.ui.actionUseWaypointTag.triggered.connect(self.updateVisibility)
        # View -> Encounter Labels
        self.ui.actionUseEncounterResRef.triggered.connect(lambda: setattr(self.settings, "encounterLabel", "resref"))
        self.ui.actionUseEncounterResRef.triggered.connect(self.updateVisibility)
        self.ui.actionUseEncounterName.triggered.connect(lambda: setattr(self.settings, "encounterLabel", "name"))
        self.ui.actionUseEncounterName.triggered.connect(self.updateVisibility)
        self.ui.actionUseEncounterTag.triggered.connect(lambda: setattr(self.settings, "encounterLabel", "tag"))
        self.ui.actionUseEncounterTag.triggered.connect(self.updateVisibility)
        # View -> Trigger Labels
        self.ui.actionUseTriggerResRef.triggered.connect(lambda: setattr(self.settings, "triggerLabel", "resref"))
        self.ui.actionUseTriggerResRef.triggered.connect(self.updateVisibility)
        self.ui.actionUseTriggerTag.triggered.connect(lambda: setattr(self.settings, "triggerLabel", "tag"))
        self.ui.actionUseTriggerTag.triggered.connect(self.updateVisibility)
        self.ui.actionUseTriggerName.triggered.connect(lambda: setattr(self.settings, "triggerLabel", "name"))
        self.ui.actionUseTriggerName.triggered.connect(self.updateVisibility)

    def load(self, filepath: str, resref: str, restype: ResourceType, data: bytes) -> None:
        super().load(filepath, resref, restype, data)

        order = [SearchLocation.OVERRIDE, SearchLocation.CHITIN, SearchLocation.MODULES]
        result = self._installation.resource(resref, ResourceType.LYT, order)
        if result:
            self.loadLayout(read_lyt(result.data))

        git = read_git(data)
        self._loadGIT(git)

    def _loadGIT(self, git: GIT):
        self._git = git
        self.ui.renderArea.setGit(self._git)
        self.ui.renderArea.centerCamera()
        self._mode = _InstanceMode(self, self._installation, self._git)
        self.updateVisibility()

    def build(self) -> bytes:
        return bytes_git(self._git)

    def new(self) -> None:
        super().new()

    def loadLayout(self, layout: LYT) -> None:
        walkmeshes = []
        for room in layout.rooms:
            order = [SearchLocation.OVERRIDE, SearchLocation.CHITIN, SearchLocation.MODULES]
            findBWM = self._installation.resource(room.model, ResourceType.WOK, order)
            if findBWM is not None:
                walkmeshes.append(read_bwm(findBWM.data))

        self.ui.renderArea.setWalkmeshes(walkmeshes)

    def git(self) -> GIT:
        return self._git

    def setMode(self, mode: _Mode) -> None:
        self._mode = mode

    def onInstanceVisibilityDoubleClick(self, checkbox: QCheckBox) -> None:
        self.ui.viewCreatureCheck.setChecked(False)
        self.ui.viewPlaceableCheck.setChecked(False)
        self.ui.viewDoorCheck.setChecked(False)
        self.ui.viewSoundCheck.setChecked(False)
        self.ui.viewTriggerCheck.setChecked(False)
        self.ui.viewEncounterCheck.setChecked(False)
        self.ui.viewWaypointCheck.setChecked(False)
        self.ui.viewCameraCheck.setChecked(False)
        self.ui.viewStoreCheck.setChecked(False)

        checkbox.setChecked(True)

    def getInstanceExternalName(self, instance: GITInstance) -> Optional[str]:
        resid = instance.identifier()
        if resid not in self.nameBuffer:
            res = self._installation.resource(resid.resname, resid.restype)
            self.nameBuffer[resid] = None if res is None else self._installation.string(extract_name(res.data))
        return self.nameBuffer[resid]

    def getInstanceExternalTag(self, instance: GITInstance) -> Optional[str]:
        resid = instance.identifier()
        if resid not in self.tagBuffer:
            res = self._installation.resource(resid.resname, resid.restype)
            self.tagBuffer[resid] = None if res is None else extract_tag(res.data)
        return self.tagBuffer[resid]

    def enterInstanceMode(self) -> None:
        self._mode = _InstanceMode(self, self._installation, self._git)

    def enterGeometryMode(self) -> None:
        self._mode = _GeometryMode(self, self._installation, self._git)

    def enterSpawnMode(self) -> None:
        ...
        # TODO

    # region Mode Calls
    def openListContextMenu(self, item: QListWidgetItem, point: QPoint) -> None:
        ...

    def updateVisibility(self) -> None:
        self._mode.updateVisibility()

    def selectUnderneath(self) -> None:
        self._mode.selectUnderneath()

    def deleteSelected(self) -> None:
        self._mode.deleteSelected()

    def duplicateSelected(self) -> None:
        self._mode.duplicateSelected()

    def moveSelected(self, x: float, y: float) -> None:
        self._mode.moveSelected(x, y)

    def rotateSelected(self, angle: float) -> None:
        self._mode.rotateSelected(angle)

    def rotateSelectedToPoint(self, x: float, y: float) -> None:
        self._mode.rotateSelectedToPoint(x, y)

    def moveCamera(self, x: float, y: float) -> None:
        self._mode.moveCamera(x, y)

    def zoomCamera(self, amount: float) -> None:
        self._mode.zoomCamera(amount)

    def rotateCamera(self, angle: float) -> None:
        self._mode.rotateCamera(angle)
    # endregion

    # region Signal Callbacks
    def onContextMenu(self, point: QPoint) -> None:
        globalPoint = self.ui.renderArea.mapToGlobal(point)
        world = self.ui.renderArea.toWorldCoords(point.x(), point.y())
        self._mode.onRenderContextMenu(world, globalPoint)

    def onFilterEdited(self) -> None:
        self._mode.onFilterEdited(self.ui.filterEdit.text())

    def onItemSelectionChanged(self) -> None:
        self._mode.onItemSelectionChanged(self.ui.listWidget.currentItem())

    def onItemContextMenu(self, point: QPoint) -> None:
        globalPoint = self.ui.listWidget.mapToGlobal(point)
        item = self.ui.listWidget.currentItem()
        self._mode.openListContextMenu(item, globalPoint)

    def onMouseMoved(self, screen: Vector2, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        worldDelta = self.ui.renderArea.toWorldDelta(delta.x, delta.y)
        world = self.ui.renderArea.toWorldCoords(screen.x, screen.y)
        self._controls.onMouseMoved(screen, delta, world, worldDelta, buttons, keys)
        self._mode.updateStatusBar(world)

    def onMouseScrolled(self, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        self._controls.onMouseScrolled(delta, buttons, keys)

    def onMousePressed(self, screen: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        self._controls.onMousePressed(screen, buttons, keys)

    def onMouseReleased(self, buttons: Set[int], keys: Set[int]) -> None:
        self._controls.onMouseReleased(Vector2(0, 0), buttons, keys)

    def onKeyPressed(self, buttons: Set[int], keys: Set[int]) -> None:
        self._controls.onKeyboardPressed(buttons, keys)

    def keyPressEvent(self, e: QKeyEvent) -> None:
        self.ui.renderArea.keyPressEvent(e)

    def keyReleaseEvent(self, e: QKeyEvent) -> None:
        self.ui.renderArea.keyReleaseEvent(e)
    # endregion


class _Mode(ABC):
    def __init__(self, editor: GITEditor, installation: HTInstallation, git: GIT):
        self._editor: GITEditor = editor
        self._installation: HTInstallation = installation
        self._git: GIT = git

        from toolset.uic.editors import git as gitui
        self._ui: gitui = editor.ui

    @abstractmethod
    def onItemSelectionChanged(self, item: QListWidgetItem) -> None:
        ...

    @abstractmethod
    def onFilterEdited(self, text: str) -> None:
        ...

    @abstractmethod
    def onRenderContextMenu(self, world: Vector2, screen: QPoint) -> None:
        ...

    @abstractmethod
    def openListContextMenu(self, item: QListWidgetItem, screen: QPoint) -> None:
        ...

    @abstractmethod
    def updateVisibility(self) -> None:
        ...

    @abstractmethod
    def selectUnderneath(self) -> None:
        ...

    @abstractmethod
    def deleteSelected(self) -> None:
        ...

    @abstractmethod
    def duplicateSelected(self) -> None:
        ...

    @abstractmethod
    def moveSelected(self, x: float, y: float) -> None:
        ...

    @abstractmethod
    def rotateSelected(self, angle: float) -> None:
        ...

    @abstractmethod
    def rotateSelectedToPoint(self, x: float, y: float) -> None:
        ...

    @abstractmethod
    def moveCamera(self, x: float, y: float) -> None:
        ...

    @abstractmethod
    def zoomCamera(self, amount: float) -> None:
        ...

    @abstractmethod
    def rotateCamera(self, angle: float) -> None:
        ...
    # endregion


class _InstanceMode(_Mode):
    def __init__(self, editor: GITEditor, installation: HTInstallation, git: GIT):
        super(_InstanceMode, self).__init__(editor, installation, git)
        self._ui.renderArea.hideGeomPoints = True
        self._ui.renderArea.geometrySelection.clear()
        self.updateVisibility()

    def setSelection(self, instances: List[GITInstance]) -> None:
        # Set the renderer widget selection
        self._ui.renderArea.instanceSelection.select(instances)

        # Set the list widget selection
        self._ui.listWidget.blockSignals(True)
        for i in range(self._ui.listWidget.count()):
            item = self._ui.listWidget.item(i)
            instance = item.data(QtCore.Qt.UserRole)
            if instance in instances:
                self._ui.listWidget.setCurrentItem(item)
        self._ui.listWidget.blockSignals(False)

    def editSelectedInstance(self) -> None:
        selection = self._ui.renderArea.instanceSelection.all()

        if selection:
            instance = selection[-1]
            openInstanceDialog(self._editor, instance, self._installation)
            self.buildList()

    def editSelectedInstanceResource(self) -> None:
        selection = self._ui.renderArea.instanceSelection.all()

        if selection:
            instance = selection[-1]
            res = self._installation.resource(instance.identifier().resname, instance.identifier().restype)
            if not res:
                # TODO Make prompt for override/MOD
                ...
            openResourceEditor(res.filepath, res.resname, res.restype, res.data, self._installation, self._editor)

    def editSelectedInstanceGeometry(self) -> None:
        if self._ui.renderArea.instanceSelection.last():
            instance = self._ui.renderArea.instanceSelection.last()
            self._editor.enterGeometryMode()

    def editSelectedInstanceSpawns(self) -> None:
        if self._ui.renderArea.instanceSelection.last():
            instance = self._ui.renderArea.instanceSelection.last()
            # TODO

    def addInstance(self, instance: GITInstance) -> None:
        if openInstanceDialog(self._editor, instance, self._installation):
            self._git.add(instance)
            self.buildList()

    def addInstanceActionsToMenu(self, instance: GITInstance, menu: QMenu) -> None:
        menu.addAction("Remove").triggered.connect(self.deleteSelected)
        menu.addAction("Edit Instance").triggered.connect(self.editSelectedInstance)

        actionEditResource = menu.addAction("Edit Resource")
        actionEditResource.triggered.connect(self.editSelectedInstanceResource)
        actionEditResource.setEnabled(not isinstance(instance, GITCamera))
        menu.addAction(actionEditResource)

        if isinstance(instance, GITEncounter) or isinstance(instance, GITTrigger):
            menu.addAction("Edit Geometry").triggered.connect(self.editSelectedInstanceGeometry)

        if isinstance(instance, GITEncounter):
            menu.addAction("Edit Spawn Points").triggered.connect(self.editSelectedInstanceSpawns)

    def setListItemLabel(self, item: QListWidgetItem, instance: GITInstance) -> None:
        item.setData(QtCore.Qt.UserRole, instance)
        item.setToolTip(self.getInstanceTooltip(instance))

        name = None
        failedToFind = True

        if isinstance(instance, GITCamera):
            item.setText(str(instance.camera_id))
            return
        elif isinstance(instance, GITCreature):
            if self._editor.settings.creatureLabel == "tag":
                name = self._editor.getInstanceExternalTag(instance)
            elif self._editor.settings.creatureLabel == "name":
                name = self._editor.getInstanceExternalName(instance)
            else:
                name = instance.identifier().resname
        elif isinstance(instance, GITPlaceable):
            if self._editor.settings.placeableLabel == "tag":
                name = self._editor.getInstanceExternalTag(instance)
            elif self._editor.settings.placeableLabel == "name":
                name = self._editor.getInstanceExternalName(instance)
            else:
                name = instance.identifier().resname
        elif isinstance(instance, GITDoor):
            if self._editor.settings.doorLabel == "tag":
                name = instance.tag
            elif self._editor.settings.doorLabel == "name":
                name = self._editor.getInstanceExternalName(instance)
            else:
                name = instance.identifier().resname
        elif isinstance(instance, GITStore):
            if self._editor.settings.storeLabel == "tag":
                name = self._editor.getInstanceExternalTag(instance)
            elif self._editor.settings.storeLabel == "name":
                name = self._editor.getInstanceExternalName(instance)
            else:
                name = instance.identifier().resname
        elif isinstance(instance, GITSound):
            if self._editor.settings.soundLabel == "tag":
                name = self._editor.getInstanceExternalTag(instance)
            elif self._editor.settings.soundLabel == "name":
                name = self._editor.getInstanceExternalName(instance)
            else:
                name = instance.identifier().resname
        elif isinstance(instance, GITWaypoint):
            if self._editor.settings.waypointLabel == "tag":
                name = instance.tag
            elif self._editor.settings.waypointLabel == "name":
                name = self._installation.string(instance.name, None)
            else:
                name = instance.identifier().resname
        elif isinstance(instance, GITEncounter):
            if self._editor.settings.encounterLabel == "tag":
                name = self._editor.getInstanceExternalTag(instance)
            elif self._editor.settings.encounterLabel == "name":
                name = self._editor.getInstanceExternalName(instance)
            else:
                name = instance.identifier().resname
        elif isinstance(instance, GITTrigger):
            if self._editor.settings.triggerLabel == "tag":
                name = instance.tag
            elif self._editor.settings.triggerLabel == "name":
                name = self._editor.getInstanceExternalName(instance)
            else:
                name = instance.identifier().resname

        failedToFind = name is None
        text = instance.identifier().resname if failedToFind else name

        if failedToFind:
            font = item.font()
            font.setItalic(True)
            item.setFont(font)

        item.setText(text)

    def getInstanceTooltip(self, instance: GITInstance) -> str:
        if isinstance(instance, GITCamera):
            return "Struct Index: {}\nCamera ID: {}".format(self._git.index(instance), instance.camera_id)
        else:
            return "Struct Index: {}\nResRef: {}".format(self._git.index(instance), instance.identifier().resname)

    # region Interface Methods
    def onFilterEdited(self, text: str) -> None:
        self._ui.renderArea.instanceFilter = text
        self.buildList()

    def onItemSelectionChanged(self, item: QListWidgetItem) -> None:
        if item is None:
            self.setSelection([])
        else:
            self.setSelection([item.data(QtCore.Qt.UserRole)])

    def updateStatusBar(self, world: Vector2) -> None:
        if self._ui.renderArea.instancesUnderMouse():
            instance = self._ui.renderArea.instancesUnderMouse()[-1]
            self._editor.statusBar().showMessage("({:.1f}, {:.1f}) {}".format(world.x, world.y, instance.identifier().resname))
        else:
            self._editor.statusBar().showMessage("({:.1f}, {:.1f})".format(world.x, world.y))

    def openListContextMenu(self, item: QListWidgetItem, point: QPoint) -> None:
        if item is None:
            return

        instance = item.data(QtCore.Qt.UserRole)
        menu = QMenu(self._ui.listWidget)

        self.addInstanceActionsToMenu(instance, menu)

        menu.popup(point)

    def onRenderContextMenu(self, world: Vector2, point: QPoint) -> None:
        underMouse = self._ui.renderArea.instancesUnderMouse()

        menu = QMenu(self._ui.listWidget)

        if not self._ui.renderArea.instanceSelection.isEmpty():
            self.addInstanceActionsToMenu(self._ui.renderArea.instanceSelection.last(), menu)
        else:
            menu.addAction("Insert Creature").triggered.connect(lambda: self.addInstance(GITCreature(world.x, world.y)))
            menu.addAction("Insert Door").triggered.connect(lambda: self.addInstance(GITDoor(world.x, world.y)))
            menu.addAction("Insert Placeable").triggered.connect(lambda: self.addInstance(GITPlaceable(world.x, world.y)))
            menu.addAction("Insert Store").triggered.connect(lambda: self.addInstance(GITStore(world.x, world.y)))
            menu.addAction("Insert Sound").triggered.connect(lambda: self.addInstance(GITSound(world.x, world.y)))
            menu.addAction("Insert Waypoint").triggered.connect(lambda: self.addInstance(GITWaypoint(world.x, world.y)))
            menu.addAction("Insert Camera").triggered.connect(lambda: self.addInstance(GITCamera(world.x, world.y)))
            menu.addAction("Insert Encounter").triggered.connect(lambda: self.addInstance(GITEncounter(world.x, world.y)))

            simpleTrigger = GITTrigger(world.x, world.y)
            simpleTrigger.geometry.extend([Vector3(0.0, 0.0, 0.0), Vector3(3.0, 0.0, 0.0), Vector3(3.0, 3.0, 0.0), Vector3(0.0, 3.0, 0.0)])
            menu.addAction("Insert Trigger").triggered.connect(lambda: self.addInstance(simpleTrigger))

        if underMouse:
            menu.addSeparator()
            for instance in underMouse:
                icon = QIcon(self._ui.renderArea.instancePixmap(instance))
                reference = "" if instance.identifier() is None else instance.identifier().resname
                index = self._editor.git().index(instance)

                instanceAction = menu.addAction(icon, "[{}] {}".format(index, reference))
                instanceAction.triggered.connect(lambda _, inst=instance: self.setSelection([inst]))
                instanceAction.setEnabled(instance not in self._ui.renderArea.instanceSelection.all())
                menu.addAction(instanceAction)

        menu.popup(point)

    def buildList(self) -> None:
        self._ui.listWidget.clear()

        def instanceSort(inst):
            textToSort = str(inst.camera_id) if isinstance(inst, GITCamera) else inst.identifier().resname.lower()
            textToSort = textToSort if isinstance(inst, GITCamera) else inst.identifier().restype.extension + textToSort
            return textToSort
        instances = self._git.instances()
        instances = sorted(instances, key=instanceSort)

        for instance in instances:
            filterSource = str(instance.camera_id) if isinstance(instance, GITCamera) else instance.identifier().resname
            isVisible = self._ui.renderArea.isInstanceVisible(instance)
            isFiltered = self._ui.filterEdit.text() in filterSource

            if isVisible and isFiltered:
                icon = QIcon(self._ui.renderArea.instancePixmap(instance))
                item = QListWidgetItem(icon, "")
                self.setListItemLabel(item, instance)
                self._ui.listWidget.addItem(item)

    def updateVisibility(self) -> None:
        self._ui.renderArea.hideCreatures = not self._ui.viewCreatureCheck.isChecked()
        self._ui.renderArea.hidePlaceables = not self._ui.viewPlaceableCheck.isChecked()
        self._ui.renderArea.hideDoors = not self._ui.viewDoorCheck.isChecked()
        self._ui.renderArea.hideTriggers = not self._ui.viewTriggerCheck.isChecked()
        self._ui.renderArea.hideEncounters = not self._ui.viewEncounterCheck.isChecked()
        self._ui.renderArea.hideWaypoints = not self._ui.viewWaypointCheck.isChecked()
        self._ui.renderArea.hideSounds = not self._ui.viewSoundCheck.isChecked()
        self._ui.renderArea.hideStores = not self._ui.viewStoreCheck.isChecked()
        self._ui.renderArea.hideCameras = not self._ui.viewCameraCheck.isChecked()
        self.buildList()

    def selectUnderneath(self) -> None:
        underMouse = self._ui.renderArea.instancesUnderMouse()
        selection = self._ui.renderArea.instanceSelection.all()

        # Do not change the selection if the selected instance if its still underneath the mouse
        if selection and selection[0] in underMouse:
            return

        if underMouse:
            self.setSelection([underMouse[-1]])
        else:
            self.setSelection([])

    def deleteSelected(self) -> None:
        for instance in self._ui.renderArea.instanceSelection.all():
            self._git.remove(instance)
            self._ui.renderArea.instanceSelection.remove(instance)
        self.buildList()

    def duplicateSelected(self) -> None:
        ...
        self.buildList()

    def moveSelected(self, x: float, y: float) -> None:
        if self._ui.lockInstancesCheck.isChecked():
            return

        for instance in self._ui.renderArea.instanceSelection.all():
            instance.move(x, y, 0)

    def rotateSelected(self, angle: float) -> None:
        for instance in self._ui.renderArea.instanceSelection.all():
            instance.rotate(angle)

    def rotateSelectedToPoint(self, x: float, y: float) -> None:
        for instance in self._ui.renderArea.instanceSelection.all():
            rotation = -math.atan2(x - instance.position.x, y - instance.position.y)
            instance.rotate(-instance.yaw() + rotation, 0, 0)

    def moveCamera(self, x: float, y: float) -> None:
        self._ui.renderArea.camera.nudgePosition(x, y)

    def zoomCamera(self, amount: float) -> None:
        self._ui.renderArea.camera.nudgeZoom(amount)

    def rotateCamera(self, angle: float) -> None:
        self._ui.renderArea.camera.nudgeRotation(angle)
    # endregion


class _GeometryMode(_Mode):
    def __init__(self, editor: GITEditor, installation: HTInstallation, git: GIT):
        super(_GeometryMode, self).__init__(editor, installation, git)

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

    def insertPointAtMouse(self) -> None:
        screen = self._ui.renderArea.mapFromGlobal(self._editor.cursor().pos())
        world = self._ui.renderArea.toWorldCoords(screen.x(), screen.y())

        instance = self._ui.renderArea.instanceSelection.get(0)
        point = world - instance.position
        instance.geometry.points.append(point)

    # region Interface Methods
    def onItemSelectionChanged(self, item: QListWidgetItem) -> None:
        pass

    def onFilterEdited(self, text: str) -> None:
        pass

    def updateStatusBar(self, world: Vector2) -> None:
        instance = self._ui.renderArea.instanceSelection.last()
        if instance:
            self._editor.statusBar().showMessage("({:.1f}, {:.1f}) Editing Geometry of {}".format(world.x, world.y, instance.identifier().resname))

    def onRenderContextMenu(self, world: Vector2, screen: QPoint) -> None:
        menu = QMenu(self._editor)

        if not self._ui.renderArea.geometrySelection.isEmpty():
            menu.addAction("Remove").triggered.connect(self.deleteSelected)

        if self._ui.renderArea.geometrySelection.count() == 0:
            menu.addAction("Insert").triggered.connect(self.insertPointAtMouse)

        menu.addSeparator()
        menu.addAction("Finish Editing").triggered.connect(self._editor.enterInstanceMode)

        menu.popup(screen)

    def openListContextMenu(self, item: QListWidgetItem, screen: QPoint) -> None:
        pass

    def updateVisibility(self) -> None:
        pass

    def selectUnderneath(self) -> None:
        underMouse = self._ui.renderArea.geomPointsUnderMouse()
        selection = self._ui.renderArea.geometrySelection.all()

        # Do not change the selection if the selected instance if its still underneath the mouse
        if selection and selection[0] in underMouse:
            return

        if underMouse:
            self._ui.renderArea.geometrySelection.select(underMouse)
        else:
            self._ui.renderArea.geometrySelection.select([])

    def deleteSelected(self) -> None:
        vertex = self._ui.renderArea.geometrySelection.last()
        instance = vertex.instance
        instance.geometry.remove(vertex.point)

    def duplicateSelected(self) -> None:
        pass

    def moveSelected(self, x: float, y: float) -> None:
        for vertex in self._ui.renderArea.geometrySelection.all():
            vertex.point.x += x
            vertex.point.y += y

    def rotateSelected(self, angle: float) -> None:
        pass

    def rotateSelectedToPoint(self, x: float, y: float) -> None:
        pass

    def moveCamera(self, x: float, y: float) -> None:
        self._ui.renderArea.camera.nudgePosition(x, y)

    def zoomCamera(self, amount: float) -> None:
        self._ui.renderArea.camera.nudgeZoom(amount)

    def rotateCamera(self, angle: float) -> None:
        self._ui.renderArea.camera.nudgeRotation(angle)
    # endregion


class GITSettings:
    def __init__(self):
        self.settings = QSettings('HolocronToolset', 'GITEditor')

    def resetMaterialColors(self) -> None:
        self.settings.remove("undefinedMaterialColour")
        self.settings.remove("dirtMaterialColour")
        self.settings.remove("obscuringMaterialColour")
        self.settings.remove("grassMaterialColour")
        self.settings.remove("stoneMaterialColour")
        self.settings.remove("woodMaterialColour")
        self.settings.remove("waterMaterialColour")
        self.settings.remove("nonWalkMaterialColour")
        self.settings.remove("transparentMaterialColour")
        self.settings.remove("carpetMaterialColour")
        self.settings.remove("metalMaterialColour")
        self.settings.remove("puddlesMaterialColour")
        self.settings.remove("swampMaterialColour")
        self.settings.remove("mudMaterialColour")
        self.settings.remove("leavesMaterialColour")
        self.settings.remove("doorMaterialColour")
        self.settings.remove("lavaMaterialColour")
        self.settings.remove("bottomlessPitMaterialColour")
        self.settings.remove("deepWaterMaterialColour")
        self.settings.remove("nonWalkGrassMaterialColour")

    def resetControls(self) -> None:
        self.settings.remove("panCameraBind")
        self.settings.remove("rotateCameraBind")
        self.settings.remove("zoomCameraBind")
        self.settings.remove("rotateSelectedToPointBind")
        self.settings.remove("moveSelectedBind")
        self.settings.remove("selectUnderneathBind")
        self.settings.remove("deleteSelectedBind")

    # region Strings (Instance Labels)
    @property
    def creatureLabel(self) -> str:
        return self.settings.value("creatureLabel", "", str)

    @creatureLabel.setter
    def creatureLabel(self, value: str) -> None:
        self.settings.setValue('creatureLabel', value)

    @property
    def doorLabel(self) -> str:
        return self.settings.value("doorLabel", "", str)

    @doorLabel.setter
    def doorLabel(self, value: str) -> None:
        self.settings.setValue('doorLabel', value)

    @property
    def placeableLabel(self) -> str:
        return self.settings.value("placeableLabel", "", str)

    @placeableLabel.setter
    def placeableLabel(self, value: str) -> None:
        self.settings.setValue('placeableLabel', value)

    @property
    def storeLabel(self) -> str:
        return self.settings.value("storeLabel", "", str)

    @storeLabel.setter
    def storeLabel(self, value: str) -> None:
        self.settings.setValue('storeLabel', value)

    @property
    def soundLabel(self) -> str:
        return self.settings.value("soundLabel", "", str)

    @soundLabel.setter
    def soundLabel(self, value: str) -> None:
        self.settings.setValue('soundLabel', value)

    @property
    def waypointLabel(self) -> str:
        return self.settings.value("waypointLabel", "", str)

    @waypointLabel.setter
    def waypointLabel(self, value: str) -> None:
        self.settings.setValue('waypointLabel', value)

    @property
    def cameraLabel(self) -> str:
        return self.settings.value("cameraLabel", "", str)

    @cameraLabel.setter
    def cameraLabel(self, value: str) -> None:
        self.settings.setValue('cameraLabel', value)

    @property
    def encounterLabel(self) -> str:
        return self.settings.value("encounterLabel", "", str)

    @encounterLabel.setter
    def encounterLabel(self, value: str) -> None:
        self.settings.setValue('encounterLabel', value)

    @property
    def triggerLabel(self) -> str:
        return self.settings.value("triggerLabel", "", str)

    @triggerLabel.setter
    def triggerLabel(self, value: str) -> None:
        self.settings.setValue('triggerLabel', value)
    # endregion

    # region Ints (Material Colours)
    @property
    def undefinedMaterialColour(self) -> int:
        return self.settings.value("undefinedMaterialColour", 671088895, int)

    @undefinedMaterialColour.setter
    def undefinedMaterialColour(self, value: int) -> None:
        self.settings.setValue('undefinedMaterialColour', value)

    @property
    def dirtMaterialColour(self) -> int:
        return self.settings.value("dirtMaterialColour", 4281084972, int)

    @dirtMaterialColour.setter
    def dirtMaterialColour(self, value: int) -> None:
        self.settings.setValue('dirtMaterialColour', value)

    @property
    def obscuringMaterialColour(self) -> int:
        return self.settings.value("obscuringMaterialColour", 671088895, int)

    @obscuringMaterialColour.setter
    def obscuringMaterialColour(self, value: int) -> None:
        self.settings.setValue('obscuringMaterialColour', value)

    @property
    def grassMaterialColour(self) -> int:
        return self.settings.value("grassMaterialColour", 4281084972, int)

    @grassMaterialColour.setter
    def grassMaterialColour(self, value: int) -> None:
        self.settings.setValue('grassMaterialColour', value)

    @property
    def stoneMaterialColour(self) -> int:
        return self.settings.value("stoneMaterialColour", 4281084972, int)

    @stoneMaterialColour.setter
    def stoneMaterialColour(self, value: int) -> None:
        self.settings.setValue('stoneMaterialColour', value)

    @property
    def woodMaterialColour(self) -> int:
        return self.settings.value("woodMaterialColour", 4281084972, int)

    @woodMaterialColour.setter
    def woodMaterialColour(self, value: int) -> None:
        self.settings.setValue('woodMaterialColour', value)

    @property
    def waterMaterialColour(self) -> int:
        return self.settings.value("waterMaterialColour", 4281084972, int)

    @waterMaterialColour.setter
    def waterMaterialColour(self, value: int) -> None:
        self.settings.setValue('waterMaterialColour', value)

    @property
    def nonWalkMaterialColour(self) -> int:
        return self.settings.value("nonWalkMaterialColour", 671088895, int)

    @nonWalkMaterialColour.setter
    def nonWalkMaterialColour(self, value: int) -> None:
        self.settings.setValue('nonWalkMaterialColour', value)

    @property
    def transparentMaterialColour(self) -> int:
        return self.settings.value("transparentMaterialColour", 671088895, int)

    @transparentMaterialColour.setter
    def transparentMaterialColour(self, value: int) -> None:
        self.settings.setValue('transparentMaterialColour', value)

    @property
    def carpetMaterialColour(self) -> int:
        return self.settings.value("carpetMaterialColour", 4281084972, int)

    @carpetMaterialColour.setter
    def carpetMaterialColour(self, value: int) -> None:
        self.settings.setValue('carpetMaterialColour', value)

    @property
    def metalMaterialColour(self) -> int:
        return self.settings.value("metalMaterialColour", 4281084972, int)

    @metalMaterialColour.setter
    def metalMaterialColour(self, value: int) -> None:
        self.settings.setValue('metalMaterialColour', value)

    @property
    def puddlesMaterialColour(self) -> int:
        return self.settings.value("puddlesMaterialColour", 4281084972, int)

    @puddlesMaterialColour.setter
    def puddlesMaterialColour(self, value: int) -> None:
        self.settings.setValue('puddlesMaterialColour', value)

    @property
    def swampMaterialColour(self) -> int:
        return self.settings.value("swampMaterialColour", 4281084972, int)

    @swampMaterialColour.setter
    def swampMaterialColour(self, value: int) -> None:
        self.settings.setValue('swampMaterialColour', value)

    @property
    def mudMaterialColour(self) -> int:
        return self.settings.value("mudMaterialColour", 4281084972, int)

    @mudMaterialColour.setter
    def mudMaterialColour(self, value: int) -> None:
        self.settings.setValue('mudMaterialColour', value)

    @property
    def leavesMaterialColour(self) -> int:
        return self.settings.value("leavesMaterialColour", 4281084972, int)

    @leavesMaterialColour.setter
    def leavesMaterialColour(self, value: int) -> None:
        self.settings.setValue('leavesMaterialColour', value)

    @property
    def doorMaterialColour(self) -> int:
        return self.settings.value("doorMaterialColour", 4281084972, int)

    @doorMaterialColour.setter
    def doorMaterialColour(self, value: int) -> None:
        self.settings.setValue('doorMaterialColour', value)

    @property
    def lavaMaterialColour(self) -> int:
        return self.settings.value("lavaMaterialColour", 671088895, int)

    @lavaMaterialColour.setter
    def lavaMaterialColour(self, value: int) -> None:
        self.settings.setValue('lavaMaterialColour', value)

    @property
    def bottomlessPitMaterialColour(self) -> int:
        return self.settings.value("bottomlessPitMaterialColour", 671088895, int)

    @bottomlessPitMaterialColour.setter
    def bottomlessPitMaterialColour(self, value: int) -> None:
        self.settings.setValue('bottomlessPitMaterialColour', value)

    @property
    def deepWaterMaterialColour(self) -> int:
        return self.settings.value("deepWaterMaterialColour", 671088895, int)

    @deepWaterMaterialColour.setter
    def deepWaterMaterialColour(self, value: int) -> None:
        self.settings.setValue('deepWaterMaterialColour', value)

    @property
    def nonWalkGrassMaterialColour(self) -> int:
        return self.settings.value("nonWalkGrassMaterialColour", 671088895, int)

    @nonWalkGrassMaterialColour.setter
    def nonWalkGrassMaterialColour(self, value: int) -> None:
        self.settings.setValue('nonWalkGrassMaterialColour', value)
    # endregion

    # region Binds (Controls)
    @property
    def panCameraBind(self) -> Bind:
        return self.settings.value("panCameraBind", ({QtCore.Qt.Key_Control}, {QtCore.Qt.LeftButton}))

    @panCameraBind.setter
    def panCameraBind(self, value: Bind) -> None:
        self.settings.setValue('panCameraBind', value)

    @property
    def rotateCameraBind(self) -> Bind:
        return self.settings.value("rotateCameraBind", ({QtCore.Qt.Key_Control}, {QtCore.Qt.MiddleButton}))

    @rotateCameraBind.setter
    def rotateCameraBind(self, value: Bind) -> None:
        self.settings.setValue('rotateCameraBind', value)

    @property
    def zoomCameraBind(self) -> Bind:
        return self.settings.value("zoomCameraBind", ({QtCore.Qt.Key_Control}, None))

    @zoomCameraBind.setter
    def zoomCameraBind(self, value: Bind) -> None:
        self.settings.setValue('zoomCameraBind', value)

    @property
    def rotateSelectedToPointBind(self) -> Bind:
        return self.settings.value("rotateSelectedToPoint", (set(), {QtCore.Qt.MiddleButton}))

    @rotateSelectedToPointBind.setter
    def rotateSelectedToPointBind(self, value: Bind) -> None:
        self.settings.setValue('rotateSelectedToPoint', value)

    @property
    def moveSelectedBind(self) -> Bind:
        return self.settings.value("moveSelectedBind", (set(), {QtCore.Qt.LeftButton}))

    @moveSelectedBind.setter
    def moveSelectedBind(self, value: Bind) -> None:
        self.settings.setValue('moveSelectedBind', value)

    @property
    def selectUnderneathBind(self) -> Bind:
        return self.settings.value("selectUnderneathBind", (set(), {QtCore.Qt.LeftButton}))

    @selectUnderneathBind.setter
    def selectUnderneathBind(self, value: Bind) -> None:
        self.settings.setValue('selectUnderneathBind', value)

    @property
    def deleteSelectedBind(self) -> Bind:
        return self.settings.value("deleteSelectedBind", ({QtCore.Qt.Key_Delete}, None))

    @deleteSelectedBind.setter
    def deleteSelectedBind(self, value: Bind) -> None:
        self.settings.setValue('deleteSelectedBind', value)
    # endregion


class GITControlScheme:
    def __init__(self, editor: GITEditor):
        self.editor: GITEditor = editor
        self.settings: GITSettings = GITSettings()

        self.panCamera: GITControlItem = GITControlItem(self.settings.panCameraBind)
        self.rotateCamera: GITControlItem = GITControlItem(self.settings.rotateCameraBind)
        self.zoomCamera: GITControlItem = GITControlItem(self.settings.zoomCameraBind)
        self.rotateSelectedToPoint: GITControlItem = GITControlItem(self.settings.rotateSelectedToPointBind)
        self.moveSelected: GITControlItem = GITControlItem(self.settings.moveSelectedBind)
        self.selectUnderneath: GITControlItem = GITControlItem(self.settings.selectUnderneathBind)
        self.deleteSelected: GITControlItem = GITControlItem(self.settings.deleteSelectedBind)

    def onMouseScrolled(self, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        if self.zoomCamera.satisfied(buttons, keys):
            self.editor.zoomCamera(delta.y / 50)

    def onMouseMoved(self, screen: Vector2, screenDelta: Vector2, world: Vector2, worldDelta: Vector2,
                     buttons: Set[int], keys: Set[int]) -> None:
        if self.panCamera.satisfied(buttons, keys):
            self.editor.moveCamera(-worldDelta.x, -worldDelta.y)
        if self.rotateCamera.satisfied(buttons, keys):
            self.editor.rotateCamera(screenDelta.y)
        if self.moveSelected.satisfied(buttons, keys):
            self.editor.moveSelected(worldDelta.x, worldDelta.y)
        if self.rotateSelectedToPoint.satisfied(buttons, keys):
            self.editor.rotateSelectedToPoint(world.x, world.y)

    def onMousePressed(self, screen: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        if self.selectUnderneath.satisfied(buttons, keys):
            self.editor.selectUnderneath()

    def onMouseReleased(self, screen: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        ...

    def onKeyboardPressed(self, buttons: Set[int], keys: Set[int]) -> None:
        if self.deleteSelected.satisfied(buttons, keys):
            self.editor.deleteSelected()

    def onKeyboardReleased(self, buttons: Set[int], keys: Set[int]) -> None:
        ...


class GITControlItem:
    def __init__(self, bind: Bind):
        self.keys: Set[int] = bind[0]
        self.mouse: Set[int] = bind[1]

    def satisfied(self, buttons: Set[int], keys: Set[int]) -> bool:
        return (self.mouse == buttons or self.mouse is None) and (self.keys == keys or self.keys is None)
