from __future__ import annotations

import tempfile
import time

from contextlib import suppress
from typing import TYPE_CHECKING

import qtpy

from qtpy import QtCore
from qtpy.QtCore import QBuffer, QIODevice, QTimer
from qtpy.QtMultimedia import QAudioOutput, QMediaPlayer
from qtpy.QtWidgets import QFileDialog, QMainWindow

from pykotor.common.stream import BinaryReader
from pykotor.extract.file import ResourceIdentifier
from pykotor.tools import sound
from utility.logger_util import RobustRootLogger
from utility.system.os_helper import remove_any
from utility.system.path import Path

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
        if qtpy.API_NAME in {"PySide2", "PyQt5"}:
            self.player.error.connect(lambda _=None: self.handleError())
        else:
            self.player.errorOccurred.connect(lambda *args, **kwargs: self.handleError(*args, **kwargs))

        self.tempFile = None  # Reference to the temporary file for PyQt6/Pyside6

    def handleError(self, *args, **kwargs):
        print("Error:", *args, **kwargs)
        self.closeEvent(None)

    def set_media(self, data: bytes, restype: ResourceType):
        # sourcery skip: extract-method
        self.player.stop()
        data = sound.deobfuscate_audio(data)
        # Clear any existing temporary file
        if self.tempFile and Path(self.tempFile.name).safe_isfile():
            self.tempFile.delete = True
            remove_any(self.tempFile.name)
        self.tempFile = None

        if not data:
            return

        if qtpy.API_NAME in {"PyQt5", "PySide2"}:
            self.buffer = QBuffer(self)
            self.buffer.setData(data)
            if not self.buffer.open(QIODevice.OpenModeFlag.ReadOnly):
                print("Audio player Buffer not ready?")
                return
            from qtpy.QtMultimedia import QMediaContent
            self.player.setMedia(QMediaContent(), self.buffer)
        else:
            self.tempFile = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            self.tempFile.write(data)
            self.tempFile.flush()
            self.tempFile.seek(0)
            self.tempFile.close()

            audioOutput = QAudioOutput(self)
            self.player.setAudioOutput(audioOutput)
            self.player.setSource(QtCore.QUrl.fromLocalFile(self.tempFile.name))
            audioOutput.setVolume(1)
            self.player.mediaStatusChanged.connect(lambda status, file_name=self.tempFile.name: self.removeTempAudioFile(status, file_name))
        QtCore.QTimer.singleShot(0, self.player.play)

    def removeTempAudioFile(
        self,
        status: QMediaPlayer.MediaStatus,
        filePathStr: str,
    ):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            try:
                self.player.stop()
                QTimer.singleShot(33, lambda: remove_any(filePathStr))
            except OSError:
                RobustRootLogger.exception(f"Error removing temporary file {filePathStr}")

    def load(self, filepath: os.PathLike | str, resname: str, restype: ResourceType, data: bytes):
        self.setWindowTitle(f"{resname}.{restype.extension} - Audio Player")
        self.set_media(data, restype)  # Use the refined set_media method

    def open(self):
        filepath: str = QFileDialog.getOpenFileName(self, "Select an audio file")[0]
        if filepath:
            with suppress(ValueError, TypeError):
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

    def closeEvent(self, e: QCloseEvent | None = None):
        self.player.stop()

        if e is not None:
            e.accept()
            super().closeEvent(e)
