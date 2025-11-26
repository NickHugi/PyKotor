from __future__ import annotations

import os

from typing import TYPE_CHECKING

from qtpy.QtWidgets import QPlainTextEdit

from pykotor.resource.type import ResourceType
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget

    from toolset.data.installation import HTInstallation


class TXTEditor(Editor):
    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation | None = None,
    ):
        """Initialize the text editor.

        Args:
        ----
            parent: {Parent widget}
            installation: {Installation object}.

        Initialize the text editor window:
            - Sets supported file types
            - Initializes parent class
            - Sets initial window size
            - Loads UI from designer file
            - Sets up menus
            - Connects signals
            - Opens new empty document.
        """
        supported: list[ResourceType] = [member for member in ResourceType if member.contents == "plaintext"]
        super().__init__(parent, "Text Editor", "none", supported, supported, installation)
        self.resize(400, 250)

        self._word_wrap: bool = False

        from toolset.uic.qtpy.editors.txt import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_menus()
        self._add_help_action()
        self._setup_signals()
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

        self.new()

    def _setup_signals(self):
        self.ui.actionWord_Wrap.triggered.connect(self.toggle_word_wrap)

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        super().load(filepath, resref, restype, data)
        self.ui.textEdit.setPlainText(decode_bytes_with_fallbacks(data))

    def build(self) -> tuple[bytes, bytes]:
        text = self.ui.textEdit.toPlainText().replace("\r\n", os.linesep).replace("\n", os.linesep)
        # Encode with proper error handling
        try:
            return text.encode("utf-8"), b""
        except UnicodeEncodeError:
            try:
                return text.encode("windows-1252", errors="replace"), b""
            except UnicodeEncodeError:
                return text.encode("latin-1", errors="replace"), b""

    def new(self):
        super().new()
        self.ui.textEdit.setPlainText("")

    def toggle_word_wrap(self):
        self._word_wrap = not self._word_wrap
        self.ui.actionWord_Wrap.setChecked(self._word_wrap)
        self.ui.textEdit.setLineWrapMode(
            QPlainTextEdit.LineWrapMode.WidgetWidth
            if self._word_wrap
            else QPlainTextEdit.LineWrapMode.NoWrap
        )
