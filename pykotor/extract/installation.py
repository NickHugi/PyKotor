from __future__ import annotations

import os
from collections import namedtuple
from contextlib import suppress
from copy import copy
from enum import Enum, IntEnum
from typing import Dict, List, Optional, Tuple, NamedTuple

from pykotor.common.stream import BinaryReader

from pykotor.common.language import Language, Gender
from pykotor.extract.file import FileResource, FileQuery, ResourceResult, LocationResult, ResourceIdentifier
from pykotor.extract.capsule import Capsule
from pykotor.extract.chitin import Chitin
from pykotor.extract.talktable import TalkTable
from pykotor.resource.formats.gff import load_gff
from pykotor.resource.formats.mdl import MDL
from pykotor.resource.formats.tlk import TLK
from pykotor.resource.formats.tpc import TPC, load_tpc
from pykotor.resource.formats.twoda import TwoDA, load_2da
from pykotor.resource.type import ResourceType


class SearchLocation(IntEnum):
    OVERRIDE = 0
    """Resources in the installation's override directory and any nested subfolders."""

    MODULES = 1
    """Encapsulated resources in the installation's 'modules' directory."""

    CHITIN = 2
    """Encapsulated resources linked to the installation's 'chitin.key' file."""

    TEXTURES_TPA = 3
    """Encapsulated resources in the installation's 'TexturePacks/swpc_tex_tpa.erf' file."""

    TEXTURES_TPB = 4
    """Encapsulated resources in the installation's 'TexturePacks/swpc_tex_tpb.erf' file."""

    TEXTURES_TPC = 5
    """Encapsulated resources in the installation's 'TexturePacks/swpc_tex_tpc.erf' file."""

    TEXTURES_GUI = 6
    """Encapsulated resources in the installation's 'TexturePacks/swpc_tex_gui.erf' file."""

    MUSIC = 7
    """Resource files in the installation's 'StreamMusic' directory and any nested subfolders."""

    SOUND = 8
    """Resource files in the installation's 'StreamSounds' directory and any nested subfolders."""

    VOICE = 9
    """Resource files in the installation's 'StreamVoice' or 'StreamWaves' directory and any nested subfolders."""

    LIPS = 10
    """Encapsulated resources in the installation's 'lips' directory."""

    RIMS = 11
    """Encapsulated resources in the installation's 'rims' directory."""

    CUSTOM_MODULES = 12
    """Encapsulated resources stored in the capsules specified in method parameters."""

    CUSTOM_FOLDERS = 13
    """Resource files stored in the folders specified in the method parameters."""


