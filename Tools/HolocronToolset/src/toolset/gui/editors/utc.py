#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Sequence

from loggerplus import RobustLogger
from qtpy.QtCore import QSettings, Qt
from qtpy.QtGui import QImage, QPixmap, QTransform
from qtpy.QtWidgets import QApplication, QListWidgetItem, QMenu, QMessageBox

from pykotor.common.language import Gender, Language
from pykotor.common.misc import Game, ResRef
from pykotor.common.module import Module
from pykotor.extract.capsule import Capsule
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.ltr import read_ltr
from pykotor.resource.formats.twoda.twoda_data import TwoDA
from pykotor.resource.generics.dlg import DLG, bytes_dlg
from pykotor.resource.generics.utc import UTC, UTCClass, read_utc, write_utc
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_capsule_file, is_sav_file
from toolset.data.installation import HTInstallation
from toolset.gui.common.localization import translate as tr
from toolset.gui.dialogs.inventory import InventoryEditor
from toolset.gui.dialogs.load_from_location_result import FileSelectionWindow, ResourceItems
from toolset.gui.editor import Editor
from toolset.gui.widgets.settings.installations import GlobalSettings
from toolset.utils.window import add_window, open_resource_editor

if TYPE_CHECKING:
    import os

    from pathlib import Path

    from qtpy.QtCore import QPoint
    from qtpy.QtGui import QClipboard
    from qtpy.QtWidgets import QWidget
    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from pykotor.common.language import LocalizedString
    from pykotor.extract.capsule import LazyCapsule
    from pykotor.extract.file import LocationResult, ResourceResult
    from pykotor.resource.formats.ltr.ltr_data import LTR
    from pykotor.resource.formats.tpc.tpc_data import TPC, TPCMipmap
    from pykotor.resource.formats.twoda.twoda_data import TwoDA
    from pykotor.tools.path import CaseAwarePath


