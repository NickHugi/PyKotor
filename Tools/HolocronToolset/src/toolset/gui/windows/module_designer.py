from __future__ import annotations

import math

from copy import deepcopy
from typing import TYPE_CHECKING

import qtpy

from qtpy import QtCore
from qtpy.QtCore import QPoint, QTimer
from qtpy.QtGui import QColor, QIcon, QPixmap
from qtpy.QtWidgets import QAction, QApplication, QListWidgetItem, QMainWindow, QMenu, QMessageBox, QTreeWidgetItem

from pykotor.gl.scene import Camera
from pykotor.tools.misc import is_mod_file
from utility.misc import is_debug_mode

if qtpy.API_NAME in ("PyQt5", "PySide2"):
    from qtpy.QtWidgets import QUndoStack
elif qtpy.API_NAME in ("PyQt6", "PySide6"):
    from qtpy.QtGui import QUndoStack
else:
    raise ValueError(f"Invalid QT_API: '{qtpy.API_NAME}'")

from pykotor.common.geometry import SurfaceMaterial, Vector2, Vector3, Vector4
from pykotor.common.misc import Color, ResRef
from pykotor.common.module import Module, ModuleResource
from pykotor.common.stream import BinaryWriter
from pykotor.extract.file import ResourceIdentifier
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
from toolset.data.misc import ControlItem
from toolset.gui.dialogs.asyncloader import AsyncLoader
from toolset.gui.dialogs.insert_instance import InsertInstanceDialog
from toolset.gui.dialogs.select_module import SelectModuleDialog
from toolset.gui.editor import Editor
from toolset.gui.editors.git import DuplicateCommand, MoveCommand, RotateCommand, _GeometryMode, _InstanceMode, _SpawnMode, openInstanceDialog
from toolset.gui.widgets.settings.module_designer import ModuleDesignerSettings
from toolset.gui.windows.help import HelpWindow
from toolset.utils.misc import QtMouse
from toolset.utils.window import openResourceEditor
from utility.error_handling import safe_repr
from utility.logger_util import RobustRootLogger

