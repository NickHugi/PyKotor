from __future__ import annotations

import time

from typing import TYPE_CHECKING

import qtpy

from qtpy import QtCore
from qtpy.QtCore import QBuffer, QIODevice
from qtpy.QtMultimedia import QMediaPlayer
from qtpy.QtWidgets import QFileDialog, QMainWindow

from pykotor.common.stream import BinaryReader
from pykotor.extract.file import ResourceIdentifier
from pykotor.tools import sound

if TYPE_CHECKING:
    import os

    from qtpy.QtGui import QCloseEvent
    from qtpy.QtWidgets import QWidget

    from pykotor.resource.type import ResourceType


class AudioPlayer(QMainWindow):
    def __init__(self, parent: QWidget | None):
        super().__init__(parent)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.windows.audio_player import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.windows.audio_player import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.windows.audio_player import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.windows.audio_player import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

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
        self.destroyed.connect(self.closeEvent)
        self.player.error.connect(lambda _: self.closeEvent())

    def load(
        self,
        filepath: os.PathLike | str,
        resname: str,
        restype: ResourceType,
        data: bytes,
    ):
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
            resname, restype = ResourceIdentifier.from_path(filepath).validate().unpack()
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

    def hideEvent(self, event):
        # closeEvent doesn't get called for whatever reason.
        super().hideEvent(event)
        self.player.stop()

    def closeEvent(self, e: QCloseEvent | None = None):  # FIXME(th3w1zard1): this event never gets called.
        print("Closing window and stopping player")  # Debugging line to confirm this method is called
        self.player.stop()  # Stop the player

        if e is not None:
            e.accept()  # Notify the event system that the event has been handled
            super().closeEvent(e)  # Call the parent class's closeEvent method
