from __future__ import annotations

import base64
import binascii
import codecs
import errno
import hashlib
import inspect
import json
import logging
import os
import platform
import re
import secrets
import shutil
import struct
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import uuid
import zipfile

from contextlib import suppress
from enum import Enum
from tempfile import TemporaryDirectory
from typing import Any, Callable
from urllib.parse import quote as url_quote

import certifi
import requests
import urllib3

from Crypto.Cipher import AES
from Crypto.Util import Counter
from PyQt5.QtWidgets import QMessageBox
from typing_extensions import Literal

from utility.error_handling import universal_simplify_exception
from utility.misc import ProcessorArchitecture
from utility.system.path import Path, PurePath

LOCAL_PROGRAM_INFO: dict[str, Any] = {
    # <---JSON_START--->#{
    "currentVersion": "2.2.1b19",
    "toolsetLatestVersion": "2.1.2",
    "toolsetLatestBetaVersion": "2.2.1b20",
    "updateInfoLink": "https://api.github.com/repos/NickHugi/PyKotor/contents/Tools/HolocronToolset/src/toolset/config.py",
    "updateBetaInfoLink": "https://api.github.com/repos/NickHugi/PyKotor/contents/Tools/HolocronToolset/src/toolset/config.py?ref=auto-update-toolset-t2",
    "toolsetDownloadLink": "https://deadlystream.com/files/file/1982-holocron-toolset",
    "toolsetBetaDownloadLink": "https://mega.nz/folder/cGJDAKaa#WzsWF8LgUkM8U2FDEoeeRA",
    "toolsetBetaDirectLinks": {
        "Darwin": {
            "32bit": [],
            "64bit": ["https://mega.nz/file/MTxwnJCS#HnGxOlMRn-u9jCVfdyUjAVnS5hwy0r8IyRb6dwIwLQ4"]
        },
        "Linux": {
            "32bit": [],
            "64bit": ["https://mega.nz/file/UO5wjRIL#x74llCH5G--Mls9vtkSLkzldYHSkgnqBoyZtJBhKJ8E"]
        },
        "Windows": {
            "32bit": ["https://mega.nz/file/4SADjRJK#0nUAwpLUkvKgNGNE8VS_6161hhN1q44ZbIfX7W14Ix0"],
            "64bit": ["https://mega.nz/file/VaI3BbKJ#Ht7yS35JoVGYwZlUsbP_bMHxGLr7UttQ_1xgWnjj4bU"]
        }
    },
    "toolsetLatestNotes": "Fixed major bug that was causing most editors to load data incorrectly.",
    "toolsetLatestBetaNotes": "Various bugfixes, update when you are able :)",
    "kits": {
        "Black Vulkar Base": {"version": 1, "id": "blackvulkar"},
        "Endar Spire": {"version": 1, "id": "endarspire"},
        "Hidden Bek Base": {"version": 1, "id": "hiddenbek"}
    },
    "help": {"version": 3}
}  # <---JSON_END--->#

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
        json_data_match = re.search(r"<---JSON_START--->\#(.*?)\#\s*<---JSON_END--->", decoded_content_str, flags=re.DOTALL)

        if not json_data_match:
            raise ValueError(f"JSON data not found or markers are incorrect: {json_data_match}")  # noqa: TRY301
        json_str = json_data_match.group(1)
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


log = logging.getLogger(__name__)


def _api_request(data, sequence_num: int | None = None, **kwargs):
    if sequence_num is None:
        sequence_num = secrets.randbelow(0xFFFFFFFF)
    params: dict[str, Any] = {"id": sequence_num}
    sequence_num += 1

    # if self.sid:
    #     params["sid"] = self.sid

    if kwargs:
        params.update(kwargs)

    # Ensure input data is a list
    if not isinstance(data, list):
        data = [data]

    req = requests.post("https://g.api.mega.co.nz/cs", params=params, data=json.dumps(data), timeout=160)
    json_resp = json.loads(req.text)

    # if numeric error code response
    if isinstance(json_resp, int):
        raise ConnectionRefusedError(f"Api request error: {json_resp}")
    return json_resp[0]


def a32_to_str(a) -> bytes:
    return struct.pack(">%dI" % len(a), *a)


def str_to_a32(b):
    if isinstance(b, str):
        b = codecs.latin_1_encode(b)[0]
    if len(b) % 4:
        # pad to multiple of 4
        b += b"\0" * (4 - len(b) % 4)
    return struct.unpack(">%dI" % (len(b) / 4), b)


def mpi_to_int(s) -> int:
    return int(binascii.hexlify(s[2:]), 16)


def base64_url_decode(data) -> bytes:
    data += "=="[(2 - len(data) * 3) % 4 :]
    for search, replace in (("-", "+"), ("_", "/"), (",", "")):
        data = data.replace(search, replace)
    return base64.b64decode(data)


def base64_to_a32(s):
    return str_to_a32(base64_url_decode(s))


def base64_url_encode(data) -> str:
    data = base64.b64encode(data)
    data = codecs.latin_1_decode(data)[0]
    for search, replace in (("+", "-"), ("/", "_"), ("=", "")):
        data = data.replace(search, replace)
    return data


def aes_cbc_decrypt(data, key):
    aes_cipher = AES.new(key, AES.MODE_CBC, codecs.latin_1_encode("\0" * 16)[0])
    return aes_cipher.decrypt(data)


def a32_to_base64(a) -> str:
    return base64_url_encode(a32_to_str(a))


