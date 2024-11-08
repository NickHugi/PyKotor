"""Dialog system for handling game conversations."""

from __future__ import annotations

from pykotor.resource.generics.dlg.base import DLG, DLGComputerType, DLGConversationType
from pykotor.resource.generics.dlg.nodes import DLGAnimation, DLGEntry, DLGNode, DLGReply
from pykotor.resource.generics.dlg.links import DLGLink
from pykotor.resource.generics.dlg.stunts import DLGStunt
from pykotor.resource.generics.dlg.io.gff import construct_dlg, dismantle_dlg
from pykotor.resource.generics.dlg.io.twine import read_twine, write_twine

__all__ = [
    # Base classes
    "DLG",
    "DLGComputerType",
    "DLGConversationType",
    # Node types
    "DLGNode",
    "DLGEntry",
    "DLGReply",
    "DLGAnimation",
    # Links
    "DLGLink",
    # Stunts
    "DLGStunt",
    # GFF format
    "construct_dlg",
    "dismantle_dlg",
    # Twine format
    "read_twine",
    "write_twine",
]

# Version info
__version__ = "1.0.0"
__author__ = "PyKotor Team"
