from __future__ import annotations

import os
import pathlib
import sys

from abc import abstractmethod
from typing import TYPE_CHECKING

from utility.gui.qt.common.filesystem.icons import qicon_from_file_ext, qpixmap_to_qicon
from utility.logger_util import RobustRootLogger


def update_sys_path(path: pathlib.Path):
    working_dir = str(path)
    print("<SDM> [update_sys_path scope] working_dir: ", working_dir)

    if working_dir not in sys.path:
        sys.path.append(working_dir)


file_absolute_path = pathlib.Path(__file__).resolve()

pykotor_path = file_absolute_path.parents[8] / "Libraries" / "PyKotor" / "src" / "pykotor"
if pykotor_path.exists():
    update_sys_path(pykotor_path.parent)
pykotor_gl_path = file_absolute_path.parents[8] / "Libraries" / "PyKotorGL" / "src" / "pykotor"
if pykotor_gl_path.exists():
    update_sys_path(pykotor_gl_path.parent)
utility_path = file_absolute_path.parents[5]
if utility_path.exists():
    update_sys_path(utility_path)
toolset_path = file_absolute_path.parents[8] / "Tools/HolocronToolset/src/toolset"
if toolset_path.exists():
    update_sys_path(toolset_path.parent)
    os.chdir(toolset_path)
print(toolset_path)
print(utility_path)

import qtpy  # noqa: E402

if qtpy.API_NAME in ("PyQt6", "PySide6"):
    QDesktopWidget = None
    from qtpy.QtGui import QUndoCommand, QUndoStack  # pyright: ignore[reportPrivateImportUsage]  # noqa: F401
elif qtpy.API_NAME in ("PyQt5", "PySide2"):
    from qtpy.QtWidgets import QDesktopWidget, QUndoCommand, QUndoStack  # noqa: F401  # pyright: ignore[reportPrivateImportUsage]
else:
    raise RuntimeError(f"Unexpected qtpy version: '{qtpy.API_NAME}'")


from qtpy.QtCore import QDateTime, QFileDevice, QFileInfo  # noqa: E402
from qtpy.QtGui import QIcon  # noqa: E402
from qtpy.QtWidgets import QFileIconProvider, QStyle  # noqa: E402

from pykotor.extract.capsule import LazyCapsule  # noqa: E402
from pykotor.extract.file import FileResource  # noqa: E402
from pykotor.tools.misc import is_capsule_file  # noqa: E402
from utility.common.more_collections import CaseInsensitiveDict  # noqa: E402
from utility.gui.qt.common.filesystem.pyfileinfogatherer import PyQExtendedInformation  # noqa: E402
from utility.system.path import Path  # noqa: E402

if TYPE_CHECKING:
    from qtpy.QtCore import QModelIndex
    from qtpy.QtWidgets import QFileSystemModel

    from toolset.gui.widgets.kotor_filesystem_model import ResourceFileSystemModel


