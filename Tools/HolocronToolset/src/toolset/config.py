from __future__ import annotations

from typing import Any

# This file serves two purposes:
# 1. Contains LOCAL_PROGRAM_INFO JSON that GitHub serves for updates
# 2. Re-exports everything from the modular config structure
#
# The JSON in this file is what gets fetched from GitHub during updates.
# All code should import from toolset.config (which uses the modular structure),
# but this file must exist and contain the JSON for the update mechanism.

# Import functions from modular structure (but not LOCAL_PROGRAM_INFO - that's defined below)
from toolset.config.config_update import (
    fetch_update_info,
    get_remote_toolset_update_info,
    is_remote_version_newer,
)
from toolset.config.config_version import toolset_tag_to_version, version_to_toolset_tag

# Re-export everything for backward compatibility
__all__ = [
    "LOCAL_PROGRAM_INFO",
    "CURRENT_VERSION",
    "fetch_update_info",
    "get_remote_toolset_update_info",
    "is_remote_version_newer",
    "toolset_tag_to_version",
    "version_to_toolset_tag",
]

# For backward compatibility with old camelCase names (not used, but kept for safety)
getRemoteToolsetUpdateInfo = get_remote_toolset_update_info
remoteVersionNewer = is_remote_version_newer

# The JSON below is what GitHub serves for updates.
# It must match the structure in config_info.py, but this file is the source of truth for updates.
LOCAL_PROGRAM_INFO: dict[str, Any] = {
    # <---JSON_START--->#{
    "currentVersion": "3.1.2",
    "toolsetLatestVersion": "3.1.1",
    "toolsetLatestBetaVersion": "3.1.1",
    "updateInfoLink": "https://api.github.com/repos/NickHugi/PyKotor/contents/Tools/HolocronToolset/src/toolset/config.py",
    "updateBetaInfoLink": "https://api.github.com/repos/NickHugi/PyKotor/contents/Tools/HolocronToolset/src/toolset/config.py?ref=bleeding-edge",
    "toolsetDownloadLink": "https://deadlystream.com/files/file/1982-holocron-toolset",
    "toolsetBetaDownloadLink": "https://github.com/NickHugi/PyKotor/releases/tag/v{tag}-toolset",
    "toolsetDirectLinks": {
        "Darwin": {
            "32bit": [],
            "64bit": [
                "https://mega.nz/file/0LxE3JYR#NUpzCQGQ8YThU9KPo2Ikql4c8jcBPnLfLwxsoVQtmN4",
                "https://github.com/NickHugi/PyKotor/releases/download/v{tag}-toolset/HolocronToolset_Mac_PyQt5_x64.zip",
            ],
        },
        "Linux": {
            "32bit": [],
            "64bit": [
                "https://mega.nz/file/JOwW0RII#SbP3HsQxKbhpTBzmL5P1ynwwovJcuJOK6NbB1QvzI_8",
                "https://github.com/NickHugi/PyKotor/releases/download/v{tag}-toolset/HolocronToolset_Linux_PyQt5_x64.zip",
            ],
        },
        "Windows": {
            "32bit": [
                "https://mega.nz/file/laAkmJxS#-CTNluRAhkoWeRvyrj8HGRwRgQMLVT-jlFdYMsKvLLE",
                "https://github.com/NickHugi/PyKotor/releases/download/v{tag}-toolset/HolocronToolset_Windows_PyQt5_x86.zip",
            ],
            "64bit": [
                "https://mega.nz/file/0ex33YTJ#RlBxTx3AOdxj8tBmgFg8SsCMSdO5i9SYu2FNsktrtzc",
                "https://github.com/NickHugi/PyKotor/releases/download/v{tag}-toolset/HolocronToolset_Windows_PyQt5_x64.zip",
            ],
        },
    },
    "toolsetBetaDirectLinks": {
        "Darwin": {
            "32bit": [],
            "64bit": [
                "https://mega.nz/file/0LxE3JYR#NUpzCQGQ8YThU9KPo2Ikql4c8jcBPnLfLwxsoVQtmN4",
                "https://github.com/NickHugi/PyKotor/releases/download/v{tag}-toolset/HolocronToolset_Mac_PyQt5_x64.zip",
            ],
        },
        "Linux": {
            "32bit": [],
            "64bit": [
                "https://mega.nz/file/JOwW0RII#SbP3HsQxKbhpTBzmL5P1ynwwovJcuJOK6NbB1QvzI_8",
                "https://github.com/NickHugi/PyKotor/releases/download/v{tag}-toolset/HolocronToolset_Linux_PyQt5_x64.zip",
            ],
        },
        "Windows": {
            "32bit": [
                "https://mega.nz/file/laAkmJxS#-CTNluRAhkoWeRvyrj8HGRwRgQMLVT-jlFdYMsKvLLE",
                "https://github.com/NickHugi/PyKotor/releases/download/v{tag}-toolset/HolocronToolset_Windows_PyQt5_x86.zip",
            ],
            "64bit": [
                "https://mega.nz/file/0ex33YTJ#RlBxTx3AOdxj8tBmgFg8SsCMSdO5i9SYu2FNsktrtzc",
                "https://github.com/NickHugi/PyKotor/releases/download/v{tag}-toolset/HolocronToolset_Windows_PyQt5_x64.zip",
            ],
        },
    },
    "toolsetLatestNotes": "Path editor now creates bidirectional links automatically, eliminating manual reciprocal edges and preventing zero-connection points.",
    "toolsetLatestBetaNotes": "Path editor now creates bidirectional links automatically, eliminating manual reciprocal edges and preventing zero-connection points.",
    "kits": {
        "Black Vulkar Base": {"version": 1, "id": "blackvulkar"},
        "Endar Spire": {"version": 1, "id": "endarspire"},
        "Hidden Bek Base": {"version": 1, "id": "hiddenbek"},
    },
    "help": {"version": 3},
}  # <---JSON_END--->#

# Override CURRENT_VERSION from the JSON in this file (this is the source of truth for updates)
CURRENT_VERSION = LOCAL_PROGRAM_INFO["currentVersion"]
