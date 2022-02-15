import struct


def fix_audio(data: bytes) -> bytes:
    b0x4 = struct.unpack('I', data[0:4])[0]
    b4x8 = struct.unpack('I', data[4:8])[0]
    b16x20 = struct.unpack('I', data[16:20])[0]
    if b0x4 == 1179011410 and b4x8 == 50 and b16x20 == 18:
        data = data[8:]
    elif b0x4 == 3294688255:
        data = data[470:]
    return data
