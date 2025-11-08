#!/usr/bin/env python3
from __future__ import annotations

import os
import pathlib
import shutil
import sys

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar, Literal, Sequence

import qtpy

from qtpy.QtCore import QAbstractItemModel, QDir, QModelIndex, QSize, Qt
from qtpy.QtGui import QColor, QDrag

if qtpy.API_NAME in ("PyQt6", "PySide6"):
    from qtpy.QtGui import QUndoCommand  # pyright: ignore[reportPrivateImportUsage]
elif qtpy.API_NAME in ("PyQt5", "PySide2"):
    from qtpy.QtWidgets import QUndoCommand
else:
    raise RuntimeError(f"Unexpected qtpy version: {qtpy.API_NAME}")
from qtpy.QtWidgets import QApplication, QHeaderView, QMainWindow, QMenu, QStyle, QUndoStack, QVBoxLayout, QWidget

from pykotor.extract.capsule import LazyCapsule
from pykotor.tools.misc import is_any_erf_type_file, is_rim_file
from utility.system.os_helper import get_size_on_disk

if __name__ == "__main__":
    def update_sys_path(path: pathlib.Path):
        working_dir = str(path)
        if working_dir not in sys.path:
            sys.path.append(working_dir)


    file_absolute_path = pathlib.Path(__file__).resolve()

    pykotor_path = file_absolute_path.parents[6] / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.exists():
        update_sys_path(pykotor_path.parent)
    pykotor_gl_path = file_absolute_path.parents[6] / "Libraries" / "PyKotorGL" / "src" / "pykotor"
    if pykotor_gl_path.exists():
        update_sys_path(pykotor_gl_path.parent)
    utility_path = file_absolute_path.parents[6] / "Libraries" / "Utility" / "src"
    if utility_path.exists():
        update_sys_path(utility_path)
    toolset_path = file_absolute_path.parents[3] / "toolset"
    if toolset_path.exists():
        update_sys_path(toolset_path.parent)
        if __name__ == "__main__":
            os.chdir(toolset_path)


from pathlib import Path  # noqa: E402

from pykotor.extract.file import FileResource  # noqa: E402
from toolset.gui.dialogs.load_from_location_result import ResourceItems  # noqa: E402
from toolset.utils.window import open_resource_editor  # noqa: E402
from utility.ui_libraries.qt.widgets.itemviews.html_delegate import ICONS_DATA_ROLE, HTMLDelegate  # noqa: E402
from utility.ui_libraries.qt.widgets.itemviews.treeview import RobustTreeView  # noqa: E402

if TYPE_CHECKING:
    from qtpy.QtCore import QPoint


class TreeItem:
    def __init__(
        self,
        path: Path,
        parent: TreeItem | None = None,
    ):
        self.path: Path = path
        self.parent: TreeItem | None = parent
        self.children: Sequence[TreeItem] = self.load_children()

    def load_children(self) -> Sequence[TreeItem]:
        """Should be overridden in subclasses to provide the specific logic for loading children."""
        return []

    def child(self, row: int) -> TreeItem:
        return self.children[row]

    def childCount(self) -> int:
        return len(self.children)

    def columnCount(self) -> Literal[1]:
        return 1

    def data(self) -> str:
        return self.path.name

    def row(self) -> int:
        if self.parent:
            return self.parent.children.index(self)
        return 0

    @abstractmethod
    def icon_data(self) -> dict[str, Any]: ...


class DirItem(TreeItem):
    def load_children(self) -> list[DirItem | CapsuleItem | FileItem]:
        children: list[DirItem | CapsuleItem | FileItem] = []
        for child_path in sorted(self.path.iterdir()):
            if child_path.is_dir():
                children.append(DirItem(child_path, self))
            elif is_any_erf_type_file(child_path) or is_rim_file(child_path):
                children.append(CapsuleItem(self.path, self))
            else:
                children.append(FileItem(child_path, self))
        return children

    def icon_data(self) -> dict[str, Any]:
        return {"icons": [(QStyle.SP_DirIcon, None, "Directory")], "spacing": 5, "columns": 1}


