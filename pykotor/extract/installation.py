from __future__ import annotations

import re
from contextlib import suppress
from copy import copy
from enum import IntEnum
from typing import TYPE_CHECKING, ClassVar, NamedTuple, Optional

from pykotor.common.language import Gender, Language, LocalizedString
from pykotor.common.misc import CaseInsensitiveDict, Game
from pykotor.common.stream import BinaryReader
from pykotor.extract.capsule import Capsule
from pykotor.extract.chitin import Chitin
from pykotor.extract.file import (
    FileResource,
    LocationResult,
    ResourceIdentifier,
    ResourceResult,
)
from pykotor.extract.talktable import TalkTable
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.formats.tpc import TPC, read_tpc
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_capsule_file, is_erf_file, is_mod_file, is_rim_file
from pykotor.tools.path import CaseAwarePath
from pykotor.tools.sound import fix_audio
from pykotor.tslpatcher.logger import PatchLogger

if TYPE_CHECKING:
    import os

    from pykotor.resource.formats.gff import GFF


def is_kotor_install_dir(path: os.PathLike | str) -> bool:
    c_path: CaseAwarePath = CaseAwarePath(path)
    return c_path.is_dir() and c_path.joinpath("chitin.key").exists()


# The SearchLocation class is an enumeration that represents different locations for searching.
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
    filepath: CaseAwarePath


