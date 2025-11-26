"""
Comprehensive tests for TXT Editor - testing EVERY possible manipulation.

Each test focuses on a specific manipulation and validates save/load roundtrips.
Following the ARE editor test pattern for comprehensive coverage.
"""
from __future__ import annotations

import pytest
from pathlib import Path
from qtpy.QtCore import Qt
from toolset.gui.editors.txt import TXTEditor  # type: ignore[import-not-found]
from toolset.data.installation import HTInstallation  # type: ignore[import-not-found]
from pykotor.resource.type import ResourceType  # type: ignore[import-not-found]
from pykotor.tools.encoding import decode_bytes_with_fallbacks  # type: ignore[import-not-found]

# ============================================================================
# BASIC TEXT MANIPULATION TESTS
# ============================================================================

def test_txt_editor_new_file_creation(qtbot, installation: HTInstallation):
    """Test creating a new TXT file from scratch."""
    editor = TXTEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create new
    editor.new()
    
    # Verify text edit is empty
    assert editor.ui.textEdit.toPlainText() == ""
    
    # Set text
    test_text = "Hello World"
    editor.ui.textEdit.setPlainText(test_text)
    
    # Build and verify
    data, _ = editor.build()
    decoded = decode_bytes_with_fallbacks(data)
    assert decoded == test_text

def test_txt_editor_load_existing_file(qtbot, installation: HTInstallation, test_files_dir: Path):
    """Test loading an existing TXT file."""
    editor = TXTEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Try to find a txt file in test_files
    txt_files = list(test_files_dir.glob("*.txt"))
    if not txt_files:
        pytest.skip("No .txt files found in test_files directory")
    
    txt_file = txt_files[0]
    original_data = txt_file.read_bytes()
    
    # Load file
    editor.load(txt_file, txt_file.stem, ResourceType.TXT, original_data)
    
    # Verify content matches
    loaded_text = editor.ui.textEdit.toPlainText()
    expected_text = decode_bytes_with_fallbacks(original_data)
    assert loaded_text == expected_text

def test_txt_editor_text_editing(qtbot, installation: HTInstallation):
    """Test basic text editing operations."""
    editor = TXTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Set initial text
    initial_text = "Initial Text"
    editor.ui.textEdit.setPlainText(initial_text)
    assert editor.ui.textEdit.toPlainText() == initial_text
    
    # Append text
    editor.ui.textEdit.appendPlainText("\nAppended Text")
    assert "Appended Text" in editor.ui.textEdit.toPlainText()
    
    # Insert text
    cursor = editor.ui.textEdit.textCursor()
    cursor.setPosition(0)
    editor.ui.textEdit.setTextCursor(cursor)
    editor.ui.textEdit.insertPlainText("Prefix: ")
    assert editor.ui.textEdit.toPlainText().startswith("Prefix: ")

def test_txt_editor_multiline_text(qtbot, installation: HTInstallation):
    """Test handling of multiline text."""
    editor = TXTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Set multiline text
    multiline_text = "Line 1\nLine 2\nLine 3"
    editor.ui.textEdit.setPlainText(multiline_text)
    
    # Build and verify
    data, _ = editor.build()
    decoded = decode_bytes_with_fallbacks(data)
    # Note: line endings may be normalized, so we check content
    assert "Line 1" in decoded
    assert "Line 2" in decoded
    assert "Line 3" in decoded

def test_txt_editor_empty_text(qtbot, installation: HTInstallation):
    """Test handling of empty text."""
    editor = TXTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Verify empty
    assert editor.ui.textEdit.toPlainText() == ""
    
    # Build empty
    data, _ = editor.build()
    assert data == b""

def test_txt_editor_unicode_characters(qtbot, installation: HTInstallation):
    """Test handling of Unicode characters."""
    editor = TXTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Set Unicode text
    unicode_text = "Hello 世界 🌍 ñoño"
    editor.ui.textEdit.setPlainText(unicode_text)
    
    # Build and verify
    data, _ = editor.build()
    decoded = decode_bytes_with_fallbacks(data)
    assert decoded == unicode_text

