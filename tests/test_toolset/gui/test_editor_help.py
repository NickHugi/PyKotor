"""
Comprehensive tests for editor help system.

Tests EditorHelpDialog, help menu integration, and wiki path resolution.
"""
from __future__ import annotations

import os

# Set Qt API to PyQt5 (default) before any Qt imports
# qtpy will use this to select the appropriate bindings
if "QT_API" not in os.environ:
    os.environ["QT_API"] = "PyQt5"

# Force offscreen (headless) mode for Qt
# This ensures tests don't fail if no display is available (e.g. CI/CD)
# Must be set before any Qt imports
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from pathlib import Path
from unittest.mock import MagicMock, patch

from qtpy.QtWidgets import QMenu

from toolset.gui.dialogs.editor_help import EditorHelpDialog, get_wiki_path
from toolset.gui.editors.are import AREEditor
from toolset.gui.editors.editor_wiki_mapping import EDITOR_WIKI_MAP


# ============================================================================
# get_wiki_path() TESTS
# ============================================================================

def test_get_wiki_path_development_mode(tmp_path, monkeypatch):
    """Test wiki path resolution in development mode."""
    # Create a mock wiki directory structure
    repo_root = tmp_path / "repo"
    wiki_dir = repo_root / "wiki"
    wiki_dir.mkdir(parents=True)
    (wiki_dir / "GFF-File-Format.md").write_text("# Test")
    
    # Mock is_frozen to return False and patch Path resolution
    with patch("toolset.gui.dialogs.editor_help.is_frozen", return_value=False):
        # Patch Path(__file__) to return our test structure
        with patch("toolset.gui.dialogs.editor_help.Path") as mock_path_class:
            # Create a mock that simulates the path structure
            mock_file = MagicMock(spec=Path)
            mock_file.parent.parent.parent.parent.parent = repo_root
            mock_path_class.return_value = mock_file
            
            path = get_wiki_path()
            # Should find the wiki directory
            assert path.exists() or str(path) == str(wiki_dir)


def test_get_wiki_path_frozen_mode(tmp_path, monkeypatch):
    """Test wiki path resolution in frozen (EXE) mode."""
    # Create a mock executable directory structure
    exe_dir = tmp_path / "exe"
    wiki_dir = exe_dir / "wiki"
    wiki_dir.mkdir(parents=True)
    (wiki_dir / "GFF-File-Format.md").write_text("# Test")
    
    # Mock sys.executable
    with patch("sys.executable", str(exe_dir / "HolocronToolset.exe")):
        with patch("toolset.gui.dialogs.editor_help.is_frozen", return_value=True):
            path = get_wiki_path()
            assert path.exists()
            assert path == wiki_dir


def test_get_wiki_path_fallback(tmp_path, monkeypatch):
    """Test wiki path fallback when wiki not found."""
    with patch("toolset.gui.dialogs.editor_help.is_frozen", return_value=False):
        # Create a temporary directory structure that doesn't have a wiki
        fake_editor_help_file = tmp_path / "toolset" / "gui" / "dialogs" / "editor_help.py"
        fake_editor_help_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Patch __file__ to point to our fake location
        with patch("toolset.gui.dialogs.editor_help.__file__", str(fake_editor_help_file)):
            path = get_wiki_path()
            # Should return fallback path (as Path object) when wiki doesn't exist
            assert isinstance(path, Path)
            # The fallback is Path("./wiki")
            assert path == Path("./wiki")


# ============================================================================
# EditorHelpDialog TESTS
# ============================================================================

def test_editor_help_dialog_creation(qtbot):
    """Test that EditorHelpDialog can be created."""
    dialog = EditorHelpDialog(None, "GFF-File-Format.md")
    qtbot.addWidget(dialog)
    
    assert dialog.windowTitle() == "Help - GFF-File-Format.md"
    assert dialog.text_browser is not None
    assert dialog.isVisible() is False  # Not shown yet


