from __future__ import annotations

import hashlib
import inspect
import json
import secrets
import shutil
import tempfile
import time

from typing import TYPE_CHECKING, Any, Callable
from urllib.parse import quote as url_quote

import certifi
import requests
import urllib3

from Crypto.Cipher import AES
from Crypto.Util import Counter
from typing_extensions import Literal

from utility.logger import get_first_available_logger
from utility.system.path import Path
from utility.updater.crypto import a32_to_str, base64_to_a32, base64_url_decode, decrypt_mega_attr, get_chunks, str_to_a32

if TYPE_CHECKING:
    import os

    from logging import Logger


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
        urls (list[str]): List of urls to use for file download
        hexdigest (str | None): The hash of the file to download

    Kwargs:
    ------
        progress_hooks ( list[Callable[dict[str, Any]]] ): A list of callable functions that can be used when we report the progress. Untested.
        headers (dict | None): Unknown
        max_download_retries (int): Maximum number of times to attempt to download the file. Defaults to zero.
        verify (bool):
            True: Verify https connection
            False: Do not verify https connection
        http_timeout: Unknown but defaults to None.
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
        logger: Logger | None = None,
    ):
        # We'll append the filename to one of the provided urls
        # to create the download link
        if not filename:
            raise FileDownloaderError("No filename provided", expected=True)
        self.filepath = Path.pathify(filename)
        self.log = logger or get_first_available_logger()

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
        self.log.warning("Downloaded file is very large, reading it into memory may crash the app")
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
            self.log.debug("Content-Length not in headers")
            self.log.debug("Callbacks will not show time left or percent downloaded.")
        if self.content_length is None or self.content_length > self.download_max_size:
            self.log.debug("Using file as storage since the file is too large")
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
        while True:
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
            self.log.debug("Block size: %s", self.block_size)
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
        self.log.debug("Download Complete")

        return self._check_hash(hash_) if check_hash else None

    # Calling all progress hooks
    def _call_progress_hooks(self, data: dict[str, Any]):
        self.log.debug(data)
        for ph in self.progress_hooks:
            try:
                ph(data)
            except Exception as err:  # noqa: PERF203
                self.log.debug("Exception in callback: %s", ph.__name__)
                self.log.debug(err, exc_info=True)

    def _check_hash(self, hash_: hashlib._Hash) -> bool | None:
        # Checks hash of downloaded file
        if self.hexdigest is None:
            self.log.debug("No hash to verify")
            return None  # No hash provided to check. So just return any data received
        if self.file_binary_data is None:
            self.log.debug("Cannot verify file hash - No Data")
            return False  # Exit quickly if we got nothing to compare.  Also I'm sure we'll get an exception trying to pass None to get hash :)
        self.log.debug("Checking file hash")
        self.log.debug("Update hash: %s", self.hexdigest)

        file_hash = hash_.hexdigest()
        if file_hash == self.hexdigest:
            self.log.debug("File hash verified")
            return True
        self.log.debug("Cannot verify file hash")
        return False

    # Creating response object to start download
    # Attempting to do some error correction for aws s3 urls
    def _create_response(self) -> urllib3.BaseHTTPResponse | None:
        data = None
        for url in self.urls:
            # Create url for resource
            file_url = url + url_quote(str(self.filepath))
            self.log.debug("Url for request: %s", file_url)
            try:
                data = self.http_pool.urlopen(
                    "GET",
                    file_url,
                    preload_content=False,
                    retries=self.max_download_retries,
                    decode_content=False,
                )
            except urllib3.exceptions.SSLError:
                self.log.debug("SSL cert not verified")
                continue
            except urllib3.exceptions.MaxRetryError:
                self.log.debug("MaxRetryError")
                continue
            except Exception as e:
                # Catch whatever else comes up and log it
                # to help fix other http related issues
                self.log.debug(str(e), exc_info=True)
            else:
                if data.status == 200:
                    break

                self.log.debug("Received a non-200 response %d", data.status)
                data = None
        if data is not None:
            self.log.debug("Resource URL: %s", file_url)
        else:
            self.log.debug("Could not create resource URL.")
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
        log = get_first_available_logger()
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
    file=None,
    progress_hooks: list[Callable[[dict[str, Any]], Any]] | None = None,
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
    decrypted_attribs = decrypt_mega_attr(attribs, k)
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
            "total": file_size,
            "downloaded": chunk_start,
            "status": "downloading",
            "percent_complete": percent,
            "time": time_left,
        }

        log = get_first_available_logger()

        # Call all progress hooks with status data
        log.debug(status)
        if progress_hooks is not None:
            for ph in progress_hooks:
                try:
                    ph(status)
                except Exception as err:  # noqa: PERF203
                    log.debug("Exception in callback: %s", ph.__name__)
                    log.debug(err, exc_info=True)
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