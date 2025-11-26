from __future__ import annotations

import wave

from typing import TYPE_CHECKING, Optional

from qtpy.QtCore import QTimer, QUrl, Qt
from qtpy.QtGui import QKeySequence
from qtpy.QtMultimedia import QAudioOutput, QMediaPlayer
from qtpy.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMenu,
    QMessageBox,
    QPushButton,
    QShortcut,  # pyright: ignore[reportPrivateImportUsage]
    QVBoxLayout,
    QWidget,
)

from pykotor.resource.formats.lip import LIP, LIPShape, bytes_lip, read_lip
from pykotor.resource.type import ResourceType
from toolset.gui.editor import Editor

if TYPE_CHECKING:
    import os

    from qtpy.QtCore import QPoint
    from qtpy.QtGui import _QAction

    from toolset.data.installation import HTInstallation


class LIPEditor(Editor):
    """Editor for KotOR LIP files."""

    def __init__(
        self,
        parent: QWidget | None = None,
        installation: HTInstallation | None = None,
    ):
        """Initialize the LIP editor."""
        supported = [ResourceType.LIP, ResourceType.LIP_XML, ResourceType.LIP_JSON]
        super().__init__(parent, "LIP Editor", "lip", supported, supported, installation)

        # Phoneme to viseme mapping from KLE
        self.phoneme_map: dict[str, LIPShape] = {
            "AA": LIPShape.AH,  # father
            "AE": LIPShape.AH,  # cat
            "AH": LIPShape.AH,  # cut
            "AO": LIPShape.OH,  # dog
            "AW": LIPShape.OH,  # cow
            "AY": LIPShape.AH,  # hide
            "B": LIPShape.MPB,  # be
            "CH": LIPShape.SH,  # cheese
            "D": LIPShape.TD,  # dee
            "DH": LIPShape.TD,  # thee
            "EH": LIPShape.EH,  # pet
            "ER": LIPShape.EE,  # fur
            "EY": LIPShape.AH,  # ate
            "F": LIPShape.FV,  # fee
            "G": LIPShape.TD,  # green
            "HH": LIPShape.EE,  # he
            "IH": LIPShape.EE,  # it
            "IY": LIPShape.EE,  # eat
            "JH": LIPShape.SH,  # gee
            "K": LIPShape.KG,  # key
            "L": LIPShape.L,  # lee
            "M": LIPShape.MPB,  # me
            "N": LIPShape.NG,  # knee
            "NG": LIPShape.NG,  # ping
            "OW": LIPShape.OH,  # oat
            "OY": LIPShape.OH,  # toy
            "P": LIPShape.MPB,  # pee
            "R": LIPShape.L,  # read
            "S": LIPShape.STS,  # sea
            "SH": LIPShape.SH,  # she
            "T": LIPShape.TD,  # tea
            "TH": LIPShape.FV,  # theta
            "UH": LIPShape.EE,  # hood
            "UW": LIPShape.OOH,  # two
            "V": LIPShape.FV,  # vee
            "W": LIPShape.MPB,  # we
            "Y": LIPShape.Y,  # yield
            "Z": LIPShape.STS,  # zee
            "ZH": LIPShape.STS,  # seizure
        }

        self.central_widget: QWidget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

        # Preview playback
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.positionChanged.connect(self.on_playback_position_changed)
        self.player.playbackStateChanged.connect(self.on_playback_state_changed)

        self.preview_timer = QTimer()
        self.preview_timer.setInterval(16)  # ~60fps
        self.preview_timer.timeout.connect(self.update_preview_display)

        # Current preview state
        self.current_shape: Optional[LIPShape] = None
        self.preview_label: Optional[QLabel] = None

        self.setup_ui()
        self._setup_menus()
        self._add_help_action()
        self.setup_shortcuts()
        self.lip: Optional[LIP] = None
        self.duration: float = 0.0

    def setup_ui(self):
        """Set up the UI elements."""
        layout = QVBoxLayout(self.central_widget)

        # Audio file selection
        audio_layout = QHBoxLayout()
        self.audio_path: QLineEdit = QLineEdit()
        self.audio_path.setReadOnly(True)
        self.audio_path.setToolTip("Path to the WAV audio file")
        audio_layout.addWidget(QLabel("Audio File:"))
        audio_layout.addWidget(self.audio_path)
        load_audio_btn = QPushButton("Load Audio")
        load_audio_btn.setToolTip("Load a WAV audio file (Ctrl+O)")
        load_audio_btn.clicked.connect(self.load_audio)
        audio_layout.addWidget(load_audio_btn)
        layout.addLayout(audio_layout)

        # Duration display
        duration_layout = QHBoxLayout()
        from toolset.gui.common.localization import translate as tr
        duration_layout.addWidget(QLabel(tr("Duration:")))
        self.duration_label: QLabel = QLabel("0.000s")
        self.duration_label.setToolTip(tr("Duration of the loaded audio file"))
        duration_layout.addWidget(self.duration_label)
        layout.addLayout(duration_layout)

        # Preview list
        self.preview_list: QListWidget = QListWidget()
        self.preview_list.setToolTip(tr("List of keyframes (right-click for options)"))
        self.preview_list.itemSelectionChanged.connect(self.on_keyframe_selected)
        self.preview_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.preview_list.customContextMenuRequested.connect(self.show_preview_context_menu)
        layout.addWidget(self.preview_list)

        # Keyframe editing
        keyframe_layout = QHBoxLayout()

        # Time input
        keyframe_layout.addWidget(QLabel("Time:"))
        self.time_input: QDoubleSpinBox = QDoubleSpinBox()
        self.time_input.setToolTip("Time in seconds for the keyframe")
        self.time_input.setDecimals(3)
        self.time_input.setRange(0.0, 999.999)
        self.time_input.setSingleStep(0.1)
        keyframe_layout.addWidget(self.time_input)

        # Shape selection
        keyframe_layout.addWidget(QLabel("Shape:"))
        self.shape_select: QComboBox = QComboBox()
        self.shape_select.setToolTip("Lip shape/viseme for the keyframe")
        for shape in LIPShape:
            self.shape_select.addItem(shape.name)
        keyframe_layout.addWidget(self.shape_select)

        layout.addLayout(keyframe_layout)

        # Keyframe buttons
        button_layout = QHBoxLayout()

        add_keyframe_btn = QPushButton("Add Keyframe")
        add_keyframe_btn.setToolTip("Add a new keyframe (Insert)")
        add_keyframe_btn.clicked.connect(self.add_keyframe)
        button_layout.addWidget(add_keyframe_btn)

        update_keyframe_btn = QPushButton("Update Keyframe")
        update_keyframe_btn.setToolTip("Update selected keyframe (Enter)")
        update_keyframe_btn.clicked.connect(self.update_keyframe)
        button_layout.addWidget(update_keyframe_btn)

        delete_keyframe_btn = QPushButton("Delete Keyframe")
        delete_keyframe_btn.setToolTip("Delete selected keyframe (Delete)")
        delete_keyframe_btn.clicked.connect(self.delete_keyframe)
        button_layout.addWidget(delete_keyframe_btn)

        layout.addLayout(button_layout)

        # Preview display
        preview_layout = QHBoxLayout()
        preview_layout.addWidget(QLabel("Current Shape:"))
        self.preview_label = QLabel("None")
        self.preview_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: #f0f0f0;
            }
        """)
        preview_layout.addWidget(self.preview_label)
        layout.addLayout(preview_layout)

        # Playback controls
        playback_layout = QHBoxLayout()

        play_btn = QPushButton("Play")
        play_btn.setToolTip("Play preview (Space)")
        play_btn.clicked.connect(self.play_preview)
        playback_layout.addWidget(play_btn)

        stop_btn = QPushButton("Stop")
        stop_btn.setToolTip("Stop preview (Esc)")
        stop_btn.clicked.connect(self.stop_preview)
        playback_layout.addWidget(stop_btn)

        layout.addLayout(playback_layout)

    def setup_shortcuts(self):
        """Set up keyboard shortcuts."""
        # File operations
        QShortcut(QKeySequence.StandardKey.Open, self, self.load_audio)
        QShortcut(QKeySequence.StandardKey.Save, self, self.save)
        QShortcut(QKeySequence.StandardKey.SaveAs, self, self.save_as)

        # Keyframe operations
        QShortcut(Qt.Key.Key_Insert, self, self.add_keyframe)
        QShortcut(Qt.Key.Key_Return, self, self.update_keyframe)
        QShortcut(Qt.Key.Key_Delete, self, self.delete_keyframe)

        # Playback controls
        QShortcut(Qt.Key.Key_Space, self, self.play_preview)
        QShortcut(Qt.Key.Key_Escape, self, self.stop_preview)

        # Undo/Redo
        QShortcut(QKeySequence.StandardKey.Undo, self, self.undo)
        QShortcut(QKeySequence.StandardKey.Redo, self, self.redo)

    def show_preview_context_menu(self, pos: QPoint):
        """Show context menu for preview list."""
        menu = QMenu(self)

        # Add actions
        add_action: _QAction = menu.addAction("Add Keyframe")
        add_action.triggered.connect(self.add_keyframe)

        # Only enable these if an item is selected
        selected_items = self.preview_list.selectedItems()
        if selected_items:
            update_action: _QAction = menu.addAction("Update Keyframe")
            update_action.triggered.connect(self.update_keyframe)

            delete_action: _QAction = menu.addAction("Delete Keyframe")
            delete_action.triggered.connect(self.delete_keyframe)

        menu.exec(self.preview_list.mapToGlobal(pos))

    def undo(self):
        """Undo last action."""
        # TODO: Implement undo/redo
        QMessageBox.information(self, "Not Implemented", "Undo not yet implemented")

    def redo(self):
        """Redo last undone action."""
        # TODO: Implement undo/redo
        QMessageBox.information(self, "Not Implemented", "Redo not yet implemented")

    def load_audio(self):
        """Load an audio file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Audio File", "", "Audio Files (*.wav)")
        if file_path:
            self.audio_path.setText(file_path)
            # Get audio duration
            with wave.open(file_path, "rb") as wav:
                frames = wav.getnframes()
                rate = wav.getframerate()
                self.duration = frames / float(rate)
                self.duration_label.setText(f"{self.duration:.3f}s")
                self.time_input.setMaximum(self.duration)

            # Set up media player
            self.player.setSource(QUrl.fromLocalFile(file_path))

    def add_keyframe(self):
        """Add a keyframe to the LIP file."""
        try:
            time = self.time_input.value()
            shape = LIPShape[self.shape_select.currentText()]

            if not self.lip:
                self.lip = LIP()
                self.lip.length = self.duration

            self.lip.add(time, shape)
            self.update_preview()

        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))

    def update_keyframe(self):
        """Update the selected keyframe."""
        if not self.lip:
            QMessageBox.warning(self, "Error", "No LIP file loaded")
            return

        selected_items = self.preview_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Please select a keyframe to update")
            return

        try:
            # Get current values
            time = self.time_input.value()
            shape = LIPShape[self.shape_select.currentText()]

            # Remove old keyframe and add updated one
            selected_idx = self.preview_list.row(selected_items[0])
            self.lip.frames.pop(selected_idx)
            self.lip.add(time, shape)

            self.update_preview()

        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))

    def delete_keyframe(self):
        """Delete the selected keyframe."""
        if not self.lip:
            QMessageBox.warning(self, "Error", "No LIP file loaded")
            return

        selected_items = self.preview_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Please select a keyframe to delete")
            return

        selected_idx = self.preview_list.row(selected_items[0])
        self.lip.frames.pop(selected_idx)
        self.update_preview()

    def on_keyframe_selected(self):
        """Update inputs when a keyframe is selected."""
        if not self.lip:
            return

        selected_items = self.preview_list.selectedItems()
        if not selected_items:
            return

        selected_idx = self.preview_list.row(selected_items[0])
        frame = self.lip.frames[selected_idx]

        self.time_input.setValue(frame.time)
        self.shape_select.setCurrentText(frame.shape.name)

    def update_preview(self):
        """Update the preview list."""
        self.preview_list.clear()
        if not self.lip:
            return

        for frame in sorted(self.lip.frames, key=lambda f: f.time):
            self.preview_list.addItem(f"{frame.time:.3f}s: {frame.shape.name}")

    def play_preview(self):
        """Start preview playback."""
        if not self.lip or not self.audio_path.text():
            QMessageBox.warning(self, "Error", "Please load both a LIP file and audio file")
            return

        self.player.play()
        self.preview_timer.start()

    def stop_preview(self):
        """Stop preview playback."""
        self.player.stop()
        self.preview_timer.stop()
        if self.preview_label:
            self.preview_label.setText("None")
        self.current_shape = None

    def on_playback_position_changed(self, position: int):
        """Update current time during playback."""
        current_time = position / 1000.0  # Convert ms to seconds

        # Find the current shape based on time
        if not self.lip:
            return

        # Sort frames by time
        sorted_frames = sorted(self.lip.frames, key=lambda f: f.time)

        # Find the last frame before current_time
        current_shape = None
        for frame in sorted_frames:
            if frame.time <= current_time:
                current_shape = frame.shape
            else:
                break

        self.current_shape = current_shape

    def update_preview_display(self):
        """Update the preview display with current shape."""
        if not self.preview_label:
            return

        if self.current_shape:
            self.preview_label.setText(self.current_shape.name)
        else:
            self.preview_label.setText("None")

    def on_playback_state_changed(self, state: QMediaPlayer.PlaybackState):
        """Handle playback state changes."""
        if state == QMediaPlayer.PlaybackState.StoppedState:
            if self.preview_label:
                self.preview_label.setText("None")
            self.preview_timer.stop()
            self.current_shape = None

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ) -> None:
        """Load a LIP file."""
        super().load(filepath, resref, restype, data)
        self.lip = read_lip(data)
        self.duration = self.lip.length
        self.duration_label.setText(f"{self.duration:.3f}s")
        self.time_input.setMaximum(self.duration)
        self.update_preview()

    def build(self) -> tuple[bytes, bytes]:
        """Build LIP file data."""
        if not self.lip:
            return b"", b""

        return bytes_lip(self.lip), b""

    def new(self):
        """Create new LIP file."""
        super().new()
        self.lip = LIP()
        self.duration = 0.0
        self.duration_label.setText("0.000s")
        self.time_input.setMaximum(999.999)
        self.update_preview()

