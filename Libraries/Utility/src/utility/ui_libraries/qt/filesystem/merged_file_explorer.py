from __future__ import annotations

import difflib
import hashlib
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
    QFileInfo,
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
from qtpy.QtGui import QDesktopServices, QDrag, QKeySequence, QWheelEvent
from qtpy.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCompleter,
    QDialog,
    QFileDialog,
    QFileIconProvider,
    QFileSystemModel,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListView,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QProgressDialog,
    QPushButton,
    QStackedWidget,
    QTableView,
    QTextEdit,
    QUndoStack,
    QVBoxLayout,
    QWidget,
)

from utility.ui_libraries.qt.filesystem.file_explorer_context_menu import FileExplorerContextMenu
from utility.ui_libraries.qt.filesystem.undo_commands import CopyCommand, DeleteCommand, MoveCommand, RenameCommand
from utility.ui_libraries.qt.widgets.itemviews.tableview import RobustTableView
from utility.ui_libraries.qt.widgets.itemviews.tileview import RobustTileView

if TYPE_CHECKING:
    from concurrent.futures import Future

    from qtpy.QtCore import QAbstractProxyModel, QByteArray, QItemSelection, QObject, QPoint, QRect
    from qtpy.QtGui import QClipboard, QCloseEvent, QDragEnterEvent, QDropEvent, QKeyEvent, QMouseEvent
    from qtpy.QtWidgets import QSplitter, QStyledItemDelegate
    from typing_extensions import Literal

    from utility.ui_libraries.qt.widgets.itemviews.listview import RobustListView


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