class ResourceItem(TreeItem):
    def __init__(
        self,
        file: Path | FileResource,
        parent: TreeItem | None = None,
    ):
        if isinstance(file, FileResource):
            super().__init__(file.filepath(), parent)
        else:
            super().__init__(file, parent)
            file = FileResource.from_path(file)
        self.resource: FileResource = file

    def icon_data(self) -> dict[str, Any]:
        return {"icons": [(QStyle.SP_FileDialogContentsView, None, "Resource File")], "spacing": 5, "columns": 1}


class FileItem(ResourceItem):
    def load_children(self) -> list[TreeItem]:
        return []

    def icon_data(self) -> dict[str, Any]:
        return {"icons": [(QStyle.SP_FileIcon, None, "File")], "spacing": 5, "columns": 1}


class CapsuleItem(DirItem, FileItem):
    def load_children(self: CapsuleItem | NestedCapsuleItem) -> list[CapsuleChildItem | NestedCapsuleItem]:
        if is_any_erf_type_file(self.resource.filename()) or is_rim_file(self.resource.filename()):
            return [
                NestedCapsuleItem(res, self) if is_any_erf_type_file(self.resource.filename()) or is_rim_file(self.resource.filename()) else CapsuleChildItem(res, self)
                for res in LazyCapsule(self.resource.filepath())
            ]
        return []

    def icon_data(self) -> dict[str, Any]:
        return {"icons": [(QStyle.SP_DirLinkIcon, None, "Capsule")], "spacing": 5, "columns": 1}


class CapsuleChildItem(ResourceItem):
    def load_children(self) -> list[TreeItem]:
        return []

    def icon_data(self) -> dict[str, Any]:
        return {"icons": [(QStyle.SP_FileLinkIcon, None, "Capsule Child")], "spacing": 5, "columns": 1}


class NestedCapsuleItem(CapsuleChildItem, ResourceItem):
    def load_children(self) -> list[CapsuleChildItem | NestedCapsuleItem]:
        return CapsuleItem.load_children(self)  # noqa: SLF001

    def icon_data(self) -> dict[str, Any]:
        return {"icons": [(QStyle.SP_DirLinkOpenIcon, None, "Nested Capsule")], "spacing": 5, "columns": 1}


class FileMoveCommand(QUndoCommand):
    def __init__(self, model: ResourceFileSystemModel, source_indexes: list[QModelIndex], target_item: TreeItem):
        super().__init__()
        self.model: ResourceFileSystemModel = model
        self.source_indexes: list[QModelIndex] = source_indexes
        self.target_item: TreeItem = target_item
        self.moved_files: list[tuple[Path, Path]] = []

    def undo(self):
        for src, dest in self.moved_files:
            if dest.exists():
                dest.rename(src)

    def redo(self):
        for index in self.source_indexes:
            source_item: TreeItem = index.internalPointer()
            source_path: Path = source_item.path
            target_path: Path = self.target_item.path / source_path.name
            if source_path.exists():
                source_path.rename(target_path)
                self.moved_files.append((source_path, target_path))


class FileCopyCommand(QUndoCommand):
    def __init__(self, model: ResourceFileSystemModel, source_indexes: list[QModelIndex]):
        super().__init__()
        self.model: ResourceFileSystemModel = model
        self.source_indexes: list[QModelIndex] = source_indexes
        self.copied_files: list[tuple[Path, Path]] = []

    def undo(self):
        for _, dest in self.copied_files:
            if dest.exists():
                if dest.is_dir():
                    shutil.rmtree(dest)
                else:
                    dest.unlink()

    def redo(self):
        for index in self.source_indexes:
            source_item: TreeItem = index.internalPointer()
            source_path: Path = source_item.path
            target_path: Path = self.model.root_item.path / source_path.name
            if source_path.exists():
                if source_path.is_dir():
                    shutil.copytree(source_path, target_path)
                else:
                    shutil.copy2(source_path, target_path)
                self.copied_files.append((source_path, target_path))


