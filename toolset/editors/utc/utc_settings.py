from typing import Optional

from PyQt5.QtCore import QSettings


class UTCSettings:
    def __init__(self):
        self.settings = QSettings('HolocronToolset', 'UTCEditor')

    @property
    def saveUnusedFields(self) -> bool:
        return self.settings.value("saveUnusedFields", True, bool)

    @saveUnusedFields.setter
    def saveUnusedFields(self, value: bool) -> None:
        self.settings.setValue('saveUnusedFields', value)

    @property
    def alwaysSaveK2Fields(self) -> bool:
        return self.settings.value("alwaysSaveK2Fields", False, bool)

    @alwaysSaveK2Fields.setter
    def alwaysSaveK2Fields(self, value: bool) -> None:
        self.settings.setValue('alwaysSaveK2Fields', value)
