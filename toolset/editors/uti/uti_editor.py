from typing import List

from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QWidget
from pykotor.resource.formats.gff import load_gff, write_gff
from pykotor.resource.generics.utd import construct_utd, UTD, dismantle_utd
from pykotor.resource.type import ResourceType

from data.installation import HTInstallation
from editors.editor import Editor


class UTIEditor(Editor):
    def __init__(self, parent: QWidget, installation: HTInstallation = None):
        supported = [ResourceType.UTD]
        super().__init__(parent, "Door Editor", supported, supported, installation)

        self.ui = uti_editor_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_menus()

        iconPath = ":/images/icons/k2/creature.png" if self._installation.tsl else ":/images/icons/k1/creature.png"
        self.setWindowIcon(QIcon(QPixmap(iconPath)))

        self.ui.nameChangeButton.clicked.connect(self.changeName)
        self.ui.tagGenerateButton.clicked.connect(self.generateTag)
        self.ui.conversationModifyButton.clicked.connect(self.editConversation)
        self.ui.inventoryButton.clicked.connect(self.openInventory)

        self.setInstallation(installation)

        self._utd = UTD()

        self.new()

    def load(self, filepath: str, resref: str, restype: ResourceType, data: bytes) -> None:
        super().load(filepath, resref, restype, data)

        utd = construct_utd(load_gff(data))
        self._loadUTC(utd)

        self.updateItemCount()

    def _loadUTD(self, utd: UTD):
        self._utd = utd

    def build(self) -> bytes:
        utd = self._utd

        data = bytearray()
        gff = dismantle_utd(utd)
        write_gff(gff, data)

        return data

    def changeName(self):
        ...

    def generateTag(self):
        ...

    def editConversation(self):
        ...

    def openInventory(self):
        ...

