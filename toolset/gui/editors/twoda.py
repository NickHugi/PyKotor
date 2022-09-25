from __future__ import annotations

from enum import IntEnum
from typing import Optional, Tuple

import pyperclip as pyperclip
from PyQt5.QtCore import QSortFilterProxyModel
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QMessageBox, QWidget, QAction
from pykotor.resource.formats.twoda import TwoDA, write_2da, read_2da
from pykotor.resource.type import ResourceType

from data.installation import HTInstallation
from gui.editor import Editor


class TwoDAEditor(Editor):
    def __init__(self, parent: Optional[QWidget], installation: Optional[HTInstallation] = None):
        supported = [ResourceType.TwoDA, ResourceType.TwoDA_CSV, ResourceType.TwoDA_JSON]
        super().__init__(parent, "2DA Editor", "none", supported, supported, installation)
        self.resize(400, 250)

        from toolset.uic.editors.twoda import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()

        self.ui.filterBox.setVisible(False)

        self.model = QStandardItemModel(self)
        self.proxyModel = SortFilterProxyModel(self)
        self.proxyModel.setSourceModel(self.model)

        self.verticalHeaderOption: VerticalHeaderOption = VerticalHeaderOption.NONE
        self.verticalHeaderColumn: str = ""

        self.model.itemChanged.connect(self.resetVerticalHeaders)

        self.new()

    def _setupSignals(self) -> None:
        self.ui.filterEdit.textEdited.connect(self.doFilter)
        self.ui.actionToggleFilter.triggered.connect(self.toggleFilter)
        self.ui.actionCopy.triggered.connect(self.copySelection)
        self.ui.actionPaste.triggered.connect(self.pasteSelection)

        self.ui.actionInsertRow.triggered.connect(self.insertRow)
        self.ui.actionDuplicateRow.triggered.connect(self.duplicateRow)
        self.ui.actionRemoveRows.triggered.connect(self.removeSelectedRows)
        self.ui.actionRedoRowLabels.triggered.connect(self.redoRowLabels)

    def load(self, filepath: str, resref: str, restype: ResourceType, data: bytes) -> None:
        super().load(filepath, resref, restype, data)
        self.model = QStandardItemModel(self)
        self.proxyModel = SortFilterProxyModel(self)

        try:
            twoda = read_2da(data)

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

            self.resetVerticalHeaders()
            self.ui.twodaTable.setModel(self.proxyModel)

            # region Menu: Set Row Header
            self.ui.menuSetRowHeader.clear()

            action = QAction("None", self)
            action.triggered.connect(lambda: self.setVerticalHeaderOption(VerticalHeaderOption.NONE))
            self.ui.menuSetRowHeader.addAction(action)

            action = QAction("Row Index", self)
            action.triggered.connect(lambda: self.setVerticalHeaderOption(VerticalHeaderOption.ROW_INDEX))
            self.ui.menuSetRowHeader.addAction(action)

            action = QAction("Row Label", self)
            action.triggered.connect(lambda: self.setVerticalHeaderOption(VerticalHeaderOption.ROW_LABEL))
            self.ui.menuSetRowHeader.addAction(action)

            self.ui.menuSetRowHeader.addSeparator()

            for header in headers[1:]:
                action = QAction(header, self)
                action.triggered.connect(lambda _, header=header: self.setVerticalHeaderOption(VerticalHeaderOption.CELL_VALUE, header))
                self.ui.menuSetRowHeader.addAction(action)
            # endregion

            self.proxyModel.setSourceModel(self.model)
            for i in range(twoda.get_height()):
                self.ui.twodaTable.resizeColumnToContents(i)
        except ValueError as e:
            QMessageBox(QMessageBox.Critical, "Failed to load file.", "Failed to open or load file data.").exec_()
            self.proxyModel.setSourceModel(self.model)
            self.new()

    def build(self) -> Tuple[bytes, bytes]:
        twoda = TwoDA()

        for i in range(self.model.columnCount())[1:]:
            twoda.add_column(self.model.horizontalHeaderItem(i).text())

        for i in range(self.model.rowCount()):
            twoda.add_row()
            twoda.set_label(i, self.model.item(i, 0).text())
            for j, header in enumerate(twoda.get_headers()):
                twoda.set_cell(i, header, self.model.item(i, j+1).text())

        data = bytearray()
        write_2da(twoda, data, self._restype)
        return data, b''

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
        self.resetVerticalHeaders()

    def duplicateRow(self) -> None:
        """
        Inserts a new row, copying values of the selected row, at the end of the table.
        """
        if self.ui.twodaTable.selectedIndexes():
            copyRow = self.ui.twodaTable.selectedIndexes()[0].row()

            rowIndex = self.model.rowCount()
            self.model.appendRow([QStandardItem(self.model.item(copyRow, i)) for i in range(self.model.columnCount())])
            self.model.setItem(rowIndex, 0, QStandardItem(str(rowIndex)))
            font = self.model.item(rowIndex, 0).font()
            font.setBold(True)
            self.model.item(rowIndex, 0).setFont(font)
            self.model.item(rowIndex, 0).setBackground(self.palette().midlight())
            self.resetVerticalHeaders()

    def removeSelectedRows(self) -> None:
        """
        Removes the rows the user has selected.
        """
        rows = set()

        for index in self.ui.twodaTable.selectedIndexes():
            rows.add(index.row())

        for row in sorted(rows, reverse=True):
            self.model.removeRow(row)

    def redoRowLabels(self) -> None:
        """
        Iterates through every row setting the row label to match the row index.
        """
        for i in range(self.model.rowCount()):
            self.model.item(i, 0).setText(str(i))

    def setVerticalHeaderOption(self, option: VerticalHeaderOption, column: Optional[str] = None) -> None:
        self.verticalHeaderOption = option
        self.verticalHeaderColumn = column
        self.resetVerticalHeaders()

    def resetVerticalHeaders(self) -> None:
        self.ui.twodaTable.verticalHeader().setStyleSheet("")
        headers = []

        if self.verticalHeaderOption == VerticalHeaderOption.ROW_INDEX:
            headers = [str(i) for i in range(self.model.rowCount())]
        elif self.verticalHeaderOption == VerticalHeaderOption.ROW_LABEL:
            headers = [self.model.item(i, 0).text() for i in range(self.model.rowCount())]
        elif self.verticalHeaderOption == VerticalHeaderOption.CELL_VALUE:
            columnIndex = 0
            for i in range(self.model.columnCount()):
                if self.model.horizontalHeaderItem(i).text() == self.verticalHeaderColumn:
                    columnIndex = i
            headers = [self.model.item(i, columnIndex).text() for i in range(self.model.rowCount())]
        elif self.verticalHeaderOption == VerticalHeaderOption.NONE:
            self.ui.twodaTable.verticalHeader().setStyleSheet("QHeaderView::section { color: rgba(0, 0, 0, 0.0); }"
                                                              "QHeaderView::section:checked { color: #000000; }")
            headers = ["⯈" for _ in range(self.model.rowCount())]

        for i in range(self.model.rowCount()):
            self.model.setVerticalHeaderItem(i, QStandardItem(headers[i]))


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


class VerticalHeaderOption(IntEnum):
    ROW_INDEX = 0
    ROW_LABEL = 1
    CELL_VALUE = 2
    NONE = 3
