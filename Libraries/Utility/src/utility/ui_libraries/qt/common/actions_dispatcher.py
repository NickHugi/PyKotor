from __future__ import annotations

import contextlib
import platform

from pathlib import Path
from typing import TYPE_CHECKING, Any

from loggerplus import RobustLogger
from qtpy.QtCore import QByteArray, QItemSelectionModel, QMimeData, QModelIndex, QSortFilterProxyModel, QUrl, Qt
from qtpy.QtWidgets import QAbstractItemView, QApplication, QFileSystemModel, QInputDialog, QListView, QMessageBox

from utility.ui_libraries.qt.common.menu_definitions import FileExplorerMenus
from utility.ui_libraries.qt.common.tasks.actions_executor import FileActionsExecutor

if TYPE_CHECKING:
    from qtpy.QtCore import QPoint, QSortFilterProxyModel
    from qtpy.QtWidgets import QMenu

    from utility.ui_libraries.qt.common.expensive_functions import FileProperties


class MenuActionsDispatcherBase:
    def __init__(
        self,
        fs_model: QFileSystemModel,
        proxy_model: QSortFilterProxyModel | None = None,
        file_actions_executor: FileActionsExecutor | None = None,
        selection_model: QItemSelectionModel | None = None,
    ):
        self.fs_model: QFileSystemModel = fs_model
        self.proxy_model: QSortFilterProxyModel | None = proxy_model
        self.file_actions_executor: FileActionsExecutor = FileActionsExecutor() if file_actions_executor is None else file_actions_executor
        self.menus = FileExplorerMenus(self)
        self.selection_model: QItemSelectionModel | None = selection_model
        self.file_actions_executor.TaskCompleted.connect(self.handle_task_result)

    def get_current_directory(self) -> Path:
        return Path(self.fs_model.rootPath()).absolute()

    def get_file_path(self, index: QModelIndex) -> Path:
        source_index = index if index.model() is self.fs_model else self.proxy_model.mapToSource(index)
        return Path(self.fs_model.filePath(source_index)).absolute()

    def confirm_deletion(self, items: list[Path]) -> bool:
        # Implement deletion confirmation dialog
        return True  # Placeholder, implement actual confirmation logic

    def get_selected_paths(self) -> list[Path]:
        return list({self.get_file_path(index) for index in self.selection_model.selectedIndexes()})

    def get_menu(self, index: QModelIndex) -> QMenu:
        shift_mod = Qt.KeyboardModifier.ShiftModifier
        shift_held = bool(QApplication.keyboardModifiers() & shift_mod) or bool(QApplication.queryKeyboardModifiers() & shift_mod)
        if not index.isValid():
            return self.menus.menu_empty_shift if shift_held else self.menus.menu_empty
        source_index = index if index.model() is self.fs_model else self.proxy_model.mapToSource(index)
        if self.fs_model.isDir(source_index):
            return self.menus.menu_dir_shift if shift_held else self.menus.menu_dir
        return self.menus.menu_file_shift if shift_held else self.menus.menu_file

    def get_context_menu(self, view: QAbstractItemView, pos: QPoint) -> QMenu:
        selectionModel = view.selectionModel()
        if selectionModel is None:
            view.setSelectionModel(QItemSelectionModel())
        selected_indexes = view.selectionModel().selectedIndexes()

        if not selected_indexes:
            return self.get_menu(QModelIndex())

        if len(selected_indexes) == 1:
            return self.get_menu(selected_indexes[0])

        # Multiple items selected
        shift_mod = Qt.KeyboardModifier.ShiftModifier
        shift_held = bool(QApplication.keyboardModifiers() & shift_mod) or bool(QApplication.queryKeyboardModifiers() & shift_mod)

        # Convert selection indexes to source indexes
        source_indexes = []
        for idx in selected_indexes:
            if self.proxy_model and idx.model() is self.proxy_model:
                source_indexes.append(self.proxy_model.mapToSource(idx))
            elif idx.model() is self.fs_model:
                source_indexes.append(idx)
            else:
                # Skip invalid indexes
                continue

        all_dirs = all(self.fs_model.isDir(idx) for idx in source_indexes)
        all_files = all(not self.fs_model.isDir(idx) for idx in source_indexes)

        if all_dirs:
            return self.menus.menu_dir_shift if shift_held else self.menus.menu_dir
        if all_files:
            return self.menus.menu_file_shift if shift_held else self.menus.menu_file
        return self.menus.menu_mixed_selection_shift if shift_held else self.menus.menu_mixed_selection

    def queue_task(self, operation: str, *args, **kwargs):
        self.file_actions_executor.queue_task(operation, args=args, kwargs=kwargs)


