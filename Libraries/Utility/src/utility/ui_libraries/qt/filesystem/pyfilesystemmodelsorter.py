from __future__ import annotations
from typing import TYPE_CHECKING
from PyQt5.QtCore import Qt

if TYPE_CHECKING:
    from utility.gui.qt.common.filesystem.pyfilesystemmodel import PyFileSystemNode

class SortingError(Exception):
    pass

class PyFileSystemModelSorter:
    def __init__(self, column: int):
        self.sortColumn: int = column

    def sort(self, root: PyFileSystemNode, column: int, order: Qt.SortOrder):
        self.sortColumn = column
        try:
            root.children = dict(sorted(root.children.items(), key=lambda x: self._compareNodes(x[1], x[1]), reverse=(order == Qt.DescendingOrder)))
        except Exception as e:
            raise SortingError(f"Error during sorting: {str(e)}")

    def _compareNodes(self, fileInfoLeft: PyFileSystemNode, fileInfoRight: PyFileSystemNode) -> bool:
        if self.sortColumn == 0:  # Column 0: Sort by file name
            if fileInfoLeft.isDir() ^ fileInfoRight.isDir():
                return fileInfoLeft.isDir()
            return self._natural_compare(fileInfoLeft.fileName, fileInfoRight.fileName)
        if self.sortColumn == 1:  # Column 1: Sort by size
            if fileInfoLeft.isDir() ^ fileInfoRight.isDir():
                return fileInfoLeft.isDir()
            sizeDifference = fileInfoLeft.size() - fileInfoRight.size()
            if sizeDifference == 0:
                return self._natural_compare(fileInfoLeft.fileName, fileInfoRight.fileName)
            return sizeDifference
        if self.sortColumn == 2:  # Column 2: Sort by type
            compare = self._natural_compare(fileInfoLeft.type(), fileInfoRight.type())
            if compare == 0:
                return self._natural_compare(fileInfoLeft.fileName, fileInfoRight.fileName)
            return compare
        if self.sortColumn == 3:  # Column 3: Sort by last modified
            if fileInfoLeft.lastModified() == fileInfoRight.lastModified():
                return self._natural_compare(fileInfoLeft.fileName, fileInfoRight.fileName)
            return fileInfoLeft.lastModified() < fileInfoRight.lastModified()
        return False

    def _natural_compare(self, a: str, b: str) -> int:
        """Natural comparison function for sorting."""
        import re
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
        return alphanum_key(a) < alphanum_key(b)
