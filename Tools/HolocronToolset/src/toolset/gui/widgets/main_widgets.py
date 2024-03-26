from __future__ import annotations

import multiprocessing

from abc import abstractmethod
from time import sleep
from typing import TYPE_CHECKING

from PyQt5 import QtCore
from PyQt5.QtCore import QPoint, QSortFilterProxyModel, QThread, QTimer, Qt
from PyQt5.QtGui import QIcon, QImage, QPixmap, QStandardItem, QStandardItemModel, QTransform
from PyQt5.QtWidgets import QHeaderView, QMenu, QWidget

from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.tpc import TPC, TPCTextureFormat
from utility.error_handling import format_exception_with_variables

if TYPE_CHECKING:
    from PyQt5.QtCore import QModelIndex
    from PyQt5.QtGui import QResizeEvent

    from pykotor.common.misc import CaseInsensitiveDict
    from pykotor.extract.file import FileResource
    from pykotor.resource.type import ResourceType
    from toolset.data.installation import HTInstallation


class MainWindowList(QWidget):
    requestOpenResource = QtCore.pyqtSignal(object, object)

    requestExtractResource = QtCore.pyqtSignal(object)

    sectionChanged = QtCore.pyqtSignal(object)

    @abstractmethod
    def selectedResources(self) -> list[FileResource]: ...


