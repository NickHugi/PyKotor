from __future__ import annotations

import math
from copy import deepcopy
from typing import TYPE_CHECKING

from PyQt5 import QtCore
from PyQt5.QtCore import QPoint, QTimer
from PyQt5.QtGui import QColor, QIcon, QKeyEvent, QPixmap
from PyQt5.QtWidgets import QAction, QCheckBox, QListWidgetItem, QMainWindow, QMenu, QMessageBox, QTreeWidgetItem, QWidget

from pykotor.common.geometry import SurfaceMaterial, Vector2, Vector3, Vector4
from pykotor.common.misc import Color, ResRef
from pykotor.common.module import Module, ModuleResource
from pykotor.common.stream import BinaryWriter
from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.generics.are import ARE
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
)
from pykotor.resource.generics.ifo import IFO
from pykotor.resource.generics.utd import read_utd
from pykotor.resource.generics.utt import read_utt
from pykotor.resource.generics.utw import read_utw
from pykotor.resource.type import ResourceType
from pykotor.tools import module
from toolset.data.misc import ControlItem
from toolset.gui.dialogs.insert_instance import InsertInstanceDialog
from toolset.gui.dialogs.select_module import SelectModuleDialog
from toolset.gui.editors.git import openInstanceDialog
from toolset.gui.widgets.settings.installations import GlobalSettings
from toolset.gui.widgets.settings.module_designer import ModuleDesignerSettings
from toolset.gui.windows.help import HelpWindow
from toolset.utils.misc import QtMouse
from toolset.utils.window import openResourceEditor

if TYPE_CHECKING:
    from toolset.data.installation import HTInstallation
    from toolset.gui.widgets.renderer.module import ModuleRenderer
    from toolset.gui.widgets.renderer.walkmesh import WalkmeshRenderer


