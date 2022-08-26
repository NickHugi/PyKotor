import os
from typing import List, Dict, Any

from PyQt5.QtCore import QSettings


class InstallationConfig:
    def __init__(self, name: str):
        self._settings = QSettings('HolocronToolset', 'Global')
        self._name: str = name

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        installations = self._settings.value("installations", {}, Dict[str, Any])
        installation = installations[self._name]

        del installations[self._name]
        installations[value] = installation
        installations[value]["name"] = value

        self._settings.setValue('installations', installations)
        self._name = value

    @property
    def path(self) -> str:
        installation = self._settings.value("installations", {})[self._name]
        return installation["path"]

    @path.setter
    def path(self, value: str) -> None:
        installations = self._settings.value("installations", {})
        installations[self._name]["path"] = value
        self._settings.setValue('installations', installations)

    @property
    def tsl(self) -> bool:
        installation = self._settings.value("installations", {})[self._name]
        return installation["tsl"]

    @tsl.setter
    def tsl(self, value: bool) -> None:
        installations = self._settings.value("installations", {})
        installations[self._name]["tsl"] = value
        self._settings.setValue('installations', installations)


class GlobalSettings:
    def __init__(self):
        self.settings = QSettings('HolocronToolset', 'Global')

    def installations(self) -> Dict[str, InstallationConfig]:
        if self.settings.value("installations", None) is None:
            self.settings.setValue("installations", {
                "KotOR": {"name": "KotOR", "path": "", "tsl": False},
                "TSL": {"name": "TSL", "path": "", "tsl": True}
            })

        installations = {}
        for name, installation in self.settings.value("installations", {}).items():
            installations[name] = InstallationConfig(name)

        return installations

    # region Strings
    @property
    def extractPath(self) -> str:
        return self.settings.value("extractPath", "", str)

    @extractPath.setter
    def extractPath(self, value: str) -> None:
        self.settings.setValue('extractPath', value)

    @property
    def nssCompilerPath(self) -> str:
        default = "ext/nwnnsscomp.exe" if os.name == "nt" else "ext/nwnnsscomp"
        return self.settings.value("nssCompilerPath", default, str)

    @nssCompilerPath.setter
    def nssCompilerPath(self, value: str) -> None:
        self.settings.setValue('nssCompilerPath', value)

    @property
    def ncsDecompilerPath(self) -> str:
        return self.settings.value("ncsDecompilerPath", "", str)

    @ncsDecompilerPath.setter
    def ncsDecompilerPath(self, value: str) -> None:
        self.settings.setValue('ncsDecompilerPath', value)
    # endregion

    # region Bools
    @property
    def disableRIMSaving(self) -> bool:
        return self.settings.value("disableRIMSaving", True, bool)

    @disableRIMSaving.setter
    def disableRIMSaving(self, value: bool) -> None:
        self.settings.setValue('disableRIMSaving', value)

    @property
    def firstTime(self) -> bool:
        return self.settings.value("firstTime", "", bool)

    @firstTime.setter
    def firstTime(self, value: bool) -> None:
        self.settings.setValue('firstTime', value)

    @property
    def gffSpecializedEditors(self) -> bool:
        return self.settings.value("gffSpecializedEditors", True, bool)

    @gffSpecializedEditors.setter
    def gffSpecializedEditors(self, value: bool) -> None:
        self.settings.setValue('gffSpecializedEditors', value)
    # endregion


class NoConfigurationSetError(Exception):
    ...
