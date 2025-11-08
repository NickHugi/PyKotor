from __future__ import annotations

from typing import TYPE_CHECKING, cast

import qtpy

from qtpy.QtCore import QBuffer, QPoint, Qt
from qtpy.QtMultimedia import QMediaPlayer
from qtpy.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSlider, QStyle, QWidget

if TYPE_CHECKING:
    from qtpy.QtGui import QFocusEvent, QMouseEvent, QShowEvent
    from qtpy.QtMultimedia import QAudioOutput


class MediaPlayerWidget(QWidget):
    def __init__(
        self,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.buffer: QBuffer = QBuffer(self)
        self.player: QMediaPlayer = QMediaPlayer(self)
        self._setup_media_player()
        self._setup_signals()
        self.hide_widget()

    def _setup_media_player(self):
        self.speed_levels: list[float] = [1, 1.25, 1.5, 2, 5, 10]
        self.current_speed_index: int = 0

        self.play_pause_button: QPushButton = QPushButton()
        self.play_pause_button.setIcon(cast(QStyle, self.style()).standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.play_pause_button.setFixedSize(24, 24)

        self.stop_button: QPushButton = QPushButton()
        self.stop_button.setIcon(cast(QStyle, self.style()).standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        self.stop_button.setFixedSize(24, 24)

        self.mute_button: QPushButton = QPushButton()
        self.mute_button.setIcon(cast(QStyle, self.style()).standardIcon(QStyle.StandardPixmap.SP_MediaVolume))
        self.mute_button.setFixedSize(24, 24)

        button_layout: QHBoxLayout = QHBoxLayout()
        for button in [self.play_pause_button, self.stop_button, self.mute_button]:
            button_layout.addWidget(button)
            button_layout.setAlignment(button, Qt.AlignmentFlag.AlignBottom)
        self.time_label: QLabel = QLabel("00:00 / 00:00")
        self._setup_time_slider()

        button_layout.addWidget(self.time_label)
        button_layout.addWidget(self.time_slider, 1)

        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(0)
        self.setLayout(button_layout)
        self.hide_widget()

    def _setup_time_slider(self):
        self.time_slider: QSlider = QSlider(Qt.Orientation.Horizontal)
        self.time_slider.setMouseTracking(True)
        self.drag_position: QPoint = QPoint()

        def slider_mouse_press_event(
            ev: QMouseEvent,
            slider: QSlider = self.time_slider,
        ):
            if ev.button() == Qt.MouseButton.LeftButton:
                self.player.pause()
                self.drag_position = ev.pos()
                ev.accept()
            super(QSlider, slider).mousePressEvent(ev)

        def slider_mouse_move_event(
            ev: QMouseEvent,
            slider: QSlider = self.time_slider,
        ):
            if ev.buttons() == Qt.MouseButton.LeftButton and not self.drag_position.isNull():
                value = int((ev.pos().x() / slider.width()) * slider.maximum())
                slider.setValue(value)
                self.player.setPosition(value)
                ev.accept()
            super(QSlider, slider).mouseMoveEvent(ev)

        def slider_mouse_release_event(
            ev: QMouseEvent,
            slider: QSlider = self.time_slider,
        ):
            if ev.button() == Qt.MouseButton.LeftButton and not self.drag_position.isNull():
                value = int((ev.pos().x() / slider.width()) * slider.maximum())
                slider.setValue(value)
                self.player.setPosition(value)
                self.player.play()
                self.drag_position = QPoint()
                ev.accept()
            super(QSlider, slider).mouseReleaseEvent(ev)

        def slider_focus_out_event(
            ev: QFocusEvent,
            slider: QSlider = self.time_slider,
        ):
            if not self.drag_position.isNull():
                value = int((self.drag_position.x() / slider.width()) * slider.maximum())
                slider.setValue(value)
                self.player.setPosition(value)
                self.player.play()
                ev.accept()
            super(QSlider, slider).focusOutEvent(ev)

        self.time_slider.mouseMoveEvent = slider_mouse_move_event  # type: ignore[attr-defined]
        self.time_slider.mousePressEvent = slider_mouse_press_event  # type: ignore[attr-defined]
        self.time_slider.mouseReleaseEvent = slider_mouse_release_event  # type: ignore[attr-defined]
        self.time_slider.focusOutEvent = slider_focus_out_event  # type: ignore[attr-defined]

    def on_play_pause_button_clicked(self):
        stateEnum = QMediaPlayer.State if qtpy.QT5 else QMediaPlayer.PlaybackState  # type: ignore[attr-defined]
        stateGetter = self.player.state if qtpy.QT5 else self.player.playbackState  # type: ignore[attr-defined]
        q_style: QStyle | None = self.style()
        assert q_style is not None, "q_style is somehow None"
        if stateGetter() == stateEnum.PlayingState:
            self.play_pause_button.setIcon(q_style.standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
            self.player.pause()
        else:
            self.play_pause_button.setIcon(q_style.standardIcon(QStyle.StandardPixmap.SP_MediaPause))
            self.player.play()

    def _setup_signals(self):
        self.player.mediaStatusChanged.connect(self.on_media_state_changed)
        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)
        state_changed = self.player.stateChanged if qtpy.QT5 else self.player.playbackStateChanged  # type: ignore[attr-defined]
        state_changed.connect(self.on_state_changed)

        self.play_pause_button.clicked.connect(self.on_play_pause_button_clicked)
        self.stop_button.clicked.connect(lambda *args: self.player.stop() or self.hide_widget())
        self.mute_button.clicked.connect(self.toggle_mute)

    def on_state_changed(
        self,
        state: QMediaPlayer.MediaStatus,
    ):
        state_enum = QMediaPlayer.State if qtpy.QT5 else QMediaPlayer.PlaybackState  # type: ignore[attr-defined]
        if state == state_enum.PlayingState:
            self.show_widget()

    def format_time(
        self,
        msecs: int,
    ) -> str:
        secs: int = msecs // 1000
        mins: int = secs // 60
        hrs: int = mins // 60
        return f"{hrs:02}:{mins % 60:02}:{secs % 60:02}"

    def on_media_state_changed(
        self,
        state: QMediaPlayer.MediaStatus,
    ):
        if state == QMediaPlayer.MediaStatus.EndOfMedia:
            self.time_slider.setValue(self.time_slider.maximum())
            self.hide_widget()
        state_enum = QMediaPlayer.State if qtpy.QT5 else QMediaPlayer.PlaybackState  # type: ignore[attr-defined]
        q_style: QStyle | None = self.style()
        assert q_style is not None, "q_style is somehow None"
        if state == state_enum.PlayingState:
            self.play_pause_button.setIcon(q_style.standardIcon(QStyle.StandardPixmap.SP_MediaPause))
        else:
            self.play_pause_button.setIcon(q_style.standardIcon(QStyle.StandardPixmap.SP_MediaPlay))

    def change_playback_speed(self, direction: int):
        """Some qt bug prevents this from working properly. Requires a start and a play in order to take effect."""
        self.current_speed_index = max(0, min(len(self.speed_levels) - 1, self.current_speed_index + direction))
        new_rate: float = self.speed_levels[self.current_speed_index]
        state_enum = QMediaPlayer.State if qtpy.QT5 else QMediaPlayer.PlaybackState  # type: ignore[attr-defined]
        state_getter = self.player.state if qtpy.QT5 else self.player.playbackState  # type: ignore[attr-defined]
        was_playing: bool = state_getter() == state_enum.PlayingState
        current_position: int = self.player.position()
        self.player.setPlaybackRate(new_rate)
        self.player.setPosition(current_position)
        if was_playing:
            self.player.play()

    def toggle_mute(self):
        if qtpy.QT5:
            self.player.setMuted(not self.player.isMuted())  # type: ignore[attr-defined]
            muted: bool = self.player.isMuted()  # type: ignore[attr-defined]
        else:
            audio_output: QAudioOutput | None = self.player.audioOutput()  # type: ignore[attr-defined]
            current_volume: float = audio_output.volume()  # type: ignore[attr-defined]
            if current_volume > 0:
                self.previous_volume: float = current_volume
                audio_output.setVolume(0)  # type: ignore[attr-defined]
                muted = True
            else:
                audio_output.setVolume(self.previous_volume if hasattr(self, "previous_volume") else 0.5)  # type: ignore[attr-defined]
                muted = False  # type: ignore[attr-defined]
        q_style: QStyle | None = self.style()
        assert q_style is not None, "q_style is somehow None"
        if muted:
            self.mute_button.setIcon(q_style.standardIcon(QStyle.StandardPixmap.SP_MediaVolumeMuted))
        else:
            self.mute_button.setIcon(q_style.standardIcon(QStyle.StandardPixmap.SP_MediaVolume))

    def on_position_changed(
        self,
        position: int,
    ):
        if not self.time_slider.isSliderDown():
            self.time_slider.setValue(position)
        current_time: str = self.format_time(position)
        total_time: str = self.format_time(self.time_slider.maximum())
        self.time_label.setText(f"{current_time} / {total_time}")

    def on_duration_changed(
        self,
        duration: int,
    ):
        self.time_slider.setRange(0, duration)
        total_time: str = self.format_time(duration)
        current_time: str = self.format_time(self.time_slider.value())
        self.time_label.setText(f"{current_time} / {total_time}")

    def show_widget(self):
        self.show()
        self.play_pause_button.show()
        self.stop_button.show()
        self.mute_button.show()
        self.time_label.show()
        self.time_slider.show()

    def hide_widget(self):
        self.hide()
        self.play_pause_button.hide()
        self.stop_button.hide()
        self.mute_button.hide()
        self.time_label.hide()
        self.time_slider.hide()

    def setVisible(
        self,
        visible: bool,  # noqa: FBT001
    ):  # noqa: FBT001
        """Override to control visibility based on player state."""
        state_enum = QMediaPlayer.State if qtpy.QT5 else QMediaPlayer.PlaybackState  # type: ignore[attr-defined]
        state_getter = self.player.state if qtpy.QT5 else self.player.playbackState  # type: ignore[attr-defined]
        if state_getter() == state_enum.PlayingState:
            return
        super().setVisible(visible)

    def showEvent(
        self,
        event: QShowEvent,
    ):  # pyright: ignore[reportIncompatibleMethodOverride]  # noqa: N802
        """Override to prevent showing unless playing."""
        state_enum = QMediaPlayer.State if qtpy.QT5 else QMediaPlayer.PlaybackState  # type: ignore[attr-defined]
        state_getter = self.player.state if qtpy.QT5 else self.player.playbackState  # type: ignore[attr-defined]
        if state_getter() != state_enum.PlayingState:
            return
        super().showEvent(event)
