"""
This module holds classes relating to geometry.
"""
from __future__ import annotations

import math
from enum import IntEnum
from typing import List


class Vector2:
    """
    Represents a 2 dimensional vector.

    Attributes:
        x: The x component.
        y: The y component.
    """

    def __init__(
            self,
            x: float,
            y: float
    ):
        self.x: float = x
        self.y: float = y

    def __iter__(
            self
    ):
        return iter((self.x, self.y))

    def __repr__(
            self
    ):
        return "Vector2({}, {})".format(self.x, self.y)

    def __str__(
            self
    ):
        """
        Returns the individual components separated by whitespace.
        """
        return "{} {}".format(self.x, self.y)

    def __eq__(
            self,
            other
    ):
        """
        Two Vector2 components are equal if their components are approximately the same.
        """
        if not isinstance(other, Vector2):
            return NotImplemented

        isclose_x = math.isclose(self.x, other.x)
        isclose_y = math.isclose(self.y, other.y)
        return isclose_x and isclose_y

    def __add__(
            self,
            other
    ):
        """
        Adds the components of two Vector2 objects.
        """
        if not isinstance(other, Vector2):
            return NotImplemented

        new = Vector2.from_vector2(self)
        new.x += other.x
        new.y += other.y
        return new

    def __sub__(
            self,
            other
    ):
        """
        Subtracts the components of two Vector2 objects.
        """
        if not isinstance(other, Vector2):
            return NotImplemented

        new = Vector2.from_vector2(self)
        new.x -= other.x
        new.y -= other.y
        return new

    def __mul__(
            self,
            other
    ):
        """
        Multiplies the components by a scalar integer.
        """
        if not isinstance(other, int):
            return NotImplemented

        new = Vector2.from_vector2(self)
        new.x *= other
        new.y *= other
        return new

    def __truediv__(
            self,
            other
    ):
        if isinstance(other, int):
            new = Vector2.from_vector2(self)
            new.x /= other
            new.y /= other
            return new
        else:
            return NotImplemented

    def __getitem__(
            self,
            item
    ):
        if isinstance(item, int):
            if item == 0:
                return self.x
            elif item == 1:
                return self.y
        else:
            return NotImplemented

    def __setitem__(
            self,
            key,
            value
    ):
        if isinstance(key, int) and (isinstance(value, float) or isinstance(value, int)):
            if key == 0:
                self.x = value
            elif key == 1:
                self.y = value
        else:
            return NotImplemented

    @classmethod
    def from_vector2(
            cls,
            other: Vector2
    ) -> Vector2:
        """
        Returns a duplicate of the specified vector.

        Args:
            other: The vector to be duplicated.

        Returns:
            A new Vector2 object.
        """
        return Vector2(other.x, other.y)

    @classmethod
    def from_vector3(
            cls,
            other: Vector3
    ) -> Vector2:
        """
        Returns a Vector2 object from the Vector3 object, discarding the Z-component.

        Args:
            other: The vector to be copied.

        Returns:
            A new Vector2 object.
        """
        return Vector2(other.x, other.y)

    @classmethod
    def from_vector4(
            cls,
            other: Vector4
    ) -> Vector2:
        """
        Returns a Vector2 object from the Vector4 object, discarding the Z-component and W-components.

        Args:
            other: The vector to be copied.

        Returns:
            A new Vector2 object.
        """
        return Vector2(other.x, other.y)

    @classmethod
    def from_null(
            cls
    ) -> Vector2:
        """
        Returns a new vector with a magnitude of zero.

        Returns:
            A new Vector2 instance.
        """
        return Vector2(0.0, 0.0)

    @classmethod
    def from_angle(
            cls,
            angle: float
    ) -> Vector2:
        """
        Returns a unit vector based on the specified angle.

        Args:
            angle: The angle of the new vector.

        Returns:
            A new Vector2 instance.
        """
        x = math.cos(math.radians(angle))
        y = math.sin(math.radians(angle))
        return Vector2(x, y)

    def set(
            self,
            x: float,
            y: float
    ) -> None:
        """
        Sets the components of the vector.

        Args:
            x: The new x component.
            y: The new y component.
        """
        self.x = x
        self.y = y

    def normalize(
            self
    ) -> None:
        """
        Normalizes the vector so that the magnitude is equal to one while maintaining the same angle.
        """
        magnitude = self.magnitude()
        self.x /= magnitude
        self.y /= magnitude

    def magnitude(
            self
    ) -> float:
        """
        Returns the magnitude of the vector.

        Returns:
            The magnitude of the vector.
        """
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def normal(
            self
    ) -> Vector2:
        vec2 = Vector2.from_vector2(self)
        magnitude = self.magnitude()
        vec2.x /= magnitude
        vec2.y /= magnitude
        return vec2

    def dot(
            self,
            other: Vector2
    ) -> float:
        """
        Returns the dot product between the two specified vectors.

        Args:
            other: The other vector.

        Returns:
            The dot product.
        """
        a = self.x * other.x
        b = self.y * other.y
        return a + b

    def distance(
            self,
            other: Vector2
    ) -> float:
        """
        Returns the distance between two vectors.

        Args:
            other: The other vector.

        Returns:
            The distance between the vectors.
        """
        a = (self.x - other.x) ** 2
        b = (self.y - other.y) ** 2
        return math.sqrt(a + b)

    def within(
            self,
            container: List
    ) -> bool:
        """
        Checks to see if the same Vector2 object in located in the specified list. This differs from using the 'in'
        keyword as that will return True for Vector2 objects that have simular coordinates.

        Args:
            container: The list to search in.

        Returns:
            True if the Vector2 exists in the container.
        """
        for item in container:
            if item is self:
                return True
        return False

    def angle(
            self
    ) -> float:
        """
        Returns the angle of the vector.

        Returns:
            The angle of the vector.
        """
        return math.degrees(math.atan2(self.y, self.x))


