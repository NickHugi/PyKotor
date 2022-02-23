from __future__ import annotations

import os
import subprocess
from operator import attrgetter
from typing import Optional

import numpy as numpy
from PyQt5 import QtCore
from PyQt5.QtCore import QSize, QRect
from PyQt5.QtGui import QIcon, QPixmap, QFontMetrics, QPaintEvent, QResizeEvent, QColor, QTextFormat, QPainter, \
    QTextBlock, QFontMetricsF
from PyQt5.QtWidgets import QWidget, QPlainTextEdit, QTextEdit, QListWidgetItem, QMessageBox, QShortcut
from pykotor.common.script import TSL_CONSTANTS, KOTOR_CONSTANTS, KOTOR_FUNCTIONS, TSL_FUNCTIONS, ScriptFunction
from pykotor.common.stream import BinaryWriter, BinaryReader
from pykotor.resource.formats.erf import ERF, load_erf, write_erf
from pykotor.resource.formats.rim import load_rim, write_rim
from pykotor.resource.type import ResourceType

from data.configuration import Configuration, NoConfigurationSetError
from data.installation import HTInstallation
from editors.editor import Editor
from editors.nss import nss_editor_ui
from utils.script import decompileScript, compileScript


class NSSEditor(Editor):
    TAB_SIZE = 4
    TAB_AS_SPACE = True

    def __init__(self, parent: QWidget, installation: Optional[HTInstallation]):
        supported = [ResourceType.NSS, ResourceType.NCS]
        super().__init__(parent, "Script Editor", supported, supported, installation)

        self.ui = nss_editor_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_menus()

        iconVersion = "x" if installation is None else "2" if installation.tsl else "1"
        iconPath = ":/images/icons/k{}/script.png".format(iconVersion)
        self.setWindowIcon(QIcon(QPixmap(iconPath)))

        self._length: int = 0
        self._config: Configuration = Configuration()
        self._installation: HTInstallation = installation
        self.setInstallation(self._installation)

        self.ui.actionCompile.triggered.connect(self.compileCurrentScript)
        self.ui.tabWidget.currentChanged.connect(self.changeDescription)
        self.ui.constantList.itemSelectionChanged.connect(self.changeDescription)
        self.ui.functionList.itemSelectionChanged.connect(self.changeDescription)
        self.ui.constantList.doubleClicked.connect(self.insertSelectedConstant)
        self.ui.functionList.doubleClicked.connect(self.insertSelectedFunction)

        self.ui.codeEdit.setTabStopDistance(QFontMetricsF(self.ui.codeEdit.font()).horizontalAdvance(' ') * NSSEditor.TAB_SIZE)
        self.ui.codeEdit.textChanged.connect(self.onTextChanged)

        QShortcut("Ctrl+Shift+S", self).activated.connect(self.compileCurrentScript)
        QShortcut("Ctrl+I", self).activated.connect(self.onInsertShortcut)

        self.new()

    def setInstallation(self, installation: HTInstallation) -> None:
        self._installation = installation

        constants = TSL_CONSTANTS if self._installation.tsl else KOTOR_CONSTANTS
        functions = TSL_FUNCTIONS if self._installation.tsl else KOTOR_FUNCTIONS

        # sort them alphabetically
        constants.sort(key=attrgetter("name"))
        functions.sort(key=attrgetter("name"))

        for function in functions:
            item = QListWidgetItem(function.name)
            item.setData(QtCore.Qt.UserRole, function)
            self.ui.functionList.addItem(item)

        for constant in constants:
            item = QListWidgetItem(constant.name)
            item.setData(QtCore.Qt.UserRole, constant)
            self.ui.constantList.addItem(item)

    def load(self, filepath: str, resref: str, restype: ResourceType, data: bytes) -> None:
        super().load(filepath, resref, restype, data)

        if restype == ResourceType.NSS:
            self.ui.codeEdit.setPlainText(data.decode())
        elif restype == ResourceType.NCS:
            try:
                source = decompileScript(data, self._installation.tsl)
                self.ui.codeEdit.setPlainText(source)
            except ValueError as e:
                QMessageBox(QMessageBox.Critical, "Decompilation Failed", str(e)).exec_()
                self.new()
            except NoConfigurationSetError as e:
                QMessageBox(QMessageBox.Critical, "Filepath is not set", str(e)).exec_()
                self.new()

    def build(self) -> bytes:
        if self._restype.NSS:
            return self.ui.codeEdit.toPlainText().encode()
        elif self._restype.NCS:
            compileScript(self.ui.codeEdit.toPlainText(), self._installation.tsl)

    def new(self) -> None:
        super().new()

        self.ui.codeEdit.setPlainText("\n\nvoid main()\n{\n    \n}\n")

    def compileCurrentScript(self) -> None:
        """
        Attempts to compile the source code. If successful it will create a NCS file at the same location as the source
        file but as a separate file, this applies to source files encapsulated in ERF or RIM type files. If the source
        code is unsaved or stored in a BIF file, it will export to the installition override folder instead.

        A MessageBox will appear stating if the compilation was successful or not. If successful it displays the
        location of the newly compiled file.
        """
        try:
            source = self.ui.codeEdit.toPlainText()
            data = compileScript(source, self._installation.tsl)

            filepath = self._filepath if self._filepath is not None else ""
            if filepath.endswith(".erf") or filepath.endswith(".mod"):
                erf = load_erf(filepath)
                erf.set(self._resref, ResourceType.NCS, data)
                write_erf(erf, filepath)
            elif filepath.endswith(".rim"):
                rim = load_rim(filepath)
                rim.set(self._resref, ResourceType.NCS, data)
                write_rim(rim, filepath)
            else:
                savePath = filepath.replace(".nss", ".ncs")
                if filepath.endswith(".bif") or filepath == "":
                    savePath = "{}{}.ncs".format(self._installation.override_path(), self._resref)
                BinaryWriter.dump(savePath, data)

            QMessageBox(QMessageBox.Information, "Success", "Compiled script successfully saved to:\n {}.".format(savePath)).exec_()
        except ValueError as e:
            QMessageBox(QMessageBox.Critical, "Failed to compile", str(e)).exec_()
        except IOError as e:
            QMessageBox(QMessageBox.Critical, "Failed to save file", str(e)).exec_()

    def changeDescription(self) -> None:
        """
        Change the description textbox to whatever function or constant the user has selected. This should be activated
        whenever the tab changes or the selection changes.
        """
        self.ui.descriptionEdit.setPlainText("")

        if self.ui.tabWidget.currentIndex() == 0 and self.ui.functionList.selectedItems():  # Functions tab
            item = self.ui.functionList.selectedItems()[0]
            function = item.data(QtCore.Qt.UserRole)
            text = function.description + "\n" + str(function)
            self.ui.descriptionEdit.setPlainText(text)
        elif self.ui.tabWidget.currentIndex() == 1 and self.ui.constantList.selectedItems():  # Constants tab
            item = self.ui.constantList.selectedItems()[0]
            constant = item.data(QtCore.Qt.UserRole)
            self.ui.descriptionEdit.setPlainText(str(constant))

    def insertSelectedConstant(self) -> None:
        """
        Inserts the selected constant on the constant list into the code textbox at the cursors location. The cursor is
        then shifted to the end of the newly inserted constant.
        """
        if self.ui.constantList.selectedItems():
            constant = self.ui.constantList.selectedItems()[0].data(QtCore.Qt.UserRole)
            insert = constant.name
            self.insertTextAtCursor(insert)

    def insertSelectedFunction(self) -> None:
        """
        Inserts the selected function on the function list into the code textbox at the cursors location. The cursor is
        then shifted to the start of the first parameter of the inserted function.
        """
        if self.ui.functionList.selectedItems():
            function: ScriptFunction = self.ui.functionList.selectedItems()[0].data(QtCore.Qt.UserRole)
            insert = "{}()".format(function.name)
            self.insertTextAtCursor(insert, insert.index('(') + 1)

    def insertTextAtCursor(self, insert: str, offset: int = None) -> None:
        """
        Inserts the given text at the cursors location and then shifts the cursor position by the offset specified. If
        no offset is specified then the cursor is moved to the end of the inserted text.
        
        Args:
            insert: Text to insert.
            offset: Amount of characters to shift the cursor.
        """
        cursor = self.ui.codeEdit.textCursor()
        index = cursor.position()
        text = self.ui.codeEdit.toPlainText()
        self.ui.codeEdit.setPlainText(text[:index] + insert + text[index:])
        offset = len(insert) if offset is None else offset
        cursor.setPosition(index + offset)
        self.ui.codeEdit.setTextCursor(cursor)

    def onTextChanged(self) -> None:
        """
        This method should be connected to codeEdit's textChanged signal. Its purpose is: to detect for newly inserted
        line breaks so as to auto-indent the new line.
        """
        # Check if text was inserted not deleted
        insertion = self._length < len(self.ui.codeEdit.toPlainText())

        if insertion:
            index = self.ui.codeEdit.textCursor().position()
            inserted = self.ui.codeEdit.toPlainText()[index-1:index]
            text = self.ui.codeEdit.toPlainText()[:index]

            startBrace = text.count("{")
            endBrace = text.count("}")
            indent = startBrace - endBrace

            if inserted == "\n" and indent > 0:
                space = " " * NSSEditor.TAB_SIZE if NSSEditor.TAB_AS_SPACE else "\t"
                self.ui.codeEdit.insertPlainText(space * indent)

        self._length = len(self.ui.codeEdit.toPlainText())

    def onInsertShortcut(self) -> None:
        """
        This method should be connected to the activated signal of a QShortcut. Its purpose is to insert a constant or
        function depending on which tab is currently open at the time.
        """
        if self.ui.tabWidget.currentIndex() == 0:
            self.insertSelectedFunction()
        elif self.ui.tabWidget.currentIndex() == 1:
            self.insertSelectedConstant()