if TYPE_CHECKING:
    import os

    from logging import Logger

    from glm import vec3
    from qtpy.QtGui import QCloseEvent, QFont, QKeyEvent, QShowEvent
    from qtpy.QtWidgets import QCheckBox, QWidget

    from pykotor.gl.scene import Camera
    from pykotor.resource.formats.bwm.bwm_data import BWM
    from pykotor.resource.generics.are import ARE
    from pykotor.resource.generics.git import GIT
    from pykotor.resource.generics.ifo import IFO
    from pykotor.tools.path import CaseAwarePath
    from toolset.data.installation import HTInstallation
    from toolset.gui.widgets.renderer.module import ModuleRenderer
    from toolset.gui.widgets.renderer.walkmesh import WalkmeshRenderer
    from utility.system.path import Path


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
        self._geomInstance: GITInstance | None = None  # Used to track which trigger/encounter you are editing
        self._orig_filepath: Path | None = mod_filepath

        self.initialPositions: dict[GITInstance, Vector3] = {}
        self.initialRotations: dict[GITCamera | GITCreature | GITDoor | GITPlaceable | GITStore | GITWaypoint, Vector4 | float] = {}
        self.undoStack: QUndoStack = QUndoStack(self)

        self.selectedInstances: list[GITInstance] = []
        self.settings: ModuleDesignerSettings = ModuleDesignerSettings()
        self.log: Logger = RobustRootLogger()

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
        self._setupSignals()

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

        # self._controls3d: ModuleDesignerControls3d | ModuleDesignerControlsFreeCam = ModuleDesignerControls3d(self, self.ui.mainRenderer)
        self._controls3d: ModuleDesignerControls3d | ModuleDesignerControlsFreeCam = ModuleDesignerControlsFreeCam(self, self.ui.mainRenderer)
        self._controls2d: ModuleDesignerControls2d = ModuleDesignerControls2d(self, self.ui.flatRenderer)

        if mod_filepath is None:  # Use singleShot timer so the ui window opens while the loading is happening.
            QTimer().singleShot(33, self.openModuleWithDialog)
        else:
            QTimer().singleShot(33, lambda: self.openModule(mod_filepath))

    def showEvent(self, a0: QShowEvent):
        super().showEvent(a0)

    def closeEvent(self, event: QCloseEvent):
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

        self.ui.viewCreatureCheck.mouseDoubleClickEvent = lambda a0: self.onInstanceVisibilityDoubleClick(self.ui.viewCreatureCheck)  # noqa: ARG005
        self.ui.viewPlaceableCheck.mouseDoubleClickEvent = lambda a0: self.onInstanceVisibilityDoubleClick(self.ui.viewPlaceableCheck)  # noqa: ARG005
        self.ui.viewDoorCheck.mouseDoubleClickEvent = lambda a0: self.onInstanceVisibilityDoubleClick(self.ui.viewDoorCheck)  # noqa: ARG005
        self.ui.viewSoundCheck.mouseDoubleClickEvent = lambda a0: self.onInstanceVisibilityDoubleClick(self.ui.viewSoundCheck)  # noqa: ARG005
        self.ui.viewTriggerCheck.mouseDoubleClickEvent = lambda a0: self.onInstanceVisibilityDoubleClick(self.ui.viewTriggerCheck)  # noqa: ARG005
        self.ui.viewEncounterCheck.mouseDoubleClickEvent = lambda a0: self.onInstanceVisibilityDoubleClick(self.ui.viewEncounterCheck)  # noqa: ARG005
        self.ui.viewWaypointCheck.mouseDoubleClickEvent = lambda a0: self.onInstanceVisibilityDoubleClick(self.ui.viewWaypointCheck)  # noqa: ARG005
        self.ui.viewCameraCheck.mouseDoubleClickEvent = lambda a0: self.onInstanceVisibilityDoubleClick(self.ui.viewCameraCheck)  # noqa: ARG005
        self.ui.viewStoreCheck.mouseDoubleClickEvent = lambda a0: self.onInstanceVisibilityDoubleClick(self.ui.viewStoreCheck)  # noqa: ARG005

        self.ui.instanceList.doubleClicked.connect(self.onInstanceListDoubleClicked)
        self.ui.instanceList.customContextMenuRequested.connect(self.onContextMenuSelectionExists)

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
        orig_filepath = mod_filepath
        mod_root = self._installation.get_module_root(mod_filepath)
        mod_filepath = mod_filepath.with_name(f"{mod_root}.mod")
        if not mod_filepath.is_file():
            self.log.info("No .mod found at '%s'", mod_filepath)
            answer = QMessageBox.question(
                self,
                "No .mod for this module found.",
                f"The Module Designer would like to create a .mod for module '{mod_root}', would you like to do this now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if answer == QMessageBox.StandardButton.Yes:
                self.log.info("Creating '%s.mod' from the rims/erfs...", mod_root)
                module.rim_to_mod(mod_filepath, game=self._installation.game())
                self._installation.reload_module(mod_filepath.name)
            else:
                mod_filepath = orig_filepath
        elif mod_filepath != orig_filepath:
            self.log.debug("User chose non-dotmod '%s'", orig_filepath)
            answer = QMessageBox.question(
                self,
                f"{orig_filepath.suffix} file chosen when {mod_filepath.suffix} preferred.",
                f"You've chosen '{orig_filepath.name}' with a '{orig_filepath.suffix}' extension. The Module Designer recommends modifying .mod's.<br><br>Use '{mod_filepath.name}' instead?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if answer != QMessageBox.StandardButton.Yes:
                mod_filepath = orig_filepath

        def task() -> tuple[Module, GIT, list[BWM]]:
            combined_module = Module(mod_root, self._installation, use_dot_mod=is_mod_file(mod_filepath))
            git_resource = combined_module.git()
            if git_resource is None:
                raise ValueError(f"This module '{mod_root}' is missing a GIT!")

            git: GIT = git_resource.resource()
            walkmeshes: list[BWM] = []
            for bwm in combined_module.resources.values():
                if bwm.restype() is not ResourceType.WOK:
                    continue
                bwm_res: BWM | None = bwm.resource()
                if bwm_res is None:
                    self.log.warning("bwm '%s.%s' returned None resource data, skipping...", bwm.resname(), bwm.restype())
                    continue
                self.log.info("Adding walkmesh '%s.%s'", bwm.resname(), bwm.restype())
                walkmeshes.append(bwm_res)
            return (combined_module, git, walkmeshes)

        # Point of no return: unload any previous module and load the new one.
        self.unloadModule()
        if is_debug_mode():
            result = task()
        else:
            loader = AsyncLoader(
                self,
                f"Loading module '{mod_filepath.name}' into designer...",
                task,
                "Error occurred loading the module designer",
            )
            result = loader.value
            if not loader.exec_():
                return
        self.log.debug("ModuleDesigner.openModule Loader finished.")
        new_module, git, walkmeshes = result
        self._module = new_module
        self.log.debug("setGit")
        self.ui.flatRenderer.setGit(git)
        self.enterInstanceMode()
        self.log.debug("init mainRenderer")
        self.ui.mainRenderer.initializeRenderer(self._installation, new_module)
        self.ui.mainRenderer.scene.show_cursor = self.ui.cursorCheck.isChecked()
        self.log.debug("set flatRenderer walkmeshes")
        self.ui.flatRenderer.setWalkmeshes(walkmeshes)
        self.ui.flatRenderer.centerCamera()
        self.show()
        # Inherently calls On3dSceneInitialized when done.

    def unloadModule(self):
        self._module = None
        self.ui.mainRenderer.shutdownRenderer()
        self.ui.mainRenderer._scene = None

    def showHelpWindow(self):
        window = HelpWindow(self, "./help/tools/1-moduleEditor.md")
        window.show()

    #    @with_variable_trace((Exception, OSError))
    def git(self) -> GIT:
        return self._module.git().resource()

    #    @with_variable_trace(Exception)
    def are(self) -> ARE:
        return self._module.are().resource()

    #    @with_variable_trace(Exception)
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
        location: CaseAwarePath = self._installation.override_path() / f"{resource.identifier()}"
        data = resource.data()
        if data is None:
            RobustRootLogger().error(f"Cannot find resource {resource.identifier()} anywhere to copy to Override. Locations: {resource.locations()}")
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

        Processing Logic:
        ----------------
            1. Clear selection if clearExisting is True
            2. Iterate through top level items
            3. Iterate through child items of each top level
            4. Check if instance matches item and select it.
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
                    self.log.warning("item was somehow None in selectResourceItem index %s", j)
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

        Rebuilding Logic:
        ----------------
            - Clear existing instance list
            - Only rebuild if module is loaded
            - Filter instances based on visible type mappings
            - Add each instance to the list with icon, text, tooltips from the instance data.
        """
        self.log.debug("rebuildInstanceList called.")
        self.ui.instanceList.clear()
        self.ui.instanceList.setEnabled(True)
        self.ui.instanceList.setVisible(True)

        # Only build if module is loaded
        if self._module is None:
            self.ui.instanceList.setEnabled(False)
            self.ui.instanceList.setVisible(False)
            return

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

        Processing Logic:
        ----------------
            - Clear any existing selection from the instance list
            - Iterate through each item in the instance list
            - Check if the item's stored data matches the passed in instance
            - If so, select the item and scroll it into view.
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

        Processing Logic:
        ----------------
            1. Snaps the instance position to the walkmesh if walkmeshSnap is True
            2. Checks if the instance is a camera, and if not:
            3. Opens an insert instance dialog
            4. If accepted, rebuilds the resource tree and sets the instance resref and adds it
            5. Also sets tag/name if waypoint/trigger/door
            6. If a camera, just adds it
            7. Rebuilds the instance list
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
                instance.resref = ResRef(dialog.resname)  # type: ignore[reportAttributeAccessIssue]
                self._module.git().resource().add(instance)

                if isinstance(instance, GITWaypoint):
                    utw = read_utw(dialog.data)
                    instance.tag = utw.tag
                    instance.name = utw.name
                elif isinstance(instance, GITTrigger):
                    utt = read_utt(dialog.data)
                    instance.tag = utt.tag
                    if not instance.geometry:
                        RobustRootLogger().info("Creating default triangle trigger geometry for %s.%s...", instance.resref, "utt")
                        instance.geometry.create_triangle(origin=instance.position)
                elif isinstance(instance, GITEncounter):
                    if not instance.geometry:
                        RobustRootLogger().info("Creating default triangle trigger geometry for %s.%s...", instance.resref, "ute")
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

        Processing Logic:
        ----------------
            - Sets position of instance to cursor position
            - Checks if instance is camera, opens dialog if not
            - Adds instance to resource tree if dialog confirms
            - Rebuilds instance list.
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
                instance.resref = ResRef(dialog.resname)  # type: ignore[reportAttributeAccessIssue]
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

    def snapCameraToView(self, instance: GITCamera):
        scene = self.ui.mainRenderer.scene
        assert scene is not None

        view: vec3 = scene.camera.true_position()
        rot: Camera = scene.camera
        new_position = Vector3(view.x, view.y, view.z)
        self.undoStack.push(MoveCommand(instance, instance.position, new_position, instance.height, scene.camera.height))
        instance.height = scene.camera.height
        instance.position = new_position

        self.log.debug("Create RotateCommand for undo/redo functionality")
        new_orientation = Vector4.from_euler(math.pi / 2 - rot.yaw, 0, math.pi - rot.pitch)
        self.undoStack.push(RotateCommand(instance, instance.orientation, new_orientation))
        instance.orientation = new_orientation

    def snapViewToGITInstance(self, instance: GITInstance):
        camera: Camera = self._getSceneCamera()
        yaw = instance.yaw()
        camera.yaw = camera.yaw if yaw is None else yaw
        camera.x, camera.y, camera.z = instance.position
        camera.y = instance.position.y
        camera.z = instance.position.z+2
        camera.distance = 0

    def snapViewToGITCamera(self, instance: GITCamera):
        camera: Camera = self._getSceneCamera()
        euler: Vector3 = instance.orientation.to_euler()
        camera.pitch = math.pi - euler.z - math.radians(instance.pitch)
        camera.yaw = math.pi / 2 - euler.x
        camera.x = instance.position.x
        camera.y = instance.position.y
        camera.z = instance.position.z + instance.height
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

    def deleteSelected(self):
        for instance in self.selectedInstances:
            self._module.git().resource().remove(instance)

        self.selectedInstances.clear()
        self.ui.mainRenderer.scene.selection.clear()
        self.ui.flatRenderer.instanceSelection.clear()
        self.rebuildInstanceList()

    def moveSelected(
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

        Processing Logic:
        ----------------
            - Checks if instance locking is enabled and returns if True
            - Loops through selected instances
            - Increases x, y position by offsets
            - Increases z position by offset if provided, else sets to walkmesh height
            - No return, modifies instances in place.
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
                    self.log.debug("3d Create the MoveCommand for undo/redo functionality")
                    move_command = MoveCommand(instance, old_position, new_position)
                    self.undoStack.push(move_command)
                elif not old_position:
                    self.log.debug("3d No old position %s", instance.resref)
                else:
                    self.log.debug("3d Both old and new positions are the same %s", instance.resref)

            # Reset for the next drag operation
            self.initialPositions.clear()
            self.log.debug("No longer drag moving 3d")
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
            self.log.debug("No longer drag rotating 3d")
            self.isDragRotating = False

    def onInstanceListDoubleClicked(self):
        if self.ui.instanceList.selectedItems():
            item: QListWidgetItem = self.ui.instanceList.selectedItems()[0]
            instance: GITInstance = item.data(QtCore.Qt.ItemDataRole.UserRole)
            self.setSelection([instance])
            self.ui.mainRenderer.snapCameraToPoint(instance.position)
            self.ui.flatRenderer.snapCameraToPoint(instance.position)

    def onInstanceVisibilityDoubleClick(self, checkbox: QCheckBox):
        """Toggles visibility of a single instance type on double click.

        This method should be called whenever one of the instance visibility checkboxes have been double clicked. The
        resulting affect should be that all checkboxes become unchecked except for the one that was pressed.

        Args:
        ----
            checkbox (QCheckBox): Checkbox that was double clicked.

        Processing Logic:
        ----------------
            - Unchecks all other instance type checkboxes
            - Checks the checkbox that was double clicked
            - This ensures only one instance type is visible at a time
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
        self._controls2d._mode = _InstanceMode(self, self._installation, self.git())
        # HACK:
        self._controls2d._mode.deleteSelected = self.deleteSelected
        self._controls2d._mode.duplicateSelected = ModuleDesignerControls3d(self, self.ui.mainRenderer)._duplicateSelectedInstance
        self._controls2d._mode.editSelectedInstance = self.editInstance

    def enterGeometryMode(self):
        self._controls2d._mode = _GeometryMode(self, self._installation, self.git(), hideOthers=False)

    def enterSpawnMode(self):
        # TODO
        self._controls2d._mode = _SpawnMode(self, self._installation, self.git())

    def onResourceTreeContextMenu(self, point: QPoint):
        menu = QMenu(self)
        curItem = self.ui.resourceTree.currentItem()
        if not curItem:
            self.log.warning("curItem was None in onResourceTreeContextMenu")
            return

        data = curItem.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if isinstance(data, ModuleResource):
            self._active_instance_location_menu(data, menu)
        menu.exec_(self.ui.resourceTree.mapToGlobal(point))

    def _active_instance_location_menu(self, data: ModuleResource, menu: QMenu):
        """Builds an active override menu for a module resource.

        Args:
        ----
            data: ModuleResource - The module resource data
            menu: QMenu - The menu to build actions on

        Processing Logic:
        ----------------
            - Adds actions to edit active file, reload active file, and copy to override
            - Loops through each location in the resource and adds an action
            - Disables the active location action
            - Disables copy to override if a location contains 'override'
            - Connects all actions to trigger appropriate functions.
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

    def on3dMouseMoved(self, screen: Vector2, screenDelta: Vector2, world: Vector3, buttons: set[int], keys: set[int]):
        self._controls3d.onMouseMoved(screen, screenDelta, world, buttons, keys)

    def on3dMouseScrolled(self, delta: Vector2, buttons: set[int], keys: set[int]):
        self._controls3d.onMouseScrolled(delta, buttons, keys)

    def on3dMousePressed(self, screen: Vector2, buttons: set[int], keys: set[int]):
        self._controls3d.onMousePressed(screen, buttons, keys)

    def on3dMouseReleased(self, screen: Vector2, buttons: set[int], keys: set[int]):
        self._controls3d.onMouseReleased(screen, buttons, keys)

    def on3dKeyboardReleased(self, buttons: set[int], keys: set[int]):
        self._controls3d.onKeyboardReleased(buttons, keys)

    def on3dKeyboardPressed(self, buttons: set[int], keys: set[int]):
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
            menu = self.onContextMenuSelectionNone(world)
        else:
            menu = self.onContextMenuSelectionExists(world, isFlatRendererCall=isFlatRendererCall, getMenu=True)

        menu.popup(self.cursor().pos())
        menu.aboutToHide.connect(self.ui.mainRenderer.resetMouseButtons)

    def onContextMenuSelectionNone(self, world: Vector3):
        """Displays a context menu for object insertion.

        Args:
        ----
            world: (Vector3): World position for context menu

        Processing Logic:
        ----------------
            - Creates a QMenu object
            - Adds actions to menu for inserting different object types at world position or view position
            - Connects actions to addInstance method
            - Pops up menu at mouse cursor position
            - Connects menu hide signal to reset mouse buttons
        """
        menu = QMenu(self)

        rot = self.ui.mainRenderer.scene.camera
        menu.addAction("Insert Camera").triggered.connect(lambda: self.addInstance(GITCamera(*world), walkmeshSnap=False))  # type: ignore[reportArgumentType]
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

    def onContextMenuSelectionExists(
        self,
        world: Vector3,
        *,
        isFlatRendererCall: bool | None = None,
        getMenu: bool | None = None,
    ) -> QMenu | None:  # sourcery skip: extract-method
        """Checks if a context menu selection exists.

        Args:
        ----
            self: The class instance

        Processing Logic:
        ----------------
            - Checks if any instances are selected
            - If a camera instance is selected, adds camera-view snapping actions
            - Always adds edit and remove actions
            - Pops up the context menu at the mouse cursor position
            - Resets mouse buttons when menu closes.
        """
        print(f"onContextMenuSelectionExists(isFlatRendererCall={isFlatRendererCall}, getMenu={getMenu})")
        menu = QMenu(self)

        if self.selectedInstances:
            instance = self.selectedInstances[0]
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
            self._controls2d._mode._getRenderContextMenu(Vector2(world.x, world.y), menu)
        if not getMenu:
            menu.popup(self.cursor().pos())
            menu.aboutToHide.connect(self.ui.mainRenderer.resetMouseButtons)
            return None
        return menu

    def on3dRendererInitialized(self):
        self.log.debug("ModuleDesigner on3dRendererInitialized")
        self.show()
        self.activateWindow()

    def on3dSceneInitialized(self):
        self.log.debug("ModuleDesigner on3dSceneInitialized")
        self.rebuildResourceTree()
        self.rebuildInstanceList()
        self._refreshWindowTitle()
        self.updateToggles()
        self.show()
        self.activateWindow()

    def on2dMouseMoved(self, screen: Vector2, delta: Vector2, buttons: set[int], keys: set[int]):
        #self.log.debug("on2dMouseMoved, screen: %s, delta: %s, buttons: %s, keys: %s", screen, delta, buttons, keys)
        worldDelta: Vector2 = self.ui.flatRenderer.toWorldDelta(delta.x, delta.y)
        world: Vector3 = self.ui.flatRenderer.toWorldCoords(screen.x, screen.y)
        self._controls2d.onMouseMoved(screen, delta, Vector2.from_vector3(world), worldDelta, buttons, keys)

    def on2dMouseReleased(self, screen: Vector2, buttons: set[int], keys: set[int]):
        #self.log.debug("on2dMouseReleased, screen: %s, buttons: %s, keys: %s", screen, buttons, keys)
        self._controls2d.onMouseReleased(screen, buttons, keys)

    def on2dKeyboardReleased(self, buttons: set[int], keys: set[int]):
        self.log.debug("on2dKeyboardReleased, buttons: %s, keys: %s", buttons, keys)
        self._controls2d.onKeyboardReleased(buttons, keys)

    def on2dMouseScrolled(self, delta: Vector2, buttons: set[int], keys: set[int]):
        self.log.debug("on2dMouseScrolled, delta: %s, buttons: %s, keys: %s", delta, buttons, keys)
        self._controls2d.onMouseScrolled(delta, buttons, keys)

    def on2dMousePressed(self, screen: Vector2, buttons: set[int], keys: set[int]):
        self.log.debug("on2dMousePressed, screen: %s, buttons: %s, keys: %s", screen, buttons, keys)
        self._controls2d.onMousePressed(screen, buttons, keys)

    def on2dKeyboardPressed(self, buttons: set[int], keys: set[int]):
        self.log.debug("on2dKeyboardPressed, buttons: %s, keys: %s", buttons, keys)
        self._controls2d.onKeyboardPressed(buttons, keys)

    # endregion

    # region Events
    def keyPressEvent(self, e: QKeyEvent, bubble: bool = True):  # noqa: FBT001, FBT002
        super().keyPressEvent(e)
        self.ui.mainRenderer.keyPressEvent(e)
        self.ui.flatRenderer.keyPressEvent(e)

    def keyReleaseEvent(self, e: QKeyEvent, bubble: bool = True):  # noqa: FBT001, FBT002
        super().keyReleaseEvent(e)
        self.ui.mainRenderer.keyReleaseEvent(e)
        self.ui.flatRenderer.keyReleaseEvent(e)

    # endregion


class ModuleDesignerControls3d:
    def __init__(self, editor: ModuleDesigner, renderer: ModuleRenderer):
        """Initializes the 3D view controller.

        Args:
        ----
            editor: ModuleDesigner - The module designer instance
            renderer: ModuleRenderer - The 3D renderer instance

        Processing Logic:
        ----------------
            - Initializes control items from settings bindings
            - Sets initial scene and renderer properties
            - Hides cursor if setting is unchecked.
        """
        self.editor: ModuleDesigner = editor
        self.settings: ModuleDesignerSettings = ModuleDesignerSettings()
        self.renderer: ModuleRenderer = renderer

        self.moveXYCamera: ControlItem = ControlItem(self.settings.moveCameraXY3dBind)
        self.moveZCamera: ControlItem = ControlItem(self.settings.moveCameraZ3dBind)
        self.moveCameraPlane: ControlItem = ControlItem(self.settings.moveCameraPlane3dBind)
        self.rotateCamera: ControlItem = ControlItem(self.settings.rotateCamera3dBind)
        self.zoomCamera: ControlItem = ControlItem(self.settings.zoomCamera3dBind)
        self.zoomCameraMM: ControlItem = ControlItem(self.settings.zoomCameraMM3dBind)
        self.rotateSelected: ControlItem = ControlItem(self.settings.rotateSelected3dBind)
        self.moveXYSelected: ControlItem = ControlItem(self.settings.moveSelectedXY3dBind)
        self.moveZSelected: ControlItem = ControlItem(self.settings.moveSelectedZ3dBind)
        self.selectUnderneath: ControlItem = ControlItem(self.settings.selectObject3dBind)
        self.moveCameraToSelected: ControlItem = ControlItem(self.settings.moveCameraToSelected3dBind)
        self.moveCameraToCursor: ControlItem = ControlItem(self.settings.moveCameraToCursor3dBind)
        self.moveCameraToEntryPoint: ControlItem = ControlItem(self.settings.moveCameraToEntryPoint3dBind)
        self.toggleFreeCam: ControlItem = ControlItem(self.settings.toggleFreeCam3dBind)
        self.deleteSelected: ControlItem = ControlItem(self.settings.deleteObject3dBind)
        self.duplicateSelected: ControlItem = ControlItem(self.settings.duplicateObject3dBind)
        self.openContextMenu: ControlItem = ControlItem((set(), {int(QtMouse.RightButton)}))
        self.rotateCameraLeft: ControlItem = ControlItem(self.settings.rotateCameraLeft3dBind)
        self.rotateCameraRight: ControlItem = ControlItem(self.settings.rotateCameraRight3dBind)
        self.rotateCameraUp: ControlItem = ControlItem(self.settings.rotateCameraUp3dBind)
        self.rotateCameraDown: ControlItem = ControlItem(self.settings.rotateCameraDown3dBind)
        self.moveCameraUp: ControlItem = ControlItem(self.settings.moveCameraUp3dBind)
        self.moveCameraDown: ControlItem = ControlItem(self.settings.moveCameraDown3dBind)
        self.moveCameraForward: ControlItem = ControlItem(self.settings.moveCameraForward3dBind)
        self.moveCameraBackward: ControlItem = ControlItem(self.settings.moveCameraBackward3dBind)
        self.moveCameraLeft: ControlItem = ControlItem(self.settings.moveCameraLeft3dBind)
        self.moveCameraRight: ControlItem = ControlItem(self.settings.moveCameraRight3dBind)
        self.zoomCameraIn: ControlItem = ControlItem(self.settings.zoomCameraIn3dBind)
        self.zoomCameraOut: ControlItem = ControlItem(self.settings.zoomCameraOut3dBind)
        self.toggleInstanceLock: ControlItem = ControlItem(self.settings.toggleLockInstancesBind)
        self.renderer.freeCam = False
        self.renderer.setCursor(QtCore.Qt.CursorShape.ArrowCursor)

    def onMouseScrolled(self, delta: Vector2, buttons: set[int], keys: set[int]):
        if self.zoomCamera.satisfied(buttons, keys):
            strength = self.settings.zoomCameraSensitivity3d / 2000
            self.renderer.scene.camera.distance += -delta.y * strength

        if self.moveZCamera.satisfied(buttons, keys):
            strength = self.settings.moveCameraSensitivity3d / 1000
            self.renderer.scene.camera.z -= -delta.y * strength

    def onMouseMoved(
        self,
        screen: Vector2,
        screenDelta: Vector2,
        world: Vector3,
        buttons: set[int],
        keys: set[int],
    ):
        """Moves the camera or selected instances on mouse movement.

        Args:
        ----
            screen (Vector2): Screen position
            screenDelta (Vector2): Screen position change
            world (Vector3): World position
            buttons (set[int]): Pressed mouse buttons
            keys (set[int]): Pressed keyboard keys
        """
        # Handle movement of View
        if self.moveXYCamera.satisfied(buttons, keys):
            forward = -screenDelta.y * self.renderer.scene.camera.forward()
            sideward = screenDelta.x * self.renderer.scene.camera.sideward()
            strength = self.settings.moveCameraSensitivity3d / 1000
            self.renderer.scene.camera.x -= (forward.x + sideward.x) * strength
            self.renderer.scene.camera.y -= (forward.y + sideward.y) * strength

        if self.moveCameraPlane.satisfied(buttons, keys):  # sourcery skip: extract-method
            upward = screenDelta.y * self.renderer.scene.camera.upward(ignore_xy=False)
            sideward = screenDelta.x * self.renderer.scene.camera.sideward()
            strength = self.settings.moveCameraSensitivity3d / 1000
            self.renderer.scene.camera.z -= (upward.z + sideward.z) * strength
            self.renderer.scene.camera.y -= (upward.y + sideward.y) * strength
            self.renderer.scene.camera.x -= (upward.x + sideward.x) * strength

        if self.rotateCamera.satisfied(buttons, keys):
            strength = self.settings.moveCameraSensitivity3d / 10000
            self.renderer.rotateCamera(-screenDelta.x * strength, screenDelta.y * strength)
            return  # save users from motion sickness: don't process other commands during view rotations.

        if self.zoomCameraMM.satisfied(buttons, keys):
            strength = self.settings.zoomCameraSensitivity3d / 10000
            self.renderer.scene.camera.distance -= screenDelta.y * strength

        # Handle movement of selected instances.
        if self.moveXYSelected.satisfied(buttons, keys):
            if self.editor.ui.lockInstancesCheck.isChecked():
                return

            if not self.editor.isDragMoving:
                self.editor.initialPositions = {instance: instance.position for instance in self.editor.selectedInstances}
                self.editor.isDragMoving = True
            for instance in self.editor.selectedInstances:
                self.editor.log.debug("Moving instance 3d '%s'", instance.resref)
                scene = self.renderer.scene
                assert scene is not None

                x = scene.cursor.position().x
                y = scene.cursor.position().y
                z = instance.position.z if isinstance(instance, GITCamera) else scene.cursor.position().z
                instance.position = Vector3(x, y, z)

        if self.moveZSelected.satisfied(buttons, keys):
            if not self.editor.isDragMoving:
                self.editor.initialPositions = {instance: instance.position for instance in self.editor.selectedInstances}
                self.editor.isDragMoving = True
            for instance in self.editor.selectedInstances:
                instance.position.z -= screenDelta.y / 40

        if self.rotateSelected.satisfied(buttons, keys):
            if not self.editor.isDragRotating and not self.editor.ui.lockInstancesCheck.isChecked():
                self.editor.log.debug("rotateSelected instance in 3d")
                for instance in self.editor.selectedInstances:
                    if not isinstance(instance, (GITCamera, GITCreature, GITDoor, GITPlaceable, GITStore, GITWaypoint)):
                        continue  # doesn't support rotations.
                    self.editor.initialRotations[instance] = instance.orientation if isinstance(instance, GITCamera) else instance.bearing
                self.editor.log.debug("3d rotate set isDragRotating")
                self.editor.isDragRotating = True
            self.editor.rotateSelected(screenDelta.x, screenDelta.y)

    def onMousePressed(self, screen: Vector2, buttons: set[int], keys: set[int]):
        """Handle mouse press events in the editor.

        Args:
        ----
            screen: Vector2 - Mouse position on screen
            buttons: set[int] - Pressed mouse buttons
            keys: set[int] - Pressed keyboard keys

        Processing Logic:
        ----------------
            - Check if select button is pressed and set doSelect flag
            - Check if duplicate button is pressed, duplicate selected instance and add/select new instance
            - Check if context menu button is pressed and open context menu at cursor position.
        """
        if self.selectUnderneath.satisfied(buttons, keys):
            self.renderer.doSelect = True

        scene = self.renderer.scene
        assert scene is not None
        if self.duplicateSelected.satisfied(buttons, keys) and self.editor.selectedInstances:
            self._duplicateSelectedInstance()
        if self.openContextMenu.satisfied(buttons, keys):
            world = Vector3(*scene.cursor.position())
            self.editor.onContextMenu(world, self.renderer.mapToGlobal(QPoint(int(screen.x), int(screen.y))))

    def onMouseReleased(
        self,
        screen: Vector2,
        buttons: set[int],
        keys: set[int],
    ):
        self.editor.handleUndoRedoFromLongActionFinished()

    def onKeyboardReleased(self, buttons: set[int], keys: set[int]):
        self.editor.handleUndoRedoFromLongActionFinished()

    def _duplicateSelectedInstance(self):
        instance: GITInstance = deepcopy(self.editor.selectedInstances[-1])
        vect3 = self.renderer.scene.cursor.position()
        instance.position = Vector3(vect3.x, vect3.y, vect3.z)
        self.editor.git().add(instance)
        self.editor.rebuildInstanceList()
        self.editor.setSelection([instance])

    def onKeyboardPressed(self, buttons: set[int], keys: set[int]):
        """Handles keyboard input in the editor.

        Args:
        ----
            buttons: set[int]: The pressed buttons
            keys: set[int]: The pressed keys

        Processes keyboard input:
            - Toggles free camera mode
            - Snaps camera to selected instance
            - Moves camera to cursor/entry point
            - Deletes selected instances
            - Rotates camera
            - Pans camera
            - Zooms camera
            - Toggles instance locking.
        """
        if self.toggleFreeCam.satisfied(buttons, keys):
            self.editor.toggleFreeCam()

        if self.moveCameraToSelected.satisfied(buttons, keys):
            for instance in self.editor.selectedInstances:
                self.renderer.snapCameraToPoint(instance.position)
                break

        if self.moveCameraToCursor.satisfied(buttons, keys):
            camera = self.renderer.scene.camera
            camera.x = self.renderer.scene.cursor.position().x
            camera.y = self.renderer.scene.cursor.position().y
            camera.z = self.renderer.scene.cursor.position().z
        if self.moveCameraToEntryPoint.satisfied(buttons, keys):
            self.editor.snapCameraToEntryLocation()

        if self.deleteSelected.satisfied(buttons, keys):
            self.editor.deleteSelected()

        if self.rotateCameraLeft.satisfied(buttons, keys):
            RobustRootLogger().debug("rotateCameraLeft")
            self.renderer.rotateCamera(math.pi / 4, 0)
        if self.rotateCameraRight.satisfied(buttons, keys):
            RobustRootLogger().debug("rotateCameraRight")
            self.renderer.rotateCamera(-math.pi / 4, 0)
        if self.rotateCameraUp.satisfied(buttons, keys):
            RobustRootLogger().debug("rotateCameraUp")
            self.renderer.rotateCamera(0, math.pi / 4)
        if self.rotateCameraDown.satisfied(buttons, keys):
            RobustRootLogger().debug("rotateCameraDown")
            self.renderer.rotateCamera(0, -math.pi / 4)

        if self.moveCameraUp.satisfied(buttons, keys):
            scene = self.renderer.scene
            assert scene is not None
            scene.camera.z += 1
        if self.moveCameraDown.satisfied(buttons, keys):
            scene = self.renderer.scene
            assert scene is not None
            scene.camera.z -= 1
        if self.moveCameraLeft.satisfied(buttons, keys):
            self.renderer.panCamera(0, -1, 0)
        if self.moveCameraRight.satisfied(buttons, keys):
            self.renderer.panCamera(0, 1, 0)
        if self.moveCameraForward.satisfied(buttons, keys):
            self.renderer.panCamera(1, 0, 0)
        if self.moveCameraBackward.satisfied(buttons, keys):
            self.renderer.panCamera(-1, 0, 0)

        if self.zoomCameraIn.satisfied(buttons, keys):
            self.renderer.zoomCamera(1)
        if self.zoomCameraOut.satisfied(buttons, keys):
            self.renderer.zoomCamera(-1)

        if self.toggleInstanceLock.satisfied(buttons, keys):
            self.editor.ui.lockInstancesCheck.setChecked(not self.editor.ui.lockInstancesCheck.isChecked())


class ModuleDesignerControlsFreeCam:
    def __init__(self, editor: ModuleDesigner, renderer: ModuleRenderer):
        """Initializes the free camera controller.

        Args:
        ----
            editor: {ModuleDesigner}: The module designer instance.
            renderer: {ModuleRenderer}: The module renderer instance.

        Initializes control items for camera movement and sets up free camera mode in the renderer:
            - Sets editor and settings references
            - Initializes control items for camera movement bindings
            - Hides cursor and enables free camera mode in renderer
            - Clears any existing key presses and centers cursor in renderer view.
        """
        self.editor: ModuleDesigner = editor
        self.settings: ModuleDesignerSettings = ModuleDesignerSettings()
        self.renderer: ModuleRenderer = renderer

        self.toggleFreeCam: ControlItem = ControlItem(self.settings.toggleFreeCam3dBind)
        self.moveCameraUp: ControlItem = ControlItem(self.settings.moveCameraUpFcBind)
        self.moveCameraDown: ControlItem = ControlItem(self.settings.moveCameraDownFcBind)
        self.moveCameraForward: ControlItem = ControlItem(self.settings.moveCameraForwardFcBind)
        self.moveCameraBackward: ControlItem = ControlItem(self.settings.moveCameraBackwardFcBind)
        self.moveCameraLeft: ControlItem = ControlItem(self.settings.moveCameraLeftFcBind)
        self.moveCameraRight: ControlItem = ControlItem(self.settings.moveCameraRightFcBind)

        self.renderer.freeCam = True
        self.renderer.setCursor(QtCore.Qt.CursorShape.BlankCursor)
        self.renderer._keysDown.clear()

        rendererPos = self.renderer.mapToGlobal(self.renderer.pos())
        mouseX = rendererPos.x() + self.renderer.width() // 2
        mouseY = rendererPos.y() + self.renderer.height() // 2
        self.renderer.cursor().setPos(mouseX, mouseY)

    def onMouseScrolled(self, delta: Vector2, buttons: set[int], keys: set[int]): ...

    def onMouseMoved(self, screen: Vector2, screenDelta: Vector2, world: Vector3, buttons: set[int], keys: set[int]):
        if self.renderer._scene and self.renderer.scene.show_cursor:  # HACK(th3w1zard1): fix later.
            self.renderer.scene.show_cursor = False
        rendererPos = self.renderer.mapToGlobal(self.renderer.pos())
        mouseX: int = rendererPos.x() + self.renderer.width() // 2
        mouseY: int = rendererPos.y() + self.renderer.height() // 2
        strength: float = self.settings.rotateCameraSensitivityFC / 10000

        print ("onMouseMoved, next call is rotateCamera.")
        self.renderer.rotateCamera(-screenDelta.x * strength, screenDelta.y * strength, snapRotations=False)
        self.renderer.cursor().setPos(mouseX, mouseY)

    def onMousePressed(self, screen: Vector2, buttons: set[int], keys: set[int]):
        print("onMousePressed2d")

    def onMouseReleased(self, screen: Vector2, buttons: set[int], keys: set[int]): ...

    def onKeyboardPressed(self, buttons: set[int], keys: set[int]):
        RobustRootLogger().debug(f"onKeyboardPressed, buttons: {buttons}, keys: {keys}")
        if self.toggleFreeCam.satisfied(buttons, keys):
            self.editor.toggleFreeCam()

        strength = self.settings.flyCameraSpeedFC / 100
        if self.moveCameraUp.satisfied(buttons, keys, exactKeys=False):
            RobustRootLogger().debug(f"moveCameraUp satisfied in onKeyboardPressed (strength {strength})")
            self.renderer.moveCamera(0, 0, strength)
        if self.moveCameraDown.satisfied(buttons, keys, exactKeys=False):
            RobustRootLogger().debug(f"moveCameraDown satisfied in onKeyboardPressed (strength {strength})")
            self.renderer.moveCamera(0, 0, -strength)
        if self.moveCameraLeft.satisfied(buttons, keys, exactKeys=False):
            RobustRootLogger().debug(f"moveCameraLeft satisfied in onKeyboardPressed (strength {strength})")
            self.renderer.moveCamera(0, -strength, 0)
        if self.moveCameraRight.satisfied(buttons, keys, exactKeys=False):
            RobustRootLogger().debug(f"moveCameraRight satisfied in onKeyboardPressed (strength {strength})")
            self.renderer.moveCamera(0, strength, 0)
        if self.moveCameraForward.satisfied(buttons, keys, exactKeys=False):
            RobustRootLogger().debug(f"moveCameraForward satisfied in onKeyboardPressed (strength {strength})")
            self.renderer.moveCamera(strength, 0, 0)
        if self.moveCameraBackward.satisfied(buttons, keys, exactKeys=False):
            RobustRootLogger().debug(f"moveCameraBackward satisfied in onKeyboardPressed (strength {strength})")
            self.renderer.moveCamera(-strength, 0, 0)

    def onKeyboardReleased(self, buttons: set[int], keys: set[int]): ...


class ModuleDesignerControls2d:
    def __init__(self, editor: ModuleDesigner, renderer: WalkmeshRenderer):
        """Initializes the 2D editor controller.

        Args:
        ----
            editor: {ModuleDesigner}: The editor module.
            renderer: {WalkmeshRenderer}: The renderer for the walkmesh.

        Processing Logic:
        ----------------
            - Sets editor and renderer references
            - Initializes control bindings from settings
            - Initializes ControlItem objects for each binding.
        """
        self.editor: ModuleDesigner = editor
        self.renderer: WalkmeshRenderer = renderer
        self.settings: ModuleDesignerSettings = ModuleDesignerSettings()
        self._mode: _InstanceMode | _GeometryMode | _SpawnMode

        self.moveCamera: ControlItem = ControlItem(self.settings.moveCamera2dBind)
        self.rotateCamera: ControlItem = ControlItem(self.settings.rotateCamera2dBind)
        self.zoomCamera: ControlItem = ControlItem(self.settings.zoomCamera2dBind)
        self.rotateSelected: ControlItem = ControlItem(self.settings.rotateObject2dBind)
        self.moveSelected: ControlItem = ControlItem(self.settings.moveObject2dBind)
        self.selectUnderneath: ControlItem = ControlItem(self.settings.selectObject2dBind)
        self.deleteSelected: ControlItem = ControlItem(self.settings.deleteObject2dBind)
        self.duplicateSelected: ControlItem = ControlItem(self.settings.duplicateObject2dBind)
        self.snapCameraToSelected: ControlItem = ControlItem(self.settings.moveCameraToSelected2dBind)
        self.openContextMenu: ControlItem = ControlItem((set(), {QtMouse.RightButton}))
        self.toggleInstanceLock: ControlItem = ControlItem(self.settings.toggleLockInstancesBind)

    def onMouseScrolled(self, delta: Vector2, buttons: set[int], keys: set[int]):
        """Scrolls camera zoom on mouse scroll.

        Args:
        ----
            delta: Mouse scroll delta vector
            buttons: Mouse buttons pressed
            keys: Keyboard keys pressed

        Processing Logic:
        ----------------
            - Checks if zoom camera control is satisfied by buttons and keys
            - Calculates zoom strength from scroll delta and sensitivity setting
            - Nudges camera zoom by calculated amount.
        """
        self.editor.log.debug("onMouseScrolled, delta: %s, buttons: %s, keys: %s", delta, buttons, keys)
        if self.zoomCamera.satisfied(buttons, keys):
            strength = self.editor.settings.zoomCameraSensitivity2d / 100 / 50
            zoomInFactor = 1.1 + strength
            zoomOutFactor = 0.90 - strength

            zoomFactor = zoomInFactor if delta.y > 0 else zoomOutFactor
            self.renderer.camera.nudgeZoom(zoomFactor)

    def onMouseMoved(self, screen: Vector2, screenDelta: Vector2, world: Vector2, worldDelta: Vector2, buttons: set[int], keys: set[int]):
        """Handles mouse movement events in the editor.

        Args:
        ----
            screen: Vector2 - Mouse position on screen in pixels
            screenDelta: Vector2 - Mouse movement since last event in pixels
            world: Vector2 - Mouse position in world space
            worldDelta: Vector2 - Mouse movement since last event in world space
            buttons: set[int] - Mouse buttons currently held down
            keys: set[int] - Keyboard keys currently held down

        Processing Logic:
        ----------------
            - Nudges camera position if move camera key is held based on worldDelta
            - Nudges camera rotation if rotate camera key is held based on screenDelta
            - Moves selected instances by worldDelta if move selected key is held
            - Rotates selected instances around world position if rotate selected key is held.
        """
        #self.editor.log.debug("onMouseMoved, screen: %s, screenDelta: %s, world: %s, worldDelta: %s, buttons: %s, keys: %s", screen, screenDelta, world, worldDelta, buttons, keys)
        if self.moveCamera.satisfied(buttons, keys):
            strength = self.settings.moveCameraSensitivity2d / 100
            self.renderer.camera.nudgePosition(-worldDelta.x * strength, -worldDelta.y * strength)

        if self.rotateCamera.satisfied(buttons, keys):
            strength = self.settings.rotateCameraSensitivity2d / 100 / 50
            self.renderer.camera.nudgeRotation(screenDelta.x * strength)

        if self.moveSelected.satisfied(buttons, keys):
            if isinstance(self._mode, _GeometryMode):
                RobustRootLogger().debug("Move geometry point? %s, %s", worldDelta.x, worldDelta.y)
                self._mode.moveSelected(worldDelta.x, worldDelta.y)
                return

            if not self.editor.isDragMoving:
                RobustRootLogger().debug("moveSelected instance in 2d")
                self.editor.initialPositions = {instance: instance.position for instance in self.editor.selectedInstances}
                self.editor.isDragMoving = True
            self.editor.moveSelected(worldDelta.x, worldDelta.y, noUndoStack=True, noZCoord=True)

        if self.rotateSelected.satisfied(buttons, keys):
            for instance in self.editor.selectedInstances:
                old_yaw = instance.yaw()
                if old_yaw is None:
                    print(instance.resref, "does not support rotating yaw")
                    continue
                if not self.editor.isDragRotating:
                    RobustRootLogger().debug("rotateSelected instance in 2d")
                    if not isinstance(instance, (GITCamera, GITCreature, GITDoor, GITPlaceable, GITStore, GITWaypoint)):
                        continue  # doesn't support rotations.
                    self.editor.initialRotations[instance] = instance.orientation if isinstance(instance, GITCamera) else instance.bearing

                rotation: float = -math.atan2(world.x - instance.position.x, world.y - instance.position.y)
                new_yaw = old_yaw - rotation if isinstance(instance, GITCamera) else -old_yaw + rotation
                instance.rotate(new_yaw, 0, 0)
            if not self.editor.isDragRotating:
                print("2d rotate set isDragRotating")
                self.editor.isDragRotating = True

    def onMousePressed(self, screen: Vector2, buttons: set[int], keys: set[int]):
        """Handle mouse press events in the editor.

        Args:
        ----
            screen: Vector2 - Mouse position
            buttons: set[int] - Pressed buttons
            keys: set[int] - Pressed keys

        Processing Logic:
        ----------------
            - Check if select button is pressed and select instance under mouse
            - Check if duplicate button is pressed and duplicate selected instance
            - Check if context menu button is pressed and open context menu.
        """
        RobustRootLogger().debug(f"onMousePressed, screen: {screen}, buttons: {buttons}, keys: {keys}")
        if self.selectUnderneath.satisfied(buttons, keys):
            if isinstance(self._mode, _GeometryMode):
                RobustRootLogger().debug("selectUnderneathGeometry?")
                self._mode.selectUnderneath()
            elif self.renderer.instancesUnderMouse():
                RobustRootLogger().debug("onMousePressed, selectUnderneath FOUND INSTANCES")
                self.editor.setSelection([self.renderer.instancesUnderMouse()[-1]])
            else:
                RobustRootLogger().debug("onMousePressed, selectUnderneath DID NOT FIND INSTANCES!")
                self.editor.setSelection([])

        if self.duplicateSelected.satisfied(buttons, keys) and self.editor.selectedInstances:
            RobustRootLogger().debug(f"Mode {self._mode.__class__.__name__}: moduleDesignerControls2d duplicateSelected satisfied ({self.editor.selectedInstances[-1]!r})")
            if isinstance(self.editor._controls2d._mode, _InstanceMode) and self.editor.selectedInstances:
                self._duplicate_instance()
        if self.openContextMenu.satisfied(buttons, keys):
            world: Vector3 = self.renderer.toWorldCoords(screen.x, screen.y)
            self.editor.onContextMenu(world, self.renderer.mapToGlobal(QPoint(int(screen.x), int(screen.y))), isFlatRendererCall=True)

    def _duplicate_instance(self):
        self.editor.undoStack.push(DuplicateCommand(self.editor.git(), self.editor.selectedInstances, self.editor))  # noqa: SLF001
        instance: GITInstance = deepcopy(self.editor.selectedInstances[-1])
        result = self.renderer.mapFromGlobal(self.renderer.cursor().pos())
        instance.position = self.renderer.toWorldCoords(result.x(), result.y())
        self.editor.git().add(instance)
        self.editor.rebuildInstanceList()
        self.editor.setSelection([instance])

    def onKeyboardPressed(self, buttons: set[int], keys: set[int]):
        """Handle keyboard input in the editor.

        Args:
        ----
            buttons: {Set of pressed button codes}
            keys: {Set of pressed key codes}.

        Processing Logic:
        ----------------
            - Check if delete selection shortcut satisfied and call editor delete selection
            - Check if snap camera to selection shortcut satisfied and snap camera to first selected instance
            - Check if toggle instance lock shortcut satisfied and toggle lock instances checkbox
        """
        if self.deleteSelected.satisfied(buttons, keys):
            RobustRootLogger().debug(f"Mode {self._mode.__class__.__name__}: moduleDesignerControls2d deleteSelected satisfied ")
            if isinstance(self._mode, _GeometryMode):
                self._mode.deleteSelected()
                return
            self.editor.deleteSelected()

        if self.snapCameraToSelected.satisfied(buttons, keys):
            RobustRootLogger().debug(f"Mode {self._mode.__class__.__name__}: moduleDesignerControls2d snapToCamera satisfied ")
            for instance in self.editor.selectedInstances:
                self.renderer.snapCameraToPoint(instance.position)
                break

        if self.toggleInstanceLock.satisfied(buttons, keys):
            self.editor.ui.lockInstancesCheck.setChecked(not self.editor.ui.lockInstancesCheck.isChecked())

    def onMouseReleased(self, screen: Vector2, buttons: set[int], keys: set[int]):
        self.editor.handleUndoRedoFromLongActionFinished()

    def onKeyboardReleased(self, buttons: set[int], keys: set[int]):
        self.editor.handleUndoRedoFromLongActionFinished()
