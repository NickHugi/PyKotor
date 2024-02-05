from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, NamedTuple
import lzma
import os
from typing import TYPE_CHECKING, Any, NamedTuple

from pykotor.common.stream import BinaryReader
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_bif_file, is_bzf_file, is_capsule_file
from utility.misc import generate_hash
from utility.system.path import Path, PurePath

if TYPE_CHECKING:
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

        self._resname: str = resname
        self._restype: ResourceType = restype
        self._size: int = size
        self._offset: int = offset
        self._filepath: Path = Path.pathify(filepath)

        self.inside_capsule: bool = is_capsule_file(self._filepath)
        self.inside_bif: bool = is_bif_file(self._filepath)
        self.inside_bzf = is_bzf_file(self._filepath)

        self._file_hash: str = ""
        self._identifier = ResourceIdentifier(self._resname, self._restype)

        self._path_ident_obj: Path = (
            self._filepath / str(self._identifier)
            if self.inside_capsule or self.inside_bif
            else self._filepath
        )

        self._sha256_hash: str = ""
        self._internal = False

    def __setattr__(self, __name, __value):
        if hasattr(self, __name):
            if __name == "_internal" or self._internal:
                return super().__setattr__(__name, __value)

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
        other: FileResource | ResourceIdentifier | bytes | bytearray | memoryview | object,
    ):
        if isinstance(other, ResourceIdentifier):
            return self.identifier() == other
        if isinstance(other, FileResource):
            if self is other:
                return True
            return self._path_ident_obj == other._path_ident_obj

        if not self._file_hash:
            return False

        if isinstance(other, (os.PathLike, bytes, bytearray, memoryview)):
            return self._file_hash == generate_hash(other)

        return NotImplemented

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

    def decompress_lzma1(  # TODO: move to a utility class or perhaps the chitin.py?
        self,
        data: bytes,
        output_size: int,
        no_end_marker: bool = False,  # From xoreos but idk what this implies
    ) -> bytes:
        temp_filepath = Path.cwd().joinpath(str(self.identifier()))
        with temp_filepath.open("wb") as f:
            print(f"Temporarily writing compressed data to '{temp_filepath}'")
            f.write(data)  # temporarily store the data, remove later once lzma decompress is working.

        props_size = 5  # For LZMA1, the properties size is usually 5 bytes.
        if len(data) < props_size:
            msg = "Input data too short to contain LZMA1 properties."
            raise ValueError(msg)

        # Extract properties and prepare the filter chain.
        props = data[:props_size]
        lzma_filter = {
            'id': lzma.FILTER_LZMA1,
            'dict_size': 1 << 23,  # You might need to adjust this based on actual properties.
            'lc': props[0] % 9,
            'lp': (props[0] // 9) % 5,
            'pb': props[0] // (9 * 5),
        }
        filter_chain = [lzma_filter]

        # Adjust data to exclude the properties bytes.
        data = data[props_size:]

        try:
            # Decompress using FORMAT_RAW with the specified filter chain.
            decompressed_data = lzma.decompress(data, format=lzma.FORMAT_RAW, filters=filter_chain)

            # Check if the decompressed data matches the expected output size, if specified.
            if len(decompressed_data) != output_size:
                if no_end_marker and len(decompressed_data) <= output_size:
                    # Allow for no end marker and data being smaller than expected.
                    pass
                else:
                    msg = "Decompressed data size does not match the expected output size."
                    raise ValueError(msg)

        except lzma.LZMAError as e:
            msg = "Failed to decompress LZMA1 data."
            raise ValueError(msg) from e

        return decompressed_data

        try:
            # Attempt to decompress using the LZMA alone format, which is used for LZMA1 data.
            # This assumes the data starts with the LZMA properties header.
            decompressed_data = lzma.decompress(data, format=lzma.FORMAT_ALONE)

            # If no_end_marker is True and decompression was successful, but we expect no end marker,
            # we would typically check if the entire output buffer was filled. However, Python's lzma
            # module does not give us a straightforward way to enforce or check this directly.

            # Check if the decompressed data matches the expected output size if specified.
            if output_size is not None and len(decompressed_data) != output_size:
                msg = "Decompressed data size does not match the expected output size."
                raise ValueError(msg)

        except lzma.LZMAError as e:
            msg = "Failed to decompress LZMA1 data."
            raise ValueError(msg) from e
        else:
            return decompressed_data

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
        self._internal = True
        try:
            if reload:
                self._index_resource()
            with BinaryReader.from_file(self._filepath) as file:
                file.seek(self._offset)
                data: bytes = file.read_bytes(self._size)
                if self.inside_bzf:
                    data = self.decompress_lzma1(data, self._size)

                with ThreadPoolExecutor(thread_name_prefix="background_fileresource_sha1hash_calculation") as executor:
                    future = executor.submit(generate_hash, data)
                    self._file_hash = future.result()
            return data
        finally:
            self._internal = False

    def get_sha256_hash(
        self,
        *,
        reload: bool = False,
    ) -> str:
        """Returns a lowercase hex string sha1 hash. If FileResource doesn't exist this returns an empty str."""
        if reload or not self._file_hash:
            if not self._filepath.safe_isfile():
                return ""  # FileResource or the capsule doesn't exist on disk.
            self.data()  # Calculate the sha1 hash
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

    def __hash__(
        self,
    ):
        return hash(CaseInsensitiveWrappedStr(str(self)))

    def __repr__(
        self,
    ):
        return f"{self.__class__.__name__}(resname={self.resname}, restype={self.restype!r})"

    def __str__(
        self,
    ):
        ext = self.restype.extension
        suffix = f".{ext}" if ext else ""
        return f"{self.resname.lower()}{suffix.lower()}"

    def __eq__(
        self,
        __value: str | ResourceIdentifier,
    ):
        if isinstance(__value, str):
            __value = self.from_path(__value)
        if isinstance(__value, ResourceIdentifier):
            return hash(self) == hash(__value)
        return NotImplemented

    def validate(self, *, strict=False):
        from pykotor.common.misc import ResRef
        if self.restype == ResourceType.INVALID or strict and not ResRef.is_valid(self.resname):
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
