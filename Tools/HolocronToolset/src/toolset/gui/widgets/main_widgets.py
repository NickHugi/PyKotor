#!/usr/bin/env python3
from __future__ import annotations

from abc import abstractmethod
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from io import BytesIO
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar, cast

import qtpy

from loggerplus import RobustLogger
from qtpy import QtCore
from qtpy.QtCore import QFileInfo, QSortFilterProxyModel, QTimer, Qt
from qtpy.QtGui import QCursor, QImage, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QFileIconProvider, QHeaderView, QMenu, QToolTip, QWidget

from pykotor.resource.formats.tpc.tpc_auto import read_tpc
from pykotor.resource.formats.tpc.tpc_data import TPCGetResult, TPCTextureFormat
from pykotor.resource.type import ResourceType
from toolset.gui.dialogs.load_from_location_result import ResourceItems
from toolset.gui.widgets.settings.installations import GlobalSettings

if TYPE_CHECKING:
    from concurrent.futures import Future

    from qtpy.QtCore import QEvent, QModelIndex, QObject, QPoint
    from qtpy.QtGui import QMouseEvent, QResizeEvent, QShowEvent
    from qtpy.QtWidgets import QAbstractItemView, QScrollBar

    from pykotor.extract.file import FileResource
    from toolset.data.installation import HTInstallation


