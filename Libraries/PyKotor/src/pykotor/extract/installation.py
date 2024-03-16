from __future__ import annotations

import os
import re

from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from copy import copy
from enum import Enum, IntEnum
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Generator, NamedTuple

from pykotor.common.language import Gender, Language, LocalizedString
from pykotor.common.misc import CaseInsensitiveDict, Game
from pykotor.common.stream import BinaryReader
from pykotor.extract.capsule import Capsule
from pykotor.extract.chitin import Chitin
from pykotor.extract.file import FileResource, LocationResult, ResourceIdentifier, ResourceResult
from pykotor.extract.talktable import TalkTable
from pykotor.resource.formats.erf.erf_data import ERFType
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.formats.gff.gff_data import GFFContent, GFFFieldType, GFFList, GFFStruct
from pykotor.resource.formats.tpc import TPC, read_tpc
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_capsule_file, is_erf_file, is_mod_file, is_rim_file
from pykotor.tools.path import CaseAwarePath
from pykotor.tools.sound import deobfuscate_audio
from utility.error_handling import format_exception_with_variables
from utility.system.path import Path, PurePath

if TYPE_CHECKING:
    from pykotor.extract.talktable import StringResult
    from pykotor.resource.formats.gff import GFF


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
    filepath: Path


class TexturePackNames(Enum):
    """Full list of texturepack ERF filenames for both games."""

    TPA = "swpc_tex_tpa.erf"
    TPB = "swpc_tex_tpb.erf"
    TPC = "swpc_tex_tpc.erf"
    GUI = "swpc_tex_gui.erf"


