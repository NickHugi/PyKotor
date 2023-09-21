"""This module handles classes relating to editing ERF files."""
from __future__ import annotations

from copy import copy
from enum import Enum
from typing import Any

from pykotor.common.misc import ResRef
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_erf_file, is_mod_file


class ERFType(Enum):
    """The type of ERF."""

    ERF = "ERF "
    MOD = "MOD "

    @staticmethod
    def from_extension(filepath: str) -> ERFType:
        if is_erf_file(filepath.lower()):
            return ERFType.ERF
        elif is_mod_file(filepath.lower()):
            return ERFType.MOD
        else:
            msg = f"Invalid ERF extension in filepath '{filepath}'."
            raise ValueError(msg)


class ERF:
    """
    Represents the data of a ERF file.

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
        """Iterates through the stored resources yielding a copied resource each iteration."""
        for resource in self._resource_dict.values():
            yield copy(resource)

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
            key = next((key for key in self._resource_dict if key[0] == item.casefold()), None)
            if key:
                return self._resource_dict[key]
            raise KeyError

        return NotImplemented

    def set_resource(
        self,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ) -> None:
        """
        The `set` function updates or adds a resource in a dictionary based on the given resource reference,
        resource type, and data.

        Args:
        ----
            resref: The `resref` as a string
            restype: The `restype` parameter is of type `ResourceType`. It represents the type of the
                resource being set
            data: The `data` parameter is of type `bytes` and represents the binary data of the resource.
                It is the actual content of the resource that you want to set
        """
        key = (resref.casefold(), restype)
        resource = self._resource_dict.get(key)
        if resource is None:
            resource = ERFResource(ResRef(resref), restype, data)
            self._resources.append(resource)
            self._resource_dict[key] = resource
        else:
            resource.resref = ResRef(resref)
            resource.restype = restype
            resource.data = data

    def get(self, resref: str, restype: ResourceType) -> bytes | None:
        """
        Returns the data of the resource with the specified resref/restype pair if it exists, otherwise returns None.

        Args:
        ----
            resref: The resref.
            restype: The resource type.

        Returns:
        -------
            The bytes data of the resource or None.
        """
        resource = self._resource_dict.get((resref.casefold(), restype))
        return resource.data if resource else None

    def remove(
        self,
        resref: str,
        restype: ResourceType,
    ) -> None:
        """
        Removes the resource with the given resref/restype pair if it exists.

        Args:
        ----
            resref: The resref.
            restype: The resource type.
        """
        key = (resref.casefold(), restype)
        resource = self._resource_dict.pop(key, None)
        if resource:
            self._resources.remove(resource)

    def to_rim(
        self,
    ):
        """
        Returns a RIM with the same resources.

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
