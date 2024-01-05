from __future__ import annotations

import math
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import TYPE_CHECKING

from pykotor.common.geometry import SurfaceMaterial, Vector2, Vector3
from pykotor.common.misc import Color
from pykotor.common.module import Module
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.bwm import read_bwm
from pykotor.resource.formats.lyt import LYT, read_lyt
from pykotor.resource.generics.git import (
    GIT,
    GITCamera,
    GITCreature,
    GITDoor,
    GITEncounter,
    GITInstance,
    GITPlaceable,
    GITSound,
    GITStore,
    GITTrigger,
    GITWaypoint,
    bytes_git,
    read_git,
)
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_rim_file
from pykotor.tools.template import extract_name, extract_tag
from PyQt5 import QtCore
from PyQt5.QtGui import QColor, QIcon, QKeyEvent, QKeySequence
from PyQt5.QtWidgets import QCheckBox, QDialog, QListWidgetItem, QMenu, QWidget
from toolset.data.misc import ControlItem
from toolset.gui.dialogs.instance.camera import CameraDialog
from toolset.gui.dialogs.instance.creature import CreatureDialog
from toolset.gui.dialogs.instance.door import DoorDialog
from toolset.gui.dialogs.instance.encounter import EncounterDialog
from toolset.gui.dialogs.instance.placeable import PlaceableDialog
from toolset.gui.dialogs.instance.sound import SoundDialog
from toolset.gui.dialogs.instance.store import StoreDialog
from toolset.gui.dialogs.instance.trigger import TriggerDialog
from toolset.gui.dialogs.instance.waypoint import WaypointDialog
from toolset.gui.editor import Editor
from toolset.gui.widgets.renderer.walkmesh import GeomPoint
from toolset.gui.widgets.settings.git import GITSettings
from toolset.utils.misc import getResourceFromFile
from toolset.utils.window import openResourceEditor

