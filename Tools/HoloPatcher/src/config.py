from __future__ import annotations

import base64
import json
import re

from contextlib import suppress
from tkinter import messagebox
from typing import Any

from utility.error_handling import universal_simplify_exception

LOCAL_PROGRAM_INFO: dict[str, Any] = {
    # <---JSON_START--->#{
    "currentVersion": "1.5.2",
    "holopatcherLatestVersion": "1.5.2",
    "holopatcherLatestBetaVersion": "1.5.3a1",
    "updateInfoLink": "https://api.github.com/repos/th3w1zard1/PyKotor/contents/Tools/HoloPatcher/src/config.py?ref=auto-update-toolset-t2",
    "updateBetaInfoLink": "https://api.github.com/repos/th3w1zard1/PyKotor/contents/Tools/HoloPatcher/src/config.py?ref=auto-update-toolset-t2",
    "holopatcherDownloadLink": "https://deadlystream.com/files/file/1982-holocron-holopatcher",
    "holopatcherBetaDownloadLink": "https://mega.nz/folder/cGJDAKaa#WzsWF8LgUkM8U2FDEoeeRA",
    "holopatcherDirectLinks": {
        "Darwin": {
            "32bit": [],
            "64bit": ["https://github.com/NickHugi/PyKotor/releases/download/{tag}/HoloPatcher_Mac.zip"]
        },
        "Linux": {
            "32bit": [],
            "64bit": ["https://github.com/NickHugi/PyKotor/releases/download/{tag}/HoloPatcher_Linux.zip"]
        },
        "Windows": {
            "32bit": ["https://github.com/NickHugi/PyKotor/releases/download/{tag}/HoloPatcher_Windows.zip"],
            "64bit": ["https://github.com/NickHugi/PyKotor/releases/download/{tag}/HoloPatcher_Windows.zip"]
        }
    },
    "holopatcherLatestNotes": "",
    "holopatcherLatestBetaNotes": "",
}  # <---JSON_END--->#

CURRENT_VERSION = LOCAL_PROGRAM_INFO["currentVersion"]

def getRemoteHolopatcherUpdateInfo(*, use_beta_channel: bool = False, silent: bool = False) -> Exception | dict[str, Any]:
    import requests
    if use_beta_channel:
        UPDATE_INFO_LINK = LOCAL_PROGRAM_INFO["updateBetaInfoLink"]
    else:
        UPDATE_INFO_LINK = LOCAL_PROGRAM_INFO["updateInfoLink"]

    try:  # Download this same file config.py from the repo and only parse the json between the markers. This prevents remote execution security issues.
        req = requests.get(UPDATE_INFO_LINK, timeout=15)
        req.raise_for_status()
        file_data = req.json()
        base64_content = file_data["content"]
        decoded_content = base64.b64decode(base64_content)  # Correctly decoding the base64 content
        decoded_content_str = decoded_content.decode(encoding="utf-8")
        # use for testing only:
        # with open("config.py") as f:
        #    decoded_content_str = f.read()
        # Use regex to extract the JSON part between the markers
        json_data_match = re.search(r"<---JSON_START--->\s\#\s(.*?)\s\#\s*<---JSON_END--->", decoded_content_str, flags=re.DOTALL)

        if not json_data_match:
            raise ValueError(f"JSON data not found or markers are incorrect: {json_data_match}")  # noqa: TRY301
        json_str = json_data_match.group(1)
        remote_info = json.loads(json_str)
        if not isinstance(remote_info, dict):
            raise TypeError(f"Expected remoteInfo to be a dict, instead got type {remote_info.__class__.__name__}")  # noqa: TRY301
    except Exception as e:  # noqa: BLE001
        err_msg = str(universal_simplify_exception(e))
        result = silent or messagebox.askyesno(
            "Error occurred fetching update information.",
            (
                "An error occurred while fetching the latest toolset information.\n\n"
                + err_msg
                + "\n\n"
                + "Would you like to check against the local database instead?"
            )
        )
        if not result:
            return e
        remote_info = LOCAL_PROGRAM_INFO
    return remote_info


def remoteVersionNewer(local_version: str, remote_version: str) -> bool | None:
    version_check: bool | None = None
    with suppress(Exception):
        from packaging import version

        version_check = version.parse(remote_version) > version.parse(local_version)
    if version_check is None:
        with suppress(Exception):
            from distutils.version import LooseVersion

            version_check = LooseVersion(remote_version) > LooseVersion(local_version)
    return version_check
