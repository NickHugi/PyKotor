from __future__ import annotations

import contextlib
import os
import platform
import re
from pathlib import (
    Path,
    PosixPath,  # type: ignore[pylance_reportGeneralTypeIssues]
    PurePath,  # type: ignore[pylance_reportGeneralTypeIssues]
    PurePosixPath,  # type: ignore[pylance_reportGeneralTypeIssues]
    PureWindowsPath,  # type: ignore[pylance_reportGeneralTypeIssues]
    WindowsPath,  # type: ignore[pylance_reportGeneralTypeIssues]
    _PosixFlavour,  # type: ignore[pylance_reportGeneralTypeIssues]
    _WindowsFlavour,  # type: ignore[pylance_reportGeneralTypeIssues]
)
from typing import TYPE_CHECKING, List, Tuple, Union

if TYPE_CHECKING:
    from pykotor.common.misc import Game

PathElem = Union[str, os.PathLike]
PATH_TYPES = Union[PathElem, List[PathElem], Tuple[PathElem, ...]]


def is_class_or_subclass_but_not_instance(cls, target_cls):
    if cls is target_cls:
        return True
    if not hasattr(cls, "__bases__"):
        return False
    return any(is_class_or_subclass_but_not_instance(base, target_cls) for base in cls.__bases__)


def is_instance_or_subinstance(instance, target_cls):
    if hasattr(instance, "__bases__"):  # instance is a class
        return False  # if instance is a class type, always return False
    # instance is not a class
    return type(instance) is target_cls or is_class_or_subclass_but_not_instance(type(instance), target_cls)


def simple_wrapper(fn_name, wrapped_class_type):
    def wrapped(self, *args, **kwargs):
        orig_fn = wrapped_class_type._original_methods[fn_name]

        # __init__ can only ever take one argument.
        if fn_name == "__init__":
            return orig_fn(self)

        def parse_arg(arg):
            if is_instance_or_subinstance(arg, PurePath) and CaseAwarePath.should_resolve_case(arg):
                return CaseAwarePath._get_case_sensitive_path(arg)

            return arg

        # Parse `self` if it meets the condition
        actual_self: CaseAwarePath | type = parse_arg(self)

        # Handle positional arguments
        args = tuple(parse_arg(arg) for arg in args)

        # Handle keyword arguments
        kwargs = {k: parse_arg(v) for k, v in kwargs.items()}

        # TODO: when orig_fn doesn't exist, the AttributeException should be raised by
        # the prior stack instead of here, as that's what would normally happen.
        return orig_fn(actual_self, *args, **kwargs)

    return wrapped


def create_case_insensitive_pathlib_class(cls):
    # Create a dictionary that'l hold the original methods for this class
    cls._original_methods = {}
    mro = cls.mro()  # Gets the method resolution order
    parent_classes = mro[1:]  # Exclude the current class itself

    # Store already wrapped methods to avoid wrapping multiple times
    wrapped_methods = set()

    # ignore these methods
    ignored_methods: set[str] = {"__instancecheck__", "__getattribute__", "__setattribute__", "__str__", "__setattr__"}

    for parent in parent_classes:
        for attr_name, attr_value in parent.__dict__.items():
            # Check if it's a method and hasn't been wrapped before
            if callable(attr_value) and attr_name not in wrapped_methods and attr_name not in ignored_methods:
                cls._original_methods[attr_name] = attr_value
                setattr(cls, attr_name, simple_wrapper(attr_name, cls))
                wrapped_methods.add(attr_name)


