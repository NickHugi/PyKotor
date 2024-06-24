from __future__ import annotations

from typing import TYPE_CHECKING

import qtpy

from qtpy import QtCore, QtGui
from qtpy.QtCore import QMimeData, Qt
from qtpy.QtGui import QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QAction, QFileDialog, QInputDialog, QLineEdit, QMenu, QMessageBox, QShortcut, QTableView

from pykotor.common.misc import ResRef
from pykotor.common.stream import BinaryReader
from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.formats.erf import ERF, ERFResource, ERFType, read_erf, write_erf
from pykotor.resource.formats.rim import RIM, read_rim, write_rim
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_capsule_file
from toolset.gui.common.filters import RobustSortFilterProxyModel
from toolset.gui.dialogs.save.generic_file_saver import FileSaveHandler
from toolset.gui.editor import Editor
from toolset.gui.widgets.settings.installations import GlobalSettings
from toolset.utils.window import openResourceEditor
from utility.error_handling import universal_simplify_exception
from utility.logger_util import RobustRootLogger
from utility.system.path import Path

if TYPE_CHECKING:
    import os

    from qtpy.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
    from qtpy.QtWidgets import QWidget

    from pykotor.resource.formats.rim import RIMResource
    from toolset.data.installation import HTInstallation

if qtpy.API_NAME in ("PyQt6", "PySide6"):
    from qtpy.QtCore import QRegularExpression as QRegExp
    from qtpy.QtGui import QRegularExpressionValidator as QRegExpValidator
else:
    from qtpy.QtCore import QRegExp
    from qtpy.QtGui import QRegExpValidator


