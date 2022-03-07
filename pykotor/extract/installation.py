from __future__ import annotations

import os
from contextlib import suppress
from copy import copy
from enum import IntEnum
from typing import Dict, List, Optional, NamedTuple

from pykotor.common.language import Language, Gender, LocalizedString
from pykotor.common.misc import CaseInsensitiveDict
from pykotor.common.stream import BinaryReader
from pykotor.extract.capsule import Capsule
from pykotor.extract.chitin import Chitin
from pykotor.extract.file import FileResource, ResourceResult, LocationResult, ResourceIdentifier
from pykotor.extract.talktable import TalkTable
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.formats.tpc import TPC, read_tpc
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

    def __init__(
            self,
            path: str
    ):
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
    def path(
            self
    ) -> str:
        """
        Returns the path to root folder of the Installation.

        Returns:
            The path to the root folder.
        """
        return self._path

    def module_path(
            self
    ) -> str:
        """
        Returns the path to modules folder of the Installation. This method maintains the case of the foldername.

        Returns:
            The path to the modules folder.
        """
        module_path = self._path
        for folder in os.listdir(self._path):
            if os.path.isdir(module_path + folder) and folder.lower() == "modules":
                module_path += folder + "/"
        if module_path == self._path:
            raise ValueError("Could not find modules folder in '{}'.".format(self._path))
        return module_path

    def override_path(
            self
    ) -> str:
        """
        Returns the path to override folder of the Installation. This method maintains the case of the foldername.

        Returns:
            The path to the override folder.
        """
        override_path = self._path
        for folder in os.listdir(self._path):
            if os.path.isdir(override_path + folder) and folder.lower() == "override":
                override_path += folder + "/"
        if override_path == self._path:
            raise ValueError("Could not find override folder in '{}'.".format(self._path))
        return override_path

    def lips_path(
            self
    ) -> str:
        """
        Returns the path to lips folder of the Installation. This method maintains the case of the foldername.

        Returns:
            The path to the lips folder.
        """
        lips_path = self._path
        for folder in os.listdir(self._path):
            if os.path.isdir(lips_path + folder) and folder.lower() == "lips":
                lips_path += folder + "/"
        if lips_path == self._path:
            raise ValueError("Could not find modules folder in '{}'.".format(self._path))
        return lips_path

    def texturepacks_path(
            self
    ) -> str:
        """
        Returns the path to texturepacks folder of the Installation. This method maintains the case of the foldername.

        Returns:
            The path to the texturepacks folder.
        """
        texturepacks_path = self._path
        for folder in os.listdir(self._path):
            if os.path.isdir(texturepacks_path + folder) and folder.lower() == "texturepacks":
                texturepacks_path += folder + "/"
        if texturepacks_path == self._path:
            raise ValueError("Could not find modules folder in '{}'.".format(self._path))
        return texturepacks_path

    def rims_path(
            self
    ) -> str:
        """
        Returns the path to rims folder of the Installation. This method maintains the case of the foldername.

        Returns:
            The path to the rims folder.
        """
        path = self._path
        for folder in os.listdir(self._path):
            if os.path.isdir(path + folder) and folder.lower() == "rims":
                path += folder + "/"
        if path == self._path:
            raise ValueError("Could not find rims folder in '{}'.".format(self._path))
        return path

    def streammusic_path(
            self
    ) -> str:
        """
        Returns the path to streammusic folder of the Installation. This method maintains the case of the foldername.

        Returns:
            The path to the streammusic folder.
        """
        path = self._path
        for folder in os.listdir(self._path):
            if os.path.isdir(path + folder) and folder.lower() == "streammusic":
                path += folder + "/"
        if path == self._path:
            raise ValueError("Could not find StreamMusic folder in '{}'.".format(self._path))
        return path

    def streamsounds_path(
            self
    ) -> str:
        """
        Returns the path to streamsounds folder of the Installation. This method maintains the case of the foldername.

        Returns:
            The path to the streamsounds folder.
        """
        path = self._path
        for folder in os.listdir(self._path):
            if os.path.isdir(path + folder) and folder.lower() == "streamsounds":
                path += folder + "/"
        if path == self._path:
            raise ValueError("Could not find StreamSounds folder in '{}'.".format(self._path))
        return path

    def streamvoice_path(
            self
    ) -> str:
        """
        Returns the path to streamvoice folder of the Installation. This method maintains the case of the foldername.

        In the first game, this folder has been named "streamwaves".

        Returns:
            The path to the streamvoice folder.
        """
        path = self._path
        for folder in os.listdir(self._path):
            if os.path.isdir(path + folder) and (folder.lower() == "streamvoice" or folder.lower() == "streamwaves"):
                path += folder + "/"
        if path == self._path:
            raise ValueError("Could not find voice over folder in '{}'.".format(self._path))
        return path
    # endregion

    # region Load Data
    def load_chitin(
            self
    ) -> None:
        """
        Reloads the list of resouces in the Chitin linked to the Installation.
        """
        chitin = Chitin(self._path)
        self._chitin = [resource for resource in chitin]

    def load_modules(
            self
    ) -> None:
        """
        Reloads the list of modules files in the modules folder linked to the Installation.
        """
        modules_path = self.module_path()
        self._modules = {}
        module_files = [file for file in os.listdir(modules_path) if file.endswith('.mod') or file.endswith('.rim') or file.endswith('.erf')]
        for module in module_files:
            with suppress(Exception):
                self._modules[module] = [resource for resource in Capsule(self.module_path() + module)]

    def reload_module(
            self,
            module: str
    ) -> None:
        """
        Reloads the list of resouces in specified module in the modules folder linked to the Installation.

        Args:
            module: The filename of the module.
        """
        self._modules[module] = [resource for resource in Capsule(self.module_path() + module)]

    def load_lips(
            self
    ) -> None:
        """
        Reloads the list of modules in the lips folder linked to the Installation.
        """
        self._lips = {}
        lips_path = self.lips_path()
        lip_files = [file for file in os.listdir(lips_path) if file.endswith('.mod')]
        for module in lip_files:
            self._lips[module] = [resource for resource in Capsule(lips_path + module)]

    def load_textures(
            self
    ) -> None:
        """
        Reloads the list of modules files in the texturepacks folder linked to the Installation.
        """
        self._texturepacks = {}
        texturepacks_path = self.texturepacks_path()
        texturepacks_files = [file for file in os.listdir(texturepacks_path) if file.endswith('.erf')]
        for module in texturepacks_files:
            self._texturepacks[module] = [resource for resource in Capsule(texturepacks_path + module)]

    def load_override(
            self
    ) -> None:
        """
        Reloads the list of subdirectories in the override folder linked to the Installation.
        """
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

    def reload_override(
            self,
            directory: str
    ) -> None:
        """
        Reloads the list of resources in subdirectory of the override folder linked to the Installation.

        Args:
            directory: The subdirectory in the override folder.
        """
        override_path = self.override_path()

        self._override[directory] = []
        files = os.listdir(override_path + directory)

        for file in files:
            with suppress(Exception):
                name, ext = file.split('.', 1)
                size = os.path.getsize(override_path + directory + file)
                resource = FileResource(name, ResourceType.from_extension(ext), size, 0, override_path + directory + file)
                self._override[directory].append(resource)

    def load_streammusic(
            self
    ) -> None:
        self._streammusic = []
        streammusic_path = self.streammusic_path()
        for filename in [file for file in os.listdir(streammusic_path)]:
            with suppress(Exception):
                filepath = streammusic_path + filename
                identifier = ResourceIdentifier.from_path(filepath)
                resource = FileResource(identifier.resname, identifier.restype, os.path.getsize(filepath), 0, filepath)
                self._streammusic.append(resource)

    def load_streamsounds(
            self
    ) -> None:
        """
        Reloads the list of resources in the streamsounds folder linked to the Installation.
        """
        self._streamsounds = []
        streamsounds_path = self.streamsounds_path()
        for filename in [file for file in os.listdir(streamsounds_path)]:
            with suppress(Exception):
                filepath = streamsounds_path + filename
                identifier = ResourceIdentifier.from_path(filepath)
                resource = FileResource(identifier.resname, identifier.restype, os.path.getsize(filepath), 0, filepath)
                self._streamsounds.append(resource)

    def load_streamvoices(
            self
    ) -> None:
        """
        Reloads the list of resources in the streamvoices folder linked to the Installation.
        """
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

    def load_rims(
            self
    ) -> None:
        """
        Reloads the list of module files in the rims folder linked to the Installation.
        """
        self._rims = {}
        with suppress(ValueError):
            rims_path = self.rims_path()
            filenames = [file for file in os.listdir(rims_path) if file.endswith('.rim')]
            for filename in filenames:
                self._rims[filename] = [resource for resource in Capsule(rims_path + filename)]
    # endregion

    # region Get FileResources
    def chitin_resources(
            self
    ) -> List[FileResource]:
        """
        Returns the list of FileResources stored in the Chitin linked to the Installaiton.

        Returns:
            A list of FileResources.
        """
        return self._chitin[:]

    def modules_list(
            self
    ) -> List[str]:
        """
        Returns the list of module filenames located in the modules folder linked to the Installaiton.

        Module filenames are cached and require to be refreshed after a file is added, deleted or renamed.

        Returns:
            A list of filenames.
        """
        return list(self._modules.keys())

    def module_resources(
            self,
            filename: str
    ) -> List[FileResource]:
        """
        Returns a list of FileResources stored in the specified module file located in the modules folder linked to the
        Installation.

        Module resources are cached and require a reload after the contents have been modified.

        Returns:
            A list of FileResources.
        """
        return self._modules[filename][:]

    def lips_list(
            self
    ) -> List[str]:
        """
        Returns the list of module filenames located in the lips folder linked to the Installaiton.

        Module filenames are cached and require to be refreshed after a file is added, deleted or renamed.

        Returns:
            A list of filenames.
        """
        return list(self._lips.keys())

    def lip_resources(
            self,
            filename: str
    ) -> List[FileResource]:
        """
        Returns a list of FileResources stored in the specified module file located in the lips folder linked to the
        Installation.

        Module resources are cached and require a reload after the contents have been modified.

        Returns:
            A list of FileResources.
        """
        return self._lips[filename][:]

    def texturepacks_list(
            self
    ) -> List[str]:
        """
        Returns the list of texturepack filenames located in the texturepacks folder linked to the Installaiton.

        Returns:
            A list of filenames.
        """
        return list(self._texturepacks.keys())

    def texturepack_resources(
            self,
            filename: str
    ) -> List[FileResource]:
        """
        Returns a list of FileResources stored in the specified module file located in the texturepacks folder linked to
        the Installation.

        Texturepacks resources are cached and require a reload after the contents have been modified.

        Returns:
            A list of FileResources.
        """
        return self._texturepacks[filename][:]

    def override_list(
            self
    ) -> List[str]:
        """
        Returns the list of subdirectories located in override folder linked to the Installation.
        
        Subdirectories are cached and require to be refreshed after a folder is added, deleted or renamed.

        Returns:
            A list of subdirectories.
        """
        return list(self._override.keys())

    def override_resources(
            self,
            directory: str
    ) -> List[FileResource]:
        """
        Returns a list of FileResources stored in the specified subdirectory located in the override folder linked to
        the Installation.

        Override resources are cached and require a reload after the contents have been modified.

        Returns:
            A list of FileResources.
        """
        return list(self._override[directory])
    # endregion

    def talktable(
            self
    ) -> TalkTable:
        """
        Returns the TalkTable linked to the Installation.

        Returns:
            A TalkTable object.
        """
        return self._talktable

    def resource(
        self,
        resname: str,
        restype: ResourceType,
        order: List[SearchLocation] = None,
        *,
        capsules: List[Capsule] = None,
        folders: List[str] = None
    ) -> Optional[ResourceResult]:
        """
        Returns a resource matching the specified resref and restype. If no resource is found then None is returned
        instead.

        The default search order is (descending priority): 1. Folders in the folders parameter, 2. Override folders,
        3. Capsules in the capsules parameter, 4. Game modules, 5. Chitin.
        
        This is a wrapper of the resources() method provided to make fetching for a single resource more convienent.

        Args:
            resname: The name of the resource to look for.
            restype: The type of resource to look for.
            capsules: An extra list of capsules to search in.
            folders: An extra list of folders to search in.
            order: The ordered list of locations to check.

        Returns:
            A ResourceResult object if the specified resource is found, otherwise None.
        """

        query = ResourceIdentifier(resname, restype)
        batch = self.resources([query], order, capsules=capsules, folders=folders)

        return batch[query] if batch[query] else None

    def resources(
            self,
            queries: List[ResourceIdentifier],
            order: List[SearchLocation] = None,
            *,
            capsules: List[Capsule] = None,
            folders: List[str] = None
    ) -> Dict[ResourceIdentifier, Optional[ResourceResult]]:
        """
        Returns a dictionary mapping the items provided in the queries argument to the resource data if it was found. If
        the resource was not found, the value will be None.

        Args:
            queries: A list of resources to try load.
            order: The ordered list of locations to check.
            capsules: An extra list of capsules to search in.
            folders: An extra list of folders to search in.

        Returns:
            A dictionary mapping the given items in the queries argument to a list of ResourceResult objects.
        """
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

    def location(
            self,
            resname: str,
            restype: ResourceType,
            order: List[SearchLocation] = None,
            *,
            capsules: List[Capsule] = None,
            folders: List[str] = None
    ) -> List[LocationResult]:
        """
        Returns a list filepaths for where a particular resource matching the given resref and restype are located.

        This is a wrapper of the locations() method provided to make searching for a single resource more convienent.

        Args:
            resname: The name of the resource to look for.
            restype: The type of resource to look for.
            order: The ordered list of locations to check.
            capsules: An extra list of capsules to search in.
            folders: An extra list of folders to search in.

        Returns:
            A list of LocationResult objects.
        """
        capsules = [] if capsules is None else capsules
        folders = [] if folders is None else folders

        query: ResourceIdentifier = ResourceIdentifier(resname, restype)

        locations = self.locations([query], order, capsules=capsules, folders=folders)[query]

        return locations

    def locations(
            self,
            queries: List[ResourceIdentifier],
            order: List[SearchLocation] = None,
            *,
            capsules: List[Capsule] = None,
            folders: List[str] = None
    ) -> Dict[ResourceIdentifier, List[LocationResult]]:
        """
        Returns a dictionary mapping the items provided in the queries argument to a list of locations for that
        respective resource.

        Args:
            queries: A list of resources to try locate.
            order: The ordered list of locations to check.
            capsules: An extra list of capsules to search in.
            folders: An extra list of folders to search in.

        Returns:
            A dictionary mapping a resource identifier to a list of locations.
        """
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

    def texture(
            self,resname: str,
            order: List[SearchLocation] = None,
            *,
            capsules: List[Capsule] = None,
            folders: List[str] = None
    ) -> Optional[TPC]:
        """
        Returns a TPC object loaded from a resource with the specified name. If the specified texture could not be found
        then the method returns None.

        This is a wrapper of the textures() method provided to make searching for a single texture more convienent.

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
            order: The ordered list of locations to check.
            capsules: An extra list of capsules to search in.
            folders: An extra list of folders to search in.

        Returns:
            TPC object or None.
        """

        batch = self.textures([resname], order, capsules=capsules, folders=folders)
        return batch[resname] if batch else None

    def textures(
            self,
            queries: List[str],
            order: List[SearchLocation] = None,
            *,
            capsules: List[Capsule] = None,
            folders: List[str] = None
    ) -> CaseInsensitiveDict[Optional[TPC]]:
        """
        Returns a dictionary mapping the items provided in the queries argument to a TPC object if it exists. If the
        texture could not be found then the value is None.

        Args:
            queries: A list of resources to try locate.
            order: The ordered list of locations to check.
            capsules: An extra list of capsules to search in.
            folders: An extra list of folders to search in.

        Returns:
            A dictionary mapping case-insensitive strings to TPC objects or None.
        """
        capsules = [] if capsules is None else capsules
        folders = [] if folders is None else folders

        order = [SearchLocation.CUSTOM_FOLDERS, SearchLocation.OVERRIDE, SearchLocation.CUSTOM_MODULES,
                 SearchLocation.TEXTURES_TPA, SearchLocation.CHITIN] if order is None else order

        textures: CaseInsensitiveDict[Optional[TPC]] = CaseInsensitiveDict[Optional[TPC]]()
        texture_types = [ResourceType.TPC, ResourceType.TGA]
        queries = [resname.lower() for resname in queries]

        for resname in queries:
            textures[resname] = None

        def check_dict(values):
            for resources in values.values():
                for resource in resources:
                    if resource.resname() in copy(queries) and resource.restype() in texture_types:
                        queries.remove(resource.resname())
                        textures[resource.resname()] = read_tpc(resource.data())

        def check_list(values):
            for resource in values:
                if resource.resname() in copy(queries) and resource.restype() in texture_types:
                    queries.remove(resource.resname())
                    textures[resource.resname()] = read_tpc(resource.data())

        def check_capsules(values):
            for capsule in values:
                for resname in queries:
                    if capsule.exists(resname, ResourceType.TPC):
                        queries.remove(resname)
                        textures[resname] = read_tpc(capsule.resource(resname, ResourceType.TPC))
                    if capsule.exists(resname, ResourceType.TGA):
                        queries.remove(resname)
                        textures[resname] = read_tpc(capsule.resource(resname, ResourceType.TGA))

        def check_folders(values):
            for folder in values:
                folder = folder + '/' if not folder.endswith('/') else folder
                for file in [file for file in os.listdir(folder) if os.path.isfile(folder + file)]:
                    filepath = folder + file
                    identifier = ResourceIdentifier.from_path(file)
                    for resname in queries:
                        if identifier.resname == resname and identifier.restype in texture_types:
                            data = BinaryReader.load_file(filepath)
                            textures[resname] = read_tpc(data)

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

    def sound(
            self,
            queries: str,
            order: List[SearchLocation] = None,
            *,
            capsules: List[Capsule] = None,
            folders: List[str] = None
    ) -> Optional[Optional[bytes]]:
        """
        Returns the bytes of a sound resource if it can be found, otherwise returns None.

        This is a wrapper of the sounds() method provided to make searching for a single resource more convienent.

        Args:
            queries: The name of the resource to look for.
            order: The ordered list of locations to check.
            capsules: An extra list of capsules to search in.
            folders: An extra list of folders to search in.

        Returns:
            A bytes object or None.
        """
        batch = self.sounds([queries], order, capsules=capsules, folders=folders)
        return batch[queries] if batch else None

    def sounds(
            self,
            resnames: List[str],
            order: List[SearchLocation] = None,
            *,
            capsules: List[Capsule] = None,
            folders: List[str] = None
    ) -> CaseInsensitiveDict[Optional[bytes]]:
        """
        Returns a dictionary mapping the items provided in the queries argument to a bytes object if the respective
        sound resource could be found. If the sound could not be found the value will return None.

        Args:
            resnames: A list of sounds to try locate.
            order: The ordered list of locations to check.
            capsules: An extra list of capsules to search in.
            folders: An extra list of folders to search in.

        Returns:
            A dictionary mapping a case-insensitive string to a bytes object or None.
        """
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

    def string(
            self,
            locstring: LocalizedString,
            default: str = ""
    ) -> str:
        """
        Returns the string for the LocalizedString provided.
        
        This is a wrapper of the strings() method provided to make searching for a single string more convienent.
        
        Args:
            locstring: 
            default: 

        Returns:

        """
        batch = self.strings([locstring], default)
        return batch[locstring]

    def strings(
            self,
            queries: List[LocalizedString],
            default: str = ""
    ) -> Dict[LocalizedString, str]:
        """
        Returns a dictionary mapping the items provided in the queries argument to a string.
        
        As the method iterates through each LocalizedString it will first check if the TalkTable linked to the
        Installation has the stringref. If not it will try fallback on whatever substring exists in the LocalizedString
        and should that fail it will fallback on the default string specified.
        
        Args:
            queries: A list of LocalizedStrings.
            default: The fallback string if no string could be found.

        Returns:
            A dictionary mapping LocalizedString to a string.
        """
        stringrefs = [locstring.stringref for locstring in queries]
        batch = self.talktable().batch(stringrefs)

        results = {}
        for locstring in queries:
            if locstring.stringref in batch and locstring.stringref != -1:
                results[locstring] = batch[locstring.stringref].text
            elif len(locstring):
                for language, gender, text in locstring:
                    results[locstring] = text
                    break
            else:
                results[locstring] = default

        return results

    def module_name(
            self,
            module_filename: str
    ) -> str:
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
                ifo = read_gff(capsule.resource("module", ResourceType.IFO))
                tag = ifo.root.get_resref("Mod_Entry_Area").get()
            if capsule.exists(tag, ResourceType.ARE):
                are = read_gff(capsule.resource(tag, ResourceType.ARE))
                locstring = are.root.get_locstring("Name")
                if locstring.stringref > 0:
                    name = self._talktable.string(locstring.stringref)
                elif locstring.exists(Language.ENGLISH, Gender.MALE):
                    name = locstring.get(Language.ENGLISH, Gender.MALE)
                break

        return name

    def module_names(
            self
    ) -> Dict[str, str]:
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
