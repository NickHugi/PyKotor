from __future__ import annotations

import os
import pathlib
import re
import shlex
import subprocess
import sys
import uuid

from contextlib import suppress
from functools import lru_cache
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Any, OrderedDict, Union, cast

from loggerplus import RobustLogger

from utility.error_handling import format_exception_with_variables

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from logging import Logger

    from typing_extensions import Literal, Self  # pyright: ignore[reportMissingModuleSource]

PathElem = Union[str, os.PathLike]

_WINDOWS_SPLITDRIVE_RE = re.compile(r"^([a-zA-Z]:)\\")
_WINDOWS_PATH_NORMALIZE_RE = re.compile(r"^\\{3,}")
_WINDOWS_EXTRA_SLASHES_RE = re.compile(r"(?<!^)\\+")
_UNIX_EXTRA_SLASHES_RE = re.compile(r"/{2,}")


def pathlib_to_override(cls: type) -> type:
    class_map: dict[type, type] = {
        pathlib.PurePath: PurePath,
        pathlib.PureWindowsPath: PureWindowsPath,
        pathlib.PurePosixPath: PurePosixPath,
        pathlib.Path: Path,
        pathlib.WindowsPath: WindowsPath,
        pathlib.PosixPath: PosixPath,
    }

    return class_map.get(cls, cls)

def _handle_non_hashable(
    cache_func: Callable,
    direct_func: Callable,
    path: os.PathLike | str,
) -> Any:
    path_str = os.fspath(path)
    try:
        return cache_func(path_str)
    except TypeError:
        return direct_func(path_str)

@lru_cache(maxsize=20000)
def _cached_splitroot(path: str) -> tuple[str, str]:
    return ("/", path[1:]) if path.startswith("/") else ("", path)

def _direct_splitroot(path: str) -> tuple[str, str]:
    return ("/", path[1:]) if path.startswith("/") else ("", path)

@lru_cache(maxsize=20000)
def _cached_normpath(path: str) -> str:
    return os.path.normpath(path)

def _direct_normpath(path: str) -> str:
    return os.path.normpath(path)

@lru_cache(maxsize=20000)
def _cached_isabs(path: str) -> bool:
    return os.path.isabs(path)  # noqa: PTH117

def _direct_isabs(path: str) -> bool:
    return os.path.isabs(path)  # noqa: PTH117

@lru_cache(maxsize=20000)
def _cached_splitdrive(path: str) -> tuple[str, str]:
    if os.name == "nt":
        return os.path.splitdrive(path)
    match = _WINDOWS_SPLITDRIVE_RE.match(path)
    return (match.group(0), path[match.end():]) if match else ("", path)

def _direct_splitdrive(path: str) -> tuple[str, str]:
    if os.name == "nt":
        return os.path.splitdrive(path)
    match = _WINDOWS_SPLITDRIVE_RE.match(path)
    return (match.group(0), path[match.end():]) if match else ("", path)

def cached_splitroot(path: os.PathLike | str) -> tuple[str, str]:
    return _handle_non_hashable(_cached_splitroot, _direct_splitroot, path)

def cached_normpath(path: os.PathLike | str) -> str:
    return _handle_non_hashable(_cached_normpath, _direct_normpath, path)

def cached_isabs(path: os.PathLike | str) -> bool:
    return _handle_non_hashable(_cached_isabs, _direct_isabs, path)

def cached_splitdrive(path: os.PathLike | str) -> tuple[str, str]:
    return _handle_non_hashable(_cached_splitdrive, _direct_splitdrive, path)

class PurePathType(type):
    def __instancecheck__(cls, instance: object) -> bool:  # sourcery skip: instance-method-first-arg-name
        return cls.__subclasscheck__(instance.__class__)

    def __subclasscheck__(cls, subclass: type) -> bool:  # sourcery skip: instance-method-first-arg-name
        return pathlib_to_override(cls) in pathlib_to_override(subclass).__mro__


class _PartialFlavourTypeHint:
    def __new__(cls, *args, **kwargs):
        raise RuntimeError("This class cannot be instantiated and is only used for type hinting.")
    sep: Literal["\\", "/"]


