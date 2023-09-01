from __future__ import annotations

import os
import platform
import re
from pathlib import Path, PurePosixPath, PureWindowsPath

from pykotor.common.misc import Game


class CustomPath(Path):
    _flavour = PureWindowsPath._flavour if os.name == "nt" else PurePosixPath._flavour  # type: ignore

    def __new__(cls, *args, **kwargs):
        # Check if all arguments are already CustomPath instances
        if all(isinstance(arg, CustomPath) for arg in args):
            return super().__new__(cls, *args, **kwargs)
        # Build a path string from args
        path_str = os.path.join(*args)

        # Apply fix_path_formatting function
        fixed_path_str = fix_path_formatting(path_str)

        # Create a new Path object with the fixed path
        return super().__new__(cls, fixed_path_str)

    def __truediv__(self, key):
        if not isinstance(key, CustomPath):
            key = fix_path_formatting(key)
        new_path = super().__truediv__(key)
        return CustomPath(new_path)

    def join(self, *args):
        # Custom logic for join
        new_path = self
        for arg in args:
            new_path /= arg
        return CustomPath(new_path)


def fix_path_formatting(path: str | object) -> str:
    if path is None:
        msg = "path cannot be None"
        raise ValueError(msg)

    str_path: str = str(path)
    if not str_path.strip():
        return str_path

    formatted_path = str_path.replace("\\", os.sep).replace("/", os.sep)

    if os.altsep is not None:
        formatted_path = formatted_path.replace(os.altsep, os.sep)

    # For Unix-like paths
    normalized_path = re.sub(r"/{2,}", "/", path)

    # For Windows paths
    normalized_path = re.sub(r"\\{2,}", "\\\\", normalized_path)

    return formatted_path.rstrip(os.sep)


def get_case_sensitive_path(path: str) -> str:
    if not path.strip():
        msg = "'path' cannot be null or whitespace."
        raise ValueError(msg)

    formatted_path: str = os.path.abspath(fix_path_formatting(path))
    if os.path.exists(formatted_path):
        return formatted_path
    # Getting the root based on the platform
    root = os.path.abspath(os.sep)
    parts = [p for p in formatted_path.split(os.path.sep) if p]

    # Get root directory
    root = os.path.abspath(os.sep)

    # Handle Windows drive letters
    if os.name == "nt":
        drive, _ = os.path.splitdrive(formatted_path)
        if drive:
            root = drive + os.path.sep

    # Ensure first element is root
    if parts and not os.path.isabs(parts[0]):
        parts = [root, *parts]
    else:
        parts[0] = root

    largest_existing_path_parts_index = -1
    case_sensitive_current_path = None
    i: int = 0
    for i in range(1, len(parts)):
        previous_current_path = os.path.join(parts[0], *parts[:i])
        current_path: str = os.path.join(previous_current_path, parts[i])
        if (
            platform.system() != "Windows"
            and not os.path.isdir(current_path)
            and os.path.isdir(previous_current_path)
        ):
            max_matching_characters = -1
            closest_match = parts[i]

            for folder_or_file in os.listdir(previous_current_path):
                full_path = os.path.join(previous_current_path, folder_or_file)

                if not os.path.exists(full_path):
                    continue
                if os.path.isfile(full_path) and i < len(parts) - 1:
                    continue

                matching_characters = get_matching_characters_count(
                    folder_or_file,
                    parts[i],
                )

                if matching_characters > max_matching_characters:
                    max_matching_characters = matching_characters
                    closest_match = folder_or_file
                    os.path.isfile(full_path)

            parts[i] = closest_match
        elif case_sensitive_current_path is None and not os.path.exists(current_path):
            largest_existing_path_parts_index = i
            case_sensitive_current_path = os.path.join(*parts[:i])
    if case_sensitive_current_path is None:
        return os.path.join(*parts)

    if largest_existing_path_parts_index > -1:
        combined_path = os.path.join(
            case_sensitive_current_path,
            os.path.join(*parts[largest_existing_path_parts_index:]),
        )
    else:
        combined_path = os.path.join(*parts)

    return combined_path


def get_matching_characters_count(str1, str2):
    if not str1:
        msg = "Value cannot be null or empty."
        raise ValueError(msg)
    if not str2:
        msg = "Value cannot be null or empty."
        raise ValueError(msg)

    matching_count = 0
    for i in range(min(len(str1), len(str2))):
        # don't consider a match if any char in the paths are not case-insensitive matches.
        if str1[i].lower() != str2[i].lower():
            return -1

        # increment matching count if case-sensitive match at this char index succeeds
        if str1[i] == str2[i]:
            matching_count += 1

    return matching_count


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
                CustomPath(
                    "~/.local/share/Steam/common/Knights of the Old Republic II",
                ),
            ],
        },
    }

    potential = locations[platform.system()][game]
    return next((path for path in potential if path.exists()), None)
