from __future__ import annotations

import os

from qtpy.QtCore import QUrl
from qtpy.QtMultimedia import QSoundEffect


class SoundManager:
    def __init__(self):
        self.sounds: dict[str, QSoundEffect] = {}
        self.enabled = True
        
        # Define sound file mappings.
        # Sound files are loaded from resources/sounds/ directory if available.
        # If sounds are not found, the game continues silently without errors.
        self.sound_files = {
            "draw": "draw.wav",
            "play_card": "play.wav",
            "stand": "stand.wav",
            "win_round": "win_round.wav",
            "lose_round": "lose_round.wav",
            "game_over": "game_over.wav",
            "bust": "bust.wav"
        }
        
        self._load_sounds()
        
    def _load_sounds(self):
        """Load sound effects from resources/sounds directory if available.
        
        Looks for sound files in holopazaak/resources/sounds/ relative to the package.
        If the directory or files don't exist, the game continues without sounds.
        This allows the game to function even without audio assets.
        """
        base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "sounds")
        
        if not os.path.exists(base_path):
            return

        for name, filename in self.sound_files.items():
            path = os.path.join(base_path, filename)
            if os.path.exists(path):
                effect = QSoundEffect()
                effect.setSource(QUrl.fromLocalFile(path))
                self.sounds[name] = effect

    def play(self, sound_name: str):
        if not self.enabled:
            return
            
        if sound_name in self.sounds:
            self.sounds[sound_name].play()
            
    def toggle(self):
        self.enabled = not self.enabled

