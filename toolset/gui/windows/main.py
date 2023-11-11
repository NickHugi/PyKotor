from __future__ import annotations

try:
    from packaging.version import Version as StrictVersion
except ImportError:
    try:
        from distutils.version import StrictVersion
    except ImportError:
        try:
            from setuptools.version import StrictVersion
        except ImportError as e3:
            msg = "Could not import StrictVersion from any known library"
            raise ImportError(msg) from e3

import json
import traceback
from contextlib import suppress
from datetime import datetime, timedelta, timezone
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, ClassVar

import requests
from config import PROGRAM_VERSION, UPDATE_INFO_LINK
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import QCloseEvent, QIcon, QPixmap, QStandardItem
from PyQt5.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QTreeView
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from pykotor.common.stream import BinaryReader
from pykotor.extract.file import FileResource, ResourceIdentifier
from pykotor.extract.installation import SearchLocation
from pykotor.helpers.error_handling import assert_with_variable_trace
from pykotor.helpers.path import Path, PurePath
from pykotor.resource.formats.mdl import read_mdl, write_mdl
from pykotor.resource.formats.tpc import read_tpc, write_tpc
from pykotor.resource.type import ResourceType
from pykotor.tools import model
from pykotor.tools.misc import is_rim_file
from pykotor.tools.path import CaseAwarePath
from toolset.data.installation import HTInstallation
from toolset.gui.dialogs.about import About
from toolset.gui.dialogs.asyncloader import AsyncBatchLoader, AsyncLoader
from toolset.gui.dialogs.clone_module import CloneModuleDialog
from toolset.gui.dialogs.search import FileResults, FileSearcher
from toolset.gui.dialogs.settings import SettingsDialog
from toolset.gui.editors.dlg import DLGEditor
from toolset.gui.editors.erf import ERFEditor
from toolset.gui.editors.gff import GFFEditor
from toolset.gui.editors.nss import NSSEditor
from toolset.gui.editors.ssf import SSFEditor
from toolset.gui.editors.txt import TXTEditor
from toolset.gui.editors.utc import UTCEditor
from toolset.gui.editors.utd import UTDEditor
from toolset.gui.editors.ute import UTEEditor
from toolset.gui.editors.uti import UTIEditor
from toolset.gui.editors.utm import UTMEditor
from toolset.gui.editors.utp import UTPEditor
from toolset.gui.editors.uts import UTSEditor
from toolset.gui.editors.utt import UTTEditor
from toolset.gui.editors.utw import UTWEditor
from toolset.gui.widgets.settings.misc import GlobalSettings
from toolset.gui.windows.help import HelpWindow
from toolset.gui.windows.indoor_builder import IndoorMapBuilder
from toolset.gui.windows.module_designer import ModuleDesigner
from toolset.utils.misc import openLink
from toolset.utils.window import addWindow, openResourceEditor

if TYPE_CHECKING:
    import os

    from pykotor.resource.formats.tpc.tpc_data import TPC
    from toolset.gui.widgets.main_widgets import ResourceList


