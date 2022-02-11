import time
from typing import List, Dict, Set, NamedTuple

from PyQt5 import QtCore
from PyQt5.QtGui import QStandardItem
from PyQt5.QtWidgets import QDialog, QWidget, QMessageBox
from pykotor.common.language import LocalizedString
from pykotor.common.misc import ResRef
from pykotor.common.module import Module
from pykotor.extract.capsule import Capsule
from pykotor.extract.file import FileQuery
from pykotor.resource.formats.erf import ERF, ERFType, write_erf
from pykotor.resource.formats.gff import load_gff, write_gff
from pykotor.resource.formats.lyt.auto import load_lyt, write_lyt
from pykotor.resource.formats.mdl import load_mdl
from pykotor.resource.formats.rim import RIM, write_rim
from pykotor.resource.formats.tpc import write_tpc, TPC, TPCTextureFormat
from pykotor.resource.formats.vis import write_vis, VIS
from pykotor.resource.generics.are import dismantle_are
from pykotor.resource.generics.git import dismantle_git
from pykotor.resource.generics.ifo import dismantle_ifo
from pykotor.resource.generics.utd import dismantle_utd
from pykotor.resource.generics.utp import dismantle_utp
from pykotor.resource.generics.uts import dismantle_uts
from pykotor.resource.type import ResourceType, FileFormat
from pykotor.tools import model, module

from data.installation import HTInstallation
from misc import clone_module_ui
from misc.asyncloader import AsyncLoader

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
        self.ui = clone_module_ui.Ui_Dialog()
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

        AsyncLoader(self, "Creating module", l, "Failed to create module").exec_()

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