class PurePath(pathlib.PurePath, metaclass=PurePathType):  # type: ignore[misc]
    _flavour: _PartialFlavourTypeHint
    _path: Self
    _drv: str
    _root: str
    _tail: str
    _tail_cached: str

    # Custom FILO cache with a max size of 10000
    _instance_cache: OrderedDict = OrderedDict()
    _max_cache_size = 10000

    # pylint: disable-all
    def __new__(cls, *args, **kwargs) -> Self:
        # sourcery skip: remove-unreachable-code
        if cls is PurePath:
            cls = PureWindowsPath if os.name == "nt" else PurePosixPath  # type: ignore[assignment]  # noqa: PLW0642
        # disable caching for now by making it unreachable, remove below line to re-enable.
        return super().__new__(cls, *cls.parse_args(args), **kwargs)  # type: ignore[arg-type]
        instance_id = (cls, args, tuple(kwargs.items()))
        if instance_id in cls._instance_cache:
            # Move the accessed item to the end to maintain order
            instance = cls._instance_cache.pop(instance_id)
            cls._instance_cache[instance_id] = instance
        else:
            instance = super().__new__(cls, *cls.parse_args(args), **kwargs)  # type: ignore[arg-type]
            cls._instance_cache[instance_id] = instance
            if len(cls._instance_cache) > cls._max_cache_size:
                # Remove the first item from the cache to maintain the size limit
                cls._instance_cache.popitem(last=False)
        return instance

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        if sys.version_info >= (3, 12, 0):
            self._raw_paths: list[str] = self.parse_args(args)
            self._cached_str = self.str_norm(self._flavour.sep.join(self._raw_paths), slash=self._flavour.sep)
        elif self._drv.strip().endswith(":") and self._flavour.sep == "\\":
            self._root = "\\"
            self._cached_str = self.str_norm(super().__str__(), slash=self._flavour.sep)

    @classmethod
    def _create_instance(
        cls,
        *args: PathElem,
        **kwargs,  # noqa: ANN003
    ) -> Self:
        instance: Self = cls.__new__(cls, *args, **kwargs)  # type: ignore[arg-type]
        if sys.version_info >= (3, 12, 0):
            instance._raw_paths = cls.parse_args(args)  # noqa: SLF001
            instance._cached_str = cls.str_norm(cls._flavour.sep.join(instance._raw_paths), slash=cls._flavour.sep)  # noqa: SLF001
        return instance

    @classmethod
    def parse_args(
        cls,
        args: tuple[PathElem, ...],
    ) -> list[str]:
        args_list: list[str] = []

        # Find the last absolute path index using os.path.isabs and os.path.normpath
        # joining an absolute path with another absolute path prioritizes the last one.
        last_absolute_index = -1
        for i, arg in enumerate(args):
            if cached_isabs(cached_normpath(arg)):  # noqa: PTH117
                last_absolute_index = i

        # If there is an absolute path, splice the args
        if last_absolute_index != -1:
            args = args[last_absolute_index:]

        for arg in args:
            normpath_str: str = cls.str_norm(os.fspath(arg), slash=cls._flavour.sep)
            if cached_isabs(normpath_str):
                drive_or_root, splitpathpart = cached_splitdrive(normpath_str) if cls._flavour.sep == "\\" else cached_splitroot(normpath_str)
                if drive_or_root:
                    args_list.append(drive_or_root)
                if splitpathpart and splitpathpart.strip():
                    args_list.append(splitpathpart)
            else:
                parts = normpath_str.split(cls._flavour.sep)
                args_list.extend(parts)

        return args_list

    @classmethod
    @lru_cache(maxsize=20000)
    def str_norm(
        cls,
        str_path: str,
        *,
        slash: str = os.sep,
    ) -> str:  # sourcery skip: assign-if-exp, reintroduce-else
        """Normalizes a path string.

        This differs from os.path.normpath in various ways, e.g. it leaves '..' parts intact just like pathlib.PurePath does.

        Args:
        ----
            str_path (str): The path string to format
            slash (str): The path separator character (kwarg)

        Returns:
        -------
            str: The formatted path string
        """
        if slash not in ("\\", "/"):
            msg = f"Invalid slash str: '{slash}'"
            raise ValueError(msg)

        formatted_path: str = str_path.strip('"').strip()
        if not formatted_path:
            return "."

        # For Windows paths
        if slash == "\\":
            formatted_path = formatted_path.replace("/", "\\").replace("\\.\\", "\\")
            formatted_path = _WINDOWS_PATH_NORMALIZE_RE.sub(r"\\\\", formatted_path)
            formatted_path = _WINDOWS_EXTRA_SLASHES_RE.sub(r"\\", formatted_path)
        # For Unix-like paths
        elif slash == "/":
            formatted_path = formatted_path.replace("\\", "/").replace("/./", "/")
            formatted_path = _UNIX_EXTRA_SLASHES_RE.sub("/", formatted_path)


        # Strip any trailing slashes, don't call rstrip if the formatted path == "/"
        if len(formatted_path) != 1:
            formatted_path = formatted_path.rstrip(slash)
        return formatted_path or "."

    def __str__(self):
        """Return the result from _fix_path_formatting that was initialized."""
        if not hasattr(self, "_cached_str"):  # Sometimes pathlib's internal instance creation mechanisms won't call our __init__
            self._cached_str = self.str_norm(super().__str__(), slash=self._flavour.sep)  # pyright: ignore[reportAttributeAccessIssue]
        return self._cached_str

    def __repr__(self):
        return f"{self.__class__.__name__}({self!s})"

    def __eq__(self, __value):  # noqa: PYI063
        if __value is None:
            return False
        if self is __value:
            return True
        if isinstance(__value, (bytes, bytearray, memoryview)):
            return os.fsencode(self) == __value

        self_compare: Self | str = self  # type: ignore[assignment]
        other_compare = __value
        if isinstance(__value, (os.PathLike, str)):
            self_compare = str(self)
            if isinstance(__value, PurePath):
                other_compare = str(__value)
            else:
                fmt_other = self.str_norm(os.fspath(__value), slash=self._flavour.sep)  # pyright: ignore[reportAttributeAccessIssue]
                other_compare = os.path.expanduser(fmt_other) if issubclass(self.__class__, (Path, WindowsPath, PosixPath)) else fmt_other  # noqa: PTH111

            if self._flavour.sep == "\\":  # pyright: ignore[reportAttributeAccessIssue]
                self_compare = self_compare.lower()
                other_compare = other_compare.lower()

        return cast("bool", self_compare == other_compare)

    def __hash__(self):
        return hash(self.as_posix() if self._flavour.sep == "/" else self.as_windows())  # pyright: ignore[reportAttributeAccessIssue]

    def __bytes__(self):
        """Return the bytes representation of the path.  This is only
        recommended to use under Unix.
        """
        return os.fsencode(self)

    def __fspath__(self) -> str:
        """Required for path-like objects."""
        return str(self)

    def __truediv__(self, key: PathElem) -> Self:
        """Appends a path part when using the divider operator '/'.
        This method is called when the left side is self.

        If key is already absolute, it will override and replace self instead of join us.

        Args:
        ----
            self: Path object
            key (path-like object or str path):
        """
        return self._create_instance(self, key)

    def __rtruediv__(self, key: PathElem) -> Self:
        """Appends a path part when using the divider operator '/'.
        This method is called when the right side is self.

        Returns self if self is already absolute.

        Args:
        ----
            self: Path object
            key (path-like object or str path):
        """
        return self._create_instance(key, self)

    def __add__(self, key: PathElem) -> str:
        """Implicitly converts the path to a str when used with the addition operator '+'.
        This method is called when the left side is self.

        Args:
        ----
            self: Path object
            key (path-like object or str path):
        """
        return self.str_norm(
            str(self / key), slash=self._flavour.sep
        )  # pyright: ignore[reportAttributeAccessIssue]

    def __radd__(self, key: PathElem) -> str:
        """Implicitly converts the path to a str when used with the addition operator '+'.
        This method is called when the right side is self.

        Args:
        ----
            self: Path object
            key (path-like object or str path):
        """
        return self.str_norm(str(key / self), slash=self._flavour.sep)  # pyright: ignore[reportAttributeAccessIssue]

    @classmethod
    def pathify(cls, path: PathElem) -> Self:
        return path if isinstance(path, cls) else cls(path)

    def split_filename(  # type: ignore[misc]
        self: PurePath,  # type: ignore[misc]
        dots: int = 1,
    ) -> tuple[str, str]:
        """Splits a filename into a tuple of stem and extension.

        Args:
        ----
            self: Path object
            dots: Number of dots to split on (default 1).
                  Negative values indicate splitting from the left.

        Returns:
        -------
            tuple: A tuple containing (stem, extension)

        Processing Logic:
        ----------------
            - The filename is split on the last N dots, where N is the dots argument
            - For negative dots, the filename is split on the first N dots from the left
            - If there are fewer parts than dots, the filename is split at the first dot
            - Otherwise, the filename is split into a stem and extension part
        """
        if dots == 0:
            msg = "Number of dots must not be 0"
            raise ValueError(msg)

        parts: list[str]
        if dots < 0:
            parts = self.name.split(".", abs(dots))
            parts.reverse()  # Reverse the order of parts for negative dots
        else:
            parts = self.name.rsplit(".", abs(dots) + 1)

        if len(parts) <= abs(dots):
            first_dot: int = self.name.find(".")
            return (self.name[:first_dot], self.name[first_dot + 1 :]) if first_dot != -1 else (self.name, "")

        return ".".join(parts[: -abs(dots)]), ".".join(parts[-abs(dots) :])

    def as_posix(self) -> str:
        """Convert path to a POSIX path.

        Args:
        ----
            self: Path object

        Returns:
        -------
            str: POSIX representation of the path
        """
        return self.str_norm(super().__str__(), slash="/")

    def as_windows(self) -> str:
        """Convert path to a WINDOWS path, lowercasing the whole path and returning a str.

        Args:
        ----
            self: Path object

        Returns:
        -------
            str: WINDOWS representation of the path as lowercase
        """
        return self.str_norm(super().__str__(), slash="\\").lower()

    def is_relative_to(self, *args, **kwargs) -> bool:
        """Return True if the path is relative to another path or False."""
        if not args or "other" in kwargs:
            msg = f"{self.__class__.__name__}.is_relative_to() missing 1 required positional argument: 'other'"
            raise TypeError(msg)

        other, *_deprecated = args
        parsed_other = self.with_segments(other, *_deprecated)
        return parsed_other == self or parsed_other in self.parents

    def joinpath(self, *args: PathElem) -> Self:
        """Appends one or more path-like objects and/or relative paths to self.

        If any path being joined is already absolute, it will override and replace self instead of join us.

        Args:
        ----
            self (Path object):
            key (path-like object or str path):
        """
        return self._create_instance(self, *args)

    def add_suffix(self, extension: str) -> Self:
        """Initialize a new path object with the added extension. Similar to with_suffix, but doesn't replace existing extensions."""
        extension = extension.strip()
        if not extension.startswith("."):
            extension = f".{extension}"
        return self._create_instance(str(self) + extension)

    @classmethod
    def with_segments(
        cls,
        *pathsegments: PathElem,
    ) -> Self:
        """Construct a new path object from any number of path-like objects.

        Subclasses may override this method to customize how new path objects
        are created from methods like `iterdir()`.
        """
        return cls._create_instance(*pathsegments)

    def with_stem(self, stem: str) -> Self:  # type: ignore[type-var, misc]
        """Return a new path with the stem changed."""
        self: PurePath = self  # type: ignore[]  # noqa: PLW0127, PLW0642
        return self.with_name(stem + self.suffix)  # type: ignore[return-value]

    def endswith(
        self,
        text: str | tuple[str, ...],
        *,
        case_sensitive: bool = False,
    ) -> bool:  # type: ignore[override]
        """Checks if string ends with the specified str or tuple of strings.

        Args:
        ----
            self: Path object
            text: String or tuple of strings to check.
            case_sensitive: Whether comparison should be case sensitive.

        Returns:
        -------
            bool: True if string ends with the text, False otherwise.

        Processing Logic:
        ----------------
            - If case sensitivity is not required, normalize self and text to lower case
            - Normalize each string in the tuple if text is a tuple
            - Utilize Python's built-in endswith method to check for text.
        """
        # If case sensitivity is not required, normalize the self string and the text to lower case
        if not case_sensitive:
            self_str: str = str(self).lower()

            # Normalize each string in the tuple if text is a tuple
            text = tuple(subtext.lower() for subtext in text) if isinstance(text, tuple) else text.lower()
        else:
            self_str = str(self)

        # Utilize Python's built-in endswith method
        return self_str.endswith(text)


