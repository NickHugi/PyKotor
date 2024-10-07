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
from typing import TYPE_CHECKING, Any, cast

import qtpy

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy import QtCore
from qtpy.QtCore import (
    QCoreApplication,
    QThread,
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
    Slot,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QIcon, QPixmap, QStandardItem
from qtpy.QtWidgets import (
    QAction,
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

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
from pykotor.tools import module
from pykotor.tools.misc import is_any_erf_type_file, is_bif_file, is_capsule_file, is_erf_file, is_mod_file, is_rim_file
from pykotor.tools.model import iterate_lightmaps, iterate_textures
from pykotor.tools.path import CaseAwarePath
from toolset.data.installation import HTInstallation
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
from toolset.gui.theme_manager import ThemeManager
from toolset.gui.widgets.main_widgets import ResourceList
from toolset.gui.widgets.settings.misc import GlobalSettings
from toolset.gui.windows.help import HelpWindow
from toolset.gui.windows.indoor_builder import IndoorMapBuilder
from toolset.gui.windows.module_designer import ModuleDesigner
from toolset.gui.windows.update_manager import UpdateManager
from toolset.utils.misc import openLink
from toolset.utils.window import add_window, open_resource_editor
from ui import stylesheet_resources  # noqa: F401  # pylint: disable=unused-import
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
    from qtpy.QtGui import QCloseEvent, QKeyEvent, QMouseEvent, QPalette
    from qtpy.QtWidgets import QStyle, QWidget
    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from pykotor.extract.file import LocationResult, ResourceResult
    from pykotor.resource.formats.mdl.mdl_data import MDL
    from pykotor.resource.formats.tpc import TPC
    from pykotor.resource.type import SOURCE_TYPES
    from toolset.gui.widgets.main_widgets import TextureList


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

        self.settings: GlobalSettings = GlobalSettings()
        self.update_manager = UpdateManager(silent=True)

        # Theme setup
        q_style: QStyle | None = self.style()
        assert q_style is not None
        self.original_style: str = q_style.objectName()
        self.original_palette: QPalette = self.palette()
        self.theme_manager = ThemeManager(self.original_style)
        self.theme_manager.change_theme(self.settings.selectedTheme)  # Ensure it comes to the front

        self.previous_game_combo_index: int = 0
        self._initUi()
        self._setup_signals()
        self.setWindowTitle(f"Holocron Toolset ({qtpy.API_NAME})")

        # Finalize the init
        self.reload_settings()
        self.unset_installation()

    def handle_change(self, path: str):
        if self.active is None:
            return

        modified_path = os.path.normpath(path)
        if os.path.isdir(modified_path):  # noqa: PTH112
            return

        now = datetime.now(tz=timezone.utc).astimezone()
        if now - self.last_modified < timedelta(seconds=1):
            return
        self.last_modified = now

        module_path = os.path.normpath(self.active.module_path())
        override_path = os.path.normpath(self.active.override_path())

        if module_path.lower() in modified_path.lower():
            self.sig_module_files_updated.emit(modified_path, "modified")
        elif override_path.lower() in modified_path.lower():
            self.sig_override_files_update.emit(modified_path, "modified")

    def _initUi(self):
        """Initialize Holocron Toolset main window UI."""
        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.windows.main import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.windows.main import Ui_MainWindow
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.windows.main import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.windows.main import Ui_MainWindow
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
            RobustLogger().warning(f"Failed to load HT main window icon from {self.MAIN_ICON_PATH}")
        self.setup_modules_tab()

    def setup_modules_tab(self):
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
        # Remove from original layouts
        modules_resource_list.horizontalLayout_2.removeWidget(modules_section_combo)  # type: ignore[arg-type]
        modules_resource_list.horizontalLayout_2.removeWidget(refresh_button)  # type: ignore[arg-type]
        modules_resource_list.verticalLayout.removeItem(modules_resource_list.horizontalLayout_2)  # type: ignore[arg-type]

        # Set size policies
        modules_section_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)  # type: ignore[arg-type]
        modules_section_combo.setMinimumWidth(250)
        refresh_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)  # type: ignore[arg-type]
        designer_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)  # type: ignore[arg-type]

        # Create a new layout to stack Designer and Refresh buttons
        stack_button_layout = QVBoxLayout()
        stack_button_layout.setSpacing(1)
        stack_button_layout.addWidget(refresh_button)  # type: ignore[arg-type]
        stack_button_layout.addWidget(designer_button)  # type: ignore[arg-type]

        # Create a new horizontal layout to place the combobox and buttons
        top_layout = QHBoxLayout()
        top_layout.addWidget(modules_section_combo)  # type: ignore[arg-type]
        top_layout.addLayout(stack_button_layout)

        # Insert the new top layout into the vertical layout
        self.ui.verticalLayoutModulesTab.insertLayout(0, top_layout)  # type: ignore[attributeAccessIssue]

        # Adjust the vertical layout to accommodate the combobox height change
        modules_resource_list.verticalLayout.addWidget(modules_resource_list.resourceTree)  # type: ignore[arg-type]
        modules_section_combo.setMaxVisibleItems(18)

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
        self.sig_installation_changed.connect(self.ui.modulesWidget.setInstallation)

        self.ui.savesWidget.sig_section_changed.connect(self.on_savepath_changed)
        self.ui.savesWidget.sig_request_reload.connect(self.on_save_reload)
        self.ui.savesWidget.sig_request_refresh.connect(self.on_save_refresh)
        self.ui.savesWidget.sig_request_extract_resource.connect(self.on_extract_resources)
        self.ui.savesWidget.sig_request_open_resource.connect(self.on_open_resources)
        self.sig_installation_changed.connect(self.ui.savesWidget.setInstallation)
        self.ui.resourceTabs.currentChanged.connect(self.on_tab_changed)

        def open_module_designer() -> ModuleDesigner | None:
            """Open the module designer."""
            assert self.active is not None

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
                RobustLogger().debug(f"Failed to load Module Designer window icon from {icon_path}")
            add_window(designer_ui, show=False)
            return designer_ui

        self.ui.specialActionButton.clicked.connect(lambda *args: open_module_designer() and None or None)

        self.ui.overrideWidget.sig_section_changed.connect(self.on_override_changed)
        self.ui.overrideWidget.sig_request_reload.connect(self.on_override_reload)
        self.ui.overrideWidget.sig_request_refresh.connect(self.on_override_refresh)
        self.ui.overrideWidget.sig_request_extract_resource.connect(self.on_extract_resources)
        self.ui.overrideWidget.sig_request_open_resource.connect(self.on_open_resources)
        self.sig_installation_changed.connect(self.ui.overrideWidget.setInstallation)

        self.ui.texturesWidget.sig_section_changed.connect(self.on_textures_changed)
        self.ui.texturesWidget.sig_request_open_resource.connect(self.on_open_resources)
        self.sig_installation_changed.connect(self.ui.texturesWidget.setInstallation)

        self.ui.extractButton.clicked.connect(
            lambda: self.on_extract_resources(
                self.get_active_resource_widget().selected_resources(),
                resource_widget=self.get_active_resource_widget(),
            ),
        )
        self.ui.openButton.clicked.connect(self.get_active_resource_widget().on_resource_double_clicked)

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
        self.ui.actionHelpUpdates.triggered.connect(self.update_manager.check_for_updates)
        self.ui.actionHelpAbout.triggered.connect(self.open_about_dialog)
        self.ui.actionDiscordDeadlyStream.triggered.connect(lambda: openLink("https://discord.com/invite/bRWyshn"))
        self.ui.actionDiscordKotOR.triggered.connect(lambda: openLink("http://discord.gg/kotor"))
        self.ui.actionDiscordHolocronToolset.triggered.connect(lambda: openLink("https://discord.gg/3ME278a9tQ"))

        self.ui.menuRecentFiles.aboutToShow.connect(self.populate_recent_files_menu)

    def on_open_resources(
        self,
        resources: list[FileResource],
        use_specialized_editor: bool | None = None,
        resource_widget: ResourceList | TextureList | None = None,
    ):
        assert self.active is not None
        for resource in resources:
            _filepath, _editor = open_resource_editor(resource.filepath(), resource.resname(), resource.restype(), resource.data(reload=True),
                                                    self.active, self, gff_specialized=use_specialized_editor)
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
        _filepath, _editor = open_resource_editor(erf_filepath, res_ident.resname, res_ident.restype, BinaryReader.load_file(erf_filepath),
                                                self.active, self, gff_specialized=use_specialized_editor)

    @Slot()
    def populate_recent_files_menu(self):
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
        obj_ret: QObject | None = self.sender()
        if not isinstance(obj_ret, QAction):
            return
        action: QAction = obj_ret

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

        open_resource_editor(file, resource.resname(), resource.restype(), resource.data(), self.active, self)


    # region Signal callbacks
    @Slot()
    def on_core_refresh(self):
        self.refresh_core_list(reload=True)

    @Slot(str)
    def on_module_changed(self, new_module_file: str):
        self.on_module_reload(new_module_file)

    @Slot(bool)
    def on_module_refresh(self, reload: bool = True):  # noqa: FBT001, FBT002
        self.refresh_module_list(reload=reload)

    @Slot(str)
    def on_module_reload(self, module_file: str):
        assert self.active is not None, "No active installation selected"
        if not module_file or not module_file.strip():
            return
        resources: list[FileResource] = self.active.module_resources(module_file)

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
        assert self.active is not None

        # Clear the entire model before loading new save resources
        self.ui.savesWidget.modules_model.invisibleRootItem().removeRows(0, self.ui.savesWidget.modules_model.rowCount())  # pyright: ignore[reportOptionalMemberAccess]
        new_save_dir_path = CaseAwarePath(new_save_dir)

        if new_save_dir_path not in self.active.saves:
            self.active.load_saves()
        if new_save_dir_path not in self.active.saves:
            return

        for save_path, resource_list in self.active.saves[new_save_dir_path].items():
            # Create a new parent item for the save_path
            save_path_item = QStandardItem(str(save_path.relative_to(save_path.parent.parent)))

            self.ui.savesWidget.modules_model.invisibleRootItem().appendRow(save_path_item)  # pyright: ignore[reportOptionalMemberAccess]

            # Dictionary to keep track of category items under this save_path_item
            category_items_under_save_path: dict[str, QStandardItem] = {}

            for resource in resource_list:
                restype: ResourceType = resource.restype()

                category: str = restype.category

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

                # Check if resource is already listed under this category
                from toolset.gui.widgets.main_widgets import ResourceStandardItem

                found_resource = False
                for i in range(category_item.rowCount()):
                    item = category_item.child(i)
                    if item is not None and isinstance(item, ResourceStandardItem) and item.resource == resource:
                        # Update the resource reference if necessary
                        item.resource = resource
                        found_resource = True
                        break

                if not found_resource:
                    # Add new resource under the category
                    item1 = ResourceStandardItem(resource.resname(), resource=resource)
                    item2 = QStandardItem(restype.extension.upper())
                    category_item.appendRow([item1, item2])

    def on_save_reload(self, save_dir: str):
        self.on_savepath_changed(save_dir)

    def on_save_refresh(self):
        self.refresh_saves_list()

    def on_override_file_updated(self, changed_file: str, event_type: str):
        if event_type == "deleted":
            self.on_override_refresh()
        else:
            self.on_override_reload(changed_file)

    def on_override_changed(self, new_directory: str):
        assert self.active is not None
        self.ui.overrideWidget.set_resources(self.active.override_resources(new_directory))

    def on_override_reload(self, file_or_folder: str):
        assert self.active is not None
        override_path = self.active.override_path()

        file_or_folder_path = override_path.joinpath(file_or_folder)

        if not file_or_folder_path.is_relative_to(self.active.override_path()):
            raise ValueError(f"'{file_or_folder_path}' is not relative to the override folder, cannot reload")
        if file_or_folder_path.is_file():
            rel_folderpath = file_or_folder_path.parent.relative_to(self.active.override_path())

            self.active.reload_override_file(file_or_folder_path)
        else:
            rel_folderpath = file_or_folder_path.relative_to(self.active.override_path())

            self.active.load_override(str(rel_folderpath))
        self.ui.overrideWidget.set_resources(self.active.override_resources(str(rel_folderpath) if rel_folderpath.name else None))

    def on_override_refresh(self):
        assert self.active is not None
        self.refresh_override_list(reload=True)

    def on_textures_changed(self, texturepackName: str):
        assert self.active is not None
        self.ui.texturesWidget.set_resources(self.active.texturepack_resources(texturepackName))

    @Slot(int)
    def change_active_installation(self, index: int):  # noqa: PLR0915, C901, PLR0912
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
            QMessageBox(QMessageBox.Icon.Information, "dialog.tlk not found", f"Could not open the TalkTable editor, dialog.tlk not found at the expected location<br><br>{filepath}.").exec_()
            return
        data: bytes = BinaryReader.load_file(filepath)
        open_resource_editor(filepath, "dialog", ResourceType.TLK, data, self.active, self)

    @Slot()
    def open_active_journal(self):
        if self.active is None:
            QMessageBox(QMessageBox.Icon.Information, "No installation loaded.", "Load an installation before opening the Journal Editor.").exec_()
            return
        jrl_ident: ResourceIdentifier = ResourceIdentifier("global", ResourceType.JRL)
        journal_resources: dict[ResourceIdentifier, list[LocationResult]] = self.active.locations(
            [jrl_ident],
            [SearchLocation.OVERRIDE, SearchLocation.CHITIN],
        )
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
        if not filename:
            return
        erf_filepath: CaseAwarePath = self.active.module_path() / filename
        if not erf_filepath.is_file():
            RobustLogger().warning(f"Not loading '{erf_filepath}'. File does not exist")
            return
        res_ident: ResourceIdentifier = ResourceIdentifier.from_path(erf_filepath)
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
        if tree == self.ui.coreWidget:
            self.ui.resourceTabs.setCurrentWidget(self.ui.coreTab)
            self.ui.coreWidget.set_resource_selection(resource)

        elif tree == self.ui.modulesWidget:
            self.ui.resourceTabs.setCurrentWidget(self.ui.modulesTab)
            filename = resource.filepath().name
            self.change_module(filename)
            self.ui.modulesWidget.set_resource_selection(resource)

        elif tree == self.ui.overrideWidget:
            self._select_override_resource(resource)
        elif tree == self.ui.savesWidget:
            self.ui.resourceTabs.setCurrentWidget(self.ui.savesTab)
            filename = resource.filepath().name
            self.on_save_reload(filename)

    def _select_override_resource(self, resource: FileResource):
        assert self.active is not None
        self.ui.resourceTabs.setCurrentWidget(self.ui.overrideTab)
        self.ui.overrideWidget.set_resource_selection(resource)
        subfolder: str = "."
        for folder_name in self.active.override_list():
            folder_path: CaseAwarePath = self.active.override_path() / folder_name
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
        profiler = None
        if self.settings.profileToolset and cProfile is not None:
            profiler = cProfile.Profile()
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
        if self.active is None:
            return
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
        c_filepath: CaseAwarePath = self.active.module_path() / module_name
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
            f"Save extracted {capsule_type} '{c_filepath.stem}' as...",
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
            RobustLogger().exception("Error extracting capsule file '%s'", module_name)
            QMessageBox(QMessageBox.Icon.Critical, "Error saving capsule file", str(universal_simplify_exception(e))).exec_()

    def build_extract_save_paths(self, resources: list[FileResource]) -> tuple[Path, dict[FileResource, Path]] | tuple[None, None]:
        # TODO(th3w1zard1): currently doesn't handle same filenames existing for extra extracts e.g. tpcTxiCheckbox.isChecked() or mdlTexturesCheckbox.isChecked()
        paths_to_write: dict[FileResource, Path] = {}

        folder_path_str: str = QFileDialog.getExistingDirectory(self, "Extract to folder")
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
                loader.exec_()
            else:
                for resource, save_path in resource_save_paths.items():
                    self._extract_resource(resource, save_path, loader, seen_resources)

            # quick main thread/ui check.
            if QThread.currentThread() != cast(QApplication, QApplication.instance()).thread():
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
                    # save_path = save_path.with_suffix(".tga")  # already handled
            except Exception as e:  # noqa: BLE001  # pylint: disable=broad-exception-caught
                loader.errors.append(e)

        if resource.restype() is ResourceType.MDL:
            if self.ui.mdlTexturesCheckbox.isChecked():
                self._extract_mdl_textures(resource, r_folderpath, loader, data, seen_resources)

            if self.ui.mdlDecompileCheckbox.isChecked():
                data = self._decompile_mdl(resource, data)
                # save_path = save_path.with_suffix(".mdl.ascii")  # already handled

        with save_path.open("wb") as file:
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
            try:
                data = r_filepath.read_bytes()
                open_resource_editor(filepath, *ResourceIdentifier.from_path(r_filepath).validate().unpack(), data, self.active, self)
            except (ValueError, OSError) as e:
                etype, msg = universal_simplify_exception(e)
                QMessageBox(QMessageBox.Icon.Critical, f"Failed to open file ({etype})", msg).exec_()
    # endregion
