from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import qtpy

from loggerplus import RobustLogger
from qtpy.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat

if qtpy.QT5:
    from qtpy.QtCore import QRegExp  # pyright: ignore[reportAttributeAccessIssue]
else:
    from qtpy.QtCore import QRegularExpression as QRegExp  # pyright: ignore[reportAttributeAccessIssue]

if TYPE_CHECKING:
    from qtpy.QtGui import QTextDocument

    from toolset.data.installation import HTInstallation


class SyntaxHighlighter(QSyntaxHighlighter):
    KEYWORDS: ClassVar[list[str]] = [
        "#include",
        "action",
        "effect",
        "FALSE",
        "float",
        "for",
        "if",
        "int",
        "location",
        "object",
        "return",
        "string",
        "talent",
        "TRUE",
        "vector",
        "void",
        "while",
    ]

    OPERATORS: ClassVar[list[str]] = ["=", "==", "!=", "<", "<=", ">", ">=", "!", "\\+", "-", "/", "<<", ">>", "\\&", "\\|"]

    COMMENT_BLOCK_START = QRegExp("/\\*")
    COMMENT_BLOCK_END = QRegExp("\\*/")

    BRACES: ClassVar[list[str]] = ["\\{", "\\}", "\\(", "\\)", "\\[", "\\]"]

    def __init__(
        self,
        parent: QTextDocument,
        installation: HTInstallation | None = None,
    ):
        super().__init__(parent)

        self._installation: HTInstallation | None = installation
        self._is_tsl: bool = installation.tsl if installation else False
        self._setupRules()

    def _setupRules(self):
        self.rules = []

        keyword_format: QTextCharFormat = self._format("blue")
        keywords: list[str] = ["int", "float", "string", "object", "void", "if", "else", "while", "for", "return"]
        self.rules.extend((QRegExp(f"\\b{w}\\b"), keyword_format) for w in keywords)

        function_format: QTextCharFormat = self._format("darkGreen")
        self.rules.append((QRegExp("\\b[A-Za-z0-9_]+(?=\\()"), function_format))

        number_format: QTextCharFormat = self._format("brown")
        self.rules.append((QRegExp("\\b[0-9]+\\b"), number_format))

        string_format: QTextCharFormat = self._format("darkMagenta")
        self.rules.append((QRegExp('".*"'), string_format))

        comment_format: QTextCharFormat = self._format("gray", italic=True)
        self.rules.append((QRegExp("//[^\n]*"), comment_format))

        self.multiline_comment_format = comment_format
        self.multiline_comment_start = QRegExp("/\\*")
        self.multiline_comment_end = QRegExp("\\*/")

    def _format(
        self,
        color: str,
        bold: bool = False,  # noqa: FBT001, FBT002
        italic: bool = False,  # noqa: FBT001, FBT002
    ) -> QTextCharFormat:
        fmt: QTextCharFormat = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Weight.Bold)
        if italic:
            fmt.setFontItalic(True)
        return fmt

    def highlightBlock(
        self,
        text: str,
    ):
        for pattern, format in self.rules:
            if qtpy.QT5:
                # Qt5: QRegExp uses indexIn and matchedLength
                expression = QRegExp(pattern)
                index = 0
                while index >= 0:
                    index = expression.indexIn(text, index)  # pyright: ignore[reportAttributeAccessIssue]
                    if index >= 0:
                        length = expression.matchedLength()  # pyright: ignore[reportAttributeAccessIssue]
                        self.setFormat(index, length, format)
                        index += length
            else:
                # Qt6: QRegularExpression needs explicit anchoring
                expression = QRegExp(pattern)
                it = expression.globalMatch(text)
                while it.hasNext():
                    match = it.next()
                    self.setFormat(match.capturedStart(), match.capturedLength(), format)

        self.setCurrentBlockState(0)

        # For multiline comments, use string methods instead of regex for compatibility
        start_index: int = 0
        if self.previousBlockState() != 1:
            try:
                start_index = text.index("/*")  # Use literal instead of pattern()
            except ValueError:
                start_index = -1

        while start_index >= 0:
            try:
                end_index: int = text.index("*/", start_index)  # Use literal instead of pattern()
            except ValueError:
                end_index = -1

            if end_index == -1:
                self.setCurrentBlockState(1)
                comment_length = len(text) - start_index
            else:
                comment_length = end_index - start_index + 2  # Use fixed length of "*/"

            self.setFormat(start_index, comment_length, self.multiline_comment_format)
            try:
                start_index = text.index("/*", start_index + comment_length)
            except ValueError:
                start_index = -1

    def update_rules(
        self,
        is_tsl: bool,  # noqa: FBT001
    ):
        self._is_tsl = is_tsl
        self._setupRules()
        try:
            self.rehighlight()
        except RuntimeError:  # wrapped C/C++ object of type 'QTextDocument' has been deleted
            RobustLogger().warning("Failed to rehighlight")
