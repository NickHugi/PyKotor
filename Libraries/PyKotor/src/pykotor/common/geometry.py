"""This module holds classes relating to geometry."""

from __future__ import annotations

import math

from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator


class Vector2:
    """Represents a 2 dimensional vector.

    Attributes:
    ----------
        x: The x component.
        y: The y component.
    """

    def __init__(
        self,
        x: float,
        y: float,
    ):
        self.x: float = x
        self.y: float = y

    def __iter__(
        self,
    ) -> Iterator[float]:
        return iter((self.x, self.y))

    def __repr__(
        self,
    ) -> str:
        return f"Vector2({self.x}, {self.y})"

    def __str__(
        self,
    ):
        """Returns the individual components separated by whitespace."""
        return f"{self.x} {self.y}"

    def __eq__(
        self,
        other,
    ):
        """Two Vector2 components are equal if their components are approximately the same."""
        if self is other:
            return True
        if not isinstance(other, Vector2):
            return NotImplemented

        isclose_x = math.isclose(self.x, other.x)
        isclose_y = math.isclose(self.y, other.y)
        return isclose_x and isclose_y

    def __add__(
        self,
        other,
    ):
        """Adds the components of two Vector2 objects."""
        if not isinstance(other, Vector2):
            return NotImplemented

        new = Vector2.from_vector2(self)
        new.x += other.x
        new.y += other.y
        return new

    def __sub__(
        self,
        other,
    ):
        """Subtracts the components of two Vector2 objects."""
        if not isinstance(other, Vector2):
            return NotImplemented

        new = Vector2.from_vector2(self)
        new.x -= other.x
        new.y -= other.y
        return new

    def __mul__(
        self,
        other,
    ):
        """Multiplies the components by a scalar integer."""
        if not isinstance(other, int):
            return NotImplemented

        new = Vector2.from_vector2(self)
        new.x *= other
        new.y *= other
        return new

    def __truediv__(
        self,
        other,
    ):
        """Performs element-wise true division of vector by scalar value.

        Args:
        ----
            self: The vector to be divided
            other: The scalar value to divide elements by

        Returns:
        -------
            new: A new vector with elements divided by the scalar value

        Processing Logic:
        ----------------
            - Check if other is an integer
            - Create a new vector from self
            - Divide x element by other
            - Divide y element by other
            - Return the new vector.
        """
        if isinstance(other, int):
            new = Vector2.from_vector2(self)
            new.x /= other
            new.y /= other
            return new
        return NotImplemented

    def __getitem__(
        self,
        item,
    ):
        if isinstance(item, int):
            if item == 0:
                return self.x
            if item == 1:
                return self.y
            raise KeyError
        return NotImplemented

    def __setitem__(
        self,
        key,
        value,
    ):
        if isinstance(key, int) and (isinstance(value, (float, int))):
            if key == 0:
                self.x = value
            elif key == 1:
                self.y = value
        return NotImplemented

    @classmethod
    def from_vector2(
        cls,
        other: Vector2,
    ) -> Vector2:
        """Returns a duplicate of the specified vector.

        Args:
        ----
            other: The vector to be duplicated.

        Returns:
        -------
            A new Vector2 object.
        """
        return Vector2(other.x, other.y)

    @classmethod
    def from_vector3(
        cls,
        other: Vector3,
    ) -> Vector2:
        """Returns a Vector2 object from the Vector3 object, discarding the Z-component.

        Args:
        ----
            other: The vector to be copied.

        Returns:
        -------
            A new Vector2 object.
        """
        return Vector2(other.x, other.y)

    @classmethod
    def from_vector4(
        cls,
        other: Vector4,
    ) -> Vector2:
        """Returns a Vector2 object from the Vector4 object, discarding the Z-component and W-components.

        Args:
        ----
            other: The vector to be copied.

        Returns:
        -------
            A new Vector2 object.
        """
        return Vector2(other.x, other.y)

    @classmethod
    def from_null(
        cls,
    ) -> Vector2:
        """Returns a new vector with a magnitude of zero.

        Returns:
        -------
            A new Vector2 instance.
        """
        return Vector2(0.0, 0.0)

    @classmethod
    def from_angle(
        cls,
        angle: float,
    ) -> Vector2:
        """Returns a unit vector based on the specified angle.

        Args:
        ----
            angle: The angle of the new vector in radians.

        Returns:
        -------
            A new Vector2 instance.
        """
        x = math.cos(angle)
        y = math.sin(angle)
        return Vector2(x, y).normal()

    def set_data(
        self,
        x: float,
        y: float,
    ):
        """Sets the components of the vector.

        Args:
        ----
            x: The new x component.
            y: The new y component.
        """
        self.x = x
        self.y = y

    def normalize(
        self,
    ):
        """Normalizes the vector so that the magnitude is equal to one while maintaining the same angle."""
        magnitude = self.magnitude()
        if magnitude == 0:
            self.x = 0
            self.y = 0
        else:
            self.x /= magnitude
            self.y /= magnitude

    def magnitude(
        self,
    ) -> float:
        """Returns the magnitude of the vector.

        Returns:
        -------
            The magnitude of the vector.
        """
        return math.sqrt(self.x**2 + self.y**2)

    def normal(
        self,
    ) -> Vector2:
        vec2 = Vector2.from_vector2(self)
        vec2.normalize()
        return vec2

    def dot(
        self,
        other: Vector2,
    ) -> float:
        """Returns the dot product between the two specified vectors.

        Args:
        ----
            other: The other vector.

        Returns:
        -------
            The dot product.
        """
        a = self.x * other.x
        b = self.y * other.y
        return a + b

    def distance(
        self,
        other: Vector2,
    ) -> float:
        """Returns the distance between two vectors.

        Args:
        ----
            other: The other vector.

        Returns:
        -------
            The distance between the vectors.
        """
        a = (self.x - other.x) ** 2
        b = (self.y - other.y) ** 2
        return math.sqrt(a + b)

    def within(
        self,
        container: list,
    ) -> bool:
        """Checks to see if the same Vector2 object in located in the specified list.

        This differs from using the 'in' keyword as that will return True for Vector2 objects that have simular coordinates.

        Args:
        ----
            container: The list to search in.

        Returns:
        -------
            True if the Vector2 exists in the container.
        """
        return any(item is self for item in container)

    def angle(
        self,
    ) -> float:
        """Returns the angle of the vector.

        Returns:
        -------
            The angle of the vector in radians.
        """
        return math.atan2(self.y, self.x)


