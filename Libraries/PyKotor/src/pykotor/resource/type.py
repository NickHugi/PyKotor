"""This module contains the ResourceType class and initializes the static list of ResourceTypes that can be found in both games."""
from __future__ import annotations

import os
import uuid
from enum import Enum
from typing import Iterable, NamedTuple, Union
from xml.etree.ElementTree import ParseError

from pykotor.common.stream import BinaryReader, BinaryWriter

SOURCE_TYPES = Union[os.PathLike, str, bytes, bytearray, BinaryReader]
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
        self._writer: BinaryWriter = BinaryWriter.to_auto(target)

    def close(
        self,
    ) -> None:
        self._writer.close()

class ResourceTuple(NamedTuple):
    type_id: int
    extension: str
    category: str
    contents: str
    is_invalid: bool = False

    def __getitem__(self, key):
        return getattr(self, key)

    def keys(self) -> Iterable[str]:
        return self._fields


class ResourceType(Enum):
    """Represents a resource type that is used within either games.

    Stored in the class is also several static attributes, each an actual resource type used by the games.

    Attributes
    ----------
        type_id: Integer id of the resource type as recognized by the games.
        extension: File extension associated with the resource type and as recognized by the game.
        category: Short description on what kind of data the resource type stores.
        contents: How the resource type stores data, ie. plaintext, binary, or gff.
    """

    INVALID = ResourceTuple(0, "", "Undefined", "binary", is_invalid=True)
    BMP = ResourceTuple(1, "bmp", "Images", "binary")
    TGA = ResourceTuple(3, "tga", "Textures", "binary")
    WAV = ResourceTuple(4, "wav", "Audio", "binary")
    PLT = ResourceTuple(6, "plt", "Other", "binary")
    INI = ResourceTuple(7, "ini", "Text Files", "plaintext")
    TXT = ResourceTuple(10, "txt", "Text Files", "plaintext")
    MDL = ResourceTuple(2002, "mdl", "Models", "binary")
    NSS = ResourceTuple(2009, "nss", "Scripts", "plaintext")
    NCS = ResourceTuple(2010, "ncs", "Scripts", "binary")
    MOD = ResourceTuple(2011, "mod", "Modules", "binary")
    ARE = ResourceTuple(2012, "are", "Module Data", "gff")
    SET = ResourceTuple(2013, "set", "Unused", "binary")
    IFO = ResourceTuple(2014, "ifo", "Module Data", "gff")
    BIC = ResourceTuple(2015, "bic", "Creatures", "binary")
    WOK = ResourceTuple(2016, "wok", "Walkmeshes", "binary")
    TwoDA = ResourceTuple(2017, "2da", "2D Arrays", "binary")
    TLK = ResourceTuple(2018, "tlk", "Talk Tables", "binary")
    TXI = ResourceTuple(2022, "txi", "Textures", "plaintext")
    GIT = ResourceTuple(2023, "git", "Module Data", "gff")
    BTI = ResourceTuple(2024, "bti", "Items", "gff")
    UTI = ResourceTuple(2025, "uti", "Items", "gff")
    BTC = ResourceTuple(2026, "btc", "Creatures", "gff")
    UTC = ResourceTuple(2027, "utc", "Creatures", "gff")
    DLG = ResourceTuple(2029, "dlg", "Dialogs", "gff")
    ITP = ResourceTuple(2030, "itp", "Palettes", "binary")
    UTT = ResourceTuple(2032, "utt", "Triggers", "gff")
    DDS = ResourceTuple(2033, "dds", "Textures", "binary")
    UTS = ResourceTuple(2035, "uts", "Sounds", "gff")
    LTR = ResourceTuple(2036, "ltr", "Other", "binary")
    GFF = ResourceTuple(2037, "gff", "Other", "gff")
    FAC = ResourceTuple(2038, "fac", "Factions", "gff")
    UTE = ResourceTuple(2040, "ute", "Encounters", "gff")
    UTD = ResourceTuple(2042, "utd", "Doors", "gff")
    UTP = ResourceTuple(2044, "utp", "Placeables", "gff")
    DFT = ResourceTuple(2045, "dft", "Other", "binary")
    GIC = ResourceTuple(2046, "gic", "Module Data", "gff")
    GUI = ResourceTuple(2047, "gui", "GUIs", "gff")
    UTM = ResourceTuple(2051, "utm", "Merchants", "gff")
    DWK = ResourceTuple(2052, "dwk", "Walkmeshes", "binary")
    PWK = ResourceTuple(2053, "pwk", "Walkmeshes", "binary")
    JRL = ResourceTuple(2056, "jrl", "Journals", "gff")
    UTW = ResourceTuple(2058, "utw", "Waypoints", "gff")
    SSF = ResourceTuple(2060, "ssf", "Soundsets", "binary")
    NDB = ResourceTuple(2064, "ndb", "Other", "binary")
    PTM = ResourceTuple(2065, "ptm", "Other", "binary")
    PTT = ResourceTuple(2066, "ptt", "Other", "binary")
    JPG = ResourceTuple(2076, "jpg", "Images", "binary")
    PNG = ResourceTuple(2110, "png", "Images", "binary")
    LYT = ResourceTuple(3000, "lyt", "Module Data", "plaintext")
    VIS = ResourceTuple(3001, "vis", "Module Data", "plaintext")
    RIM = ResourceTuple(3002, "rim", "Modules", "binary")
    PTH = ResourceTuple(3003, "pth", "Paths", "gff")
    LIP = ResourceTuple(3004, "lip", "Lips", "lips")
    TPC = ResourceTuple(3007, "tpc", "Textures", "binary")
    MDX = ResourceTuple(3008, "mdx", "Models", "binary")
    ERF = ResourceTuple(9997, "erf", "Modules", "binary")
    RES = ResourceTuple(69420, "res", "Save Data", "gff")
    SAV = ResourceTuple(42069, "sav", "Save Data", "erf")

    # For Toolset Use:
    MP3 = ResourceTuple(25014, "mp3", "Audio", "binary")
    TLK_XML = ResourceTuple(50001, "tlk.xml", "Talk Tables", "plaintext")
    MDL_ASCII = ResourceTuple(50002, "mdl.ascii", "Models", "plaintext")
    TwoDA_CSV = ResourceTuple(50003, "2da.csv", "2D Arrays", "plaintext")
    GFF_XML = ResourceTuple(50004, "gff.xml", "Other", "plaintext")
    IFO_XML = ResourceTuple(50005, "ifo.xml", "Module Data", "plaintext")
    GIT_XML = ResourceTuple(50006, "git.xml", "Module Data", "plaintext")
    UTI_XML = ResourceTuple(50007, "uti.xml", "Items", "plaintext")
    UTC_XML = ResourceTuple(50008, "utc.xml", "Creatures", "plaintext")
    DLG_XML = ResourceTuple(50009, "dlg.xml", "Dialogs", "plaintext")
    ITP_XML = ResourceTuple(50010, "itp.xml", "Palettes", "plaintext")
    UTT_XML = ResourceTuple(50011, "utt.xml", "Triggers", "plaintext")
    UTS_XML = ResourceTuple(50012, "uts.xml", "Sounds", "plaintext")
    FAC_XML = ResourceTuple(50013, "fac.xml", "Factions", "plaintext")
    UTE_XML = ResourceTuple(50014, "ute.xml", "Encounters", "plaintext")
    UTD_XML = ResourceTuple(50015, "utd.xml", "Doors", "plaintext")
    UTP_XML = ResourceTuple(50016, "utp.xml", "Placeables", "plaintext")
    GUI_XML = ResourceTuple(50017, "gui.xml", "GUIs", "plaintext")
    UTM_XML = ResourceTuple(50018, "utm.xml", "Merchants", "plaintext")
    JRL_XML = ResourceTuple(50019, "jrl.xml", "Journals", "plaintext")
    UTW_XML = ResourceTuple(50020, "utw.xml", "Waypoints", "plaintext")
    PTH_XML = ResourceTuple(50021, "pth.xml", "Paths", "plaintext")
    LIP_XML = ResourceTuple(50022, "lip.xml", "Lips", "plaintext")
    SSF_XML = ResourceTuple(50023, "ssf.xml", "Soundsets", "plaintext")
    ARE_XML = ResourceTuple(50023, "are.xml", "Module Data", "plaintext")
    TwoDA_JSON = ResourceTuple(50024, "2da.json", "2D Arrays", "plaintext")
    TLK_JSON = ResourceTuple(50025, "tlk.json", "Talk Tables", "plaintext")
    LIP_JSON = ResourceTuple(50026, "lip.json", "Lips", "plaintext")

    def __new__(cls, *args, **kwargs):
        obj: ResourceType = object.__new__(cls)  # type: ignore[annotation-unchecked]
        name = args[1].upper() or "INVALID"
        while name in cls.__members__:
            name = f"{name}_{uuid.uuid4().hex}"
        obj._name_ = name
        obj.__init__(*args, **kwargs)
        return super().__new__(cls, obj)

    def __init__(
        self,
        type_id: int,
        extension: str,
        category: str,
        contents: str,
        is_invalid: bool = False,
    ):
        self.type_id: int = type_id
        self.extension: str = extension.lower().strip()
        self.category: str = category
        self.contents: str = contents
        self.is_invalid: bool = is_invalid
        self._is_initialized = True

    def __bool__(self) -> bool:
        return not self.is_invalid

    def __repr__(
        self,
    ) -> str:
        return f"ResourceType.{self.name}"

    def __str__(
        self,
    ):
        """Returns the extension in all caps."""
        return self.extension.upper()

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
        if isinstance(other, ResourceType):
            if self.is_invalid or other.is_invalid:
                return self.is_invalid and other.is_invalid
            return self.name == other.name
        if isinstance(other, str):
            return self.extension == other.lower()
        if isinstance(other, int):
            return self.type_id == other
        return NotImplemented

    def __hash__(self):
        return hash((self.__class__, str(self.extension).lower()))

    @classmethod
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
            (
                restype
                for restype in ResourceType.__members__.values()
                if type_id == restype
            ),
            ResourceType.from_invalid(type_id=type_id),
        )

    def validate(self):
        if not self:
            msg = f"Could not find resource type with extension '{self.extension}' ID '{self.type_id}'"
            raise ValueError(msg)
        return self

    @classmethod
    def from_invalid(
        cls,
        **kwargs,
    ):
        if not kwargs:
            return cls.INVALID
        instance = object.__new__(cls)
        name = f"INVALID_{kwargs.get('extension', cls.INVALID.extension) or uuid.uuid4().hex}"
        while name in cls.__members__:
            name = f"INVALID_{kwargs.get('extension', cls.INVALID.extension)}{uuid.uuid4().hex}"
        instance._name_ = name
        instance._value_ = ResourceTuple(**{**cls.INVALID.value, **kwargs, "is_invalid": True})
        instance.__init__(**instance.value)
        return super().__new__(cls, instance)

    @classmethod
    def from_extension(
        cls,
        extension: str,
    ) -> ResourceType:
        """Returns the ResourceType for the specified extension.

        This will slice off the leading dot in the extension, if it exists.

        Args:
        ----
            extension: The resource extension.

        Returns:
        -------
            The corresponding ResourceType object.
        """
        lower_ext: str = extension.lower()
        if extension.startswith("."):
            lower_ext = lower_ext[1:]
        return next(
            (
                restype
                for restype in ResourceType.__members__.values()
                if lower_ext == restype.extension
            ),
            ResourceType.from_invalid(extension=lower_ext),
        )


def autoclose(func):
    def _autoclose(self: ResourceReader | ResourceWriter, auto_close: bool = True):
        try:
            resource = func(self, auto_close)
        except (OSError, ParseError, ValueError, IndexError, StopIteration) as e:
            msg = "Tried to load an unsupported or corrupted file."
            raise ValueError(msg) from e
        finally:
            if auto_close:
                self.close()
        return resource

    return _autoclose
