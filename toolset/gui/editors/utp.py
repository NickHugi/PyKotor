from contextlib import suppress
from typing import Optional, Tuple

from PyQt5.QtWidgets import QWidget, QMessageBox

from gui.dialogs.locstring import LocalizedStringDialog
from pykotor.common.misc import ResRef
from pykotor.common.module import Module
from pykotor.common.stream import BinaryWriter
from pykotor.extract.capsule import Capsule
from pykotor.resource.formats.gff import write_gff
from pykotor.resource.generics.dlg import dismantle_dlg, DLG
from pykotor.resource.generics.utp import UTP, dismantle_utp, read_utp
from pykotor.resource.type import ResourceType

from data.installation import HTInstallation
from gui.editor import Editor
from gui.dialogs.inventory import InventoryEditor
from utils.window import openResourceEditor

from toolset.gui.widgets.settings.installations import GlobalSettings
from pykotor.resource.generics.utd import read_utd
from pykotor.tools import placeable


class UTPEditor(Editor):
    def __init__(self, parent: Optional[QWidget], installation: HTInstallation = None, *, mainwindow=None):
        supported = [ResourceType.UTP]
        super().__init__(parent, "Placeable Editor", "placeable", supported, supported, installation, mainwindow)

        self.globalSettings: GlobalSettings = GlobalSettings()
        self._placeables2DA = installation.htGetCache2DA("placeables")
        self._utp = UTP()

        from toolset.uic.editors.utp import Ui_MainWindow
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
        self.ui.inventoryButton.clicked.connect(self.openInventory)

        self.ui.appearanceSelect.currentIndexChanged.connect(self.update3dPreview)
        self.ui.actionShowPreview.triggered.connect(self.togglePreview)

    def _setupInstallation(self, installation: HTInstallation):
        self._installation = installation
        self.ui.nameEdit.setInstallation(installation)
        self.ui.previewRenderer.installation = installation

        # Load required 2da files if they have not been loaded already
        required = [HTInstallation.TwoDA_PLACEABLES, HTInstallation.TwoDA_FACTIONS]
        installation.htBatchCache2DA(required)

        appearances = installation.htGetCache2DA(HTInstallation.TwoDA_PLACEABLES)
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

        utp = read_utp(data)
        self._loadUTP(utp)

        self.updateItemCount()

    def _loadUTP(self, utp: UTP):
        self._utp = utp

        # Basic
        self.ui.nameEdit.setLocstring(utp.name)
        self.ui.tagEdit.setText(utp.tag)
        self.ui.resrefEdit.setText(utp.resref.get())
        self.ui.appearanceSelect.setCurrentIndex(utp.appearance_id)
        self.ui.conversationEdit.setText(utp.conversation.get())

        # Advanced
        self.ui.hasInventoryCheckbox.setChecked(utp.has_inventory)
        self.ui.partyInteractCheckbox.setChecked(utp.party_interact)
        self.ui.useableCheckbox.setChecked(utp.useable)
        self.ui.min1HpCheckbox.setChecked(utp.min1_hp)
        self.ui.plotCheckbox.setChecked(utp.plot)
        self.ui.staticCheckbox.setChecked(utp.static)
        self.ui.notBlastableCheckbox.setChecked(utp.not_blastable)
        self.ui.factionSelect.setCurrentIndex(utp.faction_id)
        self.ui.animationState.setValue(utp.animation_state)
        self.ui.currenHpSpin.setValue(utp.current_hp)
        self.ui.maxHpSpin.setValue(utp.maximum_hp)
        self.ui.hardnessSpin.setValue(utp.hardness)
        self.ui.fortitudeSpin.setValue(utp.fortitude)
        self.ui.reflexSpin.setValue(utp.reflex)
        self.ui.willSpin.setValue(utp.will)

        # Lock
        self.ui.needKeyCheckbox.setChecked(utp.key_required)
        self.ui.removeKeyCheckbox.setChecked(utp.auto_remove_key)
        self.ui.keyEdit.setText(utp.key_name)
        self.ui.lockedCheckbox.setChecked(utp.locked)
        self.ui.openLockSpin.setValue(utp.unlock_dc)
        self.ui.difficultySpin.setValue(utp.unlock_diff)
        self.ui.difficultyModSpin.setValue(utp.unlock_diff_mod)

        # Scripts
        self.ui.onClosedEdit.setText(utp.on_closed.get())
        self.ui.onDamagedEdit.setText(utp.on_damaged.get())
        self.ui.onDeathEdit.setText(utp.on_death.get())
        self.ui.onEndConversationEdit.setText(utp.on_end_dialog.get())
        self.ui.onOpenFailedEdit.setText(utp.on_open_failed.get())
        self.ui.onHeartbeatEdit.setText(utp.on_heartbeat.get())
        self.ui.onInventoryEdit.setText(utp.on_inventory.get())
        self.ui.onMeleeAttackEdit.setText(utp.on_melee_attack.get())
        self.ui.onSpellEdit.setText(utp.on_force_power.get())
        self.ui.onOpenEdit.setText(utp.on_open.get())
        self.ui.onLockEdit.setText(utp.on_lock.get())
        self.ui.onUnlockEdit.setText(utp.on_unlock.get())
        self.ui.onUsedEdit.setText(utp.on_used.get())
        self.ui.onUserDefinedEdit.setText(utp.on_user_defined.get())

        # Comments
        self.ui.commentsEdit.setPlainText(utp.comment)

        self.updateItemCount()

    def build(self) -> Tuple[bytes, bytes]:
        utp = self._utp

        # Basic
        utp.name = self.ui.nameEdit.locstring()
        utp.tag = self.ui.tagEdit.text()
        utp.resref = ResRef(self.ui.resrefEdit.text())
        utp.appearance_id = self.ui.appearanceSelect.currentIndex()
        utp.conversation = ResRef(self.ui.conversationEdit.text())
        utp.has_inventory = self.ui.hasInventoryCheckbox.isChecked()

        # Advanced
        utp.min1_hp = self.ui.min1HpCheckbox.isChecked()
        utp.party_interact = self.ui.partyInteractCheckbox.isChecked()
        utp.useable = self.ui.useableCheckbox.isChecked()
        utp.plot = self.ui.plotCheckbox.isChecked()
        utp.static = self.ui.staticCheckbox.isChecked()
        utp.not_blastable = self.ui.notBlastableCheckbox.isChecked()
        utp.faction_id = self.ui.factionSelect.currentIndex()
        utp.animation_state = self.ui.animationState.value()
        utp.current_hp = self.ui.currenHpSpin.value()
        utp.maximum_hp = self.ui.maxHpSpin.value()
        utp.hardness = self.ui.hardnessSpin.value()
        utp.fortitude = self.ui.fortitudeSpin.value()
        utp.reflex = self.ui.reflexSpin.value()
        utp.will = self.ui.willSpin.value()

        # Lock
        utp.locked = self.ui.lockedCheckbox.isChecked()
        utp.unlock_dc = self.ui.openLockSpin.value()
        utp.unlock_diff = self.ui.difficultySpin.value()
        utp.unlock_diff_mod = self.ui.difficultyModSpin.value()
        utp.key_required = self.ui.needKeyCheckbox.isChecked()
        utp.auto_remove_key = self.ui.removeKeyCheckbox.isChecked()
        utp.key_name = self.ui.keyEdit.text()

        # Scripts
        utp.on_closed = ResRef(self.ui.onClosedEdit.text())
        utp.on_damaged = ResRef(self.ui.onDamagedEdit.text())
        utp.on_death = ResRef(self.ui.onDeathEdit.text())
        utp.on_end_dialog = ResRef(self.ui.onEndConversationEdit.text())
        utp.on_open_failed = ResRef(self.ui.onOpenFailedEdit.text())
        utp.on_heartbeat = ResRef(self.ui.onHeartbeatEdit.text())
        utp.on_inventory = ResRef(self.ui.onInventoryEdit.text())
        utp.on_melee_attack = ResRef(self.ui.onMeleeAttackEdit.text())
        utp.on_force_power = ResRef(self.ui.onSpellEdit.text())
        utp.on_open = ResRef(self.ui.onOpenEdit.text())
        utp.on_lock = ResRef(self.ui.onLockEdit.text())
        utp.on_unlock = ResRef(self.ui.onUnlockEdit.text())
        utp.on_used = ResRef(self.ui.onUsedEdit.text())
        utp.on_user_defined = ResRef(self.ui.onUserDefinedEdit.text())

        # Comments
        utp.comment = self.ui.commentsEdit.toPlainText()

        data = bytearray()
        gff = dismantle_utp(utp)
        write_gff(gff, data)

        return data, b''

    def new(self) -> None:
        super().new()
        self._loadUTP(UTP())

    def updateItemCount(self) -> None:
        self.ui.inventoryCountLabel.setText("Total Items: {}".format(len(self._utp.inventory)))

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
            self.ui.resrefEdit.setText("m00xx_plc_000")

    def editConversation(self) -> None:
        resname = self.ui.conversationEdit.text()
        data, filepath = None, None

        if resname == "":
            QMessageBox(QMessageBox.Critical, "Failed to open DLG Editor",
                        "Conversation field cannot be blank.").exec_()
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

        if data is not None:
            openResourceEditor(filepath, resname, ResourceType.DLG, data, self._installation, self)
            self._installation.reload_override("")

    def openInventory(self) -> None:
        capsules = []

        with suppress(Exception):
            root = Module.get_root(self._filepath)
            capsulesPaths = [path for path in self._installation.module_names() if
                             root in path and path != self._filepath]
            capsules.extend([Capsule(self._installation.module_path() + path) for path in capsulesPaths])

        inventoryEditor = InventoryEditor(self, self._installation, capsules, [], self._utp.inventory, {}, False, True)
        if inventoryEditor.exec_():
            self._utp.inventory = inventoryEditor.inventory
            self.updateItemCount()

    def togglePreview(self) -> None:
        self.globalSettings.showPreviewUTP = not self.globalSettings.showPreviewUTP
        self.update3dPreview()

    def update3dPreview(self) -> None:
        self.ui.previewRenderer.setVisible(self.globalSettings.showPreviewUTP)
        self.ui.actionShowPreview.setChecked(self.globalSettings.showPreviewUTP)

        if self.globalSettings.showPreviewUTP:
            self.setFixedSize(674, 457)

            data, _ = self.build()
            modelname = placeable.get_model(read_utp(data), self._installation, placeables=self._placeables2DA)
            mdl = self._installation.resource(modelname, ResourceType.MDL)
            mdx = self._installation.resource(modelname, ResourceType.MDX)
            if mdl and mdx:
                self.ui.previewRenderer.setModel(mdl.data, mdx.data)
            else:
                self.ui.previewRenderer.clearModel()
        else:
            self.setFixedSize(374, 457)
