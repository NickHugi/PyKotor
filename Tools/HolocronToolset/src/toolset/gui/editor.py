from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Callable

from qtpy import QtCore
from qtpy.QtCore import Qt
from qtpy.QtGui import QIcon, QPixmap
from qtpy.QtWidgets import QFileDialog, QLineEdit, QMainWindow, QMenu, QMessageBox, QPlainTextEdit, QShortcut

from pykotor.common.module import Module
from pykotor.common.stream import BinaryReader
from pykotor.extract.capsule import Capsule
from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.formats.erf import ERFType, read_erf, write_erf
from pykotor.resource.formats.erf.erf_data import ERF
from pykotor.resource.formats.gff.gff_auto import read_gff
from pykotor.resource.formats.rim import read_rim, write_rim
from pykotor.resource.type import ResourceType
from pykotor.tools import module
from pykotor.tools.misc import is_any_erf_type_file, is_bif_file, is_capsule_file, is_rim_file
from pykotor.tools.path import CaseAwarePath
from toolset.gui.dialogs.load_from_module import LoadFromModuleDialog
from toolset.gui.dialogs.save.to_bif import BifSaveDialog, BifSaveOption
from toolset.gui.dialogs.save.to_module import SaveToModuleDialog
from toolset.gui.dialogs.save.to_rim import RimSaveDialog, RimSaveOption
from toolset.gui.widgets.settings.installations import GlobalSettings
from utility.error_handling import assert_with_variable_trace, format_exception_with_variables, universal_simplify_exception
from utility.logger_util import get_root_logger
from utility.system.path import Path, PurePath

if TYPE_CHECKING:
    import os

    from qtpy.QtWidgets import QWidget

    from pykotor.common.language import LocalizedString
    from pykotor.resource.formats.rim.rim_data import RIM
    from toolset.data.installation import HTInstallation


