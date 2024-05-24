"""This module handles classes relating to editing ERF files."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from pykotor.common.misc import ResRef
from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_erf_file, is_mod_file, is_sav_file
from utility.common.more_collections import OrderedSet

if TYPE_CHECKING:
    import os


class ERFType(Enum):
    """The type of ERF."""

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


class ERF:
    """Represents the data of a ERF file.

    Attributes:
    ----------
        erf_type: The ERF type.
    """

    BINARY_TYPE = ResourceType.ERF

    def __init__(
        self,
        erf_type: ERFType = ERFType.ERF,
        *,
        is_save: bool = False,
    ):
        self.erf_type: ERFType = erf_type
        self._resources: OrderedSet[ERFResource] = OrderedSet()
        self.is_save_erf: bool = is_save

        # used for faster lookups
        self._resource_dict: dict[ResourceIdentifier, ERFResource] = {}

    def __repr__(
        self,
    ):
        return f"{self.__class__.__name__}({self.erf_type!r})"

    def __iter__(
        self,
    ):
        """Iterates through the stored resources yielding a resource each iteration."""
        yield from self._resources

    def __len__(
        self,
    ):
        """Returns the number of stored resources."""
        return len(self._resources)

    def __getitem__(
        self,
        item: int | str | ResourceIdentifier | object,
    ):
        """Returns a resource at the specified index or with the specified resref."""
        if isinstance(item, int):
            return self._resources[item]
        if isinstance(item, (ResourceIdentifier, str)):
            if isinstance(item, str):
                item = item.lower()
            try:
                return self._resource_dict[next(key for key in self._resource_dict if key[0] == item)]
            except StopIteration as e:
                msg = f"{item} not found in {self!r}"
                raise KeyError(msg) from e

        return NotImplemented

    def set_data(
        self,
        resname: str,
        restype: ResourceType,
        data: bytes,
    ):
        """Sets resource data in the ERF file.

        Args:
        ----
            resname: str - Resource reference filename
            restype: ResourceType - Resource type enumeration
            data: bytes - Resource data bytes

        Processing Logic:
        ----------------
            - Construct a tuple key from resref and restype
            - Lookup existing resource by key in internal dict
            - If no existing resource, create a new ERFResource instance
            - If existing resource, update its properties
            - Add/update resource to internal lists and dict
        """
        ident: ResourceIdentifier = ResourceIdentifier(resname, restype)
        resource: ERFResource | None = self._resource_dict.get(ident)
        resref = ResRef(ident.resname)
        if resource is None:
            resource = ERFResource(resref, restype, data)
            self._resources.append(resource)
            self._resource_dict[ident] = resource
        else:
            resource.resref = resref
            resource.restype = restype
            resource.data = data

    def get(self, resname: str, restype: ResourceType) -> bytes | None:
        """Returns the data of the resource with the specified resref/restype pair if it exists, otherwise returns None.

        Args:
        ----
            resname: The resource reference filename stem.
            restype: The resource type.

        Returns:
        -------
            The bytes data of the resource or None.
        """
        resource: ERFResource | None = self._resource_dict.get(ResourceIdentifier(resname, restype))
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
        key = ResourceIdentifier(resname, restype)
        resource: ERFResource | None = self._resource_dict.pop(key, None)
        if resource:  # FIXME: should raise here
            self._resources.remove(resource)

    def to_rim(
        self,
    ):
        """Returns a RIM with the same resources.

        Returns:
        -------
            A new RIM object.
        """
        from pykotor.resource.formats.rim import RIM  # Prevent circular imports  # noqa: PLC0415

        rim = RIM()
        for resource in self._resources:
            rim.set_data(str(resource.resref), resource.restype, resource.data)
        return rim

    def __eq__(self, other):
        from pykotor.resource.formats.rim import RIM
        if not isinstance(other, (ERF, RIM)):
            return NotImplemented
        return set(self._resources) == set(other._resources)


class ERFResource:
    def __init__(
        self,
        resref: ResRef,
        restype: ResourceType,
        data: bytes,
    ):
        self.resref: ResRef = resref
        self.restype: ResourceType = restype
        if isinstance(data, bytearray):  # FIXME: indoor map builder is passing a bytearray here somewhere.
            data = bytes(data)
        self.data: bytes = data

    def __eq__(
        self,
        other,
    ):
        from pykotor.resource.formats.rim import RIMResource
        if not isinstance(other, (ERFResource, RIMResource)):
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
