from __future__ import annotations

import json

from typing import TYPE_CHECKING, Any, ClassVar

import qtpy

from qtpy.QtCore import (
    QRect,
    QSettings,
    QSize,
    QStringListModel,
    Qt,
    QTimer,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtCore import QPoint
from qtpy.QtGui import QColor, QMouseEvent, QPainter, QPalette, QTextCharFormat, QTextCursor, QTextDocument, QTextFormat
from qtpy.QtWidgets import (
    QCheckBox,
    QCompleter,
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

if qtpy.QT5:
    from qtpy.QtCore import QRegExp  # pyright: ignore[reportAttributeAccessIssue]
elif qtpy.QT6:
    from qtpy.QtCore import QRegularExpression  # pyright: ignore[reportAttributeAccessIssue]

from pykotor.resource.formats.ncs.compiler.classes import FunctionDefinition
from toolset.gui.common.localization import translate as tr
from toolset.gui.widgets.settings.installations import GlobalSettings
from utility.ui_libraries.qt.widgets.itemviews.treewidget import RobustTreeWidget

if TYPE_CHECKING:
    from qtpy.QtCore import QAbstractItemModel, QMimeData, QPoint
    from qtpy.QtGui import QDragEnterEvent, QDropEvent, QFocusEvent, QFont, QFontMetrics, QKeyEvent, QMoveEvent, QPaintEvent, QResizeEvent, QTextBlock
    from qtpy.QtWidgets import QAbstractItemView, QScrollBar, QTreeWidgetItem
    from typing_extensions import Literal, Self  # noqa: F401  # pyright: ignore[reportMissingModuleSource]


class CodeEditor(QPlainTextEdit):
    """CodeEditor shows the line numbers on the side of the text editor and highlights the row the cursor is on.

    Adapted from the C++ code at: https://doc.qt.io/qt-5/qtwidgets-widgets-codeeditor-example.html
    """

    sig_snippet_added: ClassVar[Signal] = Signal(str, str)  # name, content
    sig_snippet_removed: ClassVar[Signal] = Signal(int)  # index
    sig_snippet_insert_requested: ClassVar[Signal] = Signal(str)  # content
    sig_snippets_load_requested: ClassVar[Signal] = Signal()
    sig_snippets_save_requested: ClassVar[Signal] = Signal(list)  # list of dicts

    def __init__(
        self,
        parent: QWidget,
    ):
        super().__init__(parent)
        self._line_number_area: LineNumberArea = LineNumberArea(self)

        self._length: int = len(self.toPlainText())

        self.find_dialog: QDialog | None = None

        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)
        self.cursorPositionChanged.connect(self._match_brackets)
        
        # Connect text changes to update foldable regions
        document = self.document()
        if document is not None:
            document.contentsChange.connect(self._on_contents_changed)

        self._update_line_number_area_width(0)
        self._highlight_current_line()

        # Snippets
        self.snippets: dict[str, Any] = {}

        # Settings
        self.settings: GlobalSettings = GlobalSettings()

        # Bookmarks
        self.bookmark_tree: RobustTreeWidget = RobustTreeWidget()
        self.bookmark_tree.setHeaderLabels(["Line", "Description"])
        self.bookmark_tree.itemDoubleClicked.connect(self.goto_bookmark)

        self.setMouseTracking(True)

        # Completer
        self.completer: QCompleter = QCompleter(self)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setWrapAround(False)
        self.update_completer_model()

        self.modified_lines: set[int] = set()
        self.bookmark_lines: set[int] = set()  # Line numbers with bookmarks (1-indexed)
        self.error_lines: set[int] = set()  # Line numbers with errors (1-indexed)
        self.warning_lines: set[int] = set()  # Line numbers with warnings (1-indexed)
        self.breakpoint_lines: set[int] = set()  # Line numbers with breakpoints (1-indexed)
        self.current_debug_line: int | None = None  # Current line being debugged (1-indexed)
        
        # Column selection state
        self._column_selection_mode: bool = False
        self._column_selection_anchor: QPoint | None = None
        
        # Multiple cursor/selection state for Ctrl+D
        self._multiple_selections: list[tuple[int, int]] = []  # List of (start, end) positions
        
        # Code folding state
        self._folded_block_numbers: set[int] = set()  # Block numbers that are folded (blocks that start foldable regions)
        self._foldable_regions: dict[int, int] = {}  # Map start block number to end block number for foldable regions

    def toggle_comment(self):
        """Toggle comment for the current line or selected lines."""
        cursor: QTextCursor = self.textCursor()
        start_pos: int = cursor.selectionStart()
        end_pos: int = cursor.selectionEnd()

        cursor.setPosition(start_pos)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.setPosition(end_pos, QTextCursor.MoveMode.KeepAnchor)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)

        selected_text: str = cursor.selectedText()
        lines: list[str] = selected_text.split("\u2029")  # Unicode line separator

        comment_out: bool = any(not line.lstrip().startswith("//") for line in lines if line.strip())

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

    def update_completer_model(self):
        words: set[str] = set()
        doc: QTextDocument | None = self.document()
        if doc is None:
            return
        for i in range(doc.blockCount()):
            block: QTextBlock = doc.findBlockByNumber(i)
            words.update(block.text().split())

        model: QStringListModel = QStringListModel(list(words))
        self.completer.setModel(model)

    def line_number_area_paint_event(
        self,
        e: QPaintEvent,
    ):
        """Draws line numbers in the line number area.

        Args:
        ----
            e (QPaintEvent): Paint event
        """
        painter: QPainter = QPainter(self._line_number_area)
        painter.fillRect(e.rect(), self.palette().color(QPalette.ColorRole.AlternateBase))

        block: QTextBlock = self.firstVisibleBlock()
        block_number: int = block.blockNumber()
        top: float = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom: float = top + self.blockBoundingRect(block).height()

        font_metrics: QFontMetrics = self.fontMetrics()
        line_number_area_width: int = self._line_number_area.width()
        font_height: int = font_metrics.height()

        text_color: QColor = self.palette().color(QPalette.ColorRole.Text)
        painter.setPen(text_color)

        while block.isValid() and top <= e.rect().bottom():
            if block.isVisible() and bottom >= e.rect().top():
                number: str = str(block_number + 1)
                painter.drawText(0, int(top), line_number_area_width, font_height, Qt.AlignmentFlag.AlignRight, number)

                # Draw error/warning indicators first (left edge, most important)
                line_num_1_indexed = block_number + 1
                if line_num_1_indexed in self.error_lines:
                    # Use palette color for errors - use a contrasting color that stands out
                    error_color = self.palette().color(QPalette.ColorRole.WindowText)
                    error_size = 10
                    error_x = 2
                    error_y = int(top + (font_height - error_size) / 2)
                    painter.setBrush(error_color)
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawEllipse(error_x, error_y, error_size, error_size)
                elif line_num_1_indexed in self.warning_lines:
                    # Use palette color for warnings - use mid color for visibility
                    warning_color = self.palette().color(QPalette.ColorRole.Mid)
                    warning_size = 10
                    warning_x = 2
                    warning_y = int(top + (font_height - warning_size) / 2)
                    painter.setBrush(warning_color)
                    painter.setPen(Qt.PenStyle.NoPen)
                    # Draw triangle
                    from qtpy.QtGui import QPolygon
                    triangle = QPolygon()
                    triangle.append(QPoint(warning_x + warning_size // 2, warning_y))
                    triangle.append(QPoint(warning_x, warning_y + warning_size))
                    triangle.append(QPoint(warning_x + warning_size, warning_y + warning_size))
                    painter.drawPolygon(triangle)
                
                # Draw breakpoint indicator (red circle on left side, before error/warning)
                if line_num_1_indexed in self.breakpoint_lines:
                    breakpoint_color = self.palette().color(QPalette.ColorRole.WindowText)
                    breakpoint_size = 12
                    breakpoint_x = 0
                    breakpoint_y = int(top + (font_height - breakpoint_size) / 2)
                    painter.setBrush(breakpoint_color)
                    painter.setPen(Qt.PenStyle.NoPen)
                    # Draw filled circle for breakpoint
                    painter.drawEllipse(breakpoint_x, breakpoint_y, breakpoint_size, breakpoint_size)
                
                # Draw current debug line indicator (highlighted background)
                if line_num_1_indexed == self.current_debug_line:
                    debug_color = self.palette().color(QPalette.ColorRole.Highlight)
                    painter.fillRect(0, int(top), line_number_area_width, font_height, debug_color)
                
                # Draw bookmark indicator (small circle on right side of line numbers)
                if line_num_1_indexed in self.bookmark_lines and line_num_1_indexed not in self.breakpoint_lines:
                    bookmark_color = self.palette().color(QPalette.ColorRole.Highlight)  # Use highlight color for bookmarks
                    # Draw a small filled circle for bookmark
                    bookmark_size = 8
                    bookmark_x = line_number_area_width - bookmark_size - 2
                    bookmark_y = int(top + (font_height - bookmark_size) / 2)
                    painter.setBrush(bookmark_color)
                    painter.setPen(Qt.PenStyle.NoPen)
                    # Draw filled circle
                    painter.drawEllipse(bookmark_x, bookmark_y, bookmark_size, bookmark_size)
                
                # Draw modification indicator (thin line on left edge, below errors/warnings)
                if block_number in self.modified_lines and line_num_1_indexed not in self.error_lines and line_num_1_indexed not in self.warning_lines:
                    mod_color = self.palette().color(QPalette.ColorRole.Mid)
                    painter.fillRect(0, int(top), 2, font_height, mod_color)
                
                # Draw folding indicator (arrow/collapse icon) if this line starts a foldable region
                if block_number in self._foldable_regions:
                    is_folded = block_number in self._folded_block_numbers
                    fold_x = line_number_area_width - 20
                    fold_y = int(top + (font_height - 10) / 2)
                    
                    # Draw triangle arrow (pointing right if folded, down if unfolded)
                    from qtpy.QtGui import QPolygon
                    triangle = QPolygon()
                    if is_folded:
                        # Pointing right (folded)
                        triangle.append(QPoint(fold_x, fold_y))
                        triangle.append(QPoint(fold_x, fold_y + 10))
                        triangle.append(QPoint(fold_x + 6, fold_y + 5))
                    else:
                        # Pointing down (unfolded)
                        triangle.append(QPoint(fold_x, fold_y))
                        triangle.append(QPoint(fold_x + 10, fold_y))
                        triangle.append(QPoint(fold_x + 5, fold_y + 6))
                    
                    fold_color = self.palette().color(QPalette.ColorRole.WindowText)
                    painter.setBrush(fold_color)
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawPolygon(triangle)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def line_number_area_width(self) -> int:
        digits: int = 1
        maximum: int = max(1, self.blockCount())
        while maximum >= 10:  # noqa: PLR2004
            maximum //= 10
            digits += 1
        space: int = 3 + self.fontMetrics().horizontalAdvance("9") * digits
        # Add extra space for bookmark indicators and folding arrows
        space += 25
        return space
    
    def set_bookmark_lines(self, bookmark_lines: set[int]):
        """Set the lines that have bookmarks (1-indexed line numbers)."""
        self.bookmark_lines = bookmark_lines
        self._line_number_area.update()  # Trigger repaint
    
    def set_error_lines(self, error_lines: set[int]):
        """Set the lines that have errors (1-indexed line numbers)."""
        self.error_lines = error_lines
        self._line_number_area.update()  # Trigger repaint
    
    def set_warning_lines(self, warning_lines: set[int]):
        """Set the lines that have warnings (1-indexed line numbers)."""
        self.warning_lines = warning_lines
        self._line_number_area.update()  # Trigger repaint

    def resizeEvent(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        e: QResizeEvent,
    ):
        super().resizeEvent(e)
        cr: QRect = self.contentsRect()
        self._line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def _update_line_number_area_width(
        self,
        new_block_count: int,
    ):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
    
    def _on_contents_changed(self, position: int, chars_removed: int, chars_added: int):
        """Handle document contents change to update foldable regions."""
        # Only update if significant change occurred
        if chars_removed > 0 or chars_added > 0:
            # Delay update slightly to avoid too frequent updates
            QTimer.singleShot(100, self._update_foldable_regions)
    
    def _update_foldable_regions(self):
        """Update the foldable regions based on braces in the document."""
        document: QTextDocument | None = self.document()
        if document is None:
            return
        
        # Preserve existing folded state
        old_folded = self._folded_block_numbers.copy()
        self._foldable_regions.clear()
        
        # Track brace pairs to find foldable regions
        brace_stack: list[tuple[int, int]] = []  # List of (block_number, brace_count) tuples
        brace_count = 0
        
        block = document.firstBlock()
        block_number = 0
        
        while block.isValid():
            text = block.text()
            
            # Count braces in this line (ignore braces in strings/comments)
            open_braces = 0
            close_braces = 0
            in_string = False
            in_single_line_comment = False
            
            i = 0
            while i < len(text):
                char = text[i]
                
                # Handle string literals
                if char == '"' and (i == 0 or text[i-1] != '\\'):
                    in_string = not in_string
                elif not in_string:
                    # Handle comments
                    if i < len(text) - 1 and text[i:i+2] == '//':
                        in_single_line_comment = True
                        break
                    elif not in_single_line_comment:
                        if char == '{':
                            open_braces += 1
                        elif char == '}':
                            close_braces += 1
                i += 1
            
            # Track when we enter a new brace level
            for _ in range(open_braces):
                brace_count += 1
                brace_stack.append((block_number, brace_count))
            
            # When closing braces, match with opening braces
            for _ in range(close_braces):
                brace_count -= 1
                if brace_count < 0:
                    brace_count = 0
                    continue
                
                # Find matching opening brace
                while brace_stack:
                    start_block, start_count = brace_stack[-1]
                    if start_count == brace_count + 1:
                        # Found matching brace pair
                        brace_stack.pop()
                        # Only create foldable region if there are multiple lines
                        if block_number > start_block + 1:
                            self._foldable_regions[start_block] = block_number
                        break
                    brace_stack.pop()
            
            block = block.next()
            block_number += 1
        
        # Restore folded state for regions that still exist
        self._folded_block_numbers.clear()
        for start_block in old_folded:
            if start_block in self._foldable_regions:
                self._folded_block_numbers.add(start_block)
                # Re-apply folding if it was folded before
                end_block = self._foldable_regions[start_block]
                block = document.findBlockByNumber(start_block)
                if block.isValid():
                    block = block.next()
                    block_num = start_block + 1
                    while block.isValid() and block_num <= end_block:
                        block.setVisible(False)
                        block = block.next()
                        block_num += 1
        
        self._line_number_area.update()

    def _highlight_current_line(self):
        """Highlights the current line in the text editor.

        Args:
        ----
            self: The text editor widget
        """
        extra_selections: list[QTextEdit.ExtraSelection] = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            # Use palette color for current line highlight
            line_color: QColor = self.palette().color(QPalette.ColorRole.AlternateBase)
            if not hasattr(selection, "format"):
                selection.format = QTextCharFormat()  # type: ignore[attr-value]
            selection.format.setBackground(line_color)  # type: ignore[attr-value]
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)  # type: ignore[attr-value]
            if not hasattr(selection, "cursor"):
                selection.cursor = self.textCursor()  # type: ignore[attr-value]
            selection.cursor.clearSelection()  # type: ignore[attr-value]
            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)
    
    def _match_brackets(self):
        """Highlight matching brackets (VS Code feature)."""
        cursor: QTextCursor = self.textCursor()
        document: QTextDocument | None = self.document()
        if document is None:
            return
        
        # Get character at cursor position
        pos = cursor.position()
        if pos >= document.characterCount():
            return
        
        char = document.characterAt(pos)
        
        # Define bracket pairs
        brackets = {
            '(': ')',
            '[': ']',
            '{': '}',
        }
        closing_brackets = {v: k for k, v in brackets.items()}
        
        bracket = None
        direction = 0
        
        # Check if cursor is at an opening bracket
        if char in brackets:
            bracket = char
            direction = 1
        # Check if cursor is before a closing bracket
        elif pos > 0 and document.characterAt(pos - 1) in closing_brackets:
            bracket = document.characterAt(pos - 1)
            direction = -1
            pos -= 1
        
        if bracket is None:
            return
        
        # Find matching bracket
        matching_bracket = brackets.get(bracket) or closing_brackets.get(bracket)
        if matching_bracket is None:
            return
        
        # Search for matching bracket
        depth = 0
        search_pos = pos + direction
        found_pos = -1
        
        while 0 <= search_pos < document.characterCount():
            char_at_pos = document.characterAt(search_pos)
            
            if char_at_pos == bracket:
                depth += 1
            elif char_at_pos == matching_bracket:
                if depth == 0:
                    found_pos = search_pos
                    break
                depth -= 1
            
            search_pos += direction
        
        # Highlight both brackets if match found
        extra_selections: list[QTextEdit.ExtraSelection] = []
        
        if found_pos >= 0:
            # Highlight opening bracket
            cursor1 = QTextCursor(document)
            cursor1.setPosition(pos)
            cursor1.setPosition(pos + 1, QTextCursor.MoveMode.KeepAnchor)
            selection1 = QTextEdit.ExtraSelection()
            selection1.cursor = cursor1  # type: ignore[attr-value]
            selection1.format = QTextCharFormat()  # type: ignore[attr-value]
            highlight_color = self.palette().color(QPalette.ColorRole.Highlight)
            selection1.format.setBackground(highlight_color.lighter(120))  # type: ignore[attr-value]
            selection1.format.setForeground(self.palette().color(QPalette.ColorRole.HighlightedText))  # type: ignore[attr-value]
            extra_selections.append(selection1)
            
            # Highlight closing bracket
            cursor2 = QTextCursor(document)
            cursor2.setPosition(found_pos)
            cursor2.setPosition(found_pos + 1, QTextCursor.MoveMode.KeepAnchor)
            selection2 = QTextEdit.ExtraSelection()
            selection2.cursor = cursor2  # type: ignore[attr-value]
            selection2.format = QTextCharFormat()  # type: ignore[attr-value]
            selection2.format.setBackground(highlight_color.lighter(120))  # type: ignore[attr-value]
            selection2.format.setForeground(self.palette().color(QPalette.ColorRole.HighlightedText))  # type: ignore[attr-value]
            extra_selections.append(selection2)
        
        # Get existing selections (for current line highlight) - preserve them
        existing_selections = self.extraSelections()
        for sel in existing_selections:
            # Keep the current line highlight selection
            if hasattr(sel, "format") and sel.format.property(QTextFormat.Property.FullWidthSelection):  # type: ignore[attr-value]
                extra_selections.insert(0, sel)  # Insert at beginning to preserve order
        
        self.setExtraSelections(extra_selections)

    def insert_text_at_cursor(
        self,
        insert: str,
        offset: int | None = None,
    ):
        cursor: QTextCursor = self.textCursor()
        index: int = cursor.position()
        text: str = self.toPlainText()
        self.setPlainText(text[:index] + insert + text[index:])
        offset = len(insert) if offset is None else offset
        cursor.setPosition(index + offset)
        self.setTextCursor(cursor)

    def on_text_changed(self):
        # Check if text was inserted not deleted
        insertion: bool = self._length < len(self.toPlainText())

        if insertion:
            index: int = self.textCursor().position()
            inserted: str = self.toPlainText()[index - 1 : index]
            text: str = self.toPlainText()[:index]

            start_brace: int = text.count("{")
            end_brace: int = text.count("}")
            indent: int = start_brace - end_brace

            if inserted == "\n" and indent > 0:
                from toolset.gui.editors.nss import NSSEditor

                space: str = " " * NSSEditor.TAB_SIZE if NSSEditor.TAB_AS_SPACE else "\t"
                self.insertPlainText(space * indent)

        self._length = len(self.toPlainText())

    def _update_line_number_area(
        self,
        rect: QRect,
        dy: int,
    ):
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(0, rect.y(), self._line_number_area.width(), rect.height())
        viewport: QWidget | None = self.viewport()
        if viewport is None:
            return
        if rect.contains(viewport.rect()):
            self._update_line_number_area_width(0)

    def goto_bookmark(
        self,
        item: QTreeWidgetItem,
    ):
        line_number: int = item.data(0, Qt.ItemDataRole.UserRole)
        self._goto_line(line_number)

    def _goto_line(
        self,
        line_number: int,
    ):
        cursor: QTextCursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.MoveAnchor, line_number - 1)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def _save_bookmarks(self):
        bookmarks: list[dict[str, Any]] = []
        for i in range(self.bookmark_tree.topLevelItemCount()):
            item: QTreeWidgetItem | None = self.bookmark_tree.topLevelItem(i)
            if item is None:
                continue
            bookmarks.append({"line": item.data(0, Qt.ItemDataRole.UserRole), "description": item.text(1)})
        QSettings().setValue("bookmarks", json.dumps(bookmarks))

    # Additional methods
    def show_auto_complete_menu(self):
        self.completer.setCompletionPrefix(self.text_under_cursor())
        if self.completer.completionCount() > 0:
            rect: QRect = self.cursorRect()
            popup_completer: QAbstractItemView | None = self.completer.popup()
            if popup_completer is None:
                return
            vertical_scrollbar: QScrollBar | None = popup_completer.verticalScrollBar()
            if vertical_scrollbar is None:
                return
            rect.setWidth(popup_completer.sizeHintForColumn(0) + vertical_scrollbar.sizeHint().width())
            self.completer.complete(rect)
            completion_model: QAbstractItemModel | None = self.completer.completionModel()
            if completion_model is None:
                return
            popup_completer.setCurrentIndex(completion_model.index(0, 0))

    def text_under_cursor(self) -> str:
        tc: QTextCursor = self.textCursor()
        tc.select(QTextCursor.SelectionType.WordUnderCursor)
        return tc.selectedText()

    def insert_completion(
        self,
        completion: str,
    ):
        tc: QTextCursor = self.textCursor()
        extra: int = len(completion) - len(self.completer.completionPrefix())
        tc.movePosition(QTextCursor.MoveOperation.Left)
        tc.movePosition(QTextCursor.MoveOperation.EndOfWord)
        tc.insertText(completion[-extra:])
        self.setTextCursor(tc)

    def scroll_horizontally(
        self,
        steps: int = 1,
    ):
        """Scroll the code editor horizontally."""
        scrollbar: QScrollBar | None = self.horizontalScrollBar()
        if scrollbar is None:
            return
        scrollbar.setValue(scrollbar.value() + steps * scrollbar.singleStep())

    def undo(self):
        """Undo the last action in the code editor."""
        super().undo()

    def redo(self):
        """Redo the last undone action in the code editor."""
        super().redo()

    def find_and_replace_dialog(self):
        """Open a dialog to replace text in the code editor."""
        if self.find_dialog is not None:
            self.find_dialog.show()
            self.find_dialog.activateWindow()
            self.find_dialog.raise_()
            return
        self.find_dialog = QDialog(self)
        self.find_dialog.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        self.find_dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.find_dialog.setWindowTitle(tr("Find and Replace"))
        layout = QVBoxLayout(self.find_dialog)

        self.find_dialog.setStyleSheet("""
            QDialog, QWidget {
                background-color: palette(window);
                color: palette(windowText);
            }
            QLabel, QCheckBox {
                color: palette(windowText);
            }
            QLineEdit {
                background-color: palette(base);
                color: palette(text);
                border: 1px solid palette(mid);
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton {
                background-color: palette(button);
                color: palette(buttonText);
                border: 1px solid palette(mid);
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: palette(light);
            }
            QPushButton:pressed {
                background-color: palette(dark);
            }
        """)

        find_layout = QHBoxLayout()
        find_label = QLabel("Find:")
        self.find_edit: QLineEdit = QLineEdit()
        find_layout.addWidget(find_label)
        find_layout.addWidget(self.find_edit)
        layout.addLayout(find_layout)

        replace_layout = QHBoxLayout()
        replace_label = QLabel("Replace:")
        self.replace_edit: QLineEdit = QLineEdit()
        replace_layout.addWidget(replace_label)
        replace_layout.addWidget(self.replace_edit)
        layout.addLayout(replace_layout)

        options_layout = QHBoxLayout()
        self.case_sensitive: QCheckBox = QCheckBox("Case sensitive")
        self.whole_words: QCheckBox = QCheckBox("Whole words")
        self.regex: QCheckBox = QCheckBox("Regular expression")
        options_layout.addWidget(self.case_sensitive)
        options_layout.addWidget(self.whole_words)
        options_layout.addWidget(self.regex)
        layout.addLayout(options_layout)

        button_layout = QHBoxLayout()
        find_button = QPushButton("Find")
        replace_button = QPushButton("Replace")
        replace_all_button = QPushButton("Replace All")
        button_layout.addWidget(find_button)
        button_layout.addWidget(replace_button)
        button_layout.addWidget(replace_all_button)
        layout.addLayout(button_layout)

        find_button.clicked.connect(self.find_next)
        replace_button.clicked.connect(self.replace_next)
        replace_all_button.clicked.connect(self.replace_all)

        self.find_dialog.setMinimumWidth(400)
        self.find_dialog.show()

    def find_next(self, find_text: str | None = None, case_sensitive: bool = False, whole_words: bool = False, regex: bool = False, backward: bool = False):
        """Find next occurrence with optional parameters for inline find widget."""
        flags = QTextDocument.FindFlag(0)
        if case_sensitive or (hasattr(self, 'case_sensitive') and self.case_sensitive.isChecked()):
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        if whole_words or (hasattr(self, 'whole_words') and self.whole_words.isChecked()):
            flags |= QTextDocument.FindFlag.FindWholeWords
        
        if backward:
            flags |= QTextDocument.FindFlag.FindBackward

        if find_text is None:
            if hasattr(self, 'find_edit'):
                find_text = self.find_edit.text()
            else:
                return False

        search_pattern = find_text
        if regex or (hasattr(self, 'regex') and self.regex.isChecked()):
            search_pattern = QRegExp(find_text) if qtpy.QT5 else QRegularExpression(find_text)  # pyright: ignore[reportPossiblyUnboundVariable, reportAssignmentType, reportAttributeAccessIssue]

        cursor: QTextCursor = self.textCursor()
        document: QTextDocument | None = self.document()
        if document is None:
            return False
        
        # If we have a selection, start search from cursor position, otherwise wrap around
        if not backward:
            new_cursor: QTextCursor = document.find(search_pattern, cursor, flags)  # pyright: ignore[reportArgumentType, reportCallIssue]
            if new_cursor.isNull():
                # Wrap around - start from beginning
                cursor.setPosition(0)
                new_cursor = document.find(search_pattern, cursor, flags)  # pyright: ignore[reportArgumentType, reportCallIssue]
        else:
            new_cursor = document.find(search_pattern, cursor, flags)  # pyright: ignore[reportArgumentType, reportCallIssue]
            if new_cursor.isNull():
                # Wrap around - start from end
                cursor.movePosition(QTextCursor.MoveOperation.End)
                new_cursor = document.find(search_pattern, cursor, flags)  # pyright: ignore[reportArgumentType, reportCallIssue]
        
        if not new_cursor.isNull():
            self.setTextCursor(new_cursor)
            return True
        return False
    
    def find_previous(self, find_text: str | None = None, case_sensitive: bool = False, whole_words: bool = False, regex: bool = False):
        """Find previous occurrence."""
        return self.find_next(find_text, case_sensitive, whole_words, regex, backward=True)
    
    def replace_current(self, find_text: str, replace_text: str):
        """Replace currently selected text."""
        cursor = self.textCursor()
        if cursor.hasSelection():
            cursor.insertText(replace_text)
            return True
        return False
    
    def replace_all_occurrences(self, find_text: str, replace_text: str, case_sensitive: bool = False, whole_words: bool = False, regex: bool = False):
        """Replace all occurrences in document."""
        flags = QTextDocument.FindFlag(0)
        if case_sensitive:
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        if whole_words:
            flags |= QTextDocument.FindFlag.FindWholeWords

        search_pattern = find_text
        if regex:
            search_pattern = QRegExp(find_text) if qtpy.QT5 else QRegularExpression(find_text)  # pyright: ignore[reportPossiblyUnboundVariable, reportAssignmentType, reportAttributeAccessIssue]

        document: QTextDocument | None = self.document()
        if document is None:
            return 0

        count = 0
        cursor = QTextCursor(document)
        cursor.beginEditBlock()
        cursor.setPosition(0)
        
        while True:
            new_cursor = document.find(search_pattern, cursor, flags)  # pyright: ignore[reportArgumentType, reportCallIssue]
            if new_cursor.isNull() or new_cursor.position() <= cursor.position():
                break
            new_cursor.insertText(replace_text)
            cursor.setPosition(new_cursor.position())
            count += 1
        
        cursor.endEditBlock()
        return count

    def replace_next(self):
        cursor: QTextCursor = self.textCursor()
        if cursor.hasSelection():
            cursor.insertText(self.replace_edit.text())
        self.find_next()

    def replace_all(self):
        cursor: QTextCursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        count: int = 0
        while True:
            self.find_next()
            if not self.textCursor().hasSelection():
                break
            self.textCursor().insertText(self.replace_edit.text())
            count += 1
        cursor.endEditBlock()
        QMessageBox.information(self, tr("Replace All"), trf("Replaced {count} occurrences", count=count))

    def on_outline_item_clicked(
        self,
        item: QTreeWidgetItem,
        column: int,
    ):
        """Handle single click on outline item - preview location."""
        obj = item.data(0, Qt.ItemDataRole.UserRole)
        if obj is None:
            return
        
        # Get line number from object
        line_num = getattr(obj, 'line_num', None)
        if line_num is None:
            # Try to find line number from identifier
            identifier = getattr(obj, 'identifier', '')
            if identifier:
                # Search for the identifier in the document
                text = self.toPlainText()
                lines = text.split('\n')
                for i, line in enumerate(lines, 1):
                    if identifier in line and (f"void {identifier}" in line or f"struct {identifier}" in line or f"{identifier}(" in line):
                        line_num = i
                        break
        
        if line_num:
            document: QTextDocument | None = self.document()
            if document is not None:
                block = document.findBlockByLineNumber(line_num - 1)
                if block.isValid():
                    cursor: QTextCursor = self.textCursor()
                    cursor.setPosition(block.position())
                    self.setTextCursor(cursor)
                    self.ensureCursorVisible()

    def on_outline_item_double_clicked(
        self,
        item: QTreeWidgetItem,
        column: int,
    ):
        """Handle double click on outline item - go to definition."""
        obj = item.data(0, Qt.ItemDataRole.UserRole)
        if obj is None:
            return
        
        # Get line number from object
        line_num = getattr(obj, 'line_num', None)
        if line_num is None:
            # Try to find line number from identifier
            identifier = getattr(obj, 'identifier', '')
            if identifier:
                # Search for the identifier in the document
                text = self.toPlainText()
                lines = text.split('\n')
                for i, line in enumerate(lines, 1):
                    if identifier in line and (f"void {identifier}" in line or f"struct {identifier}" in line or f"{identifier}(" in line):
                        line_num = i
                        break
        
        if line_num:
            document: QTextDocument | None = self.document()
            if document is not None:
                block = document.findBlockByLineNumber(line_num - 1)
                if block.isValid():
                    cursor: QTextCursor = self.textCursor()
                    cursor.setPosition(block.position())
                    self.setTextCursor(cursor)
                    self.centerCursor()

    def go_to_line(self):
        line, ok = QInputDialog.getInt(self, "Go to Line", "Enter line number:", 1, step=1)
        if not ok:
            return
        document: QTextDocument | None = self.document()
        if document is None:
            return
        block: QTextBlock | None = document.findBlockByLineNumber(line - 1)
        if block is None or not block.isValid():
            return
        cursor: QTextCursor = QTextCursor(block)
        self.setTextCursor(cursor)
        self.centerCursor()

    def select_next_occurrence(self):
        """Select next occurrence of current word (VS Code Ctrl+D behavior)."""
        cursor: QTextCursor = self.textCursor()
        document: QTextDocument | None = self.document()
        if document is None:
            return
        
        # Get the word to search for
        search_text: str
        if cursor.hasSelection():
            search_text = cursor.selectedText()
        else:
            # Select word under cursor
            temp_cursor = QTextCursor(cursor)
            temp_cursor.select(QTextCursor.SelectionType.WordUnderCursor)
            search_text = temp_cursor.selectedText()
            if not search_text:
                return
        
        # Remove any Unicode paragraph separators
        search_text = search_text.replace("\u2029", "\n").strip()
        if not search_text:
            return
        
        # Find all selections we already have
        existing_selections = []
        for sel in self.extraSelections():
            if hasattr(sel, "cursor") and sel.cursor.hasSelection():  # type: ignore[attr-value]
                existing_selections.append(sel)
        
        # Find next occurrence starting from cursor position
        search_cursor = QTextCursor(cursor)
        search_cursor.setPosition(cursor.selectionEnd() if cursor.hasSelection() else cursor.position())
        
        # Search forward
        found = document.find(search_text, search_cursor, QTextDocument.FindFlag.FindCaseSensitively | QTextDocument.FindFlag.FindWholeWords)
        
        if not found.isNull():
            # Add this to our selections
            new_selection = QTextEdit.ExtraSelection()
            new_selection.cursor = found  # type: ignore[attr-value]
            new_selection.format = QTextCharFormat()  # type: ignore[attr-value]
            highlight_color = self.palette().color(QPalette.ColorRole.Highlight)
            new_selection.format.setBackground(highlight_color.lighter(130))  # type: ignore[attr-value]
            
            # Also select the original if not already selected
            main_cursor = QTextCursor(cursor)
            if not cursor.hasSelection():
                main_cursor.select(QTextCursor.SelectionType.WordUnderCursor)
            else:
                main_cursor.setPosition(cursor.selectionStart())
                main_cursor.setPosition(cursor.selectionEnd(), QTextCursor.MoveMode.KeepAnchor)
            
            # Create selections list with all occurrences
            all_selections = []
            
            # Add original selection if not in existing
            orig_selection = QTextEdit.ExtraSelection()
            orig_selection.cursor = main_cursor  # type: ignore[attr-value]
            orig_selection.format = QTextCharFormat()  # type: ignore[attr-value]
            orig_selection.format.setBackground(highlight_color.lighter(130))  # type: ignore[attr-value]
            all_selections.append(orig_selection)
            all_selections.append(new_selection)
            
            # Set the cursor to the new selection
            self.setTextCursor(found)
            
            # Update extra selections to show all highlighted occurrences
            extra_selections = []
            extra_selections.extend(all_selections)
            
            # Preserve current line highlight
            line_selection = QTextEdit.ExtraSelection()
            line_selection.cursor = QTextCursor(cursor)  # type: ignore[attr-value]
            line_selection.cursor.clearSelection()  # type: ignore[attr-value]
            line_selection.format = QTextCharFormat()  # type: ignore[attr-value]
            line_color = self.palette().color(QPalette.ColorRole.AlternateBase)
            line_selection.format.setBackground(line_color)  # type: ignore[attr-value]
            line_selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)  # type: ignore[attr-value]
            extra_selections.append(line_selection)
            
            self.setExtraSelections(extra_selections)
    
    def duplicate_line(self):
        """Duplicate the current line or selected lines."""
        cursor: QTextCursor = self.textCursor()
        if cursor.hasSelection():
            cursor.setPosition(cursor.selectionStart())
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.setPosition(cursor.selectionEnd(), QTextCursor.MoveMode.KeepAnchor)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)
        else:
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)

        text: str = cursor.selectedText()
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
        cursor.insertText("\n" + text)
        self.setTextCursor(cursor)

    def change_text_size(
        self,
        increase: bool = True,  # noqa: FBT001, FBT002
    ):  # noqa: FBT001, FBT002
        """Change the font size of the code editor."""
        font: QFont = self.font()
        size: int = font.pointSize()
        if increase:
            size += 1
        else:
            size = max(1, size - 1)
        font.setPointSize(size)
        self.setFont(font)

    def move_line_up_or_down(
        self,
        direction: Literal["up", "down"] = "up",
    ):
        """Move the current line or selected lines up or down."""
        cursor: QTextCursor = self.textCursor()
        document: QTextDocument | None = self.document()
        if document is None:
            return

        start_block: QTextBlock = document.findBlock(cursor.selectionStart())
        end_block: QTextBlock = document.findBlock(cursor.selectionEnd())

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

    def keyPressEvent(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        event: QKeyEvent,
    ):
        if event.key() == Qt.Key.Key_Tab:
            cursor: QTextCursor = self.textCursor()
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
            selected_text = cursor.selectedText()
            if selected_text in self.snippets:
                cursor.removeSelectedText()
                cursor.insertText(self.snippets[selected_text]["content"])
            else:
                super().keyPressEvent(event)
        elif (
            self.completer is not None
            and self.completer.popup() is not None
            and self.completer.popup().isVisible()  # pyright: ignore[reportOptionalMemberAccess]
            and event.key()
            in (
                Qt.Key.Key_Enter,
                Qt.Key.Key_Return,
                Qt.Key.Key_Escape,
                Qt.Key.Key_Tab,
                Qt.Key.Key_Backtab,
            )
        ):
            self.insert_completion(self.completer.currentCompletion())
            self.completer.popup().hide()  # pyright: ignore[reportOptionalMemberAccess]
            return

        super().keyPressEvent(event)

        ctrl_or_shift: Qt.KeyboardModifier = event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
        if self.completer is None or (bool(ctrl_or_shift) and len(event.text()) == 0):
            return

        eow: str = "~!@#$%^&*()_+{}|:\"<>?,./;'[]\\-="
        has_modifier: bool = (event.modifiers() != Qt.KeyboardModifier.NoModifier) and not bool(ctrl_or_shift)
        completion_prefix: str = self.text_under_cursor()

        if (
            has_modifier
            or len(event.text()) == 0
            or len(completion_prefix) < 3  # noqa: PLR2004
            or event.text()[-1] in eow
        ):
            self.completer.popup().hide()  # pyright: ignore[reportOptionalMemberAccess]
            return

        if completion_prefix != self.completer.completionPrefix():
            self.completer.setCompletionPrefix(completion_prefix)
            self.completer.popup().setCurrentIndex(self.completer.completionModel().index(0, 0))  # pyright: ignore[reportOptionalMemberAccess]

        cr: QRect = self.cursorRect()
        cr.setWidth(self.completer.popup().sizeHintForColumn(0) + self.completer.popup().verticalScrollBar().sizeHint().width())  # pyright: ignore[reportOptionalMemberAccess]
        self.completer.complete(cr)

    def focusInEvent(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        event: QFocusEvent,
    ):
        if self.completer:
            self.completer.setWidget(self)
        super().focusInEvent(event)
    
    def select_all_occurrences(self):
        """Select all occurrences of current word (VS Code Ctrl+Shift+L behavior)."""
        cursor: QTextCursor = self.textCursor()
        document: QTextDocument | None = self.document()
        if document is None:
            return
        
        # Get the word to search for
        search_text: str
        if cursor.hasSelection():
            search_text = cursor.selectedText()
        else:
            temp_cursor = QTextCursor(cursor)
            temp_cursor.select(QTextCursor.SelectionType.WordUnderCursor)
            search_text = temp_cursor.selectedText()
            if not search_text:
                return
        
        search_text = search_text.replace("\u2029", "\n").strip()
        if not search_text:
            return
        
        # Find all occurrences
        all_selections = []
        search_cursor = QTextCursor(document)
        highlight_color = self.palette().color(QPalette.ColorRole.Highlight)
        
        while True:
            found = document.find(search_text, search_cursor, QTextDocument.FindFlag.FindCaseSensitively | QTextDocument.FindFlag.FindWholeWords)
            if found.isNull():
                break
            
            selection = QTextEdit.ExtraSelection()
            selection.cursor = found  # type: ignore[attr-value]
            selection.format = QTextCharFormat()  # type: ignore[attr-value]
            selection.format.setBackground(highlight_color.lighter(130))  # type: ignore[attr-value]
            all_selections.append(selection)
            
            search_cursor = QTextCursor(found)
            search_cursor.setPosition(found.selectionEnd())
        
        if all_selections:
            # Set cursor to first selection
            self.setTextCursor(all_selections[0].cursor)  # type: ignore[attr-value]
            
            # Add current line highlight
            line_selection = QTextEdit.ExtraSelection()
            line_selection.cursor = QTextCursor(cursor)  # type: ignore[attr-value]
            line_selection.cursor.clearSelection()  # type: ignore[attr-value]
            line_selection.format = QTextCharFormat()  # type: ignore[attr-value]
            line_color = self.palette().color(QPalette.ColorRole.AlternateBase)
            line_selection.format.setBackground(line_color)  # type: ignore[attr-value]
            line_selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)  # type: ignore[attr-value]
            all_selections.append(line_selection)
            
            self.setExtraSelections(all_selections)
    
    def select_line(self):
        """Select entire current line (VS Code Ctrl+L behavior)."""
        cursor: QTextCursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        self.setTextCursor(cursor)
    
    def _find_foldable_region_at_cursor(self) -> tuple[int, int] | None:
        """Find the foldable region that contains or starts at the current cursor position."""
        cursor = self.textCursor()
        current_block_number = cursor.blockNumber()
        
        # Check if cursor is on a foldable region start
        if current_block_number in self._foldable_regions:
            return (current_block_number, self._foldable_regions[current_block_number])
        
        # Find the closest foldable region that contains this line
        for start_block, end_block in self._foldable_regions.items():
            if start_block <= current_block_number <= end_block:
                return (start_block, end_block)
        
        return None
    
    def fold_region(self):
        """Fold current code region (VS Code Ctrl+Shift+[ behavior)."""
        region = self._find_foldable_region_at_cursor()
        if region is None:
            return
        
        start_block, end_block = region
        if start_block in self._folded_block_numbers:
            return  # Already folded
        
        document: QTextDocument | None = self.document()
        if document is None:
            return
        
        # Hide all blocks from start_block+1 to end_block
        block = document.findBlockByNumber(start_block)
        if not block.isValid():
            return
        
        block = block.next()  # Skip the starting line
        block_number = start_block + 1
        
        while block.isValid() and block_number <= end_block:
            block.setVisible(False)
            block = block.next()
            block_number += 1
        
        # Mark as folded
        self._folded_block_numbers.add(start_block)
        self._line_number_area.update()
    
    def unfold_region(self):
        """Unfold current code region (VS Code Ctrl+Shift+] behavior)."""
        region = self._find_foldable_region_at_cursor()
        if region is None:
            return
        
        start_block, end_block = region
        if start_block not in self._folded_block_numbers:
            return  # Not folded
        
        document: QTextDocument | None = self.document()
        if document is None:
            return
        
        # Show all blocks from start_block+1 to end_block
        block = document.findBlockByNumber(start_block)
        if not block.isValid():
            return
        
        block = block.next()  # Skip the starting line
        block_number = start_block + 1
        
        while block.isValid() and block_number <= end_block:
            block.setVisible(True)
            block = block.next()
            block_number += 1
        
        # Mark as unfolded
        self._folded_block_numbers.discard(start_block)
        self._line_number_area.update()
    
    def fold_all(self):
        """Fold all code regions (VS Code Ctrl+K Ctrl+0 behavior)."""
        for start_block in self._foldable_regions:
            if start_block not in self._folded_block_numbers:
                # Temporarily set cursor to this block to reuse fold logic
                document: QTextDocument | None = self.document()
                if document is None:
                    continue
                block = document.findBlockByNumber(start_block)
                if block.isValid():
                    cursor = self.textCursor()
                    cursor.setPosition(block.position())
                    self.setTextCursor(cursor)
                    self.fold_region()
    
    def unfold_all(self):
        """Unfold all code regions (VS Code Ctrl+K Ctrl+J behavior)."""
        document: QTextDocument | None = self.document()
        if document is None:
            return
        
        # Show all blocks
        block = document.firstBlock()
        while block.isValid():
            block.setVisible(True)
            block = block.next()
        
        # Clear folded blocks
        self._folded_block_numbers.clear()
        self._line_number_area.update()
    
    def mousePressEvent(self, event: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        """Handle mouse press events for column selection and folding."""
        # Check for clicks in the line number area for folding
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if click is in line number area (left side of editor)
            line_number_area_width = self.line_number_area_width()
            if event.pos().x() < line_number_area_width:
                # Check if click is on a folding indicator
                cursor = self.cursorForPosition(event.pos())
                block_number = cursor.blockNumber()
                
                if block_number in self._foldable_regions:
                    # Toggle fold/unfold
                    if block_number in self._folded_block_numbers:
                        self.unfold_region()
                    else:
                        self.fold_region()
                    event.accept()
                    return
        
        # Check if Alt+Shift is pressed for column selection
        if event.modifiers() & Qt.KeyboardModifier.AltModifier and event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self._column_selection_mode = True
            pos = event.pos()
            self._column_selection_anchor = pos
            # Get character position at click
            cursor = self.cursorForPosition(pos)
            cursor.setPosition(cursor.position(), QTextCursor.MoveMode.MoveAnchor)
            self.setTextCursor(cursor)
            event.accept()
            return
        
        self._column_selection_mode = False
        self._column_selection_anchor = None
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        """Handle mouse move events for column selection."""
        if self._column_selection_mode and self._column_selection_anchor is not None:
            # Perform column/block selection
            anchor_pos = self._column_selection_anchor
            current_pos = event.pos()
            
            # Get cursors at both positions
            anchor_cursor = self.cursorForPosition(anchor_pos)
            current_cursor = self.cursorForPosition(current_pos)
            
            # Calculate column bounds
            anchor_line = anchor_cursor.blockNumber()
            anchor_col = anchor_cursor.columnNumber()
            current_line = current_cursor.blockNumber()
            current_col = current_cursor.columnNumber()
            
            # Determine selection bounds
            start_line = min(anchor_line, current_line)
            end_line = max(anchor_line, current_line)
            start_col = min(anchor_col, current_col)
            end_col = max(anchor_col, current_col)
            
            # Create column selection by selecting same column range across all lines
            document: QTextDocument | None = self.document()
            if document is None:
                super().mouseMoveEvent(event)
                return
            
            # Use QTextEdit's block selection mode if available, otherwise create manual selection
            cursor = QTextCursor(document)
            
            # Start from first line
            start_block = document.findBlockByNumber(start_line)
            if not start_block.isValid():
                super().mouseMoveEvent(event)
                return
            
            cursor.setPosition(start_block.position())
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor, start_col)
            
            # Move to end position
            end_block = document.findBlockByNumber(end_line)
            if not end_block.isValid():
                super().mouseMoveEvent(event)
                return
            
            end_pos = end_block.position() + min(end_col, len(end_block.text()))
            
            # Create selection spanning the column
            cursor.setPosition(end_pos, QTextCursor.MoveMode.KeepAnchor)
            
            self.setTextCursor(cursor)
            event.accept()
            return
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        """Handle mouse release events."""
        if self._column_selection_mode:
            self._column_selection_mode = False
            # Don't reset anchor yet - user might want to extend selection
            event.accept()
            return
        
        self._column_selection_anchor = None
        super().mouseReleaseEvent(event)