class Vector3:
    """Represents a 3 dimensional vector.

    Attributes:
    ----------
        x: The x component.
        y: The y component.
        z: The z component.
    """

    def __init__(
        self,
        x: float,
        y: float,
        z: float,
    ):
        self.x: float = x
        self.y: float = y
        self.z: float = z

    def __iter__(
        self,
    ) -> Iterator[float]:
        return iter((self.x, self.y, self.z))

    def __repr__(
        self,
    ):
        return f"Vector3({self.x}, {self.y}, {self.z})"

    def __str__(
        self,
    ):
        """Returns the individual components as a string separated by whitespace."""
        return f"{self.x} {self.y} {self.z}"

    def __eq__(
        self,
        other: Vector3 | object,
    ) -> bool:
        """Two Vector3 components are equal if their components are approximately the same."""
        if self is other:
            return True
        if not isinstance(other, Vector3):
            return NotImplemented

        isclose_x = math.isclose(self.x, other.x)
        isclose_y = math.isclose(self.y, other.y)
        isclose_z = math.isclose(self.z, other.z)
        return isclose_x and isclose_y and isclose_z

    def __add__(
        self,
        other: Vector3,
    ) -> Vector3:
        """Adds the components of two Vector3 objects."""
        if not isinstance(other, Vector3):
            return NotImplemented

        new = Vector3.from_vector3(self)
        new.x += other.x
        new.y += other.y
        new.z += other.z
        return new

    def __sub__(
        self,
        other,
    ):
        """Subtracts the components of two Vector3 objects."""
        if not isinstance(other, Vector3):
            return NotImplemented

        new = Vector3.from_vector3(self)
        new.x -= other.x
        new.y -= other.y
        new.z -= other.z
        return new

    def __mul__(
        self,
        other: float,
    ) -> Vector3:
        """Multiplies the components by a scalar integer."""
        if isinstance(other, (int, float)):
            new = Vector3.from_vector3(self)
            new.x *= other
            new.y *= other
            new.z *= other
            return new
        return NotImplemented

    def __truediv__(
        self,
        other,
    ):
        if isinstance(other, int):
            new = Vector3.from_vector3(self)
            new.x /= other
            new.y /= other
            new.z /= other
            return new
        return NotImplemented

    def __getitem__(
        self,
        item: int,
    ) -> float:
        if isinstance(item, int):
            if item == 0:
                return self.x
            if item == 1:
                return self.y
            if item == 2:
                return self.z
            raise KeyError
        return NotImplemented

    def __setitem__(
        self,
        key,
        value,
    ):
        if isinstance(key, int) and (isinstance(value, (float, int))):
            if key == 0:
                self.x = value
                return None
            if key == 1:
                self.y = value
                return None
            if key == 2:
                self.z = value
                return None
            return None
        return NotImplemented

    @classmethod
    def from_vector2(
        cls,
        other: Vector2,
    ) -> Vector3:
        """Returns a Vector3 object from the Vector2 object, setting the Z-component to zero.

        Args:
        ----
            other: The vector to be copied.

        Returns:
        -------
            A new Vector3 object.
        """
        return Vector3(other.x, other.y, 0.0)

    @classmethod
    def from_vector3(
        cls,
        other: Vector3,
    ) -> Vector3:
        """Returns a duplicate of the specified vector.

        Args:
        ----
            other: The vector to be duplicated.

        Returns:
        -------
            A new Vector3 instance.
        """
        return Vector3(other.x, other.y, other.z)

    @classmethod
    def from_vector4(
        cls,
        other: Vector4,
    ) -> Vector3:
        """Returns a Vector3 object from the Vector4 object, discarding the W-component.

        Args:
        ----
            other: The vector to be copied.

        Returns:
        -------
            A new Vector3 object.
        """
        return Vector3(other.x, other.y, other.z)

    @classmethod
    def from_null(
        cls,
    ) -> Vector3:
        """Returns a new vector with a magnitude of zero.

        Returns:
        -------
            A new Vector3 instance.
        """
        return Vector3(0.0, 0.0, 0.0)

    def set_vector_coords(
        self,
        x: float,
        y: float,
        z: float,
    ):
        """Sets the components of the vector.

        Args:
        ----
            x: The new x component.
            y: The new y component.
            z: The new y component.
        """
        self.x = x
        self.y = y
        self.z = z

    def normalize(
        self,
    ):
        """Normalizes the vector so that the magnitude is equal to one while maintaining the same angle."""
        magnitude = self.magnitude()
        if magnitude == 0:
            self.x = 0
            self.y = 0
            self.z = 0
        else:
            self.x /= magnitude
            self.y /= magnitude
            self.z /= magnitude

    def magnitude(
        self,
    ) -> float:
        """Returns the magnitude of the vector.

        Returns:
        -------
            The magnitude of the vector.
        """
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def normal(
        self,
    ) -> Vector3:
        vec3 = Vector3.from_vector3(self)
        vec3.normalize()
        return vec3

    def dot(
        self,
        other: Vector3,
    ) -> float:
        """Returns the dot product between the two specified vectors.

        Args:
        ----
            other: The other vector.

        Returns:
        -------
            The dot product.
        """
        a = self.x * other.x
        b = self.y * other.y
        c = self.z * other.z
        return a + b + c

    def distance(
        self,
        other: Vector3,
    ) -> float:
        """Returns the distance between two vectors.

        Args:
        ----
            other: The other vector.

        Returns:
        -------
            The distance between the vectors.
        """
        a = (self.x - other.x) ** 2
        b = (self.y - other.y) ** 2
        c = (self.z - other.z) ** 2
        return math.sqrt(a + b + c)

    def within(
        self,
        container: list,
    ) -> bool:
        """Checks to see if the same Vector3 object in located in the specified list.

        This differs from using the 'in' keyword as that will return True for Vector3 objects that have similar coordinates.

        Args:
        ----
            container: The list to search in.

        Returns:
        -------
            True if the Vector3 exists in the container.
        """
        return any(item is self for item in container)


