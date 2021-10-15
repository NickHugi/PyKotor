"""
This module holds classes relating to geometry.
"""
from __future__ import annotations
import math
from enum import IntEnum


class Vector2:
    """
    Represents a 2 dimensional vector.

    Attributes:
        x: The x component.
        y: The y component.
    """

    def __init__(self, x: float, y: float):
        self.x: float = x
        self.y: float = y

    def __repr__(self):
        return "Vector2({}, {})".format(self.x, self.y)

    def __str__(self):
        """
        Returns the individual components separated by whitespace.
        """
        return "{} {}".format(self.x, self.y)

    def __eq__(self, other):
        """
        Two Vector2 components are equal if their components are approximately the same.
        """
        if not isinstance(other, Vector2):
            return NotImplemented

        isclose_x = math.isclose(self.x, other.x)
        isclose_y = math.isclose(self.y, other.y)
        return isclose_x, isclose_y

    def __add__(self, other):
        """
        Adds the components of two Vector2 objects.
        """
        if not isinstance(other, Vector2):
            return NotImplemented

        new = Vector2.from_vector2(self)
        new.x += other.x
        new.y += other.y
        return new

    def __sub__(self, other):
        """
        Subtracts the components of two Vector2 objects.
        """
        if not isinstance(other, Vector2):
            return NotImplemented

        new = Vector2.from_vector2(self)
        new.x -= other.x
        new.y -= other.y
        return new

    def __mul__(self, other):
        """
        Multiplies the components by a scalar integer.
        """
        if not isinstance(other, int):
            return NotImplemented

        new = Vector2.from_vector2(self)
        new.x *= other
        new.y *= other
        return new

    @classmethod
    def from_vector2(cls, other: Vector2) -> Vector2:
        """
        Returns a duplicate of the specified vector.

        Args:
            other: The vector to be duplicated.

        Returns:
            A new Vector2 instance.
        """
        return Vector2(other.x, other.y)

    @classmethod
    def from_null(cls) -> Vector2:
        """
        Returns a new vector with a magnitude of zero.

        Returns:
            A new Vector2 instance.
        """
        return Vector2(0.0, 0.0)

    @classmethod
    def from_angle(cls, angle: float) -> Vector2:
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

    def magnitude(self) -> float:
        """
        Returns the magnitude of the vector.

        Returns:
            The magnitude of the vector.
        """
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def angle(self) -> float:
        """
        Returns the angle of the vector.

        Returns:
            The angle of the vector.
        """
        return math.degrees(math.atan2(self.y, self.x))

    def normalize(self) -> None:
        """
        Normalizes the vector so that the magnitude is equal to one while maintaining the same angle.
        """
        magnitude = self.magnitude()
        self.x /= magnitude
        self.y /= magnitude

    def set(self, x: float, y: float) -> None:
        """
        Sets the components of the vector.

        Args:
            x: The new x component.
            y: The new y component.
        """
        self.x = x
        self.y = y


