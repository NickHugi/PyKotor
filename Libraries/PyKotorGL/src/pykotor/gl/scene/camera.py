from __future__ import annotations

import math

from typing import TYPE_CHECKING, Literal, Union

import glm

from glm import mat4, vec3

if TYPE_CHECKING:
    from pykotor.common.geometry import Vector3


class Camera:
    def __init__(self):
        self.x: float = 40.0
        self.y: float = 130.0
        self.z: float = 0.5
        self.width: int = 1920
        self.height: int = 1080
        self.pitch: float = math.pi / 2
        self.yaw: float = 0.0
        self.distance: float = 10.0
        self.fov: float = 90.0

    def set_resolution(
        self,
        width: int,
        height: int,
    ):
        self.width, self.height = width, height

    def set_position(
        self,
        position: Union[Vector3, vec3],
    ):
        self.x = position.x
        self.y = position.y
        self.z = position.z

    def view(self) -> mat4:
        up: vec3 = vec3(0, 0, 1)
        pitch: vec3 = glm.vec3(1, 0, 0)

        x, y, z = self.x, self.y, self.z
        x += math.cos(self.yaw) * math.cos(self.pitch - math.pi / 2) * self.distance
        y += math.sin(self.yaw) * math.cos(self.pitch - math.pi / 2) * self.distance
        z += math.sin(self.pitch - math.pi / 2) * self.distance

        camera: mat4 = mat4() * glm.translate(vec3(x, y, z))
        camera = glm.rotate(camera, self.yaw + math.pi / 2, up)
        camera = glm.rotate(camera, math.pi - self.pitch, pitch)
        return glm.inverse(camera)

    def projection(self) -> mat4:
        return glm.perspective(
            self.fov,
            self.width / self.height,
            0.1,
            5000,
        )

    def translate(
        self,
        translation: vec3,
    ):
        self.x += translation.x
        self.y += translation.y
        self.z += translation.z

    def rotate(
        self,
        yaw: float,
        pitch: float,
        *,
        clamp: bool = False,
        lower_limit: float = 0,
        upper_limit: float = math.pi,
    ):
        # Update angles
        self.pitch += pitch
        self.yaw += yaw

        # Normalize yaw to [-2π, 2π]
        self.yaw = self.yaw % (4 * math.pi) - (2 * math.pi)

        if pitch == 0:
            return

        # Normalize pitch to [-2π, 2π]
        self.pitch = self.pitch % (4 * math.pi) - (2 * math.pi)

        # Apply pitch clamping if enabled
        if clamp:
            self.pitch = max(lower_limit, min(upper_limit, self.pitch))

        # Avoid gimbal lock near π/2
        if abs(self.pitch - math.pi / 2) < 0.05:  # noqa: PLR2004
            self.pitch += 0.02 if pitch > 0 else -0.02

    def forward(
        self,
        *,
        ignore_z: bool = True,
    ) -> vec3:
        eye_x: float = math.cos(self.yaw) * math.cos(self.pitch - math.pi / 2)
        eye_y: float = math.sin(self.yaw) * math.cos(self.pitch - math.pi / 2)
        eye_z: Union[float, Literal[0]] = 0 if ignore_z else math.sin(self.pitch - math.pi / 2)
        return glm.normalize(-vec3(eye_x, eye_y, eye_z))

    def sideward(
        self,
        *,
        ignore_z: bool = True,
    ) -> vec3:
        return glm.normalize(glm.cross(self.forward(ignore_z=ignore_z), vec3(0.0, 0.0, 1.0)))

    def upward(
        self,
        *,
        ignore_xy: bool = True,
    ) -> vec3:
        if ignore_xy:
            return glm.normalize(vec3(0, 0, 1))
        forward: vec3 = self.forward(ignore_z=False)
        sideward: vec3 = self.sideward(ignore_z=False)
        cross: vec3 = glm.cross(forward, sideward)
        return glm.normalize(cross)

    def true_position(self) -> vec3:
        cos_yaw: float = math.cos(self.yaw)
        cos_pitch: float = math.cos(self.pitch - math.pi / 2)
        sin_yaw: float = math.sin(self.yaw)
        sin_pitch: float = math.sin(self.pitch - math.pi / 2)
        return vec3(
            self.x + cos_yaw * cos_pitch * self.distance,
            self.y + sin_yaw * cos_pitch * self.distance,
            self.z + sin_pitch * self.distance,
        )
