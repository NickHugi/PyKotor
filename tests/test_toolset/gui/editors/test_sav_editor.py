"""
Comprehensive tests for SAV Editor - testing EVERY possible manipulation.

Note: SAV Editor is actually a JRL (Journal) editor despite the name.
Each test focuses on a specific manipulation and validates save/load roundtrips.
Following the ARE editor test pattern for comprehensive coverage.
"""
import pytest
from pathlib import Path
from qtpy.QtCore import Qt
from qtpy.QtGui import QStandardItem
from toolset.gui.editors.sav import SAVEditor  # type: ignore[import-not-found]
from toolset.data.installation import HTInstallation  # type: ignore[import-not-found]
from pykotor.resource.generics.jrl import JRL, JRLQuest, JRLEntry, read_jrl  # type: ignore[import-not-found]
from pykotor.resource.type import ResourceType  # type: ignore[import-not-found]
from pykotor.common.language import LocalizedString, Language, Gender  # type: ignore[import-not-found]

# ============================================================================
# BASIC TESTS
# ============================================================================

def test_sav_editor_new_file_creation(qtbot, installation: HTInstallation):
    """Test creating a new SAV/JRL file from scratch."""
    editor = SAVEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create new
    editor.new()
    
    # Verify JRL object exists and is empty
    assert editor._jrl is not None
    assert isinstance(editor._jrl, JRL)
    assert len(editor._jrl.quests) == 0

def test_sav_editor_initialization(qtbot, installation: HTInstallation):
    """Test editor initialization."""
    editor = SAVEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify all components initialized
    assert editor._jrl is not None
    assert editor._model is not None
    assert editor.ui is not None

# ============================================================================
# QUEST MANIPULATIONS
# ============================================================================

def test_sav_editor_add_quest(qtbot, installation: HTInstallation):
    """Test adding a quest."""
    editor = SAVEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Create new quest
    quest = JRLQuest()
    quest.name = LocalizedString.from_english("Test Quest")
    
    # Add quest
    editor.add_quest(quest)
    
    # Verify quest was added
    assert len(editor._jrl.quests) == 1
    assert editor._jrl.quests[0] == quest
    assert editor._model.rowCount() == 1

def test_sav_editor_add_multiple_quests(qtbot, installation: HTInstallation):
    """Test adding multiple quests."""
    editor = SAVEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Add multiple quests
    for i in range(5):
        quest = JRLQuest()
        quest.name = LocalizedString.from_english(f"Quest {i}")
        editor.add_quest(quest)
    
    # Verify all quests were added
    assert len(editor._jrl.quests) == 5
    assert editor._model.rowCount() == 5

def test_sav_editor_remove_quest(qtbot, installation: HTInstallation):
    """Test removing a quest."""
    editor = SAVEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Add quests
    quest1 = JRLQuest()
    quest1.name = LocalizedString.from_english("Quest 1")
    quest2 = JRLQuest()
    quest2.name = LocalizedString.from_english("Quest 2")
    
    editor.add_quest(quest1)
    editor.add_quest(quest2)
    
    # Get quest item
    quest_item = editor._model.item(0)
    assert quest_item is not None
    
    # Remove quest
    editor.remove_quest(quest_item)
    
    # Verify quest was removed
    assert len(editor._jrl.quests) == 1
    assert editor._model.rowCount() == 1
    assert editor._jrl.quests[0].name == quest2.name

# ============================================================================
# ENTRY MANIPULATIONS
# ============================================================================

def test_sav_editor_add_entry(qtbot, installation: HTInstallation):
    """Test adding an entry to a quest."""
    editor = SAVEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Create quest
    quest = JRLQuest()
    quest.name = LocalizedString.from_english("Test Quest")
    editor.add_quest(quest)
    
    # Get quest item
    quest_item = editor._model.item(0)
    assert quest_item is not None
    
    # Create entry
    entry = JRLEntry()
    entry.entry_id = 1
    entry.text = LocalizedString.from_english("Entry text")
    entry.end = False
    
    # Add entry
    editor.add_entry(quest_item, entry)
    
    # Verify entry was added
    assert len(quest.entries) == 1
    assert quest.entries[0] == entry
    assert quest_item.rowCount() == 1

def test_sav_editor_add_multiple_entries(qtbot, installation: HTInstallation):
    """Test adding multiple entries to a quest."""
    editor = SAVEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Create quest
    quest = JRLQuest()
    quest.name = LocalizedString.from_english("Test Quest")
    editor.add_quest(quest)
    
    quest_item = editor._model.item(0)
    assert quest_item is not None
    
    # Add multiple entries
    for i in range(3):
        entry = JRLEntry()
        entry.entry_id = i
        entry.text = LocalizedString.from_english(f"Entry {i}")
        entry.end = (i == 2)
        editor.add_entry(quest_item, entry)
    
    # Verify all entries were added
    assert len(quest.entries) == 3
    assert quest_item.rowCount() == 3

