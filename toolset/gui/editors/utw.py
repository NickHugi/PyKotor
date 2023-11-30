from typing import Optional, Tuple

from PyQt5.QtWidgets import QWidget

from gui.dialogs.edit.locstring import LocalizedStringDialog
from pykotor.common.misc import ResRef
from pykotor.resource.formats.gff import write_gff
from pykotor.resource.generics.utw import UTW, dismantle_utw, read_utw
from pykotor.resource.type import ResourceType

from data.installation import HTInstallation
from gui.editor import Editor


class UTWEditor(Editor):
    def __init__(self, parent: Optional[QWidget], installation: HTInstallation = None):
        supported = [ResourceType.UTW]
        super().__init__(parent, "Waypoint Editor", "waypoint", supported, supported, installation)

        from toolset.uic.editors.utw import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()
        self._setupInstallation(installation)

        self._utw = UTW()

        self.new()

    def _setupSignals(self) -> None:
        self.ui.tagGenerateButton.clicked.connect(self.generateTag)
        self.ui.resrefGenerateButton.clicked.connect(self.generateResref)
        self.ui.noteChangeButton.clicked.connect(self.changeNote)

    def _setupInstallation(self, installation: HTInstallation):
        self._installation = installation
        self.ui.nameEdit.setInstallation(installation)

    def load(self, filepath: str, resref: str, restype: ResourceType, data: bytes) -> None:
        super().load(filepath, resref, restype, data)

        utw = read_utw(data)
        self._loadUTW(utw)

    def _loadUTW(self, utw: UTW):
        self._utw = utw

        # Basic
        self.ui.nameEdit.setLocstring(utw.name)
        self.ui.tagEdit.setText(utw.tag)
        self.ui.resrefEdit.setText(utw.resref.get())

        # Advanced
        self.ui.isNoteCheckbox.setChecked(utw.has_map_note)
        self.ui.noteEnabledCheckbox.setChecked(utw.map_note_enabled)
        self._loadLocstring(self.ui.noteEdit, utw.map_note)

        # Comments
        self.ui.commentsEdit.setPlainText(utw.comment)

    def build(self) -> Tuple[bytes, bytes]:
        utw = self._utw

        utw.name = self.ui.nameEdit.locstring()
        utw.tag = self.ui.tagEdit.text()
        utw.resref = ResRef(self.ui.resrefEdit.text())
        utw.has_map_note = self.ui.isNoteCheckbox.isChecked()
        utw.map_note_enabled = self.ui.noteEnabledCheckbox.isChecked()
        utw.map_note = self.ui.noteEdit.locstring
        utw.comment = self.ui.commentsEdit.toPlainText()

        data = bytearray()
        gff = dismantle_utw(utw)
        write_gff(gff, data)

        return data, b''

    def new(self) -> None:
        super().new()
        self._loadUTW(UTW())

    def changeName(self) -> None:
        dialog = LocalizedStringDialog(self, self._installation, self.ui.nameEdit.locstring)
        if dialog.exec_():
            self._loadLocstring(self.ui.nameEdit, dialog.locstring)

    def changeNote(self) -> None:
        dialog = LocalizedStringDialog(self, self._installation, self.ui.noteEdit.locstring)
        if dialog.exec_():
            self._loadLocstring(self.ui.noteEdit, dialog.locstring)

    def generateTag(self) -> None:
        if self.ui.resrefEdit.text() == "":
            self.generateResref()
        self.ui.tagEdit.setText(self.ui.resrefEdit.text())

    def generateResref(self) -> None:
        if self._resref is not None and self._resref != "":
            self.ui.resrefEdit.setText(self._resref)
        else:
            self.ui.resrefEdit.setText("m00xx_way_000")
