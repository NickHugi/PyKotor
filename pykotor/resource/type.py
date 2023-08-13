"""This module contains the ResourceType class and initializes the static list of ResourceTypes that can be found in both
games.
"""
from __future__ import annotations

from abc import ABC
from pykotor.tools.path import Path
from typing import Union, overload
from xml.etree.ElementTree import ParseError

from pykotor.common.stream import BinaryReader, BinaryWriter

SOURCE_TYPES = Union[Path, str, bytes, bytearray, BinaryReader]
TARGET_TYPES = Union[Path, str, bytearray, BinaryWriter]


class ResourceReader(ABC):
    @overload
    def __init__(
        self,
        filepath: str | Path,
        offset: int = 0,
        size: int = 0,
    ):
        ...

    @overload
    def __init__(
        self,
        data: bytes,
        offset: int = 0,
        size: int = 0,
    ):
        ...

    @overload
    def __init__(
        self,
        reader: BinaryReader,
        offset: int = 0,
        size: int = 0,
    ):
        ...

    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        self._reader = BinaryReader.from_auto(source, offset)
        self._size = self._reader.remaining() if size == 0 else size

    def close(
        self,
    ):
        self._reader.close()


class ResourceWriter(ABC):
    @overload
    def __init__(
        self,
        filepath: str | Path,
    ):
        ...

    @overload
    def __init__(
        self,
        data: bytes,
    ):
        ...

    @overload
    def __init__(
        self,
        reader: BinaryWriter,
    ):
        ...

    def __init__(
        self,
        target: TARGET_TYPES,
    ):
        self._writer = BinaryWriter.to_auto(target)

    def close(
        self,
    ):
        self._writer.close()


class ResourceType:
    """Represents a resource type that is used within either games.

    Stored in the class is also several static attributes, each an actual resource type used by the games.

    Attributes
    ----------
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
    TLK_XML: ResourceType
    MDL_ASCII: ResourceType
    TwoDA_CSV: ResourceType
    GFF_XML: ResourceType
    IFO_XML: ResourceType
    GIT_XML: ResourceType
    UTI_XML: ResourceType
    UTC_XML: ResourceType
    DLG_XML: ResourceType
    ITP_XML: ResourceType
    UTT_XML: ResourceType
    UTS_XML: ResourceType
    FAC_XML: ResourceType
    UTE_XML: ResourceType
    UTD_XML: ResourceType
    UTP_XML: ResourceType
    GUI_XML: ResourceType
    UTM_XML: ResourceType
    JRL_XML: ResourceType
    UTW_XML: ResourceType
    PTH_XML: ResourceType
    LIP_XML: ResourceType
    SSF_XML: ResourceType
    ARE_XML: ResourceType
    TwoDA_JSON: ResourceType
    TLK_JSON: ResourceType

    def __init__(
        self,
        type_id: int,
        extension: str,
        category: str,
        contents: str,
    ):
        self.type_id = type_id
        self.extension = extension
        self.category = category
        self.contents = contents

    def __repr__(
        self,
    ):
        if self is ResourceType.TwoDA:
            return "ResourceType.TwoDA"
        elif self is ResourceType.INVALID:
            return "ResourceType.INVALID"
        else:
            return f"ResourceType.{self.extension.upper()}"

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
        other: ResourceType | str | int,
    ):
        """Two ResourceTypes are equal if they are the same.
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

    def __hash__(
        self,
    ):
        return hash(str(self.extension))

    @classmethod
    def from_id(
        cls,
        type_id: int,
    ) -> ResourceType:
        """Returns the ResourceType for the specified id.

        Args:
        ----
            type_id: The resource id.

        Returns:
        -------
            The corresponding ResourceType object.
        """
        for value in ResourceType.__dict__.values():
            if value == type_id:
                return value
        msg = f"Could not find resource type with ID {type_id}."
        raise ValueError(msg)

    @classmethod
    def from_extension(
        cls,
        extension: str,
    ) -> ResourceType:
        """Returns the ResourceType for the specified extension.

        Args:
        ----
            extension: The resource extension.

        Returns:
        -------
            The corresponding ResourceType object.
        """
        for resource_type in ResourceType.__annotations__:
            if not isinstance(ResourceType.__dict__[resource_type], ResourceType):
                continue
            if (
                ResourceType.__dict__[resource_type].extension.upper()
                == extension.upper()
            ):
                return ResourceType.__dict__[resource_type]
        msg = f"Could not find resource type with extension '{extension}'."
        raise ValueError(msg)


