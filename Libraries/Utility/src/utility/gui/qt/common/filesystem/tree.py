from __future__ import annotations

from typing import TYPE_CHECKING, Any

from qtpy.QtCore import QAbstractItemModel, QModelIndex, QVariant, Qt, Signal
from qtpy.QtGui import QIcon

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget


class FileSystemNode:
    def __init__(self, name: str, parent: "FileSystemNode" | None = None,
                 is_dir: bool = False, size: str = "", ftype: str = "",
                 date_modified: str = "", path: str = ""):
        self.name = name
        self.parent = parent
        self.children = []
        self.is_dir = is_dir
        self.size = size
        self.type = ftype
        self.date_modified = date_modified
        self.path = path
        self.icon = "folder.png" if is_dir else "file.png"

    def addChild(self, child: 'FileSystemNode'):
        child.parent = self
        self.children.append(child)

    def removeChild(self, position: int):
        if position < 0 or position >= len(self.children):
            return False
        child = self.children.pop(position)
        child.parent = None
        return True

    def child(self, row: int):
        if row >= 0 and row < len(self.children):
            return self.children[row]
        return None

    def childCount(self):
        return len(self.children)

    def row(self):
        if self.parent:
            return self.parent.children.index(self)
        return 0

    def columnCount(self):
        return 4

    def data(self, column: int):
        mapping = {
            0: self.name,
            1: self.size,
            2: self.type,
            3: self.date_modified
        }
        return mapping.get(column, None)

class CustomFileSystemModel(QAbstractItemModel):
    directoryLoaded = Signal(str)
    rootPathChanged = Signal(str)
    fileRenamed = Signal(str, str, str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.rootNode = FileSystemNode("Root", is_dir=True)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.column() > 0:
            return 0
        if not parent.isValid():
            return self.rootNode.childCount()
        else:
            return parent.internalPointer().childCount()

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 4  # Name, Size, Type, Date Modified

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return QVariant()
        node = index.internalPointer()
        if role == Qt.DisplayRole:
            return node.data(index.column())
        if role == Qt.DecorationRole and index.column() == 0:
            return QIcon(node.icon)
        return QVariant()

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            headers = ["Name", "Size", "Type", "Date Modified"]
            if 0 <= section < len(headers):
                return headers[section]
        return QVariant()

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        parentNode = self.rootNode if not parent.isValid() else parent.internalPointer()
        childNode = parentNode.child(row)
        if childNode:
            return self.createIndex(row, column, childNode)
        else:
            return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()
        childNode = index.internalPointer()
        parentNode = childNode.parent
        if parentNode == self.rootNode or parentNode is None:
            return QModelIndex()
        return self.createIndex(parentNode.row(), 0, parentNode)

    def hasChildren(self, parent: QModelIndex = QModelIndex()) -> bool:
        if parent.column() > 0:
            return False
        if not parent.isValid():
            return self.rootNode.childCount() > 0
        return parent.internalPointer().childCount() > 0

    def setRootPath(self, path: str) -> QModelIndex:
        # Simulate setting a new root path
        self.beginResetModel()
        self.rootNode = FileSystemNode(path.split("/")[-1], is_dir=True)
        self.endResetModel()
        self.rootPathChanged.emit(path)
        return self.createIndex(0, 0, self.rootNode)

    def addNode(self, name: str, is_dir: bool = False, size: str = "",
                type: str = "", date_modified: str = "", path: str = "", parent: FileSystemNode | None = None):
        if parent is None:
            parent = self.rootNode
        newNode = FileSystemNode(name, parent, is_dir, size, type, date_modified, path)
        parent.addChild(newNode)
        parentIndex = self.createIndex(parent.row(), 0, parent)
        self.beginInsertRows(parentIndex, parent.childCount() - 1, parent.childCount() - 1)
        self.endInsertRows()