class Vector3:
    """
    Represents a 3 dimensional vector.

    Attributes:
        x: The x component.
        y: The y component.
        z: The z component.
    """

    def __init__(self, x: float, y: float, z: float):
        self.x: float = x
        self.y: float = y
        self.z: float = z

    def __repr__(self):
        return "Vector3({}, {}, {})".format(self.x, self.y, self.z)

    def __str__(self):
        """
        Returns the individual components as a string separated by whitespace.
        """
        return "{} {} {}".format(self.x, self.y, self.z)

    def __eq__(self, other):
        """
        Two Vector3 components are equal if their components are approximately the same.
        """
        if not isinstance(other, Vector3):
            return NotImplemented

        isclose_x = math.isclose(self.x, other.x)
        isclose_y = math.isclose(self.y, other.y)
        isclose_z = math.isclose(self.z, other.z)
        return isclose_x, isclose_y, isclose_z

    def __add__(self, other):
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

    def __sub__(self, other):
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

    def __mul__(self, other):
        """
        Multiplies the components by a scalar integer.
        """
        if not isinstance(other, int):
            return NotImplemented

        new = Vector3.from_vector3(self)
        new.x *= other
        new.y *= other
        new.z *= other
        return new

    @classmethod
    def from_vector3(cls, other: Vector3) -> Vector3:
        """
        Returns a duplicate of the specified vector.

        Args:
            other: The vector to be duplicated.

        Returns:
            A new Vector3 instance.
        """
        return Vector3(other.x, other.y, other.z)

    @classmethod
    def from_null(cls) -> Vector3:
        """
        Returns a new vector with a magnitude of zero.

        Returns:
            A new Vector3 instance.
        """
        return Vector3(0.0, 0.0, 0.0)

    def magnitude(self) -> float:
        """
        Returns the magnitude of the vector.

        Returns:
            The magnitude of the vector.
        """
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def normalize(self) -> None:
        """
        Normalizes the vector so that the magnitude is equal to one while maintaining the same angle.
        """
        magnitude = self.magnitude()
        self.x /= magnitude
        self.y /= magnitude
        self.z /= magnitude

    def set(self, x: float, y: float, z: float) -> None:
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


class Vector4:
    """
    Represents a 4 dimensional vector.

    Attributes:
        x: The x component.
        y: The y component.
        z: The z component.
        w: The w component.
    """

    def __init__(self, x: float, y: float, z: float, w: float):
        self.x: float = x
        self.y: float = y
        self.z: float = z
        self.w: float = w

    def __repr__(self):
        return "Vector4({}, {}, {}, {})".format(self.x, self.y, self.z, self.w)

    def __str__(self):
        """
        Returns the individual components as a string separated by whitespace.
        """
        return "{} {} {} {}".format(self.x, self.y, self.z, self.w)

    def __eq__(self, other):
        """
        Two Vector4 components are equal if their components are approximately the same.
        """
        if not isinstance(other, Vector4):
            return NotImplemented

        isclose_x = math.isclose(self.x, other.x)
        isclose_y = math.isclose(self.y, other.y)
        isclose_z = math.isclose(self.z, other.z)
        isclose_w = math.isclose(self.w, other.w)
        return isclose_x, isclose_y, isclose_z, isclose_w

    def __add__(self, other):
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

    def __sub__(self, other):
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

    def __mul__(self, other):
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
    def from_vector4(cls, other: Vector4) -> Vector4:
        """
        Returns a duplicate of the specified vector.

        Args:
            other: The vector to be duplicated.

        Returns:
            A new Vector4 instance.
        """
        return Vector4(other.x, other.y, other.z, other.w)

    @classmethod
    def from_null(cls) -> Vector4:
        """
        Returns a new vector with a magnitude of zero.

        Returns:
            A new Vector4 instance.
        """
        return Vector4(0.0, 0.0, 0.0, 0.0)

    def magnitude(self) -> float:
        """
        Returns the magnitude of the vector.

        Returns:
            The magnitude of the vector.
        """
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2 + self.w ** 2)

    def normalize(self) -> Vector4:
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

    def set(self, x: float, y: float, z: float, w: float) -> None:
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

    def __init__(self, axis: Vector3, angle: float):
        self.axis: Vector3 = axis
        self.angle: float = angle

    @classmethod
    def from_quaternion(cls, quaternion: Vector4) -> AxisAngle:
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
    def from_null(cls) -> AxisAngle:
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


class Face:
    """
    Represents a triangle in 3D space.

    Attributes:
        v1: First point of the triangle.
        v2: Second point of the triangle.
        v3: Third point of the triangle.
        material: Material of the triangle, for usage in-game.
    """

    def __init__(self, v1: Vector3, v2: Vector3, v3: Vector3, material=SurfaceMaterial.UNDEFINED):
        self.v1: Vector3 = v1
        self.v2: Vector3 = v2
        self.v3: Vector3 = v3
        self.material: SurfaceMaterial = material

    def normal(self) -> Vector3:
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

        return normal
