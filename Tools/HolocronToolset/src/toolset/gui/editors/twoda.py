from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

import pyperclip

from qtpy.QtCore import QSortFilterProxyModel
from qtpy.QtGui import QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QAction, QMessageBox

from pykotor.resource.formats.twoda import TwoDA, read_2da, write_2da
from pykotor.resource.type import ResourceType
from toolset.gui.editor import Editor
from utility.error_handling import assert_with_variable_trace, universal_simplify_exception

if TYPE_CHECKING:
    import os

    from qtpy.QtWidgets import QWidget

    from toolset.data.installation import HTInstallation


class TwoDAEditor(Editor):
    def __init__(self, parent: QWidget | None, installation: HTInstallation | None = None):
        """Initializes the 2DA editor.

        Args:
        ----
            parent: QWidget: The parent widget
            installation: HTInstallation: The installation

        Processing Logic:
        ----------------
            - Sets supported resource types
            - Initializes UI elements
            - Connects model change signals
            - Sets default empty model.
        """
        supported: list[ResourceType] = [ResourceType.TwoDA, ResourceType.TwoDA_CSV, ResourceType.TwoDA_JSON]
        super().__init__(parent, "2DA Editor", "none", supported, supported, installation)
        self.resize(400, 250)

        from toolset.uic.pyqt5.editors.twoda import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
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

    def _setupSignals(self):
        """Set up signal connections for UI actions and edits.

        Args:
        ----
            self: The class instance.

        Returns:
        -------
            None: No return value.

        Processing Logic:
        ----------------
            - Connect textEdited signal from filter edit to doFilter slot
            - Connect triggered signal from toggle filter action to toggleFilter slot
            - Connect triggered signal from copy action to copySelection slot
            - Connect triggered signal from paste action to pasteSelection slot
            - Connect triggered signal from insert row action to insertRow slot
            - Connect triggered signal from duplicate row action to duplicateRow slot
            - Connect triggered signal from remove rows action to removeSelectedRows slot
            - Connect triggered signal from redo row labels action to redoRowLabels slot
        """
        self.ui.filterEdit.textEdited.connect(self.doFilter)
        self.ui.actionToggleFilter.triggered.connect(self.toggleFilter)
        self.ui.actionCopy.triggered.connect(self.copySelection)
        self.ui.actionPaste.triggered.connect(self.pasteSelection)

        self.ui.actionInsertRow.triggered.connect(self.insertRow)
        self.ui.actionDuplicateRow.triggered.connect(self.duplicateRow)
        self.ui.actionRemoveRows.triggered.connect(self.removeSelectedRows)
        self.ui.actionRedoRowLabels.triggered.connect(self.redoRowLabels)

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes):
        """Loads data from a file into the model.

        Args:
        ----
            filepath: The path to the file to load from.
            resref: The resource reference.
            restype: The resource type.
            data: The raw file data.

        Processing Logic:
        ----------------
            - Parses the raw file data and populates the model
            - Sets up a proxy model for sorting and filtering
            - Catches any errors during loading and displays a message
            - Sets the proxy model as the view model if loading fails
            - Resets to a new empty state if loading fails
        """
        super().load(filepath, resref, restype, data)
        self.model = QStandardItemModel(self)
        self.proxyModel = SortFilterProxyModel(self)

        try:
            self._load_main(data)
        except ValueError as e:
            error_msg = str(universal_simplify_exception(e)).replace("\n", "<br>")
            QMessageBox(QMessageBox.Critical, "Failed to load file.", f"Failed to open or load file data.<br>{error_msg}").exec_()
            self.proxyModel.setSourceModel(self.model)
            self.new()

    def _load_main(self, data: bytes):
        """Loads data from a 2DA file into the main table.

        Args:
        ----
            data: The 2DA data to load

        Processing Logic:
        ----------------
            1. Reads the 2DA data
            2. Sets up the model with headers
            3. Loops through rows and inserts data
            4. Configures vertical header menu
            5. Sets up sorting proxy model.
        """
        twoda: TwoDA = read_2da(data)

        headers: list[str] = ["", *list(twoda.get_headers())]
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

    def build(self) -> tuple[bytes, bytes]:
        """Builds a 2D array from a table model.

        Args:
        ----
            self: The object instance
            model: The table model to convert

        Returns:
        -------
            tuple[bytes, bytes]: A tuple containing the 2DA data and an empty string

        Processing Logic:
        ----------------
            - Initialize an empty TwoDA object
            - Add column headers from the table model's horizontal header
            - Add a row for each row in the table model
            - Set the row label and cell values from the corresponding items in the table model
            - Serialize the TwoDA to a byte array
            - Return the byte array and an empty string.
        """
        twoda = TwoDA()

        for i in range(self.model.columnCount())[1:]:
            twoda.add_column(self.model.horizontalHeaderItem(i).text())

        for i in range(self.model.rowCount()):
            twoda.add_row()
            twoda.set_label(i, self.model.item(i, 0).text())
            for j, header in enumerate(twoda.get_headers()):
                twoda.set_cell(i, header, self.model.item(i, j + 1).text())

        data = bytearray()
        assert self._restype, assert_with_variable_trace(bool(self._restype), "self._restype must be valid.")
        write_2da(twoda, data, self._restype)
        return data, b""

    def new(self):
        super().new()

        self.model.clear()
        self.model.setRowCount(0)

    def doFilter(self, text: str):
        self.proxyModel.setFilterFixedString(text)

    def toggleFilter(self):
        visible: bool = not self.ui.filterBox.isVisible()
        self.ui.filterBox.setVisible(visible)
        if visible:
            self.doFilter(self.ui.filterEdit.text())
        else:
            self.doFilter("")

    def copySelection(self):
        """Copies the selected cells to the clipboard.

        Args:
        ----
            self: The object instance.

        Processing Logic:
        ----------------
            - Gets the top, bottom, left, and right indices of the selected cells.
            - Loops through the selected indices and maps them to the source model.
            - Updates the top, bottom, left, and right indices.
            - Loops through the indices range and builds a string with the cell texts separated by tabs.
            - Copies the string to the clipboard.
        """
        top = self.model.rowCount()
        bottom = -1
        left = self.model.columnCount()
        right = -1

        for index in self.ui.twodaTable.selectedIndexes():
            mapped_index = self.proxyModel.mapToSource(index)

            top = min([top, mapped_index.row()])
            bottom = max([bottom, mapped_index.row()])
            left = min([left, mapped_index.column()])
            right = max([right, mapped_index.column()])

        clipboard: str = ""
        for j in range(top, bottom + 1):
            for i in range(left, right + 1):
                clipboard += self.model.item(j, i).text()
                if i != right:
                    clipboard += "\t"
            if j != bottom:
                clipboard += "\n"

        pyperclip.copy(clipboard)

    def pasteSelection(self):
        """Pastes the clipboard contents into the selected table cells.

        Args:
        ----
            self: The object instance

        Processing Logic:
        ----------------
            - Splits the clipboard contents into rows separated by newlines
            - Gets the top left selected cell index and item
            - Loops through each row
                - Loops through each cell in the row separated by tabs
                - Sets the text of the model item at the current row and column
                - Increments the column
                - Resets column to the left column after each row
                - Increments the row.
        """
        rows: list[str] = pyperclip.paste().split("\n")

        topLeftIndex = self.proxyModel.mapToSource(self.ui.twodaTable.selectedIndexes()[0])
        topLeftItem: QStandardItem | None = self.model.itemFromIndex(topLeftIndex)

        _top, left = y, x = topLeftItem.row(), topLeftItem.column()

        for row in rows:
            for cell in row.split("\t"):
                item: QStandardItem | None = self.model.item(y, x)
                if item:
                    item.setText(cell)
                x += 1
            x = left
            y += 1

    def insertRow(self):
        """Inserts a new row at the end of the table.

        Args:
        ----
            self: The table view object.

        Processing Logic:
        ----------------
            - Gets the current row count from the model
            - Appends a new empty row to the model
            - Sets the item in the first column to the row index
            - Makes the row index bold and changes its background color
            - Resets the vertical header labels.
        """
        rowIndex: int = self.model.rowCount()
        self.model.appendRow([QStandardItem("") for _ in range(self.model.columnCount())])
        self.model.setItem(rowIndex, 0, QStandardItem(str(rowIndex)))
        font = self.model.item(rowIndex, 0).font()
        font.setBold(True)
        self.model.item(rowIndex, 0).setFont(font)
        self.model.item(rowIndex, 0).setBackground(self.palette().midlight())
        self.resetVerticalHeaders()

    def duplicateRow(self):
        """Duplicates the selected row in the table.

        Inserts a new row, copying values of the selected row, at the end of the table.

        Args:
        ----
            self: The class instance.

        Returns:
        -------
            None: Does not return anything.

        Processing Logic:
        ----------------
            - It checks if a row is selected in the table.
            - Gets the index of the selected row.
            - Increases the row count of the model by 1.
            - Appends a new row with the items copied from the selected row.
            - Sets the item of the first column of new row to the row index in bold font and changed background.
            - Resets the vertical headers of the table.
        """
        if self.ui.twodaTable.selectedIndexes():
            copyRow: int = self.ui.twodaTable.selectedIndexes()[0].row()

            rowIndex: int = self.model.rowCount()
            self.model.appendRow([QStandardItem(self.model.item(copyRow, i)) for i in range(self.model.columnCount())])
            self.model.setItem(rowIndex, 0, QStandardItem(str(rowIndex)))
            font = self.model.item(rowIndex, 0).font()
            font.setBold(True)
            self.model.item(rowIndex, 0).setFont(font)
            self.model.item(rowIndex, 0).setBackground(self.palette().midlight())
            self.resetVerticalHeaders()

    def removeSelectedRows(self):
        """Removes the rows the user has selected."""
        rows: set[int] = {index.row() for index in self.ui.twodaTable.selectedIndexes()}
        for row in sorted(rows, reverse=True):
            self.model.removeRow(row)

    def redoRowLabels(self):
        """Iterates through every row setting the row label to match the row index."""
        for i in range(self.model.rowCount()):
            self.model.item(i, 0).setText(str(i))

    def setVerticalHeaderOption(self, option: VerticalHeaderOption, column: str | None = None):
        self.verticalHeaderOption = option
        assert_with_variable_trace(column is not None, "column cannot be None")
        self.verticalHeaderColumn = column or ""
        self.resetVerticalHeaders()

    def resetVerticalHeaders(self):
        """Resets the vertical headers of the two-dimensional table.

        Args:
        ----
            self: The table widget object.

        Returns:
        -------
            None: No value is returned.

        Processing Logic:
        ----------------
            - Clear existing vertical header styling
            - Determine header values based on vertical header option
            - Populate headers list with appropriate values
            - Set vertical header item for each row using headers list values
        """
        self.ui.twodaTable.verticalHeader().setStyleSheet("")
        headers: list[str] = []

        if self.verticalHeaderOption == VerticalHeaderOption.ROW_INDEX:
            headers = [str(i) for i in range(self.model.rowCount())]
        elif self.verticalHeaderOption == VerticalHeaderOption.ROW_LABEL:
            headers = [self.model.item(i, 0).text() for i in range(self.model.rowCount())]
        elif self.verticalHeaderOption == VerticalHeaderOption.CELL_VALUE:
            columnIndex: int = 0
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

    def filterAcceptsRow(self, sourceRow, sourceParent) -> bool:
        """Filters rows based on regular expression pattern match.

        Args:
        ----
            sourceRow: Row number to check
            sourceParent: Parent model of the row

        Returns:
        -------
            True: If row matches filter pattern
            False: If row does not match filter pattern

        Processing Logic:
        ----------------
            - Get regular expression pattern from filter
            - If pattern is empty, always return True
            - Iterate through each column of the row
            - Check if cell data contains pattern using lower case comparison
            - If any cell matches, return True
        - If no cells match, return False
        """
        pattern: str = self.filterRegExp().pattern().lower()
        if not self.filterRegExp().pattern():
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