def autoclose(func):
    def _autoclose(self: ResourceReader | ResourceWriter, auto_close: bool = True):
        try:
            resource = func(self, auto_close)
        except (OSError, ParseError, ValueError, IndexError, StopIteration) as e:
            msg = "Tried to load an unsupported or corrupted file."
            raise ValueError(msg, e)
        finally:
            if auto_close:
                self.close()
        return resource

    return _autoclose


ResourceType.INVALID = ResourceType(0, "", "Undefined", "binary")
ResourceType.BMP = ResourceType(1, "bmp", "Images", "binary")
ResourceType.TGA = ResourceType(3, "tga", "Textures", "binary")
ResourceType.WAV = ResourceType(4, "wav", "Audio", "binary")
ResourceType.PLT = ResourceType(6, "plt", "Other", "binary")
ResourceType.INI = ResourceType(7, "ini", "Text Files", "plaintext")
ResourceType.TXT = ResourceType(10, "txt", "Text Files", "plaintext")
ResourceType.MDL = ResourceType(2002, "mdl", "Models", "binary")
ResourceType.NSS = ResourceType(2009, "nss", "Scripts", "plaintext")
ResourceType.NCS = ResourceType(2010, "ncs", "Scripts", "binary")
ResourceType.MOD = ResourceType(2011, "mod", "Modules", "binary")
ResourceType.ARE = ResourceType(2012, "are", "Module Data", "gff")
ResourceType.SET = ResourceType(2013, "set", "Unused", "binary")
ResourceType.IFO = ResourceType(2014, "ifo", "Module Data", "gff")
ResourceType.BIC = ResourceType(2015, "bic", "Creatures", "binary")
ResourceType.WOK = ResourceType(2016, "wok", "Walkmeshes", "binary")
ResourceType.TwoDA = ResourceType(2017, "2da", "2D Arrays", "binary")
ResourceType.TLK = ResourceType(2018, "tlk", "Talk Tables", "binary")
ResourceType.TXI = ResourceType(2022, "txi", "Textures", "plaintext")
ResourceType.GIT = ResourceType(2023, "git", "Module Data", "gff")
ResourceType.BTI = ResourceType(2024, "bti", "Items", "gff")
ResourceType.UTI = ResourceType(2025, "uti", "Items", "gff")
ResourceType.BTC = ResourceType(2026, "btc", "Creatures", "gff")
ResourceType.UTC = ResourceType(2027, "utc", "Creatures", "gff")
ResourceType.DLG = ResourceType(2029, "dlg", "Dialogs", "gff")
ResourceType.ITP = ResourceType(2030, "itp", "Palettes", "binary")
ResourceType.UTT = ResourceType(2032, "utt", "Triggers", "gff")
ResourceType.DDS = ResourceType(2033, "dds", "Textures", "binary")
ResourceType.UTS = ResourceType(2035, "uts", "Sounds", "gff")
ResourceType.LTR = ResourceType(2036, "ltr", "Other", "binary")
ResourceType.GFF = ResourceType(2037, "gff", "Other", "gff")
ResourceType.FAC = ResourceType(2038, "fac", "Factions", "gff")
ResourceType.UTE = ResourceType(2040, "ute", "Encounters", "gff")
ResourceType.UTD = ResourceType(2042, "utd", "Doors", "gff")
ResourceType.UTP = ResourceType(2044, "utp", "Placeables", "gff")
ResourceType.DFT = ResourceType(2045, "dft", "Other", "binary")
ResourceType.GIC = ResourceType(2046, "gic", "Module Data", "gff")
ResourceType.GUI = ResourceType(2047, "gui", "GUIs", "gff")
ResourceType.UTM = ResourceType(2051, "utm", "Merchants", "gff")
ResourceType.DWK = ResourceType(2052, "dwk", "Walkmeshes", "binary")
ResourceType.PWK = ResourceType(2053, "pwk", "Walkmeshes", "binary")
ResourceType.JRL = ResourceType(2056, "jrl", "Journals", "gff")
ResourceType.UTW = ResourceType(2058, "utw", "Waypoints", "gff")
ResourceType.SSF = ResourceType(2060, "ssf", "Soundsets", "binary")
ResourceType.NDB = ResourceType(2064, "ndb", "Other", "binary")
ResourceType.PTM = ResourceType(2065, "ptm", "Other", "binary")
ResourceType.PTT = ResourceType(2066, "ptt", "Other", "binary")
ResourceType.JPG = ResourceType(2076, "jpg", "Images", "binary")
ResourceType.PNG = ResourceType(2110, "png", "Images", "binary")
ResourceType.LYT = ResourceType(3000, "lyt", "Module Data", "plaintext")
ResourceType.VIS = ResourceType(3001, "vis", "Module Data", "plaintext")
ResourceType.RIM = ResourceType(3002, "rim", "Modules", "binary")
ResourceType.PTH = ResourceType(3003, "pth", "Paths", "gff")
ResourceType.LIP = ResourceType(3004, "lip", "Lips", "lips")
ResourceType.TPC = ResourceType(3007, "tpc", "Textures", "binary")
ResourceType.MDX = ResourceType(3008, "mdx", "Models", "binary")
ResourceType.ERF = ResourceType(9997, "erf", "Modules", "binary")

