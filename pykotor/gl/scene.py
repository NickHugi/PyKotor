from __future__ import annotations

import math
import random
from contextlib import suppress
from copy import copy
from typing import Dict, List, Any, Optional, Union, Callable

import glm
from OpenGL.GL import glReadPixels
from OpenGL.raw.GL.VERSION.GL_1_0 import glEnable, GL_TEXTURE_2D, GL_DEPTH_TEST, glClearColor, glClear, \
    GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_RGBA, GL_BLEND, glBlendFunc, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, \
    glDisable, GL_CULL_FACE, GL_CW, GL_BACK, glCullFace, GL_FRONT_AND_BACK
from OpenGL.raw.GL.VERSION.GL_1_2 import GL_UNSIGNED_INT_8_8_8_8, GL_BGRA
from glm import mat4, vec3, quat, vec4
from pykotor.common.misc import CaseInsensitiveDict
from pykotor.common.module import Module
from pykotor.common.stream import BinaryReader
from pykotor.extract.file import ResourceIdentifier
from pykotor.extract.installation import Installation, SearchLocation
from pykotor.resource.formats.lyt import LYT
from pykotor.resource.formats.twoda import read_2da
from pykotor.resource.generics.git import GIT, GITPlaceable, GITCreature, GITDoor, GITTrigger, GITEncounter, \
    GITWaypoint, GITSound, GITStore, GITCamera, GITInstance
from pykotor.resource.type import ResourceType

from pykotor.gl.shader import Shader, KOTOR_VSHADER, KOTOR_FSHADER, Texture, PICKER_FSHADER, PICKER_VSHADER, \
    PLAIN_VSHADER, PLAIN_FSHADER
from pykotor.gl.modelreader import gl_load_mdl, gl_load_stitched_model
from pykotor.gl.model import Model, Cube, Boundary, Empty
from pykotor.gl.models.predefined import STORE_MDL_DATA, STORE_MDX_DATA, WAYPOINT_MDL_DATA, WAYPOINT_MDX_DATA, \
    SOUND_MDL_DATA, SOUND_MDX_DATA, CAMERA_MDL_DATA, CAMERA_MDX_DATA, TRIGGER_MDL_DATA, TRIGGER_MDX_DATA, \
    ENCOUNTER_MDL_DATA, ENCOUNTER_MDX_DATA, ENTRY_MDL_DATA, ENTRY_MDX_DATA, EMPTY_MDL_DATA, EMPTY_MDX_DATA

SEARCH_ORDER_2DA = [SearchLocation.CHITIN]
SEARCH_ORDER = [SearchLocation.CUSTOM_MODULES, SearchLocation.OVERRIDE, SearchLocation.CHITIN]