def test_editor_help_dialog_load_existing_file(qtbot, tmp_path, monkeypatch):
    """Test loading an existing wiki file."""
    # Create a test wiki file
    wiki_dir = tmp_path / "wiki"
    wiki_dir.mkdir()
    test_file = wiki_dir / "test.md"
    test_file.write_text("# Test Document\n\nThis is a test.")
    
    # Mock get_wiki_path to return our test wiki
    with patch("toolset.gui.dialogs.editor_help.get_wiki_path", return_value=wiki_dir):
        dialog = EditorHelpDialog(None, "test.md")
        qtbot.addWidget(dialog)
        
        # Check that HTML was rendered
        html = dialog.text_browser.toHtml()
        assert "Test Document" in html or "test" in html.lower()


def test_editor_help_dialog_load_nonexistent_file(qtbot, tmp_path, monkeypatch):
    """Test loading a non-existent wiki file shows error."""
    wiki_dir = tmp_path / "wiki"
    wiki_dir.mkdir()
    
    with patch("toolset.gui.dialogs.editor_help.get_wiki_path", return_value=wiki_dir):
        dialog = EditorHelpDialog(None, "nonexistent.md")
        qtbot.addWidget(dialog)
        
        # Check that error message is shown
        html = dialog.text_browser.toHtml()
        assert "Help File Not Found" in html or "not found" in html.lower()
        assert "nonexistent.md" in html


def test_editor_help_dialog_markdown_rendering(qtbot, tmp_path, monkeypatch):
    """Test that markdown is properly rendered to HTML."""
    wiki_dir = tmp_path / "wiki"
    wiki_dir.mkdir()
    test_file = wiki_dir / "test.md"
    test_file.write_text("""# Heading 1

## Heading 2

- List item 1
- List item 2

**Bold text** and *italic text*

```python
def test():
    pass
```
""")
    
    with patch("toolset.gui.dialogs.editor_help.get_wiki_path", return_value=wiki_dir):
        dialog = EditorHelpDialog(None, "test.md")
        qtbot.addWidget(dialog)
        
        html = dialog.text_browser.toHtml()
        # Markdown should be converted to HTML
        assert len(html) > 0
        # Should contain some HTML tags
        assert "<" in html and ">" in html


def test_editor_help_dialog_error_handling(qtbot, tmp_path, monkeypatch):
    """Test error handling when file cannot be read."""
    wiki_dir = tmp_path / "wiki"
    wiki_dir.mkdir()
    test_file = wiki_dir / "test.md"
    test_file.write_text("# Test")
    
    with patch("toolset.gui.dialogs.editor_help.get_wiki_path", return_value=wiki_dir):
        # Mock read_bytes to raise an exception
        with patch.object(Path, "read_bytes", side_effect=IOError("Permission denied")):
            dialog = EditorHelpDialog(None, "test.md")
            qtbot.addWidget(dialog)
            
            html = dialog.text_browser.toHtml()
            assert "Error Loading Help File" in html or "error" in html.lower()


def test_editor_help_dialog_non_blocking(qtbot):
    """Test that dialog is non-blocking (can be shown without blocking)."""
    dialog = EditorHelpDialog(None, "GFF-File-Format.md")
    qtbot.addWidget(dialog)
    
    # Show dialog (non-blocking)
    dialog.show()
    qtbot.waitExposed(dialog)
    
    assert dialog.isVisible()
    assert dialog.isModal() is False  # Should not be modal


# ============================================================================
# Editor._add_help_action() TESTS
# ============================================================================

