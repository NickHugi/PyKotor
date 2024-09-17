 from __future__ import annotations

import difflib
import fnmatch
import hashlib
import logging
import mimetypes
import os
import platform
import shutil
import subprocess
import sys
import zipfile

from collections import deque
from concurrent.futures import ProcessPoolExecutor
from contextlib import suppress
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, cast

import qtpy

from PyQt5.QtCore import QSortFilterProxyModel
from loggerplus import RobustLogger
from qtpy.QtCore import (
    QDir,
    QEvent,
    QFile,
    QFileInfo,
    QItemSelection,
    QItemSelectionModel,
    QMimeData,
    QModelIndex,
    QSettings,
    QSize,
    QStandardPaths,
    QTimer,
    QUrl,
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QCursor, QDesktopServices, QDrag, QGuiApplication, QIcon, QKeySequence, QWheelEvent
from qtpy.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QCompleter,
    QDialog,
    QDialogButtonBox,
    QDockWidget,
    QFileDialog,
    QFileIconProvider,
    QFileSystemModel,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListView,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QProgressBar,
    QProgressDialog,
    QPushButton,
    QShortcut,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QTableView,
    QTextEdit,
    QToolButton,
    QUndoStack,
    QVBoxLayout,
    QWidget,
)

from utility.ui_libraries.qt.filesystem.address_bar import PyQAddressBar
from utility.ui_libraries.qt.filesystem.file_explorer_context_menu import FileExplorerContextMenu
from utility.ui_libraries.qt.filesystem.undo_commands import CopyCommand, DeleteCommand, MoveCommand, RenameCommand
from utility.ui_libraries.qt.widgets.itemviews.listview import RobustListView
from utility.ui_libraries.qt.widgets.itemviews.tableview import RobustTableView
from utility.ui_libraries.qt.widgets.itemviews.tileview import QTileView
from utility.ui_libraries.qt.widgets.itemviews.treeview import RobustTreeView

if TYPE_CHECKING:
    from concurrent.futures import Future

    from qtpy.QtCore import QObject, QPoint, QRect
    from qtpy.QtGui import QCloseEvent, QDragEnterEvent, QDropEvent, QKeyEvent, QMouseEvent, QResizeEvent
    from qtpy.QtWidgets import QWidget


class ViewMode(Enum):
    EXTRA_LARGE_ICONS = auto()
    LARGE_ICONS = auto()
    MEDIUM_ICONS = auto()
    SMALL_ICONS = auto()
    DETAILS = auto()
    LIST = auto()
    TILES = auto()
    CONTENT = auto()


class FirstColumnInteractableTableView(RobustTableView):
    def __init__(self, parent=None):
        super().__init__(parent)

    def setSelection(self, rect: QRect, command: QItemSelectionModel.SelectionFlags):
        index = self.indexAt(rect.topLeft())
        if index.isValid() and index.column() == 0:
            # Only allow selection if the click is in the first column
            super().setSelection(rect, command)
        else:
            # Clear selection if click is outside the first column
            self.clearSelection()

    def mousePressEvent(self, event: QMouseEvent):
        index = self.indexAt(event.pos())
        if index.isValid() and index.column() == 0:
            super().mousePressEvent(event)
        else:
            # Clear selection and reset the selection anchor
            self.clearSelection()

    def mouseReleaseEvent(self, event: QMouseEvent):
        index = self.indexAt(event.pos())
        if index.isValid() and index.column() == 0:
            super().mouseReleaseEvent(event)
        else:
            event.ignore()

    def clearSelection(self):
        self.selectionModel().clear()
        self.selectionModel().reset()
        self.selectionModel().setCurrentIndex(QModelIndex(), QItemSelectionModel.Clear)
        self.selectionModel().select(QModelIndex(), QItemSelectionModel.Clear | QItemSelectionModel.Rows)


