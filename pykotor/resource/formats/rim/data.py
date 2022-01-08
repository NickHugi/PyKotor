"""
This module handles classes relating to editing RIM files.
"""
from __future__ import annotations

from copy import copy
from typing import List, Optional

from pykotor.common.misc import ResRef
from pykotor.resource.type import ResourceType


class RIM:
    """
    Represents the data of a RIM file.
    """

    def __init__(self):
        self._resources: List[RIMResource] = []

    def __iter__(self):
        """
        Iterates through the stored resources yielding a copied resource each iteration.
        """
        for resource in self._resources:
            yield copy(resource)

    def __len__(self):
        """
        Returns the number of stored resources.
        """
        return len(self._resources)

    def __getitem__(self, item):
        """
        Returns a resource at the specified index or with the specified resref.
        """
        if isinstance(item, int):
            return self._resources[item]
        elif isinstance(item, str):
            resource = next([resource for resource in self._resources if resource.resref == item], None)
            if resource is None:
                raise KeyError
            else:
                return resource
        else:
            return NotImplemented

    def set(self, resref: str, restype: ResourceType, data: bytes) -> None:
        """
        Sets the data of the resource with the specified resref/restype pair. If it does not exists, a resource is
        appended to the resource list.

        Args:
            resref: The resref.
            restype: The resource type.
            data: The new resource data.
        """
        resource = next((resource for resource in self._resources if resource.resref == resref and resource.restype == restype), None)
        if resource is None:
            self._resources.append(RIMResource(ResRef(resref), restype, data))
        else:
            resource.resref = resref
            resource.restype = restype
            resource.data = data

    def get(self, resref: str, restype: ResourceType) -> Optional[bytes]:
        """
        Returns the data of the resource with the specified resref/restype pair if it exists, otherwise returns None.

        Args:
            resref: The resref.
            restype: The resource type.

        Returns:
            The bytes data of the resource or None.
        """
        resource = next((resource for resource in self._resources if resource.resref == resref and resource.restype == restype), None)
        return None if resource is None else resource.data

    def remove(self, resref: str, restype: ResourceType) -> None:
        """
        Removes the resource with the given resref/restype pair if it exists.

        Args:
            resref: The resref.
            restype: The resource type.
        """
        self._resources = [res for res in self._resources if res.resref != resref and res.restype != restype]

    def to_erf(self):
        """
        Returns a ERF with the same resources.

        Returns:
            A new ERF object.
        """
        from pykotor.resource.formats.ssf import ERF  # Prevent circular imports
        erf = ERF()
        for resource in self._resources:
            erf.set(resource.resref.get(), resource.restype, resource.data)


class RIMResource:
    def __init__(self, resref: ResRef, restype: ResourceType, data: bytes):
        self.resref: ResRef = resref
        self.restype: ResourceType = restype
        self.data: bytes = data