class FileCutCommand(QUndoCommand):
    def __init__(self, model: ResourceFileSystemModel, source_indexes: list[QModelIndex]):
        super().__init__()
        self.model: ResourceFileSystemModel = model
        self.source_indexes: list[QModelIndex] = source_indexes
        self.cut_files: list[tuple[Path, Path]] = []

    def undo(self):
        for dest, src in self.cut_files:
            if dest.exists():
                dest.rename(src)

    def redo(self):
        for index in self.source_indexes:
            source_item: TreeItem = index.internalPointer()
            source_path: Path = source_item.path
            target_path: Path = self.model.root_item.path / source_path.name
            if source_path.exists():
                source_path.rename(target_path)
                self.cut_files.append((source_path, target_path))


class FilePasteCommand(QUndoCommand):
    def __init__(self, model: ResourceFileSystemModel, target_item: TreeItem):
        super().__init__()
        self.model: ResourceFileSystemModel = model
        self.target_item: TreeItem = target_item
        self.pasted_files: list[tuple[Path, Path]] = []

    def undo(self):
        for _, dest in self.pasted_files:
            if dest.exists():
                if dest.is_dir():
                    shutil.rmtree(dest)
                else:
                    dest.unlink()

    def redo(self):
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        if mime_data.hasUrls():
            for url in mime_data.urls():
                source_path = Path(url.toLocalFile())
                target_path = self.target_item.path / source_path.name
                if source_path.exists():
                    if source_path.is_dir():
                        shutil.copytree(source_path, target_path)
                    else:
                        shutil.copy2(source_path, target_path)
                    self.pasted_files.append((source_path, target_path))


