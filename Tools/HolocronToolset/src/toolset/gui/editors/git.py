from __future__ import annotations

import math

from abc import ABC, abstractmethod
from copy import deepcopy
from typing import TYPE_CHECKING, Sequence

import qtpy

from loggerplus import RobustLogger
from qtpy import QtCore
from qtpy.QtGui import QColor, QIcon, QKeySequence
from qtpy.QtWidgets import QDialog, QListWidgetItem, QMenu, QMessageBox, QUndoCommand

from pykotor.common.geometry import SurfaceMaterial, Vector2, Vector3
from pykotor.common.misc import Color
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.bwm import read_bwm
from pykotor.resource.formats.lyt import read_lyt
from pykotor.resource.generics.git import (
    GIT,
    GITCamera,
    GITCreature,
    GITDoor,
    GITEncounter,
    GITPlaceable,
    GITSound,
    GITStore,
    GITTrigger,
    GITWaypoint,
    bytes_git,
    read_git,
)
from pykotor.resource.type import ResourceType
from pykotor.tools.template import extract_name, extract_tag_from_gff
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
from toolset.gui.dialogs.load_from_location_result import (
    FileSelectionWindow,
    ResourceItems,
)
from toolset.gui.editor import Editor
from toolset.gui.widgets.renderer.walkmesh import GeomPoint
from toolset.gui.widgets.settings.git import GITSettings
from toolset.gui.widgets.settings.module_designer import ModuleDesignerSettings
from toolset.utils.window import add_window, open_resource_editor

if TYPE_CHECKING:
    import os

    from qtpy.QtCore import QPoint
    from qtpy.QtGui import QCloseEvent, QKeyEvent
    from qtpy.QtWidgets import QCheckBox, QWidget

    from pykotor.common.geometry import Vector4
    from pykotor.extract.file import LocationResult, ResourceIdentifier, ResourceResult
    from pykotor.resource.formats.bwm.bwm_data import BWM
    from pykotor.resource.formats.lyt import LYT
    from pykotor.resource.generics.git import GITInstance
    from toolset.data.installation import HTInstallation
    from toolset.gui.windows.module_designer import (
        ModuleDesigner,  # Keep in type checking block to avoid circular imports
    )

if qtpy.API_NAME in ("PyQt6", "PySide6"):
    from qtpy.QtGui import QUndoStack
else:
    from qtpy.QtWidgets import QUndoStack

class MoveCommand(QUndoCommand):
    def __init__(
        self,
        instance: GITInstance,
        old_position: Vector3,
        new_position: Vector3,
        old_height: float | None = None,
        new_height: float | None = None,
    ):
        RobustLogger().debug(f"Init movecommand with instance {instance.identifier()}")
        super().__init__()
        self.instance: GITInstance = instance
        self.old_position: Vector3 = old_position
        self.new_position: Vector3 = new_position

    def undo(self):
        RobustLogger().debug(f"Undo position: {self.instance.identifier()} (NEW {self.new_position} --> {self.old_position})")
        self.instance.position = self.old_position

    def redo(self):
        RobustLogger().debug(f"Undo position: {self.instance.identifier()} ({self.old_position} --> NEW {self.new_position})")
        self.instance.position = self.new_position


class RotateCommand(QUndoCommand):
    def __init__(
        self,
        instance: GITCamera | GITCreature | GITDoor | GITPlaceable | GITStore | GITWaypoint,
        old_orientation: Vector4 | float,
        new_orientation: Vector4 | float
    ):
        RobustLogger().debug(f"Init rotatecommand with instance: {instance.identifier()}")
        super().__init__()
        self.instance: GITCamera | GITCreature | GITDoor | GITPlaceable | GITStore | GITWaypoint = instance
        self.old_orientation: Vector4 | float = old_orientation
        self.new_orientation: Vector4 | float = new_orientation

    def undo(self):
        RobustLogger().debug(f"Undo rotation: {self.instance.identifier()} (NEW {self.new_orientation} --> {self.old_orientation})")
        if isinstance(self.instance, GITCamera):
            self.instance.orientation = self.old_orientation
        else:
            self.instance.bearing = self.old_orientation

    def redo(self):
        RobustLogger().debug(f"Redo rotation: {self.instance.identifier()} ({self.old_orientation} --> NEW {self.new_orientation})")
        if isinstance(self.instance, GITCamera):
            self.instance.orientation = self.new_orientation
        else:
            self.instance.bearing = self.new_orientation


class DuplicateCommand(QUndoCommand):
    def __init__(
        self,
        git: GIT,
        instances: Sequence[GITInstance],
        editor: GITEditor | ModuleDesigner,
    ):
        super().__init__()
        self.git: GIT = git
        self.instances: list[GITInstance] = instances
        self.editor: GITEditor | ModuleDesigner = editor

    def undo(self):
        self.editor.enterInstanceMode()
        for instance in self.instances:
            if instance not in self.git.instances():
                print(f"{instance!r} not found in instances: no duplicate to undo.")
                continue
            RobustLogger().debug(f"Undo duplicate: {instance.identifier()}")
            if isinstance(self.editor, GITEditor):
                self.editor._mode.renderer2d.instanceSelection.select([instance])  # noqa: SLF001
            else:
                self.editor.setSelection([instance])
            self.editor.deleteSelected(noUndoStack=True)
        self.rebuildInstanceList()

    def rebuildInstanceList(self):
        if isinstance(self.editor, GITEditor):
            self.editor.enterInstanceMode()
            assert isinstance(self.editor._mode, _InstanceMode)  # noqa: SLF001
            self.editor._mode.buildList()  # noqa: SLF001
        else:
            self.editor.enterInstanceMode()
            self.editor.rebuildInstanceList()


    def redo(self):
        for instance in self.instances:
            if instance in self.git.instances():
                print(f"{instance!r} already found in instances: no duplicate to redo.")
                continue
            RobustLogger().debug(f"Redo duplicate: {instance.identifier()}")
            self.git.add(instance)
            if isinstance(self.editor, GITEditor):
                self.editor._mode.renderer2d.instanceSelection.select([instance])  # noqa: SLF001
            else:
                self.editor.setSelection([instance])
        self.rebuildInstanceList()


