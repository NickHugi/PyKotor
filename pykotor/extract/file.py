from __future__ import annotations

import os
from typing import NamedTuple

from pykotor.resource.type import ResourceType
from pykotor.tools.misc import (
    is_bif_file,
    is_capsule_file,
)
from pykotor.tools.path import CustomPath, get_case_sensitive_path


class FileResource:
    """Stores information for a resource regarding its name, type and where the data can be loaded from."""

    def __init__(
        self,
        resname: str,
        restype: ResourceType,
        size: int,
        offset: int,
        filepath: str | CustomPath,
    ):
        self._resname: str = resname
        self._restype: ResourceType = restype
        self._size: int = size
        self._filepath: CustomPath = CustomPath(filepath)
        self._offset: int = offset

    def __repr__(
        self,
    ):
        return f"{self._resname}.{self._restype.extension}"

    def __str__(
        self,
    ):
        return f"{self._resname}.{self._restype.extension}"

    def __eq__(
        self,
        other: FileResource | ResourceIdentifier | object,
    ):
        if isinstance(other, FileResource):
            return (
                other._resname.lower() == self._resname.lower()
                and other._restype == self._restype
            )
        elif isinstance(other, ResourceIdentifier):
            return (
                other.resname.lower() == self._resname.lower()
                and other.restype == self._restype
            )
        else:
            return NotImplemented

    def resname(
        self,
    ) -> str:
        return self._resname.lower()

    def restype(
        self,
    ) -> ResourceType:
        return self._restype

    def size(
        self,
    ) -> int:
        return self._size

    def filepath(
        self,
    ) -> CustomPath:
        return self._filepath

    def offset(
        self,
    ) -> int:
        return self._offset

    def data(
        self,
        *,
        reload: bool = False,
    ) -> bytes:
        """Opens the file the resource is located at and returns the bytes data of the resource.

        Returns
        -------
            Bytes data of the resource.
        """
        if reload:
            if is_capsule_file(self._filepath.name):
                from pykotor.extract.capsule import Capsule

                capsule = Capsule(self._filepath)
                res = capsule.info(self._resname, self._restype)
                self._offset = res.offset()
                self._size = res.size()
            elif not is_bif_file(self._filepath.name):
                self._offset = 0
                self._size = os.path.getsize(self._filepath)

        if not self._filepath.exists():
            self._filepath = CustomPath(get_case_sensitive_path(str(self._filepath)))
        with self._filepath.open("rb") as file:
            file.seek(self._offset)
            return file.read(self._size)

    def identifier(
        self,
    ) -> ResourceIdentifier:
        return ResourceIdentifier(self.resname(), self.restype())


class ResourceResult(NamedTuple):
    resname: str
    restype: ResourceType
    filepath: CustomPath
    data: bytes | None


class LocationResult(NamedTuple):
    filepath: CustomPath
    offset: int
    size: int


class ResourceIdentifier(NamedTuple):
    resname: str
    restype: ResourceType

    def __hash__(
        self,
    ):
        return hash(f"{self.resname.lower()}.{self.restype.extension}")

    def __repr__(
        self,
    ):
        return f"ResourceIdentifier({self.resname}, ResourceType.{self.restype})"

    def __str__(
        self,
    ):
        return f"{self.resname.lower()}.{self.restype.extension}"

    def __eq__(
        self,
        other: ResourceIdentifier | object,
    ):
        if isinstance(other, ResourceIdentifier):
            return (
                self.resname.lower() == other.resname.lower()
                and self.restype == other.restype
            )
        return NotImplemented

    @staticmethod
    def from_path(
        file_path: CustomPath | str,
    ) -> ResourceIdentifier:
        file_path = CustomPath(file_path)
        file_name = file_path.name
        resname, restype_ext = file_name.split(".", 1)
        return ResourceIdentifier(resname, ResourceType.from_extension(restype_ext))
