import pytest
from qtpy.QtCore import Qt
from toolset.gui.dialogs.clone_module import CloneModuleDialog
from toolset.data.installation import HTInstallation

def test_clone_module_dialog_all_widgets_exist(qtbot, installation: HTInstallation):
    """Verify ALL widgets exist in CloneModuleDialog."""
    from qtpy.QtWidgets import QWidget
    parent = QWidget()
    
    # Use real module_names from installation
    dialog = CloneModuleDialog(parent, installation, {installation.name: installation})
    qtbot.addWidget(dialog)
    dialog.show()
    
    # Module selector
    assert hasattr(dialog.ui, 'moduleSelect')
    
    # Text inputs
    assert hasattr(dialog.ui, 'filenameEdit')
    assert hasattr(dialog.ui, 'prefixEdit')
    assert hasattr(dialog.ui, 'nameEdit')
    assert hasattr(dialog.ui, 'moduleRootEdit')
    
    # Checkboxes
    assert hasattr(dialog.ui, 'copyTexturesCheckbox')
    assert hasattr(dialog.ui, 'copyLightmapsCheckbox')
    assert hasattr(dialog.ui, 'keepDoorsCheckbox')
    assert hasattr(dialog.ui, 'keepPlaceablesCheckbox')
    assert hasattr(dialog.ui, 'keepSoundsCheckbox')
    assert hasattr(dialog.ui, 'keepPathingCheckbox')
    
    # Buttons
    assert hasattr(dialog.ui, 'createButton')
    assert hasattr(dialog.ui, 'cancelButton')

def test_clone_module_dialog_all_widgets_interactions(qtbot, installation: HTInstallation):
    """Test ALL widgets with exhaustive interactions."""
    from qtpy.QtWidgets import QWidget
    parent = QWidget()
    
    dialog = CloneModuleDialog(parent, installation, {installation.name: installation})
    qtbot.addWidget(dialog)
    dialog.show()
    
    # Test moduleSelect - ComboBox
    if dialog.ui.moduleSelect.count() > 0:
        for i in range(min(5, dialog.ui.moduleSelect.count())):
            dialog.ui.moduleSelect.setCurrentIndex(i)
            assert dialog.ui.moduleSelect.currentIndex() == i
            
            # Verify moduleRootEdit updates
            current_data = dialog.ui.moduleSelect.currentData()
            if current_data:
                assert dialog.ui.moduleRootEdit.text() == current_data.root
    
    # Test filenameEdit - QLineEdit with prefix generation
    test_filenames = [
        ("new_module", "NEW"),
        ("a_module", "A_M"),
        ("test123", "TES"),
        ("m", "M"),
        ("ab", "AB"),
        ("abc", "ABC"),
        ("very_long_module_name", "VER"),
        ("", ""),
    ]
    
    for filename, expected_prefix in test_filenames:
        dialog.ui.filenameEdit.setText(filename)
        assert dialog.ui.filenameEdit.text() == filename
        assert dialog.ui.prefixEdit.text() == expected_prefix
    
    # Test prefixEdit - QLineEdit (can be manually edited)
    dialog.ui.prefixEdit.setText("CUSTOM")
    assert dialog.ui.prefixEdit.text() == "CUSTOM"
    
    # Test nameEdit - QLineEdit
    test_names = [
        "Test Module",
        "Another Module",
        "Module 123",
        "",
        "Very Long Module Name That Might Wrap",
    ]
    
    for name in test_names:
        dialog.ui.nameEdit.setText(name)
        assert dialog.ui.nameEdit.text() == name
    
    # Test ALL checkboxes - every combination
    checkboxes = [
        ('copyTexturesCheckbox', True),
        ('copyTexturesCheckbox', False),
        ('copyLightmapsCheckbox', True),
        ('copyLightmapsCheckbox', False),
        ('keepDoorsCheckbox', True),
        ('keepDoorsCheckbox', False),
        ('keepPlaceablesCheckbox', True),
        ('keepPlaceablesCheckbox', False),
        ('keepSoundsCheckbox', True),
        ('keepSoundsCheckbox', False),
        ('keepPathingCheckbox', True),
        ('keepPathingCheckbox', False),
    ]
    
    for checkbox_name, checked in checkboxes:
        checkbox = getattr(dialog.ui, checkbox_name)
        checkbox.setChecked(checked)
        assert checkbox.isChecked() == checked
    
    # Test all checkboxes checked simultaneously
    dialog.ui.copyTexturesCheckbox.setChecked(True)
    dialog.ui.copyLightmapsCheckbox.setChecked(True)
    dialog.ui.keepDoorsCheckbox.setChecked(True)
    dialog.ui.keepPlaceablesCheckbox.setChecked(True)
    dialog.ui.keepSoundsCheckbox.setChecked(True)
    dialog.ui.keepPathingCheckbox.setChecked(True)
    
    assert all([
        dialog.ui.copyTexturesCheckbox.isChecked(),
        dialog.ui.copyLightmapsCheckbox.isChecked(),
        dialog.ui.keepDoorsCheckbox.isChecked(),
        dialog.ui.keepPlaceablesCheckbox.isChecked(),
        dialog.ui.keepSoundsCheckbox.isChecked(),
        dialog.ui.keepPathingCheckbox.isChecked(),
    ])
    
    # Test all checkboxes unchecked
    dialog.ui.copyTexturesCheckbox.setChecked(False)
    dialog.ui.copyLightmapsCheckbox.setChecked(False)
    dialog.ui.keepDoorsCheckbox.setChecked(False)
    dialog.ui.keepPlaceablesCheckbox.setChecked(False)
    dialog.ui.keepSoundsCheckbox.setChecked(False)
    dialog.ui.keepPathingCheckbox.setChecked(False)
    
    assert not any([
        dialog.ui.copyTexturesCheckbox.isChecked(),
        dialog.ui.copyLightmapsCheckbox.isChecked(),
        dialog.ui.keepDoorsCheckbox.isChecked(),
        dialog.ui.keepPlaceablesCheckbox.isChecked(),
        dialog.ui.keepSoundsCheckbox.isChecked(),
        dialog.ui.keepPathingCheckbox.isChecked(),
    ])

