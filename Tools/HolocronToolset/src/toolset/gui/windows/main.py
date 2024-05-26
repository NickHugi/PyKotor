from __future__ import annotations

import cProfile
import errno
import os
import platform
import sys

from datetime import datetime, timedelta, timezone
from multiprocessing import Process, Queue
from typing import TYPE_CHECKING, Any

import qtpy

from qtpy import QtCore
from qtpy.QtCore import (
    QCoreApplication,
    QFile,
    QSize,
    QTextStream,
    QThread,
    Qt,
)
from qtpy.QtGui import (
    QColor,
    QIcon,
    QPalette,
    QPixmap,
    QStandardItem,
)
from qtpy.QtWidgets import (
    QAction,
    QApplication,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QSizePolicy,
    QStyle,
    QStyledItemDelegate,
    QVBoxLayout,
)
from typing_extensions import Literal
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from pykotor.common.stream import BinaryReader
from pykotor.extract.file import FileResource, ResourceIdentifier
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
from toolset.gui.dialogs.asyncloader import AsyncBatchLoader, AsyncLoader, ProgressDialog
from toolset.gui.dialogs.clone_module import CloneModuleDialog
from toolset.gui.dialogs.save.generic_file_saver import FileSaveHandler
from toolset.gui.dialogs.search import FileResults, FileSearcher
from toolset.gui.dialogs.select_update import UpdateDialog
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
from toolset.gui.helpers.main_focus_helper import MainFocusHandler
from toolset.gui.widgets.main_widgets import ResourceList
from toolset.gui.widgets.settings.misc import GlobalSettings
from toolset.gui.windows.help import HelpWindow
from toolset.gui.windows.indoor_builder import IndoorMapBuilder
from toolset.gui.windows.module_designer import ModuleDesigner
from toolset.utils.misc import openLink
from toolset.utils.window import addWindow, openResourceEditor
from utility.error_handling import universal_simplify_exception
from utility.logger_util import RobustRootLogger
from utility.misc import ProcessorArchitecture
from utility.system.path import Path, PurePath
from utility.updater.update import AppUpdate

if TYPE_CHECKING:
    from typing import NoReturn

    from qtpy import QtGui
    from qtpy.QtCore import QEvent, QObject
    from qtpy.QtGui import (
        QCloseEvent,
        QKeyEvent,
        QMouseEvent,
    )
    from qtpy.QtWidgets import QWidget
    from watchdog.events import FileSystemEvent
    from watchdog.observers.api import BaseObserver

    from pykotor.extract.file import ResourceResult
    from pykotor.resource.formats.mdl.mdl_data import MDL
    from pykotor.resource.formats.tpc import TPC
    from pykotor.resource.type import SOURCE_TYPES
    from toolset.gui.widgets.main_widgets import TextureList

def run_progress_dialog(progress_queue: Queue, title: str = "Operation Progress") -> NoReturn:
    app = QApplication(sys.argv)
    dialog = ProgressDialog(progress_queue, title)
    icon = app.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation)
    dialog.setWindowIcon(QIcon(icon))
    dialog.show()
    sys.exit(app.exec_())


