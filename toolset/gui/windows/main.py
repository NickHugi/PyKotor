from __future__ import annotations

import json
import tempfile
import traceback
from contextlib import suppress
from datetime import datetime, timedelta
from distutils.version import StrictVersion
from typing import TYPE_CHECKING, ClassVar, List, Optional

import requests
from config import PROGRAM_VERSION, UPDATE_INFO_LINK
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import QCloseEvent, QIcon, QPixmap, QStandardItem
from PyQt5.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QTreeView
from utils.misc import openLink
from utils.window import addWindow, openResourceEditor
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from pykotor.common.stream import BinaryReader
from pykotor.extract.file import FileResource, ResourceIdentifier
from pykotor.extract.installation import SearchLocation
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

if TYPE_CHECKING:
    import os

    from toolset.gui.widgets.main_widgets import ResourceList


class ToolWindow(QMainWindow):
    module_files_updated = QtCore.pyqtSignal(object, object)

    override_files_update = QtCore.pyqtSignal(object, object)

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

        first_time = self.settings.firstTime
        if first_time:
            self.settings.firstTime = False

            # Create a directory used for dumping temp files
            with suppress(Exception):
                extract_path = CaseAwarePath(str(tempfile.TemporaryDirectory()))
                extract_path.mkdir(exist_ok=True, parents=True)
                self.settings.extractPath = extract_path

        self.checkForUpdates(silent=True)

    def _setupSignals(self) -> None:
        self.ui.gameCombo.currentIndexChanged.connect(self.changeActiveInstallation)

        self.module_files_updated.connect(self.onModuleFileUpdated)
        self.override_files_update.connect(self.onOverrideFileUpdated)

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
    def onModuleFileUpdated(self, changed_file: str, event_type: str) -> None:
        if event_type == "deleted":
            self.onModuleRefresh()
        else:
            # Reload the resource cache for the module
            self.active.reload_module(changed_file)
            # If the current module opened is the file which was updated, then we
            # should refresh the ui.
            if self.ui.modulesWidget.currentSection() == changed_file:
                self.onModuleReload(changed_file)

    def onModuleChanged(self, new_module_file: str) -> None:
        self.onModuleReload(new_module_file)

    def onModuleReload(self, module_file: str) -> None:
        resources = self.active.module_resources(module_file)

        # Some users may choose to have their RIM files for the same module merged into a single option for the
        # dropdown menu.
        if self.settings.joinRIMsTogether and is_rim_file(module_file):
            resources += self.active.module_resources(module_file.replace(".rim", "_s.rim"))

        self.active.reload_module(module_file)
        self.ui.modulesWidget.setResources(resources)

    def onModuleRefresh(self) -> None:
        self.refreshModuleList()

    def onOverrideFileUpdated(self, changed_dir: str, event_type: str) -> None:
        if event_type == "deleted":
            self.onOverrideRefresh()
        else:
            self.onOverrideReload(changed_dir)

    def onOverrideChanged(self, new_directory: str) -> None:
        self.ui.overrideWidget.setResources(self.active.override_resources(new_directory))

    def onOverrideReload(self, directory) -> None:
        self.active.reload_override(directory)
        self.ui.overrideWidget.setResources(self.active.override_resources(directory))

    def onOverrideRefresh(self) -> None:
        self.refreshOverrideList()

    def onTexturesChanged(self, new_texture_pack: str) -> None:
        self.ui.texturesWidget.setResources(self.active.texturepack_resources(new_texture_pack))

    def onExtractResources(self, resources: List[FileResource]) -> None:
        if len(resources) == 1:
            # Player saves resource with a specific name
            default = f"{resources[0].resname()}.{resources[0].restype().extension}"
            filepath = QFileDialog.getSaveFileName(self, "Save resource", default)[0]

            if filepath:
                loader = AsyncBatchLoader(self, "Extracting Resources", [], "Failed to Extract Resources")
                loader.addTask(lambda: self._extractResource(resources[0], filepath, loader))
                loader.exec_()

        elif len(resources) >= 1:
            # Player saves resources with original name to a specific directory
            folder_path_str = QFileDialog.getExistingDirectory(self, "Select directory to extract to")
            folder_path = CaseAwarePath(folder_path_str)
            if folder_path_str:
                loader = AsyncBatchLoader(self, "Extracting Resources", [], "Failed to Extract Resources")

                for resource in resources:
                    filename = f"{resource.resname()}.{resource.restype().extension}"
                    filepath = folder_path / filename
                    loader.addTask(lambda a=resource, b=filepath: self._extractResource(a, b, loader))

                loader.exec_()

    def onOpenResources(self, resources: List[FileResource], use_specialized_editor: Optional[bool] = None) -> None:
        for resource in resources:
            filepath, editor = openResourceEditor(
                str(resource.filepath()),
                resource.resname(),
                resource.restype(),
                resource.data(reload=True),
                self.active,
                self,
                gff_specialized=use_specialized_editor,
            )

    # endregion

    # region Events
    def closeEvent(self, e: QCloseEvent) -> None:
        self.ui.texturesWidget.doTerminations()

    def dropEvent(self, e: QtGui.QDropEvent) -> None:
        if e.mimeData().hasUrls():
            for url in e.mimeData().urls():
                filepath = url.toLocalFile()
                with open(filepath, "rb") as file:
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

        dialog_icon_path = f":/images/icons/k{version}/dialog.png"
        self.ui.actionNewDLG.setIcon(QIcon(QPixmap(dialog_icon_path)))
        self.ui.actionNewDLG.setEnabled(self.active is not None)

        script_icon_path = f":/images/icons/k{version}/script.png"
        self.ui.actionNewNSS.setIcon(QIcon(QPixmap(script_icon_path)))
        self.ui.actionNewNSS.setEnabled(self.active is not None)

        creature_icon_path = f":/images/icons/k{version}/creature.png"
        self.ui.actionNewUTC.setIcon(QIcon(QPixmap(creature_icon_path)))
        self.ui.actionNewUTC.setEnabled(self.active is not None)

        placeable_icon_path = f":/images/icons/k{version}/placeable.png"
        self.ui.actionNewUTP.setIcon(QIcon(QPixmap(placeable_icon_path)))
        self.ui.actionNewUTP.setEnabled(self.active is not None)

        door_icon_path = f":/images/icons/k{version}/door.png"
        self.ui.actionNewUTD.setIcon(QIcon(QPixmap(door_icon_path)))
        self.ui.actionNewUTD.setEnabled(self.active is not None)

        item_icon_path = f":/images/icons/k{version}/item.png"
        self.ui.actionNewUTI.setIcon(QIcon(QPixmap(item_icon_path)))
        self.ui.actionNewUTI.setEnabled(self.active is not None)

        sound_icon_path = f":/images/icons/k{version}/sound.png"
        self.ui.actionNewUTS.setIcon(QIcon(QPixmap(sound_icon_path)))
        self.ui.actionNewUTS.setEnabled(self.active is not None)

        trigger_icon_path = f":/images/icons/k{version}/trigger.png"
        self.ui.actionNewUTT.setIcon(QIcon(QPixmap(trigger_icon_path)))
        self.ui.actionNewUTT.setEnabled(self.active is not None)

        merchant_icon_path = f":/images/icons/k{version}/merchant.png"
        self.ui.actionNewUTM.setIcon(QIcon(QPixmap(merchant_icon_path)))
        self.ui.actionNewUTM.setEnabled(self.active is not None)

        waypoint_icon_path = f":/images/icons/k{version}/waypoint.png"
        self.ui.actionNewUTW.setIcon(QIcon(QPixmap(waypoint_icon_path)))
        self.ui.actionNewUTW.setEnabled(self.active is not None)

        encounter_icon_path = f":/images/icons/k{version}/encounter.png"
        self.ui.actionNewUTE.setIcon(QIcon(QPixmap(encounter_icon_path)))
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
        # sourcery skip: use-fstring-for-concatenation
        """Opens the talktable for the active (currently selected) installation. If there is no active information, show
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
        """Opens the FileSearcher dialog. If a search is conducted then a FileResults dialog displays the results
        where the user can then select a resource and the selected resouce will then be shown in the main window.
        """
        search_dialog = FileSearcher(self, self.installations)
        if search_dialog.exec_():
            results_dialog = FileResults(self, search_dialog.results, search_dialog.installation)
            if results_dialog.exec_() and results_dialog.selection:
                selection = results_dialog.selection

                # Open relevant tab then select resource in the tree
                if self.active.module_path() == selection.filepath():
                    self.ui.resourceTabs.setCurrentIndex(1)
                    self.selectResource(self.ui.modulesWidget, selection)
                elif self.active.override_path() == selection.filepath():
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
            req = requests.get(UPDATE_INFO_LINK)
            data = json.loads(req.text)

            latest_version = data["latestVersion"]
            download_link = data["downloadLink"]

            if StrictVersion(latest_version) > StrictVersion(PROGRAM_VERSION):
                QMessageBox(
                    QMessageBox.Information,
                    "New version is available.",
                    f"New version available for <a href='{download_link}'>download</a>.",
                    QMessageBox.Ok,
                    self,
                ).exec_()
            elif not silent:
                QMessageBox(
                    QMessageBox.Information,
                    "Version is up to date",
                    f"You are running the latest version ({latest_version}).",
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

    def getActiveResourceWidget(self) -> ResourceList:
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
            item.setData(module, QtCore.Qt.UserRole)

            # Some users may choose to have items representing RIM files to have grey text.
            if self.settings.greyRIMText and module.endswith(".rim"):
                item.setForeground(self.palette().shadow())

            modules.append(item)

        self.ui.modulesWidget.setSections(modules)

    def refreshOverrideList(self) -> None:
        """Refreshes the list of override directories in the overrideFolderCombo combobox."""
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
            filename = resource.filepath().parent.name
            self.changeModule(filename)
            self.ui.modulesWidget.setResourceSelection(resource)
        elif tree == self.ui.overrideWidget:
            self.ui.resourceTabs.setCurrentWidget(self.ui.overrideTab)
            self.ui.overrideWidget.setResourceSelection(resource)
            subfolder = ""
            for folder in self.active.override_list():
                lowercase_path_parts = [f.lower() for f in resource.filepath().parts]
                if folder.lower() in lowercase_path_parts and len(subfolder) < len(folder):
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

                def task():
                    return HTInstallation(path, name, tsl, self)

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

    def _extractResource(self, resource: FileResource, filepath: os.PathLike | str, loader: AsyncBatchLoader) -> None:
        try:
            data = resource.data()
            filepath: CaseAwarePath = CaseAwarePath(filepath)
            folderpath = filepath.parent
            filename = filepath.name

            decompile_tpc = self.ui.tpcDecompileCheckbox.isChecked()
            extract_txi = self.ui.tpcTxiCheckbox.isChecked()
            decompile_mdl = self.ui.mdlDecompileCheckbox.isChecked()
            extract_textures_mdl = self.ui.mdlTexturesCheckbox.isChecked()

            manipulate_tpc = decompile_tpc or extract_txi
            manipulate_mdl = decompile_mdl or extract_textures_mdl

            if resource.restype() == ResourceType.MDX and decompile_mdl:
                # Ignore extracting MDX files if decompiling MDLs
                return

            if resource.restype() == ResourceType.TPC and manipulate_tpc:
                tpc = read_tpc(data)

                if extract_txi:
                    txi_filename = filename.lower().replace(".tpc", ".txi")
                    with folderpath.joinpath(txi_filename).open("wb") as file:
                        file.write(tpc.txi.encode("ascii"))

                if decompile_tpc:
                    data = bytearray()
                    write_tpc(tpc, data, ResourceType.TGA)
                    filepath = filepath.parent / (filepath.stem + filepath.suffix.lower().replace(".tpc", ".tga"))
            if resource.restype() == ResourceType.MDL and manipulate_mdl:
                if decompile_mdl:
                    mdx_data = self.active.resource(resource.resname(), ResourceType.MDX).data
                    mdl = read_mdl(data, 0, 0, mdx_data, 0, 0)

                    data = bytearray()
                    write_mdl(mdl, data, ResourceType.MDL_ASCII)
                    filepath = filepath.replace(".mdl", ".ascii.mdl")

                if extract_textures_mdl:
                    try:
                        for texture in model.list_textures(data):
                            try:
                                tpc = self.active.texture(texture)
                                if extract_txi:
                                    with folderpath.joinpath(f"{texture}.txi").open("wb") as file:
                                        file.write(tpc.txi.encode("ascii"))
                                file_format = ResourceType.TGA if decompile_tpc else ResourceType.TPC
                                extension = "tga" if file_format == ResourceType.TGA else "tpc"
                                write_tpc(tpc, folderpath.joinpath(f"{texture}.{extension}"), file_format)
                            except Exception:
                                loader.errors.append(ValueError(f"Could not find or extract tpc: {texture}"))
                    except:
                        loader.errors.append(
                            ValueError(
                                f"Could not determine textures used in model: {resource.resname()}",
                            ),
                        )

            with filepath.open("wb") as file:
                file.write(data)
        except Exception as e:
            traceback.print_exc()
            msg = f"Failed to extract resource: {resource.resname()}.{resource.restype().extension}"
            raise Exception(msg) from e

    def openFromFile(self) -> None:
        filepaths = QFileDialog.getOpenFileNames(self, "Select files to open")[:-1][0]

        for filepath_str in filepaths:
            filepath = CaseAwarePath(filepath_str)
            try:
                resref, restype_ext = filepath.stem, filepath.suffix[1:]
                restype = ResourceType.from_extension(restype_ext)
                with filepath.open("rb") as file:
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

        self.lastModified = datetime.now()

        module_path = self.window.active.module_path()
        override_path = self.window.active.override_path()
        modified_path = CaseAwarePath(event.src_path)

        is_dir = modified_path.is_dir()

        if module_path == modified_path and not is_dir:
            module_file = modified_path.name
            self.window.module_files_updated.emit(module_file, event.event_type)
        elif override_path == modified_path and not is_dir:
            override_dir = modified_path.parent.relative_to(override_path)
            self.window.override_files_update.emit(override_dir, event.event_type)
