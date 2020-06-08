from __future__ import annotations

import io
from typing import Union, List, BinaryIO, overload

from pykotor.general.binary_reader import BinaryReader
from pykotor.types import ResourceType, resource_types
import pykotor.formats.erf


class RIM:
    @staticmethod
    def load(data: bytes) -> RIM:
        return _RIMReader.load(data)

    def build(self) -> bytes:
        return _RIMWriter.build(self)

    def to_erf(self) -> pykotor.formats.erf.ERF:
        pass

    def __init__(self):
        self.resources: List[Resource] = []

    def add(self, resource: Resource) -> None:
        self.resources.append(resource)

    def remove(self, index: int) -> Resource:
        resource = self.resources[index]
        del self.resources[index]
        return resource

    def get(self, index: int) -> Resource:
        return self.resources[index]

    def all(self) -> List[Resource]:
        return self.resources


class Resource:
    @staticmethod
    def new(res_ref: str, res_type: Union[str, int, ResourceType], res_data: bytearray) -> Resource:
        resource = Resource()
        resource.res_ref = res_ref
        resource.res_type = ResourceType.get(res_type)
        resource.res_data = res_data
        return resource

    def __init__(self):
        self.res_ref: str = ""
        self.res_type: ResourceType = resource_types[0]
        self.res_data: bytearray = bytearray()


class _RIMReader:
    @staticmethod
    def load(data: bytes) -> RIM:
        reader = BinaryReader.from_data(data)
        rim = RIM()

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
            res_data = reader.read_bytes(res_size)
            rim.add(Resource.new(res_ref, res_type, res_data))

        return rim


class _RIMWriter:
    @staticmethod
    def build(rim: RIM) -> bytes:
        pass
        # TODO
