"""Frustum culling implementation for PyKotorGL.

This module provides view frustum extraction and object culling to improve rendering
performance by skipping objects outside the camera's view.

Reference implementations:
- reone: src/graphics/renderpipeline.cpp (frustum culling logic)
- kotor.js: src/engine/camera.ts (view frustum extraction)
"""

from __future__ import annotations

import math
from enum import IntEnum
from typing import TYPE_CHECKING

import glm

from glm import mat4, vec3, vec4

if TYPE_CHECKING:
    from pykotor.gl.scene import Camera


class FrustumPlane(IntEnum):
    """Frustum plane indices."""
    LEFT = 0
    RIGHT = 1
    BOTTOM = 2
    TOP = 3
    NEAR = 4
    FAR = 5


class Frustum:
    """View frustum for culling objects outside the camera's view.
    
    The frustum is defined by 6 planes extracted from the view-projection matrix.
    Objects can be tested against these planes to determine visibility.
    
    Implementation based on:
    - Gribb/Hartmann method for frustum plane extraction
    - Reference: reone/src/graphics/renderpipeline.cpp line ~150
    """
    
    __slots__ = ("planes", "_cached_vp_hash")
    
    def __init__(self):
        """Initialize frustum with default planes."""
        # Each plane is stored as (nx, ny, nz, d) where n is normal, d is distance
        self.planes: list[vec4] = [vec4() for _ in range(6)]
        self._cached_vp_hash: int = 0
    
    def update_from_camera(self, camera: Camera) -> None:
        """Extract frustum planes from camera's view-projection matrix.
        
        Uses the Gribb/Hartmann method to extract planes directly from the
        combined view-projection matrix.
        
        Args:
            camera: The camera to extract frustum from.
        """
        view: mat4 = camera.view()
        proj: mat4 = camera.projection()
        vp: mat4 = proj * view
        
        # Check if matrices changed (simple hash check)
        vp_hash = hash((
            vp[0][0], vp[0][1], vp[0][2], vp[0][3],
            vp[1][0], vp[1][1], vp[1][2], vp[1][3],
            vp[2][0], vp[2][1], vp[2][2], vp[2][3],
            vp[3][0], vp[3][1], vp[3][2], vp[3][3],
        ))
        if vp_hash == self._cached_vp_hash:
            return
        self._cached_vp_hash = vp_hash
        
        # Extract planes using Gribb/Hartmann method
        # Left plane: row3 + row0
        self.planes[FrustumPlane.LEFT] = vec4(
            vp[0][3] + vp[0][0],
            vp[1][3] + vp[1][0],
            vp[2][3] + vp[2][0],
            vp[3][3] + vp[3][0],
        )
        
        # Right plane: row3 - row0
        self.planes[FrustumPlane.RIGHT] = vec4(
            vp[0][3] - vp[0][0],
            vp[1][3] - vp[1][0],
            vp[2][3] - vp[2][0],
            vp[3][3] - vp[3][0],
        )
        
        # Bottom plane: row3 + row1
        self.planes[FrustumPlane.BOTTOM] = vec4(
            vp[0][3] + vp[0][1],
            vp[1][3] + vp[1][1],
            vp[2][3] + vp[2][1],
            vp[3][3] + vp[3][1],
        )
        
        # Top plane: row3 - row1
        self.planes[FrustumPlane.TOP] = vec4(
            vp[0][3] - vp[0][1],
            vp[1][3] - vp[1][1],
            vp[2][3] - vp[2][1],
            vp[3][3] - vp[3][1],
        )
        
        # Near plane: row3 + row2
        self.planes[FrustumPlane.NEAR] = vec4(
            vp[0][3] + vp[0][2],
            vp[1][3] + vp[1][2],
            vp[2][3] + vp[2][2],
            vp[3][3] + vp[3][2],
        )
        
        # Far plane: row3 - row2
        self.planes[FrustumPlane.FAR] = vec4(
            vp[0][3] - vp[0][2],
            vp[1][3] - vp[1][2],
            vp[2][3] - vp[2][2],
            vp[3][3] - vp[3][2],
        )
        
        # Normalize all planes
        for i in range(6):
            self._normalize_plane(i)
    
    def _normalize_plane(self, index: int) -> None:
        """Normalize a frustum plane.
        
        Args:
            index: Index of the plane to normalize.
        """
        plane = self.planes[index]
        length = math.sqrt(plane.x * plane.x + plane.y * plane.y + plane.z * plane.z)
        if length > 1e-10:  # Use smaller epsilon for better precision
            inv_length = 1.0 / length
            self.planes[index] = vec4(
                plane.x * inv_length,
                plane.y * inv_length,
                plane.z * inv_length,
                plane.w * inv_length,
            )
        else:
            # Degenerate plane - set to a default that won't cull anything
            self.planes[index] = vec4(0.0, 0.0, 1.0, 1e10)
    
    def point_in_frustum(self, point: vec3) -> bool:
        """Test if a point is inside the frustum.
        
        Args:
            point: The point to test.
            
        Returns:
            True if the point is inside or on the frustum, False otherwise.
        """
        for plane in self.planes:
            # Distance from point to plane
            distance = plane.x * point.x + plane.y * point.y + plane.z * point.z + plane.w
            if distance < 0:
                return False
        return True
    
    def sphere_in_frustum(self, center: vec3, radius: float) -> bool:
        """Test if a bounding sphere intersects the frustum.
        
        This is the primary culling test used for render objects.
        
        Args:
            center: Center of the bounding sphere.
            radius: Radius of the bounding sphere.
            
        Returns:
            True if the sphere is at least partially inside the frustum.
        """
        for plane in self.planes:
            # Distance from sphere center to plane
            distance = plane.x * center.x + plane.y * center.y + plane.z * center.z + plane.w
            # If sphere is completely behind the plane, it's outside
            if distance < -radius:
                return False
        return True
    
    def aabb_in_frustum(
        self,
        min_point: vec3,
        max_point: vec3,
    ) -> bool:
        """Test if an axis-aligned bounding box intersects the frustum.
        
        Uses the plane-AABB intersection test for accurate culling.
        
        Args:
            min_point: Minimum corner of the AABB.
            max_point: Maximum corner of the AABB.
            
        Returns:
            True if the AABB is at least partially inside the frustum.
        """
        for plane in self.planes:
            # Find the positive vertex (furthest in plane normal direction)
            p_vertex = vec3(
                max_point.x if plane.x >= 0 else min_point.x,
                max_point.y if plane.y >= 0 else min_point.y,
                max_point.z if plane.z >= 0 else min_point.z,
            )
            
            # If the positive vertex is behind the plane, AABB is outside
            if plane.x * p_vertex.x + plane.y * p_vertex.y + plane.z * p_vertex.z + plane.w < 0:
                return False
        
        return True
    
    def sphere_in_frustum_distance(self, center: vec3, radius: float) -> float:
        """Get the minimum distance from sphere to any frustum plane.
        
        Useful for level-of-detail calculations.
        
        Args:
            center: Center of the bounding sphere.
            radius: Radius of the bounding sphere.
            
        Returns:
            Minimum signed distance. Negative means outside frustum.
        """
        min_distance = float("inf")
        
        for plane in self.planes:
            distance = plane.x * center.x + plane.y * center.y + plane.z * center.z + plane.w
            adjusted_distance = distance + radius
            min_distance = min(min_distance, adjusted_distance)
        
        return min_distance


