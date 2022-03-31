from __future__ import annotations

import json
import math
from copy import copy, deepcopy
from time import sleep
from typing import List, Optional, Tuple, NamedTuple

from PyQt5 import QtCore
from PyQt5.QtGui import QPixmap, QPainter, QTransform, QColor, QImage
from pykotor.common.geometry import Vector3, Vector2, Vector4
from pykotor.common.language import LocalizedString
from pykotor.common.misc import ResRef, Color
from pykotor.common.stream import BinaryReader
from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.formats.bwm import BWM
from pykotor.resource.formats.bwm.bwm_auto import bytes_bwm
from pykotor.resource.formats.erf import ERF, ERFType, write_erf
from pykotor.resource.formats.lyt import LYT, LYTRoom, LYTDoorHook
from pykotor.resource.formats.lyt.lyt_auto import bytes_lyt
from pykotor.resource.formats.tpc import TPC, TPCTextureFormat
from pykotor.resource.formats.tpc.tpc_auto import bytes_tpc
from pykotor.resource.formats.vis import VIS
from pykotor.resource.formats.vis.vis_auto import bytes_vis
from pykotor.resource.generics.are import ARE, bytes_are, ARENorthAxis
from pykotor.resource.generics.git import GIT, bytes_git, GITDoor
from pykotor.resource.generics.ifo import IFO, bytes_ifo
from pykotor.resource.generics.utd import UTD, bytes_utd
from pykotor.resource.type import ResourceType
from pykotor.tools import model

from data.installation import HTInstallation
from tools.indoormap.indoorkit import KitComponent, KitComponentHook, KitDoor, Kit


class DoorInsertion(NamedTuple):
    door: KitDoor
    room: IndoorMapRoom
    static: bool
    position: Vector3
    rotation: float


class MinimapData(NamedTuple):
    image: QImage
    imagePointMin: Vector2
    imagePointMax: Vector2
    worldPointMin: Vector2
    worldPointMax: Vector2


