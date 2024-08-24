from __future__ import annotations

import os
import pathlib
import sys

from datetime import datetime
from typing import TYPE_CHECKING, Any, ClassVar, Protocol, TypeVar, Union

import qtpy

if qtpy.API_NAME in ("PyQt6", "PySide6"):
    QDesktopWidget = None
    from qtpy.QtGui import QUndoCommand, QUndoStack  # pyright: ignore[reportPrivateImportUsage]  # noqa: F401
elif qtpy.API_NAME in ("PyQt5", "PySide2"):
    from qtpy.QtWidgets import QDesktopWidget, QUndoCommand, QUndoStack  # noqa: F401  # pyright: ignore[reportPrivateImportUsage]
else:
    raise RuntimeError(f"Unexpected qtpy version: '{qtpy.API_NAME}'")
from qtpy.QtWidgets import QAbstractItemView, QApplication, QHeaderView, QMainWindow, QMenu, QStyle, QVBoxLayout, QWidget


def update_sys_path(path: pathlib.Path):
    working_dir = str(path)
    print("<SDM> [update_sys_path scope] working_dir: ", working_dir)

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



from qtpy.QtCore import QAbstractItemModel, QDir, QModelIndex, QObject, Qt  # noqa: E402, F401
from qtpy.QtGui import QColor, QDrag, QIcon, QImage, QPixmap  # noqa: E402
from qtpy.QtWidgets import QHBoxLayout, QLineEdit, QPushButton  # noqa: E402

from pykotor.extract.file import FileResource  # noqa: E402
from pykotor.tools.misc import is_capsule_file  # noqa: E402
from toolset.__main__ import main_init  # noqa: E402
from toolset.gui.common.style.delegates import _ICONS_DATA_ROLE, HTMLDelegate  # noqa: E402
from toolset.gui.common.widgets.tree import RobustTreeView  # noqa: E402
from toolset.gui.dialogs.load_from_location_result import ResourceItems  # noqa: E402
from toolset.utils.window import openResourceEditor  # noqa: E402
from utility.gui.qt.common.filesystem.node import CapsuleItem, DirItem, NestedCapsuleItem, ResourceItem, TreeItem  # noqa: E402
from utility.system.os_helper import get_size_on_disk  # noqa: E402
from utility.system.path import Path  # noqa: E402

if TYPE_CHECKING:
    from qtpy.QtCore import QPoint
    from qtpy.QtGui import QDragEnterEvent, QDragMoveEvent
    from qtpy.QtWidgets import QFileSystemModel

    from toolset.data.installation import HTInstallation
    from toolset.gui.windows.main import ToolWindow
    from utility.gui.qt.common.filesystem.node import FileItem
    from utility.gui.qt.common.filesystem.tree import PyFileSystemModel