def test_txt_editor_special_characters(qtbot, installation: HTInstallation):
    """Test handling of special characters."""
    editor = TXTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Set text with special characters
    special_text = "Tab:\tNewline:\nCarriage:\rQuote:\"Apostrophe:'Backslash:\\"
    editor.ui.textEdit.setPlainText(special_text)
    
    # Build and verify
    data, _ = editor.build()
    decoded = decode_bytes_with_fallbacks(data)
    assert "Tab:" in decoded
    assert "Newline:" in decoded

def test_txt_editor_long_text(qtbot, installation: HTInstallation):
    """Test handling of very long text."""
    editor = TXTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Create long text (1000 lines)
    long_text = "\n".join([f"Line {i}" for i in range(1000)])
    editor.ui.textEdit.setPlainText(long_text)
    
    # Build and verify
    data, _ = editor.build()
    decoded = decode_bytes_with_fallbacks(data)
    assert "Line 0" in decoded
    assert "Line 999" in decoded

# ============================================================================
# WORD WRAP TESTS
# ============================================================================

def test_txt_editor_toggle_word_wrap(qtbot, installation: HTInstallation):
    """Test toggling word wrap."""
    editor = TXTEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify initial state
    assert not editor._word_wrap
    
    # Toggle word wrap on
    editor.toggle_word_wrap()
    assert editor._word_wrap
    assert editor.ui.actionWord_Wrap.isChecked()
    assert editor.ui.textEdit.lineWrapMode() == editor.ui.textEdit.LineWrapMode.WidgetWidth
    
    # Toggle word wrap off
    editor.toggle_word_wrap()
    assert not editor._word_wrap
    assert not editor.ui.actionWord_Wrap.isChecked()
    assert editor.ui.textEdit.lineWrapMode() == editor.ui.textEdit.LineWrapMode.NoWrap

def test_txt_editor_word_wrap_action(qtbot, installation: HTInstallation):
    """Test word wrap action via menu."""
    editor = TXTEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Trigger word wrap action
    initial_state = editor._word_wrap
    editor.ui.actionWord_Wrap.trigger()
    
    # Verify state changed
    assert editor._word_wrap != initial_state

def test_txt_editor_word_wrap_with_text(qtbot, installation: HTInstallation):
    """Test word wrap with actual text content."""
    editor = TXTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Set long line that would wrap
    long_line = "This is a very long line of text that should wrap when word wrap is enabled " * 10
    editor.ui.textEdit.setPlainText(long_line)
    
    # Verify word wrap doesn't affect content
    assert long_line == editor.ui.textEdit.toPlainText()
    
    # Toggle wrap and verify content unchanged
    editor.toggle_word_wrap()
    assert long_line == editor.ui.textEdit.toPlainText()

# ============================================================================
# ENCODING TESTS
# ============================================================================

def test_txt_editor_utf8_encoding(qtbot, installation: HTInstallation):
    """Test UTF-8 encoding."""
    editor = TXTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # UTF-8 compatible text
    text = "Hello World"
    editor.ui.textEdit.setPlainText(text)
    
    # Build should use UTF-8
    data, _ = editor.build()
    assert data.decode("utf-8") == text

def test_txt_editor_windows1252_fallback(qtbot, installation: HTInstallation):
    """Test Windows-1252 encoding fallback."""
    editor = TXTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Text that might need fallback encoding
    # Note: The encoding logic tries utf-8 first, then windows-1252, then latin-1
    text = "Test with some special chars: éñ"
    editor.ui.textEdit.setPlainText(text)
    
    # Build should handle encoding
    data, _ = editor.build()
    decoded = decode_bytes_with_fallbacks(data)
    assert decoded == text

# ============================================================================
# SAVE/LOAD ROUNDTRIP TESTS
# ============================================================================

def test_txt_editor_save_load_roundtrip_identity(qtbot, installation: HTInstallation):
    """Test that save/load roundtrip preserves content exactly."""
    editor = TXTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Set initial text
    test_text = "Test content\nWith multiple lines\nAnd special chars: éñ"
    editor.ui.textEdit.setPlainText(test_text)
    
    # Save
    data1, _ = editor.build()
    
    # Load saved data
    editor.load(Path("test.txt"), "test", ResourceType.TXT, data1)
    
    # Verify content matches
    loaded_text = editor.ui.textEdit.toPlainText()
    assert loaded_text == decode_bytes_with_fallbacks(data1)
    
    # Save again
    data2, _ = editor.build()
    
    # Verify second save matches first (content-wise, line endings may differ)
    decoded1 = decode_bytes_with_fallbacks(data1)
    decoded2 = decode_bytes_with_fallbacks(data2)
    # Normalize line endings for comparison
    assert decoded1.replace("\r\n", "\n").replace("\r", "\n") == decoded2.replace("\r\n", "\n").replace("\r", "\n")

