from __future__ import annotations

import contextlib
import os
import platform

from enum import IntEnum
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Any, Union, cast

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy.QtCore import QAbstractProxyModel, QByteArray, QDataStream, QIODevice, QMimeData, QSortFilterProxyModel, QUrl, Qt
from qtpy.QtGui import QClipboard, QValidator
from qtpy.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QColumnView,
    QDialog,
    QFileDialog,
    QFileSystemModel,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStyledItemDelegate,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from utility.ui_libraries.qt.common.column_options_dialog import SetDefaultColumnsDialog
from utility.ui_libraries.qt.common.filesystem.file_properties_dialog import FilePropertiesDialog
from utility.ui_libraries.qt.common.filesystem.filename_validator import FileNameValidator
from utility.ui_libraries.qt.common.menu_definitions import FileExplorerMenus, MenuContext
from utility.ui_libraries.qt.common.tasks.actions_executor import FileActionsExecutor

try:
    from win32com.shell import shell, shellcon  # pyright: ignore[reportMissingModuleSource]
    HAS_PYWIN32 = True
except ImportError:
    HAS_PYWIN32 = False

try:
    import comtypes  # pyright: ignore[reportMissingModuleSource, reportMissingTypeStubs]
    import comtypes.client  # pyright: ignore[reportMissingModuleSource, reportMissingTypeStubs]
    HAS_COMTYPES = True
except ImportError:
    HAS_COMTYPES = False

if TYPE_CHECKING:
    from qtpy.QtCore import QModelIndex, QPoint
    from qtpy.QtWidgets import QMenu

    from utility.ui_libraries.qt.common.filesystem.file_properties_dialog import FileProperties


class DropEffect(IntEnum):
    NONE = 0
    CUT = 2
    LINK = 4
    COPY = 5


