from __future__ import annotations

from copy import copy
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Generic, TypeVar, TypedDict

from pykotor.common.misc import CaseInsensitiveDict
from pykotor.common.stream import BinaryReader, BinaryWriter
from pykotor.extract.capsule import Capsule
from pykotor.extract.file import ResourceIdentifier
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.bwm import bytes_bwm, read_bwm
from pykotor.resource.formats.erf import read_erf, write_erf
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.formats.gff.gff_data import GFFFieldType
from pykotor.resource.formats.lyt import bytes_lyt, read_lyt
from pykotor.resource.formats.rim import read_rim, write_rim
from pykotor.resource.formats.tpc import bytes_tpc, read_tpc
from pykotor.resource.formats.vis import bytes_vis, read_vis
from pykotor.resource.generics.are import bytes_are, read_are
from pykotor.resource.generics.dlg import bytes_dlg, read_dlg
from pykotor.resource.generics.git import bytes_git, read_git
from pykotor.resource.generics.ifo import bytes_ifo, read_ifo
from pykotor.resource.generics.pth import bytes_pth, read_pth
from pykotor.resource.generics.utc import UTC, bytes_utc, read_utc
from pykotor.resource.generics.utd import UTD, bytes_utd, read_utd
from pykotor.resource.generics.ute import UTE, bytes_ute, read_ute
from pykotor.resource.generics.uti import bytes_uti, read_uti
from pykotor.resource.generics.utm import UTM, bytes_utm, read_utm
from pykotor.resource.generics.utp import UTP, bytes_utp, read_utp
from pykotor.resource.generics.uts import UTS, bytes_uts, read_uts
from pykotor.resource.generics.utt import UTT, bytes_utt, read_utt
from pykotor.resource.generics.utw import UTW, bytes_utw, read_utw
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_any_erf_type_file, is_bif_file, is_capsule_file, is_rim_file
from pykotor.tools.model import list_lightmaps, list_textures
from pykotor.tools.path import CaseAwarePath
from utility.logger_util import get_root_logger
from utility.system.path import Path, PurePath

if TYPE_CHECKING:
    import os

    from collections.abc import Callable

    from typing_extensions import Self

    from pykotor.common.language import LocalizedString
    from pykotor.common.misc import Game, ResRef
    from pykotor.extract.file import LocationResult, ResourceResult
    from pykotor.extract.installation import Installation
    from pykotor.resource.formats.erf.erf_data import ERF
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.formats.lyt import LYT
    from pykotor.resource.formats.mdl import MDL
    from pykotor.resource.formats.rim.rim_data import RIM
    from pykotor.resource.formats.tpc import TPC
    from pykotor.resource.formats.vis import VIS
    from pykotor.resource.generics.are import ARE
    from pykotor.resource.generics.git import GIT
    from pykotor.resource.generics.ifo import IFO
    from pykotor.resource.generics.pth import PTH
    from pykotor.resource.generics.uti import UTI
    from pykotor.resource.type import SOURCE_TYPES

T = TypeVar("T")
SEARCH_ORDER: list[SearchLocation] = [
    SearchLocation.OVERRIDE,
    SearchLocation.CUSTOM_MODULES,
    SearchLocation.CHITIN,
]

class ModuleType(Enum):
    MAIN = ".rim"  # Contains the IFO/ARE/GIT
    DATA = "_s.rim"  # Contains everything else
    K2_DLG = "_dlg.erf"  # In TSL, DLGs are here instead of _s.rim.
    MOD = ".mod"  # Community-standard override, takes priority over the above.

    def contains(
        self,
        restype: ResourceType,
        *,
        game: Game | None = None,
        strict: bool = False,
    ) -> bool:
        """Whether this ModuleType, if not modified, would contain the specified ResourceType or not.

        Args:
        ----
            restype (ResourceType): The type of resource to check.
            game (Game | None = None): Optional game to determine whether to invalidate _s.rim if they contain DLGs.
            strict (bool = False): Whether to be strict about the resources in the _s.rim data rim. Default is False.

        Returns:
        -------
            bool: Whether this ModuleType should contain the ResourceType or not.
        """
        if restype.target_type() is not restype:
            return False
        if self is self.MAIN:
            return restype in {
                ResourceType.IFO,
                ResourceType.GIT,
                ResourceType.ARE
            }
        DATA_SET: set[ResourceType] = {
            ResourceType.FAC,
            ResourceType.LYT,
            ResourceType.NCS,
            ResourceType.PTH,
            ResourceType.UTC,
            ResourceType.UTD,
            ResourceType.UTE,
            ResourceType.UTI,
            ResourceType.UTM,
            ResourceType.UTP,
            ResourceType.UTS,
            ResourceType.UTT,
            ResourceType.UTW,
        }
        if self is self.K2_DLG:
            return restype is ResourceType.DLG
        if game is not None and game.is_k2():
            DATA_SET.remove(ResourceType.DLG)
        if self is self.DATA:
            return not strict or restype in DATA_SET
        raise RuntimeError(f"Invalid ModuleType enum: {self!r}")


