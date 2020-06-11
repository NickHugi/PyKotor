from __future__ import annotations

import io
import os
from typing import List, Optional, Union, Dict

from pykotor.manager.chitin import Chitin
from pykotor.manager.encapsulator import Encapsulator
from pykotor.types import resource_types, ResourceType


class ResourceManager:
    @staticmethod
    def new(directory: str) -> ResourceManager:
        rm = ResourceManager()
        rm.directory = directory.replace('\\', '/')
        rm.chitin = Chitin.new(directory)
        rm.refresh_modules()
        return rm

    def __init__(self):
        self.directory: str = ""
        self.chitin: Optional[Chitin] = None
        self.modules: List[str] = []
        self.texture_packs: List[str] = []

    def modules_directory(self) -> str:
        return self.directory + "/modules/"

    def lips_directory(self) -> str:
        return self.directory + "/lips/"

    def override_directory(self) -> str:
        return self.directory + "/override/"

    def refresh_modules(self) -> None:
        modules_path = self.directory + '/modules/'
        files = os.listdir(modules_path)
        for file in files.copy():
            if not os.path.isfile(modules_path + file):
                files.remove(file)
            elif not file.endswith('rim') and not file.endswith('erf') and not file.endswith('mod'):
                files.remove(file)
        self.modules = files

    def get_resource(self, res_ref: str, res_type: Union[ResourceType, str, int],
                     check_folders: List[str] = None,
                     check_modules: List[str] = None,
                     skip_override: bool = False) -> Optional[bytes]:
        res_type = ResourceType.get(res_type)

        data = None

        if check_folders is not None:
            for folder in check_folders:
                try:
                    with open(folder + "\\" + res_ref + "." + res_type.extension, 'rb') as file:
                        data = file.read()
                except:
                    pass

        if os.path.exists(self.override_directory() + res_ref + "." + res_type.extension) and not skip_override:
            with open(self.override_directory() + res_ref + "." + res_type.extension, 'rb') as file:
                data = file.read()

        if check_modules is not None:
            for module_path in check_modules:
                cap = Encapsulator.new(module_path)
                if cap.has_resource(res_ref, res_type):
                    data = cap.load(res_ref, res_type)

        if self.chitin.has_resource(res_ref, res_type):
            data = self.chitin.load(res_ref, res_type)

        return data


class RequestManager:
    @staticmethod
    def new(res_manager: Optional[ResourceManager] = None,
            chitin_directory: str = "",
            check_folders: Optional[List[str]] = None,
            check_modules: Optional[List[str]] = None):
        req_manager = RequestManager()

        if res_manager is not None:
            # req_manager._chitin = res_manager.chitin
            pass

        if chitin_directory is not None:
            try:
                req_manager._chitin = Chitin.new(chitin_directory)
            finally:
                pass

        if check_folders is None:
            check_folders = []
        req_manager.check_folders = check_folders

        if check_modules is None:
            check_modules = []
        req_manager.check_modules = check_modules

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
        # flags which affect searches
        self.skip_override = False
        self.check_folders = []
        self.check_modules = []

    def new_request(self, res_ref: str, res_type: Union[ResourceType, str, int], path: Optional[str]) -> None:
        request = ResourceRequest.new(res_ref, res_type, path)
        self._buffer.append(request)

    def get_data(self, request: ResourceRequest) -> Optional[bytes]:
        data = None
        handle = None

        if request.path is None:
            return None

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

    def _open_handle(self, path):
        self._encapsulators[path] = Encapsulator.new(path)

    def _handle_searches(self) -> None:
        for request in self._buffer:
            if request.path is None:
                request.path = self._handle_search(request)

    def _handle_search(self, request: ResourceRequest) -> Optional[str]:
        path = None
        file_name = request.res_ref + "." + ResourceType.get(request.res_type).extension

        for folder_path in self.check_folders:
            if path is None and os.path.exists(folder_path + file_name):
                path = folder_path + file_name

        if path is None and self._resource_manager is not None:
            if os.path.exists(self._resource_manager.override_directory() + file_name):
                path = self._resource_manager.override_directory() + file_name

        for module_path in self.check_modules:
            if path is None and os.path.exists(module_path):
                try:
                    self._open_handle(module_path)
                    if self._encapsulators[module_path].has_resource(request.res_ref, request.res_type):
                        path = module_path
                except:
                    pass

        if path is None and self._chitin is not None:
            path = self._chitin.resource_path(request.res_ref, request.res_type)

        return path

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
        self._handle_searches()
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

