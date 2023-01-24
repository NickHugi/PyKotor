import ntpath
import os.path
from typing import List, Optional, Dict

from pykotor.common.stream import BinaryReader
from pykotor.extract.file import FileResource, ResourceResult, ResourceIdentifier
from pykotor.resource.formats.erf import ERF, read_erf, write_erf, ERFType
from pykotor.resource.formats.rim import read_rim, write_rim, RIM
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_rim_file, is_erf_file, is_capsule_file


class Capsule:
    """
    Chitin object is used for loading the list of resources stored in the .erf/.rim/.mod files used by the game.
    Resource data is not actually stored in memory by default but is instead loaded up on demand with the
    Capsule.resource() method.
    """
    def __init__(
            self,
            path: str,
            create_nonexisting: bool = False
    ):
        self._path: str = path
        self._resources: List[FileResource] = []

        if not is_capsule_file(path):
            raise ValueError(f"Invalid file extension in capsule filepath '{path}'.")

        if create_nonexisting and not os.path.exists(path):
            if is_rim_file(path):
                write_rim(RIM(), path)
            elif is_erf_file(path):
                write_erf(ERF(ERFType.from_extension(path)), path)

        self.reload()

    def __iter__(
            self
    ):
        for resource in self._resources:
            yield resource

    def __len__(
            self
    ):
        return len(self._resources)

    def resource(
            self,
            resref: str,
            restype: ResourceType,
            reload: bool = False
    ) -> Optional[bytes]:
        """
        Returns the bytes data of the specified resource. If the resource does not exist then returns None instead.

        Args:
            resref: The resource ResRef.
            restype: The resource type.
            reload: If True Capsule will reload the ERF before opening rather than using cached offsets.

        Returns:
            None or bytes data of resource.
        """
        if reload:
            self.reload()

        query = ResourceIdentifier(resref, restype)
        resource = next((resource for resource in self._resources if resource == query), None)
        return None if resource is None else resource.data()

    def batch(
            self,
            queries: List[ResourceIdentifier],
            reload: bool = False
    ) -> Dict[ResourceIdentifier, Optional[ResourceResult]]:
        if reload:
            self.reload()

        results = {}
        reader = BinaryReader.from_file(self.path())

        for query in queries:
            results[query] = None
            if self.exists(query.resname, query.restype):
                resource = next((resource for resource in self._resources if resource == query), None)
                if resource is not None:
                    reader.seek(resource.offset())
                    data = reader.read_bytes(resource.size())
                    results[query] = ResourceResult(query.resname, query.restype, self.path(), data)

        reader.close()
        return results

    def exists(
            self,
            resref: str,
            restype: ResourceType,
            reload: bool = False
    ) -> bool:
        if reload:
            self.reload()

        query = ResourceIdentifier(resref, restype)
        resource = next((resource for resource in self._resources if resource == query), None)
        return resource is not None

    def info(
            self,
            resref: str,
            restype: ResourceType,
            reload: bool = False
    ) -> FileResource:
        if reload:
            self.reload()

        query = ResourceIdentifier(resref, restype)
        resource = next((resource for resource in self._resources if resource == query), None)
        return resource

    def reload(
            self
    ):
        """
        Reload the list of resource info linked from the module file.
        """
        with BinaryReader.from_file(self._path) as reader:
            file_type = reader.read_string(4)
            file_version = reader.read_string(4)

            if file_type in ("ERF ", "MOD "):
                self._load_erf(reader)
            elif file_type == "RIM ":
                self._load_rim(reader)
            else:
                raise ValueError("File '{}' was not an ERF/MOD/RIM.".format(self._path))

    def add(
            self,
            resname: str,
            restype: ResourceType,
            resdata: bytes
    ):
        container = read_rim(self._path) if self._path.endswith(".rim") else read_erf(self._path)
        container.set(resname, restype, resdata)
        write_rim(container, self._path) if self._path.endswith(".rim") else write_erf(container, self._path)

    def path(
            self
    ) -> str:
        return os.path.normpath(self._path)

    def filename(
            self
    ) -> str:
        return ntpath.basename(self._path)

    def _load_erf(
            self,
            reader: BinaryReader
    ):
        reader.skip(8)
        entry_count = reader.read_uint32()
        reader.skip(4)
        offset_to_keys = reader.read_uint32()
        offset_to_resources = reader.read_uint32()

        resrefs = []
        resids = []
        restypes = []
        reader.seek(offset_to_keys)
        for i in range(entry_count):
            resrefs.append(reader.read_string(16))
            resids.append(reader.read_uint32())
            restypes.append(ResourceType.from_id(reader.read_uint16()))
            reader.skip(2)

        reader.seek(offset_to_resources)
        for i in range(entry_count):
            res_offset = reader.read_uint32()
            res_size = reader.read_uint32()
            self._resources.append(FileResource(resrefs[i], restypes[i], res_size, res_offset, self._path))

    def _load_rim(
            self,
            reader: BinaryReader
    ):
        reader.skip(4)
        entry_count = reader.read_uint32()
        offset_to_entries = reader.read_uint32()

        reader.seek(offset_to_entries)
        for i in range(entry_count):
            resref = reader.read_string(16)
            restype = ResourceType.from_id(reader.read_uint32())
            res_id = reader.read_uint32()
            offset = reader.read_uint32()
            size = reader.read_uint32()
            self._resources.append(FileResource(resref, restype, size, offset, self._path))

