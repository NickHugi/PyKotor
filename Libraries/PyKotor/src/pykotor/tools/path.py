from __future__ import annotations

import os
import pathlib
import platform
import shutil
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
    from utility.system.path import PathElem


def is_filesystem_case_sensitive(path: os.PathLike | str) -> bool | None:
    """Check if the filesystem at the given path is case-sensitive.
    This function creates a temporary file to test the filesystem behavior.
    """
    try:
        with tempfile.TemporaryDirectory(dir=path) as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            test_file = temp_path / "case_test_file"
            test_file.touch()

            # Attempt to access the same file with a different case to check case sensitivity
            test_file_upper = temp_path / "CASE_TEST_FILE"
            return not test_file_upper.exists()
    except Exception:
        return None


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

        # TODO(th3w1zard1): when orig_fn doesn't exist, the AttributeException should be raised by
        # the prior stack instead of here, as that's what would normally happen.

        return orig_fn(actual_self_or_cls, *new_args, **new_kwargs)

    return wrapped


def create_case_insensitive_pathlib_class(cls: type[CaseAwarePath]):
    # Create a dictionary that'll hold the original methods for this class
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
            if callable(attr_value) and attr_name not in wrapped_methods and attr_name not in ignored_methods:
                cls._original_methods[attr_name] = attr_value  # type: ignore[attr-defined]  # pylint: disable=protected-access
                setattr(cls, attr_name, simple_wrapper(attr_name, cls))
                wrapped_methods.add(attr_name)


