from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
import sys
import threading
import time
import traceback
import uuid

from utility.logger_util import RobustRootLogger
from utility.system.path import Path


def is_admin() -> bool:
    try:  # sourcery skip: do-not-use-bare-except
        return ctypes.windll.shell32.IsUserAnAdmin()
    except OSError:  # noqa: E722
        print(f"An error occurred while determining user permissions:\n{traceback.format_exc()}", file=sys.stderr)
        return False


def get_size_on_disk(
    file_path: Path,
    stat_result: os.stat_result | None = None,
) -> int:
    """Get the size of a file on disk.

    Args:
    ----
        - file_path (Path): Path to the file.
        - stat_result (os.stat_result | None): A cached os.stat_result to use. If None, will grab from the file_path passed.

    Returns:
    -------
        - int: Size of the file on disk in bytes.

    Processing Logic:
    ----------------
        - Call pathlib.Path(file_path).stat() if stat_result is not passed.
        - If windows, call return result of windows_get_size_on_disk.
        - Otherwise, multiply stat_result.st_blocks by 512 to get the size in bytes.
    """
    if os.name == "posix":
        if stat_result is None:
            stat_result = file_path.stat()
        # st_blocks are 512-byte blocks
        return stat_result.st_blocks * 512  # type: ignore[attr-defined]

    # Define GetCompressedFileSizeW from the Windows API
    GetCompressedFileSizeW = ctypes.windll.kernel32.GetCompressedFileSizeW
    GetCompressedFileSizeW.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_ulong)]
    GetCompressedFileSizeW.restype = ctypes.c_ulong

    # Prepare the high-order DWORD
    filesizehigh = ctypes.c_ulong()

    # Call GetCompressedFileSizeW
    low = GetCompressedFileSizeW(str(file_path), ctypes.byref(filesizehigh))

    if low == 0xFFFFFFFF:  # Check for an error condition.  # noqa: PLR2004
        error = ctypes.GetLastError()
        if error:
            raise ctypes.WinError(error)

    # Combine the low and high parts
    return (filesizehigh.value << 32) + low


def start_shutdown_process():
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(sys.path)
    # Setup to hide the console window on Windows
    startupinfo = None
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
    else:
        main_pid = os.getpid()
        os.fork()
        shutdown_main_process(main_pid)
        return

    if is_frozen():
        import multiprocessing
        multiprocessing.Process(target=shutdown_main_process, args=(os.getpid(),))
    elif os.name == "nt":
        subprocess.Popen(
            [sys.executable, "-c", f"from utility.system.os_helper import shutdown_main_process; shutdown_main_process({os.getpid()})"],  # noqa: S603
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW, start_new_session=True, env=env, startupinfo=startupinfo
        )
    else:  # keep in case we end up needing to enable this logic later.
        subprocess.Popen(
            [sys.executable, "-c", f"from utility.system.os_helper import shutdown_main_process; shutdown_main_process({os.getpid()})"],  # noqa: S603
            start_new_session=True, env=env, startupinfo=startupinfo
        )


def shutdown_main_process(main_pid: int, *, timeout: int = 3):
    """Watchdog process to monitor and shut down the main application."""
    try:
        RobustRootLogger().debug(f"Waiting {timeout} second(s) before starting the shutdown failsafe.")
        time.sleep(timeout)
        RobustRootLogger().debug("Perform the shutdown/cleanup sequence")
        terminate_main_process(timeout, main_pid)
    except Exception:  # noqa: BLE001
        RobustRootLogger().exception("Shutdown process encountered an exception!", exc_info=True)


