from __future__ import annotations

import math
from abc import ABC, abstractmethod
from contextlib import suppress
from copy import deepcopy
from typing import Optional, Set, Dict

from PyQt5 import QtCore
from PyQt5.QtCore import QPoint, QSettings
from PyQt5.QtGui import QIcon, QColor, QKeySequence, QKeyEvent
from PyQt5.QtWidgets import QWidget, QMenu, QListWidgetItem, QCheckBox, QDialog
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

    dialog.exec_()
    return dialog


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
        self._mode: _Mode = _InstanceMode(self, installation)
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
        self.ui.renderArea.customContextMenuRequested.connect(self.onContextMenu)

        self.ui.filterEdit.textEdited.connect(self.onFilterEdited)
        self.ui.listWidget.itemSelectionChanged.connect(self.onItemSelectionChanged)
        self.ui.listWidget.customContextMenuRequested.connect(self.onItemContextMenu)

        self.ui.viewCreatureCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewPlaceableCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewDoorCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewSoundCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewTriggerCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewEncounterCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewWaypointCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewCameraCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewStoreCheck.toggled.connect(self.updateInstanceVisibility)

        self.ui.viewCreatureCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick(self.ui.viewCreatureCheck)
        self.ui.viewPlaceableCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick(self.ui.viewPlaceableCheck)
        self.ui.viewDoorCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick(self.ui.viewDoorCheck)
        self.ui.viewSoundCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick(self.ui.viewSoundCheck)
        self.ui.viewTriggerCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick(self.ui.viewTriggerCheck)
        self.ui.viewEncounterCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick(self.ui.viewEncounterCheck)
        self.ui.viewWaypointCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick(self.ui.viewWaypointCheck)
        self.ui.viewCameraCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick(self.ui.viewCameraCheck)
        self.ui.viewStoreCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick(self.ui.viewStoreCheck)

        # Edit
        self.ui.actionDeleteSelected.triggered.connect(lambda: self._mode.removeSelected())
        # View
        self.ui.actionZoomIn.triggered.connect(lambda: self.ui.renderArea.camera.nudgeZoom(1))
        self.ui.actionZoomOut.triggered.connect(lambda: self.ui.renderArea.camera.nudgeZoom(-1))
        self.ui.actionRecentreCamera.triggered.connect(lambda: self.ui.renderArea.centerCamera())
        # View -> Creature Labels
        self.ui.actionUseCreatureResRef.triggered.connect(lambda: setattr(self.settings, "creatureLabel", "resref"))
        self.ui.actionUseCreatureResRef.triggered.connect(self.updateInstanceVisibility)
        self.ui.actionUseCreatureTag.triggered.connect(lambda: setattr(self.settings, "creatureLabel", "tag"))
        self.ui.actionUseCreatureTag.triggered.connect(self.updateInstanceVisibility)
        self.ui.actionUseCreatureName.triggered.connect(lambda: setattr(self.settings, "creatureLabel", "name"))
        self.ui.actionUseCreatureName.triggered.connect(self.updateInstanceVisibility)
        # View -> Door Labels
        self.ui.actionUseDoorResRef.triggered.connect(lambda: setattr(self.settings, "doorLabel", "resref"))
        self.ui.actionUseDoorResRef.triggered.connect(self.updateInstanceVisibility)
        self.ui.actionUseDoorTag.triggered.connect(lambda: setattr(self.settings, "doorLabel", "tag"))
        self.ui.actionUseDoorTag.triggered.connect(self.updateInstanceVisibility)
        self.ui.actionUseDoorResName.triggered.connect(lambda: setattr(self.settings, "doorLabel", "res_name"))
        self.ui.actionUseDoorResName.triggered.connect(self.updateInstanceVisibility)
        self.ui.actionUseDoorResTag.triggered.connect(lambda: setattr(self.settings, "doorLabel", "res_tag"))
        self.ui.actionUseDoorResTag.triggered.connect(self.updateInstanceVisibility)
        # View -> Placeable Labels
        self.ui.actionUsePlaceableResRef.triggered.connect(lambda: setattr(self.settings, "placeableLabel", "resref"))
        self.ui.actionUsePlaceableResRef.triggered.connect(self.updateInstanceVisibility)
        self.ui.actionUsePlaceableResName.triggered.connect(lambda: setattr(self.settings, "placeableLabel", "res_name"))
        self.ui.actionUsePlaceableResName.triggered.connect(self.updateInstanceVisibility)
        self.ui.actionUsePlaceableResTag.triggered.connect(lambda: setattr(self.settings, "placeableLabel", "res_tag"))
        self.ui.actionUsePlaceableResTag.triggered.connect(self.updateInstanceVisibility)
        # View -> Merchant Labels
        self.ui.actionUseMerchantResRef.triggered.connect(lambda: setattr(self.settings, "storeLabel", "resref"))
        self.ui.actionUseMerchantResRef.triggered.connect(self.updateInstanceVisibility)
        self.ui.actionUseMerchantResName.triggered.connect(lambda: setattr(self.settings, "storeLabel", "res_name"))
        self.ui.actionUseMerchantResName.triggered.connect(self.updateInstanceVisibility)
        self.ui.actionUseMerchantResTag.triggered.connect(lambda: setattr(self.settings, "storeLabel", "res_tag"))
        self.ui.actionUseMerchantResTag.triggered.connect(self.updateInstanceVisibility)
        # View -> Sound Labels
        self.ui.actionUseSoundResRef.triggered.connect(lambda: setattr(self.settings, "soundLabel", "resref"))
        self.ui.actionUseSoundResRef.triggered.connect(self.updateInstanceVisibility)
        self.ui.actionUseSoundResName.triggered.connect(lambda: setattr(self.settings, "soundLabel", "res_name"))
        self.ui.actionUseSoundResName.triggered.connect(self.updateInstanceVisibility)
        self.ui.actionUseSoundResTag.triggered.connect(lambda: setattr(self.settings, "soundLabel", "res_tag"))
        self.ui.actionUseSoundResTag.triggered.connect(self.updateInstanceVisibility)
        # View -> Waypoint Labels
        self.ui.actionUseWaypointResRef.triggered.connect(lambda: setattr(self.settings, "waypointLabel", "resref"))
        self.ui.actionUseWaypointResRef.triggered.connect(self.updateInstanceVisibility)
        self.ui.actionUseWaypointName.triggered.connect(lambda: setattr(self.settings, "waypointLabel", "name"))
        self.ui.actionUseWaypointName.triggered.connect(self.updateInstanceVisibility)
        self.ui.actionUseWaypointTag.triggered.connect(lambda: setattr(self.settings, "waypointLabel", "tag"))
        self.ui.actionUseWaypointTag.triggered.connect(self.updateInstanceVisibility)
        self.ui.actionUseWaypointResName.triggered.connect(lambda: setattr(self.settings, "waypointLabel", "res_name"))
        self.ui.actionUseWaypointResName.triggered.connect(self.updateInstanceVisibility)
        self.ui.actionUseWaypointResTag.triggered.connect(lambda: setattr(self.settings, "waypointLabel", "res_tag"))
        self.ui.actionUseWaypointResTag.triggered.connect(self.updateInstanceVisibility)
        # View -> Encounter Labels
        self.ui.actionUseEncounterResRef.triggered.connect(lambda: setattr(self.settings, "encounterLabel", "resref"))
        self.ui.actionUseEncounterResRef.triggered.connect(self.updateInstanceVisibility)
        self.ui.actionUseEncounterResName.triggered.connect(lambda: setattr(self.settings, "encounterLabel", "res_name"))
        self.ui.actionUseEncounterResName.triggered.connect(self.updateInstanceVisibility)
        self.ui.actionUseEncounterResTag.triggered.connect(lambda: setattr(self.settings, "encounterLabel", "res_tag"))
        self.ui.actionUseEncounterResTag.triggered.connect(self.updateInstanceVisibility)
        # View -> Trigger Labels
        self.ui.actionUseTriggerResRef.triggered.connect(lambda: setattr(self.settings, "triggerLabel", "resref"))
        self.ui.actionUseTriggerResRef.triggered.connect(self.updateInstanceVisibility)
        self.ui.actionUseTriggerTag.triggered.connect(lambda: setattr(self.settings, "triggerLabel", "tag"))
        self.ui.actionUseTriggerTag.triggered.connect(self.updateInstanceVisibility)
        self.ui.actionUseTriggerResName.triggered.connect(lambda: setattr(self.settings, "triggerLabel", "res_name"))
        self.ui.actionUseTriggerResName.triggered.connect(self.updateInstanceVisibility)
        self.ui.actionUseTriggerResTag.triggered.connect(lambda: setattr(self.settings, "triggerLabel", "res_tag"))
        self.ui.actionUseTriggerResTag.triggered.connect(self.updateInstanceVisibility)

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
            findBWM = self._installation.resource(room.model, ResourceType.WOK, order)
            if findBWM is not None:
                walkmeshes.append(read_bwm(findBWM.data))

        self.ui.renderArea.setWalkmeshes(walkmeshes)

    def git(self) -> GIT:
        return self._git

    def setMode(self, mode: _Mode) -> None:
        self._mode = mode

    def removeSelected(self) -> None:
        self._mode.removeSelected()

    def updateStatusBar(self) -> None:
        self._mode.updateStatusBar()

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

    # region Instance State Events
    def updateInstanceVisibility(self) -> None:
        self._mode.updateInstanceVisibility()

    def onContextMenu(self, point: QPoint) -> None:
        self._mode.onContextMenu(point)

    def onFilterEdited(self) -> None:
        self._mode.onFilterEdited()

    def onItemSelectionChanged(self) -> None:
        self._mode.onItemSelectionChanged()

    def onItemContextMenu(self, point: QPoint) -> None:
        self._mode.onItemContextMenu(point)

    def onMouseMoved(self, screen: Vector2, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        self._mode.onMouseMoved(screen, delta, buttons, keys)

    def onMouseScrolled(self, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        self._mode.onMouseScrolled(delta, buttons, keys)

    def onMousePressed(self, screen: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        self._mode.onMousePressed(screen, buttons, keys)

    def keyPressEvent(self, e: QKeyEvent) -> None:
        super().keyPressEvent(e)
        self.ui.renderArea.keyPressEvent(e)

    def keyReleaseEvent(self, e: QKeyEvent) -> None:
        super().keyPressEvent(e)
        self.ui.renderArea.keyReleaseEvent(e)
    # endregion


class _Mode(ABC):
    def __init__(self, editor: GITEditor, installation: HTInstallation):
        self._editor: GITEditor = editor
        self._installation: HTInstallation = installation

        from toolset.uic.editors import git
        self._ui: git = editor.ui

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
    def onFilterEdited(self) -> None:
        ...

    @abstractmethod
    def onItemSelectionChanged(self) -> None:
        ...

    @abstractmethod
    def onItemContextMenu(self, point: QPoint) -> None:
        ...


class _InstanceMode(_Mode):
    def __init__(self, editor: GITEditor, installation: HTInstallation):
        super(_InstanceMode, self).__init__(editor, installation)
        self._ui.renderArea.hideGeomPoints = True
        self.updateInstanceVisibility()

    def _getBufferedName(self, resid: ResourceIdentifier) -> str:
        if resid not in self._editor.nameBuffer:
            res = self._installation.resource(resid.resname, resid.restype)
            if res is not None:
                self._editor.nameBuffer[resid] = self._installation.string(extract_name(res.data))
        return self._editor.nameBuffer[resid] if resid in self._editor.nameBuffer else resid.resname

    def _getBufferedTag(self, resid: ResourceIdentifier) -> str:
        if resid not in self._editor.tagBuffer:
            res = self._installation.resource(resid.resname, resid.restype)
            if res is not None:
                self._editor.tagBuffer[resid] = extract_tag(res.data)
        return self._editor.tagBuffer[resid] if resid in self._editor.tagBuffer else resid.resname

    def getInstanceLabel(self, instance: GITInstance) -> str:
        resid = None if instance.identifier() is None else instance.identifier()

        if isinstance(instance, GITCamera):
            label = "ID " + str(instance.camera_id)
        else:
            label = resid.resname

        if isinstance(instance, GITCreature):
            if self._editor.settings.creatureLabel == "tag":
                label = self._getBufferedTag(resid)
            elif self._editor.settings.creatureLabel == "name":
                label = self._getBufferedName(resid)
        elif isinstance(instance, GITDoor):
            if self._editor.settings.doorLabel == "tag":
                label = instance.tag
            elif self._editor.settings.doorLabel == "res_name":
                label = self._getBufferedName(resid)
            elif self._editor.settings.doorLabel == "res_tag":
                label = self._getBufferedTag(resid)
        elif isinstance(instance, GITPlaceable):
            if self._editor.settings.placeableLabel == "res_name":
                label = self._getBufferedName(resid)
            elif self._editor.settings.placeableLabel == "res_tag":
                label = self._getBufferedTag(resid)
        elif isinstance(instance, GITStore):
            if self._editor.settings.storeLabel == "res_name":
                label = self._getBufferedName(resid)
            elif self._editor.settings.storeLabel == "res_tag":
                label = self._getBufferedTag(resid)
        elif isinstance(instance, GITSound):
            if self._editor.settings.soundLabel == "res_name":
                label = self._getBufferedName(resid)
            elif self._editor.settings.soundLabel == "res_tag":
                label = self._getBufferedTag(resid)
        elif isinstance(instance, GITWaypoint):
            if self._editor.settings.waypointLabel == "tag":
                label = instance.tag
            elif self._editor.settings.waypointLabel == "name":
                label = self._installation.string(instance.name)
            elif self._editor.settings.waypointLabel == "res_name":
                label = self._getBufferedName(resid)
            elif self._editor.settings.waypointLabel == "res_tag":
                label = self._getBufferedTag(resid)
        elif isinstance(instance, GITEncounter):
            if self._editor.settings.encounterLabel == "res_name":
                label = self._getBufferedName(resid)
            elif self._editor.settings.encounterLabel == "res_tag":
                label = self._getBufferedTag(resid)
        elif isinstance(instance, GITTrigger):
            if self._editor.settings.triggerLabel == "tag":
                label = instance.tag
            elif self._editor.settings.triggerLabel == "res_name":
                label = self._getBufferedName(resid)
            elif self._editor.settings.triggerLabel == "res_tag":
                label = self._getBufferedTag(resid)

        return "{}".format(label)

    def getInstanceTooltip(self, instance: GITInstance) -> str:
        index = self._editor.git().index(instance)

        if isinstance(instance, GITCamera):
            return "Camera ID: {}\nList Index: {}".format(
                instance.camera_id,
                index)
        elif isinstance(instance, GITCreature):
            return "ResRef: {}\nList Index: {}".format(
                instance.identifier().resname,
                index)
        elif isinstance(instance, GITDoor):
            return "ResRef: {}\nTag (GIT): {}\nList Index: {}\n".format(
                instance.identifier().resname,
                instance.tag,
                index)
        elif isinstance(instance, GITStore):
            return "ResRef: {}\nList Index: {}".format(
                instance.identifier().resname,
                index)
        elif isinstance(instance, GITSound):
            return "ResRef: {}\nList Index: {}".format(
                instance.identifier().resname,
                index)
        elif isinstance(instance, GITWaypoint):
            return "ResRef: {}\nTag (GIT): {}\nList Index: {}".format(
                instance.identifier().resname,
                instance.tag,
                index)
        elif isinstance(instance, GITEncounter):
            return "ResRef: {}\nSpawn Count: {}\nList Index: {}".format(
                instance.identifier().resname,
                len(instance.spawn_points),
                index)
        elif isinstance(instance, GITTrigger):
            return "ResRef: {}\nTag (GIT): {}\nList Index: {}".format(
                instance.identifier().resname,
                instance.tag,
                index)

    def updateStatusBar(self) -> None:
        screen = self._ui.renderArea.mapFromGlobal(self._editor.cursor().pos())
        world = self._ui.renderArea.toWorldCoords(screen.x(), screen.y())

        reference = ""
        if self._ui.renderArea.instancesUnderMouse():
            instance = self._ui.renderArea.instancesUnderMouse()[0]
            reference = "" if instance.identifier() is None else instance.identifier().resname

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

        def instanceSort(inst):
            textToSort = str(inst.camera_id) if isinstance(inst, GITCamera) else inst.identifier().resname.lower()
            textToSort = textToSort if isinstance(inst, GITCamera) else inst.identifier().restype.extension + textToSort
            return textToSort

        instances = self._editor.git().instances()
        instances = sorted(instances, key=instanceSort)

        for instance in instances:
            filterSource = str(instance.camera_id) if isinstance(instance, GITCamera) else instance.identifier().resname
            isVisible = self._ui.renderArea.isInstanceVisible(instance)
            isFiltered = self._ui.filterEdit.text() in filterSource

            if isVisible and isFiltered:
                icon = QIcon(self._ui.renderArea.instancePixmap(instance))
                text = self.getInstanceLabel(instance)
                item = QListWidgetItem(icon, text)
                item.setData(QtCore.Qt.UserRole, instance)
                item.setToolTip(self.getInstanceTooltip(instance))
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
        for instance in self._ui.renderArea.instanceSelection.all():
            self._editor.git().remove(instance)
        self._ui.renderArea.instanceSelection.clear()
        self.rebuildInstanceList()

    def addInstance(self, instance: GITInstance):
        self._editor.git().add(instance)
        self.rebuildInstanceList()

    def editSelectedInstance(self) -> None:
        instance = self._ui.renderArea.instanceSelection.get(0)
        openInstanceDialog(self._editor, instance, self._installation)
        self.rebuildInstanceList()

    def editResource(self, instance: GITInstance) -> None:
        res = self._installation.resource(instance.identifier().resname, instance.identifier().restype)
        if not res:
            filepath = "{}/{}.{}".format(self._installation.override_path(), instance.identifier().resname, instance.identifier().restype.extension)
            with open(filepath, "wb") as f:
                f.write(instance.blank())
            self._installation.reload_override("")
            res = self._installation.resource(instance.identifier().resname, instance.identifier().restype)
        openResourceEditor(res.filepath, res.resname, res.restype, res.data, self._installation, self._editor)

    def onMouseMoved(self, screen: Vector2, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        worldDelta = self._ui.renderArea.toWorldDelta(delta.x, delta.y)
        world = self._ui.renderArea.toWorldCoords(screen.x, screen.y)

        if QtCore.Qt.LeftButton in buttons and QtCore.Qt.Key_Control in keys:
            self._ui.renderArea.camera.nudgePosition(-worldDelta.x, -worldDelta.y)
        elif QtCore.Qt.MiddleButton in buttons and QtCore.Qt.Key_Control in keys:
            self._ui.renderArea.camera.nudgeRotation(delta.x / 50)
        elif QtCore.Qt.LeftButton in buttons and not QtCore.Qt.Key_Control in keys and not self._ui.lockInstancesCheck.isChecked():
            for instance in self._ui.renderArea.instanceSelection.all():
                instance.move(worldDelta.x, worldDelta.y, 0.0)
                # Snap the instance on top of the walkmesh, if there is no walkmesh underneath it will snap Z to 0
                getZ = self._ui.renderArea.getZCoord(instance.position.x, instance.position.y)
                instance.position.z = getZ if getZ != 0.0 else instance.position.z
        elif QtCore.Qt.MiddleButton in buttons:
            if not self._ui.renderArea.instanceSelection.isEmpty():
                instance = self._ui.renderArea.instanceSelection.get(0)
                rotation = -math.atan2(world.x - instance.position.x, world.y - instance.position.y)
                instance.rotate(-instance.yaw() + rotation, 0, 0)

        self.updateStatusBar()

    def onMousePressed(self, screen: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        underMouse = self._ui.renderArea.instancesUnderMouse()
        currentSelection = self._ui.renderArea.instanceSelection.all()

        if QtCore.Qt.LeftButton in buttons and QtCore.Qt.Key_Alt in keys:
            if self._ui.renderArea.instancesUnderMouse():
                original = self._ui.renderArea.instancesUnderMouse()[0]
                duplicate = deepcopy(original)
                self._editor.git().add(duplicate)
                self.rebuildInstanceList()
                self.selectInstanceItem(original)
        elif QtCore.Qt.LeftButton in buttons:
            # Do not change the selection if the selected instance if its still underneath the mouse
            if currentSelection and currentSelection[0] in underMouse:
                return

            self._ui.renderArea.instanceSelection.clear()
            if self._ui.renderArea.instancesUnderMouse():
                instance = self._ui.renderArea.instancesUnderMouse()[0]
                self._ui.renderArea.instanceSelection.select([instance])
                self.selectInstanceItem(instance)

    def onMouseScrolled(self, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        if QtCore.Qt.Key_Control in keys:
            self._ui.renderArea.camera.nudgeZoom(delta.y / 50)

    def onContextMenu(self, point: QPoint) -> None:
        menu = QMenu(self._editor)
        world = self._ui.renderArea.toWorldCoords(point.x(), point.y())

        # Show "Remove" action if instances are selected
        if not self._ui.renderArea.instanceSelection.isEmpty():
            menu.addAction("Remove").triggered.connect(self.removeSelected)

        # Show "Edit Instance"+"Edit Geometry" action if a single instance is selected
        if self._ui.renderArea.instanceSelection.count() == 1:
            instance = self._ui.renderArea.instanceSelection.get(0)

            menu.addAction("Edit Instance").triggered.connect(self.editSelectedInstance)

            actionEditResource = menu.addAction("Edit Resource")
            actionEditResource.triggered.connect(lambda: self.editResource(instance))
            actionEditResource.setEnabled(not isinstance(instance, GITCamera))
            menu.addAction(actionEditResource)

            if isinstance(instance, GITEncounter) or isinstance(instance, GITTrigger):
                menu.addAction("Edit Geometry").triggered.connect(lambda: self._editor.setMode(_GeometryMode(self._editor, self._installation)))

        # If no instances are selected then show the actions to add new instances
        if self._ui.renderArea.instanceSelection.count() == 0:
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

        menu.addSeparator()

        # If there are instances under the mouse, add actions for each one of them. If the player triggers on of them
        # the selection will change appropriately.
        for instance in self._ui.renderArea.instancesUnderMouse():
            icon = QIcon(self._ui.renderArea.instancePixmap(instance))
            reference = "" if instance.identifier() is None else instance.identifier().resname
            index = self._editor.git().index(instance)
            onTriggered = lambda checked, inst=instance: self._ui.renderArea.selectInstance(inst)
            menu.addAction(icon, "[{}] {}".format(index, reference)).triggered.connect(onTriggered)

        menu.popup(self._ui.renderArea.mapToGlobal(point))

    def onFilterEdited(self) -> None:
        self._ui.renderArea.instanceFilter = self._ui.filterEdit.text()
        self.rebuildInstanceList()

    def onItemSelectionChanged(self) -> None:
        if self._ui.listWidget.selectedItems():
            item = self._ui.listWidget.selectedItems()[0]
            instance = item.data(QtCore.Qt.UserRole)
            self._ui.renderArea.camera.setPosition(instance.position.x, instance.position.y)
            self._ui.renderArea.selectInstance(instance)

    def onItemContextMenu(self, point: QPoint) -> None:
        if not self._ui.listWidget.selectedItems():
            return

        instance = self._ui.listWidget.selectedItems()[0].data(QtCore.Qt.UserRole)
        menu = QMenu(self._ui.listWidget)

        menu.addAction("Remove").triggered.connect(self.removeSelected)
        menu.addAction("Edit Instance").triggered.connect(self.editSelectedInstance)

        actionEditResource = menu.addAction("Edit Resource")
        actionEditResource.triggered.connect(lambda: self.editResource(instance))
        actionEditResource.setEnabled(not isinstance(instance, GITCamera))
        menu.addAction(actionEditResource)

        menu.popup(self._ui.listWidget.mapToGlobal(point))


class _GeometryMode(_Mode):
    def __init__(self, editor: GITEditor, installation: HTInstallation):
        super(_GeometryMode, self).__init__(editor, installation)

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
        geomPoints = self._ui.renderArea.geometrySelection.all()
        for geomPoint in geomPoints:
            geomPoint.instance.geometry.remove(geomPoint.point)

    def insertPointAtMouse(self) -> None:
        screen = self._ui.renderArea.mapFromGlobal(self._editor.cursor().pos())
        world = self._ui.renderArea.toWorldCoords(screen.x(), screen.y())

        instance = self._ui.renderArea.instanceSelection.get(0)
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
                instance = self._ui.renderArea.instanceSelection.get(0)
                pointIndex = instance.geometry.points.index(self._ui.renderArea.geomPointsUnderMouse()[0].point)

        statusFormat = "Mode: Geometry Mode, X: {:.2f}, Y: {:.2f}, Z: {:.2f}, Point: {}"
        status = statusFormat.format(world.x, world.y, world.z, pointIndex)

        self._editor.statusBar().showMessage(status)

    def updateInstanceVisibility(self) -> None:
        ...

    def onMouseMoved(self, screen: Vector2, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        worldDelta = self._ui.renderArea.toWorldDelta(delta.x, delta.y)

        if QtCore.Qt.LeftButton in buttons and QtCore.Qt.Key_Control in keys:
            self._ui.renderArea.camera.nudgePosition(-worldDelta.x, -worldDelta.y)
        elif QtCore.Qt.MiddleButton in buttons and QtCore.Qt.Key_Control in keys:
            self._ui.renderArea.camera.nudgeRotation(delta.x / 50)
        elif QtCore.Qt.LeftButton in buttons and not QtCore.Qt.Key_Control in keys and self._ui.renderArea.geometrySelection.all():
            instance, point = self._ui.renderArea.geometrySelection.get(0)
            point.x += worldDelta.x
            point.y += worldDelta.y
            point.z = self._ui.renderArea.toWorldCoords(instance.position.x, instance.position.y).z

        self.updateStatusBar()

    def onMousePressed(self, screen: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        if self._ui.renderArea.geomPointsUnderMouse():
            point = self._ui.renderArea.geomPointsUnderMouse()[0]
            self._ui.renderArea.geometrySelection.select([point])
        else:
            self._ui.renderArea.geometrySelection.clear()

    def onMouseScrolled(self, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        if QtCore.Qt.Key_Control in keys:
            self._ui.renderArea.camera.nudgeZoom(delta.y / 50)

    def onContextMenu(self, point: QPoint) -> None:
        menu = QMenu(self._editor)

        if not self._ui.renderArea.geometrySelection.isEmpty():
            menu.addAction("Remove").triggered.connect(self.removeSelected)

        if self._ui.renderArea.geometrySelection.count() == 1:
            menu.addAction("Edit").triggered.connect(self.editSelectedPoint)

        if self._ui.renderArea.geometrySelection.count() == 0:
            menu.addAction("Insert").triggered.connect(self.insertPointAtMouse)

        menu.addSeparator()
        menu.addAction("Finish Editing").triggered.connect(lambda: self._editor.setMode(_InstanceMode(self._editor, self._installation)))

        menu.popup(self._ui.renderArea.mapToGlobal(point))

    def onFilterEdited(self) -> None:
        ...

    def onItemSelectionChanged(self) -> None:
        ...

    def onItemContextMenu(self, point: QPoint) -> None:
        ...


class GITSettings:
    def __init__(self):
        self.settings = QSettings('HolocronToolset', 'GITEditor')

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