def decrypt_attr(attr, key):
    attr = aes_cbc_decrypt(attr, a32_to_str(key))
    attr = codecs.latin_1_decode(attr)[0]
    attr = attr.rstrip("\0")
    return json.loads(attr[4:]) if attr[:6] == 'MEGA{"' else False


def get_chunks(size):
    p = 0
    s = 0x20000
    while p + s < size:
        yield (p, s)
        p += s
        if s < 0x100000:
            s += 0x20000
    yield (p, size - p)


def _download_file(
    file_handle: str,
    file_key: str,
    dest: os.PathLike | str | None = None,
    dest_filename: str | None = None,
    is_public: bool = False,
    file=None,
):
    dest_path = Path.pathify(dest or Path.cwd()).absolute()
    if file is None:
        if is_public:
            file_key = base64_to_a32(file_key)
            file_data = _api_request({"a": "g", "g": 1, "p": file_handle})
        else:
            file_data = _api_request({"a": "g", "g": 1, "n": file_handle})

        k = (file_key[0] ^ file_key[4], file_key[1] ^ file_key[5], file_key[2] ^ file_key[6], file_key[3] ^ file_key[7])
        iv = file_key[4:6] + (0, 0)
        meta_mac = file_key[6:8]
    else:
        file_data = _api_request({"a": "g", "g": 1, "n": file["h"]})
        k = file["k"]
        iv = file["iv"]
        meta_mac = file["meta_mac"]

    # Seems to happens sometime... When  this occurs, files are
    # inaccessible also in the official also in the official web app.
    # Strangely, files can come back later.
    if "g" not in file_data:
        raise ConnectionError("File not accessible anymore")
    file_url = file_data["g"]
    file_size = file_data["s"]
    attribs = base64_url_decode(file_data["at"])
    decrypted_attribs = decrypt_attr(attribs, k)
    if decrypted_attribs is False:
        raise ValueError("Could not retrieve attribs?")

    file_name = decrypted_attribs["n"] if dest_filename is None else dest_filename
    input_file = requests.get(file_url, stream=True).raw

    temp_output_file = tempfile.NamedTemporaryFile(mode="w+b", prefix="megapy_", delete=False)

    k_str = a32_to_str(k)
    counter = Counter.new(
        128,
        initial_value=((iv[0] << 32) + iv[1]) << 64,
    )
    aes = AES.new(k_str, AES.MODE_CTR, counter=counter)

    mac_str = b"\0" * 16
    mac_encryptor = AES.new(k_str, AES.MODE_CBC, mac_str)
    iv_str = a32_to_str([iv[0], iv[1], iv[0], iv[1]])

    for _chunk_start, chunk_size in get_chunks(file_size):
        chunk = input_file.read(chunk_size)
        chunk = aes.decrypt(chunk)
        temp_output_file.write(chunk)

        encryptor = AES.new(k_str, AES.MODE_CBC, iv_str)
        for i in range(0, len(chunk) - 16, 16):
            block = chunk[i : i + 16]
            encryptor.encrypt(block)

        # Fix for files under 16 bytes failing
        if file_size > 16:
            i += 16
        else:
            i = 0

        block = chunk[i : i + 16]
        if len(block) % 16:
            block += b"\0" * (16 - (len(block) % 16))
        mac_str = mac_encryptor.encrypt(encryptor.encrypt(block))

        # Temp file size
        file_info = Path(temp_output_file.name).stat()
        log.debug(f"Status - {file_info.st_size / file_size * 100:.2f} downloaded")  # noqa: G004
        log.debug(f"{file_info.st_size} of {file_size} downloaded")  # noqa: G004

    file_mac = str_to_a32(mac_str)

    temp_output_file.close()

    # check mac integrity
    if (file_mac[0] ^ file_mac[1], file_mac[2] ^ file_mac[3]) != meta_mac:
        raise ValueError("Mismatched mac")

    if not file_name:
        file_name = dest_path.name
    if dest_path.name == file_name:
        dest_path = dest_path.parent
    dest_filepath = dest_path / file_name
    if not dest_filepath.parent.safe_isdir():
        dest_filepath.mkdir(parents=True, exist_ok=True)
    shutil.move(temp_output_file.name, dest_filepath)


def download_mega_file_url(
    url: str,
    dest_path: os.PathLike | str | None = None,
    dest_filename: str | None = None,
):
    """Download a file by it's public mega url."""
    # Splitting the URL at the first occurrence of '/file/' and '#'
    base_url, rest = url.split("/file/")
    file_id, decryption_key = rest.split("#")

    # Reconstructing the base URL to include '/file/'
    base_url = f"{base_url}/file/"

    print("Base URL:", base_url)
    print("File ID:", file_id)
    print("Decryption Key:", decryption_key)
    _download_file(file_id, decryption_key, dest_path, dest_filename, is_public=True)


def download_wrapper(filename: str, urls: list[str]):
    """Downloads a file from a list of URLs.

    Args:
    ----
        - filename (str): Name of the file to be downloaded.
        - urls (list[str]): List of URLs to download the file from.

    Processing Logic:
    ----------------
        - Downloads file from list of URLs.
        - Stops after first successful download.
        - Raises FileNotFoundError if download fails.
    """
    filepath = Path.pathify(filename).absolute()
    for url in urls:
        if "mega.nz" in url.lower():
            download_mega_file_url(url, filename)
        if filepath.safe_isfile():
            break
    if not filepath.safe_isfile():
        exc = FileNotFoundError()
        exc.filename = str(filepath)
        exc.strerror = "Downloader called but filepath doesn't exist."
    return True


