import struct


def fix_audio(
    data: bytes,
) -> bytes:
    """Fixes corrupted audio data.

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
    b0x4 = struct.unpack("I", data[0:4])[0]
    b4x8 = struct.unpack("I", data[4:8])[0]
    b16x20 = struct.unpack("I", data[16:20])[0]
    if b0x4 == 1179011410 and b4x8 == 50 and b16x20 == 18:  # 0x46464952?
        data = data[8:]
    elif b0x4 == 3294688255:  # 0xC460F3FF?
        data = data[470:]
    return data