class ResourceList(MainWindowList):
    requestReload = QtCore.pyqtSignal(object)

    requestRefresh = QtCore.pyqtSignal()

    def __init__(self, parent: QWidget):
        """Initializes the ResourceList widget.

        Args:
        ----
            parent (QWidget): The parent widget

        Processing Logic:
        ----------------
            - Initializes the UI from the designer file
            - Sets up the signal connections
            - Creates a ResourceModel and sets it as the model for the tree view
            - Creates a QStandardItemModel for the section combo box
            - Sets the section model as the model for the combo box.
        """
        super().__init__(parent)

        from toolset.uic.widgets.resource_list import Ui_Form  # pylint: disable=C0415

        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setupSignals()

        self.modulesModel = ResourceModel()
        self.modulesModel.proxyModel().setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.ui.resourceTree.setModel(self.modulesModel.proxyModel())
        self.ui.resourceTree.sortByColumn(0, QtCore.Qt.AscendingOrder)

        self.sectionModel = QStandardItemModel()
        self.ui.sectionCombo.setModel(self.sectionModel)

    def setupSignals(self):
        self.ui.searchEdit.textEdited.connect(self.onFilterStringUpdated)
        self.ui.sectionCombo.currentIndexChanged.connect(self.onSectionChanged)
        self.ui.reloadButton.clicked.connect(self.onReloadClicked)
        self.ui.refreshButton.clicked.connect(self.onRefreshClicked)
        self.ui.resourceTree.customContextMenuRequested.connect(self.onResourceContextMenu)
        self.ui.resourceTree.doubleClicked.connect(self.onResourceDoubleClicked)

    def hideReloadButton(self):
        self.ui.reloadButton.setVisible(False)

    def hideSection(self):
        self.ui.line.setVisible(False)
        self.ui.sectionCombo.setVisible(False)
        self.ui.refreshButton.setVisible(False)

    def currentSection(self) -> str:
        return self.ui.sectionCombo.currentData()

    def changeSection(self, section: str):
        for i in range(self.ui.sectionCombo.count()):
            if section in self.ui.sectionCombo.itemText(i):
                self.ui.sectionCombo.setCurrentIndex(i)

    def setResources(self, resources: list[FileResource], customCategory: str | None = None, *, clear_existing: bool = True):
        """Adds and removes FileResources from the modules model.

        Args:
        ----
            resources: {list[FileResource]}: List of FileResource objects to set

        Processing Logic:
        ----------------
            - Loops through allResources and resources to find matching resources and update references
            - Loops through allResources to find non-matching resources and removes them
            - Removes any unused categories from the model.
        """
        allResources: list[QStandardItem] = self.modulesModel.allResourcesItems()

        # Convert the list of resources to a set for O(1) lookup times
        resourceSet: set[FileResource] = set(resources)

        # Create a mapping of existing resources to their items for quick access
        resourceItemMap: dict[FileResource, QStandardItem] = {item.resource: item for item in allResources}

        # Add or update resources
        for resource in resourceSet:
            if resource in resourceItemMap:
                # Update existing resource item
                resourceItemMap[resource].resource = resource
            else:
                # Add new resource
                self.modulesModel.addResource(resource, customCategory)

        if clear_existing:
            # Identify and remove non-matching resources if they are not in the updated resources set
            for item in allResources:
                if item.resource in resourceSet:
                    continue
                item.parent().removeRow(item.row())

        # Remove unused categories
        self.modulesModel.removeUnusedCategories()

    def setSections(self, sections: list[QStandardItem]):
        self.sectionModel.clear()
        for section in sections:
            self.sectionModel.insertRow(self.sectionModel.rowCount(), section)

    def setResourceSelection(self, resource: FileResource):
        """Sets the selected resource in the resource tree.

        Args:
        ----
            resource (FileResource): The resource to select

        Processing Logic:
        ----------------
            - Loops through all resources in the model to find matching resource
            - Expands the parent item in the tree
            - Scrolls to and selects the matching child item.
        """
        model = self.ui.resourceTree.model().sourceModel()

        def select(parent, child):
            self.ui.resourceTree.expand(parent)
            self.ui.resourceTree.scrollTo(child)
            self.ui.resourceTree.setCurrentIndex(child)

        for item in model.allResourcesItems():
            resource_from_item: FileResource = item.resource
            if resource_from_item.identifier() == resource.identifier():
                _parentIndex = model.proxyModel().mapFromSource(item.parent().index())  # TODO: why is this unused
                itemIndex = model.proxyModel().mapFromSource(item.index())
                QTimer.singleShot(1, lambda index=itemIndex, item=item: select(item.parent().index(), index))

    def selectedResources(self) -> list[FileResource]:
        return self.modulesModel.resourceFromIndexes(self.ui.resourceTree.selectedIndexes())

    def onFilterStringUpdated(self):
        self.modulesModel.proxyModel().setFilterFixedString(self.ui.searchEdit.text())

    def onSectionChanged(self):
        self.sectionChanged.emit(self.ui.sectionCombo.currentData(QtCore.Qt.UserRole))

    def onReloadClicked(self):
        self.requestReload.emit(self.ui.sectionCombo.currentData(QtCore.Qt.UserRole))

    def onRefreshClicked(self):
        self.requestRefresh.emit()

    def onResourceContextMenu(self, point: QPoint):
        """Shows context menu for selected resources.

        Args:
        ----
            point: QPoint - Mouse position for context menu

        Processing Logic:
        ----------------
            - Create QMenu at mouse position
            - Get selected resources
            - If single resource and GFF type:
                - Add "Open" and "Open with GFF Editor" actions
                - Connect actions to emit signals to open resource.
        """
        resources: list[FileResource] = self.selectedResources()
        if len(resources) == 1:
            resource: FileResource = resources[0]
            if resource.restype().contents == "gff":
                menu = QMenu(self)

                def open1():
                    return self.requestOpenResource.emit(resources, False)

                def open2():
                    return self.requestOpenResource.emit(resources, True)

                menu.addAction("Open").triggered.connect(open2)
                menu.addAction("Open with GFF Editor").triggered.connect(open1)

                menu.popup(self.ui.resourceTree.mapToGlobal(point))

    def onResourceDoubleClicked(self):
        self.requestOpenResource.emit(self.selectedResources(), None)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.ui.resourceTree.setColumnWidth(1, 10)
        self.ui.resourceTree.setColumnWidth(0, self.ui.resourceTree.width() - 80)
        self.ui.resourceTree.header().setSectionResizeMode(QHeaderView.Fixed)


