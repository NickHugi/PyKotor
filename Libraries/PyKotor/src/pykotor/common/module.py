from __future__ import annotations

import errno
import os

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Any, Collection, Generic, TypeVar, TypedDict, cast

from loggerplus import RobustLogger

from pykotor.common.misc import ResRef
from pykotor.common.stream import BinaryReader, BinaryWriter
from pykotor.extract.capsule import Capsule
from pykotor.extract.file import ResourceIdentifier
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.bwm import bytes_bwm, read_bwm, write_bwm
from pykotor.resource.formats.erf import read_erf, write_erf
from pykotor.resource.formats.gff import GFF, GFFFieldType, read_gff
from pykotor.resource.formats.lyt import LYT, bytes_lyt, read_lyt, write_lyt
from pykotor.resource.formats.ncs import write_ncs
from pykotor.resource.formats.rim import read_rim, write_rim
from pykotor.resource.formats.tpc import bytes_tpc, read_tpc, write_tpc
from pykotor.resource.formats.vis import VIS, bytes_vis, read_vis, write_vis
from pykotor.resource.generics.are import bytes_are, read_are, write_are
from pykotor.resource.generics.dlg import bytes_dlg, read_dlg, write_dlg
from pykotor.resource.generics.git import GIT, bytes_git, read_git, write_git
from pykotor.resource.generics.ifo import IFO, bytes_ifo, read_ifo, write_ifo
from pykotor.resource.generics.pth import bytes_pth, read_pth, write_pth
from pykotor.resource.generics.utc import UTC, bytes_utc, read_utc, write_utc
from pykotor.resource.generics.utd import UTD, bytes_utd, read_utd, write_utd
from pykotor.resource.generics.ute import UTE, bytes_ute, read_ute, write_ute
from pykotor.resource.generics.uti import bytes_uti, read_uti, write_uti
from pykotor.resource.generics.utm import UTM, bytes_utm, read_utm, write_utm
from pykotor.resource.generics.utp import UTP, bytes_utp, read_utp, write_utp
from pykotor.resource.generics.uts import UTS, bytes_uts, read_uts, write_uts
from pykotor.resource.generics.utt import UTT, bytes_utt, read_utt, write_utt
from pykotor.resource.generics.utw import UTW, bytes_utw, read_utw, write_utw
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_any_erf_type_file, is_bif_file, is_capsule_file, is_rim_file
from pykotor.tools.model import iterate_lightmaps, iterate_textures
from pykotor.tools.path import CaseAwarePath

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Iterable, Sequence

    from typing_extensions import Self

    from pykotor.common.language import LocalizedString
    from pykotor.common.misc import Game
    from pykotor.extract.file import FileResource, LocationResult, ResourceResult
    from pykotor.extract.installation import Installation
    from pykotor.resource.formats.erf.erf_data import ERF
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.formats.mdl import MDL
    from pykotor.resource.formats.rim.rim_data import RIM
    from pykotor.resource.formats.tpc import TPC
    from pykotor.resource.generics.are import ARE
    from pykotor.resource.generics.ifo import IFO
    from pykotor.resource.generics.pth import PTH
    from pykotor.resource.generics.uti import UTI
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES

T = TypeVar("T")
SEARCH_ORDER: list[SearchLocation] = [
    SearchLocation.OVERRIDE,
    SearchLocation.CUSTOM_MODULES,
    SearchLocation.CHITIN,
]

class KModuleType(Enum):
    MAIN = ".rim"  # Contains the IFO/ARE/GIT
    DATA = "_s.rim"  # Contains everything else
    K2_DLG = "_dlg.erf"  # In TSL, DLGs are here instead of _s.rim.
    MOD = ".mod"  # Community-standard override, takes priority over the above.

    def contains(  # noqa: PLR0911
        self,
        restype: ResourceType,
        *,
        game: Game | None = None,
    ) -> bool:
        """Whether this ModuleType, if not modified, would contain the specified ResourceType or not.

        Args:
        ----
            restype (ResourceType): The type of resource to check.
            game (Game | None = None): Optional game to determine whether to invalidate _s.rim if they contain DLGs.

        Returns:
        -------
            bool: Whether this ModuleType should contain the ResourceType or not.
        """
        if restype.target_type() is not restype:
            return False
        if restype is ResourceType.DLG:
            if game is None:
                return self is self.DATA or self is self.K2_DLG
            if game.is_k1():
                return self is self.DATA
            if game.is_k2():
                return self is self.K2_DLG

        if self is self.MOD:
            return self is not ResourceType.TwoDA
        if self is self.MAIN:
            return restype in {ResourceType.ARE, ResourceType.IFO, ResourceType.GIT}
        if self is self.DATA:
            return restype in {
                ResourceType.FAC, ResourceType.LYT, ResourceType.NCS, ResourceType.PTH,
                ResourceType.UTC, ResourceType.UTD, ResourceType.UTE, ResourceType.UTI,
                ResourceType.UTM, ResourceType.UTP, ResourceType.UTS, ResourceType.UTT, ResourceType.UTW
            }
        raise RuntimeError(f"Invalid ModuleType enum: {self!r}")


@dataclass(frozen=True)
class ModulePieceInfo:
    root: str
    modtype: KModuleType

    @classmethod
    def from_filename(
        cls,
        filename: str | ResourceIdentifier,
    ) -> Self:
        if isinstance(filename, ResourceIdentifier):
            filename = str(filename)
        root = Module.find_root(filename)
        return cls(root, KModuleType(filename[len(root):]))

    def filename(self) -> str:
        return self.root + self.modtype.value

    def res_ident(self) -> ResourceIdentifier:
        return ResourceIdentifier.from_path(self.filename())

    def resname(self) -> str:
        filename = self.filename()
        return filename[:filename.index(".")]

    def restype(self) -> ResourceType:
        return ResourceType.from_extension(self.modtype.value)


class ModulePieceResource(Capsule):

    def __new__(
        cls,
        path: os.PathLike | str,
        *args,
        **kwargs,
    ):
        new_cls = cls
        if new_cls is ModulePieceResource:
            path_obj = CaseAwarePath(path)
            piece_info = ModulePieceInfo.from_filename(path_obj.name)
            if piece_info.modtype is KModuleType.DATA:
                new_cls = ModuleDataPiece
            elif piece_info.modtype is KModuleType.MAIN:
                new_cls = ModuleLinkPiece
            elif piece_info.modtype is KModuleType.K2_DLG:
                new_cls = ModuleDLGPiece
            elif piece_info.modtype is KModuleType.MOD:
                new_cls = ModuleFullOverridePiece
        return object.__new__(new_cls)  # pyright: ignore[reportArgumentType]

    def __init__(
        self,
        path: os.PathLike | str,
        *args,
        **kwargs,
    ):
        path_obj = CaseAwarePath(path)
        self.piece_info: ModulePieceInfo = ModulePieceInfo.from_filename(path_obj.name)
        self.missing_resources: list[FileResource] = []  # TODO(th3w1zard1):
        super().__init__(path_obj, *args, **kwargs)


