from __future__ import annotations

import itertools
from logging import Logger
import os
import platform
import sys

from copy import copy
from dataclasses import dataclass
from enum import Enum, IntEnum
from functools import lru_cache
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Any, Callable, ClassVar, overload
from typing import Generator, Iterable, Sequence

from loggerplus import RobustLogger  # pyright: ignore[reportMissingModuleSource]

from pykotor.common.language import Gender, Language, LocalizedString
from pykotor.common.misc import Game, ResRef
from pykotor.extract.capsule import Capsule
from pykotor.extract.chitin import Chitin
from pykotor.extract.file import FileResource, LocationResult, ResourceIdentifier, ResourceResult
from pykotor.extract.savedata import SaveFolderEntry
from pykotor.extract.talktable import TalkTable
from pykotor.resource.formats.gff.gff_auto import read_gff
from pykotor.resource.formats.gff.gff_data import GFFFieldType
from pykotor.resource.formats.tpc.tpc_auto import read_tpc
from pykotor.resource.formats.tpc.tpc_data import TPC
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_capsule_file, is_erf_file, is_mod_file
from pykotor.resource.formats.wav.wav_auto import bytes_wav, read_wav
from pykotor.tools.path import CaseAwarePath
from utility.common.more_collections import CaseInsensitiveDict

if TYPE_CHECKING:
    import io

    from collections.abc import Generator, Iterable, Sequence

    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from pykotor.common.misc import Game
    from pykotor.extract.capsule import LazyCapsule
    from pykotor.resource.formats.gff.gff_data import GFF

    from pykotor.common.language import LocalizedString
    from pykotor.extract.talktable import StringResult


@dataclass
class StrRefLocation:
    """Represents a specific location where a StrRef was found."""

    resource: FileResource
    locations: list[str]  # Location strings like "row_12.name", "field.Path.To.Field", "sound_BATTLECRY1", "offset_0x1A4"


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


