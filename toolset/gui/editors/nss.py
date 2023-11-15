from __future__ import annotations

from copy import deepcopy
from operator import attrgetter
from typing import TYPE_CHECKING, ClassVar, Optional

from PyQt5 import QtCore
from PyQt5.QtCore import QRect, QRegExp, QSize
from PyQt5.QtGui import (
    QColor,
    QFont,
    QFontMetricsF,
    QPainter,
    QPaintEvent,
    QResizeEvent,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextDocument,
    QTextFormat,
)
from PyQt5.QtWidgets import QListWidgetItem, QMessageBox, QPlainTextEdit, QShortcut, QTextEdit, QWidget

from pykotor.common.scriptdefs import KOTOR_CONSTANTS, KOTOR_FUNCTIONS, TSL_CONSTANTS, TSL_FUNCTIONS
from pykotor.common.stream import BinaryWriter
from pykotor.helpers.path import Path
from pykotor.resource.formats.erf import ERF, read_erf, write_erf
from pykotor.resource.formats.rim import RIM, read_rim, write_rim
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_bif_file, is_erf_or_mod_file, is_rim_file
from toolset.gui.editor import Editor
from toolset.gui.widgets.settings.installations import GlobalSettings, NoConfigurationSetError
from toolset.utils.script import compileScript, decompileScript

if TYPE_CHECKING:
    import os

    from pykotor.common.script import ScriptConstant, ScriptFunction
    from toolset.data.installation import HTInstallation