# For Toolset Use:
ResourceType.MP3 = ResourceType(25014, "mp3", "Audio", "binary")
ResourceType.TLK_XML = ResourceType(50001, "tlk.xml", "Talk Tables", "plaintext")
ResourceType.MDL_ASCII = ResourceType(50002, "mdl.ascii", "Models", "plaintext")
ResourceType.TwoDA_CSV = ResourceType(50003, "2da.csv", "2D Arrays", "plaintext")
ResourceType.GFF_XML = ResourceType(50004, "gff.xml", "Other", "plaintext")
ResourceType.IFO_XML = ResourceType(50005, "ifo.xml", "Module Data", "plaintext")
ResourceType.GIT_XML = ResourceType(50006, "git.xml", "Module Data", "plaintext")
ResourceType.UTI_XML = ResourceType(50007, "uti.xml", "Items", "plaintext")
ResourceType.UTC_XML = ResourceType(50008, "utc.xml", "Creatures", "plaintext")
ResourceType.DLG_XML = ResourceType(50009, "dlg.xml", "Dialogs", "plaintext")
ResourceType.ITP_XML = ResourceType(50010, "itp.xml", "Palettes", "plaintext")
ResourceType.UTT_XML = ResourceType(50011, "utt.xml", "Triggers", "plaintext")
ResourceType.UTS_XML = ResourceType(50012, "uts.xml", "Sounds", "plaintext")
ResourceType.FAC_XML = ResourceType(50013, "fac.xml", "Factions", "plaintext")
ResourceType.UTE_XML = ResourceType(50014, "ute.xml", "Encounters", "plaintext")
ResourceType.UTD_XML = ResourceType(50015, "utd.xml", "Doors", "plaintext")
ResourceType.UTP_XML = ResourceType(50016, "utp.xml", "Placeables", "plaintext")
ResourceType.GUI_XML = ResourceType(50017, "gui.xml", "GUIs", "plaintext")
ResourceType.UTM_XML = ResourceType(50018, "utm.xml", "Merchants", "plaintext")
ResourceType.JRL_XML = ResourceType(50019, "jrl.xml", "Journals", "plaintext")
ResourceType.UTW_XML = ResourceType(50020, "utw.xml", "Waypoints", "plaintext")
ResourceType.PTH_XML = ResourceType(50021, "pth.xml", "Paths", "plaintext")
ResourceType.LIP_XML = ResourceType(50022, "lip.xml", "Lips", "plaintext")
ResourceType.SSF_XML = ResourceType(50023, "ssf.xml", "Soundsets", "plaintext")
ResourceType.ARE_XML = ResourceType(50023, "are.xml", "Module Data", "plaintext")
ResourceType.TwoDA_JSON = ResourceType(50024, "2da.json", "2D Arrays", "plaintext")
ResourceType.TLK_JSON = ResourceType(50024, "tlk.json", "Talk Tables", "plaintext")
