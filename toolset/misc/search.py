import operator
from typing import Dict, List, Optional

from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QDialog, QListWidgetItem
from pykotor.extract.file import FileResource
from pykotor.resource.type import ResourceType

from data.installation import HTInstallation
from misc.asyncloader import AsyncBatchLoader


class FileSearcher(QDialog):
    """
    Searches through the
    """

    def __init__(self, parent: QWidget, installations: Dict[str, HTInstallation]):
        super().__init__(parent)

        from misc import search_ui
        self.ui = search_ui.Ui_Dialog()
        self.ui.setupUi(self)

        self.results = []
        self.installation: Optional[HTInstallation] = None

        self._installations: Dict[str, HTInstallation] = installations
        for name, installation in installations.items():
            self.ui.installationSelect.addItem(name, installation)

    def accept(self) -> None:
        installation = self.ui.installationSelect.currentData()
        caseSensitive = self.ui.caseSensitiveRadio.isChecked()
        filenamesOnly = self.ui.filenamesOnlyCheck.isChecked()
        text = self.ui.searchTextEdit.text()

        searchCore = self.ui.coreCheck.isChecked()
        searchModules = self.ui.modulesCheck.isChecked()
        searchOverride = self.ui.overrideCheck.isChecked()

        checkTypes = []
        if self.ui.typeARECheck.isChecked(): checkTypes.append(ResourceType.ARE)
        if self.ui.typeGITCheck.isChecked(): checkTypes.append(ResourceType.GIT)
        if self.ui.typeIFOCheck.isChecked(): checkTypes.append(ResourceType.IFO)
        if self.ui.typeDLGCheck.isChecked(): checkTypes.append(ResourceType.DLG)
        if self.ui.typeJRLCheck.isChecked(): checkTypes.append(ResourceType.JRL)
        if self.ui.typeUTCCheck.isChecked(): checkTypes.append(ResourceType.UTC)
        if self.ui.typeUTDCheck.isChecked(): checkTypes.append(ResourceType.UTD)
        if self.ui.typeUTECheck.isChecked(): checkTypes.append(ResourceType.UTE)
        if self.ui.typeUTICheck.isChecked(): checkTypes.append(ResourceType.UTI)
        if self.ui.typeUTPCheck.isChecked(): checkTypes.append(ResourceType.UTP)
        if self.ui.typeUTMCheck.isChecked(): checkTypes.append(ResourceType.UTM)
        if self.ui.typeUTWCheck.isChecked(): checkTypes.append(ResourceType.UTW)
        if self.ui.typeUTSCheck.isChecked(): checkTypes.append(ResourceType.UTS)
        if self.ui.typeUTTCheck.isChecked(): checkTypes.append(ResourceType.UTT)
        if self.ui.type2DACheck.isChecked(): checkTypes.append(ResourceType.TwoDA)
        if self.ui.typeNSSCheck.isChecked(): checkTypes.append(ResourceType.NSS)
        if self.ui.typeNCSCheck.isChecked(): checkTypes.append(ResourceType.NCS)

        self.search(installation, caseSensitive, filenamesOnly, text, searchCore, searchModules, searchOverride, checkTypes)
        self.installation = installation
        super().accept()

    def search(self, installation: HTInstallation, caseSensitive: bool, filenamesOnly: bool, text: str,
               searchCore: bool, searchModules: bool, searchOverride: bool, checkTypes: List[ResourceType]) -> None:
        searchIn: List[FileResource] = []
        results = []

        if searchCore:
            searchIn.extend(installation.chitin_resources())
        if searchModules:
            [searchIn.extend(installation.module_resources(module)) for module in installation.modules_list()]
        if searchOverride:
            [searchIn.extend(installation.override_resources(folder)) for folder in installation.override_list()]

        def search(resource):
            if resource.restype() in checkTypes:
                if caseSensitive and text in resource.resname():
                    results.append(resource)
                elif caseSensitive and text.lower() in resource.resname().lower():
                    results.append(resource)
                elif not filenamesOnly:
                    decoded = resource.data().decode(errors='ignore')
                    if caseSensitive and text in decoded:
                        results.append(resource)
                    elif not caseSensitive and text.lower() in decoded.lower():
                        results.append(resource)

        searches = [lambda resource=resource: search(resource) for resource in searchIn]
        AsyncBatchLoader(self, "Searching...", searches, "An error occured during the search").exec_()

        self.results = results


class FileResults(QDialog):
    def __init__(self, parent: QWidget, results: List[FileResource], installation: HTInstallation):
        super().__init__(parent)
        self.ui = search_result_ui.Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.openButton.clicked.connect(self.open)
        self.ui.okButton.clicked.connect(self.accept)

        self.selection: Optional[FileResource] = None
        self.installation: HTInstallation = installation

        for result in results:
            filename = "{}.{}".format(result.resname(), result.restype().extension)
            item = QListWidgetItem(filename)
            item.setData(QtCore.Qt.UserRole, result)
            item.setToolTip(result.filepath())
            self.ui.resultList.addItem(item)

        self.ui.resultList.sortItems(QtCore.Qt.AscendingOrder)

    def accept(self) -> None:
        item = self.ui.resultList.currentItem()
        self.selection = item.data(QtCore.Qt.UserRole) if item is not None else None
        super().accept()

    def open(self):
        item = self.ui.resultList.currentItem()
        if item:
            resource: FileResource = item.data(QtCore.Qt.UserRole)
            self.parent().openResourceEditor(resource.filepath(), resource.resname(), resource.restype(), resource.data())
