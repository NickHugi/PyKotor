from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Iterator

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]

from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_bif_file, is_capsule_file

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

        self._path_ident_obj: Path = (
            self._filepath / str(self._identifier)
            if self.inside_capsule or self.inside_bif
            else self._filepath
        )

        self._internal: bool = False

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
            with self._filepath.open("rb") as file:
                file.seek(self._offset)
                data: bytes = file.read(self._size)
            return data
        finally:
            self._internal = False

    def as_file_resource(self) -> Self:
        """For unifying use with LocationResult and ResourceResult."""
        return self

    def __setattr__(self, name, value):
        if (
            hasattr(self, name)
            and name not in {"_internal",}
            and not getattr(self, "_internal", True)
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
    _cached_filename_str: str = field(default=None, init=False, repr=False)  # pyright: ignore[reportAssignmentType, reportArgumentType]
    _lower_resname_str: str = field(default=None, init=False, repr=False)  # pyright: ignore[reportAssignmentType, reportArgumentType]

    def __post_init__(self):
        # Workaround to initialize a field in a frozen dataclass
        ext: str = self.restype.extension
        suffix: str = f".{ext}" if ext else ""
        lower_filename_str: str = f"{self.resname}{suffix}".lower()
        object.__setattr__(self, "resname", str(self.resname))
        object.__setattr__(self, "_cached_filename_str", lower_filename_str)
        object.__setattr__(self, "_lower_resname_str", self.resname.lower())

    def __hash__(self):
        return hash(str(self))

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
            - Splits the file path into resource name and type
            - Attempts to validate the extracted resource type, starting from the full extension
            - If validation fails, progressively shortens the extension and tries again
            - If all attempts fail, uses stem as name and sets type to INVALID
        """
        try:
            path_obj = PurePath(file_path)
        except Exception:  # noqa: BLE001
            resname, ext = str(file_path).split(".", 1)
            return cls(resname, ResourceType.from_extension(ext))
        name_parts = path_obj.name.split(".")
        extension_parts = name_parts[1:]
        while extension_parts:
            ext = ".".join(extension_parts)
            restype = ResourceType.from_extension(ext)
            if restype:
                resname = ".".join(name_parts[:-len(extension_parts)])
                return cls(resname, restype)
            extension_parts.pop(0)
        return cls(path_obj.stem, ResourceType.from_invalid(extension=path_obj.suffix.lstrip(".")))