class FileSystemTreeView(RobustTreeView):
    def __init__(self, parent: QWidget | None = None):
        self.auto_resize_enabled: bool = True
        super().__init__(parent, use_columns=True)
        self.setSortingEnabled(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setUniformRowHeights(False)
        self.header().setSectionsClickable(True)
        self.header().setSortIndicatorShown(True)
        self.header().setContextMenuPolicy(Qt.CustomContextMenu)
        self.header().setSectionResizeMode(QHeaderView.Interactive)
        self.header().customContextMenuRequested.connect(self.onHeaderContextMenu)
        self.customContextMenuRequested.connect(self.fileSystemModelContextMenu)
        self.undo_stack: QUndoStack = QUndoStack(self)  # Initialize QUndoStack

        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setWordWrap(False)

    def model(self) -> ResourceFileSystemModel:
        result = super().model()
        assert isinstance(result, ResourceFileSystemModel)
        return result

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if self.auto_resize_enabled:
            self.adjustColumnsToFit()

    def adjustColumnsToFit(self):
        # Calculate total available width
        total_width = self.viewport().width()

        # Calculate needed width for each column
        header = self.header()
        num_columns = header.count()

        total_needed_width = 0
        column_widths = []
        for col in range(num_columns):
            column_width = self.sizeHintForColumn(col)
            column_widths.append(column_width)
            total_needed_width += column_width

        # Adjust columns proportionally based on their needed width
        if total_needed_width > 0:
            for col in range(num_columns):
                proportion = column_widths[col] / total_needed_width
                new_width = int(proportion * total_width)
                header.resizeSection(col, new_width)

    def resizeColumnsToFitContent(self):
        header = self.header()
        for col in range(self.model().columnCount()):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)

    def auto_fit_columns(self):
        header = self.header()
        assert header is not None
        for col in range(header.count()):
            self.resizeColumnToContents(col)

    def toggle_auto_fit_columns(self):
        self.auto_resize_enabled = not self.auto_resize_enabled
        if self.auto_resize_enabled:
            self.auto_fit_columns()
            self.adjustColumnsToFit()
        else:
            self.reset_column_widths()

    def reset_column_widths(self):
        header = self.header()
        assert header is not None
        for col in range(header.count()):
            header.resizeSection(col, header.defaultSectionSize())

    def fileSystemModelDoubleClick(self, index: QModelIndex):
        model: ResourceFileSystemModel = self.model()
        filepath_str = model.filePath(index)
        if not filepath_str or not filepath_str.strip():
            return

        file_path = Path(filepath_str)
        if not file_path.exists():
            return

        tree_item = index.internalPointer()
        if isinstance(tree_item, ResourceItem):
            fileres: FileResource = tree_item.resource
            open_resource_editor(
                file_path,
                fileres.resname(),
                fileres.restype(),
                fileres.data(),
                installation=None,
                parentWindow=None,
            )
        elif isinstance(tree_item, DirItem):
            self.expand(index)
        else:
            raise NotImplementedError("Unsupported tree item type")

    def toggleHiddenFiles(self):
        filters = self.model().filter()
        if bool(filters & QDir.Hidden):
            self.model().setFilter(filters & ~QDir.Hidden)
        else:
            self.model().setFilter(filters | QDir.Hidden)

    def setIconSize(self, size: QSize):
        super().setIconSize(size)

    def refresh(self):
        current_index = self.rootIndex()
        self.setRootIndex(current_index)

    def createNewFolder(self):
        current_path = self.model().rootPath
        new_folder_path = Path(current_path, "New Folder")
        new_folder_path.mkdir(parents=True, exist_ok=True)
        self.model().setRootPath(current_path)

    def onEmptySpaceContextMenu(self, point: QPoint):
        menu = QMenu(self)

        large_icons_action = menu.addAction("Large Icons")
        large_icons_action.setCheckable(True)
        large_icons_action.setChecked(self.iconSize().width() > 32)
        large_icons_action.triggered.connect(lambda: self.setIconSize(QSize(64, 64)))

        details_view_action = menu.addAction("Details")
        details_view_action.setCheckable(True)
        details_view_action.setChecked(self.iconSize().width() <= 32)
        details_view_action.triggered.connect(lambda: self.setIconSize(QSize(16, 16)))

        sort_by_menu = menu.addMenu("Sort by")
        sort_by_name_action = sort_by_menu.addAction("Name")
        sort_by_name_action.triggered.connect(lambda: self.sortByColumn(0, Qt.AscendingOrder))
        sort_by_size_action = sort_by_menu.addAction("Size")
        sort_by_size_action.triggered.connect(lambda: self.sortByColumn(1, Qt.AscendingOrder))
        sort_by_type_action = sort_by_menu.addAction("Type")
        sort_by_type_action.triggered.connect(lambda: self.sortByColumn(2, Qt.AscendingOrder))
        sort_by_date_modified_action = sort_by_menu.addAction("Date Modified")
        sort_by_date_modified_action.triggered.connect(lambda: self.sortByColumn(3, Qt.AscendingOrder))

        refresh_action = menu.addAction("Refresh")
        refresh_action.triggered.connect(self.refresh)

        new_menu = menu.addMenu("New")
        new_folder_action = new_menu.addAction("Folder")
        new_folder_action.triggered.connect(self.createNewFolder)

        show_hidden_files_action = menu.addAction("Show Hidden Items")
        show_hidden_files_action.setCheckable(True)
        show_hidden_files_action.setChecked(bool(self.model().filter() & QDir.Hidden))
        show_hidden_files_action.triggered.connect(self.toggleHiddenFiles)

        viewport = self.viewport()
        menu.exec(viewport.mapToGlobal(point))

    def onHeaderContextMenu(self, point: QPoint):
        menu = QMenu(self)

        # Auto Fit Columns option
        auto_fit_columns_action = menu.addAction("Auto Fit Columns")
        auto_fit_columns_action.setCheckable(True)
        auto_fit_columns_action.setChecked(self.auto_resize_enabled)
        auto_fit_columns_action.triggered.connect(self.toggle_auto_fit_columns)

        alternate_row_colors_action = menu.addAction("Show in Groups")
        alternate_row_colors_action.setCheckable(True)
        alternate_row_colors_action.setChecked(self.alternatingRowColors())
        alternate_row_colors_action.triggered.connect(self.setAlternatingRowColors)

        header = self.header()
        sort_ascending_action = menu.addAction("Sort by Ascending")
        sort_ascending_action.triggered.connect(lambda: self.sortByColumn(header.logicalIndexAt(point), Qt.AscendingOrder))

        sort_descending_action = menu.addAction("Sort by Descending")
        sort_descending_action.triggered.connect(lambda: self.sortByColumn(header.logicalIndexAt(point), Qt.DescendingOrder))

        hide_column_action = menu.addAction("Hide Column")
        hide_column_action.triggered.connect(lambda: header.hideSection(header.logicalIndexAt(point)))

        show_hidden_files_action = menu.addAction("Show Hidden Items")
        show_hidden_files_action.setCheckable(True)
        show_hidden_files_action.setChecked(bool(self.model().filter() & QDir.Hidden))
        show_hidden_files_action.triggered.connect(self.toggleHiddenFiles)

        menu.exec(header.mapToGlobal(point))

    def fileSystemModelContextMenu(self, point: QPoint):
        selected_indexes = self.selectedIndexes()

        if not selected_indexes:
            self.onEmptySpaceContextMenu(point)
            return

        resources: list[FileResource] = []

        for index in selected_indexes:
            if index.column() == 0:
                filepath_str = self.model().filePath(index)
                if filepath_str and filepath_str.strip():
                    file_path = Path(filepath_str)
                    if file_path.exists():
                        resources.append(FileResource.from_path(file_path))

        if not resources:
            return

        menu = QMenu(self)
        menu.addAction("Open").triggered.connect(lambda *args: (open_resource_editor(res.filepath(), res.resname(), res.restype(), res.data()) for res in resources))
        if all(resource.restype().contents == "gff" for resource in resources):
            menu.addAction("Open with GFF Editor").triggered.connect(
                lambda *args: (open_resource_editor(res.filepath(), res.resname(), res.restype(), res.data(), gff_specialized=False) for res in resources)
            )
        menu.addSeparator()
        builder = ResourceItems(resources=resources)
        builder.viewport = lambda: self

    def startDrag(self, supportedActions):
        drag = QDrag(self)
        mime_data = self.model().mimeData(self.selectedIndexes())
        drag.setMimeData(mime_data)
        drag.exec(supportedActions)

    def dragEnterEvent(self, event: Qt.DropActions | Qt.DropAction):
        event.acceptProposedAction()

    def dragMoveEvent(self, event: Qt.DropActions | Qt.DropAction):
        event.acceptProposedAction()

    def dropEvent(self, event):
        source_indexes = self.selectedIndexes()
        target_index = self.indexAt(event.pos())
        target_item = target_index.internalPointer()

        if not target_item:
            event.ignore()
            return

        undo_command = FileMoveCommand(self.model(), source_indexes, target_item)
        self.undo_stack.push(undo_command)

        event.acceptProposedAction()

    def copyFiles(self):
        source_indexes = self.selectedIndexes()
        copy_command = FileCopyCommand(self.model(), source_indexes)
        self.undo_stack.push(copy_command)

    def cutFiles(self):
        source_indexes = self.selectedIndexes()
        cut_command = FileCutCommand(self.model(), source_indexes)
        self.undo_stack.push(cut_command)

    def pasteFiles(self, target_index: QModelIndex):
        target_item = target_index.internalPointer()
        paste_command = FilePasteCommand(self.model(), target_item)
        self.undo_stack.push(paste_command)

    def undo(self):
        self.undo_stack.undo()

    def redo(self):
        self.undo_stack.redo()


