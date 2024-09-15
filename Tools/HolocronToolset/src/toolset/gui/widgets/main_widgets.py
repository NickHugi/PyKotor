#!/usr/bin/env python3
from __future__ import annotations

import multiprocessing
import queue

from abc import abstractmethod
from io import BytesIO
from typing import TYPE_CHECKING, Any, ClassVar, cast

import qtpy

from loggerplus import RobustLogger
from qtpy import QtCore
from qtpy.QtCore import QFileInfo, QSortFilterProxyModel, QThread, QTimer, Qt
from qtpy.QtGui import QCursor, QIcon, QImage, QPixmap, QStandardItem, QStandardItemModel, QTransform
from qtpy.QtWidgets import QFileIconProvider, QHeaderView, QMenu, QToolTip, QWidget

from pykotor.resource.formats.tpc.tpc_auto import read_tpc
from pykotor.resource.formats.tpc.tpc_data import TPCGetResult, TPCTextureFormat
from pykotor.resource.type import ResourceType
from toolset.gui.dialogs.load_from_location_result import ResourceItems
from toolset.gui.widgets.settings.installations import GlobalSettings
from utility.system.app_process.task_consumer import TaskConsumer

if TYPE_CHECKING:
    from qtpy.QtCore import QEvent, QModelIndex, QObject, QPoint
    from qtpy.QtGui import QMouseEvent, QResizeEvent, QShowEvent

    from pykotor.extract.file import FileResource
    from toolset.data.installation import HTInstallation


class MainWindowList(QWidget):
    requestOpenResource = QtCore.Signal(list, bool)  # pyright: ignore[reportPrivateImportUsage]
    requestExtractResource = QtCore.Signal(object)  # pyright: ignore[reportPrivateImportUsage]
    sectionChanged = QtCore.Signal(object)  # pyright: ignore[reportPrivateImportUsage]

    @abstractmethod
    def selected_resources(self) -> list[FileResource]: ...