class PurePosixPath(PurePath, pathlib.PurePosixPath):  # type: ignore[misc]
    if sys.version_info >= (3, 12):
        import posixpath as _posixpath
        _flavour = _posixpath  # noqa: SLF001  # pyright: ignore[reportAttributeAccessIssue]
    if sys.version_info >= (3, 13):
        class _PosixFlavourProxy:
            def __init__(self, module):
                self._module = module
                self.sep = module.sep
                self.altsep = getattr(module, "altsep", None)

            def __getattr__(self, name):
                return getattr(self._module, name)

        _flavour = _PosixFlavourProxy(_posixpath)


class PureWindowsPath(PurePath, pathlib.PureWindowsPath):  # type: ignore[misc]
    if sys.version_info >= (3, 12):
        import ntpath as _ntpath
        _flavour = _ntpath  # noqa: SLF001  # pyright: ignore[reportAttributeAccessIssue]
    if sys.version_info >= (3, 13):
        class _WindowsFlavourProxy:
            def __init__(self, module):
                self._module = module
                self.sep = module.sep
                self.altsep = getattr(module, "altsep", None)

            def __getattr__(self, name):
                return getattr(self._module, name)

        _flavour = _WindowsFlavourProxy(_ntpath)


class Path(PurePath, pathlib.Path):  # type: ignore[misc]
    if sys.version_info >= (3, 13):
        _flavour = PureWindowsPath._flavour if os.name == "nt" else PurePosixPath._flavour  # type: ignore[assignment]  # noqa: SLF001  # pyright: ignore[reportUnreachable]

    def __new__(cls, *args, **kwargs) -> Self:
        if cls is Path:
            cls = WindowsPath if os.name == "nt" else PosixPath  # type: ignore[assignment]  # noqa: PLW0642, SLF001
        return super().__new__(cls, *args, **kwargs)  # pyright: ignore[reportArgumentType, reportReturnType]

    def __init__(self, *args, **kwargs):
        self._last_stat_result: os.stat_result | None = None
        super().__init__(*args, **kwargs)

    def get_stat_with_cache(self) -> os.stat_result:
        """Returns the cached stat result if available, otherwise performs a stat call."""
        if self._last_stat_result is None:
            self._last_stat_result = super().stat()
        return self._last_stat_result

    def stat(self, *args, **kwargs) -> os.stat_result:
        self._last_stat_result = super().stat(*args, **kwargs)
        return self._last_stat_result

    # Safe rglob operation
    def safe_rglob(
        self,
        pattern: str,
    ) -> Generator[Self, Any, None]:
        iterator: Generator[Self, Any, None] = self.rglob(pattern)
        while True:
            try:
                yield next(iterator)
            except StopIteration:  # noqa: PERF203
                break  # StopIteration means there are no more files to iterate over
            except Exception:  # pylint: disable=W0718  # noqa: BLE001
                RobustLogger().debug("This exception has been suppressed and is only relevant for debug purposes.", exc_info=True)
                continue  # Ignore the file that caused an exception and move to the next

    # Safe iterdir operation
    def safe_iterdir(self) -> Generator[Self, Any, None]:
        iterator: Generator[Self, Any, None] = self.iterdir()
        while True:
            try:
                yield next(iterator)
            except StopIteration:  # noqa: PERF203
                break  # StopIteration means there are no more files to iterate over
            except Exception:  # pylint: disable=W0718  # noqa: BLE001
                RobustLogger().debug("This exception has been suppressed and is only relevant for debug purposes.", exc_info=True)
                continue  # Ignore the file that caused an exception and move to the next

    # Safe is_dir operation
    def safe_isdir(self) -> bool | None:
        check: bool | None = None
        try:
            check = self.is_dir()
        except (OSError, ValueError):
            #RobustLogger().debug("This exception has been suppressed and is only relevant for debug purposes.", exc_info=True)
            return None
        else:
            return check

    # Safe is_file operation
    def safe_isfile(self) -> bool | None:
        check: bool | None = None
        try:
            check = self.is_file()
        except (OSError, ValueError):
            #RobustLogger().debug("This exception has been suppressed and is only relevant for debug purposes.", exc_info=True)
            return None
        else:
            return check

    # Safe exists operation
    def safe_exists(self) -> bool | None:
        check: bool | None = None
        try:
            check = self.exists()
        except (OSError, ValueError):
            # RobustLogger().debug("This exception has been suppressed and is only relevant for debug purposes.", exc_info=True)
            return None
        else:
            return check

    def get_highest_permission(self) -> int:
        read_permission: bool = os.access(self, os.R_OK)
        write_permission: bool = os.access(self, os.W_OK)
        execute_permission: bool = os.access(self, os.X_OK)

        permission_value: int = 0o0
        if read_permission:
            permission_value += 0o4  # Add 4 for read permission (100 in binary)
        if write_permission:
            permission_value += 0o2  # Add 2 for write permission (010 in binary)
        if execute_permission:
            permission_value += 0o1  # Add 1 for execute permission (001 in binary)
        return permission_value

    def safe_relative_to(self, *other: PathElem) -> Self:
        with suppress(ValueError):
            return super().relative_to(*other)
        return self.__class__(os.path.relpath(self, self.__class__(*other)))

    def has_access(
        self,
        mode: int = 0o6,
        *,
        recurse: bool = False,
        filter_results: Callable[[Path], bool] | None = None,
    ) -> bool:
        """Check if the path has the specified access permissions.

        This function will catch and log all exceptions. Therefore this function is always safe.

        Args:
        ----
            mode (int): The permissions to check for. Defaults to 0o6.
            recurse (bool): Whether to recursively check permissions for all child paths. Defaults to False.
            filter_results (Callable[[Path], bool] | None): An optional function that's called to determine if a file/folder should be ignored when recursing.

        Returns:
        -------
            bool: True if the path has the specified access permissions, False otherwise.

        Examples:
        --------
            >>> path = Path('/my/path')
            >>> path.has_access(mode=0o6, recurse=False)
        """
        mode_to_str: dict[int, str | None] = {
            0o0: None,  # No permissions
            0o1: None,  # Execute only
            0o2: "w",  # Write only
            0o3: "w",  # Write and execute
            0o4: "r",  # Read only
            0o5: "r",  # Read and execute
            0o6: "r+",  # Read and write
            0o7: "r+",  # Read, write, and execute
        }
        try:
            if filter_results and not filter_results(self):
                return True  # ignore anything the filter deems ignorable.
            if not self.safe_exists():
                return False

            open_mode: str | None = mode_to_str[mode]
            if self.is_file():
                if open_mode is not None:
                    with self.open(open_mode) as _:  # on windows this will fail if the file has system/read-only attributes.
                        ...
                return self.get_highest_permission() >= mode  # check against os.access

            if self.is_dir():  # sourcery skip: extract-method
                test_path: Path = self / f"pyk_{uuid.uuid4().hex}.tmp"
                test_path.touch()
                if open_mode is not None:
                    with test_path.open(open_mode) as _:  # on windows this will fail if the file has system/read-only attributes.
                        ...
                test_path.unlink()

                if not recurse:
                    return True

                for file_or_folder in self.rglob("*"):
                    cur_access: bool = file_or_folder.has_access(mode, recurse=recurse, filter_results=filter_results)
                    if not cur_access:
                        return False
                return True
        except OSError as os_exc:
            print(format_exception_with_variables(os_exc))
        return False

    def gain_access(
        self,
        mode: int = 0o7,
        *,
        recurse: bool = True,
        resolve_symlinks: bool = False,
        log_func: Callable[[str], Any] = lambda s: s,
    ) -> bool:
        """Gain access to the path by changing its permissions.

        Args:
        ----
            mode (int): The permissions to set for the path. Defaults to 0o7. Checks against self.get_highest_permission()
                        Note: `mode` specifically sets the 'other' permission for chmod if chmod is necessary.
            recurse (bool): Whether to recursively change permissions for all child paths. Defaults to True.
            resolve_symlinks (bool): Whether to resolve symlinks when changing permissions. Defaults to False.
            log_func (Callable[[str], Any]): a custom optional function to use for logging purposes. must take a single str arg representing the message.

        Returns:
        -------
            bool: True if access is gained successfully, False otherwise.

        Raises:
        ------
            AssertionError: If self is not an instance of Path.

        Examples:
        --------
            >>> path = Path('/my/path')
            >>> path.gain_access(mode=0o7, recurse=True, resolve_symlinks=False)
        """
        if os.name == "posix":
            print("(Unix) Gain ownership of the folder with os.chown()")
            e: Exception | None = None
            try:
                home_path = Path.home()
                try:
                    stat_info = home_path.stat()
                except OSError as e:
                    print(format_exception_with_variables(e, message=f"Error accessing file information at path '{home_path}'"))
                    raise
                else:
                    os.chown(self, stat_info.st_uid, stat_info.st_gid)  # type: ignore[attr-defined]
            except (OSError, NotImplementedError) as e:
                print(format_exception_with_variables(e, message=f"Error during chown for '{self}'"))

        # (Any OS) chmod the folder
        print(f"Attempting pathlib.Path.chmod({self})...")
        try:
            # Get the current permissions
            current_permissions: int = self.stat().st_mode
            # Extract owner and group permissions
            owner_permissions: int = current_permissions & 0o700  # Extracts the first number of the octal (e.g. 0o7 in 0o750)
            group_permissions: int = current_permissions & 0o70  # Extracts the second number of the octal (e.g. 0o5 in 0o750)
            # Combine them with the new 'other' permissions
            new_permissions: int = owner_permissions | group_permissions | mode
            # Apply the new permissions
            if resolve_symlinks:
                self.chmod(new_permissions)
            else:
                try:
                    self.lchmod(new_permissions)
                except NotImplementedError:
                    self.chmod(new_permissions)
        except (OSError, NotImplementedError) as e:
            print(format_exception_with_variables(e, message=f"Error during chmod at path '{self}'"))

        success: bool = True
        if not self.has_access(mode, recurse=False) and os.name == "nt":
            log_func(f"No permissions to {self}, attempting native access fix...")
            try:
                self.request_native_access(elevate=False, recurse=recurse, log_func=log_func)
            except OSError as e:
                print(format_exception_with_variables(e, message=f"Error during platform-specific permission request at path '{self}'"))

            log_func("Checking access again before attempting elevated native access fix...")
            success = self.has_access(mode, recurse=False)
            if not success:
                log_func("Still no access permitted, attempting to elevate the native access fix...")
                try:
                    self.request_native_access(elevate=True, recurse=recurse, log_func=log_func)
                except OSError as e:
                    print(format_exception_with_variables(e, message=f"Error during elevated platform-specific permission request at path '{self}'"))

        if not success:
            log_func("Verifying the operations were successful...")
            success = self.has_access(mode, recurse=False)
        try:
            if recurse and self.safe_isdir():
                for child in self.iterdir():
                    result: bool = child.gain_access(mode, recurse=recurse, resolve_symlinks=resolve_symlinks, log_func=log_func)
                    if not result:
                        log_func(f"FAILED to gain access to '{child}'!")
                    success &= result
        except (OSError, NotImplementedError) as e:
            print(format_exception_with_variables(e, message=f"Error gaining access for children of path '{self}'"))
            success = False

        return success

    if os.name == "nt":

        @staticmethod
        def get_win_attrs(file_path: str) -> tuple[bool, bool, bool]:
            import ctypes

            # Constants for file attributes
            FILE_ATTRIBUTE_READONLY = 0x1
            FILE_ATTRIBUTE_HIDDEN = 0x2
            FILE_ATTRIBUTE_SYSTEM = 0x4
            # GetFileAttributesW is a Windows API function
            attrs = ctypes.windll.kernel32.GetFileAttributesW(file_path)

            # If the function fails, it returns INVALID_FILE_ATTRIBUTES
            if attrs == -1:
                import errno
                msg = "Cannot access attributes of the file"
                raise FileNotFoundError(errno.ENOENT, msg, str(file_path))

            # Check for specific attributes
            is_read_only = bool(attrs & FILE_ATTRIBUTE_READONLY)
            is_hidden = bool(attrs & FILE_ATTRIBUTE_HIDDEN)
            is_system = bool(attrs & FILE_ATTRIBUTE_SYSTEM)

            return is_read_only, is_hidden, is_system

        @classmethod
        def run_commands_as_admin(
            cls,
            cmd: list[str],
            *,
            pause_after_command: bool = False,
            hide_window: bool = True,
            block_until_complete: bool = True,
        ):
            # sourcery skip: extract-method
            with TemporaryDirectory() as tempdir:
                # Ensure the script path is absolute
                script_path: Path = cls(tempdir, "temp_script.bat").absolute()  # pyright: ignore[reportGeneralTypeIssues]
                script_path_str = str(script_path)

                # Write the commands to a batch file
                with script_path.open("w", encoding="utf-8") as file:
                    for command in cmd:
                        file.write(command + "\n")
                    if pause_after_command and not hide_window:
                        file.write("pause\nexit\n")

                # Determine the CMD switch to use
                cmd_switch = "/K" if pause_after_command else "/C"

                # Should hide window?
                if hide_window:
                    hide_window_cmdpart: str = " -WindowStyle Hidden"
                    creation_flags: int = subprocess.CREATE_NO_WINDOW
                else:
                    hide_window_cmdpart = ""
                    creation_flags = 0

                # Use shlex to escape arguments properly
                run_script_cmd = [
                    "Powershell",
                    "-Command",
                    f"Start-Process cmd.exe -ArgumentList {shlex.quote(f'{cmd_switch} {script_path_str}')}"
                    f" -Verb RunAs{hide_window_cmdpart} -Wait",
                ]

                # Execute the batch script
                if block_until_complete:
                    subprocess.run(run_script_cmd, check=False, creationflags=creation_flags, timeout=5)  # noqa: S603
                else:
                    subprocess.Popen(run_script_cmd, creationflags=creation_flags, timeout=5)  # noqa: S603  # pyright: ignore[reportCallIssue]

            # Delete the batch script after execution
            with suppress(Exception):
                if script_path.safe_isfile():
                    script_path.unlink(missing_ok=True)

        # Inspired by the C# code provided by KOTORModSync at https://github.com/th3w1zard1/KOTORModSync
        def request_native_access(
            self: Path,  # pyright: ignore[reportGeneralTypeIssues]
            *,
            elevate: bool = False,
            recurse: bool = True,
            log_func: Callable[[str], Any] | None = None,
        ):
            if log_func is None:
                log_func = print
            self_path_str = str(self.absolute())
            if elevate:
                self_path_str = f'"{self_path_str}"'
            isdir_check: bool | None = self.safe_isdir()
            commands: list[str] = []

            print(f"Step 1: Resetting permissions and re-enabling inheritance for {self_path_str}...")
            icacls_reset_args: list[str] = ["icacls", self_path_str, "/reset", "/Q"]
            if isdir_check and recurse:
                icacls_reset_args.append("/T")
            if elevate:
                commands.append(" ".join(icacls_reset_args))
            else:
                icacls_reset_result: subprocess.CompletedProcess[str] = subprocess.run(icacls_reset_args, timeout=60, check=False, capture_output=True, text=True)  # noqa: S603
                if icacls_reset_result.returncode != 0:
                    log_func(
                        f"Failed reset permissions of {self_path_str}:\n"
                        f"exit code: {icacls_reset_result.returncode}\n"
                        f"stdout: {icacls_reset_result.stdout}\n"
                        f"stderr: {icacls_reset_result.stderr}",
                    )
                elif icacls_reset_result.stdout.strip():
                    log_func(icacls_reset_result.stdout)

            print(f"Step 2: Attempt to take ownership of the target {self_path_str}...")
            takeown_args: list[str] = ["takeown", "/F", self_path_str, "/SKIPSL"]
            if isdir_check:
                takeown_args.extend(("/D", "Y"))
                if recurse:
                    takeown_args.append("/R")
            if elevate:
                commands.append(" ".join(takeown_args))
            else:
                takeown_result: subprocess.CompletedProcess[str] = subprocess.run(takeown_args, timeout=60, check=False, capture_output=True, text=True)  # noqa: S603
                if takeown_result.returncode != 0:
                    log_func(
                        f"Failed to take ownership of {self_path_str}:\n"
                        f"exit code: {takeown_result.returncode}\n"
                        f"stdout: {takeown_result.stdout}\n"
                        f"stderr: {takeown_result.stderr}",
                    )
                elif takeown_result.stdout.strip():
                    log_func(takeown_result.stdout)

            print(f"Step 3: Attempting to set access rights of the target {self_path_str} using icacls...")
            icacls_args: list[str] = ["icacls", self_path_str, "/grant", "*S-1-1-0:(OI)(CI)F", "/C", "/L", "/Q"]
            if recurse:
                icacls_args.append("/T")
            if elevate:
                commands.append(" ".join(icacls_args))
            else:
                icacls_result: subprocess.CompletedProcess[str] = subprocess.run(icacls_args, timeout=60, check=False, capture_output=True, text=True)  # noqa: S603
                if icacls_result.returncode != 0:
                    log_func(
                        f"Could not set Windows icacls permissions at '{self_path_str}':\n"
                        f"exit code: {icacls_result.returncode}\n"
                        f"stdout: {icacls_result.stdout}\n"
                        f"stderr: {icacls_result.stderr}",
                    )
                else:
                    log_func(f"Permissions set successfully. Output:\n{icacls_result.stdout}")

            print(f"Step 4: Removing system/hidden/read-only attribute from '{self_path_str}'...")
            _is_read_only, is_hidden, is_system = self.get_win_attrs(self_path_str.replace('"', ""))
            attrib_args: list[str] = ["attrib", "-R", self_path_str]
            if is_system:
                attrib_args.insert(1, "-S")
            elif is_hidden:
                attrib_args.insert(1, "-H")
            if isdir_check:
                attrib_args.append("/D")
                if recurse:
                    attrib_args.append("/S")
            if elevate:
                commands.append(" ".join(attrib_args))
            else:
                attrib_result: subprocess.CompletedProcess[str] = subprocess.run(attrib_args, timeout=60, check=False, capture_output=True, text=True)  # noqa: S603
                if attrib_result.returncode != 0:
                    log_func(
                        f"Could not set Windows icacls permissions at '{self_path_str}':\n"
                        f"exit code: {attrib_result.returncode}\n"
                        f"stdout: {attrib_result.stdout}\n"
                        f"stderr: {attrib_result.stderr}",
                    )
                else:
                    log_func(f"Permissions set successfully. Output:\n{attrib_result.stdout}")

            if is_hidden:
                print(f"Step 4.5: Re-apply the hidden attribute to {self_path_str}...")
                rehide_args: list[str] = ["attrib", "+H", self_path_str]
                if isdir_check:
                    rehide_args.append("/D")
                    if recurse:
                        rehide_args.append("/S")
                if elevate:
                    commands.append(" ".join(rehide_args))
                else:
                    rehide_result: subprocess.CompletedProcess[str] = subprocess.run(rehide_args, timeout=60, check=False, capture_output=True, text=True)  # noqa: S603
                    if rehide_result.returncode != 0:
                        log_func(
                            f"Could not set Windows icacls permissions at '{self_path_str}':\n"
                            f"exit code: {rehide_result.returncode}\n"
                            f"stdout: {rehide_result.stdout}\n"
                            f"stderr: {rehide_result.stderr}",
                        )

            if elevate:
                self.run_commands_as_admin(commands)
                return


