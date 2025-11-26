from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.wav.io_wav import WAVBinaryReader, WAVBinaryWriter  # type: ignore[import-not-found, note]
from pykotor.resource.formats.wav.io_wav_standard import WAVStandardWriter  # type: ignore[import-not-found, note]
from pykotor.resource.type import ResourceType  # type: ignore[import-not-found, note]

if TYPE_CHECKING:
    from pykotor.resource.formats.wav.wav_data import WAV  # type: ignore[import-not-found, note]
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


def read_wav(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> WAV:
    """Returns a WAV instance from the source with automatic deobfuscation.

    The function automatically detects and removes obfuscation headers if present.
    The returned WAV object contains clean, deobfuscated data.

    Args:
    ----
        source: The source of the data.
        offset: The byte offset of the file inside the data.
        size: Number of bytes to allowed to read from the stream. If not specified, uses the whole stream.

    Raises:
    ------
        FileNotFoundError: If the file could not be found.
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be accessed.
        ValueError: If the file was corrupted or the format could not be determined.

    Returns:
    -------
        A WAV instance (automatically deobfuscated if needed).
    """
    return WAVBinaryReader(source, offset, size or 0).load()


def write_wav(
    wav: WAV,
    target: TARGET_TYPES,
    file_format: ResourceType = ResourceType.WAV,
):
    """Writes the WAV data to the target location with automatic obfuscation.

    If file_format is ResourceType.WAV, the data will be automatically obfuscated
    based on the WAV's type (SFX or VO). Otherwise, writes standard RIFF/WAVE format.

    Args:
    ----
        wav: The WAV file being written.
        target: The location to write the data to.
        file_format: The file format (WAV for obfuscated, any other for standard).

    Raises:
    ------
        IsADirectoryError: If the specified path is a directory (Unix-like systems only).
        PermissionError: If the file could not be written to the specified destination.
        ValueError: If the specified format was unsupported.
    """
    if file_format is ResourceType.WAV:
        WAVBinaryWriter(wav, target).write()
    else:
        WAVStandardWriter(wav, target).write()


def bytes_wav(
    wav: WAV,
    file_format: ResourceType = ResourceType.WAV,
) -> bytes:
    """Returns the WAV data as a bytes object with automatic obfuscation handling.

    If file_format is ResourceType.WAV, the data will be automatically obfuscated
    based on the WAV's type (SFX or VO). Otherwise, returns standard RIFF/WAVE format.

    Args:
    ----
        wav: The target WAV object.
        file_format: The file format (WAV for obfuscated, any other for standard).

    Raises:
    ------
        ValueError: If the specified format was unsupported.

    Returns:
    -------
        The WAV data (automatically obfuscated if file_format is WAV).
    """
    data = bytearray()
    write_wav(wav, data, file_format)
    return bytes(data)