def human_readable_size(byte_size: float) -> str:
    for unit in ["bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]:
        if byte_size < 1024:  # noqa: PLR2004
            return f"{round(byte_size, 2)} {unit}"
        byte_size /= 1024
    return str(byte_size)


class ERFSortFilterProxyModel(RobustSortFilterProxyModel):
    def get_sort_value(self, index: QtCore.QModelIndex) -> int:
        """Return the sort value based on the column."""
        srcModel = self.sourceModel()
        assert isinstance(srcModel, QStandardItemModel)
        if index.column() == 2:  # Size column display text not suitable for sort
            resource: ERFResource = srcModel.item(index.row(), 0).data()
            return len(resource.data)
        return self.sourceModel().data(index)


class ERFEditor(Editor):
    def __init__(self, parent: QWidget | None, installation: HTInstallation | None = None):
        """Initialize ERF Editor window.

        Args:
        ----
            parent: QWidget: Parent widget
            installation: HTInstallation: HT Installation object

        Processing Logic:
        ----------------
            - Set supported resource types
            - Initialize base editor window
            - Set up UI from designer file
            - Connect menu and signal handlers
            - Initialize model and connect to table view
            - Disable saving/loading to modules
            - Create new empty ERF.
        """
        supported: list[ResourceType] = [ResourceType.RIM, ResourceType.ERF, ResourceType.MOD, ResourceType.SAV]
        super().__init__(parent, "ERF Editor", "none", supported, supported, installation)
        self.resize(400, 250)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.editors.erf import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.editors.erf import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.editors.erf import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.editors.erf import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()
        self._is_capsule_editor = True
        self._has_changes = False

        self.model = QStandardItemModel(self)
        #self.ui.tableView.setModel(self.model)  # Old logic, before proxy model was added.

        self._proxy_model = ERFSortFilterProxyModel(self)
        self._proxy_model.setSourceModel(self.model)
        self.ui.tableView.setModel(self._proxy_model)

        self.ui.tableView.setSortingEnabled(False)
        self.ui.tableView.horizontalHeader().setSectionsClickable(True)
        self.ui.tableView.horizontalHeader().setSortIndicatorShown(True)
        self.ui.tableView.horizontalHeader().sectionClicked.connect(self.handleHeaderClick)
        self.ui.tableView.selectionModel().selectionChanged.connect(self.selectionChanged)

        # Ensure no sorting is applied initially
        self._proxy_model.setSortRole(QtCore.Qt.InitialSortOrderRole)
        self.ui.tableView.horizontalHeader().setSortIndicator(-1, QtCore.Qt.AscendingOrder)

        # Disable saving file into module
        self._saveFilter = self._saveFilter.replace(f";;Save into module ({self.CAPSULE_FILTER})", "")
        self._openFilter = self._openFilter.replace(f";;Load from module ({self.CAPSULE_FILTER})", "")

        self.new()

    def handleHeaderClick(self, column: int):
        # Enable sorting when a column is clicked
        if not self.ui.tableView.isSortingEnabled():
            self.ui.tableView.setSortingEnabled(True)

        self._proxy_model.toggle_sort(column)
        self.updateSortIndicator(column)

    def updateSortIndicator(self, column: int):
        sort_state = self._proxy_model._sort_states.get(column, 0)
        header = self.ui.tableView.horizontalHeader()
        if sort_state == 0:
            header.setSortIndicator(-1, QtCore.Qt.AscendingOrder)
        elif sort_state == 1:
            header.setSortIndicator(column, QtCore.Qt.AscendingOrder)
        elif sort_state == 2:
            header.setSortIndicator(column, QtCore.Qt.DescendingOrder)

    def _setupSignals(self):
        """Setup signal connections for UI elements.

        Processing Logic:
        ----------------
            - Connect extractButton clicked signal to extractSelected method
            - Connect loadButton clicked signal to selectFilesToAdd method
            - Connect unloadButton clicked signal to removeSelected method
            - Connect openButton clicked signal to openSelected method
            - Connect refreshButton clicked signal to refresh method
            - Connect tableView resourceDropped signal to addResources method
            - Connect tableView doubleClicked signal to openSelected method
            - Connect Del shortcut to removeSelected method.
        """
        self.ui.extractButton.clicked.connect(self.extractSelected)
        self.ui.loadButton.clicked.connect(self.selectFilesToAdd)
        self.ui.unloadButton.clicked.connect(self.removeSelected)
        self.ui.openButton.clicked.connect(self.openSelected)
        self.ui.refreshButton.clicked.connect(self.refresh)
        self.ui.tableView.resourceDropped.connect(self.addResources)
        self.ui.tableView.doubleClicked.connect(self.openSelected)

        QShortcut("Del", self).activated.connect(self.removeSelected)

        # Custom context menu for table view
        self.ui.tableView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.tableView.customContextMenuRequested.connect(self.openContextMenu)

    def promptConfirm(self) -> bool:
        result = QMessageBox.question(
            None,
            "Changes detected.",
            "The action you attempted would discard your changes. Continue?",
            buttons=QMessageBox.Yes | QMessageBox.No,
            defaultButton=QMessageBox.No,
        )
        return result == QMessageBox.Yes

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes):
        """Load resource file.

        Args:
        ----
            filepath: Path to resource file
            resref: Resource reference
            restype: Resource type
            data: File data

        Load resource file:
        ------------------
            - Clear existing model data
            - Set model column count to 3 and header labels
            - Enable refresh button
            - If ERF-type:
                - Parse file with erf reader
                - Add each resource as row to model
            - If RIM:
                - Parse file with rim reader
                - Add each resource as row to model
            - Else show error message file type not supported.
        """
        if self._has_changes and not self.promptConfirm():
            return
        self._has_changes = False
        super().load(filepath, resref, restype, data)

        self.model.clear()
        self.model.setColumnCount(3)
        self.model.setHorizontalHeaderLabels(["ResRef", "Type", "Size"])
        self.ui.refreshButton.setEnabled(True)

        if restype.name in (ResourceType.ERF, ResourceType.MOD, ResourceType.SAV):
            erf: ERF = read_erf(data)
            for resource in erf:
                resrefItem = QStandardItem(str(resource.resref))
                resrefItem.setData(resource)
                restypeItem = QStandardItem(resource.restype.extension.upper())
                sizeItem = QStandardItem(human_readable_size(len(resource.data)))
                self.model.appendRow([resrefItem, restypeItem, sizeItem])

        elif restype is ResourceType.RIM:
            rim: RIM = read_rim(data)
            for resource in rim:
                resrefItem = QStandardItem(str(resource.resref))
                resrefItem.setData(resource)
                restypeItem = QStandardItem(resource.restype.extension.upper())
                sizeItem = QStandardItem(human_readable_size(len(resource.data)))
                self.model.appendRow([resrefItem, restypeItem, sizeItem])

        else:
            QMessageBox(
                QMessageBox.Icon.Critical,
                "Unable to load file",
                "The file specified is not a MOD/ERF type file.",
                parent=self,
                flags=Qt.WindowType.Dialog | Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowSystemMenuHint,
            ).show()

    def build(self) -> tuple[bytes, bytes]:
        """Builds resource data from the model.

        Returns:
        -------
            data: The built resource data.
            b"": An empty bytes object.

        Processing Logic:
        ----------------
            - Loops through each item in the model and extracts the resource data
            - Writes the data to either a RIM or ERF based on the resource type
            - Returns the built data and an empty bytes object.
        """
        data = bytearray()
        resource: ERFResource | RIMResource

        if self._restype is ResourceType.RIM:
            rim = RIM()
            for i in range(self._proxy_model.rowCount()):
                source_index = self._proxy_model.mapToSource(self._proxy_model.index(i, 0))
                item = self.model.itemFromIndex(source_index)
                resource = item.data()
                rim.set_data(str(resource.resref), resource.restype, resource.data)
            write_rim(rim, data)

        elif self._restype in (ResourceType.ERF, ResourceType.MOD, ResourceType.SAV):  # sourcery skip: split-or-ifs
            erf = ERF(ERFType.from_extension(self._restype.extension))
            if self._restype is ResourceType.SAV:
                erf.is_save_erf = True
            for i in range(self._proxy_model.rowCount()):
                source_index = self._proxy_model.mapToSource(self._proxy_model.index(i, 0))
                item = self.model.itemFromIndex(source_index)
                resource = item.data()
                erf.set_data(str(resource.resref), resource.restype, resource.data)
            write_erf(erf, data)
        else:
            raise ValueError(f"Invalid restype for ERFEditor: {self._restype!r}")

        return bytes(data), b""

    def new(self):
        if self._has_changes and not self.promptConfirm():
            return
        self._has_changes = False
        super().new()
        self.model.clear()
        self.model.setColumnCount(3)
        self.model.setHorizontalHeaderLabels(["ResRef", "Type", "Size"])
        self.ui.refreshButton.setEnabled(False)

    def save(self):
        """Saves the current state of the editor to the file path.

        Processing Logic:
        ----------------
            - Checks if file path is None and calls saveAs() method to set the file path
            - Enables the refresh button on the UI
            - Builds the data from the editor contents
            - Opens the file path in write byte mode
            - Writes the data to the file.
        """
        self._has_changes = False
        # Must override the method as the superclass method breaks due to filepath always ending in .rim/mod/erf
        if self._filepath is None:
            self.saveAs()
            return

        self.ui.refreshButton.setEnabled(True)

        data: tuple[bytes, bytes] = self.build()
        self._revert = data[0]
        if is_capsule_file(self._filepath.parent) and not self._filepath.safe_isfile():
            try:
                self._saveNestedCapsule(*data)
            except ValueError as e:
                msg = str(e)
                if msg.startswith("You must save the ERFEditor"):  # HACK(th3w1zard1): fix later.
                    QMessageBox(
                        QMessageBox.Icon.Information,
                        "New resource added to parent ERF/RIM",
                        "You've added a new ERF/RIM and tried to save inside that new ERF/RIM's editor. You must save the ERFEditor you added the nested to first. Do so and try again."
                    ).exec_()
                else:
                    raise
        else:
            with self._filepath.open("wb") as file:
                file.write(data[0])

    def openContextMenu(self, position):
        selectedResources = self.getSelectedResources()
        if not selectedResources:
            RobustRootLogger.info("ERFEditor: Nothing selected to build context menu.")
            return

        mainMenu = QMenu(self)

        extractAction = QAction("Extract to...", self)
        extractAction.triggered.connect(self.extractSelected)
        mainMenu.addAction(extractAction)

        renameAction = QAction("Rename", self)
        renameAction.triggered.connect(self.renameSelected)
        mainMenu.addAction(renameAction)
        if len(selectedResources) != 1:
            renameAction.setEnabled(False)

        if self._filepath is not None:
            mainMenu.addSeparator()
            if all(resource.restype.target_type().contents == "gff" for resource in selectedResources):
                mainMenu.addAction("Open with GFF Editor").triggered.connect(
                    lambda *args, fp=self._filepath, **kwargs: self.openResources(fp, selectedResources, self._installation, gff_specialized=False))
                if self._installation is not None:
                    mainMenu.addAction("Open with Specialized Editor").triggered.connect(
                        lambda *args, fp=self._filepath, **kwargs: self.openResources(fp, selectedResources, self._installation, gff_specialized=True))
                    mainMenu.addAction("Open with Default Editor").triggered.connect(
                        lambda *args, fp=self._filepath, **kwargs: self.openResources(fp, selectedResources, self._installation, gff_specialized=None))

            elif self._installation is not None:
                mainMenu.addAction("Open with Editor").triggered.connect(
                    lambda *args, fp=self._filepath, **kwargs: self.openResources(fp, selectedResources, self._installation, gff_specialized=True))

        mainMenu.exec_(self.ui.tableView.viewport().mapToGlobal(position))

    def getSelectedResources(self) -> list[ERFResource]:
        selected_rows = self.ui.tableView.selectionModel().selectedRows()
        #selectedResources: list[ERFResource] = [self.model.itemFromIndex(rowItem).data() for rowItem in selected_rows]
        selectedResources: list[ERFResource] = [self.model.itemFromIndex(self._proxy_model.mapToSource(rowItem)).data() for rowItem in selected_rows]
        return selectedResources

    def extractSelected(self):
        """Extract selected resources to a folder.

        Processing Logic:
        ----------------
            - Get the target folder path from the file dialog
            - Check if a valid folder is selected
            - Get the selected rows from the table view
            - Iterate through the selected rows
            - Extract the resource data from the model
            - Write the resource data to a file in the target folder.
        """
        selectedResources = self.getSelectedResources()
        if not selectedResources:
            RobustRootLogger.info("ERFEditor: Nothing selected to save.")
        saveHandler = FileSaveHandler(selectedResources, parent=self)
        saveHandler.save_files()

    def renameSelected(self):
        indexes = self.ui.tableView.selectedIndexes()
        if not indexes:
            return

        index = indexes[0]
        source_index = self._proxy_model.mapToSource(index)
        item = self.model.itemFromIndex(source_index)
        resource: ERFResource = item.data()

        erfrim_filename = "ERF/RIM" if self._resname is None or self._restype is None else f"{self._resname}.{self._restype.extension}"
        new_resname, ok = self.getValidatedResRef(erfrim_filename, resource)
        if ok:
            resource.resref = ResRef(new_resname)
            item.setText(new_resname)
            self._has_changes = True

    def getValidatedResRef(self, erfrim_name: str, resource: ERFResource) -> tuple[str, bool]:
        dialog = QInputDialog(self)
        dialog.setWindowTitle(f"Rename {erfrim_name} Resource ResRef")
        dialog.setLabelText(f"Enter new ResRef ({resource.resref}):")
        dialog.setTextValue(str(resource.resref))
        dialog.setInputMode(QInputDialog.TextInput)

        inputField = dialog.findChild(QLineEdit)
        if inputField is None:
            RobustRootLogger.warning("inputField could not be found in parent class QLineEdit")
            return "", False
        inputField.setValidator(self.resRefValidator())

        while dialog.exec_() == QInputDialog.Accepted:
            new_resname = dialog.textValue()
            if ResRef.is_valid(new_resname):
                return new_resname, True
            QMessageBox.warning(self, "Invalid ResRef", f"The ResRef you entered ({new_resname}) is invalid. Please try again.")
        return "", False

    def resRefValidator(self) -> QRegExpValidator:
        return QRegExpValidator(QRegExp(r"^[a-zA-Z0-9_]*$"))

    def removeSelected(self):
        """Removes selected rows from table view.

        Removes selected rows from table view by:
            - Getting selected row indexes from table view
            - Reversing the list to remove from last to first
            - Removing the row from model using row number.
        """
        self._has_changes = True
        for index in reversed([index for index in self.ui.tableView.selectedIndexes() if not index.column()]):
            source_index = self._proxy_model.mapToSource(index)
            item: QStandardItem | None = self.model.itemFromIndex(source_index)
            if item is None:
                RobustRootLogger().warning("item was None in ERFEditor.removeSelected() at index %s", index)
                continue
            self.model.removeRow(item.row())

    def addResources(self, filepaths: list[str]):
        """Adds resources to the capsule.

        Args:
        ----
            filepaths: list of filepaths to add as resources

        Processing Logic:
        ----------------
            - Loops through each filepath
            - Resolves the filepath and opens it for reading
            - Splits the parent directory name to get the resref and restype
            - Creates an ERFResource object from the data
            - Adds rows to the model displaying the resref, restype and size
            - Catches any exceptions and displays an error message.
        """
        self._has_changes = True
        for filepath in filepaths:
            c_filepath = Path(filepath)
            try:
                resref, restype = ResourceIdentifier.from_path(c_filepath).validate().unpack()
                data = BinaryReader.load_file(c_filepath)
                resource = ERFResource(ResRef(resref), restype, data)

                resrefItem = QStandardItem(str(resource.resref))
                resrefItem.setData(resource)
                restypeItem = QStandardItem(resource.restype.extension.upper())
                resourceSizeStr = human_readable_size(len(resource.data))
                sizeItem = QStandardItem(resourceSizeStr)
                self.model.appendRow([resrefItem, restypeItem, sizeItem])
            except Exception as e:  # noqa: BLE001
                RobustRootLogger().exception("Failed to add resource at '%s'", c_filepath.absolute())
                error_msg = str(universal_simplify_exception(e)).replace("\n", "<br>")
                QMessageBox(
                    QMessageBox.Icon.Critical,
                    "Failed to add resource",
                    f"Could not add resource at '{c_filepath.absolute()}'<br><br>{error_msg}",
                    flags=Qt.WindowType.Dialog | Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowSystemMenuHint
                ).exec_()

    def selectFilesToAdd(self):
        filepaths: list[str] = QFileDialog.getOpenFileNames(self, "Load files into module")[:-1][0]
        self.addResources(filepaths)

    def openSelected(
        self,
        *,
        gff_specialized: bool | None = None,
    ):
        """Opens the selected resource in the editor.

        Processing Logic:
        ----------------
            - Checks if a filepath is set and shows error if not
            - Loops through selected rows in table
            - Gets the item and resource data
            - Checks resource type and skips nested types
            - Opens the resource in an editor window.
        """
        erfResources: list[ERFResource] = [self.model.itemFromIndex(self._proxy_model.mapToSource(index)).data() for index in self.ui.tableView.selectionModel().selectedRows(0)]
        if not erfResources:
            return
        if self._filepath is None:
            QMessageBox(
                QMessageBox.Icon.Critical,
                f"Cannot edit resource {erfResources[0].identifier()}. Filepath not set.",
                "This ERF/RIM must be saved to disk first, do so and try again.",
                QMessageBox.StandardButton.Ok,
                self,
                flags=Qt.WindowType.Dialog | Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowSystemMenuHint
            ).exec_()
            return

        self.openResources(
            self._filepath,
            erfResources,
            self._installation,
            self.savedFile,
            gff_specialized=gff_specialized,
        )

    @staticmethod
    def openResources(
        filepath: Path,
        resources: list[ERFResource],
        installation: HTInstallation | None = None,
        savedFileSignal: QtCore.pyqtBoundSignal | None = None,
        *,
        gff_specialized: bool | None = None,
    ):
        for resource in resources:
            new_filepath = filepath
            if resource.restype in (ResourceType.ERF, ResourceType.SAV, ResourceType.RIM, ResourceType.MOD):
                RobustRootLogger().info(f"Nested capsule selected for opening, appending resref/restype '{resource.resref}.{resource.restype}' to the filepath.")
                new_filepath /= str(ResourceIdentifier(str(resource.resref), resource.restype))

            _tempPath, editor = openResourceEditor(
                new_filepath,
                str(resource.resref),
                resource.restype,
                resource.data,
                installation,
                gff_specialized=gff_specialized
            )
            if savedFileSignal is not None and isinstance(editor, Editor):
                editor.savedFile.connect(savedFileSignal)

    def refresh(self):
        if self._has_changes and not self.promptConfirm():
            return
        if self._filepath is None:
            QMessageBox(
                QMessageBox.Icon.Critical,
                "Nothing to refresh.",
                "This ERFEditor was never loaded from a file, so there's nothing to refresh.",
                QMessageBox.StandardButton.Ok,
                self,
                flags=Qt.WindowType.Dialog | Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowSystemMenuHint
            ).exec_()
            return
        self._has_changes = False
        data: bytes = BinaryReader.load_file(self._filepath)
        self.load(self._filepath, self._resname, self._restype, data)

    def selectionChanged(self):
        """Updates UI controls based on table selection.

        Processing Logic:
        ----------------
            - Check if any rows are selected in the table view
            - If no rows selected, disable UI controls by calling _set_ui_controls_state(False)
            - If rows are selected, enable UI controls by calling _set_ui_controls_state(True).
        """
        if len(self.ui.tableView.selectedIndexes()) == 0:
            self._set_ui_controls_state(state=False)
        else:
            self._set_ui_controls_state(state=True)

    def _set_ui_controls_state(self, *, state: bool):
        self.ui.extractButton.setEnabled(state)
        self.ui.openButton.setEnabled(state)
        self.ui.unloadButton.setEnabled(state)

    def resourceSaved(self, filepath: str, resname: str, restype: ResourceType, data: bytes):
        """Saves resource data to the UI table.

        Args:
        ----
            filepath: Filepath of the resource being saved
            resname: Filestem Reference of the resource being saved
            restype: Type of the resource being saved
            data: Data being saved for the resource

        Processing Logic:
        ----------------
            - Check if filepath matches internal filepath
            - Iterate through selected rows in table view
            - Get item from selected index
            - Check if item resref/resname and restype match parameters
            - Set item data to passed in data.
        """
        if filepath != self._filepath:
            return

        for index in self.ui.tableView.selectionModel().selectedRows(0):
            source_index = self._proxy_model.mapToSource(index)
            item: ERFResource = self.model.itemFromIndex(source_index).data()
            if item.resref != resname:
                continue
            if item.restype != restype:
                continue
            item.data = data


