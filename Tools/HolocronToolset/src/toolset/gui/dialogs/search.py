from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Generator

from qtpy.QtCore import (
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtWidgets import QDialog, QListWidgetItem

from pykotor.extract.file import FileResource
from pykotor.resource.type import ResourceType
from toolset.data.installation import HTInstallation
from toolset.gui.dialogs.asyncloader import AsyncLoader
from toolset.utils.window import open_resource_editor

if TYPE_CHECKING:
    from pathlib import Path

    from qtpy.QtWidgets import QWidget



@dataclass
class FileSearchQuery:
    """Encapsulates search parameters for file search operations."""

    installation: HTInstallation
    case_sensitive: bool
    filenames_only: bool
    text: str
    search_core: bool
    search_modules: bool
    search_override: bool
    check_types: list[ResourceType]


class FileSearcher(QDialog):
    file_results = Signal(list, HTInstallation)  # pyright: ignore[reportPrivateImportUsage]

    def __init__(
        self,
        parent: QWidget | None,
        installations: dict[str, HTInstallation],
    ):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Dialog  # pyright: ignore[reportArgumentType]
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowMinMaxButtonsHint
            & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        from toolset.uic.qtpy.dialogs.search import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)
        
        assert installations, "No installations passed to FileSearcher"

        self._installations: dict[str, HTInstallation] = installations
        for name, installation in installations.items():
            self.ui.installationSelect.addItem(name, installation)

        # Connect the Select All checkbox signal to the slot
        self.ui.selectAllCheck.stateChanged.connect(self.toggle_all_checkboxes)

    def toggle_all_checkboxes(
        self,
        state: Qt.CheckState,
    ):
        """Toggles the state of all checkboxes based on the Select All checkbox state."""
        check_state: bool = state == Qt.CheckState.Checked
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
        check_types: list[ResourceType] = []
        if self.ui.typeARECheck.isChecked(): check_types.append(ResourceType.ARE)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeGITCheck.isChecked(): check_types.append(ResourceType.GIT)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeIFOCheck.isChecked(): check_types.append(ResourceType.IFO)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeVISCheck.isChecked(): check_types.append(ResourceType.VIS)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeLYTCheck.isChecked(): check_types.append(ResourceType.LYT)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeDLGCheck.isChecked(): check_types.append(ResourceType.DLG)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeJRLCheck.isChecked(): check_types.append(ResourceType.JRL)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeUTCCheck.isChecked(): check_types.append(ResourceType.UTC)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeUTDCheck.isChecked(): check_types.append(ResourceType.UTD)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeUTECheck.isChecked(): check_types.append(ResourceType.UTE)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeUTICheck.isChecked(): check_types.append(ResourceType.UTI)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeUTPCheck.isChecked(): check_types.append(ResourceType.UTP)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeUTMCheck.isChecked(): check_types.append(ResourceType.UTM)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeUTSCheck.isChecked(): check_types.append(ResourceType.UTS)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeUTTCheck.isChecked(): check_types.append(ResourceType.UTT)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeUTWCheck.isChecked(): check_types.append(ResourceType.UTW)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.type2DACheck.isChecked(): check_types.append(ResourceType.TwoDA)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeNSSCheck.isChecked(): check_types.append(ResourceType.NSS)  # noqa: E701  # pylint: disable=multiple-statements
        if self.ui.typeNCSCheck.isChecked(): check_types.append(ResourceType.NCS)  # noqa: E701  # pylint: disable=multiple-statements

        query = FileSearchQuery(
            installation=self.ui.installationSelect.currentData(),
            case_sensitive=self.ui.caseSensitiveRadio.isChecked(),
            filenames_only=self.ui.filenamesOnlyCheck.isChecked(),
            text=self.ui.searchTextEdit.text(),
            search_core=self.ui.coreCheck.isChecked(),
            search_modules=self.ui.modulesCheck.isChecked(),
            search_override=self.ui.overrideCheck.isChecked(),
            check_types=check_types,
        )

        self.search(query)

    def search(
        self,
        query: FileSearchQuery,
    ):
        """Searches files and resources for text.

        Args:
        ----
            query (FileSearchQuery): The search parameters
        """
        results: list[FileResource] = []

        def search_generator() -> Generator[FileResource, Any, None]:
            if query.search_core:
                yield from query.installation.core_resources()
            if query.search_modules:
                for module in query.installation.modules_list():
                    yield from query.installation.module_resources(module)
            if query.search_override:
                for folder in query.installation.override_list():
                    yield from query.installation.override_resources(folder)

        search_text = query.text if query.case_sensitive else query.text.lower()

        def _search(resource: FileResource):
            resource_name: str = resource.resname()
            name_check: bool = search_text in (resource_name if query.case_sensitive else resource_name.lower())
            if name_check:
                results.append(resource)
            if query.filenames_only:
                return
            if resource.restype() not in query.check_types:
                return
            resource_data: str = resource.data().decode(encoding="ascii", errors="ignore")  # HACK:
            if search_text in (resource_data if query.case_sensitive else resource_data.lower()):
                results.append(resource)

        search_in: Generator[FileResource, Any, None] = search_generator()
        searches: list[Callable[[FileResource], None]] = [lambda resource=resource: _search(resource) for resource in search_in]
        AsyncLoader(self, "Searching...", searches, "An error occured during the search").exec()
        self.file_results.emit(results, query.installation)


class FileResults(QDialog):
    sig_searchresults_selected = Signal(FileResource)  # pyright: ignore[reportPrivateImportUsage]

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
        self.setWindowFlags(
            Qt.WindowType.Dialog  # pyright: ignore[reportArgumentType]
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowMinMaxButtonsHint
            & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        from toolset.uic.qtpy.dialogs.search_result import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

        self.ui.openButton.clicked.connect(self.open)
        self.ui.okButton.clicked.connect(self.accept)
        self.ui.resultList.itemDoubleClicked.connect(self.open)

        self.selection: FileResource | None = None
        self.installation: HTInstallation = installation

        for result in results:
            filename: str = result.filename()
            filepath: Path = result.filepath()
            parent_name: str = filepath.name if filename != filepath.name else f"{filepath.parent.name}"
            item: QListWidgetItem = QListWidgetItem(f"{parent_name}/{filename}")
            item.setData(Qt.ItemDataRole.UserRole, result)
            item.setToolTip(str(result.filepath()))
            self.ui.resultList.addItem(item)  # type: ignore[arg-type]

        self.ui.resultList.sortItems(Qt.SortOrder.AscendingOrder)  # type: ignore[arg-type]

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
        item: QListWidgetItem | None = self.ui.resultList.currentItem()
        if item:
            self.selection = item.data(Qt.ItemDataRole.UserRole)
            self.sig_searchresults_selected.emit(self.selection)
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

        resource: FileResource = item.data(Qt.ItemDataRole.UserRole)
        open_resource_editor(
            resource,
            installation=self.installation,
            parent_window=self.window().parent(),  # type: ignore[arg-type]
        )
