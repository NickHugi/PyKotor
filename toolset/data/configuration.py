from typing import List

from PyQt5.QtCore import QSettings


class Configuration:
    def __init__(self):
        self.installations: List[InstallationConfig] = []

        self.firstTime: bool = True

        self.gffSpecializedEditors: bool = True

        self.nssCompilerPath: str = ""
        self.ncsDecompilerPath: str = ""

        self.extractPath: str = ""
        self.showModuleNames: bool = False
        self.mdlAllowDecompile: bool = False

        self.reload()

    def reload(self):
        settings = QSettings('cortisol', 'holocrontoolset')

        self.firstTime = settings.value('firstTime', True, bool)

        self.installations = []
        games = settings.value('games', {})
        for name, data in games.items():
            installation = InstallationConfig(name, data['path'], bool(data['tsl']))
            self.installations.append(installation)

        self.gffSpecializedEditors = settings.value('gffSpecialized', True, bool)

        self.nssCompilerPath = settings.value('nssCompilerPath', "")
        self.ncsDecompilerPath = settings.value('ncsDecompilerPath', "")

        self.extractPath = settings.value('tempDir', "")
        self.showModuleNames = settings.value('showModuleNames', True, bool)
        self.mdlAllowDecompile = settings.value('mdlDecompile', False, bool)

    def save(self):
        settings = QSettings('cortisol', 'holocrontoolset')

        settings.setValue('firstTime', self.firstTime)

        installations = {}
        for installation in self.installations:
            data = {'path': installation.path, 'tsl': installation.tsl}
            installations[installation.name] = data
        settings.setValue('games', installations)

        settings.setValue('gffSpecialized', self.gffSpecializedEditors)

        settings.setValue('nssCompilerPath', self.nssCompilerPath)
        settings.setValue('ncsDecompilerPath', self.ncsDecompilerPath)

        settings.setValue('tempDir', self.extractPath)
        settings.setValue('showModuleNames', self.showModuleNames)
        settings.setValue('mdlDecompile', self.mdlAllowDecompile)

        settings.sync()

    def installation(self, name: str):
        for installation in self.installations:
            if installation.name == name:
                return installation


class InstallationConfig:
    def __init__(self, name: str, path: str, tsl: bool):
        self.name: str = name
        self.path: str = path
        self.tsl: bool = tsl


class NoConfigurationSetError(Exception):
    ...
