from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Iterator

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs, reportMissingModuleSource]

from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_bif_file, is_capsule_file

if TYPE_CHECKING:
    import os

    from typing_extensions import Literal, Self  # pyright: ignore[reportMissingModuleSource]

    from pykotor.common.misc import ResRef


# Global file data cache with modification time tracking
# Key: (filepath, offset, size) -> Value: (data, mtime)
_FILE_DATA_CACHE: dict[tuple[Path, int, int], tuple[bytes, float]] = {}

# Cache valid ResourceTypes sorted by extension length (longest first) for efficient matching
# This avoids iterating through all ResourceTypes for every file (massive performance improvement)
_RESOURCE_TYPE_CACHE: list[tuple[ResourceType, str]] | None = None


def _get_cached_resource_types() -> list[tuple[ResourceType, str]]:
    """Get cached list of valid ResourceTypes with extensions, sorted by extension length (longest first).
    
    This cache is computed once and reused for all file parsing operations.
    """
    global _RESOURCE_TYPE_CACHE  # noqa: PLW0603
    if _RESOURCE_TYPE_CACHE is None:
        _RESOURCE_TYPE_CACHE = sorted(
            [
                (rt, f".{rt.extension}")
                for rt in ResourceType.__members__.values()
                if not rt.is_invalid and rt.extension
            ],
            key=lambda x: len(x[1]),
            reverse=True,  # Longest extensions first (handles multi-part extensions like "res.xml")
        )
    return _RESOURCE_TYPE_CACHE


def clear_file_data_cache() -> None:
    """Clear the global file data cache to free memory."""
    _FILE_DATA_CACHE.clear()


def get_file_data_cache_stats() -> dict[str, int]:
    """Get statistics about the file data cache.

    Returns:
        Dictionary with cache statistics (entries, total_size_bytes)
    """
    total_size = sum(len(data) for data, _ in _FILE_DATA_CACHE.values())
    return {
        "entries": len(_FILE_DATA_CACHE),
        "total_size_bytes": total_size,
    }


class FileResource:
    """Stores information for a resource regarding its name, type and where the data can be loaded from.
    
    Represents a resource entry with metadata (name, type, size, offset) and file location.
    Used throughout PyKotor for resource abstraction and lazy loading.
    
    References:
    ----------
        vendor/KotOR_IO/KotOR_IO/File Formats/KFile.cs (Resource file abstraction)
        vendor/KotOR-dotNET/AuroraFile.cs (Aurora file format abstraction)
        vendor/reone/src/libs/resource/resource.h (Resource abstraction)
        vendor/xoreos-tools/src/common/types.h (Resource type definitions)
    """

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

        self._path_ident_obj: Path = (
            self._filepath / str(self._identifier)
            if self.inside_capsule or self.inside_bif
            else self._filepath
        )

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
            if self.inside_capsule and self._path_ident_obj.name.lower() == self._path_ident_obj.parent.name.lower() and self.filepath().name != self.filepath().parent.name:
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
        if reload:
            self._index_resource()
        with self._filepath.open("rb") as file:
            file.seek(self._offset)
            data: bytes = file.read(self._size)
        return data

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
        if key == 2:  # noqa: PLR2004
            return self.filepath
        if key == 3:  # noqa: PLR2004
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
        if key == 2:  # noqa: PLR2004
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

    resname: str = field(default_factory=str)
    restype: ResourceType = field(default=ResourceType.INVALID)
    _cached_filename_str: str = field(default=None, init=False, repr=False)  # pyright: ignore[reportArgumentType]  # type: ignore[assignment]
    _lower_resname_str: str = field(default=None, init=False, repr=False)  # pyright: ignore[reportArgumentType]  # type: ignore[assignment]
    _cached_hash: int = field(default=None, init=False, repr=False)  # pyright: ignore[reportArgumentType]  # type: ignore[assignment]

    def __post_init__(self):
        # Workaround to initialize a field in a frozen dataclass
        ext: str = self.restype.extension
        suffix: str = f".{ext}" if ext else ""
        lower_filename_str: str = f"{self.resname}{suffix}".lower()
        object.__setattr__(self, "resname", str(self.resname))
        object.__setattr__(self, "_cached_filename_str", lower_filename_str)
        object.__setattr__(self, "_lower_resname_str", self.resname.lower())
        # Pre-compute and cache hash for performance
        object.__setattr__(self, "_cached_hash", hash(lower_filename_str))

    def __hash__(self):
        return self._cached_hash

    def __repr__(self):
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
        # Use identity check first (fastest path)
        if self is other:
            return True
        # Use cached string comparison (faster than str() call)
        if isinstance(other, ResourceIdentifier):
            return self._cached_filename_str == other._cached_filename_str
        if isinstance(other, str):
            return self._cached_filename_str == other.lower()
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
            - Splits the file path into resource name and type
            - Attempts to validate the extracted resource type, starting from the full extension
            - If validation fails, progressively shortens the extension and tries again
            - If all attempts fail, uses stem as name and sets type to INVALID
        """
        path_obj = PurePath(file_path)

        def _split_resource_filename(p: PurePath) -> tuple[str, ResourceType]:
            filename = p.name
            lower_filename = filename.lower()

            # Use cached ResourceTypes sorted by extension length (longest first)
            # This is much faster than iterating through all ResourceType.__members__.values() every time
            chosen_restype: ResourceType | None = None
            chosen_suffix_length = 0
            for candidate, suffix in _get_cached_resource_types():
                # Early exit optimization: if suffix is longer than filename, skip
                if len(suffix) > len(lower_filename):
                    continue
                # Early exit: if we already found a match longer than remaining candidates, we're done
                # (since we're sorted longest-first, any remaining matches would be shorter)
                if chosen_suffix_length > 0 and len(suffix) <= chosen_suffix_length:
                    break
                if lower_filename.endswith(suffix):
                    chosen_restype = candidate
                    chosen_suffix_length = len(suffix)
                    # Perfect match - filename ends with this extension, can't get better
                    if len(suffix) == len(lower_filename):
                        break

            if chosen_restype is not None and chosen_suffix_length > 0:
                resname_candidate = filename[:-chosen_suffix_length]
                return resname_candidate, chosen_restype

            if filename.endswith("."):
                return filename, ResourceType.from_extension("")

            if filename.startswith(".") and filename.count(".") == 1:
                return filename, ResourceType.from_extension("")

            return p.stem, ResourceType.from_extension(p.suffix)

        resname, restype = _split_resource_filename(path_obj)
        return cls(resname, restype)
