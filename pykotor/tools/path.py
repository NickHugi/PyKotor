from __future__ import annotations

import os
import platform
import re
from pathlib import Path, PurePosixPath, PureWindowsPath

from pykotor.common.misc import Game


class CaseAwarePath(Path):
    _flavour = PureWindowsPath._flavour if os.name == "nt" else PurePosixPath._flavour  # type: ignore pylint: disable-all

    def __new__(cls, *args, **kwargs) -> CaseAwarePath:
        # Build a path string from args
        path_str = os.path.join(*args)  # noqa: PTH118

        # Apply fix_path_formatting function
        fixed_path_str = CaseAwarePath._fix_path_formatting(path_str)

        # Create a new Path object with the fixed path
        if CaseAwarePath.should_resolve_case(fixed_path_str):
            return super().__new__(cls, fixed_path_str)._get_case_sensitive_path()

        return super().__new__(cls, fixed_path_str)

    def __truediv__(self, key) -> CaseAwarePath:
        """Uses divider operator to combine two paths.

        Args:
        ----
            self (CaseAwarePath):
            key (path-like object):

        """
        if not isinstance(key, CaseAwarePath):
            key = CaseAwarePath._fix_path_formatting(str(key))
        return CaseAwarePath(super().__truediv__(key))

    def __rtruediv__(self, key) -> CaseAwarePath:
        """Uses divider operator to combine two paths.

        Args:
        ----
            self (CaseAwarePath):
            key (path-like object):

        """
        if not isinstance(key, CaseAwarePath):
            key = CaseAwarePath._fix_path_formatting(str(key))
        return CaseAwarePath(super().__rtruediv__(key))

    def joinpath(self, *args) -> CaseAwarePath:
        new_path = self
        for arg in args:
            new_path /= arg
        return new_path

    def resolve(self, strict=False) -> CaseAwarePath:
        new_path = super().resolve(strict)
        if CaseAwarePath.should_resolve_case(new_path):
            new_path = self._get_case_sensitive_path()
        return new_path

    def endswith(self, text: str) -> bool:
        return str(self).endswith(text)

    def _get_case_sensitive_path(self) -> CaseAwarePath:
        parts = list(self.parts)

        for i in range(1, len(parts)):
            base_path: CaseAwarePath = super().__new__(type(self), *parts[:i])
            next_path: Path = super().joinpath(base_path, parts[i])

            # Find the first non-existent case-sensitive file/folder in hierarchy
            if not next_path.is_dir() and base_path.is_dir():
                def existing_items_gen():
                    for item in base_path.iterdir():
                        # Only the final path part can be a file.
                        if i == (len(parts) - 1) or item.is_dir():
                            yield item

                parts[i] = CaseAwarePath._find_closest_match(parts[i], existing_items_gen())

            # return a CaseAwarePath instance that resolves the case of existing items on disk, joined with the non-existing
            # parts in their original case.
            # if the root is not found, i.e. when i is 1 and base_path.exists() returns False, we return the original path here.
            elif not next_path.exists():
                return super().joinpath(base_path, *parts[i:])

        # return a CaseAwarePath instance without infinitely recursing through the constructor
        return super().__new__(type(self), *parts)

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

    @staticmethod
    def should_resolve_case(path) -> bool:
        if os.name == "nt":
            return False
        if isinstance(path, (CaseAwarePath, Path)):
            return path.is_absolute() and not path.exists()
        if isinstance(path, str):
            return os.path.isabs(path) and not os.path.exists(path)
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
