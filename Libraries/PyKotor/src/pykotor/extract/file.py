from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Iterator

from pykotor.common.stream import BinaryReader
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_bif_file, is_capsule_file
from utility.logger_util import RobustRootLogger
from utility.misc import generate_hash
from utility.system.path import Path, PurePath

if TYPE_CHECKING:
    import os

    from typing_extensions import Self

    from pykotor.common.misc import ResRef
    from pykotor.extract.capsule import LazyCapsule


class FileResource:
    """Stores information for a resource regarding its name, type and where the data can be loaded from."""
    def __new__(cls, resname: str | os.PathLike, *args, **kwargs) -> Self | LazyCapsule:
        # Check if the resource should be handled by LazyCapsule
        if cls is FileResource and is_capsule_file(resname):
            from pykotor.extract.capsule import LazyCapsule
            cls = LazyCapsule

        # Check if the current class's __new__ is overridden beyond FileResource's __new__
        if cls.__new__ is not FileResource.__new__:
            return super().__new__(cls, resname, *args, **kwargs)
        # If not, proceed with the default object creation process
        return object.__new__(cls)

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

        self._file_hash: str = ""

        self._path_ident_obj: Path = (
            self._filepath / str(self._identifier)
            if self.inside_capsule or self.inside_bif
            else self._filepath
        )

        self._sha256_hash: str = ""
        self._internal: bool = False
        self._hash_task_running: bool = False

    def __setattr__(self, name, value):
        if (
            hasattr(self, name)
            and name not in {"_internal", "_hash_task_running"}
            and not getattr(self, "_internal", True)
            and not getattr(self, "_hash_task_running", True)
        ):
            msg = f"Cannot modify immutable FileResource instance, attempted `setattr({self!r}, {name!r}, {value!r})`"
            raise RuntimeError(msg)

        return super().__setattr__(name, value)

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

    def __eq__(
        self,
        other: FileResource | ResourceIdentifier | bytes | bytearray | memoryview | object,
    ):
        if self is other:
            return True
        if isinstance(other, ResourceIdentifier):
            return self.identifier() == other
        if isinstance(other, FileResource):
            return True if self is other else self._path_ident_obj == other._path_ident_obj
        return NotImplemented

    @classmethod
    def from_path(cls, path: os.PathLike | str) -> Self:
        path_obj: Path = Path.pathify(path)
        return cls(
            resname=path_obj.stem,
            restype=ResourceType.from_extension(path_obj.suffix),
            size=path_obj.stat().st_size,
            offset=0,
            filepath=path_obj,
        )

    def identifier(self) -> ResourceIdentifier:
        """Returns the ResourceIdentifier instance for this resource."""
        return self._identifier

    def resname(self) -> str:
        return self._resname

    def resref(self) -> ResRef:
        """Returns ResRef(self.resname())."""
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

    def filename(self) -> str:
        """Return the name of the file.

        Please note that self.filepath().name will not always be the same as self.filename() or str(self.identifier()). See self.path_ident() for more information.
        """
        return str(self._identifier)

    def filepath(self) -> Path:
        """Returns the physical path to a file the data can be loaded from.

        Please note that self.filepath().name will not always be the same as str(self.identifier()) or self.filename(). See self.path_ident() for more information.
        """
        return self._filepath

    def path_ident(self) -> Path:
        """Returns a pathlib.Path identifier for this resource.

        More specifically:
        - if inside ERF/BIF/RIM/MOD/SAV, i.e. if the check `any((self.inside_capsule, self.inside_bif))` passes:
            return self.filepath().joinpath(self.filename())
        - else:
            return self.filepath()
        """
        return self._path_ident_obj

    def offset(self) -> int:
        """Offset to where the data is stored, at the filepath."""
        return self._offset

    def _index_resource(
        self,
        *,
        reload: bool = False,
    ):
        """Reload information about where the resource can be loaded from."""
        if self.inside_capsule:
            from pykotor.extract.capsule import Capsule  # Prevent circular imports

            capsule = Capsule(self._filepath)
            res: FileResource | None = capsule.info(self._resname, self._restype, reload=reload)
            if res is None and self._identifier == self._filepath.name and self._filepath.safe_isfile():  # the capsule is the resource itself:
                self._offset = 0
                self._size = self._filepath.stat().st_size
                return
            if res is None:
                import errno
                msg = f"Resource '{self._identifier}' not found in Capsule"
                raise FileNotFoundError(errno.ENOENT, msg, str(self._filepath))

            self._offset = res.offset()
            self._size = res.size()
        elif not self.inside_bif:  # bifs are read-only, offset/data will never change.
            self._offset = 0
            self._size = self._filepath.stat().st_size

    def exists(
        self,
        *,
        reload: bool = False,
    ) -> bool:
        """Determines if this FileResource exists.

        This method is completely safe to call.
        """
        try:
            if self.inside_capsule:
                from pykotor.extract.capsule import Capsule  # Prevent circular imports
                return bool(Capsule(self._filepath).info(self._resname, self._restype, reload=reload))
            return self.inside_bif or bool(self._filepath.safe_isfile())
        except Exception:
            RobustRootLogger().exception("Failed to check existence of FileResource.")
            return False

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
                self._index_resource(reload=reload)
            with BinaryReader.from_file(self._filepath) as file:
                file.seek(self._offset)
                data: bytes = file.read_bytes(self._size)

                if not self._hash_task_running:

                    def background_task(res: FileResource, sentdata: bytes):
                        res._hash_task_running = True  # noqa: SLF001
                        res._file_hash = generate_hash(sentdata)  # noqa: SLF001
                        res._hash_task_running = False  # noqa: SLF001

                    with ThreadPoolExecutor(thread_name_prefix="background_fileresource_sha1hash_calculation") as executor:
                        executor.submit(background_task, self, data)
            return data
        finally:
            self._internal = False

    def get_sha1_hash(
        self,
        *,
        reload: bool = False,
    ) -> str:
        """Returns a lowercase hex string sha1 hash. If FileResource doesn't exist this returns an empty str."""
        if reload or not self._file_hash:
            if not self._filepath.safe_isfile():
                return ""  # FileResource or the capsule doesn't exist on disk.
            self._file_hash = generate_hash(self.data())  # Calculate the sha1 hash
        return self._file_hash

    def as_file_resource(self) -> Self:
        """For unifying use with LocationResult and ResourceResult."""
        return self