class ResourceFileSystemModel(QAbstractItemModel):
    COLUMN_TO_STAT_MAP: ClassVar[dict[str, str]] = {
        "Size": "st_size",
        "Mode": "st_mode",
        "Last Accessed": "st_atime",
        "Last Modified": "st_mtime",
        "Created": "st_ctime",
        "Hard Links": "st_nlink",
        "Last Accessed (ns)": "st_atime_ns",
        "Last Modified (ns)": "st_mtime_ns",
        "Created (ns)": "st_ctime_ns",
        "Inode": "st_ino",
        "Device": "st_dev",
        "User ID": "st_uid",
        "Group ID": "st_gid",
        "File Attributes": "st_file_attributes",
        "Reparse Tag": "st_reparse_tag",
        "Blocks Allocated": "st_blocks",
        "Block Size": "st_blksize",
        "Device ID": "st_rdev",
        "Flags": "st_flags",
    }

    STAT_TO_COLUMN_MAP: ClassVar[dict[str, str]] = {v: k for k, v in COLUMN_TO_STAT_MAP.items()}

    def __init__(self, root_path: Path | FileResource):
        super().__init__()
        self.root_item: CapsuleChildItem | DirItem | FileItem | NestedCapsuleItem = self.create_root_item(root_path)
        self._detailed_view: bool = False  # New attribute to track detailed view state
        self._filter: QDir.Filters = QDir.AllEntries | QDir.NoDotAndDotDot | QDir.AllDirs | QDir.Files
        self._headers: list[str] = ["File Name", "File Path", "Offset", "Size"]
        self._detailed_headers: list[str] = [*self._headers, *self.COLUMN_TO_STAT_MAP.keys()]

    def toggle_detailed_view(self):
        self._detailed_view = not self._detailed_view
        self.layoutChanged.emit()

    def create_root_item(self, file: Path | FileResource) -> CapsuleChildItem | DirItem | FileItem | NestedCapsuleItem:
        if isinstance(file, FileResource):
            path = file.filepath()
        else:
            path = file
        self.rootPath: Path = path
        if is_any_erf_type_file(path) or is_rim_file(path):
            fileres = FileResource.from_path(path)
            if fileres.inside_capsule or any(is_any_erf_type_file(p) or is_rim_file(p) for p in path.parents):
                cls = NestedCapsuleItem
            else:
                cls = CapsuleChildItem
        elif path.is_dir():
            cls = DirItem
        elif path.is_file():
            cls = FileItem
        else:
            raise RuntimeError("Could not determine type of path")

        return cls(path)

    def filter(self) -> QDir.Filters:
        return self._filter

    def setFilter(self, filters):
        self._filter = filters

    def filePath(self, index: QModelIndex) -> str:
        if not index.isValid():
            return ""
        resource_item: TreeItem = index.internalPointer()
        return str(resource_item.path)  #

    def canFetchMore(self, index: QModelIndex) -> bool:
        if not index.isValid():
            return False

        item = index.internalPointer()
        return isinstance(item, DirItem) and item.childCount() == 0

    def fetchMore(self, index: QModelIndex) -> None:
        if not index.isValid():
            return

        item = index.internalPointer()
        if isinstance(item, DirItem):
            item.load_children()
            self.layoutChanged.emit()

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        parent = QModelIndex() if parent is None else parent
        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()
        return parent_item.childCount()

    def columnCount(self, parent: QModelIndex | None = None) -> int:
        parent = QModelIndex() if parent is None else parent
        return len(self._detailed_headers) if self._detailed_view else len(self._headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> str | dict[str, Any] | None:
        if not index.isValid():
            return None
        item: TreeItem = index.internalPointer()
        if role == Qt.DisplayRole:
            return self.get_detailed_data(index) if self._detailed_view else self.get_default_data(index)
        if role == ICONS_DATA_ROLE:
            return item.icon_data()
        return None

    def human_readable_size(
        self,
        size: float,
        decimal_places: int = 2,
    ) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
            if size < 1024.0 or unit == "PB":
                break
            size /= 1024.0
        return f"{size:.{decimal_places}f} {unit}"

    def get_detailed_data(self, index: QModelIndex) -> str:
        item: FileItem = index.internalPointer()
        if not item.path.is_file():
            return "N/A"
        filepath = item.path
        stat_result = filepath.stat()
        column_name = self._detailed_headers[index.column()]
        stat_attr = self.COLUMN_TO_STAT_MAP.get(column_name)
        if stat_attr:
            return getattr(stat_result, stat_attr, "N/A")
        if column_name == "Size on Disk":
            size_on_disk = get_size_on_disk(filepath, stat_result)
            return self.human_readable_size(size_on_disk)
        if column_name == "Size Ratio":
            size_on_disk = get_size_on_disk(filepath, stat_result)
            ratio = (size_on_disk / stat_result.st_size) * 100 if stat_result.st_size else 0
            return f"{ratio:.2f}%"
        return "N/A"

    def get_default_data(self, index: QModelIndex) -> str:
        item = index.internalPointer()
        if index.column() == 0:  # File Name
            name = item.data()
            if item.path.is_dir():
                color = QColor(0, 128, 0)  # Green for directories
                display_text = f'<span style="color:{color.name()}; font-size:12pt;">{name}</span>'
            else:
                color = QColor(0, 0, 255)  # Blue for files
                display_text = f'<span style="color:{color.name()}; font-size:12pt;">{name}</span>'
            return display_text
        if index.column() == 1:  # File Path
            return str(item.path)
        if index.column() == 2:  # Offset
            return f"0x{hex(item.resource.offset())[2:].upper()}" if hasattr(item, "resource") else "0x0"
        if index.column() == 3:  # Size
            return self.human_readable_size(item.resource.size()) if hasattr(item, "resource") else ""
        return "N/A"

    def setRootPath(self, path: os.PathLike | str):
        self.root_item = self.create_root_item(Path(path))
        self.rootIndex = self.index(0, 0, QModelIndex())
        if bool(self.filter() & QDir.Hidden):
            filters = QDir.AllEntries | QDir.NoDotAndDotDot | QDir.AllDirs | QDir.Files | QDir.Hidden
        else:
            filters = QDir.AllEntries | QDir.NoDotAndDotDot | QDir.AllDirs | QDir.Files
        self.fileInfoList = QDir(str(self.rootPath)).entryInfoList(filters)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._detailed_headers[section] if self._detailed_view else self._headers[section]
        return None

    def index(self, row: int, column: int, parent: QModelIndex | None = None) -> QModelIndex:
        parent = QModelIndex() if parent is None else parent
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        child_item = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent

        if parent_item == self.root_item:
            return QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder) -> None:
        def sort_key(item: TreeItem):  # noqa: ANN202
            if self._detailed_view:
                header = self._detailed_headers[column]
            else:
                header = self._headers[column]

            if header == "File Name":
                return item.data().lower()
            if header == "File Path":
                return str(item.path).lower()
            if header == "Size":
                return item.resource.size() if hasattr(item, "resource") else 0
            if header in self.COLUMN_TO_STAT_MAP:
                stat_result = item.path.stat()
                return getattr(stat_result, self.COLUMN_TO_STAT_MAP[header], 0)
            return 0

        def sort_items(items):
            items.sort(key=sort_key, reverse=(order == Qt.DescendingOrder))
            for item in items:
                if hasattr(item, "children"):
                    sort_items(item.children)

        # Sort the root item's children
        sort_items(self.root_item.children)

        # Notify the view that the data has changed
        self.layoutChanged.emit()



