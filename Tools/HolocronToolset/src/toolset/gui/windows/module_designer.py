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

from pykotor.common.geometry import SurfaceMaterial, Vector2, Vector3, Vector4
from pykotor.common.misc import Color, ResRef
from pykotor.common.module import Module, ModuleResource
from pykotor.extract.file import ResourceIdentifier
from pykotor.gl.scene import Camera
from pykotor.resource.generics.git import GITCamera, GITCreature, GITDoor, GITEncounter, GITInstance, GITPlaceable, GITSound, GITStore, GITTrigger, GITWaypoint
from pykotor.resource.generics.utd import read_utd
from pykotor.resource.generics.utt import read_utt
from pykotor.resource.generics.utw import read_utw
from pykotor.resource.type import ResourceType
from pykotor.tools import module
from pykotor.tools.misc import is_mod_file
from toolset.data.installation import HTInstallation
from toolset.gui.dialogs.asyncloader import AsyncLoader
from toolset.gui.dialogs.insert_instance import InsertInstanceDialog
from toolset.gui.dialogs.select_module import SelectModuleDialog
from toolset.gui.editor import Editor
from toolset.gui.editors.git import DeleteCommand, MoveCommand, RotateCommand, _GeometryMode, _InstanceMode, _SpawnMode, open_instance_dialog
from toolset.gui.widgets.renderer.module import ModuleRenderer
from toolset.gui.widgets.settings.widgets.module_designer import ModuleDesignerSettings
from toolset.gui.windows.designer_controls import ModuleDesignerControls2d, ModuleDesignerControls3d, ModuleDesignerControlsFreeCam
from toolset.gui.windows.help import HelpWindow
from toolset.utils.misc import MODIFIER_KEY_NAMES, get_qt_button_string, get_qt_key_string
from toolset.utils.window import open_resource_editor
from utility.error_handling import safe_repr

