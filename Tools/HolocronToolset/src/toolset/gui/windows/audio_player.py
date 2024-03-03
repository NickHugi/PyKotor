from __future__ import annotations

import time

from typing import TYPE_CHECKING

from PyQt5 import QtCore
from PyQt5.QtCore import QBuffer, QIODevice
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtWidgets import QFileDialog, QMainWindow

from pykotor.common.stream import BinaryReader
from pykotor.extract.file import ResourceIdentifier
from pykotor.tools import sound

if TYPE_CHECKING:
    import os

    from PyQt5.QtGui import QCloseEvent
    from PyQt5.QtWidgets import QWidget

    from pykotor.resource.type import ResourceType


class AudioPlayer(QMainWindow):
    def __init__(self, parent: QWidget | None):
        super().__init__(parent)

        from toolset.uic.windows.audio_player import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.player: QMediaPlayer = QMediaPlayer(self)
        self.buffer: QBuffer = QBuffer(self)

        self.ui.actionOpen.triggered.connect(self.open)
        self.ui.stopButton.clicked.connect(self.player.stop)
        self.ui.playButton.clicked.connect(self.player.play)
        self.ui.pauseButton.clicked.connect(self.player.pause)
        self.ui.timeSlider.sliderReleased.connect(self.changePosition)
        self.player.durationChanged.connect(self.durationChanged)
        self.player.positionChanged.connect(self.positionChanged)

    def load(self, filepath: os.PathLike | str, resname: str, restype: ResourceType, data: bytes):
        data = sound.deobfuscate_audio(data)

        self.player.stop()
        self.buffer = QBuffer(self)
        self.buffer.setData(data)
        self.setWindowTitle(f"{resname}.{restype.extension} - Audio Player")
        if self.buffer.open(QIODevice.ReadOnly):
            self.player.setMedia(QMediaContent(), self.buffer)
            QtCore.QTimer.singleShot(0, self.player.play)

    def open(self):
        filepath: str = QFileDialog.getOpenFileName(self, "Select an audio file")[0]
        if filepath:
            resname, restype = ResourceIdentifier.from_path(filepath).validate()
            data: bytes = BinaryReader.load_file(filepath)
            self.load(filepath, resname, restype, data)

    def durationChanged(self, duration: int):
        totalTime: str = time.strftime("%H:%M:%S", time.gmtime(duration // 1000))
        self.ui.totalTimeLabel.setText(totalTime)
        self.ui.timeSlider.setMaximum(duration)

    def positionChanged(self, position: int):
        currentTime: str = time.strftime("%H:%M:%S", time.gmtime(position // 1000))
        self.ui.currentTimeLabel.setText(currentTime)

        # sometimes QMediaPlayer does not accurately calculate the duration of the audio
        if position > self.ui.timeSlider.maximum():
            self.durationChanged(position)

        self.ui.timeSlider.setValue(position)

    def changePosition(self):
        position: int = self.ui.timeSlider.value()
        self.player.setPosition(position)

    def closeEvent(self, e: QCloseEvent | None):
        self.player.stop()
