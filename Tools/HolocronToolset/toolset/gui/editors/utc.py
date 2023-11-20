from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Optional, Tuple

from PyQt5 import QtCore
from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QImage, QPixmap, QTransform
from PyQt5.QtWidgets import QListWidgetItem, QMessageBox, QWidget

from pykotor.common.language import Gender, Language
from pykotor.common.misc import Game, ResRef
from pykotor.common.module import Module
from pykotor.common.stream import BinaryWriter
from pykotor.extract.capsule import Capsule
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.gff import write_gff
from pykotor.resource.formats.ltr import read_ltr
from pykotor.resource.formats.tpc import TPCTextureFormat
from pykotor.resource.generics.dlg import DLG, dismantle_dlg
from pykotor.resource.generics.utc import UTC, UTCClass, dismantle_utc, read_utc
from pykotor.resource.type import ResourceType
from toolset.data.installation import HTInstallation
from toolset.gui.dialogs.inventory import InventoryEditor
from toolset.gui.editor import Editor
from toolset.gui.widgets.settings.installations import GlobalSettings
from toolset.utils.window import openResourceEditor

if TYPE_CHECKING:
    import os


class UTCEditor(Editor):
    def __init__(self, parent: Optional[QWidget], installation: HTInstallation | None = None, *, mainwindow=None):
        """Initializes the Creature Editor window
        Args:
            parent: QWidget: The parent widget
            installation: HTInstallation: The installation object
            mainwindow: QMainWindow: The main window
        Returns:
            None: Does not return anything
        Processing Logic:
            - Sets up supported resource types
            - Initializes superclass with parameters
            - Initializes settings objects
            - Initializes UTC object
            - Sets up UI from designer file
            - Sets up installation
            - Sets up signals
            - Sets initial option states
            - Updates 3D preview
            - Creates new empty creature.
        """
        supported = [ResourceType.UTC]
        super().__init__(parent, "Creature Editor", "creature", supported, supported, installation, mainwindow)

        self.settings: UTCSettings = UTCSettings()
        self.globalSettings: GlobalSettings = GlobalSettings()
        self._utc = UTC()

        from toolset.uic.editors.utc import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupInstallation(installation)
        self._setupSignals()

        self.ui.actionSaveUnusedFields.setChecked(self.settings.saveUnusedFields)
        self.ui.actionAlwaysSaveK2Fields.setChecked(self.settings.alwaysSaveK2Fields)

        self.update3dPreview()

        self.new()

    def _setupSignals(self) -> None:
        """Connect signals to slots
        Args:
            self: {The class instance}.

        Returns
        -------
            None: {Does not return anything}
        {Processing Logic}:
        - Connects button and widget signals to appropriate slot methods
        - Connects value changed signals from slider and dropdowns
        - Connects menu action triggers to toggle settings.
        """
        self.ui.firstnameRandomButton.clicked.connect(self.randomizeFirstname)
        self.ui.lastnameRandomButton.clicked.connect(self.randomizeLastname)
        self.ui.tagGenerateButton.clicked.connect(self.generateTag)
        self.ui.alignmentSlider.valueChanged.connect(lambda: self.portraitChanged(self.ui.portraitSelect.currentIndex()))
        self.ui.portraitSelect.currentIndexChanged.connect(self.portraitChanged)
        self.ui.conversationModifyButton.clicked.connect(self.editConversation)
        self.ui.inventoryButton.clicked.connect(self.openInventory)
        self.ui.featList.itemChanged.connect(self.updateFeatSummary)
        self.ui.powerList.itemChanged.connect(self.updatePowerSummary)

        #self.ui.appearanceSelect.currentIndexChanged.connect(self.update3dPreview)
        self.ui.alignmentSlider.valueChanged.connect(self.update3dPreview)

        self.ui.actionSaveUnusedFields.triggered.connect(lambda: setattr(self.settings, "saveUnusedFields", self.ui.actionSaveUnusedFields.isChecked()))
        self.ui.actionAlwaysSaveK2Fields.triggered.connect(lambda: setattr(self.settings, "alwaysSaveK2Fields", self.ui.actionAlwaysSaveK2Fields.isChecked()))
        self.ui.actionShowPreview.triggered.connect(self.togglePreview)

    def _setupInstallation(self, installation: HTInstallation):
        """Sets up the installation for character creation
        Args:
            installation: {HTInstallation}: The installation to load data from
        Returns:
            None: No return value
        - Loads required 2da files if not already loaded
        - Sets items for dropdown menus from loaded 2da files
        - Clears and populates feat and power lists from loaded 2da files
        - Sets visibility of some checkboxes based on installation type.
        """
        self._installation = installation

        self.ui.previewRenderer.installation = installation
        self.ui.firstnameEdit.setInstallation(installation)
        self.ui.lastnameEdit.setInstallation(installation)

        # Load required 2da files if they have not been loaded already
        required = [HTInstallation.TwoDA_APPEARANCES, HTInstallation.TwoDA_SOUNDSETS, HTInstallation.TwoDA_PORTRAITS,
                    HTInstallation.TwoDA_SUBRACES, HTInstallation.TwoDA_SPEEDS, HTInstallation.TwoDA_FACTIONS,
                    HTInstallation.TwoDA_GENDERS, HTInstallation.TwoDA_PERCEPTIONS, HTInstallation.TwoDA_CLASSES,
                    HTInstallation.TwoDA_FEATS, HTInstallation.TwoDA_POWERS]
        installation.htBatchCache2DA(required)

        appearances = installation.htGetCache2DA(HTInstallation.TwoDA_APPEARANCES)
        soundsets = installation.htGetCache2DA(HTInstallation.TwoDA_SOUNDSETS)
        portraits = installation.htGetCache2DA(HTInstallation.TwoDA_PORTRAITS)
        subraces = installation.htGetCache2DA(HTInstallation.TwoDA_SUBRACES)
        speeds = installation.htGetCache2DA(HTInstallation.TwoDA_SPEEDS)
        factions = installation.htGetCache2DA(HTInstallation.TwoDA_FACTIONS)
        genders = installation.htGetCache2DA(HTInstallation.TwoDA_GENDERS)
        perceptions = installation.htGetCache2DA(HTInstallation.TwoDA_PERCEPTIONS)
        classes = installation.htGetCache2DA(HTInstallation.TwoDA_CLASSES)
        feats = installation.htGetCache2DA(HTInstallation.TwoDA_FEATS)
        powers = installation.htGetCache2DA(HTInstallation.TwoDA_POWERS)

        self.ui.appearanceSelect.setItems(appearances.get_column("label"))
        self.ui.soundsetSelect.setItems(soundsets.get_column("label"))
        self.ui.portraitSelect.setItems(portraits.get_column("baseresref"))
        self.ui.subraceSelect.setItems(subraces.get_column("label"))
        self.ui.speedSelect.setItems(speeds.get_column("label"))
        self.ui.factionSelect.setItems(factions.get_column("label"))
        self.ui.genderSelect.setItems(label.replace("_", " ").title().replace("Gender ", "") for label in genders.get_column("constant"))
        self.ui.perceptionSelect.setItems(perceptions.get_column("label"))
        self.ui.class1Select.setItems(classes.get_column("label"))

        self.ui.raceSelect.clear()
        self.ui.raceSelect.addItem("Droid", 5)
        self.ui.raceSelect.addItem("Creature", 6)

        self.ui.class2Select.clear()
        self.ui.class2Select.addItem("[None]")
        [self.ui.class2Select.addItem(label) for label in classes.get_column("label")]

        self.ui.featList.clear()
        for feat in feats:
            stringref = feat.get_integer("name", 0)
            text = installation.talktable().string(stringref) if stringref != 0 else feat.get_string("label")
            text = f"[Unused Feat ID: {feat.label()}]" if text == "" else text
            item = QListWidgetItem(text)
            item.setData(QtCore.Qt.UserRole, int(feat.label()))
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Unchecked)
            self.ui.featList.addItem(item)
        self.ui.featList.setSortingEnabled(True)
        self.ui.featList.sortItems(QtCore.Qt.AscendingOrder)

        self.ui.powerList.clear()
        for power in powers:
            stringref = power.get_integer("name", 0)
            text = installation.talktable().string(stringref) if stringref != 0 else power.get_string("label")
            text = text.replace("_", " ").replace("XXX", "").replace("\n", "").title()
            text = f"[Unused Power ID: {power.label()}]" if text == "" else text
            item = QListWidgetItem(text)
            item.setData(QtCore.Qt.UserRole, int(power.label()))
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Unchecked)
            self.ui.powerList.addItem(item)
        self.ui.powerList.setSortingEnabled(True)
        self.ui.powerList.sortItems(QtCore.Qt.AscendingOrder)

        self.ui.noBlockCheckbox.setVisible(installation.tsl)
        self.ui.hologramCheckbox.setVisible(installation.tsl)
        self.ui.k2onlyBox.setVisible(installation.tsl)

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes) -> None:
        super().load(filepath, resref, restype, data)

        utc = read_utc(data)
        self._loadUTC(utc)

        self.updateItemCount()

    def _loadUTC(self, utc: UTC):
        """Loads UTC data into the UI.

        Args:
        ----
            utc (UTC): UTC object to load data from
        Returns:
            None: No return value
        Loads UTC data:
            - Sets UTC object reference
            - Sets preview renderer creature
            - Loads basic data like name, tags, resref
            - Loads advanced data like flags, stats
            - Loads classes and levels
            - Loads feats and powers
            - Loads scripts
            - Loads comments
        """
        self._utc = utc
        self.ui.previewRenderer.setCreature(utc)

        # Basic
        self.ui.firstnameEdit.setLocstring(utc.first_name)
        self.ui.lastnameEdit.setLocstring(utc.last_name)
        self.ui.tagEdit.setText(utc.tag)
        self.ui.resrefEdit.setText(utc.resref.get())
        self.ui.appearanceSelect.setCurrentIndex(utc.appearance_id)
        self.ui.soundsetSelect.setCurrentIndex(utc.soundset_id)
        self.ui.conversationEdit.setText(utc.conversation.get())
        self.ui.portraitSelect.setCurrentIndex(utc.portrait_id)

        # Advanced
        self.ui.disarmableCheckbox.setChecked(utc.disarmable)
        self.ui.noPermDeathCheckbox.setChecked(utc.no_perm_death)
        self.ui.min1HpCheckbox.setChecked(utc.min1_hp)
        self.ui.plotCheckbox.setChecked(utc.plot)
        self.ui.isPcCheckbox.setChecked(utc.is_pc)
        self.ui.noReorientateCheckbox.setChecked(utc.not_reorienting)
        self.ui.noBlockCheckbox.setChecked(utc.ignore_cre_path)
        self.ui.hologramCheckbox.setChecked(utc.hologram)
        self.ui.raceSelect.setCurrentIndex(utc.race_id)
        self.ui.subraceSelect.setCurrentIndex(utc.subrace_id)
        self.ui.speedSelect.setCurrentIndex(utc.walkrate_id)
        self.ui.factionSelect.setCurrentIndex(utc.faction_id)
        self.ui.genderSelect.setCurrentIndex(utc.gender_id)
        self.ui.perceptionSelect.setCurrentIndex(utc.perception_id)
        self.ui.challengeRatingSpin.setValue(utc.challenge_rating)
        self.ui.blindSpotSpin.setValue(utc.blindspot)
        self.ui.multiplierSetSpin.setValue(utc.multiplier_set)

        # Stats
        self.ui.computerUseSpin.setValue(utc.computer_use)
        self.ui.demolitionsSpin.setValue(utc.demolitions)
        self.ui.stealthSpin.setValue(utc.stealth)
        self.ui.awarenessSpin.setValue(utc.awareness)
        self.ui.persuadeSpin.setValue(utc.persuade)
        self.ui.repairSpin.setValue(utc.repair)
        self.ui.securitySpin.setValue(utc.security)
        self.ui.treatInjurySpin.setValue(utc.treat_injury)
        self.ui.fortitudeSpin.setValue(utc.fortitude_bonus)
        self.ui.reflexSpin.setValue(utc.reflex_bonus)
        self.ui.willSpin.setValue(utc.willpower_bonus)
        self.ui.armorClassSpin.setValue(utc.natural_ac)
        self.ui.strengthSpin.setValue(utc.strength)
        self.ui.dexteritySpin.setValue(utc.dexterity)
        self.ui.constitutionSpin.setValue(utc.constitution)
        self.ui.intelligenceSpin.setValue(utc.intelligence)
        self.ui.wisdomSpin.setValue(utc.wisdom)
        self.ui.charismaSpin.setValue(utc.charisma)
        self.ui.baseHpSpin.setValue(utc.hp)
        self.ui.currentHpSpin.setValue(utc.current_hp)
        self.ui.maxHpSpin.setValue(utc.max_hp)
        self.ui.currentFpSpin.setValue(utc.fp)
        self.ui.maxFpSpin.setValue(utc.max_fp)

        # Classes
        if len(utc.classes) >= 1:
            self.ui.class1Select.setCurrentIndex(utc.classes[0].class_id)
            self.ui.class1LevelSpin.setValue(utc.classes[0].class_level)
        if len(utc.classes) >= 2:
            self.ui.class2Select.setCurrentIndex(utc.classes[1].class_id + 1)
            self.ui.class2LevelSpin.setValue(utc.classes[1].class_level)
        self.ui.alignmentSlider.setValue(utc.alignment)

        # Feats
        for i in range(self.ui.featList.count()):
            item = self.ui.featList.item(i)
            item.setCheckState(QtCore.Qt.Unchecked)
        for feat in utc.feats:
            item = self.getFeatItem(feat)
            if item is None:
                item = QListWidgetItem(f"[Modded Feat ID: {feat}]")
                item.setData(QtCore.Qt.UserRole, feat)
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                self.ui.featList.addItem(item)
            item.setCheckState(QtCore.Qt.Checked)

        # Powers
        for i in range(self.ui.powerList.count()):
            item = self.ui.powerList.item(i)
            item.setCheckState(QtCore.Qt.Unchecked)
        for utc_class in utc.classes:
            for power in utc_class.powers:
                item = self.getPowerItem(power)
                if item is None:
                    item = QListWidgetItem(f"[Modded Power ID: {power}]")
                    item.setData(QtCore.Qt.UserRole, power)
                    item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                    self.ui.powerList.addItem(item)
                item.setCheckState(QtCore.Qt.Checked)

        # Scripts
        self.ui.onBlockedEdit.setText(utc.on_blocked.get())
        self.ui.onAttakcedEdit.setText(utc.on_attacked.get())
        self.ui.onNoticeEdit.setText(utc.on_notice.get())
        self.ui.onConversationEdit.setText(utc.on_dialog.get())
        self.ui.onDamagedEdit.setText(utc.on_damaged.get())
        self.ui.onDeathEdit.setText(utc.on_death.get())
        self.ui.onEndRoundEdit.setText(utc.on_end_round.get())
        self.ui.onEndConversationEdit.setText(utc.on_end_dialog.get())
        self.ui.onDisturbedEdit.setText(utc.on_disturbed.get())
        self.ui.onHeartbeatEdit.setText(utc.on_heartbeat.get())
        self.ui.onSpawnEdit.setText(utc.on_spawn.get())
        self.ui.onSpellCastEdit.setText(utc.on_spell.get())
        self.ui.onUserDefinedEdit.setText(utc.on_user_defined.get())

        # Comments
        self.ui.comments.setPlainText(utc.comment)

    def build(self) -> Tuple[bytes, bytes]:
        """Builds a UTC from UI data
        Args:
            self: The class instance
        Returns:
            Tuple[bytes, bytes]: The GFF data and log
        Processing Logic:
            - Populate UTC object from UI fields
            - Add class and feat data from lists
            - Convert UTC to GFF bytes
            - Return GFF data and empty log.
        """
        utc: UTC = self._utc

        utc.first_name = self.ui.firstnameEdit.locstring()
        utc.last_name = self.ui.lastnameEdit.locstring()
        utc.tag = self.ui.tagEdit.text()
        utc.resref = ResRef(self.ui.resrefEdit.text())
        utc.appearance_id = self.ui.appearanceSelect.currentIndex()
        utc.soundset_id = self.ui.soundsetSelect.currentIndex()
        utc.conversation = ResRef(self.ui.conversationEdit.text())
        utc.portrait_id = self.ui.portraitSelect.currentIndex()
        utc.disarmable = self.ui.disarmableCheckbox.isChecked()
        utc.no_perm_death = self.ui.noPermDeathCheckbox.isChecked()
        utc.min1_hp = self.ui.min1HpCheckbox.isChecked()
        utc.is_pc = self.ui.isPcCheckbox.isChecked()
        utc.not_reorienting = self.ui.noReorientateCheckbox.isChecked()
        utc.ignore_cre_path = self.ui.noBlockCheckbox.isChecked()
        utc.hologram = self.ui.hologramCheckbox.isChecked()
        utc.race_id = self.ui.raceSelect.currentIndex()
        utc.subrace_id = self.ui.subraceSelect.currentIndex()
        utc.walkrate_id = self.ui.speedSelect.currentIndex()
        utc.faction_id = self.ui.factionSelect.currentIndex()
        utc.gender_id = self.ui.genderSelect.currentIndex()
        utc.perception_id = self.ui.perceptionSelect.currentIndex()
        utc.challenge_rating = self.ui.challengeRatingSpin.value()
        utc.blindspot = self.ui.blindSpotSpin.value()
        utc.multiplier_set = self.ui.multiplierSetSpin.value()
        utc.computer_use = self.ui.computerUseSpin.value()
        utc.demolitions = self.ui.demolitionsSpin.value()
        utc.stealth = self.ui.stealthSpin.value()
        utc.awareness = self.ui.awarenessSpin.value()
        utc.persuade = self.ui.persuadeSpin.value()
        utc.security = self.ui.securitySpin.value()
        utc.treat_injury = self.ui.treatInjurySpin.value()
        utc.fortitude_bonus = self.ui.fortitudeSpin.value()
        utc.reflex_bonus = self.ui.reflexSpin.value()
        utc.willpower_bonus = self.ui.willSpin.value()
        utc.natural_ac = self.ui.armorClassSpin.value()
        utc.strength = self.ui.strengthSpin.value()
        utc.dexterity = self.ui.dexteritySpin.value()
        utc.constitution = self.ui.constitutionSpin.value()
        utc.intelligence = self.ui.intelligenceSpin.value()
        utc.wisdom = self.ui.wisdomSpin.value()
        utc.charisma = self.ui.charismaSpin.value()
        utc.hp = self.ui.baseHpSpin.value()
        utc.current_hp = self.ui.currentHpSpin.value()
        utc.max_hp = self.ui.maxHpSpin.value()
        utc.fp = self.ui.currentFpSpin.value()
        utc.max_fp = self.ui.maxFpSpin.value()
        utc.alignment = self.ui.alignmentSlider.value()
        utc.on_blocked = ResRef(self.ui.onBlockedEdit.text())
        utc.on_attacked = ResRef(self.ui.onAttakcedEdit.text())
        utc.on_notice = ResRef(self.ui.onNoticeEdit.text())
        utc.on_dialog = ResRef(self.ui.onConversationEdit.text())
        utc.on_damaged = ResRef(self.ui.onDamagedEdit.text())
        utc.on_disturbed = ResRef(self.ui.onDisturbedEdit.text())
        utc.on_death = ResRef(self.ui.onDeathEdit.text())
        utc.on_end_round = ResRef(self.ui.onEndRoundEdit.text())
        utc.on_end_dialog = ResRef(self.ui.onEndConversationEdit.text())
        utc.on_heartbeat = ResRef(self.ui.onHeartbeatEdit.text())
        utc.on_spawn = ResRef(self.ui.onSpawnEdit.text())
        utc.on_spell = ResRef(self.ui.onSpellCastEdit.text())
        utc.on_user_defined = ResRef(self.ui.onUserDefinedEdit.text())
        utc.comment = self.ui.comments.toPlainText()

        utc.classes = []
        if self.ui.class1Select.currentIndex() != -1:
            classId = self.ui.class1Select.currentIndex()
            classLevel = self.ui.class1LevelSpin.value()
            utc.classes.append(UTCClass(classId, classLevel))
        if self.ui.class2Select.currentIndex() != 0:
            classId = self.ui.class2Select.currentIndex()
            classLevel = self.ui.class2LevelSpin.value()
            utc.classes.append(UTCClass(classId, classLevel))

        utc.feats = []
        for i in range(self.ui.featList.count()):
            item = self.ui.featList.item(i)
            if item.checkState() == QtCore.Qt.Checked:
                utc.feats.append(item.data(QtCore.Qt.UserRole))

        powers = utc.classes[-1].powers
        for i in range(self.ui.powerList.count()):
            item = self.ui.powerList.item(i)
            if item.checkState() == QtCore.Qt.Checked:
                powers.append(item.data(QtCore.Qt.UserRole))

        data = bytearray()
        version = Game.K2 if self.settings.alwaysSaveK2Fields or self._installation.tsl else Game.K1
        gff = dismantle_utc(utc, version, use_deprecated=self.settings.saveUnusedFields)
        write_gff(gff, data)

        return data, b""

    def new(self) -> None:
        super().new()
        self._loadUTC(UTC())
        self.updateItemCount()

    def randomizeFirstname(self) -> None:
        ltr_resname = "humanf" if self.ui.genderSelect.currentIndex() == 1 else "humanm"
        locstring = self.ui.firstnameEdit.locstring()
        ltr = read_ltr(self._installation.resource(ltr_resname, ResourceType.LTR).data)
        locstring.stringref = -1
        locstring.set_data(Language.ENGLISH, Gender.MALE, ltr.generate())
        self.ui.firstnameEdit.setLocstring(locstring)

    def randomizeLastname(self) -> None:
        locstring = self.ui.lastnameEdit.locstring()
        ltr = read_ltr(self._installation.resource("humanl", ResourceType.LTR).data)
        locstring.stringref = -1
        locstring.set_data(Language.ENGLISH, Gender.MALE, ltr.generate())
        self.ui.lastnameEdit.setLocstring(locstring)

    def generateTag(self) -> None:
        self.ui.tagEdit.setText(self.ui.resrefEdit.text())

    def portraitChanged(self, index: int) -> None:
        """Updates the portrait picture based on the selected index
        Args:
            index (int): The selected index
        Returns:
            None
        Updates the portrait pixmap:
            - Checks if index is 0, creates blank image
            - Else builds pixmap from index
            - Sets pixmap to portrait picture widget.
        """
        if index == 0:
            image = QImage(bytes(0 for _ in range(64 * 64 * 3)), 64, 64, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(image)
        else:
            pixmap = self._build_pixmap(index)
        self.ui.portraitPicture.setPixmap(pixmap)

    def _build_pixmap(self, index):
        """Builds a portrait pixmap based on character alignment
        Args:
            index: The character index to build a portrait for
        Returns:
            pixmap: A QPixmap of the character portrait
        Builds the portrait pixmap by:
            1. Getting the character's alignment value
            2. Looking up the character's portrait reference in the portraits 2DA based on alignment
            3. Loading the texture for the portrait reference
            4. Converting the texture to a QPixmap.
        """
        alignment = self.ui.alignmentSlider.value()
        portraits = self._installation.htGetCache2DA(HTInstallation.TwoDA_PORTRAITS)
        portrait = portraits.get_cell(index, "baseresref")
        if 40 >= alignment > 30 and portraits.get_cell(index, "baseresrefe") != "":
            portrait = portraits.get_cell(index, "baseresrefe")
        elif 30 >= alignment > 20 and portraits.get_cell(index, "baseresrefve") != "":
            portrait = portraits.get_cell(index, "baseresrefve")
        elif 20 >= alignment > 10 and portraits.get_cell(index, "baseresrefvve") != "":
            portrait = portraits.get_cell(index, "baseresrefvve")
        elif alignment <= 10 and portraits.get_cell(index, "baseresrefvvve") != "":
            portrait = portraits.get_cell(index, "baseresrefvvve")

        texture = self._installation.texture(portrait, [SearchLocation.TEXTURES_GUI])

        if texture is not None:
            width, height, rgba = texture.convert(TPCTextureFormat.RGB, 0)
            image = QImage(rgba, width, height, QImage.Format_RGB888)
            return QPixmap.fromImage(image).transformed(QTransform().scale(1, -1))
        image = QImage(bytes(0 for _ in range(64 * 64 * 3)), 64, 64, QImage.Format_RGB888)
        return QPixmap.fromImage(image)

    def editConversation(self) -> None:
        """Edits a conversation
        Args:
            self: The class instance
        Returns:
            None: Does not return anything
        Processing Logic:
        1. Gets the conversation name from the UI text field
        2. Searches the installation for the conversation resource
        3. If not found, prompts to create a new file in the override folder
        4. Opens the resource editor with the conversation data.
        """
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
                filepath = self._installation.override_path() / f"{resname}.dlg"
                writer = BinaryWriter.from_file(filepath)
                writer.write_bytes(data)
                writer.close()
        else:
            resname, restype, filepath, data = search

        if data is not None:
            openResourceEditor(filepath, resname, ResourceType.DLG, data, self._installation, self)
            self._installation.load_override()  # TODO: Why is this here?

    def openInventory(self) -> None:
        """Opens the inventory editor
        Args:
            self: The class instance
        Returns:
            None: Does not return anything
        - Loads installed capsules from the root module folder
        - Initializes InventoryEditor with loaded capsules and current inventory/equipment
        - If InventoryEditor is closed successfully, updates internal inventory/equipment
        - Refreshes item count and 3D preview.
        """
        droid = self.ui.raceSelect.currentIndex() == 0
        capsules = []

        with suppress(Exception):
            root = Module.get_root(self._filepath)
            capsulesPaths = [path for path in self._installation.module_names() if root in path and path != self._filepath]
            capsules.extend([Capsule(self._installation.module_path() / path) for path in capsulesPaths])

        inventoryEditor = InventoryEditor(self, self._installation, capsules, [], self._utc.inventory, self._utc.equipment, droid=droid)
        if inventoryEditor.exec_():
            self._utc.inventory = inventoryEditor.inventory
            self._utc.equipment = inventoryEditor.equipment
            self.updateItemCount()
            self.update3dPreview()

    def updateItemCount(self) -> None:
        self.ui.inventoryCountLabel.setText(f"Total Items: {len(self._utc.inventory)}")

    def getFeatItem(self, featId: int) -> Optional[QListWidgetItem]:
        for i in range(self.ui.featList.count()):
            item = self.ui.featList.item(i)
            if item.data(QtCore.Qt.UserRole) == featId:
                return item
        return None

    def getPowerItem(self, powerId: int) -> Optional[QListWidgetItem]:
        for i in range(self.ui.powerList.count()):
            item = self.ui.powerList.item(i)
            if item.data(QtCore.Qt.UserRole) == powerId:
                return item
        return None

    def togglePreview(self) -> None:
        self.globalSettings.showPreviewUTC = not self.globalSettings.showPreviewUTC
        self.update3dPreview()

    def updateFeatSummary(self) -> None:
        summary = ""
        for i in range(self.ui.featList.count()):
            item = self.ui.featList.item(i)
            if item.checkState() == QtCore.Qt.Checked:
                summary += item.text() + "\n"
        self.ui.featSummaryEdit.setPlainText(summary)

    def updatePowerSummary(self) -> None:
        summary = ""
        for i in range(self.ui.powerList.count()):
            item = self.ui.powerList.item(i)
            if item.checkState() == QtCore.Qt.Checked:
                summary += item.text() + "\n"
        self.ui.powerSummaryEdit.setPlainText(summary)

    def update3dPreview(self) -> None:
        """Updates the 3D preview based on global settings
        Args:
            self: The class instance
        Returns:
            None
        Processing Logic:
            - Check if the global setting for showing preview is checked
            - If checked, show the preview renderer and set the window size
            - If an installation is present, build the data and pass it to the renderer
            - If not checked, hide the preview renderer and adjust the window size.
        """
        self.ui.actionShowPreview.setChecked(self.globalSettings.showPreviewUTC)

        if self.globalSettings.showPreviewUTC:
            self.ui.previewRenderer.setVisible(True)
            self.setFixedSize(798, 553)

            if self._installation is not None:
                data, _ = self.build()
                utc = read_utc(data)
                self.ui.previewRenderer.setCreature(utc)
        else:
            self.ui.previewRenderer.setVisible(False)
            self.setFixedSize(798-350, 553)


class UTCSettings:
    def __init__(self):
        self.settings = QSettings("HolocronToolset", "UTCEditor")

    @property
    def saveUnusedFields(self) -> bool:
        return self.settings.value("saveUnusedFields", True, bool)

    @saveUnusedFields.setter
    def saveUnusedFields(self, value: bool) -> None:
        self.settings.setValue("saveUnusedFields", value)

    @property
    def alwaysSaveK2Fields(self) -> bool:
        return self.settings.value("alwaysSaveK2Fields", False, bool)

    @alwaysSaveK2Fields.setter
    def alwaysSaveK2Fields(self, value: bool) -> None:
        self.settings.setValue("alwaysSaveK2Fields", value)