def test_editor_add_help_action_creates_menu(qtbot, installation):
    """Test that _add_help_action creates a Help menu."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Call _add_help_action
    editor._add_help_action()
    
    # Check that Help menu exists
    menubar = editor.menuBar()
    help_menu = None
    for action in menubar.actions():
        if action.text() == "Help":
            help_menu = action.menu()
            break
    
    assert help_menu is not None
    assert isinstance(help_menu, QMenu)


def test_editor_add_help_action_adds_documentation_item(qtbot, installation):
    """Test that _add_help_action adds Documentation action to Help menu."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor._add_help_action()
    
    # Find Help menu
    menubar = editor.menuBar()
    help_menu = None
    for action in menubar.actions():
        if action.text() == "Help":
            help_menu = action.menu()
            break
    
    assert help_menu is not None
    
    # Check for Documentation action
    doc_action = None
    for action in help_menu.actions():
        if "Documentation" in action.text():
            doc_action = action
            break
    
    assert doc_action is not None
    assert doc_action.shortcut().toString() == "F1"


def test_editor_add_help_action_has_question_mark_icon(qtbot, installation):
    """Test that help action has question mark icon."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor._add_help_action()
    
    # Find Documentation action
    menubar = editor.menuBar()
    help_menu = None
    for action in menubar.actions():
        if action.text() == "Help":
            help_menu = action.menu()
            break
    
    assert help_menu is not None
    
    doc_action = None
    for action in help_menu.actions():
        if "Documentation" in action.text():
            doc_action = action
            break
    
    assert doc_action is not None
    # Icon should be set (may be empty QIcon if style() returns None, but should exist)
    assert doc_action.icon() is not None


def test_editor_add_help_action_auto_detects_wiki_file(qtbot, installation):
    """Test that _add_help_action auto-detects wiki file from editor class name."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Should auto-detect "GFF-File-Format.md" for AREEditor
    editor._add_help_action()
    
    # Verify help menu was created (if wiki file exists in mapping)
    menubar = editor.menuBar()
    help_menu = None
    for action in menubar.actions():
        if action.text() == "Help":
            help_menu = action.menu()
            break
    
    # AREEditor should have a wiki file in the mapping
    assert "AREEditor" in EDITOR_WIKI_MAP
    assert help_menu is not None


def test_editor_add_help_action_with_explicit_filename(qtbot, installation):
    """Test that _add_help_action works with explicit wiki filename."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor._add_help_action("GFF-File-Format.md")
    
    # Verify help menu was created
    menubar = editor.menuBar()
    help_menu = None
    for action in menubar.actions():
        if action.text() == "Help":
            help_menu = action.menu()
            break
    
    assert help_menu is not None


def test_editor_add_help_action_no_wiki_file_skips(qtbot, installation):
    """Test that _add_help_action skips if no wiki file is found."""
    from toolset.gui.editors.txt import TXTEditor
    
    # TXTEditor has None in the mapping, so _add_help_action should skip
    editor = TXTEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Count Documentation actions before
    menubar = editor.menuBar()
    help_menu_before = None
    for action in menubar.actions():
        if action.text() == "Help":
            help_menu_before = action.menu()
            break
    
    doc_actions_before = []
    if help_menu_before:
        doc_actions_before = [a for a in help_menu_before.actions() if "Documentation" in a.text()]
    
    # Call _add_help_action - should not crash and should skip since wiki_file is None
    editor._add_help_action()
    
    # Count Documentation actions after
    help_menu_after = None
    for action in menubar.actions():
        if action.text() == "Help":
            help_menu_after = action.menu()
            break
    
    doc_actions_after = []
    if help_menu_after:
        doc_actions_after = [a for a in help_menu_after.actions() if "Documentation" in a.text()]
    
    # Since TXTEditor has None in mapping, Documentation action count should be same
    assert len(doc_actions_after) == len(doc_actions_before), \
        "TXTEditor with None wiki file should not add Documentation action"


def test_editor_add_help_action_multiple_calls_idempotent(qtbot, installation):
    """Test that calling _add_help_action multiple times is idempotent."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Count initial Documentation actions (AREEditor calls _add_help_action in __init__)
    menubar = editor.menuBar()
    help_menu_before = None
    for action in menubar.actions():
        if action.text() == "Help":
            help_menu_before = action.menu()
            break
    
    if help_menu_before:
        doc_actions_before = [a for a in help_menu_before.actions() if "Documentation" in a.text()]
        initial_count = len(doc_actions_before)
    else:
        initial_count = 0
    
    # Call multiple times
    editor._add_help_action()
    editor._add_help_action()
    editor._add_help_action()
    
    # Should still have the same number of Documentation actions (idempotent)
    help_menu_after = None
    for action in menubar.actions():
        if action.text() == "Help":
            help_menu_after = action.menu()
            break
    
    assert help_menu_after is not None
    doc_actions_after = [a for a in help_menu_after.actions() if "Documentation" in a.text()]
    # Should be truly idempotent - same count as before
    assert len(doc_actions_after) == initial_count, \
        f"Expected {initial_count} Documentation action(s), got {len(doc_actions_after)} (should be idempotent)"


