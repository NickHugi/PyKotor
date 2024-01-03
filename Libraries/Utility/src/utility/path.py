from __future__ import annotations

import contextlib
import os
import pathlib
import platform
import re
import uuid
from typing import Any, Callable, Generator, TypeVar, Union

PathElem = Union[str, os.PathLike]

def override_to_pathlib(cls):
    if cls == PurePath:
        return pathlib.PurePath
    if cls == PureWindowsPath:
        return pathlib.PureWindowsPath
    if cls == PurePosixPath:
        return pathlib.PurePosixPath
    if cls == Path:
        return pathlib.Path
    if cls == WindowsPath:
        return pathlib.WindowsPath
    if cls == PosixPath:
        return pathlib.PosixPath
    return cls

def pathlib_to_override(cls):
    if cls == pathlib.PurePath:
        return PurePath
    if cls == pathlib.PureWindowsPath:
        return PureWindowsPath
    if cls == pathlib.PurePosixPath:
        return PurePosixPath
    if cls == pathlib.Path:
        return Path
    if cls == pathlib.WindowsPath:
        return WindowsPath
    if cls == pathlib.PosixPath:
        return PosixPath
    return cls

class PurePathType(type):
    def __instancecheck__(cls, instance): # sourcery skip: instance-method-first-arg-name
        instance_type = type(instance)
        mro = instance_type.__mro__
        if cls in (pathlib.PurePath, PurePath):
            return BasePurePath in mro or override_to_pathlib(cls) in override_to_pathlib(instance_type).__mro__
        if cls in (pathlib.Path, Path):
            return BasePath in mro or override_to_pathlib(cls) in override_to_pathlib(instance_type).__mro__
        return cls in mro

    def __subclasscheck__(cls, subclass): # sourcery skip: instance-method-first-arg-name
        mro = subclass.__mro__
        if cls in (pathlib.PurePath, PurePath):
            return BasePurePath in mro or override_to_pathlib(cls) in override_to_pathlib(subclass).__mro__
        if cls in (pathlib.Path, Path):
            return BasePath in mro or override_to_pathlib(cls) in override_to_pathlib(subclass).__mro__
        return cls in mro

