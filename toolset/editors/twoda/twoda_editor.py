from typing import Optional

import pyperclip as pyperclip
from PyQt5.QtCore import QSortFilterProxyModel
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QShortcut, QMessageBox, QWidget
from pykotor.extract.installation import Installation
from pykotor.resource.formats.twoda import TwoDA, write_2da, load_2da
from pykotor.resource.type import ResourceType

from editors.editor import Editor
from editors.twoda import twoda_editor_ui


class TwoDAEditor(Editor):
    def __init__(self, parent: QWidget, installation: Optional[Installation] = None):
        super().__init__(parent, "2DA Editor", [ResourceType.TwoDA], [ResourceType.TwoDA], installation)
        self.resize(400, 250)

        self.ui = twoda_editor_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_menus()
        self.ui.filterBox.setVisible(False)

        self.model = QStandardItemModel(self)
        self.ui.twodaTable.setModel(self.model)
        self.proxyModel = SortFilterProxyModel(self)
        self.proxyModel.setSourceModel(self.model)

        self.ui.filterEdit.textEdited.connect(self.doFilter)
        self.ui.actionToggleFilter.triggered.connect(self.toggleFilter)
        self.ui.actionCopy.triggered.connect(self.copySelection)
        self.ui.actionPaste.triggered.connect(self.pasteSelection)

        QShortcut("Ctrl+F", self).activated.connect(self.toggleFilter)
        QShortcut("Ctrl+C", self).activated.connect(self.copySelection)
        QShortcut("Ctrl+V", self).activated.connect(self.pasteSelection)

        self.new()

    def load(self, filepath: str, resref: str, restype: ResourceType, data: bytes) -> None:
        super().load(filepath, resref, restype, data)
        self.model.clear()
        self.model.setRowCount(0)

        try:
            twoda = load_2da(data)

            headers = list(twoda.get_headers())
            self.model.setColumnCount(len(headers))
            self.model.setHorizontalHeaderLabels(headers)

            for i, row in enumerate(twoda):
                self.model.insertRow(i)
                for j, header in enumerate(headers):
                    self.model.setItem(i, j, QStandardItem(row.get_string(header)))

            for i in range(twoda.get_height()):
                self.ui.twodaTable.resizeColumnToContents(i)

            self.model.setVerticalHeaderLabels([str(i) for i in range(twoda.get_height())])
        except ValueError as e:
            QMessageBox(QMessageBox.Critical, "Failed to load file.", "Failed to open or load file data.").exec_()
            self.new()

    def build(self) -> bytes:
        twoda = TwoDA()

        for i in range(self.model.columnCount()):
            twoda.add_column(self.model.horizontalHeaderItem(i).text())

        for i in range(self.model.rowCount()):
            twoda.add_row()
            for j, header in enumerate(twoda.get_headers()):
                twoda.set_cell(i, header, self.model.item(i, j).text())

        data = bytearray()
        write_2da(twoda, data)
        return data

    def new(self) -> None:
        super().new()

        self.model.clear()
        self.model.setRowCount(0)

    def doFilter(self, text: str) -> None:
        self.proxyModel.setFilterFixedString(text)

    def isFiltered(self) -> None:
        return self.proxyModel is self.ui.twodaTable.model()

    def toggleFilter(self) -> None:
        if not self.isFiltered():
            self.ui.twodaTable.setModel(self.proxyModel)

        visible = not self.ui.filterBox.isVisible()
        self.ui.filterBox.setVisible(visible)
        if visible:
            self.doFilter(self.ui.filterEdit.text())
        else:
            self.doFilter("")

    def copySelection(self) -> None:
        top = self.model.rowCount()
        bottom = -1
        left = self.model.columnCount()
        right = -1

        for index in self.ui.twodaTable.selectedIndexes():
            index = self.proxyModel.mapToSource(index) if self.isFiltered() else index

            top = min([top, index.row()])
            bottom = max([bottom, index.row()])
            left = min([left, index.column()])
            right = max([right, index.column()])

        clipboard = ""
        for j in range(top, bottom + 1):
            for i in range(left, right + 1):
                clipboard += self.model.item(j, i).text()
                if i != right:
                    clipboard += "\t"
            if j != bottom:
                clipboard += "\n"

        pyperclip.copy(clipboard)

    def pasteSelection(self) -> None:
        rows = pyperclip.paste().split("\n")

        topLeftIndex = self.proxyModel.mapToSource(self.ui.twodaTable.selectedIndexes()[0]) if self.isFiltered() else self.ui.twodaTable.selectedIndexes()[0]
        topLeftItem = self.model.itemFromIndex(topLeftIndex)

        top, left = y, x = topLeftItem.row(), topLeftItem.column()

        for row in rows:
            for cell in row.split("\t"):
                item = self.model.item(y, x)
                if item:
                    item.setText(cell)
                x += 1
            x = left
            y += 1


class SortFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent):
        super().__init__(parent)
        self._filterString: str = ""

    def filterAcceptsRow(self, sourceRow, sourceParent):
        if self.filterRegExp().pattern() == "":
            return True
        for i in range(self.sourceModel().columnCount()):
            index = self.sourceModel().index(sourceRow, i, sourceParent)
            if self.sourceModel().data(index) is not None and self.filterRegExp().pattern() in self.sourceModel().data(index):
                return True
        return False
