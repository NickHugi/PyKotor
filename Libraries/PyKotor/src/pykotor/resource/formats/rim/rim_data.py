"""This module handles classes relating to editing RIM files."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.bioware_archive import ArchiveResource, BiowareArchive
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.common.misc import ResRef


class RIMResource(ArchiveResource):
    """A resource stored inside a RIM archive."""

    def __init__(self, resref: ResRef, restype: ResourceType, data: bytes):
        super().__init__(resref=resref, restype=restype, data=data)


class RIM(BiowareArchive):
    """Represents the data of a RIM file."""

    BINARY_TYPE = ResourceType.RIM
    ARCHIVE_TYPE: type[ArchiveResource] = RIMResource
    COMPARABLE_SET_FIELDS = ("_resources",)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(resources={len(self._resources)})"

    def get(self, resname: str, restype: ResourceType) -> bytes | None:
        """Return the raw bytes for a resource, or None when not present."""
        resource = self._resource_dict.get(ResourceIdentifier(resname, restype))
        return None if resource is None else resource.data

    def remove(self, resname: str, restype: ResourceType) -> None:
        """Remove a resource from the archive if it exists."""
        key = ResourceIdentifier(resname, restype)
        resource = self._resource_dict.pop(key, None)
        if resource is not None:
            self._resources.remove(resource)

    def to_erf(self):
        """Return an ERF archive with the same resource payload."""
        from pykotor.resource.formats.erf.erf_data import ERF  # Prevent circular imports  # noqa: PLC0415

        erf = ERF()
        for resource in self._resources:
            erf.set_data(str(resource.resref), resource.restype, resource.data)
        return erf

    def get_resource_offset(self, resource: ArchiveResource) -> int:
        """Compute the binary offset for a given resource when serialised."""
        if not isinstance(resource, RIMResource):
            raise TypeError("Resource is not a RIMResource")
        from pykotor.resource.formats.rim.io_rim import RIMBinaryWriter  # noqa: PLC0415

        entry_count = len(self._resources)
        offset_to_keys = RIMBinaryWriter.FILE_HEADER_SIZE
        data_start = offset_to_keys + RIMBinaryWriter.KEY_ELEMENT_SIZE * entry_count

        resource_index = self._resources.index(resource)
        return data_start + sum(len(res.data) for res in self._resources[:resource_index])

    def __eq__(self, other: object):
        from pykotor.resource.formats.erf.erf_data import ERF  # Prevent circular imports  # noqa: PLC0415

        if not isinstance(other, (RIM, ERF)):
            return NotImplemented
        return set(self._resources) == set(other._resources)

    def __hash__(self) -> int:
        return hash(tuple(self._resources))