class ItemTuple(NamedTuple):
    resname: str
    name: str
    filepath: str


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

    def __init__(self, path: str, name: str = "KotOR", tsl: bool = False):
        self._path: str = path.replace('\\', '/')
        if not self._path.endswith('/'): self._path += '/'

        self.name: str = name
        self.tsl: bool = tsl

        self._chitin: List[FileResource] = []
        self._modules: Dict[str, List[FileResource]] = {}
        self._lips: Dict[str, List[FileResource]] = {}
        self._texturepacks: Dict[str, List[FileResource]] = {}
        self._override: Dict[str, Dict[str, FileResource]] = {}
        self._talktable: Optional[TalkTable] = TalkTable(self._path + "dialog.tlk")

        self.load_modules()
        self.load_override()
        self.load_lips()
        self.load_textures()
        self.load_chitin()

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

    def rims_path(self) -> str:
        path = self._path
        for folder in os.listdir(self._path):
            if os.path.isdir(path + folder) and folder.lower() == "rims":
                path += folder + "/"
        if path == self._path:
            raise ValueError("Could not find rims folder in '{}'.".format(self._path))
        return path

    def streammusic_path(self) -> str:
        path = self._path
        for folder in os.listdir(self._path):
            if os.path.isdir(path + folder) and folder.lower() == "streammusic":
                path += folder + "/"
        if path == self._path:
            raise ValueError("Could not find StreamMusic folder in '{}'.".format(self._path))
        return path

    def streamsounds_path(self) -> str:
        path = self._path
        for folder in os.listdir(self._path):
            if os.path.isdir(path + folder) and folder.lower() == "streamsounds":
                path += folder + "/"
        if path == self._path:
            raise ValueError("Could not find StreamSounds folder in '{}'.".format(self._path))
        return path

    def streamvoice_path(self) -> str:
        path = self._path
        for folder in os.listdir(self._path):
            if os.path.isdir(path + folder) and (folder.lower() == "streamvoice" or folder.lower() == "streamwaves"):
                path += folder + "/"
        if path == self._path:
            raise ValueError("Could not find voice over folder in '{}'.".format(self._path))
        return path
    # endregion

    # region Load Data
    def load_chitin(self) -> None:
        chitin = Chitin(self._path)
        self._chitin = [resource for resource in chitin]

    def load_modules(self) -> None:
        modules_path = self.module_path()
        self._modules = {}
        module_files = [file for file in os.listdir(modules_path) if file.endswith('.mod') or file.endswith('.rim') or file.endswith('.erf')]
        for module in module_files:
            with suppress(Exception):
                self._modules[module] = [resource for resource in Capsule(self.module_path() + module)]

    def reload_module(self, module) -> None:
        self._modules[module] = [resource for resource in Capsule(self.module_path() + module)]

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

    def reload_override(self, directory):
        override_path = self.override_path()

        self._override[directory] = {}
        files = os.listdir(override_path + directory)

        for file in files:
            with suppress(Exception):
                name, ext = file.split('.', 1)
                size = os.path.getsize(override_path + directory + file)
                resource = FileResource(name, ResourceType.from_extension(ext), size, 0, override_path + directory + file)
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

    def resource(self, resname: str, restype: ResourceType, search_order: List[SearchLocation] = None, *,
                 capsules: List[Capsule] = None, folders: List[str] = None) -> ResourceResult:
        """
        Returns a resource matching the specified resref and restype. If no resource is found then None is returned
        instead.

        The default search order is (descending priority): 1. Folders in the folders parameter, 2. Override folders,
        3. Capsules in the capsules parameter, 4. Game modules, 5. Chitin.

        Args:
            resname: The ResRef string.
            restype: The resource type.
            capsules: An extra list of capsules to search in.
            folders: An extra list of folders to search in.
            search_order: What locations to look in and in which order.

        Returns:
            A ResourceResult tuple if a resource is found otherwise None.
        """
        if search_order is None:
            search_order = [SearchLocation.CUSTOM_FOLDERS, SearchLocation.OVERRIDE, SearchLocation.CUSTOM_MODULES,
                            SearchLocation.MODULES, SearchLocation.CHITIN]

        capsules = [] if capsules is None else capsules
        folders = [] if folders is None else folders

        resname = resname.lower()
        query = FileQuery(resname, restype)

        def check_override():
            override_path = self.override_path()
            for subfolder, directory in self._override.items():
                for filename, resource in directory.items():
                    filepath = override_path + subfolder + filename
                    if resource == query:
                        return ResourceResult(filepath, resname, resource.data())

        def check_modules():
            module_path = self.module_path()
            for module_name, resources in self._modules.items():
                filepath = module_path + module_name
                for resource in resources:
                    if resource == query:
                        return ResourceResult(filepath, resname, resource.data())

        def check_chitin():
            filepath = self.path() + "chitin.key"
            for resource in self._chitin:
                if resource == query:
                    return ResourceResult(resource.filepath(), resname, resource.data())

        def check_texturepack(texturepack: str):
            for resource in self.texturepack_resources(texturepack):
                if resource.resname().lower() == resname.lower() and resource.restype() == ResourceType.TPC:
                    return ResourceResult(resource.filepath(), resource.resname(), resource.data())

        def check_music():
            streammusic_path = self.streammusic_path()
            sound_files = [file for file in os.listdir(streammusic_path)]
            for sound_file in sound_files:
                filepath = streammusic_path + sound_file
                f_resname, f_restype = ResourceIdentifier.from_path(filepath)
                if f_resname == resname and f_restype == restype:
                    size = os.path.getsize(filepath)
                    resource = FileResource(f_resname, f_restype, size, 0, filepath)
                    return ResourceResult(resource.filepath(), resource.resname(), resource.data())

        def check_sound():
            streamsound_path = self.streamsounds_path()
            sound_files = [file for file in os.listdir(streamsound_path)]
            for sound_file in sound_files:
                filepath = streamsound_path + sound_file
                f_resname, f_restype = ResourceIdentifier.from_path(filepath)
                if f_resname == resname and f_restype == restype:
                    size = os.path.getsize(filepath)
                    resource = FileResource(f_resname, f_restype, size, 0, filepath)
                    return ResourceResult(resource.filepath(), resource.resname(), resource.data())

        def check_voice():
            for path, subdirs, files in os.walk(self.streamvoice_path()):
                path = (path if path.endswith("/") else path + "/").replace("\\", "/")
                for file in files:
                    with suppress(Exception):
                        f_resname, f_restype = ResourceIdentifier.from_path(file)
                        if f_resname == resname and f_restype == restype:
                            size = os.path.getsize(path + file)
                            resource = FileResource(f_resname, f_restype, size, 0, path + file)
                            return ResourceResult(resource.filepath(), resource.resname(), resource.data())

        def check_lips():
            lips_path = self.lips_path()
            for module_name, resources in self._lips.items():
                filepath = lips_path + module_name
                for resource in resources:
                    if resource == query:
                        return ResourceResult(filepath, resname, resource.data())

        def check_rims():
            rims_path = self.rims_path()
            rim_files = [file for file in os.listdir(rims_path)]
            for rim_file in rim_files:
                capsule = Capsule(rims_path + rim_file)
                filepath = capsule.path()
                for resource in Capsule(filepath):
                    if resource == query:
                        return ResourceResult(filepath, resname, resource.data())

        def check_custom_modules():
            for capsule in capsules:
                if capsule.exists(resname, restype):
                    return ResourceResult(capsule.path(), resname, capsule.resource(resname, restype))

        def check_custom_folders():
            for folder in folders:
                folder = folder + '/' if not folder.endswith('/') else folder
                for file in [file for file in os.listdir(folder) if os.path.isfile(folder + file)]:
                    filepath = folder + file
                    with suppress(Exception):
                        f_resref, f_restype = ResourceIdentifier.from_path(file)
                        if query.resname.lower() == f_resref and query.restype == f_restype:
                            return ResourceResult(filepath, resname, BinaryReader.load_file(filepath))

        function_map = {
            SearchLocation.OVERRIDE: check_override,
            SearchLocation.CHITIN: check_chitin,
            SearchLocation.MODULES: check_modules,
            SearchLocation.VOICE: check_voice,
            SearchLocation.SOUND: check_sound,
            SearchLocation.MUSIC: check_music,
            SearchLocation.LIPS: check_lips,
            SearchLocation.RIMS: check_rims,
            SearchLocation.TEXTURES_TPA: lambda: check_texturepack("swpc_tex_tpa.erf"),
            SearchLocation.TEXTURES_TPB: lambda: check_texturepack("swpc_tex_tpb.erf"),
            SearchLocation.TEXTURES_TPC: lambda: check_texturepack("swpc_tex_tpc.erf"),
            SearchLocation.TEXTURES_GUI: lambda: check_texturepack("swpc_tex_gui.erf"),
            SearchLocation.CUSTOM_MODULES: check_custom_modules,
            SearchLocation.CUSTOM_FOLDERS: check_custom_folders
        }

        result = None

        for item in search_order:
            if result is None:
                result = function_map[item]()

        return result

    def resource_batch(self, queries: List[FileQuery], search_order: List[SearchLocation] = None, *,
                       capsules: List[Capsule] = None, folders: List[str] = None) -> List[ResourceResult]:
        results: List[ResourceResult] = []

        if search_order is None:
            search_order = [SearchLocation.CUSTOM_FOLDERS, SearchLocation.OVERRIDE, SearchLocation.CUSTOM_MODULES,
                            SearchLocation.MODULES, SearchLocation.CHITIN]

        capsules = [] if capsules is None else capsules
        folders = [] if folders is None else folders

        def check_override():
            override_path = self.override_path()
            for subfolder, directory in self._override.items():
                for filename, resource in directory.items():
                    filepath = override_path + subfolder + filename
                    for query in copy(queries):
                        if resource == query:
                            queries.remove(query)
                            results.append(ResourceResult(filepath, query.resname, resource.data()))

        def check_modules():
            for module_name, resources in self._modules.items():
                for resource in resources:
                    for query in copy(queries):
                        if resource == query:
                            queries.remove(query)
                            results.append(ResourceResult(resource.filepath(), query.resname, resource.data()))

        def check_chitin():
            handles = {}
            for resource in self._chitin:
                for query in copy(queries):
                    if resource == query:
                        queries.remove(query)
                        if resource.filepath() not in handles:
                            handles[resource.filepath()] = BinaryReader.from_file(resource.filepath())
                        handles[resource.filepath()].seek(resource.offset())
                        data = handles[resource.filepath()].read_bytes(resource.size())
                        results.append(ResourceResult(resource.filepath(), query.resname, data))
            for handle in handles:
                handles[handle].close()

        def check_texturepack(texturepack: str):
            for resource in self.texturepack_resources(texturepack):
                for query in copy(queries):
                    if resource == query:
                        queries.remove(query)
                        results.append(ResourceResult(resource.filepath(), resource.resname(), resource.data()))

        def check_music():
            streammusic_path = self.streammusic_path()
            sound_files = [file for file in os.listdir(streammusic_path)]
            for sound_file in sound_files:
                for query in copy(queries):
                    filepath = streammusic_path + sound_file
                    f_resname, f_restype = ResourceIdentifier.from_path(filepath)
                    if f_resname == query.resname and f_restype == query.restype:
                        queries.remove(query)
                        size = os.path.getsize(filepath)
                        resource = FileResource(f_resname, f_restype, size, 0, filepath)
                        results.append(ResourceResult(resource.filepath(), resource.resname(), resource.data()))

        def check_sound():
            streamsound_path = self.streamsounds_path()
            sound_files = [file for file in os.listdir(streamsound_path)]
            for sound_file in sound_files:
                for query in copy(queries):
                    filepath = streamsound_path + sound_file
                    f_resname, f_restype = ResourceIdentifier.from_path(filepath)
                    if f_resname == query.resname and f_restype == query.restype:
                        queries.remove(query)
                        size = os.path.getsize(filepath)
                        resource = FileResource(f_resname, f_restype, size, 0, filepath)
                        results.append(ResourceResult(resource.filepath(), resource.resname(), resource.data()))

        def check_voice():
            for path, subdirs, files in os.walk(self.streamvoice_path()):
                path = (path if path.endswith("/") else path + "/").replace("\\", "/")
                for file in files:
                    for query in copy(queries):
                        with suppress(Exception):
                            f_resname, f_restype = ResourceIdentifier.from_path(file)
                            if f_resname == query.resname and f_restype == query.restype:
                                queries.remove(query)
                                size = os.path.getsize(path + file)
                                resource = FileResource(f_resname, f_restype, size, 0, path + file)
                                results.append(ResourceResult(resource.filepath(), resource.resname(), resource.data()))

        def check_lips():
            for module_name, resources in self._lips.items():
                for resource in resources:
                    for query in copy(queries):
                        if resource == query:
                            queries.remove(query)
                            results.append(ResourceResult(resource.filepath(), resource.resname(), resource.data()))

        def check_rims():
            rims_path = self.rims_path()
            rim_files = [file for file in os.listdir(rims_path)]
            for rim_file in rim_files:
                capsule = Capsule(rims_path + rim_file)
                filepath = capsule.path()
                for resource in Capsule(filepath):
                    for query in copy(queries):
                        if resource == query:
                            results.append(ResourceResult(resource.filepath(), resource.resname(), resource.data()))

        def check_custom_modules():
            for capsule in capsules:
                for query in copy(queries):
                    if capsule.exists(query.resname, query.restype):
                        results.append(ResourceResult(capsule.path(), query.resname, capsule.resource(query.resname, query.restype)))

        def check_custom_folders():
            for folder in folders:
                folder = folder + '/' if not folder.endswith('/') else folder
                for file in [file for file in os.listdir(folder) if os.path.isfile(folder + file)]:
                    filepath = folder + file
                    with suppress(Exception):
                        f_resref, f_restype = ResourceIdentifier.from_path(file)
                        for query in copy(queries):
                            if query.resname.lower() == f_resref and query.restype == f_restype:
                                queries.remove(query)
                                results.append(ResourceResult(filepath, query.resname, BinaryReader.load_file(filepath)))

        function_map = {
            SearchLocation.OVERRIDE: check_override,
            SearchLocation.CHITIN: check_chitin,
            SearchLocation.MODULES: check_modules,
            SearchLocation.VOICE: check_voice,
            SearchLocation.SOUND: check_sound,
            SearchLocation.MUSIC: check_music,
            SearchLocation.LIPS: check_lips,
            SearchLocation.RIMS: check_rims,
            SearchLocation.TEXTURES_TPA: lambda: check_texturepack("swpc_tex_tpa.erf"),
            SearchLocation.TEXTURES_TPB: lambda: check_texturepack("swpc_tex_tpb.erf"),
            SearchLocation.TEXTURES_TPC: lambda: check_texturepack("swpc_tex_tpc.erf"),
            SearchLocation.TEXTURES_GUI: lambda: check_texturepack("swpc_tex_gui.erf"),
            SearchLocation.CUSTOM_MODULES: check_custom_modules,
            SearchLocation.CUSTOM_FOLDERS: check_custom_folders
        }

        for item in search_order:
            function_map[item]()

        return results

    def locate(self, resname: str, restype: ResourceType, search_order: List[SearchLocation] = None, *,
               capsules: List[Capsule] = None, folders: List[str] = None) -> List[LocationResult]:
        """
        Returns a list filepaths for where a particular resource matching the given resref and restype are located.

        Args:
            capsules: An extra list of capsules to search in.
            folders: An extra list of folders to search in.

        Returns:
            A list of filepaths.
        """
        capsules = [] if capsules is None else capsules
        folders = [] if folders is None else folders

        locations: List[LocationResult] = []
        query: FileQuery = FileQuery(resname, restype)

        def check_override():
            for subfolder, directory in self._override.items():
                for filename, resource in directory.items():
                    if resource == query:
                        locations.append(LocationResult(resource.filepath(), resource.offset(), resource.size()))

        def check_modules():
            for module_name, resources in self._modules.items():
                for resource in resources:
                    if resource == query:
                        locations.append(LocationResult(resource.filepath(), resource.offset(), resource.size()))

        def check_chitin():
            handles = {}
            for resource in self._chitin:
                if resource == query:
                    if resource.filepath() not in handles:
                        handles[resource.filepath()] = BinaryReader.from_file(resource.filepath())
                    handles[resource.filepath()].seek(resource.offset())
                    locations.append(LocationResult(resource.filepath(), resource.offset(), resource.size()))
            for handle in handles:
                handles[handle].close()

        def check_texturepack(texturepack: str):
            for resource in self.texturepack_resources(texturepack):
                if resource == query:
                    locations.append(LocationResult(resource.filepath(), resource.offset(), resource.size()))

        def check_music():
            streammusic_path = self.streammusic_path()
            sound_files = [file for file in os.listdir(streammusic_path)]
            for sound_file in sound_files:
                filepath = streammusic_path + sound_file
                f_resname, f_restype = ResourceIdentifier.from_path(filepath)
                if f_resname == query.resname and f_restype == query.restype:
                    size = os.path.getsize(filepath)
                    resource = FileResource(f_resname, f_restype, size, 0, filepath)
                    locations.append(LocationResult(resource.filepath(), resource.offset(), resource.size()))

        def check_sound():
            streamsound_path = self.streamsounds_path()
            sound_files = [file for file in os.listdir(streamsound_path)]
            for sound_file in sound_files:
                filepath = streamsound_path + sound_file
                f_resname, f_restype = ResourceIdentifier.from_path(filepath)
                if f_resname == query.resname and f_restype == query.restype:
                    size = os.path.getsize(filepath)
                    resource = FileResource(f_resname, f_restype, size, 0, filepath)
                    locations.append(LocationResult(resource.filepath(), resource.offset(), resource.size()))

        def check_voice():
            for path, subdirs, files in os.walk(self.streamvoice_path()):
                path = (path if path.endswith("/") else path + "/").replace("\\", "/")
                for file in files:
                    with suppress(Exception):
                        f_resname, f_restype = ResourceIdentifier.from_path(file)
                        if f_resname == query.resname and f_restype == query.restype:
                            size = os.path.getsize(path + file)
                            resource = FileResource(f_resname, f_restype, size, 0, path + file)
                            locations.append(LocationResult(resource.filepath(), resource.offset(), resource.size()))

        def check_lips():
            for module_name, resources in self._lips.items():
                for resource in resources:
                    if resource == query:
                        locations.append(LocationResult(resource.filepath(), resource.offset(), resource.size()))

        def check_rims():
            rims_path = self.rims_path()
            rim_files = [file for file in os.listdir(rims_path)]
            for rim_file in rim_files:
                capsule = Capsule(rims_path + rim_file)
                filepath = capsule.path()
                for resource in Capsule(filepath):
                    if resource == query:
                        locations.append(LocationResult(resource.filepath(), resource.offset(), resource.size()))

        def check_custom_modules():
            for capsule in capsules:
                if capsule.exists(query.resname, query.restype):
                    resource = FileResource(query.resname, query.restype, 0, 0, capsule.path())
                    locations.append(LocationResult(resource.filepath(), resource.offset(), resource.size()))

        def check_custom_folders():
            for folder in folders:
                folder = folder + '/' if not folder.endswith('/') else folder
                for file in [file for file in os.listdir(folder) if os.path.isfile(folder + file)]:
                    filepath = folder + file
                    with suppress(Exception):
                        f_resref, f_restype = ResourceIdentifier.from_path(file)
                        if query.resname.lower() == f_resref and query.restype == f_restype:
                            resource = FileResource(query.resname, query.restype, 0, 0, filepath)
                            locations.append(LocationResult(resource.filepath(), resource.offset(), resource.size()))

        function_map = {
            SearchLocation.OVERRIDE: check_override,
            SearchLocation.CHITIN: check_chitin,
            SearchLocation.MODULES: check_modules,
            SearchLocation.VOICE: check_voice,
            SearchLocation.SOUND: check_sound,
            SearchLocation.MUSIC: check_music,
            SearchLocation.LIPS: check_lips,
            SearchLocation.RIMS: check_rims,
            SearchLocation.TEXTURES_TPA: lambda: check_texturepack("swpc_tex_tpa.erf"),
            SearchLocation.TEXTURES_TPB: lambda: check_texturepack("swpc_tex_tpb.erf"),
            SearchLocation.TEXTURES_TPC: lambda: check_texturepack("swpc_tex_tpc.erf"),
            SearchLocation.TEXTURES_GUI: lambda: check_texturepack("swpc_tex_gui.erf"),
            SearchLocation.CUSTOM_MODULES: check_custom_modules,
            SearchLocation.CUSTOM_FOLDERS: check_custom_folders
        }

        for item in search_order:
            function_map[item]()

        return locations

    def texture(self, resname: str, *, capsules: List[Capsule] = None, folders: List[str] = None,
                skip_modules: bool = False, skip_chitin: bool = True, skip_gui: bool = True,
                skip_override: bool = False, texture_quality: TextureQuality = TextureQuality.HIGH) -> Optional[TPC]:
        """
        Returns a TPC object loaded from a resource with the specified ResRef.

        Texture is search for in the following order:
            1. "folders" parameter.
            2. "capsules" parameter.
            3. Installation override folder.
            4. Normal texture pack.
            5. GUI texture pack.
            6. Installation Chitin.
            7. Installation module files in modules folder.

        Args:
            resname: The ResRef string.
            capsules: An extra list of capsules to search in.
            folders: An extra list of folders to search in.
            skip_modules: If true, skips searching through module files in the installation modules folder.
            skip_chitin: If true, skips searching through chitin files in the installation.
            skip_gui: If true, skips searching through the gui files in the texturepacks folder.
            skip_override: If true, skips searching through the override files in the installation.
            texture_quality: Which texturepack to search through.

        Returns:
            TPC object or None.
        """
        capsules = [] if capsules is None else capsules
        folders = [] if folders is None else folders

        # 1 - Check user provided folders
        for folder in folders:
            folder = folder + '/' if not folder.endswith('/') else folder
            for file in [file for file in os.listdir(folder) if os.path.isfile(folder + file)]:
                with suppress(Exception):
                    f_resref, f_restype = ResourceIdentifier.from_path(file)
                    if resname.lower() == f_resref and f_restype in [ResourceType.TPC, ResourceType.TGA]:
                        return load_tpc(BinaryReader.load_file(folder + file))

        # 2 - Check user provided modules
        for capsule in capsules:
            if capsule.exists(resname, ResourceType.TGA):
                return capsule.resource(resname, ResourceType.TPC)
            if capsule.exists(resname, ResourceType.TPC):
                return capsule.resource(resname, ResourceType.TGA)

        # 3 - Check installation override folder
        if not skip_override:
            for directory in self._override.values():
                for file_name, resource in directory.items():
                    if resource.resname().lower() == resname.lower() and resource.restype() == ResourceType.TGA:
                        return load_tpc(resource.data())
                    elif resource.resname().lower() == resname.lower() and resource.restype() == ResourceType.TPC:
                        return load_tpc(resource.data())

        # 4 - Check normal texturepack
        for resource in self.texturepack_resources("swpc_tex_tp{}.erf".format(texture_quality.value)):
            if resource.resname().lower() == resname.lower() and resource.restype() == ResourceType.TPC:
                return load_tpc(resource.data())

        # 5 - Check GUI texturepack
        if not skip_gui:
            for resource in self.texturepack_resources("swpc_tex_gui.erf"):
                if resource.resname().lower() == resname.lower() and resource.restype() == ResourceType.TPC:
                    return load_tpc(resource.data())

        # 6 - Check chitin
        if not skip_chitin:
            for resource in self._chitin:
                if resource.resname().lower() == resname.lower() and resource.restype() == ResourceType.TGA:
                    return load_tpc(resource.data())
                if resource.resname().lower() == resname.lower() and resource.restype() == ResourceType.TPC:
                    return load_tpc(resource.data())

        # 7 - Check modules files in installation modules folder
        if not skip_modules:
            for module_name, resources in self._modules.items():
                for resource in resources:
                    if resource.resname().lower() == resname.lower() and resource.restype() == ResourceType.TPC:
                        return load_tpc(resource.data())
                    if resource.resname().lower() == resname.lower() and resource.restype() == ResourceType.TGA:
                        return load_tpc(resource.data())

        return None

    def twoda(self, resname: str) -> Optional[TwoDA]:
        return load_2da(self.resource(resname, ResourceType.TwoDA).data)

    def string(self, stringref: int) -> str:
        return self._talktable.string(stringref)

    def module_name(self, module_filename: str) -> str:
        """
        Returns the name of the area for a module from the installations module list. The name is taken from the
        LocalizedString "Name" in the relevant module file's ARE resource.

        Args:
            module_filename: The name of the module file.

        Returns:
            The name of the area for the module.
        """
        root = module_filename.replace(".mod", "").replace(".erf", "").replace(".rim", "")
        root = root[:-len("_s")] if root.endswith("_s") else root
        root = root[:-len("_dlg")] if root.endswith("_dlg") else root

        name = ""

        for module in self.modules_list():
            if root not in module:
                continue

            capsule = Capsule(self.module_path() + module)
            tag = ""

            if capsule.exists("module", ResourceType.IFO):
                ifo = load_gff(capsule.resource("module", ResourceType.IFO))
                tag = ifo.root.get_resref("Mod_Entry_Area").get()
            if capsule.exists(tag, ResourceType.ARE):
                are = load_gff(capsule.resource(tag, ResourceType.ARE))
                locstring = are.root.get_locstring("Name")
                if locstring.stringref > 0:
                    name = self._talktable.string(locstring.stringref)
                elif locstring.exists(Language.ENGLISH, Gender.MALE):
                    name = locstring.get(Language.ENGLISH, Gender.MALE)
                break

        return name

    def module_names(self) -> Dict[str, str]:
        """
        Returns a dictionary mapping module filename to the name of the area. The name is taken from the LocalizedString
        "Name" in the relevant module file's ARE resource.

        Returns:
            A dictionary mapping module filename to in-game module area name.
        """
        module_names = {}
        for module in self.modules_list():
            module_names[module] = self.module_name(module)
        return module_names
