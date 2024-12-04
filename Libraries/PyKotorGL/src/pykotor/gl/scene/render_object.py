from __future__ import annotations

from copy import copy
from typing import TYPE_CHECKING, Any, Callable, Union

import glm

from glm import mat4, quat, vec3, vec4

from pykotor.gl.models.mdl import Cube, Empty

if TYPE_CHECKING:
    from pykotor.gl.models.mdl import Boundary
    from pykotor.gl.scene.scene import Scene


class RenderObject:
    def __init__(
        self,
        model: str,
        position: vec3 | None = None,
        rotation: vec3 | None = None,
        *,
        data: Any = None,
        gen_boundary: Callable[[], Boundary] | None = None,
        override_texture: str | None = None,
    ):
        self.model: str = model
        self.children: list[RenderObject] = []
        self._transform: mat4 = mat4()
        self._position: vec3 = vec3() if position is None else position
        self._rotation: vec3 = vec3() if rotation is None else rotation
        self._cube: Cube | None = None
        self._boundary: Boundary | Empty | None = None
        self.gen_boundary: Callable[[], Boundary] | None = gen_boundary
        self.data: Any = data
        self.override_texture: str | None = override_texture

        self._recalc_transform()

    def transform(self) -> mat4:
        return self._transform

    def set_transform(
        self,
        transform: mat4,
    ):
        self._transform = transform
        rotation = quat()
        scale = vec3()
        skew = vec3()
        perspective = vec4()
        glm.decompose(transform, scale, rotation, self._position, skew, perspective)
        self._rotation = glm.eulerAngles(rotation)

    def _recalc_transform(self):
        self._transform = mat4() * glm.translate(self._position)
        self._transform = self._transform * glm.mat4_cast(quat(self._rotation))

    def position(self) -> vec3:
        return copy(self._position)

    def set_position(
        self,
        x: float,
        y: float,
        z: float,
    ):
        if self._position.x == x and self._position.y == y and self._position.z == z:
            return

        self._position = vec3(x, y, z)
        self._recalc_transform()

    def rotation(self) -> vec3:
        return copy(self._rotation)

    def set_rotation(
        self,
        x: float,
        y: float,
        z: float,
    ):
        if self._rotation.x == x and self._rotation.y == y and self._rotation.z == z:
            return

        self._rotation = vec3(x, y, z)
        self._recalc_transform()

    def reset_cube(self):
        self._cube = None

    def cube(
        self,
        scene: Scene,
    ) -> Cube:
        if not self._cube:
            min_point = vec3(10000, 10000, 10000)
            max_point = vec3(-10000, -10000, -10000)
            self._cube_rec(scene, mat4(), self, min_point, max_point)
            self._cube = Cube(scene, min_point, max_point)
        return self._cube

    def radius(
        self,
        scene: Scene,
    ) -> float:
        cube = self.cube(scene)
        return max(
            abs(cube.min_point.x),
            abs(cube.min_point.y),
            abs(cube.min_point.z),
            abs(cube.max_point.x),
            abs(cube.max_point.y),
            abs(cube.max_point.z),
        )

    def _cube_rec(
        self,
        scene: Scene,
        transform: mat4,
        obj: RenderObject,
        min_point: vec3,
        max_point: vec3,
    ):
        obj_min, obj_max = scene.model(obj.model).box()
        obj_min: vec3 = transform * obj_min
        obj_max: vec3 = transform * obj_max
        min_point.x = min(min_point.x, obj_min.x, obj_max.x)
        min_point.y = min(min_point.y, obj_min.y, obj_max.y)
        min_point.z = min(min_point.z, obj_min.z, obj_max.z)
        max_point.x = max(max_point.x, obj_min.x, obj_max.x)
        max_point.y = max(max_point.y, obj_min.y, obj_max.y)
        max_point.z = max(max_point.z, obj_min.z, obj_max.z)
        for child in obj.children:
            self._cube_rec(scene, transform * child.transform(), child, min_point, max_point)

    def reset_boundary(self):
        self._boundary = None

    def boundary(
        self,
        scene: Scene,
    ) -> Union[Boundary, Empty]:
        if self._boundary is None:
            self._boundary = Empty(scene) if self.gen_boundary is None else self.gen_boundary()
        return self._boundary