class ResourceStandardItem(QStandardItem):
    def __init__(self, *args: Any, resource: FileResource, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.resource: FileResource = resource


class ResourceList(MainWindowList):
    requestReload: QtCore.Signal = QtCore.Signal(object)  # pyright: ignore[reportPrivateImportUsage]
    requestRefresh: QtCore.Signal = QtCore.Signal()  # pyright: ignore[reportPrivateImportUsage]

    HORIZONTAL_HEADER_LABELS: ClassVar[list[str]] = ["ResRef", "Type"]

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
        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.widgets.resource_list import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.widgets.resource_list import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.widgets.resource_list import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.widgets.resource_list import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.tooltipText: str = ""
        self.flattened: bool = False
        self.autoResizeEnabled: bool = True
        self.expandedState: bool = False
        self.original_items: list[tuple[QStandardItem, list[list[QStandardItem]]]] = []

        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setupSignals()

        self.modulesModel: ResourceModel = ResourceModel()
        self.modulesModel.proxyModel().setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.ui.resourceTree.setModel(self.modulesModel.proxyModel())  # pyright: ignore[reportArgumentType]
        self.ui.resourceTree.sortByColumn(0, Qt.SortOrder.AscendingOrder)  # pyright: ignore[reportArgumentType]
        self.sectionModel = QStandardItemModel()
        self.ui.sectionCombo.setModel(self.sectionModel)  # pyright: ignore[reportArgumentType]

        # Connect the header context menu request signal
        tree_view_header: QHeaderView | None = self.ui.resourceTree.header()  # pyright: ignore[reportAssignmentType]
        assert tree_view_header is not None
        tree_view_header.setSectionsClickable(True)
        tree_view_header.setSortIndicatorShown(True)
        tree_view_header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)  # pyright: ignore[reportArgumentType]
        tree_view_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)  # pyright: ignore[reportArgumentType]

        self.tooltipTimer = QTimer(self)
        self.tooltipTimer.setSingleShot(True)
        self.tooltipTimer.timeout.connect(self.show_tooltip)

    def _clear_modules_model(self):
        self.modulesModel.clear()
        self.modulesModel.setColumnCount(2)
        self.modulesModel.setHorizontalHeaderLabels(["ResRef", "Type"])

    def show_tooltip(self):
        QToolTip.showText(QCursor.pos(), self.tooltipText, self.ui.resourceTree)  # pyright: ignore[reportArgumentType]

    def setupSignals(self):
        self.ui.searchEdit.textEdited.connect(self.on_filter_string_updated)
        self.ui.sectionCombo.currentIndexChanged.connect(self.on_section_changed)
        self.ui.reloadButton.clicked.connect(self.on_reload_clicked)
        self.ui.refreshButton.clicked.connect(self.on_refresh_clicked)
        self.ui.resourceTree.customContextMenuRequested.connect(self.on_resource_context_menu)
        self.ui.resourceTree.doubleClicked.connect(self.on_resource_double_clicked)

    def enterEvent(self, event: QEvent):
        self.tooltipTimer.stop()
        QToolTip.hideText()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent):
        self.tooltipTimer.stop()
        QToolTip.hideText()
        super().leaveEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        index = self.ui.resourceTree.indexAt(event.pos())  # type: ignore[arg-type]
        if index.isValid():
            model_index: QModelIndex = cast(QSortFilterProxyModel, self.ui.resourceTree.model()).mapToSource(index)  # pyright: ignore[reportArgumentType]
            item: ResourceStandardItem | QStandardItem | None = cast(
                QStandardItemModel,
                cast(QSortFilterProxyModel, self.ui.resourceTree.model()).sourceModel(),
            ).itemFromIndex(model_index)
            if isinstance(item, ResourceStandardItem):
                self.tooltipText = str(item.resource.filepath())
                self.tooltipPos = event.globalPos()
                self.tooltipTimer.start(1100)  # Set the delay to 3000ms (3 seconds)
            else:
                self.tooltipTimer.stop()
                QToolTip.hideText()
        else:
            self.tooltipTimer.stop()
            QToolTip.hideText()
        super().mouseMoveEvent(event)

    def hide_reload_button(self):
        self.ui.reloadButton.setVisible(False)

    def hide_section(self):
        self.ui.line.setVisible(False)
        self.ui.sectionCombo.setVisible(False)
        self.ui.refreshButton.setVisible(False)

    def current_section(self) -> str:
        return self.ui.sectionCombo.currentData()

    def change_section(
        self,
        section: str,
    ):
        for i in range(self.ui.sectionCombo.count()):
            if section not in self.ui.sectionCombo.itemText(i):
                continue
            self.ui.sectionCombo.setCurrentIndex(i)

    def set_resources(
        self,
        resources: list[FileResource],
        customCategory: str | None = None,
        *,
        clearExisting: bool = True,
    ):
        """Adds and removes FileResources from the modules model.

        Args:
        ----
            resources: {list[FileResource]}: List of FileResource objects to set
        """
        allResources: list[QStandardItem] = self.modulesModel.all_resources_items()
        resourceSet: set[FileResource] = set(resources)
        resourceItemMap: dict[FileResource, ResourceStandardItem] = {item.resource: item for item in allResources if isinstance(item, ResourceStandardItem)}
        for resource in resourceSet:
            if resource in resourceItemMap:
                resourceItemMap[resource].resource = resource
            else:
                self.modulesModel.addResource(resource, customCategory)
        if clearExisting:
            for item in allResources:
                if not isinstance(item, ResourceStandardItem):
                    continue
                if item.resource in resourceSet:
                    continue
                item.parent().removeRow(item.row())
        self.modulesModel.removeUnusedCategories()

    def set_sections(
        self,
        sections: list[QStandardItem],
    ):
        self.sectionModel.clear()
        for section in sections:
            self.sectionModel.insertRow(self.sectionModel.rowCount(), section)

    def set_resource_selection(
        self,
        resource: FileResource,
    ):
        model: ResourceModel = cast(QSortFilterProxyModel, self.ui.resourceTree.model()).sourceModel()  # type: ignore[attribute-access]
        assert isinstance(model, ResourceModel)

        def select(parent, child):
            self.ui.resourceTree.expand(parent)
            self.ui.resourceTree.scrollTo(child)
            self.ui.resourceTree.setCurrentIndex(child)

        for item in model.all_resources_items():
            if not isinstance(item, ResourceStandardItem):
                continue
            resource_from_item: FileResource = item.resource
            if resource_from_item == resource:
                itemIndex: QModelIndex = model.proxyModel().mapFromSource(item.index())
                QTimer.singleShot(0, lambda index=itemIndex, item=item: select(item.parent().index(), index))

    def selected_resources(self) -> list[FileResource]:
        return self.modulesModel.resource_from_indexes(self.ui.resourceTree.selectedIndexes())  # pyright: ignore[reportArgumentType]

    def _get_section_user_role_data(self):
        return self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)

    def on_filter_string_updated(self):
        self.modulesModel.proxyModel().setFilterString(self.ui.searchEdit.text())

    def on_section_changed(self):
        self.sectionChanged.emit(self._get_section_user_role_data())

    def on_reload_clicked(self):
        self.requestReload.emit(self._get_section_user_role_data())

    def on_refresh_clicked(self):
        self._clear_modules_model()
        self.requestRefresh.emit()

    def on_resource_context_menu(self, point: QPoint):
        resources: list[FileResource] = self.selected_resources()
        if not resources:
            return
        menu = QMenu(self)
        menu.addAction("Open").triggered.connect(lambda: self.requestOpenResource.emit(resources, True))
        if all(resource.restype().contents == "gff" for resource in resources):
            menu.addAction("Open with GFF Editor").triggered.connect(lambda: self.requestOpenResource.emit(resources, False))
        menu.addSeparator()
        builder = ResourceItems(resources=resources)
        builder.viewport = lambda: self.ui.resourceTree
        builder.runContextMenu(point, menu=menu)

    def on_resource_double_clicked(self):
        self.requestOpenResource.emit(self.selected_resources(), None)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.ui.resourceTree.setColumnWidth(1, 10)
        self.ui.resourceTree.setColumnWidth(0, self.ui.resourceTree.width() - 80)
        header: QHeaderView | None = self.ui.resourceTree.header()  # pyright: ignore[reportAssignmentType]
        assert header is not None
        header.setSectionResizeMode(QHeaderView.Interactive)  # type: ignore[arg-type]