# TODO(th3w1zard1): Move to pykotor.common
class CaseAwarePath(InternalWindowsPath if os.name == "nt" else InternalPosixPath):  # type: ignore[misc]
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
    def extract_absolute_prefix(relative_path: InternalPath, absolute_path: InternalPath) -> tuple[str, ...]:
        # Ensure the absolute path is absolute and the relative path is resolved relative to it
        absolute_path = absolute_path.absolute()
        relative_path_resolved = (absolute_path.parent / relative_path).absolute()

        # Convert to lists of parts for comparison
        abs_parts = absolute_path.parts
        rel_parts = relative_path_resolved.parts

        # Identify the index where the relative path starts in the absolute path
        start_index_of_rel_in_abs = len(abs_parts) - len(rel_parts)

        # Extract the differing prefix part as a new Path object
        return abs_parts[:start_index_of_rel_in_abs]

    def safe_relative_to(self, other: str | os.PathLike) -> str:
        # Normalize paths to handle different OS path conventions
        from_path = os.path.normpath(self)
        to_path = os.path.normpath(other)

        # Get common prefix
        common_prefix = os.path.commonpath([from_path, to_path])

        # Calculate relative path
        from_parts = from_path.split(os.sep)  # noqa: PTH206
        to_parts = to_path.split(os.sep)  # noqa: PTH206
        common_parts = common_prefix.split(os.sep)  # noqa: PTH206

        # Number of "../" to prepend for going up from from_path to the common prefix
        up_dirs: int | str = len(from_parts) - len(common_parts)
        if up_dirs == 0:
            up_dirs = "."

        # Remaining parts after the common prefix
        down_dirs = os.sep.join(to_parts[len(common_parts) :])  # noqa: PTH118

        result = f"{up_dirs}{os.sep}{down_dirs}" if down_dirs else up_dirs
        if isinstance(result, int):
            print(f"result somehow an int: {result}")
        return str(result)

    def relative_to(
        self,
        *args: PathElem,
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
            parsed_other = self.with_segments(other, *_deprecated)
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
            parsed_other = other if isinstance(other, InternalPurePath) else InternalPurePath(other)
            parsed_other = parsed_other.with_segments(other, *_deprecated)
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
            prefixes = self.extract_absolute_prefix(InternalPath(replacement), InternalPath(parsed_other))
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
            parsed_other = self.with_segments(other, *_deprecated)
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
            parsed_other = other if isinstance(other, InternalPurePath) else InternalPurePath(other)
            parsed_other = parsed_other.with_segments(other, *_deprecated)
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

    def replace(self, target: PathElem) -> Self:
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
    def get_case_sensitive_path(
        cls,
        path: PathElem,
        prefixes: list[str] | tuple[str, ...] | None = None,
    ) -> Self:
        """Get a case sensitive path.

        Args:
        ----
            path: The path to resolve case sensitivity for

        Returns:
        -------
            CaseAwarePath: The path with case sensitivity resolved

        Processing Logic:
        ----------------
            - Convert the path to a pathlib Path object
            - Iterate through each path part starting from index 1
            - Check if the current path part and the path up to that part exist
            - If not, find the closest matching file/folder name in the existing path
            - Return a CaseAwarePath instance with case sensitivity resolved.
        """
        prefixes = prefixes or []
        pathlib_path = pathlib.Path(path)
        pathlib_abspath = pathlib.Path(*prefixes, path).absolute() if prefixes else pathlib_path.absolute()
        num_differing_parts = len(pathlib_abspath.parts) - len(pathlib_path.parts)  # keeps the path relative if it already was.
        parts = list(pathlib_abspath.parts)

        for i in range(1, len(parts)):  # ignore the root (/, C:\\, etc)
            base_path: InternalPath = InternalPath(*parts[:i])
            next_path: InternalPath = InternalPath(*parts[: i + 1])

            if not next_path.safe_isdir() and base_path.safe_isdir():
                # Find the first non-existent case-sensitive file/folder in hierarchy
                # if multiple are found, use the one that most closely matches our case
                # A closest match is defined, in this context, as the file/folder's name that contains the most case-sensitive positional character matches
                # If two closest matches are identical (e.g. we're looking for TeST and we find TeSt and TesT), it's probably random.
                last_part: bool = i == len(parts) - 1
                parts[i] = cls.find_closest_match(
                    parts[i],
                    (item for item in base_path.safe_iterdir() if last_part or item.safe_isdir()),
                )

            elif not next_path.safe_exists():
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
    def get_matching_characters_count(str1: str, str2: str) -> int:
        """Returns the number of case sensitive characters that match in each position of the two strings.

        if str1 and str2 are NOT case-insensitive matches, this method will return -1.
        """
        return sum(a == b for a, b in zip(str1, str2)) if str1.lower() == str2.lower() else -1

    def __hash__(self):
        return hash(self.as_windows())

    def __eq__(self, other):
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


create_case_insensitive_pathlib_class(CaseAwarePath)


def get_default_paths() -> dict[str, dict[Game, list[str]]]:  # TODO(th3w1zard1): Many of these paths are incomplete and need community input.
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
        game: {case_path for case_path in (CaseAwarePath(path).expanduser().resolve() for path in paths) if case_path.safe_isdir()}
        for game, paths in raw_locations.get(os_str, {}).items()
    }

    # Build kotor locations by registry (if on windows)
    if os_str == "Windows":
        from utility.system.win32.registry import resolve_reg_key_to_path

        for game, possible_game_paths in ((Game.K1, winreg_key(Game.K1)), (Game.K2, winreg_key(Game.K2))):
            for reg_key, reg_valname in possible_game_paths:
                path_str = resolve_reg_key_to_path(reg_key, reg_valname)
                path = CaseAwarePath(path_str).resolve() if path_str else None
                if path and path.name and path.safe_isdir():
                    locations[game].add(path)
        amazon_k1_path_str: str | None = find_software_key("AmazonGames/Star Wars - Knights of the Old")
        if amazon_k1_path_str is not None and InternalPath(amazon_k1_path_str).safe_isdir():
            locations[Game.K1].add(CaseAwarePath(amazon_k1_path_str))

    # don't return nested sets, return as lists.
    return {Game.K1: [*locations[Game.K1]], Game.K2: [*locations[Game.K2]]}