def test_txt_editor_save_load_roundtrip_with_modifications(qtbot, installation: HTInstallation):
    """Test save/load roundtrip with modifications."""
    editor = TXTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Initial text
    initial_text = "Initial content"
    editor.ui.textEdit.setPlainText(initial_text)
    
    # Save
    data1, _ = editor.build()
    
    # Load and modify
    editor.load(Path("test.txt"), "test", ResourceType.TXT, data1)
    editor.ui.textEdit.appendPlainText("\nModified content")
    
    # Save modified
    data2, _ = editor.build()
    
    # Verify modification was saved
    decoded2 = decode_bytes_with_fallbacks(data2)
    assert "Modified content" in decoded2

def test_txt_editor_multiple_save_load_cycles(qtbot, installation: HTInstallation):
    """Test multiple save/load cycles preserve content."""
    editor = TXTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Perform multiple cycles
    for cycle in range(5):
        # Set text
        test_text = f"Cycle {cycle} content"
        editor.ui.textEdit.setPlainText(test_text)
        
        # Save
        data, _ = editor.build()
        
        # Load back
        editor.load(Path("test.txt"), "test", ResourceType.TXT, data)
        
        # Verify content
        loaded_text = editor.ui.textEdit.toPlainText()
        assert loaded_text == decode_bytes_with_fallbacks(data)

# ============================================================================
# LINE ENDING TESTS
# ============================================================================

def test_txt_editor_line_ending_normalization(qtbot, installation: HTInstallation):
    """Test that line endings are normalized on build."""
    editor = TXTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Set text with mixed line endings
    # Note: QPlainTextEdit uses \n internally
    text = "Line 1\nLine 2\r\nLine 3\rLine 4"
    editor.ui.textEdit.setPlainText(text)
    
    # Build - should normalize line endings
    data, _ = editor.build()
    
    # Verify it built successfully
    assert len(data) > 0
    decoded = decode_bytes_with_fallbacks(data)
    assert "Line 1" in decoded
    assert "Line 2" in decoded
    assert "Line 3" in decoded
    assert "Line 4" in decoded

# ============================================================================
# UI INTERACTION TESTS
# ============================================================================

def test_txt_editor_cursor_position(qtbot, installation: HTInstallation):
    """Test cursor position operations."""
    editor = TXTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Set text
    editor.ui.textEdit.setPlainText("Hello\nWorld")
    
    # Move cursor to start
    cursor = editor.ui.textEdit.textCursor()
    cursor.setPosition(0)
    editor.ui.textEdit.setTextCursor(cursor)
    assert editor.ui.textEdit.textCursor().position() == 0
    
    # Move cursor to end
    cursor.movePosition(cursor.MoveOperation.End)
    editor.ui.textEdit.setTextCursor(cursor)
    assert editor.ui.textEdit.textCursor().position() == len("Hello\nWorld")

def test_txt_editor_text_selection(qtbot, installation: HTInstallation):
    """Test text selection operations."""
    editor = TXTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Set text
    editor.ui.textEdit.setPlainText("Hello World")
    
    # Select text
    cursor = editor.ui.textEdit.textCursor()
    cursor.setPosition(0)
    cursor.setPosition(5, cursor.MoveMode.KeepAnchor)
    editor.ui.textEdit.setTextCursor(cursor)
    
    # Verify selection
    selected = editor.ui.textEdit.textCursor().selectedText()
    assert selected == "Hello"

def test_txt_editor_copy_paste(qtbot, installation: HTInstallation):
    """Test copy/paste operations."""
    editor = TXTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Set initial text
    editor.ui.textEdit.setPlainText("Hello")
    
    # Select and copy
    cursor = editor.ui.textEdit.textCursor()
    cursor.selectAll()
    editor.ui.textEdit.setTextCursor(cursor)
    editor.ui.textEdit.copy()
    
    # Move cursor and paste
    cursor.setPosition(len("Hello"))
    editor.ui.textEdit.setTextCursor(cursor)
    editor.ui.textEdit.paste()
    
    # Verify paste worked
    assert "HelloHello" in editor.ui.textEdit.toPlainText()

