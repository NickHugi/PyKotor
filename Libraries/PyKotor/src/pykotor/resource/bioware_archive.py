from __future__ import annotations

from abc import ABC, abstractmethod
from copy import copy
from enum import Enum
from typing import TYPE_CHECKING, TypeVar, cast

from pykotor.common.misc import ResRef  # type: ignore[import-untyped]
from pykotor.extract.file import ResourceIdentifier  # type: ignore[import-untyped]
from pykotor.resource.formats._base import ComparableMixin  # type: ignore[import-untyped]

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import ClassVar

    from typing_extensions import Self  # pyright: ignore[reportMissingModuleSource]

    from pykotor.resource.formats.bif import BIF  # type: ignore[import-untyped]
    from pykotor.resource.formats.erf import ERF  # type: ignore[import-untyped]
    from pykotor.resource.formats.rim import RIM  # type: ignore[import-untyped]
    from pykotor.resource.type import ResourceType  # type: ignore[import-untyped]

B = TypeVar("B")


class HashAlgo(Enum):
    NONE = 0
    CRC32 = 1
    FNV32 = 2
    FNV64 = 3
    JENKINS = 4


class ArchiveResource:
    """Represents a resource stored within a BioWare archive (ERF, RIM, BIF).
    
    Contains resource reference, type, and data. Used as the base resource type
    for archive-based resource storage.
    
    References:
    ----------
        vendor/KotOR-Bioware-Libs/ERF.pm (Perl ERF resource handling)
        vendor/KotOR-Bioware-Libs/RIM.pm (Perl RIM resource handling)
        vendor/KotOR_IO/KotOR_IO/File Formats/ERF.cs (C# ERF implementation)
        vendor/reone/src/libs/resource/format/erfreader.cpp (ERF reading)
    """
    def __init__(
        self,
        resref: ResRef,
        restype: ResourceType,
        data: bytes,
        size: int | None = None,
    ):
        self.resref: ResRef = resref
        self.restype: ResourceType = restype
        if isinstance(data, bytearray):
            data = bytes(data)
        self.data: bytes = data
        self.size: int = len(data) if size is None else size

    def __eq__(
        self,
        other,  # noqa: ANN001
    ) -> bool:
        if self is other or hash(self) == hash(other):
            return True
        if not isinstance(other, ArchiveResource):
            return NotImplemented
        return self.resref == other.resref and self.restype == other.restype and self.data == other.data

    def __hash__(self):
        return hash((self.resref, self.restype, self.data))

    def identifier(self) -> ResourceIdentifier:
        return ResourceIdentifier(str(self.resref), self.restype)