def requires_admin(path: os.PathLike | str) -> bool:  # pragma: no cover
    """Check if a dir or a file requires admin permissions write/change."""
    path_obj = Path.pathify(path)
    if path_obj.safe_isdir():
        return dir_requires_admin(path)
    if path_obj.safe_isfile():
        return file_requires_admin(path)
    raise ValueError("requires_admin needs dir or file, or doesn't have permissions to determine properly...")


def file_requires_admin(file_path: os.PathLike | str) -> bool:  # pragma: no cover
    """Check if a file requires admin permissions change."""
    try:
        with Path.pathify(file_path).open("a"):
            ...
    except PermissionError:
        return True
    else:
        return False


def dir_requires_admin(_dir: os.PathLike | str) -> bool:  # pragma: no cover
    """Check if a dir required admin permissions to write.
    If dir is a file test it's directory.
    """
    _dirpath = Path.pathify(_dir)
    dummy_filepath = _dirpath / str(uuid.uuid4())
    try:
        with dummy_filepath.open("w"):
            ...
        remove_any(dummy_filepath)
    except OSError:
        return True
    else:
        return False


def remove_any(path):
    path_obj = Path.pathify(path)
    if not path_obj.safe_exists():
        return

    def _remove_any(x: Path):
        if x.safe_isdir():
            shutil.rmtree(str(x), ignore_errors=True)
        else:
            path_obj.unlink(missing_ok=True)

    if sys.platform != "win32":
        _remove_any(path_obj)
    else:
        for _ in range(100):
            try:
                _remove_any(path_obj)
            except Exception as err:  # noqa: PERF203
                log.debug(err, exc_info=True)
                time.sleep(0.01)
            else:
                break
        else:
            try:
                _remove_any(path)
            except Exception as err:
                log.debug(err, exc_info=True)


def get_mac_dot_app_dir(directory: os.PathLike | str) -> Path:
    """Returns parent directory of mac .app.

    Args:
    ----
       directory (os.PathLike | str): Current directory

    Returns:
    -------
       (Path): Folder containing the mac .app
    """
    return Path.pathify(directory).parents[2]


class ChDir:
    def __init__(self, path: os.PathLike | str):
        self.old_dir: Path = Path.cwd()
        self.new_dir: Path = Path.pathify(path)

    def __enter__(self):
        log.debug(f"Changing to Directory --> '{self.new_dir}'")  # noqa: G004
        os.chdir(self.new_dir)

    def __exit__(self, *args, **kwargs):
        log.debug(f"Moving back to Directory --> '{self.old_dir}'")  # noqa: G004
        os.chdir(self.old_dir)


class UpdateStrategy(Enum):  # pragma: no cover
    """Enum representing the update strategies available."""

    DEFAULT = "overwrite"  # The default strategy to use.  Currently is the overwrite strategy
    OVERWRITE = "overwrite"  # Overwrites the binary in place  # noqa: PIE796
    RENAME = "rename"  # Renames the binary.  Only available for Windows single file bundled executables


class CorruptedArchive(OSError): ...


