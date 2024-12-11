from __future__ import annotations

import ctypes

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
from glm import vec3

if TYPE_CHECKING:
    from glm import mat4

    from pykotor.gl.scene import Scene
    from pykotor.gl.shader import Shader

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
            [0, 1, 2, 2, 3, 0, 1, 5, 6, 6, 2, 1, 7, 6, 5, 5, 4, 7, 4, 0, 3, 3, 7, 4, 4, 5, 1, 1, 0, 4, 3, 2, 6, 6, 7, 3],
            dtype="int16",
        )

        self.min_point: vec3 = min_point
        self.max_point: vec3 = max_point

        self._vao: int = glGenVertexArrays(1)
        self._vbo: int = glGenBuffers(1)
        self._ebo: int = glGenBuffers(1)
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