class BiowareArchive(ComparableMixin, ABC):
    """Abstract base class for BioWare archive formats (ERF, RIM, BIF).
    
    Provides common interface for archive operations including resource storage,
    retrieval, and comparison. Subclasses implement format-specific reading/writing.
    
    References:
    ----------
        vendor/KotOR-Bioware-Libs/ (Perl implementations: ERF.pm, RIM.pm, BIF.pm)
        vendor/KotOR_IO/KotOR_IO/File Formats/ (C# archive implementations)
        vendor/reone/src/libs/resource/format/ (C++ archive readers)
        vendor/xoreos-tools/src/ (Archive extraction tools)
    """
    BINARY_TYPE: ClassVar[ResourceType]
    ARCHIVE_TYPE: type[ArchiveResource] = ArchiveResource
    COMPARABLE_SET_FIELDS = ("_resources",)

    def __init__(self) -> None:
        self._resources: list[ArchiveResource] = []
        self._resource_dict: dict[ResourceIdentifier, ArchiveResource] = {}

    @abstractmethod
    def get_resource_offset(self, resource: ArchiveResource) -> int: ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(resources=[{self._resources!r}])"

    def __iter__(self) -> Iterator[ArchiveResource]:  # noqa: B027
        yield from self._resources.copy()

    def __len__(self) -> int:
        return len(self._resources)

    def __getitem__(
        self,
        item: int | str | ResourceIdentifier,
    ) -> ArchiveResource:
        if isinstance(item, int):
            return copy(self._resources[item])
        if isinstance(item, str):
            item = ResourceIdentifier.from_path(item)
        if not isinstance(item, ResourceIdentifier):
            raise TypeError(f"Expected ResourceIdentifier, got {type(item)}")
        return copy(self._resource_dict[item])

    def __contains__(
        self,
        item: str | ResourceIdentifier,
    ) -> bool:
        return item in self._resource_dict

    def __setitem__(
        self,
        key: str | ResourceIdentifier,
        value: ArchiveResource,
    ):
        if isinstance(key, str):
            key = ResourceIdentifier(key, value.restype)
        self._resource_dict[key] = value
        if value not in self._resources:
            self._resources.append(value)

    def __delitem__(
        self,
        key: str | ResourceIdentifier,
    ):
        if isinstance(key, str):
            key = ResourceIdentifier.from_path(key)
        self._resources.remove(cast(dict[ResourceIdentifier, ArchiveResource], self._resource_dict).pop(key))

    def __add__(
        self,
        other: BiowareArchive,
    ) -> Self:  # noqa: ANN001
        if not isinstance(other, BiowareArchive):
            return NotImplemented

        combined_archive: Self = self.__class__()
        resource: ArchiveResource
        for resource in self:
            combined_archive.set_data(str(resource.resref), resource.restype, resource.data)
        for resource in other:
            combined_archive.set_data(str(resource.resref), resource.restype, resource.data)

        return combined_archive

    def __eq__(
        self,
        other: object,  # noqa: ANN001
    ) -> bool:
        if self is other:
            return True
        if not isinstance(other, BiowareArchive):
            return NotImplemented
        return (
            set(self._resources) == set(other._resources)
            and super().__eq__(other)  # ComparableMixin.__eq__
        )

    def set_resource(
        self,
        resname: str,
        restype: ResourceType,
        data: bytes,
    ):
        self.set_data(resname, restype, data)

    def set_data(
        self,
        resname: str,
        restype: ResourceType,
        data: bytes,
    ) -> None:
        resource: ArchiveResource | None = next(
            (
                resource for resource in cast(list[ArchiveResource], self._resources)
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

    def get(
        self,
        resname: str,
        restype: ResourceType,
    ) -> bytes | None:
        resource_dict: dict[ResourceIdentifier, ArchiveResource] = cast(dict[ResourceIdentifier, ArchiveResource], self._resource_dict)
        resource: ArchiveResource | None = resource_dict.get(ResourceIdentifier(resname, restype), None)
        return None if resource is None else resource.data

    def remove(
        self,
        resname: str,
        restype: ResourceType,
    ):
        key = ResourceIdentifier(resname, restype)
        popped_resource: ArchiveResource | None = self._resource_dict.pop(key, None)
        assert popped_resource is not None
        self._resources.remove(popped_resource)

    def find_resource_by_hash(
        self,
        h: int,
    ) -> int | None:
        return next(
            (i for i, resource in enumerate(self._resources) if hash(resource) == h),
            None,
        )

    def to_bif(self) -> BIF:
        from pykotor.resource.formats.bif.bif_data import BIF  # Prevent circular imports

        bif = BIF()
        for resource in cast(list[ArchiveResource], self._resources):
            bif.set_data(ResRef(resource.resref), resource.restype, resource.data)
        return bif

    def to_erf(self) -> ERF:
        from pykotor.resource.formats.erf.erf_data import ERF  # Prevent circular imports

        erf = ERF()
        for resource in cast(list[ArchiveResource], self._resources):
            erf.set_data(ResRef(resource.resref), resource.restype, resource.data)
        return erf

    def to_rim(self) -> RIM:
        from pykotor.resource.formats.rim.rim_data import RIM  # Prevent circular imports

        rim = RIM()
        for resource in cast(list[ArchiveResource], self._resources):
            rim.set_data(ResRef(resource.resref), resource.restype, resource.data)
        return rim
