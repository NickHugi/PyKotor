from __future__ import annotations

from qtpy.QtCore import Signal, Slot
from qtpy.QtWidgets import QComboBox, QToolBar

from spyder.api.widgets.status import StatusBarWidget


class HolocronToolbar(QToolBar):
    """Toolbar for the Holocron Toolset."""
    installationChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Holocron Toolset")

        # Add installation selector
        self.installation_selector = QComboBox()
        self.installation_selector.addItem("Select Installation")
        self.addWidget(self.installation_selector)

        # Connect signals
        self.installation_selector.currentTextChanged.connect(self.on_installation_changed)

    def update_installations(self, installations):
        self.installation_selector.clear()
        self.installation_selector.addItem("Select Installation")
        for installation in installations:
            self.installation_selector.addItem(installation)

    @Slot(str)
    def on_installation_changed(self, installation_name):
        if installation_name != "Select Installation":
            self.installationChanged.emit(installation_name)

class HolocronStatus(StatusBarWidget):
    ID = "holocron_status"

    def __init__(self, parent):
        super().__init__(parent)
        self.value = "Holocron Toolset Ready"

    def get_tooltip(self):
        return "Holocron Toolset Status"

    def get_icon(self):
        return None

    def get_value(self):
        return self.value

    def set_value(self, value):
        self.value = value
        self.update_status()