class IndoorMap:
    def __init__(self):
        self.rooms: List[IndoorMapRoom] = []
        self.module_id: str = "test01"
        self.name: LocalizedString = LocalizedString.from_english("New Module")
        self.lighting: Color = Color(0.5, 0.5, 0.5)

    def rebuildRoomConnections(self) -> None:
        for room in self.rooms:
            room.rebuildConnections(self.rooms)

    def doorInsertions(self) -> List[DoorInsertion]:
        points = []
        insertions = []

        for i, room in enumerate(self.rooms):
            for hookIndex, connection in enumerate(room.hooks):
                hook = room.component.hooks[hookIndex]
                door = hook.door
                position = room.hookPosition(hook)
                rotation = hook.rotation + room.rotation
                static = connection is None
                if position not in points:
                    points.append(position)  # 47
                    insertions.append(DoorInsertion(door, room, static, position, rotation))

        return insertions

    def build(self, installation: HTInstallation, outputPath: str) -> None:
        mod = ERF(ERFType.MOD)
        lyt = LYT()
        vis = VIS()
        are = ARE()
        ifo = IFO()
        git = GIT()

        roomNames = {}
        texRenames = {}
        totalLm = 0

        for i in range(len(self.rooms)):
            modelname = "{}_room{}".format(self.module_id, i)
            vis.add_room(modelname)

        for i, room in enumerate(self.rooms):
            modelname = "{}_room{}".format(self.module_id, i)
            roomNames[room] = modelname
            lyt.rooms.append(LYTRoom(modelname, room.position))

            for j in range(len(self.rooms)):
                if j != i:
                    vis.set_visible(modelname, "{}_room{}".format(self.module_id, j), True)

            for filename, data in room.component.kit.always.items():
                resname, restype = ResourceIdentifier.from_path(filename)
                mod.set(resname, restype, data)

            mdl = model.transform(room.component.mdl, Vector3.from_null(), room.rotation)
            mdl = model.convert_to_k2(mdl) if installation.tsl else model.convert_to_k1(mdl)

            for texture in set([texture for texture in model.list_textures(mdl) if texture.lower() not in texRenames.keys()]):
                renamed = "{}_tex{}".format(self.module_id, len(texRenames.keys()))
                texRenames[texture.lower()] = renamed
                mod.set(renamed, ResourceType.TGA, room.component.kit.textures[texture])
                mod.set(renamed, ResourceType.TXI, room.component.kit.txis[texture])
            mdl = model.change_textures(mdl, texRenames)

            lmRenames = {}
            for lightmap in model.list_lightmaps(mdl):
                renamed = "{}_lm{}".format(self.module_id, totalLm)
                totalLm += 1
                lmRenames[lightmap.lower()] = renamed
                mod.set(renamed, ResourceType.TGA, room.component.kit.lightmaps[lightmap])
                mod.set(renamed, ResourceType.TXI, room.component.kit.txis[lightmap])
            mdl = model.change_lightmaps(mdl, lmRenames)

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

        for i, insert in enumerate(self.doorInsertions()):
            door = GITDoor(*insert.position)
            door.resref = ResRef("{}_dor{:02}".format(self.module_id, i))
            door.bearing = math.radians(insert.rotation)
            git.doors.append(door)

            utd = deepcopy(insert.door.utdK2 if installation.tsl else insert.door.utdK1)
            utd.resref = door.resref
            utd.static = insert.static
            utd.tag = door.resref.get().title().replace("_", "")
            mod.set(door.resref.get(), ResourceType.UTD, bytes_utd(utd))

            orientation = Vector4.from_euler(0, 0, door.bearing)
            lyt.doorhooks.append(LYTDoorHook(roomNames[insert.room], door.resref.get(), insert.position, orientation))

        minimap = self.generateMinimap()
        tpcData = bytearray()
        for y in range(256):
            for x in range(512):
                pixel = QColor(minimap.image.pixel(x, y))
                tpcData.extend([pixel.red(), pixel.green(), pixel.blue(), 255])
        minimapTpc = TPC()
        minimapTpc.set(512, 256, [tpcData], TPCTextureFormat.RGBA)
        mod.set("lbl_map{}".format(self.module_id), ResourceType.TGA, bytes_tpc(minimapTpc, ResourceType.TGA))

        # Add loadscreen
        loadTga = BinaryReader.load_file("./kits/load_k2.tga") if installation.tsl else BinaryReader.load_file("./kits/load_k1.tga")
        mod.set("load_{}".format(self.module_id), ResourceType.TGA, loadTga)

        are.tag = self.module_id
        are.dynamic_light = self.lighting
        are.name = self.name
        are.map_point_1 = minimap.imagePointMin
        are.map_point_2 = minimap.imagePointMax
        are.world_point_1 = minimap.worldPointMin
        are.world_point_2 = minimap.worldPointMax
        are.map_zoom = 1
        are.map_res_x = 1
        are.north_axis = ARENorthAxis.NegativeY
        ifo.tag = self.module_id
        ifo.area_name = ResRef(self.module_id)
        ifo.identifier = ResRef(self.module_id)

        mod.set(self.module_id, ResourceType.LYT, bytes_lyt(lyt))
        mod.set(self.module_id, ResourceType.VIS, bytes_vis(vis))
        mod.set(self.module_id, ResourceType.ARE, bytes_are(are))
        mod.set(self.module_id, ResourceType.GIT, bytes_git(git))
        mod.set("module", ResourceType.IFO, bytes_ifo(ifo))

        write_erf(mod, outputPath)

    def write(self) -> bytes:
        data = {}

        data["moduleId"] = self.module_id

        data["name"] = {}
        data["name"]["stringref"] = self.name.stringref
        for language, gender, text in self.name:
            stringid = LocalizedString.substring_id(language, gender)
            data["name"][stringid] = text

        data["lighting"] = [self.lighting.r, self.lighting.g, self.lighting.b]

        data["warp"] = self.module_id

        data["rooms"] = []
        for room in self.rooms:
            roomData = {}
            roomData["position"] = [*room.position]
            roomData["rotation"] = room.rotation
            roomData["kit"] = room.component.kit.name
            roomData["component"] = room.component.name
            data["rooms"].append(roomData)

        return json.dumps(data).encode()

    def load(self, raw: bytes, kits: List[Kit]) -> None:
        self.reset()
        data = json.loads(raw)

        try:
            self.name = LocalizedString(data["name"]["stringref"])
            for stringid in [key for key in data["name"] if key.isnumeric()]:
                language, gender = LocalizedString.substring_pair(int(stringid))
                self.name.set(language, gender, data["name"][stringid])

            self.lighting.b = data["lighting"][0]
            self.lighting.g = data["lighting"][1]
            self.lighting.r = data["lighting"][2]

            self.module_id = data["warp"]

            for roomData in data["rooms"]:
                sKit = None
                for kit in kits:
                    if kit.name == roomData["kit"]:
                        sKit = kit
                        break
                if sKit is None:
                    raise ValueError("Required kit is missing '{}'.".format(roomData["kit"]))

                sComponent = None
                for component in sKit.components:
                    if component.name == roomData["component"]:
                        sComponent = component
                        break
                if sComponent is None:
                    raise ValueError("Required component '{}' is missing in kit '{}'.".format(roomData["component"], sKit.name))

                position = Vector3(roomData["position"][0], roomData["position"][1], roomData["position"][2])
                rotation = roomData["rotation"]
                room = IndoorMapRoom(sComponent, position, rotation)
                self.rooms.append(room)
        except KeyError:
            raise ValueError("Map file is corrupted.")

    def reset(self) -> None:
        self.rooms.clear()
        self.module_id = "test01"
        self.name = LocalizedString.from_english("New Module")
        self.lighting = Color(0.5, 0.5, 0.5)

    def generateMinimap(self) -> MinimapData:
        """
        Returns the all neccessary minimap data required for a module including the image and the ARE field values.

        Returns:
            The minimap data.
        """
        # Get the bounding box that encompasses all the walkmeshes, we will use this to determine the size of the
        # unscaled pixmap for our minimap
        walkmeshes = []
        for i, room in enumerate(self.rooms):
            bwm = deepcopy(room.component.bwm)
            bwm.rotate(room.rotation)
            bwm.translate(room.position.x, room.position.y, room.position.z)
            walkmeshes.append(bwm)

        bbmin = Vector3(1000000, 1000000, 1000000)
        bbmax = Vector3(-1000000, -1000000, -1000000)
        for bwm in walkmeshes:
            for vertex in bwm.vertices():
                bbmin.x = min(bbmin.x, vertex.x)
                bbmin.y = min(bbmin.y, vertex.y)
                bbmin.z = min(bbmin.z, vertex.z)
                bbmax.x = max(bbmax.x, vertex.x)
                bbmax.y = max(bbmax.y, vertex.y)
                bbmax.z = max(bbmax.z, vertex.z)
        bbmin.x -= 5
        bbmin.y -= 5
        bbmax.x += 5
        bbmax.y += 5

        width = int(bbmax.x)*10 - int(bbmin.x)*10
        height = int(bbmax.y)*10 - int(bbmin.y)*10
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(0))

        # Draw the actual minimap
        painter = QPainter(pixmap)
        for room in self.rooms:
            image = room.component.image

            painter.save()
            painter.translate(room.position.x*10 - int(bbmin.x)*10, room.position.y*10 - int(bbmin.y)*10)
            painter.rotate(room.rotation)
            painter.translate(-image.width()/2, -image.height()/2)

            painter.drawImage(0, 0, image)
            painter.restore()
        painter.end()
        del painter

        # Minimaps are 512x256 so we need to appropriately scale down our image
        pixmap = pixmap.scaled(435, 256, QtCore.Qt.KeepAspectRatio)

        pixmap2 = QPixmap(512, 256)
        pixmap2.fill(QColor(0))
        painter2 = QPainter(pixmap2)
        painter2.drawPixmap(0, 128-pixmap.height()/2, pixmap)

        image = pixmap2.transformed(QTransform().scale(1, -1)).toImage()
        image.convertTo(QImage.Format_RGB888)
        imagePointMin = Vector2(0/435, (128-pixmap.height()/2)/256)  # +512-435
        imagePointMax = Vector2((imagePointMin.x+pixmap.width())/435, (imagePointMin.y+pixmap.height())/256)
        worldPointMin = Vector2(bbmax.x, bbmin.y)
        worldPointMax = Vector2(bbmin.x, bbmax.y)

        painter2.end()

        del painter2
        del pixmap
        del pixmap2

        return MinimapData(image, imagePointMin, imagePointMax, worldPointMin, worldPointMax)


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
                    if hookPos.distance(otherHookPos) < 0.001:
                        self.hooks[hookIndex] = otherRoom

    def walkmesh(self) -> BWM:
        bwm = deepcopy(self.component.bwm)
        bwm.rotate(self.rotation)
        bwm.translate(self.position.x, self.position.y, self.position.z)
        return bwm

