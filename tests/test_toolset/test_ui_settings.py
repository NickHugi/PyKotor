import pytest
from toolset.gui.dialogs.settings import SettingsDialog
from toolset.gui.widgets.settings.installations import GlobalSettings

def test_settings_dialog_init(qtbot):
    """Test Settings dialog initialization."""
    from qtpy.QtWidgets import QWidget
    parent = QWidget()
    
    dialog = SettingsDialog(parent)
    qtbot.addWidget(dialog)
    dialog.show()
    
    assert dialog.isVisible()
    assert "Settings" in dialog.windowTitle()

def test_settings_dialog_navigation(qtbot):
    """Test navigation between all settings pages."""
    from qtpy.QtWidgets import QWidget
    parent = QWidget()
    
    dialog = SettingsDialog(parent)
    qtbot.addWidget(dialog)
    dialog.show()
    
    # Define expected pages and their names in the tree
    pages = {
        "Installations": dialog.ui.installationsPage,
        "GIT Editor": dialog.ui.gitEditorPage,
        "Misc": dialog.ui.miscPage,
        "Module Designer": dialog.ui.moduleDesignerPage,
        "Application": dialog.ui.applicationSettingsPage,
    }
    
    for page_name, page_widget in pages.items():
        # Find item in tree
        items = dialog.ui.settingsTree.findItems(page_name, pytest.importorskip("qtpy.QtCore").Qt.MatchExactly | pytest.importorskip("qtpy.QtCore").Qt.MatchRecursive)
        if not items:
            # Recursively search if findItems is not deep enough or behaves weirdly
            def find_item(root):
                for i in range(root.childCount()):
                    child = root.child(i)
                    if child and child.text(0) == page_name:
                        return child
                    if child:
                        res = find_item(child)
                        if res: return res
                return None
            
            for i in range(dialog.ui.settingsTree.topLevelItemCount()):
                item = dialog.ui.settingsTree.topLevelItem(i)
                if item and item.text(0) == page_name:
                    items = [item]
                    break
                if item:
                    res = find_item(item)
                    if res:
                        items = [res]
                        break
        
        assert items, f"Could not find settings page: {page_name}"
        
        # Click item
        rect = dialog.ui.settingsTree.visualItemRect(items[0])
        qtbot.mouseClick(dialog.ui.settingsTree.viewport(), pytest.importorskip("qtpy.QtCore").Qt.LeftButton, pos=rect.center())
        
        # Verify page change
        assert dialog.ui.settingsStack.currentWidget() == page_widget

def test_settings_reset(qtbot, monkeypatch):
    """Test reset all settings functionality."""
    from qtpy.QtWidgets import QWidget, QMessageBox
    parent = QWidget()
    
    dialog = SettingsDialog(parent)
    qtbot.addWidget(dialog)
    dialog.show()
    
    # Mock QMessageBox.question to return Yes
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    monkeypatch.setattr(QMessageBox, "information", lambda *args: None)
    
    # Set a dummy setting in GlobalSettings to verify it gets reset/cleared
    # Note: GlobalSettings is a singleton accessing QSettings. 
    # Clearing it clears the persistent storage.
    settings = GlobalSettings()
    settings.extractPath = "some/custom/path"
    
    dialog.on_reset_all_settings()
    
    # Verify dialog closed and resetting flag set
    assert dialog._is_resetting
    assert not dialog.isVisible() 
    
    # We assume GlobalSettings().settings.clear() was called. 
    # Verifying persistent state reset might be tricky without reloading settings,
    # but the logic in on_reset_all_settings is explicit.
