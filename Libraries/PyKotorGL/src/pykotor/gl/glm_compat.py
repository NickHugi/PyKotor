"""GLM compatibility layer using NumPy for PyPy support.

This module provides a PyGLM-compatible API using NumPy arrays,
allowing PyKotorGL to work with PyPy where PyGLM is not available.

Note: All classes intentionally use lowercase names to match PyGLM's API.
Private _data members are intentionally accessed for internal operations.
"""
# ruff: noqa: SLF001

from __future__ import annotations

import math

from typing import TYPE_CHECKING, overload

import numpy as np

if TYPE_CHECKING:
    from numpy import ndarray

try:
    import glm
except ImportError:
    class vec3:  # noqa: N801
        """3D vector class compatible with PyGLM vec3."""

        def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
            if isinstance(x, (vec3, np.ndarray)):
                self._data: ndarray = np.array(x._data if isinstance(x, vec3) else x, dtype=np.float32)  # noqa: SLF001
            else:
                self._data = np.array([x, y, z], dtype=np.float32)

        @property
        def x(self) -> float:
            return float(self._data[0])

        @x.setter
        def x(self, value: float):
            self._data[0] = value

        @property
        def y(self) -> float:
            return float(self._data[1])

        @y.setter
        def y(self, value: float):
            self._data[1] = value

        @property
        def z(self) -> float:
            return float(self._data[2])

        @z.setter
        def z(self, value: float):
            self._data[2] = value

        def __repr__(self) -> str:
            return f"vec3({self.x}, {self.y}, {self.z})"

        def __eq__(self, other: object) -> bool:
            if not isinstance(other, vec3):
                return NotImplemented
            return bool(np.allclose(self._data, other._data))

        def __hash__(self) -> int:
            return hash(tuple(self._data.flatten()))


    class vec4:  # noqa: N801
        """4D vector class compatible with PyGLM vec4."""

        def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0, w: float = 0.0):
            if isinstance(x, (vec4, np.ndarray)):
                self._data: ndarray = np.array(x._data if isinstance(x, vec4) else x, dtype=np.float32)  # noqa: SLF001
            else:
                self._data = np.array([x, y, z, w], dtype=np.float32)

        @property
        def x(self) -> float:
            return float(self._data[0])

        @x.setter
        def x(self, value: float):
            self._data[0] = value

        @property
        def y(self) -> float:
            return float(self._data[1])

        @y.setter
        def y(self, value: float):
            self._data[1] = value

        @property
        def z(self) -> float:
            return float(self._data[2])

        @z.setter
        def z(self, value: float):
            self._data[2] = value

        @property
        def w(self) -> float:
            return float(self._data[3])

        @w.setter
        def w(self, value: float):
            self._data[3] = value

        def __repr__(self) -> str:
            return f"vec4({self.x}, {self.y}, {self.z}, {self.w})"

        def __eq__(self, other: object) -> bool:
            if not isinstance(other, vec4):
                return NotImplemented
            return bool(np.allclose(self._data, other._data))

        def __hash__(self) -> int:
            return hash(tuple(self._data.flatten()))


    class quat:  # noqa: N801
        """Quaternion class compatible with PyGLM quat."""

        def __init__(self, w: float = 1.0, x: float = 0.0, y: float = 0.0, z: float = 0.0):
            if isinstance(w, quat):
                self._data: ndarray = np.array(w._data, dtype=np.float32)  # noqa: SLF001
            elif isinstance(w, vec3):
                # vec3 - Euler angles
                self._data = self._from_euler(w)._data  # noqa: SLF001
            else:
                # w, x, y, z format
                self._data = np.array([w, x, y, z], dtype=np.float32)

        @staticmethod
        def _from_euler(euler: vec3) -> quat:
            """Create quaternion from Euler angles (in radians)."""
            cy = math.cos(euler.z * 0.5)
            sy = math.sin(euler.z * 0.5)
            cp = math.cos(euler.y * 0.5)
            sp = math.sin(euler.y * 0.5)
            cr = math.cos(euler.x * 0.5)
            sr = math.sin(euler.x * 0.5)

            w = cr * cp * cy + sr * sp * sy
            x = sr * cp * cy - cr * sp * sy
            y = cr * sp * cy + sr * cp * sy
            z = cr * cp * sy - sr * sp * cy

            return quat(w, x, y, z)

        @property
        def w(self) -> float:
            return float(self._data[0])

        @w.setter
        def w(self, value: float):
            self._data[0] = value

        @property
        def x(self) -> float:
            return float(self._data[1])

        @x.setter
        def x(self, value: float):
            self._data[1] = value

        @property
        def y(self) -> float:
            return float(self._data[2])

        @y.setter
        def y(self, value: float):
            self._data[2] = value

        @property
        def z(self) -> float:
            return float(self._data[3])

        @z.setter
        def z(self, value: float):
            self._data[3] = value

        def __repr__(self) -> str:
            return f"quat({self.w}, {self.x}, {self.y}, {self.z})"

        def __eq__(self, other: object) -> bool:
            if not isinstance(other, quat):
                return NotImplemented
            return bool(np.allclose(self._data, other._data))

        def __hash__(self) -> int:
            return hash(tuple(self._data.flatten()))


    class mat4:  # noqa: N801
        """4x4 matrix class compatible with PyGLM mat4."""

        def __init__(self, value: float | mat4 | np.ndarray = 1.0):
            if isinstance(value, (mat4, np.ndarray)):
                self._data: ndarray = np.array(value._data if isinstance(value, mat4) else value, dtype=np.float32)  # noqa: SLF001
            else:
                # Identity matrix scaled by value
                self._data = np.eye(4, dtype=np.float32) * value

        @overload
        def __mul__(self, other: mat4) -> mat4: ...

        @overload
        def __mul__(self, other: vec4) -> vec4: ...

        @overload
        def __mul__(self, other: vec3) -> vec3: ...

        def __mul__(self, other: mat4 | vec3 | vec4) -> mat4 | vec3 | vec4:
            if isinstance(other, mat4):
                result = mat4()
                result._data = np.matmul(self._data, other._data)
                return result
            if isinstance(other, vec4):
                result_data = np.matmul(self._data, other._data)
                return vec4(result_data[0], result_data[1], result_data[2], result_data[3])
            if isinstance(other, vec3):
                # Treat vec3 as vec4 with w=1
                vec4_data = np.array([other.x, other.y, other.z, 1.0], dtype=np.float32)
                result_data = np.matmul(self._data, vec4_data)
                return vec3(result_data[0], result_data[1], result_data[2])
            return NotImplemented

        def __repr__(self) -> str:
            return f"mat4(\n{self._data}\n)"

        def __eq__(self, other: object) -> bool:
            if not isinstance(other, mat4):
                return NotImplemented
            return bool(np.allclose(self._data, other._data))

        def __hash__(self) -> int:
            return hash(tuple(self._data.flatten()))


