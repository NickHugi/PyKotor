import os
from contextlib import suppress
from typing import Set, Dict, Optional

from PyQt5 import QtCore
from PyQt5.QtCore import QPoint, QSettings
from PyQt5.QtGui import QPixmap, QIcon, QKeyEvent
from PyQt5.QtWidgets import QMainWindow, QWidget, QTreeWidgetItem, QMenu, QAction, QListWidgetItem, \
    QMessageBox, QCheckBox
from pykotor.common.geometry import Vector2
from pykotor.common.misc import ResRef
from pykotor.common.module import Module, ModuleResource
from pykotor.common.stream import BinaryWriter
from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.generics.git import GITCreature, GITPlaceable, GITDoor, GITTrigger, GITEncounter, GITWaypoint, \
    GITSound, GITStore, GITCamera, GITInstance
from pykotor.resource.type import ResourceType

from data.installation import HTInstallation
from gui.windows.help import HelpWindow
from pykotor.gl.scene import RenderObject, FocusedCamera

from data.me_controls import ModuleEditorControls, DynamicModuleEditorControls, HolocronModuleEditorControls
from utils.window import openResourceEditor


class ModuleDesigner(QMainWindow):
    def __init__(self, parent: Optional[QWidget], installation: HTInstallation, module: Module):
        super().__init__(parent)

        self._installation: HTInstallation = installation
        self._module: Module = module
        self.hideCreatures: bool = False
        self.hidePlaceables: bool = False
        self.hideDoors: bool = False
        self.hideTriggers: bool = False
        self.hideEncounters: bool = False
        self.hideWaypoints: bool = False
        self.hideSounds: bool = False
        self.hideStores: bool = False
        self.hideCameras: bool = False

        from toolset.uic.windows.module_designer import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupSignals()

        self.customControls: Dict[str, DynamicModuleEditorControls] = {}
        self.activeControls: ModuleEditorControls = HolocronModuleEditorControls(self.ui.mainRenderer)

        self.ui.mainRenderer.init(installation, module)
        self._setupControlsMenu()
        if "aurora.jsonc" in self.customControls:
            self.activateCustomControls(self.customControls["aurora.jsonc"])

        self._refreshWindowTitle()
        self.rebuildResourceTree()
        self.rebuildInstanceList()

    def _setupSignals(self) -> None:
        self.ui.actionSave.triggered.connect(self.saveGit)
        self.ui.actionInstructions.triggered.connect(self.showHelpWindow)

        self.ui.resourceTree.customContextMenuRequested.connect(self.onResourceTreeContextMenu)

        self.ui.viewCreatureCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewPlaceableCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewDoorCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewSoundCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewTriggerCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewEncounterCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewWaypointCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewCameraCheck.toggled.connect(self.updateInstanceVisibility)
        self.ui.viewStoreCheck.toggled.connect(self.updateInstanceVisibility)

        self.ui.viewCreatureCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisiblityDoubleClick(self.ui.viewCreatureCheck)
        self.ui.viewPlaceableCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisiblityDoubleClick(self.ui.viewPlaceableCheck)
        self.ui.viewDoorCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisiblityDoubleClick(self.ui.viewDoorCheck)
        self.ui.viewSoundCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisiblityDoubleClick(self.ui.viewSoundCheck)
        self.ui.viewTriggerCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisiblityDoubleClick(self.ui.viewTriggerCheck)
        self.ui.viewEncounterCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisiblityDoubleClick(self.ui.viewEncounterCheck)
        self.ui.viewWaypointCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisiblityDoubleClick(self.ui.viewWaypointCheck)
        self.ui.viewCameraCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisiblityDoubleClick(self.ui.viewCameraCheck)
        self.ui.viewStoreCheck.mouseDoubleClickEvent = lambda _: self.onInstanceVisiblityDoubleClick(self.ui.viewStoreCheck)

        self.ui.instanceList.doubleClicked.connect(self.onInstanceListDoubleClicked)

        self.ui.mainRenderer.sceneInitalized.connect(self.onRendererSceneInitialized)
        self.ui.mainRenderer.mousePressed.connect(self.onRendererMousePressed)
        self.ui.mainRenderer.mouseMoved.connect(self.onRendererMouseMoved)
        self.ui.mainRenderer.mouseScrolled.connect(self.onRendererMouseScrolled)
        self.ui.mainRenderer.objectSelected.connect(self.onRendererObjectSelected)
        self.ui.mainRenderer.customContextMenuRequested.connect(self.onRendererContextMenu)

    def _setupControlsMenu(self) -> None:
        self.ui.menuControls.clear()
        folder = "./controls/3d/"
        if os.path.exists(folder):
            for path in [path for path in os.listdir(folder) if path.endswith(".json") or path.endswith(".jsonc")]:
                with suppress(Exception):
                    controls = DynamicModuleEditorControls(self.ui.mainRenderer)
                    controls.load(folder + path)
                    self.customControls[path] = controls

                    action = QAction(controls.name, self)
                    action.triggered.connect(lambda _, c=controls: self.activateCustomControls(c))
                    self.ui.menuControls.addAction(action)

            self.ui.menuControls.addSeparator()
            action = QAction("Reload", self)
            action.triggered.connect(self._setupControlsMenu)
            self.ui.menuControls.addAction(action)

    def _refreshWindowTitle(self) -> None:
        title = "{} - {} - Module Editor".format(self._module._id, self._installation.name)
        self.setWindowTitle(title)

    def showHelpWindow(self) -> None:
        window = HelpWindow(self, "./help/tools/1-moduleEditor.md")
        window.show()

    def saveGit(self) -> None:
        self._module.git().save()

    def activateCustomControls(self, controls: DynamicModuleEditorControls) -> None:
        self.activeControls = controls

    def rebuildResourceTree(self) -> None:
        self.ui.resourceTree.clear()
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

    def selectResouceItem(self, instance: GITInstance, clearExisting: bool = True) -> None:
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

    def rebuildInstanceList(self) -> None:
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

    def onInstanceVisiblityDoubleClick(self, checkbox: QCheckBox) -> None:
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

    def updateInstanceVisibility(self) -> None:
        self.hideCreatures = self.ui.mainRenderer.scene.hide_creatures = not self.ui.viewCreatureCheck.isChecked()
        self.hidePlaceables = self.ui.mainRenderer.scene.hide_placeables = not self.ui.viewPlaceableCheck.isChecked()
        self.hideDoors = self.ui.mainRenderer.scene.hide_doors = not self.ui.viewDoorCheck.isChecked()
        self.hideTriggers = self.ui.mainRenderer.scene.hide_triggers = not self.ui.viewTriggerCheck.isChecked()
        self.hideEncounters = self.ui.mainRenderer.scene.hide_encounters = not self.ui.viewEncounterCheck.isChecked()
        self.hideWaypoints = self.ui.mainRenderer.scene.hide_waypoints = not self.ui.viewWaypointCheck.isChecked()
        self.hideSounds = self.ui.mainRenderer.scene.hide_sounds = not self.ui.viewSoundCheck.isChecked()
        self.hideStores = self.ui.mainRenderer.scene.hide_stores = not self.ui.viewStoreCheck.isChecked()
        self.hideCameras = self.ui.mainRenderer.scene.hide_cameras = not self.ui.viewCameraCheck.isChecked()
        self.rebuildInstanceList()

    def onInstanceListDoubleClicked(self) -> None:
        if self.ui.instanceList.selectedItems():
            item = self.ui.instanceList.selectedItems()[0]
            instance: GITInstance = item.data(QtCore.Qt.UserRole)
            self.ui.mainRenderer.scene.select(instance)

            self.selectResouceItem(item.data(QtCore.Qt.UserRole))
            self.ui.mainRenderer.snapCameraToPoint(instance.position)

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

    def removeSelectedInstances(self) -> None:
        for selected in self.ui.mainRenderer.scene.selection:
            if isinstance(selected.data, GITInstance):
                self._module.git().resource().remove(selected.data)
        self.ui.mainRenderer.scene.selection.clear()

    def onRendererMouseMoved(self, screen: Vector2, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        self.activeControls.onMouseMoved(screen, delta, buttons, keys)

    def onRendererMouseScrolled(self, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        self.activeControls.onMouseScrolled(delta, buttons, keys)

    def onRendererMousePressed(self, screen: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        self.activeControls.onMousePressed(screen, buttons, keys)

    def onRendererObjectSelected(self, obj: RenderObject) -> None:
        if obj is not None:
            data = obj.data
            self.selectInstanceItemOnList(data)
            self.selectResouceItem(data)

    def onRendererContextMenu(self, point: QPoint) -> None:
        menu = QMenu(self)
        world = self.ui.mainRenderer.walkmeshPoint(self.ui.mainRenderer.scene.camera.x, self.ui.mainRenderer.scene.camera.y)

        if len(self.ui.mainRenderer.scene.selection) == 0:
            view = self.ui.mainRenderer.scene.camera.truePosition()
            rot = self.ui.mainRenderer.scene.camera
            menu.addAction("Insert Camera").triggered.connect(lambda: self.addInstance(GITCamera(world.x, world.y)))
            menu.addAction("Insert Camera at View").triggered.connect(lambda: self.addInstance(GITCamera(view.x, view.y, view.z, rot.yaw, rot.pitch, 0, 69), False))
            menu.addSeparator()
            menu.addAction("Insert Creature").triggered.connect(lambda: self.addInstance(GITCreature(world.x, world.y)))
            menu.addAction("Insert Door").triggered.connect(lambda: self.addInstance(GITDoor(world.x, world.y)))
            menu.addAction("Insert Placeable").triggered.connect(lambda: self.addInstance(GITPlaceable(world.x, world.y)))
            menu.addAction("Insert Store").triggered.connect(lambda: self.addInstance(GITStore(world.x, world.y)))
            menu.addAction("Insert Sound").triggered.connect(lambda: self.addInstance(GITSound(world.x, world.y)))
            menu.addAction("Insert Waypoint").triggered.connect(lambda: self.addInstance(GITWaypoint(world.x, world.y)))
            menu.addAction("Insert Encounter").triggered.connect(lambda: self.addInstance(GITEncounter(world.x, world.y)))
            menu.addAction("Insert Trigger").triggered.connect(lambda: self.addInstance(GITTrigger(world.x, world.y)))
        else:
            menu.addAction("Remove").triggered.connect(self.removeSelectedInstances)

        menu.popup(self.ui.mainRenderer.mapToGlobal(point))
        menu.aboutToHide.connect(self.ui.mainRenderer.resetMouseButtons)

    def onRendererSceneInitialized(self) -> None:
        if self.activeControls.cameraStyle == "FOCUSED":
            self.ui.mainRenderer.scene.camera = FocusedCamera.from_unfocused(self.ui.mainRenderer.scene.camera)

    def keyPressEvent(self, e: QKeyEvent, bubble: bool = True) -> None:
        super().keyPressEvent(e)
        if bubble:
            self.ui.mainRenderer.keyPressEvent(e, False)
        self.activeControls.onKeyPressed(self.ui.mainRenderer.mouseDown(), self.ui.mainRenderer.keysDown())

    def keyReleaseEvent(self, e: QKeyEvent, bubble: bool = True) -> None:
        super().keyReleaseEvent(e)
        if bubble:
            self.ui.mainRenderer.keyReleaseEvent(e, False)
        self.activeControls.onKeyReleased(self.ui.mainRenderer.mouseDown(), self.ui.mainRenderer.keysDown())


class ModuleDesignerSettings:
    def __init__(self):
        self.settings = QSettings('HolocronToolset', 'ModuleDesigner')

    # region Ints
    @property
    def fieldOfView(self) -> int:
        return self.settings.value('fieldOfView', 80, int)

    @fieldOfView.setter
    def fieldOfView(self, value: int) -> None:
        self.settings.setValue('fieldOfView', value)
    # endregion