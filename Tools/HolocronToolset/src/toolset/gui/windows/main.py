from __future__ import annotations

import cProfile
import errno
import os
import shutil
import sys

from collections import defaultdict
from contextlib import suppress
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Any, List, cast

import qtpy

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy import QtCore
from qtpy.QtCore import (
    QCoreApplication,
    QEvent,
    QFile,
    QTextStream,
    QThread,
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
    Slot,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QColor, QIcon, QPalette, QPixmap, QStandardItem
from qtpy.QtWidgets import (
    QAbstractItemView,
    QAction,
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QListView,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QTreeView,
    QVBoxLayout,
)

from pykotor.common.stream import BinaryReader
from pykotor.extract.file import FileResource, ResourceIdentifier, ResourceResult
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.erf.erf_auto import read_erf, write_erf
from pykotor.resource.formats.erf.erf_data import ERF, ERFType
from pykotor.resource.formats.mdl import read_mdl, write_mdl
from pykotor.resource.formats.rim.rim_auto import read_rim, write_rim
from pykotor.resource.formats.rim.rim_data import RIM
from pykotor.resource.formats.tpc import read_tpc, write_tpc
from pykotor.resource.formats.tpc.tpc_auto import bytes_tpc
from pykotor.resource.type import ResourceType
from pykotor.tools import module
from pykotor.tools.misc import is_any_erf_type_file, is_bif_file, is_capsule_file, is_erf_file, is_mod_file, is_rim_file
from pykotor.tools.model import iterate_lightmaps, iterate_textures
from pykotor.tools.path import CaseAwarePath
from toolset.config import CURRENT_VERSION, is_remote_version_newer
from toolset.data.installation import HTInstallation
from toolset.gui.dialogs.about import About
from toolset.gui.dialogs.asyncloader import AsyncLoader
from toolset.gui.dialogs.clone_module import CloneModuleDialog
from toolset.gui.dialogs.load_from_location_result import FileSelectionWindow
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
from toolset.gui.helpers.callback import BetterMessageBox
from toolset.gui.widgets.main_widgets import ResourceList
from toolset.gui.widgets.settings.misc import GlobalSettings
from toolset.gui.windows.help import HelpWindow
from toolset.gui.windows.indoor_builder import IndoorMapBuilder
from toolset.gui.windows.module_designer import ModuleDesigner
from toolset.gui.windows.update_check_thread import UpdateCheckThread
from toolset.ui import stylesheet_resources  # noqa: F401  # pylint: disable=unused-import
from toolset.utils.window import add_window, open_resource_editor
from utility.error_handling import universal_simplify_exception
from utility.misc import is_debug_mode
from utility.tricks import debug_reload_pymodules
from utility.ui_libraries.qt.widgets.widgets.combobox import FilterComboBox

if qtpy.API_NAME == "PySide2":  # pylint: disable=ungrouped-imports
    from toolset.rcc import (  # pylint: disable=unused-import
        resources_rc_pyside2,  # noqa: PLC0415, F401  # pylint: disable=ungrouped-imports,unused-import
    )
elif qtpy.API_NAME == "PySide6":
    from toolset.rcc import (  # pylint: disable=unused-import
        resources_rc_pyside6,  # noqa: PLC0415, F401  # pylint: disable=ungrouped-imports,unused-import
    )
elif qtpy.API_NAME == "PyQt5":
    from toolset.rcc import (  # pylint: disable=unused-import
        resources_rc_pyqt5,  # noqa: PLC0415, F401  # pylint: disable=ungrouped-imports,unused-import
    )
elif qtpy.API_NAME == "PyQt6":
    from toolset.rcc import (  # pylint: disable=unused-import
        resources_rc_pyqt6,  # noqa: PLC0415, F401  # pylint: disable=ungrouped-imports,unused-import
    )
else:
    raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

if TYPE_CHECKING:
    from qtpy import QtGui
    from qtpy.QtCore import QObject
    from qtpy.QtGui import QCloseEvent, QKeyEvent, QMouseEvent
    from qtpy.QtWidgets import QStyle, QWidget
    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]
    from watchdog.observers.api import BaseObserver

    from pykotor.common.module import ModuleResource
    from pykotor.extract.file import LocationResult
    from pykotor.resource.formats.lyt.lyt_data import LYT
    from pykotor.resource.formats.mdl.mdl_data import MDL
    from pykotor.resource.formats.tpc import TPC
    from pykotor.resource.type import SOURCE_TYPES
    from toolset.gui.widgets.main_widgets import TextureList
    from utility.common.more_collections import CaseInsensitiveDict


def run_module_designer(
    active_path: str,
    active_name: str,
    active_tsl: bool,  # noqa: FBT001
    module_path: str | None = None,
):
    """An alternative way to start the ModuleDesigner: run thisfunction in a new process so the main tool window doesn't wait on the module designer."""
    import sys

    from toolset.__main__ import main_init

    main_init()
    app = QApplication(sys.argv)
    designer_ui = ModuleDesigner(
        None,
        HTInstallation(active_path, active_name, tsl=active_tsl),
        CaseAwarePath(module_path) if module_path is not None else None,
    )
    # Standardized resource path format
    icon_path = ":/images/icons/sith.png"

    # Debugging: Check if the resource path is accessible
    if not QPixmap(icon_path).isNull():
        designer_ui.log.debug(f"HT main window Icon loaded successfully from {icon_path}")
        designer_ui.setWindowIcon(QIcon(QPixmap(icon_path)))
        cast(QApplication, QApplication.instance()).setWindowIcon(QIcon(QPixmap(icon_path)))
    else:
        print(f"Failed to load HT main window icon from {icon_path}")
    add_window(designer_ui, show=False)
    sys.exit(app.exec_())


