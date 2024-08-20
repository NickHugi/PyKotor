from __future__ import annotations

import os
import pathlib
import sys

from abc import abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Any, ClassVar, Protocol, Sequence, TypeVar, Union, cast

import qtpy

from qtpy.QtCore import QDir, QFileInfo, QModelIndex, QTemporaryFile, Qt
from qtpy.QtGui import QColor, QDrag, QImage, QPainter, QPixmap
from qtpy.QtWidgets import QHBoxLayout, QLineEdit, QPushButton

if qtpy.API_NAME in ("PyQt6", "PySide6"):
    QDesktopWidget = None
    from qtpy.QtGui import QUndoCommand, QUndoStack  # pyright: ignore[reportPrivateImportUsage]  # noqa: F401
elif qtpy.API_NAME in ("PyQt5", "PySide2"):
    from qtpy.QtWidgets import QDesktopWidget, QUndoCommand, QUndoStack  # noqa: F401  # pyright: ignore[reportPrivateImportUsage]
else:
    raise RuntimeError(f"Unexpected qtpy version: '{qtpy.API_NAME}'")
from qtpy.QtWidgets import QAbstractItemView, QApplication, QFileIconProvider, QHeaderView, QMainWindow, QMenu, QStyle, QVBoxLayout, QWidget


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


from qtpy.QtCore import QObject  # noqa: E402
from qtpy.QtGui import QIcon  # noqa: E402

from pykotor.extract.capsule import LazyCapsule  # noqa: E402
from pykotor.extract.file import FileResource  # noqa: E402
from pykotor.tools.misc import is_capsule_file  # noqa: E402
from toolset.__main__ import main_init  # noqa: E402
from toolset.gui.common.style.delegates import _ICONS_DATA_ROLE, HTMLDelegate  # noqa: E402
from toolset.gui.common.widgets.tree import RobustTreeView  # noqa: E402
from toolset.gui.dialogs.load_from_location_result import ResourceItems  # noqa: E402
from toolset.gui.widgets.purepy_standard_item_model import PyQStandardItem, PyQStandardItemModel  # noqa: E402
from toolset.utils.window import openResourceEditor  # noqa: E402
from utility.logger_util import RobustRootLogger  # noqa: E402
from utility.system.os_helper import get_size_on_disk  # noqa: E402
from utility.system.path import Path  # noqa: E402

if TYPE_CHECKING:
    from qtpy.QtCore import QPoint
    from qtpy.QtGui import QDragEnterEvent, QDragMoveEvent
    from qtpy.QtWidgets import QScrollBar

    from toolset.data.installation import HTInstallation
    from toolset.gui.windows.main import ToolWindow

