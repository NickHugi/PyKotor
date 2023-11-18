from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QMimeData
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QShortcut, QTableView, QWidget

from pykotor.common.misc import ResRef
from pykotor.utility.path import Path
from pykotor.resource.formats.erf import ERF, ERFResource, ERFType, read_erf, write_erf
from pykotor.resource.formats.rim import RIM, read_rim, write_rim
from pykotor.resource.type import ResourceType
from toolset.gui.editor import Editor
from toolset.gui.widgets.settings.installations import GlobalSettings
from toolset.utils.window import openResourceEditor

if TYPE_CHECKING:
    import os

    from toolset.data.installation import HTInstallation


class ERFEditor(Editor):
    def __init__(self, parent: Optional[QWidget], installation: HTInstallation | None = None):
        """Initialize ERF Editor window
        Args:
            parent: QWidget: Parent widget
            installation: HTInstallation: HT Installation object
        Returns:
            None
        Processing Logic:
            - Set supported resource types
            - Initialize base editor window
            - Set up UI from designer file
            - Connect menu and signal handlers
            - Initialize model and connect to table view
            - Disable saving/loading to modules
            - Create new empty ERF.
        """
        supported = [ResourceType.ERF, ResourceType.MOD, ResourceType.RIM]
        super().__init__(parent, "ERF Editor", "none", supported, supported, installation)
        self.resize(400, 250)

        from toolset.uic.editors.erf import Ui_MainWindow

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()

        self.model = QStandardItemModel(self)
        self.ui.tableView.setModel(self.model)
        self.ui.tableView.selectionModel().selectionChanged.connect(self.selectionChanged)

        # Disable saving file into module
        self._saveFilter = self._saveFilter.replace(";;Save into module (*.erf *.mod *.rim)", "")
        self._openFilter = self._openFilter.replace(";;Load from module (*.erf *.mod *.rim)", "")

        self.new()

    def _setupSignals(self) -> None:
        """Setup signal connections for UI elements.

        Args:
        ----
            self: {The class instance}: The class instance
        Returns:
            None: No return value
        Processing Logic:
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

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes) -> None:
        """Load resource file
        Args:
            filepath: Path to resource file
            resref: Resource reference
            restype: Resource type
            data: File data
        Returns:
            None
        Load resource file:
        - Clear existing model data
        - Set model column count to 3 and header labels
        - Enable refresh button
        - If ERF or MOD:
            - Parse file with erf reader
            - Add each resource as row to model
        - If RIM:
            - Parse file with rim reader
            - Add each resource as row to model
        - Else show error message file type not supported.
        """
        super().load(filepath, resref, restype, data)

        self.model.clear()
        self.model.setColumnCount(3)
        self.model.setHorizontalHeaderLabels(["ResRef", "Type", "Size"])
        self.ui.refreshButton.setEnabled(True)

        if restype in [ResourceType.ERF, ResourceType.MOD]:
            erf = read_erf(data)
            for resource in erf:
                resrefItem = QStandardItem(resource.resref.get())
                resrefItem.setData(resource)
                restypeItem = QStandardItem(resource.restype.extension.upper())
                sizeItem = QStandardItem(str(len(resource.data)))
                self.model.appendRow([resrefItem, restypeItem, sizeItem])
        elif restype in [ResourceType.RIM]:
            rim = read_rim(data)
            for resource in rim:
                resrefItem = QStandardItem(resource.resref.get())
                resrefItem.setData(resource)
                restypeItem = QStandardItem(resource.restype.extension.upper())
                sizeItem = QStandardItem(str(len(resource.data)))
                self.model.appendRow([resrefItem, restypeItem, sizeItem])
        else:
            QMessageBox(
                QMessageBox.Critical,
                "Unable to load file",
                "The file specified is not a MOD/ERF type file.",
                ...,
                self,
            ).show()

    def build(self) -> tuple[bytes, bytes]:
        """Builds resource data from the model.

        Args:
        ----
            self: The class instance.

        Returns:
        -------
            data: The built resource data.
            b"": An empty bytes object.
        - Loops through each item in the model and extracts the resource data
        - Writes the data to either a RIM or ERF based on the resource type
        - Returns the built data and an empty bytes object.
        """
        data = bytearray()

        if self._restype == ResourceType.RIM:
            rim = RIM()
            for i in range(self.model.rowCount()):
                item = self.model.item(i, 0)
                resource = item.data()
                rim.set_data(resource.resref.get(), resource.restype, resource.data)
            write_rim(rim, data)
        if self._restype in [ResourceType.ERF, ResourceType.MOD]:  # sourcery skip: split-or-ifs
            erfType = ERFType.ERF if self._restype == ResourceType.ERF else ERFType.MOD
            erf = ERF(erfType)
            for i in range(self.model.rowCount()):
                item = self.model.item(i, 0)
                resource = item.data()
                erf.set_data(resource.resref.get(), resource.restype, resource.data)
            write_erf(erf, data)

        return data, b""

    def new(self) -> None:
        super().new()
        self.model.clear()
        self.model.setColumnCount(3)
        self.model.setHorizontalHeaderLabels(["ResRef", "Type", "Size"])
        self.ui.refreshButton.setEnabled(False)

    def save(self) -> None:
        """Saves the current state of the editor to the file path.

        Args:
        ----
            self: The editor object
        Returns:
            None: Does not return anything
        - Checks if file path is None and calls saveAs() method to set the file path
        - Enables the refresh button on the UI
        - Builds the data from the editor contents
        - Opens the file path in write byte mode
        - Writes the data to the file.
        """
        # Must override the method as the superclass method breaks due to filepath always ending in .rim/mod/erf
        if self._filepath is None:
            self.saveAs()
            return

        self.ui.refreshButton.setEnabled(True)

        data = self.build()
        self._revert = data

        with self._filepath.open("wb") as file:
            file.write(data[0])

    def extractSelected(self) -> None:
        """Extract selected resources to a folder
        Args:
            self: The class instance
        Returns:
            None: No value is returned
        - Get the target folder path from the file dialog
        - Check if a valid folder is selected
        - Get the selected rows from the table view
        - Iterate through the selected rows
        - Extract the resource data from the model
        - Write the resource data to a file in the target folder.
        """
        folderpath_str = QFileDialog.getExistingDirectory(self, "Extract to folder")

        if folderpath_str != "":
            self.ui.tableView.selectionModel().selectedRows()
            for index in self.ui.tableView.selectionModel().selectedRows(0):
                item = self.model.itemFromIndex(index)
                resource = item.data()
                file_path = Path(folderpath_str, f"{resource.resref}.{resource.restype.extension}").resolve()
                with file_path.open("wb") as file:
                    file.write(resource.data)

    def removeSelected(self) -> None:
        """Removes selected rows from table view.

        Args:
        ----
            self: The class instance.

        Returns:
        -------
            None: Does not return anything.
        Removes selected rows from table view by:
        - Getting selected row indexes from table view
        - Reversing the list to remove from last to first
        - Removing the row from model using row number.
        """
        for index in reversed([index for index in self.ui.tableView.selectedIndexes() if index.column() == 0]):
            item = self.model.itemFromIndex(index)
            self.model.removeRow(item.row())

    def addResources(self, filepaths: list[str]) -> None:
        """Adds resource files to the project.

        Args:
        ----
            filepaths: list of filepaths to add as resources
        Returns:
            None
        - Loops through each filepath
        - Resolves the filepath and opens it for reading
        - Splits the parent directory name to get the resref and restype
        - Creates an ERFResource object from the data
        - Adds rows to the model displaying the resref, restype and size
        - Catches any exceptions and displays an error message.
        """
        for filepath in filepaths:
            c_filepath = Path(filepath).resolve()
            try:
                with c_filepath.open("rb") as file:
                    resref, restype_ext = c_filepath.parent.name.split(".", 1)
                    restype = ResourceType.from_extension(restype_ext)
                    data = file.read()

                    resource = ERFResource(ResRef(resref), restype, data)

                    resrefItem = QStandardItem(resource.resref.get())
                    resrefItem.setData(resource)
                    restypeItem = QStandardItem(resource.restype.extension.upper())
                    sizeItem = QStandardItem(str(len(resource.data)))
                    self.model.appendRow([resrefItem, restypeItem, sizeItem])
            except Exception:
                QMessageBox(
                    QMessageBox.Critical,
                    "Failed to add resource",
                    f"Could not add resource at {c_filepath}.",
                ).exec_()

    def selectFilesToAdd(self) -> None:
        filepaths = QFileDialog.getOpenFileNames(self, "Load files into module")[:-1][0]
        self.addResources(filepaths)

    def openSelected(self) -> None:
        """Opens the selected resource in the editor.

        Args:
        ----
            self: The current class instance.

        Returns:
        -------
            None
        - Checks if a filepath is set and shows error if not
        - Loops through selected rows in table
        - Gets the item and resource data
        - Checks resource type and skips nested types
        - Opens the resource in an editor window.
        """
        if self._filepath is None:
            QMessageBox(QMessageBox.Critical, "Cannot edit resource", "Save the ERF and try again.", QMessageBox.Ok, self).exec_()
            return

        for index in self.ui.tableView.selectionModel().selectedRows(0):
            item = self.model.itemFromIndex(index)
            resource = item.data()

            if resource.restype in [ResourceType.ERF, ResourceType.MOD, ResourceType.RIM]:
                QMessageBox(
                    QMessageBox.Warning,
                    "Cannot open nested ERF files",
                    "Editing ERF or RIM files nested within each other is not supported.",
                    QMessageBox.Ok,
                    self,
                ).exec_()
                continue

            tempPath, editor = openResourceEditor(
                self._filepath,
                resource.resref.get(),
                resource.restype,
                resource.data,
                self._installation,
                self,
            )
            editor.savedFile.connect(self.resourceSaved)

    def refresh(self) -> None:
        with self._filepath.open("rb") as file:
            data = file.read()
            self.load(self._filepath, self._resref, self._restype, data)

    def selectionChanged(self) -> None:
        """Updates UI controls based on table selection
        Args:
            self: The class instance
        Returns:
            None: No return value
        - Check if any rows are selected in the table view
        - If no rows selected, disable UI controls by calling _set_ui_controls_state(False)
        - If rows are selected, enable UI controls by calling _set_ui_controls_state(True).
        """
        if len(self.ui.tableView.selectedIndexes()) == 0:
            self._set_ui_controls_state(False)
        else:
            self._set_ui_controls_state(True)

    def _set_ui_controls_state(self, state: bool):
        self.ui.extractButton.setEnabled(state)
        self.ui.openButton.setEnabled(state)
        self.ui.unloadButton.setEnabled(state)

    def resourceSaved(self, filepath: str, resref: str, restype: ResourceType, data: bytes) -> None:
        """Saves resource data to the UI table
        Args:
            filepath: Filepath of the resource being saved
            resref: Reference of the resource being saved
            restype: Type of the resource being saved
            data: Data being saved for the resource
        Returns:
            None
        - Check if filepath matches internal filepath
        - Iterate through selected rows in table view
        - Get item from selected index
        - Check if item resref and restype match parameters
        - Set item data to passed in data.
        """
        if filepath != self._filepath:
            return

        for index in self.ui.tableView.selectionModel().selectedRows(0):
            item = self.model.itemFromIndex(index)
            if item.data().resref == resref and item.data().restype == restype:
                item.data().data = data


class ERFEditorTable(QTableView):
    resourceDropped = QtCore.pyqtSignal(object)

    def __init__(self, parent: QWidget):
        super().__init__(parent)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
            links = [str(url.toLocalFile()) for url in event.mimeData().urls()]
            self.resourceDropped.emit(links)
        else:
            event.ignore()

    def startDrag(self, actions: Union[QtCore.Qt.DropActions, QtCore.Qt.DropAction]) -> None:
        """Starts a drag operation with the selected items
        Args:
            actions: Union[QtCore.Qt.DropActions, QtCore.Qt.DropAction]: The allowed actions for the drag
        Returns:
            None: No return value
        - Extracts selected items to a temp directory
        - Creates a list of local file URLs from the extracted files
        - Sets the file URLs on a QMimeData object
        - Creates a drag object with the mime data
        - Executes the drag with the allowed actions.
        """
        tempDir = Path(GlobalSettings().extractPath).resolve()

        if not tempDir or not tempDir.is_dir():
            return

        urls = []
        for index in [index for index in self.selectedIndexes() if index.column() == 0]:
            resource = self.model().itemData(index)[QtCore.Qt.UserRole + 1]
            file_stem, file_ext = resource.resref.get(), resource.restype.extension
            filepath = Path(tempDir, f"{file_stem}.{file_ext}").resolve()
            with filepath.open("wb") as file:
                file.write(resource.data)
            urls.append(QtCore.QUrl.fromLocalFile(str(filepath)))

        mimeData = QMimeData()
        mimeData.setUrls(urls)
        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)
        drag.exec_(QtCore.Qt.CopyAction, QtCore.Qt.CopyAction)
