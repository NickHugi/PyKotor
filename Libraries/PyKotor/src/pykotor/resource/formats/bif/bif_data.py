"""This module handles classes relating to editing BIF/BZF files."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from pykotor.common.misc import ResRef
from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.bioware_archive import ArchiveResource, BiowareArchive
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_bif_file, is_bzf_file

if TYPE_CHECKING:
    import os


class BIFType(Enum):
    """The type of BIF. More specifically, the first 4 bytes in the file header."""
    BIF = "BIFF"
    BZF = "BZF "

    @classmethod
    def from_extension(cls, ext_or_filepath: os.PathLike | str) -> BIFType:
        if is_bif_file(ext_or_filepath):
            return cls.BIF
        if is_bzf_file(ext_or_filepath):
            return cls.BZF
        msg = f"'{ext_or_filepath}' is not a valid BZF/BIF file extension."
        raise ValueError(msg)


class BIF(BiowareArchive):
    """Represents the data of a BIF/BZF file.

    Attributes:
    ----------
        bif_type: The BIF type.
    """

    BINARY_TYPE = ResourceType.BIF

    def __init__(
        self,
        bif_type: BIFType = BIFType.BIF,
    ):
        self._resources: list[BIFResource] = []
        self._resource_dict: dict[ResourceIdentifier, BIFResource] = {}
        super().__init__()
        self.bif_type: BIFType = bif_type

    def set_data(self, resname: str, restype: ResourceType, data: bytes):
        res = BIFResource(ResRef(resname), restype, data)
        self._resources.append(res)
        self._resource_dict[ResourceIdentifier(resname, restype)] = res

    def get_resource_offset(self, resource: BIFResource) -> int:
        return NotImplementedError("Not implemented at this time.")


class BIFResource(ArchiveResource):
    def __init__(self, resref: ResRef, restype: ResourceType, data: bytes):
        super().__init__(resref=resref, restype=restype, data=data)


class BZFResource(BIFResource):
    def __init__(self, resref: ResRef, restype: ResourceType, data: bytes):
        super().__init__(resref=resref, restype=restype, data=data)
        self.packed_size: int = 0