class Scene:
    SPECIAL_MODELS = ["waypoint", "store", "sound", "camera", "trigger", "encounter"]

    def __init__(self, module: Module, installation: Installation):
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_DEPTH_TEST)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glCullFace(GL_BACK)

        self.installation: Installation = installation
        self.textures: CaseInsensitiveDict[Texture] = CaseInsensitiveDict()
        self.models: CaseInsensitiveDict[Model] = CaseInsensitiveDict()
        self.objects: List[RenderObject] = []
        self.selection: List[RenderObject] = []
        self.module: Module = module
        self.camera: Camera = Camera()

        self.textures["NULL"] = Texture.from_color()

        self.git: Optional[GIT] = None
        self.layout: Optional[LYT] = None
        self.objects: Dict[Any, RenderObject] = {}
        self.clearCacheBuffer: List[ResourceIdentifier] = []

        self.picker_shader: Shader = Shader(PICKER_VSHADER, PICKER_FSHADER)
        self.plain_shader: Shader = Shader(PLAIN_VSHADER, PLAIN_FSHADER)
        self.shader: Shader = Shader(KOTOR_VSHADER, KOTOR_FSHADER)

        self.jumpToEntryLocation()

        self.table_doors = read_2da(installation.resource("genericdoors", ResourceType.TwoDA, SEARCH_ORDER_2DA).data)
        self.table_placeables = read_2da(installation.resource("placeables", ResourceType.TwoDA, SEARCH_ORDER_2DA).data)
        self.table_creatures = read_2da(installation.resource("appearance", ResourceType.TwoDA, SEARCH_ORDER_2DA).data)
        self.table_heads = read_2da(installation.resource("heads", ResourceType.TwoDA, SEARCH_ORDER_2DA).data)

        self.hide_creatures: bool = False
        self.hide_placeables: bool = False
        self.hide_doors: bool = False
        self.hide_triggers: bool = False
        self.hide_encounters: bool = False
        self.hide_waypoints: bool = False
        self.hide_sounds: bool = False
        self.hide_stores: bool = False
        self.hide_cameras: bool = False
        self.hide_sound_boundaries: bool = True
        self.hide_trigger_boundaries: bool = True
        self.hide_encounter_boundaries: bool = True
        self.backface_culling: bool = True

    def buildCache(self, clearCache: bool = False) -> None:
        if clearCache:
            self.objects = {}

        for identifier in self.clearCacheBuffer:
            for creature in copy(self.git.creatures):
                if identifier.resname == creature.resref and identifier.restype == ResourceType.UTC:
                    del self.objects[creature]
            for placeable in copy(self.git.creatures):
                if identifier.resname == placeable.resref and identifier.restype == ResourceType.UTP:
                    del self.objects[placeable]
            for door in copy(self.git.doors):
                if door.resref.get() == identifier.resname and identifier.restype == ResourceType.UTD:
                    del self.objects[door]
            if identifier.restype in [ResourceType.TPC, ResourceType.TGA]:
                del self.textures[identifier.resname]
            if identifier.restype in [ResourceType.MDL, ResourceType.MDX]:
                del self.models[identifier.resname]
        self.clearCacheBuffer = []

        if self.git is None:
            self.git = self.module.git().resource()

        if self.layout is None:
            self.layout = self.module.layout().resource()

        for room in self.layout.rooms:
            if room not in self.objects:
                position = vec3(room.position.x, room.position.y, room.position.z)
                self.objects[room] = RenderObject(room.model, position)

        for door in self.git.doors:
            if door not in self.objects:
                position = vec3(door.position.x, door.position.y, door.position.z)
                rotation = vec3(0, 0, door.bearing)

                try:
                    utd = self.module.door(door.resref.get()).resource()
                    model_name = self.table_doors.get_row(utd.appearance_id).get_string("modelname")
                except Exception:
                    # If failed to load creature models, use an empty model instead
                    model_name = "empty"

                self.objects[door] = RenderObject(model_name, position, rotation, data=door)
            else:
                self.objects[door].set_position(door.position.x, door.position.y, door.position.z)
                self.objects[door].set_rotation(0, 0, door.bearing)

        for placeable in self.git.placeables:
            if placeable not in self.objects:
                position = vec3(placeable.position.x, placeable.position.y, placeable.position.z)
                rotation = vec3(0, 0, placeable.bearing)

                try:
                    utp = self.module.placeable(placeable.resref.get()).resource()
                    model_name = self.table_placeables.get_row(utp.appearance_id).get_string("modelname")
                except Exception:
                    # If failed to load creature models, use an empty model instead
                    model_name = "empty"

                self.objects[placeable] = RenderObject(model_name, position, rotation, data=placeable)
            else:
                self.objects[placeable].set_position(placeable.position.x, placeable.position.y, placeable.position.z)
                self.objects[placeable].set_rotation(0, 0, placeable.bearing)

        for creature in self.git.creatures:
            if creature not in self.objects:
                position = vec3(creature.position.x, creature.position.y, creature.position.z)
                rotation = vec3(0, 0, creature.bearing)

                try:
                    utc = self.module.creature(creature.resref.get()).resource()
                    body_model = self.table_creatures.get_row(utc.appearance_id).get_string("race")
                    obj = RenderObject(body_model, position, rotation, data=creature)

                    head_str = self.table_creatures.get_row(utc.appearance_id).get_string("normalhead")
                    if head_str:
                        head_id = int(head_str)
                        head_model = self.table_heads.get_row(head_id).get_string("head")
                        head_obj = RenderObject(head_model)
                        head_obj.set_transform(self.model(body_model).find("headhook").global_transform())
                        obj.children.append(head_obj)
                except Exception:
                    # If failed to load creature models, use an empty model instead
                    obj = RenderObject("empty", position, rotation, data=creature)

                self.objects[creature] = obj
            else:
                self.objects[creature].set_position(creature.position.x, creature.position.y, creature.position.z)
                self.objects[creature].set_rotation(0, 0, creature.bearing)

        for waypoint in self.git.waypoints:
            if waypoint not in self.objects:
                position = vec3(waypoint.position.x, waypoint.position.y, waypoint.position.z)
                rotation = vec3(0, 0, waypoint.bearing)
                obj = RenderObject("waypoint", position, rotation, data=waypoint)
                self.objects[waypoint] = obj
            else:
                self.objects[waypoint].set_position(waypoint.position.x, waypoint.position.y, waypoint.position.z)
                self.objects[waypoint].set_rotation(0, 0, waypoint.bearing)

        for store in self.git.stores:
            if store not in self.objects:
                position = vec3(store.position.x, store.position.y, store.position.z)
                rotation = vec3(0, 0, store.bearing)
                obj = RenderObject("store", position, rotation, data=store)
                self.objects[store] = obj
            else:
                self.objects[store].set_position(store.position.x, store.position.y, store.position.z)
                self.objects[store].set_rotation(0, 0, store.bearing)

        for sound in self.git.sounds:
            if sound not in self.objects:
                genBoundary = lambda: Empty(self)
                with suppress(Exception):
                    uts = self.module.sound(sound.resref.get()).resource()
                    genBoundary = lambda: Boundary.from_circle(self, uts.max_distance)

                position = vec3(sound.position.x, sound.position.y, sound.position.z)
                rotation = vec3(0, 0, 0)
                obj = RenderObject("sound", position, rotation, data=sound, genBoundary=genBoundary)
                self.objects[sound] = obj
            else:
                self.objects[sound].set_position(sound.position.x, sound.position.y, sound.position.z)
                self.objects[sound].set_rotation(0, 0, 0)

        for encounter in self.git.encounters:
            if encounter not in self.objects:
                position = vec3(encounter.position.x, encounter.position.y, encounter.position.z)
                rotation = vec3(0, 0, 0)
                genBoundary = lambda: Boundary(self, encounter.geometry.points)
                obj = RenderObject("encounter", position, rotation, data=encounter, genBoundary=genBoundary)
                self.objects[encounter] = obj
            else:
                self.objects[encounter].set_position(encounter.position.x, encounter.position.y, encounter.position.z)
                self.objects[encounter].set_rotation(0, 0, 0)

        for trigger in self.git.triggers:
            if trigger not in self.objects:
                position = vec3(trigger.position.x, trigger.position.y, trigger.position.z)
                rotation = vec3(0, 0, 0)
                genBoundary = lambda: Boundary(self, trigger.geometry.points)
                obj = RenderObject("trigger", position, rotation, data=trigger, genBoundary=genBoundary)
                self.objects[trigger] = obj
            else:
                self.objects[trigger].set_position(trigger.position.x, trigger.position.y, trigger.position.z)
                self.objects[trigger].set_rotation(0, 0, 0)

        for camera in self.git.cameras:
            if camera not in self.objects:
                position = vec3(camera.position.x, camera.position.y, camera.position.z)
                rotation = glm.eulerAngles(quat(camera.orientation.x, camera.orientation.y, camera.orientation.z, camera.orientation.w))
                obj = RenderObject("camera", position, rotation, data=camera)
                self.objects[camera] = obj
            else:
                self.objects[camera].set_position(camera.position.x, camera.position.y, camera.position.z)
                euler = glm.eulerAngles(quat(camera.orientation.x, camera.orientation.y, camera.orientation.z, camera.orientation.w))
                self.objects[camera].set_rotation(euler.x, euler.y, euler.z)

        # Detect if GIT still exists; if they do not then remove them from the render list
        for obj in copy(self.objects):
            if isinstance(obj, GITCreature) and obj not in self.git.creatures:
                del self.objects[obj]
            if isinstance(obj, GITPlaceable) and obj not in self.git.placeables:
                del self.objects[obj]
            if isinstance(obj, GITDoor) and obj not in self.git.doors:
                del self.objects[obj]
            if isinstance(obj, GITTrigger) and obj not in self.git.triggers:
                del self.objects[obj]
            if isinstance(obj, GITStore) and obj not in self.git.stores:
                del self.objects[obj]
            if isinstance(obj, GITCamera) and obj not in self.git.cameras:
                del self.objects[obj]
            if isinstance(obj, GITWaypoint) and obj not in self.git.waypoints:
                del self.objects[obj]
            if isinstance(obj, GITEncounter) and obj not in self.git.encounters:
                del self.objects[obj]
            if isinstance(obj, GITSound) and obj not in self.git.sounds:
                del self.objects[obj]

    def render(self) -> None:
        self.buildCache()
        glClearColor(0.5, 0.5, 1, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if self.backface_culling:
            glEnable(GL_CULL_FACE)

        glDisable(GL_BLEND)
        self.shader.use()
        self.shader.set_matrix4("view", self.camera.view())
        self.shader.set_matrix4("projection", self.camera.projection())
        group1 = [obj for obj in self.objects.values() if obj.model not in self.SPECIAL_MODELS]
        for obj in group1:
            self._render_object(self.shader, obj, mat4())

        # Draw all instance types that lack a proper model
        glEnable(GL_BLEND)
        self.plain_shader.use()
        self.plain_shader.set_matrix4("view", self.camera.view())
        self.plain_shader.set_matrix4("projection", self.camera.projection())
        self.plain_shader.set_vector4("color", vec4(0.0, 0.0, 1.0, 0.4))
        group2 = [obj for obj in self.objects.values() if obj.model in self.SPECIAL_MODELS]
        for obj in group2:
            self._render_object(self.plain_shader, obj, mat4())

        # Draw bounding box for selected objects
        self.plain_shader.set_vector4("color", vec4(1.0, 0.0, 0.0, 0.4))
        for obj in self.selection:
            obj.cube(self).draw(self.plain_shader, obj.transform())

        # Draw boundary for selected objects
        glDisable(GL_CULL_FACE)
        self.plain_shader.set_vector4("color", vec4(0.0, 1.0, 0.0, 0.4))
        for obj in self.selection:
            obj.boundary(self).draw(self.plain_shader, obj.transform())

        # Draw non-selected boundaries
        for obj in [obj for obj in self.objects.values() if obj.model == "sound" and not self.hide_sound_boundaries]:
            obj.boundary(self).draw(self.plain_shader, obj.transform())
        for obj in [obj for obj in self.objects.values() if obj.model == "encounter" and not self.hide_encounter_boundaries]:
            obj.boundary(self).draw(self.plain_shader, obj.transform())
        for obj in [obj for obj in self.objects.values() if obj.model == "trigger" and not self.hide_trigger_boundaries]:
            obj.boundary(self).draw(self.plain_shader, obj.transform())

    def _render_object(self, shader: Shader, obj: RenderObject, transform: mat4) -> None:
        if isinstance(obj.data, GITCreature) and self.hide_creatures:
            return
        if isinstance(obj.data, GITPlaceable) and self.hide_placeables:
            return
        if isinstance(obj.data, GITDoor) and self.hide_doors:
            return
        if isinstance(obj.data, GITTrigger) and self.hide_triggers:
            return
        if isinstance(obj.data, GITEncounter) and self.hide_encounters:
            return
        if isinstance(obj.data, GITWaypoint) and self.hide_waypoints:
            return
        if isinstance(obj.data, GITSound) and self.hide_sounds:
            return
        if isinstance(obj.data, GITStore) and self.hide_sounds:
            return
        if isinstance(obj.data, GITCamera) and self.hide_cameras:
            return

        model = self.model(obj.model)
        model.draw(shader, transform * obj.transform())
        for child in obj.children:
            self._render_object(shader, child, obj.transform())

    def picker_render(self) -> None:
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.picker_shader.use()
        self.picker_shader.set_matrix4("view", self.camera.view())
        self.picker_shader.set_matrix4("projection", self.camera.projection())
        instances = list(self.objects.values())
        for i, obj in enumerate(instances):
            int_rgb = instances.index(obj)
            r = int_rgb & 0xFF
            g = (int_rgb >> 8) & 0xFF
            b = (int_rgb >> 16) & 0xFF
            color = vec3(r / 255, g / 255, b / 255)
            self.picker_shader.set_vector3("colorId", color)

            self._picker_render_object(obj, mat4())

    def _picker_render_object(self, obj: RenderObject, transform: mat4) -> None:
        model = self.model(obj.model)
        model.draw(self.picker_shader, transform * obj.transform())
        for child in obj.children:
            self._picker_render_object(child, obj.transform())

    def pick(self, x, y) -> RenderObject:
        self.picker_render()
        pixel = glReadPixels(x, y, 1, 1, GL_BGRA, GL_UNSIGNED_INT_8_8_8_8)[0][0] >> 8
        instances = list(self.objects.values())
        return instances[pixel] if pixel != 0xFFFFFF else None

    def select(self, target: Union[RenderObject, GITInstance], clear_existing: bool = True):
        if clear_existing:
            self.selection.clear()

        if isinstance(target, GITInstance):
            for obj in self.objects.values():
                if obj.data is target:
                    target = obj
                    break

        self.selection.append(target)

    def texture(self, name: str) -> Texture:
        if name not in self.textures:
            # Check the textures linked to the module first
            tpc = self.module.texture(name).resource() if self.module.texture(name) is not None else None
            # Otherwise just search through all relevant game files
            tpc = self.installation.texture(name, [SearchLocation.OVERRIDE, SearchLocation.TEXTURES_TPA,
                                                   SearchLocation.CHITIN]) if tpc is None else tpc

            self.textures[name] = Texture.from_tpc(tpc) if tpc is not None else Texture.from_color(255, 0, 255)
        return self.textures[name]

    def model(self, name: str) -> Model:
        if name not in self.models:
            if name == "waypoint":
                mdl_data = WAYPOINT_MDL_DATA
                mdx_data = WAYPOINT_MDX_DATA
            elif name == "sound":
                mdl_data = SOUND_MDL_DATA
                mdx_data = SOUND_MDX_DATA
            elif name == "store":
                mdl_data = STORE_MDL_DATA
                mdx_data = STORE_MDX_DATA
            elif name == "entry":
                mdl_data = ENTRY_MDL_DATA
                mdx_data = ENTRY_MDX_DATA
            elif name == "encounter":
                mdl_data = ENCOUNTER_MDL_DATA
                mdx_data = ENCOUNTER_MDX_DATA
            elif name == "trigger":
                mdl_data = TRIGGER_MDL_DATA
                mdx_data = TRIGGER_MDX_DATA
            elif name == "camera":
                mdl_data = CAMERA_MDL_DATA
                mdx_data = CAMERA_MDX_DATA
            elif name == "empty":
                mdl_data = EMPTY_MDL_DATA
                mdx_data = EMPTY_MDX_DATA
            else:
                mdl_data = self.installation.resource(name, ResourceType.MDL, SEARCH_ORDER, capsules=self.module.capsules()).data
                mdx_data = self.installation.resource(name, ResourceType.MDX, SEARCH_ORDER, capsules=self.module.capsules()).data

            # model = gl_load_mdl(self, BinaryReader.from_bytes(mdl_data, 12), BinaryReader.from_bytes(mdx_data))
            model = gl_load_stitched_model(self, BinaryReader.from_bytes(mdl_data, 12), BinaryReader.from_bytes(mdx_data))
            self.models[name] = model
        return self.models[name]

    def jumpToEntryLocation(self) -> None:
        point = self.module.info().resource().entry_position
        self.camera.x = point.x
        self.camera.y = point.y
        self.camera.z = point.z + 1.5


class RenderObject:
    def __init__(self, model: str, position: vec3 = None, rotation: vec3 = None, *, data: Any = None,
                 genBoundary: Callable[[], Boundary] = None):
        self.model: str = model
        self.children: List[RenderObject] = []
        self._transform: mat4 = mat4()
        self._position: vec3 = position if position is not None else vec3()
        self._rotation: vec3 = rotation if rotation is not None else vec3()
        self._cube: Optional[Cube] = None
        self._boundary: Optional[Boundary] = None
        self.genBoundary: Optional[Callable[[], Boundary]] = genBoundary
        self.data: Any = data

        self._recalc_transform()

    def transform(self) -> mat4:
        return self._transform

    def set_transform(self, transform: mat4) -> None:
        self._transform = transform
        rotation = quat()
        glm.decompose(transform, vec3(), rotation, self._position, vec3(), vec4())
        self._rotation = glm.eulerAngles(rotation)

    def _recalc_transform(self) -> None:
        self._transform = glm.translate(mat4(), self._position)
        self._transform = self._transform * glm.mat4_cast(quat(self._rotation))

    def position(self) -> vec3:
        return copy(self._position)

    def set_position(self, x: float, y: float, z: float) -> None:
        if self._position.x == x and self._position.y == y and self._position.z == z:
            return

        self._position = vec3(x, y, z)
        self._recalc_transform()

    def rotation(self) -> vec3:
        return copy(self._rotation)

    def set_rotation(self, x: float, y: float, z: float) -> None:
        if self._rotation.x == x and self._rotation.y == y and self._rotation.z == z:
            return

        self._rotation = vec3(x, y, z)
        self._recalc_transform()

    def reset_cube(self) -> None:
        self._cube = None

    def cube(self, scene: Scene) -> Cube:
        if not self._cube:
            min_point = vec3(10000, 10000, 10000)
            max_point = vec3(-10000, -10000, -10000)
            self._cube_rec(scene, mat4(), self, min_point, max_point)
            self._cube = Cube(scene, min_point, max_point)
        return self._cube

    def _cube_rec(self, scene: Scene, transform: mat4, obj: RenderObject, min_point: vec3, max_point: vec3) -> None:
        obj_min, obj_max = scene.model(obj.model).box()
        obj_min = transform * obj_min
        obj_max = transform * obj_max
        min_point.x = min(min_point.x, obj_min.x, obj_max.x)
        min_point.y = min(min_point.y, obj_min.y, obj_max.y)
        min_point.z = min(min_point.z, obj_min.z, obj_max.z)
        max_point.x = max(max_point.x, obj_min.x, obj_max.x)
        max_point.y = max(max_point.y, obj_min.y, obj_max.y)
        max_point.z = max(max_point.z, obj_min.z, obj_max.z)
        for child in obj.children:
            self._cube_rec(scene, transform * child.transform(), child, min_point, max_point)

    def reset_boundary(self) -> None:
        self._boundary = None

    def boundary(self, scene: Scene) -> Boundary | Empty:
        if not self._boundary:
            if self.genBoundary is None:
                self._boundary = Empty(scene)
            else:
                self._boundary = self.genBoundary()
        return self._boundary


class Camera:
    def __init__(self):
        self.x: float = 40.0
        self.y: float = 130.0
        self.z: float = 0.5
        self.pitch: float = math.pi /2
        self.yaw: float = 0.0
        self.fov: float = 90.0
        self.aspect: float = 16 / 9

    def view(self) -> mat4:
        up = vec3(0, 0, 1)
        camera = glm.translate(mat4(), vec3(self.x, self.y, self.z))
        camera = glm.rotate(camera, self.yaw, up)
        pitch = glm.vec3(1, 0, 0)
        camera = glm.rotate(camera, self.pitch, pitch)
        view = glm.inverse(camera)
        return view

    def projection(self) -> mat4:
        return glm.perspective(90, self.aspect, 0.1, 5000)

    def translate(self, translation: vec3) -> None:
        self.x += translation.x
        self.y += translation.y
        self.z += translation.z

    def rotate(self, yaw: float, pitch: float):
        self.pitch += pitch
        self.yaw += yaw

        if self.pitch > math.pi:
            self.pitch = math.pi
        elif self.pitch < 0:
            self.pitch = 0

    def forward(self, ignoreZ: bool = True) -> vec3:
        eye_x = math.sin(self.yaw) * math.sin(self.pitch)
        eye_y = math.cos(self.yaw) * math.sin(self.pitch)
        eye_z = 0 if ignoreZ else math.sin(self.pitch)
        return glm.normalize(vec3(-eye_x, eye_y, eye_z))

    def sideward(self, ignoreZ: bool = True) -> vec3:
        eye_x = math.cos(self.yaw) * math.cos(self.pitch)
        eye_y = math.sin(self.yaw) * math.cos(self.pitch)
        eye_z = 0 if ignoreZ else math.sin(self.pitch)
        return glm.normalize(-vec3(eye_x, eye_y, eye_z))

    def upward(self, ignoreXY: bool = True) -> vec3:
        if not ignoreXY:
            raise NotImplementedError
        eye_y = 0 if ignoreXY else math.cos(self.pitch) * math.sin(self.yaw)
        eye_x = 0 if ignoreXY else math.cos(self.yaw) * math.cos(self.pitch)
        eye_z = 1
        return glm.normalize(vec3(eye_y, eye_x, eye_z))


class FocusedCamera:
    def __init__(self):
        self.x: float = 40.0
        self.y: float = 130.0
        self.z: float = 0.5
        self.pitch: float = math.pi / 2
        self.yaw: float = 0.0
        self.distance: float = 2.0
        self.fov: float = 90.0
        self.aspect: float = 16 / 9

    def view(self) -> mat4:
        eye_x = self.x + math.cos(self.yaw) * math.sin(self.pitch)
        eye_y = self.y + math.sin(self.yaw) * math.sin(self.pitch)
        eye_z = self.z + math.cos(self.pitch)

        eye = vec3(eye_x, eye_y, eye_z)
        centre = vec3(self.x, self.y, self.z)
        return glm.lookAt(eye, centre, vec3(0, 0, 1))

    def projection(self) -> mat4:
        return glm.perspective(90, 16 / 9, 0.1, 5000)

    def translate(self, translation: vec3) -> None:
        self.x += translation.x
        self.y += translation.y
        self.z += translation.z

    def rotate(self, yaw: float, pitch: float):
        self.pitch += pitch
        self.yaw += yaw

        if self.pitch > math.pi - 0.001:
            self.pitch = math.pi - 0.001
        elif self.pitch < 0.001:
            self.pitch = 0.001

    def forward(self, ignoreZ: bool = True) -> vec3:
        eye_x = -math.cos(self.yaw) * math.sin(self.pitch)
        eye_y = -math.sin(self.yaw) * math.sin(self.pitch)
        eye_z = 0 if ignoreZ else math.sin(self.pitch)
        return glm.normalize(vec3(eye_x, eye_y, eye_z))

    def sideward(self, ignoreZ: bool = True) -> vec3:
        eye_x = math.sin(self.yaw) * math.sin(self.pitch)
        eye_y = -math.cos(self.yaw) * math.sin(self.pitch)
        eye_z = 0 if ignoreZ else math.sin(self.pitch)
        return glm.normalize(vec3(eye_x, eye_y, eye_z))

    def upward(self, ignoreXY: bool = True) -> vec3:
        if not ignoreXY:
            raise NotImplementedError
        eye_y = 0 if ignoreXY else math.cos(self.pitch) * math.sin(self.yaw)
        eye_x = 0 if ignoreXY else math.cos(self.yaw) * math.cos(self.pitch)
        eye_z = 1
        return glm.normalize(vec3(eye_y, eye_x, eye_z))