if TYPE_CHECKING:
    import os

    from pykotor.extract.file import ResourceIdentifier
    from PyQt5.QtCore import QPoint
    from toolset.data.installation import HTInstallation


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

    def __init__(self, parent: QWidget | None, installation: HTInstallation | None = None):
        """Initializes the GIT editor
        Args:
            parent: QWidget | None: The parent widget
            installation: HTInstallation | None: The installation
        Returns:
            None
        Initializes the editor UI and connects signals. Loads default settings. Initializes rendering area and mode. Clears any existing geometry.
        """
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
        self._geomInstance: GITInstance | None = None  # Used to track which trigger/encounter you are editing

        self.settings = GITSettings()

        def intColorToQColor(intvalue):
            color = Color.from_rgba_integer(intvalue)
            return QColor(int(color.r * 255), int(color.g * 255), int(color.b * 255), int(color.a * 255))

        self.materialColors: dict[SurfaceMaterial, QColor] = {
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
            SurfaceMaterial.TRIGGER: intColorToQColor(self.settings.nonWalkGrassMaterialColour),
        }
        self.nameBuffer: dict[ResourceIdentifier, str] = {}
        self.tagBuffer: dict[ResourceIdentifier, str] = {}

        self.ui.renderArea.materialColors = self.materialColors
        self.ui.renderArea.hideWalkmeshEdges = True
        self.ui.renderArea.highlightBoundaries = False

        self.new()

    def _setupHotkeys(self):
        self.ui.actionDeleteSelected.setShortcut(QKeySequence("Del"))
        self.ui.actionZoomIn.setShortcut(QKeySequence("+"))
        self.ui.actionZoomOut.setShortcut(QKeySequence("-"))

    def _setupSignals(self):
        """Connect signals to UI elements
        Args:
            self: The class instance
        Returns:
            None
        Processing Logic:
        ----------------
            - Connect mouse/key events to handlers
            - Connect checkbox toggles to visibility updater
            - Connect menu options to label settings changes.
        """
        self.ui.renderArea.mousePressed.connect(self.onMousePressed)
        self.ui.renderArea.mouseMoved.connect(self.onMouseMoved)
        self.ui.renderArea.mouseScrolled.connect(self.onMouseScrolled)
        self.ui.renderArea.mouseReleased.connect(self.onMouseReleased)
        self.ui.renderArea.customContextMenuRequested.connect(self.onContextMenu)
        self.ui.renderArea.keyPressed.connect(self.onKeyPressed)

        self.ui.filterEdit.textEdited.connect(self.onFilterEdited)
        self.ui.listWidget.doubleClicked.connect(self.moveCameraToSelection)
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

        self.ui.viewCreatureCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick( self.ui.viewCreatureCheck)
        self.ui.viewPlaceableCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick( self.ui.viewPlaceableCheck)
        self.ui.viewDoorCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick(self.ui.viewDoorCheck)
        self.ui.viewSoundCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick(self.ui.viewSoundCheck)
        self.ui.viewTriggerCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick(self.ui.viewTriggerCheck)
        self.ui.viewEncounterCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick( self.ui.viewEncounterCheck)
        self.ui.viewWaypointCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick( self.ui.viewWaypointCheck)
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

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes):
        """Load a resource from a file
        Args:
            filepath: {Path or filename to load from}
            resref: {Unique identifier for the resource}
            restype: {The type of the resource}
            data: {The raw data of the resource}.

        Returns
        -------
            None
        - Call super().load() to load base resource
        - Define search order for layout files
        - Load layout if found in search locations
        - Parse git data and call _loadGIT()
        """
        super().load(filepath, resref, restype, data)

        order = [SearchLocation.OVERRIDE, SearchLocation.CHITIN, SearchLocation.MODULES]
        result = self._installation.resource(resref, ResourceType.LYT, order)
        if result:
            self.loadLayout(read_lyt(result.data))

        git = read_git(data)
        self._loadGIT(git)

    def _loadGIT(self, git: GIT):
        """Load a GIT instance
        Args:
            git: The GIT instance to load
        Returns:
            None: This function does not return anything
        - Load the provided GIT instance into the application
        - Set the GIT instance on the render area
        - Center the camera on the render area
        - Create an InstanceMode for interaction based on the loaded GIT and installation
        - Update the visibility of UI elements.
        """
        self._git = git
        self.ui.renderArea.setGit(self._git)
        self.ui.renderArea.centerCamera()
        self._mode = _InstanceMode(self, self._installation, self._git)
        self.updateVisibility()

    def build(self) -> tuple[bytes, bytes]:
        return bytes_git(self._git), b""

    def new(self):
        super().new()

    def loadLayout(self, layout: LYT):
        """Load layout walkmeshes into the UI renderer
        Args:
            layout (LYT): Layout to load walkmeshes from
        Returns:
            None: Does not return anything
        - Iterate through each room in the layout
        - Get the highest priority walkmesh asset for the room from the installation
        - If a walkmesh asset is found, read it and add it to a list
        - Set the list of walkmeshes on the UI renderer.
        """
        walkmeshes = []
        for room in layout.rooms:
            order = [SearchLocation.OVERRIDE, SearchLocation.CHITIN, SearchLocation.MODULES]
            findBWM = self._installation.resource(room.model, ResourceType.WOK, order)
            if findBWM is not None:
                walkmeshes.append(read_bwm(findBWM.data))

        self.ui.renderArea.setWalkmeshes(walkmeshes)

    def git(self) -> GIT:
        return self._git

    def setMode(self, mode: _Mode):
        self._mode = mode

    def onInstanceVisibilityDoubleClick(self, checkbox: QCheckBox):
        """Toggles visibility of the relevant UI data on double click.

        Args:
        ----
            checkbox (QCheckBox): Checkbox for instance type visibility
        Returns:
            None: No return value
        Processing Logic:
        ----------------
        - Uncheck all other instance type checkboxes
        - Check the checkbox that was double clicked
        """
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

    def getInstanceExternalName(self, instance: GITInstance) -> str | None:
        """Get external name of a GIT instance
        Args:
            instance: The GIT instance object
        Returns:
            name: The external name of the instance or None
        - Extract identifier from instance
        - Check if identifier is present in name buffer
        - If not present, get resource from installation using identifier
        - Extract name from resource data
        - Save name in buffer
        - Return name from buffer.
        """
        resid = instance.identifier()
        if resid not in self.nameBuffer:
            res = self._installation.resource(resid.resname, resid.restype)
            self.nameBuffer[resid] = None if res is None else self._installation.string(extract_name(res.data))
        return self.nameBuffer[resid]

    def getInstanceExternalTag(self, instance: GITInstance) -> str | None:
        """Gets external tag for the given instance
        Args:
            instance: The instance to get tag for
        Returns:
            tag: The external tag associated with the instance or None
        - Get resource identifier from instance
        - Check if tag is already cached for this identifier
        - If not cached, call installation to get resource and extract tag from resource data
        - Cache tag in buffer and return cached tag.
        """
        resid = instance.identifier()
        if resid not in self.tagBuffer:
            res = self._installation.resource(resid.resname, resid.restype)
            self.tagBuffer[resid] = None if res is None else extract_tag(res.data)
        return self.tagBuffer[resid]

    def enterInstanceMode(self):
        self._mode = _InstanceMode(self, self._installation, self._git)

    def enterGeometryMode(self):
        self._mode = _GeometryMode(self, self._installation, self._git)

    def enterSpawnMode(self):
        ...
        # TODO

    def moveCameraToSelection(self):
        instance = self.ui.renderArea.instanceSelection.last()
        if instance:
            self.ui.renderArea.camera.setPosition(instance.position.x, instance.position.y)

    # region Mode Calls
    def openListContextMenu(self, item: QListWidgetItem, point: QPoint):
        ...

    def updateVisibility(self):
        self._mode.updateVisibility()

    def selectUnderneath(self):
        self._mode.selectUnderneath()

    def deleteSelected(self):
        self._mode.deleteSelected()

    def duplicateSelected(self, position: Vector3):
        self._mode.duplicateSelected(position)

    def moveSelected(self, x: float, y: float):
        self._mode.moveSelected(x, y)

    def rotateSelected(self, angle: float):
        self._mode.rotateSelected(angle)

    def rotateSelectedToPoint(self, x: float, y: float):
        self._mode.rotateSelectedToPoint(x, y)

    def moveCamera(self, x: float, y: float):
        self._mode.moveCamera(x, y)

    def zoomCamera(self, amount: float):
        self._mode.zoomCamera(amount)

    def rotateCamera(self, angle: float):
        self._mode.rotateCamera(angle)

    # endregion

    # region Signal Callbacks
    def onContextMenu(self, point: QPoint):
        """Opens context menu on right click in render area.

        Args:
        ----
            point: Point of right click in local coordinates
        Returns:
            None
        Processes right click context menu:
            - Maps point from local to global coordinates
            - Converts point from local to world coordinates
        - Passes world point and global point to mode for context menu handling
        """
        globalPoint = self.ui.renderArea.mapToGlobal(point)
        world = self.ui.renderArea.toWorldCoords(point.x(), point.y())
        self._mode.onRenderContextMenu(world, globalPoint)

    def onFilterEdited(self):
        self._mode.onFilterEdited(self.ui.filterEdit.text())

    def onItemSelectionChanged(self):
        self._mode.onItemSelectionChanged(self.ui.listWidget.currentItem())

    def onItemContextMenu(self, point: QPoint):
        """Opens context menu for the current list item.

        Args:
        ----
            point: Point of context menu click
        Returns:
            None
        Processes context menu click:
            - Maps local point to global coordinate system
            - Gets current list item
        - Opens context menu through mode manager
        """
        globalPoint = self.ui.listWidget.mapToGlobal(point)
        item = self.ui.listWidget.currentItem()
        self._mode.openListContextMenu(item, globalPoint)

    def onMouseMoved(self, screen: Vector2, delta: Vector2, buttons: set[int], keys: set[int]):
        """Handle mouse movement event.

        Args:
        ----
            screen: Vector2: Mouse position on screen
            delta: Vector2: Mouse movement since last event
            buttons: set[int]: Currently pressed mouse buttons
            keys: set[int]: Currently pressed keyboard keys

        Processing Logic:
        ----------------
            - Convert mouse position and movement to world coordinates
            - Pass mouse event to controls handler
            - Update status bar with world mouse position.
        """
        worldDelta = self.ui.renderArea.toWorldDelta(delta.x, delta.y)
        world = self.ui.renderArea.toWorldCoords(screen.x, screen.y)
        self._controls.onMouseMoved(screen, delta, world, worldDelta, buttons, keys)
        self._mode.updateStatusBar(world)

    def onMouseScrolled(self, delta: Vector2, buttons: set[int], keys: set[int]):
        self._controls.onMouseScrolled(delta, buttons, keys)

    def onMousePressed(self, screen: Vector2, buttons: set[int], keys: set[int]):
        self._controls.onMousePressed(screen, buttons, keys)

    def onMouseReleased(self, buttons: set[int], keys: set[int]):
        self._controls.onMouseReleased(Vector2(0, 0), buttons, keys)

    def onKeyPressed(self, buttons: set[int], keys: set[int]):
        self._controls.onKeyboardPressed(buttons, keys)

    def keyPressEvent(self, e: QKeyEvent):
        self.ui.renderArea.keyPressEvent(e)

    def keyReleaseEvent(self, e: QKeyEvent):
        self.ui.renderArea.keyReleaseEvent(e)

    # endregion


