import pytest
from qtpy.QtWidgets import QWidget, QMainWindow
from unittest.mock import MagicMock, patch

from toolset.gui.windows.module_designer import ModuleDesigner
from toolset.gui.windows.kotordiff import KotorDiffWindow
from toolset.gui.windows.help_window import HelpWindow
from toolset.gui.windows.audio_player import AudioPlayer
from toolset.data.installation import HTInstallation

def test_module_designer_init(qtbot, installation: HTInstallation):
    """Test Module Designer initialization."""
    # Mocking settings or resource loading might be needed as it's heavy
    window = ModuleDesigner(installation)
    qtbot.addWidget(window)
    window.show()
    
    assert window.isVisible()
    assert "Module Designer" in window.windowTitle()
    
    # Test basic UI elements existence
    assert window.ui.moduleTree is not None
    assert window.ui.propertiesTable is not None

def test_kotordiff_init(qtbot, installation: HTInstallation):
    """Test KotorDiff window initialization."""
    window = KotorDiffWindow(installation)
    qtbot.addWidget(window)
    window.show()
    
    assert window.isVisible()
    assert "Kotor Diff" in window.windowTitle()
    
    # Check interactions
    # Clicking 'Compare' without files should probably show error or do nothing safe
    with patch("qtpy.QtWidgets.QMessageBox.warning") as mock_warn:
        window.compare()
        # Likely warns about missing files
        # Verify mocking worked if implemented

def test_help_window_init(qtbot):
    """Test Help Window initialization."""
    window = HelpWindow()
    qtbot.addWidget(window)
    window.show()
    
    assert window.isVisible()
    # Check if web engine or text viewer is present
    # Depending on implementation (QWebEngineView or QTextBrowser)

def test_audio_player_init(qtbot, installation: HTInstallation):
    """Test Audio Player window."""
    window = AudioPlayer(None, installation)
    qtbot.addWidget(window)
    window.show()
    
    assert window.isVisible()
    # Check controls
    assert hasattr(window.ui, "playButton")
    assert hasattr(window.ui, "stopButton")
    
    # Test loading a dummy audio file (mocked)
    # window.load_audio("test.wav")

def test_indoor_builder_init(qtbot, installation: HTInstallation):
    """Test Indoor Builder Window."""
    from toolset.gui.windows.indoor_builder import IndoorBuilder
    
    window = IndoorBuilder(installation)
    qtbot.addWidget(window)
    window.show()
    
    assert window.isVisible()
    assert "Indoor Builder" in window.windowTitle()
    
    # Check widgets
    # assert hasattr(window.ui, "roomList")
    # assert hasattr(window.ui, "propertiesDock")

