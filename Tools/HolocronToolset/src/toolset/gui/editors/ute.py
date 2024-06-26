from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, cast

import qtpy

from qtpy.QtWidgets import QCheckBox, QDoubleSpinBox, QSpinBox, QTableWidgetItem

from pykotor.common.misc import ResRef
from pykotor.resource.formats.gff import write_gff
from pykotor.resource.generics.ute import UTE, UTECreature, dismantle_ute, read_ute
from pykotor.resource.type import ResourceType
from toolset.data.installation import HTInstallation
from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    import os

    from qtpy.QtWidgets import QWidget

    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.formats.twoda.twoda_data import TwoDA


class UTEEditor(Editor):
    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation | None = None,
    ):
        """Initialize the trigger editor window.

        Args:
        ----
            parent: {The parent widget of the editor}
            installation: {The installation object being edited}.

        Processing Logic:
        ----------------
            - Call super().__init__ to initialize base editor class
            - Load UI from designer file
            - Set up menus, signals and installation
            - Initialize UTE object
            - Call new() to start with a blank trigger.
        """
        supported: list[ResourceType] = [ResourceType.UTE, ResourceType.BTE]
        super().__init__(parent, "Trigger Editor", "trigger", supported, supported, installation)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.editors.ute import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.editors.ute import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.editors.ute import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.editors.ute import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()
        if installation is not None:  # will only be none in the unittests
            self._setupInstallation(installation)

        self._ute: UTE = UTE()

        self.new()

    def _setupSignals(self):
        """Connects UI signals to handler functions.

        Processing Logic:
        ----------------
            - Connects the tagGenerateButton clicked signal to generateTag handler
            - Connects the resrefGenerateButton clicked signal to generateResref handler
            - Connects the infiniteRespawnCheckbox stateChanged signal to setInfiniteRespawn handler
            - Connects the spawnSelect currentIndexChanged signal to setContinuous handler
            - Connects the addCreatureButton clicked signal to addCreature handler
            - Connects the removeCreatureButton clicked signal to removeSelectedCreature handler.
        """
        self.ui.tagGenerateButton.clicked.connect(self.generateTag)
        self.ui.resrefGenerateButton.clicked.connect(self.generateResref)
        self.ui.infiniteRespawnCheckbox.stateChanged.connect(self.setInfiniteRespawn)
        self.ui.spawnSelect.currentIndexChanged.connect(self.setContinuous)
        self.ui.addCreatureButton.clicked.connect(self.addCreature)
        self.ui.removeCreatureButton.clicked.connect(self.removeSelectedCreature)

    def _setupInstallation(
        self,
        installation: HTInstallation,
    ):
        """Sets up the installation details in the UI.

        Args:
        ----
            installation: {The installation object being edited}

        Processing Logic:
        ----------------
            - Sets the internal installation object reference
            - Populates the name field with the installation details
            - Fetches the faction and difficulty data from the installation
            - Clears and populates the dropdowns with the faction and difficulty labels
        """
        self._installation = installation
        self.ui.nameEdit.setInstallation(installation)

        difficulties: TwoDA = installation.htGetCache2DA(HTInstallation.TwoDA_ENC_DIFFICULTIES)
        self.ui.difficultySelect.clear()
        self.ui.difficultySelect.setItems(difficulties.get_column("label"))
        self.ui.difficultySelect.setContext(difficulties, installation, HTInstallation.TwoDA_ENC_DIFFICULTIES)

        factions: TwoDA = installation.htGetCache2DA(HTInstallation.TwoDA_FACTIONS)
        self.ui.factionSelect.clear()
        self.ui.factionSelect.setItems(factions.get_column("label"))
        self.ui.factionSelect.setContext(factions, installation, HTInstallation.TwoDA_FACTIONS)

        self._installation.setupFileContextMenu(self.ui.onEnterEdit, [ResourceType.NSS, ResourceType.NCS])
        self._installation.setupFileContextMenu(self.ui.onExitEdit, [ResourceType.NSS, ResourceType.NCS])
        self._installation.setupFileContextMenu(self.ui.onExhaustedEdit, [ResourceType.NSS, ResourceType.NCS])
        self._installation.setupFileContextMenu(self.ui.onHeartbeatEdit, [ResourceType.NSS, ResourceType.NCS])
        self._installation.setupFileContextMenu(self.ui.onUserDefinedEdit, [ResourceType.NSS, ResourceType.NCS])

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        super().load(filepath, resref, restype, data)

        ute = read_ute(data)
        self._loadUTE(ute)

    def _loadUTE(self, ute: UTE):
        """Loads UTE data into UI elements.

        Args:
        ----
            ute (UTE): UTE object to load


        Processing Logic:
        ----------------
            - Sets basic UTE properties like name, tag, etc.
            - Sets advanced properties like active, faction, respawning
            - Loads creatures and adds them to creature table
            - Sets script fields
            - Sets comment text.
        """
        self._ute = ute

        # Basic
        self.ui.nameEdit.setLocstring(ute.name)
        self.ui.tagEdit.setText(ute.tag)
        self.ui.resrefEdit.setText(str(ute.resref))
        self.ui.difficultySelect.setCurrentIndex(ute.difficulty_id)
        self.ui.spawnSelect.setCurrentIndex(int(ute.single_shot))
        self.ui.minCreatureSpin.setValue(ute.rec_creatures)
        self.ui.maxCreatureSpin.setValue(ute.max_creatures)

        # Advanced
        self.ui.activeCheckbox.setChecked(ute.active)
        self.ui.playerOnlyCheckbox.setChecked(ute.player_only)
        self.ui.factionSelect.setCurrentIndex(ute.faction_id)
        self.ui.respawnsCheckbox.setChecked(ute.reset)
        self.ui.infiniteRespawnCheckbox.setChecked(ute.respawns == -1)
        self.ui.respawnTimeSpin.setValue(ute.reset_time)
        self.ui.respawnCountSpin.setValue(ute.respawns)

        # Creatures
        for _ in range(self.ui.creatureTable.rowCount()):
            self.ui.creatureTable.removeRow(0)
        for creature in ute.creatures:
            self.addCreature(str(creature.resref), creature.appearance_id, creature.challenge_rating, creature.single_spawn)

        # Scripts
        self.ui.onEnterEdit.setComboBoxText(str(ute.on_entered))
        self.ui.onExitEdit.setComboBoxText(str(ute.on_exit))
        self.ui.onExhaustedEdit.setComboBoxText(str(ute.on_exhausted))
        self.ui.onHeartbeatEdit.setComboBoxText(str(ute.on_heartbeat))
        self.ui.onUserDefinedEdit.setComboBoxText(str(ute.on_user_defined))

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

        self.ui.onEnterEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onExitEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onExhaustedEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onHeartbeatEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onUserDefinedEdit.populateComboBox(self.relevant_script_resnames)

        # Comments
        self.ui.commentsEdit.setPlainText(ute.comment)

    def build(self) -> tuple[bytes, bytes]:
        """Builds a UTE object from UI data.

        Returns:
        -------
            tuple[bytes, bytes]: A tuple containing the UTE data and an empty string.

        Builds the UTE object by:
            - Setting basic properties from UI elements
            - Setting advanced properties from checkboxes and dropdowns
            - Adding creature details from the creature table
            - Setting script references from line edits
            - Adding comment text
            - Encoding the UTE object into bytes.
        """
        ute: UTE = deepcopy(self._ute)

        # Basic
        ute.name = self.ui.nameEdit.locstring()
        ute.tag = self.ui.tagEdit.text()
        ute.resref = ResRef(self.ui.resrefEdit.text())
        ute.difficulty_id = self.ui.difficultySelect.currentIndex()
        ute.single_shot = bool(self.ui.spawnSelect.currentIndex())
        ute.rec_creatures = self.ui.minCreatureSpin.value()
        ute.max_creatures = self.ui.maxCreatureSpin.value()

        # Advanced
        ute.active = self.ui.activeCheckbox.isChecked()
        ute.player_only = self.ui.playerOnlyCheckbox.isChecked()
        ute.faction_id = self.ui.factionSelect.currentIndex()
        ute.reset = self.ui.respawnsCheckbox.isChecked()
        ute.respawns = self.ui.respawnCountSpin.value()
        ute.reset_time = self.ui.respawnTimeSpin.value()

        # Creatures
        ute.creatures = []
        for i in range(self.ui.creatureTable.rowCount()):
            singleCheckbox = cast(QCheckBox, self.ui.creatureTable.cellWidget(i, 0))
            challengeSpin = cast(QDoubleSpinBox, self.ui.creatureTable.cellWidget(i, 1))
            appearanceSpin = cast(QSpinBox, self.ui.creatureTable.cellWidget(i, 2))

            creature = UTECreature()
            creature.resref = ResRef(self.ui.creatureTable.item(i, 3).text())
            creature.single_spawn = singleCheckbox.isChecked()
            creature.appearance_id = appearanceSpin.value()
            creature.challenge_rating = challengeSpin.value()
            ute.creatures.append(creature)

        # Scripts
        ute.on_entered = ResRef(self.ui.onEnterEdit.currentText())
        ute.on_exit = ResRef(self.ui.onExitEdit.currentText())
        ute.on_exhausted = ResRef(self.ui.onExhaustedEdit.currentText())
        ute.on_heartbeat = ResRef(self.ui.onHeartbeatEdit.currentText())
        ute.on_user_defined = ResRef(self.ui.onUserDefinedEdit.currentText())

        # Comments
        ute.comment = self.ui.commentsEdit.toPlainText()

        data = bytearray()
        gff: GFF = dismantle_ute(ute)
        write_gff(gff, data)

        return data, b""

    def new(self):
        super().new()
        self._loadUTE(UTE())

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
            self.ui.resrefEdit.setText("m00xx_enc_000")

    def setInfiniteRespawn(self):
        if self.ui.infiniteRespawnCheckbox.isChecked():
            self._setInfiniteRespawnMain(val=-1, enabled=False)
        else:
            self._setInfiniteRespawnMain(val=0, enabled=True)

    def _setInfiniteRespawnMain(
        self,
        val: int,
        *,
        enabled: bool,
    ):
        self.ui.respawnCountSpin.setMinimum(val)
        self.ui.respawnCountSpin.setValue(val)
        self.ui.respawnCountSpin.setEnabled(enabled)

    def setContinuous(self):
        isContinuous = self.ui.spawnSelect.currentIndex() == 1
        self.ui.respawnsCheckbox.setEnabled(isContinuous)
        self.ui.infiniteRespawnCheckbox.setEnabled(isContinuous)
        self.ui.respawnCountSpin.setEnabled(isContinuous)
        self.ui.respawnTimeSpin.setEnabled(isContinuous)

    def addCreature(
        self,
        resname: str = "",
        appearanceId: int = 0,
        challenge: float = 0.0,
        single: bool = False,
    ):
        """Adds a new creature to the creature table.

        Args:
        ----
            resname (str): Name of the creature
            appearanceId (int): ID number for the creature's appearance
            challenge (float): Difficulty rating for the creature
            single (bool): Whether the creature is a single creature encounter

        Processing Logic:
        ----------------
            - Gets the current row count of the creature table
            - Inserts a new row at that index
            - Creates widgets for the single checkbox, challenge spinbox, and appearance spinbox
            - Sets the values of the widgets based on function arguments
            - Sets the widgets as the cell widgets in the appropriate columns
            - Sets the creature name as the item in the name column.
        """
        rowId: int = self.ui.creatureTable.rowCount()
        self.ui.creatureTable.insertRow(rowId)

        singleCheckbox = QCheckBox()
        singleCheckbox.setChecked(single)
        challengeSpin = QDoubleSpinBox()
        challengeSpin.setValue(challenge)
        appearanceSpin = QSpinBox()
        appearanceSpin.setValue(appearanceId)

        self.ui.creatureTable.setCellWidget(rowId, 0, singleCheckbox)
        self.ui.creatureTable.setCellWidget(rowId, 1, challengeSpin)
        self.ui.creatureTable.setCellWidget(rowId, 2, appearanceSpin)
        self.ui.creatureTable.setItem(rowId, 3, QTableWidgetItem(resname))

    def removeSelectedCreature(self):
        if self.ui.creatureTable.selectedItems():
            item: QTableWidgetItem = self.ui.creatureTable.selectedItems()[0]
            self.ui.creatureTable.removeRow(item.row())
