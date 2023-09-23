from __future__ import annotations

import contextlib
import os
import platform
import re
from abc import ABC, abstractmethod
from functools import wraps
from pathlib import (
    Path,
    PosixPath,
    PurePath,
    PurePosixPath,
    PureWindowsPath,
    WindowsPath,
)
from typing import TYPE_CHECKING, List, Tuple, Union
from unittest.mock import patch

if TYPE_CHECKING:
    from pykotor.common.misc import Game

PathElem = Union[str, os.PathLike]
PATH_TYPES = Union[PathElem, List[PathElem], Tuple[PathElem, ...]]


class BasePath(ABC):
    @classmethod
    @abstractmethod
    def _get_delimiter(cls) -> str:
        pass

    def __new__(cls, *args, **kwargs):
        if len(args) == 1:
            arg0 = args[0]
            # if the only arg passed is already a cls, don't do heavy lifting trying to re-parse it.
            if isinstance(arg0, cls):
                return arg0  # type: ignore  # noqa: PGH003
        args_list = [*args]
        for i, arg in enumerate(args):
            if isinstance(arg, cls):
                continue
            path_str = arg if isinstance(arg, str) else getattr(arg, "__fspath__", lambda: None)()
            if path_str is not None:
                formatted_path_str = cls._fix_path_formatting(path_str)
                super_object = super().__new__(cls, formatted_path_str, **kwargs)  # type: ignore[pylance general]
                args_list[i] = super_object
            else:
                msg = f"Object '{arg}' (index {i} of *args) must be str or a path-like object, but instead was '{type(arg)}'"
                raise TypeError(msg)
        return super().__new__(cls, *args_list, **kwargs)  # type: ignore  # noqa: PGH003

    def __str__(self):
        return self.__class__._fix_path_formatting(super().__str__(), self._get_delimiter())

    def __fspath__(self):
        return str(self)

    def __truediv__(self, key: PATH_TYPES):
        """
        Uses divider operator to combine two paths.

        Args:
        ----
            self (CaseAwarePath):
            key (path-like object):
        """
        return self.__new__(type(self), self, key)

    def __rtruediv__(self, key: PATH_TYPES):
        """
        Uses divider operator to combine two paths.

        Args:
        ----
            self (CaseAwarePath):
            key (path-like object):
        """
        return self.__new__(type(self), key, self)

    def joinpath(self, *args: PATH_TYPES):
        return self.__new__(type(self), self, *args)

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

        # Fix mixed slashes
        if os.altsep is not None:
            formatted_path = formatted_path.replace(os.altsep, os.sep)

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

        return formatted_path.rstrip(slash)


class PurePath(BasePath, PurePath):
    _flavour = PureWindowsPath._flavour if os.name == "nt" else PurePosixPath._flavour  # type: ignore pylint: disable-all

    @classmethod
    def _get_delimiter(cls):
        return "\\" if os.name == "nt" else "/"


class PurePosixPath(PurePath, PurePosixPath):
    @classmethod
    def _get_delimiter(cls):
        return "/"


class PureWindowsPath(PurePath, PureWindowsPath):
    @classmethod
    def _get_delimiter(cls):
        return "\\"

class Path(PurePath, Path):
    _flavour = PureWindowsPath._flavour if os.name == "nt" else PurePosixPath._flavour  # type: ignore pylint: disable-all
    pass

class PosixPath(Path, PurePosixPath, PosixPath):
    _flavour = PurePosixPath._flavour  # type: ignore pylint: disable-all

class WindowsPath(Path, PureWindowsPath, WindowsPath):
    _flavour = PureWindowsPath._flavour

class CaseAwareDescriptor:
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner):
        print("__get__ called.")
        print("self's type:", type(self))
        print("instance's type:", type(instance))
        print("owner's type:", type(owner))
        print("self:", self)
        print("instance:", instance)
        print("owner:", owner)
        instance = instance or self
        if CaseAwarePath.should_resolve_case(instance):
            instance = CaseAwarePath.get_case_sensitive_path(instance)
        if CaseAwarePath.should_resolve_case(self):
            self = CaseAwarePath.get_case_sensitive_path(self)

        @wraps(self.func)
        def wrapper(*args, **kwargs):
            # Check if any arg is an instance of os.PathLike
            if not any(isinstance(arg, os.PathLike) for arg in args):
                return self.func(instance, *args, **kwargs)
            args_list = [*args]
            for i, arg in enumerate(args_list):
                if isinstance(arg, os.PathLike) and CaseAwarePath.should_resolve_case(arg):
                    args_list[i] = CaseAwarePath._get_case_sensitive_path(arg)
            if CaseAwarePath.should_resolve_case(instance):
                return self.func(CaseAwarePath._get_case_sensitive_path(instance), *args, **kwargs)
            return self.func(instance, *args, **kwargs)

        return wrapper

class CaseAwareMeta(type):
    def __new__(cls, name, bases, class_dict):
        for key, value in list(class_dict.items()):
            # More selective wrapping: only wrap functions, not all callables
            if isinstance(value, (staticmethod, classmethod)):
                # Don't wrap static or class methods
                continue
            if callable(value) and type(value) is not type:
                class_dict[key] = CaseAwareDescriptor(value)
        return super().__new__(cls, name, bases, class_dict)

class CombinedMeta(CaseAwareMeta, type(BasePath)):
    pass

class CaseAwarePath(Path, metaclass=CombinedMeta):
    _flavour = PureWindowsPath._flavour if os.name == "nt" else PurePosixPath._flavour  # type: ignore pylint: disable-all

    def resolve(self, strict=False):
        new_path = super().resolve(strict)
        if CaseAwarePath.should_resolve_case(new_path):
            new_path = CaseAwarePath._get_case_sensitive_path(new_path)
        return new_path

    def __hash__(self) -> int:
        return hash(Path(str(self).lower()))

    @staticmethod
    def _get_case_sensitive_path(path: os.PathLike) -> CaseAwarePath:
        path = path if isinstance(path, (Path, CaseAwarePath)) else Path(path)
        parts = list(path.parts)

        for i in range(1, len(parts)):  # ignore the root (/, C:\\, etc)
            base_path: Path = Path(*parts[:i])
            next_path: Path = Path(*parts[: i + 1])

            # Find the first non-existent case-sensitive file/folder in hierarchy
            if not next_path.is_dir() and base_path.is_dir():
                # iterate ignoring permission/read issues from the directory.
                def safe_iterdir(path: Path):
                    with contextlib.suppress(PermissionError, IOError):
                        yield from path.iterdir()

                base_path_items_generator = (
                    item for item in safe_iterdir(base_path) if (i == len(parts) - 1) or item.is_dir()
                )

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
        if isinstance(path, (CaseAwarePath, Path)):
            return path.is_absolute() and not path.exists()
        if isinstance(path, str):
            path_obj = Path(path)
            return path_obj.is_absolute() and not path_obj.exists()
        return False


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