class ResourceModel(QStandardItemModel):
    """A data model used by the different trees (Core, Modules, Override).

    This class provides an easy way to add resources while sorting them into categories.
    """

    def __init__(self):
        super().__init__()
        self._categoryItems: dict[str, QStandardItem] = {}
        self._proxyModel = QSortFilterProxyModel(self)
        self._proxyModel.setSourceModel(self)
        self._proxyModel.setRecursiveFilteringEnabled(True)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["ResRef", "Type"])

    def proxyModel(self) -> QSortFilterProxyModel:
        return self._proxyModel

    def clear(self):
        super().clear()
        self._categoryItems = {}
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["ResRef", "Type"])

    def _addResourceIntoCategory(
        self,
        resourceType: ResourceType,
        customCategory: str | None = None,
    ) -> QStandardItem:
        chosen_category = resourceType.category if customCategory is None else customCategory
        if chosen_category not in self._categoryItems:
            categoryItem = QStandardItem(chosen_category)
            categoryItem.setSelectable(False)
            unusedItem = QStandardItem("")
            unusedItem.setSelectable(False)
            self._categoryItems[chosen_category] = categoryItem
            self.appendRow([categoryItem, unusedItem])
        return self._categoryItems[chosen_category]

    def addResource(self, resource: FileResource, customCategory: str | None = None):
        item1 = QStandardItem(resource.resname())
        item1.resource = resource
        item2 = QStandardItem(resource.restype().extension.upper())
        self._addResourceIntoCategory(resource.restype(), customCategory).appendRow([item1, item2])

    def resourceFromIndexes(self, indexes: list[QModelIndex], *, proxy: bool = True) -> list[FileResource]:
        items = []
        for index in indexes:
            sourceIndex = self._proxyModel.mapToSource(index) if proxy else index
            items.append(self.itemFromIndex(sourceIndex))
        return self.resourceFromItems(items)

    def resourceFromItems(self, items: list[QStandardItem]) -> list[FileResource]:
        return [item.resource for item in items if hasattr(item, "resource")]  # type: ignore[reportAttributeAccessIssue]

    def allResourcesItems(self) -> list[QStandardItem]:
        """Returns a list of all QStandardItem objects in the model that represent resource files."""
        resources = (category.child(i, 0) for category in self._categoryItems.values() for i in range(category.rowCount()))
        return [item for item in resources if item is not None]

    def removeUnusedCategories(self):
        for row in range(self.rowCount())[::-1]:
            item = self.item(row)
            if item.rowCount() != 0:
                continue
            text = item.text()
            if text not in self._categoryItems:
                continue
            del self._categoryItems[text]
            self.removeRow(row)


