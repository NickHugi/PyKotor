import os
from abc import abstractmethod
from typing import List, Union, Optional

from PyQt5.QtWidgets import QMainWindow, QDialog, QFileDialog, QMenu, QMessageBox, QMenuBar, QListWidgetItem, QAction, \
    QShortcut
from pykotor.extract.capsule import Capsule
from pykotor.resource.formats.erf import write_erf, load_erf, ERFType, ERF
from pykotor.resource.formats.rim import load_rim, write_rim, RIM
from pykotor.resource.type import ResourceType

from editors import savetomodule_ui, loadfrommodule_ui


class Editor(QMainWindow):
    """
    Editor is a base class for all file-specific editors. It provides methods for saving and loading files that are
    stored directly in folders and for files that are encapsulated in a MOD or RIM.
    """
    def __init__(self, parent, title: str, read_supported: List[ResourceType], write_supported: List[ResourceType]):
        super().__init__(parent)

        self.msgbox = None

        self._filepath: Optional[str] = None
        self._resref: Optional[str] = None
        self._restype: Optional[ResourceType] = None
        self._revert: Optional[bytes] = None
        self._read_supported: List[ResourceType] = read_supported
        self._write_supported: List[ResourceType] = write_supported

        self._editor_title = title
        self.setWindowTitle(title)

        self._saveFilter: str = "All valid files ("
        for resource in write_supported:
            self._saveFilter += "*.{}{}".format(resource.extension, "" if write_supported[-1] == resource else " ")
        self._saveFilter += " *.erf *.mod *.rim);;"
        for resource in write_supported:
            self._saveFilter += "{} File (*.{});;".format(resource.category, resource.extension)
        self._saveFilter += "Save into module (*.erf *.mod *.rim)"

        self._openFilter: str = "All valid files ("
        for resource in read_supported:
            self._openFilter += "*.{}{}".format(resource.extension, "" if read_supported[-1] == resource else " ")
        self._openFilter += " *.erf *.mod *.rim);;"
        for resource in read_supported:
            self._openFilter += "{} File (*.{});;".format(resource.category, resource.extension)
        self._openFilter += "Load from module (*.erf *.mod *.rim)"

    def _setup_menus(self) -> None:
        for action in self.menuBar().actions()[0].menu().actions():
            if action.text() == "New": action.triggered.connect(self.new)
            if action.text() == "Open": action.triggered.connect(self.open)
            if action.text() == "Save": action.triggered.connect(self.save)
            if action.text() == "Save As": action.triggered.connect(self.saveAs)
            if action.text() == "Revert": action.triggered.connect(self.revert)
            if action.text() == "Revert": action.setEnabled(False)
            if action.text() == "Exit": action.triggered.connect(self.close)
        QShortcut("Ctrl+N", self).activated.connect(self.new)
        QShortcut("Ctrl+O", self).activated.connect(self.open)
        QShortcut("Ctrl+S", self).activated.connect(self.save)
        QShortcut("Ctrl+Shift+S", self).activated.connect(self.saveAs)
        QShortcut("Ctrl+R", self).activated.connect(self.revert)
        QShortcut("Ctrl+Q", self).activated.connect(self.exit)

    def encapsulated(self) -> bool:
        return self._filepath.endswith(".rim") or self._filepath.endswith(".erf") or self._filepath.endswith(".mod")

    def refreshWindowTitle(self) -> None:
        if self._filepath is None:
            self.setWindowTitle(self._editor_title)
        elif self.encapsulated():
            self.setWindowTitle("{}.{} - {}".format(self._resref, self._restype.extension, self._editor_title))
            # self.setWindowTitle("{}/{}.{} - {}".format(self._filepath, self._resref, self._restype.extension, self._editor_title))
        else:
            self.setWindowTitle("{}.{} - {}".format(self._resref, self._restype.extension, self._editor_title))
            # self.setWindowTitle("{} - {}".format(self._filepath, self._editor_title))

    def saveAs(self) -> None:
        filepath, filter = QFileDialog.getSaveFileName(self, "Save As", "", self._saveFilter, "")
        if filepath != "":
            encapsulated = filepath.endswith(".erf") or filepath.endswith(".mod") or filepath.endswith(".rim")
            if encapsulated:
                if self._resref is None:
                    self._resref = "new"
                    self._restype = self._write_supported[0]

                dialog2 = SaveToModuleDialog(self._resref, self._restype, self._write_supported)
                if dialog2.exec_():
                    self._resref = dialog2.resref()
                    self._restype = dialog2.restype()
                    self._filepath = filepath
            else:
                self._filepath = filepath
                self._resref, restype_ext = os.path.basename(self._filepath).split('.', 1)
                self._restype = ResourceType.from_extension(restype_ext)
            self.save()

            self.refreshWindowTitle()
            for action in self.menuBar().actions()[0].menu().actions():
                if action.text() == "Revert": action.setEnabled(True)

    def save(self) -> None:
        if self._filepath is None:
            self.saveAs()
            return

        try:
            data = self.build()
            self._revert = data

            if self._filepath.endswith(".bif"):
                self.msgbox = QMessageBox(QMessageBox.Critical, "Could not save file",
                                          "Cannot save resource into a .BIF file, select another destination instead.")
                self.msgbox.show()
            elif self._filepath.endswith(".rim"):
                rim = load_rim(self._filepath)
                rim.set(self._resref, self._restype, data)
                write_rim(rim, self._filepath)
            elif self._filepath.endswith(".erf") or self._filepath.endswith(".mod"):
                erf = load_erf(self._filepath)
                erf.erf_type = ERFType.ERF if self._filepath.endswith(".erf") else ERFType.MOD
                erf.set(self._resref, self._restype, data)
                write_erf(erf, self._filepath)
            else:
                with open(self._filepath, 'wb') as file:
                    file.write(data)
        except Exception as e:
            QMessageBox(QMessageBox.Critical, "Failed to write to file", str(e)).exec_()

    def open(self):
        filepath, filter = QFileDialog.getOpenFileName(self, "Open file", "", self._openFilter)
        if filepath != "":
            encapsulated = filepath.endswith(".erf") or filepath.endswith(".mod") or filepath.endswith(".rim")
            if encapsulated:
                dialog = LoadFromModuleDialog(Capsule(filepath), self._read_supported)
                if dialog.exec_():
                    self.load(filepath, dialog.resref(), dialog.restype(), dialog.data())
            else:
                resref, restype_ext = os.path.basename(filepath).split('.', 1)
                restype = ResourceType.from_extension(restype_ext)
                with open(filepath, 'rb') as file:
                    data = file.read()

                self.load(filepath, resref, restype, data)

    @abstractmethod
    def build(self) -> bytes:
        ...

    def load(self, filepath: str, resref: str, restype: ResourceType, data: bytes) -> None:
        self._filepath = filepath
        self._resref = resref
        self._restype = restype
        self._revert = data
        for action in self.menuBar().actions()[0].menu().actions():
            if action.text() == "Revert": action.setEnabled(True)
        self.refreshWindowTitle()

    def exit(self) -> None:
        self.close()

    def new(self) -> None:
        self._revert = None
        self._filepath = None
        for action in self.menuBar().actions()[0].menu().actions():
            if action.text() == "Revert": action.setEnabled(False)
        self.refreshWindowTitle()

    def revert(self) -> None:
        if self._revert is not None:
            self.load(self._filepath, self._resref, self._restype, self._revert)


