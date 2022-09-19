from typing import Any

from PyQt5.QtCore import QSettings


class Settings:
    def __init__(self, scope: str):
        self.settings = QSettings("HolocronToolset", scope)

    @staticmethod
    def _addSetting(name: str, default: Any):
        prop = property(
            lambda this: this.settings.value(name, default),
            lambda this, val: this.settings.setValue(name, val)
        )
        return prop
