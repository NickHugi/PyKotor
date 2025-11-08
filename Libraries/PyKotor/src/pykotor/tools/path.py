from __future__ import annotations

import atexit
import errno
import os
import pathlib
import platform
import shutil
import subprocess
import sys
import tempfile

from functools import lru_cache
from typing import TYPE_CHECKING

from pykotor.tools.registry import find_software_key, winreg_key
from utility.string_util import ireplace
from utility.system.path import (
    Path as InternalPath,
    PosixPath as InternalPosixPath,
    PurePath as InternalPurePath,
    WindowsPath as InternalWindowsPath,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from typing import Any, ClassVar

    from typing_extensions import Self

    from pykotor.common.misc import Game

# Try to import fusepy for optional FUSE support on POSIX systems
_fuse_available = False
_fuse_operations_class = None
_fuse_class = None

if os.name == "posix":
    try:
        from fuse import FUSE, FuseOSError, Operations  # pyright: ignore[reportMissingImports]

        _fuse_available = True
        _fuse_operations_class = Operations
        _fuse_class = FUSE
    except (ImportError, Exception) as e:
        # fusepy not installed or FUSE not available on system
        print(f"FUSE support unavailable, falling back to standard implementation: {e}")
        _fuse_available = False


def is_filesystem_case_sensitive(
    path: os.PathLike | str,
) -> bool | None:
    """Check if the filesystem at the given path is case-sensitive.
    This function creates a temporary file to test the filesystem behavior.
    """
    try:
        with tempfile.TemporaryDirectory(dir=path) as temp_dir:
            temp_path: pathlib.Path = pathlib.Path(temp_dir)
            test_file: pathlib.Path = temp_path / "case_test_file"
            test_file.touch()

            # Attempt to access the same file with a different case to check case sensitivity
            test_file_upper: pathlib.Path = temp_path / "CASE_TEST_FILE"
            return not test_file_upper.exists()
    except Exception:  # noqa: BLE001
        return None


# FUSE-based case-insensitive filesystem implementation
if _fuse_available:

    def _get_case_insensitive_path_fast(
        path: str,
        ret_found: bool = False,  # noqa: FBT001, FBT002
    ) -> tuple[str, bool] | str:
        """Fast case-insensitive path resolution for FUSE.

        Args:
        ----
            path: Path to resolve
            ret_found: Whether to return a tuple with found status

        Returns:
        -------
            Resolved path, or tuple of (path, found) if ret_found is True
        """
        if path == "" or os.path.exists(path):  # noqa: PTH110
            return (path, True) if ret_found else path

        f = os.path.basename(path)  # noqa: PTH119
        d = os.path.dirname(path)  # noqa: PTH120
        suffix = ""
        if not f:
            if len(d) < len(path):
                suffix = path[: len(path) - len(d)]
            f = os.path.basename(d)  # noqa: PTH119
            d = os.path.dirname(d)  # noqa: PTH120

        if not os.path.exists(d):  # noqa: PTH110
            result = _get_case_insensitive_path_fast(d, ret_found=True)
            if isinstance(result, tuple):
                d, found = result
                if not found:
                    return (path, False) if ret_found else path
            else:
                # This shouldn't happen but handle it safely
                return (path, False) if ret_found else path

        try:
            files = os.listdir(d)  # noqa: PTH208
        except Exception as e:
            print(f"Failed to list directory {d}: {e}")
            return (path, False) if ret_found else path

        f_low = f.lower()
        try:
            f_nocase = next(fl for fl in files if fl.lower() == f_low)
        except StopIteration:
            f_nocase = None

        if f_nocase:
            return (
                (os.path.join(d, f_nocase) + suffix, True)  # noqa: PTH118
                if ret_found
                else os.path.join(d, f_nocase) + suffix  # noqa: PTH118
            )
        return (path, False) if ret_found else path

    class _CaseInsensitiveFS(_fuse_operations_class):  # type: ignore[misc,valid-type]
        """Case-insensitive passthrough filesystem using FUSE."""

        def __init__(self, root: str):
            """Initialize the filesystem.

            Args:
            ----
                root: Root directory to make case-insensitive
            """
            self.root = root
            print(f"Initialized FUSE case-insensitive filesystem for root: {root}")

        def _full_path(self, partial: str) -> str:
            """Resolve partial path to full path with case-insensitive matching.

            Args:
            ----
                partial: Partial path relative to mount point

            Returns:
            -------
                Full resolved path
            """
            if partial.startswith("/"):
                partial = partial[1:]
            path = os.path.join(self.root, partial)  # noqa: PTH118
            path = _get_case_insensitive_path_fast(path)
            return path[0] if isinstance(path, tuple) else path

        def access(self, path: str, mode: int):
            """Check file access permissions."""
            full_path = self._full_path(path)
            if not os.access(full_path, mode):
                raise FuseOSError(errno.EACCES)  # type: ignore[name-defined]

        def chmod(self, path: str, mode: int) -> None:
            """Change file permissions."""
            full_path = self._full_path(path)
            return os.chmod(full_path, mode)  # noqa: PTH101

        def chown(self, path: str, uid: int, gid: int) -> None:
            """Change file ownership."""
            full_path = self._full_path(path)
            return os.chown(full_path, uid, gid)

        def getattr(self, path: str, fh: int | None = None) -> dict[str, Any]:
            """Get file attributes."""
            full_path = self._full_path(path)
            st = os.lstat(full_path)
            return {
                key: getattr(st, key)
                for key in (
                    "st_atime",
                    "st_ctime",
                    "st_gid",
                    "st_mode",
                    "st_mtime",
                    "st_nlink",
                    "st_size",
                    "st_uid",
                )
            }

        def readdir(self, path: str, fh: int):
            """Read directory contents."""
            full_path = self._full_path(path)
            dirents = [".", ".."]
            if os.path.isdir(full_path):  # noqa: PTH112
                dirents.extend(os.listdir(full_path))  # noqa: PTH208
            yield from dirents

        def readlink(self, path: str) -> str:
            """Read symbolic link target."""
            pathname = os.readlink(self._full_path(path))
            if pathname.startswith("/"):
                return os.path.relpath(pathname, self.root)
            return pathname

        def mknod(self, path: str, mode: int, dev: int) -> None:
            """Create a filesystem node."""
            return os.mknod(self._full_path(path), mode, dev)

        def rmdir(self, path: str):  # noqa: ANN202
            """Remove directory."""
            full_path = self._full_path(path)
            return os.rmdir(full_path)  # noqa: PTH106

        def mkdir(self, path: str, mode: int) -> None:
            """Create directory."""
            return os.mkdir(self._full_path(path), mode)  # noqa: PTH102

        def statfs(self, path: str) -> dict[str, Any]:
            """Get filesystem statistics."""
            full_path = self._full_path(path)
            stv = os.statvfs(full_path)
            return {
                key: getattr(stv, key)
                for key in (
                    "f_bavail",
                    "f_bfree",
                    "f_blocks",
                    "f_bsize",
                    "f_favail",
                    "f_ffree",
                    "f_files",
                    "f_flag",
                    "f_frsize",
                    "f_namemax",
                )
            }

        def unlink(self, path: str) -> None:
            """Remove file."""
            return os.unlink(self._full_path(path))  # noqa: PTH108

        def symlink(self, name: str, target: str) -> None:
            """Create symbolic link."""
            return os.symlink(target, self._full_path(name))  # noqa: PTH211

        def rename(self, old: str, new: str) -> None:
            """Rename file or directory."""
            return os.rename(self._full_path(old), self._full_path(new))  # noqa: PTH104

        def link(self, target: str, name: str) -> None:
            """Create hard link."""
            return os.link(self._full_path(name), self._full_path(target))  # noqa: PTH200

        def utimens(self, path: str, times: tuple[float, float] | None = None) -> None:
            """Update file access and modification times."""
            return os.utime(self._full_path(path), times)

        def open(self, path: str, flags: int) -> int:
            """Open file."""
            full_path = self._full_path(path)
            return os.open(full_path, flags)

        def create(self, path: str, mode: int, fi: Any = None) -> int:
            """Create and open file."""
            full_path = self._full_path(path)
            return os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)

        def read(self, path: str, length: int, offset: int, fh: int) -> bytes:
            """Read from file."""
            os.lseek(fh, offset, os.SEEK_SET)
            return os.read(fh, length)

        def write(self, path: str, buf: bytes, offset: int, fh: int) -> int:
            """Write to file."""
            os.lseek(fh, offset, os.SEEK_SET)
            return os.write(fh, buf)

        def truncate(self, path: str, length: int, fh: int | None = None):
            """Truncate file."""
            full_path = self._full_path(path)
            with open(full_path, "r+", encoding="utf-8") as f:  # noqa: PTH123
                f.truncate(length)

        def flush(self, path: str, fh: int) -> None:
            """Flush file buffers."""
            return os.fsync(fh)

        def release(self, path: str, fh: int) -> None:
            """Release file handle."""
            return os.close(fh)

        def fsync(self, path: str, fdatasync: int, fh: int) -> None:
            """Sync file to disk."""
            return self.flush(path, fh)