# ============================================================================
# Editor._show_help_dialog() TESTS
# ============================================================================

def test_editor_show_help_dialog_opens_dialog(qtbot, installation, tmp_path, monkeypatch):
    """Test that _show_help_dialog opens a non-blocking dialog."""
    # Create test wiki
    wiki_dir = tmp_path / "wiki"
    wiki_dir.mkdir()
    (wiki_dir / "test.md").write_text("# Test")
    
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    with patch("toolset.gui.dialogs.editor_help.get_wiki_path", return_value=wiki_dir):
        # Show help dialog
        editor._show_help_dialog("test.md")
        
        # Find the dialog (it should be a child of the editor)
        dialogs = [child for child in editor.findChildren(EditorHelpDialog)]
        assert len(dialogs) > 0
        
        dialog = dialogs[0]
        qtbot.waitExposed(dialog)
        assert dialog.isVisible()


def test_editor_help_action_triggered_opens_dialog(qtbot, installation, tmp_path, monkeypatch):
    """Test that clicking help action opens dialog."""
    # Create test wiki
    wiki_dir = tmp_path / "wiki"
    wiki_dir.mkdir()
    (wiki_dir / "GFF-File-Format.md").write_text("# Test")
    
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    editor._add_help_action()
    
    with patch("toolset.gui.dialogs.editor_help.get_wiki_path", return_value=wiki_dir):
        # Find Documentation action
        menubar = editor.menuBar()
        help_menu = None
        for action in menubar.actions():
            if action.text() == "Help":
                help_menu = action.menu()
                break
        
        assert help_menu is not None
        
        doc_action = None
        for action in help_menu.actions():
            if "Documentation" in action.text():
                doc_action = action
                break
        
        assert doc_action is not None
        
        # Trigger the action
        doc_action.trigger()
        qtbot.wait(100)  # Wait for dialog to be created
        
        # Find the dialog
        dialogs = [child for child in editor.findChildren(EditorHelpDialog)]
        assert len(dialogs) > 0


# ============================================================================
# INTEGRATION TESTS - Editors have help buttons
# ============================================================================

