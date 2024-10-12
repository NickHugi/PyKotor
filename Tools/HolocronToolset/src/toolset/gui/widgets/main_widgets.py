#!/usr/bin/env python3
from __future__ import annotations

import multiprocessing
import os

from abc import abstractmethod
from collections import defaultdict
from concurrent.futures import Future, ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from io import BytesIO
from typing import TYPE_CHECKING, Any, ClassVar, List, TypeVar, cast

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy.QtCore import (
    QFileInfo,
    QPoint,
    QSortFilterProxyModel,
    QTimer,
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
    Slot,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QCursor, QIcon, QImage, QPixmap, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QFileIconProvider, QHeaderView, QMenu, QToolTip, QWidget

from pykotor.extract.file import FileResource
from pykotor.resource.formats.tpc.tpc_auto import read_tpc
from pykotor.resource.formats.tpc.tpc_data import TPCGetResult, TPCTextureFormat
from pykotor.resource.type import ResourceType
from toolset.gui.dialogs.load_from_location_result import ResourceItems
from toolset.gui.widgets.settings.installations import GlobalSettings

if TYPE_CHECKING:

    from qtpy.QtCore import QEvent, QModelIndex, QObject
    from qtpy.QtGui import QMouseEvent, QResizeEvent, QShowEvent
    from qtpy.QtWidgets import QScrollBar

    from pykotor.tools.path import CaseAwarePath
    from toolset.data.installation import HTInstallation


class MainWindowList(QWidget):
    """A widget for displaying and interacting with a list of KOTOR resources."""

    sig_request_open_resource: Signal = Signal(list, object)  # pyright: ignore[reportPrivateImportUsage]
    sig_request_extract_resource: Signal = Signal(list, object)  # pyright: ignore[reportPrivateImportUsage]
    sig_section_changed: Signal = Signal(str)  # pyright: ignore[reportPrivateImportUsage]

    @abstractmethod
    def selected_resources(self) -> list[FileResource]: ...


class ResourceStandardItem(QStandardItem):
    """A standard item for a resource."""

    def __init__(self, *args: Any, resource: FileResource, **kwargs: Any):
        """Initialize the resource standard item.

        Args:
        ----
            resource (FileResource): The resource to display.
        """
        super().__init__(*args, **kwargs)
        self.resource: FileResource = resource


class ResourceList(MainWindowList):
    """A widget for displaying and interacting with a list of KOTOR resources."""

    sig_request_reload: Signal = Signal(str)  # pyright: ignore[reportPrivateImportUsage]
    sig_request_refresh: Signal = Signal(bool)  # pyright: ignore[reportPrivateImportUsage]

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
        from toolset.uic.qtpy.widgets.resource_list import Ui_Form
        self.tooltip_text: str = ""
        self.tooltip_pos: QPoint = QPoint(0, 0)
        self.flattened: bool = False
        self.auto_resize_enabled: bool = True
        self.expanded_state: bool = False
        self.original_items: list[tuple[QStandardItem, list[list[QStandardItem]]]] = []

        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setup_signals()

        self.modules_model: ResourceModel = ResourceModel()
        self.modules_model.proxy_model().setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.ui.resourceTree.setModel(self.modules_model.proxy_model())  # pyright: ignore[reportArgumentType]
        self.ui.resourceTree.sortByColumn(0, Qt.SortOrder.AscendingOrder)  # pyright: ignore[reportArgumentType]
        self.section_model: QStandardItemModel = QStandardItemModel()
        self.ui.sectionCombo.setModel(self.section_model)  # pyright: ignore[reportArgumentType]

        # Connect the header context menu request signal
        tree_view_header: QHeaderView | None = self.ui.resourceTree.header()  # pyright: ignore[reportAssignmentType]
        assert tree_view_header is not None
        tree_view_header.setSectionsClickable(True)
        tree_view_header.setSortIndicatorShown(True)
        tree_view_header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)  # pyright: ignore[reportArgumentType]
        tree_view_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)  # pyright: ignore[reportArgumentType]

        self.tooltip_timer = QTimer(self)
        self.tooltip_timer.setSingleShot(True)
        self.tooltip_timer.timeout.connect(self.show_tooltip)

    def _clear_modules_model(self):
        self.modules_model.clear()
        self.modules_model.setColumnCount(2)
        self.modules_model.setHorizontalHeaderLabels(["ResRef", "Type"])

    def show_tooltip(self):
        """Show the tooltip, which represents the filepath of the resource."""
        print(self.tooltip_text)
        QToolTip.showText(QCursor.pos(), self.tooltip_text, self.ui.resourceTree)  # pyright: ignore[reportArgumentType]

    def setup_signals(self):
        """Set up the signals for the resource list."""
        self.ui.searchEdit.textEdited.connect(self.on_filter_string_updated)
        self.ui.sectionCombo.currentIndexChanged.connect(self.on_section_changed)
        self.ui.reloadButton.clicked.connect(self.on_reload_clicked)
        self.ui.refreshButton.clicked.connect(self.on_refresh_clicked)
        self.ui.resourceTree.customContextMenuRequested.connect(self.on_resource_context_menu)
        self.ui.resourceTree.doubleClicked.connect(self.on_resource_double_clicked)

    def enterEvent(self, event: QEvent):  # pylint: disable=invalid-name  # pyright: ignore[reportIncompatibleMethodOverride]
        """Stop the tooltip timer and hide the tooltip when the mouse enters the widget."""
        self.tooltip_timer.stop()
        QToolTip.hideText()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent):  # pylint: disable=invalid-name  # pyright: ignore[reportIncompatibleMethodOverride]
        """Stop the tooltip timer and hide the tooltip when the mouse leaves the widget."""
        self.tooltip_timer.stop()
        QToolTip.hideText()
        super().leaveEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):  # pylint: disable=invalid-name  # pyright: ignore[reportIncompatibleMethodOverride]
        """Show the tooltip when the mouse moves over a resource."""
        index = self.ui.resourceTree.indexAt(event.pos())  # type: ignore[arg-type]
        if index.isValid():
            model_index: QModelIndex = cast(QSortFilterProxyModel, self.ui.resourceTree.model()).mapToSource(index)  # pyright: ignore[reportArgumentType]
            item: ResourceStandardItem | QStandardItem | None = cast(
                QStandardItemModel,
                cast(QSortFilterProxyModel, self.ui.resourceTree.model()).sourceModel(),
            ).itemFromIndex(model_index)
            if isinstance(item, ResourceStandardItem):
                self.tooltip_text = str(item.resource.filepath())
                self.tooltip_pos = event.globalPos()
                self.tooltip_timer.start(1100)  # Set the delay to 3000ms (3 seconds)
            else:
                self.tooltip_timer.stop()
                QToolTip.hideText()
        else:
            self.tooltip_timer.stop()
            QToolTip.hideText()
        super().mouseMoveEvent(event)

    def hide_reload_button(self):
        """Hide the reload button."""
        self.ui.reloadButton.setVisible(False)

    def hide_section(self):
        """Hide the section combo box."""
        self.ui.line.setVisible(False)
        self.ui.sectionCombo.setVisible(False)
        self.ui.refreshButton.setVisible(False)

    def change_section(
        self,
        section: str,
    ):
        """Change the current section."""
        for i in range(self.ui.sectionCombo.count()):
            if section not in self.ui.sectionCombo.itemText(i):
                continue
            self.ui.sectionCombo.setCurrentIndex(i)

    def set_installation(self, installation: HTInstallation):
        """Set the installation for the resource list."""
        self._installation = installation

    def set_resources(
        self,
        resources: list[FileResource],
        custom_category: str | None = None,
        *,
        clear_existing: bool = True,
    ):
        """Adds and removes FileResources from the modules model.

        Args:
        ----
            resources: {list[FileResource]}: List of FileResource objects to set
            custom_category: {str | None}: The custom category to set the resources to.
            clear_existing: {bool}: Whether to clear the existing resources.
        """
        all_resources: list[ResourceStandardItem] = self.modules_model.all_resources_items()
        resource_set: set[FileResource] = set(resources)
        resource_item_map: dict[FileResource, ResourceStandardItem] = {item.resource: item for item in all_resources}
        for resource in resource_set:
            if resource in resource_item_map:
                resource_item_map[resource].resource = resource
            else:
                self.modules_model.add_resource(resource, custom_category)
        if clear_existing:
            for item in all_resources:
                if not isinstance(item, ResourceStandardItem):
                    continue
                if item.resource in resource_set:
                    continue
                item.parent().removeRow(item.row())
        self.modules_model.remove_unused_categories()

    def set_sections(
        self,
        sections: list[QStandardItem],
    ):
        """Set the sections for the resource list.

        Args:
        ----
            sections (list[QStandardItem]): The sections to set.
        """
        self.section_model.clear()
        for section in sections:
            self.section_model.insertRow(self.section_model.rowCount(), section)

    def set_resource_selection(
        self,
        resource: FileResource,
    ):
        """Set the selection of a resource in the resource list.

        Args:
        ----
            resource (FileResource): The resource to select.
        """
        model: ResourceModel = cast(QSortFilterProxyModel, self.ui.resourceTree.model()).sourceModel()  # type: ignore[attribute-access]
        if not isinstance(model, ResourceModel):
            RobustLogger().warning("Could not find model for resource list")
            return

        def select(parent, child):
            self.ui.resourceTree.expand(parent)
            self.ui.resourceTree.scrollTo(child)
            self.ui.resourceTree.setCurrentIndex(child)

        for item in model.all_resources_items():
            if not isinstance(item, ResourceStandardItem):
                continue
            resource_from_item: FileResource = item.resource
            if resource_from_item == resource:
                item_index: QModelIndex = model.proxy_model().mapFromSource(item.index())
                QTimer.singleShot(0, lambda index=item_index, item=item: select(item.parent().index(), index))

    def selected_resources(self) -> list[FileResource]:
        """Get the selected resources from the resource list.

        Returns:
        ----
            The resources selected by the user in the resource list.
        """
        return self.modules_model.resource_from_indexes(self.ui.resourceTree.selectedIndexes())  # pyright: ignore[reportArgumentType]

    def on_filter_string_updated(self):
        """Update the filter string for the resource list."""
        self.modules_model.proxy_model().set_filter_string(self.ui.searchEdit.text())

    def on_section_changed(self):
        """Handle the section change event."""
        data = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        self.sig_section_changed.emit(data)

    def on_reload_clicked(self):
        """Handle the reload button click event."""
        data = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        self.sig_request_reload.emit(data)

    def on_refresh_clicked(self):
        """Handle the refresh button click event."""
        self._clear_modules_model()
        self.sig_request_refresh.emit()

    def on_resource_context_menu(self, point: QPoint):
        """Handle the resource context menu event.

        Args:
        ----
            point (QPoint): The position of the context menu.
        """
        resources: list[FileResource] = self.selected_resources()
        if not resources:
            return
        menu = QMenu(self)
        menu.addAction("Open").triggered.connect(lambda: self.sig_request_open_resource.emit(resources, True))
        if all(resource.restype().contents == "gff" for resource in resources):
            menu.addAction("Open with GFF Editor").triggered.connect(lambda: self.sig_request_open_resource.emit(resources, False))
        menu.addSeparator()
        builder = ResourceItems(resources=resources)
        builder.viewport = lambda: self.ui.resourceTree
        builder.run_context_menu(point, menu=menu)

    def on_resource_double_clicked(self):
        self.sig_request_open_resource.emit(self.selected_resources(), None)

    def resizeEvent(self, event):  # pyright: ignore[reportIncompatibleMethodOverride]
        """Handle the resize event for the resource list."""
        super().resizeEvent(event)
        self.ui.resourceTree.setColumnWidth(1, 10)
        self.ui.resourceTree.setColumnWidth(0, self.ui.resourceTree.width() - 80)
        header: QHeaderView | None = self.ui.resourceTree.header()  # pyright: ignore[reportAssignmentType]
        if header is None:
            RobustLogger().warning("Could not find header for resource list")
            return
        header.setSectionResizeMode(QHeaderView.Interactive)  # type: ignore[arg-type]