class ToolWindow(QMainWindow):
    moduleFilesUpdated = QtCore.Signal(object, object)
    overrideFilesUpdate = QtCore.Signal(object, object)

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
        self._initUi()
        self._setupSignals()
        self.setWindowTitle(f"Holocron Toolset ({qtpy.API_NAME})")

        self.active: HTInstallation | None = None
        self.installations: dict[str, HTInstallation] = {}

        self.settings: GlobalSettings = GlobalSettings()
        self.log: RobustRootLogger = RobustRootLogger()

        # Watchdog
        self.dogObserver: BaseObserver | None = None
        self.dogHandler = FolderObserver(self)

        # Theme setup
        self.original_style: str = self.style().objectName()
        self.original_palette: QPalette = self.palette()
        self.toggle_stylesheet(self.settings.selectedTheme)

        # Focus handler (searchbox, various keyboard actions)
        self.focusHandler: MainFocusHandler = MainFocusHandler(self)
        self.installEventFilter(self.focusHandler)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

        # Finalize the init
        self.reloadSettings()
        self.unsetInstallation()
        self.activateWindow()
        self.raise_()
        self.activateWindow()  # Ensure it comes to the front

    def _initUi(self):
        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.windows.main import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.windows.main import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.windows.main import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.windows.main import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.coreWidget.hideSection()
        self.ui.coreWidget.hideReloadButton()
        self.setWindowIcon(QIcon(QPixmap(":/images/icons/sith.png")))
        self.setupModulesTab()

    def setupModulesTab(self):
        modulesResourceList = self.ui.modulesWidget.ui
        modulesSectionCombo = modulesResourceList.sectionCombo
        refreshButton = modulesResourceList.refreshButton
        designerButton = self.ui.specialActionButton

        # Set size policies
        modulesSectionCombo.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        refreshButton.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        designerButton.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        modulesSectionCombo.setMinimumWidth(30)

        modulesResourceList.horizontalLayout_2.removeWidget(modulesSectionCombo)
        modulesResourceList.horizontalLayout_2.removeWidget(refreshButton)
        modulesResourceList.verticalLayout.removeItem(modulesResourceList.horizontalLayout_2)

        # Create a new layout to stack Designer and Refresh buttons
        stackButtonLayout = QVBoxLayout()
        stackButtonLayout.addWidget(designerButton)
        stackButtonLayout.addWidget(refreshButton)

        # Create a new horizontal layout to place the combobox and buttons
        topLayout = QHBoxLayout()
        topLayout.addWidget(modulesSectionCombo)
        topLayout.addLayout(stackButtonLayout)

        # Insert the new top layout into the vertical layout
        self.ui.verticalLayoutModulesTab.insertLayout(0, topLayout)

        # Adjust the vertical layout to accommodate the combobox height change
        modulesResourceList.verticalLayout.addWidget(modulesResourceList.resourceTree)
        existing_stylesheet = modulesSectionCombo.styleSheet()
        merged_stylesheet = existing_stylesheet + """
            QComboBox {
                font-size: 14px; /* Increase text size */
                font-family: Arial, Helvetica, sans-serif; /* Use a readable font */
                padding: 5px; /* Add padding for spacing */
                text-align: center; /* Center the text */
            }
            QComboBox::drop-down {
                width: 30px;
                subcontrol-origin: padding;
                subcontrol-position: top right;
                border-left-width: 1px;
                border-left-color: darkgray;
                border-left-style: solid; /* Just a cosmetic line */
                icon: url(:/icons/arrow_down.png); /* Specify the arrow icon path */
            }
            QComboBox QAbstractItemView {
                font-size: 14px; /* Ensure the dropdown also has increased text size */
                font-family: Arial, Helvetica, sans-serif; /* Use the same font */
                padding: 10px 0; /* Add padding to separate lines */
            }
        """
        modulesSectionCombo.setStyleSheet(merged_stylesheet)
        modulesSectionCombo.setMaxVisibleItems(18)

        # Set the dropdown icon using QStyle standard icon
        dropdown_icon = self.style().standardIcon(QStyle.SP_ArrowDown)
        modulesSectionCombo.setItemDelegate(QStyledItemDelegate(modulesSectionCombo))
        modulesSectionCombo.setIconSize(QSize(16, 16))
        modulesSectionCombo.setItemIcon(0, dropdown_icon)

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

        self.ui.menuTheme.triggered.connect(self.toggle_stylesheet)

        self.moduleFilesUpdated.connect(self.onModuleFileUpdated)
        self.overrideFilesUpdate.connect(self.onOverrideFileUpdated)

        self.ui.coreWidget.requestExtractResource.connect(self.onExtractResources)
        self.ui.coreWidget.requestOpenResource.connect(self.onOpenResources)
        self.ui.coreWidget.requestRefresh.connect(self.onCoreRefresh)

        self.ui.modulesWidget.sectionChanged.connect(self.onModuleChanged)
        self.ui.modulesWidget.requestReload.connect(self.onModuleReload)
        self.ui.modulesWidget.requestRefresh.connect(self.onModuleRefresh)
        self.ui.modulesWidget.requestExtractResource.connect(self.onExtractResources)
        self.ui.modulesWidget.requestOpenResource.connect(self.onOpenResources)

        self.ui.savesWidget.sectionChanged.connect(self.onSavepathChanged)
        self.ui.savesWidget.requestReload.connect(self.onSaveReload)
        self.ui.savesWidget.requestRefresh.connect(self.onSaveRefresh)
        self.ui.savesWidget.requestExtractResource.connect(self.onExtractResources)
        self.ui.savesWidget.requestOpenResource.connect(self.onOpenResources)

        def openModuleDesigner() -> ModuleDesigner:
            designerUi = (
                ModuleDesigner(
                    None,
                    self.active,
                    self.active.module_path() / self.ui.modulesWidget.currentSection(),
                )
            )
            addWindow(designerUi, show=False)
            return designerUi

        self.ui.specialActionButton.clicked.connect(openModuleDesigner)

        self.ui.overrideWidget.sectionChanged.connect(self.onOverrideChanged)
        self.ui.overrideWidget.requestReload.connect(self.onOverrideReload)
        self.ui.overrideWidget.requestRefresh.connect(self.onOverrideRefresh)
        self.ui.overrideWidget.requestExtractResource.connect(self.onExtractResources)
        self.ui.overrideWidget.requestOpenResource.connect(self.onOpenResources)

        self.ui.texturesWidget.sectionChanged.connect(self.onTexturesChanged)
        self.ui.texturesWidget.requestOpenResource.connect(self.onOpenResources)

        self.ui.extractButton.clicked.connect(
            lambda: self.onExtractResources(
                self.getActiveResourceWidget().selectedResources(),
                resourceWidget=self.getActiveResourceWidget(),
            ),
        )
        self.ui.openButton.clicked.connect(
            lambda *args: self.onOpenResources(
                self.getActiveResourceWidget().selectedResources(),
                self.settings.gff_specializedEditors,
                resourceWidget=self.getActiveResourceWidget(),
            )
        )

        self.ui.openAction.triggered.connect(self.openFromFile)
        self.ui.actionSettings.triggered.connect(self.openSettingsDialog)
        self.ui.actionExit.triggered.connect(self.close)
        def _launchEditor(
            editor: QWidget
        ):
            addWindow(editor)
            if isinstance(editor, QDialog):
                editor.exec_()
            else:
                editor.show()
        self.ui.actionNewTLK.triggered.connect(lambda: _launchEditor(TLKEditor(self, self.active)))
        self.ui.actionNewDLG.triggered.connect(lambda: _launchEditor(DLGEditor(self, self.active)))
        self.ui.actionNewNSS.triggered.connect(lambda: _launchEditor(NSSEditor(self, self.active)))
        self.ui.actionNewUTC.triggered.connect(lambda: _launchEditor(UTCEditor(self, self.active)))
        self.ui.actionNewUTP.triggered.connect(lambda: _launchEditor(UTPEditor(self, self.active)))
        self.ui.actionNewUTD.triggered.connect(lambda: _launchEditor(UTDEditor(self, self.active)))
        self.ui.actionNewUTI.triggered.connect(lambda: _launchEditor(UTIEditor(self, self.active)))
        self.ui.actionNewUTT.triggered.connect(lambda: _launchEditor(UTTEditor(self, self.active)))
        self.ui.actionNewUTM.triggered.connect(lambda: _launchEditor(UTMEditor(self, self.active)))
        self.ui.actionNewUTW.triggered.connect(lambda: _launchEditor(UTWEditor(self, self.active)))
        self.ui.actionNewUTE.triggered.connect(lambda: _launchEditor(UTEEditor(self, self.active)))
        self.ui.actionNewUTS.triggered.connect(lambda: _launchEditor(UTSEditor(self, self.active)))
        self.ui.actionNewGFF.triggered.connect(lambda: _launchEditor(GFFEditor(self, self.active)))
        self.ui.actionNewERF.triggered.connect(lambda: _launchEditor(ERFEditor(self, self.active)))
        self.ui.actionNewTXT.triggered.connect(lambda: _launchEditor(TXTEditor(self, self.active)))
        self.ui.actionNewSSF.triggered.connect(lambda: _launchEditor(SSFEditor(self, self.active)))
        self.ui.actionCloneModule.triggered.connect(lambda: _launchEditor(CloneModuleDialog(self, self.active, self.installations)))

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

        self.ui.menuRecentFiles.aboutToShow.connect(self.populateRecentFilesMenu)

    def populateRecentFilesMenu(self):
        """Populate the Recent Files menu with the recent files."""
        recentFilesSetting: list[str] = self.settings.recentFiles
        recentFiles: list[Path] = [Path(file) for file in recentFilesSetting]
        self.ui.menuRecentFiles.clear()
        for file in recentFiles:
            action = QAction(file.name, self)
            action.setData(file)
            action.triggered.connect(self.openRecentFile)
            self.ui.menuRecentFiles.addAction(action)  # type: ignore[arg-type]

    def openRecentFile(self):
        """Open a file from the Recent Files menu."""
        objRet: QObject = self.sender()
        if not isinstance(objRet, QAction):
            return
        action = objRet
        if not action:
            return
        if not isinstance(action, QAction):
            return
        file = action.data()
        if not file:
            return
        if not isinstance(file, Path):
            return
        resource = FileResource.from_path(file)
        openResourceEditor(file, resource.resname(), resource.restype(), resource.data(), self.active, self)

    def toggle_stylesheet(self, theme: QAction | str):
        # get the QApplication instance,  or crash if not set
        app = QApplication.instance()
        if app is None or not isinstance(app, QApplication):
            raise RuntimeError("No Qt Application found or not a QApplication instance.")

        themeName: str = theme.text() if isinstance(theme, QAction) else theme
        self.settings.selectedTheme = themeName
        if themeName == "Breeze (Dark)":
            file = QFile(":/dark/stylesheet.qss")
            file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text)
            stream = QTextStream(file)
            app.setStyleSheet(stream.readAll())
            file.close()
            self.show()  # Re-apply the window with new flags
        elif not themeName or themeName == "Default (Light)":
            app.setStyleSheet("")  # Reset to default style
            app.setPalette(self.original_palette)  # Reset to default palette
            app.setStyle(self.original_style)
            # Reset window flags to default, which includes the title bar
            self.setWindowFlags(
                Qt.WindowType.Window
                | Qt.WindowType.WindowCloseButtonHint
                | Qt.WindowType.WindowMinimizeButtonHint
                | Qt.WindowType.WindowMaximizeButtonHint
            )
        elif themeName == "Fusion (Dark)":
            app.setStyle("Fusion")
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
            dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25))
            dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
            dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(35, 35, 35))
            dark_palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Button, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, Qt.GlobalColor.darkGray)
            dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, Qt.GlobalColor.darkGray)
            dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, Qt.GlobalColor.darkGray)
            dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Light, QColor(53, 53, 53))
            QApplication.setPalette(dark_palette)
        print("themeName:", themeName)
        self.show()  # Re-apply the window with new flags

    # region Signal callbacks
    def onCoreRefresh(self):
        self.log.debug("ToolWindow.onCoreRefresh()")
        self.refreshCoreList(reload=True)

    def onModuleChanged(self, newModuleFile: str):
        self.log.debug(f"ToolWindow.onModuleChanged(newModuleFile='{newModuleFile}')")
        self.onModuleReload(newModuleFile)

    def onModuleRefresh(self):
        self.log.debug("ToolWindow.onModuleRefresh()")
        self.refreshModuleList(reload=True)

    def onModuleReload(self, moduleFile: str):
        self.log.debug(f"ToolWindow.onModuleReload(moduleFile='{moduleFile}')")
        assert self.active is not None
        if not moduleFile or not moduleFile.strip():
            print(f"onModuleReload: can't reload module '{moduleFile}', invalid name")
            return
        resources: list[FileResource] = self.active.module_resources(moduleFile)

        # Some users may choose to have their RIM files for the same module merged into a single option for the
        # dropdown menu.
        if self.settings.joinRIMsTogether and (is_rim_file(moduleFile) or is_erf_file(moduleFile)):
            resources.extend(self.active.module_resources(f"{PurePath(moduleFile).stem}_s.rim"))
            if self.active.game().is_k2():
                resources.extend(self.active.module_resources(f"{PurePath(moduleFile).stem}_dlg.erf"))

        self.active.reload_module(moduleFile)
        self.ui.modulesWidget.setResources(resources)

    def onModuleFileUpdated(self, changedFile: str, eventType: str):
        self.log.debug(f"ToolWindow.onModuleFileUpdated(changedFile='{changedFile}', eventType='{eventType}')")
        assert self.active is not None
        if eventType == "deleted":
            self.onModuleRefresh()
        else:
            # Reload the resource cache for the module
            self.active.reload_module(changedFile)
            # If the current module opened is the file which was updated, then we
            # should refresh the ui.
            if self.ui.modulesWidget.currentSection() == changedFile:
                self.onModuleReload(changedFile)

    def onSavepathChanged(self, newSaveDir: str):
        self.log.debug(f"ToolWindow.onSavepathChanged(newSaveDir='{newSaveDir}')")
        assert self.active is not None
        print("Loading save resources into UI...")

        # Clear the entire model before loading new save resources
        self.ui.savesWidget.modulesModel.invisibleRootItem().removeRows(0, self.ui.savesWidget.modulesModel.rowCount())
        newSaveDirPath = CaseAwarePath(newSaveDir)
        if newSaveDirPath not in self.active._saves:
            self.active.load_saves()
        if newSaveDirPath not in self.active._saves:
            print(f"Cannot load save {newSaveDirPath}: not found in saves list")
            return

        for save_path, resource_list in self.active._saves[newSaveDirPath].items():
            # Create a new parent item for the save_path
            save_path_item = QStandardItem(str(save_path.relative_to(save_path.parent.parent)))
            self.ui.savesWidget.modulesModel.invisibleRootItem().appendRow(save_path_item)

            # Dictionary to keep track of category items under this save_path_item
            categoryItemsUnderSavePath: dict[str, QStandardItem] = {}

            for resource in resource_list:
                restype: ResourceType = resource.restype()
                category: str = restype.category

                # Check if the category item already exists under this save_path_item
                if category not in categoryItemsUnderSavePath:
                    # Create new category item similar to _getCategoryItem logic
                    categoryItem = QStandardItem(category)
                    categoryItem.setSelectable(False)
                    unusedItem = QStandardItem("")
                    unusedItem.setSelectable(False)
                    save_path_item.appendRow([categoryItem, unusedItem])
                    categoryItemsUnderSavePath[category] = categoryItem

                # Now, categoryItem is guaranteed to exist
                categoryItem = categoryItemsUnderSavePath[category]

                # Check if resource is already listed under this category
                foundResource = False
                for i in range(categoryItem.rowCount()):
                    item = categoryItem.child(i)
                    if item and item.resource == resource:
                        # Update the resource reference if necessary
                        item.resource = resource
                        foundResource = True
                        break

                if not foundResource:
                    # Add new resource under the category
                    item1 = QStandardItem(resource.resname())
                    item1.resource = resource
                    item2 = QStandardItem(restype.extension.upper())
                    categoryItem.appendRow([item1, item2])

    def onSaveReload(self, saveDir: str):
        self.log.debug(f"ToolWindow.onSaveReload(saveDir='{saveDir}')")
        self.onSavepathChanged(saveDir)

    def onSaveRefresh(self):
        self.log.debug("ToolWindow.onSaveRefresh()")
        self.refreshSavesList()

    def onOverrideFileUpdated(self, changedFile: str, eventType: str):
        self.log.debug(f"ToolWindow.onOverrideFileUpdated(changedFile='{changedFile}', eventType={eventType})")
        if eventType == "deleted":
            self.onOverrideRefresh()
        else:
            self.onOverrideReload(changedFile)

    def onOverrideChanged(self, newDirectory: str):
        self.log.debug(f"ToolWindow.onOverrideChanged(newDirectory='{newDirectory}')")
        assert self.active is not None
        self.ui.overrideWidget.setResources(self.active.override_resources(newDirectory))

    def onOverrideReload(self, file_or_folder: str):
        self.log.debug(f"ToolWindow.onOverrideReload(file_or_folder='{file_or_folder}')")
        assert self.active is not None
        override_path = self.active.override_path()
        file_or_folder_path = override_path.joinpath(file_or_folder)
        if not file_or_folder_path.is_relative_to(self.active.override_path()):
            raise ValueError(f"'{file_or_folder_path}' is not relative to the override folder, cannot reload")
        if file_or_folder_path.safe_isfile():
            rel_folderpath = file_or_folder_path.parent.relative_to(self.active.override_path())
            self.active.reload_override_file(file_or_folder_path)
        else:
            rel_folderpath = file_or_folder_path.relative_to(self.active.override_path())
            self.active.load_override(str(rel_folderpath))
        self.ui.overrideWidget.setResources(self.active.override_resources( str(rel_folderpath) if rel_folderpath.name else None ))

    def onOverrideRefresh(self):
        self.log.debug("ToolWindow.onOverrideRefresh()")
        assert self.active is not None
        print(f"Refreshing list of override folders available at {self.active.path()}")
        self.refreshOverrideList(reload=True)

    def onTexturesChanged(self, texturepackName: str):
        self.log.debug(f"ToolWindow.onTexturesChanged(texturepackName='{texturepackName}')")
        assert self.active is not None
        self.ui.texturesWidget.setResources(self.active.texturepack_resources(texturepackName))

    def changeActiveInstallation(self, index: int):
        """Changes the active installation selected.

        If an installation does not have a path yet set, the user is prompted
        to select a directory for it. If the installation path remains unset then the active
        installation also remains unselected.

        Args:
        ----
            index (int): Index of the installation in the installationCombo combobox.
        """
        self.log.debug(f"ToolWindow.changeActiveInstallation(index={index})")
        if index < 0:  # self.ui.gameCombo.clear() will call this function with -1
            print(f"Index out of range - {index} (expected zero or positive)")
            return

        previousIndex: int = self.ui.gameCombo.currentIndex()
        self.ui.gameCombo.setCurrentIndex(index)

        if index == 0:
            self.unsetInstallation()
            return

        name: str = self.ui.gameCombo.itemText(index)
        path: str = self.settings.installations()[name].path.strip()
        tsl: bool = self.settings.installations()[name].tsl

        # If the user has not set a path for the particular game yet, ask them too.
        if not path or not path.strip() or not Path(path).safe_isdir():
            if path and path.strip():
                QMessageBox(QMessageBox.Icon.Warning, f"Installation '{path}' not found", "Select another path now.").exec_()
            path = QFileDialog.getExistingDirectory(self, f"Select the game directory for {name}")

        # If the user still has not set a path, then return them to the [None] option.
        if not path:
            print("User did not choose a path for this installation.")
            self.ui.gameCombo.setCurrentIndex(previousIndex)
            return

        active = self.installations.get(name)
        if active:
            self.active = active
        else:
            def load_task() -> HTInstallation:
                profiler = None
                if self.settings.profileToolset and cProfile is not None:
                    profiler = cProfile.Profile()
                    profiler.enable()
                new_active = HTInstallation(path, name, self, tsl=tsl)
                if self.settings.profileToolset and profiler:
                    profiler.disable()
                    profiler.dump_stats(str(Path("load_ht_installation.pstat").absolute()))
                return new_active
            loader = AsyncLoader(self, "Loading Installation", load_task, "Failed to load installation")
            if not loader.exec_():
                self.ui.gameCombo.setCurrentIndex(previousIndex)
                return
            self.active = loader.value

        # KEEP UI CODE IN MAIN THREAD!
        self.ui.resourceTabs.setEnabled(True)
        self.ui.sidebar.setEnabled(True)
        def prepare_task() -> tuple[list[QStandardItem] | None, ...]:
            profiler = None
            if self.settings.profileToolset and cProfile is not None:
                profiler = cProfile.Profile()
                profiler.enable()
            retTuple = (
                self._getModulesList(reload=False),
                self._getOverrideList(reload=False),
                self._getTexturePackList(reload=False),
            )
            if self.settings.profileToolset and profiler:
                profiler.disable()
                profiler.dump_stats(str(Path("prepare_task.pstat").absolute()))
            return retTuple

        prepare_loader = AsyncLoader(self, "Preparing resources...", lambda: prepare_task(), "Failed to load installation")
        if not prepare_loader.exec_():
            self.ui.gameCombo.setCurrentIndex(previousIndex)
            return

        # Any issues past this point must call self.unsetInstallation()
        try:
            self.log.debug("Set sections of prepared lists")
            moduleItems, overrideItems, textureItems = prepare_loader.value
            assert moduleItems is not None
            assert overrideItems is not None
            assert textureItems is not None
            self.ui.modulesWidget.setSections(moduleItems)
            self.ui.overrideWidget.setSections(overrideItems)
            self.ui.texturesWidget.setSections(textureItems)
            self.refreshCoreList(reload=True)
            self.refreshSavesList(reload=True)
            self.ui.texturesWidget.setInstallation(self.active)
            self.updateMenus()
            self.log.debug("Setting up watchdog observer...")
            if self.dogObserver is not None:
                self.log.debug("Stopping old watchdog service...")
                self.dogObserver.stop()
            self.dogObserver = Observer()
            self.dogObserver.schedule(self.dogHandler, self.active.path(), recursive=True)
            self.dogObserver.start()
            self.log.info("Loader task completed.")
            self.settings.installations()[name].path = path
            self.installations[name] = self.active
        except Exception as e:
            self.log.exception("Failed to initialize the installation")
            QMessageBox(
                QMessageBox.Icon.Critical,
                "An unexpected error occurred initializing the installation.",
                f"Failed to initialize the installation {name}<br><br>{e}",
            ).exec_()
            self.unsetInstallation()
        self.show()
        self.activateWindow()

    def _saveCapsuleFromToolUI(self, module_name: str):
        assert self.active is not None
        c_filepath = self.active.module_path() / module_name

        capsuleFilter = "Module (*.mod);;Encapsulated Resource File (*.erf);;Resource Image File (*.rim);;Save (*.sav);;All Capsule Types (*.erf; *.mod; *.rim; *.sav)"
        capsule_type = "mod"
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
        if not filepath_str or not filepath_str.strip():
            return
        r_save_filepath = Path(filepath_str)

        try:
            if is_mod_file(r_save_filepath):
                if capsule_type == "mod":
                    write_erf(read_erf(c_filepath), r_save_filepath)
                    QMessageBox(QMessageBox.Icon.Information, "Module Saved", f"Module saved to '{r_save_filepath}'").exec_()
                else:
                    module.rim_to_mod(r_save_filepath, self.active.module_path(), module_name, self.active.game())
                    QMessageBox(QMessageBox.Icon.Information, "Module Built", f"Module built from relevant RIMs/ERFs and saved to '{r_save_filepath}'").exec_()
                return

            erf_or_rim: ERF | RIM = read_erf(c_filepath) if is_any_erf_type_file(c_filepath) else read_rim(c_filepath)
            if is_rim_file(r_save_filepath):
                if isinstance(erf_or_rim, ERF):
                    erf_or_rim = erf_or_rim.to_rim()
                write_rim(erf_or_rim, r_save_filepath)
                QMessageBox(QMessageBox.Icon.Information, "RIM Saved", f"Resource Image File saved to '{r_save_filepath}'").exec_()

            elif is_any_erf_type_file(r_save_filepath):
                if isinstance(erf_or_rim, RIM):
                    erf_or_rim = erf_or_rim.to_erf()
                erf_or_rim.erf_type = ERFType.from_extension(r_save_filepath)
                write_erf(erf_or_rim, r_save_filepath)
                QMessageBox(QMessageBox.Icon.Information, "ERF Saved", f"Encapsulated Resource File saved to '{r_save_filepath}'").exec_()

        except Exception as e:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            RobustRootLogger().exception("Error extracting capsule %s", module_name)
            QMessageBox(QMessageBox.Icon.Critical, "Error saving capsule", str(universal_simplify_exception(e))).exec_()

    def onOpenResources(
        self,
        resources: list[FileResource],
        useSpecializedEditor: bool | None = None,
        resourceWidget: ResourceList | TextureList | None = None,
    ):
        assert self.active is not None
        for resource in resources:
            _filepath, _editor = openResourceEditor(resource.filepath(), resource.resname(), resource.restype(), resource.data(reload=True),
                                                    self.active, self, gff_specialized=useSpecializedEditor)
        if resources:
            return
        if not isinstance(resourceWidget, ResourceList):
            return
        filename = resourceWidget.currentSection()
        if not filename:
            return
        erf_filepath = self.active.module_path() / filename
        if not erf_filepath.safe_isfile():
            self.log.info(f"Not loading '{erf_filepath}'. File does not exist")
            return
        res_ident = ResourceIdentifier.from_path(erf_filepath)
        if not res_ident.restype:
            self.log.info(f"Not loading '{erf_filepath}'. Invalid resource")
            return
        _filepath, _editor = openResourceEditor(erf_filepath, res_ident.resname, res_ident.restype, BinaryReader.load_file(erf_filepath),
                                                self.active, self, gff_specialized=useSpecializedEditor)

    # FileSearcher/FileResults
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
        assert self.active is not None
        # Open relevant tab then select resource in the tree
        if selection.filepath().is_relative_to(self.active.module_path()):
            self.ui.resourceTabs.setCurrentIndex(1)
            self.selectResource(self.ui.modulesWidget, selection)
        elif selection.filepath().is_relative_to(self.active.override_path()):
            self.ui.resourceTabs.setCurrentIndex(2)
            self.selectResource(self.ui.overrideWidget, selection)
        elif is_bif_file(selection.filepath().name):
            self.selectResource(self.ui.coreWidget, selection)

    # endregion

    # region Events
    def closeEvent(self, e: QCloseEvent | None):
        self.ui.texturesWidget.doTerminations()
        instance = QCoreApplication.instance()
        if instance is None:
            print("QCoreApplication.instance() returned None for some reason... calling sys.exit() directly.")
            sys.exit()
        else:
            print("ToolWindow closed, shutting down the app.")
            instance.quit()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        return self.focusHandler.eventFilter(obj, event)

    # Overriding mouse event handlers to enable dragging of the window
    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton:
            # Calculate how much the mouse has been moved
            currPos = self.mapToGlobal(self.pos())
            globalPos = event.globalPos()
            if getattr(self, "_mouseMovePos", None) is None:
                return
            diff = globalPos - self._mouseMovePos
            newPos = self.mapFromGlobal(currPos + diff)

            # Move the window
            self.move(newPos)

            # Update the position for the next move
            self._mouseMovePos = globalPos

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._mousePressPos = event.globalPos()
            self._mouseMovePos = event.globalPos()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._mousePressPos = None
            self._mouseMovePos = None

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in [Qt.Key_Tab, Qt.Key_Backtab]:
            self.focusHandler.handleTabNavigation(event)
        else:
            super().keyPressEvent(event)

    def dropEvent(self, e: QtGui.QDropEvent | None):
        if e is None:
            return
        if not e.mimeData().hasUrls():
            return
        for url in e.mimeData().urls():
            filepath: str = url.toLocalFile()
            data = BinaryReader.load_file(filepath)
            resname, restype = ResourceIdentifier.from_path(filepath).unpack()
            if not restype:
                self.log.info(f"Not loading dropped file '{filepath}'. Invalid resource")
                continue
            openResourceEditor(filepath, resname, restype, data, self.active, self,
                               gff_specialized=GlobalSettings().gff_specializedEditors)

    def dragEnterEvent(self, e: QtGui.QDragEnterEvent | None):
        if e is None:
            return
        if not e.mimeData().hasUrls():
            return
        for url in e.mimeData().urls():
            filepath = url.toLocalFile()
            _resref, restype = ResourceIdentifier.from_path(filepath).unpack()
            if not restype:
                self.log.info(f"Not loading dragged file '{filepath}'. Invalid resource")
                continue
            e.accept()

    # endregion

    # region Menu Bar
    def updateMenus(self):
        self.log.debug("Updating menus...")
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
        if self.active is None:
            QMessageBox(QMessageBox.Icon.Information, "No installation loaded.", "Load an installation before opening the Module Designer.").exec_()
            return
        # Retrieve the icon from self (assuming it's set as window icon)
        window_icon = self.windowIcon()

        # Initialize the designer and set its window icon
        designer = ModuleDesigner(None, self.active)
        designer.setWindowIcon(window_icon)
        addWindow(designer)

    def openSettingsDialog(self):
        """Opens the Settings dialog and refresh installation combo list if changes."""
        dialog = SettingsDialog(self)
        if dialog.exec_() and dialog.installationEdited:
            result = QMessageBox(
                QMessageBox.Icon.Question,
                "Reload the installations?",
                "You appear to have made changes to your installations, would you like to reload?",
                QMessageBox.Yes | QMessageBox.No,
                flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,
            ).exec_()
            if result == QMessageBox.Yes:
                self.reloadSettings()

    def openActiveTalktable(self):
        """Opens the talktable for the active (currently selected) installation.

        If there is no active information, show a message box instead.
        """
        if self.active is None:
            QMessageBox(QMessageBox.Icon.Information, "No installation loaded.", "Load an installation before opening the TalkTable Editor.").exec_()
            return
        filepath = self.active.path() / "dialog.tlk"
        data = BinaryReader.load_file(filepath)
        openResourceEditor(filepath, "dialog", ResourceType.TLK, data, self.active, self)

    def openActiveJournal(self):
        if self.active is None:
            QMessageBox(QMessageBox.Icon.Information, "No installation loaded.", "Load an installation before opening the Journal Editor.").exec_()
            return
        res = self.active.resource(
            "global",
            ResourceType.JRL,
            [SearchLocation.OVERRIDE, SearchLocation.CHITIN],
        )
        if res is None:
            QMessageBox(QMessageBox.Icon.Critical, "global.jrl not found", "Could not open the journal editor: 'global.jrl' not found.").exec_()
            return
        openResourceEditor(res.filepath, "global", ResourceType.JRL, res.data, self.active, self)

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

    # endregion


    # region updates

    def checkForUpdates(self, *, silent: bool = False):
        """Scans for any updates and opens a dialog with a message based on the scan result.

        Args:
        ----
            silent: If true, only shows popup if an update is available.
        """
        try:
            self._check_toolset_update(silent=silent)
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            self.log.exception("Failed to check for updates.")
            if not silent:
                etype, msg = universal_simplify_exception(e)
                QMessageBox(QMessageBox.Icon.Information, f"Unable to fetch latest version ({etype})",
                            f"Check if you are connected to the internet.\nError: {msg}", QMessageBox.Ok, self).exec_()

    def _check_toolset_update(self, *, silent: bool):
        def get_latest_version_info() -> tuple[dict[str, Any], dict[str, Any]]:
            edge_info = None
            if self.settings.useBetaChannel:
                edge_info = getRemoteToolsetUpdateInfo(useBetaChannel=True, silent=silent)
                if not isinstance(edge_info, dict):
                    if silent:
                        edge_info = None
                    else:
                        raise edge_info

            master_info = getRemoteToolsetUpdateInfo(useBetaChannel=False, silent=silent)
            if not isinstance(master_info, dict):
                if silent:
                    master_info = None
                else:
                    raise master_info

            return master_info, edge_info

        def determine_version_info(
            edgeRemoteInfo: dict[str, Any],
            masterRemoteInfo: dict[str, Any],
        ) -> tuple[dict[str, Any], bool]:
            version_list: list[tuple[Literal["toolsetLatestVersion", "toolsetLatestBetaVersion"], Literal["master", "edge"], str]] = []

            if self.settings.useBetaChannel:
                version_list.append(("toolsetLatestVersion", "master", masterRemoteInfo.get("toolsetLatestVersion", "")))
                version_list.append(("toolsetLatestVersion", "edge", edgeRemoteInfo.get("toolsetLatestVersion", "")))
                version_list.append(("toolsetLatestBetaVersion", "master", masterRemoteInfo.get("toolsetLatestBetaVersion", "")))
                version_list.append(("toolsetLatestBetaVersion", "edge", edgeRemoteInfo.get("toolsetLatestBetaVersion", "")))
            else:
                version_list.append(("toolsetLatestVersion", "master", masterRemoteInfo.get("toolsetLatestVersion", "")))

            # Sort the version list using remoteVersionNewer to determine order
            version_list.sort(key=lambda x: bool(remoteVersionNewer("0.0.0", x[2])))

            releaseVersion = version_list[0][0] == "toolsetLatestVersion"
            remoteInfo = edgeRemoteInfo if version_list[0][1] == "edge" else masterRemoteInfo
            return remoteInfo, releaseVersion

        def display_version_message(
            is_up_to_date: bool,  # noqa: FBT001
            cur_version_str: str,
            greatest_version: str,
            notes: str,
            download_link: str,
        ):
            if is_up_to_date:
                if silent:
                    return
                up_to_date_msg_box = QMessageBox(
                    QMessageBox.Icon.Information, "Version is up to date",
                    f"You are running the latest {cur_version_str}version ({CURRENT_VERSION}).",
                    QMessageBox.Ok | QMessageBox.Close, parent=None,
                    flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint
                )
                up_to_date_msg_box.button(QMessageBox.Ok).setText("Reinstall?")
                up_to_date_msg_box.setWindowIcon(self.windowIcon())
                result = up_to_date_msg_box.exec_()
                if result == QMessageBox.Ok:
                    toolset_updater = UpdateDialog(self)
                    toolset_updater.exec_()
                return
            beta_string = "release " if release_version_checked else "beta "
            new_version_msg_box = QMessageBox(
                QMessageBox.Icon.Information,
                f"Your toolset version {CURRENT_VERSION} is outdated.",
                f"A new toolset {beta_string}version ({greatest_version}) is available for <a href='{download_link}'>download</a>.<br><br>{notes}",
                QMessageBox.Yes | QMessageBox.Abort, parent=None,
                flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint
            )
            new_version_msg_box.setDefaultButton(QMessageBox.Abort)
            new_version_msg_box.button(QMessageBox.Yes).setText("Open")
            new_version_msg_box.button(QMessageBox.Abort).setText("Ignore")
            new_version_msg_box.setWindowIcon(self.windowIcon())
            response = new_version_msg_box.exec_()
            if response == QMessageBox.Ok:
                self.autoupdate_toolset(greatest_version, edge_info, isRelease=release_version_checked)
            elif response == QMessageBox.Yes:
                toolset_updater = UpdateDialog(self)
                toolset_updater.exec_()

        master_info, edge_info = get_latest_version_info()
        if edge_info is None:
            return

        remote_info, release_version_checked = determine_version_info(edge_info, master_info)
        greatest_available_version = remote_info["toolsetLatestVersion"] if release_version_checked else remote_info["toolsetLatestBetaVersion"]
        toolset_latest_notes = remote_info.get("toolsetLatestNotes", "") if release_version_checked else remote_info.get("toolsetBetaLatestNotes", "")
        toolset_download_link = remote_info["toolsetDownloadLink"] if release_version_checked else remote_info["toolsetBetaDownloadLink"]

        version_check = remoteVersionNewer(CURRENT_VERSION, greatest_available_version)
        cur_version_beta_release_str = ""
        if remote_info["toolsetLatestVersion"] == CURRENT_VERSION:
            cur_version_beta_release_str = "release "
        elif remote_info["toolsetLatestBetaVersion"] == CURRENT_VERSION:
            cur_version_beta_release_str = "beta "

        display_version_message(version_check is False, cur_version_beta_release_str, greatest_available_version,
                                toolset_latest_notes, toolset_download_link)

    def autoupdate_toolset(
        self,
        latestVersion: str,
        remoteInfo: dict[str, Any],
        *,
        isRelease: bool,
    ):
        """A fast and quick way to auto-install a specific toolset version.

        Uses toolsetDirectLinks and toolsetBetaDirectLinks
        """
        proc_arch = ProcessorArchitecture.from_os()
        assert proc_arch == ProcessorArchitecture.from_python()
        os_name = platform.system()
        links: list[str] = []

        isRelease = False  # TODO(th3w1zard1): remove this line when the release version direct links are ready.
        if isRelease:
            links = remoteInfo["toolsetDirectLinks"][os_name][proc_arch.value]
        else:
            links = remoteInfo["toolsetBetaDirectLinks"][os_name][proc_arch.value]
        progress_queue = Queue()
        progress_process = Process(target=run_progress_dialog, args=(progress_queue, "Holocron Toolset is updating and will restart shortly..."))
        progress_process.start()
        self.hide()

        def download_progress_hook(
            data: dict[str, Any],
            progress_queue: Queue = progress_queue,
        ):
            progress_queue.put(data)

        # Prepare the list of progress hooks with the method from ProgressDialog
        progress_hooks = [download_progress_hook]
        def exitapp(kill_self_here: bool):  # noqa: FBT001
            packaged_data = {"action": "shutdown", "data": {}}
            progress_queue.put(packaged_data)
            ProgressDialog.monitor_and_terminate(progress_process)
            if kill_self_here:
                sys.exit(0)

        updater = AppUpdate(links, "HolocronToolset", CURRENT_VERSION, latestVersion,
                            downloader=None, progress_hooks=progress_hooks, exithook=exitapp)  # type: ignore[arg-type]
        try:
            progress_queue.put({"action": "update_status", "text": "Downloading update..."})
            updater.download(background=False)
            progress_queue.put({"action": "update_status", "text": "Restarting and Applying update..."})
            updater.extract_restart()
            progress_queue.put({"action": "update_status", "text": "Cleaning up..."})
            updater.cleanup()
        except Exception as e:
            self.log.exception("Failed to complete the updater")
        finally:
            exitapp(True)

    # endregion


    # region Other

    def getActiveTabIndex(self) -> int:
        return self.ui.resourceTabs.currentIndex()

    def getActiveResourceTab(self) -> QWidget:
        return self.ui.resourceTabs.currentWidget()

    def getActiveResourceWidget(self) -> ResourceList | TextureList:
        currentWidget = self.getActiveResourceTab()
        if currentWidget is self.ui.coreTab:
            return self.ui.coreWidget
        if currentWidget is self.ui.modulesTab:
            return self.ui.modulesWidget
        if currentWidget is self.ui.overrideTab:
            return self.ui.overrideWidget
        if currentWidget is self.ui.texturesTab:
            return self.ui.texturesWidget
        if currentWidget is self.ui.savesTab:
            return self.ui.savesWidget
        raise ValueError(f"Unknown current widget: {currentWidget}")

    def reloadSettings(self):
        self.reloadInstallations()

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
            assert self.active is not None
            self.ui.resourceTabs.setCurrentWidget(self.ui.overrideTab)
            self.ui.overrideWidget.setResourceSelection(resource)
            subfolder: str = "."
            for folder_name in self.active.override_list():
                folder_path: CaseAwarePath = self.active.override_path() / folder_name
                if resource.filepath().is_relative_to(folder_path) and len(subfolder) < len(folder_path.name):
                    subfolder = folder_name
            self.changeOverrideFolder(subfolder)

        elif tree == self.ui.savesWidget:
            self.ui.resourceTabs.setCurrentWidget(self.ui.savesTab)
            filename = resource.filepath().name
            self.onSaveReload(filename)

    def reloadInstallations(self):
        """Refresh the list of installations available in the combobox."""
        self.ui.gameCombo.currentIndexChanged.disconnect(self.changeActiveInstallation)
        self.ui.gameCombo.clear()  # without above disconnect, would call ToolWindow().changeActiveInstallation(-1)
        self.ui.gameCombo.addItem("[None]")  # without above disconnect, would call ToolWindow().changeActiveInstallation(0)

        for installation in self.settings.installations().values():
            self.ui.gameCombo.addItem(installation.name)
        self.ui.gameCombo.currentIndexChanged.connect(self.changeActiveInstallation)  # without above disconnect, would NOT call changeActiveInstallation

    def unsetInstallation(self):

        self.ui.gameCombo.setCurrentIndex(0)

        self.ui.coreWidget.setResources([])
        self.ui.modulesWidget.setSections([])
        self.ui.modulesWidget.setResources([])
        self.ui.overrideWidget.setSections([])
        self.ui.overrideWidget.setResources([])

        self.ui.resourceTabs.setEnabled(False)
        self.ui.sidebar.setEnabled(False)
        self.updateMenus()
        self.active = None
        if self.dogObserver is not None:
            self.dogObserver.stop()
            self.dogObserver = None

    # endregion

    # region ResourceList handlers

    def refreshCoreList(self, *, reload: bool = True):
        """Rebuilds the tree in the Core tab. Used with the flatten/unflatten logic."""
        if self.active is None:
            print("no installation is currently loaded, cannot refresh core list")
            return
        self.log.debug("Loading core installation resources into UI...")
        self.ui.coreWidget.setResources(self.active.chitin_resources())
        self.log.debug("Remove unused categories...")
        self.ui.coreWidget.modulesModel.removeUnusedCategories()

    def changeModule(self, moduleName: str):
        # Some users may choose to merge their RIM files under one option in the Modules tab; if this is the case we
        # need to account for this.
        if self.settings.joinRIMsTogether:
            if moduleName.casefold().endswith("_s.rim"):
                moduleName = f"{moduleName[:-6]}.rim"
            if moduleName.casefold().endswith("_dlg.erf"):
                moduleName = f"{moduleName[:-8]}.rim"

        self.ui.modulesWidget.changeSection(moduleName)

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

    def _getModulesList(self, *, reload: bool = True) -> list[QStandardItem]:
        if self.active is None:
            print("No installation is currently loaded, cannot refresh modules list")
            return []
        profiler = None
        if self.settings.profileToolset and cProfile is not None:
            profiler = cProfile.Profile()
            profiler.enable()
        # If specified the user can forcibly reload the resource list for every module
        if reload:
            self.active.load_modules()

        areaNames: dict[str, str] = self.active.module_names()

        def sortAlgo(moduleFileName: str) -> str:
            lowerModuleFileName = moduleFileName.lower()
            if "stunt" in lowerModuleFileName:  # keep the stunt modules at the bottom.
                sortStr = "zzzzz"
            elif self.settings.moduleSortOption == 0:  # "Sort by filename":
                sortStr = ""
            elif self.settings.moduleSortOption == 1:  # "Sort by humanized area name":
                sortStr = areaNames.get(moduleFileName, "y").lower()
            else:  # alternate mod id that attempts to match to filename.
                sortStr = self.active.module_id(moduleFileName, use_alternate=True)
            sortStr += f"_{lowerModuleFileName}".lower()
            return sortStr

        sortedKeys: list[str] = sorted(areaNames, key=sortAlgo)

        modules: list[QStandardItem] = []
        for moduleName in sortedKeys:
            # Some users may choose to have their RIM files for the same module merged into a single option for the
            # dropdown menu.
            lower_module_name = moduleName.lower()
            if self.settings.joinRIMsTogether:
                if lower_module_name.endswith("_s.rim"):
                    continue
                if self.active.game().is_k2() and lower_module_name.endswith("_dlg.erf"):
                    continue

            item = QStandardItem(f"{areaNames[moduleName]} [{moduleName}]")
            item.setData(moduleName, Qt.UserRole)
            item.setData(areaNames[moduleName]+"\n"+moduleName, Qt.DisplayRole)  # Set area name
            item.setData(moduleName, Qt.UserRole + 11)  # Set module name

            # Some users may choose to have items representing RIM files to have grey text.
            if self.settings.greyRIMText and lower_module_name.endswith(("_dlg.erf", ".rim")):
                item.setForeground(self.palette().shadow())

            modules.append(item)
        if self.settings.profileToolset and profiler:
            profiler.disable()
            profiler.dump_stats(str(Path("main_getModulesList.pstat").absolute()))
        return modules

    def changeOverrideFolder(self, subfolder: str):
        self.ui.overrideWidget.changeSection(subfolder)

    def _getOverrideList(self, *, reload: bool = True) -> list[QStandardItem]:
        if self.active is None:
            print("No installation is currently loaded, cannot refresh override list")
            return []
        if reload:
            self.active.load_override()

        sections: list[QStandardItem] = []
        for directory in self.active.override_list():
            section = QStandardItem(directory if directory.strip() else "[Root]")
            section.setData(directory, QtCore.Qt.ItemDataRole.UserRole)
            sections.append(section)
        return sections

    def refreshOverrideList(
        self,
        *,
        reload: bool = True,
        overrideItems: list[QStandardItem] | None = None,
    ):
        """Refreshes the list of override directories in the overrideFolderCombo combobox."""
        if not overrideItems:
            action = "Reloading" if reload else "Refreshing"

            def task() -> list[QStandardItem]:
                return self._getOverrideList()

            loader = AsyncLoader(self, f"{action} override list...", task, f"Error {action}ing override list.")
            loader.exec_()
            overrideItems = loader.value
        self.ui.overrideWidget.setSections(overrideItems)

    def _getTexturePackList(self, *, reload: bool = True) -> list[QStandardItem] | None:
        if self.active is None:
            print("No installation is currently loaded, cannot refresh texturepack list")
            return None
        if reload:
            self.active.load_textures()

        sections = []
        for texturepack in self.active.texturepacks_list():
            section = QStandardItem(texturepack)
            section.setData(texturepack, QtCore.Qt.ItemDataRole.UserRole)
            sections.append(section)
        return sections

    def refreshTexturePackList(self, *, reload: bool = True):
        sections = self._getTexturePackList(reload=reload)
        if sections is None:
            self.log.error("sections was somehow None in refreshTexturePackList(reload=%s)", reload, stack_info=True)
            return
        self.ui.texturesWidget.setSections(sections)

    def refreshSavesList(self, *, reload=True):
        """Refreshes the list of override directories in the overrideFolderCombo combobox."""
        self.log.info("Loading saves list into UI...")
        if self.active is None:
            print("No installation is currently loaded, cannot refresh saves list")
            return
        if reload:
            self.active.load_saves()

        sections: list[QStandardItem] = []
        for save_path in self.active._saves:
            save_path_str = str(save_path)
            section = QStandardItem(save_path_str)
            section.setData(save_path_str, QtCore.Qt.UserRole)
            sections.append(section)
        self.ui.savesWidget.setSections(sections)

    # endregion

    # region Extract

    def onExtractResources(
        self,
        selectedResources: list[FileResource],
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
        if selectedResources:
            folder_path, paths_to_write = self.build_extract_save_paths(selectedResources)
            if folder_path is None or paths_to_write is None:
                RobustRootLogger.debug("No paths to write: user must have cancelled the getExistingDirectory dialog.")
                return
            failed_savepath_handlers: dict[Path, Exception] = {}
            resource_save_paths = FileSaveHandler(selectedResources).determine_save_paths(paths_to_write, failed_savepath_handlers)
            if not resource_save_paths:
                RobustRootLogger.debug("No resources returned from FileSaveHandler.determine_save_paths")
                return
            loader = AsyncBatchLoader(self, "Extracting Resources", [], "Failed to Extract Resources")
            loader.errors.extend(failed_savepath_handlers.values())

            for resource, save_path in resource_save_paths.items():
                loader.addTask(lambda res=resource, fp=save_path: self._extractResource(res, fp, loader))

            loader.exec_()
            qInstance = QApplication.instance()
            if qInstance is None:
                return
            if QThread.currentThread() == qInstance.thread():
                msgBox = QMessageBox(
                    QMessageBox.Icon.Information,
                    "Extraction successful.",
                    f"Successfully saved {len(paths_to_write)} files to {folder_path}",
                    flags=Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint
                )
                msgBox.setDetailedText("\n".join(str(p) for p in resource_save_paths.values()))
                msgBox.exec_()
        elif isinstance(resourceWidget, ResourceList) and is_capsule_file(resourceWidget.currentSection()):
            module_name = resourceWidget.currentSection()
            self._saveCapsuleFromToolUI(module_name)

    def build_extract_save_paths(self, resources: list[FileResource]) -> tuple[Path, dict[FileResource, Path]] | tuple[None, None]:
        # TODO(th3w1zard1): currently doesn't handle tpcTxiCheckbox.isChecked() or mdlTexturesCheckbox.isChecked()
        paths_to_write: dict[FileResource, Path] = {}

        folderpath_str: str = QFileDialog.getExistingDirectory(self, "Extract to folder")
        if not folderpath_str or not folderpath_str.strip():
            RobustRootLogger.debug("User cancelled folderpath extraction.")
            return None, None

        folder_path = Path(folderpath_str)
        for resource in resources:
            identifier = resource.identifier()
            save_path = folder_path / str(identifier)

            # Determine the final save path based on UI checks
            if resource.restype() is ResourceType.TPC and self.ui.tpcDecompileCheckbox.isChecked():
                save_path = save_path.with_suffix(".tga")
            elif resource.restype() is ResourceType.MDL and self.ui.mdlDecompileCheckbox.isChecked():
                save_path = save_path.with_suffix(".ascii.mdl")

            paths_to_write[resource] = save_path

        return folder_path, paths_to_write

    def _extractResource(self, resource: FileResource, save_path: Path, loader: AsyncBatchLoader):
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
        r_folderpath: Path = save_path.parent

        data: bytes = resource.data()

        if resource.restype() is ResourceType.MDX and self.ui.mdlDecompileCheckbox.isChecked():
            RobustRootLogger.info(f"Not extracting MDX file '{resource.identifier()}', decompiling MDLs is checked.")
            return

        if resource.restype() is ResourceType.TPC:
            tpc: TPC = read_tpc(data, txi_source=save_path)

            if self.ui.tpcTxiCheckbox.isChecked():
                RobustRootLogger.info(f"Extracting TXI from {resource.identifier()} because of settings.")
                self._extractTxi(tpc, save_path.with_suffix(".txi"))

            if self.ui.tpcDecompileCheckbox.isChecked():
                RobustRootLogger.info(f"Converting '{resource.identifier()}' to TGA because of settings.")
                data = self._decompileTpc(tpc)

        if resource.restype() is ResourceType.MDL:
            if self.ui.mdlTexturesCheckbox.isChecked():
                RobustRootLogger.info(f"Extracting MDL Textures because of settings: {resource.identifier()}")
                self._extractMdlTextures(resource, r_folderpath, loader, data)

            if self.ui.mdlDecompileCheckbox.isChecked():
                RobustRootLogger.info(f"Converting {resource.identifier()} to ASCII MDL because of settings")
                data = self._decompileMdl(resource, data)

        with save_path.open("wb") as file:
            RobustRootLogger.info(f"Saving extracted data of '{resource.identifier()}' to '{save_path}'")
            file.write(data)

    def _extractTxi(self, tpc: TPC, filepath: Path):
        with filepath.open("wb") as file:
            file.write(tpc.txi.encode("ascii"))

    def _decompileTpc(self, tpc: TPC) -> bytearray:
        data = bytearray()
        write_tpc(tpc, data, ResourceType.TGA)
        return data

    def _decompileMdl(self, resource: FileResource, data: SOURCE_TYPES) -> bytearray:
        assert self.active is not None
        reslookup: ResourceResult | None = self.active.resource(resource.resname(), ResourceType.MDX)
        if reslookup is None:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), repr(resource))
        mdxData: bytes = reslookup.data
        mdl: MDL | None = read_mdl(data, 0, 0, mdxData, 0, 0)
        data = bytearray()
        write_mdl(mdl, data, ResourceType.MDL_ASCII)
        return data

    def _extractMdlTextures(self, resource: FileResource, folderpath: Path, loader: AsyncBatchLoader, data: bytes):
        assert self.active is not None
        for texture in model.list_textures(data):
            try:
                tpc: TPC | None = self.active.texture(texture)
                if tpc is None:
                    raise ValueError(texture)  # noqa: TRY301
                if self.ui.tpcTxiCheckbox.isChecked():
                    self._extractTxi(tpc, folderpath.joinpath(f"{texture}.txi"))

                file_format = ResourceType.TGA if self.ui.tpcDecompileCheckbox.isChecked() else ResourceType.TPC
                extension = "tga" if file_format is ResourceType.TGA else "tpc"
                write_tpc(tpc, folderpath.joinpath(f"{texture}.{extension}"), file_format)
            except Exception as e:  # noqa: PERF203
                etype, msg = universal_simplify_exception(e)
                loader.errors.append(e.__class__(f"Could not find or extract tpc: '{texture}'"))

    def openFromFile(self):
        filepaths = QFileDialog.getOpenFileNames(self, "Select files to open")[:-1][0]

        for filepath in filepaths:
            r_filepath = Path(filepath)
            try:
                with r_filepath.open("rb") as file:
                    data = file.read()
                openResourceEditor(filepath, *ResourceIdentifier.from_path(r_filepath).validate().unpack(), data, self.active, self)
            except (ValueError, OSError) as e:
                etype, msg = universal_simplify_exception(e)
                QMessageBox(QMessageBox.Icon.Critical, f"Failed to open file ({etype})", msg).exec_()

    # endregion


class FolderObserver(FileSystemEventHandler):
    def __init__(self, window: ToolWindow):
        self.window: ToolWindow = window
        self.lastModified: datetime = datetime.now(tz=timezone.utc).astimezone()

    def on_any_event(self, event: FileSystemEvent):
        if self.window.active is None:
            return
        rightnow: datetime = datetime.now(tz=timezone.utc).astimezone()
        if rightnow - self.lastModified < timedelta(seconds=1):
            return

        self.lastModified = rightnow
        modified_path: Path = Path(event.src_path)

        module_path: Path = self.window.active.module_path()
        override_path: Path = self.window.active.override_path()

        if modified_path.is_relative_to(module_path):
            self.window.moduleFilesUpdated.emit(str(modified_path), event.event_type)
        elif modified_path.is_relative_to(override_path):
            self.window.overrideFilesUpdate.emit(str(modified_path), event.event_type)
        else:
            print(f"Watchdog passed unknown file: {modified_path}")
