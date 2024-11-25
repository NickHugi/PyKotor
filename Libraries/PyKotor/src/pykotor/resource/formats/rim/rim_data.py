"""This module handles classes relating to editing RIM files."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.bioware_archive import ArchiveResource, BiowareArchive
from pykotor.resource.formats.erf.erf_data import ERF
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.common.misc import ResRef
    from pykotor.extract.file import ResourceIdentifier


class RIMResource(ArchiveResource):
    def __init__(self, resref: ResRef, restype: ResourceType, data: bytes):
        super().__init__(resref=resref, restype=restype, data=data)


class RIM(BiowareArchive):
    """Represents the data of a RIM file."""

    BINARY_TYPE = ResourceType.RIM
    ARCHIVE_TYPE: type[ArchiveResource] = RIMResource

    def __init__(
        self,
    ):
        self._resources: list[RIMResource]
        self._resource_dict: dict[ResourceIdentifier, RIMResource]
        super().__init__()

    def get(
        self,
        resname: str,
        restype: ResourceType,
    ) -> bytes | None:
        """Returns the data of the resource with the specified resref/restype pair if it exists, otherwise returns None.

        Args:
        ----
            resname: The resource reference filename.
            restype: The resource type.

        Returns:
        -------
            The bytes data of the resource or None.
        """
        resource: RIMResource | None = next(
            (resource for resource in self._resources if resource.resref == resname and resource.restype == restype),
            None,
        )
        return None if resource is None else resource.data

    def remove(
        self,
        resname: str,
        restype: ResourceType,
    ):
        """Removes the resource with the given resref/restype pair if it exists.

        Args:
        ----
            resname: The resource reference filename.
            restype: The resource type.
        """
        self._resources = [res for res in self._resources if res.resref != resname and res.restype != restype]

    def to_erf(
        self,
    ):
        """Returns a ERF with the same resources. Defaults to an ERF with ERFType.ERF set.

        Returns:
        -------
            A new ERF object.
        """
        from pykotor.resource.formats.erf import ERF  # Prevent circular imports

        erf = ERF()
        for resource in self._resources:
            erf.set_data(str(resource.resref), resource.restype, resource.data)
        return erf

    def get_resource_offset(
        self,
        resource: ArchiveResource,
    ) -> int:
        if not isinstance(resource, RIMResource):
            raise TypeError("Resource is not a RIMResource")
        from pykotor.resource.formats.rim.io_rim import RIMBinaryWriter

        entry_count: int = len(self._resources)
        offset_to_keys: int = RIMBinaryWriter.FILE_HEADER_SIZE
        data_start: int = offset_to_keys + RIMBinaryWriter.KEY_ELEMENT_SIZE * entry_count

        resource_index: int = self._resources.index(resource)
        offset: int = data_start + sum(len(res.data) for res in self._resources[:resource_index])

        return offset

    def __eq__(
        self,
        other,
    ):
        from pykotor.resource.formats.rim import RIM

        if not isinstance(other, (ERF, RIM)):
            return NotImplemented
        return set(self._resources) == set(other._resources)
