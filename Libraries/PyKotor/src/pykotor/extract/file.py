from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Iterator

from loggerplus import RobustLogger

from pykotor.common.stream import BinaryReader
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_bif_file, is_capsule_file
from utility.misc import generate_hash

if TYPE_CHECKING:
    import os

    from typing_extensions import Literal, Self

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
        # This assert sometimes fails when reading dbcs or other weird encoding.
        # for example attempting to read japanese filenames got me 'resource name '?????? (??2Quad) ' cannot start/end with a whitespace'
        # I don't understand what the point of high-level unicode python strings if I can't even work through the issue?
        assert resname == resname.strip(), f"FileResource cannot be constructed, resource name '{resname}' cannot start/end with whitespace."
        self._identifier: ResourceIdentifier = ResourceIdentifier(resname, restype)

        self._resname: str = resname
        self._restype: ResourceType = restype
        self._size: int = size
        self._offset: int = offset
        self._filepath: Path = Path(filepath)

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
        path_obj: Path = Path(path)
        resname, restype = path_obj.stem, ResourceType.from_extension(path_obj.suffix)
        return cls(
            resname=resname,
            restype=restype,
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
    ):
        """Reload information about where the resource can be loaded from."""
        if self.inside_capsule:
            from pykotor.extract.capsule import LazyCapsule  # Prevent circular imports

            capsule = LazyCapsule(self._filepath)
            res: FileResource | None = capsule.info(self._resname, self._restype)
            if res is None and self._identifier == self._filepath.name and self._filepath.is_file():  # The capsule is the resource itself:
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
    ) -> bool:
        """Determines if this FileResource exists.

        This method is completely safe to call.
        """
        try:
            if (
                self.inside_capsule
                and self._path_ident_obj.name.lower() == self._path_ident_obj.parent.name.lower()
                and self.filepath().name != self.filepath().parent.name
            ):
                return self.filepath().is_file()
            if self.inside_capsule:
                from pykotor.extract.capsule import LazyCapsule  # Prevent circular imports
                return bool(LazyCapsule(self._filepath).info(self._resname, self._restype))
            return self.inside_bif or bool(self._filepath.is_file())
        except Exception:  # noqa: BLE001
            RobustLogger().exception("Failed to check existence of FileResource.")
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
                self._index_resource()
            with BinaryReader.from_file(self._filepath) as file:
                file.seek(self._offset)
                data: bytes = file.read_bytes(self._size)

                if not self._hash_task_running:

                    def background_task(res: FileResource, sentdata: bytes):
                        res._hash_task_running = True  # noqa: SLF001
                        res._file_hash = generate_hash(sentdata)  # noqa: SLF001
                        res._hash_task_running = False  # noqa: SLF001

                    with ThreadPoolExecutor(thread_name_prefix="FileResource_SHA1calc") as executor:
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
            if not self._filepath.is_file():
                return ""  # FileResource or the capsule doesn't exist on disk.
            self._file_hash = generate_hash(self.data())
        return self._file_hash

    def as_file_resource(self) -> Self:
        """For unifying use with LocationResult and ResourceResult."""
        return self


