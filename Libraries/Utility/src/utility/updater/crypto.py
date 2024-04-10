from __future__ import annotations

import base64
import binascii
import codecs
import json
import struct

from Crypto.Cipher import AES


def a32_to_str(a) -> bytes:
    return struct.pack(">%dI" % len(a), *a)


def str_to_a32(b):
    if isinstance(b, str):
        b = codecs.latin_1_encode(b)[0]
    if len(b) % 4:
        # pad to multiple of 4
        b += b"\0" * (4 - len(b) % 4)
    return struct.unpack(">%dI" % (len(b) / 4), b)


def mpi_to_int(s) -> int:
    return int(binascii.hexlify(s[2:]), 16)


def base64_url_decode(data) -> bytes:
    data += "=="[(2 - len(data) * 3) % 4 :]
    for search, replace in (("-", "+"), ("_", "/"), (",", "")):
        data = data.replace(search, replace)
    return base64.b64decode(data)


def base64_to_a32(s):
    return str_to_a32(base64_url_decode(s))


def base64_url_encode(data) -> str:
    data = base64.b64encode(data)
    data = codecs.latin_1_decode(data)[0]
    for search, replace in (("+", "-"), ("/", "_"), ("=", "")):
        data = data.replace(search, replace)
    return data


def aes_cbc_decrypt(data, key):
    aes_cipher = AES.new(key, AES.MODE_CBC, codecs.latin_1_encode("\0" * 16)[0])
    return aes_cipher.decrypt(data)


def a32_to_base64(a) -> str:
    return base64_url_encode(a32_to_str(a))


def decrypt_mega_attr(attr, key):
    attr = aes_cbc_decrypt(attr, a32_to_str(key))
    attr = codecs.latin_1_decode(attr)[0]
    attr = attr.rstrip("\0")
    return json.loads(attr[4:]) if attr[:6] == 'MEGA{"' else False


def get_chunks(size):
    p = 0
    s = 0x20000
    while p + s < size:
        yield (p, s)
        p += s
        if s < 0x100000:
            s += 0x20000
    yield (p, size - p)