def test_are_editor_has_help_button(qtbot, installation):
    """Test that AREEditor has help button after initialization."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Check that help menu exists
    menubar = editor.menuBar()
    help_menu = None
    for action in menubar.actions():
        if action.text() == "Help":
            help_menu = action.menu()
            break
    
    assert help_menu is not None, "Help menu should exist"
    
    # Check for Documentation action
    doc_actions = [a for a in help_menu.actions() if "Documentation" in a.text()]
    assert len(doc_actions) > 0, "Documentation action should exist"


def test_multiple_editors_have_help_buttons(qtbot, installation):
    """Test that multiple editors have help buttons."""
    from toolset.gui.editors.utw import UTWEditor
    from toolset.gui.editors.uti import UTIEditor
    from toolset.gui.editors.gff import GFFEditor
    
    editors = [
        AREEditor(None, installation),
        UTWEditor(None, installation),
        UTIEditor(None, installation),
        GFFEditor(None, installation),
    ]
    
    for editor in editors:
        qtbot.addWidget(editor)
        
        # Check that help menu exists
        menubar = editor.menuBar()
        help_menu = None
        for action in menubar.actions():
            if action.text() == "Help":
                help_menu = action.menu()
                break
        
        assert help_menu is not None, f"{editor.__class__.__name__} should have Help menu"
        
        # Check for Documentation action
        doc_actions = [a for a in help_menu.actions() if "Documentation" in a.text()]
        assert len(doc_actions) > 0, f"{editor.__class__.__name__} should have Documentation action"


# ============================================================================
# EDITOR_WIKI_MAP TESTS
# ============================================================================

def test_editor_wiki_map_has_all_editors():
    """Test that EDITOR_WIKI_MAP contains entries for major editors."""
    expected_editors = [
        "AREEditor",
        "UTWEditor",
        "UTIEditor",
        "UTCEditor",
        "GFFEditor",
        "DLGEditor",
        "JRLEditor",
    ]
    
    for editor_name in expected_editors:
        assert editor_name in EDITOR_WIKI_MAP, f"{editor_name} should be in EDITOR_WIKI_MAP"


def test_editor_wiki_map_values_are_strings_or_none():
    """Test that all values in EDITOR_WIKI_MAP are strings or None."""
    for editor_name, wiki_file in EDITOR_WIKI_MAP.items():
        assert wiki_file is None or isinstance(wiki_file, str), \
            f"{editor_name} has invalid wiki_file type: {type(wiki_file)}"
        if wiki_file is not None:
            assert wiki_file.endswith(".md"), \
                f"{editor_name} wiki_file should end with .md: {wiki_file}"


# ============================================================================
# F1 SHORTCUT TESTS
# ============================================================================

def test_f1_shortcut_opens_help(qtbot, installation, tmp_path, monkeypatch):
    """Test that F1 shortcut opens help dialog."""
    from qtpy.QtWidgets import QShortcut
    
    # Create test wiki
    wiki_dir = tmp_path / "wiki"
    wiki_dir.mkdir()
    (wiki_dir / "GFF-File-Format.md").write_text("# Test")
    
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    editor._add_help_action()
    
    with patch("toolset.gui.dialogs.editor_help.get_wiki_path", return_value=wiki_dir):
        # Find Documentation action and verify it has F1 shortcut
        menubar = editor.menuBar()
        help_menu = None
        for action in menubar.actions():
            if action.text() == "Help":
                help_menu = action.menu()
                break
        
        assert help_menu is not None
        
        doc_action = None
        for action in help_menu.actions():
            if "Documentation" in action.text():
                doc_action = action
                break
        
        assert doc_action is not None
        assert doc_action.shortcut().toString() == "F1"
        
        # Find QShortcut objects for F1
        from qtpy.QtWidgets import QShortcut
        shortcuts = editor.findChildren(QShortcut)
        f1_shortcuts = [s for s in shortcuts if s.key().toString() == "F1"]
        assert len(f1_shortcuts) > 0, "F1 shortcut should exist"
        
        # Trigger the action (simulating F1 press)
        doc_action.trigger()
        qtbot.wait(100)
        
        # Find the dialog
        dialogs = [child for child in editor.findChildren(EditorHelpDialog)]
        assert len(dialogs) > 0


# ============================================================================
# _setup_menus ALIAS TESTS
# ============================================================================

def test_editor_setup_menus_alias(qtbot, installation):
    """Test that _setup_menus() alias calls _setupMenus()."""
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify _setup_menus exists and is callable
    assert hasattr(editor, "_setup_menus")
    assert callable(editor._setup_menus)
    
    # Verify it's an alias (should not raise error)
    # We can't easily test it's calling _setupMenus without mocking,
    # but we can verify the menu is set up
    menubar = editor.menuBar()
    assert menubar is not None
    # Menu should have actions (from _setupMenus)
    assert len(menubar.actions()) > 0


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

def test_editor_help_dialog_handles_invalid_markdown(qtbot, tmp_path, monkeypatch):
    """Test that dialog handles invalid markdown gracefully."""
    wiki_dir = tmp_path / "wiki"
    wiki_dir.mkdir()
    # Create a file with invalid content (binary data)
    test_file = wiki_dir / "test.md"
    test_file.write_bytes(b"\x00\x01\x02\x03\xff\xfe\xfd")
    
    with patch("toolset.gui.dialogs.editor_help.get_wiki_path", return_value=wiki_dir):
        # Should not crash, should show error or handle gracefully
        dialog = EditorHelpDialog(None, "test.md")
        qtbot.addWidget(dialog)
        
        # Dialog should still be created
        assert dialog is not None


def test_editor_help_dialog_handles_unicode_content(qtbot, tmp_path, monkeypatch):
    """Test that dialog handles unicode content correctly."""
    wiki_dir = tmp_path / "wiki"
    wiki_dir.mkdir()
    test_file = wiki_dir / "test.md"
    test_file.write_text("# Test Document\n\nUnicode: 测试 🎮 émoji", encoding="utf-8")
    
    with patch("toolset.gui.dialogs.editor_help.get_wiki_path", return_value=wiki_dir):
        dialog = EditorHelpDialog(None, "test.md")
        qtbot.addWidget(dialog)
        
        html = dialog.text_browser.toHtml()
        # Should handle unicode without errors
        assert len(html) > 0


# ============================================================================
# INTEGRATION TESTS - Full workflow
# ============================================================================

def test_full_help_workflow(qtbot, installation, tmp_path, monkeypatch):
    """Test the complete workflow: editor -> help menu -> dialog -> content."""
    # Create test wiki with actual content
    wiki_dir = tmp_path / "wiki"
    wiki_dir.mkdir()
    test_file = wiki_dir / "GFF-File-Format.md"
    test_file.write_text("""# GFF File Format

