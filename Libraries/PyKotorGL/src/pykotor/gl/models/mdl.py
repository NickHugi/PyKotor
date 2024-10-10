from __future__ import annotations

import ctypes
import math
import struct

from copy import copy
from typing import TYPE_CHECKING

import glm
import numpy as np

from OpenGL.GL import glGenBuffers, glGenVertexArrays, glVertexAttribPointer
from OpenGL.GL.shaders import GL_FALSE
from OpenGL.raw.GL.ARB.tessellation_shader import GL_TRIANGLES
from OpenGL.raw.GL.ARB.vertex_shader import GL_FLOAT
from OpenGL.raw.GL.VERSION.GL_1_0 import GL_UNSIGNED_SHORT
from OpenGL.raw.GL.VERSION.GL_1_1 import glDrawElements
from OpenGL.raw.GL.VERSION.GL_1_3 import GL_TEXTURE0, GL_TEXTURE1, glActiveTexture
from OpenGL.raw.GL.VERSION.GL_1_5 import GL_ARRAY_BUFFER, GL_ELEMENT_ARRAY_BUFFER, GL_STATIC_DRAW, glBindBuffer, glBufferData
from OpenGL.raw.GL.VERSION.GL_2_0 import glEnableVertexAttribArray
from OpenGL.raw.GL.VERSION.GL_3_0 import glBindVertexArray
from glm import mat4, quat, vec3, vec4

from pykotor.common.geometry import Vector3

if TYPE_CHECKING:
    from _testbuffer import ndarray

    from pykotor.gl.scene import Scene
    from pykotor.gl.shader import Shader


from panda3d.core import NodePath, Geom, GeomNode, GeomVertexData, GeomVertexFormat, GeomVertexWriter, GeomTriangles

class Model:
    def __init__(self, scene: Scene, root: Node):
        self._scene: Scene = scene
        self.root: Node = root
        self.node_path: NodePath = scene.render.attachNewNode("model")

    def draw(
        self,
        shader: Shader,
        transform: mat4,
        *,
        override_texture: str | None = None,
    ):
        self.node_path.setMat(transform)
        self.root.draw(shader, mat4(), override_texture)

    def find(self, name: str) -> Node | None:
        return self.root.find(name)

    def all(self) -> list[Node]:
        return self.root.all()

    def box(self) -> tuple[vec3, vec3]:
        min_point = vec3(100000, 100000, 100000)
        max_point = vec3(-100000, -100000, -100000)
        self._box_rec(self.root, mat4(), min_point, max_point)

        min_point -= vec3(0.1, 0.1, 0.1)
        max_point += vec3(0.1, 0.1, 0.1)

        return min_point, max_point

    def _box_rec(
        self,
        node: Node,
        transform: mat4,
        min_point: vec3,
        max_point: vec3,
    ):
        transform = transform * glm.translate(node._position) * glm.mat4_cast(node._rotation)  # noqa: SLF001

        if node.mesh and node.render:
            vertex_count = len(node.mesh.vertex_data) // node.mesh.mdx_size
            for i in range(vertex_count):
                index = i * node.mesh.mdx_size + node.mesh.mdx_vertex
                data = node.mesh.vertex_data[index : index + 12]
                x, y, z = struct.unpack("fff", data)
                position = transform * vec3(x, y, z)
                min_point = glm.min(min_point, position)
                max_point = glm.max(max_point, position)

        for child in node.children:
            self._box_rec(child, transform, min_point, max_point)


from panda3d.core import NodePath

