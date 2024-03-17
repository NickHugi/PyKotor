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
    def __init__(self, parent: QWidget | None, installation: HTInstallation | None = None):
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
        supported: list[ResourceType] = [ResourceType.TXT, ResourceType.TXI, ResourceType.LYT, ResourceType.VIS, ResourceType.NSS]
        super().__init__(parent, "Text Editor", "none", supported, supported, installation)
        self.resize(400, 250)

        self._wordWrap: bool = False

        from toolset.uic.pyqt5.editors.txt import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()

        self.new()

    def _setupSignals(self):
        self.ui.actionWord_Wrap.triggered.connect(self.toggleWordWrap)

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes):
        super().load(filepath, resref, restype, data)
        self.ui.textEdit.setPlainText(decode_bytes_with_fallbacks(data))

    def build(self) -> tuple[bytes, bytes]:
        return self.ui.textEdit.toPlainText().replace("\r\n", os.linesep).replace("\n", os.linesep).encode(), b""

    def new(self):
        super().new()
        self.ui.textEdit.setPlainText("")

    def toggleWordWrap(self):
        self._wordWrap = not self._wordWrap
        self.ui.actionWord_Wrap.setChecked(self._wordWrap)
        self.ui.textEdit.setLineWrapMode(QPlainTextEdit.WidgetWidth if self._wordWrap else QPlainTextEdit.NoWrap)