def terminate_child_processes(
    timeout: int = 3,
    ignored_pids: list[int] | None = None,
) -> bool:
    """Attempt to gracefully terminate and join all child processes of the given PID with a timeout.

    Forcefully terminate any child processes that do not terminate within the timeout period.
    """
    ignored_pids = [] if ignored_pids is None else ignored_pids
    import multiprocessing
    log = RobustRootLogger()
    log.info("Attempting to terminate child processes gracefully...")

    active_children = multiprocessing.active_children()
    log.debug("%s active child processes found", len(active_children))
    number_timeout_children = 0
    number_failed_children = 0
    for child in active_children:
        if child.pid in ignored_pids:
            log.debug("Ignoring pid %s, found in ignore list.", child.pid)
            continue

        log.debug("Politely ask child process %s to terminate", child.pid)
        try:
            child.terminate()
            log.debug("Waiting for process %s to terminate with timeout of %s", child.pid, timeout)
            child.join(timeout)
        except multiprocessing.TimeoutError:
            number_timeout_children += 1
            log.warning("Child process %s did not terminate in time. Forcefully terminating.", child.pid)
            try:
                if sys.platform == "win32":
                    subprocess.run([str(win_get_system32_dir() / "taskkill.exe"), "/F", "/T", "/PID", str(child.pid)],  # noqa: S603
                                   creationflags=subprocess.CREATE_NO_WINDOW, check=True)
                else:
                    import signal
                    os.kill(child.pid, signal.SIGKILL)  # Use SIGKILL as a last resort
            except Exception:  # noqa: BLE001
                number_failed_children += 1
                log.critical("Failed to kill process %s", child.pid, exc_info=True)
    if number_failed_children:
        log.error("Failed to terminate %s total processes!", number_failed_children)
    return bool(number_failed_children)


def gracefully_shutdown_threads(timeout: int = 3) -> bool:
    """Attempts to gracefully join all threads in the main process with a specified timeout.

    If any thread does not terminate within the timeout, record the error and proceed to terminate the next thread.
    After attempting with all threads, if any have timed out, force shutdown the process.

    If all terminate gracefully or if there are no threads, exit normally.
    """
    RobustRootLogger().info("Attempting to terminate threads gracefully...")
    main_thread = threading.main_thread()
    other_threads = [t for t in threading.enumerate() if t is not main_thread]
    number_timeout_threads = 0
    RobustRootLogger().debug("%s existing threads to terminate.", len(other_threads))
    if not other_threads:
        return True

    for thread in other_threads:
        if thread.__class__.__name__ == "_DummyThread":
            RobustRootLogger().debug("Ignoring dummy thread '%s'", thread.getName())
            continue
        if not thread.is_alive():
            RobustRootLogger().debug("Ignoring dead thread '%s'", thread.getName())
            continue
        try:
            thread.join(timeout)
            if thread.is_alive():
                RobustRootLogger().warning("Thread '%s' did not terminate within the timeout period of %s seconds.", thread.name, timeout)
                number_timeout_threads += 1
        except Exception:  # noqa: BLE001
            RobustRootLogger().exception("Failed to stop the thread")

    if number_timeout_threads:
        RobustRootLogger().warning("%s total threads would not terminate on their own!", number_timeout_threads)
    else:
        RobustRootLogger().debug("All threads terminated gracefully; exiting normally.")
    return bool(number_timeout_threads)


def terminate_main_process(
    timeout: int = 3,
    actual_self_pid: int | None = None,
):
    """Waits for a specified timeout for threads to complete.

    If threads other than the main thread are still running after the timeout, it forcefully terminates
    the process. Otherwise, exits normally.
    """
    # Wait for the timeout period to give threads a chance to finish
    time.sleep(timeout)
    result1, result2 = True, True

    try:
        result1 = terminate_child_processes(timeout=timeout)
        if actual_self_pid is None:
            result2 = gracefully_shutdown_threads(timeout=timeout)
            actual_self_pid = os.getpid()
        if result1 and result2:
            sys.exit(0)

        RobustRootLogger().warning("Child processes and/or threads did not terminate, killing main process %s as a fallback.", actual_self_pid)
        if sys.platform == "win32":
            sys32path = win_get_system32_dir()
            subprocess.run(
                [str(sys32path / "taskkill.exe"), "/F", "/T", "/PID", str(actual_self_pid)],  # noqa: S603
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=True,
            )
        else:
            import signal
            os.kill(actual_self_pid, signal.SIGKILL)
    except Exception:  # noqa: BLE001
        RobustRootLogger().exception("Exception occurred while shutting down the main process")
    finally:
        os._exit(0 if result1 and result2 else 1)