class CullingStats:
    """Statistics for frustum culling performance monitoring."""
    
    __slots__ = ("total_objects", "culled_objects", "visible_objects", "frame_count")
    
    def __init__(self):
        self.total_objects: int = 0
        self.culled_objects: int = 0
        self.visible_objects: int = 0
        self.frame_count: int = 0
    
    def reset(self) -> None:
        """Reset statistics for a new frame."""
        self.total_objects = 0
        self.culled_objects = 0
        self.visible_objects = 0
    
    def record_object(self, *, visible: bool) -> None:
        """Record an object's visibility result.
        
        Args:
            visible: Whether the object was visible.
        """
        self.total_objects += 1
        if visible:
            self.visible_objects += 1
        else:
            self.culled_objects += 1
    
    def end_frame(self) -> None:
        """Mark end of frame for statistics."""
        self.frame_count += 1
    
    @property
    def cull_rate(self) -> float:
        """Get the percentage of objects culled.
        
        Returns:
            Percentage from 0 to 100.
        """
        if self.total_objects == 0:
            return 0.0
        return (self.culled_objects / self.total_objects) * 100.0
    
    def __repr__(self) -> str:
        return (
            f"CullingStats(total={self.total_objects}, visible={self.visible_objects}, "
            f"culled={self.culled_objects}, rate={self.cull_rate:.1f}%)"
        )

