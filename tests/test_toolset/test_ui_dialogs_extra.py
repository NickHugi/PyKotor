import pytest
from qtpy.QtWidgets import QWidget, QDialog
from toolset.data.installation import HTInstallation
from unittest.mock import MagicMock, patch

# Import dialogs to test
from toolset.gui.dialogs.extract_options import ExtractOptionsDialog
from toolset.gui.dialogs.select_module import SelectModuleDialog
from toolset.gui.dialogs.indoor_settings import IndoorMapSettings

def test_extract_options_dialog(qtbot):
    """Test ExtractOptionsDialog."""
    parent = QWidget()
    dialog = ExtractOptionsDialog(parent)
    qtbot.addWidget(dialog)
    dialog.show()
    
    assert dialog.isVisible()
    
    # Test checkbox toggles
    dialog.ui.convertTpcCheck.setChecked(True)
    assert dialog.options().texture_format is not None # Logic likely sets a format
    
    dialog.ui.convertTpcCheck.setChecked(False)
    # Check logic

def test_select_module_dialog(qtbot, installation: HTInstallation):
    """Test SelectModuleDialog."""
    parent = QWidget()
    
    # Mock modules list
    installation.module_names = lambda use_hardcoded=True: {"test_mod": "Test Module", "other_mod": "Other Module"}
    
    dialog = SelectModuleDialog(parent, installation)
    qtbot.addWidget(dialog)
    dialog.show()
    
    assert dialog.isVisible()
    assert dialog.ui.moduleList.count() >= 2
    
    # Filter functionality
    dialog.ui.filterEdit.setText("Other")
    # Check if list filtered (if implemented)
    # Assuming QListWidget or similar
    
    # Select item
    # dialog.ui.moduleList.setCurrentRow(0)
    # assert dialog.selected_module() == ...

def test_indoor_settings_dialog(qtbot, installation: HTInstallation):
    """Test IndoorMapSettings."""
    from toolset.data.indoormap import IndoorMap
    from toolset.data.indoorkit import Kit
    
    parent = QWidget()
    indoor_map = IndoorMap()
    kits: list[Kit] = []
    dialog = IndoorMapSettings(parent, installation, indoor_map, kits)
    qtbot.addWidget(dialog)
    dialog.show()
    
    assert dialog.isVisible()
    # Test generic settings widgets

def test_inventory_editor(qtbot, installation: HTInstallation):
    """Test InventoryEditor."""
    from toolset.gui.dialogs.inventory import InventoryEditor
    from pykotor.extract.capsule import LazyCapsule
    
    # Mock parent and data
    parent = QWidget()
    capsules = [] # No capsules for now
    inventory = []
    equipment = []
    
    dialog = InventoryEditor(parent, installation, capsules, [], inventory, equipment, droid=False)
    qtbot.addWidget(dialog)
    dialog.show()
    
    assert dialog.isVisible()
    # Check for inventory lists
    assert hasattr(dialog.ui, "inventoryList")
    assert hasattr(dialog.ui, "equipmentList")
    
    # Test add/remove logic if possible without heavy data
    # Usually requires drag/drop or button clicks