if TYPE_CHECKING:

    from glm import vec3
    from qtpy.QtGui import QCloseEvent, QFont, QKeyEvent, QShowEvent
    from qtpy.QtWidgets import QCheckBox
    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from pykotor.gl.scene import Camera
    from pykotor.resource.formats.bwm.bwm_data import BWM
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
        """Initializes the Module Designer window.

        Args:
        ----
            parent: QWidget | None: Parent widget
            installation: HTInstallation: Hometuck installation

        Processing Logic:
        ----------------
            - Initializes UI elements and connects signals
            - Sets up 3D and 2D renderer controls
            - Populates resource tree and instance list
            - Sets window title and loads module on next frame.
        """
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

        self.best_frame_rate = 60
        self.camera_update_timer = QTimer()
        self.camera_update_timer.timeout.connect(self.update_camera)
        self.camera_update_timer.start(int(1000 / self.best_frame_rate))  # ~60 FPS
        self.last_frame_time: float = time.time()

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

        self.ui.mainRenderer.sig_mouse_pressed.connect(self.on_3d_mouse_pressed)
        self.ui.mainRenderer.sig_mouse_released.connect(self.on_3d_mouse_released)
        self.ui.mainRenderer.sig_mouse_moved.connect(self.on_3d_mouse_moved)
        self.ui.mainRenderer.sig_mouse_scrolled.connect(self.on_3d_mouse_scrolled)
        self.ui.mainRenderer.sig_keyboard_pressed.connect(self.on_3d_keyboard_pressed)
        self.ui.mainRenderer.sig_keyboard_released.connect(self.on_3d_keyboard_released)
        self.ui.mainRenderer.sig_object_selected.connect(self.on_3d_object_selected)
        self.ui.mainRenderer.sig_renderer_initialized.connect(self.on_3d_renderer_initialized)
        self.ui.mainRenderer.sig_scene_initialized.connect(self.on_3d_scene_initialized)

        self.ui.flatRenderer.sig_mouse_pressed.connect(self.on_2d_mouse_pressed)
        self.ui.flatRenderer.sig_mouse_released.connect(self.on_2d_mouse_released)
        self.ui.flatRenderer.sig_mouse_moved.connect(self.on_2d_mouse_moved)
        self.ui.flatRenderer.sig_mouse_scrolled.connect(self.on_2d_mouse_scrolled)
        self.ui.flatRenderer.sig_key_pressed.connect(self.on_2d_keyboard_pressed)
        self.ui.flatRenderer.sig_key_released.connect(self.on_2d_keyboard_released)

    def _init_ui(self):
        self.custom_status_bar = QStatusBar(self)
        self.setStatusBar(self.custom_status_bar)
        self.custom_status_bar_container = QWidget()
        self.custom_status_bar_layout = QVBoxLayout()
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

    def update_status_bar(self, mouse_pos: QPoint | Vector2, buttons: set[Qt.MouseButton], keys: set[Qt.Key], renderer: WalkmeshRenderer | ModuleRenderer):
        norm_mouse_pos = Vector2(mouse_pos.x(), mouse_pos.y()) if isinstance(mouse_pos, QPoint) else mouse_pos
        world_pos_3d = None

        if isinstance(renderer, ModuleRenderer):
            pos = renderer.scene.cursor.position()
            world_pos_3d = Vector3(pos.x, pos.y, pos.z)
            self.mouse_pos_label.setText(f"Mouse Coords: {world_pos_3d.y:.2f}, {world_pos_3d.z:.2f}")
            camera = renderer.scene.camera
            self.view_camera_label.setText(
                f"View: Pos ({camera.x:.2f}, {camera.y:.2f}, {camera.z:.2f}), Pitch: {camera.pitch:.2f}, Yaw: {camera.yaw:.2f}, FOV: {camera.fov:.2f}"
            )
        else:
            worldPos = renderer.to_world_coords(norm_mouse_pos.x, norm_mouse_pos.y)
            self.mouse_pos_label.setText(f"Mouse Coords: {worldPos.y:.2f}")

        def sort_with_modifiers(items: set[Qt.MouseButton] | set[Qt.Key], get_string_func: Callable[[Any], str], qt_enum_type: Literal["Qt.Key", "Qt.MouseButton"]) -> Sequence[Qt.Key | Qt.MouseButton | int]:  # noqa: E501
            modifiers = [item for item in items if item in MODIFIER_KEY_NAMES] if qt_enum_type == "Qt.Key" else []
            normal = [item for item in items if item not in MODIFIER_KEY_NAMES] if qt_enum_type == "Qt.Key" else list(items)
            return sorted(modifiers, key=get_string_func) + sorted(normal, key=get_string_func)

        sorted_buttons = sort_with_modifiers(buttons, get_qt_button_string, "Qt.MouseButton")
        sorted_keys = sort_with_modifiers(keys, get_qt_key_string, "Qt.Key")

        self.buttons_keys_pressed_label.setText(f"Keys/Buttons: {'+'.join(map(get_qt_key_string, sorted_keys))} {'+'.join(map(get_qt_button_string, sorted_buttons))}")

        instance = self.selected_instances[0] if self.selected_instances else None
        self.selected_instance_label.setText(f"Selected Instance: {repr(instance) if isinstance(instance, GITCamera) else instance.identifier() if instance else 'None'}")

    def _refresh_window_title(self):
        if self._module is None:
            title = f"No Module - {self._installation.name} - Module Designer"
        else:
            title = f"{self._module.root()} - {self._installation.name} - Module Designer"
        self.setWindowTitle(title)

    def open_module_with_dialog(self):
        dialog = SelectModuleDialog(self, self._installation)

        if dialog.exec():
            mod_filepath = self._installation.module_path().joinpath(dialog.module)
            self.open_module(mod_filepath)

    #    @with_variable_trace(Exception)
    def open_module(self, mod_filepath: Path):
        """Opens a module."""
        mod_root = self._installation.get_module_root(mod_filepath)
        mod_filepath = self._ensure_mod_file(mod_filepath, mod_root)

        self.unload_module()
        combined_module = Module(mod_root, self._installation, use_dot_mod=is_mod_file(mod_filepath))
        git = combined_module.git().resource()
        if git is None:
            raise ValueError(f"This module '{mod_root}' is missing a GIT!")

        walkmeshes: list[BWM] = []
        for mod_resource in combined_module.resources.values():
            res_obj = mod_resource.resource()
            if res_obj is not None and mod_resource.restype() is ResourceType.WOK:
                walkmeshes.append(res_obj)
        result = (combined_module, git, walkmeshes)
        new_module, git, walkmeshes = result
        self._module = new_module
        self.ui.flatRenderer.set_git(git)
        self.ui.mainRenderer.initialize_renderer(self._installation, new_module)
        self.ui.mainRenderer.scene.show_cursor = self.ui.cursorCheck.isChecked()
        self.ui.flatRenderer.set_walkmeshes(walkmeshes)
        self.ui.flatRenderer.center_camera()
        self.show()

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
                (
                    f"You've chosen '{orig_filepath.name}' with a '{orig_filepath.suffix}' extension.<br><br>"
                    f"The Module Designer recommends modifying .mod's.<br><br>"
                    f"Use '{mod_filepath.name}' instead?"
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            == QMessageBox.StandardButton.Yes
        )

    def _load_async(self, mod_filepath: Path, task: Callable) -> tuple | None:
        loader = AsyncLoader(
            self,
            f"Loading module '{mod_filepath.name}' into designer...",
            task,
            "Error occurred loading the module designer",
        )
        return loader.value if loader.exec() else None

    def unload_module(self):
        self._module = None
        self.ui.mainRenderer.shutdown_renderer()

    def show_help_window(self):
        window = HelpWindow(self, "./help/tools/1-moduleEditor.md")
        window.show()

    def git(self) -> GIT:
        return self._module.git().resource()

    def are(self) -> ARE:
        return self._module.are().resource()

    def ifo(self) -> IFO:
        return self._module.info().resource()

    def save_git(self):
        self._module.git().save()

    def rebuild_resource_tree(self):
        self.ui.resourceTree.clear()
        self.ui.resourceTree.setEnabled(True)

        # Only build if module is loaded
        if self._module is None:
            self.ui.resourceTree.setEnabled(False)
            return

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
            category = categories.get(resource.restype(), categories[ResourceType.INVALID])
            category.addChild(item)

        self.ui.resourceTree.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.ui.resourceTree.setSortingEnabled(True)

    def open_module_resource(self, resource: ModuleResource):
        editor: Editor | QMainWindow | None = open_resource_editor(
            resource.active(),
            resource.resname(),
            resource.restype(),
            resource.data(),
            self._installation,
            self,
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
                parent.setExpanded(True)
                item.setSelected(True)
                self.ui.resourceTree.scrollToItem(item)

    def rebuild_instance_list(self):
        self.log.debug("rebuild_instance_list called.")
        self.ui.instanceList.clear()

        # Only build if module is loaded
        if self._module is None:
            self.ui.instanceList.setEnabled(False)
            self.ui.instanceList.setVisible(False)
            return

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
            GITInstance: QPixmap(32, 32),
        }

        self.ui.instanceList.clear()
        items: list[QListWidgetItem] = []

        git: GIT = self._module.git().resource()

        for instance in git.instances():
            if visible_mapping[instance.__class__]:
                continue

            struct_index: int = git.index(instance)

            icon = QIcon(iconMapping[instance.__class__])
            item = QListWidgetItem(icon, "")
            font: QFont = item.font()

            if isinstance(instance, GITCamera):
                item.setText(f"Camera #{instance.camera_id}")
                item.setToolTip(f"Struct Index: {struct_index}\nCamera ID: {instance.camera_id}\nFOV: {instance.fov}")
                item.setData(Qt.ItemDataRole.UserRole + 1, "cam" + str(instance.camera_id).rjust(10, "0"))
            else:
                this_ident = instance.identifier()
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
                item.setData(Qt.ItemDataRole.UserRole + 1, instance.identifier().restype.extension + name)

            item.setFont(font)
            item.setData(Qt.ItemDataRole.UserRole, instance)
            items.append(item)

        for item in sorted(items, key=lambda i: i.data(Qt.ItemDataRole.UserRole + 1)):
            self.ui.instanceList.addItem(item)

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
            assert self._module is not None, "How did we get here without a module?"
            dialog = InsertInstanceDialog(self, self._installation, self._module, instance.identifier().restype)
            if dialog.exec():
                self.rebuild_resource_tree()
                instance.resref = ResRef(dialog.resname)  # pyright: ignore[reportAttributeAccessIssue]
                self._module.git().resource().add(instance)

                if isinstance(instance, GITWaypoint):
                    utw = read_utw(dialog.data)
                    instance.tag = utw.tag
                    instance.name = utw.name
                elif isinstance(instance, GITTrigger):
                    utt = read_utt(dialog.data)
                    instance.tag = utt.tag
                    if not instance.geometry:
                        RobustLogger().info("Creating default triangle trigger geometry for %s.%s...", instance.resref, "utt")
                        instance.geometry.create_triangle(origin=instance.position)
                elif isinstance(instance, GITEncounter):
                    if not instance.geometry:
                        RobustLogger().info("Creating default triangle trigger geometry for %s.%s...", instance.resref, "ute")
                        instance.geometry.create_triangle(origin=instance.position)
                elif isinstance(instance, GITDoor):
                    utd = read_utd(dialog.data)
                    instance.tag = utd.tag
        else:
            self._module.git().resource().add(instance)
        self.rebuild_instance_list()

    def add_instance_at_cursor(self, instance: GITInstance):
        scene = self.ui.mainRenderer.scene
        assert scene is not None

        instance.position.x = scene.cursor.position().x
        instance.position.y = scene.cursor.position().y
        instance.position.z = scene.cursor.position().z

        if not isinstance(instance, GITCamera):
            assert self._module is not None
            dialog = InsertInstanceDialog(self, self._installation, self._module, instance.identifier().restype)

            if dialog.exec():
                self.rebuild_resource_tree()
                instance.resref = ResRef(dialog.resname)  # pyright: ignore[reportAttributeAccessIssue]
                self._module.git().resource().add(instance)
        else:
            if isinstance(instance, (GITEncounter, GITTrigger)) and not instance.geometry:
                self.log.info("Creating default triangle geometry for %s.%s", instance.resref, "utt" if isinstance(instance, GITTrigger) else "ute")
                instance.geometry.create_triangle(origin=instance.position)
            self._module.git().resource().add(instance)
        self.rebuild_instance_list()

    def edit_instance(self, instance: GITInstance):
        if open_instance_dialog(self, instance, self._installation):
            if not isinstance(instance, GITCamera):
                ident = instance.identifier()
                self.ui.mainRenderer.scene.clear_cache_buffer.append(ident)
            self.rebuild_instance_list()

    def snap_camera_to_view(self, git_camera_instance: GITCamera):
        view_camera: Camera = self._get_scene_camera()
        view_position: vec3 = view_camera.true_position()

        new_position = Vector3(view_position.x, view_position.y, view_position.z - git_camera_instance.height)
        self.undo_stack.push(MoveCommand(git_camera_instance, git_camera_instance.position, new_position))
        git_camera_instance.position = new_position

        self.log.debug("Create RotateCommand for undo/redo functionality")
        pitch = math.pi - (view_camera.pitch + (math.pi / 2))
        yaw = math.pi / 2 - view_camera.yaw
        new_orientation = Vector4.from_euler(yaw, 0, pitch)
        self.undo_stack.push(RotateCommand(git_camera_instance, git_camera_instance.orientation, new_orientation))
        git_camera_instance.orientation = new_orientation

    def snap_view_to_git_camera(self, git_camera_instance: GITCamera):
        view_camera: Camera = self._get_scene_camera()
        euler: Vector3 = git_camera_instance.orientation.to_euler()
        view_camera.pitch = math.pi - euler.z - math.radians(git_camera_instance.pitch)
        view_camera.yaw = math.pi / 2 - euler.x
        view_camera.x = git_camera_instance.position.x
        view_camera.y = git_camera_instance.position.y
        view_camera.z = git_camera_instance.position.z + git_camera_instance.height
        view_camera.distance = 0

    def snap_view_to_git_instance(self, git_instance: GITInstance):
        camera: Camera = self._get_scene_camera()
        yaw = git_instance.yaw()
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

    def delete_selected(self, *, no_undo_stack: bool = False):
        if not no_undo_stack:
            self.undo_stack.push(DeleteCommand(self.git(), self.selected_instances.copy(), self))  # noqa: SLF001
        for instance in self.selected_instances:
            self._module.git().resource().remove(instance)
        self.selected_instances.clear()
        self.ui.mainRenderer.scene.selection.clear()
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
    def _on_saved_resource(self, resource: ModuleResource):
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
        instance_mode.delete_selected = self.delete_selected
        instance_mode.edit_selected_instance = self.edit_instance  # type: ignore[method-assign]
        instance_mode.build_list = self.rebuild_instance_list
        instance_mode.update_visibility = self.update_toggles
        instance_mode.select_underneath = lambda: self.set_selection(self.ui.flatRenderer.instances_under_mouse())
        instance_mode.__init__(self, self._installation, self.git())
        # self._controls2d._mode.rotateSelectedToPoint = self.rotateSelected
        self._controls2d._mode = instance_mode  # noqa: SLF001

    def enter_geometry_mode(self):
        self._controls2d._mode = _GeometryMode(self, self._installation, self.git(), hide_others=False)  # noqa: SLF001

    def enter_spawn_mode(self):
        # TODO(NickHugi):
        self._controls2d._mode = _SpawnMode(self, self._installation, self.git())  # noqa: SLF001

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
        data = cur_item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(data, ModuleResource):
            self.open_module_resource(data)

    def on_resource_tree_single_clicked(self, point: QPoint):
        cur_item = self.ui.resourceTree.currentItem()
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

    def _active_instance_location_menu(self, data: ModuleResource, menu: QMenu):
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
                    self.set_selection([instance])
                    return

        menu.addAction("Find in Instance List").triggered.connect(jump_to_instance_list_action)

    def on_3d_mouse_moved(self, screen: Vector2, screenDelta: Vector2, world: Vector3, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        self.update_status_bar(screen, buttons, keys, self.ui.mainRenderer)
        self._controls3d.on_mouse_moved(screen, screenDelta, world, buttons, keys)

    def on_3d_mouse_scrolled(self, delta: Vector2, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        self.update_status_bar(QCursor.pos(), buttons, keys, self.ui.mainRenderer)
        self._controls3d.on_mouse_scrolled(delta, buttons, keys)

    def on_3d_mouse_pressed(self, screen: Vector2, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        self.update_status_bar(screen, buttons, keys, self.ui.mainRenderer)
        self._controls3d.on_mouse_pressed(screen, buttons, keys)

    def do_cursor_lock(self, mutable_screen: Vector2, *, center_mouse: bool = True, do_rotations: bool = True):
        global_new_pos = QCursor.pos()
        renderer = self.ui.mainRenderer

        if center_mouse:
            global_old_pos = renderer.mapToGlobal(renderer.rect().center())
            QCursor.setPos(global_old_pos)
        else:
            global_old_pos = renderer.mapToGlobal(QPoint(int(renderer._mouse_prev.x), int(renderer._mouse_prev.y)))  # noqa: SLF001
            QCursor.setPos(global_old_pos)
            local_old_pos = renderer.mapFromGlobal(global_old_pos)
            mutable_screen.x, mutable_screen.y = local_old_pos.x(), local_old_pos.y()

        if do_rotations:
            yaw_delta = global_old_pos.x() - global_new_pos.x()
            pitch_delta = global_old_pos.y() - global_new_pos.y()

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

    def on_context_menu(self, world: Vector3, point: QPoint):
        if self._module is None:
            return

        if len(self.ui.mainRenderer.scene.selection) == 0:
            menu = self.build_insert_instance_menu(world)
        else:
            menu = self.on_context_menu_selection_exists(world, get_menu=True)

        if menu is not None:
            self.show_final_context_menu(menu)

    def build_insert_instance_menu(self, world: Vector3) -> QMenu:
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

    def on_instance_list_right_clicked(self, *args, **kwargs):
        self.on_context_menu_selection_exists(instances=[self.ui.instanceList.selectedItems()[0].data(Qt.ItemDataRole.UserRole)])

    def on_context_menu_selection_exists(
        self,
        world: Vector3 | None = None,
        *,
        get_menu: bool | None = None,
        instances: Sequence[GITInstance] | None = None,
    ) -> QMenu | None:  # sourcery skip: extract-method
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
            if world is not None:
                self._controls2d._mode._get_render_context_menu(Vector2(world.x, world.y), menu)  # noqa: SLF001
        if not get_menu:
            self.show_final_context_menu(menu)
            return None
        return menu

    def show_final_context_menu(self, menu: QMenu):
        menu.popup(self.cursor().pos())
        menu.aboutToHide.connect(self.ui.mainRenderer.reset_all_down)
        menu.aboutToHide.connect(self.ui.flatRenderer.reset_all_down)

    def on_3d_renderer_initialized(self):
        self.show()
        self.activateWindow()

    def on_3d_scene_initialized(self):
        self.rebuild_resource_tree()
        self.rebuild_instance_list()
        self._refresh_window_title()
        self.enter_instance_mode()
        self.show()
        self.activateWindow()

    def on_2d_mouse_moved(self, screen: Vector2, delta: Vector2, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        # self.log.debug("on2dMouseMoved, screen: %s, delta: %s, buttons: %s, keys: %s", screen, delta, buttons, keys)
        world_delta: Vector2 = self.ui.flatRenderer.to_world_delta(delta.x, delta.y)
        world: Vector3 = self.ui.flatRenderer.to_world_coords(screen.x, screen.y)
        self._controls2d.on_mouse_moved(screen, delta, Vector2.from_vector3(world), world_delta, buttons, keys)
        self.update_status_bar(QCursor.pos(), buttons, keys, self.ui.flatRenderer)

    def on_2d_mouse_released(self, screen: Vector2, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        # self.log.debug("on_2d_mouse_released, screen: %s, buttons: %s, keys: %s", screen, buttons, keys)
        self._controls2d.on_mouse_released(screen, buttons, keys)
        self.update_status_bar(QCursor.pos(), buttons, keys, self.ui.flatRenderer)

    def on_2d_keyboard_pressed(self, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        # self.log.debug("on_2d_keyboard_pressed, buttons: %s, keys: %s", buttons, keys)
        self._controls2d.on_keyboard_pressed(buttons, keys)
        self.update_status_bar(QCursor.pos(), buttons, keys, self.ui.flatRenderer)

    def on_2d_keyboard_released(self, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        # self.log.debug("on_2d_keyboard_released, buttons: %s, keys: %s", buttons, keys)
        self._controls2d.on_keyboard_released(buttons, keys)
        self.update_status_bar(QCursor.pos(), buttons, keys, self.ui.flatRenderer)

    def on_2d_mouse_scrolled(self, delta: Vector2, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        # self.log.debug("on_2d_mouse_scrolled, delta: %s, buttons: %s, keys: %s", delta, buttons, keys)
        self.update_status_bar(QCursor.pos(), buttons, keys, self.ui.flatRenderer)
        self._controls2d.on_mouse_scrolled(delta, buttons, keys)

    def on_2d_mouse_pressed(self, screen: Vector2, buttons: set[Qt.MouseButton], keys: set[Qt.Key]):
        # self.log.debug("on_2d_mouse_pressed, screen: %s, buttons: %s, keys: %s", screen, buttons, keys)
        self._controls2d.on_mouse_pressed(screen, buttons, keys)
        self.update_status_bar(screen, buttons, keys, self.ui.flatRenderer)
    # endregion

    # region Events
    def keyPressEvent(self, e: QKeyEvent | None, bubble: bool = True):  # noqa: FBT001, FBT002  # pyright: ignore[reportIncompatibleMethodOverride]
        if e is None:
            return
        super().keyPressEvent(e)
        self.ui.mainRenderer.keyPressEvent(e)
        self.ui.flatRenderer.keyPressEvent(e)

    def keyReleaseEvent(self, e: QKeyEvent | None, bubble: bool = True):  # noqa: FBT001, FBT002  # pyright: ignore[reportIncompatibleMethodOverride]
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
        keys = self.ui.mainRenderer.keys_down()
        buttons = self.ui.mainRenderer.mouse_down()
        rotation_keys = {
            "left": self._controls3d.rotate_camera_left.satisfied(buttons, keys),
            "right": self._controls3d.rotate_camera_right.satisfied(buttons, keys),
            "up": self._controls3d.rotate_camera_up.satisfied(buttons, keys),
            "down": self._controls3d.rotate_camera_down.satisfied(buttons, keys),
        }
        movement_keys = {
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
        cur_time = time.perf_counter()
        time_since_last_frame = cur_time - self.last_frame_time
        self.last_frame_time = cur_time

        # Calculate rotation delta
        norm_rotate_units_setting = self.settings.rotateCameraSensitivity3d / 1000
        norm_rotate_units_setting *= self.best_frame_rate * time_since_last_frame  # apply modifier based on user's fps
        angle_units_delta = (math.pi / 4) * norm_rotate_units_setting

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
        keys = self.ui.mainRenderer.keys_down()
        buttons = self.ui.mainRenderer.mouse_down()
        if self._controls3d.speed_boost_control.satisfied(buttons, keys, exact_keys_and_buttons=False):
            move_units_delta = (
                (self.settings.boostedFlyCameraSpeedFC)
                if isinstance(self._controls3d, ModuleDesignerControlsFreeCam)
                else (self.settings.boostedMoveCameraSensitivity3d)
            )
        else:
            move_units_delta = (
                self.settings.flyCameraSpeedFC
                if isinstance(self._controls3d, ModuleDesignerControlsFreeCam)
                else self.settings.moveCameraSensitivity3d
            )

        move_units_delta /= 500  # normalize
        move_units_delta *= self.best_frame_rate * time_since_last_frame  # apply modifier based on user's fps

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
