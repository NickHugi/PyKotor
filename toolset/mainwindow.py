from __future__ import annotations

import json
import os
import subprocess
from distutils.version import Version, StrictVersion
from typing import Optional, List

import requests
from PyQt5 import QtCore
from PyQt5.QtCore import QSettings, QSortFilterProxyModel, QModelIndex
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon, QPixmap
from PyQt5.QtWidgets import QMainWindow, QDialog, QProgressBar, QVBoxLayout, QFileDialog, QTreeView, \
    QLabel, QWidget, QMessageBox
from pykotor.extract.file import FileResource
from pykotor.extract.installation import Installation
from pykotor.resource.formats.mdl import load_mdl, write_mdl
from pykotor.resource.formats.tpc import load_tpc, write_tpc
from pykotor.resource.type import ResourceType, FileFormat

import mainwindow_ui
from editors.editor import Editor
from editors.erf.erf_editor import ERFEditor
from editors.gff.gff_editor import GFFEditor
from editors.ssf.sff_editor import SSFEditor
from editors.tlk.tlk_editor import TLKEditor
from editors.tpc.tpc_editor import TPCEditor
from editors.twoda.twoda_editor import TwoDAEditor
from editors.txt.txt_editor import TXTEditor
from misc.about import About
from misc.settings import Settings

import resources_rc


PROGRAM_VERSION = "1.1.0"


class ToolWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = mainwindow_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon(QPixmap(":/icons/sith.png")))

        self.active: Optional[Installation] = None
        self.settings = QSettings('cortisol', 'holocrontoolset')

        firstTime = self.settings.value('firstTime', True, bool)
        if firstTime:
            self.settings.setValue('firstTime', False)
            self.settings.setValue('games', {
                'KotOR': {'path': "", 'tsl': False},
                'TSL': {'path': "", 'tsl': True}
            })

            self.settings.setValue('gffEditor', '')
            self.settings.setValue('2daEditor', '')
            self.settings.setValue('dlgEditor', '')
            self.settings.setValue('tlkEditor', '')

            try:
                os.mkdir(os.path.realpath('.') + "/ext")
                self.settings.setValue('tempDir', os.path.realpath('.') + "/ext")
            except:
                self.settings.setValue('tempDir', "")

        self.installations = {}
        self.reloadInstallations()

        self.ui.resourceTabs.setEnabled(False)
        self.ui.sidebar.setEnabled(False)
        self.ui.gameCombo.currentIndexChanged.connect(self.changeActiveInstallation)
        self.ui.extractButton.clicked.connect(self.extractFromSelected)
        self.ui.openButton.clicked.connect(self.openFromSelected)

        self.ui.coreSearchEdit.textEdited.connect(self.filterDataModel)

        self.ui.moduleSearchEdit.textEdited.connect(self.filterDataModel)
        self.ui.moduleReloadButton.clicked.connect(self.reloadModule)
        self.ui.moduleRefreshButton.clicked.connect(self.refreshModuleList)
        self.ui.modulesCombo.currentTextChanged.connect(self.changeModule)

        self.ui.overrideSearchEdit.textEdited.connect(self.filterDataModel)
        self.ui.overrideRefreshButton.clicked.connect(self.refreshOverrideList)
        self.ui.overrideReloadButton.clicked.connect(self.reloadOverride)
        self.ui.overrideFolderCombo.currentTextChanged.connect(self.changeOverrideFolder)

        self.ui.openAction.triggered.connect(self.openFromFile)
        self.ui.actionSettings.triggered.connect(self.openSettingsDialog)
        self.ui.actionExit.triggered.connect(self.close)
        self.ui.actionNewGFF.triggered.connect(lambda: GFFEditor(self, self.active).show())
        self.ui.actionNewERF.triggered.connect(lambda: ERFEditor(self, self.active).show())
        self.ui.actionNewTXT.triggered.connect(lambda: TXTEditor(self, self.active).show())
        self.ui.actionNewSSF.triggered.connect(lambda: SSFEditor(self, self.active).show())
        self.ui.actionEditTLK.triggered.connect(self.openActiveTalktable)
        self.ui.actionHelpUpdates.triggered.connect(self.openUpdatesDialog)
        self.ui.actionHelpAbout.triggered.connect(self.openAboutDialog)

        self.coreModel = ResourceModel()
        self.ui.coreTree.setModel(self.coreModel.proxyModel())
        self.ui.coreTree.header().resizeSection(1, 40)

        self.modulesModel = ResourceModel()
        self.ui.modulesTree.setModel(self.modulesModel.proxyModel())
        self.ui.modulesTree.header().resizeSection(1, 40)

        self.overrideModel = ResourceModel()
        self.ui.overrideTree.setModel(self.overrideModel.proxyModel())
        self.ui.overrideTree.header().resizeSection(1, 40)

        self._clearModels()

    def openSettingsDialog(self) -> None:
        """
        Opens the Settings dialog and refresh installation combo list if changes.
        """
        if Settings().exec_():
            self.reloadInstallations()

    def openAboutDialog(self) -> None:
        """
        Opens the about dialog.
        """
        About(self, PROGRAM_VERSION).exec_()

    def openUpdatesDialog(self) -> None:
        """
        Scans for any updates and opens a dialog with a message based on the scan result.
        """
        req = requests.get("https://pastebin.com/raw/tUJCGgrX")
        data = json.loads(req.text)

        latestVersion = data['latestVersion']
        downloadLink = data['downloadLink']

        if StrictVersion(latestVersion) > StrictVersion(PROGRAM_VERSION):
            QMessageBox(QMessageBox.Information, "New version is available.",
                        "New version available for <a href='{}'>download</a>.".format(downloadLink),
                        QMessageBox.Ok, self).exec_()
        else:
            QMessageBox(QMessageBox.Information, "Version is up to date",
                        "You are running the latest version (" + latestVersion + ").", QMessageBox.Ok, self).exec_()

    def openActiveTalktable(self) -> None:
        """
        Opens the talktable for the active (currently selected) installation. If there is no active information, show
        a message box instead.
        """
        if self.active:
            filepath = self.active._path + "dialog.tlk"
            with open(filepath, 'rb') as file:
                data = file.read()
            self.openResourceEditor(filepath, "dialog", ResourceType.TLK, data)
        else:
            QMessageBox(QMessageBox.Critical, "Could not open TLK file", "Must have a game selected first.",
                        QMessageBox.Ok, self).exec_()

    def _clearModels(self) -> None:
        """
        Clears all data models for the different tabs.
        """
        self.ui.modulesCombo.clear()
        self.ui.modulesCombo.addItem("[None]")

        self.ui.overrideFolderCombo.clear()
        self.ui.overrideFolderCombo.addItem("[Root]")

        self.coreModel.clear()
        self.modulesModel.clear()
        self.overrideModel.clear()

    def reloadInstallations(self) -> None:
        """
        Refresh the list of installations available in the combobox.
        """
        self.ui.gameCombo.clear()
        self.ui.gameCombo.addItem("[None]")

        for name, data in self.settings.value('games', {}).items():
            self.ui.gameCombo.addItem(name)

    def changeActiveInstallation(self, index: int) -> None:
        """
        Changes the active installation selected. If an installation does not have a path yet set, the user is prompted
        to select a directory for it. If the installation path remains unset then the active installation also remains
        unselected.

        Args:
            index: Index of the installation in the installationCombo combobox.
        """
        self.ui.gameCombo.setCurrentIndex(index)

        self._clearModels()
        self.ui.resourceTabs.setEnabled(False)
        self.ui.sidebar.setEnabled(False)
        self.active = None

        if index <= 0:
            return

        self.ui.resourceTabs.setEnabled(True)
        self.ui.sidebar.setEnabled(True)

        name = self.ui.gameCombo.itemText(index)
        path = self.settings.value('games')[name]['path']

        # If the user has not set a path for the particular game yet, ask them too.
        if path == "":
            path = QFileDialog.getExistingDirectory(self, "Select the game directory for {}".format(name))

        # If the user still has not set a path, then return them to the [None] option.
        if path == "":
            self.ui.gameCombo.setCurrentIndex(0)
        else:
            # If the installation had not already been loaded previously this session, load it now
            if name not in self.installations:
                dialog = InstallationLoaderDialog(self, path, name)
                if dialog.exec_():
                    games = self.settings.value('games')
                    games[name]['path'] = path
                    self.settings.setValue('games', games)
                    self.installations[name] = dialog.installation

            # If the data has been successfully been loaded, dump the data into the models
            if name in self.installations:
                self.active = self.installations[name]

                for resource in self.active.chitin_resources():
                    self.coreModel.addResource(resource)
                for resource in self.active.texturepack_resources("swpc_tex_tpa.erf"):
                    self.coreModel.addResource(resource)
                for directory in self.active.override_list():
                    self.refreshOverrideList()
                for module in self.active.modules_list():
                    self.ui.modulesCombo.addItem(module)
            else:
                self.ui.gameCombo.setCurrentIndex(0)

    def changeModule(self, module: str) -> None:
        """
        Updates the items in the module tree to the module specified.
        """
        self.modulesModel.clear()

        if module == "" or module == "[None]":
            return

        for resource in self.active.module_resources(module):
            self.modulesModel.addResource(resource)

    def reloadModule(self) -> None:
        """
        Reloads the files stored in the currently selected module and updates the data model.

        Returns:

        """
        self.active.load_modules()

        self.modulesModel.clear()
        module = self.ui.modulesCombo.currentText()
        for resource in self.active.module_resources(module):
            self.modulesModel.addResource(resource)

    def refreshModuleList(self) -> None:
        """
        Refreshes the list of modules in the modulesCombo combobox.
        """
        self.active.load_modules()

        self.ui.modulesCombo.clear()
        self.ui.modulesCombo.addItem("[None]")
        for module in self.active.modules_list():
            self.ui.modulesCombo.addItem(module)

    def changeOverrideFolder(self, folder: str) -> None:
        self.overrideModel.clear()

        if self.active is None:
            return

        folder = "" if folder == "[Root]" else folder

        for resource in self.active.override_resources(folder):
            self.overrideModel.addResource(resource)

    def refreshOverrideList(self) -> None:
        """
        Refreshes the list of override directories in the overrideFolderCombo combobox.
        """
        self.active.load_override()

        self.ui.overrideFolderCombo.clear()
        self.ui.overrideFolderCombo.addItem("[Root]")
        for directory in self.active.override_list():
            if directory == "":
                continue
            self.ui.overrideFolderCombo.addItem(directory)

    def reloadOverride(self) -> None:
        """
        Reloads the files stored in the active installation's override folder and updates the respective data model.
        """
        self.active.load_override()

        folder = self.ui.overrideFolderCombo.currentText()
        folder = "" if folder == "[Root]" else folder

        self.overrideModel.clear()
        for resource in self.active.override_resources(folder):
            self.overrideModel.addResource(resource)

    def currentDataTree(self) -> QTreeView:
        """
        Returns the QTreeView object that is currently being shown on the resourceTabs.
        """
        if self.ui.resourceTabs.currentIndex() == 0:
            return self.ui.coreTree
        if self.ui.resourceTabs.currentIndex() == 1:
            return self.ui.modulesTree
        if self.ui.resourceTabs.currentIndex() == 2:
            return self.ui.overrideTree

    def currentDataModel(self) -> ResourceModel:
        """
        Returns the QTreeView object that is currently being shown on the resourceTabs.
        """
        if self.ui.resourceTabs.currentIndex() == 0:
            return self.coreModel
        if self.ui.resourceTabs.currentIndex() == 1:
            return self.modulesModel
        if self.ui.resourceTabs.currentIndex() == 2:
            return self.overrideModel

    def filterDataModel(self, text: str) -> None:
        """
        Filters the data model that is currently shown on the resourceTabs.

        Args:
            text: The text to filter through.
        """
        self.currentDataTree().model().setFilterFixedString(text)

    def extractFromSelected(self) -> None:
        """
        Extracts the resources from the items selected in the tree of the currently open resourceTabs tab.
        """

        resources = self.currentDataModel().resourceFromIndexes(self.currentDataTree().selectedIndexes())

        if len(resources) == 1:
            # Player saves resource with a specific name
            default = resources[0].resref() + "." + resources[0].restype().extension
            filepath = QFileDialog.getSaveFileName(self, "Save resource", default)[0]
            if filepath:
                resref = os.path.basename(filepath)
                resref = resref.split('.')[0] if '.' in resref else resref
                resources = [FileResource(resref, resources[0].restype(), resources[0].size(), resources[0].offset(), resources[0].filepath())]
                folderpath = os.path.dirname(filepath) + "/"
                ResourceExtractorDialog(self, folderpath, resources, self.active, self).exec_()

        elif len(resources) >= 1:
            # Player saves resources with original name to a specific directory
            folderpath = QFileDialog.getExistingDirectory(self, "Select directory to extract to")
            if folderpath:
                ResourceExtractorDialog(self, folderpath + "/", resources, self.active, self).exec_()

    def openFromSelected(self) -> None:
        """
        Opens the resources from the items selected in the tree of the currently open resourceTabs tab.
        """
        resources = self.currentDataModel().resourceFromIndexes(self.currentDataTree().selectedIndexes())
        for resource in resources:
            self.openResourceEditor(resource.filepath(), resource.resref(), resource.restype(), resource.data())

    def openFromFile(self) -> None:
        filepath, filter = QFileDialog.getOpenFileName(self, "Open a file")

        if filepath != "":
            resref, restype_ext = os.path.basename(filepath).split('.', 1)
            restype = ResourceType.from_extension(restype_ext)
            with open(filepath, 'rb') as file:
                data = file.read()
            self.openResourceEditor(filepath, resref, restype, data)

    def openResourceEditor(self, filepath: str, resref: str, restype: ResourceType, data: bytes, *, noExternal=False) -> Optional[Editor]:
        """
        Opens an editor for the specified resource. If the user settings have the editor set to inbuilt it will return
        the editor, otherwise it returns None

        Args:
            filepath: Path to the resource.
            resref: The ResRef.
            restype: The resource type.
            data: The resource data.
            noExternal: If True, internal editors will only be used, regardless of user settings.

        Returns:
            The inbuilt editor window or None.
        """
        editor = None
        external = None

        if restype in [ResourceType.TwoDA]:
            if self.settings.value('2daEditor'):
                external = self.settings.value('2daEditor')
            else:
                editor = TwoDAEditor(self, self.active)

        if restype in [ResourceType.SSF]:
            editor = SSFEditor(self, self.active)

        if restype in [ResourceType.TLK]:
            if self.settings.value('tlkEditor') and not noExternal:
                external = self.settings.value('tlkEditor')
            else:
                editor = TLKEditor(self, self.active)

        if restype in [ResourceType.TPC, ResourceType.TGA]:
            editor = TPCEditor(self, self.active)

        if restype in [ResourceType.TXT, ResourceType.TXI, ResourceType.LYT, ResourceType.VIS]:
            if self.settings.value('txtEditor') and not noExternal:
                external = self.settings.value('txtEditor')
            else:
                editor = TXTEditor(self)

        if restype in [ResourceType.NSS]:
            if self.settings.value('nssEditor') and not noExternal:
                external = self.settings.value('nssEditor')
            else:
                editor = TXTEditor(self, self.active)

        if restype in [ResourceType.DLG]:
            if self.settings.value('dlgEditor') and not noExternal:
                external = self.settings.value('dlgEditor')
            else:
                editor = GFFEditor(self, self.active)

        if restype in [ResourceType.GFF, ResourceType.UTC, ResourceType.UTP, ResourceType.UTD, ResourceType.UTI,
                       ResourceType.UTM, ResourceType.UTE, ResourceType.UTT, ResourceType.UTW, ResourceType.UTS,
                       ResourceType.GUI, ResourceType.ARE, ResourceType.IFO, ResourceType.GIT, ResourceType.JRL,
                       ResourceType.ITP]:
            if self.settings.value('gffEditor') and not noExternal:
                external = self.settings.value('gffEditor')
            else:
                editor = GFFEditor(self, self.active)

        if restype in [ResourceType.MOD, ResourceType.ERF, ResourceType.RIM]:
            editor = ERFEditor(self, self.active)

        if editor is not None:
            editor.load(filepath, resref, restype, data)
            editor.show()
            return editor
        elif external is not None:
            try:
                if filepath.endswith('.erf') or filepath.endswith('.rim') or filepath.endswith('.mod') or filepath.endswith('.bif'):
                    tempFilepath = "{}/{}.{}".format(self.settings.value('tempDir'), resref, restype.extension)
                    with open(tempFilepath, 'wb') as file:
                        file.write(data)
                    subprocess.Popen([external, tempFilepath])
                else:
                    subprocess.Popen([external, filepath])
            except:
                QMessageBox(QMessageBox.Critical, "Could not open editor", "Double check the file path in settings.",
                            QMessageBox.Ok, self).show()
        else:
            QMessageBox(QMessageBox.Critical, "Failed to open file", "The selected file is not yet supported.",
                        QMessageBox.Ok, self).show()
        return None


