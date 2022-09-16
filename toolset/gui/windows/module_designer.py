import math
import os
from contextlib import suppress
from typing import Set, Dict, Optional, List

from PyQt5 import QtCore
from PyQt5.QtCore import QPoint, QSettings, QTimer
from PyQt5.QtGui import QPixmap, QIcon, QKeyEvent, QResizeEvent, QColor
from PyQt5.QtWidgets import QMainWindow, QWidget, QTreeWidgetItem, QMenu, QAction, QListWidgetItem, \
    QMessageBox, QCheckBox, QFileDialog

from data.misc import Bind, ControlItem
from gui.dialogs.insert_instance import InsertInstanceDialog
from gui.dialogs.select_module import SelectModuleDialog
from gui.editors.git import openInstanceDialog
from gui.widgets.module_renderer import ModuleRenderer
from gui.widgets.settings.module_designer import ModuleDesignerSettings
from gui.widgets.walkmesh_renderer import WalkmeshRenderer
from pykotor.common.geometry import Vector2, SurfaceMaterial, Vector3
from pykotor.common.misc import ResRef, Color
from pykotor.common.module import Module, ModuleResource
from pykotor.common.stream import BinaryWriter
from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.generics.git import GITCreature, GITPlaceable, GITDoor, GITTrigger, GITEncounter, GITWaypoint, \
    GITSound, GITStore, GITCamera, GITInstance
from pykotor.resource.type import ResourceType

from data.installation import HTInstallation
from gui.windows.help import HelpWindow
from pykotor.gl.scene import RenderObject, Camera

from data.me_controls import ModuleEditorControls, DynamicModuleEditorControls, HolocronModuleEditorControls
from utils.misc import QtKey, QtMouse
from utils.window import openResourceEditor


