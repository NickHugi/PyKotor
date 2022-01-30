import chardet
from pykotor.resource.type import ResourceType

from editors.editor import Editor
from editors.txt import txt_editor_ui


class TXTEditor(Editor):
    def __init__(self, parent):
        supported = [ResourceType.TXT, ResourceType.TXI, ResourceType.LYT, ResourceType.VIS, ResourceType.NSS]
        super().__init__(parent, "Text Editor", supported, supported)
        self.resize(400, 250)

        self.ui = txt_editor_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_menus()

        self.new()

    def load(self, filepath: str, resref: str, restype: ResourceType, data: bytes) -> None:
        super().load(filepath, resref, restype, data)
        try:
            # Try UTF-8 First - KotOR files typically do not use UTF8
            self.ui.textEdit.setPlainText(data.decode('utf-8'))
        except:
            # Slower, auto detect encoding
            encoding = chardet.detect(data)['encoding']
            self.ui.textEdit.setPlainText(data.decode(encoding))

    def build(self) -> bytes:
        return self.ui.textEdit.toPlainText().encode()

    def new(self) -> None:
        super().new()
        self.ui.textEdit.setPlainText("")