class Vector3:
    """
    Represents a 3 dimensional vector.

    Attributes:
        x: The x component.
        y: The y component.
        z: The z component.
    """

    def __init__(
            self,
            x: float,
            y: float,
            z: float
    ):
        self.x: float = x
        self.y: float = y
        self.z: float = z

    def __iter__(
            self
    ):
        return iter((self.x, self.y, self.z))

    def __repr__(
            self
    ):
        return "Vector3({}, {}, {})".format(self.x, self.y, self.z)

    def __str__(
            self
    ):
        """
        Returns the individual components as a string separated by whitespace.
        """
        return "{} {} {}".format(self.x, self.y, self.z)

    def __eq__(
            self,
            other
    ):
        """
        Two Vector3 components are equal if their components are approximately the same.
        """
        if not isinstance(other, Vector3):
            return NotImplemented

        isclose_x = math.isclose(self.x, other.x)
        isclose_y = math.isclose(self.y, other.y)
        isclose_z = math.isclose(self.z, other.z)
        return isclose_x and isclose_y and isclose_z

    def __add__(
            self,
            other
    ):
        """
        Adds the components of two Vector3 objects.
        """
        if not isinstance(other, Vector3):
            return NotImplemented

        new = Vector3.from_vector3(self)
        new.x += other.x
        new.y += other.y
        new.z += other.z
        return new

    def __sub__(
            self,
            other
    ):
        """
        Subtracts the components of two Vector3 objects.
        """
        if not isinstance(other, Vector3):
            return NotImplemented

        new = Vector3.from_vector3(self)
        new.x -= other.x
        new.y -= other.y
        new.z -= other.z
        return new

    def __mul__(
            self,
            other
    ):
        """
        Multiplies the components by a scalar integer.
        """
        if isinstance(other, int) or isinstance(other, float):
            new = Vector3.from_vector3(self)
            new.x *= other
            new.y *= other
            new.z *= other
            return new
        else:
            return NotImplemented

    def __truediv__(
            self,
            other
    ):
        if isinstance(other, int):
            new = Vector3.from_vector3(self)
            new.x /= other
            new.y /= other
            new.z /= other
            return new
        else:
            return NotImplemented

    def __getitem__(
            self,
            item
    ):
        if isinstance(item, int):
            if item == 0:
                return self.x
            elif item == 1:
                return self.y
            elif item == 2:
                return self.z
        else:
            return NotImplemented

    def __setitem__(
            self,
            key,
            value
    ):
        if isinstance(key, int) and (isinstance(value, float) or isinstance(value, int)):
            if key == 0:
                self.x = value
            elif key == 1:
                self.y = value
            elif key == 2:
                self.z = value
        else:
            return NotImplemented

    @classmethod
    def from_vector2(
            cls,
            other: Vector2
    ) -> Vector3:
        """
        Returns a Vector3 object from the Vector2 object, setting the Z-component to zero.

        Args:
            other: The vector to be copied.

        Returns:
            A new Vector3 object.
        """
        return Vector3(other.x, other.y, 0.0)

    @classmethod
    def from_vector3(
            cls,
            other: Vector3
    ) -> Vector3:
        """
        Returns a duplicate of the specified vector.

        Args:
            other: The vector to be duplicated.

        Returns:
            A new Vector3 instance.
        """
        return Vector3(other.x, other.y, other.z)

    @classmethod
    def from_vector4(
            cls,
            other: Vector4
    ) -> Vector3:
        """
        Returns a Vector3 object from the Vector4 object, discarding the W-component.

        Args:
            other: The vector to be copied.

        Returns:
            A new Vector3 object.
        """
        return Vector3(other.x, other.y, other.z)

    @classmethod
    def from_null(
            cls
    ) -> Vector3:
        """
        Returns a new vector with a magnitude of zero.

        Returns:
            A new Vector3 instance.
        """
        return Vector3(0.0, 0.0, 0.0)

    def set(
            self,
            x: float,
            y: float,
            z: float
    ) -> None:
        """
        Sets the components of the vector.

        Args:
            x: The new x component.
            y: The new y component.
            z: The new y component.
        """
        self.x = x
        self.y = y
        self.z = z

    def normalize(
            self
    ) -> None:
        """
        Normalizes the vector so that the magnitude is equal to one while maintaining the same angle.
        """
        magnitude = self.magnitude()
        self.x /= magnitude
        self.y /= magnitude
        self.z /= magnitude

    def magnitude(
            self
    ) -> float:
        """
        Returns the magnitude of the vector.

        Returns:
            The magnitude of the vector.
        """
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def normal(
            self
    ) -> Vector3:
        vec3 = Vector3.from_vector3(self)
        magnitude = self.magnitude()
        vec3.x /= magnitude
        vec3.y /= magnitude
        vec3.z /= magnitude
        return vec3

    def dot(
            self,
            other: Vector3
    ) -> float:
        """
        Returns the dot product between the two specified vectors.

        Args:
            other: The other vector.

        Returns:
            The dot product.
        """
        a = self.x * other.x
        b = self.y * other.y
        c = self.z * other.z
        return a + b + c

    def distance(
            self,
            other: Vector3
    ) -> float:
        """
        Returns the distance between two vectors.

        Args:
            other: The other vector.

        Returns:
            The distance between the vectors.
        """
        a = (self.x - other.x) ** 2
        b = (self.y - other.y) ** 2
        c = (self.z - other.z) ** 2
        return math.sqrt(a + b + c)

    def within(
            self,
            container: List
    ) -> bool:
        """
        Checks to see if the same Vector3 object in located in the specified list. This differs from using the 'in'
        keyword as that will return True for Vector3 objects that have simular coordinates.

        Args:
            container: The list to search in.

        Returns:
            True if the Vector3 exists in the container.
        """
        for item in container:
            if item is self:
                return True
        return False


