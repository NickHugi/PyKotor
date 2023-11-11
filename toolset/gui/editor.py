from __future__ import annotations

import traceback
from abc import abstractmethod
from typing import TYPE_CHECKING, Optional, Union

from PyQt5 import QtCore
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (
    QFileDialog,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QShortcut,
    QWidget,
)

from pykotor.helpers.path import Path
from pykotor.common.module import Module
from pykotor.extract.capsule import Capsule
from pykotor.resource.formats.erf import ERFType, read_erf, write_erf
from pykotor.resource.formats.rim import read_rim, write_rim
from pykotor.resource.type import ResourceType
from pykotor.tools import module
from pykotor.tools.misc import (
    is_bif_file,
    is_capsule_file,
    is_erf_or_mod_file,
    is_rim_file,
)
from toolset.gui.dialogs.load_from_module import LoadFromModuleDialog
from toolset.gui.dialogs.save.to_bif import BifSaveDialog, BifSaveOption
from toolset.gui.dialogs.save.to_module import SaveToModuleDialog
from toolset.gui.dialogs.save.to_rim import RimSaveDialog, RimSaveOption
from toolset.gui.widgets.settings.installations import GlobalSettings

if TYPE_CHECKING:
    import os

    from pykotor.common.language import LocalizedString
    from toolset.data.installation import HTInstallation


