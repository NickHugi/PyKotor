import multiprocessing
from abc import ABC, abstractmethod
from contextlib import suppress
from time import sleep
from typing import Dict, List, Optional

from PyQt5 import QtCore
from PyQt5.QtCore import QSortFilterProxyModel, QModelIndex, QPoint, QThread
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QImage, QIcon, QPixmap, QTransform, QResizeEvent, QCloseEvent
from PyQt5.QtWidgets import QWidget, QListView, QMenu

from data.installation import HTInstallation
from pykotor.extract.installation import SearchLocation

from pykotor.extract.file import FileResource
from pykotor.resource.formats.tpc import TPC, TPCTextureFormat

from pykotor.resource.type import ResourceType
from utils.window import openResourceEditor

GFF_TYPES = [ResourceType.GFF, ResourceType.UTC, ResourceType.UTP, ResourceType.UTD, ResourceType.UTI,
             ResourceType.UTM, ResourceType.UTE, ResourceType.UTT, ResourceType.UTW, ResourceType.UTS,
             ResourceType.DLG, ResourceType.GUI, ResourceType.ARE, ResourceType.IFO, ResourceType.GIT,
             ResourceType.JRL, ResourceType.ITP]


class MainWindowList(QWidget):
    requestOpenResource = QtCore.pyqtSignal(object, object)

    requestExtractResource = QtCore.pyqtSignal(object)

    sectionChanged = QtCore.pyqtSignal(object)

    @abstractmethod
    def selectedResources(self) -> List[FileResource]:
        ...


class ResourceList(MainWindowList):
    requestReload = QtCore.pyqtSignal(object)

    requestRefresh = QtCore.pyqtSignal()

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        import windows.main.ui_resourcelist
        self.ui = windows.main.ui_resourcelist.Ui_Form()
        self.ui.setupUi(self)
        self.setupSignals()

        self.modulesModel = ResourceModel()
        self.modulesModel.proxyModel().setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.ui.resourceTree.setModel(self.modulesModel.proxyModel())

        self.sectionModel = QStandardItemModel()
        self.ui.sectionCombo.setModel(self.sectionModel)

    def setupSignals(self) -> None:
        self.ui.searchEdit.textEdited.connect(self.onFilterStringUpdated)
        self.ui.sectionCombo.currentIndexChanged.connect(self.onSectionChanged)
        self.ui.reloadButton.clicked.connect(self.onReloadClicked)
        self.ui.refreshButton.clicked.connect(self.onRefreshClicked)
        self.ui.resourceTree.customContextMenuRequested.connect(self.onResourceContextMenu)
        self.ui.resourceTree.doubleClicked.connect(self.onResourceDoubleClicked)

    def hideReloadButton(self) -> None:
        self.ui.reloadButton.setVisible(False)

    def hideSection(self) -> None:
        self.ui.line.setVisible(False)
        self.ui.sectionCombo.setVisible(False)
        self.ui.refreshButton.setVisible(False)

    def setResources(self, resources: List[FileResource]) -> None:
        allResources = self.modulesModel.allResourcesItems()

        # Add any missing resources to the list
        for resource in resources:
            for item in allResources:
                if item.resource == resource:
                    break
            else:
                self.modulesModel.addResource(resource)

        # Remove any resources that should no longer be in the list
        for item in allResources:
            if item.resource not in resources:
                item.parent().removeRow(item.row())

        # Remove unused categories
        self.modulesModel.removeUnusedCategories()

    def setSections(self, sections: List[QStandardItem]) -> None:
        self.sectionModel.clear()
        for section in sections:
            self.sectionModel.insertRow(self.sectionModel.rowCount(), section)

    def selectedResources(self) -> List[FileResource]:
        return self.modulesModel.resourceFromIndexes(self.ui.resourceTree.selectedIndexes())

    def onFilterStringUpdated(self) -> None:
        self.modulesModel.proxyModel().setFilterFixedString(self.ui.searchEdit.text())

    def onSectionChanged(self) -> None:
        self.sectionChanged.emit(self.ui.sectionCombo.currentData(QtCore.Qt.UserRole))

    def onReloadClicked(self) -> None:
        self.requestReload.emit(self.ui.sectionCombo.currentData(QtCore.Qt.UserRole))

    def onRefreshClicked(self) -> None:
        self.requestRefresh.emit()

    def onResourceContextMenu(self, point: QPoint) -> None:
        menu = QMenu(self)

        resources = self.selectedResources()
        if len(resources) == 1:
            resource = resources[0]
            if resource.restype() in GFF_TYPES:
                open1 = lambda: self.requestOpenResource.emit(resources, False)
                open2 = lambda: self.requestOpenResource.emit(resources, True)
                menu.addAction("Open").triggered.connect(open2)
                menu.addAction("Open with GFF Editor").triggered.connect(open1)

        menu.popup(self.ui.resourceTree.mapToGlobal(point))

    def onResourceDoubleClicked(self) -> None:
        self.requestOpenResource.emit(self.selectedResources(), None)


