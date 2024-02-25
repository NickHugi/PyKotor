from __future__ import annotations

from copy import copy
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from pykotor.common.misc import CaseInsensitiveDict
from pykotor.common.stream import BinaryReader, BinaryWriter
from pykotor.extract.capsule import Capsule
from pykotor.extract.file import ResourceIdentifier
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.bwm import bytes_bwm, read_bwm
from pykotor.resource.formats.erf import read_erf, write_erf
from pykotor.resource.formats.gff import read_gff
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
from utility.error_handling import assert_with_variable_trace, format_exception_with_variables
from utility.system.path import Path, PurePath

if TYPE_CHECKING:
    import os

    from collections.abc import Callable

    from pykotor.common.misc import ResRef
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


class Module:  # noqa: PLR0904
    def __init__(
        self,
        root: str,
        installation: Installation,
        custom_capsule: Capsule | None = None,
    ):
        self.resources: CaseInsensitiveDict[ModuleResource] = CaseInsensitiveDict()
        self._installation: Installation = installation
        self._root: str = root.lower()

        # Build list of capsules from all .mods' in the provided installation
        self._capsules: list[Capsule] = [
            Capsule(installation.module_path() / module)
            for module in installation.module_names()
            if root in module
        ]
        # Append the custom capsule if provided
        if custom_capsule is not None:
            self._capsules.append(custom_capsule)

        # Fast-fail if capsules list is empty.
        if not self._capsules:
            msg = f"Module resource with root '{root}' not found in the provided installation."
            raise FileNotFoundError(msg)

        # Find the relevant IFO in the newly constructed capsules.
        module_resource: bytes | None = next(
            (capsule.resource("module", ResourceType.IFO) for capsule in self._capsules),
            None,
        )
        if module_resource is None:
            msg = f"Unable to locate IFO file in any modules in the installation that match the pattern '{root}'."
            raise FileNotFoundError(msg)

        ifo: GFF = read_gff(module_resource)
        self._id: ResRef = ifo.root.get_resref("Mod_Entry_Area")

        self.reload_resources()

    @staticmethod
    def get_root(
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

    def capsules(self) -> list[Capsule]:
        """Returns a copy of the capsules used by the module.

        Returns:
        -------
            A list of linked capsules.
        """
        return copy(self._capsules)  # FIXME: Capsule class is already documented as mutable (reloads on demand). Why make copies?

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
        for capsule in self._capsules:
            for resource in capsule:
                self.add_locations(
                    resource.resname(),
                    resource.restype(),
                    [capsule.path()],
                )

        # Look for LYT/VIS
        for resource in self._installation.chitin_resources():
            if resource.resname() == self._id:
                self.add_locations(
                    resource.resname(),
                    resource.restype(),
                    [resource.filepath()],
                )
        for directory in self._installation.override_list():
            for resource in self._installation.override_resources(directory):
                if resource.resname() == self._id:
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
            try:
                data: bytes = model.data()
                for texture in list_textures(data):
                    textures.add(texture)
                for lightmap in list_lightmaps(data):
                    textures.add(lightmap)
            except Exception as e:
                print(format_exception_with_variables(e, message=f"Exception occurred when executing {self!r}.reload_resources() with model '{model.resname()}.{model.restype()}'"))

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
            if not locations:
                continue
            self.add_locations(
                identifier.resname,
                identifier.restype,
                [location.filepath for location in locations],
            )

        for module_resource in self.resources.values():
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
        filename_ext = (ResourceType.TPC if restype == ResourceType.TGA else restype).extension
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
            _id: The ID of the layout resource

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
                if (resource.resname() == self._id and resource.restype() == ResourceType.LYT)
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
                if (resource.resname() == self._id and resource.restype() == ResourceType.VIS)
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
                if resource.resname() == self._id and resource.restype() == ResourceType.ARE
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
                if resource.resname() == self._id and resource.restype() == ResourceType.GIT
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
                if resource.resname() == self._id and resource.restype() == ResourceType.PTH
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
                if resource.resname().lower() == "module" and resource.restype() == ResourceType.IFO
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
                if lower_resname == resource.resname().lower() and resource.restype() == ResourceType.UTC
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
        return [resource for resource in self.resources.values() if resource.restype() == ResourceType.UTC]

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
                if lower_resname == resource.resname().lower() and resource.restype() == ResourceType.UTP
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
        return [resource for resource in self.resources.values() if resource.restype() == ResourceType.UTP]

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
                if lower_resname == resource.resname().lower() and resource.restype() == ResourceType.UTD
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
        return [resource for resource in self.resources.values() if resource.restype() == ResourceType.UTD]

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
                if lower_resname == resource.resname().lower() and resource.restype() == ResourceType.UTI
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
        return [resource for resource in self.resources.values() if resource.restype() == ResourceType.UTD]

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
                if lower_resname == resource.resname().lower() and resource.restype() == ResourceType.UTE
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
        return [resource for resource in self.resources.values() if resource.restype() == ResourceType.UTE]

    def store(self, resname: str) -> ModuleResource[UTM] | None:
        """Looks up a material (UTM) resource by the specified resname from this module and returns the resource data.

        Args:
        ----
            resname: Name of the resource to look up

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
                if lower_resname == resource.resname().lower() and resource.restype() == ResourceType.UTM
            ),
            None,
        )

    def stores(
        self,
    ) -> list[ModuleResource[UTM]]:
        """Returns a list of material (UTM) resources for this module."""
        return [resource for resource in self.resources.values() if resource.restype() == ResourceType.UTM]

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
                if lower_resname == resource.resname().lower() and resource.restype() == ResourceType.UTT
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
        return [resource for resource in self.resources.values() if resource.restype() == ResourceType.UTT]

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
                if lower_resname == resource.resname().lower() and resource.restype() == ResourceType.UTW
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
        return [resource for resource in self.resources.values() if resource.restype() == ResourceType.UTW]

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
                if lower_resname == resource.resname().lower() and resource.restype() == ResourceType.MDL
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
                if lower_resname == resource.resname().lower() and resource.restype() == ResourceType.MDX
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
        return [resource for resource in self.resources.values() if resource.restype() == ResourceType.MDL]

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
        return [resource for resource in self.resources.values() if resource.restype() == ResourceType.MDX]

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
                if lower_resname == resource.resname().lower() and resource.restype() == ResourceType.UTS
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
        return [resource for resource in self.resources.values() if resource.restype() == ResourceType.UTS]


class ModuleResource(Generic[T]):
    def __init__(self, resname: str, restype: ResourceType, installation: Installation):
        self._resname: str = resname
        self._installation: Installation = installation
        self._restype: ResourceType = restype
        self._active: Path | None = None
        self._resource_obj: Any = None
        self._locations: list[Path] = []
        self._identifier = ResourceIdentifier(resname, restype)

    def __eq__(self, other):
        return hash(self) == hash(other)

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
        if isinstance(res, UTP):
            return self._installation.string(res.name)
        if isinstance(res, UTD):
            return self._installation.string(res.name)
        if isinstance(res, UTW):
            return self._installation.string(res.name)
        if isinstance(res, UTT):
            return self._installation.string(res.name)
        if isinstance(res, UTE):
            return self._installation.string(res.name)
        if isinstance(res, UTM):
            return self._installation.string(res.name)
        if isinstance(res, UTS):
            return self._installation.string(res.name)
        print(f"Could not find res of type {type(res)}")
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
        if self._active is None:
            msg = f"No file is currently active for resource '{file_name}'."
            raise ValueError(msg)

        if is_capsule_file(self._active):
            data: bytes | None = Capsule(self._active).resource(self._resname, self._restype)
            if data is None:
                msg = f"Resource '{file_name}' not found in '{self._active}'"
                raise ValueError(msg)
            return data

        if is_bif_file(self._active):
            resource: ResourceResult | None = self._installation.resource(
                self._resname,
                self._restype,
                [SearchLocation.CHITIN],
            )
            if resource is None:
                msg = f"Resource '{file_name}' not found in '{self._active}'"
                raise ValueError(msg)
            return resource.data

        return BinaryReader.load_file(self._active)

    def resource(self) -> T | None:
        """Returns the cached resource object. If no object has been cached, then it will load the object.

        Returns:
        -------
            The resource object.
        """
        if self._resource_obj is None:
            conversions: dict[ResourceType, Callable[[SOURCE_TYPES], Any]] = {
                ResourceType.UTC: read_utc,
                ResourceType.UTP: read_utp,
                ResourceType.UTD: read_utd,
                ResourceType.UTI: read_uti,
                ResourceType.UTM: read_utm,
                ResourceType.UTE: read_ute,
                ResourceType.UTT: read_utt,
                ResourceType.UTW: read_utw,
                ResourceType.UTS: read_uts,
                ResourceType.DLG: read_dlg,
                ResourceType.PTH: read_pth,
                ResourceType.NCS: lambda data: data,
                ResourceType.TPC: read_tpc,
                ResourceType.TGA: read_tpc,
                ResourceType.LYT: read_lyt,
                ResourceType.VIS: read_vis,
                ResourceType.IFO: read_ifo,
                ResourceType.ARE: read_are,
                ResourceType.GIT: read_git,
                ResourceType.WOK: read_bwm,
            }

            file_name: str = f"{self._resname}.{self._restype.extension}"
            if self._active is None:
                try:
                    assert_with_variable_trace(self._resource_obj is not None)
                except Exception as e:
                    with Path("errorlog.txt").open("a", encoding="utf-8") as file:
                        lines = format_exception_with_variables(e)
                        file.writelines(lines)
                        file.write("\n----------------------\n")
                self._resource_obj = None

            elif is_capsule_file(self._active.name):
                data: bytes | None = Capsule(self._active).resource(self._resname, self._restype)
                if data is None:
                    msg = f"Resource '{file_name}' not found in '{self._active}'"
                    raise ValueError(msg)
                self._resource_obj = conversions[self._restype](data)

            elif is_bif_file(self._active.name):
                resource: ResourceResult | None = self._installation.resource(
                    self._resname,
                    self._restype,
                    [SearchLocation.CHITIN],
                )
                if resource is None:
                    msg = f"Resource '{file_name}' not found in '{self._active}'"
                    raise ValueError(msg)
                self._resource_obj = conversions[self._restype](resource.data)

            else:
                data = BinaryReader.load_file(self._active)
                self._resource_obj = conversions[self._restype](data)

        return self._resource_obj

    def add_locations(self, filepaths: list[Path]):
        """Adds a list of filepaths to the list of locations stored for the resource.

        If a filepath already exists, it is ignored.

        Args:
        ----
            filepaths: A list of filepaths pointing to a location for the resource.
        """
        self._locations.extend([filepath for filepath in filepaths if filepath not in self._locations])
        if self._active is None and self._locations:
            self.activate(self._locations[0])

    def locations(
        self,
    ) -> list[Path]:
        return self._locations

    def activate(self, filepath: os.PathLike | str | None = None):
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
            msg = "Active resource is not set."
            raise ValueError(msg)

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
            ResourceType.UTC: bytes_utc,
            ResourceType.UTP: bytes_utp,
            ResourceType.UTD: bytes_utd,
            ResourceType.UTI: bytes_uti,
            ResourceType.UTM: bytes_utm,
            ResourceType.UTE: bytes_ute,
            ResourceType.UTT: bytes_utt,
            ResourceType.UTW: bytes_utw,
            ResourceType.UTS: bytes_uts,
            ResourceType.DLG: bytes_dlg,
            ResourceType.PTH: bytes_pth,
            ResourceType.NCS: lambda res: res,
            ResourceType.TPC: bytes_tpc,
            ResourceType.TGA: bytes_tpc,
            ResourceType.LYT: bytes_lyt,
            ResourceType.VIS: bytes_vis,
            ResourceType.IFO: bytes_ifo,
            ResourceType.ARE: bytes_are,
            ResourceType.GIT: bytes_git,
            ResourceType.WOK: bytes_bwm,
        }

        if self._active is None:
            msg = f"No active file selected for resource '{self._resname}.{self._restype.extension}'"
            raise ValueError(msg)

        if is_bif_file(self._active.name):
            msg = "Cannot save file to BIF."
            raise ValueError(msg)

        if is_any_erf_type_file(self._active.name):
            erf: ERF = read_erf(self._active)
            erf.set_data(
                self._resname,
                self._restype,
                conversions[self._restype](self.resource()),
            )
            write_erf(erf, self._active)

        elif is_rim_file(self._active.name):
            rim: RIM = read_rim(self._active)
            rim.set_data(
                self._resname,
                self._restype,
                conversions[self._restype](self.resource()),
            )
            write_rim(rim, self._active)

        else:
            BinaryWriter.dump(self._active, conversions[self._restype](self.resource()))
