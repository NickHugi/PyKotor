from __future__ import annotations

import multiprocessing

from contextlib import contextmanager
from operator import attrgetter
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Generator, NamedTuple

import qtpy

from qtpy import QtCore
from qtpy.QtCore import QRect, QRegularExpression, QSize
from qtpy.QtGui import (
    QColor,
    QFont,
    QFontMetricsF,
    QPainter,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextFormat,
)
from qtpy.QtWidgets import QDialog, QListWidgetItem, QMessageBox, QPlainTextEdit, QShortcut, QTextEdit, QWidget

from pykotor.common.scriptdefs import KOTOR_CONSTANTS, KOTOR_FUNCTIONS, TSL_CONSTANTS, TSL_FUNCTIONS
from pykotor.common.stream import BinaryReader
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_any_erf_type_file, is_bif_file, is_rim_file
from pykotor.tools.path import CaseAwarePath
from toolset.gui.dialogs.github_selector import GitHubFileSelector
from toolset.gui.editor import Editor
from toolset.gui.widgets.settings.installations import GlobalSettings, NoConfigurationSetError
from toolset.utils.script import compileScript, decompileScript
from utility.error_handling import universal_simplify_exception
from utility.logger_util import get_log_directory
from utility.misc import is_debug_mode
from utility.system.path import Path, PurePath
from utility.updater.github import download_github_file

if TYPE_CHECKING:
    import os

    from qtpy.QtGui import (
        QPaintEvent,
        QResizeEvent,
        QTextBlock,
        QTextDocument,
    )

    from pykotor.common.script import ScriptConstant, ScriptFunction
    from toolset.data.installation import HTInstallation


def download_script(
    url: str,
    local_path: str,
    script_relpath: str,
):
    """Downloads a file using `download_github_file` and updates the progress queue."""
    print(f"Downloading script @ {url}")
    print(f"Saving to {local_path}")
    download_github_file(url, local_path, script_relpath)


