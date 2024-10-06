from __future__ import annotations

import base64
import json
import multiprocessing
import re

from contextlib import suppress
from typing import Any

import requests

from loggerplus import RobustLogger
from qtpy.QtWidgets import QMessageBox

from utility.error_handling import universal_simplify_exception

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


def fetch_update_info(update_link: str, timeout: int = 15) -> Any:
    req = requests.get(update_link, timeout=timeout)
    req.raise_for_status()
    file_data = req.json()
    return file_data


def getRemoteToolsetUpdateInfo(
    *,
    useBetaChannel: bool = False,
    silent: bool = False,
) -> Exception | dict[str, Any]:
    if useBetaChannel:
        UPDATE_INFO_LINK = LOCAL_PROGRAM_INFO["updateBetaInfoLink"]
    else:
        UPDATE_INFO_LINK = LOCAL_PROGRAM_INFO["updateInfoLink"]

    # Use multiprocessing pool to handle timeout
    pool = multiprocessing.Pool(1)  # Create a Pool with a single worker
    try:  # Download this same file config.py from the repo and only parse the json between the markers. This prevents remote execution security issues.
        timeout = 2 if silent else 10
        result = pool.apply_async(fetch_update_info, [UPDATE_INFO_LINK, timeout])
        file_data = result.get(timeout=timeout)
        base64_content = file_data["content"]
        decoded_content = base64.b64decode(base64_content)  # Correctly decoding the base64 content
        decoded_content_str = decoded_content.decode(encoding="utf-8")
        json_data_match = re.search(r"<---JSON_START--->\s*\#\s*(.*?)\s*\#\s*<---JSON_END--->", decoded_content_str, flags=re.DOTALL)

        if not json_data_match:
            raise ValueError(f"JSON data not found or markers are incorrect: {json_data_match}")  # noqa: TRY301
        json_str = json_data_match[1]
        remoteInfo = json.loads(json_str)
        if not isinstance(remoteInfo, dict):
            raise TypeError(f"Expected remoteInfo to be a dict, instead got type {remoteInfo.__class__.__name__}")  # noqa: TRY301
    except Exception as e:  # noqa: BLE001
        pool.terminate()  # Terminate the pool
        errMsg = str(universal_simplify_exception(e))
        result = silent or QMessageBox.question(
            None,
            "Error occurred fetching update information.",
            (
                "An error occurred while fetching the latest toolset information.<br><br>"
                + errMsg.replace("\n", "<br>")
                + "<br><br>"
                + "Would you like to check against the local database instead?"
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if result not in {QMessageBox.StandardButton.Yes, True}:
            return e
        remoteInfo = LOCAL_PROGRAM_INFO
    finally:
        pool.close()  # Close the pool
        pool.join()  # Wait for the worker to finish
    return remoteInfo


def is_remote_version_newer(localVersion: str, remoteVersion: str) -> bool | None:
    version_check: bool | None = None
    with suppress(Exception):
        from packaging import version

        version_check = version.parse(remoteVersion) > version.parse(localVersion)
    if version_check is None:
        RobustLogger().warning(f"Version string might be malformed, attempted 'packaging.version.parse({localVersion}) > packaging.version.parse({remoteVersion})'")
        with suppress(Exception):
            from distutils.version import LooseVersion

            version_check = LooseVersion(remoteVersion) > LooseVersion(localVersion)
    return version_check


def version_to_toolset_tag(version: str) -> str:
    major_minor_patch_count = 2
    if version.count(".") == major_minor_patch_count:
        second_dot_index = version.find(".", version.find(".") + 1)  # Find the index of the second dot
        version = version[:second_dot_index] + version[second_dot_index + 1:]  # Remove the second dot by slicing and concatenating
    return f"v{version}-toolset"

def toolset_tag_to_version(tag: str) -> str:
    numeric_part: str = "".join([c for c in tag if c.isdigit() or c == "."])
    parts = numeric_part.split(".")

    major_minor_patch_len = 3
    if len(parts) == major_minor_patch_len:
        return ".".join(parts)
    major_minor_len = 2
    if len(parts) == major_minor_len:
        return ".".join(parts)

    # Handle the legacy typo format (missing second dot)
    major_len = 1
    major: str = parts[0]
    if len(parts) > major_len:
        # Assume the minor version always precedes the concatenated patch version
        minor = parts[1][0]  # Take the first digit as the minor version
        patch = parts[1][1:]  # The rest is considered the patch
        return f"{major}.{minor}.{patch}"

    return f"{major}.0.0"  # In case there's only a major version