class InstallationLoaderDialog(QDialog):
    """
    Popup dialog responsible for loading and returning an installation.
    """
    def __init__(self, parent, path: str, name: str):
        super().__init__(parent)

        self._progressBar = QProgressBar(self)
        self._progressBar.setMinimum(0)
        self._progressBar.setMaximum(0)
        self._progressBar.setTextVisible(False)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self._progressBar)

        self.setWindowTitle("Loading Data...")
        self.setFixedSize(300, 40)

        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)

        self.installation: Optional[Installation] = None

        self.worker = InstallationLoaderWorker(path, name)
        self.worker.loaded.connect(self.loadingCompleted)
        self.worker.failed.connect(self.loadingFailed)
        self.worker.start()

    def loadingCompleted(self, installation):
        self.installation = installation
        self.accept()

    def loadingFailed(self, error):
        QMessageBox(QMessageBox.Critical, "Failed to load game", str(error), QMessageBox.Ok, self.parent()).show()
        self.reject()


class InstallationLoaderWorker(QtCore.QThread):
    loaded = QtCore.pyqtSignal(object)
    failed = QtCore.pyqtSignal(object)

    def __init__(self, path: str, name: str):
        super().__init__()
        self._path: str = path
        self._name: str = name

    def run(self):
        try:
            installation = Installation(self._path, self._name)
            self.loaded.emit(installation)
        except ValueError as e:
            self.failed.emit(e)


