"""WAV obfuscation utilities for KotOR audio files.

KotOR audio files (VO and SFX) have obfuscation headers that need to be removed
for standard media players. This module handles both deobfuscation (for reading)
and obfuscation (for writing) of these headers.

**Internal Module**: The functions in this module (`deobfuscate_audio` and `obfuscate_audio`)
are internal implementation details and should only be called from within the wav folder
(e.g., `io_wav.py`). External code should use the public API in `wav_auto.py`:
- `read_wav()` for reading WAV files (automatically handles deobfuscation)
- `write_wav()` / `bytes_wav()` for writing WAV files (automatically handles obfuscation)

References:
----------
    vendor/SithCodec/src/codec.cpp (Audio codec implementation)
    vendor/SWKotOR-Audio-Encoder/ (Full audio encoder/decoder)
    vendor/reone/src/libs/audio/format/wavreader.cpp (WAV reading with header handling)
    Note: Magic numbers 1179011410 and 3294688255 are KotOR-specific audio obfuscation
"""

from __future__ import annotations

import struct


def deobfuscate_audio(
    data: bytes,
) -> bytes:  # sourcery skip: remove-redundant-slice-index
    """Removes the junk data at the start of a kotor audio file to make it playable by most media players.

    KotOR audio files (VO and SFX) have obfuscation headers that need to be removed
    for standard media players. This function detects and removes these headers.

    Args:
    ----
        data: bytes - Audio data bytes

    Returns:
    -------
        bytes: Fixed audio data bytes

    Processing Logic:
    ----------------
        - Unpack first 4 bytes and check for magic number 1179011410
        - Unpack bytes 4-8 and check for value 50
        - Unpack bytes 16-20 and check for value 18
        - If matches, trim first 8 bytes
        - Else if matches 3294688255, trim first 470 bytes.
    """
    if len(data) < 20:
        return data

    b0x4 = struct.unpack("I", data[0:4])[0]
    b4x8 = struct.unpack("I", data[4:8])[0]
    b16x20 = struct.unpack("I", data[16:20])[0]
    if b0x4 == 1179011410 and b4x8 == 50 and b16x20 == 18:  # noqa: PLR2004
        return data[8:]
    if b0x4 == 3294688255:  # noqa: PLR2004
        return data[470:]
    return data


def obfuscate_audio(
    data: bytes,
    wav_type: str = "SFX",
) -> bytes:
    """Adds obfuscation header to audio data for KotOR compatibility.

    Args:
    ----
        data: bytes - Clean audio data bytes
        wav_type: str - Type of WAV ("SFX" or "VO"). Defaults to "SFX".

    Returns:
    -------
        bytes: Obfuscated audio data bytes

    Processing Logic:
    ----------------
        - For SFX files, prepend 470-byte header with magic number 3294688255
        - For VO files, prepend 8-byte header with magic numbers 1179011410, 50, 18
    """
    if wav_type == "SFX":
        # Create 470-byte SFX header matching io_wav.py format
        header = bytearray([
            0xff, 0xff, 0xff, 0xff,  # 0x00: Magic number
            0xff, 0xff, 0xff, 0xf3,  # 0x04: Magic number
            0x60, 0xc4, 0x00, 0x00,  # 0x08: Unknown
            0x00, 0x03, 0x48, 0x00,  # 0x0C: Unknown
            0x00, 0x00, 0x00, 0x4c,  # 0x10: Unknown
            0x41, 0x4d, 0x45, 0x33,  # 0x14: "LAME3"
            0x2e, 0x39, 0x33, 0x55,  # 0x18: ".93U"
        ] + [0x55] * 442)  # Pad with 0x55 until 470 bytes
        return bytes(header) + data
    if wav_type == "VO":
        # Create 8-byte VO header
        header = bytearray(8)
        struct.pack_into("I", header, 0, 1179011410)  # noqa: PLR2004
        struct.pack_into("I", header, 4, 50)  # noqa: PLR2004
        # Bytes 8-16 would be part of the data, but we only prepend 8 bytes
        # The value 18 check is at offset 16, which would be in the data itself
        return bytes(header) + data
    return data

