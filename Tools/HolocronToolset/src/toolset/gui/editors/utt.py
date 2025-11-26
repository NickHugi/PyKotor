from __future__ import annotations

from copy import deepcopy
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

    from qtpy.QtWidgets import QWidget

    from pykotor.common.module import GFF
    from pykotor.resource.formats.twoda.twoda_data import TwoDA


class UTTEditor(Editor):
    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation
        | None = None,
    ):
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
        supported = [ResourceType.UTT, ResourceType.BTT]
        super().__init__(parent, "Trigger Editor", "trigger", supported, supported, installation)

        from toolset.uic.qtpy.editors.utt import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_menus()
        self._add_help_action()
        self._setup_signals()
        if installation is not None:  # will only be none in the unittests
            self._setup_installation(installation)
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

        self._utt: UTT = UTT()

        self.new()

    def _setup_signals(self):
        self.ui.tagGenerateButton.clicked.connect(self.generate_tag)
        self.ui.resrefGenerateButton.clicked.connect(self.generate_resref)

    def _setup_installation(
        self,
        installation: HTInstallation,
    ):
        self._installation = installation
        self.ui.nameEdit.set_installation(installation)

        cursors: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_CURSORS)
        factions: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_FACTIONS)
        traps: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_TRAPS)

        if cursors:
            self.ui.cursorSelect.set_context(cursors, installation, HTInstallation.TwoDA_CURSORS)
        if factions:
            self.ui.factionSelect.set_context(factions, installation, HTInstallation.TwoDA_FACTIONS)
        if traps:
            self.ui.trapSelect.set_context(traps, installation, HTInstallation.TwoDA_TRAPS)

        if cursors:
            self.ui.cursorSelect.set_items(cursors.get_column("label"))
        if factions:
            self.ui.factionSelect.set_items(factions.get_column("label"))
        if traps:
            self.ui.trapSelect.set_items(traps.get_column("label"))

        self.relevant_script_resnames: list[str] = sorted(
            iter(
                {
                    res.resname().lower()
                    for res in self._installation.get_relevant_resources(
                        ResourceType.NCS, self._filepath
                    )
                }
            )
        )

        self.ui.onClickEdit.populate_combo_box(self.relevant_script_resnames)
        installation.setup_file_context_menu(self.ui.onClickEdit, [ResourceType.NCS, ResourceType.NSS])
        self.ui.onDisarmEdit.populate_combo_box(self.relevant_script_resnames)
        installation.setup_file_context_menu(self.ui.onDisarmEdit, [ResourceType.NCS, ResourceType.NSS])
        self.ui.onEnterSelect.populate_combo_box(self.relevant_script_resnames)
        installation.setup_file_context_menu(self.ui.onEnterSelect, [ResourceType.NCS, ResourceType.NSS])
        self.ui.onExitSelect.populate_combo_box(self.relevant_script_resnames)
        installation.setup_file_context_menu(self.ui.onExitSelect, [ResourceType.NCS, ResourceType.NSS])
        self.ui.onTrapTriggeredEdit.populate_combo_box(self.relevant_script_resnames)
        installation.setup_file_context_menu(self.ui.onTrapTriggeredEdit, [ResourceType.NCS, ResourceType.NSS])
        self.ui.onHeartbeatSelect.populate_combo_box(self.relevant_script_resnames)
        installation.setup_file_context_menu(self.ui.onHeartbeatSelect, [ResourceType.NCS, ResourceType.NSS])
        self.ui.onUserDefinedSelect.populate_combo_box(self.relevant_script_resnames)
        installation.setup_file_context_menu(self.ui.onUserDefinedSelect, [ResourceType.NCS, ResourceType.NSS])

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        super().load(filepath, resref, restype, data)

        utt: UTT = read_utt(data)
        self._loadUTT(utt)

    def _loadUTT(
        self,
        utt: UTT,
    ):
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
        self.ui.nameEdit.set_locstring(utt.name)
        self.ui.tagEdit.setText(utt.tag)
        self.ui.resrefEdit.setText(str(utt.resref))
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
        self.ui.onClickEdit.set_combo_box_text(str(utt.on_click))
        self.ui.onDisarmEdit.set_combo_box_text(str(utt.on_disarm))
        self.ui.onEnterSelect.set_combo_box_text(str(utt.on_enter))
        self.ui.onExitSelect.set_combo_box_text(str(utt.on_exit))
        self.ui.onHeartbeatSelect.set_combo_box_text(str(utt.on_heartbeat))
        self.ui.onTrapTriggeredEdit.set_combo_box_text(str(utt.on_trap_triggered))
        self.ui.onUserDefinedSelect.set_combo_box_text(str(utt.on_user_defined))

        # Comments
        self.ui.commentsEdit.setPlainText(utt.comment)

    def build(self) -> tuple[bytes, bytes]:
        """Builds an UTT from UI input.

        Returns:
        -------
            tuple[bytes, bytes]: A tuple containing the GFF data (bytes) and any errors (bytes).

        Processing Logic:
        ----------------
        - Gets input from various UI elements like name, tag, scripts etc and populates an UTT object
        - Serializes the UTT to GFF format
        - Returns the GFF data and any errors
        """
        utt: UTT = deepcopy(self._utt)

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
        utt.on_click = ResRef(self.ui.onClickEdit.currentText())
        utt.on_disarm = ResRef(self.ui.onDisarmEdit.currentText())
        utt.on_enter = ResRef(self.ui.onEnterSelect.currentText())
        utt.on_exit = ResRef(self.ui.onExitSelect.currentText())
        utt.on_heartbeat = ResRef(self.ui.onHeartbeatSelect.currentText())
        utt.on_trap_triggered = ResRef(self.ui.onTrapTriggeredEdit.currentText())
        utt.on_user_defined = ResRef(self.ui.onUserDefinedSelect.currentText())

        # Comments
        utt.comment = self.ui.commentsEdit.toPlainText()

        data = bytearray()
        gff: GFF = dismantle_utt(utt)
        write_gff(gff, data)

        return data, b""

    def new(self):
        super().new()
        self._loadUTT(UTT())

    def change_name(self):
        assert self._installation is not None
        dialog = LocalizedStringDialog(self, self._installation, self.ui.nameEdit.locstring())
        if dialog.exec():
            self._load_locstring(self.ui.nameEdit.ui.locstringText, dialog.locstring)

    def generate_tag(self):
        if not self.ui.resrefEdit.text():
            self.generate_resref()
        self.ui.tagEdit.setText(self.ui.resrefEdit.text())

    def generate_resref(self):
        if self._resname:
            self.ui.resrefEdit.setText(self._resname)
        else:
            self.ui.resrefEdit.setText("m00xx_trg_000")
