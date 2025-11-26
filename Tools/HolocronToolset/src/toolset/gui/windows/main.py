from __future__ import annotations

import errno
import os
import shutil
import sys

from collections import defaultdict
from contextlib import suppress
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Any, cast

import qtpy

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy import QtCore
from qtpy.QtCore import (
    QAbstractItemModel,
    QCoreApplication,
    QModelIndex,
    QSortFilterProxyModel,
    QThread,
    QTimer,
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
    Slot,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QIcon, QPixmap, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import (
    QAction,  # pyright: ignore[reportPrivateImportUsage]
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from pykotor.extract.file import FileResource, ResourceIdentifier, ResourceResult
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.erf.erf_auto import read_erf, write_erf
from pykotor.resource.formats.erf.erf_data import ERF, ERFType
from pykotor.resource.formats.mdl import read_mdl, write_mdl
from pykotor.resource.formats.rim.rim_auto import read_rim, write_rim
from pykotor.resource.formats.rim.rim_data import RIM
from pykotor.resource.formats.tpc import read_tpc, write_tpc
from pykotor.resource.type import ResourceType
from pykotor.tools import module
from pykotor.tools.misc import is_any_erf_type_file, is_bif_file, is_capsule_file, is_erf_file, is_mod_file, is_rim_file
from pykotor.tools.model import iterate_lightmaps, iterate_textures
from pykotor.tools.path import CaseAwarePath
from toolset.config import get_remote_toolset_update_info
from toolset.data.installation import HTInstallation
from toolset.gui.common.localization import (
    ToolsetLanguage,
    set_language,
    translate as tr,
    trf,
)
from toolset.gui.common.style.theme_manager import ThemeManager
from toolset.gui.dialogs.about import About
from toolset.gui.dialogs.asyncloader import AsyncLoader
from toolset.gui.dialogs.clone_module import CloneModuleDialog
from toolset.gui.dialogs.load_from_location_result import FileSelectionWindow
from toolset.gui.dialogs.save.generic_file_saver import FileSaveHandler
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
from toolset.gui.widgets.main_widgets import ResourceList, ResourceModel, ResourceStandardItem
from toolset.gui.widgets.settings.widgets.misc import GlobalSettings
from toolset.gui.windows.help import HelpWindow
from toolset.gui.windows.indoor_builder import IndoorMapBuilder
from toolset.gui.windows.module_designer import ModuleDesigner
from toolset.gui.windows.update_manager import UpdateManager
from toolset.utils.misc import open_link
from toolset.utils.window import add_window, open_resource_editor
from utility.error_handling import universal_simplify_exception
from utility.misc import is_debug_mode
from utility.tricks import debug_reload_pymodules
from utility.ui_libraries.qt.widgets.itemviews.treeview import RobustTreeView

if TYPE_CHECKING:
    from qtpy import QtGui
    from qtpy.QtCore import QPoint
    from qtpy.QtGui import QCloseEvent, QKeyEvent, QMouseEvent, QPalette, _QAction
    from qtpy.QtWidgets import QComboBox, QStyle, QWidget
    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from pykotor.extract.file import LocationResult, ResourceResult
    from pykotor.resource.formats.mdl import MDL
    from pykotor.resource.formats.mdl.mdl_data import MDL
    from pykotor.resource.formats.tpc import TPC
    from pykotor.resource.type import SOURCE_TYPES
    from toolset.gui.widgets.main_widgets import TextureList

def run_module_designer(
    active_path: str,
    active_name: str,
    active_tsl: bool,  # noqa: FBT001
    module_path: str | None = None,
):
    """An alternative way to start the ModuleDesigner: run this function in a new process so the main tool window doesn't wait on the module designer."""
    from qtpy.QtGui import QSurfaceFormat

    from toolset.__main__ import main_init
    main_init()

    # Set default OpenGL surface format before creating QApplication
    # This is critical for PyPy and ensures proper OpenGL context initialization
    fmt = QSurfaceFormat()
    fmt.setDepthBufferSize(24)
    fmt.setStencilBufferSize(8)
    fmt.setVersion(3, 3)  # Request OpenGL 3.3
    # Use CompatibilityProfile instead of CoreProfile - CoreProfile requires VAO to be bound
    # before any buffer operations, which causes issues with PyOpenGL's lazy loading
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile)
    fmt.setSamples(4)  # Enable multisampling for antialiasing
    QSurfaceFormat.setDefaultFormat(fmt)

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
        cast("QApplication", QApplication.instance()).setWindowIcon(QIcon(QPixmap(icon_path)))
    else:
        print(f"Failed to load HT main window icon from {icon_path}")
    add_window(designerUi, show=False)
    sys.exit(app.exec())


class UpdateCheckThread(QThread):
    update_info_fetched = QtCore.Signal(dict, dict, bool)  # pyright: ignore[reportPrivateImportUsage]
    def __init__(self, tool_window: ToolWindow, *, silent: bool = False):
        super().__init__()
        self.toolWindow: ToolWindow = tool_window
        self.silent: bool = silent

    def get_latest_version_info(self) -> tuple[dict[str, Any], dict[str, Any]]:
        edge_info = {}
        if self.toolWindow.settings.useBetaChannel:
            edge_info = self._get_remote_toolset_update_info(use_beta_channel=True)

        master_info = self._get_remote_toolset_update_info(use_beta_channel=False)
        return master_info, edge_info

    def _get_remote_toolset_update_info(self, *, use_beta_channel: bool) -> dict[str, Any]:
        result = get_remote_toolset_update_info(use_beta_channel=use_beta_channel, silent=self.silent)
        print(f"<SDM> [get_latest_version_info scope] {'edge_info' if use_beta_channel else 'master_info'}: ", result)

        if not isinstance(result, dict):
            if self.silent:
                result = {}
            elif isinstance(result, BaseException):
                raise result
            else:
                raise TypeError(f"Unexpected result type: {result}")

        return result

    def run(self):
        # This method is executed in a separate thread
        master_info, edge_info = self.get_latest_version_info()
        self.update_info_fetched.emit(master_info, edge_info, self.silent)


class ToolWindow(QMainWindow):
    """Main window for the Holocron Toolset."""

    sig_module_files_updated: Signal = Signal(str, str)  # pyright: ignore[reportPrivateImportUsage]
    sig_override_files_update: Signal = Signal(object, object)  # pyright: ignore[reportPrivateImportUsage]
    sig_installation_changed: Signal = Signal(HTInstallation)

    def __init__(self):
        """Initialize the main window.

        Args:
        ----
            self: The object instance
            parent: The parent widget
        """
        super().__init__()

        self.active: HTInstallation | None = None
        self.installations: dict[str, HTInstallation] = {}

        self.settings: GlobalSettings = GlobalSettings()
        self.update_manager: UpdateManager = UpdateManager(silent=True)

        # Theme setup
        q_style: QStyle | None = self.style()
        assert q_style is not None, "window style was somehow None"
        self.original_style: str = q_style.objectName()
        self.original_palette: QPalette = self.palette()
        self.theme_manager: ThemeManager = ThemeManager(self.original_style)
        # Apply both theme and style on initialization
        self.theme_manager._apply_theme_and_style(self.settings.selectedTheme, self.settings.selectedStyle)

        self.previous_game_combo_index: int = 0
        self._mouse_move_pos: QPoint | None = None
        # Initialize theme menu action dictionaries
        self._theme_actions: dict[str, _QAction] = {}
        self._style_actions: dict[str, _QAction] = {}
        # Initialize language menu action dictionary
        self._language_actions: dict[int, _QAction] = {}
        self._initUi()
        self._setup_signals()
        # Language system will set the title in apply_translations()
        self.reload_settings()
        self.unset_installation()

    def handle_change(
        self,
        path: str,
    ):
        if self.active is None:
            return

        modified_path = os.path.normpath(path)
        if os.path.isdir(modified_path):  # noqa: PTH112
            return

        now: datetime = datetime.now(tz=timezone.utc).astimezone()
        if now - self.last_modified < timedelta(seconds=1):
            return
        self.last_modified: datetime = now

        module_path: str = os.path.normpath(self.active.module_path())
        override_path: str = os.path.normpath(self.active.override_path())

        if module_path.lower() in modified_path.lower():
            self.sig_module_files_updated.emit(modified_path, "modified")
        elif override_path.lower() in modified_path.lower():
            self.sig_override_files_update.emit(modified_path, "modified")

    def _initUi(self):
        """Initialize Holocron Toolset main window UI."""
        from toolset.uic.qtpy.windows.main import Ui_MainWindow

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.coreWidget.hide_section()
        self.ui.coreWidget.hide_reload_button()

        if is_debug_mode():
            self.ui.menubar.addAction("Debug Reload").triggered.connect(debug_reload_pymodules)  # pyright: ignore[reportOptionalMemberAccess]

        self.setWindowIcon(cast(QApplication, QApplication.instance()).windowIcon())
        self.setup_modules_tab()

    def setup_modules_tab(self):
        self.erf_editor_button = QPushButton(tr("ERF Editor"), self)
        self.erf_editor_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.erf_editor_button.clicked.connect(self._open_module_tab_erf_editor)  # Connect to the ERF Editor functionality
        self.ui.verticalLayoutRightPanel.insertWidget(2, self.erf_editor_button)  # pyright: ignore[reportArgumentType]
        self.erf_editor_button.hide()
        modules_resource_list = self.ui.modulesWidget.ui
        modules_section_combo: QComboBox = modules_resource_list.sectionCombo  # type: ignore[attr-defined]
        refresh_button: QPushButton = modules_resource_list.refreshButton  # type: ignore[attr-defined]
        designer_button: QPushButton = self.ui.specialActionButton  # type: ignore[attr-defined]
        modules_resource_list.horizontalLayout_2.removeWidget(modules_section_combo)  # type: ignore[arg-type]
        modules_resource_list.horizontalLayout_2.removeWidget(refresh_button)  # type: ignore[arg-type]
        modules_resource_list.verticalLayout.removeItem(modules_resource_list.horizontalLayout_2)  # type: ignore[arg-type]
        refresh_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)  # type: ignore[arg-type]
        designer_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)  # type: ignore[arg-type]
        stack_button_layout = QVBoxLayout()
        stack_button_layout.setSpacing(1)
        stack_button_layout.addWidget(refresh_button)  # type: ignore[arg-type]
        stack_button_layout.addWidget(designer_button)  # type: ignore[arg-type]
        top_layout = QHBoxLayout()
        top_layout.addWidget(modules_section_combo)  # type: ignore[arg-type]
        top_layout.addLayout(stack_button_layout)
        self.ui.verticalLayoutModulesTab.insertLayout(0, top_layout)  # type: ignore[attributeAccessIssue]
        modules_resource_list.verticalLayout.addWidget(modules_resource_list.resourceTree)  # type: ignore[arg-type]

    def _setup_signals(self):  # sourcery skip: remove-unreachable-code  # noqa: PLR0915
        self.ui.gameCombo.currentIndexChanged.connect(self.change_active_installation)

        self.sig_module_files_updated.connect(self.on_module_file_updated)
        self.sig_override_files_update.connect(self.on_override_file_updated)

        self.ui.coreWidget.sig_request_extract_resource.connect(self.on_extract_resources)
        self.ui.coreWidget.sig_request_refresh.connect(self.on_core_refresh)
        self.ui.coreWidget.sig_request_open_resource.connect(self.on_open_resources)

        self.ui.modulesWidget.sig_section_changed.connect(self.on_module_changed)
        self.ui.modulesWidget.sig_request_reload.connect(self.on_module_reload)
        self.ui.modulesWidget.sig_request_refresh.connect(self.on_module_refresh)
        self.ui.modulesWidget.sig_request_extract_resource.connect(self.on_extract_resources)
        self.ui.modulesWidget.sig_request_open_resource.connect(self.on_open_resources)
        self.sig_installation_changed.connect(self.ui.modulesWidget.set_installation)

        self.ui.savesWidget.sig_section_changed.connect(self.on_savepath_changed)
        self.ui.savesWidget.sig_request_reload.connect(self.on_save_reload)
        self.ui.savesWidget.sig_request_refresh.connect(self.on_save_refresh)
        self.ui.savesWidget.sig_request_extract_resource.connect(self.on_extract_resources)
        self.ui.savesWidget.sig_request_open_resource.connect(self.on_open_resources)
        self.sig_installation_changed.connect(self.ui.savesWidget.set_installation)
        
        # Save Editor and corruption fix buttons
        self.ui.openSaveEditorButton.clicked.connect(self.on_open_save_editor)
        self.ui.fixCorruptionButton.clicked.connect(self.on_fix_all_corruption)
        
        # Enable/disable Open Save Editor button based on selection
        selectionModel = self.ui.savesWidget.ui.resourceTree.selectionModel()
        assert selectionModel is not None, "Selection model not found in saves widget"
        selectionModel.selectionChanged.connect(self.on_save_selection_changed)
        self.ui.resourceTabs.currentChanged.connect(self.on_tab_changed)

        def open_module_designer(*args) -> ModuleDesigner | None:
            """Open the module designer."""
            assert self.active is not None
            module_data = self.ui.modulesWidget.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
            module_path: Path | None = None
            if module_data:
                module_path = self.active.module_path() / Path(str(module_data))
            try:
                designer_window = ModuleDesigner(  # pyright: ignore[call-arg]
                    None,
                    self.active,
                    mod_filepath=module_path,
                )
            except TypeError as exc:
                RobustLogger().warning(f"ModuleDesigner signature mismatch: {exc}. Falling back without module path.")
                designer_window = ModuleDesigner(None, self.active)
                if module_path is not None:
                    QTimer.singleShot(33, lambda: designer_window.open_module(module_path))

            designer_window.setWindowIcon(cast(QApplication, QApplication.instance()).windowIcon())
            add_window(designer_window)

        self.ui.specialActionButton.clicked.connect(open_module_designer)

        self.ui.overrideWidget.sig_section_changed.connect(self.on_override_changed)
        self.ui.overrideWidget.sig_request_reload.connect(self.on_override_reload)
        self.ui.overrideWidget.sig_request_refresh.connect(self.on_override_refresh)
        self.ui.overrideWidget.sig_request_extract_resource.connect(self.on_extract_resources)
        self.ui.overrideWidget.sig_request_open_resource.connect(self.on_open_resources)
        self.sig_installation_changed.connect(self.ui.overrideWidget.set_installation)

        self.ui.texturesWidget.sig_section_changed.connect(self.on_textures_changed)
        self.ui.texturesWidget.sig_request_open_resource.connect(self.on_open_resources)
        self.sig_installation_changed.connect(self.ui.texturesWidget.set_installation)

        def extract_resources():
            self.on_extract_resources(
                self.get_active_resource_widget().selected_resources(),
                resource_widget=self.get_active_resource_widget(),
            )
        self.ui.extractButton.clicked.connect(extract_resources)
        self.ui.openButton.clicked.connect(self.get_active_resource_widget().on_resource_double_clicked)

        self.ui.openAction.triggered.connect(self.open_from_file)
        self.ui.actionSettings.triggered.connect(self.open_settings_dialog)
        self.ui.actionExit.triggered.connect(lambda *args: self.close() and None or None)

        self.ui.actionNewTLK.triggered.connect(lambda: add_window(TLKEditor(self, self.active)))
        self.ui.actionNewDLG.triggered.connect(lambda: add_window(DLGEditor(self, self.active)))
        self.ui.actionNewNSS.triggered.connect(lambda: add_window(NSSEditor(self, self.active)))
        self.ui.actionNewUTC.triggered.connect(lambda: add_window(UTCEditor(self, self.active)))  # type: ignore[arg-type]
        self.ui.actionNewUTP.triggered.connect(lambda: add_window(UTPEditor(self, self.active)))  # type: ignore[arg-type]
        self.ui.actionNewUTD.triggered.connect(lambda: add_window(UTDEditor(self, self.active)))  # type: ignore[arg-type]
        self.ui.actionNewUTI.triggered.connect(lambda: add_window(UTIEditor(self, self.active)))  # type: ignore[arg-type]
        self.ui.actionNewUTT.triggered.connect(lambda: add_window(UTTEditor(self, self.active)))
        self.ui.actionNewUTM.triggered.connect(lambda: add_window(UTMEditor(self, self.active)))
        self.ui.actionNewUTW.triggered.connect(lambda: add_window(UTWEditor(self, self.active)))
        self.ui.actionNewUTE.triggered.connect(lambda: add_window(UTEEditor(self, self.active)))
        self.ui.actionNewUTS.triggered.connect(lambda: add_window(UTSEditor(self, self.active)))  # type: ignore[arg-type]
        self.ui.actionNewGFF.triggered.connect(lambda: add_window(GFFEditor(self, self.active)))
        self.ui.actionNewERF.triggered.connect(lambda: add_window(ERFEditor(self, self.active)))
        self.ui.actionNewTXT.triggered.connect(lambda: add_window(TXTEditor(self, self.active)))
        self.ui.actionNewSSF.triggered.connect(lambda: add_window(SSFEditor(self, self.active)))
        self.ui.actionCloneModule.triggered.connect(lambda: add_window(CloneModuleDialog(self, self.active, self.installations)))  # type: ignore[arg-type]

        self.ui.actionModuleDesigner.triggered.connect(self.open_module_designer)
        self.ui.actionEditTLK.triggered.connect(self.open_active_talktable)
        self.ui.actionEditJRL.triggered.connect(self.open_active_journal)
        self.ui.actionFileSearch.triggered.connect(self.open_file_search_dialog)
        self.ui.actionIndoorMapBuilder.triggered.connect(self.open_indoor_map_builder)

        self.ui.actionInstructions.triggered.connect(self.open_instructions_window)
        self.ui.actionHelpUpdates.triggered.connect(self.update_manager.check_for_updates)
        self.ui.actionHelpAbout.triggered.connect(self.open_about_dialog)
        self.ui.actionDiscordDeadlyStream.triggered.connect(lambda: open_link("https://discord.com/invite/bRWyshn"))
        self.ui.actionDiscordKotOR.triggered.connect(lambda: open_link("http://discord.gg/kotor"))
        self.ui.actionDiscordHolocronToolset.triggered.connect(lambda: open_link("https://discord.gg/3ME278a9tQ"))

        # Setup Theme menu with both stylesheet themes and application styles in the same menu
        current_theme = self.settings.selectedTheme or "fusion (light)"
        current_style = self.settings.selectedStyle or ""
        
        # Add stylesheet themes directly to Theme menu
        available_themes = sorted(set(self.theme_manager.get_available_themes()))
        for theme_name in available_themes:
            def make_theme_handler(theme=theme_name):
                def change_theme(*args):
                    self._update_theme_menu_checkmarks(theme, None)
                    self.theme_manager.change_theme(theme)
                return change_theme
            theme_action: _QAction | None = self.ui.menuTheme.addAction(theme_name)
            assert theme_action is not None
            theme_action.setCheckable(True)
            theme_action.triggered.connect(make_theme_handler())
            self._theme_actions[theme_name.lower()] = theme_action
            # Mark current theme as checked
            if theme_name.lower() == current_theme.lower():
                theme_action.setChecked(True)
        
        # Add separator between stylesheet themes and application styles
        self.ui.menuTheme.addSeparator()
        
        # Add "Native" option for application style (system default)
        def change_to_native(*args):
            self._update_theme_menu_checkmarks(None, "")
            self.theme_manager.change_style("")  # Empty string means use theme default / native
        native_action: _QAction | None = self.ui.menuTheme.addAction(tr("Native (System Default)"))
        assert native_action is not None
        native_action.setCheckable(True)
        native_action.triggered.connect(change_to_native)
        self._style_actions[""] = native_action
        if current_style == "":
            native_action.setChecked(True)
        
        # Add all available Qt application styles
        available_styles = self.theme_manager.get_default_styles()
        for style_name in available_styles:
            def make_style_handler(style=style_name):
                def change_style(*args):
                    self._update_theme_menu_checkmarks(None, style)
                    self.theme_manager.change_style(style)
                return change_style
            style_action: _QAction | None = self.ui.menuTheme.addAction(style_name)
            assert style_action is not None
            style_action.setCheckable(True)
            style_action.triggered.connect(make_style_handler())
            self._style_actions[style_name] = style_action
            # Mark current style as checked
            if style_name == current_style:
                style_action.setChecked(True)

        self.ui.menuRecentFiles.aboutToShow.connect(self.populate_recent_files_menu)
        
        # Setup Language menu
        self._setup_language_menu()

    def _update_theme_menu_checkmarks(
        self,
        theme_name: str | None = None,
        style_name: str | None = None,
    ):
        """Update checkmarks in the theme menu based on current selection.
        
        Args:
        ----
            theme_name: The selected theme name (if changing theme)
            style_name: The selected style name (if changing style)
        """
        # Uncheck all theme actions
        for action in self._theme_actions.values():
            action.setChecked(False)
        
        # Uncheck all style actions
        for action in self._style_actions.values():
            action.setChecked(False)
        
        # Check the appropriate theme or style
        if theme_name is not None:
            theme_key = theme_name.lower()
            if theme_key in self._theme_actions:
                self._theme_actions[theme_key].setChecked(True)
        elif style_name is not None:
            if style_name in self._style_actions:
                self._style_actions[style_name].setChecked(True)

    def _setup_language_menu(self):
        """Set up the Language menu with all available languages."""
        from toolset.gui.common.localization import ToolsetLanguage
        
        # Initialize language system from settings
        current_language_id = self.settings.selectedLanguage
        try:
            current_language = ToolsetLanguage(current_language_id)
        except ValueError:
            current_language = ToolsetLanguage.ENGLISH
        
        # Set the global language
        set_language(current_language)
        
        # Add language actions to the menu
        for language in ToolsetLanguage:
            def make_language_handler(lang=language):
                def change_language(*args):
                    self.settings.selectedLanguage = lang.value
                    set_language(lang)
                    self._update_language_menu_checkmarks(lang)
                    self.apply_translations()
                return change_language
            
            display_name = language.get_display_name()
            language_action: _QAction | None = self.ui.menuLanguage.addAction(display_name)
            assert language_action is not None
            language_action.setCheckable(True)
            language_action.triggered.connect(make_language_handler())
            self._language_actions[language.value] = language_action
            
            # Mark current language as checked
            if language == current_language:
                language_action.setChecked(True)
        
        # Apply translations after setting up menu
        self.apply_translations()

    def _update_language_menu_checkmarks(self, language: ToolsetLanguage):
        """Update checkmarks in the language menu based on current selection."""
        # Uncheck all language actions
        for action in self._language_actions.values():
            action.setChecked(False)
        
        # Check the selected language
        if language.value in self._language_actions:
            self._language_actions[language.value].setChecked(True)

    def apply_translations(self):
        """Apply translations to all UI strings in the main window."""
        # Translate menu titles
        self.ui.menuFile.setTitle(tr("File"))
        self.ui.menuEdit.setTitle(tr("Edit"))
        self.ui.menuTools.setTitle(tr("Tools"))
        self.ui.menuTheme.setTitle(tr("Theme"))
        self.ui.menuLanguage.setTitle(tr("Language"))
        self.ui.menuHelp.setTitle(tr("Help"))
        self.ui.menuNew.setTitle(tr("New"))
        self.ui.menuRecentFiles.setTitle(tr("Recent Files"))
        self.ui.menuDiscord.setTitle(tr("Discord"))
        
        # Translate menu actions
        self.ui.actionExit.setText(tr("Exit"))
        self.ui.actionSettings.setText(tr("Settings"))
        self.ui.actionHelpAbout.setText(tr("About"))
        self.ui.actionInstructions.setText(tr("Instructions"))
        self.ui.actionHelpUpdates.setText(tr("Check For Updates"))
        self.ui.actionEditTLK.setText(tr("Edit Talk Table"))
        self.ui.actionEditJRL.setText(tr("Edit Journal"))
        self.ui.actionModuleDesigner.setText(tr("Module Designer"))
        self.ui.actionIndoorMapBuilder.setText(tr("Indoor Map Builder"))
        self.ui.actionKotorDiff.setText(tr("KotorDiff"))
        self.ui.actionTSLPatchDataEditor.setText(tr("TSLPatchData Editor"))
        self.ui.actionFileSearch.setText(tr("File Search"))
        self.ui.actionCloneModule.setText(tr("Clone Module"))
        self.ui.actionDiscordHolocronToolset.setText(tr("Holocron Toolset"))
        self.ui.actionDiscordKotOR.setText(tr("KOTOR Community Portal"))
        self.ui.actionDiscordDeadlyStream.setText(tr("Deadly Stream"))
        
        # Translate new resource actions
        self.ui.actionNewDLG.setText(tr("Dialog"))
        self.ui.actionNewUTC.setText(tr("Creature"))
        self.ui.actionNewUTI.setText(tr("Item"))
        self.ui.actionNewUTD.setText(tr("Door"))
        self.ui.actionNewUTP.setText(tr("Placeable"))
        self.ui.actionNewUTM.setText(tr("Merchant"))
        self.ui.actionNewUTE.setText(tr("Encounter"))
        self.ui.actionNewUTT.setText(tr("Trigger"))
        self.ui.actionNewUTW.setText(tr("Waypoint"))
        self.ui.actionNewUTS.setText(tr("Sound"))
        self.ui.actionNewNSS.setText(tr("Script"))
        self.ui.actionNewTLK.setText(tr("TalkTable"))
        self.ui.actionNewGFF.setText(tr("GFF"))
        self.ui.actionNewERF.setText(tr("ERF"))
        self.ui.actionNewTXT.setText(tr("TXT"))
        self.ui.actionNewSSF.setText(tr("SSF"))
        
        # Translate tab titles
        self.ui.resourceTabs.setTabText(0, tr("Core"))
        self.ui.resourceTabs.setTabText(1, tr("Saves"))
        self.ui.resourceTabs.setTabText(2, tr("Modules"))
        self.ui.resourceTabs.setTabText(3, tr("Override"))
        self.ui.resourceTabs.setTabText(4, tr("Textures"))
        
        # Translate buttons
        self.ui.openButton.setText(tr("Open Selected"))
        self.ui.extractButton.setText(tr("Extract Selected"))
        self.ui.openSaveEditorButton.setText(tr("Open Save Editor"))
        self.ui.fixCorruptionButton.setText(tr("Fix Corruption"))
        self.ui.specialActionButton.setText(tr("Designer"))
        
        # Translate tooltips
        self.ui.openSaveEditorButton.setToolTip(tr("Open the selected save in the Save Editor"))
        self.ui.fixCorruptionButton.setToolTip(tr("Fixes all possible save corruption in all saves"))
        
        # Translate group boxes
        self.ui.tpcGroup_2.setTitle(tr("TPC"))
        self.ui.mdlGroup_2.setTitle(tr("MDL"))
        
        # Translate checkboxes
        self.ui.tpcDecompileCheckbox.setText(tr("Decompile"))
        self.ui.tpcTxiCheckbox.setText(tr("Extract TXI"))
        self.ui.mdlDecompileCheckbox.setText(tr("Decompile"))
        self.ui.mdlDecompileCheckbox.setToolTip(tr("Decompile feature is not available."))
        self.ui.mdlTexturesCheckbox.setText(tr("Extract Textures"))
        
        # Update window title
        self.setWindowTitle(f"{tr('Holocron Toolset')} ({qtpy.API_NAME})")

    def on_open_resources(
        self,
        resources: list[FileResource],
        use_specialized_editor: bool | None = None,
        resource_widget: ResourceList | TextureList | None = None,
    ):
        assert self.active is not None
        for resource in resources:
            _filepath, _editor = open_resource_editor(resource, self.active, self, gff_specialized=use_specialized_editor)
        if resources:
            return
        if not isinstance(resource_widget, ResourceList):
            return
        filename = str(resource_widget.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole))
        if not filename:
            return
        erf_filepath = self.active.module_path() / filename
        if not erf_filepath.is_file():
            return
        res_ident = ResourceIdentifier.from_path(erf_filepath)
        if not res_ident.restype:
            return
        erf_resource = FileResource(res_ident.resname, res_ident.restype, os.path.getsize(erf_filepath), 0x0, erf_filepath)  # noqa: PTH202
        _filepath, _editor = open_resource_editor(erf_resource, self.active, self, gff_specialized=use_specialized_editor)

    def populate_recent_files_menu(
        self,
        _checked: bool | None = None,
    ):
        recent_files_setting: list[str] = self.settings.recentFiles
        recent_files: list[Path] = [Path(file) for file in recent_files_setting]
        self.ui.menuRecentFiles.clear()
        for file in recent_files:
            action = QAction(file.name, self)
            action.setData(file)
            action.triggered.connect(lambda *args, a=action: self.open_recent_file(action=a))
            self.ui.menuRecentFiles.addAction(action)  # type: ignore[arg-type]

    def open_recent_file(
        self,
        *args,
        action: _QAction,
    ):
        file = action.data()
        if not file or not isinstance(file, Path):
            return
        resource = FileResource.from_path(file)
        open_resource_editor(resource, self.active, self)

    # region Signal callbacks
    def on_core_refresh(self):
        self.refresh_core_list(reload=True)

    @Slot(str)
    def on_module_changed(
        self,
        new_module_file: str,
    ):
        self.on_module_reload(new_module_file)

    @Slot(str)
    def on_module_reload(
        self,
        module_file: str,
    ):
        assert self.active is not None, "No active installation selected"
        if not module_file or not module_file.strip():
            return
        RobustLogger().info(f"Reloading module '{module_file}'")
        resources: list[FileResource] = self.active.module_resources(module_file)
        module_file_name = PurePath(module_file).name
        if self.settings.joinRIMsTogether and ((is_rim_file(module_file) or is_erf_file(module_file)) and not module_file_name.lower().endswith(("_s.rim", "_dlg.erf"))):
            resources.extend(self.active.module_resources(f"{PurePath(module_file).stem}_s.rim"))
            if self.active.game().is_k2():
                resources.extend(self.active.module_resources(f"{PurePath(module_file).stem}_dlg.erf"))

        RobustLogger().info(f"Setting {len(resources)} resources for module '{module_file}'")
        self.active.reload_module(module_file)
        self.ui.modulesWidget.set_resources(resources)

    @Slot(str, str)
    def on_module_file_updated(
        self,
        changed_file: str,
        event_type: str,
    ):
        assert self.active is not None, "No active installation selected"
        if event_type == "deleted":
            self.refresh_module_list()
        else:
            self.active.reload_module(changed_file)
            if self.ui.modulesWidget.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole) == changed_file:
                self.on_module_reload(changed_file)

    def on_module_refresh(self):  # noqa: FBT001, FBT002
        self.refresh_module_list()

    @Slot(str)
    def on_savepath_changed(
        self,
        new_save_dir: str,
    ):
        from qtpy.QtGui import QBrush, QColor
        
        assert self.active is not None, "No active installation selected"
        self.ui.savesWidget.modules_model.invisibleRootItem().removeRows(0, self.ui.savesWidget.modules_model.rowCount())  # pyright: ignore[reportOptionalMemberAccess]
        new_save_dir_path = Path(new_save_dir)
        if new_save_dir_path not in self.active.saves:
            self.active.load_saves()
        if new_save_dir_path not in self.active.saves:
            return
        for save_path, resource_list in self.active.saves[new_save_dir_path].items():
            save_path_item = QStandardItem(str(save_path.relative_to(save_path.parent.parent)))
            
            # Check if this save is corrupted
            is_corrupted = self.active.is_save_corrupted(save_path)
            if is_corrupted:
                # Add red border/background color for corrupted saves
                save_path_item.setBackground(QBrush(QColor(255, 220, 220)))  # Light red background
                save_path_item.setForeground(QBrush(QColor(139, 0, 0)))  # Dark red text
                # Add tooltip
                save_path_item.setToolTip(
                    tr("This save is corrupted.\n"
                    "Right click and press <i>'Fix savegame corruption'</i> to fix this.")
                )
            
            self.ui.savesWidget.modules_model.invisibleRootItem().appendRow(save_path_item)  # pyright: ignore[reportOptionalMemberAccess]
            category_items_under_save_path: dict[str, QStandardItem] = {}
            for resource in resource_list:
                category: str = resource.restype().category
                if category not in category_items_under_save_path:
                    category_item = QStandardItem(category)
                    category_item.setSelectable(False)
                    unused_item = QStandardItem("")
                    unused_item.setSelectable(False)
                    save_path_item.appendRow([category_item, unused_item])
                    category_items_under_save_path[category] = category_item
                category_item = category_items_under_save_path[category]

                found_resource = False
                for i in range(category_item.rowCount()):
                    item = category_item.child(i)
                    if item is not None and isinstance(item, ResourceStandardItem) and item.resource == resource:
                        item.resource = resource
                        found_resource = True
                        break
                if not found_resource:
                    category_item.appendRow(
                        [
                            ResourceStandardItem(resource.resname(), resource=resource),
                            QStandardItem(resource.restype().extension.upper()),
                        ]
                    )

    def on_save_reload(
        self,
        save_dir: str,
    ):
        RobustLogger().info(f"Reloading save directory '{save_dir}'")
        self.on_savepath_changed(save_dir)

    def on_save_refresh(self):
        RobustLogger().info("Refreshing save list")
        self.refresh_saves_list()
    
    @Slot()
    def on_save_selection_changed(self):
        """Enable/disable Open Save Editor button based on selection."""
        has_selection = len(self.ui.savesWidget.ui.resourceTree.selectedIndexes()) > 0
        self.ui.openSaveEditorButton.setEnabled(has_selection)
    
    @Slot()
    def on_open_save_editor(self):
        """Open the Save Editor for the selected save."""
        try:
            if self.active is None:
                RobustLogger().warning("Cannot open save editor: no active installation")
                return
            
            # Safely get the saves widget and tree
            saves_widget: ResourceList = self.ui.savesWidget
            if saves_widget is None:
                RobustLogger().warning("Saves widget not found")
                return
            
            tree_view: RobustTreeView = saves_widget.ui.resourceTree
            if tree_view is None:
                RobustLogger().warning("Resource tree not found in saves widget")
                return
            
            # Get selected save folder
            selected_indexes: list[QModelIndex] = tree_view.selectedIndexes()
            if not selected_indexes:
                RobustLogger().debug("No selected indexes in saves tree")
                return
            
            # Get the top-level save folder item
            model: ResourceModel = saves_widget.modules_model            
            proxy_model: QStandardItemModel | QAbstractItemModel | None = tree_view.model()
            if proxy_model is None or not isinstance(proxy_model, QSortFilterProxyModel):
                RobustLogger().error(f"Proxy model not found or not a QSortFilterProxyModel: {proxy_model.__class__.__name__}")
                return
            
            for index in selected_indexes:
                source_index: QModelIndex = proxy_model.mapToSource(index)
                item: QStandardItem | None = None
                if source_index.isValid():
                    item = model.itemFromIndex(source_index)
                
                if not item:
                    continue
                
                # Navigate up to find the save folder item (top-level item)
                while item and item.parent():
                    item = item.parent()
                
                if item:
                    save_name = item.text()
                    RobustLogger().debug(f"Looking for save folder: {save_name}")
                    
                    # Get current save location from combo box
                    current_save_location_str = saves_widget.ui.sectionCombo.currentData(QtCore.Qt.ItemDataRole.UserRole)
                    if not current_save_location_str:
                        RobustLogger().warning("No save location selected")
                        continue
                        
                    current_save_location = Path(current_save_location_str)
                    
                    # Find the save path
                    save_paths = self.active.saves.get(current_save_location, {})
                    for save_path in save_paths:
                        # Match on the folder name (last part of path)
                        if save_path.name == save_name or save_name in str(save_path):
                            RobustLogger().info(f"Opening save editor for: {save_path}")
                            self.open_save_editor_for_path(save_path)
                            return  # Exit after opening
                    
                    RobustLogger().warning(f"Could not find save path for: {save_name}")
                    break
        except Exception as e:
            RobustLogger().exception(f"Error opening save editor: {e}")
    
    def open_save_editor_for_path(self, save_path: Path):
        """Open the Save Editor for a specific save path."""
        from toolset.gui.editors.savegame import SaveGameEditor
        
        try:
            # Create and show the save editor
            editor = SaveGameEditor(self, self.active)
            
            # Load the save
            savegame_sav = save_path / "SAVEGAME.sav"
            if savegame_sav.exists():
                with open(savegame_sav, "rb") as f:
                    data = f.read()
                editor.load(str(save_path), save_path.name, ResourceType.SAV, data)
            else:
                # If SAVEGAME.sav doesn't exist, load the folder directly
                editor.load(str(save_path), save_path.name, ResourceType.SAV, b"")
            
            editor.show()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                tr("Error Opening Save Editor"),
                trf("Failed to open save editor:\n{error}", error=str(e)),
            )
            RobustLogger().exception(f"Failed to open save editor for '{save_path}'")
    
    @Slot()
    def on_fix_all_corruption(self):
        """Fix EventQueue corruption in all saves."""
        if self.active is None:
            return
        
        fixed_count = 0
        failed_count = 0
        
        # Fix all saves in all locations
        for save_location in self.active.saves:
            for save_path in self.active.saves[save_location]:
                try:
                    if self.active.fix_save_corruption(save_path):
                        fixed_count += 1
                except Exception as e:
                    RobustLogger().error(f"Failed to fix corruption in '{save_path}': {e}")
                    failed_count += 1
        
        # Show results
        if fixed_count > 0 or failed_count > 0:
            msg = trf("Fixed corruption in {count} save(s).", count=fixed_count)
            if failed_count > 0:
                msg += "\n" + trf("Failed to fix {count} save(s).", count=failed_count)
            QMessageBox.information(self, tr("Fix Corruption Complete"), msg)
        else:
            QMessageBox.information(self, tr("No Corruption Found"), tr("No corrupted saves were found."))
        
        # Refresh the saves list to update corruption indicators
        self.refresh_saves_list()
    
    def fix_save_corruption_for_path(self, save_path: Path):
        """Fix EventQueue corruption for a specific save path."""
        if self.active is None:
            return
        
        try:
            if self.active.fix_save_corruption(save_path):
                QMessageBox.information(
                    self,
                    tr("Corruption Fixed"),
                    trf("Successfully fixed corruption in save:\n{name}", name=save_path.name),
                )
                # Refresh the saves list to update corruption indicators
                self.refresh_saves_list()
            else:
                QMessageBox.warning(
                    self,
                    tr("Fix Failed"),
                    trf("Failed to fix corruption in save:\n{name}", name=save_path.name),
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                tr("Error"),
                trf("An error occurred while fixing corruption:\n{error}", error=str(e)),
            )
            RobustLogger().exception(f"Failed to fix corruption for '{save_path}'")

    def on_override_file_updated(
        self,
        changed_file: str,
        event_type: str,
    ):
        if event_type == "deleted":
            self.refresh_override_list(reload=True)
        else:
            self.on_override_reload(changed_file)

    def on_override_changed(
        self,
        new_directory: str,
    ):
        assert self.active is not None, "No active installation selected"
        self.ui.overrideWidget.set_resources(self.active.override_resources(new_directory))

    def on_override_reload(
        self,
        file_or_folder: str,
    ):
        assert self.active is not None, "No active installation selected"
        override_path = self.active.override_path()

        file_or_folder_path = override_path.joinpath(file_or_folder)
        if file_or_folder_path.is_file():
            rel_folderpath = file_or_folder_path.parent.relative_to(self.active.override_path())
            self.active.reload_override_file(file_or_folder_path)
        else:
            rel_folderpath = file_or_folder_path.relative_to(self.active.override_path())
            self.active.load_override(str(rel_folderpath))
        self.ui.overrideWidget.set_resources(self.active.override_resources(str(rel_folderpath) if rel_folderpath.name else None))

    def on_override_refresh(self):
        self.refresh_override_list(reload=True)

    def on_textures_changed(self, texturepackName: str):
        assert self.active is not None, "No active installation selected"
        self.ui.texturesWidget.set_resources(self.active.texturepack_resources(texturepackName))

    @Slot(int)
    def change_active_installation(
        self,
        index: int,  # noqa: PLR0915, C901, PLR0912
    ):
        if index < 0:  # self.ui.gameCombo.clear() will call this function with -1
            return

        prev_index: int = self.previous_game_combo_index
        self.ui.gameCombo.setCurrentIndex(index)

        if index == 0:
            self.unset_installation()
            self.previous_game_combo_index = 0
            return

        name: str = self.ui.gameCombo.itemText(index)
        path: str = self.settings.installations()[name].path.strip()
        tsl: bool = self.settings.installations()[name].tsl

        # If the user has not set a path for the particular game yet, ask them too.
        if not path or not path.strip() or not Path(path).is_dir():
            if path and path.strip():
                QMessageBox(QMessageBox.Icon.Warning, f"Installation '{path}' not found", "Select another path now.").exec()
            path = QFileDialog.getExistingDirectory(self, trf("Select the game directory for {name}", name=name), "Knights of the Old Republic II" if tsl else "swkotor")

        # If the user still has not set a path, then return them to the [None] option.
        if not path or not path.strip():
            self.ui.gameCombo.setCurrentIndex(prev_index)
            return

        # KEEP UI CODE IN MAIN THREAD!
        self.ui.resourceTabs.setEnabled(True)

        def create_installation_task(loader: AsyncLoader) -> HTInstallation:
            """Creates and returns a new HTInstallation instance.

            Returns:
            -------
                HTInstallation: The newly created installation instance
            """
            if loader is not None and loader._realtime_progress:  # noqa: SLF001
                return HTInstallation(Path(path), name, tsl=tsl, progress_callback=loader.progress_callback_api)
            return HTInstallation(Path(path), name, tsl=tsl)

        active: HTInstallation | None = self.installations.get(name)
        if active is None:
            installation_loader = AsyncLoader.__new__(AsyncLoader)
            installation_loader.__init__(
                self,
                "Creating installation...",
                lambda: create_installation_task(installation_loader),
                "Failed to create installation",
                realtime_progress=True,
            )
            if not installation_loader.exec():
                RobustLogger().error("installation_loader.exec() failed.")
                self.ui.gameCombo.setCurrentIndex(prev_index)
                return
            self.active = installation_loader.value
        assert self.active is not None

        def prepare_task() -> tuple[list[QStandardItem] | None, ...]:
            """Prepares the lists of modules, overrides, and textures for the active installation.

            Returns:
            -------
                tuple[list[QStandardItem] | None, ...]: A tuple containing the lists of modules, overrides, and textures.
            """
            ret_tuple: tuple[list[QStandardItem] | None, ...] = (
                self._get_modules_list(reload=False),
                self._get_override_list(reload=False),
                self._get_texture_pack_list(),
            )
            return ret_tuple

        prepare_loader = AsyncLoader(self, "Preparing resources...", lambda: prepare_task(), "Failed to load installation")
        if not prepare_loader.exec():
            RobustLogger().error("prepare_loader.exec() failed.")
            self.ui.gameCombo.setCurrentIndex(prev_index)
            return
        assert prepare_loader.value is not None
        assert self.active is not None

        # Any issues past this point must call self.unset_installation()
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
            self.refresh_core_list(reload=False)
            self.refresh_saves_list(reload=False)
        except Exception as e:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            RobustLogger().exception("Failed to initialize the installation")
            QMessageBox(
                QMessageBox.Icon.Critical,
                "An unexpected error occurred initializing the installation.",
                f"Failed to initialize the installation {name}<br><br>{e}",
            ).exec()
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

    # FileSearcher/FileResults
    @Slot(list, HTInstallation)
    def handle_search_completed(
        self,
        results_list: list[FileResource],
        searched_installations: HTInstallation,
    ):
        """Event callback when the file searcher has completed its search."""
        results_dialog = FileResults(self, results_list, searched_installations)
        results_dialog.sig_searchresults_selected.connect(self.handle_results_selection)
        results_dialog.show()
        add_window(results_dialog)

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
    def closeEvent(self, e: QCloseEvent | None):  # pylint: disable=unused-argument  # pyright: ignore[reportIncompatibleMethodOverride]
        instance: QCoreApplication | None = QCoreApplication.instance()
        if instance is None:
            sys.exit()
        else:
            instance.quit()

    def mouseMoveEvent(self, event: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        if event.buttons() == Qt.MouseButton.LeftButton:
            if self._mouse_move_pos is None:
                return
            globalPos = event.globalPos() if qtpy.QT5 else event.globalPosition().toPoint()  # pyright: ignore[reportAttributeAccessIssue]
            self.move(self.mapFromGlobal(self.mapToGlobal(self.pos()) + (globalPos - self._mouse_move_pos)))
            self._mouse_move_pos = globalPos

    def mousePressEvent(self, event: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        if event.button() == Qt.MouseButton.LeftButton:
            self._mouse_move_pos = event.globalPos() if qtpy.QT5 else event.globalPosition().toPoint()  # pyright: ignore[reportAttributeAccessIssue]

    def mouseReleaseEvent(self, event: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        if event.button() == Qt.MouseButton.LeftButton:
            self._mouse_move_pos = None

    def keyPressEvent(self, event: QKeyEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        super().keyPressEvent(event)

    def dragEnterEvent(self, e: QtGui.QDragEnterEvent | None):  # pyright: ignore[reportIncompatibleMethodOverride]
        if e is None:
            return
        event_mimedata = e.mimeData()
        if event_mimedata is None:
            return
        if not event_mimedata.hasUrls():
            return
        for url in event_mimedata.urls():
            try:
                filepath = url.toLocalFile()
                _resref, restype = ResourceIdentifier.from_path(filepath).unpack()
            except Exception:  # noqa: BLE001, PERF203
                RobustLogger().exception("Could not process dragged-in item.")
                e.ignore()
                return
            else:
                if restype:
                    continue
                RobustLogger().debug(f"Not processing dragged-in item '{filepath}'. Unsupported restype.")
        e.accept()

    def dropEvent(self, e: QtGui.QDropEvent | None):  # pyright: ignore[reportIncompatibleMethodOverride]
        if e is None:
            return
        event_mimedata = e.mimeData()
        if event_mimedata is None:
            return
        for url in event_mimedata.urls():
            filepath: str = url.toLocalFile()
            resname, restype = ResourceIdentifier.from_path(filepath).unpack()
            if not restype:
                RobustLogger().debug(f"Not loading dropped file '{filepath}'. Unsupported restype.")
                continue
            resource = FileResource(resname, restype, os.path.getsize(filepath), 0x0, filepath)  # noqa: PTH202
            open_resource_editor(resource, self.active, self, gff_specialized=GlobalSettings().gffSpecializedEditors)

    # endregion

    # region Menu Bar
    def update_menus(self):
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

        # KotorDiff is always available
        self.ui.actionKotorDiff.setEnabled(True)

        # TSLPatchData editor is always available
        self.ui.actionTSLPatchDataEditor.setEnabled(True)

        self.ui.actionCloneModule.setEnabled(self.active is not None)

    def debounce_module_designer_load(self):
        """Prevents users from spamming the start button, which could easily result in a bad crash."""
        self.module_designer_load_processed = True

    def open_module_designer(self):
        assert self.active is not None, "No installation loaded."
        selected_module: Path | None = None
        try:
            combo_data = self.ui.modulesWidget.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        except Exception:  # noqa: BLE001
            combo_data = None
        if combo_data:
            selected_module = self.active.module_path() / Path(str(combo_data))
        try:
            designer_window = ModuleDesigner(None, self.active, mod_filepath=selected_module)  # pyright: ignore[call-arg]
        except TypeError as exc:
            RobustLogger().warning(f"ModuleDesigner signature mismatch: {exc}. Falling back without module path.")
            designer_window = ModuleDesigner(None, self.active)
            if selected_module is not None:
                QTimer.singleShot(33, lambda: designer_window.open_module(selected_module))
        add_window(designer_window)

    def open_settings_dialog(self):
        """Opens the Settings dialog and refresh installation combo list if changes."""
        dialog = SettingsDialog(self)
        if (
            dialog.exec()
            and dialog.installation_edited
            and QMessageBox(
                QMessageBox.Icon.Question,
                "Reload the installations?",
                "You appear to have made changes to your installations, would you like to reload?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,
            ).exec()
            == QMessageBox.StandardButton.Yes
        ):
            self.reload_settings()

    @Slot()
    def open_active_talktable(self):
        assert self.active is not None, "No installation loaded."
        c_filepath = self.active.path() / "dialog.tlk"
        if not c_filepath.exists() or not c_filepath.is_file():
            QMessageBox(
                QMessageBox.Icon.Information,
                "dialog.tlk not found",
                f"Could not open the TalkTable editor, dialog.tlk not found at the expected location<br><br>{c_filepath}.",
            ).exec()
            return
        resource = FileResource("dialog", ResourceType.TLK, os.path.getsize(c_filepath), 0x0, c_filepath)  # noqa: PTH202
        open_resource_editor(resource, self.active, self)

    @Slot()
    def open_active_journal(self):
        assert self.active is not None, "No active installation selected"
        jrl_ident: ResourceIdentifier = ResourceIdentifier("global", ResourceType.JRL)
        journal_resources: dict[ResourceIdentifier, list[LocationResult]] = self.active.locations(
            [jrl_ident],
            [SearchLocation.OVERRIDE, SearchLocation.CHITIN],
        )
        if not journal_resources or not journal_resources.get(jrl_ident):
            QMessageBox(QMessageBox.Icon.Critical, "global.jrl not found", "Could not open the journal editor: 'global.jrl' not found.").exec()
            return
        relevant: list[LocationResult] = journal_resources[jrl_ident]
        if len(relevant) > 1:
            dialog = FileSelectionWindow(relevant, self.active)
            dialog.show()
            add_window(dialog)
        else:
            open_resource_editor(relevant[0].as_file_resource(), self.active, self)

    @Slot()
    def open_file_search_dialog(self):
        assert self.active is not None, "No installation active"
        file_searcher_dialog = FileSearcher(self, self.installations)
        file_searcher_dialog.setModal(False)  # Make the dialog non-modal
        file_searcher_dialog.show()  # Show the dialog without blocking
        file_searcher_dialog.file_results.connect(self.handle_search_completed)
        add_window(file_searcher_dialog)

    @Slot()
    def open_indoor_map_builder(self):
        builder = IndoorMapBuilder(None, self.active)
        builder.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        builder.show()
        builder.activateWindow()
        add_window(builder)

    def open_instructions_window(self):
        """Opens the instructions window."""
        window = HelpWindow(None)
        window.setWindowIcon(self.windowIcon())
        window.show()
        window.activateWindow()
        add_window(window)

    def open_about_dialog(self):
        """Opens the about dialog."""
        About(self).exec()

    # endregion

    # region Other
    def get_active_tab_index(self) -> int:
        return self.ui.resourceTabs.currentIndex()

    def get_active_resource_tab(self) -> QWidget:
        return self.ui.resourceTabs.currentWidget()  # pyright: ignore[reportReturnType]

    def get_active_resource_widget(self) -> ResourceList | TextureList:
        current_widget: QWidget = self.get_active_resource_tab()
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
        reslist = self.get_active_resource_widget()
        assert isinstance(reslist, ResourceList)
        filename = reslist.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
        if not filename:
            return
        erf_filepath = self.active.module_path() / filename
        if not erf_filepath.is_file():
            return
        res_ident: ResourceIdentifier = ResourceIdentifier.from_path(erf_filepath)
        if not res_ident.restype:
            return
        erf_file_resource = FileResource(res_ident.resname, res_ident.restype, os.path.getsize(erf_filepath), 0x0, erf_filepath)  # noqa: PTH202
        _filepath, _editor = open_resource_editor(
            erf_file_resource,
            self.active,
            self,
            gff_specialized=self.settings.gffSpecializedEditors,
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
        if tree == self.ui.coreWidget:
            self.ui.resourceTabs.setCurrentWidget(self.ui.coreTab)  # pyright: ignore[reportArgumentType]
            self.ui.coreWidget.set_resource_selection(resource)

        elif tree == self.ui.modulesWidget:
            self.ui.resourceTabs.setCurrentWidget(self.ui.modulesTab)  # pyright: ignore[reportArgumentType]
            filename = resource.filepath().name
            self.change_module(filename)
            self.ui.modulesWidget.set_resource_selection(resource)

        elif tree == self.ui.overrideWidget:
            self._select_override_resource(resource)
        elif tree == self.ui.savesWidget:
            self.ui.resourceTabs.setCurrentWidget(self.ui.savesTab)  # pyright: ignore[reportArgumentType]
            filename = resource.filepath().name
            self.on_save_reload(filename)

    def _select_override_resource(self, resource: FileResource):
        assert self.active is not None
        self.ui.resourceTabs.setCurrentWidget(self.ui.overrideTab)  # pyright: ignore[reportArgumentType]
        self.ui.overrideWidget.set_resource_selection(resource)
        subfolder: str = "."
        for folder_name in self.active.override_list():
            folder_path = self.active.override_path() / folder_name
            if os.path.commonpath([resource.filepath(), folder_path]) == str(folder_path) and len(subfolder) < len(folder_path.name):
                subfolder = folder_name
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
        self.update_menus()
        self.active = None

    # endregion

    # region ResourceList handlers
    def refresh_core_list(self, *, reload: bool = True):
        """Rebuilds the tree in the Core tab. Used with the flatten/unflatten logic."""
        if self.active is None:
            return
        try:
            self.ui.coreWidget.set_resources(self.active.core_resources())
        except Exception:  # noqa: BLE001
            RobustLogger().exception("Failed to setResources of the core list")
        try:
            self.ui.coreWidget.modules_model.remove_unused_categories()
        except Exception:  # noqa: BLE001
            RobustLogger().exception("Failed to remove unused categories in the core list")

    def change_module(self, module_name: str):
        self.ui.modulesWidget.change_section(module_name)

    def refresh_module_list(
        self,
        *,
        reload: bool = True,
        module_items: list[QStandardItem] | None = None,
    ):
        """Refreshes the list of modules in the modulesCombo combobox."""
        RobustLogger().info("Refreshing module list")
        module_items = [] if module_items is None else module_items
        action: Literal["Reload", "Refresh"] = "Reload" if reload else "Refresh"
        if not module_items:
            try:
                module_items = self._get_modules_list(reload=reload)
            except Exception:  # noqa: BLE001
                RobustLogger().exception(f"Failed to get the list of {action}ed modules!")

        try:
            self.ui.modulesWidget.set_sections(module_items)
        except Exception:  # noqa: BLE001
            RobustLogger().exception(f"Failed to call setSections on the {action}ed modulesWidget!")

    def _get_modules_list(self, *, reload: bool = True) -> list[QStandardItem]:  # noqa: C901
        """Refreshes the list of modules in the modulesCombo combobox."""
        if self.active is None:
            return []
        # If specified the user can forcibly reload the resource list for every module
        if reload:
            try:
                self.active.load_modules()
            except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
                RobustLogger().exception("Failed to reload the list of modules (load_modules function)")

        try:
            area_names: dict[str, str | None] = self.active.module_names()
        except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            RobustLogger().exception("Failed to get the list of area names from the modules!")
            area_names = {k: (str(v[0].filepath()) if v else "unknown filepath") for k, v in self.active._modules.items()}

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
                    sort_str = (area_names.get(module_file_name, "y") or "unknown_area_name").lower()
                else:  # alternate mod id that attempts to match to filename.
                    assert self.active is not None, "self.active is None"
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
                if self.settings.joinRIMsTogether:
                    if lower_module_name.endswith("_s.rim"):
                        continue
                    if self.active.game().is_k2() and lower_module_name.endswith("_dlg.erf"):
                        continue

                area_text: str = area_names.get(module_name) or "<Missing ARE>"
                item: QStandardItem = QStandardItem(f"{area_text} [{module_name}]")
                item.setData(f"{area_text}\n{module_name}", Qt.ItemDataRole.DisplayRole)
                item.setData(module_name, Qt.ItemDataRole.UserRole)  # Set area name
                item.setData(module_name, Qt.ItemDataRole.UserRole + 11)  # Set module name

                # Some users may choose to have items representing RIM files to have grey text.
                if self.settings.greyRIMText and lower_module_name.endswith(("_dlg.erf", ".rim")):
                    item.setForeground(self.palette().shadow())

                modules.append(item)
            except Exception:  # noqa: PERF203, BLE001
                RobustLogger().exception(f"Unexpected exception thrown while parsing module '{module_name}', skipping...")
        return modules

    def change_override_folder(
        self,
        subfolder: str,
    ):
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

    def _get_texture_pack_list(self) -> list[QStandardItem] | None:
        assert self.active is not None, "No installation set. This should never happen!"
        texture_pack_list: list[QStandardItem] = []
        for texturepack in self.active.texturepacks_list():
            section = QStandardItem(str(texturepack))
            section.setData(texturepack, QtCore.Qt.ItemDataRole.UserRole)
            texture_pack_list.append(section)
        return texture_pack_list

    def refresh_saves_list(
        self,
        *,
        reload: bool = True,
    ):
        assert self.active is not None, "No installation set, this should never happen!"
        try:
            if reload:
                self.active.load_saves()

            saves_list: list[QStandardItem] = []
            for save_path in self.active.saves:
                save_path_str = str(save_path)
                section = QStandardItem(save_path_str)
                section.setData(save_path_str, QtCore.Qt.ItemDataRole.UserRole)
                saves_list.append(section)
            self.ui.savesWidget.set_sections(saves_list)
        except Exception:  # noqa: BLE001
            RobustLogger().exception("Failed to load/refresh the saves list")

    # endregion

    # region Extract
    @Slot(str)
    def _save_capsule_from_tool_ui(self, module_name: str):
        assert self.active is not None
        c_filepath = self.active.module_path() / module_name
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
        filepath_str, _filter = QFileDialog.getSaveFileName(
            self,
            trf("Save extracted {type} '{name}' as...", type=capsule_type, name=c_filepath.stem),
            str(Path.cwd().resolve()),
            capsule_filter,
            extension_to_filter[c_filepath.suffix.lower()],  # defaults to the original extension.
        )
        if not filepath_str or not filepath_str.strip():
            return
        r_save_filepath = Path(filepath_str)
        try:
            if is_mod_file(r_save_filepath):
                if capsule_type == "mod":
                    write_erf(read_erf(c_filepath), r_save_filepath)
                    QMessageBox(QMessageBox.Icon.Information, "Module Saved", f"Module saved to '{r_save_filepath}'").exec()
                else:
                    module.rim_to_mod(r_save_filepath, self.active.module_path(), module_name, self.active.game())
                    QMessageBox(QMessageBox.Icon.Information, "Module Built", f"Module built from relevant RIMs/ERFs and saved to '{r_save_filepath}'").exec()
                return

            erf_or_rim: ERF | RIM = read_erf(c_filepath) if is_any_erf_type_file(c_filepath) else read_rim(c_filepath)
            if is_rim_file(r_save_filepath):
                if isinstance(erf_or_rim, ERF):
                    erf_or_rim = erf_or_rim.to_rim()
                write_rim(erf_or_rim, r_save_filepath)
                QMessageBox(QMessageBox.Icon.Information, "RIM Saved", f"Resource Image File saved to '{r_save_filepath}'").exec()

            elif is_any_erf_type_file(r_save_filepath):
                if isinstance(erf_or_rim, RIM):
                    erf_or_rim = erf_or_rim.to_erf()
                erf_or_rim.erf_type = ERFType.from_extension(r_save_filepath)
                write_erf(erf_or_rim, r_save_filepath)
                QMessageBox(QMessageBox.Icon.Information, "ERF Saved", f"Encapsulated Resource File saved to '{r_save_filepath}'").exec()

        except Exception as e:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            RobustLogger().exception("Error extracting capsule file '%s'", module_name)
            QMessageBox(QMessageBox.Icon.Critical, "Error saving capsule file", str(universal_simplify_exception(e))).exec()

    def build_extract_save_paths(
        self,
        resources: list[FileResource],
    ) -> tuple[Path, dict[FileResource, Path]] | tuple[None, None]:
        # TODO(th3w1zard1): currently doesn't handle same filenames existing for extra extracts e.g. tpcTxiCheckbox.isChecked() or mdlTexturesCheckbox.isChecked()
        paths_to_write: dict[FileResource, Path] = {}

        folder_path_str: str = QFileDialog.getExistingDirectory(self, tr("Extract to folder"))
        if not folder_path_str or not folder_path_str.strip():
            RobustLogger().debug("User cancelled folderpath extraction.")
            return None, None

        folder_path = Path(folder_path_str)
        for resource in resources:
            identifier: ResourceIdentifier = resource.identifier()
            save_path: Path = folder_path / str(identifier)
            # Determine the final save path based on UI checks
            if resource.restype() is ResourceType.TPC and self.ui.tpcDecompileCheckbox.isChecked():
                save_path = save_path.with_suffix(".tga")
            elif resource.restype() is ResourceType.MDL and self.ui.mdlDecompileCheckbox.isChecked():
                save_path = save_path.with_suffix(".mdl.ascii")
            paths_to_write[resource] = save_path
        return folder_path, paths_to_write

    @Slot(list, object)
    def on_extract_resources(
        self,
        selected_resources: list[FileResource],
        resource_widget: ResourceList | TextureList | None = None,
    ):
        if selected_resources:
            folder_path, paths_to_write = self.build_extract_save_paths(selected_resources)
            if folder_path is None or paths_to_write is None:
                return
            failed_savepath_handlers: dict[Path, Exception] = {}
            resource_save_paths: dict[FileResource, Path] = FileSaveHandler(selected_resources).determine_save_paths(paths_to_write, failed_savepath_handlers)
            if not resource_save_paths:
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
                loader.errors.extend(failed_savepath_handlers.values())
                loader.exec()
            else:
                for resource, save_path in resource_save_paths.items():
                    self._extract_resource(resource, save_path, loader, seen_resources)

            # quick main thread/ui check.
            if QThread.currentThread() != cast(QApplication, QApplication.instance()).thread():
                return
            if loader.errors:
                msg_box = QMessageBox(
                    QMessageBox.Icon.Information,
                    tr("Failed to extract some items."),
                    trf("Failed to save {count} files!", count=len(loader.errors)),
                    flags=Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowStaysOnTopHint,
                )

                msg_box.setDetailedText("\n".join(f"{e.__class__.__name__}: {e}" for e in loader.errors))
                msg_box.exec()
            else:
                msg_box = QMessageBox(
                    QMessageBox.Icon.Information,
                    tr("Extraction successful."),
                    trf("Successfully saved {count} files to {path}", count=len(paths_to_write), path=folder_path),
                    flags=Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowStaysOnTopHint,
                )

                msg_box.setDetailedText("\n".join(str(p) for p in resource_save_paths.values()))
                msg_box.exec()
        elif isinstance(resource_widget, ResourceList) and is_capsule_file(resource_widget.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)):
            module_name = resource_widget.ui.sectionCombo.currentData(Qt.ItemDataRole.UserRole)
            self._save_capsule_from_tool_ui(module_name)

    def _extract_resource(
        self,
        resource: FileResource,
        save_path: Path,
        loader: AsyncLoader,
        seen_resources: dict[LocationResult, Path],
    ):
        loader._worker.progress.emit(  # noqa: SLF001  # pylint: disable=protected-access
            f"Processing resource: {resource.identifier()}",
            "update_maintask_text",
        )
        r_folderpath: Path = save_path.parent
        data: bytes = resource.data()
        if resource.restype() is ResourceType.MDX and self.ui.mdlDecompileCheckbox.isChecked():
            return
        if resource.restype() is ResourceType.TPC:
            tpc: TPC = read_tpc(data, txi_source=save_path)
            try:
                if self.ui.tpcTxiCheckbox.isChecked():
                    self._extract_txi(tpc, save_path.with_suffix(".txi"))
            except Exception as e:  # noqa: BLE001  # pylint: disable=broad-exception-caught
                loader.errors.append(e)
            try:
                if self.ui.tpcDecompileCheckbox.isChecked():
                    data = self._decompile_tpc(tpc)
            except Exception as e:  # noqa: BLE001  # pylint: disable=broad-exception-caught
                loader.errors.append(e)
        if resource.restype() is ResourceType.MDL:
            if self.ui.mdlTexturesCheckbox.isChecked():
                self._extract_mdl_textures(resource, r_folderpath, loader, data, seen_resources)  # pyright: ignore[reportArgumentType]
            if self.ui.mdlDecompileCheckbox.isChecked():
                data = bytes(self._decompile_mdl(resource, data))
        with save_path.open("wb") as file:
            file.write(data)

    def _extract_txi(self, tpc: TPC, filepath: Path):
        if not tpc.txi or not tpc.txi.strip():
            return
        with filepath.open("wb") as file:
            file.write(tpc.txi.encode("ascii", errors="ignore"))

    def _decompile_tpc(self, tpc: TPC) -> bytes:
        data = bytearray()
        write_tpc(tpc, data, ResourceType.TGA)
        return bytes(data)

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

        all_locresults: dict[str, dict[ResourceIdentifier, list[LocationResult]]] = defaultdict(lambda: defaultdict(list))
        seen_resources.setdefault(
            "all_locresults",
            all_locresults,
        )

        for item in textures_and_lightmaps:
            tex_type = "texture" if item in iterate_textures(data) else "lightmap"
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
        seen_resources[location] = savepath = subfolder / f"{resident.resname}.{file_format.extension}"

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
            try:
                file_res = FileResource(r_filepath.stem, ResourceType.from_extension(r_filepath.suffix), r_filepath.stat().st_size, 0x0, r_filepath)
                open_resource_editor(file_res, self.active, self)
            except (ValueError, OSError) as e:
                etype, msg = universal_simplify_exception(e)
                QMessageBox(QMessageBox.Icon.Critical, f"Failed to open file ({etype})", msg).exec()

    # endregion