# TODO: Creating a child editor from this class is not intuitive, document the requirements at some point.
class Editor(QMainWindow):
    """Editor is a base class for all file-specific editors.

    Provides methods for saving and loading files that are stored directly in folders and for files that are encapsulated in a MOD or RIM.
    """

    newFile = QtCore.Signal()
    savedFile = QtCore.Signal(object, object, object, object)
    loadedFile = QtCore.Signal(object, object, object, object)

    def __init__(
        self,
        parent: QWidget | None,
        title: str,
        iconName: str,
        readSupported: list[ResourceType],
        writeSupported: list[ResourceType],
        installation: HTInstallation | None = None,
        mainWindow: QMainWindow | QWidget | None = None,
    ):
        """Initializes the editor.

        Args:
        ----
            parent: QWidget: The parent widget
            title: str: The title of the editor window
            iconName: str: The name of the icon to display
            readSupported: list[ResourceType]: The supported resource types for reading
            writeSupported: list[ResourceType]: The supported resource types for writing
            installation: HTInstallation | None: The installation context
            mainwindow: QMainWindow | None: The main window

        Initializes editor properties:
            - Sets up title, icon and parent widget
            - Sets supported read/write resource types
            - Initializes file filters for opening and saving
            - Sets up other editor properties.
        """
        super().__init__(parent)
        self._is_capsule_editor: bool = False
        self._installation: HTInstallation | None = installation
        self._logger = get_root_logger()

        self._filepath: Path | None = None
        self._resname: str | None = None
        self._restype: ResourceType | None = None
        self._revert: bytes | None = None

        writeSupported = readSupported.copy() if readSupported is writeSupported else writeSupported
        additional_formats = {"XML", "JSON", "CSV", "ASCII", "YAML"}
        for add_format in additional_formats:
            readSupported.extend(
                ResourceType.__members__[f"{restype.name}_{add_format}"]
                for restype in readSupported if f"{restype.name}_{add_format}" in ResourceType.__members__
            )
            writeSupported.extend(
                ResourceType.__members__[f"{restype.name}_{add_format}"]
                for restype in writeSupported if f"{restype.name}_{add_format}" in ResourceType.__members__
            )
        self._readSupported: list[ResourceType] = readSupported
        self._writeSupported: list[ResourceType] = writeSupported
        self._global_settings: GlobalSettings = GlobalSettings()
        self._mainWindow: QMainWindow | None = mainWindow  # FIXME: unused?

        self._editorTitle: str = title
        self.setWindowTitle(title)
        self._setupIcon(iconName)

        capsule_types = " ".join(f"*.{e.name.lower()}" for e in ERFType) + " *.rim"
        self._saveFilter: str = "All valid files ("
        for resource in writeSupported:
            self._saveFilter += f'*.{resource.extension}{"" if writeSupported[-1] == resource else " "}'
        self._saveFilter += f" {capsule_types});;"
        for resource in writeSupported:
            self._saveFilter += f"{resource.category} File (*.{resource.extension});;"
        self._saveFilter += f"Save into module ({capsule_types})"

        self._openFilter: str = "All valid files ("
        for resource in readSupported:
            self._openFilter += f'*.{resource.extension}{"" if readSupported[-1] == resource else " "}'
        self._openFilter += f" {capsule_types});;"
        for resource in readSupported:
            self._openFilter += f"{resource.category} File (*.{resource.extension});;"
        self._openFilter += f"Load from module ({capsule_types})"

    def _setupMenus(self):
        """Sets up menu actions and keyboard shortcuts.

        Processing Logic:
        ----------------
            - Loops through menu actions and connects signals for New, Open, Save, Save As, Revert and Exit
            - Sets Revert action to disabled
            - Connects keyboard shortcuts for New, Open, Save, Save As, Revert and Exit.
        """
        menubar = self.menuBar().actions()[0].menu()
        if not isinstance(menubar, QMenu):
            raise TypeError(f"self.menuBar().actions()[0].menu() returned a {type(menubar).__name__} object, expected QMenu.")
        for action in menubar.actions():
            if action.text() == "New":  # sourcery skip: extract-method
                action.triggered.connect(self.new)
            if action.text() == "Open":
                action.triggered.connect(self.open)
            if action.text() == "Save":
                action.triggered.connect(self.save)
            if action.text() == "Save As":
                action.triggered.connect(self.saveAs)
            if action.text() == "Revert":
                action.triggered.connect(self.revert)
            if action.text() == "Revert":
                action.setEnabled(False)
            if action.text() == "Exit":
                action.triggered.connect(self.close)  # type: ignore[]
        QShortcut("Ctrl+N", self).activated.connect(self.new)
        QShortcut("Ctrl+O", self).activated.connect(self.open)
        QShortcut("Ctrl+S", self).activated.connect(self.save)
        QShortcut("Ctrl+Shift+S", self).activated.connect(self.saveAs)
        QShortcut("Ctrl+R", self).activated.connect(self.revert)
        QShortcut("Ctrl+Q", self).activated.connect(self.exit)

    def _setupIcon(self, iconName: str):
        iconVersion = "x" if self._installation is None else "2" if self._installation.tsl else "1"
        iconPath = f":/images/icons/k{iconVersion}/{iconName}.png"
        self.setWindowIcon(QIcon(QPixmap(iconPath)))

    def refreshWindowTitle(self):
        """Refreshes the window title based on the current state of the editor."""
        installationName = "No Installation" if self._installation is None else self._installation.name
        if self._filepath is None:
            self.setWindowTitle(f"{self._editorTitle}({installationName})")
            return

        relpath = self._filepath.relative_to(self._filepath.parent.parent) if self._filepath.parent.parent.name else self._filepath.parent
        if is_bif_file(relpath) or is_capsule_file(self._filepath):
            from toolset.gui.editors.erf import ERFEditor
            if not isinstance(self, ERFEditor):
                relpath /= f"{self._resname}.{self._restype.extension}"
        else:
            assert relpath.name.lower() == f"{self._resname}.{self._restype}".lower()
        self.setWindowTitle(f"{relpath} - {self._editorTitle}({installationName})")

    def saveAs(self):
        """Saves the file with the selected filepath.

        Processing Logic:
        ----------------
            - Gets the selected filepath and filter from a file dialog
            - Checks if the filepath is a capsule file and filter is for modules
            - If so, shows a dialog to select resource reference and type
            - Sets filepath, reference and type attributes from selection
            - Calls the save method
            - Refreshes the window title
            - Enables the Revert menu item
        """
        filepath_str, _filter = QFileDialog.getSaveFileName(self, "Save As", "", self._saveFilter, "")
        if not filepath_str:
            return
        try:
            identifier = ResourceIdentifier.from_path(filepath_str).validate()
        except ValueError as e:
            get_root_logger().exception("ValueError raised, assuming invalid filename/extension '%s'", filepath_str)
            error_msg = str(universal_simplify_exception(e)).replace("\n", "<br>")
            msgBox = QMessageBox(
                QMessageBox.Icon.Critical,
                "Invalid filename/extension",
                f"Check the filename and try again. Could not save!<br><br>{error_msg}",
                parent=None,
                flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,
            )
            msgBox.setDetailedText(format_exception_with_variables(e))
            msgBox.exec_()
            return

        capsule_types = " ".join(f"*.{e.name.lower()}" for e in ERFType) + " *.rim"
        if is_capsule_file(filepath_str) and f"Save into module ({capsule_types})" in self._saveFilter:
            if self._resname is None:
                self._resname = "new"
                self._restype = self._writeSupported[0]

            dialog2 = SaveToModuleDialog(self._resname, self._restype, self._writeSupported)
            if dialog2.exec_():
                self._resname = dialog2.resname()
                self._restype = dialog2.restype()
                self._filepath = Path(filepath_str)
        else:
            self._filepath = Path(filepath_str)
            self._resname, self._restype = identifier.unpack()
        self.save()

        self.refreshWindowTitle()
        for action in self.menuBar().actions()[0].menu().actions():
            if action.text() == "Revert":
                action.setEnabled(True)

    def save(self):
        """Saves the current data to file.

        Processing Logic:
        ----------------
            - Builds the data and extension to save
            - Checks the file extension and calls the appropriate save method
            - Catches any exceptions and writes to an error log.
        """
        if self._filepath is None:
            self.saveAs()
            return

        try:
            data, data_ext = self.build()
            if data is None:  # nsseditor
                return
            if self._global_settings.attemptKeepOldGFFFields and self._restype.is_gff():
                old_gff = read_gff(self._revert)
                new_gff = read_gff(data)
                new_gff.root.add_missing(old_gff.root)
            self._revert = data

            self.refreshWindowTitle()

            if is_bif_file(self._filepath):
                self._saveEndsWithBif(data, data_ext)
            elif is_capsule_file(self._filepath.parent):
                self._saveNestedCapsule(data, data_ext)
            elif is_rim_file(self._filepath.name):
                self._saveEndsWithRim(data, data_ext)
            elif is_any_erf_type_file(self._filepath):
                self._saveEndsWithErf(data, data_ext)
            else:
                self._saveEndsWithOther(data, data_ext)
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            get_root_logger().critical("Failed to write to file", exc_info=True)
            msgBox = QMessageBox(QMessageBox.Icon.Critical, "Failed to write to file", str(universal_simplify_exception(e)).replace("\n", "<br>"))
            msgBox.setDetailedText(format_exception_with_variables(e))
            msgBox.exec_()

    def _saveEndsWithBif(self, data: bytes, data_ext: bytes):
        """Saves data if dialog returns specific options.

        Args:
        ----
            data: bytes - Data to save
            data_ext: bytes - File extension

        Processing Logic:
        ----------------
            - Show save dialog to choose MOD or override save
            - If MOD chosen, show second dialog to set resref/restype
            - Set filepath based on option
            - Call save method.
        """
        dialog = BifSaveDialog(self)
        dialog.exec_()
        if dialog.option == BifSaveOption.MOD:
            str_filepath, filter = QFileDialog.getSaveFileName(self, "Save As", "", ".MOD File (*.mod)", "")
            if not str_filepath.strip():
                print(f"User cancelled filepath lookup in _saveEndsWithBif ({self._resname}.{self._restype})")
                return

            r_filepath = Path(str_filepath)
            dialog2 = SaveToModuleDialog(self._resname, self._restype, self._writeSupported)
            if dialog2.exec_():
                self._resname = dialog2.resname()
                self._restype = dialog2.restype()
                self._filepath = r_filepath
                self.save()
        elif dialog.option == BifSaveOption.Override:
            self._filepath = self._installation.override_path() / f"{self._resname}.{self._restype.extension}"
            self.save()
        else:
            print(f"User closed out of BifSaveDialog in _saveEndsWithBif (({self._resname}.{self._restype}))")

    def _saveEndsWithRim(self, data: bytes, data_ext: bytes):
        """Saves resource data to a RIM file.

        Args:
        ----
            data: {Bytes containing resource data}
            data_ext: {Bytes containing additional resource data like MDX for MDL}.

        Processing Logic:
        ----------------
        Saves resource data to RIM file:
            - Checks for RIM saving disabled setting and shows dialog
            - Writes data to RIM file
            - Updates installation cache.
        """  # sourcery skip: class-extract-method
        assert self._filepath is not None, assert_with_variable_trace(self._filepath is not None)
        assert self._resname is not None, assert_with_variable_trace(self._resname is not None)
        assert self._restype is not None, assert_with_variable_trace(self._restype is not None)

        if self._global_settings.disableRIMSaving:
            dialog = RimSaveDialog(self)
            dialog.exec_()
            if dialog.option == RimSaveOption.MOD:
                folderpath: Path = self._filepath.parent
                filename: str = f"{Module.find_root(self._filepath)}.mod"
                self._filepath = folderpath / filename
                # Re-save with the updated filepath
                self.save()
            elif dialog.option == RimSaveOption.Override:
                self._filepath = self._installation.override_path() / f"{self._resname}.{self._restype.extension}"
                self.save()
            return

        rim: RIM = read_rim(self._filepath)

        # MDL is a special case - we need to save the MDX file with the MDL file.
        if self._restype is ResourceType.MDL:
            rim.set_data(self._resname, ResourceType.MDX, data_ext)

        rim.set_data(self._resname, self._restype, data)

        write_rim(rim, self._filepath)
        self.savedFile.emit(str(self._filepath), self._resname, self._restype, data)

        # Update installation cache
        if self._installation is not None:
            self._installation.reload_module(self._filepath.name)

    def _saveNestedCapsule(self, data: bytes, data_ext: bytes):
        assert self._filepath is not None, assert_with_variable_trace(self._filepath is not None)
        assert self._resname is not None, assert_with_variable_trace(self._resname is not None)
        assert self._restype is not None, assert_with_variable_trace(self._restype is not None)

        # Determine the physical file and the nested paths.
        c_filepath: CaseAwarePath = CaseAwarePath.pathify(self._filepath)
        nested_paths: list[PurePath] = []
        if is_any_erf_type_file(c_filepath) or is_rim_file(c_filepath):
            nested_paths.append(c_filepath)

        c_parent_filepath = c_filepath.parent
        while (  # Iterate all parents until we find a physical folder on disk.
            ResourceType.from_extension(c_parent_filepath.suffix).name in ERFType.__members__
            or ResourceType.from_extension(c_parent_filepath.suffix) is ResourceType.RIM
        ) and not c_parent_filepath.safe_isdir():
            nested_paths.append(c_parent_filepath)
            c_filepath = c_parent_filepath
            c_parent_filepath = c_filepath.parent

        # At this point, c_filepath points to the physical ERF/RIM on disk
        # and c_parent_filepath points to the physical folder containing the file.
        erf_or_rim = read_rim(c_filepath) if ResourceType.from_extension(c_parent_filepath.suffix) is ResourceType.RIM else read_erf(c_filepath)
        nested_capsules: list[tuple[PurePath, ERF | RIM]] = [(c_filepath, erf_or_rim)]
        for capsule_path in reversed(nested_paths[:-1]):
            nested_erf_or_rim_data = erf_or_rim.get(capsule_path.stem, ResourceType.from_extension(capsule_path.suffix))
            if nested_erf_or_rim_data is None:  # TODO: loop through all windows and send hotkey ctrl+s
                msg = f"You must save the ERFEditor for '{capsule_path.relative_to(c_parent_filepath)}' to before modifying its nested resources. Do so and try again."
                raise ValueError(msg)

            erf_or_rim = read_rim(nested_erf_or_rim_data) if ResourceType.from_extension(capsule_path.suffix) is ResourceType.RIM else read_erf(nested_erf_or_rim_data)
            nested_capsules.append((capsule_path, erf_or_rim))

        # Let's now save each erf/rim to its parent.
        for index, (capsule_path, this_erf_or_rim) in enumerate(reversed(nested_capsules)):
            rel_capsule_path = capsule_path.relative_to(c_parent_filepath)
            if index == 0:
                if self._is_capsule_editor:
                    print(f"Not saving '{self._resname}.{self._restype.extension}' to '{rel_capsule_path}', is ERFEditor save.")
                else:
                    print(f"Saving non ERF/RIM '{self._resname}.{self._restype.extension}' to '{rel_capsule_path}'")
                    this_erf_or_rim.set_data(self._resname, self._restype, data)
                continue
            child_index = len(nested_capsules) - index
            child_capsule_path, child_erf_or_rim = nested_capsules[child_index]
            if self._filepath == child_capsule_path and self._is_capsule_editor:
                print(f"Found target '{child_capsule_path.relative_to(c_parent_filepath)}', using argument data for this save.")
            else:
                data = bytearray()
                print(f"Saving {child_capsule_path.relative_to(c_parent_filepath)} to {capsule_path.relative_to(c_parent_filepath)}")
                write_erf(child_erf_or_rim, data) if isinstance(child_erf_or_rim, ERF) else write_rim(child_erf_or_rim, data)
            this_erf_or_rim.set_data(child_capsule_path.stem, ResourceType.from_extension(child_capsule_path.suffix), bytes(data))

        print(f"Finally saving '{c_filepath}'")
        write_erf(this_erf_or_rim, c_filepath) if isinstance(this_erf_or_rim, ERF) else write_rim(this_erf_or_rim, c_filepath)
        self.savedFile.emit(str(c_filepath), self._resname, self._restype, data)

    def _saveEndsWithErf(self, data: bytes, data_ext: bytes):
        # Create the mod file if it does not exist.
        """Saves data to an ERF/MOD file with the given extension.

        Args:
        ----
            data: {Bytes of data to save}
            data_ext: {Bytes of associated file extension if saving MDL}.

        Processing Logic:
        ----------------
            - Create the mod file if it does not exist
            - Read the existing ERF file
            - Set the ERF type based on file extension
            - For MDL, also save the MDX file data
            - Save the provided data and file reference
            - Write updated ERF back to file
            - Emit a signal that a file was saved
            - Reload the module in the installation cache.
        """
        assert self._filepath is not None, assert_with_variable_trace(self._filepath is not None)
        assert self._resname is not None, assert_with_variable_trace(self._resname is not None)
        assert self._restype is not None, assert_with_variable_trace(self._restype is not None)

        erftype: ERFType = ERFType.from_extension(self._filepath)
        c_filepath: CaseAwarePath = CaseAwarePath.pathify(self._filepath)

        if c_filepath.is_file():
            erf: ERF = read_erf(c_filepath)
        elif c_filepath.with_suffix(".rim").is_file():
            module.rim_to_mod(c_filepath)
            erf = read_erf(c_filepath)
        else:  # originally in a bif, user chose to save into erf/mod.
            print(f"Saving '{self._resname}.{self._restype}' to a blank new {erftype.name} file at '{c_filepath}'")
            erf = ERF(erftype)  # create a new ERF I guess.
        erf.erf_type = erftype

        # MDL is a special case - we need to save the MDX file with the MDL file.
        if self._restype is ResourceType.MDL:
            assert data_ext is not None, assert_with_variable_trace(data_ext is not None)
            erf.set_data(self._resname, ResourceType.MDX, data_ext)

        erf.set_data(self._resname, self._restype, data)

        write_erf(erf, c_filepath)
        self.savedFile.emit(str(c_filepath), self._resname, self._restype, data)

        # Update installation cache
        if self._installation is not None and c_filepath.parent == self._installation.module_path():
            self._installation.reload_module(c_filepath.name)

    def _saveEndsWithOther(self, data: bytes, data_ext: bytes):
        assert self._filepath is not None, assert_with_variable_trace(self._filepath is not None)

        c_filepath: CaseAwarePath = CaseAwarePath.pathify(self._filepath)
        with c_filepath.open("wb") as file:
            file.write(data)

        # MDL is a special case - we need to save the MDX file with the MDL file.
        if self._restype is ResourceType.MDL:
            with c_filepath.with_suffix(".mdx").open("wb") as file:
                file.write(data_ext)

        self.savedFile.emit(self._filepath, self._resname, self._restype, data)

    def open(self):
        """Opens a file dialog to select a file to open.

        Processing Logic:
        ----------------
            - Use QFileDialog to open a file dialog and get the selected filepath
            - Check if the selected file is a capsule file
            - If it is, show a LoadFromModuleDialog to get additional module data
            - Otherwise, directly load the file by path, reference, type and content
        """
        filepath_str, filter = QFileDialog.getOpenFileName(self, "Open file", "", self._openFilter)
        if not filepath_str.strip():
            return
        r_filepath = Path(filepath_str)

        capsule_types = " ".join(f"*.{e.name.lower()}" for e in ERFType) + " *.rim"
        if is_capsule_file(r_filepath) and f"Load from module ({capsule_types})" in self._openFilter:
            dialog = LoadFromModuleDialog(Capsule(r_filepath), self._readSupported)
            if dialog.exec_():
                self._load_module_from_dialog_info(dialog, r_filepath)
        else:
            data: bytes = BinaryReader.load_file(r_filepath)
            res_ident: ResourceIdentifier = ResourceIdentifier.from_path(r_filepath).validate()
            self.load(r_filepath, *res_ident.unpack(), data)

    def _load_module_from_dialog_info(self, dialog: LoadFromModuleDialog, c_filepath: Path):
        resname: str | None = dialog.resname()
        restype: ResourceType | None = dialog.restype()
        data: bytes | None = dialog.data()
        assert resname is not None, assert_with_variable_trace(resname is not None)
        assert restype is not None, assert_with_variable_trace(restype is not None)
        assert data is not None, assert_with_variable_trace(data is not None)

        self.load(c_filepath, resname, restype, data)

    @abstractmethod
    def build(self) -> tuple[bytes, bytes]: ...

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes):
        """Load a resource from a file.

        Args:
        ----
            filepath: Filepath to load resource from
            resref (str): Resource reference
            restype: ResourceType
            data (bytes): Resource data.

        Processing Logic:
        ----------------
            - Convert filepath to Path object if string
            - Set internal properties like filepath, resref, restype, data
            - Enable "Revert" menu item
            - Refresh window title
            - Emit loadedFile signal with load details.
        """
        self._filepath = Path.pathify(filepath)  # type: ignore[reportGeneralTypeIssues]
        self._resname = resref
        self._restype = restype
        self._revert = data
        for action in self.menuBar().actions()[0].menu().actions():
            if action.text() == "Revert":
                action.setEnabled(True)
                break
        self.refreshWindowTitle()
        self.loadedFile.emit(str(self._filepath), self._resname, self._restype, data)

    def exit(self):
        self.close()

    def new(self):
        self._revert = None
        self._filepath = None
        for action in self.menuBar().actions()[0].menu().actions():
            if action.text() != "Revert":
                continue
            action.setEnabled(False)
        self.refreshWindowTitle()
        self.newFile.emit()

    def revert(self):
        if self._revert is None:
            print("No data to revert from")
            return
        assert self._filepath is not None, assert_with_variable_trace(self._filepath is not None)
        assert self._resname is not None, assert_with_variable_trace(self._resname is not None)
        assert self._restype is not None, assert_with_variable_trace(self._restype is not None)
        self.load(self._filepath, self._resname, self._restype, self._revert)

    def _loadLocstring(self, textbox: QLineEdit | QPlainTextEdit, locstring: LocalizedString):
        """Loads a LocalizedString into a textbox.

        Args:
        ----
            textbox: QLineEdit or QPlainTextEdit - Textbox to load string into
            locstring: LocalizedString - String to load


        Processing Logic:
        ----------------
            - Determines if textbox is QLineEdit or QPlainTextEdit
            - Sets textbox's locstring property
            - Checks if locstring has stringref or not
            - Sets textbox text and style accordingly.
        """
        setText: Callable[[str], None] = textbox.setPlainText if isinstance(textbox, QPlainTextEdit) else textbox.setText
        className = "QLineEdit" if isinstance(textbox, QLineEdit) else "QPlainTextEdit"

        textbox.locstring = locstring  # type: ignore[reportAttributeAccessIssue]
        if locstring.stringref == -1:
            text = str(locstring)
            setText(text if text != "-1" else "")
            textbox.setStyleSheet(className + " {background-color: white;}")
        else:
            assert self._installation is not None
            setText(self._installation.talktable().string(locstring.stringref))
            textbox.setStyleSheet(className + " {background-color: #fffded;}")

    def filepath(self) -> str | None:
        return str(self._filepath)
