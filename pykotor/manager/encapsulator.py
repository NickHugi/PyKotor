from __future__ import annotations
import io
from typing import Optional, List, Union

from pykotor.general.binary_reader import BinaryReader
from pykotor.types import ResourceType


class Encapsulator:
    @staticmethod
    def new(path: str) -> Encapsulator:
        cap = Encapsulator()
        cap._path = path

        if path.endswith(".rim"):
            cap._resources = _RIMReader.load_resources(path)
        elif path.endswith(".mod") or path.endswith(".erf"):
            cap._resources = _ERFReader.load_resources(path)
        else:
            raise Exception("Invalid file format loaded.")

        return cap

    def __init__(self):
        self._path: str = ""
        self._resources: List[Resource] = []
        self._handle: Optional[io.BytesIO] = None

    def _open_handle(self) -> None:
        self._handle = open(self._path, 'rb')

    def _get_resource(self, res_ref: str, res_type: Union[ResourceType, str, int]) -> Optional[Resource]:
        for resource in self._resources:
            if resource.res_ref == res_ref and resource.res_type == res_type:
                return resource

    def has_resource(self, res_ref: str, res_type: Union[ResourceType, str, int]) -> bool:
        if self._get_resource(res_ref, res_type) is not None:
            return True
        return False

    def close_handle(self) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None

    def load(self, res_ref: str, res_type: Union[ResourceType, str, int]) -> Optional[bytes]:
        resource = self._get_resource(res_ref, res_type)
        if resource is None:
            return None

        if self._handle is None:
            self._open_handle()

        self._handle.seek(resource.res_offset)
        data = self._handle.read(resource.res_size)

        return data

    def secure_load(self, res_ref: str, res_type: Union[ResourceType, str, int]) -> Optional[bytes]:
        data = None

        try:
            data = self.load(res_ref, res_type)
        finally:
            self.close_handle()

        return data

    def get_resources(self) -> List[Resource]:
        return self._resources.copy()


class Resource:
    def __init__(self, res_ref, res_type, res_size, res_offset):
        self.res_ref = res_ref
        self.res_type = res_type
        self.res_size = res_size
        self.res_offset = res_offset


class _ERFReader:
    @staticmethod
    def load_resources(path: str) -> List[Resource]:
        reader = BinaryReader.from_path(path)
        resources = []

        file_type = reader.read_string(4)
        file_version = reader.read_string(4)
        reader.seek(16)
        resource_count = reader.read_uint32()
        reader.seek(24)
        key_list_offset = reader.read_uint32()
        resource_list_offset = reader.read_uint32()

        for i in range(resource_count):
            reader.seek(key_list_offset + 24 * i)
            res_ref = reader.read_string(16)
            reader.skip(4)
            res_type = ResourceType.get(reader.read_uint16())
            reader.skip(2)

            reader.seek(resource_list_offset + 8 * i)
            res_offset = reader.read_uint32()
            res_size = reader.read_uint32()

            resources.append(Resource(res_ref, res_type, res_size, res_offset))

        return resources


class _RIMReader:
    @staticmethod
    def load_resources(path: str) -> List[Resource]:
        reader = BinaryReader.from_path(path)
        resources = []

        file_type = reader.read_string(4)
        file_version = reader.read_string(4)
        reader.skip(4)
        resource_count = reader.read_uint32()
        table_offset = reader.read_uint32()
        reader.skip(100)

        for i in range(resource_count):
            reader.seek(table_offset + 32 * i)
            res_ref = reader.read_string(16)
            res_type = ResourceType.get(reader.read_uint32())
            reader.skip(4)
            res_offset = reader.read_uint32()
            res_size = reader.read_uint32()
            reader.seek(res_offset)

            resources.append(Resource(res_ref, res_type, res_size, res_offset))

        return resources
