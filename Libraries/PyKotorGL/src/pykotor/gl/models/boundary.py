from __future__ import annotations

import ctypes
import math

from typing import TYPE_CHECKING

import numpy as np

from OpenGL.GL import glGenBuffers, glGenVertexArrays, glVertexAttribPointer
from OpenGL.GL.shaders import GL_FALSE
from OpenGL.raw.GL.ARB.tessellation_shader import GL_TRIANGLES
from OpenGL.raw.GL.ARB.vertex_shader import GL_FLOAT
from OpenGL.raw.GL.VERSION.GL_1_0 import GL_UNSIGNED_SHORT
from OpenGL.raw.GL.VERSION.GL_1_1 import glDrawElements
from OpenGL.raw.GL.VERSION.GL_1_5 import GL_ARRAY_BUFFER, GL_ELEMENT_ARRAY_BUFFER, GL_STATIC_DRAW, glBindBuffer, glBufferData
from OpenGL.raw.GL.VERSION.GL_2_0 import glEnableVertexAttribArray
from OpenGL.raw.GL.VERSION.GL_3_0 import glBindVertexArray

from utility.common.geometry import Vector3

if TYPE_CHECKING:
    from glm import mat4

    from pykotor.gl.scene import Scene
    from pykotor.gl.shader import Shader

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

    def _build_nd(self, vertices: list[Vector3]) -> tuple[np.ndarray, np.ndarray]:
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