class PyFileSystemNode:
    iconProvider: QFileIconProvider = QFileIconProvider()

    def __init__(
        self,
        filename: str = "",
        parent: PyFileSystemNode | None = None,
    ):
        self.fileName: str = filename
        if sys.platform == "win32":
            self.volumeName: str = ""
        self.parent: PyFileSystemNode | None = parent
        self.info: QFileInfo | None = None  # QExtendedInformation
        self.children: CaseInsensitiveDict[PyFileSystemNode] = CaseInsensitiveDict()
        self.visibleChildren: list[str] = []
        self.dirtyChildrenIndex: int = -1
        self.populatedChildren: bool = False
        self.isVisible: bool = False

    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, PyFileSystemNode):
            parsed_other = other.fileName
        elif isinstance(other, (str, os.PathLike)):
            parsed_other = os.fspath(other)
        elif isinstance(other, (QFileInfo, QFileInfo)):
            parsed_other = other.filePath()
        else:
            return NotImplemented

        if self.caseSensitive() or isinstance(other, PyFileSystemNode) and other.caseSensitive():
            return self.fileName == parsed_other
        return self.fileName.lower() == parsed_other.lower()

    def __lt__(self, other: PyFileSystemNode) -> bool:
        if self.caseSensitive() or other.caseSensitive():
            return self.fileName < other.fileName
        return self.fileName.lower() < other.fileName.lower()

    def __gt__(self, other: PyFileSystemNode) -> bool:
        if self.caseSensitive() or other.caseSensitive():
            return self.fileName > other.fileName
        return self.fileName.lower() > other.fileName.lower()

    def row(self) -> int:
        info = self.fileInfo()
        if info is None:
            return -1
        if self.parent is None:
            return 0
        #return self.parent.children[info.fileName()].index(self)
        sorted_children_keys = sorted(self.parent.children.keys())
        index = self._binary_search(sorted_children_keys, self.fileName)
        return index if sorted_children_keys[index] == self.fileName else -1

    def _binary_search(self, sorted_list: list[str], item: str) -> int:
        low, high = 0, len(sorted_list)
        while low < high:
            mid = (low + high) // 2
            if sorted_list[mid] < item:
                low = mid + 1
            else:
                high = mid
        return low

    def fileInfo(self) -> QFileInfo | None:
        return None if self.info is None else self.info

    def size(self) -> int:
        info = self.fileInfo()
        return 0 if info is None or not self.isDir() else info.size()

    def type(self) -> str:
        info = self.fileInfo()
        return "" if info is None else info.suffix()

    def lastModified(self) -> QDateTime:
        info = self.fileInfo()
        r1 = QDateTime() if info is None else info.lastModified()
        return QDateTime() if r1 is None else r1

    def permissions(self) -> QFileDevice.Permissions | int:
        info = self.fileInfo()
        r1 = QFileDevice.Permissions() if info is None else info.permissions()
        return QFileDevice.Permissions() if r1 is None else r1

    def isReadable(self) -> bool:
        return (self.permissions() & QFileDevice.Permission.ReadUser) != 0

    def isWritable(self) -> bool:
        return (self.permissions() & QFileDevice.Permission.WriteUser) != 0

    def isExecutable(self) -> bool:
        return (self.permissions() & QFileDevice.Permission.ExeUser) != 0

    def isDir(self) -> bool:
        info = self.fileInfo()
        return len(self.children) > 0 if info is None else info.isDir()

    def isFile(self) -> bool:
        info = self.fileInfo()
        return True if info is None else info.isFile()

    def isSystem(self) -> bool:
        info = self.fileInfo()
        if info is None or not info.exists():
            return False
        if not info.exists():
            return False
        return info.isFile() or info.isDir() or self.isSymLink()

    def isHidden(self) -> bool:
        info = self.fileInfo()
        return info is not None and info.isHidden()

    def isHiddenByFilter(self, indexNode: PyFileSystemNode, index: QModelIndex) -> bool:  # noqa: N803
        return indexNode.parent is not None and index.isValid()

    def isSymLink(self) -> bool:
        info = self.fileInfo()
        return info is not None and info.isSymLink()

    def caseSensitive(self) -> bool:
        return os.name == "posix"

    def icon(self) -> QIcon:
        info = self.fileInfo()
        return QIcon() if info is None else self.iconProvider.icon(info)

    def hasInformation(self) -> bool:
        return self.info is not None

    def populate(self, fileInfo: PyQExtendedInformation | QFileInfo):  # noqa: N803
        info = self.fileInfo()
        if info is None or not info.exists():  # noqa: PTH110
            self.info = QFileInfo(fileInfo.fileInfo() if isinstance(fileInfo, PyQExtendedInformation) else fileInfo)

    def visibleLocation(self, childName: str) -> int:  # noqa: N803
        return self.visibleChildren.index(childName)

    def updateIcon(self, iconProvider: QFileIconProvider, path: str):  # noqa: N803
        for child in self.children.values():
            if path.endswith("/"):
                child.updateIcon(iconProvider, path + child.fileName)
            else:
                child.updateIcon(iconProvider, f"{path}/{child.fileName}")

    def retranslateStrings(self, iconProvider: QFileIconProvider, path: str):  # noqa: N803
        info = self.fileInfo()
        if info is not None:
            info.setFile(path)
        for child in self.children.values():
            if path.endswith("/"):
                child.retranslateStrings(iconProvider, path + child.fileName)
            else:
                child.retranslateStrings(iconProvider, f"{path}/{child.fileName}")