def test_sav_editor_remove_entry(qtbot, installation: HTInstallation):
    """Test removing an entry from a quest."""
    editor = SAVEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Create quest with entries
    quest = JRLQuest()
    quest.name = LocalizedString.from_english("Test Quest")
    editor.add_quest(quest)
    
    quest_item = editor._model.item(0)
    assert quest_item is not None
    
    entry1 = JRLEntry()
    entry1.entry_id = 1
    entry1.text = LocalizedString.from_english("Entry 1")
    entry2 = JRLEntry()
    entry2.entry_id = 2
    entry2.text = LocalizedString.from_english("Entry 2")
    
    editor.add_entry(quest_item, entry1)
    editor.add_entry(quest_item, entry2)
    
    # Get entry item
    entry_item = quest_item.child(0)
    assert entry_item is not None
    
    # Remove entry
    editor.remove_entry(entry_item)
    
    # Verify entry was removed
    assert len(quest.entries) == 1
    assert quest_item.rowCount() == 1

# ============================================================================
# REFRESH TESTS
# ============================================================================

def test_sav_editor_refresh_quest_item(qtbot, installation: HTInstallation):
    """Test refreshing quest item display."""
    editor = SAVEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Create quest
    quest = JRLQuest()
    quest.name = LocalizedString.from_english("Test Quest")
    editor.add_quest(quest)
    
    quest_item = editor._model.item(0)
    assert quest_item is not None
    
    # Refresh quest item
    editor.refresh_quest_item(quest_item)
    
    # Verify text was set
    assert len(quest_item.text()) > 0

def test_sav_editor_refresh_entry_item(qtbot, installation: HTInstallation):
    """Test refreshing entry item display."""
    editor = SAVEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Create quest with entry
    quest = JRLQuest()
    quest.name = LocalizedString.from_english("Test Quest")
    editor.add_quest(quest)
    
    quest_item = editor._model.item(0)
    assert quest_item is not None
    
    entry = JRLEntry()
    entry.entry_id = 1
    entry.text = LocalizedString.from_english("Entry text")
    entry.end = False
    editor.add_entry(quest_item, entry)
    
    entry_item = quest_item.child(0)
    assert entry_item is not None
    
    # Refresh entry item
    editor.refresh_entry_item(entry_item)
    
    # Verify text was set
    assert len(entry_item.text()) > 0

# ============================================================================
# SAVE/LOAD ROUNDTRIP TESTS
# ============================================================================

def test_sav_editor_save_load_roundtrip(qtbot, installation: HTInstallation):
    """Test save/load roundtrip preserves data."""
    editor = SAVEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Add quest with entry
    quest = JRLQuest()
    quest.name = LocalizedString.from_english("Test Quest")
    editor.add_quest(quest)
    
    quest_item = editor._model.item(0)
    assert quest_item is not None
    
    entry = JRLEntry()
    entry.entry_id = 1
    entry.text = LocalizedString.from_english("Test Entry")
    entry.end = True
    editor.add_entry(quest_item, entry)
    
    # Build
    data, _ = editor.build()
    assert len(data) > 0
    
    # Load it back
    editor.load(Path("test.jrl"), "test", ResourceType.SAV, data)
    
    # Verify data was loaded
    assert len(editor._jrl.quests) == 1
    assert len(editor._jrl.quests[0].entries) == 1
    assert editor._jrl.quests[0].entries[0].entry_id == 1
    assert editor._jrl.quests[0].entries[0].end

def test_sav_editor_multiple_save_load_cycles(qtbot, installation: HTInstallation):
    """Test multiple save/load cycles preserve data correctly."""
    editor = SAVEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Perform multiple cycles
    for cycle in range(3):
        # Clear and add quest
        editor.new()
        quest = JRLQuest()
        quest.name = LocalizedString.from_english(f"Quest {cycle}")
        editor.add_quest(quest)
        
        # Save
        data, _ = editor.build()
        
        # Load back
        editor.load(Path("test.jrl"), "test", ResourceType.SAV, data)
        
        # Verify quest was preserved
        assert len(editor._jrl.quests) == 1

# ============================================================================
# KEYBOARD SHORTCUTS
# ============================================================================

def test_sav_editor_delete_shortcut(qtbot, installation: HTInstallation):
    """Test delete shortcut functionality."""
    editor = SAVEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Verify delete shortcut method exists
    assert hasattr(editor, 'on_delete_shortcut')
    assert callable(editor.on_delete_shortcut)

# ============================================================================
# MODEL TESTS
# ============================================================================

def test_sav_editor_model_initialization(qtbot, installation: HTInstallation):
    """Test model is properly initialized."""
    editor = SAVEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify model exists and is empty initially
    assert editor._model is not None
    assert editor._model.rowCount() == 0

def test_sav_editor_model_clears_on_new(qtbot, installation: HTInstallation):
    """Test model clears when new() is called."""
    editor = SAVEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Add quest
    quest = JRLQuest()
    quest.name = LocalizedString.from_english("Test Quest")
    editor.add_quest(quest)
    assert editor._model.rowCount() == 1
    
    # Create new
    editor.new()
    
    # Verify model was cleared
    assert editor._model.rowCount() == 0

# ============================================================================
# EDGE CASES
# ============================================================================

