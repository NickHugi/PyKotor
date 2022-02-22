from __future__ import annotations

import os
from collections import namedtuple
from contextlib import suppress
from copy import copy
from enum import Enum, IntEnum
from typing import Dict, List, Optional, Tuple, NamedTuple

from pykotor.common.misc import CaseInsensitiveDict
from pykotor.common.stream import BinaryReader

from pykotor.common.language import Language, Gender, LocalizedString
from pykotor.extract.file import FileResource, ResourceResult, LocationResult, ResourceIdentifier
from pykotor.extract.capsule import Capsule
from pykotor.extract.chitin import Chitin
from pykotor.extract.talktable import TalkTable
from pykotor.resource.formats.gff import load_gff
from pykotor.resource.formats.mdl import MDL
from pykotor.resource.formats.tlk import TLK
from pykotor.resource.formats.tpc import TPC, load_tpc
from pykotor.resource.formats.twoda import TwoDA, load_2da
from pykotor.resource.type import ResourceType
from pykotor.tools import sound


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


class Installation:
    """
    Installation provides a centralized location for loading resources stored in the game through its
    various folders and formats.
    """
    TEXTURES_TYPES = [ResourceType.TPC, ResourceType.TGA, ResourceType.DDS]

    def __init__(self, path: str):
        self._path: str = path.replace('\\', '/')
        if not self._path.endswith('/'): self._path += '/'

        self._talktable: Optional[TalkTable] = TalkTable(self._path + "dialog.tlk")

        self._chitin: List[FileResource] = []
        self._modules: Dict[str, List[FileResource]] = {}
        self._lips: Dict[str, List[FileResource]] = {}
        self._texturepacks: Dict[str, List[FileResource]] = {}
        self._override: Dict[str, List[FileResource]] = {}
        self._streammusic: List[FileResource] = []
        self._streamsounds: List[FileResource] = []
        self._streamvoices: List[FileResource] = []
        self._rims: Dict[str, List[FileResource]] = {}

        self.load_modules()
        self.load_override()
        self.load_lips()
        self.load_textures()
        self.load_chitin()
        self.load_streammusic()
        self.load_streamsounds()
        self.load_streamvoices()
        self.load_rims()

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
        override_path = self.override_path()

        for path, subdirs, files in os.walk(override_path):
            directory = path.replace("\\", "/").replace(override_path, "")
            path = (path if path.endswith("/") else path + "/").replace("\\", "/")
            self._override[directory] = []

            for file in files:
                with suppress(Exception):
                    name, ext = file.split('.', 1)
                    size = os.path.getsize(path + file)
                    resource = FileResource(name, ResourceType.from_extension(ext), size, 0, path + file)
                    self._override[directory].append(resource)

    def reload_override(self, directory) -> None:
        override_path = self.override_path()

        self._override[directory] = []
        files = os.listdir(override_path + directory)

        for file in files:
            with suppress(Exception):
                name, ext = file.split('.', 1)
                size = os.path.getsize(override_path + directory + file)
                resource = FileResource(name, ResourceType.from_extension(ext), size, 0, override_path + directory + file)
                self._override[directory].append(resource)

    def load_streammusic(self) -> None:
        self._streammusic = []
        streammusic_path = self.streammusic_path()
        for filename in [file for file in os.listdir(streammusic_path)]:
            with suppress(Exception):
                filepath = streammusic_path + filename
                identifier = ResourceIdentifier.from_path(filepath)
                resource = FileResource(identifier.resname, identifier.restype, os.path.getsize(filepath), 0, filepath)
                self._streammusic.append(resource)

    def load_streamsounds(self) -> None:
        self._streamsounds = []
        streamsounds_path = self.streamsounds_path()
        for filename in [file for file in os.listdir(streamsounds_path)]:
            with suppress(Exception):
                filepath = streamsounds_path + filename
                identifier = ResourceIdentifier.from_path(filepath)
                resource = FileResource(identifier.resname, identifier.restype, os.path.getsize(filepath), 0, filepath)
                self._streamsounds.append(resource)

    def load_streamvoices(self) -> None:
        self._streamvoices = []
        streamvoices_path = self.streamvoice_path()

        for path, subdirs, files in os.walk(streamvoices_path):
            for filename in files:
                with suppress(Exception):
                    folderpath = path.replace("\\", "/")
                    if not folderpath.endswith("/"):
                        folderpath += "/"
                    filepath = folderpath + filename
                    identifier = ResourceIdentifier.from_path(filepath)
                    resource = FileResource(identifier.resname, identifier.restype, os.path.getsize(filepath), 0, filepath)
                    self._streamvoices.append(resource)

    def load_rims(self) -> None:
        self._rims = {}
        with suppress(ValueError):
            rims_path = self.rims_path()
            filenames = [file for file in os.listdir(rims_path) if file.endswith('.rim')]
            for filename in filenames:
                self._rims[filename] = [resource for resource in Capsule(rims_path + filename)]
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
        return list(self._override[directory])
    # endregion

    def talktable(self) -> TalkTable:
        return self._talktable

    def resource(self, resname: str, restype: ResourceType, order: List[SearchLocation] = None, *,
                 capsules: List[Capsule] = None, folders: List[str] = None) -> Optional[ResourceResult]:
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
            order: What locations to look in and in which order.

        Returns:
            A ResourceResult tuple if a resource is found otherwise None.
        """

        query = ResourceIdentifier(resname, restype)
        batch = self.resources([query], order, capsules=capsules, folders=folders)

        return batch[query] if batch[query] else None

    def resources(self, queries: List[ResourceIdentifier], order: List[SearchLocation] = None, *,
                  capsules: List[Capsule] = None, folders: List[str] = None) -> Dict[ResourceIdentifier, Optional[ResourceResult]]:

        results: Dict[ResourceIdentifier, Optional[ResourceResult]] = {}
        locations = self.locations(queries, order, capsules=capsules, folders=folders)
        handles = {}

        for query in queries:
            location = locations[query][0] if locations[query] else None
            if location is None:
                results[query] = None
            else:
                if query not in handles:
                    handles[query] = BinaryReader.from_file(location.filepath)
                handles[query].seek(location.offset)
                data = handles[query].read_bytes(location.size)
                results[query] = ResourceResult(query.resname, query.restype, location.filepath, data)

        for handle in handles.values():
            handle.close()

        return results

    def location(self, resname: str, restype: ResourceType, order: List[SearchLocation] = None, *,
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

        query: ResourceIdentifier = ResourceIdentifier(resname, restype)

        locations = self.locations([query], order, capsules=capsules, folders=folders)[query]

        return locations

    def locations(self, queries: List[ResourceIdentifier], order: List[SearchLocation] = None, *,
                  capsules: List[Capsule] = None, folders: List[str] = None) -> Dict[ResourceIdentifier, List[LocationResult]]:
        capsules = [] if capsules is None else capsules
        folders = [] if folders is None else folders

        order = [SearchLocation.CUSTOM_FOLDERS, SearchLocation.OVERRIDE, SearchLocation.CUSTOM_MODULES,
                 SearchLocation.MODULES, SearchLocation.CHITIN] if order is None else order

        locations: Dict[ResourceIdentifier, List[LocationResult]] = {}
        for qinden in queries:
            locations[qinden] = []

        def check_dict(values):
            for resources in values.values():
                for resource in resources:
                    if resource in queries:
                        location = LocationResult(resource.filepath(), resource.offset(), resource.size())
                        locations[resource.identifier()].append(location)

        def check_list(values):
            for resource in values:
                if resource in queries:
                    location = LocationResult(resource.filepath(), resource.offset(), resource.size())
                    locations[resource.identifier()].append(location)

        def check_capsules(values):
            for capsule in values:
                for query in queries:
                    if capsule.exists(query.resname, query.restype):
                        resource = FileResource(query.resname, query.restype, 0, 0, capsule.path())
                        location = LocationResult(resource.filepath(), resource.offset(), resource.size())
                        locations[resource.identifier()].append(location)

        def check_folders(values):
            for folder in values:
                folder = folder + '/' if not folder.endswith('/') else folder
                for file in [file for file in os.listdir(folder) if os.path.isfile(folder + file)]:
                    filepath = folder + file
                    for query in queries:
                        with suppress(Exception):
                                identifier = ResourceIdentifier.from_path(file)
                                if query == identifier:
                                    resource = FileResource(query.resname, query.restype, 0, 0, filepath)
                                    location = LocationResult(resource.filepath(), resource.offset(), resource.size())
                                    locations[identifier].append(location)

        function_map = {
            SearchLocation.OVERRIDE: lambda: check_dict(self._override),
            SearchLocation.MODULES: lambda: check_dict(self._modules),
            SearchLocation.LIPS: lambda: check_dict(self._lips),
            SearchLocation.RIMS: lambda: check_dict(self._rims),
            SearchLocation.TEXTURES_TPA: lambda: check_list(self._texturepacks["swpc_tex_tpa.erf"]),
            SearchLocation.TEXTURES_TPB: lambda: check_list(self._texturepacks["swpc_tex_tpb.erf"]),
            SearchLocation.TEXTURES_TPC: lambda: check_list(self._texturepacks["swpc_tex_tpc.erf"]),
            SearchLocation.TEXTURES_GUI: lambda: check_list(self._texturepacks["swpc_tex_gui.erf"]),
            SearchLocation.CHITIN: lambda: check_list(self._chitin),
            SearchLocation.MUSIC: lambda: check_list(self._streammusic),
            SearchLocation.SOUND: lambda: check_list(self._streamsounds),
            SearchLocation.VOICE: lambda: check_list(self._streamvoices),
            SearchLocation.CUSTOM_MODULES: lambda: check_capsules(capsules),
            SearchLocation.CUSTOM_FOLDERS: lambda: check_folders(folders)
        }

        for item in order:
            function_map[item]()

        return locations

    def texture(self, resname: str, order: List[SearchLocation] = None, *,
                capsules: List[Capsule] = None, folders: List[str] = None) -> Optional[TPC]:
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

        batch = self.textures([resname], order, capsules=capsules, folders=folders)
        return batch[resname] if batch else None

    def textures(self, resnames: List[str], order: List[SearchLocation] = None, *,
                 capsules: List[Capsule] = None, folders: List[str] = None) -> CaseInsensitiveDict[Optional[TPC]]:
        capsules = [] if capsules is None else capsules
        folders = [] if folders is None else folders

        order = [SearchLocation.CUSTOM_FOLDERS, SearchLocation.OVERRIDE, SearchLocation.CUSTOM_MODULES,
                 SearchLocation.TEXTURES_TPA, SearchLocation.CHITIN] if order is None else order

        textures: CaseInsensitiveDict[Optional[TPC]] = CaseInsensitiveDict[Optional[TPC]]()
        texture_types = [ResourceType.TPC, ResourceType.TGA]
        resnames = [resname.lower() for resname in resnames]

        for resname in resnames:
            textures[resname] = None

        def check_dict(values):
            for resources in values.values():
                for resource in resources:
                    if resource.resname() in copy(resnames) and resource.restype() in texture_types:
                        resnames.remove(resource.resname())
                        textures[resource.resname()] = load_tpc(resource.data())

        def check_list(values):
            for resource in values:
                if resource.resname() in copy(resnames) and resource.restype() in texture_types:
                    resnames.remove(resource.resname())
                    textures[resource.resname()] = load_tpc(resource.data())

        def check_capsules(values):
            for capsule in values:
                for resname in resnames:
                    if capsule.exists(resname, ResourceType.TPC):
                        resnames.remove(resname)
                        textures[resname] = load_tpc(capsule.resource(resname, ResourceType.TPC))
                    if capsule.exists(resname, ResourceType.TGA):
                        resnames.remove(resname)
                        textures[resname] = load_tpc(capsule.resource(resname, ResourceType.TGA))

        def check_folders(values):
            for folder in values:
                folder = folder + '/' if not folder.endswith('/') else folder
                for file in [file for file in os.listdir(folder) if os.path.isfile(folder + file)]:
                    filepath = folder + file
                    identifier = ResourceIdentifier.from_path(file)
                    for resname in resnames:
                        if identifier.resname == resname and identifier.restype in texture_types:
                            data = BinaryReader.load_file(filepath)
                            textures[resname] = load_tpc(data)

        function_map = {
            SearchLocation.OVERRIDE: lambda: check_dict(self._override),
            SearchLocation.MODULES: lambda: check_dict(self._modules),
            SearchLocation.LIPS: lambda: check_dict(self._lips),
            SearchLocation.RIMS: lambda: check_dict(self._rims),
            SearchLocation.TEXTURES_TPA: lambda: check_list(self._texturepacks["swpc_tex_tpa.erf"]),
            SearchLocation.TEXTURES_TPB: lambda: check_list(self._texturepacks["swpc_tex_tpb.erf"]),
            SearchLocation.TEXTURES_TPC: lambda: check_list(self._texturepacks["swpc_tex_tpc.erf"]),
            SearchLocation.TEXTURES_GUI: lambda: check_list(self._texturepacks["swpc_tex_gui.erf"]),
            SearchLocation.CHITIN: lambda: check_list(self._chitin),
            SearchLocation.MUSIC: lambda: check_list(self._streammusic),
            SearchLocation.SOUND: lambda: check_list(self._streamsounds),
            SearchLocation.VOICE: lambda: check_list(self._streamvoices),
            SearchLocation.CUSTOM_MODULES: lambda: check_capsules(capsules),
            SearchLocation.CUSTOM_FOLDERS: lambda: check_folders(folders)
        }

        for item in order:
            function_map[item]()

        return textures

    def sound(self, resname: str, order: List[SearchLocation] = None, *, capsules: List[Capsule] = None,
              folders: List[str] = None) -> Optional[Optional[bytes]]:
        batch = self.sounds([resname], order, capsules=capsules, folders=folders)
        return batch[resname] if batch else None

    def sounds(self, resnames: List[str], order: List[SearchLocation] = None, *, capsules: List[Capsule] = None,
               folders: List[str] = None) -> CaseInsensitiveDict[Optional[bytes]]:
        capsules = [] if capsules is None else capsules
        folders = [] if folders is None else folders

        order = [SearchLocation.CUSTOM_FOLDERS, SearchLocation.OVERRIDE, SearchLocation.CUSTOM_MODULES,
                 SearchLocation.SOUND, SearchLocation.CHITIN] if not order else order

        sounds: CaseInsensitiveDict[Optional[bytes]] = CaseInsensitiveDict[Optional[bytes]]()
        texture_types = [ResourceType.WAV, ResourceType.MP3]
        resnames = [resname.lower() for resname in resnames]

        for resname in resnames:
            sounds[resname] = None

        def check_dict(values):
            for resources in values.values():
                for resource in resources:
                    if resource.resname() in copy(resnames) and resource.restype() in texture_types:
                        resnames.remove(resource.resname())
                        sounds[resource.resname()] = sound.fix_audio(resource.data())

        def check_list(values):
            for resource in values:
                if resource.resname() in copy(resnames) and resource.restype() in texture_types:
                    resnames.remove(resource.resname())
                    sounds[resource.resname()] = sound.fix_audio(resource.data())

        def check_capsules(values):
            for capsule in values:
                for resname in resnames:
                    if capsule.exists(resname, ResourceType.WAV):
                        resnames.remove(resname)
                        sounds[resname] = sound.fix_audio(capsule.resource(resname, ResourceType.TPC))
                    if capsule.exists(resname, ResourceType.MP3):
                        resnames.remove(resname)
                        sounds[resname] = sound.fix_audio(capsule.resource(resname, ResourceType.TGA))

        def check_folders(values):
            for folder in values:
                folder = folder + '/' if not folder.endswith('/') else folder
                for file in [file for file in os.listdir(folder) if os.path.isfile(folder + file)]:
                    filepath = folder + file
                    identifier = ResourceIdentifier.from_path(file)
                    for resname in resnames:
                        if identifier.resname == resname and identifier.restype in texture_types:
                            data = BinaryReader.load_file(filepath)
                            sounds[resname] = sound.fix_audio(data)

        function_map = {
            SearchLocation.OVERRIDE: lambda: check_dict(self._override),
            SearchLocation.MODULES: lambda: check_dict(self._modules),
            SearchLocation.LIPS: lambda: check_dict(self._lips),
            SearchLocation.RIMS: lambda: check_dict(self._rims),
            SearchLocation.TEXTURES_TPA: lambda: check_list(self._texturepacks["swpc_tex_tpa.erf"]),
            SearchLocation.TEXTURES_TPB: lambda: check_list(self._texturepacks["swpc_tex_tpb.erf"]),
            SearchLocation.TEXTURES_TPC: lambda: check_list(self._texturepacks["swpc_tex_tpc.erf"]),
            SearchLocation.TEXTURES_GUI: lambda: check_list(self._texturepacks["swpc_tex_gui.erf"]),
            SearchLocation.CHITIN: lambda: check_list(self._chitin),
            SearchLocation.MUSIC: lambda: check_list(self._streammusic),
            SearchLocation.SOUND: lambda: check_list(self._streamsounds),
            SearchLocation.VOICE: lambda: check_list(self._streamvoices),
            SearchLocation.CUSTOM_MODULES: lambda: check_capsules(capsules),
            SearchLocation.CUSTOM_FOLDERS: lambda: check_folders(folders)
        }

        for item in order:
            function_map[item]()

        return sounds

    def string(self, locstring: LocalizedString, default: str = "") -> str:
        batch = self.strings([locstring], default)
        return batch[locstring]

    def strings(self, locstrings: List[LocalizedString], default: str = "") -> Dict[LocalizedString, str]:
        stringrefs = [locstring.stringref for locstring in locstrings]
        batch = self.talktable().batch(stringrefs)

        results = {}
        for locstring in locstrings:
            if locstring.stringref in batch and locstring.stringref != -1:
                results[locstring] = batch[locstring.stringref].text
            elif len(locstring):
                for language, gender, text in locstring:
                    results[locstring] = text
                    break
            else:
                results[locstring] = default

        return results

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