class ToolWindow(QMainWindow):
    """Main window for the Holocron Toolset."""

    sig_module_files_updated: Signal = Signal(str, str)  # pyright: ignore[reportPrivateImportUsage]
    sig_override_files_update: Signal = Signal(object, object)  # pyright: ignore[reportPrivateImportUsage]
    sig_installation_changed: Signal = Signal(HTInstallation)

    MAIN_ICON_PATH: str = ":/images/icons/sith.png"

    def __init__(self):
        """Initialize the main window.

        Args:
        ----
            self: The object instance
            parent: The parent widget

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

        self.previous_game_combo_index: int = 0
        self.settings: GlobalSettings = GlobalSettings()
        self._initUi()
        self._setup_signals()
        self.setWindowTitle(f"Holocron Toolset ({qtpy.API_NAME})")

        # Watchdog
        self.dog_observer: BaseObserver | None = None
        # self.dogHandler: FolderObserver = FolderObserver(self)

        # Theme setup
        q_style: QStyle | None = self.style()
        assert q_style is not None
        self.original_style: str = q_style.objectName()
        self.original_palette: QPalette = self.palette()
        self.change_theme(self.settings.selectedTheme)  # Ensure it comes to the front

        # Finalize the init
        self.reload_settings()
        self.unset_installation()
        self.raise_()
        self.activateWindow()

    def handle_change(self, path: str):
        if self.active is None:
            return

        modified_path = os.path.normpath(path)
        if os.path.isdir(modified_path):  # noqa: PTH112
            return

        now = datetime.now(tz=timezone.utc).astimezone()
        if now - self.last_modified < timedelta(seconds=1):
            print(f"<SDM> [handle_change scope] Skipping change for {modified_path} because it was modified too recently.")
            return
        self.last_modified = now

        module_path = os.path.normpath(self.active.module_path())
        override_path = os.path.normpath(self.active.override_path())

        if module_path.lower() in modified_path.lower():
            self.sig_module_files_updated.emit(modified_path, "modified")
        elif override_path.lower() in modified_path.lower():
            self.sig_override_files_update.emit(modified_path, "modified")

    def _setup_watcher(self):
        """Set up file system watchers for specific paths.

        Code is massive TODO
        """
        assert self.active is not None, "Installation not set"
        paths_to_watch: list[CaseAwarePath] = [
            self.active.lips_path(),
            self.active.module_path(),
            self.active.override_path(),
            self.active.rims_path(),
            self.active.streammusic_path(),
            self.active.streamsounds_path(),
            self.active._find_resource_folderpath(("streamvoice", "streamwaves")),  # noqa: SLF001
            self.active.texturepacks_path(),
        ]
        paths_to_watch.extend(cast(List[CaseAwarePath], self.active.save_locations()))

        # Add paths to both model and watcher
        str_paths_to_watch = list(map(os.path.normpath, paths_to_watch))
        self.fs_gatherer.watchPaths(str_paths_to_watch)
        self.fs_gatherer.updates.connect(self.active.handle_file_system_changes)
        self.fs_gatherer.directoryLoaded.connect(self.handle_change)
        self.fs_gatherer.updates.connect(self.handle_change)
        self.fs_gatherer.newListOfFiles.connect(self.handle_change)
        self.fs_gatherer.nameResolved.connect(self.handle_change)

    def _initUi(self):
        """Initialize Holocron Toolset main window UI."""
        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.windows.main import (
                Ui_MainWindow,  # noqa: PLC0415  # pylint: disable=C0415
            )
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.windows.main import (
                Ui_MainWindow,  # noqa: PLC0415  # pylint: disable=C0415
            )
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.windows.main import (
                Ui_MainWindow,  # noqa: PLC0415  # pylint: disable=C0415
            )
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.windows.main import (
                Ui_MainWindow,  # noqa: PLC0415  # pylint: disable=C0415
            )
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.coreWidget.hide_section()
        self.ui.coreWidget.hide_reload_button()

        if is_debug_mode():
            self.ui.menubar.addAction("Debug Reload").triggered.connect(debug_reload_pymodules)  # pyright: ignore[reportOptionalMemberAccess]

        # Debugging: Check if the resource path is accessible
        if not QPixmap(self.MAIN_ICON_PATH).isNull():
            RobustLogger().debug(f"HT main window Icon loaded successfully from '{self.MAIN_ICON_PATH}'")
            self.setWindowIcon(QIcon(QPixmap(self.MAIN_ICON_PATH)))
            cast(QApplication, QApplication.instance()).setWindowIcon(QIcon(QPixmap(self.MAIN_ICON_PATH)))
        else:
            print(f"Failed to load HT main window icon from {self.MAIN_ICON_PATH}")
        self.setup_modules_tab()

    def setup_modules_tab(self):
        """Setup/customize the modules tab."""
        self.erf_editor_button: QPushButton = QPushButton("ERF Editor", self)
        self.erf_editor_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.erf_editor_button.clicked.connect(self._open_module_tab_erf_editor)  # Connect to the ERF Editor functionality
        self.ui.verticalLayoutRightPanel.insertWidget(2, self.erf_editor_button)  # pyright: ignore[reportArgumentType]
        self.erf_editor_button.hide()

        modules_resource_list = self.ui.modulesWidget.ui
        modules_section_combo: FilterComboBox = cast(FilterComboBox, modules_resource_list.sectionCombo)  # type: ignore[]
        modules_section_combo.__class__ = FilterComboBox
        modules_section_combo.__init__(init=False)
        modules_section_combo.setEditable(False)
        refresh_button: QPushButton = modules_resource_list.refreshButton  # type: ignore[attr-defined]
        designer_button: QPushButton = self.ui.specialActionButton  # type: ignore[attr-defined]
        self.collect_button: QToolButton = QToolButton(self)
        self.collect_button.setText("Collect...")
        # Remove from original layouts
        modules_resource_list.horizontalLayout_2.removeWidget(modules_section_combo)  # type: ignore[arg-type]
        modules_resource_list.horizontalLayout_2.removeWidget(refresh_button)  # type: ignore[arg-type]
        modules_resource_list.verticalLayout.removeItem(modules_resource_list.horizontalLayout_2)  # type: ignore[arg-type]

        # Set size policies
        modules_section_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)  # type: ignore[arg-type]
        modules_section_combo.setMinimumWidth(250)
        refresh_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)  # type: ignore[arg-type]
        designer_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)  # type: ignore[arg-type]
        self.collect_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        # Create a new layout to stack Designer and Refresh buttons
        stack_button_layout = QVBoxLayout()
        stack_button_layout.setSpacing(1)
        stack_button_layout.addWidget(refresh_button)  # type: ignore[arg-type]
        stack_button_layout.addWidget(designer_button)  # type: ignore[arg-type]
        stack_button_layout.addWidget(self.collect_button)

        # Create a new horizontal layout to place the combobox and buttons
        top_layout = QHBoxLayout()
        top_layout.addWidget(modules_section_combo)  # type: ignore[arg-type]
        top_layout.addLayout(stack_button_layout)

        # Insert the new top layout into the vertical layout
        self.ui.verticalLayoutModulesTab.insertLayout(0, top_layout)  # type: ignore[attributeAccessIssue]

        # Adjust the vertical layout to accommodate the combobox height change
        modules_resource_list.verticalLayout.addWidget(modules_resource_list.resourceTree)  # type: ignore[arg-type]
        modules_section_combo.setMaxVisibleItems(18)

        def create_more_actions_menu() -> QMenu:
            menu = QMenu()
            menu.addAction("Room Textures").triggered.connect(self.extract_module_room_textures)  # pyright: ignore[reportOptionalMemberAccess]
            menu.addAction("Room Models").triggered.connect(self.extract_module_room_models)  # pyright: ignore[reportOptionalMemberAccess]
            menu.addAction("Textures").triggered.connect(self.extract_all_module_textures)  # pyright: ignore[reportOptionalMemberAccess]
            menu.addAction("Models").triggered.connect(self.extract_all_module_models)  # pyright: ignore[reportOptionalMemberAccess]
            menu.addAction("Everything").triggered.connect(self.extract_module_everything)  # pyright: ignore[reportOptionalMemberAccess]
            return menu

        self.collect_button_menu: QMenu = create_more_actions_menu()
        self.collect_button_menu.aboutToHide.connect(self.on_menu_hide)
        self.collect_button_menu.leaveEvent = self.on_menu_hide  # type: ignore[attributeAccessIssue]
        self.collect_button.leaveEvent = self.on_menu_hide  # type: ignore[attributeAccessIssue]
        self.collect_button.setMenu(self.collect_button_menu)

        # Show menu on hover
        self.collect_button.setMouseTracking(False)
        self.collect_button.installEventFilter(self)

    @Slot()
    def on_menu_hide(self, *args):
        """Custom slot to handle menu hide actions."""
        self.collect_button.menu().hide()  # pyright: ignore[reportOptionalMemberAccess]
        self.collect_button_menu.close()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # pylint: disable=invalid-name
        """Used for the Collect button auto-collapse logic."""
        if not hasattr(self, "collect_button"):
            return False
        if obj == self.collect_button and event.type() == QEvent.Type.HoverEnter:
            self.collect_button.showMenu()
        return super().eventFilter(obj, event)

    def _setup_signals(self):  # sourcery skip: remove-unreachable-code  # noqa: PLR0915
        """Setup signals for the Holocron Toolset."""
        self.ui.gameCombo.currentIndexChanged.connect(self.change_active_installation)

        self.ui.menuTheme.triggered.connect(self.change_theme)

        self.sig_module_files_updated.connect(self.on_module_file_updated)
        self.sig_override_files_update.connect(self.on_override_file_updated)

        self.ui.coreWidget.sig_request_extract_resource.connect(self.on_extract_resources)
        self.ui.coreWidget.sig_request_open_resource.connect(self.on_open_resources)
        self.ui.coreWidget.sig_request_refresh.connect(self.on_core_refresh)

        self.ui.modulesWidget.sig_section_changed.connect(self.on_module_changed)
        self.ui.modulesWidget.sig_request_reload.connect(self.on_module_reload)
        self.ui.modulesWidget.sig_request_refresh.connect(self.on_module_refresh)
        self.ui.modulesWidget.sig_request_extract_resource.connect(self.on_extract_resources)
        self.ui.modulesWidget.sig_request_open_resource.connect(self.on_open_resources)

        self.ui.savesWidget.sig_section_changed.connect(self.on_savepath_changed)
        self.ui.savesWidget.sig_request_reload.connect(self.on_save_reload)
        self.ui.savesWidget.sig_request_refresh.connect(self.on_save_refresh)
        self.ui.savesWidget.sig_request_extract_resource.connect(self.on_extract_resources)
        self.ui.savesWidget.sig_request_open_resource.connect(self.on_open_resources)
        self.ui.resourceTabs.currentChanged.connect(self.on_tab_changed)

        def open_module_designer() -> ModuleDesigner | None:
            """Open the module designer."""
            assert self.active is not None

            # Uncomment this block to start Module Designer in new process
            # import multiprocessing
            # module_path = self.active.module_path() / self.ui.modulesWidget.currentSection()
            # print("<SDM> [openModuleDesigner scope] module_path: ", module_path)

            # process = multiprocessing.Process(target=run_module_designer, args=(str(self.active.path()), self.active.name, self.active.tsl, str(module_path)))
            # print("<SDM> [openModuleDesigner scope] process: ", process)

            # process.start()
            # BetterMessageBox("Module designer process started", "We have triggered the module designer to open, feel free to use the toolset in the meantime.").exec_()
            # QTimer.singleShot(500, self.debounceModuleDesignerLoad)
            # return None

            designer_ui = ModuleDesigner(
                None,
                self.active,
                self.active.module_path() / self.ui.modulesWidget.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole),
            )

            icon_path = ":/images/icons/sith.png"
            if not QPixmap(icon_path).isNull():
                RobustLogger().debug(f"Module Designer window Icon loaded successfully from {icon_path}")
                designer_ui.setWindowIcon(QIcon(QPixmap(icon_path)))
            else:
                print(f"Failed to load Module Designer window icon from {icon_path}")
            add_window(designer_ui, show=False)
            return designer_ui

        self.ui.specialActionButton.clicked.connect(lambda *args: open_module_designer() and None or None)

        self.ui.overrideWidget.sig_section_changed.connect(self.on_override_changed)
        self.ui.overrideWidget.sig_request_reload.connect(self.on_override_reload)
        self.ui.overrideWidget.sig_request_refresh.connect(self.on_override_refresh)
        self.ui.overrideWidget.sig_request_extract_resource.connect(self.on_extract_resources)
        self.ui.overrideWidget.sig_request_open_resource.connect(self.on_open_resources)

        self.ui.texturesWidget.sig_section_changed.connect(self.on_textures_changed)
        self.ui.texturesWidget.sig_request_open_resource.connect(self.on_open_resources)

        self.ui.extractButton.clicked.connect(
            lambda: self.on_extract_resources(
                self.get_active_resource_widget().selected_resources(),
                resource_widget=self.get_active_resource_widget(),
            ),
        )
        self.ui.openButton.clicked.connect(
            lambda *args: self.on_open_resources(
                self.get_active_resource_widget().selected_resources(),
                self.settings.gff_specializedEditors,
                resource_widget=self.get_active_resource_widget(),
            )
        )

        self.ui.openAction.triggered.connect(self.open_from_file)
        self.ui.actionSettings.triggered.connect(self.open_settings_dialog)
        self.ui.actionExit.triggered.connect(lambda *args: self.close() and None or None)

        self.ui.actionNewTLK.triggered.connect(lambda: add_window(TLKEditor(self, self.active)))
        self.ui.actionNewDLG.triggered.connect(lambda: add_window(DLGEditor(self, self.active)))
        self.ui.actionNewNSS.triggered.connect(lambda: add_window(NSSEditor(self, self.active)))
        self.ui.actionNewUTC.triggered.connect(lambda: add_window(UTCEditor(self, self.active)))
        self.ui.actionNewUTP.triggered.connect(lambda: add_window(UTPEditor(self, self.active)))
        self.ui.actionNewUTD.triggered.connect(lambda: add_window(UTDEditor(self, self.active)))
        self.ui.actionNewUTI.triggered.connect(lambda: add_window(UTIEditor(self, self.active)))
        self.ui.actionNewUTT.triggered.connect(lambda: add_window(UTTEditor(self, self.active)))
        self.ui.actionNewUTM.triggered.connect(lambda: add_window(UTMEditor(self, self.active)))
        self.ui.actionNewUTW.triggered.connect(lambda: add_window(UTWEditor(self, self.active)))
        self.ui.actionNewUTE.triggered.connect(lambda: add_window(UTEEditor(self, self.active)))
        self.ui.actionNewUTS.triggered.connect(lambda: add_window(UTSEditor(self, self.active)))
        self.ui.actionNewGFF.triggered.connect(lambda: add_window(GFFEditor(self, self.active)))
        self.ui.actionNewERF.triggered.connect(lambda: add_window(ERFEditor(self, self.active)))
        self.ui.actionNewTXT.triggered.connect(lambda: add_window(TXTEditor(self, self.active)))
        self.ui.actionNewSSF.triggered.connect(lambda: add_window(SSFEditor(self, self.active)))
        self.ui.actionCloneModule.triggered.connect(lambda: add_window(CloneModuleDialog(self, self.active, self.installations)))

        self.ui.actionModuleDesigner.triggered.connect(self.open_module_designer)
        self.ui.actionEditTLK.triggered.connect(self.open_active_talktable)
        self.ui.actionEditJRL.triggered.connect(self.open_active_journal)
        self.ui.actionFileSearch.triggered.connect(self.open_file_search_dialog)
        self.ui.actionIndoorMapBuilder.triggered.connect(self.open_indoor_map_builder)

        self.ui.actionInstructions.triggered.connect(self.open_instructions_window)
        self.ui.actionHelpUpdates.triggered.connect(self.check_for_updates)
        self.ui.actionHelpAbout.triggered.connect(self.open_about_dialog)
        self.ui.actionDiscordDeadlyStream.triggered.connect(lambda: openLink("https://discord.com/invite/bRWyshn"))
        self.ui.actionDiscordKotOR.triggered.connect(lambda: openLink("http://discord.gg/kotor"))
        self.ui.actionDiscordHolocronToolset.triggered.connect(lambda: openLink("https://discord.gg/3ME278a9tQ"))

        self.ui.menuRecentFiles.aboutToShow.connect(self.populate_recent_files_menu)

    def check_for_updates(self, *, silent: bool = False):
        """Scans for any updates and opens a dialog with a message based on the scan result.

        Args:
        ----
            silent: If true, only shows popup if an update is available.
        """
        try:
            self._check_toolset_update(silent=silent)
            print("<SDM> [checkForUpdates scope] silent: ", silent)

        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            RobustLogger().exception("Failed to check for updates.")
            if not silent:
                etype, msg = universal_simplify_exception(e)
                print("<SDM> [checkForUpdates scope] msg: ", msg)

                QMessageBox(
                    QMessageBox.Icon.Information,
                    f"Unable to fetch latest version ({etype})",
                    f"Check if you are connected to the internet.\nError: {msg}",
                    QMessageBox.Ok,
                    self,
                ).exec_()

    def _check_toolset_update(self, *, silent: bool):
        self.check_update_thread: UpdateCheckThread = UpdateCheckThread(self, silent=silent)
        self.check_update_thread.update_info_fetched.connect(self._on_update_info_fetched)
        self.check_update_thread.start()

    @Slot(dict, dict, bool)
    def _on_update_info_fetched(self, master_info: dict[str, Any], edge_info: dict[str, Any], silent: bool):  # noqa: FBT001
        print("<SDM> [display_version_message scope] edge_info: ", edge_info)

        def determine_version_info(
            edge_remote_info: dict[str, Any],
            master_remote_info: dict[str, Any],
        ) -> tuple[dict[str, Any], bool]:
            """Determines the version info from the remote info."""
            version_list: list[tuple[Literal["toolsetLatestVersion", "toolsetLatestBetaVersion"], Literal["master", "edge"], str]] = []
            print("<SDM> [determine_version_info scope] version_list: ", version_list)

            if self.settings.useBetaChannel:
                version_list.append(("toolsetLatestVersion", "master", master_remote_info.get("toolsetLatestVersion", "")))
                version_list.append(("toolsetLatestVersion", "edge", edge_remote_info.get("toolsetLatestVersion", "")))
                version_list.append(("toolsetLatestBetaVersion", "master", master_remote_info.get("toolsetLatestBetaVersion", "")))
                version_list.append(("toolsetLatestBetaVersion", "edge", edge_remote_info.get("toolsetLatestBetaVersion", "")))
            else:
                version_list.append(("toolsetLatestVersion", "master", master_remote_info.get("toolsetLatestVersion", "")))

            # Sort the version list using remoteVersionNewer to determine order
            version_list.sort(key=lambda x: bool(is_remote_version_newer("0.0.0", x[2])))

            release_version = version_list[0][0] == "toolsetLatestVersion"
            print("<SDM> [determine_version_info scope] release_version: ", release_version)

            remote_info: dict[str, Any] = edge_remote_info if version_list[0][1] == "edge" else master_remote_info
            return remote_info, release_version

        def display_version_message(
            is_up_to_date: bool,  # noqa: FBT001
            cur_version_str: str,
            greatest_version: str,
            notes: str,
            download_link: str,
            remote_info: dict[str, Any],
            release_version_checked: bool,  # noqa: FBT001
        ):
            if is_up_to_date:
                if silent:
                    return
                up_to_date_msg_box = QMessageBox(
                    QMessageBox.Icon.Information,
                    "Version is up to date",
                    f"You are running the latest {cur_version_str}version ({CURRENT_VERSION}).",
                    QMessageBox.Ok | QMessageBox.Yes | QMessageBox.Close,
                    parent=None,
                    flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,  # pyright: ignore[reportArgumentType]
                )
                print("<SDM> [display_version_message scope] up_to_date_msg_box: ", up_to_date_msg_box)

                up_to_date_msg_box.button(QMessageBox.Ok).setText("Auto-Update")
                up_to_date_msg_box.button(QMessageBox.Yes).setText("Choose Update")
                up_to_date_msg_box.setWindowIcon(self.windowIcon())
                result = up_to_date_msg_box.exec_()
                print("<SDM> [display_version_message scope] result: ", result)

                if result == QMessageBox.Ok:
                    self.autoupdate_toolset(greatest_version, remote_info, is_release=release_version_checked)
                elif result == QMessageBox.Yes:
                    toolset_updater = UpdateDialog(self)
                    print("<SDM> [display_version_message scope] toolset_updater: ", toolset_updater)

                    toolset_updater.exec_()
                return
            beta_string: Literal["release ", "beta "] = "release " if release_version_checked else "beta "
            new_version_msg_box = QMessageBox(
                QMessageBox.Icon.Information,
                f"Your toolset version {CURRENT_VERSION} is outdated.",
                f"A new toolset {beta_string}version ({greatest_version}) is available for <a href='{download_link}'>download</a>.<br><br>{notes}",
                QMessageBox.Yes | QMessageBox.Abort,
                parent=None,
                flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,
            )
            print("<SDM> [display_version_message scope] new_version_msg_box: ", new_version_msg_box)

            new_version_msg_box.setDefaultButton(QMessageBox.StandardButton.Abort)
            new_version_msg_box.button(QMessageBox.StandardButton.Ok).setText("Auto-Update")
            new_version_msg_box.button(QMessageBox.StandardButton.Yes).setText("Details")
            new_version_msg_box.button(QMessageBox.StandardButton.Abort).setText("Ignore")
            new_version_msg_box.setWindowIcon(self.windowIcon())
            response: QMessageBox.StandardButton = new_version_msg_box.exec_()
            print("<SDM> [display_version_message scope] response: ", response)
            if response == QMessageBox.StandardButton.Ok:
                self.autoupdate_toolset(greatest_version, edge_info, is_release=release_version_checked)
            elif response == QMessageBox.StandardButton.Yes:
                toolset_updater = UpdateDialog(self)
                print("<SDM> [display_version_message scope] toolset_updater: ", toolset_updater)

                toolset_updater.exec_()

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

        version_check = is_remote_version_newer(CURRENT_VERSION, greatest_available_version)
        print("<SDM> [display_version_message scope] version_check: ", version_check)

        cur_version_beta_release_str = ""
        print("<SDM> [display_version_message scope] remote_info[toolsetLatestVersion]: ", remote_info["toolsetLatestVersion"])
        print("<SDM> [display_version_message scope] remote_info[toolsetLatestBetaVersion]: ", remote_info["toolsetLatestBetaVersion"])
        if remote_info["toolsetLatestVersion"] == CURRENT_VERSION:
            cur_version_beta_release_str = "release "
        elif remote_info["toolsetLatestBetaVersion"] == CURRENT_VERSION:
            cur_version_beta_release_str = "beta "

        display_version_message(
            version_check is False, cur_version_beta_release_str, greatest_available_version, toolset_latest_notes, toolset_download_link, remote_info, release_version_checked
        )

    def autoupdate_toolset(
        self,
        latest_version: str,
        remote_info: dict[str, Any],
        *,
        is_release: bool,
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

        is_release = False  # TODO(th3w1zard1): remove this line when the release version direct links are ready.
        if is_release:
            links = remote_info["toolsetDirectLinks"][os_name][proc_arch.value]
        else:
            links = remote_info["toolsetBetaDirectLinks"][os_name][proc_arch.value]
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

        updater = AppUpdate(links, "HolocronToolset", CURRENT_VERSION, latest_version, downloader=None, progress_hooks=progress_hooks, exithook=exitapp)  # type: ignore[arg-type]
        print("<SDM> [exitapp scope] updater: ", updater)

        try:
            progress_queue.put({"action": "update_status", "text": "Downloading update..."})
            updater.download(background=False)
            progress_queue.put({"action": "update_status", "text": "Restarting and Applying update..."})
            updater.extract_restart()
            progress_queue.put({"action": "update_status", "text": "Cleaning up..."})
            updater.cleanup()
        except Exception:
            RobustLogger().exception("Failed to complete the updater")
        finally:
            exitapp(True)

    @Slot()
    def populate_recent_files_menu(self):
        """Populate the Recent Files menu with the recent files."""
        recent_files_setting: list[str] = self.settings.recentFiles
        recent_files: list[Path] = [Path(file) for file in recent_files_setting]
        self.ui.menuRecentFiles.clear()
        for file in recent_files:
            action = QAction(file.name, self)
            action.setData(file)
            action.triggered.connect(self.open_recent_file)
            self.ui.menuRecentFiles.addAction(action)  # type: ignore[arg-type]

    @Slot()
    def open_recent_file(self):
        """Open a file from the Recent Files menu."""
        obj_ret: QObject | None = self.sender()
        if not isinstance(obj_ret, QAction):
            return
        action: QAction = obj_ret
        print("<SDM> [open_recent_file scope] action: ", action)

        if not action:
            return
        if not isinstance(action, QAction):
            return
        file = action.data()

        if not file:
            return
        if not isinstance(file, Path):
            return
        resource: FileResource = FileResource.from_path(file)
        print("<SDM> [open_recent_file scope] resource: ", resource)

        open_resource_editor(file, resource.resname(), resource.restype(), resource.data(), self.active, self)

    @Slot(QApplication, str, object, object, bool)
    def apply_style(
        self,
        app: QApplication,
        sheet: str = "",
        style: str | None = None,
        palette: QPalette | None = None,
        *,
        repaint_all_widgets: bool = True,
    ):
        app.setStyleSheet(sheet)
        # self.setWindowFlags(selfFlags() & ~Qt.WindowType.FramelessWindowHint)
        if style is None or style == self.original_style:
            app.setStyle(self.original_style)
        else:
            app.setStyle(style)
            if palette:
                ...
                # still can't get the custom title bar working, leave this disabled until we do.
                # self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        app_style: QStyle | None = app.style()
        if palette is None and app_style is not None:
            palette = app_style.standardPalette()
        if palette is not None:
            app.setPalette(palette)
        if repaint_all_widgets:
            for widget in app.allWidgets():
                if palette is not None:
                    widget.setPalette(palette)
                widget.repaint()

    @Slot()
    def change_theme(self, theme: QAction | str | None = None):
        """Changes the theme of the application.

        Args:
            theme (QAction | str | None): The theme to change to.
        """
        app: QCoreApplication | None = QApplication.instance()
        assert isinstance(app, QApplication), "No Qt Application found or not a QApplication instance."

        print("<SDM> [toggle_stylesheet scope] self.settings.selectedTheme: ", self.settings.selectedTheme)
        self.settings.selectedTheme = theme.text() if isinstance(theme, QAction) else theme
        self.apply_style(app)

        app_style: QStyle | None = app.style()
        assert app_style is not None
        standard_palette: QPalette = app_style.standardPalette()

        palette: QPalette | None = None
        sheet: str = ""
        style: str = self.original_style
        if self.settings.selectedTheme == "Native":
            style = self.original_style
            palette = standard_palette
        elif self.settings.selectedTheme == "Fusion (Light)":
            style = "Fusion"
            self.apply_style(app, sheet, "Fusion")
        elif self.settings.selectedTheme == "Fusion (Dark)":
            style = "Fusion"
            palette = self.create_palette(
                QColor(53, 53, 53),
                QColor(35, 35, 35),
                QColor(240, 240, 240),
                QColor(25, 25, 25),
                self.adjust_color(QColor("orange"), saturation=80, hue_shift=-10),
                QColor(255, 69, 0),
            )
        elif self.settings.selectedTheme == "QDarkStyle":
            try:
                import qdarkstyle  # pyright: ignore[reportMissingTypeStubs]
            except ImportError:
                QMessageBox.critical(self, "Theme not found", "QDarkStyle is not installed in this environment.")
            else:
                app.setStyle(self.original_style)
                app.setPalette(standard_palette)
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
            # palette = self.create_palette("#ECECEC", "#D2D8DD", "#272727", "#FBFDFD", "#467DD1", "#FFFFFF")
        elif self.settings.selectedTheme == "ManjaroMix":
            sheet = self._get_file_stylesheet(":/themes/other/ManjaroMix.qss", app)
            palette = self.create_palette("#222b2e", "#151a1e", "#FFFFFF", "#214037", "#4fa08b", "#027f7f")
        elif self.settings.selectedTheme == "MaterialDark":
            style = "Fusion"
            sheet = self._get_file_stylesheet(":/themes/other/MaterialDark.qss", app)
            palette = self.create_palette("#1E1D23", "#1E1D23", "#FFFFFF", "#007B50", "#04B97F", "#37EFBA")
        elif self.settings.selectedTheme == "NeonButtons":
            ...
            # sheet = self._get_file_stylesheet(":/themes/other/NeonButtons.qss", app)
        elif self.settings.selectedTheme == "Ubuntu":
            ...
            # sheet = self._get_file_stylesheet(":/themes/other/Ubuntu.qss", app)
            # palette = self.create_palette("#f0f0f0", "#1e1d23", "#000000", "#f68456", "#ec743f", "#ffffff")
        elif self.settings.selectedTheme == "Breeze (Dark)":
            if qtpy.QT6:
                QMessageBox(QMessageBox.Icon.Critical, "Breeze Unavailable", "Breeze is only supported on qt5 at this time.").exec_()
                return
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

    def adjust_color(
        self,
        color: Any,
        lightness: int = 100,
        saturation: int = 100,
        hue_shift: int = 0,
    ) -> QColor:
        """Adjusts the color's lightness, saturation, and hue."""
        qcolor = QColor(color)
        h, s, v, _ = qcolor.getHsv()
        s = max(0, min(255, s * saturation // 100))
        v = max(0, min(255, v * lightness // 100))
        h = (h + hue_shift) % 360
        qcolor.setHsv(h, s, v)
        return qcolor

    def create_palette(  # noqa: PLR0913, C901
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
            QPalette.ColorRole.Dark: self.adjust_color(primary, lightness=80),
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
            QPalette.ColorRole.PlaceholderText: self.adjust_color(text, lightness=70),
        }

        # Special handling for PyQt5 and PyQt6
        if qtpy.QT5:
            extra_roles = {
                QPalette.ColorRole.Background: self.adjust_color(primary, lightness=110),  # Use Background for PyQt5
                QPalette.ColorRole.Foreground: self.adjust_color(text, lightness=95),  # Use Foreground for PyQt5
            }
        else:
            # In PyQt6, Background and Foreground are handled with Window and WindowText respectively
            extra_roles: dict[QPalette.ColorRole, QColor] = {
                QPalette.ColorRole.Window: self.adjust_color(secondary, lightness=110),
                QPalette.ColorRole.WindowText: self.adjust_color(text, lightness=95),
            }
        role_colors.update(extra_roles)
        for role, color in role_colors.items():
            palette.setColor(QPalette.ColorGroup.Normal, role, color)

        # Create disabled and inactive variations
        for state_key, saturation_factor, lightness_factor in [
            (QPalette.ColorGroup.Disabled, 80, 60),  # More muted and slightly darker
            (QPalette.ColorGroup.Inactive, 90, 80),  # Slightly muted
        ]:
            for role, base_color in role_colors.items():
                adjusted_color: QColor = self.adjust_color(
                    base_color,
                    saturation=saturation_factor,
                    lightness=lightness_factor,
                )
                palette.setColor(state_key, role, adjusted_color)

        return palette

    # region Signal callbacks
    @Slot()
    def on_core_refresh(self):
        """Refreshes the list of cores available at the active installation's core path."""
        RobustLogger().debug("ToolWindow.onCoreRefresh()")
        self.refresh_core_list(reload=True)

    @Slot(str)
    def on_module_changed(self, new_module_file: str):
        """Called when the currently selected module file changes.

        Args:
            new_module_file (str): The new module file that is currently selected.
        """
        RobustLogger().debug(f"ToolWindow.onModuleChanged(newModuleFile='{new_module_file}')")
        self.on_module_reload(new_module_file)

    @Slot(bool)
    def on_module_refresh(self, reload: bool = True):
        """Refreshes the list of modules available at the active installation's module path.

        Args:
            reload (bool, optional): Whether to reload the module list. Defaults to True.
        """
        RobustLogger().debug("ToolWindow.onModuleRefresh()")
        self.refresh_module_list(reload=reload)

    @Slot(str)
    def on_module_reload(self, module_file: str):
        """Reloads the module file and updates the UI.

        Args:
            module_file (str): The module file to reload.
        """
        RobustLogger().debug(f"ToolWindow.onModuleReload(moduleFile='{module_file}')")
        assert self.active is not None, "No active installation selected"
        if not module_file or not module_file.strip():
            print(f"onModuleReload: can't reload module '{module_file}', invalid name")
            return
        resources: list[FileResource] = self.active.module_resources(module_file)
        print("<SDM> [onModuleReload scope] resources: ", len(resources))

        # Some users may choose to have their RIM files for the same module merged into a single option for the
        # dropdown menu.
        module_file_name = PurePath(module_file).name
        if self.settings.joinRIMsTogether and ((is_rim_file(module_file) or is_erf_file(module_file)) and not module_file_name.lower().endswith(("_s.rim", "_dlg.erf"))):
            resources.extend(self.active.module_resources(f"{PurePath(module_file).stem}_s.rim"))
            if self.active.game().is_k2():
                resources.extend(self.active.module_resources(f"{PurePath(module_file).stem}_dlg.erf"))

        self.active.reload_module(module_file)
        self.ui.modulesWidget.set_resources(resources)

    @Slot(str, str)
    def on_module_file_updated(self, changed_file: str, event_type: str):
        """Event callback when a module file is updated.

        Args:
            changed_file (str): The file that was changed.
            event_type (str): The type of event that occurred.
        """
        RobustLogger().debug(f"ToolWindow.onModuleFileUpdated(changedFile='{changed_file}', eventType='{event_type}')")
        assert self.active is not None
        if event_type == "deleted":
            self.on_module_refresh()
        else:
            # Reload the resource cache for the module
            self.active.reload_module(changed_file)
            # If the current module opened is the file which was updated, then we
            # should refresh the ui.
            if self.ui.modulesWidget.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole) == changed_file:
                self.on_module_reload(changed_file)

    @Slot(str)
    def on_savepath_changed(self, new_save_dir: str):
        """Event callback when the save directory changes.

        Args:
            new_save_dir (str): The new save directory.
        """
        print("<SDM> [onSavepathChanged scope] new_save_dir: ", new_save_dir)
        RobustLogger().debug(f"ToolWindow.onSavepathChanged(newSaveDir='{new_save_dir}')")
        assert self.active is not None
        print("Loading save resources into UI...")

        # Clear the entire model before loading new save resources
        self.ui.savesWidget.modules_model.invisibleRootItem().removeRows(0, self.ui.savesWidget.modules_model.rowCount())  # pyright: ignore[reportOptionalMemberAccess]
        new_save_dir_path = CaseAwarePath(new_save_dir)
        print("<SDM> [onSavepathChanged scope] newSaveDirPath: ", new_save_dir_path)

        if new_save_dir_path not in self.active.saves:
            self.active.load_saves()
        if new_save_dir_path not in self.active.saves:
            print(f"Cannot load save {new_save_dir_path}: not found in saves list")
            return

        for save_path, resource_list in self.active.saves[new_save_dir_path].items():
            # Create a new parent item for the save_path
            save_path_item = QStandardItem(str(save_path.relative_to(save_path.parent.parent)))
            # print("<SDM> [onSavepathChanged scope] save_path_item: ", save_path_item)

            self.ui.savesWidget.modules_model.invisibleRootItem().appendRow(save_path_item)  # pyright: ignore[reportOptionalMemberAccess]

            # Dictionary to keep track of category items under this save_path_item
            category_items_under_save_path: dict[str, QStandardItem] = {}

            for resource in resource_list:
                restype: ResourceType = resource.restype()
                # print("<SDM> [onSavepathChanged scope] ResourceType: ", restype)

                category: str = restype.category
                # print("<SDM> [onSavepathChanged scope] category: ", category)

                # Check if the category item already exists under this save_path_item
                if category not in category_items_under_save_path:
                    # Create new category item similar to _getCategoryItem logic
                    category_item = QStandardItem(category)
                    category_item.setSelectable(False)
                    unused_item = QStandardItem("")
                    unused_item.setSelectable(False)
                    save_path_item.appendRow([category_item, unused_item])
                    category_items_under_save_path[category] = category_item

                # Now, categoryItem is guaranteed to exist
                category_item = category_items_under_save_path[category]
                # print("<SDM> [onSavepathChanged scope] categoryItem: ", categoryItem.text())

                # Check if resource is already listed under this category
                from toolset.gui.widgets.main_widgets import ResourceStandardItem

                found_resource = False
                print("<SDM> [onSavepathChanged scope] category_item: ", category_item)
                for i in range(category_item.rowCount()):
                    item = category_item.child(i)
                    if item is not None and isinstance(item, ResourceStandardItem) and item.resource == resource:
                        # Update the resource reference if necessary
                        print("<SDM> [onSavepathChanged scope] item: ", item)
                        item.resource = resource
                        found_resource = True
                        break

                if not found_resource:
                    # Add new resource under the category
                    item1 = ResourceStandardItem(resource.resname(), resource=resource)
                    item2 = QStandardItem(restype.extension.upper())
                    category_item.appendRow([item1, item2])

    def on_save_reload(self, save_dir: str):
        RobustLogger().debug(f"ToolWindow.onSaveReload(saveDir='{save_dir}')")
        self.on_savepath_changed(save_dir)

    def on_save_refresh(self):
        RobustLogger().debug("ToolWindow.onSaveRefresh()")
        self.refresh_saves_list()

    def on_override_file_updated(self, changed_file: str, event_type: str):
        RobustLogger().debug(f"ToolWindow.onOverrideFileUpdated(changedFile='{changed_file}', eventType={event_type})")
        print("<SDM> [onOverrideFileUpdated scope] eventType: ", event_type)

        if event_type == "deleted":
            print("<SDM> [onOverrideFileUpdated scope] eventType: ", event_type)

            self.on_override_refresh()
        else:
            self.on_override_reload(changed_file)

    def on_override_changed(self, new_directory: str):
        RobustLogger().debug(f"ToolWindow.onOverrideChanged(newDirectory='{new_directory}')")
        assert self.active is not None
        self.ui.overrideWidget.set_resources(self.active.override_resources(new_directory))

    def on_override_reload(self, file_or_folder: str):
        """Called when an override file or folder is changed.

        Args:
            file_or_folder (str): The file or folder that was changed.
        """
        RobustLogger().debug(f"ToolWindow.onOverrideReload(file_or_folder='{file_or_folder}')")
        assert self.active is not None
        override_path = self.active.override_path()
        print("<SDM> [onOverrideReload scope] override_path: ", override_path)

        file_or_folder_path = override_path.joinpath(file_or_folder)
        print("<SDM> [onOverrideReload scope] file_or_folder_path: ", file_or_folder_path)

        if not file_or_folder_path.is_relative_to(self.active.override_path()):
            raise ValueError(f"'{file_or_folder_path}' is not relative to the override folder, cannot reload")
        if file_or_folder_path.is_file():
            rel_folderpath = file_or_folder_path.parent.relative_to(self.active.override_path())
            print("<SDM> [onOverrideReload scope] rel_folderpath: ", rel_folderpath)

            self.active.reload_override_file(file_or_folder_path)
        else:
            rel_folderpath = file_or_folder_path.relative_to(self.active.override_path())
            print("<SDM> [onOverrideReload scope] rel_folderpath: ", rel_folderpath)

            self.active.load_override(str(rel_folderpath))
        self.ui.overrideWidget.set_resources(self.active.override_resources(str(rel_folderpath) if rel_folderpath.name else None))

    def on_override_refresh(self):
        """Refreshes the list of override folders available at the active installation's override path."""
        RobustLogger().debug("ToolWindow.onOverrideRefresh()")
        assert self.active is not None
        print(f"Refreshing list of override folders available at {self.active.path()}")
        self.refresh_override_list(reload=True)

    def on_textures_changed(self, texturepackName: str):
        """Called when a texture pack is changed.

        Args:
            texturepackName (str): The name of the texture pack that was changed.
        """
        RobustLogger().debug(f"ToolWindow.onTexturesChanged(texturepackName='{texturepackName}')")
        assert self.active is not None
        self.ui.texturesWidget.set_resources(self.active.texturepack_resources(texturepackName))

    @Slot(int)
    def change_active_installation(self, index: int):  # noqa: PLR0915, C901, PLR0912
        """Changes the active installation selected.

        If an installation does not have a path yet set, the user is prompted
        to select a directory for it. If the installation path remains unset then the active
        installation also remains unselected.

        Args:
        ----
            index (int): Index of the installation in the installationCombo combobox.
        """
        RobustLogger().debug(f"ToolWindow.change_active_installation(index={index})")
        print("<SDM> [change_active_installation scope] index: ", index)

        if index < 0:  # self.ui.gameCombo.clear() will call this function with -1
            print(f"Index out of range - {index} (expected zero or positive)")
            return

        prev_index: int = self.previous_game_combo_index
        print("<SDM> [change_active_installation scope] prev_index: ", prev_index)

        self.ui.gameCombo.setCurrentIndex(index)

        if index == 0:
            print("<SDM> [unset installation scope]. index: ", index)
            self.unset_installation()
            self.previous_game_combo_index = 0
            return

        name: str = self.ui.gameCombo.itemText(index)
        print("<SDM> [change_active_installation scope] name: ", name)

        path: str = self.settings.installations()[name].path.strip()
        print("<SDM> [change_active_installation scope] path: ", path)

        tsl: bool = self.settings.installations()[name].tsl
        print("<SDM> [change_active_installation scope] tsl: ", tsl)

        # If the user has not set a path for the particular game yet, ask them too.
        if not path or not path.strip() or not CaseAwarePath(path).is_dir():
            if path and path.strip():
                QMessageBox(QMessageBox.Icon.Warning, f"Installation '{path}' not found", "Select another path now.").exec_()
            path = QFileDialog.getExistingDirectory(self, f"Select the game directory for {name}", "Knights of the Old Republic II" if tsl else "swkotor")
            print("<SDM> [change_active_installation scope] path: ", path)

        # If the user still has not set a path, then return them to the [None] option.
        if not path or not path.strip():
            print("User did not choose a path for this installation.")
            self.ui.gameCombo.setCurrentIndex(prev_index)
            return

        active: HTInstallation | None = self.installations.get(name)
        if active is not None:
            self.active = active

        else:
            loader: AsyncLoader | None = None
            if not GlobalSettings().load_entire_installation:
                self.active = HTInstallation(CaseAwarePath(path), name, tsl=tsl)
            else:

                def load_task() -> HTInstallation:
                    profiler = None
                    if self.settings.profileToolset and cProfile is not None:
                        profiler = cProfile.Profile()
                        profiler.enable()
                    progress_callback = None  # pyright: ignore[reportAssignmentType]
                    if loader is not None and loader._realtime_progress:  # noqa: SLF001

                        def progress_callback(  # pylint: disable=function-redefined
                            data: int | str,
                            mtype: Literal[
                                "set_maximum",
                                "increment",
                                "update_maintask_text",
                                "update_subtask_text",
                            ],
                        ):
                            assert loader is not None
                            loader._worker.progress.emit(data, mtype)  # noqa: SLF001

                    new_active: HTInstallation = HTInstallation(
                        CaseAwarePath(path),
                        name,
                        tsl=tsl,
                        progress_callback=progress_callback,
                    )
                    if self.settings.profileToolset and profiler is not None:
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
                    self.ui.gameCombo.setCurrentIndex(prev_index)
                    return
                assert loader.value is not None
                self.active = loader.value

        # KEEP UI CODE IN MAIN THREAD!
        self.ui.resourceTabs.setEnabled(True)
        self.ui.sidebar.setEnabled(True)

        def prepare_task() -> tuple[list[QStandardItem] | None, ...]:
            """Prepares the lists of modules, overrides, and textures for the active installation.

            Returns:
            -------
                tuple[list[QStandardItem] | None, ...]: A tuple containing the lists of modules, overrides, and textures.
            """
            profiler = None
            if self.settings.profileToolset and cProfile is not None:
                profiler = cProfile.Profile()
                profiler.enable()
            ret_tuple: tuple[list[QStandardItem] | None, ...] = (
                self._get_modules_list(reload=False),
                self._get_override_list(reload=False),
                self._get_texture_pack_list(reload=False),
            )
            if self.settings.profileToolset and profiler:
                profiler.disable()
                profiler.dump_stats(str(Path("prepare_task.pstat").absolute()))
            return ret_tuple

        prepare_loader = AsyncLoader(self, "Preparing resources...", lambda: prepare_task(), "Failed to load installation")
        if not prepare_loader.exec_():
            print("prepare_loader.exec_() failed.")
            self.ui.gameCombo.setCurrentIndex(prev_index)
            return
        assert prepare_loader.value
        assert self.active is not None

        # Any issues past this point must call self.unsetInstallation()
        try:
            RobustLogger().debug("Set sections of prepared lists")
            module_items, override_items, texture_items = prepare_loader.value
            assert module_items is not None
            assert override_items is not None
            assert texture_items is not None
            self.ui.modulesWidget.set_sections(module_items)
            self.ui.overrideWidget.set_sections(override_items)
            self.ui.overrideWidget.ui.sectionCombo.setVisible(self.active.tsl)
            self.ui.overrideWidget.ui.refreshButton.setVisible(self.active.tsl)
            self.ui.texturesWidget.set_sections(texture_items)
            self.refresh_core_list(reload=True)
            self.refresh_saves_list(reload=True)
            # FIXME(th3w1zard1): Not once in my life have I seen this watchdog report modified files correctly. Not even in Cortisol's last release version.
            # Causes a hella slowdown on Linux, something to do with internal logging since it seems to be overly tracking `os.stat_result` and creating
            # about 20 debug logs every second, spamming both our logs and the console.`
            # What we should do instead, is save the Installation instance to our QSettings, modify FileResource cls to store a LastModified attr, and onLoad we just
            # load only the files that were changed. Would reduce toolset startups by a ton.
            # self.dogObserver = Observer()
            # self.dogObserver.schedule(self.dogHandler, self.active.path(), recursive=True)
            # self.dogObserver.start()
            try:
                RobustLogger().debug("Setting up watchdog observer...")
                # if self.dogObserver is not None:
                #    RobustLogger().debug("Stopping old watchdog service...")
                #    self.dogObserver.stop()
            except Exception:  # noqa: BLE001
                RobustLogger().exception("An unexpected exception occurred while dealing with watchdog.")

            # self._setup_watcher()
        except Exception as e:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            RobustLogger().exception("Failed to initialize the installation")
            QMessageBox(
                QMessageBox.Icon.Critical,
                "An unexpected error occurred initializing the installation.",
                f"Failed to initialize the installation {name}<br><br>{e}",
            ).exec_()
            self.unset_installation()
            self.previous_game_combo_index = 0
        else:
            self.update_menus()
            RobustLogger().info("Loader task completed.")
            self.settings.installations()[name].path = path
            self.installations[name] = self.active  # pyright: ignore[reportArgumentType]
        self.show()
        self.activateWindow()
        self.previous_game_combo_index = index

        if self.active:
            self.sig_installation_changed.emit(self.active)

    @Slot(str)
    def _save_capsule_from_tool_ui(self, module_name: str):
        """Saves a capsule file from the tool UI.

        Args:
            module_name (str): The name of the module to save.
        """
        assert self.active is not None
        c_filepath: CaseAwarePath = self.active.module_path() / module_name
        print("<SDM> [_saveCapsuleFromToolUI scope] c_filepath: ", c_filepath)

        capsule_filter: str = "Module (*.mod);;Encapsulated Resource File (*.erf);;Resource Image File (*.rim);;Save (*.sav);;All Capsule Types (*.erf; *.mod; *.rim; *.sav)"
        capsule_type: str = "mod"
        if is_erf_file(c_filepath):
            capsule_type = "erf"
        elif is_rim_file(c_filepath):
            capsule_type = "rim"
        extension_to_filter: dict[str, str] = {
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
            capsule_filter,
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
            RobustLogger().exception("Error extracting capsule file '%s'", module_name)
            QMessageBox(QMessageBox.Icon.Critical, "Error saving capsule file", str(universal_simplify_exception(e))).exec_()

    def on_open_resources(
        self,
        resources: list[FileResource],
        use_specialized_editor: bool | None = None,
        resource_widget: ResourceList | TextureList | None = None,
    ):
        """A signal callback from a various trigger (probably main_widgets.py) telling us the user wants to open a resource.

        Args:
        ----
            resources (list[FileResource]): A list of FileResource objects representing the resources to open.
            useSpecializedEditor (bool | None, optional): Whether to use specialized editors. Defaults to None.
            resourceWidget (ResourceList | TextureList | None, optional): The widget displaying the resources. Defaults to None.
        """
        print(f"ToolWindow.onOpenResources(resources={resources!r}, useSpecializedEditor={use_specialized_editor}, resourceWidget={resource_widget})")
        if not self.active:
            return
        for resource in resources:
            _filepath, _editor = open_resource_editor(
                resource.filepath(),
                resource.resname(),
                resource.restype(),
                resource.data(reload=True),
                self.active,
                self,
                gff_specialized=use_specialized_editor,
            )
            print("<SDM> [onOpenResources scope] _editor: ", _editor)

        if resources:
            return
        if not isinstance(resource_widget, ResourceList):
            return
        filename: str = resource_widget.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        print("<SDM> [onOpenResources scope] filename: ", filename)

        if not filename:
            return
        erf_filepath: CaseAwarePath = self.active.module_path() / filename
        print("<SDM> [onOpenResources scope] erf_filepath: ", erf_filepath)

        if not erf_filepath.is_file():
            RobustLogger().info(f"Not loading '{erf_filepath}'. File does not exist")
            return
        res_ident: ResourceIdentifier = ResourceIdentifier.from_path(erf_filepath)
        print("<SDM> [onOpenResources scope] res_ident: ", res_ident)

        if not res_ident.restype:
            RobustLogger().info(f"Not loading '{erf_filepath}'. Invalid resource")
            return
        _filepath, _editor = open_resource_editor(
            erf_filepath,
            res_ident.resname,
            res_ident.restype,
            BinaryReader.load_file(erf_filepath),
            self.active,
            self,
            gff_specialized=use_specialized_editor,
        )
        print("<SDM> [onOpenResources scope] _editor: ", _editor)

    # FileSearcher/FileResults
    @Slot(list, HTInstallation)
    def handle_search_completed(
        self,
        results_list: list[FileResource],
        searched_installations: HTInstallation,
    ):
        """Event callback when the file searcher has completed its search."""
        results_dialog = FileResults(self, results_list, searched_installations)
        print("<SDM> [handle_search_completed scope] results_list: ", len(results_list))

        results_dialog.setModal(False)
        add_window(results_dialog, show=False)
        results_dialog.show()
        results_dialog.selectionSignal.connect(self.handle_results_selection)

    @Slot(FileResource)
    def handle_results_selection(
        self,
        selection: FileResource,
    ):
        assert self.active is not None
        # Open relevant tab then select resource in the tree
        if os.path.commonpath([selection.filepath(), self.active.module_path()]) == str(self.active.module_path()):
            self.ui.resourceTabs.setCurrentIndex(1)
            self.select_resource(self.ui.modulesWidget, selection)
        elif os.path.commonpath([selection.filepath(), self.active.override_path()]) == str(self.active.override_path()):
            self.ui.resourceTabs.setCurrentIndex(2)
            self.select_resource(self.ui.overrideWidget, selection)
        elif is_bif_file(selection.filepath().name):
            self.select_resource(self.ui.coreWidget, selection)

    # endregion

    # region Events
    def closeEvent(self, e: QCloseEvent | None):  # pylint: disable=unused-argument
        instance: QCoreApplication | None = QCoreApplication.instance()
        print("<SDM> [closeEvent scope] instance: ", instance)

        if instance is None:
            print("QCoreApplication.instance() returned None for some reason... calling sys.exit() directly.")
            sys.exit()
        else:
            print("ToolWindow closed, shutting down the app.")
            instance.quit()

    def mouseMoveEvent(self, event: QMouseEvent):
        # print("mouseMoveEvent")
        if event.buttons() == Qt.MouseButton.LeftButton:
            # print("mouseMoveEvent (button passed)")
            # This code is responsible for allowing the window to be drag-moved from any point, not just the title bar.
            mouseMovePos = getattr(self, "_mouseMovePos", None)
            if mouseMovePos is None:
                # print("mouseMovePos is None (mouseMoveEvent)")
                return
            globalPos = event.globalPos()
            self.move(self.mapFromGlobal(self.mapToGlobal(self.pos()) + (globalPos - mouseMovePos)))
            self._mouse_move_pos = globalPos

    def mousePressEvent(self, event: QMouseEvent):
        # print("mousePressEvent")
        if event.button() == Qt.MouseButton.LeftButton:
            # print("mousePressEvent (button passed)")
            self._mouse_move_pos = event.globalPos()
            # print("<SDM> [mousePressEvent scope] self._mouseMovePos: ", self._mouseMovePos)

    def mouseReleaseEvent(self, event: QMouseEvent):
        # print("mouseReleaseEvent")
        if event.button() == Qt.MouseButton.LeftButton:
            # print("mouseReleaseEvent (button passed)")
            self._mouse_move_pos = None

    def keyPressEvent(self, event: QKeyEvent):
        super().keyPressEvent(event)

    def dragEnterEvent(self, e: QtGui.QDragEnterEvent | None):
        if e is None:
            return

        # print_qt_object(e)
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
                RobustLogger().exception("Could not process dragged-in item.")
                e.ignore()
                return
            else:
                if restype:
                    continue
                RobustLogger().info(f"Not processing dragged-in item '{filepath}'. Invalid resource")
        e.accept()

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
                RobustLogger().info(f"Not loading dropped file '{filepath}'. Invalid resource")
                continue
            open_resource_editor(filepath, resname, restype, data, self.active, self, gff_specialized=GlobalSettings().gff_specializedEditors)

    # endregion

    # region Menu Bar
    def update_menus(self):
        RobustLogger().debug("Updating menus...")
        version = "x" if self.active is None else "2" if self.active.tsl else "1"

        dialog_icon_path = f":/images/icons/k{version}/dialog.png"
        self.ui.actionNewDLG.setIcon(QIcon(QPixmap(dialog_icon_path)))  # type: ignore[arg-type]
        self.ui.actionNewDLG.setEnabled(self.active is not None)

        tlk_icon_path = f":/images/icons/k{version}/tlk.png"
        self.ui.actionNewTLK.setIcon(QIcon(QPixmap(tlk_icon_path)))  # type: ignore[arg-type]
        self.ui.actionNewTLK.setEnabled(True)

        script_icon_path = f":/images/icons/k{version}/script.png"
        self.ui.actionNewNSS.setIcon(QIcon(QPixmap(script_icon_path)))  # type: ignore[arg-type]
        self.ui.actionNewNSS.setEnabled(self.active is not None)

        creature_icon_path = f":/images/icons/k{version}/creature.png"
        self.ui.actionNewUTC.setIcon(QIcon(QPixmap(creature_icon_path)))  # type: ignore[arg-type]
        self.ui.actionNewUTC.setEnabled(self.active is not None)

        placeable_icon_path = f":/images/icons/k{version}/placeable.png"
        self.ui.actionNewUTP.setIcon(QIcon(QPixmap(placeable_icon_path)))  # type: ignore[arg-type]
        self.ui.actionNewUTP.setEnabled(self.active is not None)

        door_icon_path = f":/images/icons/k{version}/door.png"
        self.ui.actionNewUTD.setIcon(QIcon(QPixmap(door_icon_path)))  # type: ignore[arg-type]
        self.ui.actionNewUTD.setEnabled(self.active is not None)

        item_icon_path = f":/images/icons/k{version}/item.png"
        self.ui.actionNewUTI.setIcon(QIcon(QPixmap(item_icon_path)))  # type: ignore[arg-type]
        self.ui.actionNewUTI.setEnabled(self.active is not None)

        sound_icon_path = f":/images/icons/k{version}/sound.png"
        self.ui.actionNewUTS.setIcon(QIcon(QPixmap(sound_icon_path)))  # type: ignore[arg-type]
        self.ui.actionNewUTS.setEnabled(self.active is not None)

        trigger_icon_path = f":/images/icons/k{version}/trigger.png"
        self.ui.actionNewUTT.setIcon(QIcon(QPixmap(trigger_icon_path)))  # type: ignore[arg-type]
        self.ui.actionNewUTT.setEnabled(self.active is not None)

        merchant_icon_path = f":/images/icons/k{version}/merchant.png"
        self.ui.actionNewUTM.setIcon(QIcon(QPixmap(merchant_icon_path)))  # type: ignore[arg-type]
        self.ui.actionNewUTM.setEnabled(self.active is not None)

        waypoint_icon_path = f":/images/icons/k{version}/waypoint.png"
        self.ui.actionNewUTW.setIcon(QIcon(QPixmap(waypoint_icon_path)))  # type: ignore[arg-type]
        self.ui.actionNewUTW.setEnabled(self.active is not None)

        encounter_icon_path = f":/images/icons/k{version}/encounter.png"
        self.ui.actionNewUTE.setIcon(QIcon(QPixmap(encounter_icon_path)))  # type: ignore[arg-type]
        self.ui.actionNewUTE.setEnabled(self.active is not None)

        self.ui.actionEditTLK.setEnabled(self.active is not None)
        self.ui.actionEditJRL.setEnabled(self.active is not None)
        self.ui.actionFileSearch.setEnabled(self.active is not None)
        self.ui.actionModuleDesigner.setEnabled(self.active is not None)
        self.ui.actionIndoorMapBuilder.setEnabled(self.active is not None)

        self.ui.actionCloneModule.setEnabled(self.active is not None)

    def debounce_module_designer_load(self):
        """Prevents users from spamming the start button, which could easily result in a bad crash."""
        self.module_designer_load_processed = True

    def open_module_designer(self):
        if self.active is None:
            QMessageBox(QMessageBox.Icon.Information, "No installation loaded.", "Load an installation before opening the Module Designer.").exec_()
            return
        designer = ModuleDesigner(None, self.active)
        add_window(designer, show=False)

    def open_settings_dialog(self):
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
                self.reload_settings()

    @Slot()
    def open_active_talktable(self):
        """Opens the talktable for the active (currently selected) installation.

        If there is no active information, show a message box instead.
        """
        if self.active is None:
            QMessageBox(QMessageBox.Icon.Information, "No installation loaded.", "Load an installation before opening the TalkTable Editor.").exec_()
            return
        filepath: CaseAwarePath = self.active.path() / "dialog.tlk"
        print("<SDM> [openActiveTalktable scope] filepath: ", filepath)
        if not filepath.is_file():
            QMessageBox(
                QMessageBox.Icon.Information, "dialog.tlk not found", f"Could not open the TalkTable editor, dialog.tlk not found at the expected location<br><br>{filepath}."
            ).exec_()
            return
        data: bytes = BinaryReader.load_file(filepath)
        open_resource_editor(filepath, "dialog", ResourceType.TLK, data, self.active, self)

    @Slot()
    def open_active_journal(self):
        """Opens the journal for the active (currently selected) installation.

        If there is no active information, show a message box instead.
        """
        if self.active is None:
            QMessageBox(QMessageBox.Icon.Information, "No installation loaded.", "Load an installation before opening the Journal Editor.").exec_()
            return
        jrl_ident: ResourceIdentifier = ResourceIdentifier("global", ResourceType.JRL)
        journal_resources: dict[ResourceIdentifier, list[LocationResult]] = self.active.locations(
            [jrl_ident],
            [SearchLocation.OVERRIDE, SearchLocation.CHITIN],
        )
        print("<SDM> [openActiveJournal scope] journal_resources: ", journal_resources)

        if not journal_resources or not journal_resources.get(jrl_ident):
            QMessageBox(QMessageBox.Icon.Critical, "global.jrl not found", "Could not open the journal editor: 'global.jrl' not found.").exec_()
            return
        relevant: list[LocationResult] = journal_resources[jrl_ident]
        if len(relevant) > 1:
            dialog = FileSelectionWindow(relevant, self.active)
        else:
            jrl_resource: FileResource = relevant[0].as_file_resource()
            open_resource_editor(jrl_resource.filepath(), jrl_resource.resname(), jrl_resource.restype(), jrl_resource.data(), self.active, self)
        add_window(dialog)

    @Slot()
    def open_file_search_dialog(self):
        """Opens the FileSearcher dialog.

        If a search is conducted then a FileResults dialog displays the results
        where the user can then select a resource and the selected resouce will then be shown in the main window.
        """
        if self.active is None:
            print("No installation active, ergo nothing to search")
            return
        search_dialog = FileSearcher(self, self.installations)
        search_dialog.setModal(False)  # Make the dialog non-modal
        search_dialog.show()  # Show the dialog without blocking
        add_window(search_dialog, show=False)
        search_dialog.fileResults.connect(self.handle_search_completed)

    @Slot()
    def open_indoor_map_builder(self):
        IndoorMapBuilder(self, self.active).show()

    def open_instructions_window(self):
        """Opens the instructions window."""
        window = HelpWindow(None)
        print("<SDM> [openInstructionsWindow scope] window: ", window)

        window.setWindowIcon(self.windowIcon())
        add_window(window)
        window.activateWindow()

    def open_about_dialog(self):
        """Opens the about dialog."""
        About(self).exec_()

    # endregion

    # region updates

    # endregion

    # region Other

    def get_active_tab_index(self) -> int:
        return self.ui.resourceTabs.currentIndex()

    def get_active_resource_tab(self) -> QWidget:
        return self.ui.resourceTabs.currentWidget()

    def get_active_resource_widget(self) -> ResourceList | TextureList:
        current_widget: QWidget = self.get_active_resource_tab()
        print("<SDM> [getActiveResourceWidget scope] current_widget: ", current_widget)

        if current_widget is self.ui.coreTab:
            return self.ui.coreWidget
        if current_widget is self.ui.modulesTab:
            return self.ui.modulesWidget
        if current_widget is self.ui.overrideTab:
            return self.ui.overrideWidget
        if current_widget is self.ui.texturesTab:
            return self.ui.texturesWidget
        if current_widget is self.ui.savesTab:
            return self.ui.savesWidget
        raise ValueError(f"Unknown current widget: {current_widget}")

    def reload_settings(self):
        self.reload_installations()

    @Slot()
    def _open_module_tab_erf_editor(self):
        assert self.active is not None
        resourceWidget = self.get_active_resource_widget()
        assert isinstance(resourceWidget, ResourceList)
        filename = resourceWidget.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        print("<SDM> [openERFEditor scope] filename: ", filename)

        if not filename:
            return
        erf_filepath: CaseAwarePath = self.active.module_path() / filename
        print("<SDM> [openERFEditor scope] erf_filepath: ", erf_filepath)

        if not erf_filepath.is_file():
            RobustLogger().warning(f"Not loading '{erf_filepath}'. File does not exist")
            return
        res_ident: ResourceIdentifier = ResourceIdentifier.from_path(erf_filepath)
        print("<SDM> [openERFEditor scope] res_ident: ", res_ident)

        if not res_ident.restype:
            RobustLogger().warning(f"Not loading '{erf_filepath}'. Invalid resource")
            return
        _filepath, _editor = open_resource_editor(
            erf_filepath,
            res_ident.resname,
            res_ident.restype,
            BinaryReader.load_file(erf_filepath),
            self.active,
            self,
            gff_specialized=self.settings.gff_specializedEditors,
        )

    def on_tab_changed(self):
        current_widget: QWidget = self.get_active_resource_tab()
        if current_widget is self.ui.modulesTab:
            self.erf_editor_button.show()
        else:
            self.erf_editor_button.hide()

    def select_resource(self, tree: ResourceList, resource: FileResource):
        """This function seems to reload the resource after determining the ui widget containing it.

        Seems to only be used for the FileSearcher dialog.
        """
        print("<SDM> [selectResource scope] tree: ", tree)
        if tree == self.ui.coreWidget:
            self.ui.resourceTabs.setCurrentWidget(self.ui.coreTab)
            self.ui.coreWidget.set_resource_selection(resource)

        elif tree == self.ui.modulesWidget:
            self.ui.resourceTabs.setCurrentWidget(self.ui.modulesTab)
            filename = resource.filepath().name
            print("<SDM> [selectResource scope] filename: ", filename)

            self.change_module(filename)
            self.ui.modulesWidget.set_resource_selection(resource)

        elif tree == self.ui.overrideWidget:
            self._select_override_resource(resource)
        elif tree == self.ui.savesWidget:
            self.ui.resourceTabs.setCurrentWidget(self.ui.savesTab)
            filename = resource.filepath().name
            print("<SDM> [selectResource scope] filename: ", filename)

            self.on_save_reload(filename)

    def _select_override_resource(self, resource: FileResource):
        assert self.active is not None
        self.ui.resourceTabs.setCurrentWidget(self.ui.overrideTab)
        self.ui.overrideWidget.set_resource_selection(resource)
        subfolder: str = "."
        for folder_name in self.active.override_list():
            folder_path: CaseAwarePath = self.active.override_path() / folder_name
            print("<SDM> [_selectOverrideResource scope] folder_path: ", folder_path)

            if os.path.commonpath([resource.filepath(), folder_path]) == str(folder_path) and len(subfolder) < len(folder_path.name):
                subfolder = folder_name
                print("<SDM> [_selectOverrideResource scope] subfolder: ", subfolder)

        self.change_override_folder(subfolder)

    def reload_installations(self):
        """Refresh the list of installations available in the combobox."""
        self.ui.gameCombo.currentIndexChanged.disconnect(self.change_active_installation)
        self.ui.gameCombo.clear()  # without above disconnect, would call ToolWindow().changeActiveInstallation(-1)
        self.ui.gameCombo.addItem("[None]")  # without above disconnect, would call ToolWindow().changeActiveInstallation(0)

        for installation in self.settings.installations().values():
            self.ui.gameCombo.addItem(installation.name)
        self.ui.gameCombo.currentIndexChanged.connect(self.change_active_installation)

    @Slot()
    def unset_installation(self):
        """Unset the current installation."""
        self.ui.gameCombo.setCurrentIndex(0)

        self.ui.coreWidget.set_resources([])
        self.ui.modulesWidget.set_sections([])
        self.ui.modulesWidget.set_resources([])
        self.ui.overrideWidget.set_sections([])
        self.ui.overrideWidget.set_resources([])

        self.ui.resourceTabs.setEnabled(False)
        self.ui.sidebar.setEnabled(False)
        self.update_menus()
        self.active = None
        # if self.dogObserver is not None:
        #    self.dogObserver.stop()
        #    self.dogObserver = None

    # endregion

    # region ResourceList handlers

    def refresh_core_list(self, *, reload: bool = True):
        """Rebuilds the tree in the Core tab. Used with the flatten/unflatten logic."""
        if self.active is None:
            print("no installation is currently loaded, cannot refresh core list")
            return
        RobustLogger().info("Loading core installation resources into UI...")
        try:
            self.ui.coreWidget.set_resources(self.active.core_resources())
        except Exception:  # noqa: BLE001
            RobustLogger().exception("Failed to setResources of the core list")
        RobustLogger().debug("Remove unused Core tab categories...")
        try:
            self.ui.coreWidget.modules_model.remove_unused_categories()
        except Exception:  # noqa: BLE001
            RobustLogger().exception("Failed to remove unused categories in the core list")

    def change_module(self, module_name: str):
        # Some users may choose to merge their RIM files under one option in the Modules tab; if this is the case we
        # need to account for this.
        if self.settings.joinRIMsTogether:
            if module_name.casefold().endswith("_s.rim"):
                module_name = f"{module_name[:-6]}.rim"
                print("<SDM> [changeModule scope] moduleName: ", module_name)

            if module_name.casefold().endswith("_dlg.erf"):
                module_name = f"{module_name[:-8]}.rim"
                print("<SDM> [changeModule scope] moduleName: ", module_name)

        self.ui.modulesWidget.change_section(module_name)

    def refresh_module_list(
        self,
        *,
        reload: bool = True,
        module_items: list[QStandardItem] | None = None,
    ):
        """Refreshes the list of modules in the modulesCombo combobox."""
        module_items = [] if module_items is None else module_items
        action: Literal["Reload", "Refresh"] = "Reload" if reload else "Refresh"
        if not module_items:
            try:
                module_items = self._get_modules_list(reload=reload)
            except Exception:  # noqa: BLE001
                RobustLogger().exception(f"Failed to get the list of {action}ed modules!")
            else:
                print("<SDM> [task scope] moduleItems: ", module_items)

        try:
            self.ui.modulesWidget.set_sections(module_items)
        except Exception:  # noqa: BLE001
            RobustLogger().exception(f"Failed to call setSections on the {action}ed modulesWidget!")

    def _get_modules_list(self, *, reload: bool = True) -> list[QStandardItem]:  # noqa: C901
        """Refreshes the list of modules in the modulesCombo combobox."""
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
            try:
                self.active.load_modules()
            except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
                RobustLogger().exception("Failed to reload the list of modules (load_modules function)")

        try:
            area_names: dict[str, str] = self.active.module_names()
        except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            RobustLogger().exception("Failed to get the list of area names from the modules!")
            area_names = {k: (str(v[0].filepath()) if v else "unknown filepath") for k, v in self.active._modules.items()}
        print("<SDM> [_getModulesList scope] areaNames: ", area_names)

        def sort_algo(module_file_name: str) -> str:
            """Sorts the modules in the modulesCombo combobox."""
            lower_module_file_name: str = module_file_name.lower()
            sort_str: str = ""
            with suppress(Exception):
                if "stunt" in lower_module_file_name:  # keep the stunt modules at the bottom.
                    sort_str = "zzzzz"
                elif self.settings.moduleSortOption == 0:  # "Sort by filename":
                    sort_str = ""
                elif self.settings.moduleSortOption == 1:  # "Sort by humanized area name":
                    sort_str = area_names.get(module_file_name, "y").lower()
                else:  # alternate mod id that attempts to match to filename.
                    sort_str = self.active.module_id(module_file_name, use_alternate=True)
            sort_str += f"_{lower_module_file_name}".lower()
            return sort_str

        try:
            sorted_keys: list[str] = sorted(area_names, key=sort_algo)
        except Exception:  # noqa: BLE001
            RobustLogger().exception("Failed to sort the list of modules")
            sorted_keys = list(area_names.keys())

        modules: list[QStandardItem] = []
        for module_name in sorted_keys:
            try:
                # Some users may choose to have their RIM files for the same module merged into a single option for the
                # dropdown menu.
                lower_module_name = module_name.lower()
                # FIXME(th3w1zard1): Looks like I broke the joinRIMsTogether setting at some point.
                # Uncommenting this prevents their resources from showing up in the toolset at all.
                # if self.settings.joinRIMsTogether:
                #    if lower_module_name.endswith("_s.rim"):
                #        continue
                #    if self.active.game().is_k2() and lower_module_name.endswith("_dlg.erf"):
                #        continue

                area_text: str = area_names.get(module_name, "<module is missing area data!>")
                item = QStandardItem(f"{area_text} [{module_name}]")
                item.setData(f"{area_text}\n{module_name}", Qt.ItemDataRole.DisplayRole)
                item.setData(module_name, Qt.ItemDataRole.UserRole)  # Set area name
                item.setData(module_name, Qt.ItemDataRole.UserRole + 11)  # Set module name

                # Some users may choose to have items representing RIM files to have grey text.
                if self.settings.greyRIMText and lower_module_name.endswith(("_dlg.erf", ".rim")):
                    item.setForeground(self.palette().shadow())

                modules.append(item)
            except Exception:  # noqa: PERF203, BLE001
                RobustLogger().exception(f"Unexpected exception thrown while parsing module '{module_name}', skipping...")
        if self.settings.profileToolset and profiler:
            profiler.disable()
            profiler.dump_stats(str(Path("main_getModulesList.pstat").absolute()))
        return modules

    def change_override_folder(self, subfolder: str):
        self.ui.overrideWidget.change_section(subfolder)

    def _get_override_list(self, *, reload: bool = True) -> list[QStandardItem]:
        if self.active is None:
            print("No installation is currently loaded, cannot refresh override list")
            return []
        if reload:
            try:
                self.active.load_override()
            except Exception:  # noqa: BLE001
                RobustLogger().exception("Failed to call load_override in getOverrideList")

        sections: list[QStandardItem] = []
        for directory in self.active.override_list():
            section = QStandardItem(str(directory if directory.strip() else "[Root]"))
            section.setData(directory, QtCore.Qt.ItemDataRole.UserRole)
            sections.append(section)
        return sections

    def refresh_override_list(
        self,
        *,
        reload: bool = True,
        override_items: list[QStandardItem] | None = None,
    ):
        """Refreshes the list of override directories in the overrideFolderCombo combobox."""
        override_items = self._get_override_list(reload=reload)
        self.ui.overrideWidget.set_sections(override_items)

    def _get_texture_pack_list(self, *, reload: bool = True) -> list[QStandardItem] | None:
        if self.active is None:
            print("No installation is currently loaded, cannot refresh texturepack list")
            return None
        if reload:
            self.active.load_textures()

        texture_pack_list: list[QStandardItem] = []
        for texturepack in self.active.texturepacks_list():
            section = QStandardItem(str(texturepack))
            print("<SDM> [_getTexturePackList scope] section: ", section)

            section.setData(texturepack, QtCore.Qt.ItemDataRole.UserRole)
            texture_pack_list.append(section)
        return texture_pack_list

    def refresh_texture_pack_list(self, *, reload: bool = True):
        """Refreshes the list of texture packs in the texturePackCombo combobox."""
        texture_pack_list: list[QStandardItem] | None = self._get_texture_pack_list(reload=reload)
        print("<SDM> [refreshTexturePackList scope] texture_pack_list: ", texture_pack_list)

        if texture_pack_list is None:
            RobustLogger().error("texture_pack_list was somehow None in refreshTexturePackList(reload=%s)", reload, stack_info=True)
            print("<SDM> [refreshTexturePackList scope] reload: ", reload)

            return
        self.ui.texturesWidget.set_sections(texture_pack_list)

    def refresh_saves_list(self, *, reload: bool = True):
        """Refreshes the list of override directories in the overrideFolderCombo combobox."""
        RobustLogger().info("Loading saves list into UI...")
        if self.active is None:
            print("No installation is currently loaded, cannot refresh saves list")
            return
        try:
            if reload:
                self.active.load_saves()

            saves_list: list[QStandardItem] = []
            for save_path in self.active.saves:
                save_path_str = str(save_path)
                print("<SDM> [refresh_saves_list scope] save_path_str: ", save_path_str)

                section = QStandardItem(save_path_str)
                print("<SDM> [refresh_saves_list scope] section: ", section)

                section.setData(save_path_str, QtCore.Qt.ItemDataRole.UserRole)
                saves_list.append(section)
            self.ui.savesWidget.set_sections(saves_list)
        except Exception:  # noqa: BLE001
            RobustLogger().exception("Failed to load/refresh the saves list")

    # endregion

    # region Extract
    def get_multiple_directories(self, title: str = "Choose some folders.") -> list[Path]:
        """Get multiple directories from the user."""
        dialog = QFileDialog(self)
        print("<SDM> [get_multiple_directories scope] dialog: ", dialog)

        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        dialog.setWindowTitle(title)

        list_view: QListView = dialog.findChild(QListView, "listView")
        print("<SDM> [get_multiple_directories scope] list_view: ", list_view)
        if isinstance(list_view, QListView):
            list_view.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        tree_view: QTreeView = dialog.findChild(QTreeView)
        print("<SDM> [get_multiple_directories scope] tree_view: ", tree_view)
        if isinstance(tree_view, QTreeView):
            tree_view.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)

        if dialog.exec_() == QFileDialog.DialogCode.Accepted:
            selected_dirs: list[str] = dialog.selectedFiles()
            print("<SDM> [get_multiple_directories scope] selected_dirs: ", selected_dirs)

            return [Path(dir_path) for dir_path in selected_dirs]
        return []

    @Slot()
    def extract_module_room_textures(self):
        """Extract all textures from the currently selected module."""
        assert self.active is not None
        from pykotor.common.module import Module
        from pykotor.tools.model import iterate_lightmaps, iterate_textures

        cur_module_name: str = self.ui.modulesWidget.ui.sectionCombo.currentData(QtCore.Qt.ItemDataRole.UserRole)
        print("<SDM> [extractModuleRoomTextures scope] str: ", str)

        if cur_module_name not in self.active._modules:  # noqa: SLF001
            RobustLogger().warning(f"'{cur_module_name}' not a valid module.")
            BetterMessageBox("Invalid module.", f"'{cur_module_name}' not a valid module, could not find it in the loaded installation.").exec_()
            return
        this_module = Module(cur_module_name, self.active, use_dot_mod=is_mod_file(cur_module_name))
        print("<SDM> [extractModuleRoomTextures scope] thisModule: ", this_module)

        lyt_module_resource: ModuleResource[LYT] | None = this_module.layout()
        print("<SDM> [extractModuleRoomTextures scope] lytModuleResource: ", lyt_module_resource)

        if lyt_module_resource is None:
            BetterMessageBox(f"'{cur_module_name}' has no LYT!", f"The module '{cur_module_name}' does not store any LYT resource.").exec_()
            return
        lyt: LYT | None = lyt_module_resource.resource()
        print("<SDM> [extractModuleRoomTextures scope] lyt: ", lyt)

        if lyt is None:
            BetterMessageBox(
                f"'{cur_module_name}' has no LYT paths!",
                "The module did not contain any locations for the LYT. This is an internal error, as there should be one if we know it exists. Please report.",
            ).exec_()
            return
        optional_paths: list[Path] = []
        print("<SDM> [extractModuleRoomTextures scope] optionalPaths: ", optional_paths)

        # customFolderPath = self.get_multiple_directories("Choose optional folders to search for models")
        # if customFolderPath and customFolderPath.strip():
        #    optionalPaths.append(Path(customFolderPath))
        model_queries: list[ResourceIdentifier] = [ResourceIdentifier(mdl_name, ResourceType.MDL) for mdl_name in (lyt.all_room_models())]
        print("<SDM> [extractModuleRoomTextures scope] modelQueries: ", model_queries)

        model_location_results: dict[ResourceIdentifier, list[LocationResult]] = self.active.locations(model_queries, folders=optional_paths)
        print("<SDM> [extractModuleRoomTextures scope] modelLocationResults: ", model_location_results)

        model_locations: dict[ResourceIdentifier, FileResource] = {k: v[0].as_file_resource() for k, v in model_location_results.items() if v}
        print("<SDM> [extractModuleRoomTextures scope] modelLocations: ", model_locations)

        texture_lightmap_names: list[str] = []
        for res in model_locations.values():
            texture_names: list[str] = []
            try:
                texture_names.extend(iter(iterate_textures(res.data())))
            except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
                RobustLogger().exception(f"Failed to extract textures names from {res.identifier()}")
            lightmap_names: list[str] = []
            try:
                lightmap_names.extend(iter(iterate_lightmaps(res.data())))
            except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
                RobustLogger().exception(f"Failed to extract lightmap names from {res.identifier()}")
            texture_lightmap_names.extend(texture_names)
            texture_lightmap_names.extend(lightmap_names)
        texture_data: CaseInsensitiveDict[TPC | None] = self.active.textures(texture_lightmap_names)
        for tex, data in texture_data.copy().items():
            if data is None:
                del texture_data[tex]
        texture_resource_results: list[ResourceResult] = [
            ResourceResult(
                tex,
                ResourceType.TPC,
                Path().joinpath(tex).with_suffix(".tpc"),
                bytes_tpc(data),
            )
            for tex, data in texture_data.items()
            if data is not None
        ]

        FileSaveHandler(texture_resource_results, self).save_files()

    @Slot()
    def extract_module_room_models(self):
        """Extract all models from the currently selected module."""
        assert self.active is not None
        from pykotor.common.module import Module

        cur_module_name: str = self.ui.modulesWidget.ui.sectionCombo.currentData(QtCore.Qt.ItemDataRole.UserRole)
        if cur_module_name not in self.active._modules:
            RobustLogger().warning(f"'{cur_module_name}' not a valid module.")
            BetterMessageBox("Invalid module.", f"'{cur_module_name}' not a valid module, could not find it in the loaded installation.").exec_()
            return
        this_module = Module(cur_module_name, self.active, use_dot_mod=is_mod_file(cur_module_name))
        print("<SDM> [extractModuleRoomModels scope] thisModule: ", this_module)

        lyt_module_resource: ModuleResource[LYT] | None = this_module.layout()
        print("<SDM> [extractModuleRoomModels scope] lytModuleResource: ", lyt_module_resource)

        if lyt_module_resource is None:
            BetterMessageBox(f"'{cur_module_name}' has no LYT!", f"The module '{cur_module_name}' does not store any LYT resource.").exec_()
            return
        lyt = lyt_module_resource.resource()
        print("<SDM> [extractModuleRoomModels scope] lyt: ", lyt)

        if lyt is None:
            BetterMessageBox(
                f"'{cur_module_name}' has no LYT paths!",
                "The module did not contain any locations for the LYT. This is an internal error, as there should be one if we know it exists. Please report.",
            ).exec_()
            return
        optional_paths: list[Path] = []
        print("<SDM> [extractModuleRoomModels scope] optional_paths: ", optional_paths)

        # custom_folder_path = self.get_multiple_directories("Choose optional folders to search for models")
        # print("<SDM> [extractModuleRoomModels scope] customFolderPath: ", custom_folder_path)

        # if customFolderPath and customFolderPath.strip():
        #    optionalPaths.append(Path(customFolderPath))
        model_queries: list[ResourceIdentifier] = [ResourceIdentifier(mdl_name, ResourceType.MDL) for mdl_name in (lyt.all_room_models())]
        print("<SDM> [extractModuleRoomModels scope] model_queries: ", model_queries)

        model_location_results: dict[ResourceIdentifier, list[LocationResult]] = self.active.locations(model_queries, folders=optional_paths)
        print("<SDM> [extractModuleRoomModels scope] model_location_results: ", model_location_results)

        model_locations: dict[ResourceIdentifier, FileResource] = {k: v[0].as_file_resource() for k, v in model_location_results.items() if v}
        print("<SDM> [extractModuleRoomModels scope] model_locations: ", model_locations)

        FileSaveHandler(list(model_locations.values()), self).save_files()

    @Slot()
    def extract_all_module_textures(self):
        """Extract all textures from the currently selected module."""
        if self.active is None:
            RobustLogger().warning("No installation is currently loaded, cannot extract all module textures")
            return
        from pykotor.common.module import Module

        cur_module_name: str = self.ui.modulesWidget.ui.sectionCombo.currentData(QtCore.Qt.ItemDataRole.UserRole)
        print("<SDM> [extractAllModuleTextures scope] cur_module_name: ", cur_module_name)

        if cur_module_name not in self.active._modules:  # noqa: SLF001  # pylint: disable=protected-access
            RobustLogger().warning(f"'{cur_module_name}' not a valid module.")
            return
        this_module = Module(cur_module_name, self.active, use_dot_mod=is_mod_file(cur_module_name))
        print("<SDM> [extractAllModuleTextures scope] this_module: ", this_module)

        textures_list: list[ResourceResult] = []
        for ident, mod_res in this_module.resources.items():
            if ident.restype not in (ResourceType.TGA, ResourceType.TPC):
                continue
            data: bytes | None = mod_res.data()
            if data is None:
                continue
            locations: list[Path] = mod_res.locations()
            print("<SDM> [extractAllModuleTextures scope] locations: ", locations)

            if not locations:
                continue
            textures_list.append(ResourceResult(ident.resname, ident.restype, locations[0], data))
        FileSaveHandler(textures_list, self).save_files()

    @Slot()
    def extract_all_module_models(self):
        """Extract all models from the currently selected module."""
        if self.active is None:
            RobustLogger().warning("No installation is currently loaded, cannot extract all module models")
            return
        from pykotor.common.module import Module

        cur_module_name: str = self.ui.modulesWidget.ui.sectionCombo.currentData(QtCore.Qt.ItemDataRole.UserRole)
        if cur_module_name not in self.active._modules:  # noqa: SLF001  # pylint: disable=protected-access
            RobustLogger().warning(f"'{cur_module_name}' not a valid module.")
            return
        this_module: Module = Module(cur_module_name, self.active, use_dot_mod=is_mod_file(cur_module_name))
        print("<SDM> [extractAllModuleModels scope] this_module: ", this_module)

        models_list: list[ResourceResult] = []
        for ident, mod_res in this_module.resources.items():
            if ident.restype not in (ResourceType.MDX, ResourceType.MDL):
                continue
            data: bytes | None = mod_res.data()
            if data is None:
                continue
            locations: list[Path] = mod_res.locations()
            print("<SDM> [extractAllModuleModels scope] locations: ", locations)

            if not locations:
                continue
            models_list.append(ResourceResult(ident.resname, ident.restype, locations[0], data))
        FileSaveHandler(models_list, self).save_files()

    @Slot()
    def extract_module_everything(self):
        from pykotor.common.module import Module

        cur_module_name: str = self.ui.modulesWidget.ui.sectionCombo.currentData(QtCore.Qt.ItemDataRole.UserRole)
        print("<SDM> [extractModuleEverything scope] cur_module_name: ", cur_module_name)

        if cur_module_name not in self.active._modules:
            RobustLogger().warning(f"'{cur_module_name}' is not a valid module.")
            return
        this_module: Module = Module(cur_module_name, self.active, use_dot_mod=is_mod_file(cur_module_name))
        print("<SDM> [extractModuleEverything scope] this_module: ", this_module)

        all_module_resources: list[ResourceResult] = []
        for ident, mod_res in this_module.resources.items():
            data: bytes | None = mod_res.data()
            if data is None:
                continue
            locations: list[Path] = mod_res.locations()
            print("<SDM> [extractModuleEverything scope] locations: ", locations)

            if not locations:
                continue
            all_module_resources.append(ResourceResult(ident.resname, ident.restype, locations[0], data))
        FileSaveHandler(all_module_resources, self).save_files()

    def build_extract_save_paths(self, resources: list[FileResource]) -> tuple[Path, dict[FileResource, Path]] | tuple[None, None]:
        # TODO(th3w1zard1): currently doesn't handle same filenames existing for extra extracts e.g. tpcTxiCheckbox.isChecked() or mdlTexturesCheckbox.isChecked()
        paths_to_write: dict[FileResource, Path] = {}

        folder_path_str: str = QFileDialog.getExistingDirectory(self, "Extract to folder")
        print("<SDM> [build_extract_save_paths scope] folder_path_str: ", folder_path_str)

        if not folder_path_str or not folder_path_str.strip():
            RobustLogger().debug("User cancelled folderpath extraction.")
            return None, None

        folder_path = Path(folder_path_str)
        print("<SDM> [build_extract_save_paths scope] folder_path: ", folder_path)

        for resource in resources:
            identifier: ResourceIdentifier = resource.identifier()
            print("<SDM> [build_extract_save_paths scope] identifier: ", identifier)

            save_path: Path = folder_path / str(identifier)
            print("<SDM> [build_extract_save_paths scope] save_path: ", save_path)

            # Determine the final save path based on UI checks
            if resource.restype() is ResourceType.TPC and self.ui.tpcDecompileCheckbox.isChecked():
                save_path = save_path.with_suffix(".tga")
                print("<SDM> [build_extract_save_paths scope] save_path: ", save_path)

            elif resource.restype() is ResourceType.MDL and self.ui.mdlDecompileCheckbox.isChecked():
                save_path = save_path.with_suffix(".mdl.ascii")
                print("<SDM> [build_extract_save_paths scope] save_path: ", save_path)

            paths_to_write[resource] = save_path
            print("<SDM> [build_extract_save_paths scope] paths_to_write[resource]: ", paths_to_write[resource])

        return folder_path, paths_to_write

    @Slot(list, object)
    def on_extract_resources(
        self,
        selected_resources: list[FileResource],
        resource_widget: ResourceList | TextureList | None = None,
    ):
        """Extracts the resources selected in the main UI window.

        Args:
        ----
            selected_resources: list[FileResource]: List of selected resources to extract
            resource_widget: ResourceList | TextureList | None: The widget that contains the selected resources

        Processing Logic:
        ----------------
            - If single resource selected, prompt user to save with default or custom name
            - If multiple resources selected, prompt user for extract directory and extract each with original name.
        """
        if selected_resources:
            folder_path, paths_to_write = self.build_extract_save_paths(selected_resources)
            print("<SDM> [onExtractResources scope] paths_to_write: ", paths_to_write)

            if folder_path is None or paths_to_write is None:
                RobustLogger().debug("No paths to write: user must have cancelled the getExistingDirectory dialog.")
                return
            failed_savepath_handlers: dict[Path, Exception] = {}
            resource_save_paths: dict[FileResource, Path] = FileSaveHandler(selected_resources).determine_save_paths(paths_to_write, failed_savepath_handlers)
            print("<SDM> [onExtractResources scope] resource_save_paths: ", resource_save_paths)

            if not resource_save_paths:
                RobustLogger().debug("No resources returned from FileSaveHandler.determine_save_paths")
                return
            loader = AsyncLoader.__new__(AsyncLoader)
            seen_resources: dict[LocationResult, Path] = {}
            tasks = [lambda res=resource, fp=save_path: self._extract_resource(res, fp, loader, seen_resources) for resource, save_path in resource_save_paths.items()]
            loader.__init__(  # pylint: disable=unnecessary-dunder-call
                self,
                "Extracting Resources",
                tasks,
                "Failed to Extract Resources",
            )
            if is_debug_mode():
                print("<SDM> [onExtractResources scope] loader: ", loader)

                loader.errors.extend(failed_savepath_handlers.values())

                loader.exec_()
            else:
                for resource, save_path in resource_save_paths.items():
                    self._extract_resource(resource, save_path, loader, seen_resources)

            # quick main thread/ui check.
            if QThread.currentThread() != cast(QApplication, QApplication.instance()).thread():
                RobustLogger().warning("on_extract_resources called from wrong thread.")
                return
            if loader.errors:
                msg_box = QMessageBox(
                    QMessageBox.Icon.Information,
                    "Failed to extract some items.",
                    f"Failed to save {len(loader.errors)} files!",
                    flags=Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowStaysOnTopHint,
                )

                msg_box.setDetailedText("\n".join(f"{e.__class__.__name__}: {e}" for e in loader.errors))
                msg_box.exec_()
            else:
                msg_box = QMessageBox(
                    QMessageBox.Icon.Information,
                    "Extraction successful.",
                    f"Successfully saved {len(paths_to_write)} files to {folder_path}",
                    flags=Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowStaysOnTopHint,
                )

                msg_box.setDetailedText("\n".join(str(p) for p in resource_save_paths.values()))
                msg_box.exec_()
        elif isinstance(resource_widget, ResourceList) and is_capsule_file(resource_widget.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)):
            module_name = resource_widget.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
            print("<SDM> [onExtractResources scope] module_name: ", module_name)

            self._save_capsule_from_tool_ui(module_name)

    def _extract_resource(
        self,
        resource: FileResource,
        save_path: Path,
        loader: AsyncLoader,
        seen_resources: dict[LocationResult, Path],
    ):
        """Extracts a resource file from a FileResource object.

        Args:
        ----
            resource (FileResource): The FileResource object
            save_path (os.PathLike | str): Path to save the extracted file
            loader (AsyncLoader): Loader for async operations
            seen_resources (dict[LocationResult, Path]): Dictionary to store already seen resources

        Processing Logic:
        ----------------
            - Extracts Txi data from TPC files
            - Decompiles TPC and MDL files
            - Extracts textures from MDL files
            - Writes extracted data to the file path
        """
        loader._worker.progress.emit(  # noqa: SLF001  # pylint: disable=protected-access
            f"Processing resource: {resource.identifier()}",
            "update_maintask_text",
        )
        r_folderpath: Path = save_path.parent
        print("<SDM> [_extractResource scope] parent savepath: ", r_folderpath)

        data: bytes = resource.data()
        print("<SDM> [_extractResource scope] data: ", data)

        if resource.restype() is ResourceType.MDX and self.ui.mdlDecompileCheckbox.isChecked():
            RobustLogger().info(f"Not extracting MDX file '{resource.identifier()}', decompiling MDLs is checked.")
            return

        if resource.restype() is ResourceType.TPC:
            tpc: TPC = read_tpc(data, txi_source=save_path)

            try:
                if self.ui.tpcTxiCheckbox.isChecked():
                    RobustLogger().info(f"Extracting TXI from '{resource.identifier()}' because of settings.")
                    self._extract_txi(tpc, save_path.with_suffix(".txi"))
            except Exception as e:  # noqa: BLE001  # pylint: disable=broad-exception-caught
                loader.errors.append(e)

            try:
                if self.ui.tpcDecompileCheckbox.isChecked():
                    RobustLogger().info(f"Converting '{resource.identifier()}' to TGA because of settings.")
                    data = self._decompile_tpc(tpc)
                    # save_path = save_path.with_suffix(".tga")  # already handled
            except Exception as e:  # noqa: BLE001  # pylint: disable=broad-exception-caught
                loader.errors.append(e)

        if resource.restype() is ResourceType.MDL:
            if self.ui.mdlTexturesCheckbox.isChecked():
                RobustLogger().info(f"Extracting MDL Textures because of settings: {resource.identifier()}")
                self._extract_mdl_textures(resource, r_folderpath, loader, data, seen_resources)

            if self.ui.mdlDecompileCheckbox.isChecked():
                RobustLogger().info(f"Converting '{resource.identifier()}' to ASCII MDL because of settings")
                data = self._decompile_mdl(resource, data)
                # save_path = save_path.with_suffix(".mdl.ascii")  # already handled

        with save_path.open("wb") as file:
            RobustLogger().info(f"Saving extracted data of '{resource.identifier()}' to '{save_path}'")
            file.write(data)

    def _extract_txi(self, tpc: TPC, filepath: Path):
        if not tpc.txi or not tpc.txi.strip():
            return
        with filepath.open("wb") as file:
            file.write(tpc.txi.encode("ascii", errors="ignore"))

    def _decompile_tpc(self, tpc: TPC) -> bytearray:
        if tpc is None:
            raise ValueError("tpc was None in _decompile_tpc")
        data = bytearray()
        write_tpc(tpc, data, ResourceType.TGA)
        return data

    def _decompile_mdl(self, resource: FileResource, data: SOURCE_TYPES) -> bytearray:
        assert self.active is not None
        mdx_resource_lookup: ResourceResult | None = self.active.resource(resource.resname(), ResourceType.MDX)
        if mdx_resource_lookup is None:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), repr(resource))
        mdxData: bytes = mdx_resource_lookup.data
        mdl: MDL | None = read_mdl(data, 0, 0, mdxData, 0, 0)
        data = bytearray()
        write_mdl(mdl, data, ResourceType.MDL_ASCII)
        return data

    def _extract_mdl_textures(
        self,
        resource: FileResource,
        folderpath: Path,
        loader: AsyncLoader,
        data: bytes,
        seen_resources: dict[LocationResult | Literal["all_locresults"], Path | Any],
    ):
        assert self.active is not None, "self.active is None in _extract_mdl_textures"
        textures_and_lightmaps = set(iterate_textures(data)) | set(iterate_lightmaps(data))
        main_subfolder = folderpath / f"model_{resource.resname()}"

        all_locresults: dict[str, defaultdict[ResourceIdentifier, list[LocationResult]]] = seen_resources.setdefault(
            "all_locresults",
            defaultdict(lambda: defaultdict(list)),
        )

        for item in textures_and_lightmaps:
            tex_type = "texture" if item in interate_textures(data) else "lightmap"
            location_results = all_locresults.get(item) or self._locate_texture(item)
            all_locresults[item] = location_results

            if not self._process_texture(item, tex_type, location_results, resource, main_subfolder, seen_resources, loader):
                loader.errors.append(ValueError(f"Missing {tex_type} '{item}' for model '{resource.identifier()}'"))

    def _locate_texture(self, texture: str) -> dict[ResourceIdentifier, list[LocationResult]]:
        assert self.active is not None, "self.active is None in _locate_texture"
        return self.active.locations(
            [ResourceIdentifier(resname=texture, restype=rt) for rt in (ResourceType.TPC, ResourceType.TGA)],
            [
                SearchLocation.OVERRIDE,
                SearchLocation.TEXTURES_GUI,
                SearchLocation.TEXTURES_TPA,
                SearchLocation.CHITIN,
            ],
        )

    def _process_texture(
        self,
        texture: str,
        tex_type: str,
        location_results: dict[ResourceIdentifier, list[LocationResult]],
        resource: FileResource,
        main_subfolder: Path,
        seen_resources: dict[LocationResult | Literal["all_locresults"], Path | Any],
        loader: AsyncLoader,
    ) -> bool:
        for resident, loclist in location_results.items():
            for location in loclist:
                subfolder = main_subfolder / location.filepath.stem
                if location in seen_resources:
                    self._copy_existing_texture(seen_resources[location], subfolder)
                    continue

                try:
                    self._save_texture(location, resident, subfolder, seen_resources)
                except Exception as e:  # noqa: BLE001  # pylint: disable=broad-exception-caught
                    RobustLogger().exception(f"Failed to save {tex_type} '{resident}' ({texture}) for model '{resource.identifier()}'")
                    loader.errors.append(
                        ValueError(f"Failed to save {tex_type} '{resident}' ({texture}) for model '{resource.identifier()}':<br>    {e.__class__.__name__}: {e}")
                    )

        return bool(location_results)

    def _copy_existing_texture(
        self,
        previous_save_path: Path,
        subfolder: Path,
    ):
        subfolder.mkdir(parents=True, exist_ok=True)
        shutil.copy(str(previous_save_path), str(subfolder))
        if self.ui.tpcTxiCheckbox.isChecked():
            txi_path = previous_save_path.with_suffix(".txi")
            if txi_path.exists() and txi_path.is_file():
                shutil.copy(str(txi_path), str(subfolder))

    def _save_texture(
        self,
        location: LocationResult,
        resident: ResourceIdentifier,
        subfolder: Path,
        seen_resources: dict,
    ):
        file_format = ResourceType.TGA if self.ui.tpcDecompileCheckbox.isChecked() else ResourceType.TPC
        savepath = subfolder / f"{resident.resname}.{file_format.extension}"
        seen_resources[location] = savepath

        if self.ui.tpcTxiCheckbox.isChecked() or (resident.restype is ResourceType.TPC and self.ui.tpcDecompileCheckbox.isChecked()):
            tpc = read_tpc(location.filepath, location.offset, location.size)
            subfolder.mkdir(parents=True, exist_ok=True)
            if self.ui.tpcTxiCheckbox.isChecked():
                self._extract_txi(tpc, savepath.with_suffix(".txi"))
            write_tpc(tpc, savepath, file_format)
        else:
            with location.filepath.open("rb") as r_stream, savepath.open("wb") as w_stream:
                r_stream.seek(location.offset)
                savepath.parent.mkdir(parents=True, exist_ok=True)
                w_stream.write(r_stream.read(location.size))

    def open_from_file(self):
        filepaths: list[str] = QFileDialog.getOpenFileNames(self, "Select files to open")[:-1][0]

        for filepath in filepaths:
            r_filepath = Path(filepath)
            print("<SDM> [open_from_file scope] r_filepath: ", r_filepath)

            try:
                with r_filepath.open("rb") as file:
                    data: bytes = file.read()
                open_resource_editor(
                    filepath,
                    *ResourceIdentifier.from_path(r_filepath).validate().unpack(),
                    data,
                    self.active,
                    self,
                )
            except (ValueError, OSError) as e:
                etype, msg = universal_simplify_exception(e)
                print("<SDM> [open_from_file scope] msg: ", msg)

                QMessageBox(
                    QMessageBox.Icon.Critical,
                    f"Failed to open file ({etype})",
                    msg,
                ).exec_()

    # endregion