HARDCODED_MODULE_NAMES: dict[str, str] = {
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


class Installation:  # noqa: PLR0904
    """Installation provides a centralized location for loading resources stored in the game through its various folders and formats."""  # noqa: E501

    TEXTURES_TYPES: ClassVar[list[ResourceType]] = [
        ResourceType.TPC,
        ResourceType.TGA,
        ResourceType.DDS,
    ]

    def __init__(self, path: os.PathLike | str):
        self._path: CaseAwarePath = CaseAwarePath.pathify(path)

        self._talktable: TalkTable = TalkTable(self._path / "dialog.tlk")
        self._female_talktable: TalkTable = TalkTable(self._path / "dialogf.tlk")

        self._modules: dict[str, list[FileResource]] = {}
        self._lips: dict[str, list[FileResource]] = {}
        self._texturepacks: dict[str, list[FileResource]] = {}
        self._rims: dict[str, list[FileResource]] = {}

        self._override: dict[str, list[FileResource]] = {}

        self._chitin: list[FileResource] = []
        self._streammusic: list[FileResource] = []
        self._streamsounds: list[FileResource] = []
        self._streamwaves: list[FileResource] = []
        self._game: Game | None = None

        self._initialized = False
        self.reload_all()

    def reload_all(self):
        self.load_chitin()
        self.load_lips()
        self.load_modules()
        self.load_override()
        if self.game().is_k1():
            self.load_rims()
        self.load_streammusic()
        self.load_streamsounds()
        if self.game().is_k1():
            self.load_streamwaves()
        elif self.game().is_k2():
            self.load_streamvoice()
        self.load_textures()
        print(f"Finished loading the installation from {self._path}")
        self._initialized = True

    def __iter__(self) -> Generator[FileResource, Any, None]:
        if not self._initialized:
            self.reload_all()
        yield from self._chitin
        yield from self._streammusic
        yield from self._streamsounds
        yield from self._streamwaves
        for resources in self._override.values():
            yield from resources
        for resources in self._modules.values():
            yield from resources
        for resources in self._lips.values():
            yield from resources
        for resources in self._texturepacks.values():
            yield from resources
        for resources in self._rims.values():
            yield from resources
        tlk_path = self._path / "dialog.tlk"
        yield FileResource("dialog", ResourceType.TLK, tlk_path.stat().st_size, 0, tlk_path)
        female_tlk_path = self._path / "dialogf.tlk"
        if female_tlk_path.safe_isfile():
            yield FileResource("dialogf", ResourceType.TLK, female_tlk_path.stat().st_size, 0, female_tlk_path)

    # region Get Paths
    def path(self) -> CaseAwarePath:
        """Returns the path to root folder of the Installation.

        Returns:
        -------
            The path to the root folder.
        """
        return self._path

    def module_path(self) -> CaseAwarePath:
        """Returns the path to modules folder of the Installation. This method maintains the case of the foldername.

        Returns:
        -------
            The path to the modules folder.
        """
        return self._find_resource_folderpath("Modules")

    def override_path(self) -> CaseAwarePath:
        """Returns the path to override folder of the Installation. This method maintains the case of the foldername.

        Returns:
        -------
            The path to the override folder.
        """
        return self._find_resource_folderpath("Override", optional=True)

    def lips_path(self) -> CaseAwarePath:
        """Returns the path to 'lips' folder of the Installation. This method maintains the case of the foldername.

        Returns:
        -------
            The path to the lips folder.
        """
        return self._find_resource_folderpath("lips")

    def texturepacks_path(self) -> CaseAwarePath:
        """Returns the path to 'texturepacks' folder of the Installation. This method maintains the case of the foldername.

        Returns:
        -------
            The path to the texturepacks folder.
        """
        return self._find_resource_folderpath("texturepacks", optional=True)

    def rims_path(self) -> CaseAwarePath:
        """Returns the path to 'rims' folder of the Installation. This method maintains the case of the foldername.

        Returns:
        -------
            The path to the rims folder.
        """
        return self._find_resource_folderpath("rims", optional=True)

    def streammusic_path(self) -> CaseAwarePath:
        """Returns the path to 'streammusic' folder of the Installation. This method maintains the case of the foldername.

        Returns:
        -------
            The path to the streammusic folder.
        """
        return self._find_resource_folderpath("streammusic")

    def streamsounds_path(self) -> CaseAwarePath:
        """Returns the path to 'streamsounds' folder of the Installation. This method maintains the case of the foldername.

        Returns:
        -------
            The path to the streamsounds folder.
        """
        return self._find_resource_folderpath("streamsounds", optional=True)

    def streamwaves_path(self) -> CaseAwarePath:
        """Returns the path to 'streamwaves' or 'streamvoice' folder of the Installation. This method maintains the case of the foldername.

        In the first game, this folder is named 'streamwaves'
        In the second game, this folder has been renamed to 'streamvoice'.

        Returns:
        -------
            The path to the streamwaves/streamvoice folder.
        """
        return self._find_resource_folderpath(("streamwaves", "streamvoice"))

    def streamvoice_path(self) -> CaseAwarePath:
        """Returns the path to 'streamvoice' or 'streamwaves' folder of the Installation. This method maintains the case of the foldername.

        In the first game, this folder is named 'streamwaves'
        In the second game, this folder has been renamed to 'streamvoice'.

        Returns:
        -------
            The path to the streamvoice/streamwaves folder.
        """
        return self._find_resource_folderpath(("streamvoice", "streamwaves"))

    def _find_resource_folderpath(
        self,
        folder_names: tuple[str, ...] | str,
        *,
        optional: bool = True,
    ) -> CaseAwarePath:
        """Finds the path to a resource folder.

        Args:
        ----
            folder_names: The name(s) of the folder(s) to search for.
            optional: Whether to raise an error if the folder is not found.

        Returns:
        -------
            CaseAwarePath: The path to the found folder.

        Processing Logic:
        ----------------
            - Iterates through the provided folder names
            - Joins each name to the base path to check if the folder exists
            - Returns the first existing path
            - Raises FileNotFoundError if no path is found and optional is False.
        """
        try:
            if isinstance(folder_names, str):  # make a tuple
                folder_names = (folder_names,)
            for folder_name in folder_names:
                resource_path: CaseAwarePath = self._path / folder_name
                if resource_path.safe_isdir():
                    return resource_path
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            msg = f"An error occurred while finding the '{' or '.join(folder_names)}' folder in '{self._path}'."
            raise OSError(msg) from e
        else:
            if optional:
                return CaseAwarePath(self._path, folder_names[0])
        msg = f"Could not find the '{' or '.join(folder_names)}' folder in '{self._path}'."
        raise FileNotFoundError(msg)

    # endregion

    # region Load Data
    def load_single_resource(
        self,
        filepath: Path | CaseAwarePath,
        capsule_check: Callable | None = None,
    ) -> tuple[Path, list[FileResource] | FileResource | None]:
        # sourcery skip: extract-method
        try:
            if capsule_check:
                if not capsule_check(filepath):
                    return filepath, None
                return filepath, list(Capsule(filepath))

            resname: str
            restype: ResourceType
            resname, restype = ResourceIdentifier.from_path(filepath).unpack()
            if restype.is_invalid:
                return filepath, None

            return filepath, FileResource(
                resname,
                restype,
                filepath.stat().st_size,
                offset=0,
                filepath=filepath,
            )
        except Exception as e:  # noqa: BLE001
            with Path("errorlog.txt").open("a", encoding="utf-8") as f:
                f.write(format_exception_with_variables(e))
        return filepath, None

    def load_resources(
        self,
        path: CaseAwarePath,
        capsule_check: Callable | None = None,
        *,
        recurse: bool = False,
    ) -> dict[str, list[FileResource]] | list[FileResource]:
        """Load resources for a given path and store them in a new list/dict.

        Args:
        ----
            path (os.PathLike | str): path for lookup.
            recurse (bool): whether to recurse into subfolders (default is False)
            capsule_check (Callable returns bool or None): Determines whether to use a resource dict or resource list. If the check doesn't pass, the resource isn't added.

        Returns:
        -------
            list[FileResource]: The list where resources at the path have been stored.
             or
            dict[str, list[FileResource]]: A dict keyed by filename to the encapsulated resources
        """
        resources: dict[str, list[FileResource]] | list[FileResource] = {} if capsule_check else []

        r_path = Path(path)
        if not r_path.safe_isdir():
            print(f"The '{r_path.name}' folder did not exist when loading the installation at '{self._path}', skipping...")
            return resources

        print(f"Loading {r_path.relative_to(self._path)}...")
        files_iter = (
            path.safe_rglob("*")
            if recurse
            else path.safe_iterdir()
        )

        # Determine number of workers dynamically based on available CPUs
        num_cores = os.cpu_count() or 1  # Ensure at least one core is returned
        max_workers = num_cores * 4  # Use 4x the number of cores
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit tasks to the executor
            futures = [
                executor.submit(self.load_single_resource, file, capsule_check)
                for file in files_iter
            ]

            # Gather resources and omit `None` values (errors or skips)
            if isinstance(resources, dict):
                for f in futures:
                    filepath, resource = f.result()
                    if resource is None:
                        continue
                    if not isinstance(resource, list):
                        continue
                    resources[filepath.name] = resource
            else:
                for f in futures:
                    filepath, resource = f.result()
                    if resource is None:
                        continue
                    if isinstance(resource, FileResource):
                        resources.append(resource)

        if not resources:
            print(f"No resources found at '{r_path}' when loading the installation, skipping...")
        return resources

    def load_chitin(self):
        """Reloads the list of resources in the Chitin linked to the Installation."""
        chitin_path: CaseAwarePath = self._path / "chitin.key"
        chitin_exists: bool | None = chitin_path.safe_isfile()
        if chitin_exists:
            print(f"Loading BIFs from chitin.key at '{self._path}'...")
            self._chitin = list(Chitin(key_path=chitin_path))
            print("Done loading chitin")
        elif chitin_exists is False:
            print(f"The chitin.key file did not exist at '{self._path}' when loading the installation, skipping...")
        elif chitin_exists is None:
            print(f"No permissions to the chitin.key file at '{self._path}' when loading the installation, skipping...")

    def load_lips(
        self,
    ):
        """Reloads the list of modules in the lips folder linked to the Installation."""
        self._lips = self.load_resources(self.lips_path(), capsule_check=is_mod_file)  # type: ignore[assignment]

    def load_modules(self):
        """Reloads the list of modules files in the modules folder linked to the Installation."""
        self._modules = self.load_resources(self.module_path(), capsule_check=is_capsule_file)  # type: ignore[assignment]

    def reload_module(self, module: str):
        """Reloads the list of resources in specified module in the modules folder linked to the Installation.

        Args:
        ----
            module: The filename of the module, including the extension.
        """
        if not self._modules or module not in self._modules:
            self.load_modules()
        self._modules[module] = list(Capsule(self.module_path() / module))

    def load_rims(
        self,
    ):
        """Reloads the list of module files in the rims folder linked to the Installation."""
        self._rims = self.load_resources(self.rims_path(), capsule_check=is_rim_file)  # type: ignore[assignment]

    def load_textures(
        self,
    ):
        """Reloads the list of modules files in the texturepacks folder linked to the Installation."""
        self._texturepacks = self.load_resources(self.texturepacks_path(), capsule_check=is_erf_file)  # type: ignore[assignment]

    def load_override(self, directory: str | None = None):
        """Loads the list of resources in a specific subdirectory of the override folder linked to the Installation.

        If a directory argument is not passed, this will reload all subdirectories in the Override folder.
        If directory argument is ".", this will load all the loose files in the Override folder.

        the _override dict follows the following example format:
        _override["."] = list[FileResource]  # the loose files in the Override folder
        _override["subdir1"] = list[FileResource]  # the loose files in subdir1
        _override["subdir2"] = list[FileResource]  # the loose files in subdir2
        _override["subdir1/subdir3"] = list[FileResource]  # the loose files in subdir1/subdir3. Key is always a posix path (delimited by /'s)

        Args:
        ----
            directory: The relative path of a subfolder to the override folder.
        """
        override_path: CaseAwarePath = self.override_path()
        target_dirs: list[CaseAwarePath]
        if directory:
            target_dirs = [override_path / directory]
            self._override[directory] = []
        else:
            target_dirs = [f for f in override_path.safe_rglob("*") if f.safe_isdir()]
            target_dirs.append(override_path)
            self._override = {}

        for folder in target_dirs:
            relative_folder: str = folder.relative_to(override_path).as_posix()  # '.' if folder is the same as override_path
            self._override[relative_folder] = self.load_resources(folder)  # type: ignore[assignment]

    def reload_override(
        self,
        directory: str,
    ):
        """Reload the resources in the specified override subdirectory.

        Args:
        ----
            directory: Path to directory containing override configuration

        Processing Logic:
        ----------------
            - Load override configuration from given directory
            - Override any existing resources with new ones from directory
        """
        self.load_override(directory)

    def reload_override_file(
        self,
        file: os.PathLike | str,
    ):
        filepath: Path = Path.pathify(file)
        parent_folder = filepath.parent
        rel_folderpath: str = str(parent_folder.relative_to(self.override_path())) if parent_folder.name else "."
        if rel_folderpath not in self._override:
            self.load_override(rel_folderpath)

        identifier: ResourceIdentifier = ResourceIdentifier.from_path(filepath)
        if identifier.restype == ResourceType.INVALID:
            print("Cannot reload override file. Invalid KOTOR resource:", identifier)
            return
        resource = FileResource(
            *identifier,
            filepath.stat().st_size,
            0,
            filepath,
        )

        override_list: list[FileResource] = self._override[rel_folderpath]
        if resource not in override_list:
            override_list.append(resource)
        else:
            override_list[override_list.index(resource)] = resource

    def load_streammusic(
        self,
    ):
        """Reloads the list of resources in the streammusic folder linked to the Installation."""
        self._streammusic = self.load_resources(self.streammusic_path())  # type: ignore[assignment]

    def load_streamsounds(
        self,
    ):
        """Reloads the list of resources in the streamsounds folder linked to the Installation."""
        self._streamsounds = self.load_resources(self.streamsounds_path())  # type: ignore[assignment]

    def load_streamwaves(
        self,
    ):
        """Reloads the list of resources in the streamwaves folder linked to the Installation."""
        self._streamwaves = self.load_resources(self._find_resource_folderpath(("streamwaves", "streamvoice")), recurse=True)  # type: ignore[assignment]

    def load_streamvoice(
        self,
    ):
        """Reloads the list of resources in the streamvoice folder linked to the Installation."""
        self._streamwaves = self.load_resources(self._find_resource_folderpath(("streamvoice", "streamwaves")), recurse=True)  # type: ignore[assignment]

    # endregion

    # region Get FileResources
    def chitin_resources(self) -> list[FileResource]:
        """Returns a shallow copy of the list of FileResources stored in the Chitin linked to the Installation.

        Returns:
        -------
            A list of FileResources.
        """
        return self._chitin[:]

    def modules_list(self) -> list[str]:
        """Returns the list of module filenames located in the modules folder linked to the Installation.

        Module filenames are cached and require to be refreshed after a file is added, deleted or renamed.

        Returns:
        -------
            A list of filenames.
        """
        return list(self._modules.keys())

    def module_resources(
        self,
        filename: str,
    ) -> list[FileResource]:
        """Returns a a shallow copy of the list of FileResources stored in the specified module file located in the modules folder linked to the Installation.

        Module resources are cached and require a reload after the contents have been modified on disk.

        Returns:
        -------
            A list of FileResources.
        """
        return self._modules[filename][:]

    def lips_list(self) -> list[str]:
        """Returns the list of module filenames located in the lips folder linked to the Installation.

        Module filenames are cached and require to be refreshed after a file is added, deleted or renamed.

        Returns:
        -------
            A list of filenames.
        """
        return list(self._lips.keys())

    def lip_resources(
        self,
        filename: str,
    ) -> list[FileResource]:
        """Returns a shallow copy of the list of FileResources stored in the specified module file located in the lips folder linked to the Installation.

        Module resources are cached and require a reload after the contents have been modified on disk.

        Returns:
        -------
            A list of FileResources.
        """
        return self._lips[filename][:]

    def texturepacks_list(self) -> list[str]:
        """Returns the list of texture-pack filenames located in the texturepacks folder linked to the Installation.

        Returns:
        -------
            A list of filenames.
        """
        return list(self._texturepacks.keys())

    def texturepack_resources(
        self,
        filename: str,
    ) -> list[FileResource]:
        """Returns a shallow copy of the list of FileResources stored in the specified module file located in the texturepacks folder linked to the Installation.

        Texturepack resources are cached and require a reload after the contents have been modified on disk.

        Returns:
        -------
            A list of FileResources from the 'texturepacks' folder of the Installation.
        """
        return self._texturepacks[filename][:]

    def override_list(self) -> list[str]:
        """Returns the list of subdirectories located in override folder linked to the Installation.

        Subdirectories are cached and require a refresh after a folder is added, deleted or renamed.

        Returns:
        -------
            A list of subfolder names in Override.
        """
        return list(self._override.keys())

    def override_resources(
        self,
        directory: str | None = None,
    ) -> list[FileResource]:
        """Returns a list of FileResources stored in the specified subdirectory located in the 'override' folder linked to the Installation.

        Override resources are cached and require a reload after the contents have been modified on disk.

        Returns:
        -------
            A list of FileResources.
        """
        if not self._override or directory and directory not in self._override:
            self.load_override()

        return (
            self._override[directory]
            if directory
            else [override_resource for ov_subfolder_name in self._override for override_resource in self._override[ov_subfolder_name]]
        )

    # endregion

    @staticmethod
    def determine_game(path: os.PathLike | str) -> Game | None:
        """Determines the game based on files and folders.

        Args:
        ----
            path: Path to game directory

        Returns:
        -------
            Game: Game enum or None

        Processing Logic:
        ----------------
            1. Normalize the path and check for existence of game files
            2. Define checks for each game
            3. Run checks and score games
            4. Return game with highest score or None if scores are equal or all checks fail
        """
        r_path: CaseAwarePath = CaseAwarePath.pathify(path)

        def check(x) -> bool:
            c_path: CaseAwarePath = r_path.joinpath(x)
            return c_path.safe_exists() is not False

        # Checks for each game
        game1_pc_checks: list[bool] = [
            check("streamwaves"),
            check("swkotor.exe"),
            check("swkotor.ini"),
            check("rims"),
            check("utils"),
            check("32370_install.vdf"),
            check("miles/mssds3d.m3d"),
            check("miles/msssoft.m3d"),
            check("data/party.bif"),
            check("data/player.bif"),
            check("modules/global.mod"),
            check("modules/legal.mod"),
            check("modules/mainmenu.mod"),
        ]

        game1_xbox_checks: list[bool] = [  # TODO:

        ]

        game1_ios_checks: list[bool] = [
            check("override/ios_action_bg.tga"),
            check("override/ios_action_bg2.tga"),
            check("override/ios_action_x.tga"),
            check("override/ios_action_x2.tga"),
            check("override/ios_button_a.tga"),
            check("override/ios_button_x.tga"),
            check("override/ios_button_y.tga"),
            check("override/ios_edit_box.tga"),
            check("override/ios_enemy_plus.tga"),
            check("override/ios_gpad_bg.tga"),
            check("override/ios_gpad_gen.tga"),
            check("override/ios_gpad_gen2.tga"),
            check("override/ios_gpad_help.tga"),
            check("override/ios_gpad_help2.tga"),
            check("override/ios_gpad_map.tga"),
            check("override/ios_gpad_map2.tga"),
            check("override/ios_gpad_save.tga"),
            check("override/ios_gpad_save2.tga"),
            check("override/ios_gpad_solo.tga"),
            check("override/ios_gpad_solo2.tga"),
            check("override/ios_gpad_solox.tga"),
            check("override/ios_gpad_solox2.tga"),
            check("override/ios_gpad_ste.tga"),
            check("override/ios_gpad_ste2.tga"),
            check("override/ios_gpad_ste3.tga"),
            check("override/ios_help.tga"),
            check("override/ios_help2.tga"),
            check("override/ios_help_1.tga"),
            check("KOTOR"),
            check("KOTOR.entitlements"),
            check("kotorios-Info.plist"),
            check("AppIcon29x29.png"),
            check("AppIcon50x50@2x~ipad.png"),
            check("AppIcon50x50~ipad.png"),
        ]

        game1_android_checks: list[bool] = [  # TODO:

        ]

        game2_pc_checks: list[bool] = [
            check("streamvoice"),
            check("swkotor2.exe"),
            check("swkotor2.ini"),
            check("LocalVault"),
            check("LocalVault/test.bic"),
            check("LocalVault/testold.bic"),
            check("miles/binkawin.asi"),
            check("miles/mssds3d.flt"),
            check("miles/mssdolby.flt"),
            check("miles/mssogg.asi"),
            check("data/Dialogs.bif"),
        ]

        game2_xbox_checks: list[bool] = [  # TODO:

        ]

        game2_ios_checks: list[bool] = [
            check("override/ios_mfi_deu.tga"),
            check("override/ios_mfi_eng.tga"),
            check("override/ios_mfi_esp.tga"),
            check("override/ios_mfi_fre.tga"),
            check("override/ios_mfi_ita.tga"),
            check("override/ios_self_box_r.tga"),
            check("override/ios_self_expand2.tga"),
            check("override/ipho_forfeit.tga"),
            check("override/ipho_forfeit2.tga"),
            check("override/kotor2logon.tga"),
            check("override/lbl_miscroll_open_f.tga"),
            check("override/lbl_miscroll_open_f2.tga"),
            check("override/ydialog.gui"),
            check("KOTOR II"),
            check("KOTOR2-Icon-20-Apple.png"),
            check("KOTOR2-Icon-29-Apple.png"),
            check("KOTOR2-Icon-40-Apple.png"),
            check("KOTOR2-Icon-58-apple.png"),
            check("KOTOR2-Icon-60-apple.png"),
            check("KOTOR2-Icon-76-apple.png"),
            check("KOTOR2-Icon-80-apple.png"),
            check("KOTOR2_LaunchScreen.storyboardc"),
            check("KOTOR2_LaunchScreen.storyboardc/Info.plist"),
            check("GoogleService-Info.plist"),
        ]

        game2_android_checks: list[bool] = [  # TODO:

        ]

        # Determine the game with the most checks passed
        def determine_highest_scoring_game() -> Game | None:
            # Scoring for each game and platform
            scores: dict[Game, int] = {
                Game.K1: sum(game1_pc_checks),
                Game.K2: sum(game2_pc_checks),
                Game.K1_XBOX: sum(game1_xbox_checks),
                Game.K2_XBOX: sum(game2_xbox_checks),
                Game.K1_IOS: sum(game1_ios_checks),
                Game.K2_IOS: sum(game2_ios_checks),
                Game.K1_ANDROID: sum(game1_android_checks),
                Game.K2_ANDROID: sum(game2_android_checks),
            }

            highest_scoring_game: Game | None = None
            highest_score: int = 0

            for game, score in scores.items():
                if score > highest_score:
                    highest_score = score
                    highest_scoring_game = game

            return highest_scoring_game

        return determine_highest_scoring_game()

    def game(self) -> Game:
        """Determines the game (K1 or K2) for the given Installation.

        Args:
        ----
            self: The Installation instance

        Returns:
        -------
            Game: The determined Game object

        Processing Logic:
        ----------------
            - Check if game is already determined and stored in _game
            - Determine the game by calling determine_game() method with path
            - If game is determined, store it in _game and return
            - If game is not determined, raise ValueError with message.
        """
        if self._game is not None:
            return self._game

        game: Game | None = self.determine_game(self._path)
        if game is not None:
            self._game = game
            return game

        msg = "Could not determine the KOTOR game version! Did you select the right installation folder?"
        raise ValueError(msg)

    def talktable(self) -> TalkTable:
        """Returns the TalkTable linked to the Installation.

        Returns:
        -------
            A TalkTable object.
        """
        return self._talktable

    def female_talktable(self) -> TalkTable:
        """Returns the female TalkTable linked to the Installation. This is 'dialogf.tlk' in the Polish version of K1.

        Returns:
        -------
            A TalkTable object.
        """
        return self._female_talktable

    def resource(  # noqa: PLR0913
        self,
        resname: str,
        restype: ResourceType,
        order: list[SearchLocation] | None = None,
        *,
        capsules: list[Capsule] | None = None,
        folders: list[Path] | None = None,
    ) -> ResourceResult | None:
        """Returns a resource matching the specified resref and restype.

        This is a wrapper of the resources() method provided to make fetching for a single resource more convenient.
        If no resource is found then None is returned instead.

        The default search order is (descending priority): 1. Folders in the folders parameter, 2. Override folders,
        3. Capsules in the capsules parameter, 4. Game modules, 5. Chitin.

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
        search: ResourceResult | None = batch[query]
        if not search or not search.data:
            print(f"Could not find '{query}' during resource lookup.")
            return None
        return search

    def resources(
        self,
        queries: list[ResourceIdentifier] | set[ResourceIdentifier],
        order: list[SearchLocation] | None = None,
        *,
        capsules: list[Capsule] | None = None,
        folders: list[Path] | None = None,
    ) -> dict[ResourceIdentifier, ResourceResult | None]:
        """Returns a dictionary mapping the items provided in the queries argument to the resource data if it was found.

        If the resource was not found, the value will be None.
        Unlike self.locations(), this function will only return the first found result for each query, instead of everywhere the resource can be located.

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
            location_list: list[LocationResult] = locations.get(query, [])

            if not location_list:
                print(f"Resource not found: '{query}'")
                results[query] = None
                continue

            location: LocationResult = location_list[0]

            if query not in handles:
                handles[query] = BinaryReader.from_file(location.filepath)

            handle: BinaryReader = handles[query]
            handle.seek(location.offset)
            data: bytes = handle.read_bytes(location.size)

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
        folders: list[Path] | None = None,
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
            A list of LocationResult objects where the matching resources can be found.

        Processing Logic:
        ----------------
            - Constructs a query from the resource name and type
            - Searches locations based on the order, capsules and folders
            - Returns the matching locations for the given resource from the results
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
        queries: list[ResourceIdentifier] | set[ResourceIdentifier],
        order: list[SearchLocation] | None = None,
        *,
        capsules: list[Capsule] | None = None,
        folders: list[Path] | None = None,
    ) -> dict[ResourceIdentifier, list[LocationResult]]:
        """Returns a dictionary mapping the items provided in the queries argument to a list of locations for that respective resource.

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
        if order is None:
            order = [
                SearchLocation.CUSTOM_FOLDERS,
                SearchLocation.OVERRIDE,
                SearchLocation.CUSTOM_MODULES,
                SearchLocation.MODULES,
                SearchLocation.CHITIN,
            ]
        queries = set(queries)
        capsules = [] if capsules is None else capsules
        folders = [] if folders is None else folders

        locations: dict[ResourceIdentifier, list[LocationResult]] = {}
        for qident in queries:
            locations[qident] = []

        def check_dict(resource_dict: dict[str, list[FileResource]] | CaseInsensitiveDict[list[FileResource]]):
            for resource_list in resource_dict.values():
                check_list(resource_list)

        def check_list(resource_list: list[FileResource]):
            # Index resources by identifier
            resource_dict: dict[ResourceIdentifier, FileResource] = {resource.identifier(): resource for resource in resource_list}
            for query in queries:
                resource: FileResource | None = resource_dict.get(query)
                if resource is not None:
                    location = LocationResult(
                        resource.filepath(),
                        resource.offset(),
                        resource.size(),
                    )
                    locations[query].append(location)

        def check_capsules(values: list[Capsule]):
            for capsule in values:
                for query in queries:
                    resource: FileResource | None = capsule.info(*query)
                    if resource is None:
                        continue

                    location = LocationResult(
                        resource.filepath(),
                        resource.offset(),
                        resource.size(),
                    )
                    locations[resource.identifier()].append(location)

        def check_folders(resource_folders: list[Path]):
            for folder in resource_folders:
                for file in folder.safe_rglob("*"):
                    if not file.safe_isfile():
                        continue
                    identifier = ResourceIdentifier.from_path(file)
                    if identifier not in queries:
                        continue

                    location = LocationResult(
                        filepath=file,
                        offset=0,
                        size=file.stat().st_size,
                    )
                    locations[identifier].append(location)

        function_map: dict[SearchLocation, Callable] = {
            SearchLocation.OVERRIDE: lambda: check_dict(self._override),
            SearchLocation.MODULES: lambda: check_dict(self._modules),
            SearchLocation.LIPS: lambda: check_dict(self._lips),
            SearchLocation.RIMS: lambda: check_dict(self._rims),
            SearchLocation.TEXTURES_TPA: lambda: check_list(self._texturepacks[TexturePackNames.TPA.value]),
            SearchLocation.TEXTURES_TPB: lambda: check_list(self._texturepacks[TexturePackNames.TPB.value]),
            SearchLocation.TEXTURES_TPC: lambda: check_list(self._texturepacks[TexturePackNames.TPC.value]),
            SearchLocation.TEXTURES_GUI: lambda: check_list(self._texturepacks[TexturePackNames.GUI.value]),
            SearchLocation.CHITIN: lambda: check_list(self._chitin),
            SearchLocation.MUSIC: lambda: check_list(self._streammusic),
            SearchLocation.SOUND: lambda: check_list(self._streamsounds),
            SearchLocation.VOICE: lambda: check_list(self._streamwaves),
            SearchLocation.CUSTOM_MODULES: lambda: check_capsules(capsules),  # type: ignore[arg-type]
            SearchLocation.CUSTOM_FOLDERS: lambda: check_folders(folders),  # type: ignore[arg-type]
        }

        for item in order:
            assert isinstance(item, SearchLocation)
            function_map.get(item, lambda: None)()

        return locations

    def texture(
        self,
        resname: str,
        order: list[SearchLocation] | None = None,
        *,
        capsules: list[Capsule] | None = None,
        folders: list[Path] | None = None,
    ) -> TPC | None:
        """Returns a TPC object loaded from a resource with the specified name.

        This is a wrapper of the textures() method provided to make searching for a single texture more convenient.

        If the specified texture could not be found then the method returns None.

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
            resname: The ResRef string, case-insensitive.
            order: The ordered list of locations to check.
            capsules: An extra list of capsules to search in.
            folders: An extra list of folders to search in.

        Returns:
        -------
            TPC object or None.
        """
        batch: CaseInsensitiveDict[TPC | None] = self.textures([resname], order, capsules=capsules, folders=folders)
        return batch[resname] if batch else None

    def textures(
        self,
        resnames: list[str],
        order: list[SearchLocation] | None = None,
        *,
        capsules: list[Capsule] | None = None,
        folders: list[Path] | None = None,
    ) -> CaseInsensitiveDict[TPC | None]:
        """Returns a dictionary mapping the items provided in the queries argument to a TPC object if it exists.

        If the texture could not be found then the value is None.

        Args:
        ----
            resnames: A list of case-insensitive resource names (without the extensions) to try locate.
            order: The ordered list of locations to check.
            capsules: An extra list of capsules to search in.
            folders: An extra list of folders to search in.

        Returns:
        -------
            A dictionary mapping case-insensitive strings to TPC objects or None.
        """
        if order is None:
            order = [
                SearchLocation.CUSTOM_FOLDERS,
                SearchLocation.OVERRIDE,
                SearchLocation.CUSTOM_MODULES,
                SearchLocation.TEXTURES_TPA,
                SearchLocation.CHITIN,
            ]
        case_resnames: list[str] = [resname.lower() for resname in resnames]
        capsules = [] if capsules is None else capsules
        folders = [] if folders is None else folders

        textures: CaseInsensitiveDict[TPC | None] = CaseInsensitiveDict()
        texture_types: list[ResourceType] = [ResourceType.TPC, ResourceType.TGA]

        for resname in resnames:
            textures[resname] = None

        def decode_txi(txi_bytes: bytes):
            return txi_bytes.decode("ascii", errors="ignore")

        def get_txi_from_list(resname: str, resource_list: list[FileResource]) -> str:
            txi_resource: FileResource | None = next(
                (
                    resource
                    for resource in resource_list
                    if resource.resname() == resname and resource.restype() == ResourceType.TXI
                ),
                None,
            )
            return decode_txi(txi_resource.data()) if txi_resource is not None else ""

        def check_dict(values: dict[str, list[FileResource]]):
            for resources in values.values():
                check_list(resources)

        def check_list(resource_list: list[FileResource]):
            for resource in resource_list:
                case_resname = resource.resname().casefold()
                if case_resname in case_resnames and resource.restype() in texture_types:
                    case_resnames.remove(case_resname)
                    tpc: TPC = read_tpc(resource.data())
                    if resource.restype() == ResourceType.TGA:
                        tpc.txi = get_txi_from_list(case_resname, resource_list)
                    textures[case_resname] = tpc

        def check_capsules(values: list[Capsule]):  # NOTE: This function does not support txi's in the Override folder.
            for capsule in values:
                for case_resname in copy(case_resnames):
                    texture_data: bytes | None = None
                    tformat: ResourceType | None = None
                    for tformat in texture_types:
                        texture_data = capsule.resource(case_resname, tformat)
                        if texture_data is not None:
                            break
                    if texture_data is None:
                        continue

                    case_resnames.remove(case_resname)
                    tpc: TPC = read_tpc(texture_data) if texture_data else TPC()
                    if tformat == ResourceType.TGA:
                        tpc.txi = get_txi_from_list(case_resname, capsule.resources())
                    textures[case_resname] = tpc

        def check_folders(resource_folders: list[Path]):
            queried_texture_files: set[Path] = set()
            for folder in resource_folders:
                queried_texture_files.update(
                    file
                    for file in folder.safe_rglob("*")
                    if (
                        file.stem.casefold() in case_resnames
                        and ResourceType.from_extension(file.suffix) in texture_types
                        and file.safe_isfile()
                    )
                )
            for texture_file in queried_texture_files:
                case_resnames.remove(texture_file.stem.casefold())
                texture_data: bytes = BinaryReader.load_file(texture_file)
                tpc = read_tpc(texture_data) if texture_data else TPC()
                txi_file = CaseAwarePath(texture_file.with_suffix(".txi"))
                if txi_file.exists():
                    txi_data: bytes = BinaryReader.load_file(txi_file)
                    tpc.txi = decode_txi(txi_data)
                textures[texture_file.stem] = tpc

        function_map: dict[SearchLocation, Callable] = {
            SearchLocation.OVERRIDE: lambda: check_dict(self._override),
            SearchLocation.MODULES: lambda: check_dict(self._modules),
            SearchLocation.RIMS: lambda: check_dict(self._rims),
            SearchLocation.TEXTURES_TPA: lambda: check_list(self._texturepacks[TexturePackNames.TPA.value]),
            SearchLocation.TEXTURES_TPB: lambda: check_list(self._texturepacks[TexturePackNames.TPB.value]),
            SearchLocation.TEXTURES_TPC: lambda: check_list(self._texturepacks[TexturePackNames.TPC.value]),
            SearchLocation.TEXTURES_GUI: lambda: check_list(self._texturepacks[TexturePackNames.GUI.value]),
            SearchLocation.CHITIN: lambda: check_list(self._chitin),
            SearchLocation.CUSTOM_MODULES: lambda: check_capsules(capsules),
            SearchLocation.CUSTOM_FOLDERS: lambda: check_folders(folders),
        }

        for item in order:
            assert isinstance(item, SearchLocation)
            function_map.get(item, lambda: None)()

        return textures

    def find_tlk_entry_references(
        self,
        query_stringref: int,
        order: list[SearchLocation] | None = None,
        *,
        capsules: list[Capsule] | None = None,
        folders: list[Path] | None = None,
    ) -> set[FileResource]:  # TODO: 2da's have 'strref' columns that we should parse.
        """Finds all gffs that utilize this stringref in their localizedstring.

        If no gffs could not be found the value will return None.

        Args:
        ----
            stringref: A number representing the locstring to find.
            order: The ordered list of locations to check.
            capsules: An extra list of capsules to search in.
            folders: An extra list of folders to search in.

        Returns:
        -------
            A set of FileResources.
        """
        capsules = [] if capsules is None else capsules
        folders = [] if folders is None else folders
        if order is None:
            order = [
                SearchLocation.CUSTOM_FOLDERS,
                SearchLocation.OVERRIDE,
                SearchLocation.CUSTOM_MODULES,
                SearchLocation.CHITIN,
                SearchLocation.RIMS,
                SearchLocation.MODULES,
            ]

        gffs: set[FileResource] = set()
        gff_extensions: set[str] = GFFContent.get_extensions()

        def recurse_gff_lists(gff_list: GFFList) -> bool:
            for gff_struct in gff_list:
                result = recurse_gff_structs(gff_struct)
                if result:
                    return True
            return False

        def recurse_gff_structs(gff_struct: GFFStruct) -> bool:
            for _label, ftype, fval in gff_struct:
                if ftype == GFFFieldType.List and isinstance(fval, GFFList):
                    result = recurse_gff_lists(fval)
                    if result:
                        return True
                if ftype == GFFFieldType.Struct and isinstance(fval, GFFStruct):
                    result = recurse_gff_structs(fval)
                    if result:
                        return True
                if ftype != GFFFieldType.LocalizedString or not isinstance(fval, LocalizedString):
                    continue
                if fval.stringref == query_stringref:
                    return True
            return False

        def try_get_gff(gff_data: bytes) -> GFF | None:
            with suppress(OSError, ValueError):
                return read_gff(gff_data)
            return None

        def check_dict(resource_dict: dict[str, list[FileResource]]):
            for resources in resource_dict.values():
                check_list(resources)

        def check_list(resource_list: list[FileResource]):
            for resource in resource_list:
                this_restype: ResourceType = resource.restype()
                if this_restype.extension not in gff_extensions:
                    continue
                valid_gff: GFF | None = try_get_gff(resource.data())
                if not valid_gff:
                    continue
                if not recurse_gff_structs(valid_gff.root):
                    continue
                gffs.add(resource)

        def check_capsules(capsules_list: list[Capsule]):
            for capsule in capsules_list:
                for resource in capsule.resources():
                    if resource.restype().extension not in gff_extensions:
                        continue
                    valid_gff: GFF | None = try_get_gff(resource.data())
                    if not valid_gff:
                        continue
                    if not recurse_gff_structs(valid_gff.root):
                        continue
                    gffs.add(resource)

        def check_folders(values: list[Path]):
            gff_files: set[Path] = set()
            for folder in values:  # Having two loops makes it easier to filter out irrelevant files when stepping through the 2nd
                gff_files.update(
                    file
                    for file in folder.safe_rglob("*")
                    if (
                        file.suffix
                        and file.suffix[1:].casefold() in gff_extensions
                        and file.safe_isfile()
                    )
                )
            for gff_file in gff_files:
                gff_data = BinaryReader.load_file(gff_file)
                valid_gff: GFF | None = None
                restype: ResourceType | None = None
                with suppress(ValueError, OSError):
                    valid_gff = read_gff(gff_data)
                    restype = ResourceType.from_extension(gff_file.suffix).validate()
                if not valid_gff or not restype:
                    continue
                if not recurse_gff_structs(valid_gff.root):
                    continue
                fileres = FileResource(
                    resname=gff_file.stem,
                    restype=restype,
                    size=gff_file.stat().st_size,
                    offset=0,
                    filepath=gff_file
                )
                gffs.add(fileres)

        function_map: dict[SearchLocation, Callable] = {
            SearchLocation.OVERRIDE: lambda: check_dict(self._override),
            SearchLocation.MODULES: lambda: check_dict(self._modules),
            SearchLocation.RIMS: lambda: check_dict(self._rims),
            SearchLocation.CHITIN: lambda: check_list(self._chitin),
            SearchLocation.CUSTOM_MODULES: lambda: check_capsules(capsules),
            SearchLocation.CUSTOM_FOLDERS: lambda: check_folders(folders),  # type: ignore[arg-type]
        }

        for item in order:
            assert isinstance(item, SearchLocation)
            function_map.get(item, lambda: None)()

        return gffs

    def sound(
        self,
        resname: str,
        order: list[SearchLocation] | None = None,
        *,
        capsules: list[Capsule] | None = None,
        folders: list[Path] | None = None,
    ) -> bytes | None:
        """Returns the bytes of a sound resource if it can be found, otherwise returns None.

        This is a wrapper of the sounds() method provided to make searching for a single resource more convenient.

        Args:
        ----
            resname: The case-insensitive name of the sound (without the extension) to look for.
            order: The ordered list of locations to check.
            capsules: An extra list of capsules to search in.
            folders: An extra list of folders to search in.

        Returns:
        -------
            A bytes object or None.
        """
        batch: CaseInsensitiveDict[bytes | None] = self.sounds([resname], order, capsules=capsules, folders=folders)
        return batch[resname] if batch else None

    def sounds(
        self,
        resnames: list[str],
        order: list[SearchLocation] | None = None,
        *,
        capsules: list[Capsule] | None = None,
        folders: list[Path] | None = None,
    ) -> CaseInsensitiveDict[bytes | None]:
        """Returns a dictionary mapping the items provided in the resnames argument to a bytes object if the respective sound resource could be found.

        If the sound could not be found the value will return None.

        Args:
        ----
            resnames: A list of case-insensitive sound names (without the extensions) to try locate.
            order: The ordered list of locations to check.
            capsules: An extra list of capsules to search in.
            folders: An extra list of folders to search in.

        Returns:
        -------
            A dictionary mapping a case-insensitive string to a bytes object or None.
        """
        case_resnames: list[str] = [resname.casefold() for resname in resnames]
        capsules = [] if capsules is None else capsules
        folders = [] if folders is None else folders
        if order is None:
            order = [
                SearchLocation.CUSTOM_FOLDERS,
                SearchLocation.OVERRIDE,
                SearchLocation.CUSTOM_MODULES,
                SearchLocation.SOUND,
                SearchLocation.CHITIN,
            ]

        sounds: CaseInsensitiveDict[bytes | None] = CaseInsensitiveDict()
        sound_formats: list[ResourceType] = [ResourceType.WAV, ResourceType.MP3]

        for resname in resnames:
            sounds[resname] = None

        def check_dict(values: dict[str, list[FileResource]]):
            for resources in values.values():
                check_list(resources)

        def check_list(values: list[FileResource]):
            for resource in values:
                case_resname: str = resource.resname().casefold()
                if case_resname in case_resnames and resource.restype() in sound_formats:
                    case_resnames.remove(case_resname)
                    sound_data: bytes = resource.data()
                    sounds[resource.resname()] = deobfuscate_audio(sound_data) if sound_data else b""

        def check_capsules(values: list[Capsule]):
            for capsule in values:
                for case_resname in copy(case_resnames):
                    sound_data: bytes | None = None
                    for sformat in sound_formats:
                        sound_data = capsule.resource(case_resname, sformat)
                        if sound_data is not None:  # Break after first match found. Note that this means any other formats in this list will be ignored
                            break
                    if sound_data is None:  # No sound data found in this list.
                        continue
                    case_resnames.remove(case_resname)
                    sounds[case_resname] = deobfuscate_audio(sound_data) if sound_data else b""

        def check_folders(values: list[Path]):
            queried_sound_files: set[Path] = set()
            for folder in values:
                queried_sound_files.update(
                    file
                    for file in folder.safe_rglob("*")
                    if (
                        file.stem.casefold() in case_resnames
                        and ResourceType.from_extension(file.suffix) in sound_formats
                        and file.safe_isfile()
                    )
                )
            for sound_file in queried_sound_files:
                case_resnames.remove(sound_file.stem.casefold())
                sound_data: bytes = BinaryReader.load_file(sound_file)
                sounds[sound_file.stem] = deobfuscate_audio(sound_data) if sound_data else b""

        function_map: dict[SearchLocation, Callable] = {
            SearchLocation.OVERRIDE: lambda: check_dict(self._override),
            SearchLocation.MODULES: lambda: check_dict(self._modules),
            SearchLocation.RIMS: lambda: check_dict(self._rims),
            SearchLocation.CHITIN: lambda: check_list(self._chitin),
            SearchLocation.MUSIC: lambda: check_list(self._streammusic),
            SearchLocation.SOUND: lambda: check_list(self._streamsounds),
            SearchLocation.VOICE: lambda: check_list(self._streamwaves),
            SearchLocation.CUSTOM_MODULES: lambda: check_capsules(capsules),
            SearchLocation.CUSTOM_FOLDERS: lambda: check_folders(folders),  # type: ignore[arg-type]
        }

        for item in order:
            assert isinstance(item, SearchLocation)
            function_map.get(item, lambda: None)()

        return sounds

    def string(
        self,
        locstring: LocalizedString,
        default: str = "",
    ) -> str:
        """Returns the string for the LocalizedString provided.

        This is a wrapper of the strings() method provided to make searching for a single string more convenient.

        Args:
        ----
            locstring (LocalizedString):
            default (str): the str to return when not found.

        Returns:
        -------
            str: text from the locstring lookup
        """
        batch: dict[LocalizedString, str] = self.strings([locstring], default)
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
        stringrefs: list[int] = [locstring.stringref for locstring in queries]

        batch: dict[int, StringResult] = self.talktable().batch(stringrefs)
        female_batch: dict[int, StringResult] = self.female_talktable().batch(stringrefs) if self.female_talktable().path().safe_isfile() else {}

        results: dict[LocalizedString, str] = {}
        for locstring in queries:
            if locstring.stringref != -1:  # TODO: use gender information from locstring.
                if locstring.stringref in batch:
                    results[locstring] = batch[locstring.stringref].text
                elif locstring.stringref in female_batch:
                    results[locstring] = female_batch[locstring.stringref].text
            elif len(locstring):
                for _language, _gender, text in locstring:
                    results[locstring] = text
                    break
            else:
                results[locstring] = default

        return results

    @staticmethod
    def replace_module_extensions(module_filepath: os.PathLike | str) -> str:
        module_filename: str = PurePath(module_filepath).name
        result = re.sub(r"\.rim$", "", module_filename, flags=re.IGNORECASE)
        for erftype_name in ERFType.__members__:
            result = re.sub(rf"\.{erftype_name}$", "", result, flags=re.IGNORECASE)
        result = result[:-2] if result.lower().endswith("_s") else result
        result = result[:-4] if result.lower().endswith("_dlg") else result
        return result  # noqa: RET504

    def module_names(self, *, use_hardcoded: bool = True) -> dict[str, str]:
        """Returns a dictionary mapping module filename to the name of the area.

        The name is taken from the LocalizedString "Name" in the relevant module file's ARE resource.

        Returns:
        -------
            A dictionary mapping module filename to in-game module area name.
        """
        return {module: self.module_name(module, use_hardcoded=use_hardcoded) for module in self.modules_list()}

    def module_ids(self, *, use_hardcoded: bool = True, use_alternate: bool = False) -> dict[str, str]:
        """Returns a dictionary mapping module filename to the ID of the module.

        The ID is taken from the ResRef field "Mod_Entry_Area" in the relevant module file's IFO resource.

        Returns:
        -------
            A dictionary mapping module filename to in-game module id.
        """
        return {module: self.module_id(module, use_hardcoded=use_hardcoded, use_alternate=use_alternate) for module in self.modules_list()}

    def module_name(
        self,
        module_filename: str,
        *,
        use_hardcoded: bool = True,
    ) -> str:
        """Returns the name of the area for a module from the installations module list.

        The name is taken from the LocalizedString "Name" in the relevant module file's ARE resource.

        Args:
        ----
            module_filename: The name of the module file.
            use_hardcoded: Use hardcoded values for modules where applicable.

        Returns:
        -------
            The name of the area for the module.
        """
        root: str = self.replace_module_extensions(module_filename)
        lower_root: str = root.lower()
        if use_hardcoded:
            for key, value in HARDCODED_MODULE_NAMES.items():
                if key.upper() in root.upper():
                    return value
        matching_module_filenames = self._find_matching_erf_rim_from_root(lower_root)
        name: str | None = root
        our_erf_rims_module: set[tuple[str, Capsule]] = set()
        self._build_capsule_info(
            lower_root,
            module_filename,
            matching_module_filenames,
            our_erf_rims_module,
        )
        mod_ids_to_try: set[str] = set()
        for mod_id, capsule in our_erf_rims_module:
            try:
                are_tag_resource: bytes | None = capsule.resource(mod_id, ResourceType.ARE)
                if are_tag_resource is None:
                    continue

                are: GFF = read_gff(are_tag_resource)
                locstring: LocalizedString = are.root.get_locstring("Name")
                if locstring.stringref == -1:
                    name = locstring.get(Language.ENGLISH, Gender.MALE)
                else:
                    name = self.talktable().string(locstring.stringref)
            except Exception as e:  # pylint: disable=W0718  # noqa: BLE001, PERF203
                print(format_exception_with_variables(e, message="This exception has been suppressed in pykotor.extract.installation."))
            mod_ids_to_try.add(mod_id)

        # Deeper check.
        for mod_id in mod_ids_to_try:
            for _unfound_mod_id, capsule in our_erf_rims_module:
                with suppress(Exception):
                    #print(f"Checking for '{mod_id}' in '{module_filename}'")
                    are_resource = capsule.info(mod_id, ResourceType.ARE)
                    if are_resource is None:
                        continue
                    locstring: LocalizedString = are.root.get_locstring("Name")
                    if locstring.stringref == -1:
                        name = locstring.get(Language.ENGLISH, Gender.MALE)
                    else:
                        name = self.talktable().string(locstring.stringref)
                    if name is not None:
                        return name
        return name or module_filename

    def module_id(
        self,
        module_filename: str,
        *,
        use_hardcoded: bool = True,
        use_alternate: bool = False
    ) -> str:
        """Returns the ID of the area for a module from the installations module list.

        The ID is taken from the ResRef field "Mod_Entry_Area" in the relevant module file's IFO resource.

        Args:
        ----
            module_filename: The name of the module file.
            use_hardcoded: Deprecated (does nothing)

        Returns:
        -------
            The ID of the area for the module.
        """
        root: str = self.replace_module_extensions(module_filename)
        lower_root: str = root.lower()
        found_mod_id: str = root
        matching_module_filenames = self._find_matching_erf_rim_from_root(lower_root)
        try:
            our_erf_rims_module: set[Capsule] = set()
            self._build_capsule_info(
                lower_root,
                module_filename,
                matching_module_filenames,
                our_erf_rims_module,
                modid_lookup=False,
            )
            mod_id: str = ""
            mod_ids_to_try: set[str] = set()
            for iterated_capsule in our_erf_rims_module:
                try:
                    module_ifo_data: bytes | None = iterated_capsule.resource("module", ResourceType.IFO)
                    if not module_ifo_data:
                        continue

                    ifo: GFF = read_gff(module_ifo_data)
                    try:  # Only ever seen this wrong for custom modules.
                        if ifo.root.exists("Mod_Area_list"):
                            mod_area_list = ifo.root.get_list("Mod_Area_list")
                            mod_id = found_mod_id = self._get_mod_id_from_area_list(mod_area_list)
                            if use_alternate:  # noqa: SIM102  # sourcery skip: merge-nested-ifs, remove-str-from-print, swap-nested-ifs
                                if mod_id and mod_id.lower() in lower_root:
                                    #print(f"Alternate: Found Mod_Area_list '{mod_id}' in '{lower_root}'")
                                    return mod_id
                                #print(f"Mod_Area_list '{mod_id}' not in '{lower_root}'")
                    except Exception as e:  # noqa: PERF203, BLE001
                        print(iterated_capsule.filename(), "Mod_Area_list", str(e))
                    else:
                        #if mod_id:
                        #    print(f"Got ID '{mod_id}' in Mod_Area_list erf/rim '{iterated_capsule.filename()}'")
                        if not use_alternate:
                            if mod_id and mod_id.strip():
                                if iterated_capsule.info(mod_id, ResourceType.ARE) is not None:
                                    return mod_id
                                mod_ids_to_try.add(mod_id)
                                #print(f"Mod_Area_list entry '{mod_id}' invalid? erf/rim '{iterated_capsule.filename()}'")
                            #else:
                                #print(f"Mod_Area_list not defined? erf/rim '{iterated_capsule.filename()}'")
                        mod_id = ""

                    try:  # Adding because I'm unsure if the case is maintained.
                        if ifo.root.exists("Mod_Area_List"):
                            mod_area_list = ifo.root.get_list("Mod_Area_List")
                            mod_id = found_mod_id = self._get_mod_id_from_area_list(mod_area_list)
                            if use_alternate:  # noqa: SIM102  # sourcery skip: merge-nested-ifs
                                if mod_id and mod_id.lower() in lower_root:
                                    #print(f"Alternate: Found Mod_Area_List '{mod_id}' in '{lower_root}'")
                                    return mod_id
                                #print(f"Mod_Area_List '{mod_id}' not in '{lower_root}'")
                    except Exception as e:  # noqa: PERF203, BLE001
                        print(iterated_capsule.filename(), "Mod_Area_List", str(e))
                    else:
                        #if mod_id:
                        #    print(f"Got ID '{mod_id}' in Mod_Area_List for erf/rim '{iterated_capsule.filename()}'")
                        if not use_alternate:
                            if mod_id and mod_id.strip():
                                if iterated_capsule.info(mod_id, ResourceType.ARE) is not None:
                                    return mod_id
                                mod_ids_to_try.add(mod_id)
                                #print(f"Mod_Area_List entry '{mod_id}' invalid? erf/rim '{iterated_capsule.filename()}'")
                            #else:
                                #print(f"Mod_Area_List not defined? erf/rim '{iterated_capsule.filename()}'")
                        mod_id = ""

                    try:  # Sometimes wrong, and sometimes it's not defined.
                        if ifo.root.exists("Mod_VO_ID"):
                            mod_id = found_mod_id = ifo.root.get_string("Mod_VO_ID").strip()
                            if use_alternate:  # noqa: SIM102  # sourcery skip: merge-nested-ifs
                                if mod_id and mod_id.lower() in lower_root:
                                    #print(f"Alternate: Found Mod_VO_ID '{mod_id}' in '{lower_root}'")
                                    return mod_id
                                #print(f"Mod_VO_ID '{mod_id}' not in '{lower_root}'")
                    except Exception as e:  # noqa: PERF203, BLE001
                        print(iterated_capsule.filename(), "Mod_VO_ID", str(e))
                    else:
                        #if mod_id:
                        #    print(f"Got ID '{mod_id}' in Mod_VO_ID for erf/rim '{iterated_capsule.filename()}'")
                        if not use_alternate:
                            if mod_id and mod_id.strip():
                                if iterated_capsule.info(mod_id, ResourceType.ARE) is not None:
                                    return mod_id
                                mod_ids_to_try.add(mod_id)
                                #print(f"Mod_VO_ID entry '{mod_id}' invalid? erf/rim '{iterated_capsule.filename()}'")
                            #else:
                                #print(f"Mod_VO_ID not defined? erf/rim '{iterated_capsule.filename()}'")
                        mod_id = ""

                    try:  # This one is sometimes wrong in k1, doesn't seem to be used much (if at all) in k2
                        if ifo.root.exists("Mod_Entry_Area"):
                            mod_id = found_mod_id = str(ifo.root.get_resref("Mod_Entry_Area")).strip()
                            if use_alternate:  # noqa: SIM102  # sourcery skip: merge-nested-ifs
                                if mod_id and mod_id.lower() in lower_root:
                                    #print(f"Alternate: Found Mod_Entry_Area '{mod_id}' in '{lower_root}'")
                                    return mod_id
                                #print(f"Mod_Entry_Area '{mod_id}' not in '{lower_root}'")
                    except Exception as e:  # noqa: PERF203, BLE001
                        print(iterated_capsule.filename(), "Mod_Entry_Area", str(e))
                    else:
                        #if mod_id:
                        #    print(f"Got ID '{mod_id}' in Mod_Entry_Area for erf/rim '{iterated_capsule.filename()}'")
                        if not use_alternate:  # noqa: SIM102
                            if mod_id and mod_id.strip():
                                if iterated_capsule.info(mod_id, ResourceType.ARE) is not None:
                                    return mod_id
                                mod_ids_to_try.add(mod_id)
                                #print(f"Mod_Entry_Area entry '{mod_id}' invalid? erf/rim '{iterated_capsule.filename()}'")
                            #else:
                                #print(f"Mod_Entry_Area not defined? erf/rim '{iterated_capsule.filename()}'")
                        mod_id = ""

                except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
                    print(format_exception_with_variables(e, message="This exception has been suppressed in pykotor.extract.installation."))

            # Validate the ARE exists.
            for mod_id in mod_ids_to_try:
                for capsule in our_erf_rims_module:
                    #print(f"Checking for '{mod_id}' in '{module_filename}'")
                    if capsule.info(mod_id, ResourceType.ARE) is None:
                        continue
                    return mod_id
                if mod_id.startswith("m") or mod_id[1].isdigit():
                    found_mod_id = mod_id
        except Exception as e:  # noqa: BLE001
            print(format_exception_with_variables(e, message="This exception has been suppressed in pykotor.extract.installation."))
        #print(f"NOT FOUND: Module ID for '{module_filename}', using backup of '{found_mod_id}'")
        return found_mod_id

    def _build_capsule_info(
        self,
        lower_root: str,
        module_filename: str,
        matching_module_filenames: set[str],
        our_erf_rims_module: set[tuple[str, Capsule]] | set[Capsule],
        *,
        modid_lookup: bool = True,
    ):
        mod_filename = f"{lower_root}.mod"
        mod_id: str = ""
        if modid_lookup:
            mod_id = self.module_id(mod_filename)
        if module_filename.lower() == mod_filename and mod_filename in matching_module_filenames:
            mod_filepath = self.module_path() / mod_filename
            if mod_filepath.safe_isfile():
                try:
                    self._build_item(mod_filepath, modid_lookup, mod_id, our_erf_rims_module)
                except Exception as e:  # noqa: BLE001
                    print(format_exception_with_variables(e, message="This exception has been suppressed in pykotor.extract.installation."))
        # Prioritize the .mod
        rim_filename = f"{lower_root}.rim"
        rim_s_filename = f"{lower_root}_s.rim"
        _dlg_filename = f"{lower_root}._dlg.erf"
        rim_filepath = self.module_path() / rim_filename
        rim_s_filepath = self.module_path() / rim_s_filename
        _dlg_filepath = self.module_path() / _dlg_filename
        #print("Filenames:", mod_filename, rim_filename, rim_s_filename, _dlg_filename)
        if modid_lookup:
            mod_id = self.module_id(module_filename)
        if rim_filename in matching_module_filenames and rim_filepath.safe_isfile():
            try:
                self._build_item(rim_filepath, modid_lookup, mod_id, our_erf_rims_module)
            except Exception as e:  # noqa: BLE001
                print(format_exception_with_variables(e, message="This exception has been suppressed in pykotor.extract.installation."))
        if rim_s_filename in matching_module_filenames and rim_s_filepath.safe_isfile():
            try:
                self._build_item(rim_s_filepath, modid_lookup, mod_id, our_erf_rims_module)
            except Exception as e:  # noqa: BLE001
                print(format_exception_with_variables(e, message="This exception has been suppressed in pykotor.extract.installation."))
        if _dlg_filename in matching_module_filenames and _dlg_filepath.safe_isfile():
            try:
                self._build_item(_dlg_filepath, modid_lookup, mod_id, our_erf_rims_module)
            except Exception as e:  # noqa: BLE001
                print(format_exception_with_variables(e, message="This exception has been suppressed in pykotor.extract.installation."))

    def _build_item(self, erfrim_filepath: os.PathLike | str, modid_lookup: bool, mod_id: str, our_erf_rims_module: set):  # noqa: FBT001
        item: Capsule | tuple[str, Capsule] = Capsule(erfrim_filepath)
        if modid_lookup:
            item = (mod_id, item)
        our_erf_rims_module.add(item)

    def _find_matching_erf_rim_from_root(self, lower_root: str) -> set[str]:
        result: set[str] = set()
        for iterated_module_filename in self.modules_list():
            lower_iterated_module_filename = iterated_module_filename.lower()
            if lower_root != self.replace_module_extensions(lower_iterated_module_filename):
                continue
            result.add(lower_iterated_module_filename)
        return result

    def _get_mod_id_from_area_list(self, mod_area_list: GFFList) -> str:
        mod_id: str = ""
        for gff_struct in mod_area_list:
            try:
                mod_id = str(gff_struct.get_resref("Area_Name"))
            except Exception as e:  # noqa: PERF203, BLE001
                print(format_exception_with_variables(e, message="This exception has been suppressed in pykotor.extract.installation."))
            else:
                if mod_id and mod_id.strip():
                    return mod_id
        return mod_id