class ResourceExtractorDialog(QDialog):
    """
    Popup dialog responsible for extracting a list of resources from the game files.
    """
    def __init__(self, parent: QWidget, folderpath: str, resources: List[FileResource], active: Installation,
                 toolwindow: ToolWindow):
        super().__init__(parent)

        self._progressBar = QProgressBar(self)
        self._progressBar.setMaximum(len(resources))
        self._progressBar.setValue(0)

        filename = resources[self._progressBar.value()].resref() + "." + resources[self._progressBar.value()].restype().extension
        self._progressText = QLabel("Extracting resource: " + filename)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self._progressBar)
        self.layout().addWidget(self._progressText)

        self.setWindowTitle("Extracting Resources...")

        self._folderpath: str = folderpath
        self._resources: List[FileResource] = resources
        self._active: Installation = active
        self._errorLog: str = ""

        decompileTpc = toolwindow.ui.tpcDecompileCheckbox.isChecked()
        decompileMdl = toolwindow.ui.mdlDecompileCheckbox.isChecked()
        extractTexturesMdl = toolwindow.ui.mdlTexturesCheckbox.isChecked()
        extractTxiTpc = toolwindow.ui.tpcTxiCheckbox.isChecked()

        self.worker = ResourceExtractorWorker(self._folderpath, self._resources, self._active,
                                              decompileTpc=decompileTpc, decompileMdl=decompileMdl,
                                              extractTexturesMdl=extractTexturesMdl, extractTxiTpc=extractTxiTpc)
        self.worker.extracted.connect(self.resourceExtracted)
        self.worker.error.connect(self.errorOccurred)
        self.worker.start()

    def errorOccurred(self, error: str) -> None:
        self._errorLog += error + "\n"

    def resourceExtracted(self, resource):
        progress = self._progressBar.value() + 1
        self._progressBar.setValue(progress)

        if self._progressBar.value() == len(self._resources):
            if self._errorLog != "":
                msgbox = QMessageBox()
                msgbox.setIcon(QMessageBox.Warning)
                msgbox.setWindowTitle("The following errors occurred.")
                msgbox.setText(self._errorLog)
                msgbox.exec_()
            self.close()
        else:
            filename = self._resources[progress].resref() + "." + self._resources[progress].restype().extension
            self._progressText = QLabel("Extracting resource: " + filename)


