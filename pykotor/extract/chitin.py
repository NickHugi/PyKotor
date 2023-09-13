from __future__ import annotations

from pykotor.common.stream import BinaryReader
from pykotor.extract.file import FileResource, ResourceIdentifier
from pykotor.resource.type import ResourceType
from pykotor.tools.path import CaseAwarePath


class Chitin:
    """
    Chitin object is used for loading the list of resources stored in the chitin.key/.bif files used by the game.
    Resource data is not actually stored in memory by default but is instead loaded up on demand with the
    Chitin.resource() method.

    Chitin support is read-only and you cannot write your own key/bif files with this class.
    """

    def __init__(
        self,
        kotor_path: CaseAwarePath,
    ):
        self._kotor_path = CaseAwarePath(kotor_path)

        self._resources: list[FileResource] = []
        self.load()

    def __iter__(
        self,
    ):
        yield from self._resources

    def __len__(
        self,
    ):
        return len(self._resources)

    def load(
        self,
    ) -> None:
        """Reload the list of resource info linked from the chitin.key file."""
        self._resources = []

        with BinaryReader.from_file(self._kotor_path / "chitin.key") as reader:
            reader.read_string(4)
            reader.read_string(4)
            bif_count = reader.read_uint32()
            key_count = reader.read_uint32()
            file_table_offset = reader.read_uint32()
            reader.read_uint32()

            files = []
            reader.seek(file_table_offset)
            for _ in range(bif_count):
                reader.skip(4)
                file_offset = reader.read_uint32()
                file_length = reader.read_uint16()
                reader.skip(2)
                files.append((file_offset, file_length))

            bifs = []
            for file_offset, file_length in files:
                reader.seek(file_offset)
                bif = reader.read_string(file_length)
                bifs.append(bif)

            keys = {}
            for _ in range(key_count):
                resref = reader.read_string(16)
                reader.read_uint16()
                res_id = reader.read_uint32()
                keys[res_id] = resref

        for bif in bifs:
            with BinaryReader.from_file(self._kotor_path / bif) as reader:
                reader.read_string(4)
                reader.read_string(4)
                resource_count = reader.read_uint32()
                reader.skip(4)
                resource_offset = reader.read_uint32()

                reader.seek(resource_offset)
                for _ in range(resource_count):
                    res_id = reader.read_uint32()
                    offset = reader.read_uint32()
                    size = reader.read_uint32()
                    restype = ResourceType.from_id(reader.read_uint32())
                    resref = keys[res_id]
                    resource = FileResource(
                        resref,
                        restype,
                        size,
                        offset,
                        self._kotor_path / bif,
                    )
                    self._resources.append(resource)

    def resource(
        self,
        resref: str,
        restype: ResourceType,
    ) -> bytes | None:
        """
        Returns the bytes data of the specified resource. If the resource does not exist then returns None instead.

        Args:
        ----
            resref: The resource ResRef.
            restype: The resource type.

        Returns:
        -------
            None or bytes data of resource.
        """
        query = ResourceIdentifier(resref, restype)
        resource = next(
            (resource for resource in self._resources if resource == query),
            None,
        )
        return None if resource is None else resource.data()

    def exists(
        self,
        resref: str,
        restype: ResourceType,
    ) -> bool:
        query = ResourceIdentifier(resref, restype)
        resource = next(
            (resource for resource in self._resources if resource == query),
            None,
        )
        return resource is not None
