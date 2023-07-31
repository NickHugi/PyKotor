"""
This module handles classes relating to editing ERF files.
"""
from __future__ import annotations

from copy import copy
from enum import Enum
from typing import List, Optional

from pykotor.common.misc import ResRef
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_erf_file, is_mod_file


class ERFType(Enum):
    """
    The type of ERF.
    """
    ERF = "ERF "
    MOD = "MOD "

    @staticmethod
    def from_extension(filepath: str) -> ERFType:
        if is_erf_file(filepath.lower()):
            return ERFType.ERF
        elif is_mod_file(filepath.lower()):
            return ERFType.MOD
        else:
            raise ValueError(f"Invalid ERF extension in filepath '{filepath}'.")


class ERF:
    """
    Represents the data of a ERF file.

    Attributes:
        erf_type: The ERF type.
    """

    BINARY_TYPE = ResourceType.ERF

    def __init__(
            self,
            erf_type: ERFType = ERFType.ERF
    ):
        self.erf_type: ERFType = erf_type
        self._resources: List[ERFResource] = []

    def __iter__(
            self
    ):
        """
        Iterates through the stored resources yielding a copied resource each iteration.
        """
        for resource in self._resources:
            yield copy(resource)

    def __len__(
            self
    ):
        """
        Returns the number of stored resources.
        """
        return len(self._resources)

    def __getitem__(
            self,
            item
    ):
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

    def set(
            self,
            resref: str,
            restype: ResourceType,
            data: bytes
    ) -> None:
        """
        Sets the data of the resource with the specified resref/restype pair. If it does not exists, a resource is
        appended to the resource list.

        Args:
            resref: The resref.
            restype: The resource type.
            data: The new resource data.
        """
        resource = next(
            (resource for resource in self._resources if resource.resref == resref and resource.restype == restype),
            None)
        if resource is None:
            self._resources.append(ERFResource(ResRef(resref), restype, data))
        else:
            resource.resref = ResRef(resref)
            resource.restype = restype
            resource.data = data

    def get(
            self,
            resref: str,
            restype: ResourceType
    ) -> Optional[bytes]:
        """
        Returns the data of the resource with the specified resref/restype pair if it exists, otherwise returns None.

        Args:
            resref: The resref.
            restype: The resource type.

        Returns:
            The bytes data of the resource or None.
        """
        resource = next(
            (resource for resource in self._resources if resource.resref == resref and resource.restype == restype),
            None)
        return None if resource is None else resource.data

    def remove(
            self,
            resref: str,
            restype: ResourceType
    ) -> None:
        """
        Removes the resource with the given resref/restype pair if it exists.

        Args:
            resref: The resref.
            restype: The resource type.
        """
        self._resources = [res for res in self._resources if res.resref != resref and res.restype != restype]

    def to_rim(
            self
    ):
        """
        Returns a RIM with the same resources.

        Returns:
            A new RIM object.
        """
        from pykotor.resource.formats.rim import RIM  # Prevent circular imports
        rim = RIM()
        for resource in self._resources:
            rim.set(resource.resref.get(), resource.restype, resource.data)
        return rim


class ERFResource:
    def __init__(
            self,
            resref: ResRef,
            restype: ResourceType,
            data: bytes
    ):
        self.resref: ResRef = resref
        self.restype: ResourceType = restype
        self.data: bytes = data
