import os
from typing import Optional, List, Union, Tuple

from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QMimeData
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QWidget, QShortcut, QTableView

from gui.widgets.settings.installations import GlobalSettings
from pykotor.common.misc import ResRef
from pykotor.resource.formats.erf import read_erf, ERF, ERFType, write_erf, ERFResource
from pykotor.resource.formats.rim import read_rim, write_rim, RIM
from pykotor.resource.type import ResourceType

from data.installation import HTInstallation
from gui.editor import Editor
from utils.window import openResourceEditor


class ERFEditor(Editor):
    def __init__(self, parent: Optional[QWidget], installation: Optional[HTInstallation] = None):
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
        self.ui.extractButton.clicked.connect(self.extractSelected)
        self.ui.loadButton.clicked.connect(self.selectFilesToAdd)
        self.ui.unloadButton.clicked.connect(self.removeSelected)
        self.ui.openButton.clicked.connect(self.openSelected)
        self.ui.refreshButton.clicked.connect(self.refresh)
        self.ui.tableView.resourceDropped.connect(self.addResources)
        self.ui.tableView.doubleClicked.connect(self.openSelected)

        QShortcut("Del", self).activated.connect(self.removeSelected)

    def load(self, filepath: str, resref: str, restype: ResourceType, data: bytes) -> None:
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
            QMessageBox(QMessageBox.Critical, "Unable to load file", "The file specified is not a MOD/ERF type file.",
                        ..., self).show()

    def build(self) -> Tuple[bytes, bytes]:
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

        return data, b''

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
            file.write(data[0])

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
        for index in reversed([index for index in self.ui.tableView.selectedIndexes() if index.column() == 0]):
            item = self.model.itemFromIndex(index)
            self.model.removeRow(item.row())

    def addResources(self, filepaths: List[str]) -> None:
        for filepath in filepaths:
            try:
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
            except Exception as e:
                QMessageBox(QMessageBox.Critical, "Failed to add resource", "Could not add resource at {}.".format(filepath)).exec_()

    def selectFilesToAdd(self) -> None:
        filepaths = QFileDialog.getOpenFileNames(self, "Load files into module")[:-1][0]
        self.addResources(filepaths)

    def openSelected(self) -> None:
        if self._filepath is None:
            QMessageBox(QMessageBox.Critical, "Cannot edit resource", "Save the ERF and try again.", QMessageBox.Ok, self).exec_()
            return

        for index in self.ui.tableView.selectionModel().selectedRows(0):
            item = self.model.itemFromIndex(index)
            resource = item.data()

            if resource.restype in [ResourceType.ERF, ResourceType.MOD, ResourceType.RIM]:
                QMessageBox(QMessageBox.Warning, "Cannot open nested ERF files",
                            "Editing ERF or RIM files nested within each other is no supported.",
                            QMessageBox.Ok, self).exec_()
                continue

            tempPath, editor = openResourceEditor(self._filepath, resource.resref.get(), resource.restype, resource.data,
                                                  self._installation, self)
            editor.savedFile.connect(self.resourceSaved)

    def refresh(self) -> None:
        with open(self._filepath, 'rb') as file:
            data = file.read()
            self.load(self._filepath, self._resref, self._restype, data)

    def selectionChanged(self) -> None:
        if len(self.ui.tableView.selectedIndexes()) == 0:
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
            links = []
            for url in event.mimeData().urls():
                links.append(str(url.toLocalFile()))
            self.resourceDropped.emit(links)
        else:
            event.ignore()

    def startDrag(self, actions: Union[QtCore.Qt.DropActions, QtCore.Qt.DropAction]) -> None:
        tempDir = GlobalSettings().extractPath

        if not tempDir or not os.path.exists(tempDir) or not os.path.isdir(tempDir):
            return

        urls = []
        for index in [index for index in self.selectedIndexes() if index.column() == 0]:
            resource = self.model().itemData(index)[QtCore.Qt.UserRole+1]
            filepath = "{}/{}.{}".format(tempDir, resource.resref.get(), resource.restype.extension)
            with open(filepath, 'wb') as file:
                file.write(resource.data)
            urls.append(QtCore.QUrl.fromLocalFile(filepath))

        mimeData = QMimeData()
        mimeData.setUrls(urls)
        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)
        drag.exec_(QtCore.Qt.CopyAction, QtCore.Qt.CopyAction)
