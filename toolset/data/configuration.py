from typing import List

from PyQt5.QtCore import QSettings


class Configuration:
    def __init__(self):
        self.installations: List[InstallationConfig] = []

        self.firstTime: bool = True

        self.twodaEditorPath: str = ""
        self.dlgEditorPath: str = ""
        self.gffEditorPath: str = ""
        self.tlkEditorPath: str = ""
        self.txtEditorPath: str = ""
        self.nssEditorPath: str = ""
        self.gffSpecializedEditors: bool = True

        self.extractPath: str = ""
        self.showModuleNames: bool = False
        self.mdlAllowDecompile: bool = False
        self.erfExternalEditors: bool = False

        self.reload()

    def reload(self):
        settings = QSettings('cortisol', 'holocrontoolset')

        self.firstTime = settings.value('firstTime', True, bool)

        self.installations = []
        games = settings.value('games', {})
        for name, data in games.items():
            installation = InstallationConfig(name, data['path'], bool(data['tsl']))
            self.installations.append(installation)

        self.twodaEditorPath = settings.value('2daEditor', "")
        self.dlgEditorPath = settings.value('dlgEditor', "")
        self.gffEditorPath = settings.value('gffEditor', "")
        self.tlkEditorPath = settings.value('tlkEditor', "")
        self.txtEditorPath = settings.value('txtEditor', "")
        self.nssEditorPath = settings.value('nssEditor', "")
        self.gffSpecializedEditors = settings.value('gffSpecialized', True, bool)

        self.extractPath = settings.value('tempDir', "")
        self.showModuleNames = settings.value('showModuleNames', True, bool)
        self.mdlAllowDecompile = settings.value('mdlDecompile', False, bool)
        self.erfExternalEditors = settings.value('encapsulatedExternalEditor', False, bool)

    def save(self):
        settings = QSettings('cortisol', 'holocrontoolset')

        settings.setValue('firstTime', self.firstTime)

        installations = {}
        for installation in self.installations:
            data = {'path': installation.path, 'tsl': installation.tsl}
            installations[installation.name] = data
        settings.setValue('games', installations)

        settings.setValue('2daEditor', self.twodaEditorPath)
        settings.setValue('dlgEditor', self.dlgEditorPath)
        settings.setValue('gffEditor', self.gffEditorPath)
        settings.setValue('tlkEditor', self.tlkEditorPath)
        settings.setValue('txtEditor', self.txtEditorPath)
        settings.setValue('nssEditor', self.nssEditorPath)
        settings.setValue('gffSpecialized', self.gffSpecializedEditors)

        settings.setValue('tempDir', self.extractPath)
        settings.setValue('showModuleNames', self.showModuleNames)
        settings.setValue('mdlDecompile', self.mdlAllowDecompile)
        settings.setValue('encapsulatedExternalEditor', self.erfExternalEditors)

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
