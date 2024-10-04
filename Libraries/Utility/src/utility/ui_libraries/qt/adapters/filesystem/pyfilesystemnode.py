from __future__ import annotations

import os
import pathlib
import sys

from typing import TYPE_CHECKING

from qtpy.QtCore import QDateTime, QFileDevice, QFileInfo  # noqa: E402
from qtpy.QtGui import QIcon  # noqa: E402
from qtpy.QtWidgets import QFileIconProvider  # noqa: E402


def update_sys_path(path: pathlib.Path):
    working_dir = str(path)
    print("<SDM> [update_sys_path scope] working_dir: ", working_dir)

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
        if __name__ == "__main__":
            os.chdir(toolset_path)

from utility.ui_libraries.qt.adapters.filesystem.pyextendedinformation import PyQExtendedInformation  # noqa: E402

if TYPE_CHECKING:
    from qtpy.QtCore import QModelIndex


class PyFileSystemNode:
    iconProvider: QFileIconProvider = QFileIconProvider()

    def __init__(
        self,
        filename: str = "",
        parent: PyFileSystemNode | None = None,
    ):
        self.fileName: str = filename
        if os.name == "nt":
            self.volumeName: str = ""
        self.parent: PyFileSystemNode | None = parent
        self.info: QFileInfo | None = None  # QExtendedInformation
        self.children: dict[str, PyFileSystemNode] = {}
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
        # return self.parent.children[info.fileName()].index(self)
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
            self.info = QFileInfo(
                fileInfo.fileInfo()
                if isinstance(fileInfo, PyQExtendedInformation)
                else fileInfo
            )

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
