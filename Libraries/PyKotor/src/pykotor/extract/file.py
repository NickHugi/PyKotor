from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, NamedTuple

from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_bif_file, is_capsule_file
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
        filepath: Path,
    ):
        self._resname: str = resname
        self._restype: ResourceType = restype
        self._size: int = size
        self._filepath: Path = filepath
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
            return other._resname.lower() == self._resname.lower() and other._restype == self._restype
        if isinstance(other, ResourceIdentifier):
            return other.resname.lower() == self._resname.lower() and other.restype == self._restype
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
            if is_capsule_file(self._filepath.name):
                from pykotor.extract.capsule import Capsule

                capsule = Capsule(self._filepath)
                res: FileResource | None = capsule.info(self._resname, self._restype)
                self._offset = res.offset()
                self._size = res.size()
            elif not is_bif_file(self._filepath.name):
                self._offset = 0
                self._size = self._filepath.stat().st_size

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
    filepath: Path
    data: bytes


class LocationResult(NamedTuple):
    filepath: Path
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
            return self.resname.lower() == other.resname.lower() and self.restype == other.restype
        return NotImplemented

    def validate(self):
        restype = self.restype
        if restype == ResourceType.INVALID:
            msg = f"Invalid resource type: {restype.extension}"
            raise ValueError(msg)
        return self

    @classmethod
    def from_path(cls, file_path: os.PathLike | str) -> ResourceIdentifier:
        """Generate a ResourceIdentifier from a file path. If not valid, will return ResourceType.INVALID.

        Args:
        ----
            file_path: {Path or string to the file}:

        Returns:
        -------
            ResourceIdentifier: Resource identifier object

        Processing Logic:
        ----------------
            - Split the file path on the filename and extension
            - Determine the resource type from the extension
            - Return a ResourceIdentifier with the name and type.
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

        return ResourceIdentifier(path_obj.stem, ResourceType.INVALID)
