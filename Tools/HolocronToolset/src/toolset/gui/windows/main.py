from __future__ import annotations

import cProfile
import errno
import os
import platform
import struct
import sys

from datetime import datetime, timedelta, timezone
from multiprocessing import Process, Queue
from typing import TYPE_CHECKING, Any, cast

import qtpy

from qtpy import QtCore
from qtpy.QtCore import (
    QCoreApplication,
    QEvent,
    QFile,
    QSize,
    QTextStream,
    QThread,
    QTimer,
    Qt,
)
from qtpy.QtGui import (
    QColor,
    QFontMetrics,
    QIcon,
    QPalette,
    QPixmap,
    QStandardItem,
)
from qtpy.QtWidgets import (
    QAbstractItemView,
    QAction,
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListView,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStyle,
    QToolButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)
from watchdog.events import FileSystemEventHandler

from pykotor.common.stream import BinaryReader
from pykotor.extract.file import FileResource, ResourceIdentifier, ResourceResult
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.erf.erf_auto import read_erf, write_erf
from pykotor.resource.formats.erf.erf_data import ERF, ERFType
from pykotor.resource.formats.mdl import read_mdl, write_mdl
from pykotor.resource.formats.rim.rim_auto import read_rim, write_rim
from pykotor.resource.formats.rim.rim_data import RIM
from pykotor.resource.formats.tpc import TPC, read_tpc, write_tpc
from pykotor.resource.formats.tpc.tpc_auto import bytes_tpc
from pykotor.resource.type import ResourceType
from pykotor.tools import model, module
from pykotor.tools.misc import is_any_erf_type_file, is_bif_file, is_capsule_file, is_erf_file, is_mod_file, is_rim_file
from pykotor.tools.path import CaseAwarePath
from toolset.config import CURRENT_VERSION, getRemoteToolsetUpdateInfo, remoteVersionNewer
from toolset.data.installation import HTInstallation
from toolset.gui.common.widgets.combobox import FilterComboBox
from toolset.gui.dialogs.about import About
from toolset.gui.dialogs.asyncloader import AsyncBatchLoader, AsyncLoader, ProgressDialog
from toolset.gui.dialogs.clone_module import CloneModuleDialog
from toolset.gui.dialogs.load_from_location_result import FileSelectionWindow
from toolset.gui.dialogs.save.generic_file_saver import FileSaveHandler
from toolset.gui.dialogs.search import FileResults, FileSearcher
from toolset.gui.dialogs.select_update import UpdateDialog, run_progress_dialog
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
from toolset.gui.helpers.callback import BetterMessageBox
from toolset.gui.helpers.main_focus_helper import MainFocusHandler
from toolset.gui.widgets.main_widgets import ResourceList
from toolset.gui.widgets.settings.misc import GlobalSettings
from toolset.gui.windows.help import HelpWindow
from toolset.gui.windows.indoor_builder import IndoorMapBuilder
from toolset.gui.windows.module_designer import ModuleDesigner
from toolset.utils.misc import openLink
from toolset.utils.window import addWindow, openResourceEditor
from ui import stylesheet_resources  # noqa: F401
from utility.error_handling import universal_simplify_exception
from utility.logger_util import RobustRootLogger
from utility.misc import ProcessorArchitecture, is_debug_mode
from utility.system.path import Path, PurePath
from utility.tricks import debug_reload_pymodules
from utility.updater.update import AppUpdate

if qtpy.API_NAME == "PySide2":
    from toolset.rcc import resources_rc_pyside2  # noqa: PLC0415, F401  # pylint: disable=C0415
elif qtpy.API_NAME == "PySide6":
    from toolset.rcc import resources_rc_pyside6  # noqa: PLC0415, F401  # pylint: disable=C0415
elif qtpy.API_NAME == "PyQt5":
    from toolset.rcc import resources_rc_pyqt5  # noqa: PLC0415, F401  # pylint: disable=C0415
elif qtpy.API_NAME == "PyQt6":
    from toolset.rcc import resources_rc_pyqt6  # noqa: PLC0415, F401  # pylint: disable=C0415
else:
    raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

if TYPE_CHECKING:

    from qtpy import QtGui
    from qtpy.QtCore import (
        QObject,
    )
    from qtpy.QtGui import (
        QCloseEvent,
        QKeyEvent,
        QMouseEvent,
        QShowEvent,
    )
    from typing_extensions import Literal
    from watchdog.events import FileSystemEvent
    from watchdog.observers.api import BaseObserver

    from pykotor.extract.file import LocationResult
    from pykotor.resource.formats.mdl.mdl_data import MDL
    from pykotor.resource.type import SOURCE_TYPES
    from toolset.gui.widgets.main_widgets import TextureList
    from utility.common.more_collections import CaseInsensitiveDict

def run_module_designer(
    active_path: str,
    active_name: str,
    active_tsl: bool,
    module_path: str | None = None,
):
    """An alternative way to start the ModuleDesigner: run this function in a new process so the main tool window doesn't wait on the module designer."""
    from toolset.__main__ import main_init
    main_init()
    app = QApplication([])
    designerUi = ModuleDesigner(
        None,
        HTInstallation(active_path, active_name, tsl=active_tsl),
        CaseAwarePath(module_path) if module_path is not None else None,
    )
    # Standardized resource path format
    icon_path = ":/images/icons/sith.png"

    # Debugging: Check if the resource path is accessible
    if not QPixmap(icon_path).isNull():
        designerUi.log.debug(f"HT main window Icon loaded successfully from {icon_path}")
        designerUi.setWindowIcon(QIcon(QPixmap(icon_path)))
        cast(QApplication, QApplication.instance()).setWindowIcon(QIcon(QPixmap(icon_path)))
    else:
        print(f"Failed to load HT main window icon from {icon_path}")
    addWindow(designerUi, show=False)
    sys.exit(app.exec_())


class CustomTitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAutoFillBackground(True)
        self.setBackgroundRole(QPalette.ColorRole.Highlight)
        self.initial_pos = None
        title_bar_layout = QHBoxLayout(self)
        title_bar_layout.setContentsMargins(1, 1, 1, 1)
        title_bar_layout.setSpacing(2)

        self.title = QLabel(f"{self.__class__.__name__}", self)
        self.title.setStyleSheet(
            """font-weight: bold;
               border: 2px solid black;
               border-radius: 12px;
               margin: 2px;
            """
        )
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = parent.windowTitle()
        if title:
            self.title.setText(title)
        title_bar_layout.addWidget(self.title)
        # Min button
        self.min_button = QToolButton(self)
        min_icon = self.style().standardIcon(
            QStyle.StandardPixmap.SP_TitleBarMinButton
        )
        self.min_button.setIcon(min_icon)
        self.min_button.clicked.connect(self.window().showMinimized)

        # Max button
        self.max_button = QToolButton(self)
        max_icon = self.style().standardIcon(
            QStyle.StandardPixmap.SP_TitleBarMaxButton
        )
        self.max_button.setIcon(max_icon)
        self.max_button.clicked.connect(self.window().showMaximized)

        # Close button
        self.close_button = QToolButton(self)
        close_icon = self.style().standardIcon(
            QStyle.StandardPixmap.SP_TitleBarCloseButton
        )
        self.close_button.setIcon(close_icon)
        self.close_button.clicked.connect(self.window().close)

        # Normal button
        self.normal_button = QToolButton(self)
        normal_icon = self.style().standardIcon(
            QStyle.StandardPixmap.SP_TitleBarNormalButton
        )
        self.normal_button.setIcon(normal_icon)
        self.normal_button.clicked.connect(self.window().showNormal)
        self.normal_button.setVisible(False)
        # Add buttons
        buttons = [
            self.min_button,
            self.normal_button,
            self.max_button,
            self.close_button,
        ]
        for button in buttons:
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button.setFixedSize(QSize(28, 28))
            button.setStyleSheet(
                """QToolButton { border: 2px solid white;
                                 border-radius: 12px;
                                }
                """
            )
            title_bar_layout.addWidget(button)

    def window_state_changed(self, state):
        if state == Qt.WindowState.WindowMaximized:
            self.normal_button.setVisible(True)
            self.max_button.setVisible(False)
        else:
            self.normal_button.setVisible(False)
            self.max_button.setVisible(True)


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

        self.active: HTInstallation | None = None
        self.installations: dict[str, HTInstallation] = {}

        self.settings: GlobalSettings = GlobalSettings()
        self.log: RobustRootLogger = RobustRootLogger()
        self._initUi()
        self._setupSignals()
        self.setWindowTitle(f"Holocron Toolset ({qtpy.API_NAME})")

        # Watchdog
        self.dogObserver: BaseObserver | None = None
        self.dogHandler = FolderObserver(self)

        # Theme setup
        self.original_style: str = self.style().objectName()
        self.original_palette: QPalette = self.palette()
        self.change_theme(self.settings.selectedTheme)

        # Focus handler (searchbox, various keyboard actions)
        self.focusHandler: MainFocusHandler = MainFocusHandler(self)
        self.installEventFilter(self.focusHandler)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()

        # Finalize the init
        self.reloadSettings()
        self.unsetInstallation()
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

        if is_debug_mode():
            self.ui.menubar.addAction("Debug Reload").triggered.connect(debug_reload_pymodules)

        # Standardized resource path format
        icon_path = ":/images/icons/sith.png"

        # Debugging: Check if the resource path is accessible
        if not QPixmap(icon_path).isNull():
            self.log.debug(f"HT main window Icon loaded successfully from {icon_path}")
            self.setWindowIcon(QIcon(QPixmap(icon_path)))
            cast(QApplication, QApplication.instance()).setWindowIcon(QIcon(QPixmap(icon_path)))
        else:
            print(f"Failed to load HT main window icon from {icon_path}")
        self.setupModulesTab()

    def showEvent(self, event: QShowEvent):
        # Set minimum size based on the current size
        super().showEvent(event)
        #self.adjustSize()
        #self.setMinimumSize(
        #    self.size().width() + QApplication.font().pointSize() * 4,
        #    self.size().height(),
        #)

    def setupModulesTab(self):
        modulesResourceList = self.ui.modulesWidget.ui
        modulesSectionCombo: FilterComboBox = modulesResourceList.sectionCombo  # type: ignore[]
        modulesSectionCombo.__class__ = FilterComboBox
        modulesSectionCombo.__init__(init=False)
        modulesSectionCombo.setEditable(False)
        refreshButton = modulesResourceList.refreshButton
        designerButton = self.ui.specialActionButton
        self.collectButton = QPushButton("Collect...", self)

        # Remove from original layouts
        modulesResourceList.horizontalLayout_2.removeWidget(modulesSectionCombo)  # type: ignore[arg-type]
        modulesResourceList.horizontalLayout_2.removeWidget(refreshButton)  # type: ignore[arg-type]
        modulesResourceList.verticalLayout.removeItem(modulesResourceList.horizontalLayout_2)  # type: ignore[arg-type]

        # Set size policies
        modulesSectionCombo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)  # type: ignore[arg-type]
        refreshButton.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)  # type: ignore[arg-type]
        designerButton.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)  # type: ignore[arg-type]
        self.collectButton.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        modulesSectionCombo.setMinimumWidth(250)

        # Create a new layout to stack Designer and Refresh buttons
        stackButtonLayout = QVBoxLayout()
        stackButtonLayout.setSpacing(1)
        stackButtonLayout.addWidget(refreshButton)  # type: ignore[arg-type]
        stackButtonLayout.addWidget(designerButton)  # type: ignore[arg-type]
        stackButtonLayout.addWidget(self.collectButton)

        # Create a new horizontal layout to place the combobox and buttons
        topLayout = QHBoxLayout()
        topLayout.addWidget(modulesSectionCombo)  # type: ignore[arg-type]
        topLayout.addLayout(stackButtonLayout)

        # Insert the new top layout into the vertical layout
        self.ui.verticalLayoutModulesTab.insertLayout(0, topLayout)  # type: ignore[attributeAccessIssue]

        # Adjust the vertical layout to accommodate the combobox height change
        modulesResourceList.verticalLayout.addWidget(modulesResourceList.resourceTree)  # type: ignore[arg-type]
        modulesSectionCombo.setMaxVisibleItems(18)
        def create_more_actions_menu() -> QMenu:
            menu = QMenu()
            menu.addAction("Room Textures").triggered.connect(self.extractModuleRoomTextures)
            menu.addAction("Room Models").triggered.connect(self.extractModuleRoomModels)
            menu.addAction("Textures").triggered.connect(self.extractAllModuleTextures)
            menu.addAction("Models").triggered.connect(self.extractAllModuleModels)
            menu.addAction("Everything").triggered.connect(lambda: self.extractModuleEverything())
            return menu

        self.collectButtonMenu = create_more_actions_menu()
        self.collectButtonMenu.aboutToHide.connect(self.onMenuHide)
        self.collectButtonMenu.leaveEvent = self.onMenuHide  # type: ignore[attributeAccessIssue]
        self.collectButton.leaveEvent = self.onMenuHide  # type: ignore[attributeAccessIssue]
        self.collectButton.setMenu(self.collectButtonMenu)

        # Show menu on hover
        self.collectButton.setMouseTracking(False)
        self.collectButton.installEventFilter(self)

    def onMenuHide(self, *args):
        """Custom slot to handle menu hide actions."""
        self.collectButton.menu().hide()
        self.collectButtonMenu.close()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj == self.collectButton and event.type() == QEvent.Type.HoverEnter:
            self.collectButton.showMenu()
        if hasattr(self, "focusHandler"):
            return self.focusHandler.eventFilter(obj, event)
        return super().eventFilter(obj, event)

    def resize_widget_to_text(widget: QWidget):
        if isinstance(widget, QComboBox):
            # Get the current font of the widget or use the application's font
            font = widget.font()
            # Create QFontMetrics from the current font
            fm = QFontMetrics(font)
            # Calculate the required width to display the text without clipping
            required_width = fm.horizontalAdvance(widget.text())
            # Get the current size of the widget
            current_size = widget.size()
            # Determine the new width (max of current and required)
            new_width = max(required_width, current_size.width())
            # Set the new size with the same height
            widget.setMinimumSize(new_width, current_size.height())

    def _setupSignals(self):  # sourcery skip: remove-unreachable-code
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

        self.ui.menuTheme.triggered.connect(self.change_theme)

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
        self.ui.resourceTabs.currentChanged.connect(self.onTabChanged)

        def openModuleDesigner() -> ModuleDesigner | None:
            assert self.active is not None

            # Uncomment this block to start Module Designer in new process
            #import multiprocessing
            #module_path = self.active.module_path() / self.ui.modulesWidget.currentSection()
            #print("<SDM> [openModuleDesigner scope] module_path: ", module_path)

            #process = multiprocessing.Process(target=run_module_designer, args=(str(self.active.path()), self.active.name, self.active.tsl, str(module_path)))
            #print("<SDM> [openModuleDesigner scope] process: ", process)

            #process.start()
            #BetterMessageBox("Module designer process started", "We have triggered the module designer to open, feel free to use the toolset in the meantime.").exec_()
            #QTimer.singleShot(500, self.debounceModuleDesignerLoad)
            #return None

            designerUi = (
                ModuleDesigner(
                    None,
                    self.active,
                    self.active.module_path() / self.ui.modulesWidget.currentSection(),
                )
            )

            icon_path = ":/images/icons/sith.png"
            if not QPixmap(icon_path).isNull():
                self.log.debug(f"Module Designer window Icon loaded successfully from {icon_path}")
                designerUi.setWindowIcon(QIcon(QPixmap(icon_path)))
            else:
                print(f"Failed to load Module Designer window icon from {icon_path}")
            addWindow(designerUi, show=False)
            return designerUi

        self.ui.specialActionButton.clicked.connect(lambda *args: openModuleDesigner() and None or None)

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
        self.ui.actionExit.triggered.connect(lambda *args: self.close() and None or None)

        self.ui.actionNewTLK.triggered.connect(lambda: addWindow(TLKEditor(self, self.active)))
        self.ui.actionNewDLG.triggered.connect(lambda: addWindow(DLGEditor(self, self.active)))
        self.ui.actionNewNSS.triggered.connect(lambda: addWindow(NSSEditor(self, self.active)))
        self.ui.actionNewUTC.triggered.connect(lambda: addWindow(UTCEditor(self, self.active)))
        self.ui.actionNewUTP.triggered.connect(lambda: addWindow(UTPEditor(self, self.active)))
        self.ui.actionNewUTD.triggered.connect(lambda: addWindow(UTDEditor(self, self.active)))
        self.ui.actionNewUTI.triggered.connect(lambda: addWindow(UTIEditor(self, self.active)))
        self.ui.actionNewUTT.triggered.connect(lambda: addWindow(UTTEditor(self, self.active)))
        self.ui.actionNewUTM.triggered.connect(lambda: addWindow(UTMEditor(self, self.active)))
        self.ui.actionNewUTW.triggered.connect(lambda: addWindow(UTWEditor(self, self.active)))
        self.ui.actionNewUTE.triggered.connect(lambda: addWindow(UTEEditor(self, self.active)))
        self.ui.actionNewUTS.triggered.connect(lambda: addWindow(UTSEditor(self, self.active)))
        self.ui.actionNewGFF.triggered.connect(lambda: addWindow(GFFEditor(self, self.active)))
        self.ui.actionNewERF.triggered.connect(lambda: addWindow(ERFEditor(self, self.active)))
        self.ui.actionNewTXT.triggered.connect(lambda: addWindow(TXTEditor(self, self.active)))
        self.ui.actionNewSSF.triggered.connect(lambda: addWindow(SSFEditor(self, self.active)))
        self.ui.actionCloneModule.triggered.connect(lambda: addWindow(CloneModuleDialog(self, self.active, self.installations)))

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
        objRet: QObject | None = self.sender()
        if not isinstance(objRet, QAction):
            return
        action = objRet
        print("<SDM> [openRecentFile scope] action: ", action)

        if not action:
            print("No action")
            return
        if not isinstance(action, QAction):
            print(f"Not a QAction, {action}")
            return
        file = action.data()
        print("<SDM> [openRecentFile scope] file: ", file)

        if not file:
            print(f"Action {action} has no file data.")
            return
        if not isinstance(file, Path):
            print(f"Action {action} does not contain a valid file path '{file}'.")
            return
        resource = FileResource.from_path(file)
        print("<SDM> [openRecentFile scope] resource: ", resource)

        openResourceEditor(file, resource.resname(), resource.restype(), resource.data(), self.active, self)

    def apply_style(
        self,
        app: QApplication,
        sheet: str = "",
        style: str | None = None,
        palette: QPalette | None = None,
        *,
        aggressive: bool = False,
    ):
        app.setStyleSheet(sheet)
        #self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.FramelessWindowHint)
        if style is None or style == self.original_style:
            app.setStyle(self.original_style)
        else:
            app.setStyle(style)
            if palette: ...
                # still can't get the custom title bar working, leave this disabled until we do.
                #self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        app_style = app.style()
        if palette is None:
            palette = app_style.standardPalette()
        app.setPalette(palette)
        if aggressive:
            for widget in app.allWidgets():
                widget.setStyleSheet(sheet)
                widget.setPalette(palette)
                widget.repaint()

    def change_theme(self, theme: QAction | str):
        app = QApplication.instance()
        assert isinstance(app, QApplication), "No Qt Application found or not a QApplication instance."

        print("<SDM> [toggle_stylesheet scope] self.settings.selectedTheme: ", self.settings.selectedTheme)
        self.settings.selectedTheme = theme.text() if isinstance(theme, QAction) else theme
        self.apply_style(app, aggressive=True)

        palette = None
        sheet = "Fusion"
        style = self.original_style
        if self.settings.selectedTheme == "Native":
            style = self.original_style
            palette = app.style().standardPalette()
        elif self.settings.selectedTheme == "Fusion (Light)":
            style = "Fusion"
            self.apply_style(app, sheet, "Fusion")
        elif self.settings.selectedTheme == "Fusion (Dark)":
            style = "Fusion"
            palette = self.create_palette(QColor(53, 53, 53), QColor(35, 35, 35), QColor(240, 240, 240),
                                          QColor(25, 25, 25), self.adjust_color(QColor("orange"), saturation=80, hue_shift=-10), QColor(255, 69, 0))
            #app.setStyle("Fusion")
            #self._applyCustomDarkPalette()
            #return
        elif self.settings.selectedTheme == "QDarkStyle":
            try:
                import qdarkstyle
            except (ImportError, ModuleNotFoundError):
                QMessageBox.critical(self, "Theme not found", "QDarkStyle is not installed in this environment.")
            else:
                app.setStyle(self.original_style)
                app.setPalette(app.style().standardPalette())
                app.setStyleSheet(qdarkstyle.load_stylesheet())  # straight from the docs. Not sure why they don't require us to explicitly set a style/palette.
            return
        elif self.settings.selectedTheme == "AMOLED":
            sheet = self._get_file_stylesheet(":/themes/other/AMOLED.qss", app)
            palette = self.create_palette("#000000", "#141414", "#e67e22", "#f39c12", "#808086", "#FFFFFF")
        elif self.settings.selectedTheme == "Aqua":
            style = self.original_style
            sheet = self._get_file_stylesheet(":/themes/other/aqua.qss", app)
        elif self.settings.selectedTheme == "ConsoleStyle":
            style = "Fusion"
            sheet = self._get_file_stylesheet(":/themes/other/ConsoleStyle.qss", app)
            palette = self.create_palette("#000000", "#1C1C1C", "#F0F0F0", "#585858", "#FF9900", "#FFFFFF")
        elif self.settings.selectedTheme == "ElegantDark":
            style = "Fusion"
            sheet = self._get_file_stylesheet(":/themes/other/ElegantDark.qss", app)
            palette = self.create_palette("#2A2A2A", "#525252", "#00FF00", "#585858", "#BDBDBD", "#FFFFFF")
        elif self.settings.selectedTheme == "MacOS":
            style = self.original_style
            sheet = self._get_file_stylesheet(":/themes/other/MacOS.qss", app)
            # dont use, looks worse
            #palette = self.create_palette("#ECECEC", "#D2D8DD", "#272727", "#FBFDFD", "#467DD1", "#FFFFFF")
        elif self.settings.selectedTheme == "ManjaroMix":
            sheet = self._get_file_stylesheet(":/themes/other/ManjaroMix.qss", app)
            palette = self.create_palette("#151a1e", QColor().blue(), "#d3dae3", "#4fa08b", "#214037", "#027f7f")
        elif self.settings.selectedTheme == "MaterialDark":
            style = "Fusion"
            sheet = self._get_file_stylesheet(":/themes/other/MaterialDark.qss", app)
            palette = self.create_palette("#1E1D23", "#1E1D23", "#FFFFFF", "#007B50", "#04B97F", "#37EFBA")
        elif self.settings.selectedTheme == "NeonButtons":
            ...
            #sheet = self._get_file_stylesheet(":/themes/other/NeonButtons.qss", app)
        elif self.settings.selectedTheme == "Ubuntu":
            ...
            #sheet = self._get_file_stylesheet(":/themes/other/Ubuntu.qss", app)
            #palette = self.create_palette("#f0f0f0", "#1e1d23", "#000000", "#f68456", "#ec743f", "#ffffff")
        elif self.settings.selectedTheme == "Breeze (Dark)":
            sheet = self._get_file_stylesheet(":/dark/stylesheet.qss", app)
        else:
            self.settings.reset_setting("selectedTheme")
            self.change_theme(self.settings.selectedTheme)
        print(f"Theme changed to: '{self.settings.selectedTheme}'. Native style name: {self.original_style}")
        self.apply_style(app, sheet, style, palette)
        self.show()

    def _get_file_stylesheet(self, qt_path: str, app: QApplication) -> str:
        file = QFile(qt_path)
        if not file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
            return ""
        try:
            return QTextStream(file).readAll()
        finally:
            file.close()

    def adjust_color(self, color: Any, lightness: int = 100, saturation: int = 100, hue_shift: int = 0) -> QColor:
        """Adjusts the color's lightness, saturation, and hue."""
        qcolor = QColor(color)
        h, s, v, _ = qcolor.getHsv()
        s = max(0, min(255, s * saturation // 100))
        v = max(0, min(255, v * lightness // 100))
        h = (h + hue_shift) % 360
        qcolor.setHsv(h, s, v)
        return qcolor

    def create_palette(
        self,
        primary: QColor | Qt.GlobalColor | str | int,
        secondary: QColor | Qt.GlobalColor | str | int,
        text: QColor | Qt.GlobalColor | str | int,
        tooltip_base: QColor | Qt.GlobalColor | str | int,
        highlight: QColor | Qt.GlobalColor | str | int,
        bright_text: QColor | Qt.GlobalColor | str | int,
    ) -> QPalette:
        """Create a QPalette using base colors adjusted for specific UI roles."""
        if not isinstance(primary, QColor):
            primary = QColor(primary)
        if not isinstance(secondary, QColor):
            secondary = QColor(secondary)
        if not isinstance(text, QColor):
            text = QColor(text)
        if not isinstance(tooltip_base, QColor):
            tooltip_base = QColor(tooltip_base)
        if not isinstance(highlight, QColor):
            highlight = QColor(highlight)
        if not isinstance(bright_text, QColor):
            bright_text = QColor(bright_text)

        palette = QPalette()
        role_colors: dict[QPalette.ColorRole, QColor] = {
            QPalette.ColorRole.Window: secondary,
            QPalette.ColorRole.Background: self.adjust_color(primary, lightness=110),
            QPalette.ColorRole.Dark: self.adjust_color(primary, lightness=80),
            QPalette.ColorRole.Foreground: self.adjust_color(secondary, lightness=80),
            QPalette.ColorRole.Button: primary,
            QPalette.ColorRole.WindowText: text,
            QPalette.ColorRole.Base: primary,
            QPalette.ColorRole.AlternateBase: self.adjust_color(secondary, lightness=120),
            QPalette.ColorRole.ToolTipBase: tooltip_base,
            QPalette.ColorRole.ToolTipText: self.adjust_color(tooltip_base, lightness=200),  # Slightly lighter for readability
            QPalette.ColorRole.Text: self.adjust_color(text, lightness=90),
            QPalette.ColorRole.ButtonText: self.adjust_color(text, lightness=95),
            QPalette.ColorRole.BrightText: bright_text,
            QPalette.ColorRole.Link: highlight,
            QPalette.ColorRole.LinkVisited: self.adjust_color(highlight, hue_shift=10),
            QPalette.ColorRole.Highlight: highlight,
            QPalette.ColorRole.HighlightedText: self.adjust_color(secondary, lightness=120, saturation=255),
            QPalette.ColorRole.Light: self.adjust_color(primary, lightness=150),
            QPalette.ColorRole.Midlight: self.adjust_color(primary, lightness=130),
            QPalette.ColorRole.Mid: self.adjust_color(primary, lightness=100),
            QPalette.ColorRole.Shadow: self.adjust_color(primary, lightness=50),
            QPalette.ColorRole.PlaceholderText: self.adjust_color(text, lightness=70)
        }
        for role, color in role_colors.items():
            palette.setColor(QPalette.Normal, role, color)

        # Create disabled and inactive variations
        for state_key, saturation_factor, lightness_factor in [
            (QPalette.Disabled, 80, 60),  # More muted and slightly darker
            (QPalette.Inactive, 90, 80)]:  # Slightly muted
            for role, base_color in role_colors.items():
                adjusted_color = self.adjust_color(base_color, saturation=saturation_factor, lightness=lightness_factor)
                palette.setColor(state_key, role, adjusted_color)

        return palette

    def _applyCustomDarkPalette(self):
        dark_palette = QPalette()

        # White
        dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(240, 240, 240))
        dark_palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText, QColor(240, 240, 240))

        # Lighter gray
        dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(230, 230, 230))

        # Light gray
        dark_palette.setColor(QPalette.ColorRole.Text, QColor(220, 220, 220))
        dark_palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Text, QColor(220, 220, 220))

        # gray
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(200, 200, 200))
        dark_palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.ToolTipText, QColor(200, 200, 200))

        # slightly darker gray
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ToolTipText, QColor(169, 169, 169))
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(169, 169, 169))

        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(128, 128, 128))  # Gray for disabled text

        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(105, 105, 105))  # Dim gray for disabled button text

        # Dark slate gray
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Button, QColor(53, 53, 53))

        # Darker slate gray
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.AlternateBase, QColor(45, 45, 45))

        # Darkest Slate Gray
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25))

        # Very Dark slate gray
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.HighlightedText, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Base, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.HighlightedText, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Base, QColor(35, 35, 35))

        dark_palette.setColor(QPalette.ColorRole.Link, QColor(100, 149, 237))  # Cornflower blue for links
        dark_palette.setColor(QPalette.ColorRole.LinkVisited, QColor(123, 104, 238))  # Medium slate blue for visited links
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.LinkVisited, QColor(123, 104, 238))  # Medium slate blue for disabled visited links

        # Dodger blue
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.LinkVisited, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Highlight, QColor(42, 130, 218))

        dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 69, 0))  # Orange-red for bright text
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.BrightText, QColor(255, 0, 0))  # Red for disabled bright text
        dark_palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.BrightText, Qt.GlobalColor.red)

        dark_palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Text, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)


        QApplication.setPalette(dark_palette)

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
        print("<SDM> [onModuleReload scope] resources: ", len(resources))

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
        print("<SDM> [onSavepathChanged scope] newSaveDirPath: ", newSaveDirPath)

        if newSaveDirPath not in self.active._saves:
            self.active.load_saves()
        if newSaveDirPath not in self.active._saves:
            print(f"Cannot load save {newSaveDirPath}: not found in saves list")
            return

        for save_path, resource_list in self.active._saves[newSaveDirPath].items():
            # Create a new parent item for the save_path
            save_path_item = QStandardItem(str(save_path.relative_to(save_path.parent.parent)))
            print("<SDM> [onSavepathChanged scope] save_path_item: ", save_path_item)

            self.ui.savesWidget.modulesModel.invisibleRootItem().appendRow(save_path_item)

            # Dictionary to keep track of category items under this save_path_item
            categoryItemsUnderSavePath: dict[str, QStandardItem] = {}

            for resource in resource_list:
                restype: ResourceType = resource.restype()
                print("<SDM> [onSavepathChanged scope] ResourceType: ", restype)

                category: str = restype.category
                print("<SDM> [onSavepathChanged scope] category: ", category)

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
                print("<SDM> [onSavepathChanged scope] categoryItem: ", categoryItem.text())

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
        print("<SDM> [onOverrideFileUpdated scope] eventType: ", eventType)

        if eventType == "deleted":
            print("<SDM> [onOverrideFileUpdated scope] eventType: ", eventType)

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
        print("<SDM> [onOverrideReload scope] override_path: ", override_path)

        file_or_folder_path = override_path.joinpath(file_or_folder)
        print("<SDM> [onOverrideReload scope] file_or_folder_path: ", file_or_folder_path)

        if not file_or_folder_path.is_relative_to(self.active.override_path()):
            raise ValueError(f"'{file_or_folder_path}' is not relative to the override folder, cannot reload")
        if file_or_folder_path.safe_isfile():
            rel_folderpath = file_or_folder_path.parent.relative_to(self.active.override_path())
            print("<SDM> [onOverrideReload scope] rel_folderpath: ", rel_folderpath)

            self.active.reload_override_file(file_or_folder_path)
        else:
            rel_folderpath = file_or_folder_path.relative_to(self.active.override_path())
            print("<SDM> [onOverrideReload scope] rel_folderpath: ", rel_folderpath)

            self.active.load_override(str(rel_folderpath))
        self.ui.overrideWidget.setResources(self.active.override_resources(str(rel_folderpath) if rel_folderpath.name else None))

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
        print("<SDM> [changeActiveInstallation scope] index: ", index)

        if index < 0:  # self.ui.gameCombo.clear() will call this function with -1
            print(f"Index out of range - {index} (expected zero or positive)")
            return

        previousIndex: int = self.ui.gameCombo.currentIndex()
        print("<SDM> [changeActiveInstallation scope] previousIndex: ", previousIndex)

        self.ui.gameCombo.setCurrentIndex(index)

        if index == 0:
            print("<SDM> [unset installation scope]. index: ", index)
            self.unsetInstallation()
            return

        name: str = self.ui.gameCombo.itemText(index)
        print("<SDM> [changeActiveInstallation scope] name: ", name)

        path: str = self.settings.installations()[name].path.strip()
        print("<SDM> [changeActiveInstallation scope] path: ", path)

        tsl: bool = self.settings.installations()[name].tsl
        print("<SDM> [changeActiveInstallation scope] tsl: ", tsl)


        # If the user has not set a path for the particular game yet, ask them too.
        if not path or not path.strip() or not CaseAwarePath(path).safe_isdir():
            if path and path.strip():
                QMessageBox(QMessageBox.Icon.Warning, f"Installation '{path}' not found", "Select another path now.").exec_()
            path = QFileDialog.getExistingDirectory(self, f"Select the game directory for {name}", "Knights of the Old Republic II" if tsl else "swkotor")
            print("<SDM> [changeActiveInstallation scope] path: ", path)


        # If the user still has not set a path, then return them to the [None] option.
        if not path or not path.strip():
            print("User did not choose a path for this installation.")
            self.ui.gameCombo.setCurrentIndex(previousIndex)
            return

        active = self.installations.get(name)
        print("<SDM> [changeActiveInstallation scope] active: ", active)

        if active:
            self.active = active
            print("<SDM> [changeActiveInstallation scope] self.active: ", self.active)

        else:
            loader: AsyncLoader | None = None
            def load_task() -> HTInstallation:
                profiler = None
                if self.settings.profileToolset and cProfile is not None:
                    profiler = cProfile.Profile()
                    profiler.enable()
                progress_callback = None
                if loader is not None and loader._realtime_progress:  # noqa: SLF001
                    def progress_callback(data: int | str, mtype: Literal["set_maximum", "increment", "update_maintask_text", "update_subtask_text"]):
                        loader._worker.progress.emit(data, mtype)  # noqa: SLF001
                new_active = HTInstallation(path, name, tsl=tsl, progress_callback=progress_callback)
                if self.settings.profileToolset and profiler:
                    profiler.disable()
                    profiler.dump_stats(str(Path("load_ht_installation.pstat").absolute()))
                return new_active

            loader = AsyncLoader(
                self,
                "Loading Installation",
                load_task,
                "Failed to load installation",
                realtime_progress=True,  # Enable/Disable progress bar information globally here.
            )
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

            # FIXME(th3w1zard1): Not once in my life have I seen this watchdog report modified files correctly. Not even in Cortisol's last release version.
            # Causes a hella slowdown on Linux, something to do with internal logging since it seems to be overly tracking `os.stat_result` and creating
            # about 20 debug logs every second, spamming both our logs and the console.`
            # What we should do instead, is save the Installation instance to our QSettings, modify FileResource cls to store a LastModified attr, and onLoad we just
            # load only the files that were changed. Would reduce toolset startups by a ton.
            #self.dogObserver = Observer()
            #self.dogObserver.schedule(self.dogHandler, self.active.path(), recursive=True)
            #self.dogObserver.start()
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
        print("<SDM> [_saveCapsuleFromToolUI scope] c_filepath: ", c_filepath)


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
        print("<SDM> [_saveCapsuleFromToolUI scope] extension_to_filter: ", extension_to_filter)

        filepath_str, _filter = QFileDialog.getSaveFileName(
            self,
            f"Save extracted {capsule_type} '{c_filepath.stem}' as...",
            str(Path.cwd().resolve()),
            capsuleFilter,
            extension_to_filter[c_filepath.suffix.lower()],  # defaults to the original extension.
        )
        print("<SDM> [_saveCapsuleFromToolUI scope] _filter: ", _filter)

        if not filepath_str or not filepath_str.strip():
            return
        r_save_filepath = Path(filepath_str)
        print("<SDM> [_saveCapsuleFromToolUI scope] r_save_filepath: ", r_save_filepath)


        try:
            if is_mod_file(r_save_filepath):
                print("<SDM> [_saveCapsuleFromToolUI scope] capsule_type: ", capsule_type)

                if capsule_type == "mod":
                    write_erf(read_erf(c_filepath), r_save_filepath)
                    QMessageBox(QMessageBox.Icon.Information, "Module Saved", f"Module saved to '{r_save_filepath}'").exec_()
                else:
                    module.rim_to_mod(r_save_filepath, self.active.module_path(), module_name, self.active.game())
                    QMessageBox(QMessageBox.Icon.Information, "Module Built", f"Module built from relevant RIMs/ERFs and saved to '{r_save_filepath}'").exec_()
                return

            erf_or_rim: ERF | RIM = read_erf(c_filepath) if is_any_erf_type_file(c_filepath) else read_rim(c_filepath)
            print("<SDM> [_saveCapsuleFromToolUI scope] erf_or_rim: ", erf_or_rim)

            if is_rim_file(r_save_filepath):
                if isinstance(erf_or_rim, ERF):
                    erf_or_rim = erf_or_rim.to_rim()
                    print("<SDM> [_saveCapsuleFromToolUI scope] erf_or_rim: ", erf_or_rim)

                write_rim(erf_or_rim, r_save_filepath)
                QMessageBox(QMessageBox.Icon.Information, "RIM Saved", f"Resource Image File saved to '{r_save_filepath}'").exec_()

            elif is_any_erf_type_file(r_save_filepath):
                if isinstance(erf_or_rim, RIM):
                    erf_or_rim = erf_or_rim.to_erf()
                    print("<SDM> [_saveCapsuleFromToolUI scope] erf_or_rim: ", erf_or_rim)

                erf_or_rim.erf_type = ERFType.from_extension(r_save_filepath)
                print("<SDM> [_saveCapsuleFromToolUI scope] erf_or_rim.erf_type: ", erf_or_rim.erf_type)

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
        print(f"ToolWindow.onOpenResources(resources={resources!r}, useSpecializedEditor={useSpecializedEditor}, resourceWidget={resourceWidget})")
        if not self.active:
            return
        for resource in resources:
            _filepath, _editor = openResourceEditor(resource.filepath(), resource.resname(), resource.restype(), resource.data(reload=True),
                                                    self.active, self, gff_specialized=useSpecializedEditor)
            print("<SDM> [onOpenResources scope] _editor: ", _editor)

        if resources:
            return
        if not isinstance(resourceWidget, ResourceList):
            return
        filename = resourceWidget.currentSection()
        print("<SDM> [onOpenResources scope] filename: ", filename)

        if not filename:
            return
        erf_filepath = self.active.module_path() / filename
        print("<SDM> [onOpenResources scope] erf_filepath: ", erf_filepath)

        if not erf_filepath.safe_isfile():
            self.log.info(f"Not loading '{erf_filepath}'. File does not exist")
            return
        res_ident = ResourceIdentifier.from_path(erf_filepath)
        print("<SDM> [onOpenResources scope] res_ident: ", res_ident)

        if not res_ident.restype:
            self.log.info(f"Not loading '{erf_filepath}'. Invalid resource")
            return
        _filepath, _editor = openResourceEditor(erf_filepath, res_ident.resname, res_ident.restype, BinaryReader.load_file(erf_filepath),
                                                self.active, self, gff_specialized=useSpecializedEditor)
        print("<SDM> [onOpenResources scope] _editor: ", _editor)


    # FileSearcher/FileResults
    def handleSearchCompleted(
        self,
        results_list: list[FileResource],
        searchedInstallation: HTInstallation,
    ):
        resultsDialog = FileResults(self, results_list, searchedInstallation)
        print("<SDM> [handleSearchCompleted scope] results_list: ", len(results_list))

        resultsDialog.setModal(False)
        addWindow(resultsDialog, show=False)
        resultsDialog.show()
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
        print("<SDM> [closeEvent scope] instance: ", instance)

        if instance is None:
            print("QCoreApplication.instance() returned None for some reason... calling sys.exit() directly.")
            sys.exit()
        else:
            print("ToolWindow closed, shutting down the app.")
            instance.quit()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton:
            # This code is responsible for allowing the window to be drag-moved from any point, not just the title bar.
            mouseMovePos = getattr(self, "_mouseMovePos", None)
            if mouseMovePos is None:
                return
            globalPos = event.globalPos()
            self.move(self.mapFromGlobal(self.mapToGlobal(self.pos()) + (globalPos - mouseMovePos)))
            self._mouseMovePos = globalPos

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._mousePressPos = event.globalPos()
            print("<SDM> [mousePressEvent scope] self._mousePressPos: ", self._mousePressPos)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._mousePressPos = None
            self._mouseMovePos = None

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in [Qt.Key_Tab, Qt.Key_Backtab]:
            self.focusHandler.handleTabNavigation(event)
        else:
            super().keyPressEvent(event)

    def dragEnterEvent(self, e: QtGui.QDragEnterEvent | None):
        if e is None:
            return

        #print_qt_object(e)
        if not e.mimeData().hasUrls():
            return

        for url in e.mimeData().urls():
            try:
                filepath = url.toLocalFile()
                print(f"URL: {url}")
                print(f"Filepath: {filepath}")

                _resref, restype = ResourceIdentifier.from_path(filepath).unpack()
                print(f"Resource Identifier: {_resref}, Resource Type: {restype}")
            except Exception:  # noqa: BLE001, PERF203
                self.log.exception("Could not process dragged-in item.")
                e.ignore()
                return
            else:
                if restype:
                    continue
                self.log.info(f"Not processing dragged-in item '{filepath}'. Invalid resource")
        e.accept()

    def _handleWindowsZipExplorerDrop(self, e: QtGui.QDropEvent):
        fd_data = e.mimeData().data('application/x-qt-windows-mime;value="FileGroupDescriptorW"').data()
        num_descriptors = struct.unpack("I", fd_data[:4])[0]
        print(f"Number of file descriptors: {num_descriptors}")
        offset = 4
        base_part_format = "I 16s 2l 2l I 2Q 2Q 2Q 2I"
        base_part_size = struct.calcsize(base_part_format)
        filename_offset = 72
        base_descriptor_data = fd_data[offset:offset + base_part_size]
        raw_filename = base_descriptor_data[filename_offset:filename_offset + len(base_descriptor_data)]
        try:
            filename = raw_filename.decode("utf-16-le", errors="replace")
        except UnicodeDecodeError as decode_error:
            print(f"UnicodeDecodeError: {decode_error}")
            return
        QMessageBox(
            QMessageBox.Icon.Critical,
            "Windows ZIP drops not supported",
            f"Please extract {filename} somewhere before attempting to open it into the toolset.",
        ).exec_()
        # TODO(th3w1zard1): get the path to the actual data from Shell IDList Array? Apparently it doesn't store in FileContents as initially predicted.
        # shell_idlist_data = e.mimeData().data('application/x-qt-windows-mime;value="Shell IDList Array"').data()

    def dropEvent(self, e: QtGui.QDropEvent | None):
        if e is None:
            return

        for url in e.mimeData().urls():
            filepath: str = url.toLocalFile()
            print("<SDM> [dropEvent scope] filepath: ", filepath)

            data = BinaryReader.load_file(filepath)
            resname, restype = ResourceIdentifier.from_path(filepath).unpack()
            print("<SDM> [dropEvent scope] restype: ", restype)

            if not restype:
                self.log.info(f"Not loading dropped file '{filepath}'. Invalid resource")
                continue
            openResourceEditor(filepath, resname, restype, data, self.active, self,
                            gff_specialized=GlobalSettings().gff_specializedEditors)
        #self._handleWindowsZipExplorerDrop(e)


    # endregion

    # region Menu Bar
    def updateMenus(self):
        self.log.debug("Updating menus...")
        version = "x" if self.active is None else "2" if self.active.tsl else "1"

        dialogIconPath = f":/images/icons/k{version}/dialog.png"
        self.ui.actionNewDLG.setIcon(QIcon(QPixmap(dialogIconPath)))  # type: ignore[arg-type]
        self.ui.actionNewDLG.setEnabled(self.active is not None)

        tlkIconPath = f":/images/icons/k{version}/tlk.png"
        self.ui.actionNewTLK.setIcon(QIcon(QPixmap(tlkIconPath)))  # type: ignore[arg-type]
        self.ui.actionNewTLK.setEnabled(True)

        scriptIconPath = f":/images/icons/k{version}/script.png"
        self.ui.actionNewNSS.setIcon(QIcon(QPixmap(scriptIconPath)))  # type: ignore[arg-type]
        self.ui.actionNewNSS.setEnabled(self.active is not None)

        creatureIconPath = f":/images/icons/k{version}/creature.png"
        self.ui.actionNewUTC.setIcon(QIcon(QPixmap(creatureIconPath)))  # type: ignore[arg-type]
        self.ui.actionNewUTC.setEnabled(self.active is not None)

        placeableIconPath = f":/images/icons/k{version}/placeable.png"
        self.ui.actionNewUTP.setIcon(QIcon(QPixmap(placeableIconPath)))  # type: ignore[arg-type]
        self.ui.actionNewUTP.setEnabled(self.active is not None)

        doorIconPath = f":/images/icons/k{version}/door.png"
        self.ui.actionNewUTD.setIcon(QIcon(QPixmap(doorIconPath)))  # type: ignore[arg-type]
        self.ui.actionNewUTD.setEnabled(self.active is not None)

        itemIconPath = f":/images/icons/k{version}/item.png"
        self.ui.actionNewUTI.setIcon(QIcon(QPixmap(itemIconPath)))  # type: ignore[arg-type]
        self.ui.actionNewUTI.setEnabled(self.active is not None)

        soundIconPath = f":/images/icons/k{version}/sound.png"
        self.ui.actionNewUTS.setIcon(QIcon(QPixmap(soundIconPath)))  # type: ignore[arg-type]
        self.ui.actionNewUTS.setEnabled(self.active is not None)

        triggerIconPath = f":/images/icons/k{version}/trigger.png"
        self.ui.actionNewUTT.setIcon(QIcon(QPixmap(triggerIconPath)))  # type: ignore[arg-type]
        self.ui.actionNewUTT.setEnabled(self.active is not None)

        merchantIconPath = f":/images/icons/k{version}/merchant.png"
        self.ui.actionNewUTM.setIcon(QIcon(QPixmap(merchantIconPath)))  # type: ignore[arg-type]
        self.ui.actionNewUTM.setEnabled(self.active is not None)

        waypointIconPath = f":/images/icons/k{version}/waypoint.png"
        self.ui.actionNewUTW.setIcon(QIcon(QPixmap(waypointIconPath)))  # type: ignore[arg-type]
        self.ui.actionNewUTW.setEnabled(self.active is not None)

        encounterIconPath = f":/images/icons/k{version}/encounter.png"
        self.ui.actionNewUTE.setIcon(QIcon(QPixmap(encounterIconPath)))  # type: ignore[arg-type]
        self.ui.actionNewUTE.setEnabled(self.active is not None)

        self.ui.actionEditTLK.setEnabled(self.active is not None)
        self.ui.actionEditJRL.setEnabled(self.active is not None)
        self.ui.actionFileSearch.setEnabled(self.active is not None)
        self.ui.actionModuleDesigner.setEnabled(self.active is not None)
        self.ui.actionIndoorMapBuilder.setEnabled(self.active is not None)

        self.ui.actionCloneModule.setEnabled(self.active is not None)

    def debounceModuleDesignerLoad(self):
        """Prevents users from spamming the start button, which could easily result in a bad crash."""
        self.moduleDesignerLoadProcessed = True

    def openModuleDesigner(self):
        if self.active is None:
            QMessageBox(QMessageBox.Icon.Information, "No installation loaded.", "Load an installation before opening the Module Designer.").exec_()
            return
        designer = ModuleDesigner(None, self.active)
        addWindow(designer, show=False)

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
            print("<SDM> [dropEvent scope] result: ", result)

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
        print("<SDM> [openActiveTalktable scope] filepath: ", filepath)
        if not filepath.safe_isfile():
            QMessageBox(QMessageBox.Icon.Information, "dialog.tlk not found", f"Could not open the TalkTable editor, dialog.tlk not found at the expected location<br><br>{filepath}.").exec_()
            return
        data = BinaryReader.load_file(filepath)
        print("<SDM> [openActiveTalktable scope] data: ", data)

        openResourceEditor(filepath, "dialog", ResourceType.TLK, data, self.active, self)

    def openActiveJournal(self):
        if self.active is None:
            QMessageBox(QMessageBox.Icon.Information, "No installation loaded.", "Load an installation before opening the Journal Editor.").exec_()
            return
        jrl_ident = ResourceIdentifier("global", ResourceType.JRL)
        journal_resources = self.active.locations(
            [jrl_ident],
            [SearchLocation.OVERRIDE, SearchLocation.CHITIN],
        )
        print("<SDM> [openActiveJournal scope] journal_resources: ", journal_resources)

        if not journal_resources or not journal_resources.get(jrl_ident):
            QMessageBox(QMessageBox.Icon.Critical, "global.jrl not found", "Could not open the journal editor: 'global.jrl' not found.").exec_()
            return
        relevant = journal_resources[jrl_ident]
        if len(relevant) > 1:
            dialog = FileSelectionWindow(relevant, self.active)
        else:
            jrl_resource = relevant[0].as_file_resource()
            openResourceEditor(jrl_resource.filepath(), jrl_resource.resname(), jrl_resource.restype(), jrl_resource.data(), self.active, self)
        addWindow(dialog)

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
        addWindow(searchDialog, show=False)
        searchDialog.fileResults.connect(self.handleSearchCompleted)

    def openIndoorMapBuilder(self):
        IndoorMapBuilder(self, self.active).show()

    def openInstructionsWindow(self):
        """Opens the instructions window."""
        window = HelpWindow(None)
        print("<SDM> [openInstructionsWindow scope] window: ", window)

        window.setWindowIcon(self.windowIcon())
        addWindow(window)
        window.activateWindow()

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
            print("<SDM> [checkForUpdates scope] silent: ", silent)

        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            self.log.exception("Failed to check for updates.")
            if not silent:
                etype, msg = universal_simplify_exception(e)
                print("<SDM> [checkForUpdates scope] msg: ", msg)

                QMessageBox(QMessageBox.Icon.Information, f"Unable to fetch latest version ({etype})",
                            f"Check if you are connected to the internet.\nError: {msg}", QMessageBox.Ok, self).exec_()

    def _check_toolset_update(self, *, silent: bool):
        def get_latest_version_info() -> tuple[dict[str, Any], dict[str, Any]]:
            edge_info = None
            if self.settings.useBetaChannel:
                edge_info = getRemoteToolsetUpdateInfo(useBetaChannel=True, silent=silent)
                print("<SDM> [get_latest_version_info scope] edge_info: ", edge_info)

                if not isinstance(edge_info, dict):
                    if silent:
                        edge_info = None
                    else:
                        raise edge_info

            master_info = getRemoteToolsetUpdateInfo(useBetaChannel=False, silent=silent)
            print("<SDM> [get_latest_version_info scope] master_info: ", master_info)

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
            print("<SDM> [determine_version_info scope] version_list: ", version_list)


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
            print("<SDM> [determine_version_info scope] releaseVersion: ", releaseVersion)

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
                print("<SDM> [display_version_message scope] up_to_date_msg_box: ", up_to_date_msg_box)

                up_to_date_msg_box.button(QMessageBox.Ok).setText("Reinstall?")
                up_to_date_msg_box.setWindowIcon(self.windowIcon())
                result = up_to_date_msg_box.exec_()
                print("<SDM> [display_version_message scope] result: ", result)

                if result == QMessageBox.Ok:
                    toolset_updater = UpdateDialog(self)
                    print("<SDM> [display_version_message scope] toolset_updater: ", toolset_updater)

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
            print("<SDM> [display_version_message scope] new_version_msg_box: ", new_version_msg_box)

            new_version_msg_box.setDefaultButton(QMessageBox.Abort)
            new_version_msg_box.button(QMessageBox.Yes).setText("Open")
            new_version_msg_box.button(QMessageBox.Abort).setText("Ignore")
            new_version_msg_box.setWindowIcon(self.windowIcon())
            response = new_version_msg_box.exec_()
            print("<SDM> [display_version_message scope] response: ", response)
            if response == QMessageBox.Ok:
                self.autoupdate_toolset(greatest_version, edge_info, isRelease=release_version_checked)
            elif response == QMessageBox.Yes:
                toolset_updater = UpdateDialog(self)
                print("<SDM> [display_version_message scope] toolset_updater: ", toolset_updater)

                toolset_updater.exec_()

        master_info, edge_info = get_latest_version_info()
        print("<SDM> [display_version_message scope] edge_info: ", edge_info)

        if edge_info is None:
            return

        remote_info, release_version_checked = determine_version_info(edge_info, master_info)
        print("<SDM> [display_version_message scope] release_version_checked: ", release_version_checked)

        greatest_available_version = remote_info["toolsetLatestVersion"] if release_version_checked else remote_info["toolsetLatestBetaVersion"]
        print("<SDM> [display_version_message scope] greatest_available_version: ", greatest_available_version)

        toolset_latest_notes = remote_info.get("toolsetLatestNotes", "") if release_version_checked else remote_info.get("toolsetBetaLatestNotes", "")
        print("<SDM> [display_version_message scope] toolset_latest_notes: ", toolset_latest_notes)

        toolset_download_link = remote_info["toolsetDownloadLink"] if release_version_checked else remote_info["toolsetBetaDownloadLink"]
        print("<SDM> [display_version_message scope] toolset_download_link: ", toolset_download_link)


        version_check = remoteVersionNewer(CURRENT_VERSION, greatest_available_version)
        print("<SDM> [display_version_message scope] version_check: ", version_check)

        cur_version_beta_release_str = ""
        print("<SDM> [display_version_message scope] remote_info[toolsetLatestVersion]: ", remote_info["toolsetLatestVersion"])
        print("<SDM> [display_version_message scope] remote_info[toolsetLatestBetaVersion]: ", remote_info["toolsetLatestBetaVersion"])
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
        print("<SDM> [autoupdate_toolset scope] proc_arch: ", proc_arch)

        assert proc_arch == ProcessorArchitecture.from_python()
        os_name = platform.system()
        print("<SDM> [autoupdate_toolset scope] os_name: ", os_name)

        links: list[str] = []

        isRelease = False  # TODO(th3w1zard1): remove this line when the release version direct links are ready.
        if isRelease:
            links = remoteInfo["toolsetDirectLinks"][os_name][proc_arch.value]
        else:
            links = remoteInfo["toolsetBetaDirectLinks"][os_name][proc_arch.value]
        print("<SDM> [autoupdate_toolset scope] links: ", links)

        progress_queue = Queue()
        print("<SDM> [autoupdate_toolset scope] progress_queue: ", progress_queue)
        progress_process = Process(target=run_progress_dialog, args=(progress_queue, "Holocron Toolset is updating and will restart shortly..."))
        print("<SDM> [autoupdate_toolset scope] progress_process: ", progress_process)

        progress_process.start()
        self.hide()

        def download_progress_hook(
            data: dict[str, Any],
            progress_queue: Queue = progress_queue,
        ):
            print("<SDM> [download_progress_hook scope] data: ", data)
            progress_queue.put(data)

        # Prepare the list of progress hooks with the method from ProgressDialog
        progress_hooks = [download_progress_hook]
        print("<SDM> [download_progress_hook scope] progress_hooks: ", progress_hooks)

        def exitapp(kill_self_here: bool):  # noqa: FBT001
            packaged_data = {"action": "shutdown", "data": {}}
            print("<SDM> [exitapp scope] packaged_data: ", packaged_data)

            progress_queue.put(packaged_data)
            ProgressDialog.monitor_and_terminate(progress_process)
            if kill_self_here:
                sys.exit(0)

        updater = AppUpdate(links, "HolocronToolset", CURRENT_VERSION, latestVersion,
                            downloader=None, progress_hooks=progress_hooks, exithook=exitapp)  # type: ignore[arg-type]
        print("<SDM> [exitapp scope] updater: ", updater)

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
        print("<SDM> [getActiveResourceWidget scope] currentWidget: ", currentWidget)

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

    def onTabChanged(self):
        ...
        # self.setMinimumSize(512, 471)

    def selectResource(self, tree: ResourceList, resource: FileResource):
        """This function seems to reload the resource after determining the ui widget containing it.

        Seems to only be used for the FileSearcher dialog.
        """
        print("<SDM> [selectResource scope] tree: ", tree)
        if tree == self.ui.coreWidget:
            self.ui.resourceTabs.setCurrentWidget(self.ui.coreTab)
            self.ui.coreWidget.setResourceSelection(resource)

        elif tree == self.ui.modulesWidget:
            self.ui.resourceTabs.setCurrentWidget(self.ui.modulesTab)
            filename = resource.filepath().name
            print("<SDM> [selectResource scope] filename: ", filename)

            self.changeModule(filename)
            self.ui.modulesWidget.setResourceSelection(resource)

        elif tree == self.ui.overrideWidget:
            self._selectOverrideResource(resource)
        elif tree == self.ui.savesWidget:
            self.ui.resourceTabs.setCurrentWidget(self.ui.savesTab)
            filename = resource.filepath().name
            print("<SDM> [selectResource scope] filename: ", filename)

            self.onSaveReload(filename)

    def _selectOverrideResource(self, resource: FileResource):
        assert self.active is not None
        self.ui.resourceTabs.setCurrentWidget(self.ui.overrideTab)
        self.ui.overrideWidget.setResourceSelection(resource)
        subfolder: str = "."
        for folder_name in self.active.override_list():
            folder_path: CaseAwarePath = self.active.override_path() / folder_name
            print("<SDM> [_selectOverrideResource scope] folder_path: ", folder_path)

            if resource.filepath().is_relative_to(folder_path) and len(subfolder) < len(folder_path.name):
                subfolder = folder_name
                print("<SDM> [_selectOverrideResource scope] subfolder: ", subfolder)

        self.changeOverrideFolder(subfolder)

    def reloadInstallations(self):
        """Refresh the list of installations available in the combobox."""
        self.ui.gameCombo.currentIndexChanged.disconnect(self.changeActiveInstallation)
        self.ui.gameCombo.clear()  # without above disconnect, would call ToolWindow().changeActiveInstallation(-1)
        self.ui.gameCombo.addItem("[None]")  # without above disconnect, would call ToolWindow().changeActiveInstallation(0)

        for installation in self.settings.installations().values():
            self.ui.gameCombo.addItem(installation.name)
        self.ui.gameCombo.currentIndexChanged.connect(self.changeActiveInstallation)

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
        self.log.info("Loading core installation resources into UI...")
        self.ui.coreWidget.setResources(self.active.core_resources())
        self.log.debug("Remove unused Core tab categories...")
        self.ui.coreWidget.modulesModel.removeUnusedCategories()

    def changeModule(self, moduleName: str):
        # Some users may choose to merge their RIM files under one option in the Modules tab; if this is the case we
        # need to account for this.
        if self.settings.joinRIMsTogether:
            if moduleName.casefold().endswith("_s.rim"):
                moduleName = f"{moduleName[:-6]}.rim"
                print("<SDM> [changeModule scope] moduleName: ", moduleName)

            if moduleName.casefold().endswith("_dlg.erf"):
                moduleName = f"{moduleName[:-8]}.rim"
                print("<SDM> [changeModule scope] moduleName: ", moduleName)


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
            print("<SDM> [task scope] loader: ", loader)

            loader.exec_()
            moduleItems = loader.value
            print("<SDM> [task scope] moduleItems: ", moduleItems)

        self.ui.modulesWidget.setSections(moduleItems)

    def _getModulesList(self, *, reload: bool = True) -> list[QStandardItem]:
        if self.active is None:
            print("No installation is currently loaded, cannot refresh modules list")
            return []
        profiler = None
        if self.settings.profileToolset and cProfile is not None:
            profiler = cProfile.Profile()
            print("<SDM> [_getModulesList scope] profiler: ", profiler)

            profiler.enable()
        # If specified the user can forcibly reload the resource list for every module
        if reload:
            self.active.load_modules()

        areaNames: dict[str, str] = self.active.module_names()
        print("<SDM> [_getModulesList scope] areaNames: ", areaNames)


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
            print("<SDM> [_getTexturePackList scope] section: ", section)

            section.setData(texturepack, QtCore.Qt.ItemDataRole.UserRole)
            sections.append(section)
        return sections

    def refreshTexturePackList(self, *, reload: bool = True):
        sections = self._getTexturePackList(reload=reload)
        print("<SDM> [refreshTexturePackList scope] sections: ", sections)

        if sections is None:
            self.log.error("sections was somehow None in refreshTexturePackList(reload=%s)", reload, stack_info=True)
            print("<SDM> [refreshTexturePackList scope] reload: ", reload)

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
            print("<SDM> [refreshSavesList scope] save_path_str: ", save_path_str)

            section = QStandardItem(save_path_str)
            print("<SDM> [refreshSavesList scope] section: ", section)

            section.setData(save_path_str, QtCore.Qt.UserRole)
            sections.append(section)
        self.ui.savesWidget.setSections(sections)

    # endregion

    # region Extract
    def get_multiple_directories(self, title: str = "Choose some folders."):
        dialog = QFileDialog(self)
        print("<SDM> [get_multiple_directories scope] dialog: ", dialog)

        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        dialog.setWindowTitle(title)
        dialog.setDirectory(self)  # Optionally set the initial directory

        # Create a layout to enable multi-selection of directories
        list_view = dialog.findChild(QListView, "listView")
        print("<SDM> [get_multiple_directories scope] list_view: ", list_view)

        tree_view = dialog.findChild(QTreeView)
        print("<SDM> [get_multiple_directories scope] tree_view: ", tree_view)

        if list_view:
            list_view.setSelectionMode(QAbstractItemView.MultiSelection)
        if tree_view:
            tree_view.setSelectionMode(QAbstractItemView.MultiSelection)

        if dialog.exec_() == QFileDialog.Accepted:
            selected_dirs = dialog.selectedFiles()
            print("<SDM> [get_multiple_directories scope] selected_dirs: ", selected_dirs)

            return [Path(dir_path) for dir_path in selected_dirs]
        return []

    def extractModuleRoomTextures(self):
        assert self.active is not None
        from pykotor.common.module import Module
        from pykotor.tools.model import list_lightmaps, list_textures
        curModuleName: str = self.ui.modulesWidget.ui.sectionCombo.currentData(QtCore.Qt.ItemDataRole.UserRole)
        print("<SDM> [extractModuleRoomTextures scope] str: ", str)

        if curModuleName not in self.active._modules:
            RobustRootLogger.warning(f"'{curModuleName}' not a valid module.")
            BetterMessageBox("Invalid module.", f"'{curModuleName}' not a valid module, could not find it in the loaded installation.").exec_()
            return
        thisModule = Module(curModuleName, self.active, use_dot_mod=is_mod_file(curModuleName))
        print("<SDM> [extractModuleRoomTextures scope] thisModule: ", thisModule)

        lytModuleResource = thisModule.layout()
        print("<SDM> [extractModuleRoomTextures scope] lytModuleResource: ", lytModuleResource)

        if lytModuleResource is None:
            BetterMessageBox(f"'{curModuleName}' has no LYT!", f"The module '{curModuleName}' does not store any LYT resource.").exec_()
            return
        lyt = lytModuleResource.resource()
        print("<SDM> [extractModuleRoomTextures scope] lyt: ", lyt)

        if lyt is None:
            BetterMessageBox(f"'{curModuleName}' has no LYT paths!", "The module did not contain any locations for the LYT. This is an internal error, as there should be one if we know it exists. Please report.").exec_()
            return
        optionalPaths = []
        print("<SDM> [extractModuleRoomTextures scope] optionalPaths: ", optionalPaths)

        #customFolderPath = self.get_multiple_directories("Choose optional folders to search for models")
        #if customFolderPath and customFolderPath.strip():
        #    optionalPaths.append(Path(customFolderPath))
        modelQueries = [ResourceIdentifier(mdlName, ResourceType.MDL) for mdlName in (lyt.all_room_models())]
        print("<SDM> [extractModuleRoomTextures scope] modelQueries: ", modelQueries)

        modelLocationResults: dict[ResourceIdentifier, list[LocationResult]] = self.active.locations(modelQueries, folders=optionalPaths)
        print("<SDM> [extractModuleRoomTextures scope] modelLocationResults: ", modelLocationResults)

        modelLocations: dict[ResourceIdentifier, FileResource] = {k: v[0].as_file_resource() for k, v in modelLocationResults.items() if v}
        print("<SDM> [extractModuleRoomTextures scope] modelLocations: ", modelLocations)

        texlmNames: list[str] = []
        for res in modelLocations.values():
            texNames = []
            try:
                texNames.extend(iter(list_textures(res.data())))
            except Exception:
                RobustRootLogger.exception(f"Failed to extract textures names from {res.identifier()}")
            lmNames = []
            try:
                lmNames.extend(iter(list_lightmaps(res.data())))
            except Exception:
                RobustRootLogger.exception(f"Failed to extract lightmap names from {res.identifier()}")
            texlmNames.extend(texNames)
            texlmNames.extend(lmNames)
        textureData: CaseInsensitiveDict[TPC | None] = self.active.textures(texlmNames)
        for tex, data in textureData.copy().items():
            if data is None:
                del textureData[tex]
        textureResourceResults: list[ResourceResult] = [ResourceResult(tex, ResourceType.TPC, Path().joinpath(tex).with_suffix(".tpc"), bytes_tpc(data)) for tex, data in textureData.items()]

        FileSaveHandler(textureResourceResults, self).save_files()

    def extractModuleRoomModels(self):
        assert self.active is not None
        from pykotor.common.module import Module
        curModuleName: str = self.ui.modulesWidget.ui.sectionCombo.currentData(QtCore.Qt.ItemDataRole.UserRole)
        if curModuleName not in self.active._modules:
            RobustRootLogger.warning(f"'{curModuleName}' not a valid module.")
            BetterMessageBox("Invalid module.", f"'{curModuleName}' not a valid module, could not find it in the loaded installation.").exec_()
            return
        thisModule = Module(curModuleName, self.active, use_dot_mod=is_mod_file(curModuleName))
        print("<SDM> [extractModuleRoomModels scope] thisModule: ", thisModule)

        lytModuleResource = thisModule.layout()
        print("<SDM> [extractModuleRoomModels scope] lytModuleResource: ", lytModuleResource)

        if lytModuleResource is None:
            BetterMessageBox(f"'{curModuleName}' has no LYT!", f"The module '{curModuleName}' does not store any LYT resource.").exec_()
            return
        lyt = lytModuleResource.resource()
        print("<SDM> [extractModuleRoomModels scope] lyt: ", lyt)

        if lyt is None:
            BetterMessageBox(f"'{curModuleName}' has no LYT paths!", "The module did not contain any locations for the LYT. This is an internal error, as there should be one if we know it exists. Please report.").exec_()
            return
        optionalPaths = []
        print("<SDM> [extractModuleRoomModels scope] optionalPaths: ", optionalPaths)

        #customFolderPath = self.get_multiple_directories("Choose optional folders to search for models")
        #print("<SDM> [extractModuleRoomModels scope] customFolderPath: ", customFolderPath)

        #if customFolderPath and customFolderPath.strip():
        #    optionalPaths.append(Path(customFolderPath))
        modelQueries = [ResourceIdentifier(mdlName, ResourceType.MDL) for mdlName in (lyt.all_room_models())]
        print("<SDM> [extractModuleRoomModels scope] modelQueries: ", modelQueries)

        modelLocationResults: dict[ResourceIdentifier, list[LocationResult]] = self.active.locations(modelQueries, folders=optionalPaths)
        print("<SDM> [extractModuleRoomModels scope] list[LocationResult]]: ", modelLocationResults)

        modelLocations: dict[ResourceIdentifier, FileResource] = {k: v[0].as_file_resource() for k, v in modelLocationResults.items() if v}
        print("<SDM> [extractModuleRoomModels scope] FileResource]: ", modelLocations)

        FileSaveHandler(list(modelLocations.values()), self).save_files()

    def extractAllModuleTextures(self):
        assert self.active is not None
        from pykotor.common.module import Module
        curModuleName: str = self.ui.modulesWidget.ui.sectionCombo.currentData(QtCore.Qt.ItemDataRole.UserRole)
        print("<SDM> [extractAllModuleTextures scope] str: ", str)

        if curModuleName not in self.active._modules:
            RobustRootLogger.warning(f"'{curModuleName}' not a valid module.")
            return
        thisModule = Module(curModuleName, self.active, use_dot_mod=is_mod_file(curModuleName))
        print("<SDM> [extractAllModuleTextures scope] thisModule: ", thisModule)

        texturesList: list[ResourceResult] = []
        for ident, modRes in thisModule.resources.items():
            if ident.restype not in (ResourceType.TGA, ResourceType.TPC):
                continue
            data = modRes.data()
            print("<SDM> [extractAllModuleTextures scope] data: ", data)

            if data is None:
                continue
            locations = modRes.locations()
            print("<SDM> [extractAllModuleTextures scope] locations: ", locations)

            if not locations:
                continue
            texturesList.append(ResourceResult(ident.resname, ident.restype, locations[0], data))
        FileSaveHandler(texturesList, self).save_files()

    def extractAllModuleModels(self):
        from pykotor.common.module import Module
        curModuleName: str = self.ui.modulesWidget.ui.sectionCombo.currentData(QtCore.Qt.ItemDataRole.UserRole)
        if curModuleName not in self.active._modules:
            RobustRootLogger.warning(f"'{curModuleName}' not a valid module.")
            return
        thisModule = Module(curModuleName, self.active, use_dot_mod=is_mod_file(curModuleName))
        print("<SDM> [extractAllModuleModels scope] thisModule: ", thisModule)

        modelsList: list[ResourceResult] = []
        for ident, modRes in thisModule.resources.items():
            if ident.restype not in (ResourceType.MDX, ResourceType.MDL):
                continue
            data = modRes.data()
            if data is None:
                continue
            locations = modRes.locations()
            print("<SDM> [extractAllModuleModels scope] locations: ", locations)

            if not locations:
                continue
            modelsList.append(ResourceResult(ident.resname, ident.restype, locations[0], data))
        FileSaveHandler(modelsList, self).save_files()

    def extractModuleEverything(self):
        from pykotor.common.module import Module
        curModuleName: str = self.ui.modulesWidget.ui.sectionCombo.currentData(QtCore.Qt.ItemDataRole.UserRole)
        print("<SDM> [extractModuleEverything scope] curModuleName: ", curModuleName)

        if curModuleName not in self.active._modules:
            RobustRootLogger.warning(f"'{curModuleName}' not a valid module.")
            return
        thisModule = Module(curModuleName, self.active, use_dot_mod=is_mod_file(curModuleName))
        print("<SDM> [extractModuleEverything scope] thisModule: ", thisModule)

        allModuleResources: list[ResourceResult] = []
        for ident, modRes in thisModule.resources.items():
            data = modRes.data()
            print("<SDM> [extractModuleEverything scope] data: ", data)

            if data is None:
                continue
            locations = modRes.locations()
            print("<SDM> [extractModuleEverything scope] locations: ", locations)

            if not locations:
                continue
            allModuleResources.append(ResourceResult(ident.resname, ident.restype, locations[0], data))
        FileSaveHandler(allModuleResources, self).save_files()

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
            print("<SDM> [onExtractResources scope] paths_to_write: ", paths_to_write)

            if folder_path is None or paths_to_write is None:
                RobustRootLogger.debug("No paths to write: user must have cancelled the getExistingDirectory dialog.")
                return
            failed_savepath_handlers: dict[Path, Exception] = {}
            resource_save_paths = FileSaveHandler(selectedResources).determine_save_paths(paths_to_write, failed_savepath_handlers)
            print("<SDM> [onExtractResources scope] resource_save_paths: ", resource_save_paths)

            if not resource_save_paths:
                RobustRootLogger.debug("No resources returned from FileSaveHandler.determine_save_paths")
                return
            loader = AsyncBatchLoader(self, "Extracting Resources", [], "Failed to Extract Resources")
            print("<SDM> [onExtractResources scope] loader: ", loader)

            loader.errors.extend(failed_savepath_handlers.values())

            for resource, save_path in resource_save_paths.items():
                loader.addTask(lambda res=resource, fp=save_path: self._extractResource(res, fp, loader))

            loader.exec_()
            qInstance = QApplication.instance()
            print("<SDM> [onExtractResources scope] qInstance: ", qInstance)

            if qInstance is None:
                return
            if QThread.currentThread() == qInstance.thread():
                msgBox = QMessageBox(
                    QMessageBox.Icon.Information,
                    "Extraction successful.",
                    f"Successfully saved {len(paths_to_write)} files to {folder_path}",
                    flags=Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint
                )
                print("<SDM> [onExtractResources scope] msgBox: ", msgBox)

                msgBox.setDetailedText("\n".join(str(p) for p in resource_save_paths.values()))
                msgBox.exec_()
        elif isinstance(resourceWidget, ResourceList) and is_capsule_file(resourceWidget.currentSection()):
            module_name = resourceWidget.currentSection()
            print("<SDM> [onExtractResources scope] module_name: ", module_name)

            self._saveCapsuleFromToolUI(module_name)

    def build_extract_save_paths(self, resources: list[FileResource]) -> tuple[Path, dict[FileResource, Path]] | tuple[None, None]:
        # TODO(th3w1zard1): currently doesn't handle tpcTxiCheckbox.isChecked() or mdlTexturesCheckbox.isChecked()
        paths_to_write: dict[FileResource, Path] = {}

        folderpath_str: str = QFileDialog.getExistingDirectory(self, "Extract to folder")
        print("<SDM> [build_extract_save_paths scope] str: ", str)

        if not folderpath_str or not folderpath_str.strip():
            RobustRootLogger.debug("User cancelled folderpath extraction.")
            return None, None

        folder_path = Path(folderpath_str)
        print("<SDM> [build_extract_save_paths scope] folder_path: ", folder_path)

        for resource in resources:
            identifier = resource.identifier()
            print("<SDM> [build_extract_save_paths scope] identifier: ", identifier)

            save_path = folder_path / str(identifier)
            print("<SDM> [build_extract_save_paths scope] save_path: ", save_path)


            # Determine the final save path based on UI checks
            if resource.restype() is ResourceType.TPC and self.ui.tpcDecompileCheckbox.isChecked():
                save_path = save_path.with_suffix(".tga")
                print("<SDM> [build_extract_save_paths scope] save_path: ", save_path)

            elif resource.restype() is ResourceType.MDL and self.ui.mdlDecompileCheckbox.isChecked():
                save_path = save_path.with_suffix(".ascii.mdl")
                print("<SDM> [build_extract_save_paths scope] save_path: ", save_path)


            paths_to_write[resource] = save_path
            print("<SDM> [build_extract_save_paths scope] paths_to_write[resource]: ", paths_to_write[resource])


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
        print("<SDM> [_extractResource scope] Path: ", Path)


        data: bytes = resource.data()
        print("<SDM> [_extractResource scope] bytes: ", bytes)


        if resource.restype() is ResourceType.MDX and self.ui.mdlDecompileCheckbox.isChecked():
            RobustRootLogger.info(f"Not extracting MDX file '{resource.identifier()}', decompiling MDLs is checked.")
            return

        if resource.restype() is ResourceType.TPC:
            tpc: TPC = read_tpc(data, txi_source=save_path)
            print("<SDM> [_extractResource scope] TPC: ", TPC)


            if self.ui.tpcTxiCheckbox.isChecked():
                RobustRootLogger.info(f"Extracting TXI from {resource.identifier()} because of settings.")
                self._extractTxi(tpc, save_path.with_suffix(".txi"))

            if self.ui.tpcDecompileCheckbox.isChecked():
                RobustRootLogger.info(f"Converting '{resource.identifier()}' to TGA because of settings.")
                data = self._decompileTpc(tpc)
                print("<SDM> [_extractResource scope] data: ", data)


        if resource.restype() is ResourceType.MDL:
            if self.ui.mdlTexturesCheckbox.isChecked():
                RobustRootLogger.info(f"Extracting MDL Textures because of settings: {resource.identifier()}")
                self._extractMdlTextures(resource, r_folderpath, loader, data)

            if self.ui.mdlDecompileCheckbox.isChecked():
                RobustRootLogger.info(f"Converting {resource.identifier()} to ASCII MDL because of settings")
                data = self._decompileMdl(resource, data)
                print("<SDM> [_extractResource scope] data: ", data)


        with save_path.open("wb") as file:
            RobustRootLogger.info(f"Saving extracted data of '{resource.identifier()}' to '{save_path}'")
            file.write(data)

    def _extractTxi(self, tpc: TPC, filepath: Path):
        with filepath.open("wb") as file:
            file.write(tpc.txi.encode("ascii"))

    def _decompileTpc(self, tpc: TPC) -> bytearray:
        data = bytearray()
        print("<SDM> [_decompileTpc scope] data: ", data)

        write_tpc(tpc, data, ResourceType.TGA)
        return data

    def _decompileMdl(self, resource: FileResource, data: SOURCE_TYPES) -> bytearray:
        assert self.active is not None
        reslookup: ResourceResult | None = self.active.resource(resource.resname(), ResourceType.MDX)
        print("<SDM> [_decompileMdl scope] None: ", None)

        if reslookup is None:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), repr(resource))
        mdxData: bytes = reslookup.data
        print("<SDM> [_decompileMdl scope] bytes: ", bytes)

        mdl: MDL | None = read_mdl(data, 0, 0, mdxData, 0, 0)
        print("<SDM> [_decompileMdl scope] None: ", None)

        data = bytearray()
        print("<SDM> [_decompileMdl scope] data: ", data)

        write_mdl(mdl, data, ResourceType.MDL_ASCII)
        return data

    def _extractMdlTextures(self, resource: FileResource, folderpath: Path, loader: AsyncBatchLoader, data: bytes):
        assert self.active is not None
        for texture in model.list_textures(data):
            try:
                tpc: TPC | None = self.active.texture(texture)
                print("<SDM> [_extractMdlTextures scope] None: ", None)

                if tpc is None:
                    raise ValueError(texture)  # noqa: TRY301
                if self.ui.tpcTxiCheckbox.isChecked():
                    self._extractTxi(tpc, folderpath.joinpath(f"{texture}.txi"))

                file_format = ResourceType.TGA if self.ui.tpcDecompileCheckbox.isChecked() else ResourceType.TPC
                print("<SDM> [_extractMdlTextures scope] file_format: ", file_format)

                extension = "tga" if file_format is ResourceType.TGA else "tpc"
                write_tpc(tpc, folderpath.joinpath(f"{texture}.{extension}"), file_format)
            except Exception as e:  # noqa: PERF203, BLE001
                etype, msg = universal_simplify_exception(e)
                print("<SDM> [_extractMdlTextures scope] msg: ", msg)

                loader.errors.append(e.__class__(f"Could not find or extract tpc: '{texture}'"))

    def openFromFile(self):
        filepaths = QFileDialog.getOpenFileNames(self, "Select files to open")[:-1][0]
        print("<SDM> [openFromFile scope] filepaths: ", filepaths)


        for filepath in filepaths:
            r_filepath = Path(filepath)
            print("<SDM> [openFromFile scope] r_filepath: ", r_filepath)

            try:
                with r_filepath.open("rb") as file:
                    data = file.read()
                    print("<SDM> [openFromFile scope] data: ", data)

                openResourceEditor(filepath, *ResourceIdentifier.from_path(r_filepath).validate().unpack(), data, self.active, self)
            except (ValueError, OSError) as e:
                etype, msg = universal_simplify_exception(e)
                print("<SDM> [openFromFile scope] msg: ", msg)

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
        print("<SDM> [on_any_event scope] rightnow: ", rightnow)

        if rightnow - self.lastModified < timedelta(seconds=1):
            return

        self.lastModified = rightnow
        print("<SDM> [on_any_event scope] self.lastModified: ", self.lastModified)

        modified_path: Path = Path(event.src_path)
        print("<SDM> [on_any_event scope] modified_path: ", modified_path)


        if not modified_path.safe_isfile():
            return

        module_path: Path = self.window.active.module_path()
        print("<SDM> [on_any_event scope] module_path: ", module_path)

        override_path: Path = self.window.active.override_path()
        print("<SDM> [on_any_event scope] override_path: ", override_path)


        if modified_path.is_relative_to(module_path):
            self.window.moduleFilesUpdated.emit(str(modified_path), event.event_type)
        elif modified_path.is_relative_to(override_path):
            self.window.overrideFilesUpdate.emit(str(modified_path), event.event_type)
        else:
            print(f"Watchdog passed unknown file: {modified_path}")
