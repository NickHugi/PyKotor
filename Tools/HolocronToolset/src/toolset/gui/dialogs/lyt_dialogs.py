"""Dialog windows for LYT editing."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtWidgets import QDialog, QDoubleSpinBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout

from utility.common.geometry import Vector3

if TYPE_CHECKING:
    from pykotor.resource.formats.lyt.lyt_data import LYTDoorHook, LYTObstacle, LYTRoom, LYTTrack


class RoomPropertiesDialog(QDialog):
    def __init__(self, room: LYTRoom, parent=None):
        super().__init__(parent)
        self.room = room
        from toolset.gui.common.localization import translate as tr
        self.setWindowTitle(tr("Room Properties"))
        self.setup_ui()
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Model Name
        model_layout = QHBoxLayout()
        from toolset.gui.common.localization import translate as tr
        model_label = QLabel(tr("Model:"))
        self.model_input = QLineEdit(self.room.model)
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_input)
        layout.addLayout(model_layout)

        # Position
        pos_layout = QHBoxLayout()
        pos_label = QLabel(tr("Position:"))
        self.x_spin = QDoubleSpinBox()
        self.y_spin = QDoubleSpinBox()
        self.z_spin = QDoubleSpinBox()

        for spin in [self.x_spin, self.y_spin, self.z_spin]:
            spin.setRange(-10000, 10000)
            spin.setDecimals(2)

        self.x_spin.setValue(self.room.position.x)
        self.y_spin.setValue(self.room.position.y)
        self.z_spin.setValue(self.room.position.z)

        pos_layout.addWidget(QLabel("X:"))
        pos_layout.addWidget(self.x_spin)
        pos_layout.addWidget(QLabel("Y:"))
        pos_layout.addWidget(self.y_spin)
        pos_layout.addWidget(QLabel("Z:"))
        pos_layout.addWidget(self.z_spin)
        layout.addLayout(pos_layout)

        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

    def accept(self):
        try:
            # Validate inputs
            model = self.model_input.text().strip()
            from toolset.gui.common.localization import translate as tr, trf
            if not model:
                QMessageBox.warning(self, tr("Invalid Input"), tr("Model name cannot be empty."))
                return

            # Update room properties
            self.room.model = model
            self.room.position = Vector3(self.x_spin.value(), self.y_spin.value(), self.z_spin.value())
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, tr("Error"), trf("Failed to update room properties: {error}", error=str(e)))


class TrackPropertiesDialog(QDialog):
    def __init__(self, rooms: list[LYTRoom], track: LYTTrack, parent=None):
        super().__init__(parent)
        self.track = track
        self.rooms = rooms
        from toolset.gui.common.localization import translate as tr
        self.setWindowTitle(tr("Track Properties"))
        self.setup_ui()
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Model Name
        model_layout = QHBoxLayout()
        model_label = QLabel("Model:")
        self.model_input = QLineEdit(self.track.model)
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_input)
        layout.addLayout(model_layout)

        # Position
        pos_layout = QHBoxLayout()
        pos_label = QLabel("Position:")
        self.x_spin = QDoubleSpinBox()
        self.y_spin = QDoubleSpinBox()
        self.z_spin = QDoubleSpinBox()

        for spin in [self.x_spin, self.y_spin, self.z_spin]:
            spin.setRange(-10000, 10000)
            spin.setDecimals(2)

        self.x_spin.setValue(self.track.position.x)
        self.y_spin.setValue(self.track.position.y)
        self.z_spin.setValue(self.track.position.z)

        pos_layout.addWidget(QLabel("X:"))
        pos_layout.addWidget(self.x_spin)
        pos_layout.addWidget(QLabel("Y:"))
        pos_layout.addWidget(self.y_spin)
        pos_layout.addWidget(QLabel("Z:"))
        pos_layout.addWidget(self.z_spin)
        layout.addLayout(pos_layout)

        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

    def accept(self):
        try:
            # Validate inputs
            model = self.model_input.text().strip()
            if not model:
                QMessageBox.warning(self, "Invalid Input", "Model name cannot be empty.")
                return

            # Update track properties
            self.track.model = model
            self.track.position = Vector3(self.x_spin.value(), self.y_spin.value(), self.z_spin.value())
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update track properties: {e!s}")


class ObstaclePropertiesDialog(QDialog):
    def __init__(self, obstacle: LYTObstacle, parent=None):
        super().__init__(parent)
        self.obstacle = obstacle
        self.setWindowTitle("Obstacle Properties")
        self.setup_ui()
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Model Name
        model_layout = QHBoxLayout()
        model_label = QLabel("Model:")
        self.model_input = QLineEdit(self.obstacle.model)
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_input)
        layout.addLayout(model_layout)

        # Position
        pos_layout = QHBoxLayout()
        pos_label = QLabel("Position:")
        self.x_spin = QDoubleSpinBox()
        self.y_spin = QDoubleSpinBox()
        self.z_spin = QDoubleSpinBox()

        for spin in [self.x_spin, self.y_spin, self.z_spin]:
            spin.setRange(-10000, 10000)
            spin.setDecimals(2)

        self.x_spin.setValue(self.obstacle.position.x)
        self.y_spin.setValue(self.obstacle.position.y)
        self.z_spin.setValue(self.obstacle.position.z)

        pos_layout.addWidget(QLabel("X:"))
        pos_layout.addWidget(self.x_spin)
        pos_layout.addWidget(QLabel("Y:"))
        pos_layout.addWidget(self.y_spin)
        pos_layout.addWidget(QLabel("Z:"))
        pos_layout.addWidget(self.z_spin)
        layout.addLayout(pos_layout)

        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

    def accept(self):
        try:
            # Validate inputs
            model = self.model_input.text().strip()
            if not model:
                QMessageBox.warning(self, "Invalid Input", "Model name cannot be empty.")
                return

            # Update obstacle properties
            self.obstacle.model = model
            self.obstacle.position = Vector3(self.x_spin.value(), self.y_spin.value(), self.z_spin.value())
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update obstacle properties: {e!s}")


class DoorHookPropertiesDialog(QDialog):
    def __init__(self, doorhook: LYTDoorHook, parent=None):
        super().__init__(parent)
        self.doorhook: LYTDoorHook = doorhook
        self.setWindowTitle("Door Hook Properties")
        self.setup_ui()
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Room Name
        room_layout = QHBoxLayout()
        room_label = QLabel("Room:")
        self.room_input = QLineEdit(self.doorhook.room)
        room_layout.addWidget(room_label)
        room_layout.addWidget(self.room_input)
        layout.addLayout(room_layout)

        # Door Name
        door_layout = QHBoxLayout()
        door_label = QLabel("Door:")
        self.door_input = QLineEdit(self.doorhook.door)
        door_layout.addWidget(door_label)
        door_layout.addWidget(self.door_input)
        layout.addLayout(door_layout)

        # Position
        pos_layout = QHBoxLayout()
        pos_label = QLabel("Position:")
        self.x_spin = QDoubleSpinBox()
        self.y_spin = QDoubleSpinBox()
        self.z_spin = QDoubleSpinBox()

        for spin in [self.x_spin, self.y_spin, self.z_spin]:
            spin.setRange(-10000, 10000)
            spin.setDecimals(2)

        self.x_spin.setValue(self.doorhook.position.x)
        self.y_spin.setValue(self.doorhook.position.y)
        self.z_spin.setValue(self.doorhook.position.z)

        pos_layout.addWidget(QLabel("X:"))
        pos_layout.addWidget(self.x_spin)
        pos_layout.addWidget(QLabel("Y:"))
        pos_layout.addWidget(self.y_spin)
        pos_layout.addWidget(QLabel("Z:"))
        pos_layout.addWidget(self.z_spin)
        layout.addLayout(pos_layout)

        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

    def accept(self):
        try:
            # Validate inputs
            room = self.room_input.text().strip()
            door = self.door_input.text().strip()
            if not room or not door:
                QMessageBox.warning(self, "Invalid Input", "Room and door names cannot be empty.")
                return

            # Update doorhook properties
            self.doorhook.room = room
            self.doorhook.door = door
            self.doorhook.position = Vector3(self.x_spin.value(), self.y_spin.value(), self.z_spin.value())
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update door hook properties: {e!s}")


class AddRoomDialog(QDialog):
    """Dialog for adding a new room to the LYT."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

    def _setup_ui(self):
        """Initialize the UI."""
        self.setWindowTitle("Add Room")


class AddDoorHookDialog(QDialog):
    """Dialog for adding a new door hook."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

    def _setup_ui(self):
        """Initialize the UI."""
        self.setWindowTitle("Add Door Hook")