class ActionsDispatcher:
    """Dispatches certain actions to the executor after preparing them.

    Actions defined here will need more context and preparation before they can call queue_task.
    The goal is to omit preparation whenever possible, to reduce overall complexity
    for simpler actions. However some will need clipboard context, input dialogs and other constructs.

    See FileExplorerActions for simpler action examples.
    """

    def __init__(
        self,
        fs_model: QFileSystemModel,
        dialog: QFileDialog,
        file_actions_executor: FileActionsExecutor | None = None,
    ):
        self.fs_model: QFileSystemModel = fs_model
        self.dialog: QFileDialog = dialog
        self.file_actions_executor: FileActionsExecutor = FileActionsExecutor() if file_actions_executor is None else file_actions_executor
        self.file_actions_executor.TaskCompleted.connect(self._handle_task_result)
        self.file_actions_executor.TaskFailed.connect(self._handle_task_error)
        RobustLogger().debug("Connected TaskCompleted signal to handle_task_result")
        self.menus: FileExplorerMenus = FileExplorerMenus()
        self.task_operations: dict[str, str] = {}
        self.setup_signals()

    def setup_signals(self):
        self.menus.actions.actionOpen.triggered.connect(lambda: self.queue_task("open_item", self.get_selected_paths()))
        self.menus.actions.actionOpenWith.triggered.connect(lambda: self.queue_task("open_with", self.get_selected_paths()))
        self.menus.actions.actionProperties.triggered.connect(lambda: self.queue_task("get_properties", self.get_selected_paths()))
        self.menus.actions.actionOpenTerminal.triggered.connect(lambda: self.queue_task("open_terminal", self.get_selected_paths()))
        self.menus.actions.actionCut.triggered.connect(self.on_cut_items)
        self.menus.actions.actionCopy.triggered.connect(self.on_copy_items)
        self.menus.actions.actionPaste.triggered.connect(self.on_paste_items)
        self.menus.actions.actionDelete.triggered.connect(lambda: self.queue_task("delete_items", self.get_selected_paths()))
        self.menus.actions.actionRename.triggered.connect(lambda: self.queue_task("rename_item", self.get_selected_paths()))
        self.menus.actions.actionSortByName.triggered.connect(lambda: self.prepare_sort("name"))
        self.menus.actions.actionSortByDateModified.triggered.connect(lambda: self.prepare_sort("date_modified"))
        self.menus.actions.actionSortByType.triggered.connect(lambda: self.prepare_sort("type"))
        self.menus.actions.actionSortBySize.triggered.connect(lambda: self.prepare_sort("size"))
        self.menus.actions.actionSortByDateCreated.triggered.connect(lambda: self.prepare_sort("date_created"))
        self.menus.actions.actionSortByAuthor.triggered.connect(lambda: self.prepare_sort("author"))
        self.menus.actions.actionSortByTitle.triggered.connect(lambda: self.prepare_sort("title"))
        self.menus.actions.actionSortByTags.triggered.connect(lambda: self.prepare_sort("tags"))
        self.menus.actions.actionToggleSortOrder.triggered.connect(self.toggle_sort_order)
        self.menus.actions.actionShowFileOperations.triggered.connect(lambda: self.queue_task("show_file_operations"))
        self.menus.actions.actionDuplicateFinder.triggered.connect(self.prepare_duplicate_finder)
        self.menus.actions.actionHashGenerator.triggered.connect(self.prepare_hash_generator)
        self.menus.actions.actionPermissionsEditor.triggered.connect(self.prepare_permissions_editor)
        self.menus.actions.actionFileShredder.triggered.connect(self.prepare_file_shredder)
        self.menus.actions.actionFileComparison.triggered.connect(self.prepare_file_comparison)
        self.menus.actions.actionOpenInTerminal.triggered.connect(self.prepare_open_in_terminal)
        self.menus.actions.actionCustomizeContextMenu.triggered.connect(self.prepare_customize_context_menu)
        # self.menus.actions.actionAddColumns.triggered.connect(self.show_set_default_columns_dialog)
        # self.menus.actions.actionSizeColumnsToFit.triggered.connect(self.size_columns_to_fit)
        # self.menus.actions.actionItemCheckBoxes.triggered.connect(self.toggle_item_checkboxes)

    def prepare_duplicate_finder(self):
        directory = self.get_current_directory()
        self.queue_task("find_duplicates", directory)

    def prepare_hash_generator(self):
        selected_items = self.get_selected_paths()
        if not selected_items:
            return

        algorithms = ["MD5", "SHA1", "SHA256"]
        algorithm, ok = QInputDialog.getItem(self.dialog, "Hash Generator", "Select hash algorithm:", algorithms, 0, editable=False)
        if ok and algorithm:
            self.queue_task("generate_hashes", selected_items, algorithm)

    def prepare_permissions_editor(self):
        selected_items = self.get_selected_paths()
        if not selected_items:
            return

        self.queue_task("edit_permissions", selected_items)

    def prepare_file_shredder(self):
        selected_items = self.get_selected_paths()
        if not selected_items:
            return

        confirm = QMessageBox.warning(
            self.dialog,
            "Confirm Secure Deletion",
            "Are you sure you want to securely delete the selected files? This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.queue_task("shred_files", selected_items)

    def prepare_file_comparison(self):
        selected_items = self.get_selected_paths()
        if len(selected_items) != 2:
            QMessageBox.warning(self.dialog, "Invalid Selection", "Please select exactly two files for comparison.")
            return

        self.queue_task("compare_files", selected_items)

    def prepare_open_in_terminal(self):
        current_dir = self.get_current_directory()
        self.queue_task("open_terminal", current_dir)

    def prepare_customize_context_menu(self):
        # This would typically open a dialog to customize the context menu.
        # For now, we'll just show a message.
        QMessageBox.information(self.dialog, "Customize Context Menu", "Context menu customization feature is not implemented yet.")

    def show_set_default_columns_dialog(self):
        dialog = SetDefaultColumnsDialog(self.dialog)
        if dialog.exec_():
            selected_columns = dialog.get_selected_columns()
            self.queue_task("set_default_columns", selected_columns)

    def size_columns_to_fit(self):
        view = self.get_current_view()
        if isinstance(view, QTableView):
            view.resizeColumnsToContents()
        elif isinstance(view, QTreeView):
            for column in range(view.header().count()):
                view.resizeColumnToContents(column)
        elif isinstance(view, QHeaderView):
            view.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        elif isinstance(view, QColumnView):
            view.setSizeAdjustPolicy(QColumnView.SizeAdjustPolicy.AdjustToContents)

    def toggle_item_checkboxes(self):
        view: QAbstractItemView = self.get_current_view()
        if not isinstance(view.itemDelegate(), QStyledItemDelegate):
            view.setItemDelegate(QStyledItemDelegate())
        current_state = view.itemDelegate().hasCheckBoxes if hasattr(view.itemDelegate(), "hasCheckBoxes") else False
        view.itemDelegate().setCheckBoxes(not current_state)
        view.viewport().update()

    def get_current_directory(self) -> Path:
        return Path(self.fs_model.rootPath()).absolute()

    def confirm_deletion(self, items: list[Path]) -> bool:
        if not items:
            return False

        class CustomDeleteDialog(QDialog):
            def __init__(self, parent: QWidget, items: list[Path]):
                super().__init__(parent)
                self.setWindowTitle("Confirm Deletion")
                self.setMinimumWidth(400)
                layout = QVBoxLayout(self)

                # Header
                header = QLabel("Are you sure you want to delete the following items?")
                header.setStyleSheet("font-weight: bold; font-size: 14px;")
                layout.addWidget(header)

                # Scrollable area for items
                scroll = QScrollArea()
                scroll.setWidgetResizable(True)
                content = QWidget()
                content_layout = QVBoxLayout(content)

                for item in items:
                    item_label = QLabel(f'<a href="{item}">{item.name}</a>')
                    item_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
                    item_label.setOpenExternalLinks(True)
                    content_layout.addWidget(item_label)

                scroll.setWidget(content)
                layout.addWidget(scroll)

                # Buttons
                button_layout = QHBoxLayout()
                delete_button = QPushButton("Delete")
                delete_button.setStyleSheet("background-color: #ff4d4d; color: white;")
                delete_button.clicked.connect(self.accept)
                cancel_button = QPushButton("Cancel")
                cancel_button.clicked.connect(self.reject)
                button_layout.addWidget(delete_button)
                button_layout.addWidget(cancel_button)
                layout.addLayout(button_layout)

        dialog = CustomDeleteDialog(self.dialog, items)
        result = dialog.exec_()
        return result == QDialog.Accepted

    def get_selected_paths(self) -> list[Path]:
        return [Path(file) for file in self.dialog.selectedFiles()]

    def get_menu(self, index: QModelIndex) -> QMenu:
        shift_mod = Qt.KeyboardModifier.ShiftModifier
        shift_held = bool(QApplication.keyboardModifiers() & shift_mod) or bool(QApplication.queryKeyboardModifiers() & shift_mod)
        if not index.isValid():
            return self.menus.create_menu(context=MenuContext.EMPTY, shift=shift_held)
        proxy_model: QAbstractProxyModel | None = cast(Union[None, QAbstractProxyModel], self.dialog.proxyModel())
        source_index: QModelIndex = index if proxy_model is None else proxy_model.mapToSource(index)
        if self.fs_model.isDir(source_index):
            return self.menus.create_menu(context=MenuContext.DIR, shift=shift_held)
        return self.menus.create_menu(context=MenuContext.FILE, shift=shift_held)

    def get_context_menu(self, view: QAbstractItemView, pos: QPoint) -> QMenu:
        selected_indexes = view.selectionModel().selectedIndexes()
        if not selected_indexes:
            return self.menus.create_menu(context=MenuContext.EMPTY)
        if len(selected_indexes) == 1:
            return self.get_menu(selected_indexes[0])

        # Multiple items selected
        shift_mod = Qt.KeyboardModifier.ShiftModifier
        shift_held = bool(QApplication.keyboardModifiers() & shift_mod)  # or bool(QApplication.queryKeyboardModifiers() & shift_mod)

        # Convert selection indexes to source indexes
        source_indexes: list[QModelIndex] = []
        for idx in selected_indexes:
            if not idx.isValid():
                continue
            model = idx.model()
            if isinstance(model, QAbstractProxyModel):
                source_indexes.append(model.mapToSource(idx))
            elif self.fs_model is not model:
                raise ValueError("Selected indexes are not from the same model")
            else:
                source_indexes.append(idx)

        all_dirs = all(self.fs_model.isDir(idx) for idx in source_indexes)
        all_files = all(not self.fs_model.isDir(idx) for idx in source_indexes)

        context = MenuContext.DIR if all_dirs else MenuContext.FILE if all_files else MenuContext.MIXED
        multi = len(source_indexes) > 1
        return self.menus.create_menu(context=context, shift=shift_held, multi=multi)

    def _handle_task_error(self, task_name: str, error: Exception):
        RobustLogger().error(f"Task '{task_name}' failed with error: {error}")

    def prepare_sort(self, column_name):
        column_map: dict[str, int] = {}
        for column in range(self.fs_model.columnCount()):
            header = self.fs_model.headerData(column, Qt.Horizontal, Qt.DisplayRole)
            assert isinstance(header, str)
            column_map[header.casefold()] = column

        assert isinstance(column_name, str)
        if column_name.casefold() in column_map:
            self.toggle_sort_order()
        else:
            RobustLogger().warning(f"Unsupported sort column '{column_name}'")

    def get_current_view(self) -> QAbstractItemView:
        for view in self.dialog.findChildren(QAbstractItemView):
            if view.isVisible() and view.isEnabled():
                return view
        raise RuntimeError("No visible view found")

    def toggle_sort_order(self):
        # stubs are wrong, cast it as correct type.
        proxy_model: QAbstractProxyModel | None = cast(Union[None, QAbstractProxyModel], self.dialog.proxyModel())
        if isinstance(proxy_model, QSortFilterProxyModel):
            current_column = proxy_model.sortColumn()
            current_order = proxy_model.sortOrder()

            new_order = Qt.SortOrder.DescendingOrder if current_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
            proxy_model.sort(current_column, new_order)
        else:
            view: QAbstractItemView = self.get_current_view()
            if isinstance(view, QTreeView):
                if not view.isSortingEnabled():
                    return
                current_column = view.header().sortIndicatorSection()
                current_order = view.header().sortIndicatorOrder()

                new_order = Qt.SortOrder.DescendingOrder if current_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
                view.sortByColumn(current_column, new_order)
                view.header().setSortIndicator(current_column, new_order)
            elif isinstance(view, QTableView):
                if not view.isSortingEnabled():
                    return
                current_column = view.horizontalHeader().sortIndicatorSection()
                current_order = view.horizontalHeader().sortIndicatorOrder()
                new_order = Qt.SortOrder.DescendingOrder if current_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
                view.sortByColumn(current_column, new_order)
                view.horizontalHeader().setSortIndicator(current_column, new_order)
            elif isinstance(view, QHeaderView):
                current_order = view.sortIndicatorOrder()
                current_column = view.sortIndicatorSection()
                next_sort_order = Qt.SortOrder.DescendingOrder if current_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
                view.setSortIndicator(current_column, next_sort_order)

    def prepare_rename(self):
        selected_items = self.get_selected_paths()
        if not selected_items:
            return

        old_path = selected_items[0]
        validator = FileNameValidator(self.dialog)
        while True:
            name, ok = QInputDialog.getText(
                self.dialog,
                "New File",
                "File name:",
                QLineEdit.EchoMode.Normal,
                "",
                flags=Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.MSWindowsFixedSizeDialogHint | Qt.WindowType.WindowCloseButtonHint,
                inputMethodHints=Qt.InputMethodHint.ImhNoAutoUppercase | Qt.InputMethodHint.ImhLatinOnly | Qt.InputMethodHint.ImhNoPredictiveText,
            )
            if not ok:
                return
            if not name or not name.strip():
                QMessageBox.warning(self.dialog, "Invalid File Name", "File name cannot be empty/blank.")
                continue
            if validator.validate(name, 0)[0] != QValidator.State.Acceptable:
                QMessageBox.warning(self.dialog, "Invalid File Name", "File name contains invalid characters.")
                continue
            if len(PurePath(name).stem) > 16:  # resref max length  # noqa: PLR2004
                QMessageBox.warning(self.dialog, "File Name Too Long", "File name is too long.")
                continue
            new_file_path = old_path.parent / name
            if (new_file_path).exists():
                QMessageBox.warning(self.dialog, "File Exists", "File with this name already exists.")
                continue
            break

        if ok and name:
            new_path = old_path.parent / name
            self.queue_task("rename", old_path, new_path)

    def prepare_new_folder(self):
        current_dir = Path(self.fs_model.rootPath())
        name, ok = QInputDialog.getText(self.dialog, "New Folder", "Folder name:")

        if ok and name:
            new_folder_path = current_dir / name
            self.queue_task("new_folder", new_folder_path)

    def prepare_new_file(self):
        current_dir = Path(self.fs_model.rootPath())
        validator = FileNameValidator(self.dialog)
        while True:
            name, ok = QInputDialog.getText(
                self.dialog,
                "New File",
                "File name:",
                QLineEdit.EchoMode.Normal,
                "",
                flags=Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.MSWindowsFixedSizeDialogHint | Qt.WindowType.WindowCloseButtonHint,
                inputMethodHints=Qt.InputMethodHint.ImhNoAutoUppercase | Qt.InputMethodHint.ImhLatinOnly | Qt.InputMethodHint.ImhNoPredictiveText,
            )
            if not ok:
                return
            if not name:
                QMessageBox.warning(self.dialog, "Invalid File Name", "File name cannot be empty.")
                continue
            if validator.validate(name, 0)[0] != QValidator.State.Acceptable:
                QMessageBox.warning(self.dialog, "Invalid File Name", "File name contains invalid characters.")
                continue
            if len(PurePath(name).stem) > 16:  # resref max length  # noqa: PLR2004
                QMessageBox.warning(self.dialog, "File Name Too Long", "File name is too long.")
                continue
            new_file_path = current_dir / name
            if (new_file_path).exists():
                QMessageBox.warning(self.dialog, "File Exists", "File with this name already exists.")
                continue
            break

        self.queue_task("new_file", new_file_path)

    def prepare_delete(self):
        paths = self.get_selected_paths()
        if not paths:
            return
        if self.confirm_deletion(paths):
            self.queue_task("delete", paths)

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
        archive_path = paths[0].parent / f"{paths[0].stem}.zip"
        self.queue_task("compress_items", paths, archive_path)

    def prepare_extract(self):
        paths = self.get_selected_paths()
        if not paths:
            return
        archive_path = paths[0]
        extract_path = archive_path.parent
        self.queue_task("extract_items", archive_path, extract_path)

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

    def prepare_show_hidden_items(self, show: bool):  # noqa: FBT001
        self.fs_model.setFilter(self.fs_model.filter() | QDir.Hidden if show else self.fs_model.filter() & ~QDir.Hidden)
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

    def on_rename_item(self):
        paths = self.get_selected_paths()
        self.queue_task("rename_item", paths[0])

    def on_copy_items(self):
        self._prepare_clipboard_data(is_cut=False)

    def on_cut_items(self):
        self._prepare_clipboard_data(is_cut=True)

    def on_delete_items(self):
        paths = self.get_selected_paths()
        self.queue_task("delete_items", paths)

    def on_paste_items(self):
        print("on_paste_items")
        self._handle_paste()

    def _prepare_clipboard_data(self, *, is_cut: bool):
        paths = self.get_selected_paths()
        if not paths:
            return

        mime_data = QMimeData()
        urls = [QUrl.fromLocalFile(str(item)) for item in paths]
        mime_data.setUrls(urls)

        # Set the Preferred DropEffect
        drop_effect = DropEffect.CUT if is_cut else DropEffect.COPY
        effect_data = QByteArray()
        data_stream = QDataStream(effect_data, QIODevice.OpenMode(QIODevice.OpenModeFlag.WriteOnly))
        data_stream.setByteOrder(QDataStream.ByteOrder.LittleEndian)
        data_stream.writeInt32(drop_effect.value)
        mime_data.setData("Preferred DropEffect", effect_data)

        # Set platform-specific data
        if platform.system() == "Windows":
            file_descriptor_list = [f"<{p.absolute()}>" for p in paths]
            file_contents = "\n".join(file_descriptor_list)
            mime_data.setData("FileGroupDescriptorW", QByteArray(file_contents.encode("utf-16-le")))
        elif platform.system() == "Darwin":
            import plistlib
            plist_data = {"NSFilenamesPboardType": [str(item) for item in paths]}
            mime_data.setData("com.apple.NSFilePromiseContent", QByteArray(plistlib.dumps(plist_data)))
        else:  # Linux and other Unix-like
            action = "cut" if is_cut else "copy"
            mime_data.setData("x-special/gnome-copied-files", QByteArray(f"{action}\n".encode() + b"\n".join(str(item).encode() for item in paths)))

        QApplication.clipboard().setMimeData(mime_data, QClipboard.Mode.Clipboard)
        self.copied_items = paths
        self.is_cut = is_cut

    def _handle_paste(self):
        destination_folder = self.get_current_directory()
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()

        if mime_data.hasUrls():
            urls = mime_data.urls()
            sources = [Path(url.toLocalFile()) for url in urls]
            is_cut = self._get_preferred_drop_effect(mime_data) == DropEffect.CUT

            if self._can_paste_data_object(destination_folder, mime_data):
                if is_cut:
                    self.queue_task("move_item", sources, destination_folder)
                else:
                    self.queue_task("copy_item", sources, destination_folder)
                if is_cut:
                    clipboard.clear()
            else:
                QMessageBox.warning(self.dialog, "Paste Error", "Cannot paste the items to the selected destination.")

    def _can_paste_data_object(self, destination: Path, mime_data: QMimeData) -> bool:
        if not destination.is_dir() or not os.access(str(destination), os.W_OK):
            return False

        if mime_data.hasUrls():
            for url in mime_data.urls():
                source_path = Path(url.toLocalFile())
                if not source_path.exists():
                    return False
                if source_path.is_dir() and destination in source_path.parents:
                    return False

        return True

    def _get_preferred_drop_effect(self, mime_data: QMimeData) -> int:
        effect_data = mime_data.data("Preferred DropEffect")
        if effect_data:
            return int.from_bytes(effect_data, byteorder="little")
        return DropEffect.COPY.value

    def _handle_task_result(self, task_id: str, result: Any):
        """Maps the task_id to the operation's callback function and calls it with the result."""
        RobustLogger().debug(f"Handling task result for task_id: {task_id}, result: {result}")
        operation = self.task_operations.get(task_id)
        if operation == "get_properties":
            self.show_properties_dialog(result)
        elif operation == "batch_rename":
            self.result_batch_rename(result)
        elif operation == "find_duplicates":
            self.result_find_duplicates(result)  # TODO: create a dialog for this
        elif operation == "generate_hashes":
            self.result_generate_hashes(result)  # TODO: create a dialog for this
        elif operation == "shred_files":
            self.fs_model.refreshFiles()
        else:
            print("Operation completed successfully:", operation)
        self.task_operations.pop(task_id)

    def show_properties_dialog(self, properties: list[FileProperties]):
        for prop in properties:
            RobustLogger().debug(f"Showing properties dialog for: {prop.name}")
            dialog = FilePropertiesDialog(prop, self.dialog)
            dialog.show()  # don't block

    def queue_task(self, operation: str, *args, **kwargs) -> str:
        task_id = self.file_actions_executor.queue_task(operation, args=args, kwargs=kwargs)
        self.task_operations[task_id] = operation
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
    menu_actions_dispatcher = ActionsDispatcher(fs_model, file_dialog, file_actions_executor)

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
