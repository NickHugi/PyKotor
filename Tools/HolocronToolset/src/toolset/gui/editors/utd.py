from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from qtpy.QtWidgets import QMessageBox

from pykotor.common.misc import ResRef
from pykotor.resource.formats.gff import write_gff
from pykotor.resource.generics.dlg import DLG, dismantle_dlg
from pykotor.resource.generics.utd import UTD, dismantle_utd, read_utd
from pykotor.resource.type import ResourceType
from pykotor.tools import door
from toolset.data.installation import HTInstallation
from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog
from toolset.gui.editor import Editor
from toolset.gui.widgets.settings.installations import GlobalSettings
from toolset.utils.window import open_resource_editor

if TYPE_CHECKING:
    import os

    from qtpy.QtWidgets import QWidget

    from pykotor.extract.file import ResourceResult
    from pykotor.resource.formats.twoda.twoda_data import TwoDA


class UTDEditor(Editor):
    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation = None,
    ):
        """Initialize the Door Editor.

        Args:
        ----
            parent: {QWidget}: The parent widget.
            installation: {HTInstallation}: The installation object.

        Returns:
        -------
            None: Does not return anything.

        Processing Logic:
        ----------------
            1. Get supported resource types and call parent initializer.
            2. Initialize global settings object.
            3. Get generic doors 2DA cache from installation.
            4. Initialize UTD object.
            5. Set up UI from designer file.
            6. Set up menus, signals and installation.
            7. Update 3D preview and call new() to initialize editor.
        """
        supported: list[ResourceType] = [ResourceType.UTD, ResourceType.BTD]
        super().__init__(parent, "Door Editor", "door", supported, supported, installation)

        self.global_settings: GlobalSettings = GlobalSettings()
        self._genericdoors_2da: TwoDA | None = installation.ht_get_cache_2da("genericdoors")
        self._utd: UTD = UTD()

        from toolset.uic.qtpy.editors.utd import Ui_MainWindow

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_menus()
        self._add_help_action()
        self._setup_signals()
        if installation is not None:  # will only be none in the unittests
            self._setup_installation(installation)

        self.update3dPreview()
        self.new()
        self.resize(654, 495)

    def _setup_signals(self):
        """Connect GUI buttons and signals to methods.

        Args:
        ----
            self: The class instance.

        Processing Logic:
        ----------------
            - Connect tagGenerateButton click signal to generate_tag method
            - Connect resrefGenerateButton click signal to generate_resref method
            - Connect conversationModifyButton click signal to edit_conversation method
            - Connect appearanceSelect currentIndexChanged signal to update3dPreview method
            - Connect actionShowPreview triggered signal to toggle_preview method.
        """
        self.ui.tagGenerateButton.clicked.connect(self.generate_tag)
        self.ui.resrefGenerateButton.clicked.connect(self.generate_resref)
        self.ui.conversationModifyButton.clicked.connect(self.edit_conversation)

        self.ui.appearanceSelect.currentIndexChanged.connect(self.update3dPreview)
        self.ui.actionShowPreview.triggered.connect(self.toggle_preview)

    def _setup_installation(self, installation: HTInstallation):
        """Sets up the installation for editing.

        Args:
        ----
            installation: {HTInstallation}: The installation to set up for editing.

        Processing Logic:
        ----------------
            - Sets the internal installation reference and updates UI elements
            - Loads required 2da files if not already loaded
            - Populates appearance and faction dropdowns from loaded 2da files
            - Shows/hides TSL-specific UI elements based on installation type.
        """
        self._installation = installation
        self.ui.nameEdit.set_installation(installation)
        self.ui.previewRenderer.installation = installation

        # Load required 2da files if they have not been loaded already
        required: list[str] = [HTInstallation.TwoDA_DOORS, HTInstallation.TwoDA_FACTIONS]
        installation.ht_batch_cache_2da(required)

        appearances: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_DOORS)
        factions: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_FACTIONS)

        self.ui.appearanceSelect.set_context(appearances, self._installation, HTInstallation.TwoDA_DOORS)
        self.ui.factionSelect.set_context(factions, self._installation, HTInstallation.TwoDA_FACTIONS)

        if appearances is not None:
            self.ui.appearanceSelect.set_items(appearances.get_column("label"))
        if factions is not None:
            self.ui.factionSelect.set_items(factions.get_column("label"))

        self.handle_widget_with_tsl(self.ui.notBlastableCheckbox, installation)
        self.handle_widget_with_tsl(self.ui.difficultyModSpin, installation)
        self.handle_widget_with_tsl(self.ui.difficultySpin, installation)
        self.handle_widget_with_tsl(self.ui.difficultyLabel, installation)
        self.handle_widget_with_tsl(self.ui.difficultyModLabel, installation)

        installation.setup_file_context_menu(self.ui.onClickEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onClosedEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onDamagedEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onDeathEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onHeartbeatSelect, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onMeleeAttackEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onOpenEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onOpenFailedEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onSpellEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onUnlockEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onUserDefinedSelect, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.conversationEdit, [ResourceType.DLG])

    def handle_widget_with_tsl(
        self,
        widget: QWidget,
        installation: HTInstallation,
    ):
        widget.setEnabled(installation.tsl)
        if not installation.tsl:
            from toolset.gui.common.localization import translate as tr
            widget.setToolTip(tr("This widget is only available in KOTOR II."))

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        super().load(filepath, resref, restype, data)

        utd = read_utd(data)
        self._loadUTD(utd)

    def _loadUTD(
        self,
        utd: UTD,
    ):
        """Loads UTD data into UI elements.

        Args:
        ----
            utd (UTD): UTD object to load data from

        Processing Logic:
        ----------------
            - Sets UI element values from UTD object attributes
            - Divides loading into sections for Basic, Advanced, Lock, Scripts, and Comments
            - Handles different UI element types like checkboxes, dropdowns, text fields, etc.
        """
        assert self._installation is not None
        self._utd = utd

        # Basic
        self.ui.nameEdit.set_locstring(utd.name)
        self.ui.tagEdit.setText(utd.tag)
        self.ui.resrefEdit.setText(str(utd.resref))
        self.ui.appearanceSelect.setCurrentIndex(utd.appearance_id)
        self.ui.conversationEdit.set_combo_box_text(str(utd.conversation))

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
        self.ui.onClickEdit.set_combo_box_text(str(utd.on_click))
        self.ui.onClosedEdit.set_combo_box_text(str(utd.on_closed))
        self.ui.onDamagedEdit.set_combo_box_text(str(utd.on_damaged))
        self.ui.onDeathEdit.set_combo_box_text(str(utd.on_death))
        self.ui.onOpenFailedEdit.set_combo_box_text(str(utd.on_open_failed))
        self.ui.onHeartbeatSelect.set_combo_box_text(str(utd.on_heartbeat))
        self.ui.onMeleeAttackEdit.set_combo_box_text(str(utd.on_melee))
        self.ui.onSpellEdit.set_combo_box_text(str(utd.on_power))
        self.ui.onOpenEdit.set_combo_box_text(str(utd.on_open))
        self.ui.onUnlockEdit.set_combo_box_text(str(utd.on_unlock))
        self.ui.onUserDefinedSelect.set_combo_box_text(str(utd.on_user_defined))

        self.relevant_script_resnames: list[str] = sorted(iter({res.resname().lower() for res in self._installation.get_relevant_resources(ResourceType.NCS, self._filepath)}))
        self.ui.onClickEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onClosedEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onDamagedEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onDeathEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onHeartbeatSelect.populate_combo_box(self.relevant_script_resnames)
        self.ui.onMeleeAttackEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onOpenEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onOpenFailedEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onSpellEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onUnlockEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onUserDefinedSelect.populate_combo_box(self.relevant_script_resnames)
        self.ui.conversationEdit.populate_combo_box(sorted(iter({res.resname().lower() for res in self._installation.get_relevant_resources(ResourceType.DLG, self._filepath)})))

        # Comments
        self.ui.commentsEdit.setPlainText(utd.comment)

    def build(self) -> tuple[bytes, bytes]:
        """Builds a UTD object from UI data.

        Returns:
        -------
            tuple[bytes, bytes]: A tuple containing the GFF data (bytes) and errors (bytes)

        Processing Logic:
        ----------------
            - Sets UTD properties from UI elements like name, tag, resrefs etc
            - Writes the constructed UTD to a GFF bytearray
            - Returns the GFF data and any errors
        """
        utd: UTD = deepcopy(self._utd)

        # Basic
        utd.name = self.ui.nameEdit.locstring()
        utd.tag = self.ui.tagEdit.text()
        utd.resref = ResRef(self.ui.resrefEdit.text())
        utd.appearance_id = self.ui.appearanceSelect.currentIndex()
        utd.conversation = ResRef(self.ui.conversationEdit.currentText())

        # Advanced
        utd.min1_hp = self.ui.min1HpCheckbox.isChecked()
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
        utd.on_click = ResRef(self.ui.onClickEdit.currentText())
        utd.on_closed = ResRef(self.ui.onClosedEdit.currentText())
        utd.on_damaged = ResRef(self.ui.onDamagedEdit.currentText())
        utd.on_death = ResRef(self.ui.onDeathEdit.currentText())
        utd.on_open_failed = ResRef(self.ui.onOpenFailedEdit.currentText())
        utd.on_heartbeat = ResRef(self.ui.onHeartbeatSelect.currentText())
        utd.on_melee = ResRef(self.ui.onMeleeAttackEdit.currentText())
        utd.on_power = ResRef(self.ui.onSpellEdit.currentText())
        utd.on_open = ResRef(self.ui.onOpenEdit.currentText())
        utd.on_unlock = ResRef(self.ui.onUnlockEdit.currentText())
        utd.on_user_defined = ResRef(self.ui.onUserDefinedSelect.currentText())

        # Comments
        utd.comment = self.ui.commentsEdit.toPlainText()

        data = bytearray()
        gff = dismantle_utd(utd)
        write_gff(gff, data)

        return data, b""

    def new(self):
        super().new()
        self._loadUTD(UTD())

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
            self.ui.resrefEdit.setText("m00xx_dor_000")

    def edit_conversation(self):
        """Edits a conversation.

        Processing Logic:
        ----------------
            1. Gets the conversation name from the UI text field
            2. Searches the installation for the conversation resource
            3. If not found, prompts to create a new file in the override folder
            4. If found or created, opens the resource editor window.
        """
        assert self._installation is not None
        resname: str = self.ui.conversationEdit.currentText()
        data: bytes | None = None
        filepath: os.PathLike | None = None

        if not resname or not resname.strip():
            QMessageBox(QMessageBox.Icon.Critical, "Failed to open DLG Editor", "Conversation field cannot be blank.").exec()
            return

        search: ResourceResult | None = self._installation.resource(resname, ResourceType.DLG)

        if search is None:
            msgbox = QMessageBox(QMessageBox.Icon.Information, "DLG file not found", "Do you wish to create a file in the override?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No).exec()
            if QMessageBox.StandardButton.Yes == msgbox:
                data = bytearray()

                write_gff(dismantle_dlg(DLG()), data)
                filepath = self._installation.override_path() / f"{resname}.dlg"
                filepath.write_bytes(data)
        else:
            resname, filepath, data = search.resname, search.filepath, search.data

        if data is not None:
            open_resource_editor(filepath, resname, ResourceType.DLG, data, self._installation, self)

    def toggle_preview(self):
        self.global_settings.showPreviewUTP = not self.global_settings.showPreviewUTP
        self.update3dPreview()

    def update3dPreview(self):
        """Updates the 3D preview renderer visibility and size.

        Processing Logic:
        ----------------
            - Checks if the global setting for showing preview is True
            - If True, calls _update_model() to update the 3D model preview
            - If False, sets the fixed size of the window without leaving space for preview.
        """
        self.ui.previewRenderer.setVisible(self.global_settings.showPreviewUTP)
        self.ui.actionShowPreview.setChecked(self.global_settings.showPreviewUTP)

        if self.global_settings.showPreviewUTP:
            self._update_model()
        else:
            self.resize(max(374, self.sizeHint().width()), max(457, self.sizeHint().height()))

    def _update_model(self):
        """Updates the model preview.

        Processing Logic:
        ----------------
            - Build the model data from the installation data
            - Get the model name based on the data and installation details
            - Load the MDL and MDX resources using the model name
            - If resources are loaded, set them on the preview renderer
            - If not loaded, clear the existing model from the preview renderer.
        """
        assert self._installation is not None
        self.resize(max(674, self.sizeHint().width()), max(457, self.sizeHint().height()))

        data, _ = self.build()
        modelname: str = door.get_model(read_utd(data), self._installation, genericdoors=self._genericdoors_2da)
        mdl: ResourceResult | None = self._installation.resource(modelname, ResourceType.MDL)
        mdx: ResourceResult | None = self._installation.resource(modelname, ResourceType.MDX)
        if mdl is not None and mdx is not None:
            self.ui.previewRenderer.set_model(mdl.data, mdx.data)
        else:
            self.ui.previewRenderer.clear_model()