class NSSEditor(Editor):
    TAB_SIZE = 4
    TAB_AS_SPACE = True

    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation | None,
    ):
        """Initialize the script editor window.

        Args:
        ----
            parent: QWidget | None: The parent widget
            installation: HTInstallation | None: The installation object

        Processing Logic:
        ----------------
            1. Call the base class initializer
            2. Load the UI from the designer file
            3. Set up menus and signals
            4. Initialize member variables like length, global settings and syntax highlighter
            5. Set the tab size for the code editor
            6. Create a new empty script.
        """
        supported: list[ResourceType] = [ResourceType.NSS, ResourceType.NCS]
        super().__init__(parent, "Script Editor", "script", supported, supported, installation)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.editors.nss import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.editors.nss import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.editors.nss import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.editors.nss import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()

        self.owner: str = "KOTORCommunityPatches"
        self.repo: str = "Vanilla_KOTOR_Script_Source"
        self.sourcerepo_url: str = f"https://github.com/{self.owner}/{self.repo}"
        self.sourcerepo_forks_url: str = f"{self.sourcerepo_url}/forks"

        self._length: int = 0
        self._is_decompiled: bool = False
        self._global_settings: GlobalSettings = GlobalSettings()
        self._highlighter: SyntaxHighlighter = SyntaxHighlighter(self.ui.codeEdit.document(), installation)
        self.setInstallation(self._installation)

        self.ui.codeEdit.setTabStopDistance(QFontMetricsF(self.ui.codeEdit.font()).horizontalAdvance(" ") * NSSEditor.TAB_SIZE)

        self.new()

    def _setupSignals(self):
        """Sets up signals and slots for the GUI.

        Args:
        ----
            self: The class instance.

        Processing Logic:
        ----------------
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

    def setInstallation(self, installation: HTInstallation):
        """Sets the installation for the editor.

        Args:
        ----
            installation: {Installation}: The installation to set.

        Processing Logic:
        ----------------
            - Sets the global constants and functions based on the installation type (TSL or KOTOR)
            - Sorts the constants and functions alphabetically by name
            - Adds each constant and function to their respective QListWidget, storing the actual object as user data.
        """
        self._installation = installation

        # sort them alphabetically
        constants: list[ScriptConstant] = sorted(TSL_CONSTANTS if self._installation.tsl else KOTOR_CONSTANTS, key=attrgetter("name"))
        functions: list[ScriptFunction] = sorted(TSL_FUNCTIONS if self._installation.tsl else KOTOR_FUNCTIONS, key=attrgetter("name"))

        for function in functions:
            item = QListWidgetItem(function.name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, function)
            self.ui.functionList.addItem(item)

        for constant in constants:
            item = QListWidgetItem(constant.name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, constant)
            self.ui.constantList.addItem(item)

    class SavedContext(NamedTuple):
        """A context that can be saved and restored by _snapshotResTypeContext."""
        filepath: Path
        resname: str
        restype: ResourceType
        revert: bytes
        saved_connection: Any  # Specify the actual type here instead of 'any' if possible

    @contextmanager
    def _snapshotResTypeContext(
        self,
        saved_file_callback: Callable | None = None,
    ) -> Generator[SavedContext, Any, None]:
        """Snapshots the current _restype and associated state, to restore after a with statement.

        This saves the current _filepath, _resname and _revert data in a context object and restores it when done.
        If saved_file_callback is not None, it will be connected to the savedFile slot during the with statement.
        If a file is successfully saved during that time it will be called with these arguments before the context
        manager restores the original state: (filepath: str, resname: str, restype: ResourceType, data: bytes)

        Usage:

            # self._restype is NSS
            with self._snapshotResTypeContext():
                # Do something that might change self._restype to NSC.
                self.saveAs()
            # after the with statement, self._restype is returned to NSS.
        """
        if saved_file_callback:
            saved_connection = self.savedFile.connect(saved_file_callback)
        else:
            saved_connection = None
        context = NSSEditor.SavedContext(
            self._filepath,
            self._resname,
            self._restype,
            self._revert,
            saved_connection,
        )
        try:
            yield context
        finally:
            if context.saved_connection:
                self.disconnect(context.saved_connection)
            # If _restype changed, unwind all the changes that may have been made.
            if self._restype != context.restype:
                self._filepath = context.filepath
                self._resname = context.resname
                self._restype = context.restype
                self._revert = context.revert
                self.refreshWindowTitle()

    def determine_script_path(self, resref: str) -> str:
        script_filename = f"{resref}.nss"
        script_filename = script_filename.lower()
        dialog = GitHubFileSelector(self.owner, self.repo, selectedFiles=[script_filename], parent=self)
        if dialog.exec_() != QDialog.Accepted:
            raise ValueError("No script selected.")

        selected_path = dialog.getSelectedPath()
        if not selected_path:
            raise ValueError("No script selected.")
        result = selected_path
        print(f"User selected script path: {result}")
        return result

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        """Loads a resource into the editor.

        Args:
        ----
            filepath: The path to the resource file
            resref: The resource reference
            restype: The resource type
            data: The raw resource data

        Processing Logic:
        ----------------
            - Decodes NSS data and sets it as the editor text
            - Attempts to decompile NCS data and sets decompiled source as editor text
            - Catches errors during decompilation and displays message.
        """
        super().load(filepath, resref, restype, data)
        self._is_decompiled = False

        if restype is ResourceType.NSS:
            self.ui.codeEdit.setPlainText(data.decode("windows-1252", errors="ignore"))
        elif restype is ResourceType.NCS:
            error_occurred = False
            try:
                self._handle_user_ncs(data, resref)
            except ValueError as e:
                error_occurred = self._handle_exc_debug_mode(
                    "Decompilation/Download Failed", e
                )
            except NoConfigurationSetError as e:
                error_occurred = self._handle_exc_debug_mode("Filepath is not set", e)
            finally:
                if error_occurred:
                    self.new()

    def _handle_exc_debug_mode(self, arg0, e):
        QMessageBox(
            QMessageBox.Icon.Critical, arg0, str(universal_simplify_exception(e))
        ).exec_()
        if is_debug_mode():
            raise
        result = True
        return result

    def _handle_user_ncs(self, data: dict[str, str], resname: str) -> None:
        box = QMessageBox(
            QMessageBox.Icon.Question,
            "Decompile or Download",
            f"Would you like to decompile this script, or download it from the <a href='{self.sourcerepo_url}'>Vanilla Source Repository</a>?",
            buttons=QMessageBox.Yes | QMessageBox.Ok | QMessageBox.Cancel,
        )
        box.setDefaultButton(QMessageBox.Cancel)
        box.button(QMessageBox.Yes).setText("Decompile")
        box.button(QMessageBox.Ok).setText("Download")
        choice = box.exec_()
        print(f"User chose {choice} in the decompile/download messagebox.")

        if choice == QMessageBox.Yes:
            source = decompileScript(data, self._installation.path(), tsl=self._installation.tsl)
        elif choice == QMessageBox.Ok:
            source = self._download_and_load_remote_script(resname)
        else:
            return
        self.ui.codeEdit.setPlainText(source)
        self._is_decompiled = True

    def _download_and_load_remote_script(self, resref: str) -> str:
        script_path: str = self.determine_script_path(resref)
        local_path = CaseAwarePath(get_log_directory(self._global_settings.extractPath), PurePath(script_path).name)
        print(f"Local path: {local_path}")

        download_process = multiprocessing.Process(
            target=download_script,
            args=(f"{self.owner}/{self.repo}", str(local_path), script_path)
        )
        download_process.start()
        download_process.join()

        if not local_path.exists():
            raise ValueError(f"Failed to download the script: '{local_path}' did not exist after download completed.")  # noqa: TRY301

        result = BinaryReader.load_file(local_path).decode(encoding="windows-1252")

        return result

    def build(self) -> tuple[bytes | None, bytes]:
        if self._restype is not ResourceType.NCS:
            return self.ui.codeEdit.toPlainText().encode("windows-1252"), b""

        self._logger.debug(f"Compiling script '{self._resname}.{self._restype.extension}' from the NSSEditor...")
        compiled_bytes: bytes | None = compileScript(self.ui.codeEdit.toPlainText(), self._installation.path(), tsl=self._installation.tsl)
        if compiled_bytes is None:
            self._logger.debug(f"User cancelled the compilation of '{self._resname}.{self._restype.extension}'.")
            return None, b""
        return compiled_bytes, b""

    def new(self):
        super().new()

        self.ui.codeEdit.setPlainText("\n\nvoid main()\n{\n    \n}\n")

    def compileCurrentScript(self):
        """Compiles the current script.

        Attempts to compile the source code. If successful it will create a NCS file at the same location as the source
        file but as a separate file, this applies to source files encapsulated in ERF or RIM type files. If the source
        code is unsaved or stored in a BIF file, it will export to the installition override folder instead.

        A MessageBox will appear stating if the compilation was successful or not. If successful it displays the
        location of the newly compiled file.

        Args:
        ----
            self: The class instance.

        Processing Logic:
        ----------------
            1. Compiles the script source code.
            2. Determines the file path and extension to save to.
            3. Writes the compiled data to the file.
            4. Displays a success or failure message.
        """
        # _compiledResourceSaved() will show a success message if the file is saved successfully.
        with self._snapshotResTypeContext(self._compiledResourceSaved):
            try:
                self._restype = ResourceType.NCS
                filepath: Path = Path.cwd() / "untitled_script.ncs" if self._filepath is None else self._filepath
                if is_any_erf_type_file(filepath.name) or is_rim_file(filepath.name):
                    # Save the NCS resource into the given ERF/RIM.
                    # If this is not allowed save() will find a new path to save at.
                    self._filepath = filepath
                elif not filepath or is_bif_file(filepath.name):
                    self._filepath = self._installation.override_path() / f"{self._resname}.ncs"
                else:
                    self._filepath = filepath.with_suffix(".ncs")

                # Save using the overridden filepath and resource type.
                self.save()
            except ValueError as e:
                QMessageBox(QMessageBox.Icon.Critical, "Failed to compile", str(universal_simplify_exception(e))).exec_()
            except OSError as e:
                QMessageBox(QMessageBox.Icon.Critical, "Failed to save file", str(universal_simplify_exception(e))).exec_()

    def _compiledResourceSaved(
        self,
        filepath: str,
        resname: str,
        restype: ResourceType,
        data: bytes,
    ):
        """Shows a messagebox after compileCurrentScript successfully saves an NCS resource."""
        savePath = Path(filepath)
        if is_any_erf_type_file(savePath.name) or is_rim_file(savePath.name):
            # Format as /full/path/to/file.mod/resname.ncs
            savePath = savePath / f"{resname}.ncs"
        QMessageBox(
            QMessageBox.Icon.Information,
            "Success",
            f"Compiled script successfully saved to:\n {savePath}.",
        ).exec_()

    def changeDescription(self):
        """Change the description textbox to whatever function or constant the user has selected.

        This should be activated whenever the tab changes or the selection changes.

        Args:
        ----
            self: The class instance

        Processing Logic:
        ----------------
            - Clears the description edit text
            - Checks if Functions tab is selected and item is selected
            - Gets the function object and sets description text
            - Checks if Constants tab is selected and item is selected
            - Gets the constant object and sets description text
        """
        self.ui.descriptionEdit.setPlainText("")

        if self.ui.tabWidget.currentIndex() == 0 and self.ui.functionList.selectedItems():  # Functions tab
            item = self.ui.functionList.selectedItems()[0]
            function = item.data(QtCore.Qt.ItemDataRole.UserRole)
            text = function.description + "\n" + str(function)
            self.ui.descriptionEdit.setPlainText(text)
        elif self.ui.tabWidget.currentIndex() == 1 and self.ui.constantList.selectedItems():  # Constants tab
            item = self.ui.constantList.selectedItems()[0]
            constant = item.data(QtCore.Qt.ItemDataRole.UserRole)
            self.ui.descriptionEdit.setPlainText(str(constant))

    def insertSelectedConstant(self):
        """Inserts the selected constant on the constant list into the code textbox at the cursors location. The cursor is
        then shifted to the end of the newly inserted constant.
        """  # noqa: D205
        if self.ui.constantList.selectedItems():
            constant = self.ui.constantList.selectedItems()[0].data(QtCore.Qt.ItemDataRole.UserRole)
            insert = constant.name
            self.insertTextAtCursor(insert)

    def insertSelectedFunction(self):
        """Inserts the selected function on the function list into the code textbox at the cursors location. The cursor is
        then shifted to the start of the first parameter of the inserted function.
        """  # noqa: D205
        if self.ui.functionList.selectedItems():
            function: ScriptFunction = self.ui.functionList.selectedItems()[0].data(QtCore.Qt.ItemDataRole.UserRole)
            insert = f"{function.name}()"
            self.insertTextAtCursor(insert, insert.index("(") + 1)

    def insertTextAtCursor(
        self,
        insert: str,
        offset: int | None = None,
    ):
        """Inserts the given text at the cursors location and then shifts the cursor position by the offset specified. If
        no offset is specified then the cursor is moved to the end of the inserted text.

        Args:
        ----
            insert: Text to insert.
            offset: Amount of characters to shift the cursor.
        """  # noqa: D205
        cursor = self.ui.codeEdit.textCursor()
        index = cursor.position()
        text = self.ui.codeEdit.toPlainText()
        self.ui.codeEdit.setPlainText(text[:index] + insert + text[index:])
        offset = len(insert) if offset is None else offset
        cursor.setPosition(index + offset)
        self.ui.codeEdit.setTextCursor(cursor)

    def onTextChanged(self):
        """Handles text changes in the code editor.

        This method should be connected to codeEdit's textChanged signal. Its purpose is: to detect for newly inserted
        line breaks so as to auto-indent the new line.

        Args:
        ----
            self: The NSSEditor instance

        Processing Logic:
        ----------------
            - Check if text was inserted not deleted
            - Get the inserted text and preceding text
            - Count opening and closing braces in preceding text
            - Calculate indent based on brace count
            - If newline inserted and indent needed, insert indent.
        """
        # Check if text was inserted not deleted
        insertion: bool = self._length < len(self.ui.codeEdit.toPlainText())

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

    def onInsertShortcut(self):
        """Inserts selected shortcut based on active tab.

        This method should be connected to the activated signal of a QShortcut. Its purpose is to insert a constant or
        function depending on which tab is currently open at the time.

        Args:
        ----
            self: The class instance.

        Processing Logic:
        ----------------
            - Check current index of tabWidget
            - If index is 0, call insertSelectedFunction()
            - If index is 1, call insertSelectedConstant()
        """
        if self.ui.tabWidget.currentIndex() == 0:
            self.insertSelectedFunction()
        elif self.ui.tabWidget.currentIndex() == 1:
            self.insertSelectedConstant()

    def onFunctionSearch(self):
        string = self.ui.functionSearchEdit.text()
        if not string:
            return
        lower_string = string.lower()
        for i in range(self.ui.functionList.count()):
            item = self.ui.functionList.item(i)
            if not item:
                continue
            item.setHidden(lower_string not in item.text().lower())

    def onConstantSearch(self):
        string = self.ui.constantSearchEdit.text()
        if not string:
            return
        lower_string = string.lower()
        for i in range(self.ui.constantList.count()):
            item = self.ui.constantList.item(i)
            if not item:
                continue
            item.setHidden(lower_string not in item.text().lower())


class LineNumberArea(QWidget):
    def __init__(self, editor: CodeEditor):
        super().__init__(editor)
        self._editor: CodeEditor = editor

    def sizeHint(self) -> QSize:
        return QSize(self._editor.lineNumberAreaWidth(), 0)

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

    def lineNumberAreaPaintEvent(self, e: QPaintEvent):
        """Draws line numbers in the line number area.

        Args:
        ----
            e (QPaintEvent): Paint event

        Processing Logic:
        ----------------
            - Gets the painter object for the line number area
            - Fills the rect with a light gray color
            - Gets the first visible block and its top position
            - Loops through visible blocks within the paint rect
                - Draws the block number at the top position
                - Updates the top position for the next block.
        """
        painter = QPainter(self._lineNumberArea)
        painter.fillRect(e.rect(), QColor(230, 230, 230))

        block: QTextBlock = self.firstVisibleBlock()
        blockNumber: int = block.blockNumber()
        top: float = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom: float = top + self.blockBoundingRect(block).height()

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
        """Calculates the width needed to display line numbers.

        Args:
        ----
            self: The object whose method this is.

        Returns:
        -------
            int: The width in pixels needed to display line numbers.

        Processing Logic:
        ----------------
            - Calculates the number of digits needed to display the maximum line number.
            - Uses the maximum line number and digit count to calculate the minimum space needed.
            - Returns the larger of the minimum and calculated widths.
        """
        digits = 1
        maximum: int = max(1, self.blockCount())
        while maximum >= 10:
            maximum /= 10  # type: ignore[assignment]
            digits += 1
        space = 10 + self.fontMetrics().width("9") * digits
        minSpace = 10 + self.fontMetrics().width("9") * 3
        return max(minSpace, space)

    def resizeEvent(self, e: QResizeEvent):
        super().resizeEvent(e)

        cr: QRect = self.contentsRect()
        self._lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def _updateLineNumberAreaWidth(
        self,
        newBlockCount: int,
    ):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def _highlightCurrentLine(self):
        """Highlights the current line in the text editor.

        Args:
        ----
            self: The text editor widget

        Processing Logic:
        ----------------
            - Checks if the text editor is read only
            - Creates a selection object and sets the background color and full width selection property
            - Sets the selection cursor to the text cursor and clears any existing selection
            - Appends the selection to the extra selections list
            - Sets the extra selections on the text editor.
        """
        extraSelections: list[QTextEdit.ExtraSelection] = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            lineColor = QColor(255, 255, 220)
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)

        self.setExtraSelections(extraSelections)

    def _updateLineNumberArea(
        self,
        rect: QRect,
        dy: int,
    ):
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

    COMMENT_BLOCK_START = QRegularExpression("/\\*")
    COMMENT_BLOCK_END = QRegularExpression("\\*/")

    BRACES: ClassVar[list[str]] = ["\\{", "\\}", "\\(", "\\)", "\\[", "\\]"]

    def __init__(
        self,
        parent: QTextDocument,
        installation: HTInstallation,
    ):
        """Initializes the syntax highlighter.

        Args:
        ----
            parent: QTextDocument: The parent text document
            installation: HTInstallation: The installation object

        Initializes styles and rules:
            - Initializes style formats
            - Gets keywords, functions and constants from installation
            - Defines highlighting rules for keywords, functions, constants, operators, braces, numbers, strings and comments
            - Sets rules attribute with compiled rules.
        """
        super().__init__(parent)

        self.styles: dict[str, QTextCharFormat] = {
            "keyword": self.getCharFormat("blue"),
            "operator": self.getCharFormat("darkRed"),
            "numbers": self.getCharFormat("brown"),
            "comment": self.getCharFormat("gray", bold=False, italic=True),
            "string": self.getCharFormat("darkMagenta"),
            "brace": self.getCharFormat("darkRed"),
            "function": self.getCharFormat("darkGreen"),
            "constant": self.getCharFormat("darkBlue"),
        }

        functions: list[str] = [function.name for function in (TSL_FUNCTIONS if installation.tsl else KOTOR_FUNCTIONS)]
        constants: list[str] = [function.name for function in (TSL_CONSTANTS if installation.tsl else TSL_CONSTANTS)]

        rules: list[tuple[str, int, QTextCharFormat]] = []
        rules += [(rf"\b{w}\b", 0, self.styles["keyword"]) for w in SyntaxHighlighter.KEYWORDS]
        rules += [(rf"\b{w}\b", 0, self.styles["function"]) for w in functions]
        rules += [(rf"\b{w}\b", 0, self.styles["constant"]) for w in constants]
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

        self.rules: list[tuple[QtCore.QRegularExpression, int, QTextCharFormat]] = [(QtCore.QRegularExpression(pat), index, fmt) for (pat, index, fmt) in rules]

    def highlightBlock(self, text: str | None):
        """Highlights blocks of text.

        Args:
        ----
            text (str | None): The text to highlight.
        """
        if text is None:
            return

        for expression, nth, format in self.rules:
            matchIterator = expression.globalMatch(text)
            while matchIterator.hasNext():
                match = matchIterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

        self.setCurrentBlockState(0)

        startIndex = 0
        if self.previousBlockState() != 1:
            match = SyntaxHighlighter.COMMENT_BLOCK_START.match(text)
            startIndex = match.capturedStart() if match.hasMatch() else -1

        while startIndex >= 0:
            match = SyntaxHighlighter.COMMENT_BLOCK_END.match(text, startIndex)
            endIndex = match.capturedStart() if match.hasMatch() else -1

            if endIndex == -1:
                self.setCurrentBlockState(1)
                commentLength = len(text) - startIndex
            else:
                commentLength = endIndex - startIndex + match.capturedLength()

            self.setFormat(startIndex, commentLength, self.styles["comment"])
            if endIndex == -1:
                break  # Exit the loop if no end comment marker is found
            match = SyntaxHighlighter.COMMENT_BLOCK_START.match(text, startIndex + commentLength)
            startIndex = match.capturedStart() if match.hasMatch() else -1

    def getCharFormat(
        self,
        color: str | int,
        *,
        bold: bool = False,
        italic: bool = False,
    ) -> QTextCharFormat:
        # The docs on QColor are different from the stubs? Not sure why the static typing is erroring here.
        qcolor_obj = QColor(color)  # type: ignore[]
        textFormat = QTextCharFormat()
        textFormat.setForeground(qcolor_obj)
        textFormat.setFontWeight(QFont.Bold if bold else QFont.Normal)
        textFormat.setFontItalic(italic)
        return textFormat