class NSSEditor(Editor):
    TAB_SIZE = 4
    TAB_AS_SPACE = True

    def __init__(self, parent: QWidget | None, installation: HTInstallation | None):
        """Initialize the script editor window
        Args:
            parent: QWidget | None: The parent widget
            installation: HTInstallation | None: The installation object
        Returns:
            None: Does not return anything
        Processing Logic:
        1. Call the base class initializer
        2. Load the UI from the designer file
        3. Set up menus and signals
        4. Initialize member variables like length, global settings and syntax highlighter
        5. Set the tab size for the code editor
        6. Create a new empty script.
        """
        supported = [ResourceType.NSS, ResourceType.NCS]
        super().__init__(parent, "Script Editor", "script", supported, supported, installation)

        from toolset.uic.editors.nss import Ui_MainWindow

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()

        self._length: int = 0
        self._global_settings: GlobalSettings = GlobalSettings()
        self._highlighter: SyntaxHighlighter = SyntaxHighlighter(self.ui.codeEdit.document(), installation)
        self.setInstallation(self._installation)

        self.ui.codeEdit.setTabStopDistance(QFontMetricsF(self.ui.codeEdit.font()).horizontalAdvance(" ") * NSSEditor.TAB_SIZE)

        self.new()

    def _setupSignals(self) -> None:
        """Sets up signals and slots for the GUI.

        Args:
        ----
            self: The class instance.

        Returns:
        -------
            None: No return value.
        Processing Logic:
            - Connect compile action to compileCurrentScript slot
            - Connect tab changes to changeDescription slot
            - Connect constant and function list selections to changeDescription slot
            - Connect double clicks on lists to insert functions/constants
            - Connect search edits to filter function/constant lists
            - Connect code edits to onTextChanged slot
            - Add keyboard shortcuts for compile and insert
        """
        self.ui.actionCompile.triggered.connect(self.compileCurrentScript)
        self.ui.tabWidget.currentChanged.connect(self.changeDescription)
        self.ui.constantList.itemSelectionChanged.connect(self.changeDescription)
        self.ui.functionList.itemSelectionChanged.connect(self.changeDescription)
        self.ui.constantList.doubleClicked.connect(self.insertSelectedConstant)
        self.ui.functionList.doubleClicked.connect(self.insertSelectedFunction)

        self.ui.functionSearchEdit.textChanged.connect(self.onFunctionSearch)
        self.ui.constantSearchEdit.textChanged.connect(self.onConstantSearch)

        self.ui.codeEdit.textChanged.connect(self.onTextChanged)

        QShortcut("Ctrl+Shift+S", self).activated.connect(self.compileCurrentScript)
        QShortcut("Ctrl+I", self).activated.connect(self.onInsertShortcut)

    def setInstallation(self, installation: HTInstallation) -> None:
        """Sets the installation for the editor
        Args:
            installation: {Installation}: The installation to set.

        Returns
        -------
            None: No return value.
        - Sets the global constants and functions based on the installation type (TSL or KOTOR)
        - Sorts the constants and functions alphabetically by name
        - Adds each constant and function to their respective QListWidget, storing the actual object as user data.
        """
        self._installation = installation

        constants: list[ScriptConstant] = deepcopy(TSL_CONSTANTS if self._installation.tsl else KOTOR_CONSTANTS)
        functions: list[ScriptFunction] = deepcopy(TSL_FUNCTIONS if self._installation.tsl else KOTOR_FUNCTIONS)

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

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes) -> None:
        """Loads a resource into the editor
        Args:
            filepath: The path to the resource file
            resref: The resource reference
            restype: The resource type
            data: The raw resource data
        Returns:
            None
        - Decodes NSS data and sets it as the editor text
        - Attempts to decompile NCS data and sets decompiled source as editor text
        - Catches errors during decompilation and displays message.
        """
        super().load(filepath, resref, restype, data)

        if restype == ResourceType.NSS:
            self.ui.codeEdit.setPlainText(data.decode("windows-1252"))
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

    def build(self) -> tuple[bytes, bytes]:
        if self._restype.NSS:
            return self.ui.codeEdit.toPlainText().encode(encoding="windows-1252"), b""
        if self._restype.NCS:
            compileScript(self.ui.codeEdit.toPlainText(), self._installation.tsl)
        msg = "Could not convert to bytes"
        raise ValueError(msg)

    def new(self) -> None:
        super().new()

        self.ui.codeEdit.setPlainText("\n\nvoid main()\n{\n    \n}\n")

    def compileCurrentScript(self) -> None:
        """Compiles the current script.

        Attempts to compile the source code. If successful it will create a NCS file at the same location as the source
        file but as a separate file, this applies to source files encapsulated in ERF or RIM type files. If the source
        code is unsaved or stored in a BIF file, it will export to the installition override folder instead.

        A MessageBox will appear stating if the compilation was successful or not. If successful it displays the
        location of the newly compiled file.

        Args:
        ----
            self: The class instance.

        Returns:
        -------
            None: No value is returned.

        Processing Logic:
        1. Compiles the script source code.
        2. Determines the file path and extension to save to.
        3. Writes the compiled data to the file.
        4. Displays a success or failure message.
        """
        try:
            source = self.ui.codeEdit.toPlainText()
            data = compileScript(source, self._installation.tsl)

            filepath: Path = self._filepath if self._filepath is not None else Path.cwd() / "untitled_script.ncs"
            if is_erf_or_mod_file(filepath.name):
                savePath = Path(filepath, f"{self._resref}.{self._restype.extension}")
                erf: ERF = read_erf(filepath)
                erf.set_data(self._resref, ResourceType.NCS, data)
                write_erf(erf, filepath)
            elif is_rim_file(filepath.name):
                savePath = Path(filepath, f"{self._resref}.{self._restype.extension}")
                rim: RIM = read_rim(filepath)
                rim.set_data(self._resref, ResourceType.NCS, data)
                write_rim(rim, filepath)
            else:
                savePath = filepath.with_suffix(".ncs")
                if not filepath or is_bif_file(filepath.name):
                    savePath = self._installation.override_path() / f"{self._resref}.ncs"
                BinaryWriter.dump(savePath, data)

            QMessageBox(
                QMessageBox.Information,
                "Success",
                f"Compiled script successfully saved to:\n {savePath}.",
            ).exec_()
        except ValueError as e:
            QMessageBox(QMessageBox.Critical, "Failed to compile", str(e)).exec_()
        except OSError as e:
            QMessageBox(QMessageBox.Critical, "Failed to save file", str(e)).exec_()

    def changeDescription(self) -> None:
        """Change the description textbox to whatever function or constant the user has selected. This should be activated
        whenever the tab changes or the selection changes.

        Args:
        ----
            self: The class instance
        Returns:
            None: Does not return anything
        Processing Logic:
            - Clears the description edit text
            - Checks if Functions tab is selected and item is selected
            - Gets the function object and sets description text
            - Checks if Constants tab is selected and item is selected
            - Gets the constant object and sets description text
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
        """Inserts the selected constant on the constant list into the code textbox at the cursors location. The cursor is
        then shifted to the end of the newly inserted constant.
        """
        if self.ui.constantList.selectedItems():
            constant = self.ui.constantList.selectedItems()[0].data(QtCore.Qt.UserRole)
            insert = constant.name
            self.insertTextAtCursor(insert)

    def insertSelectedFunction(self) -> None:
        """Inserts the selected function on the function list into the code textbox at the cursors location. The cursor is
        then shifted to the start of the first parameter of the inserted function.
        """
        if self.ui.functionList.selectedItems():
            function: ScriptFunction = self.ui.functionList.selectedItems()[0].data(QtCore.Qt.UserRole)
            insert = f"{function.name}()"
            self.insertTextAtCursor(insert, insert.index("(") + 1)

    def insertTextAtCursor(self, insert: str, offset: Optional[int] = None) -> None:
        """Inserts the given text at the cursors location and then shifts the cursor position by the offset specified. If
        no offset is specified then the cursor is moved to the end of the inserted text.

        Args:
        ----
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
        """Handles text changes in the code editor
        This method should be connected to codeEdit's textChanged signal. Its purpose is: to detect for newly inserted
        line breaks so as to auto-indent the new line
        Args:
            self: The NSSEditor instance
        Returns:
            None: Does not return anything
        Processing Logic:
            - Check if text was inserted not deleted
            - Get the inserted text and preceding text
            - Count opening and closing braces in preceding text
            - Calculate indent based on brace count
            - If newline inserted and indent needed, insert indent.
        """
        # Check if text was inserted not deleted
        insertion = self._length < len(self.ui.codeEdit.toPlainText())

        if insertion:
            index = self.ui.codeEdit.textCursor().position()
            inserted = self.ui.codeEdit.toPlainText()[index - 1 : index]
            text = self.ui.codeEdit.toPlainText()[:index]

            startBrace = text.count("{")
            endBrace = text.count("}")
            indent = startBrace - endBrace

            if inserted == "\n" and indent > 0:
                space = " " * NSSEditor.TAB_SIZE if NSSEditor.TAB_AS_SPACE else "\t"
                self.ui.codeEdit.insertPlainText(space * indent)

        self._length = len(self.ui.codeEdit.toPlainText())

    def onInsertShortcut(self) -> None:
        """This method should be connected to the activated signal of a QShortcut. Its purpose is to insert a constant or
        function depending on which tab is currently open at the time.
        """
        if self.ui.tabWidget.currentIndex() == 0:
            self.insertSelectedFunction()
        elif self.ui.tabWidget.currentIndex() == 1:
            self.insertSelectedConstant()

    def onFunctionSearch(self) -> None:
        string = self.ui.functionSearchEdit.text()
        for i in range(self.ui.functionList.count()):
            item = self.ui.functionList.item(i)
            item.setHidden(string not in item.text())

    def onConstantSearch(self) -> None:
        string = self.ui.constantSearchEdit.text()
        for i in range(self.ui.constantList.count()):
            item = self.ui.constantList.item(i)
            item.setHidden(string not in item.text())


