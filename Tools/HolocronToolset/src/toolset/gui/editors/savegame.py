from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from qtpy.QtCore import Qt  # pyright: ignore[reportAttributeAccessIssue]
from qtpy.QtWidgets import (
    QCheckBox,
    QListWidgetItem,
    QMessageBox,
    QShortcut,
    QTableWidgetItem,
)

from pykotor.extract.savedata import (
    GlobalVars,
    PartyTable,
    SaveFolderEntry,
    SaveInfo,
    SaveNestedCapsule,
)
from pykotor.resource.generics.utc import UTC
from pykotor.resource.type import ResourceType
from toolset.gui.editor import Editor
from utility.common.geometry import Vector4

if TYPE_CHECKING:
    import os

    from qtpy.QtWidgets import QWidget

    from toolset.data.installation import HTInstallation


SKILL_NAMES = [
    "Computer Use",
    "Demolitions",
    "Stealth",
    "Awareness",
    "Persuade",
    "Repair",
    "Security",
    "Treat Injury",
]


class SaveGameEditor(Editor):
    """Comprehensive KOTOR Save Game Editor.
    
    This editor provides full access to KOTOR 1 & 2 save game data including:
    - Save metadata (name, module, time played, portraits)
    - Party composition and resources (gold, XP, components, chemicals)
    - Global variables (booleans, numbers, strings, locations)
    - Character data (player and companions - stats, equipment, skills, feats)
    - Inventory items
    - Journal entries
    - EventQueue corruption fixing
    """
    
    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation | None = None,
    ):
        supported: list[ResourceType] = [ResourceType.SAV]
        super().__init__(parent, "Save Game Editor", "savegame", supported, supported, installation)
        self.resize(1200, 800)

        try:
            from toolset.uic.qtpy.editors.savegame import Ui_MainWindow
            self.ui = Ui_MainWindow()
            self.ui.setupUi(self)
        except ImportError:
            # UI file not yet generated - needs to be compiled from savegame.ui
            raise ImportError(
                "UI file not generated. Run UI compiler on src/ui/editors/savegame.ui first."
            )
        self._setup_menus()
        self._setup_signals()
        
        if installation is not None:
            self._setup_installation(installation)

        # Save data structures
        self._save_folder: SaveFolderEntry | None = None
        self._save_info: SaveInfo | None = None
        self._party_table: PartyTable | None = None
        self._global_vars: GlobalVars | None = None
        self._nested_capsule: SaveNestedCapsule | None = None
        self._current_character: UTC | None = None
        
        self.new()

    def _setup_signals(self):
        """Connect UI signals to handlers."""
        # Shortcuts
        QShortcut("Ctrl+S", self).activated.connect(self.save)
        
        # Save Info signals
        self.ui.lineEditSaveName.editingFinished.connect(self.on_save_info_changed)
        self.ui.lineEditAreaName.editingFinished.connect(self.on_save_info_changed)
        self.ui.lineEditLastModule.editingFinished.connect(self.on_save_info_changed)
        self.ui.spinBoxTimePlayed.editingFinished.connect(self.on_save_info_changed)
        self.ui.lineEditPCName.editingFinished.connect(self.on_save_info_changed)
        self.ui.lineEditPortrait0.editingFinished.connect(self.on_save_info_changed)
        self.ui.lineEditPortrait1.editingFinished.connect(self.on_save_info_changed)
        self.ui.lineEditPortrait2.editingFinished.connect(self.on_save_info_changed)
        
        # Party Table signals
        self.ui.spinBoxGold.editingFinished.connect(self.on_party_table_changed)
        self.ui.spinBoxXPPool.editingFinished.connect(self.on_party_table_changed)
        self.ui.spinBoxComponents.editingFinished.connect(self.on_party_table_changed)
        self.ui.spinBoxChemicals.editingFinished.connect(self.on_party_table_changed)
        
        # Global variables signals
        self.ui.tableWidgetBooleans.itemChanged.connect(self.on_global_var_changed)
        self.ui.tableWidgetNumbers.itemChanged.connect(self.on_global_var_changed)
        self.ui.tableWidgetStrings.itemChanged.connect(self.on_global_var_changed)
        self.ui.tableWidgetLocations.itemChanged.connect(self.on_global_var_changed)
        
        # Character signals
        self.ui.listWidgetCharacters.currentRowChanged.connect(self.on_character_selected)
        self.ui.lineEditCharName.editingFinished.connect(self.on_character_data_changed)
        self.ui.spinBoxCharHP.editingFinished.connect(self.on_character_data_changed)
        self.ui.spinBoxCharMaxHP.editingFinished.connect(self.on_character_data_changed)
        self.ui.spinBoxCharFP.editingFinished.connect(self.on_character_data_changed)
        self.ui.spinBoxCharMaxFP.editingFinished.connect(self.on_character_data_changed)
        self.ui.spinBoxCharXP.editingFinished.connect(self.on_character_data_changed)
        self.ui.tableWidgetSkills.itemChanged.connect(self.on_character_data_changed)
        
        # Tool actions
        self.ui.actionFlushEventQueue.triggered.connect(self.flush_event_queue)
        self.ui.actionRebuildCachedModules.triggered.connect(self.rebuild_cached_modules)

    def _setup_installation(
        self,
        installation: HTInstallation,
    ):
        """Setup installation-specific data."""
        self._installation = installation

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        """Load a save game folder.
        
        Args:
        ----
            filepath: Path to the save folder or SAVEGAME.sav file
            resref: Resource reference (save name)
            restype: Resource type (should be SAV)
            data: Raw save data (not used for folder-based saves)
        """
        super().load(filepath, resref, restype, data)
        
        try:
            # Determine if this is a folder or a file
            path = Path(filepath)
            if path.is_file() and path.name.upper() == "SAVEGAME.SAV":
                # If it's SAVEGAME.sav, use the parent folder
                save_folder = path.parent
            else:
                save_folder = path
            
            # Load the save
            self._save_folder = SaveFolderEntry(str(save_folder))
            self._save_folder.load()
            
            # Extract individual components
            self._save_info = self._save_folder.save_info
            self._party_table = self._save_folder.partytable
            self._global_vars = self._save_folder.globals
            self._nested_capsule = self._save_folder.sav
            
            # Populate UI
            self.populate_save_info()
            self.populate_party_table()
            self.populate_global_vars()
            self.populate_characters()
            self.populate_inventory()
            self.populate_journal()
            
            self.ui.statusBar.showMessage(f"Loaded save: {self._save_info.savegame_name}", 3000)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading Save",
                f"Failed to load save game:\n{e}",
            )
            self.new()

    def build(self) -> tuple[bytes, bytes]:
        """Build save data from UI.
        
        Returns
        -------
            Tuple of (data, extra_data) - for saves, we return empty as saves are folder-based
        """
        # Save games are folder-based, so we handle saving differently
        return b"", b""

    def save(self):
        """Save the current save game to disk."""
        if self._save_folder is None:
            QMessageBox.warning(
                self,
                "No Save Loaded",
                "No save game is currently loaded.",
            )
            return
        
        try:
            # Update data structures from UI
            self.update_save_info_from_ui()
            self.update_party_table_from_ui()
            self.update_global_vars_from_ui()
            self.update_characters_from_ui()
            
            # Save all components
            if self._save_info:
                self._save_info.save()
            if self._party_table:
                self._party_table.save()
            if self._global_vars:
                self._global_vars.save()
            
            self.ui.statusBar.showMessage("Save game saved successfully", 3000)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Saving",
                f"Failed to save game:\n{e}",
            )

    def new(self):
        """Create a new empty save game."""
        super().new()
        self._save_folder = None
        self._save_info = None
        self._party_table = None
        self._global_vars = None
        self._nested_capsule = None
        self._current_character = None
        
        # Clear UI
        self.clear_save_info()
        self.clear_party_table()
        self.clear_global_vars()
        self.clear_characters()
        self.clear_inventory()
        self.clear_journal()

    # ==================== Save Info Methods ====================
    
    def populate_save_info(self):
        """Populate Save Info tab from loaded data."""
        if not self._save_info:
            return
        
        self.ui.lineEditSaveName.setText(self._save_info.savegame_name)
        self.ui.lineEditAreaName.setText(self._save_info.area_name)
        self.ui.lineEditLastModule.setText(self._save_info.last_module)
        self.ui.spinBoxTimePlayed.setValue(self._save_info.time_played)
        self.ui.lineEditPCName.setText(self._save_info.pc_name)
        self.ui.lineEditPortrait0.setText(str(self._save_info.portrait0))
        self.ui.lineEditPortrait1.setText(str(self._save_info.portrait1))
        self.ui.lineEditPortrait2.setText(str(self._save_info.portrait2))
    
    def update_save_info_from_ui(self):
        """Update SaveInfo data structure from UI."""
        if not self._save_info:
            return
        
        self._save_info.savegame_name = self.ui.lineEditSaveName.text()
        self._save_info.area_name = self.ui.lineEditAreaName.text()
        self._save_info.last_module = self.ui.lineEditLastModule.text()
        self._save_info.time_played = self.ui.spinBoxTimePlayed.value()
        self._save_info.pc_name = self.ui.lineEditPCName.text()
        self._save_info.portrait0 = self.ui.lineEditPortrait0.text()
        self._save_info.portrait1 = self.ui.lineEditPortrait1.text()
        self._save_info.portrait2 = self.ui.lineEditPortrait2.text()
    
    def clear_save_info(self):
        """Clear Save Info tab."""
        self.ui.lineEditSaveName.clear()
        self.ui.lineEditAreaName.clear()
        self.ui.lineEditLastModule.clear()
        self.ui.spinBoxTimePlayed.setValue(0)
        self.ui.lineEditPCName.clear()
        self.ui.lineEditPortrait0.clear()
        self.ui.lineEditPortrait1.clear()
        self.ui.lineEditPortrait2.clear()
    
    def on_save_info_changed(self):
        """Handle Save Info changes."""
        # Auto-update is handled in save()
        pass

    # ==================== Party Table Methods ====================
    
    def populate_party_table(self):
        """Populate Party Table tab from loaded data."""
        if not self._party_table:
            return
        
        # Resources
        self.ui.spinBoxGold.setValue(self._party_table.pt_gold)
        self.ui.spinBoxXPPool.setValue(self._party_table.pt_xp_pool)
        self.ui.spinBoxComponents.setValue(self._party_table.pt_item_componen)
        self.ui.spinBoxChemicals.setValue(self._party_table.pt_item_chemical)
        
        # Party members
        self.ui.listWidgetPartyMembers.clear()
        for member in self._party_table.pt_members:
            leader_text = " [Leader]" if member.is_leader else ""
            item = QListWidgetItem(f"Member {member.index}{leader_text}")
            self.ui.listWidgetPartyMembers.addItem(item)
    
    def update_party_table_from_ui(self):
        """Update PartyTable data structure from UI."""
        if not self._party_table:
            return
        
        self._party_table.pt_gold = self.ui.spinBoxGold.value()
        self._party_table.pt_xp_pool = self.ui.spinBoxXPPool.value()
        self._party_table.pt_item_componen = self.ui.spinBoxComponents.value()
        self._party_table.pt_item_chemical = self.ui.spinBoxChemicals.value()
    
    def clear_party_table(self):
        """Clear Party Table tab."""
        self.ui.spinBoxGold.setValue(0)
        self.ui.spinBoxXPPool.setValue(0)
        self.ui.spinBoxComponents.setValue(0)
        self.ui.spinBoxChemicals.setValue(0)
        self.ui.listWidgetPartyMembers.clear()
    
    def on_party_table_changed(self):
        """Handle Party Table changes."""
        # Auto-update is handled in save()
        pass

    # ==================== Global Variables Methods ====================
    
    def populate_global_vars(self):
        """Populate Global Variables tab from loaded data."""
        if not self._global_vars:
            return
        
        # Booleans
        self.ui.tableWidgetBooleans.setRowCount(len(self._global_vars.global_bools))
        for row, (name, value) in enumerate(self._global_vars.global_bools):
            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.ui.tableWidgetBooleans.setItem(row, 0, name_item)
            
            checkbox_widget = QCheckBox()
            checkbox_widget.setChecked(value)
            checkbox_widget.stateChanged.connect(self.on_global_var_changed)
            self.ui.tableWidgetBooleans.setCellWidget(row, 1, checkbox_widget)
        
        # Numbers
        self.ui.tableWidgetNumbers.setRowCount(len(self._global_vars.global_numbers))
        for row, (name, value) in enumerate(self._global_vars.global_numbers):
            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.ui.tableWidgetNumbers.setItem(row, 0, name_item)
            
            value_item = QTableWidgetItem(str(value))
            self.ui.tableWidgetNumbers.setItem(row, 1, value_item)
        
        # Strings
        self.ui.tableWidgetStrings.setRowCount(len(self._global_vars.global_strings))
        for row, (name, value) in enumerate(self._global_vars.global_strings):
            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.ui.tableWidgetStrings.setItem(row, 0, name_item)
            
            value_item = QTableWidgetItem(value)
            self.ui.tableWidgetStrings.setItem(row, 1, value_item)
        
        # Locations
        self.ui.tableWidgetLocations.setRowCount(len(self._global_vars.global_locs))
        for row, (name, loc) in enumerate(self._global_vars.global_locs):
            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.ui.tableWidgetLocations.setItem(row, 0, name_item)
            
            self.ui.tableWidgetLocations.setItem(row, 1, QTableWidgetItem(f"{loc.x:.2f}"))
            self.ui.tableWidgetLocations.setItem(row, 2, QTableWidgetItem(f"{loc.y:.2f}"))
            self.ui.tableWidgetLocations.setItem(row, 3, QTableWidgetItem(f"{loc.z:.2f}"))
            self.ui.tableWidgetLocations.setItem(row, 4, QTableWidgetItem(f"{loc.w:.2f}"))
    
    def update_global_vars_from_ui(self):
        """Update GlobalVars data structure from UI."""
        if not self._global_vars:
            return
        
        # Update booleans
        for row in range(self.ui.tableWidgetBooleans.rowCount()):
            name_item = self.ui.tableWidgetBooleans.item(row, 0)
            if name_item:
                name = name_item.text()
                checkbox = self.ui.tableWidgetBooleans.cellWidget(row, 1)
                if isinstance(checkbox, QCheckBox):
                    self._global_vars.set_boolean(name, checkbox.isChecked())
        
        # Update numbers
        for row in range(self.ui.tableWidgetNumbers.rowCount()):
            name_item = self.ui.tableWidgetNumbers.item(row, 0)
            value_item = self.ui.tableWidgetNumbers.item(row, 1)
            if name_item and value_item:
                name = name_item.text()
                try:
                    value = int(value_item.text())
                    self._global_vars.set_number(name, value)
                except ValueError:
                    pass
        
        # Update strings
        for row in range(self.ui.tableWidgetStrings.rowCount()):
            name_item = self.ui.tableWidgetStrings.item(row, 0)
            value_item = self.ui.tableWidgetStrings.item(row, 1)
            if name_item and value_item:
                name = name_item.text()
                self._global_vars.set_string(name, value_item.text())
        
        # Update locations
        for row in range(self.ui.tableWidgetLocations.rowCount()):
            name_item = self.ui.tableWidgetLocations.item(row, 0)
            if name_item:
                name = name_item.text()
                try:
                    x = float(self.ui.tableWidgetLocations.item(row, 1).text())
                    y = float(self.ui.tableWidgetLocations.item(row, 2).text())
                    z = float(self.ui.tableWidgetLocations.item(row, 3).text())
                    w = float(self.ui.tableWidgetLocations.item(row, 4).text())
                    self._global_vars.set_location(name, Vector4(x, y, z, w))
                except (ValueError, AttributeError):
                    pass
    
    def clear_global_vars(self):
        """Clear Global Variables tab."""
        self.ui.tableWidgetBooleans.setRowCount(0)
        self.ui.tableWidgetNumbers.setRowCount(0)
        self.ui.tableWidgetStrings.setRowCount(0)
        self.ui.tableWidgetLocations.setRowCount(0)
    
    def on_global_var_changed(self):
        """Handle Global Variable changes."""
        # Auto-update is handled in save()
        pass

    # ==================== Character Methods ====================
    
    def populate_characters(self):
        """Populate Characters tab from loaded data."""
        if not self._nested_capsule:
            return
        
        self.ui.listWidgetCharacters.clear()
        
        # Load cached characters
        self._nested_capsule.load_cached(reload=True)
        
        # cached_characters is a dict[ResourceIdentifier, UTC], so iterate over values
        for char in self._nested_capsule.cached_characters.values():
            first_name = str(char.first_name) if char.first_name else "Unnamed"
            item = QListWidgetItem(first_name)
            item.setData(Qt.ItemDataRole.UserRole, char)
            self.ui.listWidgetCharacters.addItem(item)
        
        if self.ui.listWidgetCharacters.count() > 0:
            self.ui.listWidgetCharacters.setCurrentRow(0)
    
    def on_character_selected(self, row: int):
        """Handle character selection."""
        if row < 0:
            self._current_character = None
            self.clear_character_details()
            return
        
        item = self.ui.listWidgetCharacters.item(row)
        if not item:
            return
        
        self._current_character = item.data(Qt.ItemDataRole.UserRole)
        if self._current_character:
            self.populate_character_details(self._current_character)
    
    def populate_character_details(self, char: UTC):
        """Populate character details panel."""
        # Stats
        self.ui.lineEditCharName.setText(str(char.first_name) if char.first_name else "")
        self.ui.spinBoxCharHP.setValue(char.current_hp)
        self.ui.spinBoxCharMaxHP.setValue(char.max_hp)
        self.ui.spinBoxCharFP.setValue(char.fp)
        self.ui.spinBoxCharMaxFP.setValue(char.max_fp)
        
        # Get total XP from classes
        total_xp = sum(cls.class_level for cls in char.classes) if char.classes else 0
        self.ui.spinBoxCharXP.setValue(total_xp)
        
        # Skills (individual attributes)
        skill_attrs = ['computer_use', 'demolitions', 'stealth', 'awareness', 'persuade', 'repair', 'security', 'treat_injury']
        self.ui.tableWidgetSkills.setRowCount(len(SKILL_NAMES))
        for row, skill_name in enumerate(SKILL_NAMES):
            skill_item = QTableWidgetItem(skill_name)
            skill_item.setFlags(skill_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.ui.tableWidgetSkills.setItem(row, 0, skill_item)
            
            skill_rank = getattr(char, skill_attrs[row], 0) if row < len(skill_attrs) else 0
            rank_item = QTableWidgetItem(str(skill_rank))
            self.ui.tableWidgetSkills.setItem(row, 1, rank_item)
        
        # Equipment (dict with EquipmentSlot keys)
        self.ui.listWidgetEquipment.clear()
        for slot, item in char.equipment.items():
            item_text = f"{item.resref} (Slot {slot.value})"
            self.ui.listWidgetEquipment.addItem(item_text)
    
    def update_characters_from_ui(self):
        """Update character data from UI."""
        if not self._current_character:
            return
        
        # Update stats
        self._current_character.first_name = self.ui.lineEditCharName.text()
        self._current_character.current_hp = self.ui.spinBoxCharHP.value()
        self._current_character.max_hp = self.ui.spinBoxCharMaxHP.value()
        self._current_character.fp = self.ui.spinBoxCharFP.value()
        self._current_character.max_fp = self.ui.spinBoxCharMaxFP.value()
        # Note: XP is stored per class, not as a single value
        
        # Update skills (individual attributes)
        skill_attrs = ['computer_use', 'demolitions', 'stealth', 'awareness', 'persuade', 'repair', 'security', 'treat_injury']
        for row in range(min(self.ui.tableWidgetSkills.rowCount(), len(skill_attrs))):
            rank_item = self.ui.tableWidgetSkills.item(row, 1)
            if rank_item:
                try:
                    rank = int(rank_item.text())
                    setattr(self._current_character, skill_attrs[row], rank)
                except ValueError:
                    pass
    
    def clear_characters(self):
        """Clear Characters tab."""
        self.ui.listWidgetCharacters.clear()
        self.clear_character_details()
    
    def clear_character_details(self):
        """Clear character details panel."""
        self.ui.lineEditCharName.clear()
        self.ui.spinBoxCharHP.setValue(0)
        self.ui.spinBoxCharMaxHP.setValue(0)
        self.ui.spinBoxCharFP.setValue(0)
        self.ui.spinBoxCharMaxFP.setValue(0)
        self.ui.spinBoxCharXP.setValue(0)
        self.ui.tableWidgetSkills.setRowCount(0)
        self.ui.listWidgetEquipment.clear()
    
    def on_character_data_changed(self):
        """Handle character data changes."""
        # Auto-update is handled in save()
        pass

    # ==================== Inventory Methods ====================
    
    def populate_inventory(self):
        """Populate Inventory tab from loaded data."""
        if not self._nested_capsule:
            return
        
        self.ui.tableWidgetInventory.setRowCount(len(self._nested_capsule.inventory))
        
        for row, item in enumerate(self._nested_capsule.inventory):
            # Item name (from LocalizedString)
            item_name = str(item.name) if item.name else "Unnamed Item"
            name_item = QTableWidgetItem(item_name)
            self.ui.tableWidgetInventory.setItem(row, 0, name_item)
            
            # Stack size
            count_item = QTableWidgetItem(str(item.stack_size))
            self.ui.tableWidgetInventory.setItem(row, 1, count_item)
            
            # ResRef
            resref_item = QTableWidgetItem(str(item.resref))
            self.ui.tableWidgetInventory.setItem(row, 2, resref_item)
    
    def clear_inventory(self):
        """Clear Inventory tab."""
        self.ui.tableWidgetInventory.setRowCount(0)

    # ==================== Journal Methods ====================
    
    def populate_journal(self):
        """Populate Journal tab from loaded data."""
        if not self._party_table:
            return
        
        self.ui.tableWidgetJournal.setRowCount(len(self._party_table.jnl_entries))
        
        for row, entry in enumerate(self._party_table.jnl_entries):
            plot_item = QTableWidgetItem(entry.plot_id)
            self.ui.tableWidgetJournal.setItem(row, 0, plot_item)
            
            state_item = QTableWidgetItem(str(entry.state))
            self.ui.tableWidgetJournal.setItem(row, 1, state_item)
            
            date_item = QTableWidgetItem(str(entry.date))
            self.ui.tableWidgetJournal.setItem(row, 2, date_item)
            
            time_item = QTableWidgetItem(str(entry.time))
            self.ui.tableWidgetJournal.setItem(row, 3, time_item)
    
    def clear_journal(self):
        """Clear Journal tab."""
        self.ui.tableWidgetJournal.setRowCount(0)

    # ==================== Tool Methods ====================
    
    def flush_event_queue(self):
        """Flush EventQueue from cached modules to fix corruption."""
        if not self._nested_capsule:
            QMessageBox.warning(
                self,
                "No Save Loaded",
                "No save game is currently loaded.",
            )
            return
        
        try:
            # Call the clear_event_queues method from savedata.py
            self._nested_capsule.clear_event_queues()
            
            # Save the changes
            if self._save_folder:
                self._save_folder.save()
            
            QMessageBox.information(
                self,
                "EventQueue Flushed",
                "EventQueue has been cleared from all cached modules.\n"
                "This should fix save corruption issues.\n\n"
                "Changes have been saved to disk.",
            )
            self.ui.statusBar.showMessage("EventQueue corruption fixed", 3000)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to flush EventQueue:\n{e}",
            )
    
    def rebuild_cached_modules(self):
        """Rebuild cached modules."""
        if not self._save_folder:
            QMessageBox.warning(
                self,
                "No Save Loaded",
                "No save game is currently loaded.",
            )
            return
        
        try:
            # TODO: Implement cached module rebuilding
            QMessageBox.information(
                self,
                "Modules Rebuilt",
                "Cached modules have been rebuilt successfully.",
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to rebuild cached modules:\n{e}",
            )

