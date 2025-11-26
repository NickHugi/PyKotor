"""Test Configuration Widget - Configures event parameters for dry-run testing of NSS scripts."""

from __future__ import annotations

from typing import Any

from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class TestConfigWidget(QWidget):
    """Widget for configuring test parameters before running a script test."""
    
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._entry_point: str = "main"  # "main" or "StartingConditional"
        self._event_number: int = 1001  # Default: HEARTBEAT
        self._test_params: dict[str, Any] = {}
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Entry point info
        self.entry_point_label = QLabel("Entry Point: main()", self)
        layout.addWidget(self.entry_point_label)
        
        # Event configuration group
        event_group = QGroupBox("Event Configuration", self)
        event_layout = QFormLayout(event_group)
        
        # Event number selector (for main() scripts)
        self.event_combo = QComboBox(self)
        self.event_combo.addItem("HEARTBEAT (1001)", 1001)
        self.event_combo.addItem("PERCEIVE (1002)", 1002)
        self.event_combo.addItem("END OF COMBAT (1003)", 1003)
        self.event_combo.addItem("ON DIALOGUE (1004)", 1004)
        self.event_combo.addItem("ATTACKED (1005)", 1005)
        self.event_combo.addItem("DAMAGED (1006)", 1006)
        self.event_combo.addItem("DEATH (1007)", 1007)
        self.event_combo.addItem("DISTURBED (1008)", 1008)
        self.event_combo.addItem("BLOCKED (1009)", 1009)
        self.event_combo.addItem("SPELL CAST AT (1010)", 1010)
        self.event_combo.addItem("DIALOGUE END (1011)", 1011)
        self.event_combo.addItem("Custom...", -1)
        self.event_combo.currentIndexChanged.connect(self._on_event_changed)
        event_layout.addRow("Event Type:", self.event_combo)
        
        # Custom event number (shown when "Custom..." is selected)
        self.custom_event_spin = QSpinBox(self)
        self.custom_event_spin.setRange(1001, 9999)
        self.custom_event_spin.setValue(1001)
        self.custom_event_spin.setEnabled(False)
        self.custom_event_spin.valueChanged.connect(self._update_event_number)
        event_layout.addRow("Custom Event Number:", self.custom_event_spin)
        
        layout.addWidget(event_group)
        
        # Mock values group
        mock_group = QGroupBox("Mock Engine Function Values", self)
        mock_layout = QFormLayout(mock_group)
        
        # GetLastAttacker() mock
        self.last_attacker_edit = QLineEdit(self)
        from toolset.gui.common.localization import translate as tr
        self.last_attacker_edit.setPlaceholderText(tr("OBJECT_INVALID (default: 0)"))
        self.last_attacker_edit.setText("0")
        mock_layout.addRow(tr("GetLastAttacker():"), self.last_attacker_edit)

        # GetLastPerceived() mock
        self.last_perceived_edit = QLineEdit(self)
        self.last_perceived_edit.setPlaceholderText(tr("OBJECT_INVALID (default: 0)"))
        self.last_perceived_edit.setText("0")
        mock_layout.addRow(tr("GetLastPerceived():"), self.last_perceived_edit)

        # GetEventCreator() mock
        self.event_creator_edit = QLineEdit(self)
        self.event_creator_edit.setPlaceholderText(tr("OBJECT_SELF (default: 1)"))
        self.event_creator_edit.setText("1")
        mock_layout.addRow(tr("GetEventCreator():"), self.event_creator_edit)

        # GetEventTarget() mock
        self.event_target_edit = QLineEdit(self)
        self.event_target_edit.setPlaceholderText(tr("OBJECT_SELF (default: 1)"))
        self.event_target_edit.setText("1")
        mock_layout.addRow(tr("GetEventTarget():"), self.event_target_edit)
        
        layout.addWidget(mock_group)
        
        layout.addStretch()
    
    def _on_event_changed(self, index: int):
        """Handle event combo box change."""
        custom_enabled = self.event_combo.itemData(index) == -1
        self.custom_event_spin.setEnabled(custom_enabled)
        if not custom_enabled:
            self._event_number = self.event_combo.itemData(index)
        else:
            self._event_number = self.custom_event_spin.value()
    
    def _update_event_number(self, value: int):
        """Update event number from custom spinbox."""
        if self.event_combo.currentData() == -1:
            self._event_number = value
    
    def set_entry_point(self, entry_point: str):
        """Set the detected entry point type.
        
        Args:
        ----
            entry_point: str: "main" or "StartingConditional"
        """
        self._entry_point = entry_point
        if entry_point == "StartingConditional":
            from toolset.gui.common.localization import translate as tr
            self.entry_point_label.setText(tr("Entry Point: StartingConditional()"))
            # Hide event configuration for StartingConditional
            self.event_combo.setEnabled(False)
            self.custom_event_spin.setEnabled(False)
        else:
            self.entry_point_label.setText(tr("Entry Point: main()"))
            self.event_combo.setEnabled(True)
    
    def get_test_config(self) -> dict[str, Any]:
        """Get the test configuration.
        
        Returns:
        -------
            dict: Test configuration with event_number and mock values
        """
        config: dict[str, Any] = {
            "entry_point": self._entry_point,
            "event_number": self._event_number,
            "mocks": {}
        }
        
        # Parse mock values - create proper mock functions
        # Note: Lambdas need to capture values, so we use default args to avoid closure issues
        try:
            attacker_val = int(self.last_attacker_edit.text() or "0")
            config["mocks"]["GetLastAttacker"] = lambda o=1, val=attacker_val: val
        except ValueError:
            # Default to OBJECT_INVALID
            config["mocks"]["GetLastAttacker"] = lambda o=1: 0
        
        try:
            perceived_val = int(self.last_perceived_edit.text() or "0")
            config["mocks"]["GetLastPerceived"] = lambda val=perceived_val: val
        except ValueError:
            # Default to OBJECT_INVALID
            config["mocks"]["GetLastPerceived"] = lambda: 0
        
        try:
            creator_val = int(self.event_creator_edit.text() or "1")
            config["mocks"]["GetEventCreator"] = lambda val=creator_val: val
        except ValueError:
            # Default to OBJECT_SELF
            config["mocks"]["GetEventCreator"] = lambda: 1
        
        try:
            target_val = int(self.event_target_edit.text() or "1")
            config["mocks"]["GetEventTarget"] = lambda val=target_val: val
        except ValueError:
            # Default to OBJECT_SELF
            config["mocks"]["GetEventTarget"] = lambda: 1
        
        # Always mock GetUserDefinedEventNumber to return the selected event
        event_num = self._event_number
        config["mocks"]["GetUserDefinedEventNumber"] = lambda val=event_num: val
        
        return config


class TestConfigDialog(QDialog):
    """Dialog for configuring test run parameters."""
    
    def __init__(self, entry_point: str = "main", parent: QWidget | None = None):
        super().__init__(parent)
        from toolset.gui.common.localization import translate as tr
        self.setWindowTitle(tr("Configure Test Run"))
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Add config widget
        self.config_widget = TestConfigWidget(self)
        self.config_widget.set_entry_point(entry_point)
        layout.addWidget(self.config_widget)
        
        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            Qt.Orientation.Horizontal,
            self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_test_config(self) -> dict[str, Any]:
        """Get the test configuration from the widget."""
        return self.config_widget.get_test_config()

