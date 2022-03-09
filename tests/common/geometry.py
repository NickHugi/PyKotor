from unittest import TestCase

from pykotor.common.geometry import Polygon2, Vector2, Vector3, Vector4


class TestVector2(TestCase):
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


class TestPolygon2(TestCase):
    def test_inside(self):
        poly = Polygon2([Vector2(0.0, 0.0), Vector2(0, 6), Vector2(6, 6), Vector2(6, 0), Vector2(3, 3)])

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
        poly = Polygon2([Vector2(0.0, 0.0), Vector2(0, 6), Vector2(6, 6), Vector2(6, 0), Vector2(3, 3)])

        self.assertEqual(27.0, poly.area())