class Node:
    def __init__(
        self,
        scene: Scene,
        parent: Node | None,
        name: str,
    ):
        self._scene: Scene = scene
        self._parent: Node | None = parent
        self.name: str = name
        self._transform: mat4 = mat4()
        self._position: vec3 = glm.vec3()
        self._rotation: quat = glm.quat()
        self.children: list[Node] = []
        self.render: bool = True
        self.mesh: Mesh | None = None

        self.node_path: NodePath = (parent.node_path if parent else scene.render).attachNewNode(name)
        self._recalc_transform()

    def root(self) -> Node | None:
        return self if self._parent is None else self._parent.root()

    def ancestors(self) -> list[Node]:
        return [] if self._parent is None else [*self._parent.ancestors(), self._parent]

    def global_position(self) -> vec3:
        return vec3(*self.node_path.getPos())

    def global_rotation(self) -> quat:
        return quat(*self.node_path.getQuat())

    def global_transform(self) -> mat4:
        return mat4(*self.node_path.getMat())

    def transform(self) -> mat4:
        return copy(self._transform)

    def _recalc_transform(self):
        self._transform = glm.translate(self._position) * glm.mat4_cast(quat(self._rotation))
        self.node_path.setMat(self._transform)

    def position(self) -> vec3:
        return copy(self._position)

    def set_position(self, x: float, y: float, z: float):
        self._position = vec3(x, y, z)
        self._recalc_transform()

    def rotation(self) -> quat:
        return copy(self._rotation)

    def set_rotation(
        self,
        pitch: float,
        yaw: float,
        roll: float,
    ):
        self._rotation = quat(vec3(pitch, yaw, roll))
        self._recalc_transform()

    def draw(
        self,
        shader: Shader,
        transform: mat4,
        override_texture: str | None = None,
    ):
        if self.mesh and self.render:
            self.mesh.draw(shader, transform, override_texture)

        for child in self.children:
            child.draw(shader, transform, override_texture=override_texture)

    def find(self, name: str) -> Node | None:
        if self.name.lower() == name.lower():
            return self
        for child in self.children:
            found = child.find(name)
            if found:
                return found
        return None

    def all(self) -> list[Node]:
        return [self] + [node for child in self.children for node in child.all()]


from panda3d.core import Geom, GeomNode, GeomVertexData, GeomVertexFormat, GeomVertexWriter, GeomTriangles, NodePath

class Mesh:
    def __init__(
        self,
        scene: Scene,
        node: Node,
        texture: str,
        lightmap: str,
        vertex_data: bytearray,
        element_data: bytearray,
        block_size: int,
        data_bitflags: int,
        vertex_offset: int,
        normal_offset: int,
        texture_offset: int,
        lightmap_offset: int,
    ):
        self._scene: Scene = scene
        self._node: Node = node

        self.texture: str = "NULL"
        self.lightmap: str = "NULL"

        self.vertex_data = vertex_data
        self.mdx_size = block_size
        self.mdx_vertex = vertex_offset

        format = GeomVertexFormat.getV3n3t2()
        vdata = GeomVertexData("mesh", format, Geom.UHStatic)
        vertex = GeomVertexWriter(vdata, "vertex")
        normal = GeomVertexWriter(vdata, "normal")
        texcoord = GeomVertexWriter(vdata, "texcoord")

        vertex_count = len(vertex_data) // block_size
        for i in range(vertex_count):
            index = i * block_size
            vertex.addData3f(*struct.unpack_from("fff", vertex_data, index + vertex_offset))
            if normal_offset != -1:
                normal.addData3f(*struct.unpack_from("fff", vertex_data, index + normal_offset))
            if texture_offset != -1:
                texcoord.addData2f(*struct.unpack_from("ff", vertex_data, index + texture_offset))

        prim = GeomTriangles(Geom.UHStatic)
        prim.setIndexType(Geom.NTUint16)
        prim.addConsecutiveVertices(0, vertex_count)
        prim.addData1i(0)

        geom = Geom(vdata)
        geom.addPrimitive(prim)

        node = GeomNode("mesh")
        node.addGeom(geom)

        self.node_path = NodePath(node)
        self.node_path.reparentTo(self._node.node_path)

        if data_bitflags & 0x0020 and texture and texture != "NULL":
            self.texture = texture

        if data_bitflags & 0x0004 and lightmap and lightmap != "NULL":
            self.lightmap = lightmap

    def draw(
        self,
        shader: Shader,
        transform: mat4,
        override_texture: str | None = None,
    ):
        self.node_path.setMat(transform)
        texture = self._scene.load_texture(override_texture or self.texture)
        lightmap = self._scene.load_texture(self.lightmap, is_lightmap=True)
        
        if texture:
            self.node_path.setTexture(texture, 0)
        if lightmap:
            self.node_path.setTexture(lightmap, 1)