class ERFEditorTable(QTableView):
    resourceDropped = QtCore.Signal(object)

    def __init__(self, parent: QWidget):
        super().__init__(parent)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.DropAction.CopyAction)
            event.accept()
            links: list[str] = [str(url.toLocalFile()) for url in event.mimeData().urls()]
            model = self.model()
            existing_items = {
                f"{model.item(row, 0).text()}.{model.item(row, 1).text()}".strip().lower()
                for row in range(model.rowCount())
            }
            always = False
            never = False
            to_skip: list[str] = []
            for link in links:
                if link.lower() in existing_items:
                    if always:
                        response = QMessageBox.Yes
                    elif never:
                        response = QMessageBox.No
                    else:
                        msgBox = QMessageBox()
                        msgBox.setIcon(QMessageBox.Warning)
                        msgBox.setWindowTitle("Duplicate Resource dropped.")
                        msgBox.setText(f"'{link}' already exists in the table. Do you want to overwrite?")
                        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.YesToAll | QMessageBox.No | QMessageBox.NoToAll | QMessageBox.Abort)
                        msgBox.button(QMessageBox.Yes).setText("Overwrite")
                        msgBox.button(QMessageBox.YesToAll).setText("Overwrite All")
                        msgBox.button(QMessageBox.No).setText("Skip")
                        msgBox.button(QMessageBox.NoToAll).setText("Skip All")
                        msgBox.setDefaultButton(QMessageBox.Abort)
                        response = msgBox.exec_()
                    if response == QMessageBox.Yes:
                        for row in range(self.model().rowCount()):
                            filename = f"{model.item(row, 0).text()}.{model.item(row, 1).text()}".strip().lower()
                            if filename == link.lower().strip():
                                print(f"Removing '{filename}' from the erf/rim.")
                                self.model().removeRow(row)
                                break
                    elif response == QMessageBox.No:
                        to_skip.append(link)
                    elif response == QMessageBox.Abort:
                        return
                    elif response == QMessageBox.YesToAll:
                        always = True
                        for row in range(self.model().rowCount()):
                            filename = f"{model.item(row, 0).text()}.{model.item(row, 1).text()}".strip().lower()
                            if filename == link.lower().strip():
                                print(f"Removing '{filename}' from the erf/rim.")
                                self.model().removeRow(row)
                                break
                    elif response == QMessageBox.NoToAll:
                        never = True
                        to_skip.append(link)

            for link in to_skip:
                print(f"Skipping dropped filename '{link}'")
                links.remove(link)
            if not links:
                print("Nothing dropped, or everything dropped was skipped.")
                return
            self.resourceDropped.emit(links)
        else:
            event.ignore()

    def startDrag(self, actions: QtCore.Qt.DropActions | QtCore.Qt.DropAction):
        """Starts a drag operation with the selected items.

        Args:
        ----
            actions: QtCore.Qt.DropActions | QtCore.Qt.DropAction: The allowed actions for the drag

        Processing Logic:
        ----------------
            - Extracts selected items to a temp directory
            - Creates a list of local file URLs from the extracted files
            - Sets the file URLs on a QMimeData object
            - Creates a drag object with the mime data
            - Executes the drag with the allowed actions.
        """
        tempDir = Path(GlobalSettings().extractPath)

        if not tempDir.safe_isdir():
            if tempDir.safe_isfile() or tempDir.exists():
                RobustRootLogger().error(f"tempDir '{tempDir}' exists but was not a valid filesystem folder.")
            else:
                tempDir.mkdir(parents=True, exist_ok=True)
            if not tempDir.safe_isdir():
                RobustRootLogger().error(f"Temp directory not valid: {tempDir}")
            return

        urls: list[QtCore.QUrl] = []
        for index in (index for index in self.selectedIndexes() if not index.column()):
            resource: ERFResource = self.model().itemData(self._proxy_model.mapToSource(index))[QtCore.Qt.ItemDataRole.UserRole + 1]
            file_stem, file_ext = str(resource.resref), resource.restype.extension
            filepath = Path(tempDir, f"{file_stem}.{file_ext}")
            with filepath.open("wb") as file:
                file.write(resource.data)
            urls.append(QtCore.QUrl.fromLocalFile(str(filepath)))

        mimeData = QMimeData()
        mimeData.setUrls(urls)
        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)
        drag.exec_(QtCore.Qt.DropAction.CopyAction, QtCore.Qt.DropAction.CopyAction)