class ResourceFileSystemWidget(QWidget):
    def __init__(self, parent: QWidget | None = None, *, view: RobustTreeView | None = None):
        super().__init__(parent)

        # Setup the view and model.
        self.fsTreeView: RobustTreeView = RobustTreeView(self, use_columns=True) if view is None else view
        self.fsModel: ResourceFileSystemModel = ResourceFileSystemModel(self)
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
        h.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.fsTreeView.setWordWrap(False)
        self.fsTreeView.setSortingEnabled(True)
        self.fsTreeView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.fsTreeView.setUniformRowHeights(False)
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

    def setRootPath(self, path: Path):
        if self.fsModel is None:
            raise RuntimeError(f"Call setModel before calling {self}.setRootPath")
        self.fsModel.setRootPath(path)
        self.updateAddressBar()

    def updateAddressBar(self):
        """Updates the address bar to show the current root path."""
        model = self.fsModel
        if model and model._root_item is not None:  # noqa: SLF001
            self.address_bar.setText(str(model._root_item.path))  # noqa: SLF001
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

    def adjust_view_size(self):
        """Adjust the view size based on content."""
        sb: QScrollBar | None = self.fsTreeView.verticalScrollBar()
        assert sb is not None
        width = sb.width() + 4  # Add some padding
        for i in range(self.fsModel.columnCount()):
            width += self.fsTreeView.columnWidth(i)
        print("all column's widths:", width)
        if QDesktopWidget is None:
            app = cast(QApplication, QApplication.instance())
            screen = app.primaryScreen()
            assert screen is not None
            screen_width = screen.geometry().width()
        else:
            screen_width = QDesktopWidget().availableGeometry().width()
        print("Screen width:", screen_width)
        self.resize(min(width, screen_width), self.height())

    def onItemExpanded(self, idx: QModelIndex):
        # sourcery skip: class-extract-method
        print(f"onItemExpanded, row={idx.row()}, col={idx.column()}")
        self.fsTreeView.debounceLayoutChanged(preChangeEmit=True)
        item = idx.internalPointer()
        if isinstance(item, DirItem) and not item._children_loaded:  # noqa: SLF001
            item.load_children(self.fsModel)
        self.refresh_item(item)
        self.fsTreeView.debounceLayoutChanged(preChangeEmit=False)

    def onItemCollapsed(self, idx: QModelIndex):
        print(f"onItemCollapsed, row={idx.row()}, col={idx.column()}")
        self.fsTreeView.debounceLayoutChanged(preChangeEmit=True)
        item = idx.internalPointer()
        if isinstance(item, DirItem):
            item.set_refresh_next_expand()
        self.refresh_item(item)
        self.fsTreeView.debounceLayoutChanged(preChangeEmit=False)

    def model(self) -> ResourceFileSystemModel:
        return self.fsModel

    def fileSystemModelDoubleClick(self, idx: QModelIndex):
        item: ResourceItem | DirItem = idx.internalPointer()
        print(f"<SDM> [fileSystemModelDoubleClick scope] {item.__class__.__name__}: ", repr(item.resource if isinstance(item, ResourceItem) else item.path))

        if isinstance(item, ResourceItem) and item.path.exists() and item.path.is_file():
            mw: ToolWindow = next((w for w in QApplication.topLevelWidgets() if isinstance(w, QMainWindow) and w.__class__.__name__ == "ToolWindow"), None)  # pyright: ignore[reportAssignmentType]
            print("<SDM> [fileSystemModelDoubleClick scope] ToolWindow: ", mw)

            openResourceEditor(item.path, item.resource.resname(), item.resource.restype(), item.resource.data(), installation=mw.active, parentWindow=None)
        elif isinstance(item, DirItem):
            if not item.children:
                item.load_children(self.fsModel)
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
            icon_data = {
                "icons": [(icon, None, "Item icon")],
                "size": 32,
                "spacing": 5,
                "rows": 1,
                "columns": 1,
            }
            self.fsModel.setData(idx, icon_data, _ICONS_DATA_ROLE)
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
        if depth > 0 and isinstance(item, DirItem) and item._children_loaded:  # noqa: SLF001
            for child in item.children:
                child_index = model.indexFromItem(child)
                if child_index.isValid():
                    self.setItemIcon(child_index, child.icon_data())
                self.refresh_item_recursive(child, depth - 1)

    def createNewFolder(self):
        root_path = self.fsModel.rootPath
        print("<SDM> [createNewFolder scope] root_path: ", root_path)

        p = Path(root_path, "New Folder")
        print("<SDM> [createNewFolder scope] p: ", p)

        p.mkdir(parents=True, exist_ok=True)
        root_item = self.fsModel._root_item  # noqa: SLF001
        assert root_item is not None
        self.refresh_item(root_item)

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
        print("<SDM> [onEmptySpaceContextMenu scope] nm: ", nm)

        nm.addAction("Folder").triggered.connect(self.createNewFolder)  # pyright: ignore[reportOptionalMemberAccess]
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
        h = self.fsTreeView.header()
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


class TreeItem(PyQStandardItem):
    icon_provider: QFileIconProvider = QFileIconProvider()

    def __init__(
        self,
        path: Path,
        parent: DirItem | None = None,
    ):
        super().__init__()
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
            if self not in self.parent.children:
                RobustRootLogger().warning(f"parent {self.parent.path} has orphaned the item {self.path} without warning!")
                return -1
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
        style = QApplication.style()
        assert style is not None
        icon = style.standardIcon(std_pixmap)  # seems to fail often, yet is the most widely accepted stackoverflow answer?
        if isinstance(icon, QIcon):
            return icon

        # fallback
        pixmap = QPixmap(w, h)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.drawPixmap(0, 0, style.standardPixmap(std_pixmap))
        painter.end()

        return QIcon(pixmap)

    def icon_from_extension(self, extension: str) -> QIcon:
        temp_file = QTemporaryFile(f"XXXXXX.{extension}")
        temp_file.setAutoRemove(False)
        temp_file.open()

        try:
            icon = self.icon_provider.icon(QFileInfo(temp_file.fileName()))
            if icon.pixmap(32, 32).isNull():
                print(f"<SDM> Failed to retrieve a valid icon for extension '{extension}'")
                return self.icon_from_standard_pixmap(QStyle.StandardPixmap.SP_DirIcon if isinstance(self, DirItem) else QStyle.StandardPixmap.SP_FileIcon)
            return icon

        finally:
            temp_file.close()
            temp_file.remove()