class Vector4:
    """Represents a 4 dimensional vector.

    Attributes:
    ----------
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
        w: float,
    ):
        self.x: float = x
        self.y: float = y
        self.z: float = z
        self.w: float = w

    def __iter__(
        self,
    ) -> Iterator[float]:
        return iter((self.x, self.y, self.z, self.w))

    def __repr__(
        self,
    ):
        return f"Vector4({self.x}, {self.y}, {self.z}, {self.w})"

    def __str__(
        self,
    ):
        """Returns the individual components as a string separated by whitespace."""
        return f"{self.x} {self.y} {self.z} {self.w}"

    def __eq__(
        self,
        other,
    ):
        """Two Vector4 components are equal if their components are approximately the same."""
        if self is other:
            return True
        if not isinstance(other, Vector4):
            return NotImplemented

        isclose_x = math.isclose(self.x, other.x)
        isclose_y = math.isclose(self.y, other.y)
        isclose_z = math.isclose(self.z, other.z)
        isclose_w = math.isclose(self.w, other.w)
        return isclose_x and isclose_y and isclose_z and isclose_w

    def __add__(
        self,
        other,
    ):
        """Adds the components of two Vector4 objects."""
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
        other,
    ):
        """Subtracts the components of two Vector4 objects."""
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
        other,
    ):
        """Multiplies the components by a scalar integer."""
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
        other: Vector2,
    ) -> Vector4:
        """Returns a Vector4 object from the Vector2 object, setting the Z-component and W-component to zero.

        Args:
        ----
            other: The vector to be copied.

        Returns:
        -------
            A new Vector4 object.
        """
        return Vector4(other.x, other.y, 0.0, 0.0)

    @classmethod
    def from_vector3(
        cls,
        other: Vector3,
    ) -> Vector4:
        """Returns a Vector4 object from the Vector3 object, setting the W-component to zero.

        Args:
        ----
            other: The vector to be copied.

        Returns:
        -------
            A new Vector4 object.
        """
        return Vector4(other.x, other.y, other.z, 0.0)

    @classmethod
    def from_vector4(
        cls,
        other: Vector4,
    ) -> Vector4:
        """Returns a duplicate of the specified vector.

        Args:
        ----
            other: The vector to be duplicated.

        Returns:
        -------
            A new Vector4 instance.
        """
        return Vector4(other.x, other.y, other.z, other.w)

    @classmethod
    def from_null(
        cls,
    ) -> Vector4:
        """Returns a new vector with a magnitude of zero.

        Returns:
        -------
            A new Vector4 instance.
        """
        return Vector4(0.0, 0.0, 0.0, 0.0)

    @classmethod
    def from_compressed(
        cls,
        data: int,
    ) -> Vector4:
        """Decompresses a compressed Vector4.

        Args:
        ----
            data: The compressed data as an integer

        Returns:
        -------
            Vector4: The decompressed Vector4

        Processing Logic:
        ----------------
            - Extract x, y, z components from data bits
            - Calculate w component from x, y, z
            - Normalize vector if magnitude is greater than 1
            - Return new Vector4 instance.
        """
        x = 1 - (data & 0x7FF) / 1023
        y = 1 - ((data >> 11) & 0x7FF) / 1023
        z = 1 - (data >> 22) / 511

        temp = x**2 + y**2 + z**2
        if temp < 1.0:
            w = -math.sqrt(1.0 - temp)
        else:
            temp = math.sqrt(temp)
            x /= temp
            y /= temp
            z /= temp
            w = 0

        return Vector4(x, y, z, w)

    @classmethod
    def from_euler(
        cls,
        x: float,
        y: float,
        z: float,
    ) -> Vector4:
        """Creates a Vector3 object from x/y/z rotations (in radians).

        Args:
        ----
            x: Roll
            y: Pitch
            z: Yaw

        Returns:
        -------
            A new Vector3 object.
        """
        roll: float = x
        pitch: float = y
        yaw: float = z

        qx: float = math.sin(roll / 2) * math.cos(pitch / 2) * math.cos(yaw / 2) - math.cos(roll / 2) * math.sin(pitch / 2) * math.sin(yaw / 2)
        qy: float = math.cos(roll / 2) * math.sin(pitch / 2) * math.cos(yaw / 2) + math.sin(roll / 2) * math.cos(pitch / 2) * math.sin(yaw / 2)
        qz: float = math.cos(roll / 2) * math.cos(pitch / 2) * math.sin(yaw / 2) - math.sin(roll / 2) * math.sin(pitch / 2) * math.cos(yaw / 2)
        qw: float = math.cos(roll / 2) * math.cos(pitch / 2) * math.cos(yaw / 2) + math.sin(roll / 2) * math.sin(pitch / 2) * math.sin(yaw / 2)

        return Vector4(qx, qy, qz, qw)

    def to_euler(
        self,
    ) -> Vector3:
        """Converts a quaternion to Euler angles.

        Args:
        ----
            self: Quaternion to convert

        Returns:
        -------
            Vector3: Converted Euler angles as roll, pitch, yaw

        Processing Logic:
        ----------------
            - Calculate roll by taking the atan2 of t0/t1 where t0 and t1 are functions of self.w, self.x, self.y, self.z
            - Calculate pitch by taking the asin of t2 where t2 is a function of self.w, self.y, self.z, with bounds checking
            - Calculate yaw by taking the atan2 of t3/t4 where t3 and t4 are functions of self.w, self.x, self.y, self.z
            - Return a Vector3 containing the calculated roll, pitch, yaw.
        """
        t0 = 2.0 * (self.w * self.x + self.y * self.z)
        t1 = 1 - 2 * (self.x * self.x + self.y * self.y)
        roll = math.atan2(t0, t1)

        t2 = 2 * (self.w * self.y - self.z * self.x)
        t2 = min(t2, 1)
        t2 = max(t2, -1)
        pitch = math.asin(t2)

        t3 = 2 * (self.w * self.z + self.x * self.y)
        t4 = 1 - 2 * (self.y * self.y + self.z * self.z)
        yaw = math.atan2(t3, t4)

        return Vector3(roll, pitch, yaw)

    def magnitude(
        self,
    ) -> float:
        """Returns the magnitude of the vector.

        Returns:
        -------
            The magnitude of the vector.
        """
        return math.sqrt(self.x**2 + self.y**2 + self.z**2 + self.w**2)

    def normalize(
        self,
    ) -> Vector4:
        """Normalizes the vector so that the magnitude is equal to one while maintaining the same angle.

        Returns:
        -------
            The same vector.
        """
        magnitude: float = self.magnitude()
        if magnitude == 0:
            self.x = 0
            self.y = 0
            self.z = 0
            self.w = 0
        else:
            self.x /= magnitude
            self.y /= magnitude
            self.z /= magnitude
            self.w /= magnitude
        return self

    def set_vector_coords(
        self,
        x: float,
        y: float,
        z: float,
        w: float,
    ):
        """Sets the components of the vector.

        Args:
        ----
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
    """Represents a rotation in 3D space.

    Attributes:
    ----------
        axis: The axis of rotation.
        angle: The magnitude of the rotation.
    """

    def __init__(
        self,
        axis: Vector3,
        angle: float,
    ):
        self.axis: Vector3 = axis
        self.angle: float = angle

    @classmethod
    def from_quaternion(
        cls,
        quaternion: Vector4,
    ) -> AxisAngle:
        """Returns a AxisAngle converted from a Vector4 quaternion.

        Args:
        ----
            quaternion: The quaternion.

        Returns:
        -------
            A new AxisAngle instance.
        """
        aa: AxisAngle = AxisAngle.from_null()
        quaternion.normalize()

        aa.angle = 2.0 * math.atan2(
            Vector3(quaternion.x, quaternion.y, quaternion.z).magnitude(),
            quaternion.w,
        )

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
        cls,
    ) -> AxisAngle:
        """Returns a AxisAngle that contains no rotation.

        Returns:
        -------
            A new AxisAngle instance.
        """
        return AxisAngle(Vector3.from_null(), 0.0)


