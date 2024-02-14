from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.misc import ResRef
from pykotor.resource.formats.gff import write_gff
from pykotor.resource.generics.utt import UTT, dismantle_utt, read_utt
from pykotor.resource.type import ResourceType
from toolset.data.installation import HTInstallation
from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    import os

    from PyQt5.QtWidgets import QWidget


class UTTEditor(Editor):
    def __init__(self, parent: QWidget | None, installation: HTInstallation | None = None):
        """Initialize the trigger editor window.

        Args:
        ----
            parent: {Parent widget}
            installation: {Installation object}.

        Processing Logic:
        ----------------
            - Initialize the base editor window
            - Set up the UI from the designer file
            - Connect menu and signal handlers
            - Load data from the provided installation if given
            - Initialize an empty UTT object.
        """
        supported = [ResourceType.UTT]
        super().__init__(parent, "Trigger Editor", "trigger", supported, supported, installation)

        from toolset.uic.editors.utt import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()
        self._setupInstallation(installation)

        self._utt = UTT()

        self.new()

    def _setupSignals(self):
        self.ui.tagGenerateButton.clicked.connect(self.generateTag)
        self.ui.resrefGenerateButton.clicked.connect(self.generateResref)

    def _setupInstallation(self, installation: HTInstallation):
        self._installation = installation
        self.ui.nameEdit.setInstallation(installation)

        cursors = installation.htGetCache2DA(HTInstallation.TwoDA_CURSORS)
        factions = installation.htGetCache2DA(HTInstallation.TwoDA_FACTIONS)
        traps = installation.htGetCache2DA(HTInstallation.TwoDA_TRAPS)

        self.ui.cursorSelect.setItems(cursors.get_column("label"))
        self.ui.factionSelect.setItems(factions.get_column("label"))
        self.ui.trapSelect.setItems(traps.get_column("label"))

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes):
        super().load(filepath, resref, restype, data)

        utt = read_utt(data)
        self._loadUTT(utt)

    def _loadUTT(self, utt: UTT):
        """Loads UTT data into UI elements.

        Args:
        ----
            utt: UTT - UTT object to load data from

        Loads UTT data:{
            - Sets name, tag, resref from utt
            - Sets cursor, type indexes from utt
            - Sets trap properties from utt
            - Sets scripts from utt
            - Sets comments from utt
        }.
        """
        self._utt = utt

        # Basic
        self.ui.nameEdit.setLocstring(utt.name)
        self.ui.tagEdit.setText(utt.tag)
        self.ui.resrefEdit.setText(utt.resref.get())
        self.ui.cursorSelect.setCurrentIndex(utt.cursor_id)
        self.ui.typeSelect.setCurrentIndex(utt.type_id)

        # Advanced
        self.ui.autoRemoveKeyCheckbox.setChecked(utt.auto_remove_key)
        self.ui.keyEdit.setText(utt.key_name)
        self.ui.factionSelect.setCurrentIndex(utt.faction_id)
        self.ui.highlightHeightSpin.setValue(utt.highlight_height)

        # Trap
        self.ui.isTrapCheckbox.setChecked(utt.is_trap)
        self.ui.activateOnceCheckbox.setChecked(utt.trap_once)
        self.ui.detectableCheckbox.setChecked(utt.trap_detectable)
        self.ui.detectDcSpin.setValue(utt.trap_detect_dc)
        self.ui.disarmableCheckbox.setChecked(utt.trap_disarmable)
        self.ui.disarmDcSpin.setValue(utt.trap_disarm_dc)
        self.ui.trapSelect.setCurrentIndex(utt.trap_type)

        # Scripts
        self.ui.onClickEdit.setText(utt.on_click.get())
        self.ui.onDisarmEdit.setText(utt.on_disarm.get())
        self.ui.onEnterEdit.setText(utt.on_enter.get())
        self.ui.onExitEdit.setText(utt.on_exit.get())
        self.ui.onHeartbeatEdit.setText(utt.on_heartbeat.get())
        self.ui.onTrapTriggeredEdit.setText(utt.on_trap_triggered.get())
        self.ui.onUserDefinedEdit.setText(utt.on_user_defined.get())

        # Comments
        self.ui.commentsEdit.setPlainText(utt.comment)

    def build(self) -> tuple[bytes, bytes]:
        """Builds an UTT from UI input.

        Returns
        -------
            tuple[bytes, bytes]: A tuple containing the GFF data (bytes) and any errors (bytes).

        Processing Logic:
        ----------------
        - Gets input from various UI elements like name, tag, scripts etc and populates an UTT object
        - Serializes the UTT to GFF format
        - Returns the GFF data and any errors
        """
        utt = self._utt

        # Basic
        utt.name = self.ui.nameEdit.locstring()
        utt.tag = self.ui.tagEdit.text()
        utt.resref = ResRef(self.ui.resrefEdit.text())
        utt.cursor_id = self.ui.cursorSelect.currentIndex()
        utt.type_id = self.ui.typeSelect.currentIndex()

        # Advanced
        utt.auto_remove_key = self.ui.autoRemoveKeyCheckbox.isChecked()
        utt.key_name = self.ui.keyEdit.text()
        utt.faction_id = self.ui.factionSelect.currentIndex()
        utt.highlight_height = self.ui.highlightHeightSpin.value()

        # Trap
        utt.is_trap = self.ui.isTrapCheckbox.isChecked()
        utt.trap_once = self.ui.activateOnceCheckbox.isChecked()
        utt.trap_detectable = self.ui.detectableCheckbox.isChecked()
        utt.trap_detect_dc = self.ui.detectDcSpin.value()
        utt.trap_disarmable = self.ui.disarmableCheckbox.isChecked()
        utt.trap_disarm_dc = self.ui.disarmDcSpin.value()
        utt.trap_type = self.ui.trapSelect.currentIndex()

        # Scripts
        utt.on_click = ResRef(self.ui.onClickEdit.text())
        utt.on_disarm = ResRef(self.ui.onDisarmEdit.text())
        utt.on_enter = ResRef(self.ui.onEnterEdit.text())
        utt.on_exit = ResRef(self.ui.onExitEdit.text())
        utt.on_heartbeat = ResRef(self.ui.onHeartbeatEdit.text())
        utt.on_trap_triggered = ResRef(self.ui.onTrapTriggeredEdit.text())
        utt.on_user_defined = ResRef(self.ui.onUserDefinedEdit.text())

        # Comments
        utt.comment = self.ui.commentsEdit.toPlainText()

        data = bytearray()
        gff = dismantle_utt(utt)
        write_gff(gff, data)

        return data, b""

    def new(self):
        super().new()
        self._loadUTT(UTT())

    def changeName(self):
        dialog = LocalizedStringDialog(self, self._installation, self.ui.nameEdit.locstring)
        if dialog.exec_():
            self._loadLocstring(self.ui.nameEdit, dialog.locstring)

    def generateTag(self):
        if self.ui.resrefEdit.text() == "":
            self.generateResref()
        self.ui.tagEdit.setText(self.ui.resrefEdit.text())

    def generateResref(self):
        if self._resref is not None and self._resref != "":
            self.ui.resrefEdit.setText(self._resref)
        else:
            self.ui.resrefEdit.setText("m00xx_trg_000")
