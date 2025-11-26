from __future__ import annotations

import contextlib
import multiprocessing
import os

from abc import abstractmethod
from collections import defaultdict
from concurrent.futures import Future, ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar, cast

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy import QtCore
from qtpy.QtCore import (
    QFileInfo,  # pyright: ignore[reportPrivateImportUsage]
    QModelIndex,  # pyright: ignore[reportPrivateImportUsage]
    QPoint,  # pyright: ignore[reportPrivateImportUsage]
    QSortFilterProxyModel,  # pyright: ignore[reportPrivateImportUsage]
    QTimer,  # pyright: ignore[reportPrivateImportUsage]
    Qt,  # pyright: ignore[reportPrivateImportUsage]
    Signal,  # pyright: ignore[reportPrivateImportUsage]
    Slot,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QCursor, QIcon, QImage, QImageReader, QPixmap, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QAbstractItemView, QApplication, QFileDialog, QFileIconProvider, QHeaderView, QInputDialog, QListView, QMenu, QStyle, QToolTip, QWidget

from pykotor.extract.file import FileResource
from pykotor.resource.formats.tpc.tpc_auto import read_tpc, write_tpc
from pykotor.resource.formats.tpc.tpc_data import TPC, TPCMipmap, TPCTextureFormat
from pykotor.resource.type import ResourceType
from toolset.data.installation import HTInstallation
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.gff import GFFContent
from pykotor.resource.formats.tpc import TPC, TPCTextureFormat
from pykotor.resource.type import ResourceType
from toolset.gui.dialogs.load_from_location_result import ResourceItems
from toolset.gui.widgets.settings.installations import GlobalSettings

try:
    from toolset.gui.widgets.texture_loader import TextureLoaderProcess, deserialize_mipmap
except Exception:  # noqa: BLE001
    TextureLoaderProcess = None
    deserialize_mipmap = None

if TYPE_CHECKING:
    from PIL.Image import Image
    from qtpy.QtCore import QAbstractItemModel, QModelIndex, QObject, QRect
    from qtpy.QtGui import QMouseEvent, QResizeEvent, QShowEvent
    from qtpy.QtWidgets import QScrollBar, _QMenu
    from qtpy.sip import voidptr

    from pykotor.resource.formats.tpc.tpc_data import TPC
    from toolset.data.installation import HTInstallation
    from utility.ui_libraries.qt.widgets.itemviews.listview import RobustListView


class MainWindowList(QWidget):
    """A widget for displaying and interacting with a list of KOTOR resources."""

    sig_request_open_resource: Signal = Signal(list, object)  # pyright: ignore[reportPrivateImportUsage]
    sig_request_extract_resource: Signal = Signal(list, object)  # pyright: ignore[reportPrivateImportUsage]
    sig_section_changed: Signal = Signal(str)  # pyright: ignore[reportPrivateImportUsage]
    requestOpenResource: ClassVar[QtCore.Signal] = QtCore.Signal(object, object)  # pyright: ignore[reportPrivateImportUsage]
    requestExtractResource: ClassVar[QtCore.Signal] = QtCore.Signal(object)  # pyright: ignore[reportPrivateImportUsage]
    requestMakeUnskippable: ClassVar[QtCore.Signal] = QtCore.Signal(object)  # pyright: ignore[reportPrivateImportUsage]
    requestConvertGFF: ClassVar[QtCore.Signal] = QtCore.Signal(object, object)  # pyright: ignore[reportPrivateImportUsage]  # resources, target_game
    requestConvertTPC: ClassVar[QtCore.Signal] = QtCore.Signal(object)  # pyright: ignore[reportPrivateImportUsage]
    requestConvertTGA: ClassVar[QtCore.Signal] = QtCore.Signal(object)  # pyright: ignore[reportPrivateImportUsage]
    sectionChanged: ClassVar[QtCore.Signal] = QtCore.Signal(object)  # pyright: ignore[reportPrivateImportUsage]
    @abstractmethod
    def selected_resources(self) -> list[FileResource]: ...


class ResourceStandardItem(QStandardItem):
    """A standard item for a resource."""

    def __init__(self, *args: Any, resource: FileResource, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.resource: FileResource = resource


class ResourceList(MainWindowList):
    """A widget for displaying and interacting with a list of KOTOR resources."""

    sig_request_reload: Signal = Signal(str)  # pyright: ignore[reportPrivateImportUsage]
    sig_request_refresh: Signal = Signal()  # pyright: ignore[reportPrivateImportUsage]

    HORIZONTAL_HEADER_LABELS: ClassVar[list[str]] = ["ResRef", "Type"]

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        from toolset.uic.qtpy.widgets.resource_list import Ui_Form

        self.tooltip_text: str = ""
        self.original_items: list[tuple[QStandardItem, list[list[QStandardItem]]]] = []

        self.ui: Ui_Form = Ui_Form()
        self.ui.setupUi(self)
        self.setup_signals()

        self.modules_model: ResourceModel = ResourceModel()
        self.modules_model.proxy_model().setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.ui.resourceTree.setModel(self.modules_model.proxy_model())
        self.ui.resourceTree.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.section_model: QStandardItemModel = QStandardItemModel()
        self.ui.sectionCombo.setModel(self.section_model)

        # Set context menu policy and selection mode
        self.ui.resourceTree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.resourceTree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        # Connect the header context menu request signal
        tree_view_header: QHeaderView | None = self.ui.resourceTree.header()
        assert tree_view_header is not None
        tree_view_header.setSectionsClickable(True)
        tree_view_header.setSortIndicatorShown(True)
        tree_view_header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        tree_view_header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    def _clear_modules_model(self):
        self.modules_model.clear()
        self.modules_model.setColumnCount(2)
        self.modules_model.setHorizontalHeaderLabels(["ResRef", "Type"])

    def setup_signals(self):
        """Set up the signals for the resource list."""
        self.ui.searchEdit.textEdited.connect(self.on_filter_string_updated)
        self.ui.sectionCombo.currentIndexChanged.connect(self.on_section_changed)
        self.ui.resourceTree.customContextMenuRequested.connect(self.on_resource_context_menu)
        self.ui.resourceTree.doubleClicked.connect(self.on_resource_double_clicked)
        self.ui.reloadButton.clicked.connect(self.on_reload_clicked)
        self.ui.refreshButton.clicked.connect(self.on_refresh_clicked)

    def hide_reload_button(self):
        """Hide the reload button."""
        self.ui.reloadButton.setVisible(False)

    def hide_section(self):
        """Hide the section combo box."""
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
        self._installation: HTInstallation = installation

    def set_resources(
        self,
        resources: list[FileResource],
        custom_category: str | None = None,
        *,
        clear_existing: bool = True,
    ):
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
                parent_item: QStandardItem | None = item.parent()
                if parent_item is None:
                    continue
                parent_item.removeRow(item.row())
        self.modules_model.remove_unused_categories()

    def set_sections(
        self,
        sections: list[QStandardItem],
    ):
        self.section_model.clear()
        for section in sections:
            self.section_model.insertRow(self.section_model.rowCount(), section)

    def set_resource_selection(
        self,
        resource: FileResource,
    ):
        model: QStandardItemModel = cast(QSortFilterProxyModel, self.ui.resourceTree.model()).sourceModel()  # type: ignore[attribute-access]
        if not isinstance(model, ResourceModel):
            RobustLogger().warning("Could not find model for resource list")
            return

        def select(parent: QModelIndex, child: QModelIndex):
            self.ui.resourceTree.expand(parent)
            self.ui.resourceTree.scrollTo(child)
            self.ui.resourceTree.setCurrentIndex(child)

        for item in model.all_resources_items():
            if not isinstance(item, ResourceStandardItem):
                continue
            resource_from_item: FileResource = item.resource
            if resource_from_item == resource:
                item_index: QModelIndex = model.proxy_model().mapFromSource(item.index())

                def select_item(index: QModelIndex = item_index):
                    if not index.isValid():
                        RobustLogger().warning(f"Invalid index to select_item: {index}")
                        return
                    select(index.parent(), index)

                QTimer.singleShot(0, select_item)

    def selected_resources(self) -> list[FileResource]:
        return self.modules_model.resource_from_indexes(self.ui.resourceTree.selectedIndexes())  # pyright: ignore[reportArgumentType]

    @Slot()
    def on_filter_string_updated(self):
        """Update the filter string for the resource list."""
        self.modules_model.proxy_model().set_filter_string(self.ui.searchEdit.text())

    @Slot()
    def on_section_changed(self):
        """Handle the section change event."""
        data: str = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        self.sig_section_changed.emit(data)

    @Slot()
    def on_reload_clicked(self):
        """Handle the reload button click event."""
        data: str = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        self.sig_request_reload.emit(data)

    @Slot()
    def on_refresh_clicked(self):
        """Handle the refresh button click event."""
        self._clear_modules_model()
        self.sig_request_refresh.emit()

    @Slot(QPoint)
    def on_resource_context_menu(self, point: QPoint):
        resources: list[FileResource] = self.selected_resources()
        if not resources:
            return
        
        # Capture the tree view reference before creating menu
        tree_view = self.ui.resourceTree
        if tree_view is None:
            return
        
        menu = QMenu(self)
        
        # Store resources in a local variable to avoid closure issues
        local_resources = list(resources)
        
        open_action = menu.addAction("Open")
        open_action.triggered.connect(lambda checked=False, res=local_resources: self.sig_request_open_resource.emit(res, True))
        
        if all(resource.restype().contents == "gff" for resource in resources):
            gff_action = menu.addAction("Open with GFF Editor")
            gff_action.triggered.connect(lambda checked=False, res=local_resources: self.sig_request_open_resource.emit(res, False))
        
        # Add save-specific context menu items if this is a save resource
        # Check if this resource list is from the saves widget by checking parent
        is_saves_widget = self._is_saves_widget()
        if is_saves_widget:
            menu.addSeparator()
            save_editor_action = menu.addAction("Open Save Editor")
            save_editor_action.triggered.connect(self.on_open_save_editor_from_context)
            fix_corruption_action = menu.addAction("Fix savegame corruption")
            fix_corruption_action.triggered.connect(self.on_fix_save_corruption_from_context)
        
        menu.addSeparator()
        builder = ResourceItems(resources=local_resources)
        
        # Use a safer approach - store tree view reference and use method
        def get_viewport():
            return tree_view
        builder.viewport = get_viewport
        
        try:
            builder.run_context_menu(point, menu=menu)
        except Exception as e:
            RobustLogger().exception(f"Error showing context menu: {e}")
    
    def _is_saves_widget(self) -> bool:
        """Check if this widget is the saves widget."""
        try:
            parent_widget = self.parent()
            depth = 0
            max_depth = 10  # Prevent infinite loops
            while parent_widget and depth < max_depth:
                parent_name = parent_widget.objectName() if hasattr(parent_widget, 'objectName') else ''
                if 'saves' in parent_name.lower():
                    return True
                if hasattr(parent_widget, 'ui') and hasattr(parent_widget.ui, 'savesWidget'):
                    return True
                parent_widget = parent_widget.parent() if hasattr(parent_widget, 'parent') and callable(parent_widget.parent) else None
                depth += 1
            return False
        except Exception:
            return False
    
    def on_open_save_editor_from_context(self):
        """Signal the main window to open the save editor."""
        # Get the main window and call its open_save_editor method
        main_window = self.window()
        if hasattr(main_window, 'on_open_save_editor'):
            main_window.on_open_save_editor()
    
    def on_fix_save_corruption_from_context(self):
        """Signal the main window to fix save corruption."""
        try:
            # Get the main window and call its fix_save_corruption_for_path method
            main_window = self.window()
            if not hasattr(main_window, 'active') or not main_window.active:
                return
            
            # Get the selected save path from the tree
            tree_view = self.ui.resourceTree
            if tree_view is None:
                return
            
            selected_indexes = tree_view.selectedIndexes()
            if not selected_indexes:
                return
            
            proxy_model: QAbstractItemModel | None = tree_view.model()
            if proxy_model is None or not isinstance(proxy_model, QSortFilterProxyModel):
                return
            
            for index in selected_indexes:
                source_index: QModelIndex = proxy_model.mapToSource(index)
                if self.modules_model is None:
                    continue
                item = self.modules_model.itemFromIndex(source_index)
                
                # Navigate up to find the save folder item (top-level item)
                while item and item.parent():
                    item = item.parent()
                
                if item:
                    save_name = item.text()
                    # Find the save path
                    combo_data = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
                    if combo_data is None:
                        continue
                    current_save_location = Path(combo_data)
                    for save_path in main_window.active.saves.get(current_save_location, {}):
                        if save_name in str(save_path):
                            if hasattr(main_window, 'fix_save_corruption_for_path'):
                                main_window.fix_save_corruption_for_path(save_path)
                            break
                    break
        except Exception as e:
            RobustLogger().exception(f"Error fixing save corruption: {e}")

    @Slot()
    def on_resource_double_clicked(self):
        self.sig_request_open_resource.emit(self.selected_resources(), None)

    def mouseMoveEvent(self, event: QMouseEvent):  # pylint: disable=invalid-name  # pyright: ignore[reportIncompatibleMethodOverride]
        """Show the tooltip when the mouse moves over a resource."""
        proxy_index: QModelIndex = self.ui.resourceTree.indexAt(event.pos())  # type: ignore[arg-type]
        if proxy_index.isValid():
            src_index: QModelIndex = cast(QSortFilterProxyModel, self.ui.resourceTree.model()).mapToSource(proxy_index)  # pyright: ignore[reportArgumentType]
            item: ResourceStandardItem | QStandardItem | None = cast(
                QStandardItemModel,
                cast(QSortFilterProxyModel, self.ui.resourceTree.model()).sourceModel(),
            ).itemFromIndex(src_index)
            if isinstance(item, ResourceStandardItem):
                QToolTip.showText(QCursor.pos(), str(item.resource.filepath()), self.ui.resourceTree)
            else:
                QToolTip.hideText()
        else:
            QToolTip.hideText()
        super().mouseMoveEvent(event)


class ResourceProxyModel(QSortFilterProxyModel):
    """A proxy model for the resource model."""

    def __init__(
        self,
        parent: QObject | None = None,
    ):
        """Initialize the resource proxy model."""
        super().__init__(parent)
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.filter_string: str = ""

    def set_filter_string(
        self,
        filter_string: str,
    ):
        self.filter_string = filter_string.lower()
        self.invalidateFilter()

    def filterAcceptsRow(
        self,
        source_row: int,
        source_parent: QModelIndex,
    ) -> bool:
        model: QAbstractItemModel | None = self.sourceModel()  # pyright: ignore[reportAssignmentType]
        assert isinstance(model, QStandardItemModel)
        resref_index: QModelIndex = model.index(source_row, 0, source_parent)
        item: ResourceStandardItem | QStandardItem | None = model.itemFromIndex(resref_index)
        if isinstance(item, ResourceStandardItem):
            # Get the file name and resource name
            filename: str = item.resource.filepath().name.lower()
            resname: str = item.resource.filename().lower()

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
        chosen_category: str = resource_type.category if custom_category is None else custom_category
        if chosen_category not in self._category_items:
            category_item = QStandardItem(chosen_category)
            category_item.setSelectable(False)
            self._category_items[chosen_category] = category_item
            unused_item = QStandardItem("")
            unused_item.setSelectable(False)
            self.appendRow([category_item, unused_item])
        return self._category_items[chosen_category]

    def add_resource(
        self,
        resource: FileResource,
        custom_category: str | None = None,
    ):
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
        return [
            item.resource
            for index in indexes
            for item in [self.itemFromIndex(self._proxy_model.mapToSource(index) if proxy else index)]
            if isinstance(item, ResourceStandardItem)
        ]

    def all_resources_items(self) -> list[ResourceStandardItem]:
        resources: tuple[QStandardItem | None, ...] = tuple(category.child(i, 0) for category in self._category_items.values() for i in range(category.rowCount()))
        return [item for item in resources if isinstance(item, ResourceStandardItem)]

    def remove_unused_categories(self):
        """Remove unused categories from the resource model."""
        for row in range(self.rowCount())[::-1]:
            item: QStandardItem | None = self.item(row)
            assert item is not None, "Item should not be None"
            if item.rowCount() != 0:
                continue
            text: str = item.text()
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
        # Ensure loader attribute exists even if initialization aborts early.
        self._loader: multiprocessing.Process | None = None
        super().__init__(parent)

        from toolset.uic.qtpy.widgets.texture_list import Ui_Form

        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.resourceList.setUniformItemSizes(False)  # should be default
        self.ui.resourceList.setResizeMode(QListView.ResizeMode.Adjust)
        self.ui.resourceList.setMovement(QListView.Movement.Snap)
        self.ui.resourceList.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setup_signals()

        self._installation: HTInstallation | None = None
        self._executor: ProcessPoolExecutor = ProcessPoolExecutor(max_workers=max(1, multiprocessing.cpu_count()))
        self.texture_source_models: defaultdict[str, QStandardItemModel] = defaultdict(QStandardItemModel)
        self.textures_proxy_model: QSortFilterProxyModel = QSortFilterProxyModel()
        self.textures_proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        self.ui.resourceList.setModel(self.textures_proxy_model)  # pyright: ignore[reportArgumentType]
        self.ui.resourceList.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)  # pyright: ignore[reportArgumentType]
        self.ui.resourceList.customContextMenuRequested.connect(self.on_resource_context_menu)
        self._loading_resources: set[FileResource] = set()
        self._loadRequestQueue: multiprocessing.Queue[Any] = multiprocessing.Queue()
        self._loadedTextureQueue: multiprocessing.Queue[Any] = multiprocessing.Queue()
        
        # Timer for polling the result queue from TextureLoaderProcess
        self._poll_timer: QTimer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_result_queue)
        # Map of (section_name, row) -> FileResource for pending process loads
        self._pending_process_loads: dict[tuple[str, int], FileResource] = {}

    def __del__(self):
        """Shutdown the executor when the texture list is deleted."""
        print("Shutting down executor in TextureList destructor")
        
        # Stop the poll timer
        poll_timer: QTimer | None = getattr(self, "_poll_timer", None)
        if poll_timer is not None:
            with contextlib.suppress(Exception):
                poll_timer.stop()
        
        self._executor.shutdown(wait=False)
        loader: multiprocessing.Process | None = getattr(self, "_loader", None)
        if loader is not None:
            try:
                if hasattr(loader, "request_shutdown"):
                    loader.request_shutdown()
                loader.terminate()
            except Exception:  # noqa: BLE001
                RobustLogger().exception("Failed to terminate texture loader process during cleanup")
            self._loader = None
        with contextlib.suppress(Exception):
            self._loadRequestQueue.close()
            self._loadRequestQueue.join_thread()
        with contextlib.suppress(Exception):
            self._loadedTextureQueue.close()
            self._loadedTextureQueue.join_thread()

    def setup_signals(self):
        """Setup the signals for the texture list."""
        print("Setting up signals for TextureList")
        self.ui.searchEdit.textChanged.connect(self.on_filter_string_updated)
        self.ui.sectionCombo.currentIndexChanged.connect(self.on_section_changed)
        self.ui.resourceList.doubleClicked.connect(self.on_resource_double_clicked)
        self.ui.reloadButton.clicked.connect(self.on_reload_clicked)
        self.ui.refreshButton.clicked.connect(self.on_refresh_clicked)

        vert_scroll_bar: QScrollBar | None = self.ui.resourceList.verticalScrollBar()  # pyright: ignore[reportAssignmentType]
        if vert_scroll_bar is None:
            RobustLogger().warning("Could not find vertical scroll bar for resource list")
        else:
            vert_scroll_bar.valueChanged.connect(self.queue_load_visible_icons)
        self.sig_icon_loaded.connect(self.on_icon_loaded)

    def set_installation(self, installation: HTInstallation):
        """Set the installation for the resource list."""
        self._installation = installation
        
        # Stop poll timer and terminate old loader if exists
        self._poll_timer.stop()
        loader: multiprocessing.Process | None = getattr(self, "_loader", None)
        if loader is not None:
            if hasattr(loader, "request_shutdown"):
                loader.request_shutdown()
            loader.terminate()
            self._loader = None
        
        # Clear pending loads when switching installations
        self._pending_process_loads.clear()
        
        if TextureLoaderProcess is None:
            RobustLogger().warning("TextureLoaderProcess is unavailable; texture loading will run on the main process via ProcessPoolExecutor")
            return
            
        # Start new loader process with installation path
        if installation is not None:
            try:
                self._loader = TextureLoaderProcess(
                    str(installation.path()),
                    installation.tsl,
                    self._loadRequestQueue,
                    self._loadedTextureQueue
                )
                self._loader.start()
                # Start polling for results at 60Hz (every ~16ms)
                self._poll_timer.start(16)
                RobustLogger().info(f"Started TextureLoader process for installation: {installation.path()}")
            except PermissionError as perm_exc:
                RobustLogger().exception(f"Permission error starting TextureLoader process: {perm_exc}")
                RobustLogger().error("This is a Windows multiprocessing issue. Try running the application as administrator.")
                self._loader = None
            except Exception as start_exc:
                RobustLogger().exception(f"Failed to start TextureLoader process: {start_exc}")
                self._loader = None

    def selected_resources(self) -> list[FileResource]:
        """Get the user selected resources from the texture list."""
        print("Getting selected resources from TextureList")
        resources: list[FileResource] = []
        current_section_name: str = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        print(f"Current section: {current_section_name}")
        cur_src_model: QStandardItemModel = self.texture_source_models[current_section_name]

        for index in self.ui.resourceList.selectedIndexes():
            source_index: QModelIndex = self.textures_proxy_model.mapToSource(index)
            if not source_index.isValid():
                RobustLogger().warning(f"Invalid source index for row {source_index.row()}")
                continue
            item: QStandardItem | None = cur_src_model.itemFromIndex(source_index)
            if item is None:
                RobustLogger().warning(f"No item found for row {source_index.row()}")
                continue
            if not isinstance(item, ResourceStandardItem):
                RobustLogger().warning(f"Expected ResourceStandardItem, got {item.__class__.__name__}")
                continue
            resource: QStandardItem | None = item.data(Qt.ItemDataRole.UserRole + 1)
            if not isinstance(resource, FileResource):
                RobustLogger().warning(f"Expected FileResource, got {resource.__class__.__name__}")
                continue
            resources.append(resource)

        print(f"Selected resources: {resources}")
        return resources

    def visible_indexes(self) -> list[QModelIndex]:
        """Get the visible source indexes visible on the viewport."""
        view: RobustListView = self.ui.resourceList
        if not view.isVisible() or self.textures_proxy_model.rowCount() == 0:
            print("View is not visible or model is empty")
            return []

        visible_rect: QRect = view.viewport().rect()  # pyright: ignore[reportOptionalMemberAccess]
        visible_indexes: list[QModelIndex] = []
        for row in range(self.textures_proxy_model.rowCount()):
            proxy_index: QModelIndex = self.textures_proxy_model.index(row, 0)
            if not proxy_index.isValid():
                RobustLogger().warning(f"Invalid proxy index for row {row}")
                continue
            if not view.visualRect(proxy_index).intersects(visible_rect):  # pyright: ignore[reportArgumentType]
                continue
            src_index: QModelIndex = self.textures_proxy_model.mapToSource(proxy_index)  # pyright: ignore[reportArgumentType]
            if not src_index.isValid():
                RobustLogger().warning(f"Invalid source index for row {row}")
                continue
            visible_indexes.append(src_index)

        return visible_indexes

    def set_sections(self, items: list[QStandardItem]):
        """Set the sections to be displayed in the texture list combobox."""
        print(f"Setting sections for TextureList with {len(items)} items")
        current_sections: set[str] = {self.ui.sectionCombo.itemData(i, Qt.ItemDataRole.UserRole) for i in range(self.ui.sectionCombo.count())}
        new_sections: set[str] = {item.data(Qt.ItemDataRole.UserRole) for item in items}

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
        print(f"Current section: '{current_section_name}'")
        current_source_model: QStandardItemModel = self.texture_source_models[current_section_name]
        current_source_model.clear()

        added_count = 0
        for resource in resources:
            resname, restype = resource.resname(), resource.restype()
            if restype not in (ResourceType.TGA, ResourceType.TPC):
                continue
            item = ResourceStandardItem(resname, resource=resource)
            item.setData(resource, Qt.ItemDataRole.UserRole + 1)
            item.setIcon(QIcon(QPixmap.fromImage(self.BLANK_IMAGE)))
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
        if not self.isVisible():
            return
        self.on_reload_clicked()  # FIXME: models are forgetting their items' icons for some reason.

    def on_filter_string_updated(self):
        self.textures_proxy_model.setFilterFixedString(self.ui.searchEdit.text())

    def on_resource_context_menu(self, position: QPoint):
        """Show the context menu for the texture list."""
        print(f"Showing context menu at position: {position}")
        menu: _QMenu = QMenu(self)
        menu.addAction("Open in Editor").triggered.connect(self.on_resource_double_clicked)
        menu.addAction("Reload").triggered.connect(self.on_reload_selected)

        export_submenu: _QMenu = QMenu("Export texture as...", menu)
        menu.addMenu(export_submenu)

        for tpc_format in TPCTextureFormat:

            def export_texture_wrapper(_checked, f=tpc_format):
                return self.export_texture(f)

            export_submenu.addAction(tpc_format.name).triggered.connect(export_texture_wrapper)

        menu.exec(self.ui.resourceList.mapToGlobal(position))  # pyright: ignore[reportArgumentType, reportCallIssue]

    def export_texture(self, target_format: TPCTextureFormat):
        selected_items: list[ResourceStandardItem] = self._get_selected_items()
        if len(selected_items) > 1:
            folder_path = QFileDialog.getExistingDirectory(self, "Select Export Folder")
            if not folder_path or not folder_path.strip():
                return
            folderpath = Path(folder_path)
            target_restype: ResourceType = ResourceType.__members__[
                str(
                    QInputDialog.getItem(
                        self,
                        "Export Texture",
                        "Select Target Format",
                        (ResourceType.TPC.name,)
                        if target_format.is_dxt()
                        else (
                            ResourceType.TGA.name,
                            ResourceType.TPC.name,
                        ),
                        0,
                    )[0]
                )
            ]
        else:
            file_filter = "TPC Files (*.tpc);;All Files (*)" if target_format.is_dxt() else "TGA Files (*.tga);;TPC Files (*.tpc);;All Files (*)"
            filepath, _ = QFileDialog.getSaveFileName(self, "Export Texture", "", file_filter)
            if not filepath or not filepath.strip():
                return
            folderpath = Path(filepath).parent
            target_restype = ResourceType.TGA if filepath.endswith(".tga") else ResourceType.TPC
        for item in selected_items:
            orig_tpc: TPC = read_tpc(item.resource.data())
            tpc: TPC = orig_tpc.copy()
            tpc.convert(target_format)
            write_tpc(tpc, folderpath / f"{item.resource.resname()}{target_restype.extension}", target_restype)

    def on_reload_selected(self):
        """Handle reloading selected textures."""
        print("Reloading selected textures")
        selected_items: list[ResourceStandardItem] = self._get_selected_items()
        for item in selected_items:
            self.offload_texture_load(item, reload=True)

    def _get_selected_items(self) -> list[ResourceStandardItem]:
        selected_indexes: list[QModelIndex] = self.ui.resourceList.selectedIndexes()
        section_name: str = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        selected_items: list[ResourceStandardItem] = []

        for proxy_index in selected_indexes:
            source_index: QModelIndex = self.textures_proxy_model.mapToSource(proxy_index)  # pyright: ignore[reportArgumentType]
            if not source_index.isValid():
                continue
            item: QStandardItem | None = self.texture_source_models[section_name].itemFromIndex(source_index)
            if item is None or not isinstance(item, ResourceStandardItem):
                RobustLogger().warning(f"Expected ResourceStandardItem, got {type(item).__name__}")
                continue
            selected_items.append(item)

        return selected_items

    def _process_all_items(self, *, reload: bool):
        cur_section_name: str = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        cur_src_model: QStandardItemModel = self.texture_source_models[cur_section_name]
        for row in range(self.textures_proxy_model.rowCount()):
            proxy_index: QModelIndex = self.textures_proxy_model.index(row, 0)
            if not proxy_index.isValid():
                RobustLogger().warning(f"Could not find item in the proxy model for row {row}")
                continue
            src_index: QModelIndex = self.textures_proxy_model.mapToSource(proxy_index)  # pyright: ignore[reportArgumentType]
            if not src_index.isValid():
                RobustLogger().warning(f"Could not find item in the src model for row {row}")
                continue
            item: QStandardItem | None = cur_src_model.itemFromIndex(src_index)
            if item is None or not isinstance(item, ResourceStandardItem):
                RobustLogger().warning(f"Expected ResourceStandardItem, got {type(item).__name__}")
                continue
            self.offload_texture_load(item, reload=reload)

    def queue_load_visible_icons(self):
        """Queue the loading of icons for visible items."""
        visible_indexes: list[QModelIndex] = self.visible_indexes()
        if not visible_indexes:
            return
        section_name: str = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        cur_src_model: QStandardItemModel = self.texture_source_models[section_name]
        for index in visible_indexes:
            item: QStandardItem | None = cur_src_model.itemFromIndex(index)
            if item is None:
                RobustLogger().warning(f"No item found for row {index.row()}")
                continue
            if not isinstance(item, ResourceStandardItem):
                RobustLogger().warning(f"Expected ResourceStandardItem, got {type(item).__name__}")
                continue
            self.offload_texture_load(item, reload=False)

    def offload_texture_load(
        self,
        item: QStandardItem,
        icon_size: int = 64,
        *,
        reload: bool = False,
    ):
        """Queue the loading of an icon for a given item."""
        assert isinstance(item, ResourceStandardItem), f"Expected ResourceStandardItem, got {type(item).__name__}"
        if reload:
            self._loading_resources.discard(item.resource)
        if item.resource in self._loading_resources:
            return
        self._loading_resources.add(item.resource)

        section_name: str = self.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        row: int = item.row()
        context = (section_name, row)
        
        # Use TextureLoaderProcess if available and running
        if self._loader is not None and self._loader.is_alive():
            try:
                # Send request to the loader process
                resref = item.resource.resname()
                restype = item.resource.restype()
                self._loadRequestQueue.put_nowait((resref, restype, context, icon_size))
                self._pending_process_loads[context] = item.resource
                return
            except Exception as e:
                RobustLogger().warning(f"Failed to queue texture load request: {e}, falling back to executor")
        
        # Fall back to ProcessPoolExecutor
        try:
            future: Future[tuple[tuple[str, int], TPCMipmap]] = self._executor.submit(get_image_from_resource, context, item.resource, icon_size)
        except BrokenProcessPool as e:
            RobustLogger().error("Broken process pool, recreating...", exc_info=e)
            self._executor = ProcessPoolExecutor(max_workers=multiprocessing.cpu_count())
            future = self._executor.submit(get_image_from_resource, context, item.resource, icon_size)
        future.add_done_callback(self.sig_icon_loaded.emit)

    def _poll_result_queue(self):
        """Poll the result queue for completed texture loads from TextureLoaderProcess."""
        if deserialize_mipmap is None:
            return
            
        # Process up to 10 results per poll to avoid blocking the UI
        for _ in range(10):
            try:
                result = self._loadedTextureQueue.get_nowait()
                context, mipmap_data, error = result
                
                # Remove from pending loads
                resource = self._pending_process_loads.pop(context, None)
                if resource is not None:
                    self._loading_resources.discard(resource)
                
                if error is not None:
                    # Only log non-None errors (None means texture simply not found, which is expected)
                    RobustLogger().warning(f"Texture load error: {error}")
                    continue
                    
                if mipmap_data is None:
                    continue
                
                # Deserialize the mipmap
                try:
                    mipmap = deserialize_mipmap(mipmap_data)
                except Exception as e:
                    RobustLogger().warning(f"Failed to deserialize mipmap: {e}")
                    continue
                
                # Update the icon
                section_name, row = context
                src_index: QModelIndex = self.texture_source_models[section_name].index(row, 0)
                if not src_index.isValid():
                    continue
                    
                item: QStandardItem | None = self.texture_source_models[section_name].itemFromIndex(src_index)
                if item is None:
                    continue
                
                image: QImage = mipmap.to_qimage()
                y_flipped_image: QPixmap = QPixmap.fromImage(image.mirrored(False, True))
                pixmap: QPixmap = y_flipped_image.scaled(
                    self.ui.resourceList.iconSize(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                item.setIcon(QIcon(pixmap))
                
            except Exception:
                # Queue is empty or other error, stop polling this cycle
                break

    def on_reload_clicked(self):
        """Handle the reload button click."""
        self._process_all_items(reload=True)

    def on_refresh_clicked(self):
        """Handle the refresh button click."""
        self._process_all_items(reload=False)

    @Slot(Future)
    def on_icon_loaded(
        self,
        future: Future[tuple[tuple[str, int], TPCMipmap]],
    ):
        """Handle the completion of an icon load."""
        # print("Icon loaded callback triggered")
        item_context, tpc_mipmap = future.result()
        section_name, row = item_context
        # print(f"Loaded icon for section: {section_name}, row: {row}")
        src_index: QModelIndex = self.texture_source_models[section_name].index(row, 0)
        if not src_index.isValid():
            RobustLogger().warning("Invalid source index for row {row}")
            return
        item: QStandardItem | None = self.texture_source_models[section_name].itemFromIndex(src_index)
        if item is None:
            RobustLogger().warning(f"No item found for row {row}")
            return
        image: QImage = tpc_mipmap.to_qimage()
        y_flipped_image: QPixmap = QPixmap.fromImage(image.mirrored(False, True))
        pixmap: QPixmap = y_flipped_image.scaled(
            self.ui.resourceList.iconSize(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        item.setIcon(QIcon(pixmap))

    @Slot()
    def on_resource_double_clicked(self):
        self.sig_request_open_resource.emit(self.selected_resources(), None)

    def resizeEvent(self, a0: QResizeEvent):  # pylint: disable=unused-argument,invalid-name  # pyright: ignore[reportIncompatibleMethodOverride]
        """Ensures icons that come into view are queued to load when the widget is resized."""
        QTimer.singleShot(0, self.queue_load_visible_icons)

    def showEvent(self, a0: QShowEvent):  # pylint: disable=unused-argument,invalid-name,  # pyright: ignore[reportIncompatibleMethodOverride]
        """Ensures icons that come into view are queued to load when the widget is shown."""
        QTimer.singleShot(0, self.queue_load_visible_icons)


T = TypeVar("T")


def get_image_from_tpc(resource: FileResource, icon_size: int) -> TPCMipmap:
    """Get an image from a TPC resource."""
    tpc: TPC = read_tpc(resource.data())
    tpc.decode()
    best_mipmap: TPCMipmap = next(
        (mipmap for mipmap in tpc.layers[0].mipmaps if mipmap.width <= icon_size and mipmap.height <= icon_size),
        tpc.layers[0].mipmaps[-1],
    )
    mm: TPCMipmap = best_mipmap
    assert mm.data
    assert mm.width
    assert mm.height
    assert mm.tpc_format not in (TPCTextureFormat.DXT1, TPCTextureFormat.DXT3, TPCTextureFormat.DXT5)
    return mm


def get_image_from_pillow(resource: FileResource, icon_size: int = 64) -> TPCMipmap:
    """Get an image using Pillow."""
    from PIL import Image

    with Image.open(BytesIO(resource.data())) as img:
        rgba_img: Image = img.convert("RGBA")
    return TPCMipmap(
        icon_size,
        icon_size,
        TPCTextureFormat.RGBA,
        bytearray(rgba_img.resize((icon_size, icon_size), Image.Resampling.BICUBIC).tobytes()),
    )


def get_image_from_qt(
    resource: FileResource,
    icon_size: int = 64,
) -> TPCMipmap:
    """Get an image using Qt."""
    from qtpy.QtGui import QImage  # pylint: disable=redefined-outer-name,reimported

    qimg = QImage()
    if not qimg.loadFromData(resource.data()):
        icon_provider: QFileIconProvider = QFileIconProvider()
        icon: QIcon = icon_provider.icon(QFileInfo(str(resource.filepath())))
        pixmap: QPixmap = icon.pixmap(icon_size, icon_size)
        qimg: QImage = pixmap.toImage()

    return qimg_to_tpc_get_result(qimg, icon_size)


def get_image_from_resource(
    context: T,
    resource: FileResource,
    icon_size: int = 64,
) -> tuple[T, TPCMipmap]:
    """Get an image from a resource."""
    if resource.restype() is ResourceType.TPC:
        return context, get_image_from_tpc(resource, icon_size)

    try:
        from PIL import Image

        if resource.restype().extension.lower() in Image.registered_extensions():
            return context, get_image_from_pillow(resource, icon_size)
    except ImportError:  # noqa: S110
        RobustLogger().warning(f"Pillow not available to load image data in resource: '{resource.path_ident()!r}'")

    try:
        from PIL import Image

        if resource.restype().extension.lower() not in {x.data().decode(errors="ignore").lower() for x in QImageReader.supportedImageFormats()}:
            RobustLogger().warning(f"Unsupported image format for resource: '{resource.path_ident()!r}'")
            return context, get_fallback_icon(icon_size)
        return context, get_image_from_qt(resource, icon_size)
    except ImportError:  # noqa: S110
        RobustLogger().warning(f"Qt not available to load image data in resource: '{resource.path_ident()!r}'")

    raise ValueError(f"No suitable image processing library available to load image data in resource: '{resource.path_ident()!r}'")


def qimg_to_tpc_get_result(qimg: QImage, icon_size: int = 64) -> TPCMipmap:
    tex_fmt = TPCTextureFormat.RGBA
    if qimg.format() == QImage.Format.Format_RGB888:
        tex_fmt = TPCTextureFormat.RGB
    elif qimg.format() != QImage.Format.Format_RGBA8888:
        qimg = qimg.convertToFormat(QImage.Format.Format_RGBA8888, Qt.ImageConversionFlag.AutoColor)
    if (icon_size < qimg.width() and icon_size < qimg.height()) or (icon_size > qimg.width() and icon_size > qimg.height()):
        qimg = qimg.scaled(icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    const_bits: voidptr | None = qimg.constBits()
    assert const_bits is not None
    return TPCMipmap(icon_size, icon_size, tex_fmt, bytearray(const_bits.asarray(icon_size)))


def get_fallback_icon(icon_size: int = 64) -> TPCMipmap:
    app_style: QStyle | None = QApplication.style()
    assert app_style is not None
    pixmap: QPixmap = app_style.standardPixmap(QStyle.StandardPixmap.SP_VistaShield)
    qimg: QImage = pixmap.toImage()
    return qimg_to_tpc_get_result(qimg, icon_size)


def on_open_resources(
    resources: list[FileResource],
    resource_widget: ResourceList | TextureList,
    active: HTInstallation | None,
):
    """Open the given resources."""
    from pykotor.extract.file import ResourceIdentifier
    from toolset.utils.window import open_resource_editor

    for resource in resources:
        _filepath, _editor = open_resource_editor(resource, active, gff_specialized=GlobalSettings().gffSpecializedEditors)

    if resources or isinstance(resource_widget, TextureList):
        return
    filename: str = resource_widget.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)

    if not filename or not filename.strip() or not active:
        return
    erf_filepath: Path = active.module_path() / filename

    if not erf_filepath.exists() or not erf_filepath.is_file():
        return
    res_ident: ResourceIdentifier = ResourceIdentifier.from_path(erf_filepath)

    if not res_ident.restype:
        return
    erfrim_file_resource = FileResource(res_ident.resname, res_ident.restype, os.path.getsize(erf_filepath), 0x0, erf_filepath)  # noqa: PTH202
    _filepath, _editor = open_resource_editor(erfrim_file_resource, active, gff_specialized=GlobalSettings().gffSpecializedEditors)
