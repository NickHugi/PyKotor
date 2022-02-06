from __future__ import annotations

import os.path
from typing import List, TypeVar, Generic, Optional, Dict

from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.tpc import TPC, load_tpc

from pykotor.resource.generics.ifo import IFO
from pykotor.resource.generics.are import ARE
from pykotor.resource.generics.git import GIT
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

from pykotor.extract.installation import Installation

from pykotor.resource.formats.lyt import LYT
from pykotor.resource.generics.utc import UTC, construct_utc


T = TypeVar('T')


class Module:
    def __init__(self, name: str, installation: Installation, custom_capsule: Optional[Capsule] = None):
        self.installation = installation

        self._capsules = [custom_capsule] if custom_capsule is not None else []
        self._capsules.extend([Capsule(installation.module_path() + module) for module in self.installation.module_names() if name in module])

        for capsule in self._capsules:
            if capsule.exists("module", ResourceType.IFO):
                ifo = load_gff(capsule.resource("module", ResourceType.IFO))
                self._id = ifo.root.get_resref("Mod_Entry_Area").get()
                break
        else:
            raise ValueError("Unable to locate module IFO file.")

        self._creatures: Dict[str, ModuleResource[UTC]] = {}
        self._placeables: Dict[str, ModuleResource[UTP]] = {}
        self._doors: Dict[str, ModuleResource[UTD]] = {}
        self._items: Dict[str, ModuleResource[UTI]] = {}
        self._merchants: Dict[str, ModuleResource[UTM]] = {}
        self._encounters: Dict[str, ModuleResource[UTE]] = {}
        self._triggers: Dict[str, ModuleResource[UTT]] = {}
        self._waypoints: Dict[str, ModuleResource[UTW]] = {}
        self._sounds: Dict[str, ModuleResource[UTS]] = {}
        self._dialog: Dict[str, ModuleResource[DLG]] = {}
        self._paths: Dict[str, ModuleResource[PTH]] = {}
        self._scripts: Dict[str, ModuleResource[bytes]] = {}
        self._textures: Dict[str, ModuleResource[TPC]] = {}

        self._layout: ModuleResource[LYT] = ModuleResource(self._id, LYT(), None, [])
        self._dynamic: ModuleResource[GIT] = ModuleResource(self._id, GIT(), None, [])
        self._static: ModuleResource[ARE] = ModuleResource(self._id, ARE(), None, [])
        self._info: ModuleResource[IFO] = ModuleResource("module", IFO(), None, [])

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
        root = os.path.basename(filepath).replace(".rim", "").replace(".erf", "").replace(".mod", "")
        roota = root[:5]
        rootb = root[5:]
        if "_" in rootb:
            rootb = rootb[:rootb.index("_")]
        return roota + rootb

    def reload_resources(self):
        self._layout: ModuleResource[LYT] = ModuleResource(self._id, LYT(), None, [])
        self._dynamic: ModuleResource[GIT] = ModuleResource(self._id, GIT(), None, [])
        self._static: ModuleResource[ARE] = ModuleResource(self._id, ARE(), None, [])
        self._info: ModuleResource[IFO] = ModuleResource("module", IFO(), None, [])

        load_list = {
            ResourceType.UTC: (self._creatures, lambda data: construct_utc(load_gff(data))),
            ResourceType.UTP: (self._placeables, lambda data: construct_utp(load_gff(data))),
            ResourceType.UTD: (self._doors, lambda data: construct_utd(load_gff(data))),
            ResourceType.UTI: (self._items, lambda data: construct_uti(load_gff(data))),
            ResourceType.UTM: (self._merchants, lambda data: construct_utm(load_gff(data))),
            ResourceType.UTE: (self._encounters, lambda data: construct_ute(load_gff(data))),
            ResourceType.UTT: (self._triggers, lambda data: construct_utt(load_gff(data))),
            ResourceType.UTW: (self._waypoints, lambda data: construct_utw(load_gff(data))),
            ResourceType.UTS: (self._sounds, lambda data: construct_uts(load_gff(data))),
            ResourceType.DLG: (self._dialog, lambda data: construct_dlg(load_gff(data))),
            ResourceType.PTH: (self._paths, lambda data: construct_pth(load_gff(data))),
            ResourceType.NCS: (self._scripts, lambda data: data),
            ResourceType.TPC: (self._textures, lambda data: load_tpc(data))
        }

        for capsule in self._capsules:
            for resource in capsule:
                if resource.restype() in load_list:
                    dictionary, compile = load_list[resource.restype()]
                    res = compile(resource.data())
                    if resource.resref() not in dictionary:
                        dictionary[resource.resref()] = ModuleResource(resource.resref(), res, capsule.path(), [capsule.path()])
                    else:
                        dictionary[resource.resref()].add_location(capsule.path())

                if resource.restype() == ResourceType.LYT:
                    self._layout.resource = load_lyt(resource.data()) if self._layout.resource is None else self._layout.resource
                    self._layout.active = capsule.path() if self._layout.active is None else self._layout.active
                    self._layout.add_location(capsule.path())

                if resource.restype() == ResourceType.IFO:
                    self._info.resource = load_lyt(resource.data()) if self._info.resource is None else self._info.resource
                    self._info.active = capsule.path() if self._info.active is None else self._info.active
                    self._info.add_location(capsule.path())

                if resource.restype() == ResourceType.ARE:
                    self._static.resource = load_lyt(resource.data()) if self._static.resource is None else self._static.resource
                    self._static.active = capsule.path() if self._static.active is None else self._static.active
                    self._static.add_location(capsule.path())

                if resource.restype() == ResourceType.GIT:
                    self._dynamic.resource = load_lyt(resource.data()) if self._dynamic.resource is None else self._dynamic.resource
                    self._dynamic.active = capsule.path() if self._dynamic.active is None else self._dynamic.active
                    self._dynamic.add_location(capsule.path())


class ModuleResource(Generic[T]):
    def __init__(self, resname: str, resource: Optional[T], active: Optional[str], locations: List[str]):
        self._resname: str = resname
        self._resource: T = resource
        self._active: str = active
        self._locations: List[str] = locations

    def change_active(self, location: str) -> None:
        if location not in self._locations:
            raise ValueError("Location specified is not valid.")

        if location.endswith(".erf") or location.endswith(".mod") or location.endswith(".rim"):
            capsule = Capsule(location)
            data = capsule.resource(self._resname, T)
        else:
            data = BinaryReader.load_file(location)

    def resource(self) -> T:
        return self._resource

    def active(self) -> str:
        return self._active

    def add_location(self, location: str) -> None:
        self._locations.append(location)