class UTCEditor(Editor):
    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation = None,
    ):
        """Initializes the Creature Editor window.

        Args:
        ----
            parent: QWidget: The parent widget
            installation: HTInstallation: The installation object

        Processing Logic:
        ----------------
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
        supported: list[ResourceType] = [ResourceType.UTC, ResourceType.BTC, ResourceType.BIC]
        super().__init__(parent, "Creature Editor", "creature", supported, supported, installation)

        self.settings: UTCSettings = UTCSettings()
        self.global_settings: GlobalSettings = GlobalSettings()
        self._utc: UTC = UTC()
        self.setMinimumSize(0, 0)

        from toolset.uic.qtpy.editors.utc import Ui_MainWindow

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.resize(798, 553)
        self._setup_menus()
        self._add_help_action()
        self._setup_installation(installation)
        self._setup_signals()
        self._installation: HTInstallation

        self.ui.actionSaveUnusedFields.setChecked(self.settings.saveUnusedFields)
        self.ui.actionAlwaysSaveK2Fields.setChecked(self.settings.alwaysSaveK2Fields)

        self.update3dPreview()

        self.new()

        # Connect the new context menu and tooltip actions
        self.ui.portraitPicture.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)  # type: ignore[arg-type]
        self.ui.portraitPicture.customContextMenuRequested.connect(self._portrait_context_menu)
        self.ui.portraitPicture.setToolTip(self._generate_portrait_tooltip(as_html=True))

    def _generate_portrait_tooltip(self, *, as_html: bool = False) -> str:
        # sourcery skip: lift-return-into-if
        """Generates a detailed tooltip for the portrait picture."""
        portrait = self._get_portrait_resref()
        if as_html:
            tooltip = f"<b>Portrait:</b> {portrait}<br>" "<br><i>Right-click for more options.</i>"
        else:
            tooltip = f"Portrait: {portrait}\n" "\nRight-click for more options."
        return tooltip

    def _portrait_context_menu(self, position: QPoint):
        context_menu = QMenu(self)

        portrait = self._get_portrait_resref()
        file_menu = context_menu.addMenu("File...")
        assert file_menu is not None, f"`file_menu = context_menu.addMenu('File...')` {file_menu.__class__.__name__}: {file_menu}"
        locations: dict[str, list[LocationResult]] = self._installation.locations(
            ([portrait], [ResourceType.TGA, ResourceType.TPC]),
            order=[SearchLocation.OVERRIDE, SearchLocation.TEXTURES_GUI, SearchLocation.TEXTURES_TPA, SearchLocation.TEXTURES_TPB, SearchLocation.TEXTURES_TPC],
        )
        flat_locations: list[LocationResult] = [item for sublist in locations.values() for item in sublist]
        if flat_locations:
            for location in flat_locations:
                display_path_str: str = str(location.filepath.relative_to(self._installation.path()))
                loc_menu = file_menu.addMenu(display_path_str)
                resource_menu_builder = ResourceItems(resources=[location])
                resource_menu_builder.build_menu(loc_menu)

            action = file_menu.addAction("Details...")
            assert action is not None, f"`action = file_menu.addAction('Details...')` {action.__class__.__name__}: {action}"
            action.triggered.connect(lambda: self._open_details(flat_locations))

        context_menu.exec(self.ui.portraitPicture.mapToGlobal(position))  # pyright: ignore[reportCallIssue, reportArgumentType]  # type: ignore[call-overload]

    def _get_portrait_resref(self) -> str:
        index: int = self.ui.portraitSelect.currentIndex()
        alignment: int = self.ui.alignmentSlider.value()
        portraits: TwoDA | None = self._installation.ht_get_cache_2da(HTInstallation.TwoDA_PORTRAITS)
        assert portraits is not None, f"portraits = self._installation.ht_get_cache_2da(HTInstallation.TwoDA_PORTRAITS) {portraits}: {portraits}"
        result: str = portraits.get_cell(index, "baseresref")
        if 40 >= alignment > 30 and portraits.get_cell(index, "baseresrefe"):
            result = portraits.get_cell(index, "baseresrefe")
        elif 30 >= alignment > 20 and portraits.get_cell(index, "baseresrefve"):
            result = portraits.get_cell(index, "baseresrefve")
        elif 20 >= alignment > 10 and portraits.get_cell(index, "baseresrefvve"):
            result = portraits.get_cell(index, "baseresrefvve")
        elif alignment <= 10 and portraits.get_cell(index, "baseresrefvvve"):
            result = portraits.get_cell(index, "baseresrefvvve")
        return result

    def _open_details(
        self,
        locations: list[LocationResult],
    ):
        """Opens a details window for the given resource locations."""
        selection_window: FileSelectionWindow = FileSelectionWindow(locations, self._installation)
        selection_window.show()
        selection_window.activateWindow()
        add_window(selection_window)

    def _copy_portrait_tooltip(self):
        tooltip_text: str = self._generate_portrait_tooltip(as_html=False)
        clipboard: QClipboard | None = QApplication.clipboard()
        assert clipboard is not None, f"`clipboard = QApplication.clipboard()` {clipboard.__class__.__name__}: {clipboard}"
        clipboard.setText(tooltip_text)

    def _copy_to_clipboard(
        self,
        text: str,
    ):
        clipboard: QClipboard | None = QApplication.clipboard()
        assert clipboard is not None, f"`clipboard = QApplication.clipboard()` {clipboard.__class__.__name__}: {clipboard}"
        clipboard.setText(text)

    def _setup_signals(self):
        """Connect signals to slots.

        Processing Logic:
        ----------------
            - Connects button and widget signals to appropriate slot methods
            - Connects value changed signals from slider and dropdowns
            - Connects menu action triggers to toggle settings.
        """
        self.ui.firstnameRandomButton.clicked.connect(self.randomize_first_name)
        self.ui.firstnameRandomButton.setToolTip(tr("Utilize the game's LTR randomizers to generate a unique name."))
        self.ui.lastnameRandomButton.clicked.connect(self.randomize_last_name)
        self.ui.lastnameRandomButton.setToolTip(tr("Utilize the game's LTR randomizers to generate a unique name."))
        self.ui.tagGenerateButton.clicked.connect(self.generate_tag)
        self.ui.alignmentSlider.valueChanged.connect(lambda: self.portrait_changed(self.ui.portraitSelect.currentIndex()))
        self.ui.portraitSelect.currentIndexChanged.connect(self.portrait_changed)
        self.ui.conversationModifyButton.clicked.connect(self.edit_conversation)
        self.ui.inventoryButton.clicked.connect(self.open_inventory)
        self.ui.featList.itemChanged.connect(self.update_feat_summary)
        self.ui.powerList.itemChanged.connect(self.update_power_summary)
        self.ui.class1LevelSpin.setToolTip(tr("Class Level"))
        self.ui.class2LevelSpin.setToolTip(tr("Class Level"))

        self.ui.appearanceSelect.currentIndexChanged.connect(self.update3dPreview)
        self.ui.alignmentSlider.valueChanged.connect(self.update3dPreview)

        self.ui.actionSaveUnusedFields.triggered.connect(lambda: setattr(self.settings, "saveUnusedFields", self.ui.actionSaveUnusedFields.isChecked()))
        self.ui.actionAlwaysSaveK2Fields.triggered.connect(lambda: setattr(self.settings, "alwaysSaveK2Fields", self.ui.actionAlwaysSaveK2Fields.isChecked()))
        self.ui.actionShowPreview.triggered.connect(self.toggle_preview)

    def _setup_installation(  # noqa: C901, PLR0912, PLR0915
        self,
        installation: HTInstallation,
    ):
        """Sets up the installation for character creation.

        Args:
        ----
            installation: {HTInstallation}: The installation to load data from

        Processing Logic:
        ----------------
            - Loads required 2da files if not already loaded
            - Sets items for dropdown menus from loaded 2da files
            - Clears and populates feat and power lists from loaded 2da files
            - Sets visibility of some checkboxes based on installation type.
        """
        self._installation = installation

        self.ui.previewRenderer.installation = installation
        self.ui.firstnameEdit.set_installation(installation)
        self.ui.lastnameEdit.set_installation(installation)

        # Load required 2da files if they have not been loaded already
        required: list[str] = [
            HTInstallation.TwoDA_APPEARANCES,
            HTInstallation.TwoDA_SOUNDSETS,
            HTInstallation.TwoDA_PORTRAITS,
            HTInstallation.TwoDA_SUBRACES,
            HTInstallation.TwoDA_SPEEDS,
            HTInstallation.TwoDA_FACTIONS,
            HTInstallation.TwoDA_GENDERS,
            HTInstallation.TwoDA_PERCEPTIONS,
            HTInstallation.TwoDA_CLASSES,
            HTInstallation.TwoDA_FEATS,
            HTInstallation.TwoDA_POWERS,
        ]
        installation.ht_batch_cache_2da(required)

        appearances: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_APPEARANCES)
        soundsets: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_SOUNDSETS)
        portraits: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_PORTRAITS)
        subraces: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_SUBRACES)
        speeds: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_SPEEDS)
        factions: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_FACTIONS)
        genders: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_GENDERS)
        perceptions: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_PERCEPTIONS)
        classes: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_CLASSES)
        races: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_RACES)

        if appearances is not None:
            self.ui.appearanceSelect.set_context(appearances, self._installation, HTInstallation.TwoDA_APPEARANCES)
            self.ui.appearanceSelect.set_items(appearances.get_column("label"))

        if soundsets is not None:
            self.ui.soundsetSelect.set_context(soundsets, self._installation, HTInstallation.TwoDA_SOUNDSETS)
            self.ui.soundsetSelect.set_items(soundsets.get_column("label"))

        if portraits is not None:
            self.ui.portraitSelect.set_context(portraits, self._installation, HTInstallation.TwoDA_PORTRAITS)
            self.ui.portraitSelect.set_items(portraits.get_column("baseresref"))

        if subraces is not None:
            self.ui.subraceSelect.set_context(subraces, self._installation, HTInstallation.TwoDA_SUBRACES)
            self.ui.subraceSelect.set_items(subraces.get_column("label"))

        if speeds is not None:
            self.ui.speedSelect.set_context(speeds, self._installation, HTInstallation.TwoDA_SPEEDS)
            self.ui.speedSelect.set_items(speeds.get_column("label"))

        if factions is not None:
            self.ui.factionSelect.set_context(factions, self._installation, HTInstallation.TwoDA_FACTIONS)
            self.ui.factionSelect.set_items(factions.get_column("label"))

        if genders is not None:
            self.ui.genderSelect.set_context(genders, self._installation, HTInstallation.TwoDA_GENDERS)
            self.ui.genderSelect.set_items([label.replace("_", " ").title().replace("Gender ", "") for label in genders.get_column("constant")])

        if perceptions is not None:
            self.ui.perceptionSelect.set_context(perceptions, self._installation, HTInstallation.TwoDA_PERCEPTIONS)
            self.ui.perceptionSelect.set_items(perceptions.get_column("label"))

        if classes is not None:  # sourcery skip: extract-method
            self.ui.class1Select.set_context(classes, self._installation, HTInstallation.TwoDA_CLASSES)
            self.ui.class1Select.set_items(classes.get_column("label"))

            self.ui.class2Select.set_context(classes, self._installation, HTInstallation.TwoDA_CLASSES)
            self.ui.class2Select.clear()
            self.ui.class2Select.setPlaceholderText(tr("[Unset]"))
            for label in classes.get_column("label"):  # pyright: ignore[reportArgumentType]
                self.ui.class2Select.addItem(label)
        self.ui.raceSelect.set_context(races, self._installation, HTInstallation.TwoDA_RACES)

        self.ui.raceSelect.clear()
        self.ui.raceSelect.addItem("Droid", 5)
        self.ui.raceSelect.addItem("Creature", 6)

        feats: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_FEATS)
        if feats is not None:
            self.ui.featList.clear()
            for feat in feats:
                stringref: int = feat.get_integer("name", 0)
                text: str = installation.talktable().string(stringref) if stringref else feat.get_string("label")
                text = text or f"[Unused Feat ID: {feat.label()}]"
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, int(feat.label()))
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.ui.featList.addItem(item)  # pyright: ignore[reportArgumentType, reportCallIssue]
            self.ui.featList.setSortingEnabled(True)
            self.ui.featList.sortItems(Qt.SortOrder.AscendingOrder)  # pyright: ignore[reportArgumentType]

        powers: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_POWERS)
        if powers is not None:
            self.ui.powerList.clear()
            for power in powers:
                stringref = power.get_integer("name", 0)
                text = installation.talktable().string(stringref) if stringref else power.get_string("label")
                text = text.replace("_", " ").replace("XXX", "").replace("\n", "").title()
                text = text or f"[Unused Power ID: {power.label()}]"
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, int(power.label()))
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.ui.powerList.addItem(item)  # pyright: ignore[reportArgumentType, reportCallIssue]
            self.ui.powerList.setSortingEnabled(True)
            self.ui.powerList.sortItems(Qt.SortOrder.AscendingOrder)  # pyright: ignore[reportArgumentType]

        self.ui.noBlockCheckbox.setVisible(installation.tsl)
        self.ui.hologramCheckbox.setVisible(installation.tsl)
        self.ui.k2onlyBox.setVisible(installation.tsl)

        self._installation.setup_file_context_menu(self.ui.onBlockedEdit, [ResourceType.NSS, ResourceType.NCS])
        self._installation.setup_file_context_menu(self.ui.onAttackedEdit, [ResourceType.NSS, ResourceType.NCS])
        self._installation.setup_file_context_menu(self.ui.onNoticeEdit, [ResourceType.NSS, ResourceType.NCS])
        self._installation.setup_file_context_menu(self.ui.onConversationEdit, [ResourceType.NSS, ResourceType.NCS])
        self._installation.setup_file_context_menu(self.ui.onDamagedEdit, [ResourceType.NSS, ResourceType.NCS])
        self._installation.setup_file_context_menu(self.ui.onDeathEdit, [ResourceType.NSS, ResourceType.NCS])
        self._installation.setup_file_context_menu(self.ui.onEndRoundEdit, [ResourceType.NSS, ResourceType.NCS])
        self._installation.setup_file_context_menu(self.ui.onEndConversationEdit, [ResourceType.NSS, ResourceType.NCS])
        self._installation.setup_file_context_menu(self.ui.onDisturbedEdit, [ResourceType.NSS, ResourceType.NCS])
        self._installation.setup_file_context_menu(self.ui.onHeartbeatSelect, [ResourceType.NSS, ResourceType.NCS])
        self._installation.setup_file_context_menu(self.ui.onSpawnEdit, [ResourceType.NSS, ResourceType.NCS])
        self._installation.setup_file_context_menu(self.ui.onSpellCastEdit, [ResourceType.NSS, ResourceType.NCS])
        self._installation.setup_file_context_menu(self.ui.onUserDefinedSelect, [ResourceType.NSS, ResourceType.NCS])

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        super().load(filepath, resref, restype, data)
        self._load_utc(read_utc(data))
        self.update_item_count()

    def _load_utc(
        self,
        utc: UTC,
    ):
        """Loads UTC data into the UI.

        Args:
        ----
            utc (UTC): UTC object to load data from

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
        self.ui.previewRenderer.set_creature(utc)

        # Basic
        self.ui.firstnameEdit.set_locstring(utc.first_name)
        self.ui.lastnameEdit.set_locstring(utc.last_name)
        self.ui.tagEdit.setText(utc.tag)
        self.ui.resrefEdit.setText(str(utc.resref))
        self.ui.appearanceSelect.setCurrentIndex(utc.appearance_id)
        self.ui.soundsetSelect.setCurrentIndex(utc.soundset_id)
        self.ui.conversationEdit.set_combo_box_text(str(utc.conversation))
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

        # TODO(th3w1zard1): Fix the maximum. Use max() due to uncertainty, but it's probably always 150.
        self.ui.baseHpSpin.setMaximum(max(self.ui.baseHpSpin.maximum(), utc.hp))
        self.ui.currentHpSpin.setMaximum(max(self.ui.currentHpSpin.maximum(), utc.current_hp))
        self.ui.maxHpSpin.setMaximum(max(self.ui.maxHpSpin.maximum(), utc.max_hp))
        self.ui.currentFpSpin.setMaximum(max(self.ui.currentFpSpin.maximum(), utc.fp))
        self.ui.maxFpSpin.setMaximum(max(self.ui.maxFpSpin.maximum(), utc.max_fp))
        self.ui.baseHpSpin.setValue(utc.hp)
        self.ui.currentHpSpin.setValue(utc.current_hp)
        self.ui.maxHpSpin.setValue(utc.max_hp)
        self.ui.currentFpSpin.setValue(utc.fp)
        self.ui.maxFpSpin.setValue(utc.max_fp)

        # Classes
        if len(utc.classes) >= 1:
            self.ui.class1Select.setCurrentIndex(utc.classes[0].class_id)
            self.ui.class1LevelSpin.setValue(utc.classes[0].class_level)
        if len(utc.classes) >= 2:  # noqa: PLR2004
            self.ui.class2Select.setCurrentIndex(utc.classes[1].class_id + 1)
            self.ui.class2LevelSpin.setValue(utc.classes[1].class_level)
        self.ui.alignmentSlider.setValue(utc.alignment)

        # Feats
        for i in range(self.ui.featList.count()):
            item: QListWidgetItem | None = self.ui.featList.item(i)
            assert item is not None, f"{self.__class__.__name__}.ui.featList.item({i}) {item.__class__.__name__}: {item}"
            item.setCheckState(Qt.CheckState.Unchecked)  # pyright: ignore[reportArgumentType]
        for feat in utc.feats:
            item = self.get_feat_item(feat)
            if item is None:
                item = QListWidgetItem(f"[Modded Feat ID: {feat}]")
                item.setData(Qt.ItemDataRole.UserRole, feat)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                self.ui.featList.addItem(item)  # pyright: ignore[reportArgumentType, reportCallIssue]
            item.setCheckState(Qt.CheckState.Checked)

        # Powers
        for i in range(self.ui.powerList.count()):
            item = self.ui.powerList.item(i)
            assert item is not None, f"{self.__class__.__name__}.ui.powerList.item({i}) {item.__class__.__name__}: {item}"
            item.setCheckState(Qt.CheckState.Unchecked)  # pyright: ignore[reportArgumentType]
        for utc_class in utc.classes:
            for power in utc_class.powers:
                item = self.get_power_item(power)
                if item is None:
                    item = QListWidgetItem(f"[Modded Power ID: {power}]")
                    item.setData(Qt.ItemDataRole.UserRole, power)
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    self.ui.powerList.addItem(item)  # pyright: ignore[reportCallIssue, reportArgumentType]
                item.setCheckState(Qt.CheckState.Checked)
        self.relevant_script_resnames: list[str] = sorted(iter({res.resname().lower() for res in self._installation.get_relevant_resources(ResourceType.NCS, self._filepath)}))

        self.ui.conversationEdit.populate_combo_box(sorted(iter({res.resname().lower() for res in self._installation.get_relevant_resources(ResourceType.DLG, self._filepath)})))
        self._installation.setup_file_context_menu(self.ui.conversationEdit, [ResourceType.DLG])

        self.ui.onBlockedEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onAttackedEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onNoticeEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onConversationEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onDamagedEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onDeathEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onEndRoundEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onEndConversationEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onDisturbedEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onHeartbeatSelect.populate_combo_box(self.relevant_script_resnames)
        self.ui.onSpawnEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onSpellCastEdit.populate_combo_box(self.relevant_script_resnames)
        self.ui.onUserDefinedSelect.populate_combo_box(self.relevant_script_resnames)

        # Scripts
        self.ui.onBlockedEdit.set_combo_box_text(str(utc.on_blocked))
        self.ui.onAttackedEdit.set_combo_box_text(str(utc.on_attacked))
        self.ui.onNoticeEdit.set_combo_box_text(str(utc.on_notice))
        self.ui.onConversationEdit.set_combo_box_text(str(utc.on_dialog))
        self.ui.onDamagedEdit.set_combo_box_text(str(utc.on_damaged))
        self.ui.onDeathEdit.set_combo_box_text(str(utc.on_death))
        self.ui.onEndRoundEdit.set_combo_box_text(str(utc.on_end_round))
        self.ui.onEndConversationEdit.set_combo_box_text(str(utc.on_end_dialog))
        self.ui.onDisturbedEdit.set_combo_box_text(str(utc.on_disturbed))
        self.ui.onHeartbeatSelect.set_combo_box_text(str(utc.on_heartbeat))
        self.ui.onSpawnEdit.set_combo_box_text(str(utc.on_spawn))
        self.ui.onSpellCastEdit.set_combo_box_text(str(utc.on_spell))
        self.ui.onUserDefinedSelect.set_combo_box_text(str(utc.on_user_defined))

        # Comments
        self.ui.comments.setPlainText(utc.comment)
        self._update_comments_tab_title()

    def _update_comments_tab_title(self):
        """Updates the Comments tab title with a notification badge if comments are not blank."""
        comments = self.ui.comments.toPlainText()
        if comments:
            self.ui.tabWidget.setTabText(self.ui.tabWidget.indexOf(self.ui.commentsTab), "Comments *")  # pyright: ignore[reportArgumentType]
        else:
            self.ui.tabWidget.setTabText(self.ui.tabWidget.indexOf(self.ui.commentsTab), "Comments")  # pyright: ignore[reportArgumentType]

    def build(self) -> tuple[bytes, bytes]:
        """Builds a UTC from UI data.

        Returns:
        -------
            tuple[bytes, bytes]: The GFF data and log.

        Processing Logic:
        ----------------
            - Populate UTC object from UI fields
            - Add class and feat data from lists
            - Convert UTC to GFF bytes
            - Return GFF data and empty log.
        """
        utc: UTC = deepcopy(self._utc)

        utc.first_name = self.ui.firstnameEdit.locstring()
        utc.last_name = self.ui.lastnameEdit.locstring()
        utc.tag = self.ui.tagEdit.text()
        utc.resref = ResRef(self.ui.resrefEdit.text())
        utc.appearance_id = self.ui.appearanceSelect.currentIndex()
        utc.soundset_id = self.ui.soundsetSelect.currentIndex()
        utc.conversation = ResRef(self.ui.conversationEdit.currentText())
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
        utc.on_blocked = ResRef(self.ui.onBlockedEdit.currentText())
        utc.on_attacked = ResRef(self.ui.onAttackedEdit.currentText())
        utc.on_notice = ResRef(self.ui.onNoticeEdit.currentText())
        utc.on_dialog = ResRef(self.ui.onConversationEdit.currentText())
        utc.on_damaged = ResRef(self.ui.onDamagedEdit.currentText())
        utc.on_disturbed = ResRef(self.ui.onDisturbedEdit.currentText())
        utc.on_death = ResRef(self.ui.onDeathEdit.currentText())
        utc.on_end_round = ResRef(self.ui.onEndRoundEdit.currentText())
        utc.on_end_dialog = ResRef(self.ui.onEndConversationEdit.currentText())
        utc.on_heartbeat = ResRef(self.ui.onHeartbeatSelect.currentText())
        utc.on_spawn = ResRef(self.ui.onSpawnEdit.currentText())
        utc.on_spell = ResRef(self.ui.onSpellCastEdit.currentText())
        utc.on_user_defined = ResRef(self.ui.onUserDefinedSelect.currentText())
        utc.comment = self.ui.comments.toPlainText()

        utc.classes = []
        if self.ui.class1Select.currentIndex() != -1:
            class_id: int = self.ui.class1Select.currentIndex()
            class_level: int = self.ui.class1LevelSpin.value()
            utc.classes.append(UTCClass(class_id, class_level))
        if self.ui.class2Select.currentIndex() != 0:
            class_id = self.ui.class2Select.currentIndex()
            class_level = self.ui.class2LevelSpin.value()
            utc.classes.append(UTCClass(class_id, class_level))

        item: QListWidgetItem | None
        utc.feats = []
        for i in range(self.ui.featList.count()):
            item = self.ui.featList.item(i)  # pyright: ignore[reportAssignmentType]
            assert item is not None, f"{self.__class__.__name__}.ui.featList.item({i}) {item.__class__.__name__}: {item}"
            if item.checkState() == Qt.CheckState.Checked:
                utc.feats.append(item.data(Qt.ItemDataRole.UserRole))

        powers: list[int] = utc.classes[-1].powers
        for i in range(self.ui.powerList.count()):
            item = self.ui.powerList.item(i)  # pyright: ignore[reportAssignmentType]
            assert item is not None, f"{self.__class__.__name__}.ui.powerList.item({i}) {item.__class__.__name__}: {item}"
            if item.checkState() == Qt.CheckState.Checked:
                powers.append(item.data(Qt.ItemDataRole.UserRole))

        use_tsl: Literal[Game.K2, Game.K1] = Game.K2 if self.settings.alwaysSaveK2Fields or self._installation.tsl else Game.K1
        data = bytearray()
        write_utc(
            utc,
            data,
            game=use_tsl,
            use_deprecated=self.settings.saveUnusedFields,
        )

        return data, b""

    def new(self):
        super().new()
        self._load_utc(UTC())
        self.update_item_count()

    def randomize_first_name(self):
        ltr_resname: Literal["humanf", "humanm"] = "humanf" if self.ui.genderSelect.currentIndex() == 1 else "humanm"
        locstring: LocalizedString = self.ui.firstnameEdit.locstring()
        ltr: LTR = read_ltr(self._installation.resource(ltr_resname, ResourceType.LTR).data)
        locstring.stringref = -1
        locstring.set_data(Language.ENGLISH, Gender.MALE, ltr.generate())
        self.ui.firstnameEdit.set_locstring(locstring)

    def randomize_last_name(self):
        locstring: LocalizedString = self.ui.lastnameEdit.locstring()
        ltr: LTR = read_ltr(self._installation.resource("humanl", ResourceType.LTR).data)
        locstring.stringref = -1
        locstring.set_data(Language.ENGLISH, Gender.MALE, ltr.generate())
        self.ui.lastnameEdit.set_locstring(locstring)

    def generate_tag(self):
        self.ui.tagEdit.setText(self.ui.resrefEdit.text())

    def portrait_changed(
        self,
        _actual_combo_index: int,
    ):
        """Updates the portrait picture based on the selected index.

        Args:
        ----
            index (int): The selected index

        Updates the portrait pixmap:
            - Checks if index is 0, creates blank image
            - Else builds pixmap from index
            - Sets pixmap to portrait picture widget.
        """
        index: int = self.ui.portraitSelect.currentIndex()
        if index == 0:
            image = QImage(bytes(0 for _ in range(64 * 64 * 3)), 64, 64, QImage.Format.Format_RGB888)
            pixmap: QPixmap = QPixmap.fromImage(image)
        else:
            pixmap = self._build_pixmap(index)
        self.ui.portraitPicture.setPixmap(pixmap)
        self.ui.portraitPicture.setToolTip(self._generate_portrait_tooltip(as_html=True))

    def _build_pixmap(
        self,
        index: int,
    ) -> QPixmap:
        """Builds a portrait pixmap based on character alignment.

        Args:
        ----
            index: The character index to build a portrait for.

        Returns:
        -------
            pixmap: A QPixmap of the character portrait

        Builds the portrait pixmap by:
            1. Getting the character's alignment value
            2. Looking up the character's portrait reference in the portraits 2DA based on alignment
            3. Loading the texture for the portrait reference
            4. Converting the texture to a QPixmap.
        """
        alignment: int = self.ui.alignmentSlider.value()
        portraits: TwoDA | None = self._installation.ht_get_cache_2da(HTInstallation.TwoDA_PORTRAITS)
        assert portraits is not None, f"portraits = self._installation.ht_get_cache_2da(HTInstallation.TwoDA_PORTRAITS) {portraits.__class__.__name__}: {portraits}"
        portrait: str = portraits.get_cell(index, "baseresref")

        if 40 >= alignment > 30 and portraits.get_cell(index, "baseresrefe"):  # TODO(th3w1zard1): document these magic numbers  # noqa: PLR2004
            portrait = portraits.get_cell(index, "baseresrefe")
        elif 30 >= alignment > 20 and portraits.get_cell(index, "baseresrefve"):  # noqa: PLR2004
            portrait = portraits.get_cell(index, "baseresrefve")
        elif 20 >= alignment > 10 and portraits.get_cell(index, "baseresrefvve"):  # noqa: PLR2004
            portrait = portraits.get_cell(index, "baseresrefvve")
        elif alignment <= 10 and portraits.get_cell(index, "baseresrefvvve"):  # noqa: PLR2004
            portrait = portraits.get_cell(index, "baseresrefvvve")

        texture: TPC | None = self._installation.texture(portrait, [SearchLocation.TEXTURES_GUI])

        if texture is not None:
            if texture.format().is_dxt():
                texture.decode()
            mipmap: TPCMipmap = texture.get(0, 0)
            image = QImage(bytes(mipmap.data), mipmap.width, mipmap.height, texture.format().to_qimage_format())
            return QPixmap.fromImage(image).transformed(QTransform().scale(1, -1))

        image = QImage(bytes(0 for _ in range(64 * 64 * 3)), 64, 64, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(image)

    def edit_conversation(self):
        """Edits a conversation.

        Processing Logic:
        ----------------
            1. Gets the conversation name from the UI text field
            2. Searches the installation for the conversation resource
            3. If not found, prompts to create a new file in the override folder
            4. Opens the resource editor with the conversation data.
        """
        resname: str = self.ui.conversationEdit.currentText()

        restype: ResourceType | None = None
        filepath: Path | CaseAwarePath | None = None
        data: bytes | None = None

        if not resname:
            QMessageBox(QMessageBox.Icon.Critical, "Invalid Dialog Reference", "Conversation field cannot be blank.").exec()
            return

        search: ResourceResult | None = self._installation.resource(resname, ResourceType.DLG)
        if search is None:
            if (
                QMessageBox(
                    QMessageBox.Icon.Information,
                    "DLG file not found",
                    "Do you wish to create a new dialog in the 'Override' folder?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                ).exec()
                == QMessageBox.StandardButton.Yes
            ):
                filepath = self._installation.override_path() / f"{resname}.dlg"
                blank_dlg: bytes = bytes_dlg(DLG(), self._installation.game())
                filepath.write_bytes(blank_dlg)
        else:
            resname, restype, filepath, data = search  # pyright: ignore[reportAssignmentType]

        if data is None or filepath is None:
            print(f"Data/filepath cannot be None in self.edit_conversation() relevance: (resname={resname}, restype={restype!r}, filepath={filepath!r})")
            return

        open_resource_editor(filepath, resname, ResourceType.DLG, data, self._installation, self)

    def open_inventory(self):
        """Opens the inventory editor.

        Processing Logic:
        ----------------
            - Loads installed capsules from the root module folder
            - Initializes InventoryEditor with loaded capsules and current inventory/equipment
            - If InventoryEditor is closed successfully, updates internal inventory/equipment
            - Refreshes item count and 3D preview.
        """
        droid: bool = self.ui.raceSelect.currentIndex() == 0
        capsules_to_search: Sequence[LazyCapsule] = []
        if self._filepath is None:
            ...
        elif is_sav_file(self._filepath):
            # search the capsules inside the .sav outer capsule.
            # self._filepath represents the outer capsule
            # res.filepath() is potentially a nested capsule.
            capsules_to_search = [Capsule(res.filepath()) for res in Capsule(self._filepath) if is_capsule_file(res.filename()) and res.inside_capsule]
        elif is_capsule_file(self._filepath):
            capsules_to_search = Module.get_capsules_tuple_matching(self._installation, self._filepath.name)
        inventory_editor = InventoryEditor(
            self,
            self._installation,
            capsules_to_search,
            [],
            self._utc.inventory,
            self._utc.equipment,
            droid=droid,
        )
        if inventory_editor.exec():
            self._utc.inventory = inventory_editor.inventory
            self._utc.equipment = inventory_editor.equipment
            self.update_item_count()
            self.update3dPreview()

    def update_item_count(self):
        self.ui.inventoryCountLabel.setText(f"Total Items: {len(self._utc.inventory)}")

    def get_feat_item(
        self,
        feat_id: int,
    ) -> QListWidgetItem | None:
        for i in range(self.ui.featList.count()):
            item: QListWidgetItem | None = self.ui.featList.item(i)  # pyright: ignore[reportAssignmentType]
            if item is None:
                RobustLogger().warning(f"self.ui.featList.item(i={i}) returned None. Relevance: {self!r}.get_feat_item(feat_id={feat_id!r})")
                continue
            if item.data(Qt.ItemDataRole.UserRole) == feat_id:
                return item
        return None

    def get_power_item(
        self,
        power_id: int,
    ) -> QListWidgetItem | None:
        for i in range(self.ui.powerList.count()):
            item: QListWidgetItem | None = self.ui.powerList.item(i)  # pyright: ignore[reportAssignmentType]
            if item is None:
                RobustLogger().warning(f"self.ui.powerList.item(i={i}) returned None. Relevance: {self!r}.get_power_item(power_id={power_id!r})")
                continue
            if item.data(Qt.ItemDataRole.UserRole) == power_id:
                return item
        return None

    def toggle_preview(self):
        self.global_settings.showPreviewUTC = not self.global_settings.showPreviewUTC
        self.update3dPreview()

    def update_feat_summary(self):
        summary: str = ""
        for i in range(self.ui.featList.count()):
            item: QListWidgetItem | None = self.ui.featList.item(i)  # pyright: ignore[reportAssignmentType]
            if item is None:
                RobustLogger().warning(f"self.ui.featList.item(i={i}) returned None. Relevance: {self!r}.update_feat_summary()")
                continue

            if item.checkState() == Qt.CheckState.Checked:
                summary += f"{item.text()}\n"
        self.ui.featSummaryEdit.setPlainText(summary)

    def update_power_summary(self):
        summary: str = ""
        for i in range(self.ui.powerList.count()):
            item: QListWidgetItem | None = self.ui.powerList.item(i)  # pyright: ignore[reportAssignmentType]
            if item is None:
                RobustLogger().warning(f"self.ui.powerList.item(i={i}) returned None. Relevance: {self!r}.update_power_summary()")
                continue

            if item.checkState() == Qt.CheckState.Checked:
                summary += f"{item.text()}\n"
        self.ui.powerSummaryEdit.setPlainText(summary)

    def update3dPreview(self):
        self.ui.actionShowPreview.setChecked(self.global_settings.showPreviewUTC)

        if self.global_settings.showPreviewUTC:
            self.ui.previewRenderer.setVisible(True)
            self.resize(max(798, self.sizeHint().width()), max(553, self.sizeHint().height()))

            if self._installation is not None:
                data, _ = self.build()
                utc: UTC = read_utc(data)
                self.ui.previewRenderer.set_creature(utc)
        else:
            self.ui.previewRenderer.setVisible(False)
            self.resize(max(798 - 350, self.sizeHint().width()), max(553, self.sizeHint().height()))


class UTCSettings:
    def __init__(self):
        self.settings = QSettings("HolocronToolsetV3", "UTCEditor")

    @property
    def saveUnusedFields(self) -> bool:
        return self.settings.value("saveUnusedFields", True, bool)

    @saveUnusedFields.setter
    def saveUnusedFields(self, value: bool):
        self.settings.setValue("saveUnusedFields", value)

    @property
    def alwaysSaveK2Fields(self) -> bool:
        return self.settings.value("alwaysSaveK2Fields", False, bool)

    @alwaysSaveK2Fields.setter
    def alwaysSaveK2Fields(self, value: bool):
        self.settings.setValue("alwaysSaveK2Fields", value)