class DeleteCommand(QUndoCommand):
    def __init__(
        self,
        git: GIT,
        instances: list[GITInstance],
        editor: GITEditor | ModuleDesigner,
    ):
        super().__init__()
        self.git: GIT = git
        self.instances: list[GITInstance] = instances
        self.editor: GITEditor | ModuleDesigner = editor

    def undo(self):
        RobustLogger().debug(f"Undo delete: {[repr(instance) for instance in self.instances]}")
        for instance in self.instances:
            if instance in self.git.instances():
                print(f"{instance!r} already found in instances: no deletecommand to undo.")
                continue
            self.git.add(instance)
        self.rebuildInstanceList()

    def rebuildInstanceList(self):
        if isinstance(self.editor, GITEditor):
            self.editor.enterInstanceMode()
            assert isinstance(self.editor._mode, _InstanceMode)  # noqa: SLF001
            self.editor._mode.buildList()  # noqa: SLF001
        else:
            self.editor.enterInstanceMode()
            self.editor.rebuildInstanceList()

    def redo(self):
        RobustLogger().debug(f"Redo delete: {[repr(instance) for instance in self.instances]}")
        self.editor.enterInstanceMode()
        for instance in self.instances:
            if instance not in self.git.instances():
                print(f"{instance!r} not found in instances: no deletecommand to redo.")
                continue
            RobustLogger().debug(f"Redo delete: {instance!r}")
            if isinstance(self.editor, GITEditor):
                self.editor._mode.renderer2d.instanceSelection.select([instance])  # noqa: SLF001
            else:
                self.editor.setSelection([instance])
            self.editor.deleteSelected(noUndoStack=True)
        self.rebuildInstanceList()


class InsertCommand(QUndoCommand):
    def __init__(
        self,
        git: GIT,
        instance: GITInstance,
        editor: GITEditor | ModuleDesigner,
    ):
        super().__init__()
        self.git: GIT = git
        self.instance: GITInstance = instance
        self._firstRun: bool = True
        self.editor: GITEditor | ModuleDesigner = editor

    def undo(self):
        RobustLogger().debug(f"Undo insert: {self.instance.identifier()}")
        self.git.remove(self.instance)
        self.rebuildInstanceList()

    def rebuildInstanceList(self):
        if isinstance(self.editor, GITEditor):
            old_mode = self.editor._mode  # noqa: SLF001
            self.editor.enterInstanceMode()
            assert isinstance(self.editor._mode, _InstanceMode)  # noqa: SLF001
            self.editor._mode.buildList()  # noqa: SLF001
            if isinstance(old_mode, _GeometryMode):
                self.editor.enterGeometryMode()
            elif isinstance(old_mode, _SpawnMode):
                self.editor.enterSpawnMode()
        else:
            self.editor.rebuildInstanceList()

    def redo(self):
        if self._firstRun is True:
            print("Skipping first redo of InsertCommand.")
            self._firstRun = False
            return
        RobustLogger().debug(f"Redo insert: {self.instance.identifier()}")
        self.git.add(self.instance)
        self.rebuildInstanceList()


def openInstanceDialog(
    parent: QWidget,
    instance: GITInstance,
    installation: HTInstallation,
) -> int:
    dialog = QDialog()

    if isinstance(instance, GITCamera):
        dialog = CameraDialog(parent, instance)
    elif isinstance(instance, GITCreature):
        dialog = CreatureDialog(parent, instance)
    elif isinstance(instance, GITDoor):
        dialog = DoorDialog(parent, instance, installation)
    elif isinstance(instance, GITEncounter):
        dialog = EncounterDialog(parent, instance)
    elif isinstance(instance, GITPlaceable):
        dialog = PlaceableDialog(parent, instance)
    elif isinstance(instance, GITTrigger):
        dialog = TriggerDialog(parent, instance, installation)
    elif isinstance(instance, GITSound):
        dialog = SoundDialog(parent, instance)
    elif isinstance(instance, GITStore):
        dialog = StoreDialog(parent, instance)
    elif isinstance(instance, GITWaypoint):
        dialog = WaypointDialog(parent, instance, installation)

    return dialog.exec_()


