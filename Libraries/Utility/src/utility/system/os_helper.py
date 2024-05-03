from __future__ import annotations

import ctypes
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


def windows_get_size_on_disk(file_path: os.PathLike | str) -> int:
    # Define GetCompressedFileSizeW from the Windows API
    GetCompressedFileSizeW = ctypes.windll.kernel32.GetCompressedFileSizeW
    GetCompressedFileSizeW.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_ulong)]
    GetCompressedFileSizeW.restype = ctypes.c_ulong

    # Prepare the high-order DWORD
    filesizehigh = ctypes.c_ulong()

    # Call GetCompressedFileSizeW
    low = GetCompressedFileSizeW(str(file_path), ctypes.byref(filesizehigh))

    if low == 0xFFFFFFFF:  # Check for an error condition.
        error = ctypes.GetLastError()
        if error:
            raise ctypes.WinError(error)

    # Combine the low and high parts
    return (filesizehigh.value << 32) + low


def get_size_on_disk(
    file_path: Path,
    stat_result: os.stat_result | None = None,
) -> int:
    """Returns the size on disk of the file at file_path in bytes."""
    if os.name == "posix":
        if stat_result is None:
            stat_result = file_path.stat()
        # st_blocks are 512-byte blocks
        return stat_result.st_blocks * 512  # type: ignore[attr-defined]

    return windows_get_size_on_disk(file_path)


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
                    sys32path = win_get_system32_dir()
                    subprocess.run([str(sys32path / "taskkill.exe"), "/F", "/T", "/PID", str(child.pid)], check=True)  # noqa: S603
                else:
                    import signal
                    os.kill(child.pid, signal.SIGKILL)  # Use SIGKILL as a last resort
            except Exception:
                log.critical("Failed to kill process", exc_info=True)


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

def requires_admin(path: os.PathLike | str) -> bool:    # pragma: no cover
    """Check if a dir or a file requires admin permissions for read/write."""
    path_obj = Path.pathify(path)
    isdir_check = path_obj.safe_isdir()
    if isdir_check is True:
        return dir_requires_admin(path)
    isfile_check = path_obj.safe_isfile()
    if isfile_check:
        return file_requires_admin(path)
    return isdir_check is None or isfile_check is None


def file_requires_admin(file_path: os.PathLike | str) -> bool:  # pragma: no cover
    """Check if a file requires admin permissions for read/write."""
    try:
        with Path.pathify(file_path).open("a"):
            ...
    except PermissionError:
        return True
    else:
        return False


def dir_requires_admin(
    dirpath: os.PathLike | str,
    *,
    ignore_errors: bool = True,
) -> bool:  # pragma: no cover
    """Check if a dir required admin permissions to write.
    If dir is a file test it's directory.
    """
    _dirpath = Path.pathify(dirpath)
    dummy_filepath = _dirpath / str(uuid.uuid4())
    try:
        with dummy_filepath.open("w"):
            ...
        remove_any(dummy_filepath, ignore_errors=False, missing_ok=False)
    except OSError:
        if ignore_errors:
            return True
        raise
    else:
        return False


def remove_any(
    path: os.PathLike | str,
    *,
    ignore_errors: bool = True,
    missing_ok: bool = True
):
    path_obj = Path.pathify(path)
    isdir_func = Path.safe_isdir if ignore_errors else Path.is_dir
    exists_func = Path.safe_exists if ignore_errors else Path.exists
    if not exists_func(path_obj):
        if missing_ok:
            return
        import errno
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(path_obj))

    def _remove_any(x: Path):
        if isdir_func(x):
            shutil.rmtree(str(x), ignore_errors=ignore_errors)
        else:
            x.unlink(missing_ok=missing_ok)

    if sys.platform != "win32":
        _remove_any(path_obj)
    else:
        for i in range(100):
            try:
                _remove_any(path_obj)
            except Exception:  # noqa: PERF203, BLE001
                if not ignore_errors:
                    raise
                time.sleep(0.01)
            else:
                if not exists_func(path_obj):
                    return
                print(f"File/folder {path_obj} still exists after {i} iterations! (remove_any)", file=sys.stderr)
        if not ignore_errors:  # should raise at this point.
            _remove_any(path_obj)


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


def win_get_system32_dir() -> Path:
    import ctypes
    try:  # PyInstaller sometimes fails to import wintypes.
        ctypes.windll.kernel32.GetSystemDirectoryW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint]
        ctypes.windll.kernel32.GetSystemDirectoryW.restype = ctypes.c_uint
        # Buffer size (MAX_PATH is generally 260 as defined by Windows)
        buffer = ctypes.create_unicode_buffer(260)
        ctypes.windll.kernel32.GetSystemDirectoryW(buffer, len(buffer))
        return Path(buffer.value)
    except Exception:  # noqa: BLE001
        get_root_logger().warning("Error accessing system directory via GetSystemDirectoryW. Attempting fallback.", exc_info=True)
        buffer = ctypes.create_unicode_buffer(260)
        ctypes.windll.kernel32.GetWindowsDirectoryW(buffer, len(buffer))
        return Path(buffer.value).joinpath("system32")


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
