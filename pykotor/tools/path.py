from __future__ import annotations

import os
import platform
from pathlib import Path, PurePosixPath, PureWindowsPath
import re

from pykotor.common.misc import Game

class CustomPath(Path):
    _flavour = PureWindowsPath._flavour if os.name == 'nt' else PurePosixPath._flavour # type: ignore

    def __new__(cls, *args, **kwargs):
        new_args: list[str] = [str(arg).replace("\\", "/") for arg in args]
        return super().__new__(cls, *new_args, **kwargs)

def fix_path_formatting(path):
    if path is None:
        raise ValueError("path cannot be None")

    if not path.strip():
        return path

    formatted_path = path.replace("\\", os.sep).replace("/", os.sep)

    if os.altsep is not None:
        formatted_path = formatted_path.replace(os.altsep, os.sep)

    formatted_path: str = re.sub(
        f"(?<!:){re.escape(os.sep)}+",
        os.sep,
        formatted_path
    )

    formatted_path = formatted_path.rstrip(os.sep)

    return formatted_path

def get_case_sensitive_path(path: str) -> str:
    if not path.strip():
        raise ValueError("'path' cannot be null or whitespace.")

    formatted_path: str = os.path.abspath(path.replace("/", os.path.sep))
    if os.path.exists(formatted_path):
        return formatted_path

    parts: list[str] = formatted_path.split(os.path.sep)
    current_path = os.path.splitdrive(formatted_path)[0]
    if current_path and not os.path.isabs(parts[0]):
        parts = [current_path] + parts
    if parts[0].endswith(":"):
        parts[0] += os.path.sep

    case_sensitive_current_path = None
    i: int = 0
    for i in range(1, len(parts)):
        current_path: str = os.path.join(os.path.sep.join(parts[:i]), parts[i])
        if os.name != "nt" and os.path.isdir(os.path.sep.join(parts[:i])):
            for folder_or_file_info in os.scandir(os.path.sep.join(parts[:i])):
                if folder_or_file_info.name == parts[i]:
                    break
            else:
                case_sensitive_current_path = os.path.sep.join(parts[:i])
                break
    return os.path.join(case_sensitive_current_path or "", os.path.sep.join(parts[i:]))

def get_matching_characters_count(str1, str2) -> int:
    if not str1 or not str2:
        raise ValueError("Value cannot be null or empty.")
    
    matching_count: int = sum(1 for i in range(min(len(str1), len(str2))) if str1[i] == str2[i])
    return -1 if matching_count == 0 else matching_count


def is_valid_path(path):
    try:
        # Check if the path exists and is not empty
        if not os.path.exists(path) or not path.strip():
            return False
        
        # Check if the path is properly formatted
        return os.path.normpath(path) == path
    except:
        return False

def resolve_case_insensitive(path: CustomPath):
    # Quick checks for cases where resolving is unnecessary.
    if os.name != "posix" or path.exists():
        return path

    current_path = CustomPath(path.root)
    for part in path.parts[1:]:
        # Using a set for faster membership checks.
        # Note: We're assuming case-insensitive filesystem, so we lowercase everything.
        entries = {entry.name.lower() for entry in current_path.iterdir()}

        if part.lower() in entries:
            # Reconstruct the original path, retaining the case of filenames.
            current_path /= next(
                entry
                for entry in current_path.iterdir()
                if entry.name.lower() == part.lower()
            )
        else:
            # If part was not found, just return the original path
            return path

    return current_path


def locate_game_path(game: Game):
    locations = {
        "Windows": {
            Game.K1: [
                CustomPath(r"C:\Program Files\Steam\steamapps\common\swkotor"),
                CustomPath(r"C:\Program Files (x86)\Steam\steamapps\common\swkotor"),
                CustomPath(r"C:\Program Files\LucasArts\SWKotOR"),
                CustomPath(r"C:\Program Files (x86)\LucasArts\SWKotOR"),
                CustomPath(r"C:\GOG Games\Star Wars - KotOR"),
            ],
            Game.K2: [
                CustomPath(
                    r"C:\Program Files\Steam\steamapps\common\Knights of the Old Republic II",
                ),
                CustomPath(
                    r"C:\Program Files (x86)\Steam\steamapps\common\Knights of the Old Republic II",
                ),
                CustomPath(r"C:\Program Files\LucasArts\SWKotOR2"),
                CustomPath(r"C:\Program Files (x86)\LucasArts\SWKotOR2"),
                CustomPath(r"C:\GOG Games\Star Wars - KotOR2"),
            ],
        },
        "Darwin": {
            Game.K1: [
                CustomPath(
                    "~/Library/Application Support/Steam/steamapps/common/swkotor/Knights of the Old Republic.app/Contents/Assets",
                ),
            ],
            Game.K2: [
                CustomPath(
                    "~/Library/Application Support/Steam/steamapps/common/Knights of the Old Republic II/Knights of the Old Republic II.app/Contents/Assets",
                ),
            ],
        },
        "Linux": {
            Game.K1: [
                CustomPath("~/.local/share/Steam/common/SteamApps/swkotor"),
                CustomPath("~/.local/share/Steam/common/steamapps/swkotor"),
                CustomPath("~/.local/share/Steam/common/swkotor"),
            ],
            Game.K2: [
                CustomPath(
                    "~/.local/share/Steam/common/SteamApps/Knights of the Old Republic II",
                ),
                CustomPath(
                    "~/.local/share/Steam/common/steamapps/Knights of the Old Republic II",
                ),
                CustomPath("~/.local/share/Steam/common/Knights of the Old Republic II"),
            ],
        },
    }

    potential = locations[platform.system()][game]
    return next((path for path in potential if path.exists()), None)
