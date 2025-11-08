# Import necessary components from the key format modules
from __future__ import annotations
from pykotor.resource.formats.key.io_key import KEYBinaryReader, KEYBinaryWriter
from pykotor.resource.formats.key.key_auto import detect_key, read_key, write_key, bytes_key
from pykotor.resource.formats.key.key_data import KEY, BifEntry, KeyEntry

__all__ = [
    "KEY",
    "BifEntry",
    "KEYBinaryReader",
    "KEYBinaryWriter",
    "KeyEntry",
    "bytes_key",
    "detect_key",
    "read_key",
    "write_key",
]