class ResourceExtractorWorker(QtCore.QThread):
    extracted = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(object)

    def __init__(self, folderpath, resources, active, *, decompileTpc, decompileMdl, extractTexturesMdl, extractTxiTpc):
        super().__init__()
        self._folderpath = folderpath
        self._active = active
        self._resources = resources
        self._decompileTpc: bool = decompileTpc
        self._decompileMdl: bool = decompileMdl
        self._extractTexturesMdl: bool = extractTexturesMdl
        self._extractTxiTpc: bool = extractTxiTpc
        self._errorLog: str = ""

    def run(self) -> None:
        for resource in self._resources:
            try:
                self.saveResource(resource, self._folderpath, resource.resref() + "." + resource.restype().extension)
            except Exception as e:
                print(e)
                self.error.emit("Failed to extract resource: " + resource.resref())
            self.extracted.emit(resource)

    def saveResource(self, resource: FileResource, folderpath: str, filename: str) -> None:
        data = resource.data()

        manipulateTPC = self._decompileTpc or self._extractTxiTpc
        manipulateMDL = self._decompileMdl or self._extractTexturesMdl

        if resource.restype() == ResourceType.MDX and self._decompileMdl:
            # Ignore extracting MDX files if decompiling MDLs
            return

        if resource.restype() == ResourceType.TPC and manipulateTPC:
            tpc = load_tpc(data)

            if self._extractTxiTpc:
                txi_filename = filename.replace(".tpc", ".txi")
                with open(folderpath + txi_filename, 'wb') as file:
                    file.write(tpc.txi.encode('ascii'))

            if self._decompileTpc:
                data = bytearray()
                write_tpc(tpc, data, FileFormat.TGA)
                filename = filename.replace(".tpc", ".tga")

        if resource.restype() == ResourceType.MDL and manipulateMDL:
            mdx_data = self._active.resource(resource.restype(), ResourceType.MDX)
            mdl = load_mdl(data, 0, mdx_data)

            if self._decompileMdl:
                data = bytearray()
                write_mdl(mdl, data, FileFormat.ASCII)
                filename = filename.replace(".mdl", ".ascii.mdl")

            if self._extractTexturesMdl:
                for texture in mdl.all_textures():
                    try:
                        tpc = self._active.texture(texture)
                        if self._extractTxiTpc:
                            with open(folderpath + texture + ".txi", 'wb') as file:
                                file.write(tpc.txi.encode('ascii'))
                        file_format = FileFormat.TGA if self._decompileTpc else FileFormat.BINARY
                        extension = "tga" if file_format == FileFormat.TGA else "tpc"
                        write_tpc(tpc, "{}{}.{}".format(folderpath, texture, extension), file_format)
                    except Exception as e:
                        self.error.emit("Could not find or extract tpc: " + texture)

        with open(folderpath + filename, 'wb') as file:
            file.write(data)

    def errorLog(self) -> str:
        return self._errorLog


