from __future__ import annotations

import os.path
from copy import copy
from typing import List, TypeVar, Generic, Optional, Dict, Type, Any

from pykotor.resource.formats.vis import load_vis
from pykotor.resource.formats.vis.data import VIS

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.tpc import TPC, load_tpc

from pykotor.resource.generics.ifo import IFO, construct_ifo
from pykotor.resource.generics.are import ARE, construct_are
from pykotor.resource.generics.git import GIT, construct_git
from pykotor.resource.generics.pth import PTH, construct_pth
from pykotor.resource.generics.dlg import DLG, construct_dlg
from pykotor.resource.generics.uts import UTS, construct_uts
from pykotor.resource.generics.utw import UTW, construct_utw
from pykotor.resource.generics.utt import UTT, construct_utt
from pykotor.resource.generics.ute import UTE, construct_ute
from pykotor.resource.generics.utm import UTM, construct_utm
from pykotor.resource.generics.uti import UTI, construct_uti
from pykotor.resource.generics.utd import UTD, construct_utd
from pykotor.resource.generics.utp import UTP, construct_utp

from pykotor.resource.formats.gff import load_gff
from pykotor.resource.formats.twoda import load_2da
from pykotor.resource.type import ResourceType

from pykotor.extract.capsule import Capsule

from pykotor.resource.formats.lyt.auto import load_lyt

from pykotor.extract.installation import Installation, SearchLocation

from pykotor.resource.formats.lyt import LYT
from pykotor.resource.generics.utc import UTC, construct_utc

T = TypeVar('T')
SEARCH_ORDER = [SearchLocation.OVERRIDE, SearchLocation.CUSTOM_MODULES, SearchLocation.CHITIN]


