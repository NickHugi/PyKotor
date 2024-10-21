"""This module handles classes relating to editing ERF files."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from pykotor.resource.bioware_archive import ArchiveResource, BiowareArchive
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_erf_file, is_mod_file, is_sav_file

if TYPE_CHECKING:
    import os

    from pykotor.common.misc import ResRef
    from pykotor.extract.file import ResourceIdentifier


class ERFResource(ArchiveResource):
    def __init__(self, resref: ResRef, restype: ResourceType, data: bytes):
        super().__init__(resref=resref, restype=restype, data=data)



class ERFType(Enum):
    """The type of ERF. More specifically, the first 4 bytes in the file header."""

    ERF = "ERF "
    MOD = "MOD "

    @classmethod
    def from_extension(cls, ext_or_filepath: os.PathLike | str) -> ERFType:
        if is_erf_file(ext_or_filepath):
            return cls.ERF
        if is_mod_file(ext_or_filepath):
            return cls.MOD
        if is_sav_file(ext_or_filepath):
            return cls.MOD
        msg = f"Invalid ERF extension in filepath '{ext_or_filepath}'."
        raise ValueError(msg)


class ERF(BiowareArchive):
    """Represents the data of a ERF file.

    Attributes:
    ----------
        erf_type: The ERF type.
    """

    BINARY_TYPE = ResourceType.ERF
    ARCHIVE_TYPE: type[ArchiveResource] = ERFResource

    def __init__(
        self,
        erf_type: ERFType = ERFType.ERF,
        *,
        is_save: bool = False,
    ):
        self._resources: list[ERFResource]
        self._resource_dict: dict[ResourceIdentifier, ERFResource]
        super().__init__()

        self.erf_type: ERFType = erf_type
        self.is_save: bool = is_save

    def __eq__(self, other):
        from pykotor.resource.formats.rim import RIM

        if not isinstance(other, (ERF, RIM)):
            return NotImplemented
        return set(self._resources) == set(other._resources)

    def get_resource_offset(self, resource: ArchiveResource) -> int:
        from pykotor.resource.formats.erf.io_erf import ERFBinaryWriter

        entry_count = len(self._resources)
        offset_to_keys = ERFBinaryWriter.FILE_HEADER_SIZE
        data_start = offset_to_keys + ERFBinaryWriter.KEY_ELEMENT_SIZE * entry_count

        resource_index = self._resources.index(resource)
        offset = data_start + sum(len(res.data) for res in self._resources[:resource_index])

        return offset
