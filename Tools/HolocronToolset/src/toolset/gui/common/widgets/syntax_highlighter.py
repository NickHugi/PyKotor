from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from loggerplus import RobustLogger
from qtpy.QtCore import QRegularExpression
from qtpy.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat

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

    COMMENT_BLOCK_START = QRegularExpression("/\\*")
    COMMENT_BLOCK_END = QRegularExpression("\\*/")

    BRACES: ClassVar[list[str]] = ["\\{", "\\}", "\\(", "\\)", "\\[", "\\]"]

    def __init__(
        self,
        parent: QTextDocument,
        installation: HTInstallation | None = None,
    ):
        """Initializes the syntax highlighter.

        Args:
        ----
            parent: QTextDocument: The parent text document
            installation: HTInstallation | None: The installation object

        Initializes styles and rules:
            - Initializes style formats
            - Gets keywords, functions and constants from installation
            - Defines highlighting rules for keywords, functions, constants, operators, braces, numbers, strings and comments
            - Sets rules attribute with compiled rules.
        """
        super().__init__(parent)

        self._installation = installation
        self._is_tsl = installation.tsl if installation else False
        self._setupRules()

    def _setupRules(self):
        self.rules = []

        keyword_format = self._format("blue")
        keywords = ["int", "float", "string", "object", "void", "if", "else", "while", "for", "return"]
        self.rules.extend((QRegularExpression(f"\\b{w}\\b"), keyword_format) for w in keywords)

        function_format = self._format("darkGreen")
        self.rules.append((QRegularExpression("\\b[A-Za-z0-9_]+(?=\\()"), function_format))

        number_format = self._format("brown")
        self.rules.append((QRegularExpression("\\b[0-9]+\\b"), number_format))

        string_format = self._format("darkMagenta")
        self.rules.append((QRegularExpression('".*"'), string_format))

        comment_format = self._format("gray", italic=True)
        self.rules.append((QRegularExpression("//[^\n]*"), comment_format))

        self.multiline_comment_format = comment_format
        self.multiline_comment_start = QRegularExpression("/\\*")
        self.multiline_comment_end = QRegularExpression("\\*/")

    def _format(self, color: str, bold: bool = False, italic: bool = False) -> QTextCharFormat:
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Bold)
        if italic:
            fmt.setFontItalic(True)
        return fmt

    def highlightBlock(self, text: str):
        for pattern, format in self.rules:
            expression = QRegularExpression(pattern)
            it = expression.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

        self.setCurrentBlockState(0)

        startIndex = 0
        if self.previousBlockState() != 1:
            try:
                startIndex = text.index(self.multiline_comment_start.pattern())
            except ValueError:
                startIndex = -1

        while startIndex >= 0:
            try:
                endIndex = text.index(self.multiline_comment_end.pattern(), startIndex)
            except ValueError:
                endIndex = -1

            if endIndex == -1:
                self.setCurrentBlockState(1)
                commentLength = len(text) - startIndex
            else:
                commentLength = endIndex - startIndex + len(self.multiline_comment_end.pattern())

            self.setFormat(startIndex, commentLength, self.multiline_comment_format)
            try:
                startIndex = text.index(self.multiline_comment_start.pattern(), startIndex + commentLength)
            except ValueError:
                startIndex = -1

    def update_rules(self, is_tsl: bool):
        self._is_tsl = is_tsl
        self._setupRules()
        try:
            self.rehighlight()
        except RuntimeError:  # wrapped C/C++ object of type 'QTextDocument' has been deleted
            RobustLogger().warning("Failed to rehighlight")
