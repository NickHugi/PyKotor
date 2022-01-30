from __future__ import annotations

import os
from contextlib import suppress
from enum import Enum
from typing import Dict, List, Optional, Tuple

from pykotor.extract.file import FileResource, FileQuery
from pykotor.extract.capsule import Capsule
from pykotor.extract.chitin import Chitin
from pykotor.extract.talktable import TalkTable
from pykotor.resource.formats.mdl import MDL
from pykotor.resource.formats.tlk import TLK
from pykotor.resource.formats.tpc import TPC, load_tpc
from pykotor.resource.type import ResourceType


class TextureQuality(Enum):
    HIGH = "a"
    MODERATE = "b"
    LOW = "c"


class Installation:
    """
    Installation provides a centralized location for loading resources stored in the game through its
    various folders and formats.
    """
    TEXTURES_TYPES = [ResourceType.TPC, ResourceType.TGA, ResourceType.DDS]

    def __init__(self, path: str, name: str):
        self._path: str = path.replace('\\', '/')
        if not self._path.endswith('/'): self._path += '/'

        self.name = name

        self._chitin: List[FileResource] = []
        self._modules: Dict[str, List[FileResource]] = {}
        self._lips: Dict[str, List[FileResource]] = {}
        self._texturepacks: Dict[str, List[FileResource]] = {}
        self._override: Dict[str, Dict[str, FileResource]] = {}
        self._talktable: Optional[TalkTable] = None

        self.load_modules()
        self.load_override()
        self.load_lips()
        self.load_textures()
        self.load_chitin()
        self._talktable = TalkTable(self._path + "dialog.tlk")

    # region Get Paths
    def path(self) -> str:
        return self._path

    def module_path(self) -> str:
        module_path = self._path
        for folder in os.listdir(self._path):
            if os.path.isdir(module_path + folder) and folder.lower() == "modules":
                module_path += folder + "/"
        if module_path == self._path:
            raise ValueError("Could not find modules folder in '{}'.".format(self._path))
        return module_path

    def override_path(self) -> str:
        override_path = self._path
        for folder in os.listdir(self._path):
            if os.path.isdir(override_path + folder) and folder.lower() == "override":
                override_path += folder + "/"
        if override_path == self._path:
            raise ValueError("Could not find override folder in '{}'.".format(self._path))
        return override_path

    def lips_path(self) -> str:
        lips_path = self._path
        for folder in os.listdir(self._path):
            if os.path.isdir(lips_path + folder) and folder.lower() == "lips":
                lips_path += folder + "/"
        if lips_path == self._path:
            raise ValueError("Could not find modules folder in '{}'.".format(self._path))
        return lips_path

    def texturepacks_path(self) -> str:
        texturepacks_path = self._path
        for folder in os.listdir(self._path):
            if os.path.isdir(texturepacks_path + folder) and folder.lower() == "texturepacks":
                texturepacks_path += folder + "/"
        if texturepacks_path == self._path:
            raise ValueError("Could not find modules folder in '{}'.".format(self._path))
        return texturepacks_path
    # endregion

    # region Load Data
    def load_chitin(self) -> None:
        chitin = Chitin(self._path)
        self._chitin = [resource for resource in chitin]

    def load_modules(self) -> None:
        self._modules = {}
        module_path = self.module_path()
        module_files = [file for file in os.listdir(module_path) if file.endswith('.mod')or file.endswith('.rim') or file.endswith('.erf')]
        for module in module_files:
            self._modules[module] = [resource for resource in Capsule(module_path + module)]

    def load_lips(self) -> None:
        self._lips = {}
        lips_path = self.lips_path()
        lip_files = [file for file in os.listdir(lips_path) if file.endswith('.mod')]
        for module in lip_files:
            self._lips[module] = [resource for resource in Capsule(lips_path + module)]

    def load_textures(self) -> None:
        self._texturepacks = {}
        texturepacks_path = self.texturepacks_path()
        texturepacks_files = [file for file in os.listdir(texturepacks_path) if file.endswith('.erf')]
        for module in texturepacks_files:
            self._texturepacks[module] = [resource for resource in Capsule(texturepacks_path + module)]

    def load_override(self) -> None:
        self._override = {}

        for path, subdirs, files in os.walk(self.override_path()):
            directory = path.replace("\\", "/").replace(self.override_path(), "")
            path = (path if path.endswith("/") else path + "/").replace("\\", "/")
            self._override[directory] = {}

            for file in files:
                with suppress(Exception):
                    name, ext = file.split('.', 1)
                    size = os.path.getsize(path + file)
                    resource = FileResource(name, ResourceType.from_extension(ext), size, 0, path + file)
                    self._override[directory][file] = resource
    # endregion

    # region Get FileResources
    def chitin_resources(self) -> List[FileResource]:
        return self._chitin[:]

    def modules_list(self) -> List[str]:
        return list(self._modules.keys())

    def module_resources(self, filename) -> List[FileResource]:
        return self._modules[filename][:]

    def lips_list(self) -> List[str]:
        return list(self._lips.keys())

    def lip_resources(self, filename) -> List[FileResource]:
        return self._lips[filename][:]

    def texturepacks_list(self) -> List[str]:
        return list(self._texturepacks.keys())

    def texturepack_resources(self, filename) -> List[FileResource]:
        return self._texturepacks[filename][:]

    def override_list(self) -> List[str]:
        return list(self._override.keys())

    def override_resources(self, directory: str) -> List[FileResource]:
        return list(self._override[directory].values())
    # endregion

    def talktable(self) -> TalkTable:
        return self._talktable

    def resource(self, resref: str, restype: ResourceType) -> Optional[bytes]:
        """
        Returns a resource matching the specified resref and restype. If no resource is found then None is returned
        instead. The method checks the following locations in descending order: override folder, in modules folder,
        then finally chitin.key.

        Args:
            resref: The ResRef.
            restype: The resource type.

        Returns:
            Resource data or None.
        """
        query = FileQuery(resref, restype)

        # 1st: Override
        for directory in self._override.values():
            for file_name, resource in directory.items():
                if resource == query:
                    return resource.data()

        # 2nd: Modules
        for module_name, resources in self._modules.items():
            for resource in resources:
                if resource == query:
                    return resource.data()

        # 3rd: Chitin
        for resource in self._chitin:
            if resource == query:
                return resource.data()

        return None

    def texture(self, resref: str, *, check_modules: bool = True, check_chitin: bool = True,
                check_gui: bool = True, texture_quality: TextureQuality = TextureQuality.HIGH) -> Optional[TPC]:
        """
        Returns a TPC object loaded from a resource with the specified ResRef. If no resource is found then None is
        returned instead. The method checks the following locations in descending order: override folder, tpa texture
        pack, then optionally the chitin.key and/or all modules.

        Args:
            resref: The ResRef.
            check_modules: Check the modules in the /modules folder.
            check_chitin: Check the resources referenced by the chitin.key file.
            check_gui: Check the textures stored in the GUI texturepack.
            texture_quality: Which texturepack to check.

        Returns:
            TPC object or None.
        """
        for directory in self._override.values():
            for file_name, resource in directory.items():
                if resource.resref() == resref and resource.restype() == ResourceType.TGA:
                    return load_tpc(resource.data())
                elif resource.resref() == resref and resource.restype() == ResourceType.TPC:
                    return load_tpc(resource.data())

        for resource in self.texturepack_resources("swpc_tex_tp{}.erf".format(texture_quality.value)):
            if resource.resref() == resref and resource.restype() == ResourceType.TPC:
                return load_tpc(resource.data())

        if check_gui:
            for resource in self.texturepack_resources("swpc_tex_gui.erf"):
                if resource.resref() == resref and resource.restype() == ResourceType.TPC:
                    return load_tpc(resource.data())

        if check_chitin:
            for resource in self._chitin:
                if resource.resref() == resref and resource.restype() == ResourceType.TPC:
                    return load_tpc(resource.data())

        if check_modules:
            for module_name, resources in self._modules.items():
                for resource in resources:
                    if resource.resref() == resref and resource.restype() == ResourceType.TPC:
                        return load_tpc(resource.data())

        return None

    def string(self, stringref: int) -> str:
        return self._talktable.string(stringref)