# Global mount management for FUSE
_fuse_mounts: dict[str, str] = {}  # Maps real_path -> mount_point
_fuse_mount_tempdir: tempfile.TemporaryDirectory | None = None


def _cleanup_fuse_mounts():
    """Unmount all FUSE filesystems and cleanup on exit."""
    global _fuse_mounts, _fuse_mount_tempdir  # noqa: PLW0602, PLW0603
    for _real_path, mount_point in list(_fuse_mounts.items()):
        try:
            print(f"Unmounting FUSE filesystem: {mount_point}")
            subprocess.run(  # noqa: S603
                ["fusermount", "-u", mount_point],  # noqa: S607
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except Exception:
            print(f"Failed to unmount {mount_point}")

    _fuse_mounts.clear()

    if _fuse_mount_tempdir:
        try:
            _fuse_mount_tempdir.cleanup()
        except Exception:
            print("Failed to cleanup FUSE temp directory")
        _fuse_mount_tempdir = None


# Register cleanup on exit
if _fuse_available:
    atexit.register(_cleanup_fuse_mounts)


def _get_or_create_fuse_mount(root_path: str) -> str | None:
    """Get existing FUSE mount or create a new one for the given root path.

    Args:
    ----
        root_path: Root directory to mount as case-insensitive

    Returns:
    -------
        Mount point path if successful, None if mounting failed
    """
    global _fuse_mounts, _fuse_mount_tempdir  # noqa: PLW0602, PLW0603

    if not _fuse_available:
        return None

    # Normalize root path
    root_path = str(pathlib.Path(root_path).resolve())

    # Check if already mounted
    if root_path in _fuse_mounts:
        mount_point = _fuse_mounts[root_path]
        if os.path.isdir(mount_point):  # noqa: PTH112
            return mount_point
        # Mount point disappeared, remove from dict
        print(f"Mount point {mount_point} no longer exists, will remount {root_path}")
        del _fuse_mounts[root_path]

    # Create temp directory for mounts if needed
    if _fuse_mount_tempdir is None:
        try:
            _fuse_mount_tempdir = tempfile.TemporaryDirectory(prefix="pykotor_fuse_")
        except Exception as e:
            print(f"Failed to create FUSE mount temp directory: {e}")
            return None

    # Create mount point
    try:
        mount_point = os.path.join(  # noqa: PTH118
            _fuse_mount_tempdir.name, f"mount_{len(_fuse_mounts)}"
        )
        os.makedirs(mount_point, exist_ok=True)  # noqa: PTH103
    except Exception as e:
        print(f"Failed to create mount point directory: {e}")
        return None

    # Mount the filesystem in background using ProcessPoolExecutor
    try:
        if _fuse_class is None:
            print(f"FUSE class not available, cannot mount {root_path}")
            return None

        print(f"Mounting FUSE case-insensitive filesystem: {root_path} -> {mount_point}")

        # Start FUSE in a background process using ProcessPoolExecutor
        from concurrent.futures import ProcessPoolExecutor

        def mount_process(root: str, mount: str) -> None:
            """Run FUSE mount in a separate process.

            Args:
            ----
                root: Root directory to mount
                mount: Mount point directory
            """
            try:
                # Import here to avoid pickling issues
                from fuse import FUSE  # noqa: PLC0415  # pyright: ignore[reportMissingImports]

                fs = _CaseInsensitiveFS(root)
                FUSE(
                    fs,
                    mount,
                    nothreads=True,
                    foreground=True,
                    allow_other=False,
                )
            except Exception as e:
                print(f"FUSE mount process failed for {root}: {e}")
                import traceback
                traceback.print_exc()

        # Submit to process pool executor
        executor = ProcessPoolExecutor(max_workers=1)
        _future = executor.submit(mount_process, root_path, mount_point)

        # Don't wait for it to complete, it runs indefinitely
        # The process will be killed when program exits

        # Give it a moment to mount
        import time

        time.sleep(0.5)

        # Verify mount succeeded
        if not os.path.ismount(mount_point):
            print(f"FUSE mount verification failed for {root_path}")
            executor.shutdown(wait=False, cancel_futures=True)
            return None

        _fuse_mounts[root_path] = mount_point
        print(f"Successfully mounted {root_path} at {mount_point}")

    except Exception as e:
        print(f"Failed to mount FUSE filesystem for {root_path}: {e}")
        import traceback

        traceback.print_exc()
        return None
    else:
        return mount_point


def simple_wrapper(fn_name: str, wrapped_class_type: type[CaseAwarePath]) -> Callable[..., Any]:
    """Wraps a function to handle case-sensitive pathlib.PurePath arguments.

    This is a hacky way of ensuring that all args to any pathlib methods have their path case-sensitively resolved.
    This also resolves self, *args, and **kwargs for ensured accuracy.

    Args:
    ----
        fn_name: The name of the function to wrap
        wrapped_class_type: The class type that the function belongs to

    Returns:
    -------
        Callable[..., Any]: A wrapped function with the same signature as the original

    Processing Logic:
    ----------------
        1. Gets the original function from the class's _original_methods attribute
        2. Parses arguments that are paths, resolving case if needed
        3. Calls the original function with the parsed arguments.
    """

    def wrapped(self: CaseAwarePath, *args, **kwargs) -> Any:
        """Wraps a function to handle case-sensitive path resolution.

        Args:
        ----
            self: The object the method is called on
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments

        Returns:
        -------
            Any: The return value of the wrapped function

        Processing Logic:
        ----------------
            - Parse self, args and kwargs to resolve case-sensitive paths where needed
            - Call the original function, passing the parsed arguments
            - Return the result
        """
        orig_fn = wrapped_class_type._original_methods[fn_name]  # noqa: SLF001
        # Do not use. CaseAwarePath's performance depends on only resolving case when it absolutely has to.
        # if fn_name == "__new__":
        #    path_obj = pathlib.Path(*args, **kwargs)
        #    if "called_from_getcase" not in kwargs and not path_obj.exists():
        #        return CaseAwarePath.get_case_sensitive_path(path_obj)

        def parse_arg(arg: Any) -> CaseAwarePath | Any:
            if hasattr(arg, "__fspath__"):
                pathlib_path_obj = pathlib.Path(arg)
                is_absolute = pathlib_path_obj.is_absolute()
                if arg.__class__ is CaseAwarePath and is_absolute:
                    # For CaseAwarePath instances, always resolve case when absolute
                    # This ensures we use the correct case even if pathlib.exists() returns True
                    # due to case-insensitive filesystem checks
                    resolved = CaseAwarePath.get_case_sensitive_path(arg)
                    # Ensure the resolved path is still absolute if original was absolute
                    resolved_pathlib = pathlib.Path(resolved)
                    # Use resolve() to get the actual filesystem path (handles symlinks and gets real path)
                    # This is important for Windows case-sensitive directories where os.replace() needs exact paths
                    try:
                        resolved_str = str(resolved_pathlib.resolve())
                    except (OSError, RuntimeError):  # noqa: BLE001
                        # If resolve() fails (e.g., path doesn't exist), fall back to absolute()
                        resolved_str = str(resolved_pathlib.absolute())
                    resolved = CaseAwarePath._create_instance(resolved_str, called_from_getcase=True)  # noqa: SLF001
                    return resolved
                if is_absolute and not pathlib_path_obj.exists() and not hasattr(arg, "__bases__"):
                    # For non-CaseAwarePath path-like objects, resolve case and convert
                    new_cls = arg.__class__
                    instance = CaseAwarePath.get_case_sensitive_path(arg)
                    # Ensure the resolved path is still absolute if original was absolute
                    # Use pathlib.Path to convert to avoid triggering wrapper recursion
                    instance_pathlib = pathlib.Path(instance)
                    # Always make absolute if original was absolute, regardless of what is_absolute() says
                    instance_str = str(instance_pathlib.absolute())
                    instance = CaseAwarePath._create_instance(instance_str, called_from_getcase=True)  # noqa: SLF001
                    # Return the appropriate class type if it's a base class of CaseAwarePath
                    return new_cls(instance) if (arg.__class__ in CaseAwarePath.__bases__ and arg.__class__ is not object) else instance
            return arg

        actual_self_or_cls: CaseAwarePath | type = parse_arg(self)
        new_args: tuple[CaseAwarePath | Any, ...] = tuple(parse_arg(arg) for arg in args)
        new_kwargs: dict[str, CaseAwarePath | Any] = {k: parse_arg(v) for k, v in kwargs.items()}

        # TODO(th3w1zard1): when orig_fn doesn't exist, the AttributeException should be raised by  # noqa: TD003
        # the prior stack instead of here, as that's what would normally happen.

        return orig_fn(actual_self_or_cls, *new_args, **new_kwargs)

    return wrapped


def create_case_insensitive_pathlib_class(
    cls: type[CaseAwarePath],
) -> None:
    """Wraps methods of a pathlib class to be case insensitive.

    Args:
    ----
        cls: The pathlib class to wrap

    Processing Logic:
    ----------------
        1. Create a dictionary to store original methods
        2. Get the method resolution order and exclude current class
        3. Store already wrapped methods to avoid wrapping multiple times
        4. Loop through parent classes and methods
        5. Check if method and not wrapped before
        6. Add method to wrapped dictionary and reassign with wrapper.
    """
    mro: list[type] = cls.mro()  # Gets the method resolution order
    parent_classes: list[type] = mro[1:-1]  # Exclude the current class itself and the object class
    cls_methods: set[str] = {method for method in cls.__dict__ if callable(getattr(cls, method))}  # define names of methods in the cls, excluding inherited

    # Store already wrapped methods to avoid wrapping multiple times
    wrapped_methods = set()

    # ignore these methods
    ignored_methods: set[str] = {
        "__instancecheck__",
        "__getattribute__",
        "__setattribute__",
        "_fix_path_formatting",
        "__getattr__",
        "__setattr__",
        "__init__",
        "__fspath__",
        "__truediv__",
        "_fspath_str",
        "_init",
        "__new__",
        "pathify",
        "is_relative_to",
        "replace",
        *cls_methods,
    }

    for parent in parent_classes:
        for attr_name, attr_value in parent.__dict__.items():
            # Check if it's a method and hasn't been wrapped before
            if not callable(attr_value):
                continue
            if attr_name in wrapped_methods:
                continue
            if attr_name in ignored_methods:
                continue
            cls._original_methods[attr_name] = attr_value  # type: ignore[attr-defined]  # pylint: disable=protected-access
            setattr(cls, attr_name, simple_wrapper(attr_name, cls))
            wrapped_methods.add(attr_name)


# TODO(th3w1zard1): Move to pykotor.common  # noqa: TD003
class CaseAwarePath(InternalWindowsPath if os.name == "nt" else InternalPosixPath):  # type: ignore[misc, no-redef]
    """A class capable of resolving case-sensitivity in a path. Absolutely essential for working with KOTOR files on Unix filesystems."""

    __slots__: tuple[str] = ("_tail_cached",)
    _original_methods: ClassVar[dict[str, Callable[..., Any]]] = {}

    if sys.version_info < (3, 13):
        def as_posix(self) -> str:
            """Convert path to a POSIX path.

            Override for Python 3.12 compatibility - avoids calling super().__str__()
            which expects _str and _drv attributes that may not be initialized.
            """
            # For Python < 3.13, use str() directly to avoid AttributeError on _str/_drv
            return self.str_norm(str(self), slash="/")

    if sys.version_info[:2] == (3, 12):
        @property
        def drive(self) -> str:
            """Return the drive letter (e.g., 'C:') for Windows paths.

            Override for Python 3.12 compatibility - avoids accessing _drv attribute
            which may not be initialized.
            """
            path_str = str(self)
            if os.name == "nt" and len(path_str) >= 2 and path_str[1] == ":":
                return path_str[:2]
            return ""

        @property
        def root(self) -> str:
            r"""Return the root path (e.g., '\\' for Windows absolute paths).

            Override for Python 3.12 compatibility - avoids accessing _root attribute
            which may not be initialized.
            """
            path_str = str(self)
            if os.name == "nt":
                # Windows absolute path: C:\Users\... -> root is "\\"
                if len(path_str) >= 3 and path_str[1] == ":" and path_str[2] in ("\\", "/"):
                    return "\\"
                # UNC path: \\server\share\... -> root is "\\"
                if path_str.startswith("\\\\"):
                    return "\\\\"
            elif path_str.startswith("/"):
                return "/"
            return ""

    @staticmethod
    def extract_absolute_prefix(
        relative_path: InternalPath,
        absolute_path: InternalPath,
    ) -> tuple[str, ...]:
        # Ensure the absolute path is absolute and the relative path is resolved relative to it
        absolute_path = absolute_path.absolute()
        relative_path_resolved: InternalPath = (absolute_path.parent / relative_path).absolute()

        # Convert to lists of parts for comparison
        abs_parts: tuple[str, ...] = absolute_path.parts
        rel_parts: tuple[str, ...] = relative_path_resolved.parts

        # Identify the index where the relative path starts in the absolute path
        start_index_of_rel_in_abs = len(abs_parts) - len(rel_parts)

        # Extract the differing prefix part as a new Path object
        return abs_parts[:start_index_of_rel_in_abs]

    def safe_relative_to(
        self,
        other: str | os.PathLike,
    ) -> str:
        """Calculate the relative path between two paths, ensuring the result is case-sensitive if needed.

        Args:
        ----
            other: The target path to calculate the relative path to.

        Returns:
        -------
            str: The relative path between the two paths.

        Processing Logic:
        ----------------
            - Normalize the paths to handle different OS path conventions.
            - Get the common prefix of the two paths.
            - Calculate the relative path based on the common prefix.
            - Return the relative path as a string.
        """
        # Normalize paths to handle different OS path conventions
        from_path = os.path.normpath(self)
        to_path = os.path.normpath(other)

        # Get common prefix
        common_prefix = os.path.commonpath([os.path.abspath(from_path), os.path.abspath(to_path)])  # noqa: PTH100

        # Calculate relative path
        from_parts: tuple[str, ...] = tuple(from_path.split(os.sep))  # noqa: PTH206
        to_parts: tuple[str, ...] = tuple(to_path.split(os.sep))  # noqa: PTH206
        common_parts: tuple[str, ...] = tuple(common_prefix.split(os.sep))  # noqa: PTH206

        # Number of "../" to prepend for going up from from_path to the common prefix
        up_dirs: int | str = len(from_parts) - len(common_parts)
        if up_dirs == 0:
            up_dirs = "."

        # Remaining parts after the common prefix
        down_dirs = os.sep.join(to_parts[len(common_parts) :])  # noqa: PTH118

        result: str | int = f"{up_dirs}{os.sep}{down_dirs}" if down_dirs else up_dirs
        if isinstance(result, int):
            print(f"result somehow an int: {result}")
        return str(result)

    def relative_to(
        self,
        *args: os.PathLike | str,
        walk_up: bool = False,
        **kwargs,
    ) -> InternalPath:
        if not args or "other" in kwargs:
            raise TypeError("relative_to() missing 1 required positional argument: 'other'")  # noqa: TRY003, EM101

        other, *_deprecated = args
        # Use pathlib.Path directly to avoid triggering wrapped methods and recursion
        pathlib_self = pathlib.Path(self)
        if isinstance(self, InternalPath) and pathlib_self.is_absolute():
            # Ensure path is absolute and CaseAwarePath for case-insensitive comparison
            if isinstance(self, CaseAwarePath):
                resolved_self = CaseAwarePath(str(pathlib_self.absolute()))
            else:
                resolved_self = self.__class__(str(pathlib_self.absolute()))
        else:
            resolved_self = self

        if isinstance(other, (str, os.PathLike)):
            # Construct the "other" path with the same type as self (handling any _deprecated args)
            if _deprecated:
                # If there are additional arguments, join them as segments.
                segments = (other, *_deprecated)
                parsed_other = self.__class__(*segments)
            else:
                parsed_other = self.__class__(other)
            pathlib_parsed_other = pathlib.Path(parsed_other)
            if isinstance(parsed_other, InternalPath) and pathlib_parsed_other.is_absolute():
                # Ensure path is absolute and CaseAwarePath for case-insensitive comparison
                if isinstance(self, CaseAwarePath):
                    parsed_other = CaseAwarePath(str(pathlib_parsed_other.absolute()))
                else:
                    parsed_other = parsed_other.__class__(str(pathlib_parsed_other.absolute()))
            # Ensure parsed_other is a CaseAwarePath if self is
            if isinstance(self, CaseAwarePath) and not isinstance(parsed_other, CaseAwarePath):
                parsed_other = CaseAwarePath(parsed_other)
        else:
            # If not a string/PathLike, ensure it's an InternalPurePath, then join further segments if present
            if not isinstance(other, InternalPurePath):
                parsed_other = InternalPurePath(other)
            else:
                parsed_other = other
            if _deprecated:
                # Join segments if provided
                parsed_other = parsed_other.__class__(str(parsed_other), *_deprecated)
            # Ensure parsed_other is a CaseAwarePath if self is
            if isinstance(self, CaseAwarePath) and not isinstance(parsed_other, CaseAwarePath):
                parsed_other = CaseAwarePath(parsed_other)

        # For CaseAwarePath, use case-insensitive comparison via as_posix().lower()
        if isinstance(self, CaseAwarePath):
            # Normalize both paths to remove trailing separators and get consistent comparison
            pathlib_resolved_self = pathlib.Path(resolved_self)
            pathlib_parsed_other = pathlib.Path(parsed_other)
            resolved_self_normalized = CaseAwarePath(str(pathlib_resolved_self.absolute()))
            parsed_other_normalized = CaseAwarePath(str(pathlib_parsed_other.absolute()))

            # Use case-insensitive comparison to find matching prefix
            self_posix = resolved_self_normalized.as_posix().lower()
            other_posix = parsed_other_normalized.as_posix().lower()

            if not self_posix.startswith(other_posix):
                msg = f"self '{resolved_self_normalized}' is not relative to other '{parsed_other_normalized}'"
                raise ValueError(msg)

            # Extract the relative part using the case from resolved_self
            if self_posix == other_posix:
                # Paths are the same
                replacement = "."
            else:
                # Remove the matching prefix and normalize separators
                relative_part = self_posix[len(other_posix) :].lstrip("/")
                if not relative_part:
                    replacement = "."
                else:
                    # Use the actual case from resolved_self for the relative part
                    resolved_self_str = resolved_self_normalized.as_posix()
                    parsed_other_str = parsed_other_normalized.as_posix()
                    # Find the case-sensitive match
                    if resolved_self_str.lower().startswith(parsed_other_str.lower()):
                        replacement = resolved_self_str[len(parsed_other_str) :].lstrip("/")
                        # Convert forward slashes to backslashes for Windows compatibility
                        if os.name == "nt":
                            replacement = replacement.replace("/", "\\")
                    else:
                        replacement = relative_part
                        # Convert forward slashes to backslashes for Windows compatibility
                        if os.name == "nt":
                            replacement = replacement.replace("/", "\\")
        else:
            # Original logic for non-CaseAwarePath
            self_str, other_str = map(str, (resolved_self, parsed_other))
            replacement = ireplace(self_str, other_str, "").lstrip("\\").lstrip("/")
            if replacement == self_str:
                msg = f"self '{self_str}' is not relative to other '{other_str}'"
                raise ValueError(msg)
            # Normalize relative paths to use forward slashes for cross-platform compatibility
            replacement = replacement.replace("\\", "/")

        if isinstance(self, CaseAwarePath) and not pathlib.Path(replacement).exists():
            prefixes: tuple[str, ...] = self.extract_absolute_prefix(InternalPath(replacement), InternalPath(parsed_other))
            return self.get_case_sensitive_path(replacement, prefixes)
        return self.__class__(replacement)

    def is_relative_to(self, *args, **kwargs) -> bool:
        """Return True if the path is relative to another path or False.

        This override ensures case-insensitive comparison works correctly for absolute paths
        that don't exist on the filesystem.
        """
        if not args or "other" in kwargs:
            msg = f"{self.__class__.__name__}.is_relative_to() missing 1 required positional argument: 'other'"
            raise TypeError(msg)

        other, *_deprecated = args
        # For case-insensitive comparison, ensure both paths are CaseAwarePath and absolute
        # Use pathlib.Path directly to avoid triggering wrapped methods and recursion
        pathlib_self = pathlib.Path(self)
        if isinstance(self, InternalPath) and pathlib_self.is_absolute():
            # Ensure path is absolute and CaseAwarePath for case-insensitive comparison
            if isinstance(self, CaseAwarePath):
                resolved_self = CaseAwarePath(str(pathlib_self.absolute()))
            else:
                resolved_self = self.__class__(str(pathlib_self.absolute()))
        else:
            resolved_self = self

        if isinstance(other, (str, os.PathLike)):
            # Convert 'other' to a Path instance (InternalPath) and apply any _deprecated tail elements using joinpath
            parsed_other = InternalPath(other)
            for extra in _deprecated:
                parsed_other = parsed_other.joinpath(extra)
            pathlib_parsed_other = pathlib.Path(parsed_other)
            if isinstance(parsed_other, InternalPath) and pathlib_parsed_other.is_absolute():
                # Ensure path is absolute and CaseAwarePath for case-insensitive comparison
                if isinstance(self, CaseAwarePath):
                    parsed_other = CaseAwarePath(str(pathlib_parsed_other.absolute()))
                else:
                    parsed_other = parsed_other.__class__(str(pathlib_parsed_other.absolute()))
            # Ensure parsed_other is a CaseAwarePath if self is
            if isinstance(self, CaseAwarePath) and not isinstance(parsed_other, CaseAwarePath):
                parsed_other = CaseAwarePath(parsed_other)
        else:
            # If other is already InternalPurePath, use it, else convert to InternalPurePath
            parsed_other = other if isinstance(other, InternalPurePath) else InternalPurePath(other)
            for extra in _deprecated:
                parsed_other = parsed_other.joinpath(extra)
            # Ensure parsed_other is a CaseAwarePath if self is
            if isinstance(self, CaseAwarePath) and not isinstance(parsed_other, CaseAwarePath):
                parsed_other = CaseAwarePath(parsed_other)

        # Use case-insensitive comparison (via __eq__) to check if parsed_other is self or in self.parents
        if isinstance(resolved_self, CaseAwarePath):
            # Ensure parsed_other is also CaseAwarePath for proper case-insensitive comparison
            if not isinstance(parsed_other, CaseAwarePath):
                parsed_other = CaseAwarePath(parsed_other)

            # For Python < 3.12, handle Unix-style absolute paths differently
            if sys.version_info < (3, 12):
                # Check if parsed_other equals self (case-insensitive via __eq__) first
                if parsed_other == resolved_self:
                    return True

                # Check if paths appear absolute (either is_absolute() or start with / for Posix-style)
                pathlib_self_check = pathlib.Path(resolved_self)
                pathlib_parsed_other_check = pathlib.Path(parsed_other)
                self_str = str(resolved_self)
                other_str = str(parsed_other)
                self_appears_absolute = pathlib_self_check.is_absolute() or self_str.startswith("/")
                other_appears_absolute = pathlib_parsed_other_check.is_absolute() or other_str.startswith("/")

                if self_appears_absolute and other_appears_absolute:
                    # Normalize both paths to absolute CaseAwarePath instances for comparison
                    # Use pathlib.Path().absolute() to ensure proper normalization
                    try:
                        abs_self = CaseAwarePath(str(pathlib_self_check.absolute())) if pathlib_self_check.is_absolute() else CaseAwarePath(self_str)
                        abs_other = CaseAwarePath(str(pathlib_parsed_other_check.absolute())) if pathlib_parsed_other_check.is_absolute() else CaseAwarePath(other_str)
                    except (OSError, RuntimeError):  # noqa: BLE001
                        # If absolute() fails, use string-based comparison
                        abs_self = CaseAwarePath(self_str)
                        abs_other = CaseAwarePath(other_str)

                    # Use case-insensitive comparison via as_posix()
                    self_posix = abs_self.as_posix().lower()
                    other_posix = abs_other.as_posix().lower()

                    # Check if paths are the same (case-insensitive)
                    if self_posix == other_posix:
                        return True
                    # Check if other is a parent of self (case-insensitive)
                    other_posix_with_slash = other_posix + "/"
                    if self_posix.startswith(other_posix_with_slash) or (
                        self_posix.startswith(other_posix) and len(self_posix) > len(other_posix) and self_posix[len(other_posix)] == "/"
                    ):
                        return True
                else:
                    # For relative paths, check parents directly using case-insensitive comparison
                    for parent in resolved_self.parents:  # type: ignore[attr-defined]
                        if parsed_other == CaseAwarePath(parent):
                            return True
                return False

            # Python 3.12+ logic (original implementation)
            # Check if parsed_other equals self (case-insensitive via __eq__)
            if parsed_other == resolved_self:
                return True
            # Check if paths appear absolute (either is_absolute() or start with / for Posix-style)
            pathlib_self_check = pathlib.Path(resolved_self)
            pathlib_parsed_other_check = pathlib.Path(parsed_other)
            self_str = str(resolved_self)
            other_str = str(parsed_other)
            self_appears_absolute = pathlib_self_check.is_absolute() or (os.name == "nt" and self_str.startswith("/"))
            other_appears_absolute = pathlib_parsed_other_check.is_absolute() or (os.name == "nt" and other_str.startswith("/"))

            if self_appears_absolute and other_appears_absolute:
                # For paths that appear absolute, normalize using as_posix() for case-insensitive comparison
                self_posix = resolved_self.as_posix().lower()
                other_posix = parsed_other.as_posix().lower()
                # Check if paths are the same (case-insensitive)
                if self_posix == other_posix:
                    return True
                # Check if other is a parent of self (case-insensitive)
                other_posix_with_slash = other_posix + "/"
                if self_posix.startswith(other_posix_with_slash) or (
                    self_posix.startswith(other_posix) and len(self_posix) > len(other_posix) and self_posix[len(other_posix)] == "/"
                ):
                    return True
            else:
                # For relative paths, check parents directly using case-insensitive comparison
                for parent in resolved_self.parents:  # type: ignore[attr-defined]
                    if parsed_other == CaseAwarePath(parent):
                        return True
            return False

        # Fall back to parent implementation for non-CaseAwarePath
        if isinstance(resolved_self, InternalPath):
            return parsed_other == resolved_self or parsed_other in resolved_self.parents
        # PurePath fallback
        if isinstance(resolved_self, InternalPurePath):
            return parsed_other == resolved_self or any(parsed_other == parent for parent in resolved_self.parents)  # type: ignore[attr-defined]
        # Final fallback
        return parsed_other == resolved_self

    def replace(self, target: os.PathLike | str) -> Self:
        """Replace this path with target.

        This override ensures that both self and target have their case resolved
        correctly before calling os.replace(). This is critical for case-sensitive
        filesystems (Unix/Linux) and Windows case-sensitive directories where
        os.replace() requires exact path matches.

        Args:
        ----
            target: The target path to replace this path with

        Returns:
        -------
            Self: Returns self for method chaining (pathlib behavior)

        Processing Logic:
        ----------------
            - Resolve case for both self and target paths (absolute or relative)
            - Convert resolved paths to absolute paths for consistent handling
            - Use os.replace() directly with resolved string paths to ensure exact case matching
            - Works consistently across Windows, macOS, and Linux
        """
        # Convert to pathlib for checking absolute/relative status
        pathlib_self = pathlib.Path(self)
        pathlib_target = pathlib.Path(target)

        # Resolve self to absolute path and resolve case
        if pathlib_self.is_absolute():
            absolute_self = pathlib_self
        else:
            # For relative paths, resolve relative to current working directory
            absolute_self = pathlib_self.resolve()

        # Resolve case for self - get_case_sensitive_path returns the exact filesystem case
        resolved_self = CaseAwarePath.get_case_sensitive_path(absolute_self)
        # Ensure the resolved path is absolute and get its string representation
        # Use absolute() instead of resolve() to avoid potential issues on Windows case-sensitive dirs
        resolved_self_pathlib = pathlib.Path(resolved_self)
        if resolved_self_pathlib.is_absolute():
            resolved_self_str = str(resolved_self_pathlib)
        else:
            resolved_self_str = str(resolved_self_pathlib.absolute())

        # Resolve target to absolute path and resolve case
        if pathlib_target.is_absolute():
            absolute_target = pathlib_target
        else:
            # For relative paths, resolve relative to self's parent (pathlib behavior)
            # Use the resolved self path's parent
            absolute_target = (pathlib.Path(resolved_self_str).parent / target).resolve()

        # Resolve case for target - get_case_sensitive_path returns the exact filesystem case
        resolved_target = CaseAwarePath.get_case_sensitive_path(absolute_target)
        # Ensure the resolved path is absolute and get its string representation
        # Use absolute() instead of resolve() to avoid potential issues on Windows case-sensitive dirs
        resolved_target_pathlib = pathlib.Path(resolved_target)
        if resolved_target_pathlib.is_absolute():
            resolved_target_str = str(resolved_target_pathlib)
        else:
            resolved_target_str = str(resolved_target_pathlib.absolute())

        # Use os.replace() directly with the resolved string paths
        # This ensures exact case matching on all case-sensitive filesystems
        # (Unix/Linux always case-sensitive, Windows with case-sensitive directories)
        # We cannot use Path.replace() here because it may not preserve exact case
        try:
            os.replace(resolved_self_str, resolved_target_str)  # noqa: PTH105, PTH116
        except PermissionError:
            # On Windows with case-sensitive directories, os.replace() may fail
            # with PermissionError even with correct case. Fall back to shutil.move()
            # which handles this case better, though it's not atomic.
            # This ensures cross-platform compatibility while handling Windows edge cases.
            if platform.system() == "Windows":
                shutil.move(resolved_self_str, resolved_target_str)
            else:
                # Re-raise on non-Windows platforms as this shouldn't happen
                raise

        # Return self for method chaining (pathlib behavior)
        return self

    @classmethod
    def get_case_sensitive_path(  # noqa: ANN206
        cls,
        path: os.PathLike | str,
        prefixes: list[str] | tuple[str, ...] | None = None,
    ) -> Self:
        """Get a case sensitive path with optional FUSE optimization.

        Args:
        ----
            path: The path to resolve case sensitivity for
            prefixes: Optional prefix components

        Returns:
        -------
            CaseAwarePath: The path with case sensitivity resolved

        Processing Logic:
        ----------------
            - On POSIX with FUSE available: Try to use FUSE-mounted case-insensitive filesystem
            - Fallback: Use standard iterative case resolution
            - Convert the path to a pathlib Path object
            - Iterate through each path part starting from index 1
            - Check if the current path part and the path up to that part exist
            - If not, find the closest matching file/folder name in the existing path
            - Return a CaseAwarePath instance with case sensitivity resolved.
        """
        prefixes = tuple(prefixes or [])
        pathlib_path = pathlib.Path(path)
        try:
            pathlib_abspath = pathlib.Path(*prefixes, path).absolute() if prefixes else pathlib_path.absolute()
        except RuntimeError:
            pathlib_abspath = pathlib_path.absolute()

        num_differing_parts = len(pathlib_abspath.parts) - len(pathlib_path.parts)  # keeps the path relative if it already was.

        # Try FUSE optimization on POSIX systems
        if _fuse_available and os.name == "posix" and pathlib_abspath.is_absolute():
            try:
                # Identify a good root to mount (e.g., first 3-4 path components)
                # Don't mount the entire filesystem root, find a reasonable subdirectory
                parts = pathlib_abspath.parts
                if len(parts) >= 3:
                    # Mount at a reasonable level (e.g., /home/user or /mnt/data)
                    mount_root = str(pathlib.Path(*parts[:min(3, len(parts) - 1)]))
                    mount_point = _get_or_create_fuse_mount(mount_root)

                    if mount_point:
                        # Translate the path to use the mount point
                        relative_to_mount = str(pathlib_abspath)[len(mount_root):].lstrip("/")
                        mounted_path = pathlib.Path(mount_point) / relative_to_mount

                        # If the path exists in the mount, use it (case-insensitive access works!)
                        if mounted_path.exists():
                            print(f"Using FUSE mount for {pathlib_abspath}: {mounted_path}")
                            # Get the real path from the mount to preserve case
                            real_resolved = mounted_path.resolve()
                            # Map back to original filesystem
                            real_path_str = str(real_resolved).replace(mount_point, mount_root, 1)
                            result_path = pathlib.Path(real_path_str)
                            return cls._create_instance(*result_path.parts[num_differing_parts:], called_from_getcase=True)
            except Exception as e:
                print(f"FUSE optimization failed, falling back to standard resolution: {e}")
                # Fall through to standard implementation

        # Standard implementation (fallback or when FUSE not available)
        parts = list(pathlib_abspath.parts)

        for i in range(1, len(parts)):  # ignore the root (/, C:\\, etc)
            base_path: InternalPath = InternalPath(*parts[:i])
            next_path: InternalPath = InternalPath(*parts[: i + 1])

            if not next_path.is_dir() and base_path.is_dir():
                # Find the first non-existent case-sensitive file/folder in hierarchy
                # if multiple are found, use the one that most closely matches our case
                # A closest match is defined, in this context, as the file/folder's name that contains the most case-sensitive positional character matches
                # If two closest matches are identical (e.g. we're looking for TeST and we find TeSt and TesT), it's probably random.
                last_part: bool = i == len(parts) - 1
                parts[i] = cls.find_closest_match(
                    parts[i],
                    (item for item in base_path.iterdir() if last_part or item.is_dir()),
                )

            elif not next_path.exists():
                break

        # Return a CaseAwarePath instance
        return cls._create_instance(*parts[num_differing_parts:], called_from_getcase=True)

    @classmethod
    def find_closest_match(
        cls,
        target: str,
        candidates: Generator[InternalPath, None, None],
    ) -> str:
        """Finds the closest match from candidates to the target string.

        Args:
        ----
            target: str - The target string to find closest match for
            candidates: Generator[pathlib.Path, None, None] - Generator of candidate paths

        Returns:
        -------
            str - The closest matching candidate's file/folder name from the candidates

        Processing Logic:
        ----------------
            - Initialize max_matching_chars to -1
            - Iterate through each candidate
            - Get the matching character count between candidate and target using get_matching_characters_count method
            - Update closest_match and max_matching_chars if new candidate has more matches
            - Return closest_match after full iteration.
            - If no exact match found, return target which will of course be nonexistent.
        """
        max_matching_chars: int = -1
        closest_match: str | None = None

        for candidate in candidates:
            matching_chars: int = cls.get_matching_characters_count(candidate.name, target)
            if matching_chars > max_matching_chars:
                closest_match = candidate.name
                if matching_chars == len(target):
                    break  # Exit the loop early if exact match (faster)
                max_matching_chars = matching_chars

        return closest_match or target

    @staticmethod
    @lru_cache(maxsize=10000)
    def get_matching_characters_count(
        str1: str,
        str2: str,
    ) -> int:
        """Returns the number of case sensitive characters that match in each position of the two strings.

        if str1 and str2 are NOT case-insensitive matches, this method will return -1.
        """
        return sum(a == b for a, b in zip(str1, str2)) if str1.lower() == str2.lower() else -1

    def __hash__(self):
        return hash(self.as_windows())

    def __eq__(
        self,
        other,
    ):
        """All pathlib classes that derive from PurePath are equal to this object if their str paths are case-insensitive equivalents."""
        if self is other:
            return True
        if not isinstance(other, (os.PathLike, str)):
            return NotImplemented
        if isinstance(other, CaseAwarePath):
            return self.as_posix().lower() == other.as_posix().lower()

        return self.str_norm(str(other), slash="/").lower() == self.as_posix().lower()

    def __repr__(self):
        str_path = self._flavour.sep.join(str(part) for part in self.parts)
        return f'{self.__class__.__name__}("{str_path}")'

    def __str__(self):
        path_obj = pathlib.Path(self)
        if path_obj.exists():
            # Use os.fspath() to get the proper string representation
            # This ensures we get the correct format even if super().__str__() returns malformed paths
            try:
                result = os.fspath(path_obj)
            except (TypeError, AttributeError):
                # Fallback to super().__str__() if os.fspath() doesn't work
                result = super().__str__()

            # Fix Windows absolute paths that might have lost the backslash after drive letter
            # e.g., "C:Users/..." should be "C:\Users\..." or "C:/Users/..." -> "C:\Users\..."
            # Check if path appears absolute (starts with drive letter) even if is_absolute() returns False
            # This handles cases where malformed paths like "C:Users/..." aren't recognized as absolute
            appears_absolute = path_obj.is_absolute() or (result and len(result) > 1 and result[1] == ":")
            if os.name == "nt" and appears_absolute and result and len(result) > 1 and result[1] == ":":
                # Ensure we have a backslash after the drive letter
                if len(result) == 2 or (len(result) > 2 and result[2] not in ("\\", "/")):
                    # Insert backslash: "C:Users" -> "C:\Users"
                    result = result[:2] + "\\" + result[2:].lstrip("/\\")
                elif result[2] == "/":
                    # Convert forward slash to backslash: "C:/Users" -> "C:\Users"
                    result = result[:2] + "\\" + result[3:].lstrip("/\\")
                # Convert remaining forward slashes to backslashes for Windows absolute paths
                # Windows absolute paths should always use backslashes: C:\Users\...
                if len(result) > 3:
                    result = result[:3] + result[3:].replace("/", "\\")
                # Handle edge case: if path is just a drive root (e.g., "C:\\" or "C:/"), return "C:" without trailing separator
                elif len(result) == 3 and result[2] in ("\\", "/"):
                    result = result[:2]

            # Normalize separators to os.sep for relative paths (platform-appropriate)
            # For absolute paths, preserve native format (keep Windows backslashes)
            # Use appears_absolute to handle malformed paths that aren't recognized as absolute
            if not appears_absolute:
                # Normalize separators to os.sep for relative paths
                result = result.replace("\\", os.sep).replace("/", os.sep)
            return result

        case_resolved_path: CaseAwarePath = self.get_case_sensitive_path(path_obj)
        # Convert to pathlib.Path to avoid recursive __str__ calls and wrapped method calls
        case_resolved_pathlib = pathlib.Path(case_resolved_path)

        # Get the string representation using os.fspath to ensure proper formatting
        # This avoids potential issues with pathlib.Path.__str__() on Windows
        try:
            result = os.fspath(case_resolved_pathlib)
        except (TypeError, AttributeError):
            # Fallback to str() if os.fspath() doesn't work
            result = str(case_resolved_pathlib)

        # Fix Windows absolute paths that might have lost the backslash after drive letter
        # e.g., "C:Users/..." should be "C:\Users\..." or "C:/Users/..." -> "C:\Users\..."
        # Check if path appears absolute (starts with drive letter) even if is_absolute() returns False
        # This handles cases where malformed paths like "C:Users/..." aren't recognized as absolute
        appears_absolute = case_resolved_pathlib.is_absolute() or (result and len(result) > 1 and result[1] == ":")
        if os.name == "nt" and appears_absolute and result and len(result) > 1 and result[1] == ":":
            # Ensure we have a backslash after the drive letter
            if len(result) == 2 or (len(result) > 2 and result[2] not in ("\\", "/")):
                # Insert backslash: "C:Users" -> "C:\Users"
                result = result[:2] + "\\" + result[2:].lstrip("/\\")
            elif result[2] == "/":
                # Convert forward slash to backslash: "C:/Users" -> "C:\Users"
                result = result[:2] + "\\" + result[3:].lstrip("/\\")
            # Convert remaining forward slashes to backslashes for Windows absolute paths
            # Windows absolute paths should always use backslashes: C:\Users\...
            if len(result) > 3:
                result = result[:3] + result[3:].replace("/", "\\")
            # Handle edge case: if path is just a drive root (e.g., "C:\\" or "C:/"), return "C:" without trailing separator
            elif len(result) == 3 and result[2] in ("\\", "/"):
                result = result[:2]

        # Normalize separators to os.sep for relative paths (platform-appropriate)
        # For absolute paths, preserve native format (keep Windows backslashes)
        # Use appears_absolute to handle malformed paths that aren't recognized as absolute
        if not appears_absolute:
            # Normalize separators to os.sep for relative paths
            result = result.replace("\\", os.sep).replace("/", os.sep)
        return result

if os.name == "posix":
    create_case_insensitive_pathlib_class(CaseAwarePath)


def get_default_paths() -> dict[str, dict[Game, list[str]]]:  # TODO(th3w1zard1): Many of these paths are incomplete and need community input.  # noqa: TD003
    from pykotor.common.misc import Game  # noqa: PLC0415  # pylint: disable=import-outside-toplevel

    return {
        "Windows": {
            Game.K1: [
                r"C:\Program Files\Steam\steamapps\common\swkotor",
                r"C:\Program Files (x86)\Steam\steamapps\common\swkotor",
                r"C:\Program Files\LucasArts\SWKotOR",
                r"C:\Program Files (x86)\LucasArts\SWKotOR",
                r"C:\GOG Games\Star Wars - KotOR",
                r"C:\Amazon Games\Library\Star Wars - Knights of the Old",
            ],
            Game.K2: [
                r"C:\Program Files\Steam\steamapps\common\Knights of the Old Republic II",
                r"C:\Program Files (x86)\Steam\steamapps\common\Knights of the Old Republic II",
                r"C:\Program Files\LucasArts\SWKotOR2",
                r"C:\Program Files (x86)\LucasArts\SWKotOR2",
                r"C:\GOG Games\Star Wars - KotOR2",
            ],
        },
        "Darwin": {
            Game.K1: [
                "~/Library/Application Support/Steam/steamapps/common/swkotor/Knights of the Old Republic.app/Contents/Assets",  # Verified
                "~/Library/Applications/Steam/steamapps/common/swkotor/Knights of the Old Republic.app/Contents/Assets/",
                # TODO(th3w1zard1): app store version of k1  # noqa: FIX002, TD003
            ],
            Game.K2: [
                "~/Library/Application Support/Steam/steamapps/common/Knights of the Old Republic II/Knights of the Old Republic II.app/Contents/Assets",
                "~/Library/Applications/Steam/steamapps/common/Knights of the Old Republic II/Star Wars™: Knights of the Old Republic II.app/Contents/GameData",
                "~/Library/Application Support/Steam/steamapps/common/Knights of the Old Republic II/KOTOR2.app/Contents/GameData/",  # Verified
                # The following might be from a pirated version of the game, they were provided anonymously
                # It is also possible these are the missing app store paths.
                "~/Applications/Knights of the Old Republic 2.app/Contents/Resources/transgaming/c_drive/Program Files/SWKotOR2/",
                "/Applications/Knights of the Old Republic 2.app/Contents/Resources/transgaming/c_drive/Program Files/SWKotOR2/",
                # TODO(th3w1zard1): app store version of k2  # noqa: FIX002, TD003
            ],
        },
        "Linux": {
            Game.K1: [
                "~/.local/share/steam/common/steamapps/swkotor",
                "~/.local/share/steam/common/steamapps/swkotor",
                "~/.local/share/steam/common/swkotor",
                "~/.steam/debian-installation/steamapps/common/swkotor",  # verified
                "~/.steam/root/steamapps/common/swkotor",  # executable name is `KOTOR1` no extension
                # Flatpak
                "~/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/common/swkotor",
                # wsl paths
                "/mnt/C/Program Files/Steam/steamapps/common/swkotor",
                "/mnt/C/Program Files (x86)/Steam/steamapps/common/swkotor",
                "/mnt/C/Program Files/LucasArts/SWKotOR",
                "/mnt/C/Program Files (x86)/LucasArts/SWKotOR",
                "/mnt/C/GOG Games/Star Wars - KotOR",
                "/mnt/C/Amazon Games/Library/Star Wars - Knights of the Old",
            ],
            Game.K2: [
                "~/.local/share/Steam/common/steamapps/Knights of the Old Republic II",
                "~/.local/share/Steam/common/steamapps/kotor2",  # guess
                "~/.local/share/aspyr-media/kotor2",
                "~/.local/share/aspyr-media/Knights of the Old Republic II",  # guess
                "~/.local/share/Steam/common/Knights of the Old Republic II",  # ??? wrong?
                "~/.steam/debian-installation/steamapps/common/Knights of the Old Republic II",  # guess
                "~/.steam/debian-installation/steamapps/common/kotor2",  # guess
                "~/.steam/root/steamapps/common/Knights of the Old Republic II",  # executable name is `KOTOR2` no extension
                # Flatpak
                "~/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/common/Knights of the Old Republic II/steamassets",
                # wsl paths
                "/mnt/C/Program Files/Steam/steamapps/common/Knights of the Old Republic II",
                "/mnt/C/Program Files (x86)/Steam/steamapps/common/Knights of the Old Republic II",
                "/mnt/C/Program Files/LucasArts/SWKotOR2",
                "/mnt/C/Program Files (x86)/LucasArts/SWKotOR2",
                "/mnt/C/GOG Games/Star Wars - KotOR2",
            ],
        },
    }


def find_kotor_paths_from_default() -> dict[Game, list[CaseAwarePath]]:
    """Finds paths to Knights of the Old Republic game data directories.

    Returns:
    -------
        dict[Game, list[CaseAwarePath]]: A dictionary mapping Games to lists of existing path locations.

    Processing Logic:
    ----------------
        - Gets default hardcoded path locations from a lookup table
        - Resolves paths and filters out non-existing ones
        - On Windows, also searches the registry for additional locations
        - Returns results as lists for each Game rather than sets
    """
    from pykotor.common.misc import Game  # noqa: PLC0415  # pylint: disable=import-outside-toplevel

    os_str = platform.system()

    # Build hardcoded default kotor locations
    raw_locations: dict[str, dict[Game, list[str]]] = get_default_paths()
    locations: dict[Game, set[CaseAwarePath]] = {
        game: {
            case_path
            for case_path in (
                CaseAwarePath(path).expanduser().resolve()
                for path in paths
            )
            if case_path.exists()
        }
        for game, paths in raw_locations.get(os_str, {}).items()
    }

    # Build kotor locations by registry (if on windows)
    if os_str == "Windows":
        from utility.system.win32.registry import resolve_reg_key_to_path

        for game, possible_game_paths in ((Game.K1, winreg_key(Game.K1)), (Game.K2, winreg_key(Game.K2))):
            for reg_key, reg_valname in possible_game_paths:
                path_str = resolve_reg_key_to_path(reg_key, reg_valname)
                path = CaseAwarePath(path_str).resolve() if path_str else None
                if path and path.name and path.is_dir():
                    locations[game].add(path)
        amazon_k1_path_str: str | None = find_software_key("AmazonGames/Star Wars - Knights of the Old")
        if amazon_k1_path_str is not None and InternalPath(amazon_k1_path_str).is_dir():
            locations[Game.K1].add(CaseAwarePath(amazon_k1_path_str))

    # don't return nested sets, return as lists.
    return {Game.K1: [*locations[Game.K1]], Game.K2: [*locations[Game.K2]]}