class _Mode(ABC):
    def __init__(self, editor: GITEditor, installation: HTInstallation, git: GIT):
        self._editor: GITEditor = editor
        self._installation: HTInstallation = installation
        self._git: GIT = git

        self._ui = editor.ui

    @abstractmethod
    def onItemSelectionChanged(self, item: QListWidgetItem):
        ...

    @abstractmethod
    def onFilterEdited(self, text: str):
        ...

    @abstractmethod
    def onRenderContextMenu(self, world: Vector2, screen: QPoint):
        ...

    @abstractmethod
    def openListContextMenu(self, item: QListWidgetItem, screen: QPoint):
        ...

    @abstractmethod
    def updateVisibility(self):
        ...

    @abstractmethod
    def selectUnderneath(self):
        ...

    @abstractmethod
    def deleteSelected(self):
        ...

    @abstractmethod
    def duplicateSelected(self, position: Vector3):
        ...

    @abstractmethod
    def moveSelected(self, x: float, y: float):
        ...

    @abstractmethod
    def rotateSelected(self, angle: float):
        ...

    @abstractmethod
    def rotateSelectedToPoint(self, x: float, y: float):
        ...

    @abstractmethod
    def moveCamera(self, x: float, y: float):
        ...

    @abstractmethod
    def zoomCamera(self, amount: float):
        ...

    @abstractmethod
    def rotateCamera(self, angle: float):
        ...

    # endregion


