from __future__ import annotations

import contextlib
import os
import platform
import re
from pathlib import Path, PurePosixPath, PureWindowsPath

from pykotor.common.misc import Game


class CaseAwarePath(Path):
    _flavour = PureWindowsPath._flavour if os.name == "nt" else PurePosixPath._flavour  # type: ignore pylint: disable-all

    def __new__(cls, *args, **kwargs):
        if not all(isinstance(arg, CaseAwarePath) for arg in args): # don't even assume __fspath__ objects are valid.
            args = list(args)
            for i, arg in enumerate(args):
                if isinstance(arg, str) or hasattr(arg, "__fspath__"):
                    args[i] = Path(cls._fix_path_formatting(str(arg)))
                else:
                    msg = f"argument '{arg}' in CaseAwarePath constructor must be a path-like object, got {type(arg)}"
                    raise TypeError(msg)

        returned_path = super().__new__(cls, *args, **kwargs)
        if cls.should_resolve_case(returned_path):
            return cls._get_case_sensitive_path(returned_path)
        return returned_path

    def __fspath__(self):
        return str(self)

    def __truediv__(self, key) -> CaseAwarePath:
        """Uses divider operator to combine two paths.
        Args:
        ----
            self (CaseAwarePath):
            key (path-like object):
        """
        return CaseAwarePath(self, key)

    def __rtruediv__(self, key) -> CaseAwarePath:
        """Uses divider operator to combine two paths.
        Args:
        ----
            self (CaseAwarePath):
            key (path-like object):
        """
        return CaseAwarePath(key, self)

    def joinpath(self, *args) -> CaseAwarePath:
        new_path = self
        for arg in args:
            new_path /= arg
        return new_path

    def resolve(self, strict=False) -> CaseAwarePath:
        new_path = super().resolve(strict)
        if CaseAwarePath.should_resolve_case(new_path):
            new_path = CaseAwarePath._get_case_sensitive_path(new_path)
        return new_path

    def endswith(self, text: str) -> bool:
        return str(self).endswith(text)

    @staticmethod
    def _get_case_sensitive_path(path: Path | CaseAwarePath) -> CaseAwarePath:
        parts = list(path.parts)

        for i in range(1, len(parts)):  # ignore the root (/, C:\\, etc)
            base_path: Path = Path(*parts[:i])
            next_path: Path = Path(*parts[: i + 1])

            # Find the first non-existent case-sensitive file/folder in hierarchy
            if not next_path.is_dir() and base_path.is_dir():
                # iterate ignoring permission/read issues from the directory.
                def safe_iterdir(path):
                    with contextlib.suppress(PermissionError, IOError):
                        yield from path.iterdir()

                base_path_items_generator = (
                    item
                    for item in safe_iterdir(base_path)
                    if (i == len(parts) - 1) or item.is_dir()
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
        return (
            sum(a == b for a, b in zip(str1, str2))
            if str1.lower() == str2.lower()
            else -1
        )

    @staticmethod
    def _fix_path_formatting(str_path: str) -> str:
        if not str_path.strip():
            return str_path

        formatted_path: str = str_path

        # Fix mixed slashes
        if os.altsep is not None:
            formatted_path = formatted_path.replace(os.altsep, os.sep)

        # For Windows paths
        if os.name == "nt":
            # Fix mixed slashes, replacing all forwardslashes with backslashes
            formatted_path = formatted_path.replace("/", "\\")
            # Replace multiple backslash's with a single backslash
            formatted_path = re.sub(r"\\{2,}", "\\\\", formatted_path)
            # Strip the leading backslash if one exists
            formatted_path = formatted_path.lstrip("\\")
        # For Unix-like paths
        else:
            # Fix mixed slashes, replacing all backslashes with forwardslashes
            formatted_path = formatted_path.replace("\\", "/")
            # Replace multiple forwardslash's with a single forwardslash
            formatted_path = re.sub(r"/{2,}", "/", formatted_path)

        return formatted_path.rstrip(os.sep)

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
