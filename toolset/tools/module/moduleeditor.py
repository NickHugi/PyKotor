from PyQt5 import QtCore
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QMainWindow, QWidget, QOpenGLWidget, QTreeWidgetItem, QMenu, QAction, QListWidgetItem
from pykotor.common.module import Module, ModuleResource
from pykotor.common.stream import BinaryWriter
from pykotor.resource.generics.git import GITCreature, GITPlaceable, GITDoor, GITTrigger, GITEncounter, GITWaypoint, \
    GITSound, GITStore, GITCamera, GITInstance
from pykotor.resource.type import ResourceType

from data.installation import HTInstallation
from tools.module import moduleeditor_ui


class ModuleEditor(QMainWindow):
    def __init__(self, parent: QWidget, installation: HTInstallation, module: Module):
        super().__init__(parent)

        self._installation: HTInstallation = installation
        self._module: Module = module

        self.ui = moduleeditor_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupSignals()

        self.hideCreatures = False
        self.hidePlaceables = False
        self.hideDoors = False
        self.hideTriggers = False
        self.hideEncounters = False
        self.hideWaypoints = False
        self.hideSounds = False
        self.hideStores = False
        self.hideCameras = False

        self.rebuildResourceTree()
        self.rebuildInstanceList()

    def _setupSignals(self) -> None:
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
        self.parent().openResourceEditor(resource.active(), resource.resname(), resource.restype(), resource.data())

    def copyResourceToOverride(self, resource: ModuleResource) -> None:
        location = "{}/{}.{}".format(self._installation.override_path(), resource.resname(), resource.restype().extension)
        BinaryWriter.dump(location, resource.data())
        resource.add_locations([location])
        resource.activate(location)

    def onResourceTreeContextMenu(self, point: QPoint) -> None:
        menu = QMenu(self)

        data = self.ui.resourceTree.currentItem().data(0, QtCore.Qt.UserRole)
        if isinstance(data, ModuleResource):
            copyToOverrideAction = QAction("Copy To Override", self)
            copyToOverrideAction.triggered.connect(lambda _, r=data: self.copyResourceToOverride(r))

            menu.addAction("Edit Active File").triggered.connect(lambda _, r=data: self.openModuleResource(r))
            menu.addAction(copyToOverrideAction)
            menu.addSeparator()
            for location in data.locations():
                locationAciton = QAction(location, self)
                locationAciton.triggered.connect(lambda _, l=location: data.activate(l))
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

            icon = QIcon(iconMapping[type(instance)])
            reference = "" if instance.reference() is None else instance.reference().get()
            text = "[{}] {}".format(self._module.git().resource().index(instance), reference)
            item = QListWidgetItem(icon, text)
            item.setData(QtCore.Qt.UserRole, instance)
            self.ui.instanceList.addItem(item)

    def updateInstanceVisibility(self) -> None:
        self.hideCreatures = not self.ui.viewCreatureCheck.isChecked()
        self.hidePlaceables = not self.ui.viewPlaceableCheck.isChecked()
        self.hideDoors = not self.ui.viewDoorCheck.isChecked()
        self.hideTriggers = not self.ui.viewTriggerCheck.isChecked()
        self.hideEncounters = not self.ui.viewEncounterCheck.isChecked()
        self.hideWaypoints = not self.ui.viewWaypointCheck.isChecked()
        self.hideSounds = not self.ui.viewSoundCheck.isChecked()
        self.hideStores = not self.ui.viewStoreCheck.isChecked()
        self.hideCameras = not self.ui.viewCameraCheck.isChecked()
        self.rebuildInstanceList()


class ModuleRenderer(QOpenGLWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
