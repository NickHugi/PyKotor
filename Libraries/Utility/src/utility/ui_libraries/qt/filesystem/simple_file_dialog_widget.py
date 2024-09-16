from __future__ import annotations

import platform
import shutil
import subprocess
import sys

from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING

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
    QSize,
    QUrl,
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QCursor, QDesktopServices, QGuiApplication, QIcon, QKeySequence, QWheelEvent
from qtpy.QtWidgets import (
    QApplication,
    QCompleter,
    QFileSystemModel,
    QInputDialog,
    QListView,
    QMainWindow,
    QMenu,
    QMessageBox,
    QShortcut,
    QSplitter,
    QStackedWidget,
    QTableView,
    QTreeView,
    QUndoStack,
    QVBoxLayout,
    QWidget,
)

from utility.ui_libraries.qt.debug.print_qobject import print_qt_class_calls
from utility.ui_libraries.qt.filesystem.address_bar import PyQAddressBar
from utility.ui_libraries.qt.widgets.itemviews.listview import RobustListView
from utility.ui_libraries.qt.widgets.itemviews.tableview import RobustTableView
from utility.ui_libraries.qt.widgets.itemviews.tileview import TileItemDelegate
from utility.ui_libraries.qt.widgets.itemviews.treeview import RobustTreeView

if TYPE_CHECKING:
    import os

    from qtpy.QtCore import QObject, QPoint, QRect
    from qtpy.QtGui import QDragEnterEvent, QDropEvent, QMouseEvent, QResizeEvent
    from qtpy.QtWidgets import QWidget


