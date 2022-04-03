from typing import Optional

import chardet
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QWidget
from pykotor.extract.installation import Installation
from pykotor.resource.type import ResourceType

from editors.editor import Editor


class TXTEditor(Editor):
    def __init__(self, parent: QWidget, installation: Optional[Installation] = None):
        supported = [ResourceType.TXT, ResourceType.TXI, ResourceType.LYT, ResourceType.VIS, ResourceType.NSS]
        super().__init__(parent, "Text Editor", "none", supported, supported, installation)
        self.resize(400, 250)

        from editors.txt import txt_editor_ui
        self.ui = txt_editor_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()

        self.new()

    def _setupSignals(self) -> None:
        ...

    def load(self, filepath: str, resref: str, restype: ResourceType, data: bytes) -> None:
        super().load(filepath, resref, restype, data)
        try:
            # Try UTF-8 First - KotOR files typically do not use UTF8
            self.ui.textEdit.setPlainText(data.decode("windows-1252"))
        except:
            # Slower, auto detect encoding
            encoding = chardet.detect(data)['encoding']
            self.ui.textEdit.setPlainText(data.decode(encoding))

    def build(self) -> bytes:
        return self.ui.textEdit.toPlainText().replace("\n", "\r\n").encode()

    def new(self) -> None:
        super().new()
        self.ui.textEdit.setPlainText("")
