from __future__ import annotations

import math
import os
import pathlib
import sys
import unittest

from unittest import TestCase

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[2].joinpath("Libraries", "PyKotor", "src")
UTILITY_PATH = THIS_SCRIPT_PATH.parents[2].joinpath("Libraries", "Utility", "src")


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.common.geometry import Face, Polygon2, Vector2, Vector3, Vector4


class TestVector2(TestCase):
    def test_unpacking(self):
        source = Vector2(1.2, 2.3)
        x, y = source
        self.assertEqual(x, 1.2)
        self.assertEqual(y, 2.3)

    def test_from_vector2(self):
        source = Vector2(1.2, 2.3)
        vec2 = Vector2.from_vector2(source)
        self.assertEqual(vec2.x, 1.2)
        self.assertEqual(vec2.y, 2.3)

    def test_from_vector3(self):
        source = Vector3(1.2, 2.3, 3.4)
        vec2 = Vector2.from_vector3(source)
        self.assertEqual(vec2.x, 1.2)
        self.assertEqual(vec2.y, 2.3)

    def test_from_vector4(self):
        source = Vector4(1.2, 2.3, 3.4, 5.6)
        vec2 = Vector2.from_vector4(source)
        self.assertEqual(vec2.x, 1.2)
        self.assertEqual(vec2.y, 2.3)


class TestVector3(TestCase):
    def test_unpacking(self):
        source = Vector3(1.2, 2.3, 3.4)
        x, y, z = source
        self.assertEqual(x, 1.2)
        self.assertEqual(y, 2.3)
        self.assertEqual(z, 3.4)

    def test_from_vector2(self):
        source = Vector2(1.2, 2.3)
        vec3 = Vector3.from_vector2(source)
        self.assertEqual(vec3.x, 1.2)
        self.assertEqual(vec3.y, 2.3)
        self.assertEqual(vec3.z, 0.0)

    def test_from_vector3(self):
        source = Vector3(1.2, 2.3, 3.4)
        vec3 = Vector3.from_vector3(source)
        self.assertEqual(vec3.x, 1.2)
        self.assertEqual(vec3.y, 2.3)
        self.assertEqual(vec3.z, 3.4)

    def test_from_vector4(self):
        source = Vector4(1.2, 2.3, 3.4, 5.6)
        vec3 = Vector3.from_vector4(source)
        self.assertEqual(vec3.x, 1.2)
        self.assertEqual(vec3.y, 2.3)
        self.assertEqual(vec3.z, 3.4)


class TestVector4(TestCase):
    def test_unpacking(self):
        source = Vector4(1.2, 2.3, 3.4, 4.5)
        x, y, z, w = source
        self.assertEqual(x, 1.2)
        self.assertEqual(y, 2.3)
        self.assertEqual(z, 3.4)
        self.assertEqual(w, 4.5)

    def test_from_vector2(self):
        source = Vector2(1.2, 2.3)
        vec4 = Vector4.from_vector2(source)
        self.assertEqual(vec4.x, 1.2)
        self.assertEqual(vec4.y, 2.3)
        self.assertEqual(vec4.z, 0.0)
        self.assertEqual(vec4.w, 0.0)

    def test_from_vector3(self):
        source = Vector3(1.2, 2.3, 3.4)
        vec4 = Vector4.from_vector3(source)
        self.assertEqual(vec4.x, 1.2)
        self.assertEqual(vec4.y, 2.3)
        self.assertEqual(vec4.z, 3.4)
        self.assertEqual(vec4.w, 0.0)

    def test_from_vector4(self):
        source = Vector4(1.2, 2.3, 3.4, 5.6)
        vec4 = Vector4.from_vector4(source)
        self.assertEqual(vec4.x, 1.2)
        self.assertEqual(vec4.y, 2.3)
        self.assertEqual(vec4.z, 3.4)
        self.assertEqual(vec4.w, 5.6)

    def test_from_euler(self):
        # Converting degrees to radians
        rad_90 = math.radians(90)

        q1 = Vector4.from_euler(0, 0, 0)
        q2 = Vector4.from_euler(rad_90, 0, 0)
        q3 = Vector4.from_euler(0, rad_90, 0)
        q4 = Vector4.from_euler(0, 0, rad_90)

        self.assertAlmostEqual(0.0, q1.x, 1)
        self.assertAlmostEqual(0.0, q1.y, 1)
        self.assertAlmostEqual(0.0, q1.z, 1)
        self.assertAlmostEqual(1.0, q1.w, 1)

        self.assertAlmostEqual(0.7, q2.x, 1)
        self.assertAlmostEqual(0.0, q2.y, 1)
        self.assertAlmostEqual(0.0, q2.z, 1)
        self.assertAlmostEqual(0.7, q2.w, 1)

        self.assertAlmostEqual(0.0, q3.x, 1)
        self.assertAlmostEqual(0.7, q3.y, 1)
        self.assertAlmostEqual(0.0, q3.z, 1)
        self.assertAlmostEqual(0.7, q3.w, 1)

        self.assertAlmostEqual(0.0, q4.x, 1)
        self.assertAlmostEqual(0.0, q4.y, 1)
        self.assertAlmostEqual(0.7, q4.z, 1)
        self.assertAlmostEqual(0.7, q4.w, 1)


class TestFace(TestCase):
    def test_determine_z(self):
        v1 = Vector3(0.0, 0.0, 0.0)
        v2 = Vector3(1.0, 0.0, 1.0)
        v3 = Vector3(0.0, 1.0, 1.0)
        face = Face(v1, v2, v3)
        # At the points
        self.assertEqual(0.0, face.determine_z(0.0, 0.0))  # v1
        self.assertEqual(1.0, face.determine_z(1.0, 0.0))  # v2
        self.assertEqual(1.0, face.determine_z(0.0, 1.0))  # v3
        # Middle of each edge
        self.assertEqual(0.5, face.determine_z(0.5, 0.0))  # v1, v2
        self.assertEqual(0.5, face.determine_z(0.0, 0.5))  # v1, v3
        self.assertEqual(1.0, face.determine_z(0.5, 0.5))  # v2, v3
        # Centre of the face
        self.assertEqual(0.66, face.determine_z(0.33, 0.33))


class TestPolygon2(TestCase):
    def test_inside(self):
        poly = Polygon2(
            [
                Vector2(0.0, 0.0),
                Vector2(0, 6),
                Vector2(6, 6),
                Vector2(6, 0),
                Vector2(3, 3),
            ]
        )

        # Inside
        self.assertTrue(poly.inside(Vector2(2.0, 4.0)))
        self.assertTrue(poly.inside(Vector2(5.0, 6.0)))

        # On the edge
        self.assertTrue(poly.inside(Vector2(0.0, 3.0)))
        self.assertFalse(poly.inside(Vector2(0.0, 3.0), False))

        # Outside
        self.assertFalse(poly.inside(Vector2(3.0, 0.0)))
        self.assertFalse(poly.inside(Vector2(3.0, 7.0)))

    def test_area(self):
        poly = Polygon2(
            [
                Vector2(0.0, 0.0),
                Vector2(0, 6),
                Vector2(6, 6),
                Vector2(6, 0),
                Vector2(3, 3),
            ]
        )

        self.assertEqual(27.0, poly.area())


if __name__ == "__main__":
    unittest.main()
