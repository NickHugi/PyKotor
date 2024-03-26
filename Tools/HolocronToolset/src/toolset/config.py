from __future__ import annotations

import base64
import json
import re

from contextlib import suppress
from typing import TYPE_CHECKING, Any

import requests

from PyQt5.QtWidgets import QMessageBox

from utility.error_handling import universal_simplify_exception
from utility.system.path import Path, PurePath

if TYPE_CHECKING:
    import os

LOCAL_PROGRAM_INFO: dict[str, Any] = {
    # <---JSON_START--->#{
    "currentVersion": "2.2.1b20",
    "toolsetLatestVersion": "2.1.2",
    "toolsetLatestBetaVersion": "2.2.1b20",
    "updateInfoLink": "https://api.github.com/repos/NickHugi/PyKotor/contents/Tools/HolocronToolset/src/toolset/config.py",
    "updateBetaInfoLink": "https://api.github.com/repos/NickHugi/PyKotor/contents/Tools/HolocronToolset/src/toolset/config.py?ref=bleeding-edge",
    "toolsetDownloadLink": "https://deadlystream.com/files/file/1982-holocron-toolset",
    "toolsetBetaDownloadLink": "https://mega.nz/folder/cGJDAKaa#WzsWF8LgUkM8U2FDEoeeRA",
    "toolsetDirectLinks": {
        "Darwin": {
            "32bit": [],
            "64bit": ["https://mega.nz/file/MTxwnJCS#HnGxOlMRn-u9jCVfdyUjAVnS5hwy0r8IyRb6dwIwLQ4", "https://github.com/NickHugi/PyKotor/releases/download/{tag}/HolocronToolset_Mac-x64.tar.gz"]
        },
        "Linux": {
            "32bit": [],
            "64bit": ["https://mega.nz/file/UO5wjRIL#x74llCH5G--Mls9vtkSLkzldYHSkgnqBoyZtJBhKJ8E", "https://github.com/NickHugi/PyKotor/releases/download/{tag}/HolocronToolset_Linux-x64.tar.gz"]
        },
        "Windows": {
            "32bit": ["https://mega.nz/file/4SADjRJK#0nUAwpLUkvKgNGNE8VS_6161hhN1q44ZbIfX7W14Ix0", "https://github.com/NickHugi/PyKotor/releases/download/{tag}/HolocronToolset_Windows-x86.zip"],
            "64bit": ["https://mega.nz/file/VaI3BbKJ#Ht7yS35JoVGYwZlUsbP_bMHxGLr7UttQ_1xgWnjj4bU", "https://github.com/NickHugi/PyKotor/releases/download/{tag}/HolocronToolset_Windows-x64.zip"]
        }
    },
    "toolsetBetaDirectLinks": {
        "Darwin": {
            "32bit": [],
            "64bit": ["https://mega.nz/file/MTxwnJCS#HnGxOlMRn-u9jCVfdyUjAVnS5hwy0r8IyRb6dwIwLQ4", "https://github.com/NickHugi/PyKotor/releases/download/{tag}/HolocronToolset_Mac-x64.tar.gz"]
        },
        "Linux": {
            "32bit": [],
            "64bit": ["https://mega.nz/file/UO5wjRIL#x74llCH5G--Mls9vtkSLkzldYHSkgnqBoyZtJBhKJ8E", "https://github.com/NickHugi/PyKotor/releases/download/{tag}/HolocronToolset_Linux-x64.tar.gz"]
        },
        "Windows": {
            "32bit": ["https://mega.nz/file/4SADjRJK#0nUAwpLUkvKgNGNE8VS_6161hhN1q44ZbIfX7W14Ix0", "https://github.com/NickHugi/PyKotor/releases/download/{tag}/HolocronToolset_Windows-x86.zip"],
            "64bit": ["https://mega.nz/file/VaI3BbKJ#Ht7yS35JoVGYwZlUsbP_bMHxGLr7UttQ_1xgWnjj4bU", "https://github.com/NickHugi/PyKotor/releases/download/{tag}/HolocronToolset_Windows-x64.zip"]
        }
    },
    "toolsetLatestNotes": "Fixed major bug that was causing most editors to load data incorrectly.",
    "toolsetLatestBetaNotes": "Fixed help booklet, and other various bugfixes. Update when you are able :)",
    "kits": {
        "Black Vulkar Base": {"version": 1, "id": "blackvulkar"},
        "Endar Spire": {"version": 1, "id": "endarspire"},
        "Hidden Bek Base": {"version": 1, "id": "hiddenbek"}
    },
    "help": {"version": 3}
}  #<---JSON_END--->#
CURRENT_VERSION = LOCAL_PROGRAM_INFO["currentVersion"]


