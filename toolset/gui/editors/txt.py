from __future__ import annotations

from typing import TYPE_CHECKING, Optional

try:
    import chardet
except ImportError:
    chardet = None
from PyQt5.QtWidgets import QPlainTextEdit, QWidget

from pykotor.resource.type import ResourceType
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    from pykotor.extract.installation import Installation


class TXTEditor(Editor):
    def __init__(self, parent: Optional[QWidget], installation: Optional[Installation] = None):
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

    def load(self, filepath: str, resref: str, restype: ResourceType, data: bytes) -> None:
        super().load(filepath, resref, restype, data)
        try:
            # Try UTF-8 First - KotOR files typically do not use UTF8
            self.ui.textEdit.setPlainText(data.decode("windows-1252"))
        except UnicodeDecodeError:
            # Slower, auto detect encoding
            encoding = (chardet.detect(data) or {}).get("encoding") if chardet else "utf8"
            try:
                self.ui.textEdit.setPlainText(data.decode(encoding))
            except UnicodeDecodeError:
                try:
                    self.ui.textEdit.setPlainText(data.decode("cp-1252"))
                except UnicodeDecodeError:
                    self.ui.textEdit.setPlainText(data.decode(encoding="windows-1252", errors="replace"))

    def build(self) -> tuple[bytes, bytes]:
        return self.ui.textEdit.toPlainText().replace("\n", "\r\n").encode(), b""

    def new(self) -> None:
        super().new()
        self.ui.textEdit.setPlainText("")

    def toggleWordWrap(self) -> None:
        self._wordWrap = not self._wordWrap
        self.ui.actionWord_Wrap.setChecked(self._wordWrap)
        self.ui.textEdit.setLineWrapMode(QPlainTextEdit.WidgetWidth if self._wordWrap else QPlainTextEdit.NoWrap)
