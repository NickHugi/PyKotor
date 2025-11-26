from __future__ import annotations

import itertools
import json
import math

from copy import copy, deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Any, NamedTuple

from loggerplus import RobustLogger  # type: ignore[import-untyped]
from qtpy import QtCore
from qtpy.QtGui import QColor, QImage, QPainter, QPixmap, QTransform

from pykotor.common.language import LocalizedString  # type: ignore[import-not-found]
from pykotor.common.misc import Color, ResRef  # type: ignore[import-not-found]
from pykotor.extract.file import ResourceIdentifier  # type: ignore[import-not-found]
from pykotor.resource.formats.bwm import bytes_bwm  # type: ignore[import-not-found]
from pykotor.resource.formats.erf import ERF, ERFType, write_erf  # type: ignore[import-not-found]
from pykotor.resource.formats.lyt import LYT, LYTDoorHook, LYTRoom, bytes_lyt  # type: ignore[import-not-found]
from pykotor.resource.formats.tpc import TPC, TPCTextureFormat, bytes_tpc  # type: ignore[import-not-found]
from pykotor.resource.formats.vis import VIS, bytes_vis  # type: ignore[import-not-found]
from pykotor.resource.generics.are import ARE, ARENorthAxis, bytes_are  # type: ignore[import-not-found]
from pykotor.resource.generics.git import GIT, GITDoor, bytes_git  # type: ignore[import-not-found]
from pykotor.resource.generics.ifo import IFO, bytes_ifo  # type: ignore[import-not-found]
from pykotor.resource.generics.utd import bytes_utd  # type: ignore[import-not-found]
from pykotor.resource.type import ResourceType  # type: ignore[import-not-found]
from pykotor.tools import model  # type: ignore[import-not-found]
from utility.common.geometry import Vector2, Vector3, Vector4  # type: ignore[import-not-found]

if TYPE_CHECKING:
    import os

    from pykotor.resource.formats.bwm import BWM
    from pykotor.resource.generics.utd import UTD
    from toolset.data.indoorkit import Kit, KitComponent, KitComponentHook, KitDoor  # type: ignore[import-not-found]
    from toolset.data.installation import HTInstallation  # type: ignore[import-not-found]


class DoorInsertion(NamedTuple):
    door: KitDoor
    room: IndoorMapRoom
    room2: IndoorMapRoom | None
    static: bool
    position: Vector3
    rotation: float
    hook1: KitComponentHook
    hook2: KitComponentHook | None


class MinimapData(NamedTuple):
    image: QImage
    imagePointMin: Vector2
    imagePointMax: Vector2
    worldPointMin: Vector2
    worldPointMax: Vector2


