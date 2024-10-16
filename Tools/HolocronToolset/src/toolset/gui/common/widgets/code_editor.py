from __future__ import annotations

import json

from typing import TYPE_CHECKING, Any, ClassVar, cast

import qtpy

from loggerplus import RobustLogger
from qtpy.QtCore import (
    QRect,
    QSettings,
    QSize,
    QStringListModel,
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QColor, QKeySequence, QPainter, QPalette, QTextCharFormat, QTextCursor, QTextDocument, QTextFormat
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
    from qtpy.QtCore import QRegExp
elif qtpy.QT6:
    from qtpy.QtCore import QRegularExpression

from pykotor.resource.formats.ncs.compiler.classes import FunctionDefinition
from toolset.gui.widgets.settings.installations import GlobalSettings
from utility.ui_libraries.qt.widgets.itemviews.treewidget import RobustTreeWidget

if TYPE_CHECKING:
    from qtpy.QtCore import QPoint
    from qtpy.QtGui import QDragEnterEvent, QDropEvent, QFocusEvent, QFont, QFontMetrics, QKeyEvent, QMoveEvent, QPaintEvent, QResizeEvent, QTextBlock
    from qtpy.QtWidgets import QScrollBar, QTreeWidgetItem
    from typing_extensions import Literal, Self  # noqa: F401



class CodeEditor(QPlainTextEdit):
    """CodeEditor shows the line numbers on the side of the text editor and highlights the row the cursor is on.

    Adapted from the C++ code at: https://doc.qt.io/qt-5/qtwidgets-widgets-codeeditor-example.html
    """

    sig_snippet_added: ClassVar[Signal] = Signal(str, str)  # name, content
    sig_snippet_removed: ClassVar[Signal] = Signal(int)  # index
    sig_snippet_insert_requested: ClassVar[Signal] = Signal(str)  # content
    sig_snippets_load_requested: ClassVar[Signal] = Signal()
    sig_snippets_save_requested: ClassVar[Signal] = Signal(list)  # list of dicts

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self._line_number_area: LineNumberArea = LineNumberArea(self)

        self._length: int = len(self.toPlainText())

        self.find_dialog: QDialog | None = None

        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)

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
        doc: QTextDocument = self.document()
        for i in range(doc.blockCount()):
            block: QTextBlock = doc.findBlockByNumber(i)
            words.update(block.text().split())

        model: QStringListModel = QStringListModel(list(words))
        self.completer.setModel(model)

    def line_number_area_paint_event(self, e: QPaintEvent):
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

                # Draw modification indicator
                if block_number in self.modified_lines:
                    painter.fillRect(0, int(top), 2, font_height, QColor(0, 0, 255))

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def line_number_area_width(self) -> int:
        """Calculates the width needed to display line numbers.

        Args:
        ----
            self: The object whose method this is.

        Returns:
        -------
            int: The width in pixels needed to display line numbers.
        """
        digits: int = 1
        maximum: int = max(1, self.blockCount())
        while maximum >= 10:  # noqa: PLR2004
            maximum //= 10
            digits += 1
        space: int = 3 + self.fontMetrics().horizontalAdvance("9") * digits
        return space

    def resizeEvent(self, e: QResizeEvent):
        super().resizeEvent(e)
        cr: QRect = self.contentsRect()
        self._line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def _update_line_number_area_width(
        self,
        new_block_count: int,
    ):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _highlight_current_line(self):
        """Highlights the current line in the text editor.

        Args:
        ----
            self: The text editor widget
        """
        extra_selections: list[QTextEdit.ExtraSelection] = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color: QColor = QColor(255, 255, 220)
            if not hasattr(selection, "format"):
                selection.format = QTextCharFormat()  # type: ignore[attr-value]
            selection.format.setBackground(line_color)  # type: ignore[attr-value]
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)  # type: ignore[attr-value]
            if not hasattr(selection, "cursor"):
                selection.cursor = self.textCursor()  # type: ignore[attr-value]
            selection.cursor.clearSelection()  # type: ignore[attr-value]
            extra_selections.append(selection)

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

    def _update_line_number_area(self, rect: QRect, dy: int):
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(0, rect.y(), self._line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

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
            rect = self.cursorRect()
            rect.setWidth(self.completer.popup().sizeHintForColumn(0) + self.completer.popup().verticalScrollBar().sizeHint().width())
            self.completer.complete(rect)
            self.completer.popup().setCurrentIndex(self.completer.completionModel().index(0, 0))

    def text_under_cursor(self) -> str:
        tc: QTextCursor = self.textCursor()
        tc.select(QTextCursor.SelectionType.WordUnderCursor)
        return tc.selectedText()

    def insert_completion(self, completion: str):
        tc: QTextCursor = self.textCursor()
        extra: int = len(completion) - len(self.completer.completionPrefix())
        tc.movePosition(QTextCursor.MoveOperation.Left)
        tc.movePosition(QTextCursor.MoveOperation.EndOfWord)
        tc.insertText(completion[-extra:])
        self.setTextCursor(tc)

    def scroll_horizontally(self, steps: int = 1):
        """Scroll the code editor horizontally."""
        scrollbar: QScrollBar = self.horizontalScrollBar()
        scrollbar.setValue(scrollbar.value() + steps * scrollbar.singleStep())

    def undo(self):
        """Undo the last action in the code editor."""
        self.undo()

    def redo(self):
        """Redo the last undone action in the code editor."""
        self.redo()

    def find_and_replace_dialog(self):
        """Open a dialog to replace text in the code editor."""
        if self.find_dialog is not None:
            self.find_dialog.show()
            self.find_dialog.activateWindow()
            self.find_dialog.raise_()
            return
        self.find_dialog = QDialog(self)
        self.find_dialog.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.find_dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.find_dialog.setWindowTitle("Find and Replace")
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

    def find_next(self):
        flags = QTextDocument.FindFlag.FindWholeWords
        flags &= ~QTextDocument.FindFlag.FindWholeWords
        if self.case_sensitive.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        if self.whole_words.isChecked():
            flags |= QTextDocument.FindFlag.FindWholeWords

        find_text = self.find_edit.text()
        if self.regex.isChecked():
            find_text = QRegExp(find_text) if qtpy.QT5 else QRegularExpression(find_text)

        cursor: QTextCursor = self.textCursor()
        new_cursor: QTextCursor = self.document().find(find_text, cursor, flags)  # pyright: ignore[reportArgumentType, reportCallIssue]
        if not new_cursor.isNull():
            self.setTextCursor(new_cursor)
        else:
            QMessageBox.information(self, "Find", "Text not found")

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
        QMessageBox.information(self, "Replace All", f"Replaced {count} occurrences")

    def on_outline_item_clicked(self, item: QTreeWidgetItem, column: int):
        obj: FunctionDefinition | None = item.data(0, Qt.ItemDataRole.UserRole)
        if obj is None:
            RobustLogger().error(f"Outline item '{item.text(0)}' has no function definition")
            return
        cursor: QTextCursor = self.textCursor()
        cursor.setPosition(obj.line_num)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def on_outline_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        obj: FunctionDefinition | None = item.data(0, Qt.ItemDataRole.UserRole)
        if obj is None:
            return
        assert isinstance(obj, FunctionDefinition)
        cursor: QTextCursor = self.textCursor()
        cursor.setPosition(obj.line_num)
        self.setTextCursor(cursor)
        self.centerCursor()

    def go_to_line(self):
        line, ok = QInputDialog.getInt(self, "Go to Line", "Enter line number:", 1, step=1)
        if not ok:
            return
        block: QTextBlock = self.document().findBlockByLineNumber(line - 1)
        if block.isValid():
            cursor: QTextCursor = QTextCursor(block)
            self.setTextCursor(cursor)
            self.centerCursor()

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

    def change_text_size(self, increase: bool = True):  # noqa: FBT001, FBT002
        """Change the font size of the code editor."""
        font: QFont = self.font()
        size: int = font.pointSize()
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

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Tab:
            cursor = self.textCursor()
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
            selected_text = cursor.selectedText()
            if selected_text in self.snippets:
                cursor.removeSelectedText()
                cursor.insertText(self.snippets[selected_text]["content"])
            else:
                super().keyPressEvent(event)
        elif (
            self.completer
            and self.completer.popup().isVisible()
            and event.key() in (
                Qt.Key.Key_Enter,
                Qt.Key.Key_Return,
                Qt.Key.Key_Escape,
                Qt.Key.Key_Tab,
                Qt.Key.Key_Backtab,
            )
        ):
            self.insert_completion(self.completer.currentCompletion())
            self.completer.popup().hide()
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
            self.completer.popup().hide()
            return

        if completion_prefix != self.completer.completionPrefix():
            self.completer.setCompletionPrefix(completion_prefix)
            self.completer.popup().setCurrentIndex(self.completer.completionModel().index(0, 0))

        cr: QRect = self.cursorRect()
        cr.setWidth(self.completer.popup().sizeHintForColumn(0) + self.completer.popup().verticalScrollBar().sizeHint().width())
        self.completer.complete(cr)

    def focusInEvent(self, event: QFocusEvent):
        if self.completer:
            self.completer.setWidget(self)
        super().focusInEvent(event)


class LineNumberArea(QWidget):
    def __init__(self, editor: CodeEditor):
        super().__init__(editor)
        self._editor: CodeEditor = editor

    def sizeHint(self) -> QSize:
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event: QPaintEvent):
        self._editor.line_number_area_paint_event(event)


