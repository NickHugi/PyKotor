from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, NamedTuple

from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_bif_file, is_capsule_file
from utility.misc import generate_sha256_hash
from utility.path import Path, PurePath

if TYPE_CHECKING:
    import os


class FileResource:
    """Stores information for a resource regarding its name, type and where the data can be loaded from."""

    def __init__(
        self,
        resname: str,
        restype: ResourceType,
        size: int,
        offset: int,
        filepath: os.PathLike | str,
    ):
        self._resname: str = resname.lower()
        self._restype: ResourceType = restype
        self._size: int = size
        self._filepath: Path = Path.pathify(filepath)
        self._offset: int = offset
        self._sha256_hash: str = ""

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
                f"resname='{self._resname}', "
                f"restype={self._restype!r}, "
                f"size={self._size}, "
                f"offset={self._offset}, "
                f"filepath={self._filepath!r}"
            ")"
        )

    def __str__(
        self,
    ) -> str:
        return f"{self._resname}.{self._restype.extension}"

    def __eq__(
        self,
        other: FileResource | ResourceIdentifier | Path | bytes | bytearray | memoryview | object,
    ):
        if isinstance(other, FileResource):
            return self.get_sha256_hash() == other.get_sha256_hash()
        if isinstance(other, (Path, bytes, bytearray, memoryview)):
            return self.get_sha256_hash() == generate_sha256_hash(other)
        if isinstance(other, ResourceIdentifier):
            return self.identifier() == other
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self.__class__, self._filepath, self._offset, self._size, self.identifier()))

    def resname(
        self,
    ) -> str:
        return self._resname

    def restype(
        self,
    ) -> ResourceType:
        return self._restype

    def size(
        self,
    ) -> int:
        return self._size

    def filename(
        self,
    ) -> str:
        return f"{self._resname}.{self.restype().extension}"

    def filepath(
        self,
    ) -> Path:
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
            if is_capsule_file(self._filepath):
                from pykotor.extract.capsule import Capsule  # Prevent circular imports

                capsule = Capsule(self._filepath)
                res: FileResource | None = capsule.info(self._resname, self._restype)  # type: ignore[assignment]
                assert res is not None, f"Resource '{self._resname}.{self._restype.extension}' not found in Capsule at '{self._filepath}"

                self._offset = res.offset()
                self._size = res.size()
            elif not is_bif_file(self._filepath):  # bifs are read-only and there's no reason to reload them.
                self._offset = 0
                self._size = self._filepath.stat().st_size

        with self._filepath.open("rb") as file:
            file.seek(self._offset)
            data: bytes = file.read(self._size)
            self._sha256_hash = generate_sha256_hash(data)
            return data

    def get_sha256_hash(self):
        if not self._sha256_hash:
            self.data()  # Ensure that the SHA256 hash is calculated
        return self._sha256_hash

    def identifier(
        self,
    ) -> ResourceIdentifier:
        return ResourceIdentifier(self.resname(), self.restype())


class ResourceResult(NamedTuple):
    resname: str
    restype: ResourceType
    filepath: Path
    data: bytes


class LocationResult(NamedTuple):
    filepath: Path
    offset: int
    size: int


class ResourceIdentifier(NamedTuple):
    """Class for storing resource name and type, facilitating case-insensitive object comparisons and hashing equal to their string representations."""

    resname: str
    restype: ResourceType

    def __hash__(
        self,
    ):
        return hash(str(self))

    def __repr__(
        self,
    ):
        return f"ResourceIdentifier({self.resname}, ResourceType.{self.restype})"

    def __str__(
        self,
    ):
        return f"{self.resname.lower()}{f'.{self.restype.extension.lower()}' if self.restype.extension else ''}"

    def __eq__(
        self,
        other: ResourceIdentifier | str | object,
    ):
        if isinstance(other, str):
            other = ResourceIdentifier.from_path(other)
        if isinstance(other, ResourceIdentifier):
            return (
                self.resname.lower() == other.resname.lower()
                and self.restype.extension.lower() == other.restype.extension.lower()
            )
        return NotImplemented

    def validate(self):
        restype = self.restype
        if restype == ResourceType.INVALID:
            msg = f"Invalid resource: '{self}'"
            raise ValueError(msg)
        return self

    @classmethod
    def identify(cls, obj: ResourceIdentifier | os.PathLike | str):
        return obj if isinstance(obj, (cls, ResourceIdentifier)) else cls.from_path(obj)

    @classmethod
    def from_path(cls, file_path: os.PathLike | str) -> ResourceIdentifier:
        """Generate a ResourceIdentifier from a file path or file name. If not valid, will return an invalidated ResourceType equal to ResourceType.INVALID.

        Args:
        ----
            file_path (os.PathLike | str): The filename, or path to the file, to construct an identifier from

        Returns:
        -------
            ResourceIdentifier: Determined ResourceIdentifier object.

        Processing Logic:
        ----------------
            - Splits the file path into resource name and type by filename dots, starting from maximum dots
            - Validates the extracted resource type
            - If splitting fails, uses stem as name and extension (from the last dot) as type
            - Handles exceptions during processing
        """
        path_obj: PurePath = PurePath("")  #PurePath("<INVALID>")
        with suppress(Exception), suppress(TypeError):
            path_obj = PurePath(file_path)
        with suppress(Exception):
            max_dots: int = path_obj.name.count(".")
            for dots in range(max_dots+1, 1, -1):
                with suppress(Exception):
                    resname, restype_ext = path_obj.split_filename(dots)
                    return ResourceIdentifier(
                        resname,
                        ResourceType.from_extension(restype_ext).validate(),
                    )

        return ResourceIdentifier(path_obj.stem, ResourceType.from_extension(path_obj.suffix))