class MergedFileExplorer(QFileDialog):
    fileSelected: Signal = Signal(str)
    filesSelected: Signal = Signal(list)
    currentChanged: Signal = Signal(str)
    directoryEntered: Signal = Signal(str)
    filterSelected: Signal = Signal(str)
    urlsSelected: Signal = Signal(list)

    def __init__(
        self,
        parent: QWidget | None = None,
        caption: str = "",
        directory: str = "",
        file_filter: str = "",
        initial_filter: str = "",
        options: QFileDialog.Options | None = None,
    ):
        super().__init__(parent, caption, directory, file_filter)
        if qtpy.API_NAME == "PyQt5":
            from utility.ui_libraries.qt.uic.pyqt5.filesystem.file_system_explorer_widget import Ui_FileSystemExplorerWidget
        elif qtpy.API_NAME == "PySide6":
            from utility.ui_libraries.qt.uic.pyside6.filesystem.file_system_explorer_widget import Ui_FileSystemExplorerWidget
        elif qtpy.API_NAME == "PySide2":
            from utility.ui_libraries.qt.uic.pyside2.filesystem.file_system_explorer_widget import Ui_FileSystemExplorerWidget
        elif qtpy.API_NAME == "PyQt6":
            from utility.ui_libraries.qt.uic.pyqt6.filesystem.file_system_explorer_widget import Ui_FileSystemExplorerWidget
        else:
            raise ImportError(f"Unsupported Qt API: {qtpy.API_NAME}")

        self.ui = Ui_FileSystemExplorerWidget()
        self.ui.setupUi(self)
        self.resize(800, 600)
        self.setSizeGripEnabled(True)

        self._options: QFileDialog.Option | QFileDialog.Options = QFileDialog.Options() if options is None else options
        self._fileMode: QFileDialog.FileMode | int = QFileDialog.FileMode.AnyFile
        self._acceptMode: QFileDialog.AcceptMode | int = QFileDialog.AcceptMode.AcceptOpen
        self._viewMode: QFileDialog.ViewMode | int = QFileDialog.ViewMode.Detail
        self._currentPath: str = QDir.homePath()
        self._selectedFiles: list[str] = []
        self._nameFilters: list[str] = []
        self.mime_type_filters: list[str] = []
        self.default_suffix: str = ""
        self._sidebar_urls: list[QUrl] = []
        self.tabs: list[QWidget] = []
        self.recent_directories: deque[str] = deque(maxlen=10)
        self.settings = QSettings("QtCustomWidgets", "MergedFileExplorer")
        self.file_operation_queue: list[tuple[Callable[[], Any], Callable[[Exception], Any] | None]] = []
        self.process_pool = ProcessPoolExecutor(max_workers=min(4, (os.cpu_count() or 1)))
        self.lazy_load_batch_size: int = 100

        self.current_path: Path = Path.home()
        self.navigation_history: list[Path] = []
        self.navigation_index: int = -1
        self.clipboard = QApplication.clipboard()
        self.undo_stack = QUndoStack(self)

        self.setup_ui(caption)
        self.setup_menu()
        self.setup_connections()

        self.fileSystemModel: QFileSystemModel = QFileSystemModel(self)
        self.fileSystemModel.setIconProvider(QFileIconProvider())
        self.fileSystemModel.setOption(QFileSystemModel.Option.DontWatchForChanges)
        self.setup_sidebar()

        self.setup_logging()

        self.setDirectory(directory or QDir.homePath())
        if file_filter:
            self.setNameFilters(file_filter.split(";;"))
        if initial_filter and initial_filter.strip() and initial_filter not in self.nameFilters():
            self.setNameFilter(initial_filter)

        self._history = []

        self.setup_file_operations()

        # Setup progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        self.ui.status_bar.addPermanentWidget(self.progress_bar)

        # Setup COM interfaces for Windows
        if platform.system() == "Windows":
            self.setup_com_interfaces()

        # Setup context menu handler
        self.context_menu_handler = FileExplorerContextMenu(self)

        # Setup custom icon provider
        self.icon_provider = QFileIconProvider()
        self.fileSystemModel.setIconProvider(self.icon_provider)

        # Setup file watcher
        self.fileSystemModel.setReadOnly(False)
        self.fileSystemModel.setOption(QFileSystemModel.DontWatchForChanges, False)

    def setup_com_interfaces(self):
        with suppress(ImportError):
            self.setup_com_interfaces_comtypes()
            return
        with suppress(ImportError):
            self.setup_com_interfaces_pywin32()
            return
        RobustLogger().warning("Neither comtypes nor pywin32 is available. COM interfaces will not be used.")

    def setup_com_interfaces_comtypes(self):
        import comtypes.client as cc  # pyright: ignore[reportMissingTypeStubs]

        self.shell = cc.CreateObject("Shell.Application")

    def setup_com_interfaces_pywin32(self):
        import win32com.client

        self.shell = win32com.client.Dispatch("Shell.Application")

    def setup_ui(self, caption: str):
        self.setWindowTitle(caption or "Select File")

        # Setup address bar
        self.address_bar: PyQAddressBar = PyQAddressBar()
        self.ui.toolbar_widget.layout().insertWidget(7, self.address_bar)

        # Setup views
        self.setup_views()

        # Setup completer
        self.completer: QCompleter = QCompleter(self)
        self.completer.setModel(self.fileSystemModel)
        self.ui.address_bar.setCompleter(self.completer)

        # Setup icon sizes
        self.base_icon_size: int = 16
        self.icon_size: int = self.base_icon_size
        self.icon_size_multiplier: float = 1.1
        self.details_max_multiplier: float = 1.5
        self.list_max_multiplier: float = 4.0
        self.view_transition_multiplier: float = 1.0417
        self.list_min_multiplier: float = self.details_max_multiplier * self.view_transition_multiplier
        self.tiles_min_multiplier: float = self.list_max_multiplier * self.view_transition_multiplier
        self.minimum_multiplier: float = 1.0
        self.maximum_multiplier: float = 16.0

        # Setup splitter
        self.splitter: QSplitter = self.ui.splitter

        # Setup stacked widget
        self.stacked_widget: QStackedWidget = QStackedWidget()
        self.splitter.replaceWidget(1, self.stacked_widget)

        # Add views to stacked widget
        self.stacked_widget.addWidget(self.ui.file_list_view)
        self.stacked_widget.addWidget(self.table_view)
        self.stacked_widget.addWidget(self.tiles_view)

        # Set current view
        self.current_view: ViewMode = ViewMode.DETAILS
        self.stacked_widget.setCurrentWidget(self.table_view)

    def setup_views(self):
        self.list_view: RobustListView = self.ui.file_list_view
        self.table_view: FirstColumnInteractableTableView = FirstColumnInteractableTableView()
        self.tiles_view: QTileView = QTileView()
        self.preview_view: QLabel = QLabel()

        for view in (self.list_view, self.table_view, self.tiles_view):
            view.setModel(self.fileSystemModel)
            view.setRootIndex(self.fileSystemModel.index(str(self.current_path)))
            view.doubleClicked.connect(self.on_item_double_clicked)
            view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            view.customContextMenuRequested.connect(self.show_context_menu)
            view.viewport().installEventFilter(self)

        self.list_view.setViewMode(QListView.ViewMode.ListMode)
        self.list_view.setResizeMode(QListView.ResizeMode.Adjust)
        self.list_view.setWrapping(False)
        self.list_view.setUniformItemSizes(True)

        self.table_view.horizontalHeader().setVisible(False)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setShowGrid(False)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)
        self.table_view.setColumnWidth(0, 200)
        self.table_view.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)

        self.ui.navigation_pane.setModel(self.fileSystemModel)
        self.ui.navigation_pane.setRootIndex(self.fileSystemModel.index(""))
        self.ui.navigation_pane.expandToDepth(0)
        self.ui.navigation_pane.setHeaderHidden(True)
        self.ui.navigation_pane.clicked.connect(self.on_tree_view_clicked)

        for i in range(1, self.fileSystemModel.columnCount()):
            self.ui.navigation_pane.hideColumn(i)

    def setup_menu(self):
        self.ui.menu_file.addAction("New Folder", self.create_new_folder, QKeySequence.StandardKey.New)
        self.ui.menu_file.addAction("Open", self.open, QKeySequence.StandardKey.Open)
        self.ui.menu_file.addAction("Delete", self.delete_file, QKeySequence.StandardKey.Delete)

        self.ui.menu_edit.addAction("Cut", self.cut_file, QKeySequence.StandardKey.Cut)
        self.ui.menu_edit.addAction("Copy", self.copy_file, QKeySequence.StandardKey.Copy)
        self.ui.menu_edit.addAction("Paste", self.paste_file, QKeySequence.StandardKey.Paste)

        self.ui.menu_view.addAction("Refresh", self.refresh_view, QKeySequence.StandardKey.Refresh)
        self.ui.menu_view.addAction("Disk Usage", self.show_disk_usage)
        self.ui.menu_view.addAction("Secure Delete", self.secure_delete)

    def setup_connections(self):
        self.ui.back_button.clicked.connect(self.go_back)
        self.ui.forward_button.clicked.connect(self.go_forward)
        self.ui.up_button.clicked.connect(self.go_up)
        self.ui.go_button.clicked.connect(self.on_go_button_clicked)
        self.ui.search_bar.textChanged.connect(self.on_search_text_changed)

        self.address_bar.path_changed.connect(self.on_address_bar_path_changed)
        self.fileSystemModel.directoryLoaded.connect(self.on_directory_loaded)

        for view in [self.list_view, self.table_view, self.tiles_view]:
            view.selectionModel().selectionChanged.connect(self.on_selection_changed)

        self.ui.action_new_window.triggered.connect(self.new_window)
        self.ui.action_open_windows_terminal.triggered.connect(self.open_windows_terminal)
        self.ui.action_close.triggered.connect(self.close)
        self.ui.action_properties.triggered.connect(self.show_properties)

        self.ui.action_refresh.triggered.connect(self.refresh_view)
        self.ui.action_list.triggered.connect(lambda: self.change_view_mode(ViewMode.LIST))
        self.ui.action_details.triggered.connect(lambda: self.change_view_mode(ViewMode.DETAILS))
        self.ui.action_tiles.triggered.connect(lambda: self.change_view_mode(ViewMode.TILES))
        self.ui.action_show_hidden_items.triggered.connect(self.toggle_hidden_items)

    def setup_file_operations(self):
        self.file_operation_queue.clear()
        QTimer.singleShot(0, self.process_file_operations)

    def setup_logging(self, log_file: str = "merged_file_explorer.log"):
        logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", filemode="w")
        logging.getLogger().addHandler(logging.StreamHandler())
        logging.getLogger().setLevel(logging.INFO)
        self.logger = logging.getLogger(__name__)

    def setup_sidebar(self):
        self._sidebarUrls: list[QUrl] = [
            QUrl.fromLocalFile(QDir.homePath()),
            QUrl.fromLocalFile(QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)),
            QUrl.fromLocalFile(QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)),
            QUrl.fromLocalFile(QDir.rootPath()),
        ] + [QUrl.fromLocalFile(path) for path in QStandardPaths.standardLocations(QStandardPaths.MusicLocation)]
        self.update_sidebar()

    def update_sidebar(self):
        self.ui.navigation_pane.blockSignals(True)
        for url in self.sidebarUrls():
            index = self.fileSystemModel.index(url.toLocalFile())
            if index.isValid():
                self.ui.navigation_pane.setCurrentIndex(index)
                self.ui.navigation_pane.scrollTo(index)
            self.ui.navigation_pane.setExpanded(index, True)
        self.ui.navigation_pane.blockSignals(False)

    def on_selection_changed(self, selected: QItemSelection, deselected: QItemSelection):
        selected_indexes = selected.indexes()
        if selected_indexes:
            file_path = self.fileSystemModel.filePath(selected_indexes[0])
            self.ui.address_bar.setText(QFileInfo(file_path).fileName())
            if len(selected_indexes) == 1:
                self.fileSelected.emit(file_path)
            self.filesSelected.emit([self.fileSystemModel.filePath(index) for index in selected_indexes])
        else:
            self.ui.address_bar.clear()
            self.fileSelected.emit("")
            self.filesSelected.emit([])

    def on_item_double_clicked(self, index: QModelIndex):
        path = Path(self.fileSystemModel.filePath(index))
        if path.is_dir():
            self.set_current_path(path)
        else:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def on_tree_view_clicked(self, index: QModelIndex):
        path = Path(self.fileSystemModel.filePath(index))
        self.set_current_path(path)

    def on_go_button_clicked(self):
        path = self.ui.address_bar.text()
        self.set_current_path(path)

    def on_search_text_changed(self, text: str):
        proxy_model = QSortFilterProxyModel(self)
        proxy_model.setSourceModel(self.fileSystemModel)
        proxy_model.setFilterRegExp(text)
        proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.list_view.setModel(proxy_model)
        self.table_view.setModel(proxy_model)
        self.tiles_view.setModel(proxy_model)

    def on_address_bar_path_changed(self, path: Path):
        self.setDirectory(str(path))

    def on_directory_loaded(self, path: str):
        loaded_path = Path(path)
        if loaded_path == self.current_path:
            self.update_address_bar(loaded_path)

    def setDirectory(self, directory: str):
        path_obj = Path(directory)
        if path_obj.is_dir():
            self._currentPath = str(path_obj)
            index = self.fileSystemModel.index(self._currentPath)
            self.list_view.setRootIndex(index)
            self.table_view.setRootIndex(index)
            self.tiles_view.setRootIndex(index)
            self.ui.navigation_pane.setCurrentIndex(index)
            self.address_bar.setText(self._currentPath)
            self.directoryEntered.emit(self._currentPath)
            self.add_to_history(path_obj)
            self.update_ui()
        else:
            self.address_bar.setText(self._currentPath)

    def directory(self) -> str:
        return self._currentPath

    def add_to_history(self, path: Path):
        if self.navigation_index < len(self.navigation_history) - 1:
            self.navigation_history = self.navigation_history[: self.navigation_index + 1]
        self.navigation_history.append(path)
        self.navigation_index = len(self.navigation_history) - 1

    def go_back(self):
        if self.navigation_index > 0:
            self.navigation_index -= 1
            self.set_current_path(self.navigation_history[self.navigation_index])

    def go_forward(self):
        if self.navigation_index < len(self.navigation_history) - 1:
            self.navigation_index += 1
            self.set_current_path(self.navigation_history[self.navigation_index])

    def go_up(self):
        parent_path = self.current_path.parent
        if parent_path != self.current_path:
            self.set_current_path(parent_path)

    def refresh_view(self):
        self.set_current_path(self.current_path)

    def update_ui(self):
        self.update_status_bar()
        self.ui.back_button.setEnabled(self.navigation_index > 0)
        self.ui.forward_button.setEnabled(self.navigation_index < len(self.navigation_history) - 1)
        self.ui.up_button.setEnabled(self.current_path != Path(QDir.rootPath()))

    def update_status_bar(self):
        selected_items = len(self.list_view.selectedIndexes())
        total_items = self.fileSystemModel.rowCount(self.list_view.rootIndex())
        if selected_items > 0:
            status_text = f"{selected_items} item{'s' if selected_items > 1 else ''} selected"
        else:
            status_text = f"{total_items} item{'s' if total_items > 1 else ''}"
        self.ui.status_items.setText(status_text)

        total_size = sum(self.fileSystemModel.size(self.fileSystemModel.index(i, 0, self.list_view.rootIndex())) for i in range(total_items))
        self.ui.status_size.setText(self.format_size(total_size))

    def format_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def new_window(self):
        new_window = MergedFileExplorer()
        new_window.show()

    def open_windows_terminal(self):
        subprocess.Popen(f'start cmd /K "cd /d {self.current_path}"', shell=True)

    def show_properties(self):
        selected_indexes = self.list_view.selectedIndexes()
        if selected_indexes:
            file_path = Path(self.fileSystemModel.filePath(selected_indexes[0]))
            properties = f"Name: {file_path.name}\n"
            properties += f"Type: {'Directory' if file_path.is_dir() else 'File'}\n"
            properties += f"Size: {self.format_size(file_path.stat().st_size)}\n"
            properties += f"Created: {file_path.stat().st_ctime}\n"
            properties += f"Modified: {file_path.stat().st_mtime}\n"
            properties += f"Accessed: {file_path.stat().st_atime}\n"

            QMessageBox.information(self, "Properties", properties)

    def cut_file(self):
        self.copy_file(cut=True)

    def copy_file(self, cut: bool = False):
        selected_indexes = self.list_view.selectedIndexes()
        if selected_indexes:
            source_paths = [Path(self.fileSystemModel.filePath(index)) for index in selected_indexes]
            mime_data = QMimeData()
            urls = [QUrl.fromLocalFile(str(path)) for path in source_paths]
            mime_data.setUrls(urls)
            self.clipboard.setMimeData(mime_data)

            if cut:
                self.to_cut = source_paths
            else:
                self.to_cut = None

    def paste_file(self):
        mime_data = self.clipboard.mimeData()
        if mime_data.hasUrls():
            source_paths = [Path(url.toLocalFile()) for url in mime_data.urls()]
            destination_path = self.current_path

            if hasattr(self, "to_cut") and self.to_cut:
                command = MoveCommand(source_paths, destination_path)
            else:
                command = CopyCommand(source_paths, destination_path)

            self.undo_stack.push(command)
            self.refresh_view()

            if hasattr(self, "to_cut"):
                self.to_cut = None

    def delete_file(self):
        selected_indexes = self.list_view.selectedIndexes()
        if selected_indexes:
            paths = [Path(self.fileSystemModel.filePath(index)) for index in selected_indexes]
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete {len(paths)} item(s)?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                command = DeleteCommand(paths)
                self.undo_stack.push(command)
                self.refresh_view()

    def rename_file(self):
        selected_indexes = self.list_view.selectedIndexes()
        if selected_indexes:
            file_path = Path(self.fileSystemModel.filePath(selected_indexes[0]))
            new_name, ok = QInputDialog.getText(self, "Rename", "Enter new name:", QLineEdit.Normal, file_path.name)
            if ok and new_name:
                new_path = file_path.with_name(new_name)
                if new_path.exists():
                    QMessageBox.warning(self, "Rename", "A file with this name already exists.")
                else:
                    command = RenameCommand(file_path, new_path)
                    self.undo_stack.push(command)
                    self.refresh_view()

    def run_in_background(
        self,
        func: Callable,
        *args,
        callback: Callable[[Future[Any]], None] | None = None,
        **kwargs,
    ):
        future = self.process_pool.submit(func, *args, **kwargs)
        if callback is not None:
            future.add_done_callback(callback)

    def update_progress(self, value: int):
        self.progress_bar.setValue(value)
        if value >= 100:
            self.progress_bar.setVisible(False)
        elif not self.progress_bar.isVisible():
            self.progress_bar.setVisible(True)

    def create_new_folder(self):
        new_folder_name, ok = QInputDialog.getText(self, "Create New Folder", "Folder name:")
        if ok and new_folder_name:
            new_folder_path = self.current_path / new_folder_name
            try:
                new_folder_path.mkdir(parents=True, exist_ok=True)
                self.refresh_view()
                self.logger.info(f"Created new folder: {new_folder_path}")
            except OSError:
                self.logger.exception("Failed to create folder")
                QMessageBox.warning(self, "Error", "Failed to create folder")

    def show_context_menu(self, pos: QPoint):
        sender = self.sender()
        assert isinstance(sender, QAbstractItemView)
        global_pos = sender.mapToGlobal(pos)
        index = sender.indexAt(pos)

        menu = QMenu(self)
        open_action = menu.addAction("Open")
        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")
        compress_action = menu.addAction("Compress")
        extract_action = menu.addAction("Extract")
        properties_action = menu.addAction("Properties")
        calculate_checksum_action = menu.addAction("Calculate Checksum")
        compare_files_action = menu.addAction("Compare Files")
        secure_delete_action = menu.addAction("Secure Delete")

        action = menu.exec_(global_pos)

        file_path = self.fileSystemModel.filePath(index)

        if action == open_action:
            self.on_item_double_clicked(index)
        elif action == rename_action:
            self.rename_file()
        elif action == delete_action:
            self.delete_file()
        elif action == compress_action:
            self.compress_file(file_path)
        elif action == extract_action:
            self.extract_file(file_path)
        elif action == properties_action:
            self.show_file_properties(file_path)
        elif action == calculate_checksum_action:
            self.calculate_checksum(file_path)
        elif action == compare_files_action:
            self.compare_files()
        elif action == secure_delete_action:
            self.secure_delete(file_path)

    def compress_file(self, file_path: str):
        zip_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Zip File",
            os.path.dirname(file_path),
            "Zip Files (*.zip)",
        )
        if not zip_path or not zip_path.strip():
            return
        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                if os.path.isfile(file_path):
                    zipf.write(file_path, os.path.basename(file_path))
                else:
                    for root, _, files in os.walk(file_path):
                        for file in files:
                            zipf.write(
                                os.path.join(root, file),
                                os.path.relpath(
                                    os.path.join(root, file),
                                    os.path.join(file_path, ".."),
                                ),
                            )
                QMessageBox.information(self, "Success", f"File(s) compressed successfully to {zip_path}")
        except Exception as e:
            error_msg = f"Could not compress file(s): {e}"
            self.logger.exception(error_msg)
            QMessageBox.warning(self, "Error", error_msg)

    def extract_file(self, file_path: str):
        if not file_path.lower().endswith(".zip"):
            QMessageBox.warning(self, "Error", "Selected file is not a zip file")
            return
        extract_path = QFileDialog.getExistingDirectory(self, "Select Extraction Directory", os.path.dirname(file_path))
        if not extract_path or not extract_path.strip():
            return
        try:
            with zipfile.ZipFile(file_path, "r") as zipf:
                zipf.extractall(extract_path)
            QMessageBox.information(self, "Success", f"File(s) extracted successfully to {extract_path}")
        except Exception as e:
            error_msg = f"Could not extract file(s): {e}"
            self.logger.exception(error_msg)
            QMessageBox.warning(self, "Error", error_msg)

    def show_file_properties(self, file_path: str):
        file_info = QFileInfo(file_path)
        properties = {
            "Name": file_info.fileName(),
            "Path": file_info.filePath(),
            "Size": f"{file_info.size()} bytes",
            "Created": file_info.birthTime().toString(),
            "Modified": file_info.lastModified().toString(),
            "Permissions": self.get_permissions_string(file_info),
            "Owner": file_info.owner(),
            "Group": file_info.group(),
        }

        properties_dialog = QDialog(self)
        properties_dialog.setWindowTitle("File Properties")
        layout = QVBoxLayout(properties_dialog)

        for key, value in properties.items():
            label = QLabel()
            label.setText(f"<b>{key}:</b> {value}")
            layout.addWidget(label)

        close_button = QPushButton("Close")
        close_button.clicked.connect(properties_dialog.accept)
        layout.addWidget(close_button)

        properties_dialog.exec_()

    def get_permissions_string(self, file_info: QFileInfo) -> str:
        permissions = []
        if file_info.isReadable():
            permissions.append("Read")
        if file_info.isWritable():
            permissions.append("Write")
        if file_info.isExecutable():
            permissions.append("Execute")
        return ", ".join(permissions)

    def calculate_checksum(self, file_path: str):
        try:
            with open(file_path, "rb") as f:
                file_hash = hashlib.sha256()
                chunk = f.read(8192)
                while chunk:
                    file_hash.update(chunk)
                    chunk = f.read(8192)
            checksum = file_hash.hexdigest()
            QMessageBox.information(self, "Checksum", f"SHA256 Checksum for {os.path.basename(file_path)}:\n{checksum}")
            self.logger.info(f"Calculated checksum for {file_path}: {checksum}")
        except Exception as e:
            error_msg = f"Could not calculate checksum: {e}"
            self.logger.exception(error_msg)
            QMessageBox.warning(self, "Error", error_msg)

    def compare_files(self):
        selected_files = self.get_selected_files()
        if len(selected_files) != 2:
            QMessageBox.warning(self, "Error", "Please select exactly two files to compare.")
            return

        try:
            with open(selected_files[0]) as file1, open(selected_files[1]) as file2:
                diff = difflib.unified_diff(
                    file1.readlines(),
                    file2.readlines(),
                    fromfile=selected_files[0],
                    tofile=selected_files[1],
                )
                diff_text = "".join(diff)
                if diff_text:
                    comparison_dialog = QDialog(self)
                    comparison_dialog.setWindowTitle("File Comparison")
                    layout = QVBoxLayout(comparison_dialog)
                    text_edit = QTextEdit()
                    text_edit.setPlainText(diff_text)
                    layout.addWidget(text_edit)
                    comparison_dialog.exec_()
                else:
                    QMessageBox.information(self, "File Comparison", "The selected files are identical.")
            self.logger.info(f"Compared files: {selected_files[0]} and {selected_files[1]}")
        except Exception as e:
            error_msg = f"Error comparing files: {e}"
            self.logger.exception(error_msg)
            QMessageBox.warning(self, "Error", error_msg)

    def secure_delete(self, file_path: str | None = None):
        if not file_path:
            selected_files = self.get_selected_files()
            if not selected_files:
                QMessageBox.warning(self, "Error", "Please select a file to securely delete.")
                return
            file_path = selected_files[0]

        reply = QMessageBox.question(
            self,
            "Confirm Secure Delete",
            f"Are you sure you want to securely delete {file_path}? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            assert file_path is not None, "File path is None"
            with open(file_path, "ba+", buffering=0) as f:
                length = f.seek(0, os.SEEK_END)
                f.seek(0)
                f.write(os.urandom(length))
            os.remove(file_path)
            QMessageBox.information(self, "Success", f"File {file_path} has been securely deleted.")
            self.logger.info(f"Securely deleted file: {file_path}")
            self.refresh_view()
        except Exception as e:
            error_msg = f"Error securely deleting file: {e}"
            self.logger.exception(error_msg)
            QMessageBox.warning(self, "Error", error_msg)

    def show_disk_usage(self):
        try:
            import psutil
        except ImportError:
            QMessageBox.warning(self, "Error", "psutil is not installed. Please install psutil to use this feature.")
            return
        disk_usage = psutil.disk_usage(str(self.current_path))
        usage_dialog = QDialog(self)
        usage_dialog.setWindowTitle("Disk Usage")
        layout = QVBoxLayout(usage_dialog)
        layout.addWidget(QLabel(f"Total: {self.format_size(disk_usage.total)}"))
        layout.addWidget(QLabel(f"Used: {self.format_size(disk_usage.used)} ({disk_usage.percent}%)"))
        layout.addWidget(QLabel(f"Free: {self.format_size(disk_usage.free)}"))
        usage_dialog.exec_()
        self.logger.info(f"Displayed disk usage for {self.current_path}")

    def get_selected_files(self) -> list[str]:
        selected_files = []
        for view in [self.list_view, self.table_view, self.tiles_view]:
            selected_indexes = view.selectedIndexes()
            for index in selected_indexes:
                file_path = self.fileSystemModel.filePath(index)
                if file_path not in selected_files:
                    selected_files.append(file_path)
        return selected_files

    def change_view_mode(self, mode: ViewMode):
        if mode == ViewMode.EXTRA_LARGE_ICONS:
            self.change_icon_size(3.0)
        elif mode == ViewMode.LARGE_ICONS:
            self.change_icon_size(2.0)
        elif mode == ViewMode.MEDIUM_ICONS:
            self.change_icon_size(1.0)
        elif mode == ViewMode.SMALL_ICONS:
            self.change_icon_size(0.5)
        elif mode == ViewMode.LIST:
            self.stacked_widget.setCurrentWidget(self.list_view)
            self.list_view.setViewMode(QListView.ListMode)
            self.list_view.setIconSize(QSize(16, 16))
            self.list_view.setGridSize(QSize())
        elif mode == ViewMode.DETAILS:
            self.stacked_widget.setCurrentWidget(self.table_view)
        elif mode == ViewMode.TILES:
            self.stacked_widget.setCurrentWidget(self.tiles_view)
            self.tiles_view.setIconSize(QSize(32, 32))
            self.tiles_view.setGridSize(QSize(120, 80))
        self.current_view = mode
        self.update_view()

    def change_icon_size(self, delta: float):
        new_multiplier = max(
            self.minimum_multiplier,
            min(self.maximum_multiplier, self.icon_size_multiplier + delta),
        )
        if new_multiplier != self.icon_size_multiplier:
            self.icon_size_multiplier = new_multiplier
            self.update_view()

    def update_view(self):
        self.icon_size = int(self.base_icon_size * self.icon_size_multiplier)
        icon_size = QSize(self.icon_size, self.icon_size)

        if self.current_view == ViewMode.DETAILS:
            self.table_view.setIconSize(icon_size)
            self.table_view.resizeColumnsToContents()
            self.table_view.horizontalHeader().setStretchLastSection(True)
        elif self.current_view == ViewMode.LIST:
            self.list_view.setIconSize(icon_size)
        elif self.current_view == ViewMode.TILES:
            self.tiles_view.setIconSize(icon_size)
        else:
            raise ValueError(f"Invalid view mode: {self.current_view}")

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if isinstance(event, QWheelEvent) and event.type() == QEvent.Type.Wheel and bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            delta = event.angleDelta().y() / 120
            self.change_icon_size(delta * 0.25)
            return True
        return super().eventFilter(obj, event)

    def update_address_bar(self, path: Path):
        self.address_bar.update_path(path)

    def toggle_hidden_items(self):
        filters = self.fileSystemModel.filter()
        if bool(filters & QDir.Hidden):
            self.fileSystemModel.setFilter(filters & ~QDir.Hidden)
            self.ui.action_show_hidden_items.setText("Show Hidden Items")
        else:
            self.fileSystemModel.setFilter(filters | QDir.Hidden)
            self.ui.action_show_hidden_items.setText("Hide Hidden Items")
        self.refresh_view()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            source_path = Path(url.toLocalFile())
            destination_path = self.current_path / source_path.name
            if source_path.is_dir():
                shutil.copytree(source_path, destination_path)
            else:
                shutil.copy2(source_path, destination_path)
        self.refresh_view()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Backspace:
            self.go_up()
        elif event.matches(QKeySequence.Refresh):
            self.refresh_view()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event: QCloseEvent):
        self.process_pool.shutdown(wait=False)
        super().closeEvent(event)

    def selectFile(self, filename: str):
        self.fileNameEdit.setText(filename)
        self._selectedFiles = [filename]
        self.fileSelected.emit(filename)

    def selectedFiles(self) -> list[str]:
        return self._selectedFiles

    def setViewMode(self, mode: QFileDialog.ViewMode):
        self._viewMode = mode
        if mode == QFileDialog.ViewMode.List:
            self.change_view_mode(ViewMode.LIST)
        elif mode == QFileDialog.ViewMode.Detail:
            self.change_view_mode(ViewMode.DETAILS)

    def viewMode(self) -> QFileDialog.ViewMode:
        return self._viewMode

    def setFileMode(self, mode: QFileDialog.FileMode):
        self._fileMode = mode

    def fileMode(self) -> QFileDialog.FileMode:
        return self._fileMode

    def setAcceptMode(self, mode: QFileDialog.AcceptMode):
        self._acceptMode = mode

    def acceptMode(self) -> QFileDialog.AcceptMode:
        return self._acceptMode

    def setNameFilter(self, filter: str):
        self.setNameFilters([filter])

    def setNameFilters(self, filters: list[str]):
        self._nameFilters = filters
        self.ui.fileTypeCombo.clear()
        self.ui.fileTypeCombo.addItems(self._nameFilters)
        self.apply_filter(self._nameFilters[0] if self._nameFilters else "*")

    def nameFilters(self) -> list[str]:
        return self._nameFilters

    def selectNameFilter(self, filter: str):
        index = self.ui.fileTypeCombo.findText(filter)
        if index >= 0:
            self.ui.fileTypeCombo.setCurrentIndex(index)

    def selectedNameFilter(self) -> str:
        return self.ui.fileTypeCombo.currentText()

    def setOption(self, option: QFileDialog.Option, on: bool = True):
        if on:
            self._options |= option
        else:
            self._options &= ~option

    def testOption(self, option: QFileDialog.Option) -> bool:
        return bool(self._options & option)

    def options(self) -> QFileDialog.Options:
        return self._options

    def setOptions(self, options: QFileDialog.Options):
        self._options = options

    def setMimeTypeFilters(self, filters: list[str]):
        self.mime_type_filters = filters
        self.ui.fileTypeCombo.clear()
        self.ui.fileTypeCombo.addItems(self.mime_type_filters)
        self.apply_filter()

    def mimeTypeFilters(self) -> list[str]:
        return self.mime_type_filters

    def selectedMimeTypeFilter(self) -> str:
        return self.ui.fileTypeCombo.currentText()

    def selectMimeTypeFilter(self, filter: str):
        index = self.ui.fileTypeCombo.findText(filter)
        if index >= 0:
            self.ui.fileTypeCombo.setCurrentIndex(index)

    def setSidebarUrls(self, urls: list[QUrl]):
        self._sidebarUrls = urls
        self.update_sidebar()

    def sidebarUrls(self) -> list[QUrl]:
        return self._sidebarUrls

    def setLabelText(self, label: QFileDialog.DialogLabel, text: str):
        if label == QFileDialog.DialogLabel.FileName:
            self.ui.fileNameLabel.setText(text)
        elif label == QFileDialog.DialogLabel.Accept:
            self.ui.okButton.setText(text)
        elif label == QFileDialog.DialogLabel.Reject:
            self.ui.cancelButton.setText(text)
        elif label == QFileDialog.DialogLabel.LookIn:
            self.ui.lookInLabel.setText(text)
        elif label == QFileDialog.DialogLabel.FileType:
            self.ui.fileTypeLabel.setText(text)

    def labelText(self, label: QFileDialog.DialogLabel) -> str:
        if label == QFileDialog.DialogLabel.FileName:
            return self.ui.fileNameLabel.text()
        elif label == QFileDialog.DialogLabel.Accept:
            return self.ui.okButton.text()
        elif label == QFileDialog.DialogLabel.Reject:
            return self.ui.cancelButton.text()
        elif label == QFileDialog.DialogLabel.LookIn:
            return self.ui.lookInLabel.text()
        elif label == QFileDialog.DialogLabel.FileType:
            return self.ui.fileTypeLabel.text()
        return ""

    def setProxyModel(self, model: QAbstractProxyModel):
        self.proxy_model = model
        self.list_view.setModel(self.proxy_model)
        self.table_view.setModel(self.proxy_model)
        self.tiles_view.setModel(self.proxy_model)

    def proxyModel(self) -> QAbstractProxyModel:
        return self.proxy_model

    def setIconProvider(self, provider: QFileIconProvider):
        self.icon_provider = provider
        self.fileSystemModel.setIconProvider(self.icon_provider)

    def iconProvider(self) -> QFileIconProvider:
        return self.icon_provider

    def setHistory(self, paths: list[str]):
        self.navigation_history = [Path(path) for path in paths]
        self.navigation_index = len(self.navigation_history) - 1

    def history(self) -> list[str]:
        return [str(path) for path in self.navigation_history]

    def setItemDelegate(self, delegate: QAbstractItemDelegate):
        self.list_view.setItemDelegate(delegate)
        self.table_view.setItemDelegate(delegate)
        self.tiles_view.setItemDelegate(delegate)

    def itemDelegate(self) -> QAbstractItemDelegate:
        return self.list_view.itemDelegate()

    def setFilter(self, filters: QDir.Filters):
        self.fileSystemModel.setFilter(filters)

    def filter(self) -> QDir.Filters:
        return self.fileSystemModel.filter()

    def setDefaultSuffix(self, suffix: str):
        self.default_suffix = suffix.lstrip('.')

    def defaultSuffix(self) -> str:
        return self.default_suffix

if __name__ == "__main__":
    app = QApplication(sys.argv)
    file_explorer = MergedFileExplorer(caption="Merged File Explorer")
    file_explorer.setFileMode(QFileDialog.FileMode.ExistingFiles)
    file_explorer.setViewMode(QFileDialog.ViewMode.Detail)
    file_explorer.setNameFilter("All Files (*);;Text Files (*.txt);;Python Files (*.py)")
    file_explorer.resize(1000, 600)
    if file_explorer.exec_() == QDialog.Accepted:
        selected_files = file_explorer.selectedFiles()
        print("Selected files:", selected_files)
    sys.exit(app.exec_())