def translate(v: vec3) -> mat4:
    """Create a translation matrix."""
    result = mat4()
    result._data[3, 0] = v.x
    result._data[3, 1] = v.y
    result._data[3, 2] = v.z
    return result


def rotate(m: mat4, angle: float, axis: vec3) -> mat4:
    """Rotate a matrix by angle (radians) around axis."""
    # Normalize axis
    axis_length = math.sqrt(axis.x**2 + axis.y**2 + axis.z**2)
    if axis_length == 0:
        return mat4(m)

    x = axis.x / axis_length
    y = axis.y / axis_length
    z = axis.z / axis_length

    c = math.cos(angle)
    s = math.sin(angle)
    t = 1 - c

    # Rotation matrix
    rot = mat4()
    rot._data[0, 0] = t * x * x + c
    rot._data[0, 1] = t * x * y + s * z
    rot._data[0, 2] = t * x * z - s * y
    rot._data[1, 0] = t * x * y - s * z
    rot._data[1, 1] = t * y * y + c
    rot._data[1, 2] = t * y * z + s * x
    rot._data[2, 0] = t * x * z + s * y
    rot._data[2, 1] = t * y * z - s * x
    rot._data[2, 2] = t * z * z + c

    return m * rot


def mat4_cast(q: quat) -> mat4:
    """Convert a quaternion to a 4x4 rotation matrix."""
    result = mat4()

    qw, qx, qy, qz = q.w, q.x, q.y, q.z

    result._data[0, 0] = 1 - 2 * qy * qy - 2 * qz * qz
    result._data[0, 1] = 2 * qx * qy + 2 * qz * qw
    result._data[0, 2] = 2 * qx * qz - 2 * qy * qw

    result._data[1, 0] = 2 * qx * qy - 2 * qz * qw
    result._data[1, 1] = 1 - 2 * qx * qx - 2 * qz * qz
    result._data[1, 2] = 2 * qy * qz + 2 * qx * qw

    result._data[2, 0] = 2 * qx * qz + 2 * qy * qw
    result._data[2, 1] = 2 * qy * qz - 2 * qx * qw
    result._data[2, 2] = 1 - 2 * qx * qx - 2 * qy * qy

    return result


