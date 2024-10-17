# Third-party imports
from __future__ import annotations

from qtpy.QtCore import Slot  # pyright: ignore[reportPrivateImportUsage]
from qtpy.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout

# Local imports
from plugin.spyder_holocron_toolset.spyder.widgets import HolocronStatus, HolocronToolbar

# Spyder imports
from spyder.api.translations import get_translation
from spyder.api.widgets.main_container import PluginMainContainer
from toolset.gui.windows.main import ToolWindow

_ = get_translation("spyder_holocron_toolset.spyder")

class HolocronToolsetContainer(PluginMainContainer):
    def __init__(self, name, plugin: HolocronToolsetPlugin, parent: QObject | None=None):
        super().__init__(name, plugin, parent)

        # Create widgets
        self.holocron_toolbar = HolocronToolbar(self)
        self.holocron_status = HolocronStatus(self)
        self.tool_window: ToolWindow = ToolWindow()

        # Create additional buttons
        self.refresh_button = QPushButton(_("Refresh"))
        self.about_button = QPushButton(_("About"))

        # Set up layout
        main_layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.about_button)

        main_layout.addWidget(self.holocron_toolbar)
        main_layout.addWidget(self.tool_window)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        # Connect signals
        self.refresh_button.clicked.connect(self.refresh_toolset)
        self.about_button.clicked.connect(self.plugin.show_about_dialog)
        self.holocron_toolbar.installationChanged.connect(self.on_installation_changed)

    # --- PluginMainContainer API
    # ------------------------------------------------------------------------
    def setup(self):
        # Set up any additional configuration here
        pass

    def update_actions(self):
        # Update actions if needed
        pass

    # --- Public API
    # ------------------------------------------------------------------------
    @Slot()
    def refresh_toolset(self):
        # Implement refresh functionality
        self.tool_window.refresh_core_list(reload=True)
        self.tool_window.refresh_module_list(reload=True)
        self.tool_window.refresh_override_list(reload=True)
        self.tool_window.refresh_texture_pack_list(reload=True)
        self.tool_window.refresh_saves_list(reload=True)

    @Slot(str)
    def on_installation_changed(
        self,
        installation_name: str,
    ):
        self.tool_window.change_active_installation(
            self.tool_window.ui.gameCombo.findText(installation_name)
        )

    def setup_toolbar(self, toolbar):
        """Set up toolbars specific to Holocron Toolset."""
        # Add toolbar setup logic here
        pass

    def setup_widgets(self):
        """Set up widgets specific to Holocron Toolset."""
        # Add widget setup logic here
        pass

    def open_resource(self, resource_type: str, resource_path: str):
        """Open a resource in the appropriate editor."""
        # Implement logic to open the resource
        pass

    def update_for_installation(self, installation):
        """Update UI based on the current installation."""
        # Implement logic to update the UI
        pass