class LibUpdate:
    """Used to update library files used by an application. This object is
    returned by pyupdater.client.Client.update_check.

    ######Args:
    """

    def __init__(
        self,
        update_urls: list[str],
        name: str,
        current_version: str,
        latest: str,
        progress_hooks: list[Callable[[dict[str, Any]], Any]] | None = None,
        max_download_retries: int | None = None,
        downloader: Callable | None = None,
        http_timeout=None,
        strategy: UpdateStrategy = UpdateStrategy.DEFAULT,
    ):
        # If user is using async download this will be True.
        # Future calls to an download methods will not run
        # until the current download is complete. Which will
        # set this back to False.
        self._is_downloading: bool = False

        self.update_folder = TemporaryDirectory("update", "ht")

        # Used with the version property.
        # Returns a user friendly version string
        self._version: str = ""

        # List of urls used to look for meta data & updates
        self.update_urls: list[str] = update_urls

        # The name of the asset we are targeting.
        self.name: str = name

        # The version of the current asset
        self.current_version = current_version

        # Progress callbacks
        self.progress_hooks = progress_hooks

        # The amount of times to retry a url before giving up
        self.max_download_retries = max_download_retries

        # HTTP Timeout
        self.http_timeout = http_timeout

        self.downloader = downloader

        # The update strategy to use
        self.strategy = strategy

        self.latest: str = latest

        self.archive_name = self.get_archive_name()
        self._current_app_dir: Path = Path(sys.executable).absolute().parent
        self._download_status: bool = False  # The status of the download. Once downloaded this will be True

        # TODO(th3w1zard1): Used to remove version earlier than the current.
        self.cleanup()

    @property
    def filename(self) -> str:
        # sourcery skip: assign-if-exp, switch, use-fstring-for-concatenation
        os_lookup_str = platform.system()
        if os_lookup_str == "Windows":
            return self.name + ".exe"
        if os_lookup_str == "Linux":
            return self.name
        if os_lookup_str == "Darwin":
            return self.name + ".app"
        return self.name

    @property
    def version(self) -> str:
        """Generates a user friendly version string.

        ######Returns (str): User friendly version string
        """
        if not self._version:
            self._version = self.latest
        channel = {0: "Alpha", 1: "Beta"}
        v = list(map(int, self._version.split(".")))

        # 1.2
        version = f"{v[0]}.{v[1]}"
        if v[2] != 0:
            # 1.2.1
            version += f".{v[2]}"
        if v[3] != 2:
            # 1.2.1 Alpha
            version += f" {channel[v[3]]}"
            if v[4] != 0:
                version += f" {v[4]}"
        return self._version

    def get_archive_name(self) -> str:
        proc_arch = ProcessorArchitecture.from_python()
        assert proc_arch == ProcessorArchitecture.from_os()
        os_short_name: str = ""
        lookup_os_name = platform.system()
        if lookup_os_name == "Windows":
            os_short_name = "Win"
            ext = ".zip"
        elif lookup_os_name == "Linux":
            os_short_name = "Linux"
            ext = ".tar.gz"
        elif lookup_os_name == "Darwin":
            os_short_name = "Mac"
            ext = ".tar.gz"

        return f"{self.name}_{os_short_name}_{proc_arch.get_machine_repr()}{ext}"

    def is_downloaded(self) -> bool | None:
        """Used to check if update has been downloaded.

        ######Returns (bool):
            True - File is already downloaded.
            False - File has not been downloaded.
        """
        return False if self._is_downloading else self._is_downloaded()

    def download(self, *, background: bool = False) -> bool | None:
        """Downloads update.

        ######Args:

            background (bool): Perform download in background thread
        """
        if background:
            if not self._is_downloading:
                self._is_downloading = True
                threading.Thread(target=self._download).start()
        elif not self._is_downloading:
            self._is_downloading = True
            return self._download()
        return None

    def extract(self) -> bool:
        """Will extract the update from its archive to the update folder.
        If updating a lib you can take over from there. If updating
        an app this call should be followed by method "restart" to
        complete update.

        ######Returns:
            (bool)
                True - Extract successful.
                False - Extract failed.
        """
        if platform.system() == "Windows":
            log.debug("Only supported on Unix like systems")
            return False
        try:
            self._extract_update()
        except OSError as err:
            log.debug(err, exc_info=True)
            return False
        return True

    def _download(self):
        if self.name is not None:
            if self._is_downloaded():  # pragma: no cover
                self._download_status = True
            else:
                log.debug("Starting full download")
                update_success = self._full_update()
                if update_success:
                    self._download_status = True
                    log.debug("Full download successful")
                else:  # pragma: no cover
                    log.debug("Full download failed")

        self._is_downloading = False
        return self._download_status

    def _extract_update(self):
        with ChDir(self.update_folder.name):
            archive_path = Path(self.get_archive_name()).absolute()
            if not archive_path.safe_exists():
                log.debug("File does not exists")
                raise FileNotFoundError(errno.ENOENT, "File does not exist", str(archive_path))
            if not archive_path.gain_access():
                raise PermissionError(errno.EACCES, "Permission denied", str(archive_path))

            log.debug("Extracting Update")
            archive_ext = archive_path.suffix.lower()

            if archive_ext in [".gz", ".bz2"]:
                try:
                    mode = f"r:{archive_ext[1:]}"
                    with tarfile.open(str(archive_path), mode) as tfile:
                        # Extract file update to current directory.
                        tfile.extractall()
                except Exception as err:  # pragma: no cover
                    log.debug(err, exc_info=True)
                    raise ValueError("Error reading gzip file") from err
            elif archive_ext == ".zip":
                try:
                    with zipfile.ZipFile(str(archive_path), "r") as zfile:
                        # Extract update file to current directory.
                        zfile.extractall()
                except Exception as err:  # pragma: no cover
                    log.debug(err, exc_info=True)
                    raise ValueError("Error reading zip file") from err
            else:
                raise ValueError("Unknown file type")

    # Checks if latest update is already downloaded
    def _is_downloaded(self) -> bool | None:
        # Comparing file hashes to ensure security
        with ChDir(self.update_folder.name):
            return Path(self.get_archive_name()).safe_exists()

    def _full_update(self) -> bool:
        log.debug("Starting full update")
        with ChDir(self.update_folder.name):
            log.debug("Downloading update...")
            if self.downloader:
                return self.downloader(self.archive_name, self.update_urls)

            fd = FileDownloader(
                self.archive_name,
                self.update_urls,
                hexdigest=None,
                verify=True,
                progress_hooks=self.progress_hooks,
                max_download_retries=self.max_download_retries,
                headers=None,
                http_timeout=self.http_timeout,
            )
            result = fd.download_verify_write()
            if result:
                log.debug("Download Complete")
            else:  # pragma: no cover
                log.debug("Failed To Download Latest Version")
            return bool(result)

    def cleanup(self):
        self.update_folder.cleanup()


