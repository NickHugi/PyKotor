from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Generator

from pykotor.resource.type import ResourceType
from PyQt5 import QtCore
from PyQt5.QtWidgets import QDialog, QListWidgetItem, QWidget
from toolset.gui.dialogs.asyncloader import AsyncBatchLoader
from toolset.utils.window import openResourceEditor

if TYPE_CHECKING:
    from pykotor.extract.file import FileResource
    from toolset.data.installation import HTInstallation


class FileSearcher(QDialog):

    def __init__(self, parent: QWidget, installations: dict[str, HTInstallation]):
        super().__init__(self)

        from toolset.uic.dialogs import search
        self.ui = search.Ui_Dialog()
        self.ui.setupUi(self)

        self.results: list[FileResource] = []
        self.installation: HTInstallation | None = None

        self._installations: dict[str, HTInstallation] = installations
        for name, installation in installations.items():
            self.ui.installationSelect.addItem(name, installation)

    def accept(self):
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
        installation: HTInstallation = self.ui.installationSelect.currentData()
        caseSensitive = self.ui.caseSensitiveRadio.isChecked()
        filenamesOnly = self.ui.filenamesOnlyCheck.isChecked()
        text = self.ui.searchTextEdit.text()

        searchCore = self.ui.coreCheck.isChecked()
        searchModules = self.ui.modulesCheck.isChecked()
        searchOverride = self.ui.overrideCheck.isChecked()

        checkTypes: list[ResourceType] = []
        if self.ui.typeARECheck.isChecked(): checkTypes.append(ResourceType.ARE)  # noqa: E701
        if self.ui.typeGITCheck.isChecked(): checkTypes.append(ResourceType.GIT)  # noqa: E701
        if self.ui.typeIFOCheck.isChecked(): checkTypes.append(ResourceType.IFO)  # noqa: E701
        if self.ui.typeDLGCheck.isChecked(): checkTypes.append(ResourceType.DLG)  # noqa: E701
        if self.ui.typeJRLCheck.isChecked(): checkTypes.append(ResourceType.JRL)  # noqa: E701
        if self.ui.typeUTCCheck.isChecked(): checkTypes.append(ResourceType.UTC)  # noqa: E701
        if self.ui.typeUTDCheck.isChecked(): checkTypes.append(ResourceType.UTD)  # noqa: E701
        if self.ui.typeUTECheck.isChecked(): checkTypes.append(ResourceType.UTE)  # noqa: E701
        if self.ui.typeUTICheck.isChecked(): checkTypes.append(ResourceType.UTI)  # noqa: E701
        if self.ui.typeUTPCheck.isChecked(): checkTypes.append(ResourceType.UTP)  # noqa: E701
        if self.ui.typeUTMCheck.isChecked(): checkTypes.append(ResourceType.UTM)  # noqa: E701
        if self.ui.typeUTWCheck.isChecked(): checkTypes.append(ResourceType.UTW)  # noqa: E701
        if self.ui.typeUTSCheck.isChecked(): checkTypes.append(ResourceType.UTS)  # noqa: E701
        if self.ui.typeUTTCheck.isChecked(): checkTypes.append(ResourceType.UTT)  # noqa: E701
        if self.ui.type2DACheck.isChecked(): checkTypes.append(ResourceType.TwoDA)  # noqa: E701
        if self.ui.typeNSSCheck.isChecked(): checkTypes.append(ResourceType.NSS)  # noqa: E701
        if self.ui.typeNCSCheck.isChecked(): checkTypes.append(ResourceType.NCS)  # noqa: E701

        self.search(installation, caseSensitive, filenamesOnly, text, searchCore, searchModules, searchOverride, checkTypes)
        self.installation = installation
        super().accept()

    def search(self, installation: HTInstallation, caseSensitive: bool, filenamesOnly: bool, text: str,
               searchCore: bool, searchModules: bool, searchOverride: bool, checkTypes: list[ResourceType]):
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
        results: list[FileResource] = []

        def search_generator() -> Generator[FileResource, Any, None]:
            if searchCore:
                yield from installation.chitin_resources()
            if searchModules:
                for module in installation.modules_list():
                    yield from installation.module_resources(module)
            if searchOverride:
                for folder in installation.override_list():
                    yield from installation.override_resources(folder)

        lowercase_text = text.lower()

        def search(resource: FileResource):
            resource_name: str = resource.resname()

            name_check: bool = text in resource_name if caseSensitive else lowercase_text in resource_name.lower()
            if name_check:
                results.append(resource)
                return
            if not filenamesOnly:
                resource_data: str = resource.data().decode(encoding="windows-1252", errors="ignore")
                data_check: bool = text in resource_data if caseSensitive else lowercase_text in resource_data.lower()
                if data_check:
                    results.append(resource)

        searchIn: Generator[FileResource, Any, None] = search_generator()
        searches: list[Callable[[FileResource], None]] = [lambda resource=resource: search(resource) for resource in searchIn]
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

        Processing Logic:
        ----------------
            - Populate the list widget with search results
            - Connect button click signals to accept and open actions
            - Save search results and installation object as member variables
            - Sort results alphabetically.
        """
        super().__init__(self)

        from toolset.uic.dialogs.search_result import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.openButton.clicked.connect(self.open)
        self.ui.okButton.clicked.connect(self.accept)

        self.selection: FileResource | None = None
        self.installation: HTInstallation = installation

        for result in results:
            item = QListWidgetItem(result.filename())
            item.setData(QtCore.Qt.UserRole, result)
            item.setToolTip(str(result.filepath()))
            self.ui.resultList.addItem(item)

        self.ui.resultList.sortItems(QtCore.Qt.AscendingOrder)

    def accept(self):
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

        Processing Logic:
        ----------------
            - Gets the current item from the result list
            - Checks if an item is selected
            - Gets the FileResource object from the item's data
            - Opens the resource editor window with the resource's details.
        """
        item: QListWidgetItem | None = self.ui.resultList.currentItem()
        if item:
            resource: FileResource = item.data(QtCore.Qt.UserRole)
            openResourceEditor(resource.filepath(), resource.resname(), resource.restype(), resource.data(),
                               self.installation, self.window().parent())
