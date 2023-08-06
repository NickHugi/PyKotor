from __future__ import annotations

import os.path
from contextlib import suppress
from copy import copy
from typing import Any, Generic, List, Optional, TypeVar

from pykotor.common.misc import CaseInsensitiveDict
from pykotor.common.stream import BinaryReader, BinaryWriter
from pykotor.extract.capsule import Capsule

from pykotor.extract.file import ResourceIdentifier

from pykotor.extract.installation import Installation, SearchLocation

from pykotor.resource.formats.bwm import read_bwm

from pykotor.resource.formats.bwm.bwm_auto import bytes_bwm
from pykotor.resource.formats.erf import ERFType, read_erf, write_erf
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.formats.lyt import LYT
from pykotor.resource.formats.lyt.lyt_auto import bytes_lyt, read_lyt
from pykotor.resource.formats.mdl import MDL
from pykotor.resource.formats.rim import read_rim, write_rim
from pykotor.resource.formats.tpc import TPC, read_tpc
from pykotor.resource.formats.tpc.tpc_auto import bytes_tpc
from pykotor.resource.formats.vis import VIS, read_vis
from pykotor.resource.formats.vis.vis_auto import bytes_vis
from pykotor.resource.generics.are import ARE, bytes_are, read_are
from pykotor.resource.generics.dlg import bytes_dlg, read_dlg
from pykotor.resource.generics.git import GIT, bytes_git, read_git
from pykotor.resource.generics.ifo import IFO, bytes_ifo, read_ifo
from pykotor.resource.generics.pth import PTH, bytes_pth, read_pth
from pykotor.resource.generics.utc import UTC, bytes_utc, read_utc
from pykotor.resource.generics.utd import UTD, bytes_utd, read_utd
from pykotor.resource.generics.ute import UTE, bytes_ute, read_ute
from pykotor.resource.generics.uti import UTI, bytes_uti, read_uti
from pykotor.resource.generics.utm import UTM, bytes_utm, read_utm
from pykotor.resource.generics.utp import UTP, bytes_utp, read_utp
from pykotor.resource.generics.uts import UTS, bytes_uts, read_uts
from pykotor.resource.generics.utt import UTT, bytes_utt, read_utt
from pykotor.resource.generics.utw import UTW, bytes_utw, read_utw
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import (
    is_bif_file,
    is_capsule_file,
    is_erf_or_mod_file,
    is_mod_file,
    is_rim_file,
)

from pykotor.tools.model import list_lightmaps, list_textures

T = TypeVar("T")
SEARCH_ORDER = [SearchLocation.OVERRIDE, SearchLocation.CUSTOM_MODULES, SearchLocation.CHITIN]