class PosixPath(Path):  # type: ignore[misc]
    if sys.version_info < (3, 12):
        # In Python 3.12+, _flavour attribute was removed
        _flavour = pathlib.PurePosixPath._flavour  # noqa: SLF001  # pyright: ignore[reportAttributeAccessIssue]
    if sys.version_info >= (3, 13):
        _flavour = PurePosixPath._flavour  # noqa: SLF001


class WindowsPath(Path):  # type: ignore[misc]
    if sys.version_info < (3, 12):
        # In Python 3.12+, _flavour attribute was removed
        _flavour = pathlib.PureWindowsPath._flavour  # noqa: SLF001  # pyright: ignore[reportAttributeAccessIssue]
    if sys.version_info >= (3, 13):
        _flavour = PureWindowsPath._flavour  # noqa: SLF001



class ChDir:
    def __init__(
        self,
        path: os.PathLike | str,
        logger: Logger | None = None,
    ):
        self.old_dir: Path = Path.cwd()
        self.new_dir: Path = Path.pathify(path)
        self.log = logger or RobustLogger()

    def __enter__(self):
        self.log.debug(f"Changing to Directory --> '{self.new_dir}'")  # noqa: G004
        os.chdir(self.new_dir)

    def __exit__(self, *args, **kwargs):
        self.log.debug(f"Moving back to Directory --> '{self.old_dir}'")  # noqa: G004
        os.chdir(self.old_dir)
