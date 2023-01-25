import os
import platform

from pykotor.common.misc import Game


def locate_game_path(game: Game):
    locations = {
        "Windows": {
            Game.K1: [
                r"C:\Program Files\Steam\steamapps\common\swkotor",
                r"C:\Program Files (x86)\Steam\steamapps\common\swkotor",
                r"C:\Program Files\LucasArts\SWKotOR",
                r"C:\Program Files (x86)\LucasArts\SWKotOR",
                r"C:\GOG Games\Star Wars - KotOR",
            ],
            Game.K2: [
                r"C:\Program Files\Steam\steamapps\common\Knights of the Old Republic II",
                r"C:\Program Files (x86)\Steam\steamapps\common\Knights of the Old Republic II",
                r"C:\Program Files\LucasArts\SWKotOR2",
                r"C:\Program Files (x86)\LucasArts\SWKotOR2",
                r"C:\GOG Games\Star Wars - KotOR2",
            ]
        },
        "Darwin": {
            Game.K1: [
                "~/Library/Application Support/Steam/SteamApps/common/swkotor",
            ],
            Game.K2: [
                "~/Library/Application Support/Steam/SteamApps/common/Knights of the Old Republic II",
            ]
        },
        "Linux": {
            Game.K1: [
                "~/.local/share/Steam/common/SteamApps/swkotor",
                "~/.local/share/Steam/common/steamapps/swkotor",
                "~/.local/share/Steam/common/swkotor",
            ],
            Game.K2: [
                "~/.local/share/Steam/common/SteamApps/Knights of the Old Republic II",
                "~/.local/share/Steam/common/steamapps/Knights of the Old Republic II",
                "~/.local/share/Steam/common/Knights of the Old Republic II",
            ]
        }
    }

    potential = locations[platform.system()][game]
    for path in potential:
        if os.path.exists(path):
            return path
    else:
        return None