class Vector4:
    """
    Represents a 4 dimensional vector.

    Attributes:
        x: The x component.
        y: The y component.
        z: The z component.
        w: The w component.
    """

    def __init__(
            self,
            x: float,
            y: float,
            z: float,
            w: float
    ):
        self.x: float = x
        self.y: float = y
        self.z: float = z
        self.w: float = w

    def __iter__(
            self
    ):
        return iter((self.x, self.y, self.z, self.w))

    def __repr__(
            self
    ):
        return "Vector4({}, {}, {}, {})".format(self.x, self.y, self.z, self.w)

    def __str__(
            self
    ):
        """
        Returns the individual components as a string separated by whitespace.
        """
        return "{} {} {} {}".format(self.x, self.y, self.z, self.w)

    def __eq__(
            self,
            other
    ):
        """
        Two Vector4 components are equal if their components are approximately the same.
        """
        if not isinstance(other, Vector4):
            return NotImplemented

        isclose_x = math.isclose(self.x, other.x)
        isclose_y = math.isclose(self.y, other.y)
        isclose_z = math.isclose(self.z, other.z)
        isclose_w = math.isclose(self.w, other.w)
        return isclose_x and isclose_y and isclose_z and isclose_w

    def __add__(
            self,
            other
    ):
        """
        Adds the components of two Vectorr objects.
        """
        if not isinstance(other, Vector4):
            return NotImplemented

        new = Vector4.from_vector4(self)
        new.x += other.x
        new.y += other.y
        new.z += other.z
        new.w += other.w
        return new

    def __sub__(
            self,
            other
    ):
        """
        Subtracts the components of two Vector4 objects.
        """
        if not isinstance(other, Vector4):
            return NotImplemented

        new = Vector4.from_vector4(self)
        new.x -= other.x
        new.y -= other.y
        new.z -= other.z
        new.w -= other.w
        return new

    def __mul__(
            self,
            other
    ):
        """
        Multiplies the components by a scalar integer.
        """
        if not isinstance(other, int):
            return NotImplemented

        new = Vector4.from_vector4(self)
        new.x *= other
        new.y *= other
        new.z *= other
        new.w *= other
        return new

    @classmethod
    def from_vector2(
            cls,
            other: Vector2
    ) -> Vector4:
        """
        Returns a Vector4 object from the Vector2 object, setting the Z-component and W-component to zero.

        Args:
            other: The vector to be copied.

        Returns:
            A new Vector4 object.
        """
        return Vector4(other.x, other.y, 0.0, 0.0)

    @classmethod
    def from_vector3(
            cls,
            other: Vector3
    ) -> Vector4:
        """
        Returns a Vector4 object from the Vector3 object, setting the W-component to zero.

        Args:
            other: The vector to be copied.

        Returns:
            A new Vector4 object.
        """
        return Vector4(other.x, other.y, other.z, 0.0)

    @classmethod
    def from_vector4(
            cls,
            other: Vector4
    ) -> Vector4:
        """
        Returns a duplicate of the specified vector.

        Args:
            other: The vector to be duplicated.

        Returns:
            A new Vector4 instance.
        """
        return Vector4(other.x, other.y, other.z, other.w)

    @classmethod
    def from_null(
            cls
    ) -> Vector4:
        """
        Returns a new vector with a magnitude of zero.

        Returns:
            A new Vector4 instance.
        """
        return Vector4(0.0, 0.0, 0.0, 0.0)

    @classmethod
    def from_compressed(
            cls,
            data: int
    ) -> Vector4:
        x = 1 - (data & 0x7FF) / 1023
        y = 1 - ((data >> 11) & 0x7FF) / 1023
        z = 1 - (data >> 22) / 511

        temp = x ** 2 + y ** 2 + z ** 2
        if temp < 1.0:
            w = -math.sqrt(1.0 - temp)
        else:
            temp = math.sqrt(temp)
            x /= temp
            y /= temp
            z /= temp
            w = 0

        return Vector4(x, y, z, w)

    def magnitude(
            self
    ) -> float:
        """
        Returns the magnitude of the vector.

        Returns:
            The magnitude of the vector.
        """
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2 + self.w ** 2)

    def normalize(
            self
    ) -> Vector4:
        """
        Normalizes the vector so that the magnitude is equal to one while maintaining the same angle.

        Returns:
            The same vector.
        """
        magnitude = self.magnitude()
        self.x /= magnitude
        self.y /= magnitude
        self.z /= magnitude
        self.w /= magnitude
        return self

    def set(
            self,
            x: float,
            y: float,
            z: float,
            w: float
    ) -> None:
        """
        Sets the components of the vector.

        Args:
            x: The new x component.
            y: The new y component.
            z: The new y component.
            w: The new w component.
        """
        self.x = x
        self.y = y
        self.z = z
        self.w = w