class AppUpdate(LibUpdate):  # pragma: no cover
    """Used to update an application. This object is returned by
    pyupdater.client.Client.update_check.
    """

    def __init__(
        self,
        update_urls: list[str],
        name: str,
        current_version: str,
        latest: str,
        progress_hooks: list[Callable[[dict[str, Any]], Any]] | None = None,
        max_download_retries: int | None = None,
        downloader: Callable | None = None,
        http_timeout=None,
        strategy: UpdateStrategy = UpdateStrategy.DEFAULT,
    ):
        self._is_win = os.name == "nt"
        super().__init__(
            update_urls,
            name,
            current_version,
            latest,
            progress_hooks,
            max_download_retries,
            downloader,
            http_timeout,
            strategy,
        )

    def extract_restart(self):
        """Will extract the update, overwrite the current binary, then restart the application using the updated binary."""
        try:
            self._extract_update()
            if self._is_win:
                if self.strategy == UpdateStrategy.RENAME:
                    self._win_rename(restart=True)
                else:
                    self._win_overwrite(restart=True)
            else:
                self._overwrite()
                self._restart()
        except OSError as err:
            log.debug(err, exc_info=True)

    def extract_overwrite(self):
        """Will extract the update then overwrite the current binary."""
        try:
            self._extract_update()
            if self._is_win:
                if self.strategy == UpdateStrategy.RENAME:
                    self._win_rename()
                else:
                    self._win_overwrite()
            else:
                self._overwrite()
        except OSError as err:
            log.debug(err, exc_info=True)

    def _overwrite(self):
        # Unix: Overwrites the running applications binary
        if platform.system() == "Darwin" and self._current_app_dir.endswith("MacOS"):
            log.debug("Looks like we're dealing with a Mac Gui")
            temp_dir = get_mac_dot_app_dir(self._current_app_dir)
            self._current_app_dir = temp_dir

        app_update_path = Path(self.update_folder.name, self.filename)
        log.debug("Update Location:\n%s", app_update_path.parent)
        log.debug("Update Name: %s", app_update_path.parent.name)

        current_app_path = Path(self._current_app_dir, self.filename)
        log.debug("Current App location:\n\n%s", current_app_path)

        # Remove current app to prevent errors when moving update to new location
        # if update_app is a directory, then we are updating a directory
        if app_update_path.safe_isdir():
            if current_app_path.safe_isdir():
                shutil.rmtree(current_app_path)
            else:
                shutil.rmtree(str(current_app_path.parent))

        if current_app_path.safe_exists():
            remove_any(current_app_path)

        log.debug("Moving app to new location:\n\n%s", self._current_app_dir)
        shutil.move(str(current_app_path), self._current_app_dir)

    def _restart(self):
        log.debug("Restarting")
        current_app_path = Path(self._current_app_dir, self.filename)
        if platform.system() == "Darwin" and current_app_path.suffix.lower() == ".app":
            log.debug(f"Must be a .app bundle: '{current_app_path}'")  # noqa: G004
            mac_app_binary_dir = current_app_path / "Contents" / "MacOS"

            # We are making an assumption here that only 1
            # executable will be in the MacOS folder.
            current_app_path = mac_app_binary_dir / sys.executable

        r = Restarter(current_app_path, name=self.filename)
        r.process()

    def _win_rename(self, *, restart: bool = False) -> tuple[Path, Path]:
        exe_name = self.filename
        current_app_path = self._current_app_dir / exe_name
        old_exe_name = f"{exe_name}.old"
        old_app_path = self._current_app_dir / old_exe_name
        updated_app_path = Path(self.update_folder.name, exe_name)
        update_folder_path = Path(self.update_folder.name)

        # detect if is a folder
        if update_folder_path.joinpath(exe_name).safe_exists():
            raise ValueError("The rename strategy is only supported for one file bundled executables")

        # Remove the old app from previous updates
        if old_app_path.exists():
            old_app_path.unlink(missing_ok=True)

        # On Windows, it's possible to rename a currently running exe file
        current_app_path.rename(old_app_path)

        # Any operation from here forward will require rollback on failure
        try:
            updated_app_path.rename(current_app_path)
        except OSError:
            log.exception("Failed to move updated app into position, rolling back")
            # Rollback strategy: move current app back into position
            if current_app_path.safe_exists():
                current_app_path.unlink(missing_ok=True)
            old_app_path.rename(current_app_path)
            raise

        try:
            # Hide the old app
            import ctypes

            ret = ctypes.windll.kernel32.SetFileAttributesW(str(old_app_path), 0x02)
            if not ret:
                # WinError will automatically grab the relevant code and message
                raise ctypes.WinError()
        except OSError:
            # Failed to hide file, which is fine - we can still continue
            log.exception("Failed to hide file")

        if not restart:
            return old_app_path, current_app_path

        try:
            r = Restarter(current_app_path, name=self.filename, strategy=UpdateStrategy.RENAME)
            r.process()
        except OSError:
            # Raised by os.execl
            log.exception("Failed to launch updated app, rolling back")
            # Rollback strategy: unhide old app, delete current app, move old app back
            try:
                import ctypes

                attrs = ctypes.windll.kernel32.GetFileAttributesW(str(old_app_path))
                if attrs == -1:
                    raise ctypes.WinError()
                if not ctypes.windll.kernel32.SetFileAttributesW(str(old_app_path), attrs & (~0x02)):
                    raise ctypes.WinError()
            except OSError:
                # Better to stay hidden than to just fail at this point
                log.exception("Could not unhide file in rollback process")
            # Rename does not overwrite on Windows, so will need to unlink
            current_app_path.unlink()
            # Move old app back
            old_app_path.rename(current_app_path)
            raise

        return old_app_path, current_app_path

    def _win_overwrite(self, *, restart: bool = False):
        # Windows: Moves update to current directory of running
        #                 application then restarts application using
        #                 new update.
        exe_name = self.filename
        update_folder_path = Path(self.update_folder.name)

        # detect if is a folder
        if update_folder_path.joinpath(self.name).safe_exists():
            current_app_path = self._current_app_dir
            updated_app_path = update_folder_path.joinpath(self.name)
        else:
            current_app_path = self._current_app_dir / exe_name
            updated_app_path = Path(self.update_folder.name, exe_name)

        r = Restarter(current_app_path, updated_app=updated_app_path, name=exe_name)
        r.process(win_restart=restart)


