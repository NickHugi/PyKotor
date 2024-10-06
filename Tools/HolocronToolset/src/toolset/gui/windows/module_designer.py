from __future__ import annotations

import math
import time

from typing import TYPE_CHECKING, Any, Callable, Sequence

import qtpy

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy import QtCore
from qtpy.QtCore import QPoint, QTimer
from qtpy.QtGui import QColor, QCursor, QIcon, QPixmap
from qtpy.QtWidgets import (
    QAction,
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
from pykotor.common.stream import BinaryWriter
from pykotor.extract.file import ResourceIdentifier
from pykotor.gl.scene import Camera
from pykotor.resource.generics.git import (
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
)
from pykotor.resource.generics.utd import read_utd
from pykotor.resource.generics.utt import read_utt
from pykotor.resource.generics.utw import read_utw
from pykotor.resource.type import ResourceType
from pykotor.tools import module
from pykotor.tools.misc import is_mod_file
from toolset.gui.dialogs.asyncloader import AsyncLoader
from toolset.gui.dialogs.insert_instance import InsertInstanceDialog
from toolset.gui.dialogs.select_module import SelectModuleDialog
from toolset.gui.editor import Editor
from toolset.gui.editors.git import (
    DeleteCommand,
    MoveCommand,
    RotateCommand,
    _GeometryMode,
    _InstanceMode,
    _SpawnMode,
    openInstanceDialog,
)
from toolset.gui.widgets.renderer.module import ModuleRenderer
from toolset.gui.widgets.settings.module_designer import ModuleDesignerSettings
from toolset.gui.windows.designer_controls import (
    ModuleDesignerControls2d,
    ModuleDesignerControls3d,
    ModuleDesignerControlsFreeCam,
)
from toolset.gui.windows.help import HelpWindow
from toolset.utils.misc import MODIFIER_KEY_NAMES, getQtButtonString, getQtKeyString
from toolset.utils.window import open_resource_editor
from utility.error_handling import safe_repr
from utility.misc import is_debug_mode

if TYPE_CHECKING:
    import os

    from pathlib import Path

    from glm import vec3
    from qtpy.QtGui import QCloseEvent, QFont, QKeyEvent, QShowEvent
    from qtpy.QtWidgets import QCheckBox
    from typing_extensions import Literal

    from pykotor.gl.scene import Camera
    from pykotor.resource.formats.bwm.bwm_data import BWM
    from pykotor.resource.generics.are import ARE
    from pykotor.resource.generics.git import GIT
    from pykotor.resource.generics.ifo import IFO
    from pykotor.tools.path import CaseAwarePath
    from toolset.data.installation import HTInstallation
    from toolset.gui.widgets.renderer.walkmesh import WalkmeshRenderer
    from toolset.utils.misc import QtKey, QtMouse

if qtpy.API_NAME in ("PyQt5", "PySide2"):
    from qtpy.QtWidgets import QUndoStack
elif qtpy.API_NAME in ("PyQt6", "PySide6"):
    from qtpy.QtGui import QUndoStack
else:
    raise ValueError(f"Invalid QT_API: '{qtpy.API_NAME}'")


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
        self._origFilepath: Path | None = mod_filepath

        self.initialPositions: dict[GITInstance, Vector3] = {}
        self.initialRotations: dict[GITCamera | GITCreature | GITDoor | GITPlaceable | GITStore | GITWaypoint, Vector4 | float] = {}
        self.undoStack: QUndoStack = QUndoStack(self)

        self.selectedInstances: list[GITInstance] = []
        self.settings: ModuleDesignerSettings = ModuleDesignerSettings()
        self.log: RobustLogger = RobustLogger()

        self.baseFrameRate = 60
        self.cameraUpdateTimer = QTimer()
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
            from toolset.uic.pyside2.windows.module_designer import (
                Ui_MainWindow,  # noqa: PLC0415  # pylint: disable=C0415
            )
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.windows.module_designer import (
                Ui_MainWindow,  # noqa: PLC0415  # pylint: disable=C0415
            )
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.windows.module_designer import (
                Ui_MainWindow,  # noqa: PLC0415  # pylint: disable=C0415
            )
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.windows.module_designer import (
                Ui_MainWindow,  # noqa: PLC0415  # pylint: disable=C0415
            )
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui: Ui_MainWindow = Ui_MainWindow()
        self.ui.setupUi(self)
        self._initUi()
        self._setupSignals()
        self.last_free_cam_time: float = 0.0  # Initialize the last toggle time

        def intColorToQColor(intvalue: int) -> QColor:
            """Converts an integer color value to a QColor object.

            Args:
            ----
                intvalue: Integer color value.

            Returns:
            -------
                QColor: QColor object representing the color

            Processing Logic:
            ----------------
                - Extract RGBA components from integer color value using Color.from_rgba_integer()
                - Multiply each component by 255 to convert to QColor expected value range of 0-255
                - Pass converted values to QColor constructor to return QColor object.
            """
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

    def _setupSignals(self):
        """Connect signals to slots.

        Args:
        ----
            self: {The class instance}: Connects signals from UI elements to methods

        Processing Logic:
        ----------------
            - Connect menu actions to methods like open, save
            - Connect toggles of instance visibility checks to update method
            - Connect double clicks on checks and instance list to methods
            - Connect 3D renderer signals to mouse, key methods
            - Connect 2D renderer signals to mouse, key methods.
        """
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

        self.customStatusBarContainer = QWidget()
        self.customStatusBarLayout = QVBoxLayout()

        # Create labels for the status bar
        self.mousePosLabel = QLabel("Mouse Coords: ")
        self.buttonsKeysPressedLabel = QLabel("Keys/Buttons: ")
        self.selectedInstanceLabel = QLabel("Selected Instance: ")
        self.viewCameraLabel = QLabel("View: ")

        # Create a horizontal layout for the first row
        firstRow = QHBoxLayout()

        # Add widgets to the first row layout with appropriate stretching
        firstRow.addWidget(self.mousePosLabel, 1)  # Stretch factor 1 for left alignment
        firstRow.addStretch(1)  # Adds stretch in the middle to push the labels to sides and center
        firstRow.addWidget(self.selectedInstanceLabel, 2)  # Stretch factor 2 for center alignment
        firstRow.addStretch(1)  # Additional stretch for better spacing
        firstRow.addWidget(self.buttonsKeysPressedLabel, 1)  # Stretch factor 1 for right alignment

        # Add the first row layout and the camera info label to the main layout
        self.customStatusBarLayout.addLayout(firstRow)
        self.customStatusBarLayout.addWidget(self.viewCameraLabel)

        self.customStatusBarContainer.setLayout(self.customStatusBarLayout)
        self.customStatusBar.addPermanentWidget(self.customStatusBarContainer)

    def updateStatusBar(self, mousePos: QPoint | Vector2, buttons: set[int], keys: set[int], renderer: WalkmeshRenderer | ModuleRenderer):
        normMousePos = Vector2(mousePos.x(), mousePos.y()) if isinstance(mousePos, QPoint) else mousePos
        worldPos3d = None

        if isinstance(renderer, ModuleRenderer):
            pos = renderer.scene.cursor.position()
            worldPos3d = Vector3(pos.x, pos.y, pos.z)
            self.mousePosLabel.setText(f"Mouse Coords: {worldPos3d.y:.2f}, {worldPos3d.z:.2f}")
            camera = renderer.scene.camera
            self.viewCameraLabel.setText(f"View: Pos ({camera.x:.2f}, {camera.y:.2f}, {camera.z:.2f}), Pitch: {camera.pitch:.2f}, Yaw: {camera.yaw:.2f}, FOV: {camera.fov:.2f}")
        else:
            worldPos = renderer.toWorldCoords(normMousePos.x, normMousePos.y)
            self.mousePosLabel.setText(f"Mouse Coords: {worldPos.y:.2f}")

        def sort_with_modifiers(items: set[int], get_string_func: Callable[[Any], str], qtEnumType: Literal["QtKey", "QtMouse"]) -> Sequence[QtKey | QtMouse | int]:
            modifiers = [item for item in items if item in MODIFIER_KEY_NAMES] if qtEnumType == "QtKey" else []
            normal = [item for item in items if item not in MODIFIER_KEY_NAMES] if qtEnumType == "QtKey" else list(items)
            return sorted(modifiers, key=get_string_func) + sorted(normal, key=get_string_func)

        sorted_buttons = sort_with_modifiers(buttons, getQtButtonString, "QtMouse")
        sorted_keys = sort_with_modifiers(keys, getQtKeyString, "QtKey")

        self.buttonsKeysPressedLabel.setText(f"Keys/Buttons: {'+'.join(map(getQtKeyString, sorted_keys))} {'+'.join(map(getQtButtonString, sorted_buttons))}")

        instance = self.selectedInstances[0] if self.selectedInstances else None
        self.selectedInstanceLabel.setText(f"Selected Instance: {repr(instance) if isinstance(instance, GITCamera) else instance.identifier() if instance else 'None'}")

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

    #    @with_variable_trace(Exception)
    def openModule(self, mod_filepath: Path):
        """Opens a module."""
        mod_root = self._installation.get_module_root(mod_filepath)
        mod_filepath = self._ensure_mod_file(mod_filepath, mod_root)

        def task() -> tuple[Module, GIT, list[BWM]]:
            combined_module = Module(mod_root, self._installation, use_dot_mod=is_mod_file(mod_filepath))
            git = combined_module.git().resource()
            if not git:
                raise ValueError(f"This module '{mod_root}' is missing a GIT!")

            walkmeshes = [
                bwm.resource() for bwm in combined_module.resources.values()
                if bwm.restype() is ResourceType.WOK and bwm.resource() is not None
            ]
            return (combined_module, git, walkmeshes)

        self.unloadModule()
        result = task() if is_debug_mode() else self._load_async(mod_filepath, task)
        if not result:
            return

        new_module, git, walkmeshes = result
        self._module = new_module
        self.ui.flatRenderer.setGit(git)
        self.ui.mainRenderer.initializeRenderer(self._installation, new_module)
        self.ui.mainRenderer.scene.show_cursor = self.ui.cursorCheck.isChecked()
        self.ui.flatRenderer.setWalkmeshes(walkmeshes)
        self.ui.flatRenderer.centerCamera()
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
                f"You've chosen '{orig_filepath.name}' with a '{orig_filepath.suffix}' extension. The Module Designer recommends modifying .mod's.<br><br>Use '{mod_filepath.name}' instead?",
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
        return loader.value if loader.exec_() else None

    def unloadModule(self):
        self._module = None
        self.ui.mainRenderer.shutdownRenderer()

    def showHelpWindow(self):
        window = HelpWindow(self, "./help/tools/1-moduleEditor.md")
        window.show()

    def git(self) -> GIT:
        return self._module.git().resource()

    def are(self) -> ARE:
        return self._module.are().resource()

    def ifo(self) -> IFO:
        return self._module.info().resource()

    def saveGit(self):
        self._module.git().save()

    def rebuildResourceTree(self):
        """Rebuilds the resource tree widget.

        Args:
        ----
            self: The class instance

        Rebuilds the resource tree widget by:
            - Clearing existing items
            - Enabling the tree
            - Grouping resources by type into categories
            - Adding category items and resource items
            - Sorting items alphabetically.
        """
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
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, resource)
            category = categories.get(resource.restype(), categories[ResourceType.INVALID])
            category.addChild(item)

        self.ui.resourceTree.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder)
        self.ui.resourceTree.setSortingEnabled(True)

    def openModuleResource(self, resource: ModuleResource):
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
            ).exec_()
        elif isinstance(editor, Editor):
            editor.savedFile.connect(lambda: self._onSavedResource(resource))

    def copyResourceToOverride(self, resource: ModuleResource):
        location: CaseAwarePath = self._installation.override_path() / f"{resource.identifier()}"
        data = resource.data()
        if data is None:
            RobustLogger().error(f"Cannot find resource {resource.identifier()} anywhere to copy to Override. Locations: {resource.locations()}")
            return
        BinaryWriter.dump(location, data)
        resource.add_locations([location])
        resource.activate(location)
        self.ui.mainRenderer.scene.clearCacheBuffer.append(resource.identifier())

    def activateResourceFile(
        self,
        resource: ModuleResource,
        location: os.PathLike | str,
    ):
        resource.activate(location)
        self.ui.mainRenderer.scene.clearCacheBuffer.append(resource.identifier())

    def selectResourceItem(
        self,
        instance: GITInstance,
        *,
        clearExisting: bool = True,
    ):
        """Select a resource item in the tree.

        Args:
        ----
            instance: {The GIT instance to select}
            clearExisting: {Clear existing selections if True}.
        """
        if clearExisting:
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
                res: ModuleResource = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
                if not isinstance(res, ModuleResource):
                    self.log.warning("item.data(0, QtCore.Qt.ItemDataRole.UserRole) returned non ModuleResource in ModuleDesigner.selectResourceItem(): %s", safe_repr(res))
                    continue
                if res.identifier() != this_ident:
                    continue
                self.log.debug("Selecting ModuleResource in selectResourceItem loop: %s", res.identifier())
                parent.setExpanded(True)
                item.setSelected(True)
                self.ui.resourceTree.scrollToItem(item)

    def rebuildInstanceList(self):
        """Rebuilds the instance list.

        Args:
        ----
            self: The class instance
        """
        self.log.debug("rebuildInstanceList called.")
        self.ui.instanceList.clear()

        # Only build if module is loaded
        if self._module is None:
            self.ui.instanceList.setEnabled(False)
            self.ui.instanceList.setVisible(False)
            return

        self.ui.instanceList.setEnabled(True)
        self.ui.instanceList.setVisible(True)

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
            if visibleMapping[instance.__class__]:
                continue

            struct_index: int = git.index(instance)

            icon = QIcon(iconMapping[instance.__class__])
            item = QListWidgetItem(icon, "")
            font: QFont = item.font()

            if isinstance(instance, GITCamera):
                item.setText(f"Camera #{instance.camera_id}")
                item.setToolTip(f"Struct Index: {struct_index}\nCamera ID: {instance.camera_id}\nFOV: {instance.fov}")
                item.setData(QtCore.Qt.ItemDataRole.UserRole + 1, "cam" + str(instance.camera_id).rjust(10, "0"))
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
                item.setData(QtCore.Qt.ItemDataRole.UserRole + 1, instance.identifier().restype.extension + name)

            item.setFont(font)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, instance)
            items.append(item)

        for item in sorted(items, key=lambda i: i.data(QtCore.Qt.ItemDataRole.UserRole + 1)):
            self.ui.instanceList.addItem(item)

    def selectInstanceItemOnList(self, instance: GITInstance):
        """Select an instance item on the instance list.

        Args:
        ----
            instance (GITInstance): The instance to select
        """
        self.ui.instanceList.clearSelection()
        for i in range(self.ui.instanceList.count()):
            item: QListWidgetItem | None = self.ui.instanceList.item(i)
            if item is None:
                self.log.warning("item was somehow None at index %s in selectInstanceItemOnList", i)
                continue
            data: GITInstance = item.data(QtCore.Qt.ItemDataRole.UserRole)
            if data is instance:
                item.setSelected(True)
                self.ui.instanceList.scrollToItem(item)

    def updateToggles(self):
        scene = self.ui.mainRenderer.scene
        assert scene is not None

        self.hideCreatures = scene.hide_creatures = self.ui.flatRenderer.hideCreatures = not self.ui.viewCreatureCheck.isChecked()
        self.hidePlaceables = scene.hide_placeables = self.ui.flatRenderer.hidePlaceables = not self.ui.viewPlaceableCheck.isChecked()
        self.hideDoors = scene.hide_doors = self.ui.flatRenderer.hideDoors = not self.ui.viewDoorCheck.isChecked()
        self.hideTriggers = scene.hide_triggers = self.ui.flatRenderer.hideTriggers = not self.ui.viewTriggerCheck.isChecked()
        self.hideEncounters = scene.hide_encounters = self.ui.flatRenderer.hideEncounters = not self.ui.viewEncounterCheck.isChecked()
        self.hideWaypoints = scene.hide_waypoints = self.ui.flatRenderer.hideWaypoints = not self.ui.viewWaypointCheck.isChecked()
        self.hideSounds = scene.hide_sounds = self.ui.flatRenderer.hideSounds = not self.ui.viewSoundCheck.isChecked()
        self.hideStores = scene.hide_stores = self.ui.flatRenderer.hideStores = not self.ui.viewStoreCheck.isChecked()
        self.hideCameras = scene.hide_cameras = self.ui.flatRenderer.hideCameras = not self.ui.viewCameraCheck.isChecked()

        scene.backface_culling = self.ui.backfaceCheck.isChecked()
        scene.use_lightmap = self.ui.lightmapCheck.isChecked()
        scene.show_cursor = self.ui.cursorCheck.isChecked()

        self.rebuildInstanceList()

    #    @with_variable_trace(Exception)
    def addInstance(
        self,
        instance: GITInstance,
        *,
        walkmeshSnap: bool = True,
    ):
        """Adds a GIT instance to the editor.

        Args:
        ----
            instance: {The instance to add}
            walkmeshSnap (optional): {Whether to snap the instance to the walkmesh}.
        """
        if walkmeshSnap:
            instance.position.z = self.ui.mainRenderer.walkmeshPoint(
                instance.position.x,
                instance.position.y,
                self.ui.mainRenderer.scene.camera.z,
            ).z

        if not isinstance(instance, GITCamera):
            assert self._module is not None
            dialog = InsertInstanceDialog(self, self._installation, self._module, instance.identifier().restype)

            if dialog.exec_():
                self.rebuildResourceTree()
                if not hasattr(instance, "resref"):
                    self.log.error("resref attr doesn't exist for %s", safe_repr(instance))
                    return
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
        self.rebuildInstanceList()

    #    @with_variable_trace()
    def addInstanceAtCursor(self, instance: GITInstance):
        """Adds instance at cursor position.

        Args:
        ----
            instance (GITInstance): Instance to add
        """
        scene = self.ui.mainRenderer.scene
        assert scene is not None

        instance.position.x = scene.cursor.position().x
        instance.position.y = scene.cursor.position().y
        instance.position.z = scene.cursor.position().z

        if not isinstance(instance, GITCamera):
            assert self._module is not None
            dialog = InsertInstanceDialog(self, self._installation, self._module, instance.identifier().restype)

            if dialog.exec_():
                self.rebuildResourceTree()
                instance.resref = ResRef(dialog.resname)  # pyright: ignore[reportAttributeAccessIssue]
                self._module.git().resource().add(instance)
        else:
            if isinstance(instance, (GITEncounter, GITTrigger)) and not instance.geometry:
                self.log.info("Creating default triangle geometry for %s.%s", instance.resref, "utt" if isinstance(instance, GITTrigger) else "ute")
                instance.geometry.create_triangle(origin=instance.position)
            self._module.git().resource().add(instance)
        self.rebuildInstanceList()

    #    @with_variable_trace()
    def editInstance(self, instance: GITInstance):
        if openInstanceDialog(self, instance, self._installation):
            if not isinstance(instance, GITCamera):
                ident = instance.identifier()
                self.ui.mainRenderer.scene.clearCacheBuffer.append(ident)
            self.rebuildInstanceList()

    def snapCameraToView(self, gitCameraInstance: GITCamera):
        viewCamera: Camera = self._getSceneCamera()
        viewPosition: vec3 = viewCamera.true_position()

        new_position = Vector3(viewPosition.x, viewPosition.y, viewPosition.z - gitCameraInstance.height)
        self.undoStack.push(MoveCommand(gitCameraInstance, gitCameraInstance.position, new_position))
        gitCameraInstance.position = new_position

        self.log.debug("Create RotateCommand for undo/redo functionality")
        pitch = math.pi - (viewCamera.pitch + (math.pi / 2))
        yaw = math.pi / 2 - viewCamera.yaw
        new_orientation = Vector4.from_euler(yaw, 0, pitch)
        self.undoStack.push(RotateCommand(gitCameraInstance, gitCameraInstance.orientation, new_orientation))
        gitCameraInstance.orientation = new_orientation

    def snapViewToGITCamera(self, gitCameraInstance: GITCamera):
        viewCamera: Camera = self._getSceneCamera()
        euler: Vector3 = gitCameraInstance.orientation.to_euler()
        viewCamera.pitch = math.pi - euler.z - math.radians(gitCameraInstance.pitch)
        viewCamera.yaw = math.pi / 2 - euler.x
        viewCamera.x = gitCameraInstance.position.x
        viewCamera.y = gitCameraInstance.position.y
        viewCamera.z = gitCameraInstance.position.z + gitCameraInstance.height
        viewCamera.distance = 0

    def snapViewToGITInstance(self, gitInstance: GITInstance):
        camera: Camera = self._getSceneCamera()
        yaw = gitInstance.yaw()
        camera.yaw = camera.yaw if yaw is None else yaw
        camera.x, camera.y, camera.z = gitInstance.position
        camera.y = gitInstance.position.y
        camera.z = gitInstance.position.z + 2
        camera.distance = 0

    def _getSceneCamera(self) -> Camera:
        scene = self.ui.mainRenderer.scene
        assert scene is not None
        result: Camera = scene.camera
        return result

    def snapCameraToEntryLocation(self):
        scene = self.ui.mainRenderer.scene
        assert scene is not None

        scene.camera.x = self.ifo().entry_position.x
        scene.camera.y = self.ifo().entry_position.y
        scene.camera.z = self.ifo().entry_position.z

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
            self.ui.mainRenderer.scene.select(instances[0])
            self.ui.flatRenderer.instanceSelection.select(instances)
            self.selectInstanceItemOnList(instances[0])
            self.selectResourceItem(instances[0])
            self.selectedInstances = instances
        else:
            self.ui.mainRenderer.scene.selection.clear()
            self.ui.flatRenderer.instanceSelection.clear()
            self.selectedInstances.clear()

    def deleteSelected(self, *, noUndoStack: bool = False):
        if not noUndoStack:
            self.undoStack.push(DeleteCommand(self.git(), self.selectedInstances.copy(), self))  # noqa: SLF001
        for instance in self.selectedInstances:
            self._module.git().resource().remove(instance)
        self.selectedInstances.clear()
        self.ui.mainRenderer.scene.selection.clear()
        self.ui.flatRenderer.instanceSelection.clear()
        self.rebuildInstanceList()

    def moveSelected(  # noqa: PLR0913
        self,
        x: float,
        y: float,
        z: float | None = None,
        *,
        noUndoStack: bool = False,
        noZCoord: bool = False,
    ):
        """Moves selected instances by the given offsets.

        Args:
        ----
            x: Float offset to move instances along the x-axis.
            y: Float offset to move instances along the y-axis.
            z: Float offset to move instances along the z-axis or None.
        """
        if self.ui.lockInstancesCheck.isChecked():
            return

        for instance in self.selectedInstances:
            self.log.debug("Moving %s", instance.resref)
            new_x = instance.position.x + x
            new_y = instance.position.y + y
            if noZCoord:
                new_z = instance.position.z
            else:
                new_z = instance.position.z + (z or self.ui.mainRenderer.walkmeshPoint(instance.position.x, instance.position.y).z)
            old_position = instance.position
            new_position = Vector3(new_x, new_y, new_z)
            if not noUndoStack:
                self.undoStack.push(MoveCommand(instance, old_position, new_position))
            instance.position = new_position

    def rotateSelected(self, x: float, y: float):
        if self.ui.lockInstancesCheck.isChecked():
            return

        for instance in self.selectedInstances:
            new_yaw = x / 60
            new_pitch = (y or 1) / 60
            new_roll = 0.0
            if not isinstance(instance, (GITCamera, GITCreature, GITDoor, GITPlaceable, GITStore, GITWaypoint)):
                continue  # doesn't support rotations.
            instance.rotate(new_yaw, new_pitch, new_roll)

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

    def getGitInstanceFromHighlightedListItem(self):
        item: QListWidgetItem = self.ui.instanceList.selectedItems()[0]
        result: GITInstance = item.data(QtCore.Qt.ItemDataRole.UserRole)
        return result

    def onInstanceVisibilityDoubleClick(self, checkbox: QCheckBox):
        """Toggles visibility of a single instance type on double click.

        This method should be called whenever one of the instance visibility checkboxes have been double clicked. The
        resulting affect should be that all checkboxes become unchecked except for the one that was pressed.

        Args:
        ----
            checkbox (QCheckBox): Checkbox that was double clicked.
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

    def enterInstanceMode(self):
        self._controls2d._mode = _InstanceMode.__new__(_InstanceMode)
        # HACK:
        self._controls2d._mode.deleteSelected = self.deleteSelected
        self._controls2d._mode.editSelectedInstance = self.editInstance
        self._controls2d._mode.buildList = self.rebuildInstanceList
        self._controls2d._mode.updateVisibility = self.updateToggles
        self._controls2d._mode.selectUnderneath = lambda: self.setSelection(self.ui.flatRenderer.instancesUnderMouse())
        self._controls2d._mode.__init__(self, self._installation, self.git())
        # self._controls2d._mode.rotateSelectedToPoint = self.rotateSelected

    def enterGeometryMode(self):
        self._controls2d._mode = _GeometryMode(self, self._installation, self.git(), hideOthers=False)

    def enterSpawnMode(self):
        # TODO
        self._controls2d._mode = _SpawnMode(self, self._installation, self.git())

    def onResourceTreeContextMenu(self, point: QPoint):
        menu = QMenu(self)
        curItem = self.ui.resourceTree.currentItem()
        if curItem is None:
            return
        data = curItem.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if isinstance(data, ModuleResource):
            self._active_instance_location_menu(data, menu)
        menu.exec_(self.ui.resourceTree.mapToGlobal(point))

    def onResourceTreeDoubleClicked(self, point: QPoint):
        curItem = self.ui.resourceTree.currentItem()
        data = curItem.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if isinstance(data, ModuleResource):
            self.openModuleResource(data)

    def onResourceTreeSingleClicked(self, point: QPoint):
        curItem = self.ui.resourceTree.currentItem()
        data = curItem.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if isinstance(data, ModuleResource):
            self.jump_to_instance_list_action(data=data)

    def jump_to_instance_list_action(self, *args, data: ModuleResource, **kwargs):
        this_ident = data.identifier()
        instances = self.git().instances()
        for instance in instances:
            if instance.identifier() == this_ident:
                self.selectInstanceItemOnList(instance)
                # self.setSelection([instance])
                return

    def _active_instance_location_menu(self, data: ModuleResource, menu: QMenu):
        """Builds an active override menu for a module resource.

        Args:
        ----
            data: ModuleResource - The module resource data
            menu: QMenu - The menu to build actions on
        """
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
            instances = self.git().instances()
            for instance in instances:
                if instance.identifier() == this_ident:
                    # self.selectInstanceItemOnList(instance)
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
        renderer = self.ui.mainRenderer

        if centerMouse:
            global_old_pos = renderer.mapToGlobal(renderer.rect().center())
            QCursor.setPos(global_old_pos)
        else:
            global_old_pos = renderer.mapToGlobal(QPoint(int(renderer._mousePrev.x), int(renderer._mousePrev.y)))
            QCursor.setPos(global_old_pos)
            local_old_pos = renderer.mapFromGlobal(global_old_pos)
            mutableScreen.x, mutableScreen.y = local_old_pos.x(), local_old_pos.y()

        if doRotations:
            yaw_delta = global_old_pos.x() - global_new_pos.x()
            pitch_delta = global_old_pos.y() - global_new_pos.y()

            if isinstance(self._controls3d, ModuleDesignerControlsFreeCam):
                strength = self.settings.rotateCameraSensitivityFC / 10000
                clamp = False
            else:
                strength = self.settings.rotateCameraSensitivity3d / 10000
                clamp = True

            renderer.rotateCamera(yaw_delta * strength, -pitch_delta * strength, clampRotations=clamp)

    def on3dMouseReleased(self, screen: Vector2, buttons: set[int], keys: set[int]):
        self.updateStatusBar(screen, buttons, keys, self.ui.mainRenderer)
        self._controls3d.onMouseReleased(screen, buttons, keys)

    def on3dKeyboardReleased(self, buttons: set[int], keys: set[int]):
        self.updateStatusBar(QCursor.pos(), buttons, keys, self.ui.mainRenderer)
        self._controls3d.onKeyboardReleased(buttons, keys)

    def on3dKeyboardPressed(self, buttons: set[int], keys: set[int]):
        self.updateStatusBar(QCursor.pos(), buttons, keys, self.ui.mainRenderer)
        self._controls3d.onKeyboardPressed(buttons, keys)

    def on3dObjectSelected(self, instance: GITInstance):
        if instance is not None:
            self.setSelection([instance])
        else:
            self.setSelection([])

    def onContextMenu(self, world: Vector3, point: QPoint, *, isFlatRendererCall: bool | None = None):
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
        """Displays a context menu for object insertion.

        Args:
        ----
            world: (Vector3): World position for context menu
        """
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

    def onInstanceListRightClicked(
        self,
        *args,
        **kwargs,
    ):
        item: QListWidgetItem = self.ui.instanceList.selectedItems()[0]
        instance: GITInstance = item.data(QtCore.Qt.ItemDataRole.UserRole)
        self.onContextMenuSelectionExists(instances=[instance])

    def onContextMenuSelectionExists(
        self,
        world: Vector3 | None = None,
        *,
        isFlatRendererCall: bool | None = None,
        getMenu: bool | None = None,
        instances: Sequence[GITInstance] | None = None,
    ) -> QMenu | None:  # sourcery skip: extract-method
        """Checks if a context menu selection exists.

        Args:
        ----
            self: The class instance
        """
        self.log.debug(f"onContextMenuSelectionExists(isFlatRendererCall={isFlatRendererCall}, getMenu={getMenu})")
        menu = QMenu(self)
        instances = self.selectedInstances if instances is None else instances

        if instances:
            instance = instances[0]
            if isinstance(instance, GITCamera):
                menu.addAction("Snap Camera to 3D View").triggered.connect(lambda: self.snapCameraToView(instance))
                menu.addAction("Snap 3D View to Camera").triggered.connect(lambda: self.snapViewToGITCamera(instance))
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
        self.log.debug("ModuleDesigner on3dRendererInitialized")
        self.show()
        self.activateWindow()

    def on3dSceneInitialized(self):
        self.log.debug("ModuleDesigner on3dSceneInitialized")
        self.rebuildResourceTree()
        self.rebuildInstanceList()
        self._refreshWindowTitle()
        self.enterInstanceMode()
        self.show()
        self.activateWindow()

    def on2dMouseMoved(self, screen: Vector2, delta: Vector2, buttons: set[int], keys: set[int]):
        # self.log.debug("on2dMouseMoved, screen: %s, delta: %s, buttons: %s, keys: %s", screen, delta, buttons, keys)
        worldDelta: Vector2 = self.ui.flatRenderer.toWorldDelta(delta.x, delta.y)
        world: Vector3 = self.ui.flatRenderer.toWorldCoords(screen.x, screen.y)
        self._controls2d.onMouseMoved(screen, delta, Vector2.from_vector3(world), worldDelta, buttons, keys)
        self.updateStatusBar(QCursor.pos(), buttons, keys, self.ui.flatRenderer)

    def on2dMouseReleased(self, screen: Vector2, buttons: set[int], keys: set[int]):
        # self.log.debug("on2dMouseReleased, screen: %s, buttons: %s, keys: %s", screen, buttons, keys)
        self._controls2d.onMouseReleased(screen, buttons, keys)
        self.updateStatusBar(QCursor.pos(), buttons, keys, self.ui.flatRenderer)

    def on2dKeyboardPressed(self, buttons: set[int], keys: set[int]):
        # self.log.debug("on2dKeyboardPressed, buttons: %s, keys: %s", buttons, keys)
        self._controls2d.onKeyboardPressed(buttons, keys)
        self.updateStatusBar(QCursor.pos(), buttons, keys, self.ui.flatRenderer)

    def on2dKeyboardReleased(self, buttons: set[int], keys: set[int]):
        # self.log.debug("on2dKeyboardReleased, buttons: %s, keys: %s", buttons, keys)
        self._controls2d.onKeyboardReleased(buttons, keys)
        self.updateStatusBar(QCursor.pos(), buttons, keys, self.ui.flatRenderer)

    def on2dMouseScrolled(self, delta: Vector2, buttons: set[int], keys: set[int]):
        # self.log.debug("on2dMouseScrolled, delta: %s, buttons: %s, keys: %s", delta, buttons, keys)
        self.updateStatusBar(QCursor.pos(), buttons, keys, self.ui.flatRenderer)
        self._controls2d.onMouseScrolled(delta, buttons, keys)

    def on2dMousePressed(self, screen: Vector2, buttons: set[int], keys: set[int]):
        # self.log.debug("on2dMousePressed, screen: %s, buttons: %s, keys: %s", screen, buttons, keys)
        self._controls2d.onMousePressed(screen, buttons, keys)
        self.updateStatusBar(screen, buttons, keys, self.ui.flatRenderer)

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
        keys = self.ui.mainRenderer.keysDown()
        buttons = self.ui.mainRenderer.mouseDown()
        rotation_keys = {
            "left": self._controls3d.rotateCameraLeft.satisfied(buttons, keys),
            "right": self._controls3d.rotateCameraRight.satisfied(buttons, keys),
            "up": self._controls3d.rotateCameraUp.satisfied(buttons, keys),
            "down": self._controls3d.rotateCameraDown.satisfied(buttons, keys),
        }
        movement_keys = {
            "up": self._controls3d.moveCameraUp.satisfied(buttons, keys),
            "down": self._controls3d.moveCameraDown.satisfied(buttons, keys),
            "left": self._controls3d.moveCameraLeft.satisfied(buttons, keys),
            "right": self._controls3d.moveCameraRight.satisfied(buttons, keys),
            "forward": self._controls3d.moveCameraForward.satisfied(buttons, keys),
            "backward": self._controls3d.moveCameraBackward.satisfied(buttons, keys),
            "in": self._controls3d.zoomCameraIn.satisfied(buttons, keys),
            "out": self._controls3d.zoomCameraOut.satisfied(buttons, keys),
        }

        # Determine last frame time to determine the delta modifiers
        curTime = time.time()
        timeSinceLastFrame = curTime - self.lastFrameTime
        self.lastFrameTime = curTime

        # Calculate rotation delta
        normRotateUnitsSetting = self.settings.rotateCameraSensitivity3d / 1000
        normRotateUnitsSetting *= self.baseFrameRate * timeSinceLastFrame  # apply modifier based on user's fps
        angleUnitsDelta = (math.pi / 4) * normRotateUnitsSetting

        # Rotate camera based on key inputs
        if rotation_keys["left"]:
            self.ui.mainRenderer.rotateCamera(angleUnitsDelta, 0)
        elif rotation_keys["right"]:
            self.ui.mainRenderer.rotateCamera(-angleUnitsDelta, 0)
        if rotation_keys["up"]:
            self.ui.mainRenderer.rotateCamera(0, angleUnitsDelta)
        elif rotation_keys["down"]:
            self.ui.mainRenderer.rotateCamera(0, -angleUnitsDelta)

        # Calculate movement delta
        keys = self.ui.mainRenderer.keysDown()
        buttons = self.ui.mainRenderer.mouseDown()
        if self._controls3d.speedBoostControl.satisfied(buttons, keys, exactKeysAndButtons=False):
            moveUnitsDelta = (
                (self.settings.boostedFlyCameraSpeedFC)
                if isinstance(self._controls3d, ModuleDesignerControlsFreeCam)
                else (self.settings.boostedMoveCameraSensitivity3d)
            )
        else:
            moveUnitsDelta = (
                (self.settings.flyCameraSpeedFC)
                if isinstance(self._controls3d, ModuleDesignerControlsFreeCam)
                else (self.settings.moveCameraSensitivity3d)
            )


        moveUnitsDelta /= 500  # normalize
        moveUnitsDelta *= timeSinceLastFrame * self.baseFrameRate  # apply modifier based on user's fps

        # Zoom camera based on inputs
        if movement_keys["in"]:
            self.ui.mainRenderer.zoomCamera(moveUnitsDelta)
        if movement_keys["out"]:
            self.ui.mainRenderer.zoomCamera(-moveUnitsDelta)

        # Move camera based on key inputs
        if movement_keys["up"]:
            if isinstance(self._controls3d, ModuleDesignerControls3d):
                self.ui.mainRenderer.scene.camera.z += moveUnitsDelta
            else:
                self.ui.mainRenderer.moveCamera(0, 0, moveUnitsDelta)
        if movement_keys["down"]:
            if isinstance(self._controls3d, ModuleDesignerControls3d):
                self.ui.mainRenderer.scene.camera.z -= moveUnitsDelta
            else:
                self.ui.mainRenderer.moveCamera(0, 0, -moveUnitsDelta)

        if movement_keys["left"]:
            if isinstance(self._controls3d, ModuleDesignerControls3d):
                self.ui.mainRenderer.panCamera(0, -moveUnitsDelta, 0)
            else:
                self.ui.mainRenderer.moveCamera(0, -moveUnitsDelta, 0)
        if movement_keys["right"]:
            if isinstance(self._controls3d, ModuleDesignerControls3d):
                self.ui.mainRenderer.panCamera(0, moveUnitsDelta, 0)
            else:
                self.ui.mainRenderer.moveCamera(0, moveUnitsDelta, 0)

        if movement_keys["forward"]:
            if isinstance(self._controls3d, ModuleDesignerControls3d):
                self.ui.mainRenderer.panCamera(moveUnitsDelta, 0, 0)
            else:
                self.ui.mainRenderer.moveCamera(moveUnitsDelta, 0, 0)
        if movement_keys["backward"]:
            if isinstance(self._controls3d, ModuleDesignerControls3d):
                self.ui.mainRenderer.panCamera(-moveUnitsDelta, 0, 0)
            else:
                self.ui.mainRenderer.moveCamera(-moveUnitsDelta, 0, 0)