class ModuleDesigner(QMainWindow):
    def __init__(self, parent: QWidget | None, installation: HTInstallation):
        """Initializes the Module Designer window
        Args:
            parent: Optional[QWidget]: Parent widget
            installation: HTInstallation: Hometuck installation
        Returns:
            None
        Processing Logic:
            - Initializes UI elements and connects signals
            - Sets up 3D and 2D renderer controls
            - Populates resource tree and instance list
            - Sets window title and loads module on next frame.
        """
        super().__init__(parent)

        self._installation: HTInstallation = installation
        self._module: Module | None = None

        self.selectedInstances: list[GITInstance] = []
        self.settings: ModuleDesignerSettings = ModuleDesignerSettings()

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

        from toolset.uic.windows.module_designer import Ui_MainWindow

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupSignals()

        def intColorToQColor(intvalue):
            """Converts an integer color value to a QColor object
            Args:
                intvalue: Integer color value
            Returns:
                QColor: QColor object representing the color
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

        self._controls3d: ModuleDesignerControls3d = ModuleDesignerControls3d(self, self.ui.mainRenderer)
        self._controls2d: ModuleDesignerControls2d = ModuleDesignerControls2d(self, self.ui.flatRenderer)

        self._refreshWindowTitle()
        self.rebuildResourceTree()
        self.rebuildInstanceList()

        QTimer().singleShot(33, self.openModule)

    def _setupSignals(self) -> None:
        """Connect signals to slots
        Args:
            self: {The class instance}: Connects signals from UI elements to methods
        Returns:
            None: No return value
        Processing Logic:
            - Connect menu actions to methods like open, save
            - Connect toggles of instance visibility checks to update method
            - Connect double clicks on checks and instance list to methods
            - Connect 3D renderer signals to mouse, key methods
            - Connect 2D renderer signals to mouse, key methods.
        """
        self.ui.actionOpen.triggered.connect(self.openModule)
        self.ui.actionSave.triggered.connect(self.saveGit)
        self.ui.actionInstructions.triggered.connect(self.showHelpWindow)

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

        self.ui.viewCreatureCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick(self.ui.viewCreatureCheck)
        self.ui.viewPlaceableCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick(self.ui.viewPlaceableCheck)
        self.ui.viewDoorCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick(self.ui.viewDoorCheck)
        self.ui.viewSoundCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick(self.ui.viewSoundCheck)
        self.ui.viewTriggerCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick(self.ui.viewTriggerCheck)
        self.ui.viewEncounterCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick(self.ui.viewEncounterCheck)
        self.ui.viewWaypointCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick(self.ui.viewWaypointCheck)
        self.ui.viewCameraCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick(self.ui.viewCameraCheck)
        self.ui.viewStoreCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisibilityDoubleClick(self.ui.viewStoreCheck)

        self.ui.instanceList.doubleClicked.connect(self.onInstanceListDoubleClicked)
        self.ui.instanceList.customContextMenuRequested.connect(self.onContextMenuSelectionExists)

        self.ui.mainRenderer.sceneInitalized.connect(self.on3dSceneInitialized)
        self.ui.mainRenderer.mousePressed.connect(self.on3dMousePressed)
        self.ui.mainRenderer.mouseMoved.connect(self.on3dMouseMoved)
        self.ui.mainRenderer.mouseScrolled.connect(self.on3dMouseScrolled)
        self.ui.mainRenderer.keyboardPressed.connect(self.on3dKeyboardPressed)
        self.ui.mainRenderer.objectSelected.connect(self.on3dObjectSelected)

        self.ui.flatRenderer.mousePressed.connect(self.on2dMousePressed)
        self.ui.flatRenderer.mouseMoved.connect(self.on2dMouseMoved)
        self.ui.flatRenderer.mouseScrolled.connect(self.on2dMouseScrolled)
        self.ui.flatRenderer.keyPressed.connect(self.on2dKeyboardPressed)

    def _refreshWindowTitle(self) -> None:
        if self._module is None:
            title = f"No Module - {self._installation.name} - Module Designer"
        else:
            title = f"{self._module._id} - {self._installation.name} - Module Designer"
        self.setWindowTitle(title)

    def openModule(self) -> None:
        """Opens a module
        Args:
            self: The class instance
            dialog: The dialog to select a module
        Returns:
            None: Does not return anything
        Processing Logic:
            - Unloads any currently loaded module
            - Gets the selected module filepath
            - Converts RIM file to mod if saving is disabled
            - Loads the selected module into the installation
            - Initializes the main renderer with the new module
            - Sets the flat renderer resources from the new module.
        """
        dialog = SelectModuleDialog(self, self._installation)

        if dialog.exec_():
            self.unloadModule()

            mod_filepath = self._installation.module_path().joinpath(f"{dialog.module}.mod")
            if not mod_filepath.exists() and GlobalSettings().disableRIMSaving:
                module.rim_to_mod(mod_filepath)
                self._installation.load_modules()

            self._module = Module(dialog.module, self._installation)
            self.ui.mainRenderer.init(self._installation, self._module)

            self.ui.flatRenderer.setGit(self._module.git().resource())
            self.ui.flatRenderer.setWalkmeshes(
                [bwm.resource() for bwm in self._module.resources.values() if bwm.restype() == ResourceType.WOK],
            )
            self.ui.flatRenderer.centerCamera()

    def unloadModule(self) -> None:
        self._module = None
        self.ui.mainRenderer.scene = None
        self.ui.mainRenderer._init = False

    def showHelpWindow(self) -> None:
        window = HelpWindow(self, "./help/tools/1-moduleEditor.md")
        window.show()

    def git(self) -> GIT:
        return self._module.git().resource()

    def are(self) -> ARE:
        return self._module.are().resource()

    def ifo(self) -> IFO:
        return self._module.info().resource()

    def saveGit(self) -> None:
        self._module.git().save()

    def rebuildResourceTree(self) -> None:
        """Rebuilds the resource tree widget
        Args:
            self: The class instance
        Returns:
            None
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

    def openModuleResource(self, resource: ModuleResource) -> None:
        editor = openResourceEditor(resource.active(), resource.resname(), resource.restype(), resource.data(),
                                    self._installation, self)[1]

        if editor is None:
            QMessageBox(
                QMessageBox.Critical,
                "Failed to open editor",
                f"Failed to open editor for file: {resource.resname()}.{resource.restype().extension}",
            )
        else:
            editor.savedFile.connect(lambda: self._onSavedResource(resource))

    def copyResourceToOverride(self, resource: ModuleResource) -> None:
        location = self._installation.override_path() / f"{resource.resname()}.{resource.restype().extension}"
        BinaryWriter.dump(location, resource.data())
        resource.add_locations([location])
        resource.activate(location)
        self.ui.mainRenderer.scene.clearCacheBuffer.append(ResourceIdentifier(resource.resname(), resource.restype()))

    def activateResourceFile(self, resource: ModuleResource, location: str) -> None:
        resource.activate(location)
        self.ui.mainRenderer.scene.clearCacheBuffer.append(ResourceIdentifier(resource.resname(), resource.restype()))

    def selectResourceItem(self, instance: GITInstance, clearExisting: bool = True) -> None:
        """Select a resource item in the tree
        Args:
            instance: {The GIT instance to select}
            clearExisting: {Clear existing selections if True}.

        Returns
        -------
            None
        Processing Logic:
            1. Clear selection if clearExisting is True
            2. Iterate through top level items
            3. Iterate through child items of each top level
            4. Check if instance matches item and select it.
        """
        if clearExisting:
            self.ui.resourceTree.clearSelection()

        for i in range(self.ui.resourceTree.topLevelItemCount()):
            parent = self.ui.resourceTree.topLevelItem(i)
            for j in range(parent.childCount()):
                item = parent.child(j)
                res: ModuleResource = item.data(0, QtCore.Qt.UserRole)
                if (
                    instance.identifier() is not None
                    and res.resname() == instance.identifier().resname
                    and res.restype() == instance.identifier().restype
                ):
                    parent.setExpanded(True)
                    item.setSelected(True)
                    self.ui.resourceTree.scrollToItem(item)

    def rebuildInstanceList(self) -> None:
        """Rebuilds the instance list
        Args:
            self: The class instance
        Returns:
            None
        Rebuilding Logic:
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
        items = []

        for instance in self._module.git().resource().instances():
            if visibleMapping[type(instance)]:
                continue

            struct_index = self._module.git().resource().index(instance)

            icon = QIcon(iconMapping[type(instance)])
            item = QListWidgetItem(icon, "")
            font = item.font()

            if isinstance(instance, GITCamera):
                item.setText(f"Camera #{instance.camera_id}")
                item.setToolTip(f"Struct Index: {struct_index}\nCamera ID: {instance.camera_id}\nFOV: {instance.fov}")
                item.setData(QtCore.Qt.UserRole + 1, "cam" + str(instance.camera_id).rjust(10, "0"))
            else:
                resource = self._module.resource(instance.identifier().resname, instance.identifier().restype)
                resourceExists = resource is not None and resource.resource() is not None
                resref = instance.identifier().resname
                name = resref
                tag = ""

                if isinstance(instance, GITDoor) or isinstance(instance, GITTrigger) and resourceExists:
                    # Tag is stored in the GIT
                    name = resource.localized_name()
                    tag = instance.tag
                elif isinstance(instance, GITWaypoint):
                    # Name and tag are stored in the GIT
                    name = self._installation.string(instance.name)
                    tag = instance.tag
                elif resourceExists:
                    name = resource.localized_name()
                    tag = resource.resource().tag

                if resource is None:
                    font.setItalic(True)

                item.setText(name)
                item.setToolTip(f"Struct Index: {struct_index}\nResRef: {resref}\nName: {name}\nTag: {tag}")
                item.setData(QtCore.Qt.UserRole + 1, instance.identifier().restype.extension + name)

            item.setFont(font)
            item.setData(QtCore.Qt.UserRole, instance)
            items.append(item)

        for item in sorted(items, key=lambda i: i.data(QtCore.Qt.UserRole + 1)):
            self.ui.instanceList.addItem(item)

    def selectInstanceItemOnList(self, instance: GITInstance) -> None:
        """Select an instance item on the instance list
        Args:
            instance (GITInstance): The instance to select
        Returns:
            None
        - Clear any existing selection from the instance list
        - Iterate through each item in the instance list
        - Check if the item's stored data matches the passed in instance
        - If so, select the item and scroll it into view.
        """
        self.ui.instanceList.clearSelection()
        for i in range(self.ui.instanceList.count()):
            item = self.ui.instanceList.item(i)
            data: GITInstance = item.data(QtCore.Qt.UserRole)
            if data is instance:
                item.setSelected(True)
                self.ui.instanceList.scrollToItem(item)

    def updateToggles(self) -> None:
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

    def addInstance(self, instance: GITInstance, walkmeshSnap: bool = True) -> None:
        """Adds a GIT instance to the editor.

        Args:
        ----
            instance: {The instance to add}
            walkmeshSnap (optional): {Whether to snap the instance to the walkmesh}.

        Returns:
        -------
            None
        Processing Logic:
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
            dialog = InsertInstanceDialog(self, self._installation, self._module, instance.identifier().restype)

            if dialog.exec_():
                self.rebuildResourceTree()
                instance.resref = ResRef(dialog.resname)
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

    def addInstanceAtCursor(self, instance: GITInstance) -> None:
        """Adds instance at cursor position
        Args:
            instance (GITInstance): Instance to add
        Returns:
            None: No return value
        - Sets position of instance to cursor position
        - Checks if instance is camera, opens dialog if not
        - Adds instance to resource tree if dialog confirms
        - Rebuilds instance list.
        """
        instance.position.x = self.ui.mainRenderer.scene.cursor.position().x
        instance.position.y = self.ui.mainRenderer.scene.cursor.position().y
        instance.position.z = self.ui.mainRenderer.scene.cursor.position().z

        if not isinstance(instance, GITCamera):
            dialog = InsertInstanceDialog(self, self._installation, self._module, instance.identifier().restype)

            if dialog.exec_():
                self.rebuildResourceTree()
                instance.resref = ResRef(dialog.resname)
                self._module.git().resource().add(instance)
        else:
            self._module.git().resource().add(instance)
        self.rebuildInstanceList()

    def editInstance(self, instance: GITInstance) -> None:
        if openInstanceDialog(self, instance, self._installation):
            if not isinstance(instance, GITCamera):
                self.ui.mainRenderer.scene.clearCacheBuffer.append(instance.identifier())
            self.rebuildInstanceList()

    def snapCameraToView(self, instance: GITCamera) -> None:
        view = self.ui.mainRenderer.scene.camera.truePosition()
        rot = self.ui.mainRenderer.scene.camera
        instance.pitch = 0
        instance.height = 0
        instance.position = Vector3(view.x, view.y, view.z)
        instance.orientation = Vector4.from_euler(math.pi / 2 - rot.yaw, 0, math.pi - rot.pitch)

    def snapViewToCamera(self, instance: GITCamera) -> None:
        camera = self.ui.mainRenderer.scene.camera
        euler = instance.orientation.to_euler()
        camera.pitch = math.pi - euler.z - math.radians(instance.pitch)
        camera.yaw = math.pi / 2 - euler.x
        camera.x = instance.position.x
        camera.y = instance.position.y
        camera.z = instance.position.z + instance.height
        camera.distance = 0

    def snapCameraToEntryLocation(self) -> None:
        self.ui.mainRenderer.scene.camera.x = self.ifo().entry_position.x
        self.ui.mainRenderer.scene.camera.y = self.ifo().entry_position.y
        self.ui.mainRenderer.scene.camera.z = self.ifo().entry_position.z

    def toggleFreeCam(self) -> None:
        if isinstance(self._controls3d, ModuleDesignerControls3d):
            self._controls3d = ModuleDesignerControlsFreeCam(self, self.ui.mainRenderer)
        else:
            self._controls3d = ModuleDesignerControls3d(self, self.ui.mainRenderer)

    # region Selection Manipulations
    def setSelection(self, instances: list[GITInstance]) -> None:
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

    def deleteSelected(self) -> None:
        for instance in self.selectedInstances:
            self._module.git().resource().remove(instance)

        self.selectedInstances.clear()
        self.ui.mainRenderer.scene.selection.clear()
        self.ui.flatRenderer.instanceSelection.clear()
        self.rebuildInstanceList()

    def moveSelected(self, x: float, y: float, z: float | None = None) -> None:
        """Moves selected instances by the given offsets.

        Args:
        ----
            x: Float offset to move instances along the x-axis.
            y: Float offset to move instances along the y-axis.
            z: Float offset to move instances along the z-axis or None.

        Returns:
        -------
            None
        - Checks if instance locking is enabled and returns if True
        - Loops through selected instances
        - Increases x, y position by offsets
        - Increases z position by offset if provided, else sets to walkmesh height
        - No return, modifies instances in place.
        """
        if self.ui.lockInstancesCheck.isChecked():
            return

        for instance in self.selectedInstances:
            instance.position.x += x
            instance.position.y += y
            if z is None:
                instance.position.z = self.ui.mainRenderer.walkmeshPoint(instance.position.x, instance.position.y).z
            else:
                instance.position.z += z

    def rotateSelected(self, x: float, y: float) -> None:
        if self.ui.lockInstancesCheck.isChecked():
            return

        for instance in self.selectedInstances:
            instance.rotate(x / 60, y / 60, 0.0)

    # endregion

    # region Signal Callbacks
    def _onSavedResource(self, resource: ModuleResource) -> None:
        resource.reload()
        self.ui.mainRenderer.scene.clearCacheBuffer.append(ResourceIdentifier(resource.resname(), resource.restype()))

    def onInstanceListDoubleClicked(self) -> None:
        if self.ui.instanceList.selectedItems():
            item = self.ui.instanceList.selectedItems()[0]
            instance: GITInstance = item.data(QtCore.Qt.UserRole)
            self.setSelection([instance])
            self.ui.mainRenderer.snapCameraToPoint(instance.position)
            self.ui.flatRenderer.snapCameraToPoint(instance.position)

    def onInstanceVisibilityDoubleClick(self, checkbox: QCheckBox) -> None:
        """Toggles visibility of a single instance type on double click.
        This method should be called whenever one of the instance visibility checkboxes have been double clicked. The
        resulting affect should be that all checkboxes become unchecked except for the one that was pressed.

        Args:
        ----
            checkbox (QCheckBox): Checkbox that was double clicked.

        Returns:
        -------
            None
        Processing Logic:
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

    def onResourceTreeContextMenu(self, point: QPoint) -> None:
        menu = QMenu(self)

        data = self.ui.resourceTree.currentItem().data(0, QtCore.Qt.UserRole)
        if isinstance(data, ModuleResource):
            self._build_active_override_menu(data, menu)
        menu.exec_(self.ui.resourceTree.mapToGlobal(point))

    def _build_active_override_menu(self, data: ModuleResource, menu: QMenu):
        """Builds an active override menu for a module resource
        Args:
            data: ModuleResource - The module resource data
            menu: QMenu - The menu to build actions on
        Returns:
            None
        Processing Logic:
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
            lowercase_parts = [part.lower for part in location.parts]
            if "override" in lowercase_parts:
                copyToOverrideAction.setEnabled(False)
            menu.addAction(locationAction)

    def on3dMouseMoved(self, screen: Vector2, screenDelta: Vector2, world: Vector3, buttons: set[int], keys: set[int]) -> None:
        self._controls3d.onMouseMoved(screen, screenDelta, world, buttons, keys)

    def on3dMouseScrolled(self, delta: Vector2, buttons: set[int], keys: set[int]) -> None:
        self._controls3d.onMouseScrolled(delta, buttons, keys)

    def on3dMousePressed(self, screen: Vector2, buttons: set[int], keys: set[int]) -> None:
        self._controls3d.onMousePressed(screen, buttons, keys)

    def on3dKeyboardPressed(self, buttons: set[int], keys: set[int]) -> None:
        self._controls3d.onKeyboardPressed(buttons, keys)

    def on3dObjectSelected(self, instance: GITInstance) -> None:
        if instance is not None:
            self.setSelection([instance])
        else:
            self.setSelection([])

    def onContextMenu(self, world: Vector3, point: QPoint) -> None:
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
        Returns:
            None: Does not return anything
        Processing Logic:
        - Creates a QMenu object
        - Adds actions to menu for inserting different object types at world position or view position
        - Connects actions to addInstance method
        - Pops up menu at mouse cursor position
        - Connects menu hide signal to reset mouse buttons
        """
        menu = QMenu(self)

        view = self.ui.mainRenderer.scene.camera.true_position()
        rot = self.ui.mainRenderer.scene.camera
        menu.addAction("Insert Camera").triggered.connect(lambda: self.addInstance(GITCamera(*world), False))
        menu.addAction("Insert Camera at View").triggered.connect(
            lambda: self.addInstance(GITCamera(view.x, view.y, view.z, rot.yaw, rot.pitch, 0, 0), False),
        )
        menu.addSeparator()
        menu.addAction("Insert Creature").triggered.connect(lambda: self.addInstance(GITCreature(*world), True))
        menu.addAction("Insert Door").triggered.connect(lambda: self.addInstance(GITDoor(*world), False))
        menu.addAction("Insert Placeable").triggered.connect(lambda: self.addInstance(GITPlaceable(*world), False))
        menu.addAction("Insert Store").triggered.connect(lambda: self.addInstance(GITStore(*world), False))
        menu.addAction("Insert Sound").triggered.connect(lambda: self.addInstance(GITSound(*world), False))
        menu.addAction("Insert Waypoint").triggered.connect(lambda: self.addInstance(GITWaypoint(*world), False))
        menu.addAction("Insert Encounter").triggered.connect(lambda: self.addInstance(GITEncounter(*world), False))
        menu.addAction("Insert Trigger").triggered.connect(lambda: self.addInstance(GITTrigger(*world), False))

        menu.popup(self.cursor().pos())
        menu.aboutToHide.connect(self.ui.mainRenderer.resetMouseButtons)

    def onContextMenuSelectionExists(self) -> None:
        """Checks if a context menu selection exists
        Args:
            self: The class instance
        Returns:
            None: Does not return anything
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
                menu.addAction("Snap 3D View to Camera").triggered.connect(lambda: self.snapViewToCamera(instance))
                menu.addSeparator()

            menu.addAction("Edit Instance").triggered.connect(lambda: self.editInstance(instance))
            menu.addAction("Remove").triggered.connect(self.deleteSelected)

        menu.popup(self.cursor().pos())
        menu.aboutToHide.connect(self.ui.mainRenderer.resetMouseButtons)

    def on3dSceneInitialized(self) -> None:
        self.rebuildResourceTree()
        self.rebuildInstanceList()
        self._refreshWindowTitle()
        self.updateToggles()

    def on2dMouseMoved(self, screen: Vector2, delta: Vector2, buttons: set[int], keys: set[int]) -> None:
        worldDelta = self.ui.flatRenderer.toWorldDelta(delta.x, delta.y)
        world = self.ui.flatRenderer.toWorldCoords(screen.x, screen.y)
        self._controls2d.onMouseMoved(screen, delta, world, worldDelta, buttons, keys)

    def on2dMouseScrolled(self, delta: Vector2, buttons: set[int], keys: set[int]) -> None:
        self._controls2d.onMouseScrolled(delta, buttons, keys)

    def on2dMousePressed(self, screen: Vector2, buttons: set[int], keys: set[int]) -> None:
        self._controls2d.onMousePressed(screen, buttons, keys)

    def on2dKeyboardPressed(self, buttons: set[int], keys: set[int]) -> None:
        self._controls2d.onKeyboardPressed(buttons, keys)

    # endregion

    # region Events
    def keyPressEvent(self, e: QKeyEvent, bubble: bool = True) -> None:
        super().keyPressEvent(e)
        self.ui.mainRenderer.keyPressEvent(e)
        self.ui.flatRenderer.keyPressEvent(e)

    def keyReleaseEvent(self, e: QKeyEvent, bubble: bool = True) -> None:
        super().keyReleaseEvent(e)
        self.ui.mainRenderer.keyReleaseEvent(e)
        self.ui.flatRenderer.keyReleaseEvent(e)

    # endregion


