from __future__ import annotations

import os
from typing import TYPE_CHECKING, Optional, Tuple

from PyQt5.QtWidgets import QPlainTextEdit, QWidget

from pykotor.common.misc import decode_bytes_with_fallbacks
from pykotor.resource.type import ResourceType
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    from data.installation import HTInstallation


class TXTEditor(Editor):
    def __init__(self, parent: Optional[QWidget], installation: HTInstallation | None = None):
        """Initialize the text editor
        Args:
            parent: {Parent widget}
            installation: {Installation object}.

        Returns
        -------
            None
        Initializes the text editor window:
            - Sets supported file types
            - Initializes parent class
            - Sets initial window size
            - Loads UI from designer file
            - Sets up menus
            - Connects signals
            - Opens new empty document.
        """
        supported = [ResourceType.TXT, ResourceType.TXI, ResourceType.LYT, ResourceType.VIS, ResourceType.NSS]
        super().__init__(parent, "Text Editor", "none", supported, supported, installation)
        self.resize(400, 250)

        self._wordWrap: bool = False

        from toolset.uic.editors.txt import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()

        self.new()

    def _setupSignals(self) -> None:
        self.ui.actionWord_Wrap.triggered.connect(self.toggleWordWrap)

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes) -> None:
        super().load(filepath, resref, restype, data)
        self.ui.textEdit.setPlainText(decode_bytes_with_fallbacks(data))

    def build(self) -> Tuple[bytes, bytes]:
        return self.ui.textEdit.toPlainText().replace("\r\n", os.linesep).replace("\n", os.linesep).encode(), b""

    def new(self) -> None:
        super().new()
        self.ui.textEdit.setPlainText("")

    def toggleWordWrap(self) -> None:
        self._wordWrap = not self._wordWrap
        self.ui.actionWord_Wrap.setChecked(self._wordWrap)
        self.ui.textEdit.setLineWrapMode(QPlainTextEdit.WidgetWidth if self._wordWrap else QPlainTextEdit.NoWrap)
