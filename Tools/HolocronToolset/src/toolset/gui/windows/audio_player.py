from __future__ import annotations

import time
from typing import TYPE_CHECKING

from pykotor.common.stream import BinaryReader
from pykotor.extract.file import ResourceIdentifier
from pykotor.tools import sound
from PyQt5 import QtCore
from PyQt5.QtCore import QBuffer, QIODevice
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtWidgets import QFileDialog, QMainWindow, QWidget

if TYPE_CHECKING:
    import os

    from pykotor.resource.type import ResourceType
    from PyQt5.QtGui import QCloseEvent


class AudioPlayer(QMainWindow):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        from toolset.uic.windows.audio_player import Ui_MainWindow

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.player = QMediaPlayer(self)
        self.buffer = QBuffer(self)

        self.ui.actionOpen.triggered.connect(self.open)
        self.ui.stopButton.clicked.connect(self.player.stop)
        self.ui.playButton.clicked.connect(self.player.play)
        self.ui.pauseButton.clicked.connect(self.player.pause)
        self.ui.timeSlider.sliderReleased.connect(self.changePosition)
        self.player.durationChanged.connect(self.durationChanged)
        self.player.positionChanged.connect(self.positionChanged)

    def load(self, filepath: os.PathLike | str, resname: str, restype: ResourceType, data: bytes):
        data = sound.fix_audio(data)

        self.player.stop()
        self.buffer = QBuffer(self)
        self.buffer.setData(data)
        self.setWindowTitle(f"{resname}.{restype.extension} - Audio Player")
        if self.buffer.open(QIODevice.ReadOnly):
            self.player.setMedia(QMediaContent(), self.buffer)
            QtCore.QTimer.singleShot(0, self.player.play)

    def open(self):
        filepath = QFileDialog.getOpenFileName(self, "Select an audio file")[0]
        if filepath != "":
            resname, restype = ResourceIdentifier.from_path(filepath).validate()
            data = BinaryReader.load_file(filepath)
            self.load(filepath, resname, restype, data)

    def durationChanged(self, duration: int):
        totalTime = time.strftime("%H:%M:%S", time.gmtime(duration // 1000))
        self.ui.totalTimeLabel.setText(totalTime)
        self.ui.timeSlider.setMaximum(duration)

    def positionChanged(self, position: int):
        currentTime = time.strftime("%H:%M:%S", time.gmtime(position // 1000))
        self.ui.currentTimeLabel.setText(currentTime)

        # sometimes QMediaPlayer does not accurately calculate the duration of the audio
        if position > self.ui.timeSlider.maximum():
            self.durationChanged(position)

        self.ui.timeSlider.setValue(position)

    def changePosition(self):
        position = self.ui.timeSlider.value()
        self.player.setPosition(position)

    def closeEvent(self, e: QCloseEvent | None):
        self.player.stop()
