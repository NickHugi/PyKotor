from __future__ import annotations

import re
from contextlib import suppress
from copy import copy
from enum import Enum, IntEnum
from typing import TYPE_CHECKING, ClassVar, NamedTuple

from pykotor.common.language import Gender, Language, LocalizedString
from pykotor.common.misc import CaseInsensitiveDict, Game
from pykotor.common.stream import BinaryReader
from pykotor.extract.capsule import Capsule
from pykotor.extract.chitin import Chitin
from pykotor.extract.file import FileResource, LocationResult, ResourceIdentifier, ResourceResult
from pykotor.extract.talktable import StringResult, TalkTable
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.formats.tpc import TPC, read_tpc
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_capsule_file, is_erf_file, is_mod_file, is_rim_file
from pykotor.tools.path import CaseAwarePath
from pykotor.tools.sound import fix_audio
from pykotor.tslpatcher.logger import PatchLogger
from utility.path import Path, PurePath

if TYPE_CHECKING:
    import os

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
    """Full list of ERF filenames containing the texture files for both games."""

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
HARDCODED_MODULE_IDS: dict[str, str] = {
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


class Installation:
    """Installation provides a centralized location for loading resources stored in the game through its various folders and formats."""

    TEXTURES_TYPES: ClassVar[list[ResourceType]] = [
        ResourceType.TPC,
        ResourceType.TGA,
        ResourceType.DDS,
    ]

    def __init__(self, path: os.PathLike | str):
        self._path: CaseAwarePath = path if isinstance(path, CaseAwarePath) else CaseAwarePath(path)

        self._talktable: TalkTable = TalkTable(self._path / "dialog.tlk")
        self._female_talktable: TalkTable = TalkTable(self._path / "dialogf.tlk")

        self._chitin: list[FileResource] = []
        self._modules: dict[str, list[FileResource]] = {}
        self._lips: dict[str, list[FileResource]] = {}
        self._texturepacks: dict[str, list[FileResource]] = {}
        self._override: dict[str, list[FileResource]] = {}
        self._streammusic: list[FileResource] = []
        self._streamsounds: list[FileResource] = []
        self._streamwaves: list[FileResource] = []
        self._rims: dict[str, list[FileResource]] = {}
        self._game: Game | None = None

        self.load_chitin()
        self.load_lips()
        self.load_modules()
        self.load_override()
        if self.game() == Game.K1:
            self.load_rims()
        self.load_streammusic()
        self.load_streamsounds()
        self.load_streamwaves()
        self.load_textures()
        print(f"Finished loading the installation from {self._path!s}")

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
        return self._find_resource_folderpath("Modules")

    def override_path(self) -> CaseAwarePath:
        """Returns the path to override folder of the Installation. This method maintains the case of the foldername.

        Returns
        -------
            The path to the override folder.
        """
        return self._find_resource_folderpath("Override", optional=True)

    def lips_path(self) -> CaseAwarePath:
        """Returns the path to 'lips' folder of the Installation. This method maintains the case of the foldername.

        Returns
        -------
            The path to the lips folder.
        """
        return self._find_resource_folderpath("lips")

    def texturepacks_path(self) -> CaseAwarePath:
        """Returns the path to 'texturepacks' folder of the Installation. This method maintains the case of the foldername.

        Returns
        -------
            The path to the texturepacks folder.
        """
        return self._find_resource_folderpath("texturepacks", optional=True)

    def rims_path(self) -> CaseAwarePath:
        """Returns the path to 'rims' folder of the Installation. This method maintains the case of the foldername.

        Returns
        -------
            The path to the rims folder.
        """
        return self._find_resource_folderpath("rims", optional=True)

    def streammusic_path(self) -> CaseAwarePath:
        """Returns the path to 'streammusic' folder of the Installation. This method maintains the case of the foldername.

        Returns
        -------
            The path to the streammusic folder.
        """
        return self._find_resource_folderpath("streammusic")

    def streamsounds_path(self) -> CaseAwarePath:
        """Returns the path to 'streamsounds' folder of the Installation. This method maintains the case of the foldername.

        Returns
        -------
            The path to the streamsounds folder.
        """
        return self._find_resource_folderpath("streamsounds", optional=True)

    def streamwaves_path(self) -> CaseAwarePath:
        """Returns the path to 'streamwaves' folder of the Installation. This method maintains the case of the foldername.

        In the second game, this folder has been named 'streamvoice'.

        Returns
        -------
            The path to the streamvoice folder.
        """
        return self._find_resource_folderpath(("streamwaves", "streamvoice"))

    def _find_resource_folderpath(
        self,
        folder_names: tuple[str, ...] | str,
        optional: bool = False,
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
            resource_path = self._path
            if isinstance(folder_names, str):  # make a tuple
                folder_names = (folder_names,)
            for folder_name in folder_names:
                resource_path = CaseAwarePath(self._path, folder_name)
                if resource_path.is_dir():
                    return resource_path
        except Exception as e:  # noqa: BLE001
            msg = f"An error occurred while finding the '{' or '.join(folder_names)}' folder in '{self._path}'."
            raise OSError(msg) from e
        else:
            if optional:
                return CaseAwarePath(self._path, folder_names[0])
        errored_folder_names = "' or '".join(folder_names)
        msg = f"Could not find the '{errored_folder_names}' folder in '{self._path}'."
        raise FileNotFoundError(msg)

    # endregion

    # region Load Data

    def load_resources(self, path: CaseAwarePath, capsule_check=None, recurse=False) -> dict[str, list[FileResource]] | list[FileResource]:
        """Load resources for a given path and store them in a new list/dict.

        Args:
        ----
            path_method (os.PathLike | str): path for lookup.
            recurse (bool): whether to recurse into subfolders (default is False)

        Returns:
        -------
            list[FileResource]: The list where resources at the path have been stored.
             or
            dict[str, list[FileResource]]: A dict keyed by filename to the encapsulated resources
        """
        resources: dict[str, list[FileResource]] | list[FileResource] = {} if capsule_check else []

        if not path.exists():
            print(f"The '{path.name}' folder did not exist at '{self.path()!s}' when loading the installation, skipping...")
            return resources

        files_list: list[CaseAwarePath] = list(path.safe_rglob("*")) if recurse else list(path.safe_iterdir())  # type: ignore[reportGeneralTypeIssues]
        for file in files_list:
            if capsule_check and capsule_check(file.name):
                resources[file.name] = list(Capsule(file))  # type: ignore[assignment, call-overload]
            else:
                with suppress(Exception):
                    resname, restype = ResourceIdentifier.from_path(file).validate()
                    resource = FileResource(
                        resname,
                        restype,
                        file.stat().st_size,
                        0,
                        file,
                    )
                    resources.append(resource)  # type: ignore[assignment, call-overload, union-attr]
        if not resources or not files_list:
            print(f"No resources found at '{path!s}' when loading the installation, skipping...")
        else:
            print(f"Loading '{path.name}' folder from installation...")
        return resources

    def load_chitin(self) -> None:
        """Reloads the list of resources in the Chitin linked to the Installation."""
        chitin_path = self._path / "chitin.key"
        if not chitin_path.exists():
            print(f"The chitin.key file did not exist at '{self._path!s}' when loading the installation, skipping...")
            return
        print("Load chitin...")
        self._chitin = list(Chitin(key_path=chitin_path))

    def load_lips(
        self,
    ) -> None:
        """Reloads the list of modules in the lips folder linked to the Installation."""
        self._lips = self.load_resources(self.lips_path(), capsule_check=is_mod_file)  # type: ignore[assignment]

    def load_modules(self) -> None:
        """Reloads the list of modules files in the modules folder linked to the Installation."""
        self._modules = self.load_resources(self.module_path(), capsule_check=is_capsule_file)  # type: ignore[assignment]

    def reload_module(self, module: str) -> None:
        """Reloads the list of resources in specified module in the modules folder linked to the Installation.

        Args:
        ----
            module: The filename of the module.
        """
        self._modules[module] = list(Capsule(self.module_path() / module))

    def load_rims(
        self,
    ) -> None:
        """Reloads the list of module files in the rims folder linked to the Installation."""
        self._rims = self.load_resources(self.rims_path(), capsule_check=is_rim_file)  # type: ignore[assignment]

    def load_textures(
        self,
    ) -> None:
        """Reloads the list of modules files in the texturepacks folder linked to the Installation."""
        self._texturepacks = self.load_resources(self.texturepacks_path(), capsule_check=is_erf_file)  # type: ignore[assignment]

    def load_override(self, directory: str | None = None) -> None:
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
        override_path = self.override_path()
        if directory:
            target_dirs = [override_path / directory]
            self._override[directory] = []
        else:
            target_dirs = [f for f in override_path.safe_rglob("*") if f.safe_isdir()]
            target_dirs.append(override_path)
            self._override = {}

        for folder in target_dirs:
            relative_folder = folder.relative_to(override_path).as_posix()  # '.' if folder is the same as override_path
            self._override[relative_folder] = self.load_resources(folder)  # type: ignore[assignment]

    def reload_override(self, directory: str) -> None:
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

    def reload_override_file(self, file: os.PathLike | str) -> None:
        filepath: Path = file if isinstance(file, Path) else Path(file)  # type: ignore[reportGeneralTypeIssues, assignment]
        rel_folderpath = filepath.parent.relative_to(self.override_path())
        identifier = ResourceIdentifier.from_path(filepath)
        if identifier.restype == ResourceType.INVALID:
            print("Cannot reload override file. Invalid KOTOR resource:", identifier)
            return
        resource = FileResource(
            *identifier,
            filepath.stat().st_size,
            0,
            filepath,
        )
        override_list: list[FileResource] = self._override[str(rel_folderpath)]
        if resource not in override_list:
            print(f"Cannot reload override file '{identifier!s}'. File not found in ", rel_folderpath)
            return
        index: int = override_list.index(resource)
        override_list[index] = resource

    def load_streammusic(self) -> None:
        """Reloads the list of resources in the streammusic folder linked to the Installation."""
        self._streammusic = self.load_resources(self.streammusic_path())  # type: ignore[assignment]

    def load_streamsounds(self) -> None:
        """Reloads the list of resources in the streamsounds folder linked to the Installation."""
        self._streamsounds = self.load_resources(self.streamsounds_path())  # type: ignore[assignment]

    def load_streamwaves(self) -> None:
        """Reloads the list of resources in the streamvoice/streamwaves folder linked to the Installation."""
        self._streamwaves = self.load_resources(self.streamwaves_path(), recurse=True)  # type: ignore[assignment]

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
        """Returns the list of module filenames located in the modules folder linked to the Installation.

        Module filenames are cached and require to be refreshed after a file is added, deleted or renamed.

        Returns
        -------
            A list of filenames.
        """
        return list(self._modules.keys())

    def module_resources(self, filename: str) -> list[FileResource]:
        """Returns a list of FileResources stored in the specified module file located in the modules folder linked to the Installation.

        Module resources are cached and require a reload after the contents have been modified.

        Returns
        -------
            A list of FileResources.
        """
        return self._modules[filename][:]

    def lips_list(self) -> list[str]:
        """Returns the list of module filenames located in the lips folder linked to the Installation.

        Module filenames are cached and require to be refreshed after a file is added, deleted or renamed.

        Returns
        -------
            A list of filenames.
        """
        return list(self._lips.keys())

    def lip_resources(self, filename: str) -> list[FileResource]:
        """Returns a list of FileResources stored in the specified module file located in the lips folder linked to the Installation.

        Module resources are cached and require a reload after the contents have been modified.

        Returns
        -------
            A list of FileResources.
        """
        return self._lips[filename][:]

    def texturepacks_list(self) -> list[str]:
        """Returns the list of texture-pack filenames located in the texturepacks folder linked to the Installation.

        Returns
        -------
            A list of filenames.
        """
        return list(self._texturepacks.keys())

    def texturepack_resources(self, filename: str) -> list[FileResource]:
        """Returns a list of FileResources stored in the specified module file located in the texturepacks folder linked to the Installation.

        Texturepacks resources are cached and require a reload after the contents have been modified.

        Returns
        -------
            A list of FileResources.
        """
        return self._texturepacks[filename][:]

    def override_list(self) -> list[str]:
        """Returns the list of subdirectories located in override folder linked to the Installation.

        Subdirectories are cached and require a refresh after a folder is added, deleted or renamed.

        Returns
        -------
            A list of subdirectories.
        """
        return list(self._override.keys())

    def override_resources(self, directory: str) -> list[FileResource]:
        """Returns a list of FileResources stored in the specified subdirectory located in the override folder linked to the Installation.

        Override resources are cached and require a reload after the contents have been modified.

        Returns
        -------
            A list of FileResources.
        """
        return self._override[directory]

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
        r_path: CaseAwarePath = path if isinstance(path, CaseAwarePath) else CaseAwarePath(path)

        def check(x) -> bool:
            file_path: CaseAwarePath = r_path.joinpath(x)
            return file_path.exists()

        # Checks for each game
        game1_checks = [
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
            check("modules/danm13_loc.mod"),
            check("modules/danm14aa_loc.mod"),
            check("modules/danm14ab_loc.mod"),
            check("modules/danm14ac_loc.mod"),
            check("modules/danm14ad_loc.mod"),
            check("modules/danm14ae_loc.mod"),
            check("modules/danm15_loc.mod"),
            check("modules/danm16_loc.mod"),
            check("modules/ebo_m12aa_loc.mod"),
            check("modules/ebo_m40aa_loc.mod"),
            check("modules/ebo_m40ad_loc.mod"),
            check("modules/ebo_m41aa_loc.mod"),
            check("modules/ebo_m46ab_loc.mod"),
            check("modules/end_m01aa_loc.mod"),
            check("modules/end_m01ab_loc.mod"),
            check("modules/global.mod"),
            check("modules/kas_m22aa_loc.mod"),
            check("modules/kas_m22ab_loc.mod"),
            check("modules/kas_m23aa_loc.mod"),
            check("modules/kas_m23ab_loc.mod"),
            check("modules/kas_m23ac_loc.mod"),
            check("modules/kas_m23ad_loc.mod"),
            check("modules/kas_m24aa_loc.mod"),
            check("modules/kas_m25aa_loc.mod"),
            check("modules/korr_m33aa_loc.mod"),
            check("modules/korr_m33ab_loc.mod"),
            check("modules/korr_m34aa_loc.mod"),
            check("modules/korr_m35aa_loc.mod"),
            check("modules/korr_m36aa_loc.mod"),
            check("modules/korr_m37aa_loc.mod"),
            check("modules/korr_m38aa_loc.mod"),
            check("modules/korr_m38ab_loc.mod"),
            check("modules/korr_m39aa_loc.mod"),
            check("modules/legal.mod"),
            check("modules/lev_m40aa_loc.mod"),
            check("modules/lev_m40ab_loc.mod"),
            check("modules/lev_m40ac_loc.mod"),
            check("modules/lev_m40ad_loc.mod"),
            check("modules/liv_m99aa_loc.mod"),
            check("modules/M12ab_loc.mod"),
            check("modules/mainmenu.mod"),
            check("modules/manm26aa_loc.mod"),
            check("modules/manm26ab_loc.mod"),
            check("modules/manm26ac_loc.mod"),
            check("modules/STUNT_00_loc.mod"),
        ]

        game2_checks = [
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
            check("lips/001EBO_loc.mod"),
            check("Modules/002EBO_loc.mod"),
            check("Modules/003EBO_loc.mod"),
            check("Modules/004EBO_loc.mod"),
            check("Modules/005EBO_loc.mod"),
            check("Modules/006EBO_loc.mod"),
            check("Modules/007EBO_loc.mod"),
            check("Modules/101per_loc.mod"),
            check("Modules/102PER_loc.mod"),
            check("Modules/103PER_loc.mod"),
            check("Modules/104PER_loc.mod"),
            check("Modules/105PER_loc.mod"),
            check("Modules/106PER_loc.mod"),
            check("Modules/107PER_loc.mod"),
            check("Modules/151HAR_loc.mod"),
            check("Modules/152HAR_loc.mod"),
            check("Modules/153HAR_loc.mod"),
        ]

        # Scoring for each game
        game1_score = sum(game1_checks)
        game2_score = sum(game2_checks)

        # Determine the game with the most checks passed
        if game1_score > game2_score:
            return Game(1)
        if game2_score > game1_score:
            return Game(2)

        # No checks passed
        if game1_score == 0 and game2_score == 0:
            return None

        # Same score
        return None

    def game(self) -> Game:
        """Determines the game object for the given save file path.

        Args:
        ----
            self: The class instance

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

        game = self.determine_game(self.path())
        if game is not None:
            self._game = game
            return game

        msg = "Could not determine the KOTOR game version! Did you select the right installation folder?"
        raise ValueError(msg)

    def talktable(self) -> TalkTable:
        """Returns the TalkTable linked to the Installation.

        Returns
        -------
            A TalkTable object.
        """
        return self._talktable

    def female_talktable(self) -> TalkTable:
        """Returns the female TalkTable linked to the Installation. This is 'dialogf.tlk' in the Polish version of K1.

        Returns
        -------
            A TalkTable object.
        """
        return self._female_talktable

    def resource(
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
            print(f"Could not find '{resname}.{restype}' during resource lookup.")
            return None
        return search

    def resources(
        self,
        queries: list[ResourceIdentifier],
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
            location_list = locations.get(query, [])

            if not location_list:
                print(f"Resource not found: '{query}'")
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
        capsules = [] if capsules is None else capsules
        folders = [] if folders is None else folders

        locations: dict[ResourceIdentifier, list[LocationResult]] = {}
        for qinden in queries:
            locations[qinden] = []

        def check_dict(values: dict[str, list[FileResource]]):
            for resources in values.values():
                check_list(resources)

        def check_list(values: list[FileResource]):
            for query in queries:
                for resource in values:
                    identifier = resource.identifier()
                    if query.resname.lower() == identifier.resname.lower() and identifier.restype == query.restype:
                        location = LocationResult(
                            resource.filepath(),
                            resource.offset(),
                            resource.size(),
                        )
                        locations[resource.identifier()].append(location)

        def check_capsules(values: list[Capsule]):
            for capsule in values:
                for query in queries:
                    resource: FileResource | None = capsule.info(*query)
                    if resource is not None:
                        location = LocationResult(
                            resource.filepath(),
                            resource.offset(),
                            resource.size(),
                        )
                        locations[resource.identifier()].append(location)


        def check_folders(values: list[Path]):
            queried_files: set[Path] = set()
            for query in queries:
                for folder in values:
                    queried_files.update(
                        file
                        for file in folder.rglob("*")
                        if (
                            file.stem.lower() == query.resname.lower()
                            and file.suffix.lower() == f".{query.restype.extension.lower()}"
                            and file.safe_isfile()
                        )
                    )
            for file in queried_files:
                identifier = ResourceIdentifier.from_path(file)
                resource = FileResource(
                    *identifier,
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
        batch = self.textures([resname], order, capsules=capsules, folders=folders)
        return batch[resname] if batch else None

    def textures(
        self,
        resnames: list[str] | set[str],
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
        resnames = {resname.lower() for resname in resnames}
        capsules = [] if capsules is None else capsules
        folders = [] if folders is None else folders

        textures: CaseInsensitiveDict[TPC | None] = CaseInsensitiveDict()
        texture_types: list[ResourceType] = [ResourceType.TPC, ResourceType.TGA]

        for resname in resnames:
            textures[resname] = None

        def decode_txi(txi_bytes: bytes):
            return txi_bytes.decode("ascii", errors="ignore")

        def get_txi_from_list(resource_list: list[FileResource]) -> str:
            txi_resource: FileResource | None = next(
                (
                    resource
                    for resource in resource_list
                    if resource.resname() == resname and resource.restype() == ResourceType.TXI
                ),
                None,
            )
            if txi_resource is not None:
                return decode_txi(txi_resource.data())
            return ""

        def check_dict(values: dict[str, list[FileResource]]):
            for resources in values.values():
                check_list(resources)

        def check_list(resource_list: list[FileResource]):
            for resource in resource_list:
                resname = resource.resname()
                if resname.lower() in resnames and resource.restype() in texture_types:
                    resnames.remove(resname)
                    tpc = read_tpc(resource.data())
                    if resource.restype() == ResourceType.TGA:
                        tpc.txi = get_txi_from_list(resource_list)
                    textures[resname] = tpc

        def check_capsules(values: list[Capsule]):
            for capsule in values:
                for resname in resnames:
                    texture_data: bytes | None = None
                    tformat: ResourceType | None = None
                    for tformat in texture_types:
                        texture_data = capsule.resource(resname, tformat)
                        if texture_data is not None:
                            break
                    if texture_data is None:
                        continue

                    resnames.remove(resname)
                    tpc: TPC = read_tpc(texture_data)
                    if tformat == ResourceType.TGA:
                        txi_source: bytes | None = capsule.resource(resname, ResourceType.TXI)
                        if txi_source is not None:
                            tpc.txi = decode_txi(txi_source)
                    textures[resname] = tpc

        def check_folders(values: list[Path]):
            queried_texture_files: set[Path] = set()
            for folder in values:
                queried_texture_files.update(
                    file
                    for file in folder.rglob("*")
                    if (
                        file.stem.lower() in resnames
                        and ResourceType.from_extension(file.suffix) in texture_types
                        and file.safe_isfile()
                    )
                )
            for texture_file in queried_texture_files:
                texture_data: bytes = BinaryReader.load_file(texture_file)
                tpc = read_tpc(texture_data)
                txi_file = CaseAwarePath(texture_file.with_suffix(".txi"))
                if Path(txi_file) in queried_texture_files:
                    txi_data: bytes = BinaryReader.load_file(txi_file)
                    tpc.txi = decode_txi(txi_data)
                textures[texture_file.stem] = tpc

        function_map = {
            SearchLocation.OVERRIDE: lambda: check_dict(self._override),
            SearchLocation.MODULES: lambda: check_dict(self._modules),
            SearchLocation.RIMS: lambda: check_dict(self._rims),
            SearchLocation.TEXTURES_TPA: lambda: check_list(self._texturepacks[TexturePackNames.TPA.value]),
            SearchLocation.TEXTURES_TPB: lambda: check_list(self._texturepacks[TexturePackNames.TPB.value]),
            SearchLocation.TEXTURES_TPC: lambda: check_list(self._texturepacks[TexturePackNames.TPC.value]),
            SearchLocation.TEXTURES_GUI: lambda: check_list(self._texturepacks[TexturePackNames.GUI.value]),
            SearchLocation.CHITIN: lambda: check_list(self._chitin),
            SearchLocation.CUSTOM_MODULES: lambda: check_capsules(capsules),  # type: ignore[arg-type]
            SearchLocation.CUSTOM_FOLDERS: lambda: check_folders(folders),  # type: ignore[arg-type]
        }

        for item in order:
            assert isinstance(item, SearchLocation)
            function_map.get(item, lambda: None)()

        return textures

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
        batch = self.sounds([resname], order, capsules=capsules, folders=folders)
        return batch[resname] if batch else None

    def sounds(
        self,
        resnames: list[str] | set[str],
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
        resnames = {resname.lower() for resname in resnames}
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
                if resource.resname().lower() in resnames and resource.restype() in sound_formats:
                    resnames.remove(resource.resname())
                    sounds[resource.resname()] = fix_audio(resource.data())

        def check_capsules(values: list[Capsule]):
            for capsule in values:
                for resname in resnames:
                    sound_data: bytes | None = None
                    for sformat in sound_formats:
                        sound_data = capsule.resource(resname, sformat)
                        if sound_data is not None:
                            break
                    if sound_data is None:
                        continue
                    resnames.remove(resname)
                    sounds[resname] = fix_audio(sound_data)
                    continue

        def check_folders(values: list[Path]):
            queried_sound_files: set[Path] = set()
            for folder in values:
                queried_sound_files.update(
                    file
                    for file in folder.rglob("*")
                    if (
                        file.stem.lower() in resnames
                        and ResourceType.from_extension(file.suffix) in sound_formats
                        and file.safe_isfile()
                    )
                )
            for sound_file in queried_sound_files:
                data = BinaryReader.load_file(sound_file)
                sounds[sound_file.stem] = fix_audio(data)

        function_map = {
            SearchLocation.OVERRIDE: lambda: check_dict(self._override),
            SearchLocation.MODULES: lambda: check_dict(self._modules),
            SearchLocation.RIMS: lambda: check_dict(self._rims),
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

        return sounds

    def string(self, locstring: LocalizedString, default: str = "") -> str:
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

        batch: dict[int, StringResult] = self.talktable().batch(stringrefs)
        female_batch: dict[int, StringResult] = self.female_talktable().batch(stringrefs) if self.female_talktable().path().exists() else {}

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


    def module_name(self, module_filename: str, use_hardcoded: bool = True) -> str:
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
        root = self.replace_module_extensions(module_filename)
        if use_hardcoded:

            for key, value in HARDCODED_MODULE_NAMES.items():
                if key.upper() in module_filename.upper():
                    return value

        name: str = ""
        female_talktable_exists = self.female_talktable().path().exists()
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
                    name = self.talktable().string(locstring.stringref)
                    if not name and female_talktable_exists:  # check the female talktable if not found.
                        name = self.female_talktable().string(locstring.stringref)
                elif locstring.exists(Language.ENGLISH, Gender.MALE):
                    name = locstring.get(Language.ENGLISH, Gender.MALE)
                break

        return name

    def module_names(self) -> dict[str, str]:
        """Returns a dictionary mapping module filename to the name of the area.

        The name is taken from the LocalizedString "Name" in the relevant module file's ARE resource.

        Returns
        -------
            A dictionary mapping module filename to in-game module area name.
        """
        return {module: self.module_name(module) for module in self.modules_list()}


    def module_id(self, module_filename: str, use_hardcoded: bool = True) -> str:
        """Returns the ID of the area for a module from the installations module list.

        The ID is taken from the ResRef field "Mod_Entry_Area" in the relevant module file's IFO resource.

        Args:
        ----
            module_filename: The name of the module file.
            use_hardcoded: Use hardcoded values for modules where applicable.

        Returns:
        -------
            The ID of the area for the module.
        """
        root = self.replace_module_extensions(module_filename)
        if use_hardcoded:
            for key, value in HARDCODED_MODULE_IDS.items():
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

    @staticmethod
    def replace_module_extensions(module_filepath: os.PathLike | str) -> str:
        module_filename: str = PurePath(module_filepath).name
        result = re.sub(r"\.mod$", "", module_filename, flags=re.IGNORECASE)
        result = re.sub(r"\.erf$", "", result, flags=re.IGNORECASE)
        result = re.sub(r"\.rim$", "", result, flags=re.IGNORECASE)
        result = result[:-2] if result.lower().endswith("_s") else result
        result = result[:-4] if result.lower().endswith("_dlg") else result
        return result  # noqa: RET504

    def module_ids(self) -> dict[str, str]:
        """Returns a dictionary mapping module filename to the ID of the module.

        The ID is taken from the ResRef field "Mod_Entry_Area" in the relevant module file's IFO resource.

        Returns
        -------
            A dictionary mapping module filename to in-game module id.
        """
        return {module: self.module_id(module) for module in self.modules_list()}
