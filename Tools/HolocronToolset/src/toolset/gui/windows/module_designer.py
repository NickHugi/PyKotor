from __future__ import annotations

import math
import time

from typing import TYPE_CHECKING, Any, Callable, Generator, Sequence, Union

import qtpy

from qtpy.QtCore import QPoint, QTimer, Qt
from qtpy.QtGui import QColor, QCursor, QIcon, QPixmap
from qtpy.QtWidgets import QAction, QApplication, QHBoxLayout, QLabel, QListWidgetItem, QMainWindow, QMenu, QMessageBox, QStatusBar, QTreeWidgetItem, QWidget

from toolset.gui.widgets.renderer.lyt_editor import LYTEditor

if qtpy.API_NAME in ("PyQt5", "PySide2"):
    from qtpy.QtWidgets import QUndoStack
elif qtpy.API_NAME in ("PyQt6", "PySide6"):
    from qtpy.QtGui import QUndoStack
else:
    raise ValueError(f"Invalid QT_API: '{qtpy.API_NAME}'")

from glm import vec3
from loggerplus import RobustLogger
from qtpy.QtGui import QPalette

from pykotor.common.geometry import SurfaceMaterial, Vector2, Vector3, Vector4
from pykotor.common.misc import Color, ResRef
from pykotor.common.module import Module, ModuleResource
from pykotor.common.stream import BinaryWriter
from pykotor.extract.file import ResourceIdentifier
from pykotor.gl.scene import Camera
from pykotor.resource.generics.git import GITCamera, GITCreature, GITDoor, GITEncounter, GITPlaceable, GITSound, GITStore, GITTrigger, GITWaypoint
from pykotor.resource.generics.utd import read_utd
from pykotor.resource.generics.utt import read_utt
from pykotor.resource.generics.utw import read_utw
from pykotor.resource.type import ResourceType
from pykotor.tools import module
from pykotor.tools.misc import is_mod_file
from toolset.gui.dialogs.insert_instance import InsertInstanceDialog
from toolset.gui.dialogs.select_module import SelectModuleDialog
from toolset.gui.editor import Editor
from toolset.gui.editors.git import DeleteCommand, MoveCommand, RotateCommand, _GeometryMode, _InstanceMode, _SpawnMode, openInstanceDialog
from toolset.gui.widgets.renderer.module import ModuleRenderer
from toolset.gui.widgets.settings.module_designer import ModuleDesignerSettings
from toolset.gui.windows.designer_controls import ModuleDesignerControls2d, ModuleDesignerControls3d, ModuleDesignerControlsFreeCam
from toolset.gui.windows.help import HelpWindow
from toolset.utils.misc import MODIFIER_KEY_NAMES, getQtButtonString, getQtKeyString
from toolset.utils.window import openResourceEditor
from utility.error_handling import safe_repr

if TYPE_CHECKING:
    import os

    from data.misc import ControlItem
    from qtpy.QtGui import QCloseEvent, QKeyEvent, QShowEvent
    from qtpy.QtWidgets import QCheckBox
    from typing_extensions import Literal

    from pykotor.gl.scene import Camera
    from pykotor.resource.formats.bwm.bwm_data import BWM
    from pykotor.resource.generics.git import GIT, GITInstance
    from toolset.data.installation import HTInstallation
    from toolset.gui.widgets.renderer.walkmesh import WalkmeshRenderer
    from utility.system.path import Path


