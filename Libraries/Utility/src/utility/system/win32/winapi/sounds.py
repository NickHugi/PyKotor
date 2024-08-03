from __future__ import annotations

import ctypes


def play_system_sound(sound_type):
    ctypes.windll.user32.MessageBeep(sound_type)

play_system_sound(0x40)  # MB_ICONASTERISK