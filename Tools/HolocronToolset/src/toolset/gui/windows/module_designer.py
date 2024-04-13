from __future__ import annotations

import math

from copy import deepcopy
from typing import TYPE_CHECKING

import qtpy

from qtpy import QtCore
from qtpy.QtCore import QPoint, QTimer
from qtpy.QtGui import QColor, QIcon, QPixmap
from qtpy.QtWidgets import QAction, QListWidgetItem, QMainWindow, QMenu, QMessageBox, QTreeWidgetItem, QUndoCommand, QUndoStack

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
from toolset.gui.editors.git import openInstanceDialog
from toolset.gui.widgets.settings.installations import GlobalSettings
from toolset.gui.widgets.settings.module_designer import ModuleDesignerSettings
from toolset.gui.windows.help import HelpWindow
from toolset.utils.misc import QtMouse
from toolset.utils.window import openResourceEditor
from utility.error_handling import assert_with_variable_trace, safe_repr
from utility.logger_util import get_root_logger

if TYPE_CHECKING:
    from glm import vec3
    from qtpy.QtGui import QFont, QKeyEvent
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


class MoveCommand(QUndoCommand):
    def __init__(
        self,
        instance: GITInstance,
        old_position: Vector3,
        new_position: Vector3,
    ):
        print(f"Init movecommand with instance {instance.resref}")
        super().__init__()
        self.instance: GITInstance = instance
        self.old_position: Vector3 = old_position
        self.new_position: Vector3 = new_position

    def undo(self):
        print("Undo position")
        self.instance.position = self.old_position

    def redo(self):
        print("Redo position")
        self.instance.position = self.new_position


class RotateCommand(QUndoCommand):
    def __init__(
        self,
        instance: GITInstance,
        old_yaw: float,
        old_pitch: float,
        old_roll: float,
        new_yaw: float,
        new_pitch: float,
        new_roll: float
    ):
        print(f"Init rotatecommand with instance {instance.resref}")
        self.is_super_call = True
        super().__init__()
        self.instance: GITInstance = instance
        self.old_yaw: float = old_yaw
        self.old_pitch: float = old_pitch
        self.old_roll: float = old_roll
        self.new_yaw: float = new_yaw
        self.new_pitch: float = new_pitch
        self.new_roll: float = new_roll

    def undo(self):
        print(f"Undo rotation: {self.instance.resref}")
        self.instance.rotate(self.old_yaw, self.old_pitch, self.old_roll)

    def redo(self):
        if self.is_super_call:  # This is required because the rotate function doesn't appear to be 100% accurate
            print("Redo rotation called by super/qt, ignoring")
            self.is_super_call = False
            return
        print(f"Redo rotation: {self.instance.resref}")
        self.instance.rotate(self.new_yaw, self.new_pitch, self.new_roll)


class OrientationCommand(QUndoCommand):
    def __init__(
        self,
        instance: GITCamera,
        old_x: float,
        old_y: float,
        old_z: float,
        old_w: float,
        new_x: float,
        new_y: float,
        new_z: float,
        new_w: float,
    ):
        print(f"Init orientation with instance {instance.resref}")
        self.is_super_call = True
        super().__init__()
        self.instance: GITCamera = instance
        self.old_x: float = old_x
        self.old_y: float = old_y
        self.old_z: float = old_z
        self.old_w: float = old_w
        self.new_x: float = new_x
        self.new_y: float = new_y
        self.new_z: float = new_z
        self.new_w: float = new_w

    def undo(self):
        print(f"Undo orientation: {self.instance.resref}")
        self.instance.orientation = Vector4.from_euler(self.old_x, self.old_y, self.old_z, self.old_w)

    def redo(self):
        print(f"Redo orientation: {self.instance.resref}")
        self.instance.orientation = Vector4.from_euler(self.new_x, self.new_y, self.new_z, self.new_w)


