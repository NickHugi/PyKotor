from __future__ import annotations

from typing import Any

LOCAL_PROGRAM_INFO: dict[str, Any] = {
    # <---JSON_START--->#{
    "currentVersion": "3.1.1",
    "toolsetLatestVersion": "3.1.1",
    "toolsetLatestBetaVersion": "3.1.1",
    "updateInfoLink": "https://api.github.com/repos/NickHugi/PyKotor/contents/Tools/HolocronToolset/src/toolset/config.py",
    "updateBetaInfoLink": "https://api.github.com/repos/NickHugi/PyKotor/contents/Tools/HolocronToolset/src/toolset/config.py?ref=bleeding-edge",
    "toolsetDownloadLink": "https://deadlystream.com/files/file/1982-holocron-toolset",
    "toolsetBetaDownloadLink": "https://github.com/NickHugi/PyKotor/releases/tag/v{tag}-toolset",
    "toolsetDirectLinks": {
        "Darwin": {
            "32bit": [],
            "64bit": ["https://mega.nz/file/0LxE3JYR#NUpzCQGQ8YThU9KPo2Ikql4c8jcBPnLfLwxsoVQtmN4", "https://github.com/NickHugi/PyKotor/releases/download/v{tag}-toolset/HolocronToolset_Mac_PyQt5_x64.zip"]
        },
        "Linux": {
            "32bit": [],
            "64bit": ["https://mega.nz/file/JOwW0RII#SbP3HsQxKbhpTBzmL5P1ynwwovJcuJOK6NbB1QvzI_8", "https://github.com/NickHugi/PyKotor/releases/download/v{tag}-toolset/HolocronToolset_Linux_PyQt5_x64.zip"]
        },
        "Windows": {
            "32bit": ["https://mega.nz/file/laAkmJxS#-CTNluRAhkoWeRvyrj8HGRwRgQMLVT-jlFdYMsKvLLE", "https://github.com/NickHugi/PyKotor/releases/download/v{tag}-toolset/HolocronToolset_Windows_PyQt5_x86.zip"],
            "64bit": ["https://mega.nz/file/0ex33YTJ#RlBxTx3AOdxj8tBmgFg8SsCMSdO5i9SYu2FNsktrtzc", "https://github.com/NickHugi/PyKotor/releases/download/v{tag}-toolset/HolocronToolset_Windows_PyQt5_x64.zip"]
        }
    },
    "toolsetBetaDirectLinks": {
        "Darwin": {
            "32bit": [],
            "64bit": ["https://mega.nz/file/0LxE3JYR#NUpzCQGQ8YThU9KPo2Ikql4c8jcBPnLfLwxsoVQtmN4", "https://github.com/NickHugi/PyKotor/releases/download/v{tag}-toolset/HolocronToolset_Mac_PyQt5_x64.zip"]
        },
        "Linux": {
            "32bit": [],
            "64bit": ["https://mega.nz/file/JOwW0RII#SbP3HsQxKbhpTBzmL5P1ynwwovJcuJOK6NbB1QvzI_8", "https://github.com/NickHugi/PyKotor/releases/download/v{tag}-toolset/HolocronToolset_Linux_PyQt5_x64.zip"]
        },
        "Windows": {
            "32bit": ["https://mega.nz/file/laAkmJxS#-CTNluRAhkoWeRvyrj8HGRwRgQMLVT-jlFdYMsKvLLE", "https://github.com/NickHugi/PyKotor/releases/download/v{tag}-toolset/HolocronToolset_Windows_PyQt5_x86.zip"],
            "64bit": ["https://mega.nz/file/0ex33YTJ#RlBxTx3AOdxj8tBmgFg8SsCMSdO5i9SYu2FNsktrtzc", "https://github.com/NickHugi/PyKotor/releases/download/v{tag}-toolset/HolocronToolset_Windows_PyQt5_x64.zip"]
        }
    },
    "toolsetLatestNotes": "Fixed major bug that was causing most editors to load data incorrectly.",
    "toolsetLatestBetaNotes": "A new major Release version is available.",
    "kits": {
        "Black Vulkar Base": {"version": 1, "id": "blackvulkar"},
        "Endar Spire": {"version": 1, "id": "endarspire"},
        "Hidden Bek Base": {"version": 1, "id": "hiddenbek"}
    },
    "help": {"version": 3}
}  #<---JSON_END--->#
CURRENT_VERSION = LOCAL_PROGRAM_INFO["currentVersion"]
