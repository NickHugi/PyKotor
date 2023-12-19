from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.type import ResourceType
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from PyQt5 import QtCore
from PyQt5.QtWidgets import QDialog, QListWidgetItem, QWidget
from toolset.gui.dialogs.asyncloader import AsyncBatchLoader
from toolset.utils.window import openResourceEditor

if TYPE_CHECKING:
    from pykotor.extract.file import FileResource
    from toolset.data.installation import HTInstallation


class FileSearcher(QDialog):

    def __init__(self, parent: QWidget, installations: dict[str, HTInstallation]):
        super().__init__(parent)

        from toolset.uic.dialogs import search
        self.ui = search.Ui_Dialog()
        self.ui.setupUi(self)

        self.results = []
        self.installation: HTInstallation | None = None

        self._installations: dict[str, HTInstallation] = installations
        for name, installation in installations.items():
            self.ui.installationSelect.addItem(name, installation)

    def accept(self) -> None:
        """Submits search parameters and starts search.

        Implicit Args:
        ----
            installation: {Installation object selected by user}
            caseSensitive: {True if case sensitive search is checked, False otherwise}
            filenamesOnly: {True if filenames only search is checked, False otherwise}
            text: {Search text entered by user}
            searchCore: {True if core search is checked, False otherwise}
            searchModules: {True if modules search is checked, False otherwise}
            searchOverride: {True if override search is checked, False otherwise}
            checkTypes: {List of selected resource types}.

        Returns
        -------
            None
        {Processes user search parameters by:
            - Getting selected installation
            - Getting search options from UI
            - Mapping checked resource types to list
            - Calling search function to start search}.
        """
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
               searchCore: bool, searchModules: bool, searchOverride: bool, checkTypes: list[ResourceType]) -> None:
        """Searches files and resources for text.

        Args:
        ----
            installation: HTInstallation - Installation object
            caseSensitive: bool - Case sensitivity flag
            filenamesOnly: bool - Search filenames only flag
            text: str - Search text
            searchCore: bool - Search core flag
            searchModules: bool - Search modules flag
            searchOverride: bool - Search override flag
            checkTypes: list[ResourceType] - Resource types to check

        Processing Logic:
        ----------------
            - Filters resources to search based on flags
            - Defines search function to check resources
            - Applies search function asynchronously to resources
            - Stores results in self.results.
        """
        searchIn: list[FileResource] = []
        results = []

        if searchCore:
            searchIn.extend(installation.chitin_resources())
        if searchModules:
            for module in installation.modules_list():
                searchIn.extend(installation.module_resources(module))
        if searchOverride:
            for folder in installation.override_list():
                searchIn.extend(installation.override_resources(folder))

        def search(resource: FileResource) -> None:
            resource_name = resource.resname()
            resource_data = decode_bytes_with_fallbacks(resource.data())

            name_check: bool = text in resource_name if caseSensitive else text.lower() in resource_name.lower()
            data_check: bool = text in resource_data if caseSensitive else text.lower() in resource_data.lower()

            if name_check or (not filenamesOnly and data_check):
                results.append(resource)

        searches = [lambda resource=resource: search(resource) for resource in searchIn]
        AsyncBatchLoader(self, "Searching...", searches, "An error occured during the search").exec_()

        self.results = results


class FileResults(QDialog):
    def __init__(self, parent: QWidget, results: list[FileResource], installation: HTInstallation):
        """Initialize the search results dialog.

        Args:
        ----
            parent (QWidget): Parent widget
            results (list[FileResource]): List of search results
            installation (HTInstallation): HT installation object
        Returns:
            None: Does not return anything
        - Populate the list widget with search results
        - Connect button click signals to accept and open actions
        - Save search results and installation object as member variables
        - Sort results alphabetically.
        """
        super().__init__(parent)

        from toolset.uic.dialogs.search_result import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.openButton.clicked.connect(self.open)
        self.ui.okButton.clicked.connect(self.accept)

        self.selection: FileResource | None = None
        self.installation: HTInstallation = installation

        for result in results:
            filename = f"{result.resname()}.{result.restype().extension}"
            item = QListWidgetItem(filename)
            item.setData(QtCore.Qt.UserRole, result)
            item.setToolTip(str(result.filepath()))
            self.ui.resultList.addItem(item)

        self.ui.resultList.sortItems(QtCore.Qt.AscendingOrder)

    def accept(self) -> None:
        """Accepts the current selection from the result list.

        Args:
        ----
            self: The object instance.

        Returns:
        -------
            None: Does not return anything.
        Processes the current selection:
            - Gets the current item from the result list
            - Gets the data associated with the item if it exists
            - Sets the selection attribute to the data
            - Calls the parent accept method.
        """
        item = self.ui.resultList.currentItem()
        self.selection = item.data(QtCore.Qt.UserRole) if item is not None else None
        super().accept()

    def open(self):  # noqa: A003
        """Opens the current item in the result list.

        Args:
        ----
            self: The class instance.

        Returns:
        -------
            None: Does not return anything.
        - Gets the current item from the result list
        - Checks if an item is selected
        - Gets the FileResource object from the item's data
        - Opens the resource editor window with the resource's details.
        """
        item = self.ui.resultList.currentItem()
        if item:
            resource: FileResource = item.data(QtCore.Qt.UserRole)
            openResourceEditor(resource.filepath(), resource.resname(), resource.restype(), resource.data(),
                               self.installation, self.window().parent())
