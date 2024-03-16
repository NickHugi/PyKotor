from __future__ import annotations

import traceback

from contextlib import suppress
from datetime import datetime, timedelta, timezone
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, ClassVar

from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap, QStandardItem
from PyQt5.QtWidgets import QFileDialog, QMainWindow, QMessageBox
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from pykotor.common.stream import BinaryReader
from pykotor.extract.file import ResourceIdentifier
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.erf.erf_auto import read_erf, write_erf
from pykotor.resource.formats.erf.erf_data import ERF, ERFType
from pykotor.resource.formats.mdl import read_mdl, write_mdl
from pykotor.resource.formats.rim.rim_auto import read_rim, write_rim
from pykotor.resource.formats.rim.rim_data import RIM
from pykotor.resource.formats.tpc import read_tpc, write_tpc
from pykotor.resource.type import ResourceType
from pykotor.tools import model, module
from pykotor.tools.misc import is_any_erf_type_file, is_bif_file, is_capsule_file, is_erf_file, is_mod_file, is_rim_file
from pykotor.tools.path import CaseAwarePath
from toolset.config import CURRENT_VERSION, getRemoteToolsetUpdateInfo, remoteVersionNewer
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
from toolset.gui.editors.tlk import TLKEditor
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
from toolset.gui.widgets.main_widgets import ResourceList
from toolset.gui.widgets.settings.misc import GlobalSettings
from toolset.gui.windows.help import HelpWindow
from toolset.gui.windows.indoor_builder import IndoorMapBuilder
from toolset.gui.windows.module_designer import ModuleDesigner
from toolset.utils.misc import openLink
from toolset.utils.window import addWindow, openResourceEditor
from utility.error_handling import format_exception_with_variables, universal_simplify_exception
from utility.system.path import Path, PurePath