class Installation:
    """Installation provides a centralized location for loading resources stored in the game through its various folders and formats.
    
    Handles resource loading from game installation directories including override folders,
    modules, chitin.key/BIF files, texture packs, RIM files, and stream directories.
    Provides lazy loading and caching for performance.
    
    References:
    ----------
        vendor/KOTOR_Registry_Install_Path_Editor/ (Windows registry path detection)
        vendor/reone/src/libs/resource/provider/ (Resource provider architecture)
        vendor/KotOR.js/src/loaders/ (Resource loading patterns)
        vendor/xoreos-tools/src/ (Resource extraction tools)
    
    Note: Installation path detection may differ between platforms (Windows registry vs manual path)
    """  # noqa: E501

    TEXTURES_TYPES: ClassVar[list[ResourceType]] = [
        ResourceType.TPC,
        ResourceType.TGA,
        ResourceType.DDS,
    ]

    def __init__(
        self,
        path: os.PathLike | str,
        *,
        progress_callback: Callable[[int | str, Literal["set_maximum", "increment", "update_maintask_text", "update_subtask_text"]], Any] | None = None,
    ):
        self._log: Logger = RobustLogger()
        self._path: CaseAwarePath = CaseAwarePath(path)

        self._talktable: TalkTable = TalkTable(self._path / "dialog.tlk")
        self._female_talktable: TalkTable = TalkTable(self._path / "dialogf.tlk")

        # Lazy-loaded data structures
        self._modules_data: dict[str, list[FileResource]] = {}
        self._lips_data: dict[str, list[FileResource]] = {}
        self.saves: dict[Path, dict[Path, list[FileResource]]] = {}
        self.save_folders: dict[Path, SaveFolderEntry] = {}  # Map save folder path to SaveFolderEntry
        self._texturepacks_data: dict[str, list[FileResource]] = {}

        self._override_data: dict[str, list[FileResource]] = {}

        self._patch_erf_data: list[FileResource] = []  # K1 only patch.erf file
        self._chitin_data: list[FileResource] = []
        self._streammusic_data: list[FileResource] = []
        self._streamsounds_data: list[FileResource] = []
        self._streamwaves_data: list[FileResource] = []
        self._game: Game | None = None

        # Lazy-loading flags
        self._modules_loaded: bool = False
        self._lips_loaded: bool = False
        self._saves_loaded: bool = False
        self._texturepacks_loaded: bool = False
        self._override_loaded: bool = False
        self._patch_erf_loaded: bool = False
        self._chitin_loaded: bool = False
        self._streammusic_loaded: bool = False
        self._streamsounds_loaded: bool = False
        self._streamwaves_loaded: bool = False

        self._initialized = False
        self.progress_callback: Callable[[int | str, Literal["set_maximum", "increment", "update_maintask_text", "update_subtask_text"]], Any] | None = progress_callback

    def __getstate__(self) -> dict[str, Any]:
        """Prepare Installation for pickling by excluding unpicklable objects."""
        state = self.__dict__.copy()
        # Remove unpicklable objects
        state["_log"] = None
        state["progress_callback"] = None
        return state

    def __setstate__(self, state: dict[str, Any]):
        """Restore Installation from pickle and recreate unpicklable objects."""
        self.__dict__.update(state)
        # Recreate unpicklable objects
        self._log = RobustLogger()
        self.progress_callback = None

    # Lazy-loading properties
    @property
    def _modules(self) -> dict[str, list[FileResource]]:
        if not self._modules_loaded:
            self.load_modules()
        return self._modules_data

    @property
    def _lips(self) -> dict[str, list[FileResource]]:
        if not self._lips_loaded:
            self.load_lips()
        return self._lips_data

    @property
    def _texturepacks(self) -> dict[str, list[FileResource]]:
        if not self._texturepacks_loaded:
            self.load_textures()
        return self._texturepacks_data

    @property
    def _override(self) -> dict[str, list[FileResource]]:
        if not self._override_loaded:
            self.load_override()
        return self._override_data

    @property
    def _patch_erf(self) -> list[FileResource]:
        if not self._patch_erf_loaded:
            self._load_patch_erf()
        return self._patch_erf_data

    @property
    def _chitin(self) -> list[FileResource]:
        if not self._chitin_loaded:
            self.load_chitin()
        return self._chitin_data

    @property
    def _streammusic(self) -> list[FileResource]:
        if not self._streammusic_loaded:
            self.load_streammusic()
        return self._streammusic_data

    @property
    def _streamsounds(self) -> list[FileResource]:
        if not self._streamsounds_loaded:
            self.load_streamsounds()
        return self._streamsounds_data

    @property
    def _streamwaves(self) -> list[FileResource]:
        if not self._streamwaves_loaded:
            # Need to determine game type to know which loader to call
            if self.game().is_k1():
                self.load_streamwaves()
            else:
                self.load_streamvoice()
        return self._streamwaves_data

    def reload_all(self):
        """Explicitly loads all resources from the installation."""
        # Reset all loaded flags to force reload
        self._chitin_loaded = False
        self._lips_loaded = False
        self._modules_loaded = False
        self._streammusic_loaded = False
        self._streamsounds_loaded = False
        self._streamwaves_loaded = False
        self._texturepacks_loaded = False
        self._override_loaded = False
        self._patch_erf_loaded = False
        self._saves_loaded = False

        if self.progress_callback is not None:
            self.progress_callback(9, "set_maximum")
        self._report_main_progress("Loading chitin...")
        self.load_chitin()
        self._report_main_progress("Loading lips...")
        self.load_lips()
        self._report_main_progress("Loading modules...")
        self.load_modules()
        self._report_main_progress("Loading streammusic...")
        self.load_streammusic()
        self._report_main_progress("Loading streamsounds...")
        self.load_streamsounds()
        self._report_main_progress("Loading textures...")
        self.load_textures()
        self._report_main_progress("Loading saves...")
        self.load_saves()
        if self.game().is_k1():
            self._report_main_progress("Loading streamwaves...")
            self.load_streamwaves()
        elif self.game().is_k2():
            self._report_main_progress("Loading streamvoice...")
            self.load_streamvoice()
        self._report_main_progress("Loading override...")
        self.load_override()
        self._load_patch_erf()
        self._report_main_progress(f"Finished loading the installation from {self._path}")
        self._initialized = True

    def _report_main_progress(self, message: str):
        if self.progress_callback:
            self.progress_callback(message, "update_maintask_text")
            self.progress_callback(1, "increment")
        # self._log.info(message)

    # region Load Data
    def _build_single_resource(
        self,
        filepath: Path | str,
    ) -> FileResource | None:
        resource: FileResource | None = None
        try:
            if self.progress_callback:
                self.progress_callback(f"Loading '{os.path.relpath(filepath, self._path)}'", "update_subtask_text")
            resname, restype = ResourceIdentifier.from_path(filepath).unpack()
            if restype.is_invalid:
                return None
            resource = FileResource(resname, restype, os.path.getsize(filepath), 0, filepath)  # noqa: PTH202
        except Exception as e:  # noqa: BLE001
            RobustLogger().exception(f"Error loading file '{filepath}'", exc_info=e)
            return None
        return resource

    def _build_resource_list(
        self,
        filepath: Path | str,
        capsule_check: Callable,
    ) -> list[FileResource] | None:
        resource_list: list[FileResource] | None = None
        try:
            if not capsule_check(filepath):
                return None
            if self.progress_callback:
                self.progress_callback(f"Indexing capsule '{os.path.relpath(filepath, self._path)}'", "update_subtask_text")
            resource_list = list(Capsule(filepath))
        except Exception as e:  # noqa: BLE001
            RobustLogger().error(f"Error loading file '{filepath}'", exc_info=e)
            return None
        return resource_list

    def load_resources_dict(
        self,
        path: str | Path,
        capsule_check: Callable,
        *,
        recurse: bool = False,
    ) -> dict[str, list[FileResource]]:
        """Load resources for a given path and store them in a new dict.

        Args:
        ----
            path (os.PathLike | str): path for lookup.
            recurse (bool): whether to recurse into subfolders (default is False)
            capsule_check (Callable returns bool): If the check doesn't pass, the resource isn't added.

        Returns:
        -------
            dict[str, list[FileResource]]: A dict keyed by filename to the encapsulated resources
        """
        r_path = Path(path)
        if not r_path.is_dir():
            self._log.info("The '%s' folder did not exist when loading the installation at '%s', skipping...", r_path.name, self._path)
            return {}

        self._log.info("Loading '%s' from installation...", r_path.relative_to(self._path))
        files_iter = r_path.rglob("*") if recurse else r_path.iterdir()

        resources_dict: dict[str, list[FileResource]] = {}
        str_path = str(r_path)

        for file in files_iter:
            resource_list = self._build_resource_list(file, capsule_check)
            if resource_list is None:
                continue
            resources_dict[file.name] = resource_list
        if not resources_dict:
            RobustLogger().warning(f"No resources found at '{str_path}' when loading the installation, skipping...")
        return resources_dict

    def load_resources_list(
        self,
        path: str | Path,
        *,
        recurse: bool = False,
    ) -> list[FileResource]:
        """Load resources for a given path and store them in a new list.

        Args:
        ----
            path (os.PathLike | str): path for lookup.
            recurse (bool): whether to recurse into subfolders (default is False)

        Returns:
        -------
            list[FileResource]: The list where resources at the path have been stored.
        """
        r_path = Path(path)
        if not r_path.is_dir():
            self._log.info("The '%s' folder did not exist when loading the installation at '%s', skipping...", r_path.name, self._path)
            return []

        self._log.info("Loading '%s' from installation...", r_path.relative_to(self._path))
        files_iter = r_path.rglob("*") if recurse else r_path.iterdir()

        resources_list: list[FileResource] = []
        str_path = str(r_path)
        RobustLogger().info(f"Loading '{os.path.relpath(str_path, self._path)}' from installation...")

        try:
            for entry in os.scandir(str_path):
                try:
                    if recurse and entry.is_dir(follow_symlinks=False):
                        resources_list.extend(self.load_resources_list(entry.path, recurse=True))
                    elif entry.is_file():
                        resource: FileResource | None = self._build_single_resource(entry.path)
                        if resource is not None:
                            resources_list.append(resource)
                except Exception as e:  # noqa: PERF203, BLE001
                    RobustLogger().warning(f"Error processing file '{entry.path}'", exc_info=e)
        except Exception as e:  # noqa: BLE001
            RobustLogger().exception(f"Error scanning directory '{str_path}'", exc_info=e)

        for file in files_iter:
            resource = self._build_single_resource(file)
            if resource is None:
                continue
            resources_list.append(resource)
        if not resources_list:
            RobustLogger().warning(f"No resources found at '{str_path}' when loading the installation, skipping...")
        return resources_list

    def load_chitin(self):
        """Reloads the list of resources in the Chitin linked to the Installation."""
        if self._chitin_loaded:
            return
        chitin_path: CaseAwarePath = self._path / "chitin.key"
        chitin_exists: bool | None = chitin_path.is_file()
        if chitin_exists:
            self._log.info("Loading BIFs from chitin.key at '%s'...", self._path)
            self._chitin_data = list(Chitin(key_path=chitin_path))
            self._log.info("Done loading chitin")
        elif chitin_exists is False:
            RobustLogger().warning(f"The chitin.key file did not exist at '{self._path}', skipping...")
        elif chitin_exists is None:
            self._log.error("No permissions to the chitin.key file at '%s' when loading the installation, skipping...", self._path)
        self._chitin_loaded = True

    def load_lips(
        self,
    ):
        """Reloads the list of modules in the lips folder linked to the Installation."""
        if self._lips_loaded:
            return
        self._lips_data = self.load_resources_dict(self.lips_path(), capsule_check=is_mod_file)
        self._lips_loaded = True

    def load_modules(self):
        """Reloads the list of modules files in the modules folder linked to the Installation."""
        if self._modules_loaded:
            return
        self._modules_data = self.load_resources_dict(self.module_path(), capsule_check=is_capsule_file)
        self._modules_loaded = True

    def reload_module(self, module: str):
        """Reloads the list of resources in specified module in the modules folder linked to the Installation.

        Args:
        ----
            module: The filename of the module, including the extension.
        """
        if not self._modules_loaded or module not in self._modules_data:
            self.load_modules()
        self._modules_data[module] = list(Capsule(self.module_path() / module))

    def load_textures(
        self,
    ):
        """Reloads the list of modules files in the texturepacks folder linked to the Installation."""
        if self._texturepacks_loaded:
            return
        self._texturepacks_data = self.load_resources_dict(self.texturepacks_path(), capsule_check=is_erf_file)
        self._texturepacks_loaded = True

    def load_saves(
        self,
    ):
        """Reloads the data in the 'saves' folder linked to the Installation.
        
        This method loads both:
        1. File resources for each save (for UI display)
        2. SaveFolderEntry objects (for save editing and corruption detection)
        """
        if self._saves_loaded:
            return
        self.saves = {}
        self.save_folders = {}
        for save_location in self.save_locations():
            RobustLogger().debug(f"Found an active save location at '{save_location}'")
            self.saves[save_location] = {}
            for this_save_path in save_location.iterdir():
                if not this_save_path.is_dir():
                    continue
                self.saves[save_location][this_save_path] = []
                
                # Load file resources for UI display
                for file in this_save_path.iterdir():
                    res_ident = ResourceIdentifier.from_path(file)
                    file_res = FileResource(res_ident.resname, res_ident.restype, file.stat().st_size, 0, file)
                    self.saves[save_location][this_save_path].append(file_res)
                
                # Load SaveFolderEntry for save editing and corruption detection
                try:
                    save_folder = SaveFolderEntry(str(this_save_path))
                    # Don't fully load the save yet (lazy loading) - just store the path
                    self.save_folders[this_save_path] = save_folder
                except Exception as e:  # noqa: BLE001
                    RobustLogger().warning(f"Failed to create SaveFolderEntry for '{this_save_path}': {e}")
                    
        self._saves_loaded = True

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
        override_path: Path = self.override_path()
        target_dirs: list[Path] = []
        if directory:
            target_dirs = [override_path / directory]
            self._override_data[directory] = []
        else:
            if self._override_loaded:
                return
            try:
                is_k1 = self.game().is_k1()
            except (ValueError, Exception):
                is_k1 = True
                RobustLogger().exception("Failed to get the game of your installation!")
            if is_k1:
                target_dirs = [f for f in override_path.rglob("*") if f.is_dir()]
            target_dirs.append(override_path)
            self._override_data = {}

        for folder in target_dirs:
            try:  # sourcery skip: remove-redundant-exception, simplify-single-exception-tuple
                relative_folder: str = folder.relative_to(override_path).as_posix()  # '.' if folder is the same as override_path
                self._override_data[relative_folder] = self.load_resources_list(folder, recurse=True)
            except Exception:  # noqa: BLE001
                RobustLogger().exception(f"Failed to get the relative folder of '{folder}' and '{override_path}'")

        if not directory:
            self._override_loaded = True

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
        filepath: Path = Path(file)
        parent_folder = filepath.parent
        rel_folderpath: str = str(parent_folder.relative_to(self.override_path())) if parent_folder.name else "."
        if rel_folderpath not in self._override_data:
            self.load_override(rel_folderpath)

        identifier: ResourceIdentifier = ResourceIdentifier.from_path(filepath)
        if identifier.restype is ResourceType.INVALID:
            RobustLogger().error(f"Cannot reload override file. Invalid KOTOR resource: {identifier!r}")
            return
        resource = FileResource(*identifier.unpack(), filepath.stat().st_size, 0, filepath)

        override_list: list[FileResource] = self._override_data[rel_folderpath]
        if resource not in override_list:
            override_list.append(resource)
        else:
            override_list[override_list.index(resource)] = resource

    def load_streammusic(
        self,
    ):
        """Reloads the list of resources in the streammusic folder linked to the Installation."""
        if self._streammusic_loaded:
            return
        self._streammusic_data = self.load_resources_list(self.streammusic_path())
        self._streammusic_loaded = True

    def load_streamsounds(
        self,
    ):
        """Reloads the list of resources in the streamsounds folder linked to the Installation."""
        if self._streamsounds_loaded:
            return
        self._streamsounds_data = self.load_resources_list(self.streamsounds_path())
        self._streamsounds_loaded = True

    def _quicker_load_resources(self, folder_path: Path) -> list[FileResource]:
        """streamwaves/streamvoice have tens of thousands of audio files, offload here for performance reasons.

        More or less executes exactly the same as load_resources_list/dict methods.
        """
        files: list[FileResource] = []
        try:
            if not folder_path.is_dir():
                return files
            stack: list[str] = [str(folder_path)]
            install_path_str = str(self.path())
            file_count = 0
            # Only update progress every 100 files to reduce logging overhead
            PROGRESS_UPDATE_INTERVAL = 100

            while stack:
                current_dir = stack.pop()
                with os.scandir(current_dir) as it:
                    for entry in it:
                        if entry.is_file():
                            try:
                                file_count += 1
                                # Only update progress callback periodically to reduce overhead
                                if self.progress_callback and file_count % PROGRESS_UPDATE_INTERVAL == 0:
                                    relpath = entry.path[len(install_path_str) :].strip("\\").strip("/")
                                    self.progress_callback(f"Loading '{relpath}'... ({file_count} files)", "update_subtask_text")
                                files.append(FileResource.from_path(entry.path))
                            except Exception:  # noqa: BLE001
                                self._log.exception("Error loading resource:", entry.path)
                        elif entry.is_dir():
                            stack.append(entry.path)
        except Exception:  # noqa: BLE001
            self._log.exception("Error loading resources from folder:", folder_path)
        return files

    def load_streamwaves(self):
        """Reloads the list of resources in the streamwaves folder linked to the Installation."""
        if self._streamwaves_loaded:
            return
        self._streamwaves_data[:] = self._quicker_load_resources(self._find_resource_folderpath(("streamvoice", "streamwaves")))
        self._streamwaves_loaded = True

    def load_streamvoice(self):
        """Reloads the list of resources in the streamvoice folder linked to the Installation."""
        if self._streamwaves_loaded:
            return
        self._streamwaves_data[:] = self._quicker_load_resources(self._find_resource_folderpath(("streamwaves", "streamvoice")))
        self._streamwaves_loaded = True

    def _load_patch_erf(self):
        """Loads the patch.erf file for K1 installations."""
        if self._patch_erf_loaded:
            return
        if self.game().is_k1():
            patch_erf_path = self.path().joinpath("patch.erf")
            if patch_erf_path.is_file():
                if self.progress_callback:
                    self.progress_callback("Loading patch.erf...", "update_maintask_text")
                self._patch_erf_data.extend(Capsule(patch_erf_path))
        self._patch_erf_loaded = True

    # endregion

    # region Get Paths
    def path(self) -> Path:
        """Returns the path to root folder of the Installation.

        Returns:
        -------
            The path to the root folder.
        """
        return self._path

    def module_path(self) -> Path:
        """Returns the path to modules folder of the Installation. This method maintains the case of the foldername.

        Returns:
        -------
            The path to the modules folder.
        """
        return self._find_resource_folderpath("Modules")

    def override_path(self) -> Path:
        """Returns the path to override folder of the Installation. This method maintains the case of the foldername.

        Returns:
        -------
            The path to the override folder.
        """
        return self._find_resource_folderpath("Override", optional=True)

    def lips_path(self) -> Path:
        """Returns the path to 'lips' folder of the Installation. This method maintains the case of the foldername.

        Returns:
        -------
            The path to the lips folder.
        """
        return self._find_resource_folderpath("lips")

    def texturepacks_path(self) -> Path:
        """Returns the path to 'texturepacks' folder of the Installation. This method maintains the case of the foldername.

        Returns:
        -------
            The path to the texturepacks folder.
        """
        return self._find_resource_folderpath("texturepacks", optional=True)

    def rims_path(self) -> Path:
        """Returns the path to 'rims' folder of the Installation. This method maintains the case of the foldername.

        Returns:
        -------
            The path to the rims folder.
        """
        return self._find_resource_folderpath("rims", optional=True)

    def streammusic_path(self) -> Path:
        """Returns the path to 'streammusic' folder of the Installation. This method maintains the case of the foldername.

        Returns:
        -------
            The path to the streammusic folder.
        """
        return self._find_resource_folderpath("streammusic")

    def streamsounds_path(self) -> Path:
        """Returns the path to 'streamsounds' folder of the Installation. This method maintains the case of the foldername.

        Returns:
        -------
            The path to the streamsounds folder.
        """
        return self._find_resource_folderpath("streamsounds", optional=True)

    def streamwaves_path(self) -> Path:
        """Returns the path to 'streamwaves' or 'streamvoice' folder of the Installation. This method maintains the case of the foldername.

        In the first game, this folder is named 'streamwaves'
        In the second game, this folder has been renamed to 'streamvoice'.

        Returns:
        -------
            The path to the streamwaves/streamvoice folder.
        """
        return self._find_resource_folderpath(("streamwaves", "streamvoice"))

    def streamvoice_path(self) -> Path:
        """Returns the path to 'streamvoice' or 'streamwaves' folder of the Installation. This method maintains the case of the foldername.

        In the first game, this folder is named 'streamwaves'
        In the second game, this folder has been renamed to 'streamvoice'.

        Returns:
        -------
            The path to the streamvoice/streamwaves folder.
        """
        return self._find_resource_folderpath(("streamvoice", "streamwaves"))

    def save_locations(self) -> list[Path]:
        # sourcery skip: assign-if-exp, extract-method
        """Returns a list of existing save locations (paths where save files can be found)."""
        save_paths: list[Path] = [self._find_resource_folderpath("saves", optional=True)]
        if self.game().is_k2():
            cloudsave_dir = self._find_resource_folderpath("cloudsaves", optional=True)
            if cloudsave_dir.is_dir():
                for folder in cloudsave_dir.iterdir():
                    if not folder.is_dir():
                        continue
                    save_paths.append(folder)
        system = platform.system()

        if system == "Windows":
            roamingappdata_env: str = os.getenv("APPDATA", "")
            if not roamingappdata_env.strip() or not Path(roamingappdata_env).is_dir():
                roamingappdata_path = Path.home().joinpath("AppData", "Roaming")
            else:
                roamingappdata_path = Path(roamingappdata_env)

            game_folder1 = "kotor" if self.game().is_k1() else "kotor2"  # FIXME: k1 is known but k2's 'kotor2' is a guess
            save_paths.append(roamingappdata_path.joinpath("LucasArts", game_folder1, "saves"))

            localappdata_env: str = os.getenv("LOCALAPPDATA", "")
            if not localappdata_env.strip() or not Path(localappdata_env).is_dir():
                localappdata_path = Path.home().joinpath("AppData", "Local")
            else:
                localappdata_path = Path(localappdata_env)

            local_virtual_store = localappdata_path / "VirtualStore"
            game_folder2 = "SWKotOR2" if self.game().is_k2() else "SWKotOR"
            save_paths.extend(
                (
                    local_virtual_store.joinpath("Program Files", "LucasArts", game_folder2, "saves"),
                    local_virtual_store.joinpath("Program Files (x86)", "LucasArts", game_folder2, "saves"),
                )
            )

        elif system == "Darwin":  # TODO
            home = Path.home()
            save_paths.extend(
                (
                    home.joinpath("Library", "Application Support", "Star Wars Knights of the Old Republic II", "saves"),
                    home.joinpath(
                        "Library", "Containers", "com.aspyr.kotor2.appstore", "Data", "Library", "Application Support", "Star Wars Knights of the Old Republic II", "saves"
                    ),
                )
            )

        elif system == "Linux":  # TODO(th3w1zard1): Linux save paths
            xdg_data_home = os.getenv("XDG_DATA_HOME", "")
            remaining_path_parts = PurePath("aspyr-media", "kotor2", "saves")
            if xdg_data_home.strip() and CaseAwarePath(xdg_data_home).is_dir():
                save_paths.append(CaseAwarePath(xdg_data_home, remaining_path_parts))
            save_paths.append(CaseAwarePath.home().joinpath(".local", "share", remaining_path_parts))

        # Filter and return existing paths
        return [path for path in save_paths if path.is_dir()]

    def _find_resource_folderpath(
        self,
        folder_names: tuple[str, ...] | str,
        *,
        optional: bool = True,
    ) -> Path:
        """Finds the path to a resource folder.

        Args:
        ----
            folder_names: The name(s) of the folder(s) to search for.
            optional: Whether to raise an error if the folder is not found.

        Returns:
        -------
            Path: The path to the found folder.

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
                if resource_path.is_dir():
                    return resource_path
        except Exception as e:  # noqa: BLE001
            msg = f"An error occurred while finding the '{' or '.join(folder_names)}' folder in '{self._path}'."
            raise OSError(msg) from e
        else:
            if optional:
                return Path(self._path, folder_names[0])
        msg = f"Could not find the '{' or '.join(folder_names)}' folder in '{self._path}'."
        raise FileNotFoundError(msg)

    # endregion

    # region Get FileResources

    def __iter__(self) -> Generator[FileResource, Any, None]:
        # Properties will handle lazy loading
        yield from self._chitin
        yield from self._streammusic
        yield from self._streamsounds
        # Only yield from streamwaves if they're already loaded (lazy loading)
        if self._streamwaves_loaded:
            yield from self._streamwaves_data
        for resources in self._override.values():
            yield from resources
        for resources in self._modules.values():
            yield from resources
        for resources in self._lips.values():
            yield from resources
        for resources in self._texturepacks.values():
            yield from resources
        tlk_path = self._path / "dialog.tlk"
        yield FileResource("dialog", ResourceType.TLK, tlk_path.stat().st_size, 0, tlk_path)
        female_tlk_path = self._path / "dialogf.tlk"
        if female_tlk_path.is_file():
            yield FileResource("dialogf", ResourceType.TLK, female_tlk_path.stat().st_size, 0, female_tlk_path)

    def chitin_resources(self) -> list[FileResource]:
        """Returns a shallow copy of the list of FileResources stored in the Chitin linked to the Installation.

        Returns:
        -------
            A list of FileResources.
        """
        return self._chitin[:]

    def core_resources(self) -> list[FileResource]:
        """Similar to chitin_resources, but also return the resources in `patch.erf` if exists and the installation is Game.K1."""
        return self.chitin_resources() + self._patch_erf[:]

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
        """Returns a shallow copy of the list of FileResources stored in the specified module file located in the modules folder linked to the Installation.

        Module resources are cached and require a reload after the contents have been modified on disk.

        Returns:
        -------
            A list of FileResources.
        """
        if filename not in self._modules:
            print(f"Module '{filename}' not found in the installation!", file=sys.stderr)
            return []
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
        if filename not in self._lips:
            print(f"Lip '{filename}' not found in the installation!", file=sys.stderr)
            return []
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
        if filename not in self._texturepacks:
            print(f"Texturepack '{filename}' not found in the installation!", file=sys.stderr)
            return []
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
        # If asking for specific directory and it's not loaded, load it
        if directory and directory not in self._override:
            self.load_override(directory)
        # If asking for all and nothing is loaded, load everything
        elif not directory and not self._override:
            self.load_override()

        return (
            self._override[directory] if directory else [override_resource for ov_subfolder_name in self._override for override_resource in self._override[ov_subfolder_name]]
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
        from pykotor.tools.heuristics import determine_game
        return determine_game(path)

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
        order: Sequence[SearchLocation] | None = None,
        *,
        capsules: Sequence[Capsule] | None = None,
        folders: list[Path] | None = None,
        module_root: str | None = None,
        logger: Callable[[str], None] | None = None,
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
            module_root: The root name of the module to search in. (e.g. "danm13") (Optional)
            logger: A logger to use for logging. (Optional)

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
            module_root=module_root,
            logger=logger,
        )
        search: ResourceResult | None = batch[query]
        if search is None:
            # Use debug level for texture resources (TPC/TGA) as missing textures are expected when browsing
            if query.restype in (ResourceType.TPC, ResourceType.TGA):
                RobustLogger().debug(f"Could not find '{query}' during resource lookup.")
            else:
                RobustLogger().warning(f"Could not find '{query}' during resource lookup.")
            return None
        return search

    def resources(
        self,
        queries: list[ResourceIdentifier] | tuple[Sequence[str], Sequence[ResourceType]],
        order: Sequence[SearchLocation] | None = None,
        *,
        capsules: Sequence[LazyCapsule] | None = None,
        folders: list[Path] | None = None,
        module_root: str | None = None,
        logger: Callable[[str], None] | None = None,
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
            module_root: The root name of the module to search in. (e.g. "danm13") (Optional)
            logger: A logger to use for logging. (Optional)

        Returns:
        -------
            A dictionary mapping the given items in the queries argument to a list of ResourceResult objects.
        """
        order_list: list[SearchLocation] | None = list(order) if order is not None else []
        results: dict[ResourceIdentifier, ResourceResult | None] = {}
        locations: dict[ResourceIdentifier, list[LocationResult]] = self.locations(
            queries,
            order_list,
            capsules=capsules,
            folders=folders,
            module_root=module_root,
            logger=logger,
        )

        handles: dict[ResourceIdentifier, io.BufferedReader] = {}

        for query in queries:
            assert isinstance(query, ResourceIdentifier), f"{type(query).__name__}: {query}"
            location_list: list[LocationResult] = locations.get(query, [])

            if not location_list:
                # Use debug level for texture resources (TPC/TGA) as missing textures are expected when browsing
                if query.restype in (ResourceType.TPC, ResourceType.TGA):
                    RobustLogger().debug(f"Resource not found: '{query}'")
                else:
                    RobustLogger().warning(f"Resource not found: '{query}'")
                results[query] = None
                continue

            location: LocationResult = location_list[0]

            if query not in handles:
                handles[query] = location.filepath.open("rb")

            handle: io.BufferedReader = handles[query]
            handle.seek(location.offset)
            data: bytes = handle.read(location.size)

            result = ResourceResult(
                query.resname,
                query.restype,
                location.filepath,
                data,
            )
            result.set_file_resource(FileResource(query.resname, query.restype, location.size, location.offset, location.filepath))
            results[query] = result

        # Close all open handles
        for handle in handles.values():
            handle.close()

        return results

    @overload
    def location(self, file: os.PathLike | str, order: Sequence[SearchLocation] | None = None, /, *, capsules: list[Capsule] | None = None, folders: list[Path] | None = None) -> list[LocationResult]: ...
    @overload
    def location(self, query: ResourceIdentifier, order: Sequence[SearchLocation] | None = None, /, *, capsules: list[Capsule] | None = None, folders: list[Path] | None = None) -> list[LocationResult]: ...
    @overload
    def location(self, resname: str, restype: ResourceType | None = None, order: Sequence[SearchLocation] | None = None, /, *, capsules: list[Capsule] | None = None, folders: list[Path] | None = None) -> list[LocationResult]: ...
    @overload
    def location(
        self,
        query: ResourceIdentifier,
        order: Sequence[SearchLocation] | None = None,
        /,
        *,
        capsules: list[Capsule] | None = None,
        folders: list[Path] | None = None,
        module_root: str | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> list[LocationResult]: ...
    @overload
    def location(
        self,
        resname: str,
        restype: ResourceType,
        order: Sequence[SearchLocation] | None = None,
        /,
        *,
        capsules: list[Capsule] | None = None,
        folders: list[Path] | None = None,
        module_root: str | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> list[LocationResult]: ...
    def location(
        self,
        resname: str | os.PathLike | ResourceIdentifier,
        restype: ResourceType | Sequence[SearchLocation] | None = None,
        order: Sequence[SearchLocation] | None = None,
        /,
        *,
        capsules: list[Capsule] | None = None,
        folders: list[Path] | None = None,
        module_root: str | None = None,
        logger: Callable[[str], None] | None = None,
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
            module_root: The root name of the module to search in. (e.g. "danm13") (Optional)
            logger: A logger to use for logging. (Optional)

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
        order_list: list[SearchLocation] | None = list(order) if order is not None else []
        query: ResourceIdentifier

        if isinstance(restype, list) or restype is None:
            if isinstance(resname, (os.PathLike, str)):
                query = ResourceIdentifier.from_path(resname)
            elif isinstance(resname, ResourceIdentifier):
                query = resname
            else:
                raise TypeError(
                    f"Invalid argument at position 0. Expected filename or filepath (os.PathLike | str), got {resname} ({resname!r}) of type {resname.__class__.__name__}"
                )
        elif isinstance(restype, ResourceType):
            assert isinstance(resname, (str, ResRef)), f"resname must be a string or ResRef, got {resname} ({resname!r}) of type {resname.__class__.__name__}"
            query = ResourceIdentifier(str(resname), restype)
        else:
            raise TypeError(f"Invalid argument at position 1. Expected ResourceType, got {restype} ({restype!r}) of type {restype.__class__.__name__}")

        return self.locations(
            [query],
            order_list,
            capsules=capsules,
            folders=folders,
            module_root=module_root,
            logger=logger,
        )[query]

    @overload
    def locations(
        self,
        queries: list[ResourceIdentifier],
        order: list[SearchLocation] | None = None,
        *,
        capsules: Sequence[LazyCapsule] | None = None,
        folders: list[Path] | None = None,
        module_root: str | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> dict[ResourceIdentifier, list[LocationResult]]: ...
    @overload
    def locations(
        self,
        queries: tuple[Sequence[str], Sequence[ResourceIdentifier] | Sequence[ResourceType]],
        order: list[SearchLocation] | None = None,
        *,
        capsules: Sequence[LazyCapsule] | None = None,
        folders: list[Path] | None = None,
        module_root: str | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> dict[ResourceIdentifier, list[LocationResult]]: ...
    def locations(
        self,
        queries: list[ResourceIdentifier] | tuple[Sequence[str], Sequence[ResourceType] | Sequence[ResourceIdentifier]],
        order: list[SearchLocation] | None = None,
        *,
        capsules: Sequence[LazyCapsule] | None = None,
        folders: list[Path] | None = None,
        module_root: str | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> dict[ResourceIdentifier, list[LocationResult]]:
        """Returns a dictionary mapping the items provided in the queries argument to a list of locations for that respective resource.

        Args:
        ----
            queries: A list of resources to try locate.
            order: The ordered list of locations to check.
            capsules: An extra list of capsules to search in.
            folders: An extra list of folders to search in.
            module_root: The root name of the module to search in. (e.g. "danm13") (Optional)
            logger: A logger to use for logging. (Optional)

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

        # Log the search if logger is provided
        if logger and len(queries) == 1:
            query = next(iter(queries)) if isinstance(queries, set) else queries[0]
            if isinstance(query, ResourceIdentifier):
                logger(f"Installation-wide search for '{query}':")
                logger("  Checking each location:")

        real_queries: set[ResourceIdentifier] = set()

        if isinstance(queries, tuple):
            resnames, restypes = queries
            for resname, restype in itertools.product(resnames, restypes):
                real_queries.add(ResourceIdentifier(resname, restype if isinstance(restype, ResourceType) else restype.restype))
        else:
            real_queries.update(queries)

        locations: dict[ResourceIdentifier, list[LocationResult]] = {}
        for qident in real_queries:
            locations[qident] = []

        def check_dict(resource_dict: dict[str, list[FileResource]] | CaseInsensitiveDict[list[FileResource]]):
            for resource_list in resource_dict.values():
                check_list(resource_list)

        def check_list(resource_list: list[FileResource]):
            # Index resources by identifier
            lookup_dict: dict[ResourceIdentifier, FileResource] = {resource.identifier(): resource for resource in resource_list}

            for query in real_queries:
                resource = lookup_dict.get(query)
                if resource is None:
                    continue
                location = LocationResult(
                    resource.filepath(),
                    resource.offset(),
                    resource.size(),
                )
                location.set_file_resource(resource)
                locations[query].append(location)

        def check_capsules(values: Sequence[LazyCapsule]):
            for capsule in values:
                for query in real_queries:
                    resource: FileResource | None = capsule.info(*query.unpack())
                    if resource is None:
                        continue

                    location = LocationResult(
                        resource.filepath(),
                        resource.offset(),
                        resource.size(),
                    )
                    location.set_file_resource(resource)
                    locations[resource.identifier()].append(location)

        def check_folders(resource_folders: list[Path]):
            for folder in resource_folders:
                for file in folder.rglob("*"):
                    if not file.is_file():
                        continue
                    identifier = ResourceIdentifier.from_path(file)
                    if identifier not in real_queries:
                        continue

                    location = LocationResult(
                        filepath=file,
                        offset=0,
                        size=file.stat().st_size,
                    )

                    location.set_file_resource(FileResource(identifier.resname, identifier.restype, location.size, location.offset, location.filepath))
                    locations[identifier].append(location)

        def check_modules():
            if module_root is None:
                # No module filter, search all modules
                check_dict(self._modules)
            else:
                # Filter modules by root name
                filtered_modules = {filename: resources for filename, resources in self._modules.items() if self.get_module_root(filename) == module_root.lower()}
                check_dict(filtered_modules)

        function_map: dict[SearchLocation, Callable] = {
            SearchLocation.OVERRIDE: lambda: check_dict(self._override),
            SearchLocation.MODULES: check_modules,
            SearchLocation.LIPS: lambda: check_dict(self._lips),
            SearchLocation.TEXTURES_TPA: lambda: check_list(self._texturepacks[TexturePackNames.TPA.value]),
            SearchLocation.TEXTURES_TPB: lambda: check_list(self._texturepacks[TexturePackNames.TPB.value]),
            SearchLocation.TEXTURES_TPC: lambda: check_list(self._texturepacks[TexturePackNames.TPC.value]),
            SearchLocation.TEXTURES_GUI: lambda: check_list(self._texturepacks[TexturePackNames.GUI.value]),
            SearchLocation.CHITIN: lambda: check_list(self._chitin) or check_list(self._patch_erf),
            SearchLocation.MUSIC: lambda: check_list(self._streammusic),
            SearchLocation.SOUND: lambda: check_list(self._streamsounds),
            SearchLocation.VOICE: lambda: check_list(self._streamwaves),
            SearchLocation.CUSTOM_MODULES: lambda: check_capsules(capsules),  # type: ignore[arg-type]
            SearchLocation.CUSTOM_FOLDERS: lambda: check_folders(folders),  # type: ignore[arg-type]
        }

        for i, item in enumerate(order, 1):
            assert isinstance(item, SearchLocation), f"{type(item).__name__}: {item}"

            # Track locations before searching this item
            before_count = 0
            if logger and len(queries) == 1:
                query = next(iter(queries)) if isinstance(queries, set) else queries[0]
                if isinstance(query, ResourceIdentifier):
                    before_count = len(locations.get(query, []))

            function_map.get(item, lambda: None)()

            # Log results after searching this item
            if logger and len(queries) == 1:
                query = next(iter(queries)) if isinstance(queries, set) else queries[0]
                if isinstance(query, ResourceIdentifier):
                    after_locations = locations.get(query, [])
                    location_names = {
                        SearchLocation.CUSTOM_FOLDERS: "Custom folders",
                        SearchLocation.OVERRIDE: "Override folders",
                        SearchLocation.CUSTOM_MODULES: "Custom modules",
                        SearchLocation.MODULES: "Module capsules",
                        SearchLocation.CHITIN: "Chitin BIFs",
                        SearchLocation.TEXTURES_TPA: "Texture pack TPA",
                        SearchLocation.TEXTURES_TPB: "Texture pack TPB",
                        SearchLocation.TEXTURES_TPC: "Texture pack TPC",
                        SearchLocation.TEXTURES_GUI: "Texture pack GUI",
                        SearchLocation.RIMS: "RIM files",
                        SearchLocation.LIPS: "LIP files",
                        SearchLocation.MUSIC: "StreamMusic",
                        SearchLocation.SOUND: "StreamSounds",
                        SearchLocation.VOICE: "StreamWaves/StreamVoice",
                    }
                    description = location_names.get(item, str(item))

                    new_locations = after_locations[before_count:]
                    if new_locations:
                        for j, location_result in enumerate(new_locations):
                            # Format the filepath relative to installation root for readability
                            try:
                                rel_path = location_result.filepath.relative_to(self._path)
                            except ValueError:
                                rel_path = location_result.filepath
                            # Show SELECTED for the first location found (highest priority)
                            if before_count == 0 and j == 0:
                                logger(f"    {i}. {description} -> FOUND at {rel_path} -> SELECTED")
                            else:
                                logger(f"    {i}. {description} -> FOUND at {rel_path}")
                    else:
                        # Only log "not found" if this location type was actually checked
                        # Skip logging for CUSTOM_FOLDERS if no folders were provided
                        # Skip logging for CUSTOM_MODULES if no capsules were provided
                        if item == SearchLocation.CUSTOM_FOLDERS and not folders:
                            continue
                        if item == SearchLocation.CUSTOM_MODULES and not capsules:
                            continue
                        logger(f"    {i}. {description} -> not found")

        return locations

    def texture(
        self,
        resname: str,
        order: Sequence[SearchLocation] | None = None,
        *,
        capsules: Sequence[Capsule] | None = None,
        folders: list[Path] | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> TPC | None:
        """Returns a TPC object loaded from a resource with the specified name.

        This is a wrapper of the textures() method provided to make searching for a single texture more convenient.

        If the specified texture could not be found then the method returns None.

        Texture is searched using the following default order:
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
        batch: CaseInsensitiveDict[TPC | None] = self.textures([resname], order, capsules=capsules, folders=folders, logger=logger)
        return batch[resname] if batch else None

    def textures(
        self,
        resnames: Iterable[str],
        order: Sequence[SearchLocation] | None = None,
        *,
        capsules: Sequence[Capsule] | None = None,
        folders: list[Path] | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> CaseInsensitiveDict[TPC | None]:
        """Returns a dictionary mapping the items provided in the queries argument to a TPC object if it exists.

        If the texture could not be found then the value is None.

        Args:
        ----
            resnames: A list of case-insensitive resource names (without the extensions) to try locate.
            order: The ordered list of locations to check.
            capsules: An extra list of capsules to search in.
            folders: An extra list of folders to search in.
            logger: A logger to use for logging. (Optional)

        Returns:
        -------
            A dictionary mapping case-insensitive strings to TPC objects or None.
        """
        if order is None:
            order = (
                SearchLocation.CUSTOM_FOLDERS,
                SearchLocation.OVERRIDE,
                SearchLocation.CUSTOM_MODULES,
                SearchLocation.TEXTURES_TPA,
                SearchLocation.CHITIN,
            )
        resnames = set(resnames)
        case_resnames: set[str] = {resname.lower() for resname in resnames}
        capsules = [] if capsules is None else capsules
        folders = [] if folders is None else folders

        textures: CaseInsensitiveDict[TPC | None] = CaseInsensitiveDict()
        texture_types: tuple[ResourceType, ...] = (ResourceType.TPC, ResourceType.TGA)

        for resname in resnames:
            textures[resname] = None

        def decode_txi(txi_bytes: bytes) -> str:
            return txi_bytes.decode("ascii", errors="ignore").strip()

        def get_txi_from_list(case_resname: str, resource_list: list[FileResource]) -> str:
            txi_resource: FileResource | None = next(
                (resource for resource in resource_list if resource.restype() is ResourceType.TXI and resource.identifier().lower_resname == case_resname),
                None,
            )
            if txi_resource is not None:
                RobustLogger().debug("Found txi resource '%s' at %s", txi_resource.identifier(), txi_resource.filepath().relative_to(self._path.parent))
                contents = decode_txi(txi_resource.data())
                if contents and not contents.isascii():
                    RobustLogger().warning("Texture TXI '%s' is not ascii! (found at %s)", txi_resource.identifier(), txi_resource.filepath())
                return contents
            RobustLogger().debug("'%s.txi' resource not found during texture lookup.", case_resname)
            return ""

        def check_dict(values: dict[str, list[FileResource]]):
            for resources in values.values():
                check_list(resources)

        def check_list(resource_list: list[FileResource]):
            for resource in resource_list:
                if resource.restype() not in texture_types:
                    continue
                case_resname = resource.identifier().lower_resname
                if case_resname not in case_resnames:
                    continue
                case_resnames.remove(case_resname)
                tpc: TPC = read_tpc(resource.data())
                if resource.restype() is ResourceType.TGA:
                    tpc.txi = get_txi_from_list(case_resname, resource_list)
                textures[case_resname] = tpc

        def check_capsules(values: Sequence[LazyCapsule]):  # NOTE: This function does not support txi's in the Override folder.
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
                    if tformat is ResourceType.TGA:
                        tpc.txi = get_txi_from_list(case_resname, capsule.resources())
                    textures[case_resname] = tpc

        def check_folders(resource_folders: list[Path]):
            queried_texture_files: set[Path] = set()
            for folder in resource_folders:
                queried_texture_files.update(
                    file
                    for file in folder.rglob("*")
                    if (file.stem.casefold() in case_resnames and ResourceType.from_extension(file.suffix) in texture_types and file.is_file())
                )
            for texture_file in queried_texture_files:
                case_resnames.remove(texture_file.stem.casefold())
                try:
                    textures[texture_file.stem] = read_tpc(texture_file)
                except (OSError, ValueError):
                    RobustLogger().warning(f"Invalid/corrupted texture file: {texture_file}")
                    continue

        function_map: dict[SearchLocation, Callable] = {
            SearchLocation.OVERRIDE: lambda: check_dict(self._override),
            SearchLocation.MODULES: lambda: check_dict(self._modules),
            SearchLocation.TEXTURES_TPA: lambda: check_list(self._texturepacks[TexturePackNames.TPA.value]),
            SearchLocation.TEXTURES_TPB: lambda: check_list(self._texturepacks[TexturePackNames.TPB.value]),
            SearchLocation.TEXTURES_TPC: lambda: check_list(self._texturepacks[TexturePackNames.TPC.value]),
            SearchLocation.TEXTURES_GUI: lambda: check_list(self._texturepacks[TexturePackNames.GUI.value]),
            SearchLocation.CHITIN: lambda: check_list(self._chitin) or check_list(self._patch_erf),
            SearchLocation.CUSTOM_MODULES: lambda: check_capsules(capsules),
            SearchLocation.CUSTOM_FOLDERS: lambda: check_folders(folders),
        }

        for item in order:
            assert isinstance(item, SearchLocation), f"{type(item).__name__}: {item}"
            function_map.get(item, lambda: None)()

        return textures

    def sound(
        self,
        resname: str,
        order: Sequence[SearchLocation] | None = None,
        *,
        capsules: list[Capsule] | None = None,
        folders: list[Path] | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> bytes | None:
        """Returns the bytes of a sound resource if it can be found, otherwise returns None.

        This is a wrapper of the sounds() method provided to make searching for a single resource more convenient.

        Args:
        ----
            resname: The case-insensitive name of the sound (without the extension) to look for.
            order: The ordered list of locations to check.
            capsules: An extra list of capsules to search in.
            folders: An extra list of folders to search in.
            logger: A logger to use for logging. (Optional)

        Returns:
        -------
            A bytes object or None.
        """
        batch: CaseInsensitiveDict[bytes | None] = self.sounds([resname], order, capsules=capsules, folders=folders, logger=logger)
        return batch[resname] if batch else None

    def sounds(
        self,
        resnames: Iterable[str],
        order: Sequence[SearchLocation] | None = None,
        *,
        capsules: list[Capsule] | None = None,
        folders: list[Path] | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> CaseInsensitiveDict[bytes | None]:
        """Returns a dictionary mapping the items provided in the resnames argument to a bytes object if the respective sound resource could be found.

        If the sound could not be found the value will return None.

        Args:
        ----
            resnames: A list of case-insensitive sound names (without the extensions) to try locate.
            order: The ordered list of locations to check.
            capsules: An extra list of capsules to search in.
            folders: An extra list of folders to search in.
            logger: A logger to use for logging. (Optional)

        Returns:
        -------
            A dictionary mapping a case-insensitive string to a bytes object or None.
        """
        resnames_set = set(resnames)
        case_resnames: set[str] = {resname.casefold() for resname in resnames_set}
        capsules = [] if capsules is None else capsules
        folders = [] if folders is None else folders
        if order is None:
            order = (
                SearchLocation.CUSTOM_FOLDERS,
                SearchLocation.OVERRIDE,
                SearchLocation.CUSTOM_MODULES,
                SearchLocation.SOUND,
                SearchLocation.CHITIN,
            )

        sounds: CaseInsensitiveDict[bytes | None] = CaseInsensitiveDict()
        sound_formats: list[ResourceType] = [ResourceType.WAV, ResourceType.MP3]

        for resname in resnames_set:
            sounds[resname] = None

        def check_dict(values: dict[str, list[FileResource]]):
            for resources in values.values():
                check_list(resources)

        def check_list(values: list[FileResource]):
            for resource in values:
                if resource.restype() not in sound_formats:
                    continue
                case_resname = resource.identifier().lower_resname
                if case_resname not in case_resnames:
                    continue
                RobustLogger().debug("Found sound at '%s'", resource.filepath())
                case_resnames.remove(case_resname)
                sound_data: bytes = resource.data()
                from io import BytesIO
                try:
                    wav = read_wav(BytesIO(sound_data))
                    sounds[resource.resname()] = bytes_wav(wav, ResourceType.INVALID)
                except (ValueError, OSError) as e:
                    RobustLogger().warning("Failed to load WAV file '%s': %s", resource.filepath(), e)
                    # Skip invalid WAV files instead of crashing
                    continue

        def check_capsules(values: Sequence[LazyCapsule]):
            for capsule in values:
                for case_resname in copy(case_resnames):
                    sound_data: bytes | None = None
                    for sformat in sound_formats:
                        sound_data = capsule.resource(case_resname, sformat)
                        if sound_data is not None:  # Break after first match found. Note that this means any other formats in this list will be ignored
                            break
                    if sound_data is None:  # No sound data found in this list.
                        continue
                    RobustLogger().debug("Found sound resource in capsule at '%s'", capsule.filepath())
                    case_resnames.remove(case_resname)
                    from io import BytesIO
                    try:
                        wav = read_wav(BytesIO(sound_data))
                        sounds[case_resname] = bytes_wav(wav, ResourceType.INVALID)
                    except (ValueError, OSError) as e:
                        RobustLogger().warning("Failed to load WAV file from capsule '%s': %s", capsule.filepath(), e)
                        # Skip invalid WAV files instead of crashing
                        continue

        def check_folders(values: list[Path]):
            queried_sound_files: set[Path] = set()
            for folder in values:
                queried_sound_files.update(
                    file
                    for file in folder.rglob("*")
                    if (file.stem.casefold() in case_resnames and ResourceType.from_extension(file.suffix) in sound_formats and file.is_file())
                )
            for sound_file in queried_sound_files:
                RobustLogger().debug("Found sound file resource at '%s'", sound_file)
                case_resnames.remove(sound_file.stem.casefold())
                sound_data: bytes = sound_file.read_bytes()
                from io import BytesIO
                try:
                    wav = read_wav(BytesIO(sound_data))
                    sounds[sound_file.stem] = bytes_wav(wav, ResourceType.INVALID)
                except (ValueError, OSError) as e:
                    RobustLogger().warning("Failed to load WAV file '%s': %s", sound_file, e)
                    # Skip invalid WAV files instead of crashing
                    continue

        function_map: dict[SearchLocation, Callable] = {
            SearchLocation.OVERRIDE: lambda: check_dict(self._override),
            SearchLocation.MODULES: lambda: check_dict(self._modules),
            SearchLocation.CHITIN: lambda: check_list(self._chitin) or check_list(self._patch_erf),
            SearchLocation.MUSIC: lambda: check_list(self._streammusic),
            SearchLocation.SOUND: lambda: check_list(self._streamsounds),
            SearchLocation.VOICE: lambda: check_list(self._streamwaves),
            SearchLocation.CUSTOM_MODULES: lambda: check_capsules(capsules),
            SearchLocation.CUSTOM_FOLDERS: lambda: check_folders(folders),  # type: ignore[arg-type]
        }

        for item in order:
            assert isinstance(item, SearchLocation), f"{type(item).__name__}: {item}"
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
        female_batch: dict[int, StringResult] = self.female_talktable().batch(stringrefs) if self.female_talktable().path().is_file() else {}

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
    @lru_cache(maxsize=1000)
    def get_module_root(module_filepath: os.PathLike | str) -> str:
        root: str = PurePath(module_filepath).stem.lower()
        root = root[:-2] if root.endswith("_s") else root
        root = root[:-4] if root.endswith("_dlg") else root
        return root  # noqa: RET504

    def module_names(self, *, use_hardcoded: bool = True) -> dict[str, str | None]:
        """Returns a dictionary mapping module filename to the name of the area.

        The name is taken from the LocalizedString "Name" in the relevant module file's ARE resource.

        Returns:
        -------
            A dictionary mapping module filename to in-game module area name.
        """
        area_names: dict[str, str | None] = {}
        root_to_extensions: dict[str, dict[str, str | None]] = {}

        for module in self._modules:
            lower_module = module.lower()
            root = self.get_module_root(lower_module)
            lower_root = root.lower()
            qualifier = lower_module[len(root) :]

            if lower_root not in root_to_extensions:
                root_to_extensions[lower_root] = {".rim": None, ".mod": None, "_s.rim": None, "_dlg.erf": None}

            if qualifier not in root_to_extensions[lower_root]:
                RobustLogger().warning(f"No area name found for lonewolf capsule 'Modules/{module}'")
                continue
            root_to_extensions[lower_root][qualifier] = module

        for extensions in root_to_extensions.values():
            mod_filename = extensions[".mod"]
            rim_link = extensions[".rim"] or mod_filename
            if rim_link:
                area_name = self.module_name(rim_link)
                area_names[rim_link] = area_name

                dlg_erf_filename = extensions["_dlg.erf"]
                if dlg_erf_filename is not None and dlg_erf_filename not in area_names:
                    area_names[dlg_erf_filename] = area_name
                _s_rim_filename = extensions["_s.rim"]
                if _s_rim_filename is not None and _s_rim_filename not in area_names:
                    area_names[_s_rim_filename] = area_name

            if rim_link != mod_filename and mod_filename is not None:
                area_names[mod_filename] = self.module_name(mod_filename)

        return area_names

    def module_ids(
        self,
        *,
        use_hardcoded: bool = True,
        use_alternate: bool = False,
    ) -> dict[str, str]:
        module_idents: dict[str, str] = {}
        root_to_extensions: dict[str, dict[str, str | None]] = {}

        for module in self._modules:
            lower_module = module.lower()
            root = self.get_module_root(lower_module)
            lower_root = root.lower()
            qualifier = lower_module[len(root) :]

            if lower_root not in root_to_extensions:
                root_to_extensions[lower_root] = {".rim": None, ".mod": None, "_s.rim": None, "_dlg.erf": None}

            if qualifier not in root_to_extensions[lower_root]:
                RobustLogger().warning(f"No id found for lonewolf capsule 'Modules/{module}'")
                continue
            root_to_extensions[lower_root][qualifier] = module

        for extensions in root_to_extensions.values():
            mod_filename = extensions[".mod"]
            rim_link = extensions[".rim"] or mod_filename
            if rim_link:
                area_name = self.module_id(rim_link)
                module_idents[rim_link] = area_name
                dlg_erf_filename = extensions["_dlg.erf"]
                if dlg_erf_filename is not None and dlg_erf_filename not in module_idents:
                    module_idents[dlg_erf_filename] = area_name
                _s_rim_filename = extensions["_s.rim"]
                if _s_rim_filename is not None and _s_rim_filename not in module_idents:
                    module_idents[_s_rim_filename] = area_name

            if rim_link != mod_filename and mod_filename is not None:
                module_idents[mod_filename] = self.module_id(mod_filename)

        return module_idents

    def module_name(
        self,
        module_filename: str,
        *,
        use_hardcoded: bool = True,
    ) -> str | None:
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
        root: str = self.get_module_root(module_filename)
        upper_root: str = root.upper()
        if use_hardcoded and upper_root in HARDCODED_MODULE_NAMES:
            return HARDCODED_MODULE_NAMES[upper_root]
        try:
            module_path: Path = self.module_path()
            if not is_mod_file(module_filename):
                relevant_capsule = Capsule(module_path.joinpath(f"{root}.rim"))
            else:
                relevant_capsule = Capsule(module_path.joinpath(module_filename))
        except Exception:  # noqa: BLE001
            RobustLogger().exception(f"Could not build capsule for 'Modules/{module_filename}'")
            return root

        area_resource: FileResource | None = next((resource for resource in relevant_capsule.resources() if resource.restype() is ResourceType.ARE), None)
        try:
            if area_resource is not None:
                are: GFF = read_gff(area_resource.data())
                if are.root.exists("Name"):
                    actual_ftype = are.root.what_type("Name")
                    if actual_ftype is not GFFFieldType.LocalizedString:
                        RobustLogger().warning(f"{area_resource.filename()} has incorrect field 'Name' type '{actual_ftype.name}', expected type 'List'")
                    locstring: LocalizedString | None = are.root.get_locstring("Name")
                    if locstring is None:
                        RobustLogger().warning(f"{area_resource.filename()} has incorrect field 'Name' type '{actual_ftype.name}', expected type 'LocalizedString'")
                        return ""
                    if locstring.stringref == -1:
                        return locstring.get(Language.ENGLISH, Gender.MALE) or ""
                    return self.talktable().string(locstring.stringref)
        except Exception:  # noqa: BLE001
            RobustLogger().exception(f"Could not read ARE for '{module_filename}'")
            return root
        return ""

    def module_id(
        self,
        module_filename: str,
        *,
        use_hardcoded: bool = True,
        use_alternate: bool = False,
    ) -> str:  # sourcery skip: assign-if-exp, remove-unreachable-code
        """Returns an identifier for the module that matches the filename/IFO/ARE resname.

        NOTE: Since this is only used for sorting currently, does not parse Mod_Area_list or Mod_VO_ID.

        Args:
        ----
            module_filename: str - The name of the module file.
            use_hardcoded: bool - Deprecated (does nothing)
            use_alternate: bool - Gets the ID that matches the part of the filename. Only really useful for sorting. Normally this function returns the ID name that matches the existing ARE/GIT resources.

        Returns:
        -------
            The ID of the area for the module.
        """  # noqa: E501
        root: str = self.get_module_root(module_filename)

        try:

            @lru_cache(maxsize=1000)
            def quick_id(filename: str) -> str:
                base_name: str = filename.rsplit(".")[0]  # Strip extension
                if len(base_name) >= 6 and base_name[3:4].lower() == "m" and base_name[4:6].isdigit():  # e.g. 'danm13', 'manm26mg'...  # noqa: PLR2004
                    base_name = f"{base_name[:3]}_{base_name[3:]}"
                parts: list[str] = base_name.split("_")

                mod_id = base_name  # If there are no underscores, return the base name itself
                if len(parts) == 2:  # noqa: PLR2004
                    # If there's exactly one underscore, return the part after the underscore
                    if parts[1] in ("s", "dlg"):
                        mod_id = parts[0]
                    else:  # ...except when the part after matches a qualifier
                        mod_id = parts[1]
                elif len(parts) >= 3:  # noqa: PLR2004
                    # If there are three or more underscores, return what's between the first two underscores
                    if parts[-1].lower() in ("s", "dlg"):
                        mod_id = "_".join(parts[1:-1])
                    else:  # ...except when the last part matches a qualifier
                        mod_id = "_".join(parts[1:-2])
                # self._log.debug("parts: %s id: '%s'", parts, mod_id)
                return mod_id

            if use_alternate:
                return quick_id(module_filename).lower()
        except Exception:  # noqa: BLE001
            RobustLogger().exception(f"Could not quick ID capsule '{module_filename}'")
            return root

        try:
            module_path: Path = self.module_path()
            if not is_mod_file(module_filename):
                relevant_capsule = Capsule(module_path.joinpath(f"{root}.rim"))
            else:
                relevant_capsule = Capsule(module_path.joinpath(module_filename))
        except Exception:  # noqa: BLE001
            RobustLogger().exception(f"Could not build capsule for 'Modules/{module_filename}'")
            return root

        try:
            return next(
                (resource.resname() for resource in relevant_capsule.resources() if resource.restype() is ResourceType.GIT),
                next((resource.resname() for resource in relevant_capsule.resources() if resource.restype() is ResourceType.ARE), quick_id(module_filename)),
            )
        except Exception:  # noqa: BLE001
            RobustLogger().exception("Error occurred while recursing nested resources in func module_id()")
            return root
