from typing import Optional

from PyQt5.QtCore import QSettings


class GITSettings:
    def __init__(self, editor = None):
        self.settings = QSettings('HolocronToolset', 'GITEditor')

    @property
    def creatureLabel(self) -> str:
        return self.settings.value("creatureLabel", "", str)

    @creatureLabel.setter
    def creatureLabel(self, value: str) -> None:
        self.settings.setValue('creatureLabel', value)

    @property
    def doorLabel(self) -> str:
        return self.settings.value("doorLabel", "", str)

    @doorLabel.setter
    def doorLabel(self, value: str) -> None:
        self.settings.setValue('doorLabel', value)

    @property
    def placeableLabel(self) -> str:
        return self.settings.value("placeableLabel", "", str)

    @placeableLabel.setter
    def placeableLabel(self, value: str) -> None:
        self.settings.setValue('placeableLabel', value)

    @property
    def storeLabel(self) -> str:
        return self.settings.value("storeLabel", "", str)

    @storeLabel.setter
    def storeLabel(self, value: str) -> None:
        self.settings.setValue('storeLabel', value)

    @property
    def soundLabel(self) -> str:
        return self.settings.value("soundLabel", "", str)

    @soundLabel.setter
    def soundLabel(self, value: str) -> None:
        self.settings.setValue('soundLabel', value)

    @property
    def waypointLabel(self) -> str:
        return self.settings.value("waypointLabel", "", str)

    @waypointLabel.setter
    def waypointLabel(self, value: str) -> None:
        self.settings.setValue('waypointLabel', value)

    @property
    def cameraLabel(self) -> str:
        return self.settings.value("cameraLabel", "", str)

    @cameraLabel.setter
    def cameraLabel(self, value: str) -> None:
        self.settings.setValue('cameraLabel', value)

    @property
    def encounterLabel(self) -> str:
        return self.settings.value("encounterLabel", "", str)

    @encounterLabel.setter
    def encounterLabel(self, value: str) -> None:
        self.settings.setValue('encounterLabel', value)

    @property
    def triggerLabel(self) -> str:
        return self.settings.value("triggerLabel", "", str)

    @triggerLabel.setter
    def triggerLabel(self, value: str) -> None:
        self.settings.setValue('triggerLabel', value)

