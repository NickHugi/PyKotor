from __future__ import annotations

import errno
import os
import platform
import shutil
import sys
import tarfile
import tempfile
import threading
import uuid
import zipfile

from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Any, Callable

from utility.error_handling import format_exception_with_variables
from utility.logger import get_first_available_logger
from utility.misc import ProcessorArchitecture
from utility.system.os_helper import ChDir, get_app_dir, get_mac_dot_app_dir, is_frozen, remove_any
from utility.system.path import Path, PurePath
from utility.updater.downloader import FileDownloader, download_mega_file_url
from utility.updater.restarter import RestartStrategy, Restarter, UpdateStrategy

if TYPE_CHECKING:
    from logging import Logger


class LibUpdate:
    """Used to update library files used by an application. This object is
    returned by pyupdater.client.Client.update_check.

    ######Args:
    """

    def __init__(
        self,
        update_urls: list[str],
        filestem: str,
        current_version: str,
        latest: str,
        progress_hooks: list[Callable[[dict[str, Any]], Any]] | None = None,
        max_download_retries: int | None = None,
        downloader: Callable | None = None,
        http_timeout=None,
        u_strategy: UpdateStrategy = UpdateStrategy.RENAME,
        r_strategy: RestartStrategy = RestartStrategy.DEFAULT,
        logger: Logger | None = None,
        version_to_tag_parser: Callable | None = None,
    ):
        # If user is using async download this will be True.
        # Future calls to an download methods will not run
        # until the current download is complete. Which will
        # set this back to False.
        self._is_downloading: bool = False
        self.version_to_tag_parser: Callable | None = version_to_tag_parser

        self.update_folder = tempfile.mkdtemp("_update", "holotoolset_")
        self.update_temp_path = Path(self.update_folder)

        # Used with the version property.
        # Returns a user friendly version string
        self._version: str = ""

        # List of urls used to look for meta data & updates
        self.update_urls: list[str] = update_urls

        # The name of the asset we are targeting.
        self.filestem: str = filestem

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
        self.u_strategy = u_strategy

        # The restart strategy to use
        self.r_strategy = r_strategy

        self.latest: str = latest

        self.archive_name = self.get_archive_name()
        self._current_app_dir: Path = get_app_dir()
        self._download_status: bool = False  # The status of the download. Once downloaded this will be True
        self.log = logger or get_first_available_logger()

    @property
    def filename(self) -> str:
        # sourcery skip: assign-if-exp, switch, use-fstring-for-concatenation
        # TODO(th3w1zard1): allow customization of this in the constructor.
        os_lookup_str = platform.system()
        if os_lookup_str == "Windows":
            return f"{self.filestem}.exe"
        if os_lookup_str == "Linux":
            return self.filestem
        if os_lookup_str == "Darwin":
            return f"{self.filestem}.app"
        raise ValueError(f"Unsupported return from platform.system() call: '{os_lookup_str}'")

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
        # TODO(th3w1zard1): Allow customization of this in the constructor.
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
        else:
            raise ValueError(f"Unsupported return from platform.system() call: '{lookup_os_name}'")

        return f"{self.filestem}_{os_short_name}-{proc_arch.get_machine_repr()}{ext}"

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
        try:
            self._extract_update()
        except OSError as err:
            self.log.debug(err, exc_info=True)
            return False
        return True

    def _download(self):
        if self.filestem is not None:
            if self._is_downloaded():  # pragma: no cover
                self._download_status = True
            else:
                self.log.debug("Starting full download")
                update_success = self._full_update()
                if update_success:
                    self._download_status = True
                    self.log.debug("Full download successful")
                else:  # pragma: no cover
                    self.log.debug("Full download failed")

        self._is_downloading = False
        return self._download_status

    def _extract_update(self):
        self.log.info("Main extraction, starting in working dir '%s'", self.update_folder)
        with ChDir(self.update_folder):
            archive_path = Path(self.get_archive_name()).absolute()
            self._recursive_extract(archive_path)

    def _recursive_extract(self, archive_path: Path):
        if not archive_path.safe_isfile():
            self.log.debug("File does not exist")
            raise FileNotFoundError(errno.ENOENT, "File does not exist", str(archive_path))
        if not os.access(str(archive_path), os.R_OK):
            raise PermissionError(errno.EACCES, "Permission denied", str(archive_path))

        self.log.debug(f"(recursive) Extracting '{archive_path}'...")  # noqa: G004
        archive_ext = archive_path.suffix.lower()
        if archive_ext in {".gz", ".bz2", ".tar"}:
            self.extract_tar(archive_path, recursive_extract=True)
        elif archive_ext == ".zip":
            self.extract_zip(archive_path, recursive_extract=True)
        else:
            raise ValueError(f"Invalid file extension: '{archive_ext}' for archive path '{archive_path}'")

    @classmethod
    def extract_tar(
        cls,
        archive_path: os.PathLike | str,
        *,
        recursive_extract: bool = False,
    ):
        log = get_first_available_logger()
        log.info("Extracting TAR/GZ/BZIP archive at path '%s'", archive_path)
        try:
            with tarfile.open(archive_path, "r:*") as tfile:
                for member in tfile.getmembers():
                    if not member.isfile():
                        continue  # Ignore directories and non-file members
                    # Sanitize and extract each file
                    member_path = PurePath(member.name).parts
                    sanitized_path = Path.cwd() / PurePath(*[p for p in member_path if p not in ("/", "..", "")])
                    sanitized_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
                    with sanitized_path.open("wb") as f:
                        extracted_member = tfile.extractfile(member)
                        if not extracted_member:
                            raise ValueError(f"Issue extracting member '{member}' ({member!r}): extractfile(member) returned None")  # noqa: TRY301
                        f.write(extracted_member.read())
                    if sanitized_path.exists():
                        log.info("Successfully extracted '%s'", sanitized_path)
                    else:
                        log.warning("Expected '%s' to exist after extraction, but it does not.", sanitized_path)
                    if not recursive_extract:
                        continue
                    if sanitized_path.suffix.lower() in {".gz", ".bz2", ".tar", ".zip"} and sanitized_path.safe_isfile():
                        cls._recursive_extract(sanitized_path)
        except Exception as err:  # pragma: no cover
            log = get_first_available_logger()
            log.debug(err, exc_info=True)
            raise ValueError(f"Error reading tar/gzip file: {archive_path}") from err

    @classmethod
    def extract_zip(
        cls,
        archive_path: os.PathLike | str,
        *,
        recursive_extract: bool = False,
    ):
        log = get_first_available_logger()
        log.info("Extracting ZIP '%s'", archive_path)
        try:
            with zipfile.ZipFile(archive_path, "r") as zfile:
                zfile.extractall()  # noqa: S202
                if not recursive_extract:
                    return
                for file_info in zfile.infolist():
                    extracted_path = Path.cwd() / file_info.filename
                    if extracted_path.exists():
                        log.info("Successfully extracted '%s'", extracted_path)
                    else:
                        log.warning("Expected '%s' to exist after extraction, but it does not.", extracted_path)
                    if extracted_path.suffix.lower() in {".gz", ".bz2", ".tar", ".zip"} and extracted_path.safe_isfile():
                        cls._recursive_extract(extracted_path)
        except Exception as err:  # pragma: no cover
            log.debug(err, exc_info=True)
            raise ValueError("Error reading zip file") from err

    def _is_downloaded(self) -> bool | None:
        """Checks if latest update is already downloaded."""
        # TODO(th3w1zard1): Compare file hashes to ensure security
        with ChDir(self.update_folder):
            return Path(self.get_archive_name()).safe_exists()

    def _full_update(self) -> bool:
        self.log.debug("Starting full update")
        result = True
        with ChDir(self.update_folder):
            self.log.debug("Downloading update...")
            archive_path = Path(self.get_archive_name()).absolute()
            parsed_url = ""
            for url in self.update_urls:
                parsed_url = url
                try:
                    if self.downloader:
                        return self.downloader(self.archive_name, parsed_url, self.progress_hooks)

                    if "mega.nz" in parsed_url.lower():
                        download_mega_file_url(parsed_url, archive_path, progress_hooks=self.progress_hooks)
                    else:
                        if "https://github.com" in parsed_url.lower():
                            tag = self.latest
                            if self.version_to_tag_parser is not None:
                                tag = self.version_to_tag_parser(tag)
                            parsed_url = parsed_url.replace("{tag}", tag)
                        fd = FileDownloader(
                            self.archive_name,
                            [parsed_url],
                            hexdigest=None,
                            verify=True,
                            progress_hooks=self.progress_hooks,
                            max_download_retries=self.max_download_retries,
                            headers=None,
                            http_timeout=self.http_timeout,
                        )
                        result = fd.download_verify_write()
                        if result:
                            self.log.debug("Download Complete")
                        else:  # pragma: no cover
                            self.log.debug("Failed To Download Latest Version")
                    if archive_path.safe_isfile():
                        break  # One of the mirrors worked successfully.
                except Exception as e:  # noqa: PERF203
                    self.log.exception()
                    print(format_exception_with_variables(e))
        #if not archive_path.safe_isfile():
            #exc = FileNotFoundError()
            #exc.filename = str(archive_path)
            #exc.strerror = "file downloader finished, but archive filepath doesn't exist."
        return bool(result and archive_path.safe_isfile())

    def cleanup(self):
        shutil.rmtree(self.update_temp_path, ignore_errors=True)


