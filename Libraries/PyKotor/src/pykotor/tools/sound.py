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
    
    References:
    ----------
        vendor/SithCodec/src/codec.cpp (Audio codec implementation)
        vendor/SWKotOR-Audio-Encoder/ (Full audio encoder/decoder)
        vendor/reone/src/libs/audio/format/wavreader.cpp (WAV reading with header handling)
        Note: Magic numbers 1179011410 and 3294688255 are KotOR-specific audio obfuscation
    """
    b0x4 = struct.unpack("I", data[0:4])[0]
    b4x8 = struct.unpack("I", data[4:8])[0]
    b16x20 = struct.unpack("I", data[16:20])[0]
    if b0x4 == 1179011410 and b4x8 == 50 and b16x20 == 18:  # noqa: PLR2004
        data = data[8:]
    elif b0x4 == 3294688255:  # noqa: PLR2004
        data = data[470:]
    return data
