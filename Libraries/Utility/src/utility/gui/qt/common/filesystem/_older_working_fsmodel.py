#!/usr/bin/env python3
from __future__ import annotations

import os
import pathlib
import sys
import tempfile

from abc import abstractmethod
from contextlib import suppress
from datetime import datetime
from typing import TYPE_CHECKING, Any, ClassVar, List, Protocol, Sequence, TypeVar, Union, cast

import qtpy

from qtpy.QtCore import QAbstractItemModel, QDir, QFileInfo, QModelIndex, Qt
from qtpy.QtGui import QDrag, QImage, QPainter, QPixmap

from utility.system.os_helper import get_size_on_disk

if qtpy.API_NAME in ("PyQt6", "PySide6"):
    from qtpy.QtGui import QUndoCommand  # pyright: ignore[reportPrivateImportUsage]  # noqa: F401
elif qtpy.API_NAME in ("PyQt5", "PySide2"):
    from qtpy.QtWidgets import QUndoCommand  # noqa: F401
else:
    raise RuntimeError(f"Unexpected qtpy version: {qtpy.API_NAME}")
from pykotor.extract.capsule import LazyCapsule
from pykotor.tools.misc import is_capsule_file, is_rim_file
from qtpy.QtWidgets import QAbstractItemView, QApplication, QFileIconProvider, QHeaderView, QMainWindow, QMenu, QStyle, QUndoStack, QVBoxLayout, QWidget


def update_sys_path(path: pathlib.Path):
    working_dir = str(path)
    if working_dir not in sys.path:
        sys.path.append(working_dir)



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
        os.chdir(toolset_path)


from pykotor.extract.file import FileResource  # noqa: E402
from qtpy.QtGui import QIcon  # noqa: E402
from qtpy.QtWidgets import QTreeView  # noqa: E402
from toolset.gui.dialogs.load_from_location_result import ResourceItems  # noqa: E402
from toolset.utils.window import openResourceEditor  # noqa: E402

if TYPE_CHECKING:
    from qtpy.QtCore import QObject, QPoint
    from qtpy.QtGui import QDragEnterEvent, QDragMoveEvent, QResizeEvent
    from toolset.gui.windows.main import ToolWindow



class TreeItem:
    icon_provider: QFileIconProvider = QFileIconProvider()

    def __init__(
        self,
        path: Path,
        parent: DirItem | None = None,
    ):
        self.path: Path = path
        self.parent: DirItem | None = parent

    @abstractmethod
    def childCount(self) -> int:
        ...

    @abstractmethod
    def icon_data(self) -> QIcon:
        ...

    def row(self) -> int:
        if self.parent is None:
            return -1
        if isinstance(self.parent, DirItem):
            return self.parent.children.index(self)
        raise RuntimeError(f"INVALID parent item! Only `DirItem` instances should children, but parent was: '{self.parent.__class__.__name__}'")

    def data(self) -> str:
        return self.path.name

    @staticmethod
    def icon_from_standard_pixmap(
        std_pixmap: QStyle.StandardPixmap,
        w: int = 16,
        h: int = 16,
    ) -> QIcon:
        icon = QApplication.style().standardIcon(QStyle.SP_DirIcon)  # seems to fail often, yet is the most widely accepted stackoverflow answer?
        if isinstance(icon, QIcon):
            return icon

        # fallback
        pixmap = QPixmap(w, h)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.drawPixmap(0, 0, QApplication.style().standardPixmap(std_pixmap))
        painter.end()

        return QIcon(pixmap)

    def icon_from_extension(self, extension: str) -> QIcon:
        with tempfile.NamedTemporaryFile(suffix=extension, delete=True) as tmp_file:
            return self.icon_provider.icon(QFileInfo(str(Path(tmp_file.name))))


class DirItem(TreeItem):
    def __init__(
        self,
        path: Path,
        parent: DirItem | None = None,
    ):
        super().__init__(path, parent)
        self.children: list[TreeItem] = [None]  # Dummy child
        self._children_loaded: bool = False

    def childCount(self) -> int:
        return len(self.children)

    def load_children(self, model: ResourceFileSystemModel) -> list[TreeItem]:
        children: list[TreeItem] = []
        toplevel_items = list(self.path.iterdir())
        for child_path in sorted(toplevel_items):
            if child_path.is_dir():
                item = DirItem(child_path, self)
            elif is_capsule_file(child_path):
                item = CapsuleItem(child_path, self)
            else:
                item = FileItem(child_path, self)
            children.append(item)
        self.set_children(children)
        return self.children

    def set_children(self, children: Sequence[TreeItem]):
        self.remove_dummy_child()
        self.children = list(children)
        self._children_loaded = True

    def has_dummy_child(self) -> bool:
        return len(self.children) == 1 and self.children[0] is None

    def remove_dummy_child(self):
        if self.has_dummy_child():
            self.children[:] = ()
            self._children_loaded = False

    def child(self, row: int) -> TreeItem:
        return self.children[row]

    def icon_data(self) -> QIcon:
        return self.icon_from_standard_pixmap(QStyle.SP_DirIcon, 16, 16)