class ResourceModel(QStandardItemModel):
    """
    A data model used by the different trees (Core, Modules, Override). This class provides an easy way to add resources
    while sorting the into categories.
    """
    def __init__(self):
        super().__init__()
        self._categoryItems = {}
        self._proxyModel = QSortFilterProxyModel()
        self._proxyModel.setSourceModel(self)
        self._proxyModel.setRecursiveFilteringEnabled(True)

    def proxyModel(self) -> QSortFilterProxyModel:
        return self._proxyModel

    def clear(self) -> None:
        super().clear()
        self._categoryItems = {}
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["ResRef", "Type"])

    def _getCategoryItem(self, resourceType: ResourceType) -> QStandardItem:
        if resourceType.category not in self._categoryItems:
            categoryItem = QStandardItem(resourceType.category)
            self._categoryItems[resourceType.category] = categoryItem
            self.appendRow(categoryItem)
        return self._categoryItems[resourceType.category]

    def addResource(self, resource: FileResource) -> None:
        item1 = QStandardItem(resource.resref())
        item1.resource = resource
        item2 = QStandardItem(resource.restype().extension.upper())
        self._getCategoryItem(resource.restype()).appendRow([item1, item2])

    def resourceFromIndexes(self, indexes: List[QModelIndex], proxy: bool = True) -> List[FileResource]:
        items = []
        for index in indexes:
            sourceIndex = self._proxyModel.mapToSource(index) if proxy else index
            items.append(self.itemFromIndex(sourceIndex))
        return self.resourceFromItems(items)

    def resourceFromItems(self, items: List[QStandardItem]) -> List[FileResource]:
        return [item.resource for item in items if hasattr(item, 'resource')]
