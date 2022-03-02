from __future__ import annotations

import ctypes
import struct
from copy import copy
from typing import Optional, List, Tuple

import glm
import numpy
from OpenGL.GL import glVertexAttribPointer, glGenVertexArrays, glGenBuffers
from OpenGL.GL.shaders import GL_FALSE
from OpenGL.raw.GL.ARB.internalformat_query2 import GL_TEXTURE_2D
from OpenGL.raw.GL.ARB.tessellation_shader import GL_TRIANGLES
from OpenGL.raw.GL.ARB.vertex_shader import GL_FLOAT
from OpenGL.raw.GL.VERSION.GL_1_0 import GL_UNSIGNED_SHORT
from OpenGL.raw.GL.VERSION.GL_1_1 import glBindTexture, glDrawElements
from OpenGL.raw.GL.VERSION.GL_1_3 import glActiveTexture, GL_TEXTURE0, GL_TEXTURE1
from OpenGL.raw.GL.VERSION.GL_1_5 import GL_ARRAY_BUFFER, glBindBuffer, glBufferData, GL_ELEMENT_ARRAY_BUFFER, \
    GL_STATIC_DRAW
from OpenGL.raw.GL.VERSION.GL_2_0 import glEnableVertexAttribArray
from OpenGL.raw.GL.VERSION.GL_3_0 import glBindVertexArray
from glm import mat4, vec3, quat, vec4

from pykotor.gl.shader import Texture, Shader
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pykotor.gl.scene import Scene


class Model:
    def __init__(self, scene: Scene, root: Node):
        self._scene: Scene = scene
        self.root: Node = root

    def draw(self, shader: Shader, transform: mat4):
        self.root.draw(shader, transform)

    def find(self, name: str) -> Optional[Node]:
        nodes = [self.root]
        while nodes:
            node = nodes.pop()
            if node.name == name:
                return node
            nodes.extend(node.children)
        return None

    def all(self) -> List[Node]:
        all_nodes = []
        search = [self.root]
        while search:
            node = search.pop()
            search.extend(node.children)
            all_nodes.append(node)
        return all_nodes

    def box(self) -> Tuple[vec3, vec3]:
        min_point = vec3(100000, 100000, 100000)
        max_point = vec3(-100000, -100000, -100000)
        self._box_rec(self.root, mat4(), min_point, max_point)

        min_point.x -= 0.1
        min_point.y -= 0.1
        min_point.z -= 0.1
        max_point.x += 0.1
        max_point.y += 0.1
        max_point.z += 0.1

        return min_point, max_point

    def _box_rec(self, node: Node, transform: mat4, min_point: vec3, max_point: vec3) -> None:
        transform = glm.translate(transform, node._position)
        transform = transform * glm.mat4_cast(node._rotation)

        if node.mesh and node.render:
            vertex_count = len(node.mesh.vertex_data) // node.mesh.mdx_size
            for i in range(vertex_count):
                index = i * node.mesh.mdx_size + node.mesh.mdx_vertex
                data = node.mesh.vertex_data[index:index+12]
                x, y, z = struct.unpack("fff", data)
                position = transform * vec3(x, y, z)
                min_point.x = min(min_point.x, position.x)
                min_point.y = min(min_point.y, position.y)
                min_point.z = min(min_point.z, position.z)
                max_point.x = max(max_point.x, position.x)
                max_point.y = max(max_point.y, position.y)
                max_point.z = max(max_point.z, position.z)

        for child in node.children:
            self._box_rec(child, transform, min_point, max_point)


class Node:
    def __init__(self, scene: Scene, parent: Optional[Node], name: str):
        self._scene: Scene = scene
        self._parent: Optional[Node] = parent
        self.name: str = name
        self._transform: mat4 = mat4()
        self._position: vec3 = glm.vec3()
        self._rotation: quat = glm.quat()
        self.children: List[Node] = []
        self.render: bool = True
        self.mesh: Optional[Mesh] = None

        self._recalc_transform()

    def root(self) -> Node:
        ancestor = self._parent
        while ancestor:
            ancestor = ancestor._parent
        return ancestor

    def ancestors(self) -> List[Node]:
        ancestors = []
        ancestor = self._parent
        while ancestor:
            ancestors.append(ancestor)
            ancestor = ancestor._parent
        return list(reversed(ancestors))

    def global_position(self) -> vec3:
        ancestors = self.ancestors() + [self]
        transform = mat4()
        for ancestor in ancestors:
            transform = glm.translate(transform, ancestor._position)
            transform = transform * glm.mat4_cast(ancestor._rotation)
        position = vec3()
        glm.decompose(transform, vec3(), quat(), position, vec3(), vec4())
        return position

    def global_rotation(self) -> quat:
        ancestors = self.ancestors() + [self]
        transform = mat4()
        for ancestor in ancestors:
            transform = glm.translate(transform, ancestor._position)
            transform = transform * glm.mat4_cast(ancestor._rotation)
        rotation = quat()
        glm.decompose(transform, vec3(), rotation, vec3(), vec3(), vec4())
        return rotation

    def global_transform(self) -> mat4:
        ancestors = self.ancestors() + [self]
        transform = mat4()
        for ancestor in ancestors:
            transform = glm.translate(transform, ancestor._position)
            transform = transform * glm.mat4_cast(ancestor._rotation)
        return transform

    def transform(self) -> mat4:
        return copy(self._transform)

    def _recalc_transform(self) -> None:
        self._transform = glm.translate(mat4(), self._position)
        self._transform = self._transform * glm.mat4_cast(quat(self._rotation))

    def position(self) -> vec3:
        return copy(self._position)

    def set_position(self, x: float, y: float, z: float) -> None:
        self._position = vec3(x, y, z)
        self._recalc_transform()

    def rotation(self) -> quat:
        return copy(self._rotation)

    def set_rotation(self, pitch: float, yaw: float, roll: float) -> None:
        self._rotation = quat(vec3(pitch, yaw, roll))
        self._recalc_transform()

    def draw(self, shader: Shader, transform: mat4):
        transform = transform * self._transform

        if self.mesh and self.render:
            self.mesh.draw(shader, transform)

        for child in self.children:
            child.draw(shader, transform)


