from typing import List, Optional

from pykotor.common.stream import BinaryReader
from pykotor.extract.file import FileResource, FileQuery
from pykotor.resource.type import ResourceType


class Capsule:
    """
    Chitin object is used for loading the list of resources stored in the .erf/.rim/.mod files used by the game.
    Resource data is not actually stored in memory by default but is instead loaded up on demand with the
    Capsule.resource() method.

    Capsule data is read-only, use ERF or RIM classes instead for creating and editing files.
    """
    def __init__(self, path: str):
        self._path: str = path
        self._resources: List[FileResource] = []

        self.reload()

    def __iter__(self):
        for resource in self._resources:
            yield resource

    def __len__(self):
        return len(self._resources)

    def resource(self, resref: str, restype: ResourceType, reload: bool = False) -> Optional[bytes]:
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

        query = FileQuery(resref, restype)
        resource = next((resource for resource in self._resources if resource == query), None)
        return None if resource is None else resource.data()

    def exists(self, resref: str, restype: ResourceType) -> bool:
        query = FileQuery(resref, restype)
        resource = next((resource for resource in self._resources if resource == query), None)
        return resource is not None

    def reload(self):
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

    def _load_erf(self, reader: BinaryReader):
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

    def _load_rim(self, reader: BinaryReader):
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

