from __future__ import annotations

import math
import random
from copy import copy
from typing import Dict, List, Any, Optional

import glm
from OpenGL.GL import glReadPixels
from OpenGL.raw.GL.VERSION.GL_1_0 import glEnable, GL_TEXTURE_2D, GL_DEPTH_TEST, glClearColor, glClear, \
    GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_RGBA, GL_BLEND, glBlendFunc, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, \
    glDisable
from OpenGL.raw.GL.VERSION.GL_1_2 import GL_UNSIGNED_INT_8_8_8_8, GL_BGRA
from glm import mat4, vec3, quat, vec4
from pykotor.common.module import Module
from pykotor.common.stream import BinaryReader
from pykotor.extract.installation import Installation, SearchLocation
from pykotor.resource.formats.twoda import load_2da
from pykotor.resource.type import ResourceType

from pykotor.gl.shader import Shader, KOTOR_VSHADER, KOTOR_FSHADER, Texture, PICKER_FSHADER, PICKER_VSHADER, \
    SELECT_VSHADER, SELECT_FSHADER
from pykotor.gl.modelreader import gl_load_mdl
from pykotor.gl.model import Model, Cube


SEARCH_ORDER_2DA = [SearchLocation.CHITIN]
SEARCH_ORDER = [SearchLocation.OVERRIDE, SearchLocation.CHITIN]