class MainWindow(QMainWindow):
    def __init__(self, root_path: Path):
        super().__init__()
        self.setWindowTitle("QTreeView with HTMLDelegate")

        self.model = ResourceFileSystemModel(root_path)
        self.tree_view = FileSystemTreeView(self)
        self.tree_view.setModel(self.model)

        # Set the custom delegate
        self.html_delegate = HTMLDelegate(self.tree_view, word_wrap=False)
        self.tree_view.setItemDelegate(self.html_delegate)

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.tree_view)
        self.setCentralWidget(central_widget)


def create_example_directory_structure(base_path: Path):
    if base_path.exists():
        import shutil

        shutil.rmtree(base_path)
    # Create some example directories and files
    (base_path / "Folder1").mkdir(parents=True, exist_ok=True)
    (base_path / "Folder2").mkdir(parents=True, exist_ok=True)
    (base_path / "Folder1" / "Subfolder1").mkdir(parents=True, exist_ok=True)
    (base_path / "Folder1" / "Subfolder1" / "SubSubFolder1").mkdir(parents=True, exist_ok=True)
    (base_path / "Folder1" / "file1.txt").write_text("This is file1 in Folder1")
    (base_path / "Folder1" / "file2.txt").write_text("This is file2 in Folder1")
    (base_path / "Folder2" / "file3.txt").write_text("This is file3 in Folder2")
    (base_path / "Folder2" / "file4.txt").write_text("This is file4 in Folder2")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setDoubleClickInterval(1)

    # Assuming you have already called create_example_directory_structure
    base_path = Path("example_directory").resolve()
    create_example_directory_structure(base_path)

    main_window = MainWindow(base_path)
    main_window.show()

    sys.exit(app.exec())
