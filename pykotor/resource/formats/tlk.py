"""
This module handles classes relating to editing TLK files.
"""
from __future__ import annotations

from typing import List

from pykotor.common.language import Language
from pykotor.common.misc import ResRef
from pykotor.resource.formats.tlk_io import TLKBinaryReader, TLKBinaryWriter
from pykotor.resource.ops import XMLOps, BinaryOps


class TLK(BinaryOps, XMLOps):
    BINARY_READER = TLKBinaryReader
    BINARY_WRITER = TLKBinaryWriter

    def __init__(self):
        self.entries: List[TLKEntry] = []
        self.language: Language = Language.ENGLISH

    def __len__(self):
        return len(self.entries)

    def __iter__(self):
        for stringref, entry in enumerate(self.entries):
            yield stringref, entry

    def __getitem__(self, item):
        if not isinstance(item, int):
            return NotImplemented
        return self.entries[item]

    def get(self, stringref: int):
        return self.entries[stringref] if stringref in self.entries else None

    def resize(self, size: int):
        if len(self) > size:
            self.entries = self.entries[:size]
        else:
            self.entries = [TLKEntry("", ResRef.from_blank()) for _ in range(len(self), size)]


class TLKEntry:
    def __init__(self, text: str, voiceover: ResRef):
        self.text: str = text
        self.voiceover: ResRef = voiceover

    def __eq__(self, other):
        if not isinstance(other, TLKEntry):
            return NotImplemented
        return other.text == self.text and other.voiceover == self.voiceover