@dataclass(frozen=True)
class ModulePieceInfo:
    root: str
    modtype: ModuleType

    @classmethod
    def from_filename(
        cls,
        filename: str | ResourceIdentifier,
    ) -> Self:
        if isinstance(filename, ResourceIdentifier):
            filename = str(filename)
        root = Module.find_root(filename)
        return cls(
            root,
            ModuleType(filename[len(root):])
        )

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
    REQUIRED=True
    def __new__(cls, path: os.PathLike | str, *args, **kwargs):
        path_obj: CaseAwarePath | None = None
        if cls is ModulePieceResource:
            path_obj = CaseAwarePath.pathify(path)
            piece_info = ModulePieceInfo.from_filename(path_obj.name)
            if piece_info.modtype is ModuleType.DATA:
                cls = ModuleDataPiece
            elif piece_info.modtype is ModuleType.MAIN:
                cls = ModuleLinkPiece
            elif piece_info.modtype is ModuleType.K2_DLG:
                cls = ModuleDLGPiece
            elif piece_info.modtype is ModuleType.MOD:
                cls = ModuleFullOverridePiece
            kwargs["piece_info"] = piece_info
        instance = super().__new__(cls)  # type: ignore[reportArgumentType]
        instance.__init__(path if path_obj is None else path_obj, *args, **kwargs)

    def __init__(
        self,
        path: os.PathLike | str,
        *args,
        piece_info: ModulePieceInfo,
        **kwargs,
    ):
        self.piece_info: ModulePieceInfo = piece_info
        self.activated: bool = False

        path_obj: CaseAwarePath = CaseAwarePath.pathify(path)
        if not self.REQUIRED and not path_obj.safe_isfile():
            return  # Keep deactivated if not required.

        self.activated = True
        super().__init__(*args, **kwargs)



class ModuleLinkPiece(ModulePieceResource):
    def ifo(self):
        lookup = self.resource("module", ResourceType.IFO)
        if lookup is None:
            raise FileNotFoundError(self.filepath().joinpath("module.ifo"))
        return read_gff(lookup)

    def id(self) -> str:
        # Only ever seen this wrong for custom modules.
        return next(
            (resource.resname() for resource in self._resources if resource.restype() is ResourceType.GIT),
            next(
                (resource.resname() for resource in self._resources if resource.restype() is ResourceType.ARE),
                self.quick_id(self.filename())
            )
        )

    @staticmethod
    def quick_id(filename: str) -> str:
        base_name: str = filename.rsplit(".")[0]  # Strip extension
        parts: list[str] = base_name.split("_")

        if len(parts) == 1:  # noqa: PLR2004
            # If there are no underscores, return the base name itself
            return base_name
        if len(parts) == 2:  # noqa: PLR2004
            # If there's exactly one underscore, return the part after the underscore
            return parts[1]
        if len(parts) >= 3:  # noqa: PLR2004
            # If there are three or more underscores, return what's between the first two underscores
            return (
                "_".join(parts[1:-1])
                if parts[-1].lower() in ("s", "dlg")
                else "_".join(parts[1:2])
            )

        return base_name

    def area_name(self) -> LocalizedString | ResRef:
        # Check 1: See if the ARE is already cached.
        area_resource = next(
            (resource for resource in self._resources if resource.restype() is ResourceType.ARE),
            None
        )
        if area_resource is not None:
            are = read_gff(area_resource.data())
            if are.root.exists("Name"):
                actual_ftype = are.root.what_type("Name")
                if actual_ftype is not GFFFieldType.LocalizedString:
                    get_root_logger().warning(f"{self.filename()} has IFO with incorrect field 'Mod_Area_List' type '{actual_ftype.name}', expected 'List'")
                return are.root.get_locstring("Name")

        # Check 2: Attempt to use the Mod_Area_List
        ifo = self.ifo()
        if ifo.root.exists("Mod_Area_List"):
            actual_ftype = ifo.root.what_type("Mod_Area_List")
            if actual_ftype is not GFFFieldType.List:
                get_root_logger().warning(f"{self.filename()} has IFO with incorrect field 'Mod_Area_List' type '{actual_ftype.name}', expected 'List'")
            else:
                area_list = ifo.root.get_list("Mod_Area_List")
                area_localized_name = next(
                    (
                        gff_struct.get_resref("Area_Name")
                        for gff_struct in area_list
                        if gff_struct.exists("Area_Name")
                    ),
                    None
                )
                if area_localized_name is not None and str(area_localized_name).strip():
                    return area_localized_name
            get_root_logger().error(f"{self.filename()}: Module.IFO does not contain a valid Mod_Area_List. Could not get the area name.")
        else:
            get_root_logger().error(f"{self.filename()}: Module.IFO does not have an existing Mod_Area_List.")
        raise ValueError(f"Failed to get the area name from module filename '{self.filename()}'")


