from __future__ import annotations

import ctypes
from typing import Optional, List

import glm
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
from glm import mat4, vec3, quat

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


class Node:
    def __init__(self, scene: Scene, parent: Optional[Node], name: str):
        self._scene: Scene = scene
        self._parent: Optional[Node] = parent
        self.name: str = name
        self.position: vec3 = glm.vec3()
        self.rotation: quat = glm.quat()
        self.children: List[Node] = []
        self.render: bool = True
        self.mesh: Optional[Mesh] = None

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

    def draw(self, shader: Shader, transform: mat4):
        transform = glm.translate(transform, self.position)
        transform = transform * glm.mat4_cast(self.rotation)

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
