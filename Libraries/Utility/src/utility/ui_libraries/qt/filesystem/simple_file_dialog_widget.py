from __future__ import annotations

import platform
import shutil
import subprocess
import sys

from concurrent.futures import ProcessPoolExecutor
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

import qtpy

from loggerplus import RobustLogger
from qtpy.QtCore import (
    QDir,
    QEvent,
    QFile,
    QFileInfo,
    QItemSelectionModel,
    QMimeData,
    QModelIndex,
    QSortFilterProxyModel,
    QUrl,
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QClipboard, QCursor, QDesktopServices, QGuiApplication, QIcon, QKeySequence, QWheelEvent
from qtpy.QtWidgets import (
    QApplication,
    QCompleter,
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
    QShortcut,
    QSplitter,
    QTableView,
    QUndoStack,
    QVBoxLayout,
    QWidget,
)

from utility.ui_libraries.qt.filesystem.address_bar import QAddressBar
from utility.ui_libraries.qt.filesystem.explorer.file_explorer_context_menu import FileExplorerContextMenu
from utility.ui_libraries.qt.filesystem.explorer.undo_commands import CopyCommand, DeleteCommand, MoveCommand, RenameCommand
from utility.ui_libraries.qt.widgets.itemviews.dynamic_view import DynamicView, ViewMode
from utility.ui_libraries.qt.widgets.itemviews.tileview import RobustTileView
from utility.ui_libraries.qt.widgets.itemviews.treeview import RobustTreeView

if TYPE_CHECKING:
    import os

    from concurrent.futures import Future

    from qtpy.QtCore import QModelIndex, QObject, QPoint
    from qtpy.QtGui import QClipboard, QDragEnterEvent, QDropEvent, QResizeEvent
    from qtpy.QtWidgets import QWidget
    try:  # noqa: SIM105
        from win32com.client.dynamic import CDispatch  # pyright: ignore[reportMissingModuleSource]
    except ImportError:  # noqa: S110
        pass  # Handle the case when win32com is not available


class FileSystemExplorerWidget(QMainWindow):
    file_selected = Signal(str)
    directory_changed = Signal(str)

    def __init__(self, initial_path: Path | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        if qtpy.API_NAME == "PyQt5":
            from utility.ui_libraries.qt.uic.pyqt5.filesystem.file_system_explorer_widget import Ui_FileSystemExplorerWidget  # pyright: ignore[reportMissingImports]
        elif qtpy.API_NAME == "PySide6":

            from utility.ui_libraries.qt.uic.pyside6.filesystem.file_system_explorer_widget import Ui_FileSystemExplorerWidget  # pyright: ignore[reportMissingImports]
        elif qtpy.API_NAME == "PySide2":

            from utility.ui_libraries.qt.uic.pyside2.filesystem.file_system_explorer_widget import Ui_FileSystemExplorerWidget  # pyright: ignore[reportMissingImports]
        elif qtpy.API_NAME == "PyQt6":

            from utility.ui_libraries.qt.uic.pyqt6.filesystem.file_system_explorer_widget import Ui_FileSystemExplorerWidget  # pyright: ignore[reportMissingImports]
        else:
            raise ImportError(f"Unsupported Qt API: {qtpy.API_NAME}")

        self.ui: Ui_FileSystemExplorerWidget = Ui_FileSystemExplorerWidget()
        self.ui.setupUi(self)
        self.current_path: Path = Path.home()

        self.navigation_history: list[Path] = []
        self.navigation_index: int = -1
        self.clipboard: QClipboard = QApplication.clipboard()
        self.undo_stack: QUndoStack = QUndoStack(self)
        initial_path: Path = Path.home() if initial_path is None else initial_path

        self.address_bar: QAddressBar = QAddressBar()
        self.current_path: Path = initial_path
        self.proxy_model: QSortFilterProxyModel = QSortFilterProxyModel()
        self.fs_model: QFileSystemModel = QFileSystemModel()
        self.fs_model.setRootPath(str(initial_path.root))
        self.side_panel_tree: RobustTreeView = RobustTreeView()
        self.main_layout: QVBoxLayout = QVBoxLayout(self)
        self.splitter: QSplitter = QSplitter(Qt.Orientation.Horizontal)
        self.completer: QCompleter = QCompleter(self)

        self.stacked_widget: DynamicView = DynamicView()
        self.preview_view: QLabel = QLabel()

        self.base_icon_size: int = 16
        self.icon_size: int = self.base_icon_size
        self.icon_size_multiplier: float = 1.1
        self.details_max_multiplier: float = 1.5
        self.list_max_multiplier: float = 4.0
        self.view_transition_multiplier: float = 1.0417  # Approximately 1/24 larger
        self.list_min_multiplier: float = self.details_max_multiplier * self.view_transition_multiplier
        self.tiles_min_multiplier: float = self.list_max_multiplier * self.view_transition_multiplier

        self.minimum_multiplier: float = 1.0
        self.maximum_multiplier: float = 16.0

        self.completer.setModel(self.fs_model)
        self.ui.navigation_pane.setModel(self.fs_model)  # pyright: ignore[reportArgumentType]
        self.ui.file_list_view.setModel(self.fs_model)  # pyright: ignore[reportArgumentType]

        self.setup_connections()
        self.setup_shortcuts()
        self.setup_icons()
        self.update_ui()

        self.setup_views()

        self.main_layout.addWidget(self.address_bar, stretch=0)
        self.main_layout.addWidget(self.splitter, stretch=1)
        self.splitter.addWidget(self.side_panel_tree)
        self.splitter.addWidget(self.stacked_widget)
        self.splitter.setStretchFactor(1, 0x7FFFFFFF)  # Stretch the second widget (main view) to fill the remaining space

        self.address_bar.path_changed.connect(self.on_address_bar_path_changed)
        self.fs_model.directoryLoaded.connect(self.on_directory_loaded)

        self.update_address_bar(initial_path)

        # Setup progress bar
        self.progress_bar: QProgressBar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        self.ui.status_bar.addPermanentWidget(self.progress_bar)  # pyright: ignore[reportArgumentType]

        # Setup process pool executor
        self.executor: ProcessPoolExecutor = ProcessPoolExecutor()

        # Setup COM interfaces for Windows
        if platform.system() == "Windows":
            self.setup_com_interfaces()

        # Setup context menu handler
        self.context_menu_handler: FileExplorerContextMenu = FileExplorerContextMenu(self)

        # Setup custom icon provider
        self.icon_provider: QFileIconProvider = QFileIconProvider()
        self.fs_model.setIconProvider(self.icon_provider)

        # Setup file watcher
        self.fs_model.setReadOnly(False)
        self.fs_model.setOption(QFileSystemModel.DontWatchForChanges, False)  # noqa: FBT003

    def setup_com_interfaces(self):
        with suppress(ImportError):
            import comtypes.client as cc  # pyright: ignore[reportMissingTypeStubs]

            self.shell = cc.CreateObject("Shell.Application")
            return
        with suppress(ImportError):
            import win32com.client

            self.shell: CDispatch = win32com.client.Dispatch("Shell.Application")
            return
        RobustLogger().warning("Neither comtypes nor pywin32 is available. COM interfaces will not be used.")

    def setup_icons(self):
        self.ui.back_button.setIcon(QIcon.fromTheme("go-previous"))  # pyright: ignore[reportArgumentType]
        self.ui.forward_button.setIcon(QIcon.fromTheme("go-next"))  # pyright: ignore[reportArgumentType]
        self.ui.up_button.setIcon(QIcon.fromTheme("go-up"))  # pyright: ignore[reportArgumentType]
        self.ui.go_button.setIcon(QIcon.fromTheme("go-jump"))  # pyright: ignore[reportArgumentType]

    def setup_connections(self):
        self.ui.navigation_pane.clicked.connect(self.on_navigation_pane_clicked)
        self.ui.file_list_view.clicked.connect(self.on_file_list_view_clicked)
        self.ui.file_list_view.doubleClicked.connect(self.on_file_list_view_double_clicked)
        self.ui.address_bar.returnPressed.connect(self.on_address_bar_return)
        self.ui.go_button.clicked.connect(self.on_go_button_clicked)
        self.ui.file_list_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)  # pyright: ignore[reportArgumentType]
        self.ui.file_list_view.customContextMenuRequested.connect(self.show_context_menu)
        self.ui.back_button.clicked.connect(self.go_back)
        self.ui.forward_button.clicked.connect(self.go_forward)
        self.ui.up_button.clicked.connect(self.go_up)
        self.ui.search_bar.editingFinished.connect(self.on_search_text_changed)

        # Connect menu actions
        self.ui.action_new_window.triggered.connect(self.new_window)
        self.ui.action_open_windows_terminal.triggered.connect(self.open_windows_terminal)
        self.ui.action_close.triggered.connect(self.close)
        self.ui.action_properties.triggered.connect(self.show_properties)
        self.ui.action_exit.triggered.connect(self.close)

        self.ui.action_cut.triggered.connect(self.cut)
        self.ui.action_copy.triggered.connect(self.copy)
        self.ui.action_paste.triggered.connect(self.paste)
        self.ui.action_delete.triggered.connect(self.delete)
        self.ui.action_select_all.triggered.connect(self.select_all)
        self.ui.action_invert_selection.triggered.connect(self.invert_selection)
        self.ui.action_select_none.triggered.connect(self.select_none)

        self.ui.action_refresh.triggered.connect(self.refresh)
        self.ui.action_list.triggered.connect(lambda: self.stacked_widget.change_view_mode(ViewMode.LIST))
        self.ui.action_details.triggered.connect(lambda: self.stacked_widget.change_view_mode(ViewMode.DETAILS))
        self.ui.action_tiles.triggered.connect(lambda: self.stacked_widget.change_view_mode(ViewMode.TILES))
        self.ui.action_show_hidden_items.triggered.connect(self.toggle_hidden_items)

    def setup_shortcuts(self):
        QShortcut(QKeySequence.Back, self, self.go_back)
        QShortcut(QKeySequence.Forward, self, self.go_forward)
        QShortcut(QKeySequence("Ctrl+Up"), self, self.go_up)
        QShortcut(QKeySequence.Refresh, self, self.refresh)
        QShortcut(QKeySequence.Cut, self, self.cut)
        QShortcut(QKeySequence.Copy, self, self.copy)
        QShortcut(QKeySequence.Paste, self, self.paste)
        QShortcut(QKeySequence.Delete, self, self.delete)
        QShortcut(QKeySequence("F2"), self, self.rename)
        QShortcut(QKeySequence.SelectAll, self, self.select_all)
        QShortcut(QKeySequence("Ctrl+L"), self, self.focus_address_bar)
        QShortcut(QKeySequence("Ctrl+E"), self, self.focus_search_bar)
        QShortcut(QKeySequence("Ctrl+Shift+N"), self, self.create_new_folder)
        QShortcut(QKeySequence("F4"), self, self.open_windows_terminal)

    def on_navigation_pane_clicked(self, index):
        path = self.fs_model.filePath(index)
        self.set_current_path(path)

    def on_file_list_view_clicked(self, index):
        path = self.fs_model.filePath(index)
        self.file_selected.emit(path)

    def on_file_list_view_double_clicked(self, index):
        path = self.fs_model.filePath(index)
        if self.fs_model.isDir(index):
            self.set_current_path(path)
        else:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def on_address_bar_return(self):
        path = self.ui.address_bar.text()
        self.set_current_path(path)

    def on_go_button_clicked(self):
        self.on_address_bar_return()

    def set_current_path(self, path: os.PathLike | str):
        path_obj = Path(path)
        if path_obj.is_dir():
            self.current_path = path_obj
            self.ui.file_list_view.setRootIndex(self.proxy_model.mapFromSource(self.fs_model.index(str(path_obj))))  # pyright: ignore[reportArgumentType]
            self.ui.navigation_pane.setCurrentIndex(self.proxy_model.mapFromSource(self.fs_model.index(str(path_obj))))  # pyright: ignore[reportArgumentType]
            self.ui.address_bar.setText(str(path_obj))
            self.directory_changed.emit(str(path_obj))
            self.add_to_history(path_obj)
            self.update_ui()
        else:
            # Handle invalid path
            self.ui.address_bar.setText(str(self.current_path))

    def add_to_history(self, path: os.PathLike | str):
        if self.navigation_index < len(self.navigation_history) - 1:
            self.navigation_history = self.navigation_history[: self.navigation_index + 1]
        self.navigation_history.append(Path(path))
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

    def on_search_text_changed(self, text):
        self.proxy_model.setFilterRegExp(text)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        proxy_index = self.fs_model.index(str(self.current_path))
        srcIndex = self.proxy_model.mapFromSource(proxy_index)
        self.ui.file_list_view.setRootIndex(srcIndex)  # pyright: ignore[reportArgumentType]

    def focus_address_bar(self):
        self.ui.address_bar.setFocus()
        self.ui.address_bar.selectAll()

    def show_item_context_menu(self, position: QPoint, index: QModelIndex):
        menu = QMenu(self)
        open_action = menu.addAction("Open")
        open_action.triggered.connect(lambda: self.on_file_list_view_double_clicked(index))
        menu.addSeparator()
        cut_action = menu.addAction("Cut")
        cut_action.triggered.connect(self.cut)
        copy_action = menu.addAction("Copy")
        copy_action.triggered.connect(self.copy)
        paste_action = menu.addAction("Paste")
        paste_action.triggered.connect(self.paste)
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(self.delete)
        rename_action = menu.addAction("Rename")
        rename_action.triggered.connect(self.rename)
        menu.addSeparator()
        properties_action = menu.addAction("Properties")
        properties_action.triggered.connect(self.show_properties)
        menu.exec_(QCursor.pos())

    def update_ui(self):
        self.update_status_bar()
        self.ui.back_button.setEnabled(self.navigation_index > 0)
        self.ui.forward_button.setEnabled(self.navigation_index < len(self.navigation_history) - 1)
        self.ui.up_button.setEnabled(self.current_path != Path(QDir.rootPath()))

    def update_status_bar(self):
        selected_items = len(self.ui.file_list_view.selectedIndexes())
        view_model = self.ui.file_list_view.model()
        assert view_model is not None, "View model is None"
        total_items = view_model.rowCount(self.ui.file_list_view.rootIndex())  # pyright: ignore[reportArgumentType]
        if selected_items > 0:
            status_text = f"{selected_items} item{'s' if selected_items > 1 else ''} selected"
        else:
            status_text = f"{total_items} item{'s' if total_items > 1 else ''}"
        self.ui.status_bar.addWidget(QLabel(status_text))  # pyright: ignore[reportArgumentType]

        root_index = self.ui.file_list_view.rootIndex()
        fs_model: QFileSystemModel = self.fs_model
        proxy_model: QSortFilterProxyModel = self.proxy_model

        def get_source_index(i: int) -> QModelIndex:
            proxy_index = view_model.index(i, 0, root_index)  # pyright: ignore[reportArgumentType]
            return proxy_model.mapToSource(proxy_index)  # pyright: ignore[reportArgumentType]

        total_size = sum(fs_model.size(get_source_index(i)) for i in range(total_items))
        self.ui.status_size.setText(self.format_size(total_size))

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

    def show_properties(self):
        selected_indexes = self.ui.file_list_view.selectedIndexes()
        if selected_indexes:
            file_path = Path(self.fs_model.filePath(self.proxy_model.mapToSource(selected_indexes[0])))
            properties = f"Name: {file_path.name}\n"
            properties += f"Type: {'Directory' if file_path.is_dir() else 'File'}\n"
            properties += f"Size: {self.format_size(file_path.stat().st_size)}\n"
            properties += f"Created: {file_path.stat().st_ctime}\n"
            properties += f"Modified: {file_path.stat().st_mtime}\n"
            properties += f"Accessed: {file_path.stat().st_atime}\n"

            QMessageBox.information(self, "Properties", properties)

    def cut(self):
        self.copy(cut=True)

    def copy(self, cut: bool = False):  # noqa: FBT001, FBT002
        selected_indexes = self.ui.file_list_view.selectedIndexes()
        if selected_indexes:
            source_paths = [Path(self.fs_model.filePath(index)) for index in selected_indexes]  # pyright: ignore[reportArgumentType]
            mime_data = QMimeData()
            urls = [QUrl.fromLocalFile(str(path)) for path in source_paths]
            mime_data.setUrls(urls)
            self.clipboard.setMimeData(mime_data)

            if cut:
                self.to_cut = source_paths
            else:
                self.to_cut = None

    def paste(self):
        mime_data = self.clipboard.mimeData()
        if mime_data.hasUrls():
            source_paths = [Path(url.toLocalFile()) for url in mime_data.urls()]
            destination_path = self.current_path

            if hasattr(self, "to_cut") and self.to_cut:
                command = MoveCommand(source_paths, destination_path)
            else:
                command = CopyCommand(source_paths, destination_path)

            self.undo_stack.push(command)
            self.refresh()

            if hasattr(self, "to_cut"):
                self.to_cut = None

    def delete(self):
        selected_indexes = self.ui.file_list_view.selectedIndexes()
        if selected_indexes:
            paths = [Path(self.fs_model.filePath(index)) for index in selected_indexes]  # pyright: ignore[reportArgumentType]
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
                self.refresh()

    def rename(self):
        selected_indexes = self.ui.file_list_view.selectedIndexes()
        if selected_indexes:
            file_path = Path(self.fs_model.filePath(selected_indexes[0]))  # pyright: ignore[reportArgumentType]
            new_name, ok = QInputDialog.getText(self, "Rename", "Enter new name:", QLineEdit.Normal, file_path.name)
            if ok and new_name:
                new_path = file_path.with_name(new_name)
                if new_path.exists():
                    QMessageBox.warning(self, "Rename", "A file with this name already exists.")
                else:
                    command = RenameCommand(file_path, new_path)
                    self.undo_stack.push(command)
                    self.refresh()

    def run_in_background(
        self,
        func: Callable,
        *args,
        callback: Callable[[Future[Any]], None] | None = None,
        **kwargs,
    ):
        future = self.executor.submit(func, *args, **kwargs)
        if callback is not None:
            future.add_done_callback(callback)

    def update_progress(self, value: int):
        self.progress_bar.setValue(value)
        if value >= 100:  # noqa: PLR2004
            self.progress_bar.setVisible(False)
        elif not self.progress_bar.isVisible():
            self.progress_bar.setVisible(True)

    def select_all(self):
        self.ui.file_list_view.selectAll()

    def invert_selection(self):
        selection_model = self.ui.file_list_view.selectionModel()
        assert isinstance(selection_model, QItemSelectionModel), f"Selection model is not a QItemSelectionModel, instead was a {type(selection_model)}"
        for i in range(self.fs_model.rowCount(self.ui.file_list_view.rootIndex())):  # pyright: ignore[reportArgumentType]
            index = self.fs_model.index(i, 0, self.ui.file_list_view.rootIndex())  # pyright: ignore[reportArgumentType]
            selection_model.select(index, QItemSelectionModel.SelectionFlag.Toggle)  # pyright: ignore[reportCallIssue, reportArgumentType]

    def select_none(self):
        self.ui.file_list_view.clearSelection()

    def refresh(self):
        current_index = self.fs_model.index(self.current_path)  # pyright: ignore[reportArgumentType]
        self.fs_model.setRootPath(self.current_path)  # pyright: ignore[reportArgumentType]
        self.ui.file_list_view.setRootIndex(current_index)  # pyright: ignore[reportArgumentType]
        self.update_ui()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if isinstance(event, QWheelEvent) and event.type() == QEvent.Type.Wheel and bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            delta = event.angleDelta().y() / 120  # This gives us -1 or 1 for most mouse wheels
            self.stacked_widget.change_icon_size(delta * 0.25)
            return True
        return super().eventFilter(obj, event)

    def update_address_bar(self, path: Path):
        self.address_bar.update_path(path)
        self.update_address_bar_contents(path)

    def update_address_bar_contents(self, path: Path):
        contents = []

        # Add parent folders
        current = path
        while current != current.parent:
            index = self.fs_model.index(str(current))
            name = current.name or str(current)  # Use str(current) for root directory
            icon = self.fs_model.fileIcon(index)
            contents.insert(0, (name, current, icon))
            current = current.parent

        # Add root directory if not already included
        if not contents or contents[0][1] != current:
            index = self.fs_model.index(str(current))
            icon = self.fs_model.fileIcon(index)
            contents.insert(0, (str(current), current, icon))

        # Add current directory contents
        index = self.fs_model.index(str(path))
        for i in range(self.fs_model.rowCount(index)):
            child_index = self.fs_model.index(i, 0, index)
            child_path = Path(self.fs_model.filePath(child_index))
            if child_path.is_dir():
                name = child_path.name
                icon = self.fs_model.fileIcon(child_index)
                contents.append((name, child_path, icon))

        self.address_bar.set_directory_contents(path, contents)

    def on_address_bar_path_changed(self, path: Path):
        self.change_path(path)

    def on_directory_loaded(self, path: str):
        loaded_path = Path(path)
        if loaded_path == self.current_path:
            self.update_address_bar_contents(loaded_path)

    def setup_views(self):
        self.stacked_widget.setup_views()

        # Set the root index of the tree view to the root of the file system model
        self.side_panel_tree.setRootIndex(self.fs_model.index(""))
        self.side_panel_tree.expandToDepth(0)  # Expand the root level to show all drives

        min_tree_width = 200
        self.side_panel_tree.setMinimumWidth(min_tree_width)
        self.side_panel_tree.setModel(self.fs_model)
        self.side_panel_tree.setRootIndex(self.fs_model.index(QDir.rootPath()))
        self.side_panel_tree.clicked.connect(self.on_view_clicked)
        # Modify the QTreeView to show only the Name column
        for i in range(1, self.fs_model.columnCount()):
            self.side_panel_tree.hideColumn(i)

    def change_path(self, path: Path):
        self.current_path = path
        index = self.fs_model.index(str(path))
        self.stacked_widget.list_view.setRootIndex(index)
        self.stacked_widget.table_view.setRootIndex(index)
        self.stacked_widget.tiles_view.setRootIndex(index)
        self.side_panel_tree.setCurrentIndex(index)
        self.update_address_bar(path)

    def on_view_clicked(self, index: QModelIndex):
        path = Path(self.fs_model.filePath(index))
        self.change_path(path)

    def on_item_double_clicked(self, index: QModelIndex):
        path = Path(self.fs_model.filePath(index))
        if path.is_dir():
            self.change_path(path)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.stacked_widget.update_view()

    def show_context_menu(self, pos: QPoint):
        current_view: QWidget = self.stacked_widget.currentWidget()
        assert isinstance(current_view, (QListView, QTableView, RobustTileView)), f"Current view is not a QListView, instead was a {type(current_view)}"
        index: QModelIndex = current_view.indexAt(pos)
        if index.isValid():
            self.show_item_context_menu(pos, index)
        else:
            self.show_empty_space_context_menu(pos)

    def create_new_folder(self):
        folder_name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and folder_name:
            new_folder_path = Path(self.current_path) / folder_name
            try:
                new_folder_path.mkdir(parents=True, exist_ok=True)
                self.refresh()
            except OSError:
                QMessageBox.warning(self, "Error", "Failed to create new folder.")

    def create_new_file(self):
        file_name, ok = QInputDialog.getText(self, "New File", "Enter file name:")
        if ok and file_name:
            new_file_path = QDir(str(self.current_path)).filePath(file_name)
            file = QFile(new_file_path)
            if file.open(QFile.WriteOnly):
                file.close()
                self.fs_model.setRootPath(str(self.current_path))  # Refresh the view
            else:
                QMessageBox.warning(self, "Error", "Failed to create file.")

    def cut_file(self, file_path: str):
        self.copy_file(file_path)
        self.clipboard_operation = "cut"

    def show_empty_space_context_menu(self, pos: QPoint):
        context_menu = QMenu(self)
        new_folder_action = context_menu.addAction("New Folder")
        new_file_action = context_menu.addAction("New File")
        context_menu.addSeparator()
        paste_action = context_menu.addAction("Paste")
        paste_action.setEnabled(QGuiApplication.clipboard().mimeData().hasUrls())  # pyright: ignore[reportArgumentType]

        current_view = self.stacked_widget.currentWidget()
        action = context_menu.exec_(current_view.mapToGlobal(pos))

        if action == new_folder_action:
            self.create_new_folder()
        elif action == new_file_action:
            self.create_new_file()
        elif action == paste_action:
            self.paste_file()

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
        filters = self.fs_model.filter()
        if bool(filters & QDir.Hidden):
            self.fs_model.setFilter(filters & ~QDir.Hidden)
            self.ui.action_show_hidden_items.setText("Show Hidden Items")
        else:
            self.fs_model.setFilter(filters | QDir.Hidden)
            self.ui.action_show_hidden_items.setText("Hide Hidden Items")
        self.refresh()

    def copy_file(self, file_path: str):
        try:
            clipboard = QGuiApplication.clipboard()
            mime_data = QMimeData()

            # Set the URL
            mime_data.setUrls([QUrl.fromLocalFile(file_path)])  # pyright: ignore[reportArgumentType]
            mime_data.setText(file_path)

            # Platform-specific handling
            if platform.system() == "Windows":
                mime_data.setData('application/x-qt-windows-mime;value="FileName"', file_path.encode("utf-16"))
            elif platform.system() == "Linux":
                mime_data.setData("x-special/gnome-copied-files", f"copy\n{file_path}".encode())

            clipboard.setMimeData(mime_data)
            self.clipboard_operation = "copy"
        except Exception as e:  # noqa: BLE001
            RobustLogger().exception("Failed to copy to clipboard")
            QMessageBox.warning(
                self,
                "Clipboard Error",
                f"Failed to copy to clipboard (this was a {e.__class__.__name__} exception). Please try again.",
            )

    def paste_file(self):
        clipboard: QClipboard = QGuiApplication.clipboard()
        mime_data: QMimeData = clipboard.mimeData()
        if mime_data.hasUrls():
            for url in mime_data.urls():
                source_path = url.toLocalFile()
                file_info = QFileInfo(source_path)
                dest_path = QDir(str(self.current_path)).filePath(file_info.fileName())

                if self.clipboard_operation == "cut":
                    QFile.rename(source_path, dest_path)
                else:
                    QFile.copy(source_path, dest_path)

            self.fs_model.setRootPath(str(self.current_path))
            if self.clipboard_operation == "cut":
                clipboard.clear()

    def delete_file(self, file_path: str):
        reply: QMessageBox.StandardButton = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete {file_path}?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.StandardButton.Yes:
            file_info = QFileInfo(file_path)
            if file_info.isDir():
                qdir = QDir(file_path)
                if qdir.removeRecursively():
                    self.fs_model.setRootPath(str(self.current_path))  # Refresh the view
                else:
                    QMessageBox.warning(self, "Error", "Failed to delete directory.")
            elif QFile.remove(file_path):
                self.fs_model.setRootPath(str(self.current_path))  # Refresh the view
            else:
                QMessageBox.warning(self, "Error", "Failed to delete file.")

    def focus_search_bar(self):
        self.ui.search_bar.setFocus()
        self.ui.search_bar.selectAll()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            source_path = Path(url.toLocalFile())
            destination_path: Path = Path(self.current_path) / source_path.name
            if source_path.is_dir():
                shutil.copytree(source_path, destination_path)
            else:
                shutil.copy2(source_path, destination_path)
        self.refresh()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = QMainWindow()
    file_explorer = FileSystemExplorerWidget()
    main_window.setCentralWidget(file_explorer)
    main_window.setWindowTitle("File System Explorer")
    main_window.resize(1000, 600)
    main_window.show()
    sys.exit(app.exec_())