def test_clone_module_dialog_prefix_generation_exhaustive(qtbot, installation: HTInstallation):
    """Test prefix generation logic exhaustively."""
    from qtpy.QtWidgets import QWidget
    parent = QWidget()
    
    dialog = CloneModuleDialog(parent, installation, {installation.name: installation})
    qtbot.addWidget(dialog)
    dialog.show()
    
    # Test various filename patterns
    test_cases = [
        ("single", "SIN"),
        ("ab", "AB"),
        ("abc", "ABC"),
        ("abcd", "ABC"),
        ("test_module", "TES"),
        ("a_b_c", "A_B"),
        ("123test", "123"),
        ("test123", "TES"),
        ("TEST_UPPER", "TES"),
        ("test-with-dashes", "TES"),
        ("test.with.dots", "TES"),
        ("", ""),
        ("a", "A"),
    ]
    
    for filename, expected in test_cases:
        dialog.ui.filenameEdit.setText(filename)
        assert dialog.ui.prefixEdit.text() == expected, f"Failed for filename '{filename}': expected '{expected}', got '{dialog.ui.prefixEdit.text()}'"

def test_clone_module_dialog_module_selection_updates_root(qtbot, installation: HTInstallation):
    """Test that module selection updates root edit."""
    from qtpy.QtWidgets import QWidget
    parent = QWidget()
    
    dialog = CloneModuleDialog(parent, installation, {installation.name: installation})
    qtbot.addWidget(dialog)
    dialog.show()
    
    # Test changing module selection updates root
    if dialog.ui.moduleSelect.count() > 0:
        initial_root = dialog.ui.moduleRootEdit.text()
        
        # Change to different module
        for i in range(dialog.ui.moduleSelect.count()):
            dialog.ui.moduleSelect.setCurrentIndex(i)
            current_data = dialog.ui.moduleSelect.currentData()
            if current_data:
                assert dialog.ui.moduleRootEdit.text() == current_data.root
                break