class Module:
    def __init__(self, root: str, installation: Installation, custom_capsule: Optional[Capsule] = None):
        self._installation = installation

        self._capsules = [custom_capsule] if custom_capsule is not None else []
        self._capsules.extend([Capsule(installation.module_path() + module) for module in installation.module_names() if root in module])

        for capsule in self._capsules:
            if capsule.exists("module", ResourceType.IFO):
                ifo = load_gff(capsule.resource("module", ResourceType.IFO))
                self._id = ifo.root.get_resref("Mod_Entry_Area").get()
                break
        else:
            raise ValueError("Unable to locate module IFO file for '{}'.".format(root))

        self.creatures: Dict[str, ModuleResource[UTC]] = {}
        self.placeables: Dict[str, ModuleResource[UTP]] = {}
        self.doors: Dict[str, ModuleResource[UTD]] = {}
        self.items: Dict[str, ModuleResource[UTI]] = {}
        self.merchants: Dict[str, ModuleResource[UTM]] = {}
        self.encounters: Dict[str, ModuleResource[UTE]] = {}
        self.triggers: Dict[str, ModuleResource[UTT]] = {}
        self.waypoints: Dict[str, ModuleResource[UTW]] = {}
        self.sounds: Dict[str, ModuleResource[UTS]] = {}
        self.dialog: Dict[str, ModuleResource[DLG]] = {}
        self.scripts: Dict[str, ModuleResource] = {}
        self.textures: Dict[str, ModuleResource[TPC]] = {}

        self.layout: ModuleResource[LYT] = ModuleResource(self._id, ResourceType.LYT, installation, [])
        self.visibility: ModuleResource[VIS] = ModuleResource(self._id, ResourceType.VIS, installation, [])
        self.dynamic: ModuleResource[GIT] = ModuleResource(self._id, ResourceType.GIT, installation, [])
        self.static: ModuleResource[ARE] = ModuleResource(self._id, ResourceType.ARE, installation, [])
        self.path: ModuleResource[PTH] = ModuleResource(self._id, ResourceType.PTH, installation, [])
        self.info: ModuleResource[IFO] = ModuleResource("module", ResourceType.IFO, installation, [])

        self.restype_to_resources = {
            ResourceType.UTC: self.creatures,
            ResourceType.UTP: self.placeables,
            ResourceType.UTD: self.doors,
            ResourceType.UTI: self.items,
            ResourceType.UTM: self.merchants,
            ResourceType.UTE: self.encounters,
            ResourceType.UTT: self.triggers,
            ResourceType.UTW: self.waypoints,
            ResourceType.UTS: self.sounds,
            ResourceType.DLG: self.dialog,
            ResourceType.NCS: self.scripts,
            ResourceType.TPC: self.textures
        }

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
        root = os.path.basename(filepath).replace(".rim", "").replace(".erf", "").replace(".mod", "").lower()
        roota = root[:5]
        rootb = root[5:]
        if "_" in rootb:
            rootb = rootb[:rootb.index("_")]
        return roota + rootb

    def reload_resources(self):
        utc_list = set()
        utp_list = set()
        utd_list = set()
        uti_list = set()
        utm_list = set()
        ute_list = set()
        utt_list = set()
        utw_list = set()
        uts_list = set()
        dlg_list = set()
        ncs_list = set()

        for capsule in self._capsules:
            for resource in capsule:
                resname = resource.resname()
                restype = resource.restype()

                if restype in self.restype_to_resources:
                    self.add_locations(resname, restype, [capsule.path()])

                if resource.restype() == ResourceType.GIT:
                    git = construct_git(load_gff(capsule.resource(self._id, ResourceType.GIT)))
                    utc_list = utc_list.union(set([creature.resref.get() for creature in git.creatures]))
                    utp_list = utp_list.union(set([placeable.resref.get() for placeable in git.placeables]))
                    utd_list = utd_list.union(set([door.resref.get() for door in git.doors]))
                    utm_list = utm_list.union(set([merchant.resref.get() for merchant in git.stores]))
                    ute_list = ute_list.union(set([encounter.resref.get() for encounter in git.encounters]))
                    utt_list = utt_list.union(set([trigger.resref.get() for trigger in git.triggers]))
                    utw_list = utw_list.union(set([waypoint.resref.get() for waypoint in git.waypoints]))
                    uts_list = uts_list.union(set([sound.resref.get() for sound in git.sounds]))

        for utc_resname in utc_list:
            search = self._installation.location(utc_resname, ResourceType.UTC, SEARCH_ORDER)
            self.add_locations(utc_resname, ResourceType.UTC, [result.filepath for result in search])

        for utp_resname in utp_list:
            search = self._installation.location(utp_resname, ResourceType.UTP, SEARCH_ORDER)
            self.add_locations(utp_resname, ResourceType.UTP, [result.filepath for result in search])

        for utd_resname in utd_list:
            search = self._installation.location(utd_resname, ResourceType.UTD, SEARCH_ORDER)
            self.add_locations(utd_resname, ResourceType.UTD, [result.filepath for result in search])

        for uti_resname in uti_list:
            search = self._installation.location(uti_resname, ResourceType.UTI, SEARCH_ORDER)
            self.add_locations(uti_resname, ResourceType.UTI, [result.filepath for result in search])

        for utm_resname in utm_list:
            search = self._installation.location(utm_resname, ResourceType.UTM, SEARCH_ORDER)
            self.add_locations(utm_resname, ResourceType.UTM, [result.filepath for result in search])

        for ute_resname in ute_list:
            search = self._installation.location(ute_resname, ResourceType.UTE, SEARCH_ORDER)
            self.add_locations(ute_resname, ResourceType.UTE, [result.filepath for result in search])

        for utt_resname in utt_list:
            search = self._installation.location(utt_resname, ResourceType.UTT, SEARCH_ORDER)
            self.add_locations(utt_resname, ResourceType.UTT, [result.filepath for result in search])

        for utw_resname in utw_list:
            search = self._installation.location(utw_resname, ResourceType.UTW, SEARCH_ORDER)
            self.add_locations(utw_resname, ResourceType.UTW, [result.filepath for result in search])

        for uts_resname in uts_list:
            search = self._installation.location(uts_resname, ResourceType.UTS, SEARCH_ORDER)
            self.add_locations(uts_resname, ResourceType.UTS, [result.filepath for result in search])

        self.info = ModuleResource("module", ResourceType.IFO, self._installation, [])
        search = self._installation.location("module", ResourceType.IFO, SEARCH_ORDER, capsules=self._capsules)
        self.info.add_locations([result.filepath for result in search])

        self.static = ModuleResource(self._id, ResourceType.ARE, self._installation, [])
        search = self._installation.location(self._id, ResourceType.ARE, SEARCH_ORDER, capsules=self._capsules)
        self.static.add_locations([result.filepath for result in search])

        self.dynamic = ModuleResource(self._id, ResourceType.GIT, self._installation, [])
        search = self._installation.location(self._id, ResourceType.GIT, SEARCH_ORDER, capsules=self._capsules)
        self.dynamic.add_locations([result.filepath for result in search])

        self.path = ModuleResource(self._id, ResourceType.PTH, self._installation, [])
        search = self._installation.location(self._id, ResourceType.PTH, SEARCH_ORDER, capsules=self._capsules)
        self.path.add_locations([result.filepath for result in search])

        self.layout = ModuleResource(self._id, ResourceType.LYT, self._installation, [])
        search = self._installation.location(self._id, ResourceType.LYT, SEARCH_ORDER, capsules=self._capsules)
        self.layout.add_locations([result.filepath for result in search])

        self.visibility = ModuleResource(self._id, ResourceType.VIS, self._installation, [])
        search = self._installation.location(self._id, ResourceType.VIS, SEARCH_ORDER, capsules=self._capsules)
        self.visibility.add_locations([result.filepath for result in search])

    def add_locations(self, resname: str, restype: ResourceType, locations: List[str]):
        resource_list = self.restype_to_resources[restype]
        if resname in resource_list:
            resource_list[resname].add_locations(locations)
        else:
            resource_list[resname] = ModuleResource(resname, restype, self._installation, locations)


