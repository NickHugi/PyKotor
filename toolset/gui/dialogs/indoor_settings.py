from typing import List

from PyQt5.QtWidgets import QDialog, QWidget

from data.installation import HTInstallation
from data.indoorkit import Kit
from data.indoormap import IndoorMap


class IndoorMapSettings(QDialog):
    def __init__(self, parent: QWidget, installation: HTInstallation, indoorMap: IndoorMap, kits: List[Kit]):
        super().__init__(parent)

        from toolset.uic.dialogs.indoor_settings import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.nameEdit.setInstallation(installation)

        self._indoorMap: IndoorMap = indoorMap
        self._kits: List[Kit] = kits

        self.ui.nameEdit.setLocstring(indoorMap.name)
        self.ui.colorEdit.setColor(indoorMap.lighting)
        self.ui.warpCodeEdit.setText(indoorMap.moduleId)

        self.ui.skyboxSelect.addItem("[None]", "")
        for kit in kits:
            for skybox in kit.skyboxes.keys():
                self.ui.skyboxSelect.addItem(skybox, skybox)
        self.ui.skyboxSelect.setCurrentText(indoorMap.skybox)

    def _setupSignals(self) -> None:
        ...

    def accept(self) -> None:
        super().accept()

        self._indoorMap.name = self.ui.nameEdit.locstring()
        self._indoorMap.lighting = self.ui.colorEdit.color()
        self._indoorMap.moduleId = self.ui.warpCodeEdit.text()
        self._indoorMap.skybox = self.ui.skyboxSelect.currentData()