class ModuleDesigner(QMainWindow):
    def __init__(self, parent: QWidget | None, installation: HTInstallation, mod_filepath: Path | None = None):
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

        self._installation: HTInstallation = installation
        self._module: Module | None = None

        self.initialPositions: dict[GITInstance, Vector3] = {}
        self.initialRotations: dict[GITInstance, Vector3] = {}
        self.undoStack = QUndoStack(self)

        self.selectedInstances: list[GITInstance] = []
        self.settings: ModuleDesignerSettings = ModuleDesignerSettings()
        self.log = get_root_logger()

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

        self.ui = Ui_MainWindow()
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

        self._controls3d: ModuleDesignerControls3d | ModuleDesignerControlsFreeCam = ModuleDesignerControls3d(self, self.ui.mainRenderer)
        self._controls2d: ModuleDesignerControls2d = ModuleDesignerControls2d(self, self.ui.flatRenderer)

        self._refreshWindowTitle()
        self.rebuildResourceTree()
        self.rebuildInstanceList()

        if mod_filepath is None:  # Use singleShot timer so the ui window opens while the loading is happening.
            QTimer().singleShot(33, self.openModuleWithDialog)
        else:
            self.openModule(mod_filepath)  # for some reason 3d rendering never loads when this is used...

    def closeEvent(self, event):
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

        self.ui.mainRenderer.sceneInitalized.connect(self.on3dSceneInitialized)
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
            title = f"{self._module.get_id()} - {self._installation.name} - Module Designer"
        self.setWindowTitle(title)

    def openModuleWithDialog(self):
        dialog = SelectModuleDialog(self, self._installation)

        if dialog.exec_():
            mod_filepath = self._installation.module_path().joinpath(f"{dialog.module}.mod")
            self.openModule(mod_filepath)

    #    @with_variable_trace(Exception)
    def openModule(self, mod_filepath: Path):
        """Opens a module."""

        def task() -> tuple[Module, GIT, list[BWM]]:
            # TODO: prompt/notify the user first at least before creating a .mod
            mod_root = self._installation.replace_module_extensions(mod_filepath)
            if GlobalSettings().disableRIMSaving and not mod_filepath.is_file():
                print(f"Converting {mod_filepath.name} to a .mod")
                module.rim_to_mod(mod_filepath)
                self._installation.reload_module(mod_root)

            new_module = Module(mod_root, self._installation)
            git: GIT | None = new_module.git().resource()
            assert git is not None, assert_with_variable_trace(git is not None, f"GIT file cannot be found in {new_module.get_id()}")
            walkmeshes: list[BWM] = []
            for bwm in new_module.resources.values():
                if bwm.restype() != ResourceType.WOK:
                    continue
                bwm_res: BWM | None = bwm.resource()
                if bwm_res is None:
                    print(f"bwm '{bwm.localized_name()}' '{bwm.resname()}.{bwm.restype()}' returned None resource data, skipping...")
                    continue
                print(f"Adding walkmesh '{bwm.localized_name()}' filename: '{bwm.resname()}.{bwm.restype()}'")
                walkmeshes.append(bwm_res)
            return (new_module, git, walkmeshes)

        self.unloadModule()
        loader = AsyncLoader(
            self,
            f"Loading '{mod_filepath.name}' into designer...",
            task,
            "Error occurred loading the module designer",
        )
        if loader.exec_():
            self.log.debug("ModuleDesigner.openModule Loader finished.")
            new_module, git, walkmeshes = loader.value
            self._module = new_module
            print("setGit")
            self.ui.flatRenderer.setGit(git)
            print("init mainRenderer")
            self.ui.mainRenderer.init(self._installation, new_module)
            print("set flatRenderer walkmeshes")
            self.ui.flatRenderer.setWalkmeshes(walkmeshes)
            self.ui.flatRenderer.centerCamera()
        else:
            self.log.info("ModuleDesigner.openModule Loader unexpected error?")

    def unloadModule(self):
        self._module = None
        self.ui.mainRenderer.scene = None
        self.ui.mainRenderer._init = False

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
            item.setData(0, QtCore.Qt.UserRole, resource)
            category = categories.get(resource.restype(), categories[ResourceType.INVALID])
            category.addChild(item)

        self.ui.resourceTree.sortByColumn(0, QtCore.Qt.AscendingOrder)
        self.ui.resourceTree.setSortingEnabled(True)

    def openModuleResource(self, resource: ModuleResource):
        editor: Editor | QMainWindow | None = openResourceEditor(resource.active(), resource.resname(), resource.restype(), resource.data(), self._installation, self)[1]

        if editor is None:
            QMessageBox(
                QMessageBox.Critical,
                "Failed to open editor",
                f"Failed to open editor for file: {resource.resname()}.{resource.restype().extension}",
            ).exec_()
        elif isinstance(editor, Editor):
            editor.savedFile.connect(lambda: self._onSavedResource(resource))

    def copyResourceToOverride(self, resource: ModuleResource):
        location: CaseAwarePath = self._installation.override_path() / f"{resource.resname()}.{resource.restype().extension}"
        BinaryWriter.dump(location, resource.data())
        resource.add_locations([location])
        resource.activate(location)
        self.ui.mainRenderer.scene.clearCacheBuffer.append(ResourceIdentifier(resource.resname(), resource.restype()))

    def activateResourceFile(self, resource: ModuleResource, location: str):
        resource.activate(location)
        self.ui.mainRenderer.scene.clearCacheBuffer.append(ResourceIdentifier(resource.resname(), resource.restype()))

    def selectResourceItem(self, instance: GITInstance, *, clearExisting: bool = True):
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
        if instance.identifier() is None:  # Should only ever be None for GITCamera.
            self.log.debug("Cannot select a resource for GITCamera instances: %s(%s)", instance, repr(instance))
            return

        for i in range(self.ui.resourceTree.topLevelItemCount()):
            parent: QTreeWidgetItem | None = self.ui.resourceTree.topLevelItem(i)
            if parent is None:
                self.log.debug("parent was None in ModuleDesigner.selectResourceItem()")
                continue
            for j in range(parent.childCount()):
                item = parent.child(j)
                res: ModuleResource = item.data(0, QtCore.Qt.UserRole)
                if not isinstance(res, ModuleResource):
                    self.log.debug("item.data(0, QtCore.Qt.UserRole) returned non ModuleResource in ModuleDesigner.selectResourceItem(): %s", safe_repr(res))
                    continue
                if res.identifier() != instance.identifier():
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
        self.ui.instanceList.clear()
        self.ui.instanceList.setEnabled(True)

        # Only build if module is loaded
        if self._module is None:
            self.ui.instanceList.setEnabled(False)
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
                item.setData(QtCore.Qt.UserRole + 1, "cam" + str(instance.camera_id).rjust(10, "0"))
            else:
                filename: str = instance.identifier().resname
                name: str = filename
                tag: str = ""
                resource: ModuleResource[ARE] | None = self._module.resource(instance.identifier().resname, instance.identifier().restype)

                resourceExists: bool = resource is not None and resource.resource() is not None
                if isinstance(instance, GITDoor) or (isinstance(instance, GITTrigger) and resourceExists):
                    # Tag is stored in the GIT
                    name = resource.localized_name() or filename
                    tag = instance.tag
                elif isinstance(instance, GITWaypoint):
                    # Name and tag are stored in the GIT
                    name = self._installation.string(instance.name)
                    tag = instance.tag
                elif resourceExists:
                    name = resource.localized_name() or filename
                    tag = resource.resource().tag

                if resource is None:
                    font.setItalic(True)

                item.setText(name)
                item.setToolTip(f"Struct Index: {struct_index}\nResRef: {filename}\nName: {name}\nTag: {tag}")
                item.setData(QtCore.Qt.UserRole + 1, instance.identifier().restype.extension + name)

            item.setFont(font)
            item.setData(QtCore.Qt.UserRole, instance)
            items.append(item)

        for item in sorted(items, key=lambda i: i.data(QtCore.Qt.UserRole + 1)):
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
            data: GITInstance = item.data(QtCore.Qt.UserRole)
            if data is instance:  # TODO(th3w1zard1): Don't trust data(role) lookups to match original python ids, should be checking __eq__ here.
                item.setSelected(True)
                self.ui.instanceList.scrollToItem(item)

    def updateToggles(self):
        self.hideCreatures = self.ui.mainRenderer.scene.hide_creatures = self.ui.flatRenderer.hideCreatures = not self.ui.viewCreatureCheck.isChecked()
        self.hidePlaceables = self.ui.mainRenderer.scene.hide_placeables = self.ui.flatRenderer.hidePlaceables = not self.ui.viewPlaceableCheck.isChecked()
        self.hideDoors = self.ui.mainRenderer.scene.hide_doors = self.ui.flatRenderer.hideDoors = not self.ui.viewDoorCheck.isChecked()
        self.hideTriggers = self.ui.mainRenderer.scene.hide_triggers = self.ui.flatRenderer.hideTriggers = not self.ui.viewTriggerCheck.isChecked()
        self.hideEncounters = self.ui.mainRenderer.scene.hide_encounters = self.ui.flatRenderer.hideEncounters = not self.ui.viewEncounterCheck.isChecked()
        self.hideWaypoints = self.ui.mainRenderer.scene.hide_waypoints = self.ui.flatRenderer.hideWaypoints = not self.ui.viewWaypointCheck.isChecked()
        self.hideSounds = self.ui.mainRenderer.scene.hide_sounds = self.ui.flatRenderer.hideSounds = not self.ui.viewSoundCheck.isChecked()
        self.hideStores = self.ui.mainRenderer.scene.hide_stores = self.ui.flatRenderer.hideStores = not self.ui.viewStoreCheck.isChecked()
        self.hideCameras = self.ui.mainRenderer.scene.hide_cameras = self.ui.flatRenderer.hideCameras = not self.ui.viewCameraCheck.isChecked()

        self.ui.mainRenderer.scene.backface_culling = self.ui.backfaceCheck.isChecked()
        self.ui.mainRenderer.scene.use_lightmap = self.ui.lightmapCheck.isChecked()
        self.ui.mainRenderer.scene.show_cursor = self.ui.cursorCheck.isChecked()

        self.rebuildInstanceList()

    #    @with_variable_trace(Exception)
    def addInstance(self, instance: GITInstance, *, walkmeshSnap: bool = True):
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
        instance.position.x = self.ui.mainRenderer.scene.cursor.position().x
        instance.position.y = self.ui.mainRenderer.scene.cursor.position().y
        instance.position.z = self.ui.mainRenderer.scene.cursor.position().z

        if not isinstance(instance, GITCamera):
            assert self._module is not None
            dialog = InsertInstanceDialog(self, self._installation, self._module, instance.identifier().restype)

            if dialog.exec_():
                self.rebuildResourceTree()
                instance.resref = ResRef(dialog.resname)  # type: ignore[reportAttributeAccessIssue]
                self._module.git().resource().add(instance)
        else:
            self._module.git().resource().add(instance)
        self.rebuildInstanceList()

    #    @with_variable_trace()
    def editInstance(self, instance: GITInstance):
        if openInstanceDialog(self, instance, self._installation):
            if not isinstance(instance, GITCamera):
                ident = instance.identifier()
                assert ident is not None, "identifier() returned None for a non-GITCamera instance?"
                self.ui.mainRenderer.scene.clearCacheBuffer.append(ident)
            self.rebuildInstanceList()

    def snapCameraToView(self, instance: GITCamera):
        scene = self.ui.mainRenderer.scene
        assert scene is not None
        view: vec3 = scene.camera.true_position()
        rot: Camera = scene.camera
        old_pitch = instance.pitch
        instance.pitch = 0
        instance.height = 0
        old_position = instance.position
        new_position = Vector3(view.x, view.y, view.z)
        self.undoStack.push(MoveCommand(instance, old_position, new_position))
        instance.position = new_position

        print("Create the RotateCommand for undo/redo functionality")
        rotate_command = RotateCommand(instance, 0, old_pitch, 0, 0, 0, 0)
        self.undoStack.push(rotate_command)
        new_orientation = Vector4.from_euler(math.pi / 2 - rot.yaw, 0, math.pi - rot.pitch)
        old_orientation = instance.orientation
        orientation_command = OrientationCommand(instance, *old_orientation, *new_orientation)
        self.undoStack.push(orientation_command)

    def snapViewToGITCamera(self, instance: GITCamera):
        scene = self.ui.mainRenderer.scene
        assert scene is not None
        camera: Camera = scene.camera
        euler: Vector3 = instance.orientation.to_euler()
        camera.pitch = math.pi - euler.z - math.radians(instance.pitch)
        camera.yaw = math.pi / 2 - euler.x
        camera.x = instance.position.x
        camera.y = instance.position.y
        camera.z = instance.position.z + instance.height
        camera.distance = 0

    def snapCameraToEntryLocation(self):
        scene = self.ui.mainRenderer.scene
        assert scene is not None
        scene.camera.x = self.ifo().entry_position.x
        scene.camera.y = self.ifo().entry_position.y
        scene.camera.z = self.ifo().entry_position.z

    def toggleFreeCam(self):
        if isinstance(self._controls3d, ModuleDesignerControls3d):
            print("Enabling free cam")
            self._controls3d = ModuleDesignerControlsFreeCam(self, self.ui.mainRenderer)
        else:
            print("Disable free cam")
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

    def moveSelected(self, x: float, y: float, z: float | None = None, noUndoStack: bool = False, noZCoord: bool = False):
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
            print("Moving", instance.resref)
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

        for instance in self.selectedInstances:  # HACK: I have no idea what's going on with the rotation here, but this incorporates the old logic.
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
        print("handleUndoRedoFromLongActionFinished()")
        # Check if we were dragging
        if self.isDragMoving:
            for instance, old_position in self.initialPositions.items():
                new_position = instance.position
                if old_position and new_position != old_position:
                    print("3d Create the MoveCommand for undo/redo functionality")
                    move_command = MoveCommand(instance, old_position, new_position)
                    self.undoStack.push(move_command)
                elif not old_position:
                    print(f"3d No old position for {instance.resref}")
                else:
                    print(f"3d Both old and new positions are the same for {instance.resref}")

            # Reset for the next drag operation
            self.initialPositions.clear()
            print("No longer drag moving 3d")
            self.isDragMoving = False

        if self.isDragRotating:
            for instance, old_rotation in self.initialRotations.items():
                old_yaw, old_pitch, old_roll = old_rotation
                new_yaw = instance.yaw() or 0
                new_pitch = instance.get_pitch() if hasattr(instance, "get_pitch") else 0  # type: ignore[]
                new_roll = instance.get_roll() if hasattr(instance, "get_roll") else 0  # type: ignore[]
                new_rotation = Vector3(new_yaw, new_pitch, new_roll)
                if old_rotation and new_rotation != old_rotation:
                    print("Create the RotateCommand for undo/redo functionality")
                    rotate_command = RotateCommand(instance, old_yaw, old_pitch, old_roll, new_yaw, new_pitch, new_roll)
                    self.undoStack.push(rotate_command)
                    print("Push stack")
                elif not old_rotation:
                    print(f"No old rotation for {instance.resref}")
                else:
                    print(f"Both old and new rotations are the same for {instance.resref}")

            # Reset for the next drag operation
            self.initialRotations.clear()
            print("No longer drag rotating 3d")
            self.isDragRotating = False

    def onInstanceListDoubleClicked(self):
        if self.ui.instanceList.selectedItems():
            item: QListWidgetItem = self.ui.instanceList.selectedItems()[0]
            instance: GITInstance = item.data(QtCore.Qt.UserRole)
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

    def onResourceTreeContextMenu(self, point: QPoint):
        menu = QMenu(self)

        data = self.ui.resourceTree.currentItem().data(0, QtCore.Qt.UserRole)
        if isinstance(data, ModuleResource):
            self._build_active_override_menu(data, menu)
        menu.exec_(self.ui.resourceTree.mapToGlobal(point))

    def _build_active_override_menu(self, data: ModuleResource, menu: QMenu):
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
        copyToOverrideAction.triggered.connect(lambda _, r=data: self.copyResourceToOverride(r))

        menu.addAction("Edit Active File").triggered.connect(lambda _, r=data: self.openModuleResource(r))
        menu.addAction("Reload Active File").triggered.connect(lambda _: data.reload())
        menu.addAction(copyToOverrideAction)
        menu.addSeparator()
        for location in data.locations():
            locationAction = QAction(str(location), self)
            locationAction.triggered.connect(lambda _, loc=location: self.activateResourceFile(data, loc))
            if location == data.active():
                locationAction.setEnabled(False)
            lowercase_parts: list[str] = [part.lower() for part in location.parts]
            if "override" in lowercase_parts:
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

    def onContextMenu(self, world: Vector3, point: QPoint):
        if self._module is None:
            return

        if len(self.ui.mainRenderer.scene.selection) == 0:
            self.onContextMenuSelectionNone(world)
        else:
            self.onContextMenuSelectionExists()

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
        menu.addAction("Insert Camera at View").triggered.connect(lambda: self.addInstance(GITCamera(view.x, view.y, view.z, rot.yaw, rot.pitch, 0, 0), walkmeshSnap=False))
        menu.addSeparator()
        menu.addAction("Insert Creature").triggered.connect(lambda: self.addInstance(GITCreature(*world), walkmeshSnap=True))
        menu.addAction("Insert Door").triggered.connect(lambda: self.addInstance(GITDoor(*world), walkmeshSnap=False))
        menu.addAction("Insert Placeable").triggered.connect(lambda: self.addInstance(GITPlaceable(*world), walkmeshSnap=False))
        menu.addAction("Insert Store").triggered.connect(lambda: self.addInstance(GITStore(*world), walkmeshSnap=False))
        menu.addAction("Insert Sound").triggered.connect(lambda: self.addInstance(GITSound(*world), walkmeshSnap=False))
        menu.addAction("Insert Waypoint").triggered.connect(lambda: self.addInstance(GITWaypoint(*world), walkmeshSnap=False))
        menu.addAction("Insert Encounter").triggered.connect(lambda: self.addInstance(GITEncounter(*world), walkmeshSnap=False))
        menu.addAction("Insert Trigger").triggered.connect(lambda: self.addInstance(GITTrigger(*world), walkmeshSnap=False))

        menu.popup(self.cursor().pos())
        menu.aboutToHide.connect(self.ui.mainRenderer.resetMouseButtons)

    def onContextMenuSelectionExists(self):
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
        menu = QMenu(self)

        if self.selectedInstances:
            instance = self.selectedInstances[0]
            if isinstance(instance, GITCamera):
                menu.addAction("Snap Camera to 3D View").triggered.connect(lambda: self.snapCameraToView(instance))
                menu.addAction("Snap 3D View to Camera").triggered.connect(lambda: self.snapViewToGITCamera(instance))
                menu.addSeparator()

            menu.addAction("Copy position to clipboard").triggered.connect(lambda: self.copyInstancePosition(instance))
            menu.addAction("Edit Instance").triggered.connect(lambda: self.editInstance(instance))
            menu.addAction("Remove").triggered.connect(self.deleteSelected)

        menu.popup(self.cursor().pos())
        menu.aboutToHide.connect(self.ui.mainRenderer.resetMouseButtons)

    def copyInstancePosition(self, instance: GITInstance):
        print("Copied instance position to clipboard", instance.resref)
        position_str = str(instance.position)
        pyperclip.copy(position_str)

    def on3dSceneInitialized(self):
        self.rebuildResourceTree()
        self.rebuildInstanceList()
        self._refreshWindowTitle()
        self.updateToggles()

    def on2dMouseMoved(self, screen: Vector2, delta: Vector2, buttons: set[int], keys: set[int]):
        worldDelta: Vector2 = self.ui.flatRenderer.toWorldDelta(delta.x, delta.y)
        world: Vector3 = self.ui.flatRenderer.toWorldCoords(screen.x, screen.y)
        self._controls2d.onMouseMoved(screen, delta, Vector2.from_vector3(world), worldDelta, buttons, keys)

    def on2dMouseReleased(self, screen: Vector2, buttons: set[int], keys: set[int]):
        self._controls2d.onMouseReleased(screen, buttons, keys)

    def on2dKeyboardReleased(self, buttons: set[int], keys: set[int]):
        self._controls2d.onKeyboardReleased(buttons, keys)

    def on2dMouseScrolled(self, delta: Vector2, buttons: set[int], keys: set[int]):
        self._controls2d.onMouseScrolled(delta, buttons, keys)

    def on2dMousePressed(self, screen: Vector2, buttons: set[int], keys: set[int]):
        self._controls2d.onMousePressed(screen, buttons, keys)

    def on2dKeyboardPressed(self, buttons: set[int], keys: set[int]):
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
        self.openContextMenu: ControlItem = ControlItem((set(), {QtMouse.RightButton}))
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

        if self.renderer.scene is not None:
            self.renderer.scene.show_cursor = self.editor.ui.cursorCheck.isChecked()
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

        Processing Logic:
        ----------------
            - Moves camera if moveXYCamera or moveCameraPlane bindings are satisfied based on screenDelta
            - Rotates camera if rotateCamera binding is satisfied based on screenDelta
            - Zooms camera if zoomCameraMM binding is satisfied based on screenDelta
            - Moves selected instances if moveXYSelected or moveZSelected bindings are satisfied based on screenDelta and position
            - Rotates selected instances if rotateSelected binding is satisfied based on screenDelta
        """
        if self.moveXYCamera.satisfied(buttons, keys):
            forward = -screenDelta.y * self.renderer.scene.camera.forward()
            sideward = screenDelta.x * self.renderer.scene.camera.sideward()
            strength = self.settings.moveCameraSensitivity3d / 1000
            self.renderer.scene.camera.x -= (forward.x + sideward.x) * strength
            self.renderer.scene.camera.y -= (forward.y + sideward.y) * strength

        if self.moveCameraPlane.satisfied(buttons, keys):  # sourcery skip: extract-method
            upward = screenDelta.y * self.renderer.scene.camera.upward(ignore_z=False)
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
            strength = self.settings.zoomCameraSensitivity3d / 5000
            self.renderer.scene.camera.distance -= screenDelta.y * strength

        if self.moveXYSelected.satisfied(buttons, keys):
            if self.editor.ui.lockInstancesCheck.isChecked():
                return

            if not self.editor.isDragMoving:
                self.editor.initialPositions = {instance: instance.position for instance in self.editor.selectedInstances}
                self.editor.isDragMoving = True
            for instance in self.editor.selectedInstances:
                print("Moving instance 3d", instance.resref)
                scene = self.renderer.scene
                assert scene is not None

                x = scene.cursor.position().x
                y = scene.cursor.position().y
                z = instance.position.z if isinstance(instance, GITCamera) else scene.cursor.position().z
                instance.position = Vector3(x, y, z)

        if self.moveZSelected.satisfied(buttons, keys):
            for instance in self.editor.selectedInstances:
                instance.position.z -= screenDelta.y / 40

        if self.rotateSelected.satisfied(buttons, keys):
            if not self.editor.isDragRotating and not self.editor.ui.lockInstancesCheck.isChecked():
                print("rotateSelected instance in 3d")
                for instance in self.editor.selectedInstances:
                    old_yaw = instance.yaw()
                    if old_yaw is None:
                        print(instance.resref, "does not support rotating yaw")
                        continue
                    old_pitch = instance.pitch() if hasattr(instance, "pitch") else 0  # type: ignore[]
                    old_roll = instance.roll() if hasattr(instance, "roll") else 0  # type: ignore[]
                    old_rotation = Vector3(old_yaw, old_pitch, old_roll)
                    self.editor.initialRotations[instance] = old_rotation
                print("3d rotate set isDragRotating")
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
            scene = self.renderer.scene
            assert scene is not None
            camera = scene.camera
            camera.x = scene.cursor.position().x
            camera.y = scene.cursor.position().y
            camera.z = scene.cursor.position().z
        if self.moveCameraToEntryPoint.satisfied(buttons, keys):
            self.editor.snapCameraToEntryLocation()

        if self.deleteSelected.satisfied(buttons, keys):
            self.editor.deleteSelected()

        if self.rotateCameraLeft.satisfied(buttons, keys):
            print("rotateCameraLeft")
            self.renderer.rotateCamera(math.pi / 4, 0)
        if self.rotateCameraRight.satisfied(buttons, keys):
            print("rotateCameraRight")
            self.renderer.rotateCamera(-math.pi / 4, 0)
        if self.rotateCameraUp.satisfied(buttons, keys):
            print("rotateCameraUp")
            self.renderer.rotateCamera(0, math.pi / 4)
        if self.rotateCameraDown.satisfied(buttons, keys):
            print("rotateCameraDown")
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

        self.renderer.scene.show_cursor = False
        self.renderer.freeCam = True
        self.renderer.setCursor(QtCore.Qt.CursorShape.BlankCursor)
        self.renderer._keysDown.clear()

        rendererPos = self.renderer.mapToGlobal(self.renderer.pos())
        mouseX = rendererPos.x() + self.renderer.width() // 2
        mouseY = rendererPos.y() + self.renderer.height() // 2
        self.renderer.cursor().setPos(mouseX, mouseY)

    def onMouseScrolled(self, delta: Vector2, buttons: set[int], keys: set[int]): ...

    def onMouseMoved(self, screen: Vector2, screenDelta: Vector2, world: Vector3, buttons: set[int], keys: set[int]):
        rendererPos = self.renderer.mapToGlobal(self.renderer.pos())
        mouseX: int = rendererPos.x() + self.renderer.width() // 2
        mouseY: int = rendererPos.y() + self.renderer.height() // 2
        strength: float = self.settings.rotateCameraSensitivityFC / 10000

        print ("onMouseMoved, next call is rotateCamera.")
        self.renderer.rotateCamera(-screenDelta.x * strength, screenDelta.y * strength, snapRotations=False)
        self.renderer.cursor().setPos(mouseX, mouseY)

    def onMousePressed(self, screen: Vector2, buttons: set[int], keys: set[int]): ...

    def onMouseReleased(self, screen: Vector2, buttons: set[int], keys: set[int]): ...

    def onKeyboardPressed(self, buttons: set[int], keys: set[int]):
        if self.toggleFreeCam.satisfied(buttons, keys):
            self.editor.toggleFreeCam()

        strength = self.settings.flyCameraSpeedFC / 100
        if self.moveCameraUp.satisfied(buttons, keys, exactKeys=False):
            self.renderer.moveCamera(0, 0, strength)
        if self.moveCameraDown.satisfied(buttons, keys, exactKeys=False):
            self.renderer.moveCamera(0, 0, -strength)
        if self.moveCameraLeft.satisfied(buttons, keys, exactKeys=False):
            self.renderer.moveCamera(0, -strength, 0)
        if self.moveCameraRight.satisfied(buttons, keys, exactKeys=False):
            self.renderer.moveCamera(0, strength, 0)
        if self.moveCameraForward.satisfied(buttons, keys, exactKeys=False):
            self.renderer.moveCamera(strength, 0, 0)
        if self.moveCameraBackward.satisfied(buttons, keys, exactKeys=False):
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
        if self.zoomCamera.satisfied(buttons, keys):
            strength: float = self.settings.moveCameraSensitivity2d / 100 / 50
            zoomInFactor = 1.1
            zoomOutFactor = 0.90

            zoomFactor: float = zoomInFactor if delta.y > 0 else zoomOutFactor
            self.renderer.camera.nudgeZoom(delta.y * zoomFactor * strength)

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
            buttons: set[int] - Mouse buttons currently held down
            keys: set[int] - Keyboard keys currently held down

        Processing Logic:
        ----------------
            - Nudges camera position if move camera key is held based on worldDelta
            - Nudges camera rotation if rotate camera key is held based on screenDelta
            - Moves selected instances by worldDelta if move selected key is held
            - Rotates selected instances around world position if rotate selected key is held.
        """
        if self.moveCamera.satisfied(buttons, keys):
            strength = self.settings.moveCameraSensitivity2d / 100
            self.renderer.camera.nudgePosition(-worldDelta.x * strength, -worldDelta.y * strength)

        if self.rotateCamera.satisfied(buttons, keys):
            strength = self.settings.rotateCameraSensitivity2d / 100 / 50
            self.renderer.camera.nudgeRotation(screenDelta.x * strength)

        if self.moveSelected.satisfied(buttons, keys):
            if not self.editor.isDragMoving:
                print("moveSelected instance in 2d")
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
                    print("rotateSelected instance in 2d")
                    old_pitch = instance.pitch() if hasattr(instance, "pitch") else 0  # type: ignore[]
                    old_roll = instance.roll() if hasattr(instance, "roll") else 0  # type: ignore[]
                    old_rotation = Vector3(old_yaw, old_pitch, old_roll)
                    self.editor.initialRotations[instance] = old_rotation

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
        if self.selectUnderneath.satisfied(buttons, keys):
            if self.renderer.instancesUnderMouse():
                self.editor.setSelection([self.renderer.instancesUnderMouse()[-1]])
            else:
                self.editor.setSelection([])

        if self.duplicateSelected.satisfied(buttons, keys) and self.editor.selectedInstances:
            self._duplicate_instance()  # TODO: undo/redo support
        if self.openContextMenu.satisfied(buttons, keys):
            world: Vector3 = self.renderer.toWorldCoords(screen.x, screen.y)
            self.editor.onContextMenu(world, self.renderer.mapToGlobal(QPoint(int(screen.x), int(screen.y))))

    def _duplicate_instance(self):
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
            self.editor.deleteSelected()

        if self.snapCameraToSelected.satisfied(buttons, keys):
            for instance in self.editor.selectedInstances:
                self.renderer.snapCameraToPoint(instance.position)
                break

        if self.toggleInstanceLock.satisfied(buttons, keys):
            self.editor.ui.lockInstancesCheck.setChecked(not self.editor.ui.lockInstancesCheck.isChecked())

    def onMouseReleased(self, screen: Vector2, buttons: set[int], keys: set[int]):
        self.editor.handleUndoRedoFromLongActionFinished()

    def onKeyboardReleased(self, buttons: set[int], keys: set[int]):
        self.editor.handleUndoRedoFromLongActionFinished()