class ModuleLinkPiece(ModulePieceResource):
    def ifo(self) -> GFF:
        lookup = self.resource("module", ResourceType.IFO)
        if lookup is None:
            import errno
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(self.filepath().joinpath("module.ifo")))
        return read_gff(lookup)

    def module_id(self) -> ResRef | None:
        """Get the module id, attempt to just check resrefs, fallback to the Mod_Area_list."""
        link_resources = {
            resource
            for resource in self._resources
            if resource.restype() is not ResourceType.IFO and KModuleType.MAIN.contains(resource.restype())
        }
        if link_resources:
            check_resname = next(iter(link_resources)).identifier().lower_resname
            if all(check_resname == res.identifier().lower_resname for res in link_resources):
                RobustLogger().debug("Module ID, Check 1: All link resources have the same resref of '%s'", check_resname)
                return ResRef(check_resname)

        ifo = self.ifo()
        if ifo.root.exists("Mod_Area_list"):
            actual_ftype = ifo.root.what_type("Mod_Area_list")
            if actual_ftype is not GFFFieldType.List:
                RobustLogger().warning(f"{self.filename()} has IFO with incorrect field 'Mod_Area_list' type '{actual_ftype.name}', expected 'List'")
            else:
                area_list = ifo.root.get_list("Mod_Area_list")
                area_localized_name = next(
                    (
                        gff_struct.get_resref("Area_Name")
                        for gff_struct in area_list
                        if gff_struct.exists("Area_Name")
                    ),
                    None
                )
                if area_localized_name is not None and str(area_localized_name).strip():
                    RobustLogger().debug("Module ID, Check 2: Found in Mod_Area_list: %s", area_localized_name)
                    return area_localized_name
            RobustLogger().error(f"{self.filename()}: Module.IFO does not contain a valid Mod_Area_list. Could not get the module id!")
        else:
            RobustLogger().error(f"{self.filename()}: Module.IFO does not have an existing Mod_Area_list.")
        return None

    def area_name(self) -> LocalizedString | ResRef:
        """See if the ARE is already cached, otherwise use the fallback."""
        area_resource = next(
            (resource for resource in self._resources if resource.restype() is ResourceType.ARE),
            None
        )
        if area_resource is not None:
            are = read_gff(area_resource.data())
            if are.root.exists("Name"):
                actual_ftype = are.root.what_type("Name")
                if actual_ftype is not GFFFieldType.LocalizedString:
                    raise ValueError(f"{self.filename()} has IFO with incorrect field 'Name' type '{actual_ftype.name}', expected 'LocalizedString'")
                result = are.root.get_locstring("Name")
                RobustLogger().debug("Check 1 result: '%s'", result)
                return result
        raise ValueError(f"Failed to find an ARE for module '{self.piece_info.filename()}'")


class ModuleDataPiece(ModulePieceResource): ...
class ModuleDLGPiece(ModulePieceResource): ...
class ModuleFullOverridePiece(ModuleDLGPiece, ModuleDataPiece, ModuleLinkPiece): ...


class _CapsuleDictTypes(TypedDict, total=False):
    MAIN: ModuleLinkPiece | None
    DATA: ModuleDataPiece | None
    K2_DLG: ModuleDLGPiece | None
    MOD: ModuleFullOverridePiece | None