class ModuleDataPiece(ModulePieceResource): ...


class ModuleDLGPiece(ModulePieceResource):
    REQUIRED=False


class ModuleFullOverridePiece(ModuleDLGPiece, ModuleDataPiece, ModuleLinkPiece):
    REQUIRED=False


class Module:  # noqa: PLR0904
    def __init__(
        self,
        root: str,
        installation: Installation,
        *,
        use_dot_mod: bool = True
    ):
        self.resources: CaseInsensitiveDict[ModuleResource] = CaseInsensitiveDict()
        self._installation: Installation = installation
        self._root: str = self.find_root(root.lower())
        self._dot_mod: bool = use_dot_mod and installation.module_path().joinpath(f"{self._root}.mod").is_file()

        # Build all capsules relevant to this root in the provided installation
        self._link_capsule = ModuleLinkPiece(installation.path().joinpath("Modules", self._root + ModuleType.MAIN.value))
        self._data_capsule = ModuleDataPiece(installation.path().joinpath("Modules", self._root + ModuleType.DATA.value))
        self._k2_capsule = ModuleDLGPiece(installation.path().joinpath("Modules", self._root + ModuleType.K2_DLG.value))
        self._override_piece = ModuleFullOverridePiece(installation.path().joinpath("Modules", self._root + ModuleType.MOD.value))

        # Fast-fail if capsules list is empty.
        num_expected_capsules = 3 if installation.game().is_k2() else 2
        if num_expected_capsules != len(self._capsules):
            msg = f"Your installation is missing some vanilla ERFs/RIMs in the Modules folder for module '{self._root}'"
            raise FileNotFoundError(msg)

        self.reload_resources()

    def get_capsules(self) -> tuple[ModuleLinkPiece, ModuleDataPiece, ModuleDLGPiece]:
        """Returns all relevant ERFs/RIMs for this module."""
        return self._capsules

    def root_name(self) -> str:
        return self._root

    def area_name(self) -> ResRef:
        if self._area_name is not None:
            return self._area_name

        self._area_name = self._capsules[0].area_name()
        return self._area_name

    def sortable_id(self) -> str:
        if self._alternate_id is not None:
            return self._alternate_id

        self._alternate_id = self._capsules[0].quick_id(self._root)
        return self._alternate_id

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
        root: str = PurePath.pathify(filepath).stem
        case_root: str = root.casefold()
        root = root[:-2] if case_root.endswith("_s") else root
        root = root[:-4] if case_root.endswith("_dlg") else root
        return root  # noqa: RET504

    def capsules(self) -> tuple[Capsule]:
        """Returns a copy of the capsules used by the module.

        Returns:
        -------
            A tuple of linked capsules.
        """
        return copy(self._capsules)

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
        # Look in module files
        for capsule in self._capsules.values():
            for resource in capsule:
                self.add_locations(
                    resource.resname(),
                    resource.restype(),
                    [capsule.path()],
                )

        # Look for LYT/VIS
        for resource in self._installation.chitin_resources():
            if resource.resname() == self._area_name:
                self.add_locations(
                    resource.resname(),
                    resource.restype(),
                    [resource.filepath()],
                )
        for directory in self._installation.override_list():
            for resource in self._installation.override_resources(directory):
                if resource.resname() == self._area_name:
                    self.add_locations(
                        resource.resname(),
                        resource.restype(),
                        [resource.filepath()],
                    )

        # Any resource linked in the GIT not present in the module files
        original_git: ModuleResource[GIT] | None = self.git()
        assert original_git is not None, "self.git() cannot be None here"

        original: Path = original_git.active()
        look_for: list[ResourceIdentifier] = []
        for location in original_git.locations():
            original_git.activate(location)
            git: GIT | None = original_git.resource()
            assert git is not None, "self.git().resource() cannot be None here"
            look_for.extend(
                [ResourceIdentifier(str(creature.resref), ResourceType.UTC) for creature in git.creatures]
                + [ResourceIdentifier(str(placeable.resref), ResourceType.UTP) for placeable in git.placeables]
                + [ResourceIdentifier(str(door.resref), ResourceType.UTD) for door in git.doors]
                + [ResourceIdentifier(str(sound.resref), ResourceType.UTS) for sound in git.sounds]
                + [ResourceIdentifier(str(waypoint.resref), ResourceType.UTW) for waypoint in git.waypoints]
                + [ResourceIdentifier(str(encounter.resref), ResourceType.UTE) for encounter in git.encounters]
                + [ResourceIdentifier(str(trigger.resref), ResourceType.UTT) for trigger in git.triggers]
                + [ResourceIdentifier(str(store.resref), ResourceType.UTM) for store in git.stores],
            )
        original_git.activate(original)

        # Models referenced in LYTs
        original_layout: ModuleResource[LYT] | None = self.layout()
        assert original_layout is not None, "self.layout() cannot be None here"

        original = original_layout.active()
        for location in original_layout.locations():
            original_layout.activate(location)
            layout: LYT | None = original_layout.resource()
            assert layout is not None, "self.layout().resource() cannot be None here"
            for room in layout.rooms:
                look_for.extend(
                    (
                        ResourceIdentifier(room.model, ResourceType.MDL),
                        ResourceIdentifier(room.model, ResourceType.MDX),
                        ResourceIdentifier(room.model, ResourceType.WOK),
                    ),
                )
        original_layout.activate(original)

        search: dict[ResourceIdentifier, list[LocationResult]] = self._installation.locations(
            look_for,
            [SearchLocation.OVERRIDE, SearchLocation.CHITIN],
        )
        for identifier, locations in search.items():
            self.add_locations(
                identifier.resname,
                identifier.restype,
                [location.filepath for location in locations],
            )

        # Also try get paths for textures in models
        look_for = []
        textures: set[str] = set()
        for model in self.models():
            get_root_logger().debug("Finding textures/lightmaps for model '%s'...", model.identifier())
            try:
                data: bytes = model.data()
                for texture in list_textures(data):
                    textures.add(texture)
                for lightmap in list_lightmaps(data):
                    textures.add(lightmap)
            except OSError:  # noqa: PERF203
                get_root_logger().debug("Suppressed exception when executing %s.reload_resources() with model '%s'", repr(self), model.identifier(), exc_info=True)
            except Exception:  # noqa: BLE001
                get_root_logger().exception("Unexpected exception when executing %s.reload_resources() with model '%s'", repr(self), model.identifier(), exc_info=True)

        for texture in textures:
            look_for.extend(
                (
                    ResourceIdentifier(texture, ResourceType.TPC),
                    ResourceIdentifier(texture, ResourceType.TGA),
                ),
            )

        search2: dict[ResourceIdentifier, list[LocationResult]] = self._installation.locations(
            look_for,
            [
                SearchLocation.OVERRIDE,
                SearchLocation.CHITIN,
                SearchLocation.TEXTURES_TPA,
                SearchLocation.TEXTURES_TPB,
                SearchLocation.TEXTURES_TPC,
            ],
        )
        for identifier, locations in search2.items():
            get_root_logger().info("Adding %s locations for resource '%s'...", len(locations), identifier)
            if not locations:
                continue
            self.add_locations(
                identifier.resname,
                identifier.restype,
                [location.filepath for location in locations],
            )

        for module_resource in self.resources.values():
            get_root_logger().info("Activating module resource '%s'...", module_resource.identifier())
            module_resource.activate()

    def add_locations(
        self,
        resname: str,
        restype: ResourceType,
        locations: list[Path],
    ):
        """Adds resource locations to a ModuleResource.

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
        # In order to store TGA resources in the same ModuleResource as their TPC counterpart, we use the .TPC extension
        # instead of the .TGA for the dictionary key.
        filename_ext = (ResourceType.TPC if restype is ResourceType.TGA else restype).extension
        filename: str = f"{resname}.{filename_ext}"
        module_resource: ModuleResource = self.resources.get(filename)
        if module_resource is None:
            module_resource = ModuleResource(resname, restype, self._installation)
            self.resources[filename] = module_resource

        self.resources[filename].add_locations(locations)

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
        return self.resources.get(f"{resname}.{restype.extension}", None)

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
                if (resource.resname() == self._area_name and resource.restype() == ResourceType.LYT)
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
                if (resource.resname() == self._area_name and resource.restype() == ResourceType.VIS)
            ),
            None,
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
                if resource.resname() == self._area_name and resource.restype() == ResourceType.ARE
            ),
            None,
        )

    def git(
        self,
    ) -> ModuleResource[GIT] | None:
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
        return next(
            (
                resource
                for resource in self.resources.values()
                if resource.resname() == self._area_name and resource.restype() == ResourceType.GIT
            ),
            None,
        )

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
                if resource.resname() == self._area_name and resource.restype() == ResourceType.PTH
            ),
            None,
        )

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
                if resource.resname().lower() == "module" and resource.restype() is ResourceType.IFO
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
                if lower_resname == resource.resname().lower() and resource.restype() is ResourceType.UTC
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
                if lower_resname == resource.resname().lower() and resource.restype() is ResourceType.UTP
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
                if lower_resname == resource.resname().lower() and resource.restype() is ResourceType.UTD
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
                if lower_resname == resource.resname().lower() and resource.restype() is ResourceType.UTI
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
                if lower_resname == resource.resname().lower() and resource.restype() is ResourceType.UTE
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

    def store(self, resname: str | ResRef) -> ModuleResource[UTM] | None:
        """Looks up a material (UTM) resource by the specified resname from this module and returns the resource data.

        Args:
        ----
            resname(str | ResRef): Name of the resource to look up

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
        lower_resname: str = str(resname).lower()
        return next(
            (
                resource
                for resource in self.resources.values()
                if lower_resname == resource.resname().lower() and resource.restype() is ResourceType.UTM
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
                if lower_resname == resource.resname().lower() and resource.restype() is ResourceType.UTT
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
                if lower_resname == resource.resname().lower() and resource.restype() is ResourceType.UTW
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
        lower_resname = resname.lower()
        return next(
            (
                resource
                for resource in self.resources.values()
                if lower_resname == resource.resname().lower() and resource.restype() is ResourceType.MDL
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
                if lower_resname == resource.resname().lower() and resource.restype() is ResourceType.MDX
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
        texture_types: list[ResourceType] = [ResourceType.TPC, ResourceType.TGA]
        return next(
            (
                resource
                for resource in self.resources.values()
                if lower_resname == resource.resname().lower() and resource.restype() in texture_types
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
        texture_types: list[ResourceType] = [ResourceType.TPC, ResourceType.TGA]
        return [resource for resource in self.resources.values() if resource.restype() in texture_types]

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
                if lower_resname == resource.resname().lower() and resource.restype() is ResourceType.UTS
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
        if isinstance(res, (UTP, UTD, UTW, UTT, UTE, UTM, UTS)):
            return self._installation.string(res.name)
        print(f"Could not find a localized name for a ModuleResource typed {type(res).__name__}")
        return None

    def data(self) -> bytes:
        """Opens the file at the active location and returns the data.

        Raises:
        ------
            ValueError: If no file is active.

        Returns:
        -------
            The bytes data of the active file.
        """
        file_name: str = f"{self._resname}.{self._restype.extension}"

        if is_capsule_file(self.active()):
            data: bytes | None = Capsule(self.active()).resource(self._resname, self._restype)
            if data is None:
                msg = f"Resource '{file_name}' not found in '{self.active()}'"
                raise ValueError(msg)
            return data

        if is_bif_file(self.active()):
            resource: ResourceResult | None = self._installation.resource(
                self._resname,
                self._restype,
                [SearchLocation.CHITIN],
            )
            if resource is None:
                msg = f"Resource '{file_name}' not found in BIF '{self._active}' somehow?"
                raise ValueError(msg)
            return resource.data

        return BinaryReader.load_file(self.active())

    def resource(self) -> T:
        """Returns the cached resource object. If no object has been cached, then it will load the object.

        Returns:
        -------
            The resource object.

        Raises:
            ValueError - resource not found somewhere
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

            if is_capsule_file(self.active().name):
                data: bytes | None = Capsule(self.active()).resource(self._resname, self._restype)
                if data is None:
                    msg = f"Resource '{self._identifier}' not found in '{self.active()}'"
                    raise ValueError(msg)
                self._resource_obj = conversions[self._restype](data)

            elif is_bif_file(self.active().name):
                resource: ResourceResult | None = self._installation.resource(
                    self._resname,
                    self._restype,
                    [SearchLocation.CHITIN],
                )
                if resource is None:
                    msg = f"Resource '{self._identifier}' not found in '{self.active()}'"
                    raise ValueError(msg)
                self._resource_obj = conversions[self._restype](resource.data)

            else:
                data = BinaryReader.load_file(self.active())
                self._resource_obj = conversions[self._restype](data)

        return self._resource_obj

    def add_locations(self, filepaths: list[Path]):
        """Adds a list of filepaths to the list of locations stored for the resource.

        If a filepath already exists, it is ignored.
        If the ModuleResource has not yet been activated, will activate it with the first filepath.

        Args:
        ----
            filepaths: A list of filepaths pointing to a location for the resource.
        """
        self._locations.extend(
            [
                filepath
                for filepath in filepaths
                if filepath not in self._locations
            ]
        )
        if self._active is None and self._locations:
            self.activate(self._locations[0])

    def locations(self) -> list[Path]:
        return self._locations

    def activate(
        self,
        filepath: os.PathLike | str | None = None,
    ):
        """Sets the active file to the specified path. Calling this method will reset the loaded resource.

        Raises:
        ------
            ValueError: If the filepath is not stored in the resource list of locations.

        Args:
        ----
            filepath: The new active file.
        """
        self._resource_obj = None
        if filepath is None:
            self._active = self._locations[0] if self._locations else None

        else:
            r_filepath = Path.pathify(filepath)
            if r_filepath in self._locations:
                self._active = r_filepath
            else:
                msg = f"The filepath '{self._active}' is not being tracked as a location for the resource."
                raise ValueError(msg)

    def unload(self):
        """Clears the cached resource object from memory."""
        self._resource_obj = None

    def reload(self):
        """Reloads the resource object from the active location."""
        self._resource_obj = None
        self.resource()

    def active(self) -> Path:
        """Returns the filepath of the currently active file for the resource.

        Returns:
        -------
            Filepath to the active resource.
        """
        if self._active is None:
            raise RuntimeError(f"{self!r}.activate(filepath) must be called before use.")
        return self._active

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

        if is_bif_file(self.active().name):
            msg = "Cannot save file to BIF."
            raise ValueError(msg)

        if is_any_erf_type_file(self.active().name):
            erf: ERF = read_erf(self.active())
            erf.set_data(
                self._resname,
                self._restype,
                conversions[self._restype](self.resource()),
            )
            write_erf(erf, self.active())

        elif is_rim_file(self.active().name):
            rim: RIM = read_rim(self.active())
            rim.set_data(
                self._resname,
                self._restype,
                conversions[self._restype](self.resource()),
            )
            write_rim(rim, self.active())

        else:
            BinaryWriter.dump(self.active(), conversions[self._restype](self.resource()))