class GITEditor(Editor):
    settingsUpdated = QtCore.Signal(object)  # pyright: ignore[reportPrivateImportUsage]

    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation = None,
    ):
        """Initializes the GIT editor.

        Args:
        ----
            parent: QWidget | None: The parent widget
            installation: HTInstallation | None: The installation

        Initializes the editor UI and connects signals. Loads default settings. Initializes rendering area and mode. Clears any existing geometry.
        """
        supported = [ResourceType.GIT]
        super().__init__(parent, "GIT Editor", "git", supported, supported, installation)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.editors.git import (
                Ui_MainWindow,  # noqa: PLC0415  # pylint: disable=C0415
            )
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.editors.git import (
                Ui_MainWindow,  # noqa: PLC0415  # pylint: disable=C0415
            )
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.editors.git import (
                Ui_MainWindow,  # noqa: PLC0415  # pylint: disable=C0415
            )
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.editors.git import (
                Ui_MainWindow,  # noqa: PLC0415  # pylint: disable=C0415
            )
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()
        self._setupHotkeys()

        self._git: GIT = GIT()
        self._mode: _Mode = _InstanceMode(self, installation, self._git)
        self._controls: GITControlScheme = GITControlScheme(self)
        self._geomInstance: GITInstance | None = None  # Used to track which trigger/encounter you are editing

        self.ui.actionUndo.triggered.connect(lambda: print("Undo signal") or self._controls.undoStack.undo())
        self.ui.actionRedo.triggered.connect(lambda: print("Redo signal") or self._controls.undoStack.redo())

        self.settings = GITSettings()

        def intColorToQColor(intvalue: int) -> QColor:
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

    def _setupHotkeys(self):  # TODO: use GlobalSettings() defined hotkeys
        self.ui.actionDeleteSelected.setShortcut(QKeySequence("Del"))  # type: ignore[arg-type]
        self.ui.actionZoomIn.setShortcut(QKeySequence("+"))  # type: ignore[arg-type]
        self.ui.actionZoomOut.setShortcut(QKeySequence("-"))  # type: ignore[arg-type]
        self.ui.actionUndo.setShortcut(QKeySequence("Ctrl+Z"))  # type: ignore[arg-type]
        self.ui.actionRedo.setShortcut(QKeySequence("Ctrl+Shift+Z"))  # type: ignore[arg-type]

    def _setupSignals(self):
        """Connect signals to UI elements.

        Args:
        ----
            self: The class instance

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

        self.ui.viewCreatureCheck.mouseDoubleClickEvent = lambda a0: self.onInstanceVisibilityDoubleClick(self.ui.viewCreatureCheck)  # noqa: ARG005
        self.ui.viewPlaceableCheck.mouseDoubleClickEvent = lambda a0: self.onInstanceVisibilityDoubleClick(self.ui.viewPlaceableCheck)  # noqa: ARG005
        self.ui.viewDoorCheck.mouseDoubleClickEvent = lambda a0: self.onInstanceVisibilityDoubleClick(self.ui.viewDoorCheck)  # noqa: ARG005
        self.ui.viewSoundCheck.mouseDoubleClickEvent = lambda a0: self.onInstanceVisibilityDoubleClick(self.ui.viewSoundCheck)  # noqa: ARG005
        self.ui.viewTriggerCheck.mouseDoubleClickEvent = lambda a0: self.onInstanceVisibilityDoubleClick(self.ui.viewTriggerCheck)  # noqa: ARG005
        self.ui.viewEncounterCheck.mouseDoubleClickEvent = lambda a0: self.onInstanceVisibilityDoubleClick(self.ui.viewEncounterCheck)  # noqa: ARG005
        self.ui.viewWaypointCheck.mouseDoubleClickEvent = lambda a0: self.onInstanceVisibilityDoubleClick(self.ui.viewWaypointCheck)  # noqa: ARG005
        self.ui.viewCameraCheck.mouseDoubleClickEvent = lambda a0: self.onInstanceVisibilityDoubleClick(self.ui.viewCameraCheck)  # noqa: ARG005
        self.ui.viewStoreCheck.mouseDoubleClickEvent = lambda a0: self.onInstanceVisibilityDoubleClick(self.ui.viewStoreCheck)  # noqa: ARG005

        # Undo/Redo
        self.ui.actionUndo.triggered.connect(lambda: print("Undo signal") or self._controls.undoStack.undo())
        self.ui.actionUndo.triggered.connect(lambda: print("Redo signal") or self._controls.undoStack.redo())

        # View
        self.ui.actionZoomIn.triggered.connect(lambda: self.ui.renderArea.camera.nudgeZoom(1))
        self.ui.actionZoomOut.triggered.connect(lambda: self.ui.renderArea.camera.nudgeZoom(-1))
        self.ui.actionRecentreCamera.triggered.connect(self.ui.renderArea.centerCamera)
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
        """Load a resource from a file.

        Args:
        ----
            filepath: {Path or filename to load from}
            resref: {Unique identifier for the resource}
            restype: {The type of the resource}
            data: {The raw data of the resource}.

        Processing Logic:
        ----------------
            - Call super().load() to load base resource
            - Define search order for layout files
            - Load layout if found in search locations
            - Parse git data and call _loadGIT()
        """
        super().load(filepath, resref, restype, data)

        order: list[SearchLocation] = [SearchLocation.OVERRIDE, SearchLocation.CHITIN, SearchLocation.MODULES]
        result: ResourceResult | None = self._installation.resource(resref, ResourceType.LYT, order)
        if result:
            self._logger.debug("Found GITEditor layout for '%s'", filepath)
            self.loadLayout(read_lyt(result.data))
        else:
            self._logger.warning("Missing layout %s.lyt, needed for GITEditor '%s.%s'", resref, resref, restype)

        git = read_git(data)
        self._loadGIT(git)

    def _loadGIT(self, git: GIT):
        """Load a GIT instance.

        Args:
        ----
            git: The GIT instance to load

        Processing Logic:
        ----------------
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

    def closeEvent(self, event: QCloseEvent):
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Really quit the GIT editor? You may lose unsaved changes.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()  # Let the window close
        else:
            event.ignore()  # Ignore the close event

    def loadLayout(self, layout: LYT):
        """Load layout walkmeshes into the UI renderer.

        Args:
        ----
            layout (LYT): Layout to load walkmeshes from

        Processing Logic:
        ----------------
            - Iterate through each room in the layout
            - Get the highest priority walkmesh asset for the room from the installation
            - If a walkmesh asset is found, read it and add it to a list
            - Set the list of walkmeshes on the UI renderer.
        """
        walkmeshes: list[BWM] = []
        for room in layout.rooms:
            order: list[SearchLocation] = [SearchLocation.OVERRIDE, SearchLocation.CHITIN, SearchLocation.MODULES]
            findBWM: ResourceResult | None = self._installation.resource(room.model, ResourceType.WOK, order)
            if findBWM is not None:
                try:
                    walkmeshes.append(read_bwm(findBWM.data))
                except (ValueError, OSError):
                    self._logger.exception("Corrupted walkmesh cannot be loaded: '%s.wok'", room.model)
            else:
                self._logger.warning("Missing walkmesh '%s.wok'", room.model)

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
        """Get external name of a GIT instance.

        Args:
        ----
            instance: The GIT instance object

        Returns:
        -------
            name: The external name of the instance or None

        Processing Logic:
        ----------------
            - Extract identifier from instance
            - Check if identifier is present in name buffer
            - If not present, get resource from installation using identifier
            - Extract name from resource data
            - Save name in buffer
            - Return name from buffer.
        """
        resid: ResourceIdentifier | None = instance.identifier()
        if resid not in self.nameBuffer:
            res: ResourceResult | None = self._installation.resource(resid.resname, resid.restype)
            if res is None:
                return None
            self.nameBuffer[resid] = self._installation.string(extract_name(res.data))
        return self.nameBuffer[resid]

    def getInstanceExternalTag(self, instance: GITInstance) -> str | None:
        """Gets external tag for the given instance.

        Args:
        ----
            instance: The instance to get tag for

        Returns:
        -------
            tag: The external tag associated with the instance or None

        Processing Logic:
        ----------------
            - Get resource identifier from instance
            - Check if tag is already cached for this identifier
            - If not cached, call installation to get resource and extract tag from resource data
            - Cache tag in buffer and return cached tag.
        """
        resid: ResourceIdentifier | None = instance.identifier()
        assert resid is not None, f"resid cannot be None in getInstanceExternalTag({instance!r})"
        if resid not in self.tagBuffer:
            res: ResourceResult | None = self._installation.resource(resid.resname, resid.restype)
            if res is None:
                return None
            self.tagBuffer[resid] = extract_tag_from_gff(res.data)
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
        if not instance:
            self._logger.warning("No instance selected - moveCameraToSelection")
            return
        self.ui.renderArea.camera.setPosition(instance.position.x, instance.position.y)

    # region Mode Calls
    def openListContextMenu(self, item: QListWidgetItem, point: QPoint): ...

    def updateVisibility(self):
        self._mode.updateVisibility()

    def selectUnderneath(self):
        self._mode.selectUnderneath()

    def deleteSelected(self, *, noUndoStack: bool = False):
        self._mode.deleteSelected(noUndoStack=noUndoStack)

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
        globalPoint: QPoint = self.ui.renderArea.mapToGlobal(point)
        world: Vector3 = self.ui.renderArea.toWorldCoords(point.x(), point.y())
        self._mode.onRenderContextMenu(Vector2.from_vector3(world), globalPoint)

    def onFilterEdited(self):
        self._mode.onFilterEdited(self.ui.filterEdit.text())

    def onItemSelectionChanged(self):
        self._mode.onItemSelectionChanged(self.ui.listWidget.currentItem())

    def onItemContextMenu(self, point: QPoint):
        globalPoint: QPoint = self.ui.listWidget.mapToGlobal(point)
        item: QListWidgetItem | None = self.ui.listWidget.currentItem()
        assert item is not None, f"item cannot be None in {self!r}.onItemContextMenu({point!r})"
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
        worldDelta: Vector2 = self.ui.renderArea.toWorldDelta(delta.x, delta.y)
        world: Vector3 = self.ui.renderArea.toWorldCoords(screen.x, screen.y)
        self._controls.onMouseMoved(screen, delta, Vector2.from_vector3(world), worldDelta, buttons, keys)
        self._mode.updateStatusBar(Vector2.from_vector3(world))

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
    def __init__(
        self,
        editor: GITEditor | ModuleDesigner,
        installation: HTInstallation,
        git: GIT,
    ):
        self._editor: GITEditor | ModuleDesigner = editor
        self._installation: HTInstallation = installation
        self._git: GIT = git

        self._ui = editor.ui
        self.renderer2d = editor.ui.renderArea if isinstance(editor, GITEditor) else editor.ui.flatRenderer

    def listWidget(self):
        return self._ui.listWidget if isinstance(self._editor, GITEditor) else self._ui.instanceList

    @abstractmethod
    def onItemSelectionChanged(self, item: QListWidgetItem): ...

    @abstractmethod
    def onFilterEdited(self, text: str): ...

    @abstractmethod
    def onRenderContextMenu(self, world: Vector2, screen: QPoint): ...

    @abstractmethod
    def openListContextMenu(self, item: QListWidgetItem, screen: QPoint): ...

    @abstractmethod
    def updateVisibility(self): ...

    @abstractmethod
    def selectUnderneath(self): ...

    @abstractmethod
    def deleteSelected(self, *, noUndoStack: bool = False): ...

    @abstractmethod
    def duplicateSelected(self, position: Vector3): ...

    @abstractmethod
    def moveSelected(self, x: float, y: float): ...

    @abstractmethod
    def rotateSelected(self, angle: float): ...

    @abstractmethod
    def rotateSelectedToPoint(self, x: float, y: float): ...

    def moveCamera(self, x: float, y: float):
        self.renderer2d.camera.nudgePosition(x, y)

    def zoomCamera(self, amount: float):
        self.renderer2d.camera.nudgeZoom(amount)

    def rotateCamera(self, angle: float):
        self.renderer2d.camera.nudgeRotation(angle)

    @abstractmethod
    def updateStatusBar(self, world: Vector2): ...

    # endregion


