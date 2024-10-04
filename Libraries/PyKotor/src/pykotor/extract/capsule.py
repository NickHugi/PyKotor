from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, cast

from pykotor.common.stream import BinaryReader
from pykotor.extract.file import FileResource, ResourceIdentifier, ResourceResult
from pykotor.resource.formats.erf import ERF, ERFType, write_erf
from pykotor.resource.formats.rim import RIM, write_rim
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_any_erf_type_file, is_capsule_file, is_rim_file

if TYPE_CHECKING:
    import os

    from collections.abc import Iterator

    from typing_extensions import Self


class LazyCapsule(FileResource):
    """LazyCapsule object is used for loading the list of resources stored in the .erf/.rim/.mod/.sav files used by the game.

    Resource data is not actually stored in memory by default but is instead loaded up on demand with the
    LazyCapsule.resource() method. Use the Capsule, RIM, or ERF classes if you want to solely work with capsules in memory.
    """
    def __init__(
        self,
        path: os.PathLike | str,
        *,
        create_nonexisting: bool = False,
    ):
        """Initialize a Capsule object.

        Args:
        ----
            path: Path to the capsule file
            create_nonexisting: Whether to create the file if it doesn't exist

        Returns:
        -------
            self: The initialized Capsule object

        Processing Logic:
        ----------------
            - Check if the path points to a valid capsule file
            - If create_nonexisting is True and file doesn't exist:
                - Create RIM file if rim extension
                - Create ERF file if erf/mod extension
            - Initialize self._path and self._resources attributes
            - Reload resources from file.
        """
        ident = ResourceIdentifier.from_path(path)
        c_filepath = Path(path)
        if not is_capsule_file(c_filepath):
            msg = f"Invalid file extension in capsule filepath '{c_filepath}'."
            raise ValueError(msg)
        if create_nonexisting and not c_filepath.is_file():
            if is_rim_file(c_filepath):
                write_rim(RIM(), c_filepath)
            elif is_any_erf_type_file(c_filepath):
                write_erf(ERF(ERFType.from_extension(c_filepath.suffix)), c_filepath)
        super().__init__(*ident.unpack(), c_filepath.stat().st_size, 0x0, c_filepath)

    def __iter__(
        self,
    ) -> Iterator[FileResource]:
        yield from self.resources()

    def __len__(
        self,
    ):
        return len(self.resources())

    def resource(
        self,
        resref: str,
        restype: ResourceType,
    ) -> bytes | None:
        """Returns the bytes data of the specified resource. If the resource does not exist then returns None instead.

        Args:
        ----
            resref: The resource ResRef.
            restype: The resource type.

        Returns:
        -------
            bytes data of the resource or None if not existing.
        """
        query = ResourceIdentifier(resref, restype)
        resource: FileResource | None = next(
            (resource for resource in self.resources() if resource == query),
            None,
        )
        return resource.data() if resource else None

    def batch(
        self,
        queries: list[ResourceIdentifier],
    ) -> dict[ResourceIdentifier, ResourceResult | None]:
        """Batches queries against a capsule.

        Args:
        ----
            queries: list[ResourceIdentifier]: The queries to batch

        Returns:
        -------
            dict[ResourceIdentifier, ResourceResult | None]: The results for each query keyed by query

        Processing Logic:
        ----------------
            - Reloads capsule resources from erf/rim if reload is True
            - Initializes results dict to return
            - Opens capsule file as binary reader
            - Loops through queries
                - Sets result to None
                - Checks if resource exists in capsule
                - If so, seeks to offset, reads bytes and sets result
            - Closes reader
            - Returns results dict.
        """
        results: dict[ResourceIdentifier, ResourceResult | None] = {}
        with BinaryReader.from_file(self._filepath) as reader:
            for query in queries:
                results[query] = None

                resource: FileResource | None = next(
                    (resource for resource in self.resources() if resource == query),
                    None,
                )
                if resource is None:
                    continue

                reader.seek(resource.offset())
                data: bytes = reader.read_bytes(resource.size())
                results[query] = ResourceResult(
                    query.resname,
                    query.restype,
                    self._filepath,
                    data,
                )
        return results

    def contains(
        self,
        resref: str,
        restype: ResourceType,
    ) -> bool:
        """Check if a resource exists within this capsule.

        Args:
        ----
            resref: str: Resource reference
            restype: ResourceType: Resource type

        Returns:
        -------
            bool: True if resource exists, False otherwise

        Checks if a resource exists:
            - Constructs a ResourceIdentifier from resref and restype
            - Searches the ERF/RIM for a matching resource
            - Returns True if a match is found, False otherwise.
        """
        query = ResourceIdentifier(resref, restype)
        return bool(
            next(
                (resource for resource in self.resources() if resource == query),
                False,
            )
        )

    def info(
        self,
        resref: str,
        restype: ResourceType,
    ) -> FileResource | None:
        """Get file resource by reference and type.

        Args:
        ----
            resref: Resource reference as string
            restype: Resource type

        Returns:
        -------
            FileResource: Matched file resource

        Processing Logic:
        ----------------
            - Check if reload is True and call reload()
            - Create query object from resref and restype
            - Return first matching resource.
        """
        query = ResourceIdentifier(resref, restype)
        return next((resource for resource in self.resources() if resource == query), None)

    def resources(
        self,
    ) -> list[FileResource]:
        """Get the list of FileResources from the ERF/RIM file.

        Args:
        ----
            self: Capsule object to reload

        Returns:
        -------
            resources: list[FileResource] A list of FileResources from the ERF/RIM.

        Processing Logic:
        ----------------
            - Check if capsule exists on disk and print error if not
            - Open file and read header
            - Call appropriate reload method based on file type
            - Raise error if unknown file type.
        """
        with BinaryReader.from_file(self._filepath) as reader:
            file_type = reader.read_string(4)
            reader.skip(4)  # file version

            if file_type in (member.value for member in ERFType):
                resources = self._load_erf(reader)
            elif file_type == "RIM ":
                resources = self._load_rim(reader)
            else:
                msg = f"File '{self._filepath}' must be a ERF/MOD/SAV/RIM capsule, '{self._filepath.suffix}' is not implemented."
                raise NotImplementedError(msg)
        #get_root_logger().debug("%s.resources() call, found %s total resources inside %s", self.__class__.__name__, len(resources), self._filepath)
        return resources

    def add(
        self,
        resname: str,
        restype: ResourceType,
        resdata: bytes,
    ):
        """Adds a resource to the capsule and writes the updated capsule to the disk.

        Args:
        ----
            resname: Name of the resource to add.
            restype: Type of the resource to add.
            resdata: Data of the resource to add.

        Returns:
        -------
            None: No value is returned.

        Processing Logic:
        ----------------
            - Checks if the file is RIM or a type of ERF
            - Reads the file as appropriate container
            - Calls set_data to add the resource
            - Writes the container back to the file.
        """
        def _add_to(container: RIM | ERF):
            container.set_data(resname, restype, resdata)
            for resource in self.resources():
                container.set_data(resource.resname(), resource.restype(), resource.data())
            self._hash_task_running = True
            self._file_hash = ""
            self._hash_task_running = False

        if is_rim_file(self._filepath.name):
            container = RIM()
            _add_to(container)
            write_rim(container, self._filepath)
        elif is_any_erf_type_file(self._filepath.name):
            container = ERF(ERFType.from_extension(self._filepath))
            _add_to(container)
            write_erf(container, self._filepath)
        else:
            msg = f"File '{self._filepath}' is not a ERF/MOD/SAV/RIM capsule."
            raise NotImplementedError(msg)

    def delete(
        self,
        resname: str,
        restype: ResourceType,
    ):
        """Removes a resource from the capsule and writes the updated capsule to the disk.

        Args:
        ----
            resname: Name of the resource to add.
            restype: Type of the resource to add.

        Returns:
        -------
            None: No value is returned.

        Processing Logic:
        ----------------
            - Checks if the file is RIM or a type of ERF
            - Reads the file as appropriate container
            - Calls ERF.remove or RIM.remove
            - Writes the container back to the file.
        """
        def _remove_from(container: RIM | ERF):
            for resource in self.resources():
                if resource.resname().lower() == resname.lower() and resource.restype() is restype:
                    continue
                container.set_data(resource.resname(), resource.restype(), resource.data())
            self._hash_task_running = True
            self._file_hash = ""
            self._hash_task_running = False

        if is_rim_file(self._filepath.name):
            container = RIM()
            _remove_from(container)
            write_rim(container, self._filepath)
        elif is_any_erf_type_file(self._filepath.name):
            container = ERF(ERFType.from_extension(self._filepath))
            _remove_from(container)
            write_erf(container, self._filepath)
        else:
            msg = f"File '{self._filepath}' is not a ERF/MOD/SAV/RIM capsule."
            raise NotImplementedError(msg)

    def as_cached_erf(self, erf_type: ERFType | None = None) -> ERF:
        erf: ERF = ERF() if erf_type is None else ERF(ERFType(erf_type))
        for resource in self.resources():
            erf.set_data(resource.resname(), resource.restype(), resource.data())
        return erf

    def as_cached_rim(self) -> RIM:
        rim: RIM = RIM()
        for resource in self.resources():
            rim.set_data(resource.resname(), resource.restype(), resource.data())
        return rim

    def as_cached(self) -> ERF | RIM:
        return (
            self.as_cached_erf()
            if is_any_erf_type_file(self._filepath)
            else self.as_cached_rim()
        )

    def _load_erf(
        self,
        reader: BinaryReader,
    ) -> list[FileResource]:
        """Loads an ERF resource file.

        Args:
        ----
            reader: BinaryReader - Reader for the ERF file

        Returns:
        -------
            resources: list[FileResource] A list of FileResources from the ERF.

        Processing Logic:
        ----------------
            - Skips header data
            - Reads entry count and offset tables
            - Loops through keys to read resource references, IDs and types
            - Seeks to resource data offset table
            - Loops to read offsets and sizes and populate resource objects.
        """
        resources: list[FileResource] = []
        reader.skip(8)
        entry_count = reader.read_uint32()
        reader.skip(4)
        offset_to_keys = reader.read_uint32()
        offset_to_resources = reader.read_uint32()

        resrefs:  list[str] = []
        resids:   list[int] = []
        restypes: list[ResourceType] = []
        reader.seek(offset_to_keys)
        for _ in range(entry_count):
            resref = reader.read_string(16)
            resrefs.append(resref)
            resids.append(reader.read_uint32())
            restype = reader.read_uint16()
            restypes.append(ResourceType.from_id(restype))
            reader.skip(2)

        reader.seek(offset_to_resources)
        for i in range(entry_count):
            res_offset: int = reader.read_uint32()
            res_size:   int = reader.read_uint32()
            resources.append(FileResource(resrefs[i], restypes[i], res_size, res_offset, self._filepath))
        return resources

    def _load_rim(
        self,
        reader: BinaryReader,
    ) -> list[FileResource]:
        """Load resources from a rim file.

        Args:
        ----
            reader: BinaryReader: The binary reader to read data from

        Returns:
        -------
            resources: list[FileResource] A list of FileResources from the rim.

        Processing Logic:
        ----------------
            - Skip the first 4 bytes of unknown data
            - Read the entry count from the next 4 bytes
            - Read the offset to entries from the next 4 bytes
            - Seek to the offset to entries
            - Loop through each entry
                - Read the 16 byte resref string
                - Read the 4 byte resource type id and convert to enum
                - Skip the next 4 bytes of unknown data
                - Read the 4 byte offset
                - Read the 4 byte size
        """
        resources: list[FileResource] = []
        reader.skip(4)
        entry_count = reader.read_uint32()
        offset_to_entries = reader.read_uint32()

        reader.seek(offset_to_entries)
        for _ in range(entry_count):
            resref = reader.read_string(16)
            restype = ResourceType.from_id(reader.read_uint32())
            reader.skip(4)
            offset = reader.read_uint32()
            size = reader.read_uint32()
            resources.append(FileResource(resref, restype, size, offset, self._filepath))
        return resources