class TreeItem:
    icon_provider: QFileIconProvider = QFileIconProvider()

    def __init__(
        self,
        path: os.PathLike | str,
        parent: DirItem | None = None,
    ):
        super().__init__()
        self.path: Path = Path.pathify(path)
        self.parent: DirItem | None = parent

    def row(self) -> int:
        if self.parent is None:
            return -1
        if isinstance(self.parent, DirItem):
            if self not in self.parent.children:
                RobustRootLogger().warning(f"parent '{self.parent.path}' has orphaned the item '{self.path}' without warning!")
                return -1
            return self.parent.children.index(self)
        raise RuntimeError(f"INVALID parent item! Only `DirItem` instances should children, but parent was: '{self.parent.__class__.__name__}'")

    @abstractmethod
    def childCount(self) -> int:
        return 0

    @abstractmethod
    def iconData(self) -> QIcon:
        ...

    def data(self) -> str:
        return self.path.name


class DirItem(TreeItem):
    def __init__(
        self,
        path: Path,
        parent: DirItem | None = None,
    ):
        super().__init__(path, parent)
        self.children: list[TreeItem | None] = [None]  # dummy!!

    def childCount(self) -> int:
        return len(self.children)

    def loadChildren(self, model: ResourceFileSystemModel | QFileSystemModel) -> list[TreeItem | None]:
        print(f"{self.__class__.__name__}({self.path}).load_children, row={self.row()}")
        children: list[TreeItem] = []
        toplevel_items = list(self.path.safe_iterdir())
        for child_path in sorted(toplevel_items):
            if child_path.is_dir():
                item = DirItem(child_path, self)
            elif is_capsule_file(child_path):
                item = CapsuleItem(child_path, self)
            else:
                item = FileItem(child_path, self)
            children.append(item)
        self.children = list(children)
        for child in self.children:
            if child is None:
                continue
            model.getContainerWidget().setItemIcon(model.indexFromItem(child), child.iconData())
        return self.children

    def child(self, row: int) -> TreeItem | None:
        return self.children[row]

    def iconData(self) -> QIcon:
        return qpixmap_to_qicon(QStyle.StandardPixmap.SP_DirIcon, 16, 16)


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

    def iconData(self) -> QIcon:
        result_qfileiconprovider: QIcon = qicon_from_file_ext(self.resource.restype().extension)
        return result_qfileiconprovider


class FileItem(ResourceItem):
    def iconData(self) -> QIcon:
        result_qfileiconprovider: QIcon = qicon_from_file_ext(self.resource.restype().extension)
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

    def loadChildren(self: CapsuleItem | NestedCapsuleItem, model: ResourceFileSystemModel) -> list[CapsuleChildItem | NestedCapsuleItem]:
        print(f"{self.__class__.__name__}({self.path}).load_children, row={self.row()}")
        children: list[NestedCapsuleItem | CapsuleChildItem] = [
            NestedCapsuleItem(res, self)
            if is_capsule_file(res.filename())
            else CapsuleChildItem(res, self)
            for res in LazyCapsule(self.resource.filepath())
        ]
        self.children = children
        return self.children

    def iconData(self) -> QIcon:
        return qpixmap_to_qicon(QStyle.StandardPixmap.SP_DirLinkOpenIcon, 16, 16)


class CapsuleChildItem(ResourceItem):
    def iconData(self) -> QIcon:
        return qpixmap_to_qicon(QStyle.StandardPixmap.SP_FileIcon, 16, 16)


class NestedCapsuleItem(CapsuleItem, CapsuleChildItem):
    def iconData(self) -> QIcon:
        return qpixmap_to_qicon(QStyle.StandardPixmap.SP_DirLinkIcon, 16, 16)