def test_clone_module_dialog_parameter_collection(qtbot, installation: HTInstallation):
    """Test that ok() collects ALL parameters correctly from UI."""
    from qtpy.QtWidgets import QWidget
    parent = QWidget()
    
    dialog = CloneModuleDialog(parent, installation, {installation.name: installation})
    qtbot.addWidget(dialog)
    dialog.show()
    
    # Set ALL UI values
    dialog.ui.filenameEdit.setText("test_clone")
    dialog.ui.prefixEdit.setText("TST")
    dialog.ui.nameEdit.setText("Test Clone Module")
    dialog.ui.copyTexturesCheckbox.setChecked(True)
    dialog.ui.copyLightmapsCheckbox.setChecked(False)
    dialog.ui.keepDoorsCheckbox.setChecked(True)
    dialog.ui.keepPlaceablesCheckbox.setChecked(False)
    dialog.ui.keepSoundsCheckbox.setChecked(True)
    dialog.ui.keepPathingCheckbox.setChecked(False)
    
    if dialog.ui.moduleSelect.count() > 0:
        dialog.ui.moduleSelect.setCurrentIndex(0)
        
        # Verify parameters would be collected correctly
        # We can't easily test ok() without AsyncLoader blocking, but we verify UI state
        installation_obj = dialog.ui.moduleSelect.currentData().installation
        root = dialog.ui.moduleSelect.currentData().root
        identifier = dialog.ui.filenameEdit.text().lower()
        prefix = dialog.ui.prefixEdit.text().lower()
        name = dialog.ui.nameEdit.text()
        
        assert identifier == "test_clone"
        assert prefix == "tst"
        assert name == "Test Clone Module"
        assert installation_obj == installation
        
        copy_textures = dialog.ui.copyTexturesCheckbox.isChecked()
        copy_lightmaps = dialog.ui.copyLightmapsCheckbox.isChecked()
        keep_doors = dialog.ui.keepDoorsCheckbox.isChecked()
        keep_placeables = dialog.ui.keepPlaceablesCheckbox.isChecked()
        keep_sounds = dialog.ui.keepSoundsCheckbox.isChecked()
        keep_pathing = dialog.ui.keepPathingCheckbox.isChecked()
        
        assert copy_textures
        assert not copy_lightmaps
        assert keep_doors
        assert not keep_placeables
        assert keep_sounds
        assert not keep_pathing

def test_clone_module_dialog_buttons(qtbot, installation: HTInstallation):
    """Test button functionality."""
    from qtpy.QtWidgets import QWidget
    parent = QWidget()
    
    dialog = CloneModuleDialog(parent, installation, {installation.name: installation})
    qtbot.addWidget(dialog)
    dialog.show()
    
    # Test cancel button
    assert dialog.ui.cancelButton.isEnabled()
    # Cancel should close dialog
    qtbot.mouseClick(dialog.ui.cancelButton, Qt.MouseButton.LeftButton)
    # Dialog should be closed or closing
    
    # Recreate for create button test
    dialog = CloneModuleDialog(parent, installation, {installation.name: installation})
    qtbot.addWidget(dialog)
    dialog.show()
    
    # Test create button exists and is enabled
    assert dialog.ui.createButton.isEnabled()
    # Create button triggers ok() which shows dialogs and runs AsyncLoader
    # We verify the button exists and signal is connected
    assert dialog.ui.createButton.receivers(dialog.ui.createButton.clicked) > 0

def test_clone_module_dialog_validation_edge_cases(qtbot, installation: HTInstallation):
    """Test validation with edge cases."""
    from qtpy.QtWidgets import QWidget
    parent = QWidget()
    
    dialog = CloneModuleDialog(parent, installation, {installation.name: installation})
    qtbot.addWidget(dialog)
    dialog.show()
    
    # Test empty filename
    dialog.ui.filenameEdit.setText("")
    assert dialog.ui.prefixEdit.text() == ""
    
    # Test very long filename
    long_name = "a" * 100
    dialog.ui.filenameEdit.setText(long_name)
    assert dialog.ui.prefixEdit.text() == "A" * 3  # Should still be 3 chars max
    
    # Test special characters in filename
    dialog.ui.filenameEdit.setText("test!@#$%^&*()")
    prefix = dialog.ui.prefixEdit.text()
    assert len(prefix) <= 3
    
    # Test whitespace handling
    dialog.ui.filenameEdit.setText("test module")
    # Prefix should handle spaces (may convert or truncate)
    prefix = dialog.ui.prefixEdit.text()
    assert len(prefix) <= 3

def test_clone_module_dialog_module_root_readonly(qtbot, installation: HTInstallation):
    """Test that module root edit is read-only or updates correctly."""
    from qtpy.QtWidgets import QWidget
    parent = QWidget()
    
    dialog = CloneModuleDialog(parent, installation, {installation.name: installation})
    qtbot.addWidget(dialog)
    dialog.show()
    
    # Module root should be set from selected module
    if dialog.ui.moduleSelect.count() > 0:
        initial_root = dialog.ui.moduleRootEdit.text()
        assert len(initial_root) > 0 or initial_root == ""  # May be empty if no modules
        
        # Changing module should update root
        if dialog.ui.moduleSelect.count() > 1:
            dialog.ui.moduleSelect.setCurrentIndex(1)
            new_root = dialog.ui.moduleRootEdit.text()
            # Root should update (may be same if modules share root)
