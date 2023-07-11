from __future__ import annotations

import os
from contextlib import suppress
from copy import copy
from enum import IntEnum
from pathlib import Path
from typing import Dict, List, Optional, NamedTuple

from pykotor.common.language import Language, Gender, LocalizedString
from pykotor.common.misc import CaseInsensitiveDict, Game
from pykotor.common.stream import BinaryReader
from pykotor.extract.capsule import Capsule
from pykotor.extract.chitin import Chitin
from pykotor.extract.file import FileResource, ResourceResult, LocationResult, ResourceIdentifier
from pykotor.extract.talktable import TalkTable
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.formats.tpc import TPC, read_tpc
from pykotor.resource.type import ResourceType
from pykotor.tools import sound

def is_module_rim_file(filename: str):
    return filename.lower().endswith(".rim")
def is_module_mod_file(filename: str):
    return filename.lower().endswith(".mod")
def is_module_erf_file(filename: str):
    return filename.lower().endswith(".erf")
def is_module_file(filename: str):
    filename = filename.lower()
    return (
        filename.endswith(".rim")
        or filename.endswith(".erf")
        or filename.endswith(".mod")
    )

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
            path: Path
    ):
        self._path: Path = path

        self._talktable: Optional[TalkTable] = TalkTable(self._path / "dialog.tlk")

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
    ) -> Path:
        """
        Returns the path to modules folder of the Installation. This method maintains the case of the foldername.

        Returns:
            The path to the modules folder.
        """
        module_path = self._path
        for folder in os.listdir(self._path):
            this_path = module_path / folder
            if this_path.is_dir() and folder.lower() == "modules":
                module_path = this_path
        if module_path == self._path:
            raise ValueError(f"Could not find modules folder in '{self._path}'.")
        return module_path

    def override_path(
            self
    ) -> Path:
        """
        Returns the path to override folder of the Installation. This method maintains the case of the foldername.

        Returns:
            The path to the override folder.
        """
        override_path = self._path
        for folder in os.listdir(self._path):
            this_path = override_path / folder
            if this_path.is_dir() and folder.lower() == "override":
                override_path = this_path
        if override_path == self._path:
            raise ValueError(f"Could not find override folder in '{self._path}'.")
        return override_path

    def lips_path(
            self
    ) -> Path:
        """
        Returns the path to lips folder of the Installation. This method maintains the case of the foldername.

        Returns:
            The path to the lips folder.
        """
        lips_path = self._path
        for folder in os.listdir(self._path):
            this_path = lips_path / folder
            if this_path.is_dir() and folder.lower() == "lips":
                lips_path = this_path
        if lips_path == self._path:
            raise ValueError(f"Could not find modules folder in '{self._path}'.")
        return lips_path

    def texturepacks_path(
            self
    ) -> Path:
        """
        Returns the path to texturepacks folder of the Installation. This method maintains the case of the foldername.

        Returns:
            The path to the texturepacks folder.
        """
        texturepacks_path = self._path
        for folder in os.listdir(self._path):
            this_path = texturepacks_path / folder
            if this_path.is_dir() and folder.lower() == "texturepacks":
                texturepacks_path = this_path
        if texturepacks_path == self._path:
            raise ValueError(f"Could not find modules folder in '{self._path}'.")
        return texturepacks_path

    def rims_path(
            self
    ) -> Path:
        """
        Returns the path to rims folder of the Installation. This method maintains the case of the foldername.

        Returns:
            The path to the rims folder.
        """
        rims_path = self._path
        for folder in os.listdir(self._path):
            this_path = Path(rims_path, folder)
            if this_path.is_dir() and folder.lower() == "rims":
                rims_path = this_path
        if rims_path == self._path:
            raise ValueError(f"Could not find rims folder in '{self._path}'.")
        return rims_path

    def streammusic_path(
            self
    ) -> Path:
        """
        Returns the path to streammusic folder of the Installation. This method maintains the case of the foldername.

        Returns:
            The path to the streammusic folder.
        """
        for folder in [folder for folder in self._path.iterdir() if folder.is_dir()]:
            this_path = streammusic_path / folder
            if this_path.is_dir() and folder.lower() == "streammusic":
                streammusic_path = this_path
        if streammusic_path == self._path:
            raise ValueError(f"Could not find StreamMusic folder in '{self._path}'.")
        return streammusic_path

    def streamsounds_path(
            self
    ) -> Path:
        """
        Returns the path to streamsounds folder of the Installation. This method maintains the case of the foldername.

        Returns:
            The path to the streamsounds folder.
        """
        streamsounds_path = self._path
        for folder in [folder for folder in self._path.iterdir() if folder.is_dir()]:
            this_path = streamsounds_path / folder
            if this_path.is_dir() and folder.lower() == "streamsounds":
                streamsounds_path = this_path
        if streamsounds_path == self._path:
            raise ValueError(f"Could not find StreamSounds folder in '{self._path}'.")
        return Path(streamsounds_path).resolve()

    def streamvoice_path(
            self
    ) -> Path:
        """
        Returns the path to streamvoice folder of the Installation. This method maintains the case of the foldername.

        In the first game, this folder has been named "streamwaves".

        Returns:
            The path to the streamvoice folder.
        """
        streamwavesvoice_path = self._path
        for folder in os.listdir(self._path):
            this_path = streamwavesvoice_path / folder
            if this_path.is_dir() and (folder.lower() == "streamvoice" or folder.lower() == "streamwaves"):
                streamwavesvoice_path = this_path
        if streamwavesvoice_path == self._path:
            raise ValueError(f"Could not find voice over folder in '{self._path}'.")
        return Path(streamwavesvoice_path).resolve()
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
        for module in [file for file in os.listdir(modules_path) if is_module_file(file)]:
            with suppress(Exception):
                self._modules[module] = [resource for resource in Capsule(self.module_path() / module)]

    def reload_module(
            self,
            module: str
    ) -> None:
        """
        Reloads the list of resouces in specified module in the modules folder linked to the Installation.

        Args:
            module: The filename of the module.
        """
        self._modules[module] = [resource for resource in Capsule(self.module_path() / module)]

    def load_lips(
            self
    ) -> None:
        """
        Reloads the list of modules in the lips folder linked to the Installation.
        """
        self._lips = {}
        lips_path = self.lips_path()
        lip_files = [file for file in os.listdir(lips_path) if is_module_mod_file(file)]
        for module in lip_files:
            self._lips[module] = [resource for resource in Capsule(lips_path / module)]

    def load_textures(
            self
    ) -> None:
        """
        Reloads the list of modules files in the texturepacks folder linked to the Installation.
        """
        self._texturepacks = {}
        texturepacks_path = self.texturepacks_path()
        texturepacks_files = [file for file in os.listdir(texturepacks_path) if is_module_erf_file(file)]
        for module in texturepacks_files:
            self._texturepacks[module] = [resource for resource in Capsule(texturepacks_path / module)]

    def load_override(
            self
    ) -> None:
        """
        Reloads the list of subdirectories in the override folder linked to the Installation.
        """
        self._override = {}
        override_path = self.override_path()

        for file_path in Path(override_path).glob('**' + os.sep + '*'):
            override_subdir = file_path.parent
            self._override[override_subdir] = []
            with suppress(Exception):
                name, ext = file_path.stem, file_path.suffix
                size = file_path.stat().st_size
                resource = FileResource(name, ResourceType.from_extension(ext), size, 0, file_path)
                self._override[override_subdir].append(resource)

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
        for file in (override_path / directory).iterdir():
            with suppress(Exception):
                resource = FileResource(file.stem, ResourceType.from_extension(file.suffix), file.stat().st_size, 0, file)
                self._override[directory].append(resource)

    def load_streammusic(
            self
    ) -> None:
        self._streammusic = []
        streammusic_path = self.streammusic_path()
        for file in streammusic_path.iterdir():
            with suppress(Exception):
                identifier = ResourceIdentifier.from_path(file)
                resource = FileResource(identifier.resname, identifier.restype, file.stat().st_size, 0, file)
                self._streammusic.append(resource)

    def load_streamsounds(
            self
    ) -> None:
        """
        Reloads the list of resources in the streamsounds folder linked to the Installation.
        """
        self._streamsounds = []
        streamsounds_path = self.streamsounds_path()
        for file in streamsounds_path.iterdir():
            with suppress(Exception):
                identifier = ResourceIdentifier.from_path(file)
                resource = FileResource(identifier.resname, identifier.restype, file.stat().st_size, 0, filepath)
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
                    filepath = Path(path, filename)
                    identifier = ResourceIdentifier.from_path(filepath)
                    resource = FileResource(identifier.resname, identifier.restype, pathlib.getsize(filepath), 0, filepath)
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
            filenames = [file for file in os.listdir(rims_path) if file.lower().endswith('.rim')]
            for filename in filenames:
                self._rims[filename] = [resource for resource in Capsule(Path(rims_path, filename))]
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

    def game(
        self
    ) -> Game:
        return Game(2 if Path(Path(self._path, "swkotor2.exe").exists) else 1)

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
        folders: List[Path] = None
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
                        resource = capsule.info(query.resname, query.restype, reload=True)
                        location = LocationResult(resource.filepath(), resource.offset(), resource.size())
                        locations[resource.identifier()].append(location)

        def check_folders(values):
            for folder in values:
                folder = Path(folder).resolve()
                filepath = Path(folder, file)
                for file in [file for file in os.listdir(folder) if pathlib.isfile(filepath)]:
                    filepath = Path(folder, file)
                    for query in queries:
                        with suppress(Exception):
                                identifier = ResourceIdentifier.from_path(file)
                                if query == identifier:
                                    resource = FileResource(query.resname, query.restype, pathlib.getsize(filepath), 0, filepath)
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
                folder = Path(folder).resolve()
                filepath = Path(folder, file)
                for file in [file for file in os.listdir(folder) if pathlib.isfile(filepath)]:
                    filepath = Path(folder, file)
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
                folder = Path(folder).resolve()
                filepath = Path(folder, file)
                for file in [file for file in os.listdir(folder) if pathlib.isfile(filepath)]:
                    filepath = Path(folder, file)
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
            module_filename: str,
            use_hardcoded: bool = True
    ) -> str:
        """
        Returns the name of the area for a module from the installations module list. The name is taken from the
        LocalizedString "Name" in the relevant module file's ARE resource.

        Args:
            module_filename: The name of the module file.
            use_hardcoded: Use hardcoded values for modules where applicable.

        Returns:
            The name of the area for the module.
        """
        root = module_filename.replace(".mod", "").replace(".erf", "").replace(".rim", "")
        root = root[:-len("_s")] if root.endswith("_s") else root
        root = root[:-len("_dlg")] if root.endswith("_dlg") else root

        hardcoded = {
            "STUNT_00": "Ebon Hawk - Cutscene (Vision Sequences)",
            "STUNT_03A": "Leviathan - Cutscene (Destroy Taris)",
            "STUNT_06": "Leviathan - Cutscene (Resume Bombardment)",
            "STUNT_07": "Ebon Hawk - Cutscene (Escape Taris)",
            "STUNT_12": "Leviathan - Cutscene (Calo Nord)",
            "STUNT_14": "Leviathan - Cutscene (Darth Bandon)",
            "STUNT_16": "Ebon Hawk - Cutscene (Leviathan Capture)",
            "STUNT_18": "Unknown World - Cutscene (Bastila Torture)",
            "STUNT_19": "Star Forge - Cutscene (Jawless Malak)",
            "STUNT_31B": "Unknown World - Cutscene (Revan Reveal)",
            "STUNT_34": "Ebon Hawk - Cutscene (Star Forge Arrival)",
            "STUNT_35": "Ebon Hawk - Cutscene (Lehon Crash)",
            "STUNT_42": "Ebon Hawk - Cutscene (LS Dodonna Call)",
            "STUNT_44": "Ebon Hawk - Cutscene (DS Dodonna Call)",
            "STUNT_50A": "Dodonna Flagship - Cutscene (Break In Formation)",
            "STUNT_51A": "Dodonna Flagship - Cutscene (Bastilla Against Us)",
            "STUNT_54A": "Dodonna Flagship - Cutscene (Pull Back)",
            "STUNT_55A": "Unknown World - Cutscene (DS Ending)",
            "STUNT_56A": "Dodona Flagship - Cutscene (Star Forge Destroyed)",
            "STUNT_57": "Unknown World - Cutscene (LS Ending)",
            "001EBO": "Ebon Hawk - Interior (Prologue)",
            "004EBO": "Ebon Hawk - Interior (Red Eclipse)",
            "005EBO": "Ebon Hawk - Interior (Escaping Peragus)",
            "006EBO": "Ebon Hawk - Cutscene (After Rebuilt Enclave)",
            "007EBO": "Ebon Hawk - Cutscene (After Goto's Yatch)",
            "154HAR": "Harbinger - Cutscene (Sion Introduction)",
            "205TEL": "Citadel Station - Cutscene (Carth Discussion)",
            "352NAR": "Nar Shaddaa - Cutscene (Goto Introduction)",
            "853NIH": "Ravager - Cutscene (Nihilus Introduction)",
            "856NIH": "Ravager - Cutscene (Sion vs. Nihilus)"
        }

        if use_hardcoded:
            for key in hardcoded.keys():
                if key.upper() in module_filename.upper():
                    return hardcoded[key]

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

    def module_id(
            self,
            module_filename: str,
            use_hardcoded: bool = True
    ) -> str:
        """
        Returns the ID of the area for a module from the installations module list. The ID is taken from the
        ResRef field "Mod_Entry_Area" in the relevant module file's IFO resource.

        Args:
            module_filename: The name of the module file.
            use_hardcoded: Use hardcoded values for modules where applicable.

        Returns:
            The ID of the area for the module.
        """
        base_file_name, ext = pathlib.splitext(module_filename)
        newExt = ext.lower().replace(".mod", "").replace(".erf", "").replace(".rim", "")
        if newExt.lower() != ext.lower():
            ext = newExt
        root = base_file_name + ext
        root = root.lower()[:-len("_s")] if root.lower().endswith("_s") else root
        root = root.lower()[:-len("_dlg")] if root.lower().endswith("_dlg") else root

        hardcoded = {
            "STUNT_00": "000",
            "STUNT_03A": "m03a",
            "STUNT_06": "m07",
            "STUNT_07": "m07",
            "STUNT_12": "m12",
            "STUNT_14": "m14",
            "STUNT_16": "m16",
            "STUNT_18": "m18",
            "STUNT_19": "m19",
            "STUNT_31B": "m31b",
            "STUNT_34": "m34",
            "STUNT_35": "m35",
            "STUNT_42": "m43",
            "STUNT_44": "m44",
            "STUNT_50A": "m50a",
            "STUNT_51A": "m51a",
            "STUNT_54A": "m54a",
            "STUNT_55A": "m55a",
            "STUNT_56A": "m56a",
            "STUNT_57": "m57",
        }

        if use_hardcoded:
            for key in hardcoded.keys():
                if key.upper() in module_filename.upper():
                    return hardcoded[key]

        mod_id = ""

        for module in self.modules_list():
            if root not in module:
                continue

            capsule = Capsule(self.module_path() + module)

            if capsule.exists("module", ResourceType.IFO):
                ifo = read_gff(capsule.resource("module", ResourceType.IFO))
                mod_id = ifo.root.get_resref("Mod_Entry_Area").get()

        return mod_id

    def module_ids(
            self
    ) -> Dict[str, str]:
        """
        Returns a dictionary mapping module filename to the ID of the module. The ID is taken from the
        ResRef field "Mod_Entry_Area" in the relevant module file's IFO resource.

        Returns:
            A dictionary mapping module filename to in-game module id.
        """
        module_ids = {}
        for module in self.modules_list():
            module_ids[module] = self.module_id(module)
        return module_ids

    def uninstall_mods(
            self
    ) -> None:
        """
        Uninstalls all mods from the game.

        What this method really does is delete all the contents of the override folder and delete all .MOD files from
        the modules folder.
        """
        for file in os.listdir(self.module_path()):
            filepath = Path(Path(self.module_path().resolve(), file))
            if is_module_mod_file(filepath) and pathlib.isfile(filepath):
                os.remove(filepath)

        for file in os.listdir(self.override_path()):
            filepath = Path(Path(self.override_path().resolve(), file))
            if pathlib.isfile(filepath):
                os.remove(filepath)
