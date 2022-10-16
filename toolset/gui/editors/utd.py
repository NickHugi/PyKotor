from typing import Optional, Tuple

from PyQt5.QtWidgets import QWidget, QMessageBox

from gui.dialogs.locstring import LocalizedStringDialog
from pykotor.common.misc import ResRef
from pykotor.common.stream import BinaryWriter
from pykotor.resource.formats.gff import write_gff
from pykotor.resource.generics.dlg import dismantle_dlg, DLG
from pykotor.resource.generics.utd import UTD, dismantle_utd, read_utd
from pykotor.resource.type import ResourceType

from data.installation import HTInstallation
from gui.editor import Editor
from utils.window import openResourceEditor

from toolset.gui.widgets.settings.installations import GlobalSettings
from pykotor.tools import door


class UTDEditor(Editor):
    def __init__(self, parent: Optional[QWidget], installation: HTInstallation = None, *, mainwindow=None):
        supported = [ResourceType.UTD]
        super().__init__(parent, "Door Editor", "door", supported, supported, installation, mainwindow)

        self.globalSettings: GlobalSettings = GlobalSettings()
        self._genericdoors2DA = installation.htGetCache2DA("genericdoors")
        self._utd = UTD()

        from toolset.uic.editors.utd import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()
        self._setupInstallation(installation)

        self.update3dPreview()
        self.new()

    def _setupSignals(self) -> None:
        self.ui.tagGenerateButton.clicked.connect(self.generateTag)
        self.ui.resrefGenerateButton.clicked.connect(self.generateResref)
        self.ui.conversationModifyButton.clicked.connect(self.editConversation)

        self.ui.appearanceSelect.currentIndexChanged.connect(self.update3dPreview)
        self.ui.actionShowPreview.triggered.connect(self.togglePreview)

    def _setupInstallation(self, installation: HTInstallation):
        self._installation = installation
        self.ui.nameEdit.setInstallation(installation)
        self.ui.previewRenderer.installation = installation

        # Load required 2da files if they have not been loaded already
        required = [HTInstallation.TwoDA_DOORS, HTInstallation.TwoDA_FACTIONS]
        installation.htBatchCache2DA(required)

        appearances = installation.htGetCache2DA(HTInstallation.TwoDA_DOORS)
        factions = installation.htGetCache2DA(HTInstallation.TwoDA_FACTIONS)

        self.ui.appearanceSelect.setItems(appearances.get_column("label"))
        self.ui.factionSelect.setItems(factions.get_column("label"))

        self.ui.notBlastableCheckbox.setVisible(installation.tsl)
        self.ui.difficultyModSpin.setVisible(installation.tsl)
        self.ui.difficultySpin.setVisible(installation.tsl)
        self.ui.difficultyLabel.setVisible(installation.tsl)
        self.ui.difficultyModLabel.setVisible(installation.tsl)

    def load(self, filepath: str, resref: str, restype: ResourceType, data: bytes) -> None:
        super().load(filepath, resref, restype, data)

        utd = read_utd(data)
        self._loadUTD(utd)

    def _loadUTD(self, utd: UTD) -> None:
        self._utd = utd

        # Basic
        self.ui.nameEdit.setLocstring(utd.name)
        self.ui.tagEdit.setText(utd.tag)
        self.ui.resrefEdit.setText(utd.resref.get())
        self.ui.appearanceSelect.setCurrentIndex(utd.appearance_id)
        self.ui.conversationEdit.setText(utd.conversation.get())

        # Advanced
        self.ui.min1HpCheckbox.setChecked(utd.min1_hp)
        self.ui.plotCheckbox.setChecked(utd.plot)
        self.ui.staticCheckbox.setChecked(utd.static)
        self.ui.notBlastableCheckbox.setChecked(utd.not_blastable)
        self.ui.factionSelect.setCurrentIndex(utd.faction_id)
        self.ui.animationState.setValue(utd.animation_state)
        self.ui.currenHpSpin.setValue(utd.current_hp)
        self.ui.maxHpSpin.setValue(utd.maximum_hp)
        self.ui.hardnessSpin.setValue(utd.hardness)
        self.ui.fortitudeSpin.setValue(utd.fortitude)
        self.ui.reflexSpin.setValue(utd.reflex)
        self.ui.willSpin.setValue(utd.willpower)

        # Lock
        self.ui.needKeyCheckbox.setChecked(utd.key_required)
        self.ui.removeKeyCheckbox.setChecked(utd.auto_remove_key)
        self.ui.keyEdit.setText(utd.key_name)
        self.ui.lockedCheckbox.setChecked(utd.locked)
        self.ui.openLockSpin.setValue(utd.unlock_dc)
        self.ui.difficultySpin.setValue(utd.unlock_diff)
        self.ui.difficultyModSpin.setValue(utd.unlock_diff_mod)

        # Scripts
        self.ui.onClickEdit.setText(utd.on_click.get())
        self.ui.onClosedEdit.setText(utd.on_closed.get())
        self.ui.onDamagedEdit.setText(utd.on_damaged.get())
        self.ui.onDeathEdit.setText(utd.on_death.get())
        self.ui.onOpenFailedEdit.setText(utd.on_open_failed.get())
        self.ui.onHeartbeatEdit.setText(utd.on_heartbeat.get())
        self.ui.onMeleeAttackEdit.setText(utd.on_melee.get())
        self.ui.onSpellEdit.setText(utd.on_power.get())
        self.ui.onOpenEdit.setText(utd.on_open.get())
        self.ui.onUnlockEdit.setText(utd.on_unlock.get())
        self.ui.onUserDefinedEdit.setText(utd.on_user_defined.get())

        # Comments
        self.ui.commentsEdit.setPlainText(utd.comment)

    def build(self) -> Tuple[bytes, bytes]:
        utd = self._utd

        # Basic
        utd.name = self.ui.nameEdit.locstring()
        utd.tag = self.ui.tagEdit.text()
        utd.resref = ResRef(self.ui.resrefEdit.text())
        utd.appearance_id = self.ui.appearanceSelect.currentIndex()
        utd.conversation = ResRef(self.ui.conversationEdit.text())

        # Advanced
        utd.min1_hp = self.ui.min1HpCheckbox.isChecked()
        utd.party_interact = self.ui.partyInteractCheckbox.isChecked()
        utd.useable = self.ui.useableCheckbox.isChecked()
        utd.plot = self.ui.plotCheckbox.isChecked()
        utd.static = self.ui.staticCheckbox.isChecked()
        utd.not_blastable = self.ui.notBlastableCheckbox.isChecked()
        utd.faction_id = self.ui.factionSelect.currentIndex()
        utd.animation_state = self.ui.animationState.value()
        utd.current_hp = self.ui.currenHpSpin.value()
        utd.maximum_hp = self.ui.maxHpSpin.value()
        utd.hardness = self.ui.hardnessSpin.value()
        utd.fortitude = self.ui.fortitudeSpin.value()
        utd.reflex = self.ui.reflexSpin.value()
        utd.willpower = self.ui.willSpin.value()

        # Lock
        utd.locked = self.ui.lockedCheckbox.isChecked()
        utd.unlock_dc = self.ui.openLockSpin.value()
        utd.unlock_diff = self.ui.difficultySpin.value()
        utd.unlock_diff_mod = self.ui.difficultyModSpin.value()
        utd.key_required = self.ui.needKeyCheckbox.isChecked()
        utd.auto_remove_key = self.ui.removeKeyCheckbox.isChecked()
        utd.key_name = self.ui.keyEdit.text()

        # Scripts
        utd.on_click = ResRef(self.ui.onClickEdit.text())
        utd.on_closed = ResRef(self.ui.onClosedEdit.text())
        utd.on_damaged = ResRef(self.ui.onDamagedEdit.text())
        utd.on_death = ResRef(self.ui.onDeathEdit.text())
        utd.on_open_failed = ResRef(self.ui.onOpenFailedEdit.text())
        utd.on_heartbeat = ResRef(self.ui.onHeartbeatEdit.text())
        utd.on_melee = ResRef(self.ui.onMeleeAttackEdit.text())
        utd.on_power = ResRef(self.ui.onSpellEdit.text())
        utd.on_open = ResRef(self.ui.onOpenEdit.text())
        utd.on_unlock = ResRef(self.ui.onUnlockEdit.text())
        utd.on_user_defined = ResRef(self.ui.onUserDefinedEdit.text())

        # Comments
        utd.comment = self.ui.commentsEdit.toPlainText()

        data = bytearray()
        gff = dismantle_utd(utd)
        write_gff(gff, data)

        return data, b''

    def new(self) -> None:
        super().new()
        self._loadUTD(UTD())

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
            self.ui.resrefEdit.setText("m00xx_dor_000")

    def editConversation(self) -> None:
        resname = self.ui.conversationEdit.text()
        data, filepath = None, None

        if resname == "":
            QMessageBox(QMessageBox.Critical, "Failed to open DLG Editor", "Conversation field cannot be blank.").exec_()
            return

        search = self._installation.resource(resname, ResourceType.DLG)

        if search is None:
            msgbox = QMessageBox(QMessageBox.Information, "DLG file not found",
                                 "Do you wish to create a file in the override?",
                                 QMessageBox.Yes | QMessageBox.No).exec_()
            if QMessageBox.Yes == msgbox:
                data = bytearray()

                write_gff(dismantle_dlg(DLG()), data)
                filepath = self._installation.override_path() + resname + ".dlg"
                writer = BinaryWriter.to_file(filepath)
                writer.write_bytes(data)
                writer.close()
        else:
            resname, restype, filepath, data = search
            self._installation.reload_override("")

        if data is not None:
            openResourceEditor(filepath, resname, ResourceType.DLG, data, self._installation, self)

    def togglePreview(self) -> None:
        self.globalSettings.showPreviewUTP = not self.globalSettings.showPreviewUTP
        self.update3dPreview()

    def update3dPreview(self) -> None:
        self.ui.previewRenderer.setVisible(self.globalSettings.showPreviewUTP)
        self.ui.actionShowPreview.setChecked(self.globalSettings.showPreviewUTP)

        if self.globalSettings.showPreviewUTP:
            self.setFixedSize(674, 457)

            data, _ = self.build()
            modelname = door.get_model(read_utd(data), self._installation, genericdoors=self._genericdoors2DA)
            mdl = self._installation.resource(modelname, ResourceType.MDL)
            mdx = self._installation.resource(modelname, ResourceType.MDX)
            if mdl and mdx:
                self.ui.previewRenderer.setModel(mdl.data, mdx.data)
            else:
                self.ui.previewRenderer.clearModel()
        else:
            self.setFixedSize(374, 457)
