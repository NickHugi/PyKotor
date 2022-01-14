from __future__ import annotations

from pykotor.resource.type import ResourceType


class FileResource:
    """
    Stores information for a resource regarding its name, type and where the data can be loaded from.
    """
    def __init__(self, resref: str, restype: ResourceType, size: int, offset: int, filepath: str):
        self._resref: str = resref
        self._restype: ResourceType = restype
        self._size: int = size
        self._filepath: str = filepath
        self._offset: int = offset

    def __repr__(self):
        return self._resref + "." + self._restype.extension

    def __str__(self):
        return self._resref + "." + self._restype.extension

    def __eq__(self, other: FileResource):
        if isinstance(other, FileResource):
            return other._resref == self._resref and other._restype == self._restype
        elif isinstance(other, FileQuery):
            return other.resref == self._resref and other.restype == self._restype
        else:
            return NotImplemented

    def resref(self) -> str:
        return self._resref

    def restype(self) -> ResourceType:
        return self._restype

    def size(self) -> int:
        return self._size

    def filepath(self) -> str:
        return self._filepath

    def offset(self) -> int:
        return self._offset

    def data(self) -> bytes:
        """
        Opens the file the resource is located at and returns the bytes data of the resource.

        Returns:
            Bytes data of the resource.
        """
        with open(self._filepath, 'rb') as file:
            file.seek(self._offset)
            return file.read(self._size)


class FileQuery:
    """
    Stores a ResRef and resource type value. If a FileQuery object is compared (equality) to a FileResource object it
    will return True if the resref and restype values match.
    """
    def __init__(self, resref: str, restype: ResourceType):
        self.resref: str = resref
        self.restype: ResourceType = restype