class BasePath:
    def __new__(cls, *args: PATH_TYPES, **kwargs):
        # if the only arg passed is already a cls, don't do heavy lifting trying to re-parse it.
        if len(args) == 1:
            arg0 = args[0]
            if isinstance(arg0, cls):
                return arg0  # type: ignore  # noqa: PGH003

        args_list = list(args)
        for i, arg in enumerate(args_list):
            if isinstance(arg, cls):
                continue
            path_str = arg if isinstance(arg, str) else getattr(arg, "__fspath__", lambda: None)()
            if path_str is None:
                msg = f"Object '{arg}' (index {i} of *args) must be str or a path-like object, but instead was '{type(arg)}'"
                raise TypeError(msg)

            formatted_path_str = cls._fix_path_formatting(path_str, cls._flavour.sep)
            super_object = super().__new__(cls, formatted_path_str, **kwargs)  # type: ignore[pylance general]
            args_list[i] = super_object
        return super().__new__(cls, *args_list, **kwargs)  # type: ignore  # noqa: PGH003

    def __str__(self):
        return self.__class__._fix_path_formatting(super().__str__(), self._flavour.sep)

    def __fspath__(self):
        return str(self)

    def __truediv__(self, key: PathElem):
        """
        Appends a path part with the divider operator '/'.
        This method is called when the left side is self.

        Args:
        ----
            self (CaseAwarePath):
            key (path-like object):
        """
        return type(self).__new__(type(self), self, key)

    def __rtruediv__(self, key: PathElem):
        """
        Appends a path part with the divider operator '/'.
        This method is called when the right side is self.

        Args:
        ----
            self (CaseAwarePath):
            key (path-like object):
        """
        return type(self).__new__(type(self), key, self)

    def __add__(self, key: PathElem):
        """
        Appends a path part with the addition operator '+'.
        This method is called when the left side is self.

        Args:
        ----
            self (CaseAwarePath):
            key (path-like object):
        """
        return type(self).__new__(type(self), self, key)

    def __radd__(self, key: PathElem):
        """
        Appends a path part with the addition operator '+'.
        This method is called when the right side is self.

        Args:
        ----
            self (CaseAwarePath):
            key (path-like object):
        """
        return type(self).__new__(type(self), key, self)

    def joinpath(self, *args: PATH_TYPES):
        """
        Appends one or more path-like objects and/or relative paths to self.

        Args:
        ----
            self (CaseAwarePath):
            key (path-like object):
        """
        return type(self).__new__(type(self), self, *args)

    def endswith(self, text: str) -> bool:
        return str(self).endswith(text)

    @staticmethod
    def _fix_path_formatting(str_path: str, slash=os.sep) -> str:
        if slash not in ("\\", "/"):
            msg = f"Invalid slash str: '{slash}'"
            raise ValueError(msg)
        if not str_path.strip():
            return str_path

        formatted_path: str = str_path

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
        return formatted_path if len(formatted_path) == 1 else formatted_path.rstrip(slash)


class PurePath(BasePath, PurePath):
    _flavour = _WindowsFlavour() if os.name == "nt" else _PosixFlavour()  # type: ignore pylint: disable-all


class PurePosixPath(BasePath, PurePosixPath):
    pass


class PureWindowsPath(BasePath, PureWindowsPath):
    pass


class Path(BasePath, Path):
    _flavour = _WindowsFlavour() if os.name == "nt" else _PosixFlavour()  # type: ignore pylint: disable-all
    pass


class PosixPath(BasePath, PosixPath):
    pass


class WindowsPath(BasePath, WindowsPath):
    pass


class CaseAwarePath(Path):
    def resolve(self, strict=False):
        new_path = super().resolve(strict)
        if CaseAwarePath.should_resolve_case(new_path):
            new_path = CaseAwarePath._get_case_sensitive_path(new_path)
        return new_path

    def __hash__(self) -> int:
        return hash(Path(str(self).lower()))

    def __str__(self):
        return super(self.__class__, self.__class__._get_case_sensitive_path(self)).__str__()

    @staticmethod
    def _get_case_sensitive_path(path: os.PathLike) -> CaseAwarePath:
        path: Path = path if isinstance(path, (Path, CaseAwarePath)) else Path(path)
        parts = list(path.parts)

        for i in range(1, len(parts)):  # ignore the root (/, C:\\, etc)
            base_path: Path = Path(*parts[:i])
            next_path: Path = Path(*parts[: i + 1])

            # Find the first non-existent case-sensitive file/folder in hierarchy
            if not next_path.is_dir() and base_path.is_dir():
                # iterate ignoring permission/read issues from the directory.
                def safe_iterdir(curpath: Path):
                    with contextlib.suppress(PermissionError, IOError):
                        yield from curpath.iterdir()

                base_path_items_generator = (item for item in safe_iterdir(base_path) if (i == len(parts) - 1) or item.is_dir())

                # if multiple are found, we get the one that most closely matches our case
                # A closest match is defined by the item that has the most case-sensitive positional matches
                # If two closest matches are identical (e.g. we're looking for TeST and we find TeSt and TesT), it's random.
                parts[i] = CaseAwarePath._find_closest_match(
                    parts[i],
                    base_path_items_generator,
                )

            # return a CaseAwarePath instance that resolves the case of existing items on disk, joined with the non-existing
            # parts in their original case.
            # if parts[1] is not found on disk, i.e. when i is 1 and base_path.exists() returns False, this will also return the original path.
            elif not next_path.exists():
                return super().__new__(CaseAwarePath, base_path.joinpath(*parts[i:]))

        # return a CaseAwarePath instance without infinitely recursing through the constructor
        return super().__new__(CaseAwarePath, *parts)

    @staticmethod
    def _find_closest_match(target, candidates) -> str:
        max_matching_chars = -1
        closest_match = target
        for candidate in candidates:
            matching_chars = CaseAwarePath._get_matching_characters_count(
                candidate.name,
                target,
            )
            if matching_chars > max_matching_chars:
                max_matching_chars = matching_chars
                closest_match = candidate.name
                if max_matching_chars == len(target):
                    break
        return closest_match

    @staticmethod
    def _get_matching_characters_count(str1: str, str2: str) -> int:
        """
        Returns the number of case sensitive characters that match in each position of the two strings.
        if str1 and str2 are NOT case-insensitive matches, this method will return -1
        """
        return sum(a == b for a, b in zip(str1, str2)) if str1.lower() == str2.lower() else -1

    @staticmethod
    def should_resolve_case(path) -> bool:
        if os.name == "nt":
            return False
        if isinstance(path, Path):
            return Path.is_absolute(path) and not os.path.exists(str(path))  # noqa: PTH110
        if isinstance(path, str):
            path_obj = Path(path)
            return path_obj.is_absolute() and not path_obj.exists()
        return False


