from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from utility.gui.qt.common.filesystem.tree import PyFileSystemNode


class PyFileSystemModelSorter:
    def __init__(self, column: int):
        self.sortColumn: int = column

    def compareNodes(self, fileInfoLeft: PyFileSystemNode, fileInfoRight: PyFileSystemNode) -> bool:  # noqa: PLR0911, N803
        if self.sortColumn == 0:  # Column 0: Sort by file name
            if fileInfoLeft.isDir() ^ fileInfoRight.isDir():
                return fileInfoLeft.isDir()
            return self._natural_compare(fileInfoLeft.fileName, fileInfoRight.fileName) < 0
        if self.sortColumn == 1:  # Column 1: Sort by size
            if fileInfoLeft.isDir() ^ fileInfoRight.isDir():
                return fileInfoLeft.isDir()
            sizeDifference = fileInfoLeft.size() - fileInfoRight.size()
            if sizeDifference == 0:
                return self._natural_compare(fileInfoLeft.fileName, fileInfoRight.fileName) < 0
            return sizeDifference < 0
        if self.sortColumn == 2:  # Column 2: Sort by type
            compare = self._natural_compare(fileInfoLeft.type(), fileInfoRight.type())
            if compare == 0:
                return self._natural_compare(fileInfoLeft.fileName, fileInfoRight.fileName) < 0
            return compare < 0
        if self.sortColumn == 3:  # Column 3: Sort by last modified
            if fileInfoLeft.lastModified().toTime_t() == fileInfoRight.lastModified().toTime_t():
                return self._natural_compare(fileInfoLeft.fileName, fileInfoRight.fileName) < 0
            return fileInfoLeft.lastModified().toTime_t() < fileInfoRight.lastModified().toTime_t()
        return False

    def _natural_compare(self, a: str, b: str) -> int:
        """Natural comparison function for sorting."""
        return (a > b) - (a < b)  # Simplified natural comparison
