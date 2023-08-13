import os
import platform
from pathlib import Path as OriginalPath

from pykotor.common.misc import Game


class Path(OriginalPath):
    def resolve_case_insensitive(self):
        # Quick checks for cases where resolving is unnecessary.
        if os.name != "posix" or self.exists():
            return self

        current_path = Path(self.root)
        for part in self.parts[1:]:
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
                return self

        return current_path


def locate_game_path(game: Game):
    locations = {
        "Windows": {
            Game.K1: [
                Path(r"C:\Program Files\Steam\steamapps\common\swkotor"),
                Path(r"C:\Program Files (x86)\Steam\steamapps\common\swkotor"),
                Path(r"C:\Program Files\LucasArts\SWKotOR"),
                Path(r"C:\Program Files (x86)\LucasArts\SWKotOR"),
                Path(r"C:\GOG Games\Star Wars - KotOR"),
            ],
            Game.K2: [
                Path(
                    r"C:\Program Files\Steam\steamapps\common\Knights of the Old Republic II",
                ),
                Path(
                    r"C:\Program Files (x86)\Steam\steamapps\common\Knights of the Old Republic II",
                ),
                Path(r"C:\Program Files\LucasArts\SWKotOR2"),
                Path(r"C:\Program Files (x86)\LucasArts\SWKotOR2"),
                Path(r"C:\GOG Games\Star Wars - KotOR2"),
            ],
        },
        "Darwin": {
            Game.K1: [
                Path(
                    "~/Library/Application Support/Steam/steamapps/common/swkotor/Knights of the Old Republic.app/Contents/Assets",
                ),
            ],
            Game.K2: [
                Path(
                    "~/Library/Application Support/Steam/steamapps/common/Knights of the Old Republic II/Knights of the Old Republic II.app/Contents/Assets",
                ),
            ],
        },
        "Linux": {
            Game.K1: [
                Path("~/.local/share/Steam/common/SteamApps/swkotor"),
                Path("~/.local/share/Steam/common/steamapps/swkotor"),
                Path("~/.local/share/Steam/common/swkotor"),
            ],
            Game.K2: [
                Path(
                    "~/.local/share/Steam/common/SteamApps/Knights of the Old Republic II",
                ),
                Path(
                    "~/.local/share/Steam/common/steamapps/Knights of the Old Republic II",
                ),
                Path("~/.local/share/Steam/common/Knights of the Old Republic II"),
            ],
        },
    }

    potential = locations[platform.system()][game]
    return next((path for path in potential if path.exists()), None)
