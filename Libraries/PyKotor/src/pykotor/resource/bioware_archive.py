from __future__ import annotations

from abc import ABC, abstractmethod
from copy import copy
from enum import Enum
from typing import TYPE_CHECKING, Dict, List, TypeVar, cast

from pykotor.common.misc import ResRef
from pykotor.extract.file import ResourceIdentifier

if TYPE_CHECKING:
    from typing import ClassVar

    from typing_extensions import Self

    from pykotor.resource.formats.bif.bif_data import BIF
    from pykotor.resource.formats.erf.erf_data import ERF
    from pykotor.resource.formats.rim.rim_data import RIM
    from pykotor.resource.type import ResourceType

B = TypeVar("B")


class HashAlgo(Enum):
    NONE = 0
    CRC32 = 1
    FNV32 = 2
    FNV64 = 3
    JENKINS = 4



class ArchiveResource:
    def __init__(
        self,
        resref: ResRef,
        restype: ResourceType,
        data: bytes,
    ):
        self.resref: ResRef = resref
        self.restype: ResourceType = restype
        if isinstance(data, bytearray):
            data = bytes(data)
        self.data: bytes = data

    def __eq__(self, other):
        if self is other or hash(self) == hash(other):
            return True
        if not isinstance(other, ArchiveResource):
            return NotImplemented
        return (
            self.resref == other.resref
            and self.restype == other.restype
            and self.data == other.data
        )

    def __hash__(self):
        return hash((self.resref, self.restype, self.data))

    def identifier(self) -> ResourceIdentifier:
        return ResourceIdentifier(str(self.resref), self.restype)



class BiowareArchive(ABC):
    BINARY_TYPE: ClassVar[ResourceType]
    ARCHIVE_TYPE: type[ArchiveResource] = ArchiveResource

    def __init__(self):
        self._resources = []
        self._resource_dict = {}

    @abstractmethod
    def get_resource_offset(self, resource: ArchiveResource) -> int:
        ...

    def __repr__(self):
        return f"{self.__class__.__name__}(resources=[{self._resources!r}])"

    def __iter__(self):
        yield from self._resources.copy()

    def __len__(self):
        return len(self._resources)

    def __getitem__(self, item):
        if isinstance(item, int):
            return copy(self._resources[item])
        if isinstance(item, str):
            item = ResourceIdentifier.from_path(item)
        return copy(self._resource_dict[item])

    def __contains__(self, item):
        return item in self._resource_dict

    def __setitem__(self, key: str | ResourceIdentifier, value: ArchiveResource):
        if isinstance(key, str):
            key = ResourceIdentifier(key, value.restype)
        self._resource_dict[key] = value
        if value not in self._resources:
            self._resources.append(value)

    def __delitem__(self, key: str | ResourceIdentifier):
        if isinstance(key, str):
            key = ResourceIdentifier.from_path(key)
        self._resources.remove(cast(Dict[ResourceIdentifier, ArchiveResource], self._resource_dict).pop(key))

    def __add__(self, other) -> Self:  # noqa: ANN001
        if not isinstance(other, BiowareArchive):
            return NotImplemented

        combined_archive = self.__class__()
        resource: ArchiveResource
        for resource in self:
            combined_archive.set_data(str(resource.resref), resource.restype, resource.data)
        for resource in other:
            combined_archive.set_data(str(resource.resref), resource.restype, resource.data)

        return combined_archive

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, BiowareArchive):
            return NotImplemented
        return set(self._resources) == set(other._resources)

    def set_data(
        self,
        resname: str,
        restype: ResourceType,
        data: bytes,
    ):
        resource: ArchiveResource | None = next(
            (
                resource
                for resource in cast(List[ArchiveResource], self._resources)
                if resource.resref == resname and resource.restype == restype
            ),
            None,
        )
        if resource is None:
            resource = self.ARCHIVE_TYPE(ResRef(resname), restype, data)
            self._resources.append(resource)
            self._resource_dict[resource.identifier()] = resource
        else:
            resource.data = data

    def get(self, resname: str, restype: ResourceType) -> bytes | None:
        resource_dict = cast(Dict[ResourceIdentifier, ArchiveResource], self._resource_dict)
        resource: ArchiveResource | None = resource_dict.get(ResourceIdentifier(resname, restype), None)
        return None if resource is None else resource.data

    def remove(
        self,
        resname: str,
        restype: ResourceType,
    ):
        key = ResourceIdentifier(resname, restype)
        self._resources.remove(self._resource_dict.pop(key, None))

    def find_resource_by_hash(self, h: int) -> int | None:
        return next(
            (
                i
                for i, resource in enumerate(self._resources)
                if hash(resource) == h
            ),
            None,
        )

    def to_bif(
        self,
    ) -> BIF:
        from pykotor.resource.formats.bif.bif_data import BIF  # Prevent circular imports

        bif = BIF()
        for resource in cast(List[ArchiveResource], self._resources):
            bif.set_data(str(resource.resref), resource.restype, resource.data)
        return bif

    def to_erf(
        self,
    ) -> ERF:
        from pykotor.resource.formats.erf.erf_data import ERF  # Prevent circular imports

        erf = ERF()
        for resource in cast(List[ArchiveResource], self._resources):
            erf.set_data(str(resource.resref), resource.restype, resource.data)
        return erf

    def to_rim(
        self,
    ) -> RIM:
        from pykotor.resource.formats.rim.rim_data import RIM  # Prevent circular imports

        rim = RIM()
        for resource in cast(List[ArchiveResource], self._resources):
            rim.set_data(str(resource.resref), resource.restype, resource.data)
        return rim
