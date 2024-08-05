from __future__ import annotations
import sys

if sys.platform == "linux":
    from utility.system.Linux.file_folder_browser import *
    from utility.system.Linux.messagebox import *
elif sys.platform == "darwin":
    from utility.system.MacOS.file_folder_browser import *
    from macos.messagebox import *
elif sys.platform == "win32":
    from utility.system.win32.file_folder_browser import *
    from utility.system.win32.messagebox import *
else:
    raise RuntimeError(f"Unsupported platform: {sys.platform}")