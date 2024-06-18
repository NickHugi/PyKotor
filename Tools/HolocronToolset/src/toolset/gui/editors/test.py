from __future__ import annotations

import sys

from qtpy.QtCore import QByteArray, QDataStream, QIODevice, QMimeData, Qt
from qtpy.QtGui import QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QApplication, QMainWindow, QTreeView, QVBoxLayout, QWidget


class CustomStandardItem(QStandardItem):
    def __init__(self, text):
        super().__init__(text)

    def __eq__(self, other):
        if not isinstance(other, CustomStandardItem):
            return NotImplemented
        return id(self) == id(other)

    def __hash__(self):
        return id(self)

class CustomStandardItemModel(QStandardItemModel):
    def __init__(self, parent=None):
        super().__init__(parent)

    def mimeData(self, indexes):
        mimeData = QMimeData()
        encodedData = QByteArray()
        stream = QDataStream(encodedData, QIODevice.WriteOnly)
        for index in indexes:
            if index.isValid():
                item = self.itemFromIndex(index)
                stream.writeQString(item.text())
        mimeData.setData("application/x-custom-item", encodedData)
        return mimeData

    def dropMimeData(self, data, action, row, column, parent):
        if not data.hasFormat("application/x-custom-item"):
            return False

        if action == Qt.IgnoreAction:
            return True

        if parent.isValid():
            parentItem = self.itemFromIndex(parent)
        else:
            parentItem = self.invisibleRootItem()

        encodedData = data.data("application/x-custom-item")
        stream = QDataStream(encodedData, QIODevice.ReadOnly)
        while not stream.atEnd():
            text = stream.readQString()
            newItem = CustomStandardItem(text)

            if row == -1:
                row = parentItem.rowCount()
            parentItem.insertRow(row, newItem)

        return True

    def supportedDropActions(self):
        return Qt.MoveAction

    def flags(self, index):
        defaultFlags = super().flags(index)
        if index.isValid():
            return Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled | defaultFlags
        return Qt.ItemIsDropEnabled | defaultFlags

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drag and Drop Example")

        self.treeView = QTreeView()
        self.model = CustomStandardItemModel()
        self.treeView.setModel(self.model)

        rootNode = self.model.invisibleRootItem()

        for i in range(3):
            item = CustomStandardItem(f"Item {i}")
            rootNode.appendRow(item)

        self.treeView.setDragDropMode(QTreeView.InternalMove)

        centralWidget = QWidget()
        layout = QVBoxLayout(centralWidget)
        layout.addWidget(self.treeView)
        self.setCentralWidget(centralWidget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