class ResourceProxyModel(QSortFilterProxyModel):
    """A proxy model for the resource model."""

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.filter_string: str = ""

    def setFilterString(self, filter_string: str):
        self.filter_string = filter_string.lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        model = self.sourceModel()  # pyright: ignore[reportAssignmentType]
        assert isinstance(model, QStandardItemModel)
        resref_index = model.index(source_row, 0, source_parent)
        item: ResourceStandardItem | QStandardItem | None = model.itemFromIndex(resref_index)
        if isinstance(item, ResourceStandardItem):
            # Get the file name and resource name
            filename = item.resource.filepath().name.lower()
            resname = item.resource.filename().lower()

            # Check if the filter string is a substring of either the filename or the resource name
            if self.filter_string in filename or self.filter_string in resname:
                return True

        return False


class ResourceModel(QStandardItemModel):
    """A data model used by the different trees (Core, Modules, Override).

    This class provides an easy way to add resources while sorting them into categories.
    """

    def __init__(self):
        super().__init__()
        self._categoryItems: dict[str, QStandardItem] = {}
        self._proxyModel: ResourceProxyModel = ResourceProxyModel(self)
        self._proxyModel.setSourceModel(self)
        self._proxyModel.setRecursiveFilteringEnabled(True)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["ResRef", "Type"])

    def proxyModel(self) -> ResourceProxyModel:
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

    def addResource(
        self,
        resource: FileResource,
        customCategory: str | None = None,
    ):
        self._addResourceIntoCategory(resource.restype(), customCategory).appendRow(
            [
                ResourceStandardItem(resource.resname(), resource=resource),
                QStandardItem(resource.restype().extension.upper()),
            ]
        )

    def resource_from_indexes(
        self,
        indexes: list[QModelIndex],
        *,
        proxy: bool = True,
    ) -> list[FileResource]:
        items = []
        for index in indexes:
            sourceIndex = self._proxyModel.mapToSource(index) if proxy else index
            items.append(self.itemFromIndex(sourceIndex))
        return self.resourceFromItems(items)

    def resourceFromItems(
        self,
        items: list[QStandardItem],
    ) -> list[FileResource]:
        return [item.resource for item in items if isinstance(item, ResourceStandardItem)]  # pyright: ignore[reportAttributeAccessIssue]

    def all_resources_items(self) -> list[QStandardItem]:
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
    requestReload = QtCore.Signal(object)  # pyright: ignore[reportPrivateImportUsage]
    requestRefresh = QtCore.Signal()  # pyright: ignore[reportPrivateImportUsage]
    iconUpdate = QtCore.Signal(object, object)  # pyright: ignore[reportPrivateImportUsage]

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self._loaded_icons: dict[FileResource, QIcon] = {}

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.widgets.texture_list import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.widgets.texture_list import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.widgets.texture_list import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.widgets.texture_list import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setupSignals()

        self._installation: HTInstallation | None = None

        self.texturesModel: QStandardItemModel = QStandardItemModel()
        self.texturesProxyModel: QSortFilterProxyModel = QSortFilterProxyModel()
        self.texturesProxyModel.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.texturesProxyModel.setSourceModel(self.texturesModel)
        self.ui.resourceList.setModel(self.texturesProxyModel)  # type: ignore[arg-type]

        self.sectionModel: QStandardItemModel = QStandardItemModel()
        self.ui.sectionCombo.setModel(self.sectionModel)  # type: ignore[arg-type]

        print("Setting up multiprocessing queue and icon processor")
        self.task_queue: multiprocessing.JoinableQueue = multiprocessing.JoinableQueue()
        self.result_queue: multiprocessing.Queue[tuple[int, TPCGetResult]] = multiprocessing.Queue()
        self.stop_event = multiprocessing.Event()

        self._consumers: list[TaskConsumer] = [
            TaskConsumer(
                task_queue=self.task_queue,
                result_queue=self.result_queue,
                stop_event=self.stop_event,
                name=f"TextureLoadTask-{i}",
            )
            for i in range(GlobalSettings().max_child_processes)
        ]
        for consumer in self._consumers:
            consumer.start()

        print("Setting up context menu")
        self.ui.resourceList.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)  # pyright: ignore[reportArgumentType]
        self.ui.resourceList.customContextMenuRequested.connect(self.showContextMenu)
        self._loading_resources: set[FileResource] = set()

        self._scanner: QThread = QThread(self)
        self._scanner.setObjectName("TextureListScanner")
        self._scanner.run = self.scan
        self._scanner.start(QThread.Priority.LowestPriority)

    def scan(self):
        print("Starting TextureList run loop")
        while not self.stop_event.is_set():
            try:
                result: tuple[int, TPCGetResult | None] | None = self.result_queue.get(True, None)
                if result is None:
                    continue
                row, entry = result
                if entry is None:
                    continue
                width, height, image_format, img_bytes = entry
                image = QImage(img_bytes, width, height, QImage.Format.Format_RGBA8888)
                pixmap = QPixmap.fromImage(image).transformed(QTransform().scale(1, -1))
                icon = QIcon(pixmap)
                self.iconUpdate.emit(row, icon)
            except queue.Empty:
                ...

    def __del__(self):
        print("TextureList destructor called")
        self.doTerminations()

    def setupSignals(self):
        print("Setting up signals for TextureList")
        self.ui.searchEdit.textEdited.connect(self.onFilterStringUpdated)
        self.ui.sectionCombo.currentIndexChanged.connect(self.onSectionChanged)
        self.ui.resourceList.doubleClicked.connect(self.onResourceDoubleClicked)
        self.iconUpdate.connect(self.onIconUpdate)

        vertScrollBar = self.ui.resourceList.verticalScrollBar()
        assert vertScrollBar is not None
        vertScrollBar.valueChanged.connect(self.queueLoadViewableIcons)
        self.ui.searchEdit.textChanged.connect(self.queueLoadViewableIcons)

    def showContextMenu(self, position: QPoint):
        print(f"Showing context menu at position: {position}")
        menu = QMenu(self)
        reloadAction = menu.addAction("Reload")
        reloadAction.triggered.connect(self.onReloadClicked)
        action = menu.exec_(self.ui.resourceList.mapToGlobal(position))  # pyright: ignore[reportArgumentType, reportCallIssue]
        if action != reloadAction:
            print("No action selected from context menu")
            return
        index = self.ui.resourceList.indexAt(position)  # pyright: ignore[reportArgumentType]
        if not index.isValid():
            print("Invalid index for context menu")
            return
        sourceIndex = self.texturesProxyModel.mapToSource(index)  # pyright: ignore[reportArgumentType]
        if not sourceIndex.isValid():
            print("Invalid source index for context menu")
            return
        print(f"Reloading texture at row: {sourceIndex.row()}")
        self.offload_texture_load(sourceIndex.row(), reload=True)

    def resizeEvent(self, a0: QResizeEvent):  # pylint: disable=W0613
        QTimer.singleShot(0, self.queueLoadViewableIcons)

    def showEvent(self, a0: QShowEvent):  # pylint: disable=W0613
        QTimer.singleShot(0, self.queueLoadViewableIcons)

    def mouseMoveEvent(self, event: QMouseEvent):  # pylint: disable=W0613
        super().mouseMoveEvent(event)
        globalPos = self.mapToGlobal(event.pos())
        index2line = self.ui.resourceList.indexAt(self.ui.resourceList.mapFromGlobal(globalPos))  # pyright: ignore[reportCallIssue, reportArgumentType]
        if not index2line.isValid():
            return
        sourceIndex = self.texturesProxyModel.mapToSource(index2line)  # pyright: ignore[reportArgumentType]
        if not sourceIndex.isValid():
            return
        print(f"Mouse moved over row: {sourceIndex.row()}")
        self.offload_texture_load(sourceIndex.row(), reload=False)

    def doTerminations(self):
        print("Terminating TextureList processes and threads")
        self.running = False
        self.result_queue.put(None)

    def setResources(
        self,
        resources: list[FileResource],
    ):
        print(f"Setting resources, count: {len(resources)}")
        blankImage = QImage(bytes(0 for _ in range(64 * 64 * 3)), 64, 64, QImage.Format.Format_RGB888)
        blankIcon = QIcon(QPixmap.fromImage(blankImage))

        self.texturesModel.clear()
        for resource in resources:
            item = QStandardItem(blankIcon, resource.resname())
            item.setToolTip(resource.resname())
            item.setData(False, Qt.ItemDataRole.UserRole)
            item.setData(resource, Qt.ItemDataRole.UserRole + 1)
            self.texturesModel.appendRow(item)
        print(f"Added {self.texturesModel.rowCount()} items to the model")

        self.queueLoadViewableIcons()

    def setSections(
        self,
        sections: list[QStandardItem],
    ):
        print(f"Setting sections, count: {len(sections)}")
        self.sectionModel.clear()
        for section in sections:
            self.sectionModel.insertRow(self.sectionModel.rowCount(), section)

    def selected_resources(self) -> list[FileResource]:
        print("Getting selected resources")
        resources: list[FileResource] = []
        for proxyIndex in self.ui.resourceList.selectedIndexes():
            sourceIndex = self.texturesProxyModel.mapToSource(proxyIndex)  # pyright: ignore[reportArgumentType]
            item = self.texturesModel.item(sourceIndex.row())
            resources.append(item.data(Qt.ItemDataRole.UserRole + 1))
        print(f"Selected resources count: {len(resources)}")
        return resources

    def visible_rows(self) -> list[int]:
        if not self.isVisible() or self.texturesModel.rowCount() == 0:
            print("Widget not visible or no rows in model")
            return []

        resourceList = self.ui.resourceList
        visibleRect = resourceList.viewport().rect()  # pyright: ignore[reportOptionalMemberAccess]

        # Try to find the first visible index
        firstVisibleIndex = None
        for row in range(self.texturesProxyModel.rowCount()):
            index = self.texturesProxyModel.index(row, 0)
            if not resourceList.visualRect(index).intersects(visibleRect):  # pyright: ignore[reportArgumentType]
                continue
            print(f"Found first visible index: {index} at row {row} because of visualRect intersection")
            firstVisibleIndex = index
            break

        # If still no valid index found, return an empty list
        if not firstVisibleIndex or not firstVisibleIndex.isValid():
            print("No valid visible index found, using first index")
            firstVisibleIndex = self.texturesProxyModel.index(0, 0)

        visible_items: list[int] = []
        current_index = firstVisibleIndex
        lastVisibleIndex: QModelIndex | None = None
        while current_index.isValid():
            sourceIndex = self.texturesProxyModel.mapToSource(current_index)
            visible_items.append(sourceIndex.row())
            lastVisibleIndex = current_index
            current_index = self.texturesProxyModel.index(current_index.row() + 1, current_index.column())
            if not current_index.isValid() or not resourceList.visualRect(current_index).intersects(visibleRect):  # pyright: ignore[reportArgumentType]
                break

        topLeftRow = self.texturesProxyModel.mapToSource(firstVisibleIndex).row()
        bottomRightRow = self.texturesProxyModel.mapToSource(lastVisibleIndex).row() if lastVisibleIndex else topLeftRow

        print(f"Visible rows: top left = {topLeftRow}, bottom right = {bottomRightRow}")
        return visible_items

    def onFilterStringUpdated(self):
        filterString = self.ui.searchEdit.text()
        print(f"Filter string updated: '{filterString}'")
        self.texturesProxyModel.setFilterFixedString(filterString)

    def onSectionChanged(self):
        selectedSection = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        print(f"Section changed to: {selectedSection}")
        self.sectionChanged.emit(selectedSection)

    def onReloadClicked(self):
        selectedSection = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        print(f"Reload requested for section: {selectedSection}")
        self.requestReload.emit(selectedSection)

    def onRefreshClicked(self):
        print("Refresh requested")
        self.requestRefresh.emit()

    def queueLoadViewableIcons(self):
        print("Texture list scrolled")
        visible_items = self.visible_rows()
        if not visible_items:
            return
        for row in visible_items:
            self.offload_texture_load(row, reload=False)

    def offload_texture_load(
        self,
        row: int,
        mipmap: int = 64,
        *,
        reload: bool = False,
    ):
        item = self.texturesModel.item(row)
        resource: FileResource | None = item.data(Qt.ItemDataRole.UserRole + 1)
        assert resource is not None, f"texture item at row {row} has no resource"
        if resource in self._loading_resources:
            return
        self._loading_resources.add(resource)
        self.task_queue.put(TextureLoadTask(row=row, resource=resource, mipmap=mipmap))

    def onIconUpdate(self, row: int, icon: QIcon):
        print(f"Updating icon for row {row}")
        item = self.texturesModel.item(row)
        assert item is not None, f"texture item at row {row} is None"
        resource: FileResource = item.data(Qt.ItemDataRole.UserRole + 1)
        item.setIcon(icon)
        self._loaded_icons[resource] = icon
        self._loading_resources.discard(resource)
        self.ui.resourceList.update(item.index())  # pyright: ignore[reportArgumentType]

    def onResourceDoubleClicked(self):
        print("Resource double-clicked")
        selected = self.selected_resources()
        print(f"Opening {len(selected)} selected resources")
        self.requestOpenResource.emit(selected, None)