@dataclass(frozen=True)
class ResourceResult:
    resname: str
    restype: ResourceType
    filepath: Path
    data: bytes
    _resource: FileResource | None = field(repr=False, default=None, init=False)  # Metadata is hidden in the representation

    def __iter__(self) -> Iterator[str | ResourceType | Path | bytes]:
        """This method enables unpacking like tuple behavior."""
        return iter((self.resname, self.restype, self.filepath, self.data))

    def __hash__(self):
        return hash(self.identifier())

    def set_file_resource(self, value: FileResource) -> None:
        # Allow _resource to be set only once
        if self._resource is None:
            object.__setattr__(self, "_resource", value)
        else:
            raise RuntimeError("_resource can only be called once.")

    def as_file_resource(self) -> FileResource:
        return self._resource

    def identifier(self) -> ResourceIdentifier:
        return ResourceIdentifier(self.resname, self.restype)


@dataclass(frozen=True)
class LocationResult:
    filepath: Path
    offset: int
    size: int
    _resource: FileResource | None = field(repr=False, default=None, init=False)  # Metadata is hidden in the representation

    def __iter__(self) -> Iterator[Path | int]:
        """This method enables unpacking like tuple behavior."""
        return iter((self.filepath, self.offset, self.size))

    def set_file_resource(self, value: FileResource) -> None:
        # Allow _resource to be set only once
        if self._resource is None:
            object.__setattr__(self, "_resource", value)
        else:
            raise RuntimeError("set_file_resource can only be called once.")

    def as_file_resource(self) -> FileResource:
        return self._resource

    def identifier(self) -> ResourceIdentifier:
        if self._resource is None:
            raise RuntimeError(f"{self!r} unexpectedly never assigned a FileResource instance.")
        return self._resource.identifier()


@dataclass(frozen=True)
class ResourceIdentifier:
    """Class for storing resource name and type, facilitating case-insensitive object comparisons and hashing equal to their string representations."""

    resname: str
    restype: ResourceType
    _cached_filename_str: str = field(default=None, init=False, repr=False)  # type: ignore[reportArgumentType]
    _lower_resname_str: str = field(default=None, init=False, repr=False)  # type: ignore[reportArgumentType]

    def __post_init__(self):
        # Workaround to initialize a field in a frozen dataclass
        ext: str = self.restype.extension
        suffix: str = f".{ext}" if ext else ""
        lower_filename_str = f"{self.resname}{suffix}".lower()
        object.__setattr__(self, "_cached_filename_str", lower_filename_str)
        object.__setattr__(self, "_lower_resname_str", self.resname.lower())

    def __hash__(
        self,
    ):
        return hash(str(self))

    def __repr__(
        self,
    ):
        return f"{self.__class__.__name__}(resname='{self.resname}', restype={self.restype!r})"

    def __str__(self) -> str:
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
        if self is other:
            return True
        if isinstance(other, ResourceIdentifier):
            return str(self) == str(other)
        if isinstance(other, str):
            return str(self) == other.lower()
        return NotImplemented

    @property
    def lower_resname(self) -> str:
        return self.resname.lower()

    def unpack(self) -> tuple[str, ResourceType]:
        return self.resname, self.restype

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
            path_obj = PurePath.pathify(file_path)
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