class Module:  # noqa: PLR0904
    def __init__(
        self,
        root: str,
        installation: Installation,
        *,
        use_dot_mod: bool = True
    ):
        self.resources: dict[ResourceIdentifier, ModuleResource] = {}  # The keys are only used for ensured uniqueness.
        self.dot_mod: bool = use_dot_mod
        self._installation: Installation = installation
        self._root: str = self.find_root(root.lower())
        self._cached_mod_id: ResRef | None = None
        self._cached_sort_id: str | None = None

        # Build all capsules relevant to this root in the provided installation
        self._capsules: _CapsuleDictTypes = {
            KModuleType.MAIN.name: None,
            KModuleType.DATA.name: None,
            KModuleType.K2_DLG.name: None,
            KModuleType.MOD.name: None,
        }
        if self.dot_mod:
            mod_filepath = installation.module_path().joinpath(self._root + KModuleType.MOD.value)
            if mod_filepath.is_file():
                self._capsules[KModuleType.MOD.name] = ModuleFullOverridePiece(mod_filepath)
            else:
                self.dot_mod = False
                self._capsules[KModuleType.MAIN.name] = ModuleLinkPiece(installation.module_path().joinpath(self._root + KModuleType.MAIN.value))
                self._capsules[KModuleType.DATA.name] = ModuleDataPiece(installation.module_path().joinpath(self._root + KModuleType.DATA.value))
                if self._installation.game().is_k2():
                    self._capsules[KModuleType.K2_DLG.name] = ModuleDLGPiece(installation.module_path().joinpath(self._root + KModuleType.K2_DLG.value))
        else:
            self._capsules[KModuleType.MAIN.name] = ModuleLinkPiece(installation.module_path().joinpath(self._root + KModuleType.MAIN.value))
            self._capsules[KModuleType.DATA.name] = ModuleDataPiece(installation.module_path().joinpath(self._root + KModuleType.DATA.value))
            if self._installation.game().is_k2():
                self._capsules[KModuleType.K2_DLG.name] = ModuleDLGPiece(installation.module_path().joinpath(self._root + KModuleType.K2_DLG.value))

        self.reload_resources()

    def root(self) -> str:
        return self._root

    @classmethod
    def find_capsules(
        cls,
        install_or_path: Installation | Path,
        filename: str,
        *,
        strict: bool = False,
    ) -> Sequence[Capsule]:
        from pykotor.extract.installation import Installation
        root = cls.find_root(filename)
        # Build all capsules relevant to this root in the provided installation
        capsules: _CapsuleDictTypes = {
            KModuleType.MAIN.name: None,
            KModuleType.DATA.name: None,
            KModuleType.K2_DLG.name: None,
            KModuleType.MOD.name: None,
        }
        module_path: Path | CaseAwarePath = install_or_path if isinstance(install_or_path, Path) else install_or_path.module_path()
        if filename.lower().endswith(".mod"):
            mod_filepath = module_path.joinpath(root + KModuleType.MOD.value)
            if mod_filepath.is_file():
                capsules[KModuleType.MOD.name] = ModuleFullOverridePiece(mod_filepath)
            elif not strict:
                capsules[KModuleType.MAIN.name] = ModuleLinkPiece(module_path.joinpath(root + KModuleType.MAIN.value))
                capsules[KModuleType.DATA.name] = ModuleDataPiece(module_path.joinpath(root + KModuleType.DATA.value))
                if not isinstance(install_or_path, Installation) or install_or_path.game().is_k2():
                    capsules[KModuleType.K2_DLG.name] = ModuleDLGPiece(module_path.joinpath(root + KModuleType.K2_DLG.value))
        else:
            capsules[KModuleType.MAIN.name] = ModuleLinkPiece(module_path.joinpath(root + KModuleType.MAIN.value))
            capsules[KModuleType.DATA.name] = ModuleDataPiece(module_path.joinpath(root + KModuleType.DATA.value))
            if not isinstance(install_or_path, Installation) or install_or_path.game().is_k2():
                capsules[KModuleType.K2_DLG.name] = ModuleDLGPiece(module_path.joinpath(root + KModuleType.K2_DLG.value))
        return [capsule for capsule in capsules.values() if capsule is not None]  # pyright: ignore[reportReturnType]  # type: ignore[misc]


    def get_capsules(self) -> list[ModulePieceResource]:
        """Returns all relevant ERFs/RIMs for this module."""
        return list(self._capsules.values())  # pyright: ignore[reportReturnType]  # type: ignore[arg-type]

    def root_name(self) -> str:
        return self._root

    def lookup_main_capsule(
        self,
    ) -> ModuleFullOverridePiece | ModuleLinkPiece:
        mod_capsule = self._capsules[KModuleType.MOD.name] if self.dot_mod else None  # pyright: ignore[reportTypedDictNotRequiredAccess]
        relevant_capsule: ModuleFullOverridePiece | ModuleLinkPiece | None = mod_capsule or self._capsules[KModuleType.MAIN.name]  # pyright: ignore[reportTypedDictNotRequiredAccess]
        assert relevant_capsule is not None
        return relevant_capsule

    def lookup_data_capsule(
        self,
    ) -> ModuleFullOverridePiece | ModuleDataPiece:
        relevant_capsule: ModuleFullOverridePiece | ModuleDataPiece | None = (
            self._capsules[KModuleType.MOD.name]  # pyright: ignore[reportTypedDictNotRequiredAccess]
            if self.dot_mod and self._capsules[KModuleType.MOD.name] is not None  # pyright: ignore[reportTypedDictNotRequiredAccess]
            else self._capsules[KModuleType.DATA.name]  # pyright: ignore[reportTypedDictNotRequiredAccess]
        )
        assert relevant_capsule is not None
        return relevant_capsule

    def lookup_dlg_capsule(
        self,
    ) -> ModuleFullOverridePiece | ModuleDLGPiece:
        relevant_capsule: ModuleDataPiece | ModuleDLGPiece | None = (
            self._capsules[KModuleType.MOD.name]  # pyright: ignore[reportTypedDictNotRequiredAccess]
            if self.dot_mod and self._capsules[KModuleType.MOD.name] is not None  # pyright: ignore[reportTypedDictNotRequiredAccess]
            else (self._capsules[KModuleType.K2_DLG.name] if self._installation.game().is_k2() else self._capsules[KModuleType.DATA.name])  # pyright: ignore[reportTypedDictNotRequiredAccess]
        )
        assert relevant_capsule is not None
        return relevant_capsule  # pyright: ignore[reportReturnType]  # type: ignore[return-value]

    def module_id(self) -> ResRef | None:
        if self._cached_mod_id is not None:
            return self._cached_mod_id
        data_capsule = self.lookup_main_capsule()
        found_id = data_capsule.module_id()
        RobustLogger().debug("Found module id '%s' for module '%s'", found_id, data_capsule.filename())
        self._cached_mod_id = found_id
        return found_id

    @staticmethod
    @lru_cache(maxsize=1000)
    def find_root(
        filepath: os.PathLike | str,
    ) -> str:  # sourcery skip: inline-immediately-returned-variable
        """Returns the root name for a module from the given filepath (or filename). For example "danm13_s.rim" would become "danm13".

        Args:
        ----
            filepath: The filename or filepath of one of the module encapsulated file.

        Returns:
        -------
            The string for the root name of a module.
        """
        root: str = PurePath(filepath).stem
        lower_root: str = root.lower()
        root = root[:-2] if lower_root.endswith("_s") else root
        root = root[:-4] if lower_root.endswith("_dlg") else root
        return root  # noqa: RET504

    def capsules(self) -> list[ModulePieceResource]:
        """Returns a copy of the capsules used by the module.

        Returns:
        -------
            A tuple of linked capsules.
        """
        return [cast(ModulePieceResource, cap) for cap in self._capsules.values() if cap is not None]

    def reload_resources(self):
        """Reload resources from modules, LYT/VIS and overrides.

        Processing Logic:
        ----------------
            - Look in module files for resources
            - Look for LYT/VIS resources
            - Look in override directories
            - Look for resources linked in the GIT not present in module files
            - Look for texture paths for models
            - Add found locations to the resource registry.
        """
        display_name = f"{self._root}.mod" if self.dot_mod else f"{self._root}.rim"
        RobustLogger().info("Loading module resources needed for '%s'", display_name)
        mod_capsule = self._capsules[KModuleType.MOD.name]  # pyright: ignore[reportTypedDictNotRequiredAccess]
        capsules_to_search = [self.lookup_main_capsule()] if mod_capsule is None else [mod_capsule]
        # Lookup the GIT and LYT first.
        order = [
            SearchLocation.OVERRIDE,
            SearchLocation.CUSTOM_MODULES,
            SearchLocation.CHITIN,
        ]
        link_resname = str(self.module_id())
        lyt_query = ResourceIdentifier(link_resname, ResourceType.LYT)
        git_query = ResourceIdentifier(link_resname, ResourceType.GIT)
        vis_query = ResourceIdentifier(link_resname, ResourceType.VIS)

        # Start in our module resources.
        # Needs to happen first so we can determine what resources are part of our module.
        for capsule in self._capsules.values():
            if capsule is None:
                continue
            typed_capsule = cast(ModulePieceResource, capsule)  # No idea why static types aren't working here as that's the whole point of the TypedDict...
            for resource in typed_capsule:
                RobustLogger().info("Adding location '%s' for resource '%s' from erf/rim '%s'",
                                        typed_capsule.filepath(), resource.identifier(), typed_capsule.identifier())
                self.add_locations(resource.resname(), resource.restype(), [typed_capsule.filepath()])

        # Find references needs to happen second. This will be done in GIT/LYT. 2da comes during the rendering process itself, those aren't part of the module.

        # Any resource linked in the GIT not present in the module files
        # First ensure we have a git.
        main_search_results: dict[ResourceIdentifier, list[LocationResult]] = self._installation.locations(
            [lyt_query, git_query, vis_query],
            order,
            capsules=capsules_to_search
        )
        git_search = self._handle_git_lyt_reloads(main_search_results, git_query, GIT,
            "Git is somehow None even though we know the path there. Fix this later if the stars ever align here somehow.",
        )
        lyt_search = self._handle_git_lyt_reloads(main_search_results, lyt_query, LYT,
            "Lyt is somehow None even though we know the path there. Fix this later if the stars ever align here somehow.",
        )
        vis_search = self._handle_git_lyt_reloads(main_search_results, vis_query, VIS,
            "Vis is somehow None even though we know the path there. Fix this later if the stars ever align here somehow.",
        )

        # From GIT/LYT references, find them in the installation.
        search_results: dict[ResourceIdentifier, list[LocationResult]] = self._installation.locations(
            list({*git_search, *lyt_search, *vis_search}),
            order,
            capsules=capsules_to_search
        )
        for identifier, locations in search_results.items():
            self.add_locations(identifier.resname, identifier.restype, (location.filepath for location in locations))

        # Third. Since we now have a known full list of resources that make up this module, we can now process Override and chitin in one fell swoop.
        # Realistically we'll do this at the end, but right now we're interested in enumerating the models so we can find textures.

        # Check chitin first.
        for resource in self._installation.core_resources():
            if resource.identifier() in self.resources or resource.identifier() in git_search:
                RobustLogger().info("Found chitin/core location '%s' for resource '%s' for module '%s'",
                                        resource.filepath(), resource.identifier(), display_name)
                self.add_locations(resource.resname(), resource.restype(), (resource.filepath(),)).activate()

        # Prioritize Override by checking/activating last.
        for directory in self._installation.override_list():
            for resource in self._installation.override_resources(directory):
                if resource.identifier() in self.resources or resource.identifier() in git_search:
                    RobustLogger().info("Found override location '%s' for module '%s'", resource.filepath(), display_name)
                    self.add_locations(resource.resname(), resource.restype(), [resource.filepath()]).activate()

        # Also try get paths for textures in models
        lookup_texture_queries: set[str] = set()
        for model in self.models():
            RobustLogger().debug("Finding textures/lightmaps for model '%s'...", model.identifier())
            try:
                model_data = model.data()
            except OSError:
                RobustLogger().warning("Suppressed known exception while executing %s.reload_resources() while getting model data '%s': %s",
                                           repr(self), model.identifier(), exc_info=True, extra={"detailed": False})
                continue
            else:
                if model_data is None:
                    RobustLogger().warning("Missing model '%s', needed by module '%s'", model.identifier(), display_name)
                    continue
                if not model_data:
                    RobustLogger().warning("model '%s' was unexpectedly empty, but is needed by module '%s'", model.identifier(), display_name)
                    continue
            try:
                lookup_texture_queries.update(iterate_textures(model_data))
            except OSError:  # noqa: PERF203
                RobustLogger().warning("Suppressed known exception while executing %s.reload_resources() in iterate_textures() with model '%s': %s",
                                           repr(self), model.identifier(), exc_info=True, extra={"detailed": False})
            except Exception:  # noqa: BLE001
                RobustLogger().exception("Unexpected exception when executing %s.reload_resources() with model '%s'",
                                             repr(self), model.identifier(), exc_info=True)
            else:
                RobustLogger().info("Found %s textures in '%s'", model.identifier(), display_name)
            try:
                lookup_texture_queries.update(iterate_lightmaps(model_data))
            except OSError:  # noqa: PERF203
                RobustLogger().warning("Suppressed known exception while executing %s.reload_resources() in iterate_lightmaps() with model '%s': %s",
                                           repr(self), model.identifier(), exc_info=True, extra={"detailed": False})
            except Exception:  # noqa: BLE001
                RobustLogger().exception("Unexpected exception when executing %s.reload_resources() with model '%s'",
                                             repr(self), model.identifier(), exc_info=True)
            else:
                RobustLogger().info("Found %s lightmaps in '%s'", model.identifier(), display_name)

        texture_search: dict[ResourceIdentifier, list[LocationResult]] = self._installation.locations(
            [
                ResourceIdentifier(texture, res_type)
                for texture in lookup_texture_queries
                for res_type in (ResourceType.TPC, ResourceType.TGA)
            ],
            [
                SearchLocation.OVERRIDE,
                SearchLocation.CHITIN,
                SearchLocation.TEXTURES_TPA,
                #SearchLocation.TEXTURES_TPB,  # lower quality version of tpa
                #SearchLocation.TEXTURES_TPC,  # even worse quality than tpb
            ],
        )
        for identifier, locations in texture_search.items():
            if identifier == "dirt.tpc":
                continue  # skip this constant name
            if not locations:
                continue
            RobustLogger().debug(f"Adding {len(locations)} texture locations to module '{display_name}'")
            self.add_locations(identifier.resname, identifier.restype, (location.filepath for location in locations)).activate()

        # Finally iterate through all resources we may have missed.
        for ident, module_resource in self.resources.items():
            if module_resource.isActive():
                continue
            if ident.restype is ResourceType.TPC and f"{ident.lower_resname}.tga" in self.resources:
                continue
            if ident.restype is ResourceType.TGA and f"{ident.lower_resname}.tpc" in self.resources:
                continue
            module_resource.activate()

    def _handle_git_lyt_reloads(
        self,
        main_search_results: dict[ResourceIdentifier, list[LocationResult]],
        query: ResourceIdentifier,
        useable_type: type[GIT | LYT | VIS],
        errmsg: str,
    ) -> set[ResourceIdentifier]:
        if not main_search_results.get(query):
            if useable_type == VIS:
                return set()  # make vis optional I guess
            raise FileNotFoundError(errno.ENOENT,
                                    os.strerror(errno.ENOENT),
                                    self.lookup_main_capsule().filepath() / str(query))
        original_git_or_lyt = self.add_locations(
            query.resname, query.restype,
            (loc.filepath for loc in main_search_results[query]),
        )
        # Activate each GIT/LYT location for this module, and fill this module with all of their resources (all of the resources their instances point to).
        original_path: Path = original_git_or_lyt.locations()[0]
        result: set[ResourceIdentifier] = set()
        for location in original_git_or_lyt.locations():
            original_git_or_lyt.activate(location)
            loaded_git_or_lyt: type[GIT | LYT | VIS] | None = original_git_or_lyt.resource()
            if not isinstance(loaded_git_or_lyt, (GIT, LYT, VIS)):
                raise RuntimeError(errmsg)  # noqa: TRY004
            if not isinstance(loaded_git_or_lyt, VIS):
                result.update(loaded_git_or_lyt.iter_resource_identifiers())
        original_git_or_lyt.activate(original_path)  # reactivate the main one.

        return result

    def add_locations(
        self,
        resname: str,
        restype: ResourceType,
        locations: Iterable[Path],
    ) -> ModuleResource:
        """Creates or extends a ModuleResource keyed by the resname/restype with additional locations.

        This is how Module.resources dict gets filled.

        Args:
        ----
            resname: The resource name.
            restype: The resource type.
            locations: The locations of the resource files.

        Processing Logic:
        ----------------
            - Checks if the resource already exists in the dictionary
            - If it doesn't exist, creates a new ModuleResource object
            - Adds the locations to the existing or newly created ModuleResource
            - Does not return anything, modifies the dictionary in-place.
        """
        if not isinstance(locations, Collection):
            locations = list(locations)
        if not locations:
            RobustLogger().warning("No locations found for '%s.%s' which are intended to add to module '%s'", resname, restype, self._root)
        module_resource: ModuleResource | None = self.resource(resname, restype)
        if module_resource is None:
            module_resource = ModuleResource(resname, restype, self._installation)
            self.resources[module_resource.identifier()] = module_resource
        module_resource.add_locations(locations)
        return module_resource

    def installation(self) -> Installation:
        return self._installation

    def resource(
        self,
        resname: str,
        restype: ResourceType,
    ) -> ModuleResource | None:
        """Returns the resource with the given name and type from the module.

        Args:
        ----
            resname (str): The name of the resource.
            restype (ResourceType): The type of the resource.

        Returns:
        -------
            ModuleResource | None: The resource with the given name and type, or None if it does not exist.
        """
        ident = ResourceIdentifier(resname, restype)
        return self.resources.get(ident, None)

    def layout(self) -> ModuleResource[LYT] | None:
        """Returns the LYT layout resource with a matching ID if it exists.

        Args:
        ----
            self: The Module instance

        Returns:
        -------
            ModuleResource[LYT] | None: The layout resource or None if not found

        Processing Logic:
        ----------------
            - Iterates through all resources in self.resources
            - Checks if resource name matches self._id and type is LYT
            - Returns first matching resource or None if not found.
        """
        return next(
            (
                resource
                for resource in self.resources.values()
                if (resource.restype() is ResourceType.LYT and resource.resname() == self.module_id())
            ),
            None,
        )

    def vis(self) -> ModuleResource[VIS] | None:
        """Finds the VIS resource with matching ID.

        Args:
        ----
            self: The Module object.

        Returns:
        -------
            ModuleResource[VIS] | None: The VIS resource object or None.

        Finds the VIS resource object from the Module's resources:
            - Iterates through the resources dictionary values
            - Checks if the resource name matches self._id in lowercase and type is VIS
            - Returns the first matching resource or None.
        """
        return next(
            (
                resource
                for resource in self.resources.values()
                if (resource.restype() is ResourceType.VIS and resource.resname() == self.module_id())
            ),
            None
        )

    def are(
        self,
    ) -> ModuleResource[ARE] | None:
        """Returns the ARE resource with the given ID if it exists.

        Args:
        ----
            self: The Module object

        Returns:
        -------
            ModuleResource[ARE] | None: The ARE resource or None if not found

        Processing Logic:
        ----------------
            - Iterate through all resources in self.resources
            - Check if resource name matches self._id in lowercase and resource type is ARE
            - Return first matching resource or None if no match.
        """
        return next(
            (
                resource
                for resource in self.resources.values()
                if resource.restype() is ResourceType.ARE and resource.resname() == self.module_id()
            ),
            None,
        )

    def git(
        self,
    ) -> ModuleResource[GIT] | None:  # sourcery skip: remove-unreachable-code
        """Returns the git resource with matching id if found.

        Args:
        ----
            self: The module object

        Returns:
        -------
            ModuleResource[GIT] | None: The git resource or None

        Processing Logic:
        ----------------
            - Iterate through all resources in module
            - Check if resource name matches id in lowercase and type is GIT
            - Return matching resource or None if not found.
        """
        result = next(
            (
                resource
                for resource in self.resources.values()
                if resource.restype() is ResourceType.GIT and resource.resname() == self.module_id()
            ),
            None,
        )
        if result is None:  # noqa: RET503
            fallback = next(
                (
                    resource
                    for resource in self.resources.values()
                    if resource.restype() is ResourceType.GIT
                ),
                None,
            )
            if fallback is not None:  # noqa: RET503
                RobustLogger().warning("This module '%s' has an incorrect GIT resname/resref! Expected '%s', found '%s'", self._root, self.module_id(), fallback.resname())  # noqa: RET503
        return result  # noqa: RET504


    def pth(
        self,
    ) -> ModuleResource[PTH] | None:
        """Finds the PTH resource with matching ID.

        Args:
        ----
            self: The Module object.

        Returns:
        -------
            ModuleResource[PTH] | None: The PTH resource or None if not found.

        Finds the PTH resource:
            - Iterates through all resources
            - Checks if resource name matches self._id and type is PTH
            - Returns first matching resource or None.
        """
        return next(
            (
                resource
                for resource in self.resources.values()
                if resource.restype() is ResourceType.PTH and resource.resname() == self.module_id()
            ),
            None,
        )

    def ifo(self) -> ModuleResource[IFO] | None:
        return self.info()

    def info(
        self,
    ) -> ModuleResource[IFO] | None:
        """Returns the ModuleResource with type IFO if it exists.

        Args:
        ----
            self: The object instance

        Returns:
        -------
            ModuleResource[IFO] | None: The ModuleResource with type IFO or None

        Processing Logic:
        ----------------
            - Iterate through self.resources values
            - Check if resource name is 'module' and type is IFO
            - Return first matching resource
            - Return None if no match found.
        """
        return next(
            (
                resource
                for resource in self.resources.values()
                if resource.restype() is ResourceType.IFO and resource.identifier().lower_resname == "module"
            ),
            None,
        )

    def creature(
        self,
        resname: str,
    ) -> ModuleResource[UTC] | None:
        """Returns a UTC resource by name if it exists.

        Args:
        ----
            resname: Name of the resource to search for

        Returns:
        -------
            ModuleResource[UTC]: The UTC resource or None if not found

        Processing Logic:
        ----------------
            - Iterate through self.resources dictionary values
            - Check if resname matches resource name and type is UTC
            - Return matching resource or None if not found.
        """
        lower_resname: str = resname.lower()
        return next(
            (
                resource
                for resource in self.resources.values()
                if resource.restype() is ResourceType.UTC and lower_resname == resource.identifier().lower_resname
            ),
            None,
        )

    def creatures(
        self,
    ) -> list[ModuleResource[UTC]]:
        """Returns a list of UTC resources.

        Args:
        ----
            self: The class instance

        Returns:
        -------
            list[ModuleResource[UTC]]: A list of UTC resources

        Processing Logic:
        ----------------
            - Iterate through all resources in self.resources
            - Check if each resource's type is UTC
            - Add matching resources to the return list.
        """
        return [resource for resource in self.resources.values() if resource.restype() is ResourceType.UTC]

    def placeable(
        self,
        resname: str,
    ) -> ModuleResource[UTP] | None:
        """Check if a placeable UTP resource with the given resname exists.

        Args:
        ----
            resname (str): Name of the resource to check

        Returns:
        -------
            resource: Found resource or None

        Processing Logic:
        ----------------
            - Iterate through self.resources dictionary
            - Check if resource name matches given name and type is UTP
            - Return matching resource if found, else return None.
        """
        lower_resname: str = resname.lower()
        return next(
            (
                resource
                for resource in self.resources.values()
                if resource.restype() is ResourceType.UTP and lower_resname == resource.identifier().lower_resname
            ),
            None,
        )

    def placeables(
        self,
    ) -> list[ModuleResource[UTP]]:
        """Returns a list of UTP resources for this module.

        Args:
        ----
            self: The class instance

        Returns:
        -------
            list[ModuleResource[UTP]]: List of UTP resources

        Processing Logic:
        ----------------
            - Iterate through self.resources dictionary
            - Check if resource type is UTP
            - Add matching resources to the return list.
        """
        return [resource for resource in self.resources.values() if resource.restype() is ResourceType.UTP]

    def door(
        self,
        resname: str,
    ) -> ModuleResource[UTD] | None:
        """Returns a UTD resource matching the provided resname from this module.

        Args:
        ----
            resname (str): The name of the resource

        Returns:
        -------
            ModuleResource[UTD] | None: The UTD resource or None if not found

        Processing Logic:
        ----------------
            - Iterate through self.resources values
            - Check if resname matches resource name and type is UTD
            - Return matching resource or None if not found.
        """
        lower_resname: str = resname.lower()
        return next(
            (
                resource
                for resource in self.resources.values()
                if resource.restype() is ResourceType.UTD and lower_resname == resource.identifier().lower_resname
            ),
            None,
        )

    def doors(
        self,
    ) -> list[ModuleResource[UTD]]:
        """Returns a list of all UTD resources for this module.

        Args:
        ----
            self: The class instance

        Returns:
        -------
            list[ModuleResource[UTD]]: List of UTD resources

        Processing Logic:
        ----------------
            - Iterate through all resources stored in self.resources
            - Check if each resource's type is UTD
            - Add matching resources to the return list.
        """
        return [resource for resource in self.resources.values() if resource.restype() is ResourceType.UTD]

    def item(
        self,
        resname: str,
    ) -> ModuleResource[UTI] | None:
        """Returns a UTI resource matching the provided resname from this module if it exists.

        Args:
        ----
            resname (str): Name of the resource to lookup

        Returns:
        -------
            ModuleResource[UTI] | None: The matching UTI resource or None

        Processing Logic:
        ----------------
            - Iterates through self.resources dictionary values
            - Returns the first resource where resname matches resource.resname() and resource type is UTI
            - Returns None if no matching resource found.
        """
        lower_resname: str = resname.lower()
        return next(
            (
                resource
                for resource in self.resources.values()
                if resource.restype() is ResourceType.UTI and lower_resname == resource.identifier().lower_resname
            ),
            None,
        )

    def items(
        self,
    ) -> list[ModuleResource[UTI]]:
        """Returns a list of UTI resources for this module.

        Args:
        ----
            self: The class instance

        Returns:
        -------
            list[ModuleResource[UTI]]: A list of UTI resources

        Processing Logic:
        ----------------
            - Iterate through self.resources which is a dictionary of all resources
            - Check if each resource's restype is equal to ResourceType.UTD
            - If equal, add it to the return list
            - Return the list of UTI resources.
        """
        return [resource for resource in self.resources.values() if resource.restype() is ResourceType.UTD]

    def encounter(
        self,
        resname: str,
    ) -> ModuleResource[UTE] | None:
        """Find UTE resource by the specified resname.

        Args:
        ----
            resname: Resource name to search for

        Returns:
        -------
            resource: Found UTE resource or None

        Processing Logic:
        ----------------
            - Iterate through self.resources values
            - Check if resname matches resource name and type is UTE
            - Return first matching resource or None.
        """
        lower_resname: str = resname.lower()
        return next(
            (
                resource
                for resource in self.resources.values()
                if resource.restype() is ResourceType.UTE and lower_resname == resource.identifier().lower_resname
            ),
            None,
        )

    def encounters(
        self,
    ) -> list[ModuleResource[UTE]]:
        """Returns a list of UTE resources for this module.

        Args:
        ----
            self: The class instance

        Returns:
        -------
            list[ModuleResource[UTE]]: A list of UTE resources

        Processing Logic:
        ----------------
            - Iterate through all resources stored in self.resources
            - Check if each resource's type is UTE
            - If type matches, add it to the return list
            - Return the list of UTE resources.
        """
        return [resource for resource in self.resources.values() if resource.restype() is ResourceType.UTE]

    def store(self, resname: str) -> ModuleResource[UTM] | None:
        """Looks up a material (UTM) resource by the specified resname from this module and returns the resource data.

        Args:
        ----
            resname(str): Name of the resource to look up

        Returns:
        -------
            resource: The looked up resource or None if not found

        Processing Logic:
        ----------------
            - Loops through all resources stored in self.resources
            - Checks if the resource name matches the given name and type is UTM
            - Returns the first matching resource
            - Returns None if no match found.
        """
        lower_resname: str = resname.lower()
        return next(
            (
                resource
                for resource in self.resources.values()
                if resource.restype() is ResourceType.UTM and lower_resname == resource.identifier().lower_resname
            ),
            None,
        )

    def stores(
        self,
    ) -> list[ModuleResource[UTM]]:
        """Returns a list of material (UTM) resources for this module."""
        return [resource for resource in self.resources.values() if resource.restype() is ResourceType.UTM]

    def trigger(
        self,
        resname: str,
    ) -> ModuleResource[UTT] | None:
        """Returns a trigger (UTT) resource by the specified resname if it exists.

        Args:
        ----
            resname: Name of the resource to retrieve

        Returns:
        -------
            resource: The requested UTT resource or None

        Processing Logic:
        ----------------
            - Iterate through self.resources dictionary values
            - Check if resname matches resource name and type is UTT
            - Return first matching resource
            - Return None if no match found.
        """
        lower_resname: str = resname.lower()
        return next(
            (
                resource
                for resource in self.resources.values()
                if resource.restype() is ResourceType.UTT and lower_resname == resource.identifier().lower_resname
            ),
            None,
        )

    def triggers(
        self,
    ) -> list[ModuleResource[UTT]]:
        """Returns a list of UTT resources for this module.

        Args:
        ----
            self: The class instance

        Returns:
        -------
            list[ModuleResource[UTT]]: A list of UTT resources

        Processing Logic:
        ----------------
            - Iterate through self.resources dictionary
            - Check if each resource's restype is UTT
            - Add matching resources to a list
            - Return the list of UTT resources.
        """
        return [resource for resource in self.resources.values() if resource.restype() is ResourceType.UTT]

    def waypoint(
        self,
        resname: str,
    ) -> ModuleResource[UTW] | None:
        """Returns the UTW resource with the given name if it exists.

        Args:
        ----
            resname: The name of the UTW resource

        Returns:
        -------
            resource: The UTW resource or None if not found

        Processing Logic:
        ----------------
            - Iterate through self.resources dictionary values
            - Check if resname matches resource name and type is UTW
            - Return first matching resource
            - Return None if no match found.
        """
        lower_resname: str = resname.lower()
        return next(
            (
                resource
                for resource in self.resources.values()
                if resource.restype() is ResourceType.UTW and lower_resname == resource.identifier().lower_resname
            ),
            None,
        )

    def waypoints(
        self,
    ) -> list[ModuleResource[UTW]]:
        """Returns list of UTW resources from resources dict.

        Returns:
        -------
            list[ModuleResource[UTW]]: List of UTW resources

        Processing Logic:
        ----------------
            - Iterate through self.resources dict values
            - Check if resource type is UTW
            - Add matching resources to return list
            - Return list of UTW resources.
        """
        return [resource for resource in self.resources.values() if resource.restype() is ResourceType.UTW]

    def model(
        self,
        resname: str,
    ) -> ModuleResource[MDL] | None:
        """Returns a ModuleResource object for the given resource name if it exists in this module.

        Args:
        ----
            resname: The name of the resource to lookup.

        Returns:
        -------
            resource: The ModuleResource object if found, None otherwise.

        Processing Logic:
        ----------------
            - Loops through all resources stored in self.resources
            - Checks if the resource name matches the given name and the resource type is MDL
            - Returns the matching resource if found, None otherwise.
        """
        lower_resname: str = resname.lower()
        return next(
            (
                resource
                for resource in self.resources.values()
                if resource.restype() is ResourceType.MDL and lower_resname == resource.identifier().lower_resname
            ),
            None,
        )

    def model_ext(
        self,
        resname: str,
    ) -> ModuleResource | None:
        """Finds a MDX module resource by name from this module.

        Args:
        ----
            resname: The name of the resource to find.

        Returns:
        -------
            ModuleResource|None: The matching resource or None if not found.

        Processes the resources dictionary:
            - Iterates through resources.values()
            - Checks if resname matches resource.resname() and resource type is MDX
            - Returns first matching resource or None.
        """
        lower_resname: str = resname.lower()
        return next(
            (
                resource
                for resource in self.resources.values()
                if resource.restype() is ResourceType.MDX and lower_resname == resource.identifier().lower_resname
            ),
            None,
        )

    def models(
        self,
    ) -> list[ModuleResource[MDL]]:
        """Returns a list of MDL model resources.

        Args:
        ----
            self: The class instance

        Returns:
        -------
            list[ModuleResource[MDL]]: A list of MDL model resources

        Processes the resources dictionary:
            - Loops through each value in the resources dictionary
            - Checks if the resource type is MDL
            - Adds matching resources to the return list.
        """
        return [resource for resource in self.resources.values() if resource.restype() is ResourceType.MDL]

    def model_exts(
        self,
    ) -> list[ModuleResource]:
        """Returns a list of MDX model resources.

        Args:
        ----
            self: The class instance

        Returns:
        -------
            list[ModuleResource]: A list of MDX model resources

        Processes the resources dictionary:
            - Loops through each value in the resources dictionary
            - Checks if the resource type is MDX
            - Adds matching resources to the return list.
        """
        return [resource for resource in self.resources.values() if resource.restype() is ResourceType.MDX]

    def texture(
        self,
        resname: str,
    ) -> ModuleResource[TPC] | None:
        """Looks up a texture resource by resname from this module.

        Args:
        ----
            resname: Name of the texture resource to look up.

        Returns:
        -------
            resource: Found texture resource or None.

        Processing Logic:
        ----------------
            - Loops through all resources stored in self.resources
            - Checks if resname matches the resource name in any case-insensitive way
            - Checks if the resource type is a texture format like TPC or TGA
            - Returns the first matching resource or None if not found.
        """
        lower_resname: str = resname.lower()
        texture_types: set[ResourceType] = {ResourceType.TPC, ResourceType.TGA}
        return next(
            (
                resource
                for resource in self.resources.values()
                if resource.isActive() and resource.restype() in texture_types and lower_resname == resource.identifier().lower_resname
            ),
            None,
        )

    def textures(
        self,
    ) -> list[ModuleResource[MDL]]:
        """Generates a list of texture resources from this module.

        Args:
        ----
            self: The class instance

        Returns:
        -------
            list[ModuleResource[MDL]]: List of texture resources

        Processing Logic:
        ----------------
            - Iterate through self.resources dictionary
            - Check if resource type is TPC or TGA texture format
            - Include the resource in return list if type matches.
        """
        texture_types: set[ResourceType] = {ResourceType.TPC, ResourceType.TGA}
        return [resource for resource in self.resources.values() if resource.isActive() is not None and resource.restype() in texture_types]

    def sound(
        self,
        resname: str,
    ) -> ModuleResource[UTS] | None:
        """Returns the UTS resource with the given name if it exists.

        Args:
        ----
            resname: The name of the UTS resource

        Returns:
        -------
            resource: The UTS resource or None if not found

        Processing Logic:
        ----------------
            - Iterate through self.resources dictionary values
            - Check if resname matches resource name and type is UTS
            - Return matching resource or None if not found.
        """
        lower_resname: str = resname.lower()
        return next(
            (
                resource
                for resource in self.resources.values()
                if resource.restype() is ResourceType.UTS and lower_resname == resource.identifier().lower_resname
            ),
            None,
        )

    def sounds(
        self,
    ) -> list[ModuleResource[UTS]]:
        """Returns a list of UTS resources.

        Args:
        ----
            self: The class instance

        Returns:
        -------
            list[ModuleResource[UTS]]: A list of UTS resources

        Processing Logic:
        ----------------
            - Iterate through self.resources dictionary
            - Check if each resource's type is UTS
            - Add matching resources to a list
            - Return the list of UTS resources.
        """
        return [resource for resource in self.resources.values() if resource.restype() is ResourceType.UTS]