class ResourceFileSystemWidget(QWidget):
    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        view: RobustTreeView | None = None,
        model: PyFileSystemModel | QFileSystemModel | ResourceFileSystemModel | None = None,
    ):
        super().__init__(parent)

        # Setup the view and model.
        self.fsTreeView: RobustTreeView = RobustTreeView(self, use_columns=True) if view is None else view
        self.fsModel: QFileSystemModel | ResourceFileSystemModel | PyFileSystemModel = ResourceFileSystemModel(self) if model is None else model
        self.fsTreeView.setModel(self.fsModel)

        # Address bar
        self.address_bar = QLineEdit(self)
        self.address_bar.returnPressed.connect(self.onAddressBarReturnPressed)

        # Go button
        self.go_button = QPushButton("Go", self)
        self.go_button.clicked.connect(self.onGoButtonClicked)

        # Refresh button
        self.refresh_button = QPushButton("Refresh", self)
        self.refresh_button.clicked.connect(self.onRefreshButtonClicked)

        # Layout for the address bar, go button, and refresh button
        self.address_layout = QHBoxLayout()
        self.address_layout.addWidget(self.address_bar)
        self.address_layout.addWidget(self.go_button)
        self.address_layout.addWidget(self.refresh_button)

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addLayout(self.address_layout)
        self.main_layout.addWidget(self.fsTreeView)

        # Configure the QTreeView
        self.setup_tree_view()


    def setup_tree_view(self):
        self.undo_stack: QUndoStack = QUndoStack(self)
        h: QHeaderView | None = self.fsTreeView.header()
        assert h is not None
        h.setSectionsClickable(True)
        h.setSortIndicatorShown(True)
        h.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        h.setSectionsMovable(True)
        self.fsTreeView.setWordWrap(False)
        self.fsTreeView.setSortingEnabled(True)
        self.fsTreeView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.fsTreeView.setUniformRowHeights(True)
        self.fsTreeView.setVerticalScrollMode(self.fsTreeView.ScrollMode.ScrollPerItem)
        self.fsTreeView.setSelectionMode(self.fsTreeView.SelectionMode.ExtendedSelection)
        self.fsTreeView.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.fsTreeView.setDragEnabled(True)
        self.fsTreeView.setAcceptDrops(True)
        self.fsTreeView.setDropIndicatorShown(True)
        self.fsTreeView.expanded.connect(self.onItemExpanded)
        self.fsTreeView.collapsed.connect(self.onItemCollapsed)
        self.fsTreeView.customContextMenuRequested.connect(self.fileSystemModelContextMenu)
        self.fsTreeView.doubleClicked.connect(self.fileSystemModelDoubleClick)
        self.fsTreeView._addSimpleAction(  # noqa: SLF001
            self.fsTreeView.viewMenu,
            "Resize Columns",
            self.resize_all_columns,
        )
        if hasattr(self.fsModel, "toggle_detailed_view"):
            self.fsTreeView._addSimpleAction(  # noqa: SLF001
                self.fsTreeView.viewMenu,
                "Toggle Detailed View",
                self.fsModel.toggle_detailed_view,
            )
        self.fsTreeView._addExclusiveMenuAction(  # noqa: SLF001
            self.fsTreeView.viewMenu,
            "Resize Mode",
            lambda: next((h.sectionResizeMode(i) for i in range(self.fsModel.columnCount())), QHeaderView.ResizeMode.ResizeToContents),
            lambda mode: [h.setSectionResizeMode(i, mode) for i in range(self.fsModel.columnCount())],
            {
                "Custom": QHeaderView.ResizeMode.Custom,
                "Fixed": QHeaderView.ResizeMode.Fixed,
                "Interactive": QHeaderView.ResizeMode.Interactive,
                "ResizeToContents": QHeaderView.ResizeMode.ResizeToContents,
                "Stretch": QHeaderView.ResizeMode.Stretch,
            },
            "columnResizeMode",
        )
        self.fsTreeView._addMultiSelectMenuAction(  # noqa: SLF001
            self.fsTreeView.viewMenu,
            "File System Filters",
            self.fsModel.filter,  # noqa: SLF001
            self.fsModel.setFilter,
            {
                "All Entries": QDir.Filter.AllEntries,
                "Files": QDir.Filter.Files,
                "Directories": QDir.Filter.Dirs,
                "Hidden Files": QDir.Filter.Hidden,
                "No Dot Files": QDir.Filter.NoDotAndDotDot,
            },
            "fileSystemFilter",
            QDir.Filters(),
        )

    def setRootPath(self, path: os.PathLike | str):
        if self.fsModel is None:
            raise RuntimeError(f"Call setModel before calling {self}.setRootPath")
        self.fsModel.setRootPath(str(Path(path)))
        self.updateAddressBar()

    def updateAddressBar(self):
        """Updates the address bar to show the current root path."""
        model = self.fsModel
        if model and model.rootPath() is not None:  # noqa: SLF001
            self.address_bar.setText(str(model.rootPath()))  # noqa: SLF001
        else:
            self.address_bar.setText("")

    def onGoButtonClicked(self):
        """Handle Go button click to change the root path."""
        self.onAddressBarReturnPressed()

    def onAddressBarReturnPressed(self):
        """Handle user input in the address bar to change the root path."""
        new_path = Path(self.address_bar.text())
        if new_path.exists() and new_path.is_dir():
            self.setRootPath(new_path)
        else:
            print(f"Invalid path: {new_path}")
        self.updateAddressBar()

    def onRefreshButtonClicked(self):
        self.fsModel.resetInternalData()

    def resize_all_columns(self):
        """Adjust the view size based on content."""
        h = self.fsTreeView.header()
        assert h is not None
        for i in range(self.fsModel.columnCount()):
            h.setSectionResizeMode(i, h.ResizeMode.ResizeToContents)
        for i in range(self.fsModel.columnCount()):
            h.setSectionResizeMode(i, h.ResizeMode.Interactive)

    def onItemExpanded(self, idx: QModelIndex):
        # sourcery skip: class-extract-method
        print(f"onItemExpanded, row={idx.row()}, col={idx.column()}")
        self.fsTreeView.debounceLayoutChanged(preChangeEmit=True)
        item = idx.internalPointer()
        if isinstance(item, DirItem):
            item.loadChildren(self.fsModel)
        self.refresh_item(item)
        self.fsTreeView.debounceLayoutChanged(preChangeEmit=False)

    def onItemCollapsed(self, idx: QModelIndex):
        print(f"onItemCollapsed, row={idx.row()}, col={idx.column()}")
        self.fsTreeView.debounceLayoutChanged(preChangeEmit=True)
        item = idx.internalPointer()
        assert isinstance(item, TreeItem)
        self.refresh_item(item)
        self.fsTreeView.debounceLayoutChanged(preChangeEmit=False)

    def model(self) -> QFileSystemModel | ResourceFileSystemModel | PyFileSystemModel:
        return self.fsModel

    def fileSystemModelDoubleClick(self, idx: QModelIndex):
        item: ResourceItem | DirItem = idx.internalPointer()
        print(f"<SDM> [fileSystemModelDoubleClick scope] {item.__class__.__name__}: ", repr(item.resource if isinstance(item, ResourceItem) else item.path))

        if isinstance(item, ResourceItem) and item.path.exists() and item.path.is_file():
            mw: ToolWindow = next((w for w in QApplication.topLevelWidgets() if isinstance(w, QMainWindow) and w.__class__.__name__ == "ToolWindow"), None)  # pyright: ignore[reportAssignmentType]
            print("<SDM> [fileSystemModelDoubleClick scope] ToolWindow: ", mw)
            if mw is None:
                return
            openResourceEditor(item.path, item.resource.resname(), item.resource.restype(), item.resource.data(), installation=mw.active, parentWindow=None)
        elif isinstance(item, DirItem):
            if not item.children:
                item.loadChildren(self.fsModel)
            self.fsTreeView.expand(idx)
        else:
            raise TypeError("Unsupported tree item type")

    def setItemIcon(self, idx: QModelIndex, icon: QIcon | QStyle.StandardPixmap | str | QPixmap | QImage):
        if isinstance(icon, QStyle.StandardPixmap):
            q_style = QApplication.style()
            assert q_style is not None
            icon = q_style.standardIcon(icon)
            print("<SDM> [setItemIcon scope] QStyle.StandardPixmap -> icon: ", icon)

        elif isinstance(icon, str):
            icon = QIcon(QPixmap(icon).scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            print("<SDM> [setItemIcon scope] str -> icon: ", icon)

        elif isinstance(icon, QImage):
            icon = QIcon(QPixmap.fromImage(icon))
            print("<SDM> [setItemIcon scope] QImage -> icon: ", icon)

        if not isinstance(icon, QIcon):
            raise TypeError(f"Invalid icon passed to {self.__class__.__name__}.setItemIcon()!")
        if isinstance(self.fsTreeView.itemDelegate(), HTMLDelegate):
            iconData = {
                "icons": [(icon, None, "Item icon")],
                "size": 32,
                "spacing": 5,
                "rows": 1,
                "columns": 1,
            }
            self.fsModel.setData(idx, iconData, _ICONS_DATA_ROLE)
        else:
            self.fsModel.setData(idx, icon, Qt.ItemDataRole.DecorationRole)

    def toggleHiddenFiles(self):
        f = self.fsModel.filter()
        print("<SDM> [toggleHiddenFiles scope] f: ", f)

        self.fsModel.setFilter(f & ~QDir.Filter.Hidden if bool(f & QDir.Filter.Hidden) else f | QDir.Filter.Hidden)  # pyright: ignore[reportArgumentType]

    def refresh_item(self, item: TreeItem, depth: int = 1):
        """Refresh the given TreeItem and its children up to the specified depth."""
        model = self.fsModel
        if not isinstance(item, TreeItem):
            raise TypeError(f"Expected a TreeItem, got {type(item).__name__}")
        index = model.indexFromItem(item)
        if not index.isValid():
            return
        self.refresh_item_recursive(item, depth)

    def refresh_item_recursive(self, item: TreeItem, depth: int):
        """Recursively refresh the given TreeItem and its children up to the specified depth."""
        model = self.fsModel

        index = model.indexFromItem(item)
        if not index.isValid():
            return
        model.dataChanged.emit(index, index)
        if depth > 0 and isinstance(item, DirItem):
            for child in item.children:
                if child is None:
                    continue
                childIndex = model.indexFromItem(child)
                if childIndex.isValid():
                    self.setItemIcon(childIndex, child.iconData())
                self.refresh_item_recursive(child, depth - 1)

    def createRootFolder(self):
        root_path = self.fsModel.rootPath()
        p = Path(root_path, "New Folder")
        p.mkdir(parents=True, exist_ok=True)
        self.fsModel.resetInternalData()

    def onEmptySpaceContextMenu(self, point: QPoint):
        m = QMenu(self)
        print("<SDM> [onEmptySpaceContextMenu scope] m: ", m)

        sm = m.addMenu("Sort by")
        print("<SDM> [onEmptySpaceContextMenu scope] sm: ", sm)

        for i, t in enumerate(["Name", "Size", "Type", "Date Modified"]):
            sm.addAction(t).triggered.connect(lambda i=i: self.fsTreeView.sortByColumn(i, Qt.SortOrder.AscendingOrder))  # pyright: ignore[reportOptionalMemberAccess]
            print("<SDM> [onEmptySpaceContextMenu scope] i: ", i)

        m.addAction("Refresh").triggered.connect(lambda *args, **kwargs: self.fsModel.resetInternalData())  # pyright: ignore[reportOptionalMemberAccess]
        nm = m.addMenu("New")

        nm.addAction("Folder").triggered.connect(self.createRootFolder)  # pyright: ignore[reportOptionalMemberAccess]
        sh = m.addAction("Show Hidden Items")
        print("<SDM> [onEmptySpaceContextMenu scope] sh: ", sh)

        sh.setCheckable(True)  # pyright: ignore[reportOptionalMemberAccess]
        sh.setChecked(bool(self.fsModel.filter() & QDir.Filter.Hidden))  # pyright: ignore[reportOptionalMemberAccess]
        sh.triggered.connect(self.toggleHiddenFiles)  # pyright: ignore[reportOptionalMemberAccess]
        if hasattr(m, "exec"):
            m.exec(self.fsTreeView.viewport().mapToGlobal(point))  # pyright: ignore[reportOptionalMemberAccess]
        elif hasattr(m, "exec_"):
            m.exec_(self.fsTreeView.viewport().mapToGlobal(point))  # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue]

    def onHeaderContextMenu(self, point: QPoint):
        print(f"<SDM> [{self.__class__.__name__}.onHeaderContextMenu scope] point.x", point.x(), "y:", point.y())
        m = QMenu(self)
        td = m.addAction("Advanced")

        td.setCheckable(True)  # pyright: ignore[reportOptionalMemberAccess]
        td.setChecked(self.fsModel._detailed_view)  # noqa: SLF001  # pyright: ignore[reportOptionalMemberAccess]
        td.triggered.connect(self.fsModel.toggle_detailed_view)  # pyright: ignore[reportOptionalMemberAccess]

        sh = m.addAction("Show Hidden Items")
        sh.setCheckable(True)  # pyright: ignore[reportOptionalMemberAccess]
        sh.setChecked(bool(self.fsModel.filter() & QDir.Filter.Hidden))  # pyright: ignore[reportOptionalMemberAccess]
        sh.triggered.connect(self.toggleHiddenFiles)  # pyright: ignore[reportOptionalMemberAccess]
        self.fsTreeView.showHeaderContextMenu(point, m)

    def fileSystemModelContextMenu(self, point: QPoint):
        sel_idx = self.fsTreeView.selectedIndexes()
        print("<SDM> [fileSystemModelContextMenu scope] sel_idx: ", sel_idx)

        if not sel_idx:
            self.onEmptySpaceContextMenu(point)
            return
        resources: set[FileResource] = set()
        for idx in sel_idx:
            item: DirItem | ResourceItem = idx.internalPointer()
            if isinstance(item, ResourceItem):
                resources.add(item.resource)
            else:
                resources.add(FileResource.from_path(item.path))
        print("<SDM> [fileSystemModelContextMenu scope] resources: ", resources)

        if not resources:
            return
        mw: ToolWindow | None = next(  # pyright: ignore[reportAssignmentType]
            (w for w in QApplication.topLevelWidgets() if isinstance(w, QMainWindow) and w.__class__.__name__ == "ToolWindow"),
            None,
        )
        active_installation: HTInstallation | None = None if mw is None else mw.active
        m = QMenu(self)
        print("<SDM> [fileSystemModelContextMenu scope] m: ", m)

        m.addAction("Open").triggered.connect(lambda: [openResourceEditor(r.filepath(), r.resname(), r.restype(), r.data(), installation=active_installation) for r in resources])  # pyright: ignore[reportOptionalMemberAccess]

        if all(r.restype().contents == "gff" for r in resources):
            m.addAction("Open with GFF Editor").triggered.connect(lambda: [openResourceEditor(r.filepath(), r.resname(), r.restype(), r.data(), installation=active_installation, gff_specialized=False) for r in resources])  # pyright: ignore[reportOptionalMemberAccess]

        m.addSeparator()
        ResourceItems(resources=list(resources), viewport=lambda: self.parent()).runContextMenu(point, installation=active_installation, menu=m)
        print("<SDM> [fileSystemModelContextMenu scope] resources: ", resources)
        self.fsModel.resetInternalData()


    def startDrag(self, actions: Qt.DropAction):  # pyright: ignore[reportOptionalMemberAccess]
        print("startDrag")
        d = QDrag(self)
        d.setMimeData(self.fsModel.mimeData(self.fsTreeView.selectedIndexes()))
        if hasattr(d, "exec_"):
            d.exec_(actions)  # pyright: ignore[reportAttributeAccessIssue]
        elif hasattr(d, "exec"):
            d.exec(actions)

    def dragEnterEvent(self, e: QDragEnterEvent):
        print("dragEnterEvent")
        e.acceptProposedAction()

    def dragMoveEvent(self, e: QDragMoveEvent):
        print("dragMoveEvent")
        e.acceptProposedAction()


class SupportsRichComparison(Protocol):
    def __lt__(self, other: Any) -> bool: ...
    def __le__(self, other: Any) -> bool: ...
    def __gt__(self, other: Any) -> bool: ...
    def __ge__(self, other: Any) -> bool: ...

T = TypeVar("T", bound=Union[SupportsRichComparison, str])
class ResourceFileSystemModel(QAbstractItemModel):
    COLUMN_TO_STAT_MAP: ClassVar[dict[str, str]] = {
        "Size on Disk": "size_on_disk",
        "Size Ratio": "size_ratio",
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

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent=parent)
        self._detailed_view: bool = False
        self._root: DirItem | None = None
        self._headers: list[str] = ["Name", "Size", "Path", "Offset", "Last Modified"]
        self._detailed_headers: list[str] = [*self._headers]
        self._detailed_headers.extend(h for h in self.COLUMN_TO_STAT_MAP if h not in self._headers)
        self._filter: QDir.Filter | QDir.Filters | int = (
            QDir.Filter.AllEntries
            | QDir.Filter.NoDotAndDotDot
            | QDir.Filter.AllDirs
            | QDir.Filter.Files
        )

    @property
    def NumColumns(self) -> int:
        """Note: This overrides a class level variable."""
        return len(self._detailed_headers if self._detailed_view else self._headers)

    def getTreeView(self) -> RobustTreeView:
        qparent_obj = QObject.parent(self)
        if not isinstance(qparent_obj, ResourceFileSystemWidget):
            raise RuntimeError("ResourceFileSystem MVC setup incorrectly, the parent of the model must be the container.")  # noqa: TRY004
        return qparent_obj.fsTreeView

    def getContainerWidget(self) -> ResourceFileSystemWidget:
        qParentObj = QObject.parent(self)
        if not isinstance(qParentObj, ResourceFileSystemWidget):
            raise RuntimeError("ResourceFileSystem MVC setup incorrectly, the parent of the model must be the container.")  # noqa: TRY004
        return qParentObj

    def toggle_detailed_view(self):
        #self.layoutAboutToBeChanged.emit()
        self._detailed_view = not self._detailed_view
        print("<SDM> [toggle_detailed_view scope] self._detailed_view: ", self._detailed_view)
        self.getContainerWidget().resize_all_columns()
        #self.layoutChanged.emit()

    def rootPath(self) -> Path | None:
        return None if self._root is None else self._root.path

    def resetInternalData(self, *, _alwaysEndReset: bool = True):
        """Resets the internal data of the model, forcing a reload of the view. i.e.: restat's all files on disk and reloads them into the ui anew."""
        self.beginResetModel()

        # Clear the current root item and reset it
        if self._root:
            self._root.children.clear()
            self._root.loadChildren(self)

        if _alwaysEndReset:
            self.endResetModel()
        print("<SDM> [resetInternalData scope] Model data has been reset.")
        self.getContainerWidget().updateAddressBar()  # TODO(th3w1zard1): emit a signal for this.

    def setRootPath(self, path: os.PathLike | str):
        self.resetInternalData(_alwaysEndReset=False)
        self._root = self.create_fertile_tree_item(Path(path))
        print("<SDM> [setRootPath scope] self._root: ", self._root.path)

        self._root.loadChildren(self)
        self._rootIndex = self.index(0, 0, QModelIndex())
        assert self._rootIndex.isValid()
        self.endResetModel()

    def create_fertile_tree_item(self, file: Path | FileResource) -> DirItem:
        """Creates a tree item that can have children."""
        path = file.filepath() if isinstance(file, FileResource) else file
        cls = (
            NestedCapsuleItem if is_capsule_file(path) and not path.exists() and any(p.exists() and p.is_file() for p in path.parents)
            else CapsuleItem if isinstance(file, FileResource) or is_capsule_file(path)
            else DirItem if path.is_dir() else None.__class__
        )
        if cls is None.__class__:
            raise ValueError(f"invalid path: {file}")
        return cls(path)

    def getGrandpaIndex(self, index: QModelIndex) -> QModelIndex:
        if isinstance(index, QModelIndex):
            if not index.isValid():
                return QModelIndex()
            return index.parent().parent() if index.parent().isValid() else QModelIndex()
        return None

    def itemFromIndex(self, index: QModelIndex) -> TreeItem | None:
        return index.internalPointer() if index.isValid() else None

    def indexFromItem(self, item: TreeItem) -> QModelIndex:
        if not isinstance(item, TreeItem):
            return None
        if self._root == item:
            return self.createIndex(0, 0, self._root)
        parent_node = item.parent
        if parent_node is None:
            return QModelIndex()
        return self.createIndex(item.row(), 0, parent_node)

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        parent = QModelIndex() if parent is None else parent
        if not parent.isValid():  # Root level
            return 0 if self._root is None else self._root.childCount()
        item = parent.internalPointer()
        assert isinstance(item, TreeItem)
        return 0 if item is None else item.childCount()

    def columnCount(self, parent: QModelIndex | None = None) -> int:
        return self.NumColumns

    def index(self, row: int, column: int, parent: QModelIndex | None = None) -> QModelIndex:
        parent = QModelIndex() if parent is None else parent
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        parentItem = parent.internalPointer() if parent.isValid() else self._root
        assert isinstance(parentItem, TreeItem)
        childItem = parentItem.child(row) if parentItem else None
        return QModelIndex() if childItem is None else self.createIndex(row, column, childItem)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:  # noqa: PLR0911
        if not index.isValid():
            return None
        item: TreeItem = index.internalPointer()
        if isinstance(self.getTreeView().itemDelegate(), HTMLDelegate):
            if role == Qt.ItemDataRole.DisplayRole:
                if self._detailed_view:
                    display_data = self.get_detailed_data(index)
                else:
                    display_data = self.get_default_data(index)
                return f'<span style="color:{QColor(0, 0, 0).name()}; font-size:{self.getTreeView().getTextSize()}pt;">{display_data}</span>'
            if role == Qt.ItemDataRole.DecorationRole and index.column() == 0:
                return item.iconData()
        if role == Qt.ItemDataRole.DisplayRole:
            if self._detailed_view:
                return self.get_detailed_data(index)
            return self.get_default_data(index)

        if role == Qt.ItemDataRole.DecorationRole and index.column() == 0:
            return item.iconData()

        if role == _ICONS_DATA_ROLE and index.column() == 0:
            iconData = {
                "icons": [(item.iconData(), None, "Item icon")],
                "size": 32,
                "spacing": 5,
                "rows": 1,
                "columns": 1,
            }
            self.setData(index, iconData, _ICONS_DATA_ROLE)

        return None

    def canFetchMore(self, index: QModelIndex) -> bool:
        print(f"canFetchMore({index.row()}, {index.column()})")
        if not index.isValid():
            return False
        item = index.internalPointer()
        result = isinstance(item, DirItem) and item.childCount() == 0
        print("<SDM> [canFetchMore scope]", result)
        return result

    def fetchMore(self, index: QModelIndex) -> None:
        print(f"fetchMore({index.row()}, {index.column()})")
        if not index.isValid():
            return

        item: TreeItem = index.internalPointer()
        print(
            "<SDM> [fetchMore scope] index.internalPointer(): ", item,
            f"row: {'item is None' if item is None else item.row()}",
        )

        if isinstance(item, DirItem):
            item.loadChildren(self)

    def filter(self) -> QDir.Filter | QDir.Filters | int:
        return self._filter

    def setFilter(self, filters: QDir.Filter):
        self._filter = filters
        print("<SDM> [setFilter scope] self._filter: ", self._filter)

    def filePath(self, index: QModelIndex) -> str:
        return str(index.internalPointer().path) if index.isValid() else ""

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> str | None:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._detailed_headers[section] if self._detailed_view else self._headers[section]
        return None

    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()
        childItem: Any = index.internalPointer()
        if not isinstance(childItem, TreeItem):
            return QModelIndex()
        parentItem = None if childItem is None else childItem.parent
        if parentItem is None or parentItem == self._root:
            return QModelIndex()
        return self.createIndex(parentItem.row(), 0, parentItem)

    def human_readable_size(self, size: float, decimal_places: int = 2) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
            if size < 1024 or unit == "PB":  # noqa: PLR2004
                break
            size /= 1024
        return f"{size:.{decimal_places}f} {unit}"

    def format_time(self, timestamp: float) -> str:
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")  # noqa: DTZ006

    def get_detailed_from_stat(self, index: QModelIndex, item: FileItem) -> str:  # noqa: C901, PLR0911
        column_name = self._detailed_headers[index.column()]

        stat_result: os.stat_result = item.resource.filepath().stat()
        if column_name in ("Size on Disk", "Size Ratio"):
            size_on_disk = get_size_on_disk(item.resource.filepath(), stat_result)
            ratio = (size_on_disk / stat_result.st_size) * 100 if stat_result.st_size else 0
            if column_name == "Size on Disk":
                return self.human_readable_size(size_on_disk)
            if column_name == "Size Ratio":
                return f"{ratio:.2f}%"
        stat_attr = self.COLUMN_TO_STAT_MAP.get(column_name, "")
        value = getattr(stat_result, stat_attr, None)
        if "size" in stat_attr:
            return "N/A" if value is None else self.human_readable_size(value)
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
        return str(value)

    def get_detailed_data(self, index: QModelIndex) -> str:
        item: FileItem | DirItem = index.internalPointer()
        column_name = self._detailed_headers[index.column()]
        stat_attr = self.COLUMN_TO_STAT_MAP.get(column_name)
        if (stat_attr is not None or column_name in ("Size on Disk", "Size Ratio")) and isinstance(item, ResourceItem):
            return self.get_detailed_from_stat(index, item)
        if column_name == "Name":
            return item.path.name if isinstance(item, DirItem) else item.resource.filename()
        if column_name == "Path":
            return str(item.path if isinstance(item, DirItem) else item.resource.filepath())
        if column_name == "Offset":
            return "0x0" if isinstance(item, DirItem) else f"{hex(item.resource.offset())}"
        if column_name == "Size":
            return "" if isinstance(item, DirItem) else self.human_readable_size(item.resource.size())
        return "N/A"

    def get_default_data(self, index: QModelIndex) -> str:
        item: ResourceItem | DirItem = index.internalPointer()
        column_name = self._headers[index.column()]
        if column_name == "Name":
            return item.path.name if isinstance(item, DirItem) else item.resource.filename()
        if column_name == "Path":
            return str(item.path if isinstance(item, DirItem) else item.resource.filepath().relative_to(self.rootPath()))  # pyright: ignore[reportCallIssue, reportArgumentType]
        if column_name == "Offset":
            return "0x0" if isinstance(item, DirItem) else f"{hex(item.resource.offset())}"
        if column_name == "Size":
            return "" if isinstance(item, DirItem) else self.human_readable_size(item.resource.size())
        return "N/A"

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder):  # noqa: C901
        def get_sort_key(item: TreeItem | None, list_index: int) -> tuple:
            """Generate a sort key that prioritizes directories over files and correctly sorts file sizes."""
            if item is None:
                return (1, "", list_index)  # Sort None items last

            is_dir = isinstance(item, DirItem)
            column_name = self._detailed_headers[column] if self._detailed_view else self._headers[column]

            if column_name == "Size":
                assert isinstance(item, (DirItem, ResourceItem))
                size_value = 0 if isinstance(item, DirItem) else item.resource.size()
                key = (0 if is_dir else 1, size_value)  # Directories first, then by size in bytes
            else:
                if column_name == "Name":
                    key_value = item.path.name if isinstance(item, DirItem) else item.resource.filename()
                    key_value = key_value.lower()
                elif column_name == "Path":
                    key_value = str(item.path if isinstance(item, DirItem) else item.resource.filepath().relative_to(self.rootPath()))
                elif column_name == "Offset":
                    key_value = "0x0" if isinstance(item, DirItem) else f"{hex(item.resource.offset())}"
                else:
                    key_value = "N/A"
                key = (0 if is_dir else 1, key_value)  # Directories first, then by the appropriate column value

            return (*key, list_index)

        def sort_items(items: list[TreeItem | None]):
            items_copy = [(item, i) for i, item in enumerate(items)]
            items_copy.sort(key=lambda x: get_sort_key(x[0], x[1]), reverse=(order == Qt.SortOrder.DescendingOrder))
            for item in items_copy:
                if isinstance(item, DirItem):
                    sort_items(item.children)
            items[:] = [item for item, _ in items_copy]

        if self._root is not None:
            self.layoutAboutToBeChanged.emit()
            sort_items(self._root.children)
            self.layoutChanged.emit()


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