class MainWindowList(QWidget):
    requestOpenResource: QtCore.Signal = QtCore.Signal(list, object)  # pyright: ignore[reportPrivateImportUsage]
    requestExtractResource: QtCore.Signal = QtCore.Signal(object)  # pyright: ignore[reportPrivateImportUsage]
    sectionChanged: QtCore.Signal = QtCore.Signal(object)  # pyright: ignore[reportPrivateImportUsage]

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
    requestReload: QtCore.Signal = QtCore.Signal(object)  # pyright: ignore[reportPrivateImportUsage]
    requestRefresh: QtCore.Signal = QtCore.Signal()  # pyright: ignore[reportPrivateImportUsage]
    iconLoaded: QtCore.Signal = QtCore.Signal(object)  # pyright: ignore[reportPrivateImportUsage]

    BLANK_IMAGE: QImage = QImage(bytes(0 for _ in range(64 * 64 * 3)), 64, 64, QImage.Format.Format_RGB888)

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

        self.texture_models: dict[str, QStandardItemModel] = {}
        self.texturesModel: QStandardItemModel = QStandardItemModel()
        self.texturesProxyModel: QSortFilterProxyModel = QSortFilterProxyModel()
        self.texturesProxyModel.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.texturesProxyModel.setSourceModel(self.texturesModel)
        self.ui.resourceList.setModel(self.texturesProxyModel)  # type: ignore[arg-type]

        self.sectionModel: QStandardItemModel = QStandardItemModel()
        self.ui.sectionCombo.setModel(self.sectionModel)  # type: ignore[arg-type]

        self._executor: ProcessPoolExecutor = ProcessPoolExecutor(max_workers=GlobalSettings().max_child_processes)

        self.ui.resourceList.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)  # pyright: ignore[reportArgumentType]
        self.ui.resourceList.customContextMenuRequested.connect(self.showContextMenu)
        self._loading_resources: set[FileResource] = set()

    def __del__(self):
        self._executor.shutdown(wait=False)

    def setupSignals(self):
        self.ui.searchEdit.textEdited.connect(self.onFilterStringUpdated)
        self.ui.sectionCombo.currentIndexChanged.connect(self.onSectionChanged)
        section_combo_model = self.ui.sectionCombo.model()
        assert isinstance(section_combo_model, QStandardItemModel), "Section combo model is not a QStandardItemModel"
        section_combo_model.rowsInserted.connect(self.onSectionAdded)
        section_combo_model.rowsRemoved.connect(self.onSectionRemoved)
        self.ui.resourceList.doubleClicked.connect(self.onResourceDoubleClicked)

        vertScrollBar: QScrollBar | None = self.ui.resourceList.verticalScrollBar()  # pyright: ignore[reportAssignmentType]
        assert vertScrollBar is not None
        vertScrollBar.valueChanged.connect(self.queueLoadViewableIcons)
        self.ui.searchEdit.textChanged.connect(self.queueLoadViewableIcons)
        self.iconLoaded.connect(self.onIconLoaded)

    def showContextMenu(self, position: QPoint):
        menu = QMenu(self)
        reloadAction = menu.addAction("Reload")
        reloadAction.triggered.connect(self.onReloadClicked)
        action = menu.exec_(self.ui.resourceList.mapToGlobal(position))  # pyright: ignore[reportArgumentType, reportCallIssue]
        if action != reloadAction:
            return
        index = self.ui.resourceList.indexAt(position)  # pyright: ignore[reportArgumentType]
        if not index.isValid():
            return
        sourceIndex = self.texturesProxyModel.mapToSource(index)  # pyright: ignore[reportArgumentType]
        if not sourceIndex.isValid():
            return
        item = self.texturesModel.itemFromIndex(sourceIndex)
        self.offload_texture_load(item, reload=True)

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
        item = self.texturesModel.itemFromIndex(sourceIndex)
        if item is None:
            return
        self.offload_texture_load(item, reload=False)

    def setResources(self, resources: list[FileResource]):
        section = self.ui.sectionCombo.currentData()
        model = self.texture_models[section]
        model.clear()

        for resource in resources:
            resname, restype = resource.resname(), resource.restype()
            if restype not in (ResourceType.TGA, ResourceType.TPC):
                continue
            item = ResourceStandardItem(resname, resource=resource)
            model.appendRow(item)

        self.ui.resourceList.setModel(model)  # pyright: ignore[reportArgumentType]

        self.queueLoadViewableIcons()

    def setSections(self, items: list[QStandardItem]):
        current_sections: set[str] = {self.ui.sectionCombo.itemData(i, Qt.ItemDataRole.UserRole) for i in range(self.ui.sectionCombo.count())}
        new_sections: set[str] = {item.data(Qt.ItemDataRole.UserRole) for item in items}

        # Remove sections that are no longer present
        for section in current_sections - new_sections:
            del self.texture_models[section]

        self.ui.sectionCombo.clear()

        for item in items:
            section = item.data(Qt.UserRole)
            self.ui.sectionCombo.addItem(item.text(), section)
            if section not in self.texture_models:
                self.texture_models[section] = QStandardItemModel()

        # Set the model for the current section
        if self.ui.sectionCombo.count() > 0:
            current_section = self.ui.sectionCombo.itemData(0, Qt.ItemDataRole.UserRole)
            self.texturesProxyModel.setSourceModel(self.texture_models[current_section])

    @staticmethod
    def selected_indexes(resource_list: QAbstractItemView) -> list[QModelIndex]:
        indexes: list[QModelIndex] = []
        current_model = resource_list.model()
        for index in resource_list.selectedIndexes():
            sourceIndex = (
                current_model.mapToSource(index)  # pyright: ignore[reportArgumentType]
                if isinstance(current_model, QSortFilterProxyModel)
                else index
            )
            if not sourceIndex.isValid():
                RobustLogger().warning("Invalid source index for row %d", index.row())
                continue
            indexes.append(sourceIndex)
        return indexes

    def selected_resources(self) -> list[FileResource]:
        section = self.ui.sectionCombo.currentText()
        resources = [
            self.texture_models[section].itemFromIndex(index).data(Qt.UserRole + 1)
            for index in self.selected_indexes(self.ui.resourceList)  # pyright: ignore[reportArgumentType]
            if self.texture_models[section].itemFromIndex(index) is not None
        ]
        return resources

    @staticmethod
    def visible_indexes(view: QAbstractItemView) -> list[QModelIndex]:
        if not view.isVisible() or view.model().rowCount() == 0:
            return []

        visibleRect = view.viewport().rect()  # pyright: ignore[reportOptionalMemberAccess]

        model = view.model()
        visible_indexes: list[QModelIndex] = []
        for row in range(model.rowCount()):
            idx = model.index(row, 0)
            src_idx = (
                model.mapToSource(idx)  # pyright: ignore[reportArgumentType]
                if isinstance(model, QSortFilterProxyModel)
                else idx
            )
            if not view.visualRect(idx).intersects(visibleRect):  # pyright: ignore[reportArgumentType]
                continue
            if not src_idx.isValid():
                RobustLogger().warning("Could not find item in the texture model for row %d", row)
                continue
            visible_indexes.append(src_idx)

        return visible_indexes

    def onFilterStringUpdated(self):
        filterString = self.ui.searchEdit.text()
        self.texturesProxyModel.setFilterFixedString(filterString)

    def onSectionAdded(self, parent: QStandardItem, first: int, last: int):
        for row in range(first, last + 1):
            section = self.ui.sectionCombo.itemData(row, Qt.UserRole)
            self.texture_models[section] = QStandardItemModel()

    def onSectionRemoved(self, parent: QStandardItem, first: int, last: int):
        for row in range(first, last + 1):
            section = self.ui.sectionCombo.itemData(row, Qt.UserRole)
            del self.texture_models[section]

    def onSectionChanged(self):
        section_name: str = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        self.texturesProxyModel.setSourceModel(self.texture_models[section_name])
        self.sectionChanged.emit(section_name)

    def onReloadClicked(self):
        for row in range(self.texturesModel.rowCount()):
            item = self.texturesModel.item(row)
            if item is None:
                RobustLogger().warning("Could not find item in the texture model for row %d", row)
                continue
            self.offload_texture_load(item, reload=True)

    def onRefreshClicked(self):
        for row in range(self.texturesModel.rowCount()):
            item = self.texturesModel.item(row)
            if item is None:
                RobustLogger().warning("Could not find item in the texture model for row %d", row)
                continue
            self.offload_texture_load(item, reload=False)
            self.ui.resourceList.update(item.index())  # pyright: ignore[reportArgumentType]
        viewport: QWidget | None = self.ui.resourceList.viewport()  # pyright: ignore[reportAssignmentType]
        assert viewport is not None, "Could not find viewport for resource list"
        viewport.update(0, 0, viewport.width(), viewport.height())

    def queueLoadViewableIcons(self):
        visible_indexes = self.visible_indexes(self.ui.resourceList)  # pyright: ignore[reportArgumentType]
        if not visible_indexes:
            return
        for index in visible_indexes:
            item = self.texturesModel.itemFromIndex(index)
            if item is None:
                RobustLogger().warning("Could not find item in the texture model for row %d", index.row())
                continue
            self.offload_texture_load(item, reload=False)

    def offload_texture_load(
        self,
        item: QStandardItem,
        desired_mipmap: int = 64,
        *,
        reload: bool = False,
    ):
        resource: FileResource = item.data(Qt.ItemDataRole.UserRole + 1)
        if reload:
            self._loading_resources.discard(resource)
        if resource in self._loading_resources:
            return
        self._loading_resources.add(resource)
        section_name = self.ui.sectionCombo.currentText()
        row = item.row()
        try:
            future = self._executor.submit(get_image_from_resource, (section_name, row), resource, desired_mipmap)
        except BrokenProcessPool as e:
            RobustLogger().warning("Process pool is broken, recreating...", exc_info=e)
            self._executor = ProcessPoolExecutor(max_workers=GlobalSettings().max_child_processes)
            future = self._executor.submit(get_image_from_resource, (section_name, row), resource, desired_mipmap)
        future.add_done_callback(self.iconLoaded.emit)

    def onIconLoaded(self, future: Future[tuple[tuple[str, int], TPCGetResult]]):
        item_context, tpc_get_result = future.result()
        section_name, row = item_context
        item = self.texture_models[section_name].item(row)
        if item is None:
            RobustLogger().warning("Could not find item in the texture model for row %d", row)
            return
        item.setIcon(tpc_get_result.to_qicon())
        self.ui.resourceList.update(item.index())  # pyright: ignore[reportArgumentType]

    def onResourceDoubleClicked(self):
        selected = self.selected_resources()
        if not selected:
            RobustLogger().warning("No resources selected in texture list for double click event")
            return
        self.requestOpenResource.emit(selected, None)


