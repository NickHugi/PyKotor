from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys

from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Generic, TypeVar, cast

from PyQt5.QtCore import QFile, QItemSelectionModel
from PySide2.QtCore import QIODevice
from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy.QtCore import (
    QDir,
    QMimeData,
    QModelIndex,
    QSize,
    QSortFilterProxyModel,
    QUrl,
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QIcon, QPalette, QStandardItemModel
from qtpy.QtWidgets import (
    QAction,
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
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from utility.ui_libraries.qt.common.actions_dispatcher import MenuActionsDispatcher
from utility.ui_libraries.qt.common.filesystem.preview_widget import PreviewWidget
from utility.ui_libraries.qt.common.tasks.actions_executor import FileActionsExecutor
from utility.ui_libraries.qt.common.tasks.task_details_dialog import TaskDetailsDialog
from utility.ui_libraries.qt.filesystem.qfiledialogextended.explorer_ui import Ui_QFileExplorer

if TYPE_CHECKING:

    from types import TracebackType

    from PyQt5.QtGui import QResizeEvent
    from qtpy.QtCore import QFileInfo, QModelIndex, QPoint
    from qtpy.QtGui import QDragEnterEvent, QDropEvent
    from qtpy.QtWidgets import QWidget


class FileOperation(Enum):
    COPY = auto()
    MOVE = auto()
    DELETE = auto()
    RENAME = auto()


T = TypeVar("T")


class Task(Generic[T]):
    def __init__(
        self,
        func: Callable[..., T],
        args: tuple[Any, ...],
        callback: Callable[[T], None] | None = None,
        error_callback: Callable[[Exception], None] | None = None,
    ):
        self.func: Callable[..., T] = func
        self.args: tuple[Any, ...] = args
        self.callback: Callable[[T], None] | None = callback
        self.error_callback: Callable[[Exception], None] | None = error_callback

    def __call__(self):
        try:
            result = self.func(*self.args)
            if self.callback:
                self.callback(result)
        except Exception as e:  # noqa: BLE001
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


class FileSystemExplorerWidget(QMainWindow):
    file_selected = Signal(str)
    directory_changed = Signal(str)
    open_in_new_tab = Signal(str)

    def __init__(
        self,
        initial_path: os.PathLike | str | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.ui: Ui_QFileExplorer = Ui_QFileExplorer()
        self.ui.setupUi(self)

        # Initialize basic attributes
        self.current_path: Path = Path.home() if initial_path is None else Path(initial_path)
        self.navigation_history: list[Path] = []
        self.navigation_index: int = -1
        self.cut_files: list[Path] | None = None
        self.task_queue = []

        self.setup_models()

        # Connect signals
        self.connect_ui_signals()

        # Setup UI components
        self.setup_ui_components()

        # Setup file watcher and icon loader
        self.setup_file_watcher_and_icon_loader()

        # Setup Platform-specific features
        self.setup_platform_features()

        # Apply styling
        self.apply_styling()

        # Final UI updates
        self.update_ui()
        self.update_address_bar(self.current_path)
        self.ui.dynamicView.setRootIndex(self.proxy_model.mapFromSource(self.fs_model.index(str(self.current_path))))

    def setup_ui_components(self):

        # Setup other UI components
        self.setup_sidebar()
        self.setup_preview_widget()
        self.setup_task_status_widget()
        self.setup_progress_bar()
        self.setup_drive_buttons()
        self.setup_view_mode_actions()
        self.setup_ribbons()

        # Set visibility
        self.ui.sidebarToolBox.setVisible(True)
        self.ui.previewWidget.setVisible(False)
        self.ui.taskStatusWidget.setVisible(True)
        self.ui.ribbonTabWidget.setVisible(False)  # Hide ribbon by default

        # Setup toolbar
        self.setup_toolbar()

        # Add ribbon toggle button
        self.toggle_ribbon_button = QPushButton("▼", self)
        self.toggle_ribbon_button.setToolTip("Toggle Ribbon Menu")
        self.toggle_ribbon_button.setMaximumWidth(20)
        self.ui.mainToolBar.addWidget(self.toggle_ribbon_button)
        self.toggle_ribbon_button.clicked.connect(self.toggle_ribbon)

        # Adjust UI sizes
        self.adjust_ui_sizes()

    def setup_file_watcher_and_icon_loader(self):
        self.fs_model.directoryLoaded.connect(self.on_directory_loaded)
        self.fs_model.setReadOnly(False)
        self.fs_model.setOption(QFileSystemModel.Option.DontWatchForChanges, False)  # noqa: FBT003
        self.icon_provider: QFileIconProvider = QFileIconProvider()
        self.fs_model.setIconProvider(self.icon_provider)

    def setup_platform_features(self):
        if platform.system() == "Windows":
            try:
                import comtypes.client as cc  # pyright: ignore[reportMissingTypeStubs]
                self.shell = cc.CreateObject("Shell.Application")
            except ImportError:
                try:
                    import win32com.client
                    self.shell = win32com.client.Dispatch("Shell.Application")
                except ImportError:
                    RobustLogger().warning("Neither comtypes nor pywin32 is available. COM interfaces will not be used.")
                    self.shell = None

    def apply_styling(self):
        self.apply_modern_style()
        self.apply_progress_bar_style()

    def setup_sidebar(self):
        self.ui.fileSystemTreeView.setModel(self.fs_model)
        self.ui.fileSystemTreeView.setRootIndex(self.fs_model.index(QDir.rootPath()))
        self.ui.fileSystemTreeView.clicked.connect(self.on_sidepanel_treeview_clicked)
        self.ui.fileSystemTreeView.expanded.connect(self.on_treeview_expanded)
        self.ui.fileSystemTreeView.collapsed.connect(self.on_treeview_collapsed)

        for i in range(1, self.fs_model.columnCount()):
            self.ui.fileSystemTreeView.hideColumn(i)

    def setup_task_status_widget(self):
        self.statusBar().addPermanentWidget(self.ui.taskStatusWidget)
        self.task_status_toggle: QPushButton = QPushButton("Task Status")
        self.task_status_toggle.setCheckable(True)
        self.task_status_toggle.setChecked(True)
        self.task_status_toggle.clicked.connect(self.toggle_task_status_widget)

    def setup_progress_bar(self):
        self.ui.progressBar.mousePressEvent = self.show_task_details
        self.ui.progressBar.hide()

    def setup_drive_buttons(self):
        drive_layout = self.ui.horizontalLayout_2
        for drive in QDir.drives():
            drive_path = drive.path()
            drive_button = QPushButton(drive_path)
            drive_button.clicked.connect(lambda _, path=drive_path: self.set_current_path(path))
            drive_layout.addWidget(drive_button)

    def setup_view_mode_actions(self):
        self.actionIconView = QAction("Icon View", self)
        self.actionListView = QAction("List View", self)
        self.actionDetailView = QAction("Detail View", self)

        self.actionIconView.triggered.connect(lambda: self.ui.dynamicView.list_view().setViewMode(QListView.ViewMode.IconMode))
        self.actionListView.triggered.connect(lambda: self.ui.dynamicView.list_view().setViewMode(QListView.ViewMode.ListMode))
        self.actionDetailView.triggered.connect(lambda: self.ui.dynamicView.setCurrentWidget(self.ui.dynamicView.tree_view()))

    def setup_toolbar(self):
        self.ui.mainToolBar.addWidget(self.ui.taskStatusToggle)
        self.ui.mainToolBar.setMovable(False)
        self.ui.mainToolBar.setIconSize(QSize(24, 24))

        self.ui.mainToolBar.addAction(self._actions.actionNewWindow)
        self.ui.mainToolBar.addAction(self._actions.actionOpenTerminal)
        self.ui.mainToolBar.addSeparator()
        self.ui.mainToolBar.addAction(self._actions.actionCut)
        self.ui.mainToolBar.addAction(self._actions.actionCopy)
        self.ui.mainToolBar.addAction(self._actions.actionPaste)
        self.ui.mainToolBar.addSeparator()
        self.ui.mainToolBar.addAction(self._actions.actionRefresh)
        self.ui.mainToolBar.addAction(self._actions.actionShowHiddenItems)

        if self.ui.searchBar.isVisible():
            self.ui.searchBar.hide()
        else:
            self.ui.searchBar.show()
            self.ui.searchBar.setFocus()

        self.ui.searchBar.textChanged.connect(self.on_search_text_changed)
        self.ui.searchBar.setPlaceholderText("Search...")

    def setup_models(self):
        self.fs_model: QFileSystemModel = QFileSystemModel()
        self.fs_model.setOption(QFileSystemModel.Option.DontWatchForChanges, False)  # noqa: FBT003
        self.fs_model.setOption(QFileSystemModel.Option.DontResolveSymlinks, True)  # noqa: FBT003
        self.fs_model.setRootPath(str(self.current_path.root))
        self.proxy_model: QSortFilterProxyModel = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.fs_model)
        self.completer: QCompleter = QCompleter(self)
        self.completer.setModel(self.fs_model)
        self.bookmarks_model = QStandardItemModel()

        self.ui.fileSystemTreeView.setModel(self.proxy_model)
        self.ui.dynamicView.setModel(self.proxy_model)
        self.ui.dynamicView.show()
        self.ui.bookmarksListView.setModel(self.bookmarks_model)

        # Setup actions and connections
        self.executor = FileActionsExecutor()
        self.dispatcher: MenuActionsDispatcher = MenuActionsDispatcher(self.fs_model, self.proxy_model, self.executor)

    def connect_ui_signals(self):
        self.ui.fileSystemTreeView.clicked.connect(self.on_navigation_pane_clicked)
        for view in self.ui.dynamicView.all_views:
            view.clicked.connect(self.on_file_list_view_clicked)
            view.doubleClicked.connect(self.on_item_double_clicked)
        self.ui.dynamicView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.dynamicView.customContextMenuRequested.connect(self.show_context_menu)
        self.ui.addressBar.refreshButton.clicked.connect(self.refresh)
        self.ui.ribbonTabWidget.currentChanged.connect(self.on_ribbon_tab_changed)
        self.ui.zoomSlider.valueChanged.connect(self.on_zoom_slider_changed)
        self.ui.itemCountLabel.linkActivated.connect(self.on_item_count_clicked)
        self.ui.selectedCountLabel.linkActivated.connect(self.on_selected_count_clicked)
        self.ui.freeSpaceLabel.linkActivated.connect(self.on_free_space_clicked)
        self.ui.progressBar.mousePressEvent = self.show_task_details  # pyright: ignore[reportAttributeAccessIssue]
        self.ui.taskStatusToggle.clicked.connect(self.toggle_task_status_widget)
        self.ui.addressBar.pathChanged.connect(self.on_address_bar_path_changed)
        self.ui.addressBar.returnPressed.connect(self.on_address_bar_return)
        self.ui.bookmarksListView.clicked.connect(self.on_bookmark_clicked)

        self.ui.dynamicView.selectionModel().selectionChanged.connect(self.update_preview)

        self.executor.TaskStarted.connect(self.on_task_started)
        self.executor.TaskCompleted.connect(self.on_task_completed)
        self.executor.TaskFailed.connect(self.on_task_failed)
        self.executor.TaskCancelled.connect(self.on_task_cancelled)
        self.executor.TaskProgress.connect(self.on_task_progress)
        self.executor.AllTasksCompleted.connect(self.on_all_tasks_completed)
        self.executor.ProgressUpdated.connect(self.update_progress_bar)
        self.ui.taskStatusWidget.task_clicked.connect(self.show_task_details)

    def setup_ribbons(self):
        self.ui.homeTab.setLayout(self.dispatcher.menus.home_ribbon_layout)
        self.ui.viewTab.setLayout(self.dispatcher.menus.view_ribbon_layout)

    def apply_modern_style(self):
        palette = self.palette()
        background_color = palette.color(QPalette.ColorRole.Base).name()
        toolbar_color = palette.color(QPalette.ColorRole.Midlight).name()
        border_color = palette.color(QPalette.ColorRole.Mid).name()
        title_color = palette.color(QPalette.ColorRole.Midlight).name()

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {background_color};
            }}
            QToolBar {{
                border: none;
                background-color: {toolbar_color};
            }}
            QDockWidget {{
                border: 1px solid {border_color};
            }}
            QDockWidget::title {{
                background-color: {title_color};
                padding-left: 5px;
            }}
        """)

    def apply_progress_bar_style(self):
        palette = self.palette()
        self.ui.progressBar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {palette.color(QPalette.ColorRole.Mid).name()};
                border-radius: 2px;
                text-align: center;
                font-size: 10px;
            }}
            QProgressBar::chunk {{
                background-color: {palette.color(QPalette.ColorRole.Highlight).name()};
                width: 5px;
                margin: 0.5px;
            }}
        """)

    def connect_signals(self):
        self.executor.TaskStarted.connect(self.on_task_started)
        self.executor.TaskCompleted.connect(self.on_task_completed)
        self.executor.TaskFailed.connect(self.on_task_failed)
        self.executor.TaskCancelled.connect(self.on_task_cancelled)
        self.executor.TaskProgress.connect(self.on_task_progress)
        self.executor.AllTasksCompleted.connect(self.on_all_tasks_completed)
        self.executor.ProgressUpdated.connect(self.update_progress_bar)
        self.ui.taskStatusWidget.set_dispatcher(self.executor)
        self.ui.taskStatusWidget.task_clicked.connect(self.show_task_details)
        self.ui.dynamicView.selectionModel().selectionChanged.connect(self.update_preview)

    def on_task_started(self, task_id):
        cast(QStatusBar, self.statusBar()).showMessage(f"Task {task_id} started")

    def on_task_completed(self, task_id, result):
        cast(QStatusBar, self.statusBar()).showMessage(f"Task {task_id} completed")
        self.refresh()

    def on_task_failed(self, task_id, error):
        cast(QStatusBar, self.statusBar()).showMessage(f"Task {task_id} failed: {error}")

    def on_task_cancelled(self, task_id):
        cast(QStatusBar, self.statusBar()).showMessage(f"Task {task_id} cancelled")

    def on_task_progress(self, task_id, progress):
        cast(QStatusBar, self.statusBar()).showMessage(f"Task {task_id} progress: {progress:.2f}%")

    def on_all_tasks_completed(self):
        cast(QStatusBar, self.statusBar()).showMessage("All tasks completed")
        self.refresh()

    def toggle_task_status_widget(self) -> None:
        """Toggle the visibility of the task status widget."""
        if self.ui.taskStatusWidget.isVisible():
            self.ui.taskStatusWidget.hide()
            self.task_status_toggle.setChecked(False)
        else:
            self.ui.taskStatusWidget.show()
            self.task_status_toggle.setChecked(True)

    def toggle_ribbon(self):
        """Toggle the visibility of the ribbon menu."""
        if self.ui.ribbonTabWidget.isVisible():
            self.ui.ribbonTabWidget.hide()
            self.toggle_ribbon_button.setText("▼")
        else:
            self.ui.ribbonTabWidget.show()
            self.toggle_ribbon_button.setText("▲")

    def adjust_ui_sizes(self):
        """Adjust UI sizes to match typical file explorer dimensions."""
        # Set initial window size
        # TODO: find alternatives to hardcoded window sizes
        self.resize(1000, 600)

        # Adjust splitter sizes
        self.ui.mainSplitter.setSizes([200, 800])  # Left sidebar: 200px, Main view: 800px

        # Set minimum sizes for better usability
        # TODO: find alternative to hardcoded minimum sizes
        self.ui.sidebarToolBox.setMinimumWidth(150)
        self.ui.dynamicView.setMinimumWidth(400)

        # Adjust toolbar and address bar heights
        # TODO: find alternative to fixed heights please
        self.ui.mainToolBar.setFixedHeight(30)
        self.ui.searchAndAddressWidget.setFixedHeight(30)

        # Adjust font sizes
        font = self.font()
        font.setPointSize(9)
        self.setFont(font)

    def on_sidepanel_treeview_clicked(self, index):
        path = self.fs_model.filePath(index)
        self.set_current_path(path)

    def on_bookmark_clicked(self, index):
        path = self.bookmarks_model.data(index, Qt.ItemDataRole.UserRole)
        self.set_current_path(path)

    def setup_actions(self):
        # This method is no longer needed as we're using FileExplorerMenus
        pass

    # Remove duplicate setup_ribbons, setup_home_ribbon, and setup_view_ribbon functions

    def on_ribbon_tab_changed(self, index):
        # Handle ribbon tab changes
        pass

    def on_zoom_slider_changed(self, value):
        # Implement zoom functionality
        self.ui.dynamicView.current_view().set_text_size(value)

    # These methods have been removed as they are no longer used

    def on_item_count_clicked(self, link):
        # Handle item count label click
        total_items = self.fs_model.rowCount(self.ui.dynamicView.rootIndex())
        QMessageBox.information(self, "Item Count", f"Total items: {total_items}")

    def on_selected_count_clicked(self, link):
        # Handle selected count label click
        selected_items = len(self.ui.dynamicView.selectedIndexes())
        QMessageBox.information(self, "Selected Count", f"Selected items: {selected_items}")

    def on_free_space_clicked(self, link):
        # Handle free space label click
        free_space = shutil.disk_usage(self.current_path).free
        QMessageBox.information(self, "Free Space", f"Free space on {self.current_path}: {self.format_size(free_space)}")

    # Remove duplicate show_progress_log function

    def on_navigation_pane_clicked(self, index: QModelIndex):
        path = self.fs_model.filePath(index)
        self.set_current_path(path)

    def on_file_list_view_clicked(self, index: QModelIndex):
        source_index = self.proxy_model.mapToSource(index)
        path = self.fs_model.filePath(source_index)
        self.file_selected.emit(path)

    def on_item_double_clicked(self, index: QModelIndex):
        source_index = self.proxy_model.mapToSource(index)
        path = self.fs_model.filePath(source_index)
        if self.fs_model.isDir(source_index):
            self.set_current_path(path)
        else:
            os.startfile(path)  # noqa: S606
            self.executor.queue_task("open_file", (path,))

    def on_address_bar_return(self):
        path = self.ui.addressBar.line_edit.text()
        self.set_current_path(path)

    def on_go_button_clicked(self):
        self.on_address_bar_return()

    def set_current_path(self, path: os.PathLike | str):
        path_obj = Path(path)
        if path_obj.is_dir():
            self.current_path = path_obj
            source_index = self.fs_model.index(str(path_obj))
            proxy_index = self.proxy_model.mapFromSource(source_index)
            self.ui.dynamicView.setRootIndex(proxy_index)
            self.ui.fileSystemTreeView.setCurrentIndex(source_index)
            self.ui.addressBar.update_path(path_obj)
            self.directory_changed.emit(str(path_obj))
            self.ui.addressBar._update_history(path_obj)
            self.update_ui()
        else:
            # Handle invalid path
            self.ui.addressBar.update_path(self.current_path)

    def on_search_text_changed(self, text: str):
        self.proxy_model.setFilterRegularExpression(text)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        proxy_index = self.proxy_model.mapFromSource(self.fs_model.index(str(self.current_path)))
        self.ui.dynamicView.setRootIndex(proxy_index)

    def focus_address_bar(self):
        self.ui.addressBar.setFocus()
        self.ui.addressBar.line_edit.selectAll()

    def connect_menu_actions(self, menu: QMenu):
        for action in menu.actions():
            if isinstance(action, QAction):
                action.triggered.connect(lambda checked, a=action: self.execute_menu_action(a))
            elif isinstance(action, QMenu):
                self.connect_menu_actions(action)

    def execute_menu_action(self, action: QAction):
        action_name = action.text().lower().replace(" ", "_")
        method_name = f"on_{action_name}"
        if hasattr(self, method_name):
            getattr(self, method_name)()
        else:
            print(f"Method {method_name} not implemented")

    def on_open_in_new_window(self):
        index = self.ui.dynamicView.currentIndex()
        path = self.fs_model.filePath(self.proxy_model.mapToSource(index))
        new_window = FileSystemExplorerWidget(initial_path=path)
        new_window.show()
        new_window.raise_()
        new_window.activateWindow()

    def on_open_in_new_tab(self):
        index = self.ui.dynamicView.currentIndex()
        path = self.fs_model.filePath(self.proxy_model.mapToSource(index))
        self.open_in_new_tab.emit(str(path))  # Emit signal to be handled by parent widget

    def on_properties(self):
        index = self.ui.dynamicView.currentIndex()
        path = self.fs_model.filePath(self.proxy_model.mapToSource(index))
        self.executor.queue_task("get_properties", args=(path,), callback=self.show_properties, priority=1)

    def show_properties(self, properties: dict):
        dialog = PropertiesDialog(properties, self)
        dialog.exec()

    def update_status_bar(self):
        selected_items = len(self.ui.dynamicView.selectedIndexes())
        view_model = self.ui.dynamicView.current_view().model()
        assert view_model is not None, "View model is None"

        # Map the proxy index to the source index
        proxy_root_index = self.ui.dynamicView.rootIndex()
        source_root_index = self.proxy_model.mapToSource(proxy_root_index)

        total_items = self.fs_model.rowCount(source_root_index)

        self.ui.itemCountLabel.setText(f"{total_items} item{'s' if total_items != 1 else ''}")
        self.ui.selectedCountLabel.setText(f"{selected_items} selected")

        root_path = self.fs_model.filePath(source_root_index)
        try:
            free_space = shutil.disk_usage(root_path).free
            self.ui.freeSpaceLabel.setText(f"Free space: {self.format_size(free_space)}")
        except OSError:
            self.ui.freeSpaceLabel.setText("Free space: Unknown")

        # Update progress bar
        completed_tasks = self.executor.completed_tasks
        total_tasks = self.executor.total_tasks
        if total_tasks > 0:
            progress = int((completed_tasks / total_tasks) * 100)
            self.ui.progressBar.setValue(progress)
            self.ui.progressBar.setFormat(f"{completed_tasks}/{total_tasks}")
            self.ui.progressBar.setVisible(True)
        else:
            self.ui.progressBar.setVisible(False)

    def format_size(self, size: int) -> str:
        readable_size: float = size
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if readable_size < 1024.0:  # noqa: PLR2004
                return f"{readable_size:.1f} {unit}"
            readable_size /= 1024.0
        return f"{readable_size:.1f} PB"

    def new_window(self):
        new_window = FileSystemExplorerWidget()
        new_window.show()

    def open_windows_terminal(self):
        import shlex

        command: str = f'start cmd /K "cd /d {self.current_path}"'
        args: list[str] = shlex.split(command)
        subprocess.Popen(args)  # noqa: S603

    def cut(self):
        self.copy(cut=True)

    def copy(self, cut: bool = False):  # noqa: FBT001, FBT002
        selected_indexes = self.ui.dynamicView.selectedIndexes()
        if selected_indexes:
            source_paths = [Path(self.fs_model.filePath(index)) for index in selected_indexes]  # pyright: ignore[reportArgumentType]
            mime_data = QMimeData()
            urls = [QUrl.fromLocalFile(str(path)) for path in source_paths]
            mime_data.setUrls(urls)
            QApplication.clipboard().setMimeData(mime_data)

            operation = "cut" if cut else "copy"
            self.executor.queue_task(
                lambda _: setattr(self, "to_cut", source_paths if cut else None),
                args=(source_paths,),
            )

    def paste(self):
        mime_data = QApplication.clipboard().mimeData()
        if mime_data.hasUrls():
            source_paths = [Path(url.toLocalFile()) for url in mime_data.urls()]
            destination_path = self.current_path

            def on_complete(_):
                self.refresh()
                if hasattr(self, "to_cut") and self.to_cut == source_paths:
                    self.executor.queue_task("delete_items", args=(self.to_cut,), on_complete=lambda _: setattr(self, "to_cut", None))

            self.executor.queue_task("paste", args=(source_paths, destination_path), on_complete=on_complete)

    def delete_items(self):
        selected_indexes = self.ui.dynamicView.selectedIndexes()
        if selected_indexes:
            paths = [Path(self.fs_model.filePath(index)) for index in selected_indexes]
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete {len(paths)} item(s)?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                task_id = self.executor.queue_task("delete_items", args=(paths,), priority=1, description=f"Deleting {len(paths)} item(s)")
                self.update_ui()
                self.show_task_details(task_id)

    def show_error_message(self, error):
        QMessageBox.critical(self, "Error", str(error))

    def update_ui(self):
        self.update_status_bar()
        # self.update_task_status_widget()

    def update_task_status_widget(self):
        self.ui.taskStatusWidget.update_all_tasks()

    def show_task_details(self, task_id):
        task_details_dialog = TaskDetailsDialog(self.executor, task_id, self)
        task_details_dialog.exec()

    def rename(self):
        selected_indexes = self.ui.dynamicView.selectedIndexes()
        if selected_indexes:
            file_path = Path(self.fs_model.filePath(selected_indexes[0]))  # pyright: ignore[reportArgumentType]
            new_name, ok = QInputDialog.getText(self, "Rename", "Enter new name:", QLineEdit.EchoMode.Normal, file_path.name)
            if ok and new_name:
                new_path = file_path.with_name(new_name)
                if new_path.exists():
                    QMessageBox.warning(self, "Rename", "A file with this name already exists.")
                else:

                    def redo_rename():
                        self.executor.queue_task("rename_item", args=(file_path, new_path), on_complete=self.refresh)

                    def undo_rename():
                        self.executor.queue_task("rename_item", args=(new_path, file_path), on_complete=self.refresh)

                    self.create_undo_command(redo_rename, undo_rename, f"Rename {file_path.name} to {new_name}")

    def update_progress(self, value: int):
        self.ui.progressBar.setValue(value)
        if value >= 100:  # noqa: PLR2004
            self.ui.progressBar.setVisible(False)
        elif not self.ui.progressBar.isVisible():
            self.ui.progressBar.setVisible(True)

    def select_all(self):
        self.ui.dynamicView.selectAll()

    def invert_selection(self):
        selection_model = self.ui.dynamicView.selectionModel()
        assert isinstance(selection_model, QItemSelectionModel), f"Selection model is not a QItemSelectionModel, instead was a {type(selection_model)}"
        for i in range(self.fs_model.rowCount(self.ui.dynamicView.rootIndex())):  # pyright: ignore[reportArgumentType]
            index = self.fs_model.index(i, 0, self.ui.dynamicView.rootIndex())  # pyright: ignore[reportArgumentType]
            selection_model.select(index, QItemSelectionModel.SelectionFlag.Toggle)  # pyright: ignore[reportCallIssue, reportArgumentType]

    def select_none(self):
        self.ui.dynamicView.clearSelection()

    def refresh(self):
        current_index = self.fs_model.index(str(self.current_path))
        self.fs_model.setRootPath(str(self.current_path))
        self.ui.dynamicView.setRootIndex(current_index)
        self.update_ui()

    def update_address_bar(self, path: os.PathLike | str):
        path_obj = Path(path)
        self.ui.addressBar.update_path(path_obj)

    def on_address_bar_path_changed(self, path: Path):
        self.change_path(path)

    def on_directory_loaded(self, path: str):
        loaded_path = Path(path)
        if loaded_path == self.current_path:
            self.ui.addressBar.update_path(loaded_path)
        for i in range(self.fs_model.rowCount(self.fs_model.index(path))):
            child_index = self.fs_model.index(i, 0, self.fs_model.index(path))
            file_path = self.fs_model.filePath(child_index)

    def setup_views(self):
        # Set up the DynamicView
        self.ui.dynamicView.setModel(self.proxy_model)
        self.ui.dynamicView.setRootIndex(self.proxy_model.mapFromSource(self.fs_model.index(str(self.current_path))))
        for view in self.ui.dynamicView.all_views:
            view.doubleClicked.connect(self.on_item_double_clicked)
            view.clicked.connect(self.on_view_clicked)

        # Set up the tree view in the sidebar
        self.ui.fileSystemTreeView.setModel(self.fs_model)
        self.ui.fileSystemTreeView.setRootIndex(self.fs_model.index(QDir.rootPath()))
        self.ui.fileSystemTreeView.clicked.connect(self.on_sidepanel_treeview_clicked)
        self.ui.fileSystemTreeView.expanded.connect(self.on_treeview_expanded)
        self.ui.fileSystemTreeView.collapsed.connect(self.on_treeview_collapsed)

        # Set up the PyAddressBar
        self.ui.addressBar.pathChanged.connect(self.on_address_bar_path_changed)
        self.ui.addressBar.returnPressed.connect(self.on_address_bar_return)

        # Show only the Name column in the tree view
        for i in range(1, self.fs_model.columnCount()):
            self.ui.fileSystemTreeView.hideColumn(i)

        # Set up view mode actions
        self.actionIconView = QAction("Icon View", self)
        self.actionListView = QAction("List View", self)
        self.actionDetailView = QAction("Detail View", self)

        self.actionIconView.triggered.connect(lambda: self.ui.dynamicView.list_view().setViewMode(QListView.ViewMode.IconMode))
        self.actionListView.triggered.connect(lambda: self.ui.dynamicView.list_view().setViewMode(QListView.ViewMode.ListMode))
        self.actionDetailView.triggered.connect(lambda: self.ui.dynamicView.setCurrentWidget(self.ui.dynamicView.tree_view()))

    def on_treeview_expanded(self, index: QModelIndex):
        self.fs_model.fetchMore(index)

    def on_treeview_collapsed(self, index: QModelIndex): ...

    def change_path(self, path: Path):
        self.current_path = path
        source_index = self.fs_model.index(str(path))
        proxy_index = self.proxy_model.mapFromSource(source_index)
        self.ui.dynamicView.setRootIndex(proxy_index)
        self.ui.fileSystemTreeView.setCurrentIndex(source_index)
        self.update_address_bar(path)

    def on_view_clicked(self, index: QModelIndex):
        source_index = self.proxy_model.mapToSource(index)
        path = Path(self.fs_model.filePath(source_index))
        self.change_path(path)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)

    def show_context_menu(self, pos: QPoint):
        current_view: QWidget | None = self.ui.dynamicView.currentWidget()
        assert isinstance(current_view, RobustAbstractItemView), f"Current view is not a QListView, instead was a {type(current_view).__name__}"
        index: QModelIndex = current_view.indexAt(pos)
        if index.isValid():
            self.show_item_context_menu(current_view.viewport().mapToGlobal(pos), index)
        else:
            self.show_empty_space_context_menu(current_view.viewport().mapToGlobal(pos))

    def create_new_folder(self):
        folder_name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and folder_name:
            new_folder_path = Path(self.current_path, folder_name)
            try:
                new_folder_path.mkdir(parents=True, exist_ok=False)
                self.refresh()
            except FileExistsError:
                QMessageBox.warning(self, "Error", f"A folder named '{folder_name}' already exists.")
            except PermissionError:
                QMessageBox.warning(self, "Error", f"Permission denied. Unable to create folder '{folder_name}'.")
            except OSError as e:
                QMessageBox.warning(self, "Error", f"Failed to create folder '{folder_name}'. Error: {e!s}")

    def create_new_file(self):
        file_name, ok = QInputDialog.getText(self, "New File", "Enter file name:")
        if ok and file_name:
            new_file_path = QDir(str(self.current_path)).filePath(file_name)
            file = QFile(new_file_path)
            if file.open(QIODevice.OpenModeFlag.WriteOnly):
                file.close()
                self.fs_model.setRootPath(str(self.current_path))  # Refresh the view
            else:
                QMessageBox.warning(self, "Error", "Failed to create file.")

    def cut_file(self, file_path: Path) -> None:
        """Cut the selected file."""
        self.executor.queue_task("prepare_cut", args=([file_path],), callback=lambda _: self.set_cut_files([file_path]))
        self.copy_to_clipboard([file_path])

    def copy_file(self, file_path: Path) -> None:
        """Copy the selected file."""
        self.executor.queue_task("prepare_copy", args=([file_path],), callback=lambda _: self.set_cut_files(None))
        self.copy_to_clipboard([file_path])

    def paste_file(self) -> None:
        """Paste the file from the clipboard."""
        mime_data = QApplication.clipboard().mimeData()
        if mime_data.hasUrls():
            source_paths = [Path(url.toLocalFile()) for url in mime_data.urls()]
            destination_path = self.current_path
            self.executor.queue_task("paste", args=(source_paths, destination_path), callback=self.on_paste_complete)

    def on_paste_complete(self, _) -> None:
        """Handle completion of paste operation."""
        self.refresh()
        if self.cut_files:
            self.executor.queue_task("delete_items", args=(self.cut_files,), callback=lambda _: self.set_cut_files(None))

    def set_cut_files(self, files: list[Path] | None) -> None:
        """Set the files that have been cut."""
        self.cut_files = files

    def copy_to_clipboard(self, paths: list[Path]) -> None:
        """Copy the given paths to the clipboard."""
        mime_data = QMimeData()
        urls = [QUrl.fromLocalFile(str(path)) for path in paths]
        mime_data.setUrls(urls)
        QApplication.clipboard().setMimeData(mime_data)

    def show_empty_space_context_menu(self, pos: QPoint):
        menu = self.dispatcher.get_menu(shift_held=bool(QApplication.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier))

        # Connect actions to appropriate methods
        for action in menu.actions():
            if action.data():
                action.triggered.connect(lambda checked, a=action: self.execute_menu_action(a.data()))

        current_view = self.ui.dynamicView
        menu.exec(current_view.mapToGlobal(pos))

    def get_permissions_string(self, file_info: QFileInfo) -> str:
        permissions = []
        if file_info.isReadable():
            permissions.append("Read")
        if file_info.isWritable():
            permissions.append("Write")
        if file_info.isExecutable():
            permissions.append("Execute")
        return ", ".join(permissions)

    def toggle_hidden_items(self):
        self._actions.actionShowHiddenItems.trigger()
        self.refresh()

    def toggle_all_directories(self):
        self._actions.actionShowAllDirectories.trigger()
        self.refresh()

    def toggle_files(self):
        self._actions.actionShowFiles.trigger()
        self.refresh()

    def toggle_executables(self):
        self._actions.actionShowExecutables.trigger()
        self.refresh()

    def toggle_symlinks(self):
        self._actions.actionShowSymlinks.trigger()
        self.refresh()

    def toggle_readable(self):
        self._actions.actionShowReadable.trigger()
        self.refresh()

    def toggle_writable(self):
        self._actions.actionShowWritable.trigger()
        self.refresh()

    def toggle_system(self):
        self._actions.actionShowSystem.trigger()
        self.refresh()

    def toggle_dot_and_dotdot(self):
        self._actions.actionShowDotAndDotDot.trigger()
        self.refresh()

    def toggle_dirs(self):
        self._actions.actionShowDirs.trigger()
        self.refresh()

    def focus_search_bar(self):
        self.ui.searchBar.setFocus()
        self.ui.searchBar.selectAll()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            urls = event.mimeData().urls()
            paths = [Path(url.toLocalFile()) for url in urls]
            for path in paths:
                if path.is_dir():
                    self.executor.queue_task("copy_directory", args=(path, self.current_path), callback=self.refresh)
                else:
                    self.executor.queue_task("copy_file", args=(path, self.current_path), callback=self.refresh)
            self.statusBar().showMessage(f"Copying {len(paths)} item(s)...")
        else:
            event.ignore()

    # ... implement other file action methods ...

    # Update the context menu creation to use the new file _actions
    def create_context_menu(self, index: QModelIndex) -> QMenu:
        menu = QMenu(self)
        if index.isValid():
            file_path = Path(self.fs_model.filePath(index))
            delete_action = menu.addAction("Delete")
            assert delete_action is not None, "Delete action is None"
            delete_action.triggered.connect(lambda: self.executor.queue_task("delete_items", args=([file_path],), callback=self.refresh))
            rename_action = menu.addAction("Rename")
            assert rename_action is not None, "Rename action is None"
            rename_action.triggered.connect(lambda: self.show_rename_dialog(file_path))

            copy_action = menu.addAction("Copy")
            assert copy_action is not None, "Copy action is None"
            copy_action.triggered.connect(lambda: self.copy_file(file_path))

            cut_action = menu.addAction("Cut")
            assert cut_action is not None, "Cut action is None"
            cut_action.triggered.connect(lambda: self.cut_file(file_path))

            if file_path.is_dir():
                compress_action = menu.addAction("Compress")
                assert compress_action is not None, "Compress action is None"
                compress_action.triggered.connect(lambda: self.compress_items([file_path]))

            properties_action = menu.addAction("Properties")
            assert properties_action is not None, "Properties action is None"
            properties_action.triggered.connect(lambda: self.executor.queue_task("get_properties", args=(file_path,), callback=self.show_properties))

        paste_action = menu.addAction("Paste")
        assert paste_action is not None, "Paste action is None"
        paste_action.triggered.connect(self.paste_file)
        paste_action.setEnabled(QApplication.clipboard().mimeData().hasUrls())

        return menu

    def show_rename_dialog(self, path: Path):
        new_name, ok = QInputDialog.getText(self, "Rename", "Enter new name:", text=path.name)
        if ok and new_name:
            self.executor.queue_task("rename_item", (path, new_name))

    def create_mime_data(self, paths: list[Path]) -> QMimeData:
        mime_data = QMimeData()
        urls = [QUrl.fromLocalFile(str(path)) for path in paths]
        mime_data.setUrls(urls)
        return mime_data

    def compress_items(self, paths: list[Path]) -> None:
        """Compress selected items into an archive."""
        archive_name, _ = QFileDialog.getSaveFileName(self, "Save Compressed File", str(self.current_path), "Zip Files (*.zip)")
        if archive_name:
            if not archive_name.lower().endswith(".zip"):
                archive_name += ".zip"
            self.executor.queue_task(
                "compress_items", args=(paths, archive_name), callback=self.refresh, error_callback=lambda e: QMessageBox.warning(self, "Compression Error", str(e))
            )

    def setup_preview_widget(self):
        self.ui.previewWidget = PreviewWidget(self)
        self.ui.previewWidget.setVisible(False)

    def update_preview(self):
        selected_indexes = self.ui.dynamicView.selectedIndexes()
        if selected_indexes:
            file_path = Path(self.fs_model.filePath(selected_indexes[0]))
            if file_path.is_file():
                if file_path.suffix.lower() in [".jpg", ".jpeg", ".png", ".gif", ".bmp"]:
                    self.icon_loader.load_thumbnail(str(file_path))
                elif file_path.suffix.lower() in [".txt", ".py", ".cpp", ".h", ".html", ".css", ".js"]:
                    self.load_text_preview(file_path)
                elif file_path.suffix.lower() in [".pdf"]:
                    self.load_pdf_preview(file_path)
                else:
                    self.icon_loader.load_icon(str(file_path))
                self.ui.previewWidget.setVisible(True)
            else:
                self.load_folder_preview(file_path)
                self.ui.previewWidget.setVisible(True)
        else:
            self.ui.previewWidget.setVisible(False)

    def load_text_preview(self, file_path: Path):
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read(1000)  # Read first 1000 characters
            self.ui.previewWidget.set_text(content)
        except Exception as e:
            self.ui.previewWidget.set_text(f"Error loading text preview: {e!s}")

    def load_pdf_preview(self, file_path: Path):
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(file_path)
            page = doc.load_page(0)  # Load the first page
            pix = page.get_pixmap()
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            self.ui.previewWidget.set_image(img)
        except ImportError:
            self.ui.previewWidget.set_text("PDF preview requires PyMuPDF library")
        except Exception as e:
            self.ui.previewWidget.set_text(f"Error loading PDF preview: {e!s}")

    def load_folder_preview(self, folder_path: Path):
        try:
            items = list(folder_path.iterdir())
            preview_text = f"Folder: {folder_path.name}\n"
            preview_text += f"Items: {len(items)}\n"
            preview_text += f"Size: {self.format_size(sum(f.stat().st_size for f in items if f.is_file()))}\n"
            preview_text += "\nContents:\n"
            for item in items[:10]:  # Show first 10 items
                preview_text += f"- {item.name}\n"
            if len(items) > 10:
                preview_text += "..."
            self.ui.previewWidget.set_text(preview_text)
        except Exception as e:
            self.ui.previewWidget.set_text(f"Error loading folder preview: {e!s}")

    def on_icon_loaded(self, file_path: str, icon: QIcon):
        self.ui.previewWidget.set_icon(icon)
        self.fs_model.setData(self.fs_model.index(file_path), icon, Qt.ItemDataRole.DecorationRole)

    def on_thumbnail_loaded(self, file_path: str, image: QImage):
        val = image.bits()
        if val is None:
            return
        if not isinstance(val, bytes):
            val = bytes(val.asarray())
        self.ui.previewWidget.set_image(val, image.width(), image.height())
        icon = QIcon(QPixmap.fromImage(image))
        self.fs_model.setData(self.fs_model.index(file_path), icon, Qt.ItemDataRole.DecorationRole)

    def update_progress_bar(self, completed_tasks: int, total_tasks: int) -> None:
        """Update the progress bar with the current task completion status."""
        progress = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        self.ui.progressBar.setValue(int(progress))
        self.ui.progressBar.setFormat(f"{completed_tasks}/{total_tasks} tasks completed")
        self.ui.progressBar.setStyleSheet("""
            QProgressBar {
                border: 1px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 10px;
                margin: 0.5px;
            }
        """)
        self.ui.progressBar.show()

    def show_properties(self, properties: dict) -> None:
        """Show file or directory properties."""
        property_text = "\n".join(f"{k}: {v}" for k, v in properties.items())
        QMessageBox.information(self, "Properties", property_text)


if __name__ == "__main__":
    def onAppCrash(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: TracebackType | None,
    ) -> None:
        error_message = f"An unexpected error occurred:\n{exc_type.__name__}: {exc_value}"
        RobustLogger().exception(error_message, exc_info=(exc_type, exc_value, exc_traceback))
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = onAppCrash
    app = QApplication(sys.argv)
    main_window = QMainWindow()
    file_explorer = FileSystemExplorerWidget()
    main_window.setCentralWidget(file_explorer)
    main_window.setWindowTitle("File System Explorer")
    main_window.resize(1000, 600)
    main_window.show()
    sys.exit(app.exec())

class PropertiesDialog(QDialog):
    def __init__(self, properties: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Properties")
        self.setLayout(QVBoxLayout())

        for key, value in properties.items():
            label = QLabel(f"{key}: {value}")
            self.layout().addWidget(label)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        self.layout().addWidget(close_button)