if TYPE_CHECKING:
    import os

    from PyQt5 import QtGui
    from PyQt5.QtGui import QCloseEvent
    from watchdog.observers.api import BaseObserver

    from pykotor.extract.file import FileResource
    from pykotor.resource.formats.mdl.mdl_data import MDL
    from pykotor.resource.formats.tpc import TPC
    from pykotor.resource.type import SOURCE_TYPES
    from pykotor.tools.path import CaseAwarePath
    from toolset.gui.widgets.main_widgets import TextureList


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
        """Initializes the main window.

        Args:
        ----
            self: The object instance

        Processing Logic:
        ----------------
            - Sets up superclass initialization
            - Initializes observer and handler objects
            - Hides unnecessary UI sections on startup
            - Loads settings from file
            - Checks for updates on first run.
        """
        super().__init__()

        self.dogObserver: BaseObserver | None = None
        self.dogHandler = FolderObserver(self)
        self.active: HTInstallation | None = None
        self.settings: GlobalSettings = GlobalSettings()
        self.installations: dict[str, HTInstallation] = {}

        from toolset.uic.windows.main import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415

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

        self.checkForUpdates(silent=True)

    def _setupSignals(self):
        """Connects signals to slots for UI interactions.

        Args:
        ----
            self: {The class instance}: Sets up connections for UI signals.

        Processing Logic:
        ----------------
            - Connects game combo box index changed to change active installation
            - Connects module/override file updated signals to update handlers
            - Connects various widget signals like section changed to handler methods
            - Connects button clicks to extract/open resource methods
            - Connects menu actions to various editor, dialog and tool openings.
        """
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

        def openModuleDesigner() -> ModuleDesigner:
            designerUi = ModuleDesigner(self, self.active, self.active.module_path() / self.ui.modulesWidget.currentSection())
            addWindow(designerUi)
            return designerUi
        self.ui.specialActionButton.clicked.connect(openModuleDesigner)

        self.ui.overrideWidget.sectionChanged.connect(self.onOverrideChanged)
        self.ui.overrideWidget.requestReload.connect(self.onOverrideReload)
        self.ui.overrideWidget.requestRefresh.connect(self.onOverrideRefresh)
        self.ui.overrideWidget.requestExtractResource.connect(self.onExtractResources)
        self.ui.overrideWidget.requestOpenResource.connect(self.onOpenResources)

        self.ui.texturesWidget.sectionChanged.connect(self.onTexturesChanged)
        self.ui.texturesWidget.requestOpenResource.connect(self.onOpenResources)

        self.ui.extractButton.clicked.connect(lambda: self.onExtractResources(self.getActiveResourceWidget().selectedResources(), resourceWidget=self.getActiveResourceWidget()))
        self.ui.openButton.clicked.connect(lambda *args: self.onOpenResources(self.getActiveResourceWidget().selectedResources(),
                                                                              self.settings.gff_specializedEditors, resourceWidget=self.getActiveResourceWidget()))

        self.ui.openAction.triggered.connect(self.openFromFile)
        self.ui.actionSettings.triggered.connect(self.openSettingsDialog)
        self.ui.actionExit.triggered.connect(self.close)
        self.ui.actionNewTLK.triggered.connect(lambda: TLKEditor(self, self.active).show())
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
    def onModuleFileUpdated(self, changedFile: str, eventType: str):
        if eventType == "deleted":
            self.onModuleRefresh()
        else:
            if not changedFile or not changedFile.strip():  # FIXME(th3w1zard1): Why is the watchdog constantly sending invalid filenames?
                print(f"onModuleFileUpdated: can't reload module '{changedFile}', invalid name")
                return
            # Reload the resource cache for the module
            self.active.reload_module(changedFile)
            # If the current module opened is the file which was updated, then we
            # should refresh the ui.
            if self.ui.modulesWidget.currentSection() == changedFile:
                self.onModuleReload(changedFile)

    def onModuleChanged(self, newModuleFile: str):
        self.onModuleReload(newModuleFile)

    def onModuleReload(self, moduleFile: str):
        if not moduleFile or not moduleFile.strip():  # FIXME(th3w1zard1): Why is the watchdog constantly sending invalid filenames?
            print(f"onModuleReload: can't reload module '{moduleFile}', invalid name")
            return
        resources: list[FileResource] = self.active.module_resources(moduleFile)

        # Some users may choose to have their RIM files for the same module merged into a single option for the
        # dropdown menu.
        if self.settings.joinRIMsTogether:
            if is_rim_file(moduleFile):
                resources += self.active.module_resources(f"{PurePath(moduleFile).stem}_s.rim")
            if is_erf_file(moduleFile):
                resources += self.active.module_resources(f"{PurePath(moduleFile).stem}_dlg.erf")

        self.active.reload_module(moduleFile)
        self.ui.modulesWidget.setResources(resources)

    def onModuleRefresh(self):
        self.refreshModuleList(reload=False)

    def onOverrideFileUpdated(self, changedFile: str, eventType: str):
        if eventType == "deleted":
            self.onOverrideRefresh()
        else:
            self.onOverrideReload(changedFile)

    def onOverrideChanged(self, newDirectory: str):
        self.ui.overrideWidget.setResources(self.active.override_resources(newDirectory))

    def onOverrideReload(self, file_or_folder: str):
        if not self.active:
            print(f"No installation loaded, cannot reload {file_or_folder}")
            return
        file_or_folder_path = Path(self.active.override_path(), file_or_folder)
        if not file_or_folder_path.is_relative_to(self.active.override_path()):
            print(f"{file_or_folder_path} is not relative to the override folder, cannot reload")
            return
        if file_or_folder_path.safe_isfile():
            self.active.reload_override_file(file_or_folder_path)
            folder_path = file_or_folder_path.parent
        else:
            folder_path = file_or_folder_path
            self.active.load_override(folder_path)
        self.ui.overrideWidget.setResources(
            self.active.override_resources(
                Path._fix_path_formatting(str(folder_path.relative_to(self.active.override_path())).replace(str(self.active.override_path()), ""))
                if folder_path not in self.active.override_path().parents
                else "."
            )
        )

    def onOverrideRefresh(self):
        if not self.active:
            print("No installation loaded, cannot refresh Override")
            return
        print(f"Refreshing list of override folders available at {self.active.path()}")
        self.refreshOverrideList(reload=False)

    def onTexturesChanged(self, newTexturepack: str):
        if not self.active:
            print(f"No installation loaded, cannot change texturepack to '{newTexturepack}'")
            return
        self.ui.texturesWidget.setResources(self.active.texturepack_resources(newTexturepack))

    def onExtractResources(
        self,
        resources: list[FileResource],
        resourceWidget: ResourceList | TextureList | None = None,
    ):
        """Extracts the resources selected in the main UI window.

        Args:
        ----
            resources: list[FileResource]: List of selected resources to extract

        Processing Logic:
        ----------------
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
        elif isinstance(resourceWidget, ResourceList) and is_capsule_file(resourceWidget.currentSection()):
            module_name = resourceWidget.currentSection()
            self._saveCapsuleFromToolUI(module_name)

    def _saveCapsuleFromToolUI(self, module_name: str):
        c_filepath = self.active.module_path() / module_name

        capsuleFilter = "Module file (*.mod);;Encapsulated Resource File (*.erf);;Resource Image File (*.rim);;Save (*.sav);;All Capsule Types (*.erf; *.mod; *.rim; *.sav)"
        capsule_type = "module"
        if is_erf_file(c_filepath):
            capsule_type = "erf"
        elif is_rim_file(c_filepath):
            capsule_type = "rim"
        extension_to_filter = {
            ".mod": "Module (*.mod)",
            ".erf": "Encapsulated Resource File (*.erf)",
            ".rim": "Resource Image File (*.rim)",
            ".sav": "Save ERF (*.sav)",
        }
        filepath_str, _filter = QFileDialog.getSaveFileName(
            self,
            f"Save extracted {capsule_type} '{c_filepath.stem}' as...",
            str(Path.cwd().resolve()),
            capsuleFilter,
            extension_to_filter[c_filepath.suffix.lower()],  # defaults to the original extension.
        )
        if not filepath_str.strip():
            return
        r_save_filepath = Path(filepath_str)

        try:
            if is_mod_file(r_save_filepath):
                module.rim_to_mod(r_save_filepath, self.active.module_path(), module_name)
                QMessageBox(QMessageBox.Information, "Module Saved", f"Module saved to '{r_save_filepath}'").exec_()
                return

            erf_or_rim: ERF | RIM = read_erf(c_filepath) if is_any_erf_type_file(c_filepath) else read_rim(c_filepath)
            if is_rim_file(r_save_filepath):
                if isinstance(erf_or_rim, ERF):
                    erf_or_rim = erf_or_rim.to_rim()
                write_rim(erf_or_rim, r_save_filepath)
                QMessageBox(QMessageBox.Information, "RIM Saved", f"Resource Image File saved to '{r_save_filepath}'").exec_()

            elif is_any_erf_type_file(r_save_filepath):
                if isinstance(erf_or_rim, RIM):
                    erf_or_rim = erf_or_rim.to_erf()
                erf_or_rim.erf_type = ERFType.from_extension(r_save_filepath)
                write_erf(erf_or_rim, r_save_filepath)
                QMessageBox(QMessageBox.Information, "ERF Saved", f"Encapsulated Resource File saved to '{r_save_filepath}'").exec_()

        except Exception as e:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            with Path("errorlog.txt").open("a", encoding="utf-8") as file:
                lines = format_exception_with_variables(e)
                file.writelines(lines)
                file.write("\n----------------------\n")
            QMessageBox(QMessageBox.Critical, "Error saving capsule", str(universal_simplify_exception(e))).exec_()

    def onOpenResources(
        self,
        resources: list[FileResource],
        useSpecializedEditor: bool | None = None,
        resourceWidget: ResourceList | TextureList | None = None,
    ):
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
        if resources:
            return
        if not isinstance(resourceWidget, ResourceList):
            return
        filename = resourceWidget.currentSection()
        if not filename:
            return
        erf_filepath = self.active.module_path() / filename
        if not erf_filepath.safe_isfile():
            return
        res_ident = ResourceIdentifier.from_path(erf_filepath)
        if not res_ident.restype:
            return
        _filepath, _editor = openResourceEditor(
            erf_filepath,
            res_ident.resname,
            res_ident.restype,
            BinaryReader.load_file(erf_filepath),
            self.active,
            self,
            gff_specialized=useSpecializedEditor
        )

    # endregion

    # region Events
    def closeEvent(self, e: QCloseEvent | None):
        self.ui.texturesWidget.doTerminations()

    def dropEvent(self, e: QtGui.QDropEvent | None):
        if e is None:
            return
        if not e.mimeData().hasUrls():
            return
        for url in e.mimeData().urls():
            filepath: str = url.toLocalFile()
            data = BinaryReader.load_file(filepath)
            resref, restype = ResourceIdentifier.from_path(filepath)
            openResourceEditor(filepath, resref, restype, data, self.active, self)

    def dragEnterEvent(self, e: QtGui.QDragEnterEvent | None):
        if e is None:
            return
        if not e.mimeData().hasUrls():
            return
        for url in e.mimeData().urls():
            with suppress(Exception):
                _resref, _restype = ResourceIdentifier.from_path(url.toLocalFile()).validate()
                e.accept()

    # endregion

    # region Menu Bar
    def updateMenus(self):
        version = "x" if self.active is None else "2" if self.active.tsl else "1"

        dialogIconPath = f":/images/icons/k{version}/dialog.png"
        self.ui.actionNewDLG.setIcon(QIcon(QPixmap(dialogIconPath)))
        self.ui.actionNewDLG.setEnabled(self.active is not None)

        tlkIconPath = f":/images/icons/k{version}/tlk.png"
        self.ui.actionNewTLK.setIcon(QIcon(QPixmap(tlkIconPath)))
        self.ui.actionNewTLK.setEnabled(True)

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

    def openModuleDesigner(self):
        designer = ModuleDesigner(None, self.active)
        addWindow(designer)

    def openSettingsDialog(self):
        """Opens the Settings dialog and refresh installation combo list if changes."""
        dialog = SettingsDialog(self)
        if dialog.exec_() and dialog.installationEdited:
            self.reloadSettings()

    def openActiveTalktable(self):
        """Opens the talktable for the active (currently selected) installation.

        If there is no active information, show a message box instead.
        """
        filepath = self.active.path() / "dialog.tlk"
        data = BinaryReader.load_file(filepath)
        openResourceEditor(filepath, "dialog", ResourceType.TLK, data, self.active, self)

    def openActiveJournal(self):
        self.active.load_override(".")
        res = self.active.resource(
            "global",
            ResourceType.JRL,
            [SearchLocation.OVERRIDE, SearchLocation.CHITIN],
        )
        if res is None:
            print("res cannot be None in openActiveJournal")
            return
        openResourceEditor(
            res.filepath,
            resref="global",
            restype=ResourceType.JRL,
            data=res.data,
            installation=self.active,
            parentWindow=self,
        )

    def openFileSearchDialog(self):
        """Opens the FileSearcher dialog.

        If a search is conducted then a FileResults dialog displays the results
        where the user can then select a resource and the selected resouce will then be shown in the main window.
        """
        if self.active is None:
            print("No installation active, ergo nothing to search")
            return
        searchDialog = FileSearcher(self, self.installations)
        searchDialog.setModal(False)  # Make the dialog non-modal
        searchDialog.show()  # Show the dialog without blocking
        addWindow(searchDialog)
        searchDialog.fileResults.connect(self.handleSearchCompleted)

    def handleSearchCompleted(
        self,
        results_list: list[FileResource],
        searchedInstallation: HTInstallation,
    ):
        resultsDialog = FileResults(self, results_list, searchedInstallation)
        resultsDialog.setModal(False)  # Make the dialog non-modal
        resultsDialog.show()  # Show the dialog without blocking
        addWindow(resultsDialog)
        resultsDialog.selectionSignal.connect(self.handleResultsSelection)

    def handleResultsSelection(
        self,
        selection: FileResource,
    ):
        # Open relevant tab then select resource in the tree
        if selection.filepath().is_relative_to(self.active.module_path()):
            self.ui.resourceTabs.setCurrentIndex(1)
            self.selectResource(self.ui.modulesWidget, selection)
        elif selection.filepath().is_relative_to(self.active.override_path()):
            self.ui.resourceTabs.setCurrentIndex(2)
            self.selectResource(self.ui.overrideWidget, selection)
        elif is_bif_file(selection.filepath().name):
            self.selectResource(self.ui.coreWidget, selection)

    def openIndoorMapBuilder(self):
        IndoorMapBuilder(self, self.active).show()

    def openInstructionsWindow(self):
        """Opens the instructions window."""
        window = HelpWindow(None)
        window.setWindowIcon(self.windowIcon())
        window.show()
        window.activateWindow()
        addWindow(window)

    def openAboutDialog(self):
        """Opens the about dialog."""
        About(self).exec_()

    def checkForUpdates(self, *, silent: bool = False):
        """Scans for any updates and opens a dialog with a message based on the scan result.

        Args:
        ----
            silent: If true, only shows popup if an update is available.
        """
        try:
            self._check_toolset_update(silent=silent)
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            if not silent:
                etype, msg = universal_simplify_exception(e)
                QMessageBox(
                    QMessageBox.Information,
                    f"Unable to fetch latest version ({etype})",
                    f"Check if you are connected to the internet.\nError: {msg}",
                    QMessageBox.Ok,
                    self,
                ).exec_()

    def _check_toolset_update(self, *, silent: bool):
        remoteInfo = getRemoteToolsetUpdateInfo(
            useBetaChannel=self.settings.useBetaChannel,
            silent=silent,
        )
        if not isinstance(remoteInfo, dict):
            if silent:
                return
            raise remoteInfo

        toolsetLatestReleaseVersion = remoteInfo["toolsetLatestVersion"]
        toolsetLatestBetaVersion = remoteInfo["toolsetLatestBetaVersion"]
        releaseNewerThanBeta = remoteVersionNewer(toolsetLatestReleaseVersion, toolsetLatestBetaVersion)
        if (
            self.settings.alsoCheckReleaseVersion
            and (
                not self.settings.useBetaChannel
                or releaseNewerThanBeta is True
            )
        ):
            releaseVersionChecked = True
            greatestAvailableVersion = remoteInfo["toolsetLatestVersion"]
            toolsetLatestNotes = remoteInfo.get("toolsetLatestNotes", "")
            toolsetDownloadLink = remoteInfo["toolsetDownloadLink"]
        else:
            releaseVersionChecked = False
            greatestAvailableVersion = remoteInfo["toolsetLatestBetaVersion"]
            toolsetLatestNotes = remoteInfo.get("toolsetBetaLatestNotes", "")
            toolsetDownloadLink = remoteInfo["toolsetBetaDownloadLink"]

        version_check = remoteVersionNewer(CURRENT_VERSION, greatestAvailableVersion)
        if version_check is False:  # Only check False. if None then the version check failed
            if silent:
                return
            upToDateMsgBox = QMessageBox(
                QMessageBox.Information,
                "Version is up to date",
                f"You are running the latest version ({CURRENT_VERSION}).",
                QMessageBox.Ok,
                parent=None,
                flags=Qt.Window | Qt.Dialog | Qt.WindowStaysOnTopHint
            )
            upToDateMsgBox.setWindowIcon(self.windowIcon())
            upToDateMsgBox.exec_()
            return

        betaString = "release " if releaseVersionChecked else "beta "
        newVersionMsgBox = QMessageBox(
            QMessageBox.Information,
            f"New toolset {betaString}version available.",
            f"Your toolset version ({CURRENT_VERSION}) is outdated.<br>A new toolset {betaString}version ({greatestAvailableVersion}) available for <a href='{toolsetDownloadLink}'>download</a>.<br>{toolsetLatestNotes}",
            QMessageBox.Ok,
            parent=None,
            flags=Qt.Window | Qt.Dialog | Qt.WindowStaysOnTopHint
        )
        newVersionMsgBox.setWindowIcon(self.windowIcon())
        newVersionMsgBox.exec_()

    # endregion

    # region Other
    def reloadSettings(self):
        self.reloadInstallations()

    def getActiveResourceWidget(self) -> ResourceList | TextureList | None:
        if self.ui.resourceTabs.currentWidget() is self.ui.coreTab:
            return self.ui.coreWidget
        if self.ui.resourceTabs.currentWidget() is self.ui.modulesTab:
            return self.ui.modulesWidget
        if self.ui.resourceTabs.currentWidget() is self.ui.overrideTab:
            return self.ui.overrideWidget
        if self.ui.resourceTabs.currentWidget() is self.ui.texturesTab:
            return self.ui.texturesWidget
        return None

    def _getModulesList(self, *, reload: bool = True) -> list[QStandardItem]:
        if self.active is None:
            print("No installation is currently loaded, cannot refresh modules list")
            return []

        # If specified the user can forcibly reload the resource list for every module
        if reload:
            self.active.load_modules()

        areaNames: dict[str, str] = self.active.module_names()
        def sortAlgo(moduleFileName: str):
            lowerModuleFileName = moduleFileName.lower()
            if "stunt" in lowerModuleFileName:  # keep the least used stunt modules at the bottom.
                return f"zzzzz{lowerModuleFileName}"
            if self.settings.moduleSortOption == 0:  #"Sort by filename":
                return lowerModuleFileName
            if self.settings.moduleSortOption == 1:  #"Sort by humanized area name":
                return areaNames.get(moduleFileName).lower() + lowerModuleFileName
            # non-hardcoded mod_area_name
            areaName = self.active.module_id(moduleFileName, use_hardcoded=False, use_alternate=True)
            #print("filename:", moduleFileName, "area_id:", areaName)
            return areaName + lowerModuleFileName

        sortedKeys: list[str] = sorted(
            areaNames,
            key=sortAlgo
        )

        modules: list[QStandardItem] = []
        for moduleName in sortedKeys:
            # Some users may choose to have their RIM files for the same module merged into a single option for the
            # dropdown menu.
            lower_module_name = moduleName.lower()
            if self.settings.joinRIMsTogether:
                if lower_module_name.endswith("_s.rim"):
                    continue
                if lower_module_name.endswith("_dlg.erf"):
                    continue

            item = QStandardItem(f"{areaNames[moduleName]} [{moduleName}]")
            item.setData(moduleName, QtCore.Qt.UserRole)

            # Some users may choose to have items representing RIM files to have grey text.
            if self.settings.greyRIMText and lower_module_name.endswith(".rim"):
                item.setForeground(self.palette().shadow())

            modules.append(item)
        return modules

    def refreshModuleList(
        self,
        *,
        reload: bool = True,
        moduleItems: list[QStandardItem] | None = None,
    ):
        """Refreshes the list of modules in the modulesCombo combobox."""
        if not moduleItems:
            action = "Reloading" if reload else "Refreshing"
            def task() -> list[QStandardItem]:
                return self._getModulesList(reload=reload)
            loader = AsyncLoader(self, f"{action} modules list...", task, "Error refreshing module list.")
            loader.exec_()
            moduleItems = loader.value
        self.ui.modulesWidget.setSections(moduleItems)

    def _getOverrideList(self, *, reload=True):
        if self.active is None:
            print("No installation is currently loaded, cannot refresh override list")
            return []
        if reload:
            self.active.load_override()

        sections = []
        for directory in self.active.override_list():
            section = QStandardItem(directory if directory.strip() else "[Root]")
            section.setData(directory, QtCore.Qt.UserRole)
            sections.append(section)
        return sections

    def refreshOverrideList(
        self,
        *,
        reload: bool = True,
        overrideItems: list[QStandardItem] | None = None,
    ):
        """Refreshes the list of override directories in the overrideFolderCombo combobox."""
        if reload:
            self.active.load_override()
        if not overrideItems:
            action = "Reloading" if reload else "Refreshing"
            def task() -> list[QStandardItem]:
                return self._getOverrideList(reload=reload)
            loader = AsyncLoader(self, f"{action} override list...", task, "Error refreshing override list.")
            loader.exec_()
            overrideItems = loader.value
        self.ui.overrideWidget.setSections(overrideItems)

    def _getTexturePackList(
        self,
        *,
        reload: bool = True,
    ) -> list[QStandardItem] | None:
        if self.active is None:
            print("No installation is currently loaded, cannot refresh texturepack list")
            return None
        if reload:
            self.active.load_textures()

        sections = []
        for texturepack in self.active.texturepacks_list():
            section = QStandardItem(texturepack)
            section.setData(texturepack, QtCore.Qt.UserRole)
            sections.append(section)
        return sections

    def refreshTexturePackList(self, *, reload=True):
        sections = self._getTexturePackList(reload=reload)
        self.ui.texturesWidget.setSections(sections)

    def changeModule(self, moduleName: str):
        # Some users may choose to merge their RIM files under one option in the Modules tab; if this is the case we
        # need to account for this.
        if self.settings.joinRIMsTogether:
            if moduleName.casefold().endswith("_s.rim"):
                moduleName = f"{moduleName[:-6]}.rim"
            if moduleName.casefold().endswith("_dlg.erf"):
                moduleName = f"{moduleName[:-8]}.rim"

        self.ui.modulesWidget.changeSection(moduleName)

    def selectResource(self, tree: ResourceList, resource: FileResource):
        """This function seems to reload the resource after determining the ui widget containing it.

        Seems to only be used for the FileSearcher dialog.
        """
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
            for folder_name in self.active.override_list():
                folder_path: CaseAwarePath = self.active.override_path() / folder_name
                if resource.filepath().is_relative_to(folder_path) and len(subfolder) < len(folder_path.name):
                    subfolder = folder_name
            self.changeOverrideFolder(subfolder)

    def changeOverrideFolder(self, subfolder: str):
        self.ui.overrideWidget.changeSection(subfolder)

    def reloadInstallations(self):
        """Refresh the list of installations available in the combobox."""
        self.ui.gameCombo.clear()
        self.ui.gameCombo.addItem("[None]")

        for installation in self.settings.installations().values():
            self.ui.gameCombo.addItem(installation.name)

    def changeActiveInstallation(self, index: int):
        """Changes the active installation selected.

        If an installation does not have a path yet set, the user is prompted
        to select a directory for it. If the installation path remains unset then the active
        installation also remains unselected.

        Args:
        ----
            index (int): Index of the installation in the installationCombo combobox.
        """
        self.ui.gameCombo.setCurrentIndex(index)

        self.ui.coreWidget.setResources([])
        self.ui.modulesWidget.setSections([])
        self.ui.modulesWidget.setResources([])
        self.ui.overrideWidget.setSections([])
        self.ui.overrideWidget.setResources([])

        self.ui.resourceTabs.setEnabled(False)
        self.ui.sidebar.setEnabled(False)
        self.updateMenus()

        if index <= 0:
            if index < 0:
                print(f"Index out of range - self.changeActiveInstallation({index})")
                self.ui.gameCombo.setCurrentIndex(0)
            self.active = None
            if self.dogObserver is not None:
                self.dogObserver.stop()
                self.dogObserver = None
            return

        self.ui.resourceTabs.setEnabled(True)
        self.ui.sidebar.setEnabled(True)

        name: str = self.ui.gameCombo.itemText(index)
        path: str = self.settings.installations()[name].path.strip()
        tsl: bool = self.settings.installations()[name].tsl

        # If the user has not set a path for the particular game yet, ask them too.
        if not path or not Path(path).safe_isdir():
            if path and path.strip():
                QMessageBox(QMessageBox.Warning, f"installation '{path}' not found", "Select another path now.").exec_()
            path = QFileDialog.getExistingDirectory(self, f"Select the game directory for {name}")

        # If the user still has not set a path, then return them to the [None] option.
        if not path:
            print("User did not choose a path for this installation.")
            self.ui.gameCombo.setCurrentIndex(0)
            self.active = None
            if self.dogObserver is not None:
                self.dogObserver.stop()
                self.dogObserver = None
            return

        def load_task(active: HTInstallation | None = None) -> HTInstallation:
            return active or HTInstallation(path, name, tsl, self)

        active = self.installations.get(name)
        loader = AsyncLoader(self, "Loading Installation" if not active else "Refreshing installation", lambda: load_task(active), "Failed to load installation")
        if not loader.exec_():
            self.active = None
            self.ui.gameCombo.setCurrentIndex(0)
            if self.dogObserver is not None:
                self.dogObserver.stop()
                self.dogObserver = None
            return
        self.active = loader.value
        # KEEP UI CODE IN MAIN THREAD!
        def prepare_task() -> tuple[list[QStandardItem] | None, ...]:
            return (
                self._getModulesList(reload=False),
                self._getOverrideList(reload=False),
                self._getTexturePackList(reload=False),
            )
        prepare_loader = AsyncLoader(self, "Preparing resources...", lambda: prepare_task(), "Failed to load installation")
        if not prepare_loader.exec_():
            self.active = None
            self.ui.gameCombo.setCurrentIndex(0)
            if self.dogObserver is not None:
                self.dogObserver.stop()
                self.dogObserver = None
            return
        print("Loading core installation resources into UI...")
        self.ui.coreWidget.setResources(self.active.chitin_resources())
        moduleItems, overrideItems, textureItems = prepare_loader.value
        self.ui.modulesWidget.setSections(moduleItems)
        self.ui.overrideWidget.setSections(overrideItems)
        self.ui.texturesWidget.setSections(textureItems)
        print("Remove unused categories...")
        self.ui.coreWidget.modulesModel.removeUnusedCategories()
        self.ui.texturesWidget.setInstallation(self.active)
        print("Updating menus...")
        self.updateMenus()
        print("Setting up watchdog observer...")
        if self.dogObserver is not None:
            print("Stopping old watchdog service...")
            self.dogObserver.stop()
        self.dogObserver = Observer()
        self.dogObserver.schedule(self.dogHandler, self.active.path(), recursive=True)
        self.dogObserver.start()
        print("Loader task completed.")
        self.settings.installations()[name].path = path
        self.installations[name] = self.active

    def _extractResource(self, resource: FileResource, filepath: os.PathLike | str, loader: AsyncBatchLoader):
        """Extracts a resource file from a FileResource object.

        Args:
        ----
            resource (FileResource): The FileResource object
            filepath (os.PathLike | str): Path to save the extracted file
            loader (AsyncBatchLoader): Loader for async operations

        Processing Logic:
        ----------------
            - Extracts Txi data from TPC files
            - Decompiles TPC and MDL files
            - Extracts textures from MDL files
            - Writes extracted data to the file path
        """
        r_filepath: Path = Path.pathify(filepath)
        folderpath: Path = r_filepath.parent

        try:
            data: bytes = resource.data()

            if resource.restype() == ResourceType.MDX and self.ui.mdlDecompileCheckbox.isChecked():
                # Ignore extracting MDX files if decompiling MDLs
                return

            if resource.restype() == ResourceType.TPC:
                tpc: TPC = read_tpc(data, txi_source=r_filepath)

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
        QMessageBox(QMessageBox.Information, "Finished extracting", f"Extracted {resource.resname()} to {r_filepath}").exec_()

    def _extractTxi(self, tpc: TPC, filepath: Path):
        with filepath.with_suffix(".txi").open("wb") as file:
            file.write(tpc.txi.encode("ascii"))

    def _decompileTpc(self, tpc: TPC) -> bytearray:
        data = bytearray()
        write_tpc(tpc, data, ResourceType.TGA)
        return data

    def _decompileMdl(self, resource: FileResource, data: SOURCE_TYPES) -> bytearray:
        mdxData: bytes = self.active.resource(resource.resname(), ResourceType.MDX).data
        mdl: MDL | None = read_mdl(data, 0, 0, mdxData, 0, 0)

        data = bytearray()
        write_mdl(mdl, data, ResourceType.MDL_ASCII)
        return data

    def _extractMdlTextures(self, resource: FileResource, folderpath: Path, loader: AsyncBatchLoader, data: bytes):
        try:
            for texture in model.list_textures(data):
                try:
                    tpc: TPC | None = self.active.texture(texture)
                    if tpc is None:
                        raise ValueError(texture)  # noqa: TRY301
                    if self.ui.tpcTxiCheckbox.isChecked():
                        self._extractTxi(tpc, folderpath.joinpath(f"{texture}.tpc"))
                    file_format = ResourceType.TGA if self.ui.tpcDecompileCheckbox.isChecked() else ResourceType.TPC
                    extension = "tga" if file_format == ResourceType.TGA else "tpc"
                    write_tpc(tpc, folderpath.joinpath(f"{texture}.{extension}"), file_format)
                except Exception as e:  # noqa: PERF203
                    etype, msg = universal_simplify_exception(e)
                    loader.errors.append(e.__class__(f"Could not find or extract tpc: '{texture}'"))
        except Exception as e:
            etype, msg = universal_simplify_exception(e)
            loader.errors.append(e.__class__(f"Could not determine textures used in model: '{resource.resname()}'\nReason ({etype}): {msg}"))

    def openFromFile(self):
        filepaths = QFileDialog.getOpenFileNames(self, "Select files to open")[:-1][0]

        for filepath in filepaths:
            r_filepath = Path(filepath)
            try:
                with r_filepath.open("rb") as file:
                    data = file.read()
                openResourceEditor(filepath, *ResourceIdentifier.from_path(r_filepath).validate(), data, self.active, self)
            except ValueError as e:
                etype, msg = universal_simplify_exception(e)
                QMessageBox(QMessageBox.Critical, f"Failed to open file ({etype})", msg).exec_()

    # endregion


class FolderObserver(FileSystemEventHandler):
    def __init__(self, window: ToolWindow):
        self.window: ToolWindow = window
        self.lastModified: datetime = datetime.now(tz=timezone.utc).astimezone()

    def on_any_event(self, event):
        rightnow: datetime = datetime.now(tz=timezone.utc).astimezone()
        if rightnow - self.lastModified < timedelta(seconds=1):
            return

        self.lastModified = rightnow
        modified_path: Path = Path(event.src_path)
        if not modified_path.is_dir():
            return

        module_path: Path = self.window.active.module_path()
        override_path: Path = self.window.active.override_path()

        if modified_path.is_relative_to(module_path):
            module_file: Path = modified_path.parent
            self.window.moduleFilesUpdated.emit(str(module_file), event.event_type)
        elif modified_path.is_relative_to(override_path):
            self.window.overrideFilesUpdate.emit(str(modified_path), event.event_type)