class LineNumberArea(QWidget):
    def __init__(self, editor: CodeEditor):
        super().__init__(editor)
        self._editor: CodeEditor = editor

    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self._editor.lineNumberAreaPaintEvent(event)


class CodeEditor(QPlainTextEdit):
    """
    CodeEditor shows the line numbers on the side of the text editor and highlights the row the cursor is on.

    Ported from the C++ code at: https://doc.qt.io/qt-5/qtwidgets-widgets-codeeditor-example.html
    """

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self._lineNumberArea = LineNumberArea(self)

        self.blockCountChanged.connect(self._updateLineNumberAreaWidth)
        self.updateRequest.connect(self._updateLineNumberArea)
        self.cursorPositionChanged.connect(self._highlightCurrentLine)

        self._updateLineNumberAreaWidth(0)
        self._highlightCurrentLine()

    def lineNumberAreaPaintEvent(self, e: QPaintEvent) -> None:
        painter = QPainter(self._lineNumberArea)
        painter.fillRect(e.rect(), QColor(230, 230, 230))

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= e.rect().bottom():
            if block.isVisible() and bottom >= e.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(QColor(140, 140, 140))
                painter.drawText(0, int(top), self._lineNumberArea.width(), self.fontMetrics().height(),
                                 QtCore.Qt.AlignCenter, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1

    def lineNumberAreaWidth(self) -> int:
        digits = 1
        maximum = max(1, self.blockCount())
        while maximum >= 10:
            maximum /= 10
            digits += 1
        space = 10 + self.fontMetrics().width('9') * digits
        minSpace = 10 + self.fontMetrics().width('9') * 3
        return max(minSpace, space)

    def resizeEvent(self, e: QResizeEvent) -> None:
        super().resizeEvent(e)

        cr = self.contentsRect()
        self._lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def _updateLineNumberAreaWidth(self, newBlockCount: int) -> None:
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def _highlightCurrentLine(self) -> None:
        extraSelections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            lineColor = QColor(255, 255, 220)
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)

        self.setExtraSelections(extraSelections)

    def _updateLineNumberArea(self, rect: QRect, dy: int) -> None:
        if dy:
            self._lineNumberArea.scroll(0, dy)
        else:
            self._lineNumberArea.update(0, rect.y(), self._lineNumberArea.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self._updateLineNumberAreaWidth(0)