class SurfaceMaterial(IntEnum):
    """The surface materials for walkmeshes found in both games."""

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
    SURFACE_MATERIAL_20 = 20
    SURFACE_MATERIAL_21 = 21
    SURFACE_MATERIAL_22 = 22
    SURFACE_MATERIAL_23 = 23
    SURFACE_MATERIAL_24 = 24
    SURFACE_MATERIAL_25 = 25
    SURFACE_MATERIAL_26 = 26
    SURFACE_MATERIAL_27 = 27
    SURFACE_MATERIAL_28 = 28
    SURFACE_MATERIAL_29 = 29
    TRIGGER = 30

    def walkable(
        self,
    ) -> bool:
        """Returns True if the surface material is walkable, False otherwise."""
        return self in {
            SurfaceMaterial.DIRT,
            SurfaceMaterial.GRASS,
            SurfaceMaterial.STONE,
            SurfaceMaterial.WOOD,
            SurfaceMaterial.WATER,
            SurfaceMaterial.CARPET,
            SurfaceMaterial.METAL,
            SurfaceMaterial.PUDDLES,
            SurfaceMaterial.SWAMP,
            SurfaceMaterial.MUD,
            SurfaceMaterial.LEAVES,
            SurfaceMaterial.DOOR,
            SurfaceMaterial.TRIGGER,
        }


