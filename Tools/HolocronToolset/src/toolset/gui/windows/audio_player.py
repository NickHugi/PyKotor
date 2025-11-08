from __future__ import annotations

import time

from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import qtpy

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy import QtCore
from qtpy.QtCore import QBuffer, QIODevice, QTimer
from qtpy.QtMultimedia import QMediaPlayer
from qtpy.QtWidgets import QFileDialog, QMainWindow

from pykotor.extract.file import ResourceIdentifier
from pykotor.tools import sound
from utility.system.os_helper import remove_any

if TYPE_CHECKING:

    import os

    from PyQt6.QtMultimedia import QMediaPlayer as PyQt6MediaPlayer  # pyright: ignore[reportMissingImports, reportAttributeAccessIssue]
    from PySide6.QtMultimedia import QMediaPlayer as PySide6MediaPlayer  # pyright: ignore[reportMissingImports, reportAttributeAccessIssue]
    from qtpy.QtGui import QCloseEvent
    from qtpy.QtWidgets import QWidget

    from pykotor.resource.type import ResourceType


class AudioPlayer(QMainWindow):
    def __init__(self, parent: QWidget | None):
        super().__init__(parent)

        from toolset.uic.qtpy.windows.audio_player import Ui_MainWindow

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.player: QMediaPlayer = QMediaPlayer(self)
        self.buffer: QBuffer = QBuffer(self)

        self.ui.actionOpen.triggered.connect(self.open)
        self.ui.stopButton.clicked.connect(self.player.stop)
        self.ui.playButton.clicked.connect(self.player.play)
        self.ui.pauseButton.clicked.connect(self.player.pause)
        self.ui.timeSlider.sliderReleased.connect(self.changePosition)
        self.player.durationChanged.connect(self.duration_changed)
        self.player.positionChanged.connect(self.positionChanged)
        self.destroyed.connect(self.closeEvent)
        if qtpy.QT5:
            self.player.error.connect(lambda _=None: self.handle_error())
        else:
            self.player.errorOccurred.connect(lambda *args, **kwargs: self.handle_error(*args, **kwargs))  # noqa: FBT001  # pyright: ignore[reportAttributeAccessIssue]

        self.temp_file = None  # Reference to the temporary file for PyQt6/Pyside6

    def handle_error(self, *args, **kwargs):
        print("Error:", *args, **kwargs)
        self.closeEvent(None)

    def set_media(self, data: bytes, restype: ResourceType):
        # sourcery skip: extract-method
        self.player.stop()
        data = sound.deobfuscate_audio(data)
        # Clear any existing temporary file
        if self.temp_file and Path(self.temp_file.name).is_file():
            self.temp_file.delete = True
            remove_any(self.temp_file.name)
        self.temp_file = None

        if not data:
            return

        if qtpy.QT5:
            self.buffer = QBuffer(self)
            self.buffer.setData(data)
            if not self.buffer.open(QIODevice.OpenModeFlag.ReadOnly):
                print("Audio player Buffer not ready?")
                return
            from qtpy.QtMultimedia import QMediaContent  # pyright: ignore[reportAttributeAccessIssue]
            self.player.setMedia(QMediaContent(), self.buffer)  # pyright: ignore[reportAttributeAccessIssue]
        elif qtpy.QT6:
            from qtpy.QtMultimedia import QAudioOutput

            # Create buffer and load data
            buffer = QBuffer(self)
            buffer.setData(data)
            buffer.open(QIODevice.OpenModeFlag.ReadOnly)

            # Set up player
            player: PyQt6MediaPlayer | PySide6MediaPlayer = cast(Any, self.player)
            audio_output = QAudioOutput(self)
            audio_output.setVolume(1)
            player.setAudioOutput(audio_output)

            # Use the buffer directly instead of a file
            player.setSourceDevice(buffer)
            player.play()
        QtCore.QTimer.singleShot(0, self.player.play)

    def remove_temp_audio_file(
        self,
        status: QMediaPlayer.MediaStatus,
        filePathStr: str,
    ):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            try:
                self.player.stop()
                QTimer.singleShot(33, lambda: remove_any(filePathStr))
            except OSError:
                RobustLogger().exception(f"Error removing temporary file {filePathStr}")

    def load(
        self,
        filepath: os.PathLike | str,
        resname: str,
        restype: ResourceType,
        data: bytes,
    ):
        self.setWindowTitle(f"{resname}.{restype.extension} - Audio Player")
        self.set_media(data, restype)  # Use the refined set_media method

    def open(self):
        filepath: str = QFileDialog.getOpenFileName(self, "Select an audio file")[0]
        if filepath and str(filepath).strip():
            with suppress(ValueError, TypeError):
                resname, restype = ResourceIdentifier.from_path(filepath).validate().unpack()
                data: bytes = Path(filepath).read_bytes()
                self.load(filepath, resname, restype, data)

    def duration_changed(self, duration: int):
        total_time: str = time.strftime("%H:%M:%S", time.gmtime(duration // 1000))
        self.ui.totalTimeLabel.setText(total_time)
        self.ui.timeSlider.setMaximum(duration)

    def positionChanged(self, position: int):
        current_time: str = time.strftime("%H:%M:%S", time.gmtime(position // 1000))
        self.ui.currentTimeLabel.setText(current_time)

        # sometimes QMediaPlayer does not accurately calculate the duration of the audio
        if position > self.ui.timeSlider.maximum():
            self.duration_changed(position)

        self.ui.timeSlider.setValue(position)

    def changePosition(self):
        position: int = self.ui.timeSlider.value()
        self.player.setPosition(position)

    def closeEvent(self, e: QCloseEvent | None = None):
        self.player.stop()

        if e is not None:
            e.accept()
            super().closeEvent(e)
