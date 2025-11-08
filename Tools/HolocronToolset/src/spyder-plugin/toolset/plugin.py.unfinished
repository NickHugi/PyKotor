# Third-party imports
from __future__ import annotations

import json

from typing import TYPE_CHECKING, Any, ClassVar

import qtpy
from contextlib import suppress

from qtpy.QtCore import Signal, Slot  # pyright: ignore[reportPrivateImportUsage]
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QAction, QMessageBox

from spyder.api.plugin_registration.decorators import on_plugin_available
from spyder.api.plugins import Plugins, SpyderPluginV2
from spyder.api.translations import get_translation
from spyder.config.base import get_conf_path
from toolset.data.installation import HTInstallation
from toolset.gui.windows.main import ToolWindow

if TYPE_CHECKING:
    from qtpy.QtWidgets import QCheckBox, QComboBox, QFrame, QGroupBox, QHBoxLayout, QMenu, QMenuBar, QPushButton, QStatusBar, QTabWidget, QWidget
    from typing_extensions import Self

    from toolset.gui.widgets.main_widgets import ResourceList, TextureList

_ = get_translation("spyder_holocron_toolset.spyder")

class HolocronToolset(SpyderPluginV2):
    """Holocron Toolset plugin for Spyder."""

    NAME: str = "holocron_toolset"
    REQUIRES: ClassVar[list[str]] = [Plugins.Toolbar, Plugins.StatusBar, Plugins.Preferences]
    OPTIONAL: ClassVar[list[str]] = []
    CONTAINER_CLASS: ClassVar[type[HolocronToolsetContainer]] = HolocronToolsetContainer
    CONF_SECTION: str = NAME
    CONF_FILE: str = "holocron_toolset.json"

    # Signals
    sig_installation_changed = Signal(HTInstallation)

    def __init__(self, parent: QWidget, configuration: dict | None = None):
        super().__init__(parent, configuration)
        self.current_installation: HTInstallation | None = None
        self.installations: list[HTInstallation] = []

    def _setup_plugin(self):
        """Setup the plugin with modular components."""
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup the user interface components."""
        container = self.get_container()
        self.integrate_menubar(container)
        self.reposition_widgets(container)
        # Initialize the tool window for plugin mode
        self.tool_window = ToolWindow(plugin_mode=True)
        container.add_widget(self.tool_window)
        # Setup additional UI components specific to Spyder integration
        self.setup_spyder_ui(container)

    def _connect_signals(self):
        """Connect signals for inter-component communication."""
        self.tool_window.installationChanged.connect(self.on_installation_changed)
        self.tool_window.installationsUpdated.connect(self.on_installations_updated)
        # Additional signal connections for Spyder integration
        self.sig_installation_changed.connect(self.update_status_bar)
        self.sig_installation_changed.connect(self.update_toolbar)

    def setup_spyder_ui(self, container: HolocronToolsetContainer):
        """Setup additional UI components specific to Spyder integration."""
        # Example: Add a custom toolbar or status bar widget
        toolbar: SpyderPluginV2 = self.get_plugin(Plugins.Toolbar)
        if toolbar:
            toolbar.add_application_toolbar(container.holocron_toolbar)
        statusbar = self.get_plugin(Plugins.StatusBar)
        if statusbar:
            statusbar.add_status_widget(self.holocron_status)

    def _disassemble_tool_window(self):

        # Import the appropriate Ui_MainWindow based on the Qt bindings
        from toolset.uic.qtpy.windows.main import Ui_MainWindow
        orig_ui = Ui_MainWindow()
        orig_ui.setupUi(self)

        # Define all widgets in the local scope
        central_widget: QWidget = orig_ui.centralwidget
        central_widget_parent: Self = self
        assert central_widget.parent() == central_widget_parent

        menubar: QMenuBar = orig_ui.menubar
        menubar_parent: Self = self
        assert menubar.parent() == menubar_parent

        statusbar: QStatusBar = orig_ui.statusbar
        statusbar_parent: Self = self
        assert statusbar.parent() == statusbar_parent

        main_horiz_layout: QHBoxLayout = orig_ui.horizontalLayout
        main_horiz_layout_parent: QWidget = central_widget
        assert main_horiz_layout.parent() == main_horiz_layout_parent

        game_combo: QComboBox = orig_ui.gameCombo
        game_combo_parent: QWidget = central_widget
        assert game_combo.parent() == game_combo_parent

        outer_tab_widget: QTabWidget = orig_ui.outerTabWidget
        outer_tab_widget_parent: QWidget = central_widget
        assert outer_tab_widget.parent() == outer_tab_widget_parent

        resource_list_tab: QWidget = orig_ui.resourceListTab
        resource_list_tab_parent: QWidget = outer_tab_widget
        assert resource_list_tab.parent() == resource_list_tab_parent

        resource_tabs: QTabWidget = orig_ui.resourceTabs
        resource_tabs_parent: QWidget = resource_list_tab
        assert resource_tabs.parent() == resource_tabs_parent

        core_tab: QWidget = orig_ui.coreTab
        core_tab_parent: QWidget = resource_tabs
        assert core_tab.parent() == core_tab_parent

        core_widget: ResourceList = orig_ui.coreWidget
        core_widget_parent: QWidget = core_tab
        assert core_widget.parent() == core_widget_parent

        saves_tab: QWidget = orig_ui.savesTab
        saves_tab_parent: QTabWidget = resource_tabs
        assert saves_tab.parent() == saves_tab_parent

        saves_widget: ResourceList = orig_ui.savesWidget
        saves_widget_parent: QWidget = saves_tab
        assert saves_widget.parent() == saves_widget_parent

        modules_tab: QWidget = orig_ui.modulesTab
        modules_tab_parent: QTabWidget = resource_tabs
        assert modules_tab.parent() == modules_tab_parent

        special_action_button: QPushButton = orig_ui.specialActionButton
        special_action_button_parent: QWidget = modules_tab
        assert special_action_button.parent() == special_action_button_parent

        modules_widget: ResourceList = orig_ui.modulesWidget
        modules_widget_parent: QWidget = modules_tab
        assert modules_widget.parent() == modules_widget_parent

        override_tab: QWidget = orig_ui.overrideTab
        override_tab_parent: QWidget = resource_tabs
        assert override_tab.parent() == override_tab_parent

        override_widget: ResourceList = orig_ui.overrideWidget
        override_widget_parent: QWidget = override_tab
        assert override_widget.parent() == override_widget_parent

        textures_tab: QWidget = orig_ui.texturesTab
        textures_tab_parent: QWidget = resource_tabs
        assert textures_tab.parent() == textures_tab_parent

        textures_widget: TextureList = orig_ui.texturesWidget
        textures_widget_parent: QWidget = textures_tab
        assert textures_widget.parent() == textures_widget_parent

        sidebar: QFrame = orig_ui.sidebar
        sidebar_parent: QWidget = central_widget
        assert sidebar.parent() == sidebar_parent

        open_button: QPushButton = orig_ui.openButton
        open_button_parent: QWidget = sidebar
        assert open_button.parent() == open_button_parent

        extract_button: QPushButton = orig_ui.extractButton
        extract_button_parent: QFrame = sidebar
        assert extract_button.parent() == extract_button_parent

        tpc_group: QGroupBox = orig_ui.tpcGroup_2
        tpc_group_parent: QFrame = sidebar
        assert tpc_group.parent() == tpc_group_parent

        tpc_decompile_checkbox: QCheckBox = orig_ui.tpcDecompileCheckbox
        tpc_decompile_checkbox_parent: QGroupBox = tpc_group
        assert tpc_decompile_checkbox.parent() == tpc_decompile_checkbox_parent

        tpc_txi_checkbox: QCheckBox = orig_ui.tpcTxiCheckbox
        tpc_txi_checkbox_parent: QGroupBox = tpc_group
        assert tpc_txi_checkbox.parent() == tpc_txi_checkbox_parent

        mdl_group: QGroupBox = orig_ui.mdlGroup_2
        mdl_group_parent: QFrame = sidebar
        assert mdl_group.parent() == mdl_group_parent

        mdl_decompile_checkbox: QCheckBox = orig_ui.mdlDecompileCheckbox
        mdl_decompile_checkbox_parent: QGroupBox = mdl_group
        assert mdl_decompile_checkbox.parent() == mdl_decompile_checkbox_parent

        mdl_textures_checkbox: QCheckBox = orig_ui.mdlTexturesCheckbox
        mdl_textures_checkbox_parent: QGroupBox = mdl_group
        assert mdl_textures_checkbox.parent() == mdl_textures_checkbox_parent

        menu_file: QMenu = orig_ui.menuFile
        menu_file_parent: QMenuBar = menubar
        assert menu_file.parent() == menu_file_parent

        menu_new: QMenu = orig_ui.menuNew
        menu_new_parent: QMenu = menu_file
        assert menu_new.parent() == menu_new_parent

        menu_recent_files: QMenu = orig_ui.menu_recent_files
        menu_recent_files_parent: QMenu = menu_file
        assert menu_recent_files.parent() == menu_recent_files_parent

        menu_edit: QMenu = orig_ui.menuEdit
        menu_edit_parent: QMenuBar = menubar
        assert menu_edit.parent() == menu_edit_parent

        menu_theme: QMenu = orig_ui.menuTheme
        menu_theme_parent: QMenuBar = menubar
        assert menu_theme.parent() == menu_theme_parent

        menu_tools: QMenu = orig_ui.menuTools
        menu_tools_parent: QMenuBar = menubar
        assert menu_tools.parent() == menu_tools_parent

        menu_help: QMenu = orig_ui.menuHelp
        menu_help_parent: QMenuBar = menubar
        assert menu_help.parent() == menu_help_parent

        menu_discord: QMenu = orig_ui.menuDiscord
        menu_discord_parent: QMenu = menu_help
        assert menu_discord.parent() == menu_discord_parent

        # Now we start disassembling, starting from the innermost widgets
        # Remove widgets from their parents
        core_widget.setParent(None)
        saves_widget.setParent(None)
        modules_widget.setParent(None)
        override_widget.setParent(None)
        textures_widget.setParent(None)

        special_action_button.setParent(None)

        tpc_decompile_checkbox.setParent(None)
        tpc_txi_checkbox.setParent(None)
        mdl_decompile_checkbox.setParent(None)
        mdl_textures_checkbox.setParent(None)

        # Remove tabs from resource_tabs
        resource_tabs.clear()

        # Remove widgets from sidebar
        open_button.setParent(None)
        extract_button.setParent(None)
        tpc_group.setParent(None)
        mdl_group.setParent(None)

        # Remove tabs from outer_tab_widget
        outer_tab_widget.clear()

        # Remove widgets from central_widget
        game_combo.setParent(None)
        outer_tab_widget.setParent(None)
        sidebar.setParent(None)

        # Remove central_widget from main window
        self.setCentralWidget(None)

        # Remove menus from menubar
        menubar.clear()

        # Remove menubar and statusbar from main window
        self.setMenuBar(None)
        self.setStatusBar(None)

        # Store disassembled widgets for later use
        self.disassembled_widgets: dict[str, QWidget] = {
            "central_widget": central_widget,
            "menubar": menubar,
            "statusbar": statusbar,
            "game_combo": game_combo,
            "outer_tab_widget": outer_tab_widget,
            "resource_tabs": resource_tabs,
            "core_widget": core_widget,
            "saves_widget": saves_widget,
            "modules_widget": modules_widget,
            "override_widget": override_widget,
            "textures_widget": textures_widget,
            "special_action_button": special_action_button,
            "sidebar": sidebar,
            "open_button": open_button,
            "extract_button": extract_button,
            "tpc_group": tpc_group,
            "tpc_decompile_checkbox": tpc_decompile_checkbox,
            "tpc_txi_checkbox": tpc_txi_checkbox,
            "mdl_group": mdl_group,
            "mdl_decompile_checkbox": mdl_decompile_checkbox,
            "mdl_textures_checkbox": mdl_textures_checkbox,
        }

        self.disassembled_menus: dict[str, QMenu] = {
            "file": menu_file,
            "new": menu_new,
            "recent_files": menu_recent_files,
            "edit": menu_edit,
            "theme": menu_theme,
            "tools": menu_tools,
            "help": menu_help,
            "discord": menu_discord,
        }

        # The widgets are now disassembled and ready to be reassembled into the plugin structure
    # --- SpyderPluginV2 API
    # ------------------------------------------------------------------------
    def get_name(self):
        return _("Holocron Toolset")

    def get_description(self):
        return _("KotOR modding toolset")

    def get_icon(self):
        return QIcon(":/images/icons/sith.png")

    def on_initialize(self):
        """Initialize the Holocron Toolset plugin."""
        # Step 1: Get the container
        container = self.get_container()

        # Step 2: Integrate the menu bar
        self.integrate_menubar(container)

        # Step 3: Reposition widgets if necessary
        self.reposition_widgets(container)

        # Step 4: Initialize the ToolWindow in plugin mode
        self.tool_window = ToolWindow(plugin_mode=True)
        container.add_widget(self.tool_window)

        # Step 5: Connect signals
        self.tool_window.installationChanged.connect(self.on_installation_changed)
        self.tool_window.installationsUpdated.connect(self.on_installations_updated)

        # Step 6: Load installations
        self.load_installations()

        # Step 7: Set up the plugin's UI
        self._setup_plugin()

        print("HolocronToolset initialized!")

    @on_plugin_available(plugin=Plugins.Toolbar)
    def on_toolbar_available(self):
        container = self.get_container()
        toolbar = self.get_plugin(Plugins.Toolbar)
        toolbar.add_application_toolbar(container.holocron_toolbar)

    @on_plugin_available(plugin=Plugins.StatusBar)
    def on_statusbar_available(self):
        statusbar = self.get_plugin(Plugins.StatusBar)
        if statusbar:
            statusbar.add_status_widget(self.holocron_status)

    @on_plugin_available(plugin=Plugins.Preferences)
    def on_preferences_available(self):
        preferences = self.get_plugin(Plugins.Preferences)
        preferences.register_plugin_preferences(self)

    def integrate_menubar(self, container):
        # Assuming `self.main` has access to Spyder's main window
        main_window = self.main
        file_menu = main_window.get_menu("file")

        # Add custom actions
        debug_action = QAction("Debug Reload", container)
        debug_action.triggered.connect(self.debug_reload_pymodules)
        file_menu.addAction(debug_action)

    def debug_reload_pymodules(self):
        # Placeholder for the actual debug reload logic
        print("Debug reload of Python modules triggered.")
        # Example: Move a widget to a new location in the Spyder interface
        # self.ui.someWidget.setParent(container.someNewContainer)
        # container.someNewContainer.layout().addWidget(self.ui.someWidget)
        conf_file = get_conf_path(self.CONF_FILE)
        with suppress(FileNotFoundError):
            with open(conf_file) as f:
                data = json.load(f)
                installations = data.get("installations", [])
                for installation in installations:
                    self.tool_window.add_installation(
                        installation["name"],
                        installation["path"],
                        installation["tsl"]
                    )
        except FileNotFoundError:
            pass

    def save_installations(self):
        conf_file = get_conf_path(self.CONF_FILE)
        data: dict[str, list[dict[str, Any]]] = {
            "installations": [
                {
                    "name": name,
                    "path": inst.path(),
                    "tsl": inst.tsl
                }
                for name, inst in self.tool_window.installations.items()
            ]
        }
        with open(conf_file, "w") as f:
            json.dump(data, f)

    def check_compatibility(self):
        valid = True
        message = ""
        return valid, message

    def on_close(self, cancellable=True):
        return True

    @property
    def holocron_status(self):
        container = self.get_container()
        return container.holocron_status

    # --- Public API
    # ------------------------------------------------------------------------
    @Slot(HTInstallation)
    def on_installation_changed(self, installation: HTInstallation):
        self.current_installation = installation
        self.sig_installation_changed.emit(installation)
        self.holocron_status.set_value(f"Active: {installation.name}")

    @Slot(list)
    def on_installations_updated(self, installations):
        self.save_installations()
        container = self.get_container()
        container.holocron_toolbar.update_installations(installations)

    def get_installations(self):
        return self.tool_window.get_installations()

    def show_about_dialog(self):
        QMessageBox.about(self.main, _("About Holocron Toolset"),
                          _("Holocron Toolset is a KotOR modding toolset for Spyder."))

    # --- Preferences API
    # ------------------------------------------------------------------------
    def apply_conf(self):
        self.load_installations()
        container = self.get_container()
        container.holocron_toolbar.update_installations(self.tool_window.get_installations())

    def reset_conf(self):
        for name in self.tool_window.get_installations():
            self.tool_window.remove_installation(name)
        self.save_installations()
        container = self.get_container()
        container.holocron_toolbar.update_installations([])

    def get_config_page(self):
        return HolocronToolsetConfigPage(self, self.name)

    # --- Preferences API
    # ------------------------------------------------------------------------
    def apply_conf(self):
        self.load_installations()
        container = self.get_container()
        container.holocron_toolbar.update_installations(self.installations)

    def reset_conf(self):
        self.installations = []
        self.save_installations()
        container = self.get_container()
        container.holocron_toolbar.update_installations(self.installations)

    def get_config_page(self):
        return HolocronToolsetConfigPage(self, self.name)
    @on_plugin_available(plugin=Plugins.Toolbar)
    def on_toolbar_available(self):
        container = self.get_container()
        toolbar = self.get_plugin(Plugins.Toolbar)
        toolbar.add_application_toolbar(container.holocron_toolbar)

    @on_plugin_available(plugin=Plugins.StatusBar)
    def on_statusbar_available(self):
        statusbar = self.get_plugin(Plugins.StatusBar)
        if statusbar:
            statusbar.add_status_widget(self.holocron_status)

    @on_plugin_available(plugin=Plugins.Preferences)
    def on_preferences_available(self):
        preferences = self.get_plugin(Plugins.Preferences)
        preferences.register_plugin_preferences(self)

    def integrate_menubar(self, container):
        # Assuming `self.main` has access to Spyder's main window
        main_window = self.main
        file_menu = main_window.get_menu("file")

        # Add custom actions
        debug_action = QAction("Debug Reload", container)
        debug_action.triggered.connect(self.debug_reload_pymodules)
        file_menu.addAction(debug_action)

    def debug_reload_pymodules(self):
        # Placeholder for the actual debug reload logic
        print("Debug reload of Python modules triggered.")
        # Example: Move a widget to a new location in the Spyder interface
        # self.ui.someWidget.setParent(container.someNewContainer)
        # container.someNewContainer.layout().addWidget(self.ui.someWidget)
        conf_file = get_conf_path(self.CONF_FILE)
        with suppress(FileNotFoundError):
            with open(conf_file) as f:
                data = json.load(f)
                installations = data.get("installations", [])
                for installation in installations:
                    self.tool_window.add_installation(
                        installation["name"],
                        installation["path"],
                        installation["tsl"]
                    )
        except FileNotFoundError:
            pass

    def save_installations(self):
        conf_file = get_conf_path(self.CONF_FILE)
        data: dict[str, list[dict[str, Any]]] = {
            "installations": [
                {
                    "name": name,
                    "path": inst.path(),
                    "tsl": inst.tsl
                }
                for name, inst in self.tool_window.installations.items()
            ]
        }
        with open(conf_file, "w") as f:
            json.dump(data, f)

    def check_compatibility(self):
        valid = True
        message = ""
        return valid, message

    def on_close(self, cancellable=True):
        return True

    @property
    def holocron_status(self):
        container = self.get_container()
        return container.holocron_status

    # --- Public API
    # ------------------------------------------------------------------------
    @Slot(HTInstallation)
    def on_installation_changed(self, installation: HTInstallation):
        self.current_installation = installation
        self.sig_installation_changed.emit(installation)
        self.holocron_status.set_value(f"Active: {installation.name}")

    @Slot(list)
    def on_installations_updated(self, installations):
        self.save_installations()
        container = self.get_container()
        container.holocron_toolbar.update_installations(installations)

    def get_installations(self):
        return self.tool_window.get_installations()

    def show_about_dialog(self):
        QMessageBox.about(self.main, _("About Holocron Toolset"),
                          _("Holocron Toolset is a KotOR modding toolset for Spyder."))

    # --- Preferences API
    # ------------------------------------------------------------------------
    def apply_conf(self):
        self.load_installations()
        container = self.get_container()
        container.holocron_toolbar.update_installations(self.tool_window.get_installations())

    def reset_conf(self):
        for name in self.tool_window.get_installations():
            self.tool_window.remove_installation(name)
        self.save_installations()
        container = self.get_container()
        container.holocron_toolbar.update_installations([])

    def get_config_page(self):
        return HolocronToolsetConfigPage(self, self.name)

    # --- Preferences API
    # ------------------------------------------------------------------------
    def apply_conf(self):
        self.load_installations()
        container = self.get_container()
        container.holocron_toolbar.update_installations(self.installations)

    def reset_conf(self):
        self.installations = []
        self.save_installations()
        container = self.get_container()
        container.holocron_toolbar.update_installations(self.installations)

    def get_config_page(self):
        return HolocronToolsetConfigPage(self, self.name)