class Restarter:
    def __init__(
        self,
        current_app: os.PathLike | str,
        *,
        name: str | None = None,
        data_dir: os.PathLike | str | None = None,
        updated_app: os.PathLike | str | None = None,
        strategy: UpdateStrategy = UpdateStrategy.DEFAULT,
    ):
        self.current_app: Path = Path.pathify(current_app)
        self.name: str = name or self.current_app.stem
        self.strategy: UpdateStrategy = strategy

        log.debug("Current App: %s", self.current_app)
        self.is_win = platform.system() == "Windows"
        if self.is_win and self.strategy == UpdateStrategy.OVERWRITE:
            if not data_dir:
                raise ValueError("data_dir must be provided on Windows.")
            self.data_dir = Path.pathify(data_dir)
            self.bat_file = self.data_dir / "update.bat"
            self.vbs_file = self.data_dir / "invis.vbs"
            if not updated_app:
                raise ValueError("updated_app must be provided on Windows.")
            self.updated_app: Path = Path.pathify(updated_app)
            log.debug("Restart script dir: %s", self.data_dir)
            log.debug("Update path: %s", self.updated_app)

    def process(self, *, win_restart: bool = True):
        if self.is_win and self.strategy == UpdateStrategy.OVERWRITE:
            if win_restart:
                self._win_overwrite_restart()
            else:
                self._win_overwrite()
        else:
            self._restart()

    def _restart(self):
        os.execl(self.current_app, self.name, *sys.argv[1:])

    def _win_overwrite(self):
        is_folder = self.updated_app.safe_isdir()
        if is_folder:
            needs_admin = requires_admin(self.updated_app) or requires_admin(self.current_app)
        else:
            needs_admin = requires_admin(self.current_app)
        log.debug(f"Admin required to update={needs_admin}")  # noqa: G004
        with self.bat_file.open("w", encoding="utf-8") as bat:
            if is_folder:
                bat.write(
                    f"""
@echo off
chcp 65001
echo Updating to latest version...
ping 127.0.0.1 -n 5 -w 1000 > NUL
robocopy "{self.updated_app}" "{self.current_app}" /e /move /V /PURGE > NUL
DEL "{self.vbs_file}"
DEL "%~f0"
"""
                )
            else:
                bat.write(
                    f"""
@echo off
chcp 65001
echo Updating to latest version...
ping 127.0.0.1 -n 5 -w 1000 > NUL
move /Y "{self.updated_app}" "{self.current_app}" > NUL
DEL "{self.vbs_file}"
DEL "%~f0"
"""
                )

        self._extracted_from__win_overwrite_restart_34(needs_admin=needs_admin)

    def _win_overwrite_restart(self):
        is_folder = self.updated_app.safe_isdir()
        if is_folder:
            needs_admin = requires_admin(self.updated_app) or requires_admin(self.current_app)
        else:
            needs_admin = requires_admin(self.current_app)
        log.debug(f"Admin required to update={needs_admin}")  # noqa: G004
        with self.bat_file.open("w", encoding="utf-8") as bat:
            if is_folder:
                bat.write(
                    f"""
@echo off
chcp 65001
echo Updating to latest version...
ping 127.0.0.1 -n 5 -w 1000 > NUL
robocopy "{self.updated_app}" "{self.current_app}" /e /move /V > NUL
echo restarting...
start "" "{Path(self.current_app, f"{self.name}.exe")}"
DEL "{self.vbs_file}"
DEL "%~f0"
"""
                )
            else:
                bat.write(
                    f"""
@echo off
chcp 65001
echo Updating to latest version...
ping 127.0.0.1 -n 5 -w 1000 > NUL
move /Y "{self.updated_app}" "{self.current_app}" > NUL
echo restarting...
start "" "{self.current_app}"
DEL "{self.vbs_file}"
DEL "%~f0"
"""
                )
        self._extracted_from__win_overwrite_restart_34(needs_admin=needs_admin)

    # TODO Rename this here and in `_win_overwrite` and `_win_overwrite_restart`
    def _extracted_from__win_overwrite_restart_34(self, *, needs_admin: bool):
        with self.vbs_file.open("w", encoding="utf-8") as vbs:
            vbs.write('CreateObject("Wscript.Shell").Run """" & WScript.Arguments(0) & """", 0, False')
        log.debug("Starting update batch file")
        win_run(
            "wscript.exe",
            [str(self.vbs_file), str(self.bat_file)],
            admin=needs_admin,
        )
        os._exit(0)


def win_run(command: str, args: list[str], *, admin: bool = False):  # pragma: no cover
    """In windows run a command, optionally as admin."""
    if admin:
        import win32con  # type: ignore[reportMissingModuleSource, import-untyped]

        from win32com.shell import shellcon  # type: ignore[reportMissingModuleSource, import-untyped]
        from win32com.shell.shell import ShellExecuteEx  # type: ignore[reportMissingModuleSource, import-untyped]

        ShellExecuteEx(
            nShow=win32con.SW_SHOWNORMAL,
            fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
            lpVerb="runas",
            lpFile=command,
            lpParameters=" ".join(f'"{arg}"' for arg in args),
        )
    else:
        subprocess.Popen([command, *args])  # noqa: S603


