from __future__ import annotations

import ctypes

from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from glm import mat4

    from pykotor.gl.models.node import Node
    from pykotor.gl.scene import Scene
    from pykotor.gl.shader import Shader

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

        self.vertex_data: bytearray = vertex_data
        self.mdx_size: int = block_size
        self.mdx_vertex: int = vertex_offset

        self._vao: int = glGenVertexArrays(1)
        self._vbo: int = glGenBuffers(1)
        self._ebo: int = glGenBuffers(1)
        glBindVertexArray(self._vao)

        glBindBuffer(GL_ARRAY_BUFFER, self._vbo)
        # Convert vertex_data bytearray to MemoryView
        vertex_data_mv = memoryview(vertex_data)
        glBufferData(GL_ARRAY_BUFFER, len(vertex_data), vertex_data_mv, GL_STATIC_DRAW)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self._ebo)
        # Convert element_data bytearray to MemoryView
        element_data_mv = memoryview(element_data)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(element_data), element_data_mv, GL_STATIC_DRAW)

        self._face_count: int = len(element_data) // 2

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
        self._scene.texture(self.lightmap, lightmap=True).use()

        glBindVertexArray(self._vao)
        glDrawElements(GL_TRIANGLES, self._face_count, GL_UNSIGNED_SHORT, None)