class Installation:
    """Installation provides a centralized location for loading resources stored in the game through its
    various folders and formats.
    """

    TEXTURES_TYPES: ClassVar[list[ResourceType]] = [
        ResourceType.TPC,
        ResourceType.TGA,
        ResourceType.DDS,
    ]

    def __init__(self, path: CaseAwarePath | os.PathLike | str, logger: PatchLogger | None = None):
        self._path: CaseAwarePath = path if isinstance(path, CaseAwarePath) else CaseAwarePath(path)
        self.log = logger or PatchLogger()

        self._talktable: TalkTable = TalkTable(self._path / "dialog.tlk")

        self._chitin: list[FileResource] = []
        self._modules: dict[str, list[FileResource]] = {}
        self._lips: dict[str, list[FileResource]] = {}
        self._texturepacks: dict[str, list[FileResource]] = {}
        self._override = CaseInsensitiveDict()
        self._streammusic: list[FileResource] = []
        self._streamsounds: list[FileResource] = []
        self._streamwaves: list[FileResource] = []
        self._rims: dict[str, list[FileResource]] = {}

        self.log.add_note("Load modules...")
        self.load_modules()
        self.log.add_note("Load override...")
        self.load_override()
        self.log.add_note("Load lips...")
        self.load_lips()
        self.log.add_note("Load textures...")
        self.load_textures()
        self.log.add_note("Load chitin...")
        self.load_chitin()
        self.log.add_note("Load streammusic...")
        self.load_streammusic()
        self.log.add_note("Load streamsounds...")
        self.load_streamsounds()
        self.log.add_note(f"Load {'streamvoice' if self.game() == Game.K2 else 'streamwaves'}...")
        self.load_streamwaves()
        self.log.add_note("Load rims...")
        self.load_rims()
        self.log.add_note("Finished loading installation")

    # region Get Paths
    def path(self) -> CaseAwarePath:
        """Returns the path to root folder of the Installation.

        Returns
        -------
            The path to the root folder.
        """
        return self._path

    def module_path(self) -> CaseAwarePath:
        """Returns the path to modules folder of the Installation. This method maintains the case of the foldername.

        Returns
        -------
            The path to the modules folder.
        """
        return self._find_resource_folderpath(
            ("Modules",),
            "Could not find modules folder in '{}'.",
        )

    def override_path(self) -> CaseAwarePath:
        """Returns the path to override folder of the Installation. This method maintains the case of the foldername.

        Returns
        -------
            The path to the override folder.
        """
        return self._find_resource_folderpath(
            ("Override",),
            "Could not find override folder in '{}'.",
            optional=True,
        )

    def lips_path(self) -> CaseAwarePath:
        """Returns the path to lips folder of the Installation. This method maintains the case of the foldername.

        Returns
        -------
            The path to the lips folder.
        """
        return self._find_resource_folderpath(
            ("lips",),
            "Could not find lips folder in '{}'.",
        )

    def texturepacks_path(self) -> CaseAwarePath:
        """Returns the path to texturepacks folder of the Installation. This method maintains the case of the foldername.

        Returns
        -------
            The path to the texturepacks folder.
        """
        return self._find_resource_folderpath(
            ("texturepacks",),
            "Could not find texturepacks folder in '{}'.",
        )

    def rims_path(self) -> CaseAwarePath:
        """Returns the path to rims folder of the Installation. This method maintains the case of the foldername.

        Returns
        -------
            The path to the rims folder.
        """
        return self._find_resource_folderpath(
            ("rims",),
            "Could not find rims folder in '{}'.",
            optional=True,
        )

    def streammusic_path(self) -> CaseAwarePath:
        """Returns the path to streammusic folder of the Installation. This method maintains the case of the foldername.

        Returns
        -------
            The path to the streammusic folder.
        """
        return self._find_resource_folderpath(
            ("streammusic",),
            "Could not find StreamMusic folder in '{}'.",
        )

    def streamsounds_path(self) -> CaseAwarePath:
        """Returns the path to streamsounds folder of the Installation. This method maintains the case of the foldername.

        Returns
        -------
            The path to the streamsounds folder.
        """
        return self._find_resource_folderpath(
            ("streamsounds",),
            "Could not find StreamSounds folder in '{}'.",
        )

    def _find_resource_folderpath(
        self,
        folder_names: tuple[str, ...],
        error_msg: str,
        optional: bool = False,
    ) -> CaseAwarePath:
        resource_path = self._path

        for folder_name in folder_names:
            resource_path = self._path / folder_name
            if resource_path.is_dir():
                break
        if resource_path == self._path:
            if optional:
                return next(
                    (self._path / name for name in folder_names if (self._path / name).exists()),
                    self._path / folder_names[0],
                )
            raise ValueError(error_msg.format(self._path))

        return resource_path

    def streamwaves_path(self) -> CaseAwarePath:
        """Returns the path to streamvoice folder of the Installation. This method maintains the case of the foldername.

        In the first game, this folder has been named "streamwaves".

        Returns
        -------
            The path to the streamvoice folder.
        """
        return self._find_resource_folderpath(
            ("streamvoice", "streamwaves"),
            "Could not find voice over folder in '{}'.",
        )

    # endregion

    # region Load Data

    def load_chitin(self) -> None:
        """Reloads the list of resources in the Chitin linked to the Installation."""
        chitin = Chitin(self._path)
        self._chitin = list(chitin)

    def load_modules(self) -> None:
        """Reloads the list of modules files in the modules folder linked to the Installation."""
        self._modules = {}
        for module in self.module_path().iterdir():
            if is_capsule_file(module.name):
                with suppress(Exception):
                    self._modules[module.name] = list(Capsule(module))

    def reload_module(self, module: str) -> None:
        """Reloads the list of resources in specified module in the modules folder linked to the Installation.

        Args:
        ----
            module: The filename of the module.
        """
        self._modules[module] = list(Capsule(self.module_path() / module))

    def load_lips(
        self,
    ) -> None:
        """Reloads the list of modules in the lips folder linked to the Installation."""
        self._lips = {}
        lips_path = self.lips_path()
        lip_files = [file for file in lips_path.iterdir() if is_mod_file(file.name)]
        for module in lip_files:
            self._lips[module.name] = list(Capsule(lips_path / module))

    def load_textures(
        self,
    ) -> None:
        """Reloads the list of modules files in the texturepacks folder linked to the Installation."""
        self._texturepacks = {}
        texturepacks_path = self.texturepacks_path()
        texturepacks_files = [file for file in texturepacks_path.iterdir() if is_erf_file(file.name)]
        for module in texturepacks_files:
            self._texturepacks[module.name] = list(Capsule(texturepacks_path / module))

    def load_override(self, directory: str | None = None) -> None:
        """Loads the list of resources in a specific subdirectory of the override folder linked to the Installation.
        If a directory argument is not passed, this will reload all subdirectories in the Override folder.
        If directory argument is "", this will load all the loose files in the Override folder.

        the _override dict follows the following example format:
        _override[""] = list[FileResource]  # the loose files in the Override folder
        _override["subdir1"] = list[FileResource]  # the loose files in subdir1
        _override["subdir2"] = list[FileResource]  # the loose files in subdir2
        _override["subdir1/subdir3"] = list[FileResource]  # the loose files in subdir1/subdir3. Key is always a posix path (delimited by /'s)

        Args:
        ----
            directory: The subdirectory in the override folder.
        """
        override_path = self.override_path()
        if directory is not None:
            target_dirs = [override_path / directory]
            self._override[directory] = []
        else:
            target_dirs = [f for f in override_path.rglob("*") if f.is_dir()]
            target_dirs.append(override_path)
            self._override = CaseInsensitiveDict()

        for folder in target_dirs:
            relative_folder = folder.relative_to(override_path).as_posix()
            self._override[relative_folder] = self.load_resources_list(folder, recurse=False)

    def load_resources_list(self, path: os.PathLike | str, recurse=True) -> list[FileResource]:
        """Load resources for a given path and store them in the provided list.

        Args:
        ----
            path_method (os.PathLike | str): path for lookup.
            recurse (bool): whether to recurse into subfolders (default is True)

        Returns:
        -------
            (list[FileResource]): The list where resources at the path have been stored.
        """
        c_path = CaseAwarePath(path)
        resource_list = []
        for file in c_path.rglob("*") if recurse else c_path.iterdir():
            with suppress(Exception):
                identifier = ResourceIdentifier.from_path(file)
                resource = FileResource(
                    identifier.resname,
                    identifier.restype,
                    file.stat().st_size,
                    0,
                    file,
                )
                resource_list.append(resource)
        return resource_list

    def load_streammusic(self) -> None:
        """Reloads the list of resources in the streammusic folder linked to the Installation."""
        self._streammusic = self.load_resources_list(self.streammusic_path(), recurse=False)

    def load_streamsounds(self) -> None:
        """Reloads the list of resources in the streamsounds folder linked to the Installation."""
        self._streamsounds = self.load_resources_list(self.streamsounds_path(), recurse=False)

    def load_streamwaves(self) -> None:
        """Reloads the list of resources in the streamvoice/streamwaves folder linked to the Installation."""
        self._streamwaves = self.load_resources_list(self.streamwaves_path(), recurse=True)

    def load_rims(
        self,
    ) -> None:
        """Reloads the list of module files in the rims folder linked to the Installation."""
        self._rims = {}
        with suppress(FileNotFoundError, IsADirectoryError, ValueError):
            rims_path: CaseAwarePath = self.rims_path()
            for file in rims_path.iterdir():
                if is_rim_file(file.name):
                    self._rims[file.name] = list(Capsule(file))

    # endregion

    # region Get FileResources
    def chitin_resources(self) -> list[FileResource]:
        """Returns the list of FileResources stored in the Chitin linked to the Installation.

        Returns
        -------
            A list of FileResources.
        """
        return self._chitin[:]

    def modules_list(self) -> list[str]:
        """Returns the list of module filenames located in the modules folder
        linked to the Installation.

        Module filenames are cached and require to be refreshed after a file
        is added, deleted or renamed.

        Returns
        -------
            A list of filenames.
        """
        return list(self._modules.keys())

    def module_resources(self, filename: str) -> list[FileResource]:
        """Returns a list of FileResources stored in the specified module file
        located in the modules folder linked to the Installation.

        Module resources are cached and require a reload after the contents
        have been modified.

        Returns
        -------
            A list of FileResources.
        """
        return self._modules[filename][:]

    def lips_list(self) -> list[str]:
        """Returns the list of module filenames located in the lips folder
        linked to the Installation.

        Module filenames are cached and require to be refreshed after a file
        is added, deleted or renamed.

        Returns
        -------
            A list of filenames.
        """
        return list(self._lips.keys())

    def lip_resources(self, filename: str) -> list[FileResource]:
        """Returns a list of FileResources stored in the specified module file
        located in the lips folder linked to the
        Installation.

        Module resources are cached and require a reload after the contents
        have been modified.

        Returns
        -------
            A list of FileResources.
        """
        return self._lips[filename][:]

    def texturepacks_list(self) -> list[str]:
        """Returns the list of texture-pack filenames located in the texturepacks
        folder linked to the Installation.

        Returns
        -------
            A list of filenames.
        """
        return list(self._texturepacks.keys())

    def texturepack_resources(self, filename: str) -> list[FileResource]:
        """Returns a list of FileResources stored in the specified module file
        located in the texturepacks folder linked to
        the Installation.

        Texturepacks resources are cached and require a reload after the
        contents have been modified.

        Returns
        -------
            A list of FileResources.
        """
        return self._texturepacks[filename][:]

    def override_list(self) -> list[str]:
        """Returns the list of subdirectories located in override folder
        linked to the Installation.

        Subdirectories are cached and require to be refreshed after a folder
        is added, deleted or renamed.

        Returns
        -------
            A list of subdirectories.
        """
        return list(self._override.keys())

    def override_resources(self, directory: str) -> list[FileResource]:
        """Returns a list of FileResources stored in the specified subdirectory
        located in the override folder linked to
        the Installation.

        Override resources are cached and require a reload after the contents
        have been modified.

        Returns
        -------
            A list of FileResources.
        """
        return self._override[directory]

    # endregion

    def game(self) -> Game:
        if (self._path.joinpath("streamvoice").exists() or self._path.joinpath("swkotor2.exe")) and is_kotor_install_dir(
            self._path,
        ):
            return Game(2)
        if (self._path.joinpath("streamwaves").exists() or self._path.joinpath("swkotor.exe")) and is_kotor_install_dir(
            self._path,
        ):
            return Game(1)
        msg = "Could not find the game executable!"
        raise ValueError(msg)

    def talktable(self) -> TalkTable:
        """Returns the TalkTable linked to the Installation.

        Returns
        -------
            A TalkTable object.
        """
        return self._talktable

    def resource(
        self,
        resname: str,
        restype: ResourceType,
        order: list[SearchLocation] | None = None,
        *,
        capsules: list[Capsule] | None = None,
        folders: list[CaseAwarePath] | None = None,
    ) -> ResourceResult | None:
        """Returns a resource matching the specified resref and restype. If no resource is found then None is returned
        instead.

        The default search order is (descending priority): 1. Folders in the folders parameter, 2. Override folders,
        3. Capsules in the capsules parameter, 4. Game modules, 5. Chitin.

        This is a wrapper of the resources() method provided to make fetching for a single resource more convenient.

        Args:
        ----
            resname: The name of the resource to look for.
            restype: The type of resource to look for.
            capsules: An extra list of capsules to search in.
            folders: An extra list of folders to search in.
            order: The ordered list of locations to check.

        Returns:
        -------
            A ResourceResult object if the specified resource is found, otherwise None.
        """
        query = ResourceIdentifier(resname, restype)
        batch: dict[ResourceIdentifier, ResourceResult | None] = self.resources(
            [query],
            order,
            capsules=capsules,
            folders=folders,
        )

        return batch[query] or None

    def resources(
        self,
        queries: list[ResourceIdentifier],
        order: list[SearchLocation] | None = None,
        *,
        capsules: list[Capsule] | None = None,
        folders: list[CaseAwarePath] | None = None,
    ) -> dict[ResourceIdentifier, ResourceResult | None]:
        """Returns a dictionary mapping the items provided in the queries argument to the resource data if it was found. If
        the resource was not found, the value will be None.

        Args:
        ----
            queries: A list of resources to try load.
            order: The ordered list of locations to check.
            capsules: An extra list of capsules to search in.
            folders: An extra list of folders to search in.

        Returns:
        -------
            A dictionary mapping the given items in the queries argument to a list of ResourceResult objects.
        """
        results: dict[ResourceIdentifier, ResourceResult | None] = {}
        locations: dict[ResourceIdentifier, list[LocationResult]] = self.locations(
            queries,
            order,
            capsules=capsules,
            folders=folders,
        )

        handles: dict[ResourceIdentifier, BinaryReader] = {}

        for query in queries:
            location_list = locations.get(query, [])

            if not location_list:
                self.log.add_error(f"Resource not found: '{query}'")
                results[query] = None
                continue

            location = location_list[0]

            if query not in handles:
                handles[query] = BinaryReader.from_file(location.filepath)

            handle = handles[query]
            handle.seek(location.offset)
            data = handle.read_bytes(location.size)

            results[query] = ResourceResult(
                query.resname,
                query.restype,
                location.filepath,
                data,
            )

        # Close all open handles
        for handle in handles.values():
            handle.close()

        return results

    def location(
        self,
        resname: str,
        restype: ResourceType,
        order: list[SearchLocation] | None = None,
        *,
        capsules: list[Capsule] | None = None,
        folders: list[CaseAwarePath] | None = None,
    ) -> list[LocationResult]:
        """Returns a list filepaths for where a particular resource matching the given resref and restype are located.

        This is a wrapper of the locations() method provided to make searching for a single resource more convenient.

        Args:
        ----
            resname: The name of the resource to look for.
            restype: The type of resource to look for.
            order: The ordered list of locations to check.
            capsules: An extra list of capsules to search in.
            folders: An extra list of folders to search in.

        Returns:
        -------
            A list of LocationResult objects.
        """
        capsules = [] if capsules is None else capsules
        folders = [] if folders is None else folders

        query: ResourceIdentifier = ResourceIdentifier(resname, restype)

        return self.locations(
            [query],
            order,
            capsules=capsules,
            folders=folders,
        )[query]

    def locations(
        self,
        queries: list[ResourceIdentifier],
        order: list[SearchLocation] | None = None,
        *,
        capsules: list[Capsule] | None = None,
        folders: list[CaseAwarePath] | None = None,
    ) -> dict[ResourceIdentifier, list[LocationResult]]:
        """Returns a dictionary mapping the items provided in the queries argument to a list of locations for that
        respective resource.

        Args:
        ----
            queries: A list of resources to try locate.
            order: The ordered list of locations to check.
            capsules: An extra list of capsules to search in.
            folders: An extra list of folders to search in.

        Returns:
        -------
            A dictionary mapping a resource identifier to a list of locations.
        """
        capsules = [] if capsules is None else capsules
        folders = [] if folders is None else folders

        order = (
            order
            if order is not None
            else (
                [
                    SearchLocation.CUSTOM_FOLDERS,
                    SearchLocation.OVERRIDE,
                    SearchLocation.CUSTOM_MODULES,
                    SearchLocation.MODULES,
                    SearchLocation.CHITIN,
                ]
            )
        )

        locations: dict[ResourceIdentifier, list[LocationResult]] = {}
        for qinden in queries:
            locations[qinden] = []

        def check_dict(values: dict[str, list[FileResource]]):
            for resources in values.values():
                for resource in resources:
                    if resource in queries:
                        location = LocationResult(
                            resource.filepath(),
                            resource.offset(),
                            resource.size(),
                        )
                        locations[resource.identifier()].append(location)

        def check_list(values: list[FileResource]):
            for resource in values:
                if resource in queries:
                    location = LocationResult(
                        resource.filepath(),
                        resource.offset(),
                        resource.size(),
                    )
                    locations[resource.identifier()].append(location)

        def check_capsules(values: list[Capsule]):
            for capsule in values:
                for query in queries:
                    if capsule.exists(query.resname, query.restype):
                        resource = capsule.info(
                            query.resname,
                            query.restype,
                            reload=True,
                        )
                        location = LocationResult(
                            resource.filepath(),
                            resource.offset(),
                            resource.size(),
                        )
                        locations[resource.identifier()].append(location)

        def check_folders(values: list[CaseAwarePath]):
            for folderpath in values:
                c_folderpath = CaseAwarePath(folderpath)
                for file in c_folderpath.iterdir():
                    if not file.is_file():
                        continue
                    for query in queries:
                        with suppress(Exception):
                            identifier = ResourceIdentifier.from_path(file)
                            if query == identifier:
                                resource = FileResource(
                                    query.resname,
                                    query.restype,
                                    file.stat().st_size,
                                    0,
                                    file,
                                )
                                location = LocationResult(
                                    resource.filepath(),
                                    resource.offset(),
                                    resource.size(),
                                )
                                locations[identifier].append(location)

        function_map = {
            SearchLocation.OVERRIDE: lambda: check_dict(self._override),  # type: ignore[case insensitive dict]
            SearchLocation.MODULES: lambda: check_dict(self._modules),
            SearchLocation.LIPS: lambda: check_dict(self._lips),
            SearchLocation.RIMS: lambda: check_dict(self._rims),
            SearchLocation.TEXTURES_TPA: lambda: check_list(
                self._texturepacks["swpc_tex_tpa.erf"],
            ),
            SearchLocation.TEXTURES_TPB: lambda: check_list(
                self._texturepacks["swpc_tex_tpb.erf"],
            ),
            SearchLocation.TEXTURES_TPC: lambda: check_list(
                self._texturepacks["swpc_tex_tpc.erf"],
            ),
            SearchLocation.TEXTURES_GUI: lambda: check_list(
                self._texturepacks["swpc_tex_gui.erf"],
            ),
            SearchLocation.CHITIN: lambda: check_list(self._chitin),
            SearchLocation.MUSIC: lambda: check_list(self._streammusic),
            SearchLocation.SOUND: lambda: check_list(self._streamsounds),
            SearchLocation.VOICE: lambda: check_list(self._streamwaves),
            SearchLocation.CUSTOM_MODULES: lambda: check_capsules(capsules),
            SearchLocation.CUSTOM_FOLDERS: lambda: check_folders(folders),
        }

        for item in order:
            function_map[item]()

        return locations

    def texture(
        self,
        resname: str,
        order: list[SearchLocation] | None = None,
        *,
        capsules: list[Capsule] | None = None,
        folders: list[CaseAwarePath | str] | None = None,
    ) -> TPC | None:
        """Returns a TPC object loaded from a resource with the specified name. If the specified texture could not be found
        then the method returns None.

        This is a wrapper of the textures() method provided to make searching for a single texture more convenient.

        Texture is search for in the following order:
            1. "folders" parameter.
            2. "capsules" parameter.
            3. Installation override folder.
            4. Normal texture pack.
            5. GUI texture pack.
            6. Installation Chitin.
            7. Installation module files in modules folder.

        Args:
        ----
            resname: The ResRef string.
            order: The ordered list of locations to check.
            capsules: An extra list of capsules to search in.
            folders: An extra list of folders to search in.

        Returns:
        -------
            TPC object or None.
        """
        batch = self.textures([resname], order, capsules=capsules, folders=folders)
        return batch[resname] if batch else None

    def textures(
        self,
        queries: list[str],
        order: list[SearchLocation] | None = None,
        *,
        capsules: list[Capsule] | None = None,
        folders: list[CaseAwarePath | str] | None = None,
    ) -> CaseInsensitiveDict[TPC | None]:
        """Returns a dictionary mapping the items provided in the queries argument to a TPC object if it exists. If the
        texture could not be found then the value is None.

        Args:
        ----
            queries: A list of resources to try locate.
            order: The ordered list of locations to check.
            capsules: An extra list of capsules to search in.
            folders: An extra list of folders to search in.

        Returns:
        -------
            A dictionary mapping case-insensitive strings to TPC objects or None.
        """
        capsules = [] if capsules is None else capsules
        folders = [] if folders is None else folders

        order = (
            order
            if order is not None
            else (
                [
                    SearchLocation.CUSTOM_FOLDERS,
                    SearchLocation.OVERRIDE,
                    SearchLocation.CUSTOM_MODULES,
                    SearchLocation.TEXTURES_TPA,
                    SearchLocation.CHITIN,
                ]
            )
        )

        textures: CaseInsensitiveDict[TPC | None] = CaseInsensitiveDict[Optional[TPC]]()
        texture_types = [ResourceType.TPC, ResourceType.TGA]
        queries = [resname.lower() for resname in queries]

        for resname in queries:
            textures[resname] = None

        def check_dict(values: dict[str, list[FileResource]]):
            for resources in values.values():
                for resource in resources:
                    if resource.resname() in copy(queries) and resource.restype() in texture_types:
                        queries.remove(resource.resname())
                        textures[resource.resname()] = read_tpc(resource.data())

        def check_list(values: list[FileResource]):
            for resource in values:
                if resource.resname() in copy(queries) and resource.restype() in texture_types:
                    queries.remove(resource.resname())
                    textures[resource.resname()] = read_tpc(resource.data())

        def check_capsules(values: list[Capsule]):
            for capsule in values:
                for resname in queries:
                    if capsule.exists(resname, ResourceType.TPC):
                        queries.remove(resname)
                        resource = capsule.resource(resname, ResourceType.TPC)
                        textures[resname] = read_tpc(resource)
                    if capsule.exists(resname, ResourceType.TGA):
                        queries.remove(resname)
                        resource = capsule.resource(resname, ResourceType.TGA)
                        textures[resname] = read_tpc(resource)

        def check_folders(values: list[CaseAwarePath | str]):
            for folder in values:
                c_folder = folder if isinstance(folder, CaseAwarePath) else CaseAwarePath(folder)
                for file in [file for file in c_folder.iterdir() if file.is_file()]:
                    identifier = ResourceIdentifier.from_path(file.name)
                    filepath: CaseAwarePath = CaseAwarePath(c_folder, file)
                    for resname in queries:
                        if identifier.resname == resname and identifier.restype in texture_types:
                            data = BinaryReader.load_file(filepath)
                            textures[resname] = read_tpc(data)

        function_map = {
            SearchLocation.OVERRIDE: lambda: check_dict(self._override),  # type: ignore[case insensitive dict]
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
            SearchLocation.VOICE: lambda: check_list(self._streamwaves),
            SearchLocation.CUSTOM_MODULES: lambda: check_capsules(capsules),
            SearchLocation.CUSTOM_FOLDERS: lambda: check_folders(folders),
        }

        for item in order:
            function_map[item]()

        return textures

    def sound(
        self,
        queries: str,
        order: list[SearchLocation] | None = None,
        *,
        capsules: list[Capsule] | None = None,
        folders: list[str] | None = None,
    ) -> bytes | None:
        """Returns the bytes of a sound resource if it can be found, otherwise returns None.

        This is a wrapper of the sounds() method provided to make searching for a single resource more convenient.

        Args:
        ----
            queries: The name of the resource to look for.
            order: The ordered list of locations to check.
            capsules: An extra list of capsules to search in.
            folders: An extra list of folders to search in.

        Returns:
        -------
            A bytes object or None.
        """
        batch = self.sounds([queries], order, capsules=capsules, folders=folders)
        return batch[queries] if batch else None

    def sounds(
        self,
        resnames: list[str],
        order: list[SearchLocation] | None = None,
        *,
        capsules: list[Capsule] | None = None,
        folders: list[str] | None = None,
    ) -> CaseInsensitiveDict[bytes | None]:
        """Returns a dictionary mapping the items provided in the queries argument to a bytes object if the respective
        sound resource could be found. If the sound could not be found the value will return None.

        Args:
        ----
            resnames: A list of sounds to try locate.
            order: The ordered list of locations to check.
            capsules: An extra list of capsules to search in.
            folders: An extra list of folders to search in.

        Returns:
        -------
            A dictionary mapping a case-insensitive string to a bytes object or None.
        """
        capsules = capsules or []
        folders = folders or []

        order = (
            order
            if order is not None
            else (
                [
                    SearchLocation.CUSTOM_FOLDERS,
                    SearchLocation.OVERRIDE,
                    SearchLocation.CUSTOM_MODULES,
                    SearchLocation.SOUND,
                    SearchLocation.CHITIN,
                ]
            )
        )

        sounds: CaseInsensitiveDict[bytes | None] = CaseInsensitiveDict[Optional[bytes]]()
        texture_types = [ResourceType.WAV, ResourceType.MP3]
        resnames = [resname.lower() for resname in resnames]

        for resname in resnames:
            sounds[resname] = None

        def check_dict(values: dict[str, list[FileResource]]):
            for resources in values.values():
                for resource in resources:
                    if resource.resname() in copy(resnames) and resource.restype() in texture_types:
                        resnames.remove(resource.resname())
                        sounds[resource.resname()] = fix_audio(resource.data())

        def check_list(values: list[FileResource]):
            for resource in values:
                if resource.resname() in copy(resnames) and resource.restype() in texture_types:
                    resnames.remove(resource.resname())
                    sounds[resource.resname()] = fix_audio(resource.data())

        def check_capsules(values: list[Capsule]):
            for capsule in values:
                for resname in resnames:
                    resource = None
                    if capsule.exists(resname, ResourceType.WAV):
                        resnames.remove(resname)
                        resource = capsule.resource(resname, ResourceType.TPC)
                    if capsule.exists(resname, ResourceType.MP3):
                        resnames.remove(resname)
                        resource = capsule.resource(resname, ResourceType.TGA)
                    if resource is not None:
                        sounds[resname] = fix_audio(resource)

        def check_folders(values: list[str] | list[CaseAwarePath]):
            for folder in values:
                filepath: CaseAwarePath = CaseAwarePath(folder)
                for file in [file for file in filepath.iterdir() if file.is_file()]:
                    identifier = ResourceIdentifier.from_path(file.name)
                    for resname in resnames:
                        if identifier.resname == resname and identifier.restype in texture_types:
                            data = BinaryReader.load_file(file)
                            sounds[resname] = fix_audio(data)

        function_map = {
            SearchLocation.OVERRIDE: lambda: check_dict(self._override),  # type: ignore[case insensitive dict]
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
            SearchLocation.VOICE: lambda: check_list(self._streamwaves),
            SearchLocation.CUSTOM_MODULES: lambda: check_capsules(capsules),
            SearchLocation.CUSTOM_FOLDERS: lambda: check_folders(folders),
        }

        for item in order:
            function_map[item]()

        return sounds

    def string(self, locstring: LocalizedString, default: str = "") -> str:
        """Returns the string for the LocalizedString provided.
        This is a wrapper of the strings() method provided to make searching for a single string more convenient.

        Args:
        ----
            locstring:
            default:
        Returns:
        -------.
        """
        batch = self.strings([locstring], default)
        return batch[locstring]

    def strings(
        self,
        queries: list[LocalizedString],
        default: str = "",
    ) -> dict[LocalizedString, str]:
        """Returns a dictionary mapping the items provided in the queries argument to a string.

        As the method iterates through each LocalizedString it will first check if the TalkTable linked to the
        Installation has the stringref. If not it will try fallback on whatever substring exists in the LocalizedString
        and should that fail it will fallback on the default string specified.

        Args:
        ----
            queries: A list of LocalizedStrings.
            default: The fallback string if no string could be found.

        Returns:
        -------
            A dictionary mapping LocalizedString to a string.
        """
        stringrefs = [locstring.stringref for locstring in queries]
        batch = self.talktable().batch(stringrefs)

        results: dict[LocalizedString, str] = {}
        for locstring in queries:
            if locstring.stringref in batch and locstring.stringref != -1:
                results[locstring] = batch[locstring.stringref].text
            elif len(locstring):
                for _language, _gender, text in locstring:
                    results[locstring] = text
                    break
            else:
                results[locstring] = default

        return results

    def module_name(self, module_filename: str, use_hardcoded: bool = True) -> str:
        """Returns the name of the area for a module from the installations module list. The name is taken from the
        LocalizedString "Name" in the relevant module file's ARE resource.

        Args:
        ----
            module_filename: The name of the module file.
            use_hardcoded: Use hardcoded values for modules where applicable.

        Returns:
        -------
            The name of the area for the module.
        """
        root = self._replace_module_extensions(module_filename)
        if use_hardcoded:
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
                "STUNT_51A": "Dodonna Flagship - Cutscene (Bastila Against Us)",
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
                "856NIH": "Ravager - Cutscene (Sion vs. Nihilus)",
            }

            for key, value in hardcoded.items():
                if key.upper() in module_filename.upper():
                    return value

        name: str = ""
        for module in self.modules_list():
            if root not in module:
                continue

            capsule = Capsule(self.module_path() / module)
            tag = ""

            if capsule.exists("module", ResourceType.IFO):
                ifo: GFF = read_gff(capsule.resource("module", ResourceType.IFO))
                tag = ifo.root.get_resref("Mod_Entry_Area").get()
            if capsule.exists(tag, ResourceType.ARE):
                are: GFF = read_gff(capsule.resource(tag, ResourceType.ARE))
                locstring = are.root.get_locstring("Name")
                if locstring.stringref > 0:
                    name = self._talktable.string(locstring.stringref) or ""  # TODO: why did I add 'or ""'?
                elif locstring.exists(Language.ENGLISH, Gender.MALE):
                    name = locstring.get(Language.ENGLISH, Gender.MALE) or ""
                break

        return name

    def module_names(self) -> dict[str, str]:
        """Returns a dictionary mapping module filename to the name of the area. The name is taken from the LocalizedString
        "Name" in the relevant module file's ARE resource.

        Returns
        -------
            A dictionary mapping module filename to in-game module area name.
        """
        return {module: self.module_name(module) for module in self.modules_list()}

    def module_id(self, module_filename: str, use_hardcoded: bool = True) -> str:
        """Returns the ID of the area for a module from the installations module list. The ID is taken from the
        ResRef field "Mod_Entry_Area" in the relevant module file's IFO resource.

        Args:
        ----
            module_filename: The name of the module file.
            use_hardcoded: Use hardcoded values for modules where applicable.

        Returns:
        -------
            The ID of the area for the module.
        """
        root = self._replace_module_extensions(module_filename)
        if use_hardcoded:
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

            for key, value in hardcoded.items():
                if key.upper() in module_filename.upper():
                    return value

        mod_id = ""

        for module in self.modules_list():
            if root not in module:
                continue

            capsule = Capsule(self.module_path() / module)

            if capsule.exists("module", ResourceType.IFO):
                these_bytes = capsule.resource("module", ResourceType.IFO)
                if these_bytes:
                    ifo = read_gff(these_bytes)
                    mod_id = ifo.root.get_resref("Mod_Entry_Area").get()

        return mod_id

    def _replace_module_extensions(self, module_filename: str) -> str:
        result = re.sub(r"\.mod$", "", module_filename, flags=re.IGNORECASE)
        result = re.sub(r"\.erf$", "", result, flags=re.IGNORECASE)
        result = re.sub(r"\.rim$", "", result, flags=re.IGNORECASE)
        result = result[:-2] if result.endswith("_s") else result
        result = result[:-4] if result.endswith("_dlg") else result
        return result  # noqa: RET504

    def module_ids(self) -> dict[str, str]:
        """Returns a dictionary mapping module filename to the ID of the module. The ID is taken from the
        ResRef field "Mod_Entry_Area" in the relevant module file's IFO resource.

        Returns
        -------
            A dictionary mapping module filename to in-game module id.
        """
        return {module: self.module_id(module) for module in self.modules_list()}
