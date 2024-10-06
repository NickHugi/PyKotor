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

from contextlib import suppress
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Any, Callable

from loggerplus import RobustLogger

from utility.misc import ProcessorArchitecture
from utility.system.os_helper import (
    get_app_dir,
    get_mac_dot_app_dir,
    is_frozen,
    remove_any,
    win_hide_file,
)
from utility.system.path import ChDir
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
        http_timeout: int | None = None,
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

        self.archive_name = self.get_archive_names()[0]
        self._current_app_dir: Path = get_app_dir()
        self._download_status: bool = False  # The status of the download. Once downloaded this will be True
        self.log = logger or RobustLogger()

    def get_expected_filename(self) -> str:
        os_lookup_str = platform.system()
        if os_lookup_str == "Windows":
            return f"{self.filestem}.exe"
        if os_lookup_str == "Linux":
            return self.filestem
        if os_lookup_str == "Darwin":
            return f"{self.filestem}.app"
        raise ValueError(f"Unsupported return from platform.system() call: '{os_lookup_str}'")

    @property
    def filename(self) -> str:
        # sourcery skip: assign-if-exp, switch, use-fstring-for-concatenation
        # TODO(th3w1zard1): allow customization of this in the constructor.
        if is_frozen():  # The application is frozen with PyInstaller
            return Path(sys.executable).name
        return self.get_expected_filename()

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

    def get_archive_names(self) -> list[str]:
        proc_arch = ProcessorArchitecture.from_python()
        assert proc_arch == ProcessorArchitecture.from_os()

        lookup_os_name = platform.system()
        str_arch = proc_arch.get_machine_repr()
        qt_name = ""
        with suppress(Exception):
            import qtpy
            qt_name = qtpy.API_NAME
        if lookup_os_name == "Windows":
            return [
                f"{self.filestem}_Win_{str_arch}.zip",
                f"{self.filestem}_Windows_{str_arch}.zip"
                f"{self.filestem}_Windows_{qt_name}_{str_arch}.zip"
            ]
        if lookup_os_name == "Linux":
            return [
                f"{self.filestem}_Linux_{str_arch}.zip",
                f"{self.filestem}_Linux_{str_arch}.tar.gz",
                f"{self.filestem}_Linux_{str_arch}.tar.bz2",
                f"{self.filestem}_Linux_{str_arch}.tar.xz",
                f"{self.filestem}_Linux_{qt_name}_{str_arch}.zip",
                f"{self.filestem}_Linux_{qt_name}_{str_arch}.tar.gz",
                f"{self.filestem}_Linux_{qt_name}_{str_arch}.tar.bz2",
                f"{self.filestem}_Linux_{qt_name}_{str_arch}.tar.xz"
            ]
        if lookup_os_name == "Darwin":
            return [
                f"{self.filestem}_Mac_{str_arch}.tar.gz",
                f"{self.filestem}_macOS_{str_arch}.tar.gz",
                f"{self.filestem}_Mac_{str_arch}.tar.bz2",
                f"{self.filestem}_macOS_{str_arch}.tar.bz2",
                f"{self.filestem}_Mac_{str_arch}.tar.xz",
                f"{self.filestem}_macOS_{str_arch}.tar.xz",
                f"{self.filestem}_Mac_{str_arch}.zip",
                f"{self.filestem}_macOS_{str_arch}.zip",
                f"{self.filestem}_macOS_{qt_name}_{str_arch}.zip",
                f"{self.filestem}_macOS_{qt_name}_{str_arch}.tar.gz",
                f"{self.filestem}_macOS_{qt_name}_{str_arch}.tar.bz2",
                f"{self.filestem}_macOS_{qt_name}_{str_arch}.tar.xz"
            ]

        raise ValueError(f"Unexpected and unsupported OS: {lookup_os_name}")

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
                threading.Thread(target=self._download, name="LibUpdate_download_thread").start()
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

    def _download(self) -> bool:
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
            for archive_name in self.get_archive_names():
                archive_path = Path.cwd().joinpath(archive_name).absolute()
                if archive_path.is_file():
                    self.log.info("Found archive %s", archive_name)
                    break
                self.log.warning("Archive not found, attempting to find it via similar extensions")
                for ext in (".gz", ".tar", ".zip", ".bz2"):
                    test_path = archive_path.with_suffix(ext)
                    if test_path.is_file():
                        self.log.info("Found archive %s", test_path.name)
                        self._recursive_extract(test_path)
                        return
            self._recursive_extract(archive_path)

    @classmethod
    def _recursive_extract(cls, archive_path: Path):
        log = RobustLogger()
        if not archive_path.is_file():
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(archive_path))
        if not os.access(str(archive_path), os.R_OK):
            raise PermissionError(errno.EACCES, os.strerror(errno.EACCES), str(archive_path))

        log.debug(f"(recursive) Extracting '{archive_path}'...")  # noqa: G004
        archive_ext = archive_path.suffix.lower()
        if archive_ext in {".gz", ".bz2", ".tar"}:
            cls.extract_tar(archive_path, recursive_extract=True)
        elif archive_ext == ".zip":
            cls.extract_zip(archive_path, recursive_extract=True)
        else:
            raise ValueError(f"Invalid file extension: '{archive_ext}' for archive path '{archive_path}'")

    @classmethod
    def extract_tar(
        cls,
        archive_path: os.PathLike | str,
        *,
        recursive_extract: bool = False,
    ):
        log = RobustLogger()
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
                    if sanitized_path.suffix.lower() in {".gz", ".bz2", ".tar", ".zip"} and sanitized_path.is_file():
                        cls._recursive_extract(sanitized_path)
        except Exception as err:  # pragma: no cover
            log = RobustLogger()
            log.debug(err, exc_info=True)
            raise ValueError(f"Error reading tar/gzip file: {archive_path}") from err

    @classmethod
    def extract_zip(
        cls,
        archive_path: os.PathLike | str,
        *,
        recursive_extract: bool = False,
    ):
        log = RobustLogger()
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
                    if extracted_path.suffix.lower() in {".gz", ".bz2", ".tar", ".zip"} and extracted_path.is_file():
                        cls._recursive_extract(extracted_path)
        except Exception as err:  # pragma: no cover
            log.debug(err, exc_info=True)
            raise ValueError("Error reading zip file") from err

    def _is_downloaded(self) -> bool | None:
        """Checks if latest update is already downloaded."""
        # TODO(th3w1zard1): Compare file hashes to ensure security
        with ChDir(self.update_folder):
            for archive_name in self.get_archive_names():
                if Path(archive_name).is_file():
                    return True
        return False

    def _full_update(self) -> bool:
        self.log.debug("Starting full update")
        result = True
        with ChDir(self.update_folder):
            self.log.debug("Downloading update...")
            archive_path = Path(self.get_archive_names()[0]).absolute()
            parsed_url = ""
            for url in self.update_urls:
                parsed_url = url
                try:
                    if self.downloader:
                        return self.downloader(self.archive_name, parsed_url, self.progress_hooks)

                    if "mega.nz" in parsed_url.lower():
                        download_mega_file_url(parsed_url, archive_path, progress_hooks=self.progress_hooks)
                    else:
                        # HACK(th3w1zard1): use the latest tag for GitHub based downloads.
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
                            archive_path = fd.filepath.parent / fd.downloaded_filename  # TODO(th3w1zard1): loop through archive names...
                            if not archive_path.is_file():
                                self.log.error("Download complete but %s not found on disk at expected %s filepath?", fd.downloaded_filename, archive_path)
                                continue
                            if fd.downloaded_filename not in self.get_archive_names():
                                self.log.warning("Archive name %s does not exist in the archive name getter function, will override with downloaded name.", archive_path.name)
                                def getarchivename(a: Path = archive_path) -> list[str]:
                                    return [a.name]
                                self.get_archive_names = getarchivename
                        else:  # pragma: no cover
                            self.log.debug("Failed To Download Latest Version")
                    if archive_path.is_file():
                        break  # One of the mirrors worked successfully.
                except Exception:  # noqa: PERF203
                    self.log.exception("Exception while downloading %s", url)
        #if not archive_path.is_file():
            #exc = FileNotFoundError()
            #exc.filename = str(archive_path)
            #exc.strerror = "file downloader finished, but archive filepath doesn't exist."
        return bool(result and archive_path.is_file())

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
        http_timeout: int | None = None,
        u_strategy: UpdateStrategy = UpdateStrategy.RENAME,
        r_strategy: RestartStrategy = RestartStrategy.DEFAULT,
        exithook: Callable | None = None,
        version_to_tag_parser: Callable | None = None,
    ):
        super().__init__(
            update_urls,
            filestem,
            current_version,
            latest,
            progress_hooks,
            max_download_retries,
            downloader,
            http_timeout,
            u_strategy,
            r_strategy,
            None,
            version_to_tag_parser,
        )
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
        if platform.system() == "Darwin" and self._current_app_dir.name.endswith("MacOS"):
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
        if app_update_path.is_dir():
            if current_app_path.is_dir():
                shutil.rmtree(str(current_app_path))
            else:
                current_app_path.unlink()

        remove_any(current_app_path)

        self.log.info("Moving update: %s --> %s", app_update_path, self._current_app_dir)
        shutil.move(str(app_update_path), str(current_app_path))

    def _unix_restart(self):
        self.log.debug("Restarting %s", self.filename)
        current_app_path = Path(self._current_app_dir, self.filename)
        if platform.system() == "Darwin" and current_app_path.suffix.lower() == ".app":
            self.log.debug(f"Must be a .app bundle: '{current_app_path}'")  # noqa: G004
            mac_app_binary_dir = current_app_path.joinpath("Contents", "MacOS")

            # We are making an assumption here that only 1
            # executable will be in the MacOS folder.
            current_app_path = mac_app_binary_dir / self.filestem

        r = Restarter(
            current_app_path,
            current_app_path,
            restart_strategy=self.r_strategy,
            filename=self.filestem,
            update_strategy=self.u_strategy,
            exithook=self.exithook,
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
        if cur_app_filepath.is_dir():
            raise ValueError(f"Current app path '{cur_app_filepath}' cannot be a directory!")

        old_app_path = self._current_app_dir / f"{exe_name}.old"
        temp_app_filepath = self.update_temp_path.joinpath(exe_name)

        # Ensure it's a file.
        if not temp_app_filepath.is_file():
            # Detect if archive expanded some folder with the same name as the archive.
            # This assumes all dots in the archive filename are extensions of the file archive.
            temp_app_filepath = temp_app_filepath.parent
            for archive_name in self.get_archive_names():
                archive_stem = archive_name[:archive_name.find(".")]
                check_path = temp_app_filepath.joinpath(archive_stem, exe_name)
                if check_path.is_file():
                    temp_app_filepath = check_path
                    break
            if temp_app_filepath.is_dir():
                self.log.warning("The rename strategy is only supported for one file bundled executables. Falling back to overwrite strategy.")
                self._win_overwrite(restart=True)
            elif not temp_app_filepath.safe_exists():
                self.log.error("Updated app filepath: %s not found", temp_app_filepath)


        # Remove the old app from previous updates
        try:
            if old_app_path.is_file():
                old_app_path.unlink(missing_ok=True)
            elif old_app_path.is_dir():
                shutil.rmtree(str(old_app_path), ignore_errors=True)
            elif old_app_path.safe_exists():
                raise ValueError(f"Old app path at '{old_app_path}' was neither a file or directory, perhaps we don't have permission to check? No changes have been made.")
        except PermissionError:
            # Fallback to the good ol' rename strategy.
            randomized_old_app_path = old_app_path.add_suffix(uuid.uuid4().hex[:7])
            old_app_path.rename(randomized_old_app_path)

        # On Windows, it's possible to rename a currently running exe file
        if is_frozen() or cur_app_filepath.safe_exists():  # exe may not exist if running from .py source
            cur_app_filepath.rename(old_app_path)

        # Any operation from here forward will require rollback on failure
        try:
            self.log.info("Copy '%s' --> '%s'", temp_app_filepath, cur_app_filepath)
            shutil.copy(str(temp_app_filepath), str(cur_app_filepath))
        except OSError:
            self.log.exception("Failed to move updated app into position, rolling back")
            self._win_rollback_on_exception(cur_app_filepath, old_app_path)

        assert temp_app_filepath.is_file()
        if is_frozen() or old_app_path.is_file():  # exe may not exist if running from .py source
            try:
                win_hide_file(old_app_path)
            except OSError:
                self.log.info("Failed to hide file. This is fine - we can still continue", exc_info=True)

        if not restart:
            return old_app_path, cur_app_filepath

        try:
            r = Restarter(cur_app_filepath, temp_app_filepath, restart_strategy=self.r_strategy, filename=self.filename,
                          update_strategy=self.u_strategy, exithook=self.exithook)
            r.process()
        except OSError as e:
            if not is_frozen():
                raise  # nothing to roll back if working from src
            # Raised by os.execl
            self.log.exception("Failed to launch updated app, rolling back")
            # Rollback strategy: unhide old app, delete current app, move old app back
            try:
                import ctypes

                attrs = ctypes.windll.kernel32.GetFileAttributesW(str(old_app_path))
                if attrs == -1:
                    raise ctypes.WinError() from e
                if not ctypes.windll.kernel32.SetFileAttributesW(str(old_app_path), attrs & (~0x02)):
                    raise ctypes.WinError() from e
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
        exc_type, exc_value, _exc_traceback = sys.exc_info()
        if exc_type is not None and exc_value is not None:
            raise exc_value

    def _win_overwrite(self, *, restart: bool = False):
        """Moves update to current directory of running application then restarts application using new update."""
        update_folder_path = Path(self.update_folder)
        current_app_path = self._current_app_dir / self.filename
        archive_stem = self.archive_name[:self.archive_name.find(".")]

        # TODO(th3w1zard1): clean this up... i'm ashamed.
        check_path1 = update_folder_path.joinpath(archive_stem)
        check_path2 = update_folder_path.joinpath(archive_stem.replace("_Win-", "_Windows_"))

        # Detect if archive expanded some folder with the same name as the archive.
        # This assumes all dots in the archive filename are extensions of the file archive.
        if check_path1.is_dir():
            updated_app_path = check_path1
        elif check_path2.is_dir():
            updated_app_path = check_path2
        else:
            updated_app_path = Path(self.update_folder, self.get_expected_filename())

        r = Restarter(
            current_app_path,
            updated_app=updated_app_path,
            restart_strategy=self.r_strategy,
            filename=self.filestem,
            update_strategy=self.u_strategy,
            exithook=self.exithook,
        )
        r.process()