class Module:
    def __init__(
        self, root: str, installation: Installation, custom_capsule: Optional[Capsule] = None
    ):
        self._installation = installation
        self._root = root = root.lower()

        self._capsules = [custom_capsule] if custom_capsule is not None else []
        self._capsules.extend([
            Capsule(installation.module_path() + module)
            for module in installation.module_names()
            if root in module.lower()
        ])

        for capsule in self._capsules:
            if capsule.exists("module", ResourceType.IFO):
                ifo = read_gff(capsule.resource("module", ResourceType.IFO))
                self._id = ifo.root.get_resref("Mod_Entry_Area").get().lower()
                break
        else:
            raise ValueError(f"Unable to locate module IFO file for '{root}'.")
        self.resources: CaseInsensitiveDict[ModuleResource] = CaseInsensitiveDict()
        self.reload_resources()

    @staticmethod
    def get_root(filepath: str) -> str:
        """
        Returns the root name for a module from the given filepath (or filename). For example "danm13_s.rim" would
        become "danm13".

        Args:
            filepath: The filename or filepath of one of the module encapsulated file.

        Returns:
            The string for the root name of a module.
        """
        root = (
            os.path.basename(filepath)
            .replace(".rim", "")
            .replace(".erf", "")
            .replace(".mod", "")
            .lower()
        )
        root_a = root[:5]
        root_b = root[5:]
        if "_" in root_b:
            root_b = root_b[: root_b.index("_")]
        return root_a + root_b

    def capsules(self) -> List[Capsule]:
        """
        Returns a copy of the capsules used by the module.

        Returns:
            A list of linked capsules.
        """
        return copy(self._capsules)

    def reload_resources(self):
        # Look in module files
        for capsule in self._capsules:
            for resource in capsule:
                resname = resource.resname()
                restype = resource.restype()
                self.add_locations(resname, restype, [capsule.path()])
        # Look for LYT/VIS
        for resource in self._installation.chitin_resources():
            if resource.resname() == self._id:
                self.add_locations(resource.resname(), resource.restype(), [resource.filepath()])
        for directory in self._installation.override_list():
            for resource in self._installation.override_resources(directory):
                if resource.resname() == self._id:
                    self.add_locations(
                        resource.resname(), resource.restype(), [resource.filepath()]
                    )
        # Any resource linked in the GIT not present in the module files
        original = self.git().active()
        look_for = []
        for location in self.git().locations():
            self.git().activate(location)
            self.git().resource()
            git = self.git().resource()
            [look_for.append(ResourceIdentifier(creature.resref.get(), ResourceType.UTC)) for creature in git.creatures]
            [look_for.append(ResourceIdentifier(placeable.resref.get(), ResourceType.UTP)) for placeable in git.placeables]
            [look_for.append(ResourceIdentifier(door.resref.get(), ResourceType.UTD)) for door in git.doors]
            [look_for.append(ResourceIdentifier(sound.resref.get(), ResourceType.UTS)) for sound in git.sounds]
            [look_for.append(ResourceIdentifier(waypoint.resref.get(), ResourceType.UTW)) for waypoint in git.waypoints]
            [look_for.append(ResourceIdentifier(encounter.resref.get(), ResourceType.UTE)) for encounter in git.encounters]
            [look_for.append(ResourceIdentifier(trigger.resref.get(), ResourceType.UTT)) for trigger in git.triggers]
            [look_for.append(ResourceIdentifier(store.resref.get(), ResourceType.UTM)) for store in git.stores]
        self.git().activate(original)

        # Models referenced in LYTs
        original = self.layout().active()
        for location in self.layout().locations():
            self.layout().activate(location)
            layout = self.layout().resource()
            for room in layout.rooms:
                look_for.extend((
                    ResourceIdentifier(room.model, ResourceType.MDL),
                    ResourceIdentifier(room.model, ResourceType.MDX),
                    ResourceIdentifier(room.model, ResourceType.WOK),
                ))
        self.layout().activate(original)

        search = self._installation.locations(
            look_for, [SearchLocation.OVERRIDE, SearchLocation.CHITIN]
        )
        for identifier, locations in search.items():
            self.add_locations(
                identifier.resname,
                identifier.restype,
                [location.filepath for location in locations],
            )
        # Also try get paths for textures in models
        look_for = []
        textures = set()
        for model in self.models():
            with suppress(Exception):
                data = model.data()
                for texture in list_textures(data):
                    textures.add(texture)
                for lightmap in list_lightmaps(data):
                    textures.add(lightmap)
        for texture in textures:
            look_for.extend((
                ResourceIdentifier(texture, ResourceType.TPC),
                ResourceIdentifier(texture, ResourceType.TGA),
            ))
        search = self._installation.locations(
            look_for,
            [
                SearchLocation.OVERRIDE,
                SearchLocation.CHITIN,
                SearchLocation.TEXTURES_TPA,
                SearchLocation.TEXTURES_TPB,
                SearchLocation.TEXTURES_TPC,
        ],)
        for identifier, locations in search.items():
            if len(locations) == 0:
                continue
            self.add_locations(
                identifier.resname,
                identifier.restype,
                [location.filepath for location in locations],
            )
        for resource in self.resources.values():
            resource.activate()

    def add_locations(self, resname: str, restype: ResourceType, locations: List[str]):
        # In order to store TGA resources in the same ModuleResource as their TPC counterpart, we use the .TPC extension
        # instead of the .TGA for the dictionary key.
        filename_ext = str(ResourceType.TPC if restype == ResourceType.TGA else restype)
        filename = f"{resname}.{filename_ext}"
        if filename not in self.resources:
            self.resources[filename] = ModuleResource(resname, restype, self._installation)
        self.resources[filename].add_locations(locations)

    def installation(self) -> Installation:
        return self._installation

    def resource(self, resname: str, restype: ResourceType) -> Optional[ModuleResource]:
        filename = resname + "." + restype.extension
        return self.resources[filename] if filename in self.resources else None

    def layout(self) -> ModuleResource[LYT]:
        for filename, resource in self.resources.items():
            if resource.resname().lower() == self._id and resource.restype() == ResourceType.LYT:
                return resource

    def vis(self) -> ModuleResource[VIS]:
        for filename, resource in self.resources.items():
            if resource.resname().lower() == self._id and resource.restype() == ResourceType.VIS:
                return resource

    def are(self) -> ModuleResource[ARE]:
        for filename, resource in self.resources.items():
            if resource.resname().lower() == self._id and resource.restype() == ResourceType.ARE:
                return resource

    def git(self) -> ModuleResource[GIT]:
        for filename, resource in self.resources.items():
            if resource.resname().lower() == self._id and resource.restype() == ResourceType.GIT:
                return resource

    def pth(self) -> ModuleResource[PTH]:
        for filename, resource in self.resources.items():
            if resource.resname().lower() == self._id and resource.restype() == ResourceType.PTH:
                return resource

    def info(self) -> ModuleResource[IFO]:
        for filename, resource in self.resources.items():
            if resource.resname().lower() == "module" and resource.restype() == ResourceType.IFO:
                return resource

    def creature(self, resname: str) -> Optional[ModuleResource[UTC]]:
        for resource in self.resources.values():
            if resname == resource.resname() and resource.restype() == ResourceType.UTC:
                return resource
        return None

    def creatures(self) -> List[ModuleResource[UTC]]:
        return [
            resource
            for resource in self.resources.values()
            if resource.restype() == ResourceType.UTC
        ]

    def placeable(self, resname: str) -> Optional[ModuleResource[UTP]]:
        for resource in self.resources.values():
            if resname == resource.resname() and resource.restype() == ResourceType.UTP:
                return resource
        return None

    def placeables(self) -> List[ModuleResource[UTP]]:
        return [
            resource
            for resource in self.resources.values()
            if resource.restype() == ResourceType.UTP
        ]

    def door(self, resname: str) -> Optional[ModuleResource[UTD]]:
        for resource in self.resources.values():
            if resname == resource.resname() and resource.restype() == ResourceType.UTD:
                return resource
        return None

    def doors(self) -> List[ModuleResource[UTD]]:
        return [
            resource
            for resource in self.resources.values()
            if resource.restype() == ResourceType.UTD
        ]

    def item(self, resname: str) -> Optional[ModuleResource[UTI]]:
        for resource in self.resources.values():
            if resname == resource.resname() and resource.restype() == ResourceType.UTI:
                return resource
        return None

    def items(self) -> List[ModuleResource[UTI]]:
        return [
            resource
            for resource in self.resources.values()
            if resource.restype() == ResourceType.UTD
        ]

    def encounter(self, resname: str) -> Optional[ModuleResource[UTE]]:
        for resource in self.resources.values():
            if resname == resource.resname() and resource.restype() == ResourceType.UTE:
                return resource
        return None

    def encounters(self) -> List[ModuleResource[UTE]]:
        return [
            resource
            for resource in self.resources.values()
            if resource.restype() == ResourceType.UTE
        ]

    def store(self, resname: str) -> Optional[ModuleResource[UTM]]:
        for resource in self.resources.values():
            if resname == resource.resname() and resource.restype() == ResourceType.UTM:
                return resource
        return None

    def stores(self) -> List[ModuleResource[UTM]]:
        return [
            resource
            for resource in self.resources.values()
            if resource.restype() == ResourceType.UTM
        ]

    def trigger(self, resname: str) -> Optional[ModuleResource[UTT]]:
        for resource in self.resources.values():
            if resname == resource.resname() and resource.restype() == ResourceType.UTT:
                return resource
        return None

    def triggers(self) -> List[ModuleResource[UTT]]:
        return [
            resource
            for resource in self.resources.values()
            if resource.restype() == ResourceType.UTT
        ]

    def waypoint(self, resname: str) -> Optional[ModuleResource[UTW]]:
        for resource in self.resources.values():
            if resname == resource.resname() and resource.restype() == ResourceType.UTW:
                return resource
        return None

    def waypoints(self) -> List[ModuleResource[UTW]]:
        return [
            resource
            for resource in self.resources.values()
            if resource.restype() == ResourceType.UTW
        ]

    def model(self, resname: str) -> Optional[ModuleResource[MDL]]:
        return next((
            resource
            for resource in self.resources.values()
            if resname == resource.resname() and resource.restype() == ResourceType.MDL
            ),
            None,
        )

    def model_ext(self, resname: str) -> Optional[ModuleResource]:
        for resource in self.resources.values():
            if resname == resource.resname() and resource.restype() == ResourceType.MDX:
                return resource
        return None

    def models(self) -> List[ModuleResource[MDL]]:
        return [
            resource
            for resource in self.resources.values()
            if resource.restype() == ResourceType.MDL
        ]

    def texture(self, resname: str) -> Optional[ModuleResource[TPC]]:
        for resource in self.resources.values():
            if resname.lower() == resource.resname().lower() and resource.restype() in (
                ResourceType.TPC,
                ResourceType.TGA,
            ):
                return resource
        return None

    def textures(self) -> List[ModuleResource[MDL]]:
        return [
            resource
            for resource in self.resources.values()
            if resource.restype() in (ResourceType.TPC, ResourceType.TGA)
        ]

    def sound(self, resname: str) -> Optional[ModuleResource[UTS]]:
        for resource in self.resources.values():
            if resname == resource.resname() and resource.restype() == ResourceType.UTS:
                return resource
        return None

    def sounds(self) -> List[ModuleResource[UTS]]:
        return [
            resource
            for resource in self.resources.values()
            if resource.restype() == ResourceType.UTS
        ]



