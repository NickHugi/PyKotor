import math
from typing import Dict, List

import glm
from OpenGL.raw.GL.VERSION.GL_1_0 import glEnable, GL_TEXTURE_2D, GL_DEPTH_TEST, glClearColor, glClear, \
    GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT
from glm import mat4, vec3
from pykotor.common.module import Module
from pykotor.common.stream import BinaryReader
from pykotor.extract.installation import Installation, SearchLocation
from pykotor.resource.type import ResourceType

from pykotor.gl.modelreader import gl_load_mdl
from pykotor.gl.model import Model
from pykotor.gl.shader import Shader, KOTOR_VSHADER, KOTOR_FSHADER, Texture


class Scene:
    def __init__(self, module_root: str, installation: Installation):
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_DEPTH_TEST)

        self.installation: Installation = installation
        self.textures: Dict[str, Texture] = { "NULL": Texture.from_color() }
        self.models: Dict[str, Model] = {}
        self.objects: List[RenderObject] = []

        self.shader: Shader = Shader(KOTOR_VSHADER, KOTOR_FSHADER)
        self.shader.use()

        self.camera: Camera = Camera()

        self.module: Module = Module(module_root, self.installation)
        for room in self.module.layout.resource().rooms:
            model_name = room.model

            mdl = BinaryReader.from_bytes(self.installation.resource(model_name, ResourceType.MDL).data, 12)
            mdx = BinaryReader.from_bytes(self.installation.resource(model_name, ResourceType.MDX).data)
            self.models[room.model] = gl_load_mdl(self, mdl, mdx)

            position = vec3(room.position.x, room.position.y, room.position.z)
            self.objects.append(RenderObject(room.model, position))

    def render(self) -> None:
        glClearColor(0.5, 0.5, 1, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.shader.set_matrix4("view", self.camera.view())
        self.shader.set_matrix4("projection", self.camera.projection())

        for obj in self.objects:
            transform = mat4()
            transform = glm.translate(transform, obj.position)

            model = self.models[obj.model]
            model.draw(self.shader, transform)

    def texture(self, name: str) -> Texture:
        if name not in self.textures:
            tpc = self.installation.texture(name, [SearchLocation.OVERRIDE, SearchLocation.TEXTURES_TPA, SearchLocation.CHITIN])
            self.textures[name] = Texture.from_tpc(tpc) if tpc is not None else Texture.from_color(255, 255, 255)
        return self.textures[name]


class RenderObject:
    def __init__(self, model: str, position: vec3):
        self.model: str = model
        self.position: vec3 = position


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

