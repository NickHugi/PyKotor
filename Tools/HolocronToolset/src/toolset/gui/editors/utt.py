from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

import qtpy

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

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.editors.utt import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.editors.utt import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.editors.utt import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.editors.utt import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()
        if installation is not None:  # will only be none in the unittests
            self._setupInstallation(installation)

        self._utt: UTT = UTT()

        self.new()

    def _setupSignals(self):
        self.ui.tagGenerateButton.clicked.connect(self.generateTag)
        self.ui.resrefGenerateButton.clicked.connect(self.generateResref)

    def _setupInstallation(
        self,
        installation: HTInstallation,
    ):
        self._installation = installation
        self.ui.nameEdit.setInstallation(installation)

        cursors: TwoDA | None = installation.htGetCache2DA(HTInstallation.TwoDA_CURSORS)
        factions: TwoDA | None = installation.htGetCache2DA(HTInstallation.TwoDA_FACTIONS)
        traps: TwoDA | None = installation.htGetCache2DA(HTInstallation.TwoDA_TRAPS)

        if cursors:
            self.ui.cursorSelect.setContext(cursors, installation, HTInstallation.TwoDA_CURSORS)
        if factions:
            self.ui.factionSelect.setContext(factions, installation, HTInstallation.TwoDA_FACTIONS)
        if traps:
            self.ui.trapSelect.setContext(traps, installation, HTInstallation.TwoDA_TRAPS)

        self.ui.cursorSelect.setItems(cursors.get_column("label"))
        self.ui.factionSelect.setItems(factions.get_column("label"))
        self.ui.trapSelect.setItems(traps.get_column("label"))

        self.relevant_script_resnames = sorted(
            iter(
                {
                    res.resname().lower()
                    for res in self._installation.getRelevantResources(
                        ResourceType.NCS, self._filepath
                    )
                }
            )
        )

        self.ui.onClickEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onDisarmEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onEnterEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onExitEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onTrapTriggeredEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onHeartbeatEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onUserDefinedEdit.populateComboBox(self.relevant_script_resnames)

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
        self.ui.nameEdit.setLocstring(utt.name)
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
        self.ui.onClickEdit.setComboBoxText(str(utt.on_click))
        self.ui.onDisarmEdit.setComboBoxText(str(utt.on_disarm))
        self.ui.onEnterEdit.setComboBoxText(str(utt.on_enter))
        self.ui.onExitEdit.setComboBoxText(str(utt.on_exit))
        self.ui.onHeartbeatEdit.setComboBoxText(str(utt.on_heartbeat))
        self.ui.onTrapTriggeredEdit.setComboBoxText(str(utt.on_trap_triggered))
        self.ui.onUserDefinedEdit.setComboBoxText(str(utt.on_user_defined))

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
        utt.on_enter = ResRef(self.ui.onEnterEdit.currentText())
        utt.on_exit = ResRef(self.ui.onExitEdit.currentText())
        utt.on_heartbeat = ResRef(self.ui.onHeartbeatEdit.currentText())
        utt.on_trap_triggered = ResRef(self.ui.onTrapTriggeredEdit.currentText())
        utt.on_user_defined = ResRef(self.ui.onUserDefinedEdit.currentText())

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
        dialog = LocalizedStringDialog(self, self._installation, self.ui.nameEdit.locstring())
        if dialog.exec_():
            self._loadLocstring(self.ui.nameEdit.ui.locstringText, dialog.locstring)

    def generateTag(self):
        if not self.ui.resrefEdit.text():
            self.generateResref()
        self.ui.tagEdit.setText(self.ui.resrefEdit.text())

    def generateResref(self):
        if self._resname:
            self.ui.resrefEdit.setText(self._resname)
        else:
            self.ui.resrefEdit.setText("m00xx_trg_000")