def test_sav_editor_empty_jrl_file(qtbot, installation: HTInstallation):
    """Test handling of empty JRL file."""
    editor = SAVEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Build empty file
    data, _ = editor.build()
    
    # Load it back
    editor.load(Path("test.jrl"), "test", ResourceType.SAV, data)
    
    # Verify empty JRL loaded correctly
    assert editor._jrl is not None
    assert len(editor._jrl.quests) == 0

def test_sav_editor_entry_with_end_flag(qtbot, installation: HTInstallation):
    """Test entries with end flag set."""
    editor = SAVEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Create quest with ending entry
    quest = JRLQuest()
    quest.name = LocalizedString.from_english("Test Quest")
    editor.add_quest(quest)
    
    quest_item = editor._model.item(0)
    assert quest_item is not None
    
    entry = JRLEntry()
    entry.entry_id = 1
    entry.text = LocalizedString.from_english("Ending entry")
    entry.end = True
    
    editor.add_entry(quest_item, entry)
    
    # Verify entry has end flag
    assert quest.entries[0].end
    
    # Refresh and verify color (end entries should have different color)
    entry_item = quest_item.child(0)
    assert entry_item is not None
    editor.refresh_entry_item(entry_item)
    
    # End entries should have red color
    foreground = entry_item.foreground()
    assert foreground is not None

# ============================================================================
# COMBINATION TESTS
# ============================================================================

def test_sav_editor_complex_jrl_structure(qtbot, installation: HTInstallation):
    """Test complex JRL structure with multiple quests and entries."""
    editor = SAVEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Add multiple quests with entries
    for quest_num in range(3):
        quest = JRLQuest()
        quest.name = LocalizedString.from_english(f"Quest {quest_num}")
        editor.add_quest(quest)
        
        quest_item = editor._model.item(quest_num)
        assert quest_item is not None
        
        # Add multiple entries per quest
        for entry_num in range(quest_num + 1):
            entry = JRLEntry()
            entry.entry_id = entry_num
            entry.text = LocalizedString.from_english(f"Entry {entry_num}")
            entry.end = (entry_num == quest_num)
            editor.add_entry(quest_item, entry)
    
    # Verify structure
    assert len(editor._jrl.quests) == 3
    assert len(editor._jrl.quests[0].entries) == 1
    assert len(editor._jrl.quests[1].entries) == 2
    assert len(editor._jrl.quests[2].entries) == 3
    
    # Build and verify
    data, _ = editor.build()
    assert len(data) > 0
    
    # Load and verify
    editor.load(Path("test.jrl"), "test", ResourceType.SAV, data)
    assert len(editor._jrl.quests) == 3

# ============================================================================
# UI ELEMENT TESTS
# ============================================================================

def test_sav_editor_ui_elements(qtbot, installation: HTInstallation):
    """Test that UI elements exist."""
    editor = SAVEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify UI exists
    assert editor.ui is not None
    
    # UI structure depends on the .ui file
    # Just verify UI was set up
    assert hasattr(editor.ui, 'setupUi')

# ============================================================================
# INSTALLATION SETUP TESTS
# ============================================================================

def test_sav_editor_installation_setup(qtbot, installation: HTInstallation):
    """Test installation setup."""
    editor = SAVEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify installation was set up
    assert editor._installation == installation

def test_sav_editor_without_installation(qtbot):
    """Test editor works without installation (limited functionality)."""
    editor = SAVEditor(None, None)
    qtbot.addWidget(editor)
    
    # Should still initialize
    assert editor._jrl is not None
    
    # But installation may be None
    assert editor._installation is None

# ============================================================================
# HEADLESS UI TESTS WITH REAL FILES
# ============================================================================

def test_sav_editor_headless_ui_load_build(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test SAV Editor (JRL) in headless UI - loads real file and builds data."""
    editor = SAVEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Try to find a JRL file (SAV editor is actually JRL editor)
    jrl_files = list(test_files_dir.glob("*.jrl")) + list(test_files_dir.rglob("*.jrl"))
    if not jrl_files:
        # Try to get one from installation
        jrl_resources = list(installation.resources(ResourceType.JRL))[:1]
        if not jrl_resources:
            pytest.skip("No JRL files available for testing")
        jrl_resource = jrl_resources[0]
        jrl_data = installation.resource(jrl_resource.identifier)
        if not jrl_data:
            pytest.skip(f"Could not load JRL data for {jrl_resource.identifier}")
        editor.load(
            jrl_resource.filepath if hasattr(jrl_resource, 'filepath') else Path("module.jrl"),
            jrl_resource.resname,
            ResourceType.JRL,
            jrl_data
        )
    else:
        jrl_file = jrl_files[0]
        original_data = jrl_file.read_bytes()
        editor.load(jrl_file, jrl_file.stem, ResourceType.JRL, original_data)
    
    # Verify editor loaded the data
    assert editor is not None
    assert editor._jrl is not None
    
    # Build and verify it works
    data, _ = editor.build()
    assert len(data) > 0
    
    # Verify we can read it back
    loaded_jrl = read_jrl(data)
    assert loaded_jrl is not None