def getRemoteToolsetUpdateInfo(*, useBetaChannel: bool = False, silent: bool = False) -> Exception | dict[str, Any]:
    if useBetaChannel:
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
        json_data_match = re.search(r"<---JSON_START--->\s*\#\s*(.*?)\s*\#\s*<---JSON_END--->", decoded_content_str, flags=re.DOTALL)

        if not json_data_match:
            raise ValueError(f"JSON data not found or markers are incorrect: {json_data_match}")  # noqa: TRY301
        json_str = json_data_match[1]
        remoteInfo = json.loads(json_str)
        if not isinstance(remoteInfo, dict):
            raise TypeError(f"Expected remoteInfo to be a dict, instead got type {remoteInfo.__class__.__name__}")  # noqa: TRY301
    except Exception as e:  # noqa: BLE001
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
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if result not in {QMessageBox.Yes, True}:
            return e
        remoteInfo = LOCAL_PROGRAM_INFO
    return remoteInfo


def remoteVersionNewer(localVersion: str, remoteVersion: str) -> bool | None:
    version_check: bool | None = None
    with suppress(Exception):
        from packaging import version

        version_check = version.parse(remoteVersion) > version.parse(localVersion)
    if version_check is None:
        with suppress(Exception):
            from distutils.version import LooseVersion

            version_check = LooseVersion(remoteVersion) > LooseVersion(localVersion)
    return version_check


def download_github_file(
    url_or_repo: str,
    local_path: os.PathLike | str,
    repo_path: os.PathLike | str | None = None,
    timeout: int | None = None,
):
    timeout = 180 if timeout is None else timeout
    local_path = Path(local_path).absolute()
    local_path.parent.mkdir(parents=True, exist_ok=True)

    if repo_path is not None:
        # Construct the API URL for the file in the repository
        owner, repo = PurePath(url_or_repo).parts[-2:]
        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{PurePath(repo_path).as_posix()}"

        file_info: dict[str, str] = _request_api_data(api_url)
        # Check if it's a file and get the download URL
        if file_info["type"] == "file":
            download_url = file_info["download_url"]
        else:
            msg = "The provided repo_path does not point to a file."
            raise ValueError(msg)
    else:
        # Direct URL
        download_url = url_or_repo

    # Download the file
    with requests.get(download_url, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        with local_path.open("wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def download_github_directory(
    repo: os.PathLike | str,
    local_dir: os.PathLike | str,
    repo_path: os.PathLike | str,
):
    """This method should not be used due to github's api restrictions. Use download_file to get a .zip of the folder instead."""  # noqa: D404
    repo = PurePath(repo)
    repo_path = PurePath(repo_path)
    api_url = f"https://api.github.com/repos/{repo.as_posix()}/contents/{repo_path.as_posix()}"
    data = _request_api_data(api_url)
    for item in data:
        item_path = Path(item["path"])
        local_path = item_path.relative_to("toolset")

        if item["type"] == "file":
            download_github_file(item["download_url"], Path(local_dir, local_path))
        elif item["type"] == "dir":
            download_github_directory(repo, item_path, local_path)


def download_github_directory_fallback(
    repo: os.PathLike | str,
    local_dir: os.PathLike | str,
    repo_path: os.PathLike | str,
):
    """There were two versions of this function and I can't remember which one worked."""
    repo = PurePath.pathify(repo)
    repo_path = PurePath.pathify(repo_path)
    api_url = f"https://api.github.com/repos/{repo.as_posix()}/contents/{repo_path.as_posix()}"
    data = _request_api_data(api_url)
    for item in data:
        item_path = Path(item["path"])
        local_path = item_path.relative_to("toolset")

        if item["type"] == "file":
            download_github_file(item["download_url"], local_path)
        elif item["type"] == "dir":
            download_github_directory(repo, item_path, local_path)


def _request_api_data(api_url: str) -> Any:
    response: requests.Response = requests.get(api_url, timeout=15)
    response.raise_for_status()
    return response.json()
