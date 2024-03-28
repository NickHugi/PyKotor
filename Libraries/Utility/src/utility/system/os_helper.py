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

def kill_child_processes(
    timeout: int = 3,
):
    """Attempt to gracefully terminate and join all child processes of the given PID with a timeout.
    Forcefully terminate any child processes that do not terminate within the timeout period.
    """
    import multiprocessing
    active_children = multiprocessing.active_children()
    for child in active_children:
        # Politely ask child processes to terminate
        child.terminate()

        # Wait for the process to terminate, with a timeout
        try:
            child.join(timeout)
        except multiprocessing.TimeoutError:
            from utility.logger_util import get_root_logger
            log = get_root_logger()
            try:
                log.warning("Child process %s did not terminate in time. Forcefully terminating.", child.pid)
                # Forcefully terminate the child process if it didn't terminate in time
                if sys.platform == "win32":
                    from utility.updater.restarter import Restarter
                    sys32path = Restarter.win_get_system32_dir()
                    subprocess.run([str(sys32path / "taskkill.exe"), "/F", "/T", "/PID", str(child.pid)], check=True)  # noqa: S603
                else:
                    import signal
                    os.kill(child.pid, signal.SIGKILL)  # Use SIGKILL as a last resort
            except Exception:
                log.critical("Failed to kill process", msgbox=False)

def kill_self_pid(timeout=3):
    """Waits for a specified timeout for threads to complete.
    If threads other than the main thread are still running after the timeout,
    it forcefully terminates the process. Otherwise, exits normally.
    """
    # Wait for the timeout period to give threads a chance to finish
    time.sleep(timeout)
    from utility.logger_util import get_root_logger
    try:
        import threading
        # First, try to clean up child processes gracefully
        kill_child_processes(timeout=timeout)

        # Check for any active threads
        number_threads_remaining = len(threading.enumerate())
        if number_threads_remaining > 1:
            self_pid = os.getpid()
            # More than one thread means threads other than the main thread are still running
            get_root_logger().warning("%s threads still running. Forcefully terminating the main process pid %s.", number_threads_remaining, self_pid)
            if sys.platform == "win32":
                # Forcefully terminate the process on Windows
                from utility.updater.restarter import Restarter
                sys32path = Restarter.win_get_system32_dir()
                subprocess.run([str(sys32path / "taskkill.exe"), "/F", "/PID", str(self_pid)], check=True)  # noqa: S603
            else:
                # Send SIGKILL to the current process on Unix-like systems
                import signal
                os.kill(self_pid, signal.SIGKILL)
        else:
            # Only the main thread is running, can exit normally
            get_root_logger().debug("No additional threads running. Exiting normally.")
            sys.exit(0)
    except Exception:
        get_root_logger().exception("Exception occurred while stopping main process")
    finally:
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


def is_frozen() -> bool:
    return (
        getattr(sys, "frozen", False)
        or getattr(sys, "_MEIPASS", False)
        or tempfile.gettempdir() in sys.executable
    )

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