def get_image_from_resource(row: int, resource: FileResource, mipmap: int = 64) -> tuple[int, TPCGetResult]:
    if resource.restype() is ResourceType.TPC:
        tpc = read_tpc(resource.data())
        best_mipmap = next((i for i in range(tpc.mipmap_count()) if tpc.get(i).width <= mipmap), 0)
        width, height, data = tpc.convert(TPCTextureFormat.RGBA, best_mipmap)
        return row, TPCGetResult(width, height, TPCTextureFormat.RGBA, data)

    try:
        from PIL import Image

        if resource.restype().extension.lower() in Image.registered_extensions():
            with Image.open(BytesIO(resource.data())) as img:
                pil_img = img.convert("RGBA")
            return row, TPCGetResult(pil_img.width, pil_img.height, TPCTextureFormat.RGBA, pil_img.tobytes())
    except ImportError:  # noqa: S110
        RobustLogger().warning(f"Pillow not available for resource type: {resource.restype()!r}")

    try:
        from qtpy.QtCore import Qt
        from qtpy.QtGui import QImage, QImageReader

        if resource.restype().extension.lower() in [bytes(x.data()).decode().lower() for x in QImageReader.supportedImageFormats()]:
            qimg = QImage()
            if qimg.loadFromData(resource.data()):
                qimg = qimg.convertToFormat(QImage.Format.Format_RGBA8888)
                if mipmap < qimg.width() or mipmap < qimg.height():
                    qimg = qimg.scaled(mipmap, mipmap, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                return row, TPCGetResult(qimg.width(), qimg.height(), TPCTextureFormat.RGBA, bytes(qimg.constBits().asarray()))
        else:  # use QFileIconProvider
            iconProvider = QFileIconProvider()
            pixmap = iconProvider.icon(QFileInfo(str(resource.filepath()))).pixmap(mipmap, mipmap)
            qimg = pixmap.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
            return row, TPCGetResult(qimg.width(), qimg.height(), TPCTextureFormat.RGBA, bytes(qimg.constBits().asarray()))
    except ImportError:  # noqa: S110
        RobustLogger().warning(f"Qt not available for resource type: {resource.restype()!r}")

    raise ValueError(f"No suitable image processing library available for resource type: {resource!r}")


class TextureLoadTask:
    def __init__(self, row: int, resource: FileResource, mipmap: int):
        self.row: int = row
        self.resource: FileResource = resource
        self.mipmap: int = mipmap

    def __call__(self) -> tuple[int, TPCGetResult]:
        return get_image_from_resource(self.row, self.resource, self.mipmap)
