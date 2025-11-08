from __future__ import annotations

from copy import copy
from typing import TYPE_CHECKING

import glm

from glm import mat4, quat, vec3, vec4

if TYPE_CHECKING:
    from pykotor.gl.models.mesh import Mesh
    from pykotor.gl.scene import Scene
    from pykotor.gl.shader import Shader

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

        self._recalc_transform()

    def root(self) -> Node | None:
        ancestor: Node | None = self._parent
        while ancestor:
            ancestor = ancestor._parent  # noqa: SLF001
        return ancestor

    def ancestors(self) -> list[Node]:
        ancestors: list[Node] = []
        ancestor: Node | None = self._parent
        while ancestor:
            ancestors.append(ancestor)
            ancestor = ancestor._parent  # noqa: SLF001
        return list(reversed(ancestors))

    def global_position(self) -> vec3:  # sourcery skip: class-extract-method
        ancestors: list[Node] = [*self.ancestors(), self]
        transform = mat4()
        for ancestor in ancestors:
            transform = transform * glm.translate(ancestor._position)  # noqa: SLF001
            transform = transform * glm.mat4_cast(ancestor._rotation)  # noqa: SLF001
        position = vec3()
        glm.decompose(transform, vec3(), quat(), position, vec3(), vec4())  # pyright: ignore[reportCallIssue, reportArgumentType]
        return position

    def global_rotation(self) -> quat:
        ancestors: list[Node] = [*self.ancestors(), self]
        transform = mat4()
        for ancestor in ancestors:
            transform = transform * glm.translate(ancestor._position)  # noqa: SLF001
            transform = transform * glm.mat4_cast(ancestor._rotation)  # noqa: SLF001
        rotation = quat()
        glm.decompose(transform, vec3(), rotation, vec3(), vec3(), vec4())  # pyright: ignore[reportCallIssue, reportArgumentType]
        return rotation

    def global_transform(self) -> mat4:
        ancestors: list[Node] = [*self.ancestors(), self]
        transform = mat4()
        for ancestor in ancestors:
            transform = transform * glm.translate(ancestor._position)  # noqa: SLF001
            transform = transform * glm.mat4_cast(ancestor._rotation)  # noqa: SLF001
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
        transform = transform * self._transform

        if self.mesh and self.render:
            self.mesh.draw(shader, transform, override_texture)

        for child in self.children:
            child.draw(shader, transform, override_texture=override_texture)