@dataclass
class ResourceStatResult:
    st_size: int | None = None
    st_mode: int | None = None
    st_atime: float | None = None
    st_mtime: float | None = None
    st_ctime: float | None = None
    st_nlink: int | None = None
    st_atime_ns: int | None = None
    st_mtime_ns: int | None = None
    st_ctime_ns: int | None = None
    st_ino: int | None = None
    st_dev: int | None = None
    st_uid: int | None = None
    st_gid: int | None = None
    st_file_attributes: int | None = None
    st_reparse_tag: int | None = None
    st_blocks: int | None = None
    st_blksize: int | None = None
    st_rdev: int | None = None
    st_flags: int | None = None

    @classmethod
    def from_stat_result(cls, stat_result: os.stat_result) -> ResourceStatResult:
        return cls(
            st_size=stat_result.st_size,
            st_mode=stat_result.st_mode,
            st_atime=stat_result.st_atime,
            st_mtime=stat_result.st_mtime,
            st_ctime=stat_result.st_ctime,
            st_nlink=stat_result.st_nlink,
            st_atime_ns=stat_result.st_atime_ns,
            st_mtime_ns=stat_result.st_mtime_ns,
            st_ctime_ns=stat_result.st_ctime_ns,
            st_ino=stat_result.st_ino,
            st_dev=stat_result.st_dev,
            st_uid=stat_result.st_uid,
            st_gid=stat_result.st_gid,
            st_file_attributes=getattr(stat_result, "st_file_attributes", None),
            st_reparse_tag=getattr(stat_result, "st_reparse_tag", None),
            st_blocks=getattr(stat_result, "st_blocks", None),
            st_blksize=getattr(stat_result, "st_blksize", None),
            st_rdev=getattr(stat_result, "st_rdev", None),
            st_flags=getattr(stat_result, "st_flags", None),
        )


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

    def __repr__(self):
        return f"ResourceResult({self.resname}, {self.restype}, {self.filepath}, {self.data.__class__.__name__}[{len(self.data)}])"

    def __eq__(self, other: object):
        # sourcery skip: assign-if-exp, reintroduce-else
        if self is other:
            return True
        if isinstance(other, ResourceResult):
            return (
                self.filepath == other.filepath
                and self.resname == other.resname
                and self.restype == other.restype
                and self.data == other.data
            )
        return NotImplemented

    def __len__(self) -> Literal[4]:
        return 4

    def __getitem__(self, key: int) -> str | ResourceType | Path | bytes:
        if key == 0:
            return self.resname
        if key == 1:
            return self.restype
        if key == 2:
            return self.filepath
        if key == 3:
            return self.data
        msg = f"Index out of range for ResourceResult. key: {key}"
        raise IndexError(msg)

    def set_file_resource(self, value: FileResource) -> None:
        # Allow _resource to be set only once
        if self._resource is None:
            object.__setattr__(self, "_resource", value)
        else:
            raise RuntimeError("_resource can only be called once.")

    def as_file_resource(self) -> FileResource:
        if self._resource is None:
            raise RuntimeError(f"{self!r} unexpectedly never assigned a FileResource instance.")
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

    def __repr__(self):
        return f"LocationResult({self.filepath}, {self.offset}, {self.size})"

    def __hash__(self):
        return hash((self.filepath, self.offset, self.size))

    def __eq__(self, other: object):
        # sourcery skip: assign-if-exp, reintroduce-else
        if self is other:
            return True
        if isinstance(other, LocationResult):
            return (
                self.filepath == other.filepath
                and self.size == other.size
                and self.offset == other.offset
            )
        return NotImplemented

    def __len__(self) -> Literal[3]:
        return 3

    def __getitem__(self, key: int) -> Path | int:
        if key == 0:
            return self.filepath
        if key == 1:
            return self.offset
        if key == 2:
            return self.size
        msg = f"Index out of range for LocationResult. key: {key}"
        raise IndexError(msg)

    def set_file_resource(self, value: FileResource) -> None:
        # Allow _resource to be set only once
        if self._resource is None:
            object.__setattr__(self, "_resource", value)
        else:
            raise RuntimeError("set_file_resource can only be called once.")

    def as_file_resource(self) -> FileResource:
        if self._resource is None:
            raise RuntimeError(f"{self!r} unexpectedly never assigned a FileResource instance.")
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
    _cached_filename_str: str = field(default=None, init=False, repr=False)  # pyright: ignore[reportArgumentType]
    _lower_resname_str: str = field(default=None, init=False, repr=False)  # pyright: ignore[reportArgumentType]

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

    def validate(self) -> Self:
        if self.restype == ResourceType.INVALID:
            msg = f"Invalid resource: '{self}'"
            raise ValueError(msg)
        return self

    @classmethod
    def identify(cls, obj: ResourceIdentifier | os.PathLike | str) -> ResourceIdentifier:
        return obj if isinstance(obj, (cls, ResourceIdentifier)) else cls.from_path(obj)

    @classmethod
    def from_path(cls, file_path: os.PathLike | str) -> Self:
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
            return cls("", ResourceType.from_extension(""))

        max_dots: int = path_obj.name.count(".")
        for dots in range(max_dots + 1, 1, -1):
            with suppress(Exception):
                resname, restype_ext = path_obj.split_filename(dots)
                return cls(
                    resname,
                    ResourceType.from_extension(restype_ext).validate(),
                )

        # ResourceType is invalid at this point.
        return cls(path_obj.stem, ResourceType.from_extension(path_obj.suffix))
