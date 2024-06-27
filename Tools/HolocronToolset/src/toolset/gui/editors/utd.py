from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

import qtpy

from qtpy.QtWidgets import QMessageBox

from pykotor.common.misc import ResRef
from pykotor.common.stream import BinaryWriter
from pykotor.resource.formats.gff import write_gff
from pykotor.resource.generics.dlg import DLG, dismantle_dlg
from pykotor.resource.generics.utd import UTD, dismantle_utd, read_utd
from pykotor.resource.type import ResourceType
from pykotor.tools import door
from toolset.data.installation import HTInstallation
from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog
from toolset.gui.editor import Editor
from toolset.gui.widgets.settings.installations import GlobalSettings
from toolset.utils.window import openResourceEditor

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

        self.globalSettings: GlobalSettings = GlobalSettings()
        self._genericdoors2DA: TwoDA = installation.htGetCache2DA("genericdoors")
        self._utd: UTD = UTD()

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.editors.utd import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.editors.utd import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.editors.utd import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.editors.utd import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
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
        """Connect GUI buttons and signals to methods.

        Args:
        ----
            self: The class instance.

        Processing Logic:
        ----------------
            - Connect tagGenerateButton click signal to generateTag method
            - Connect resrefGenerateButton click signal to generateResref method
            - Connect conversationModifyButton click signal to editConversation method
            - Connect appearanceSelect currentIndexChanged signal to update3dPreview method
            - Connect actionShowPreview triggered signal to togglePreview method.
        """
        self.ui.tagGenerateButton.clicked.connect(self.generateTag)
        self.ui.resrefGenerateButton.clicked.connect(self.generateResref)
        self.ui.conversationModifyButton.clicked.connect(self.editConversation)

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
            - Populates appearance and faction dropdowns from loaded 2da files
            - Shows/hides TSL-specific UI elements based on installation type.
        """
        self._installation = installation
        self.ui.nameEdit.setInstallation(installation)
        self.ui.previewRenderer.installation = installation

        # Load required 2da files if they have not been loaded already
        required: list[str] = [HTInstallation.TwoDA_DOORS, HTInstallation.TwoDA_FACTIONS]
        installation.htBatchCache2DA(required)

        appearances: TwoDA | None = installation.htGetCache2DA(HTInstallation.TwoDA_DOORS)
        factions: TwoDA | None = installation.htGetCache2DA(HTInstallation.TwoDA_FACTIONS)

        self.ui.appearanceSelect.setContext(appearances, self._installation, HTInstallation.TwoDA_DOORS)
        self.ui.factionSelect.setContext(factions, self._installation, HTInstallation.TwoDA_FACTIONS)

        self.ui.appearanceSelect.setItems(appearances.get_column("label"))
        self.ui.factionSelect.setItems(factions.get_column("label"))

        self.handleWidgetWithTSL(self.ui.notBlastableCheckbox, installation)
        self.handleWidgetWithTSL(self.ui.difficultyModSpin, installation)
        self.handleWidgetWithTSL(self.ui.difficultySpin, installation)
        self.handleWidgetWithTSL(self.ui.difficultyLabel, installation)
        self.handleWidgetWithTSL(self.ui.difficultyModLabel, installation)

        installation.setupFileContextMenu(self.ui.onClickEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setupFileContextMenu(self.ui.onClosedEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setupFileContextMenu(self.ui.onDamagedEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setupFileContextMenu(self.ui.onDeathEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setupFileContextMenu(self.ui.onHeartbeatEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setupFileContextMenu(self.ui.onMeleeAttackEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setupFileContextMenu(self.ui.onOpenEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setupFileContextMenu(self.ui.onOpenFailedEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setupFileContextMenu(self.ui.onSpellEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setupFileContextMenu(self.ui.onUnlockEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setupFileContextMenu(self.ui.onUserDefinedEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setupFileContextMenu(self.ui.conversationEdit, [ResourceType.DLG])

    def handleWidgetWithTSL(self, widget: QWidget, installation: HTInstallation):
        widget.setEnabled(installation.tsl)
        if not installation.tsl:
            widget.setToolTip("This widget is only available in KOTOR II.")

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

    def _loadUTD(self, utd: UTD):
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
        self._utd = utd

        # Basic
        self.ui.nameEdit.setLocstring(utd.name)
        self.ui.tagEdit.setText(utd.tag)
        self.ui.resrefEdit.setText(str(utd.resref))
        self.ui.appearanceSelect.setCurrentIndex(utd.appearance_id)
        self.ui.conversationEdit.setComboBoxText(str(utd.conversation))

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
        self.ui.onClickEdit.setComboBoxText(str(utd.on_click))
        self.ui.onClosedEdit.setComboBoxText(str(utd.on_closed))
        self.ui.onDamagedEdit.setComboBoxText(str(utd.on_damaged))
        self.ui.onDeathEdit.setComboBoxText(str(utd.on_death))
        self.ui.onOpenFailedEdit.setComboBoxText(str(utd.on_open_failed))
        self.ui.onHeartbeatEdit.setComboBoxText(str(utd.on_heartbeat))
        self.ui.onMeleeAttackEdit.setComboBoxText(str(utd.on_melee))
        self.ui.onSpellEdit.setComboBoxText(str(utd.on_power))
        self.ui.onOpenEdit.setComboBoxText(str(utd.on_open))
        self.ui.onUnlockEdit.setComboBoxText(str(utd.on_unlock))
        self.ui.onUserDefinedEdit.setComboBoxText(str(utd.on_user_defined))

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
        self.ui.onClosedEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onDamagedEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onDeathEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onHeartbeatEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onMeleeAttackEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onOpenEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onOpenFailedEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onSpellEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onUnlockEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.onUserDefinedEdit.populateComboBox(self.relevant_script_resnames)
        self.ui.conversationEdit.populateComboBox(
            sorted(
                iter(
                    {
                        res.resname().lower()
                        for res in self._installation.getRelevantResources(
                            ResourceType.DLG, self._filepath
                        )
                    }
                )
            )
        )

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
        utd.on_heartbeat = ResRef(self.ui.onHeartbeatEdit.currentText())
        utd.on_melee = ResRef(self.ui.onMeleeAttackEdit.currentText())
        utd.on_power = ResRef(self.ui.onSpellEdit.currentText())
        utd.on_open = ResRef(self.ui.onOpenEdit.currentText())
        utd.on_unlock = ResRef(self.ui.onUnlockEdit.currentText())
        utd.on_user_defined = ResRef(self.ui.onUserDefinedEdit.currentText())

        # Comments
        utd.comment = self.ui.commentsEdit.toPlainText()

        data = bytearray()
        gff = dismantle_utd(utd)
        write_gff(gff, data)

        return data, b""

    def new(self):
        super().new()
        self._loadUTD(UTD())

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
            self.ui.resrefEdit.setText("m00xx_dor_000")

    def editConversation(self):
        """Edits a conversation.

        Processing Logic:
        ----------------
            1. Gets the conversation name from the UI text field
            2. Searches the installation for the conversation resource
            3. If not found, prompts to create a new file in the override folder
            4. If found or created, opens the resource editor window.
        """
        resname = self.ui.conversationEdit.currentText()
        data, filepath = None, None

        if not resname or not resname.strip():
            QMessageBox(QMessageBox.Icon.Critical, "Failed to open DLG Editor", "Conversation field cannot be blank.").exec_()
            return

        search = self._installation.resource(resname, ResourceType.DLG)

        if search is None:
            msgbox = QMessageBox(QMessageBox.Icon.Information, "DLG file not found", "Do you wish to create a file in the override?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No).exec_()
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

    def togglePreview(self):
        self.globalSettings.showPreviewUTP = not self.globalSettings.showPreviewUTP
        self.update3dPreview()

    def update3dPreview(self):
        """Updates the 3D preview renderer visibility and size.

        Processing Logic:
        ----------------
            - Checks if the global setting for showing preview is True
            - If True, calls _update_model() to update the 3D model preview
            - If False, sets the fixed size of the window without leaving space for preview.
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
            - Build the model data from the installation data
            - Get the model name based on the data and installation details
            - Load the MDL and MDX resources using the model name
            - If resources are loaded, set them on the preview renderer
            - If not loaded, clear the existing model from the preview renderer.
        """
        self.setFixedSize(674, 457)

        data, _ = self.build()
        modelname: str = door.get_model(read_utd(data), self._installation, genericdoors=self._genericdoors2DA)
        mdl: ResourceResult | None = self._installation.resource(modelname, ResourceType.MDL)
        mdx: ResourceResult | None = self._installation.resource(modelname, ResourceType.MDX)
        if mdl is not None and mdx is not None:
            self.ui.previewRenderer.setModel(mdl.data, mdx.data)
        else:
            self.ui.previewRenderer.clearModel()
