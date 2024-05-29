from __future__ import annotations

import pathlib
import sys
import unittest

from glm import lookAt, perspective, radians, vec3

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "PyKotor", "src")
UTILITY_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "Utility", "src")
GL_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "PyKotorGL", "src")


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if GL_PATH.joinpath("pykotor").exists():
    add_sys_path(GL_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.gl.scene import Frustum, Plane


class TestPlane(unittest.TestCase):
    def setUp(self):
        self.plane = Plane(vec3(0, 0, 1), -10)  # Plane z=10

    def test_point_in_front_of_plane(self):
        point = vec3(0, 0, 15)
        self.assertGreaterEqual(self.plane.distance_to_point(point), 0)

    def test_point_behind_plane(self):
        point = vec3(0, 0, 5)
        self.assertLess(self.plane.distance_to_point(point), 0)

    def test_point_on_plane(self):
        point = vec3(0, 0, 10)
        self.assertAlmostEqual(self.plane.distance_to_point(point), 0)

class TestFrustum(unittest.TestCase):
    def setUp(self):
        fov = radians(90)
        aspect_ratio = 16/9
        near = 1.0
        far = 100.0
        self.projection_matrix = perspective(fov, aspect_ratio, near, far)
        self.camera_pos = vec3(0, 0, 10)
        self.camera_target = vec3(0, 0, 0)
        self.camera_up = vec3(0, 1, 0)
        self.view_matrix = lookAt(self.camera_pos, self.camera_target, self.camera_up)
        self.frustum = Frustum(self.projection_matrix, self.view_matrix)

    def test_point_inside_frustum(self):
        point = vec3(0, 0, 5)
        radius = 1
        self.assertTrue(self.frustum.is_sphere_visible(point, radius))

    def test_point_outside_frustum(self):
        point = vec3(0, 0, -20)  # behind the camera
        radius = 1
        self.assertFalse(self.frustum.is_sphere_visible(point, radius))

    def test_point_on_near_plane(self):
        point = vec3(0, 0, 9)  # near the near plane
        radius = 1
        self.assertTrue(self.frustum.is_sphere_visible(point, radius))

    def test_point_on_far_plane(self):
        point = vec3(0, 0, 0)  # near the far plane
        radius = 1
        self.assertTrue(self.frustum.is_sphere_visible(point, radius))

if __name__ == "__main__":
    unittest.main(verbosity=2)