class ToolWindow(QMainWindow):
    moduleFilesUpdated = QtCore.pyqtSignal(object, object)

    overrideFilesUpdate = QtCore.pyqtSignal(object, object)

    GFF_TYPES: ClassVar[list[ResourceType]] = [
        ResourceType.GFF,
        ResourceType.UTC,
        ResourceType.UTP,
        ResourceType.UTD,
        ResourceType.UTI,
        ResourceType.UTM,
        ResourceType.UTE,
        ResourceType.UTT,
        ResourceType.UTW,
        ResourceType.UTS,
        ResourceType.DLG,
        ResourceType.GUI,
        ResourceType.ARE,
        ResourceType.IFO,
        ResourceType.GIT,
        ResourceType.JRL,
        ResourceType.ITP,
    ]

    def __init__(self):
        super().__init__()

        self.dogObserver = None
        self.dogHandler = FolderObserver(self)
        self.active: HTInstallation | None = None
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
                self.settings.extractPath = str(Path(str(TemporaryDirectory().name)))

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

        self.ui.actionModuleDesigner.triggered.connect(self.openModuleDesigner)
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
        if self.settings.joinRIMsTogether and is_rim_file(moduleFile):
            resources += self.active.module_resources(PurePath(moduleFile).with_suffix("_s.rim").name)

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

    def onOverrideReload(self, directory: str) -> None:
        self.active.load_override(directory)
        self.ui.overrideWidget.setResources(self.active.override_resources(directory))

    def onOverrideRefresh(self) -> None:
        self.refreshOverrideList()

    def onTexturesChanged(self, newTexturepack: str) -> None:
        self.ui.texturesWidget.setResources(self.active.texturepack_resources(newTexturepack))

    def onExtractResources(self, resources: list[FileResource]) -> None:
        """Extracts the resources selected in the main UI window.

        Args:
        ----
            resources: list[FileResource]: List of selected resources to extract
        Processing Logic:
            - If single resource selected, prompt user to save with default or custom name
            - If multiple resources selected, prompt user for extract directory and extract each with original name.
        """
        if len(resources) == 1:
            # Player saves resource with a specific name
            default = f"{resources[0].resname()}.{resources[0].restype().extension}"
            filepath: str = QFileDialog.getSaveFileName(self, "Save resource", default)[0]

            if filepath:
                loader = AsyncBatchLoader(self, "Extracting Resources", [], "Failed to Extract Resources")
                loader.addTask(lambda: self._extractResource(resources[0], filepath, loader))
                loader.exec_()

        elif len(resources) >= 1:
            # Player saves resources with original name to a specific directory
            folderpath: str = QFileDialog.getExistingDirectory(self, "Select directory to extract to")
            if folderpath:
                loader = AsyncBatchLoader(self, "Extracting Resources", [], "Failed to Extract Resources")

                for resource in resources:
                    filename = f"{resource.resname()}.{resource.restype().extension}"
                    filepath = str(Path(folderpath, filename))
                    loader.addTask(lambda a=resource, b=filepath: self._extractResource(a, b, loader))

                loader.exec_()

    def onOpenResources(self, resources: list[FileResource], useSpecializedEditor: bool | None = None) -> None:
        for resource in resources:
            _filepath, _editor = openResourceEditor(
                resource.filepath(),
                resource.resname(),
                resource.restype(),
                resource.data(reload=True),
                self.active,
                self,
                gff_specialized=useSpecializedEditor,
            )

    # endregion

    # region Events
    def closeEvent(self, e: QCloseEvent) -> None:
        self.ui.texturesWidget.doTerminations()

    def dropEvent(self, e: QtGui.QDropEvent) -> None:
        if e.mimeData().hasUrls():
            for url in e.mimeData().urls():
                filepath = url.toLocalFile()
                r_filepath = Path(filepath)
                with r_filepath.open("rb") as file:
                    resref, restype = ResourceIdentifier.from_path(filepath)
                    data = file.read()
                    openResourceEditor(r_filepath, resref, restype, data, self.active, self)

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

        dialogIconPath = f":/images/icons/k{version}/dialog.png"
        self.ui.actionNewDLG.setIcon(QIcon(QPixmap(dialogIconPath)))
        self.ui.actionNewDLG.setEnabled(self.active is not None)

        scriptIconPath = f":/images/icons/k{version}/script.png"
        self.ui.actionNewNSS.setIcon(QIcon(QPixmap(scriptIconPath)))
        self.ui.actionNewNSS.setEnabled(self.active is not None)

        creatureIconPath = f":/images/icons/k{version}/creature.png"
        self.ui.actionNewUTC.setIcon(QIcon(QPixmap(creatureIconPath)))
        self.ui.actionNewUTC.setEnabled(self.active is not None)

        placeableIconPath = f":/images/icons/k{version}/placeable.png"
        self.ui.actionNewUTP.setIcon(QIcon(QPixmap(placeableIconPath)))
        self.ui.actionNewUTP.setEnabled(self.active is not None)

        doorIconPath = f":/images/icons/k{version}/door.png"
        self.ui.actionNewUTD.setIcon(QIcon(QPixmap(doorIconPath)))
        self.ui.actionNewUTD.setEnabled(self.active is not None)

        itemIconPath = f":/images/icons/k{version}/item.png"
        self.ui.actionNewUTI.setIcon(QIcon(QPixmap(itemIconPath)))
        self.ui.actionNewUTI.setEnabled(self.active is not None)

        soundIconPath = f":/images/icons/k{version}/sound.png"
        self.ui.actionNewUTS.setIcon(QIcon(QPixmap(soundIconPath)))
        self.ui.actionNewUTS.setEnabled(self.active is not None)

        triggerIconPath = f":/images/icons/k{version}/trigger.png"
        self.ui.actionNewUTT.setIcon(QIcon(QPixmap(triggerIconPath)))
        self.ui.actionNewUTT.setEnabled(self.active is not None)

        merchantIconPath = f":/images/icons/k{version}/merchant.png"
        self.ui.actionNewUTM.setIcon(QIcon(QPixmap(merchantIconPath)))
        self.ui.actionNewUTM.setEnabled(self.active is not None)

        waypointIconPath = f":/images/icons/k{version}/waypoint.png"
        self.ui.actionNewUTW.setIcon(QIcon(QPixmap(waypointIconPath)))
        self.ui.actionNewUTW.setEnabled(self.active is not None)

        encounterIconPath = f":/images/icons/k{version}/encounter.png"
        self.ui.actionNewUTE.setIcon(QIcon(QPixmap(encounterIconPath)))
        self.ui.actionNewUTE.setEnabled(self.active is not None)

        self.ui.actionEditTLK.setEnabled(self.active is not None)
        self.ui.actionEditJRL.setEnabled(self.active is not None)
        self.ui.actionFileSearch.setEnabled(self.active is not None)
        self.ui.actionModuleDesigner.setEnabled(self.active is not None)
        self.ui.actionIndoorMapBuilder.setEnabled(self.active is not None)

        self.ui.actionCloneModule.setEnabled(self.active is not None)

    def openModuleDesigner(self) -> None:
        designer = ModuleDesigner(None, self.active)
        addWindow(designer)

    def openSettingsDialog(self) -> None:
        """Opens the Settings dialog and refresh installation combo list if changes."""
        dialog = SettingsDialog(self)
        if dialog.exec_() and dialog.installationEdited:
            self.reloadSettings()

    def openActiveTalktable(self) -> None:
        """Opens the talktable for the active (currently selected) installation. If there is no active information, show
        a message box instead.
        """
        filepath = CaseAwarePath(self.active.path(), "dialog.tlk")
        data = BinaryReader.load_file(filepath)
        openResourceEditor(filepath, "dialog", ResourceType.TLK, data, self.active, self)

    def openActiveJournal(self) -> None:
        self.active.load_override(".")
        res = self.active.resource("global", ResourceType.JRL, [SearchLocation.OVERRIDE, SearchLocation.CHITIN])
        openResourceEditor(res.filepath, "global", ResourceType.JRL, res.data, self.active, self)

    def openFileSearchDialog(self) -> None:
        """Opens the FileSearcher dialog. If a search is conducted then a FileResults dialog displays the results
        where the user can then select a resource and the selected resouce will then be shown in the main window.
        """
        searchDialog = FileSearcher(self, self.installations)
        if searchDialog.exec_():
            resultsDialog = FileResults(self, searchDialog.results, searchDialog.installation)
            if resultsDialog.exec_() and resultsDialog.selection:
                selection = resultsDialog.selection

                # Open relevant tab then select resource in the tree
                if self.active.module_path().is_relative_to(selection.filepath()):
                    self.ui.resourceTabs.setCurrentIndex(1)
                    self.selectResource(self.ui.modulesWidget, selection)
                elif self.active.override_path().is_relative_to(selection.filepath()):
                    self.ui.resourceTabs.setCurrentIndex(2)
                    self.selectResource(self.ui.overrideWidget, selection)
                elif selection.filepath().endswith(".bif"):
                    self.selectResource(self.ui.coreWidget, selection)

    def openIndoorMapBuilder(self) -> None:
        IndoorMapBuilder(self, self.active).show()

    def openInstructionsWindow(self) -> None:
        """Opens the instructions window."""
        window = HelpWindow(None)
        addWindow(window)

    def openAboutDialog(self) -> None:
        """Opens the about dialog."""
        About(self).exec_()

    def checkForUpdates(self, silent: bool = False) -> None:
        """Scans for any updates and opens a dialog with a message based on the scan result.

        Args:
        ----
            silent: If true, only shows popup if an update is available.
        """
        try:
            req = requests.get(UPDATE_INFO_LINK, timeout=15)
            data = json.loads(req.text)

            latestVersion = data["latestVersion"]
            downloadLink = data["downloadLink"]

            if StrictVersion(latestVersion) > StrictVersion(PROGRAM_VERSION):
                QMessageBox(
                    QMessageBox.Information,
                    "New version is available.",
                    f"New version available for <a href='{downloadLink}'>download</a>.",
                    QMessageBox.Ok,
                    self,
                ).exec_()
            elif not silent:
                QMessageBox(
                    QMessageBox.Information,
                    "Version is up to date",
                    f"You are running the latest version ({latestVersion}).",
                    QMessageBox.Ok,
                    self,
                ).exec_()
        except Exception:
            if not silent:
                QMessageBox(
                    QMessageBox.Information,
                    "Unable to fetch latest version.",
                    "Check if you are connected to the internet.",
                    QMessageBox.Ok,
                    self,
                ).exec_()

    # endregion

    # region Other
    def reloadSettings(self) -> None:
        self.reloadInstallations()

    def getActiveResourceWidget(self) -> ResourceList | None:
        if self.ui.resourceTabs.currentWidget() is self.ui.coreTab:
            return self.ui.coreWidget
        if self.ui.resourceTabs.currentWidget() is self.ui.modulesTab:
            return self.ui.modulesWidget
        if self.ui.resourceTabs.currentWidget() is self.ui.overrideTab:
            return self.ui.overrideWidget
        if self.ui.resourceTabs.currentWidget() is self.ui.texturesTab:
            return self.ui.texturesWidget
        return None

    def refreshModuleList(self, reload: bool = True) -> None:
        """Refreshes the list of modules in the modulesCombo combobox."""
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

            item = QStandardItem(f"{areaNames[module]} [{module}]")
            item.setData(module, QtCore.Qt.UserRole)  # type: ignore[reportGeneralTypeIssues]

            # Some users may choose to have items representing RIM files to have grey text.
            if self.settings.greyRIMText and module.endswith(".rim"):
                item.setForeground(self.palette().shadow())

            modules.append(item)

        self.ui.modulesWidget.setSections(modules)

    def refreshOverrideList(self, reload=True) -> None:
        """Refreshes the list of override directories in the overrideFolderCombo combobox."""
        if reload:
            self.active.load_override()

        sections = []
        for directory in self.active.override_list():
            section = QStandardItem(directory if directory != "" else "[Root]")
            section.setData(directory, QtCore.Qt.UserRole)  # type: ignore[reportGeneralTypeIssues]
            sections.append(section)
        self.ui.overrideWidget.setSections(sections)

    def refreshTexturePackList(self, reload=True):
        if reload:
            self.active.load_textures()

        sections = []
        for texturepack in self.active.texturepacks_list():
            section = QStandardItem(texturepack)
            section.setData(texturepack, QtCore.Qt.UserRole)  # type: ignore[reportGeneralTypeIssues]
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
            filename = resource.filepath().name
            self.changeModule(filename)
            self.ui.modulesWidget.setResourceSelection(resource)
        elif tree == self.ui.overrideWidget:
            self.ui.resourceTabs.setCurrentWidget(self.ui.overrideTab)
            self.ui.overrideWidget.setResourceSelection(resource)
            subfolder = ""
            for folder in self.active.override_list():
                if Path(folder).is_relative_to(resource.filepath()) and len(subfolder) < len(folder):
                    subfolder = folder
            self.changeOverrideFolder(subfolder)

    def changeOverrideFolder(self, subfolder: str) -> None:
        self.ui.overrideWidget.changeSection(subfolder)

    def reloadInstallations(self) -> None:
        """Refresh the list of installations available in the combobox."""
        self.ui.gameCombo.clear()
        self.ui.gameCombo.addItem("[None]")

        for installation in self.settings.installations().values():
            self.ui.gameCombo.addItem(installation.name)

    def changeActiveInstallation(self, index: int) -> None:
        """Changes the active installation selected. If an installation does not have a path yet set, the user is prompted
        to select a directory for it. If the installation path remains unset then the active installation also remains
        unselected.

        Args:
        ----
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
        path = self.settings.installations()[name].path.strip()
        tsl = self.settings.installations()[name].tsl

        # If the user has not set a path for the particular game yet, ask them too.
        if not path:
            path = QFileDialog.getExistingDirectory(self, f"Select the game directory for {name}")

        # If the user still has not set a path, then return them to the [None] option.
        if not path:
            self.ui.gameCombo.setCurrentIndex(0)
        else:
            # If the installation had not already been loaded previously this session, load it now
            if name not in self.installations:

                def task():
                    return HTInstallation(path, name, tsl, self)

                loader = AsyncLoader(self, "Loading Installation", task, "Failed to load installation")

                if loader.exec_():
                    self.settings.installations()[name].path = path
                    self.installations[name] = loader.value

            # If the data has been successfully been loaded, dump the data into the models
            if name in self.installations:
                self.active = self.installations[name]

                assert_with_variable_trace(isinstance(self.active, HTInstallation))
                assert isinstance(self.active, HTInstallation)  # noqa: S101

                self.ui.coreWidget.setResources(self.active.chitin_resources())

                print("Loading installation resources into UI...")
                self.refreshModuleList(reload=True)  # TODO: Modules/Override/Textures are loaded twice when HT is first initialized.
                self.refreshOverrideList(reload=True)
                self.refreshTexturePackList(reload=True)
                self.ui.texturesWidget.setInstallation(self.active)

                print("Updating menus...")
                self.updateMenus()
                self.dogObserver = Observer()
                self.dogObserver.schedule(self.dogHandler, self.active.path(), recursive=True)
                self.dogObserver.start()
            else:
                self.ui.gameCombo.setCurrentIndex(0)

    def _extractResource(self, resource: FileResource, filepath: os.PathLike | str, loader: AsyncBatchLoader) -> None:
        """Extracts a resource file from a FileResource object.

        Args:
        ----
            resource: {FileResource}: The FileResource object
            filepath: {os.PathLike | str}: Path to save the extracted file
            loader: {AsyncBatchLoader}: Loader for async operations
        Returns:
            None: No return value

        {Processes the resource based on its type:
        - Extracts Txi data from TPC files
        - Decompiles TPC and MDL files
        - Extracts textures from MDL files
        - Writes extracted data to the file path}
        """
        r_filepath = filepath if isinstance(filepath, Path) else Path(filepath)
        folderpath = r_filepath.parent

        try:
            data = resource.data()

            if resource.restype() == ResourceType.MDX and self.ui.mdlDecompileCheckbox.isChecked():
                # Ignore extracting MDX files if decompiling MDLs
                return

            if resource.restype() == ResourceType.TPC:
                tpc = read_tpc(data)

                if self.ui.tpcTxiCheckbox.isChecked():
                    self._extractTxi(tpc, r_filepath)

                if self.ui.tpcDecompileCheckbox.isChecked():
                    data = self._decompileTpc(tpc)
                    r_filepath = r_filepath.with_suffix(".tga")

            if resource.restype() == ResourceType.MDL:
                if self.ui.mdlDecompileCheckbox.isChecked():
                    data = self._decompileMdl(resource, data)
                    r_filepath = r_filepath.with_suffix(".ascii.mdl")

                if self.ui.mdlTexturesCheckbox.isChecked():
                    self._extractMdlTextures(resource, folderpath, loader, data)

            with r_filepath.open("wb") as file:
                file.write(data)

        except Exception as e:
            traceback.print_exc()
            msg = f"Failed to extract resource: {resource.resname()}.{resource.restype().extension}"
            raise RuntimeError(msg) from e

    def _extractTxi(self, tpc: TPC, filepath: Path):
        with filepath.with_suffix(".txi").open("wb") as file:
            file.write(tpc.txi.encode("ascii"))

    def _decompileTpc(self, tpc):
        data = bytearray()
        write_tpc(tpc, data, ResourceType.TGA)
        return data

    def _decompileMdl(self, resource, data):
        mdxData = self.active.resource(resource.resname(), ResourceType.MDX).data
        mdl = read_mdl(data, 0, 0, mdxData, 0, 0)

        data = bytearray()
        write_mdl(mdl, data, ResourceType.MDL_ASCII)
        return data

    def _extractMdlTextures(self, resource, folderpath: Path, loader: AsyncBatchLoader, data: bytes):
        try:
            for texture in model.list_textures(data):
                try:
                    tpc = self.active.texture(texture)
                    if self.ui.tpcTxiCheckbox.isChecked():
                        self._extractTxi(tpc, folderpath.joinpath(f"{texture}.txi"))
                    file_format = ResourceType.TGA if self.ui.tpcDecompileCheckbox.isChecked() else ResourceType.TPC
                    extension = "tga" if file_format == ResourceType.TGA else "tpc"
                    write_tpc(tpc, folderpath.joinpath(f"{texture}.{extension}"), file_format)
                except Exception:
                    loader.errors.append(ValueError(f"Could not find or extract tpc: '{texture}'"))
        except Exception:
            loader.errors.append(ValueError(f"Could not determine textures used in model: '{resource.resname()}'"))

    def openFromFile(self) -> None:
        filepaths = QFileDialog.getOpenFileNames(self, "Select files to open")[:-1][0]

        for filepath in filepaths:
            r_filepath = Path(filepath)
            try:
                resref, restype_ext = r_filepath.name.rsplit(".", 1)
                restype = ResourceType.from_extension(restype_ext)
                with r_filepath.open("rb") as file:
                    data = file.read()
                openResourceEditor(filepath, resref, restype, data, self.active, self)
            except ValueError as e:
                QMessageBox(QMessageBox.Critical, "Failed to open file", str(e)).exec_()

    # endregion


class FolderObserver(FileSystemEventHandler):
    def __init__(self, window: ToolWindow):
        self.window = window
        self.lastModified = datetime.now(tz=timezone.utc).astimezone()

    def on_any_event(self, event):
        rightnow = datetime.now(tz=timezone.utc).astimezone()
        if rightnow - self.lastModified < timedelta(seconds=1):
            return

        self.lastModified = rightnow

        modulePath = Path(self.window.active.module_path())
        overridePath = Path(self.window.active.override_path())
        modifiedPath = Path(event.src_path)

        isDir = Path(modifiedPath).is_dir()

        if modulePath.is_relative_to(modifiedPath) and not isDir:
            moduleFile = modifiedPath.parent
            self.window.moduleFilesUpdated.emit(str(moduleFile), event.event_type)
        elif overridePath.is_relative_to(modifiedPath) and not isDir:
            overrideDir = str(overridePath.relative_to(modifiedPath.parent))
            if overrideDir.startswith(("\\", "//")):
                overrideDir = overrideDir[1:]
            self.window.overrideFilesUpdate.emit(overrideDir, event.event_type)