class FileDownloaderError(ConnectionError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class FileDownloader:
    """The FileDownloader object downloads files to memory and
    verifies their hash.  If hash is verified data is either
    written to disk to returned to calling object.

    Args:
    ----
        filename (os.PathLike | str): The name of file to download
        urls (list): List of urls to use for file download
        hexdigest (str): The hash of the file to download
    Kwargs:
    ------
        headers (str):
        hexdigest (str): The hash of the file to download
        max_download_retries (int): Maximum number of times to attempt to download the file. Defaults to zero.
        http_timeout: Unknown but defaults to None.
        progress_hooks: Unknown but should be a list if provided.
        verify (bool):
            True: Verify https connection
            False: Do not verify https connection
    """

    def __init__(
        self,
        filename: os.PathLike | str,
        urls: list[str],
        hexdigest: str | None,
        *,
        progress_hooks: list[Callable[[dict[str, Any]], Any]] | None = None,
        headers: dict | None = None,
        max_download_retries: int | None = None,
        verify: bool = True,
        http_timeout=None,
    ):
        # We'll append the filename to one of the provided urls
        # to create the download link
        if not filename:
            raise FileDownloaderError("No filename provided", expected=True)
        self.filepath = Path.pathify(filename)

        self.file_binary_data: list = []  # Hold all binary data once file has been downloaded
        self.file_binary_path: Path = self.filepath.add_suffix(".part")  # Temporary file to hold large download data

        if not urls:
            raise FileDownloaderError("No urls provided", expected=True)
        if not isinstance(urls, list):  # User may have accidentally passed a string to the urls parameter
            raise FileDownloaderError("Must pass list of urls", expected=True)
        self.urls: list[str] = urls

        self.hexdigest = hexdigest
        self.verify = verify  # Specify if we want to verify TLS connections
        self.max_download_retries: int = max_download_retries or 0  # Max attempts to download resource
        self.progress_hooks: list[Callable[[dict[str, Any]], Any]] = progress_hooks or []  # Progress hooks to be called
        self.block_size: int = 4096 * 4  # Initial block size for each read
        self.file_binary_type: Literal["memory", "file"] = "memory"  # Storage type

        # Extra headers
        self.headers: dict = headers or {}
        self.http_timeout = http_timeout
        self.download_max_size: int = (
            16 * 1024 * 1024
        )  # Max size of download to memory, larger file will be stored to file
        self.content_length: int | None = None  # Total length of data to download.

        self.http_pool = self._get_http_pool(secure=self.verify)

    def _get_http_pool(self, *, secure=True):
        if secure:
            _http = urllib3.PoolManager(
                cert_reqs="CERT_REQUIRED",
                ca_certs=certifi.where(),
                timeout=self.http_timeout,
            )
        else:
            _http = urllib3.PoolManager(timeout=self.http_timeout)

        if self.headers:
            self._apply_custom_headers(_http)
        log.debug(f"HTTP Timeout is {self.http_timeout!s}")  # noqa: G004
        return _http

    def _apply_custom_headers(self, _http: urllib3.PoolManager):
        urllib_keys = inspect.getfullargspec(urllib3.make_headers).args
        urllib_headers = {header: value for header, value in self.headers.items() if header in urllib_keys}
        other_headers = {header: value for header, value in self.headers.items() if header not in urllib_keys}
        _headers: dict[str, str] = urllib3.make_headers(**urllib_headers)
        _headers.update(other_headers)
        if not isinstance(_http.headers, dict):
            _http.headers = dict(_http.headers)
        _http.headers.update(_headers)

    def download_verify_write(self) -> bool:
        """Downloads file then verifies against provided hash
        If hash verfies then writes data to disk.

        Returns:
             (bool):
                 True - Hashes match or no hash was given during initialization.
                 False - Hashes don't match
        """
        # Downloading data internally
        check = self._download_to_storage(check_hash=True) is not False
        if check:
            self._write_to_file()  # If no hash is passed just write the file
        else:
            del self.file_binary_data
        return check

    def download_verify_return(self):
        """Downloads file to memory, checks against provided hash
        If matched returns binary data.

        Returns:
            (data):
                Binary data - If hashes match or no hash was given during initialization.
                None - If any verification didn't pass
        """
        if self._download_to_storage(check_hash=True) is not False:
            return None
        if self.file_binary_type == "memory":
            return b"".join(self.file_binary_data) if self.file_binary_data else None
        log.warning("Downloaded file is very large, reading it into memory may crash the app")
        return self.file_binary_path.open("rb").read()

    @staticmethod
    def _best_block_size(elapsed_time: float, _bytes: float) -> int:
        new_max = min(max(_bytes * 2.0, 1.0), 4194304)  # Do not surpass 4 MB
        one_millisecond = 0.001
        if elapsed_time < one_millisecond:
            return int(new_max)
        rate = _bytes / elapsed_time
        if rate > new_max:
            return int(new_max)
        # Returns best block size for current Internet connection speed
        new_min = max(_bytes / 2.0, 1.0)
        return int(new_min) if rate < new_min else int(rate)

    def _download_to_storage(self, *, check_hash: bool = True) -> bool | None:
        data = self._create_response()

        if data is None:
            return None
        hash_ = hashlib.sha256()

        # Getting length of file to show progress
        self.content_length = FileDownloader._get_content_length(data)
        if self.content_length is None:
            log.debug("Content-Length not in headers")
            log.debug("Callbacks will not show time left or percent downloaded.")
        if self.content_length is None or self.content_length > self.download_max_size:
            log.debug("Using file as storage since the file is too large")
            self.file_binary_type = "file"
        else:
            self.file_binary_type = "memory"

        start_download = time.time()
        block = data.read(1)
        received_data = 0 + len(block)
        if self.file_binary_type == "memory":
            self.file_binary_data = [block]
        else:
            binary_file = self.file_binary_path.open("wb")
            binary_file.write(block)
        hash_.update(block)
        while 1:
            # Grabbing start time for use with best block size
            start_block = time.time()

            # Get data from connection
            block = data.read(self.block_size)

            # Grabbing end time for use with best block size
            end_block = time.time()

            if not block:
                # No more data, get out of this never ending loop!
                if self.file_binary_type == "file":
                    binary_file.close()
                break

            # Calculating the best block size for the current connection speed
            self.block_size = self._best_block_size(end_block - start_block, len(block))
            log.debug("Block size: %s", self.block_size)
            if self.file_binary_type == "memory":
                self.file_binary_data.append(block)
            else:
                binary_file.write(block)
            hash_.update(block)

            # Total data we've received so far
            received_data += len(block)

            # If content length is None we will return a static percent
            # -.-%
            percent = FileDownloader._calc_progress_percent(received_data, self.content_length)

            # If content length is None we will return a static time remaining
            # --:--
            time_left = FileDownloader._calc_eta(start_download, time.time(), self.content_length, received_data)

            status = {
                "total": self.content_length,
                "downloaded": received_data,
                "status": "downloading",
                "percent_complete": percent,
                "time": time_left,
            }

            # Call all progress hooks with status data
            self._call_progress_hooks(status)

        status = {
            "total": self.content_length,
            "downloaded": received_data,
            "status": "finished",
            "percent_complete": percent,
            "time": "00:00",
        }
        self._call_progress_hooks(status)
        log.debug("Download Complete")

        return self._check_hash(hash_) if check_hash else None

    def _check_hash(self, hash_: hashlib._Hash) -> bool | None:
        # Checks hash of downloaded file
        if self.hexdigest is None:
            log.debug("No hash to verify")
            return None  # No hash provided to check. So just return any data received
        if self.file_binary_data is None:
            log.debug("Cannot verify file hash - No Data")
            return False  # Exit quickly if we got nothing to compare.  Also I'm sure we'll get an exception trying to pass None to get hash :)
        log.debug("Checking file hash")
        log.debug("Update hash: %s", self.hexdigest)

        file_hash = hash_.hexdigest()
        if file_hash == self.hexdigest:
            log.debug("File hash verified")
            return True
        log.debug("Cannot verify file hash")
        return False

    # Calling all progress hooks
    def _call_progress_hooks(self, data: dict[str, Any]):
        log.debug(data)
        for ph in self.progress_hooks:
            try:
                ph(data)
            except Exception as err:  # noqa: PERF203
                log.debug("Exception in callback: %s", ph.__name__)
                log.debug(err, exc_info=True)

    # Creating response object to start download
    # Attempting to do some error correction for aws s3 urls
    def _create_response(self) -> urllib3.BaseHTTPResponse | None:
        data = None
        for url in self.urls:
            # Create url for resource
            file_url = url + url_quote(str(self.filepath))
            log.debug("Url for request: %s", file_url)
            try:
                data = self.http_pool.urlopen(
                    "GET",
                    file_url,
                    preload_content=False,
                    retries=self.max_download_retries,
                    decode_content=False,
                )
            except urllib3.exceptions.SSLError:
                log.debug("SSL cert not verified")
                continue
            except urllib3.exceptions.MaxRetryError:
                log.debug("MaxRetryError")
                continue
            except Exception as e:
                # Catch whatever else comes up and log it
                # to help fix other http related issues
                log.debug(str(e), exc_info=True)
            else:
                if data.status == 200:
                    break

                log.debug("Received a non-200 response %d", data.status)
                data = None
        if data is not None:
            log.debug("Resource URL: %s", file_url)
        else:
            log.debug("Could not create resource URL.")
        return data

    def _write_to_file(self):
        # Writes download data to disk
        if self.file_binary_type == "memory":
            with self.filepath.open("wb") as f:
                for block in self.file_binary_data:
                    f.write(block)
        else:
            filepath = Path.pathify(self.filepath)
            if filepath.safe_exists():
                filepath.unlink(missing_ok=True)
            self.file_binary_path.rename(self.filepath)

    @staticmethod
    def _get_content_length(
        data: urllib3.BaseHTTPResponse,
    ) -> int | None:
        content_length_lookup: str | None = data.headers.get("Content-Length")
        log.debug("Got content length of: %s", content_length_lookup)
        return int(content_length_lookup) if content_length_lookup else None

    @staticmethod
    def _calc_eta(
        start: float,
        now: float,
        total: int | None,
        current: int,
    ) -> str:
        """Calculates remaining time of download."""
        if total is None:
            return "--:--"

        diff = now - start
        one_millisecond = 0.001
        if current == 0 or diff < one_millisecond:
            return "--:--"

        rate = float(current) / diff
        eta = int((float(total) - float(current)) / rate)
        (eta_mins, eta_secs) = divmod(eta, 60)
        long_time = 99
        return "--:--" if eta_mins > long_time else "%02d:%02d" % (eta_mins, eta_secs)

    @staticmethod
    def _calc_progress_percent(
        received: float | str,
        total: int | None,
    ) -> str:
        if total is None:
            return "-.-%"
        percent = float(received) / total * 100
        return "%.1f" % percent