class ModuleResource(Generic[T]):
    def __init__(self, resname: str, restype: ResourceType, installation: Installation,
                 locations: List[str]):
        self.resname: str = resname
        self._installation = installation
        self.restype: ResourceType = restype
        self.active: Optional[str] = locations[0] if len(locations) > 0 else None
        self.locations: List[str] = locations

    def resource(self) -> T:
        conversions = {
            ResourceType.UTC: (lambda data: construct_utc(load_gff(data))),
            ResourceType.UTP: (lambda data: construct_utp(load_gff(data))),
            ResourceType.UTD: (lambda data: construct_utd(load_gff(data))),
            ResourceType.UTI: (lambda data: construct_uti(load_gff(data))),
            ResourceType.UTM: (lambda data: construct_utm(load_gff(data))),
            ResourceType.UTE: (lambda data: construct_ute(load_gff(data))),
            ResourceType.UTT: (lambda data: construct_utt(load_gff(data))),
            ResourceType.UTW: (lambda data: construct_utw(load_gff(data))),
            ResourceType.UTS: (lambda data: construct_uts(load_gff(data))),
            ResourceType.DLG: (lambda data: construct_dlg(load_gff(data))),
            ResourceType.PTH: (lambda data: construct_pth(load_gff(data))),
            ResourceType.NCS: (lambda data: data),
            ResourceType.TPC: (lambda data: load_tpc(data)),
            ResourceType.LYT: (lambda data: load_lyt(data)),
            ResourceType.VIS: (lambda data: load_vis(data)),
            ResourceType.IFO: (lambda data: construct_ifo(load_gff(data))),
            ResourceType.ARE: (lambda data: construct_are(load_gff(data))),
            ResourceType.GIT: (lambda data: construct_git(load_gff(data)))
        }

        if self.active is None:
            ...
        elif self.active.endswith(".erf") or self.active.endswith(".mod") or self.active.endswith(".rim"):
            capsule = Capsule(self.active)
            data = capsule.resource(self.resname, self.restype)
            return conversions[self.restype](data)
        elif self.active.endswith("bif"):
            data = self._installation.resource(self.resname, self.restype, [SearchLocation.CHITIN]).data
            return conversions[self.restype](data)
        else:
            data = BinaryReader.load_file(self.active)
            return conversions[self.restype](data)

    def add_locations(self, filepaths: List[str]) -> None:
        self.locations.extend([filepath for filepath in filepaths if filepath not in self.locations])
        self.active = self.locations[0] if self.active is None and self.locations else self.active