class ResourceItem(TreeItem):
    def __init__(
        self,
        file: Path | FileResource,
        parent: DirItem | None = None,
    ):
        self.resource: FileResource
        if isinstance(file, FileResource):
            self.resource = file
            super().__init__(self.resource.filepath(), parent)
        else:
            self.resource = FileResource.from_path(file)
            super().__init__(file, parent)

    def data(self) -> str:
        assert self.resource.filename().lower() == self.path.name.lower()
        assert self.resource.filename() == self.path.name
        return self.resource.filename()

    def icon_data(self) -> QIcon:
        return QIcon(self.icon_from_standard_pixmap(QStyle.SP_FileIcon))


class FileItem(ResourceItem):
    def icon_data(self) -> QIcon:
        return QIcon(self.icon_from_standard_pixmap(QStyle.SP_FileIcon))

    def childCount(self) -> int:
        return 0


class CapsuleItem(DirItem, FileItem):
    def __init__(
        self,
        file: Path | FileResource,
        parent: DirItem | None = None,
    ):
        FileItem.__init__(self, file, parent)  # call BEFORE diritem.__init__!
        DirItem.__init__(self, file.filepath() if isinstance(file, FileResource) else file, parent)  # noqa: SLF001
        self.children: list[CapsuleChildItem | NestedCapsuleItem]

    def childCount(self) -> int:
        return 0

    def load_children(self: CapsuleItem | NestedCapsuleItem, model: ResourceFileSystemModel) -> list[CapsuleChildItem | NestedCapsuleItem]:
        children: list[NestedCapsuleItem | CapsuleChildItem] = [
            NestedCapsuleItem(res, self)
            if is_capsule_file(self.resource.filename()) or is_rim_file(self.resource.filename())
            else CapsuleChildItem(res, self)
            for res in LazyCapsule(self.resource.filepath())
        ]
        self.set_children(children)
        return self.children

    def icon_data(self) -> QIcon:
        return self.icon_from_standard_pixmap(QStyle.SP_FileIcon, 16, 16)


class CapsuleChildItem(ResourceItem):
    def icon_data(self) -> QIcon:
        return self.icon_from_standard_pixmap(QStyle.SP_FileIcon, 16, 16)


class NestedCapsuleItem(CapsuleItem, CapsuleChildItem):
    def icon_data(self) -> QIcon:
        return self.icon_from_standard_pixmap(QStyle.SP_FileIcon, 16, 16)


