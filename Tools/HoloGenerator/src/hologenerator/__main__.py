#!/usr/bin/env python3
"""
HoloGenerator GUI Launcher

Main entry point for launching the HoloGenerator GUI application.
This tool is designed exclusively for GUI usage.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add the PyKotor library to the path
if getattr(sys, "frozen", False) is False:
    def update_sys_path(path):
        working_dir = str(path)
        hologenerator_path = path.parents[3].joinpath("Tools/HoloGenerator/src")
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.append(working_dir)
        # Add the hologenerator src directory to sys.path so the hologenerator package can be found
        sys.path.insert(0, str(hologenerator_path))

    pykotor_path = Path(__file__).parents[4] / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.exists():
        update_sys_path(pykotor_path.parent)

CURRENT_VERSION = "1.0.0"


def main():
    """Main entry point for launching the GUI application."""
    print(f"HoloGenerator version {CURRENT_VERSION}")
    print("KOTOR Configuration Generator for HoloPatcher")
    print()
    print("Launching GUI application...")
    
    try:
        from hologenerator.gui.main import main as gui_main
        gui_main()
    except ImportError as e:
        print(f"Error: {e}")
        print("GUI mode not available. Please ensure tkinter is installed.")
        print()
        print("HoloGenerator is a GUI-only tool. If you need command-line functionality,")
        print("please use KotorDiff instead.")
        sys.exit(1)
    except Exception as e:
        print(f"Failed to start GUI: {e.__class__.__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
