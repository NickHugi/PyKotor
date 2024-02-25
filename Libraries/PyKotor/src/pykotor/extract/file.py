from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, NamedTuple

from pykotor.common.stream import BinaryReader
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_bif_file, is_capsule_file
<<<<<<< HEAD
=======
from utility.misc import generate_hash
>>>>>>> master
from utility.system.path import Path, PurePath

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
        assert resname == resname.strip(), f"FileResource cannot be constructed, resource name '{resname}' cannot start/end with whitespace."
<<<<<<< HEAD

=======
>>>>>>> master
        self._identifier = ResourceIdentifier(resname, restype)

        self._resname: str = resname
        self._restype: ResourceType = restype
        self._size: int = size
        self._offset: int = offset
        self._filepath: Path = Path.pathify(filepath)

        self.inside_capsule: bool = is_capsule_file(self._filepath)
<<<<<<< HEAD
        if self._identifier == self._filepath.name:
            self.inside_capsule = False  # HACK: For when capsules are the resource themselves.
        self.inside_bif: bool = is_bif_file(self._filepath)

#        filehash = self.get_hash(reload=True)
#        self._internal = True
#        self._file_hash: str = filehash
#        self._identifier = ResourceIdentifier(self._resname, self._restype)

        self._path_ident_obj: Path
        if self.inside_capsule or self.inside_bif:
            self._path_ident_obj = self._filepath / str(self._identifier)
        else:
            self._path_ident_obj = self._filepath

        self._sha256_hash: str = ""
        self._internal = False

    def __setattr__(self, __name, __value):
        if (
            hasattr(self, __name)
            and __name not in {"_internal", "_task_running"}
            and not getattr(self, "_internal", True)
        ):
=======
        self.inside_bif: bool = is_bif_file(self._filepath)

        self._file_hash: str = ""

        self._path_ident_obj: Path = (
            self._filepath / str(self._identifier)
            if self.inside_capsule or self.inside_bif
            else self._filepath
        )

        self._sha256_hash: str = ""
        self._internal = False
        self._task_running = False

    def __setattr__(self, __name, __value):
        if hasattr(self, __name) and __name not in {"_internal", "_task_running"} and not self._internal and not self._task_running:
>>>>>>> master
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
        return str(self._identifier)

    def __eq__(  # Checks are ordered from fastest to slowest.
        self,
<<<<<<< HEAD
        other: FileResource | ResourceIdentifier  # | bytes | bytearray | memoryview | object,
=======
        other: FileResource | ResourceIdentifier | bytes | bytearray | memoryview | object,
>>>>>>> master
    ):
        if isinstance(other, ResourceIdentifier):
            return self.identifier() == other
        if isinstance(other, FileResource):
<<<<<<< HEAD
            if self is other:
                return True
            if (
                self._offset == other._offset
                and self._resname == other._resname
                and self._restype == other._restype
                and self._filepath == other._filepath
            ):
                return True

        return NotImplemented
#        self_hash = self.get_hash(reload=False)
#        if not self_hash:
#            return False

#        other_hash: str | None = None
#        if isinstance(other, FileResource):
#            other_hash = other.get_hash(reload=False)
#        if isinstance(other, (bytes, bytearray, memoryview)):
#            other_hash = generate_hash(other)
#        if other_hash is None:
#            return NotImplemented
#        return self_hash == other_hash

    def resname(self) -> str:
        return self._resname

    def resref(self) -> ResRef | None:
=======
            return True if self is other else self._path_ident_obj == other._path_ident_obj
        return NotImplemented

    def resname(self) -> str:
        return self._resname

    def resref(self) -> ResRef:
>>>>>>> master
        from pykotor.common.misc import ResRef
        return ResRef(self._resname)

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

        Raises:
        ------
            FileNotFoundError: File not found on disk.
        """
        self._internal = True
        try:
            if reload:
                self._index_resource()
<<<<<<< HEAD

            with BinaryReader.from_file(self._filepath) as file:
                file.seek(self._offset)
                data: bytes = file.read_bytes(self._size)
                # self._file_hash = generate_hash(data)
                return data
        finally:
            self._internal = False

    def get_hash(
=======
            with BinaryReader.from_file(self._filepath) as file:
                file.seek(self._offset)
                data: bytes = file.read_bytes(self._size)

                if not self._task_running:
                    def background_task(res: FileResource, sentdata: bytes):
                        res._task_running = True
                        res._file_hash = generate_hash(sentdata)
                        res._task_running = False

                    with ThreadPoolExecutor(thread_name_prefix="background_fileresource_sha1hash_calculation") as executor:
                        executor.submit(background_task, self, data)
            return data
        finally:
            self._internal = False

    def get_sha1_hash(
>>>>>>> master
        self,
        *,
        reload: bool = False,
    ) -> str:
        """Returns a lowercase hex string sha1 hash. If FileResource doesn't exist this returns an empty str."""
<<<<<<< HEAD
        if reload:
            if self._filepath.safe_exists():
                self.data()  # Ensure that the hash is calculated
            else:
                return ""
=======
        if reload or not self._file_hash:
            if not self._filepath.safe_isfile():
                return ""  # FileResource or the capsule doesn't exist on disk.
            self._file_hash = generate_hash(self.data())  # Calculate the sha1 hash
>>>>>>> master
        return self._file_hash

    def identifier(self) -> ResourceIdentifier:
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

@dataclass(frozen=True)
class ResourceIdentifier:
    """Class for storing resource name and type, facilitating case-insensitive object comparisons and hashing equal to their string representations."""

    resname: str
    restype: ResourceType
    _cached_filename_str: str = field(default=None, init=False, repr=False)  # type: ignore[reportArgumentType]

    def __post_init__(self):
        # Workaround to initialize a field in a frozen dataclass
        object.__setattr__(self, "_cached_filename_str", None)

    def __hash__(
        self,
    ):
        return hash(str(self).lower())

    def __repr__(
        self,
    ):
        return f"{self.__class__.__name__}(resname='{self.resname}', restype={self.restype!r})"

<<<<<<< HEAD
    def __str__(
        self,
    ):
        ext: str = self.restype.extension
        suffix: str = f".{ext}" if ext else ""
        return f"{self.resname}{suffix}".lower()

    def __eq__(self, other: object):
        if isinstance(other, str):
            return hash(self) == hash(other.lower())
        if isinstance(other, ResourceIdentifier):
            return hash(self) == hash(other)
=======
    def __str__(self) -> str:
        if self._cached_filename_str is None:
            ext: str = self.restype.extension
            suffix: str = f".{ext}" if ext else ""
            cached_str = f"{self.resname}{suffix}".lower()
            object.__setattr__(self, "_cached_filename_str", cached_str)
        return self._cached_filename_str

    def __getitem__(self, key: int) -> str | ResourceType:
        if key == 0:
            return self.resname
        if key == 1:
            return self.restype
        msg = f"Index out of range for ResourceIdentifier. key: {key}"
        raise IndexError(msg)

    def __eq__(self, other: object):
        # sourcery skip: assign-if-exp, reintroduce-else
        if isinstance(other, ResourceIdentifier):
            return str(self) == str(other)
        if isinstance(other, str):
            return str(self) == other.lower()
>>>>>>> master
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
        for dots in range(max_dots + 1, 1, -1):
            with suppress(Exception):
                resname, restype_ext = path_obj.split_filename(dots)
                return ResourceIdentifier(
                    resname,
                    ResourceType.from_extension(restype_ext).validate(),
                )

        # ResourceType is invalid at this point.
        return ResourceIdentifier(path_obj.stem, ResourceType.from_extension(path_obj.suffix))
