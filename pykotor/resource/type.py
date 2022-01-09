"""
This module contains the ResourceType class and initializes the static list of ResourceTypes that can be found in both
games.
"""
from __future__ import annotations

from abc import ABC
from enum import Enum
from typing import Union, overload

from pykotor.common.stream import BinaryReader, BinaryWriter

SOURCE_TYPES = Union[str, bytes, bytearray, BinaryReader]
TARGET_TYPES = Union[str, bytearray, BinaryWriter]


class FileFormat(Enum):
    INVALID = "invalid"
    BINARY = "binary"
    ASCII = "ascii"
    XML = "xml"
    CSV = "csv"


class ResourceReader(ABC):
    @overload
    def __init__(self, filepath: str, offset: int = 0, size: int = 0):
        ...

    @overload
    def __init__(self, data: bytes, offset: int = 0, size: int = 0):
        ...

    @overload
    def __init__(self, data: bytearray, offset: int = 0, size: int = 0):
        ...

    @overload
    def __init__(self, reader: BinaryReader, offset: int = 0, size: int = 0):
        ...

    def __init__(self, source: Union[str, bytes, bytearray, BinaryReader], offset: int = 0, size: int = 0):
        self._reader = BinaryReader.from_auto(source, offset)
        self._size = self._reader.remaining() if size == 0 else size


class ResourceWriter(ABC):
    @overload
    def __init__(self, filepath: str):
        ...

    @overload
    def __init__(self, data: bytes):
        ...

    @overload
    def __init__(self, data: bytearray):
        ...

    @overload
    def __init__(self, reader: BinaryWriter):
        ...

    def __init__(self, target: Union[str, bytearray, BinaryReader]):
        self._writer = BinaryWriter.to_auto(target)


class ResourceType:
    """
    Represents a resource type that is used within either games.

    Stored in the class is also several static attributes, each an actual resource type used by the games.

    Attributes:
        type_id: Integer id of the resource type as recognized by the games.
        extension: File extension associated with the resource type and as recognized by the game.
        category: Short description on what kind of data the resource type stores.
        contents: How the resource type stores data, ie. plaintext, binary, or gff.
    """

    # For PyCharm type hints
    INVALID: ResourceType
    BMP: ResourceType
    TGA: ResourceType
    WAV: ResourceType
    PLT: ResourceType
    INI: ResourceType
    TXT: ResourceType
    MDL: ResourceType
    NSS: ResourceType
    NCS: ResourceType
    MOD: ResourceType
    ARE: ResourceType
    SET: ResourceType
    IFO: ResourceType
    BIC: ResourceType
    WOK: ResourceType
    TwoDA: ResourceType
    TLK: ResourceType
    TXI: ResourceType
    GIT: ResourceType
    BTI: ResourceType
    UTI: ResourceType
    BTC: ResourceType
    UTC: ResourceType
    DLG: ResourceType
    ITP: ResourceType
    UTT: ResourceType
    DDS: ResourceType
    UTS: ResourceType
    LTR: ResourceType
    GFF: ResourceType
    FAC: ResourceType
    UTE: ResourceType
    UTD: ResourceType
    UTP: ResourceType
    DFT: ResourceType
    GIC: ResourceType
    GUI: ResourceType
    UTM: ResourceType
    DWK: ResourceType
    PWK: ResourceType
    JRL: ResourceType
    UTW: ResourceType
    SSF: ResourceType
    NDB: ResourceType
    PTM: ResourceType
    PTT: ResourceType
    JPG: ResourceType
    PNG: ResourceType
    LYT: ResourceType
    VIS: ResourceType
    RIM: ResourceType
    PTH: ResourceType
    LIP: ResourceType
    TPC: ResourceType
    MDX: ResourceType
    ERF: ResourceType
    MP3: ResourceType

    def __init__(self, type_id: int, extension: str, category: str, contents: str):
        self.type_id = type_id
        self.extension = extension
        self.category = category
        self.contents = contents

    def __repr__(self):
        if self is ResourceType.TwoDA:
            return "ResourceType.TwoDA"
        elif self is ResourceType.INVALID:
            return "ResourceType.INVALID"
        else:
            return "ResourceType.{}".format(self.extension.upper())

    def __str__(self):
        """
        Returns the extension in all caps.
        """
        return self.extension.upper()

    def __int__(self):
        """
        Returns the type_id.
        """
        return self.type_id

    def __eq__(self, other: Union[ResourceType, str, int]):
        """
        Two ResourceTypes are equal if they are the same.
        A ResourceType and a str are equal if the extension is equal to the string.
        A ResourceType and a int are equal if the type_id is equal to the integer.
        """
        if type(other) is ResourceType:
            return self is other
        elif type(other) is str:
            return self.extension == other
        elif type(other) is int:
            return self.type_id == other
        else:
            return NotImplemented

    @classmethod
    def from_id(cls, type_id: int) -> ResourceType:
        """
        Returns the ResourceType for the specified id.

        Args:
            type_id: The resource id.

        Returns:
            The corresponding ResourceType object.
        """
        for value in ResourceType.__dict__.values():
            if value == type_id:
                return value

    @classmethod
    def from_extension(cls, extension: str) -> ResourceType:
        """
        Returns the ResourceType for the specified extension.

        Args:
            extension: The resource extension.

        Returns:
            The corresponding ResourceType object.
        """
        for value in ResourceType.__dict__.values():
            if value == extension:
                return value