class Mesh:
    def __init__(self, scene, node, texture, lightmap, vertex_data, element_data, block_size, data_bitflags, vertex_offset,
                 normal_offset, texture_offset, lightmap_offset):
        self._scene: Scene = scene
        self._node: Node = node

        self.texture: str = "NULL"
        self.lightmap: str = "NULL"

        self.vertex_data = vertex_data
        self.mdx_size = block_size
        self.mdx_vertex = vertex_offset

        self._vao = glGenVertexArrays(1)
        self._vbo = glGenBuffers(1)
        self._ebo = glGenBuffers(1)
        glBindVertexArray(self._vao)

        glBindBuffer(GL_ARRAY_BUFFER, self._vbo)
        glBufferData(GL_ARRAY_BUFFER, len(vertex_data), vertex_data, GL_STATIC_DRAW)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self._ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(element_data), element_data, GL_STATIC_DRAW)
        self._face_count = len(element_data) // 2

        if data_bitflags & 0x0001:
            glEnableVertexAttribArray(1)
            glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, block_size, ctypes.c_void_p(vertex_offset))

        if data_bitflags & 0x0020 and texture != "" and texture != "NULL":
            glEnableVertexAttribArray(3)
            glVertexAttribPointer(3, 2, GL_FLOAT, GL_FALSE, block_size, ctypes.c_void_p(texture_offset))
            self.texture = texture

        if data_bitflags & 0x0004 and lightmap != "" and lightmap != "NULL":
            glEnableVertexAttribArray(4)
            glVertexAttribPointer(4, 2, GL_FLOAT, GL_FALSE, block_size, ctypes.c_void_p(lightmap_offset))
            self.lightmap = lightmap

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def draw(self, shader: Shader, transform: mat4):
        shader.set_matrix4("model", transform)

        glActiveTexture(GL_TEXTURE0)
        self._scene.texture(self.texture).use()

        glActiveTexture(GL_TEXTURE1)
        self._scene.texture(self.lightmap).use()

        glBindVertexArray(self._vao)
        glDrawElements(GL_TRIANGLES, self._face_count, GL_UNSIGNED_SHORT, None)


class Cube:
    def __init__(self, scene: Scene, min_point: vec3 = None, max_point: vec3 = None):
        self._scene = scene

        min_point = vec3(-1.0, -1.0, -1.0) if min_point is None else min_point
        max_point = vec3(1.0, 1.0, 1.0) if max_point is None else max_point

        vertices = numpy.array([
            min_point.x, min_point.y, max_point.z,
            max_point.x, min_point.y, max_point.z,
            max_point.x, max_point.y, max_point.z,
            min_point.x, max_point.y, max_point.z,
            min_point.x, min_point.y, min_point.z,
            max_point.x, min_point.y, min_point.z,
            max_point.x, max_point.y, min_point.z,
            min_point.x, max_point.y, min_point.z
        ], dtype='float32')

        elements = numpy.array([
            0, 1, 2,
            2, 3, 0,
            1, 5, 6,
            6, 2, 1,
            7, 6, 5,
            5, 4, 7,
            4, 0, 3,
            3, 7, 4,
            4, 5, 1,
            1, 0, 4,
            3, 2, 6,
            6, 7, 3
        ], dtype='int16')

        self._vao = glGenVertexArrays(1)
        self._vbo = glGenBuffers(1)
        self._ebo = glGenBuffers(1)
        glBindVertexArray(self._vao)

        glBindBuffer(GL_ARRAY_BUFFER, self._vbo)
        glBufferData(GL_ARRAY_BUFFER, len(vertices)*4, vertices, GL_STATIC_DRAW)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self._ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(elements)*4, elements, GL_STATIC_DRAW)
        self._face_count = len(elements)

        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 12, ctypes.c_void_p(0))

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def draw(self, shader: Shader, transform: mat4):
        shader.set_matrix4("model", transform)
        glBindVertexArray(self._vao)
        glDrawElements(GL_TRIANGLES, self._face_count, GL_UNSIGNED_SHORT, None)
