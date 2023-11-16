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
from pykotor.resource.formats.bwm.bwm_auto import bytes_bwm
from pykotor.resource.formats.erf import ERF, ERFType
from pykotor.resource.formats.erf.erf_auto import write_erf
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
    def __init__(self) -> None:
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
        """Returns a list of connections between rooms. Used when determining when to place doors when building a map.
        Generates door insertions between rooms
        Args:
            self: The FloorPlan object
        Returns:
            list[DoorInsertion]: List of door insertion objects
        1. Loops through each room and connection
        2. Determines door, rooms, hooks and positions
        3. Checks if door already exists at point
        4. Adds valid door insertion to return list.
        """
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
                    #if room2 is None:
                    #    msg = "room2 cannot be None"
                    #    raise ValueError(msg)

                    static = connection is None
                    insertions.append(DoorInsertion(door, room1, room2, static, position, rotation, hook1, hook2))

        return insertions

    def add_rooms(self):
        for i in range(len(self.rooms)):
            modelname = f"{self.moduleId}_room{i}"
            self.vis.add_room(modelname)

    def process_room_components(self):
        """Process room components by adding them to tracking sets
        Args:
            self: The class instance
        Returns:
            None: No value is returned
        - Iterate through rooms and add component to usedRooms set
        - Iterate through usedRooms and add mdl to scanMdls and kit to usedKits
        - Iterate through door padding dicts and values, adding padding mdl to scanMdls.
        """
        for room in self.rooms:
            self.usedRooms.add(room.component)
        for room in self.usedRooms:
            self.scanMdls.add(room.mdl)
            self.usedKits.add(room.kit)
            for doorPaddingDict in list(room.kit.top_padding.values()) + list(room.kit.side_padding.values()):
                for paddingModel in doorPaddingDict.values():
                    self.scanMdls.add(paddingModel.mdl)

    def handle_textures(self):
        """Rename textures to avoid conflicts.

        Returns
        -------
            None: {Does not return anything}
        Processing Logic:
            - Scan through all models
            - Get textures from each model
            - Check if texture is already renamed
            - If not, rename it and add to renaming dictionary
            - Check texture usage in all kits
            - Replace texture references in kit textures and txis with new renamed texture.
        """
        for mdl in self.scanMdls:
            for texture in [texture for texture in model.list_textures(mdl) if texture not in self.texRenames]:
                renamed = f"{self.moduleId}_tex{len(self.texRenames.keys())}"
                self.texRenames[texture] = renamed
                for kit in self.usedKits:
                    if texture in kit.textures:
                        self.mod.set_data(renamed, ResourceType.TGA, kit.textures[texture])
                        self.mod.set_data(renamed, ResourceType.TXI, kit.txis[texture])

    def handle_lightmaps(self, installation):
        """Processes lightmaps for a room model.

        Args:
        ----
            room: {The room object being processed}
            mdl: {The 3D room model object}.

        Returns:
        -------
            None
        Processing Logic:
            - Loops through each face in the room model
            - Generates a lightmap texture for each face
            - Bakes ambient occlusion and lighting information into the lightmap texture
            - Attaches the generated lightmap texture to the corresponding face.
        """
        for i, room in enumerate(self.rooms):

            # Set model name
            modelname = f"{self.moduleId}_room{i}"
            self.roomNames[room] = modelname

            # Add room to layout
            self.lyt.rooms.append(LYTRoom(modelname, room.position))

            # Add static resources
            self.add_static_resources(room)

            # Process model
            mdl, mdx = self.process_model(room, installation)

            # Process lightmaps
            self.process_lightmaps(room, mdl)

            # Add model resources
            self.add_model_resources(modelname, mdl, mdx)

            # Process BWM
            bwm = self.process_bwm(room)
            self.add_bwm_resource(modelname, bwm)

    def add_static_resources(self, room):
        """Adds static resources from a room's kit to the mod.

        Args:
        ----
            room: The room object containing static resources.

        Returns:
        -------
            None: No value is returned.
        Processes static resources:
            - Loops through each static resource filename and data in the room's kit
            - Extracts the resource name and type from the filename
            - Adds the resource data to the mod with the extracted name and type.
        """
        for filename, data in room.component.kit.always.items():
            resname, restype = ResourceIdentifier.from_path(filename)
            self.mod.set_data(resname, restype, data)

    def process_model(self, room: IndoorMapRoom, installation):
        """Processes a model based on room properties
        Args:
            room: IndoorMapRoom: The room object containing model properties
            installation: Installation: The installation object containing target system properties
        Returns:
            mdl: str: The processed model string
            mdx: str: The processed material index string
        Processing Logic:
            - Flip the model based on room flip_x and flip_y properties
            - Rotate the model based on room rotation property
            - Convert the model to target system format based on installation tsl property
            - Return processed model and material index strings.
        """
        mdl, mdx = model.flip(room.component.mdl, room.component.mdx, room.flip_x, room.flip_y)
        mdl = model.transform(mdl, Vector3.from_null(), room.rotation)
        mdl = model.convert_to_k2(mdl) if installation.tsl else model.convert_to_k1(mdl)
        return mdl, mdx

    def process_lightmaps(self, room: IndoorMapRoom, mdl):
        """Processes lightmaps for a room
        Args:
            room (IndoorMapRoom): The room to process lightmaps for
            mdl: The model to process lightmaps on
        Returns:
            mdl: The model with renamed lightmaps
        Processing Logic:
            - Renames each lightmap to a unique name prefixed with the module ID
            - Sets the renamed lightmap and txi textures in the mod
            - Returns the model with all lightmaps renamed according to the mapping.
        """
        lm_renames = {}
        for lightmap in model.list_lightmaps(mdl):
            renamed = f"{self.moduleId}_lm{self.totalLm}"
            self.totalLm += 1
            lm_renames[lightmap.lower()] = renamed
            self.mod.set_data(renamed, ResourceType.TGA, room.component.kit.lightmaps[lightmap])
            self.mod.set_data(renamed, ResourceType.TXI, room.component.kit.txis[lightmap])
        mdl = model.change_lightmaps(mdl, lm_renames)

    def add_model_resources(self, modelname, mdl, mdx):
        """Adds model resources to the mod object
        Args:
            modelname: Name of the model
            mdl: MDL file data
            mdx: MDX file data
        Returns:
            None: Does not return anything
        - Sets the MDL file data for the given modelname using ResourceType.MDL
        - Sets the MDX file data for the given modelname using ResourceType.MDX
        - Does not return anything, just adds the resources to the mod object.
        """
        self.mod.set_data(modelname, ResourceType.MDL, mdl)
        self.mod.set_data(modelname, ResourceType.MDX, mdx)

    def process_bwm(self, room: IndoorMapRoom) -> BWM:
        """Processes the BWM for a room.

        Args:
        ----
            room: {IndoorMapRoom}: Room object containing BWM and transform info
        Returns:
            bwm: {OccupancyGridMap}: Processed BWM for the room
        Processing Logic:
            - Make a deep copy of the room BWM
            - Apply flip, rotation and translation transforms to the copy
            - Remap transition indices to reference connected rooms
            - Return the processed BWM.
        """
        bwm = deepcopy(room.component.bwm)
        bwm.flip(room.flip_x, room.flip_y)
        bwm.rotate(room.rotation)
        bwm.translate(room.position.x, room.position.y, room.position.z)
        for hookIndex, connection in enumerate(room.hooks):
            dummyIndex = room.component.hooks[hookIndex].edge
            actualIndex = self.rooms.index(connection) if connection is not None else None
            self.remap_transitions(bwm, dummyIndex, actualIndex)
        return bwm

    def remap_transitions(self, bwm: BWM, dummyIndex, actualIndex):
        """Remaps dummy transition index to actual transition index in BWM faces.

        Args:
        ----
            bwm: BWM object containing faces
            dummyIndex: Dummy transition index to remap
            actualIndex: Actual transition index to remap to
        Returns:
            None: Function does not return anything
        - Loops through each face in the BWM object
        - Checks if the face's trans1, trans2 or trans3 attribute equals the dummy index
        - If so, replaces it with the actual index.
        """
        for face in bwm.faces:
            if face.trans1 == dummyIndex:
                face.trans1 = actualIndex
            if face.trans2 == dummyIndex:
                face.trans2 = actualIndex
            if face.trans3 == dummyIndex:
                face.trans3 = actualIndex

    def add_bwm_resource(self, modelname, bwm):
        self.mod.set_data(modelname, ResourceType.WOK, bytes_bwm(bwm))

    def _handle_door_insertions(self, installation):
        """Handle door insertions
        Args:
            self: The class instance
            installation: The installation details
        Returns:
            None: No value is returned
        Processing Logic:
        1. Loops through each door insertion
        2. Creates a door object and sets properties
        3. Copies UTD data and sets properties
        4. Adds door to layout and visibility graphs
        5. Checks for height/width padding needs and adds if needed.
        """
        paddingCount = 0
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

            if insert.hook1 and insert.hook2:
                if insert.hook1.door.height != insert.hook2.door.height:
                    cRoom = insert.room if insert.hook1.door.height < insert.hook2.door.height else insert.room2
                    cHook = insert.hook1 if insert.hook1.door.height < insert.hook2.door.height else insert.hook2
                    altHook = insert.hook2 if insert.hook1.door.height < insert.hook2.door.height else insert.hook1

                    kit = cRoom.component.kit
                    doorIndex = kit.doors.index(cHook.door)
                    height = altHook.door.height * 100
                    paddingKey = (
                        min((i for i in kit.top_padding[doorIndex] if i > height), default=None)
                        if doorIndex in kit.top_padding
                        else None
                    )
                    if paddingKey is not None:
                        paddingName = f"{self.moduleId}_tpad{paddingCount}"
                        paddingCount += 1
                        pad_mdl = model.transform(
                            kit.top_padding[doorIndex][paddingKey].mdl,
                            Vector3.from_null(),
                            insert.rotation,
                        )
                        pad_mdl = model.convert_to_k2(pad_mdl) if installation.tsl else model.convert_to_k1(pad_mdl)
                        pad_mdl = model.change_textures(pad_mdl, self.texRenames)
                        lmRenames = {}
                        for lightmap in model.list_lightmaps(pad_mdl):
                            renamed = f"{self.moduleId}_lm{self.totalLm}"
                            self.totalLm += 1
                            lmRenames[lightmap.lower()] = renamed
                            self.mod.set_data(renamed, ResourceType.TGA, kit.lightmaps[lightmap])
                            self.mod.set_data(renamed, ResourceType.TXI, kit.txis[lightmap])
                        pad_mdl = model.change_lightmaps(pad_mdl, lmRenames)
                        self.mod.set_data(paddingName, ResourceType.MDL, pad_mdl)
                        self.mod.set_data(paddingName, ResourceType.MDX, kit.top_padding[doorIndex][paddingKey].mdx)
                        self.lyt.rooms.append(LYTRoom(paddingName, insert.position))
                        self.vis.add_room(paddingName)
                if insert.hook1.door.width != insert.hook2.door.width:
                    cRoom = insert.room if insert.hook1.door.height < insert.hook2.door.height else insert.room2
                    cHook = insert.hook1 if insert.hook1.door.height < insert.hook2.door.height else insert.hook2
                    altHook = insert.hook2 if insert.hook1.door.height < insert.hook2.door.height else insert.hook1

                    kit = cRoom.component.kit
                    doorIndex = kit.doors.index(cHook.door)
                    width = altHook.door.width * 100
                    paddingKey = (
                        min((i for i in kit.side_padding[doorIndex] if i > width), default=None)
                        if doorIndex in kit.side_padding
                        else None
                    )
                    if paddingKey is not None:
                        paddingName = f"{self.moduleId}_tpad{paddingCount}"
                        paddingCount += 1
                        pad_mdl = model.transform(
                            kit.side_padding[doorIndex][paddingKey].mdl,
                            Vector3.from_null(),
                            insert.rotation,
                        )
                        pad_mdl = model.convert_to_k2(pad_mdl) if installation.tsl else model.convert_to_k1(pad_mdl)
                        pad_mdl = model.change_textures(pad_mdl, self.texRenames)
                        lmRenames = {}
                        for lightmap in model.list_lightmaps(pad_mdl):
                            renamed = f"{self.moduleId}_lm{self.totalLm}"
                            self.totalLm += 1
                            lmRenames[lightmap.lower()] = renamed
                            self.mod.set_data(renamed, ResourceType.TGA, kit.lightmaps[lightmap])
                            self.mod.set_data(renamed, ResourceType.TXI, kit.txis[lightmap])
                        pad_mdl = model.change_lightmaps(pad_mdl, lmRenames)
                        self.mod.set_data(paddingName, ResourceType.MDL, pad_mdl)
                        self.mod.set_data(paddingName, ResourceType.MDX, kit.side_padding[doorIndex][paddingKey].mdx)
                        self.lyt.rooms.append(LYTRoom(paddingName, insert.position))
                        self.vis.add_room(paddingName)

    def process_skybox(self, kits):
        """Process the skybox for the module
        Args:
            kits: List of kit objects containing skybox models
        Returns:
            None: No value is returned
        Processing Logic:
            - Check if a skybox is specified for the module
            - Loop through kits to find matching skybox
            - Extract model and texture from matching kit
            - Set model and texture in module data
            - Add room to layout with model
            - Add room to visibility graph.
        """
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
        """Generates and sets the minimap texture
        Args:
            self: The module object
        Returns:
            None: No value is returned
        - Generates a 256x512 minimap image from the module view
        - Converts the image to a bytearray with RGBA pixel values
        - Creates a TPC texture from the bytearray
        - Sets the TPC texture as the module's minimap label texture.
        """
        minimap = self.generateMinimap()
        tpcData = bytearray()
        for y, x in itertools.product(range(256), range(512)):
            pixel = QColor(minimap.image.pixel(x, y))
            tpcData.extend([pixel.red(), pixel.green(), pixel.blue(), 255])
        minimapTpc = TPC()
        minimapTpc.set_data(512, 256, [tpcData], TPCTextureFormat.RGBA)
        self.mod.set_data(f"lbl_map{self.moduleId}", ResourceType.TGA, bytes_tpc(minimapTpc, ResourceType.TGA))

    def handle_loadscreen(self, installation):
        """Handles loading screen for installation
        Args:
            installation: The installation object
        Returns:
            None: Does not return anything
        - Loads the appropriate load screen TGA file based on installation type
        - Sets the loaded TGA as load screen data for the module.
        """
        loadTga = (BinaryReader.load_file("./kits/load_k2.tga") if installation.tsl else BinaryReader.load_file("./kits/load_k1.tga"))
        self.mod.set_data(f"load_{self.moduleId}", ResourceType.TGA, loadTga)

    def set_area_attributes(self, minimap):
        """Sets area attributes from minimap data
        Args:
            minimap: {Minimap object containing area bounds}.

        Returns
        -------
            None: {No return value}
        Processing Logic:
            - Set area tag from module ID
            - Set area dynamic lighting from lighting value
            - Set area name from name
            - Set area map points from minimap image bounds
            - Set area world points from minimap world bounds
            - Set default area map zoom and resolution.
        """
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
        """Sets attributes of IFO object
        Args:
            self: The class instance
        Returns:
            None: No return value
        - Sets tag attribute of IFO object to module ID
        - Sets area_name attribute of IFO object to module ID resource reference
        - Sets identifier attribute of IFO object to module ID resource reference
        - Calls set_all_visible() method on vis object to set all objects visible
        - Sets entry_position attribute of IFO object to warpPoint.
        """
        self.ifo.tag = self.moduleId
        self.ifo.area_name = ResRef(self.moduleId)
        self.ifo.identifier = ResRef(self.moduleId)
        self.vis.set_all_visible()
        self.ifo.entry_position = self.warpPoint

    def finalize_module_data(self, output_path: os.PathLike | str):
        """Finalizes module data and writes it to an ERF file
        Args:
            output_path: os.PathLike | str - Path to output ERF file
        Returns:
            None - Writes module data to ERF file
        Processing Logic:
            - Sets module data for LYT, VIS, ARE, GIT resources
            - Sets module info (IFO) data
            - Writes finalized module data to ERF file at output path.
        """
        self.mod.set_data(self.moduleId, ResourceType.LYT, bytes_lyt(self.lyt))
        self.mod.set_data(self.moduleId, ResourceType.VIS, bytes_vis(self.vis))
        self.mod.set_data(self.moduleId, ResourceType.ARE, bytes_are(self.are))
        self.mod.set_data(self.moduleId, ResourceType.GIT, bytes_git(self.git))
        self.mod.set_data("module", ResourceType.IFO, bytes_ifo(self.ifo))

        write_erf(self.mod, output_path)

    def build(self, installation: HTInstallation, kits: list[Kit], output_path: os.PathLike | str) -> None:
        """Builds the indoor map from room components and kits.

        Args:
        ----
            installation: HTInstallation - The installation object.
            kits: list[Kit] - List of available kits.
            output_path: os.PathLike | str - Path to output the built indoor map.

        Returns:
        -------
            None

        Processing Logic:
        - Adds all rooms from components to the indoor map
        - Processes room components like inserting textures and models
        - Handles textures renaming and lightmap generation
        - Processes skybox from kits
        - Generates and sets minimap
        - Handles loadscreen attributes
        - Inserts door connections
        - Sets area and info attributes
        - Finalizes and saves the indoor map data
        """
        self.mod = ERF(ERFType.MOD)
        self.lyt = LYT()
        self.vis = VIS()
        self.are = ARE()
        self.ifo = IFO()
        self.git = GIT()
        self.roomNames: dict[IndoorMapRoom, str] = {}
        self.texRenames: dict[str, str] = {}
        self.totalLm = 0
        self.usedRooms: set[KitComponent] = set()
        self.usedKits: set[Kit] = set()
        self.scanMdls: set[bytes] = set()

        self.add_rooms()
        self.process_room_components()
        self.handle_textures()
        self.handle_lightmaps(installation)
        self.process_skybox(kits)
        self.generate_and_set_minimap()

        self.handle_loadscreen(installation)
        self._handle_door_insertions(installation)
        self.set_area_attributes(self.generateMinimap())
        self.set_ifo_attributes()
        self.finalize_module_data(output_path)

    def write(self) -> bytes:
        """Writes module data to bytes
        Args:
            self: The Module object
        Returns:
            bytes: Serialized module data as bytes
        Writes module data to bytes:
        - Collects module data like name, lighting, skybox etc into a dictionary
        - Serializes room data like position, rotation etc for each room
        - Converts dictionary to JSON and encodes to bytes.
        """
        data: dict[str, str | dict | list] = {"moduleId": self.moduleId, "name": {}}

        data["name"]["stringref"] = self.name.stringref  # type: ignore[call-overload, index]
        for language, gender, text in self.name:
            stringid = LocalizedString.substring_id(language, gender)
            data["name"][stringid] = text  # type: ignore[index]

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
            data["rooms"].append(roomData)  # type: ignore[union-attr]

        return json.dumps(data).encode()

    def load(self, raw: bytes, kits: list[Kit]) -> None:
        """Load raw data and initialize the map
        Args:
            raw: Raw bytes data to load
            kits: List of available kits
        Returns:
            None
        - Decode raw data from JSON format
        - Try to load map data and initialize with available kits
        - Raise error if corrupted data is encountered during loading.
        """
        self.reset()
        data = json.loads(raw)

        try:
            self._load_data(data, kits)
        except KeyError as e:
            msg = "Map file is corrupted."
            raise ValueError(msg) from e

    def _load_data(self, data, kits):
        """Load data into an indoor map object
        Args:
            data: The indoor map data
            kits: Available kits
        Returns:
            self: The indoor map object with data loaded
        Processing Logic:
            - Load name data from stringrefs
            - Load lighting values
            - Load moduleId and skybox
            - For each room:
                - Find matching kit and component
                - Create room with position, rotation, flips.
        """
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
        """Generates a minimap image from room data to display an overview of the level layout.

        Args:
        ----
            self: The level object containing room data
        Returns:
            MinimapData: A data object containing the minimap image and bounding points
        Processing Logic:
            1. Get the bounding box of all walkmeshes
            2. Draw each room image onto the pixmap at the correct position/rotation
            3. Scale the pixmap to the target minimap size
            4. Return a MinimapData object containing the image and bounding points
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
        pixmap = pixmap.scaled(435, 256, QtCore.Qt.KeepAspectRatio)  # type: ignore[attr-defined, reportGeneralTypeIssues]

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
        """Calculates the position of a hook relative to the component.

        Args:
        ----
            hook (KitComponentHook): The hook to calculate the position for
            worldOffset (bool): Whether to offset the position by the component's world position
        Returns:
            Vector3: The calculated position of the hook
        Processing Logic:
            - Copies the hook's position
            - Flips the x and y coordinates if the component is flipped
            - Rotates the position by the component's rotation
            - Adds the component's position if worldOffset is True
            - Returns the final calculated position.
        """
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
        """Rebuilds connections between rooms
        Args:
            rooms: {List of rooms to rebuild connections from}.

        Returns
        -------
            None: {No return value}
        Processing Logic:
            - Loops through each hook in the component's hooks
            - Finds the index of the current hook
            - Gets the position of the current hook
            - Loops through each other room that is not the current room
            - Loops through each hook in the other room's component
            - Gets the position of the other hook
            - Checks if the distance between the two hook positions is close
            - Assigns the other room to the current hook's slot in the hooks list if close.
        """
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
        """Rotates and translates a copy of the component's BWM.

        Args:
        ----
            self: The component instance.

        Returns:
        -------
            bwm: A translated and rotated copy of the component's BWM.
        - A deep copy of the component's BWM is made to avoid modifying the original.
        - The copy is rotated by the component's rotation value.
        - The copy is translated to the component's position.
        - The translated and rotated copy is returned.
        """
        bwm = deepcopy(self.component.bwm)
        bwm.rotate(self.rotation)
        bwm.translate(self.position.x, self.position.y, self.position.z)
        return bwm
