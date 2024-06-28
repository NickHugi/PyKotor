from __future__ import annotations

from contextlib import suppress
from copy import deepcopy
from typing import TYPE_CHECKING

import qtpy

from qtpy.QtWidgets import QMessageBox

from pykotor.common.misc import ResRef
from pykotor.common.module import Module
from pykotor.common.stream import BinaryWriter
from pykotor.extract.capsule import Capsule
from pykotor.resource.formats.gff import write_gff
from pykotor.resource.generics.dlg import DLG, dismantle_dlg
from pykotor.resource.generics.utp import UTP, dismantle_utp, read_utp
from pykotor.resource.type import ResourceType
from pykotor.tools import placeable
from toolset.data.installation import HTInstallation
from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog
from toolset.gui.dialogs.inventory import InventoryEditor
from toolset.gui.editor import Editor
from toolset.gui.widgets.settings.installations import GlobalSettings
from toolset.utils.window import openResourceEditor
from utility.logger_util import RobustRootLogger

if TYPE_CHECKING:
    import os

    from qtpy.QtWidgets import QWidget

    from pykotor.extract.file import ResourceResult
    from pykotor.resource.formats.twoda.twoda_data import TwoDA


class UTPEditor(Editor):
    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation = None,
    ):
        """Initialize Placeable Editor.

        Args:
        ----
            parent: {QWidget}: Parent widget
            installation: {HTInstallation}: HTInstallation object

        Processing Logic:
        ----------------
            1. Initialize supported resource types and call super constructor
            2. Initialize global settings object
            3. Get placeables 2DA cache from installation
            4. Initialize UTP object
            5. Set up UI from designer file
            6. Set up menus, signals and installation
            7. Update 3D preview and call new() to initialize editor.
        """
        supported = [ResourceType.UTP, ResourceType.BTP]
        super().__init__(parent, "Placeable Editor", "placeable", supported, supported, installation)

        self.globalSettings: GlobalSettings = GlobalSettings()
        self._placeables2DA = installation.htGetCache2DA("placeables")
        self._utp = UTP()

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.editors.utp import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.editors.utp import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.editors.utp import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.editors.utp import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()
        if installation is not None:  # will only be none in the unittests
            self._setupInstallation(installation)

        self.update3dPreview()
        self.new()

    def _setupSignals(self):
        """Connect UI buttons to their respective methods.

        Processing Logic:
        ----------------
            - Connect tagGenerateButton clicked signal to generateTag method
            - Connect resrefGenerateButton clicked signal to generateResref method
            - Connect conversationModifyButton clicked signal to editConversation method
            - Connect inventoryButton clicked signal to openInventory method

            - Connect appearanceSelect currentIndexChanged signal to update3dPreview method
            - Connect actionShowPreview triggered signal to togglePreview method
        """
        self.ui.tagGenerateButton.clicked.connect(self.generateTag)
        self.ui.resrefGenerateButton.clicked.connect(self.generateResref)
        self.ui.conversationModifyButton.clicked.connect(self.editConversation)
        self.ui.inventoryButton.clicked.connect(self.openInventory)

        self.ui.appearanceSelect.currentIndexChanged.connect(self.update3dPreview)
        self.ui.actionShowPreview.triggered.connect(self.togglePreview)

    def _setupInstallation(self, installation: HTInstallation):
        """Sets up the installation for editing.

        Args:
        ----
            installation: {HTInstallation}: The installation to set up for editing.

        Processing Logic:
        ----------------
            - Sets the internal installation reference and updates UI elements
            - Loads required 2da files if not already loaded
            - Populates appearance and faction dropdowns from loaded 2da data
            - Hides/shows TSL specific UI elements based on installation type
        """
        self._installation = installation
        self.ui.nameEdit.setInstallation(installation)
        self.ui.previewRenderer.installation = installation

        # Load required 2da files if they have not been loaded already
        required: list[str] = [HTInstallation.TwoDA_PLACEABLES, HTInstallation.TwoDA_FACTIONS]
        installation.htBatchCache2DA(required)

        appearances: TwoDA = installation.htGetCache2DA(HTInstallation.TwoDA_PLACEABLES)
        factions: TwoDA = installation.htGetCache2DA(HTInstallation.TwoDA_FACTIONS)

        self.ui.appearanceSelect.setContext(appearances, installation, HTInstallation.TwoDA_PLACEABLES)
        self.ui.factionSelect.setContext(factions, installation, HTInstallation.TwoDA_FACTIONS)

        self.ui.appearanceSelect.setItems(appearances.get_column("label"))
        self.ui.factionSelect.setItems(factions.get_column("label"))

        self.ui.notBlastableCheckbox.setVisible(installation.tsl)
        self.ui.difficultyModSpin.setVisible(installation.tsl)
        self.ui.difficultySpin.setVisible(installation.tsl)
        self.ui.difficultyLabel.setVisible(installation.tsl)
        self.ui.difficultyModLabel.setVisible(installation.tsl)

        installation.setupFileContextMenu(self.ui.onClosedEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setupFileContextMenu(self.ui.onDamagedEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setupFileContextMenu(self.ui.onDeathEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setupFileContextMenu(self.ui.onEndConversationEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setupFileContextMenu(self.ui.onOpenFailedEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setupFileContextMenu(self.ui.onHeartbeatEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setupFileContextMenu(self.ui.onInventoryEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setupFileContextMenu(self.ui.onMeleeAttackEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setupFileContextMenu(self.ui.onSpellEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setupFileContextMenu(self.ui.onOpenEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setupFileContextMenu(self.ui.onLockEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setupFileContextMenu(self.ui.onUnlockEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setupFileContextMenu(self.ui.onUsedEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setupFileContextMenu(self.ui.onUserDefinedEdit, [ResourceType.NSS, ResourceType.NCS])

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        super().load(filepath, resref, restype, data)

        utp = read_utp(data)
        self._loadUTP(utp)

        self.updateItemCount()

    def _loadUTP(self, utp: UTP):
        """Loads UTP data into UI elements.

        Args:
        ----
            utp (UTP): UTP object to load data from.

        Loads UTP data:
            - Sets UI element values like name, tag, etc from UTP properties
            - Sets checkboxes, dropdowns, spinboxes from UTP boolean and integer properties
            - Sets script text fields from UTP script properties
            - Sets comment text from UTP comment property.
        """
        self._utp: UTP = utp

        # Basic
        self.ui.nameEdit.setLocstring(utp.name)
        self.ui.tagEdit.setText(utp.tag)
        self.ui.resrefEdit.setText(str(utp.resref))
        self.ui.appearanceSelect.setCurrentIndex(utp.appearance_id)
        self.ui.conversationEdit.setComboBoxText(str(utp.conversation))

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

        self.ui.onClosedEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onDamagedEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onDeathEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onEndConversationEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onOpenFailedEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onHeartbeatEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onInventoryEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onMeleeAttackEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onSpellEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onOpenEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onLockEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onUnlockEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onUsedEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onUserDefinedEdit.populateComboBox(self.relevant_script_resnames)

        # Scripts
        self.ui.onClosedEdit.setComboBoxText(str(utp.on_closed))
        self.ui.onDamagedEdit.setComboBoxText(str(utp.on_damaged))
        self.ui.onDeathEdit.setComboBoxText(str(utp.on_death))
        self.ui.onEndConversationEdit.setComboBoxText(str(utp.on_end_dialog))
        self.ui.onOpenFailedEdit.setComboBoxText(str(utp.on_open_failed))
        self.ui.onHeartbeatEdit.setComboBoxText(str(utp.on_heartbeat))
        self.ui.onInventoryEdit.setComboBoxText(str(utp.on_inventory))
        self.ui.onMeleeAttackEdit.setComboBoxText(str(utp.on_melee_attack))
        self.ui.onSpellEdit.setComboBoxText(str(utp.on_force_power))
        self.ui.onOpenEdit.setComboBoxText(str(utp.on_open))
        self.ui.onLockEdit.setComboBoxText(str(utp.on_lock))
        self.ui.onUnlockEdit.setComboBoxText(str(utp.on_unlock))
        self.ui.onUsedEdit.setComboBoxText(str(utp.on_used))
        self.ui.onUserDefinedEdit.setComboBoxText(str(utp.on_user_defined))

        # Comments
        self.ui.commentsEdit.setPlainText(utp.comment)

        self.updateItemCount()

    def build(self) -> tuple[bytes, bytes]:
        """Builds a UTP from UI fields.

        Args:
        ----
            self: The class instance
            utp: The UTP object

        Returns:
        -------
            data: The built UTP data
            mdx b"": Empty byte string

        Builds a UTP by:
            - Setting UTP properties like name, tag, scripts from UI elements
            - Writing the constructed UTP to a byte array
            - Returning the byte array and an empty byte string.
        """
        utp: UTP = deepcopy(self._utp)

        # Basic
        utp.name = self.ui.nameEdit.locstring()
        utp.tag = self.ui.tagEdit.text()
        utp.resref = ResRef(self.ui.resrefEdit.text())
        utp.appearance_id = self.ui.appearanceSelect.currentIndex()
        utp.conversation = ResRef(self.ui.conversationEdit.currentText())
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
        utp.on_closed = ResRef(self.ui.onClosedEdit.currentText())
        utp.on_damaged = ResRef(self.ui.onDamagedEdit.currentText())
        utp.on_death = ResRef(self.ui.onDeathEdit.currentText())
        utp.on_end_dialog = ResRef(self.ui.onEndConversationEdit.currentText())
        utp.on_open_failed = ResRef(self.ui.onOpenFailedEdit.currentText())
        utp.on_heartbeat = ResRef(self.ui.onHeartbeatEdit.currentText())
        utp.on_inventory = ResRef(self.ui.onInventoryEdit.currentText())
        utp.on_melee_attack = ResRef(self.ui.onMeleeAttackEdit.currentText())
        utp.on_force_power = ResRef(self.ui.onSpellEdit.currentText())
        utp.on_open = ResRef(self.ui.onOpenEdit.currentText())
        utp.on_lock = ResRef(self.ui.onLockEdit.currentText())
        utp.on_unlock = ResRef(self.ui.onUnlockEdit.currentText())
        utp.on_used = ResRef(self.ui.onUsedEdit.currentText())
        utp.on_user_defined = ResRef(self.ui.onUserDefinedEdit.currentText())

        # Comments
        utp.comment = self.ui.commentsEdit.toPlainText()

        data = bytearray()
        gff = dismantle_utp(utp)
        write_gff(gff, data)

        return data, b""

    def new(self):
        super().new()
        self._loadUTP(UTP())

    def updateItemCount(self):
        self.ui.inventoryCountLabel.setText(f"Total Items: {len(self._utp.inventory)}")

    def changeName(self):
        if self._installation is None:
            self.blinkWindow()
            return
        dialog = LocalizedStringDialog(self, self._installation, self.ui.nameEdit.locstring())
        if dialog.exec_():
            self._loadLocstring(self.ui.nameEdit.ui.locstringText, dialog.locstring)

    def generateTag(self):
        if not self.ui.resrefEdit.text():
            self.generateResref()
        self.ui.tagEdit.setText(self.ui.resrefEdit.text())

    def generateResref(self):
        if self._resname is not None and self._resname != "":
            self.ui.resrefEdit.setText(self._resname)
        else:
            self.ui.resrefEdit.setText("m00xx_plc_000")

    def editConversation(self):
        """Edits a conversation. This function is duplicated in most UT-prefixed gffs."""
        resname = self.ui.conversationEdit.currentText()
        data, filepath = None, None

        if not resname or not resname.strip():
            QMessageBox(QMessageBox.Icon.Critical, "Failed to open DLG Editor", "Conversation field cannot be blank.").exec_()
            return

        search: ResourceResult | None = self._installation.resource(resname, ResourceType.DLG)
        if search is None:
            msgbox: int = QMessageBox(QMessageBox.Icon.Information, "DLG file not found", "Do you wish to create a file in the override?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No).exec_()
            if QMessageBox.StandardButton.Yes == msgbox:
                data = bytearray()

                write_gff(dismantle_dlg(DLG()), data)
                filepath = self._installation.override_path() / f"{resname}.dlg"
                writer = BinaryWriter.to_file(filepath)
                writer.write_bytes(data)
                writer.close()
        else:
            resname, restype, filepath, data = search

        if data is not None:
            openResourceEditor(filepath, resname, ResourceType.DLG, data, self._installation, self)

    def openInventory(self):
        """Opens inventory editor for the module.

        Processing Logic:
        ----------------
            - Gets list of capsule paths for the module
            - Creates capsule objects from the paths
            - Initializes InventoryEditor with the capsules and other data
            - Runs editor and updates inventory if changes were made.
        """
        if self._installation is None:
            self.blinkWindow()
            return
        capsules: list[Capsule] = []
        with suppress(Exception):
            root = Module.find_root(self._filepath)
            moduleNames: list[str] = [path for path in self._installation.module_names() if root in path and path != self._filepath]
            newCapsules: list[Capsule] = [Capsule(self._installation.module_path() / mod_filename) for mod_filename in moduleNames]
            capsules.extend(newCapsules)

        inventoryEditor = InventoryEditor(
            self,
            self._installation,
            capsules,
            [],
            self._utp.inventory,
            {},
            droid=False,
            hide_equipment=True,
        )
        if inventoryEditor.exec_():
            self._utp.inventory = inventoryEditor.inventory
            self.updateItemCount()

    def togglePreview(self):
        self.globalSettings.showPreviewUTP = not self.globalSettings.showPreviewUTP
        self.update3dPreview()

    def update3dPreview(self):
        """Updates the model preview.

        Processing Logic:
        ----------------
            - Build the data and model name from the provided data
            - Get the MDL and MDX resources from the installation based on the model name
            - If both resources exist, set them on the preview renderer
            - If not, clear out any existing model from the preview.
        """
        self.ui.previewRenderer.setVisible(self.globalSettings.showPreviewUTP)
        self.ui.actionShowPreview.setChecked(self.globalSettings.showPreviewUTP)

        if self.globalSettings.showPreviewUTP:
            self._update_model()
        else:
            self.setFixedSize(374, 457)

    def _update_model(self):
        """Updates the model preview.

        Processing Logic:
        ----------------
            - Build the data and model name from the provided data
            - Get the MDL and MDX resources from the installation based on the model name
            - If both resources exist, set them on the preview renderer
            - If not, clear out any existing model from the preview
        """
        if self._installation is None:
            self.blinkWindow()
            return

        self.setFixedSize(674, 457)
        data, _ = self.build()
        modelname: str = placeable.get_model(read_utp(data), self._installation, placeables=self._placeables2DA)
        if not modelname or not modelname.strip():
            RobustRootLogger().warning("Placeable '%s.%s' has no model to render!", self._resname, self._restype)
            self.ui.previewRenderer.clearModel()
            return
        mdl: ResourceResult | None = self._installation.resource(modelname, ResourceType.MDL)
        mdx: ResourceResult | None = self._installation.resource(modelname, ResourceType.MDX)
        if mdl is not None and mdx is not None:
            self.ui.previewRenderer.setModel(mdl.data, mdx.data)
        else:
            self.ui.previewRenderer.clearModel()
