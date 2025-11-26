from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

import qtpy

from qtpy.QtCore import QSortFilterProxyModel, Qt
from qtpy.QtGui import QStandardItem, QStandardItemModel
from qtpy.QtWidgets import (
    QAction,  # pyright: ignore[reportPrivateImportUsage]
    QApplication,
    QMessageBox,
)

from pykotor.resource.formats.twoda import TwoDA, read_2da, write_2da
from pykotor.resource.type import ResourceType
from toolset.gui.editor import Editor
from toolset.gui.widgets.settings.installations import GlobalSettings
from utility.error_handling import assert_with_variable_trace, universal_simplify_exception

if TYPE_CHECKING:
    import os

    from qtpy.QtCore import QModelIndex
    from qtpy.QtWidgets import QHeaderView, QWidget

    from toolset.data.installation import HTInstallation


class TwoDAEditor(Editor):
    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation | None = None,
    ):
        supported: list[ResourceType] = [ResourceType.TwoDA, ResourceType.TwoDA_CSV, ResourceType.TwoDA_JSON]
        super().__init__(parent, "2DA Editor", "none", supported, supported, installation)
        self.resize(400, 250)

        from toolset.uic.qtpy.editors.twoda import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_menus()
        self._add_help_action()
        self._setup_signals()

        self.ui.filterBox.setVisible(False)

        self.source_model: QStandardItemModel = QStandardItemModel(self)
        self.proxy_model: SortFilterProxyModel = SortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.source_model)

        self.vertical_header_option: VerticalHeaderOption = VerticalHeaderOption.NONE
        self.vertical_header_column: str = ""
        vert_header: QHeaderView | None = self.ui.twodaTable.verticalHeader()
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)
        self.source_model.itemChanged.connect(self.reset_vertical_headers)

        self.new()
        if vert_header is not None and "(Dark)" in GlobalSettings().selectedTheme:
            vert_header.setStyleSheet("""
                QHeaderView::section {
                    color: rgba(255, 255, 255, 0.0);  /* Transparent text */
                    background-color: #333333;  /* Dark background */
                }
                QHeaderView::section:checked {
                    color: #FFFFFF;  /* White text for checked sections */
                    background-color: #444444;  /* Slightly lighter background for checked sections */
                }
                QHeaderView::section:hover {
                    color: #FFFFFF;  /* White text on hover */
                    background-color: #555555;  /* Even lighter background on hover */
                }
            """)
            self.ui.twodaTable.setStyleSheet("""
                QHeaderView::section {
                    background-color: #444444;  /* Dark background for header */
                    color: #FFFFFF;  /* White text for header */
                    padding: 4px;
                    border: 1px solid #333333;
                }
                QHeaderView::section:checked {
                    background-color: #555555;  /* Slightly lighter background for checked header */
                    color: #FFFFFF;  /* White text for checked header */
                }
                QHeaderView::section:hover {
                    background-color: #555555;  /* Lighter background for hovered header */
                    color: #FFFFFF;  /* White text for hovered header */
                }
                QTableView {
                    background-color: #333333;  /* Dark background for table */
                    alternate-background-color: #3c3c3c;  /* Slightly lighter background for alternating rows */
                    color: #FFFFFF;  /* White text for table */
                    gridline-color: #444444;  /* Dark grid lines */
                    selection-background-color: #555555;  /* Slightly lighter background for selected items */
                    selection-color: #FFFFFF;  /* White text for selected items */
                }
                QTableView::item {
                    background-color: #333333;  /* Dark background for items */
                    color: #FFFFFF;  /* White text for items */
                }
                QTableView::item:selected {
                    background-color: #555555;  /* Slightly lighter background for selected items */
                    color: #FFFFFF;  /* White text for selected items */
                }
                QTableCornerButton::section {
                    background-color: #444444;  /* Dark background for corner button */
                    border: 1px solid #333333;
                }
            """)

    def _setup_signals(self):
        self.ui.filterEdit.textEdited.connect(self.do_filter)
        self.ui.actionToggleFilter.triggered.connect(self.toggle_filter)
        self.ui.actionCopy.triggered.connect(self.copy_selection)
        self.ui.actionPaste.triggered.connect(self.paste_selection)

        self.ui.actionInsertRow.triggered.connect(self.insert_row)
        self.ui.actionDuplicateRow.triggered.connect(self.duplicate_row)
        self.ui.actionRemoveRows.triggered.connect(self.remove_selected_rows)
        self.ui.actionRedoRowLabels.triggered.connect(self.redo_row_labels)

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        super().load(filepath, resref, restype, data)

        # FIXME(th3w1zard1): Why set this here when it's already set in __init__...?
        self.source_model = QStandardItemModel(self)
        self.proxy_model = SortFilterProxyModel(self)

        try:
            self._load_main(data)
        except ValueError as e:
            error_msg = str(universal_simplify_exception(e)).replace("\n", "<br>")
            from toolset.gui.common.localization import translate as tr, trf
            QMessageBox(QMessageBox.Icon.Critical, tr("Failed to load file."), trf("Failed to open or load file data.<br>{error}", error=error_msg)).exec()
            self.proxy_model.setSourceModel(self.source_model)
            self.new()

    def _load_main(
        self,
        data: bytes,
    ):
        twoda: TwoDA = read_2da(data)
        headers: list[str] = ["", *twoda.get_headers()]
        self.source_model.setColumnCount(len(headers))
        self.source_model.setHorizontalHeaderLabels(headers)

        # Disconnect the model to improve performance during updates (especially for appearance.2da)
        self.ui.twodaTable.setModel(None)  # type: ignore[arg-type]

        items: list[list[QStandardItem]] = []
        for i, row in enumerate(twoda):
            label_item = QStandardItem(str(twoda.get_label(i)))
            font = label_item.font()
            font.setBold(True)
            label_item.setFont(font)
            label_item.setBackground(self.palette().midlight())
            row_items = [label_item]
            row_items.extend(QStandardItem(row.get_string(header)) for header in headers[1:])
            items.append(row_items)

        for i, row_items in enumerate(items):
            self.source_model.insertRow(i, row_items)

        self.reset_vertical_headers()
        self.proxy_model.setSourceModel(self.source_model)
        self.ui.twodaTable.setModel(self.proxy_model)  # type: ignore[arg-type]
        self._reconstruct_menu(headers)

    def _reconstruct_menu(
        self,
        headers: list[str],
    ):
        self.ui.menuSetRowHeader.clear()
        action = QAction("None", self)
        action.triggered.connect(lambda: self.set_vertical_header_option(VerticalHeaderOption.NONE))
        self.ui.menuSetRowHeader.addAction(action)  # type: ignore[arg-type]

        action = QAction("Row Index", self)
        action.triggered.connect(lambda: self.set_vertical_header_option(VerticalHeaderOption.ROW_INDEX))
        self.ui.menuSetRowHeader.addAction(action)  # type: ignore[arg-type]

        action = QAction("Row Label", self)
        action.triggered.connect(lambda: self.set_vertical_header_option(VerticalHeaderOption.ROW_LABEL))
        self.ui.menuSetRowHeader.addAction(action)  # type: ignore[arg-type]
        self.ui.menuSetRowHeader.addSeparator()
        for header in headers[1:]:
            action = QAction(header, self)
            action.triggered.connect(lambda _=None, h=header: self.set_vertical_header_option(VerticalHeaderOption.CELL_VALUE, h))
            self.ui.menuSetRowHeader.addAction(action)  # type: ignore[arg-type]

    def build(self) -> tuple[bytes, bytes]:
        twoda = TwoDA()

        for i in range(self.source_model.columnCount())[1:]:
            twoda.add_column(self.source_model.horizontalHeaderItem(i).text())

        for i in range(self.source_model.rowCount()):
            twoda.add_row()
            twoda.set_label(i, self.source_model.item(i, 0).text())
            for j, header in enumerate(twoda.get_headers()):
                twoda.set_cell(i, header, self.source_model.item(i, j + 1).text())

        data = bytearray()
        assert self._restype, assert_with_variable_trace(bool(self._restype), "self._restype must be valid.")
        write_2da(twoda, data, self._restype)
        return bytes(data), b""

    def new(self):
        super().new()

        self.source_model.clear()
        self.source_model.setRowCount(0)

    def jump_to_row(
        self,
        row: int,
    ):
        if row < 0 or row >= self.source_model.rowCount():
            from toolset.gui.common.localization import translate as tr, trf
            QMessageBox.warning(self, tr("Invalid Row"), trf("Row {row} is out of range.", row=row))
            return
        index: QModelIndex = self.proxy_model.mapFromSource(self.source_model.index(row, 0))
        self.ui.twodaTable.setCurrentIndex(index)
        self.ui.twodaTable.scrollTo(index, self.ui.twodaTable.ScrollHint.EnsureVisible)  # type: ignore[arg-type]
        self.ui.twodaTable.selectRow(index.row())

    def do_filter(
        self,
        text: str,
    ):
        self.proxy_model.setFilterFixedString(text)

    def toggle_filter(self):
        visible: bool = not self.ui.filterBox.isVisible()
        self.ui.filterBox.setVisible(visible)
        if visible:
            self.do_filter(self.ui.filterEdit.text())
            self.ui.filterEdit.setFocus()
            self.ui.filterEdit.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # type: ignore[arg-type]
        else:
            self.do_filter("")

    def copy_selection(self):
        top = self.source_model.rowCount()
        bottom = -1
        left = self.source_model.columnCount()
        right = -1

        for index in self.ui.twodaTable.selectedIndexes():
            if not index.isValid():
                continue
            mapped_index = self.proxy_model.mapToSource(index)  # type: ignore[arg-type]

            top = min([top, mapped_index.row()])
            bottom = max([bottom, mapped_index.row()])
            left = min([left, mapped_index.column()])
            right = max([right, mapped_index.column()])

        clipboard: str = ""
        for j in range(top, bottom + 1):
            for i in range(left, right + 1):
                clipboard += self.source_model.item(j, i).text()
                if i != right:
                    clipboard += "\t"
            if j != bottom:
                clipboard += "\n"

        QApplication.clipboard().setText(clipboard)

    def paste_selection(self):
        rows: list[str] = QApplication.clipboard().text().split("\n")
        selected_indexes = self.ui.twodaTable.selectedIndexes()
        if not selected_indexes:
            return
        selected_index = self.ui.twodaTable.selectedIndexes()[0]
        if not selected_index.isValid():
            return

        top_left_index = self.proxy_model.mapToSource(selected_index)  # type: ignore[arg-type]
        top_left_item: QStandardItem | None = self.source_model.itemFromIndex(top_left_index)

        _top, left = y, x = top_left_item.row(), top_left_item.column()

        for row in rows:
            for cell in row.split("\t"):
                item: QStandardItem | None = self.source_model.item(y, x)
                if item:
                    item.setText(cell)
                x += 1
            x = left
            y += 1

    def insert_row(self):
        row_index: int = self.source_model.rowCount()
        self.source_model.appendRow([QStandardItem("") for _ in range(self.source_model.columnCount())])
        self.set_item_display_data(row_index)

    def duplicate_row(self):
        if self.ui.twodaTable.selectedIndexes():
            copy_row: int = self.ui.twodaTable.selectedIndexes()[0].row()

            row_index: int = self.source_model.rowCount()
            self.source_model.appendRow([QStandardItem(self.source_model.item(copy_row, i)) for i in range(self.source_model.columnCount())])
            self.set_item_display_data(row_index)

    def set_item_display_data(self, rowIndex: int):
        self.source_model.setItem(rowIndex, 0, QStandardItem(str(rowIndex)))
        font = self.source_model.item(rowIndex, 0).font()
        font.setBold(True)
        self.source_model.item(rowIndex, 0).setFont(font)
        self.source_model.item(rowIndex, 0).setBackground(self.palette().midlight())
        self.reset_vertical_headers()

    def remove_selected_rows(self):
        """Removes the rows the user has selected."""
        rows: set[int] = {index.row() for index in self.ui.twodaTable.selectedIndexes()}
        for row in sorted(rows, reverse=True):
            self.source_model.removeRow(row)

    def redo_row_labels(self):
        """Iterates through every row setting the row label to match the row index."""
        for i in range(self.source_model.rowCount()):
            self.source_model.item(i, 0).setText(str(i))

    def set_vertical_header_option(
        self,
        option: VerticalHeaderOption,
        column: str | None = None,
    ):
        self.vertical_header_option = option
        self.vertical_header_column = column or ""
        self.reset_vertical_headers()

    def reset_vertical_headers(self):
        vertical_header = self.ui.twodaTable.verticalHeader()
        assert vertical_header is not None
        if GlobalSettings().selectedTheme in ("Native", "Fusion (Light)"):
            vertical_header.setStyleSheet("")
        headers: list[str] = []

        if self.vertical_header_option == VerticalHeaderOption.ROW_INDEX:
            headers = [str(i) for i in range(self.source_model.rowCount())]
        elif self.vertical_header_option == VerticalHeaderOption.ROW_LABEL:
            headers = [self.source_model.item(i, 0).text() for i in range(self.source_model.rowCount())]
        elif self.vertical_header_option == VerticalHeaderOption.CELL_VALUE:
            col_index: int = 0
            for i in range(self.source_model.columnCount()):
                if self.source_model.horizontalHeaderItem(i).text() == self.vertical_header_column:
                    col_index = i
            headers = [self.source_model.item(i, col_index).text() for i in range(self.source_model.rowCount())]
        elif self.vertical_header_option == VerticalHeaderOption.NONE:
            if GlobalSettings().selectedTheme in ("Native", "Fusion (Light)"):
                vertical_header.setStyleSheet("QHeaderView::section { color: rgba(0, 0, 0, 0.0); }" "QHeaderView::section:checked { color: #000000; }")
            elif GlobalSettings().selectedTheme == "Fusion (Dark)":
                vertical_header.setStyleSheet("""
                    QHeaderView::section {
                        color: rgba(255, 255, 255, 0.0);  /* Transparent text */
                        background-color: #333333;  /* Dark background */
                    }
                    QHeaderView::section:checked {
                        color: #FFFFFF;  /* White text for checked sections */
                        background-color: #444444;  /* Slightly lighter background for checked sections */
                    }
                    QHeaderView::section:hover {
                        color: #FFFFFF;  /* White text on hover */
                        background-color: #555555;  /* Even lighter background on hover */
                    }
                """)
                self.ui.twodaTable.setStyleSheet("""
                    QHeaderView::section {
                        background-color: #444444;  /* Dark background for header */
                        color: #FFFFFF;  /* White text for header */
                        padding: 4px;
                        border: 1px solid #333333;
                    }
                    QHeaderView::section:checked {
                        background-color: #555555;  /* Slightly lighter background for checked header */
                        color: #FFFFFF;  /* White text for checked header */
                    }
                    QHeaderView::section:hover {
                        background-color: #555555;  /* Lighter background for hovered header */
                        color: #FFFFFF;  /* White text for hovered header */
                    }
                    QTableView {
                        background-color: #333333;  /* Dark background for table */
                        alternate-background-color: #3c3c3c;  /* Slightly lighter background for alternating rows */
                        color: #FFFFFF;  /* White text for table */
                        gridline-color: #444444;  /* Dark grid lines */
                        selection-background-color: #555555;  /* Slightly lighter background for selected items */
                        selection-color: #FFFFFF;  /* White text for selected items */
                    }
                    QTableView::item {
                        background-color: #333333;  /* Dark background for items */
                        color: #FFFFFF;  /* White text for items */
                    }
                    QTableView::item:selected {
                        background-color: #555555;  /* Slightly lighter background for selected items */
                        color: #FFFFFF;  /* White text for selected items */
                    }
                    QTableCornerButton::section {
                        background-color: #444444;  /* Dark background for corner button */
                        border: 1px solid #333333;
                    }
                """)
            headers = ["⯈" for _ in range(self.source_model.rowCount())]

        for i in range(self.source_model.rowCount()):
            self.source_model.setVerticalHeaderItem(i, QStandardItem(headers[i]))


class SortFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent):
        super().__init__(parent)
        self._filterString: str = ""

    def filterAcceptsRow(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        source_row: int,
        source_parent: QModelIndex,
    ) -> bool:
        if qtpy.QT5:
            pattern = self.filterRegExp().pattern()
        else:
            pattern = self.filterRegularExpression().pattern()

        if not pattern:
            return True
        case_insens_pattern = pattern.lower()
        src_model = self.sourceModel()
        for i in range(src_model.columnCount()):
            index = src_model.index(source_row, i, source_parent)
            if not index.isValid():
                continue
            data: str = src_model.data(index)
            if data is None:
                continue
            if case_insens_pattern in data.lower():
                return True
        return False


class VerticalHeaderOption(IntEnum):
    ROW_INDEX = 0
    ROW_LABEL = 1
    CELL_VALUE = 2
    NONE = 3
