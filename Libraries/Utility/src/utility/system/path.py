from __future__ import annotations

import contextlib
import os
import pathlib
import re
import subprocess
import uuid
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Any, Callable, Generator, Union

from utility.error_handling import format_exception_with_variables

if TYPE_CHECKING:
    from typing_extensions import Self

PathElem = Union[str, os.PathLike]

def override_to_pathlib(cls: type) -> type:
    class_map: dict[type, type] = {
        PurePath: pathlib.PurePath,
        PureWindowsPath: pathlib.PureWindowsPath,
        PurePosixPath: pathlib.PurePosixPath,
        Path: pathlib.Path,
        WindowsPath: pathlib.WindowsPath,
        PosixPath: pathlib.PosixPath,
    }

    return class_map.get(cls, cls)

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
        if self is __value:
            return True
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
        except Exception as e:  # noqa: BLE001
            print(format_exception_with_variables(e,  message="This exception has been suppressed and is only relevant for debug purposes."))
            return
        else:
            while True:
                try:
                    yield next(iterator)  # type: ignore[misc, reportGeneralTypeIssues]
                except StopIteration:  # noqa: PERF203
                    break  # StopIteration means there are no more files to iterate over
                except Exception as e:  # noqa: BLE001
                    print(format_exception_with_variables(e,  message="This exception has been suppressed and is only relevant for debug purposes."))
                    continue  # Ignore the file that caused an exception and move to the next

    # Safe iterdir operation
    def safe_iterdir(  # type: ignore[misc]
        self: Path,  # type: ignore[reportGeneralTypeIssues]
    ) -> Generator[Self, Any, None]:  # type: ignore[reportGeneralTypeIssues]
        try:
            iterator: Generator[Self, Any, None] = self.iterdir()  # type: ignore[assignment, reportGeneralTypeIssues]
        except Exception as e:  # noqa: BLE001
            print(format_exception_with_variables(e,  message="This exception has been suppressed and is only relevant for debug purposes."))
            return
        else:
            while True:
                try:
                    yield next(iterator)  # type: ignore[misc, reportGeneralTypeIssues]
                except StopIteration:  # noqa: PERF203
                    break  # StopIteration means there are no more files to iterate over
                except Exception as e:  # noqa: BLE001
                    print(format_exception_with_variables(e,  message="This exception has been suppressed and is only relevant for debug purposes."))
                    continue  # Ignore the file that caused an exception and move to the next

    # Safe is_dir operation
    def safe_isdir(self: Path) -> bool | None:  # type: ignore[misc]
        check: bool | None = None
        try:
            check = self.is_dir()
        except OSError as e:
            print(format_exception_with_variables(e,  message="This exception has been suppressed and is only relevant for debug purposes."))
            return None
        else:
            return check

    # Safe is_file operation
    def safe_isfile(self: Path) -> bool | None:  # type: ignore[misc]
        check: bool | None = None
        try:
            check = self.is_file()
        except OSError as e:
            print(format_exception_with_variables(e,  message="This exception has been suppressed and is only relevant for debug purposes."))
            return None
        else:
            return check

    # Safe exists operation
    def safe_exists(self: Path) -> bool | None:  # type: ignore[misc]
        check: bool | None = None
        try:
            check = self.exists()
        except Exception as e:
            print(format_exception_with_variables(e,  message="This exception has been suppressed and is only relevant for debug purposes."))
            return None
        else:
            return check

    def walk(
        self: Path,  # type: ignore[misc]
        top_down=True,
        on_error=None,
        follow_symlinks=False,
    ) -> Generator[tuple[Self, list[str], list[str]], Any, None]:  # type: ignore[reportGeneralTypeIssues]
        """Walk the directory tree from this directory, similar to os.walk()."""  # noqa: D402
        paths: list[Self] = [self]  # type: ignore[reportGeneralTypeIssues]

        while paths:
            path = paths.pop()
            if isinstance(path, tuple):
                yield path
                continue

            # We may not have read permission for self, in which case we can't
            # get a list of the files the directory contains. os.walk()
            # always suppressed the exception in that instance, rather than
            # blow up for a minor reason when (say) a thousand readable
            # directories are still left to visit. That logic is copied here.
            try:
                scandir_it = os.scandir(self)
            except OSError as error:
                if on_error is not None:
                    on_error(error)
                continue

            with scandir_it:
                dirnames: list[str] = []
                filenames: list[str] = []
                for entry in scandir_it:
                    try:
                        is_dir = entry.is_dir(follow_symlinks=follow_symlinks)
                    except OSError:
                        # Carried over from os.path.isdir().
                        is_dir = False

                    if is_dir:
                        dirnames.append(entry.name)
                    else:
                        filenames.append(entry.name)

            if top_down:
                yield path, dirnames, filenames  # type: ignore[reportGeneralTypeIssues]
            else:
                paths.append((path, dirnames, filenames))  # type: ignore[reportGeneralTypeIssues]

            paths += [path.joinpath(d) for d in reversed(dirnames)]

    def is_relative_to(self: Path, *args, **kwargs) -> bool:  # type: ignore[misc]
        """Return True if the path is relative to another path or False."""
        if not args or "other" in kwargs:
            msg = f"{type(self)}.is_relative_to() missing 1 required positional argument: 'other'"
            raise TypeError(msg)

        other, *_deprecated = args
        parsed_other = self.with_segments(other, *_deprecated)
        return parsed_other == self or parsed_other in self.parents

    def get_highest_posix_permission(
        self: Path,  # type: ignore[reportGeneralTypeIssues]
        uid: int | None = None,
        gid: int | None = None,
    ) -> int:
        """Similar to get_highest_permission but will not take runtime elevation (e.g. sudo) into account."""
        if os.name == "nt":
            msg = "Not supported on Windows."
            raise OSError(msg)

        # Retrieve the current user's UID and GID
        current_uid = uid if uid is not None else os.getuid()
        current_gid = gid if gid is not None else os.getgid()

        # Retrieve the UID and GID of the owner of the path_obj
        stat_info = self.stat()
        owner_uid: int = stat_info.st_uid
        owner_gid: int = stat_info.st_gid

        # Extract user, group, and other permissions from mode
        mode: int = stat_info.st_mode
        user_perms: int = (mode >> 6) & 0o7  # sourcery skip: move-assign
        group_perms: int = (mode >> 3) & 0o7
        other_perms: int = mode & 0o7
        highest_perm: int = 0

        # If the user is the owner, user_perms apply
        if current_uid == owner_uid:
            highest_perm = user_perms

        # If the user's group matches the file's group, check group_perms
        if current_gid == owner_gid:
            highest_perm = max(highest_perm, group_perms)

        # Check against other_perms
        return max(highest_perm, other_perms)

    def get_highest_permission(
        self: Path,  # type: ignore[reportGeneralTypeIssues]
    ) -> int:
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


    def has_access(  # type: ignore[misc]
        self: Path,  # type: ignore[reportGeneralTypeIssues]
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

        Returns:
        -------
            bool: True if the path has the specified access permissions, False otherwise.

        Examples:
        --------
            >>> path = Path('/my/path')
            >>> path.has_access(mode=0o6, recurse=False)
        """
        mode_to_str: dict[int, str | None] = {
            0o0: None,   # No permissions
            0o1: None,   # Execute only
            0o2: "w",    # Write only
            0o3: "w",    # Write and execute
            0o4: "r",    # Read only
            0o5: "r",    # Read and execute
            0o6: "r+",   # Read and write
            0o7: "r+",   # Read, write, and execute
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
        except Exception as exc:
            print(format_exception_with_variables(exc))
            #raise
        return False

    unique_sentinel = object()
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
        assert isinstance(self, Path), f"self of '{self}' must inherit from BasePath not be literal BasePath instance."

        if os.name == "posix":
            print("(Unix) Gain ownership of the folder with os.chown()")
            e = None
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
        print("Attempting pathlib.Path.chmod(self)...")
        try:
            # Get the current permissions
            current_permissions: int = self.stat().st_mode
            # Extract owner and group permissions
            owner_permissions: int = current_permissions & 0o700  # Extracts the first number of the octal (e.g. 0o7 in 0o750)
            group_permissions: int = current_permissions & 0o70   # Extracts the second number of the octal (e.g. 0o5 in 0o750)
            # Combine them with the new 'other' permissions
            new_permissions: int = owner_permissions | group_permissions | mode
            # Apply the new permissions
            if resolve_symlinks:
                self.chmod(new_permissions)
            else:
                try:
                    self.lchmod(new_permissions)
                except NotImplementedError as e2:
                    self.chmod(new_permissions)
        except (OSError, NotImplementedError) as e:
            print(format_exception_with_variables(e, message=f"Error during chmod at path '{self}'"))

        success: bool = True
        if not self.has_access(mode, recurse=False):
            log_func(f"No permissions to {self}, attempting native access fix...")
            try:
                self.request_native_access(elevate=False, recurse=recurse, log_func=log_func)
            except Exception as e:
                print(format_exception_with_variables(e, message=f"Error during platform-specific permission request at path '{self}'"))

            log_func("Checking access again before attempting elevated native access fix...")
            success = self.has_access(mode, recurse=False)
            if not success:
                log_func("Still no access permitted, attempting to elevate the native access fix...")
                try:
                    self.request_native_access(elevate=True, recurse=recurse, log_func=log_func)
                except Exception as e:
                    print(format_exception_with_variables(e, message=f"Error during elevated platform-specific permission request at path '{self}'"))

        if not success:
            log_func("Verifying the operations were successful...")
            success= self.has_access(mode, recurse=False)
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

    if os.name == "posix":
        # Inspired by the C# code provided by KOTORModSync's source code at https://github.com/th3w1zard1/KOTORModSync
        def request_native_access(self, elevate: bool = False, recurse: bool = True):
            if elevate:
                if recurse:
                    # TODO: call os.system so a new terminal is ran, then remove '-n true'
                    chmod_args = ["sudo", "-n", "true", "chmod", "-R", "777", f"{self}"]
                    chown_args = ["sudo", "-n", "true", "chown", "-R", "$(whoami)", f"{self}"]
                else:
                    chmod_args = ["sudo", "-n", "true", "chmod", "777", f"{self}"]
                    chown_args = ["sudo", "-n", "true", "chown", "$(whoami)", f"{self}"]
            elif recurse:
                chmod_args = ["chmod", "-R", "777", f"{self}"]
                chown_args = ["chown", "-R", "$(whoami)", f"{self}"]
            else:
                chmod_args = ["chmod", "777", f"{self}"]
                chown_args = ["chown", "$(whoami)", f"{self}"]

            # Note: -c/-v is preferred but is not supported on some unix systems.
            chmod_result: subprocess.CompletedProcess[str] = subprocess.run(chmod_args, timeout=60, check=False, capture_output=True, text=True)
            chown_result: subprocess.CompletedProcess[str] = subprocess.run(chown_args, timeout=60, check=False, capture_output=True, text=True)

            if chmod_result.returncode != 0:
                print(
                    f"Could not set unix chmod permissions at '{self}':\n"
                    f"exit code: {chmod_result.returncode}\n"
                    f"stdout: {chmod_result.stdout}\n"
                    f"stderr: {chmod_result.stderr}",
                )

            if chown_result.returncode != 0:
                print(
                    f"Could not set unix chmod permissions at '{self}':\n"
                    f"exit code: {chown_result.returncode}\n"
                    f"stdout: {chown_result.stdout}\n"
                    f"stderr: {chown_result.stderr}",
                )

            print(chmod_result.stdout)
            print(chown_result.stdout)


    if os.name == "nt":

        # TODO: move to utility.system
        @staticmethod
        def get_win_attrs(file_path):
            import ctypes

            # Constants for file attributes
            FILE_ATTRIBUTE_READONLY = 0x1
            FILE_ATTRIBUTE_HIDDEN = 0x2
            FILE_ATTRIBUTE_SYSTEM = 0x4
            # GetFileAttributesW is a Windows API function
            attrs = ctypes.windll.kernel32.GetFileAttributesW(file_path)

            # If the function fails, it returns INVALID_FILE_ATTRIBUTES
            if attrs == -1:
                msg = f"Cannot access attributes of file: {file_path}"
                raise FileNotFoundError(msg)

            # Check for specific attributes
            is_read_only = bool(attrs & FILE_ATTRIBUTE_READONLY)
            is_hidden = bool(attrs & FILE_ATTRIBUTE_HIDDEN)
            is_system = bool(attrs & FILE_ATTRIBUTE_SYSTEM)

            return is_read_only, is_hidden, is_system

        # TODO: move to utility.system
        def run_commands_as_admin(self, cmd: list[str], pause_after_command: bool = True):
            # sourcery skip: extract-method
            with TemporaryDirectory() as tempdir:
                # Ensure the script path is absolute
                script_path_obj: Path = self.__class__(tempdir, "temp_script.bat")  # type: ignore[reportGeneralTypeIssues]
                script_path_obj = script_path_obj.absolute()
                script_path = str(script_path_obj)

                # Write the commands to a batch file
                with script_path_obj.open("w") as file:
                    for command in cmd:
                        file.write(command + "\n")
                    if pause_after_command:
                        file.write("pause\nexit\n")

                # Determine the CMD switch to use
                cmd_switch = "/K" if pause_after_command else "/C"

                # Construct the command to run the batch script with elevated privileges
                run_script_cmd: list[str] = [
                    "Powershell",
                    "-Command",
                    f"Start-Process cmd.exe -ArgumentList '{cmd_switch} \"{script_path}\"' -Verb RunAs -Wait",
                ]

                # Execute the batch script
                subprocess.run(run_script_cmd, check=False)

            # Delete the batch script after execution
            with contextlib.suppress(Exception):
                if script_path_obj.safe_isfile():
                    script_path_obj.unlink()

        # Inspired by the C# code provided by KOTORModSync at https://github.com/th3w1zard1/KOTORModSync
        def request_native_access(
            self: Path,  # type: ignore[reportGeneralTypeIssues]
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
                icacls_reset_result: subprocess.CompletedProcess[str] = subprocess.run(icacls_reset_args, timeout=60, check=False,
                                                                                  capture_output=True, text=True)
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
            if elevate:  # sourcery skip: extract-duplicate-method
                commands.append(" ".join(takeown_args))
            else:
                takeown_result: subprocess.CompletedProcess[str] = subprocess.run(takeown_args, timeout=60, check=False,
                                                                                  capture_output=True, text=True)
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
                icacls_result: subprocess.CompletedProcess[str] = subprocess.run(icacls_args, timeout=60, check=False,
                                                                                  capture_output=True, text=True)
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
            is_read_only, is_hidden, is_system = self.get_win_attrs(self_path_str.replace('"', ""))
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
                attrib_result: subprocess.CompletedProcess[str] = subprocess.run(attrib_args, timeout=60, check=False,
                                                                                    capture_output=True, text=True)
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
                    rehide_result: subprocess.CompletedProcess[str] = subprocess.run(rehide_args, timeout=60, check=False,
                                                                                        capture_output=True, text=True)
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


class Path(BasePath, pathlib.Path):  # type: ignore[misc]
    # pylint: disable-all
    _flavour = pathlib.PureWindowsPath._flavour if os.name == "nt" else pathlib.PurePosixPath._flavour  # type: ignore[attr-defined]


class PosixPath(BasePath, pathlib.PosixPath):  # type: ignore[misc]
    pass


class WindowsPath(BasePath, pathlib.WindowsPath):  # type: ignore[misc]
    pass