class NSSCodeEditor(CodeEditor):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.load_settings()

    def load_settings(self):
        self.restoreGeometry(QSettings().value("NSSCodeEditor/geometry", self.saveGeometry()))  # type: ignore[arg-type]

    def save_settings(self):
        QSettings().setValue("NSSCodeEditor/geometry", self.saveGeometry())

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        self.insert_text_at_position(event.mimeData().text(), event.pos())

    def insert_text_at_position(self, text: str, pos: QPoint):
        cursor = self.cursorForPosition(pos)
        cursor.insertText(text)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.save_settings()

    def moveEvent(self, event: QMoveEvent):
        super().moveEvent(event)
        self.save_settings()


class WebViewEditor(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        try:
            from qtpy.QtWebEngineWidgets import QWebEngineView  # pyright: ignore[reportPrivateImportUsage]

            self.web_view: QWebEngineView = QWebEngineView(self)
            layout.addWidget(self.web_view)
        except ImportError:
            label = QLabel("WebEngine not available. Please install QtWebEngine.", self)
            layout.addWidget(label)

    def load_url(self, url: str):
        from qtpy.QtCore import QUrl
        from qtpy.QtWebEngineCore import QWebEngineHttpRequest

        if self.web_view:
            get_request = QWebEngineHttpRequest(QUrl(url), QWebEngineHttpRequest.Method.Get)
            self.web_view.load(get_request)
