from __future__ import annotations

import json

from typing import TYPE_CHECKING, Any, cast

from loggerplus import RobustLogger
from qtpy.QtCore import QRect, QSettings, QSize, QStringListModel, Qt, Signal
from qtpy.QtGui import QColor, QPainter, QPalette, QTextCursor, QTextFormat
from qtpy.QtWidgets import (
    QAction,
    QCompleter,
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from pykotor.resource.formats.ncs.compiler.classes import FunctionDefinition
from toolset.gui.widgets.settings.installations import GlobalSettings
from utility.ui_libraries.qt.widgets.itemviews.treewidget import RobustTreeWidget

if TYPE_CHECKING:
    from qtpy.QtCore import QPoint
    from qtpy.QtGui import QFocusEvent, QKeyEvent, QPaintEvent, QResizeEvent, QTextBlock, QTextDocument
    from qtpy.QtWidgets import QTreeWidgetItem
    from typing_extensions import Literal



class CodeEditor(QPlainTextEdit):
    """CodeEditor shows the line numbers on the side of the text editor and highlights the row the cursor is on.

    Ported from the C++ code at: https://doc.qt.io/qt-5/qtwidgets-widgets-codeeditor-example.html
    """
    snippetAdded: Signal = Signal(str, str)  # name, content
    snippetRemoved: Signal = Signal(int)  # index
    snippetInsertRequested: Signal = Signal(str)  # content
    snippetsLoadRequested: Signal = Signal()
    snippetsSaveRequested: Signal = Signal(list)  # list of dicts

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self._lineNumberArea: LineNumberArea = LineNumberArea(self)

        self._length: int = len(self.toPlainText())

        self.blockCountChanged.connect(self._updateLineNumberAreaWidth)
        self.updateRequest.connect(self._updateLineNumberArea)
        self.cursorPositionChanged.connect(self._highlightCurrentLine)

        self._updateLineNumberAreaWidth(0)
        self._highlightCurrentLine()

        # Snippets
        self.snippets: dict[str, Any] = {}

        # Settings
        self.settings = GlobalSettings()

        # Bookmarks
        self.bookmarkTree: RobustTreeWidget = RobustTreeWidget()
        self.bookmarkTree.setHeaderLabels(["Line", "Description"])
        self.bookmarkTree.itemDoubleClicked.connect(self.goto_bookmark)

        self.setMouseTracking(True)

        # Completer
        self.completer: QCompleter = QCompleter(self)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setWrapAround(False)
        self.updateCompleterModel()

        self.breakpoints: set[int] = set()
        self.modified_lines: set[int] = set()
        self.git_added_lines: set[int] = set()
        self.git_modified_lines: set[int] = set()

    def toggle_comment(self):
        """Toggle comment for the current line or selected lines."""
        cursor = self.textCursor()
        start_pos = cursor.selectionStart()
        end_pos = cursor.selectionEnd()

        cursor.setPosition(start_pos)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.setPosition(end_pos, QTextCursor.MoveMode.KeepAnchor)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)

        selected_text = cursor.selectedText()
        lines = selected_text.split("\u2029")  # Unicode line separator

        comment_out = any(not line.lstrip().startswith("//") for line in lines if line.strip())

        cursor.beginEditBlock()
        for i, line in enumerate(lines):
            if comment_out:
                if line.strip():
                    lines[i] = "// " + line
            elif line.lstrip().startswith("//"):
                lines[i] = line.replace("//", "", 1).lstrip()

        cursor.removeSelectedText()
        cursor.insertText("\n".join(lines))
        cursor.endEditBlock()

        self.setTextCursor(cursor)

    def updateCompleterModel(self):
        words = set()
        doc = self.document()
        for i in range(doc.blockCount()):
            block = doc.findBlockByNumber(i)
            words.update(block.text().split())

        model = QStringListModel(list(words))
        self.completer.setModel(model)

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
        painter.fillRect(e.rect(), self.palette().color(QPalette.ColorRole.AlternateBase))

        block: QTextBlock = self.firstVisibleBlock()
        blockNumber: int = block.blockNumber()
        top: float = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom: float = top + self.blockBoundingRect(block).height()

        font_metrics = self.fontMetrics()
        line_number_area_width = self._lineNumberArea.width()
        font_height = font_metrics.height()

        text_color = self.palette().color(QPalette.ColorRole.Text)
        painter.setPen(text_color)

        while block.isValid() and top <= e.rect().bottom():
            if block.isVisible() and bottom >= e.rect().top():
                number = str(blockNumber + 1)
                painter.drawText(0, int(top), line_number_area_width, font_height,
                                 Qt.AlignmentFlag.AlignRight, number)

                # Draw breakpoint
                if blockNumber in self.breakpoints:
                    painter.setBrush(QColor(255, 0, 0))
                    painter.drawEllipse(2, int(top) + 2, 10, 10)

                # Draw modification indicator
                if blockNumber in self.modified_lines:
                    painter.fillRect(0, int(top), 2, font_height, QColor(0, 0, 255))

                # Draw git indicators
                if blockNumber in self.git_added_lines:
                    painter.fillRect(0, int(top), 2, font_height, QColor(0, 255, 0))
                elif blockNumber in self.git_modified_lines:
                    painter.fillRect(0, int(top), 2, font_height, QColor(255, 165, 0))

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
            maximum //= 10
            digits += 1
        space = 3 + self.fontMetrics().horizontalAdvance("9") * digits
        return space

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

    def insert_text_at_cursor(
        self,
        insert: str,
        offset: int | None = None,
    ):
        cursor = self.textCursor()
        index = cursor.position()
        text = self.toPlainText()
        self.setPlainText(text[:index] + insert + text[index:])
        offset = len(insert) if offset is None else offset
        cursor.setPosition(index + offset)
        self.setTextCursor(cursor)

    def on_text_changed(self):
        # Check if text was inserted not deleted
        insertion: bool = self._length < len(self.toPlainText())

        if insertion:
            index = self.textCursor().position()
            inserted = self.toPlainText()[index - 1 : index]
            text = self.toPlainText()[:index]

            startBrace = text.count("{")
            endBrace = text.count("}")
            indent = startBrace - endBrace

            if inserted == "\n" and indent > 0:
                from toolset.gui.editors.nss import NSSEditor
                space = " " * NSSEditor.TAB_SIZE if NSSEditor.TAB_AS_SPACE else "\t"
                self.insertPlainText(space * indent)

        self._length = len(self.toPlainText())

    def _updateLineNumberArea(self, rect: QRect, dy: int):
        if dy:
            self._lineNumberArea.scroll(0, dy)
        else:
            self._lineNumberArea.update(0, rect.y(), self._lineNumberArea.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self._updateLineNumberAreaWidth(0)

    def goto_bookmark(self, item: QTreeWidgetItem):
        line_number: int = item.data(0, Qt.ItemDataRole.UserRole)
        self._goto_line(line_number)

    def _goto_line(self, line_number: int):
        cursor: QTextCursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.MoveAnchor, line_number - 1)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def _save_bookmarks(self):
        bookmarks: list[dict[str, Any]] = []
        for i in range(self.bookmarkTree.topLevelItemCount()):
            item: QTreeWidgetItem | None = self.bookmarkTree.topLevelItem(i)
            if item is None:
                continue
            bookmarks.append({"line": item.data(0, Qt.ItemDataRole.UserRole), "description": item.text(1)})
        QSettings().setValue("bookmarks", json.dumps(bookmarks))

    def contextMenuEvent(self, event):
        """Override context menu to show snippet options."""
        menu = self.createStandardContextMenu()
        snippet_menu = QMenu("Snippets", self)
        for trigger, content in self.snippets.items():
            action = QAction(trigger, self)
            action.triggered.connect(lambda checked, content=content: self.insertPlainText(content))
            snippet_menu.addAction(action)
        menu.addMenu(snippet_menu)
        menu.exec_(event.globalPos())

    # Additional methods
    def show_auto_complete_menu(self):
        self.completer.setCompletionPrefix(self.textUnderCursor())
        if self.completer.completionCount() > 0:
            rect = self.cursorRect()
            rect.setWidth(self.completer.popup().sizeHintForColumn(0) + self.completer.popup().verticalScrollBar().sizeHint().width())
            self.completer.complete(rect)

    def textUnderCursor(self) -> str:
        tc: QTextCursor = self.textCursor()
        tc.select(QTextCursor.SelectionType.WordUnderCursor)
        return tc.selectedText()

    def insertCompletion(self, completion: str):
        tc = self.textCursor()
        extra = len(completion) - len(self.completer.completionPrefix())
        tc.movePosition(QTextCursor.MoveOperation.Left)
        tc.movePosition(QTextCursor.MoveOperation.EndOfWord)
        tc.insertText(completion[-extra:])
        self.setTextCursor(tc)

    def scroll_horizontally(self, steps: int = 1):
        """Scroll the code editor horizontally."""
        scrollbar = self.horizontalScrollBar()
        scrollbar.setValue(scrollbar.value() + steps * scrollbar.singleStep())

    def undo(self):
        """Undo the last action in the code editor."""
        self.undo()

    def redo(self):
        """Redo the last undone action in the code editor."""
        self.redo()

    def replace(self):
        """Open a dialog to replace text in the code editor."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Replace")
        layout = QVBoxLayout()

        find_layout = QHBoxLayout()
        find_layout.addWidget(QLabel("Find:"))
        find_edit = QLineEdit()
        find_layout.addWidget(find_edit)
        layout.addLayout(find_layout)

        replace_layout = QHBoxLayout()
        replace_layout.addWidget(QLabel("Replace:"))
        replace_edit = QLineEdit()
        replace_layout.addWidget(replace_edit)
        layout.addLayout(replace_layout)

        button_layout = QHBoxLayout()
        replace_button = QPushButton("Replace")
        replace_all_button = QPushButton("Replace All")
        button_layout.addWidget(replace_button)
        button_layout.addWidget(replace_all_button)
        layout.addLayout(button_layout)

        dialog.setLayout(layout)
        splitter = QSplitter(self)
        splitter.setOrientation(Qt.Vertical)
        splitter.setSizes([400, 100])
        layout.addWidget(splitter)

        def do_replace(all_occurrences: bool = False):  # noqa: FBT001, FBT002
            find_text = find_edit.text()
            replace_text = replace_edit.text()
            cursor = self.textCursor()

            if all_occurrences:
                cursor.beginEditBlock()
                cursor.movePosition(QTextCursor.MoveOperation.Start)
                while cursor.hasSelection() or cursor.movePosition(QTextCursor.MoveOperation.NextWord):
                    cursor.select(QTextCursor.SelectionType.WordUnderCursor)
                    if cursor.selectedText() == find_text:
                        cursor.insertText(replace_text)
                cursor.endEditBlock()
            elif cursor.hasSelection() and cursor.selectedText() == find_text:
                cursor.insertText(replace_text)
            else:
                cursor = self.document().find(find_text, cursor)
                if not cursor.isNull():
                    cursor.insertText(replace_text)

            self.setTextCursor(cursor)

        replace_button.clicked.connect(lambda: do_replace(False))
        replace_all_button.clicked.connect(lambda: do_replace(True))

        dialog.exec_()

    def on_outline_item_clicked(self, item: QTreeWidgetItem, column: int):
        obj: FunctionDefinition | None = item.data(0, Qt.ItemDataRole.UserRole)
        if obj is None:
            RobustLogger().error(f"Outline item '{item.text(0)}' has no function definition")
            return
        cursor = self.textCursor()
        cursor.setPosition(obj.line_num)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def on_outline_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        obj = item.data(0, Qt.ItemDataRole.UserRole)
        if obj is None:
            return
        assert isinstance(obj, FunctionDefinition)
        cursor = self.textCursor()
        cursor.setPosition(obj.line_num)
        self.setTextCursor(cursor)
        self.centerCursor()

    def go_to_line(self):
        line, ok = QInputDialog.getInt(self, "Go to Line", "Enter line number:", min=1, step=1)
        if not ok:
            return
        block = self.document().findBlockByLineNumber(line - 1)
        if block.isValid():
            cursor = QTextCursor(block)
            self.setTextCursor(cursor)
            self.centerCursor()

    def search(self):
        from toolset.gui.editors.nss import NSSEditor
        searchText = cast(NSSEditor, self.parent()).ui.searchBar.text()
        if not searchText:
            return

        document = self.document()
        cursor = document.find(searchText, self.textCursor())
        if cursor.isNull():
            cursor = document.find(searchText, 0)
        if not cursor.isNull():
            self.setTextCursor(cursor)

    def show_context_menu(self, pos: QPoint):
        menu = self.createStandardContextMenu()
        goToDefinitionAction = QAction("Go to Definition", self)
        goToDefinitionAction.triggered.connect(self.go_to_definition)
        menu.addAction(goToDefinitionAction)
        menu.exec_(self.mapToGlobal(pos))

    def go_to_definition(self):
        cursor = self.textCursor()
        word = cursor.selectedText()
        if not word:
            cursor.select(QTextCursor.WordUnderCursor)
            word = cursor.selectedText()

        if word:
            from toolset.gui.editors.nss import NSSEditor
            for obj in cast(NSSEditor, self.parent()).ui.outlineView.findItems(word, Qt.MatchFlag.MatchRecursive):  # pyright: ignore[reportArgumentType]
                if obj.data(0, Qt.ItemDataRole.UserRole):
                    self.on_outline_item_double_clicked(obj, 0)  # pyright: ignore[reportArgumentType]
                    break

    def duplicate_line(self):
        """Duplicate the current line or selected lines."""
        cursor: QTextCursor = self.textCursor()
        if cursor.hasSelection():
            start = cursor.selectionStart()
            end = cursor.selectionEnd()
            cursor.setPosition(start)
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)
        else:
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)

        text = cursor.selectedText()
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
        cursor.insertText("\n" + text)
        self.setTextCursor(cursor)

    def change_text_size(self, increase: bool = True):  # noqa: FBT001, FBT002
        """Change the font size of the code editor."""
        font = self.font()
        size = font.pointSize()
        if increase:
            size += 1
        else:
            size = max(1, size - 1)
        font.setPointSize(size)
        self.setFont(font)

    def move_line_up_or_down(self, direction: Literal["up", "down"] = "up"):
        """Move the current line or selected lines up or down."""
        cursor: QTextCursor = self.textCursor()
        document: QTextDocument = self.document()

        start_block = document.findBlock(cursor.selectionStart())
        end_block = document.findBlock(cursor.selectionEnd())

        if direction == "up" and start_block.blockNumber() == 0:
            return
        if direction == "down" and end_block.blockNumber() == document.blockCount() - 1:
            return

        cursor.beginEditBlock()

        if direction == "up":
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            cursor.movePosition(QTextCursor.MoveOperation.Up)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor)
            text_to_move = cursor.selectedText()
            cursor.removeSelectedText()
            cursor.movePosition(QTextCursor.MoveOperation.Down)
            cursor.insertText(text_to_move)
        else:  # down
            cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
            cursor.movePosition(QTextCursor.MoveOperation.Down)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
            if not cursor.atEnd():
                cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor)
            text_to_move = cursor.selectedText()
            cursor.removeSelectedText()
            cursor.movePosition(QTextCursor.MoveOperation.Up)
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            cursor.insertText(text_to_move)

        cursor.endEditBlock()
        self.setTextCursor(cursor)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Tab:
            cursor = self.textCursor()
            cursor.select(cursor.WordUnderCursor)
            selected_text = cursor.selectedText()
            if selected_text in self.snippets:
                cursor.removeSelectedText()
                cursor.insertText(self.snippets[selected_text]["content"])
            else:
                super().keyPressEvent(event)
        elif (
            self.completer
            and self.completer.popup().isVisible()
            and event.key()
            in (
                Qt.Key.Key_Enter,
                Qt.Key.Key_Return,
                Qt.Key.Key_Escape,
                Qt.Key.Key_Tab,
                Qt.Key.Key_Backtab,
            )
        ):
            event.ignore()
            return

        super().keyPressEvent(event)

        ctrlOrShift = event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
        if self.completer is None or (bool(ctrlOrShift) and len(event.text()) == 0):
            return

        eow = "~!@#$%^&*()_+{}|:\"<>?,./;'[]\\-="
        hasModifier = (event.modifiers() != Qt.KeyboardModifier.NoModifier) and not bool(ctrlOrShift)
        completionPrefix = self.textUnderCursor()

        if hasModifier or len(event.text()) == 0 or len(completionPrefix) < 3 or event.text()[-1] in eow:
            self.completer.popup().hide()
            return

        if completionPrefix != self.completer.completionPrefix():
            self.completer.setCompletionPrefix(completionPrefix)
            self.completer.popup().setCurrentIndex(self.completer.completionModel().index(0, 0))

        cr = self.cursorRect()
        cr.setWidth(self.completer.popup().sizeHintForColumn(0) + self.completer.popup().verticalScrollBar().sizeHint().width())
        self.completer.complete(cr)

    def focusInEvent(self, event: QFocusEvent):
        if self.completer:
            self.completer.setWidget(self)
        super().focusInEvent(event)

    def toggleBreakpoint(self, line: int):
        if line in self.breakpoints:
            self.breakpoints.remove(line)
        else:
            self.breakpoints.add(line)
        self._lineNumberArea.update()

    def setModifiedLines(self, lines: list[int]):
        self.modified_lines: set[int] = set(lines)
        self._lineNumberArea.update()

    def setGitLines(self, added_lines: list[int], modified_lines: list[int]):
        self.git_added_lines: set[int] = set(added_lines)
        self.git_modified_lines: set[int] = set(modified_lines)
        self._lineNumberArea.update()


class LineNumberArea(QWidget):
    def __init__(self, editor: CodeEditor):
        super().__init__(editor)
        self._editor: CodeEditor = editor

    def sizeHint(self) -> QSize:
        return QSize(self._editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self._editor.lineNumberAreaPaintEvent(event)

class NSSCodeEditor(CodeEditor):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.load_settings()

    def load_settings(self):
        settings = QSettings()
        self.restoreGeometry(settings.value("NSSCodeEditor/geometry", self.saveGeometry()))

    def save_settings(self):
        settings = QSettings()
        settings.setValue("NSSCodeEditor/geometry", self.saveGeometry())

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        pos = event.pos()
        text = event.mimeData().text()
        self.insert_text_at_position(text, pos)

    def insert_text_at_position(self, text: str, pos: QPoint):
        cursor = self.cursorForPosition(pos)
        cursor.insertText(text)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.save_settings()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.save_settings()

class WebViewEditor(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.web_view = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        try:
            from qtpy.QtWebEngineWidgets import QWebEngineView
            self.web_view = QWebEngineView(self)
            layout.addWidget(self.web_view)
        except ImportError:
            label = QLabel("Web engine not available. Please install QtWebEngine.", self)
            layout.addWidget(label)

    def load_url(self, url: str):
        if self.web_view:
            self.web_view.load(url)

class NSSEditor(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.native_editor = NSSCodeEditor(self)
        self.web_editor = WebViewEditor(self)
        self.current_editor = self.native_editor
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.editor_stack = QStackedWidget(self)
        self.editor_stack.addWidget(self.native_editor)
        self.editor_stack.addWidget(self.web_editor)
        layout.addWidget(self.editor_stack)

        self.toggle_button = QPushButton("Toggle Editor", self)
        self.toggle_button.clicked.connect(self.toggle_editor)
        layout.addWidget(self.toggle_button)

    def toggle_editor(self):
        if self.current_editor == self.native_editor:
            self.editor_stack.setCurrentWidget(self.web_editor)
            self.current_editor = self.web_editor
            # Here you would sync the content from native to web editor
        else:
            self.editor_stack.setCurrentWidget(self.native_editor)
            self.current_editor = self.native_editor
            # Here you would sync the content from web to native editor

    def load_file(self, file_path: str):
        with open(file_path) as file:
            content = file.read()
        self.native_editor.setPlainText(content)
        # If using web editor, you'd need to implement a way to load the content there as well

    def save_file(self, file_path: str):
        content = self.native_editor.toPlainText()
        with open(file_path, "w") as file:
            file.write(content)
        # If using web editor, you'd need to implement a way to get the content from there as well

    def set_syntax_highlighter(self, highlighter):
        # Assuming the highlighter is compatible with QSyntaxHighlighter
        highlighter(self.native_editor.document())
        # For web editor, you'd need to implement syntax highlighting differently

    def get_text(self) -> str:
        return self.native_editor.toPlainText()
        # If using web editor, you'd need to implement a way to get the content from there as well