class _InstanceMode(_Mode):
    def __init__(
        self,
        editor: GITEditor | ModuleDesigner,
        installation: HTInstallation,
        git: GIT,
    ):
        super().__init__(editor, installation, git)
        RobustLogger().debug("init InstanceMode")
        self.renderer2d.hideGeomPoints = True
        self.renderer2d.geometrySelection.clear()
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
        self.renderer2d.instanceSelection.select(instances)

        # set the list widget selection
        self.listWidget().blockSignals(True)
        for i in range(self.listWidget().count()):
            item = self.listWidget().item(i)
            if item is None:
                continue
            instance = item.data(QtCore.Qt.ItemDataRole.UserRole)
            if instance in instances:
                self.listWidget().setCurrentItem(item)
        self.listWidget().blockSignals(False)

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
        selection: list[GITInstance] = self.renderer2d.instanceSelection.all()

        if selection:
            instance: GITInstance = selection[-1]
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
        selection: list[GITInstance] = self.renderer2d.instanceSelection.all()

        if not selection:
            return
        instance: GITInstance = selection[-1]
        resname, restype = instance.identifier().unpack()

        order: list[SearchLocation] = [SearchLocation.CHITIN, SearchLocation.MODULES, SearchLocation.OVERRIDE]
        search: list[LocationResult] = self._installation.location(resname, restype, order)

        if isinstance(self._editor, GITEditor):
            assert self._editor._filepath is not None  # noqa: SLF001
            module_root: str = self._installation.get_module_root(self._editor._filepath.name).lower()
            edited_file_from_dot_mod = self._editor._filepath.suffix.lower() == ".mod"
        else:
            assert self._editor._module is not None  # noqa: SLF001
            module_root = self._editor._module.root_name().lower()
            edited_file_from_dot_mod = self._editor._module.dot_mod

        for i, loc in reversed(list(enumerate(search))):
            if loc.filepath.parent.name.lower() == "modules":
                loc_module_root = self._installation.get_module_root(loc.filepath.name.lower())
                loc_is_dot_mod = loc.filepath.suffix.lower() == ".mod"
                if loc_module_root != module_root:
                    RobustLogger.debug(f"Removing location '{loc.filepath}' (not in our module '{module_root}')")
                    search.pop(i)
                elif loc_is_dot_mod != edited_file_from_dot_mod:
                    RobustLogger.debug(f"Removing location '{loc.filepath}' due to rim/mod check")
                    search.pop(i)
        if len(search) > 1:
            selectionWindow = FileSelectionWindow(search, self._installation)
            selectionWindow.show()
            selectionWindow.activateWindow()
            add_window(selectionWindow)
        elif search:
            resource = search[0].as_file_resource()
            open_resource_editor(
                resource.filepath(),
                resource.resname(),
                resource.restype(),
                resource.data(),
                self._installation
            )

    def editSelectedInstanceGeometry(self):
        if self.renderer2d.instanceSelection.last():
            self.renderer2d.instanceSelection.last()
            self._editor.enterGeometryMode()

    def editSelectedInstanceSpawns(self):
        if self.renderer2d.instanceSelection.last():
            self.renderer2d.instanceSelection.last()
            # TODO
            #self._editor.enterSpawnMode()

    def addInstance(self, instance: GITInstance):
        if openInstanceDialog(self._editor, instance, self._installation):
            self._git.add(instance)
            undoStack = self._editor._controls.undoStack if isinstance(self._editor, GITEditor) else self._editor.undoStack  # noqa: SLF001
            undoStack.push(InsertCommand(self._git, instance, self._editor))
            self.buildList()

    def addInstanceActionsToMenu(self, instance: GITInstance, menu: QMenu):
        """Adds instance actions to a context menu.

        Args:
        ----
            instance: {The selected GIT instance object}
            menu: {The QMenu to add actions to}.
        """
        menu.addAction("Remove").triggered.connect(self.deleteSelected)
        if isinstance(self._editor, GITEditor):
            menu.addAction("Edit Instance").triggered.connect(self.editSelectedInstance)

        actionEditResource = menu.addAction("Edit Resource")
        actionEditResource.triggered.connect(self.editSelectedInstanceResource)
        actionEditResource.setEnabled(not isinstance(instance, GITCamera))
        menu.addAction(actionEditResource)

        if isinstance(instance, (GITEncounter, GITTrigger)):
            menu.addAction("Edit Geometry").triggered.connect(self.editSelectedInstanceGeometry)

        if isinstance(instance, GITEncounter):
            menu.addAction("Edit Spawn Points").triggered.connect(self.editSelectedInstanceSpawns)
        menu.addSeparator()
        self.addResourceSubMenu(menu, instance)

    def addResourceSubMenu(self, menu: QMenu, instance: GITInstance) -> QMenu:
        if isinstance(instance, GITCamera):
            return menu
        locations = self._installation.location(*instance.identifier().unpack())
        if not locations:
            return menu

        # Create the main context menu
        fileMenu = menu.addMenu("File Actions")
        assert fileMenu is not None

        if isinstance(self._editor, GITEditor):
            valid_filepaths = [self._editor._filepath]
        else:
            assert self._editor._module is not None  # noqa: SLF001
            valid_filepaths = [res.filepath() for res in self._editor._module.get_capsules() if res is not None]

        override_path = self._installation.override_path()
        # Iterate over each location to create submenus
        for result in locations:
            # Create a submenu for each location
            if result.filepath not in valid_filepaths:
                continue
            if result.filepath.is_relative_to(override_path):
                displayPath = result.filepath.relative_to(override_path.parent)
            else:
                displayPath = result.filepath.joinpath(str(instance.identifier())).relative_to(self._installation.path())
            locMenu: QMenu = fileMenu.addMenu(str(displayPath))
            resourceMenuBuilder = ResourceItems(resources=[result])
            resourceMenuBuilder.build_menu(locMenu)
        def moreInfo():
            selectionWindow = FileSelectionWindow(
                locations,
                self._installation,
            )
            selectionWindow.show()
            selectionWindow.activateWindow()
            add_window(selectionWindow)

        fileMenu.addAction("Details...").triggered.connect(moreInfo)
        return menu

    def setListItemLabel(self, item: QListWidgetItem, instance: GITInstance):
        """Sets the label text of a QListWidget item for a game instance.

        Args:
        ----
            item (QListWidgetItem): The list widget item
            instance (GITInstance): The game instance

        Sets the item data and tooltip, determines the label text based on instance type and editor settings, sets the item text and font if label not found.
        """
        item.setData(QtCore.Qt.ItemDataRole.UserRole, instance)
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
        elif isinstance(instance, GITPlaceable):
            if self._editor.settings.placeableLabel == "tag":
                name = self._editor.getInstanceExternalTag(instance)
            elif self._editor.settings.placeableLabel == "name":
                name = self._editor.getInstanceExternalName(instance)
        elif isinstance(instance, GITDoor):
            if self._editor.settings.doorLabel == "tag":
                name = instance.tag
            elif self._editor.settings.doorLabel == "name":
                name = self._editor.getInstanceExternalName(instance)
        elif isinstance(instance, GITStore):
            if self._editor.settings.storeLabel == "tag":
                name = self._editor.getInstanceExternalTag(instance)
            elif self._editor.settings.storeLabel == "name":
                name = self._editor.getInstanceExternalName(instance)
        elif isinstance(instance, GITSound):
            if self._editor.settings.soundLabel == "tag":
                name = self._editor.getInstanceExternalTag(instance)
            elif self._editor.settings.soundLabel == "name":
                name = self._editor.getInstanceExternalName(instance)
        elif isinstance(instance, GITWaypoint):
            if self._editor.settings.waypointLabel == "tag":
                name = instance.tag
            elif self._editor.settings.waypointLabel == "name":
                name = self._installation.string(instance.name, "")
        elif isinstance(instance, GITEncounter):
            if self._editor.settings.encounterLabel == "tag":
                name = self._editor.getInstanceExternalTag(instance)
            elif self._editor.settings.encounterLabel == "name":
                name = self._editor.getInstanceExternalName(instance)
        elif isinstance(instance, GITTrigger):
            if self._editor.settings.triggerLabel == "tag":
                name = instance.tag
            elif self._editor.settings.triggerLabel == "name":
                name = self._editor.getInstanceExternalName(instance)

        ident = instance.identifier()
        text: str = name or ""
        if not name:
            text = ident and ident.resname or ""
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
        self.renderer2d.instanceFilter = text
        self.buildList()

    def onItemSelectionChanged(self, item: QListWidgetItem):
        if item is None:
            self.setSelection([])
        else:
            self.setSelection([item.data(QtCore.Qt.ItemDataRole.UserRole)])

    def updateStatusBar(self, world: Vector2):
        if self.renderer2d.instancesUnderMouse() and self.renderer2d.instancesUnderMouse()[-1] is not None:
            instance = self.renderer2d.instancesUnderMouse()[-1]
            resname = "" if isinstance(instance, GITCamera) else instance.identifier().resname
            self._editor.statusBar().showMessage(f"({world.x:.1f}, {world.y:.1f}) {resname}")
        else:
            self._editor.statusBar().showMessage(f"({world.x:.1f}, {world.y:.1f})")

    def openListContextMenu(self, item: QListWidgetItem, point: QPoint):
        if item is None:
            return

        instance = item.data(QtCore.Qt.ItemDataRole.UserRole)
        menu = QMenu(self.listWidget())

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
        menu = QMenu(self.listWidget())
        self._getRenderContextMenu(world, menu)
        menu.popup(point)

    def _getRenderContextMenu(self, world: Vector2, menu: QMenu):
        underMouse: list[GITInstance] = self.renderer2d.instancesUnderMouse()
        if not self.renderer2d.instanceSelection.isEmpty():
            self.addInstanceActionsToMenu(self.renderer2d.instanceSelection.last(), menu)
        else:
            self.addInsertActionsToMenu(menu, world)
        if underMouse:
            menu.addSeparator()
            for instance in underMouse:
                icon = QIcon(self.renderer2d.instancePixmap(instance))
                reference = "" if instance.identifier() is None else instance.identifier().resname
                index = self._editor.git().index(instance)

                instanceAction = menu.addAction(icon, f"[{index}] {reference}")
                instanceAction.triggered.connect(lambda _=None, inst=instance: self.setSelection([inst]))
                instanceAction.setEnabled(instance not in self.renderer2d.instanceSelection.all())
                menu.addAction(instanceAction)

    def addInsertActionsToMenu(self, menu: QMenu, world: Vector2):
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
        self.listWidget().clear()

        def instanceSort(inst: GITInstance) -> str:
            textToSort: str = str(inst.camera_id) if isinstance(inst, GITCamera) else inst.identifier().resname
            return textToSort.rjust(9, "0") if isinstance(inst, GITCamera) else inst.identifier().restype.extension + textToSort

        instances: list[GITInstance] = sorted(self._git.instances(), key=instanceSort)
        for instance in instances:
            filterSource: str = str(instance.camera_id) if isinstance(instance, GITCamera) else instance.identifier().resname
            isVisible: bool | None = self.renderer2d.isInstanceVisible(instance)
            isFiltered: bool = self._ui.filterEdit.text().lower() in filterSource.lower()

            if isVisible and isFiltered:
                icon = QIcon(self.renderer2d.instancePixmap(instance))
                item = QListWidgetItem(icon, "")
                self.setListItemLabel(item, instance)
                self.listWidget().addItem(item)

    def updateVisibility(self):
        self.renderer2d.hideCreatures = not self._ui.viewCreatureCheck.isChecked()
        self.renderer2d.hidePlaceables = not self._ui.viewPlaceableCheck.isChecked()
        self.renderer2d.hideDoors = not self._ui.viewDoorCheck.isChecked()
        self.renderer2d.hideTriggers = not self._ui.viewTriggerCheck.isChecked()
        self.renderer2d.hideEncounters = not self._ui.viewEncounterCheck.isChecked()
        self.renderer2d.hideWaypoints = not self._ui.viewWaypointCheck.isChecked()
        self.renderer2d.hideSounds = not self._ui.viewSoundCheck.isChecked()
        self.renderer2d.hideStores = not self._ui.viewStoreCheck.isChecked()
        self.renderer2d.hideCameras = not self._ui.viewCameraCheck.isChecked()
        self.buildList()

    def selectUnderneath(self):
        underMouse: list[GITInstance] = self.renderer2d.instancesUnderMouse()
        selection: list[GITInstance] = self.renderer2d.instanceSelection.all()

        # Do not change the selection if the selected instance if its still underneath the mouse
        if selection and selection[0] in underMouse:
            RobustLogger().info(f"Not changing selection: selected instance '{selection[0].classification()}' is still underneath the mouse.")
            return

        if underMouse:
            self.setSelection([underMouse[-1]])
        else:
            self.setSelection([])

    def deleteSelected(self, *, noUndoStack: bool = False):
        selection = self.renderer2d.instanceSelection.all()
        if noUndoStack:
            for instance in selection:
                self._git.remove(instance)
                self.renderer2d.instanceSelection.remove(instance)
        else:
            undoStack = self._editor._controls.undoStack if isinstance(self._editor, GITEditor) else self._editor.undoStack
            undoStack.push(DeleteCommand(self._git, selection.copy(), self._editor))
        self.buildList()

    def duplicateSelected(self, position: Vector3, *, noUndoStack: bool = False):
        selection = self.renderer2d.instanceSelection.all()
        if selection:
            instance: GITInstance = deepcopy(selection[-1])
            if isinstance(instance, GITCamera):
                instance.camera_id = self._editor.git().next_camera_id()
            instance.position = position
            if noUndoStack:
                self._git.add(instance)
                self.buildList()
                self.setSelection([instance])
            else:
                undoStack = self._editor._controls.undoStack if isinstance(self._editor, GITEditor) else self._editor.undoStack
                undoStack.push(DuplicateCommand(self._git, [instance], self._editor))

    def moveSelected(
        self,
        x: float,
        y: float,
        *,
        noUndoStack: bool = False,
    ):
        if self._ui.lockInstancesCheck.isChecked():
            RobustLogger().info("Ignoring moveSelected for instancemode, lockInstancesCheck is checked.")
            return

        for instance in self.renderer2d.instanceSelection.all():
            instance.move(x, y, 0)

    def rotateSelected(self, angle: float):
        for instance in self.renderer2d.instanceSelection.all():
            if isinstance(instance, (GITCamera, GITCreature, GITDoor, GITPlaceable, GITStore, GITWaypoint)):
                instance.rotate(angle, 0, 0)

    def rotateSelectedToPoint(self, x: float, y: float):
        rotation_threshold = 0.05  # Threshold for rotation changes, adjust as needed
        for instance in self.renderer2d.instanceSelection.all():
            current_angle = -math.atan2(x - instance.position.x, y - instance.position.y)
            current_angle = (current_angle + math.pi) % (2 * math.pi) - math.pi  # Normalize to -π to π

            yaw = instance.yaw() or 0.01
            yaw = (yaw + math.pi) % (2 * math.pi) - math.pi  # Normalize to -π to π

            rotation_difference = yaw - current_angle
            # Normalize the rotation difference
            rotation_difference = (rotation_difference + math.pi) % (2 * math.pi) - math.pi

            if abs(rotation_difference) < rotation_threshold:
                continue  # Skip if the rotation change is too small

            if isinstance(instance, GITCamera):
                instance.rotate(yaw - current_angle, 0, 0)
            elif isinstance(instance, (GITCreature, GITDoor, GITPlaceable, GITStore, GITWaypoint)):
                instance.rotate(-yaw + current_angle, 0, 0)

    # endregion