class AxisAngle:
    """
    Represents a rotation in 3D space.

    Attributes:
        axis: The axis of rotation.
        angle: The magnitude of the rotation.
    """

    def __init__(
            self,
            axis: Vector3,
            angle: float
    ):
        self.axis: Vector3 = axis
        self.angle: float = angle

    @classmethod
    def from_quaternion(
            cls,
            quaternion: Vector4
    ) -> AxisAngle:
        """
        Returns a AxisAngle converted from a Vector4 quaternion.

        Args:
            quaternion: The quaternion.

        Returns:
            A new AxisAngle instance.
        """
        aa = AxisAngle.from_null()
        quaternion.normalize()

        aa.angle = 2.0 * math.atan2(Vector3(quaternion.x, quaternion.y, quaternion.z).magnitude(), quaternion.w)

        s = math.sin(aa.angle / 2.0)
        if s < 0.001:
            aa.axis = Vector3(1.0, 0.0, 0.0)
        else:
            aa.axis.x = quaternion.x / s
            aa.axis.y = quaternion.y / s
            aa.axis.z = quaternion.z / s

        return aa

    @classmethod
    def from_null(
            cls
    ) -> AxisAngle:
        """
        Returns a AxisAngle that contains no rotation.

        Returns:
            A new AxisAngle instance.
        """
        return AxisAngle(Vector3.from_null(), 0.0)