class DirItem(TreeItem):
    def __init__(
        self,
        path: Path,
        parent: DirItem | None = None,
    ):
        super().__init__(path, parent)
        self.set_refresh_next_expand()

    def childCount(self) -> int:
        return len(self.children)

    def set_refresh_next_expand(self):
        self.children: list[TreeItem] = [None]  # dummy!!
        self._children_loaded: bool = False  # noqa: SLF001

    def load_children(self, model: ResourceFileSystemModel) -> list[TreeItem]:
        print(f"{self.__class__.__name__}({self.path}).load_children, row={self.row()}, col={self.column()}")
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
        for child in self.children:
            model.getContainerWidget().setItemIcon(child.index(), child.icon_data())
        if not self.children:
            self.set_refresh_next_expand()
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
        return self.icon_from_standard_pixmap(QStyle.StandardPixmap.SP_DirIcon, 16, 16)


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
        result_qfileiconprovider: QIcon = self.icon_from_extension(self.resource.restype().extension)
        return result_qfileiconprovider


class FileItem(ResourceItem):
    def icon_data(self) -> QIcon:
        result_qfileiconprovider: QIcon = self.icon_from_extension(self.resource.restype().extension)
        return result_qfileiconprovider

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

    def child(self, row: int) -> TreeItem:
        return self.children[row]

    def load_children(self: CapsuleItem | NestedCapsuleItem, model: ResourceFileSystemModel) -> list[CapsuleChildItem | NestedCapsuleItem]:
        print(f"{self.__class__.__name__}({self.path}).load_children, row={self.row()}, col={self.column()}")
        children: list[NestedCapsuleItem | CapsuleChildItem] = [
            NestedCapsuleItem(res, self)
            if is_capsule_file(res.filename())
            else CapsuleChildItem(res, self)
            for res in LazyCapsule(self.resource.filepath())
        ]
        self.set_children(children)
        return self.children

    def icon_data(self) -> QIcon:
        return self.icon_from_standard_pixmap(QStyle.StandardPixmap.SP_DirLinkOpenIcon, 16, 16)


class CapsuleChildItem(ResourceItem):
    def icon_data(self) -> QIcon:
        return self.icon_from_standard_pixmap(QStyle.StandardPixmap.SP_FileIcon, 16, 16)


class NestedCapsuleItem(CapsuleItem, CapsuleChildItem):
    def icon_data(self) -> QIcon:
        return self.icon_from_standard_pixmap(QStyle.StandardPixmap.SP_DirLinkIcon, 16, 16)


class SupportsRichComparison(Protocol):
    def __lt__(self, other: Any) -> bool: ...
    def __le__(self, other: Any) -> bool: ...
    def __gt__(self, other: Any) -> bool: ...
    def __ge__(self, other: Any) -> bool: ...