class ModuleDesigner(QMainWindow):
    def __init__(self,
        parent: QWidget | None,
        installation: HTInstallation,
        mod_filepath: Path | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Module Designer")

        self._installation: HTInstallation = installation
        self._module: Module | None = None
        self._origFilepath: Path | None = mod_filepath

        self.initialPositions: dict[GITInstance, Vector3] = {}
        self.initialRotations: dict[GITCamera | GITCreature | GITDoor | GITPlaceable | GITStore | GITWaypoint, Vector4 | float] = {}
        self.undoStack: QUndoStack = QUndoStack(self)

        self.selectedInstances: list[GITInstance] = []
        self.settings: ModuleDesignerSettings = ModuleDesignerSettings()
        self.log: RobustLogger = RobustLogger()

        self.baseFrameRate: int = 60
        self.cameraUpdateTimer: QTimer = QTimer()
        self.cameraUpdateTimer.timeout.connect(self.update_camera)
        self.cameraUpdateTimer.start(int(1000 / self.baseFrameRate))  # ~60 FPS
        self.lastFrameTime: float = time.time()

        self.hideCreatures: bool = False
        self.hidePlaceables: bool = False
        self.hideDoors: bool = False
        self.hideTriggers: bool = False
        self.hideEncounters: bool = False
        self.hideWaypoints: bool = False
        self.hideSounds: bool = False
        self.hideStores: bool = False
        self.hideCameras: bool = False
        self.lockInstances: bool = False
        # used for the undo/redo events, don't create undo/redo events until the drag finishes.
        self.isDragMoving: bool = False
        self.isDragRotating: bool = False
        self.mousePosHistory: list[Vector2] = [Vector2(0, 0), Vector2(0, 0)]

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.windows.module_designer import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.windows.module_designer import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.windows.module_designer import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.windows.module_designer import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui: Ui_MainWindow = Ui_MainWindow()
        self.ui.setupUi(self)
        self.renderer = ModuleRenderer(self)
        self.ui.rendererLayout.addWidget(self.renderer)
        self.lytEditor = LYTEditor(self.renderer)

        self.settings = ModuleDesignerSettings()
        self.module: Module | None = None

        self.last_free_cam_time: float = 0.0  # Initialize the last toggle time

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

        self.ui.flatRenderer.materialColors = self.materialColors
        self.ui.flatRenderer.hideWalkmeshEdges = True
        self.ui.flatRenderer.highlightBoundaries = False

        self._controls3d: ModuleDesignerControls3d | ModuleDesignerControlsFreeCam = ModuleDesignerControls3d(self, self.ui.mainRenderer)
        # self._controls3d: ModuleDesignerControls3d | ModuleDesignerControlsFreeCam = ModuleDesignerControlsFreeCam(self, self.ui.mainRenderer)  # Doesn't work when set in __init__, trigger this in onMousePressed
        self._controls2d: ModuleDesignerControls2d = ModuleDesignerControls2d(self, self.ui.flatRenderer)

        if mod_filepath is None:  # Use singleShot timer so the ui window opens while the loading is happening.
            QTimer().singleShot(33, self.openModuleWithDialog)
        else:
            QTimer().singleShot(33, lambda: self.openModule(mod_filepath))

        self._setupSignals()
        self._initUi()

    def showEvent(self, a0: QShowEvent):
        if self.ui.mainRenderer._scene is None:  # noqa: SLF001
            return  # Don't show the window if the scene isn't ready, otherwise the gl context stuff will start prematurely.
        super().showEvent(a0)

    def closeEvent(self, event: QCloseEvent):
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Really quit the module designer? You may lose unsaved changes.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            event.accept()  # Let the window close
        else:
            event.ignore()  # Ignore the close event

    def _setupSignals(self):
        self.ui.actionOpen.triggered.connect(self.openModuleWithDialog)
        self.ui.actionSave.triggered.connect(self.saveGit)
        self.ui.actionInstructions.triggered.connect(self.showHelpWindow)

        self.ui.actionUndo.triggered.connect(lambda: print("Undo signal") or self.undoStack.undo())
        self.ui.actionRedo.triggered.connect(lambda: print("Redo signal") or self.undoStack.redo())

        self.ui.resourceTree.clicked.connect(self.onResourceTreeSingleClicked)
        self.ui.resourceTree.doubleClicked.connect(self.onResourceTreeDoubleClicked)
        self.ui.resourceTree.customContextMenuRequested.connect(self.onResourceTreeContextMenu)

        self.ui.viewCreatureCheck.toggled.connect(self.updateToggles)
        self.ui.viewPlaceableCheck.toggled.connect(self.updateToggles)
        self.ui.viewDoorCheck.toggled.connect(self.updateToggles)
        self.ui.viewSoundCheck.toggled.connect(self.updateToggles)
        self.ui.viewTriggerCheck.toggled.connect(self.updateToggles)
        self.ui.viewEncounterCheck.toggled.connect(self.updateToggles)
        self.ui.viewWaypointCheck.toggled.connect(self.updateToggles)
        self.ui.viewCameraCheck.toggled.connect(self.updateToggles)
        self.ui.viewStoreCheck.toggled.connect(self.updateToggles)
        self.ui.backfaceCheck.toggled.connect(self.updateToggles)
        self.ui.lightmapCheck.toggled.connect(self.updateToggles)
        self.ui.cursorCheck.toggled.connect(self.updateToggles)

        self.ui.viewCreatureCheck.mouseDoubleClickEvent = lambda a0: self.onInstanceVisibilityDoubleClick(self.ui.viewCreatureCheck)  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue, reportArgumentType]
        self.ui.viewPlaceableCheck.mouseDoubleClickEvent = lambda a0: self.onInstanceVisibilityDoubleClick(self.ui.viewPlaceableCheck)  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue, reportArgumentType]
        self.ui.viewDoorCheck.mouseDoubleClickEvent = lambda a0: self.onInstanceVisibilityDoubleClick(self.ui.viewDoorCheck)  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue, reportArgumentType]
        self.ui.viewSoundCheck.mouseDoubleClickEvent = lambda a0: self.onInstanceVisibilityDoubleClick(self.ui.viewSoundCheck)  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue, reportArgumentType]
        self.ui.viewTriggerCheck.mouseDoubleClickEvent = lambda a0: self.onInstanceVisibilityDoubleClick(self.ui.viewTriggerCheck)  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue, reportArgumentType]
        self.ui.viewEncounterCheck.mouseDoubleClickEvent = lambda a0: self.onInstanceVisibilityDoubleClick(self.ui.viewEncounterCheck)  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue, reportArgumentType]
        self.ui.viewWaypointCheck.mouseDoubleClickEvent = lambda a0: self.onInstanceVisibilityDoubleClick(self.ui.viewWaypointCheck)  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue, reportArgumentType]
        self.ui.viewCameraCheck.mouseDoubleClickEvent = lambda a0: self.onInstanceVisibilityDoubleClick(self.ui.viewCameraCheck)  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue, reportArgumentType]
        self.ui.viewStoreCheck.mouseDoubleClickEvent = lambda a0: self.onInstanceVisibilityDoubleClick(self.ui.viewStoreCheck)  # noqa: ARG005  # pyright: ignore[reportAttributeAccessIssue, reportArgumentType]

        self.ui.instanceList.clicked.connect(self.onInstanceListSingleClicked)
        self.ui.instanceList.doubleClicked.connect(self.onInstanceListDoubleClicked)
        self.ui.instanceList.customContextMenuRequested.connect(self.onInstanceListRightClicked)

        self.ui.mainRenderer.rendererInitialized.connect(self.on3dRendererInitialized)
        self.ui.mainRenderer.sceneInitialized.connect(self.on3dSceneInitialized)
        self.ui.mainRenderer.mousePressed.connect(self.on3dMousePressed)
        self.ui.mainRenderer.mouseReleased.connect(self.on3dMouseReleased)
        self.ui.mainRenderer.mouseMoved.connect(self.on3dMouseMoved)
        self.ui.mainRenderer.mouseScrolled.connect(self.on3dMouseScrolled)
        self.ui.mainRenderer.keyboardPressed.connect(self.on3dKeyboardPressed)
        self.ui.mainRenderer.objectSelected.connect(self.on3dObjectSelected)
        self.ui.mainRenderer.keyboardReleased.connect(self.on3dKeyboardReleased)

        self.ui.flatRenderer.mousePressed.connect(self.on2dMousePressed)
        self.ui.flatRenderer.mouseMoved.connect(self.on2dMouseMoved)
        self.ui.flatRenderer.mouseScrolled.connect(self.on2dMouseScrolled)
        self.ui.flatRenderer.keyPressed.connect(self.on2dKeyboardPressed)
        self.ui.flatRenderer.mouseReleased.connect(self.on2dMouseReleased)
        self.ui.flatRenderer.keyReleased.connect(self.on2dKeyboardReleased)

    def _initUi(self):
        self.customStatusBar = QStatusBar(self)
        self.setStatusBar(self.customStatusBar)

        self.mousePosLabel = QLabel("Mouse Coords: ")
        self.buttonsKeysPressedLabel = QLabel("Keys/Buttons: ")
        self.selectedInstanceLabel = QLabel("Selected Instance: ")
        self.viewCameraLabel = QLabel("View: ")

        # Create a horizontal layout for the first row
        firstRow = QHBoxLayout()
        firstRow.addWidget(self.mousePosLabel)
        firstRow.addWidget(self.selectedInstanceLabel)
        firstRow.addWidget(self.buttonsKeysPressedLabel)
        firstRow.addStretch(1)  # This will push all widgets to the left

        # Create a widget to hold the first row layout
        firstRowWidget = QWidget()
        firstRowWidget.setLayout(firstRow)

        # Add the first row widget and the view camera label directly to the status bar
        self.customStatusBar.addPermanentWidget(firstRowWidget, 1)  # Stretch factor of 1
        self.customStatusBar.addPermanentWidget(self.viewCameraLabel)

    def updateStatusBar(self, mouse_pos: QPoint | Vector2, buttons: set[int], keys: set[int], renderer: WalkmeshRenderer | ModuleRenderer):  # noqa: N803
        norm_mouse_pos = Vector2(mouse_pos.x(), mouse_pos.y()) if isinstance(mouse_pos, QPoint) else mouse_pos
        worldPos: Vector2 | Vector3
        worldPos3d: Vector3 | None = None
        if isinstance(renderer, ModuleRenderer):
            pos = renderer.scene.cursor.position()
            worldPos3d = Vector3(pos.x, pos.y, pos.z)
            self.mousePosLabel.setText(f"<b>Cursor:</b> <font color='{self.palette().color(QPalette.Link).name()}'>X: {worldPos3d.x:.2f}, Y: {worldPos3d.y:.2f}, Z: {worldPos3d.z:.2f}</font>")

            # Update view camera info
            camera = renderer.scene.camera
            self.viewCameraLabel.setText(
                f"<b>Camera:</b> <font color='{self.palette().color(QPalette.Link).name()}'>Position (X: {camera.x:.2f}, Y: {camera.y:.2f}, Z: {camera.z:.2f})</font> | "
                f"<b>Rotation:</b> <font color='{self.palette().color(QPalette.Link).name()}'>Pitch: {camera.pitch:.2f}°, Yaw: {camera.yaw:.2f}°</font> | "
                f"<b>FOV:</b> <font color='{self.palette().color(QPalette.Link).name()}'>{camera.fov:.2f}°</font>"
            )
        else:
            worldPos = renderer.toWorldCoords(norm_mouse_pos.x, norm_mouse_pos.y)
            self.mousePosLabel.setText(f"<b>Cursor:</b> <font color='{self.palette().color(QPalette.Link).name()}'>X: {worldPos.x:.2f}, Y: {worldPos.y:.2f}</font>")

        # Sort keys and buttons with modifiers at the beginning
        def sort_with_modifiers(items: set[int], get_string_func: Callable[[Any], str], gt_enum_type: Literal["QtKey", "QtMouse"]):
            modifiers = []
            if gt_enum_type == "QtKey":
                modifiers = [item for item in items if item in MODIFIER_KEY_NAMES]
                normal = [item for item in items if item not in MODIFIER_KEY_NAMES]
            else:
                normal = list(items)
            return sorted(modifiers, key=get_string_func) + sorted(normal, key=get_string_func)

        # Update keys/mouse buttons
        buttons_str = "+".join([getQtButtonString(button) for button in sort_with_modifiers(buttons, getQtButtonString, "QtMouse")])
        keys_str = "+".join([getQtKeyString(key) for key in sort_with_modifiers(keys, getQtKeyString, "QtKey")])
        self.buttonsKeysPressedLabel.setText(f"<b>Input:</b> <font color='{self.palette().color(QPalette.Link).name()}'>{keys_str} {buttons_str}</font>")

        # Update selected instance
        instance_name = "None"
        if self.selectedInstances:
            instance = self.selectedInstances[0]
            instance_name = repr(instance) if isinstance(instance, GITCamera) else instance.identifier()
        self.selectedInstanceLabel.setText(f"<b>Selected:</b> <font color='{self.palette().color(QPalette.Link).name()}'>{instance_name}</font>")

    def _refreshWindowTitle(self):
        if self._module is None:
            title = f"No Module - {self._installation.name} - Module Designer"
        else:
            title = f"{self._module.root_name()} - {self._installation.name} - Module Designer"
        self.setWindowTitle(title)

    def openModuleWithDialog(self):
        dialog = SelectModuleDialog(self, self._installation)

        if dialog.exec_():
            mod_filepath = self._installation.module_path().joinpath(dialog.module)
            self.openModule(mod_filepath)

    def openModule(self, mod_filepath: Path):
        """Opens a module."""
        mod_root = self._installation.get_module_root(mod_filepath)
        mod_filepath = self._ensure_mod_file(mod_filepath, mod_root)

        if mod_filepath is None:
            return  # User cancelled the operation

        self.unloadModule()  # Unload any existing module
        try:
            module_data = self._load_module_data(mod_filepath, mod_root)
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Error", f"Failed to load module: {e!s}")
            return

        self._setup_module(module_data)
        self.show()

    def _load_module_data(self, mod_filepath: Path, mod_root: str) -> tuple[Module, GIT, list[BWM]]:
        combined_module = Module(mod_root, self._installation, use_dot_mod=is_mod_file(mod_filepath))
        git_resource = combined_module.git()
        if git_resource is None:
            raise ValueError(f"The module '{mod_root}' is missing a GIT resource and cannot be used in the Module Designer.")

        git = git_resource.resource()
        assert git is not None

        walkmeshes = self._load_walkmeshes(combined_module)
        return (combined_module, git, walkmeshes)

    def _ensure_mod_file(self, mod_filepath: Path, mod_root: str) -> Path:
        mod_file = mod_filepath.with_name(f"{mod_root}.mod")
        if not mod_file.is_file():
            return self._handle_missing_mod_file(mod_filepath, mod_root)
        if mod_file != mod_filepath:
            return self._confirm_mod_file_usage(mod_filepath, mod_file)
        return mod_filepath

    def _handle_missing_mod_file(self, mod_filepath: Path, mod_root: str) -> Path:
        answer = QMessageBox.question(
            self,
            "Editing .RIM/.ERF modules is discouraged.",
            f"Create a .mod for module '{mod_root}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if answer == QMessageBox.Yes:
            new_mod_file = mod_filepath.with_name(f"{mod_root}.mod")
            module.rim_to_mod(new_mod_file, game=self._installation.game())
            self._installation.reload_module(new_mod_file.name)
            return new_mod_file

        return mod_filepath

    def _confirm_mod_file_usage(self, orig_filepath: Path, mod_file: Path) -> Path:
        answer = QMessageBox.question(
            self,
            f"{orig_filepath.suffix} file chosen when {mod_file.suffix} preferred.",
            f"Use '{mod_file.name}' instead of '{orig_filepath.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        return mod_file if answer == QMessageBox.Yes else orig_filepath

    def _load_walkmeshes(self, module: Module) -> list[BWM]:
        walkmeshes = []
        for bwm in module.resources.values():
            if bwm.restype() is not ResourceType.WOK:
                continue
            bwm_res = bwm.resource()
            if bwm_res is None:
                self.log.warning("bwm '%s.%s' returned None resource data, skipping...", bwm.resname(), bwm.restype())
                continue
            self.log.info("Adding walkmesh '%s.%s'", bwm.resname(), bwm.restype())
            walkmeshes.append(bwm_res)
        return walkmeshes

    def _setup_module(self, module_data: tuple[Module, GIT, list[BWM]]):
        self._module, git, walkmeshes = module_data
        self.ui.flatRenderer.setGit(git)
        self.ui.mainRenderer.initializeRenderer(self._installation, self._module)
        self.ui.mainRenderer.scene.show_cursor = self.ui.cursorCheck.isChecked()
        self.ui.flatRenderer.setWalkmeshes(walkmeshes)
        self.ui.flatRenderer.centerCamera()
        self.show()
        # Inherently calls On3dSceneInitialized when done.

    def unloadModule(self):
        self._module = None
        self.ui.mainRenderer.shutdownRenderer()

    def showHelpWindow(self):
        window = HelpWindow(self, "./help/tools/1-moduleEditor.md")
        window.show()

    def saveGit(self):
        self._module.git().save()
        # TODO: LYT Editing support
        # Also save LYT if it has been edited
        # if self.lyt_editor is not None and self.lyt_editor.is_modified():
        #     self.saveLYT()

    def rebuildResourceTree(self):
        self.ui.resourceTree.clear()
        self.ui.resourceTree.setEnabled(True)

        # Only build if module is loaded
        if self._module is None:
            self.ui.resourceTree.setEnabled(False)
            return

        categories = {ResourceType.UTC: QTreeWidgetItem(["Creatures"]), ResourceType.UTP: QTreeWidgetItem(["Placeables"]), ResourceType.UTD: QTreeWidgetItem(["Doors"]), ResourceType.UTI: QTreeWidgetItem(["Items"]), ResourceType.UTE: QTreeWidgetItem(["Encounters"]), ResourceType.UTT: QTreeWidgetItem(["Triggers"]), ResourceType.UTW: QTreeWidgetItem(["Waypoints"]), ResourceType.UTS: QTreeWidgetItem(["Sounds"]), ResourceType.UTM: QTreeWidgetItem(["Merchants"]), ResourceType.DLG: QTreeWidgetItem(["Dialogs"]), ResourceType.FAC: QTreeWidgetItem(["Factions"]), ResourceType.MDL: QTreeWidgetItem(["Models"]), ResourceType.TGA: QTreeWidgetItem(["Textures"]), ResourceType.NCS: QTreeWidgetItem(["Scripts"]), ResourceType.IFO: QTreeWidgetItem(["Module Data"]), ResourceType.INVALID: QTreeWidgetItem(["Other"])}  # noqa: E501
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
            item.setData(0, Qt.UserRole, resource)
            category = categories.get(resource.restype(), categories[ResourceType.INVALID])
            category.addChild(item)

        self.ui.resourceTree.sortByColumn(0, Qt.AscendingOrder)
        self.ui.resourceTree.setSortingEnabled(True)

    def openModuleResource(self, resource: ModuleResource):
        editor: Editor | QMainWindow | None = openResourceEditor(
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
            ).exec_()
        elif isinstance(editor, Editor):
            editor.savedFile.connect(lambda: self._onSavedResource(resource))

    def copyResourceToOverride(self, resource: ModuleResource):
        location = self._installation.override_path() / resource.identifier()
        if data := resource.data():
            BinaryWriter.dump(location, data)
            resource.add_locations([location])
            resource.activate(location)
            self.ui.mainRenderer.scene.clearCacheBuffer.append(resource.identifier())
        else:
            RobustLogger().error(f"Cannot find resource {resource.identifier()} to copy to Override. Locations: {resource.locations()}")

    def activateResourceFile(self, resource: ModuleResource, location: os.PathLike | str):
        resource.activate(location)
        self.ui.mainRenderer.scene.clearCacheBuffer.append(resource.identifier())

    def selectResourceItem(self, instance: GITInstance, *, clearExisting: bool = True):
        if clearExisting:
            self.ui.resourceTree.clearSelection()

        if (this_ident := instance.identifier()) is None:
            assert isinstance(instance, GITCamera), f"Identifier should only be None for GITCamera, not {type(instance).__name__}."
            return

        for parent in self._iter_tree_items(self.ui.resourceTree):
            for item in self._iter_tree_items(parent):
                if isinstance(res := item.data(0, Qt.UserRole), ModuleResource) and res.identifier() == this_ident:
                    self._select_and_scroll_to_item(parent, item)
                    return

    def _iter_tree_items(self, parent: QTreeWidgetItem) -> Generator[QTreeWidgetItem, None, None]:
        if hasattr(parent, "childCount"):
            for i in range(parent.childCount()):
                if item := parent.child(i):
                    yield item
        else:
            for i in range(parent.topLevelItemCount()):
                if item := parent.topLevelItem(i):
                    yield item

    def _select_and_scroll_to_item(self, parent: QTreeWidgetItem, item: QTreeWidgetItem):
        self.log.debug(f"Selecting ModuleResource: {item.data(0, Qt.UserRole).identifier()}")
        parent.setExpanded(True)
        item.setSelected(True)
        self.ui.resourceTree.scrollToItem(item)

    def rebuildInstanceList(self):
        if self._module is None:
            self._setInstanceListVisibility(False)
            return
        self._setInstanceListVisibility(True)

        git = self._module.git().resource()
        if git is None:
            raise ValueError(f"GIT resource missing from module '{self._module.root()}'.")

        items = self._createInstanceItems(git)
        for item in sorted(items, key=lambda i: i.data(Qt.UserRole + 1)):
            self.ui.instanceList.addItem(item)

    def _setInstanceListVisibility(self, visible: bool):
        self.ui.instanceList.setEnabled(visible)
        self.ui.instanceList.setVisible(visible)
        self.ui.instanceList.clear()

    def _createInstanceItems(self, git):
        items = []
        for instance in git.instances():
            if self._shouldHideInstance(instance):
                continue
            item = self._createInstanceItem(instance, git.index(instance))
            items.append(item)
        return items

    def _shouldHideInstance(self, instance):
        return {
            GITCreature: self.hideCreatures,
            GITPlaceable: self.hidePlaceables,
            GITDoor: self.hideDoors,
            GITTrigger: self.hideTriggers,
            GITEncounter: self.hideEncounters,
            GITWaypoint: self.hideWaypoints,
            GITSound: self.hideSounds,
            GITStore: self.hideStores,
            GITCamera: self.hideCameras,
        }.get(type(instance), False)

    def _createInstanceItem(self, instance, struct_index):
        item = QListWidgetItem(QIcon(self._getIconForInstance(instance)), "")
        self._setItemProperties(item, instance, struct_index)
        return item

    def _getIconForInstance(self, instance):
        return {
            GITCreature: ":/images/icons/k1/creature.png",
            GITPlaceable: ":/images/icons/k1/placeable.png",
            GITDoor: ":/images/icons/k1/door.png",
            GITSound: ":/images/icons/k1/sound.png",
            GITTrigger: ":/images/icons/k1/trigger.png",
            GITEncounter: ":/images/icons/k1/encounter.png",
            GITWaypoint: ":/images/icons/k1/waypoint.png",
            GITCamera: ":/images/icons/k1/camera.png",
            GITStore: ":/images/icons/k1/merchant.png",
        }.get(type(instance), QPixmap(32, 32))

    def _setItemProperties(self, item: QListWidgetItem, instance: GITInstance, struct_index: int):
        if isinstance(instance, GITCamera):
            self._setCameraItemProperties(item, instance, struct_index)
        else:
            self._setNonCameraItemProperties(item, instance, struct_index)
        item.setData(Qt.UserRole, instance)

    def _setCameraItemProperties(self, item: QListWidgetItem, instance: GITCamera, struct_index: int):
        item.setText(f"Camera #{instance.camera_id}")
        item.setToolTip(f"Struct Index: {struct_index}\nCamera ID: {instance.camera_id}\nFOV: {instance.fov}")
        item.setData(Qt.UserRole + 1, f"cam{instance.camera_id:010}")

    def _setNonCameraItemProperties(self, item: QListWidgetItem, instance: GITInstance, struct_index: int):
        this_ident = instance.identifier()
        resname = this_ident.resname
        name, tag = self._getNameAndTag(instance, resname)

        item.setText(name)
        item.setToolTip(f"Struct Index: {struct_index}\nResRef: {resname}\nName: {name}\nTag: {tag}")
        item.setData(Qt.UserRole + 1, f"{this_ident.restype.extension}{name}")

        if not self._module.resource(this_ident.resname, this_ident.restype).resource():
            font = item.font()
            font.setItalic(True)
            item.setFont(font)

    def _getNameAndTag(self, instance: GITInstance, resname: str) -> tuple[str, str]:
        module_resource = self._module.resource(instance.identifier().resname, instance.identifier().restype)
        if not module_resource:
            return resname, ""

        abstracted_resource = module_resource.resource()
        if not abstracted_resource:
            return resname, ""

        if isinstance(instance, (GITDoor, GITTrigger)):
            return module_resource.localized_name() or resname, instance.tag
        if isinstance(instance, GITWaypoint):
            return self._installation.string(instance.name), instance.tag
        return module_resource.localized_name() or resname, abstracted_resource.tag

    def selectInstanceItemOnList(self, instance: GITInstance):
        self.ui.instanceList.clearSelection()
        for i in range(self.ui.instanceList.count()):
            item = self.ui.instanceList.item(i)
            if item and item.data(Qt.UserRole) is instance:
                item.setSelected(True)
                self.ui.instanceList.scrollToItem(item)
                return
        self.log.warning(f"Instance not found in list: {instance}")

    def updateToggles(self):
        scene = self.ui.mainRenderer.scene
        assert scene is not None

        toggles = {
            "creatures": self.ui.viewCreatureCheck,
            "placeables": self.ui.viewPlaceableCheck,
            "doors": self.ui.viewDoorCheck,
            "triggers": self.ui.viewTriggerCheck,
            "encounters": self.ui.viewEncounterCheck,
            "waypoints": self.ui.viewWaypointCheck,
            "sounds": self.ui.viewSoundCheck,
            "stores": self.ui.viewStoreCheck,
            "cameras": self.ui.viewCameraCheck
        }

        for attr, check in toggles.items():
            visible = check.isChecked()
            setattr(self, f"hide{attr.capitalize()}", not visible)
            setattr(scene, f"hide_{attr}", not visible)
            setattr(self.ui.flatRenderer, f"hide{attr.capitalize()}", not visible)

        scene.backface_culling = self.ui.backfaceCheck.isChecked()
        scene.use_lightmap = self.ui.lightmapCheck.isChecked()
        scene.show_cursor = self.ui.cursorCheck.isChecked()

        self.rebuildInstanceList()

    def addInstance(self, instance: GITInstance, *, walkmeshSnap: bool = True):
        if walkmeshSnap:
            instance.position.z = self.ui.mainRenderer.walkmeshPoint(
                instance.position.x, instance.position.y, self.ui.mainRenderer.scene.camera.z
            ).z

        if isinstance(instance, GITCamera):
            self._module.git().resource().add(instance)
        else:
            self._addNonCameraInstance(instance)

        self.rebuildInstanceList()

    def _addNonCameraInstance(self, instance: GITInstance):
        dialog = self._showInsertInstanceDialog(instance)
        if not dialog:
            return

        self._updateInstanceFromDialog(instance, dialog)
        self._addInstanceToModule(instance)
        self._setupInstanceSpecifics(instance, dialog.data)

    def _showInsertInstanceDialog(self, instance: GITInstance) -> InsertInstanceDialog | None:
        dialog = InsertInstanceDialog(self, self._installation, self._module, instance.identifier().restype)
        return dialog if dialog.exec_() else None

    def _updateInstanceFromDialog(self, instance: GITInstance, dialog: InsertInstanceDialog):
        self.rebuildResourceTree()
        if hasattr(instance, "resref"):
            instance.resref = ResRef(dialog.resname)
        else:
            self.log.error(f"resref attr doesn't exist for {safe_repr(instance)}")

    def _addInstanceToModule(self, instance: GITInstance):
        self._module.git().resource().add(instance)

    def _setupInstanceSpecifics(self, instance: GITInstance, data: bytes):
        if isinstance(instance, GITWaypoint):
            utw = read_utw(data)
            instance.tag, instance.name = utw.tag, utw.name
        elif isinstance(instance, GITTrigger):
            instance.tag = read_utt(data).tag
            self._ensureGeometry(instance, "utt")
        elif isinstance(instance, GITEncounter):
            self._ensureGeometry(instance, "ute")
        elif isinstance(instance, GITDoor):
            instance.tag = read_utd(data).tag

    def _ensureGeometry(self, instance: Union[GITTrigger, GITEncounter], ext: str):
        if not instance.geometry:
            RobustLogger().info(f"Creating default triangle geometry for {instance.resref}.{ext}...")
            instance.geometry.create_triangle(origin=instance.position)

    def addInstanceAtCursor(self, instance: GITInstance):
        scene = self.ui.mainRenderer.scene
        assert scene is not None

        instance.position = Vector3(*scene.cursor.position())

        if isinstance(instance, GITCamera):
            self._addInstanceToModule(instance)
        else:
            dialog = self._showInsertInstanceDialog(instance)
            if dialog:
                self._updateInstanceFromDialog(instance, dialog)
                self._addInstanceToModule(instance)

        self._ensureGeometryIfNeeded(instance)
        self.rebuildInstanceList()

    def _ensureGeometryIfNeeded(self, instance: GITInstance):
        if isinstance(instance, (GITEncounter, GITTrigger)) and not instance.geometry:
            ext = "utt" if isinstance(instance, GITTrigger) else "ute"
            self._ensureGeometry(instance, ext)

    def editInstance(self, instance: GITInstance):
        if openInstanceDialog(self, instance, self._installation):
            if not isinstance(instance, GITCamera):
                self.ui.mainRenderer.scene.clearCacheBuffer.append(instance.identifier())
            self.rebuildInstanceList()

    def snapCameraToView(self, gitCameraInstance: GITCamera):
        viewCamera: Camera = self._getSceneCamera()
        new_position, new_orientation = self._calculateNewPositionAndOrientation(viewCamera, gitCameraInstance)
        self._updateCameraInstance(gitCameraInstance, new_position, new_orientation)

    def _calculateNewPositionAndOrientation(self, viewCamera: Camera, gitCameraInstance: GITCamera) -> tuple[Vector3, Vector4]:
        viewPosition: vec3 = viewCamera.true_position()
        new_position = Vector3(viewPosition.x, viewPosition.y, viewPosition.z - gitCameraInstance.height)

        pitch = math.pi - (viewCamera.pitch + (math.pi / 2))
        yaw = math.pi / 2 - viewCamera.yaw
        new_orientation = Vector4.from_euler(yaw, 0, pitch)

        return new_position, new_orientation

    def _updateCameraInstance(self, gitCameraInstance: GITCamera, new_position: Vector3, new_orientation: Vector4):
        self.undoStack.push(MoveCommand(gitCameraInstance, gitCameraInstance.position, new_position))
        gitCameraInstance.position = new_position
        self.undoStack.push(RotateCommand(gitCameraInstance, gitCameraInstance.orientation, new_orientation))
        gitCameraInstance.orientation = new_orientation

    def snapViewToGITCamera(self, gitCameraInstance: GITCamera):
        viewCamera: Camera = self._getSceneCamera()
        self._updateViewCamera(viewCamera, gitCameraInstance)

    def _updateViewCamera(self, viewCamera: Camera, gitCameraInstance: GITCamera):
        euler: Vector3 = gitCameraInstance.orientation.to_euler()
        viewCamera.pitch = math.pi - euler.z - math.radians(gitCameraInstance.pitch)
        viewCamera.yaw = math.pi / 2 - euler.x
        viewCamera.x, viewCamera.y, viewCamera.z = gitCameraInstance.position
        viewCamera.z += gitCameraInstance.height
        viewCamera.distance = 0

    def snapViewToGITInstance(self, gitInstance: GITInstance):
        camera: Camera = self._getSceneCamera()
        camera.yaw = gitInstance.yaw() or camera.yaw
        camera.x, camera.y, camera.z = gitInstance.position
        camera.z += 2
        camera.distance = 0

    def _getSceneCamera(self) -> Camera:
        scene = self.ui.mainRenderer.scene
        assert scene is not None
        return scene.camera

    def snapCameraToEntryLocation(self):
        scene = self.ui.mainRenderer.scene
        assert scene is not None
        scene.camera.x, scene.camera.y, scene.camera.z = self._module.ifo().resource()().entry_position

    def toggleFreeCam(self):
        if isinstance(self._controls3d, ModuleDesignerControls3d):
            self.log.info("Enabling ModuleDesigner free cam")
            self._controls3d = ModuleDesignerControlsFreeCam(self, self.ui.mainRenderer)
        else:
            self.log.info("Disabling ModuleDesigner free cam")
            self._controls3d = ModuleDesignerControls3d(self, self.ui.mainRenderer)

    # region Selection Manipulations
    def setSelection(self, instances: list[GITInstance]):
        if instances:
            self._updateSelectionWithInstances(instances)
        else:
            self._clearSelection()

    def _updateSelectionWithInstances(self, instances: list[GITInstance]):
        self.ui.mainRenderer.scene.select(instances[0])
        self.ui.flatRenderer.instanceSelection.select(instances)
        self.selectInstanceItemOnList(instances[0])
        self.selectResourceItem(instances[0])
        self.selectedInstances = instances

    def _clearSelection(self):
        self.ui.mainRenderer.scene.selection.clear()
        self.ui.flatRenderer.instanceSelection.clear()
        self.selectedInstances.clear()

    def deleteSelected(self, *, noUndoStack: bool = False):
        if not noUndoStack:
            self.undoStack.push(DeleteCommand(self._module.git().resource()(), self.selectedInstances.copy(), self))

        self._removeSelectedInstances()
        self._clearSelection()
        self.rebuildInstanceList()

    def _removeSelectedInstances(self):
        git_resource = self._module.git().resource()
        for instance in self.selectedInstances:
            git_resource.remove(instance)

    def moveSelected(self, x: float, y: float, z: float | None = None, *, noUndoStack: bool = False, noZCoord: bool = False):
        if self.ui.lockInstancesCheck.isChecked():
            return

        for instance in self.selectedInstances:
            self._moveInstance(instance, x, y, z, noUndoStack, noZCoord)

    def _moveInstance(self, instance: GITInstance, x: float, y: float, z: float | None, noUndoStack: bool, noZCoord: bool):
        self.log.debug("Moving %s", instance.resref)
        new_position = self._calculateNewPosition(instance, x, y, z, noZCoord)

        if not noUndoStack:
            self.undoStack.push(MoveCommand(instance, instance.position, new_position))

        instance.position = new_position

    def _calculateNewPosition(self, instance: GITInstance, x: float, y: float, z: float | None, noZCoord: bool) -> Vector3:
        new_x = instance.position.x + x
        new_y = instance.position.y + y

        if noZCoord:
            new_z = instance.position.z
        else:
            new_z = instance.position.z + (z or self.ui.mainRenderer.walkmeshPoint(instance.position.x, instance.position.y).z)

        return Vector3(new_x, new_y, new_z)

    def rotateSelected(self, x: float, y: float):
        if self.ui.lockInstancesCheck.isChecked():
            return

        for instance in self.selectedInstances:
            if isinstance(instance, (GITCamera, GITCreature, GITDoor, GITPlaceable, GITStore, GITWaypoint)):
                new_yaw = x / 60
                new_pitch = y / 60
                instance.rotate(new_yaw, new_pitch, 0.0)

    # endregion

    # region Signal Callbacks
    def _onSavedResource(self, resource: ModuleResource):
        resource.reload()
        self.ui.mainRenderer.scene.clearCacheBuffer.append(ResourceIdentifier(resource.resname(), resource.restype()))

    def handleUndoRedoFromLongActionFinished(self):
        # Check if we were dragging
        if self.isDragMoving:
            for instance, old_position in self.initialPositions.items():
                new_position = instance.position
                if old_position and new_position != old_position:
                    self.log.debug("Create the MoveCommand for undo/redo functionality")
                    move_command = MoveCommand(instance, old_position, new_position)
                    self.undoStack.push(move_command)
                elif not old_position:
                    self.log.debug("No old position for %s", instance.resref)
                else:
                    self.log.debug("Both old and new positions are the same %s", instance.resref)

            # Reset for the next drag operation
            self.initialPositions.clear()
            self.log.debug("No longer drag moving")
            self.isDragMoving = False

        if self.isDragRotating:
            for instance, old_rotation in self.initialRotations.items():
                new_rotation = instance.orientation if isinstance(instance, GITCamera) else instance.bearing
                if old_rotation and new_rotation != old_rotation:
                    self.log.debug("Create the RotateCommand for undo/redo functionality")
                    self.undoStack.push(RotateCommand(instance, old_rotation, new_rotation))
                elif not old_rotation:
                    self.log.debug("No old rotation for %s", instance.resref)
                else:
                    self.log.debug("Both old and new rotations are the same for %s", instance.resref)

            # Reset for the next drag operation
            self.initialRotations.clear()
            self.log.debug("No longer drag rotating")
            self.isDragRotating = False

    def onInstanceListSingleClicked(self):
        if self.ui.instanceList.selectedItems():
            instance = self.getGitInstanceFromHighlightedListItem()
            self.setSelection([instance])

    def onInstanceListDoubleClicked(self):
        if self.ui.instanceList.selectedItems():
            instance = self.getGitInstanceFromHighlightedListItem()
            self.setSelection([instance])
            self.ui.mainRenderer.snapCameraToPoint(instance.position)
            self.ui.flatRenderer.snapCameraToPoint(instance.position)

    def getGitInstanceFromHighlightedListItem(self) -> GITInstance:
        item: QListWidgetItem = self.ui.instanceList.selectedItems()[0]
        result: GITInstance = item.data(Qt.UserRole)
        return result

    def onInstanceVisibilityDoubleClick(self, checkbox: QCheckBox):
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

    def enterInstanceMode(self):
        self._controls2d._mode = _InstanceMode.__new__(_InstanceMode)
        # HACK:
        self._controls2d._mode.deleteSelected = self.deleteSelected
        self._controls2d._mode.editSelectedInstance = self.editInstance
        self._controls2d._mode.buildList = self.rebuildInstanceList
        self._controls2d._mode.updateVisibility = self.updateToggles
        self._controls2d._mode.selectUnderneath = lambda: self.setSelection(self.ui.flatRenderer.instancesUnderMouse())
        self._controls2d._mode.__init__(self, self._installation, self._module.git().resource()())
        # self._controls2d._mode.rotateSelectedToPoint = self.rotateSelected

    def enterGeometryMode(self):
        self._controls2d._mode = _GeometryMode(self, self._installation, self._module.git().resource()(), hideOthers=False)

    def enterSpawnMode(self):
        # TODO
        self._controls2d._mode = _SpawnMode(self, self._installation, self._module.git().resource()())

    def onResourceTreeContextMenu(self, point: QPoint):
        menu = QMenu(self)
        curItem = self.ui.resourceTree.currentItem()
        if curItem is None:
            return
        data = curItem.data(0, Qt.UserRole)
        if isinstance(data, ModuleResource):
            self._active_instance_location_menu(data, menu)
        menu.exec_(self.ui.resourceTree.mapToGlobal(point))

    def onResourceTreeDoubleClicked(self, point: QPoint):
        curItem = self.ui.resourceTree.currentItem()
        data = curItem.data(0, Qt.UserRole)
        if isinstance(data, ModuleResource):
            self.openModuleResource(data)

    def onResourceTreeSingleClicked(self, point: QPoint):
        curItem = self.ui.resourceTree.currentItem()
        data = curItem.data(0, Qt.UserRole)
        if isinstance(data, ModuleResource):
            self.jump_to_instance_list_action(data=data)

    def jump_to_instance_list_action(self, *args, data: ModuleResource, **kwargs):
        this_ident = data.identifier()
        instances = self._module.git().resource()().instances()
        for instance in instances:
            if instance.identifier() != this_ident:
                continue
            self.selectInstanceItemOnList(instance)
            return

    def _active_instance_location_menu(self, data: ModuleResource, menu: QMenu):
        copyToOverrideAction = QAction("Copy To Override", self)
        copyToOverrideAction.triggered.connect(lambda _=None, r=data: self.copyResourceToOverride(r))

        menu.addAction("Edit Active File").triggered.connect(lambda _=None, r=data: self.openModuleResource(r))
        menu.addAction("Reload Active File").triggered.connect(lambda _=None: data.reload())
        menu.addAction(copyToOverrideAction)
        menu.addSeparator()
        for location in data.locations():
            locationAction = QAction(str(location), self)
            locationAction.triggered.connect(lambda _=None, loc=location: self.activateResourceFile(data, loc))
            if location == data.active():
                locationAction.setEnabled(False)
            if location.is_relative_to(self._installation.override_path()):
                copyToOverrideAction.setEnabled(False)
            menu.addAction(locationAction)
        def jump_to_instance_list_action(*args, data=data, **kwargs):
            this_ident = data.identifier()
            instances = self._module.git().resource()().instances()
            for instance in instances:
                if instance.identifier() != this_ident:
                    continue
                #self.selectInstanceItemOnList(instance)
                self.setSelection([instance])
                return
        menu.addAction("Find in Instance List").triggered.connect(jump_to_instance_list_action)

    def on3dMouseMoved(self, screen: Vector2, screenDelta: Vector2, world: Vector3, buttons: set[int], keys: set[int]):
        self.updateStatusBar(screen, buttons, keys, self.ui.mainRenderer)
        self._controls3d.onMouseMoved(screen, screenDelta, world, buttons, keys)

    def on3dMouseScrolled(self, delta: Vector2, buttons: set[int], keys: set[int]):
        self.updateStatusBar(QCursor.pos(), buttons, keys, self.ui.mainRenderer)
        self._controls3d.onMouseScrolled(delta, buttons, keys)

    def on3dMousePressed(self, screen: Vector2, buttons: set[int], keys: set[int]):
        self.updateStatusBar(screen, buttons, keys, self.ui.mainRenderer)
        self._controls3d.onMousePressed(screen, buttons, keys)

    def doCursorLock(self, mutableScreen: Vector2, *, centerMouse: bool = True, doRotations: bool = True):
        global_new_pos = QCursor.pos()
        global_old_pos = self.ui.mainRenderer.mapToGlobal(
            self.ui.mainRenderer.rect().center() if centerMouse
            else QPoint(int(self.ui.mainRenderer._mousePrev.x), int(self.ui.mainRenderer._mousePrev.y))  # noqa: SLF001
        )
        QCursor.setPos(global_old_pos)

        if not centerMouse:
            local_old_pos = self.ui.mainRenderer.mapFromGlobal(global_old_pos)
            mutableScreen.x, mutableScreen.y = local_old_pos.x(), local_old_pos.y()

        if doRotations:
            is_free_cam = isinstance(self._controls3d, ModuleDesignerControlsFreeCam)
            strength = (self.settings.rotateCameraSensitivityFC if is_free_cam else self.settings.rotateCameraSensitivity3d) / 10000
            delta = global_old_pos - global_new_pos
            self.ui.mainRenderer.rotateCamera(delta.x() * strength, -delta.y() * strength, clampRotations=not is_free_cam)

    def on3dMouseReleased(self, screen: Vector2, buttons: set[int], keys: set[int]):
        self.updateStatusBar(screen, buttons, keys, self.ui.mainRenderer)
        self._controls3d.onMouseReleased(screen, buttons, keys)

    def on3dKeyboardReleased(self, buttons: set[int], keys: set[int]):
        self.updateStatusBar(QCursor.pos(), buttons, keys, self.ui.mainRenderer)
        self._controls3d.onKeyboardReleased(buttons, keys)

    def on3dKeyboardPressed(self, buttons: set[int], keys: set[int]):
        self.updateStatusBar(QCursor.pos(), buttons, keys, self.ui.mainRenderer)
        self._controls3d.onKeyboardPressed(buttons, keys)

    def on3dObjectSelected(self, instance: GITInstance | None):
        if isinstance(instance, GITCamera):
            self.setSelection([instance])
        else:
            self.setSelection([])

    def onContextMenu(self, world: Vector3, point: QPoint, *, isFlatRendererCall: bool | None = None):  # noqa: N803
        self.log.debug(f"onContextMenu(world={world}, point={point}, isFlatRendererCall={isFlatRendererCall})")
        if self._module is None:
            self.log.warning("onContextMenu No module.")
            return

        if len(self.ui.mainRenderer.scene.selection) == 0:
            self.log.debug("onContextMenu No selection")
            menu = self.buildInsertInstanceMenu(world)
        else:
            menu = self.onContextMenuSelectionExists(world, isFlatRendererCall=isFlatRendererCall, getMenu=True)

        self.showFinalContextMenu(menu)

    def buildInsertInstanceMenu(self, world: Vector3) -> QMenu:
        menu = QMenu(self)

        rot = self.ui.mainRenderer.scene.camera
        menu.addAction("Insert Camera").triggered.connect(lambda: self.addInstance(GITCamera(*world), walkmeshSnap=False))  # pyright: ignore[reportArgumentType]
        menu.addAction("Insert Camera at View").triggered.connect(lambda: self.addInstance(GITCamera(rot.x, rot.y, rot.z, rot.yaw, rot.pitch, 0, 0), walkmeshSnap=False))
        menu.addSeparator()
        menu.addAction("Insert Creature").triggered.connect(lambda: self.addInstance(GITCreature(*world), walkmeshSnap=True))
        menu.addAction("Insert Door").triggered.connect(lambda: self.addInstance(GITDoor(*world), walkmeshSnap=False))
        menu.addAction("Insert Placeable").triggered.connect(lambda: self.addInstance(GITPlaceable(*world), walkmeshSnap=False))
        menu.addAction("Insert Store").triggered.connect(lambda: self.addInstance(GITStore(*world), walkmeshSnap=False))
        menu.addAction("Insert Sound").triggered.connect(lambda: self.addInstance(GITSound(*world), walkmeshSnap=False))
        menu.addAction("Insert Waypoint").triggered.connect(lambda: self.addInstance(GITWaypoint(*world), walkmeshSnap=False))
        menu.addAction("Insert Encounter").triggered.connect(lambda: self.addInstance(GITEncounter(*world), walkmeshSnap=False))
        menu.addAction("Insert Trigger").triggered.connect(lambda: self.addInstance(GITTrigger(*world), walkmeshSnap=False))
        return menu

    def onInstanceListRightClicked(self, point: QPoint):
        instance: GITInstance = self.ui.instanceList.selectedItems()[0].data(Qt.UserRole)
        self.onContextMenuSelectionExists(world=instance.position)

    def onContextMenuSelectionExists(self, world: Vector3 | None = None, *, isFlatRendererCall: bool | None = None, getMenu: bool | None = None, instances: Sequence[GITInstance] | None = None) -> QMenu | None:    # sourcery skip: extract-method
        menu = QMenu(self)
        instances = self.selectedInstances if instances is None else instances

        if instances:
            instance = instances[0]
            if isinstance(instance, GITCamera):
                menu.addAction("Snap GIT-cam to 3D View").triggered.connect(lambda: self.snapCameraToView(instance))
                menu.addAction("Snap 3D View to GIT-cam").triggered.connect(lambda: self.snapViewToGITCamera(instance))
            else:
                menu.addAction("Snap 3D View to Instance Position").triggered.connect(lambda: self.snapViewToGITInstance(instance))
            menu.addSeparator()
            menu.addAction("Copy position to clipboard").triggered.connect(lambda: QApplication.clipboard().setText(str(instance.position)))
            menu.addAction("Edit Instance").triggered.connect(lambda: self.editInstance(instance))
            menu.addAction("Remove").triggered.connect(self.deleteSelected)
            menu.addSeparator()
            if world is not None:
                self._controls2d._mode._getRenderContextMenu(Vector2(world.x, world.y), menu)
        if not getMenu:
            self.showFinalContextMenu(menu)
            return None
        return menu

    def showFinalContextMenu(self, menu: QMenu):
        menu.popup(self.cursor().pos())
        menu.aboutToHide.connect(self.ui.mainRenderer.resetAllDown)
        menu.aboutToHide.connect(self.ui.flatRenderer.resetAllDown)

    def on3dRendererInitialized(self):
        self.show()
        self.activateWindow()

    def on3dSceneInitialized(self):
        self.rebuildResourceTree()
        self.rebuildInstanceList()
        self._refreshWindowTitle()
        self.enterInstanceMode()
        self.show()
        self.activateWindow()

    def on2dMouseMoved(self, screen: Vector2, delta: Vector2, buttons: set[int], keys: set[int]):
        worldDelta: Vector2 = self.ui.flatRenderer.toWorldDelta(delta.x, delta.y)
        world: Vector3 = self.ui.flatRenderer.toWorldCoords(screen.x, screen.y)
        self._controls2d.onMouseMoved(screen, delta, Vector2.from_vector3(world), worldDelta, buttons, keys)
        self.updateStatusBar(QCursor.pos(), buttons, keys, self.ui.flatRenderer)

    def on2dMouseReleased(self, screen: Vector2, buttons: set[int], keys: set[int]):
        self._controls2d.onMouseReleased(screen, buttons, keys)
        self.updateStatusBar(QCursor.pos(), buttons, keys, self.ui.flatRenderer)

    def on2dKeyboardPressed(self, buttons: set[int], keys: set[int]):
        self._controls2d.onKeyboardPressed(buttons, keys)
        self.updateStatusBar(QCursor.pos(), buttons, keys, self.ui.flatRenderer)

    def on2dKeyboardReleased(self, buttons: set[int], keys: set[int]):
        self._controls2d.onKeyboardReleased(buttons, keys)
        self.updateStatusBar(QCursor.pos(), buttons, keys, self.ui.flatRenderer)

    def on2dMouseScrolled(self, delta: Vector2, buttons: set[int], keys: set[int]):
        self.updateStatusBar(QCursor.pos(), buttons, keys, self.ui.flatRenderer)
        self._controls2d.onMouseScrolled(delta, buttons, keys)

    def on2dMousePressed(self, screen: Vector2, buttons: set[int], keys: set[int]):
        self._controls2d.onMousePressed(screen, buttons, keys)
        self.updateStatusBar(screen, buttons, keys, self.ui.flatRenderer)

    # endregion

    # region Events
    def keyPressEvent(self, e: QKeyEvent | None, bubble: bool = True):  # noqa: FBT001, FBT002
        if e is None:
            return
        super().keyPressEvent(e)
        self.ui.mainRenderer.keyPressEvent(e)
        self.ui.flatRenderer.keyPressEvent(e)

    def keyReleaseEvent(self, e: QKeyEvent | None, bubble: bool = True):  # noqa: FBT001, FBT002
        if e is None:
            return
        super().keyReleaseEvent(e)
        self.ui.mainRenderer.keyReleaseEvent(e)
        self.ui.flatRenderer.keyReleaseEvent(e)

    # endregion

    def update_camera(self):
        mainRenderer = self.ui.mainRenderer
        if not mainRenderer.underMouse():
            return

        keys = mainRenderer.keysDown()
        buttons = mainRenderer.mouseDown()
        timeDelta = time.time() - self.lastFrameTime
        self.lastFrameTime += timeDelta
        is_3d_cam = isinstance(self._controls3d, ModuleDesignerControls3d)

        angleDelta = self.settings.rotateCameraSensitivity3d * self.baseFrameRate * timeDelta * math.pi / 4000
        is_free_cam = isinstance(self._controls3d, ModuleDesignerControlsFreeCam)
        is_boosted = self._controls3d.speedBoostControl.satisfied(buttons, keys, exactKeysAndButtons=False)

        speeds = {
            (True, True): self.settings.boostedFlyCameraSpeedFC,
            (True, False): self.settings.flyCameraSpeedFC,
            (False, True): self.settings.boostedMoveCameraSensitivity3d,
            (False, False): self.settings.moveCameraSensitivity3d
        }
        moveDelta = speeds[(is_free_cam, is_boosted)]
        moveDelta *= timeDelta * self.baseFrameRate / 500

        actions: list[tuple[ControlItem, Callable[[], None]]] = [
            (self._controls3d.rotateCameraLeft, lambda: mainRenderer.rotateCamera(angleDelta, 0)),
            (self._controls3d.rotateCameraRight, lambda: mainRenderer.rotateCamera(-angleDelta, 0)),
            (self._controls3d.rotateCameraUp, lambda: mainRenderer.rotateCamera(0, angleDelta)),
            (self._controls3d.rotateCameraDown, lambda: mainRenderer.rotateCamera(0, -angleDelta)),
            (self._controls3d.zoomCameraIn, lambda: mainRenderer.zoomCamera(moveDelta)),
            (self._controls3d.zoomCameraOut, lambda: mainRenderer.zoomCamera(-moveDelta)),
            (self._controls3d.moveCameraUp, lambda: mainRenderer.moveCamera(0, 0, moveDelta) if is_3d_cam else mainRenderer.scene.camera.translate(vec3(0, 0, moveDelta))),
            (self._controls3d.moveCameraDown, lambda: mainRenderer.moveCamera(0, 0, -moveDelta) if is_3d_cam else mainRenderer.scene.camera.translate(vec3(0, 0, -moveDelta))),
            (self._controls3d.moveCameraLeft, lambda: mainRenderer.moveCamera(0, -moveDelta, 0) if is_3d_cam else mainRenderer.panCamera(0, -moveDelta, 0)),
            (self._controls3d.moveCameraRight, lambda: mainRenderer.moveCamera(0, moveDelta, 0) if is_3d_cam else mainRenderer.panCamera(0, moveDelta, 0)),
            (self._controls3d.moveCameraForward, lambda: mainRenderer.moveCamera(moveDelta, 0, 0) if is_3d_cam else mainRenderer.panCamera(moveDelta, 0, 0)),
            (self._controls3d.moveCameraBackward, lambda: mainRenderer.panCamera(-moveDelta, 0, 0) if is_3d_cam else mainRenderer.moveCamera(-moveDelta, 0, 0)),
        ]

        for key, action in actions:
            if key.satisfied(buttons, keys):
                action()