class Scene:
    def __init__(self, module_root: str, installation: Installation):
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_DEPTH_TEST)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.installation: Installation = installation
        self.textures: Dict[str, Texture] = { "NULL": Texture.from_color() }
        self.models: Dict[str, Model] = {}
        self.objects: List[RenderObject] = []
        self.selection: List[RenderObject] = []

        self.picker_shader: Shader = Shader(PICKER_VSHADER, PICKER_FSHADER)
        self.select_shader: Shader = Shader(SELECT_VSHADER, SELECT_FSHADER)
        self.shader: Shader = Shader(KOTOR_VSHADER, KOTOR_FSHADER)

        self.camera: Camera = Camera()

        self.table_doors = load_2da(installation.resource("genericdoors", ResourceType.TwoDA, SEARCH_ORDER_2DA).data)
        self.table_placeables = load_2da(installation.resource("placeables", ResourceType.TwoDA, SEARCH_ORDER_2DA).data)
        self.table_creatures = load_2da(installation.resource("appearance", ResourceType.TwoDA, SEARCH_ORDER_2DA).data)
        self.table_heads = load_2da(installation.resource("heads", ResourceType.TwoDA, SEARCH_ORDER_2DA).data)

        self.module: Module = Module(module_root, self.installation)
        for room in self.module.layout.resource().rooms:
            position = vec3(room.position.x, room.position.y, room.position.z)
            self.objects.append(RenderObject(room.model, position, data=room))

        for door in self.module.dynamic.resource().doors:
            utd = self.module.doors[door.resref.get()].resource()
            model_name = self.table_doors.get_row(utd.appearance_id).get_string("modelname")
            position = vec3(door.position.x, door.position.y, door.position.z)
            rotation = vec3(0, 0, door.bearing)
            self.objects.append(RenderObject(model_name, position, rotation, data=door))

        for placeable in self.module.dynamic.resource().placeables:
            utp = self.module.placeables[placeable.resref.get()].resource()
            model_name = self.table_placeables.get_row(utp.appearance_id).get_string("modelname")
            position = vec3(placeable.position.x, placeable.position.y, placeable.position.z)
            rotation = vec3(0, 0, placeable.bearing)
            self.objects.append(RenderObject(model_name, position, rotation, data=placeable))

        for creature in self.module.dynamic.resource().creatures:
            utc = self.module.creatures[creature.resref.get()].resource()
            position = vec3(creature.position.x, creature.position.y, creature.position.z)
            rotation = vec3(0, 0, creature.bearing)
            body_model = self.table_creatures.get_row(utc.appearance_id).get_string("race")

            obj = RenderObject(body_model, position, rotation, data=creature)
            self.objects.append(obj)

            head_str = self.table_creatures.get_row(utc.appearance_id).get_string("normalhead")
            if head_str:
                head_id = int(head_str)
                head_model = self.table_heads.get_row(head_id).get_string("head")
                head_obj = RenderObject(head_model)
                head_obj.set_transform(self.model(body_model).find("headhook").global_transform())
                obj.children.append(head_obj)

    def render(self) -> None:
        glClearColor(0.5, 0.5, 1, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glDisable(GL_BLEND)
        self.shader.use()
        self.shader.set_matrix4("view", self.camera.view())
        self.shader.set_matrix4("projection", self.camera.projection())
        for obj in self.objects:
            self._render_object(obj, mat4())

        self.select_shader.use()
        self.select_shader.set_matrix4("view", self.camera.view())
        self.select_shader.set_matrix4("projection", self.camera.projection())
        glEnable(GL_BLEND)
        for obj in self.selection:
            transform = glm.translate(mat4(), obj.position())
            transform = transform * glm.mat4_cast(quat(obj.rotation()))
            obj.cube(self).draw(self.select_shader, transform)

    def _render_object(self, obj: RenderObject, transform: mat4) -> None:
        model = self.model(obj.model)
        model.draw(self.shader, transform * obj.transform())
        for child in obj.children:
            self._render_object(child, obj.transform())

    def picker_render(self) -> None:
        self.picker_shader.use()

        glClearColor(1.0, 1.0, 1, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.picker_shader.set_matrix4("view", self.camera.view())
        self.picker_shader.set_matrix4("projection", self.camera.projection())

        for obj in self.objects:
            int_rgb = self.objects.index(obj)
            r = int_rgb & 0xFF
            g = (int_rgb >> 8) & 0xFF
            b = (int_rgb >> 16) & 0xFF
            color = vec3(r/255, g/255, b/255)
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
        self.render()  # Stop screen from blinking when picking
        return self.objects[pixel] if pixel != 0xFFFFFF else None

    def select(self, obj: RenderObject, clear_existing: bool = True):
        if clear_existing:
            self.selection.clear()
        self.selection.append(obj)

    def texture(self, name: str) -> Texture:
        if name not in self.textures:
            tpc = self.installation.texture(name, [SearchLocation.OVERRIDE, SearchLocation.TEXTURES_TPA, SearchLocation.CHITIN])
            self.textures[name] = Texture.from_tpc(tpc) if tpc is not None else Texture.from_color(255, 255, 255)
        return self.textures[name]

    def model(self, name: str) -> Model:
        if name not in self.models:
            mdl_data = self.installation.resource(name, ResourceType.MDL, SEARCH_ORDER).data
            mdx_data = self.installation.resource(name, ResourceType.MDX, SEARCH_ORDER).data
            model = gl_load_mdl(self, BinaryReader.from_bytes(mdl_data, 12), BinaryReader.from_bytes(mdx_data))
            self.models[name] = model
        return self.models[name]


class RenderObject:
    def __init__(self, model: str, position: vec3 = None, rotation: vec3 = None, *, data=None):
        self.model: str = model
        self.children: List[RenderObject] = []
        self._transform: mat4 = mat4()
        self._position: vec3 = position if position is not None else vec3()
        self._rotation: vec3 = rotation if rotation is not None else vec3()
        self._cube: Optional[Cube] = None
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
        self._position = vec3(x, y, z)
        self._recalc_transform()

    def rotation(self) -> vec3:
        return copy(self._rotation)

    def set_rotation(self, x: float, y: float, z: float) -> None:
        self._rotation = glm.quat()
        self._recalc_transform()

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


class Camera:
    def __init__(self):
        self.x: float = 40.0
        self.y: float = 130.0
        self.z: float = 0.5
        self.pitch: float = 0.0
        self.yaw: float = 0.0
        self.fov: float = 90.0
        self.aspect: float = 16/9

    def view(self) -> mat4:
        forward = self.forward()
        eye = vec3(self.x - forward.x, self.y - forward.y, self.z - forward.z)
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

    def forward(self) -> vec3:
        eye_x = math.cos(self.pitch) * math.sin(self.yaw)
        eye_y = math.cos(self.yaw) * math.cos(self.pitch)
        eye_z = math.sin(self.pitch)
        return vec3(eye_x, eye_y, eye_z)

    def sideward(self) -> vec3:
        eye_y = math.cos(self.pitch) * math.sin(self.yaw)
        eye_x = math.cos(self.yaw) * math.cos(self.pitch)
        eye_z = math.sin(self.pitch)
        return vec3(eye_x, -eye_y, -eye_z)

    def upward(self) -> vec3:
        eye_y = math.cos(self.pitch) * math.sin(self.yaw)
        eye_x = math.cos(self.yaw) * math.cos(self.pitch)
        eye_z = math.sin(self.pitch)
        return vec3(0, 0, 1)

