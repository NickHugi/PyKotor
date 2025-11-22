from __future__ import annotations

import math
import os
import time

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Sequence, cast

import qtpy

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy.QtCore import QPoint, QTimer, Qt
from qtpy.QtGui import QColor, QCursor, QIcon, QPixmap
from qtpy.QtWidgets import (
    QAction,  # pyright: ignore[reportPrivateImportUsage]
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QStatusBar,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pykotor.common.misc import Color, ResRef
from pykotor.common.module import Module, ModuleResource
from pykotor.extract.file import ResourceIdentifier
from pykotor.gl.scene import Camera
from pykotor.resource.formats.bwm import BWM
from pykotor.resource.formats.lyt import LYT, LYTDoorHook, LYTObstacle, LYTRoom, LYTTrack
from pykotor.resource.generics.git import GITCamera, GITCreature, GITDoor, GITEncounter, GITInstance, GITPlaceable, GITSound, GITStore, GITTrigger, GITWaypoint
from pykotor.resource.generics.utd import read_utd
from pykotor.resource.generics.utt import read_utt
from pykotor.resource.generics.utw import read_utw
from pykotor.resource.type import ResourceType
from pykotor.tools import module
from pykotor.tools.misc import is_mod_file
from toolset.data.installation import HTInstallation
from toolset.gui.dialogs.insert_instance import InsertInstanceDialog
from toolset.gui.dialogs.select_module import SelectModuleDialog
from toolset.gui.editor import Editor
from toolset.gui.editors.git import DeleteCommand, MoveCommand, RotateCommand, _GeometryMode, _InstanceMode, _SpawnMode, open_instance_dialog
from toolset.gui.widgets.renderer.lyt_renderer import LYTRenderer
from toolset.gui.widgets.renderer.module import ModuleRenderer
from toolset.gui.widgets.settings.widgets.module_designer import ModuleDesignerSettings
from toolset.gui.windows.designer_controls import ModuleDesignerControls2d, ModuleDesignerControls3d, ModuleDesignerControlsFreeCam
from toolset.gui.windows.help import HelpWindow
from toolset.utils.misc import MODIFIER_KEY_NAMES, get_qt_button_string, get_qt_key_string
from toolset.utils.window import open_resource_editor
from utility.common.geometry import SurfaceMaterial, Vector2, Vector3, Vector4
from utility.error_handling import safe_repr

if TYPE_CHECKING:

    from qtpy.QtGui import QCloseEvent, QFont, QKeyEvent, QShowEvent
    from qtpy.QtWidgets import QCheckBox, _QMenu
    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from pykotor.common.module import UTT, UTW
    from pathlib import Path

    from pykotor.gl.scene import Camera
    from pykotor.resource.formats.bwm import BWM
    from pykotor.resource.formats.lyt import LYT
    from pykotor.resource.generics.are import ARE
    from pykotor.resource.generics.git import GIT
    from pykotor.resource.generics.ifo import IFO
    from toolset.gui.widgets.renderer.walkmesh import WalkmeshRenderer

if qtpy.QT5:
    from qtpy.QtWidgets import QUndoStack
elif qtpy.QT6:
    from qtpy.QtGui import QUndoStack
else:
    raise ValueError(f"Invalid QT_API: '{qtpy.API_NAME}'")


def run_module_designer(
    active_path: str,
    active_name: str,
    active_tsl: bool,  # noqa: FBT001
    module_path: str | None = None,
):
    """An alternative way to start the ModuleDesigner: run thisfunction in a new process so the main tool window doesn't wait on the module designer."""
    import sys

    from toolset.__main__ import main_init

    main_init()
    app = QApplication(sys.argv)
    designer_ui = ModuleDesigner(
        None,
        HTInstallation(active_path, active_name, tsl=active_tsl),
        Path(module_path) if module_path is not None else None,
    )
    # Standardized resource path format
    icon_path = ":/images/icons/sith.png"

    # Debugging: Check if the resource path is accessible
    if not QPixmap(icon_path).isNull():
        designer_ui.log.debug(f"HT main window Icon loaded successfully from {icon_path}")
        designer_ui.setWindowIcon(QIcon(QPixmap(icon_path)))
        cast(QApplication, QApplication.instance()).setWindowIcon(QIcon(QPixmap(icon_path)))
    else:
        print(f"Failed to load HT main window icon from {icon_path}")
    sys.exit(app.exec())


class ModuleDesigner(QMainWindow):
    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation,
        mod_filepath: Path | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Module Designer")

        self._installation: HTInstallation = installation
        self._module: Module | None = None
        self._orig_filepath: Path | None = mod_filepath

        self.initial_positions: dict[GITInstance, Vector3] = {}
        self.initial_rotations: dict[GITCamera | GITCreature | GITDoor | GITPlaceable | GITStore | GITWaypoint, Vector4 | float] = {}
        self.undo_stack: QUndoStack = QUndoStack(self)

        self.selected_instances: list[GITInstance] = []
        self.settings: ModuleDesignerSettings = ModuleDesignerSettings()
        self.log: RobustLogger = RobustLogger()

        self.target_frame_rate = 120  # Target higher for smoother camera
        self.camera_update_timer = QTimer()
        self.camera_update_timer.timeout.connect(self.update_camera)
        self.camera_update_timer.start(int(1000 / self.target_frame_rate))
        self.last_frame_time: float = time.time()
        self.frame_time_samples: list[float] = []  # For adaptive timing

        self.hide_creatures: bool = False
        self.hide_placeables: bool = False
        self.hide_doors: bool = False
        self.hide_triggers: bool = False
        self.hide_encounters: bool = False
        self.hide_waypoints: bool = False
        self.hide_sounds: bool = False
        self.hide_stores: bool = False
        self.hide_cameras: bool = False
        self.lock_instances: bool = False
        # used for the undo/redo events, don't create undo/redo events until the drag finishes.
        self.is_drag_moving: bool = False
        self.is_drag_rotating: bool = False
        self.mouse_pos_history: list[Vector2] = [Vector2(0, 0), Vector2(0, 0)]

        from toolset.uic.qtpy.windows.module_designer import Ui_MainWindow

        self.ui: Ui_MainWindow = Ui_MainWindow()
        self.ui.setupUi(self)
        self._init_ui()
        self._setup_signals()

        self.last_free_cam_time: float = 0.0  # Initialize the last toggle time

        def int_color_to_qcolor(int_value: int) -> QColor:
            color = Color.from_rgba_integer(int_value)
            return QColor(
                int(color.r * 255),
                int(color.g * 255),
                int(color.b * 255),
                int(color.a * 255),
            )

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

        self.ui.flatRenderer.material_colors = self.material_colors
        self.ui.flatRenderer.hide_walkmesh_edges = True
        self.ui.flatRenderer.highlight_boundaries = False

        self._controls3d: ModuleDesignerControls3d | ModuleDesignerControlsFreeCam = ModuleDesignerControls3d(self, self.ui.mainRenderer)
        # self._controls3d: ModuleDesignerControls3d | ModuleDesignerControlsFreeCam = ModuleDesignerControlsFreeCam(self, self.ui.mainRenderer)  # Doesn't work when set in __init__, trigger this in onMousePressed
        self._controls2d: ModuleDesignerControls2d = ModuleDesignerControls2d(self, self.ui.flatRenderer)

        # LYT renderer for layout tab
        self._lyt_renderer: LYTRenderer | None = None

        if mod_filepath is None:  # Use singleShot timer so the ui window opens while the loading is happening.
            QTimer().singleShot(33, self.open_module_with_dialog)
        else:
            QTimer().singleShot(33, lambda: self.open_module(mod_filepath))

    def showEvent(self, a0: QShowEvent):
        if self.ui.mainRenderer._scene is None:  # noqa: SLF001
            return  # Don't show the window if the scene isn't ready, otherwise the gl context stuff will start prematurely.
        super().showEvent(a0)

    def closeEvent(self, event: QCloseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Really quit the module designer? You may lose unsaved changes.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()  # Let the window close
        else:
            event.ignore()  # Ignore the close event

    def _setup_signals(self):
        self.ui.actionOpen.triggered.connect(self.open_module_with_dialog)
        self.ui.actionSave.triggered.connect(self.save_git)
        self.ui.actionInstructions.triggered.connect(self.show_help_window)

        self.ui.actionUndo.triggered.connect(lambda: print("Undo signal") or self.undo_stack.undo())
        self.ui.actionRedo.triggered.connect(lambda: print("Redo signal") or self.undo_stack.redo())

        # Layout tab actions
        self.ui.actionAddRoom.triggered.connect(self.on_add_room)
        self.ui.actionAddDoorHook.triggered.connect(self.on_add_door_hook)
        self.ui.actionAddTrack.triggered.connect(self.on_add_track)
        self.ui.actionAddObstacle.triggered.connect(self.on_add_obstacle)
        self.ui.actionImportTexture.triggered.connect(self.on_import_texture)
        self.ui.actionGenerateWalkmesh.triggered.connect(self.on_generate_walkmesh)

        # Connect LYT editor signals to update UI
        self.ui.mainRenderer.sig_lyt_updated.connect(self.on_lyt_updated)

        self.ui.resourceTree.clicked.connect(self.on_resource_tree_single_clicked)
        self.ui.resourceTree.doubleClicked.connect(self.on_resource_tree_double_clicked)
        self.ui.resourceTree.customContextMenuRequested.connect(self.on_resource_tree_context_menu)

        self.ui.viewCreatureCheck.toggled.connect(self.update_toggles)
        self.ui.viewPlaceableCheck.toggled.connect(self.update_toggles)
        self.ui.viewDoorCheck.toggled.connect(self.update_toggles)
        self.ui.viewSoundCheck.toggled.connect(self.update_toggles)
        self.ui.viewTriggerCheck.toggled.connect(self.update_toggles)
        self.ui.viewEncounterCheck.toggled.connect(self.update_toggles)
        self.ui.viewWaypointCheck.toggled.connect(self.update_toggles)
        self.ui.viewCameraCheck.toggled.connect(self.update_toggles)
        self.ui.viewStoreCheck.toggled.connect(self.update_toggles)
        self.ui.backfaceCheck.toggled.connect(self.update_toggles)
        self.ui.lightmapCheck.toggled.connect(self.update_toggles)
        self.ui.cursorCheck.toggled.connect(self.update_toggles)

        self.ui.viewCreatureCheck.mouseDoubleClickEvent = lambda a0: self.on_instance_visibility_double_click(self.ui.viewCreatureCheck)  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue, reportArgumentType]
        self.ui.viewPlaceableCheck.mouseDoubleClickEvent = lambda a0: self.on_instance_visibility_double_click(self.ui.viewPlaceableCheck)  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue, reportArgumentType]
        self.ui.viewDoorCheck.mouseDoubleClickEvent = lambda a0: self.on_instance_visibility_double_click(self.ui.viewDoorCheck)  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue, reportArgumentType]
        self.ui.viewSoundCheck.mouseDoubleClickEvent = lambda a0: self.on_instance_visibility_double_click(self.ui.viewSoundCheck)  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue, reportArgumentType]
        self.ui.viewTriggerCheck.mouseDoubleClickEvent = lambda a0: self.on_instance_visibility_double_click(self.ui.viewTriggerCheck)  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue, reportArgumentType]
        self.ui.viewEncounterCheck.mouseDoubleClickEvent = lambda a0: self.on_instance_visibility_double_click(self.ui.viewEncounterCheck)  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue, reportArgumentType]
        self.ui.viewWaypointCheck.mouseDoubleClickEvent = lambda a0: self.on_instance_visibility_double_click(self.ui.viewWaypointCheck)  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue, reportArgumentType]
        self.ui.viewCameraCheck.mouseDoubleClickEvent = lambda a0: self.on_instance_visibility_double_click(self.ui.viewCameraCheck)  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue, reportArgumentType]
        self.ui.viewStoreCheck.mouseDoubleClickEvent = lambda a0: self.on_instance_visibility_double_click(self.ui.viewStoreCheck)  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue, reportArgumentType]

        self.ui.instanceList.clicked.connect(self.on_instance_list_single_clicked)
        self.ui.instanceList.doubleClicked.connect(self.on_instance_list_double_clicked)
        self.ui.instanceList.customContextMenuRequested.connect(self.on_instance_list_right_clicked)

        self.ui.mainRenderer.sig_renderer_initialized.connect(self.on_3d_renderer_initialized)
        self.ui.mainRenderer.sig_scene_initialized.connect(self.on_3d_scene_initialized)
        self.ui.mainRenderer.sig_mouse_pressed.connect(self.on_3d_mouse_pressed)
        self.ui.mainRenderer.sig_mouse_released.connect(self.on_3d_mouse_released)
        self.ui.mainRenderer.sig_mouse_moved.connect(self.on_3d_mouse_moved)
        self.ui.mainRenderer.sig_mouse_scrolled.connect(self.on_3d_mouse_scrolled)
        self.ui.mainRenderer.sig_keyboard_pressed.connect(self.on_3d_keyboard_pressed)
        self.ui.mainRenderer.sig_object_selected.connect(self.on_3d_object_selected)
        self.ui.mainRenderer.sig_keyboard_released.connect(self.on_3d_keyboard_released)

        self.ui.flatRenderer.sig_mouse_pressed.connect(self.on_2d_mouse_pressed)
        self.ui.flatRenderer.sig_mouse_moved.connect(self.on_2d_mouse_moved)
        self.ui.flatRenderer.sig_mouse_scrolled.connect(self.on_2d_mouse_scrolled)
        self.ui.flatRenderer.sig_key_pressed.connect(self.on_2d_keyboard_pressed)
        self.ui.flatRenderer.sig_mouse_released.connect(self.on_2d_mouse_released)
        self.ui.flatRenderer.sig_key_released.connect(self.on_2d_keyboard_released)

        # Layout tree signals
        self.ui.lytTree.itemSelectionChanged.connect(self.on_lyt_tree_selection_changed)
        self.ui.lytTree.customContextMenuRequested.connect(self.on_lyt_tree_context_menu)

        # Position/rotation spinbox signals
        self.ui.posXSpin.valueChanged.connect(self.on_room_position_changed)
        self.ui.posYSpin.valueChanged.connect(self.on_room_position_changed)
        self.ui.posZSpin.valueChanged.connect(self.on_room_position_changed)
        self.ui.rotXSpin.valueChanged.connect(self.on_room_rotation_changed)
        self.ui.rotYSpin.valueChanged.connect(self.on_room_rotation_changed)
        self.ui.rotZSpin.valueChanged.connect(self.on_room_rotation_changed)

        # Model edit signals
        self.ui.modelEdit.textChanged.connect(self.on_room_model_changed)
        self.ui.browseModelButton.clicked.connect(self.on_browse_model)

        # Door hook signals
        self.ui.roomNameCombo.currentTextChanged.connect(self.on_doorhook_room_changed)
        self.ui.doorNameEdit.textChanged.connect(self.on_doorhook_name_changed)

    def _init_ui(self):
        self.custom_status_bar = QStatusBar(self)
        self.setStatusBar(self.custom_status_bar)

        self.custom_status_bar_container = QWidget()
        self.custom_status_bar_layout = QVBoxLayout()

        # Create labels for the status bar
        self.mouse_pos_label = QLabel("Mouse Coords: ")
        self.buttons_keys_pressed_label = QLabel("Keys/Buttons: ")
        self.selected_instance_label = QLabel("Selected Instance: ")
        self.view_camera_label = QLabel("View: ")

        first_row = QHBoxLayout()

        first_row.addWidget(self.mouse_pos_label, 1)
        first_row.addStretch(1)
        first_row.addWidget(self.selected_instance_label, 2)
        first_row.addStretch(1)
        first_row.addWidget(self.buttons_keys_pressed_label, 1)

        self.custom_status_bar_layout.addLayout(first_row)
        self.custom_status_bar_layout.addWidget(self.view_camera_label)
        self.custom_status_bar_container.setLayout(self.custom_status_bar_layout)
        self.custom_status_bar.addPermanentWidget(self.custom_status_bar_container)

    def update_status_bar(
        self,
        mouse_pos: QPoint | Vector2,
        buttons: set[Qt.MouseButton],
        keys: set[Qt.Key],
        renderer: WalkmeshRenderer | ModuleRenderer,
    ):
        if isinstance(mouse_pos, QPoint):
            assert not isinstance(mouse_pos, Vector2)
            # QPoint.x() and QPoint.y() are methods that return int
            norm_mouse_pos = Vector2(float(mouse_pos.x()), float(mouse_pos.y()))
        else:
            norm_mouse_pos = mouse_pos
        # Update mouse position
        world_pos: Vector2 | Vector3
        world_pos_3d: Vector3 | None = None
        if isinstance(renderer, ModuleRenderer):
            pos = renderer.scene.cursor.position()
            world_pos_3d = Vector3(pos.x, pos.y, pos.z)
            world_pos = world_pos_3d
            self.mouse_pos_label.setText(f"Mouse Coords: {world_pos_3d.y:.2f}, {world_pos_3d.z:.2f}")

            # Update view camera info
            camera = renderer.scene.camera
            self.view_camera_label.setText(f"View: Pos ({camera.x:.2f}, {camera.y:.2f}, {camera.z:.2f}), " f"Pitch: {camera.pitch:.2f}, Yaw: {camera.yaw:.2f}, " f"FOV: {camera.fov:.2f}")
        else:
            if isinstance(norm_mouse_pos, Vector2):
                norm_mouse_pos = Vector2(float(norm_mouse_pos.x), float(norm_mouse_pos.y))
            else:
                norm_mouse_pos = Vector2(float(norm_mouse_pos.x()), float(norm_mouse_pos.y()))
            world_pos = renderer.to_world_coords(norm_mouse_pos.x, norm_mouse_pos.y)
            self.mouse_pos_label.setText(f"Mouse Coords: {world_pos.y:.2f}")

        # Sort keys and buttons with modifiers at the beginning
        def sort_with_modifiers(
            items: set[Qt.Key] | set[Qt.MouseButton],
            get_string_func: Callable[[Any], str],
            qt_enum_type: Literal["QtKey", "QtMouse"],
        ) -> Sequence[Qt.Key | Qt.MouseButton]:
            modifiers = []
            if qt_enum_type == "QtKey":
                modifiers = [item for item in items if item in MODIFIER_KEY_NAMES]
                normal = [item for item in items if item not in MODIFIER_KEY_NAMES]
            else:
                normal = list(items)
            return sorted(modifiers, key=get_string_func) + sorted(normal, key=get_string_func)

        sorted_buttons = sort_with_modifiers(buttons, get_qt_button_string, "QtMouse")
        sorted_keys = sort_with_modifiers(keys, get_qt_key_string, "QtKey")

        # Update keys/mouse buttons
        buttons_str = "+".join([get_qt_button_string(button) for button in sorted_buttons])
        keys_str = "+".join([get_qt_key_string(key) for key in sorted_keys])
        self.buttons_keys_pressed_label.setText(f"Keys/Buttons: {keys_str} {buttons_str}")

        # Update selected instance
        if self.selected_instances:
            instance = self.selected_instances[0]
            instance_name = repr(instance) if isinstance(instance, GITCamera) else instance.identifier()
            self.selected_instance_label.setText(f"Selected Instance: {instance_name}")
        else:
            self.selected_instance_label.setText("Selected Instance: None")

    def _refresh_window_title(self):
        if self._module is None:
            title = f"No Module - {self._installation.name} - Module Designer"
        else:
            title = f"{self._module.root()} - {self._installation.name} - Module Designer"
        self.setWindowTitle(title)

    def on_lyt_updated(self, lyt: LYT):
        """Handle LYT updates from the editor."""
        if self._module is not None:
            layout = self._module.layout()
            if layout is not None:
                layout.save()
            self.rebuild_resource_tree()

    def open_module_with_dialog(self):
        dialog = SelectModuleDialog(self, self._installation)

        if dialog.exec():
            mod_filepath = self._installation.module_path().joinpath(dialog.module)
            self.open_module(mod_filepath)

    #    @with_variable_trace(Exception)
    def open_module(
        self,
        mod_filepath: Path,
    ):
        """Opens a module."""
        mod_root: str = self._installation.get_module_root(mod_filepath)
        mod_filepath = self._ensure_mod_file(mod_filepath, mod_root)

        self.unload_module()
        combined_module = Module(mod_root, self._installation, use_dot_mod=is_mod_file(mod_filepath))
        git_module = combined_module.git()
        if git_module is None:
            raise ValueError(f"This module '{mod_root}' is missing a GIT!")
        git: GIT | None = git_module.resource()
        if git is None:
            raise ValueError(f"This module '{mod_root}' is missing a GIT!")

        walkmeshes: list[BWM] = []
        for mod_resource in combined_module.resources.values():
            res_obj = mod_resource.resource()
            if res_obj is not None and mod_resource.restype() == ResourceType.WOK:
                walkmeshes.append(res_obj)
        result: tuple[Module, GIT, list[BWM]] = (combined_module, git, walkmeshes)
        new_module, git, walkmeshes = result
        self._module = new_module
        self.ui.flatRenderer.set_git(git)
        self.ui.mainRenderer.initialize_renderer(self._installation, new_module)
        self.ui.mainRenderer.scene.show_cursor = self.ui.cursorCheck.isChecked()
        self.ui.flatRenderer.set_walkmeshes(walkmeshes)
        self.ui.flatRenderer.center_camera()
        self.show()
        # Inherently calls On3dSceneInitialized when done.

    def _ensure_mod_file(self, mod_filepath: Path, mod_root: str) -> Path:
        mod_file = mod_filepath.with_name(f"{mod_root}.mod")
        if not mod_file.is_file():
            if self._confirm_create_mod(mod_root):
                self._create_mod(mod_file, mod_root)
                return mod_file
            return mod_filepath

        if mod_file != mod_filepath and not self._confirm_use_mod(mod_filepath, mod_file):
            return mod_filepath
        return mod_file

    def _confirm_create_mod(self, mod_root: str) -> bool:
        return (
            QMessageBox.question(
                self,
                "Editing .RIM/.ERF modules is discouraged.",
                f"The Module Designer would like to create a .mod for module '{mod_root}', would you like to do this now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            == QMessageBox.StandardButton.Yes
        )

    def _create_mod(self, mod_file: Path, mod_root: str):
        self.log.info("Creating '%s.mod' from the rims/erfs...", mod_root)
        module.rim_to_mod(mod_file, game=self._installation.game())
        self._installation.reload_module(mod_file.name)

    def _confirm_use_mod(self, orig_filepath: Path, mod_filepath: Path) -> bool:
        return (
            QMessageBox.question(
                self,
                f"{orig_filepath.suffix} file chosen when {mod_filepath.suffix} preferred.",
                (f"You've chosen '{orig_filepath.name}' with a '{orig_filepath.suffix}' extension.<br><br>" f"The Module Designer recommends modifying .mod's.<br><br>" f"Use '{mod_filepath.name}' instead?"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            == QMessageBox.StandardButton.Yes
        )

    def unload_module(self):
        self._module = None
        self.ui.mainRenderer.shutdown_renderer()

    def show_help_window(self):
        window = HelpWindow(self, "./help/tools/1-moduleEditor.md")
        window.show()

    def git(self) -> GIT:
        assert self._module is not None
        git = self._module.git()
        assert git is not None
        git_resource = git.resource()
        assert git_resource is not None
        return git_resource

    def are(self) -> ARE:
        assert self._module is not None
        are = self._module.are()
        assert are is not None
        are_resource = are.resource()
        assert are_resource is not None
        return are_resource

    def ifo(self) -> IFO:
        assert self._module is not None
        ifo = self._module.info()
        assert ifo is not None
        ifo_resource = ifo.resource()
        assert ifo_resource is not None
        return ifo_resource

    def save_git(self):
        assert self._module is not None
        git_module = self._module.git()
        assert git_module is not None
        git_module.save()
        
        # Also save the layout if it has been modified
        layout_module = self._module.layout()
        if layout_module is not None:
            layout_module.save()

    def rebuild_resource_tree(self):
        """Rebuilds the resource tree widget.

        Rebuilds the resource tree widget by:
            - Clearing existing items
            - Enabling the tree
            - Grouping resources by type into categories
            - Adding category items and resource items
            - Sorting items alphabetically.
        """
        # Only build if module is loaded
        if self._module is None:
            self.ui.resourceTree.setEnabled(False)
            return

        # Block signals and sorting during bulk update for better performance
        self.ui.resourceTree.blockSignals(True)
        self.ui.resourceTree.setSortingEnabled(False)
        self.ui.resourceTree.clear()
        self.ui.resourceTree.setEnabled(True)

        categories: dict[ResourceType, QTreeWidgetItem] = {
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
            ResourceType.INVALID: QTreeWidgetItem(["Other"]),
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

        for value in categories.values():
            self.ui.resourceTree.addTopLevelItem(value)

        for resource in self._module.resources.values():
            item = QTreeWidgetItem([f"{resource.resname()}.{resource.restype().extension}"])
            item.setData(0, Qt.ItemDataRole.UserRole, resource)
            category: QTreeWidgetItem = categories.get(resource.restype(), categories[ResourceType.INVALID])
            category.addChild(item)

        self.ui.resourceTree.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.ui.resourceTree.setSortingEnabled(True)

        # Restore signals after bulk update
        self.ui.resourceTree.blockSignals(False)

    def open_module_resource(self, resource: ModuleResource):
        active_path = resource.active()
        if active_path is None:
            QMessageBox(
                QMessageBox.Icon.Critical,
                "Failed to open editor",
                f"Resource {resource.identifier()} has no active file path.",
            ).exec()
            return
        editor: Editor | QMainWindow | None = open_resource_editor(
            active_path,
            installation=self._installation,
            parent_window=self,
            resname=resource.resname(),
            restype=resource.restype(),
            data=resource.data(),
        )[1]

        if editor is None:
            QMessageBox(
                QMessageBox.Icon.Critical,
                "Failed to open editor",
                f"Failed to open editor for file: {resource.identifier()}",
            ).exec()
        elif isinstance(editor, Editor):
            editor.sig_saved_file.connect(lambda: self._on_saved_resource(resource))

    def copy_resource_to_override(self, resource: ModuleResource):
        location = self._installation.override_path() / f"{resource.identifier()}"
        data = resource.data()
        if data is None:
            RobustLogger().error(f"Cannot find resource {resource.identifier()} anywhere to copy to Override. Locations: {resource.locations()}")
            return
        location.write_bytes(data)
        resource.add_locations([location])
        resource.activate(location)
        self.ui.mainRenderer.scene.clear_cache_buffer.append(resource.identifier())

    def activate_resource_file(
        self,
        resource: ModuleResource,
        location: os.PathLike | str,
    ):
        resource.activate(location)
        self.ui.mainRenderer.scene.clear_cache_buffer.append(resource.identifier())

    def select_resource_item(
        self,
        instance: GITInstance,
        *,
        clear_existing: bool = True,
    ):
        if clear_existing:
            self.ui.resourceTree.clearSelection()
        this_ident = instance.identifier()
        if this_ident is None:  # Should only ever be None for GITCamera.
            assert isinstance(instance, GITCamera), f"Should only ever be None for GITCamera, not {type(instance).__name__}."
            return

        for i in range(self.ui.resourceTree.topLevelItemCount()):
            parent: QTreeWidgetItem | None = self.ui.resourceTree.topLevelItem(i)
            if parent is None:
                self.log.warning("parent was None in ModuleDesigner.selectResourceItem()")
                continue
            for j in range(parent.childCount()):
                item = parent.child(j)
                if item is None:
                    self.log.warning(f"parent.child({j}) was somehow None in selectResourceItem")
                    continue
                res: ModuleResource = item.data(0, Qt.ItemDataRole.UserRole)
                if not isinstance(res, ModuleResource):
                    self.log.warning("item.data(0, Qt.ItemDataRole.UserRole) returned non ModuleResource in ModuleDesigner.selectResourceItem(): %s", safe_repr(res))
                    continue
                if res.identifier() != this_ident:
                    continue
                self.log.debug("Selecting ModuleResource in selectResourceItem loop: %s", res.identifier())
                parent.setExpanded(True)
                item.setSelected(True)
                self.ui.resourceTree.scrollToItem(item)

    def rebuild_instance_list(self):
        self.log.debug("rebuildInstanceList called.")

        # Only build if module is loaded
        if self._module is None:
            self.ui.instanceList.setEnabled(False)
            self.ui.instanceList.setVisible(False)
            return

        # Block signals during bulk update for better performance
        self.ui.instanceList.blockSignals(True)
        self.ui.instanceList.clear()
        self.ui.instanceList.setEnabled(True)
        self.ui.instanceList.setVisible(True)

        visible_mapping = {
            GITCreature: self.hide_creatures,
            GITPlaceable: self.hide_placeables,
            GITDoor: self.hide_doors,
            GITTrigger: self.hide_triggers,
            GITEncounter: self.hide_encounters,
            GITWaypoint: self.hide_waypoints,
            GITSound: self.hide_sounds,
            GITStore: self.hide_stores,
            GITCamera: self.hide_cameras,
            GITInstance: False,
        }
        icon_mapping = {
            GITCreature: QPixmap(":/images/icons/k1/creature.png"),
            GITPlaceable: QPixmap(":/images/icons/k1/placeable.png"),
            GITDoor: QPixmap(":/images/icons/k1/door.png"),
            GITSound: QPixmap(":/images/icons/k1/sound.png"),
            GITTrigger: QPixmap(":/images/icons/k1/trigger.png"),
            GITEncounter: QPixmap(":/images/icons/k1/encounter.png"),
            GITWaypoint: QPixmap(":/images/icons/k1/waypoint.png"),
            GITCamera: QPixmap(":/images/icons/k1/camera.png"),
            GITStore: QPixmap(":/images/icons/k1/merchant.png"),
            GITInstance: QPixmap(32, 32),
        }

        self.ui.instanceList.clear()
        items: list[QListWidgetItem] = []

        if self._module is None:
            return
        git_module = self._module.git()
        if git_module is None:
            return
        git_resource = git_module.resource()
        if git_resource is None:
            return
        git: GIT = git_resource

        for instance in git.instances():
            if visible_mapping[instance.__class__]:
                continue

            struct_index: int = git.index(instance)

            icon = QIcon(icon_mapping[instance.__class__])
            item = QListWidgetItem(icon, "")
            font: QFont = item.font()

            if isinstance(instance, GITCamera):
                item.setText(f"Camera #{instance.camera_id}")
                item.setToolTip(f"Struct Index: {struct_index}\nCamera ID: {instance.camera_id}\nFOV: {instance.fov}")
                item.setData(Qt.ItemDataRole.UserRole + 1, "cam" + str(instance.camera_id).rjust(10, "0"))
            else:
                this_ident = instance.identifier()
                assert this_ident is not None
                resname: str = this_ident.resname
                name: str = resname
                tag: str = ""
                module_resource: ModuleResource[ARE] | None = self._module.resource(this_ident.resname, this_ident.restype)
                if module_resource is None:
                    continue
                abstracted_resource = module_resource.resource()
                if abstracted_resource is None:
                    continue

                if isinstance(instance, GITDoor) or (isinstance(instance, GITTrigger) and module_resource):
                    # Tag is stored in the GIT
                    name = module_resource.localized_name() or resname
                    tag = instance.tag
                elif isinstance(instance, GITWaypoint):
                    # Name and tag are stored in the GIT
                    name = self._installation.string(instance.name)
                    tag = instance.tag
                elif module_resource:
                    name = module_resource.localized_name() or resname
                    tag = abstracted_resource.tag

                if module_resource is None:
                    font.setItalic(True)

                item.setText(name)
                item.setToolTip(f"Struct Index: {struct_index}\nResRef: {resname}\nName: {name}\nTag: {tag}")
                ident = instance.identifier()
                assert ident is not None
                item.setData(Qt.ItemDataRole.UserRole + 1, ident.restype.extension + name)

            item.setFont(font)
            item.setData(Qt.ItemDataRole.UserRole, instance)
            items.append(item)

        for item in sorted(items, key=lambda i: i.data(Qt.ItemDataRole.UserRole + 1)):
            self.ui.instanceList.addItem(item)

        # Restore signals after bulk update
        self.ui.instanceList.blockSignals(False)

    def select_instance_item_on_list(self, instance: GITInstance):
        self.ui.instanceList.clearSelection()
        for i in range(self.ui.instanceList.count()):
            item: QListWidgetItem | None = self.ui.instanceList.item(i)
            if item is None:
                self.log.warning("item was somehow None at index %s in selectInstanceItemOnList", i)
                continue
            data: GITInstance = item.data(Qt.ItemDataRole.UserRole)
            if data is instance:
                item.setSelected(True)
                self.ui.instanceList.scrollToItem(item)

    def update_toggles(self):
        scene = self.ui.mainRenderer.scene
        assert scene is not None

        self.hide_creatures = scene.hide_creatures = self.ui.flatRenderer.hide_creatures = not self.ui.viewCreatureCheck.isChecked()
        self.hide_placeables = scene.hide_placeables = self.ui.flatRenderer.hide_placeables = not self.ui.viewPlaceableCheck.isChecked()
        self.hide_doors = scene.hide_doors = self.ui.flatRenderer.hide_doors = not self.ui.viewDoorCheck.isChecked()
        self.hide_triggers = scene.hide_triggers = self.ui.flatRenderer.hide_triggers = not self.ui.viewTriggerCheck.isChecked()
        self.hide_encounters = scene.hide_encounters = self.ui.flatRenderer.hide_encounters = not self.ui.viewEncounterCheck.isChecked()
        self.hide_waypoints = scene.hide_waypoints = self.ui.flatRenderer.hide_waypoints = not self.ui.viewWaypointCheck.isChecked()
        self.hide_sounds = scene.hide_sounds = self.ui.flatRenderer.hide_sounds = not self.ui.viewSoundCheck.isChecked()
        self.hide_stores = scene.hide_stores = self.ui.flatRenderer.hide_stores = not self.ui.viewStoreCheck.isChecked()
        self.hide_cameras = scene.hide_cameras = self.ui.flatRenderer.hide_cameras = not self.ui.viewCameraCheck.isChecked()

        scene.backface_culling = self.ui.backfaceCheck.isChecked()
        scene.use_lightmap = self.ui.lightmapCheck.isChecked()
        scene.show_cursor = self.ui.cursorCheck.isChecked()

        self.rebuild_instance_list()

    #    @with_variable_trace(Exception)
    def add_instance(
        self,
        instance: GITInstance,
        *,
        walkmesh_snap: bool = True,
    ):
        """Adds a GIT instance to the editor.

        Args:
        ----
            instance: {The instance to add}
            walkmesh_snap (optional): {Whether to snap the instance to the walkmesh}.
        """
        if walkmesh_snap:
            instance.position.z = self.ui.mainRenderer.walkmesh_point(
                instance.position.x,
                instance.position.y,
                self.ui.mainRenderer.scene.camera.z,
            ).z

        if not isinstance(instance, GITCamera):
            assert self._module is not None
            ident = instance.identifier()
            assert ident is not None
            dialog = InsertInstanceDialog(self, self._installation, self._module, ident.restype)

            if dialog.exec():
                self.rebuild_resource_tree()
                instance.resref = ResRef(dialog.resname)  # pyright: ignore[reportAttributeAccessIssue]
                assert self._module is not None
                git = self._module.git()
                assert git is not None
                git_resource = git.resource()
                assert git_resource is not None
                git_resource.add(instance)

                if isinstance(instance, GITWaypoint):
                    utw: UTW = read_utw(dialog.data)
                    instance.tag = utw.tag
                    instance.name = utw.name
                elif isinstance(instance, GITTrigger):
                    utt: UTT = read_utt(dialog.data)
                    instance.tag = utt.tag
                    if not instance.geometry:
                        RobustLogger().info("Creating default triangle trigger geometry for %s.%s...", instance.resref, "utt")
                        instance.geometry.create_triangle(origin=instance.position)
                elif isinstance(instance, GITEncounter):
                    if not instance.geometry:
                        RobustLogger().info("Creating default triangle trigger geometry for %s.%s...", instance.resref, "ute")
                        instance.geometry.create_triangle(origin=instance.position)
                elif isinstance(instance, GITDoor):
                    utd: module.UTD = read_utd(dialog.data)
                    instance.tag = utd.tag
        else:
            assert self._module is not None
            git_module = self._module.git()
            assert git_module is not None
            git_resource = git_module.resource()
            assert git_resource is not None
            git_resource.add(instance)
        self.ui.mainRenderer.scene.invalidate_cache()
        self.rebuild_instance_list()

    #    @with_variable_trace()
    def add_instance_at_cursor(
        self,
        instance: GITInstance,
    ):
        scene = self.ui.mainRenderer.scene
        assert scene is not None

        instance.position.x = scene.cursor.position().x
        instance.position.y = scene.cursor.position().y
        instance.position.z = scene.cursor.position().z

        if not isinstance(instance, GITCamera):
            assert self._module is not None
            ident = instance.identifier()
            assert ident is not None
            dialog = InsertInstanceDialog(self, self._installation, self._module, ident.restype)

            if dialog.exec():
                self.rebuild_resource_tree()
                instance.resref = ResRef(dialog.resname)  # pyright: ignore[reportAttributeAccessIssue]
                assert self._module is not None
                git = self._module.git()
                assert git is not None
                git_resource = git.resource()
                assert git_resource is not None
                git_resource.add(instance)
        else:
            assert self._module is not None
            if isinstance(instance, (GITEncounter, GITTrigger)) and not instance.geometry:
                self.log.info("Creating default triangle geometry for %s.%s", instance.resref, "utt" if isinstance(instance, GITTrigger) else "ute")
                instance.geometry.create_triangle(origin=instance.position)
            git_module = self._module.git()
            assert git_module is not None
            git_resource = git_module.resource()
            assert git_resource is not None
            git_resource.add(instance)
        self.rebuild_instance_list()

    #    @with_variable_trace()
    def edit_instance(
        self,
        instance: GITInstance | None = None,
    ):
        if instance is None:
            if not self.selected_instances:
                return
            instance = self.selected_instances[0]
        if open_instance_dialog(self, instance, self._installation):
            if not isinstance(instance, GITCamera):
                ident = instance.identifier()
                if ident is not None:
                    self.ui.mainRenderer.scene.clear_cache_buffer.append(ident)
            self.rebuild_instance_list()

    def snap_camera_to_view(
        self,
        git_camera_instance: GITCamera,
    ):
        view_camera: Camera = self._get_scene_camera()
        true_pos = view_camera.true_position()
        # Convert vec3 to Vector3
        git_camera_instance.position = Vector3(float(true_pos.x), float(true_pos.y), float(true_pos.z))

        self.undo_stack.push(MoveCommand(git_camera_instance, git_camera_instance.position, git_camera_instance.position))

        self.log.debug("Create RotateCommand for undo/redo functionality")
        pitch = math.pi - (view_camera.pitch + (math.pi / 2))
        yaw = math.pi / 2 - view_camera.yaw
        new_orientation = Vector4.from_euler(yaw, 0, pitch)
        self.undo_stack.push(RotateCommand(git_camera_instance, git_camera_instance.orientation, new_orientation))
        git_camera_instance.orientation = new_orientation

    def snap_view_to_git_camera(
        self,
        git_camera_instance: GITCamera,
    ):
        view_camera: Camera = self._get_scene_camera()
        euler: Vector3 = git_camera_instance.orientation.to_euler()
        view_camera.pitch = math.pi - euler.z - math.radians(git_camera_instance.pitch)
        view_camera.yaw = math.pi / 2 - euler.x
        view_camera.x = git_camera_instance.position.x
        view_camera.y = git_camera_instance.position.y
        view_camera.z = git_camera_instance.position.z + git_camera_instance.height
        view_camera.distance = 0

    def snap_view_to_git_instance(
        self,
        git_instance: GITInstance,
    ):
        camera: Camera = self._get_scene_camera()
        yaw: float | None = git_instance.yaw()
        camera.yaw = camera.yaw if yaw is None else yaw
        camera.x, camera.y, camera.z = git_instance.position
        camera.y = git_instance.position.y
        camera.z = git_instance.position.z + 2
        camera.distance = 0

    def _get_scene_camera(self) -> Camera:
        scene = self.ui.mainRenderer.scene
        assert scene is not None
        result: Camera = scene.camera
        return result

    def snap_camera_to_entry_location(self):
        scene = self.ui.mainRenderer.scene
        assert scene is not None

        scene.camera.x = self.ifo().entry_position.x
        scene.camera.y = self.ifo().entry_position.y
        scene.camera.z = self.ifo().entry_position.z

    def toggle_free_cam(self):
        if isinstance(self._controls3d, ModuleDesignerControls3d):
            self.log.info("Enabling ModuleDesigner free cam")
            self._controls3d = ModuleDesignerControlsFreeCam(self, self.ui.mainRenderer)
        else:
            self.log.info("Disabling ModuleDesigner free cam")
            self._controls3d = ModuleDesignerControls3d(self, self.ui.mainRenderer)

    # region Selection Manipulations
    def set_selection(self, instances: list[GITInstance]):
        if instances:
            self.ui.mainRenderer.scene.select(instances[0])
            self.ui.flatRenderer.instance_selection.select(instances)
            self.select_instance_item_on_list(instances[0])
            self.select_resource_item(instances[0])
            self.selected_instances = instances
        else:
            self.ui.mainRenderer.scene.selection.clear()
            self.ui.flatRenderer.instance_selection.clear()
            self.selected_instances.clear()

    def delete_selected(
        self,
        *,
        no_undo_stack: bool = False,
    ):
        assert self._module is not None
        if not no_undo_stack:
            self.undo_stack.push(DeleteCommand(self.git(), self.selected_instances.copy(), self))  # noqa: SLF001
        git_module = self._module.git()
        assert git_module is not None
        git_resource = git_module.resource()
        if git_resource is not None:
            for instance in self.selected_instances:
                git_resource.remove(instance)
        self.selected_instances.clear()
        self.ui.mainRenderer.scene.selection.clear()
        self.ui.mainRenderer.scene.invalidate_cache()
        self.ui.flatRenderer.instance_selection.clear()
        self.rebuild_instance_list()

    def move_selected(  # noqa: PLR0913
        self,
        x: float,
        y: float,
        z: float | None = None,
        *,
        no_undo_stack: bool = False,
        no_z_coord: bool = False,
    ):
        if self.ui.lockInstancesCheck.isChecked():
            return

        for instance in self.selected_instances:
            self.log.debug("Moving %s", instance.resref)
            new_x = instance.position.x + x
            new_y = instance.position.y + y
            if no_z_coord:
                new_z = instance.position.z
            else:
                new_z = instance.position.z + (z or self.ui.mainRenderer.walkmesh_point(instance.position.x, instance.position.y).z)
            old_position = instance.position
            new_position = Vector3(new_x, new_y, new_z)
            if not no_undo_stack:
                self.undo_stack.push(MoveCommand(instance, old_position, new_position))
            instance.position = new_position

    def rotate_selected(self, x: float, y: float):
        if self.ui.lockInstancesCheck.isChecked():
            return

        for instance in self.selected_instances:
            new_yaw = x / 60
            new_pitch = (y or 1) / 60
            new_roll = 0.0
            if not isinstance(instance, (GITCamera, GITCreature, GITDoor, GITPlaceable, GITStore, GITWaypoint)):
                continue  # doesn't support rotations.
            instance.rotate(new_yaw, new_pitch, new_roll)

    # endregion

    # region Signal Callbacks
    def _on_saved_resource(
        self,
        resource: ModuleResource,
    ):
        resource.reload()
        self.ui.mainRenderer.scene.clear_cache_buffer.append(ResourceIdentifier(resource.resname(), resource.restype()))

    def handle_undo_redo_from_long_action_finished(self):
        if self.is_drag_moving:
            for instance, old_position in self.initial_positions.items():
                new_position = instance.position
                if old_position and new_position != old_position:
                    self.log.debug("Create the MoveCommand for undo/redo functionality")
                    move_command = MoveCommand(instance, old_position, new_position)
                    self.undo_stack.push(move_command)
                elif not old_position:
                    self.log.debug("No old position for %s", instance.resref)
                else:
                    self.log.debug("Both old and new positions are the same %s", instance.resref)

            # Reset for the next drag operation
            self.initial_positions.clear()
            self.log.debug("No longer drag moving")
            self.is_drag_moving = False

        if self.is_drag_rotating:
            for instance, old_rotation in self.initial_rotations.items():
                new_rotation = instance.orientation if isinstance(instance, GITCamera) else instance.bearing
                if old_rotation and new_rotation != old_rotation:
                    self.log.debug("Create the RotateCommand for undo/redo functionality")
                    self.undo_stack.push(RotateCommand(instance, old_rotation, new_rotation))
                elif not old_rotation:
                    self.log.debug("No old rotation for %s", instance.resref)
                else:
                    self.log.debug("Both old and new rotations are the same for %s", instance.resref)
            self.initial_rotations.clear()
            self.log.debug("No longer drag rotating")
            self.is_drag_rotating = False

    def on_instance_list_single_clicked(self):
        if self.ui.instanceList.selectedItems():
            instance = self.get_git_instance_from_highlighted_list_item()
            self.set_selection([instance])

    def on_instance_list_double_clicked(self):
        if self.ui.instanceList.selectedItems():
            instance = self.get_git_instance_from_highlighted_list_item()
            self.set_selection([instance])
            self.ui.mainRenderer.snap_camera_to_point(instance.position)
            self.ui.flatRenderer.snap_camera_to_point(instance.position)

    def get_git_instance_from_highlighted_list_item(self) -> GITInstance:
        item: QListWidgetItem = self.ui.instanceList.selectedItems()[0]
        result: GITInstance = item.data(Qt.ItemDataRole.UserRole)
        return result

    def on_instance_visibility_double_click(self, checkbox: QCheckBox):
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

    def enter_instance_mode(self):
        instance_mode = _InstanceMode.__new__(_InstanceMode)
        # HACK:
        instance_mode.delete_selected = self.delete_selected # type: ignore[method-assign]
        instance_mode.edit_selected_instance = self.edit_instance  # type: ignore[method-assign]
        instance_mode.build_list = self.rebuild_instance_list  # type: ignore[method-assign]
        instance_mode.update_visibility = self.update_toggles  # type: ignore[method-assign]
        instance_mode.select_underneath = lambda: self.set_selection(self.ui.flatRenderer.instances_under_mouse())  # type: ignore[method-assign]
        instance_mode.__init__(self, self._installation, self.git())
        # self._controls2d._mode.rotateSelectedToPoint = self.rotateSelected
        self._controls2d._mode = instance_mode  # noqa: SLF001

    def enter_geometry_mode(self):
        self._controls2d._mode = _GeometryMode(self, self._installation, self.git(), hide_others=False)  # noqa: SLF001

    def enter_spawn_mode(self):
        # TODO(NickHugi): _SpawnMode is incomplete - needs to implement all abstract methods from _Mode
        # Temporarily disabled until _SpawnMode is fully implemented
        # self._controls2d._mode = _SpawnMode(self, self._installation, self.git())
        self.log.warning("Spawn mode is not yet implemented")

    def on_resource_tree_context_menu(self, point: QPoint):
        menu = QMenu(self)
        cur_item = self.ui.resourceTree.currentItem()
        if cur_item is None:
            return
        data = cur_item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(data, ModuleResource):
            self._active_instance_location_menu(data, menu)
        menu.exec(self.ui.resourceTree.mapToGlobal(point))

    def on_resource_tree_double_clicked(self, point: QPoint):
        cur_item = self.ui.resourceTree.currentItem()
        assert cur_item is not None
        data = cur_item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(data, ModuleResource):
            self.open_module_resource(data)

    def on_resource_tree_single_clicked(self, point: QPoint):
        cur_item = self.ui.resourceTree.currentItem()
        assert cur_item is not None
        data = cur_item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(data, ModuleResource):
            self.jump_to_instance_list_action(data=data)

    def jump_to_instance_list_action(self, *args, data: ModuleResource, **kwargs):
        this_ident = data.identifier()
        instances = self.git().instances()
        for instance in instances:
            if instance.identifier() == this_ident:
                self.select_instance_item_on_list(instance)
                return

    def _active_instance_location_menu(self, data: ModuleResource, menu: _QMenu):
        """Builds an active override menu for a module resource.

        Args:
        ----
            data: ModuleResource - The module resource data
            menu: QMenu - The menu to build actions on
        """
        copy_to_override_action = QAction("Copy To Override", self)
        copy_to_override_action.triggered.connect(lambda _=None, r=data: self.copy_resource_to_override(r))

        menu.addAction("Edit Active File").triggered.connect(lambda _=None, r=data: self.open_module_resource(r))
        menu.addAction("Reload Active File").triggered.connect(lambda _=None: data.reload())
        menu.addAction(copy_to_override_action)
        menu.addSeparator()
        for location in data.locations():
            location_action = QAction(str(location), self)
            location_action.triggered.connect(lambda _=None, loc=location: self.activate_resource_file(data, loc))
            if location == data.active():
                location_action.setEnabled(False)
            if os.path.commonpath([str(location.absolute()), str(self._installation.override_path())]) == str(self._installation.override_path()):
                copy_to_override_action.setEnabled(False)
            menu.addAction(location_action)

        def jump_to_instance_list_action(*args, data=data, **kwargs):
            this_ident = data.identifier()
            instances = self.git().instances()
            for instance in instances:
                if instance.identifier() == this_ident:
                    # self.selectInstanceItemOnList(instance)
                    self.set_selection([instance])
                    return

        menu.addAction("Find in Instance List").triggered.connect(jump_to_instance_list_action)

    def on_3d_mouse_moved(self, screen: Vector2, screen_delta: Vector2, world: Vector3, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        self.update_status_bar(screen, buttons, keys, self.ui.mainRenderer)
        self._controls3d.on_mouse_moved(screen, screen_delta, world, buttons, keys)

    def on_3d_mouse_scrolled(self, delta: Vector2, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        self.update_status_bar(QCursor.pos(), buttons, keys, self.ui.mainRenderer)
        self._controls3d.on_mouse_scrolled(delta, buttons, keys)

    def on_3d_mouse_pressed(self, screen: Vector2, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        self.update_status_bar(screen, buttons, keys, self.ui.mainRenderer)
        self._controls3d.on_mouse_pressed(screen, buttons, keys)

    def do_cursor_lock(
        self,
        mut_scr: Vector2,
        *,
        center_mouse: bool = True,
        do_rotations: bool = True,
    ):
        new_pos: QPoint = QCursor.pos()
        renderer: ModuleRenderer = self.ui.mainRenderer
        if center_mouse:
            old_pos = renderer.mapToGlobal(renderer.rect().center())
            QCursor.setPos(old_pos.x(), old_pos.y())
        else:
            old_pos = renderer.mapToGlobal(QPoint(int(renderer._mouse_prev.x), int(renderer._mouse_prev.y)))
            QCursor.setPos(old_pos)
            local_old_pos: QPoint = renderer.mapFromGlobal(QPoint(old_pos.x(), old_pos.y()))
            mut_scr.x, mut_scr.y = local_old_pos.x(), local_old_pos.y()

        if do_rotations:
            yaw_delta = old_pos.x() - new_pos.x()
            pitch_delta = old_pos.y() - new_pos.y()
            if isinstance(self._controls3d, ModuleDesignerControlsFreeCam):
                strength = self.settings.rotateCameraSensitivityFC / 10000
                clamp = False
            else:
                strength = self.settings.rotateCameraSensitivity3d / 10000
                clamp = True
            renderer.rotate_camera(yaw_delta * strength, -pitch_delta * strength, clamp_rotations=clamp)

    def on_3d_mouse_released(self, screen: Vector2, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        self.update_status_bar(screen, buttons, keys, self.ui.mainRenderer)
        self._controls3d.on_mouse_released(screen, buttons, keys)

    def on_3d_keyboard_released(self, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        self.update_status_bar(QCursor.pos(), buttons, keys, self.ui.mainRenderer)
        self._controls3d.on_keyboard_released(buttons, keys)

    def on_3d_keyboard_pressed(self, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        self.update_status_bar(QCursor.pos(), buttons, keys, self.ui.mainRenderer)
        self._controls3d.on_keyboard_pressed(buttons, keys)

    def on_3d_object_selected(self, instance: GITInstance):
        if instance is not None:
            self.set_selection([instance])
        else:
            self.set_selection([])

    def on_context_menu(self, world: Vector3, point: QPoint, *, is_flat_renderer_call: bool | None = None):
        self.log.debug(f"onContextMenu(world={world}, point={point}, isFlatRendererCall={is_flat_renderer_call})")
        if self._module is None:
            self.log.warning("onContextMenu No module.")
            return

        if len(self.ui.mainRenderer.scene.selection) == 0:
            self.log.debug("onContextMenu No selection")
            menu = self.build_insert_instance_menu(world)
        else:
            menu = self.on_context_menu_selection_exists(world, is_flat_renderer_call=is_flat_renderer_call, get_menu=True)

        if menu is None:
            return
        self.show_final_context_menu(menu)

    def build_insert_instance_menu(self, world: Vector3):
        menu = QMenu(self)

        rot = self.ui.mainRenderer.scene.camera
        menu.addAction("Insert Camera").triggered.connect(lambda: self.add_instance(GITCamera(*world), walkmesh_snap=False))  # pyright: ignore[reportArgumentType]
        menu.addAction("Insert Camera at View").triggered.connect(lambda: self.add_instance(GITCamera(rot.x, rot.y, rot.z, rot.yaw, rot.pitch, 0, 0), walkmesh_snap=False))
        menu.addSeparator()
        menu.addAction("Insert Creature").triggered.connect(lambda: self.add_instance(GITCreature(*world), walkmesh_snap=True))
        menu.addAction("Insert Door").triggered.connect(lambda: self.add_instance(GITDoor(*world), walkmesh_snap=False))
        menu.addAction("Insert Placeable").triggered.connect(lambda: self.add_instance(GITPlaceable(*world), walkmesh_snap=False))
        menu.addAction("Insert Store").triggered.connect(lambda: self.add_instance(GITStore(*world), walkmesh_snap=False))
        menu.addAction("Insert Sound").triggered.connect(lambda: self.add_instance(GITSound(*world), walkmesh_snap=False))
        menu.addAction("Insert Waypoint").triggered.connect(lambda: self.add_instance(GITWaypoint(*world), walkmesh_snap=False))
        menu.addAction("Insert Encounter").triggered.connect(lambda: self.add_instance(GITEncounter(*world), walkmesh_snap=False))
        menu.addAction("Insert Trigger").triggered.connect(lambda: self.add_instance(GITTrigger(*world), walkmesh_snap=False))
        return menu

    def on_instance_list_right_clicked(
        self,
        *args,
        **kwargs,
    ):
        item: QListWidgetItem = self.ui.instanceList.selectedItems()[0]
        instance: GITInstance = item.data(Qt.ItemDataRole.UserRole)
        self.on_context_menu_selection_exists(instances=[instance])

    def on_context_menu_selection_exists(
        self,
        world: Vector3 | None = None,
        *,
        is_flat_renderer_call: bool | None = None,
        get_menu: bool | None = None,
        instances: Sequence[GITInstance] | None = None,
    ) -> _QMenu | None:  # sourcery skip: extract-method
        self.log.debug(f"onContextMenuSelectionExists(isFlatRendererCall={is_flat_renderer_call}, getMenu={get_menu})")
        menu = QMenu(self)
        instances = self.selected_instances if instances is None else instances

        if instances:
            instance = instances[0]
            if isinstance(instance, GITCamera):
                menu.addAction("Snap Camera to 3D View").triggered.connect(lambda: self.snap_camera_to_view(instance))
                menu.addAction("Snap 3D View to Camera").triggered.connect(lambda: self.snap_view_to_git_camera(instance))
            else:
                menu.addAction("Snap 3D View to Instance Position").triggered.connect(lambda: self.snap_view_to_git_instance(instance))
            menu.addSeparator()
            menu.addAction("Copy position to clipboard").triggered.connect(lambda: QApplication.clipboard().setText(str(instance.position)))
            menu.addAction("Edit Instance").triggered.connect(lambda: self.edit_instance(instance))
            menu.addAction("Remove").triggered.connect(self.delete_selected)
            menu.addSeparator()
            if world is not None and not isinstance(self._controls2d._mode, _SpawnMode):
                self._controls2d._mode._get_render_context_menu(Vector2(world.x, world.y), menu)
        if not get_menu:
            self.show_final_context_menu(menu)
            return None
        return menu

    def show_final_context_menu(self, menu: _QMenu):
        menu.popup(self.cursor().pos())
        menu.aboutToHide.connect(self.ui.mainRenderer.reset_all_down)
        menu.aboutToHide.connect(self.ui.flatRenderer.reset_all_down)

    def on_3d_renderer_initialized(self):
        self.log.debug("ModuleDesigner on3dRendererInitialized")
        self.show()
        self.activateWindow()

    def on_3d_scene_initialized(self):
        self.log.debug("ModuleDesigner on3dSceneInitialized")
        self._refresh_window_title()
        self.show()
        self.activateWindow()

        # Defer UI population to avoid blocking during module load
        QTimer.singleShot(50, self._deferred_initialization)

    def _deferred_initialization(self):
        """Complete initialization after window is shown."""
        self.log.debug("Building resource tree and instance list...")
        self.rebuild_resource_tree()
        self.rebuild_instance_list()
        self.rebuild_layout_tree()
        self.enter_instance_mode()
        self.log.info("Module designer ready")

    def on_2d_mouse_moved(self, screen: Vector2, delta: Vector2, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        # self.log.debug("on2dMouseMoved, screen: %s, delta: %s, buttons: %s, keys: %s", screen, delta, buttons, keys)
        world_delta: Vector2 = self.ui.flatRenderer.to_world_delta(delta.x, delta.y)
        world: Vector3 = self.ui.flatRenderer.to_world_coords(screen.x, screen.y)
        self._controls2d.on_mouse_moved(screen, delta, Vector2.from_vector3(world), world_delta, buttons, keys)
        self.update_status_bar(QCursor.pos(), buttons, keys, self.ui.flatRenderer)

    def on_2d_mouse_released(self, screen: Vector2, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        # self.log.debug("on2dMouseReleased, screen: %s, buttons: %s, keys: %s", screen, buttons, keys)
        self._controls2d.on_mouse_released(screen, buttons, keys)
        self.update_status_bar(QCursor.pos(), buttons, keys, self.ui.flatRenderer)

    def on_2d_keyboard_pressed(self, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        # self.log.debug("on2dKeyboardPressed, buttons: %s, keys: %s", buttons, keys)
        self._controls2d.on_keyboard_pressed(buttons, keys)
        self.update_status_bar(QCursor.pos(), buttons, keys, self.ui.flatRenderer)

    def on_2d_keyboard_released(self, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        # self.log.debug("on2dKeyboardReleased, buttons: %s, keys: %s", buttons, keys)
        self._controls2d.on_keyboard_released(buttons, keys)
        self.update_status_bar(QCursor.pos(), buttons, keys, self.ui.flatRenderer)

    def on_2d_mouse_scrolled(self, delta: Vector2, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        # self.log.debug("on2dMouseScrolled, delta: %s, buttons: %s, keys: %s", delta, buttons, keys)
        self.update_status_bar(QCursor.pos(), buttons, keys, self.ui.flatRenderer)
        self._controls2d.on_mouse_scrolled(delta, buttons, keys)

    def on_2d_mouse_pressed(self, screen: Vector2, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        # self.log.debug("on2dMousePressed, screen: %s, buttons: %s, keys: %s", screen, buttons, keys)
        self._controls2d.on_mouse_pressed(screen, buttons, keys)
        self.update_status_bar(screen, buttons, keys, self.ui.flatRenderer)

    # endregion

    # region Layout Tab Handlers
    def on_add_room(self):
        """Add a new room to the layout."""
        if self._module is None:
            return

        layout_module = self._module.layout()
        if layout_module is None:
            self.log.warning("No layout resource found in module")
            return

        lyt: LYT | None = layout_module.resource()
        if lyt is None:
            lyt = LYT()
            layout_module._resource = lyt  # noqa: SLF001

        # Create a new room at origin
        room = LYTRoom(
            model="newroom",
            position=Vector3(0, 0, 0)
        )
        lyt.rooms.append(room)

        self.rebuild_layout_tree()
        self.log.info(f"Added room '{room.model}' to layout")

    def on_add_door_hook(self):
        """Add a new door hook to the layout."""
        if self._module is None:
            return

        layout_module = self._module.layout()
        if layout_module is None:
            self.log.warning("No layout resource found in module")
            return

        lyt: LYT | None = layout_module.resource()
        if lyt is None or not lyt.rooms:
            self.log.warning("Cannot add door hook: no rooms in layout")
            return

        # Create a new door hook
        doorhook = LYTDoorHook(
            room=lyt.rooms[0].model,
            door=f"door{len(lyt.doorhooks)}",
            position=Vector3(0, 0, 0),
            orientation=Vector4(0, 0, 0, 1)
        )
        lyt.doorhooks.append(doorhook)

        self.rebuild_layout_tree()
        self.log.info(f"Added door hook '{doorhook.door}' to layout")

    def on_add_track(self):
        """Add a new track to the layout."""
        if self._module is None:
            return

        layout_module = self._module.layout()
        if layout_module is None:
            self.log.warning("No layout resource found in module")
            return

        lyt: LYT | None = layout_module.resource()
        if lyt is None:
            lyt = LYT()
            layout_module._resource = lyt  # noqa: SLF001

        # Create a new track
        track = LYTTrack(
            model="newtrack",
            position=Vector3(0, 0, 0)
        )
        lyt.tracks.append(track)

        self.rebuild_layout_tree()
        self.log.info(f"Added track '{track.model}' to layout")

    def on_add_obstacle(self):
        """Add a new obstacle to the layout."""
        if self._module is None:
            return

        layout_module = self._module.layout()
        if layout_module is None:
            self.log.warning("No layout resource found in module")
            return

        lyt: LYT | None = layout_module.resource()
        if lyt is None:
            lyt = LYT()
            layout_module._resource = lyt  # noqa: SLF001

        # Create a new obstacle
        obstacle = LYTObstacle(
            model="newobstacle",
            position=Vector3(0, 0, 0)
        )
        lyt.obstacles.append(obstacle)

        self.rebuild_layout_tree()
        self.log.info(f"Added obstacle '{obstacle.model}' to layout")

    def on_import_texture(self):
        """Import a texture for use in the layout."""
        from qtpy.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Texture",
            "",
            "Image Files (*.tga *.tpc *.dds *.png *.jpg)"
        )

        if file_path:
            self.log.info(f"Importing texture from {file_path}")
            # TODO: Implement texture import logic

    def on_generate_walkmesh(self):
        """Generate walkmesh from the current layout."""
        if self._module is None:
            return

        layout_module = self._module.layout()
        if layout_module is None:
            self.log.warning("No layout resource found in module")
            return

        lyt: LYT | None = layout_module.resource()
        if lyt is None or not lyt.rooms:
            self.log.warning("Cannot generate walkmesh: no rooms in layout")
            return

        self.log.info("Generating walkmesh from layout...")
        # TODO: Implement walkmesh generation logic

    def rebuild_layout_tree(self):
        """Rebuild the layout tree widget to show current LYT structure."""
        if self._module is None:
            return

        layout_module = self._module.layout()
        if layout_module is None:
            return

        lyt: LYT | None = layout_module.resource()
        if lyt is None:
            return

        self.ui.lytTree.blockSignals(True)
        self.ui.lytTree.clear()

        # Add rooms
        if lyt.rooms:
            rooms_item = QTreeWidgetItem(["Rooms"])
            self.ui.lytTree.addTopLevelItem(rooms_item)
            for room in lyt.rooms:
                room_item = QTreeWidgetItem([room.model])
                room_item.setData(0, Qt.ItemDataRole.UserRole, room)
                rooms_item.addChild(room_item)
            rooms_item.setExpanded(True)

        # Add door hooks
        if lyt.doorhooks:
            doors_item = QTreeWidgetItem(["Door Hooks"])
            self.ui.lytTree.addTopLevelItem(doors_item)
            for doorhook in lyt.doorhooks:
                door_item = QTreeWidgetItem([doorhook.door])
                door_item.setData(0, Qt.ItemDataRole.UserRole, doorhook)
                doors_item.addChild(door_item)
            doors_item.setExpanded(True)

        # Add tracks
        if lyt.tracks:
            tracks_item = QTreeWidgetItem(["Tracks"])
            self.ui.lytTree.addTopLevelItem(tracks_item)
            for track in lyt.tracks:
                track_item = QTreeWidgetItem([track.model])
                track_item.setData(0, Qt.ItemDataRole.UserRole, track)
                tracks_item.addChild(track_item)
            tracks_item.setExpanded(True)

        # Add obstacles
        if lyt.obstacles:
            obstacles_item = QTreeWidgetItem(["Obstacles"])
            self.ui.lytTree.addTopLevelItem(obstacles_item)
            for obstacle in lyt.obstacles:
                obstacle_item = QTreeWidgetItem([obstacle.model])
                obstacle_item.setData(0, Qt.ItemDataRole.UserRole, obstacle)
                obstacles_item.addChild(obstacle_item)
            obstacles_item.setExpanded(True)

        self.ui.lytTree.blockSignals(False)

        # Update LYT renderer if it exists
        if self._lyt_renderer:
            self._lyt_renderer.set_lyt(lyt)

    def on_lyt_tree_selection_changed(self):
        """Handle selection change in the layout tree."""
        selected_items: list[QTreeWidgetItem] = self.ui.lytTree.selectedItems()
        if not selected_items:
            return

        item = selected_items[0]
        data = item.data(0, Qt.ItemDataRole.UserRole)

        if isinstance(data, LYTRoom):
            self.ui.lytElementTabs.setCurrentIndex(0)  # Room tab
            self.update_room_properties(data)
        elif isinstance(data, LYTDoorHook):
            self.ui.lytElementTabs.setCurrentIndex(1)  # Door Hook tab
            self.update_doorhook_properties(data)

    def update_room_properties(self, room: LYTRoom):
        """Update the room property editors with the selected room's data."""
        self.ui.modelEdit.blockSignals(True)
        self.ui.posXSpin.blockSignals(True)
        self.ui.posYSpin.blockSignals(True)
        self.ui.posZSpin.blockSignals(True)
        self.ui.rotXSpin.blockSignals(True)
        self.ui.rotYSpin.blockSignals(True)
        self.ui.rotZSpin.blockSignals(True)

        self.ui.modelEdit.setText(room.model)
        self.ui.posXSpin.setValue(room.position.x)
        self.ui.posYSpin.setValue(room.position.y)
        self.ui.posZSpin.setValue(room.position.z)

        # LYTRoom doesn't have orientation - reset rotation spinboxes
        self.ui.rotXSpin.setValue(0)
        self.ui.rotYSpin.setValue(0)
        self.ui.rotZSpin.setValue(0)

        self.ui.modelEdit.blockSignals(False)
        self.ui.posXSpin.blockSignals(False)
        self.ui.posYSpin.blockSignals(False)
        self.ui.posZSpin.blockSignals(False)
        self.ui.rotXSpin.blockSignals(False)
        self.ui.rotYSpin.blockSignals(False)
        self.ui.rotZSpin.blockSignals(False)

    def update_doorhook_properties(self, doorhook: LYTDoorHook):
        """Update the door hook property editors with the selected door hook's data."""
        if self._module is None:
            return

        layout_module = self._module.layout()
        if layout_module is None:
            return

        lyt: LYT | None = layout_module.resource()
        if lyt is None:
            return

        self.ui.roomNameCombo.blockSignals(True)
        self.ui.doorNameEdit.blockSignals(True)

        # Populate room combo
        self.ui.roomNameCombo.clear()
        for room in lyt.rooms:
            self.ui.roomNameCombo.addItem(room.model)

        # Set current values
        self.ui.roomNameCombo.setCurrentText(doorhook.room)
        self.ui.doorNameEdit.setText(doorhook.door)

        self.ui.roomNameCombo.blockSignals(False)
        self.ui.doorNameEdit.blockSignals(False)

    def get_selected_lyt_element(self) -> LYTRoom | LYTDoorHook | LYTTrack | LYTObstacle | None:
        """Get the currently selected LYT element from the tree."""
        selected_items = self.ui.lytTree.selectedItems()
        if not selected_items:
            return None
        return selected_items[0].data(0, Qt.ItemDataRole.UserRole)

    def on_room_position_changed(self):
        """Handle room position change from spinboxes."""
        element = self.get_selected_lyt_element()
        if not isinstance(element, LYTRoom):
            return

        element.position.x = self.ui.posXSpin.value()
        element.position.y = self.ui.posYSpin.value()
        element.position.z = self.ui.posZSpin.value()

    def on_room_rotation_changed(self):
        """Handle room rotation change from spinboxes."""
        element = self.get_selected_lyt_element()
        if not isinstance(element, LYTRoom):
            return

        # LYTRoom doesn't have orientation property - this is a no-op
        # Rotation is handled at the model level, not the room level

    def on_room_model_changed(self):
        """Handle room model name change."""
        element = self.get_selected_lyt_element()
        if not isinstance(element, LYTRoom):
            return

        element.model = self.ui.modelEdit.text()
        self.rebuild_layout_tree()

    def on_browse_model(self):
        """Browse for a model file to assign to the room."""
        from qtpy.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Model",
            "",
            "Model Files (*.mdl)"
        )

        if file_path:
            model_name = Path(file_path).stem
            self.ui.modelEdit.setText(model_name)

    def on_doorhook_room_changed(self):
        """Handle door hook room change."""
        element = self.get_selected_lyt_element()
        if not isinstance(element, LYTDoorHook):
            return

        element.room = self.ui.roomNameCombo.currentText()

    def on_doorhook_name_changed(self):
        """Handle door hook name change."""
        element = self.get_selected_lyt_element()
        if not isinstance(element, LYTDoorHook):
            return

        element.door = self.ui.doorNameEdit.text()
        self.rebuild_layout_tree()

    def on_lyt_tree_context_menu(self, point: QPoint):
        """Show context menu for layout tree items."""
        item = self.ui.lytTree.itemAt(point)
        if not item:
            return

        element = item.data(0, Qt.ItemDataRole.UserRole)
        if not element:
            return

        menu = QMenu(self)

        # Common operations
        edit_action = QAction("Edit Properties", self)
        edit_action.triggered.connect(lambda: self.edit_lyt_element(element))
        menu.addAction(edit_action)

        duplicate_action = QAction("Duplicate", self)
        duplicate_action.triggered.connect(lambda: self.duplicate_lyt_element(element))
        menu.addAction(duplicate_action)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.delete_lyt_element(element))
        menu.addAction(delete_action)

        menu.addSeparator()

        # Type-specific operations
        if isinstance(element, LYTRoom):
            load_model_action = QAction("Load Room Model", self)
            load_model_action.triggered.connect(lambda: self.load_room_model(element))
            menu.addAction(load_model_action)

        elif isinstance(element, LYTDoorHook):
            place_action = QAction("Place in 3D View", self)
            place_action.triggered.connect(lambda: self.place_doorhook_in_view(element))
            menu.addAction(place_action)

        menu.exec(self.ui.lytTree.mapToGlobal(point))

    def edit_lyt_element(self, element: LYTRoom | LYTDoorHook | LYTTrack | LYTObstacle):
        """Open editor dialog for LYT element."""
        # Select the element in the tree
        for i in range(self.ui.lytTree.topLevelItemCount()):
            parent = self.ui.lytTree.topLevelItem(i)
            if parent:
                for j in range(parent.childCount()):
                    child = parent.child(j)
                    if child and child.data(0, Qt.ItemDataRole.UserRole) == element:
                        self.ui.lytTree.setCurrentItem(child)
                        break

    def duplicate_lyt_element(self, element: LYTRoom | LYTDoorHook | LYTTrack | LYTObstacle):
        """Duplicate the selected LYT element."""
        if self._module is None:
            return

        layout_module = self._module.layout()
        if layout_module is None:
            return

        lyt: LYT | None = layout_module.resource()
        if lyt is None:
            return

        # Create duplicate with offset
        offset = Vector3(10, 10, 0)

        if isinstance(element, LYTRoom):
            new_element = LYTRoom(f"{element.model}_copy", element.position + offset)
            lyt.rooms.append(new_element)
        elif isinstance(element, LYTDoorHook):
            new_element = LYTDoorHook(
                element.room,
                f"{element.door}_copy",
                element.position + offset,
                element.orientation
            )
            lyt.doorhooks.append(new_element)
        elif isinstance(element, LYTTrack):
            new_element = LYTTrack(f"{element.model}_copy", element.position + offset)
            lyt.tracks.append(new_element)
        elif isinstance(element, LYTObstacle):
            new_element = LYTObstacle(f"{element.model}_copy", element.position + offset)
            lyt.obstacles.append(new_element)

        self.rebuild_layout_tree()
        self.log.info(f"Duplicated {type(element).__name__}")

    def delete_lyt_element(self, element: LYTRoom | LYTDoorHook | LYTTrack | LYTObstacle):
        """Delete the selected LYT element."""
        if self._module is None:
            return

        layout_module = self._module.layout()
        if layout_module is None:
            return

        lyt: LYT | None = layout_module.resource()
        if lyt is None:
            return

        # Confirm deletion
        element_type = type(element).__name__
        element_name = element.model if hasattr(element, 'model') else element.door if hasattr(element, 'door') else "element"

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete {element_type} '{element_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Remove element
        if isinstance(element, LYTRoom):
            lyt.rooms.remove(element)
        elif isinstance(element, LYTDoorHook):
            lyt.doorhooks.remove(element)
        elif isinstance(element, LYTTrack):
            lyt.tracks.remove(element)
        elif isinstance(element, LYTObstacle):
            lyt.obstacles.remove(element)

        self.rebuild_layout_tree()
        self.log.info(f"Deleted {element_type} '{element_name}'")

    def load_room_model(self, room: LYTRoom):
        """Load and display a room model in the 3D view."""
        if self._module is None:
            return

        # Try to load the MDL file
        mdl_resource = self._module.resource(room.model, ResourceType.MDL)
        if mdl_resource:
            self.log.info(f"Loading room model: {room.model}")
            # The model will be loaded and positioned at room.position
            # This would integrate with the 3D renderer's model loading system
        else:
            self.log.warning(f"Room model not found: {room.model}")
            QMessageBox.warning(
                self,
                "Model Not Found",
                f"Could not find model '{room.model}.mdl' in the module."
            )

    def place_doorhook_in_view(self, doorhook: LYTDoorHook):
        """Place the door hook at the current 3D view position."""
        # Get the cursor position from the 3D view
        scene = self.ui.mainRenderer.scene
        if scene:
            doorhook.position.x = scene.cursor.position().x
            doorhook.position.y = scene.cursor.position().y
            doorhook.position.z = scene.cursor.position().z
            self.rebuild_layout_tree()
            self.log.info(f"Placed door hook '{doorhook.door}' in 3D view")

    # endregion

    # region Events
    def keyPressEvent(self, e: QKeyEvent | None):  # noqa: FBT001, FBT002  # pyright: ignore[reportIncompatibleMethodOverride]
        if e is None:
            return
        super().keyPressEvent(e)
        self.ui.mainRenderer.keyPressEvent(e)
        self.ui.flatRenderer.keyPressEvent(e)

    def keyReleaseEvent(self, e: QKeyEvent | None):  # noqa: FBT001, FBT002  # pyright: ignore[reportIncompatibleMethodOverride]
        if e is None:
            return
        super().keyReleaseEvent(e)
        self.ui.mainRenderer.keyReleaseEvent(e)
        self.ui.flatRenderer.keyReleaseEvent(e)

    # endregion

    def update_camera(self):
        if not self.ui.mainRenderer.underMouse():
            return

        # Check camera rotation and movement keys
        keys: set[Qt.Key] = self.ui.mainRenderer.keys_down()
        buttons: set[Qt.MouseButton] = self.ui.mainRenderer.mouse_down()
        rotation_keys: dict[str, bool] = {
            "left": self._controls3d.rotate_camera_left.satisfied(buttons, keys),
            "right": self._controls3d.rotate_camera_right.satisfied(buttons, keys),
            "up": self._controls3d.rotate_camera_up.satisfied(buttons, keys),
            "down": self._controls3d.rotate_camera_down.satisfied(buttons, keys),
        }
        movement_keys: dict[str, bool] = {
            "up": self._controls3d.move_camera_up.satisfied(buttons, keys),
            "down": self._controls3d.move_camera_down.satisfied(buttons, keys),
            "left": self._controls3d.move_camera_left.satisfied(buttons, keys),
            "right": self._controls3d.move_camera_right.satisfied(buttons, keys),
            "forward": self._controls3d.move_camera_forward.satisfied(buttons, keys),
            "backward": self._controls3d.move_camera_backward.satisfied(buttons, keys),
            "in": self._controls3d.zoom_camera_in.satisfied(buttons, keys),
            "out": self._controls3d.zoom_camera_out.satisfied(buttons, keys),
        }

        # Determine last frame time to determine the delta modifiers
        cur_time = time.time()
        time_since_last_frame = cur_time - self.last_frame_time
        self.last_frame_time = cur_time

        # Skip if frame time is too large (e.g., window was minimized)
        if time_since_last_frame > 0.1:
            return

        # Calculate rotation delta with frame-independent timing
        norm_rotate_units_setting: float = self.settings.rotateCameraSensitivity3d / 1000
        norm_rotate_units_setting *= self.target_frame_rate * time_since_last_frame
        angle_units_delta: float = (math.pi / 4) * norm_rotate_units_setting

        # Rotate camera based on key inputs
        if rotation_keys["left"]:
            self.ui.mainRenderer.rotate_camera(angle_units_delta, 0)
        elif rotation_keys["right"]:
            self.ui.mainRenderer.rotate_camera(-angle_units_delta, 0)
        if rotation_keys["up"]:
            self.ui.mainRenderer.rotate_camera(0, angle_units_delta)
        elif rotation_keys["down"]:
            self.ui.mainRenderer.rotate_camera(0, -angle_units_delta)

        # Calculate movement delta
        if self._controls3d.speed_boost_control.satisfied(
            self.ui.mainRenderer.mouse_down(),
            self.ui.mainRenderer.keys_down(),
            exact_keys_and_buttons=False,
        ):
            move_units_delta: float = (
                self.settings.boostedFlyCameraSpeedFC
                if isinstance(self._controls3d, ModuleDesignerControlsFreeCam)
                else self.settings.boostedMoveCameraSensitivity3d
            )
        else:
            move_units_delta = (
                self.settings.flyCameraSpeedFC
                if isinstance(self._controls3d, ModuleDesignerControlsFreeCam)
                else self.settings.moveCameraSensitivity3d
            )

        move_units_delta /= 500  # normalize
        move_units_delta *= time_since_last_frame * self.target_frame_rate  # apply modifier based on frame time

        # Zoom camera based on inputs
        if movement_keys["in"]:
            self.ui.mainRenderer.zoom_camera(move_units_delta)
        if movement_keys["out"]:
            self.ui.mainRenderer.zoom_camera(-move_units_delta)

        # Move camera based on key inputs
        if movement_keys["up"]:
            if isinstance(self._controls3d, ModuleDesignerControls3d):
                self.ui.mainRenderer.scene.camera.z += move_units_delta
            else:
                self.ui.mainRenderer.move_camera(0, 0, move_units_delta)
        if movement_keys["down"]:
            if isinstance(self._controls3d, ModuleDesignerControls3d):
                self.ui.mainRenderer.scene.camera.z -= move_units_delta
            else:
                self.ui.mainRenderer.move_camera(0, 0, -move_units_delta)

        if movement_keys["left"]:
            if isinstance(self._controls3d, ModuleDesignerControls3d):
                self.ui.mainRenderer.pan_camera(0, -move_units_delta, 0)
            else:
                self.ui.mainRenderer.move_camera(0, -move_units_delta, 0)
        if movement_keys["right"]:
            if isinstance(self._controls3d, ModuleDesignerControls3d):
                self.ui.mainRenderer.pan_camera(0, move_units_delta, 0)
            else:
                self.ui.mainRenderer.move_camera(0, move_units_delta, 0)

        if movement_keys["forward"]:
            if isinstance(self._controls3d, ModuleDesignerControls3d):
                self.ui.mainRenderer.pan_camera(move_units_delta, 0, 0)
            else:
                self.ui.mainRenderer.move_camera(move_units_delta, 0, 0)
        if movement_keys["backward"]:
            if isinstance(self._controls3d, ModuleDesignerControls3d):
                self.ui.mainRenderer.pan_camera(-move_units_delta, 0, 0)
            else:
                self.ui.mainRenderer.move_camera(-move_units_delta, 0, 0)
