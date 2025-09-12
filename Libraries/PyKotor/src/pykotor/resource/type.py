"""This module contains the ResourceType class and initializes the static list of ResourceTypes that can be found in both games."""

from __future__ import annotations

import io
import mmap
import os
import struct
import uuid

from enum import Enum
from functools import lru_cache
from typing import TYPE_CHECKING, NamedTuple, TypeVar, Union
from xml.etree.ElementTree import ParseError

from pykotor.common.stream import BinaryReader, BinaryWriter
from utility.string_util import WrappedStr

if TYPE_CHECKING:
    from collections.abc import Callable

    from pykotor.common.stream import BinaryWriterBytearray, BinaryWriterFile

STREAM_TYPES = Union[io.BufferedIOBase, io.RawIOBase, mmap.mmap]
BASE_SOURCE_TYPES = Union[os.PathLike, str, bytes, bytearray, memoryview]
SOURCE_TYPES = Union[BASE_SOURCE_TYPES, STREAM_TYPES]
TARGET_TYPES = Union[os.PathLike, str, bytearray, BinaryWriter]


class ResourceReader:
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        self._reader: BinaryReader = BinaryReader.from_auto(source, offset)
        self._size: int = self._reader.remaining() if size == 0 else size

    def close(
        self,
    ):
        self._reader.close()


class ResourceWriter:
    def __init__(
        self,
        target: TARGET_TYPES,
    ):
        self._writer: BinaryWriterFile | BinaryWriterBytearray = BinaryWriter.to_auto(target)

    def close(
        self,
    ):
        self._writer.close()


class ResourceTuple(NamedTuple):
    type_id: int
    extension: str
    category: str
    contents: str
    is_invalid: bool = False
    target_member: str | None = None