class ResourceModel(QStandardItemModel):
    """
    A data model used by the different trees (Core, Modules, Override). This class provides an easy way to add resources
    while sorting the into categories.
    """

    def __init__(self):
        super().__init__()
        self._categoryItems: Dict[str, QStandardItem] = {}
        self._proxyModel = QSortFilterProxyModel(self)
        self._proxyModel.setSourceModel(self)
        self._proxyModel.setRecursiveFilteringEnabled(True)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["ResRef", "Type"])

    def proxyModel(self) -> QSortFilterProxyModel:
        return self._proxyModel

    def clear(self) -> None:
        super().clear()
        self._categoryItems = {}
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["ResRef", "Type"])

    def _getCategoryItem(self, resourceType: ResourceType) -> QStandardItem:
        if resourceType.category not in self._categoryItems:
            categoryItem = QStandardItem(resourceType.category)
            categoryItem.setSelectable(False)
            unusedItem = QStandardItem("")
            unusedItem.setSelectable(False)
            self._categoryItems[resourceType.category] = categoryItem
            self.appendRow([categoryItem, unusedItem])
        return self._categoryItems[resourceType.category]

    def addResource(self, resource: FileResource) -> None:
        item1 = QStandardItem(resource.resname())
        item1.resource = resource
        item2 = QStandardItem(resource.restype().extension.upper())
        self._getCategoryItem(resource.restype()).appendRow([item1, item2])

    def resourceFromIndexes(self, indexes: List[QModelIndex], proxy: bool = True) -> List[FileResource]:
        items = []
        for index in indexes:
            sourceIndex = self._proxyModel.mapToSource(index) if proxy else index
            items.append(self.itemFromIndex(sourceIndex))
        return self.resourceFromItems(items)

    def resourceFromItems(self, items: List[QStandardItem]) -> List[FileResource]:
        return [item.resource for item in items if hasattr(item, 'resource')]

    def allResourcesItems(self) -> List[QStandardItem]:
        """
        Returns a list of all QStandardItem objects in the model that represents resource files.
        """
        resources = []
        for category in self._categoryItems.values():
            for i in range(category.rowCount()):
                resources.append(category.child(i, 0))
        return resources

    def removeUnusedCategories(self):
        for row in range(self.rowCount())[::-1]:
            item = self.item(row)
            if item.rowCount() == 0:
                del self._categoryItems[item.text()]
                self.removeRow(row)