def inverse(m: mat4) -> mat4:
    """Calculate the inverse of a matrix."""
    result = mat4()
    try:
        result._data = np.linalg.inv(m._data)
    except np.linalg.LinAlgError:
        # Return identity matrix if singular
        result._data = np.eye(4, dtype=np.float32)
    return result


def perspective(fov: float, aspect: float, near: float, far: float) -> mat4:
    """Create a perspective projection matrix.

    Args:
    ----
        fov: Field of view in degrees
        aspect: Aspect ratio (width/height)
        near: Near clipping plane
        far: Far clipping plane

    Returns:
    -------
        mat4: Perspective projection matrix

    """
    result = mat4(0.0)

    fov_rad = math.radians(fov)
    tan_half_fov = math.tan(fov_rad / 2.0)

    result._data[0, 0] = 1.0 / (aspect * tan_half_fov)
    result._data[1, 1] = 1.0 / tan_half_fov
    result._data[2, 2] = -(far + near) / (far - near)
    result._data[2, 3] = -1.0
    result._data[3, 2] = -(2.0 * far * near) / (far - near)

    return result


def normalize(v: vec3) -> vec3:
    """Normalize a vector."""
    length = math.sqrt(v.x**2 + v.y**2 + v.z**2)
    if length == 0:
        return vec3(0, 0, 0)
    return vec3(v.x / length, v.y / length, v.z / length)


def cross(a: vec3, b: vec3) -> vec3:
    """Calculate the cross product of two vectors."""
    return vec3(
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x,
    )


def decompose(
    transform: mat4,
    scale: vec3,
    rotation: quat,
    translation: vec3,
    skew: vec3,  # noqa: ARG001
    perspective: vec4,  # noqa: ARG001
) -> bool:
    """Decompose a transformation matrix into its components.

    Args:
    ----
        transform: The transformation matrix to decompose
        scale: Output scale vector
        rotation: Output rotation quaternion
        translation: Output translation vector
        skew: Output skew vector (not implemented)
        perspective: Output perspective vector (not implemented)

    Returns:
    -------
        bool: True if decomposition was successful

    """
    m = transform._data

    # Extract translation
    translation.x = m[3, 0]
    translation.y = m[3, 1]
    translation.z = m[3, 2]

    # Extract scale
    scale_x = math.sqrt(m[0, 0]**2 + m[0, 1]**2 + m[0, 2]**2)
    scale_y = math.sqrt(m[1, 0]**2 + m[1, 1]**2 + m[1, 2]**2)
    scale_z = math.sqrt(m[2, 0]**2 + m[2, 1]**2 + m[2, 2]**2)

    scale.x = scale_x
    scale.y = scale_y
    scale.z = scale_z

    # Normalize matrix to extract rotation
    if scale_x == 0 or scale_y == 0 or scale_z == 0:
        rotation.w = 1.0
        rotation.x = 0.0
        rotation.y = 0.0
        rotation.z = 0.0
        return True

    rot_matrix = np.array([
        [m[0, 0] / scale_x, m[0, 1] / scale_x, m[0, 2] / scale_x],
        [m[1, 0] / scale_y, m[1, 1] / scale_y, m[1, 2] / scale_y],
        [m[2, 0] / scale_z, m[2, 1] / scale_z, m[2, 2] / scale_z],
    ], dtype=np.float32)

    # Convert rotation matrix to quaternion
    trace = rot_matrix[0, 0] + rot_matrix[1, 1] + rot_matrix[2, 2]

    if trace > 0:
        s = math.sqrt(trace + 1.0) * 2
        rotation.w = 0.25 * s
        rotation.x = (rot_matrix[2, 1] - rot_matrix[1, 2]) / s
        rotation.y = (rot_matrix[0, 2] - rot_matrix[2, 0]) / s
        rotation.z = (rot_matrix[1, 0] - rot_matrix[0, 1]) / s
    elif rot_matrix[0, 0] > rot_matrix[1, 1] and rot_matrix[0, 0] > rot_matrix[2, 2]:
        s = math.sqrt(1.0 + rot_matrix[0, 0] - rot_matrix[1, 1] - rot_matrix[2, 2]) * 2
        rotation.w = (rot_matrix[2, 1] - rot_matrix[1, 2]) / s
        rotation.x = 0.25 * s
        rotation.y = (rot_matrix[0, 1] + rot_matrix[1, 0]) / s
        rotation.z = (rot_matrix[0, 2] + rot_matrix[2, 0]) / s
    elif rot_matrix[1, 1] > rot_matrix[2, 2]:
        s = math.sqrt(1.0 + rot_matrix[1, 1] - rot_matrix[0, 0] - rot_matrix[2, 2]) * 2
        rotation.w = (rot_matrix[0, 2] - rot_matrix[2, 0]) / s
        rotation.x = (rot_matrix[0, 1] + rot_matrix[1, 0]) / s
        rotation.y = 0.25 * s
        rotation.z = (rot_matrix[1, 2] + rot_matrix[2, 1]) / s
    else:
        s = math.sqrt(1.0 + rot_matrix[2, 2] - rot_matrix[0, 0] - rot_matrix[1, 1]) * 2
        rotation.w = (rot_matrix[1, 0] - rot_matrix[0, 1]) / s
        rotation.x = (rot_matrix[0, 2] + rot_matrix[2, 0]) / s
        rotation.y = (rot_matrix[1, 2] + rot_matrix[2, 1]) / s
        rotation.z = 0.25 * s

    return True