T = TypeVar("T")


def get_image_from_resource(context: T, resource: FileResource, desired_mipmap: int = 64) -> tuple[T, TPCGetResult]:
    if resource.restype() is ResourceType.TPC:
        tpc = read_tpc(resource.data())
        best_mipmap = next((i for i in range(tpc.mipmap_count()) if tpc.get(i).width <= desired_mipmap), 0)
        width, height, data = tpc.convert(TPCTextureFormat.RGBA, best_mipmap)
        return context, TPCGetResult(width, height, TPCTextureFormat.RGBA, data)

    try:
        from PIL import Image

        if resource.restype().extension.lower() in Image.registered_extensions():
            with Image.open(BytesIO(resource.data())) as img:
                pil_img = img.convert("RGBA")
            return context, TPCGetResult(pil_img.width, pil_img.height, TPCTextureFormat.RGBA, pil_img.tobytes())
    except ImportError:  # noqa: S110
        RobustLogger().warning(f"Pillow not available for resource type: {resource.restype()!r}")

    try:
        from qtpy.QtCore import Qt
        from qtpy.QtGui import QImage, QImageReader

        if resource.restype().extension.lower() in [bytes(x.data()).decode().lower() for x in QImageReader.supportedImageFormats()]:
            qimg = QImage()
            if qimg.loadFromData(resource.data()):
                qimg = qimg.convertToFormat(QImage.Format.Format_RGBA8888)
                if desired_mipmap < qimg.width() or desired_mipmap < qimg.height():
                    qimg = qimg.scaled(desired_mipmap, desired_mipmap, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                return context, TPCGetResult(qimg.width(), qimg.height(), TPCTextureFormat.RGBA, bytes(qimg.constBits().asarray()))
        else:  # use QFileIconProvider
            iconProvider = QFileIconProvider()
            pixmap = iconProvider.icon(QFileInfo(str(resource.filepath()))).pixmap(desired_mipmap, desired_mipmap)
            qimg = pixmap.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
            return context, TPCGetResult(qimg.width(), qimg.height(), TPCTextureFormat.RGBA, bytes(qimg.constBits().asarray()))
    except ImportError:  # noqa: S110
        RobustLogger().warning(f"Qt not available for resource type: {resource.restype()!r}")

    raise ValueError(f"No suitable image processing library available for resource type: {resource!r}")