class Capsule(LazyCapsule):
    """Capsule object is used for loading the list of resources stored in the .erf/.rim/.mod/.sav files used by the game.

    Resource data is stored in memory on initialization and only reloaded when self.reload() is called or a `reload` argument is passed to relevant functions.
    """

    def __init__(
        self,
        path: os.PathLike | str,
        *,
        create_nonexisting: bool = False,
        reload: bool = True,
    ):
        """Initialize a Capsule object.

        Args:
        ----
            path: Path to the capsule file
            create_nonexisting: Whether to create the file if it doesn't exist

        Returns:
        -------
            self: The initialized Capsule object

        Processing Logic:
        ----------------
            - Check if the path points to a valid capsule file
            - If create_nonexisting is True and file doesn't exist:
                - Create RIM file if rim extension
                - Create ERF file if erf/mod extension
            - Initialize self._path and self._resources attributes
            - Reload resources from file.
        """
        self._resources: list[FileResource] = []
        super().__init__(path, create_nonexisting=create_nonexisting)
        if reload:
            self.reload()

    def resources(
        self,
        *,
        reload: bool = False,
    ) -> list[FileResource]:
        if reload:
            self.reload()
        return self._resources

    def resource(
        self,
        resref: str,
        restype: ResourceType,
        *,
        reload: bool = False,
    ) -> bytes | None:
        """Returns the bytes data of the specified resource. If the resource does not exist then returns None instead.

        Args:
        ----
            resref: The resource ResRef.
            restype: The resource type.
            reload: If True Capsule will reload the ERF before opening rather than using cached offsets.

        Returns:
        -------
            bytes data of the resource.
        """
        if reload:
            self.reload()
        return super().resource(resref, restype)

    def batch(
        self,
        queries: list[ResourceIdentifier],
        *,
        reload: bool = False,
    ) -> dict[ResourceIdentifier, ResourceResult | None]:
        """Batches queries against a capsule.

        Args:
        ----
            queries: list[ResourceIdentifier]: The queries to batch
            reload: bool = False: Whether to reload the capsule resources

        Returns:
        -------
            dict[ResourceIdentifier, ResourceResult | None]: The results for each query keyed by query

        Processing Logic:
        ----------------
            - Reloads capsule resources from erf/rim if reload is True
            - Initializes results dict to return
            - Opens capsule file as binary reader
            - Loops through queries
                - Sets result to None
                - Checks if resource exists in capsule
                - If so, seeks to offset, reads bytes and sets result
            - Closes reader
            - Returns results dict.
        """
        if reload:
            self.reload()
        return super().batch(queries)

    def contains(
        self,
        resref: str,
        restype: ResourceType,
        *,
        reload: bool = False,
    ) -> bool:
        """Check if a resource exists.

        Args:
        ----
            resref: str: Resource reference
            restype: ResourceType: Resource type
            reload: bool: Reload resources cache

        Returns:
        -------
            bool: True if resource exists, False otherwise

        Checks if a resource exists:
            - Constructs a ResourceIdentifier from resref and restype
            - Searches self._resources for a matching resource
            - Returns True if a match is found, False otherwise.
        """
        if reload:
            self.reload()
        return super().contains(resref, restype)

    def info(
        self,
        resref: str,
        restype: ResourceType,
        *,
        reload: bool = False,
    ) -> FileResource | None:
        """Get file resource by reference and type.

        Args:
        ----
            resref: Resource reference as string
            restype: Resource type
            reload: Reload resources if True (kwarg)

        Returns:
        -------
            FileResource: Matched file resource

        Processing Logic:
        ----------------
            - Check if reload is True and call reload()
            - Create query object from resref and restype
            - Return first matching resource from internal list.
        """
        if reload:
            self.reload()
        return super().info(resref, restype)

    def reload(
        self,
    ):
        """Reload the list of resource info linked from the module file.

        Args:
        ----
            self: Capsule object to reload

        Returns:
        -------
            None: Reloading is done in-place

        Processing Logic:
        ----------------
            - Check if capsule exists on disk and print error if not
            - Open file and read header
            - Call appropriate reload method based on file type
            - Raise error if unknown file type.
        """
        self._internal = True
        self._resources = super().resources()
        self._internal = False

    def delete(
        self,
        resname: str,
        restype: ResourceType,
    ):
        result = super().delete(resname, restype)
        self.reload()
        return result

    def add(
        self,
        resname: str,
        restype: ResourceType,
        resdata: bytes,
    ):
        """Adds a resource to the capsule and writes the updated capsule to the disk.

        Args:
        ----
            resname: Name of the resource to add in one line.
            restype: Type of the resource to add in one line.
            resdata: Data of the resource to add in one line.

        Returns:
        -------
            None: No value is returned in one line.

        Processing Logic:
        ----------------
            - Checks if the file is RIM or a type of ERF
            - Reads the file as appropriate container
            - Calls set_data to add the resource
            - Writes the container back to the file.
        """
        result = super().add(resname, restype, resdata)
        self.reload()
        return result

    @classmethod
    def from_data(cls, data: bytes, resname: str, restype: ResourceType) -> Self:
        """Initialize a Capsule object from raw data bytes.

        Args:
        ----
            data: The raw bytes of the capsule file.
            resname: The resource name for identification.
            restype: The resource type.

        Returns:
        -------
            Capsule: The initialized Capsule object.
        """
        with BinaryReader.from_bytes(data) as reader:
            capsule = cast(cls, object())
            capsule.__class__ = cls
            file_type = reader.read_string(4)
            reader.skip(4)
            if file_type in (member.value for member in ERFType):
                capsule._resources = capsule._load_erf(reader)  # noqa: SLF001
            elif file_type == "RIM ":
                capsule._resources = capsule._load_rim(reader)  # noqa: SLF001
            else:
                msg = f"Data provided is not a valid ERF/MOD/SAV/RIM format, found '{file_type}'."
                raise ValueError(msg)
            return capsule
