from __future__ import annotations

import io
from typing import Union, List, BinaryIO

from pykotor.formats.erf import ERF
from pykotor.general.binary_reader import BinaryReader
from pykotor.types import ResourceType, resource_types


class RIM:
    @staticmethod
    def load(data: bytes) -> RIM:
        return _RIMReader.load(data)

    def build(self) -> bytes:
        return _RIMWriter.build(self)

    def to_erf(self) -> ERF:
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
        pass
        # TODO


class _RIMWriter:
    @staticmethod
    def build(rim: RIM) -> bytes:
        pass
        # TODO
