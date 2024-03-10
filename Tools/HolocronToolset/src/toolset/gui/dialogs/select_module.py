from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5 import QtCore
from PyQt5.QtWidgets import QDialog, QFileDialog, QListWidgetItem

from pykotor.common.module import Module
from pykotor.resource.formats.erf.erf_data import ERFType

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget
    from pykotor.common.misc import CaseInsensitiveDict
    from toolset.data.installation import HTInstallation


class SelectModuleDialog(QDialog):
    def __init__(self, parent: QWidget, installation: HTInstallation):
        """Initializes the dialog to select a module.

        Args:
        ----
            parent (QWidget): Parent widget
            installation (HTInstallation): HT installation object

        Processing Logic:
        ----------------
            - Initializes the UI from the dialog design
            - Connects button click signals to methods
            - Builds the initial module list
            - Sets up filtering of module list.
        """
        super().__init__(parent)

        self._installation: HTInstallation = installation

        self.module: str = ""

        from toolset.uic.dialogs.select_module import Ui_Dialog  # pylint: disable=C0415  # noqa: PLC0415

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.openButton.clicked.connect(self.confirm)
        self.ui.cancelButton.clicked.connect(self.reject)
        self.ui.browseButton.clicked.connect(self.browse)
        self.ui.moduleList.currentRowChanged.connect(self.onRowChanged)
        self.ui.filterEdit.textEdited.connect(self.onFilterEdited)

        self._buildModuleList()

    def _buildModuleList(self):
        """Builds a list of installed modules.

        Args:
        ----
            self: The class instance

        Processing Logic:
        ----------------
            - Gets list of module names from installation object
            - Initializes empty set to track listed modules
            - Loops through modules list
            - Gets module root and checks if already listed
            - If not already listed, adds to list widget with name and root in brackets
            - Sets root as item data for later retrieval.
        """
        moduleNames: CaseInsensitiveDict[str] = self._installation.module_names()
        listedModules = set()

        for module in self._installation.modules_list():
            root = Module.get_root(module)

            if root in listedModules:
                continue
            listedModules.add(root)

            item = QListWidgetItem(f"{moduleNames[module]}  [{root}]")
            item.setData(QtCore.Qt.UserRole, root)
            self.ui.moduleList.addItem(item)

    def browse(self):
        capsule_types = " ".join(f"*.{e.name.lower()}" for e in ERFType) + " *.rim"
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Select module to open",
            str(self._installation.module_path()),
            f"Module File ({capsule_types})",
        )

        if filepath:
            self.module = Module.get_root(filepath)
            self.accept()

    def confirm(self):
        """Confirms the selected module.

        Args:
        ----
            self: The object instance

        Processing Logic:
        ----------------
            - Gets the currently selected module from the module list widget
            - Calls accept to close the dialog and apply changes.
        """
        self.module = self.ui.moduleList.currentItem().data(QtCore.Qt.UserRole)
        self.accept()

    def onRowChanged(self):
        self.ui.openButton.setEnabled(self.ui.moduleList.currentItem() is not None)

    def onFilterEdited(self):
        """Filter modules based on filter text.

        Args:
        ----
            self: The class instance

        Processing Logic:
        ----------------
            - Get filter text from filter edit box
            - Loop through each row in module list
            - Get item at that row
            - Hide item if filter text is not present in item text
            - This will filter and show only matching items.
        """
        text: str = self.ui.filterEdit.text()
        text_nocase = text.casefold()
        for row in range(self.ui.moduleList.count()):
            item: QListWidgetItem | None = self.ui.moduleList.item(row)
            item.setHidden(text_nocase not in item.text().casefold())