class SurfaceMaterial(IntEnum):
    """
    The surface materials for walkmeshes found in both games.
    """
    # as according to 'surfacemat.2da'
    UNDEFINED = 0
    DIRT = 1
    OBSCURING = 2
    GRASS = 3
    STONE = 4
    WOOD = 5
    WATER = 6
    NON_WALK = 7
    TRANSPARENT = 8
    CARPET = 9
    METAL = 10
    PUDDLES = 11
    SWAMP = 12
    MUD = 13
    LEAVES = 14
    LAVA = 15
    BOTTOMLESS_PIT = 16
    DEEP_WATER = 17
    DOOR = 18
    NON_WALK_GRASS = 19
    TRIGGER = 30

    def walkable(
            self
    ) -> bool:
        return self in [SurfaceMaterial.DIRT, SurfaceMaterial.GRASS, SurfaceMaterial.STONE, SurfaceMaterial.WOOD,
                        SurfaceMaterial.WATER, SurfaceMaterial.CARPET, SurfaceMaterial.METAL, SurfaceMaterial.PUDDLES,
                        SurfaceMaterial.SWAMP, SurfaceMaterial.MUD, SurfaceMaterial.LEAVES, SurfaceMaterial.DOOR,
                        SurfaceMaterial.TRIGGER]


class Face:
    """
    Represents a triangle in 3D space.

    Attributes:
        v1: First point of the triangle.
        v2: Second point of the triangle.
        v3: Third point of the triangle.
        material: Material of the triangle, for usage in-game.
    """

    def __init__(
            self,
            v1: Vector3,
            v2: Vector3,
            v3: Vector3,
            material=SurfaceMaterial.UNDEFINED
    ):
        self.v1: Vector3 = v1
        self.v2: Vector3 = v2
        self.v3: Vector3 = v3
        self.material: SurfaceMaterial = material

    def normal(
            self
    ) -> Vector3:
        """
        Returns the normal for the face.

        Returns:
            A new Vector3 instance representing the face normal.
        """
        u = self.v2 - self.v1
        v = self.v3 - self.v2

        normal = Vector3.from_null()
        normal.x = (u.y * v.z) - (u.z * v.y)
        normal.y = (u.z * v.x) - (u.x * v.z)
        normal.z = (u.x * v.y) - (u.y * v.x)
        normal.normalize()

        return normal

    def area(
            self
    ) -> float:
        a = self.v1.distance(self.v2)
        b = self.v1.distance(self.v3)
        c = self.v2.distance(self.v3)
        return 0.25 * math.sqrt((a + b + c) * (-a + b + c) * (a - b + c) * (a + b - c))

    def planar_distance(
            self
    ) -> float:
        return -1.0 * (self.normal().dot(self.v1))

    def centre(
            self
    ) -> Vector3:
        return (self.v1 + self.v2 + self.v3) / 3


