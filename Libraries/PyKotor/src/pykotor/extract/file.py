from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, NamedTuple

from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_bif_file, is_capsule_file
from utility.misc import generate_hash
from utility.path import Path, PurePath

if TYPE_CHECKING:
    import os

    from pykotor.common.misc import ResRef


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
        self._resname: str = resname.strip()
        self._restype: ResourceType = restype
        self._size: int = size
        self._offset: int = offset
        self._filepath: Path = Path.pathify(filepath)

        self._file_hash: str = self.get_hash(reload=True)
        self._identifier = ResourceIdentifier(self._resname, self._restype)

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
        return str(self._identifier)

    def __eq__(  # Checks are ordered from fastest to slowest.
        self,
        other: FileResource | ResourceIdentifier | bytes | bytearray | memoryview | object,
    ):
        if isinstance(other, ResourceIdentifier):
            return self.identifier() == other
        if isinstance(other, FileResource):
            if self is other:
                return True
            if (
                self._offset == other._offset
                and self._resname == other._resname
                and self._restype == other._restype
                and self._filepath == other._filepath
            ):
                return True

        self_hash = self.get_hash(reload=False)
        if not self_hash:
            return False

        other_hash: str | None = None
        if isinstance(other, FileResource):
            other_hash = other.get_hash(reload=False)
        if isinstance(other, (bytes, bytearray, memoryview)):
            other_hash = generate_hash(other)
        if other_hash is None:
            return NotImplemented
        return self_hash == other_hash

    def resname(
        self,
    ) -> str:
        return self._resname

    def resref(
        self,
    ) -> ResRef | None:
        from pykotor.common.misc import ResRef
        with suppress(ResRef.ExceedsMaxLengthError, ResRef.InvalidEncodingError):
            return ResRef(self._resname)
        return None

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
        return str(self)

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

        Raises
        ------
            FileNotFoundError: File not found on disk.
        """
        if reload:
            if is_capsule_file(self._filepath):
                from pykotor.extract.capsule import Capsule  # Prevent circular imports

                capsule = Capsule(self._filepath)
                res: FileResource | None = capsule.info(self._resname, self._restype)  # type: ignore[assignment]
                assert res is not None, f"Resource '{self._resname}.{self._restype.extension}' not found in Capsule at '{self._filepath!s}'"

                self._offset = res.offset()
                self._size = res.size()
            elif not is_bif_file(self._filepath):  # bifs are read-only and there's no reason to reload them.
                # Regular file on disk.
                self._offset = 0
                self._size = self._filepath.stat().st_size

        with self._filepath.open("rb") as file:
            file.seek(self._offset)
            data: bytes = file.read(self._size)
            self._file_hash = generate_hash(data)
            return data

    def get_hash(
        self,
        *,
        reload: bool = False,
    ) -> str:
        """Returns a lowercase hex string sha1 hash. If FileResource doesn't exist this returns an empty str."""
        if reload:
            if self._filepath.safe_exists():
                self.data()  # Ensure that the hash is calculated
            else:
                return ""
        return self._file_hash

    def identifier(
        self,
    ) -> ResourceIdentifier:
        return self._identifier


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
        return hash(str(self).lower())

    def __repr__(
        self,
    ):
        return f"ResourceIdentifier({self.resname}, {self.restype!r})"

    def __str__(
        self,
    ):
        return f"{self.resname}{f'.{self.restype.extension}' if self.restype.extension else ''}"

    def __eq__(self, other: object):
        if isinstance(other, str):
            return hash(self) == hash(other.lower())
        if isinstance(other, ResourceIdentifier):
            return hash(self) == hash(other)
        return NotImplemented

    def validate(self):
        if self.restype == ResourceType.INVALID:
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
        try:
            path_obj = PurePath(file_path)
        except Exception:
            return ResourceIdentifier("", ResourceType.from_extension(""))

        max_dots: int = path_obj.name.count(".")
        for dots in range(max_dots+1, 1, -1):
            with suppress(Exception):
                resname, restype_ext = path_obj.split_filename(dots)
                return ResourceIdentifier(
                    resname,
                    ResourceType.from_extension(restype_ext).validate(),
                )

        # ResourceType is invalid at this point.
        return ResourceIdentifier(path_obj.stem, ResourceType.from_extension(path_obj.suffix))
