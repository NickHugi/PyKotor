from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from pykotor.common.module import Module
from pykotor.extract.capsule import Capsule
from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.formats.erf import ERFType, read_erf, write_erf
from pykotor.resource.formats.rim import read_rim, write_rim
from pykotor.resource.type import ResourceType
from pykotor.tools import module
from pykotor.tools.misc import is_any_erf_type_file, is_bif_file, is_capsule_file, is_rim_file
from pykotor.tools.path import CaseAwarePath
from PyQt5 import QtCore
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QFileDialog, QLineEdit, QMainWindow, QMessageBox, QPlainTextEdit, QShortcut, QWidget
from toolset.gui.dialogs.load_from_module import LoadFromModuleDialog
from toolset.gui.dialogs.save.to_bif import BifSaveDialog, BifSaveOption
from toolset.gui.dialogs.save.to_module import SaveToModuleDialog
from toolset.gui.dialogs.save.to_rim import RimSaveDialog, RimSaveOption
from toolset.gui.widgets.settings.installations import GlobalSettings
from utility.error_handling import format_exception_with_variables, universal_simplify_exception
from utility.path import Path

if TYPE_CHECKING:
    import os

    from pykotor.common.language import LocalizedString
    from toolset.data.installation import HTInstallation


class Editor(QMainWindow):
    """Editor is a base class for all file-specific editors.

    Provides methods for saving and loading files that are stored directly in folders and for files that are encapsulated in a MOD or RIM.
    """

    newFile = QtCore.pyqtSignal()
    savedFile = QtCore.pyqtSignal(object, object, object, object)
    loadedFile = QtCore.pyqtSignal(object, object, object, object)

    def __init__(
        self,
        parent: QWidget | None,
        title: str,
        iconName: str,
        readSupported: list[ResourceType],
        writeSupported: list[ResourceType],
        installation: HTInstallation | None = None,
        mainwindow: QMainWindow | None = None,
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

        self._filepath: Path | None = None
        self._resname: str | None = None
        self._restype: ResourceType | None = None
        self._revert: bytes | None = None
        self._readSupported: list[ResourceType] = readSupported
        self._writeSupported: list[ResourceType] = writeSupported
        self._global_settings: GlobalSettings = GlobalSettings()
        self._installation: HTInstallation = installation
        self._mainwindow: QMainWindow | None = mainwindow

        self._editorTitle: str = title
        self.setWindowTitle(title)
        self._setupIcon(iconName)

        self._saveFilter: str = "All valid files ("
        for resource in writeSupported:
            self._saveFilter += f'*.{resource.extension}{"" if writeSupported[-1] == resource else " "}'
        self._saveFilter += " *.erf *.mod *.rim *.sav);;"
        for resource in writeSupported:
            self._saveFilter += f"{resource.category} File (*.{resource.extension});;"
        self._saveFilter += "Save into module (*.erf *.mod *.rim *.sav)"

        self._openFilter: str = "All valid files ("
        for resource in readSupported:
            self._openFilter += f'*.{resource.extension}{"" if readSupported[-1] == resource else " "}'
        self._openFilter += " *.erf *.mod *.rim *.sav);;"
        for resource in readSupported:
            self._openFilter += f"{resource.category} File (*.{resource.extension});;"
        self._openFilter += "Load from module (*.erf *.mod *.rim *.sav)"

    def _setupMenus(self):
        """Sets up menu actions and keyboard shortcuts.

        Processing Logic:
        ----------------
            - Loops through menu actions and connects signals for New, Open, Save, Save As, Revert and Exit
            - Sets Revert action to disabled
            - Connects keyboard shortcuts for New, Open, Save, Save As, Revert and Exit.
        """
        for action in self.menuBar().actions()[0].menu().actions():
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
        """Refreshes the window title based on the current state.

        Processing Logic:
        ----------------
            - Sets the installation name variable based on whether an installation is set or not
            - Checks if a file path is set, if not just uses the editor title
            - If encapsulated, constructs the title combining file path, installation, editor title
            - If not encapsulated, constructs title combining parent folder, file, installation, editor title.
        """
        installationName = "No Installation" if self._installation is None else self._installation.name  # TODO: Fix it always saying 'no installation' in every case.

        if self._filepath is None:
            self.setWindowTitle(self._editorTitle)
        elif is_capsule_file(self._filepath.name):
            self.setWindowTitle(f"{self._filepath.name}/{self._resname}.{self._restype.extension} - {installationName} - {self._editorTitle}")
        else:
            hierarchy: tuple[str, ...] = self._filepath.parts
            folder = f"{hierarchy[-2]}/" if len(hierarchy) >= 2 else ""
            self.setWindowTitle(f"{folder}{self._resname}.{self._restype.extension} - {installationName} - {self._editorTitle}")

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

        if is_capsule_file(filepath_str) and "Save into module (*.erf *.mod *.rim *.sav)" in self._saveFilter:
            if self._resname is None:
                self._resname = "new"
                self._restype = self._writeSupported[0]

            dialog2 = SaveToModuleDialog(self._resname, self._restype, self._writeSupported)
            if dialog2.exec_():
                self._resname = dialog2.resref()
                self._restype = dialog2.restype()
                self._filepath = Path(filepath_str)
        else:
            self._filepath = Path(filepath_str)
            self._resname, self._restype = ResourceIdentifier.from_path(self._filepath).validate()
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
            self._revert = data

            self.refreshWindowTitle()

            if is_bif_file(self._filepath.name):
                self._saveEndsWithBif(data, data_ext)
            elif is_rim_file(self._filepath.name):
                self._saveEndsWithRim(data, data_ext)
            elif is_any_erf_type_file(self._filepath.name):
                self._saveEndsWithErf(data, data_ext)
            else:
                self._saveEndsWithOther(data, data_ext)
        except Exception as e:  # noqa: BLE001
            with Path("errorlog.txt").open("a", encoding="utf-8") as file:
                lines = format_exception_with_variables(e)
                file.writelines(lines)
                file.write("\n----------------------\n")
            QMessageBox(QMessageBox.Critical, "Failed to write to file", str(universal_simplify_exception(e))).exec_()

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
            filepath, filter = QFileDialog.getSaveFileName(self, "Save As", "", ".MOD File (*.mod)", "")
            dialog2 = SaveToModuleDialog(self._resname, self._restype, self._writeSupported)
            if dialog2.exec_():
                self._resname = dialog2.resref()
                self._restype = dialog2.restype()
                self._filepath = Path(filepath)
                self.save()
        elif dialog.option == BifSaveOption.Override:
            self._filepath = self._installation.override_path() / f"{self._resname}.{self._restype.extension}"
            self.save()

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
        """
        if self._global_settings.disableRIMSaving:
            dialog = RimSaveDialog(self)
            dialog.exec_()
            if dialog.option == RimSaveOption.MOD:
                folderpath: Path = self._filepath.parent
                filename: str = f"{Module.get_root(self._filepath)}.mod"
                self._filepath = folderpath / filename
                # Re-save with the updated filepath
                self.save()
            elif dialog.option == RimSaveOption.Override:
                self._filepath = self._installation.override_path() / f"{self._resname}.{self._restype.extension}"
                self.save()
            return

        rim = read_rim(self._filepath)

        # MDL is a special case - we need to save the MDX file with the MDL file.
        if self._restype == ResourceType.MDL:
            rim.set_data(self._resname, ResourceType.MDX, data_ext)

        rim.set_data(self._resname, self._restype, data)

        write_rim(rim, self._filepath)
        self.savedFile.emit(str(self._filepath), self._resname, self._restype, data)

        # Update installation cache
        if self._installation is not None:
            basename = self._filepath.name
            self._installation.reload_module(basename)

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
        if not self._filepath.exists():
            module.rim_to_mod(self._filepath)

        erf = read_erf(self._filepath)
        erf.erf_type = ERFType.from_extension(self._filepath)

        # MDL is a special case - we need to save the MDX file with the MDL file.
        if self._restype == ResourceType.MDL:
            erf.set_data(self._resname, ResourceType.MDX, data_ext)

        erf.set_data(self._resname, self._restype, data)

        write_erf(erf, self._filepath)
        self.savedFile.emit(self._filepath, self._resname, self._restype, data)

        # Update installation cache
        if self._installation is not None:
            self._installation.reload_module(self._filepath.name)

    def _saveEndsWithOther(self, data: bytes, data_ext: bytes):
        with self._filepath.open("wb") as file:
            file.write(data)

        # MDL is a special case - we need to save the MDX file with the MDL file.
        if self._restype == ResourceType.MDL:
            with CaseAwarePath.pathify(self._filepath).with_suffix(".mdx").open("wb") as file:
                file.write(data_ext)

        self.savedFile.emit(self._filepath, self._resname, self._restype, data)

    def open(self):  # noqa: A003
        """Opens a file dialog to select a file to open.

        Processing Logic:
        ----------------
            - Use QFileDialog to open a file dialog and get the selected filepath
            - Check if the selected file is a capsule file
            - If it is, show a LoadFromModuleDialog to get additional module data
            - Otherwise, directly load the file by path, reference, type and content
        """
        filepath_str, filter = QFileDialog.getOpenFileName(self, "Open file", "", self._openFilter)
        if filepath_str:
            c_filepath = Path(filepath_str)
            if is_capsule_file(c_filepath.name) and "Load from module (*.erf *.mod *.rim *.sav)" in self._openFilter:
                dialog = LoadFromModuleDialog(Capsule(c_filepath), self._readSupported)
                if dialog.exec_():
                    self.load(c_filepath, dialog.resname(), dialog.restype(), dialog.data())
            else:
                with c_filepath.open("rb") as file:
                    data = file.read()
                self.load(c_filepath, *ResourceIdentifier.from_path(c_filepath).validate(), data)

    @abstractmethod
    def build(self) -> tuple[bytes, bytes]:
        ...

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
        self.refreshWindowTitle()
        self.loadedFile.emit(str(self._filepath), self._resname, self._restype, data)

    def exit(self):  # noqa: A003
        self.close()

    def new(self):
        self._revert = None
        self._filepath = None
        for action in self.menuBar().actions()[0].menu().actions():
            if action.text() == "Revert":
                action.setEnabled(False)
        self.refreshWindowTitle()
        self.newFile.emit()

    def revert(self):
        if self._revert is not None:
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
        setText = textbox.setPlainText if isinstance(textbox, QPlainTextEdit) else textbox.setText
        className = "QLineEdit" if isinstance(textbox, QLineEdit) else "QPlainTextEdit"

        textbox.locstring = locstring
        if locstring.stringref == -1:
            text = str(locstring)
            setText(text if text != "-1" else "")
            textbox.setStyleSheet(className + " {background-color: white;}")
        else:
            setText(self._installation.talktable().string(locstring.stringref))
            textbox.setStyleSheet(className + " {background-color: #fffded;}")

    def filepath(self) -> str | None:
        return str(self._filepath)
