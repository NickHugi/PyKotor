import os
from contextlib import suppress
from typing import Set, Dict, Optional, List

from PyQt5 import QtCore
from PyQt5.QtCore import QPoint, QSettings, QTimer
from PyQt5.QtGui import QPixmap, QIcon, QKeyEvent
from PyQt5.QtWidgets import QMainWindow, QWidget, QTreeWidgetItem, QMenu, QAction, QListWidgetItem, \
    QMessageBox, QCheckBox, QFileDialog

from data.misc import Bind, ControlItem
from gui.dialogs.insert_instance import InsertInstanceDialog
from gui.dialogs.select_module import SelectModuleDialog
from gui.widgets.settings.module_designer import ModuleDesignerSettings
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
from pykotor.gl.scene import RenderObject, Camera

from data.me_controls import ModuleEditorControls, DynamicModuleEditorControls, HolocronModuleEditorControls
from utils.misc import QtKey, QtMouse
from utils.window import openResourceEditor


class ModuleDesigner(QMainWindow):
    def __init__(self, parent: Optional[QWidget], installation: HTInstallation):
        super().__init__(parent)

        self._installation: HTInstallation = installation
        self._module: Optional[Module] = None
        self._controls: ModuleDesignerControlScheme = ModuleDesignerControlScheme(self)

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

        self.selectedInstances: List[GITInstance] = []

        from toolset.uic.windows.module_designer import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupSignals()

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
        self.ui.mainRenderer.keyboardPressed.connect(self.onKeyboardPressed)
        self.ui.mainRenderer.objectSelected.connect(self.onRendererObjectSelected)
        self.ui.mainRenderer.customContextMenuRequested.connect(self.onRendererContextMenu)

    def _refreshWindowTitle(self) -> None:
        if self._module is None:
            title = "No Module - {} - Module Editor".format(self._installation.name)
        else:
            title = "{} - {} - Module Editor".format(self._module._id, self._installation.name)
        self.setWindowTitle(title)

    def openModule(self) -> None:
        dialog = SelectModuleDialog(self, self._installation)

        if dialog.exec_():
            self.unloadModule()
            self._module = Module(dialog.module, self._installation)
            self.ui.mainRenderer.init(self._installation, self._module)

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

    def updateToggles(self) -> None:
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

            self.selectResourceItem(item.data(QtCore.Qt.UserRole))
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

    # region State Methods
    def snapCameraToInstance(self) -> None:
        for instance in self.selectedInstances:
            self.ui.mainRenderer.snapCameraToPoint(instance.position)
            break

    def deleteSelected(self) -> None:
        for instance in self.selectedInstances:
            self._module.git().resource().remove(instance)

        self.selectedInstances.clear()
        self.ui.mainRenderer.scene.selection.clear()
        self.rebuildInstanceList()

    def moveCamera(self, x: float, y: float) -> None:
        forward = -y * self.ui.mainRenderer.scene.camera.forward()
        sideward = x * self.ui.mainRenderer.scene.camera.sideward()
        self.ui.mainRenderer.scene.camera.x -= (forward.x + sideward.x) / 10
        self.ui.mainRenderer.scene.camera.y -= (forward.y + sideward.y) / 10

    def rotateCamera(self, yaw: float, pitch: float) -> None:
        self.ui.mainRenderer.rotateCamera(-yaw/150, pitch/150)

    def zoomCamera(self, amount: float) -> None:
        self.ui.mainRenderer.scene.camera.distance += amount

    def selectUnderneath(self) -> None:
        self.ui.mainRenderer.doSelect = True

    def moveSelected(self, x: float, y: float) -> None:
        if self.ui.lockInstancesCheck.isChecked():
            return

        forward = -y * self.ui.mainRenderer.scene.camera.forward()
        sideward = x * self.ui.mainRenderer.scene.camera.sideward()

        for instance in self.selectedInstances:
            instance.position.x += (forward.x + sideward.x) / 10
            instance.position.y += (forward.y + sideward.y) / 10
            instance.position.z = self.ui.mainRenderer.walkmeshPoint(instance.position.x, instance.position.y).z

    def rotateSelected(self, x: float, y: float) -> None:
        if self.ui.lockInstancesCheck.isChecked():
            return

        for instance in self.selectedInstances:
            instance.rotate(x/60, 0.0, 0.0)
    # endregion

    # region Signal Callbacks
    def onRendererMouseMoved(self, screen: Vector2, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        self._controls.onMouseMoved(screen, delta, None, None, buttons, keys)

    def onRendererMouseScrolled(self, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        self._controls.onMouseScrolled(delta, buttons, keys)

    def onRendererMousePressed(self, screen: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        self._controls.onMousePressed(screen, buttons, keys)

    def onKeyboardPressed(self, buttons: Set[int], keys: Set[int]) -> None:
        self._controls.onKeyboardPressed(buttons, keys)

    def onRendererObjectSelected(self, instance: GITInstance) -> None:
        if instance is not None:
            self.selectedInstances = [instance]

            self.ui.mainRenderer.scene.select(instance, True)
            self.selectInstanceItemOnList(instance)
            self.selectResourceItem(instance)
        else:
            self.selectedInstances = []
            self.ui.mainRenderer.scene.selection.clear()

    def onRendererContextMenu(self, point: QPoint) -> None:
        if self._module is None:
            return

        menu = QMenu(self)
        world = self.ui.mainRenderer.walkmeshPoint(self.ui.mainRenderer.scene.camera.x, self.ui.mainRenderer.scene.camera.y)

        if len(self.ui.mainRenderer.scene.selection) == 0:
            view = self.ui.mainRenderer.scene.camera.truePosition()
            rot = self.ui.mainRenderer.scene.camera
            menu.addAction("Insert Camera").triggered.connect(lambda: self.addInstance(GITCamera(world.x, world.y)))
            menu.addAction("Insert Camera at View").triggered.connect(lambda: self.addInstance(GITCamera(view.x, view.y, view.z, rot.yaw, rot.pitch, 0, 0), False))
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
        self.rebuildResourceTree()
        self.rebuildInstanceList()
        self._refreshWindowTitle()
    # endregion

    # region Events
    def keyPressEvent(self, e: QKeyEvent, bubble: bool = True) -> None:
        super().keyPressEvent(e)

    def keyReleaseEvent(self, e: QKeyEvent, bubble: bool = True) -> None:
        super().keyReleaseEvent(e)
    # endregion


class ModuleDesignerControlScheme:
    def __init__(self, editor: ModuleDesigner):
        self.editor: ModuleDesigner = editor
        self.settings: ModuleDesignerSettings = ModuleDesignerSettings()

        self.panCamera: ControlItem = ControlItem(self.settings.panCamera3dBind)
        self.rotateCamera: ControlItem = ControlItem(self.settings.rotateCamera3dBind)
        self.zoomCamera: ControlItem = ControlItem(self.settings.zoomCamera3dBind)
        self.rotateSelected: ControlItem = ControlItem(self.settings.rotateSelected3dBind)
        self.moveSelected: ControlItem = ControlItem(self.settings.moveSelected3dBind)
        self.selectUnderneath: ControlItem = ControlItem(self.settings.selectUnderneath3dBind)
        self.snapCameraToSelected: ControlItem = ControlItem(self.settings.snapCameraToSelected3dBind)
        self.deleteSelected: ControlItem = ControlItem(self.settings.deleteSelected3dBind)
        self.openContextMenu: ControlItem = ControlItem((set(), {QtMouse.RightButton}))

    def onMouseScrolled(self, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        if self.zoomCamera.satisfied(buttons, keys):
            self.editor.zoomCamera(-delta.y/60)

    def onMouseMoved(self, screen: Vector2, screenDelta: Vector2, world: Vector2, worldDelta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        if self.panCamera.satisfied(buttons, keys):
            self.editor.moveCamera(screenDelta.x, screenDelta.y)
        if self.rotateCamera.satisfied(buttons, keys):
            self.editor.rotateCamera(screenDelta.x, screenDelta.y)
        if self.moveSelected.satisfied(buttons, keys):
            self.editor.moveSelected(screenDelta.x, screenDelta.y)
        if self.rotateSelected.satisfied(buttons, keys):
            self.editor.rotateSelected(screenDelta.x, screenDelta.y)

    def onMousePressed(self, screen: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        if self.selectUnderneath.satisfied(buttons, keys):
            self.editor.selectUnderneath()
        if self.openContextMenu.satisfied(buttons, keys):
            self.editor.onRendererContextMenu(QPoint(screen.x, screen.y))

    def onMouseReleased(self, screen: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        ...

    def onKeyboardPressed(self, buttons: Set[int], keys: Set[int]) -> None:
        if self.snapCameraToSelected.satisfied(buttons, keys):
            self.editor.snapCameraToInstance()
        if self.deleteSelected.satisfied(buttons, keys):
            self.editor.deleteSelected()

    def onKeyboardReleased(self, buttons: Set[int], keys: Set[int]) -> None:
        ...