class _GeometryMode(_Mode):
    def __init__(
        self,
        editor: GITEditor | ModuleDesigner,
        installation: HTInstallation,
        git: GIT,
        *,
        hideOthers: bool = True,
    ):
        super().__init__(editor, installation, git)

        if hideOthers:
            self.renderer2d.hideCreatures = True
            self.renderer2d.hideDoors = True
            self.renderer2d.hidePlaceables = True
            self.renderer2d.hideSounds = True
            self.renderer2d.hideStores = True
            self.renderer2d.hideCameras = True
            self.renderer2d.hideTriggers = True
            self.renderer2d.hideEncounters = True
            self.renderer2d.hideWaypoints = True
        else:
            self.renderer2d.hideEncounters = False
            self.renderer2d.hideTriggers = False
        self.renderer2d.hideGeomPoints = False

    def insertPointAtMouse(self):
        screen: QPoint = self.renderer2d.mapFromGlobal(self._editor.cursor().pos())
        world: Vector3 = self.renderer2d.toWorldCoords(screen.x(), screen.y())

        instance: GITInstance = self.renderer2d.instanceSelection.get(0)
        assert isinstance(instance, (GITEncounter, GITTrigger))
        point: Vector3 = world - instance.position
        newGeomPoint = GeomPoint(instance, point)
        instance.geometry.append(point)
        self.renderer2d.geomPointsUnderMouse().append(newGeomPoint)
        self.renderer2d.geometrySelection._selection.append(newGeomPoint)
        RobustLogger().debug(f"Inserting new geompoint, instance {instance.identifier()}. Total points: {len(list(instance.geometry))}")

    # region Interface Methods
    def onItemSelectionChanged(self, item: QListWidgetItem):
        pass

    def onFilterEdited(self, text: str):
        pass

    def updateStatusBar(self, world: Vector2):
        instance: GITInstance | None = self.renderer2d.instanceSelection.last()
        if instance:
            self._editor.statusBar().showMessage(f"({world.x:.1f}, {world.y:.1f}) Editing Geometry of {instance.identifier().resname}")

    def onRenderContextMenu(self, world: Vector2, screen: QPoint):
        menu = QMenu(self._editor)
        self._getRenderContextMenu(world, menu)
        menu.popup(screen)

    def _getRenderContextMenu(self, world: Vector2, menu: QMenu):
        if not self.renderer2d.geometrySelection.isEmpty():
            menu.addAction("Remove").triggered.connect(self.deleteSelected)

        if self.renderer2d.geometrySelection.count() == 0:
            menu.addAction("Insert").triggered.connect(self.insertPointAtMouse)

        menu.addSeparator()
        menu.addAction("Finish Editing").triggered.connect(self._editor.enterInstanceMode)

    def openListContextMenu(self, item: QListWidgetItem, screen: QPoint):
        pass

    def updateVisibility(self):
        pass

    def selectUnderneath(self):
        underMouse: list[GeomPoint] = self.renderer2d.geomPointsUnderMouse()
        selection: list[GeomPoint] = self.renderer2d.geometrySelection.all()

        # Do not change the selection if the selected instance if its still underneath the mouse
        if selection and selection[0] in underMouse:
            RobustLogger().info(f"Not changing selection: selected instance '{selection[0].instance.classification()}' is still underneath the mouse.")
            return
        self.renderer2d.geometrySelection.select(underMouse or [])

    def deleteSelected(self, *, noUndoStack: bool = False):
        vertex: GeomPoint | None = self.renderer2d.geometrySelection.last()
        if vertex is None:
            RobustLogger().error("Could not delete last GeomPoint, there's none selected.")
            return
        instance: GITInstance = vertex.instance
        RobustLogger().debug(f"Removing last geometry point for instance {instance.identifier()}")
        self.renderer2d.geometrySelection.remove(GeomPoint(instance, vertex.point))

    def duplicateSelected(self, position: Vector3):
        pass

    def moveSelected(self, x: float, y: float):
        for vertex in self.renderer2d.geometrySelection.all():
            vertex.point.x += x
            vertex.point.y += y

    def rotateSelected(self, angle: float):
        pass

    def rotateSelectedToPoint(self, x: float, y: float):
        pass

    # endregion