class LineNumberArea(QWidget):
    def __init__(self, editor: CodeEditor):
        super().__init__(editor)
        self._editor: CodeEditor = editor

    def sizeHint(self) -> QSize:
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event: QPaintEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        self._editor.line_number_area_paint_event(event)


class NSSCodeEditor(CodeEditor):
    def __init__(
        self,
        parent: QWidget,
    ):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.load_settings()

    def load_settings(self):
        self.restoreGeometry(QSettings().value("NSSCodeEditor/geometry", self.saveGeometry()))  # type: ignore[arg-type]

    def save_settings(self):
        QSettings().setValue("NSSCodeEditor/geometry", self.saveGeometry())

    def dragEnterEvent(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        event: QDragEnterEvent,
    ):
        mime_data: QMimeData | None = event.mimeData()
        if mime_data is None:
            return
        if mime_data.hasText():
            event.acceptProposedAction()

    def dropEvent(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        event: QDropEvent,
    ):
        mime_data: QMimeData | None = event.mimeData()
        if mime_data is None:
            return
        self.insert_text_at_position(mime_data.text(), event.pos() if qtpy.QT5 else event.position().toPoint())  # pyright: ignore[reportAttributeAccessIssue]

    def insert_text_at_position(
        self,
        text: str,
        pos: QPoint,
    ):
        cursor: QTextCursor = self.cursorForPosition(pos)
        cursor.insertText(text)

    def resizeEvent(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        event: QResizeEvent,
    ):
        super().resizeEvent(event)
        self.save_settings()

    def moveEvent(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        event: QMoveEvent,
    ):
        super().moveEvent(event)
        self.save_settings()
    
    def set_breakpoint_lines(self, lines: set[int]):
        """Set the lines with breakpoints.
        
        Args:
        ----
            lines: set[int]: Set of line numbers (1-indexed) with breakpoints
        """
        self.breakpoint_lines = lines.copy()
        self.update()
    
    def set_current_debug_line(self, line: int | None):
        """Set the current debug line.
        
        Args:
        ----
            line: int | None: Line number (1-indexed) currently being debugged, or None
        """
        self.current_debug_line = line
        self.update()
