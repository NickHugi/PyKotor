from typing import Optional

import pyperclip as pyperclip
from PyQt5 import QtCore
from PyQt5.QtCore import QSortFilterProxyModel
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon, QPixmap
from PyQt5.QtWidgets import QShortcut, QMessageBox, QWidget
from pykotor.resource.formats.twoda import TwoDA, write_2da, load_2da
from pykotor.resource.type import ResourceType

from data.installation import HTInstallation
from editors.editor import Editor
from editors.twoda import twoda_editor_ui


class TwoDAEditor(Editor):
    def __init__(self, parent: QWidget, installation: Optional[HTInstallation] = None):
        supported = [ResourceType.TwoDA, ResourceType.TwoDA_CSV]
        super().__init__(parent, "2DA Editor", supported, supported, installation)
        self.resize(400, 250)

        self.ui = twoda_editor_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_menus()
        self.ui.filterBox.setVisible(False)

        iconVersion = "x" if installation is None else "2" if installation.tsl else "1"
        iconPath = ":/images/icons/k{}/none.png".format(iconVersion)
        self.setWindowIcon(QIcon(QPixmap(iconPath)))

        self.model = QStandardItemModel(self)
        self.proxyModel = SortFilterProxyModel(self)
        self.proxyModel.setSourceModel(self.model)

        self.ui.filterEdit.textEdited.connect(self.doFilter)
        self.ui.actionToggleFilter.triggered.connect(self.toggleFilter)
        self.ui.actionCopy.triggered.connect(self.copySelection)
        self.ui.actionPaste.triggered.connect(self.pasteSelection)

        self.ui.actionInsertRow.triggered.connect(self.insertRow)
        self.ui.actionRemoveRows.triggered.connect(self.removeSelectedRows)
        self.ui.actionRedoRowLabels.triggered.connect(self.redoRowLabels)

        QShortcut("Ctrl+F", self).activated.connect(self.toggleFilter)
        QShortcut("Ctrl+C", self).activated.connect(self.copySelection)
        QShortcut("Ctrl+V", self).activated.connect(self.pasteSelection)
        QShortcut("Ctrl+I", self).activated.connect(self.insertRow)
        QShortcut("Ctrl+D", self).activated.connect(self.removeSelectedRows)

        self.new()

    def load(self, filepath: str, resref: str, restype: ResourceType, data: bytes) -> None:
        super().load(filepath, resref, restype, data)
        self.model = QStandardItemModel(self)
        self.proxyModel = SortFilterProxyModel(self)

        try:
            twoda = load_2da(data)

            headers = [""] + list(twoda.get_headers())
            self.model.setColumnCount(len(headers))
            self.model.setHorizontalHeaderLabels(headers)

            for i, row in enumerate(twoda):
                self.model.insertRow(i)
                for j, header in enumerate(headers):
                    if j == 0:
                        self.model.setItem(i, 0, QStandardItem(str(twoda.get_label(i))))
                        font = self.model.item(i, 0).font()
                        font.setBold(True)
                        self.model.item(i, 0).setFont(font)
                        self.model.item(i, 0).setBackground(self.palette().midlight())
                    else:
                        self.model.setItem(i, j, QStandardItem(row.get_string(header)))

            self.model.setVerticalHeaderLabels(["   " for i in range(twoda.get_height())])
            self.ui.twodaTable.setModel(self.proxyModel)

            self.proxyModel.setSourceModel(self.model)
            for i in range(twoda.get_height()):
                self.ui.twodaTable.resizeColumnToContents(i)
        except ValueError as e:
            QMessageBox(QMessageBox.Critical, "Failed to load file.", "Failed to open or load file data.").exec_()
            self.proxyModel.setSourceModel(self.model)
            self.new()

    def build(self) -> bytes:
        twoda = TwoDA()

        for i in range(self.model.columnCount())[1:]:
            twoda.add_column(self.model.horizontalHeaderItem(i).text())

        for i in range(self.model.rowCount()):
            twoda.add_row()
            twoda.set_label(i, int(self.model.item(i, 0).text()))
            for j, header in enumerate(twoda.get_headers()):
                twoda.set_cell(i, header, self.model.item(i, j+1).text())

        print(self._restype)
        data = bytearray()
        write_2da(twoda, data, self._restype)
        return data

    def new(self) -> None:
        super().new()

        self.model.clear()
        self.model.setRowCount(0)

    def doFilter(self, text: str) -> None:
        self.proxyModel.setFilterFixedString(text)

    def toggleFilter(self) -> None:
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
            index = self.proxyModel.mapToSource(index)

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

        topLeftIndex = self.proxyModel.mapToSource(self.ui.twodaTable.selectedIndexes()[0])
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

    def insertRow(self) -> None:
        """
        Inserts a new row at the end of the table.
        """
        rowIndex = self.model.rowCount()
        self.model.appendRow([QStandardItem("") for i in range(self.model.columnCount())])
        self.model.setItem(rowIndex, 0, QStandardItem(str(rowIndex)))
        font = self.model.item(rowIndex, 0).font()
        font.setBold(True)
        self.model.item(rowIndex, 0).setFont(font)
        self.model.item(rowIndex, 0).setBackground(self.palette().midlight())
        self.model.setVerticalHeaderItem(rowIndex, QStandardItem("   "))

    def removeSelectedRows(self) -> None:
        """
        Removes the rows the user has selected.
        """
        for i in range(self.model.rowCount())[::-1]:
            for j in range(self.model.columnCount()):
                if self.ui.twodaTable.selectionModel().isSelected(self.model.index(i, j)):
                    self.model.removeRow(i)
                    continue

    def redoRowLabels(self) -> None:
        """
        Iterates through every row setting the row label to match the row index.
        """
        for i in range(self.model.rowCount()):
            self.model.item(i, 0).setText(str(i))


class SortFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent):
        super().__init__(parent)
        self._filterString: str = ""

    def filterAcceptsRow(self, sourceRow, sourceParent):
        pattern = self.filterRegExp().pattern().lower()
        if self.filterRegExp().pattern() == "":
            return True
        for i in range(self.sourceModel().columnCount()):
            index = self.sourceModel().index(sourceRow, i, sourceParent)
            if self.sourceModel().data(index) is not None and pattern in self.sourceModel().data(index).lower():
                return True
        return False
