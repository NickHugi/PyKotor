from __future__ import annotations

import os.path
from copy import copy
from typing import List, TypeVar, Generic, Optional, Dict

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

from pykotor.extract.installation import Installation

from pykotor.resource.formats.lyt import LYT
from pykotor.resource.generics.utc import UTC, construct_utc

T = TypeVar('T')


class Module:
    def __init__(self, name: str, installation: Installation, custom_capsule: Optional[Capsule] = None):
        self._installation = installation

        self._capsules = [custom_capsule] if custom_capsule is not None else []
        self._capsules.extend(
            [Capsule(installation.module_path() + module) for module in installation.module_names() if name in module])

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

        self.layout: ModuleResource[LYT] = ModuleResource(self._id, None, [])
        self.visibility: ModuleResource[VIS] = ModuleResource(self._id, None, [])
        self.dynamic: ModuleResource[GIT] = ModuleResource(self._id, None, [])
        self.static: ModuleResource[ARE] = ModuleResource(self._id, None, [])
        self.info: ModuleResource[IFO] = ModuleResource("module", None, [])

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
        self.layout: ModuleResource[LYT] = ModuleResource(self._id, None, [])
        self.dynamic: ModuleResource[GIT] = ModuleResource(self._id, None, [])
        self.static: ModuleResource[ARE] = ModuleResource(self._id, None, [])
        self.info: ModuleResource[IFO] = ModuleResource("module", None, [])

        load_list = {
            ResourceType.UTC: self._creatures,
            ResourceType.UTP: self._placeables,
            ResourceType.UTD: self._doors,
            ResourceType.UTI: self._items,
            ResourceType.UTM: self._merchants,
            ResourceType.UTE: self._encounters,
            ResourceType.UTT: self._triggers,
            ResourceType.UTW: self._waypoints,
            ResourceType.UTS: self._sounds,
            ResourceType.DLG: self._dialog,
            ResourceType.PTH: self._paths,
            ResourceType.NCS: self._scripts,
            ResourceType.TPC: self._textures
        }

        for capsule in self._capsules:
            for resource in capsule:
                if resource.restype() in load_list:
                    dictionary = load_list[resource.restype()]
                    if resource.resname() not in dictionary:
                        dictionary[resource.resname()] = ModuleResource(resource.resname(), capsule.path(), [capsule.path()])
                    else:
                        dictionary[resource.resname()].locations.append(capsule.path())

                if resource.restype() == ResourceType.LYT:
                    self.layout.active = capsule.path() if self.layout.active is None else self.layout.active
                    self.layout.locations.append(capsule.path())

                if resource.restype() == ResourceType.VIS:
                    self.visibility.active = capsule.path() if self.layout.active is None else self.visibility.active
                    self.visibility.locations.append(capsule.path())

                if resource.restype() == ResourceType.IFO:
                    self.info.active = capsule.path() if self.info.active is None else self.info.active
                    self.info.locations.append(capsule.path())

                if resource.restype() == ResourceType.ARE:
                    self.static.active = capsule.path() if self.static.active is None else self.static.active
                    self.static.locations.append(capsule.path())

                if resource.restype() == ResourceType.GIT:
                    self.dynamic.active = capsule.path() if self.dynamic.active is None else self.dynamic.active
                    self.dynamic.locations.append(capsule.path())

        lyts = self._installation.locate(self._id, ResourceType.LYT, capsules=self._capsules, skip_modules=True,
                                         skip_textures=True)
        for location in lyts:
            self.layout.active = location.filepath if self.layout.active is None else self.layout.active
            self.layout.locations.append(location.filepath)

        viss = self._installation.locate(self._id, ResourceType.VIS, capsules=self._capsules, skip_modules=True,
                                         skip_textures=True)
        for location in viss:
            self.visibility.active = location.filepath if self.visibility.active is None else self.visibility.active
            self.visibility.locations.append(location.filepath)


class ModuleResource(Generic[T]):
    def __init__(self, resname: str, active: Optional[str], locations: List[str]):
        self.resname: str = resname
        self.active: str = active
        self.locations: List[str] = locations

    def resource(self) -> T:
        conversion = {
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
            data = capsule.resource(self.resname, T.BINARY_TYPE)
            return conversion[T.BINARY_TYPE](data)
        else:
            data = BinaryReader.load_file(self.active)
            return conversion[T.BINARY_TYPE](data)