class BasePurePath(metaclass=PurePathType):  # type: ignore[misc]
    """BasePath is a class created to fix some annoyances with pathlib, such as its refusal to resolve mixed/repeating/trailing slashes."""

    @classmethod
    def _get_sep(cls):
        return cls._flavour.sep  # type: ignore[attr-defined]

    @classmethod
    def _create_super_instance(cls, *args, **kwargs):
        # Create the pathlib class instance, ignore the type errors in super().__new__
        arg_pathlib_instance = super().__new__(cls, *args, **kwargs)  # type: ignore[call-arg]
        arg_pathlib_instance.__init__(*args, _called_from_pathlib=False)  # type: ignore[misc]
        return arg_pathlib_instance

    @classmethod
    def _create_instance(cls, *args, **kwargs):
        instance = cls.__new__(cls, *args, **kwargs)
        instance.__init__(*args, **kwargs)
        return instance

    @classmethod
    def parse_args(cls, args: tuple[PathElem, ...]) -> list[BasePurePath]:
        args_list = list(args)
        for i, arg in enumerate(args_list):
            if isinstance(arg, BasePurePath):
                continue  # do nothing if already our instance type

            formatted_path_str = cls._fix_path_formatting(cls._fspath_str(arg), slash=cls._get_sep())
            if formatted_path_str.endswith(":") and "/" not in formatted_path_str and "\\" not in formatted_path_str:
                formatted_path_str = f"{formatted_path_str}{cls._get_sep()}"  # HACK: fix later

            args_list[i] = formatted_path_str

        return args_list  # type: ignore[return-value]

    def __new__(cls, *args: PathElem, **kwargs):
        return (
            args[0]
            if len(args) == 1 and args[0].__class__ == cls and isinstance(args[0], cls)
            else super().__new__(cls, *cls.parse_args(args), **kwargs)
        )

    def __init__(self, *args, _called_from_pathlib=True):
        """Initializes a path object. This is used to unify python 3.7-3.11 with most of python 3.12's changes.

        Args:
        ----
            *args (os.PathLike | str): the path parts to join and create a path object out of.

        Returns:
        -------
            A constructed Path object

        Processing Logic:
        ----------------
            - Finds the next class in the MRO that defines __init__ and is not BasePurePath
            - Return immediately (do nothing here) if the next class with a __init__ is the object class
            - Gets the __init__ method from the found class
            - Parses args if called from pathlib and calls __init__ with parsed args
            - Else directly calls __init__ with passed args.
        """
        next_init_method_class = next(
            (cls for cls in self.__class__.mro() if "__init__" in cls.__dict__ and cls is not BasePurePath),
            self.__class__,
        )
        # Check if the class that defines the next __init__ is object
        if next_init_method_class is object:
            return

        # If not object, fetch the __init__ of that class
        init_method = next_init_method_class.__init__  # type: ignore[misc]

        # Parse args if called from pathlib (Python 3.12+)
        if _called_from_pathlib:
            init_method(self, *self.parse_args(args))
        else:
            init_method(self, *args)

        self._cache_str: str = self._fix_path_formatting(super().__str__())
        assert not self._cache_str.startswith("C:Users")
        self._cache_windows_str: str = self._fix_path_formatting(super().__str__().lower(), slash="\\")
        self._cache_posix_str: str = self._fix_path_formatting(super().__str__(), slash="/")

    @staticmethod
    def _fix_path_formatting(
        str_path: str,
        *,
        slash=os.sep,
    ) -> str:
        """Formats a path string.

        Args:
        ----
            str_path (str): The path string to format
            slash (str): The path separator character

        Returns:
        -------
            str: The formatted path string

        Processing Logic:
        ----------------
            1. Validate the slash character
            2. Strip quotes from the path
            3. Format Windows paths by replacing mixed slashes and normalizing slashes
            4. Format Unix paths by replacing mixed slashes and normalizing slashes
            5. Strip trailing slashes from the formatted path.
        """
        if slash not in ("\\", "/"):
            msg = f"Invalid slash str: '{slash}'"
            raise ValueError(msg)

        formatted_path: str = str_path.strip('"')
        if not formatted_path.strip():
            return formatted_path

        # For Windows paths
        if slash == "\\":
            # Fix mixed slashes, replacing all forwardslashes with backslashes
            formatted_path = formatted_path.replace("/", "\\")
            # Replace 3 or more leading slashes with two backslashes
            formatted_path = re.sub(r"^\\{3,}", r"\\\\", formatted_path)
            # Replace repeating non-leading slashes with a single backslash
            formatted_path = re.sub(r"(?<!^)\\+", r"\\", formatted_path)
        # For Unix-like paths
        elif slash == "/":
            # Fix mixed slashes, replacing all backslashes with forwardslashes
            formatted_path = formatted_path.replace("\\", "/")
            # Replace multiple forwardslash's with a single forwardslash
            formatted_path = re.sub(r"/{2,}", "/", formatted_path)

        # Strip any trailing slashes, don't call rstrip if the formatted path == "/"
        if len(formatted_path) != 1:
            formatted_path = formatted_path.rstrip(slash)
        return formatted_path

    @staticmethod
    def _fspath_str(arg: object) -> str:
        """Convert object to a file system path string.

        Args:
        ----
            arg: Object to convert to a file system path string

        Returns:
        -------
            str: File system path string

        Processing Logic:
        ----------------
            - Check if arg is already a string
            - Check if arg has a __fspath__ method and call it
            - Check if arg somehow inherits os.PathLike despite not having __fspath__ (redundant)
            - Raise TypeError if arg is neither string nor has __fspath__ method.
        """
        if isinstance(arg, str):
            return arg

        fspath_method: Callable | None = getattr(arg, "__fspath__", None)
        if fspath_method is not None:
            return fspath_method()
        if isinstance(arg, os.PathLike):
            return str(arg)

        msg = f"Object '{arg!r}' must be str, or path-like object (implementing __fspath__). Instead got type '{type(arg)}'"
        raise TypeError(msg)

    def __str__(self) -> str:
        """Return the result from _fix_path_formatting that was initialized."""
        return self.as_posix() if self._get_sep() == "/" else self._cache_str

    def __repr__(self):
        return f"{self.__class__.__name__}({self})"

    def __eq__(self, __value):
        if isinstance(__value, (bytes, bytearray, memoryview)):
            return os.fsencode(self) == __value

        self_compare = self
        other_compare = __value
        if isinstance(__value, (os.PathLike, str)):
            self_compare = str(self)
            if isinstance(__value, PurePath):
                other_compare = str(__value)
            else:
                other_compare = self._fix_path_formatting(self._fspath_str(__value), slash=self._get_sep())

            if self._get_sep() == "\\":
                self_compare = self_compare.lower()
                other_compare = other_compare.lower()

        return self_compare == other_compare

    def __hash__(self):
        return hash(self.as_posix() if self._get_sep() == "/" else self.as_windows())

    def __bytes__(self):
        """Return the bytes representation of the path.  This is only
        recommended to use under Unix.
        """
        return os.fsencode(self)

    def __fspath__(self) -> str:
        """Ensures any use of __fspath__ will call our __str__ method."""
        return str(self)

    def __truediv__(self, key: PathElem):
        """Appends a path part when using the divider operator '/'.
        This method is called when the left side is self.

        If key is already absolute, it will override and replace self instead of join us.

        Args:
        ----
            self: Path object
            key (path-like object or str path):
        """
        return self._create_instance(self, key)

    def __rtruediv__(self, key: PathElem):
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
        return self._fix_path_formatting(f"{self}/{key}", slash=self._get_sep())

    def __radd__(self, key: PathElem) -> str:
        """Implicitly converts the path to a str when used with the addition operator '+'.
        This method is called when the right side is self.

        Args:
        ----
            self: Path object
            key (path-like object or str path):
        """
        return self._fix_path_formatting(f"{key}/{self}", slash=self._get_sep())

    @classmethod
    def pathify(cls, path: PathElem):
        return path if isinstance(path, cls) else cls(path)

    def split_filename(self, dots: int = 1) -> tuple[str, str]:
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

        self_path = self
        if not isinstance(self_path, PurePath):
            msg = f"self must be a path, got {self_path!r}"
            raise NotImplementedError(msg)

        parts: list[str]
        if dots < 0:
            parts = self_path.name.split(".", abs(dots))
            parts.reverse()  # Reverse the order of parts for negative dots
        else:
            parts = self_path.name.rsplit(".", abs(dots) + 1)

        if len(parts) <= abs(dots):
            first_dot = self_path.name.find(".")
            return (
                (self_path.name[:first_dot], self_path.name[first_dot + 1:])
                if first_dot != -1
                else (self_path.name, "")
            )

        return ".".join(parts[:-abs(dots)]), ".".join(parts[-abs(dots):])

    def as_posix(self):
        """Convert path to a POSIX path.

        Args:
        ----
            self: Path object

        Returns:
        -------
            str: POSIX representation of the path
        """
        return self._cache_posix_str

    def as_windows(self) -> str:
        """Convert path to a WINDOWS path, lowercasing the whole path and returning a str.

        Args:
        ----
            self: Path object

        Returns:
        -------
            str: POSIX representation of the path
        """
        return self._cache_windows_str

    def joinpath(self, *args: PathElem):
        """Appends one or more path-like objects and/or relative paths to self.

        If any path being joined is already absolute, it will override and replace self instead of join us.

        Args:
        ----
            self (Path object):
            key (path-like object or str path):
        """
        return self._create_instance(self, *args)

    def add_suffix(self, extension: str):
        """Initialize a new path object with the added extension. Similar to with_suffix, but doesn't replace existing extensions."""
        extension = extension.strip()
        if not extension.startswith("."):
            extension = f".{extension}"
        return self._create_instance(str(self) + extension)

    def with_segments(self, *pathsegments):
        """Construct a new path object from any number of path-like objects.

        Subclasses may override this method to customize how new path objects
        are created from methods like `iterdir()`.
        """
        return self._create_instance(*pathsegments)

    def with_stem(self, stem):
        """Return a new path with the stem changed."""

        self_path = self
        if not isinstance(self_path, PurePath):
            msg = f"self must be a path, got {self_path!r}"
            raise NotImplementedError(msg)

        return self_path.with_name(stem + self_path.suffix)

    def endswith(self, text: str | tuple[str, ...], case_sensitive: bool = False) -> bool:  # type: ignore[override]
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
            self_str = str(self).lower()

            # Normalize each string in the tuple if text is a tuple
            text = tuple(subtext.lower() for subtext in text) if isinstance(text, tuple) else text.lower()
        else:
            self_str = str(self)

        # Utilize Python's built-in endswith method
        return self_str.endswith(text)