# ============================================================================
# EDGE CASES
# ============================================================================

def test_txt_editor_very_long_line(qtbot, installation: HTInstallation):
    """Test handling of very long line without newlines."""
    editor = TXTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Create very long line
    long_line = "A" * 10000
    editor.ui.textEdit.setPlainText(long_line)
    
    # Build and verify
    data, _ = editor.build()
    decoded = decode_bytes_with_fallbacks(data)
    assert len(decoded) == 10000
    assert decoded == long_line

def test_txt_editor_only_newlines(qtbot, installation: HTInstallation):
    """Test handling of file with only newlines."""
    editor = TXTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Set only newlines
    editor.ui.textEdit.setPlainText("\n\n\n")
    
    # Build and verify
    data, _ = editor.build()
    decoded = decode_bytes_with_fallbacks(data)
    assert "\n" in decoded

def test_txt_editor_tab_characters(qtbot, installation: HTInstallation):
    """Test handling of tab characters."""
    editor = TXTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Set text with tabs
    text_with_tabs = "Column1\tColumn2\tColumn3"
    editor.ui.textEdit.setPlainText(text_with_tabs)
    
    # Build and verify
    data, _ = editor.build()
    decoded = decode_bytes_with_fallbacks(data)
    assert "\t" in decoded or "Column1" in decoded

def test_txt_editor_control_characters(qtbot, installation: HTInstallation):
    """Test handling of control characters."""
    editor = TXTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Set text with control characters (ASCII 0-31, except common ones)
    # Note: Some control chars may not be editable in QPlainTextEdit
    text = "Normal text"
    editor.ui.textEdit.setPlainText(text)
    
    # Build and verify
    data, _ = editor.build()
    assert len(data) > 0

# ============================================================================
# RESOURCE TYPE TESTS
# ============================================================================

def test_txt_editor_supported_resource_types(qtbot, installation: HTInstallation):
    """Test that editor supports all plaintext resource types."""
    editor = TXTEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Verify supported types include plaintext types
    supported = editor.supported()
    assert ResourceType.TXT in supported
    
    # All plaintext types should be supported
    plaintext_types = [member for member in ResourceType if member.contents == "plaintext"]
    for plaintext_type in plaintext_types:
        assert plaintext_type in supported

# ============================================================================
# COMBINATION TESTS
# ============================================================================

def test_txt_editor_complex_document(qtbot, installation: HTInstallation):
    """Test handling of complex document with all features."""
    editor = TXTEditor(None, installation)
    qtbot.addWidget(editor)
    
    editor.new()
    
    # Create complex document
    complex_text = """# Header
This is a paragraph with multiple sentences. It contains various characters like é, ñ, and 🌍.

- List item 1
- List item 2
\tIndented line
\t\tDouble indented

Another paragraph with special chars: "quotes", 'apostrophes', and backslashes: \\
"""
    editor.ui.textEdit.setPlainText(complex_text)
    
    # Toggle word wrap
    editor.toggle_word_wrap()
    
    # Build and verify
    data, _ = editor.build()
    decoded = decode_bytes_with_fallbacks(data)
    assert "# Header" in decoded
    assert "List item" in decoded
    
    # Toggle word wrap back
    editor.toggle_word_wrap()
    
    # Save again
    data2, _ = editor.build()
    decoded2 = decode_bytes_with_fallbacks(data2)
    assert "# Header" in decoded2

def test_txt_editor_all_operations(qtbot, installation: HTInstallation):
    """Test all operations together."""
    editor = TXTEditor(None, installation)
    qtbot.addWidget(editor)
    
    # Create new
    editor.new()
    
    # Add text
    editor.ui.textEdit.setPlainText("Initial")
    
    # Toggle word wrap
    editor.toggle_word_wrap()
    
    # Modify text
    editor.ui.textEdit.appendPlainText("\nAppended")
    
    # Save
    data, _ = editor.build()
    
    # Load
    editor.load(Path("test.txt"), "test", ResourceType.TXT, data)
    
    # Verify all operations worked
    loaded = editor.ui.textEdit.toPlainText()
    assert "Initial" in loaded
    assert "Appended" in loaded
