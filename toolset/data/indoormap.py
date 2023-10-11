from __future__ import annotations

import itertools
import json
import math
from copy import copy, deepcopy
from typing import TYPE_CHECKING, NamedTuple, Optional

from PyQt5 import QtCore
from PyQt5.QtGui import QColor, QImage, QPainter, QPixmap, QTransform

from pykotor.common.geometry import Vector2, Vector3, Vector4
from pykotor.common.language import LocalizedString
from pykotor.common.misc import Color, ResRef
from pykotor.common.stream import BinaryReader
from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.formats.erf import ERF, ERFType, write_erf
from pykotor.resource.formats.lyt import LYT, LYTDoorHook, LYTRoom
from pykotor.resource.formats.lyt.lyt_auto import bytes_lyt
from pykotor.resource.formats.tpc import TPC, TPCTextureFormat
from pykotor.resource.formats.tpc.tpc_auto import bytes_tpc
from pykotor.resource.formats.vis import VIS
from pykotor.resource.formats.vis.vis_auto import bytes_vis
from pykotor.resource.generics.are import ARE, ARENorthAxis, bytes_are
from pykotor.resource.generics.git import GIT, GITDoor, bytes_git
from pykotor.resource.generics.ifo import IFO, bytes_ifo
from pykotor.resource.generics.utd import bytes_utd
from pykotor.resource.type import ResourceType
from pykotor.tools import model

if TYPE_CHECKING:
    import os

    from pykotor.resource.formats.bwm import BWM
    from toolset.data.indoorkit import Kit, KitComponent, KitComponentHook, KitDoor
    from toolset.data.installation import HTInstallation


class DoorInsertion(NamedTuple):
    door: KitDoor
    room: IndoorMapRoom
    room2: IndoorMapRoom
    static: bool
    position: Vector3
    rotation: float
    hook1: KitComponentHook
    hook2: Optional[KitComponentHook]


class MinimapData(NamedTuple):
    image: QImage
    imagePointMin: Vector2
    imagePointMax: Vector2
    worldPointMin: Vector2
    worldPointMax: Vector2


