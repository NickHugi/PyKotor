from __future__ import annotations

import math
from copy import copy, deepcopy
from typing import List, Optional, Tuple

from pykotor.common.geometry import Vector3, Vector2
from pykotor.common.misc import ResRef
from pykotor.resource.formats.bwm import BWM
from pykotor.resource.formats.bwm.bwm_auto import bytes_bwm
from pykotor.resource.formats.erf import ERF, ERFType, write_erf
from pykotor.resource.formats.lyt import LYT, LYTRoom
from pykotor.resource.formats.lyt.lyt_auto import bytes_lyt
from pykotor.resource.formats.vis import VIS
from pykotor.resource.formats.vis.vis_auto import bytes_vis
from pykotor.resource.generics.are import ARE, bytes_are
from pykotor.resource.generics.git import GIT, bytes_git
from pykotor.resource.generics.ifo import IFO, bytes_ifo
from pykotor.resource.type import ResourceType
from pykotor.tools import model

from tools.indoormap.indoorkit import KitComponent, KitComponentHook


class IndoorMap:
    def __init__(self):
        self.rooms: List[IndoorMapRoom] = []

    def rebuildRoomConnections(self) -> None:
        for room in self.rooms:
            room.rebuildConnections(self.rooms)

    def build(self, mod_id: str, output_path: str) -> None:
        mod = ERF(ERFType.MOD)
        lyt = LYT()
        vis = VIS()
        are = ARE()
        ifo = IFO()
        git = GIT()

        for i in range(len(self.rooms)):
            modelname = "{}_room{}".format(mod_id, i)
            vis.add_room(modelname)

        for i, room in enumerate(self.rooms):
            modelname = "{}_room{}".format(mod_id, i)
            lyt.rooms.append(LYTRoom(modelname, room.position))

            for j in range(len(self.rooms)):
                if j != i:
                    vis.set_visible(modelname, "{}_room{}".format(mod_id, j), True)

            mdl = room.component.mdl
            mdl = model.transform(mdl, Vector3.from_null(), room.rotation)

            mod.set(modelname, ResourceType.MDL, mdl)
            mod.set(modelname, ResourceType.MDX, room.component.mdx)

            bwm = deepcopy(room.component.bwm)
            bwm.rotate(room.rotation)
            bwm.translate(room.position.x, room.position.y, room.position.z)
            for hookIndex, connection in enumerate(room.hooks):
                dummyIndex = room.component.hooks[hookIndex].edge
                actualIndex = self.rooms.index(connection) if connection is not None else None
                for face in bwm.faces:
                    if face.trans1 == dummyIndex:
                        face.trans1 = actualIndex
                    if face.trans2 == dummyIndex:
                        face.trans2 = actualIndex
                    if face.trans3 == dummyIndex:
                        face.trans3 = actualIndex
            mod.set(modelname, ResourceType.WOK, bytes_bwm(bwm))

        are.tag = mod_id
        ifo.tag = mod_id
        ifo.area_name = ResRef(mod_id)

        mod.set(mod_id, ResourceType.LYT, bytes_lyt(lyt))
        mod.set(mod_id, ResourceType.VIS, bytes_vis(vis))
        mod.set(mod_id, ResourceType.ARE, bytes_are(are))
        mod.set(mod_id, ResourceType.GIT, bytes_git(git))
        mod.set("module", ResourceType.IFO, bytes_ifo(ifo))

        write_erf(mod, output_path)


class IndoorMapRoom:
    def __init__(self, component: KitComponent, position: Vector3, rotation: float):
        self.component: KitComponent = component
        self.position: Vector3 = position
        self.rotation: float = rotation
        self.hooks: List[Optional[IndoorMapRoom]] = [None] * len(component.hooks)

    def hookPosition(self, hook: KitComponentHook, worldOffset: bool = True):
        pos = copy(hook.position)

        cos = math.cos(math.radians(self.rotation))
        sin = math.sin(math.radians(self.rotation))
        pos.x = (hook.position.x * cos - hook.position.y * sin)
        pos.y = (hook.position.x * sin + hook.position.y * cos)

        if worldOffset:
            pos = pos + self.position

        return pos

    def rebuildConnections(self, rooms: List[IndoorMapRoom]) -> None:
        self.hooks: List[Optional[IndoorMapRoom]] = [None] * len(self.component.hooks)

        for hook in self.component.hooks:
            hookIndex = self.component.hooks.index(hook)
            hookPos = self.hookPosition(hook)
            for otherRoom in [room for room in rooms if room is not self]:
                for otherHook in otherRoom.component.hooks:
                    otherHookPos = otherRoom.hookPosition(otherHook)
                    if hookPos.distance(otherHookPos) < 1:
                        self.hooks[hookIndex] = otherRoom

    def walkmesh(self) -> BWM:
        bwm = deepcopy(self.component.bwm)
        bwm.rotate(self.rotation)
        bwm.translate(self.position.x, self.position.y, self.position.z)
        return bwm

