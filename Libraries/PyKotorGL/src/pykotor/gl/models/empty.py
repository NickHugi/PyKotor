from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from glm import mat4

    from pykotor.gl.scene import Scene
    from pykotor.gl.shader import Shader

class Empty:
    def __init__(self, scene: Scene):
        self._scene: Scene = scene

    def draw(self, shader: Shader, transform: mat4):
        ...
