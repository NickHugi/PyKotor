import pytest
from toolset.gui.dialogs.about import About
from toolset.config import LOCAL_PROGRAM_INFO

def test_about_dialog_init(qtbot):
    """Test About dialog initialization."""
    # Need a parent widget
    from qtpy.QtWidgets import QWidget
    parent = QWidget()
    
    dialog = About(parent)
    qtbot.addWidget(dialog)
    dialog.show()
    
    assert dialog.isVisible()
    assert dialog.ui.aboutLabel.text().find(LOCAL_PROGRAM_INFO["currentVersion"]) != -1
    
    # Test close button
    dialog.ui.closeButton.click()
    assert not dialog.isVisible()