T = TypeVar("T", bound=Union[SupportsRichComparison, str])
class ResourceFileSystemModel(PyQStandardItemModel):
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
        self._testParent = parent
        super().__init__(parent=parent)
        self._detailed_view: bool = False
        self._root_item: DirItem | None = None
        self._headers: list[str] = ["File Name", "File Path", "Offset", "Size"]
        self._detailed_headers: list[str] = list({*self._headers, *self.COLUMN_TO_STAT_MAP.keys()})
        self._filter: QDir.Filter | QDir.Filters | int = QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot | QDir.Filter.AllDirs | QDir.Filter.Files

    def getTreeView(self) -> RobustTreeView:
        qparent_obj = QObject.parent(self)
        if not isinstance(qparent_obj, ResourceFileSystemWidget):
            raise RuntimeError("ResourceFileSystem MVC setup incorrectly, the parent of the model must be the container.")  # noqa: TRY004
        return qparent_obj.fsTreeView

    def getContainerWidget(self) -> ResourceFileSystemWidget:
        qparent_obj = QObject.parent(self)
        if not isinstance(qparent_obj, ResourceFileSystemWidget):
            raise RuntimeError("ResourceFileSystem MVC setup incorrectly, the parent of the model must be the container.")  # noqa: TRY004
        return qparent_obj

    def toggle_detailed_view(self):
        self._detailed_view = not self._detailed_view
        print("<SDM> [toggle_detailed_view scope] self._detailed_view: ", self._detailed_view)

        self.layoutAboutToBeChanged.emit()
        self.layoutChanged.emit()
        self.getContainerWidget().adjust_view_size()

    @property
    def rootPath(self) -> Path | None:
        return None if self._root_item is None else self._root_item.path

    def resetInternalData(self, *, _alwaysEndReset: bool = True):
        """Resets the internal data of the model, forcing a reload of the view. i.e.: restat's all files on disk and reloads them into the ui anew."""
        self.beginResetModel()

        # Clear the current root item and reset it
        if self._root_item:
            self._root_item.children.clear()
            self._root_item.load_children(self)

        if _alwaysEndReset:
            self.endResetModel()
        print("<SDM> [resetInternalData scope] Model data has been reset.")
        self.getContainerWidget().updateAddressBar()
 
    def setRootPath(self, path: os.PathLike | str):
        self.resetInternalData(_alwaysEndReset=False)
        self._root_item = self.create_fertile_tree_item(Path(path))
        print("<SDM> [setRootPath scope] self._root_item: ", self._root_item.path)

        self._root_item.load_children(self)
        self._root_index = self.index(0, 0, QModelIndex())
        assert self._root_index.isValid()
        filters = (
            QDir.Filter.AllEntries
            | QDir.Filter.NoDotAndDotDot
            | QDir.Filter.AllDirs
            | QDir.Filter.Files
            | (
                QDir.Filter.Hidden
                if bool(self.filter() & QDir.Filter.Hidden)
                else QDir.Filter(0)
            )
        )

        self.fileInfoList = QDir(str(self.rootPath)).entryInfoList(filters)  # pyright: ignore[reportCallIssue, reportArgumentType]
        self.endResetModel()

    def _getItem(self, index: QModelIndex) -> TreeItem | None:
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item
        return self._root_item

    def indexFromItem(self, item: PyQStandardItem) -> QModelIndex:
        if item == self._root_item:
            return QModelIndex()
        return self.createIndex(item.row(), item.column(), item)

    def itemFromIndex(self, index: QModelIndex) -> TreeItem | None:
        return self._getItem(index)

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
        inst = cls(path)
        return inst

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        parent = QModelIndex() if parent is None else parent
        if not parent.isValid():  # Root level
            res = self._root_item.childCount() if self._root_item else 0
            return res or 0
        item = parent.internalPointer()
        assert isinstance(item, TreeItem)
        res = item.childCount() if item else 0
        return res or 0

    def columnCount(self, parent: QModelIndex | None = None) -> int:
        parent = QModelIndex() if parent is None else parent
        return len(self._detailed_headers if self._detailed_view else self._headers)

    def index(self, row: int, column: int, parent: QModelIndex | None = None) -> QModelIndex:
        parent = QModelIndex() if parent is None else parent
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        parent_item = parent.internalPointer() if parent.isValid() else self._root_item
        assert isinstance(parent_item, TreeItem)
        child_item = parent_item.child(row) if parent_item else None
        if child_item:
            return self.createIndex(row, column, child_item)
        return QModelIndex()

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
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
                return item.icon_data()
        if role == Qt.ItemDataRole.DisplayRole:
            if self._detailed_view:
                return self.get_detailed_data(index)
            return self.get_default_data(index)

        if role == Qt.ItemDataRole.DecorationRole and index.column() == 0:
            return item.icon_data()

        if role == _ICONS_DATA_ROLE and index.column() == 0:
            icon_data = {
                "icons": [(item.icon_data(), None, "Item icon")],
                "size": 32,
                "spacing": 5,
                "rows": 1,
                "columns": 1,
            }
            self.setData(index, icon_data, _ICONS_DATA_ROLE)

        return None

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        if not index.isValid():
            return False
        if role == Qt.ItemDataRole.EditRole:
            self.dataChanged.emit(index, index, [role])
            return True
        return False

    def canFetchMore(self, index: QModelIndex) -> bool:
        print(f"canFetchMore({index.row()}, {index.column()})")
        if not index.isValid():
            return False
        item = index.internalPointer()
        result = isinstance(item, DirItem) and (item.childCount() == 0 or item.has_dummy_child())
        print("<SDM> [canFetchMore scope] result: ", result)
        return result

    def fetchMore(self, index: QModelIndex) -> None:
        print(f"fetchMore({index.row()}, {index.column()})")
        if not index.isValid():
            return

        item: TreeItem = index.internalPointer()
        print(
            "<SDM> [fetchMore scope] index.internalPointer(): ", item,
            f"row: {'item is None' if item is None else item.row()}",
            f"column: {'item is None' if item is None else item.column()}",
        )

        if isinstance(item, DirItem):
            item.load_children(self)
            self.layoutChanged.emit()

    def filter(self) -> QDir.Filter:
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
        child_item: Any = index.internalPointer()
        if not isinstance(child_item, TreeItem):
            return QModelIndex()
        parent_item = child_item.parent if child_item else None
        if parent_item == self._root_item or not parent_item:
            return QModelIndex()
        row = parent_item.row() if hasattr(parent_item, "row") else parent_item().row()  # pyright: ignore[reportCallIssue]
        return self.createIndex(row, 0, parent_item)

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
            return str(item.path if isinstance(item, DirItem) else item.resource.filepath().relative_to(self.rootPath))  # pyright: ignore[reportCallIssue, reportArgumentType]
        if column_name == "Offset":
            return "0x0" if isinstance(item, DirItem) else f"{hex(item.resource.offset())}"
        if column_name == "Size":
            return "" if isinstance(item, DirItem) else self.human_readable_size(item.resource.size())
        return "N/A"

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder):
        def get_sort_key(item: TreeItem | None, original_index: int) -> tuple:
            """Generate a sort key that prioritizes directories over files and correctly sorts file sizes."""
            if item is None:
                return (1, "", original_index)  # Sort None items last

            is_dir = isinstance(item, DirItem)
            index = self.indexFromItem(item)
            if not index.isValid():
                return (1, "", original_index)
            column_name = self._detailed_headers[column] if self._detailed_view else self._headers[column]
            if column_name == "Size":
                assert isinstance(item, (DirItem, ResourceItem))
                size_value = 0 if isinstance(item, DirItem) else item.resource.size()
                key = (0 if is_dir else 1, size_value)  # Directories first, then by size in bytes
            else:
                value = self.data(index.sibling(index.row(), column), Qt.ItemDataRole.DisplayRole)
                if value is None:
                    value = ""
                try:  # noqa: SIM105
                    value = float(value)
                except (ValueError, TypeError):  # noqa: S110
                    ...
                key = (0 if is_dir else 1, value) if isinstance(value, (float, int)) else (0 if is_dir else 1, value.lower())

            return (*key, original_index)

        def sort_items(items: list[TreeItem]):
            items_copy = [(item, i) for i, item in enumerate(items)]
            items_copy.sort(key=lambda x: get_sort_key(x[0], x[1]), reverse=(order == Qt.SortOrder.DescendingOrder))
            for item in items_copy:
                if isinstance(item, DirItem):
                    sort_items(item.children)
            items[:] = [item for item, _ in items_copy]

        if self._root_item is not None:
            self.layoutAboutToBeChanged.emit()
            sort_items(self._root_item.children)
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
        self.rFileSystemWidget.setRootPath(root_path)

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.rFileSystemWidget)
        self.setCentralWidget(central_widget)
        self.setMinimumSize(824, 568)
        self.resize_and_center()

    def resize_and_center(self):
        """Resize and center the window on the screen."""
        self.rFileSystemWidget.adjust_view_size()
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
    print("<SDM> [create_example_directory_structure scope] main_window: ", main_window)

    main_window.show()

    sys.exit(app.exec_() if hasattr(app, "exec_") else app.exec())  # pyright: ignore[reportAttributeAccessIssue]
