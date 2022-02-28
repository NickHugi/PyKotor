from typing import List

from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QWidget, QCheckBox, QDoubleSpinBox, QSpinBox, QTableWidgetItem
from pykotor.common.misc import ResRef
from pykotor.resource.formats.gff import load_gff, write_gff
from pykotor.resource.generics.ute import construct_ute, UTE, dismantle_ute, UTECreature
from pykotor.resource.type import ResourceType

from data.installation import HTInstallation
from editors.editor import Editor, LocalizedStringDialog
from editors.ute import ute_editor_ui


class UTEEditor(Editor):
    def __init__(self, parent: QWidget, installation: HTInstallation = None):
        supported = [ResourceType.UTE]
        super().__init__(parent, "Trigger Editor", supported, supported, installation)

        self.ui = ute_editor_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_menus()
        self._setupSignals()

        iconPath = ":/images/icons/k2/trigger.png" if self._installation.tsl else ":/images/icons/k1/trigger.png"
        self.setWindowIcon(QIcon(QPixmap(iconPath)))

        self.setInstallation(installation)

        self._ute = UTE()

        self.new()

    def _setupSignals(self) -> None:
        self.ui.nameChangeButton.clicked.connect(self.changeName)
        self.ui.tagGenerateButton.clicked.connect(self.generateTag)
        self.ui.resrefGenerateButton.clicked.connect(self.generateResref)
        self.ui.infiniteRespawnCheckbox.stateChanged.connect(self.setInfiniteRespawn)
        self.ui.spawnSelect.currentIndexChanged.connect(self.setContinuous)
        self.ui.addCreatureButton.clicked.connect(self.addCreature)
        self.ui.removeCreatureButton.clicked.connect(self.removeSelectedCreature)

    def load(self, filepath: str, resref: str, restype: ResourceType, data: bytes) -> None:
        super().load(filepath, resref, restype, data)

        ute = construct_ute(load_gff(data))
        self._loadUTE(ute)

    def _loadUTE(self, ute: UTE):
        self._ute = ute

        # Basic
        self._loadLocstring(self.ui.nameEdit, ute.name)
        self.ui.tagEdit.setText(ute.tag)
        self.ui.resrefEdit.setText(ute.resref.get())
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
        [self.ui.creatureTable.removeRow(0) for _ in range(self.ui.creatureTable.rowCount())]
        for creature in ute.creatures:
            self.addCreature(creature.resref.get(), creature.appearance_id, creature.challenge_rating, creature.single_spawn)

        # Scripts
        self.ui.onEnterEdit.setText(ute.on_entered.get())
        self.ui.onExitEdit.setText(ute.on_exit.get())
        self.ui.onExhaustedEdit.setText(ute.on_exhausted.get())
        self.ui.onHeartbeatEdit.setText(ute.on_heartbeat.get())
        self.ui.onUserDefinedEdit.setText(ute.on_user_defined.get())

        # Comments
        self.ui.commentsEdit.setPlainText(ute.comment)

    def build(self) -> bytes:
        ute = self._ute

        # Basic
        ute.name = self.ui.nameEdit.locstring
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
            singleCheckbox: QCheckBox = self.ui.creatureTable.cellWidget(i, 0)
            challengeSpin: QDoubleSpinBox = self.ui.creatureTable.cellWidget(i, 1)
            appearanceSpin: QSpinBox = self.ui.creatureTable.cellWidget(i, 2)

            creature = UTECreature()
            creature.resref = ResRef(self.ui.creatureTable.item(i, 3).text())
            creature.single_spawn = singleCheckbox.isChecked()
            creature.appearance_id = appearanceSpin.value()
            creature.challenge_rating = challengeSpin.value()
            ute.creatures.append(creature)

        # Scripts
        ute.on_entered = ResRef(self.ui.onEnterEdit.text())
        ute.on_exit = ResRef(self.ui.onExitEdit.text())
        ute.on_exhausted = ResRef(self.ui.onExhaustedEdit.text())
        ute.on_heartbeat = ResRef(self.ui.onHeartbeatEdit.text())
        ute.on_user_defined = ResRef(self.ui.onUserDefinedEdit.text())

        # Comments
        ute.comment = self.ui.commentsEdit.toPlainText()

        data = bytearray()
        gff = dismantle_ute(ute)
        write_gff(gff, data)

        return data

    def new(self) -> None:
        super().new()
        self._loadUTE(UTE())

    def setInstallation(self, installation: HTInstallation):
        self._installation = installation

        factions = installation.htGetCache2DA(HTInstallation.TwoDA_FACTIONS)
        difficulties = installation.htGetCache2DA(HTInstallation.TwoDA_ENC_DIFFICULTIES)

        self.ui.difficultySelect.clear()
        [self.ui.difficultySelect.addItem(label) for label in difficulties.get_column("label")]

        self.ui.factionSelect.clear()
        [self.ui.factionSelect.addItem(label) for label in factions.get_column("label")]

    def changeName(self) -> None:
        dialog = LocalizedStringDialog(self, self._installation, self.ui.nameEdit.locstring)
        if dialog.exec_():
            self._loadLocstring(self.ui.nameEdit, dialog.locstring)

    def generateTag(self) -> None:
        if self.ui.resrefEdit.text() == "":
            self.generateResref()
        self.ui.tagEdit.setText(self.ui.resrefEdit.text())

    def generateResref(self) -> None:
        if self._resref is not None and self._resref != "":
            self.ui.resrefEdit.setText(self._resref)
        else:
            self.ui.resrefEdit.setText("m00xx_enc_000")

    def setInfiniteRespawn(self):
        if self.ui.infiniteRespawnCheckbox.isChecked():
            self.ui.respawnCountSpin.setMinimum(-1)
            self.ui.respawnCountSpin.setValue(-1)
            self.ui.respawnCountSpin.setEnabled(False)
        else:
            self.ui.respawnCountSpin.setMinimum(0)
            self.ui.respawnCountSpin.setValue(0)
            self.ui.respawnCountSpin.setEnabled(True)

    def setContinuous(self):
        isContinuous = self.ui.spawnSelect.currentIndex() == 1
        self.ui.respawnsCheckbox.setEnabled(isContinuous)
        self.ui.infiniteRespawnCheckbox.setEnabled(isContinuous)
        self.ui.respawnCountSpin.setEnabled(isContinuous)
        self.ui.respawnTimeSpin.setEnabled(isContinuous)

    def addCreature(self, resname: str = "", appearanceId: int = 0, challenge: float = 0.0, singe: bool = False):
        rowId = self.ui.creatureTable.rowCount()
        self.ui.creatureTable.insertRow(rowId)

        singleCheckbox = QCheckBox()
        singleCheckbox.setChecked(singe)
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
            item = self.ui.creatureTable.selectedItems()[0]
            self.ui.creatureTable.removeRow(item.row())