class Cube:
    def __init__(
        self,
        scene: Scene,
        min_point: vec3 | None = None,
        max_point: vec3 | None = None,
    ):
        self._scene = scene

        min_point = vec3(-1.0, -1.0, -1.0) if min_point is None else min_point
        max_point = vec3(1.0, 1.0, 1.0) if max_point is None else max_point

        vertices = np.array(
            [
                min_point.x, min_point.y, max_point.z,
                max_point.x, min_point.y, max_point.z,
                max_point.x, max_point.y, max_point.z,
                min_point.x, max_point.y, max_point.z,
                min_point.x, min_point.y, min_point.z,
                max_point.x, min_point.y, min_point.z,
                max_point.x, max_point.y, min_point.z,
                min_point.x, max_point.y, min_point.z
            ],
            dtype="float32",
        )

        elements = np.array(
            [0, 1, 2, 2, 3, 0, 1, 5, 6, 6, 2, 1, 7, 6, 5, 5, 4, 7, 4, 0, 3, 3, 7, 4, 4, 5, 1, 1, 0, 4, 3, 2, 6, 6, 7, 3],
            dtype="int16",
        )

        self.min_point: vec3 = min_point
        self.max_point: vec3 = max_point

        self._vao = glGenVertexArrays(1)
        self._vbo = glGenBuffers(1)
        self._ebo = glGenBuffers(1)
        glBindVertexArray(self._vao)

        glBindBuffer(GL_ARRAY_BUFFER, self._vbo)
        glBufferData(GL_ARRAY_BUFFER, len(vertices) * 4, vertices, GL_STATIC_DRAW)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self._ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(elements) * 4, elements, GL_STATIC_DRAW)
        self._face_count: int = len(elements)

        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 12, ctypes.c_void_p(0))

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def draw(self, shader: Shader, transform: mat4):
        shader.set_matrix4("model", transform)
        glBindVertexArray(self._vao)
        glDrawElements(GL_TRIANGLES, self._face_count, GL_UNSIGNED_SHORT, None)


class Boundary:
    def __init__(
        self,
        scene: Scene,
        vertices: list[Vector3],
    ):
        self._scene: Scene = scene

        vertices, elements = self._build_nd(vertices)

        self._vao = glGenVertexArrays(1)
        self._vbo = glGenBuffers(1)
        self._ebo = glGenBuffers(1)
        glBindVertexArray(self._vao)

        glBindBuffer(GL_ARRAY_BUFFER, self._vbo)
        glBufferData(GL_ARRAY_BUFFER, len(vertices) * 4, vertices, GL_STATIC_DRAW)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self._ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(elements) * 4, elements, GL_STATIC_DRAW)
        self._face_count: int = len(elements)

        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 12, ctypes.c_void_p(0))

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    @classmethod
    def from_circle(
        cls,
        scene: Scene,
        radius: float,
        smoothness: int = 10,
    ) -> Boundary:
        vertices: list[Vector3] = []
        for i in range(smoothness):
            x = math.cos(i / smoothness * math.pi / 2)
            y = math.sin(i / smoothness * math.pi / 2)
            vertices.append(Vector3(x, y, 0) * radius)
        for i in range(smoothness):
            x = math.cos(i / smoothness * math.pi / 2 + math.pi / 2)
            y = math.sin(i / smoothness * math.pi / 2 + math.pi / 2)
            vertices.append(Vector3(x, y, 0) * radius)
        for i in range(smoothness):
            x = math.cos(i / smoothness * math.pi / 2 + math.pi / 2 * 2)
            y = math.sin(i / smoothness * math.pi / 2 + math.pi / 2 * 2)
            vertices.append(Vector3(x, y, 0) * radius)
        for i in range(smoothness):
            x = math.cos(i / smoothness * math.pi / 2 + math.pi / 2 * 3)
            y = math.sin(i / smoothness * math.pi / 2 + math.pi / 2 * 3)
            vertices.append(Vector3(x, y, 0) * radius)
        return Boundary(scene, vertices)

    def draw(self, shader: Shader, transform: mat4):
        shader.set_matrix4("model", transform)
        glBindVertexArray(self._vao)
        glDrawElements(GL_TRIANGLES, self._face_count, GL_UNSIGNED_SHORT, None)

    def _build_nd(self, vertices: list[Vector3]) -> tuple[ndarray, ndarray]:
        npvertices = []
        for vertex in vertices:
            npvertices.extend([*vertex, *Vector3(vertex.x, vertex.y, vertex.z + 2)])

        npfaces: list[int] = []
        count = len(vertices) * 2
        for i, _vertex in enumerate(vertices):
            index1 = i * 2
            index2 = i * 2 + 2 if i * 2 + 2 < count else 0
            index3 = i * 2 + 1
            index4 = (i * 2 + 2) + 1 if (i * 2 + 2) + 1 < count else 1
            npfaces.extend([index1, index2, index3, index2, index4, index3])
        return np.array(npvertices, dtype="float32"), np.array(npfaces, dtype="int16")


class Empty:
    def __init__(self, scene: Scene):
        self._scene: Scene = scene

    def draw(self, shader: Shader, transform: mat4): ...
