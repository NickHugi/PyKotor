from __future__ import annotations

from typing import TYPE_CHECKING

import qtpy

from qtpy.QtWidgets import QTableWidgetItem

from pykotor.resource.formats.ltr.ltr_auto import bytes_ltr, read_ltr
from pykotor.resource.formats.ltr.ltr_data import LTR
from pykotor.resource.type import ResourceType
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    import os

    from qtpy.QtWidgets import QWidget

    from toolset.data.installation import HTInstallation


class LTREditor(Editor):
    def __init__(self, parent: QWidget | None, installation: HTInstallation | None = None):
        supported = [ResourceType.LTR]
        super().__init__(parent, "LTR Editor", "ltr", supported, supported, installation)
        self.resize(800, 600)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.editors.ltr import Ui_MainWindow
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.editors.ltr import Ui_MainWindow
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.editors.ltr import Ui_MainWindow
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.editors.ltr import Ui_MainWindow
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()

        self.ltr = LTR()

        self.populateComboBoxes()
        self.new()

    def _setupSignals(self):
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
        indices = self.ui.tableSingles.selectionModel().selectedRows()
        for index in sorted(indices):
            self.ui.tableSingles.removeRow(index.row())

    def addDoubleRow(self):
        row_position = self.ui.tableDoubles.rowCount()
        self.ui.tableDoubles.insertRow(row_position)

    def removeDoubleRow(self):
        indices = self.ui.tableDoubles.selectionModel().selectedRows()
        for index in sorted(indices):
            self.ui.tableDoubles.removeRow(index.row())

    def addTripleRow(self):
        row_position = self.ui.tableTriples.rowCount()
        self.ui.tableTriples.insertRow(row_position)

    def removeTripleRow(self):
        indices = self.ui.tableTriples.selectionModel().selectedRows()
        for index in sorted(indices):
            self.ui.tableTriples.removeRow(index.row())

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes):
        super().load(filepath, resref, restype, data)
        self.ltr = read_ltr(data)
        self.updateUIFromLTR()

    def build(self) -> tuple[bytes, bytes]:
        return bytes_ltr(self.ltr), b""

    def new(self):
        super().new()
        self.ltr = LTR()
        self.ui.lineEditGeneratedName.setText("")
        self.updateUIFromLTR()
