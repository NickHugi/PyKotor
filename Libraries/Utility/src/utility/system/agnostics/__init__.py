from __future__ import annotations
import sys

if sys.platform == "linux":
    from utility.system.Linux.file_folder_browser import *  # noqa: F403
    from utility.system.Linux.messagebox import *  # noqa: F403
elif sys.platform == "darwin":
    from utility.system.MacOS.file_folder_browser import *  # noqa: F403
    from utility.system.MacOS.messagebox import *  # noqa: F403
elif sys.platform == "win32":
    from utility.system.win32.file_folder_browser import *  # noqa: F403
    from utility.system.win32.messagebox import *  # noqa: F403
else:
    raise RuntimeError(f"Unsupported platform: '{sys.platform}'")