class Face:
    """Represents a triangle in 3D space.

    Attributes:
    ----------
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
        material: SurfaceMaterial = SurfaceMaterial.UNDEFINED,
    ):
        self.v1: Vector3 = v1
        self.v2: Vector3 = v2
        self.v3: Vector3 = v3
        self.material: SurfaceMaterial = material

    def normal(
        self,
    ) -> Vector3:
        """Returns the normal for the face.

        Returns:
        -------
            A new Vector3 instance representing the face normal.
        """
        u: Vector3 = self.v2 - self.v1
        v: Vector3 = self.v3 - self.v2

        normal: Vector3 = Vector3.from_null()
        normal.x = (u.y * v.z) - (u.z * v.y)
        normal.y = (u.z * v.x) - (u.x * v.z)
        normal.z = (u.x * v.y) - (u.y * v.x)
        normal.normalize()

        return normal

    def area(
        self,
    ) -> float:
        a = self.v1.distance(self.v2)
        b = self.v1.distance(self.v3)
        c = self.v2.distance(self.v3)
        return 0.25 * math.sqrt((a + b + c) * (-a + b + c) * (a - b + c) * (a + b - c))

    def planar_distance(
        self,
    ) -> float:
        return -1.0 * (self.normal().dot(self.v1))

    def centre(
        self,
    ) -> Vector3:
        return (self.v1 + self.v2 + self.v3) / 3

    def average(
        self,
    ) -> Vector3:
        """Returns the average point of the face.

        Returns:
        -------
            A vector representing the average point of the face.
        """
        return (self.v1 + self.v2 + self.v3) / 3

    def determine_z(
        self,
        x: float,
        y: float,
    ) -> float:
        """Returns the Z-component determined from the given X and Y components.

        This method does not check if the point exists within the face, that must be done separately with inside().

        Returns:
        -------
            The Z-component.
        """
        dx1 = x - self.v1.x
        dy1 = y - self.v1.y
        dx2 = self.v2.x - self.v1.x
        dy2 = self.v2.y - self.v1.y
        dx3 = self.v3.x - self.v1.x
        dy3 = self.v3.z - self.v1.y
        scale = dx3 * dy2 - dx2 * dy3
        nx = (dx1 * dy2 - dy1 * dx2) / scale
        ny = (dy1 * dx3 - dx1 * dy3) / scale
        return self.v1.z + ny * (self.v2.z - self.v1.z) + nx * (self.v3.z - self.v1.z)


class Polygon2:
    def __init__(
        self,
        points: list[Vector2] | None = None,
    ):
        self.points: list[Vector2] = [] if points is None else points

    def __iter__(
        self,
    ) -> Iterator[Vector2]:
        yield from self.points

    def __len__(
        self,
    ) -> int:
        return len(self.points)

    def __repr__(
        self,
    ) -> str:
        return f"Polygon2({self.points})"

    def __getitem__(
        self,
        item: int | slice,
    ) -> Vector2 | list[Vector2]:
        if isinstance(item, int):
            return self.points[item]
        if isinstance(item, slice):
            return self.points[item.start : item.stop : item.step]
        return NotImplemented

    def __setitem__(
        self,
        key: int,
        value: Vector2,
    ):
        if isinstance(key, int) and isinstance(value, Vector2):
            self.points[key] = value
        return NotImplemented

    @classmethod
    def from_polygon3(
        cls,
        poly3: Polygon3,
    ) -> Polygon2:
        """Converts a Polygon3 object into a Polygon2 object. The Z-axis is removed.

        Args:
        ----
            poly3: The polygon3 object to flatten.

        Returns:
        -------
            A Polygon2 object.
        """
        poly2 = Polygon2()
        for point in poly3:
            poly2.points.append(Vector2(point.x, point.y))
        return poly2

    def inside(
        self,
        point: Vector2,
        include_edges: bool = True,
    ) -> bool:
        """Returns if the specified point is inside the polygon.

        Args:
        ----
            point: The point.
            include_edges: If True, a points on edges are considered inside the polygon.

        Returns:
        -------
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
                    if point.x < min(p1.x, p2.x):
                        inside = not inside
            elif min(p1.y, p2.y) <= point.y <= max(p1.y, p2.y):
                xinters = (point.y - p1.y) * (p2.x - p1.x) / float(p2.y - p1.y) + p1.x

                if point.x == xinters:
                    inside = include_edges
                    break

                if point.x < xinters:
                    inside = not inside
            p1 = p2
        return inside

    def area(
        self,
    ) -> float:
        """Calculates the area of a polygon.

        Args:
        ----
            self: The polygon object

        Returns:
        -------
            float: The calculated area of the polygon

        Processing Logic:
        ----------------
            - Loops through points calculating trianglular areas
            - Sums all triangular areas
            - Returns absolute value of the calculated area to ensure positivity.
        """
        # Code was adapted from this stackoverflow post:
        # https://stackoverflow.com/a/34327761

        n = len(self.points)
        area = 0.0
        for i in range(n - 1):
            area += -self.points[i].y * self.points[i + 1].x + self.points[i].x * self.points[i + 1].y
        area += -self.points[n - 1].y * self.points[0].x + self.points[n - 1].x * self.points[0].y
        return 0.5 * math.fabs(area)

    def append(
        self,
        point: Vector2,
    ):
        self.points.append(point)

    def extend(
        self,
        points: list[Vector2],
    ):
        self.points.extend(points)

    def remove(
        self,
        point: Vector2,
    ):
        self.points.remove(point)

    def index(
        self,
        point: Vector2,
    ) -> int:
        return self.points.index(point)


