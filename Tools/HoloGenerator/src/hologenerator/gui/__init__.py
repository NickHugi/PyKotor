"""
HoloGenerator GUI package.

Contains the tkinter-based graphical interface for the configuration generator.
All tkinter imports are protected to ensure the core functionality works
without requiring tkinter.
"""

# Protected import test
try:
    import tkinter
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

__all__ = ["GUI_AVAILABLE"]

if GUI_AVAILABLE:
    from hologenerator.gui.main import main
    __all__.append("main")