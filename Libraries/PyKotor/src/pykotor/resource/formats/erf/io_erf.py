from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.erf.erf_data import ERF, ERFType
from pykotor.resource.type import ResourceReader, ResourceType, ResourceWriter, autoclose

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class ERFBinaryReader(ResourceReader):
    """Reads ERF (Encapsulated Resource File) files.
    
    ERF files are container formats that store multiple game resources. Used for MOD files,
    save games, and other resource collections.
    
    References:
    ----------
        vendor/reone/src/libs/resource/format/erfreader.cpp:26-72 (ERF reading)
        vendor/reone/src/libs/resource/format/erfwriter.cpp (ERF writing)
        vendor/xoreos-tools/src/unerf.cpp:108-145 (password/decryption support)
    
    Missing Features:
    ----------------
        - ResRef lowercasing (reone lowercases at erfreader.cpp:63)
        - ERF password/decryption support (xoreos-tools supports at unerf.cpp:108-145)
    """
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self._erf: ERF | None = None

    @autoclose
    def load(self, *, auto_close: bool = True) -> ERF:  # noqa: FBT001, FBT002, ARG002
        """Load ERF file.

        Args:
        ----
            self: The ERF object

        Returns:
        -------
            ERF: The loaded ERF object

        Processing Logic:
        ----------------
            - Read file header and validate file type and version
            - Read entry count and offsets to keys and resources sections
            - Read keys section into lists of ref, id, type
            - Read resources section into lists of offsets and sizes
            - Seek to each resource and read data into ERF object.
        """
        file_type: str = self._reader.read_string(4)
        file_version: str = self._reader.read_string(4)

        if file_version != "V1.0":
            msg = f"ERF version '{file_version}' is unsupported."
            raise ValueError(msg)

        erf_type: ERFType | None = next(
            (x for x in ERFType if x.value == file_type),
            None,
        )
        if erf_type is None:
            msg = f"Not a valid ERF file: '{file_type}'"
            raise ValueError(msg)

        self._erf = ERF(erf_type)

        self._reader.skip(8)
        entry_count: int = self._reader.read_uint32()
        self._reader.skip(4)
        offset_to_keys: int = self._reader.read_uint32()
        offset_to_resources: int = self._reader.read_uint32()
        self._reader.skip(8)
        description_strref: int = self._reader.read_uint32()
        if description_strref == 0 and file_type == ERFType.MOD.value:  # estimated guess based on observed files
            self._erf.is_save = True

        resrefs: list[str] = []
        resids: list[int] = []
        restypes: list[int] = []
        self._reader.seek(offset_to_keys)
        for _ in range(entry_count):
            # vendor/reone/src/libs/resource/format/erfreader.cpp:62-72
            # reone lowercases resrefs at line 63
            resref_str = self._reader.read_string(16).rstrip("\0")
            resrefs.append(resref_str.lower())
            resids.append(self._reader.read_uint32())
            restypes.append(self._reader.read_uint16())
            self._reader.skip(2)

        resoffsets: list[int] = []
        ressizes: list[int] = []
        self._reader.seek(offset_to_resources)
        for _ in range(entry_count):
            resoffsets.append(self._reader.read_uint32())
            ressizes.append(self._reader.read_uint32())

        for i in range(entry_count):
            self._reader.seek(resoffsets[i])
            resdata: bytes = self._reader.read_bytes(ressizes[i])
            self._erf.set_data(resrefs[i], ResourceType.from_id(restypes[i]), resdata)

        return self._erf


class ERFBinaryWriter(ResourceWriter):
    FILE_HEADER_SIZE = 160
    KEY_ELEMENT_SIZE = 24
    RESOURCE_ELEMENT_SIZE = 8

    def __init__(
        self,
        erf: ERF,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self.erf: ERF = erf

    @autoclose
    def write(self, *, auto_close: bool = True):  # noqa: FBT001, FBT002, ARG002  # pyright: ignore[reportUnusedParameters]
        entry_count: int = len(self.erf)
        offset_to_keys: int = ERFBinaryWriter.FILE_HEADER_SIZE
        offset_to_resources: int = offset_to_keys + ERFBinaryWriter.KEY_ELEMENT_SIZE * entry_count
        offset_to_localized_strings: int = 0x0
        description_strref_dword_value: int = 0xFFFFFFFF
        if self.erf.is_save:
            # might matter.
            offset_to_localized_strings = 0xA0
            description_strref_dword_value = 0x00000000
        elif self.erf.erf_type is ERFType.ERF:
            # default, also doesn't matter
            offset_to_localized_strings = 0x69
            description_strref_dword_value = 0xCDCDCDCD
        elif self.erf.erf_type is ERFType.MOD:
            # mod's aren't in the vanilla game, doesn't matter
            offset_to_localized_strings = 0x0
            description_strref_dword_value = 0xFFFFFFFF

        self._writer.write_string(self.erf.erf_type.value)
        self._writer.write_string("V1.0")
        self._writer.write_uint32(0)
        self._writer.write_uint32(0)
        self._writer.write_uint32(entry_count)
        self._writer.write_uint32(offset_to_localized_strings)
        self._writer.write_uint32(offset_to_keys)
        self._writer.write_uint32(offset_to_resources)
        self._writer.write_uint32(0)
        self._writer.write_uint32(0)
        self._writer.write_uint32(description_strref_dword_value)
        self._writer.write_bytes(b"\0" * 116)

        for resid, resource in enumerate(self.erf):
            self._writer.write_string(str(resource.resref), string_length=16)
            self._writer.write_uint32(resid)
            self._writer.write_uint16(resource.restype.type_id)
            self._writer.write_uint16(0)
        data_offset: int = offset_to_resources + ERFBinaryWriter.RESOURCE_ELEMENT_SIZE * entry_count
        for resource in self.erf:
            self._writer.write_uint32(data_offset)
            self._writer.write_uint32(len(resource.data))
            data_offset += len(resource.data)

        for resource in self.erf:
            self._writer.write_bytes(resource.data)