class Editor(QMainWindow):
    """Editor is a base class for all file-specific editors. It provides methods for saving and loading files that are
    stored directly in folders and for files that are encapsulated in a MOD or RIM.
    """

    newFile = QtCore.pyqtSignal()
    savedFile = QtCore.pyqtSignal(object, object, object, object)
    loadedFile = QtCore.pyqtSignal(object, object, object, object)

    def __init__(
        self,
        parent: Optional[QWidget],
        title: str,
        iconName: str,
        readSupported: list[ResourceType],
        writeSupported: list[ResourceType],
        installation: Optional[HTInstallation] = None,
        mainwindow: Optional[QMainWindow] = None,
    ):
        super().__init__(parent)

        self._filepath: Optional[Path] = None
        self._resref: Optional[str] = None
        self._restype: Optional[ResourceType] = None
        self._revert: Optional[bytes] = None
        self._readSupported: list[ResourceType] = readSupported
        self._writeSupported: list[ResourceType] = writeSupported
        self._global_settings: GlobalSettings = GlobalSettings()
        self._installation: Optional[HTInstallation] = installation
        self._mainwindow = mainwindow

        self._editorTitle = title
        self.setWindowTitle(title)
        self._setupIcon(iconName)

        self._saveFilter: str = "All valid files ("
        for resource in writeSupported:
            self._saveFilter += f'*.{resource.extension}{"" if writeSupported[-1] == resource else " "}'
        self._saveFilter += " *.erf *.mod *.rim);;"
        for resource in writeSupported:
            self._saveFilter += f"{resource.category} File (*.{resource.extension});;"
        self._saveFilter += "Save into module (*.erf *.mod *.rim)"

        self._openFilter: str = "All valid files ("
        for resource in readSupported:
            self._openFilter += f'*.{resource.extension}{"" if readSupported[-1] == resource else " "}'
        self._openFilter += " *.erf *.mod *.rim);;"
        for resource in readSupported:
            self._openFilter += f"{resource.category} File (*.{resource.extension});;"
        self._openFilter += "Load from module (*.erf *.mod *.rim)"

    def _setupMenus(self) -> None:
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
                action.triggered.connect(self.close)
        QShortcut("Ctrl+N", self).activated.connect(self.new)
        QShortcut("Ctrl+O", self).activated.connect(self.open)
        QShortcut("Ctrl+S", self).activated.connect(self.save)
        QShortcut("Ctrl+Shift+S", self).activated.connect(self.saveAs)
        QShortcut("Ctrl+R", self).activated.connect(self.revert)
        QShortcut("Ctrl+Q", self).activated.connect(self.exit)

    def _setupIcon(self, iconName: str) -> None:
        iconVersion = "x" if self._installation is None else "2" if self._installation.tsl else "1"
        iconPath = f":/images/icons/k{iconVersion}/{iconName}.png"
        self.setWindowIcon(QIcon(QPixmap(iconPath)))

    def encapsulated(self) -> bool:
        return (
            self._filepath.endswith(".rim")
            or self._filepath.endswith(".erf")
            or self._filepath.endswith(".mod")
            or self._filepath.endswith(".bif")
        )

    def refreshWindowTitle(self) -> None:
        installationName = "No Installation" if self._installation is None else self._installation.name

        if self._filepath is None:
            self.setWindowTitle(self._editorTitle)
        elif self.encapsulated():
            self.setWindowTitle(
                f"{self._filepath.name}/{self._resref}.{self._restype.extension} - {installationName} - {self._editorTitle}",
            )
        else:
            folders = self._filepath.parts
            folder = folders[-2] if len(folders) >= 2 else ""
            self.setWindowTitle(
                f"{folder}/{self._resref}.{self._restype.extension} - {installationName} - {self._editorTitle}",
            )

    def saveAs(self) -> None:
        filepath_str, _filter = QFileDialog.getSaveFileName(self, "Save As", "", self._saveFilter, "")
        if filepath_str != "":
            encapsulated = filepath_str.lower().endswith((".erf", ".mod", ".rim"))
            encapsulated = encapsulated and "Save into module (*.erf *.mod *.rim)" in self._saveFilter
            if encapsulated:
                if self._resref is None:
                    self._resref = "new"
                    self._restype = self._writeSupported[0]

                dialog2 = SaveToModuleDialog(self._resref, self._restype, self._writeSupported)
                if dialog2.exec_():
                    self._resref = dialog2.resref()
                    self._restype = dialog2.restype()
                    self._filepath = Path(filepath_str)
            else:
                self._filepath = Path(filepath_str)
                self._resref, restype_ext = self._filepath.stem, self._filepath.suffix[1:]
                self._restype = ResourceType.from_extension(restype_ext)
            self.save()

            self.refreshWindowTitle()
            for action in self.menuBar().actions()[0].menu().actions():
                if action.text() == "Revert":
                    action.setEnabled(True)

    def save(self) -> None:
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
            elif is_erf_or_mod_file(self._filepath.name):
                self._saveEndsWithErf(data, data_ext)
            else:
                self._saveEndsWithOther(data, data_ext)
        except Exception as e:  # noqa: BLE001
            with Path("errorlog.txt").open("a") as file:
                lines = traceback.format_exception(type(e), e, e.__traceback__)
                file.writelines(lines)
                file.write("\n----------------------\n")
            QMessageBox(QMessageBox.Critical, "Failed to write to file", str(e)).exec_()

    def _saveEndsWithBif(self, data: bytes, data_ext: bytes):
        dialog = BifSaveDialog(self)
        dialog.exec_()
        if dialog.option == BifSaveOption.MOD:
            filepath, filter = QFileDialog.getSaveFileName(self, "Save As", "", ".MOD File (*.mod)", "")
            dialog2 = SaveToModuleDialog(self._resref, self._restype, self._writeSupported)
            if dialog2.exec_():
                self._resref = dialog2.resref()
                self._restype = dialog2.restype()
                self._filepath = Path(filepath)
                self.save()
        elif dialog.option == BifSaveOption.Override:
            self._filepath = self._installation.override_path() / f"{self._resref}.{self._restype.extension}"
            self.save()

    def _saveEndsWithRim(self, data: bytes, data_ext: bytes):
        if self._global_settings.disableRIMSaving:
            dialog = RimSaveDialog(self)
            dialog.exec_()
            if dialog.option == RimSaveOption.MOD:
                folderpath = self._filepath.parent
                filename = f"{Module.get_root(str(self._filepath))}.mod"
                self._filepath = folderpath / filename
                # Re-save with the updated filepath
                self.save()
            elif dialog.option == RimSaveOption.Override:
                self._filepath = self._installation.override_path().joinpath(f"{self._resref}.{self._restype.extension}")
                self.save()
            return

        rim = read_rim(self._filepath)

        # MDL is a special case - we need to save the MDX file with the MDL file.
        if self._restype == ResourceType.MDL:
            rim.set_data(self._resref, ResourceType.MDX, data_ext)

        rim.set_data(self._resref, self._restype, data)

        write_rim(rim, self._filepath)
        self.savedFile.emit(str(self._filepath), self._resref, self._restype, data)

        # Update installation cache
        if self._installation is not None:
            basename = self._filepath.name
            self._installation.reload_module(basename)

    def _saveEndsWithErf(self, data: bytes, data_ext: bytes):
        # Create the mod file if it does not exist.
        if not self._filepath.exists():
            module.rim_to_mod(self._filepath)

        erf = read_erf(self._filepath)
        erf.erf_type = ERFType.ERF if self._filepath.endswith(".erf") else ERFType.MOD

        # MDL is a special case - we need to save the MDX file with the MDL file.
        if self._restype == ResourceType.MDL:
            erf.set_data(self._resref, ResourceType.MDX, data_ext)

        erf.set_data(self._resref, self._restype, data)

        write_erf(erf, self._filepath)
        self.savedFile.emit(self._filepath, self._resref, self._restype, data)

        # Update installation cache
        if self._installation is not None:
            self._installation.reload_module(self._filepath.name)

    def _saveEndsWithOther(self, data: bytes, data_ext: bytes):
        with self._filepath.open("wb") as file:
            file.write(data)

        # MDL is a special case - we need to save the MDX file with the MDL file.
        if self._restype == ResourceType.MDL:
            with (self._filepath.with_suffix(".mdx")).open("wb") as file:
                file.write(data_ext)

        self.savedFile.emit(self._filepath, self._resref, self._restype, data)

    def open(self):  # noqa: A003
        filepath_str, filter = QFileDialog.getOpenFileName(self, "Open file", "", self._openFilter)
        if filepath_str != "":
            c_filepath = Path(filepath_str)
            encapsulated = is_capsule_file(c_filepath.name)
            encapsulated = encapsulated and "Load from module (*.erf *.mod *.rim)" in self._openFilter
            if encapsulated:
                dialog = LoadFromModuleDialog(Capsule(c_filepath), self._readSupported)
                if dialog.exec_():
                    self.load(c_filepath, dialog.resref(), dialog.restype(), dialog.data())
            else:
                resref, restype_ext = c_filepath.stem, c_filepath.suffix[1:]
                restype = ResourceType.from_extension(restype_ext)
                with c_filepath.open("rb") as file:
                    data = file.read()

                self.load(c_filepath, resref, restype, data)

    @abstractmethod
    def build(self) -> tuple[bytes, bytes]:
        ...

    def load(self, filepath: os.PathLike | str, resref: str, restype: ResourceType, data: bytes) -> None:
        self._filepath = filepath if isinstance(filepath, Path) else Path(filepath)
        self._resref = resref
        self._restype = restype
        self._revert = data
        for action in self.menuBar().actions()[0].menu().actions():
            if action.text() == "Revert":
                action.setEnabled(True)
        self.refreshWindowTitle()
        self.loadedFile.emit(str(self._filepath), self._resref, self._restype, data)

    def exit(self) -> None:  # noqa: A003
        self.close()

    def new(self) -> None:
        self._revert = None
        self._filepath = None
        for action in self.menuBar().actions()[0].menu().actions():
            if action.text() == "Revert":
                action.setEnabled(False)
        self.refreshWindowTitle()
        self.newFile.emit()

    def revert(self) -> None:
        if self._revert is not None:
            self.load(self._filepath, self._resref, self._restype, self._revert)

    def _loadLocstring(self, textbox: Union[QLineEdit, QPlainTextEdit], locstring: LocalizedString) -> None:
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

    def filepath(self) -> Optional[str]:
        return str(self._filepath)
