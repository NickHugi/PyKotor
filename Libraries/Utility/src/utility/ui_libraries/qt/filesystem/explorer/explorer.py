from __future__ import annotations

import asyncio
import difflib
import fnmatch
import functools
import logging
import mimetypes
import multiprocessing
import os
import queue
import shutil
import zipfile

from collections import deque
from concurrent.futures import ProcessPoolExecutor
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Generic, TypeVar, cast, overload

from PyQt6.QtWidgets import QComboBox, QDockWidget, QStyle, QToolTip
from qasync import QEventLoop  # pyright: ignore[reportPrivateImportUsage]
from qtpy.QtCore import (
    QDir,
    QFileInfo,
    QMimeData,
    QSettings,
    QSortFilterProxyModel,
    QStandardPaths,
    QThread,
    QTimer,
    QUrl,
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QCursor, QDesktopServices, QDrag, QIcon, QKeySequence
from qtpy.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFileIconProvider,
    QFileSystemModel,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMenuBar,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTextEdit,
    QToolButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from utility.misc import generate_hash
from utility.system.app_process.task_consumer import TaskConsumer
from utility.ui_libraries.qt.filesystem.explorer.explorer_ui import UI_PyFileExplorer
from utility.ui_libraries.qt.filesystem.explorer.qfiledialog.private.qfiledialog import QFileDialog  # noqa: F811
from utility.ui_libraries.qt.widgets.itemviews.treeview import RobustTreeView

if TYPE_CHECKING:
    from multiprocessing.synchronize import Event as multiprocessing_Event

    from qtpy.QtCore import QAbstractProxyModel, QByteArray, QEvent, QItemSelection, QModelIndex, QPoint
    from qtpy.QtGui import QDragEnterEvent, QDropEvent, QKeyEvent
    from qtpy.QtWidgets import QAbstractItemDelegate, QWidget


class FileOperation(Enum):
    COPY = auto()
    MOVE = auto()
    DELETE = auto()
    RENAME = auto()


T = TypeVar("T")


class Task(Generic[T]):
    def __init__(self, func: Callable[..., T], args: tuple[Any, ...], callback: Callable[[T], None] | None = None, error_callback: Callable[[Exception], None] | None = None):
        self.func: Callable[..., T] = func
        self.args: tuple[Any, ...] = args
        self.callback: Callable[[T], None] | None = callback
        self.error_callback: Callable[[Exception], None] | None = error_callback

    def __call__(self):
        try:
            result = self.func(*self.args)
            if self.callback:
                self.callback(result)
        except Exception as e:
            if self.error_callback:
                self.error_callback(e)


F = TypeVar("F", bound=Callable[..., Any])


class Callback(Generic[F]):
    def __init__(self, func: F, *args: Any, **kwargs: Any):
        self.wrapped_func: F = func
        self.args: tuple[Any, ...] = args or ()
        self.kwargs: dict[str, Any] = kwargs or {}

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        func = self.wrapped_func(*self.args, **self.kwargs)
        result: Any = func(*args, **kwargs)
        return result


class PyFileExplorer(QDialog):
    fileSelected: Signal = Signal(str)
    filesSelected: Signal = Signal(list)

    currentChanged: Signal = Signal(str)
    directoryEntered: Signal = Signal(str)
    filterSelected: Signal = Signal(str)
    directoryUrlEntered: Signal = Signal(str)
    currentUrlChanged: Signal = Signal(str)
    urlsSelected: Signal = Signal(list)
    urlSelected: Signal = Signal(str)

    def selectedMimeTypeFilter(self) -> str: ...
    def selectMimeTypeFilter(self, filter: str) -> None: ...  # noqa: A002
    def mimeTypeFilters(self) -> list[str]: ...
    def setFilter(self, filters: QDir.Filters | QDir.Filter) -> None: ...
    def filter(self) -> QDir.Filters: ...
    def selectNameFilter(self, filter: str) -> None: ...  # noqa: A002
    def nameFilters(self) -> list[str]: ...
    def proxyModel(self) -> QAbstractProxyModel: ...
    def setProxyModel(self, model: QAbstractProxyModel) -> None: ...
    def restoreState(self, state: QByteArray | bytes | bytearray) -> bool: ...
    def saveState(self) -> QByteArray: ...
    def changeEvent(self, e: QEvent) -> None: ...
    def accept(self) -> None: ...
    def done(self, result: int) -> None: ...
    def labelText(self, label: QFileDialog.DialogLabel) -> str: ...
    def iconProvider(self) -> QFileIconProvider: ...
    def setIconProvider(self, provider: QFileIconProvider) -> None: ...
    def itemDelegate(self) -> QAbstractItemDelegate: ...
    def setItemDelegate(self, delegate: QAbstractItemDelegate) -> None: ...
    def defaultSuffix(self) -> str: ...

    def __init__(
        self,
        parent: QWidget | None = None,
        caption: str = "",
        directory: str = "",
        file_filter: str = "",
        initial_filter: str = "",
        options: QFileDialog.Options | None = None,
    ):
        super().__init__(parent)
        self.resize(1000, 600)
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
        self.settings = QSettings("QtCustomWidgets", "PyFileExplorer")
        self.file_operation_queue: list[tuple[FileOperation, str, str | None]] = []
        self.lazy_load_batch_size: int = 100
        self._showing_hidden_files: bool = False

        self._fs_model: QFileSystemModel = QFileSystemModel(self)
        self._fs_model.setIconProvider(QFileIconProvider())
        self._fs_model.setOption(QFileSystemModel.Option.DontWatchForChanges)

        self._history: list[str] = []
        self._history_index: int = -1  # Track the current position in history

        self._abort: multiprocessing_Event = multiprocessing.Event()
        self._task_queue: multiprocessing.JoinableQueue = multiprocessing.JoinableQueue()
        self._result_queue: multiprocessing.Queue = multiprocessing.Queue()
        self._setup_consumers()
        self._consumers: list[TaskConsumer] = []
        self._executor = ProcessPoolExecutor(max_workers=min(4, (os.cpu_count() or 1)))

        self.ui = UI_PyFileExplorer
        self.ui.setupUi(self)
        self.setup_menu()
        self.setup_connections()
        self.setup_sidebar()

        self.setup_logging()

        self.setDirectory(directory or QDir.homePath())
        if file_filter:
            self.setNameFilters(file_filter.split(";;"))
        if initial_filter and initial_filter.strip() and initial_filter not in self.nameFilters():
            self.setNameFilter(initial_filter)

        self.process_file_operations()

        self._scanner: QThread = QThread(self)
        self._scanner.setObjectName("TextureListScanner")
        self._scanner.run = self.scan
        self._scanner.start(QThread.Priority.LowestPriority)

    def toggle_hidden_files(self):
        self._showing_hidden_files = not self._showing_hidden_files
        self._fs_model.setFilter(self._fs_model.filter() | QDir.Filter.Hidden)

    def scan(self):
        while not self._abort.is_set():
            try:
                result = self._result_queue.get(True, None)
                if result is None:
                    continue
                self._handle_result(result)
            except queue.Empty:
                ...

    def _setup_consumers(self) -> None:
        num_consumers = multiprocessing.cpu_count() * 2
        self._consumers = []
        for _ in range(num_consumers):
            consumer = TaskConsumer(
                stop_event=self._abort,
                task_queue=self._task_queue,
                result_queue=self._result_queue,
                daemon=True,
            )
            self._consumers.append(consumer)
        for consumer in self._consumers:
            consumer.start()

    def _execute_file_operation(self, operation: FileOperation, source: str, destination: str | None = None) -> tuple[FileOperation, str, str | None]:
        if operation == FileOperation.COPY:
            assert destination is not None, "Destination is None"
            if os.path.isdir(source):  # noqa: PTH112
                shutil.copytree(source, os.path.join(destination, os.path.basename(source)))  # noqa: PTH118, PTH119
            else:
                shutil.copy2(source, destination)
        elif operation == FileOperation.MOVE:
            assert destination is not None, "Destination is None"
            shutil.move(source, destination)
        elif operation == FileOperation.DELETE:
            if os.path.isfile(source):  # noqa: PTH113
                os.remove(source)  # noqa: PTH107
            else:
                shutil.rmtree(source, ignore_errors=True, onerror=self.logger.exception)
        elif operation == FileOperation.RENAME:
            assert destination is not None, "Destination is None"
            os.rename(source, destination)  # noqa: PTH104
        self.logger.info(f"Completed file operation: {operation} - {source} to {destination}")
        return operation, source, destination

    def setup_file_operations(self):
        self.file_operation_queue.clear()
        QTimer.singleShot(0, self.process_file_operations)

    def add_file_operation(
        self,
        operation: FileOperation,
        source: str,
        destination: str | None = None,
        callback: Callable[[Any], None] | None = None,
        error_callback: Callable[[Exception], None] | None = None,
    ) -> None:
        task = functools.partial(self._execute_file_operation, operation, source, destination)
        self._task_queue.put((task, callback, error_callback))
        self.logger.info(f"Added file operation: {operation} - {source} to {destination}")

    def run_in_background(self, func: Callable[..., Any], *args: Any, callback: Callable | None = None, error_callback: Callable | None = None) -> None:
        task = functools.partial(func, *args)
        self._task_queue.put((task, callback, error_callback))

    def process_file_operations(self):
        if not self.file_operation_queue:
            return

        operation, source, destination = self.file_operation_queue.pop(0)
        progress_dialog = QProgressDialog("Processing file operation...", "Cancel", 0, 100, self)
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.setAutoClose(True)
        progress_dialog.setAutoReset(True)

        def operation_callback(result: tuple[str, str, str | None]):
            self.logger.info(f"File operation completed: {result}")
            self.refresh_view()
            QTimer.singleShot(0, self.process_file_operations)

        self.run_in_background(
            self._execute_file_operation,
            operation,
            source,
            destination,
            callback=operation_callback,
        )

    def lazy_load_directory(self, root_index: QModelIndex):
        total_items = self._fs_model.rowCount(root_index)
        start = 0
        end = min(self.lazy_load_batch_size, total_items)

        while start < total_items:
            for i in range(start, end):
                self._fs_model.fetchMore(self._fs_model.index(i, 0, root_index))
            start = end
            end = min(end + self.lazy_load_batch_size, total_items)

        self.logger.debug(f"Finished lazy loading directory: {self._currentPath}")

    def _handle_result(self, result: Any) -> None:
        if isinstance(result, tuple) and len(result) == 3:
            task, value, error = result
            if error:
                self.logger.error(f"Task error: {error}")
                QMessageBox.critical(self, "Error", f"Task error: {error}")
                if isinstance(task, tuple) and len(task) > 2 and callable(task[2]):
                    task[2](error)  # Call error_callback if available
            else:
                self.logger.info(f"Task completed: {value}")
                if isinstance(task, tuple) and len(task) > 1 and callable(task[1]):
                    task[1](value)  # Call callback if available
        else:
            self.logger.warning(f"Unexpected result format: {result}")
        self.refresh_view()

    def history(self) -> list[str]:
        return self._history

    def setHistory(self, history: list[str]):
        self._history = history

    def options(self) -> QFileDialog.Option | QFileDialog.Options:
        return self._options

    def setOptions(self, options: QFileDialog.Option | QFileDialog.Options):
        self._options = options

    def fileMode(self) -> QFileDialog.FileMode | int:
        return self._fileMode

    def setFileMode(self, mode: int):
        self._fileMode = mode

    def acceptMode(self) -> QFileDialog.AcceptMode | int:
        return self._acceptMode

    def setAcceptMode(self, mode: int):
        self._acceptMode = mode
        self.buttonBox.button(QDialogButtonBox.Ok).setText("Open" if mode == QFileDialog.AcceptMode.AcceptOpen else "Save")
        self.fileNameLabel.setText("File name:" if mode == QFileDialog.AcceptMode.AcceptOpen else "Save As:")

    def viewMode(self) -> QFileDialog.ViewMode | int:
        return self._viewMode

    def setViewMode(self, mode: int):
        self._viewMode = mode
        self.setCurrentIndex(mode)
        self.listModeButton.setChecked(mode == QFileDialog.ViewMode.List)
        self.detailModeButton.setChecked(mode == QFileDialog.ViewMode.Detail)
        if mode == QFileDialog.ViewMode.Detail:
            self.side_panel_tree.setColumnWidth(0, self.side_panel_tree.width() // 2)

    def current_path(self) -> str:
        return self._currentPath

    def set_current_path(self, path: str):
        self._currentPath = path

    def selectedFiles(self) -> list[str]:
        return self._selectedFiles

    def get_file_info(self, index):
        file_path = self._fs_model.filePath(index)
        file_info = QFileInfo(file_path)
        return f"Name: {file_info.fileName()}\nSize: {file_info.size()} bytes"

    def setup_logging(self, log_file: str = "pyfileexplorer.log"):
        logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", filemode="w")
        logging.getLogger().addHandler(logging.StreamHandler())  # Add console output
        logging.getLogger().setLevel(logging.INFO)  # Set to INFO for production, DEBUG for development
        self.logger = logging.getLogger(__name__)

    def setup_sidebar(self):
        self._sidebarUrls: list[QUrl] = [
            QUrl.fromLocalFile(QDir.homePath()),
            QUrl.fromLocalFile(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DesktopLocation)),
            QUrl.fromLocalFile(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)),
            QUrl.fromLocalFile(QDir.rootPath()),
        ] + [QUrl.fromLocalFile(path) for path in QStandardPaths.standardLocations(QStandardPaths.StandardLocation.MusicLocation)]
        self.update_sidebar()

    def setup_ui(self, caption: str):
        self.setWindowTitle(caption or "Select File")
        main_layout = QVBoxLayout(self)

        # Look In section
        look_in_layout = QHBoxLayout()
        self.lookInLabel: QLabel = QLabel("Look in:", self)
        self.addressBar: QLineEdit = QLineEdit(self)
        self.backButton = QToolButton(self)
        self.backButton.setIcon(self.style().standardIcon(self.style().SP_ArrowBack))
        self.forwardButton: QToolButton = QToolButton(self)
        self.forwardButton.setIcon(self.style().standardIcon(self.style().SP_ArrowForward))
        self.toParentButton: QToolButton = QToolButton(self)
        self.toParentButton.setIcon(self.style().standardIcon(self.style().SP_ArrowUp))
        self.newFolderButton: QToolButton = QToolButton(self)
        self.newFolderButton.setIcon(self.style().standardIcon(self.style().SP_FileDialogNewFolder))
        self.listModeButton: QToolButton = QToolButton(self)
        self.listModeButton.setIcon(self.style().standardIcon(self.style().SP_FileDialogListView))
        self.detailModeButton: QToolButton = QToolButton(self)
        self.detailModeButton.setIcon(QIcon.fromTheme("view-list-details"))

        look_in_layout.addWidget(self.lookInLabel)
        look_in_layout.addWidget(self.addressBar)
        look_in_layout.addWidget(self.backButton)
        look_in_layout.addWidget(self.forwardButton)
        look_in_layout.addWidget(self.toParentButton)
        look_in_layout.addWidget(self.newFolderButton)
        look_in_layout.addWidget(self.listModeButton)
        look_in_layout.addWidget(self.detailModeButton)

        self.toggleDualPaneButton: QToolButton = QToolButton(self)
        self.toggleDualPaneButton.setIcon(QIcon.fromTheme("view-split-left-right"))
        self.toggleDualPaneButton.setCheckable(True)
        self.toggleDualPaneButton.setChecked(True)
        self.toggleDualPaneButton.clicked.connect(self.toggle_dual_pane)
        look_in_layout.addWidget(self.toggleDualPaneButton)

        main_layout.addLayout(look_in_layout)

        # Main content area
        content_splitter = QSplitter(Qt.Horizontal)

        # Sidebar
        self.sidebarDock = QDockWidget("Folders", self)
        self.side_panel_tree: RobustTreeView = RobustTreeView()
        self.side_panel_tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.side_panel_tree.setModel(self.fsModel)
        self.side_panel_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.side_panel_tree.customContextMenuRequested.connect(self.show_context_menu)
        self.sidebarDock.setWidget(self.side_panel_tree)
        content_splitter.addWidget(self.sidebarDock)

        # Dual-pane view
        self.dual_pane_splitter = QSplitter(Qt.Horizontal)

        # Left pane
        self.left_pane = self.create_file_view()
        self.dual_pane_splitter.addWidget(self.left_pane)

        # Right pane
        self.right_pane = self.create_file_view()
        self.dual_pane_splitter.addWidget(self.right_pane)

        content_splitter.addWidget(self.dual_pane_splitter)
        content_splitter.setSizes([200, 800])

        main_layout.addWidget(content_splitter)

        # Setup file system model
        self.fsModel: QFileSystemModel = QFileSystemModel(self)
        self.fsModel.setRootPath(QDir.rootPath())
        self.side_panel_tree.setModel(self.fsModel)
        self.left_pane.setModel(self.fsModel)
        self.right_pane.setModel(self.fsModel)
        self.side_panel_tree.clicked.connect(self.on_sidebar_item_clicked)

        # File name section
        file_name_layout = QHBoxLayout()
        self.fileNameLabel: QLabel = QLabel("File name:", self)
        self.fileNameEdit: QLineEdit = QLineEdit(self)
        self.fileNameEdit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        file_name_layout.addWidget(self.fileNameLabel)
        file_name_layout.addWidget(self.fileNameEdit)

        main_layout.addLayout(file_name_layout)

        # File type section
        file_type_layout = QHBoxLayout()
        self.fileTypeLabel: QLabel = QLabel("Files of type:", self)
        self.fileTypeCombo: QComboBox = QComboBox(self)
        self.fileTypeCombo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.fileTypeCombo.setEditable(True)
        file_type_layout.addWidget(self.fileTypeLabel)
        file_type_layout.addWidget(self.fileTypeCombo)

        main_layout.addLayout(file_type_layout)

        # Buttons
        self.buttonBox: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setText("Open" if self._acceptMode == QFileDialog.AcceptMode.AcceptOpen else "Save")
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancel")
        main_layout.addWidget(self.buttonBox)

        self.setLayout(main_layout)

    def create_file_view(self) -> QTreeView:
        view = QTreeView()
        view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        view.customContextMenuRequested.connect(self.show_context_menu)
        return view

    def close_tab(self, index: int):
        self.tabWidget.removeTab(index)

    def setup_menu(self):
        menubar = QMenuBar(self)
        self.layout().setMenuBar(menubar)

        # File menu
        file_menu = menubar.addMenu("File")
        file_menu.addAction("New Folder", self.create_new_folder, QKeySequence.StandardKey.New)
        file_menu.addAction("Open", self.open, QKeySequence.StandardKey.Open)
        file_menu.addAction("Delete", self.delete_file, QKeySequence.StandardKey.Delete)
        file_menu.addSeparator()
        file_menu.addAction("Exit", cast(QApplication, QApplication.instance()).quit, QKeySequence.StandardKey.Quit)  # pyright: ignore[reportCallIssue, reportArgumentType]

        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        edit_menu.addAction("Cut", self.cut_file, QKeySequence.StandardKey.Cut)
        edit_menu.addAction("Copy", self.copy_file, QKeySequence.StandardKey.Copy)
        edit_menu.addAction("Paste", self.paste_file, QKeySequence.StandardKey.Paste)

        # View menu
        view_menu = menubar.addMenu("View")
        view_menu.addAction("list View", lambda: self.setViewMode(QFileDialog.ViewMode.List))
        view_menu.addAction("Detail View", lambda: self.setViewMode(QFileDialog.ViewMode.Detail))
        view_menu.addAction("Refresh", self.refresh_view, QKeySequence.StandardKey.Refresh)
        view_menu.addSeparator()
        view_menu.addAction("New Tab", self.new_tab, QKeySequence.AddTab)
        view_menu.addAction("Disk Usage", self.show_disk_usage)
        view_menu.addAction("Secure Delete", self.secure_delete)
        view_menu.addAction("Recent Directories", self.show_recent_directories)

    def setup_tooltips(self):
        for view in self.stackedWidget.all_views:
            view.setToolTip("Double-click to open")

    def setup_connections(self):
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.backButton.clicked.connect(self.go_back)
        self.forwardButton.clicked.connect(self.go_forward)
        self.toParentButton.clicked.connect(self.go_to_parent)
        self.newFolderButton.clicked.connect(self.create_new_folder)
        self.listModeButton.clicked.connect(lambda: self.setViewMode(QFileDialog.ViewMode.List))
        self.detailModeButton.clicked.connect(lambda: self.setViewMode(QFileDialog.ViewMode.Detail))
        self.toggleHiddenButton.clicked.connect(self.toggle_hidden_files)
        self.addressBar.returnPressed.connect(self.navigate_to_address)
        self.fileNameEdit.returnPressed.connect(self.on_file_name_return)
        self.left_pane.doubleClicked.connect(self.on_item_double_clicked)
        self.right_pane.doubleClicked.connect(self.on_item_double_clicked)
        self.fileTypeCombo.currentTextChanged.connect(self.on_filter_changed)
        self.left_pane.setDragEnabled(True)
        self.right_pane.setDragEnabled(True)
        self.fsModel.directoryLoaded.connect(self.on_directory_loaded)
        self.left_pane.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.right_pane.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.fileNameEdit.editingFinished.connect(self.on_file_name_changed)
        self.left_pane.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.right_pane.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.left_pane.customContextMenuRequested.connect(self.show_context_menu)
        self.right_pane.customContextMenuRequested.connect(self.show_context_menu)
        self.left_pane.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.right_pane.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)

        # Load session
        self.load_session()
        self.update_navigation_buttons()

    def toggle_dual_pane(self):
        if self.toggleDualPaneButton.isChecked():
            self.right_pane.show()
        else:
            self.right_pane.hide()

    def go_back(self):
        if self._history_index > 0:
            self._history_index -= 1
            self.setDirectory(self._history[self._history_index], add_to_history=False)
        self.update_navigation_buttons()

    def go_forward(self):
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            self.setDirectory(self._history[self._history_index], add_to_history=False)
        self.update_navigation_buttons()

    def update_navigation_buttons(self):
        self.backButton.setEnabled(self._history_index > 0)
        self.forwardButton.setEnabled(self._history_index < len(self._history) - 1)

    def refresh_view(self):
        self.setDirectory(self._currentPath)

    def go_to_parent(self):
        parent_path = os.path.dirname(self._currentPath)  # noqa: PTH120
        self.setDirectory(parent_path)

    def create_new_folder(self):
        self.create_new_folder_in(self._currentPath)

    def create_new_folder_in(self, directory: str):
        new_folder_name, ok = QInputDialog.getText(self, "Create New Folder", "Folder name:")
        if ok and new_folder_name:
            new_folder_path = os.path.join(directory, new_folder_name)  # noqa: PTH118
            try:
                os.makedirs(new_folder_path)  # noqa: PTH103
                self.setDirectory(directory)  # Refresh the view
                self.logger.info(f"Created new folder: {new_folder_path}")
            except OSError:
                self.logger.exception("Failed to create folder")
                QMessageBox.warning(self, "Error", "Failed to create folder")

    def navigate_to_address(self):
        path = self.addressBar.text()
        if Path(path) == Path(self._currentPath):
            return
        self.setDirectory(path)

    def on_file_name_return(self):
        file_name = self.fileNameEdit.text()
        if not file_name or not file_name.strip():
            return
        full_path = os.path.join(self._currentPath, file_name)  # noqa: PTH118
        if os.path.isdir(full_path):  # noqa: PTH112
            self.setDirectory(full_path)
        else:
            self.selectFile(full_path)
            self.accept()

    def on_item_double_clicked(self, index: QModelIndex):
        sender = self.sender()
        model = sender.model()
        assert isinstance(model, QFileSystemModel), "Invalid model type: " + type(model).__name__
        path = model.filePath(index)
        if os.path.isdir(path):  # noqa: PTH112
            self.setDirectory(path, pane=sender)
        else:
            QToolTip.showText(QCursor.pos(), self.get_file_info(index))
            self.selectFile(path)
            self.accept()

    def on_directory_loaded(self, path: str):
        self.currentChanged.emit(self._currentPath)

    def on_filter_changed(self, new_filter: str):
        self.setNameFilter(new_filter)

    def on_file_name_changed(self, text: str):
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(bool(text))

    def on_sidebar_item_clicked(self, index: QModelIndex):
        path = self._fs_model.filePath(index)
        self.setDirectory(path)

    @staticmethod
    def filter_files(directory: str, current_filter: str) -> list[str]:
        filtered_files: list[str] = []
        filter_parts: list[str] = current_filter.split("(")
        extensions: list[str] = filter_parts[1].strip(")").split() if len(filter_parts) > 1 else ["*"]
        for file_name in os.listdir(directory):
            if current_filter == "All Files (*)" or any(
                fnmatch.fnmatch(file_name.lower(), ext.lower())
                for ext in extensions
            ):
                filtered_files.append(file_name)
            else:
                mime_type, _ = mimetypes.guess_type(file_name)
                if os.path.isdir(os.path.join(directory, file_name)) or (  # noqa: PTH118, PTH112
                    mime_type and any(
                        fnmatch.fnmatch(mime_type, ext.lower().strip("*"))
                        for ext in extensions
                    )
                ):
                    filtered_files.append(file_name)
        return filtered_files

    def update_file_list(self, filtered_files: list[str]):
        self._fs_model.setNameFilters(filtered_files)
        self._fs_model.setNameFilterDisables(not self.testOption(QFileDialog.Option.HideNameFilterDetails))

    def expand_sidebar_to_current_directory(self, directory: str):
        index = self._fs_model.index(os.path.abspath(directory))  # noqa: PTH100
        while index.isValid():
            self.side_panel_tree.expand(index)
            index = index.parent()

    def update_sidebar(self):
        self.side_panel_tree.blockSignals(True)  # noqa: FBT003
        for url in self.sidebarUrls():
            index = self._fs_model.index(url.toLocalFile())
            if index.isValid():
                self.side_panel_tree.setCurrentIndex(index)
                self.side_panel_tree.scrollTo(index)
            self.side_panel_tree.setExpanded(index, True)  # noqa: FBT003
        self.side_panel_tree.blockSignals(False)  # noqa: FBT003

    def on_selection_changed(self, selected: QItemSelection, deselected: QItemSelection):
        selected_indexes = selected.indexes()
        if selected_indexes:
            model = cast(QAbstractItemView, self.sender()).model()
            assert isinstance(model, QFileSystemModel)
            file_path = model.filePath(selected_indexes[0])
            self.fileNameEdit.setText(QFileInfo(file_path).fileName())
            if len(selected_indexes) == 1:
                self.fileSelected.emit(file_path)
            self.filesSelected.emit([model.filePath(index) for index in selected_indexes])
        else:
            self.fileNameEdit.clear()
            self.fileSelected.emit("")
            self.filesSelected.emit([])

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Backspace:
            self.go_to_parent()
        elif event.matches(QKeySequence.StandardKey.Refresh):
            self.setDirectory(self._currentPath)
        else:
            super().keyPressEvent(event)

    def show_context_menu(self, pos: QPoint):
        sender = self.sender()
        assert isinstance(sender, QAbstractItemView)
        global_pos = sender.mapToGlobal(pos)
        index = sender.indexAt(pos)

        menu = QMenu(self)
        open_action = menu.addAction(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon), "Open")
        open_action.setToolTip("Open the selected file or folder")
        open_action.setWhatsThis("Opens the selected file or folder.")
        rename_action = menu.addAction(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView), "Rename")
        rename_action.setToolTip("Rename the selected file or folder")
        rename_action.setWhatsThis("Allows you to rename the selected file or folder.")
        delete_action = menu.addAction(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon), "Delete")
        delete_action.setToolTip("Delete the selected file or folder")
        delete_action.setWhatsThis("Deletes the selected file or folder. This action cannot be undone.")
        compress_action = menu.addAction(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton), "Compress")
        compress_action.setToolTip("Compress the selected file or folder")
        compress_action.setWhatsThis("Compresses the selected file or folder into a zip archive.")
        extract_action = menu.addAction(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton), "Extract")
        extract_action.setToolTip("Extract the selected compressed file")
        extract_action.setWhatsThis("Extracts the contents of the selected compressed file.")
        properties_action = menu.addAction(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogInfoView), "Properties")
        properties_action.setToolTip("View properties of the selected file or folder")
        properties_action.setWhatsThis("Shows detailed properties of the selected file or folder.")
        calculate_checksum_action = menu.addAction(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton), "Calculate Checksum")
        calculate_checksum_action.setToolTip("Calculate checksum of the selected file")
        calculate_checksum_action.setWhatsThis("Calculates and displays the SHA256 checksum of the selected file.")
        compare_files_action = menu.addAction(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView), "Compare Files")
        compare_files_action.setToolTip("Compare two selected files")
        compare_files_action.setWhatsThis("Compares the contents of two selected files and shows the differences.")
        secure_delete_action = menu.addAction(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogResetButton), "Secure Delete")
        secure_delete_action.setToolTip("Securely delete the selected file")
        secure_delete_action.setWhatsThis("Securely deletes the selected file by overwriting its contents before deletion.")

        action = menu.exec_(global_pos)

        file_path = self._fs_model.filePath(index)

        if action == open_action:
            self.on_item_double_clicked(index)
        elif action == rename_action:
            self.rename_file(index)
        elif action == delete_action:
            self.delete_file(index)
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

    def __reduce__(self):
        return (QFileDialog, ())

    def calculate_checksum(self, file_path: str):
        task = Task(
            generate_hash,
            (file_path, "sha256"),
            callback=Callback(
                QMessageBox.information,
                (None, "Checksum Result", "Checksum for: %s : %s"),
            ),
        )
        # Usage:
        # hash = generate_hash(file_path, "sha256")
        # task(hash)
        self._task_queue.put(task)

    def rename_file(self, index: QModelIndex):
        model = cast(QAbstractItemView, self.sender()).model()
        assert isinstance(model, QFileSystemModel)
        old_name = model.fileName(index)
        new_name, ok = QInputDialog.getText(self, "Rename", "New name:", QLineEdit.Normal, old_name)
        if ok and new_name:
            old_path = model.filePath(index)
            new_path = os.path.join(os.path.dirname(old_path), new_name)  # noqa: PTH120, PTH118
            self.add_file_operation(FileOperation.RENAME, old_path, new_path)

    def delete_file(self, index: QModelIndex):
        model = cast(QAbstractItemView, self.sender()).model()
        assert isinstance(model, QFileSystemModel)
        file_path = model.filePath(index)
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete {file_path}:",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.add_file_operation("delete", file_path)
            self.setDirectory(self._currentPath)  # Refresh the view

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
            error_msg = f"Could not compress file(s): {e}"
            self.logger.exception(error_msg)
            QMessageBox.warning(self, "Error", error_msg)

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

    def get_selected_files(self) -> list[str]:
        selected_files = []
        for view in [self.listView(), self.tableView(), self.tilesView()]:
            assert isinstance(view, QAbstractItemView)
            selected_indexes = view.selectedIndexes()
            for index in selected_indexes:
                file_path = self._fs_model.filePath(index)
                if file_path not in selected_files:
                    selected_files.append(file_path)
        return selected_files

    def compare_files(self):
        selected_files = self.get_selected_files()
        if len(selected_files) != 2:
            error_msg = "Please select exactly two files to compare."
            self.logger.warning(error_msg)
            QMessageBox.warning(self, "Error", error_msg)
            return
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
            self.logger.info(f"Compared files: {selected_files[0]} and {selected_files[1]}")
        except Exception as e:  # noqa: BLE001
            error_msg = f"Error comparing files: {e}"
            self.logger.exception(error_msg)
            QMessageBox.warning(self, "Error", error_msg)

    @overload
    def open(self) -> None: ...
    @overload
    def open(self, slot) -> None: ...  # noqa: ANN001
    def open(self, slot=None):
        selected_files = self.get_selected_files()
        if not selected_files:
            QMessageBox.warning(self, "Error", "Please select a file to open.")
            return
        file_path = selected_files[0]
        url = QUrl.fromLocalFile(file_path)
        QDesktopServices.openUrl(url)

    def setVisible(self, visible: bool):  # noqa: FBT001
        super().setVisible(visible)
        if visible:
            self.refresh_view()

    def selectUrl(self, url: QUrl):
        self.selectFile(url.toLocalFile())

    def selectedUrls(self) -> list[QUrl]:
        return [QUrl.fromLocalFile(file) for file in self.selectedFiles()]

    def directoryUrl(self) -> QUrl:
        return QUrl.fromLocalFile(self._currentPath)

    def setDirectoryUrl(self, directory: QUrl):
        self.setDirectory(directory.toLocalFile())

    def supportedSchemes(self) -> list[str]:
        return ["file"]  # We only support local files for now

    def setSupportedSchemes(self, schemes: list[str]):
        # We don't actually change the supported schemes, but we'll log it
        self.logger.info(f"Attempted to set supported schemes: {schemes}")
        self.logger.warning("PyFileExplorer only supports 'file' scheme")

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
            self.logger.info(f"Securely deleted file: {file_path}")
            self.refresh_view()
        except Exception as e:  # noqa: BLE001
            error_msg = f"Error securely deleting file: {e}"
            self.logger.exception(error_msg)
            QMessageBox.warning(self, "Error", error_msg)

    def show_disk_usage(self):
        try:
            import psutil
        except ImportError:
            QMessageBox.warning(self, "Error", "psutil is not installed. Please install psutil to use this feature.")
            return
        disk_usage = psutil.disk_usage(self._currentPath)
        usage_dialog = QDialog(self)
        usage_dialog.setWindowTitle("Disk Usage")
        layout = QVBoxLayout(usage_dialog)
        layout.addWidget(QLabel(f"Total: {self.format_size(disk_usage.total)}"))
        layout.addWidget(QLabel(f"Used: {self.format_size(disk_usage.used)} ({disk_usage.percent}%)"))
        layout.addWidget(QLabel(f"Free: {self.format_size(disk_usage.free)}"))
        usage_dialog.exec_()
        self.logger.info(f"Displayed disk usage for {self._currentPath}")

    def format_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:  # noqa: PLR2004
                return f"{size:.2f} {unit}"
            size = int(size / 1024.0)
        return "N/A"

    def get_disk_info(self):
        try:
            import psutil

            usage = psutil.disk_usage(self._currentPath)
            return f"Total: {self.format_size(usage.total)}, " f"Used: {self.format_size(usage.used)} ({usage.percent}%), " f"Free: {self.format_size(usage.free)}"
        except Exception as e:  # noqa: BLE001
            error_msg = f"Error getting disk info: {e}"
            self.logger.exception(error_msg)
            return "N/A"

    def format_permissions(self, path: str) -> str:
        try:
            return oct(os.stat(path).st_mode)[-3:]  # noqa: PTH116
        except Exception:  # noqa: BLE001
            self.logger.exception(f"Error getting permissions for {path}")
            return "N/A"

    def show_recent_directories(self):
        show_hidden = self.toggleHiddenButton.isChecked()
        self._fs_model.setFilter(self._fs_model.filter() | QDir.Hidden if show_hidden else self._fs_model.filter() & ~QDir.Hidden)
        self.refresh_view()
        menu = QMenu("Recent Directories", self)
        for directory in self.recent_directories:
            action = menu.addAction(directory)
            action.triggered.connect(lambda _, folder=directory: self.setDirectory(folder))
        if not self.recent_directories:
            menu.addAction("No recent directories")
        menu.exec_(QCursor.pos())

    def directory(self) -> QDir:
        return QDir(self._currentPath)

    def setDirectory(self, directory: str | QDir, *, add_to_history: bool = True, pane: QTreeView | None = None):
        abs_directory = (
            directory.absolutePath() if isinstance(directory, QDir) else os.path.abspath(directory)  # noqa: PTH100
        )
        if not abs_directory or not os.path.isdir(abs_directory):  # noqa: PTH112
            self.logger.warning(f"Invalid directory: {abs_directory}")
            return

        self.fsModel.setRootPath(abs_directory)
        root_index = self.fsModel.index(abs_directory)

        if pane is None or pane == self.left_pane:
            self.left_pane.setRootIndex(root_index)
            self._currentPath = abs_directory
            self.addressBar.setText(abs_directory)
            self.currentChanged.emit(self._currentPath)
            if add_to_history:
                # Add to history and update the index
                if self._history_index < len(self._history) - 1:
                    self._history = self._history[: self._history_index + 1]
                self._history.append(abs_directory)
                self._history_index += 1

        if pane is None or pane == self.right_pane:
            self.right_pane.setRootIndex(root_index)

        self.update_navigation_buttons()
        self.save_session()
        self.directoryEntered.emit(abs_directory)
        self.expand_sidebar_to_current_directory(abs_directory)
        self.update_sidebar()
        self.lazy_load_directory(root_index)
        self.logger.debug(f"Set directory to: {abs_directory}")

    def set_left_pane_directory(self, directory: str | QDir):
        self.setDirectory(directory, pane=self.left_pane)

    def set_right_pane_directory(self, directory: str | QDir):
        self.setDirectory(directory, pane=self.right_pane)

    def setNameFilters(self, filters: list[str]):
        self._nameFilters = filters
        self.fileTypeCombo.clear()
        self.fileTypeCombo.addItems(self._nameFilters)
        self.apply_filter(self._nameFilters[0] if self._nameFilters else "*")

    def setNameFilter(self, file_filter: str):
        self.apply_filter(file_filter)

    def apply_filter(self, file_filter: str | None = None):
        current_filter = self.fileTypeCombo.currentText()
        self.filterSelected.emit(current_filter)

        # Create a QSortFilterProxyModel if it doesn't exist
        if not hasattr(self, "_proxyModel"):
            self._proxyModel = QSortFilterProxyModel(self)
            self._proxyModel.setSourceModel(self._fs_model)

        # Set the file_filter on the proxy model
        self._proxyModel.setFilterRegExp(file_filter or current_filter)
        self._proxyModel.setFilterKeyColumn(0)  # Filter on the first column (file name)

    def selectFile(self, file_name: str):
        self.fileNameEdit.setText(file_name)
        self._selectedFiles = [file_name]
        self.fileSelected.emit(file_name)

    def selectedNameFilter(self) -> str:
        return self.fileTypeCombo.currentText()

    def setOption(self, option: int, on: bool = True):  # noqa: FBT001, FBT002
        self._options = (self._options | option) if on else (self._options & ~option)  # pyright: ignore[reportAttributeAccessIssue]

    def testOption(self, option: int) -> bool:
        return bool(self._options & option)

    def setMimeTypeFilters(self, filters: list[str]):
        self.mime_type_filters = filters
        self.fileTypeCombo.clear()
        self.fileTypeCombo.addItems(self.mime_type_filters)
        self.apply_filter()

    def setSidebarUrls(self, urls: list[QUrl]):
        self._sidebarUrls = urls
        self.update_sidebar()

    def sidebarUrls(self) -> list[QUrl]:
        return self._sidebarUrls

    def setDefaultSuffix(self, suffix: str):
        if suffix.startswith("."):
            suffix = suffix[1:]
        self._defaultSuffix: str = suffix

    getOpenFileName = QFileDialog.getOpenFileName
    getOpenFileNames = QFileDialog.getOpenFileNames
    getExistingDirectory = QFileDialog.getExistingDirectory
    getExistingDirectoryUrl = QFileDialog.getExistingDirectoryUrl
    getOpenFileUrl = QFileDialog.getOpenFileUrl
    getOpenFileUrls = QFileDialog.getOpenFileUrls
    getSaveFileUrl = QFileDialog.getSaveFileUrl
    getSaveFileName = QFileDialog.getSaveFileName
    saveFileContent = QFileDialog.saveFileContent

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        elif event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()
        else:
            self.logger.warning("Unknown mime data format: %s", event.mimeData().formats())

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            urls: list[QUrl] = event.mimeData().urls()
            for url in urls:
                file_path = url.toLocalFile()
                if os.path.isdir(file_path):  # noqa: PTH112
                    self.setDirectory(file_path)
                else:
                    self.copy_file(file_path, self._currentPath)
        elif event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            source_widget = cast(QAbstractItemView, event.source())
            if source_widget != self.sender():
                indexes = source_widget.selectedIndexes()
                for index in indexes:
                    source_path: str = self._fs_model.filePath(index)
                    self.copy_file(source_path, self._currentPath)
        else:
            self.logger.warning("Unknown mime data format: %s", event.mimeData().formats())
        self.refresh_view()

    def copy_file(self, source: str, destination: str):
        self.add_file_operation(FileOperation.COPY, source, destination)

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
            self._selectedFiles = [self.fileNameEdit.text()]
        if self._acceptMode == QFileDialog.AcceptMode.AcceptSave and self._defaultSuffix and not self._selectedFiles[0].endswith(self._defaultSuffix):
            self._selectedFiles[0] += f".{self._defaultSuffix}"
        super().accept()

    def setLabelText(self, label: str, text: str):
        if label == QFileDialog.FileName:
            self.fileNameLabel.setText(text)
        elif label == QFileDialog.Accept:
            self.buttonBox.button(QDialogButtonBox.Ok).setText(text)
        elif label == QFileDialog.Reject:
            self.buttonBox.button(QDialogButtonBox.Cancel).setText(text)
        elif label == QFileDialog.LookIn:
            self.lookInLabel.setText(text)
        elif label == QFileDialog.FileType:
            self.fileTypeLabel.setText(text)
        else:
            self.logger.warning(f"Unknown label: '{label}' sent with text: '{text}'")

    def whatsThis(self) -> str:
        return """
        PyFileExplorer: A custom file dialog with advanced features.

        - Address Bar: Enter a path to navigate directly to that location.
        - Back/Forward Buttons: Navigate through your browsing history.
        - Up Button: Go to the parent directory.
        - New Folder Button: Create a new folder in the current directory.
        - List/Detail View Buttons: Switch between different view modes.
        - Toggle Hidden Button: Show or hide hidden files and folders.
        - What's This Button: Get detailed information about specific elements.

        Use the file list to browse and select files. Double-click to open folders or select files.
        The file name field shows the currently selected file or can be used to enter a specific file name.
        Use the file type dropdown to filter the displayed files.
        """

    def __del__(self):
        self.logger.info("PyFileExplorer instance destroyed")
        self._abort.set()
        for consumer in self._consumers:
            consumer.stop()
        for consumer in self._consumers:
            consumer.join()

    def cut_file(self):
        self.copy_file(source=self._fs_model.filePath(self.current_view().currentIndex()), destination=self._currentPath)
        self.delete_file(self.current_view().currentIndex())
        for i in range(1, self.tabWidget.count()):
            widget: QAbstractItemView | None = self.tabWidget.widget(i).findChild(QAbstractItemView)
            if widget is None:
                continue
            self.delete_file(widget.currentIndex())

    def paste_file(self):
        for i in range(self.tabWidget.count()):
            widget: QAbstractItemView | None = self.tabWidget.widget(i).findChild(QAbstractItemView)
            if widget is None:
                continue
            self.copy_file(source=self._fs_model.filePath(widget.currentIndex()), destination=self._currentPath)

    def new_tab(self):
        new_tab_index: int = self.tabWidget.addTab(self.stackWidget, f"Tab {self.tabWidget.count() + 1}")
        self.tabWidget.setCurrentIndex(new_tab_index)

    def save_session(self):
        self.settings = QSettings("YourOrganizationName", "YourAppName")
        self.settings.setValue("recentDirectories", list(self.recent_directories))
        self.settings.setValue("lastDirectory", self._currentPath)
        self.settings.setValue("viewMode", self.viewMode())
        self.settings.setValue("splitterState", self.saveState())
        self.settings.setValue("tabIndex", self.tabWidget.currentIndex())
        for i in range(self.tabWidget.count()):
            widget: QAbstractItemView | None = self.tabWidget.widget(i).findChild(QAbstractItemView)
            if widget is None:
                self.settings.setValue(f"tab{i}Path", "")
                continue
            self.settings.setValue(f"tab{i}Path", self._fs_model.filePath(widget.currentIndex()))

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
            self.setViewMode(int(view_mode))
        splitter_state = self.settings.value("splitterState")
        if splitter_state:
            self.restoreState(splitter_state)
        tab_index = self.settings.value("tabIndex")
        if tab_index:
            self.tabWidget.setCurrentIndex(int(tab_index))
        for i in range(self.tabWidget.count()):
            tab_path = self.settings.value(f"tab{i}Path")
            if tab_path and os.path.isdir(tab_path):  # noqa: PTH112
                self.setDirectory(tab_path, add_to_history=False)


if __name__ == "__main__":
    app = QApplication([])
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    explorer = PyFileExplorer()
    explorer.show()

    with loop:
        loop.run_forever()
    def sync_panes(self):
        active_pane = self.focusWidget()
        if active_pane == self.left_pane:
            self.set_right_pane_directory(self.fsModel.filePath(self.left_pane.rootIndex()))
        elif active_pane == self.right_pane:
            self.set_left_pane_directory(self.fsModel.filePath(self.right_pane.rootIndex()))

    def setup_connections(self):
        # ... (existing connections)
        self.toggleDualPaneButton.clicked.connect(self.toggle_dual_pane)

        # Add a new button for syncing panes
        self.syncPanesButton = QToolButton(self)
        self.syncPanesButton.setIcon(QIcon.fromTheme("view-refresh"))
        self.syncPanesButton.clicked.connect(self.sync_panes)
        self.layout().itemAt(0).layout().addWidget(self.syncPanesButton)