# HACK: fix later
if os.name == "posix":
    create_case_insensitive_pathlib_class(CaseAwarePath)
elif os.name == "nt":
    CaseAwarePath = Path  # type: ignore[pylance_reportGeneralTypeIssues]


def locate_game_path(game: Game) -> CaseAwarePath | None:
    from pykotor.common.misc import Game

    locations = {
        "Windows": {
            Game.K1: [
                CaseAwarePath(r"C:\Program Files\Steam\steamapps\common\swkotor"),
                CaseAwarePath(r"C:\Program Files (x86)\Steam\steamapps\common\swkotor"),
                CaseAwarePath(r"C:\Program Files\LucasArts\SWKotOR"),
                CaseAwarePath(r"C:\Program Files (x86)\LucasArts\SWKotOR"),
                CaseAwarePath(r"C:\GOG Games\Star Wars - KotOR"),
            ],
            Game.K2: [
                CaseAwarePath(
                    r"C:\Program Files\Steam\steamapps\common\Knights of the Old Republic II",
                ),
                CaseAwarePath(
                    r"C:\Program Files (x86)\Steam\steamapps\common\Knights of the Old Republic II",
                ),
                CaseAwarePath(r"C:\Program Files\LucasArts\SWKotOR2"),
                CaseAwarePath(r"C:\Program Files (x86)\LucasArts\SWKotOR2"),
                CaseAwarePath(r"C:\GOG Games\Star Wars - KotOR2"),
            ],
        },
        "Darwin": {
            Game.K1: [
                CaseAwarePath(
                    "~/Library/Application Support/Steam/steamapps/common/swkotor/Knights of the Old Republic.app/Contents/Assets",
                ),
            ],
            Game.K2: [
                CaseAwarePath(
                    "~/Library/Application Support/Steam/steamapps/common/Knights of the Old Republic II/Knights of the Old Republic II.app/Contents/Assets",
                ),
            ],
        },
        "Linux": {
            Game.K1: [
                CaseAwarePath("~/.local/share/Steam/common/SteamApps/swkotor"),
                CaseAwarePath("~/.local/share/Steam/common/steamapps/swkotor"),
                CaseAwarePath("~/.local/share/Steam/common/swkotor"),
            ],
            Game.K2: [
                CaseAwarePath(
                    "~/.local/share/Steam/common/SteamApps/Knights of the Old Republic II",
                ),
                CaseAwarePath(
                    "~/.local/share/Steam/common/steamapps/Knights of the Old Republic II",
                ),
                CaseAwarePath(
                    "~/.local/share/Steam/common/Knights of the Old Republic II",
                ),
            ],
        },
    }

    potential = locations[platform.system()][game]
    return next((path for path in potential if path.exists()), None)
