"""Dialog system for handling game conversations."""
from __future__ import annotations

from pykotor.resource.generics.dlg.anims import DLGAnimation
from pykotor.resource.generics.dlg.base import DLG, DLGComputerType, DLGConversationType
from pykotor.resource.generics.dlg.nodes import DLGEntry, DLGNode, DLGReply
from pykotor.resource.generics.dlg.links import DLGLink
from pykotor.resource.generics.dlg.stunts import DLGStunt
from pykotor.resource.generics.dlg.io.gff import construct_dlg, dismantle_dlg, read_dlg, write_dlg, bytes_dlg
from pykotor.resource.generics.dlg.io.twine import read_twine, write_twine
from pykotor.resource.generics.dlg.io.twine_data import TwineLink, TwinePassage, TwineStory, PassageMetadata, TwineMetadata, FormatConverter

__all__ = [
    "DLG",
    "DLGAnimation",
    "DLGComputerType",
    "DLGConversationType",
    "DLGEntry",
    "DLGLink",
    "DLGNode",
    "DLGReply",
    "DLGStunt",
    "FormatConverter",
    "PassageMetadata",
    "TwineLink",
    "TwineMetadata",
    "TwinePassage",
    "TwineStory",
    "bytes_dlg",
    "construct_dlg",
    "dismantle_dlg",
    "read_dlg",
    "read_twine",
    "write_dlg",
    "write_twine",
]