class MergedFileExplorer(QWidget):
    fileSelected: Signal = Signal(str)
    filesSelected: Signal = Signal(list)
    currentChanged: Signal = Signal(str)
    directoryEntered: Signal = Signal(str)
    filterSelected: Signal = Signal(str)
    directoryUrlEntered: Signal = Signal(str)
    currentUrlChanged: Signal = Signal(str)
    urlsSelected: Signal = Signal(list)
    urlSelected: Signal = Signal(str)

    getOpenFileName = QFileDialog.getOpenFileName
    getOpenFileNames = QFileDialog.getOpenFileNames
    getExistingDirectory = QFileDialog.getExistingDirectory
    getExistingDirectoryUrl = QFileDialog.getExistingDirectoryUrl
    getOpenFileUrl = QFileDialog.getOpenFileUrl
    getOpenFileUrls = QFileDialog.getOpenFileUrls
    getSaveFileUrl = QFileDialog.getSaveFileUrl
    getSaveFileName = QFileDialog.getSaveFileName
    saveFileContent = QFileDialog.saveFileContent

    # Leave here to show confirmation that we expose every function that QFileDialog provides, except these.
    def restoreState(self, state: QByteArray | bytes | bytearray) -> bool: ...
    def saveState(self) -> QByteArray: ...
    def changeEvent(self, e: QEvent) -> None: ...
    def accept(self) -> None: ...
    def done(self, result: int) -> None: ...

    def __init__(
        self,
        parent: QWidget | None = None,
        caption: str = "",
        directory: str = "",
        options: QFileDialog.Options | None = None,
    ):
        super().__init__(parent)
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

        self._options: QFileDialog.Option | QFileDialog.Options = QFileDialog.Options() if options is None else options
        self._fileMode: QFileDialog.FileMode | int = QFileDialog.FileMode.AnyFile
        self._acceptMode: QFileDialog.AcceptMode | int = QFileDialog.AcceptMode.AcceptOpen
        self._viewMode: QFileDialog.ViewMode | int = QFileDialog.ViewMode.Detail
        self.current_path: str = QDir.homePath()
        self.mime_type_filters: list[str] = []
        self.default_suffix: str = ""
        self._sidebar_urls: list[QUrl] = []
        self.tabs: list[QWidget] = []
        self.recent_directories: deque[str] = deque(maxlen=10)
        self.settings = QSettings("QtCustomWidgets", "MergedFileExplorer")
        self.file_operation_queue: list[tuple[Callable[[], Any], Literal["copy", "move", "delete", "rename"], str, str | None]] = []
        self.process_pool: ProcessPoolExecutor = ProcessPoolExecutor(max_workers=min(4, (os.cpu_count() or 1)))
        self.lazy_load_batch_size: int = 100
        self.navigation_history: list[Path] = []
        self.navigation_index: int = -1
        self.clipboard: QClipboard = QApplication.clipboard()
        self.undo_stack: QUndoStack = QUndoStack(self)

        self._history: list[str] = []

        self.fsModel: QFileSystemModel = QFileSystemModel(self)
        self.fsModel.setIconProvider(QFileIconProvider())
        self.fsModel.setOption(QFileSystemModel.Option.DontWatchForChanges)

        self.setup_ui(caption)
        self.setup_menu()
        self.setup_connections()
        self.setup_sidebar()

        self.setDirectory(directory or QDir.homePath())
        self.setup_file_operations()

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        self.ui.status_bar.addPermanentWidget(self.progress_bar)  # pyright: ignore[reportArgumentType]

        if platform.system() == "Windows":
            self.setup_com_interfaces()

        self.context_menu_handler = FileExplorerContextMenu(self)
        self.icon_provider = QFileIconProvider()
        self.fsModel.setIconProvider(self.icon_provider)
        self.fsModel.setReadOnly(False)
        self.fsModel.setOption(QFileSystemModel.DontWatchForChanges, False)

    def set_current_path(self, path: os.PathLike | str):
        self.current_path = os.path.normpath(path)

    def handle_process_result(
        self,
        future: Future,
        callback: Callable[[Any], Any],
        error_callback: Callable[[Exception], Any],
    ):
        try:
            result = future.result()
            QTimer.singleShot(0, lambda: self._handle_process_result(result, callback))
        except Exception as e:
            RobustLogger().exception("Error in process execution")
            if error_callback is None:
                return
            QTimer.singleShot(0, lambda e=e: error_callback(e))

    def _handle_process_result(self, result: Any, callback: Callable[[Any], Any]):
        if callback and result is not None:
            callback(result)

    def go_to_parent(self):
        parent_path = os.path.dirname(self.current_path)  # noqa: PTH120
        self.setDirectory(parent_path)

    def create_new_folder_in(self, directory: str):
        new_folder_name, ok = QInputDialog.getText(self, "Create New Folder", "Folder name:")
        if ok and new_folder_name:
            new_folder_path = os.path.join(directory, new_folder_name)  # noqa: PTH118
            try:
                os.makedirs(new_folder_path)  # noqa: PTH103
                self.setDirectory(directory)  # Refresh the view
                RobustLogger().info(f"Created new folder: {new_folder_path}")
            except OSError:
                RobustLogger().exception("Failed to create folder")
                QMessageBox.warning(self, "Error", "Failed to create folder")

    def lazy_load_directory(self, root_index: QModelIndex):
        total_items = self.fsModel.rowCount(root_index)
        self.load_batch(root_index, 0, min(self.lazy_load_batch_size, total_items))

    def load_batch(self, root_index: QModelIndex, start: int, end: int):
        def fetch_batch(root: QModelIndex) -> int:
            for i in range(start, end):
                self.fsModel.fetchMore(self.fsModel.index(i, 0, root))
            return end

        def continue_loading(end: int):
            total_items = self.fsModel.rowCount(root_index)
            if end < total_items:
                next_end = min(end + self.lazy_load_batch_size, total_items)
                self.run_in_background(fetch_batch, callback=lambda _: continue_loading(next_end))
            else:
                RobustLogger().debug(f"Finished lazy loading directory: {self.current_path}")

        self.run_in_background(fetch_batch, callback=lambda _: continue_loading(end))

    def expand_sidebar_to_current_directory(self, directory: str):
        index = self.fsModel.index(os.path.abspath(directory))  # noqa: PTH100
        while index.isValid():
            self.ui.navigation_pane.expand(index)  # pyright: ignore[reportArgumentType]
            index = index.parent()

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
            with open(file_path, "rb") as f:  # noqa: PTH123
                file_hash = hashlib.sha256()
                chunk = f.read(8192)
                while chunk:
                    file_hash.update(chunk)
                    chunk = f.read(8192)
            checksum = file_hash.hexdigest()
            QMessageBox.information(self, "Checksum", f"SHA256 Checksum for {os.path.basename(file_path)}:\n{checksum}")  # noqa: PTH119
            RobustLogger().info(f"Calculated checksum for {file_path}: {checksum}")
        except Exception as e:
            error_msg = f"Could not calculate checksum: {e}"
            RobustLogger().exception(error_msg)
            QMessageBox.warning(self, "Error", error_msg)

    def compare_files(self):
        selected_files = self.get_selected_files()
        if len(selected_files) != 2:
            error_msg = "Please select exactly two files to compare."
            RobustLogger().warning(error_msg)
            QMessageBox.warning(self, "Error", error_msg)
            return

        try:
            with open(selected_files[0]) as file1, open(selected_files[1]) as file2:  # noqa: PTH123
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
            RobustLogger().info(f"Compared files: {selected_files[0]} and {selected_files[1]}")
        except Exception as e:  # noqa: BLE001
            error_msg = f"Error comparing files: {e}"
            RobustLogger().exception(error_msg)
            QMessageBox.warning(self, "Error", error_msg)

    def open(self, slot: Callable[[QUrl], None] | None = None):
        selected_files = self.get_selected_files()
        if not selected_files:
            QMessageBox.warning(self, "Error", "Please select a file to open.")
            return
        file_path = selected_files[0]
        url = QUrl.fromLocalFile(file_path)
        if slot is None:
            QDesktopServices.openUrl(url)
        else:
            slot(url)

    def setVisible(self, visible: bool):  # noqa: FBT001
        super().setVisible(visible)
        if visible:
            self.refresh_view()

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
            with open(file_path, "ba+", buffering=0) as f:  # noqa: PTH123
                length = f.seek(0, os.SEEK_END)
                f.seek(0)
                f.write(os.urandom(length))
            os.remove(file_path)  # noqa: PTH107
            QMessageBox.information(self, "Success", f"File {file_path} has been securely deleted.")
            RobustLogger().info(f"Securely deleted file: {file_path}")
            self.refresh_view()
        except Exception as e:  # noqa: BLE001
            error_msg = f"Error securely deleting file: {e}"
            RobustLogger().exception(error_msg)
            QMessageBox.warning(self, "Error", error_msg)

    def show_disk_usage(self):
        try:
            import psutil
        except ImportError:
            QMessageBox.warning(self, "Error", "psutil is not installed. Please install psutil to use this feature.")
            return
        disk_usage = psutil.disk_usage(self.current_path)
        usage_dialog = QDialog(self)
        usage_dialog.setWindowTitle("Disk Usage")
        layout = QVBoxLayout(usage_dialog)
        layout.addWidget(QLabel(f"Total: {self.format_size(disk_usage.total)}"))
        layout.addWidget(QLabel(f"Used: {self.format_size(disk_usage.used)} ({disk_usage.percent}%)"))
        layout.addWidget(QLabel(f"Free: {self.format_size(disk_usage.free)}"))
        usage_dialog.exec_()
        RobustLogger().info(f"Displayed disk usage for {self.current_path}")

    def setDirectory(self, directory: str, *, add_to_history: bool = True):
        abs_directory = os.path.abspath(os.path.normpath(directory))  # noqa: PTH100
        if not abs_directory or not os.path.isdir(abs_directory):  # noqa: PTH112
            RobustLogger().warning(f"Invalid directory: {abs_directory}")
            return

        self.fsModel.setRootPath(abs_directory)
        path_obj = Path(abs_directory)
        if path_obj.is_dir():
            self.current_path = abs_directory
            root_index = self.fsModel.index(abs_directory)
            self.ui.file_list_view.setRootIndex(root_index)  # pyright: ignore[reportArgumentType]
            self.table_view.setRootIndex(root_index)  # pyright: ignore[reportArgumentType]
            self.tiles_view.setRootIndex(root_index)  # pyright: ignore[reportArgumentType]
            self.list_view.setRootIndex(root_index)  # pyright: ignore[reportArgumentType]
            self.ui.navigation_pane.setCurrentIndex(root_index)  # pyright: ignore[reportArgumentType]
            self.ui.address_bar.setText(self.current_path)  # pyright: ignore[reportArgumentType]
            self.directoryEntered.emit(self.current_path)
            self.add_to_history(path_obj)
            self.update_ui()
        else:
            self.ui.address_bar.setText(self.current_path)  # pyright: ignore[reportArgumentType]
        self.currentChanged.emit(self.current_path)
        if add_to_history:
            self._history.append(abs_directory)
            self.recent_directories.appendleft(abs_directory)
        self.save_session()
        self.directoryEntered.emit(abs_directory)
        self.expand_sidebar_to_current_directory(abs_directory)
        self.update_sidebar()
        self.lazy_load_directory(root_index)
        RobustLogger().debug(f"Set directory to: {abs_directory}")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        elif event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()
        else:
            RobustLogger().warning("Unknown mime data format: %s", event.mimeData().formats())

    def startDrag(self, supported_actions: Qt.DropAction | Qt.DropActions):
        drag = QDrag(self)
        mime_data: QMimeData = QMimeData()
        view = cast(QAbstractItemView, self.sender())
        model: QFileSystemModel = cast(QFileSystemModel, view.model())
        urls: list[QUrl] = [QUrl.fromLocalFile(model.filePath(index)) for index in view.selectedIndexes()]
        mime_data.setUrls(urls)
        drag.setMimeData(mime_data)
        result = drag.exec_(supported_actions)
        if result == Qt.DropAction.MoveAction:
            for url in urls:
                file_path = url.toLocalFile()
                try:
                    if os.path.isdir(file_path):  # noqa: PTH112
                        shutil.rmtree(file_path)
                    else:
                        os.remove(file_path)  # noqa: PTH107
                except OSError as e:
                    QMessageBox.warning(self, "Error", f"Could not remove {file_path}: {e}")
            self.refresh_view()

        elif not self._selectedFiles:
            self._selectedFiles = self.get_selected_files()
        if self._acceptMode == QFileDialog.AcceptMode.AcceptSave and self.default_suffix and not self._selectedFiles[0].endswith(self.default_suffix):
            self._selectedFiles[0] += f".{self.default_suffix}"

    def __del__(self):
        RobustLogger().info("PyFileExplorer instance destroyed")
        self.process_pool.shutdown(wait=True)

    def save_session(self):
        self.settings = QSettings("YourOrganizationName", "YourAppName")
        self.settings.setValue("recentDirectories", list(self.recent_directories))
        self.settings.setValue("lastDirectory", self.current_path)
        self.settings.setValue("viewMode", self.viewMode())
        self.settings.setValue("splitterState", self.saveState())

    def load_session(self):
        recent_directories = self.settings.value("recentDirectories", [])
        if isinstance(recent_directories, list):
            self.recent_directories = deque(recent_directories, maxlen=self.recent_directories.maxlen)
        else:
            self.recent_directories = deque([], maxlen=self.recent_directories.maxlen)
        last_directory = self.settings.value("lastDirectory")
        if last_directory and os.path.exists(last_directory) and os.path.isdir(last_directory):  # noqa: PTH112, PTH110
            self.setDirectory(last_directory, add_to_history=False)
        view_mode = self.settings.value("viewMode")
        if view_mode:
            self.setViewMode(view_mode)
        splitter_state = self.settings.value("splitterState")
        if splitter_state:
            self.ui.splitter.restoreState(splitter_state)

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

        # Setup views
        self.setup_views()

        # Setup completer
        self.completer: QCompleter = QCompleter(self)
        self.completer.setModel(self.fsModel)
        self.ui.address_bar.setCompleter(self.completer)  # pyright: ignore[reportArgumentType]

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
        self.splitter: QSplitter = self.ui.splitter  # pyright: ignore[reportAttributeAccessIssue]

        # Setup stacked widget
        self.stacked_widget: QStackedWidget = QStackedWidget()
        self.splitter.replaceWidget(1, self.stacked_widget)

        # Add views to stacked widget
        self.stacked_widget.addWidget(self.ui.file_list_view)  # pyright: ignore[reportArgumentType]
        self.stacked_widget.addWidget(self.table_view)
        self.stacked_widget.addWidget(self.tiles_view)

        # Set current view
        self.current_view: ViewMode = ViewMode.DETAILS
        self.stacked_widget.setCurrentWidget(self.table_view)

    def setup_views(self):
        self.list_view: RobustListView = self.ui.file_list_view  # pyright: ignore[reportAttributeAccessIssue]
        self.table_view: FirstColumnInteractableTableView = FirstColumnInteractableTableView()
        self.tiles_view: RobustTileView = RobustTileView()
        self.preview_view: QLabel = QLabel()

        self.list_view.viewport().installEventFilter(self)
        self.table_view.viewport().installEventFilter(self)
        self.tiles_view.viewport().installEventFilter(self)

        for view in (self.list_view, self.table_view, self.tiles_view):
            view.setModel(self.fsModel)
            view.setRootIndex(self.fsModel.index(str(self.current_path)))
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

        self.ui.navigation_pane.setModel(self.fsModel)  # pyright: ignore[reportArgumentType]
        self.ui.navigation_pane.setRootIndex(self.fsModel.index(""))  # pyright: ignore[reportArgumentType]
        self.ui.navigation_pane.expandToDepth(0)
        self.ui.navigation_pane.setHeaderHidden(True)
        self.ui.navigation_pane.clicked.connect(self.on_tree_view_clicked)

        for i in range(1, self.fsModel.columnCount()):
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
        self.ui.search_bar.editingFinished.connect(self.on_search_text_changed)

        self.ui.address_bar.editingFinished.connect(self.on_address_bar_path_changed)
        self.fsModel.directoryLoaded.connect(self.on_directory_loaded)

        for view in [self.list_view, self.table_view, self.tiles_view]:
            assert isinstance(view, QAbstractItemView), "Invalid view type: " + view.__class__.__name__
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

    def add_file_operation(self, operation: Callable[[], None], source: str, destination: str | None = None):
        self.file_operation_queue.append((operation, source, destination))
        QTimer.singleShot(0, self.process_file_operations)
        RobustLogger().info(f"Added file operation: {operation} - {source} to {destination}")

    def process_file_operations(self):
        if not self.file_operation_queue:
            return

        operation, source, destination = self.file_operation_queue.pop(0)
        progress_dialog = QProgressDialog("Processing file operation...", "Cancel", 0, 100, self)
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.setAutoClose(True)
        progress_dialog.setAutoReset(True)

        def update_progress(progress: float):
            progress_dialog.setValue(int(progress * 100))
            QApplication.processEvents()

        def operation_callback(result: tuple[str, str, str | None]):
            RobustLogger().info(f"File operation completed: {result}")
            self.refresh_view()
            QTimer.singleShot(0, self.process_file_operations)

        def error_callback(error: Exception):
            RobustLogger().exception("Error in file operation")
            QMessageBox.warning(self, "Error", f"An error occurred during the file operation: {error}")

        self.run_in_background(
            self._execute_file_operation,
            operation,
            source,
            destination,
            callback=operation_callback,
            error_callback=error_callback,
        )

    def _execute_file_operation(self, operation: Literal["copy", "move", "delete", "rename"], source: str, destination: str | None = None) -> tuple[str, str, str | None]:
        if operation == "copy":
            assert destination is not None, "Destination is None"
            if os.path.isdir(source):  # noqa: PTH112
                shutil.copytree(source, os.path.join(destination, os.path.basename(source)))  # noqa: PTH118, PTH119
            else:
                shutil.copy2(source, destination)
        elif operation == "move":
            assert destination is not None, "Destination is None"
            shutil.move(source, destination)
        elif operation == "delete":
            if os.path.isfile(source):  # noqa: PTH113
                os.remove(source)  # noqa: PTH107
            else:
                shutil.rmtree(source, ignore_errors=True, onerror=RobustLogger().exception)
        elif operation == "rename":
            assert destination is not None, "Destination is None"
            os.rename(source, destination)  # noqa: PTH104
        RobustLogger().info(f"Completed file operation: {operation} - {source} to {destination}")
        return operation, source, destination

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
            index = self.fsModel.index(url.toLocalFile())
            if index.isValid():
                self.ui.navigation_pane.setCurrentIndex(index)  # pyright: ignore[reportArgumentType]
                self.ui.navigation_pane.scrollTo(index)  # pyright: ignore[reportArgumentType]
            self.ui.navigation_pane.setExpanded(index, True)  # pyright: ignore[reportArgumentType]  # noqa: FBT003
        self.ui.navigation_pane.blockSignals(False)  # noqa: FBT003

    def on_selection_changed(self, selected: QItemSelection, deselected: QItemSelection):
        selected_indexes = selected.indexes()
        if selected_indexes:
            file_path = self.fsModel.filePath(selected_indexes[0])
            self.ui.address_bar.setText(QFileInfo(file_path).fileName())
            if len(selected_indexes) == 1:
                self.fileSelected.emit(file_path)
            self.filesSelected.emit([self.fsModel.filePath(index) for index in selected_indexes])
        else:
            self.ui.address_bar.clear()
            self.fileSelected.emit("")
            self.filesSelected.emit([])

    def on_item_double_clicked(self, index: QModelIndex):
        path = Path(self.fsModel.filePath(index))
        if path.is_dir():
            self.set_current_path(path)
        else:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def on_tree_view_clicked(self, index: QModelIndex):
        path = Path(self.fsModel.filePath(index))
        self.set_current_path(path)

    def on_go_button_clicked(self):
        path = self.ui.address_bar.text()
        self.set_current_path(path)

    def on_search_text_changed(self, text: str):
        proxy_model = QSortFilterProxyModel(self)
        proxy_model.setSourceModel(self.fsModel)
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

    def directory(self) -> str:
        return self.current_path

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
        parent_path = os.path.dirname(self.current_path)  # noqa: PTH120
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
        total_items = self.fsModel.rowCount(self.list_view.rootIndex())
        if selected_items > 0:
            status_text = f"{selected_items} item{'s' if selected_items > 1 else ''} selected"
        else:
            status_text = f"{total_items} item{'s' if total_items > 1 else ''}"
        self.ui.status_items.setText(status_text)

        total_size = sum(self.fsModel.size(self.fsModel.index(i, 0, self.list_view.rootIndex())) for i in range(total_items))
        self.ui.status_size.setText(self.format_size(total_size))

    def format_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:  # noqa: PLR2004
                return f"{size:.1f} {unit}"
            size = int(size / 1024.0)
        return f"{size:.1f} PB"

    def new_window(self):
        new_window = MergedFileExplorer()
        new_window.show()

    def open_windows_terminal(self):
        import shlex
        command = f'start cmd /K "cd /d {shlex.quote(str(self.current_path))}"'
        subprocess.Popen(shlex.split(command))  # noqa: S603

    def show_properties(self):
        selected_indexes = self.list_view.selectedIndexes()
        if selected_indexes:
            file_path = Path(self.fsModel.filePath(selected_indexes[0]))
            properties = f"Name: {file_path.name}\n"
            properties += f"Type: {'Directory' if file_path.is_dir() else 'File'}\n"
            properties += f"Size: {self.format_size(file_path.stat().st_size)}\n"
            properties += f"Created: {file_path.stat().st_ctime}\n"
            properties += f"Modified: {file_path.stat().st_mtime}\n"
            properties += f"Accessed: {file_path.stat().st_atime}\n"

            QMessageBox.information(self, "Properties", properties)

    def cut_file(self, slot: bool = False):  # noqa: FBT002, FBT001
        selected_indexes = self.list_view.selectedIndexes()
        if not selected_indexes:
            return
        source_paths = [Path(self.fsModel.filePath(index)) for index in selected_indexes]
        # TODO: some code to put onto the os clipboard (windows, linux, macos, etc). Then use in paste_file.
        # TODO: set transparency of the cut files to 50%

    def copy_file(self, slot: bool = False):  # noqa: FBT002, FBT001
        selected_indexes = self.list_view.selectedIndexes()
        if not selected_indexes:
            return
        source_paths = [Path(self.fsModel.filePath(index)) for index in selected_indexes]
        # TODO: some code to put onto the os clipboard (windows, linux, macos, etc). Then use in paste_file.
        # TODO: set transparency of the copied files to 50%

    def paste_file(self, slot: bool = False):  # noqa: FBT002, FBT001
        mime_data = self.clipboard.mimeData()
        if not mime_data.hasUrls():
            return
        source_paths = [Path(url.toLocalFile()) for url in mime_data.urls()]
        destination_path = Path(self.current_path)

        if self.undo_stack.undoText() == "Cut":
            command = MoveCommand(source_paths, destination_path)
        else:
            command = CopyCommand(source_paths, destination_path)

        self.undo_stack.push(command)
        self.refresh_view()

    def delete_file(self, slot: bool = False):  # noqa: FBT002, FBT001
        selected_indexes = self.list_view.selectedIndexes()
        if not selected_indexes:
            return
        paths = [Path(self.fsModel.filePath(index)) for index in selected_indexes]
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

    def rename_file(self, slot: bool = False):  # noqa: FBT002, FBT001
        selected_indexes = self.list_view.selectedIndexes()
        if not selected_indexes:
            return
        file_path = Path(self.fsModel.filePath(selected_indexes[0]))
        new_name, ok = QInputDialog.getText(self, "Rename", "Enter new name:", QLineEdit.EchoMode.Normal, file_path.name)
        if not ok or not new_name:
            return
        new_path = file_path.with_name(new_name)
        if new_path.exists():
            QMessageBox.warning(self, "Rename", "A file with this name already exists.")
        else:
            command = RenameCommand(file_path, new_path)
            self.undo_stack.push(command)
            self.refresh_view()

    def run_in_background(
        self,
        func: Callable[..., Any],
        *args: Any,
        callback: Callable[..., Any] | None = None,
        error_callback: Callable[[Exception], Any] | None = None,
    ):
        try:
            future = self.process_pool.submit(func, *args)
            if callback is None and error_callback is None:
                return
            if callback is None:
                callback = lambda _: None  # noqa: E731
            if error_callback is None:
                error_callback = lambda _: None  # noqa: E731
        except Exception as e:
            RobustLogger().exception("Error submitting task to process pool")
            if error_callback:
                error_callback(e)
        else:
            future.add_done_callback(lambda f: self.handle_process_result(f, callback, error_callback))

    def update_progress(self, value: int):
        self.progress_bar.setValue(value)
        if value >= 100:
            self.progress_bar.setVisible(False)
        elif not self.progress_bar.isVisible():
            self.progress_bar.setVisible(True)

    def create_new_folder(self):
        new_folder_name, ok = QInputDialog.getText(self, "Create New Folder", "Folder name:")
        if ok and new_folder_name:
            new_folder_path = os.path.join(self.current_path, new_folder_name)  # noqa: PTH118
            try:
                os.makedirs(new_folder_path, exist_ok=True)  # noqa: PTH103
                self.refresh_view()
                RobustLogger().info(f"Created new folder: {new_folder_path}")
            except OSError:
                RobustLogger().exception("Failed to create folder")
                QMessageBox.warning(self, "Error", "Failed to create folder")

    def show_context_menu(self, pos: QPoint):
        sender = self.sender()
        assert isinstance(sender, QAbstractItemView), f"Expected QAbstractItemView, got {sender.__class__.__name__}"
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

        file_path = self.fsModel.filePath(index)

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
            os.path.dirname(file_path),  # noqa: PTH120
            "Zip Files (*.zip)",
        )
        if not zip_path or not zip_path.strip():
            return
        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                if os.path.isfile(file_path):  # noqa: PTH113
                    zipf.write(file_path, os.path.basename(file_path))  # noqa: PTH119
                    return
                for root, _, files in os.walk(file_path):
                    for file in files:
                        zipf.write(
                            os.path.join(root, file),  # noqa: PTH118
                            os.path.relpath(
                                os.path.join(root, file),  # noqa: PTH118
                                os.path.join(file_path, ".."),  # noqa: PTH118
                            ),
                        )  # noqa: PTH118
                QMessageBox.information(self, "Success", f"File(s) compressed successfully to {zip_path}")
        except Exception as e:  # noqa: BLE001
            error_msg = "Could not compress file(s)"
            RobustLogger().exception(error_msg)
            QMessageBox.warning(self, "Error", f"{error_msg}: {e}")

    def extract_file(self, file_path: str):
        if not file_path.lower().endswith(".zip"):
            QMessageBox.warning(self, "Error", "Selected file is not a zip file")
            return
        extract_path = QFileDialog.getExistingDirectory(self, "Select Extraction Directory", os.path.dirname(file_path))  # noqa: PTH120
        if not extract_path or not extract_path.strip():
            return
        try:
            with zipfile.ZipFile(file_path, "r") as zipf:
                zipf.extractall(extract_path)
            QMessageBox.information(self, "Success", f"File(s) extracted successfully to {extract_path}")
        except Exception as e:  # noqa: BLE001
            error_msg = f"Could not extract file(s): {e}"
            RobustLogger().exception(error_msg)
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

    def get_selected_files(self) -> list[str]:
        selected_files: list[str] = []
        for view in (self.list_view, self.table_view, self.tiles_view):
            assert isinstance(view, QAbstractItemView), f"Expected QAbstractItemView, got {view.__class__.__name__}"
            selected_indexes = view.selectedIndexes()
            for index in selected_indexes:
                file_path = self.fsModel.filePath(index)
                if file_path in selected_files:
                    continue
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
        if (
            isinstance(event, QWheelEvent)
            and event.type() == QEvent.Type.Wheel
            and bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
        ):
            delta = event.angleDelta().y() / 120
            self.change_icon_size(delta * 0.25)
            return True
        return super().eventFilter(obj, event)

    def update_address_bar(self, path: Path):
        self.ui.address_bar.setText(str(path))

    def toggle_hidden_items(self):
        filters = self.fsModel.filter()
        if bool(filters & QDir.Hidden):
            self.fsModel.setFilter(filters & ~QDir.Hidden)
            self.ui.action_show_hidden_items.setText("Show Hidden Items")
        else:
            self.fsModel.setFilter(filters | QDir.Hidden)
            self.ui.action_show_hidden_items.setText("Hide Hidden Items")
        self.refresh_view()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            urls: list[QUrl] = event.mimeData().urls()
            for url in urls:
                file_path = url.toLocalFile()
                if os.path.isdir(file_path):  # noqa: PTH112
                    self.setDirectory(file_path)
                else:
                    self.copy_file(file_path)  # FIXME: figure out why it's relying on selectedIndexes and figure out how to set these as selected?
        elif event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            source_widget = cast(QAbstractItemView, event.source())
            if source_widget != self.sender():
                indexes = source_widget.selectedIndexes()
                for index in indexes:
                    source_path: str = self.fsModel.filePath(index)
                    self.copy_file(source_path)  # FIXME: figure out why it's relying on selectedIndexes and figure out how to set these as selected?
        else:
            RobustLogger().warning("Unknown mime data format: %s", event.mimeData().formats())
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

    def setViewMode(self, mode: QFileDialog.ViewMode):
        self._viewMode = mode
        if mode == QFileDialog.ViewMode.List:
            self.change_view_mode(ViewMode.LIST)
        elif mode == QFileDialog.ViewMode.Detail:
            self.change_view_mode(ViewMode.DETAILS)

    def viewMode(self) -> QFileDialog.ViewMode | int:
        return self._viewMode

    def setFileMode(self, mode: QFileDialog.FileMode):
        self._fileMode = mode

    def setSidebarUrls(self, urls: list[QUrl]):
        self._sidebarUrls = urls
        self.update_sidebar()

    def sidebarUrls(self) -> list[QUrl]:
        return self._sidebarUrls

    def setProxyModel(self, model: QAbstractProxyModel):
        self.proxy_model = model
        self.list_view.setModel(self.proxy_model)
        self.table_view.setModel(self.proxy_model)
        self.tiles_view.setModel(self.proxy_model)

    def proxyModel(self) -> QAbstractProxyModel:
        return self.proxy_model

    def setIconProvider(self, provider: QFileIconProvider):
        self.icon_provider = provider
        self.fsModel.setIconProvider(self.icon_provider)

    def iconProvider(self) -> QFileIconProvider:
        return self.icon_provider

    def setHistory(self, paths: list[str]):
        self.navigation_history = [Path(path) for path in paths]
        self.navigation_index = len(self.navigation_history) - 1

    def history(self) -> list[str]:
        return [str(path) for path in self.navigation_history]

    def setItemDelegate(self, delegate: QStyledItemDelegate):
        self.list_view.setItemDelegate(delegate)
        self.table_view.setItemDelegate(delegate)
        self.tiles_view.setItemDelegate(delegate)

    def itemDelegate(self) -> QStyledItemDelegate:
        return self.list_view.itemDelegate()

    def setFilter(self, filters: QDir.Filters):
        self.fsModel.setFilter(filters)

    def filter(self) -> QDir.Filters:
        return self.fsModel.filter()

    def setDefaultSuffix(self, suffix: str):
        self.default_suffix = suffix.lstrip(".")

    def defaultSuffix(self) -> str:
        return self.default_suffix


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = QMainWindow()
    file_explorer = MergedFileExplorer(caption="Merged File Explorer")
    file_explorer.setFileMode(QFileDialog.FileMode.ExistingFiles)
    file_explorer.setViewMode(QFileDialog.ViewMode.Detail)
    file_explorer.resize(1000, 600)
    main_window.setCentralWidget(file_explorer)
    main_window.show()
    sys.exit(app.exec_())
