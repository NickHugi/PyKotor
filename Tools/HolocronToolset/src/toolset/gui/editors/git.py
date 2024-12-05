from __future__ import annotations

import math
import os

from abc import ABC, abstractmethod
from copy import deepcopy
from typing import TYPE_CHECKING, Sequence

import qtpy

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy.QtCore import (
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QColor, QIcon, QKeySequence
from qtpy.QtWidgets import (
    QDialog,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QUndoCommand,  # pyright: ignore[reportPrivateImportUsage]
)

from pykotor.common.misc import Color
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.bwm import read_bwm
from pykotor.resource.formats.lyt import read_lyt
from pykotor.resource.generics.git import GIT, GITCamera, GITCreature, GITDoor, GITEncounter, GITPlaceable, GITSound, GITStore, GITTrigger, GITWaypoint, bytes_git, read_git
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
from toolset.gui.dialogs.load_from_location_result import FileSelectionWindow, ResourceItems
from toolset.gui.editor import Editor
from toolset.gui.widgets.renderer.walkmesh import GeomPoint
from toolset.gui.widgets.settings.editor_settings.git import GITSettings
from toolset.gui.widgets.settings.widgets.module_designer import ModuleDesignerSettings
from toolset.utils.window import add_window, open_resource_editor
from utility.common.geometry import SurfaceMaterial, Vector2, Vector3, Vector4

if TYPE_CHECKING:

    from qtpy.QtCore import QPoint
    from qtpy.QtGui import QCloseEvent, QKeyEvent
    from qtpy.QtWidgets import QCheckBox, QListWidget, QWidget

    from pykotor.extract.file import LocationResult, ResourceIdentifier, ResourceResult
    from pykotor.resource.formats.bwm import BWM
    from pykotor.resource.formats.lyt import LYT
    from pykotor.resource.generics.git import GITInstance
    from toolset.data.installation import HTInstallation
    from toolset.gui.windows.module_designer import ModuleDesigner

if qtpy.QT5:
    from qtpy.QtWidgets import QUndoStack
elif qtpy.QT6:
    from qtpy.QtGui import QUndoStack

class MoveCommand(QUndoCommand):
    def __init__(
        self,
        instance: GITInstance,
        old_position: Vector3,
        new_position: Vector3,
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
            assert isinstance(self.old_orientation, Vector4)
            self.instance.orientation = self.old_orientation
        else:
            assert isinstance(self.old_orientation, float)
            self.instance.bearing = self.old_orientation

    def redo(self):
        RobustLogger().debug(f"Redo rotation: {self.instance.identifier()} ({self.old_orientation} --> NEW {self.new_orientation})")
        if isinstance(self.instance, GITCamera):
            assert isinstance(self.new_orientation, Vector4)
            self.instance.orientation = self.new_orientation
        else:
            assert isinstance(self.new_orientation, float)
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
        self.instances: list[GITInstance] = list(instances)
        self.editor: GITEditor | ModuleDesigner = editor

    def undo(self):
        self.editor.enter_instance_mode()
        for instance in self.instances:
            if instance not in self.git.instances():
                print(f"{instance!r} not found in instances: no duplicate to undo.")
                continue
            RobustLogger().debug(f"Undo duplicate: {instance.identifier()}")
            if isinstance(self.editor, GITEditor):
                self.editor._mode.renderer2d.instance_selection.select([instance])  # noqa: SLF001
            else:
                self.editor.set_selection([instance])
            self.editor.delete_selected(no_undo_stack=True)
        self.rebuild_instance_list()

    def rebuild_instance_list(self):
        if isinstance(self.editor, GITEditor):
            self.editor.enter_instance_mode()
            assert isinstance(self.editor._mode, _InstanceMode)  # noqa: SLF001
            self.editor._mode.build_list()  # noqa: SLF001
        else:
            self.editor.enter_instance_mode()
            self.editor.rebuild_instance_list()


    def redo(self):
        for instance in self.instances:
            if instance in self.git.instances():
                print(f"{instance!r} already found in instances: no duplicate to redo.")
                continue
            RobustLogger().debug(f"Redo duplicate: {instance.identifier()}")
            self.git.add(instance)
            if isinstance(self.editor, GITEditor):
                self.editor._mode.renderer2d.instance_selection.select([instance])  # noqa: SLF001
            else:
                self.editor.set_selection([instance])
        self.rebuild_instance_list()


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
        self.rebuild_instance_list()

    def rebuild_instance_list(self):
        if isinstance(self.editor, GITEditor):
            self.editor.enter_instance_mode()
            assert isinstance(self.editor._mode, _InstanceMode)  # noqa: SLF001
            self.editor._mode.build_list()  # noqa: SLF001
        else:
            self.editor.enter_instance_mode()
            self.editor.rebuild_instance_list()

    def redo(self):
        RobustLogger().debug(f"Redo delete: {[repr(instance) for instance in self.instances]}")
        self.editor.enter_instance_mode()
        for instance in self.instances:
            if instance not in self.git.instances():
                print(f"{instance!r} not found in instances: no deletecommand to redo.")
                continue
            RobustLogger().debug(f"Redo delete: {instance!r}")
            if isinstance(self.editor, GITEditor):
                self.editor._mode.renderer2d.instance_selection.select([instance])  # noqa: SLF001
            else:
                self.editor.set_selection([instance])
            self.editor.delete_selected(no_undo_stack=True)
        self.rebuild_instance_list()


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
        self._first_run: bool = True
        self.editor: GITEditor | ModuleDesigner = editor

    def undo(self):
        RobustLogger().debug(f"Undo insert: {self.instance.identifier()}")
        self.git.remove(self.instance)
        self.rebuild_instance_list()

    def rebuild_instance_list(self):
        if isinstance(self.editor, GITEditor):
            old_mode = self.editor._mode  # noqa: SLF001
            self.editor.enter_instance_mode()
            assert isinstance(self.editor._mode, _InstanceMode)  # noqa: SLF001
            self.editor._mode.build_list()  # noqa: SLF001
            if isinstance(old_mode, _GeometryMode):
                self.editor.enter_geometry_mode()
            elif isinstance(old_mode, _SpawnMode):
                self.editor.enter_spawn_mode()
        else:
            self.editor.rebuild_instance_list()

    def redo(self):
        if self._first_run is True:
            print("Skipping first redo of InsertCommand.")
            self._first_run = False
            return
        RobustLogger().debug(f"Redo insert: {self.instance.identifier()}")
        self.git.add(self.instance)
        self.rebuild_instance_list()


def open_instance_dialog(
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

    return dialog.exec()


class GITEditor(Editor):
    sig_settings_updated = Signal(object)  # pyright: ignore[reportPrivateImportUsage]

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

        from toolset.uic.qtpy.editors.git import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_menus()
        self._setup_signals()
        self._setup_hotkeys()

        self._git: GIT = GIT()
        self._mode: _Mode = _InstanceMode(self, installation, self._git)
        self._controls: GITControlScheme = GITControlScheme(self)
        self._geom_instance: GITInstance | None = None  # Used to track which trigger/encounter you are editing

        self.ui.actionUndo.triggered.connect(lambda: print("Undo signal") or self._controls.undo_stack.undo())
        self.ui.actionRedo.triggered.connect(lambda: print("Redo signal") or self._controls.undo_stack.redo())

        self.settings = GITSettings()

        def int_color_to_qcolor(int_value: int) -> QColor:
            color = Color.from_rgba_integer(int_value)
            return QColor(int(color.r * 255), int(color.g * 255), int(color.b * 255), int(color.a * 255))

        self.material_colors: dict[SurfaceMaterial, QColor] = {
            SurfaceMaterial.UNDEFINED: int_color_to_qcolor(self.settings.undefinedMaterialColour),
            SurfaceMaterial.OBSCURING: int_color_to_qcolor(self.settings.obscuringMaterialColour),
            SurfaceMaterial.DIRT: int_color_to_qcolor(self.settings.dirtMaterialColour),
            SurfaceMaterial.GRASS: int_color_to_qcolor(self.settings.grassMaterialColour),
            SurfaceMaterial.STONE: int_color_to_qcolor(self.settings.stoneMaterialColour),
            SurfaceMaterial.WOOD: int_color_to_qcolor(self.settings.woodMaterialColour),
            SurfaceMaterial.WATER: int_color_to_qcolor(self.settings.waterMaterialColour),
            SurfaceMaterial.NON_WALK: int_color_to_qcolor(self.settings.nonWalkMaterialColour),
            SurfaceMaterial.TRANSPARENT: int_color_to_qcolor(self.settings.transparentMaterialColour),
            SurfaceMaterial.CARPET: int_color_to_qcolor(self.settings.carpetMaterialColour),
            SurfaceMaterial.METAL: int_color_to_qcolor(self.settings.metalMaterialColour),
            SurfaceMaterial.PUDDLES: int_color_to_qcolor(self.settings.puddlesMaterialColour),
            SurfaceMaterial.SWAMP: int_color_to_qcolor(self.settings.swampMaterialColour),
            SurfaceMaterial.MUD: int_color_to_qcolor(self.settings.mudMaterialColour),
            SurfaceMaterial.LEAVES: int_color_to_qcolor(self.settings.leavesMaterialColour),
            SurfaceMaterial.LAVA: int_color_to_qcolor(self.settings.lavaMaterialColour),
            SurfaceMaterial.BOTTOMLESS_PIT: int_color_to_qcolor(self.settings.bottomlessPitMaterialColour),
            SurfaceMaterial.DEEP_WATER: int_color_to_qcolor(self.settings.deepWaterMaterialColour),
            SurfaceMaterial.DOOR: int_color_to_qcolor(self.settings.doorMaterialColour),
            SurfaceMaterial.NON_WALK_GRASS: int_color_to_qcolor(self.settings.nonWalkGrassMaterialColour),
            SurfaceMaterial.TRIGGER: int_color_to_qcolor(self.settings.nonWalkGrassMaterialColour),
        }
        self.name_buffer: dict[ResourceIdentifier, str] = {}
        self.tag_buffer: dict[ResourceIdentifier, str] = {}

        self.ui.renderArea.material_colors = self.material_colors
        self.ui.renderArea.hide_walkmesh_edges = True
        self.ui.renderArea.highlight_boundaries = False

        self.new()

    def _setup_hotkeys(self):  # TODO: use GlobalSettings() defined hotkeys
        self.ui.actionDeleteSelected.setShortcut(QKeySequence("Del"))  # type: ignore[arg-type]
        self.ui.actionZoomIn.setShortcut(QKeySequence("+"))  # type: ignore[arg-type]
        self.ui.actionZoomOut.setShortcut(QKeySequence("-"))  # type: ignore[arg-type]
        self.ui.actionUndo.setShortcut(QKeySequence("Ctrl+Z"))  # type: ignore[arg-type]
        self.ui.actionRedo.setShortcut(QKeySequence("Ctrl+Shift+Z"))  # type: ignore[arg-type]

    def _setup_signals(self):
        self.ui.renderArea.sig_mouse_pressed.connect(self.on_mouse_pressed)
        self.ui.renderArea.sig_mouse_moved.connect(self.on_mouse_moved)
        self.ui.renderArea.sig_mouse_scrolled.connect(self.on_mouse_scrolled)
        self.ui.renderArea.sig_mouse_released.connect(self.on_mouse_released)
        self.ui.renderArea.sig_key_pressed.connect(self.on_key_pressed)
        self.ui.renderArea.customContextMenuRequested.connect(self.on_context_menu)

        self.ui.filterEdit.textEdited.connect(self.on_filter_edited)
        self.ui.listWidget.doubleClicked.connect(self.move_camera_to_selection)
        self.ui.listWidget.itemSelectionChanged.connect(self.on_item_selection_changed)
        self.ui.listWidget.customContextMenuRequested.connect(self.on_item_context_menu)

        self.ui.viewCreatureCheck.toggled.connect(self.update_visibility)
        self.ui.viewPlaceableCheck.toggled.connect(self.update_visibility)
        self.ui.viewDoorCheck.toggled.connect(self.update_visibility)
        self.ui.viewSoundCheck.toggled.connect(self.update_visibility)
        self.ui.viewTriggerCheck.toggled.connect(self.update_visibility)
        self.ui.viewEncounterCheck.toggled.connect(self.update_visibility)
        self.ui.viewWaypointCheck.toggled.connect(self.update_visibility)
        self.ui.viewCameraCheck.toggled.connect(self.update_visibility)
        self.ui.viewStoreCheck.toggled.connect(self.update_visibility)

        self.ui.viewCreatureCheck.mouseDoubleClickEvent = lambda a0: self.on_instance_visibility_double_click(self.ui.viewCreatureCheck)  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue]
        self.ui.viewPlaceableCheck.mouseDoubleClickEvent = lambda a0: self.on_instance_visibility_double_click(self.ui.viewPlaceableCheck)  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue]
        self.ui.viewDoorCheck.mouseDoubleClickEvent = lambda a0: self.on_instance_visibility_double_click(self.ui.viewDoorCheck)  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue]
        self.ui.viewSoundCheck.mouseDoubleClickEvent = lambda a0: self.on_instance_visibility_double_click(self.ui.viewSoundCheck)  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue]
        self.ui.viewTriggerCheck.mouseDoubleClickEvent = lambda a0: self.on_instance_visibility_double_click(self.ui.viewTriggerCheck)  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue]
        self.ui.viewEncounterCheck.mouseDoubleClickEvent = lambda a0: self.on_instance_visibility_double_click(self.ui.viewEncounterCheck)  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue]
        self.ui.viewWaypointCheck.mouseDoubleClickEvent = lambda a0: self.on_instance_visibility_double_click(self.ui.viewWaypointCheck)  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue]
        self.ui.viewCameraCheck.mouseDoubleClickEvent = lambda a0: self.on_instance_visibility_double_click(self.ui.viewCameraCheck)  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue]
        self.ui.viewStoreCheck.mouseDoubleClickEvent = lambda a0: self.on_instance_visibility_double_click(self.ui.viewStoreCheck)  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue]

        # Undo/Redo
        self.ui.actionUndo.triggered.connect(lambda: print("Undo signal") or self._controls.undo_stack.undo())
        self.ui.actionUndo.triggered.connect(lambda: print("Redo signal") or self._controls.undo_stack.redo())

        # View
        self.ui.actionZoomIn.triggered.connect(lambda: self.ui.renderArea.camera.nudge_zoom(1))
        self.ui.actionZoomOut.triggered.connect(lambda: self.ui.renderArea.camera.nudge_zoom(-1))
        self.ui.actionRecentreCamera.triggered.connect(self.ui.renderArea.center_camera)
        # View -> Creature Labels
        self.ui.actionUseCreatureResRef.triggered.connect(lambda: setattr(self.settings, "creatureLabel", "resref"))
        self.ui.actionUseCreatureResRef.triggered.connect(self.update_visibility)
        self.ui.actionUseCreatureTag.triggered.connect(lambda: setattr(self.settings, "creatureLabel", "tag"))
        self.ui.actionUseCreatureTag.triggered.connect(self.update_visibility)
        self.ui.actionUseCreatureName.triggered.connect(lambda: setattr(self.settings, "creatureLabel", "name"))
        self.ui.actionUseCreatureName.triggered.connect(self.update_visibility)
        # View -> Door Labels
        self.ui.actionUseDoorResRef.triggered.connect(lambda: setattr(self.settings, "doorLabel", "resref"))
        self.ui.actionUseDoorResRef.triggered.connect(self.update_visibility)
        self.ui.actionUseDoorTag.triggered.connect(lambda: setattr(self.settings, "doorLabel", "tag"))
        self.ui.actionUseDoorTag.triggered.connect(self.update_visibility)
        self.ui.actionUseDoorName.triggered.connect(lambda: setattr(self.settings, "doorLabel", "name"))
        self.ui.actionUseDoorName.triggered.connect(self.update_visibility)
        # View -> Placeable Labels
        self.ui.actionUsePlaceableResRef.triggered.connect(lambda: setattr(self.settings, "placeableLabel", "resref"))
        self.ui.actionUsePlaceableResRef.triggered.connect(self.update_visibility)
        self.ui.actionUsePlaceableName.triggered.connect(lambda: setattr(self.settings, "placeableLabel", "name"))
        self.ui.actionUsePlaceableName.triggered.connect(self.update_visibility)
        self.ui.actionUsePlaceableTag.triggered.connect(lambda: setattr(self.settings, "placeableLabel", "tag"))
        self.ui.actionUsePlaceableTag.triggered.connect(self.update_visibility)
        # View -> Merchant Labels
        self.ui.actionUseMerchantResRef.triggered.connect(lambda: setattr(self.settings, "storeLabel", "resref"))
        self.ui.actionUseMerchantResRef.triggered.connect(self.update_visibility)
        self.ui.actionUseMerchantName.triggered.connect(lambda: setattr(self.settings, "storeLabel", "name"))
        self.ui.actionUseMerchantName.triggered.connect(self.update_visibility)
        self.ui.actionUseMerchantTag.triggered.connect(lambda: setattr(self.settings, "storeLabel", "tag"))
        self.ui.actionUseMerchantTag.triggered.connect(self.update_visibility)
        # View -> Sound Labels
        self.ui.actionUseSoundResRef.triggered.connect(lambda: setattr(self.settings, "soundLabel", "resref"))
        self.ui.actionUseSoundResRef.triggered.connect(self.update_visibility)
        self.ui.actionUseSoundName.triggered.connect(lambda: setattr(self.settings, "soundLabel", "name"))
        self.ui.actionUseSoundName.triggered.connect(self.update_visibility)
        self.ui.actionUseSoundTag.triggered.connect(lambda: setattr(self.settings, "soundLabel", "tag"))
        self.ui.actionUseSoundTag.triggered.connect(self.update_visibility)
        # View -> Waypoint Labels
        self.ui.actionUseWaypointResRef.triggered.connect(lambda: setattr(self.settings, "waypointLabel", "resref"))
        self.ui.actionUseWaypointResRef.triggered.connect(self.update_visibility)
        self.ui.actionUseWaypointName.triggered.connect(lambda: setattr(self.settings, "waypointLabel", "name"))
        self.ui.actionUseWaypointName.triggered.connect(self.update_visibility)
        self.ui.actionUseWaypointTag.triggered.connect(lambda: setattr(self.settings, "waypointLabel", "tag"))
        self.ui.actionUseWaypointTag.triggered.connect(self.update_visibility)
        # View -> Encounter Labels
        self.ui.actionUseEncounterResRef.triggered.connect(lambda: setattr(self.settings, "encounterLabel", "resref"))
        self.ui.actionUseEncounterResRef.triggered.connect(self.update_visibility)
        self.ui.actionUseEncounterName.triggered.connect(lambda: setattr(self.settings, "encounterLabel", "name"))
        self.ui.actionUseEncounterName.triggered.connect(self.update_visibility)
        self.ui.actionUseEncounterTag.triggered.connect(lambda: setattr(self.settings, "encounterLabel", "tag"))
        self.ui.actionUseEncounterTag.triggered.connect(self.update_visibility)
        # View -> Trigger Labels
        self.ui.actionUseTriggerResRef.triggered.connect(lambda: setattr(self.settings, "triggerLabel", "resref"))
        self.ui.actionUseTriggerResRef.triggered.connect(self.update_visibility)
        self.ui.actionUseTriggerTag.triggered.connect(lambda: setattr(self.settings, "triggerLabel", "tag"))
        self.ui.actionUseTriggerTag.triggered.connect(self.update_visibility)
        self.ui.actionUseTriggerName.triggered.connect(lambda: setattr(self.settings, "triggerLabel", "name"))
        self.ui.actionUseTriggerName.triggered.connect(self.update_visibility)

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
            self.load_layout(read_lyt(result.data))
        else:
            self._logger.warning("Missing layout %s.lyt, needed for GITEditor '%s.%s'", resref, resref, restype)

        git = read_git(data)
        self._loadGIT(git)

    def _loadGIT(self, git: GIT):
        self._git = git
        self.ui.renderArea.set_git(self._git)
        self.ui.renderArea.center_camera()
        self._mode = _InstanceMode(self, self._installation, self._git)
        self.update_visibility()

    def build(self) -> tuple[bytes, bytes]:
        return bytes_git(self._git), b""

    def new(self):
        super().new()

    def closeEvent(self, event: QCloseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
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

    def load_layout(self, layout: LYT):
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
            find_bwm: ResourceResult | None = self._installation.resource(room.model, ResourceType.WOK, order)
            if find_bwm is not None:
                try:
                    walkmeshes.append(read_bwm(find_bwm.data))
                except (ValueError, OSError):
                    self._logger.exception("Corrupted walkmesh cannot be loaded: '%s.wok'", room.model)
            else:
                self._logger.warning("Missing walkmesh '%s.wok'", room.model)

        self.ui.renderArea.set_walkmeshes(walkmeshes)

    def git(self) -> GIT:
        return self._git

    def set_mode(self, mode: _Mode):
        self._mode = mode

    def on_instance_visibility_double_click(self, checkbox: QCheckBox):
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

    def get_instance_external_name(self, instance: GITInstance) -> str | None:
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
        if resid not in self.name_buffer:
            res: ResourceResult | None = self._installation.resource(resid.resname, resid.restype)
            if res is None:
                return None
            self.name_buffer[resid] = self._installation.string(extract_name(res.data))
        return self.name_buffer[resid]

    def get_instance_external_tag(self, instance: GITInstance) -> str | None:
        res_ident: ResourceIdentifier | None = instance.identifier()
        assert res_ident is not None, f"resid cannot be None in get_instance_external_tag({instance!r})"
        if res_ident not in self.tag_buffer:
            res: ResourceResult | None = self._installation.resource(res_ident.resname, res_ident.restype)
            if res is None:
                return None
            self.tag_buffer[res_ident] = extract_tag_from_gff(res.data)
        return self.tag_buffer[res_ident]

    def enter_instance_mode(self):
        self._mode = _InstanceMode(self, self._installation, self._git)

    def enter_geometry_mode(self):
        self._mode = _GeometryMode(self, self._installation, self._git)

    def enter_spawn_mode(self):
        ...
        # TODO(NickHugi): Encounter spawn mode.

    def move_camera_to_selection(self):
        instance = self.ui.renderArea.instance_selection.last()
        if not instance:
            self._logger.warning("No instance selected - moveCameraToSelection")
            return
        self.ui.renderArea.camera.set_position(instance.position.x, instance.position.y)

    # region Mode Calls
    def open_list_context_menu(self, item: QListWidgetItem, point: QPoint): ...

    def update_visibility(self):
        self._mode.update_visibility()

    def select_underneath(self):
        self._mode.select_underneath()

    def delete_selected(self, *, no_undo_stack: bool = False):
        self._mode.delete_selected(no_undo_stack=no_undo_stack)

    def duplicate_selected(self, position: Vector3):
        self._mode.duplicate_selected(position)

    def move_selected(self, x: float, y: float):
        self._mode.move_selected(x, y)

    def rotate_selected(self, angle: float):
        self._mode.rotate_selected(angle)

    def rotate_selected_to_point(self, x: float, y: float):
        self._mode.rotate_selected_to_point(x, y)

    def move_camera(self, x: float, y: float):
        self._mode.move_camera(x, y)

    def zoom_camera(self, amount: float):
        self._mode.zoom_camera(amount)

    def rotate_camera(self, angle: float):
        self._mode.rotate_camera(angle)

    # endregion

    # region Signal Callbacks
    def on_context_menu(self, point: QPoint):
        global_point: QPoint = self.ui.renderArea.mapToGlobal(point)
        world: Vector3 = self.ui.renderArea.to_world_coords(point.x(), point.y())
        self._mode.on_render_context_menu(Vector2.from_vector3(world), global_point)

    def on_filter_edited(self):
        self._mode.on_filter_edited(self.ui.filterEdit.text())

    def on_item_selection_changed(self):
        self._mode.on_item_selection_changed(self.ui.listWidget.currentItem())  # pyright: ignore[reportArgumentType]

    def on_item_context_menu(self, point: QPoint):
        global_point: QPoint = self.ui.listWidget.mapToGlobal(point)
        item: QListWidgetItem | None = self.ui.listWidget.currentItem()
        assert item is not None, f"item cannot be None in {self!r}.onItemContextMenu({point!r})"
        self._mode.open_list_context_menu(item, global_point)

    def on_mouse_moved(self, screen: Vector2, delta: Vector2, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        world_delta: Vector2 = self.ui.renderArea.to_world_delta(delta.x, delta.y)
        world: Vector3 = self.ui.renderArea.to_world_coords(screen.x, screen.y)
        self._controls.on_mouse_moved(screen, delta, Vector2.from_vector3(world), world_delta, buttons, keys)
        self._mode.update_status_bar(Vector2.from_vector3(world))

    def on_mouse_scrolled(self, delta: Vector2, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        self._controls.on_mouse_scrolled(delta, buttons, keys)

    def on_mouse_pressed(self, screen: Vector2, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        self._controls.on_mouse_pressed(screen, buttons, keys)

    def on_mouse_released(self, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        self._controls.on_mouse_released(Vector2(0, 0), buttons, keys)

    def on_key_pressed(self, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        self._controls.on_keyboard_pressed(buttons, keys)

    def keyPressEvent(self, e: QKeyEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        self.ui.renderArea.keyPressEvent(e)

    def keyReleaseEvent(self, e: QKeyEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
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

    def list_widget(self) -> QListWidget:
        return self._ui.listWidget if isinstance(self._editor, GITEditor) else self._ui.instanceList  # pyright: ignore[reportAttributeAccessIssue]

    @abstractmethod
    def on_item_selection_changed(self, item: QListWidgetItem): ...

    @abstractmethod
    def on_filter_edited(self, text: str): ...

    @abstractmethod
    def on_render_context_menu(self, world: Vector2, screen: QPoint): ...

    @abstractmethod
    def open_list_context_menu(self, item: QListWidgetItem, screen: QPoint): ...

    @abstractmethod
    def update_visibility(self): ...

    @abstractmethod
    def select_underneath(self): ...

    @abstractmethod
    def delete_selected(self, *, no_undo_stack: bool = False): ...

    @abstractmethod
    def duplicate_selected(self, position: Vector3): ...

    @abstractmethod
    def move_selected(self, x: float, y: float): ...

    @abstractmethod
    def rotate_selected(self, angle: float): ...

    @abstractmethod
    def rotate_selected_to_point(self, x: float, y: float): ...

    def move_camera(self, x: float, y: float):
        self.renderer2d.camera.nudge_position(x, y)

    def zoom_camera(self, amount: float):
        self.renderer2d.camera.nudge_zoom(amount)

    def rotate_camera(self, angle: float):
        self.renderer2d.camera.nudge_rotation(angle)

    @abstractmethod
    def update_status_bar(self, world: Vector2): ...

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
        self.renderer2d.hide_geom_points = True
        self.renderer2d.geometry_selection.clear()
        self.update_visibility()

    def set_selection(self, instances: list[GITInstance]):
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
        self.renderer2d.instance_selection.select(instances)

        # set the list widget selection
        self.list_widget().blockSignals(True)
        for i in range(self.list_widget().count()):
            item = self.list_widget().item(i)
            if item is None:
                continue
            instance = item.data(Qt.ItemDataRole.UserRole)
            if instance in instances:
                self.list_widget().setCurrentItem(item)
        self.list_widget().blockSignals(False)

    def edit_selected_instance(self):
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
        selection: list[GITInstance] = self.renderer2d.instance_selection.all()

        if selection:
            instance: GITInstance = selection[-1]
            open_instance_dialog(self._editor, instance, self._installation)
            self.build_list()

    def edit_selected_instance_resource(self):
        selection: list[GITInstance] = self.renderer2d.instance_selection.all()

        if not selection:
            return
        instance: GITInstance = selection[-1]
        resname, restype = instance.identifier().unpack()

        order: list[SearchLocation] = [SearchLocation.CHITIN, SearchLocation.MODULES, SearchLocation.OVERRIDE]
        search: list[LocationResult] = self._installation.location(resname, restype, order)

        if isinstance(self._editor, GITEditor):
            assert self._editor._filepath is not None  # noqa: SLF001
            module_root: str = self._installation.get_module_root(self._editor._filepath.name).lower()  # noqa: SLF001
            edited_file_from_dot_mod = self._editor._filepath.suffix.lower() == ".mod"  # noqa: SLF001
        else:
            assert self._editor._module is not None  # noqa: SLF001
            module_root = self._editor._module.root().lower()  # noqa: SLF001
            edited_file_from_dot_mod = self._editor._module.dot_mod  # noqa: SLF001

        for i, loc in reversed(list(enumerate(search))):
            if loc.filepath.parent.name.lower() == "modules":
                loc_module_root = self._installation.get_module_root(loc.filepath.name.lower())
                loc_is_dot_mod = loc.filepath.suffix.lower() == ".mod"
                if loc_module_root != module_root:
                    RobustLogger().debug(f"Removing location '{loc.filepath}' (not in our module '{module_root}')")
                    search.pop(i)
                elif loc_is_dot_mod != edited_file_from_dot_mod:
                    RobustLogger().debug(f"Removing location '{loc.filepath}' due to rim/mod check")
                    search.pop(i)
        if len(search) > 1:
            selection_window = FileSelectionWindow(search, self._installation)
            selection_window.show()
            selection_window.activateWindow()
            add_window(selection_window)
        elif search:
            open_resource_editor(search[0].as_file_resource(), self._installation)

    def edit_selected_instance_geometry(self):
        if self.renderer2d.instance_selection.last():
            self.renderer2d.instance_selection.last()
            self._editor.enter_geometry_mode()

    def edit_selected_instance_spawns(self):
        if self.renderer2d.instance_selection.last():
            self.renderer2d.instance_selection.last()
            # TODO
            #self._editor.enter_spawn_mode()

    def add_instance(self, instance: GITInstance):
        if open_instance_dialog(self._editor, instance, self._installation):
            self._git.add(instance)
            undo_stack = self._editor._controls.undo_stack if isinstance(self._editor, GITEditor) else self._editor.undo_stack  # noqa: SLF001
            undo_stack.push(InsertCommand(self._git, instance, self._editor))
            self.build_list()

    def add_instance_actions_to_menu(self, instance: GITInstance, menu: QMenu):
        """Adds instance actions to a context menu.

        Args:
        ----
            instance: {The selected GIT instance object}
            menu: {The QMenu to add actions to}.
        """
        menu.addAction("Remove").triggered.connect(self.delete_selected)
        if isinstance(self._editor, GITEditor):
            menu.addAction("Edit Instance").triggered.connect(self.edit_selected_instance)

        action_edit_resource = menu.addAction("Edit Resource")
        action_edit_resource.triggered.connect(self.edit_selected_instance_resource)
        action_edit_resource.setEnabled(not isinstance(instance, GITCamera))
        menu.addAction(action_edit_resource)

        if isinstance(instance, (GITEncounter, GITTrigger)):
            menu.addAction("Edit Geometry").triggered.connect(self.edit_selected_instance_geometry)

        if isinstance(instance, GITEncounter):
            menu.addAction("Edit Spawn Points").triggered.connect(self.edit_selected_instance_spawns)
        menu.addSeparator()
        self.add_resource_sub_menu(menu, instance)

    def add_resource_sub_menu(self, menu: QMenu, instance: GITInstance) -> QMenu:
        if isinstance(instance, GITCamera):
            return menu
        locations = self._installation.location(*instance.identifier().unpack())
        if not locations:
            return menu

        # Create the main context menu
        file_menu = menu.addMenu("File Actions")
        assert file_menu is not None

        if isinstance(self._editor, GITEditor):
            valid_filepaths = [self._editor._filepath]  # noqa: SLF001
        else:
            assert self._editor._module is not None  # noqa: SLF001
            valid_filepaths = [res.filepath() for res in self._editor._module.get_capsules() if res is not None]  # noqa: SLF001

        override_path = self._installation.override_path()
        # Iterate over each location to create submenus
        for result in locations:
            # Create a submenu for each location
            if result.filepath not in valid_filepaths:
                continue
            if os.path.commonpath([result.filepath, override_path]) == str(override_path):
                display_path = result.filepath.relative_to(override_path.parent)
            else:
                display_path = result.filepath.joinpath(str(instance.identifier())).relative_to(self._installation.path())
            loc_menu: QMenu = file_menu.addMenu(str(display_path))
            ResourceItems(resources=[result]).build_menu(loc_menu)
        def more_info():
            selection_window = FileSelectionWindow(locations, self._installation)
            selection_window.show()
            selection_window.activateWindow()
            add_window(selection_window)

        file_menu.addAction("Details...").triggered.connect(more_info)
        return menu

    def set_list_item_label(self, item: QListWidgetItem, instance: GITInstance):
        item.setData(Qt.ItemDataRole.UserRole, instance)
        item.setToolTip(self.get_instance_tooltip(instance))

        name: str | None = None

        assert isinstance(self._editor, GITEditor)
        if isinstance(instance, GITCamera):
            item.setText(str(instance.camera_id))
            return
        if isinstance(instance, GITCreature):
            if self._editor.settings.creatureLabel == "tag":
                name = self._editor.get_instance_external_tag(instance)
            elif self._editor.settings.creatureLabel == "name":
                name = self._editor.get_instance_external_name(instance)
        elif isinstance(instance, GITPlaceable):
            if self._editor.settings.placeableLabel == "tag":
                name = self._editor.get_instance_external_tag(instance)
            elif self._editor.settings.placeableLabel == "name":
                name = self._editor.get_instance_external_name(instance)
        elif isinstance(instance, GITDoor):
            if self._editor.settings.doorLabel == "tag":
                name = instance.tag
            elif self._editor.settings.doorLabel == "name":
                name = self._editor.get_instance_external_name(instance)
        elif isinstance(instance, GITStore):
            if self._editor.settings.storeLabel == "tag":
                name = self._editor.get_instance_external_tag(instance)
            elif self._editor.settings.storeLabel == "name":
                name = self._editor.get_instance_external_name(instance)
        elif isinstance(instance, GITSound):
            if self._editor.settings.soundLabel == "tag":
                name = self._editor.get_instance_external_tag(instance)
            elif self._editor.settings.soundLabel == "name":
                name = self._editor.get_instance_external_name(instance)
        elif isinstance(instance, GITWaypoint):
            if self._editor.settings.waypointLabel == "tag":
                name = instance.tag
            elif self._editor.settings.waypointLabel == "name":
                name = self._installation.string(instance.name, "")
        elif isinstance(instance, GITEncounter):
            if self._editor.settings.encounterLabel == "tag":
                name = self._editor.get_instance_external_tag(instance)
            elif self._editor.settings.encounterLabel == "name":
                name = self._editor.get_instance_external_name(instance)
        elif isinstance(instance, GITTrigger):
            if self._editor.settings.triggerLabel == "tag":
                name = instance.tag
            elif self._editor.settings.triggerLabel == "name":
                name = self._editor.get_instance_external_name(instance)

        ident = instance.identifier()
        text: str = name or ""
        if not name:
            text = ident and ident.resname or ""
            font = item.font()
            font.setItalic(True)
            item.setFont(font)

        item.setText(text)

    def get_instance_tooltip(self, instance: GITInstance) -> str:
        if isinstance(instance, GITCamera):
            return f"Struct Index: {self._git.index(instance)}\nCamera ID: {instance.camera_id}"
        return f"Struct Index: {self._git.index(instance)}\nResRef: {instance.identifier().resname}"

    # region Interface Methods
    def on_filter_edited(self, text: str):
        self.renderer2d.instance_filter = text
        self.build_list()

    def on_item_selection_changed(self, item: QListWidgetItem):
        self.set_selection([] if item is None else [item.data(Qt.ItemDataRole.UserRole)])

    def update_status_bar(self, world: Vector2):
        if self.renderer2d.instances_under_mouse() and self.renderer2d.instances_under_mouse()[-1] is not None:
            instance = self.renderer2d.instances_under_mouse()[-1]
            resname = "" if isinstance(instance, GITCamera) else instance.identifier().resname
            self._editor.statusBar().showMessage(f"({world.x:.1f}, {world.y:.1f}) {resname}")
        else:
            self._editor.statusBar().showMessage(f"({world.x:.1f}, {world.y:.1f})")

    def open_list_context_menu(self, item: QListWidgetItem, point: QPoint):  # pyright: ignore[reportIncompatibleMethodOverride]
        if item is None:
            return

        instance = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self.list_widget())

        self.add_instance_actions_to_menu(instance, menu)

        menu.popup(point)

    def on_render_context_menu(self, world: Vector2, point: QPoint):  # pyright: ignore[reportIncompatibleMethodOverride]
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
        menu = QMenu(self.list_widget())
        self._get_render_context_menu(world, menu)
        menu.popup(point)

    def _get_render_context_menu(self, world: Vector2, menu: QMenu):
        under_mouse: list[GITInstance] = self.renderer2d.instances_under_mouse()
        if not self.renderer2d.instance_selection.isEmpty():
            last = self.renderer2d.instance_selection.last()
            assert last is not None
            self.add_instance_actions_to_menu(last, menu)
        else:
            self.add_insert_actions_to_menu(menu, world)
        if under_mouse:
            menu.addSeparator()
            for instance in under_mouse:
                icon = QIcon(self.renderer2d.instance_pixmap(instance))
                reference = "" if instance.identifier() is None else instance.identifier().resname
                index = self._editor.git().index(instance)

                instance_action = menu.addAction(icon, f"[{index}] {reference}")
                instance_action.triggered.connect(lambda _=None, inst=instance: self.set_selection([inst]))
                instance_action.setEnabled(instance not in self.renderer2d.instance_selection.all())
                menu.addAction(instance_action)

    def add_insert_actions_to_menu(self, menu: QMenu, world: Vector2):
        menu.addAction("Insert Creature").triggered.connect(lambda: self.add_instance(GITCreature(world.x, world.y)))
        menu.addAction("Insert Door").triggered.connect(lambda: self.add_instance(GITDoor(world.x, world.y)))
        menu.addAction("Insert Placeable").triggered.connect(lambda: self.add_instance(GITPlaceable(world.x, world.y)))
        menu.addAction("Insert Store").triggered.connect(lambda: self.add_instance(GITStore(world.x, world.y)))
        menu.addAction("Insert Sound").triggered.connect(lambda: self.add_instance(GITSound(world.x, world.y)))
        menu.addAction("Insert Waypoint").triggered.connect(lambda: self.add_instance(GITWaypoint(world.x, world.y)))
        menu.addAction("Insert Camera").triggered.connect(lambda: self.add_instance(GITCamera(world.x, world.y)))
        menu.addAction("Insert Encounter").triggered.connect(lambda: self.add_instance(GITEncounter(world.x, world.y)))

        simple_trigger = GITTrigger(world.x, world.y)
        simple_trigger.geometry.extend(
            [
                Vector3(0.0, 0.0, 0.0),
                Vector3(3.0, 0.0, 0.0),
                Vector3(3.0, 3.0, 0.0),
                Vector3(0.0, 3.0, 0.0),
            ],
        )
        menu.addAction("Insert Trigger").triggered.connect(lambda: self.add_instance(simple_trigger))

    def build_list(self):
        self.list_widget().clear()

        def instance_sort(inst: GITInstance) -> str:
            text_to_sort: str = str(inst.camera_id) if isinstance(inst, GITCamera) else inst.identifier().resname
            return text_to_sort.rjust(9, "0") if isinstance(inst, GITCamera) else inst.identifier().restype.extension + text_to_sort

        instances: list[GITInstance] = sorted(self._git.instances(), key=instance_sort)
        for instance in instances:
            filter_source: str = str(instance.camera_id) if isinstance(instance, GITCamera) else instance.identifier().resname
            is_visible: bool | None = self.renderer2d.is_instance_visible(instance)
            is_filtered: bool = self._ui.filterEdit.text().lower() in filter_source.lower()  # pyright: ignore[reportAttributeAccessIssue]

            if is_visible and is_filtered:
                icon = QIcon(self.renderer2d.instance_pixmap(instance))
                item = QListWidgetItem(icon, "")
                self.set_list_item_label(item, instance)
                self.list_widget().addItem(item)

    def update_visibility(self):
        self.renderer2d.hide_creatures = not self._ui.viewCreatureCheck.isChecked()
        self.renderer2d.hide_placeables = not self._ui.viewPlaceableCheck.isChecked()
        self.renderer2d.hide_doors = not self._ui.viewDoorCheck.isChecked()
        self.renderer2d.hide_triggers = not self._ui.viewTriggerCheck.isChecked()
        self.renderer2d.hide_encounters = not self._ui.viewEncounterCheck.isChecked()
        self.renderer2d.hide_waypoints = not self._ui.viewWaypointCheck.isChecked()
        self.renderer2d.hide_sounds = not self._ui.viewSoundCheck.isChecked()
        self.renderer2d.hide_stores = not self._ui.viewStoreCheck.isChecked()
        self.renderer2d.hide_cameras = not self._ui.viewCameraCheck.isChecked()
        self.build_list()

    def select_underneath(self):
        under_mouse: list[GITInstance] = self.renderer2d.instances_under_mouse()
        selection: list[GITInstance] = self.renderer2d.instance_selection.all()

        # Do not change the selection if the selected instance if its still underneath the mouse
        if selection and selection[0] in under_mouse:
            RobustLogger().info(f"Not changing selection: selected instance '{selection[0].classification()}' is still underneath the mouse.")
            return

        if under_mouse:
            self.set_selection([under_mouse[-1]])
        else:
            self.set_selection([])

    def delete_selected(
        self,
        *,
        no_undo_stack: bool = False,
    ):
        selection = self.renderer2d.instance_selection.all()
        if no_undo_stack:
            for instance in selection:
                self._git.remove(instance)
                self.renderer2d.instance_selection.remove(instance)
        else:
            (self._editor._controls.undo_stack if isinstance(self._editor, GITEditor) else self._editor.undo_stack).push(DeleteCommand(self._git, selection.copy(), self._editor))  # noqa: SLF001
        self.build_list()

    def duplicate_selected(
        self,
        position: Vector3,
        *,
        no_undo_stack: bool = False,
    ):
        selection = self.renderer2d.instance_selection.all()
        if selection:
            instance: GITInstance = deepcopy(selection[-1])
            if isinstance(instance, GITCamera):
                instance.camera_id = self._editor.git().next_camera_id()
            instance.position = position
            if no_undo_stack:
                self._git.add(instance)
                self.build_list()
                self.set_selection([instance])
            else:
                undo_stack = (
                    self._editor._controls.undo_stack  # noqa: SLF001
                    if isinstance(self._editor, GITEditor)
                    else self._editor.undo_stack
                )
                undo_stack.push(DuplicateCommand(self._git, [instance], self._editor))

    def move_selected(
        self,
        x: float,
        y: float,
        *,
        no_undo_stack: bool = False,
    ):
        if self._ui.lockInstancesCheck.isChecked():
            RobustLogger().info("Ignoring move_selected for instancemode, lockInstancesCheck is checked.")
            return

        for instance in self.renderer2d.instance_selection.all():
            instance.move(x, y, 0)

    def rotate_selected(self, angle: float):
        for instance in self.renderer2d.instance_selection.all():
            if isinstance(instance, (GITCamera, GITCreature, GITDoor, GITPlaceable, GITStore, GITWaypoint)):
                instance.rotate(angle, 0, 0)

    def rotate_selected_to_point(self, x: float, y: float):
        rotation_threshold = 0.05  # Threshold for rotation changes, adjust as needed
        for instance in self.renderer2d.instance_selection.all():
            current_angle = -math.atan2(x - instance.position.x, y - instance.position.y)
            current_angle = (current_angle + math.pi) % (2 * math.pi) - math.pi  # Normalize to -π to π
            yaw = ((instance.yaw() or 0.01) + math.pi) % (2 * math.pi) - math.pi  # Normalize to -π to π
            rotation_difference = ((yaw - current_angle) + math.pi) % (2 * math.pi) - math.pi
            if abs(rotation_difference) < rotation_threshold:
                continue
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
        hide_others: bool = True,
    ):
        super().__init__(editor, installation, git)

        if hide_others:
            self.renderer2d.hide_creatures = True
            self.renderer2d.hide_doors = True
            self.renderer2d.hide_placeables = True
            self.renderer2d.hide_sounds = True
            self.renderer2d.hide_stores = True
            self.renderer2d.hide_cameras = True
            self.renderer2d.hide_triggers = True
            self.renderer2d.hide_encounters = True
            self.renderer2d.hide_waypoints = True
        else:
            self.renderer2d.hide_encounters = False
            self.renderer2d.hide_triggers = False
        self.renderer2d.hide_geom_points = False

    def insert_point_at_mouse(self):
        screen: QPoint = self.renderer2d.mapFromGlobal(self._editor.cursor().pos())
        world: Vector3 = self.renderer2d.to_world_coords(screen.x(), screen.y())

        instance: GITInstance = self.renderer2d.instance_selection.get(0)
        assert isinstance(instance, (GITEncounter, GITTrigger))
        point: Vector3 = world - instance.position
        new_geom_point = GeomPoint(instance, point)
        instance.geometry.append(point)
        self.renderer2d.geom_points_under_mouse().append(new_geom_point)
        self.renderer2d.geometry_selection._selection.append(new_geom_point)  # noqa: SLF001
        RobustLogger().debug(f"Inserting new geompoint, instance {instance.identifier()}. Total points: {len(list(instance.geometry))}")

    # region Interface Methods
    def on_item_selection_changed(self, item: QListWidgetItem):
        ...

    def on_filter_edited(self, text: str):
        ...

    def update_status_bar(self, world: Vector2):
        instance: GITInstance | None = self.renderer2d.instance_selection.last()
        if instance:
            self._editor.statusBar().showMessage(f"({world.x:.1f}, {world.y:.1f}) Editing Geometry of {instance.identifier().resname}")

    def on_render_context_menu(self, world: Vector2, screen: QPoint):
        menu = QMenu(self._editor)
        self._get_render_context_menu(world, menu)
        menu.popup(screen)

    def _get_render_context_menu(self, world: Vector2, menu: QMenu):
        if not self.renderer2d.geometry_selection.isEmpty():
            menu.addAction("Remove").triggered.connect(self.delete_selected)

        if self.renderer2d.geometry_selection.count() == 0:
            menu.addAction("Insert").triggered.connect(self.insert_point_at_mouse)

        menu.addSeparator()
        menu.addAction("Finish Editing").triggered.connect(self._editor.enter_instance_mode)

    def open_list_context_menu(self, item: QListWidgetItem, screen: QPoint):
        ...

    def update_visibility(self):
        ...

    def select_underneath(self):
        under_mouse: list[GeomPoint] = self.renderer2d.geom_points_under_mouse()
        selection: list[GeomPoint] = self.renderer2d.geometry_selection.all()

        # Do not change the selection if the selected instance if its still underneath the mouse
        if selection and selection[0] in under_mouse:
            RobustLogger().info(f"Not changing selection: selected instance '{selection[0].instance.classification()}' is still underneath the mouse.")
            return
        self.renderer2d.geometry_selection.select(under_mouse or [])

    def delete_selected(self, *, no_undo_stack: bool = False):
        vertex: GeomPoint | None = self.renderer2d.geometry_selection.last()
        if vertex is None:
            RobustLogger().error("Could not delete last GeomPoint, there's none selected.")
            return
        instance: GITInstance = vertex.instance
        RobustLogger().debug(f"Removing last geometry point for instance {instance.identifier()}")
        self.renderer2d.geometry_selection.remove(GeomPoint(instance, vertex.point))

    def duplicate_selected(self, position: Vector3):
        ...

    def move_selected(self, x: float, y: float):
        for vertex in self.renderer2d.geometry_selection.all():
            vertex.point.x += x
            vertex.point.y += y

    def rotate_selected(self, angle: float):
        ...

    def rotate_selected_to_point(self, x: float, y: float):
        ...
    # endregion


class _SpawnMode(_Mode):
    def on_item_selection_changed(self, item: QListWidgetItem):
        ...

    def on_filter_edited(self, text: str):
        ...


def calculate_zoom_strength(delta_y: float, sens_setting: int) -> float:
    m = 0.00202
    b = 1
    factor_in = (m * sens_setting + b)
    return 1 / abs(factor_in) if delta_y < 0 else abs(factor_in)


class GITControlScheme:
    def __init__(self, editor: GITEditor):
        self.editor: GITEditor = editor
        self.settings: GITSettings = GITSettings()

        self.undo_stack: QUndoStack = QUndoStack(self.editor)
        self.initial_positions: dict[GITInstance, Vector3] = {}
        self.initial_rotations: dict[GITCamera | GITCreature | GITDoor | GITPlaceable | GITStore | GITWaypoint, Vector4 | float] = {}
        self.is_drag_moving: bool = False
        self.is_drag_rotating: bool = False

    def on_mouse_scrolled(self, delta: Vector2, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        if self.zoom_camera.satisfied(buttons, keys):
            if not delta.y:
                return  # sometimes it'll be zero when holding middlemouse-down.
            sens_setting = ModuleDesignerSettings().zoomCameraSensitivity2d
            zoom_factor = calculate_zoom_strength(delta.y, sens_setting)
            #RobustLogger.debug(f"on_mouse_scrolled zoom_camera (delta.y={delta.y}, zoom_factor={zoom_factor}, sensSetting={sensSetting}))")
            self.editor.zoom_camera(zoom_factor)

    def on_mouse_moved(
        self,
        screen: Vector2,
        screen_delta: Vector2,
        world: Vector2,
        world_delta: Vector2,
        buttons: set[Qt.MouseButton],
        keys: set[Qt.Key],
    ):
        # sourcery skip: extract-duplicate-method, remove-redundant-if, split-or-ifs
        should_pan_camera = self.pan_camera.satisfied(buttons, keys)
        should_rotate_camera = self.rotate_camera.satisfied(buttons, keys)

        # Adjust world_delta if cursor is locked
        adjusted_world_delta = world_delta
        if should_pan_camera or should_rotate_camera:
            self.editor.ui.renderArea.do_cursor_lock(screen)
            adjusted_world_delta = Vector2(-world_delta.x, -world_delta.y)

        if should_pan_camera:
            moveSens = ModuleDesignerSettings().moveCameraSensitivity2d / 100
            #RobustLogger.debug(f"on_mouse_scrolled move_camera (delta.y={screenDelta.y}, sensSetting={moveSens}))")
            self.editor.move_camera(-world_delta.x * moveSens, -world_delta.y * moveSens)
        if should_rotate_camera:
            self._handle_camera_rotation(screen_delta)

        if self.move_selected.satisfied(buttons, keys):
            if not self.is_drag_moving and isinstance(self.editor._mode, _InstanceMode):  # noqa: SLF001
                #RobustLogger().debug("move_selected instance GITControlScheme")
                selection: list[GITInstance] = self.editor._mode.renderer2d.instance_selection.all()  # noqa: SLF001
                self.initial_positions = {instance: Vector3(*instance.position) for instance in selection}
                self.is_drag_moving = True
            self.editor.move_selected(adjusted_world_delta.x, adjusted_world_delta.y)
        if self.rotate_selected_to_point.satisfied(buttons, keys):
            if (
                not self.is_drag_rotating
                and not self.editor.ui.lockInstancesCheck.isChecked()
                and isinstance(self.editor._mode, _InstanceMode)  # noqa: SLF001
            ):
                self.is_drag_rotating = True
                RobustLogger().debug("rotateSelected instance in GITControlScheme")
                selection: list[GITInstance] = self.editor._mode.renderer2d.instance_selection.all()  # noqa: SLF001
                for instance in selection:
                    if not isinstance(instance, (GITCamera, GITCreature, GITDoor, GITPlaceable, GITStore, GITWaypoint)):
                        continue  # doesn't support rotations.
                    self.initial_rotations[instance] = instance.orientation if isinstance(instance, GITCamera) else instance.bearing
            self.editor.rotate_selected_to_point(world.x, world.y)

    def _handle_camera_rotation(self, screen_delta: Vector2):
        delta_magnitude = abs(screen_delta.x)
        direction = -1 if screen_delta.x < 0 else 1 if screen_delta.x > 0 else 0
        rotate_sens = ModuleDesignerSettings().rotateCameraSensitivity2d / 1000
        rotate_amount = delta_magnitude * rotate_sens * direction
        #RobustLogger.debug(f"on_mouse_scrolled rotate_camera (delta_value={delta_magnitude}, rotateAmount={rotateAmount}, sensSetting={rotateSens}))")
        self.editor.rotate_camera(rotate_amount)

    def handle_undo_redo_from_long_action_finished(self):
        # Check if we were dragging
        if self.is_drag_moving:
            for instance, old_position in self.initial_positions.items():
                new_position = instance.position
                if old_position and new_position != old_position:
                    RobustLogger().debug("GITControlScheme: Create the MoveCommand for undo/redo functionality")
                    move_command = MoveCommand(instance, old_position, new_position)
                    self.undo_stack.push(move_command)
                elif not old_position:
                    RobustLogger().debug("GITControlScheme: No old position %s", instance.resref)
                else:
                    RobustLogger().debug("GITControlScheme: Both old and new positions are the same %s", instance.resref)

            # Reset for the next drag operation
            self.initial_positions.clear()
            #RobustLogger().debug("No longer drag moving GITControlScheme")
            self.is_drag_moving = False

        if self.is_drag_rotating:
            for instance, old_rotation in self.initial_rotations.items():
                new_rotation = instance.orientation if isinstance(instance, GITCamera) else instance.bearing
                if old_rotation and new_rotation != old_rotation:
                    RobustLogger().debug(f"Create the RotateCommand for undo/redo functionality: {instance!r}")
                    self.undo_stack.push(RotateCommand(instance, old_rotation, new_rotation))
                elif not old_rotation:
                    RobustLogger().debug("No old rotation for %s", instance.resref)
                else:
                    RobustLogger().debug("Both old and new rotations are the same for %s", instance.resref)

            # Reset for the next drag operation
            self.initial_rotations.clear()
            #RobustLogger().debug("No longer drag rotating GITControlScheme")
            self.is_drag_rotating = False

    def on_mouse_pressed(self, screen: Vector2, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        if self.duplicate_selected.satisfied(buttons, keys):
            position = self.editor.ui.renderArea.to_world_coords(screen.x, screen.y)
            self.editor.duplicate_selected(position)
        if self.select_underneath.satisfied(buttons, keys):
            self.editor.select_underneath()

    def on_mouse_released(self, screen: Vector2, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        self.handle_undo_redo_from_long_action_finished()

    def on_keyboard_pressed(self, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        if self.delete_selected.satisfied(buttons, keys):
            if isinstance(self.editor._mode, _InstanceMode):  # noqa: SLF001
                selection: list[GITInstance] = self.editor._mode.renderer2d.instance_selection.all()  # noqa: SLF001
                if selection:
                    self.undo_stack.push(DeleteCommand(self.editor._git, selection.copy(), self.editor))  # noqa: SLF001
            self.editor.delete_selected(no_undo_stack=True)

        if self.toggle_instance_lock.satisfied(buttons, keys):
            self.editor.ui.lockInstancesCheck.setChecked(not self.editor.ui.lockInstancesCheck.isChecked())

    def on_keyboard_released(self, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        self.handle_undo_redo_from_long_action_finished()

    # Use @property decorators to allow Users to change their settings without restarting the editor.
    @property
    def pan_camera(self) -> ControlItem:
        return ControlItem(self.settings.moveCameraBind)

    @property
    def rotate_camera(self) -> ControlItem:
        return ControlItem(self.settings.rotateCameraBind)

    @property
    def zoom_camera(self) -> ControlItem:
        return ControlItem(self.settings.zoomCameraBind)

    @property
    def rotate_selected_to_point(self) -> ControlItem:
        return ControlItem(self.settings.rotateSelectedToPointBind)

    @property
    def move_selected(self) -> ControlItem:
        return ControlItem(self.settings.moveSelectedBind)

    @property
    def select_underneath(self) -> ControlItem:
        return ControlItem(self.settings.selectUnderneathBind)

    @property
    def delete_selected(self) -> ControlItem:
        return ControlItem(self.settings.deleteSelectedBind)

    @property
    def duplicate_selected(self) -> ControlItem:
        return ControlItem(self.settings.duplicateSelectedBind)

    @property
    def toggle_instance_lock(self) -> ControlItem:
        return ControlItem(self.settings.toggleLockInstancesBind)
