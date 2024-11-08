"""Dialog I/O package."""

from __future__ import annotations

from pykotor.resource.generics.dlg.io.gff import construct_dlg, dismantle_dlg, read_dlg, write_dlg, bytes_dlg
from pykotor.resource.generics.dlg.io.twine import read_twine, write_twine
from pykotor.resource.generics.dlg.io.twine_data import FormatConverter, PassageMetadata, PassageType, TwineLink, TwineMetadata, TwinePassage, TwineStory

__all__ = [
    # GFF format
    "construct_dlg",
    "dismantle_dlg",
    
    # Twine format
    "read_twine",
    "write_twine",
    
    # Twine data structures
    "FormatConverter",
    "PassageMetadata",
    "PassageType",
    "TwineLink",
    "TwineMetadata",
    "TwinePassage",
    "TwineStory",
    "read_dlg",
    "write_dlg",
    "bytes_dlg",
]
