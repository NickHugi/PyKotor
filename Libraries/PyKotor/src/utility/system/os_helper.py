from __future__ import annotations

import ctypes
import os
import shutil
import sys
import time
import uuid

from pathlib import Path

from loggerplus import RobustLogger


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


def get_app_dir() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent
    main_module = sys.modules["__main__"]
    RobustLogger().debug("Try to get the __file__ attribute that contains the path of the entry-point script.")
    main_script_path = getattr(main_module, "__file__", None)
    if main_script_path is not None:
        return Path(main_script_path).resolve().parent
    RobustLogger().debug("Fall back to the current working directory if the __file__ attribute was not found.")
    return Path.cwd()


def is_frozen() -> bool:
    return (
        getattr(sys, "frozen", False)
        or getattr(sys, "_MEIPASS", False)
        # or tempfile.gettempdir() in sys.executable  # Not sure any frozen implementations use this (PyInstaller/py2exe). Re-enable if we find one that does.
    )


def requires_admin(path: os.PathLike | str) -> bool:    # pragma: no cover
    """Check if a dir or a file requires admin permissions for read/write."""
    path_obj = Path(path)
    isdir_check = path_obj.is_dir()
    if isdir_check is True:
        return dir_requires_admin(path)
    isfile_check = path_obj.is_file()
    if isfile_check:
        return file_requires_admin(path)
    return isdir_check is None or isfile_check is None


def file_requires_admin(file_path: os.PathLike | str) -> bool:  # pragma: no cover
    """Check if a file requires admin permissions for read/write."""
    try:
        with Path(file_path).open("a"):
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
    _dirpath = Path(dirpath)
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
    path_obj = Path(path)
    isdir_func = Path.is_dir
    isfile_func = Path.exists
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
            print(f"File/folder {path_obj} still exists (remove_any)", file=sys.stderr)
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
                print(f"File/folder {path_obj} still exists after {i} iterations! (remove_any)", file=sys.stderr)
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
    return Path(directory).parents[2]


def win_get_system32_dir() -> Path:
    try:  # PyInstaller sometimes fails to import wintypes.
        ctypes.windll.kernel32.GetSystemDirectoryW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint]
        ctypes.windll.kernel32.GetSystemDirectoryW.restype = ctypes.c_uint
        # Buffer size (MAX_PATH is generally 260 as defined by Windows)
        buffer = ctypes.create_unicode_buffer(260)
        ctypes.windll.kernel32.GetSystemDirectoryW(buffer, len(buffer))
        return Path(buffer.value)
    except Exception:  # noqa: BLE001
        RobustLogger().warning("Error accessing system directory via GetSystemDirectoryW. Attempting fallback.", exc_info=True)
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
