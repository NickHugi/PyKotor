from __future__ import annotations

import os
import platform
import re
from pathlib import Path, PurePosixPath, PureWindowsPath
try:
    from typing import Self # type: ignore
except ImportError:
    from typing_extensions import Self


from pykotor.common.misc import Game


class CaseAwarePath(Path):
    _flavour = PureWindowsPath._flavour if os.name == "nt" else PurePosixPath._flavour  # type: ignore pylint: disable-all

    def __new__(cls, *args, **kwargs):
        # Check if all arguments are already CaseAwarePath instances
        if all(isinstance(arg, CaseAwarePath) for arg in args):
            return super().__new__(cls, *args, **kwargs)
        # Build a path string from args
        path_str = os.path.join(*args)  # noqa: PTH118

        # Apply fix_path_formatting function
        fixed_path_str = CaseAwarePath._fix_path_formatting(path_str)

        # todo(th3w1zard1) check if path is rooted and if not return here.

        # Create a new Path object with the fixed path
        if os.name == "nt" or os.path.exists(fixed_path_str):
            return super().__new__(cls, fixed_path_str)

        return super().__new__(cls, fixed_path_str)._get_case_sensitive_path()

    def __truediv__(self, key) -> Self:
        """Uses divider operator to combine two paths.

        Args:
        ----
            self (CaseAwarePath):
            key (path-like object):

        """
        if not isinstance(key, CaseAwarePath):
            key = CaseAwarePath._fix_path_formatting(str(key))
        new_path = super().__truediv__(key)
        if os.name != "nt" and not new_path.exists():
            new_path = new_path._get_case_sensitive_path()
        return new_path

    def __rtruediv__(self, key) -> Self:
        """Uses divider operator to combine two paths.

        Args:
        ----
            self (CaseAwarePath):
            key (path-like object):

        """
        if not isinstance(key, CaseAwarePath):
            key = CaseAwarePath._fix_path_formatting(str(key))
        new_path = super().__rtruediv__(key)
        if os.name != "nt" and not new_path.exists():
            new_path = new_path._get_case_sensitive_path()
        return new_path

    def joinpath(self, *args) -> Self:
        new_path = self
        for arg in args:
            new_path /= arg
        return new_path

    def resolve(self, strict=False) -> Self:
        new_path = super(CaseAwarePath, self).resolve(strict)
        if os.name != "nt" and not new_path.exists():
            new_path = self._get_case_sensitive_path()
        return new_path

    def _get_case_sensitive_path(self):
        parts = list(self.parts)
        i = 0

        for i in range(1, len(parts)):
            base_path: CaseAwarePath = super().__new__(type(self), *parts[:i])
            next_path: CaseAwarePath = base_path / parts[i]

            if not next_path.is_dir() and base_path.is_dir():
                existing_items = [
                    item
                    for item in base_path.iterdir()
                    if (i == len(parts) - 1 or not item.is_file()) and item.exists()
                ]
                parts[i] = self._find_closest_match(parts[i], existing_items)

            elif not next_path.exists():
                return super().joinpath(base_path, *parts[i:])

        return super().__new__(type(self), *parts)

    def _find_closest_match(self, target, candidates: list[Self]) -> str:
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
        return closest_match

    @staticmethod
    def _get_matching_characters_count(str1: str, str2: str) -> int:
        # don't consider a match if any char in the paths are not case-insensitive matches.
        if str1.lower() != str2.lower():
            return -1
        return sum(str1[i] == str2[i] for i in range(min(len(str1), len(str2))))

    @staticmethod
    def _fix_path_formatting(str_path: str) -> str:
        if not str_path.strip():
            return str_path

        formatted_path = str_path.replace("\\", os.sep).replace("/", os.sep)

        if os.altsep is not None:
            formatted_path = formatted_path.replace(os.altsep, os.sep)

        # For Unix-like paths
        formatted_path = re.sub(r"/{2,}", "/", formatted_path)

        # For Windows paths
        formatted_path = re.sub(r"\\{2,}", "\\\\", formatted_path)

        return formatted_path.rstrip(os.sep)


def locate_game_path(game: Game):
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
