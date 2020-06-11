from __future__ import annotations

import io
from typing import Union, Optional, List, Dict, BinaryIO

from pykotor.general.binary_reader import BinaryReader
from pykotor.types import ResourceType


class Chitin:
    @staticmethod
    def new(path: str) -> Chitin:
        chitin = Chitin()
        chitin._resources = _KEYReader.load_resources(path)
        return chitin

    def __init__(self):
        self._resources: Dict[int, Resource] = {}
        self._handles: Dict[str, BinaryIO] = {}

    def load(self, res_ref: str, res_type: Union[ResourceType, str, int]) -> Optional[bytes]:
        resource = self._get_resource(res_ref, res_type)
        if resource is None:
            return None

        handle = self._open_handle(resource.path)
        handle.seek(resource.res_offset)
        data = handle.read(resource.res_size)

        return data

    def secure_load(self, res_ref: str, res_type: Union[ResourceType, str, int]) -> Optional[bytes]:
        resource = self._get_resource(res_ref, res_type)
        if resource is None:
            return None

        handle = open(resource.path, 'rb')
        handle.seek(resource.res_offset)
        data = handle.read(resource.res_size)
        handle.close()

        return data

    def has_resource(self, res_ref: str, res_type: Union[ResourceType, str, int]) -> bool:
        if self._get_resource(res_ref, res_type) is not None:
            return True
        return False

    def resource_path(self, res_ref: str, res_type: Union[ResourceType, str, int]) -> Optional[str]:
        resource = self._get_resource(res_ref, res_type)
        if resource is not None:
            return resource.path
        return None

    def close_handles(self) -> None:
        for handle in self._handles.values():
            handle.close()
        self._handles.clear()

    def _open_handle(self, path: str) -> BinaryIO:
        if path not in self._handles:
            self._handles[path] = open(path, 'rb')
        return self._handles[path]

    def _get_resource(self, res_ref: str, res_type: Union[ResourceType, str, int]) -> Optional[Resource]:
        for resource in self._resources.values():
            if resource.res_ref == res_ref and resource.res_type == res_type:
                return resource


class Resource:
    def __init__(self, res_ref, res_type):
        self.res_ref = res_ref
        self.res_type = res_type
        self.res_offset = -1
        self.res_size = -1
        self.path = None

    def loaded(self):
        return self.res_offset != -1 and self.res_size != -1 and self.path is not None


class _KEYReader:
    @staticmethod
    def load_resources(directory: str) -> Dict[int, Resource]:
        reader = BinaryReader.from_path(directory + "/chitin.key")
        resources:Dict[int, Resource] = dict()

        file_type = reader.read_string(4)
        file_version = reader.read_string(4)

        bif_count = reader.read_uint32()
        key_count = reader.read_uint32()

        bif_names_offset = reader.read_uint32()
        keys_offset = reader.read_uint32()

        bif_paths = []
        for i in range(bif_count):
            reader.seek(bif_names_offset + i * 12)
            bif_size = reader.read_uint32()
            filename_offset = reader.read_uint32()
            filename_size = reader.read_uint16()
            drive = reader.read_uint16()

            reader.seek(filename_offset)
            bif_path = (directory + '/' + reader.read_string(filename_size)).replace('\\', '/')
            bif_paths.append(bif_path)

        reader.seek(keys_offset)
        for i in range(key_count):
            res_ref = reader.read_string(16)
            res_type = ResourceType.get(reader.read_uint16())
            res_id = reader.read_uint32()
            resources[res_id] = Resource(res_ref, res_type)

        for bif in bif_paths:
            try:
                _BIFReader.load_resources(bif, resources)
            finally:
                pass

        return resources


class _BIFReader:
    @staticmethod
    def load_resources(path: str, resources: Dict[int, Resource]) -> None:
        reader = BinaryReader.from_path(path)

        file_type = reader.read_string(4)
        file_version = reader.read_string(4)

        resource_count = reader.read_uint32()
        reader.skip(4)
        resources_offset = reader.read_uint32()

        reader.seek(resources_offset)
        for i in range(resource_count):
            res_id = reader.read_uint32()
            resources[res_id].res_offset = reader.read_uint32()
            resources[res_id].res_size = reader.read_uint32()
            resources[res_id].path = path
            res_type_id = reader.read_uint32()
