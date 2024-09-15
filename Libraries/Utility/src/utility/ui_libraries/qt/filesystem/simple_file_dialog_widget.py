from __future__ import annotations

import platform
import sys

from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING

from loggerplus import RobustLogger
from qtpy.QtCore import QDir, QEvent, QFile, QFileInfo, QItemSelectionModel, QMimeData, QModelIndex, QSize, QUrl, Qt
from qtpy.QtGui import QGuiApplication, QWheelEvent
from qtpy.QtWidgets import (
    QApplication,
    QCompleter,
    QFileSystemModel,
    QInputDialog,
    QListView,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from utility.ui_libraries.qt.debug.print_qobject import print_qt_class_calls
from utility.ui_libraries.qt.filesystem.address_bar import PyQAddressBar
from utility.ui_libraries.qt.widgets.itemviews.listview import RobustListView
from utility.ui_libraries.qt.widgets.itemviews.tableview import RobustTableView
from utility.ui_libraries.qt.widgets.itemviews.tile_delegate import TileItemDelegate
from utility.ui_libraries.qt.widgets.itemviews.treeview import RobustTreeView

if TYPE_CHECKING:
    from qtpy.QtCore import QObject, QPoint, QRect
    from qtpy.QtGui import QMouseEvent, QResizeEvent


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


@print_qt_class_calls(exclude_funcs=["paint", "sizeHint", "eventFilter"])
class FileSystemExplorerWidget(QWidget):
    def __init__(self, initial_path: Path | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        initial_path = Path.home() if initial_path is None else initial_path

        self.address_bar: PyQAddressBar = PyQAddressBar()
        self.current_path: Path = initial_path
        self.fs_model: QFileSystemModel = QFileSystemModel()
        self.fs_model.setRootPath("")  # Set root path to the file system root
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

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if (
            isinstance(event, QWheelEvent)
            and event.type() == QEvent.Type.Wheel
            and bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
        ):
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
        else:  # ViewMode.TILES
            self.tiles_view.setIconSize(icon_size)

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

    def show_item_context_menu(self, pos: QPoint, index: QModelIndex):
        context_menu = QMenu(self)
        cut_action = context_menu.addAction("Cut")
        copy_action = context_menu.addAction("Copy")
        delete_action = context_menu.addAction("Delete")
        context_menu.addSeparator()
        properties_action = context_menu.addAction("Properties")

        file_path = self.fs_model.filePath(index)
        current_view = self.stacked_widget.currentWidget()
        action = context_menu.exec_(current_view.mapToGlobal(pos))

        if action == cut_action:
            self.cut_file(file_path)
        elif action == copy_action:
            self.copy_file(file_path)
        elif action == delete_action:
            self.delete_file(file_path)
        elif action == properties_action:
            self.show_properties(file_path)

    def show_empty_space_context_menu(self, pos: QPoint):
        context_menu = QMenu(self)
        new_folder_action = context_menu.addAction("New Folder")
        new_file_action = context_menu.addAction("New File")
        context_menu.addSeparator()
        paste_action = context_menu.addAction("Paste")
        paste_action.setEnabled(QGuiApplication.clipboard().mimeData().hasUrls())

        current_view = self.stacked_widget.currentWidget()
        action = context_menu.exec_(current_view.mapToGlobal(pos))

        if action == new_folder_action:
            self.create_new_folder()
        elif action == new_file_action:
            self.create_new_file()
        elif action == paste_action:
            self.paste_file()

    def create_new_folder(self):
        folder_name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and folder_name:
            new_folder_path = QDir(str(self.current_path)).filePath(folder_name)
            if QDir().mkdir(new_folder_path):
                self.fs_model.setRootPath(str(self.current_path))  # Refresh the view
            else:
                QMessageBox.warning(self, "Error", "Failed to create folder.")

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

    def copy_file(self, file_path: str):
        try:
            clipboard = QGuiApplication.clipboard()
            mime_data = QMimeData()

            # Set the URL
            url = QUrl.fromLocalFile(file_path)
            mime_data.setUrls([url])

            # Set plain text (for applications that don't support URLs)
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

    def show_properties(self, file_path: str):
        file_info = QFileInfo(file_path)
        properties = f"Name: {file_info.fileName()}\n"
        properties += f"Path: {file_info.filePath()}\n"
        properties += f"Size: {file_info.size()} bytes\n"
        properties += f"Created: {file_info.birthTime().toString()}\n"
        properties += f"Modified: {file_info.lastModified().toString()}\n"
        properties += f"Permissions: {self.get_permissions_string(file_info)}"

        QMessageBox.information(self, "File Properties", properties)

    def get_permissions_string(self, file_info: QFileInfo) -> str:
        permissions = []
        if file_info.isReadable():
            permissions.append("Read")
        if file_info.isWritable():
            permissions.append("Write")
        if file_info.isExecutable():
            permissions.append("Execute")
        return ", ".join(permissions)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = QMainWindow()
    file_explorer = FileSystemExplorerWidget()
    main_window.setCentralWidget(file_explorer)
    main_window.setWindowTitle("File System Explorer")
    main_window.resize(1000, 600)
    main_window.show()
    sys.exit(app.exec_())
