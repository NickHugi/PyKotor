from __future__ import annotations

import itertools
import os
import platform
import sys

from contextlib import suppress
from copy import copy
from functools import lru_cache
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Any, Callable, Generator, Iterable, Sequence, TypeVar, overload

from loggerplus import RobustLogger
from qtpy.QtCore import (
    QPoint,
    Qt,
    Slot,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QImage, QPixmap, QTransform
from qtpy.QtWidgets import (
    QAction,  # pyright: ignore[reportPrivateImportUsage]
    QComboBox,
    QLineEdit,
    QMenu,
)

from pykotor.common.language import Gender, Language, LocalizedString
from pykotor.extract.capsule import Capsule
from pykotor.extract.chitin import Chitin
from pykotor.extract.file import FileResource, LocationResult, ResourceIdentifier, ResourceResult
from pykotor.extract.installation import HARDCODED_MODULE_NAMES, SearchLocation, TexturePackNames
from pykotor.extract.talktable import TalkTable
from pykotor.resource.formats.gff.gff_auto import read_gff
from pykotor.resource.formats.gff.gff_data import GFFContent, GFFFieldType, GFFList, GFFStruct
from pykotor.resource.formats.tpc.tpc_auto import read_tpc
from pykotor.resource.formats.tpc.tpc_data import TPC
from pykotor.resource.formats.twoda import TwoDA
from pykotor.resource.formats.twoda.twoda_auto import read_2da
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_capsule_file, is_erf_file, is_mod_file, is_rim_file
from pykotor.tools.sound import deobfuscate_audio
from toolset.utils.window import add_window
from utility.common.more_collections import CaseInsensitiveDict

if TYPE_CHECKING:
    import io

    from qtpy.QtWidgets import QPlainTextEdit
    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from pykotor.common.misc import Game
    from pykotor.extract.capsule import LazyCapsule
    from pykotor.extract.talktable import StringResult
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.formats.tpc.tpc_data import TPCMipmap
    from pykotor.resource.formats.twoda.twoda_data import TwoDA
    from pykotor.resource.generics.uti import UTI

T = TypeVar("T")


class HTInstallation:
    """A specialized Installation class that extends the base Installation class with toolset-related functionality.

    While Installation is intending to load all resources from an installation immediately, HTInstallation
    adds additional caching and loading methods for resources.

    Ideally we want all IO to be non-blocking and asynchronous, and load resources as they are needed in the processpoolexecutor.
    """

    TwoDA_PORTRAITS: Literal["portraits"] = "portraits"
    TwoDA_APPEARANCES: Literal["appearance"] = "appearance"
    TwoDA_SUBRACES: Literal["subrace"] = "subrace"
    TwoDA_SPEEDS: Literal["creaturespeed"] = "creaturespeed"
    TwoDA_SOUNDSETS: Literal["soundset"] = "soundset"
    TwoDA_FACTIONS: Literal["repute"] = "repute"
    TwoDA_GENDERS: Literal["gender"] = "gender"
    TwoDA_PERCEPTIONS: Literal["ranges"] = "ranges"
    TwoDA_CLASSES: Literal["classes"] = "classes"
    TwoDA_FEATS: Literal["feat"] = "feat"
    TwoDA_POWERS: Literal["spells"] = "spells"
    TwoDA_BASEITEMS: Literal["baseitems"] = "baseitems"
    TwoDA_PLACEABLES: Literal["placeables"] = "placeables"
    TwoDA_DOORS: Literal["genericdoors"] = "genericdoors"
    TwoDA_CURSORS: Literal["cursors"] = "cursors"
    TwoDA_TRAPS: Literal["traps"] = "traps"
    TwoDA_RACES: Literal["racialtypes"] = "racialtypes"
    TwoDA_SKILLS: Literal["skills"] = "skills"
    TwoDA_UPGRADES: Literal["upgrade"] = "upgrade"
    TwoDA_ENC_DIFFICULTIES: Literal["encdifficulty"] = "encdifficulty"
    TwoDA_ITEM_PROPERTIES: Literal["itempropdef"] = "itempropdef"
    TwoDA_IPRP_PARAMTABLE: Literal["iprp_paramtable"] = "iprp_paramtable"
    TwoDA_IPRP_COSTTABLE: Literal["iprp_costtable"] = "iprp_costtable"
    TwoDA_IPRP_ABILITIES: Literal["iprp_abilities"] = "iprp_abilities"
    TwoDA_IPRP_ALIGNGRP: Literal["iprp_aligngrp"] = "iprp_aligngrp"
    TwoDA_IPRP_COMBATDAM: Literal["iprp_combatdam"] = "iprp_combatdam"
    TwoDA_IPRP_DAMAGETYPE: Literal["iprp_damagetype"] = "iprp_damagetype"
    TwoDA_IPRP_PROTECTION: Literal["iprp_protection"] = "iprp_protection"
    TwoDA_IPRP_ACMODTYPE: Literal["iprp_acmodtype"] = "iprp_acmodtype"
    TwoDA_IPRP_IMMUNITY: Literal["iprp_immunity"] = "iprp_immunity"
    TwoDA_IPRP_SAVEELEMENT: Literal["iprp_saveelement"] = "iprp_saveelement"
    TwoDA_IPRP_SAVINGTHROW: Literal["iprp_savingthrow"] = "iprp_savingthrow"
    TwoDA_IPRP_ONHIT: Literal["iprp_onhit"] = "iprp_onhit"
    TwoDA_IPRP_AMMOTYPE: Literal["iprp_ammotype"] = "iprp_ammotype"
    TwoDA_IPRP_MONSTERHIT: Literal["iprp_mosterhit"] = "iprp_mosterhit"
    TwoDA_IPRP_WALK: Literal["iprp_walk"] = "iprp_walk"
    TwoDA_EMOTIONS: Literal["emotion"] = "emotion"
    TwoDA_EXPRESSIONS: Literal["facialanim"] = "facialanim"
    TwoDA_VIDEO_EFFECTS: Literal["videoeffects"] = "videoeffects"
    TwoDA_DIALOG_ANIMS: Literal["dialoganimations"] = "dialoganimations"
    TwoDA_PLANETS: Literal["planetary"] = "planetary"
    TwoDA_PLOT: Literal["plot"] = "plot"
    TwoDA_CAMERAS: Literal["camerastyle"] = "camerastyle"

    def __init__(
        self,
        path: str | os.PathLike,
        name: str,
        *,
        tsl: bool | None = None,
        progress_callback: Callable[[int | str, Literal["set_maximum", "increment", "update_maintask_text", "update_subtask_text"]], Any] | None = None,
    ):
        self.name: str = name
        self._tsl: bool | None = tsl
        self._cache2da: dict[str, TwoDA] = {}
        self._cache_tpc: dict[str, TPC] = {}
        self._path: Path = Path(path)

        self._talktable: TalkTable = TalkTable(self._path / "dialog.tlk")
        self._female_talktable: TalkTable = TalkTable(self._path / "dialogf.tlk")

        self._modules: dict[str, list[FileResource]] = {}
        self._lips: dict[str, list[FileResource]] = {}
        self.saves: dict[Path, dict[Path, list[FileResource]]] = {}
        self._texturepacks: dict[str, list[FileResource]] = {}
        self._rims: dict[str, list[FileResource]] = {}

        self._override: dict[str, list[FileResource]] = {}

        self._patch_erf: list[FileResource] = []  # K1 only patch.erf file
        self._chitin: list[FileResource] = []
        self._streammusic: list[FileResource] = []
        self._streamsounds: list[FileResource] = []
        self._streamwaves: list[FileResource] = []
        self._game: Game | None = None

        self._initialized = False
        self.progress_callback: Callable[[int | str, Literal["set_maximum", "increment", "update_maintask_text", "update_subtask_text"]], Any] | None = progress_callback
        self.reload_all()

    def reload_all(self):
        if self.progress_callback is not None:
            self.progress_callback(9, "set_maximum")
        self._report_main_progress("Loading chitin...")
        self.load_chitin()
        self._report_main_progress("Loading lips...")
        self.load_lips()
        self._report_main_progress("Loading modules...")
        self.load_modules()
        # K1 doesn't actually use the RIMs in the Rims folder.
        # if self.game().is_k1():
        #    self.load_rims()
        #self._report_main_progress("Loading streammusic...")
        #self.load_streammusic()
        #self._report_main_progress("Loading streamsounds...")
        #self.load_streamsounds()
        #self._report_main_progress("Loading textures...")
        self.load_textures()
        self._report_main_progress("Loading saves...")
        self.load_saves()
        #if self.game().is_k1():
        #    self._report_main_progress("Loading streamwaves...")
        #    self.load_streamwaves()
        #elif self.game().is_k2():
        #    self._report_main_progress("Loading streamvoice...")
        #    self.load_streamvoice()
        self._report_main_progress("Loading override...")
        self.load_override()
        if self.game().is_k1():
            patch_erf_path = self.path().joinpath("patch.erf")
            if patch_erf_path.is_file():
                RobustLogger().info(f"Game is K1 and 'patch.erf' found at {patch_erf_path.relative_to(self._path.parent)}")
                self._patch_erf.extend(Capsule(patch_erf_path))
        self._report_main_progress(f"Finished loading the installation from {self._path}")
        self._initialized = True

    def _report_main_progress(self, message: str):
        if self.progress_callback:
            self.progress_callback(message, "update_maintask_text")
            self.progress_callback(1, "increment")
        RobustLogger().info(message)

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
        str_path = os.fspath(path)
        if not os.path.exists(str_path) or not os.path.isdir(str_path):  # noqa: PTH110, PTH112
            RobustLogger().info(f"The '{os.path.basename(str_path)}' folder did not exist when loading the installation at '{self._path}', skipping...")  # noqa: PTH119
            return {}

        RobustLogger().info(f"Loading '{os.path.relpath(str_path, self._path)}' from installation...")
        resources_dict: dict[str, list[FileResource]] = {}

        try:
            for entry in os.scandir(str_path):
                try:
                    if recurse and entry.is_dir(follow_symlinks=False):
                        resources_dict.update(self.load_resources_dict(entry.path, capsule_check, recurse=True))
                    elif entry.is_file():
                        reslist: list[FileResource] | None = self._build_resource_list(entry.path, capsule_check)
                        if reslist is not None:
                            resources_dict[entry.name] = reslist
                except Exception as e:  # noqa: PERF203, BLE001
                    RobustLogger().warning(f"Error processing file '{entry.path}'", exc_info=e)
        except Exception as e:  # noqa: BLE001
            RobustLogger().error(f"Error scanning directory '{str_path}'", exc_info=e)

        if not resources_dict:
            RobustLogger().warning(f"No resources found at '{str_path}' when loading the installation, skipping...")
        return resources_dict

    def load_resources_list(
        self,
        path: str | Path,
        *,
        recurse: bool = False,
    ) -> list[FileResource]:
        str_path = os.fspath(path)
        if not os.path.exists(str_path) or not os.path.isdir(str_path):  # noqa: PTH110, PTH112
            RobustLogger().info(f"The '{os.path.basename(str_path)}' folder did not exist when loading the installation at '{self._path}', skipping...")  # noqa: PTH119
            return []

        resources_list: list[FileResource] = []
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

        if not resources_list:
            RobustLogger().warning(f"No resources found at '{str_path}' when loading the installation, skipping...")
        return resources_list

    def load_chitin(self):
        """Reloads the list of resources in the Chitin linked to the Installation."""
        chitin_path: Path = self._path / "chitin.key"
        chitin_exists: bool | None = chitin_path.is_file()
        if chitin_exists:
            RobustLogger().info(f"Loading BIFs from chitin.key at '{self._path}'...")
            self._chitin = list(Chitin(key_path=chitin_path))
            RobustLogger().info(f"Loaded {len(self._chitin)} BIF resources from chitin.key at '{self._path}'")
        elif chitin_exists is False:
            RobustLogger().warning(f"The chitin.key file did not exist at '{self._path}', skipping...")
        elif chitin_exists is None:
            RobustLogger().error(f"No permissions to the chitin.key file at '{self._path}', skipping...")

    def load_lips(
        self,
    ):
        """Reloads the list of modules in the lips folder linked to the Installation."""
        self._lips = self.load_resources_dict(self.lips_path(), capsule_check=is_mod_file)

    def load_modules(self):
        """Reloads the list of modules files in the modules folder linked to the Installation."""
        self._modules = self.load_resources_dict(self.module_path(), capsule_check=is_capsule_file)

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
        self._rims = self.load_resources_dict(self.rims_path(), capsule_check=is_rim_file)

    def load_textures(
        self,
    ):
        """Reloads the list of modules files in the texturepacks folder linked to the Installation."""
        self._texturepacks = self.load_resources_dict(self.texturepacks_path(), capsule_check=is_erf_file)

    def load_saves(
        self,
    ):
        """Reloads the data in the 'saves' folder linked to the Installation."""
        self.saves.clear()
        for save_location in self.save_locations():
            RobustLogger().debug(f"Found an active save location at '{save_location}'")
            self.saves[save_location] = {}
            for this_save_path in save_location.iterdir():
                if not this_save_path.is_dir():
                    continue
                self.saves[save_location][this_save_path] = []
                for file in this_save_path.iterdir():
                    res_ident = ResourceIdentifier.from_path(file)
                    file_res = FileResource(res_ident.resname, res_ident.restype, file.stat().st_size, 0, file)
                    self.saves[save_location][this_save_path].append(file_res)

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
            self._override[directory] = []
        else:
            try:
                is_k1 = self.game().is_k1()
            except (ValueError, Exception):
                is_k1 = True
                RobustLogger().exception("Failed to get the game of your installation!")
            if is_k1:
                target_dirs = [f for f in override_path.rglob("*") if f.is_dir()]
            target_dirs.append(override_path)
            self._override.clear()

        for folder in target_dirs:
            try:  # sourcery skip: remove-redundant-exception, simplify-single-exception-tuple
                relative_folder: str = folder.relative_to(override_path).as_posix()  # '.' if folder is the same as override_path
            except Exception:  # noqa: BLE001
                RobustLogger().exception(f"Failed to get the relative folder of '{folder}' and '{override_path}'")
                relative_folder = folder.as_posix()
            self._override[relative_folder] = self.load_resources_list(folder, recurse=True)

    def reload_override_file(
        self,
        file: os.PathLike | str,
    ):
        filepath: Path = Path(file)
        parent_folder = filepath.parent
        rel_folderpath: str = str(parent_folder.relative_to(self.override_path())) if parent_folder.name else "."
        if rel_folderpath not in self._override:
            self.load_override(rel_folderpath)

        identifier: ResourceIdentifier = ResourceIdentifier.from_path(filepath)
        if identifier.restype is ResourceType.INVALID:
            RobustLogger().error(f"Cannot reload override file. Invalid KOTOR resource: {identifier!r}")
            return
        resource = FileResource(*identifier.unpack(), filepath.stat().st_size, 0, filepath)

        override_list: list[FileResource] = self._override[rel_folderpath]
        if resource not in override_list:
            override_list.append(resource)
        else:
            override_list[override_list.index(resource)] = resource

    def load_streammusic(
        self,
    ):
        """Reloads the list of resources in the streammusic folder linked to the Installation."""
        self._streammusic[:] = self.load_resources_list(self.streammusic_path())

    def load_streamsounds(
        self,
    ):
        """Reloads the list of resources in the streamsounds folder linked to the Installation."""
        self._streamsounds[:] = self.load_resources_list(self.streamsounds_path())

    def load_streamwaves(self):
        """Reloads the list of resources in the streamwaves folder linked to the Installation."""
        self._streamwaves[:] = self.load_resources_list(self._find_resource_folderpath(("streamvoice", "streamwaves")), recurse=True)

    def load_streamvoice(self):
        """Reloads the list of resources in the streamvoice folder linked to the Installation."""
        self._streamwaves[:] = self.load_resources_list(self._find_resource_folderpath(("streamwaves", "streamvoice")), recurse=True)

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

        elif system == "Linux":  # TODO
            xdg_data_home = os.getenv("XDG_DATA_HOME", "")
            remaining_path_parts = PurePath("aspyr-media", "kotor2", "saves")
            if xdg_data_home.strip() and Path(xdg_data_home).is_dir():
                save_paths.append(Path(xdg_data_home, remaining_path_parts))
            save_paths.append(Path.home().joinpath(".local", "share", remaining_path_parts))

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
                resource_path: Path = self._path / folder_name
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
        if not self._override or directory and directory not in self._override:
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
        if search is None:
            RobustLogger().warning(f"Could not find '{query}' during resource lookup.")
            return None
        return search

    def resources(
        self,
        queries: list[ResourceIdentifier] | set[ResourceIdentifier],
        order: Sequence[SearchLocation] | None = None,
        *,
        capsules: Sequence[LazyCapsule] | None = None,
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

        handles: dict[ResourceIdentifier, io.BufferedReader] = {}

        for query in queries:
            location_list: list[LocationResult] = locations.get(query, [])

            if not location_list:
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
    def location(
        self, file: os.PathLike | str, order: Sequence[SearchLocation] | None = None, /, *, capsules: list[Capsule] | None = None, folders: list[Path] | None = None
    ) -> list[LocationResult]: ...
    @overload
    def location(
        self, query: ResourceIdentifier, order: Sequence[SearchLocation] | None = None, /, *, capsules: list[Capsule] | None = None, folders: list[Path] | None = None
    ) -> list[LocationResult]: ...
    @overload
    def location(
        self,
        resname: str,
        restype: ResourceType | None = None,
        order: Sequence[SearchLocation] | None = None,
        /,
        *,
        capsules: list[Capsule] | None = None,
        folders: list[Path] | None = None,
    ) -> list[LocationResult]: ...
    def location(
        self,
        resname: str,
        restype: ResourceType | None = None,
        order: Sequence[SearchLocation] | None = None,
        /,
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
        query: ResourceIdentifier

        if isinstance(restype, list) or restype is None:
            order = order if restype is None else restype
            if isinstance(resname, (os.PathLike, str)):
                query = ResourceIdentifier.from_path(resname)
            elif isinstance(resname, ResourceIdentifier):
                query = resname
            else:
                raise TypeError(
                    f"Invalid argument at position 0. Expected filename or filepath (os.PathLike | str), got {resname} ({resname!r}) of type {resname.__class__.__name__}"
                )
        elif isinstance(restype, ResourceType):
            query = ResourceIdentifier(resname, restype)
        else:
            raise TypeError(f"Invalid argument at position 1. Expected ResourceType, got {restype} ({restype!r}) of type {restype.__class__.__name__}")

        return self.locations(
            [query],
            order,
            capsules=capsules,
            folders=folders,
        )[query]

    def locations(
        self,
        queries: list[ResourceIdentifier] | tuple[Sequence[str], Sequence[ResourceType]],
        order: Sequence[SearchLocation] | None = None,
        *,
        capsules: Sequence[Capsule] | None = None,
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
            order = (
                SearchLocation.CUSTOM_FOLDERS,
                SearchLocation.OVERRIDE,
                SearchLocation.CUSTOM_MODULES,
                SearchLocation.MODULES,
                SearchLocation.CHITIN,
            )
        capsules = [] if capsules is None else capsules
        folders = [] if folders is None else folders

        real_queries: set[ResourceIdentifier] = set()

        if isinstance(queries, tuple):
            resnames, restypes = queries
            for resname, restype in itertools.product(resnames, restypes):
                real_queries.add(ResourceIdentifier(resname, restype))
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
            lookup_dict = {resource.identifier(): resource for resource in resource_list}
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

        def check_capsules(values: list[Capsule]):
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

        function_map: dict[SearchLocation, Callable] = {
            SearchLocation.OVERRIDE: lambda: check_dict(self._override),
            SearchLocation.MODULES: lambda: check_dict(self._modules),
            SearchLocation.LIPS: lambda: check_dict(self._lips),
            SearchLocation.RIMS: lambda: check_dict(self._rims),
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

        for item in order:
            assert isinstance(item, SearchLocation), f"{type(item).__name__}: {item}"
            function_map.get(item, lambda: None)()

        return locations

    def texture(
        self,
        resname: str,
        order: Sequence[SearchLocation] | None = None,
        *,
        capsules: Sequence[Capsule] | None = None,
        folders: list[Path] | None = None,
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
        batch: CaseInsensitiveDict[TPC | None] = self.textures([resname], order, capsules=capsules, folders=folders)
        return batch[resname] if batch else None

    def textures(
        self,
        resnames: Iterable[str],
        order: Sequence[SearchLocation] | None = None,
        *,
        capsules: Sequence[Capsule] | None = None,
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

        def check_capsules(values: Sequence[Capsule]):  # NOTE: This function does not support txi's in the Override folder.
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
            SearchLocation.RIMS: lambda: check_dict(self._rims),
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

    def find_tlk_entry_references(
        self,
        query_stringref: int,
        order: Sequence[SearchLocation] | None = None,
        *,
        capsules: list[Capsule] | None = None,
        folders: list[Path] | None = None,
    ) -> set[FileResource]:
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
            order = (
                SearchLocation.CUSTOM_FOLDERS,
                SearchLocation.OVERRIDE,
                SearchLocation.CUSTOM_MODULES,
                SearchLocation.CHITIN,
                SearchLocation.RIMS,
                SearchLocation.MODULES,
            )

        found_resources: set[FileResource] = set()
        gff_extensions: set[str] = GFFContent.get_extensions()
        relevant_2da_filenames: dict[str, set[str]] = {}
        from pykotor.extract.twoda import K1Columns2DA, K2Columns2DA

        if self.game().is_k1():  # TODO(th3w1zard1): TSL:
            relevant_2da_filenames = K1Columns2DA.StrRefs.as_dict()
        elif self.game().is_k2():
            relevant_2da_filenames = K2Columns2DA.StrRefs.as_dict()

        def check_2da(resource2da: FileResource) -> bool:
            valid_2da: TwoDA | None = None
            with suppress(ValueError, OSError):
                valid_2da = read_2da(resource2da.data())
            if not valid_2da:
                print(f"'{resource2da._path_ident_obj}' cannot be loaded, probably corrupted.")  # noqa: SLF001
                return False
            filename_2da = resource2da.filename().lower()
            for column_name in relevant_2da_filenames[filename_2da]:
                if column_name == ">>##HEADER##<<":
                    for header in valid_2da.get_headers():
                        try:
                            stripped_header = header.strip()
                            if not stripped_header.isdigit():
                                if stripped_header and stripped_header not in ("****", "*****", "-1"):
                                    RobustLogger().warning(f"header '{header}' in '{filename_2da}' is invalid, expected a stringref number.")
                                continue
                            if int(stripped_header) == query_stringref:
                                return True
                        except Exception as e:  # noqa: BLE001
                            RobustLogger().error("Error parsing '%s' header '%s': %s", filename_2da, header, str(e), exc_info=False)
                else:
                    try:
                        for i, cell in enumerate(valid_2da.get_column(column_name)):
                            stripped_cell = cell.strip()
                            if not stripped_cell.isdigit():
                                if stripped_cell and stripped_cell not in ("****", "*****", "-1"):
                                    RobustLogger().warning(
                                        f"column '{column_name}' rowindex {i} in '{filename_2da}' is invalid, expected a stringref number. Instead got '{cell}'"
                                    )
                                continue
                            if int(stripped_cell) == query_stringref:
                                return True
                    except Exception as e:  # noqa: BLE001
                        RobustLogger().error("Error parsing '%s' column '%s': %s", filename_2da, column_name, str(e), exc_info=False)
            return False

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
                if resource.filename().lower() in relevant_2da_filenames and this_restype is ResourceType.TwoDA and check_2da(resource):
                    found_resources.add(resource)
                if this_restype.extension not in gff_extensions:
                    continue
                valid_gff: GFF | None = try_get_gff(resource.data())
                if not valid_gff:
                    continue
                if not recurse_gff_structs(valid_gff.root):
                    continue
                found_resources.add(resource)

        def check_capsules(capsules_list: list[Capsule]):
            for capsule in capsules_list:
                for resource in capsule.resources():
                    this_restype: ResourceType = resource.restype()
                    if resource.filename().lower() in relevant_2da_filenames and this_restype is ResourceType.TwoDA and check_2da(resource):
                        found_resources.add(resource)
                    if this_restype.extension not in gff_extensions:
                        continue
                    valid_gff: GFF | None = try_get_gff(resource.data())
                    if not valid_gff:
                        continue
                    if not recurse_gff_structs(valid_gff.root):
                        continue
                    found_resources.add(resource)

        def check_folders(values: list[Path]):
            relevant_files: set[Path] = set()
            for folder in values:  # Having two loops makes it easier to filter out irrelevant files when stepping through the 2nd
                relevant_files.update(
                    file
                    for file in folder.rglob("*")
                    if (
                        file.suffix
                        and (file.suffix[1:].casefold() in gff_extensions or (file.name.lower() in relevant_2da_filenames and file.suffix.casefold() == ".2da"))
                        and file.is_file()
                    )
                )
            for gff_file in relevant_files:
                restype: ResourceType | None = ResourceType.from_extension(gff_file.suffix)
                if not restype:
                    continue
                fileres = FileResource(resname=gff_file.stem, restype=restype, size=gff_file.stat().st_size, offset=0, filepath=gff_file)
                if restype is ResourceType.TwoDA and check_2da(fileres):
                    found_resources.add(fileres)
                else:
                    gff_data = gff_file.read_bytes()
                    valid_gff: GFF | None = None
                    with suppress(ValueError, OSError):
                        valid_gff = read_gff(gff_data)
                    if not valid_gff:
                        continue
                    if not recurse_gff_structs(valid_gff.root):
                        continue
                    found_resources.add(fileres)

        function_map: dict[SearchLocation, Callable] = {
            SearchLocation.OVERRIDE: lambda: check_dict(self._override),
            SearchLocation.MODULES: lambda: check_dict(self._modules),
            SearchLocation.RIMS: lambda: check_dict(self._rims),
            SearchLocation.CHITIN: lambda: check_list(self._chitin) or check_list(self._patch_erf),
            SearchLocation.CUSTOM_MODULES: lambda: check_capsules(capsules),
            SearchLocation.CUSTOM_FOLDERS: lambda: check_folders(folders),  # type: ignore[arg-type]
        }

        for item in order:
            assert isinstance(item, SearchLocation), f"{type(item).__name__}: {item}"
            function_map.get(item, lambda: None)()

        return found_resources

    def sound(
        self,
        resname: str,
        order: Sequence[SearchLocation] | None = None,
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
        resnames: Iterable[str],
        order: Sequence[SearchLocation] | None = None,
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
        resnames_set: set[str] = set(resnames)
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
                sounds[resource.resname()] = deobfuscate_audio(sound_data)

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
                    RobustLogger().debug("Found sound resource in capsule at '%s'", capsule.filepath())
                    case_resnames.remove(case_resname)
                    sounds[case_resname] = deobfuscate_audio(sound_data)

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
                sounds[sound_file.stem] = deobfuscate_audio(sound_data)

        function_map: dict[SearchLocation, Callable] = {
            SearchLocation.OVERRIDE: lambda: check_dict(self._override),
            SearchLocation.MODULES: lambda: check_dict(self._modules),
            SearchLocation.RIMS: lambda: check_dict(self._rims),
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

    def module_names(self, *, use_hardcoded: bool = True) -> dict[str, str]:
        """Returns a dictionary mapping module filename to the name of the area.

        The name is taken from the LocalizedString "Name" in the relevant module file's ARE resource.

        Returns:
        -------
            A dictionary mapping module filename to in-game module area name.
        """
        area_names: dict[str, str] = {}
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

        area_resource = next((resource for resource in relevant_capsule.resources() if resource.restype() is ResourceType.ARE), None)
        try:
            if area_resource is not None:
                are = read_gff(area_resource.data())
                if are.root.exists("Name"):
                    actual_ftype = are.root.what_type("Name")
                    if actual_ftype is not GFFFieldType.LocalizedString:
                        RobustLogger().warning(f"{area_resource.filename()} has incorrect field 'Name' type '{actual_ftype.name}', expected type 'List'")
                    locstring: LocalizedString = are.root.get_locstring("Name")
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
        """
        root: str = self.get_module_root(module_filename)

        try:

            @lru_cache(maxsize=1000)
            def quick_id(filename: str) -> str:
                base_name: str = filename.rsplit(".")[0]  # Strip extension
                if len(base_name) >= 6 and base_name[3:4].lower() == "m" and base_name[4:6].isdigit():  # e.g. 'danm13', 'manm26mg'...
                    base_name = f"{base_name[:3]}_{base_name[3:]}"
                parts: list[str] = base_name.split("_")

                mod_id = base_name  # If there are no underscores, return the base name itself
                if len(parts) == 2:
                    # If there's exactly one underscore, return the part after the underscore
                    if parts[1] in ("s", "dlg"):
                        mod_id = parts[0]
                    else:  # ...except when the part after matches a qualifier
                        mod_id = parts[1]
                elif len(parts) >= 3:
                    # If there are three or more underscores, return what's between the first two underscores
                    if parts[-1].lower() in ("s", "dlg"):
                        mod_id = "_".join(parts[1:-1])
                    else:  # ...except when the last part matches a qualifier
                        mod_id = "_".join(parts[1:-2])
                # RobustLogger().debug("parts: %s id: '%s'", parts, mod_id)
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

    # region qt-specific code
    def setup_file_context_menu(
        self,
        widget: QPlainTextEdit | QLineEdit | QComboBox,
        resref_type: list[ResourceType] | list[ResourceIdentifier],
        order: list[SearchLocation] | None = None,
    ):
        from toolset.gui.dialogs.load_from_location_result import ResourceItems

        @Slot(QPoint)
        def extend_context_menu(pos: QPoint):
            root_menu = QMenu(widget) if isinstance(widget, QComboBox) else widget.createStandardContextMenu()
            widget_text: str = (
                widget.currentText().strip() if isinstance(widget, QComboBox) else (widget.text() if isinstance(widget, QLineEdit) else widget.toPlainText()).strip()
            )

            build_file_context_menu(root_menu, widget_text)
            root_menu.exec(widget.mapToGlobal(pos))

        def build_file_context_menu(root_menu: QMenu, widget_text: str):
            """Build and populate a file context menu for the given widget text.

            This function creates a "File..." submenu in the root menu, populates it with
            file locations based on the widget text, and adds a "Details..." action.

            Args:
                rootMenu (QMenu): The parent menu to which the file submenu will be added.
                pos (QPoint): The position where the menu should be displayed.
                widgetText (str): The text from the widget used to search for file locations.
            """
            file_menu = QMenu("File...", widget)
            root_menu.addMenu(file_menu)
            root_menu.addSeparator()

            search_order: list[SearchLocation] = order or [SearchLocation.CHITIN, SearchLocation.OVERRIDE, SearchLocation.MODULES, SearchLocation.RIMS]
            resource_types: list[ResourceType] | list[ResourceIdentifier] = resref_type if isinstance(resref_type[0], ResourceType) else resref_type
            # FIXME(th3w1zard1): Seems the type hinter override's for `locations` are wrong, need to fix
            locations: dict[str, list[LocationResult]] = self.locations(
                ([widget_text], resource_types),  # pyright: ignore[reportArgumentType, reportAssignmentType]
                search_order,
            )
            flat_locations: list[LocationResult] = [item for sublist in locations.values() for item in sublist] if isinstance(locations, dict) else locations

            if flat_locations:
                for location in flat_locations:
                    display_path: Path = location.filepath.relative_to(self.path())
                    file_resource: FileResource = location.as_file_resource()
                    if file_resource.inside_bif:
                        display_path /= file_resource.filename()
                    location_menu: QMenu | None = file_menu.addMenu(str(display_path))
                    ResourceItems(resources=[location]).build_menu(location_menu, self)

                details_action = QAction("Details...", file_menu)
                details_action.triggered.connect(lambda: self._open_details(flat_locations))
                file_menu.addAction(details_action)
            else:
                file_menu.setDisabled(True)

            for action in root_menu.actions():
                if action.text() == "File...":
                    action.setText(f"{len(flat_locations)} file(s) located")
                    break

        widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        widget.customContextMenuRequested.connect(extend_context_menu)

    @Slot(list)
    def _open_details(self, locations: list[LocationResult]):
        from toolset.gui.dialogs.load_from_location_result import FileSelectionWindow

        selection_window = FileSelectionWindow(locations, self)
        selection_window.show()
        selection_window.activateWindow()
        add_window(selection_window)

    @Slot(list)
    def handle_file_system_changes(self, changed_files: list[str]):
        """Handle file system changes and update caches accordingly.

        This function handles changes in the file system by clearing specific caches
        based on the changed files. It ensures that the caches are updated correctly
        when files are modified, added, or removed.

        Args:
            changed_files (list[str]): A list of file paths that have changed.
        """
        lower_install_path = str(self._path).lower()
        lower_lips_path = str(self.lips_path()).lower()
        lower_module_path = str(self.module_path()).lower()
        lower_override_path = str(self.override_path()).lower()
        lower_rims_path = str(self.rims_path()).lower()
        lower_streammusic_path = str(self.streammusic_path()).lower()
        lower_streamsounds_path = str(self.streamsounds_path()).lower()
        lower_streamwaves_path = str(self._find_resource_folderpath(("streamvoice", "streamwaves"))).lower()
        lower_texturepacks_path = str(self.texturepacks_path()).lower()
        lower_save_locations: list[str] = [str(save_loc).lower() for save_loc in self.save_locations()]

        for path in changed_files:
            lower_path: str = path.lower()
            if lower_path == lower_install_path:
                self._clear_cache("chitin")
            elif lower_lips_path in lower_path:
                self._clear_cache("lips")
            elif lower_module_path in lower_path:
                self._clear_cache("modules")
            elif lower_override_path in lower_path:
                self._clear_cache("override")
            elif lower_rims_path in lower_path:
                self._clear_cache("rims")
            elif any(save_loc in lower_path for save_loc in lower_save_locations):
                self._clear_cache("saves")
            elif lower_streammusic_path in lower_path:
                self._clear_cache("streammusic")
            elif lower_streamsounds_path in lower_path:
                self._clear_cache("streamsounds")
            elif lower_streamwaves_path in lower_path:
                self._clear_cache("streamwaves")
            elif lower_texturepacks_path in lower_path:
                self._clear_cache("texturepacks")
            else:
                RobustLogger().warning(f"Unhandled file change: '{path}'")

    # region Cache 2DA
    def ht_get_cache_2da(self, resname: str) -> TwoDA | None:
        """Gets a 2DA resource from the cache or loads it if not present.

        Args:
        ----
            resname: The name of the 2DA resource to retrieve

        Returns:
        -------
            2DA: The retrieved 2DA data

        Processing Logic:
        ----------------
            - Check if the 2DA is already cached
            - If not cached, retrieve the 2DA data from the resource system
            - Parse and cache the retrieved 2DA data
            - Return the cached 2DA data.
        """
        resname = resname.lower()
        if resname not in self._cache2da:
            result: ResourceResult | None = self.resource(resname, ResourceType.TwoDA, [SearchLocation.OVERRIDE, SearchLocation.CHITIN])
            if result is None:
                return None
            self._cache2da[resname] = read_2da(result.data)
        return self._cache2da[resname]

    def get_relevant_resources(self, restype: ResourceType, src_filepath: Path | None = None) -> set[FileResource]:
        """Get relevant resources for a given resource type and source filepath.

        This function retrieves relevant resources based on the specified resource type
        and an optional source file path. It uses the installation's resources and caches
        to determine which resources are relevant.

        Args:
        ----
            restype (ResourceType): The type of resource to retrieve.
            src_filepath (PurePath | None): The source file path to use for determining relevant resources.

        Returns:
        -------
            set[FileResource]: A set of relevant resources.

        Processing Logic:
        ----------------
            - If no source file path is provided, return all resources of the specified type.
            - If a source file path is provided, check if it is inside the module or override folder.
            - If inside module, add all resources of the specified type from the module.
            - If inside override, add all resources of the specified type from the override.
            - Return the set of relevant resources.
        """
        from pykotor.common.module import Module

        if src_filepath is None:
            return {res for res in self if res.restype() is restype}

        relevant_resources: set[FileResource] = {res for res in (*self.override_resources(), *self.chitin_resources()) if res.restype() is restype}

        if os.path.commonpath([src_filepath.absolute(), self.module_path()]) == self.module_path():
            relevant_resources.update(res for cap in Module.get_capsules_tuple_matching(self, src_filepath.name) for res in cap if res.restype() is restype)
        elif os.path.commonpath([src_filepath.absolute(), self.override_path()]) == self.override_path():
            relevant_resources.update(
                res for reslist in self._modules.values() if any(r.identifier() == src_filepath.name for r in reslist) for res in reslist if res.restype() is restype
            )  # noqa: E501

        return relevant_resources

    def ht_batch_cache_2da(self, resnames: list[str], *, reload: bool = False):
        """Cache 2D array resources in batch.

        Args:
        ----
            resnames: List of resource names to cache
            reload: Whether to reload cached resources

        Processing Logic:
        ----------------
            1. Check if reload is True, query all resources. Else, query only non-cached resources
            2. Query the resources from override and chitin locations
            3. Read and cache the 2DA data for each queried resource.
        """
        queries: list[ResourceIdentifier] = []
        if reload:
            queries.extend(ResourceIdentifier(resname, ResourceType.TwoDA) for resname in resnames)
        else:
            queries.extend(ResourceIdentifier(resname, ResourceType.TwoDA) for resname in resnames if resname not in self._cache2da)

        if not queries:
            return

        resources: dict[ResourceIdentifier, ResourceResult | None] = self.resources(queries, [SearchLocation.OVERRIDE, SearchLocation.CHITIN])
        for iden, resource in resources.items():
            if not resource:
                continue
            self._cache2da[iden.resname] = read_2da(resource.data)

    def htClearCache2DA(self):
        self._cache2da = {}

    # endregion

    # region Cache TPC
    def ht_get_cache_tpc(self, resname: str) -> TPC | None:
        if resname not in self._cache_tpc:
            tex: TPC | None = self.texture(
                resname,
                [
                    SearchLocation.OVERRIDE,
                    SearchLocation.TEXTURES_TPA,
                    SearchLocation.TEXTURES_GUI,
                ],
            )
            if tex is not None:
                self._cache_tpc[resname] = tex
        return self._cache_tpc.get(resname, None)

    def ht_batch_cache_tpc(self, names: list[str], *, reload: bool = False):
        queries: list[str] = list(names) if reload else [name for name in names if name not in self._cache_tpc]

        if not queries:
            return

        for resname in queries:
            tex: TPC | None = self.texture(
                resname,
                [
                    SearchLocation.TEXTURES_TPA,
                    SearchLocation.TEXTURES_GUI,
                ],
            )
            if tex is not None:
                self._cache_tpc[resname] = tex

    def ht_clear_cache_tpc(self):
        self._cache_tpc = {}

    # endregion

    def get_item_icon_from_uti(self, uti: UTI) -> QPixmap:
        pixmap = QPixmap(":/images/inventory/unknown.png")
        baseitems: TwoDA | None = self.ht_get_cache_2da(HTInstallation.TwoDA_BASEITEMS)
        if baseitems is None:
            RobustLogger().error("Failed to retrieve BASEITEMS 2DA.")
            return pixmap

        with suppress(Exception):
            item_class: str = baseitems.get_cell(uti.base_item, "itemclass")
            variation: int = uti.model_variation if uti.model_variation != 0 else uti.texture_variation
            texture_resname: str = f'i{item_class}_{str(variation).rjust(3, "0")}'
            texture: TPC | None = self.ht_get_cache_tpc(texture_resname.lower())

            if texture is not None:
                return self._get_icon(texture)
        return pixmap

    def get_item_base_name(self, base_item: int) -> str:
        """Get the name of the base item from its ID."""
        try:
            baseitems: TwoDA | None = self.ht_get_cache_2da(HTInstallation.TwoDA_BASEITEMS)
            if baseitems is None:
                RobustLogger().error("Failed to retrieve `baseitems.2da` from your installation.")
                return "Unknown"
        except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            RobustLogger().exception("An exception occurred while retrieving `baseitems.2da` from your installation.")
            return "Unknown"
        else:
            return baseitems.get_cell(base_item, "label")

    def get_model_var_name(self, model_variation: int) -> str:
        """Get the name of the model variation from its ID."""
        return "Default" if model_variation == 0 else f"Variation {model_variation}"

    def get_texture_var_name(self, texture_variation: int) -> str:
        """Get the name of the texture variation from its ID."""
        return "Default" if texture_variation == 0 else f"Texture {texture_variation}"

    def get_item_icon_path(self, base_item: int, model_variation: int, texture_variation: int) -> str:
        """Get the icon path based on base item, model variation, and texture variation."""
        baseitems: TwoDA | None = self.ht_get_cache_2da(HTInstallation.TwoDA_BASEITEMS)
        if baseitems is None:
            RobustLogger().warning("Failed to retrieve `baseitems.2da` from your installation.")
            return "Unknown"
        try:
            item_class: str = baseitems.get_cell(base_item, "itemclass")
        except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            RobustLogger().exception(f"An exception occurred while getting cell '{base_item}' from `baseitems.2da`.")
            return "Unknown"
        else:
            variation: int = model_variation if model_variation != 0 else texture_variation
            return f"i{item_class}_{str(variation).rjust(3, '0')}"

    def get_item_icon(
        self,
        base_item: int,
        model_variation: int,
        texture_variation: int,
    ) -> QPixmap:
        pixmap = QPixmap(":/images/inventory/unknown.png")
        icon_path: str = self.get_item_icon_path(base_item, model_variation, texture_variation)
        print(f"Icon path: '{icon_path}'")
        try:
            texture: TPC | None = self.ht_get_cache_tpc(os.path.basename(icon_path.lower()))  # noqa: PTH119
            if texture is None:
                return pixmap
            return self._get_icon(texture)
        except Exception as e:  # noqa: BLE001
            RobustLogger().error(
                f"An error occurred loading the icon at '{icon_path}' " f"model variation '{model_variation}' and " f"texture variation '{texture_variation}'.",
                exc_info=e,
            )
            return pixmap
        return pixmap

    def _get_icon(self, texture: TPC, mipmap: int = 0) -> QPixmap:
        if texture.format().is_dxt():
            texture.decode()
        mm: TPCMipmap = texture.get(0, mipmap)
        image = QImage(bytes(mm.data), mm.width, mm.height, mm.tpc_format.to_qimage_format())
        return QPixmap.fromImage(image).transformed(QTransform().scale(1, -1))

    @property
    def tsl(self) -> bool:
        if self._tsl is None:
            self._tsl = self.game().is_k2()
        return self._tsl
