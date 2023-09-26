from PyQt5 import QtCore
from PyQt5.QtWidgets import QDialog, QFileDialog, QListWidgetItem, QWidget

from pykotor.common.module import Module
from toolset.data.installation import HTInstallation


class SelectModuleDialog(QDialog):
    def __init__(self, parent: QWidget, installation: HTInstallation):
        super().__init__(parent)

        self._installation: HTInstallation = installation

        self.module: str = ""

        from toolset.uic.dialogs.select_module import Ui_Dialog

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.openButton.clicked.connect(self.confirm)
        self.ui.cancelButton.clicked.connect(self.reject)
        self.ui.browseButton.clicked.connect(self.browse)
        self.ui.moduleList.currentRowChanged.connect(self.onRowChanged)
        self.ui.filterEdit.textEdited.connect(self.onFilterEdited)

        self._buildModuleList()

    def _buildModuleList(self) -> None:
        moduleNames = self._installation.module_names()
        listedModules = set()

        for module in self._installation.modules_list():
            root = Module.get_root(module)

            if root in listedModules:
                continue
            listedModules.add(root)

            item = QListWidgetItem(f"{moduleNames[module]}  [{root}]")
            item.setData(QtCore.Qt.UserRole, root)
            self.ui.moduleList.addItem(item)

    def browse(self) -> None:
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Select module to open",
            self._installation.module_path(),
            "Module File (*.mod *.rim *.erf)",
        )

        if filepath:
            self.module = Module.get_root(filepath)
            self.accept()

    def confirm(self) -> None:
        self.module = self.ui.moduleList.currentItem().data(QtCore.Qt.UserRole)
        self.accept()

    def onRowChanged(self) -> None:
        self.ui.openButton.setEnabled(self.ui.moduleList.currentItem() is not None)

    def onFilterEdited(self) -> None:
        text = self.ui.filterEdit.text()
        for row in range(self.ui.moduleList.count()):
            item = self.ui.moduleList.item(row)
            item.setHidden(text.lower() not in item.text().lower())