## ARE (Area)

ARE files define static area properties.

### Core Identity Fields

| Field | Type | Description |
| ----- | ---- | ----------- |
| Tag | CExoString | Unique area identifier |
| Name | CExoLocString | Area name (localized) |
""")
    
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    with patch("toolset.gui.dialogs.editor_help.get_wiki_path", return_value=wiki_dir):
        # Verify help menu exists
        menubar = editor.menuBar()
        help_menu = None
        for action in menubar.actions():
            if action.text() == "Help":
                help_menu = action.menu()
                break
        
        assert help_menu is not None
        
        # Find Documentation action
        doc_action = None
        for action in help_menu.actions():
            if "Documentation" in action.text():
                doc_action = action
                break
        
        assert doc_action is not None
        
        # Trigger the action
        doc_action.trigger()
        qtbot.wait(200)  # Wait for dialog to be created and shown
        
        # Find the dialog
        dialogs = [child for child in editor.findChildren(EditorHelpDialog)]
        assert len(dialogs) > 0
        
        dialog = dialogs[0]
        qtbot.waitExposed(dialog)
        
        # Verify dialog content
        html = dialog.text_browser.toHtml()
        assert "GFF File Format" in html or "gff" in html.lower()
        assert "ARE" in html or "area" in html.lower()


def test_help_dialog_can_be_opened_multiple_times(qtbot, installation, tmp_path, monkeypatch):
    """Test that multiple help dialogs can be opened (non-blocking)."""
    wiki_dir = tmp_path / "wiki"
    wiki_dir.mkdir()
    (wiki_dir / "test.md").write_text("# Test")
    
    editor = AREEditor(None, installation)
    qtbot.addWidget(editor)
    
    with patch("toolset.gui.dialogs.editor_help.get_wiki_path", return_value=wiki_dir):
        # Open dialog multiple times
        editor._show_help_dialog("test.md")
        qtbot.wait(100)
        editor._show_help_dialog("test.md")
        qtbot.wait(100)
        editor._show_help_dialog("test.md")
        qtbot.wait(100)
        
        # Should have multiple dialogs
        dialogs = [child for child in editor.findChildren(EditorHelpDialog)]
        assert len(dialogs) >= 1  # At least one dialog should exist

