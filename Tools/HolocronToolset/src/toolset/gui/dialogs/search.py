from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Generator

import qtpy

from qtpy import QtCore
from qtpy.QtWidgets import QDialog, QListWidgetItem

from pykotor.extract.file import FileResource
from pykotor.resource.type import ResourceType
from toolset.data.installation import HTInstallation
from toolset.gui.dialogs.asyncloader import AsyncLoader
from toolset.utils.window import open_resource_editor

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget



@dataclass
class FileSearchQuery:
    """Encapsulates search parameters for file search operations."""

    installation: HTInstallation
    caseSensitive: bool
    filenamesOnly: bool
    text: str
    searchCore: bool
    searchModules: bool
    searchOverride: bool
    checkTypes: list[ResourceType]


class FileSearcher(QDialog):
    fileResults = QtCore.Signal(list, HTInstallation)  # pyright: ignore[reportPrivateImportUsage]

    def __init__(self, parent: QWidget | None, installations: dict[str, HTInstallation]):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowMinMaxButtonsHint & ~QtCore.Qt.WindowContextHelpButtonHint)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.dialogs import (
                search,  # noqa: PLC0415  # pylint: disable=C0415
            )
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.dialogs import (
                search,  # noqa: PLC0415  # pylint: disable=C0415
            )
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.dialogs import (
                search,  # noqa: PLC0415  # pylint: disable=C0415
            )
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.dialogs import (
                search,  # noqa: PLC0415  # pylint: disable=C0415
            )
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = search.Ui_Dialog()
        self.ui.setupUi(self)
        assert installations, "No installations passed to FileSearcher"

        self._installations: dict[str, HTInstallation] = installations
        for name, installation in installations.items():
            self.ui.installationSelect.addItem(name, installation)

        # Connect the Select All checkbox signal to the slot
        self.ui.selectAllCheck.stateChanged.connect(self.toggle_all_checkboxes)

    def toggle_all_checkboxes(self, state):
        """Toggles the state of all checkboxes based on the Select All checkbox state."""
        check_state = state == QtCore.Qt.Checked
        self.ui.typeARECheck.setChecked(check_state)
        self.ui.typeGITCheck.setChecked(check_state)
        self.ui.typeIFOCheck.setChecked(check_state)
        self.ui.typeVISCheck.setChecked(check_state)
        self.ui.typeLYTCheck.setChecked(check_state)
        self.ui.typeDLGCheck.setChecked(check_state)
        self.ui.typeJRLCheck.setChecked(check_state)
        self.ui.typeUTCCheck.setChecked(check_state)
        self.ui.typeUTDCheck.setChecked(check_state)
        self.ui.typeUTECheck.setChecked(check_state)
        self.ui.typeUTICheck.setChecked(check_state)
        self.ui.typeUTPCheck.setChecked(check_state)
        self.ui.typeUTMCheck.setChecked(check_state)
        self.ui.typeUTWCheck.setChecked(check_state)
        self.ui.typeUTSCheck.setChecked(check_state)
        self.ui.typeUTTCheck.setChecked(check_state)
        self.ui.type2DACheck.setChecked(check_state)
        self.ui.typeNSSCheck.setChecked(check_state)
        self.ui.typeNCSCheck.setChecked(check_state)

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

        Returns:
        -------
            None
        """
        installation: HTInstallation = self.ui.installationSelect.currentData()
        assert bool(installation), "No installation chosen in FileSearcher"
        caseSensitive = self.ui.caseSensitiveRadio.isChecked()
        filenamesOnly = self.ui.filenamesOnlyCheck.isChecked()
        text = self.ui.searchTextEdit.text()

        searchCore = self.ui.coreCheck.isChecked()
        searchModules = self.ui.modulesCheck.isChecked()
        searchOverride = self.ui.overrideCheck.isChecked()

        checkTypes: list[ResourceType] = []
        if self.ui.typeARECheck.isChecked(): checkTypes.append(ResourceType.ARE)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeGITCheck.isChecked(): checkTypes.append(ResourceType.GIT)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeIFOCheck.isChecked(): checkTypes.append(ResourceType.IFO)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeVISCheck.isChecked(): checkTypes.append(ResourceType.VIS)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeLYTCheck.isChecked(): checkTypes.append(ResourceType.LYT)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeDLGCheck.isChecked(): checkTypes.append(ResourceType.DLG)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeJRLCheck.isChecked(): checkTypes.append(ResourceType.JRL)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeUTCCheck.isChecked(): checkTypes.append(ResourceType.UTC)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeUTDCheck.isChecked(): checkTypes.append(ResourceType.UTD)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeUTECheck.isChecked(): checkTypes.append(ResourceType.UTE)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeUTICheck.isChecked(): checkTypes.append(ResourceType.UTI)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeUTPCheck.isChecked(): checkTypes.append(ResourceType.UTP)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeUTMCheck.isChecked(): checkTypes.append(ResourceType.UTM)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeUTSCheck.isChecked(): checkTypes.append(ResourceType.UTS)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeUTTCheck.isChecked(): checkTypes.append(ResourceType.UTT)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeUTWCheck.isChecked(): checkTypes.append(ResourceType.UTW)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.type2DACheck.isChecked(): checkTypes.append(ResourceType.TwoDA)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeNSSCheck.isChecked(): checkTypes.append(ResourceType.NSS)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeNCSCheck.isChecked(): checkTypes.append(ResourceType.NCS)  # noqa: E701  # pylint: disable=multiple-statements

        query = FileSearchQuery(
            installation=installation,
            caseSensitive=caseSensitive,
            filenamesOnly=filenamesOnly,
            text=text,
            searchCore=searchCore,
            searchModules=searchModules,
            searchOverride=searchOverride,
            checkTypes=checkTypes,
        )

        self.search(query)

    def search(self, query: FileSearchQuery):
        """Searches files and resources for text.

        Args:
        ----
            query (FileSearchQuery): The search parameters
        """
        results: list[FileResource] = []

        def search_generator() -> Generator[FileResource, Any, None]:
            if query.searchCore:
                yield from query.installation.core_resources()
            if query.searchModules:
                for module in query.installation.modules_list():
                    yield from query.installation.module_resources(module)
            if query.searchOverride:
                for folder in query.installation.override_list():
                    yield from query.installation.override_resources(folder)

        searchText = query.text if query.caseSensitive else query.text.lower()

        def _search(resource: FileResource):
            resource_name: str = resource.resname()
            name_check: bool = searchText in (resource_name if query.caseSensitive else resource_name.lower())
            if name_check:
                results.append(resource)
            if query.filenamesOnly:
                return
            if resource.restype() not in query.checkTypes:
                return
            resource_data: str = resource.data().decode(encoding="ascii", errors="ignore")  # HACK:
            if searchText in (resource_data if query.caseSensitive else resource_data.lower()):
                results.append(resource)

        searchIn: Generator[FileResource, Any, None] = search_generator()
        searches: list[Callable[[FileResource], None]] = [lambda resource=resource: _search(resource) for resource in searchIn]
        AsyncLoader(self, "Searching...", searches, "An error occured during the search").exec_()
        self.fileResults.emit(results, query.installation)


class FileResults(QDialog):
    selectionSignal = QtCore.Signal(FileResource)  # pyright: ignore[reportPrivateImportUsage]

    def __init__(
        self,
        parent: QWidget,
        results: list[FileResource] | set[FileResource],
        installation: HTInstallation,
    ):
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
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.WindowMinMaxButtonsHint & ~QtCore.Qt.WindowContextHelpButtonHint)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.dialogs.search_result import (
                Ui_Dialog,  # noqa: PLC0415  # pylint: disable=C0415
            )
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.dialogs.search_result import (
                Ui_Dialog,  # noqa: PLC0415  # pylint: disable=C0415
            )
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.dialogs.search_result import (
                Ui_Dialog,  # noqa: PLC0415  # pylint: disable=C0415
            )
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.dialogs.search_result import (
                Ui_Dialog,  # noqa: PLC0415  # pylint: disable=C0415
            )
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.openButton.clicked.connect(self.open)
        self.ui.okButton.clicked.connect(self.accept)
        self.ui.resultList.itemDoubleClicked.connect(self.open)

        self.selection: FileResource | None = None
        self.installation: HTInstallation = installation

        for result in results:
            filename = result.filename()
            filepath = result.filepath()
            parent_name = filepath.name if filename != filepath.name else f"{filepath.parent.name}"
            item = QListWidgetItem(f"{parent_name}/{filename}")
            item.setData(QtCore.Qt.ItemDataRole.UserRole, result)
            item.setToolTip(str(result.filepath()))
            self.ui.resultList.addItem(item)  # type: ignore[arg-type]

        self.ui.resultList.sortItems(QtCore.Qt.SortOrder.AscendingOrder)  # type: ignore[arg-type]

    def accept(self):
        """Accepts the current selection from the result list.

        Args:
        ----
            self: The object instance.

        Processes the current selection:
            - Gets the current item from the result list
            - Gets the data associated with the item if it exists
            - Sets the selection attribute to the data
            - Calls the parent accept method.
        """
        item = self.ui.resultList.currentItem()
        if item:
            self.selection = item.data(QtCore.Qt.ItemDataRole.UserRole)
            self.selectionSignal.emit(self.selection)
        super().accept()

    def open(self):
        """Opens the current item in the result list.

        Args:
        ----
            self: The class instance.

        Processing Logic:
        ----------------
            - Gets the current item from the result list
            - Checks if an item is selected
            - Gets the FileResource object from the item's data
            - Opens the resource editor window with the resource's details.
        """
        item: QListWidgetItem | None = self.ui.resultList.currentItem()  # type: ignore[arg-type]
        if item is None:
            print("Nothing to open, item is None")
            return

        resource: FileResource = item.data(QtCore.Qt.ItemDataRole.UserRole)
        open_resource_editor(
            filepath=resource.filepath(),
            resref=resource.resname(),
            restype=resource.restype(),
            data=resource.data(),
            installation=self.installation,
            parent_window=self.window().parent(),  # type: ignore[arg-type]
        )
