#!/usr/bin/env python3
from __future__ import annotations

from abc import abstractmethod
from ctypes import c_bool
from queue import Empty, Queue
from time import sleep
import time
from typing import TYPE_CHECKING, Any, Callable, ClassVar, cast

import qtpy

from loggerplus import RobustLogger
from qtpy import QtCore
from qtpy.QtCore import QMutex, QMutexLocker, QPoint, QRunnable, QSortFilterProxyModel, QThread, QThreadPool, QTimer, QWaitCondition, Qt
from qtpy.QtGui import (
    QCursor,
    QIcon,
    QImage,
    QPixmap,
    QStandardItem,
    QStandardItemModel,
    QTransform,
)
from qtpy.QtWidgets import QHeaderView, QMenu, QToolTip, QWidget

from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.tpc import TPC, TPCTextureFormat
from toolset.gui.dialogs.load_from_location_result import ResourceItems

if TYPE_CHECKING:
    from qtpy.QtCore import QEvent, QModelIndex, QObject
    from qtpy.QtGui import QMouseEvent, QResizeEvent

    from pykotor.extract.file import FileResource
    from pykotor.resource.type import ResourceType
    from toolset.data.installation import HTInstallation
    from utility.common.more_collections import CaseInsensitiveDict


class MainWindowList(QWidget):
    requestOpenResource = QtCore.Signal(object, object)  # pyright: ignore[reportPrivateImportUsage]
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
            if section in self.ui.sectionCombo.itemText(i):
                RobustLogger().debug("changing to section '%s'", section)
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
        resourceItemMap: dict[FileResource, ResourceStandardItem] = {
            item.resource: item
            for item in allResources
            if isinstance(item, ResourceStandardItem)
        }
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
                QTimer.singleShot(1, lambda index=itemIndex, item=item: select(item.parent().index(), index))

    def selected_resources(self) -> list[FileResource]:
        return self.modulesModel.resource_from_indexes(self.ui.resourceTree.selectedIndexes())  # type: ignore[arg-type]

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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.filter_string: str = ""

    def setFilterString(self, filter_string: str):
        self.filter_string = filter_string.lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        model: QStandardItemModel = self.sourceModel()  # pyright: ignore[reportAssignmentType]

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
        resources = (
            category.child(i, 0)
            for category in self._categoryItems.values()
            for i in range(category.rowCount())
        )
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
        self._scannedTextures: set[str] = set()

        self.texturesModel: QStandardItemModel = QStandardItemModel()
        self.texturesProxyModel: QSortFilterProxyModel = QSortFilterProxyModel()
        self.texturesProxyModel.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.texturesProxyModel.setSourceModel(self.texturesModel)
        self.ui.resourceList.setModel(self.texturesProxyModel)  # type: ignore[arg-type]

        self.sectionModel: QStandardItemModel = QStandardItemModel()
        self.ui.sectionCombo.setModel(self.sectionModel)  # type: ignore[arg-type]

        self._mutex: QMutex = QMutex()

    def setupSignals(self):
        self.ui.searchEdit.textEdited.connect(self.onFilterStringUpdated)
        self.ui.sectionCombo.currentIndexChanged.connect(self.onSectionChanged)
        self.ui.resourceList.doubleClicked.connect(self.onResourceDoubleClicked)
        self.iconUpdate.connect(self.onIconUpdate)

        vertScrollBar = self.ui.resourceList.verticalScrollBar()
        assert vertScrollBar is not None
        vertScrollBar.valueChanged.connect(self.onTextureListScrolled)
        self.ui.searchEdit.textChanged.connect(self.onTextureListScrolled)

    def doTerminations(self):
        """Do some things to terminate all the texture tasks."""

    def setInstallation(self, installation: HTInstallation):
        self._installation = installation

    def setResources(
        self,
        resources: list[FileResource],
    ):
        blankImage = QImage(bytes(0 for _ in range(64 * 64 * 3)), 64, 64, QImage.Format.Format_RGB888)
        blankIcon = QIcon(QPixmap.fromImage(blankImage))

        self.texturesModel.clear()
        for resource in resources:
            item = QStandardItem(blankIcon, resource.resname())
            item.setToolTip(resource.resname())
            item.setData(False, Qt.ItemDataRole.UserRole)
            item.setData(resource, Qt.ItemDataRole.UserRole + 1)
            self.texturesModel.appendRow(item)

        if self._installation is not None:
            self.onTextureListScrolled()

    def setSections(
        self,
        sections: list[QStandardItem],
    ):
        self.sectionModel.clear()
        for section in sections:
            self.sectionModel.insertRow(self.sectionModel.rowCount(), section)

    def selectedResources(self) -> list[FileResource]:
        resources: list[FileResource] = []
        for proxyIndex in self.ui.resourceList.selectedIndexes():
            sourceIndex = self.texturesProxyModel.mapToSource(proxyIndex)  # pyright: ignore[reportArgumentType]
            item = self.texturesModel.item(sourceIndex.row())
            resources.append(item.data(Qt.ItemDataRole.UserRole + 1))
        return resources

    def visibleItems(self) -> list[QStandardItem]:
        if self.texturesModel.rowCount() == 0:
            return []

        parent: QObject = self.parent()
        assert isinstance(parent, QWidget)
        scanWidth: int = parent.width()
        scanHeight: int = parent.height()

        proxyModel = self.texturesProxyModel
        model = self.texturesModel

        firstItem: QStandardItem | None = None
        firstIndex: QModelIndex | None = None

        for y in range(2, 92, 2):
            for x in range(2, 92, 2):
                proxyIndex = self.ui.resourceList.indexAt(QPoint(x, y))  # type: ignore[arg-type]
                index = proxyModel.mapToSource(proxyIndex)
                item = model.itemFromIndex(index)
                if not firstItem and item:
                    firstItem = item
                    firstIndex = proxyIndex
                    break

        items: list[QStandardItem] = []

        if firstItem is not None and firstIndex is not None:
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

    def onFilterStringUpdated(self):
        self.texturesProxyModel.setFilterFixedString(self.ui.searchEdit.text())

    def onSectionChanged(self):
        self.sectionChanged.emit(self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole))

    def onReloadClicked(self):
        self.requestReload.emit(self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole))

    def onRefreshClicked(self):
        self.requestRefresh.emit()

    def onTextureListScrolled(self):
        # Avoid redundantly loading textures that have already been loaded
        visible_items = self.visibleItems()
        textures_to_load = {item.text() for item in visible_items if item.text().lower() not in self._scannedTextures}
        texname_to_item = {item.text().lower(): item for item in visible_items}

        # Emit signals to load textures that have not had their icons assigned
        for texture_name_lower in iter(textures_to_load):
            if texture_name_lower in self._scannedTextures:
                continue
            if texture_name_lower not in texname_to_item:  # should never happen.
                continue
            def get_texture_func(resname: str) -> TPC | None:
                return self._installation.texture(resname, [SearchLocation.TEXTURES_GUI, SearchLocation.TEXTURES_TPA])
            item = texname_to_item[texture_name_lower]
            self._scannedTextures.add(texture_name_lower)
            task = LoadTextureTask(get_texture_func, item.row(), item.column(), texture_name_lower, self.onIconUpdate, self._mutex)
            QThreadPool.globalInstance().start(task)

    def onIconUpdate(
        self,
        row: int,
        col: int,
        icon: QIcon,
    ):
        item = self.texturesModel.item(row, col)
        item.setIcon(icon)

    def onResourceDoubleClicked(self):
        self.requestOpenResource.emit(self.selectedResources(), None)

    def resizeEvent(self, a0: QResizeEvent):  # pylint: disable=W0613
        self.onTextureListScrolled()


class LoadTextureTask(QRunnable):
    def __init__(
        self,
        get_texture_func: Callable[[str], TPC | None],
        row: int,
        col: int,
        resname: str,
        callback: Callable[[int, int, QIcon], None],
        mutex: QMutex,
    ):
        super().__init__()
        self.get_texture_func: Callable[[str], TPC | None] = get_texture_func
        self.row: int = row
        self.col: int = col
        self.resname: str = resname
        self.callback: Callable[[int, int, QIcon], None] = callback
        self._mutex: QMutex = mutex

    def run(self):
        tpc = self.get_texture_func(self.resname)
        if tpc is None:
            return
        width, height, data = tpc.convert(TPCTextureFormat.RGB, self.bestMipmap(tpc))
        image = QImage(data, width, height, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(image).transformed(QTransform().scale(1, -1))
        icon = QIcon(pixmap)
        with QMutexLocker(self._mutex):
            self.callback(self.row, self.col, icon)

    def bestMipmap(self, tpc: TPC) -> int:
        return next((i for i in range(tpc.mipmap_count()) if tpc.get(i).width <= 64), 0)
