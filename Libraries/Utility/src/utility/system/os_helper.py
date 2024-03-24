from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

from typing import TYPE_CHECKING

from utility.logger_util import get_root_logger
from utility.system.path import Path

if TYPE_CHECKING:
    from logging import Logger


def kill_self_pid():
    # Get the current process id
    pid = os.getpid()
    # Try to kill all child multiprocessing processes
    try:
        # Get all active child processes spawned by multiprocessing
        import multiprocessing
        active_children = multiprocessing.active_children()
        for child in active_children:
            # Send a SIGTERM signal to each child process
            if sys.platform == "win32":
                from utility.updater.restarter import Restarter
                sys32path = Restarter.win_get_system32_dir()
                subprocess.run([str(sys32path / "taskkill.exe"), "/F", "/T", "/PID", str(child.pid)], check=True)
            else:
                subprocess.run(["/bin/kill", "-TERM", str(child.pid)], check=True)

        # Now kill the main process
        if sys.platform == "win32":
            from utility.updater.restarter import Restarter
            sys32path = Restarter.win_get_system32_dir()
            subprocess.run([str(sys32path / "taskkill.exe"), "/F", "/T", "/PID", str(pid)], check=True)
        else:
            subprocess.run(["/bin/kill", "-9", str(pid)], check=True)
    except Exception:
        from utility.logger_util import get_root_logger
        log = get_root_logger()
        log.exception("Failed to kill process", msgbox=False)
    finally:
        # Forcefully exit the process
        os._exit(0)

def get_app_dir() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent
    main_module = sys.modules["__main__"]
    # Try to get the __file__ attribute that contains the path of the entry-point script.
    main_script_path = getattr(main_module, "__file__", None)
    if main_script_path is not None:
        return Path(main_script_path).resolve().parent
    # Fall back to the current working directory if the __file__ attribute was not found.
    return Path.cwd()


def is_frozen() -> bool:  # sourcery skip: assign-if-exp, boolean-if-exp-identity, reintroduce-else, remove-unnecessary-cast
    # Check for sys.frozen attribute
    if getattr(sys, "frozen", False):
        return True
    # Check if the executable is in a temp directory (common for frozen apps)
    if tempfile.gettempdir() in sys.executable:
        return True
    return False

def requires_admin(path: os.PathLike | str) -> bool:  # pragma: no cover
    """Check if a dir or a file requires admin permissions write/change."""
    path_obj = Path.pathify(path)
    if path_obj.safe_isdir():
        return dir_requires_admin(path)
    if path_obj.safe_isfile():
        return file_requires_admin(path)
    if is_frozen():
        raise ValueError("requires_admin needs dir or file, or doesn't have permissions to determine properly...")
    return False


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
    log = get_root_logger()
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
    def __init__(self, path: os.PathLike | str, logger: Logger | None = None):
        self.old_dir: Path = Path.cwd()
        self.new_dir: Path = Path.pathify(path)
        self.log = logger or get_root_logger()

    def __enter__(self):
        self.log.debug(f"Changing to Directory --> '{self.new_dir}'")  # noqa: G004
        os.chdir(self.new_dir)

    def __exit__(self, *args, **kwargs):
        self.log.debug(f"Moving back to Directory --> '{self.old_dir}'")  # noqa: G004
        os.chdir(self.old_dir)