class PurePath(BasePurePath, pathlib.PurePath):  # type: ignore[misc]
    # pylint: disable-all
    _flavour = pathlib.PureWindowsPath._flavour if os.name == "nt" else pathlib.PurePosixPath._flavour  # type: ignore[attr-defined]

class PurePosixPath(BasePurePath, pathlib.PurePosixPath):  # type: ignore[misc]
    ...

class PureWindowsPath(BasePurePath, pathlib.PureWindowsPath):  # type: ignore[misc]
    ...

T = TypeVar("T", bound="BasePath")
class BasePath(BasePurePath):

    # Safe rglob operation
    def safe_rglob(self: T, pattern: str) -> Generator[T, Any, None]:
        if not isinstance(self, Path):
            msg = f"self must be a path, got {self!r}"
            raise NotImplementedError(msg)
        with contextlib.suppress(Exception):
            yield from self.rglob(pattern)  # type: ignore[misc]

    # Safe iterdir operation
    def safe_iterdir(self: T) -> Generator[T, Any, None]:
        if not isinstance(self, Path):
            msg = f"self must be a path, got {self!r}"
            raise NotImplementedError(msg)
        with contextlib.suppress(Exception):
            yield from self.iterdir()  # type: ignore[misc]

    # Safe is_dir operation
    def safe_isdir(self) -> bool:
        if not isinstance(self, Path):
            msg = f"self must be a path, got {self!r}"
            raise NotImplementedError(msg)
        try:
            return self.is_dir()
        except Exception:  # noqa: BLE001
            return False

    # Safe is_file operation
    def safe_isfile(self) -> bool:
        if not isinstance(self, Path):
            msg = f"self must be a path, got {self!r}"
            raise NotImplementedError(msg)
        try:
            return self.is_file()
        except Exception:  # noqa: BLE001
            return False

    # Safe exists operation
    def safe_exists(self) -> bool:
        if not isinstance(self, Path):
            msg = f"self must be a path, got {self!r}"
            raise NotImplementedError(msg)
        try:
            return self.exists()
        except Exception:  # noqa: BLE001
            return False

    # Safe stat operation
    def safe_stat(self, *args, **kwargs):
        if not isinstance(self, Path):
            msg = f"self must be a path, got {self!r}"
            raise NotImplementedError(msg)
        try:
            return self.stat(*args, **kwargs)
        except Exception:  # noqa: BLE001
            return None

    # Safe open operation
    def safe_open(self, *args, **kwargs):
        if not isinstance(self, Path):
            msg = f"self must be a path, got {self!r}"
            raise NotImplementedError(msg)
        try:
            return self.open(*args, **kwargs)
        except Exception:  # noqa: BLE001
            return None

    def has_access(self, recurse=False) -> bool:
        """Check if we have access to the path.

        Args:
        ----
            recurse (bool): check access for all files inside of self. Only valid if self is a folder (default is False)

        Returns:
        -------
            True if path can be modified, False otherwise.
        """
        if not isinstance(self, Path):
            msg = f"self must be a path, got {self!r}"
            raise NotImplementedError(msg)
        try:
            path_obj = Path(self)  # prevents usage of CaseAwarePath's wrappers
            if path_obj.is_dir():  # sourcery skip: extract-method
                test_path: Path = path_obj / f"temp_test_file_{uuid.uuid4().hex}.tmp"
                with test_path.open("w") as f:
                    f.write("test")
                test_path.unlink()
                success = True
                if recurse:
                    for file_or_folder in path_obj.rglob("*"):
                        success &= file_or_folder.has_access()
                return success
            if path_obj.is_file():
                return os.access(path_obj, os.R_OK) and os.access(path_obj, os.W_OK)
        except Exception:  # noqa: BLE001
            return False
        return False

    def gain_access(self, mode=0o777, owner_uid=-1, owner_gid=-1, recurse=True) -> bool:
        if not isinstance(self, Path):
            msg = f"self must be a path, got {self!r}"
            raise NotImplementedError(msg)
        path_obj = Path(self)  # prevents usage of CaseAwarePath's wrappers
        # (Unix) Gain ownership of the folder
        if os.name != "nt" and (owner_uid != -1 or owner_gid != -1) and not path_obj.has_access():
            try:
                os.chown(path_obj, owner_uid, owner_gid)  # type: ignore[attr-defined]
            except Exception as e:  # noqa: BLE001
                print(f"Error during chown for {path_obj}: {e}")

        # chmod the folder
        if not path_obj.has_access():
            try:
                path_obj.chmod(mode)
            except Exception as e:  # noqa: BLE001
                print(f"Error during chmod for {path_obj}: {e}")

        # TODO: prompt the user and gain access with os-native methods.
        if not path_obj.has_access():
            try:
                if platform.system() == "Darwin":
                    path_obj.request_mac_permission()
                elif platform.system() == "Linux":
                    path_obj.request_linux_permission()
                elif platform.system() == "Windows":
                    path_obj.request_windows_permission()

            except Exception as e:  # noqa: BLE001
                print(f"Error during platform-specific permission request for {path_obj}: {e}")

        success: bool = path_obj.has_access()
        try:
            if recurse and path_obj.is_dir():
                for child in path_obj.iterdir():
                    success &= child.gain_access(mode, owner_uid, owner_gid)
        except Exception as e:  # noqa: BLE001
            print(f"Error gaining access for children of {path_obj}: {e}")
            success = False

        return success


class Path(BasePath, pathlib.Path):  # type: ignore[misc]
    # pylint: disable-all
    _flavour = pathlib.PureWindowsPath._flavour if os.name == "nt" else pathlib.PurePosixPath._flavour  # type: ignore[attr-defined]


class PosixPath(BasePath, pathlib.PosixPath):  # type: ignore[misc]
    pass


class WindowsPath(BasePath, pathlib.WindowsPath):  # type: ignore[misc]
    pass