class _InstanceMode(_Mode):
    def __init__(self, editor: GITEditor, installation: HTInstallation, git: GIT):
        super().__init__(editor, installation, git)
        self._ui.renderArea.hideGeomPoints = True
        self._ui.renderArea.geometrySelection.clear()
        self.updateVisibility()

    def setSelection(self, instances: list[GITInstance]):
        # set the renderer widget selection
        """Sets the selection of instances in the renderer and list widgets.

        Args:
        ----
            instances: list[GITInstance]: List of instances to select

        Processing Logic:
        ----------------
            - Select instances in the renderer widget
            - Block list widget signals to prevent selection changed signal
            - Loop through list widget items and select matching instances
            - Unblock list widget signals.
        """
        self._ui.renderArea.instanceSelection.select(instances)

        # set the list widget selection
        self._ui.listWidget.blockSignals(True)
        for i in range(self._ui.listWidget.count()):
            item = self._ui.listWidget.item(i)
            instance = item.data(QtCore.Qt.UserRole)
            if instance in instances:
                self._ui.listWidget.setCurrentItem(item)
        self._ui.listWidget.blockSignals(False)

    def editSelectedInstance(self):
        """Edits the selected instance.

        Args:
        ----
            self: The class instance

        Processing Logic:
        ----------------
            - Gets the selected instance from the render area
            - Checks if an instance is selected
            - Gets the last selected instance from the list
            - Opens an instance dialog to edit the selected instance properties
            - Rebuilds the instance list after editing.
        """
        selection = self._ui.renderArea.instanceSelection.all()

        if selection:
            instance = selection[-1]
            openInstanceDialog(self._editor, instance, self._installation)
            self.buildList()

    def editSelectedInstanceResource(self):
        """Edits the selected instance resource.

        Processing Logic:
        ----------------
            - Gets the selected instance from the render area
            - Gets the resource name and type from the instance
            - Searches installation locations for the resource file path
            - Checks if the path contains "override" or is in the module root
            - Opens the resource editor with the file if a path is found.
        """
        selection = self._ui.renderArea.instanceSelection.all()

        if selection:
            instance = selection[-1]
            resname, restype = instance.identifier()
            filepath = None

            order = [SearchLocation.CHITIN, SearchLocation.MODULES, SearchLocation.OVERRIDE]
            search = self._installation.location(resname, restype, order)

            for result in search:
                lowercase_path_parts = [f.lower() for f in result.filepath.parts]
                if "override" in lowercase_path_parts:
                    filepath = result.filepath
                else:
                    module_root = Module.get_root(self._editor.filepath()).lower()

                    # Check if module root is in path parents or is a .rim
                    lowercase_path_parents = [str(parent).lower() for parent in result.filepath.parents]
                    if module_root in lowercase_path_parents and (filepath is None or is_rim_file(filepath)):
                        filepath = result.filepath

            if filepath:
                data = getResourceFromFile(filepath, resname, restype)
                openResourceEditor(filepath, resname, restype, data, self._installation, self._editor)
            else:
                # TODO Make prompt for override/MOD
                ...

    def editSelectedInstanceGeometry(self):
        if self._ui.renderArea.instanceSelection.last():
            self._ui.renderArea.instanceSelection.last()
            self._editor.enterGeometryMode()

    def editSelectedInstanceSpawns(self):
        if self._ui.renderArea.instanceSelection.last():
            self._ui.renderArea.instanceSelection.last()
            # TODO

    def addInstance(self, instance: GITInstance):
        if openInstanceDialog(self._editor, instance, self._installation):
            self._git.add(instance)
            self.buildList()

    def addInstanceActionsToMenu(self, instance: GITInstance, menu: QMenu):
        """Adds instance actions to a context menu.

        Args:
        ----
            instance: {The selected GIT instance object}
            menu: {The QMenu to add actions to}.

        Returns:
        -------
            None: {Does not return anything, just adds actions to the provided menu}

        Processing Logic:
        ----------------
            - Adds basic "Remove" and "Edit Instance" actions
            - Conditionally adds "Edit Resource" action and disables for cameras
            - Adds additional geometry and spawn point editing for encounters and triggers
            - Connects each action to a method on the class to handle the trigger
        """
        menu.addAction("Remove").triggered.connect(self.deleteSelected)
        menu.addAction("Edit Instance").triggered.connect(self.editSelectedInstance)

        actionEditResource = menu.addAction("Edit Resource")
        actionEditResource.triggered.connect(self.editSelectedInstanceResource)
        actionEditResource.setEnabled(not isinstance(instance, GITCamera))
        menu.addAction(actionEditResource)

        if isinstance(instance, (GITEncounter, GITTrigger)):
            menu.addAction("Edit Geometry").triggered.connect(self.editSelectedInstanceGeometry)

        if isinstance(instance, GITEncounter):
            menu.addAction("Edit Spawn Points").triggered.connect(self.editSelectedInstanceSpawns)

    def setListItemLabel(self, item: QListWidgetItem, instance: GITInstance):
        """Sets the label text of a QListWidget item for a game instance.

        Args:
        ----
            item (QListWidgetItem): The list widget item
            instance (GITInstance): The game instance

        Sets the item data and tooltip, determines the label text based on instance type and editor settings, sets the item text and font if label not found.
        """
        item.setData(QtCore.Qt.UserRole, instance)
        item.setToolTip(self.getInstanceTooltip(instance))

        name: str | None = None

        if isinstance(instance, GITCamera):
            item.setText(str(instance.camera_id))
            return
        if isinstance(instance, GITCreature):
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

        text: str = instance.identifier().resname if name is None else name
        if name is None:
            font = item.font()
            font.setItalic(True)
            item.setFont(font)

        item.setText(text)

    def getInstanceTooltip(self, instance: GITInstance) -> str:
        if isinstance(instance, GITCamera):
            return f"Struct Index: {self._git.index(instance)}\nCamera ID: {instance.camera_id}"
        return f"Struct Index: {self._git.index(instance)}\nResRef: {instance.identifier().resname}"

    # region Interface Methods
    def onFilterEdited(self, text: str):
        self._ui.renderArea.instanceFilter = text
        self.buildList()

    def onItemSelectionChanged(self, item: QListWidgetItem):
        if item is None:
            self.setSelection([])
        else:
            self.setSelection([item.data(QtCore.Qt.UserRole)])

    def updateStatusBar(self, world: Vector2):
        if self._ui.renderArea.instancesUnderMouse() and self._ui.renderArea.instancesUnderMouse()[-1] is not None:
            instance = self._ui.renderArea.instancesUnderMouse()[-1]
            resname = "" if isinstance(instance, GITCamera) else instance.identifier().resname
            self._editor.statusBar().showMessage(f"({world.x:.1f}, {world.y:.1f}) {resname}")
        else:
            self._editor.statusBar().showMessage(f"({world.x:.1f}, {world.y:.1f})")

    def openListContextMenu(self, item: QListWidgetItem, point: QPoint):
        if item is None:
            return

        instance = item.data(QtCore.Qt.UserRole)
        menu = QMenu(self._ui.listWidget)

        self.addInstanceActionsToMenu(instance, menu)

        menu.popup(point)

    def onRenderContextMenu(self, world: Vector2, point: QPoint):
        """Renders context menu on right click.

        Args:
        ----
            self: {The class instance}
            world: {The world coordinates clicked}
            point: {The screen coordinates clicked}.

        Renders context menu:
            - Adds instance creation actions if no selection
            - Adds instance actions to selected instance if single selection
            - Adds deselect action for instances under mouse
        """
        underMouse = self._ui.renderArea.instancesUnderMouse()

        menu = QMenu(self._ui.listWidget)

        if not self._ui.renderArea.instanceSelection.isEmpty():
            self.addInstanceActionsToMenu(self._ui.renderArea.instanceSelection.last(), menu)
        else:
            self._add_submenu(menu, world)
        if underMouse:
            menu.addSeparator()
            for instance in underMouse:
                icon = QIcon(self._ui.renderArea.instancePixmap(instance))
                reference = "" if instance.identifier() is None else instance.identifier().resname
                index = self._editor.git().index(instance)

                instanceAction = menu.addAction(icon, f"[{index}] {reference}")
                instanceAction.triggered.connect(lambda _, inst=instance: self.setSelection([inst]))
                instanceAction.setEnabled(instance not in self._ui.renderArea.instanceSelection.all())
                menu.addAction(instanceAction)

        menu.popup(point)

    def _add_submenu(self, menu: QMenu, world: Vector2):
        menu.addAction("Insert Creature").triggered.connect(lambda: self.addInstance(GITCreature(world.x, world.y)))
        menu.addAction("Insert Door").triggered.connect(lambda: self.addInstance(GITDoor(world.x, world.y)))
        menu.addAction("Insert Placeable").triggered.connect(lambda: self.addInstance(GITPlaceable(world.x, world.y)))
        menu.addAction("Insert Store").triggered.connect(lambda: self.addInstance(GITStore(world.x, world.y)))
        menu.addAction("Insert Sound").triggered.connect(lambda: self.addInstance(GITSound(world.x, world.y)))
        menu.addAction("Insert Waypoint").triggered.connect(lambda: self.addInstance(GITWaypoint(world.x, world.y)))
        menu.addAction("Insert Camera").triggered.connect(lambda: self.addInstance(GITCamera(world.x, world.y)))
        menu.addAction("Insert Encounter").triggered.connect(lambda: self.addInstance(GITEncounter(world.x, world.y)))

        simpleTrigger = GITTrigger(world.x, world.y)
        simpleTrigger.geometry.extend(
            [Vector3(0.0, 0.0, 0.0), Vector3(3.0, 0.0, 0.0), Vector3(3.0, 3.0, 0.0), Vector3(0.0, 3.0, 0.0)],
        )
        menu.addAction("Insert Trigger").triggered.connect(lambda: self.addInstance(simpleTrigger))

    def buildList(self):
        self._ui.listWidget.clear()

        def instanceSort(inst: GITInstance):
            textToSort = str(inst.camera_id) if isinstance(inst, GITCamera) else inst.identifier().resname.lower()
            return textToSort.rjust(9, "0") if isinstance(inst, GITCamera) else inst.identifier().restype.extension + textToSort

        instances: list[GITInstance] = sorted(self._git.instances(), key=instanceSort)
        for instance in instances:
            filterSource = str(instance.camera_id) if isinstance(instance, GITCamera) else instance.identifier().resname
            isVisible = self._ui.renderArea.isInstanceVisible(instance)
            isFiltered = self._ui.filterEdit.text() in filterSource

            if isVisible and isFiltered:
                icon = QIcon(self._ui.renderArea.instancePixmap(instance))
                item = QListWidgetItem(icon, "")
                self.setListItemLabel(item, instance)
                self._ui.listWidget.addItem(item)

    def updateVisibility(self):
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

    def selectUnderneath(self):
        underMouse = self._ui.renderArea.instancesUnderMouse()
        selection = self._ui.renderArea.instanceSelection.all()

        # Do not change the selection if the selected instance if its still underneath the mouse
        if selection and selection[0] in underMouse:
            return

        if underMouse:
            self.setSelection([underMouse[-1]])
        else:
            self.setSelection([])

    def deleteSelected(self):
        for instance in self._ui.renderArea.instanceSelection.all():
            self._git.remove(instance)
            self._ui.renderArea.instanceSelection.remove(instance)
        self.buildList()

    def duplicateSelected(self, position: Vector3):
        if self._ui.renderArea.instanceSelection.all():
            instance = deepcopy(self._ui.renderArea.instanceSelection.all()[-1])
            instance.position = position
            self._git.add(instance)
            self.buildList()
            self.setSelection([instance])

    def moveSelected(self, x: float, y: float):
        if self._ui.lockInstancesCheck.isChecked():
            return

        for instance in self._ui.renderArea.instanceSelection.all():
            instance.move(x, y, 0)

    def rotateSelected(self, angle: float):
        for instance in self._ui.renderArea.instanceSelection.all():
            instance.rotate(angle)

    def rotateSelectedToPoint(self, x: float, y: float):
        for instance in self._ui.renderArea.instanceSelection.all():
            rotation = -math.atan2(x - instance.position.x, y - instance.position.y)
            if isinstance(instance, GITCamera):
                instance.rotate(instance.yaw() - rotation, 0, 0)
            else:
                instance.rotate(-instance.yaw() + rotation, 0, 0)

    def moveCamera(self, x: float, y: float):
        self._ui.renderArea.camera.nudgePosition(x, y)

    def zoomCamera(self, amount: float):
        self._ui.renderArea.camera.nudgeZoom(amount)

    def rotateCamera(self, angle: float):
        self._ui.renderArea.camera.nudgeRotation(angle)

    # endregion


