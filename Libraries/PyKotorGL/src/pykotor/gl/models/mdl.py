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


class Model:
    def __init__(self, scene: Scene, root: Node):
        self._scene: Scene = scene
        self.root: Node = root

    def draw(self, shader: Shader, transform: mat4, *, override_texture: str | None = None):
        self.root.draw(shader, transform, override_texture)

    def find(self, name: str) -> Node | None:
        nodes: list[Node] = [self.root]
        while nodes:
            node: Node = nodes.pop()
            if node.name.lower() == name.lower():
                return node
            nodes.extend(node.children)
        return None

    def all(self) -> list[Node]:
        all_nodes: list[Node] = []
        search: list[Node] = [self.root]
        while search:
            node: Node = search.pop()
            search.extend(node.children)
            all_nodes.append(node)
        return all_nodes

    def box(self) -> tuple[vec3, vec3]:
        """Calculates bounding box of the scene.

        Args:
        ----
            self: {Node to calculate bounding box for}.

        Returns:
        -------
            tuple[vec3, vec3]: {Minimum and maximum points of bounding box}

        Processing Logic:
        ----------------
            - Initialize minimum and maximum points to extreme values
            - Recursively calculate bounding box of each child node
            - Expand bounding box by 0.1 units in each direction
            - Return minimum and maximum points of final bounding box.
        """
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

    def _box_rec(self, node: Node, transform: mat4, min_point: vec3, max_point: vec3):
        """Calculates bounding box of node and its children recursively.

        Call the 'box' function to get started here, don't call this directly.

        Args:
        ----
            node: {Node object whose bounding box is calculated}
            transform: {Transformation matrix to apply on node}
            min_point: {vec3 to store minimum point of bounding box}
            max_point: {vec3 to store maximum point of bounding box}.

        Processing Logic:
        ----------------
            - Apply transformation on node position and rotation
            - Iterate through vertices of node mesh if present
            - Transform vertices and update bounding box points
            - Recursively call function for each child node.
        """
        transform = transform * glm.translate(node._position)
        transform = transform * glm.mat4_cast(node._rotation)

        if node.mesh and node.render:
            vertex_count = len(node.mesh.vertex_data) // node.mesh.mdx_size
            for i in range(vertex_count):
                index = i * node.mesh.mdx_size + node.mesh.mdx_vertex
                data = node.mesh.vertex_data[index : index + 12]
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
    def __init__(self, scene: Scene, parent: Node | None, name: str):
        self._scene: Scene = scene
        self._parent: Node | None = parent
        self.name: str = name
        self._transform: mat4 = mat4()
        self._position: vec3 = glm.vec3()
        self._rotation: quat = glm.quat()
        self.children: list[Node] = []
        self.render: bool = True
        self.mesh: Mesh | None = None

        self._recalc_transform()

    def root(self) -> Node:
        ancestor: Node | None = self._parent
        while ancestor:
            ancestor = ancestor._parent
        return ancestor

    def ancestors(self) -> list[Node]:
        ancestors: list[Node] = []
        ancestor: Node | None = self._parent
        while ancestor:
            ancestors.append(ancestor)
            ancestor = ancestor._parent
        return list(reversed(ancestors))

    def global_position(self) -> vec3:  # sourcery skip: class-extract-method
        ancestors: list[Node] = [*self.ancestors(), self]
        transform = mat4()
        for ancestor in ancestors:
            transform = transform * glm.translate(ancestor._position)
            transform = transform * glm.mat4_cast(ancestor._rotation)
        position = vec3()
        glm.decompose(transform, vec3(), quat(), position, vec3(), vec4())
        return position

    def global_rotation(self) -> quat:
        ancestors: list[Node] = [*self.ancestors(), self]
        transform = mat4()
        for ancestor in ancestors:
            transform = transform * glm.translate(ancestor._position)
            transform = transform * glm.mat4_cast(ancestor._rotation)
        rotation = quat()
        glm.decompose(transform, vec3(), rotation, vec3(), vec3(), vec4())
        return rotation

    def global_transform(self) -> mat4:
        ancestors: list[Node] = [*self.ancestors(), self]
        transform = mat4()
        for ancestor in ancestors:
            transform = transform * glm.translate(ancestor._position)
            transform = transform * glm.mat4_cast(ancestor._rotation)
        return transform

    def transform(self) -> mat4:
        return copy(self._transform)

    def _recalc_transform(self):
        self._transform = glm.translate(self._position) * glm.mat4_cast(quat(self._rotation))

    def position(self) -> vec3:
        return copy(self._position)

    def set_position(self, x: float, y: float, z: float):
        self._position = vec3(x, y, z)
        self._recalc_transform()

    def rotation(self) -> quat:
        return copy(self._rotation)

    def set_rotation(self, pitch: float, yaw: float, roll: float):
        self._rotation = quat(vec3(pitch, yaw, roll))
        self._recalc_transform()

    def draw(self, shader: Shader, transform: mat4, override_texture: str | None = None):
        # TODO: use multi-threading to accumulate texture data, then draw all at once.
        transform = transform * self._transform

        if self.mesh and self.render:
            self.mesh.draw(shader, transform, override_texture)

        for child in self.children:
            child.draw(shader, transform, override_texture=override_texture)


