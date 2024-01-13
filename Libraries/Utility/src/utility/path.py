from __future__ import annotations

import os
import pathlib
import platform
import re
import uuid
from typing import TYPE_CHECKING, Any, Callable, Generator, Union

from utility.error_handling import format_exception_with_variables

if TYPE_CHECKING:
    from typing_extensions import Self

PathElem = Union[str, os.PathLike]

def override_to_pathlib(cls: type):
    # sourcery skip: assign-if-exp, reintroduce-else
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

class PurePathType(type):
    def __instancecheck__(cls, instance: object) -> bool: # sourcery skip: instance-method-first-arg-name
        return cls.__subclasscheck__(type(instance))

    def __subclasscheck__(cls, subclass: type) -> bool: # sourcery skip: instance-method-first-arg-name
        return override_to_pathlib(cls) in override_to_pathlib(subclass).__mro__

class BasePurePath(metaclass=PurePathType):  # type: ignore[misc]
    """BasePath is a class created to fix some annoyances with pathlib, such as its refusal to resolve mixed/repeating/trailing slashes."""

    @classmethod
    def _get_sep(cls) -> str:
        return cls._flavour.sep  # type: ignore[attr-defined]

    @classmethod
    def _create_super_instance(cls, *args, **kwargs) -> Self:
        # Create the pathlib class instance, ignore the type errors in super().__new__
        arg_pathlib_instance: Self = super().__new__(cls, *args, **kwargs)  # type: ignore[call-arg]
        arg_pathlib_instance.__init__(*args, _called_from_pathlib=False)  # type: ignore[misc]
        return arg_pathlib_instance

    @classmethod
    def _create_instance(cls, *args, **kwargs) -> Self:
        instance: Self = cls.__new__(cls, *args, **kwargs)
        instance.__init__(*args, **kwargs)  # type: ignore[misc]
        return instance

    @classmethod
    def parse_args(
        cls,
        args: tuple[PathElem, ...],
    ) -> list[PathElem]:
        args_list = list(args)
        for i, arg in enumerate(args_list):
            if isinstance(arg, BasePurePath):
                continue  # Do nothing if already our instance type

            formatted_path_str: str = cls._fix_path_formatting(cls._fspath_str(arg), slash=cls._get_sep())
            if formatted_path_str.endswith(":") and "/" not in formatted_path_str and "\\" not in formatted_path_str:
                formatted_path_str = f"{formatted_path_str}{cls._get_sep()}"  # HACK: cleanup later

            args_list[i] = formatted_path_str

        return args_list  # type: ignore[return-value]

    def __new__(cls, *args: PathElem, **kwargs) -> Self:
        return (
            args[0]  # type: ignore[return-value]
            if len(args) == 1 and args[0].__class__ == cls
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
        next_init_method_class: type | type[Self] = next(
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
            slash (str): The path separator character (kwarg)

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

    def __str__(self):
        """Return the result from _fix_path_formatting that was initialized."""
        return self.as_posix() if self._get_sep() == "/" else self._fix_path_formatting(super().__str__(), slash="\\")

    def __repr__(self):
        return f"{self.__class__.__name__}({self})"

    def __eq__(self, __value):
        if isinstance(__value, (bytes, bytearray, memoryview)):
            return os.fsencode(self) == __value

        self_compare: Self | str = self  # type: ignore[assignment]
        other_compare: object = __value
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
        return self._fix_path_formatting(str(self / key), slash=self._get_sep())

    def __radd__(self, key: PathElem) -> str:
        """Implicitly converts the path to a str when used with the addition operator '+'.
        This method is called when the right side is self.

        Args:
        ----
            self: Path object
            key (path-like object or str path):
        """
        return self._fix_path_formatting(str(key / self), slash=self._get_sep())

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
            return (
                (self.name[:first_dot], self.name[first_dot + 1:])
                if first_dot != -1
                else (self.name, "")
            )

        return ".".join(parts[:-abs(dots)]), ".".join(parts[-abs(dots):])

    def as_posix(self) -> str:
        """Convert path to a POSIX path.

        Args:
        ----
            self: Path object

        Returns:
        -------
            str: POSIX representation of the path
        """
        return self._fix_path_formatting(super().__str__(), slash="/")

    def as_windows(self) -> str:
        """Convert path to a WINDOWS path, lowercasing the whole path and returning a str.

        Args:
        ----
            self: Path object

        Returns:
        -------
            str: POSIX representation of the path
        """
        return self._fix_path_formatting(super().__str__(), slash="\\").lower()

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
    def with_segments(cls, *pathsegments) -> Self:
        """Construct a new path object from any number of path-like objects.

        Subclasses may override this method to customize how new path objects
        are created from methods like `iterdir()`.
        """
        return cls._create_instance(*pathsegments)

    def with_stem(self: PurePath, stem) -> Self:  # type: ignore[type-var, misc]
        """Return a new path with the stem changed."""
        return self.with_name(stem + self.suffix)  # type: ignore[return-value]

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
            self_str: str = str(self).lower()

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

class BasePath(BasePurePath):

    # Safe rglob operation
    def safe_rglob(  # type: ignore[misc]
        self: Path,  # type: ignore[reportGeneralTypeIssues]
        pattern: str,
    ) -> Generator[Self, Any, None]:  # type: ignore[reportGeneralTypeIssues]
        try:
            iterator: Generator[Self, Any, None] = self.rglob(pattern)  # type: ignore[assignment, reportGeneralTypeIssues]
        except Exception:  # noqa: BLE001
            print(format_exception_with_variables(e,  ___message___="This exception has been suppressed and is only relevant for debug purposes."))
            return
        while True:
            try:
                yield next(iterator)  # type: ignore[misc, reportGeneralTypeIssues]
            except StopIteration:  # noqa: PERF203
                break  # StopIteration means there are no more files to iterate over
            except Exception as e:  # noqa: BLE001
                print(format_exception_with_variables(e,  ___message___="This exception has been suppressed and is only relevant for debug purposes."))
                continue  # Ignore the file that caused an exception and move to the next

    # Safe iterdir operation
    def safe_iterdir(  # type: ignore[misc]
        self: Path,  # type: ignore[reportGeneralTypeIssues]
    ) -> Generator[Self, Any, None]:  # type: ignore[reportGeneralTypeIssues]
        try:
            iterator: Generator[Self, Any, None] = self.iterdir()  # type: ignore[assignment, reportGeneralTypeIssues]
        except Exception:  # noqa: BLE001
            print(format_exception_with_variables(e,  ___message___="This exception has been suppressed and is only relevant for debug purposes."))
            return
        while True:
            try:
                yield next(iterator)  # type: ignore[misc, reportGeneralTypeIssues]
            except StopIteration:  # noqa: PERF203
                break  # StopIteration means there are no more files to iterate over
            except Exception as e:  # noqa: BLE001
                print(format_exception_with_variables(e,  ___message___="This exception has been suppressed and is only relevant for debug purposes."))
                continue  # Ignore the file that caused an exception and move to the next

    # Safe is_dir operation
    def safe_isdir(self: Path) -> bool | None:  # type: ignore[misc]
        try:
            return self.is_dir()
        except Exception as e:  # noqa: BLE001
            print(format_exception_with_variables(e,  ___message___="This exception has been suppressed and is only relevant for debug purposes."))
        return None

    # Safe is_file operation
    def safe_isfile(self: Path) -> bool | None:  # type: ignore[misc]
        try:
            return self.is_file()
        except Exception as e:  # noqa: BLE001
            print(format_exception_with_variables(e,  ___message___="This exception has been suppressed and is only relevant for debug purposes."))
        return None

    # Safe exists operation
    def safe_exists(self: Path) -> bool | None:  # type: ignore[misc]
        try:
            return self.exists()
        except Exception as e:  # noqa: BLE001
            print(format_exception_with_variables(e,  ___message___="This exception has been suppressed and is only relevant for debug purposes."))
        return None

    def relative_to(self: Path, *args, walk_up=False, **kwargs) -> Self:  # type: ignore[misc]
        if not args or "other" in kwargs:
            raise TypeError("relative_to() missing 1 required positional argument: 'other'")  # noqa: EM101

        other, *_deprecated = args
        parsed_other = self.with_segments(other, *_deprecated)
        for step, path in enumerate([parsed_other, *list(parsed_other.parents)]):  # noqa: B007
            if self.is_relative_to(path):
                break
            if not walk_up:
                raise ValueError(f"{str(self)!r} is not in the subpath of {str(parsed_other)!r}")
            if path.name == "..":
                raise ValueError(f"'..' segment in {str(parsed_other)!r} cannot be walked")
        else:
            raise ValueError(f"{str(self)!r} and {str(parsed_other)!r} have different anchors")

        parts: list[str] = [".."] * step + list(self.parts[step:])
        return self.with_segments(*parts)  # type: ignore[return-value]

    def is_relative_to(self: Path, *args, **kwargs) -> bool:  # type: ignore[misc]
        """Return True if the path is relative to another path or False."""
        if not args or "other" in kwargs:
            raise TypeError(f"{type(self)}.is_relative_to() missing 1 required positional argument: 'other'")

        other, *_deprecated = args
        parsed_other = self.with_segments(other, *_deprecated)
        return parsed_other == self or parsed_other in self.parents

    def get_highest_permission(
        self: Path,  # type: ignore[reportGeneralTypeIssues]
        uid: int | None = None,
        gid: int | None = None,
    ) -> int:
        if os.name == "posix":
            # Retrieve the current user's UID and GID
            current_uid = uid if uid is not None else os.getuid()
            current_gid = gid if gid is not None else os.getgid()

            # Retrieve the UID and GID of the owner of the path_obj
            stat_info = self.stat()
            owner_uid: int = stat_info.st_uid
            owner_gid: int = stat_info.st_gid

            # Extract user, group, and other permissions from mode
            mode: int = stat_info.st_mode
            group_perms: int = (mode >> 3) & 0o7
            other_perms: int = mode & 0o7

            # Determine the highest permission level
            if owner_uid == current_uid:
                user_perms: int = (mode >> 6) & 0o7
                if owner_gid == current_gid:
                    return max(user_perms, group_perms, other_perms)
                return max(user_perms, other_perms)
            if owner_gid == current_gid:
                return max(group_perms, other_perms)

        if os.name == "nt":
            read_permission: bool = os.access(self, os.R_OK)
            write_permission: bool = os.access(self, os.W_OK)
            execute_permission: bool = os.access(self, os.X_OK)
            permission_value = 0

            if read_permission:
                permission_value += 4  # Add 4 for read permission (100 in binary)

            if write_permission:
                permission_value += 2  # Add 2 for write permission (010 in binary)

            if execute_permission:
                permission_value += 1  # Add 1 for execute permission (001 in binary)

            return permission_value

        raise RuntimeError(f"Unsupported operating system: {os.name}")


    def has_access(  # type: ignore[misc]
        self: Path,  # type: ignore[reportGeneralTypeIssues]
        mode: int = 0o6,
        *,
        recurse: bool = False,
    ) -> bool:
        """Check if we have access to the path.

        Args:
        ----
            recurse (bool): check access for all files inside of self. Only valid if self is a folder (default is False)

        Returns:
        -------
            True if path can be modified, False otherwise.
        """
        try:
            if self.is_file():
                return self.get_highest_permission() >= mode

            if self.is_dir():  # sourcery skip: extract-method
                test_path: Path = self / f"temp_test_file_{uuid.uuid4().hex}.tmp"
                with test_path.open("w") as f:
                    f.write("test")
                test_path.unlink()

                if not recurse:
                    return True

                for file_or_folder in self.rglob("*"):
                    cur_access: bool = file_or_folder.has_access(mode, recurse=recurse)
                    if not cur_access:
                        return False
                return True

        except OSError as os_exc:
            print(format_exception_with_variables(os_exc))
        except Exception as exc:
            print(format_exception_with_variables(exc))
            #raise
        return False

    def gain_access(
        self,
        mode: int = 0o7,
        *,
        recurse: bool = True,
    ) -> bool:
        assert isinstance(self, Path), f"self of '{self}' must inherit from BasePath not be literal BasePath instance."

        # (Unix) Gain ownership of the folder
        if os.name != "nt" and not self.has_access(mode, recurse=recurse):
            e = None
            try:
                home_path = Path.home()
                try:
                    stat_info = home_path.stat()
                except OSError as e:
                    print(format_exception_with_variables(e, ___message___=f"Error accessing file information at path '{home_path}'"))
                    raise
                else:
                    os.chown(self, stat_info.st_uid, stat_info.st_gid)  # type: ignore[attr-defined]
            except OSError as exc:
                if e is not None:
                    exc.__cause__ = e
                print(format_exception_with_variables(exc, ___message___=f"Error during chown for '{self}'"))

        # (Any OS) chmod the folder
        if not self.has_access(mode, recurse=recurse):
            try:
                self.chmod(mode * 100)
            except OSError as e:
                print(format_exception_with_variables(e, ___message___=f"Error during chmod at path '{self}'"))

        # TODO: prompt the user and gain access with os-native methods (UAC for windows, etc)
        if not self.has_access(mode, recurse=recurse):
            try:
                if platform.system() == "Darwin":
                    self.request_mac_permission()
                elif platform.system() == "Linux":
                    self.request_linux_permission()
                elif platform.system() == "Windows":
                    self.request_windows_permission()

            except Exception as e:
                print(format_exception_with_variables(e, ___message___=f"Error during platform-specific permission request at path '{self}'"))

        success: bool = self.has_access(mode, recurse=recurse)
        try:
            if recurse and self.is_dir():
                for child in self.iterdir():
                    success &= child.gain_access(mode, recurse=recurse)
        except OSError as e:
            print(format_exception_with_variables(e, ___message___=f"Error gaining access for children of path '{self}'"))
            success = False

        return success


class Path(BasePath, pathlib.Path):  # type: ignore[misc]
    # pylint: disable-all
    _flavour = pathlib.PureWindowsPath._flavour if os.name == "nt" else pathlib.PurePosixPath._flavour  # type: ignore[attr-defined]


class PosixPath(BasePath, pathlib.PosixPath):  # type: ignore[misc]
    pass


class WindowsPath(BasePath, pathlib.WindowsPath):  # type: ignore[misc]
    pass
