from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import Qt
from qtpy.QtGui import QFontMetrics
from qtpy.QtWidgets import (
    QAction,  # pyright: ignore[reportPrivateImportUsage]
    QApplication,
    QMenu,
    QTableWidgetItem,
)

from pykotor.resource.formats.ltr.ltr_auto import bytes_ltr, read_ltr
from pykotor.resource.formats.ltr.ltr_data import LTR
from pykotor.resource.type import ResourceType
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    import os

    from qtpy.QtCore import QPoint
    from qtpy.QtWidgets import QTableWidget, QWidget

    from toolset.data.installation import HTInstallation


class LTREditor(Editor):
    def __init__(self, parent: QWidget | None, installation: HTInstallation | None = None):
        supported = [ResourceType.LTR]
        super().__init__(parent, "LTR Editor", "ltr", supported, supported, installation)
        self.resize(800, 600)

        from toolset.uic.qtpy.editors.ltr import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.tableSingles.setSortingEnabled(True)
        self.ui.tableDoubles.setSortingEnabled(True)
        self.ui.tableTriples.setSortingEnabled(True)
        self._setup_menus()
        self._add_help_action()
        self._setup_signals()
        self.auto_resize_enabled = True

        self.ltr = LTR()

        self.populateComboBoxes()
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)
        
        self.new()

    def _setup_signals(self):
        self.ui.buttonSetSingle.clicked.connect(self.setSingleCharacter)
        self.ui.buttonSetDouble.clicked.connect(self.setDoubleCharacter)
        self.ui.buttonSetTriple.clicked.connect(self.setTripleCharacter)
        self.ui.buttonGenerate.clicked.connect(self.generateName)
        self.ui.buttonAddSingle.clicked.connect(self.addSingleRow)
        self.ui.buttonRemoveSingle.clicked.connect(self.removeSingleRow)
        self.ui.buttonAddDouble.clicked.connect(self.addDoubleRow)
        self.ui.buttonRemoveDouble.clicked.connect(self.removeDoubleRow)
        self.ui.buttonAddTriple.clicked.connect(self.addTripleRow)
        self.ui.buttonRemoveTriple.clicked.connect(self.removeTripleRow)
        hor_header = self.ui.tableSingles.horizontalHeader()
        assert hor_header is not None
        hor_header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        hor_header.customContextMenuRequested.connect(self.show_header_context_menu)
        hor_header2 = self.ui.tableDoubles.horizontalHeader()
        assert hor_header2 is not None
        hor_header2.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        hor_header2.customContextMenuRequested.connect(self.show_header_context_menu)
        hor_header3 = self.ui.tableTriples.horizontalHeader()
        assert hor_header3 is not None
        hor_header3.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        hor_header3.customContextMenuRequested.connect(self.show_header_context_menu)

    def populateComboBoxes(self):
        char_set = LTR.CHARACTER_SET
        for char in char_set:
            self.ui.comboBoxSingleChar.addItem(char)
            self.ui.comboBoxDoubleChar.addItem(char)
            self.ui.comboBoxDoublePrevChar.addItem(char)
            self.ui.comboBoxTriplePrev1Char.addItem(char)
            self.ui.comboBoxTriplePrev2Char.addItem(char)
            self.ui.comboBoxTripleChar.addItem(char)

    def updateUIFromLTR(self):
        char_set = LTR.CHARACTER_SET
        self.ui.tableSingles.setRowCount(len(char_set))
        self.ui.tableDoubles.setRowCount(len(char_set)**2)
        self.ui.tableTriples.setRowCount(len(char_set)**2 * len(char_set))

        for i, char in enumerate(char_set):
            self.ui.tableSingles.setItem(i, 0, QTableWidgetItem(char))
            self.ui.tableSingles.setItem(i, 1, QTableWidgetItem(str(self.ltr._singles.get_start(char))))
            self.ui.tableSingles.setItem(i, 2, QTableWidgetItem(str(self.ltr._singles.get_middle(char))))
            self.ui.tableSingles.setItem(i, 3, QTableWidgetItem(str(self.ltr._singles.get_end(char))))

        index = 0
        for prev_char in char_set:
            for char in char_set:
                self.ui.tableDoubles.setItem(index, 0, QTableWidgetItem(prev_char))
                self.ui.tableDoubles.setItem(index, 1, QTableWidgetItem(char))
                self.ui.tableDoubles.setItem(index, 2, QTableWidgetItem(str(self.ltr._doubles[char_set.index(prev_char)].get_start(char))))
                self.ui.tableDoubles.setItem(index, 3, QTableWidgetItem(str(self.ltr._doubles[char_set.index(prev_char)].get_middle(char))))
                self.ui.tableDoubles.setItem(index, 4, QTableWidgetItem(str(self.ltr._doubles[char_set.index(prev_char)].get_end(char))))
                index += 1

        index = 0
        for prev2_char in char_set:
            for prev1_char in char_set:
                for char in char_set:
                    self.ui.tableTriples.setItem(index, 0, QTableWidgetItem(prev2_char))
                    self.ui.tableTriples.setItem(index, 1, QTableWidgetItem(prev1_char))
                    self.ui.tableTriples.setItem(index, 2, QTableWidgetItem(char))
                    self.ui.tableTriples.setItem(index, 3, QTableWidgetItem(str(self.ltr._triples[char_set.index(prev2_char)][char_set.index(prev1_char)].get_start(char))))
                    self.ui.tableTriples.setItem(index, 4, QTableWidgetItem(str(self.ltr._triples[char_set.index(prev2_char)][char_set.index(prev1_char)].get_middle(char))))
                    self.ui.tableTriples.setItem(index, 5, QTableWidgetItem(str(self.ltr._triples[char_set.index(prev2_char)][char_set.index(prev1_char)].get_end(char))))
                    index += 1

    def show_header_context_menu(self, position: QPoint):
        menu = QMenu()

        toggle_auto_fit_action = QAction("Auto-fit Columns", self)
        toggle_auto_fit_action.setCheckable(True)
        toggle_auto_fit_action.setChecked(self.auto_resize_enabled)
        toggle_auto_fit_action.triggered.connect(self.toggle_auto_fit_columns)
        menu.addAction(toggle_auto_fit_action)

        toggle_alternate_row_colors_action = QAction("Toggle Alternate Row Colors", self)
        toggle_alternate_row_colors_action.triggered.connect(self.toggle_alternate_row_colors)
        menu.addAction(toggle_alternate_row_colors_action)

        if self.ui.tableSingles.hasFocus():
            hor_header_single = self.ui.tableSingles.horizontalHeader()
            assert hor_header_single is not None
            menu.exec(hor_header_single.mapToGlobal(position))
        if self.ui.tableDoubles.hasFocus():
            hor_header_double = self.ui.tableDoubles.horizontalHeader()
            assert hor_header_double is not None
            menu.exec(hor_header_double.mapToGlobal(position))
        if self.ui.tableTriples.hasFocus():
            hor_header_triple = self.ui.tableTriples.horizontalHeader()
            assert hor_header_triple is not None
            menu.exec(hor_header_triple.mapToGlobal(position))

    def toggle_alternate_row_colors(self):
        for table in (self.ui.tableSingles, self.ui.tableDoubles, self.ui.tableTriples):
            if table.alternatingRowColors():
                table.setAlternatingRowColors(False)
            else:
                table.setAlternatingRowColors(True)

    def reset_column_widths(self):
        for table in (self.ui.tableSingles, self.ui.tableDoubles, self.ui.tableTriples):
            header = table.horizontalHeader()
            assert header is not None
            for col in range(header.count()):
                header.resizeSection(col, header.defaultSectionSize())

    def auto_fit_columns(self, table: QTableWidget):
        header = table.horizontalHeader()
        assert header is not None

        # Resize columns to contents
        table.resizeColumnsToContents()

        # Adjust each column's width to ensure the header text is fully visible
        font_metrics = QFontMetrics(QApplication.font())

        # Loop over each column and adjust based on header text width
        for col in range(header.count()):
            # Calculate the width required for the text in the header
            header_model = header.model()
            assert header_model is not None
            header_text = header_model.headerData(col, Qt.Orientation.Horizontal)
            text_width = font_metrics.horizontalAdvance(str(header_text)) + 10

            # Ensure the column is wide enough for the header text
            current_width = header.sectionSize(col)
            new_width = max(current_width, text_width)
            header.resizeSection(col, new_width)

    def toggle_auto_fit_columns(self, state: bool | None = None):
        for table in (self.ui.tableSingles, self.ui.tableDoubles, self.ui.tableTriples):
            self.auto_resize_enabled = not self.auto_resize_enabled if state is None else state
            if self.auto_resize_enabled:
                self.auto_fit_columns(table)
            else:
                self.reset_column_widths()
            header = table.horizontalHeader()
            assert header is not None
            header_viewport = header.viewport()
            assert header_viewport is not None
            header_viewport.update()

    def setSingleCharacter(self):
        char = self.ui.comboBoxSingleChar.currentText()
        start = self.ui.spinBoxSingleStart.value()
        middle = self.ui.spinBoxSingleMiddle.value()
        end = self.ui.spinBoxSingleEnd.value()

        self.ltr.set_singles_start(char, start)
        self.ltr.set_singles_middle(char, middle)
        self.ltr.set_singles_end(char, end)

    def setDoubleCharacter(self):
        prev_char = self.ui.comboBoxDoublePrevChar.currentText()
        char = self.ui.comboBoxDoubleChar.currentText()
        start = self.ui.spinBoxDoubleStart.value()
        middle = self.ui.spinBoxDoubleMiddle.value()
        end = self.ui.spinBoxDoubleEnd.value()

        self.ltr.set_doubles_start(prev_char, char, start)
        self.ltr.set_doubles_middle(prev_char, char, middle)
        self.ltr.set_doubles_end(prev_char, char, end)

    def setTripleCharacter(self):
        prev2_char = self.ui.comboBoxTriplePrev2Char.currentText()
        prev1_char = self.ui.comboBoxTriplePrev1Char.currentText()
        char = self.ui.comboBoxTripleChar.currentText()
        start = self.ui.spinBoxTripleStart.value()
        middle = self.ui.spinBoxTripleMiddle.value()
        end = self.ui.spinBoxTripleEnd.value()

        self.ltr.set_triples_start(prev2_char, prev1_char, char, start)
        self.ltr.set_triples_middle(prev2_char, prev1_char, char, middle)
        self.ltr.set_triples_end(prev2_char, prev1_char, char, end)

    def generateName(self):
        generated_name = self.ltr.generate()
        self.ui.lineEditGeneratedName.setText(generated_name)

    def addSingleRow(self):
        row_position = self.ui.tableSingles.rowCount()
        self.ui.tableSingles.insertRow(row_position)

    def removeSingleRow(self):
        sel_model = self.ui.tableSingles.selectionModel()
        assert sel_model is not None
        indices = sel_model.selectedRows()
        for index in sorted(indices):
            self.ui.tableSingles.removeRow(index.row())

    def addDoubleRow(self):
        row_position = self.ui.tableDoubles.rowCount()
        self.ui.tableDoubles.insertRow(row_position)

    def removeDoubleRow(self):
        sel_model = self.ui.tableDoubles.selectionModel()
        assert sel_model is not None
        indices = sel_model.selectedRows()
        for index in sorted(indices):
            self.ui.tableDoubles.removeRow(index.row())

    def addTripleRow(self):
        row_position = self.ui.tableTriples.rowCount()
        self.ui.tableTriples.insertRow(row_position)

    def removeTripleRow(self):
        sel_model = self.ui.tableTriples.selectionModel()
        assert sel_model is not None
        indices = sel_model.selectedRows()
        for index in sorted(indices):
            self.ui.tableTriples.removeRow(index.row())

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        super().load(filepath, resref, restype, data)
        self.ltr = read_ltr(data)
        self.updateUIFromLTR()
        self.toggle_auto_fit_columns(True)

    def build(self) -> tuple[bytes, bytes]:
        return bytes_ltr(self.ltr), b""

    def new(self):
        super().new()
        self.ltr = LTR()
        self.ui.lineEditGeneratedName.setText("")
        self.updateUIFromLTR()