def get_app_dir() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent
    main_module = sys.modules["__main__"]
    RobustRootLogger().debug("Try to get the __file__ attribute that contains the path of the entry-point script.")
    main_script_path = getattr(main_module, "__file__", None)
    if main_script_path is not None:
        return Path(main_script_path).resolve().parent
    RobustRootLogger().debug("Fall back to the current working directory if the __file__ attribute was not found.")
    return Path.cwd()


def is_frozen() -> bool:
    return (
        getattr(sys, "frozen", False)
        or getattr(sys, "_MEIPASS", False)
        # or tempfile.gettempdir() in sys.executable  # Not sure any frozen implementations use this (PyInstaller/py2exe). Re-enable if we find one that does.
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
    finally:
        remove_any(dummy_filepath, ignore_errors=True, missing_ok=True)


def remove_any(
    path: os.PathLike | str,
    *,
    ignore_errors: bool = True,
    missing_ok: bool = True
):
    path_obj = Path.pathify(path)
    isdir_func = Path.safe_isdir if ignore_errors else Path.is_dir
    isfile_func = Path.safe_exists if ignore_errors else Path.exists
    if not isfile_func(path_obj):
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
        try:
            _remove_any(path_obj)
        except Exception:  # noqa: BLE001
            if not ignore_errors:
                raise
        else:
            if not isfile_func(path_obj):
                return
            print(f"File/folder {path_obj} still exists after {i} iterations! (remove_any)", file=sys.stderr)  # DO NOT IMPORT GET_ROOT_LOGGER HERE
    else:
        for i in range(100):
            try:
                _remove_any(path_obj)
            except Exception:  # noqa: PERF203, BLE001
                if not ignore_errors:
                    raise
                time.sleep(0.01)
            else:
                if not isfile_func(path_obj):
                    return
                print(f"File/folder {path_obj} still exists after {i} iterations! (remove_any)", file=sys.stderr)  # DO NOT IMPORT GET_ROOT_LOGGER HERE
        if not ignore_errors:  # should raise at this point.
            _remove_any(path_obj)


def get_mac_dot_app_dir(directory: os.PathLike | str) -> Path:
    """Returns the .app directory of literal executable.

    For example if `directory` is '~/MyApp.app/Contents/MacOS/MyApp', will return MyApp.app

    Args:
    ----
       directory (os.PathLike | str): Directory of the literal executable inside the .app (e.g. '~/MyApp.app/Contents/MacOS/MyApp')

    Returns:
    -------
       (pathlib.Path): Path to the .app
    """
    return Path.pathify(directory).parents[2]


def win_get_system32_dir() -> Path:
    try:  # PyInstaller sometimes fails to import wintypes.
        ctypes.windll.kernel32.GetSystemDirectoryW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint]
        ctypes.windll.kernel32.GetSystemDirectoryW.restype = ctypes.c_uint
        # Buffer size (MAX_PATH is generally 260 as defined by Windows)
        buffer = ctypes.create_unicode_buffer(260)
        ctypes.windll.kernel32.GetSystemDirectoryW(buffer, len(buffer))
        return Path(buffer.value)
    except Exception:  # noqa: BLE001
        RobustRootLogger().warning("Error accessing system directory via GetSystemDirectoryW. Attempting fallback.", exc_info=True)
        buffer = ctypes.create_unicode_buffer(260)
        ctypes.windll.kernel32.GetWindowsDirectoryW(buffer, len(buffer))
        return Path(buffer.value).joinpath("system32")


def win_hide_file(filepath: os.PathLike | str):
    """Hides a file. More specifically, uses `ctypes` to set the hidden attribute.

    Args:
    ----
        filepath: os.PathLike | str - the path to the file

    Raises:
    ------
        OSError: Some os error occurred, probably permissions related.
    """
    ret = ctypes.windll.kernel32.SetFileAttributesW(str(filepath), 0x02)
    if not ret:
        # WinError will automatically grab the relevant code and message
        raise ctypes.WinError()