class _GeometryMode(_Mode):
    def __init__(self, editor: GITEditor, installation: HTInstallation, git: GIT):
        super().__init__(editor, installation, git)

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

    def insertPointAtMouse(self):
        screen = self._ui.renderArea.mapFromGlobal(self._editor.cursor().pos())
        world = self._ui.renderArea.toWorldCoords(screen.x(), screen.y())

        instance = self._ui.renderArea.instanceSelection.get(0)
        point = world - instance.position
        self._ui.renderArea.geomPointsUnderMouse().append(GeomPoint(instance, point))

    # region Interface Methods
    def onItemSelectionChanged(self, item: QListWidgetItem):
        pass

    def onFilterEdited(self, text: str):
        pass

    def updateStatusBar(self, world: Vector2):
        instance: GITInstance | None = self._ui.renderArea.instanceSelection.last()
        if instance:
            self._editor.statusBar().showMessage(
                f"({world.x:.1f}, {world.y:.1f}) Editing Geometry of {instance.identifier().resname}",
            )

    def onRenderContextMenu(self, world: Vector2, screen: QPoint):
        menu = QMenu(self._editor)

        if not self._ui.renderArea.geometrySelection.isEmpty():
            menu.addAction("Remove").triggered.connect(self.deleteSelected)

        if self._ui.renderArea.geometrySelection.count() == 0:
            menu.addAction("Insert").triggered.connect(self.insertPointAtMouse)

        menu.addSeparator()
        menu.addAction("Finish Editing").triggered.connect(self._editor.enterInstanceMode)

        menu.popup(screen)

    def openListContextMenu(self, item: QListWidgetItem, screen: QPoint):
        pass

    def updateVisibility(self):
        pass

    def selectUnderneath(self):
        underMouse: list[GeomPoint] = self._ui.renderArea.geomPointsUnderMouse()
        selection: list[GeomPoint] = self._ui.renderArea.geometrySelection.all()

        # Do not change the selection if the selected instance if its still underneath the mouse
        if selection and selection[0] in underMouse:
            return

        if underMouse:
            self._ui.renderArea.geometrySelection.select(underMouse)
        else:
            self._ui.renderArea.geometrySelection.select([])

    def deleteSelected(self):
        vertex: GeomPoint | None = self._ui.renderArea.geometrySelection.last()
        instance: GITInstance = vertex.instance
        self._ui.renderArea.geometrySelection.remove(GeomPoint(instance, vertex.point))  # FIXME

    def duplicateSelected(self, position: Vector3):
        pass

    def moveSelected(self, x: float, y: float):
        for vertex in self._ui.renderArea.geometrySelection.all():
            vertex.point.x += x
            vertex.point.y += y

    def rotateSelected(self, angle: float):
        pass

    def rotateSelectedToPoint(self, x: float, y: float):
        pass

    def moveCamera(self, x: float, y: float):
        self._ui.renderArea.camera.nudgePosition(x, y)

    def zoomCamera(self, amount: float):
        self._ui.renderArea.camera.nudgeZoom(amount)

    def rotateCamera(self, angle: float):
        self._ui.renderArea.camera.nudgeRotation(angle)

    # endregion