class Mesh:
    def __init__(
        self,
        scene: Scene,
        node: Node,
        texture: str,
        lightmap: str,
        vertex_data: memoryview,
        element_data: memoryview,
        block_size: int,
        data_bitflags: int,
        vertex_offset: int,
        normal_offset: int,
        texture_offset: int,
        lightmap_offset: int,
    ):
        """Initializes a Mesh object.

        Args:
        ----
            scene: Scene - The scene object
            node: Node - The node object
            texture: str - The texture path
            lightmap: str - The lightmap path
            vertex_data: list - The vertex data
            element_data: list - The element data
            block_size: int - The block size
            data_bitflags: int - The data bitflags
            vertex_offset: int - The vertex offset
            normal_offset: int - The normal offset
            texture_offset: int - The texture offset
            lightmap_offset: int - The lightmap offset

        Processing Logic:
        ----------------
            - Generates VAO and VBO
            - Binds vertex and element data to VBO and EBO
            - Enables vertex attributes based on bitflags
            - Sets texture and lightmap if present
            - Unbinds buffers.
        """
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
        # Convert vertex_data bytearray to MemoryView
        if not isinstance(vertex_data, memoryview):
            vertex_data = memoryview(vertex_data)
        glBufferData(GL_ARRAY_BUFFER, len(vertex_data), vertex_data, GL_STATIC_DRAW)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self._ebo)
        # Convert element_data bytearray to MemoryView
        if not isinstance(element_data, memoryview):
            element_data = memoryview(element_data)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(element_data), element_data, GL_STATIC_DRAW)

        self._face_count = len(element_data) // 2

        if data_bitflags & 0x0001:
            glEnableVertexAttribArray(1)
            glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, block_size, ctypes.c_void_p(vertex_offset))

        if data_bitflags & 0x0020 and texture and texture != "NULL":
            glEnableVertexAttribArray(3)
            glVertexAttribPointer(3, 2, GL_FLOAT, GL_FALSE, block_size, ctypes.c_void_p(texture_offset))
            self.texture = texture

        if data_bitflags & 0x0004 and lightmap and lightmap != "NULL":
            glEnableVertexAttribArray(4)
            glVertexAttribPointer(4, 2, GL_FLOAT, GL_FALSE, block_size, ctypes.c_void_p(lightmap_offset))
            self.lightmap = lightmap

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def draw(
        self,
        shader: Shader,
        transform: mat4,
        override_texture: str | None = None,
    ):
        shader.set_matrix4("model", transform)

        glActiveTexture(GL_TEXTURE0)
        self._scene.texture(override_texture or self.texture).use()

        glActiveTexture(GL_TEXTURE1)
        self._scene.texture(self.lightmap).use()

        glBindVertexArray(self._vao)
        glDrawElements(GL_TRIANGLES, self._face_count, GL_UNSIGNED_SHORT, None)


class Cube:
    def __init__(self, scene: Scene, min_point: vec3 | None = None, max_point: vec3 | None = None):
        """Initializes a cube mesh.

        Args:
        ----
            scene: Scene: The scene object
            min_point: vec3 | None: The minimum point of the cube (default is (-1, -1, -1))
            max_point: vec3 | None: The maximum point of the cube (default is (1, 1, 1)).

        Processing Logic:
        ----------------
            - Sets default values for min_point and max_point if not provided
            - Generates vertex and element arrays for the cube mesh
            - Binds VAO, VBO and EBO buffers and uploads data
            - Enables vertex attribute arrays.
        """
        self._scene = scene

        min_point = vec3(-1.0, -1.0, -1.0) if min_point is None else min_point
        max_point = vec3(1.0, 1.0, 1.0) if max_point is None else max_point

        vertices = np.array(
            [
                min_point.x,
                min_point.y,
                max_point.z,
                max_point.x,
                min_point.y,
                max_point.z,
                max_point.x,
                max_point.y,
                max_point.z,
                min_point.x,
                max_point.y,
                max_point.z,
                min_point.x,
                min_point.y,
                min_point.z,
                max_point.x,
                min_point.y,
                min_point.z,
                max_point.x,
                max_point.y,
                min_point.z,
                min_point.x,
                max_point.y,
                min_point.z,
            ],
            dtype="float32",
        )

        elements = np.array(
            [
                0,
                1,
                2,
                2,
                3,
                0,
                1,
                5,
                6,
                6,
                2,
                1,
                7,
                6,
                5,
                5,
                4,
                7,
                4,
                0,
                3,
                3,
                7,
                4,
                4,
                5,
                1,
                1,
                0,
                4,
                3,
                2,
                6,
                6,
                7,
                3,
            ],
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
    def __init__(self, scene: Scene, vertices: list[Vector3]):
        """Initializes a mesh from vertices.

        Args:
        ----
            scene: Scene - The scene to add this mesh to
            vertices: list[Vector3] - The vertices of the mesh

        Processing Logic:
        ----------------
            - Build normalized data from vertices
            - Generate VAO, VBO, EBO OpenGL buffers
            - Populate VBO with vertex data
            - Populate EBO with element indices
            - Configure vertex attributes.
        """
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
    def from_circle(cls, scene: Scene, radius: float, smoothness: int = 10) -> Boundary:
        """Generates a circular boundary from a circle.

        Args:
        ----
            scene: Scene - The scene to add the boundary to
            radius: float - The radius of the circle
            smoothness: int = 10 - The number of vertices used to approximate the circle

        Returns:
        -------
            Boundary - The generated circular boundary

        Processing Logic:
        ----------------
            - Calculate vertex positions around the circle at intervals of smoothness
            - Add vertices rotating around the circle four times
            - Return a new Boundary instance with the calculated vertices.
        """
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