class _SpawnMode(_Mode): ...


def calculate_zoom_strength(delta_y: float, sensSetting: int) -> float:
    m = 0.00202
    b = 1
    factor_in = (m * sensSetting + b)
    return 1 / abs(factor_in) if delta_y < 0 else abs(factor_in)


class GITControlScheme:
    def __init__(self, editor: GITEditor):
        self.editor: GITEditor = editor
        self.settings: GITSettings = GITSettings()
        self.log: RobustLogger = RobustLogger()

        # Undo/Redo support setup.
        self.undoStack: QUndoStack = QUndoStack(self.editor)
        self.initialPositions: dict[GITInstance, Vector3] = {}
        self.initialRotations: dict[GITCamera | GITCreature | GITDoor | GITPlaceable | GITStore | GITWaypoint, Vector4 | float] = {}
        self.isDragMoving: bool = False
        self.isDragRotating: bool = False

    def onMouseScrolled(self, delta: Vector2, buttons: set[int], keys: set[int]):
        if self.zoomCamera.satisfied(buttons, keys):
            if not delta.y:
                return  # sometimes it'll be zero when holding middlemouse-down.
            sensSetting = ModuleDesignerSettings().zoomCameraSensitivity2d
            zoom_factor = calculate_zoom_strength(delta.y, sensSetting)
            #RobustLogger.debug(f"onMouseScrolled zoomCamera (delta.y={delta.y}, zoom_factor={zoom_factor}, sensSetting={sensSetting}))")
            self.editor.zoomCamera(zoom_factor)

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
        # sourcery skip: extract-duplicate-method, remove-redundant-if, split-or-ifs
        shouldPanCamera = self.panCamera.satisfied(buttons, keys)
        shouldRotateCamera = self.rotateCamera.satisfied(buttons, keys)

        # Adjust worldDelta if cursor is locked
        adjustedWorldDelta = worldDelta
        if shouldPanCamera or shouldRotateCamera:
            self.editor.ui.renderArea.doCursorLock(screen)
            adjustedWorldDelta = Vector2(-worldDelta.x, -worldDelta.y)

        if shouldPanCamera:
            moveSens = ModuleDesignerSettings().moveCameraSensitivity2d / 100
            #RobustLogger.debug(f"onMouseScrolled moveCamera (delta.y={screenDelta.y}, sensSetting={moveSens}))")
            self.editor.moveCamera(-worldDelta.x * moveSens, -worldDelta.y * moveSens)
        if shouldRotateCamera:
            self._handleCameraRotation(screenDelta)

        if self.moveSelected.satisfied(buttons, keys):
            if not self.isDragMoving and isinstance(self.editor._mode, _InstanceMode):  # noqa: SLF001
                #RobustLogger().debug("moveSelected instance GITControlScheme")
                selection: list[GITInstance] = self.editor._mode.renderer2d.instanceSelection.all()  # noqa: SLF001
                self.initialPositions = {instance: Vector3(*instance.position) for instance in selection}
                self.isDragMoving = True
            self.editor.moveSelected(adjustedWorldDelta.x, adjustedWorldDelta.y)
        if self.rotateSelectedToPoint.satisfied(buttons, keys):
            if (
                not self.isDragRotating
                and not self.editor.ui.lockInstancesCheck.isChecked()
                and isinstance(self.editor._mode, _InstanceMode)  # noqa: SLF001
            ):
                self.isDragRotating = True
                self.log.debug("rotateSelected instance in GITControlScheme")
                selection: list[GITInstance] = self.editor._mode.renderer2d.instanceSelection.all()  # noqa: SLF001
                for instance in selection:
                    if not isinstance(instance, (GITCamera, GITCreature, GITDoor, GITPlaceable, GITStore, GITWaypoint)):
                        continue  # doesn't support rotations.
                    self.initialRotations[instance] = instance.orientation if isinstance(instance, GITCamera) else instance.bearing
            self.editor.rotateSelectedToPoint(world.x, world.y)

    def _handleCameraRotation(self, screenDelta: Vector2):
        delta_magnitude = abs(screenDelta.x)
        direction = -1 if screenDelta.x < 0 else 1 if screenDelta.x > 0 else 0
        rotateSens = ModuleDesignerSettings().rotateCameraSensitivity2d / 1000
        rotateAmount = delta_magnitude * rotateSens * direction
        #RobustLogger.debug(f"onMouseScrolled rotateCamera (delta_value={delta_magnitude}, rotateAmount={rotateAmount}, sensSetting={rotateSens}))")
        self.editor.rotateCamera(rotateAmount)

    def handleUndoRedoFromLongActionFinished(self):
        # Check if we were dragging
        if self.isDragMoving:
            for instance, old_position in self.initialPositions.items():
                new_position = instance.position
                if old_position and new_position != old_position:
                    self.log.debug("GITControlScheme: Create the MoveCommand for undo/redo functionality")
                    move_command = MoveCommand(instance, old_position, new_position)
                    self.undoStack.push(move_command)
                elif not old_position:
                    self.log.debug("GITControlScheme: No old position %s", instance.resref)
                else:
                    self.log.debug("GITControlScheme: Both old and new positions are the same %s", instance.resref)

            # Reset for the next drag operation
            self.initialPositions.clear()
            self.log.debug("No longer drag moving GITControlScheme")
            self.isDragMoving = False

        if self.isDragRotating:
            for instance, old_rotation in self.initialRotations.items():
                new_rotation = instance.orientation if isinstance(instance, GITCamera) else instance.bearing
                if old_rotation and new_rotation != old_rotation:
                    self.log.debug(f"Create the RotateCommand for undo/redo functionality: {instance!r}")
                    self.undoStack.push(RotateCommand(instance, old_rotation, new_rotation))
                elif not old_rotation:
                    self.log.debug("No old rotation for %s", instance.resref)
                else:
                    self.log.debug("Both old and new rotations are the same for %s", instance.resref)

            # Reset for the next drag operation
            self.initialRotations.clear()
            self.log.debug("No longer drag rotating GITControlScheme")
            self.isDragRotating = False

    def onMousePressed(self, screen: Vector2, buttons: set[int], keys: set[int]):
        if self.duplicateSelected.satisfied(buttons, keys):
            position = self.editor.ui.renderArea.toWorldCoords(screen.x, screen.y)
            self.editor.duplicateSelected(position)
        if self.selectUnderneath.satisfied(buttons, keys):
            self.editor.selectUnderneath()

    def onMouseReleased(self, screen: Vector2, buttons: set[int], keys: set[int]):
        self.handleUndoRedoFromLongActionFinished()

    def onKeyboardPressed(self, buttons: set[int], keys: set[int]):
        if self.deleteSelected.satisfied(buttons, keys):
            if isinstance(self.editor._mode, _InstanceMode):  # noqa: SLF001
                selection: list[GITInstance] = self.editor._mode.renderer2d.instanceSelection.all()  # noqa: SLF001
                if selection:
                    self.undoStack.push(DeleteCommand(self.editor._git, selection.copy(), self.editor))  # noqa: SLF001
            self.editor.deleteSelected(noUndoStack=True)

        if self.toggleInstanceLock.satisfied(buttons, keys):
            self.editor.ui.lockInstancesCheck.setChecked(not self.editor.ui.lockInstancesCheck.isChecked())

    def onKeyboardReleased(self, buttons: set[int], keys: set[int]):
        self.handleUndoRedoFromLongActionFinished()

    # Use @property decorators to allow Users to change their settings without restarting the editor.
    @property
    def panCamera(self) -> ControlItem:
        return ControlItem(self.settings.moveCameraBind)

    @panCamera.setter
    def panCamera(self, value) -> None:
        ...

    @property
    def rotateCamera(self) -> ControlItem:
        return ControlItem(self.settings.rotateCameraBind)

    @rotateCamera.setter
    def rotateCamera(self, value) -> None:
        ...

    @property
    def zoomCamera(self) -> ControlItem:
        return ControlItem(self.settings.zoomCameraBind)

    @zoomCamera.setter
    def zoomCamera(self, value) -> None:
        ...

    @property
    def rotateSelectedToPoint(self) -> ControlItem:
        return ControlItem(self.settings.rotateSelectedToPointBind)

    @rotateSelectedToPoint.setter
    def rotateSelectedToPoint(self, value):
        ...

    @property
    def moveSelected(self) -> ControlItem:
        return ControlItem(self.settings.moveSelectedBind)

    @moveSelected.setter
    def moveSelected(self, value):
        ...

    @property
    def selectUnderneath(self) -> ControlItem:
        return ControlItem(self.settings.selectUnderneathBind)

    @selectUnderneath.setter
    def selectUnderneath(self, value):
        ...

    @property
    def deleteSelected(self) -> ControlItem:
        return ControlItem(self.settings.deleteSelectedBind)

    @deleteSelected.setter
    def deleteSelected(self, value):
        ...

    @property
    def duplicateSelected(self) -> ControlItem:
        return ControlItem(self.settings.duplicateSelectedBind)

    @duplicateSelected.setter
    def duplicateSelected(self, value):
        ...

    @property
    def toggleInstanceLock(self) -> ControlItem:
        return ControlItem(self.settings.toggleLockInstancesBind)

    @toggleInstanceLock.setter
    def toggleInstanceLock(self, value):
        ...
