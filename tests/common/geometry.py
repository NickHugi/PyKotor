from unittest import TestCase

from pykotor.common.geometry import Polygon2, Vector2


class TestPolygon2(TestCase):
    def test_concave(self):
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

        self.assertEqual(27.0)

