from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Any, TypeVar

from pykotor.extract.file import ResourceIdentifier

if TYPE_CHECKING:
    from typing import ClassVar

    from pykotor.common.misc import ResRef
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

    def __init__(self):
        self._resources = []
        self._resource_dict = {}

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def __iter__(self):
        yield from self._resources

    def __len__(self):
        return len(self._resources)

    def __getitem__(self, item: int | str | ResourceIdentifier | object) -> Any:
        if isinstance(item, int):
            return self._resources[item]
        elif isinstance(item, (str, ResourceIdentifier)):
            return self._resource_dict[item]
        else:
            raise TypeError(f"Invalid key type: {type(item)}")

    def __setitem__(self, key: str | ResourceIdentifier, value: ArchiveResource):
        if isinstance(key, str):
            key = ResourceIdentifier(key, value.restype)
        self._resource_dict[key] = value
        if value not in self._resources:
            self._resources.append(value)

    def __delitem__(self, key: str | ResourceIdentifier):
        if isinstance(key, str):
            key = next((k for k in self._resource_dict.keys() if k.resref == key), None)
            if key is None:
                raise KeyError(key)
        resource = self._resource_dict.pop(key)
        self._resources.remove(resource)

    def __contains__(self, item):
        return item in self._resource_dict

    @abstractmethod
    def set_data(self, resname: str, restype: ResourceType, data: bytes): ...

    @abstractmethod
    def get(self, resname: str, restype: ResourceType) -> bytes | None: ...

    @abstractmethod
    def remove(self, resname: str, restype: ResourceType): ...

    @abstractmethod
    def to_rim(self): ...

    @abstractmethod
    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, BiowareArchive):
            return NotImplemented
        return set(self._resources) == set(other._resources)

    @abstractmethod
    def get_resource_offset(
        self,
        resource: ArchiveResource,
    ) -> int:
        ...  # TODO: implement this method. Ensure subclasses provided a class property we can access here.

    def get_name_hash_algo(self) -> HashAlgo:
        """Get the hash algorithm used for resource names."""
        return HashAlgo.NONE

    def find_resource_by_hash(self, h: int) -> int | None:
        """Find a resource by its hash value."""
        if self.get_name_hash_algo() == HashAlgo.NONE:
            return None
        return next(
            (
                i
                for i, resource in enumerate(self._resources)
                if hash(resource) == h
            ),
            None,
        )

    def find_resource(
        self,
        name: str,
        restype: ResourceType,
    ) -> int | None:
        """Find a resource by its name and type."""
        ident = ResourceIdentifier(name, restype)
        return next(
            (
                i
                for i, resource in enumerate(self._resources)
                if resource.identifier() == ident
            ),
            None,
        )