class ResourceProxyModel(QSortFilterProxyModel):
    """A proxy model for the resource model."""

    def __init__(self, parent: QObject | None = None):
        """Initialize the resource proxy model."""
        super().__init__(parent)
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.filter_string: str = ""

    def set_filter_string(self, filter_string: str):
        """Set the filter string for the proxy model.

        Args:
        ----
            filter_string (str): The filter string to set.
        """
        self.filter_string = filter_string.lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        """Check if a row should be filtered out.

        Args:
        ----
            source_row (int): The row to check.
            source_parent (QModelIndex): The parent index of the row.

        Returns:
        ----
            Whether the row should be filtered out.
        """
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
        """Initialize the resource model."""
        super().__init__()
        self._category_items: dict[str, QStandardItem] = {}
        self._proxy_model: ResourceProxyModel = ResourceProxyModel(self)
        self._proxy_model.setSourceModel(self)
        self._proxy_model.setRecursiveFilteringEnabled(True)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["ResRef", "Type"])

    def proxy_model(self) -> ResourceProxyModel:
        """Get the proxy model for the resource model.

        Returns:
        ----
            The proxy model for the resource model.
        """
        return self._proxy_model

    def clear(self):
        """Clear the resource model."""
        super().clear()
        self._category_items = {}
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["ResRef", "Type"])

    def _add_resource_into_category(
        self,
        resource_type: ResourceType,
        custom_category: str | None = None,
    ) -> QStandardItem:
        """Add a resource to the resource model.

        Args:
            resource_type (ResourceType): The type of resource to add.
            custom_category (str | None): The custom category to add the resource to.

        Returns:
            The category item for the resource.
        """
        chosen_category = resource_type.category if custom_category is None else custom_category
        if chosen_category not in self._category_items:
            category_item = QStandardItem(chosen_category)
            category_item.setSelectable(False)
            unused_item = QStandardItem("")
            unused_item.setSelectable(False)
            self._category_items[chosen_category] = category_item
            self.appendRow([category_item, unused_item])
        return self._category_items[chosen_category]

    def add_resource(
        self,
        resource: FileResource,
        custom_category: str | None = None,
    ):
        """Add a resource to the resource model.

        Args:
        ----
            resource (FileResource): The resource to add.
            custom_category (str | None): The custom category to add the resource to.
        """
        self._add_resource_into_category(resource.restype(), custom_category).appendRow(
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
        """Get the resources from the resource model.

        Args:
        ----
            indexes (list[QModelIndex]): The indexes to get the resources from.
            proxy (bool): Whether to use the proxy model.

        Returns:
        ----
            The resources from the resource model.
        """
        items: list[QStandardItem] = [
            self.itemFromIndex(
                self._proxy_model.mapToSource(index)
                if proxy
                else index
            )
            for index in indexes
        ]
        return self.resource_from_items(items)

    def resource_from_items(
        self,
        items: list[QStandardItem],
    ) -> list[FileResource]:
        """Get the resources from the resource model.

        Args:
        ----
            items (list[QStandardItem]): The items to get the resources from.

        Returns:
        ----
            The resources from the resource model.
        """
        return [
            item.resource
            for item in items
            if isinstance(item, ResourceStandardItem)
        ]  # pyright: ignore[reportAttributeAccessIssue]

    def all_resources_items(self) -> list[ResourceStandardItem]:
        """Get all the resource items from the resource model.

        Returns:
        ----
            A list of all QStandardItem objects in the model that represent resource files.
        """
        resources = (
            category.child(i, 0)
            for category in self._category_items.values()
            for i in range(category.rowCount())
        )
        return cast(List[ResourceStandardItem], [item for item in resources if item is not None])

    def remove_unused_categories(self):
        """Remove unused categories from the resource model."""
        for row in range(self.rowCount())[::-1]:
            item = self.item(row)
            if item.rowCount() != 0:
                continue
            text = item.text()
            if text not in self._category_items:
                continue
            del self._category_items[text]
            self.removeRow(row)


class TextureList(MainWindowList):
    """A list widget for displaying tpc/tga textures, providing functionality to load images without blocking the UI."""

    sig_request_reload: Signal = Signal(object)  # pyright: ignore[reportPrivateImportUsage]
    sig_request_refresh: Signal = Signal()  # pyright: ignore[reportPrivateImportUsage]
    sig_icon_loaded: Signal = Signal(Future)  # pyright: ignore[reportPrivateImportUsage]

    BLANK_IMAGE: QImage = QImage(bytes(0 for _ in range(64 * 64 * 3)), 64, 64, QImage.Format.Format_RGB888)

    def __init__(self, parent: QWidget):
        """Initialize the texture list."""
        print(f"Initializing TextureList with parent: {parent}")
        super().__init__(parent)

        from toolset.uic.qtpy.widgets.texture_list import Ui_Form
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.resourceList.setUniformItemSizes(False)  # should be default but for clarity
        self.setup_signals()

        self._installation: HTInstallation | None = None
        self._executor: ProcessPoolExecutor = ProcessPoolExecutor(multiprocessing.cpu_count())
        self.texture_source_models: defaultdict[str, QStandardItemModel] = defaultdict(QStandardItemModel)
        self.textures_proxy_model: QSortFilterProxyModel = QSortFilterProxyModel()
        self.textures_proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        self.ui.resourceList.setModel(self.textures_proxy_model)  # pyright: ignore[reportArgumentType]
        self.ui.resourceList.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)  # pyright: ignore[reportArgumentType]
        self.ui.resourceList.customContextMenuRequested.connect(self.show_context_menu)
        self._loading_resources: set[FileResource] = set()

    def __del__(self):
        """Shutdown the executor when the texture list is deleted."""
        print("Shutting down executor in TextureList destructor")
        self._executor.shutdown(wait=False)

    def setup_signals(self):
        """Setup the signals for the texture list."""
        print("Setting up signals for TextureList")
        self.ui.searchEdit.editingFinished.connect(self.on_filter_string_updated)
        self.ui.sectionCombo.currentIndexChanged.connect(self.on_section_changed)
        self.ui.resourceList.doubleClicked.connect(self.on_resource_double_clicked)

        vert_scroll_bar: QScrollBar | None = self.ui.resourceList.verticalScrollBar()  # pyright: ignore[reportAssignmentType]
        if vert_scroll_bar is None:
            RobustLogger().warning("Could not find vertical scroll bar for resource list")
        else:
            vert_scroll_bar.valueChanged.connect(self.queue_load_visible_icons)
        self.sig_icon_loaded.connect(self.on_icon_loaded)

    def set_installation(self, installation: HTInstallation):
        """Set the installation for the resource list."""
        self._installation = installation

    def selected_resources(self) -> list[FileResource]:
        """Get the user selected resources from the texture list."""
        print("Getting selected resources from TextureList")
        resources: list[FileResource] = []
        current_section_name: str = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        print(f"Current section: {current_section_name}")
        cur_src_model = self.texture_source_models[current_section_name]

        for index in self.ui.resourceList.selectedIndexes():
            source_index = self.textures_proxy_model.mapToSource(index)
            if not source_index.isValid():
                RobustLogger().warning("Invalid source index for row {source_index.row()}")
                continue
            item = cur_src_model.itemFromIndex(source_index)
            if item is None:
                RobustLogger().warning("No item found for row {source_index.row()}")
                continue
            if not isinstance(item, ResourceStandardItem):
                RobustLogger().warning("Expected ResourceStandardItem, got {type(item).__name__}")
                continue
            resource = item.data(Qt.ItemDataRole.UserRole + 1)
            resources.append(resource)

        print(f"Selected resources: {resources}")
        return resources

    def visible_indexes(self) -> list[QModelIndex]:
        """Get the visible source indexes visible on the viewport."""
        print("Getting visible indexes for TextureList")
        view = self.ui.resourceList
        if (
            not view.isVisible()
            or self.textures_proxy_model.rowCount() == 0
        ):
            print("View is not visible or model is empty")
            return []

        visible_rect = view.viewport().rect()  # pyright: ignore[reportOptionalMemberAccess]
        print(f"Visible rect: {visible_rect}")

        visible_indexes: list[QModelIndex] = []
        for row in range(self.textures_proxy_model.rowCount()):
            proxy_index = self.textures_proxy_model.index(row, 0)
            if not proxy_index.isValid():
                RobustLogger().warning("Invalid proxy index for row {row}")
                continue
            if not view.visualRect(proxy_index).intersects(visible_rect):  # pyright: ignore[reportArgumentType]
                continue
            src_index = self.textures_proxy_model.mapToSource(proxy_index)  # pyright: ignore[reportArgumentType]
            if not src_index.isValid():
                RobustLogger().warning("Invalid source index for row {row}")
                continue
            visible_indexes.append(src_index)

        print(f"Number of visible indexes: {len(visible_indexes)}")
        return visible_indexes

    def set_sections(self, items: list[QStandardItem]):
        """Set the sections to be displayed in the texture list combobox."""
        print(f"Setting sections for TextureList with {len(items)} items")
        current_sections: set[str] = {
            self.ui.sectionCombo.itemData(i, Qt.ItemDataRole.UserRole)
            for i in range(self.ui.sectionCombo.count())
        }
        new_sections: set[str] = {
            item.data(Qt.ItemDataRole.UserRole)
            for item in items
        }

        # Remove sections that are no longer present
        removed_sections: set[str] = current_sections - new_sections
        for section in removed_sections:
            del self.texture_source_models[section]

        self.ui.sectionCombo.clear()

        for item in items:
            section = item.data(Qt.ItemDataRole.UserRole)
            self.ui.sectionCombo.addItem(item.text(), section)

    def set_resources(self, resources: list[FileResource]):
        """Set the resources to be displayed in the texture list."""
        print(f"Setting resources for TextureList with {len(resources)} resources")
        current_section_name: str = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        print(f"Current section: {current_section_name}")
        current_source_model: QStandardItemModel = self.texture_source_models[current_section_name]
        current_source_model.clear()

        added_count = 0
        for resource in resources:
            resname, restype = resource.resname(), resource.restype()
            if restype not in (ResourceType.TGA, ResourceType.TPC):
                continue
            item = ResourceStandardItem(resname, resource=resource)
            item.setData(resource, Qt.ItemDataRole.UserRole + 1)
            current_source_model.appendRow(item)
            added_count += 1

        print(f"Added {added_count} resources to the model")
        self.queue_load_visible_icons()

    def on_section_changed(self):
        """Handle the section combobox selection change."""
        new_section_name: str = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        print(f"Section changed to: '{new_section_name}'")
        self.textures_proxy_model.setSourceModel(self.texture_source_models[new_section_name])
        self.sig_section_changed.emit(new_section_name)

    def on_filter_string_updated(self):
        """Handle the filter string update."""
        filter_string = self.ui.searchEdit.text()
        print(f"Updating filter string to: {filter_string}")
        self.textures_proxy_model.setFilterFixedString(filter_string)

    def show_context_menu(self, position: QPoint):
        """Show the context menu for the texture list."""
        print(f"Showing context menu at position: {position}")
        menu = QMenu(self)
        reload_action = menu.addAction("Reload")
        reload_action.triggered.connect(self.on_reload_clicked)
        action = menu.exec(self.ui.resourceList.mapToGlobal(position))  # pyright: ignore[reportArgumentType, reportCallIssue]
        if action != reload_action:
            return
        proxy_index = self.ui.resourceList.indexAt(position)  # pyright: ignore[reportArgumentType]
        if not proxy_index.isValid():
            return
        source_index = self.textures_proxy_model.mapToSource(proxy_index)  # pyright: ignore[reportArgumentType]
        if not source_index.isValid():
            return
        section_name: str = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        item = self.texture_source_models[section_name].itemFromIndex(source_index)
        if item is None:
            RobustLogger().warning("Could not find item in the texture model for row %d", source_index.row())
            return
        if not isinstance(item, ResourceStandardItem):
            RobustLogger().warning("Expected ResourceStandardItem, got %s", type(item).__name__)
            return
        self.offload_texture_load(item, reload=True)

    def on_reload_clicked(self):
        """Handle the reload button click."""
        print("Reload button clicked")
        cur_section_name: str = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        cur_src_model = self.texture_source_models[cur_section_name]
        for row in range(self.textures_proxy_model.rowCount()):
            proxy_index = self.textures_proxy_model.index(row, 0)
            if not proxy_index.isValid():
                RobustLogger().warning("Could not find item in the proxy model for row %d", row)
                continue
            src_index = self.textures_proxy_model.mapToSource(proxy_index)  # pyright: ignore[reportArgumentType]
            if not src_index.isValid():
                RobustLogger().warning("Could not find item in the src model for row %d", row)
                continue
            item = cur_src_model.itemFromIndex(src_index)
            if item is None:
                RobustLogger().warning("Could not find item in the texture model for row %d", row)
                continue
            if not isinstance(item, ResourceStandardItem):
                RobustLogger().warning("Expected ResourceStandardItem, got %s", type(item).__name__)
                continue
            self.offload_texture_load(item, reload=True)

    def on_refresh_clicked(self):
        """Handle the refresh button click."""
        print("Refresh button clicked")
        cur_section_name: str = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        cur_src_model = self.texture_source_models[cur_section_name]
        for row in range(self.textures_proxy_model.rowCount()):
            proxy_index = self.textures_proxy_model.index(row, 0)
            if not proxy_index.isValid():
                RobustLogger().warning("Could not find item in the proxy model for row %d", row)
                continue
            src_index = self.textures_proxy_model.mapToSource(proxy_index)  # pyright: ignore[reportArgumentType]
            if not src_index.isValid():
                RobustLogger().warning("Could not find item in the src model for row %d", row)
                continue
            item = cur_src_model.itemFromIndex(src_index)
            if item is None:
                RobustLogger().warning("Could not find item in the texture model for row %d", row)
                continue
            if not isinstance(item, ResourceStandardItem):
                RobustLogger().warning("Expected ResourceStandardItem, got %s", type(item).__name__)
                continue
            self.offload_texture_load(item=item, reload=False)
            self.ui.resourceList.update(item.index())  # pyright: ignore[reportArgumentType]
        viewport: QWidget | None = self.ui.resourceList.viewport()  # pyright: ignore[reportAssignmentType]
        if viewport is None:
            RobustLogger().warning("Could not find viewport for resource list")
        viewport.update(0, 0, viewport.width(), viewport.height())

    def queue_load_visible_icons(self):
        """Queue the loading of icons for visible items."""
        print("Queueing load of visible icons")
        visible_indexes = self.visible_indexes()
        print(f"Number of visible indexes: {len(visible_indexes)}")
        if not visible_indexes:
            return
        section_name: str = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        print(f"Current section: {section_name}")
        cur_src_model: QStandardItemModel = self.texture_source_models[section_name]
        for index in visible_indexes:
            item = cur_src_model.itemFromIndex(index)
            if item is None:
                RobustLogger().warning("No item found for row {index.row()}")
                continue
            if not isinstance(item, ResourceStandardItem):
                RobustLogger().warning("Expected ResourceStandardItem, got {type(item).__name__}")
                continue
            self.offload_texture_load(item, reload=False)

    def offload_texture_load(
        self,
        item: ResourceStandardItem,
        desired_mipmap: int = 64,
        *,
        reload: bool = False,
    ):
        """Queue the loading of an icon for a given item."""
        print(f"Offloading texture load for item: {item.text()}, desired_mipmap: {desired_mipmap}, reload: {reload}")
        assert isinstance(item, ResourceStandardItem), f"Expected ResourceStandardItem, got {type(item).__name__}"
        if reload:
            self._loading_resources.discard(item.resource)
        if item.resource in self._loading_resources:
            print(f"Resource {item.resource.resname()} already loading, skipping")
            return
        self._loading_resources.add(item.resource)

        section_name: str = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        row = item.row()
        try:
            future = self._executor.submit(get_image_from_resource, (section_name, row), item.resource, desired_mipmap)
            print(f"Submitted texture load job for {item.resource.resname()}")
        except BrokenProcessPool as e:
            RobustLogger().error("Process pool is broken, recreating... Error", exc_info=e)
            self._executor = ProcessPoolExecutor(max_workers=GlobalSettings().max_child_processes)
            future = self._executor.submit(get_image_from_resource, (section_name, row), item.resource, desired_mipmap)
            print(f"Resubmitted texture load job for {item.resource.resname()}")
        future.add_done_callback(self.sig_icon_loaded.emit)

    @Slot(Future)
    def on_icon_loaded(
        self,
        future: Future[tuple[tuple[str, int], TPCGetResult]],
    ):
        """Handle the completion of an icon load."""
        #print("Icon loaded callback triggered")
        item_context, tpc_get_result = future.result()
        section_name, row = item_context
        print(f"Loaded icon for section: {section_name}, row: {row}")
        src_index = self.texture_source_models[section_name].index(row, 0)
        if not src_index.isValid():
            RobustLogger().warning("Invalid source index for row {row}")
            return
        item = self.texture_source_models[section_name].itemFromIndex(src_index)
        if item is None:
            RobustLogger().warning(f"No item found for row {row}")
            return
        image: QImage = tpc_get_result.to_qimage()
        print(f"Image size: {image.width()}x{image.height()} name '{item.text()}'")
        pixmap = QPixmap.fromImage(image.mirrored(False, True)).scaled(self.ui.resourceList.iconSize(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        item.setIcon(QIcon(pixmap))

    def on_resource_double_clicked(self):
        self.sig_request_open_resource.emit(self.selected_resources(), None)

    def resizeEvent(self, a0: QResizeEvent):  # pylint: disable=unused-argument,invalid-name  # pyright: ignore[reportIncompatibleMethodOverride]
        """Ensures icons that come into view are queued to load when the widget is resized."""
        print(f"Resize event: {a0.size()}")
        QTimer.singleShot(0, self.queue_load_visible_icons)

    def showEvent(self, a0: QShowEvent):  # pylint: disable=unused-argument,invalid-name,  # pyright: ignore[reportIncompatibleMethodOverride]
        """Ensures icons that come into view are queued to load when the widget is shown."""
        print("Show event triggered")
        QTimer.singleShot(0, self.queue_load_visible_icons)

    def mouseMoveEvent(self, event: QMouseEvent):  # pylint: disable=unused-argument,invalid-name  # pyright: ignore[reportIncompatibleMethodOverride]
        """Prioritize loading textures for the currently hovered item."""
        super().mouseMoveEvent(event)
        global_pos = self.mapToGlobal(event.pos())
        print(f"Mouse move event at global position: {global_pos}")
        proxy_index: QModelIndex = self.ui.resourceList.indexAt(self.ui.resourceList.mapFromGlobal(global_pos))  # pyright: ignore[reportAssignmentType, reportCallIssue, reportArgumentType]
        if not proxy_index.isValid():
            return
        source_index: QModelIndex = self.textures_proxy_model.mapToSource(proxy_index)  # pyright: ignore[reportArgumentType]
        if not source_index.isValid():
            return
        section_name: str = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        model = self.texture_source_models[section_name]
        item: QStandardItem | None = model.itemFromIndex(source_index)
        if item is None:
            RobustLogger().warning(f"Warning: No item found for row {source_index.row()}")
            return
        if not isinstance(item, ResourceStandardItem):
            RobustLogger().warning(f"Warning: Expected ResourceStandardItem, got {type(item).__name__}")
            return
        print(f"Prioritizing texture load for hovered item: {item.text()}")
        self.offload_texture_load(item, reload=True)


T = TypeVar("T")


def get_image_from_tpc(resource: FileResource, desired_mipmap: int) -> TPCGetResult:
    """Get an image from a TPC resource."""
    tpc = read_tpc(resource.data())
    best_mipmap = next((i for i in range(tpc.mipmap_count()) if tpc.get(i).width <= desired_mipmap), 0)
    width, height, data = tpc.convert(TPCTextureFormat.RGB, best_mipmap)
    return TPCGetResult(width, height, TPCTextureFormat.RGB, bytes(data))


def get_image_from_pillow(resource: FileResource) -> TPCGetResult:
    """Get an image using Pillow."""
    from PIL import Image

    if resource.restype().extension.lower() in Image.registered_extensions():
        with Image.open(BytesIO(resource.data())) as img:
            rgba_img = img.convert("RGBA")
        return TPCGetResult(rgba_img.width, rgba_img.height, TPCTextureFormat.RGBA, rgba_img.tobytes())
    raise ValueError(f"Unsupported image format for Pillow: {resource.restype()!r}")


def get_image_from_qt(resource: FileResource, desired_mipmap: int) -> TPCGetResult:
    """Get an image using Qt."""
    from qtpy.QtCore import Qt  # pylint: disable=redefined-outer-name,reimported
    from qtpy.QtGui import QImage, QImageReader  # pylint: disable=redefined-outer-name,reimported

    if resource.restype().extension.lower() in {
        bytes(x.data()).decode().lower()
        for x in QImageReader.supportedImageFormats()
    }:
        qimg = QImage()
        if qimg.loadFromData(resource.data()):
            qimg = qimg.convertToFormat(QImage.Format.Format_RGBA8888)
            if (
                desired_mipmap < qimg.width()
                or desired_mipmap < qimg.height()
            ):
                qimg = qimg.scaled(
                    desired_mipmap,
                    desired_mipmap,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            return TPCGetResult(
                qimg.width(),
                qimg.height(),
                TPCTextureFormat.RGBA,
                bytes(qimg.constBits().asarray()),
            )

    icon_provider: QFileIconProvider = QFileIconProvider()
    icon: QIcon = icon_provider.icon(QFileInfo(str(resource.filepath())))
    pixmap: QPixmap = icon.pixmap(desired_mipmap, desired_mipmap)
    qimg: QImage = pixmap.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
    return TPCGetResult(
        qimg.width(),
        qimg.height(),
        TPCTextureFormat.RGBA,
        bytes(qimg.constBits().asarray()),
    )


def get_image_from_resource(
    context: T,
    resource: FileResource,
    desired_mipmap: int = 64,
) -> tuple[T, TPCGetResult]:
    """Get an image from a resource."""
    if resource.restype() is ResourceType.TPC:
        return context, get_image_from_tpc(resource, desired_mipmap)

    try:
        return context, get_image_from_pillow(resource)
    except ImportError:  # noqa: S110
        RobustLogger().warning(f"Pillow not available to load image data in resource: {resource.path_ident()!r}")

    try:
        return context, get_image_from_qt(resource, desired_mipmap)
    except ImportError:  # noqa: S110
        RobustLogger().warning(f"Qt not available to load image data in resource: {resource.path_ident()!r}")

    raise ValueError(f"No suitable image processing library available to load image data in resource: {resource.path_ident()!r}")


def on_open_resources(
    resources: list[FileResource],
    resource_widget: ResourceList | TextureList,
    active: HTInstallation | None,
):
    """Open the given resources."""
    from pykotor.extract.file import ResourceIdentifier
    from toolset.utils.window import open_resource_editor
    for resource in resources:
        _filepath, _editor = open_resource_editor(
            resource,
            active,
            gff_specialized=GlobalSettings().gff_specializedEditors,
        )
        print("<SDM> [onOpenResources scope] _editor: ", _editor)

    if (
        resources
        or isinstance(resource_widget, TextureList)
    ):
        return
    filename: str = resource_widget.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
    print("<SDM> [onOpenResources scope] filename: ", filename)

    if (
        not filename
        or not filename.strip()
        or not active
    ):
        return
    erf_filepath: CaseAwarePath = active.module_path() / filename
    print("<SDM> [onOpenResources scope] erf_filepath: ", erf_filepath)

    if (
        not erf_filepath.exists()
        or not erf_filepath.is_file()
    ):
        RobustLogger().warning(f"Not loading '{erf_filepath}'. File does not exist")
        return
    res_ident: ResourceIdentifier = ResourceIdentifier.from_path(erf_filepath)

    if not res_ident.restype:
        RobustLogger().warning(f"Not loading '{erf_filepath}'. Invalid resource")
        return
    erf_file_resource = FileResource(res_ident.resname, res_ident.restype, os.path.getsize(erf_filepath), 0x0, erf_filepath)  # noqa: PTH202
    _filepath, _editor = open_resource_editor(
        erf_file_resource,
        active,
        gff_specialized=GlobalSettings().gff_specializedEditors,
    )