class MenuActionsDispatcher(MenuActionsDispatcherBase):
    """Dispatches certain actions to the executor after preparing them.

    Actions defined here will need more context and preparation before they can call queue_task.
    The goal is to omit preparation whenever possible, to reduce overall complexity
    for simpler actions. However some will need clipboard context, input dialogs and other constructs.

    See FileExplorerActions for simpler action examples.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_actions_executor.TaskCompleted.connect(self.handle_task_result)
        RobustLogger().debug("Connected TaskCompleted signal to handle_task_result")

    def prepare_sort(self, column_name, order=Qt.SortOrder.AscendingOrder):
        column_map = {}
        for column in range(self.fs_model.columnCount()):
            header = self.fs_model.headerData(column, Qt.Horizontal, Qt.DisplayRole)
            assert isinstance(header, str)
            column_map[header.casefold()] = column

        assert isinstance(column_name, str)
        if column_name.casefold() in column_map:
            column = column_map[column_name.casefold()]
            self.fs_model.sort(column, order)
        else:
            print(f"Warning: Unsupported sort column '{column_name}'")

    def toggle_sort_order(self):
        current_column = self.proxy_model.sortColumn() if self.proxy_model else 0
        current_order = self.proxy_model.sortOrder() if self.proxy_model else Qt.SortOrder.AscendingOrder
        new_order = (
            Qt.SortOrder.DescendingOrder
            if current_order == Qt.SortOrder.AscendingOrder
            else Qt.SortOrder.AscendingOrder
        )
        if self.proxy_model:
            self.proxy_model.sort(current_column, new_order)
        else:
            self.fs_model.sort(current_column, new_order)

    def prepare_rename(self):
        selected_items = self.get_selected_paths()
        if not selected_items:
            return

        item = selected_items[0]
        assert isinstance(item, QModelIndex)
        old_name = self.fs_model.fileName(item)
        new_name, ok = QInputDialog.getText(QApplication.activeWindow(), "Rename", "New name:", text=old_name)

        if ok and new_name:
            old_path = self.get_file_path(item)
            new_path = old_path.parent / new_name
            self.queue_task("rename", old_path, new_path)

    def prepare_new_folder(self):
        current_dir = Path(self.fs_model.rootPath())
        name, ok = QInputDialog.getText(QApplication.activeWindow(), "New Folder", "Folder name:")

        if ok and name:
            new_folder_path = current_dir / name
            self.queue_task("new_folder", new_folder_path)

    def prepare_new_file(self):
        current_dir = Path(self.fs_model.rootPath())
        name, ok = QInputDialog.getText(QApplication.activeWindow(), "New File", "File name:")

        if ok and name:
            new_file_path = current_dir / name
            self.queue_task("new_file", new_file_path)

    def prepare_delete(self):
        paths = self.get_selected_paths()
        if not paths:
            return

        self.queue_task("delete", paths)

    def prepare_properties(self):
        paths = self.get_selected_paths()
        if not paths:
            return

        self.queue_task("show_properties", paths)

    def prepare_create_shortcut(self):
        source_paths = self.get_selected_paths()
        if not source_paths:
            return

        shortcut_path = source_paths[0].parent / f"{source_paths[0].stem} - Shortcut{source_paths[0].suffix}"
        self.queue_task("create_shortcut", source_paths, shortcut_path)

    def prepare_open_with(self):
        paths = self.get_selected_paths()
        if not paths:
            return

        self.queue_task("open_with", paths)

    def prepare_open_terminal(self):
        paths = self.get_selected_paths()
        if not paths:
            return

        path = paths[0]
        if path.is_file():
            path = path.parent
        self.queue_task("open_terminal", path)

    def prepare_compress(self):
        paths = self.get_selected_paths()
        if not paths:
            return

        self.queue_task("compress", paths)

    def prepare_extract(self):
        paths = self.get_selected_paths()
        if not paths:
            return

        archive_path = paths[0]
        extract_path = archive_path.parent
        self.queue_task("extract", archive_path, extract_path)

    def prepare_take_ownership(self):
        paths = self.get_selected_paths()
        if not paths:
            return

        self.queue_task("take_ownership", paths)

    def prepare_send_to(self, destination):
        paths = self.get_selected_paths()
        if not paths:
            return

        self.queue_task("send_to", paths, destination)

    def prepare_open_as_admin(self):
        paths = self.get_selected_paths()
        if not paths:
            return

        self.queue_task("open_as_admin", paths)

    def prepare_print(self):
        paths = self.get_selected_paths()
        if not paths:
            return

        self.queue_task("print_file", paths)

    def prepare_share(self):
        paths = self.get_selected_paths()
        if not paths:
            return

        self.queue_task("share", paths)

    def prepare_group_by(self, grouping: str):
        if self.proxy_model is None:
            return

        if grouping == "None":
            self.proxy_model.setGroupRole(None)
        elif grouping == "Name":
            self.proxy_model.setGroupRole(Qt.ItemDataRole.DisplayRole)
        elif grouping == "Type":
            self.proxy_model.setGroupRole(Qt.ItemDataRole.UserRole)  # Assuming file type is stored in UserRole
        elif grouping == "Size":
            self.proxy_model.setGroupRole(Qt.ItemDataRole.SizeHintRole)
        elif grouping == "Date Modified":
            self.proxy_model.setGroupRole(Qt.ItemDataRole.UserRole + 1)  # Assuming date modified is stored in UserRole + 1

        self.queue_task("refresh_view")

    def prepare_view_mode(self, mode: QListView.ViewMode):
        if isinstance(self.view, QListView) and hasattr(self.view, "setViewMode"):
            self.view.setViewMode(mode)
        self.queue_task("refresh_view")

    def prepare_show_hidden_items(self, show: bool):  # noqa: FBT001
        self.fs_model.setFilter(
            self.fs_model.filter() | QDir.Hidden
            if show
            else self.fs_model.filter() & ~QDir.Hidden
        )
        self.queue_task("refresh_view")

    def prepare_show_file_extensions(self, show: bool):  # noqa: FBT001
        if hasattr(self.fs_model, "setNameFilterDisables"):
            self.fs_model.setNameFilterDisables(not show)
        if hasattr(self.fs_model, "setNameFilters"):
            self.fs_model.setNameFilters([] if show else ["*"])
        self.queue_task("refresh_view")

    def on_open_file(self):
        paths = self.get_selected_paths()
        self.queue_task("open_file", paths)

    def on_open_dir(self):
        paths = self.get_selected_paths()
        self.queue_task("open_dir", paths)

    def on_open(self):
        paths = self.get_selected_paths()
        for path in paths:
            if path.is_dir():
                self.queue_task("open_dir", [path])
            else:
                self.queue_task("open_file", [path])

    def on_open_with_file(self):
        paths = self.get_selected_paths()
        self.queue_task("open_with", paths)

    def on_properties_file(self):
        paths = self.get_selected_paths()
        self.queue_task("get_properties", paths[0])

    def on_properties_dir(self):
        paths = self.get_selected_paths()
        self.queue_task("get_properties", paths[0])

    def on_open_terminal_file(self):
        paths = self.get_selected_paths()
        self.queue_task("open_terminal", paths[0].parent)

    def on_open_terminal_dir(self):
        paths = self.get_selected_paths()
        self.queue_task("open_terminal", paths[0])

    def on_rename_file(self):
        paths = self.get_selected_paths()
        self.queue_task("rename_item", paths[0])

    def on_rename_dir(self):
        paths = self.get_selected_paths()
        self.queue_task("rename_item", paths[0])

    # Multi-selection actions
    def on_copy_files(self):
        paths = self.get_selected_paths()
        self.queue_task("prepare_copy", paths)

    def on_copy_dirs(self):
        paths = self.get_selected_paths()
        self.queue_task("prepare_copy", paths)

    def on_copy_items(self):
        paths = self.get_selected_paths()
        self.queue_task("prepare_copy", paths)

    def on_cut_files(self):
        paths = self.get_selected_paths()
        self.queue_task("prepare_cut", paths)

    def on_cut_dirs(self):
        paths = self.get_selected_paths()
        self.queue_task("prepare_cut", paths)

    def on_cut_items(self):
        paths = self.get_selected_paths()
        self.queue_task("prepare_cut", paths)

    def on_delete_files(self):
        paths = self.get_selected_paths()
        self.queue_task("delete_items", paths)

    def on_delete_dirs(self):
        paths = self.get_selected_paths()
        self.queue_task("delete_items", paths)

    def on_delete_items(self):
        paths = self.get_selected_paths()
        self.queue_task("delete_items", paths)

    def on_cut_file(self):
        self._prepare_clipboard_data(is_cut=True)

    def on_cut_dir(self):
        self._prepare_clipboard_data(is_cut=True, is_dir=True)

    def on_copy_file(self):
        self._prepare_clipboard_data(is_cut=False)

    def on_copy_dir(self):
        self._prepare_clipboard_data(is_cut=False, is_dir=True)

    def _prepare_clipboard_data(self, is_cut: bool, is_dir: bool = False):  # noqa: FBT001, FBT002
        paths = self.get_selected_paths()
        if not paths:
            return

        mime_data = QMimeData()
        urls = [QUrl.fromLocalFile(str(item)) for item in paths]
        mime_data.setUrls(urls)

        if is_cut:
            mime_data.setData("application/x-cut-data", QByteArray(b"1"))
        if is_dir:
            mime_data.setData("application/x-dir-data", QByteArray(b"1"))

        if platform.system() == "Windows":
            file_descriptor_list = [str(item) for item in paths]
            mime_data.setData("FileGroupDescriptor", QByteArray(repr(file_descriptor_list).encode()))
        elif platform.system() == "Darwin":
            import plistlib

            plist_data = {"NSFilenamesPboardType": [str(item) for item in paths]}
            mime_data.setData("com.apple.NSFilePromiseContent", QByteArray(plistlib.dumps(plist_data)))
        else:  # Linux and other Unix-like
            action = "cut" if is_cut else "copy"
            mime_data.setData("x-special/gnome-copied-files", QByteArray(f"{action}\n".encode() + b"\n".join(str(item).encode() for item in paths)))

        QApplication.clipboard().setMimeData(mime_data)
        self.copied_items = paths
        self.is_cut = is_cut

    def on_paste_file(self):
        self._handle_paste(is_dir=False)

    def on_paste_dir(self):
        self._handle_paste(is_dir=True)

    def _handle_paste(self, is_dir: bool):  # noqa: FBT001
        paths = self.get_selected_paths()
        if not paths:
            return

        destination = paths[0]
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()

        if mime_data.hasUrls():
            urls = mime_data.urls()
            sources = [Path(url.toLocalFile()) for url in urls]
            is_cut = mime_data.hasFormat("application/x-cut-data")
            is_source_dir = mime_data.hasFormat("application/x-dir-data")

            if is_dir == is_source_dir:
                self.queue_task("paste", sources, destination, is_cut)

            if is_cut:
                clipboard.clear()  # Clear clipboard after cut-paste operation

    def handle_task_result(self, task_id: str, result: Any):
        RobustLogger().debug(f"Handling task result for task_id: {task_id}, result: {result}")
        if task_id.startswith("get_properties"):
            self.show_properties_dialog(result)

    def show_properties_dialog(self, properties: FileProperties):
        RobustLogger().debug(f"Showing properties dialog for: {properties.name}")
        msg = QMessageBox()
        msg.setWindowTitle("File Properties")
        msg.setText(f"Properties for {properties.name}")
        msg.setInformativeText(f"""
        Type: {properties.type}
        Size: {properties.size}
        Size on disk: {properties.size_on_disk}
        Created: {properties.created}
        Modified: {properties.modified}
        Accessed: {properties.accessed}
        """)
        msg.exec_()

    def queue_task(self, operation: str, *args, **kwargs):
        task_id = self.file_actions_executor.queue_task(operation, args=args, kwargs=kwargs)
        RobustLogger().debug(f"Queued task: {task_id} for operation: {operation}")
        return task_id


if __name__ == "__main__":
    import sys
    import traceback

    from qtpy.QtCore import QDir, Qt
    from qtpy.QtWidgets import QApplication, QFileDialog, QMessageBox, QTreeView

    app = QApplication(sys.argv)

    file_dialog = QFileDialog()
    file_dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)  # noqa: FBT003
    file_dialog.setFileMode(QFileDialog.FileMode.Directory)
    file_dialog.setOption(QFileDialog.Option.ShowDirsOnly, False)  # noqa: FBT003

    tree_view = file_dialog.findChild(QTreeView)
    assert isinstance(tree_view, QTreeView)
    fs_model = tree_view.model()
    assert isinstance(fs_model, QFileSystemModel)
    file_actions_executor = FileActionsExecutor()
    menu_actions_dispatcher = MenuActionsDispatcher(fs_model, None, file_actions_executor)

    def on_task_failed(task_id: str, error: Exception):
        RobustLogger().exception(f"Task {task_id} failed", exc_info=error)
        error_msg = QMessageBox()
        error_msg.setIcon(QMessageBox.Icon.Critical)
        error_msg.setText(f"Task {task_id} failed")
        error_msg.setInformativeText(str(error))
        error_msg.setDetailedText("".join(traceback.format_exception(type(error), error, None)))
        error_msg.setWindowTitle("Task Failed")
        error_msg.exec_()

    file_actions_executor.TaskFailed.connect(on_task_failed)

    views = file_dialog.findChildren(QAbstractItemView)

    for view in views:
        print("Setting context menu policy for view:", view.objectName(), "of type:", type(view).__name__)

        def show_context_menu(pos: QPoint, view: QAbstractItemView = view):
            index = view.indexAt(pos)
            if not index.isValid():
                view.clearSelection()
            menu_actions_dispatcher.selection_model = view.selectionModel()
            menu = menu_actions_dispatcher.get_context_menu(view, pos)
            if menu:
                menu.exec_(view.viewport().mapToGlobal(pos))

        view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        with contextlib.suppress(TypeError):  # TypeError: disconnect() failed between 'customContextMenuRequested' and all its connections
            view.customContextMenuRequested.disconnect()
        view.customContextMenuRequested.connect(show_context_menu)

    file_dialog.resize(800, 600)
    file_dialog.show()

    sys.exit(app.exec_())
