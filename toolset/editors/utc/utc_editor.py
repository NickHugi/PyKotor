from contextlib import suppress
from typing import Optional

from PyQt5 import QtCore
from PyQt5.QtGui import QPixmap, QImage, QTransform
from PyQt5.QtWidgets import QWidget, QListWidgetItem
from pykotor.common.language import Language, Gender
from pykotor.common.misc import ResRef
from pykotor.common.module import Module
from pykotor.common.stream import BinaryWriter
from pykotor.extract.capsule import Capsule
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.gff import write_gff
from pykotor.resource.formats.ltr import read_ltr
from pykotor.resource.formats.tpc import TPCTextureFormat
from pykotor.resource.generics.dlg import DLG, dismantle_dlg, DLGLink, DLGEntry
from pykotor.resource.generics.utc import UTC, UTCClass, dismantle_utc, read_utc
from pykotor.resource.type import ResourceType

from data.installation import HTInstallation
from editors.editor import Editor, LocalizedStringDialog
from editors.inventory_editor import InventoryEditor


class UTCEditor(Editor):
    def __init__(self, parent: QWidget, installation: HTInstallation = None):
        supported = [ResourceType.UTC]
        super().__init__(parent, "Creature Editor", "creature", supported, supported, installation)

        from editors.utc import utc_editor_ui
        self.ui = utc_editor_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()
        self._setupInstallation(installation)

        self._utc = UTC()

        self.new()

    def _setupSignals(self) -> None:
        self.ui.firstnameRandomButton.clicked.connect(self.randomizeFirstname)
        self.ui.firstnameChangeButton.clicked.connect(self.changeFirstname)
        self.ui.lastnameRandomButton.clicked.connect(self.randomizeLastname)
        self.ui.lastnameChangeButton.clicked.connect(self.changeLastname)
        self.ui.tagGenerateButton.clicked.connect(self.generateTag)
        self.ui.alignmentSlider.valueChanged.connect(lambda: self.portraitChanged(self.ui.portraitSelect.currentIndex()))
        self.ui.portraitSelect.currentIndexChanged.connect(self.portraitChanged)
        self.ui.conversationModifyButton.clicked.connect(self.editConversation)
        self.ui.inventoryButton.clicked.connect(self.openInventory)
        self.ui.featList.itemChanged.connect(self.updateFeatSummary)
        self.ui.powerList.itemChanged.connect(self.updatePowerSummary)

    def _setupInstallation(self, installation: HTInstallation):
        self._installation = installation

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

        self.ui.appearanceSelect.clear()
        [self.ui.appearanceSelect.addItem(label.replace("_", " ")) for label in appearances.get_column("label")]

        self.ui.soundsetSelect.clear()
        [self.ui.soundsetSelect.addItem(label.replace("_", " ")) for label in soundsets.get_column("label")]

        self.ui.portraitSelect.clear()
        [self.ui.portraitSelect.addItem(baseresref) for baseresref in portraits.get_column("baseresref")]

        self.ui.raceSelect.addItems(["Droid", "Human"])

        self.ui.subraceSelect.clear()
        [self.ui.subraceSelect.addItem(label) for label in subraces.get_column("label")]

        self.ui.speedSelect.clear()
        [self.ui.speedSelect.addItem(label) for label in speeds.get_column("label")]

        self.ui.factionSelect.clear()
        [self.ui.factionSelect.addItem(label) for label in factions.get_column("label")]

        self.ui.genderSelect.clear()
        [self.ui.genderSelect.addItem(label.replace("_", " ").title().replace("Gender ", "")) for label in genders.get_column("constant")]

        self.ui.perceptionSelect.clear()
        [self.ui.perceptionSelect.addItem(label) for label in perceptions.get_column("label")]

        self.ui.class1Select.clear()
        [self.ui.class1Select.addItem(label) for label in classes.get_column("label")]

        self.ui.class2Select.clear()
        self.ui.class2Select.addItem("[None]")
        [self.ui.class2Select.addItem(label) for label in classes.get_column("label")]

        self.ui.featList.clear()
        for feat in feats:
            stringref = feat.get_integer("name", 0)
            text = installation.talktable().string(stringref) if stringref != 0 else feat.get_string("label")
            text = "[Unused Feat ID: {}]".format(feat.label()) if text == "" else text
            item = QListWidgetItem(text)
            item.setData(QtCore.Qt.UserRole, feat.label())
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
            text = "[Unused Power ID: {}]".format(power.label()) if text == "" else text
            item = QListWidgetItem(text)
            item.setData(QtCore.Qt.UserRole, power.label())
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Unchecked)
            self.ui.powerList.addItem(item)
        self.ui.powerList.setSortingEnabled(True)
        self.ui.powerList.sortItems(QtCore.Qt.AscendingOrder)

        self.ui.noReorientateCheckbox.setVisible(installation.tsl)
        self.ui.noBlockCheckbox.setVisible(installation.tsl)
        self.ui.hologramCheckbox.setVisible(installation.tsl)
        self.ui.k2onlyBox.setVisible(installation.tsl)

    def load(self, filepath: str, resref: str, restype: ResourceType, data: bytes) -> None:
        super().load(filepath, resref, restype, data)

        utc = read_utc(data)
        self._loadUTC(utc)

        self.updateItemCount()

    def _loadUTC(self, utc: UTC):
        self._utc = utc

        # Basic
        self._loadLocstring(self.ui.firstnameEdit, utc.first_name)
        self._loadLocstring(self.ui.lastnameEdit, utc.last_name)
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
        self.ui.raceSelect.setCurrentIndex(utc.race_id - 5)
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
                item = QListWidgetItem("[Modded Feat ID: {}]".format(feat))
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
                    item = QListWidgetItem("[Modded Power ID: {}]".format(power))
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

    def build(self) -> bytes:
        utc = self._utc

        utc.first_name = self.ui.firstnameEdit.locstring
        utc.last_name = self.ui.lastnameEdit.locstring
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
        utc.race_id = self.ui.raceSelect.currentIndex() + 5
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
        gff = dismantle_utc(utc)
        write_gff(gff, data)

        return data

    def new(self) -> None:
        super().new()
        self._loadUTC(UTC())
        self.updateItemCount()

    def randomizeFirstname(self) -> None:
        ltr_resname = "humanf" if self.ui.genderSelect.currentIndex() == 1 else "humanm"
        locstring = self.ui.firstnameEdit.locstring
        ltr = read_ltr(self._installation.resource(ltr_resname, ResourceType.LTR).data)
        locstring.stringref = -1
        locstring.set(Language.ENGLISH, Gender.MALE, ltr.generate())
        self._loadLocstring(self.ui.firstnameEdit, locstring)

    def changeFirstname(self) -> None:
        dialog = LocalizedStringDialog(self, self._installation, self.ui.firstnameEdit.locstring)
        if dialog.exec_():
            self._loadLocstring(self.ui.firstnameEdit, dialog.locstring)

    def randomizeLastname(self) -> None:
        locstring = self.ui.lastnameEdit.locstring
        ltr = read_ltr(self._installation.resource("humanl", ResourceType.LTR).data)
        locstring.stringref = -1
        locstring.set(Language.ENGLISH, Gender.MALE, ltr.generate())
        self._loadLocstring(self.ui.lastnameEdit, locstring)

    def changeLastname(self) -> None:
        dialog = LocalizedStringDialog(self, self._installation, self.ui.lastnameEdit.locstring)
        if dialog.exec_():
            self._loadLocstring(self.ui.lastnameEdit, dialog.locstring)

    def generateTag(self) -> None:
        self.ui.tagEdit.setText(self.ui.resrefEdit.text())

    def portraitChanged(self, index: int) -> None:
        if index == 0:
            image = QImage(bytes([0 for _ in range(64 * 64 * 3)]), 64, 64, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(image)
            self.ui.portraitPicture.setPixmap(pixmap)
        else:
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
                pixmap = QPixmap.fromImage(image).transformed(QTransform().scale(1, -1))
                self.ui.portraitPicture.setPixmap(pixmap)
            else:
                image = QImage(bytes([0 for _ in range(64 * 64 * 3)]), 64, 64, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(image)
                self.ui.portraitPicture.setPixmap(pixmap)

    def editConversation(self) -> None:
        resname = self.ui.conversationEdit.text()
        filepath, data = self._installation.resource(resname, ResourceType.DLG)

        if data is None:
            data = bytearray()

            blank_dlg = DLG()
            starter = DLGLink()
            entry = DLGEntry()
            entry.text.set(Language.ENGLISH, Gender.MALE, "")
            starter.node = entry
            blank_dlg.starters.append(starter)

            write_gff(dismantle_dlg(blank_dlg), data)
            filepath = self._installation.override_path() + resname + ".dlg"
            writer = BinaryWriter.to_file(filepath)
            writer.write_bytes(data)
            writer.close()

        self.parent().openResourceEditor(filepath, resname, ResourceType.DLG, data)

    def openInventory(self) -> None:
        droid = self.ui.raceSelect.currentIndex() == 0
        capsules = []

        with suppress(Exception):
            root = Module.get_root(self._filepath)
            capsulesPaths = [path for path in self._installation.module_names() if root in path and path != self._filepath]
            capsules.extend([Capsule(self._installation.module_path() + path) for path in capsulesPaths])

        inventoryEditor = InventoryEditor(self, self._installation, capsules, [], self._utc.inventory, self._utc.equipment, droid=droid)
        if inventoryEditor.exec_():
            self._utc.inventory = inventoryEditor.inventory
            self._utc.equipment = inventoryEditor.equipment
            self.updateItemCount()

    def updateItemCount(self) -> None:
        self.ui.inventoryCountLabel.setText("Total Items: {}".format(len(self._utc.inventory)))

    def getFeatItem(self, featId: int) -> Optional[QListWidgetItem]:
        for i in range(self.ui.featList.count()):
            item = self.ui.featList.item(i)
            if item.data(QtCore.Qt.UserRole) == featId:
                return item
        else:
            return None

    def getPowerItem(self, powerId: int) -> Optional[QListWidgetItem]:
        for i in range(self.ui.powerList.count()):
            item = self.ui.powerList.item(i)
            if item.data(QtCore.Qt.UserRole) == powerId:
                return item
        else:
            return None

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