ResourceType.INVALID = ResourceType(0,      "",     "Undefined",    "binary")
ResourceType.BMP    = ResourceType(1,       "bmp",  "Images",       "binary")
ResourceType.TGA    = ResourceType(3,       "tga",  "Textures",     "binary")
ResourceType.WAV    = ResourceType(4,       "wav",  "Audio",        "binary")
ResourceType.PLT    = ResourceType(6,       "plt",  "Other",        "binary")
ResourceType.INI    = ResourceType(7,       "ini",  "Other",        "plaintext")
ResourceType.TXT    = ResourceType(10,      "txt",  "Other",        "plaintext")
ResourceType.MDL    = ResourceType(2002,    "mdl",  "Models",       "binary")
ResourceType.NSS    = ResourceType(2009,    "nss",  "Scripts",      "plaintext")
ResourceType.NCS    = ResourceType(2010,    "ncs",  "Scripts",      "binary")
ResourceType.MOD    = ResourceType(2011,    "mod",  "Module",       "binary")
ResourceType.ARE    = ResourceType(2012,    "are",  "Area Data",    "gff")
ResourceType.SET    = ResourceType(2013,    "set",  "Unknown",      "binary")
ResourceType.IFO    = ResourceType(2014,    "ifo",  "Module Data",  "gff")
ResourceType.BIC    = ResourceType(2015,    "bic",  "Unknown",      "binary")
ResourceType.WOK    = ResourceType(2016,    "wok",  "Walkmeshes",   "binary")
ResourceType.TwoDA  = ResourceType(2017,    "2da",  "2D Arrays",    "binary")
ResourceType.TLK    = ResourceType(2018,    "tlk",  "Talk Files",   "binary")
ResourceType.TXI    = ResourceType(2022,    "txi",  "Textures",     "plaintext")
ResourceType.GIT    = ResourceType(2023,    "git",  "Module Data",  "gff")
ResourceType.BTI    = ResourceType(2024,    "bti",  "Items",        "gff")
ResourceType.UTI    = ResourceType(2025,    "uti",  "Items",        "gff")
ResourceType.BTC    = ResourceType(2026,    "btc",  "Creature",     "gff")
ResourceType.UTC    = ResourceType(2027,    "utc",  "Creature",     "gff")
ResourceType.DLG    = ResourceType(2029,    "dlg",  "Dialog",       "gff")
ResourceType.ITP    = ResourceType(2030,    "itp",  "Other",        "binary")
ResourceType.UTT    = ResourceType(2032,    "utt",  "Trigger",      "gff")
ResourceType.DDS    = ResourceType(2033,    "dds",  "Textures",     "binary")
ResourceType.UTS    = ResourceType(2035,    "uts",  "Sounds",       "gff")
ResourceType.LTR    = ResourceType(2036,    "ltr",  "Other",        "binary")
ResourceType.GFF    = ResourceType(2037,    "gff",  "Other",        "gff")
ResourceType.FAC    = ResourceType(2038,    "fac",  "Factions",     "gff")
ResourceType.UTE    = ResourceType(2040,    "ute",  "Encounters",   "gff")
ResourceType.UTD    = ResourceType(2042,    "utd",  "Doors",        "gff")
ResourceType.UTP    = ResourceType(2044,    "utp",  "Placeables",   "gff")
ResourceType.DFT    = ResourceType(2045,    "dft",  "Other",        "binary")
ResourceType.GIC    = ResourceType(2046,    "gic",  "Module Data",  "gff")
ResourceType.GUI    = ResourceType(2047,    "gui",  "GUIs",         "gff")
ResourceType.UTM    = ResourceType(2051,    "utm",  "Merchants",    "gff")
ResourceType.DWK    = ResourceType(2052,    "dwk",  "Walkmeshes",   "binary")
ResourceType.PWK    = ResourceType(2053,    "pwk",  "Walkmeshes",   "binary")
ResourceType.JRL    = ResourceType(2056,    "jrl",  "Journals",     "gff")
ResourceType.UTW    = ResourceType(2058,    "utw",  "Waypoints",    "gff")
ResourceType.SSF    = ResourceType(2060,    "ssf",  "Soundsets",    "binary")
ResourceType.NDB    = ResourceType(2064,    "ndb",  "Other",        "binary")
ResourceType.PTM    = ResourceType(2065,    "ptm",  "Other",        "binary")
ResourceType.PTT    = ResourceType(2066,    "ptt",  "Other",        "binary")
ResourceType.JPG    = ResourceType(2076,    "jpg",  "Images",       "binary")
ResourceType.PNG    = ResourceType(2110,    "png",  "Images",       "binary")
ResourceType.LYT    = ResourceType(3000,    "lyt",  "Module Data",  "plaintext")
ResourceType.VIS    = ResourceType(3001,    "vis",  "Module Data",  "plaintext")
ResourceType.RIM    = ResourceType(3002,    "rim",  "Module",       "binary")
ResourceType.PTH    = ResourceType(3003,    "pth",  "Paths",        "gff")
ResourceType.LIP    = ResourceType(3004,    "lip",  "Lip Syncs",    "lips")
ResourceType.TPC    = ResourceType(3007,    "tpc",  "Textures",     "binary")
ResourceType.MDX    = ResourceType(3008,    "mdx",  "Model",       "binary")
ResourceType.ERF    = ResourceType(9997,    "ssf",  "Archive",      "binary")
ResourceType.MP3    = ResourceType(25014,   "mp3",  "Audio",        "binary")
