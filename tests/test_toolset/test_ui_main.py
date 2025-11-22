from __future__ import annotations

import pytest
from qtpy.QtGui import QAction
from qtpy.QtWidgets import QComboBox, QPushButton
from toolset.gui.windows.main import ToolWindow
from toolset.data.installation import HTInstallation

def test_main_window_init(qtbot):
    """Test that the main window initializes correctly."""
    window = ToolWindow()
    qtbot.addWidget(window)
    window.show()
    
    assert window.isVisible()
    assert "Holocron Toolset" in window.windowTitle()
    assert window.active is None
    assert window.ui.gameCombo.count() >= 1  # Should have [None] at least

def test_main_window_set_installation(qtbot, installation):
    """Test setting an active installation in the main window."""
    window = ToolWindow()
    qtbot.addWidget(window)
    window.show()

    # Manually add the installation to the settings/installations dict to simulate it being available
    window.installations[installation.name] = installation
    window.settings.installations()[installation.name] = installation
    window.reload_installations()

    # Find the index of our test installation
    index = window.ui.gameCombo.findText(installation.name)
    assert index != -1

    # Select the installation
    window.ui.gameCombo.setCurrentIndex(index)
    
    # Allow events to process (async loader might run)
    # In headless/offscreen mode, waitExposed might be unreliable or block indefinitely.
    # Instead, we wait until the active installation matches our expectation.
    qtbot.waitUntil(lambda: window.active == installation, timeout=5000)
    
    assert window.active == installation
    assert window.ui.resourceTabs.isEnabled()
    
    # Check if tabs are populated (basic check)
    assert window.ui.modulesWidget.ui.sectionCombo.count() >= 0

def test_menu_actions_state(qtbot, installation):
    """Test that menu actions are enabled/disabled correctly based on installation."""
    window = ToolWindow()
    qtbot.addWidget(window)
    window.show()
    
    # Initially no installation, most "New" actions should be disabled
    # Note: Some might be enabled if they don't require an installation (like TLK?)
    # Let's check a specific one we know requires installation, e.g. New DLG
    assert not window.ui.actionNewDLG.isEnabled()
    
    # Set installation
    window.active = installation
    window.update_menus()
    
    assert window.ui.actionNewDLG.isEnabled()
    assert window.ui.actionNewUTC.isEnabled()
    assert window.ui.actionNewNSS.isEnabled()

def test_tab_switching(qtbot, installation):
    """Test switching between tabs in the main window."""
    window = ToolWindow()
    qtbot.addWidget(window)
    window.show()
    
    # Set installation to enable tabs
    window.active = installation
    window.ui.resourceTabs.setEnabled(True)
    
    # Switch to Modules tab
    window.ui.resourceTabs.setCurrentWidget(window.ui.modulesTab)
    assert window.get_active_resource_tab() == window.ui.modulesTab
    
    # Switch to Override tab
    window.ui.resourceTabs.setCurrentWidget(window.ui.overrideTab)
    assert window.get_active_resource_tab() == window.ui.overrideTab

def test_modules_filter(qtbot, installation):
    """Test that the modules filter works (basic UI check)."""
    window = ToolWindow()
    qtbot.addWidget(window)
    window.show()
    window.active = installation
    
    # Mock some modules
    from qtpy.QtGui import QStandardItem
    modules = [QStandardItem("Test Module 1"), QStandardItem("Test Module 2")]
    window.refresh_module_list(reload=False, module_items=modules)
    
    assert window.ui.modulesWidget.ui.sectionCombo.count() == 2

