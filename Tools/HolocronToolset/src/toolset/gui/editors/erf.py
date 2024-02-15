from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QMimeData
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QShortcut, QTableView

from pykotor.common.misc import ResRef
from pykotor.common.stream import BinaryReader
from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.formats.erf import ERF, ERFResource, ERFType, read_erf, write_erf
from pykotor.resource.formats.rim import RIM, read_rim, write_rim
from pykotor.resource.type import ResourceType
from toolset.gui.editor import Editor
from toolset.gui.widgets.settings.installations import GlobalSettings
from toolset.utils.window import openResourceEditor
from utility.error_handling import format_exception_with_variables, universal_simplify_exception
from utility.system.path import Path

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget
    from PyQt5.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
    import os

    from pykotor.resource.formats.rim import RIMResource
    from toolset.data.installation import HTInstallation


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
        supported: list[ResourceType] = [ResourceType.__members__[name] for name in ERFType.__members__]
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
        capsule_types = " ".join(f"*.{e.name.lower()}" for e in ERFType) + " *.rim"
        self._saveFilter = self._saveFilter.replace(f";;Save into module ({capsule_types})", "")
        self._openFilter = self._openFilter.replace(f";;Load from module ({capsule_types})", "")

        self.new()

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

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes):
        """Load resource file.

        Args:
        ----
            filepath: Path to resource file
            resref: Resource reference
            restype: Resource type
            data: File data

        Load resource file:
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
        super().load(filepath, resref, restype, data)

        self.model.clear()
        self.model.setColumnCount(3)
        self.model.setHorizontalHeaderLabels(["ResRef", "Type", "Size"])
        self.ui.refreshButton.setEnabled(True)
        def human_readable_size(byte_size: float) -> str:
            for unit in ["bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]:
                if byte_size < 1024:  # noqa: PLR2004
                    return f"{round(byte_size, 2)} {unit}"
                byte_size /= 1024
            return str(byte_size)

        if restype.name in ERFType.__members__:
            erf: ERF = read_erf(data)
            for resource in erf:
                resrefItem = QStandardItem(str(resource.resref))
                resrefItem.setData(resource)
                restypeItem = QStandardItem(resource.restype.extension.upper())
                sizeItem = QStandardItem(human_readable_size(len(resource.data)))
                self.model.appendRow([resrefItem, restypeItem, sizeItem])

        elif restype == ResourceType.RIM:
            rim: RIM = read_rim(data)
            for resource in rim:
                resrefItem = QStandardItem(str(resource.resref))
                resrefItem.setData(resource)
                restypeItem = QStandardItem(resource.restype.extension.upper())
                sizeItem = QStandardItem(human_readable_size(len(resource.data)))
                self.model.appendRow([resrefItem, restypeItem, sizeItem])

        else:
            QMessageBox(
                QMessageBox.Critical,
                "Unable to load file",
                "The file specified is not a MOD/ERF type file.",
                parent=self,
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

        if self._restype == ResourceType.RIM:
            rim = RIM()
            for i in range(self.model.rowCount()):
                item = self.model.item(i, 0)
                resource = item.data()
                rim.set_data(str(resource.resref), resource.restype, resource.data)
            write_rim(rim, data)

        elif self._restype.name in ERFType.__members__:  # sourcery skip: split-or-ifs
            erf = ERF(ERFType.__members__[self._restype.name])
            for i in range(self.model.rowCount()):
                item = self.model.item(i, 0)
                resource = item.data()
                erf.set_data(str(resource.resref), resource.restype, resource.data)
            write_erf(erf, data)

        return data, b""

    def new(self):
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
        # Must override the method as the superclass method breaks due to filepath always ending in .rim/mod/erf
        if self._filepath is None:
            self.saveAs()
            return

        self.ui.refreshButton.setEnabled(True)

        data: tuple[bytes, bytes] = self.build()
        self._revert = data[0]

        with self._filepath.open("wb") as file:
            file.write(data[0])

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
        folderpath_str = QFileDialog.getExistingDirectory(self, "Extract to folder")
        if not folderpath_str:
            return

        self.ui.tableView.selectionModel().selectedRows()
        for index in self.ui.tableView.selectionModel().selectedRows(0):
            item = self.model.itemFromIndex(index)
            resource: ERFResource = item.data()
            file_path = Path(folderpath_str, f"{resource.resref}.{resource.restype.extension}")
            with file_path.open("wb") as file:
                file.write(resource.data)

    def removeSelected(self):
        """Removes selected rows from table view.

        Removes selected rows from table view by:
            - Getting selected row indexes from table view
            - Reversing the list to remove from last to first
            - Removing the row from model using row number.
        """
        for index in reversed([index for index in self.ui.tableView.selectedIndexes() if not index.column()]):
            item: QStandardItem | None = self.model.itemFromIndex(index)
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
        for filepath in filepaths:
            c_filepath = Path(filepath)
            try:
                resref, restype = ResourceIdentifier.from_path(c_filepath).validate()
                data = BinaryReader.load_file(c_filepath)
                resource = ERFResource(ResRef(resref), restype, data)

                resrefItem = QStandardItem(str(resource.resref))
                resrefItem.setData(resource)
                restypeItem = QStandardItem(resource.restype.extension.upper())
                sizeItem = QStandardItem(str(len(resource.data)))
                self.model.appendRow([resrefItem, restypeItem, sizeItem])
            except Exception as e:
                with Path("errorlog.txt").open("a", encoding="utf-8") as file:
                    lines = format_exception_with_variables(e)
                    file.writelines(lines)
                    file.write("\n----------------------\n")
                QMessageBox(
                    QMessageBox.Critical,
                    "Failed to add resource",
                    f"Could not add resource at {c_filepath.absolute()}:\n{universal_simplify_exception(e)}",
                ).exec_()

    def selectFilesToAdd(self):
        filepaths: list[str] = QFileDialog.getOpenFileNames(self, "Load files into module")[:-1][0]
        self.addResources(filepaths)

    def openSelected(self):
        """Opens the selected resource in the editor.

        Processing Logic:
        ----------------
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
            resource: ERFResource = item.data()

            # if resource.restype.name in ERFType.__members__:
            #    QMessageBox(
            #        QMessageBox.Warning,
            #        "Cannot open nested ERF files",
            #        "Editing ERF or RIM files nested within each other is not supported.",
            #        QMessageBox.Ok,
            #        self,
            #    ).exec_()
            #    continue

            tempPath, editor = openResourceEditor(
                self._filepath,
                str(resource.resref),
                resource.restype,
                resource.data,
                self._installation,
                self,
            )
            editor.savedFile.connect(self.resourceSaved)

    def refresh(self):
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
            self._set_ui_controls_state(False)
        else:
            self._set_ui_controls_state(True)

    def _set_ui_controls_state(self, state: bool):
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
            item: ERFResource = self.model.itemFromIndex(index).data()
            if item.resref == resname and item.restype == restype:
                item.data = data


class ERFEditorTable(QTableView):
    resourceDropped = QtCore.pyqtSignal(object)

    def __init__(self, parent: QWidget):
        super().__init__(parent)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
            links: list[str] = [str(url.toLocalFile()) for url in event.mimeData().urls()]
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

        if not tempDir or not tempDir.safe_isdir():
            print(f"Temp directory not valid: {tempDir}")
            return

        urls: list[QtCore.QUrl] = []
        for index in (index for index in self.selectedIndexes() if not index.column()):
            resource: ERFResource = self.model().itemData(index)[QtCore.Qt.UserRole + 1]
            file_stem, file_ext = str(resource.resref), resource.restype.extension
            filepath = Path(tempDir, f"{file_stem}.{file_ext}")
            with filepath.open("wb") as file:
                file.write(resource.data)
            urls.append(QtCore.QUrl.fromLocalFile(str(filepath)))

        mimeData = QMimeData()
        mimeData.setUrls(urls)
        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)
        drag.exec_(QtCore.Qt.CopyAction, QtCore.Qt.CopyAction)
