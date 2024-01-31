from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator

from pykotor.common.stream import BinaryReader
from pykotor.extract.file import FileResource, ResourceIdentifier, ResourceResult
from pykotor.resource.formats.erf import ERF, ERFType, read_erf, write_erf
from pykotor.resource.formats.rim import RIM, read_rim, write_rim
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_any_erf_type_file, is_capsule_file, is_rim_file
from utility.system.path import Path

if TYPE_CHECKING:
    import os


class Capsule:
    """Capsule object is used for loading the list of resources stored in the .erf/.rim/.mod/.sav files used by the game.

    Resource data is not actually stored in memory by default but is instead loaded up on demand with the
    Capsule.resource() method. Use the RIM or ERF classes if you want to solely work with capsules in memory.
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
        self._path: Path = Path.pathify(path)  # type: ignore[assignment]
        self._resources: list[FileResource] = []

        if not is_capsule_file(self._path):
            msg = f"Invalid file extension in capsule filepath '{self._path}'."
            raise ValueError(msg)

        if create_nonexisting and not self._path.safe_isfile():  # type: ignore[reportGeneralTypeIssues]
            if is_rim_file(self._path):
                write_rim(RIM(), self._path)
            elif is_any_erf_type_file(self._path):
                write_erf(ERF(ERFType.from_extension(self._path.suffix)), self._path)

        self.reload()

    def __iter__(
        self,
    ) -> Generator[FileResource, Any, None]:
        yield from self._resources

    def __len__(
        self,
    ):
        return len(self._resources)

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

        query = ResourceIdentifier(resref, restype)
        resource: FileResource | None = next(
            (resource for resource in self._resources if resource == query),
            None,
        )
        return resource.data() if resource else None

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

        results: dict[ResourceIdentifier, ResourceResult | None] = {}
        with BinaryReader.from_file(self._path) as reader:
            for query in queries:
                results[query] = None

                resource: FileResource | None = next(
                    (resource for resource in self._resources if resource == query),
                    None,
                )
                if resource is None:
                    continue

                reader.seek(resource.offset())
                data: bytes = reader.read_bytes(resource.size())
                results[query] = ResourceResult(
                    query.resname,
                    query.restype,
                    self._path,
                    data,
                )
        return results

    def exists(
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

        query = ResourceIdentifier(resref, restype)
        resource: FileResource | None = next(
            (resource for resource in self._resources if resource == query),
            None,
        )
        return resource is not None

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

        query = ResourceIdentifier(resref, restype)
        return next((resource for resource in self._resources if resource == query), None)

    def reload(
        self,
    ):
        # nothing to reload if capsule doesn't exist on disk (from_file will error if not existing)
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
        with BinaryReader.from_file(self._path) as reader:
            file_type = reader.read_string(4)
            reader.skip(4)  # file version

            if file_type in {ERFType.__members__[erf_name].value for erf_name in ERFType.__members__}:
                return self._load_erf(reader)
            if file_type == "RIM ":
                return self._load_rim(reader)

            msg = f"File '{self._path}' must be a ERF/MOD/SAV/RIM capsule."
            raise NotImplementedError(msg)

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
        container: RIM | ERF
        if is_rim_file(self._path.name):
            container = read_rim(self._path)
            container.set_data(resname, restype, resdata)
            write_rim(container, self._path)
        elif is_any_erf_type_file(self._path.name):
            container = read_erf(self._path)
            container.set_data(resname, restype, resdata)
            write_erf(container, self._path)
        else:
            msg = f"File '{self._path}' is not a ERF/MOD/SAV/RIM capsule."
            raise NotImplementedError(msg)

    def path(
        self,
    ) -> Path:
        return self._path

    def filename(
        self,
    ) -> str:
        return self._path.name

    def _load_erf(
        self,
        reader: BinaryReader,
    ):
        """Loads an ERF resource file.

        Args:
        ----
            reader: BinaryReader - Reader for the ERF file

        Processing Logic:
        ----------------
            - Skips header data
            - Reads entry count and offset tables
            - Loops through keys to read resource references, IDs and types
            - Seeks to resource data offset table
            - Loops to read offsets and sizes and populate resource objects.
        """
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
            resrefs.append(reader.read_string(16))
            resids.append(reader.read_uint32())
            restypes.append(ResourceType.from_id(reader.read_uint16()))
            reader.skip(2)

        reader.seek(offset_to_resources)
        for i in range(entry_count):
            res_offset: int = reader.read_uint32()
            res_size:   int = reader.read_uint32()
            self._resources.append(FileResource(resrefs[i], restypes[i], res_size, res_offset, self._path))

    def _load_rim(
        self,
        reader: BinaryReader,
    ):
        """Load resources from a rim file.

        Args:
        ----
            reader: BinaryReader: The binary reader to read data from

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
                - Append a FileResource to the internal resources list.
        """
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
            self._resources.append(FileResource(resref, restype, size, offset, self._path))
