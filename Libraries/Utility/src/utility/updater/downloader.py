from __future__ import annotations

import hashlib
import inspect
import json
import re
import secrets
import shutil
import tempfile
import time

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

import certifi
import requests
import urllib3

from Crypto.Cipher import AES
from Crypto.Util import Counter
from loggerplus import RobustLogger

from utility.updater.crypto import (
    a32_to_str,
    base64_to_a32,
    base64_url_decode,
    decrypt_mega_attr,
    get_chunks,
    str_to_a32,
)

if TYPE_CHECKING:
    import os

    from logging import Logger

    from typing_extensions import Literal


class FileDownloaderError(ConnectionError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class FileDownloader:
    """The FileDownloader object downloads files to memory and
    verifies their hash.  If hash is verified data is either
    written to disk to returned to calling object.

    Args:
    ----
        filepath (os.PathLike | str): The filepath to download to.
        urls (list[str]): List of urls to use for file download
        hexdigest (str | None): The hash of the file to download

    Kwargs:
    ------
        progress_hooks ( list[Callable[dict[str, Any]]] ): A list of callable functions that can be used when we report the progress. Untested.
        headers: (dict[str, Any] | None): custom headers to pass
        max_download_retries (int): Maximum number of times to attempt to download the file. Defaults to zero.
        verify (bool):
            True: Verify https connection
            False: Do not verify https connection
        http_timeout: Unknown but defaults to None.
    """

    def __init__(
        self,
        filepath: os.PathLike | str,
        urls: list[str],
        hexdigest: str | None,
        *,
        progress_hooks: list[Callable[[dict[str, Any]], Any]] | None = None,
        headers: dict[str, Any] | None = None,
        max_download_retries: int | None = None,
        verify: bool = True,
        http_timeout: int | None = None,
        logger: Logger | None = None,
    ):
        # We'll append the filename to one of the provided urls
        # to create the download link
        if not filepath:
            raise FileDownloaderError("No filename provided", expected=True)
        self.filepath = Path(filepath)
        self.log = logger or RobustLogger()

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
        self.downloaded_filename: str = self.filepath.name

        # Extra headers
        self.headers: dict[str, Any] = headers or {"User-Agent": "MyAppName/1.0 (https://myappwebsite.com/)"}
        self.http_timeout = http_timeout
        self.download_max_size: int = (
            16 * 1024 * 1024
        )  # Max size of download to memory, larger file will be stored to file
        self.content_length: int | None = None  # Total length of data to download.
        self.session = requests.Session()
        self.session.headers.update(self.headers)

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
        self.log.debug(f"HTTP Timeout is {self.http_timeout!s}")  # noqa: G004
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

    def _start_hooks(self, content_length):
        for hook in self.progress_hooks:
            hook(
                {
                    "action": "starting",
                    "data": {"total": content_length}
                }
            )

    def _progress_hooks(self, just_downloaded, total):
        for hook in self.progress_hooks:
            hook(
                {
                    "action": "update_progress",
                    "data": {
                        "downloaded": just_downloaded,
                        "total": total
                    }
                }
            )

    @staticmethod
    def _get_filename_from_cd(cd):
        """Get filename from content-disposition header."""
        if not cd:
            return None
        fname = re.findall('filename="(.+)"', cd)
        return fname[0] if fname else None

    def download_verify_write(self) -> bool:
        """Downloads file then verifies against provided hash
        If hash verfies then writes data to disk.

        Returns:
             (bool):
                 True - Hashes match or no hash was given during initialization.
                 False - Hashes don't match
        """
        success: bool = False
        for url in self.urls:
            try:
                with self.session.get(url, stream=True, timeout=self.http_timeout, verify=self.verify) as r:
                    r.raise_for_status()

                    # Determine the filename from the Content-Disposition header or URL.
                    filename = self._get_filename_from_cd(r.headers.get("Content-Disposition")) or Path(url).name
                    self.downloaded_filename = filename
                    RobustLogger().info(f"Expected downloaded filename: {self.downloaded_filename}")
                    file_path = self.filepath.parent / filename
                    RobustLogger().info(f"Expected download path: {file_path}")

                    # Start the download process.
                    content_length = int(r.headers.get("Content-Length", 0))
                    self._start_hooks(content_length)
                    start_time = time.time()
                    with file_path.open("wb") as f:
                        chunk_start = 0
                        for chunk in r.iter_content(chunk_size=8192):
                            if not chunk:
                                continue
                            f.write(chunk)
                            chunk_start += len(chunk)
                            for hook in self.progress_hooks:
                                hook(
                                    {
                                        "action": "update_progress",
                                        "data": {
                                            "total": content_length,
                                            "downloaded": chunk_start,
                                            "status": "downloading",
                                            "percent_complete": self._calc_progress_percent(chunk_start, content_length),
                                            "time": self._calc_eta(start_time, time.time(), content_length, chunk_start),
                                        }
                                    }
                                )
                    success = self._check_hash()
                    if success:
                        break
            except requests.exceptions.RequestException:
                self.log.exception("Request failed")
                continue
        return success

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

    def _check_hash(self) -> bool:
        if not self.hexdigest:
            return True
        sha256 = hashlib.sha256()
        with self.filepath.open("rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest() == self.hexdigest

    def _write_to_file(self):
        # Writes download data to disk
        if self.file_binary_type == "memory":
            with self.filepath.open("wb") as f:
                for block in self.file_binary_data:
                    f.write(block)
        else:
            filepath = Path(self.filepath)
            if filepath.safe_exists():
                filepath.unlink(missing_ok=True)
            self.file_binary_path.rename(self.filepath)

    @staticmethod
    def _get_content_length(
        data,
    ) -> int | None:
        content_length_lookup: str | None = data.headers.get("Content-Length")
        log = RobustLogger()
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
        return f"{percent:.1f}"




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


def _download_file(
    file_handle: str,
    file_key: str,
    dest: os.PathLike | str | None = None,
    dest_filename: str | None = None,
    is_public: bool = False,
    file: dict[str, Any] | None = None,
    progress_hooks: list[Callable[[dict[str, Any]], Any]] | None = None,
):
    dest_path = Path(dest or Path.cwd()).absolute()
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
    decrypted_attribs = decrypt_mega_attr(attribs, k)
    if decrypted_attribs is False:
        raise ValueError("Could not retrieve attribs?")

    file_name = decrypted_attribs["n"] if dest_filename is None else dest_filename
    input_file = requests.get(file_url, stream=True, timeout=30).raw

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

    start_download = time.time()

    for chunk_start, chunk_size in get_chunks(file_size):
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

        # If content length is None we will return a static percent
        # -.-%
        percent = FileDownloader._calc_progress_percent(chunk_start, file_size)

        # If content length is None we will return a static time remaining
        # --:--
        time_left = FileDownloader._calc_eta(start_download, time.time(), file_size, chunk_start)

        status = {
            "action": "update_progress",
            "data": {
                "total": file_size,
                "downloaded": chunk_start,
                "status": "downloading",
                "percent_complete": percent,
                "time": time_left,
            }
        }

        log = RobustLogger()

        # Call all progress hooks with status data
        log.debug(status)
        if progress_hooks is not None:
            for ph in progress_hooks:
                try:
                    ph(status)
                except Exception as err:  # noqa: PERF203
                    log.exception("Exception in callback: %s", ph.__name__)
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
    if not dest_filepath.parent.is_dir():
        dest_filepath.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(temp_output_file.name, dest_filepath)


def download_mega_file_url(
    url: str,
    dest_path: os.PathLike | str | None = None,
    dest_filename: str | None = None,
    progress_hooks: list[Callable] | None = None,
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
    _download_file(file_id, decryption_key, dest_path, dest_filename, is_public=True, progress_hooks=progress_hooks)