class IndoorMap:
    def __init__(self):
        self.rooms: list[IndoorMapRoom] = []
        self.moduleId: str = "test01"
        self.name: LocalizedString = LocalizedString.from_english("New Module")
        self.lighting: Color = Color(0.5, 0.5, 0.5)
        self.skybox: str = ""
        self.warpPoint: Vector3 = Vector3.from_null()

    def rebuildRoomConnections(self) -> None:
        for room in self.rooms:
            room.rebuildConnections(self.rooms)

    def doorInsertions(self) -> list[DoorInsertion]:
        """Returns a list of connections between rooms. Used when determining when to place doors when building a map."""
        points = []  # Used to determine if door already exists at this point
        insertions = []

        for room in self.rooms:
            for hookIndex, connection in enumerate(room.hooks):
                room1 = room
                room2 = None
                hook1 = room1.component.hooks[hookIndex]
                hook2 = None
                door = hook1.door
                position = room1.hookPosition(hook1)
                rotation = hook1.rotation + room1.rotation
                if connection is not None:
                    for otherHookIndex, otherRoom in enumerate(connection.hooks):
                        if otherRoom == room1:
                            otherHook = connection.component.hooks[otherHookIndex]
                            if hook1.door.width < otherHook.door.width:
                                door = otherHook.door
                                hook2 = hook1
                                hook1 = otherHook
                                room2 = room1
                                room1 = connection
                            else:
                                hook2 = connection.component.hooks[otherHookIndex]
                                room2 = connection
                                rotation = hook2.rotation + room2.rotation

                if position not in points:
                    points.append(position)  # 47
                    if room2 is None:
                        msg = "room2 cannot be None"
                        raise ValueError(msg)

                    static = connection is None
                    insertions.append(DoorInsertion(door, room1, room2, static, position, rotation, hook1, hook2))

        return insertions

    def add_rooms(self):
        for i in range(len(self.rooms)):
            modelname = f"{self.moduleId}_room{i}"
            self.vis.add_room(modelname)

    def process_room_components(self):
        for room in self.rooms:
            self.usedRooms.add(room.component)
        for room in self.usedRooms:
            self.scanMdls.add(room.mdl)
            self.usedKits.add(room.kit)
            for doorPaddingDict in list(room.kit.top_padding.values()) + list(room.kit.side_padding.values()):
                for paddingModel in doorPaddingDict.values():
                    self.scanMdls.add(paddingModel.mdl)

    def handle_textures(self):
        for mdl in self.scanMdls:
            for texture in [texture for texture in model.list_textures(mdl) if texture not in self.texRenames]:
                renamed = f"{self.moduleId}_tex{len(self.texRenames.keys())}"
                self.texRenames[texture] = renamed
                for kit in self.usedKits:
                    if texture in kit.textures:
                        self.mod.set_data(renamed, ResourceType.TGA, kit.textures[texture])
                        self.mod.set_data(renamed, ResourceType.TXI, kit.txis[texture])

    def handle_lightmaps(self, installation):
        for i, room in enumerate(self.rooms):
            modelname = f"{self.moduleId}_room{i}"
            self.roomNames[room] = modelname
            self.lyt.rooms.append(LYTRoom(modelname, room.position))

            for filename, data in room.component.kit.always.items():
                resname, restype = ResourceIdentifier.from_path(filename)
                self.mod.set_data(resname, restype, data)

            mdl, mdx = model.flip(room.component.mdl, room.component.mdx, room.flip_x, room.flip_y)
            mdl = model.transform(mdl, Vector3.from_null(), room.rotation)
            mdl = model.convert_to_k2(mdl) if installation.tsl else model.convert_to_k1(mdl)
            mdl = model.change_textures(mdl, self.texRenames)

            lmRenames = {}
            for lightmap in model.list_lightmaps(mdl):
                renamed = f"{self.moduleId}_lm{self.totalLm}"
                self.totalLm += 1
                lmRenames[lightmap.lower()] = renamed
                self.mod.set_data(renamed, ResourceType.TGA, room.component.kit.lightmaps[lightmap])
                self.mod.set_data(renamed, ResourceType.TXI, room.component.kit.txis[lightmap])
            mdl = model.change_lightmaps(mdl, lmRenames)

            self.mod.set_data(modelname, ResourceType.MDL, mdl)
            self.mod.set_data(modelname, ResourceType.MDX, mdx)

    def handle_door_insertions(self, installation):
        for i, insert in enumerate(self.doorInsertions()):
            door = GITDoor(*insert.position)
            door.resref = ResRef(f"{self.moduleId}_dor{i:02}")
            door.bearing = math.radians(insert.rotation)
            door.tweak_color = None
            self.git.doors.append(door)

            utd = deepcopy(insert.door.utdK2 if installation.tsl else insert.door.utdK1)
            utd.resref = door.resref
            utd.static = insert.static
            utd.tag = door.resref.get().title().replace("_", "")
            self.mod.set_data(door.resref.get(), ResourceType.UTD, bytes_utd(utd))

            orientation = Vector4.from_euler(0, 0, math.radians(door.bearing))
            self.lyt.doorhooks.append(LYTDoorHook(self.roomNames[insert.room], door.resref.get(), insert.position, orientation))

            # ... Other door insertion logic ...

    def process_skybox(self, kits):
        if self.skybox != "":
            for kit in kits:
                if self.skybox in kit.skyboxes:
                    mdl, mdx = kit.skyboxes[self.skybox]
                    modelName = f"{self.moduleId}_sky"
                    mdl = model.change_textures(mdl, self.texRenames)
                    self.mod.set_data(modelName, ResourceType.MDL, mdl)
                    self.mod.set_data(modelName, ResourceType.MDX, mdx)
                    self.lyt.rooms.append(LYTRoom(modelName, Vector3.from_null()))
                    self.vis.add_room(modelName)

    def generate_and_set_minimap(self):
        minimap = self.generateMinimap()
        tpcData = bytearray()
        for y, x in itertools.product(range(256), range(512)):
            pixel = QColor(minimap.image.pixel(x, y))
            tpcData.extend([pixel.red(), pixel.green(), pixel.blue(), 255])
        minimapTpc = TPC()
        minimapTpc.set_data(512, 256, [tpcData], TPCTextureFormat.RGBA)
        self.mod.set_data(f"lbl_map{self.moduleId}", ResourceType.TGA, bytes_tpc(minimapTpc, ResourceType.TGA))

    def handle_loadscreen(self, installation):
        loadTga = (
            BinaryReader.load_file("./kits/load_k2.tga") if installation.tsl else BinaryReader.load_file("./kits/load_k1.tga")
        )
        self.mod.set_data(f"load_{self.moduleId}", ResourceType.TGA, loadTga)

    def set_area_attributes(self, minimap):
        self.are.tag = self.moduleId
        self.are.dynamic_light = self.lighting
        self.are.name = self.name
        self.are.map_point_1 = minimap.imagePointMin
        self.are.map_point_2 = minimap.imagePointMax
        self.are.world_point_1 = minimap.worldPointMin
        self.are.world_point_2 = minimap.worldPointMax
        self.are.map_zoom = 1
        self.are.map_res_x = 1
        self.are.north_axis = ARENorthAxis.NegativeY

    def set_ifo_attributes(self):
        self.ifo.tag = self.moduleId
        self.ifo.area_name = ResRef(self.moduleId)
        self.ifo.identifier = ResRef(self.moduleId)
        self.vis.set_all_visible()
        self.ifo.entry_position = self.warpPoint

    def finalize_module_data(self, output_path):
        self.mod.set_data(self.moduleId, ResourceType.LYT, bytes_lyt(self.lyt))
        self.mod.set_data(self.moduleId, ResourceType.VIS, bytes_vis(self.vis))
        self.mod.set_data(self.moduleId, ResourceType.ARE, bytes_are(self.are))
        self.mod.set_data(self.moduleId, ResourceType.GIT, bytes_git(self.git))
        self.mod.set_data("module", ResourceType.IFO, bytes_ifo(self.ifo))

        write_erf(self.mod, output_path)

    def build(self, installation: HTInstallation, kits: list[Kit], output_path: os.PathLike) -> None:
        self.mod = ERF(ERFType.MOD)
        self.lyt = LYT()
        self.vis = VIS()
        self.are = ARE()
        self.ifo = IFO()
        self.git = GIT()
        self.roomNames = {}
        self.texRenames = {}
        self.totalLm = 0
        self.usedRooms = set()
        self.usedKits = set()
        self.scanMdls = set()

        self.add_rooms()
        self.process_room_components()
        self.handle_textures()
        self.handle_lightmaps(installation)
        self.process_skybox(kits)
        self.generate_and_set_minimap()

        self.handle_loadscreen(installation)
        self.handle_door_insertions(installation)
        self.set_area_attributes(self.generateMinimap())
        self.set_ifo_attributes()
        self.finalize_module_data(output_path)

    def write(self) -> bytes:
        data = {"moduleId": self.moduleId, "name": {}}

        data["name"]["stringref"] = self.name.stringref
        for language, gender, text in self.name:
            stringid = LocalizedString.substring_id(language, gender)
            data["name"][stringid] = text

        data["lighting"] = [self.lighting.r, self.lighting.g, self.lighting.b]
        data["skybox"] = self.skybox
        data["warp"] = self.moduleId

        data["rooms"] = []
        for room in self.rooms:
            roomData = {
                "position": [*room.position],
                "rotation": room.rotation,
                "flip_x": room.flip_x,
                "flip_y": room.flip_y,
                "kit": room.component.kit.name,
                "component": room.component.name,
            }
            data["rooms"].append(roomData)

        return json.dumps(data).encode()

    def load(self, raw: bytes, kits: list[Kit]) -> None:
        self.reset()
        data = json.loads(raw)

        try:
            self._load_data(data, kits)
        except KeyError as e:
            msg = "Map file is corrupted."
            raise ValueError(msg) from e

    def _load_data(self, data, kits):
        self.name = LocalizedString(data["name"]["stringref"])
        for stringid in [key for key in data["name"] if key.isnumeric()]:
            language, gender = LocalizedString.substring_pair(int(stringid))
            self.name.set_data(language, gender, data["name"][stringid])

        self.lighting.b = data["lighting"][0]
        self.lighting.g = data["lighting"][1]
        self.lighting.r = data["lighting"][2]

        self.moduleId = data["warp"]
        self.skybox = data["skybox"] if "skybox" in data else ""

        for roomData in data["rooms"]:
            sKit = next((kit for kit in kits if kit.name == roomData["kit"]), None)
            if sKit is None:
                msg = f"""Required kit is missing '{roomData["kit"]}'."""
                raise ValueError(msg)

            sComponent = next(
                (component for component in sKit.components if component.name == roomData["component"]),
                None,
            )
            if sComponent is None:
                msg = f"""Required component '{roomData["component"]}' is missing in kit '{sKit.name}'."""
                raise ValueError(msg)

            position = Vector3(roomData["position"][0], roomData["position"][1], roomData["position"][2])
            rotation = roomData["rotation"]
            flip_x = bool(roomData["flip_x"] if "flip_x" in roomData else False)
            flip_y = bool(roomData["flip_y"] if "flip_y" in roomData else False)
            room = IndoorMapRoom(sComponent, position, rotation, flip_x, flip_y)
            self.rooms.append(room)

    def reset(self) -> None:
        self.rooms.clear()
        self.moduleId = "test01"
        self.name = LocalizedString.from_english("New Module")
        self.lighting = Color(0.5, 0.5, 0.5)

    def generateMinimap(self) -> MinimapData:
        """Returns the all neccessary minimap data required for a module including the image and the ARE field values.

        Returns
        -------
            The minimap data.
        """
        # Get the bounding box that encompasses all the walkmeshes, we will use this to determine the size of the
        # unscaled pixmap for our minimap
        walkmeshes = []
        for room in self.rooms:
            bwm = deepcopy(room.component.bwm)
            bwm.rotate(room.rotation)
            bwm.translate(room.position.x, room.position.y, room.position.z)
            walkmeshes.append(bwm)

        bbmin = Vector3(1000000, 1000000, 1000000)
        bbmax = Vector3(-1000000, -1000000, -1000000)
        for bwm in walkmeshes:
            for vertex in bwm.vertices():
                self._normalize_bwm_vertices(bbmin, vertex, bbmax)
        bbmin.x -= 5
        bbmin.y -= 5
        bbmax.x += 5
        bbmax.y += 5

        width = bbmax.x * 10 - bbmin.x * 10
        height = bbmax.y * 10 - bbmin.y * 10
        pixmap = QPixmap(int(width), int(height))
        pixmap.fill(QColor(0))

        # Draw the actual minimap
        painter = QPainter(pixmap)
        for room in self.rooms:
            image = room.component.image

            painter.save()
            painter.translate(
                room.position.x * 10 - bbmin.x * 10,
                room.position.y * 10 - bbmin.y * 10,
            )
            painter.rotate(room.rotation)
            painter.scale(-1 if room.flip_x else 1, -1 if room.flip_y else 1)
            painter.translate(-image.width() / 2, -image.height() / 2)

            painter.drawImage(0, 0, image)
            painter.restore()
        painter.end()
        del painter

        # Minimaps are 512x256 so we need to appropriately scale down our image
        pixmap = pixmap.scaled(435, 256, QtCore.Qt.KeepAspectRatio)

        pixmap2 = QPixmap(512, 256)
        pixmap2.fill(QColor(0))
        painter2 = QPainter(pixmap2)
        painter2.drawPixmap(0, int(128 - pixmap.height() / 2), pixmap)

        image = pixmap2.transformed(QTransform().scale(1, -1)).toImage()
        image.convertTo(QImage.Format_RGB888)
        imagePointMin = Vector2(0 / 435, (128 - pixmap.height() / 2) / 256)  # +512-435
        imagePointMax = Vector2((imagePointMin.x + pixmap.width()) / 435, (imagePointMin.y + pixmap.height()) / 256)
        worldPointMin = Vector2(bbmax.x, bbmin.y)
        worldPointMax = Vector2(bbmin.x, bbmax.y)

        painter2.end()

        del painter2
        del pixmap
        del pixmap2

        return MinimapData(image, imagePointMin, imagePointMax, worldPointMin, worldPointMax)

    def _normalize_bwm_vertices(self, bbmin, vertex, bbmax):
        bbmin.x = min(bbmin.x, vertex.x)
        bbmin.y = min(bbmin.y, vertex.y)
        bbmin.z = min(bbmin.z, vertex.z)
        bbmax.x = max(bbmax.x, vertex.x)
        bbmax.y = max(bbmax.y, vertex.y)
        bbmax.z = max(bbmax.z, vertex.z)


class IndoorMapRoom:
    def __init__(self, component: KitComponent, position: Vector3, rotation: float, flip_x: bool, flip_y: bool):
        self.component: KitComponent = component
        self.position: Vector3 = position
        self.rotation: float = rotation
        self.hooks: list[Optional[IndoorMapRoom]] = [None] * len(component.hooks)
        self.flip_x: bool = flip_x
        self.flip_y: bool = flip_y

    def hookPosition(self, hook: KitComponentHook, worldOffset: bool = True):
        pos = copy(hook.position)

        pos.x = -pos.x if self.flip_x else pos.x
        pos.y = -pos.y if self.flip_y else pos.y
        temp = copy(pos)

        cos = math.cos(math.radians(self.rotation))
        sin = math.sin(math.radians(self.rotation))
        pos.x = temp.x * cos - temp.y * sin
        pos.y = temp.x * sin + temp.y * cos

        if worldOffset:
            pos = pos + self.position

        return pos

    def rebuildConnections(self, rooms: list[IndoorMapRoom]) -> None:
        self.hooks: list[Optional[IndoorMapRoom]] = [None] * len(self.component.hooks)

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
