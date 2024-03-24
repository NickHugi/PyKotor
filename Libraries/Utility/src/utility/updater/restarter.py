from __future__ import annotations

import os
import subprocess
import sys
import time

from enum import Enum
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Callable

from utility.logger import get_first_available_logger
from utility.system.os_helper import is_frozen, requires_admin
from utility.system.path import Path

if TYPE_CHECKING:
    from logging import Logger


class UpdateStrategy(Enum):  # pragma: no cover
    """Enum representing the update strategies available."""

    OVERWRITE = "overwrite"  # Overwrites the binary in place
    RENAME = "rename"  # Renames the binary.  Only available for Windows single file bundled executables

class RestartStrategy(Enum):
    DEFAULT = "default"
    BATCH = "batch"
    EXEC1 = "exec1"

class Restarter:
    def __init__(
        self,
        current_app: os.PathLike | str,
        updated_app: os.PathLike | str,
        *,
        filename: str | None = None,
        update_strategy: UpdateStrategy = UpdateStrategy.RENAME,
        restart_strategy: RestartStrategy = RestartStrategy.DEFAULT,
        exithook: Callable | None = None,
        logger: Logger | None = None,
    ):
        self.log = logger or get_first_available_logger()
        self.current_app: Path = Path.pathify(current_app)
        self.log.debug("Current App: %s resolved to %s", current_app, self.current_app)
        if is_frozen() and not self.current_app.safe_exists():
            raise ValueError(f"Bad path to current_app provided to Restarter: '{self.current_app}'")

        self.filename: str = self.current_app.name if filename is None else filename
        self.u_strategy: UpdateStrategy = update_strategy
        self.r_strategy: RestartStrategy = restart_strategy

        self.data_dir = TemporaryDirectory("_restarter", "holotoolset_")
        data_dirpath = Path(self.data_dir.name)
        self.exithook = exithook
        self.updated_app: Path = Path.pathify(updated_app)
        self.log.debug("Update path: %s", self.updated_app)
        assert self.updated_app.exists()
        if os.name == "nt": # and self.strategy == UpdateStrategy.OVERWRITE:
            self.bat_file = data_dirpath / "update.bat"
            self.log.debug("Restart script dir: %s", self.data_dir)

    def cleanup(self):
        self.data_dir.cleanup()

    def process(self):
        self.log.info("Restarter.process() called")
        if os.name == "nt":
            if self.current_app == self.updated_app:
                self.log.warning("Current app and updated app path are exactly the same, I guess they only wanted us to restart? path: %s", self.current_app)
            if self.u_strategy == UpdateStrategy.OVERWRITE:
                self._win_overwrite()
            if self.r_strategy == RestartStrategy.DEFAULT:
                if is_frozen():
                    self._join()
                else:
                    self._win_restart()
            elif self.r_strategy == RestartStrategy.BATCH:
                self._win_restart()
            elif self.r_strategy == RestartStrategy.EXEC1:
                self._join()
            return

        self._join()
        if self.u_strategy == UpdateStrategy.OVERWRITE:
            return  # TODO: maybe?

    def _win_restart(self):
        self.log.debug("Starting updated app at '%s'...", self.current_app)
        cmd_exe_path = str(self.win_get_system32_dir() / "cmd.exe")
        run_script_cmd: list[str] = [cmd_exe_path, "/C", "start", "", f"{self.current_app}"]
        flags = 0
        flags |= 0x00000008  # DETACHED_PROCESS
        flags |= 0x00000200  # CREATE_NEW_PROCESS_GROUP
        flags |= 0x08000000  # CREATE_NO_WINDOW
        subprocess.Popen(
            run_script_cmd,
            text=True,
            #capture_output=True,
            #check=True,
            close_fds=True,
            start_new_session=True,
            creationflags=flags,
        )
        time.sleep(5)
        #self.log.debug(
        #    "Result from simple restart 'start' subprocess.run call: Stdout: %s, Stderr: %s",
        #    result.stdout,
        #    result.stderr,
        #)
        self.log.info("Finally exiting app '%s'", sys.executable)
        if self.exithook is not None:
            self.exithook(True)
        #try:
        #    self._win_kill_self()
        #finally:
            # This code might not be reached, but it's here for completeness
        #    os._exit(0)

    def _join(self):
        #if not is_frozen():
        #    self.log.warning("Cannot call os.exec1() from non-frozen executables.")
        #    return
        if self.exithook is not None:
            self.exithook(False)
        self.log.debug("Setting executable permissions on %s | %s", self.current_app, self.filename)
        self.current_app.gain_access(mode=7)
        self.log.info("Replacing current process with new app '%s' | %s", self.current_app, self.filename)
        os.execl(self.current_app, self.filename, *sys.argv[1:])

    def _win_overwrite(self):  # sourcery skip: class-extract-method
        self.log.info("Calling _win_overwrite for updated app '%s'", self.updated_app)
        is_folder = self.updated_app.safe_isdir()
        if is_folder:
            needs_admin = requires_admin(self.updated_app) or requires_admin(self.current_app)
        else:
            needs_admin = requires_admin(self.current_app)
        self.log.debug(f"Admin required to update={needs_admin}")  # noqa: G004
        with self.bat_file.open("w", encoding="utf-8") as batchfile_writer:
            if is_folder:
                batchfile_writer.write(
                    f"""
chcp 65001
echo Updating to latest version...
ping 127.0.0.1 -n 5 -w 1000 > NUL
robocopy "{self.updated_app}" "{self.current_app}" /e /move /V /PURGE
"""
                )
            else:
                batchfile_writer.write(
                    f"""
chcp 65001
echo Updating to latest version...
ping 127.0.0.1 -n 5 -w 1000 > NUL
move /Y "{self.updated_app}" "{self.current_app}"
"""
                )
        self._win_batch_mover(admin=needs_admin)

    def _win_batch_mover(self, *, admin: bool):
        self.log.info(f"Executing restart script @ {self.bat_file}")  # noqa: G004
        if admin:
            run_script_cmd: list[str] = [
                "Powershell",
                "-Command",
                f"Start-Process cmd.exe -ArgumentList '/C \"{self.bat_file}\"' -Verb RunAs -WindowStyle Hidden -Wait",
            ]
            try:
                result = subprocess.run(
                    run_script_cmd,
                #    executable=cmd_exe_path,
                    text=True,
                    capture_output=True,
                    check=False,
                #    stdout=Path.cwd().joinpath("suboutput.txt").open("a", encoding="utf-8"),
                #    stderr=Path.cwd().joinpath("suberror.txt").open("a", encoding="utf-8"),
                #    start_new_session=True,
                #    creationflags=subprocess.CREATE_NEW_CONSOLE,
                #    close_fds=True
                )
                self.log.debug("Result from admin-ran update.bat. Stdout: %s, Stderr: %s", result.stdout, result.stderr)
            except OSError:
                self.log.exception("Error running batch script")
                #self.log.debug(f"subprocess.call result: {result}")  # noqa: G004
        else:
            cmd_exe_path = str(self.win_get_system32_dir() / "cmd.exe")
            self.log.debug(f"CMD.exe path: {cmd_exe_path}")  # noqa: G004
            # Construct the command to run the batch script
            run_script_cmd: list[str] = [
                cmd_exe_path,
                "/C",
                str(self.bat_file)
            ]
            try:
                result = subprocess.run(
                    run_script_cmd,
                #    executable=cmd_exe_path,
                    text=True,
                    capture_output=True,
                    check=False,
                #    stdout=Path.cwd().joinpath("suboutput.txt").open("a", encoding="utf-8"),
                #    stderr=Path.cwd().joinpath("suberror.txt").open("a", encoding="utf-8"),
                #    start_new_session=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                #    close_fds=True
                )
                self.log.debug("Result from non-admin update.bat. Stdout: %s, Stderr: %s", result.stdout, result.stderr)
            except OSError:
                self.log.exception("Error running batch script")
                #self.log.debug(f"subprocess.call result: {result}")  # noqa: G004

    @staticmethod
    def win_get_system32_dir() -> Path:
        import ctypes

        from ctypes import wintypes

        ctypes.windll.kernel32.GetSystemDirectoryW.argtypes = [wintypes.LPWSTR, wintypes.UINT]
        ctypes.windll.kernel32.GetSystemDirectoryW.restype = wintypes.UINT
        # Buffer size (MAX_PATH is generally 260 as defined by Windows)
        buffer = ctypes.create_unicode_buffer(260)
        # Call the function
        ctypes.windll.kernel32.GetSystemDirectoryW(buffer, len(buffer))
        return Path(buffer.value)

    @classmethod
    def _win_kill_self(cls):
        taskkill_path = cls.win_get_system32_dir() / "taskkill.exe"
        if taskkill_path.safe_isfile():
            subprocess.run([str(taskkill_path), "/F", "/PID", str(os.getpid())], check=True)  # noqa: S603
        else:
            log = get_first_available_logger()
            log.warning(f"taskkill.exe not found at '{taskkill_path}', could not guarantee our process is terminated.")  # noqa: G004
        os._exit(0)