class ModuleDesignerControls3d:
    def __init__(self, editor: ModuleDesigner, renderer: ModuleRenderer):
        """Initializes the 3D view controller
        Args:
            editor: ModuleDesigner - The module designer instance
            renderer: ModuleRenderer - The 3D renderer instance
        Returns:
            None - Initializes controller items and properties
        Processing Logic:
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

    def onMouseScrolled(self, delta: Vector2, buttons: set[int], keys: set[int]) -> None:
        if self.zoomCamera.satisfied(buttons, keys):
            strength = self.settings.zoomCameraSensitivity3d / 2000
            self.renderer.scene.camera.distance += -delta.y * strength

        if self.moveZCamera.satisfied(buttons, keys):
            strength = self.settings.moveCameraSensitivity3d / 1000
            self.renderer.scene.camera.z -= -delta.y * strength

    def onMouseMoved(self, screen: Vector2, screenDelta: Vector2, world: Vector3, buttons: set[int], keys: set[int]) -> None:
        """Moves the camera or selected instances on mouse movement.

        Args:
        ----
            screen (Vector2): Screen position
            screenDelta (Vector2): Screen position change
            world (Vector3): World position
            buttons (set[int]): Pressed mouse buttons
            keys (set[int]): Pressed keyboard keys
        Returns:
            None

        Processing Logic:
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
            upward = screenDelta.y * self.renderer.scene.camera.upward(False)
            sideward = screenDelta.x * self.renderer.scene.camera.sideward()
            strength = self.settings.moveCameraSensitivity3d / 1000
            self.renderer.scene.camera.z -= (upward.z + sideward.z) * strength
            self.renderer.scene.camera.y -= (upward.y + sideward.y) * strength
            self.renderer.scene.camera.x -= (upward.x + sideward.x) * strength

        if self.rotateCamera.satisfied(buttons, keys):
            strength = self.settings.moveCameraSensitivity3d / 10000
            self.renderer.rotateCamera(-screenDelta.x * strength, screenDelta.y * strength)

        if self.zoomCameraMM.satisfied(buttons, keys):
            strength = self.settings.zoomCameraSensitivity3d / 5000
            self.renderer.scene.camera.distance -= screenDelta.y * strength

        if self.moveXYSelected.satisfied(buttons, keys):
            if self.editor.ui.lockInstancesCheck.isChecked():
                return

            for instance in self.editor.selectedInstances:
                instance.position.x = self.renderer.scene.cursor.position().x
                instance.position.y = self.renderer.scene.cursor.position().y
                if not isinstance(instance, GITCamera):
                    instance.position.z = self.renderer.scene.cursor.position().z

        if self.moveZSelected.satisfied(buttons, keys):
            for instance in self.editor.selectedInstances:
                instance.position.z -= screenDelta.y / 40

        if self.rotateSelected.satisfied(buttons, keys):
            self.editor.rotateSelected(screenDelta.x, screenDelta.y)

    def onMousePressed(self, screen: Vector2, buttons: set[int], keys: set[int]) -> None:
        """Handle mouse press events in the editor
        Args:
            screen: Vector2 - Mouse position on screen
            buttons: set[int] - Pressed mouse buttons
            keys: set[int] - Pressed keyboard keys
        Returns:
            None
        Processing Logic:
            - Check if select button is pressed and set doSelect flag
            - Check if duplicate button is pressed, duplicate selected instance and add/select new instance
            - Check if context menu button is pressed and open context menu at cursor position.
        """
        if self.selectUnderneath.satisfied(buttons, keys):
            self.renderer.doSelect = True

        if self.duplicateSelected.satisfied(buttons, keys) and self.editor.selectedInstances:
            instance = deepcopy(self.editor.selectedInstances[-1])
            instance.position = self.renderer.scene.cursor.position()
            self.editor.git().add(instance)
            self.editor.rebuildInstanceList()
            self.editor.setSelection([instance])

        if self.openContextMenu.satisfied(buttons, keys):
            world = Vector3(*self.renderer.scene.cursor.position())
            self.editor.onContextMenu(world, self.renderer.mapToGlobal(QPoint(screen.x, screen.y)))

    def onMouseReleased(self, screen: Vector2, buttons: set[int], keys: set[int]) -> None:
        ...

    def onKeyboardPressed(self, buttons: set[int], keys: set[int]) -> None:
        """Handles keyboard input in the editor
        Args:
            buttons: set[int]: The pressed buttons
            keys: set[int]: The pressed keys
        Returns:
            None: Does not return anything
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
            self.renderer.rotateCamera(math.pi / 4, 0)
        if self.rotateCameraRight.satisfied(buttons, keys):
            self.renderer.rotateCamera(-math.pi / 4, 0)
        if self.rotateCameraUp.satisfied(buttons, keys):
            self.renderer.rotateCamera(0, math.pi / 4)
        if self.rotateCameraDown.satisfied(buttons, keys):
            self.renderer.rotateCamera(0, -math.pi / 4)

        if self.moveCameraUp.satisfied(buttons, keys):
            self.renderer.scene.camera.z += 1
        if self.moveCameraDown.satisfied(buttons, keys):
            self.renderer.scene.camera.z -= 1
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

    def onKeyboardReleased(self, buttons: set[int], keys: set[int]) -> None:
        ...


class ModuleDesignerControlsFreeCam:
    def __init__(self, editor: ModuleDesigner, renderer: ModuleRenderer):
        """Initializes the free camera controller.

        Args:
        ----
            editor: {ModuleDesigner}: The module designer instance.
            renderer: {ModuleRenderer}: The module renderer instance.

        Returns:
        -------
            None
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
        mouseX = rendererPos.x() + self.renderer.width() / 2
        mouseY = rendererPos.y() + self.renderer.height() / 2
        self.renderer.cursor().setPos(mouseX, mouseY)

    def onMouseScrolled(self, delta: Vector2, buttons: set[int], keys: set[int]) -> None:
        ...

    def onMouseMoved(self, screen: Vector2, screenDelta: Vector2, world: Vector3, buttons: set[int], keys: set[int]) -> None:
        rendererPos = self.renderer.mapToGlobal(self.renderer.pos())
        mouseX = rendererPos.x() + self.renderer.width() / 2
        mouseY = rendererPos.y() + self.renderer.height() / 2
        strength = self.settings.rotateCameraSensitivityFC / 10000

        self.renderer.rotateCamera(-screenDelta.x * strength, screenDelta.y * strength, snapRotations=False)
        self.renderer.cursor().setPos(mouseX, mouseY)

    def onMousePressed(self, screen: Vector2, buttons: set[int], keys: set[int]) -> None:
        ...

    def onMouseReleased(self, screen: Vector2, buttons: set[int], keys: set[int]) -> None:
        ...

    def onKeyboardPressed(self, buttons: set[int], keys: set[int]) -> None:
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

    def onKeyboardReleased(self, buttons: set[int], keys: set[int]) -> None:
        ...