class LineNumberArea(QWidget):
    def __init__(self, editor: CodeEditor):
        super().__init__(editor)
        self._editor: CodeEditor = editor

    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self._editor.lineNumberAreaPaintEvent(event)


class CodeEditor(QPlainTextEdit):
    """CodeEditor shows the line numbers on the side of the text editor and highlights the row the cursor is on.

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
        """Draws line numbers in the line number area
        Args:
            e (QPaintEvent): Paint event
        Returns:
            None
        - Gets the painter object for the line number area
        - Fills the rect with a light gray color
        - Gets the first visible block and its top position
        - Loops through visible blocks within the paint rect
            - Draws the block number at the top position
            - Updates the top position for the next block.
        """
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
                painter.drawText(
                    0,
                    int(top),
                    self._lineNumberArea.width(),
                    self.fontMetrics().height(),
                    QtCore.Qt.AlignCenter,
                    number,
                )

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1

    def lineNumberAreaWidth(self) -> int:
        digits = 1
        maximum = max(1, self.blockCount())
        while maximum >= 10:
            maximum /= 10  # type: ignore[assignment]
            digits += 1
        space = 10 + self.fontMetrics().width("9") * digits
        minSpace = 10 + self.fontMetrics().width("9") * 3
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


class SyntaxHighlighter(QSyntaxHighlighter):
    KEYWORDS: ClassVar[list[str]] = [
        "return",
        "float",
        "int",
        "object",
        "location",
        "void",
        "effect",
        "action",
        "string",
        "vector",
        "talent",
        "if",
        "for",
        "while",
        "#include",
        "TRUE",
        "FALSE",
    ]

    OPERATORS: ClassVar[list[str]] = ["=", "==", "!=", "<", "<=", ">", ">=", "!", "\\+", "-", "/", "<<", ">>", "\\&", "\\|"]

    COMMENT_BLOCK_START = QRegExp("/\\*")
    COMMENT_BLOCK_END = QRegExp("\\*/")

    BRACES: ClassVar[list[str]] = ["\\{", "\\}", "\\(", "\\)", "\\[", "\\]"]

    def __init__(self, parent: QTextDocument, installation: HTInstallation):
        """Initializes the syntax highlighter
        Args:
            parent: QTextDocument: The parent text document
            installation: HTInstallation: The installation object
        Returns:
            None
        Initializes styles and rules:
            - Initializes style formats
            - Gets keywords, functions and constants from installation
            - Defines highlighting rules for keywords, functions, constants, operators, braces, numbers, strings and comments
            - Sets rules attribute with compiled rules.
        """
        super().__init__(parent)

        self.styles = {
            "keyword": self.getCharFormat("blue"),
            "operator": self.getCharFormat("darkRed"),
            "numbers": self.getCharFormat("brown"),
            "comment": self.getCharFormat("gray", False, True),
            "string": self.getCharFormat("darkMagenta"),
            "brace": self.getCharFormat("darkRed"),
            "function": self.getCharFormat("darkGreen"),
            "constant": self.getCharFormat("darkBlue"),
        }

        functions = [function.name for function in (TSL_FUNCTIONS if installation.tsl else KOTOR_FUNCTIONS)]
        constants = [function.name for function in (TSL_CONSTANTS if installation.tsl else TSL_CONSTANTS)]

        rules = []
        rules += [(r"\b%s\b" % w, 0, self.styles["keyword"]) for w in SyntaxHighlighter.KEYWORDS]
        rules += [(r"\b%s\b" % w, 0, self.styles["function"]) for w in functions]
        rules += [(r"\b%s\b" % w, 0, self.styles["constant"]) for w in constants]
        rules += [(o, 0, self.styles["operator"]) for o in SyntaxHighlighter.OPERATORS]
        rules += [(o, 0, self.styles["brace"]) for o in SyntaxHighlighter.BRACES]

        rules += [
            (r"\b[+-]?[0-9]+[lL]?\b", 0, self.styles["numbers"]),
            (r"\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b", 0, self.styles["numbers"]),
            (r"\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b", 0, self.styles["numbers"]),
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, self.styles["string"]),
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, self.styles["string"]),
            (r"//[^\n]*", 0, self.styles["comment"]),
        ]

        self.rules = [(QtCore.QRegExp(pat), index, fmt) for (pat, index, fmt) in rules]

    def highlightBlock(self, text: str | None) -> None:
        """Highlights blocks of text.

        Args:
        ----
            text (str | None): The text to highlight.

        Returns:
        -------
            None: No value is returned.
        {Processing Logic}:
        1. Checks if text is None and returns if so.
        2. Loops through rules to find expressions and apply formatting.
        3. Sets current block state to 0.
        4. Finds comment blocks and applies comment formatting.
        """
        if text is None:
            print("text cannot be None", "highlightBlock")
            return
        for expression, nth, format in self.rules:
            index = expression.indexIn(text, 0)

            while index >= 0:
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)

        startIndex = 0
        if self.previousBlockState() != 1:
            startIndex = SyntaxHighlighter.COMMENT_BLOCK_START.indexIn(text, startIndex)

        while startIndex >= 0:
            endIndex = SyntaxHighlighter.COMMENT_BLOCK_END.indexIn(text, startIndex)
            if endIndex == -1:
                self.setCurrentBlockState(1)
                commentLength = len(text) - startIndex
            else:
                commentLength = endIndex - startIndex + 2
            self.setFormat(startIndex, commentLength, self.styles["comment"])
            startIndex = SyntaxHighlighter.COMMENT_BLOCK_START.indexIn(text, startIndex + commentLength + 2)

    def getCharFormat(self, color: str | int, bold: bool = False, italic: bool = False) -> QTextCharFormat:
        color = QColor(color)
        textFormat = QTextCharFormat()
        textFormat.setForeground(color)
        textFormat.setFontWeight(QFont.Bold if bold else QFont.Normal)
        textFormat.setFontItalic(italic)
        return textFormat
