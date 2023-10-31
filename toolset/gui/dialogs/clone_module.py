from typing import Dict, List, NamedTuple

from data.installation import HTInstallation
from gui.dialogs.asyncloader import AsyncLoader
from PyQt5.QtWidgets import QDialog, QMessageBox, QWidget

from pykotor.common.module import Module
from pykotor.tools import module

_ROOT_INDEX = 0
_INSTALLATION_INDEX = 1


class ModuleOption(NamedTuple):
    name: str
    root: str
    files: List[str]
    installation: HTInstallation


class CloneModuleDialog(QDialog):
    def __init__(self, parent: QWidget, active: HTInstallation, installations: Dict[str, HTInstallation]):
        super().__init__(parent)

        from toolset.uic.dialogs import clone_module
        self.ui = clone_module.Ui_Dialog()
        self.ui.setupUi(self)

        self._active: HTInstallation = active
        self._installations: Dict[str, HTInstallation] = {active.name: active}

        self.ui.createButton.clicked.connect(self.ok)
        self.ui.cancelButton.clicked.connect(self.close)
        self.ui.filenameEdit.textChanged.connect(self.setPrefixFromFilename)
        self.ui.moduleSelect.currentIndexChanged.connect(self.changedModule)

        self.loadModules()

    def ok(self) -> None:
        installation = self.ui.moduleSelect.currentData().installation
        root = self.ui.moduleSelect.currentData().root
        identifier = self.ui.filenameEdit.text().lower()
        prefix = self.ui.prefixEdit.text().lower()
        name = self.ui.nameEdit.text()

        copyTextures = self.ui.copyTexturesCheckbox.isChecked()
        copyLightmaps = self.ui.copyLightmapsCheckbox.isChecked()
        keepDoors = self.ui.keepDoorsCheckbox.isChecked()
        keepPlaceables = self.ui.keepPlaceablesCheckbox.isChecked()
        keepSounds = self.ui.keepSoundsCheckbox.isChecked()
        keepPathing = self.ui.keepPathingCheckbox.isChecked()

        l = lambda: module.clone_module(root, identifier, prefix, name, installation, copyTextures=copyTextures,
                                        copyLightmaps=copyLightmaps, keepDoors=keepDoors, keepPlaceables=keepPlaceables,
                                        keepSounds=keepSounds, keepPathing=keepPathing)

        if copyTextures:
            QMessageBox(QMessageBox.Information, "This may take a while", "You have selected to create copies of the "
                        "texture. This process may add a few extra minutes to the waiting time.").exec_()

        if AsyncLoader(self, "Creating module", l, "Failed to create module").exec_():
            QMessageBox(QMessageBox.Information, "Clone Successful",
                        f"You can now warp to the cloned module '{identifier}'.").exec_()

    def loadModules(self) -> None:
        options: Dict[str, ModuleOption] = {}
        for installation in self._installations.values():
            for filename, name in installation.module_names().items():
                root = Module.get_root(filename)
                if root not in options:
                    options[root] = ModuleOption(name, root, [], installation)
                options[root].files.append(filename)

        for option in options.values():
            self.ui.moduleSelect.addItem(option.name, option)

    def changedModule(self, index: int):
        root = self.ui.moduleSelect.currentData().root
        self.ui.moduleRootEdit.setText(root)

    def setPrefixFromFilename(self) -> None:
        self.ui.prefixEdit.setText(self.ui.filenameEdit.text().upper()[:3])