class ModuleResource(Generic[T]):
    def __init__(
        self,
        resname: str,
        restype: ResourceType,
        installation: Installation,
    ):
        self._resname: str = resname
        self._installation: Installation = installation
        self._restype: ResourceType = restype
        self._active: Path | None = None
        self._resource_obj: Any = None
        self._locations: list[Path] = []
        self._identifier = ResourceIdentifier(resname, restype)

    def __repr__(self):
        return f"ModuleResource(resname={self._resname} restype={self._restype!r} installation={self._installation!r})"

    def __eq__(self, other):
        if self is other:
            return True
        if isinstance(other, ResourceIdentifier):
            return self._identifier == other
        if isinstance(other, ModuleResource):
            return self._identifier == other._identifier
        return NotImplemented

    def __hash__(self):
        return hash(self._identifier)

    def resname(self) -> str:
        """Returns the resource name.

        Returns:
        -------
            The resource name.
        """
        return self._resname

    def restype(self) -> ResourceType:
        """Returns the type of resource stored.

        Returns:
        -------
            The resource type.
        """
        return self._restype

    def filename(self) -> str:
        return str(self._identifier)

    def identifier(self) -> ResourceIdentifier:
        return self._identifier

    def localized_name(self) -> str | None:
        # sourcery skip: assign-if-exp, reintroduce-else
        """Returns a localized name for the resource.

        Args:
        ----
            self: The object instance

        Returns:
        -------
            str | None: Localized name or None if not found

        Processing Logic:
        ----------------
            - Get the resource from self.resource()
            - Check if resource is None and return None
            - Check type of resource and return localized name by calling installation string method
            - Return None if type is not matched.
        """
        res: T | None = self.resource()
        if res is None:
            return None
        if isinstance(res, UTC):
            return f"{self._installation.string(res.first_name)} {self._installation.string(res.last_name)}"
        if isinstance(res, (UTD, UTE, UTM, UTP, UTS, UTT, UTW)):
            return self._installation.string(res.name)
        print(f"Could not find a localized name for a ModuleResource typed {type(res).__name__}")
        return None

    def data(self) -> bytes | None:
        """Opens the file at the active location and returns the data.

        Raises:
        ------
            ValueError: If no file is active.

        Returns:
        -------
            The bytes data of the active file.
        """
        file_name: str = f"{self._resname}.{self._restype.extension}"
        active_path = self.active()
        if active_path is None:
            return None

        if is_capsule_file(active_path):
            data: bytes | None = Capsule(active_path).resource(self._resname, self._restype)
            if data is None:
                RobustLogger().error(f"Resource '{file_name}' not found in '{active_path}'")
            return data

        if is_bif_file(active_path):
            resource: ResourceResult | None = self._installation.resource(
                self._resname,
                self._restype,
                [SearchLocation.CHITIN],
            )
            if resource is None:
                msg = f"Resource '{file_name}' not found in BIF '{self._active}' somehow?"
                RobustLogger().error(msg)
                return None
            return resource.data

        return BinaryReader.load_file(active_path)

    def resource(self) -> T | None:
        """Returns the cached resource object. If no object has been cached, then it will load the object.

        Returns:
        -------
            The resource object.

        Returns:
            The abstracted resource, or None if not found.
        """
        if self._resource_obj is None:
            conversions: dict[ResourceType, Callable[[SOURCE_TYPES], Any]] = {
                ResourceType.ARE: read_are,
                ResourceType.DLG: read_dlg,
                ResourceType.GIT: read_git,
                ResourceType.IFO: read_ifo,
                ResourceType.LYT: read_lyt,
                ResourceType.NCS: lambda data: data,
                ResourceType.PTH: read_pth,
                ResourceType.TPC: read_tpc,
                ResourceType.TGA: read_tpc,
                ResourceType.UTD: read_utd,
                ResourceType.UTE: read_ute,
                ResourceType.UTI: read_uti,
                ResourceType.UTM: read_utm,
                ResourceType.UTP: read_utp,
                ResourceType.UTS: read_uts,
                ResourceType.UTT: read_utt,
                ResourceType.UTW: read_utw,
                ResourceType.UTC: read_utc,
                ResourceType.VIS: read_vis,
                ResourceType.WOK: read_bwm,
            }
            active_path = self.active()
            if active_path is None:
                return None

            if is_capsule_file(active_path):
                data: bytes | None = Capsule(active_path).resource(self._resname, self._restype)
                if data is None:
                    msg = f"Resource '{self._identifier}' not found in '{active_path}'"
                    RobustLogger().error(msg)
                    return None
                self._resource_obj = conversions[self._restype](data)

            elif is_bif_file(active_path):
                resource: ResourceResult | None = self._installation.resource(
                    self._resname,
                    self._restype,
                    [SearchLocation.CHITIN],
                )
                if resource is None:
                    msg = f"Resource '{self._identifier}' not found in '{active_path}'"
                    RobustLogger().error(msg)
                    return None
                self._resource_obj = conversions[self._restype](resource.data)

            else:
                data = BinaryReader.load_file(active_path)
                self._resource_obj = conversions[self._restype](data)

        return self._resource_obj

    def to_bytes(self) -> bytes | None:
        if self._resource_obj is None:
            return None
        conversions: dict[ResourceType, Callable[[Any, TARGET_TYPES], Any]] = {
            ResourceType.ARE: write_are,
            ResourceType.DLG: write_dlg,
            ResourceType.GIT: write_git,
            ResourceType.IFO: write_ifo,
            ResourceType.LYT: write_lyt,
            ResourceType.NCS: write_ncs,
            ResourceType.PTH: write_pth,
            ResourceType.TPC: write_tpc,
            ResourceType.TGA: write_tpc,
            ResourceType.UTD: write_utd,
            ResourceType.UTE: write_ute,
            ResourceType.UTI: write_uti,
            ResourceType.UTM: write_utm,
            ResourceType.UTP: write_utp,
            ResourceType.UTS: write_uts,
            ResourceType.UTT: write_utt,
            ResourceType.UTW: write_utw,
            ResourceType.UTC: write_utc,
            ResourceType.VIS: write_vis,
            ResourceType.WOK: write_bwm,
        }
        result: bytearray = bytearray()
        conversions[self._restype](self._resource_obj, result)
        return bytes(result)

    def add_locations(self, filepaths: Iterable[Path]):
        """Adds a list of filepaths to the list of locations stored for the resource.

        If a filepath already exists, it is ignored.

        Args:
        ----
            filepaths: A list of filepaths pointing to a location for the resource.
        """
        self._locations.extend(
            filepath
            for filepath in filepaths
            if filepath not in self._locations
        )

    def locations(self) -> list[Path]:
        return self._locations

    def activate(
        self,
        filepath: os.PathLike | str | None = None,
    ) -> Path | None:
        """Sets the active file to the specified path. Calling this method will reset the loaded resource.

        If the filepath is not in the stored locations, calling this method will add it.

        Args:
        ----
            filepath: The new active file.
        """
        self._resource_obj = None
        if filepath is None:
            self._active = next(iter(self._locations), None)
        else:
            r_filepath = Path(filepath)
            if r_filepath not in self._locations:
                self._locations.append(r_filepath)
            self._active = r_filepath
        if self._active is None:
            RobustLogger().warning("Cannot activate module resource '%s': No locations found.", self.identifier())
        else:
            other_locations_available = len(self._locations)-1
            other_locations_available_display = f" ({other_locations_available} other locations available)" if other_locations_available else ""
            RobustLogger().debug("Activating module resource '%s' at filepath '%s'%s", self.identifier(), self._active, other_locations_available_display)
        return self._active

    def unload(self):
        """Clears the cached resource object from memory."""
        self._resource_obj = None

    def reload(self):
        """Reloads the resource object from the active location."""
        self._resource_obj = None
        self.resource()

    def active(self) -> Path | None:
        """Returns the filepath of the currently active file for the resource.

        Returns:
        -------
            Filepath to the active resource.
        """
        if self._active is None:
            next_path = next(iter(self._locations), None)
            if next_path is None:
                RobustLogger().warning("No resource found for '%s'", self._identifier)
                return None
            self.activate()
            #raise RuntimeError(f"{self!r}.activate(filepath) must be called before use.")
        return self._active

    def isActive(self) -> bool:
        return bool(self._active)

    def save(
        self,
    ):
        """Saves the resource to the active file.

        Args:
        ----
            self: The resource object

        Returns:
        -------
            None: This function does not return anything

        Processing Logic:
        ----------------
            - Checks if an active file is selected
            - Checks file type and writes resource data accordingly
            - Writes resource data to ERF, RIM or binary file using appropriate conversion and writer.
        """
        conversions: dict[ResourceType, Callable[[Any], bytes]] = {
            ResourceType.ARE: bytes_are,
            ResourceType.DLG: bytes_dlg,
            ResourceType.GIT: bytes_git,
            ResourceType.IFO: bytes_ifo,
            ResourceType.LYT: bytes_lyt,
            ResourceType.NCS: lambda data: data,
            ResourceType.PTH: bytes_pth,
            ResourceType.TPC: bytes_tpc,
            ResourceType.TGA: bytes_tpc,
            ResourceType.UTD: bytes_utd,
            ResourceType.UTE: bytes_ute,
            ResourceType.UTI: bytes_uti,
            ResourceType.UTM: bytes_utm,
            ResourceType.UTP: bytes_utp,
            ResourceType.UTS: bytes_uts,
            ResourceType.UTT: bytes_utt,
            ResourceType.UTW: bytes_utw,
            ResourceType.UTC: bytes_utc,
            ResourceType.VIS: bytes_vis,
            ResourceType.WOK: bytes_bwm,
        }

        active_path = self.active()
        if not active_path:
            active_path = self._create_anew_in_override()
        if is_bif_file(active_path):
            msg = "Cannot save file to BIF."
            raise ValueError(msg)

        if is_any_erf_type_file(active_path):
            erf: ERF = read_erf(active_path)
            erf.set_data(
                self._resname,
                self._restype,
                conversions[self._restype](self.resource()),
            )
            write_erf(erf, active_path)

        elif is_rim_file(active_path):
            rim: RIM = read_rim(active_path)
            rim.set_data(
                self._resname,
                self._restype,
                conversions[self._restype](self.resource()),
            )
            write_rim(rim, active_path)

        else:
            BinaryWriter.dump(active_path, conversions[self._restype](self.resource()))

    def _create_anew_in_override(self) -> CaseAwarePath:
        bytedata = self.to_bytes()
        if bytedata is None:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), self._installation.override_path().joinpath(self.filename()))

        RobustLogger().warning("Saving ModuleResource '%s' to the Override folder as it does not have any other paths available...", self.identifier())
        result = self._installation.override_path().joinpath(self.filename())
        with result.open("wb") as f:
            f.write(bytedata)
        self.activate(result)
        return result