# Apply the decorator to all functions in the file
@print_qt_class_calls(exclude_funcs=["paint", "sizeHint"])
class QTileView(RobustListView):
    """A view that displays items in a 2D grid."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setViewMode(QListView.ViewMode.IconMode)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setWrapping(True)
        self.setUniformItemSizes(False)
        self.setItemDelegate(TileItemDelegate(self))

    def setIconSize(self, size: QSize):
        super().setIconSize(size)
        self.setGridSize(QSize(size.width(), size.height()))


class ViewMode(Enum):
    DETAILS = auto()
    LIST = auto()
    TILES = auto()


@print_qt_class_calls(exclude_funcs=["paint", "sizeHint", "eventFilter"])
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


class FileSystemExplorerWidget(QMainWindow):
    file_selected = Signal(str)
    directory_changed = Signal(str)

    def __init__(self, initial_path: Path | None = None, parent: QWidget | None = None):
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
        self.current_path: Path = Path.home()
        self.navigation_history: list[Path] = []
        self.navigation_index: int = -1
        self.clipboard = QApplication.clipboard()
        self.undo_stack = QUndoStack(self)
        initial_path = Path.home() if initial_path is None else initial_path

        self.address_bar: PyQAddressBar = PyQAddressBar()
        self.current_path: Path = initial_path
        self.fs_model: QFileSystemModel = QFileSystemModel()
        self.fs_model.setRootPath(str(initial_path.root))
        self.tree_view: RobustTreeView = RobustTreeView()
        self.main_layout: QVBoxLayout = QVBoxLayout(self)
        self.splitter: QSplitter = QSplitter(Qt.Orientation.Horizontal)
        self.completer: QCompleter = QCompleter(self)

        self.stacked_widget: QStackedWidget = QStackedWidget()
        self.list_view: RobustListView = RobustListView()
        self.table_view: FirstColumnInteractableTableView = FirstColumnInteractableTableView()
        self.tiles_view: QTileView = QTileView()
        self.list_view.viewport().installEventFilter(self)
        self.table_view.viewport().installEventFilter(self)
        self.tiles_view.viewport().installEventFilter(self)
        self.current_view: ViewMode = ViewMode.DETAILS

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

        # Hide all columns in navigation pane except the first one
        for i in range(1, self.fs_model.columnCount()):
            self.ui.navigation_pane.hideColumn(i)
        self.setup_connections()
        self.setup_shortcuts()
        self.setup_icons()
        self.update_ui()

        self.setup_views()

        self.main_layout.addWidget(self.address_bar, stretch=0)
        self.main_layout.addWidget(self.splitter, stretch=1)
        self.splitter.addWidget(self.tree_view)
        self.splitter.addWidget(self.stacked_widget)
        self.splitter.setStretchFactor(1, 0x7FFFFFFF)  # Stretch the second widget (main view) to fill the remaining space
        self.stacked_widget.addWidget(self.table_view)
        self.stacked_widget.addWidget(self.list_view)
        self.stacked_widget.addWidget(self.tiles_view)
        self.stacked_widget.setCurrentWidget(self.table_view)

        self.address_bar.path_changed.connect(self.on_address_bar_path_changed)
        self.fs_model.directoryLoaded.connect(self.on_directory_loaded)

        self.update_address_bar(initial_path)

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
        self.ui.file_list_view.setContextMenuPolicy(Qt.CustomContextMenu)  # pyright: ignore[reportArgumentType]
        self.ui.file_list_view.customContextMenuRequested.connect(self.show_context_menu)
        self.ui.back_button.clicked.connect(self.go_back)
        self.ui.forward_button.clicked.connect(self.go_forward)
        self.ui.up_button.clicked.connect(self.go_up)
        self.ui.search_bar.textChanged.connect(self.on_search_text_changed)

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
        self.ui.action_extra_large_icons.triggered.connect(lambda: self.change_view_mode("extra_large_icons"))
        self.ui.action_large_icons.triggered.connect(lambda: self.change_view_mode("large_icons"))
        self.ui.action_medium_icons.triggered.connect(lambda: self.change_view_mode("medium_icons"))
        self.ui.action_small_icons.triggered.connect(lambda: self.change_view_mode("small_icons"))
        self.ui.action_list.triggered.connect(lambda: self.change_view_mode("list"))
        self.ui.action_details.triggered.connect(lambda: self.change_view_mode("details"))
        self.ui.action_tiles.triggered.connect(lambda: self.change_view_mode("tiles"))
        self.ui.action_content.triggered.connect(lambda: self.change_view_mode("content"))
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
            self.ui.file_list_view.setRootIndex(self.fs_model.index(str(path_obj)))  # pyright: ignore[reportArgumentType]
            self.ui.navigation_pane.setCurrentIndex(self.fs_model.index(str(path_obj)))  # pyright: ignore[reportArgumentType]
            self.ui.address_bar.setText(str(path_obj))
            self.directory_changed.emit(path_obj)
            self.add_to_history(path_obj)
            self.update_ui()
        else:
            # Handle invalid path
            self.ui.address_bar.setText(str(self.current_path))

    def add_to_history(self, path):
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

    def on_search_text_changed(self, text):
        if text:
            self.fs_model.setNameFilters([f"*{text}*"])
            self.fs_model.setNameFilterDisables(False)
        else:
            self.fs_model.setNameFilters([])
            self.fs_model.setNameFilterDisables(True)
        self.ui.file_list_view.setRootIndex(self.fs_model.index(str(self.current_path)))  # pyright: ignore[reportArgumentType]

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
        self.ui.up_button.setEnabled(self.current_path != QDir.rootPath())

    def update_status_bar(self):
        selected_items = len(self.ui.file_list_view.selectedIndexes())
        view_model = self.ui.file_list_view.model()
        assert view_model is not None, "View model is None"
        total_items = view_model.rowCount(self.ui.file_list_view.rootIndex())  # pyright: ignore[reportArgumentType]
        if selected_items > 0:
            status_text = f"{selected_items} item{'s' if selected_items > 1 else ''} selected"
        else:
            status_text = f"{total_items} item{'s' if total_items > 1 else ''}"
        self.ui.status_items.setText(status_text)

        total_size = sum(
            self.fs_model.size(view_model.index(i, 0, self.ui.file_list_view.rootIndex()))  # pyright: ignore[reportCallIssue, reportArgumentType]
            for i in range(total_items)
        )
        self.ui.status_size.setText(self.format_size(total_size))

    def format_size(self, size):
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def new_window(self):
        new_window = FileSystemExplorerWidget()
        new_window.show()

    def open_windows_terminal(self):
        subprocess.Popen(f'start cmd /K "cd /d {self.current_path}"', shell=True)

    def show_properties(self):
        selected_indexes = self.ui.file_list_view.selectedIndexes()
        if selected_indexes:
            file_path = Path(self.fs_model.filePath(selected_indexes[0]))  # pyright: ignore[reportArgumentType]
            properties = f"Name: {file_path.name}\n"
            properties += f"Type: {'Directory' if file_path.is_dir() else 'File'}\n"
            properties += f"Size: {self.format_size(file_path.stat().st_size)}\n"
            properties += f"Created: {file_path.stat().st_ctime}\n"
            properties += f"Modified: {file_path.stat().st_mtime}\n"
            properties += f"Accessed: {file_path.stat().st_atime}\n"

            QMessageBox.information(self, "Properties", properties)

    def cut(self):
        self.copy(cut=True)

    def copy(self, cut: bool = False):
        selected_indexes = self.ui.file_list_view.selectedIndexes()
        if selected_indexes:
            urls = [QUrl.fromLocalFile(self.fs_model.filePath(index)) for index in selected_indexes]  # pyright: ignore[reportArgumentType]
            mime_data = QMimeData()
            mime_data.setUrls(urls)
            self.clipboard.setMimeData(mime_data)
            if cut:
                self.to_cut = urls
            else:
                self.to_cut = None

    def paste(self):
        mime_data = self.clipboard.mimeData()
        if mime_data.hasUrls():
            for url in mime_data.urls():
                source_path = Path(url.toLocalFile())
                destination_path = self.current_path / source_path.name

                if hasattr(self, "to_cut") and self.to_cut and url in self.to_cut:
                    shutil.move(source_path, destination_path)
                elif source_path.is_dir():
                    shutil.copytree(source_path, destination_path)
                else:
                    shutil.copy2(source_path, destination_path)

            self.refresh()
            if hasattr(self, "to_cut"):
                self.to_cut = None

    def delete(self):
        selected_indexes = self.ui.file_list_view.selectedIndexes()
        if selected_indexes:
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete {len(selected_indexes)} item(s)?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                for index in selected_indexes:
                    file_path = Path(self.fs_model.filePath(index))  # pyright: ignore[reportArgumentType]
                    if file_path.is_dir():
                        shutil.rmtree(file_path)
                    else:
                        file_path.unlink(missing_ok=True)
                self.refresh()

    def rename(self):
        selected_indexes = self.ui.file_list_view.selectedIndexes()
        if len(selected_indexes) == 1:
            old_name = self.fs_model.fileName(selected_indexes[0])  # pyright: ignore[reportArgumentType]
            new_name, ok = QInputDialog.getText(self, "Rename", "Enter new name:", text=old_name)
            if ok and new_name:
                old_path = Path(self.fs_model.filePath(selected_indexes[0]))  # pyright: ignore[reportArgumentType]
                new_path = old_path.parent / new_name
                old_path.rename(new_path)
                self.refresh()

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
            self.change_icon_size(delta * 0.25)
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
        for view in (self.list_view, self.table_view, self.tiles_view):
            view.setModel(self.fs_model)
            view.setRootIndex(self.fs_model.index(str(self.current_path)))
            view.doubleClicked.connect(self.on_item_double_clicked)
            view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            view.customContextMenuRequested.connect(self.show_context_menu)
            view.viewport().installEventFilter(self)

        qsize_for_icon = QSize(self.icon_size, self.icon_size)
        self.list_view.setIconSize(qsize_for_icon)
        self.table_view.setIconSize(qsize_for_icon)
        self.tiles_view.setIconSize(qsize_for_icon)

        self.list_view.setViewMode(QListView.ViewMode.ListMode)
        self.list_view.setResizeMode(QListView.ResizeMode.Adjust)
        self.list_view.setWrapping(False)
        self.list_view.setUniformItemSizes(True)

        self.table_view.horizontalHeader().setVisible(False)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setShowGrid(False)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)
        self.table_view.setColumnWidth(0, 200)  # Set a reasonable width for the first column
        self.table_view.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)  # Disable editing

        # Set the root index of the tree view to the root of the file system model
        self.tree_view.setRootIndex(self.fs_model.index(""))
        self.tree_view.expandToDepth(0)  # Expand the root level to show all drives

        min_tree_width = 200
        self.tree_view.setMinimumWidth(min_tree_width)
        self.tree_view.setModel(self.fs_model)
        self.tree_view.setRootIndex(self.fs_model.index(QDir.rootPath()))
        self.tree_view.clicked.connect(self.on_tree_view_clicked)

        # Modify the QTreeView to show only the Name column
        self.tree_view.setModel(self.fs_model)
        for i in range(1, self.fs_model.columnCount()):
            self.tree_view.hideColumn(i)

    def update_icon_size(self):
        self.icon_size = int(self.base_icon_size * self.icon_size_multiplier)

    def update_view(self):
        self.update_icon_size()
        icon_size = QSize(self.icon_size, self.icon_size)

        if self.current_view == ViewMode.DETAILS:
            self.table_view.setIconSize(icon_size)
            self.table_view.horizontalHeader().setVisible(True)
            self.table_view.verticalHeader().setVisible(False)
            self.table_view.setShowGrid(False)
            self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
            self.table_view.resizeColumnsToContents()
            self.table_view.horizontalHeader().setStretchLastSection(True)
        elif self.current_view == ViewMode.LIST:
            self.list_view.setViewMode(QListView.ViewMode.ListMode)
            self.list_view.setIconSize(icon_size)
            self.list_view.setResizeMode(QListView.ResizeMode.Adjust)
            self.list_view.setWrapping(False)
            self.list_view.setUniformItemSizes(True)
            self.list_view.setModelColumn(0)
        elif self.current_view == ViewMode.TILES:
            self.tiles_view.setIconSize(icon_size)
        else:
            raise ValueError(f"Invalid view mode: {self.current_view}")

    def change_path(self, path: Path):
        self.current_path = path
        index = self.fs_model.index(str(path))
        self.list_view.setRootIndex(index)
        self.table_view.setRootIndex(index)
        self.tiles_view.setRootIndex(index)
        self.tree_view.setCurrentIndex(index)
        self.update_address_bar(path)

    def on_tree_view_clicked(self, index: QModelIndex):
        path = Path(self.fs_model.filePath(index))
        self.change_path(path)

    def on_item_double_clicked(self, index: QModelIndex):
        path = Path(self.fs_model.filePath(index))
        if path.is_dir():
            self.change_path(path)

    def toggle_view(self):
        if self.current_view == ViewMode.DETAILS:
            self.current_view = ViewMode.LIST
            self.stacked_widget.setCurrentWidget(self.list_view)
        elif self.current_view == ViewMode.LIST:
            self.current_view = ViewMode.TILES
            self.stacked_widget.setCurrentWidget(self.tiles_view)
        else:
            self.current_view = ViewMode.DETAILS
            self.stacked_widget.setCurrentWidget(self.table_view)
        self.update_view()

    def change_view_mode(self, mode):
        if mode == "extra_large_icons":
            self.ui.file_list_view.setViewMode(QListView.IconMode)  # pyright: ignore[reportArgumentType]
            self.ui.file_list_view.setIconSize(QSize(96, 96))  # pyright: ignore[reportArgumentType]
            self.ui.file_list_view.setGridSize(QSize(120, 120))  # pyright: ignore[reportArgumentType]
        elif mode == "large_icons":
            self.ui.file_list_view.setViewMode(QListView.IconMode)  # pyright: ignore[reportArgumentType]
            self.ui.file_list_view.setIconSize(QSize(48, 48))  # pyright: ignore[reportArgumentType]
            self.ui.file_list_view.setGridSize(QSize(80, 80))  # pyright: ignore[reportArgumentType]
        elif mode == "medium_icons":
            self.ui.file_list_view.setViewMode(QListView.IconMode)  # pyright: ignore[reportArgumentType]
            self.ui.file_list_view.setIconSize(QSize(32, 32))  # pyright: ignore[reportArgumentType]
            self.ui.file_list_view.setGridSize(QSize(60, 60))  # pyright: ignore[reportArgumentType]
        elif mode == "small_icons":
            self.ui.file_list_view.setViewMode(QListView.IconMode)  # pyright: ignore[reportArgumentType]
            self.ui.file_list_view.setIconSize(QSize(16, 16))  # pyright: ignore[reportArgumentType]
            self.ui.file_list_view.setGridSize(QSize(40, 40))  # pyright: ignore[reportArgumentType]
        elif mode == "list":
            self.ui.file_list_view.setViewMode(QListView.ListMode)  # pyright: ignore[reportArgumentType]
            self.ui.file_list_view.setIconSize(QSize(16, 16))  # pyright: ignore[reportArgumentType]
            self.ui.file_list_view.setGridSize(QSize())  # pyright: ignore[reportArgumentType]
        elif mode == "details":
            assert isinstance(self.ui.file_list_view, QTreeView)
            # Switch to QTreeView for details view
            self.ui.file_list_view.setViewMode(QListView.ListMode)  # pyright: ignore[reportArgumentType]
            self.ui.file_list_view.setIconSize(QSize(16, 16))  # pyright: ignore[reportArgumentType]
            self.ui.file_list_view.setGridSize(QSize())  # pyright: ignore[reportArgumentType]
            # Show all columns
            for i in range(self.fs_model.columnCount()):
                self.ui.file_list_view.setColumnHidden(i, False)
        elif mode == "tiles":
            self.ui.file_list_view.setViewMode(QListView.IconMode)  # pyright: ignore[reportArgumentType]
            self.ui.file_list_view.setIconSize(QSize(32, 32))  # pyright: ignore[reportArgumentType]
            self.ui.file_list_view.setGridSize(QSize(120, 80))  # pyright: ignore[reportArgumentType]
        elif mode == "content":
            # Similar to details view but with a preview pane
            self.change_view_mode("details")
            # Add a preview pane here if needed

    def change_icon_size(self, delta: float):
        new_multiplier = max(
            self.minimum_multiplier,
            min(self.maximum_multiplier, self.icon_size_multiplier + delta),
        )
        if new_multiplier != self.icon_size_multiplier:
            self.icon_size_multiplier = new_multiplier

            if self.icon_size_multiplier <= self.details_max_multiplier:
                self.current_view = ViewMode.DETAILS
                self.stacked_widget.setCurrentWidget(self.table_view)
            elif self.list_min_multiplier <= self.icon_size_multiplier <= self.list_max_multiplier:
                self.current_view = ViewMode.LIST
                self.stacked_widget.setCurrentWidget(self.list_view)
            else:
                self.current_view = ViewMode.TILES
                self.stacked_widget.setCurrentWidget(self.tiles_view)

            self.update_view()

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.update_view()

    def show_context_menu(self, pos: QPoint):
        current_view = self.stacked_widget.currentWidget()
        assert isinstance(current_view, (QListView, QTableView, QTileView)), f"Current view is not a QListView, instead was a {type(current_view)}"

        index = current_view.indexAt(pos)
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
        clipboard = QGuiApplication.clipboard()
        mime_data = clipboard.mimeData()
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
        reply = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete {file_path}?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
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
            destination_path = Path(self.current_path) / source_path.name
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
