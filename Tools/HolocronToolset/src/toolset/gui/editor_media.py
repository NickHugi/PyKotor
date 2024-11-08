from __future__ import annotations

import tempfile

from typing import TYPE_CHECKING, Any, cast

import qtpy

from loggerplus import RobustLogger
from qtpy.QtCore import QBuffer, QIODevice, QTimer, QUrl
from qtpy.QtMultimedia import QMediaPlayer

from pykotor.extract.installation import SearchLocation
from utility.system.os_helper import remove_any

if TYPE_CHECKING:
    import os

    from PyQt6.QtMultimedia import QMediaPlayer as PyQt6MediaPlayer  # pyright: ignore[reportMissingImports, reportAttributeAccessIssue]
    from PySide6.QtMultimedia import QMediaPlayer as PySide6MediaPlayer  # pyright: ignore[reportMissingImports, reportAttributeAccessIssue]

    from toolset.gui.editor_base import Editor


class EditorMedia:
    def __init__(self, editor: Editor):
        self.editor = editor

    def play_byte_source_media(
        self,
        data: bytes | None,
    ) -> bool:
        if not data:
            self.editor.blink_window()
            return False
        if qtpy.QT5:
            from qtpy.QtMultimedia import QMediaContent  # pyright: ignore[reportAttributeAccessIssue]

            self.editor.media_player.buffer = buffer = QBuffer(self.editor)
            buffer.setData(data)
            buffer.open(QIODevice.OpenModeFlag.ReadOnly)
            self.editor.media_player.player.setMedia(QMediaContent(), buffer)  # pyright: ignore[reportAttributeAccessIssue]
            QTimer.singleShot(0, self.editor.media_player.player.play)

        elif qtpy.QT6:
            from qtpy.QtMultimedia import QAudioOutput

            temp_file: tempfile._TemporaryFileWrapper[bytes] = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_file.write(data)  # pyright: ignore[reportArgumentType, reportCallIssue]
            temp_file.flush()
            temp_file.seek(0)
            temp_file.close()

            player: PyQt6MediaPlayer | PySide6MediaPlayer = cast(Any, self.editor.media_player.player)
            audio_output = QAudioOutput(self.editor)  # pyright: ignore[reportCallIssue, reportArgumentType]
            audio_output.setVolume(1)
            player.setAudioOutput(audio_output)  # pyright: ignore[reportArgumentType]
            player.setSource(QUrl.fromLocalFile(temp_file.name))  # pyright: ignore[reportArgumentType]
            player.mediaStatusChanged.connect(lambda status, file_name=temp_file.name: self.remove_temp_audio_file(status, file_name))
            player.play()
        return True

    def play_sound(
        self,
        resname: str,
        order: list[SearchLocation] | None = None,
    ) -> bool:
        """Plays a sound resource."""
        if not resname or not resname.strip() or self.editor._installation is None:
            self.editor.blink_window(sound=False)
            return False

        self.editor.media_player.player.stop()

        data: bytes | None = self.editor._installation.sound(
            resname,
            order
            if order is not None
            else [
                SearchLocation.MUSIC,
                SearchLocation.VOICE,
                SearchLocation.SOUND,
                SearchLocation.OVERRIDE,
                SearchLocation.CHITIN,
            ],
        )
        if not data:
            self.editor.blink_window(sound=False)
        return self.play_byte_source_media(data)

    def remove_temp_audio_file(
        self,
        status: QMediaPlayer.MediaStatus,
        file_path: os.PathLike | str,
    ):
        if status != QMediaPlayer.MediaStatus.EndOfMedia:
            return
        try:
            self.editor.media_player.player.stop()
            QTimer.singleShot(33, lambda: remove_any(file_path))
        except OSError:
            RobustLogger().exception(f"Error removing temporary file '{file_path}'")