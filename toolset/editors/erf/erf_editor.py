import os
from typing import Optional

from PyQt5.QtCore import QItemSelection
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QWidget
from pykotor.common.misc import ResRef
from pykotor.extract.installation import Installation
from pykotor.resource.formats.erf import load_erf, ERF, ERFType, write_erf, ERFResource
from pykotor.resource.formats.rim import load_rim, write_rim, RIM
from pykotor.resource.type import ResourceType

from editors.editor import Editor
from editors.erf import erf_editor_ui


class ERFEditor(Editor):
    def __init__(self, parent: QWidget, installation: Optional[Installation] = None):
        supported = [ResourceType.ERF, ResourceType.MOD, ResourceType.RIM]
        super().__init__(parent, "ERF Editor", supported, supported, installation)
        self.resize(400, 250)

        self.ui = erf_editor_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_menus()

        self.model = QStandardItemModel(self)
        self.ui.tableView.setModel(self.model)

        self.ui.extractButton.clicked.connect(self.extractSelected)
        self.ui.loadButton.clicked.connect(self.add)
        self.ui.unloadButton.clicked.connect(self.removeSelected)
        self.ui.openButton.clicked.connect(self.openSelected)
        self.ui.refreshButton.clicked.connect(self.refresh)
        self.ui.tableView.selectionModel().selectionChanged.connect(self.selectionChanged)

        # Disable saving file into module
        self._saveFilter = self._saveFilter.replace(";;Save into module (*.erf *.mod *.rim)", "")
        self._openFilter = self._openFilter.replace(";;Load from module (*.erf *.mod *.rim)", "")

        self.new()

    def load(self, filepath: str, resref: str, restype: ResourceType, data: bytes) -> None:
        super().load(filepath, resref, restype, data)

        self.model.clear()
        self.model.setColumnCount(3)
        self.model.setHorizontalHeaderLabels(["ResRef", "Type", "Size"])
        self.ui.refreshButton.setEnabled(True)

        if restype in [ResourceType.ERF, ResourceType.MOD]:
            erf = load_erf(data)
            for resource in erf:
                resrefItem = QStandardItem(resource.resref.get())
                resrefItem.setData(resource)
                restypeItem = QStandardItem(resource.restype.extension.upper())
                sizeItem = QStandardItem(str(len(resource.data)))
                self.model.appendRow([resrefItem, restypeItem, sizeItem])
        elif restype in [ResourceType.RIM]:
            rim = load_rim(data)
            for resource in rim:
                resrefItem = QStandardItem(resource.resref.get())
                resrefItem.setData(resource)
                restypeItem = QStandardItem(resource.restype.extension.upper())
                sizeItem = QStandardItem(str(len(resource.data)))
                self.model.appendRow([resrefItem, restypeItem, sizeItem])
        else:
            QMessageBox(QMessageBox.Critical, "Unable to load file", "The file specified is not a MOD/ERF type file.",
                        ..., self).show()

    def build(self) -> bytes:
        data = bytearray()

        if self._restype == ResourceType.RIM:
            rim = RIM()
            for i in range(self.model.rowCount()):
                item = self.model.item(i, 0)
                resource = item.data()
                rim.set(resource.resref.get(), resource.restype, resource.data)
            write_rim(rim, data)
        if self._restype in [ResourceType.ERF, ResourceType.MOD]:
            erfType = ERFType.ERF if self._restype == ResourceType.ERF else ERFType.MOD
            erf = ERF(erfType)
            for i in range(self.model.rowCount()):
                item = self.model.item(i, 0)
                resource = item.data()
                erf.set(resource.resref.get(), resource.restype, resource.data)
            write_erf(erf, data)

        return data

    def new(self) -> None:
        super().new()
        self.model.clear()
        self.model.setColumnCount(3)
        self.model.setHorizontalHeaderLabels(["ResRef", "Type", "Size"])
        self.ui.refreshButton.setEnabled(False)

    def save(self) -> None:
        # Must override the method as the superclass method breaks due to filepath always ending in .rim/mod/erf
        if self._filepath is None:
            self.saveAs()
            return

        self.ui.refreshButton.setEnabled(True)

        data = self.build()
        self._revert = data

        with open(self._filepath, 'wb') as file:
            file.write(data)

    def extractSelected(self) -> None:
        folderpath = QFileDialog.getExistingDirectory(self, "Extract to folder")

        if folderpath != "":
            self.ui.tableView.selectionModel().selectedRows()
            for index in self.ui.tableView.selectionModel().selectedRows(0):
                item = self.model.itemFromIndex(index)
                resource = item.data()
                filepath = "{}/{}.{}".format(folderpath, resource.resref, resource.restype.extension)
                with open(filepath, 'wb') as file:
                    file.write(resource.data)

    def removeSelected(self) -> None:
        for index in self.ui.tableView.selectionModel().selectedRows(0):
            item = self.model.itemFromIndex(index)
            self.model.removeRow(item.row())

    def add(self) -> None:
        filepaths = QFileDialog.getOpenFileNames(self, "Load files into module")[:-1][0]

        for filepath in filepaths:
            with open(filepath, 'rb') as file:
                resref, restype_ext = os.path.basename(filepath).split('.', 1)
                restype = ResourceType.from_extension(restype_ext)
                data = file.read()

                resource = ERFResource(ResRef(resref), restype, data)

                resrefItem = QStandardItem(resource.resref.get())
                resrefItem.setData(resource)
                restypeItem = QStandardItem(resource.restype.extension.upper())
                sizeItem = QStandardItem(str(len(resource.data)))
                self.model.appendRow([resrefItem, restypeItem, sizeItem])

    def openSelected(self) -> None:
        if self._filepath is None:
            QMessageBox(QMessageBox.Critical, "Cannot edit resource", "Save the ERF and try again.", QMessageBox.Ok, self).exec_()
            return

        for index in self.ui.tableView.selectionModel().selectedRows(0):
            item = self.model.itemFromIndex(index)
            resource = item.data()
            editor = self.parent().openResourceEditor(self._filepath, resource.resref.get(), resource.restype, resource.data, noExternal=True)
            if editor is not None:
                editor.savedFile.connect(self.resourceSaved)

    def refresh(self) -> None:
        with open(self._filepath, 'rb') as file:
            data = file.read()
            self.load(self._filepath, self._resref, self._restype, data)

    def selectionChanged(self, selection: QItemSelection) -> None:
        if len(selection.indexes()) == 0:
            self.ui.extractButton.setEnabled(False)
            self.ui.openButton.setEnabled(False)
            self.ui.unloadButton.setEnabled(False)
        else:
            self.ui.extractButton.setEnabled(True)
            self.ui.openButton.setEnabled(True)
            self.ui.unloadButton.setEnabled(True)

    def resourceSaved(self, filepath: str, resref: str, restype: ResourceType, data: bytes) -> None:
        if filepath != self._filepath:
            return

        for index in self.ui.tableView.selectionModel().selectedRows(0):
            item = self.model.itemFromIndex(index)
            if item.data().resref == resref and item.data().restype == restype:
                item.data().data = data
