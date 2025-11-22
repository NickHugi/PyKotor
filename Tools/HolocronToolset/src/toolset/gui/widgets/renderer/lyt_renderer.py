"""LYT (Layout) renderer for visualizing and editing module layouts.

This module provides rendering and interaction capabilities for LYT files,
matching the functionality of kotorblender's LYT operations.

Based on:
    vendor/kotorblender/io_scene_kotor/io/lyt.py - LYT import/export
    vendor/kotorblender/io_scene_kotor/ops/lyt/ - LYT operations
"""

from __future__ import annotations

import math

from typing import TYPE_CHECKING

from qtpy.QtCore import Qt, Signal
from qtpy.QtGui import QBrush, QColor, QPainter, QPen, QTransform
from qtpy.QtWidgets import QWidget

from pykotor.resource.formats.lyt import LYT, LYTDoorHook, LYTObstacle, LYTRoom, LYTTrack
from utility.common.geometry import Vector2, Vector3, Vector4

if TYPE_CHECKING:
    from qtpy.QtGui import QMouseEvent, QPaintEvent, QWheelEvent

    from pykotor.common.module import Module


class LYTRenderer(QWidget):
    """Widget for rendering and editing LYT layout elements.
    
    Provides 2D visualization of rooms, door hooks, tracks, and obstacles
    matching kotorblender's visual representation.
    """

    # Signals
    sig_element_selected = Signal(object)  # Emits selected LYT element
    sig_element_moved = Signal(object, Vector3)  # Emits element and new position
    sig_element_added = Signal(object)  # Emits newly added element
    sig_element_deleted = Signal(object)  # Emits deleted element

    # Visual constants matching kotorblender style
    ROOM_COLOR = QColor(100, 100, 200, 150)
    ROOM_SELECTED_COLOR = QColor(150, 150, 255, 200)
    ROOM_BORDER_COLOR = QColor(50, 50, 100, 255)
    ROOM_SIZE = 50.0  # Default room size for visualization

    DOORHOOK_COLOR = QColor(0, 255, 0, 200)
    DOORHOOK_SELECTED_COLOR = QColor(100, 255, 100, 255)
    DOORHOOK_SIZE = 10.0

    TRACK_COLOR = QColor(255, 200, 0, 150)
    TRACK_SELECTED_COLOR = QColor(255, 255, 100, 255)
    TRACK_SIZE = 30.0

    OBSTACLE_COLOR = QColor(255, 0, 0, 150)
    OBSTACLE_SELECTED_COLOR = QColor(255, 100, 100, 255)
    OBSTACLE_SIZE = 40.0

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setMouseTracking(True)

        # Layout data
        self._lyt: LYT | None = None
        self._module: Module | None = None

        # Selection and interaction
        self._selected_element: LYTRoom | LYTDoorHook | LYTTrack | LYTObstacle | None = None
        self._dragging: bool = False
        self._drag_start_pos: Vector2 | None = None
        self._element_start_pos: Vector3 | None = None

        # Camera/view
        self._camera_pos: Vector2 = Vector2(0, 0)
        self._zoom: float = 1.0
        self._mouse_prev: Vector2 = Vector2(0, 0)
        self._panning: bool = False

    def set_lyt(self, lyt: LYT | None):
        """Set the LYT data to display."""
        self._lyt = lyt
        self.update()

    def set_module(self, module: Module | None):
        """Set the module for context."""
        self._module = module
        if module:
            layout_resource = module.layout()
            if layout_resource:
                self._lyt = layout_resource.resource()
        self.update()

    def get_selected_element(self) -> LYTRoom | LYTDoorHook | LYTTrack | LYTObstacle | None:
        """Get the currently selected element."""
        return self._selected_element

    def select_element(self, element: LYTRoom | LYTDoorHook | LYTTrack | LYTObstacle | None):
        """Set the selected element."""
        self._selected_element = element
        self.sig_element_selected.emit(element)
        self.update()

    def add_room(self, position: Vector3 | None = None) -> LYTRoom:
        """Add a new room at the specified position."""
        if self._lyt is None:
            self._lyt = LYT()

        if position is None:
            # Place at camera center
            position = Vector3(self._camera_pos.x, self._camera_pos.y, 0)

        room = LYTRoom("newroom", position)
        self._lyt.rooms.append(room)
        self.sig_element_added.emit(room)
        self.update()
        return room

    def add_doorhook(self, room: LYTRoom | None = None, position: Vector3 | None = None) -> LYTDoorHook:
        """Add a new door hook."""
        if self._lyt is None:
            self._lyt = LYT()

        if room is None and self._lyt.rooms:
            room = self._lyt.rooms[0]

        if position is None:
            position = Vector3(self._camera_pos.x, self._camera_pos.y, 0)

        room_name = room.model if room else "NULL"
        doorhook = LYTDoorHook(room_name, f"door{len(self._lyt.doorhooks)}", position, Vector4(0, 0, 0, 1))
        self._lyt.doorhooks.append(doorhook)
        self.sig_element_added.emit(doorhook)
        self.update()
        return doorhook

    def add_track(self, position: Vector3 | None = None) -> LYTTrack:
        """Add a new track."""
        if self._lyt is None:
            self._lyt = LYT()

        if position is None:
            position = Vector3(self._camera_pos.x, self._camera_pos.y, 0)

        track = LYTTrack("newtrack", position)
        self._lyt.tracks.append(track)
        self.sig_element_added.emit(track)
        self.update()
        return track

    def add_obstacle(self, position: Vector3 | None = None) -> LYTObstacle:
        """Add a new obstacle."""
        if self._lyt is None:
            self._lyt = LYT()

        if position is None:
            position = Vector3(self._camera_pos.x, self._camera_pos.y, 0)

        obstacle = LYTObstacle("newobstacle", position)
        self._lyt.obstacles.append(obstacle)
        self.sig_element_added.emit(obstacle)
        self.update()
        return obstacle

    def delete_element(self, element: LYTRoom | LYTDoorHook | LYTTrack | LYTObstacle | None = None):
        """Delete the specified element (or selected element if none specified)."""
        if element is None:
            element = self._selected_element

        if element is None or self._lyt is None:
            return

        if isinstance(element, LYTRoom):
            self._lyt.rooms.remove(element)
        elif isinstance(element, LYTDoorHook):
            self._lyt.doorhooks.remove(element)
        elif isinstance(element, LYTTrack):
            self._lyt.tracks.remove(element)
        elif isinstance(element, LYTObstacle):
            self._lyt.obstacles.remove(element)

        if element == self._selected_element:
            self._selected_element = None

        self.sig_element_deleted.emit(element)
        self.update()

    def duplicate_element(self, element: LYTRoom | LYTDoorHook | LYTTrack | LYTObstacle | None = None):
        """Duplicate the specified element (or selected element if none specified)."""
        if element is None:
            element = self._selected_element

        if element is None or self._lyt is None:
            return None

        # Offset the duplicate slightly
        offset = Vector3(20, 20, 0)

        if isinstance(element, LYTRoom):
            new_element = LYTRoom(f"{element.model}_copy", element.position + offset)
            self._lyt.rooms.append(new_element)
        elif isinstance(element, LYTDoorHook):
            new_element = LYTDoorHook(
                element.room,
                f"{element.door}_copy",
                element.position + offset,
                element.orientation
            )
            self._lyt.doorhooks.append(new_element)
        elif isinstance(element, LYTTrack):
            new_element = LYTTrack(f"{element.model}_copy", element.position + offset)
            self._lyt.tracks.append(new_element)
        elif isinstance(element, LYTObstacle):
            new_element = LYTObstacle(f"{element.model}_copy", element.position + offset)
            self._lyt.obstacles.append(new_element)
        else:
            return None

        self.sig_element_added.emit(new_element)
        self.update()
        return new_element

    def _world_to_screen(self, world_pos: Vector3) -> Vector2:
        """Convert world coordinates to screen coordinates."""
        # Apply camera transform
        screen_x = (world_pos.x - self._camera_pos.x) * self._zoom + self.width() / 2
        screen_y = (world_pos.y - self._camera_pos.y) * self._zoom + self.height() / 2
        return Vector2(screen_x, screen_y)

    def _screen_to_world(self, screen_pos: Vector2) -> Vector3:
        """Convert screen coordinates to world coordinates."""
        world_x = (screen_pos.x - self.width() / 2) / self._zoom + self._camera_pos.x
        world_y = (screen_pos.y - self.height() / 2) / self._zoom + self._camera_pos.y
        return Vector3(world_x, world_y, 0)

    def _get_element_at_position(self, screen_pos: Vector2) -> LYTRoom | LYTDoorHook | LYTTrack | LYTObstacle | None:
        """Get the element at the specified screen position."""
        if self._lyt is None:
            return None

        world_pos = self._screen_to_world(screen_pos)

        # Check door hooks first (smallest, should be on top)
        for doorhook in self._lyt.doorhooks:
            dist = math.sqrt(
                (doorhook.position.x - world_pos.x) ** 2 +
                (doorhook.position.y - world_pos.y) ** 2
            )
            if dist <= self.DOORHOOK_SIZE / self._zoom:
                return doorhook

        # Check tracks
        for track in self._lyt.tracks:
            dist = math.sqrt(
                (track.position.x - world_pos.x) ** 2 +
                (track.position.y - world_pos.y) ** 2
            )
            if dist <= self.TRACK_SIZE / self._zoom:
                return track

        # Check obstacles
        for obstacle in self._lyt.obstacles:
            dist = math.sqrt(
                (obstacle.position.x - world_pos.x) ** 2 +
                (obstacle.position.y - world_pos.y) ** 2
            )
            if dist <= self.OBSTACLE_SIZE / self._zoom:
                return obstacle

        # Check rooms (largest, should be checked last)
        for room in self._lyt.rooms:
            dist = math.sqrt(
                (room.position.x - world_pos.x) ** 2 +
                (room.position.y - world_pos.y) ** 2
            )
            if dist <= self.ROOM_SIZE / self._zoom:
                return room

        return None

    def paintEvent(self, event: QPaintEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        """Paint the LYT elements."""
        if self._lyt is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fill background
        painter.fillRect(0, 0, self.width(), self.height(), QColor(30, 30, 30))

        # Create transform
        transform = QTransform()
        transform.translate(self.width() / 2, self.height() / 2)
        transform.scale(self._zoom, self._zoom)
        transform.translate(-self._camera_pos.x, -self._camera_pos.y)
        painter.setTransform(transform)

        # Draw grid
        self._draw_grid(painter)

        # Draw elements (back to front: rooms, obstacles, tracks, doorhooks)
        for room in self._lyt.rooms:
            self._draw_room(painter, room)

        for obstacle in self._lyt.obstacles:
            self._draw_obstacle(painter, obstacle)

        for track in self._lyt.tracks:
            self._draw_track(painter, track)

        for doorhook in self._lyt.doorhooks:
            self._draw_doorhook(painter, doorhook)

    def _draw_grid(self, painter: QPainter):
        """Draw a background grid."""
        grid_size = 100.0
        pen = QPen(QColor(50, 50, 50), 1.0 / self._zoom)
        painter.setPen(pen)

        # Calculate visible range
        view_width = self.width() / self._zoom
        view_height = self.height() / self._zoom
        start_x = self._camera_pos.x - view_width / 2
        end_x = self._camera_pos.x + view_width / 2
        start_y = self._camera_pos.y - view_height / 2
        end_y = self._camera_pos.y + view_height / 2

        # Draw vertical lines
        x = math.floor(start_x / grid_size) * grid_size
        while x <= end_x:
            painter.drawLine(int(x), int(start_y), int(x), int(end_y))
            x += grid_size

        # Draw horizontal lines
        y = math.floor(start_y / grid_size) * grid_size
        while y <= end_y:
            painter.drawLine(int(start_x), int(y), int(end_x), int(y))
            y += grid_size

    def _draw_room(self, painter: QPainter, room: LYTRoom):
        """Draw a room."""
        is_selected = room == self._selected_element
        color = self.ROOM_SELECTED_COLOR if is_selected else self.ROOM_COLOR
        border_width = 3.0 if is_selected else 1.5

        painter.setBrush(QBrush(color))
        painter.setPen(QPen(self.ROOM_BORDER_COLOR, border_width / self._zoom))

        # Draw as square
        size = self.ROOM_SIZE
        painter.drawRect(
            int(room.position.x - size / 2),
            int(room.position.y - size / 2),
            int(size),
            int(size)
        )

        # Draw label
        if self._zoom > 0.5:  # Only show text when zoomed in enough
            painter.save()
            painter.resetTransform()
            screen_pos = self._world_to_screen(room.position)
            painter.setPen(Qt.GlobalColor.white)
            painter.drawText(int(screen_pos.x - 50), int(screen_pos.y + size * self._zoom / 2 + 15), 100, 20,
                           Qt.AlignmentFlag.AlignCenter, room.model)
            painter.restore()

    def _draw_doorhook(self, painter: QPainter, doorhook: LYTDoorHook):
        """Draw a door hook."""
        is_selected = doorhook == self._selected_element
        color = self.DOORHOOK_SELECTED_COLOR if is_selected else self.DOORHOOK_COLOR
        border_width = 2.0 if is_selected else 1.0

        painter.setBrush(QBrush(color))
        painter.setPen(QPen(Qt.GlobalColor.black, border_width / self._zoom))

        # Draw as circle
        painter.drawEllipse(
            int(doorhook.position.x - self.DOORHOOK_SIZE / 2),
            int(doorhook.position.y - self.DOORHOOK_SIZE / 2),
            int(self.DOORHOOK_SIZE),
            int(self.DOORHOOK_SIZE)
        )

        # Draw orientation indicator
        euler = doorhook.orientation.to_euler()
        angle = euler.z
        end_x = doorhook.position.x + math.cos(angle) * self.DOORHOOK_SIZE
        end_y = doorhook.position.y + math.sin(angle) * self.DOORHOOK_SIZE
        painter.drawLine(
            int(doorhook.position.x),
            int(doorhook.position.y),
            int(end_x),
            int(end_y)
        )

    def _draw_track(self, painter: QPainter, track: LYTTrack):
        """Draw a track."""
        is_selected = track == self._selected_element
        color = self.TRACK_SELECTED_COLOR if is_selected else self.TRACK_COLOR
        border_width = 2.0 if is_selected else 1.0

        painter.setBrush(QBrush(color))
        painter.setPen(QPen(Qt.GlobalColor.black, border_width / self._zoom))

        # Draw as diamond
        size = self.TRACK_SIZE / 2
        points = [
            (track.position.x, track.position.y - size),
            (track.position.x + size, track.position.y),
            (track.position.x, track.position.y + size),
            (track.position.x - size, track.position.y),
        ]
        from qtpy.QtCore import QPoint
        from qtpy.QtGui import QPolygon
        polygon = QPolygon([QPoint(int(p[0]), int(p[1])) for p in points])
        painter.drawPolygon(polygon)

    def _draw_obstacle(self, painter: QPainter, obstacle: LYTObstacle):
        """Draw an obstacle."""
        is_selected = obstacle == self._selected_element
        color = self.OBSTACLE_SELECTED_COLOR if is_selected else self.OBSTACLE_COLOR
        border_width = 2.0 if is_selected else 1.0

        painter.setBrush(QBrush(color))
        painter.setPen(QPen(Qt.GlobalColor.black, border_width / self._zoom))

        # Draw as cross
        size = self.OBSTACLE_SIZE / 2
        painter.drawLine(
            int(obstacle.position.x - size),
            int(obstacle.position.y - size),
            int(obstacle.position.x + size),
            int(obstacle.position.y + size)
        )
        painter.drawLine(
            int(obstacle.position.x - size),
            int(obstacle.position.y + size),
            int(obstacle.position.x + size),
            int(obstacle.position.y - size)
        )

        # Draw circle around it
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(
            int(obstacle.position.x - size),
            int(obstacle.position.y - size),
            int(size * 2),
            int(size * 2)
        )

    def mousePressEvent(self, event: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        """Handle mouse press events."""
        mouse_pos = Vector2(event.pos().x(), event.pos().y())

        if event.button() == Qt.MouseButton.LeftButton:
            element = self._get_element_at_position(mouse_pos)
            if element:
                self.select_element(element)
                self._dragging = True
                self._drag_start_pos = mouse_pos
                self._element_start_pos = element.position.copy() if hasattr(element.position, 'copy') else Vector3(element.position.x, element.position.y, element.position.z)
            else:
                self.select_element(None)

        elif event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._mouse_prev = mouse_pos

    def mouseMoveEvent(self, event: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        """Handle mouse move events."""
        mouse_pos = Vector2(event.pos().x(), event.pos().y())

        if self._dragging and self._selected_element and self._drag_start_pos and self._element_start_pos:
            # Calculate world space delta
            world_start = self._screen_to_world(self._drag_start_pos)
            world_current = self._screen_to_world(mouse_pos)
            delta = Vector3(
                world_current.x - world_start.x,
                world_current.y - world_start.y,
                0
            )

            # Update element position
            new_pos = Vector3(
                self._element_start_pos.x + delta.x,
                self._element_start_pos.y + delta.y,
                self._element_start_pos.z
            )
            self._selected_element.position = new_pos
            self.update()

        elif self._panning:
            delta_x = (mouse_pos.x - self._mouse_prev.x) / self._zoom
            delta_y = (mouse_pos.y - self._mouse_prev.y) / self._zoom
            self._camera_pos.x -= delta_x
            self._camera_pos.y -= delta_y
            self._mouse_prev = mouse_pos
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        """Handle mouse release events."""
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            if self._selected_element and self._element_start_pos:
                self.sig_element_moved.emit(self._selected_element, self._selected_element.position)
            self._dragging = False
            self._drag_start_pos = None
            self._element_start_pos = None

        elif event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False

    def wheelEvent(self, event: QWheelEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        """Handle mouse wheel events for zooming."""
        delta = event.angleDelta().y()
        zoom_factor = 1.1 if delta > 0 else 0.9
        self._zoom *= zoom_factor
        self._zoom = max(0.1, min(5.0, self._zoom))
        self.update()

    def reset_view(self):
        """Reset the camera to default view."""
        self._camera_pos = Vector2(0, 0)
        self._zoom = 1.0
        self.update()

    def frame_all(self):
        """Frame all elements in view."""
        if not self._lyt or not self._lyt.rooms:
            return

        # Calculate bounding box of all elements
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')

        for room in self._lyt.rooms:
            min_x = min(min_x, room.position.x)
            max_x = max(max_x, room.position.x)
            min_y = min(min_y, room.position.y)
            max_y = max(max_y, room.position.y)

        # Center camera on bounding box
        self._camera_pos.x = (min_x + max_x) / 2
        self._camera_pos.y = (min_y + max_y) / 2

        # Adjust zoom to fit
        width = max_x - min_x + 200  # Add padding
        height = max_y - min_y + 200
        zoom_x = self.width() / width if width > 0 else 1.0
        zoom_y = self.height() / height if height > 0 else 1.0
        self._zoom = min(zoom_x, zoom_y, 2.0)  # Cap at 2x zoom

        self.update()

