from __future__ import annotations

import shutil

from typing import TYPE_CHECKING

import qtpy

from qtpy import QtCore, QtGui
from qtpy.QtCore import QMimeData, Qt
from qtpy.QtGui import QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QFileDialog, QMessageBox, QShortcut, QTableView

from pykotor.common.misc import ResRef
from pykotor.common.stream import BinaryReader
from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.formats.erf import ERF, ERFResource, ERFType, read_erf, write_erf
from pykotor.resource.formats.rim import RIM, read_rim, write_rim
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_capsule_file
from toolset.gui.editor import Editor
from toolset.gui.widgets.settings.installations import GlobalSettings
from toolset.utils.window import openResourceEditor
from utility.error_handling import format_exception_with_variables, universal_simplify_exception
from utility.logger_util import RobustRootLogger
from utility.system.path import Path

if TYPE_CHECKING:
    import os

    from qtpy.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
    from qtpy.QtWidgets import QWidget

    from pykotor.resource.formats.rim import RIMResource
    from toolset.data.installation import HTInstallation
    from utility.system.path import PurePath


def human_readable_size(byte_size: float) -> str:
    for unit in ["bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]:
        if byte_size < 1024:  # noqa: PLR2004
            return f"{round(byte_size, 2)} {unit}"
        byte_size /= 1024
    return str(byte_size)

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
        self.ui.tableView.setModel(self.model)
        self.ui.tableView.selectionModel().selectionChanged.connect(self.selectionChanged)

        # Disable saving file into module
        self._saveFilter = self._saveFilter.replace(f";;Save into module ({self.CAPSULE_FILTER})", "")
        self._openFilter = self._openFilter.replace(f";;Load from module ({self.CAPSULE_FILTER})", "")

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
            for i in range(self.model.rowCount()):
                item = self.model.item(i, 0)
                resource = item.data()
                rim.set_data(str(resource.resref), resource.restype, resource.data)
            write_rim(rim, data)

        elif self._restype in (ResourceType.ERF, ResourceType.MOD, ResourceType.SAV):  # sourcery skip: split-or-ifs
            erf = ERF(ERFType.from_extension(self._restype.extension))
            if self._restype is ResourceType.SAV:
                erf.is_save_erf = True
            for i in range(self.model.rowCount()):
                item = self.model.item(i, 0)
                resource = item.data()
                erf.set_data(str(resource.resref), resource.restype, resource.data)
            write_erf(erf, data)
        else:
            raise ValueError(f"Invalid restype for ERFEditor: {self._restype!r}")

        return data, b""

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

    def extractSelected(self):  # TODO(th3w1zard1): move this logic into a util function as it's more-or-less used fairly often in this toolset.
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
        selected_rows = self.ui.tableView.selectionModel().selectedRows()
        assert self._filepath is not None
        erf_path = self._filepath.parent / f"{self._resname}.{self._restype}"
        erf_relpath = erf_path.relative_to(erf_path.parent)
        if len(selected_rows) == 1:
            # Handle single file with file dialog
            resource: ERFResource = self.model.itemFromIndex(selected_rows[0]).data()
            dialog = QFileDialog(self, "Save File", f"{resource.resref}.{resource.restype.extension}", f"Files (*.{resource.restype.extension})")
            dialog.setAcceptMode(QFileDialog.AcceptSave)
            dialog.setOption(QFileDialog.DontConfirmOverwrite)  # Disable default overwrite confirmation
            response = dialog.exec_()
            if response == QFileDialog.Accepted:
                filepath_str = dialog.selectedFiles()[0]
                if not filepath_str or not filepath_str.strip():
                    RobustRootLogger().debug("QFileDialog was accepted but no filepath str passed.")
                    return
                self._handle_single_file_save(Path(filepath_str), resource.data, erf_relpath, catch_exceptions=True)
            else:
                print(f"User cancelled selecting a save filepath, response {response}")
            return

        # Handle multiple files with folder dialog
        folderpath_str = QFileDialog.getExistingDirectory(self, "Extract to folder")
        if not folderpath_str:
            RobustRootLogger().debug("User cancelled folderpath extraction.")
            return
        RobustRootLogger().debug("Determining existing files and whether to overwrite.")
        existing_files_and_folders: list[str] = []
        paths_to_write: dict[Path, bytes] = {}
        for index in selected_rows:
            item = self.model.itemFromIndex(index)
            resource: ERFResource = item.data()
            file_path = Path(folderpath_str, f"{resource.resref}.{resource.restype.extension}")
            if file_path.safe_exists():
                file_relpath = str(file_path.relative_to(file_path.parents[1] if file_path.parent.parent.name else file_path.parent))
                existing_files_and_folders.append(file_relpath)
            paths_to_write[file_path] = resource.data

        self._handle_multiple_existing(erf_relpath, existing_files_and_folders, paths_to_write)

    def _handle_multiple_existing(  # TODO(th3w1zard1): allow subfunction to show its error messageboxes, if a user sets their toolset settings to do so.
        self,
        erf_relpath: PurePath,
        existing_files_and_folders: list[str],
        paths_to_write: dict[Path, bytes],
    ):
        if not existing_files_and_folders:
            choice = QMessageBox.StandardButton.No  # Default to rename.
        else:
            msgBox = QMessageBox()  # sourcery skip: extract-method
            msgBox.setIcon(QMessageBox.Icon.Warning)
            msgBox.setWindowTitle("Existing files/folders found.")
            msgBox.setText(f"The following {len(existing_files_and_folders)} files and folders already exist in the selected folder.<br><br>How would you like to handle this?")
            msgBox.setDetailedText("\n".join(existing_files_and_folders))
            msgBox.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Abort)
            msgBox.button(QMessageBox.StandardButton.Yes).setText("Overwrite")   # type: ignore[union-attr]
            msgBox.button(QMessageBox.StandardButton.No).setText("Auto-Rename")  # type: ignore[union-attr]
            msgBox.setDefaultButton(QMessageBox.StandardButton.Abort)
            msgBox.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowSystemMenuHint)
            choice = msgBox.exec_()

        failed_extractions: dict[Path, Exception] = {}
        if choice == QMessageBox.StandardButton.Yes:
            RobustRootLogger().debug(
                "User chose to Overwrite %s files/folders in the '%s' folder.",
                len(existing_files_and_folders),
                next(iter(paths_to_write.keys())).parent,
            )
            for path, data in paths_to_write.items():
                is_overwrite = "overwriting existing file" if path.safe_isfile() else "saving as"
                RobustRootLogger().info("Extracting '%s' to '%s' and %s '%s'", erf_relpath/path.name, path.parent, is_overwrite, path.name)
                try:
                    if path.safe_isdir():
                        shutil.rmtree(path)
                    elif path.safe_isfile():
                        path.unlink(missing_ok=True)
                except Exception as e:  # noqa: BLE001
                    RobustRootLogger().exception("ERFEditor: Failed to delete file '%s' while attempting to overwrite", path)
                    failed_extractions[path] = e
                self._handle_single_file_save(path, data, erf_relpath, choice)
        elif choice == QMessageBox.StandardButton.No:
            RobustRootLogger().debug(
                "User chose to Rename %s files in the '%s' folder.",
                len(existing_files_and_folders),
                next(iter(paths_to_write.keys())).parent,
            )
            for path, data in paths_to_write.items():
                new_path = path
                try:
                    i = 1
                    while new_path.safe_exists():
                        i += 1
                        new_path = new_path.with_stem(f"{path.stem} ({i})")
                    is_rename = "with new filename" if path.safe_isfile() else "saving as"
                    RobustRootLogger().info("Extracting '%s' to '%s' and %s '%s'", erf_relpath/path.name, path.parent, is_rename, new_path.name)
                    self._handle_single_file_save(new_path, data, erf_relpath, choice)
                except Exception as e:  # noqa: BLE001
                    RobustRootLogger().exception("ERFEditor: Failed to extract file '%s'", new_path)
                    failed_extractions[path] = e
        else:
            RobustRootLogger().debug(
                "User chose to CANCEL overwrite/renaming of %s files in the '%s' folder.",
                len(existing_files_and_folders),
                next(iter(paths_to_write.keys())).parent,
            )
        if failed_extractions:
            self._handle_failed_extractions(failed_extractions)

    def _handle_failed_extractions(self, failed_extractions: dict[Path, Exception]):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Icon.Critical)
        msgBox.setWindowTitle("Failed to extract files to disk.")
        msgBox.setText(f"{len(failed_extractions)} files FAILED to to be saved<br><br>Press 'show details' for information.")
        detailed_info = "\n".join(
            f"{file}: {universal_simplify_exception(exc)}"
            for file, exc in failed_extractions.items()
        )
        msgBox.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowSystemMenuHint)
        msgBox.setDetailedText(detailed_info)
        msgBox.exec_()

    def _handle_single_file_save(
        self,
        path: Path,
        data: bytes,
        erf_relpath: PurePath,
        arg_choice: int | QMessageBox.StandardButton | None = None,
        *,
        catch_exceptions: bool = False,
    ):
        new_path = path
        check = new_path.safe_exists()
        first_run = True
        while first_run or check:
            first_run = False
            try:
                if arg_choice is None and check:
                    msgBox = QMessageBox()
                    msgBox.setIcon(QMessageBox.Warning)
                    msgBox.setWindowTitle(f"Overwrite {'File' if new_path.safe_isfile() else 'Folder'}?")
                    msgBox.setText(f"The following {'file' if new_path.safe_isfile() else 'folder'} exists with the same name as one of the resources you are trying to extract. How would you like to handle this problem?")
                    msgBox.setDetailedText(str(path))
                    msgBox.setStandardButtons(
                        QMessageBox.StandardButton.Yes
                        | QMessageBox.StandardButton.No
                        | QMessageBox.StandardButton.Retry
                        | QMessageBox.StandardButton.Abort
                    )
                    msgBox.button(QMessageBox.StandardButton.Yes).setText("Delete Folder" if new_path.safe_isdir() else "Overwrite")   # type: ignore[union-attr]
                    msgBox.button(QMessageBox.StandardButton.No).setText("Auto-Rename File(s)")  # type: ignore[union-attr]
                    msgBox.button(QMessageBox.StandardButton.Retry).setText("Retry")
                    msgBox.button(QMessageBox.StandardButton.Abort).setText("Cancel")    # type: ignore[union-attr]
                    msgBox.setDefaultButton(QMessageBox.StandardButton.Abort)
                    msgBox.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowSystemMenuHint)
                    choice = msgBox.exec_()
                else:
                    choice = arg_choice
                if choice == QMessageBox.StandardButton.Abort:
                    return
                if choice == QMessageBox.StandardButton.Retry:
                    check = new_path.safe_exists()
                    continue
                if choice == QMessageBox.StandardButton.Yes:
                    try:
                        if path.safe_isdir():
                            shutil.rmtree(path)
                        elif path.safe_exists():  # do not use is_file here.
                            path.unlink(missing_ok=True)
                    except Exception as e:  # noqa: BLE001
                        check = path.safe_exists()
                        if check:
                            if not catch_exceptions:
                                raise
                            simple_exc_str = str(universal_simplify_exception(e))
                            msgBox = QMessageBox(
                                QMessageBox.Icon.Critical,
                                "Failed to delete the folder.",
                                f"An error occurred attempting to delete the folder '{path}'.<br><br>{simple_exc_str}",
                            )
                            msgBox.setDetailedText(format_exception_with_variables(e))
                            msgBox.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowSystemMenuHint)
                            msgBox.exec_()
                            continue
                        RobustRootLogger().warning("Attempted to delete file/folder at '%s' but the path doesn't even exist?", new_path)
                    check = path.safe_exists()
                    if check:
                        print("Path still exists, restart dialog.")
                        continue
                    print(f"Overwriting file at '{path}'")
                elif choice == QMessageBox.StandardButton.No:
                    i = 1
                    stem = new_path.stem
                    while new_path.safe_exists():
                        i += 1
                        new_path = new_path.with_stem(f"{stem} ({i})")
                    if path.name != new_path.name:
                        print(f"Changed save filename '{path.name}' to '{new_path.name}'")
                    check = False
                print(f"Saving to '{new_path}'")
                with new_path.open("wb") as file:
                    file.write(data)
            except Exception as e:  # noqa: PERF203, BLE001
                simple_exc_str = str(universal_simplify_exception(e))
                msg = f"ERFEditor: Failed to extract {erf_relpath}"
                if not catch_exceptions:
                    raise
                RobustRootLogger().exception("%s: %s", msg, simple_exc_str)
                msgBox = QMessageBox(
                    QMessageBox.Icon.Critical,
                    "Failed to extract the file(s).",
                    f"An error occurred attempting to extract '{erf_relpath}' to '{new_path}'.<br><br>{simple_exc_str}",
                )
                msgBox.setDetailedText(format_exception_with_variables(e))
                msgBox.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowSystemMenuHint)
                msgBox.exec_()

    def removeSelected(self):
        """Removes selected rows from table view.

        Removes selected rows from table view by:
            - Getting selected row indexes from table view
            - Reversing the list to remove from last to first
            - Removing the row from model using row number.
        """
        self._has_changes = True
        for index in reversed([index for index in self.ui.tableView.selectedIndexes() if not index.column()]):
            item: QStandardItem | None = self.model.itemFromIndex(index)
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
            QMessageBox(
                QMessageBox.Icon.Critical,
                "Cannot edit resource. Filepath invalid.",
                "Save the ERF and try again.",
                QMessageBox.StandardButton.Ok,
                self,
                flags=Qt.WindowType.Dialog | Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowSystemMenuHint
            ).exec_()
            return

        for index in self.ui.tableView.selectionModel().selectedRows(0):
            item = self.model.itemFromIndex(index)
            resource: ERFResource = item.data()

            #  if resource.restype.name in ERFType.__members__:  check if in nested erf/rim if needed
            new_filepath = self._filepath
            if resource.restype in (ResourceType.ERF, ResourceType.SAV, ResourceType.RIM, ResourceType.MOD):
                RobustRootLogger().info(f"Nested capsule selected for opening, appending resref/restype '{resource.resref}.{resource.restype}' to the filepath.")
                new_filepath /= str(ResourceIdentifier(str(resource.resref), resource.restype))

            tempPath, editor = openResourceEditor(
                new_filepath,
                str(resource.resref),
                resource.restype,
                resource.data,
                self._installation,
                self,
            )
            if isinstance(editor, Editor):
                editor.savedFile.connect(self.resourceSaved)

    def refresh(self):
        if self._has_changes and not self.promptConfirm():
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
            item: ERFResource = self.model.itemFromIndex(index).data()
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
            resource: ERFResource = self.model().itemData(index)[QtCore.Qt.ItemDataRole.UserRole + 1]
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