class SaveToModuleDialog(QDialog):
    """
    SaveToModuleDialog lets the user specify a ResRef and a resource type when saving to a module.
    """
    def __init__(self, resref, restype, supported):
        super().__init__()

        self.ui = savetomodule_ui.Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.resrefEdit.setText(resref)
        self.ui.typeCombo.addItems([restype.extension.upper() for restype in supported])
        self.ui.typeCombo.setCurrentIndex(supported.index(restype))

    def resref(self) -> str:
        return self.ui.resrefEdit.text()

    def restype(self) -> ResourceType:
        return ResourceType.from_extension(self.ui.typeCombo.currentText().lower())


class LoadFromModuleDialog(QDialog):
    """
    LoadFromModuleDialog lets the user select a resource from a ERF or RIM.
    """
    def __init__(self, capsule: Capsule, supported):
        super().__init__()

        self.ui = loadfrommodule_ui.Ui_Dialog()
        self.ui.setupUi(self)

        for resource in capsule:
            if resource.restype() not in supported:
                continue
            filename = resource.resref() + "." + resource.restype().extension
            item = QListWidgetItem(filename)
            item.resource = resource
            self.ui.resourceList.addItem(item)

    def resref(self) -> str:
        return self.ui.resourceList.currentItem().resource.resref()

    def restype(self) -> ResourceType:
        return self.ui.resourceList.currentItem().resource.restype()

    def data(self) -> bytes:
        return self.ui.resourceList.currentItem().resource.data()