class Polygon3:
    def __init__(
        self,
        points: list[Vector3] | None = None,
    ):
        self.points: list[Vector3] = [] if points is None else points

    def __iter__(
        self,
    ) -> Iterator[Vector3]:
        yield from self.points

    def __len__(
        self,
    ) -> int:
        return len(self.points)

    def __repr__(
        self,
    ):
        return f"Polygon3({self.points})"

    def __getitem__(
        self,
        item: int | slice,
    ):
        if isinstance(item, int):
            return self.points[item]
        if isinstance(item, slice):
            return self.points[item.start : item.stop : item.step]
        return NotImplemented

    def __setitem__(
        self,
        key: int,
        value: Vector3,
    ):
        if isinstance(key, int) and isinstance(value, Vector3):
            self.points[key] = value
        return NotImplemented

    @classmethod
    def from_polygon2(
        cls,
        poly2: Polygon2,
    ) -> Polygon3:
        """Converts a Polygon3 object into a Polygon2 object. Points have their Z-axis set to 0.

        Args:
        ----
            poly2: The polygon3 object to copy.

        Returns:
        -------
            A Polygon3 object with the Z-axis of its points set to 0.
        """
        poly3 = Polygon3()
        for point in poly2.points:
            poly3.points.append(Vector3(point.x, point.y, 0))
        return poly3

    def create_triangle(
        self,
        size: float = 1.0,
        origin: Vector3 | tuple[float, float, float] = (0.0, 0.0, 0.0),
    ):
        """Creates an equilateral triangle in the XY-plane with the given size and the bottom vertex at the specified origin.

        Args:
        ----
            size: The length of each side of the triangle.
            origin: A tuple representing the (x, y, z) coordinates of the bottom vertex of the triangle.

        This method modifies the instance by adding three Vector3 points defining the triangle.
        """
        x, y, z = origin
        height = size * (3 ** 0.5) / 2
        self.points = [
            Vector3(x, y, z),
            Vector3(x + size, y, z),
            Vector3(x + size / 2, y + height, z)
        ]

    def default_square(
        self,
        size: float = 1.0,
        origin: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ):
        """Creates a square in the XY-plane with the given size and the bottom-left corner at the specified origin.

        Args:
        ----
            size: The length of each side of the square.
            origin: A tuple representing the (x, y, z) coordinates of the bottom-left corner of the square.

        This method modifies the instance by adding four Vector3 points defining the square.
        """
        x, y, z = origin
        self.points = [
            Vector3(x, y, z),
            Vector3(x + size, y, z),
            Vector3(x + size, y + size, z),
            Vector3(x, y + size, z)
        ]

    def append(
        self,
        point: Vector3,
    ):
        self.points.append(point)

    def extend(
        self,
        points: list[Vector3],
    ):
        self.points.extend(points)

    def remove(
        self,
        point: Vector3,
    ):
        self.points.remove(point)

    def index(
        self,
        point: Vector3,
    ) -> int:
        return self.points.index(point)

def get_aurora_scale(obj):
    """If the scale is uniform, i.e, x=y=z, we will return
    the value. Else we'll return 1.
    """
    scale = obj.scale
    if (scale[0] == scale[1] == scale[2]):
        return scale[0]

    return 1.0

def get_aurora_rot_from_object(obj):
    q = obj.rotation_quaternion
    return [q.axis[0], q.axis[1], q.axis[2], q.angle]