class Polygon2:
    def __init__(
            self,
            points: List[Vector2] = None
    ):
        self.points: List[Vector2] = [] if points is None else points

    def __iter__(
            self
    ):
        for point in self.points:
            yield point

    def __len__(
            self
    ):
        return len(self.points)

    def __repr__(
            self
    ):
        return "Polygon3({})".format(self.points)

    def __getitem__(
            self,
            item: int
    ):
        if isinstance(item, int):
            return self.points[item]
        elif isinstance(item, slice):
            return self.points[item.start:item.stop:item.step]
        else:
            return NotImplemented

    def __setitem__(
            self,
            key: int,
            value: Vector2
    ):
        if isinstance(key, int) and isinstance(value, Vector2):
            self.points[key] = value
        else:
            return NotImplemented

    @classmethod
    def from_polygon3(
            cls,
            poly3: Polygon3
    ) -> Polygon2:
        """
        Converts a Polygon3 object into a Polygon2 object. The Z-axis is removed.

        Args:
            poly3: The polygon3 object to flatten.

        Returns:
            A Polygon2 object.
        """
        poly2 = Polygon2()
        for point in poly3:
            poly2.points.append(Vector2(point.x, point.y))
        return poly2

    def inside(
            self,
            point: Vector2,
            include_edges: bool = True
    ) -> bool:
        """
        Returns if the specified point is inside the polygon.

        Args:
            point: The point.
            include_edges: If True, a points on edges are considered inside the polygon.

        Returns:
            True if the point is inside the polygon.
        """
        # Code was adapted from this stackoverflow post:
        # https://stackoverflow.com/a/42306732

        n = len(self.points)
        inside = False

        p1 = self.points[0]
        for i in range(1, n + 1):
            p2 = self.points[i % n]
            if p1.y == p2.y:
                if point.y == p2.y:
                    if min(p1.x, p2.x) <= point.x <= max(p1.x, p2.x):
                        inside = include_edges
                        break
                    elif point.x < min(p1.x, p2.x):
                        inside = not inside
            else:
                if min(p1.y, p2.y) <= point.y <= max(p1.y, p2.y):
                    xinters = (point.y - p1.y) * (p2.x - p1.x) / float(p2.y - p1.y) + p1.x

                    if point.x == xinters:
                        inside = include_edges
                        break

                    if point.x < xinters:
                        inside = not inside
            p1 = p2
        return inside

    def area(
            self
    ) -> float:
        # Code was adapted from this stackoverflow post:
        # https://stackoverflow.com/a/34327761

        n = len(self.points)
        area = 0.0
        for i in range(0, n - 1):
            area += -self.points[i].y * self.points[i + 1].x + self.points[i].x * self.points[i + 1].y
        area += -self.points[n - 1].y * self.points[0].x + self.points[n - 1].x * self.points[0].y
        area = 0.5 * math.fabs(area)
        return area

    def append(
            self,
            point: Vector2
    ) -> None:
        self.points.append(point)

    def extend(
            self,
            points: List[Vector2]
    ) -> None:
        self.points.extend(points)

    def remove(
            self,
            point: Vector2
    ) -> None:
        self.points.remove(point)

    def index(
            self,
            point: Vector2
    ) -> int:
        return self.points.index(point)


class Polygon3:
    def __init__(
            self,
            points: List[Vector3] = None
    ):
        self.points: List[Vector3] = [] if points is None else points

    def __iter__(
            self
    ):
        for point in self.points:
            yield point

    def __len__(
            self
    ):
        return len(self.points)

    def __repr__(
            self
    ):
        return "Polygon3({})".format(self.points)

    def __getitem__(
            self,
            item: int
    ):
        if isinstance(item, int):
            return self.points[item]
        elif isinstance(item, slice):
            return self.points[item.start:item.stop:item.step]
        else:
            return NotImplemented

    def __setitem__(
            self,
            key: int,
            value: Vector3
    ):
        if isinstance(key, int) and isinstance(value, Vector3):
            self.points[key] = value
        else:
            return NotImplemented

    @classmethod
    def from_polygon2(
            cls,
            poly2: Polygon2
    ) -> Polygon3:
        """
        Converts a Polygon3 object into a Polygon2 object. Points have their Z-axis set to 0.

        Args:
            poly2: The polygon3 object to copy.

        Returns:
            A Polygon2 object.
        """
        poly3 = Polygon3()
        for point in poly3:
            poly3.points.append(Vector3(point.x, point.y, point.z))
        return poly3

    def append(
            self,
            point: Vector3
    ) -> None:
        self.points.append(point)

    def extend(
            self,
            points: List[Vector3]
    ) -> None:
        self.points.extend(points)

    def remove(
            self,
            point: Vector3
    ) -> None:
        self.points.remove(point)

    def index(
            self,
            point: Vector3
    ) -> int:
        return self.points.index(point)
