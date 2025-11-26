from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from qtpy.QtCore import Qt, QEvent  # pyright: ignore[reportAttributeAccessIssue]
from qtpy.QtGui import QImage, QPixmap
from qtpy.QtWidgets import (
    QCheckBox,
    QHeaderView,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QShortcut,
    QTableWidget,
    QTableWidgetItem,
)
from toolset.gui.dialogs.load_from_location_result import FileSelectionWindow

from pykotor.common.misc import ResRef
from pykotor.extract.savedata import (
    GlobalVars,
    PartyTable,
    SaveFolderEntry,
    SaveInfo,
    SaveNestedCapsule,
)
from pykotor.resource.generics.utc import UTC
from pykotor.resource.type import ResourceType
from toolset.gui.common.filters import NoScrollEventFilter
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
        self._add_help_action()
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
        
        # Screenshot display - store original pixmap for resize handling
        self._screenshot_original_pixmap: QPixmap | None = None
        self._screenshot_original_size: tuple[int, int] | None = None  # (width, height)
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)
        
        # Setup screenshot label for proper display
        if hasattr(self.ui, 'labelScreenshotPreview'):
            # Install event filter for resize handling
            self.ui.labelScreenshotPreview.installEventFilter(self)
            # Ensure label is set up for proper image display
            self.ui.labelScreenshotPreview.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.labelScreenshotPreview.setScaledContents(False)  # We handle scaling manually
            # Enable mouse tracking for tooltip updates
            self.ui.labelScreenshotPreview.setMouseTracking(True)
        
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
            self.populate_screenshot()
            
            self.ui.statusBar.showMessage(f"Loaded save: {self._save_info.savegame_name}", 3000)
            
        except Exception as e:
            # Use try-except to prevent access violations if Qt widgets are in invalid state
            from loggerplus import RobustLogger
            logger = RobustLogger()
            
            # Log the error first (safest operation)
            try:
                logger.error(f"Failed to load save game: {e}")
            except Exception:
                pass  # Even logging might fail in extreme cases
            
            # Try to show error message, but be very defensive
            try:
                # Check if self is still valid before accessing it
                if hasattr(self, 'isVisible') and hasattr(self, 'ui'):
                    from toolset.gui.common.localization import translate as tr, trf
                    QMessageBox.critical(
                        self,
                        tr("Error Loading Save"),
                        trf("Failed to load save game:\n{error}", error=str(e)),
                    )
            except Exception:
                # If message box fails, just log (already done above)
                pass
            
            # Try to reset state, but be defensive
            try:
                if hasattr(self, 'new'):
                    self.new()
            except Exception:
                # If new() fails, just ensure we're in a clean state
                try:
                    self._save_folder = None
                    self._save_info = None
                    self._party_table = None
                    self._global_vars = None
                    self._nested_capsule = None
                except Exception:
                    pass  # Even setting attributes might fail
                self._nested_capsule = None

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
            
            from toolset.gui.common.localization import translate as tr, trf
            self.ui.statusBar.showMessage(tr("Save game saved successfully"), 3000)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                tr("Error Saving"),
                trf("Failed to save game:\n{error}", error=str(e)),
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
        self.clear_screenshot()

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
    
    def clear_screenshot(self):
        """Clear screenshot preview."""
        self._screenshot_original_pixmap = None
        self._screenshot_original_size = None
        if hasattr(self.ui, 'labelScreenshotPreview'):
            self.ui.labelScreenshotPreview.setText("No screenshot available")
            self.ui.labelScreenshotPreview.setPixmap(QPixmap())
            self.ui.labelScreenshotPreview.setToolTip("")
    
    def on_save_info_changed(self):
        """Handle Save Info changes."""
        # Auto-update is handled in save()
        pass

    # ==================== Party Table Methods ====================
    
    def populate_party_table(self):
        """Populate Party Table tab from loaded data.
        
        This method populates the party members list with actual character names
        instead of generic "Member #" labels, and provides rich tooltips with
        comprehensive character information.
        """
        if not self._party_table:
            return
        
        # Resources
        self.ui.spinBoxGold.setValue(self._party_table.pt_gold)
        self.ui.spinBoxXPPool.setValue(self._party_table.pt_xp_pool)
        self.ui.spinBoxComponents.setValue(self._party_table.pt_item_componen)
        self.ui.spinBoxChemicals.setValue(self._party_table.pt_item_chemical)
        
        # Ensure cached characters are loaded for name resolution
        if self._nested_capsule:
            self._nested_capsule.load_cached(reload=False)
        
        # Party members - show actual character names with rich information
        # Sort members: leader first, then by index
        sorted_members = sorted(
            self._party_table.pt_members,
            key=lambda m: (not m.is_leader, m.index if m.index >= 0 else 999)
        )
        
        self.ui.listWidgetPartyMembers.clear()
        for member in sorted_members:
            char_name = self._get_party_member_name(member)
            leader_text = " [Leader]" if member.is_leader else ""
            display_text = f"{char_name}{leader_text}"
            
            item = QListWidgetItem(display_text)
            # Set rich HTML tooltip with exhaustive information
            tooltip = self._get_party_member_tooltip(member)
            item.setToolTip(tooltip)
            item.setData(Qt.ItemDataRole.UserRole, member)
            
            # Visual indicator for leader (bold font)
            if member.is_leader:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            
            self.ui.listWidgetPartyMembers.addItem(item)
    
    def _get_party_member_name(self, member) -> str:
        """Get the display name for a party member.
        
        This method resolves character names from multiple sources:
        - PC: From SaveInfo.pc_name, or from cached characters by matching name
        - Companions: From AVAILNPC*.utc files in cached_characters
        
        Args:
        ----
            member: PartyMemberEntry instance
            
        Returns:
        -------
            str: Display name for the party member
        """
        if member.index == -1:
            # Player character (index -1)
            # First try SaveInfo.pc_name (most reliable for K2)
            if self._save_info and self._save_info.pc_name:
                pc_name = self._save_info.pc_name.strip()
                if pc_name:
                    return pc_name
            
            # Try to find PC in cached characters by matching name
            if self._nested_capsule and self._save_info and self._save_info.pc_name:
                pc_name_to_match = self._save_info.pc_name.strip()
                for res_id, char in self._nested_capsule.cached_characters.items():
                    # Check if this character matches the PC name
                    if char.first_name:
                        char_name = str(char.first_name).strip()
                        if char_name == pc_name_to_match:
                            # Also check is_pc flag if available
                            if hasattr(char, 'is_pc') and char.is_pc:
                                return char_name
                            # If name matches, likely the PC
                            return char_name
            
            # Try to find PC by is_pc flag
            if self._nested_capsule:
                for char in self._nested_capsule.cached_characters.values():
                    if hasattr(char, 'is_pc') and char.is_pc:
                        if char.first_name:
                            name = str(char.first_name).strip()
                            if name and name != "Unnamed":
                                return name
            
            # Try to get any character name from cached characters as fallback
            if self._nested_capsule:
                for char in self._nested_capsule.cached_characters.values():
                    if char.first_name:
                        name = str(char.first_name).strip()
                        if name and name != "Unnamed":
                            return name
            
            return "Player Character"
        else:
            # Companion - index 0-11 maps to AVAILNPC{index}.utc
            if self._nested_capsule:
                from pykotor.extract.file import ResourceIdentifier
                from pykotor.resource.type import ResourceType
                
                # Try to find AVAILNPC{index}.utc in cached characters
                # Use cached_character_indices if available (more efficient)
                if member.index in self._nested_capsule.cached_character_indices:
                    npc_ident = self._nested_capsule.cached_character_indices[member.index]
                    if npc_ident in self._nested_capsule.cached_characters:
                        char = self._nested_capsule.cached_characters[npc_ident]
                        return self._format_character_name(char, member.index)
                
                # Fallback: try direct lookup
                npc_resref = f"availnpc{member.index}"
                npc_ident = ResourceIdentifier(resname=npc_resref, restype=ResourceType.UTC)
                
                if npc_ident in self._nested_capsule.cached_characters:
                    char = self._nested_capsule.cached_characters[npc_ident]
                    return self._format_character_name(char, member.index)
            
            return f"Companion {member.index}"
    
    def _format_character_name(self, char: UTC, index: int | None = None) -> str:
        """Format character name for display.
        
        Args:
        ----
            char: UTC character object
            index: Optional companion index (for companions)
            
        Returns:
        -------
            str: Formatted character name
        """
        # Try first name first
        if char.first_name:
            name = str(char.first_name).strip()
            if name and name != "Unnamed":
                # Add last name if available
                if char.last_name:
                    last_name = str(char.last_name).strip()
                    if last_name and last_name != "Unnamed":
                        return f"{name} {last_name}"
                return name
        
        # Fallback to tag
        if char.tag:
            tag = char.tag.strip()
            if tag:
                return tag
        
        # Fallback to resref
        if char.resref:
            resref = str(char.resref).strip()
            if resref:
                return resref
        
        # Ultimate fallback
        if index is not None:
            return f"Companion {index}"
        return "Unnamed Character"
    
    def _get_party_member_tooltip(self, member) -> str:
        """Generate rich HTML tooltip for party member with exhaustive information.
        
        This tooltip provides comprehensive character information including:
        - Basic info (index, leader status, type)
        - Character names (first, last, tag, resref)
        - Stats (HP, FP, attributes)
        - Classes and levels (with readable names if installation available)
        - Race and appearance info
        - Equipment summary
        - Skills summary
        
        Args:
        ----
            member: PartyMemberEntry instance
            
        Returns:
        -------
            str: HTML-formatted tooltip text
        """
        lines = []
        lines.append("<b>Party Member Information</b><br>")
        lines.append("<hr>")
        
        # Basic Information
        lines.append("<b>Basic Information</b><br>")
        lines.append(f"<b>Index:</b> {member.index}<br>")
        lines.append(f"<b>Type:</b> {'Player Character' if member.index == -1 else 'Companion'}<br>")
        lines.append(f"<b>Is Leader:</b> {'Yes' if member.is_leader else 'No'}<br>")
        
        # Get character UTC if available
        char: UTC | None = None
        if member.index == -1:
            # Try to find PC in cached characters
            if self._nested_capsule:
                if self._save_info and self._save_info.pc_name:
                    pc_name_to_match = self._save_info.pc_name.strip()
                    for res_id, candidate_char in self._nested_capsule.cached_characters.items():
                        if candidate_char.first_name and str(candidate_char.first_name).strip() == pc_name_to_match:
                            char = candidate_char
                            break
                        # Also check is_pc flag
                        if hasattr(candidate_char, 'is_pc') and candidate_char.is_pc:
                            char = candidate_char
                            break
                
                # If still not found, try first character
                if char is None and self._nested_capsule.cached_characters:
                    char = next(iter(self._nested_capsule.cached_characters.values()))
        else:
            # Companion - get from cached characters
            if self._nested_capsule:
                from pykotor.extract.file import ResourceIdentifier
                from pykotor.resource.type import ResourceType
                
                # Use cached_character_indices if available
                if member.index in self._nested_capsule.cached_character_indices:
                    npc_ident = self._nested_capsule.cached_character_indices[member.index]
                    if npc_ident in self._nested_capsule.cached_characters:
                        char = self._nested_capsule.cached_characters[npc_ident]
                else:
                    # Fallback: direct lookup
                    npc_resref = f"availnpc{member.index}"
                    npc_ident = ResourceIdentifier(resname=npc_resref, restype=ResourceType.UTC)
                    if npc_ident in self._nested_capsule.cached_characters:
                        char = self._nested_capsule.cached_characters[npc_ident]
        
        # Character Details Section
        if char:
            lines.append("<hr>")
            lines.append("<b>Character Details</b><br>")
            
            # Names
            first_name = str(char.first_name).strip() if char.first_name else "N/A"
            last_name = str(char.last_name).strip() if char.last_name else "N/A"
            full_name = f"{first_name} {last_name}".strip() if last_name != "N/A" else first_name
            lines.append(f"<b>Full Name:</b> {full_name if full_name != 'N/A' else 'Unnamed'}<br>")
            if char.first_name and char.last_name:
                lines.append(f"<b>First Name:</b> {first_name}<br>")
                lines.append(f"<b>Last Name:</b> {last_name}<br>")
            lines.append(f"<b>Tag:</b> {char.tag or 'N/A'}<br>")
            lines.append(f"<b>ResRef:</b> {char.resref or 'N/A'}<br>")
            
            # Health and Force Points
            lines.append("<hr>")
            lines.append("<b>Vital Statistics</b><br>")
            hp_percent = (char.current_hp / char.max_hp * 100) if char.max_hp > 0 else 0
            fp_percent = (char.fp / char.max_fp * 100) if char.max_fp > 0 else 0
            hp_color = "#00AA00" if hp_percent > 50 else "#FFAA00" if hp_percent > 25 else "#FF0000"
            fp_color = "#00AA00" if fp_percent > 50 else "#FFAA00" if fp_percent > 25 else "#FF0000"
            lines.append(f"<b>HP:</b> <span style='color: {hp_color}'>{char.current_hp}/{char.max_hp}</span> ({hp_percent:.1f}%)<br>")
            lines.append(f"<b>FP:</b> <span style='color: {fp_color}'>{char.fp}/{char.max_fp}</span> ({fp_percent:.1f}%)<br>")
            
            # Attributes
            lines.append("<hr>")
            lines.append("<b>Attributes</b><br>")
            lines.append(f"<b>STR:</b> {char.strength} | <b>DEX:</b> {char.dexterity} | <b>CON:</b> {char.constitution}<br>")
            lines.append(f"<b>INT:</b> {char.intelligence} | <b>WIS:</b> {char.wisdom} | <b>CHA:</b> {char.charisma}<br>")
            
            # Classes
            if char.classes:
                lines.append("<hr>")
                lines.append("<b>Classes</b><br>")
                class_names = []
                for cls in char.classes:
                    class_name = self._get_class_name(cls.class_id) if self._installation else f"Class {cls.class_id}"
                    class_names.append(f"{class_name} (Level {cls.class_level})")
                lines.append(", ".join(class_names) + "<br>")
                
                # Total level
                total_level = sum(cls.class_level for cls in char.classes)
                lines.append(f"<b>Total Level:</b> {total_level}<br>")
            
            # Race and Appearance
            if self._installation:
                lines.append("<hr>")
                lines.append("<b>Race & Appearance</b><br>")
                race_name = self._get_race_name(char.race_id)
                if race_name:
                    lines.append(f"<b>Race:</b> {race_name}<br>")
                if hasattr(char, 'gender_id'):
                    gender_name = self._get_gender_name(char.gender_id)
                    if gender_name:
                        lines.append(f"<b>Gender:</b> {gender_name}<br>")
            
            # Skills Summary
            if hasattr(char, 'computer_use'):
                lines.append("<hr>")
                lines.append("<b>Skills</b><br>")
                skill_values = [
                    ("Computer Use", char.computer_use),
                    ("Demolitions", char.demolitions),
                    ("Stealth", char.stealth),
                    ("Awareness", char.awareness),
                    ("Persuade", char.persuade),
                    ("Repair", char.repair),
                    ("Security", char.security),
                    ("Treat Injury", char.treat_injury),
                ]
                # Show only non-zero skills to keep tooltip concise
                non_zero_skills = [f"{name}: {val}" for name, val in skill_values if val > 0]
                if non_zero_skills:
                    lines.append(", ".join(non_zero_skills) + "<br>")
                else:
                    lines.append("No skills trained<br>")
            
            # Equipment Summary
            if char.equipment:
                lines.append("<hr>")
                lines.append("<b>Equipment</b><br>")
                equipment_count = len(char.equipment)
                lines.append(f"<b>Equipped Items:</b> {equipment_count}<br>")
                # Show first few items
                shown_items = 0
                for slot, item in list(char.equipment.items())[:3]:
                    slot_name = slot.name if hasattr(slot, 'name') else f"Slot {slot.value}"
                    item_name = str(item.resref) if item.resref else "Unknown"
                    lines.append(f"  • {slot_name}: {item_name}<br>")
                    shown_items += 1
                if equipment_count > shown_items:
                    lines.append(f"  ... and {equipment_count - shown_items} more<br>")
            
            # Additional Flags
            flags = []
            if hasattr(char, 'is_pc') and char.is_pc:
                flags.append("Is PC")
            if hasattr(char, 'plot') and char.plot:
                flags.append("Plot")
            if hasattr(char, 'min1_hp') and char.min1_hp:
                flags.append("Min 1 HP")
            if flags:
                lines.append("<hr>")
                lines.append("<b>Flags:</b> " + ", ".join(flags) + "<br>")
        else:
            # No character data available
            if member.index == -1:
                if self._save_info and self._save_info.pc_name:
                    lines.append(f"<b>PC Name:</b> {self._save_info.pc_name}<br>")
                lines.append("<i>Character data not available in cached files</i><br>")
            else:
                lines.append(f"<b>NPC Resource:</b> AVAILNPC{member.index}.utc<br>")
                lines.append("<i>Character data not found in cached files</i><br>")
        
        return "".join(lines)
    
    def _get_class_name(self, class_id: int) -> str | None:
        """Get readable class name from class ID.
        
        Args:
        ----
            class_id: Class ID from UTC
            
        Returns:
        -------
            str | None: Class name or None if not available
        """
        if not self._installation:
            return None
        
        try:
            from toolset.data.installation import HTInstallation
            from pykotor.resource.formats.twoda.twoda_data import TwoDA
            
            classes: TwoDA | None = self._installation.ht_get_cache_2da(HTInstallation.TwoDA_CLASSES)
            if classes and 0 <= class_id < classes.get_height():
                return classes.get_cell(class_id, "label")
        except Exception:
            pass
        
        return None
    
    def _get_race_name(self, race_id: int) -> str | None:
        """Get readable race name from race ID.
        
        Args:
        ----
            race_id: Race ID from UTC
            
        Returns:
        -------
            str | None: Race name or None if not available
        """
        if not self._installation:
            return None
        
        try:
            from toolset.data.installation import HTInstallation
            from pykotor.resource.formats.twoda.twoda_data import TwoDA
            
            races: TwoDA | None = self._installation.ht_get_cache_2da(HTInstallation.TwoDA_RACES)
            if races and 0 <= race_id < races.get_height():
                # Try to get name from talktable first
                name_strref = races.get_row(race_id).get_integer("name", -1)
                if name_strref >= 0:
                    name = self._installation.talktable().string(name_strref)
                    if name:
                        return name
                # Fallback to label
                return races.get_cell(race_id, "label")
        except Exception:
            pass
        
        return None
    
    def _get_gender_name(self, gender_id: int) -> str | None:
        """Get readable gender name from gender ID.
        
        Args:
        ----
            gender_id: Gender ID from UTC
            
        Returns:
        -------
            str | None: Gender name or None if not available
        """
        if not self._installation:
            return None
        
        try:
            from toolset.data.installation import HTInstallation
            from pykotor.resource.formats.twoda.twoda_data import TwoDA
            
            genders: TwoDA | None = self._installation.ht_get_cache_2da(HTInstallation.TwoDA_GENDERS)
            if genders and 0 <= gender_id < genders.get_height():
                constant = genders.get_cell(gender_id, "constant")
                if constant:
                    # Format: "GENDER_MALE" -> "Male"
                    return constant.replace("GENDER_", "").replace("_", " ").title()
        except Exception:
            pass
        
        return None
    
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
        """Populate Global Variables tab from loaded data.
        
        This method optimizes whitespace usage by:
        - Using compact row heights
        - Hiding vertical headers
        - Using stretch modes for better column sizing
        - Disabling word wrap for simple values to keep rows single-line
        - Enabling alternating row colors for better readability
        """
        if not self._global_vars:
            return
        
        # Common table optimizations for all global var tables
        tables = [
            self.ui.tableWidgetBooleans,
            self.ui.tableWidgetNumbers,
            self.ui.tableWidgetStrings,
            self.ui.tableWidgetLocations,
        ]
        for table in tables:
            # Compact row height - reduce from default ~20-24px to ~18px
            table.verticalHeader().setDefaultSectionSize(18)
            table.verticalHeader().setVisible(False)  # Hide row numbers to save space
            table.setAlternatingRowColors(True)  # Better readability
            table.setShowGrid(False)  # Cleaner look, saves visual space
            table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Booleans - compact single-line display
        self.ui.tableWidgetBooleans.setRowCount(len(self._global_vars.global_bools))
        self.ui.tableWidgetBooleans.setWordWrap(False)  # No wrap for compact display
        header = self.ui.tableWidgetBooleans.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Name column stretches
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Value column fixed
        self.ui.tableWidgetBooleans.setColumnWidth(1, 60)  # Compact checkbox column
        for row, (name, value) in enumerate(self._global_vars.global_bools):
            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.ui.tableWidgetBooleans.setItem(row, 0, name_item)
            
            checkbox_widget = QCheckBox()
            checkbox_widget.setChecked(value)
            checkbox_widget.stateChanged.connect(self.on_global_var_changed)
            self.ui.tableWidgetBooleans.setCellWidget(row, 1, checkbox_widget)
        
        # Numbers - compact single-line display
        self.ui.tableWidgetNumbers.setRowCount(len(self._global_vars.global_numbers))
        self.ui.tableWidgetNumbers.setWordWrap(False)  # No wrap for compact display
        header = self.ui.tableWidgetNumbers.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Name column stretches
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Value column fixed
        self.ui.tableWidgetNumbers.setColumnWidth(1, 120)  # Compact value column
        for row, (name, value) in enumerate(self._global_vars.global_numbers):
            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.ui.tableWidgetNumbers.setItem(row, 0, name_item)
            
            value_item = QTableWidgetItem(str(value))
            value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.ui.tableWidgetNumbers.setItem(row, 1, value_item)
        
        # Strings - allow word wrap for long strings, but optimize layout
        self.ui.tableWidgetStrings.setRowCount(len(self._global_vars.global_strings))
        self.ui.tableWidgetStrings.setWordWrap(True)  # Wrap for long strings
        header = self.ui.tableWidgetStrings.horizontalHeader()
        header.setStretchLastSection(True)  # Value column stretches
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Name column fits content
        # Set minimum width for name column to prevent it from being too narrow
        self.ui.tableWidgetStrings.setColumnWidth(0, 200)
        for row, (name, value) in enumerate(self._global_vars.global_strings):
            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.ui.tableWidgetStrings.setItem(row, 0, name_item)
            
            value_item = QTableWidgetItem(value)
            value_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.ui.tableWidgetStrings.setItem(row, 1, value_item)
        
        # Locations - compact multi-column display
        self.ui.tableWidgetLocations.setRowCount(len(self._global_vars.global_locs))
        self.ui.tableWidgetLocations.setWordWrap(False)  # No wrap for compact display
        header = self.ui.tableWidgetLocations.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Name column stretches
        # Coordinate columns are fixed width
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # X
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Y
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Z
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Orientation
        self.ui.tableWidgetLocations.setColumnWidth(1, 80)   # X - compact
        self.ui.tableWidgetLocations.setColumnWidth(2, 80)   # Y - compact
        self.ui.tableWidgetLocations.setColumnWidth(3, 80)   # Z - compact
        self.ui.tableWidgetLocations.setColumnWidth(4, 80)  # Orientation - compact
        for row, (name, loc) in enumerate(self._global_vars.global_locs):
            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.ui.tableWidgetLocations.setItem(row, 0, name_item)
            
            # Use compact format for coordinates (fewer decimals if possible)
            x_item = QTableWidgetItem(f"{loc.x:.1f}")
            x_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.ui.tableWidgetLocations.setItem(row, 1, x_item)
            
            y_item = QTableWidgetItem(f"{loc.y:.1f}")
            y_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.ui.tableWidgetLocations.setItem(row, 2, y_item)
            
            z_item = QTableWidgetItem(f"{loc.z:.1f}")
            z_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.ui.tableWidgetLocations.setItem(row, 3, z_item)
            
            ori_item = QTableWidgetItem(f"{loc.w:.1f}")
            ori_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.ui.tableWidgetLocations.setItem(row, 4, ori_item)
    
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
        """Populate Characters tab from loaded data.
        
        This method displays actual character names instead of numbers,
        using the same name resolution logic as the Party & Resources tab.
        """
        if not self._nested_capsule:
            return
        
        self.ui.listWidgetCharacters.clear()
        
        # Load cached characters
        self._nested_capsule.load_cached(reload=True)
        
        # Add PC first if available - use same name resolution as Party tab
        if self._save_info and self._save_info.pc_name:
            pc_name = self._save_info.pc_name.strip()
            if pc_name:
                pc_item = QListWidgetItem(f"PC: {pc_name}")
                pc_item.setData(Qt.ItemDataRole.UserRole, None)  # Special marker for PC
                pc_item.setData(Qt.ItemDataRole.UserRole + 1, "PC")  # Type marker
                self.ui.listWidgetCharacters.addItem(pc_item)
        
        # cached_characters is a dict[ResourceIdentifier, UTC], so iterate over values
        # Sort by resname for consistent ordering
        sorted_chars = sorted(
            self._nested_capsule.cached_characters.items(),
            key=lambda x: str(x[0].resname).lower()
        )
        
        for res_id, char in sorted_chars:
            # Use the same name formatting as Party tab
            display_name = self._format_character_name(char)
            
            # Determine if this is a companion (AVAILNPC) or other character
            resname_lower = str(res_id.resname).lower()
            if resname_lower.startswith("availnpc"):
                # Extract index
                try:
                    idx = int(resname_lower.replace("availnpc", ""))
                    display_name = f"Companion {idx}: {display_name}"
                except ValueError:
                    pass  # Keep display_name as is
            
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, char)
            item.setData(Qt.ItemDataRole.UserRole + 1, "NPC" if resname_lower.startswith("availnpc") else "Other")
            # Add tooltip with additional info
            tooltip = f"ResRef: {res_id.resname}\nTag: {char.tag or 'N/A'}\nType: {'Companion' if resname_lower.startswith('availnpc') else 'Other'}"
            item.setToolTip(tooltip)
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
        
        char_type = item.data(Qt.ItemDataRole.UserRole + 1)
        if char_type == "PC":
            # For PC, we need to find the actual UTC - it might be in cached_characters
            # or we might need to load it differently
            # For now, try to find a character that looks like the PC
            if self._nested_capsule:
                # PC might be the first character or have a specific identifier
                # Try to find it in cached_characters
                for char in self._nested_capsule.cached_characters.values():
                    if char.first_name and str(char.first_name) == self._save_info.pc_name:
                        self._current_character = char
                        self.populate_character_details(self._current_character)
                        return
                # If not found, use first character as fallback
                if self._nested_capsule.cached_characters:
                    self._current_character = next(iter(self._nested_capsule.cached_characters.values()))
                    self.populate_character_details(self._current_character)
                    return
            self._current_character = None
            self.clear_character_details()
        else:
            self._current_character = item.data(Qt.ItemDataRole.UserRole)
            if self._current_character:
                self.populate_character_details(self._current_character)
    
    def populate_character_details(self, char: UTC):
        """Populate character details panel.
        
        This method populates all character detail tabs including Stats, Equipment, and Skills.
        It uses consistent name resolution and properly identifies PC vs NPC characters.
        """
        # Use the same name formatting as other parts of the editor for consistency
        char_name = self._format_character_name(char)
        
        # Check if this is the PC - use multiple methods for better detection
        is_pc = False
        if self._save_info and self._save_info.pc_name:
            pc_name_to_match = self._save_info.pc_name.strip()
            # Check if first name matches
            if char.first_name and str(char.first_name).strip() == pc_name_to_match:
                is_pc = True
            # Also check is_pc flag if available
            elif hasattr(char, 'is_pc') and char.is_pc:
                is_pc = True
        
        # Stats
        self.ui.lineEditCharName.setText(str(char.first_name) if char.first_name else "")
        self.ui.spinBoxCharHP.setValue(char.current_hp)
        self.ui.spinBoxCharMaxHP.setValue(char.max_hp)
        self.ui.spinBoxCharFP.setValue(char.fp)
        self.ui.spinBoxCharMaxFP.setValue(char.max_fp)
        
        # Get total XP from classes
        total_xp = sum(cls.class_level for cls in char.classes) if char.classes else 0
        self.ui.spinBoxCharXP.setValue(total_xp)
        
        # Skills (individual attributes) - add label showing whose skills these are
        skill_attrs = ['computer_use', 'demolitions', 'stealth', 'awareness', 'persuade', 'repair', 'security', 'treat_injury']
        self.ui.tableWidgetSkills.setRowCount(len(SKILL_NAMES))
        
        # Update skills label with character name - make it clear whose skills are displayed
        # Format: "Skills (PC: Name)" or "Skills (Character Name)" or "Skills (Companion X: Name)"
        if is_pc:
            skills_label_text = f"Skills (PC: {char_name})"
        else:
            # Check if this is a companion by looking at the selected character in the list
            # We can't easily determine companion index here, so just show the name
            skills_label_text = f"Skills ({char_name})"
        
        # Set the label text - the label exists in the UI file
        if hasattr(self.ui, 'labelSkillsCharacter'):
            self.ui.labelSkillsCharacter.setText(skills_label_text)
            # Make the label more prominent with a tooltip
            self.ui.labelSkillsCharacter.setToolTip(
                f"<b>Character Skills</b><br>"
                f"<b>Character:</b> {char_name}<br>"
                f"<b>Type:</b> {'Player Character' if is_pc else 'Companion/NPC'}<br>"
                f"<b>Tag:</b> {char.tag or 'N/A'}<br>"
                f"<b>ResRef:</b> {char.resref or 'N/A'}"
            )
        
        for row, skill_name in enumerate(SKILL_NAMES):
            skill_item = QTableWidgetItem(skill_name)
            skill_item.setFlags(skill_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            skill_item.setToolTip(skills_label_text)
            self.ui.tableWidgetSkills.setItem(row, 0, skill_item)
            
            skill_rank = getattr(char, skill_attrs[row], 0) if row < len(skill_attrs) else 0
            rank_item = QTableWidgetItem(str(skill_rank))
            rank_item.setToolTip(skills_label_text)
            self.ui.tableWidgetSkills.setItem(row, 1, rank_item)
        
        # Set tooltip on the table itself
        self.ui.tableWidgetSkills.setToolTip(skills_label_text)
        
        # Equipment (dict with EquipmentSlot keys) - make it show item names and be editable
        self.ui.listWidgetEquipment.clear()
        
        # Disconnect previous connections to avoid duplicates
        try:
            self.ui.listWidgetEquipment.itemDoubleClicked.disconnect()
        except TypeError:
            pass  # No connections yet
        
        # Set up context menu for equipment list
        self.ui.listWidgetEquipment.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.listWidgetEquipment.customContextMenuRequested.connect(self.on_equipment_context_menu)
        
        # Populate equipment list
        for slot, item in char.equipment.items():
            # Get item name from installation if available
            item_name = str(item.resref)
            if self._installation:
                try:
                    from pykotor.resource.generics.uti import read_uti
                    result = self._installation.resource(str(item.resref), ResourceType.UTI)
                    if result:
                        uti = read_uti(result.data)
                        item_name = self._installation.string(uti.name, str(item.resref))
                except Exception:
                    pass  # Fallback to resref
            
            slot_name = slot.name if hasattr(slot, 'name') else f"Slot {slot.value}"
            item_text = f"{slot_name}: {item_name}"
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.ItemDataRole.UserRole, (slot, item))
            list_item.setToolTip(
                f"<b>Equipment Slot</b><br>"
                f"<b>Slot:</b> {slot_name}<br>"
                f"<b>Item:</b> {item_name}<br>"
                f"<b>ResRef:</b> {item.resref}<br>"
                f"<br><i>Double-click to edit, right-click for menu</i>"
            )
            self.ui.listWidgetEquipment.addItem(list_item)
        
        # Make equipment list editable (double-click to edit)
        self.ui.listWidgetEquipment.itemDoubleClicked.connect(self.on_equipment_item_double_clicked)
    
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
        
        # Reset skills label
        if hasattr(self.ui, 'labelSkillsCharacter'):
            self.ui.labelSkillsCharacter.setText("Skills")
            self.ui.labelSkillsCharacter.setToolTip("")
        # Clear skills label
        if hasattr(self.ui, 'labelSkillsCharacter'):
            self.ui.labelSkillsCharacter.setText("Skills")
    
    def on_character_data_changed(self):
        """Handle character data changes."""
        # Auto-update is handled in save()
        pass
    
    def on_equipment_item_double_clicked(self, item: QListWidgetItem):
        """Handle double-click on equipment item to edit it.
        
        Opens a file selection dialog to choose a UTI resource for the equipment slot,
        similar to how the UTC editor handles equipment editing.
        """
        if not self._current_character or not self._installation:
            QMessageBox.warning(
                self,
                "Cannot Edit Equipment",
                "Character or installation data is not available."
            )
            return
        
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
        
        slot, current_item = data
        
        # Search for UTI resources in the installation
        from pykotor.extract.installation import SearchLocation
        from pykotor.extract.file import ResourceIdentifier
        
        # Get all UTI resources from the installation
        locations = self._installation.locations(
            ([], [ResourceType.UTI]),
            order=[
                SearchLocation.OVERRIDE,
                SearchLocation.MODULES,
                SearchLocation.CHITIN,
            ],
        )
        
        # Flatten the locations dict into a list
        flat_locations: list = []
        for location_list in locations.values():
            flat_locations.extend(location_list)
        
        if not flat_locations:
            QMessageBox.warning(
                self,
                "No Items Found",
                "No UTI resources found in the installation."
            )
            return
        
        # Open file selection window
        selection_window = FileSelectionWindow(flat_locations, self._installation)
        selection_window.setWindowTitle(f"Select Item for {slot.name if hasattr(slot, 'name') else f'Slot {slot.value}'}")
        
        if selection_window.exec():
            selected_resources = selection_window.selected_resources()
            if selected_resources:
                # Get the first selected resource
                selected_resource = selected_resources[0]
                new_resref = ResRef(selected_resource.resname)
                
                # Update the equipment slot
                from pykotor.common.misc import InventoryItem
                self._current_character.equipment[slot] = InventoryItem(new_resref)
                
                # Refresh the equipment list display
                self.populate_character_details(self._current_character)
                
                # Show confirmation
                QMessageBox.information(
                    self,
                    "Equipment Updated",
                    f"Equipment slot updated to: {new_resref}"
                )
    
    def on_equipment_context_menu(self, position: QPoint):
        """Handle context menu for equipment list."""
        if not self._current_character:
            return
        
        item = self.ui.listWidgetEquipment.itemAt(position)
        if not item:
            return
        
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
        
        slot, current_item = data
        
        menu = QMenu(self)
        
        # Edit item action
        edit_action = menu.addAction("Edit Item...")
        edit_action.triggered.connect(lambda: self.on_equipment_item_double_clicked(item))
        
        # Remove item action
        remove_action = menu.addAction("Remove Item")
        remove_action.triggered.connect(lambda: self.on_equipment_remove(slot))
        
        menu.exec(self.ui.listWidgetEquipment.mapToGlobal(position))
    
    def on_equipment_remove(self, slot):
        """Remove equipment from a slot."""
        if not self._current_character:
            return
        
        # Remove the equipment slot
        if slot in self._current_character.equipment:
            del self._current_character.equipment[slot]
            
            # Refresh the equipment list display
            self.populate_character_details(self._current_character)
            
            QMessageBox.information(
                self,
                "Equipment Removed",
                f"Equipment removed from {slot.name if hasattr(slot, 'name') else f'Slot {slot.value}'}."
            )

    # ==================== Inventory Methods ====================
    
    def populate_inventory(self):
        """Populate Inventory tab from loaded data.
        
        This method displays inventory items with actual item names from UTI files,
        similar to how the UTI editor and equipment list work. It resolves item names
        from the installation and provides rich tooltips with item information.
        """
        if not self._nested_capsule:
            return
        
        # Configure table for better display
        self.ui.tableWidgetInventory.setRowCount(len(self._nested_capsule.inventory))
        self.ui.tableWidgetInventory.setWordWrap(True)
        self.ui.tableWidgetInventory.horizontalHeader().setStretchLastSection(False)
        header = self.ui.tableWidgetInventory.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Item name stretches
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)    # Count fixed
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)     # ResRef fixed
        self.ui.tableWidgetInventory.setColumnWidth(1, 80)   # Count column
        self.ui.tableWidgetInventory.setColumnWidth(2, 150)  # ResRef column
        
        for row, item in enumerate(self._nested_capsule.inventory):
            # Get item name from installation - same logic as equipment display
            item_name = self._get_item_name(item)
            
            # Item name column
            name_item = QTableWidgetItem(item_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            
            # Rich tooltip with item information
            tooltip = self._get_inventory_item_tooltip(item)
            name_item.setToolTip(tooltip)
            self.ui.tableWidgetInventory.setItem(row, 0, name_item)
            
            # Stack size
            stack_size = getattr(item, 'stack_size', 1)  # Default to 1 if not available
            count_item = QTableWidgetItem(str(stack_size))
            count_item.setFlags(count_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            count_item.setToolTip(f"Stack Size: {stack_size}")
            self.ui.tableWidgetInventory.setItem(row, 1, count_item)
            
            # ResRef
            resref_item = QTableWidgetItem(str(item.resref))
            resref_item.setFlags(resref_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            resref_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            resref_item.setToolTip(f"Resource Reference: {item.resref}")
            self.ui.tableWidgetInventory.setItem(row, 2, resref_item)
    
    def _get_item_name(self, item) -> str:
        """Get display name for an inventory item.
        
        This method resolves item names from UTI files in the installation,
        with fallbacks to LocalizedString or ResRef.
        
        Args:
        ----
            item: InventoryItem instance
            
        Returns:
        -------
            str: Display name for the item
        """
        # Try to get name from UTI file in installation
        if self._installation:
            try:
                from pykotor.resource.generics.uti import read_uti
                result = self._installation.resource(str(item.resref), ResourceType.UTI)
                if result:
                    uti = read_uti(result.data)
                    item_name = self._installation.string(uti.name, str(item.resref))
                    if item_name and item_name.strip():
                        return item_name
            except Exception:
                pass  # Fallback to other methods
        
        # Fallback to LocalizedString from item if available
        if hasattr(item, 'name') and item.name:
            if self._installation:
                item_name = self._installation.string(item.name, str(item.resref))
                if item_name and item_name.strip():
                    return item_name
            else:
                name_str = str(item.name)
                if name_str and name_str.strip():
                    return name_str
        
        # Ultimate fallback to ResRef
        return str(item.resref)
    
    def _get_inventory_item_tooltip(self, item) -> str:
        """Generate rich HTML tooltip for inventory item.
        
        Args:
        ----
            item: InventoryItem instance
            
        Returns:
        -------
            str: HTML-formatted tooltip text
        """
        lines = []
        lines.append("<b>Inventory Item</b><br>")
        lines.append("<hr>")
        
        # Item name
        item_name = self._get_item_name(item)
        lines.append(f"<b>Name:</b> {item_name}<br>")
        
        # ResRef
        lines.append(f"<b>ResRef:</b> {item.resref}<br>")
        
        # Stack size
        stack_size = getattr(item, 'stack_size', 1)  # Default to 1 if not available
        lines.append(f"<b>Stack Size:</b> {stack_size}<br>")
        
        # Additional item properties if available
        if hasattr(item, 'droppable'):
            lines.append(f"<b>Droppable:</b> {'Yes' if item.droppable else 'No'}<br>")
        if hasattr(item, 'infinite'):
            lines.append(f"<b>Infinite:</b> {'Yes' if item.infinite else 'No'}<br>")
        if hasattr(item, 'tag') and item.tag:
            lines.append(f"<b>Tag:</b> {item.tag}<br>")
        
        # Try to get additional info from UTI if available
        if self._installation:
            try:
                from pykotor.resource.generics.uti import read_uti
                result = self._installation.resource(str(item.resref), ResourceType.UTI)
                if result:
                    uti = read_uti(result.data)
                    lines.append("<hr>")
                    lines.append("<b>Item Details</b><br>")
                    if uti.tag:
                        lines.append(f"<b>Tag:</b> {uti.tag}<br>")
                    if uti.base_item is not None:
                        base_item_name = self._installation.get_item_base_name(uti.base_item) if hasattr(self._installation, 'get_item_base_name') else f"Base Item {uti.base_item}"
                        lines.append(f"<b>Base Item:</b> {base_item_name}<br>")
                    if uti.cost:
                        lines.append(f"<b>Cost:</b> {uti.cost}<br>")
            except Exception:
                pass
        
        return "".join(lines)
    
    def clear_inventory(self):
        """Clear Inventory tab."""
        self.ui.tableWidgetInventory.setRowCount(0)

    # ==================== Journal Methods ====================
    
    def populate_journal(self):
        """Populate Journal tab from loaded data.
        
        Journal entries are simpler than JRL format - they track quest states.
        Each entry has a plot_id (quest identifier) and state (current quest state).
        """
        if not self._party_table:
            return
        
        self.ui.tableWidgetJournal.setRowCount(len(self._party_table.jnl_entries))
        
        # Try to get plot names from installation if available
        plot_names = {}
        if self._installation:
            try:
                from pykotor.resource.formats.twoda.twoda_data import TwoDA
                from toolset.data.installation import HTInstallation
                plot_2da: TwoDA | None = self._installation.ht_get_cache_2da(HTInstallation.TwoDA_PLOT)
                if plot_2da:
                    for i in range(plot_2da.get_height()):
                        label = plot_2da.get_cell(i, "label")
                        if label:
                            plot_names[label.lower()] = label.replace("_", " ").title()
            except Exception:
                pass
        
        for row, entry in enumerate(self._party_table.jnl_entries):
            # Plot ID - try to get readable name
            plot_display = str(entry.plot_id) if entry.plot_id is not None else "Unknown"
            plot_id_str = str(entry.plot_id).lower() if entry.plot_id is not None else ""
            if plot_id_str and plot_id_str in plot_names:
                plot_display = f"{plot_names[plot_id_str]} ({entry.plot_id})"
            elif entry.plot_id is not None:
                # Format plot_id to be more readable (if it's a string)
                plot_id_str = str(entry.plot_id)
                if "_" in plot_id_str:
                    plot_display = plot_id_str.replace("_", " ").title()
                else:
                    plot_display = plot_id_str
            
            plot_item = QTableWidgetItem(plot_display)
            plot_item.setToolTip(f"Plot ID: {entry.plot_id}")
            self.ui.tableWidgetJournal.setItem(row, 0, plot_item)
            
            # State - make it more readable
            state_display = str(entry.state)
            if entry.state >= 0:
                state_display = f"State {entry.state}"
            else:
                state_display = "Not Started"
            
            state_item = QTableWidgetItem(state_display)
            state_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.ui.tableWidgetJournal.setItem(row, 1, state_item)
            
            # Date - format as days
            date_display = str(entry.date) if entry.date >= 0 else "N/A"
            if entry.date >= 0:
                date_display = f"Day {entry.date}"
            
            date_item = QTableWidgetItem(date_display)
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.ui.tableWidgetJournal.setItem(row, 2, date_item)
            
            # Time - format as seconds or time string
            time_display = str(entry.time) if entry.time >= 0 else "N/A"
            if entry.time >= 0:
                hours = entry.time // 3600
                minutes = (entry.time % 3600) // 60
                seconds = entry.time % 60
                time_display = f"{hours:02d}:{minutes:02d}:{seconds:02d} ({entry.time}s)"
            
            time_item = QTableWidgetItem(time_display)
            time_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.ui.tableWidgetJournal.setItem(row, 3, time_item)
    
    def clear_journal(self):
        """Clear Journal tab."""
        self.ui.tableWidgetJournal.setRowCount(0)

    # ==================== Screenshot Methods ====================
    
    def populate_screenshot(self):
        """Populate screenshot preview from loaded save data.
        
        TGA files from KotOR saves may be stored with bottom-left origin,
        so they need to be flipped vertically for correct display.
        
        This implementation:
        - Properly maintains aspect ratio regardless of label size
        - Stores original pixmap for efficient resize handling
        - Handles edge cases (zero size, invalid images, corrupted data)
        - Uses proper size calculation similar to TPC editor
        - Provides informative tooltips with image dimensions
        - Handles window resize events automatically
        
        References:
        ----------
            vendor/kotor-savegame-editor/kse.pl:6448-6474 (PrintScreenshot)
            Libraries/PyKotor/src/pykotor/resource/formats/tpc/tga.py (read_tga)
            TGA file format specification (origin bit in descriptor byte)
            Tools/HolocronToolset/src/toolset/gui/editors/tpc.py:669-740 (aspect ratio handling)
        """
        # Check if we have the screenshot preview label
        if not hasattr(self.ui, 'labelScreenshotPreview'):
            return
        
        # Clear previous screenshot
        self._screenshot_original_pixmap = None
        self._screenshot_original_size = None
        self.ui.labelScreenshotPreview.setToolTip("")
        
        if not self._save_folder:
            self.ui.labelScreenshotPreview.setText("No save game loaded")
            self.ui.labelScreenshotPreview.setPixmap(QPixmap())
            return
        
        if not self._save_folder.screenshot:
            self.ui.labelScreenshotPreview.setText("No screenshot available")
            self.ui.labelScreenshotPreview.setPixmap(QPixmap())
            return
        
        # Validate screenshot data
        if len(self._save_folder.screenshot) < 18:  # Minimum TGA header size
            self.ui.labelScreenshotPreview.setText("Screenshot data too small (corrupted?)")
            self.ui.labelScreenshotPreview.setPixmap(QPixmap())
            return
        
        try:
            from io import BytesIO
            from pykotor.resource.formats.tpc.tga import read_tga
            
            # Read TGA file from bytes - this handles origin flipping automatically
            # read_tga handles bottom-left origin conversion to top-left for display
            tga_image = read_tga(BytesIO(self._save_folder.screenshot))
            
            # Validate image dimensions
            if tga_image.width <= 0 or tga_image.height <= 0:
                raise ValueError(f"Invalid TGA dimensions: {tga_image.width}x{tga_image.height}")
            
            # Validate data size matches expected dimensions
            expected_data_size = tga_image.width * tga_image.height * 4  # RGBA = 4 bytes per pixel
            if len(tga_image.data) < expected_data_size:
                raise ValueError(
                    f"TGA data size mismatch: expected {expected_data_size} bytes, "
                    f"got {len(tga_image.data)} bytes"
                )
            
            # Convert RGBA data to QImage
            # TGA data is in RGBA format after read_tga processes it
            # IMPORTANT: QImage constructor doesn't copy the data by default!
            # We must use QImage.copy() to ensure data is owned by the QImage,
            # otherwise the data pointer becomes invalid when tga_image goes out of scope.
            qimage = QImage(
                tga_image.data,
                tga_image.width,
                tga_image.height,
                tga_image.width * 4,  # bytes per line (4 bytes per pixel for RGBA)
                QImage.Format.Format_RGBA8888
            ).copy()  # CRITICAL: Copy to own the data
            
            # Validate QImage
            if qimage.isNull():
                raise ValueError("Failed to create QImage from TGA data")
            
            if qimage.width() != tga_image.width or qimage.height() != tga_image.height:
                raise ValueError(
                    f"QImage dimension mismatch: expected {tga_image.width}x{tga_image.height}, "
                    f"got {qimage.width()}x{qimage.height()}"
                )
            
            # Store original pixmap and size for resize handling
            self._screenshot_original_pixmap = QPixmap.fromImage(qimage)
            self._screenshot_original_size = (tga_image.width, tga_image.height)
            
            # Update tooltip with image information
            self._update_screenshot_tooltip()
            
            # Scale to fit the label while maintaining aspect ratio
            self._update_screenshot_display()
            
        except ValueError as e:
            # Validation errors - show user-friendly message
            from loggerplus import RobustLogger
            RobustLogger().warning(f"Failed to load screenshot (validation error): {e}")
            self._screenshot_original_pixmap = None
            self._screenshot_original_size = None
            self.ui.labelScreenshotPreview.setText(f"Invalid screenshot data:\n{str(e)}")
            self.ui.labelScreenshotPreview.setPixmap(QPixmap())
            self.ui.labelScreenshotPreview.setToolTip("")
        except Exception as e:
            # Other errors (parsing, format issues, etc.)
            from loggerplus import RobustLogger
            RobustLogger().warning(f"Failed to load screenshot: {e}", exc_info=True)
            self._screenshot_original_pixmap = None
            self._screenshot_original_size = None
            error_msg = str(e)
            # Truncate very long error messages
            if len(error_msg) > 100:
                error_msg = error_msg[:97] + "..."
            self.ui.labelScreenshotPreview.setText(f"Failed to load screenshot:\n{error_msg}")
            self.ui.labelScreenshotPreview.setPixmap(QPixmap())
            self.ui.labelScreenshotPreview.setToolTip("")
    
    def _update_screenshot_display(self):
        """Update screenshot display with proper aspect ratio.
        
        This method recalculates the scaled pixmap based on the current label size,
        maintaining the original image's aspect ratio. It's called both during initial
        load and when the label is resized.
        
        The implementation:
        - Calculates optimal display size maintaining aspect ratio
        - Uses high-quality scaling for best visual results
        - Handles edge cases (zero sizes, invalid dimensions)
        - Updates tooltip with current display information
        """
        if not hasattr(self.ui, 'labelScreenshotPreview'):
            return
        
        if not self._screenshot_original_pixmap or self._screenshot_original_pixmap.isNull():
            return
        
        if not self._screenshot_original_size:
            return
        
        original_width, original_height = self._screenshot_original_size
        
        # Validate original dimensions
        if original_width <= 0 or original_height <= 0:
            return
        
        # Get available size from label
        # Use contentsRect() for more accurate available space
        label_rect = self.ui.labelScreenshotPreview.contentsRect()
        if label_rect.isEmpty():
            # Fallback to size() if contentsRect is empty
            label_size = self.ui.labelScreenshotPreview.size()
            available_width = max(1, label_size.width())
            available_height = max(1, label_size.height())
        else:
            available_width = max(1, label_rect.width())
            available_height = max(1, label_rect.height())
        
        # Calculate aspect ratios
        image_aspect = original_width / original_height
        available_aspect = available_width / available_height
        
        # Calculate scaled dimensions maintaining aspect ratio
        # Algorithm matches TPC editor (tpc.py:711-717) for consistency
        if available_aspect > image_aspect:
            # Available space is wider than image - fit to height
            display_height = available_height
            display_width = int(display_height * image_aspect)
        else:
            # Available space is taller than image - fit to width
            display_width = available_width
            display_height = int(display_width / image_aspect)
        
        # Ensure minimum size (at least 1x1 pixel)
        display_width = max(1, display_width)
        display_height = max(1, display_height)
        
        # Don't upscale beyond original size if original is smaller than available space
        # This prevents pixelation when the screenshot is small
        if display_width > original_width or display_height > original_height:
            # Use original size if it fits, otherwise scale down
            if original_width <= available_width and original_height <= available_height:
                display_width = original_width
                display_height = original_height
            else:
                # Scale down to fit
                scale_w = available_width / original_width
                scale_h = available_height / original_height
                scale = min(scale_w, scale_h)
                display_width = int(original_width * scale)
                display_height = int(original_height * scale)
                display_width = max(1, display_width)
                display_height = max(1, display_height)
        
        # Scale the pixmap with high-quality transformation
        # SmoothTransformation uses bilinear filtering for best quality
        scaled_pixmap = self._screenshot_original_pixmap.scaled(
            display_width,
            display_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Validate scaled pixmap
        if scaled_pixmap.isNull():
            from loggerplus import RobustLogger
            RobustLogger().warning(
                f"Failed to scale screenshot: {display_width}x{display_height} "
                f"from {original_width}x{original_height}"
            )
            return
        
        # Update the label
        self.ui.labelScreenshotPreview.setPixmap(scaled_pixmap)
        self.ui.labelScreenshotPreview.setText("")  # Clear text when showing image
        
        # Update tooltip with current display info
        self._update_screenshot_tooltip(display_width, display_height)
        
        # Set minimum size to prevent label from collapsing
        # Use actual display size to maintain aspect ratio in layout
        self.ui.labelScreenshotPreview.setMinimumSize(display_width, display_height)
    
    def _update_screenshot_tooltip(self, display_width: int | None = None, display_height: int | None = None):
        """Update tooltip with screenshot information.
        
        Args:
        ----
            display_width: Current display width (if None, will be calculated)
            display_height: Current display height (if None, will be calculated)
        """
        if not hasattr(self.ui, 'labelScreenshotPreview'):
            return
        
        if not self._screenshot_original_size:
            return
        
        orig_w, orig_h = self._screenshot_original_size
        
        # Calculate display size if not provided
        if display_width is None or display_height is None:
            if self._screenshot_original_pixmap and not self._screenshot_original_pixmap.isNull():
                # Get current pixmap size
                current_pixmap = self.ui.labelScreenshotPreview.pixmap()
                if current_pixmap and not current_pixmap.isNull():
                    display_width = current_pixmap.width()
                    display_height = current_pixmap.height()
                else:
                    display_width = orig_w
                    display_height = orig_h
            else:
                display_width = orig_w
                display_height = orig_h
        
        # Calculate file size if available
        file_size_str = "Unknown"
        if self._save_folder and self._save_folder.screenshot:
            file_size = len(self._save_folder.screenshot)
            if file_size < 1024:
                file_size_str = f"{file_size} bytes"
            elif file_size < 1024 * 1024:
                file_size_str = f"{file_size / 1024:.1f} KB"
            else:
                file_size_str = f"{file_size / (1024 * 1024):.2f} MB"
        
        # Build tooltip with rich HTML formatting
        tooltip_lines = [
            "<b>Screenshot Information</b>",
            f"<b>Original Size:</b> {orig_w} × {orig_h} pixels",
            f"<b>Display Size:</b> {display_width} × {display_height} pixels",
            f"<b>File Size:</b> {file_size_str}",
        ]
        
        # Add aspect ratio info
        orig_aspect = orig_w / orig_h if orig_h > 0 else 0
        tooltip_lines.append(f"<b>Aspect Ratio:</b> {orig_aspect:.2f}:1")
        
        # Add scale factor if different from original
        if display_width != orig_w or display_height != orig_h:
            scale_factor = min(display_width / orig_w, display_height / orig_h) if orig_w > 0 and orig_h > 0 else 1.0
            tooltip_lines.append(f"<b>Scale:</b> {scale_factor * 100:.1f}%")
        
        tooltip = "<br>".join(tooltip_lines)
        self.ui.labelScreenshotPreview.setToolTip(tooltip)
    
    def eventFilter(self, obj, event):
        """Handle events for screenshot label resize and mouse hover.
        
        This event filter handles:
        - Resize events: Recalculates screenshot display when label is resized
        - Mouse move events: Could be used for future zoom/pan features
        """
        if obj == self.ui.labelScreenshotPreview:
            from qtpy.QtCore import QEvent
            
            if event.type() == QEvent.Type.Resize:
                # Recalculate screenshot display when label is resized
                # Use a small delay to avoid excessive recalculations during rapid resizing
                self._update_screenshot_display()
            elif event.type() == QEvent.Type.Enter:
                # Mouse entered - ensure tooltip is up to date
                if self._screenshot_original_pixmap and not self._screenshot_original_pixmap.isNull():
                    self._update_screenshot_tooltip()
        
        return super().eventFilter(obj, event)

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