class MainWindow(QMainWindow):
    def __init__(self, root_path: Path):
        super().__init__()
        self.setWindowTitle("QTreeView with HTMLDelegate")

        self.rFileSystemWidget: ResourceFileSystemWidget = ResourceFileSystemWidget(self)
        self.rFileSystemWidget.setRootPath(str(root_path))

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.rFileSystemWidget)
        self.setCentralWidget(central_widget)
        self.setMinimumSize(824, 568)
        self.resize_and_center()

    def resize_and_center(self):
        """Resize and center the window on the screen."""
        self.rFileSystemWidget.resize_all_columns()
        screen = QApplication.primaryScreen().geometry()  # pyright: ignore[reportOptionalMemberAccess]
        new_x = (screen.width() - self.width()) // 2
        new_y = (screen.height() - self.height()) // 2
        new_x = max(0, min(new_x, screen.width() - self.width()))
        new_y = max(0, min(new_y, screen.height() - self.height()))
        self.move(new_x, new_y)


if __name__ == "__main__":
    main_init()
    app = QApplication(sys.argv)
    app.setDoubleClickInterval(1)
    base_path = Path(r"C:\Program Files (x86)\Steam\steamapps\common\swkotor").resolve()
    main_window = MainWindow(base_path)

    main_window.show()

    sys.exit(app.exec_() if hasattr(app, "exec_") else app.exec())  # pyright: ignore[reportAttributeAccessIssue]
