from __future__ import annotations

import io
from typing import List, Optional, Union, Dict

from pykotor.manager.chitin import Chitin
from pykotor.manager.encapsulator import Encapsulator
from pykotor.types import resource_types, ResourceType


class ResourceManager:
    def __init__(self):
        pass


class RequestManager:
    @staticmethod
    def new(res_manager: Optional[ResourceManager] = None,
            chitin_directory: str = ""):
        req_manager = RequestManager()

        if res_manager is not None:
            # req_manager._chitin = res_manager.chitin
            pass

        if chitin_directory is not None:
            try:
                req_manager._chitin = Chitin.new(chitin_directory)
            finally:
                pass

        return req_manager

    def __init__(self, chitin_path=None):
        self._resource_manager: Optional[ResourceManager] = None
        self._buffer: List[ResourceRequest] = []
        self._encapsulators: Dict[str, Encapsulator] = {}
        self._chitin: Optional[Chitin] = None
        # flags which affect write() behaviour
        self.decompile_tpcs = False
        self.decompile_mdls = False
        self.decompile_2das = False
        self.decompile_gffs = False
        self.extract_mdl_textures = False
        self.extract_tpc_txis = False

    def new_request(self, res_ref: str, res_type: Union[ResourceType, str, int], path: str) -> None:
        request = ResourceRequest.new(res_ref, res_type, path)
        self._buffer.append(request)

    def get_data(self, request: ResourceRequest) -> Optional[bytes]:
        data = None
        handle = None

        try:
            if request.encapsulated():
                if request.path not in self._encapsulators:
                    self._encapsulators[request.path] = Encapsulator.new(request.path)
                data = self._encapsulators[request.path].load(request.res_ref, request.res_type)
            elif request.keyed():
                if self._chitin is not None:
                    data = self._chitin.load(request.res_ref, request.res_type)
            else:
                handle = open(request.path, 'rb')
                data = handle.read()
        finally:
            if handle is not None and not request.encapsulated():
                handle.close()

        return data

    def close_handles(self) -> None:
        for cap in self._encapsulators.values():
            cap.close_handle()
        if self._chitin is not None:
            self._chitin.close_handles()

    def write(self, directory: str) -> None:
        while len(self._buffer) > 0:
            request = self._buffer.pop(0)
            data = self.get_data(request)

            '''
            try:
                if res_type == 'tpc':
                    data = TPC.load(data).build(tga)
            finally:
                pass
            '''

            with open(directory + '/' + request.file_name()) as file:
                file.write(data)

    def load(self) -> List[ResourceRequest]:
        """ Using this on too many files may result in a memory error. """
        for request in self._buffer:
            request.data = self.get_data(request)
        return self._buffer


class ResourceRequest:
    @staticmethod
    def new(res_ref: str, res_type: ResourceType, path: str) -> ResourceRequest:
        request = ResourceRequest()
        request.res_ref = res_ref
        request.res_type = res_type
        request.path = path
        return request

    def __init__(self):
        self.res_ref: str = ""
        self.res_type: ResourceType = resource_types[0]
        self.path: str = ""
        self.data: Optional[bytes] = None

    def successful(self) -> bool:
        return self.data is not None

    def keyed(self) -> bool:
        return self.path.endswith(".bif")

    def encapsulated(self) -> bool:
        return self.path.endswith(".rim") or self.path.endswith(".erf") or self.path.endswith(".mod")

    def file_name(self) -> str:
        return self.res_ref + "." + self.res_type.extension