class IndoorMap:
    def __init__(self):
        self.rooms: list[IndoorMapRoom] = []
        self.module_id: str = "test01"
        self.name: LocalizedString = LocalizedString.from_english("New Module")
        self.lighting: Color = Color(0.5, 0.5, 0.5)
        self.skybox: str = ""
        self.warp_point: Vector3 = Vector3.from_null()

    def rebuild_room_connections(self):
        for room in self.rooms:
            room.rebuild_connections(self.rooms)

    def door_insertions(self) -> list[DoorInsertion]:
        """Generates door insertions between rooms.

        Used when determining when to place doors when building a map.

        Args:
        ----
            self: The FloorPlan object.

        Returns:
        -------
            list[DoorInsertion]: Returns a list of connections between rooms.

        Processing Logic:
        ----------------
            1. Loops through each room and connection
            2. Determines door, rooms, hooks and positions
            3. Checks if door already exists at point
            4. Adds valid door insertion to return list.
        """
        points: list[Vector3] = []  # Used to determine if door already exists at this point
        insertions: list[DoorInsertion] = []

        for room in self.rooms:
            for hook_index, connection in enumerate(room.hooks):
                room1: IndoorMapRoom = room
                room2: IndoorMapRoom | None = None
                hook1: KitComponentHook = room1.component.hooks[hook_index]
                hook2: KitComponentHook | None = None
                door: KitDoor = hook1.door
                position: Vector3 = room1.hook_position(hook1)
                rotation: float = hook1.rotation + room1.rotation
                if connection is not None:
                    for otherHookIndex, otherRoom in enumerate(connection.hooks):
                        if otherRoom == room1:
                            other_hook: KitComponentHook = connection.component.hooks[otherHookIndex]
                            if hook1.door.width < other_hook.door.width:
                                door = other_hook.door
                                hook2 = hook1
                                hook1 = other_hook
                                room2 = room1
                                room1 = connection
                            else:
                                hook2 = connection.component.hooks[otherHookIndex]
                                room2 = connection
                                rotation = hook2.rotation + room2.rotation

                if position not in points:
                    points.append(position)  # 47
                    # if room2 is None:  # FIXME(th3w1zard1) ??? why is this conditional ever hit
                    #    msg = "room2 cannot be None"
                    #    raise ValueError(msg)

                    static: bool = connection is None
                    insertions.append(DoorInsertion(door, room1, room2, static, position, rotation, hook1, hook2))

        return insertions

    def add_rooms(self):
        for i in range(len(self.rooms)):
            modelname: str = f"{self.module_id}_room{i}"
            self.vis.add_room(modelname)

    def process_room_components(self):
        """Process room components by adding them to tracking sets.

        Args:
        ----
            self: The class instance.

        Processing Logic:
        ----------------
            - Iterate through rooms and add component to used_rooms set
            - Iterate through used_rooms and add mdl to scan_mdls and kit to used_kits
            - Iterate through door padding dicts and values, adding padding mdl to scan_mdls.
        """
        for room in self.rooms:
            self.used_rooms.add(room.component)
        for room in self.used_rooms:
            self.scan_mdls.add(room.mdl)
            self.used_kits.add(room.kit)
            for door_padding_dict in list(room.kit.top_padding.values()) + list(room.kit.side_padding.values()):
                for padding_model in door_padding_dict.values():
                    self.scan_mdls.add(padding_model.mdl)

    def handle_textures(self):
        """Rename textures to avoid conflicts.

        Processing Logic:
        ----------------
            - Scan through all models
            - Get textures from each model
            - Check if texture is already renamed
            - If not, rename it and add to renaming dictionary
            - Check texture usage in all kits
            - Replace texture references in kit textures and txis with new renamed texture.
        """
        for mdl in self.scan_mdls:
            for texture in (texture for texture in model.iterate_textures(mdl) if texture not in self.tex_renames):
                renamed: str = f"{self.module_id}_tex{len(self.tex_renames.keys())}"
                self.tex_renames[texture] = renamed
                for kit in self.used_kits:
                    if texture not in kit.textures:
                        continue
                    self.mod.set_data(renamed, ResourceType.TGA, kit.textures[texture])
                    self.mod.set_data(renamed, ResourceType.TXI, kit.txis[texture])

    def handle_lightmaps(
        self,
        installation: HTInstallation,
    ):
        """Processes lightmaps for a room model.

        Args:
        ----
            room: {The room object being processed}
            mdl: {The 3D room model object}.

        Processing Logic:
        ----------------
            - Loops through each face in the room model
            - Generates a lightmap texture for each face
            - Bakes ambient occlusion and lighting information into the lightmap texture
            - Attaches the generated lightmap texture to the corresponding face.
        """
        for i, room in enumerate(self.rooms):
            # Set model name
            modelname: str = f"{self.module_id}_room{i}"
            self.room_names[room] = modelname

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
            bwm: BWM = self.process_bwm(room)
            self.add_bwm_resource(modelname, bwm)

    def add_static_resources(
        self,
        room: IndoorMapRoom,
    ):
        """Adds static resources from a room's kit to the mod.

        Args:
        ----
            room: The room object containing static resources.

        Processes static resources:
            - Loops through each static resource filename and data in the room's kit
            - Extracts the resource name and type from the filename
            - Adds the resource data to the mod with the extracted name and type.
        """
        for filename, data in room.component.kit.always.items():
            resname, restype = ResourceIdentifier.from_path(filename).unpack()
            if restype == ResourceType.INVALID:
                print("Invalid resource, skipping...", filename, restype)
                continue
            self.mod.set_data(resname, restype, data)

    def process_model(
        self,
        room: IndoorMapRoom,
        installation: HTInstallation,
    ) -> tuple[bytes, bytes]:
        """Processes a model based on room properties.

        Args:
        ----
            room: IndoorMapRoom: The room object containing model properties
            installation: Installation: The installation object containing target system properties.

        Returns:
        -------
            mdl: str: The processed model string
            mdx: str: The processed material index string

        Processing Logic:
        ----------------
            - Flip the model based on room flip_x and flip_y properties
            - Rotate the model based on room rotation property
            - Convert the model to target system format based on installation tsl property
            - Return processed model and material index strings.
        """
        mdl, mdx = model.flip(room.component.mdl, room.component.mdx, flip_x=room.flip_x, flip_y=room.flip_y)
        mdl_transformed: bytes = model.transform(mdl, Vector3.from_null(), room.rotation)
        mdl_converted: bytes = model.convert_to_k2(mdl_transformed) if installation.tsl else model.convert_to_k1(mdl_transformed)
        return mdl_converted, mdx

    def process_lightmaps(
        self,
        room: IndoorMapRoom,
        mdl_data: bytes,
    ):
        """Processes lightmaps for a room.

        Args:
        ----
            room (IndoorMapRoom): The room to process lightmaps for
            mdl_data (bytes): The model to process lightmaps on

        Processing Logic:
        ----------------
            - Renames each lightmap to a unique name prefixed with the module ID
            - Sets the renamed lightmap and txi textures in the mod
            - Returns the model with all lightmaps renamed according to the mapping.
        """
        lm_renames: dict[str, str] = {}
        for lightmap in model.iterate_lightmaps(mdl_data):
            renamed: str = f"{self.module_id}_lm{self.total_lm}"
            self.total_lm += 1
            lm_renames[lightmap.lower()] = renamed
            self.mod.set_data(renamed, ResourceType.TGA, room.component.kit.lightmaps[lightmap])
            self.mod.set_data(renamed, ResourceType.TXI, room.component.kit.txis[lightmap])
        mdl_data = model.change_lightmaps(mdl_data, lm_renames)  # FIXME(th3w1zard1): Should this be returned and used throughout?

    def add_model_resources(
        self,
        modelname: str,
        mdl_data: bytes,
        mdx_data: bytes,
    ):
        """Adds model resources to the mod object.

        Args:
        ----
            modelname (str): Name of the model
            mdl_data (bytes): MDL file data
            mdx_data (bytes): MDX file data

        Processing Logic:
        ----------------
            - Sets the MDL file data for the given modelname using ResourceType.MDL
            - Sets the MDX file data for the given modelname using ResourceType.MDX
            - Does not return anything, just adds the resources to the mod object.
        """
        self.mod.set_data(modelname, ResourceType.MDL, mdl_data)
        self.mod.set_data(modelname, ResourceType.MDX, mdx_data)

    def process_bwm(
        self,
        room: IndoorMapRoom,
    ) -> BWM:
        """Processes the BWM for a room.

        Args:
        ----
            room: {IndoorMapRoom}: Room object containing BWM and transform info

        Returns:
        -------
            bwm: {OccupancyGridMap}: Processed BWM for the room

        Processing Logic:
        ----------------
            - Make a deep copy of the room BWM
            - Apply flip, rotation and translation transforms to the copy
            - Remap transition indices to reference connected rooms
            - Return the processed BWM.
        """
        bwm: BWM = deepcopy(room.component.bwm)
        bwm.flip(room.flip_x, room.flip_y)
        bwm.rotate(room.rotation)
        bwm.translate(room.position.x, room.position.y, room.position.z)
        for hook_index, connection in enumerate(room.hooks):
            dummy_index: int = int(room.component.hooks[hook_index].edge)
            actual_index: int | None = None if connection is None else self.rooms.index(connection)
            self.remap_transitions(bwm, dummy_index, actual_index)
        return bwm

    def remap_transitions(
        self,
        bwm: BWM,
        dummy_index: int,
        actual_index: int | None,
    ):
        """Remaps dummy transition index to actual transition index in BWM faces.

        Args:
        ----
            bwm: BWM object containing faces
            dummy_index: Dummy transition index to remap
            actual_index: Actual transition index to remap to

        Processing Logic:
        ----------------
            - Loops through each face in the BWM object
            - Checks if the face's trans1, trans2 or trans3 attribute equals the dummy index
            - If so, replaces it with the actual index.
        """
        for face in bwm.faces:
            if face.trans1 == dummy_index:
                face.trans1 = actual_index
            if face.trans2 == dummy_index:
                face.trans2 = actual_index
            if face.trans3 == dummy_index:
                face.trans3 = actual_index

    def add_bwm_resource(
        self,
        modelname: str,
        bwm: BWM,
    ):
        self.mod.set_data(modelname, ResourceType.WOK, bytes_bwm(bwm))

    def handle_door_insertions(  # noqa: PLR0915
        self,
        installation: HTInstallation,
    ):
        """Handle door insertions.

        Args:
        ----
            self: The class instance
            installation: The installation details

        Processing Logic:
        ----------------
            1. Loops through each door insertion
            2. Creates a door object and sets properties
            3. Copies UTD data and sets properties
            4. Adds door to layout and visibility graphs
            5. Checks for height/width padding needs and adds if needed.
        """
        padding_count = 0
        for i, insert in enumerate(self.door_insertions()):
            door = GITDoor(*insert.position)
            door_resname: str = f"{self.module_id}_dor{i:02}"
            door.resref = ResRef(door_resname)
            door.bearing = math.radians(insert.rotation)
            door.tweak_color = None
            self.git.doors.append(door)

            utd: UTD = deepcopy(insert.door.utd_k2 if installation.tsl else insert.door.utd_k1)
            utd.resref = door.resref
            utd.static = insert.static
            utd.tag = door_resname.title().replace("_", "")
            self.mod.set_data(door_resname, ResourceType.UTD, bytes_utd(utd))

            orientation: Vector4 = Vector4.from_euler(0, 0, math.radians(door.bearing))
            self.lyt.doorhooks.append(LYTDoorHook(self.room_names[insert.room], door_resname, insert.position, orientation))

            if insert.hook1 and insert.hook2:
                if insert.hook1.door.height != insert.hook2.door.height:
                    c_room: IndoorMapRoom | None = insert.room if insert.hook1.door.height < insert.hook2.door.height else insert.room2
                    if c_room is None:
                        RobustLogger().warning(f"No room found for door insertion {i}")
                        continue
                    c_hook: KitComponentHook = insert.hook1 if insert.hook1.door.height < insert.hook2.door.height else insert.hook2
                    alt_hook: KitComponentHook = insert.hook2 if insert.hook1.door.height < insert.hook2.door.height else insert.hook1

                    kit: Kit = c_room.component.kit
                    door_index: int = kit.doors.index(c_hook.door)
                    height: float = alt_hook.door.height * 100
                    padding_key: int | None = (
                        min(
                            (i for i in kit.top_padding[door_index] if i > height),
                            default=None,
                        )
                        if door_index in kit.top_padding
                        else None
                    )
                    if padding_key is None:
                        RobustLogger().info(f"No padding key found for door insertion {i}")
                    else:
                        padding_name: str = f"{self.module_id}_tpad{padding_count}"
                        padding_count += 1
                        pad_mdl: bytes = model.transform(
                            kit.top_padding[door_index][padding_key].mdl,
                            Vector3.from_null(),
                            insert.rotation,
                        )
                        pad_mdl_converted: bytes = model.convert_to_k2(pad_mdl) if installation.tsl else model.convert_to_k1(pad_mdl)
                        pad_mdl_converted = model.change_textures(pad_mdl_converted, self.tex_renames)
                        lmRenames: dict[str, str] = {}
                        for lightmap in model.iterate_lightmaps(pad_mdl_converted):
                            renamed: str = f"{self.module_id}_lm{self.total_lm}"
                            self.total_lm += 1
                            lmRenames[lightmap.lower()] = renamed
                            self.mod.set_data(renamed, ResourceType.TGA, kit.lightmaps[lightmap])
                            self.mod.set_data(renamed, ResourceType.TXI, kit.txis[lightmap])
                        pad_mdl = model.change_lightmaps(pad_mdl, lmRenames)
                        self.mod.set_data(padding_name, ResourceType.MDL, pad_mdl)
                        self.mod.set_data(padding_name, ResourceType.MDX, kit.top_padding[door_index][padding_key].mdx)
                        self.lyt.rooms.append(LYTRoom(padding_name, insert.position))
                        self.vis.add_room(padding_name)
                if insert.hook1.door.width != insert.hook2.door.width:
                    c_room = insert.room if insert.hook1.door.height < insert.hook2.door.height else insert.room2
                    c_hook = insert.hook1 if insert.hook1.door.height < insert.hook2.door.height else insert.hook2
                    alt_hook = insert.hook2 if insert.hook1.door.height < insert.hook2.door.height else insert.hook1
                    if c_room is None:
                        RobustLogger().warning(f"No room found for door insertion {i}")
                        continue
                    kit = c_room.component.kit
                    door_index = kit.doors.index(c_hook.door)
                    width: float = alt_hook.door.width * 100
                    padding_key = (
                        min(
                            (i for i in kit.side_padding[door_index] if i > width),
                            default=None,
                        )
                        if door_index in kit.side_padding
                        else None
                    )
                    if padding_key is not None:
                        padding_name = f"{self.module_id}_tpad{padding_count}"
                        padding_count += 1
                        pad_mdl = model.transform(
                            kit.side_padding[door_index][padding_key].mdl,
                            Vector3.from_null(),
                            insert.rotation,
                        )
                        pad_mdl = model.convert_to_k2(pad_mdl) if installation.tsl else model.convert_to_k1(pad_mdl)
                        pad_mdl = model.change_textures(pad_mdl, self.tex_renames)
                        lmRenames = {}
                        for lightmap in model.iterate_lightmaps(pad_mdl):
                            renamed = f"{self.module_id}_lm{self.total_lm}"
                            self.total_lm += 1
                            lmRenames[lightmap.lower()] = renamed
                            self.mod.set_data(renamed, ResourceType.TGA, kit.lightmaps[lightmap])
                            self.mod.set_data(renamed, ResourceType.TXI, kit.txis[lightmap])
                        pad_mdl = model.change_lightmaps(pad_mdl, lmRenames)
                        self.mod.set_data(padding_name, ResourceType.MDL, pad_mdl)
                        self.mod.set_data(padding_name, ResourceType.MDX, kit.side_padding[door_index][padding_key].mdx)
                        self.lyt.rooms.append(LYTRoom(padding_name, insert.position))
                        self.vis.add_room(padding_name)

    def process_skybox(
        self,
        kits: list[Kit],
    ):
        """Process the skybox for the module.

        Args:
        ----
            kits: List of kit objects containing skybox models

        Processing Logic:
        ----------------
            - Check if a skybox is specified for the module
            - Loop through kits to find matching skybox
            - Extract model and texture from matching kit
            - Set model and texture in module data
            - Add room to layout with model
            - Add room to visibility graph.
        """
        if not self.skybox:
            return
        for kit in kits:
            if self.skybox not in kit.skyboxes:
                continue
            mdl, mdx = kit.skyboxes[self.skybox].mdl, kit.skyboxes[self.skybox].mdx
            model_name: str = f"{self.module_id}_sky"
            mdl_converted: bytes = model.change_textures(mdl, self.tex_renames)
            self.mod.set_data(model_name, ResourceType.MDL, mdl_converted)
            self.mod.set_data(model_name, ResourceType.MDX, mdx)
            self.lyt.rooms.append(LYTRoom(model_name, Vector3.from_null()))
            self.vis.add_room(model_name)

    def generate_and_set_minimap(self):
        """Generates and sets the minimap texture.

        Args:
        ----
            self: The module object

        Processing Logic:
        ----------------
            - Generates a 256x512 minimap image from the module view
            - Converts the image to a bytearray with RGBA pixel values
            - Creates a TPC texture from the bytearray
            - Sets the TPC texture as the module's minimap label texture.
        """
        minimap: MinimapData = self.generate_mipmap()
        tpc_data: bytearray = bytearray()
        for y, x in itertools.product(range(256), range(512)):
            pixel: QColor = QColor(minimap.image.pixel(x, y))
            tpc_data.extend([pixel.red(), pixel.green(), pixel.blue(), 255])
        minimap_tpc: TPC = TPC()
        minimap_tpc.set_single(tpc_data, TPCTextureFormat.RGBA, 512, 256)
        self.mod.set_data(f"lbl_map{self.module_id}", ResourceType.TGA, bytes_tpc(minimap_tpc, ResourceType.TGA))

    def handle_loadscreen(
        self,
        installation: HTInstallation,
    ):
        """Handles loading screen for installation.

        Args:
        ----
            installation: The installation object

        Processing Logic:
        ----------------
            - Loads the appropriate load screen TGA file based on installation type
            - Sets the loaded TGA as load screen data for the module.
        """
        try:
            load_tga: bytes = Path("./kits/load_k2.tga" if installation.tsl else "./kits/load_k1.tga").read_bytes()
        except FileNotFoundError:
            RobustLogger().error(f"Load screen file not found for installation '{installation.name}'.")
        else:
            self.mod.set_data(f"load_{self.module_id}", ResourceType.TGA, load_tga)

    def set_area_attributes(
        self,
        minimap: MinimapData,
    ):
        """Sets area attributes from minimap data.

        Args:
        ----
            minimap: {Minimap object containing area bounds}.

        Processing Logic:
        ----------------
            - Set area tag from module ID
            - Set area dynamic lighting from lighting value
            - Set area name from name
            - Set area map points from minimap image bounds
            - Set area world points from minimap world bounds
            - Set default area map zoom and resolution.
        """
        self.are.tag = self.module_id
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
        """Sets attributes of IFO object.

        Args:
        ----
            self: The class instance

        Processing Logic:
        ----------------
            - Sets tag attribute of IFO object to module ID
            - Sets area_name attribute of IFO object to module ID resource reference
            - Sets identifier attribute of IFO object to module ID resource reference
            - Calls set_all_visible() method on vis object to set all objects visible
            - Sets entry_position attribute of IFO object to warpPoint.
        """
        self.ifo.tag = self.module_id
        self.ifo.area_name = ResRef(self.module_id)
        self.ifo.resref = ResRef(self.module_id)
        self.vis.set_all_visible()
        self.ifo.entry_position = self.warp_point

    def finalize_module_data(
        self,
        output_path: os.PathLike | str,
    ):
        """Finalizes module data and writes it to an ERF file.

        Args:
        ----
            output_path: os.PathLike | str - Path to output ERF file

        Returns:
        -------
            None - Writes module data to ERF file

        Processing Logic:
        ----------------
            - Sets module data for LYT, VIS, ARE, GIT resources
            - Sets module info (IFO) data
            - Writes finalized module data to ERF file at output path.
        """
        self.mod.set_data(self.module_id, ResourceType.LYT, bytes_lyt(self.lyt))
        self.mod.set_data(self.module_id, ResourceType.VIS, bytes_vis(self.vis))
        self.mod.set_data(self.module_id, ResourceType.ARE, bytes_are(self.are))
        self.mod.set_data(self.module_id, ResourceType.GIT, bytes_git(self.git))
        self.mod.set_data("module", ResourceType.IFO, bytes_ifo(self.ifo))

        write_erf(self.mod, output_path)

    def build(
        self,
        installation: HTInstallation,
        kits: list[Kit],
        output_path: os.PathLike | str,
    ):
        """Builds the indoor map from room components and kits.

        Args:
        ----
            installation: HTInstallation - The installation object.
            kits: list[Kit] - List of available kits.
            output_path: os.PathLike | str - Path to output the built indoor map.

        Processing Logic:
        ----------------
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
        self.room_names: dict[IndoorMapRoom, str] = {}
        self.tex_renames: dict[str, str] = {}
        self.total_lm: int = 0
        self.used_rooms: set[KitComponent] = set()
        self.used_kits: set[Kit] = set()
        self.scan_mdls: set[bytes] = set()

        self.add_rooms()
        self.process_room_components()
        self.handle_textures()
        self.handle_lightmaps(installation)
        self.process_skybox(kits)
        self.generate_and_set_minimap()

        self.handle_loadscreen(installation)
        self.handle_door_insertions(installation)
        self.set_area_attributes(self.generate_mipmap())
        self.set_ifo_attributes()
        self.finalize_module_data(output_path)

    def write(self) -> bytes:
        """Writes module data to bytes.

        Args:
        ----
            self: The Module object

        Returns:
        -------
            bytes: Serialized module data encoded as utf-8 bytes

        Writes module data to bytes:
            - Collects module data like name, lighting, skybox etc into a dictionary
            - Serializes room data like position, rotation etc for each room
            - Converts dictionary to JSON and encodes to bytes.
        """
        data: dict[str, str | dict | list] = {"module_id": self.module_id, "name": {}}

        data["name"]["stringref"] = self.name.stringref  # type: ignore[call-overload, index]
        for language, gender, text in self.name:
            stringid: int = LocalizedString.substring_id(language, gender)
            data["name"][stringid] = text  # type: ignore[index]

        data["lighting"] = [self.lighting.r, self.lighting.g, self.lighting.b]
        data["skybox"] = self.skybox
        data["warp"] = self.module_id

        data["rooms"] = []
        for room in self.rooms:
            room_data: dict[str, Any] = {
                "position": [*room.position],
                "rotation": room.rotation,
                "flip_x": room.flip_x,
                "flip_y": room.flip_y,
                "kit": room.component.kit.name,
                "component": room.component.name,
            }
            data["rooms"].append(room_data)  # type: ignore[union-attr]

        return json.dumps(data).encode()

    def load(
        self,
        raw: bytes,
        kits: list[Kit],
    ):
        """Load raw data and initialize the map.

        Args:
        ----
            raw: Raw bytes data to load
            kits: List of available kits

        Processing Logic:
        ----------------
            - Decode raw data from JSON format
            - Try to load map data and initialize with available kits
            - Raise error if corrupted data is encountered during loading.
        """
        self.reset()
        data: dict[str, Any] = json.loads(raw)

        try:
            self._load_data(data, kits)
        except KeyError as e:
            msg = "Map file is corrupted."
            raise ValueError(msg) from e

    def _load_data(
        self,
        data: dict[str, Any],
        kits: list[Kit],
    ):
        """Load data into an indoor map object.

        Args:
        ----
            self: The indoor map object
            data: The indoor map data
            kits: Available kits

        Returns:
        -------
            None: Loads the data into the indoor map object

        Processing Logic:
        ----------------
            - Load name data from stringrefs
            - Load lighting values
            - Load module_id and skybox
            - For each room:
                - Find matching kit and component
                - Create room with position, rotation, flips.
        """
        self.name = LocalizedString(data["name"]["stringref"])
        for substring_id in (key for key in data["name"] if key.isnumeric()):
            language, gender = LocalizedString.substring_pair(int(substring_id))
            self.name.set_data(language, gender, data["name"][substring_id])

        self.lighting.b = data["lighting"][0]
        self.lighting.g = data["lighting"][1]
        self.lighting.r = data["lighting"][2]

        self.module_id = data["warp"]
        self.skybox = data.get("skybox", "")

        for room_data in data["rooms"]:
            sKit: Kit | None = next((kit for kit in kits if kit.name == room_data["kit"]), None)
            if sKit is None:
                msg = f"""Required kit is missing '{room_data["kit"]}'."""
                raise ValueError(msg)

            s_component: KitComponent | None = next(
                (component for component in sKit.components if component.name == room_data["component"]),
                None,
            )
            if s_component is None:
                msg = f"""Required component '{room_data["component"]}' is missing in kit '{sKit.name}'."""
                raise ValueError(msg)

            room: IndoorMapRoom = IndoorMapRoom(
                s_component,
                Vector3(room_data["position"][0], room_data["position"][1], room_data["position"][2]),
                room_data["rotation"],
                flip_x=bool(room_data.get("flip_x", False)),
                flip_y=bool(room_data.get("flip_y", False)),
            )
            self.rooms.append(room)

    def reset(self):
        self.rooms.clear()
        self.module_id = "test01"
        self.name = LocalizedString.from_english("New Module")
        self.lighting = Color(0.5, 0.5, 0.5)

    def generate_mipmap(self) -> MinimapData:
        """Generates a minimap image from room data to display an overview of the level layout.

        Args:
        ----
            self: The level object containing room data

        Returns:
        -------
            MinimapData: A data object containing the minimap image and bounding points

        Processing Logic:
        ----------------
            1. Get the bounding box of all walkmeshes
            2. Draw each room image onto the pixmap at the correct position/rotation
            3. Scale the pixmap to the target minimap size
            4. Return a MinimapData object containing the image and bounding points
        """
        # Get the bounding box that encompasses all the walkmeshes, we will use this to determine the size of the
        # unscaled pixmap for our minimap
        walkmeshes: list[BWM] = []
        for room in self.rooms:
            bwm: BWM = deepcopy(room.component.bwm)
            bwm.flip(room.flip_x, room.flip_y)
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

        width: float = bbmax.x * 10 - bbmin.x * 10
        height: float = bbmax.y * 10 - bbmin.y * 10
        pixmap: QPixmap = QPixmap(int(width), int(height))
        pixmap.fill(QColor(0))

        # Draw the actual minimap
        painter = QPainter(pixmap)
        for room in self.rooms:
            image: QImage = room.component.image

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
        pixmap = pixmap.scaled(435, 256, QtCore.Qt.KeepAspectRatio)  # type: ignore[attr-defined]

        pixmap2 = QPixmap(512, 256)
        pixmap2.fill(QColor(0))
        painter2 = QPainter(pixmap2)
        painter2.drawPixmap(0, int(128 - pixmap.height() / 2), pixmap)

        image = pixmap2.transformed(QTransform().scale(1, -1)).toImage()
        image.convertTo(QImage.Format.Format_RGB888)
        image_point_min: Vector2 = Vector2(0 / 435, (128 - pixmap.height() / 2) / 256)  # +512-435
        image_point_max: Vector2 = Vector2((image_point_min.x + pixmap.width()) / 435, (image_point_min.y + pixmap.height()) / 256)
        world_point_min: Vector2 = Vector2(bbmax.x, bbmin.y)
        world_point_max: Vector2 = Vector2(bbmin.x, bbmax.y)

        painter2.end()

        del painter2
        del pixmap
        del pixmap2

        return MinimapData(image, image_point_min, image_point_max, world_point_min, world_point_max)

    def _normalize_bwm_vertices(
        self,
        bbmin: Vector3,
        vertex: Vector3,
        bbmax: Vector3,
    ):
        bbmin.x = min(bbmin.x, vertex.x)
        bbmin.y = min(bbmin.y, vertex.y)
        bbmin.z = min(bbmin.z, vertex.z)
        bbmax.x = max(bbmax.x, vertex.x)
        bbmax.y = max(bbmax.y, vertex.y)
        bbmax.z = max(bbmax.z, vertex.z)


class IndoorMapRoom:
    def __init__(
        self,
        component: KitComponent,
        position: Vector3,
        rotation: float,
        *,
        flip_x: bool,
        flip_y: bool,
    ):
        self.component: KitComponent = component
        self.position: Vector3 = position
        self.rotation: float = rotation
        self.hooks: list[IndoorMapRoom | None] = [None] * len(component.hooks)
        self.flip_x: bool = flip_x
        self.flip_y: bool = flip_y

    def hook_position(
        self,
        hook: KitComponentHook,
        *,
        world_offset: bool = True,
    ) -> Vector3:
        """Calculates the position of a hook relative to the component.

        Args:
        ----
            hook (KitComponentHook): The hook to calculate the position for
            world_offset (bool): Whether to offset the position by the component's world position

        Returns:
        -------
            Vector3: The calculated position of the hook

        Processing Logic:
        ----------------
            - Copies the hook's position
            - Flips the x and y coordinates if the component is flipped
            - Rotates the position by the component's rotation
            - Adds the component's position if world_offset is True
            - Returns the final calculated position.
        """
        pos: Vector3 = copy(hook.position)

        pos.x = -pos.x if self.flip_x else pos.x
        pos.y = -pos.y if self.flip_y else pos.y
        temp: Vector3 = copy(pos)

        cos: float = math.cos(math.radians(self.rotation))
        sin: float = math.sin(math.radians(self.rotation))
        pos.x = temp.x * cos - temp.y * sin
        pos.y = temp.x * sin + temp.y * cos

        if world_offset:
            pos = pos + self.position

        return pos

    def rebuild_connections(
        self,
        rooms: list[IndoorMapRoom],
    ):
        """Rebuilds connections between rooms.

        Args:
        ----
            rooms: {List of rooms to rebuild connections from}.

        Returns:
        -------
            None: {No return value}

        Processing Logic:
        ----------------
            - Loops through each hook in the component's hooks
            - Finds the index of the current hook
            - Gets the position of the current hook
            - Loops through each other room that is not the current room
            - Loops through each hook in the other room's component
            - Gets the position of the other hook
            - Checks if the distance between the two hook positions is close
            - Assigns the other room to the current hook's slot in the hooks list if close.
        """
        self.hooks = [None] * len(self.component.hooks)

        for hook in self.component.hooks:
            hook_index: int = self.component.hooks.index(hook)
            hook_pos: Vector3 = self.hook_position(hook)
            for otherRoom in (room for room in rooms if room is not self):
                for other_hook in otherRoom.component.hooks:
                    other_hook_pos: Vector3 = otherRoom.hook_position(other_hook)
                    if hook_pos.distance(other_hook_pos) < 0.001:  # noqa: PLR2004
                        self.hooks[hook_index] = otherRoom

    def walkmesh(self) -> BWM:
        """Rotates and translates a copy of the component's BWM.

        Args:
        ----
            self: The component instance.

        Returns:
        -------
            bwm: A translated and rotated copy of the component's BWM.

        Processing Logic:
        ----------------
            - A deep copy of the component's BWM is made to avoid modifying the original.
            - The copy is flipped, rotated, and translated to match the room's transformation.
            - The transformed copy is returned.
        """
        bwm: BWM = deepcopy(self.component.bwm)
        bwm.flip(self.flip_x, self.flip_y)
        bwm.rotate(self.rotation)
        bwm.translate(self.position.x, self.position.y, self.position.z)
        return bwm