class FileSystemTreeView(QTreeView):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.autoResizeEnabled = True
        self.undo_stack = QUndoStack(self)
        h = self.header()
        h.setSectionsClickable(True)
        h.setSortIndicatorShown(True)
        h.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        h.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        h.customContextMenuRequested.connect(self.onHeaderContextMenu)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setSortingEnabled(True)
        self.setUniformRowHeights(False)
        self.setVerticalScrollMode(self.ScrollMode.ScrollPerItem)
        self.setSelectionMode(self.SelectionMode.ExtendedSelection)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setWordWrap(False)
        self.expanded.connect(self.onItemExpanded)
        self.customContextMenuRequested.connect(self.fileSystemModelContextMenu)
        self.doubleClicked.connect(self.fileSystemModelDoubleClick)

    def onItemExpanded(self, idx: QModelIndex):
        item = idx.internalPointer()
        if isinstance(item, DirItem) and not item._children_loaded:  # Load the children if not already loaded
            item.load_children(self.model())
            for child in item.children:
                self.setItemIcon(child.index, child.icon_data())
            self.model().layoutChanged.emit()

    def model(self) -> ResourceFileSystemModel:
        result = super().model()
        assert isinstance(result, ResourceFileSystemModel)
        return result

    def resizeEvent(self, e: QResizeEvent):
        super().resizeEvent(e)
        if self.autoResizeEnabled:
            self.adjustColumnsToFit()

    def adjustColumnsToFit(self):
        total_w, h, col_w, needed_w = self.viewport().width(), self.header(), [], 0
        for c in range(h.count()):
            w = int(self.sizeHintForColumn(c) / 2)
            col_w.append(w)
            needed_w += w
        if needed_w > 0:
            for c in range(h.count()):
                h.resizeSection(c, int(col_w[c] / needed_w * total_w))

    def resizeColumnsToFitContent(self):
        h = self.header()
        for c in range(self.model().columnCount()):
            h.setSectionResizeMode(c, QHeaderView.ResizeToContents)

    def autoFitColumns(self):
        h = self.header()
        for c in range(h.count()):
            self.resizeColumnToContents(c)

    def toggleAutoFitColumns(self):
        self.autoResizeEnabled = not self.autoResizeEnabled
        self.autoFitColumns() if self.autoResizeEnabled else self.resetColumnWidths()

    def resetColumnWidths(self):
        h = self.header()
        for c in range(h.count()):
            h.resizeSection(c, h.defaultSectionSize())

    def fileSystemModelDoubleClick(self, idx: QModelIndex):
        item: ResourceItem | DirItem = idx.internalPointer()
        if isinstance(item, ResourceItem) and item.path.exists() and item.path.is_file():
            mw: ToolWindow = next((w for w in QApplication.topLevelWidgets() if isinstance(w, QMainWindow) and w.__class__.__name__ == "ToolWindow"), None)  # pyright: ignore[reportAssignmentType]
            openResourceEditor(item.path, item.resource.resname(), item.resource.restype(), item.resource.data(), installation=mw.active, parentWindow=None)
        elif isinstance(item, DirItem):
            if not item.children:
                item.load_children(self.model())
            self.expand(idx)
        else:
            raise TypeError("Unsupported tree item type")

    def setItemIcon(self, idx: QModelIndex, icon: QIcon | QStyle.StandardPixmap | str | QPixmap | QImage):
        if isinstance(icon, QStyle.StandardPixmap):
            icon = QApplication.style().standardIcon(icon)
        elif isinstance(icon, str):
            icon = QIcon(QPixmap(icon).scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        elif isinstance(icon, QImage):
            icon = QIcon(QPixmap.fromImage(icon))
        if not isinstance(icon, QIcon):
            raise TypeError(f"Invalid icon passed to {self.__class__.__name__}.setItemIcon()!")
        self.model().setData(idx, icon, Qt.ItemDataRole.DecorationRole)

    def toggleHiddenFiles(self):
        f = self.model().filter()
        self.model().setFilter(f & ~QDir.Filter.Hidden if bool(f & QDir.Filter.Hidden) else f | QDir.Filter.Hidden)

    def refresh(self):
        #self.setRootIndex(self.rootIndex())  # FIXME: doesn't actually do anything?
        model = self.model()
        assert model.rootPath is not None, "Must call setRootPath(root_item_path) at least once, before a refresh call can be made."
        model.setRootPath(model.rootPath)

    def createNewFolder(self):
        root_path = self.model().rootPath
        p = Path(root_path, "New Folder")
        p.mkdir(parents=True, exist_ok=True)
        self.model().setRootPath(root_path)

    def onEmptySpaceContextMenu(self, point: QPoint):
        m = QMenu(self)
        sm = m.addMenu("Sort by")
        for i, t in enumerate(["Name", "Size", "Type", "Date Modified"]):
            sm.addAction(t).triggered.connect(lambda i=i: self.sortByColumn(i, Qt.SortOrder.AscendingOrder))
        m.addAction("Refresh").triggered.connect(self.refresh)
        nm = m.addMenu("New")
        nm.addAction("Folder").triggered.connect(self.createNewFolder)
        sh = m.addAction("Show Hidden Items")
        sh.setCheckable(True)
        sh.setChecked(bool(self.model().filter() & QDir.Filter.Hidden))
        sh.triggered.connect(self.toggleHiddenFiles)
        m.exec_(self.viewport().mapToGlobal(point))

    def onHeaderContextMenu(self, point: QPoint):
        m, h = QMenu(self), self.header()
        af = m.addAction("Auto Fit Columns")
        af.setCheckable(True)
        af.setChecked(self.autoResizeEnabled)
        af.triggered.connect(self.toggleAutoFitColumns)
        td = m.addAction("Toggle Detailed View")
        td.setCheckable(True)
        td.setChecked(self.model()._detailed_view)  # noqa: SLF001
        td.triggered.connect(self.model().toggle_detailed_view)
        ac = m.addAction("Show in Groups")
        ac.setCheckable(True)
        ac.setChecked(self.alternatingRowColors())
        ac.triggered.connect(self.setAlternatingRowColors)
        for i, t in enumerate(["Sort by Ascending", "Sort by Descending", "Hide Column"]):
            a = m.addAction(t)
            if i == 2:
                a.triggered.connect(lambda: h.hideSection(h.logicalIndexAt(point)))
            else:
                a.triggered.connect(lambda i=i: self.sortByColumn(h.logicalIndexAt(point), Qt.AscendingOrder if i == 0 else Qt.DescendingOrder))
        sh = m.addAction("Show Hidden Items")
        sh.setCheckable(True)
        sh.setChecked(bool(self.model().filter() & QDir.Hidden))
        sh.triggered.connect(self.toggleHiddenFiles)
        m.exec_(h.mapToGlobal(point))

    def fileSystemModelContextMenu(self, point: QPoint):
        sel_idx = self.selectedIndexes()
        if not sel_idx:
            self.onEmptySpaceContextMenu(point)
            return
        resources = list({FileResource.from_path(idx.internalPointer().path) for idx in sel_idx})
        if not resources:
            return
        mw: ToolWindow = next((w for w in QApplication.topLevelWidgets() if isinstance(w, QMainWindow) and w.__class__.__name__ == "ToolWindow"), None)  # pyright: ignore[reportAssignmentType]
        m = QMenu(self)
        m.addAction("Open").triggered.connect(lambda: [openResourceEditor(r.filepath(), r.resname(), r.restype(), r.data(), installation=mw.active) for r in resources])
        if all(r.restype().contents == "gff" for r in resources):
            m.addAction("Open with GFF Editor").triggered.connect(lambda: [openResourceEditor(r.filepath(), r.resname(), r.restype(), r.data(), installation=mw.active, gff_specialized=False) for r in resources])
        m.addSeparator()
        ResourceItems(resources=resources, viewport=lambda: self.parent()).runContextMenu(point, installation=mw.active, menu=m)

    def startDrag(self, actions: Qt.DropActions | Qt.DropAction):
        d = QDrag(self)
        d.setMimeData(self.model().mimeData(self.selectedIndexes()))
        d.exec_(actions)

    def dragEnterEvent(self, e: QDragEnterEvent):
        e.acceptProposedAction()

    def dragMoveEvent(self, e: QDragMoveEvent):
        e.acceptProposedAction()

class SupportsRichComparison(Protocol):
    def __lt__(self, other: Any) -> bool: ...
    def __le__(self, other: Any) -> bool: ...
    def __gt__(self, other: Any) -> bool: ...
    def __ge__(self, other: Any) -> bool: ...

T = TypeVar("T", bound=Union[SupportsRichComparison, str])
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

    def __init__(self, treeView: FileSystemTreeView, parent: QObject | None = None):
        super().__init__(parent)
        self._detailed_view: bool = False
        self._root_item: DirItem | CapsuleItem | NestedCapsuleItem | None = None
        self._headers: list[str] = ["File Name", "File Path", "Offset", "Size"]
        self._detailed_headers = self._headers + list(self.COLUMN_TO_STAT_MAP.keys())
        self._filter = QDir.AllEntries | QDir.NoDotAndDotDot | QDir.AllDirs | QDir.Files
        self.treeView = treeView
        treeView.setModel(self)

    def toggle_detailed_view(self):
        self._detailed_view = not self._detailed_view
        self.layoutAboutToBeChanged.emit()
        self.layoutChanged.emit()

    def setRootPath(self, path: os.PathLike | str):
        self.beginResetModel()
        self.rootPath = Path(path)
        self._root_item = self.create_fertile_tree_item(self.rootPath)
        self._root_item.load_children(self)
        print("root item row:", self._root_item.row())
        print("root item rowCount:", self._root_item.rowCount() if hasattr(self._root_item, "rowCount") else "No attribute named 'rowCount'")
        print("root item childCount:", self._root_item.childCount() if hasattr(self._root_item, "childCount") else "No attribute named 'childCount'")
        self._root_index = self.index(0, 0, QModelIndex())
        print("root index columnCount:", self.columnCount(self._root_index))
        print("root index rowCount:", self.rowCount(self._root_index) if hasattr(self._root_index, "rowCount") else "No attribute named 'rowCount'")
        assert self._root_index.isValid()
        filters = QDir.AllEntries | QDir.NoDotAndDotDot | QDir.AllDirs | QDir.Files | (
            QDir.Hidden if bool(self.filter() & QDir.Hidden) else 0
        )
        self.fileInfoList = QDir(str(self.rootPath)).entryInfoList(filters)
        self.endResetModel()

    def create_fertile_tree_item(self, file: Path | FileResource) -> CapsuleChildItem | DirItem | FileItem | NestedCapsuleItem:
        """Creates a tree item that can have children."""
        path = file.filepath() if isinstance(file, FileResource) else file
        self.rootPath = path
        cls = (
            NestedCapsuleItem if is_capsule_file(path) and not path.exists() and any(p.exists() and p.is_file() for p in path.parents)
            else CapsuleItem if isinstance(file, FileResource) or is_capsule_file(path)
            else DirItem if path.is_dir() else None
        )
        print(f"root_item: {cls.__name__}(file={file}, path={path})")
        if cls is None:
            raise ValueError(f"invalid path: {file}")
        inst = cls(path)
        return inst

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        parent = QModelIndex() if parent is None else parent
        if not parent.isValid():  # Root level
            return self._root_item.childCount() if self._root_item else 0
        item = parent.internalPointer()
        assert isinstance(item, TreeItem)
        return item.childCount() if item else 0

    def columnCount(self, parent: QModelIndex | None = None) -> int:
        parent = QModelIndex() if parent is None else parent
        return len(self._detailed_headers if self._detailed_view else self._headers)

    def index(self, row: int, column: int, parent: QModelIndex | None = None) -> QModelIndex:
        parent = QModelIndex() if parent is None else parent
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parent_item = self._root_item
        else:
            parent_item = parent.internalPointer()

        assert isinstance(parent_item, TreeItem)
        child_item = parent_item.child(row) if parent_item else None
        if child_item:
            return self.createIndex(row, column, child_item)
        return QModelIndex()

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> str | None:
        if not index.isValid():
            return None
        item = index.internalPointer()
        if role == Qt.DisplayRole:
            return self.get_detailed_data(index) if self._detailed_view else self.get_default_data(index)
        if role == Qt.DecorationRole and index.column() == 0:
            return item.icon_data()
        return None

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        if not index.isValid():
            return False
        if role == Qt.ItemDataRole.EditRole:
            self.dataChanged.emit(index, index, [role])
            return True
        return False

    def canFetchMore(self, index: QModelIndex) -> bool:
        if not index.isValid():
            return False

        item = index.internalPointer()
        return isinstance(item, DirItem) and (item.childCount() == 0 or item.has_dummy_child())

    def fetchMore(self, index: QModelIndex) -> None:
        if not index.isValid():
            return

        item = index.internalPointer()
        if isinstance(item, DirItem):
            item.load_children(self)
            self.layoutChanged.emit()

    def filter(self) -> QDir.Filters:
        return self._filter

    def setFilter(self, filters: QDir.Filters):
        self._filter = filters

    def refresh(self):
        if self._root_item is not None:
            for child in self._root_item.children:
                if isinstance(child, FileItem):
                    child.stat_result = ResourceStatResult.from_stat_result(child.resource.filepath().stat())
            self.layoutChanged.emit()

    def filePath(self, index: QModelIndex) -> str:
        return str(index.internalPointer().path) if index.isValid() else ""

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._detailed_headers[section] if self._detailed_view else self._headers[section]
        return None

    def indexFromItem(self, item: TreeItem) -> QModelIndex:
        """Returns the QModelIndex associated with a given TreeItem."""
        if item.parent is None:
            return self.index(0, 0, QModelIndex())
        parent_index = self.indexFromItem(item.parent)
        return self.index(item.row(), 0, parent_index)

    def itemFromIndex(self, index: QModelIndex) -> TreeItem | None:
        """Returns the TreeItem associated with a given QModelIndex."""
        if not index.isValid():
            return None
        return index.internalPointer()

    def parent(self, index: QModelIndex):
        if not index.isValid():
            return QModelIndex()
        child_item = index.internalPointer()
        parent_item = child_item.parent if child_item else None
        if parent_item == self._root_item or not parent_item:
            return QModelIndex()
        return self.createIndex(parent_item.row(), 0, parent_item)

    def human_readable_size(self, size: float, decimal_places: int = 2) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
            if size < 1024 or unit == "PB":
                break
            size /= 1024
        return f"{size:.{decimal_places}f} {unit}"

    def format_time(self, timestamp: float) -> str:
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")  # noqa: DTZ006

    def get_detailed_from_stat(self, index: QModelIndex, item: FileItem) -> str:
        column_name = self._detailed_headers[index.column()]

        stat_result: os.stat_result = item.resource.filepath().stat()
        stat_attr = self.COLUMN_TO_STAT_MAP.get(column_name, "")
        value = getattr(stat_result, stat_attr, None)
        if "size" in stat_attr:
            if value is None:
                return "N/A"
            return self.human_readable_size(value)
        if "time" in stat_attr:
            if value is None:
                return "N/A"
            if stat_attr.endswith("time_ns"):
                value = value / 1e9
            return self.format_time(value)
        if column_name == "st_mode":
            if value is None:
                return "N/A"
            value = oct(value)[-3:]
        if column_name in ("Size on Disk", "Size Ratio"):
            size_on_disk = get_size_on_disk(item.resource.filepath(), stat_result)
            ratio = (size_on_disk / stat_result.st_size) * 100 if stat_result.st_size else 0
            if column_name == "Size on Disk":
                return self.human_readable_size(size_on_disk)
            if column_name == "Size Ratio":
                return f"{ratio:.2f}%"
        return str(value)

    def get_detailed_data(self, index: QModelIndex) -> str:
        item: FileItem | DirItem = index.internalPointer()
        column_name = self._detailed_headers[index.column()]
        stat_attr = self.COLUMN_TO_STAT_MAP.get(column_name)
        if (stat_attr is not None or column_name in ("Size on Disk", "Size Ratio")) and isinstance(item, ResourceItem):
            return self.get_detailed_from_stat(index, item)
        if column_name == "File Name":
            return item.path.name if isinstance(item, DirItem) else item.resource.filename()
        if column_name == "File Path":
            return str(item.path if isinstance(item, DirItem) else item.resource.filepath())
        if column_name == "Offset":
            return "0x0" if isinstance(item, DirItem) else f"{hex(item.resource.offset())}"
        if column_name == "Size":
            return "" if isinstance(item, DirItem) else self.human_readable_size(item.resource.size())
        return "N/A"

    def get_default_data(self, index: QModelIndex) -> str:
        item: ResourceItem | DirItem = index.internalPointer()
        column_name = self._headers[index.column()]
        if column_name == "File Name":
            return item.path.name if isinstance(item, DirItem) else item.resource.filename()
        if column_name == "File Path":
            return str(item.path if isinstance(item, DirItem) else item.resource.filepath().relative_to(self.rootPath))
        if column_name == "Offset":
            return "0x0" if isinstance(item, DirItem) else f"{hex(item.resource.offset())}"
        if column_name == "Size":
            return "" if isinstance(item, DirItem) else self.human_readable_size(item.resource.size())
        return "N/A"

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder):
        def get_sort_key(value: T) -> float | T:
            """Process the value to determine the appropriate sort key."""
            if isinstance(value, str):
                stripped_value = value.strip()
                if stripped_value.isdigit():
                    return int(stripped_value)
                if stripped_value.startswith("0x"):
                    with suppress(ValueError):
                        return int(stripped_value, 16)
                try:
                    return float(stripped_value)
                except ValueError:
                    return value.lower()
            return value

        def sort_key(item: TreeItem) -> float | str:
            index = self.indexFromItem(item)  # Get the index of the item
            value = self.data(index.sibling(index.row(), column), Qt.ItemDataRole.DisplayRole)  # Get the value for the column
            assert value is not None
            return get_sort_key(value)

        def sort_items(items: Sequence[TreeItem]):
            cast(List[TreeItem], items).sort(key=sort_key, reverse=(order == Qt.SortOrder.DescendingOrder))
            for item in items:
                if isinstance(item, DirItem):
                    sort_items(item.children)

        if self._root_item is not None:
            self.layoutAboutToBeChanged.emit()
            sort_items(self._root_item.children)
            self.layoutChanged.emit()




class MainWindow(QMainWindow):
    def __init__(self, root_path: Path):
        super().__init__()
        self.setWindowTitle("QTreeView with HTMLDelegate")

        self.treeView: FileSystemTreeView = FileSystemTreeView(self)
        self.model: ResourceFileSystemModel = ResourceFileSystemModel(self.treeView)
        self.model.setRootPath(root_path)

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.treeView)
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

    sys.exit(app.exec_())