class TextureList(MainWindowList):
    requestReload = QtCore.pyqtSignal(object)  # TODO:

    requestRefresh = QtCore.pyqtSignal()  # TODO:
    iconUpdate = QtCore.pyqtSignal(object, object)

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        from toolset.uic.widgets.texture_list import Ui_Form  # pylint: disable=C0415

        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setupSignals()

        self._installation: HTInstallation | None = None
        self._scannedTextures: set[str] = set()

        self.texturesModel = QStandardItemModel()
        self.texturesProxyModel = QSortFilterProxyModel()
        self.texturesProxyModel.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.texturesProxyModel.setSourceModel(self.texturesModel)
        self.ui.resourceList.setModel(self.texturesProxyModel)

        self.sectionModel = QStandardItemModel()
        self.ui.sectionCombo.setModel(self.sectionModel)

        self._taskQueue = multiprocessing.JoinableQueue()
        self._resultQueue = multiprocessing.Queue()
        self._consumers: list[TextureListConsumer] = [TextureListConsumer(self._taskQueue, self._resultQueue) for _ in range(multiprocessing.cpu_count())]
        for consumer in self._consumers:
            consumer.start()

        self._scanner = QThread(self)
        self._scanner.run = self.scan
        self._scanner.start()

    def setupSignals(self):
        self.ui.searchEdit.textEdited.connect(self.onFilterStringUpdated)
        self.ui.sectionCombo.currentIndexChanged.connect(self.onSectionChanged)
        self.ui.resourceList.doubleClicked.connect(self.onResourceDoubleClicked)
        self.iconUpdate.connect(self.onIconUpdate)

        self.ui.resourceList.verticalScrollBar().valueChanged.connect(self.onTextureListScrolled)
        self.ui.searchEdit.textChanged.connect(self.onTextureListScrolled)

    def doTerminations(self):
        self._scanner.terminate()
        for consumer in self._consumers:
            consumer.terminate()

    def setInstallation(self, installation: HTInstallation):
        self._installation = installation

    def setResources(self, resources: list[FileResource]):
        blankImage = QImage(bytes(0 for _ in range(64 * 64 * 3)), 64, 64, QImage.Format_RGB888)
        blankIcon = QIcon(QPixmap.fromImage(blankImage))

        self.texturesModel.clear()
        for resource in resources:
            item = QStandardItem(blankIcon, resource.resname())
            item.setToolTip(resource.resname())
            item.setData(False, QtCore.Qt.UserRole)
            item.setData(resource, QtCore.Qt.UserRole + 1)
            self.texturesModel.appendRow(item)

        if self._installation is not None:
            self.onTextureListScrolled()

    def setSections(self, sections: list[QStandardItem]):
        self.sectionModel.clear()
        for section in sections:
            self.sectionModel.insertRow(self.sectionModel.rowCount(), section)

    def selectedResources(self) -> list[FileResource]:
        resources: list[FileResource] = []
        for proxyIndex in self.ui.resourceList.selectedIndexes():
            sourceIndex = self.texturesProxyModel.mapToSource(proxyIndex)
            item = self.texturesModel.item(sourceIndex.row())
            resources.append(item.data(QtCore.Qt.UserRole + 1))
        return resources

    def visibleItems(self) -> list[QStandardItem]:
        if self.texturesModel.rowCount() == 0:
            return []

        scanWidth: int = self.parent().width()
        scanHeight: int = self.parent().height()

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

        items: list[QStandardItem] = []

        if firstItem:
            _startRow: int = firstItem.row()
            widthCount: int = scanWidth // 92
            heightCount: int = scanHeight // 92 + 2
            numVisible: int = min(proxyModel.rowCount(), widthCount * heightCount)

            for i in range(numVisible):
                proxyIndex: QModelIndex = proxyModel.index(firstIndex.row() + i, 0)
                sourceIndex: QModelIndex = proxyModel.mapToSource(proxyIndex)
                item: QStandardItem | None = model.itemFromIndex(sourceIndex)
                if item is not None:
                    items.append(item)

        return items

    def scan(self):
        while True:
            for row, _resname, width, height, data in iter(self._resultQueue.get, None):
                image = QImage(data, width, height, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(image).transformed(QTransform().scale(1, -1))
                item = self.texturesModel.item(row, 0)
                if item is not None:
                    self.iconUpdate.emit(item, QIcon(pixmap))

            sleep(0.1)

    def onFilterStringUpdated(self):
        self.texturesProxyModel.setFilterFixedString(self.ui.searchEdit.text())

    def onSectionChanged(self):
        self.sectionChanged.emit(self.ui.sectionCombo.currentData(QtCore.Qt.UserRole))

    def onReloadClicked(self):
        self.requestReload.emit(self.ui.sectionCombo.currentData(QtCore.Qt.UserRole))

    def onRefreshClicked(self):
        self.requestRefresh.emit()

    def onTextureListScrolled(self):
        if self._installation is None:
            print("No installation loaded, nothing to scroll through?")
            return
        # Note: Avoid redundantly loading textures that have already been loaded
        textures: CaseInsensitiveDict[TPC | None] = self._installation.textures(
            [item.text() for item in self.visibleItems() if item.text().casefold() not in self._scannedTextures],
            [SearchLocation.TEXTURES_GUI, SearchLocation.TEXTURES_TPA],
        )

        # Emit signals to load textures that have not had their icons assigned
        for item in [item for item in self.visibleItems() if item.text().casefold() not in self._scannedTextures]:
            item_text = item.text()

            # Avoid trying to load the same texture multiple times.
            self._scannedTextures.add(item_text.casefold())

            cache_tpc: TPC | None = textures.get(item_text)
            tpc: TPC = cache_tpc if cache_tpc is not None else TPC()

            task = TextureListTask(item.row(), tpc, item_text)
            self._taskQueue.put(task)
            item.setData(True, QtCore.Qt.UserRole)

    def onIconUpdate(
        self,
        item: QStandardItem,
        icon,
    ):
        try:  # FIXME: there's a race condition happening somewhere, causing the item to have previously been deleted.
            item.setIcon(icon)
        except RuntimeError as e:
            print(format_exception_with_variables(e, message="This exception has been suppressed."))

    def onResourceDoubleClicked(self):
        self.requestOpenResource.emit(self.selectedResources(), None)

    def resizeEvent(self, a0: QResizeEvent):  # pylint: disable=W0613
        # Trigger the scroll slot method - this will cause any newly visible icons to load.
        self.onTextureListScrolled()


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
    def __init__(self, row: int, tpc: TPC, resname: str):
        self.row: int = row
        self.tpc: TPC = tpc
        self.resname: str = resname

    def __repr__(self):
        return str(self.row)

    def __call__(self, *args, **kwargs) -> tuple[int, str, int, int, bytearray]:
        width, height, data = self.tpc.convert(TPCTextureFormat.RGB, self.bestMipmap(self.tpc))
        return self.row, self.resname, width, height, data

    def bestMipmap(self, tpc: TPC) -> int:
        for i in range(tpc.mipmap_count()):
            size = tpc.get(i).width
            if size <= 64:
                return i
        return 0