class AppUpdate(LibUpdate):  # pragma: no cover
    """Used to update an application. This object is returned by `update_check`."""

    def __init__(
        self,
        update_urls: list[str],
        filestem: str,
        current_version: str,
        latest: str,
        progress_hooks: list[Callable[[dict[str, Any]], Any]] | None = None,
        max_download_retries: int | None = None,
        downloader: Callable | None = None,
        http_timeout=None,
        u_strategy: UpdateStrategy = UpdateStrategy.RENAME,
        r_strategy: RestartStrategy = RestartStrategy.DEFAULT,
        exithook: Callable | None = None,
        version_to_tag_parser: Callable | None = None,
    ):
        super().__init__(update_urls, filestem, current_version, latest, progress_hooks, max_download_retries, downloader, http_timeout, u_strategy, r_strategy, None, version_to_tag_parser)
        self.exithook = exithook

    def extract_restart(self):
        """Will extract the update, overwrite the current binary, then restart the application using the updated binary."""
        try:
            self._extract_update()
            if os.name == "nt":
                if self.u_strategy == UpdateStrategy.RENAME:
                    self._win_rename(restart=True)
                else:
                    self._win_overwrite(restart=True)
            else:
                self._unix_overwrite()
                self._unix_restart()
        except OSError as err:
            self.log.debug(err, exc_info=True)

    def extract_overwrite(self):
        """Will extract the update then overwrite the current binary."""
        try:
            self._extract_update()
            if os.name == "nt":
                if self.u_strategy == UpdateStrategy.RENAME:
                    self._win_rename()
                else:
                    self._win_overwrite()
            else:
                self._unix_overwrite()
        except OSError as err:
            self.log.debug(err, exc_info=True)

    def _unix_overwrite(self):
        # Unix: Overwrites the running applications binary
        if platform.system() == "Darwin" and self._current_app_dir.endswith("MacOS"):
            self.log.debug("Looks like we're dealing with a Mac GUI")
            temp_dir = get_mac_dot_app_dir(self._current_app_dir)
            self._current_app_dir = temp_dir

        app_update_path = Path(self.update_folder, self.filename)
        self.log.debug("Update Location:\n%s", app_update_path.parent)
        self.log.debug("Update Name: %s", app_update_path.parent.name)

        current_app_path = Path(self._current_app_dir, self.filename)
        self.log.debug("Current App location: %s", current_app_path)

        # Remove current app to prevent errors when moving update to new location
        # if update_app is a directory, then we are updating a directory
        if app_update_path.safe_isdir():
            if current_app_path.safe_isdir():
                shutil.rmtree(str(current_app_path))
            else:
                shutil.rmtree(str(current_app_path.parent))

        if current_app_path.safe_exists():
            remove_any(current_app_path)

        self.log.debug("Moving update: %s --> %s", app_update_path, self._current_app_dir)
        shutil.move(str(current_app_path), str(self._current_app_dir))

    def _unix_restart(self):
        self.log.debug("Restarting")
        exe_name = self.filename
        current_app_path = Path(self._current_app_dir, exe_name)
        updated_app_path = Path(self.update_folder, exe_name)
        if platform.system() == "Darwin" and current_app_path.suffix.lower() == ".app":
            self.log.debug(f"Must be a .app bundle: '{current_app_path}'")  # noqa: G004
            mac_app_binary_dir = current_app_path.joinpath("Contents", "MacOS")

            # We are making an assumption here that only 1
            # executable will be in the MacOS folder.
            current_app_path = mac_app_binary_dir / self.filestem

        r = Restarter(
            current_app_path,
            updated_app_path,
            restart_strategy=self.r_strategy,
            filename=self.filestem,
            update_strategy=self.u_strategy,
            exithook=self.exithook
        )
        r.process()

    def _win_rename(self, *, restart: bool = False) -> tuple[Path, Path]:
        """This function renames the current application with a temporary name and moves the updated application into its place.

        It also handles rollback in case of failure.

        Args:
        ----
            - restart (bool): If True, the updated application will be launched after the rename process is complete. Default is False.

        Returns:
        -------
            - tuple[Path, Path]: A tuple containing the paths of the old application and the current application after the rename process is complete.

        Processing Logic:
        ----------------
            - Checks if the current application path is a directory and raises an error if it is.
            - Renames the current application with a temporary name.
            - Checks if the updated application is a file and raises an error if it is not.
            - Removes the old application from previous updates.
            - Renames the updated application to the current application name.
            - Hides the old application.
            - Launches the updated application if restart is True.
            - Handles rollback in case of failure.
        """
        exe_name = self.filename
        cur_app_filepath = self._current_app_dir / exe_name
        if cur_app_filepath.safe_isdir():
            raise ValueError(f"Current app path '{cur_app_filepath}' cannot be a directory!")

        old_exe_name = f"{exe_name}.old"
        old_app_path = self._current_app_dir / old_exe_name
        updated_app_filepath = self.update_temp_path.joinpath(exe_name)

        # Ensure it's a file.
        if not updated_app_filepath.safe_isfile():
            self.log.warning("The rename strategy is only supported for one file bundled executables. Falling back to overwrite strategy.")
            self._win_overwrite(restart=True)

        # Remove the old app from previous updates
        try:
            if old_app_path.safe_isfile():
                old_app_path.unlink(missing_ok=True)
            elif old_app_path.safe_isdir():
                shutil.rmtree(str(old_app_path), ignore_errors=True)
            elif old_app_path.safe_exists():
                raise ValueError(f"Old app path at '{old_app_path}' was neither a file or directory, perhaps we don't have permission to check? No changes have been made.")
        except PermissionError:
            # Fallback to the good ol' rename strategy.
            randomized_old_app_path = old_app_path.add_suffix(str(uuid.uuid4()))
            old_app_path.rename(randomized_old_app_path)

        # On Windows, it's possible to rename a currently running exe file
        if is_frozen() or cur_app_filepath.safe_exists():  # exe may not exist if running from .py source
            cur_app_filepath.rename(old_app_path)

        # Any operation from here forward will require rollback on failure
        try:
            self.log.info("Rename '%s' --> '%s'", updated_app_filepath, cur_app_filepath)
            updated_app_filepath = updated_app_filepath.rename(cur_app_filepath)
        except OSError:
            self.log.exception("Failed to move updated app into position, rolling back")
            self._win_rollback_on_exception(cur_app_filepath, old_app_path)

        assert updated_app_filepath.safe_isfile()
        if is_frozen() or old_app_path.safe_isfile():  # exe may not exist if running from .py source
            try:
                # Hide the old app
                import ctypes

                ret = ctypes.windll.kernel32.SetFileAttributesW(str(old_app_path), 0x02)
                if not ret:
                    # WinError will automatically grab the relevant code and message
                    raise ctypes.WinError()
            except OSError:
                # Failed to hide file, which is fine - we can still continue
                self.log.exception("Failed to hide file")

        if not restart:
            return old_app_path, cur_app_filepath

        try:
            r = Restarter(cur_app_filepath, updated_app_filepath, restart_strategy=self.r_strategy, filename=self.filename, update_strategy=self.u_strategy, exithook=self.exithook)
            r.process()
        except OSError:
            if not is_frozen():
                raise  # nothing to roll back if working from src
            # Raised by os.execl
            self.log.exception("Failed to launch updated app, rolling back")
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
                self.log.exception("Could not unhide file in rollback process")
            self._win_rollback_on_exception(cur_app_filepath, old_app_path)
        return old_app_path, cur_app_filepath

    def _win_rollback_on_exception(
        self,
        cur_app_filepath: Path,
        old_app_path: Path,
        *,
        no_raise: bool = False,
    ):
        """Rollback strategy: move current app back into position."""
        cur_app_filepath.unlink(missing_ok=True)
        old_app_path.rename(cur_app_filepath)
        if no_raise:
            return
        # Check if there is an exception currently being handled
        # If there is an exception, re-raise it
        exc_type, _exc_value, _exc_traceback = sys.exc_info()
        if exc_type is not None:
            raise

    def _win_overwrite(self, *, restart: bool = False):
        """Moves update to current directory of running application then restarts application using new update."""
        exe_name = self.filename
        update_folder_path = Path(self.update_folder)

        # Detect if folder
        if update_folder_path.joinpath(self.filestem).safe_isdir():
            current_app_path = self._current_app_dir
            updated_app_path = update_folder_path.joinpath(self.filestem)
        else:
            current_app_path = self._current_app_dir / exe_name
            updated_app_path = Path(self.update_folder, exe_name)

        r = Restarter(
            current_app_path,
            updated_app=updated_app_path,
            restart_strategy=self.r_strategy,
            filename=self.filestem,
            update_strategy=self.u_strategy,
            exithook=self.exithook
        )
        r.process()
