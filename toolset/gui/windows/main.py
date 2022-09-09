from __future__ import annotations

import json
import os
import traceback
from contextlib import suppress
from datetime import datetime, timedelta
from distutils.version import StrictVersion
from pathlib import Path
from typing import Optional, List

import requests
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import QStandardItem, QIcon, QPixmap, QCloseEvent
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QTreeView

from globalsettings import GlobalSettings
from gui.dialogs.settings import SettingsDialog
from pykotor.tools import model

from pykotor.common.module import Module
from pykotor.common.stream import BinaryReader
from pykotor.extract.file import FileResource, ResourceIdentifier
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.mdl import read_mdl, write_mdl
from pykotor.resource.formats.tpc import read_tpc, write_tpc
from pykotor.resource.type import ResourceType

from config import PROGRAM_VERSION, UPDATE_INFO_LINK
from data.installation import HTInstallation
from gui.editors.dlg import DLGEditor
from gui.editors.erf import ERFEditor
from gui.editors.gff import GFFEditor
from gui.editors.nss import NSSEditor
from gui.editors.ssf import SSFEditor
from gui.editors.txt import TXTEditor
from gui.editors.utc import UTCEditor
from gui.editors.utd import UTDEditor
from gui.editors.ute import UTEEditor
from gui.editors.uti import UTIEditor
from gui.editors.utm import UTMEditor
from gui.editors.utp import UTPEditor
from gui.editors.uts import UTSEditor
from gui.editors.utt import UTTEditor
from gui.editors.utw import UTWEditor
from gui.dialogs.about import About
from gui.dialogs.asyncloader import AsyncLoader, AsyncBatchLoader
from gui.windows.help import HelpWindow
from gui.dialogs.search import FileSearcher, FileResults
from gui.dialogs.clone_module import CloneModuleDialog
from gui.windows.indoor_builder import IndoorMapBuilder
from gui.windows.module_designer import ModuleDesigner
from utils.misc import openLink
from utils.window import openResourceEditor, addWindow
from gui.widgets.main_widgets import ResourceList

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class ToolWindow(QMainWindow):
    moduleFilesUpdated = QtCore.pyqtSignal(object, object)

    overrideFilesUpdate = QtCore.pyqtSignal(object, object)

    GFF_TYPES = [ResourceType.GFF, ResourceType.UTC, ResourceType.UTP, ResourceType.UTD, ResourceType.UTI,
                 ResourceType.UTM, ResourceType.UTE, ResourceType.UTT, ResourceType.UTW, ResourceType.UTS,
                 ResourceType.DLG, ResourceType.GUI, ResourceType.ARE, ResourceType.IFO, ResourceType.GIT,
                 ResourceType.JRL, ResourceType.ITP]

    def __init__(self):
        super().__init__()

        self.dogObserver = None
        self.dogHandler = FolderObserver(self)
        self.active: Optional[HTInstallation] = None
        self.settings: GlobalSettings = GlobalSettings()
        self.installations = {}

        from toolset.uic.windows.main import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupSignals()

        self.ui.coreWidget.hideSection()
        self.ui.coreWidget.hideReloadButton()
        self.setWindowIcon(QIcon(QPixmap(":/images/icons/sith.png")))
        self.reloadSettings()

        firstTime = self.settings.firstTime
        if firstTime:
            self.settings.firstTime = False

            # Create a directory used for dumping temp files
            with suppress(Exception):
                extractPath = os.path.realpath('../..') + "/temp"
                os.mkdir(extractPath)
                self.settings.extractPath = extractPath

        self.checkForUpdates(True)

    def _setupSignals(self) -> None:
        self.ui.gameCombo.currentIndexChanged.connect(self.changeActiveInstallation)

        self.moduleFilesUpdated.connect(self.onModuleFileUpdated)
        self.overrideFilesUpdate.connect(self.onOverrideFileUpdated)

        self.ui.coreWidget.requestExtractResource.connect(self.onExtractResources)
        self.ui.coreWidget.requestOpenResource.connect(self.onOpenResources)

        self.ui.modulesWidget.sectionChanged.connect(self.onModuleChanged)
        self.ui.modulesWidget.requestReload.connect(self.onModuleReload)
        self.ui.modulesWidget.requestRefresh.connect(self.onModuleRefresh)
        self.ui.modulesWidget.requestExtractResource.connect(self.onExtractResources)
        self.ui.modulesWidget.requestOpenResource.connect(self.onOpenResources)

        self.ui.overrideWidget.sectionChanged.connect(self.onOverrideChanged)
        self.ui.overrideWidget.requestReload.connect(self.onOverrideReload)
        self.ui.overrideWidget.requestRefresh.connect(self.onOverrideRefresh)
        self.ui.overrideWidget.requestExtractResource.connect(self.onExtractResources)
        self.ui.overrideWidget.requestOpenResource.connect(self.onOpenResources)

        self.ui.texturesWidget.sectionChanged.connect(self.onTexturesChanged)
        self.ui.texturesWidget.requestOpenResource.connect(self.onOpenResources)

        self.ui.extractButton.clicked.connect(lambda: self.onExtractResources(self.getActiveResourceWidget().selectedResources()))
        self.ui.openButton.clicked.connect(lambda: self.onOpenResources(self.getActiveResourceWidget().selectedResources()))

        self.ui.openAction.triggered.connect(self.openFromFile)
        self.ui.actionSettings.triggered.connect(self.openSettingsDialog)
        self.ui.actionEditModule.triggered.connect(self.openModuleEditor)
        self.ui.actionExit.triggered.connect(self.close)
        self.ui.actionNewDLG.triggered.connect(lambda: DLGEditor(self, self.active).show())
        self.ui.actionNewNSS.triggered.connect(lambda: NSSEditor(self, self.active).show())
        self.ui.actionNewUTC.triggered.connect(lambda: UTCEditor(self, self.active).show())
        self.ui.actionNewUTP.triggered.connect(lambda: UTPEditor(self, self.active).show())
        self.ui.actionNewUTD.triggered.connect(lambda: UTDEditor(self, self.active).show())
        self.ui.actionNewUTI.triggered.connect(lambda: UTIEditor(self, self.active).show())
        self.ui.actionNewUTT.triggered.connect(lambda: UTTEditor(self, self.active).show())
        self.ui.actionNewUTM.triggered.connect(lambda: UTMEditor(self, self.active).show())
        self.ui.actionNewUTW.triggered.connect(lambda: UTWEditor(self, self.active).show())
        self.ui.actionNewUTE.triggered.connect(lambda: UTEEditor(self, self.active).show())
        self.ui.actionNewUTS.triggered.connect(lambda: UTSEditor(self, self.active).show())
        self.ui.actionNewGFF.triggered.connect(lambda: GFFEditor(self, self.active).show())
        self.ui.actionNewERF.triggered.connect(lambda: ERFEditor(self, self.active).show())
        self.ui.actionNewTXT.triggered.connect(lambda: TXTEditor(self, self.active).show())
        self.ui.actionNewSSF.triggered.connect(lambda: SSFEditor(self, self.active).show())
        self.ui.actionCloneModule.triggered.connect(lambda: CloneModuleDialog(self, self.active, self.installations).exec_())

        self.ui.actionEditTLK.triggered.connect(self.openActiveTalktable)
        self.ui.actionEditJRL.triggered.connect(self.openActiveJournal)
        self.ui.actionFileSearch.triggered.connect(self.openFileSearchDialog)
        self.ui.actionIndoorMapBuilder.triggered.connect(self.openIndoorMapBuilder)

        self.ui.actionInstructions.triggered.connect(self.openInstructionsWindow)
        self.ui.actionHelpUpdates.triggered.connect(self.checkForUpdates)
        self.ui.actionHelpAbout.triggered.connect(self.openAboutDialog)
        self.ui.actionDiscordDeadlyStream.triggered.connect(lambda: openLink("https://discord.com/invite/bRWyshn"))
        self.ui.actionDiscordKotOR.triggered.connect(lambda: openLink("http://discord.gg/kotor"))
        self.ui.actionDiscordHolocronToolset.triggered.connect(lambda: openLink("https://discord.gg/3ME278a9tQ"))

    # region Signal callbacks
    def onModuleFileUpdated(self, changedFile: str, eventType: str) -> None:
        if eventType == "deleted":
            self.onModuleRefresh()
        else:
            # Reload the resource cache for the module
            self.active.reload_module(changedFile)
            # If the current module opened is the file which was updated, then we
            # should refresh the ui.
            if self.ui.modulesWidget.currentSection() == changedFile:
                self.onModuleReload(changedFile)

    def onModuleChanged(self, newModuleFile: str) -> None:
        self.onModuleReload(newModuleFile)

    def onModuleReload(self, moduleFile: str) -> None:
        resources = self.active.module_resources(moduleFile)

        # Some users may choose to have their RIM files for the same module merged into a single option for the
        # dropdown menu.
        if self.settings.joinRIMsTogether and moduleFile.endswith(".rim"):
            resources += self.active.module_resources(moduleFile.replace(".rim", "_s.rim"))

        self.active.reload_module(moduleFile)
        self.ui.modulesWidget.setResources(resources)

    def onModuleRefresh(self) -> None:
        self.refreshModuleList()

    def onOverrideFileUpdated(self, changedDir: str, eventType: str) -> None:
        if eventType == "deleted":
            self.onOverrideRefresh()
        else:
            self.onOverrideReload(changedDir)

    def onOverrideChanged(self, newDirectory: str) -> None:
        self.ui.overrideWidget.setResources(self.active.override_resources(newDirectory))

    def onOverrideReload(self, directory) -> None:
        self.active.reload_override(directory)
        self.ui.overrideWidget.setResources(self.active.override_resources(directory))

    def onOverrideRefresh(self) -> None:
        self.refreshOverrideList()

    def onTexturesChanged(self, newTexturepack: str) -> None:
        self.ui.texturesWidget.setResources(self.active.texturepack_resources(newTexturepack))

    def onExtractResources(self, resources: List[FileResource]) -> None:
        if len(resources) == 1:
            # Player saves resource with a specific name
            default = resources[0].resname() + "." + resources[0].restype().extension
            filepath = QFileDialog.getSaveFileName(self, "Save resource", default)[0]

            if filepath:
                loader = AsyncBatchLoader(self, "Extracting Resources", [], "Failed to Extract Resources")
                loader.addTask(lambda: self._extractResource(resources[0], filepath, loader))
                loader.exec_()

        elif len(resources) >= 1:
            # Player saves resources with original name to a specific directory
            folderpath = QFileDialog.getExistingDirectory(self, "Select directory to extract to")
            if folderpath:
                loader = AsyncBatchLoader(self, "Extracting Resources", [], "Failed to Extract Resources")

                for resource in resources:
                    filename = resource.resname() + "." + resource.restype().extension
                    filepath = folderpath + "/" + filename
                    loader.addTask(lambda a=resource, b=filepath: self._extractResource(a, b, loader))

                loader.exec_()

    def onOpenResources(self, resources: List[FileResource], useSpecializedEditor: bool = None) -> None:
        for resource in resources:
            filepath, editor = openResourceEditor(resource.filepath(), resource.resname(), resource.restype(),
                                                  resource.data(reload=True), self.active, self,
                                                  gffSpecialized=useSpecializedEditor)
    # endregion

    # region Events
    def closeEvent(self, e: QCloseEvent) -> None:
        self.ui.texturesWidget.doTerminations()

    def dropEvent(self, e: QtGui.QDropEvent) -> None:
        if e.mimeData().hasUrls():
            for url in e.mimeData().urls():
                filepath = url.toLocalFile()
                with open(filepath, 'rb') as file:
                    resref, restype = ResourceIdentifier.from_path(filepath)
                    data = file.read()
                    openResourceEditor(filepath, resref, restype, data, self.active, self)

    def dragEnterEvent(self, e: QtGui.QDragEnterEvent) -> None:
        if e.mimeData().hasUrls():
            for url in e.mimeData().urls():
                with suppress(Exception):
                    # Call from_path method as it will throw an error if the file extension is not recognized.
                    ResourceIdentifier.from_path(url.toLocalFile())
                    e.accept()
    # endregion

    # region Menu Bar
    def updateMenus(self) -> None:
        version = "x" if self.active is None else "2" if self.active.tsl else "1"

        dialogIconPath = ":/images/icons/k{}/dialog.png".format(version)
        self.ui.actionNewDLG.setIcon(QIcon(QPixmap(dialogIconPath)))
        self.ui.actionNewDLG.setEnabled(self.active is not None)

        scriptIconPath = ":/images/icons/k{}/script.png".format(version)
        self.ui.actionNewNSS.setIcon(QIcon(QPixmap(scriptIconPath)))
        self.ui.actionNewNSS.setEnabled(self.active is not None)

        creatureIconPath = ":/images/icons/k{}/creature.png".format(version)
        self.ui.actionNewUTC.setIcon(QIcon(QPixmap(creatureIconPath)))
        self.ui.actionNewUTC.setEnabled(self.active is not None)

        placeableIconPath = ":/images/icons/k{}/placeable.png".format(version)
        self.ui.actionNewUTP.setIcon(QIcon(QPixmap(placeableIconPath)))
        self.ui.actionNewUTP.setEnabled(self.active is not None)

        doorIconPath = ":/images/icons/k{}/door.png".format(version)
        self.ui.actionNewUTD.setIcon(QIcon(QPixmap(doorIconPath)))
        self.ui.actionNewUTD.setEnabled(self.active is not None)

        itemIconPath = ":/images/icons/k{}/item.png".format(version)
        self.ui.actionNewUTI.setIcon(QIcon(QPixmap(itemIconPath)))
        self.ui.actionNewUTI.setEnabled(self.active is not None)

        soundIconPath = ":/images/icons/k{}/sound.png".format(version)
        self.ui.actionNewUTS.setIcon(QIcon(QPixmap(soundIconPath)))
        self.ui.actionNewUTS.setEnabled(self.active is not None)

        triggerIconPath = ":/images/icons/k{}/trigger.png".format(version)
        self.ui.actionNewUTT.setIcon(QIcon(QPixmap(triggerIconPath)))
        self.ui.actionNewUTT.setEnabled(self.active is not None)

        merchantIconPath = ":/images/icons/k{}/merchant.png".format(version)
        self.ui.actionNewUTM.setIcon(QIcon(QPixmap(merchantIconPath)))
        self.ui.actionNewUTM.setEnabled(self.active is not None)

        waypointIconPath = ":/images/icons/k{}/waypoint.png".format(version)
        self.ui.actionNewUTW.setIcon(QIcon(QPixmap(waypointIconPath)))
        self.ui.actionNewUTW.setEnabled(self.active is not None)

        encounterIconPath = ":/images/icons/k{}/encounter.png".format(version)
        self.ui.actionNewUTE.setIcon(QIcon(QPixmap(encounterIconPath)))
        self.ui.actionNewUTE.setEnabled(self.active is not None)

        self.ui.actionEditTLK.setEnabled(self.active is not None)
        self.ui.actionEditJRL.setEnabled(self.active is not None)
        self.ui.actionFileSearch.setEnabled(self.active is not None)
        self.ui.actionEditModule.setEnabled(self.active is not None)
        self.ui.actionIndoorMapBuilder.setEnabled(self.active is not None)

        self.ui.actionCloneModule.setEnabled(self.active is not None)

    def openModuleEditor(self) -> None:
        filepath = QFileDialog.getOpenFileName(self, "Select a module", self.active.module_path())[0]
        if filepath:
            module = Module(Module.get_root(filepath), self.active)
            designer = ModuleDesigner(None, self.active, module)
            addWindow(designer)

    def openSettingsDialog(self) -> None:
        """
        Opens the Settings dialog and refresh installation combo list if changes.
        """
        if SettingsDialog(self).exec_():
            self.reloadSettings()

    def openActiveTalktable(self) -> None:
        """
        Opens the talktable for the active (currently selected) installation. If there is no active information, show
        a message box instead.
        """
        filepath = self.active.path() + "dialog.tlk"
        data = BinaryReader.load_file(filepath)
        openResourceEditor(filepath, "dialog", ResourceType.TLK, data, self.active, self)

    def openActiveJournal(self) -> None:
        self.active.reload_override("")
        res = self.active.resource("global", ResourceType.JRL, [SearchLocation.OVERRIDE, SearchLocation.CHITIN])
        openResourceEditor(res.filepath, "global", ResourceType.JRL, res.data, self.active, self)

    def openFileSearchDialog(self) -> None:
        """
        Opens the FileSearcher dialog. If a search is conducted then a FileResults dialog displays the results
        where the user can then select a resource and the selected resouce will then be shown in the main window.
        """
        searchDialog = FileSearcher(self, self.installations)
        if searchDialog.exec_():
            resultsDialog = FileResults(self, searchDialog.results, searchDialog.installation)
            if resultsDialog.exec_() and resultsDialog.selection:
                selection = resultsDialog.selection

                # Open the installation of the resource
                index = 0
                for i, installation in enumerate(self.installations.values()):
                    if installation is searchDialog.installation:
                        index = i + 1
                self.changeActiveInstallation(index)

                # Open relevant tab then select resource in the tree
                if self.active.module_path() in selection.filepath():
                    self.ui.resourceTabs.setCurrentIndex(1)
                    self.selectResource(self.ui.modulesWidget, selection)
                elif self.active.override_path() in selection.filepath():
                    self.ui.resourceTabs.setCurrentIndex(2)
                    self.selectResource(self.ui.overrideWidget, selection)
                elif selection.filepath().endswith(".bif"):
                    self.selectResource(self.ui.coreWidget, selection)

    def openIndoorMapBuilder(self) -> None:
        IndoorMapBuilder(self, self.active).show()

    def openInstructionsWindow(self) -> None:
        """
        Opens the instructions window.
        """
        window = HelpWindow(None)
        addWindow(window)

    def openAboutDialog(self) -> None:
        """
        Opens the about dialog.
        """
        About(self).exec_()

    def checkForUpdates(self, silent: bool = False) -> None:
        """
        Scans for any updates and opens a dialog with a message based on the scan result.

        Args:
            silent: If true, only shows popup if an update is available.
        """
        try:
            req = requests.get(UPDATE_INFO_LINK)
            data = json.loads(req.text)

            latestVersion = data['latestVersion']
            downloadLink = data['downloadLink']

            if StrictVersion(latestVersion) > StrictVersion(PROGRAM_VERSION):
                QMessageBox(QMessageBox.Information, "New version is available.",
                            "New version available for <a href='{}'>download</a>.".format(downloadLink),
                            QMessageBox.Ok, self).exec_()
            else:
                if not silent:
                    QMessageBox(QMessageBox.Information, "Version is up to date",
                                "You are running the latest version (" + latestVersion + ").", QMessageBox.Ok, self).exec_()
        except Exception:
            if not silent:
                QMessageBox(QMessageBox.Information, "Unable to fetch latest version.",
                            "Check if you are connected to the internet.", QMessageBox.Ok, self).exec_()
    # endregion

    # region Other
    def reloadSettings(self) -> None:
        self.reloadInstallations()

    def getActiveResourceWidget(self) -> ResourceList:
        if self.ui.resourceTabs.currentWidget() is self.ui.coreTab:
            return self.ui.coreWidget
        elif self.ui.resourceTabs.currentWidget() is self.ui.modulesTab:
            return self.ui.modulesWidget
        elif self.ui.resourceTabs.currentWidget() is self.ui.overrideTab:
            return self.ui.overrideWidget
        elif self.ui.resourceTabs.currentWidget() is self.ui.texturesTab:
            return self.ui.texturesWidget

    def refreshModuleList(self, reload: bool = True) -> None:
        """
        Refreshes the list of modules in the modulesCombo combobox.
        """
        # Do nothing if no installation is currently loaded
        if self.active is None:
            return

        # If specified the user can forcibly reload the resource list for every module
        if reload:
            self.active.load_modules()

        areaNames = self.active.module_names()
        sortedKeys = sorted(areaNames, key=lambda key: areaNames.get(key).lower())

        modules = []
        for module in sortedKeys:
            # Some users may choose to have their RIM files for the same module merged into a single option for the
            # dropdown menu.
            if self.settings.joinRIMsTogether and module.endswith("_s.rim"):
                continue

            item = QStandardItem("{} [{}]".format(areaNames[module], module))
            item.setData(module, QtCore.Qt.UserRole)

            # Some users may choose to have items representing RIM files to have grey text.
            if self.settings.greyRIMText and module.endswith(".rim"):
                item.setForeground(self.palette().shadow())

            modules.append(item)

        self.ui.modulesWidget.setSections(modules)

    def refreshOverrideList(self) -> None:
        """
        Refreshes the list of override directories in the overrideFolderCombo combobox.
        """
        self.active.load_override()

        sections = []
        for directory in self.active.override_list():
            section = QStandardItem(directory if directory != "" else "[Root]")
            section.setData(directory, QtCore.Qt.UserRole)
            sections.append(section)
        self.ui.overrideWidget.setSections(sections)

    def refreshTexturePackList(self):
        self.active.load_textures()

        sections = []
        for texturepack in self.active.texturepacks_list():
            section = QStandardItem(texturepack)
            section.setData(texturepack, QtCore.Qt.UserRole)
            sections.append(section)

        self.ui.texturesWidget.setSections(sections)

    def changeModule(self, module: str) -> None:
        # Some users may choose to merge their RIM files under one option in the Modules tab; if this is the case we
        # need to account for this.
        if self.settings.joinRIMsTogether and module.endswith("_s.rim"):
            module = module.replace("_s.rim", ".rim")

        self.ui.modulesWidget.changeSection(module)

    def selectResource(self, tree: QTreeView, resource: FileResource) -> None:
        if tree == self.ui.coreWidget:
            self.ui.resourceTabs.setCurrentWidget(self.ui.coreTab)
            self.ui.coreWidget.setResourceSelection(resource)
        elif tree == self.ui.modulesWidget:
            self.ui.resourceTabs.setCurrentWidget(self.ui.modulesTab)
            self.ui.modulesWidget.setResourceSelection(resource)
            filename = os.path.basename(resource.filepath())
            self.changeModule(filename)
        elif tree == self.ui.overrideWidget:
            self.ui.resourceTabs.setCurrentIndex(self.ui.overrideTab)
            self.ui.overrideWidget.setResourceSelection(resource)
            subfolder = ""
            for folder in self.active.override_list():
                if folder in resource.filepath() and len(subfolder) < len(folder):
                    subfolder = folder
            self.changeOverrideFolder(subfolder)

    def reloadInstallations(self) -> None:
        """
        Refresh the list of installations available in the combobox.
        """
        self.ui.gameCombo.clear()
        self.ui.gameCombo.addItem("[None]")

        for installation in self.settings.installations().values():
            self.ui.gameCombo.addItem(installation.name)

    def changeActiveInstallation(self, index: int) -> None:
        """
        Changes the active installation selected. If an installation does not have a path yet set, the user is prompted
        to select a directory for it. If the installation path remains unset then the active installation also remains
        unselected.

        Args:
            index: Index of the installation in the installationCombo combobox.
        """
        self.ui.gameCombo.setCurrentIndex(index)

        self.ui.coreWidget.setResources([])
        self.ui.modulesWidget.setSections([])
        self.ui.modulesWidget.setResources([])
        self.ui.overrideWidget.setSections([])
        self.ui.overrideWidget.setResources([])

        self.ui.resourceTabs.setEnabled(False)
        self.ui.sidebar.setEnabled(False)
        self.active = None
        self.updateMenus()

        if self.dogObserver is not None:
            self.dogObserver.stop()

        if index <= 0:
            return

        self.ui.resourceTabs.setEnabled(True)
        self.ui.sidebar.setEnabled(True)

        name = self.ui.gameCombo.itemText(index)
        path = self.settings.installations()[name].path
        tsl = self.settings.installations()[name].tsl

        # If the user has not set a path for the particular game yet, ask them too.
        if path == "":
            path = QFileDialog.getExistingDirectory(self, "Select the game directory for {}".format(name))

        # If the user still has not set a path, then return them to the [None] option.
        if path == "":
            self.ui.gameCombo.setCurrentIndex(0)
        else:
            # If the installation had not already been loaded previously this session, load it now
            if name not in self.installations:
                task = lambda: HTInstallation(path, name, tsl, self)
                loader = AsyncLoader(self, "Loading Installation", task, "Failed to load installation")

                if loader.exec_():
                    self.settings.installations()[name].path = path
                    self.installations[name] = loader.value

            # If the data has been successfully been loaded, dump the data into the models
            if name in self.installations:
                self.active = self.installations[name]

                self.ui.coreWidget.setResources(self.active.chitin_resources())

                self.refreshModuleList(False)
                self.refreshOverrideList()
                self.refreshTexturePackList()
                self.ui.texturesWidget.setInstallation(self.active)

                self.updateMenus()
                self.dogObserver = Observer()
                self.dogObserver.schedule(self.dogHandler, self.active.path(), recursive=True)
                self.dogObserver.start()
            else:
                self.ui.gameCombo.setCurrentIndex(0)

    def _extractResource(self, resource: FileResource, filepath: str, loader: AsyncBatchLoader) -> None:
        try:
            data = resource.data()
            folderpath = os.path.dirname(filepath) + "/"
            filename = os.path.basename(filepath)

            decompileTPC = self.ui.tpcDecompileCheckbox.isChecked()
            extractTXI = self.ui.tpcTxiCheckbox.isChecked()
            decompileMDL = self.ui.mdlDecompileCheckbox.isChecked()
            extractTexturesMDL = self.ui.mdlTexturesCheckbox.isChecked()

            manipulateTPC = decompileTPC or extractTXI
            manipulateMDL = decompileMDL or extractTexturesMDL

            if resource.restype() == ResourceType.MDX and decompileMDL:
                # Ignore extracting MDX files if decompiling MDLs
                return

            if resource.restype() == ResourceType.TPC and manipulateTPC:
                tpc = read_tpc(data)

                if extractTXI:
                    txi_filename = filename.replace(".tpc", ".txi")
                    with open(folderpath + txi_filename, 'wb') as file:
                        file.write(tpc.txi.encode('ascii'))

                if decompileTPC:
                    data = bytearray()
                    write_tpc(tpc, data, ResourceType.TGA)
                    filepath = filepath.replace(".tpc", ".tga")

            if resource.restype() == ResourceType.MDL and manipulateMDL:
                if decompileMDL:
                    mdxData = self.active.resource(resource.resname(), ResourceType.MDX).data
                    mdl = read_mdl(data, 0, 0, mdxData, 0, 0)

                    data = bytearray()
                    write_mdl(mdl, data, ResourceType.MDL_ASCII)
                    filepath = filepath.replace(".mdl", ".ascii.mdl")

                if extractTexturesMDL:
                    try:
                        for texture in model.list_textures(data):
                            try:
                                tpc = self.active.texture(texture)
                                if extractTXI:
                                    with open(folderpath + texture + ".txi", 'wb') as file:
                                        file.write(tpc.txi.encode('ascii'))
                                file_format = ResourceType.TGA if decompileTPC else ResourceType.TPC
                                extension = "tga" if file_format == ResourceType.TGA else "tpc"
                                write_tpc(tpc, "{}{}.{}".format(folderpath, texture, extension), file_format)
                            except Exception as e:
                                loader.errors.append(ValueError("Could not find or extract tpc: " + texture))
                    except:
                        loader.errors.append(ValueError("Could not determine textures used in model: " + resource.resname()))

            with open(filepath, 'wb') as file:
                file.write(data)
        except Exception as e:
            traceback.print_exc()
            raise Exception("Failed to extract resource: " + resource.resname() + "." + resource.restype().extension)

    def openFromFile(self) -> None:
        filepaths = QFileDialog.getOpenFileNames(self, "Select files to open")[:-1][0]

        for filepath in filepaths:
            try:
                resref, restype_ext = os.path.basename(filepath).split('.', 1)
                restype = ResourceType.from_extension(restype_ext)
                with open(filepath, 'rb') as file:
                    data = file.read()
                openResourceEditor(filepath, resref, restype, data, self.active, self)
            except ValueError as e:
                QMessageBox(QMessageBox.Critical, "Failed to open file", str(e)).exec_()
    # endregion


class FolderObserver(FileSystemEventHandler):
    def __init__(self, window: ToolWindow):
        self.window = window
        self.lastModified = datetime.now()

    def on_any_event(self, event):
        if datetime.now() - self.lastModified < timedelta(seconds=1):
            return
        else:
            self.lastModified = datetime.now()

        modulePath = str(Path(self.window.active.module_path()))
        overridePath = str(Path(self.window.active.override_path()))
        modifiedPath = str(Path(event.src_path.replace("\\", "/")))

        isDir = Path(modifiedPath).is_dir()

        if modulePath in modifiedPath and not isDir:
            moduleFile = os.path.basename(modifiedPath)
            self.window.moduleFilesUpdated.emit(moduleFile, event.event_type)
        elif overridePath in modifiedPath and not isDir:
            overrideDir = os.path.dirname(modifiedPath).replace(overridePath, "")
            if overrideDir.startswith("\\") or overrideDir.startswith("//"):
                overrideDir = overrideDir[1:]
            self.window.overrideFilesUpdate.emit(overrideDir, event.event_type)