class ModuleDesigner(QMainWindow):
    def __init__(self, parent: Optional[QWidget], installation: HTInstallation):
        super().__init__(parent)

        self._installation: HTInstallation = installation
        self._module: Optional[Module] = None

        self.selectedInstances: List[GITInstance] = []
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
            color = Color.from_rgba_integer(intvalue)
            return QColor(int(color.r*255), int(color.g*255), int(color.b*255), int(color.a*255))
        self.materialColors: Dict[SurfaceMaterial, QColor] = {
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
            SurfaceMaterial.TRIGGER: intColorToQColor(self.settings.nonWalkGrassMaterialColour)
        }

        self.ui.flatRenderer.materialColors = self.materialColors
        self.ui.flatRenderer.hideWalkmeshEdges = True
        self.ui.flatRenderer.highlightBoundaries = False

        self._controls3d: ModuleDesignerControl3dScheme = ModuleDesignerControl3dScheme(self, self.ui.mainRenderer)
        self._controls2d: ModuleDesignerControl2dScheme = ModuleDesignerControl2dScheme(self, self.ui.flatRenderer)

        self._refreshWindowTitle()
        self.rebuildResourceTree()
        self.rebuildInstanceList()

        QTimer().singleShot(33, self.openModule)

    def _setupSignals(self) -> None:
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
            title = "No Module - {} - Module Designer".format(self._installation.name)
        else:
            title = "{} - {} - Module Designer".format(self._module._id, self._installation.name)
        self.setWindowTitle(title)

    def openModule(self) -> None:
        dialog = SelectModuleDialog(self, self._installation)

        if dialog.exec_():
            self.unloadModule()

            self._module = Module(dialog.module, self._installation)
            self.ui.mainRenderer.init(self._installation, self._module)

            self.ui.flatRenderer.setGit(self._module.git().resource())
            self.ui.flatRenderer.setWalkmeshes([bwm.resource() for bwm in self._module.resources.values() if bwm.restype() == ResourceType.WOK])
            self.ui.flatRenderer.centerCamera()

    def unloadModule(self) -> None:
        self._module = None
        self.ui.mainRenderer.scene = None
        self.ui.mainRenderer._init = False

    def showHelpWindow(self) -> None:
        window = HelpWindow(self, "./help/tools/1-moduleEditor.md")
        window.show()

    def saveGit(self) -> None:
        self._module.git().save()

    def activateCustomControls(self, controls: DynamicModuleEditorControls) -> None:
        self.activeControls = controls

    def rebuildResourceTree(self) -> None:
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
            ResourceType.INVALID: QTreeWidgetItem(["Other"])
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

        for category in categories:
            self.ui.resourceTree.addTopLevelItem(categories[category])

        for resource in self._module.resources.values():
            item = QTreeWidgetItem([resource.resname() + "." + resource.restype().extension])
            item.setData(0, QtCore.Qt.UserRole, resource)
            category = categories[resource.restype()] if resource.restype() in categories else categories[ResourceType.INVALID]
            category.addChild(item)

        self.ui.resourceTree.sortByColumn(0, QtCore.Qt.AscendingOrder)
        self.ui.resourceTree.setSortingEnabled(True)

    def openModuleResource(self, resource: ModuleResource) -> None:
        editor = openResourceEditor(resource.active(), resource.resname(), resource.restype(), resource.data(),
                                    self._installation, self)[1]

        if editor is None:
            QMessageBox(QMessageBox.Critical,
                        "Failed to open editor",
                        "Failed to open editor for file: {}.{}".format(resource.resname(), resource.restype().extension))
        else:
            editor.savedFile.connect(lambda: self._onSavedResource(resource))

    def _onSavedResource(self, resource: ModuleResource) -> None:
        resource.reload()
        self.ui.mainRenderer.scene.clearCacheBuffer.append(ResourceIdentifier(resource.resname(), resource.restype()))

    def copyResourceToOverride(self, resource: ModuleResource) -> None:
        location = "{}/{}.{}".format(self._installation.override_path(), resource.resname(), resource.restype().extension)
        BinaryWriter.dump(location, resource.data())
        resource.add_locations([location])
        resource.activate(location)
        self.ui.mainRenderer.scene.clearCacheBuffer.append(ResourceIdentifier(resource.resname(), resource.restype()))

    def activateResourceFile(self, resource: ModuleResource, location: str) -> None:
        resource.activate(location)
        self.ui.mainRenderer.scene.clearCacheBuffer.append(ResourceIdentifier(resource.resname(), resource.restype()))

    def selectResourceItem(self, instance: GITInstance, clearExisting: bool = True) -> None:
        if clearExisting:
            self.ui.resourceTree.clearSelection()

        for i in range(self.ui.resourceTree.topLevelItemCount()):
            parent = self.ui.resourceTree.topLevelItem(i)
            for j in range(parent.childCount()):
                item = parent.child(j)
                res: ModuleResource = item.data(0, QtCore.Qt.UserRole)
                if res.resname() == instance.identifier() and res.restype() == instance.identifier().restype:
                    parent.setExpanded(True)
                    item.setSelected(True)
                    self.ui.resourceTree.scrollToItem(item)

    def rebuildInstanceList(self) -> None:
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
            GITInstance: False
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
            GITInstance: QPixmap(32, 32)
        }

        self.ui.instanceList.clear()
        for instance in self._module.git().resource().instances():
            if visibleMapping[type(instance)]:
                continue

            if instance.identifier():
                resource = self._module.resource(instance.identifier().resname, instance.identifier().restype)
                text = resource.localized_name()
                if text is None or text.isspace():
                    text = "[{}]".format(resource.resname())
            else:
                text = "Camera #{}".format(self._module.git().resource().index(instance))

            icon = QIcon(iconMapping[type(instance)])
            item = QListWidgetItem(icon, text)
            item.setToolTip("" if instance.identifier() is None else instance.identifier().resname)
            item.setData(QtCore.Qt.UserRole, instance)
            self.ui.instanceList.addItem(item)

    def selectInstanceItemOnList(self, instance: GITInstance) -> None:
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
        if walkmeshSnap:
            instance.position.z = self.ui.mainRenderer.walkmeshPoint(instance.position.x, instance.position.y, self.ui.mainRenderer.scene.camera.z).z

        if not isinstance(instance, GITCamera):
            dialog = InsertInstanceDialog(self, self._installation, self._module, instance.identifier().restype)

            if dialog.exec_():
                self.rebuildResourceTree()
                instance.resref = ResRef(dialog.resname)
                self._module.git().resource().add(instance)
        else:
            self._module.git().resource().add(instance)
        self.rebuildInstanceList()

    def addInstanceAtCursor(self, instance: GITInstance) -> None:
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
        openInstanceDialog(self, instance, self._installation)

    # region Selection Manipulations
    def setSelection(self, instances: List[GITInstance]) -> None:
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

    def moveSelected(self, x: float, y: float, z: float = None) -> None:
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
            instance.rotate(x/60, 0*y/60, 0.0)
    # endregion

    # region Signal Callbacks
    def onInstanceListDoubleClicked(self) -> None:
        if self.ui.instanceList.selectedItems():
            item = self.ui.instanceList.selectedItems()[0]
            instance: GITInstance = item.data(QtCore.Qt.UserRole)
            self.ui.mainRenderer.scene.select(instance)

            self.selectResourceItem(item.data(QtCore.Qt.UserRole))
            self.ui.mainRenderer.snapCameraToPoint(instance.position)

    def onInstanceVisibilityDoubleClick(self, checkbox: QCheckBox) -> None:
        """
        This method should be called whenever one of the instance visibility checkboxes have been double clicked. The
        resulting affect should be that all checkboxes become unchecked except for the one that was pressed.
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
            copyToOverrideAction = QAction("Copy To Override", self)
            copyToOverrideAction.triggered.connect(lambda _, r=data: self.copyResourceToOverride(r))

            menu.addAction("Edit Active File").triggered.connect(lambda _, r=data: self.openModuleResource(r))
            menu.addAction("Reload Active File").triggered.connect(lambda _: data.reload())
            menu.addAction(copyToOverrideAction)
            menu.addSeparator()
            for location in data.locations():
                locationAciton = QAction(location, self)
                locationAciton.triggered.connect(lambda _, l=location: self.activateResourceFile(data, l))
                if location == data.active():
                    locationAciton.setEnabled(False)
                if "override" in location.lower():
                    copyToOverrideAction.setEnabled(False)
                menu.addAction(locationAciton)

        menu.exec_(self.ui.resourceTree.mapToGlobal(point))

    def on3dMouseMoved(self, screen: Vector2, screenDelta: Vector2, world: Vector3, buttons: Set[int], keys: Set[int]) -> None:
        self._controls3d.onMouseMoved(screen, screenDelta, world, buttons, keys)

    def on3dMouseScrolled(self, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        self._controls3d.onMouseScrolled(delta, buttons, keys)

    def on3dMousePressed(self, screen: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        self._controls3d.onMousePressed(screen, buttons, keys)

    def on3dKeyboardPressed(self, buttons: Set[int], keys: Set[int]) -> None:
        self._controls3d.onKeyboardPressed(buttons, keys)

    def on3dObjectSelected(self, instance: GITInstance) -> None:
        if instance is not None:
            self.setSelection([instance])
        else:
            self.setSelection([])

    def onContextMenu(self, world: Vector3, point: QPoint) -> None:
        if self._module is None:
            return

        menu = QMenu(self)
        world = self.ui.mainRenderer.scene.cursor.position()

        if len(self.ui.mainRenderer.scene.selection) == 0:
            view = self.ui.mainRenderer.scene.camera.truePosition()
            rot = self.ui.mainRenderer.scene.camera
            menu.addAction("Insert Camera").triggered.connect(lambda: self.addInstance(GITCamera(*world), False))
            menu.addAction("Insert Camera at View").triggered.connect(lambda: self.addInstance(GITCamera(view.x, view.y, view.z, rot.yaw, rot.pitch, 0, 0), False))
            menu.addSeparator()
            menu.addAction("Insert Creature").triggered.connect(lambda: self.addInstance(GITCreature(*world), True))
            menu.addAction("Insert Door").triggered.connect(lambda: self.addInstance(GITDoor(*world), False))
            menu.addAction("Insert Placeable").triggered.connect(lambda: self.addInstance(GITPlaceable(*world), False))
            menu.addAction("Insert Store").triggered.connect(lambda: self.addInstance(GITStore(*world), False))
            menu.addAction("Insert Sound").triggered.connect(lambda: self.addInstance(GITSound(*world), False))
            menu.addAction("Insert Waypoint").triggered.connect(lambda: self.addInstance(GITWaypoint(*world), False))
            menu.addAction("Insert Encounter").triggered.connect(lambda: self.addInstance(GITEncounter(*world), False))
            menu.addAction("Insert Trigger").triggered.connect(lambda: self.addInstance(GITTrigger(*world), False))
        else:
            menu.addAction("Edit Instance").triggered.connect(lambda: self.editInstance(self.selectedInstances[0]))
            menu.addAction("Remove").triggered.connect(self.deleteSelected)

        menu.popup(point)
        menu.aboutToHide.connect(self.ui.mainRenderer.resetMouseButtons)

    def on3dSceneInitialized(self) -> None:
        self.rebuildResourceTree()
        self.rebuildInstanceList()
        self._refreshWindowTitle()
        self.updateToggles()

    def on2dMouseMoved(self, screen: Vector2, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        worldDelta = self.ui.flatRenderer.toWorldDelta(delta.x, delta.y)
        world = self.ui.flatRenderer.toWorldCoords(screen.x, screen.y)
        self._controls2d.onMouseMoved(screen, delta, world, worldDelta, buttons, keys)

    def on2dMouseScrolled(self, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        self._controls2d.onMouseScrolled(delta, buttons, keys)

    def on2dMousePressed(self, screen: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        self._controls2d.onMousePressed(screen, buttons, keys)

    def on2dKeyboardPressed(self, buttons: Set[int], keys: Set[int]) -> None:
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


class ModuleDesignerControl3dScheme:
    def __init__(self, editor: ModuleDesigner, renderer: ModuleRenderer):
        self.editor: ModuleDesigner = editor
        self.settings: ModuleDesignerSettings = ModuleDesignerSettings()
        self.renderer: ModuleRenderer = renderer

        self.panXYCamera: ControlItem = ControlItem(self.settings.moveCameraXY3dBind)
        self.panZCamera: ControlItem = ControlItem(self.settings.moveCameraZ3dBind)
        self.rotateCamera: ControlItem = ControlItem(self.settings.rotateCamera3dBind)
        self.zoomCamera: ControlItem = ControlItem(self.settings.zoomCamera3dBind)
        self.zoomCameraMM: ControlItem = ControlItem(self.settings.zoomCamera3dMMBind)
        self.rotateSelected: ControlItem = ControlItem(self.settings.rotateSelected3dBind)
        self.moveXYSelected: ControlItem = ControlItem(self.settings.moveSelectedXY3dBind)
        self.moveZSelected: ControlItem = ControlItem(self.settings.moveSelectedZ3dBind)
        self.selectUnderneath: ControlItem = ControlItem(self.settings.selectUnderneath3dBind)
        self.snapCameraToSelected: ControlItem = ControlItem(self.settings.snapCameraToSelected3dBind)
        self.deleteSelected: ControlItem = ControlItem(self.settings.deleteSelected3dBind)
        self.openContextMenu: ControlItem = ControlItem((set(), {QtMouse.RightButton}))

    def onMouseScrolled(self, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        if self.zoomCamera.satisfied(buttons, keys):
            strength = self.settings.zoomCameraSensitivity3d / 2000
            self.renderer.scene.camera.distance += -delta.y * strength

        if self.panZCamera.satisfied(buttons, keys):
            strength = self.settings.moveCameraSensitivity3d / 1000
            self.renderer.scene.camera.z -= -delta.y * strength

    def onMouseMoved(self, screen: Vector2, screenDelta: Vector2, world: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        if self.panXYCamera.satisfied(buttons, keys):
            forward = -screenDelta.y * self.renderer.scene.camera.forward()
            sideward = screenDelta.x * self.renderer.scene.camera.sideward()
            strength = self.settings.moveCameraSensitivity3d / 1000
            self.renderer.scene.camera.x -= (forward.x + sideward.x) * strength
            self.renderer.scene.camera.y -= (forward.y + sideward.y) * strength

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
                instance.position.z = self.renderer.scene.cursor.position().z

        if self.moveZSelected.satisfied(buttons, keys):
            for instance in self.editor.selectedInstances:
                instance.position.z -= screenDelta.y / 40

        if self.rotateSelected.satisfied(buttons, keys):
            self.editor.rotateSelected(screenDelta.x, screenDelta.y)

    def onMousePressed(self, screen: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        if self.selectUnderneath.satisfied(buttons, keys):
            self.renderer.doSelect = True

        if self.openContextMenu.satisfied(buttons, keys):
            world = Vector3(*self.renderer.scene.cursor.position())
            self.editor.onContextMenu(world, self.renderer.mapToGlobal(QPoint(screen.x, screen.y)))

    def onMouseReleased(self, screen: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        ...

    def onKeyboardPressed(self, buttons: Set[int], keys: Set[int]) -> None:
        if self.snapCameraToSelected.satisfied(buttons, keys):
            for instance in self.editor.selectedInstances:
                self.renderer.snapCameraToPoint(instance.position)
                break

        if self.deleteSelected.satisfied(buttons, keys):
            self.editor.deleteSelected()

    def onKeyboardReleased(self, buttons: Set[int], keys: Set[int]) -> None:
        ...


class ModuleDesignerControl2dScheme:
    def __init__(self, editor: ModuleDesigner, renderer: WalkmeshRenderer):
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
        self.snapCameraToSelected: ControlItem = ControlItem(self.settings.snapCameraToSelected2dBind)
        self.openContextMenu: ControlItem = ControlItem((set(), {QtMouse.RightButton}))

    def onMouseScrolled(self, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        if self.zoomCamera.satisfied(buttons, keys):
            strength = self.settings.moveCameraSensitivity2d / 100 / 50
            self.renderer.camera.nudgeZoom(delta.y * strength)

    def onMouseMoved(self, screen: Vector2, screenDelta: Vector2, world: Vector2, worldDelta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
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
                instance.rotate(-instance.yaw() + rotation, 0, 0)

    def onMousePressed(self, screen: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        if self.selectUnderneath.satisfied(buttons, keys):
            if self.renderer.instancesUnderMouse():
                self.editor.setSelection([self.renderer.instancesUnderMouse()[-1]])
            else:
                self.editor.setSelection([])

        if self.openContextMenu.satisfied(buttons, keys):
            world = self.renderer.toWorldCoords(screen.x, screen.y)
            self.editor.onContextMenu(world, self.renderer.mapToGlobal(QPoint(screen.x, screen.y)))

    def onMouseReleased(self, screen: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        ...

    def onKeyboardPressed(self, buttons: Set[int], keys: Set[int]) -> None:
        if self.deleteSelected.satisfied(buttons, keys):
            self.editor.deleteSelected()

        if self.snapCameraToSelected.satisfied(buttons, keys):
            for instance in self.editor.selectedInstances:
                self.renderer.camera.setPosition(instance.position.x, instance.position.y)
                break

    def onKeyboardReleased(self, buttons: Set[int], keys: Set[int]) -> None:
        ...