class TextureList(MainWindowList):
    iconUpdate = QtCore.pyqtSignal(object, object)

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        import windows.main.ui_texturelist
        self.ui = windows.main.ui_texturelist.Ui_Form()
        self.ui.setupUi(self)
        self.setupSignals()

        self._installation: Optional[HTInstallation] = None

        self.texturesModel = QStandardItemModel()
        self.texturesProxyModel = QSortFilterProxyModel()
        self.texturesProxyModel.setSourceModel(self.texturesModel)
        self.ui.resourceList.setModel(self.texturesProxyModel)

        self.sectionModel = QStandardItemModel()
        self.ui.sectionCombo.setModel(self.sectionModel)

        self._taskQueue = multiprocessing.JoinableQueue()
        self._resultQueue = multiprocessing.Queue()
        self._consumers: List[TextureListConsumer] = [TextureListConsumer(self._taskQueue, self._resultQueue) for i in
                                                      range(multiprocessing.cpu_count())]
        [consumer.start() for consumer in self._consumers]

        self._scanner = QThread(self)
        self._scanner.run = self.scan
        self._scanner.start()

    def setupSignals(self) -> None:
        self.ui.searchEdit.textEdited.connect(self.onFilterStringUpdated)
        self.ui.sectionCombo.currentIndexChanged.connect(self.onSectionChanged)
        self.ui.resourceList.verticalScrollBar().valueChanged.connect(self.onTextureListScrolled)
        self.iconUpdate.connect(self.onIconUpdate)

    def doTerminations(self) -> None:
        self._scanner.terminate()
        [consumer.terminate() for consumer in self._consumers]

    def setInstallation(self, installation: HTInstallation) -> None:
        self._installation = installation

        if self._installation is not None:
            self.onTextureListScrolled()

    def setResources(self, resources: List[FileResource]) -> None:
        blankImage = QImage(bytes([0 for i in range(64 * 64 * 3)]), 64, 64, QImage.Format_RGB888)
        blankIcon = QIcon(QPixmap.fromImage(blankImage))

        self.texturesModel.clear()
        for resource in resources:
            item = QStandardItem(blankIcon, resource.resname())
            item.setToolTip(resource.resname())
            item.setData(False, QtCore.Qt.UserRole)
            self.texturesModel.appendRow(item)

        if self._installation is not None:
            self.onTextureListScrolled()

    def setSections(self, sections: List[QStandardItem]) -> None:
        self.sectionModel.clear()
        for section in sections:
            self.sectionModel.insertRow(self.sectionModel.rowCount(), section)

    def selectedResources(self) -> List[FileResource]:
        return self.modulesModel.resourceFromIndexes(self.ui.resourceList.selectedIndexes())

    def visibleItems(self) -> List[QStandardItem]:
        if self.texturesModel.rowCount() == 0:
            return []

        scanWidth = self.ui.resourceList.viewport().width()
        scanHeight = self.ui.resourceList.viewport().height()

        proxyModel = self.texturesProxyModel
        model = self.texturesModel

        firstItem = None
        firstIndex = None

        for y in range(2, 92, 2):
            for x in range(2, 92, 2):
                proxyIndex = self.ui.resourceList.indexAt(QPoint(x, y))
                index = proxyModel.mapToSource(proxyIndex)
                item = model.itemFromIndex(index)
                if not firstItem and item:
                    firstItem = item
                    firstIndex = proxyIndex
                    break

        items = []

        if firstItem:
            startRow = firstItem.row()
            widthCount = scanWidth // 92
            heightCount = scanHeight // 92 + 2
            numVisible = min(proxyModel.rowCount(), widthCount * heightCount)

            for i in range(numVisible):
                proxyIndex = proxyModel.index(firstIndex.row() + i, 0)
                sourceIndex = proxyModel.mapToSource(proxyIndex)
                item = model.itemFromIndex(sourceIndex)
                items.append(item)

        return items

    def scan(self) -> None:
        while True:
            for row, resname, width, height, data in iter(self._resultQueue.get, None):
                image = QImage(data, width, height, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(image).transformed(QTransform().scale(1, -1))
                item = self.texturesModel.item(row, 0)
                if item is not None:
                    self.iconUpdate.emit(item, QIcon(pixmap))

            sleep(0.1)

    def onFilterStringUpdated(self) -> None:
        self.modulesModel.proxyModel().setFilterFixedString(self.ui.searchEdit.text())

    def onSectionChanged(self) -> None:
        self.sectionChanged.emit(self.ui.sectionCombo.currentData(QtCore.Qt.UserRole))

    def onReloadClicked(self) -> None:
        self.requestReload.emit(self.ui.sectionCombo.currentData(QtCore.Qt.UserRole))

    def onRefreshClicked(self) -> None:
        self.requestRefresh.emit()

    def onTextureListScrolled(self) -> None:
        for item in self.visibleItems():
            tpc = self._installation.texture(item.text(), [SearchLocation.TEXTURES_GUI, SearchLocation.TEXTURES_TPA])
            tpc = TPC() if tpc is None else tpc

            task = TextureListTask(item.row(), tpc, item.text())
            self._taskQueue.put(task)
            item.setData(True, QtCore.Qt.UserRole)

    def onIconUpdate(self, item, icon):
        with suppress(RuntimeError):
            item.setIcon(icon)


class TextureListConsumer(multiprocessing.Process):
    def __init__(self, taskQueue, resultQueue):
        multiprocessing.Process.__init__(self)
        self.taskQueue: multiprocessing.JoinableQueue = taskQueue
        self.resultQueue: multiprocessing.Queue = resultQueue
        self.stopLoop: bool = False

    def run(self):
        while not self.stopLoop:
            next_task = self.taskQueue.get()

            answer = next_task()
            self.taskQueue.task_done()
            self.resultQueue.put(answer)


class TextureListTask:
    def __init__(self, row, tpc, resname):
        self.row = row
        self.tpc = tpc
        self.resname = resname

    def __repr__(self):
        return str(self.row)

    def __call__(self, *args, **kwargs):
        width, height, data = self.tpc.convert(TPCTextureFormat.RGB, self.bestMipmap(self.tpc))
        return self.row, self.resname, width, height, data

    def bestMipmap(self, tpc: TPC) -> int:
        for i in range(tpc.mipmap_count()):
            size = tpc.get(i).width
            if size <= 64:
                return i
        return 0
