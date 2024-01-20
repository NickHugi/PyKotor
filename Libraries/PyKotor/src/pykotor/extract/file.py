from __future__ import annotations

import os
from contextlib import suppress
from typing import TYPE_CHECKING, NamedTuple

from pykotor.common.misc import ResRef
from pykotor.common.stream import BinaryReader
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_bif_file, is_capsule_file
from utility.misc import generate_sha256_hash
from utility.path import Path, PurePath

if TYPE_CHECKING:
    from utility.string import CaseInsensitiveWrappedStr


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
        assert resname == resname.strip(), f"FileResource cannot be constructed, resource name '{resname}' cannot start/end with whitespace."

        self._identifier = ResourceIdentifier(resname, restype)

        self._resname: str = resname
        self._restype: ResourceType = restype
        self._size: int = size
        self._offset: int = offset
        self._filepath: Path = Path.pathify(filepath)

        self.inside_capsule: bool = is_capsule_file(self._filepath)
        self.inside_bif: bool = is_bif_file(self._filepath)

        self._path_ident_obj: Path
        if self.inside_capsule or self.inside_bif:
            self._path_ident_obj = self._filepath / str(self._identifier)
        else:
            self._path_ident_obj = self._filepath

        self._sha256_hash: str = ""
        self._internal = False

    def __setattr__(self, __name, __value):
        if hasattr(self, __name) and __name != "_internal" and not self._internal:
            msg = f"Cannot modify immutable FileResource instance, attempted `setattr({self!r}, {__name!r}, {__value!r})`"
            raise RuntimeError(msg)

        return super().__setattr__(__name, __value)

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
                f"resname='{self._resname}', "
                f"restype={self._restype!r}, "
                f"size={self._size}, "
                f"offset={self._offset}, "
                f"filepath={self._filepath!r}"
            ")"
        )

    def __hash__(self):
        return hash(self._path_ident_obj)

    def __str__(self):
        return str(self._path_ident_obj)

    def __eq__(
        self,
        __value: object,
    ):
        if isinstance(__value, FileResource):
            return self.get_sha256_hash() == __value.get_sha256_hash()
        if isinstance(__value, (os.PathLike, bytes, bytearray, memoryview)):
            return self.get_sha256_hash() == generate_sha256_hash(__value)
        if isinstance(__value, (ResRef, ResourceIdentifier)):
            return hash(self._identifier) == hash(__value)
        if isinstance(__value, str):
            return hash(self._identifier) == hash(__value.lower())
        return hash(self._identifier) == hash(__value)

    def resname(self) -> str:
        return self._resname

    def resref(self) -> ResRef:
        from pykotor.common.misc import ResRef
        return ResRef.from_invalid(self._resname)

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
        return str(self._identifier)

    def filepath(
        self,
    ) -> Path:
        return self._filepath

    def offset(
        self,
    ) -> int:
        return self._offset

    def _index_resource(
        self,
    ):
        if self.inside_capsule:
            from pykotor.extract.capsule import Capsule  # Prevent circular imports

            capsule = Capsule(self._filepath)
            res: FileResource | None = capsule.info(self._resname, self._restype)
            assert res is not None, f"Resource '{self._identifier}' not found in Capsule at '{self._filepath}'"

            self._offset = res.offset()
            self._size = res.size()
        elif not self.inside_bif:  # bifs are read-only, offset/data will never change.
            self._offset = 0
            self._size = self._filepath.stat().st_size

    def data(
        self,
        *,
        reload: bool = False,
    ) -> bytes:
        """Opens the file the resource is located at and returns the bytes data of the resource.

        Args:
        ----
            reload (bool, kwarg): Whether to reload the file from disk or use the cache. Default is False

        Returns:
        -------
            Bytes data of the resource.
        """
        self._internal = True
        try:
            if reload:
                self._index_resource()

            with BinaryReader.from_file(self._filepath) as file:
                file.seek(self._offset)
                data: bytes = file.read_bytes(self._size)
                self._sha256_hash = generate_sha256_hash(data)
                return data
        finally:
            self._internal = False

    def get_sha256_hash(
        self,
        *,
        reload: bool = False,
    ) -> str:
        if reload or not self._sha256_hash:
            self.data()  # Recalculate SHA256 hash
        return self._sha256_hash

    def identifier(self) -> ResourceIdentifier:
        return self._identifier


class ResourceResult(NamedTuple):
    resname: CaseInsensitiveWrappedStr | str
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
        return f"{self.__class__.__name__}(resname='{self.resname}', restype={self.restype!r})"

    def __str__(
        self,
    ):
        ext: str = self.restype.extension
        suffix: str = f".{ext}" if ext else ""
        return f"{self.resname}{suffix}".lower()

    def __eq__(
        self,
        __value: object,
    ):
        if isinstance(__value, str) and not isinstance(__value, ResRef):
            __value = self.from_path(__value)
        return hash(self) == hash(__value)

    def validate(self, *, strict: bool = False):
        from pykotor.common.misc import ResRef
        _ = strict and ResRef(self.resname)

        if self.restype == ResourceType.INVALID:
            msg = f"Invalid resource: '{self!r}'"
            raise ValueError(msg)

        return self

    def as_resref_compatible(self):
        from pykotor.common.misc import ResRef
        return self.__class__(str(ResRef.from_invalid(self.resname)), self.restype)

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
            path_obj = PurePath.pathify(file_path)
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