class GITControlScheme:
    def __init__(self, editor: GITEditor):
        self.editor: GITEditor = editor
        self.settings: GITSettings = GITSettings()

        self.panCamera: ControlItem = ControlItem(self.settings.moveCameraBind)
        self.rotateCamera: ControlItem = ControlItem(self.settings.rotateCameraBind)
        self.zoomCamera: ControlItem = ControlItem(self.settings.zoomCameraBind)
        self.rotateSelectedToPoint: ControlItem = ControlItem(self.settings.rotateSelectedToPointBind)
        self.moveSelected: ControlItem = ControlItem(self.settings.moveSelectedBind)
        self.selectUnderneath: ControlItem = ControlItem(self.settings.selectUnderneathBind)
        self.deleteSelected: ControlItem = ControlItem(self.settings.deleteSelectedBind)
        self.duplicateSelected: ControlItem = ControlItem(self.settings.duplicateSelectedBind)
        self.toggleInstanceLock: ControlItem = ControlItem(self.settings.toggleLockInstancesBind)

    def onMouseScrolled(self, delta: Vector2, buttons: set[int], keys: set[int]):
        if self.zoomCamera.satisfied(buttons, keys):
            self.editor.zoomCamera(delta.y / 50)

    def onMouseMoved(
        self,
        screen: Vector2,
        screenDelta: Vector2,
        world: Vector2,
        worldDelta: Vector2,
        buttons: set[int],
        keys: set[int],
    ):
        """Handles mouse movement events in the editor.

        Args:
        ----
            screen: Vector2 - Mouse position on screen in pixels
            screenDelta: Vector2 - Mouse movement since last event in pixels
            world: Vector2 - Mouse position in world space
            worldDelta: Vector2 - Mouse movement since last event in world space
            buttons: set[int] - Currently pressed mouse buttons
            keys: set[int] - Currently pressed keyboard keys

        Processing Logic:
        ----------------
            - Checks if pan camera condition is satisfied and moves camera accordingly
            - Checks if rotate camera condition is satisfied and rotates camera
            - Checks if move selected condition is satisfied and moves selected object
            - Checks if rotate selected to point condition is satisfied and rotates selected object to point.
        """
        if self.panCamera.satisfied(buttons, keys):
            self.editor.moveCamera(-worldDelta.x, -worldDelta.y)
        if self.rotateCamera.satisfied(buttons, keys):
            self.editor.rotateCamera(screenDelta.y)
        if self.moveSelected.satisfied(buttons, keys):
            self.editor.moveSelected(worldDelta.x, worldDelta.y)
        if self.rotateSelectedToPoint.satisfied(buttons, keys):
            self.editor.rotateSelectedToPoint(world.x, world.y)

    def onMousePressed(self, screen: Vector2, buttons: set[int], keys: set[int]):
        if self.selectUnderneath.satisfied(buttons, keys):
            self.editor.selectUnderneath()
        if self.duplicateSelected.satisfied(buttons, keys):
            position = self.editor.ui.renderArea.toWorldCoords(screen.x, screen.y)
            self.editor.duplicateSelected(position)

    def onMouseReleased(self, screen: Vector2, buttons: set[int], keys: set[int]):
        ...

    def onKeyboardPressed(self, buttons: set[int], keys: set[int]):
        if self.deleteSelected.satisfied(buttons, keys):
            self.editor.deleteSelected()

        if self.toggleInstanceLock.satisfied(buttons, keys):
            self.editor.ui.lockInstancesCheck.setChecked(not self.editor.ui.lockInstancesCheck.isChecked())

    def onKeyboardReleased(self, buttons: set[int], keys: set[int]):
        ...