class ModuleResource(Generic[T]):
    def __init__(self, resname: str, restype: ResourceType, installation: Installation):
        self._resname: str = resname
        self._installation = installation
        self._restype: ResourceType = restype
        self._active: Optional[str] = None
        self._resource: Any = None
        self._locations: List[str] = []

    def resname(self) -> str:
        """
        Returns the resource name.

        Returns:
            The resource name.
        """
        return self._resname

    def restype(self) -> ResourceType:
        """
        Returns the type of resource stored.

        Returns:
            The resource type.
        """
        return self._restype

    def localized_name(self) -> Optional[str]:
        res = self.resource()
        if res is None:
            return None
        if isinstance(res, UTC):
            return (
                self._installation.string(res.first_name)
                + " "
                + self._installation.string(res.last_name)
            )
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
        return None

    def data(self) -> bytes:
        """
        Opens the file at the active location and returns the data.

        Raises:
            ValueError: If no file is active.

        Returns:
            The bytes data of the active file.
        """

        if self._active is None:
            raise ValueError(
                f"No file is currently active for resource '{self.resname}.{self._restype.extension}'."
            )
        if is_capsule_file(self._active):
            capsule = Capsule(self._active)
            return capsule.resource(self._resname, self._restype)
        if is_bif_file(self._active):
            return self._installation.resource(
                self._resname, self._restype, [SearchLocation.CHITIN]
            ).data
        return BinaryReader.load_file(self._active)

    def resource(self) -> Optional[T]:
        """
        Returns the cached resource object. If no object has been cached, then it will load the object.

        Returns:
            The resource object.
        """

        if self._resource is None:
            conversions = {
                ResourceType.UTC: (read_utc),
                ResourceType.UTP: (read_utp),
                ResourceType.UTD: (read_utd),
                ResourceType.UTI: (read_uti),
                ResourceType.UTM: (read_utm),
                ResourceType.UTE: (read_ute),
                ResourceType.UTT: (read_utt),
                ResourceType.UTW: (read_utw),
                ResourceType.UTS: (read_uts),
                ResourceType.DLG: (read_dlg),
                ResourceType.PTH: (read_pth),
                ResourceType.NCS: (lambda data: data),
                ResourceType.TPC: (read_tpc),
                ResourceType.TGA: (read_tpc),
                ResourceType.LYT: (read_lyt),
                ResourceType.VIS: (read_vis),
                ResourceType.IFO: (read_ifo),
                ResourceType.ARE: (read_are),
                ResourceType.GIT: (read_git),
                ResourceType.WOK: (read_bwm),
            }

            if self._active is None:
                self._resource = None
            elif is_capsule_file(self._active):
                data = Capsule(self._active).resource(self._resname, self._restype)
                self._resource = conversions[self._restype](data)
            elif is_bif_file(self._active):
                data = self._installation.resource(
                    self._resname, self._restype, [SearchLocation.CHITIN]
                ).data
                self._resource = conversions[self._restype](data)
            else:
                data = BinaryReader.load_file(self._active)
                self._resource = conversions[self._restype](data)
        return self._resource

    def add_locations(self, filepaths: List[str]) -> None:
        """
        Adds a list of filepaths to the list of locations stored for the resource. If a filepath already exists, it is
        ignored.

        Args:
            filepaths: A list of filepaths pointing to a location for the resource.
        """
        self._locations.extend(
            [filepath for filepath in filepaths if filepath not in self._locations]
        )
        if self._active is None and self._locations:
            self.activate(self._locations[0])

    def locations(
        self,
    ) -> List[str]:
        return self._locations

    def activate(self, filepath: str = None) -> None:
        """
        Sets the active file to the specified path. Calling this method will reset the loaded resource.

        Raises:
            ValueError: If the filepath is not stored in the resource list of locations.

        Args:
            filepath: The new active file.
        """
        self._resource = None
        if filepath is None:
            self._active = self._locations[0] if len(self._locations) > 0 else None
        elif filepath in self._locations:
            self._active = filepath
        else:
            raise ValueError(
                f"The filepath '{self._active}' is not being tracked as a location for the resource."
            )

    def unload(self) -> None:
        """
        Clears the cached resource object from memory.
        """
        self._resource = None

    def reload(self) -> None:
        """
        Reloads the resource object from the active location.
        """
        self._resource = None
        self.resource()

    def active(self) -> Optional[str]:
        """
        Returns the filepath of the currently active file for the resource.

        Returns:
            Filepath to the active resource.
        """
        return self._active

    def save(self) -> None:
        conversions = {
            ResourceType.UTC: (bytes_utc),
            ResourceType.UTP: (bytes_utp),
            ResourceType.UTD: (bytes_utd),
            ResourceType.UTI: (bytes_uti),
            ResourceType.UTM: (bytes_utm),
            ResourceType.UTE: (bytes_ute),
            ResourceType.UTT: (bytes_utt),
            ResourceType.UTW: (bytes_utw),
            ResourceType.UTS: (bytes_uts),
            ResourceType.DLG: (bytes_dlg),
            ResourceType.PTH: (bytes_pth),
            ResourceType.NCS: (lambda res: res),
            ResourceType.TPC: (bytes_tpc),
            ResourceType.TGA: (bytes_tpc),
            ResourceType.LYT: (bytes_lyt),
            ResourceType.VIS: (bytes_vis),
            ResourceType.IFO: (bytes_ifo),
            ResourceType.ARE: (bytes_are),
            ResourceType.GIT: (bytes_git),
            ResourceType.WOK: (bytes_bwm),
        }

        if self._active is None:
            raise ValueError(
                f"No active file selected for resource '{self._resname}.{self._restype.extension}'"
            )
        if is_erf_or_mod_file(self._active):
            erf = read_erf(self._active)
            erf.erf_type = ERFType.MOD if is_mod_file(self._active) else ERFType.ERF
            erf.set(self._resname, self._restype, conversions[self._restype](self.resource()))
            write_erf(erf, self._active)
        elif is_rim_file(self._active):
            rim = read_rim(self._active)
            rim.set(self._resname, self._restype, conversions[self._restype](self.resource()))
            write_rim(rim, self._active)
        elif is_bif_file(self._active):
            raise ValueError("Cannot save file to BIF.")
        else:
            BinaryWriter.dump(self._active, conversions[self._restype](self.resource()))
