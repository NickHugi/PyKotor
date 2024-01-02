"""This module handles classes relating to editing ERF files."""
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any

from pykotor.common.misc import ResRef
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_erf_file, is_mod_file, is_sav_file

if TYPE_CHECKING:
    import os


class ERFType(Enum):
    """The type of ERF."""

    ERF = "ERF "
    MOD = "MOD "
    SAV = "SAV "

    @staticmethod
    def from_extension(filepath: os.PathLike | str) -> ERFType:
        if is_erf_file(filepath):
            return ERFType.ERF
        if is_mod_file(filepath):
            return ERFType.MOD
        if is_sav_file(filepath):
            return ERFType.SAV
        msg = f"Invalid ERF extension in filepath '{filepath}'."
        raise ValueError(msg)


class ERF:
    """Represents the data of a ERF file.

    Attributes
    ----------
        erf_type: The ERF type.
    """

    BINARY_TYPE = ResourceType.ERF

    def __init__(
        self,
        erf_type: ERFType = ERFType.ERF,
    ):
        self.erf_type: ERFType = erf_type
        self._resources: list[ERFResource] = []

        # used for faster lookups
        self._resource_dict: dict[tuple[str, ResourceType], ERFResource] = {}

    def __iter__(
        self,
    ):
        """Iterates through the stored resources yielding a resource each iteration."""
        yield from self._resource_dict.values()

    def __len__(
        self,
    ):
        """Returns the number of stored resources."""
        return len(self._resources)

    def __getitem__(
        self,
        item: int | str | Any,
    ):
        """Returns a resource at the specified index or with the specified resref."""
        if isinstance(item, int):
            return self._resources[item]
        if isinstance(item, str):
            try:
                return self._resource_dict[next(key for key in self._resource_dict if key[0] == item.casefold())]
            except StopIteration as e:
                msg = f"{item} not found"
                raise KeyError(msg) from e

        return NotImplemented

    def set_data(  # noqa: D417
        self,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ) -> None:
        """Sets resource data in the ERF file.

        Args:
        ----
            resref: str - Resource reference identifier
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
        key: tuple[str, ResourceType] = (resref.casefold(), restype)
        resource: ERFResource | None = self._resource_dict.get(key)
        if resource is None:
            resource = ERFResource(ResRef(resref), restype, data)
            self._resources.append(resource)
            self._resource_dict[key] = resource
        else:
            resource.resref = ResRef(resref)
            resource.restype = restype
            resource.data = data

    def get(self, resref: str, restype: ResourceType) -> bytes | None:
        """Returns the data of the resource with the specified resref/restype pair if it exists, otherwise returns None.

        Args:
        ----
            resref: The resref.
            restype: The resource type.

        Returns:
        -------
            The bytes data of the resource or None.
        """
        resource: ERFResource | None = self._resource_dict.get((resref.casefold(), restype))
        return resource.data if resource is not None else None

    def remove(
        self,
        resref: str,
        restype: ResourceType,
    ) -> None:
        """Removes the resource with the given resref/restype pair if it exists.

        Args:
        ----
            resref: The resref.
            restype: The resource type.
        """
        key: tuple[str, ResourceType] = (resref.casefold(), restype)
        resource: ERFResource | None = self._resource_dict.pop(key, None)
        if resource:  # FIXME: should raise here
            self._resources.remove(resource)

    def to_rim(
        self,
    ):
        """Returns a RIM with the same resources.

        Returns
        -------
            A new RIM object.
        """
        from pykotor.resource.formats.rim import RIM  # Prevent circular imports

        rim = RIM()
        for resource in self._resources:
            rim.set_data(resource.resref.get(), resource.restype, resource.data)
        return rim


class ERFResource:
    def __init__(
        self,
        resref: ResRef,
        restype: ResourceType,
        data: bytes,
    ):
        self.resref: ResRef = resref
        self.restype: ResourceType = restype
        self.data: bytes = data