class ModuleDesignerControls2d:
    def __init__(self, editor: ModuleDesigner, renderer: WalkmeshRenderer):
        """Initializes the 2D editor controller.

        Args:
        ----
            editor: {ModuleDesigner}: The editor module.
            renderer: {WalkmeshRenderer}: The renderer for the walkmesh.

        Returns:
        -------
            None: None
        Processing Logic:
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

    def onMouseScrolled(self, delta: Vector2, buttons: set[int], keys: set[int]) -> None:
        """Scrolls camera zoom on mouse scroll
        Args:
            delta: Mouse scroll delta vector
            buttons: Mouse buttons pressed
            keys: Keyboard keys pressed
        Returns:
            None: No return value
        - Checks if zoom camera control is satisfied by buttons and keys
        - Calculates zoom strength from scroll delta and sensitivity setting
        - Nudges camera zoom by calculated amount.
        """
        if self.zoomCamera.satisfied(buttons, keys):
            strength = self.settings.moveCameraSensitivity2d / 100 / 50
            self.renderer.camera.nudgeZoom(delta.y * strength)

    def onMouseMoved(
        self,
        screen: Vector2,
        screenDelta: Vector2,
        world: Vector2,
        worldDelta: Vector2,
        buttons: set[int],
        keys: set[int],
    ) -> None:
        """Handles mouse movement events in the editor
        Args:
            screen: Vector2 - Mouse position on screen in pixels
            screenDelta: Vector2 - Mouse movement since last event in pixels
            world: Vector2 - Mouse position in world space
            worldDelta: Vector2 - Mouse movement since last event in world space
            buttons: set[int] - Mouse buttons currently held down
            keys: set[int] - Keyboard keys currently held down
        Returns:
            None
        Processing Logic:
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
            self.editor.moveSelected(worldDelta.x, worldDelta.y)

        if self.rotateSelected.satisfied(buttons, keys):
            for instance in self.editor.selectedInstances:
                rotation = -math.atan2(world.x - instance.position.x, world.y - instance.position.y)
                if isinstance(instance, GITCamera):
                    instance.rotate(instance.yaw() - rotation, 0, 0)
                else:
                    instance.rotate(-instance.yaw() + rotation, 0, 0)

    def onMousePressed(self, screen: Vector2, buttons: set[int], keys: set[int]) -> None:
        """Handle mouse press events in the editor
        Args:
            screen: Vector2 - Mouse position
            buttons: set[int] - Pressed buttons
            keys: set[int] - Pressed keys
        Returns:
            None
        Processing Logic:
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
            self._duplicate_instance()
        if self.openContextMenu.satisfied(buttons, keys):
            world = self.renderer.toWorldCoords(screen.x, screen.y)
            self.editor.onContextMenu(world, self.renderer.mapToGlobal(QPoint(screen.x, screen.y)))

    # TODO Rename this here and in `onMousePressed`
    def _duplicate_instance(self):
        instance = deepcopy(self.editor.selectedInstances[-1])
        result = self.renderer.mapFromGlobal(self.renderer.cursor().pos())
        instance.position = self.renderer.toWorldCoords(result.x(), result.y())
        self.editor.git().add(instance)
        self.editor.rebuildInstanceList()
        self.editor.setSelection([instance])

    def onMouseReleased(self, screen: Vector2, buttons: set[int], keys: set[int]) -> None:
        ...

    def onKeyboardPressed(self, buttons: set[int], keys: set[int]) -> None:
        """Handle keyboard input in the editor.

        Args:
        ----
            buttons: {Set of pressed button codes}
            keys: {Set of pressed key codes}.

        Returns:
        -------
            None
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

    def onKeyboardReleased(self, buttons: set[int], keys: set[int]) -> None:
        ...