def eulerAngles(q: quat) -> vec3:
    """Convert a quaternion to Euler angles (in radians).

    Args:
    ----
        q: Input quaternion

    Returns:
    -------
        vec3: Euler angles (roll, pitch, yaw) in radians

    """
    # Roll (x-axis rotation)
    sinr_cosp = 2 * (q.w * q.x + q.y * q.z)
    cosr_cosp = 1 - 2 * (q.x * q.x + q.y * q.y)
    roll = math.atan2(sinr_cosp, cosr_cosp)

    # Pitch (y-axis rotation)
    sinp = 2 * (q.w * q.y - q.z * q.x)
    if abs(sinp) >= 1:
        pitch = math.copysign(math.pi / 2, sinp)
    else:
        pitch = math.asin(sinp)

    # Yaw (z-axis rotation)
    siny_cosp = 2 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
    yaw = math.atan2(siny_cosp, cosy_cosp)

    return vec3(roll, pitch, yaw)


def value_ptr(obj: mat4 | vec3 | vec4) -> np.ndarray:
    """Get a pointer to the underlying data (returns flattened numpy array).

    Args:
    ----
        obj: Matrix or vector to get pointer from

    Returns:
    -------
        np.ndarray: Flattened array of the data

    """
    if isinstance(obj, mat4):
        # OpenGL expects column-major order
        return np.ascontiguousarray(obj._data.T.flatten())
    return np.ascontiguousarray(obj._data.flatten())


def unProject(
    win: vec3,
    model: mat4,
    proj: mat4,
    viewport: tuple[int, int, int, int],
) -> vec3:
    """Unproject a window coordinate to world coordinates.

    Args:
    ----
        win: Window coordinates (x, y, z where z is depth)
        model: Model-view matrix
        proj: Projection matrix
        viewport: Viewport as (x, y, width, height)

    Returns:
    -------
        vec3: World coordinates

    """
    # Compute the inverse of model * projection
    m: mat4 = proj * model  # type: ignore[assignment]
    inv_m: mat4 = inverse(m)

    # Normalize window coordinates to NDC [-1, 1]
    ndc = vec4(
        (win.x - viewport[0]) / viewport[2] * 2.0 - 1.0,
        (win.y - viewport[1]) / viewport[3] * 2.0 - 1.0,
        2.0 * win.z - 1.0,
        1.0,
    )

    # Transform NDC to world coordinates
    world: vec4 = inv_m * ndc  # type: ignore[assignment]

    # Perspective divide
    if world.w != 0:
        world.x /= world.w
        world.y /= world.w
        world.z /= world.w

    return vec3(world.x, world.y, world.z)