class ResourceType(Enum):
    """Represents a resource type that is used within either games.

    Stored in the class is also several static attributes, each an actual resource type used by the games.

    Attributes:
    ----------
        type_id: Integer id of the resource type as recognized by the games.
        extension: File extension associated with the resource type and as recognized by the game.
        category: Short description on what kind of data the resource type stores.
        contents: How the resource type stores data, ie. plaintext, binary, or gff.

    """

    INVALID = ResourceTuple(-1, "", "Undefined", "binary", is_invalid=True)  # pyright: ignore[reportCallIssue]
    RES = ResourceTuple(0, "res", "Save Data", "gff")  # pyright: ignore[reportCallIssue]
    BMP = ResourceTuple(1, "bmp", "Images", "binary")  # pyright: ignore[reportCallIssue]
    MVE = ResourceTuple(2, "mve", "Video", "video")  # Video, Infinity Engine  # pyright: ignore[reportCallIssue]
    TGA = ResourceTuple(3, "tga", "Textures", "binary")  # pyright: ignore[reportCallIssue]
    WAV = ResourceTuple(4, "wav", "Audio", "binary")  # pyright: ignore[reportCallIssue]
    PLT = ResourceTuple(6, "plt", "Other", "binary")  # pyright: ignore[reportCallIssue]
    INI = ResourceTuple(7, "ini", "Text Files", "plaintext")  # swkotor.ini  # pyright: ignore[reportCallIssue]
    BMU = ResourceTuple(8, "bmu", "Audio", "binary")  # mp3 with obfuscated extra header  # pyright: ignore[reportCallIssue]
    MPG = ResourceTuple(9, "mpg", "Video", "binary")  # pyright: ignore[reportCallIssue]
    TXT = ResourceTuple(10, "txt", "Text Files", "plaintext")  # pyright: ignore[reportCallIssue]
    WMA = ResourceTuple(11, "wma", "Audio", "binary")  # pyright: ignore[reportCallIssue]
    WMV = ResourceTuple(12, "wmv", "Audio", "binary")  # pyright: ignore[reportCallIssue]
    XMV = ResourceTuple(13, "xmv", "Audio", "binary")  # Xbox video  # pyright: ignore[reportCallIssue]
    PLH = ResourceTuple(2000, "plh", "Models", "binary")  # pyright: ignore[reportCallIssue]
    TEX = ResourceTuple(2001, "tex", "Textures", "binary")  # pyright: ignore[reportCallIssue]
    MDL = ResourceTuple(2002, "mdl", "Models", "binary")  # pyright: ignore[reportCallIssue]
    THG = ResourceTuple(2003, "thg", "Unused", "binary")  # pyright: ignore[reportCallIssue]
    FNT = ResourceTuple(2005, "fnt", "Font", "binary")  # pyright: ignore[reportCallIssue]
    LUA = ResourceTuple(2007, "lua", "Scripts", "plaintext")  # pyright: ignore[reportCallIssue]
    SLT = ResourceTuple(2008, "slt", "Unused", "binary")  # pyright: ignore[reportCallIssue]
    NSS = ResourceTuple(2009, "nss", "Scripts", "plaintext")  # pyright: ignore[reportCallIssue]
    NCS = ResourceTuple(2010, "ncs", "Scripts", "binary")  # pyright: ignore[reportCallIssue]
    MOD = ResourceTuple(2011, "mod", "Modules", "binary")  # pyright: ignore[reportCallIssue]
    ARE = ResourceTuple(2012, "are", "Module Data", "gff")  # pyright: ignore[reportCallIssue]
    SET = ResourceTuple(2013, "set", "Unused", "binary")  # pyright: ignore[reportCallIssue]
    IFO = ResourceTuple(2014, "ifo", "Module Data", "gff")  # pyright: ignore[reportCallIssue]
    BIC = ResourceTuple(2015, "bic", "Creatures", "gff")  # pyright: ignore[reportCallIssue]
    WOK = ResourceTuple(2016, "wok", "Walkmeshes", "binary")  # pyright: ignore[reportCallIssue]
    TwoDA = ResourceTuple(2017, "2da", "2D Arrays", "binary")  # pyright: ignore[reportCallIssue]
    TLK = ResourceTuple(2018, "tlk", "Talk Tables", "binary")  # pyright: ignore[reportCallIssue]
    TXI = ResourceTuple(2022, "txi", "Textures", "plaintext")  # pyright: ignore[reportCallIssue]
    GIT = ResourceTuple(2023, "git", "Module Data", "gff")  # pyright: ignore[reportCallIssue]
    BTI = ResourceTuple(2024, "bti", "Items", "gff")  # pyright: ignore[reportCallIssue]
    UTI = ResourceTuple(2025, "uti", "Items", "gff")  # pyright: ignore[reportCallIssue]
    BTC = ResourceTuple(2026, "btc", "Creatures", "gff")  # pyright: ignore[reportCallIssue]
    UTC = ResourceTuple(2027, "utc", "Creatures", "gff")  # pyright: ignore[reportCallIssue]
    DLG = ResourceTuple(2029, "dlg", "Dialogs", "gff")  # pyright: ignore[reportCallIssue]
    ITP = ResourceTuple(2030, "itp", "Palettes", "binary")  # pyright: ignore[reportCallIssue]
    BTT = ResourceTuple(2031, "btt", "Triggers", "gff")  # pyright: ignore[reportCallIssue]
    UTT = ResourceTuple(2032, "utt", "Triggers", "gff")  # pyright: ignore[reportCallIssue]
    DDS = ResourceTuple(2033, "dds", "Textures", "binary")  # pyright: ignore[reportCallIssue]
    UTS = ResourceTuple(2035, "uts", "Sounds", "gff")  # pyright: ignore[reportCallIssue]
    LTR = ResourceTuple(2036, "ltr", "Other", "binary")  # pyright: ignore[reportCallIssue]
    GFF = ResourceTuple(2037, "gff", "Other", "gff")  # pyright: ignore[reportCallIssue]
    FAC = ResourceTuple(2038, "fac", "Factions", "gff")  # pyright: ignore[reportCallIssue]
    BTE = ResourceTuple(2039, "bte", "Encounters", "gff")  # pyright: ignore[reportCallIssue]
    UTE = ResourceTuple(2040, "ute", "Encounters", "gff")  # pyright: ignore[reportCallIssue]
    BTD = ResourceTuple(2041, "btd", "Doors", "gff")  # pyright: ignore[reportCallIssue]
    UTD = ResourceTuple(2042, "utd", "Doors", "gff")  # pyright: ignore[reportCallIssue]
    BTP = ResourceTuple(2043, "btp", "Placeables", "gff")  # pyright: ignore[reportCallIssue]
    UTP = ResourceTuple(2044, "utp", "Placeables", "gff")  # pyright: ignore[reportCallIssue]
    DFT = ResourceTuple(2045, "dft", "Defaults", "binary")  # pyright: ignore[reportCallIssue]
    DTF = ResourceTuple(2045, "dft", "Defaults", "plaintext")  # pyright: ignore[reportCallIssue]
    GIC = ResourceTuple(2046, "gic", "Module Data", "gff")  # pyright: ignore[reportCallIssue]
    GUI = ResourceTuple(2047, "gui", "GUIs", "gff")  # pyright: ignore[reportCallIssue]
    BTM = ResourceTuple(2050, "btm", "Merchants", "gff")  # pyright: ignore[reportCallIssue]
    UTM = ResourceTuple(2051, "utm", "Merchants", "gff")  # pyright: ignore[reportCallIssue]
    DWK = ResourceTuple(2052, "dwk", "Walkmeshes", "binary")  # pyright: ignore[reportCallIssue]
    PWK = ResourceTuple(2053, "pwk", "Walkmeshes", "binary")  # pyright: ignore[reportCallIssue]
    JRL = ResourceTuple(2056, "jrl", "Journals", "gff")  # pyright: ignore[reportCallIssue]
    SAV = ResourceTuple(2057, "sav", "Save Data", "erf")  # pyright: ignore[reportCallIssue]
    UTW = ResourceTuple(2058, "utw", "Waypoints", "gff")  # pyright: ignore[reportCallIssue]
    FourPC = ResourceTuple(2059, "4pc", "Textures", "binary")  # RGBA 16-bit  # pyright: ignore[reportCallIssue]
    SSF = ResourceTuple(2060, "ssf", "Soundsets", "binary")  # pyright: ignore[reportCallIssue]
    HAK = ResourceTuple(2061, "hak", "Modules", "erf")  # pyright: ignore[reportCallIssue]
    NWM = ResourceTuple(2062, "nwm", "Modules", "erf")  # pyright: ignore[reportCallIssue]
    BIK = ResourceTuple(2063, "bik", "Videos", "binary")  # pyright: ignore[reportCallIssue]
    NDB = ResourceTuple(2064, "ndb", "Other", "binary")  # pyright: ignore[reportCallIssue]
    PTM = ResourceTuple(2065, "ptm", "Other", "binary")  # pyright: ignore[reportCallIssue]
    PTT = ResourceTuple(2066, "ptt", "Other", "binary")  # pyright: ignore[reportCallIssue]
    NCM = ResourceTuple(2067, "ncm", "Unused", "binary")  # pyright: ignore[reportCallIssue]
    MFX = ResourceTuple(2068, "mfx", "Unused", "binary")  # pyright: ignore[reportCallIssue]
    MAT = ResourceTuple(2069, "mat", "Materials", "binary")  # pyright: ignore[reportCallIssue]
    MDB = ResourceTuple(2070, "mdb", "Models", "binary")  # pyright: ignore[reportCallIssue]
    SAY = ResourceTuple(2071, "say", "Unused", "binary")  # pyright: ignore[reportCallIssue]
    TTF = ResourceTuple(2072, "ttf", "Fonts", "binary")  # pyright: ignore[reportCallIssue]
    TTC = ResourceTuple(2073, "ttc", "Unused", "binary")  # pyright: ignore[reportCallIssue]
    CUT = ResourceTuple(2074, "cut", "Cutscenes", "gff")  # pyright: ignore[reportCallIssue]
    KA  = ResourceTuple(2075, "ka", "Unused", "xml")  # noqa: E221  # pyright: ignore[reportCallIssue]
    JPG = ResourceTuple(2076, "jpg", "Images", "binary")  # pyright: ignore[reportCallIssue]
    ICO = ResourceTuple(2077, "ico", "Images", "binary")  # pyright: ignore[reportCallIssue]
    OGG = ResourceTuple(2078, "ogg", "Audio", "binary")  # pyright: ignore[reportCallIssue]
    SPT = ResourceTuple(2079, "spt", "Unused", "binary")  # pyright: ignore[reportCallIssue]
    SPW = ResourceTuple(2080, "spw", "Unused", "binary")  # pyright: ignore[reportCallIssue]
    WFX = ResourceTuple(2081, "wfx", "Unused", "xml")  # pyright: ignore[reportCallIssue]
    UGM = ResourceTuple(2082, "ugm", "Unused", "binary")  # pyright: ignore[reportCallIssue]
    QDB = ResourceTuple(2083, "qdb", "Unused", "gff")  # pyright: ignore[reportCallIssue]
    QST = ResourceTuple(2084, "qst", "Unused", "gff")  # pyright: ignore[reportCallIssue]
    NPC = ResourceTuple(2085, "npc", "Unused", "binary")  # pyright: ignore[reportCallIssue]
    SPN = ResourceTuple(2086, "spn", "Unused", "binary")  # pyright: ignore[reportCallIssue]
    UTX = ResourceTuple(2087, "utx", "Unused", "binary")  # pyright: ignore[reportCallIssue]
    MMD = ResourceTuple(2088, "mmd", "Unused", "binary")  # pyright: ignore[reportCallIssue]
    SMM = ResourceTuple(2089, "smm", "Unused", "binary")  # pyright: ignore[reportCallIssue]
    UTA = ResourceTuple(2090, "uta", "Unused", "binary")  # pyright: ignore[reportCallIssue]
    MDE = ResourceTuple(2091, "mde", "Unused", "binary")  # pyright: ignore[reportCallIssue]
    MDV = ResourceTuple(2092, "mdv", "Unused", "binary")  # pyright: ignore[reportCallIssue]
    MDA = ResourceTuple(2093, "mda", "Unused", "binary")  # pyright: ignore[reportCallIssue]
    MBA = ResourceTuple(2094, "mba", "Unused", "binary")  # pyright: ignore[reportCallIssue]
    OCT = ResourceTuple(2095, "oct", "Unused", "binary")  # pyright: ignore[reportCallIssue]
    BFX = ResourceTuple(2096, "bfx", "Unused", "binary")  # pyright: ignore[reportCallIssue]
    PDB = ResourceTuple(2097, "pdb", "Unused", "binary")  # pyright: ignore[reportCallIssue]
    PVS = ResourceTuple(2099, "pvs", "Unused", "binary")  # pyright: ignore[reportCallIssue]
    CFX = ResourceTuple(2100, "cfx", "Unused", "binary")  # pyright: ignore[reportCallIssue]
    LUC = ResourceTuple(2101, "luc", "Scripts", "binary")  # pyright: ignore[reportCallIssue]
    PNG = ResourceTuple(2110, "png", "Images", "binary")  # pyright: ignore[reportCallIssue]
    LYT = ResourceTuple(3000, "lyt", "Module Data", "plaintext")  # pyright: ignore[reportCallIssue]
    VIS = ResourceTuple(3001, "vis", "Module Data", "plaintext")  # pyright: ignore[reportCallIssue]
    RIM = ResourceTuple(3002, "rim", "Modules", "binary")  # pyright: ignore[reportCallIssue]
    PTH = ResourceTuple(3003, "pth", "Paths", "gff")  # pyright: ignore[reportCallIssue]
    LIP = ResourceTuple(3004, "lip", "Lips", "lips")  # pyright: ignore[reportCallIssue]
    TPC = ResourceTuple(3007, "tpc", "Textures", "binary")  # pyright: ignore[reportCallIssue]
    MDX = ResourceTuple(3008, "mdx", "Models", "binary")  # pyright: ignore[reportCallIssue]
    CWA = ResourceTuple(3027, "cwa", "Crowd Attributes", "gff")  # pyright: ignore[reportCallIssue]
    BIP = ResourceTuple(3028, "bip", "Lips", "lips")  # pyright: ignore[reportCallIssue]
    ERF = ResourceTuple(9997, "erf", "Modules", "binary")  # pyright: ignore[reportCallIssue]
    BIF = ResourceTuple(9998, "bif", "Archives", "binary")  # pyright: ignore[reportCallIssue]
    KEY = ResourceTuple(9999, "key", "Chitin", "binary")  # pyright: ignore[reportCallIssue]

    # For Toolset Use:
    MP3 = ResourceTuple(25014, "mp3", "Audio", "binary")  # pyright: ignore[reportCallIssue]
    TLK_XML = ResourceTuple(50001, "tlk.xml", "Talk Tables", "plaintext")  # pyright: ignore[reportCallIssue]
    MDL_ASCII = ResourceTuple(50002, "mdl.ascii", "Models", "plaintext")  # pyright: ignore[reportCallIssue]
    TwoDA_CSV = ResourceTuple(50003, "2da.csv", "2D Arrays", "plaintext")  # pyright: ignore[reportCallIssue]
    GFF_XML = ResourceTuple(50004, "gff.xml", "Other", "plaintext", target_member="GFF")  # pyright: ignore[reportCallIssue]
    GFF_JSON = ResourceTuple(50005, "gff.json", "Other", "plaintext", target_member="GFF")  # pyright: ignore[reportCallIssue]
    IFO_XML = ResourceTuple(50006, "ifo.xml", "Module Data", "plaintext", target_member="IFO")  # pyright: ignore[reportCallIssue]
    GIT_XML = ResourceTuple(50007, "git.xml", "Module Data", "plaintext", target_member="GIT")  # pyright: ignore[reportCallIssue]
    UTI_XML = ResourceTuple(50008, "uti.xml", "Items", "plaintext", target_member="UTI")  # pyright: ignore[reportCallIssue]
    UTC_XML = ResourceTuple(50009, "utc.xml", "Creatures", "plaintext", target_member="UTC")  # pyright: ignore[reportCallIssue]
    DLG_XML = ResourceTuple(50010, "dlg.xml", "Dialogs", "plaintext", target_member="DLG")  # pyright: ignore[reportCallIssue]
    ITP_XML = ResourceTuple(50011, "itp.xml", "Palettes", "plaintext")  # pyright: ignore[reportCallIssue]
    UTT_XML = ResourceTuple(50012, "utt.xml", "Triggers", "plaintext", target_member="UTT")  # pyright: ignore[reportCallIssue]
    UTS_XML = ResourceTuple(50013, "uts.xml", "Sounds", "plaintext", target_member="UTS")  # pyright: ignore[reportCallIssue]
    FAC_XML = ResourceTuple(50014, "fac.xml", "Factions", "plaintext", target_member="FAC")  # pyright: ignore[reportCallIssue]
    UTE_XML = ResourceTuple(50015, "ute.xml", "Encounters", "plaintext", target_member="UTE")  # pyright: ignore[reportCallIssue]
    UTD_XML = ResourceTuple(50016, "utd.xml", "Doors", "plaintext", target_member="UTD")  # pyright: ignore[reportCallIssue]
    UTP_XML = ResourceTuple(50017, "utp.xml", "Placeables", "plaintext", target_member="UTP")  # pyright: ignore[reportCallIssue]
    GUI_XML = ResourceTuple(50018, "gui.xml", "GUIs", "plaintext", target_member="GUI")  # pyright: ignore[reportCallIssue]
    UTM_XML = ResourceTuple(50019, "utm.xml", "Merchants", "plaintext", target_member="UTM")  # pyright: ignore[reportCallIssue]
    JRL_XML = ResourceTuple(50020, "jrl.xml", "Journals", "plaintext", target_member="JRL")  # pyright: ignore[reportCallIssue]
    UTW_XML = ResourceTuple(50021, "utw.xml", "Waypoints", "plaintext", target_member="UTW")  # pyright: ignore[reportCallIssue]
    PTH_XML = ResourceTuple(50022, "pth.xml", "Paths", "plaintext", target_member="PTH")  # pyright: ignore[reportCallIssue]
    LIP_XML = ResourceTuple(50023, "lip.xml", "Lips", "plaintext", target_member="LIP")  # pyright: ignore[reportCallIssue]
    SSF_XML = ResourceTuple(50024, "ssf.xml", "Soundsets", "plaintext", target_member="SSF")  # pyright: ignore[reportCallIssue]
    ARE_XML = ResourceTuple(50025, "are.xml", "Module Data", "plaintext", target_member="ARE")  # pyright: ignore[reportCallIssue]
    TwoDA_JSON = ResourceTuple(50026, "2da.json", "2D Arrays", "plaintext", target_member="TwoDA")  # pyright: ignore[reportCallIssue]
    TLK_JSON = ResourceTuple(50027, "tlk.json", "Talk Tables", "plaintext", target_member="TLK")  # pyright: ignore[reportCallIssue]
    LIP_JSON = ResourceTuple(50028, "lip.json", "Lips", "plaintext", target_member="LIP")  # pyright: ignore[reportCallIssue]
    RES_XML = ResourceTuple(50029, "res.xml", "Save Data", "plaintext", target_member="RES")  # pyright: ignore[reportCallIssue]

    def __new__(cls, *args, **kwargs):
        obj: ResourceType = object.__new__(cls)  # type: ignore[annotation-unchecked]
        name = args[1].upper() or "INVALID"
        while name in cls.__members__:
            name = f"{name}_{uuid.uuid4().hex}"
        obj._name_ = name
        obj.__init__(*args, **kwargs)  # type: ignore[misc]
        return super().__new__(cls, obj)

    def __init__(
        self,
        type_id: int,
        extension: str,
        category: str,
        contents: str,
        is_invalid: bool = False,  # noqa: FBT001, FBT002
        target_member: str | None = None,
    ):
        self.type_id: int = type_id
        self.extension: str = extension.strip().lower()
        self.category: str = category
        self.contents: str = contents
        self.is_invalid: bool = is_invalid
        self.target_member: str | None = target_member

    def is_gff(self) -> bool:
        """Returns True if this resourcetype is a gff, excluding the xml/json abstractions, False otherwise."""
        return self.contents == "gff"

    def target_type(self):
        return self if self.target_member is None else self.__class__.__members__[self.target_member]

    def __bool__(self) -> bool:
        return not self.is_invalid

    def __repr__(
        self,
    ) -> str:  # sourcery skip: simplify-fstring-formatting
        if self.name == "INVALID" or not self.is_invalid:
            return f"{self.__class__.__name__}.{self.name}"

        return (  # For dynamically constructed invalid members
            f"{self.__class__.__name__}.from_invalid("
            f"{f'type_id={self.type_id}, '}"
            f"{f'extension={self.extension}, ' if self.extension else ''}"
            f"{f'category={self.category}, ' if self.category else ''}"
            f"contents={self.contents})"
        )

    def __str__(
        self,
    ) -> str:
        """Returns the extension in all caps."""
        return str(self.extension.upper())

    def __int__(
        self,
    ):
        """Returns the type_id."""
        return self.type_id

    def __eq__(
        self,
        other: ResourceType | str | int | object,
    ):
        """Two ResourceTypes are equal if they are the same.

        A ResourceType and a str are equal if the extension is case-sensitively equal to the string.
        A ResourceType and a int are equal if the type_id is equal to the integer.
        """
        # sourcery skip: assign-if-exp, merge-duplicate-blocks, reintroduce-else, remove-redundant-if, split-or-ifs
        if self is other:
            return True
        if isinstance(other, ResourceType):
            if self.is_invalid or other.is_invalid:
                return self.is_invalid and other.is_invalid
            return self.name == other.name
        if isinstance(other, (str, WrappedStr)):
            return self.extension == other.lower()
        if isinstance(other, int):
            return self.type_id == other
        return NotImplemented

    def __hash__(self):
        return hash(self.extension)

    @classmethod
    @lru_cache(maxsize=0xFFFF)
    def from_id(
        cls,
        type_id: int | str,
    ) -> ResourceType:
        """Returns the ResourceType for the specified id.

        Args:
        ----
            type_id: The resource id.

        Returns:
        -------
            The corresponding ResourceType object.
        """
        if isinstance(type_id, str):
            type_id = int(type_id)

        return next(
            (restype for restype in ResourceType.__members__.values() if type_id == restype),
            ResourceType.from_invalid(type_id=type_id),
        )

    @classmethod
    def from_extension(
        cls,
        extension: str,
    ) -> ResourceType:
        """Returns the ResourceType for the specified extension.

        This will slice off the leading dot in the extension, if it exists.

        Args:
        ----
            extension: The resource's extension. This is case-insensitive

        Returns:
        -------
            The corresponding ResourceType object.
        """
        lower_ext: str = extension.lower()
        if lower_ext.startswith("."):
            lower_ext = lower_ext[1:]
        return next(
            (restype for restype in ResourceType.__members__.values() if lower_ext == restype.extension),
            ResourceType.from_invalid(extension=lower_ext),
        )

    @classmethod
    def from_invalid(
        cls,
        **kwargs,
    ):
        if not kwargs:
            return cls.INVALID
        instance = object.__new__(cls)
        name = f"INVALID_{kwargs.get('extension', kwargs.get('type_id', cls.INVALID.extension)) or uuid.uuid4().hex}"
        while name in cls.__members__:
            name = f"INVALID_{kwargs.get('extension', kwargs.get('type_id', cls.INVALID.extension))}{uuid.uuid4().hex}"
        instance._name_ = name
        instance._value_ = ResourceTuple(
            type_id=kwargs.get("type_id", cls.INVALID.type_id),
            extension=kwargs.get("extension", cls.INVALID.extension),
            category=kwargs.get("category", cls.INVALID.category),
            contents=kwargs.get("contents", cls.INVALID.contents),
            is_invalid=kwargs.get("is_invalid", cls.INVALID.is_invalid),
            target_member=kwargs.get("target_member", cls.INVALID.target_member)
        )
        instance.__init__(
            type_id=kwargs.get("type_id", cls.INVALID.type_id),
            extension=kwargs.get("extension", cls.INVALID.extension),
            category=kwargs.get("category", cls.INVALID.category),
            contents=kwargs.get("contents", cls.INVALID.contents),
            is_invalid=kwargs.get("is_invalid", cls.INVALID.is_invalid),
            target_member=kwargs.get("target_member", cls.INVALID.target_member)
        )
        return super().__new__(cls, instance)

    def validate(self):
        if not self:
            msg = f"Invalid ResourceType: '{self!r}'"
            raise ValueError(msg)
        return self


R = TypeVar("R")


def autoclose(func: Callable[..., R]) -> Callable[..., R]:
    def _autoclose(self: ResourceReader | ResourceWriter, auto_close: bool = True) -> R:  # noqa: FBT002, FBT001
        try:
            resource: R = func(self, auto_close)
        except (OSError, ParseError, ValueError, IndexError, StopIteration, struct.error) as e:
            msg = "Tried to save or load an unsupported or corrupted file."
            raise ValueError(msg) from e
        finally:
            if auto_close:
                self.close()
        return resource

    return _autoclose
