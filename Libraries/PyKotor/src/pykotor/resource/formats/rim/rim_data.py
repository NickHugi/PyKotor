"""This module handles classes relating to editing RIM files."""
from __future__ import annotations

from copy import copy

from pykotor.common.misc import ResRef
from pykotor.resource.type import ResourceType


class RIM:
    """Represents the data of a RIM file."""

    BINARY_TYPE = ResourceType.RIM

    def __init__(
        self,
    ):
        self._resources: list[RIMResource] = []

    def __iter__(
        self,
    ):
        """Iterates through the stored resources yielding a copied resource each iteration."""
        for resource in self._resources:
            yield copy(resource)

    def __len__(
        self,
    ):
        """Returns the number of stored resources."""
        return len(self._resources)

    def __getitem__(
        self,
        item,
    ):
        """Returns a resource at the specified index or with the specified resref."""
        if isinstance(item, int):
            return self._resources[item]
        if isinstance(item, str):
            try:
                return next(resource for resource in self._resources if resource.resref == item)
            except StopIteration as e:
                msg = f"{item} not found."
                raise KeyError(msg) from e
        return NotImplemented

    def __add__(self, other: RIM) -> RIM:
        """Combines the resources of two RIM instances into a new RIM instance.

        Args:
        ----
            other: Another RIM instance.

        Returns:
        -------
            A new RIM instance containing the combined resources.
        """
        if not isinstance(other, RIM):
            return NotImplemented

        combined_rim = RIM()
        for resource in self:
            combined_rim.set_data(str(resource.resref), resource.restype, resource.data)
        for resource in other:
            combined_rim.set_data(str(resource.resref), resource.restype, resource.data)

        return combined_rim

    def set_data(
        self,
        resname: str,
        restype: ResourceType,
        data: bytes,
    ):
        """Sets the data of the resource with the specified resref/restype pair.

        If it does not exists, a resource is appended to the resource list.

        Args:
        ----
            resname: The resource reference filename.
            restype: The resource type.
            data: The new resource data.
        """
        resource: RIMResource | None = next(
            (resource for resource in self._resources if resource.resref == resname and resource.restype == restype),
            None,
        )
        if resource is None:
            self._resources.append(RIMResource(ResRef(resname), restype, data))
        else:
            resource.resref = ResRef(resname)
            resource.restype = restype
            resource.data = data

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
        self._resources = [
            res
            for res in self._resources
            if res.resref != resname and res.restype != restype
        ]

    def to_erf(
        self,
    ):
        """Returns a ERF with the same resources.

        Returns
        -------
            A new ERF object.
        """
        from pykotor.resource.formats.erf import ERF  # Prevent circular imports

        erf = ERF()
        for resource in self._resources:
            erf.set_data(str(resource.resref), resource.restype, resource.data)
        return erf


class RIMResource:
    def __init__(
        self,
        resref: ResRef,
        restype: ResourceType,
        data: bytes,
    ):
        self.resref: ResRef = resref
        self.restype: ResourceType = restype
        self.data: bytes = data
