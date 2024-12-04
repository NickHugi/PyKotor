from __future__ import annotations

import math

from copy import copy
from typing import TYPE_CHECKING, Generic, NamedTuple, TypeVar

import qtpy

from qtpy.QtCore import (
    QPoint,
    QPointF,
    QRect,
    QRectF,
    QTimer,
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QColor, QCursor, QImage, QPainter, QPainterPath, QPen, QPixmap, QTransform
from qtpy.QtWidgets import QWidget

from pykotor.common.geometry import Vector2, Vector3
from pykotor.resource.formats.bwm import BWM
from pykotor.resource.formats.tpc import TPCTextureFormat
from pykotor.resource.generics.are import ARENorthAxis
from pykotor.resource.generics.git import GITCamera, GITCreature, GITDoor, GITEncounter, GITPlaceable, GITSound, GITStore, GITTrigger, GITWaypoint
from toolset.utils.misc import clamp
from utility.error_handling import assert_with_variable_trace

if TYPE_CHECKING:
    from qtpy.QtGui import QFocusEvent, QKeyEvent, QMouseEvent, QPaintEvent, QWheelEvent

    from pykotor.common.geometry import SurfaceMaterial
    from pykotor.resource.formats.bwm.bwm_data import BWMFace
    from pykotor.resource.formats.lyt.lyt_data import LYT, LYTRoom
    from pykotor.resource.formats.tpc.tpc_data import TPC, TPCMipmap
    from pykotor.resource.generics.are import ARE
    from pykotor.resource.generics.git import GIT, GITInstance
    from pykotor.resource.generics.pth import PTH

T = TypeVar("T")


class GeomPoint(NamedTuple):
    instance: GITInstance
    point: Vector3


class WalkmeshCamera:
    def __init__(self):
        self._position: Vector2 = Vector2.from_null()
        self._rotation: float = 0.0
        self._zoom: float = 1.0

    def position(self) -> Vector2:
        return copy(self._position)

    def rotation(self) -> float:
        return self._rotation

    def zoom(self) -> float:
        return self._zoom

    def set_position(self, x: float, y: float):
        self._position.x = x
        self._position.y = y

    def nudge_position(self, x: float, y: float):
        self._position.x += x
        self._position.y += y

    def set_rotation(self, rotation: float):
        self._rotation = rotation

    def nudge_rotation(self, rotation: float):
        self._rotation += rotation

    def set_zoom(self, zoom: float):
        self._zoom = clamp(zoom, 0.1, 100)

    def nudge_zoom(self, zoomFactor: float):
        new_zoom = self._zoom * zoomFactor
        self._zoom = clamp(new_zoom, 0.1, 100)


class WalkmeshSelection(Generic[T]):
    def __init__(self):
        self._selection: list[T] = []

    def remove(self, element: T):
        self._selection.remove(element)

    def last(self) -> T | None:
        return self._selection[-1] if self._selection else None

    def count(self) -> int:
        return len(self._selection)

    def isEmpty(self) -> bool:
        return len(self._selection) == 0

    def all(self) -> list[T]:
        return copy(self._selection)

    def get(self, index: int) -> T:
        return self._selection[index]

    def clear(self):
        self._selection.clear()

    def select(self, elements: list[T], *, clear_existing: bool = True):
        if clear_existing:
            self._selection.clear()
        self._selection.extend(elements)


class WalkmeshRenderer(QWidget):
    sig_mouse_moved = Signal(object, object, object, object)  # screen coords, screen delta, mouse, keys  # pyright: ignore[reportPrivateImportUsage]
    """Signal emitted when mouse is moved over the widget."""

    sig_mouse_scrolled = Signal(object, object, object)  # screen delta, mouse, keys  # pyright: ignore[reportPrivateImportUsage]
    """Signal emitted when mouse is scrolled over the widget."""

    sig_mouse_released = Signal(object, object, object)  # screen coords, mouse, keys  # pyright: ignore[reportPrivateImportUsage]
    """Signal emitted when a mouse button is released after being pressed on the widget."""

    sig_mouse_pressed = Signal(object, object, object)  # screen coords, mouse, keys  # pyright: ignore[reportPrivateImportUsage]
    """Signal emitted when a mouse button is pressed on the widget."""

    sig_key_pressed = Signal(object, object)  # mouse keys  # pyright: ignore[reportPrivateImportUsage]
    sig_key_released = Signal(object, object)  # mouse keys  # pyright: ignore[reportPrivateImportUsage]
    sig_instance_hovered = Signal(object)  # instance  # pyright: ignore[reportPrivateImportUsage]
    sig_instance_pressed = Signal(object)  # instance  # pyright: ignore[reportPrivateImportUsage]

    def __init__(self, parent: QWidget):
        """Initializes the WalkmeshViewer widget.

        Args:
        ----
            parent (QWidget): The parent widget
        """
        super().__init__(parent)

        self._walkmeshes: list[BWM] = []
        self._git: GIT | None = None
        self._pth: PTH | None = None
        self._are: ARE | None = None
        self._minimap_image: QImage | None = None

        # Min/Max points and lengths for each axis
        self._bbmin: Vector3 = Vector3.from_null()
        self._bbmax: Vector3 = Vector3.from_null()
        self._world_size: Vector3 = Vector3.from_null()

        self.camera: WalkmeshCamera = WalkmeshCamera()
        self.instance_selection: WalkmeshSelection[GITInstance] = WalkmeshSelection()
        self.geometry_selection: WalkmeshSelection[GeomPoint] = WalkmeshSelection()

        self._mouse_prev: Vector2 = Vector2(self.cursor().pos().x(), self.cursor().pos().y())
        self._walkmesh_face_cache: dict[BWMFace, QPainterPath] | None = None

        self.highlight_on_hover: bool = False
        self.highlight_boundaries: bool = True
        self.hide_walkmesh_edges: bool = False
        self.hide_geom_points: bool = True
        self.instance_filter: str = ""
        self.hide_creatures: bool = True
        self.hide_placeables: bool = True
        self.hide_doors: bool = True
        self.hide_stores: bool = True
        self.hide_sounds: bool = True
        self.hide_triggers: bool = True
        self.hide_encounters: bool = True
        self.hide_waypoints: bool = True
        self.hide_cameras: bool = True

        self.material_colors: dict[SurfaceMaterial, QColor] = {}
        self.default_material_color: QColor = QColor(255, 0, 255)

        self._keys_down: set[int] = set()
        self._mouse_down: set[int] = set()

        self._pixmap_creature: QPixmap = QPixmap(":/images/icons/k1/creature.png")
        self._pixmap_door: QPixmap = QPixmap(":/images/icons/k1/door.png")
        self._pixmap_placeable: QPixmap = QPixmap(":/images/icons/k1/placeable.png")
        self._pixmap_merchant: QPixmap = QPixmap(":/images/icons/k1/merchant.png")
        self._pixmap_waypoint: QPixmap = QPixmap(":/images/icons/k1/waypoint.png")
        self._pixmap_sound: QPixmap = QPixmap(":/images/icons/k1/sound.png")
        self._pixmap_trigger: QPixmap = QPixmap(":/images/icons/k1/trigger.png")
        self._pixmap_encounter: QPixmap = QPixmap(":/images/icons/k1/encounter.png")
        self._pixmap_camera: QPixmap = QPixmap(":/images/icons/k1/camera.png")

        self._instances_under_mouse: list[GITInstance] = []
        self._geom_points_under_mouse: list[GeomPoint] = []

        self._path_nodes_under_mouse: list[Vector2] = []
        self.path_selection: WalkmeshSelection[Vector2] = WalkmeshSelection()
        self._path_node_size: float = 0.3
        self._path_edge_width: float = 0.2

        self._loop()

    def keys_down(self) -> set[int]:
        return self._keys_down

    def mouse_down(self) -> set[int]:
        return self._mouse_down

    def _loop(self):
        """The render loop."""
        self.repaint()
        QTimer.singleShot(33, self._loop)

    def reset_buttons_down(self):
        self._mouse_down.clear()

    def reset_keys_down(self):
        self._keys_down.clear()

    def reset_all_down(self):
        self._mouse_down.clear()
        self._keys_down.clear()

    def set_walkmeshes(self, walkmeshes: list[BWM]):
        """Sets the list of walkmeshes to be rendered.

        Args:
        ----
            walkmeshes: The list of walkmeshes.
        """
        self._walkmeshes = walkmeshes

    def generate_walkmeshes(self, layout: LYT):
        """Generate walkmesh based on the current room layout."""
        # Logic to generate walkmesh from layout
        self._walkmeshes = []  # Clear existing walkmeshes
        for room in layout.rooms:
            # Generate walkmesh for each room
            walkmesh = self.create_walkmesh_for_room(room)
            self._walkmeshes.append(walkmesh)
        self.update_walkmesh_display()

    def create_walkmesh_for_room(self, room: LYTRoom) -> BWM:
        """Create a walkmesh for a given room."""
        # Placeholder logic for creating a walkmesh
        # Replace with actual walkmesh generation logic
        walkmesh = BWM()
        # Add faces to walkmesh based on room dimensions
        return walkmesh

    def update_walkmesh_display(self):
        self.repaint()
        self._bbmin = Vector3(1000000, 1000000, 1000000)
        self._bbmax = Vector3(-1000000, -1000000, -1000000)
        for walkmesh in self._walkmeshes:
            bbmin, bbmax = walkmesh.box()
            self._bbmin.x = min(bbmin.x, self._bbmin.x)
            self._bbmin.y = min(bbmin.y, self._bbmin.y)
            self._bbmin.z = min(bbmin.z, self._bbmin.z)
            self._bbmax.x = max(bbmax.x, self._bbmax.x)
            self._bbmax.y = max(bbmax.y, self._bbmax.y)
            self._bbmax.z = max(bbmax.z, self._bbmax.z)

        self._world_size.x = math.fabs(self._bbmax.x - self._bbmin.x)
        self._world_size.y = math.fabs(self._bbmax.y - self._bbmin.y)
        self._world_size.z = math.fabs(self._bbmax.z - self._bbmin.z)

        # Reset camera
        self.camera.set_zoom(1.0)

        # Erase the cache so it will be rebuilt
        self._walkmesh_face_cache = None

    def set_git(self, git: GIT):
        self._git = git

    def set_pth(self, pth: PTH):
        self._pth = pth

    def set_minimap(self, are: ARE, tpc: TPC):
        self._are = are

        # Convert the TPC to RGB format and get the first mipmap
        tpc_rgb_data: bytearray = tpc.convert(TPCTextureFormat.RGB).data  # pyright: ignore[reportAttributeAccessIssue]
        get_result: TPCMipmap = tpc.get(0, 0)
        image = QImage(bytes(tpc_rgb_data), get_result.width, get_result.height, QImage.Format.Format_RGB888)
        crop: QRect = QRect(0, 0, 435, 256)
        self._minimap_image: QImage = image.copy(crop)

    def snap_camera_to_point(
        self,
        point: Vector2 | Vector3,
        zoom: int = 8,
    ):
        self.camera.set_position(point.x, point.y)
        self.camera.set_zoom(zoom)

    def do_cursor_lock(
        self,
        mutable_screen: Vector2,
    ):
        """Reset the cursor to the center of the screen to prevent it from going off screen.

        Used with the FreeCam and drag camera movements and drag rotations.
        """
        global_old_pos: QPoint = self.mapToGlobal(QPoint(int(self._mouse_prev.x), int(self._mouse_prev.y)))
        QCursor.setPos(global_old_pos)
        local_old_pos: QPoint = self.mapFromGlobal(QPoint(global_old_pos.x(), global_old_pos.y()))
        mutable_screen.x = local_old_pos.x()
        mutable_screen.y = local_old_pos.y()

    def to_render_coords(
        self,
        x: float,
        y: float,
    ) -> Vector2:
        """Returns a screen-space coordinates coverted from the specified world-space coordinates.

        The origin of the screen-space coordinates is the top-left of the WalkmeshRenderer widget.
        """
        cos: float = math.cos(self.camera.rotation())
        sin: float = math.sin(self.camera.rotation())
        x -= self.camera.position().x
        y -= self.camera.position().y
        x2: float = (x * cos - y * sin) * self.camera.zoom() + self.width() / 2
        y2: float = (x * sin + y * cos) * self.camera.zoom() + self.height() / 2
        return Vector2(x2, y2)

    def to_world_coords(
        self,
        x: float,
        y: float,
    ) -> Vector3:
        """Returns the world-space coordinates converted from the specified screen-space coordinates.

        The Z component is calculated using the X/Y components and the walkmesh
        face the mouse is over. If there is no face underneath the mouse, the Z component is set to zero.
        """
        y = self.height() - y
        cos: float = math.cos(self.camera.rotation())
        sin: float = math.sin(self.camera.rotation())
        x = (x - self.width() / 2) / self.camera.zoom()
        y = (y - self.height() / 2) / self.camera.zoom()
        x2: float = x * cos - y * sin + self.camera.position().x
        y2: float = x * sin + y * cos + self.camera.position().y

        z: float = self.get_z_coord(x2, y2)

        return Vector3(x2, y2, z)

    def to_world_delta(
        self,
        x: float,
        y: float,
    ) -> Vector2:
        """Returns the coordinates representing a change in world-space.

        This is convereted from coordinates representing a
        change in screen-space, such as the delta paramater given in a mouseMove event.
        """
        cos: float = math.cos(-self.camera.rotation())
        sin: float = math.sin(-self.camera.rotation())
        x /= self.camera.zoom()
        y /= self.camera.zoom()
        x2: float = x * cos - y * sin
        y2: float = x * sin + y * cos
        return Vector2(x2, -y2)

    def get_z_coord(
        self,
        x: float,
        y: float,
    ) -> float:
        """Returns the Z coordinate based of walkmesh data for the specified point.

        If there are overlapping faces, the walkable face will take priority.
        """
        # We need to find a face in the walkmesh that is underneath the mouse to find the Z
        # We also want to prioritize walkable faces
        # And if we cant find a face, then set the Z to 0.0
        face: BWMFace | None = None
        for walkmesh in self._walkmeshes:
            over: BWMFace | None = walkmesh.faceAt(x, y)
            if over and (face is None or (not face.material.walkable() and over.material.walkable())):
                face = over
        return 0.0 if face is None else face.determine_z(x, y)

    def material_color(self, material: SurfaceMaterial) -> QColor:
        return self.material_colors.get(material, self.default_material_color)

    def instances_under_mouse(self) -> list[GITInstance]:
        return self._instances_under_mouse

    def path_nodes_under_mouse(self) -> list[Vector2]:
        return self._path_nodes_under_mouse

    def geom_points_under_mouse(self) -> list[GeomPoint]:
        return self._geom_points_under_mouse

    def is_instance_visible(self, instance: GITInstance) -> bool | None:
        retBool: bool | None = None
        if isinstance(instance, GITCamera):
            retBool = not self.hide_cameras
        elif isinstance(instance, GITCreature):
            retBool = not self.hide_creatures
        elif isinstance(instance, GITDoor):
            retBool = not self.hide_doors
        elif isinstance(instance, GITEncounter):
            retBool = not self.hide_encounters
        elif isinstance(instance, GITPlaceable):
            retBool = not self.hide_placeables
        elif isinstance(instance, GITSound):
            retBool = not self.hide_sounds
        elif isinstance(instance, GITStore):
            retBool = not self.hide_stores
        elif isinstance(instance, GITTrigger):
            retBool = not self.hide_triggers
        elif isinstance(instance, GITWaypoint):
            retBool = not self.hide_waypoints
        return retBool

    def instance_pixmap(self, instance: GITInstance) -> QPixmap:
        retPixmap: QPixmap = QPixmap()
        if isinstance(instance, GITCamera):
            retPixmap = self._pixmap_camera
        if isinstance(instance, GITCreature):
            retPixmap = self._pixmap_creature
        if isinstance(instance, GITDoor):
            retPixmap = self._pixmap_door
        if isinstance(instance, GITEncounter):
            retPixmap = self._pixmap_encounter
        if isinstance(instance, GITPlaceable):
            retPixmap = self._pixmap_placeable
        if isinstance(instance, GITTrigger):
            retPixmap = self._pixmap_trigger
        if isinstance(instance, GITSound):
            retPixmap = self._pixmap_sound
        if isinstance(instance, GITStore):
            retPixmap = self._pixmap_merchant
        if isinstance(instance, GITWaypoint):
            retPixmap = self._pixmap_waypoint
        return retPixmap

    def center_camera(self):
        self.camera.set_position((self._bbmin.x + self._bbmax.x) / 2, (self._bbmin.y + self._bbmax.y) / 2)
        world_w: float = self._world_size.x
        world_h: float = self._world_size.y

        # If the GIT is being loaded directly after the window opens the widget won't have appropriately resized itself,
        # so we check for this and set the sizes to what it should be by default.
        if self.width() == 100:  # noqa: PLR2004
            screen_w = 520
            screen_h = 507
        else:
            screen_w: int = self.width()
            screen_h: int = self.height()

        scale_w: float = screen_w / world_w if world_w != 0 else 0.0
        scale_h: float = screen_h / world_h if world_h != 0 else 0.0
        camScale: float = min(scale_w, scale_h)

        self.camera.set_zoom(camScale)
        self.camera.set_rotation(0)

    def _build_face(
        self,
        face: BWMFace,
    ) -> QPainterPath:
        v1: Vector2 = Vector2(face.v1.x, face.v1.y)
        v2: Vector2 = Vector2(face.v2.x, face.v2.y)
        v3: Vector2 = Vector2(face.v3.x, face.v3.y)

        path = QPainterPath()
        path.moveTo(v1.x, v1.y)
        path.lineTo(v2.x, v2.y)
        path.lineTo(v3.x, v3.y)
        path.lineTo(v1.x, v1.y)
        path.closeSubpath()

        return path

    def _build_instance_bounds(
        self,
        instance: GITInstance,
    ) -> QPainterPath:
        path = QPainterPath()
        if (isinstance(instance, (GITEncounter, GITTrigger))) and len(instance.geometry) > 0:
            path.moveTo(instance.position.x + instance.geometry[0].x, instance.position.y + instance.geometry[0].y)  # type: ignore[]
            for point in instance.geometry[1:]:
                path.lineTo(instance.position.x + point.x, instance.position.y + point.y)  # type: ignore[]
            path.lineTo(instance.position.x + instance.geometry[0].x, instance.position.y + instance.geometry[0].y)  # type: ignore[]
        return path

    def _build_instance_bounds_points(
        self,
        instance: GITInstance,
    ) -> QPainterPath:
        path = QPainterPath()
        if isinstance(instance, (GITTrigger, GITEncounter)):
            for point in instance.geometry:
                size: float = 4 / self.camera.zoom()
                path.addEllipse(QPointF(instance.position.x + point.x, instance.position.y + point.y), size, size)
        return path

    def _draw_image(  # noqa: PLR0913
        self,
        painter: QPainter,
        pixmap: QPixmap,
        x: float,
        y: float,
        rotation: float,
        scale: float,
    ):
        painter.save()
        painter.translate(x, y)
        painter.rotate(math.degrees(rotation))
        painter.scale(-1, 1)

        source = QRectF(0, 0, pixmap.width(), pixmap.height())
        true_width, true_height = pixmap.width() * scale, pixmap.height() * scale
        painter.drawPixmap(QRectF(-true_width / 2, -true_height / 2, true_width, true_height), pixmap, source)
        painter.restore()

    # region Events
    def paintEvent(
        self,
        e: QPaintEvent,  # pyright: ignore[reportIncompatibleMethodOverride]
    ):
        # Build walkmesh faces cache
        if self._walkmesh_face_cache is None:
            self._walkmesh_face_cache = {}
            for walkmesh in self._walkmeshes:
                # We want to draw walkable faces over the unwalkable ones
                for face in walkmesh.walkable_faces():
                    self._walkmesh_face_cache[face] = self._build_face(face)
                for face in walkmesh.unwalkable_faces():
                    self._walkmesh_face_cache[face] = self._build_face(face)

        # Create the transform object using the camera values
        transform = QTransform()
        transform.translate(self.width() / 2, self.height() / 2)
        transform.rotate(math.degrees(self.camera.rotation()))
        transform.scale(self.camera.zoom(), -self.camera.zoom())
        transform.translate(-self.camera.position().x, -self.camera.position().y)

        # Fill the screen with black
        painter = QPainter(self)
        painter.setBrush(QColor(0))
        painter.drawRect(0, 0, self.width(), self.height())

        # Draw the faces of the walkmesh (cached).
        painter.setTransform(transform)

        # Draw the minimap
        if self._are and self._minimap_image:
            axis_to_rotation: dict[ARENorthAxis, int] = {
                ARENorthAxis.PositiveY: 0,
                ARENorthAxis.PositiveX: 270,
                ARENorthAxis.NegativeY: 180,
                ARENorthAxis.NegativeX: 90,
            }
            rotation: int = axis_to_rotation[self._are.north_axis]
            rads: float = math.radians(-rotation)

            map_point_1_x: float = ((self._are.map_point_1.x - 0.5) * math.cos(rads)) - ((self._are.map_point_1.y - 0.5) * math.sin(rads)) + 0.5
            map_point_1_y: float = ((self._are.map_point_1.x - 0.5) * math.sin(rads)) + ((self._are.map_point_1.y - 0.5) * math.cos(rads)) + 0.5
            map_point_2_x: float = ((self._are.map_point_2.x - 0.5) * math.cos(rads)) - ((self._are.map_point_2.y - 0.5) * math.sin(rads)) + 0.5
            map_point_2_y: float = ((self._are.map_point_2.x - 0.5) * math.sin(rads)) + ((self._are.map_point_2.y - 0.5) * math.cos(rads)) + 0.5

            world_point_1_x: float = self._are.world_point_1.x
            world_point_1_y: float = self._are.world_point_1.y
            world_point_2_x: float = self._are.world_point_2.x
            world_point_2_y: float = self._are.world_point_2.y

            # X% of the width of the image
            widthPercent: float = abs(map_point_1_x - map_point_2_x)
            heightPercent: float = abs(map_point_1_y - map_point_2_y)
            # Takes up Y amount of WUs.
            widthWU: float = abs(world_point_1_x - world_point_2_x)
            heightWU: float = abs(world_point_1_y - world_point_2_y)

            # Here we determine how many world units the full texture covers
            # 100% of the image width/height covers X amount of world units
            fullWidthWU: float = widthWU / widthPercent
            fullHeightWU: float = heightWU / heightPercent

            # Now we can figure out where the X/Y coords of the image go
            # Remember world_point_1 not the corner of the image, but somewhere within the image, so we must calculate
            # where the corner of the image is in the world space.
            imageX: float = world_point_1_x - (fullWidthWU * map_point_1_x)
            imageY: float = world_point_1_y - (fullHeightWU * (1 - map_point_1_y))

            rotated: QImage = self._minimap_image.transformed(QTransform().rotate(rotation))

            targetRect = QRectF(QPointF(imageX, imageY), QPointF(imageX + fullWidthWU, imageY + fullHeightWU))
            painter.drawImage(targetRect, rotated)

        pen: QPen = (
            QPen(Qt.PenStyle.NoPen)
            if self.hide_walkmesh_edges
            else QPen(
                QColor(10, 10, 10, 120),
                1 / self.camera.zoom(),
                Qt.PenStyle.SolidLine,
            )
        )
        painter.setPen(pen)
        for face, path in self._walkmesh_face_cache.items():
            painter.setBrush(self.material_color(face.material))
            painter.drawPath(path)

        if self.highlight_boundaries:
            for walkmesh in self._walkmeshes:
                for face in walkmesh.walkable_faces():
                    painter.setPen(QPen(QColor(255, 0, 0), 3 / self.camera.zoom()))
                    path = QPainterPath()
                    if face.trans1 is not None:
                        path.moveTo(face.v1.x, face.v1.y)
                        path.lineTo(face.v2.x, face.v2.y)
                    if face.trans2 is not None:
                        path.moveTo(face.v2.x, face.v2.y)
                        path.lineTo(face.v3.x, face.v3.y)
                    if face.trans3 is not None:
                        path.moveTo(face.v1.x, face.v1.y)
                        path.lineTo(face.v3.x, face.v3.y)
                    painter.drawPath(path)

        # Draw the pathfinding nodes and edges
        painter.setOpacity(1.0)
        if self._pth is not None:
            for i, source in enumerate(self._pth):
                painter.setPen(QPen(QColor(200, 200, 200, 255), self._path_edge_width, Qt.PenStyle.SolidLine))
                for j in self._pth.outgoing(i):
                    target: Vector2 | None = self._pth.get(j.target)
                    assert target is not None, assert_with_variable_trace(target is not None)
                    painter.drawLine(QPointF(source.x, source.y), QPointF(target.x, target.y))

            for point_2d in self._pth:
                painter.setPen(QColor(0, 0, 0, 0))
                painter.setBrush(QColor(200, 200, 200, 255))
                painter.drawEllipse(QPointF(point_2d.x, point_2d.y), self._path_node_size, self._path_node_size)

            for point_2d in self._path_nodes_under_mouse:
                painter.setPen(QColor(0, 0, 0, 0))
                painter.setBrush(QColor(255, 255, 255, 255))
                painter.drawEllipse(QPointF(point_2d.x, point_2d.y), self._path_node_size, self._path_node_size)

            for point_2d in self.path_selection.all():
                painter.setPen(QColor(0, 0, 0, 0))
                painter.setBrush(QColor(0, 255, 0, 255))
                painter.drawEllipse(QPointF(point_2d.x, point_2d.y), self._path_node_size, self._path_node_size)

        # Draw the git instances (represented as icons)
        painter.setOpacity(0.6)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        lower_filter: str = self.instance_filter.lower()
        if self._git is not None:
            for creature in [] if self.hide_creatures else self._git.creatures:
                if creature.resref and lower_filter not in str(creature.resref).lower():
                    continue
                self._draw_image(painter, self._pixmap_creature, creature.position.x, creature.position.y, math.pi + self.camera.rotation(), 1 / 16)

            for door in [] if self.hide_doors else self._git.doors:
                if door.resref and lower_filter not in str(door.resref).lower():
                    continue
                self._draw_image(painter, self._pixmap_door, door.position.x, door.position.y, math.pi + self.camera.rotation(), 1 / 16)

            for placeable in [] if self.hide_placeables else self._git.placeables:
                if placeable.resref and lower_filter not in str(placeable.resref).lower():
                    continue
                self._draw_image(painter, self._pixmap_placeable, placeable.position.x, placeable.position.y, math.pi + self.camera.rotation(), 1 / 16)

            for merchant in [] if self.hide_stores else self._git.stores:
                if merchant.resref and lower_filter not in str(merchant.resref).lower():
                    continue
                self._draw_image(painter, self._pixmap_merchant, merchant.position.x, merchant.position.y, math.pi + self.camera.rotation(), 1 / 16)

            for waypoint in [] if self.hide_waypoints else self._git.waypoints:
                if waypoint.resref and lower_filter not in str(waypoint.resref).lower():
                    continue
                self._draw_image(painter, self._pixmap_waypoint, waypoint.position.x, waypoint.position.y, math.pi + self.camera.rotation(), 1 / 16)

            for sound in [] if self.hide_sounds else self._git.sounds:
                if sound.resref and lower_filter not in str(sound.resref).lower():
                    continue
                self._draw_image(painter, self._pixmap_sound, sound.position.x, sound.position.y, math.pi + self.camera.rotation(), 1 / 16)

            for encounter in [] if self.hide_encounters else self._git.encounters:
                if encounter.resref and lower_filter not in str(encounter.resref).lower():
                    continue
                self._draw_image(painter, self._pixmap_encounter, encounter.position.x, encounter.position.y, math.pi + self.camera.rotation(), 1 / 16)

            for trigger in [] if self.hide_triggers else self._git.triggers:
                if trigger.resref and lower_filter not in str(trigger.resref).lower():
                    continue
                self._draw_image(painter, self._pixmap_trigger, trigger.position.x, trigger.position.y, math.pi + self.camera.rotation(), 1 / 16)

            for camera in [] if self.hide_cameras else self._git.cameras:
                self._draw_image(painter, self._pixmap_camera, camera.position.x, camera.position.y, math.pi + self.camera.rotation(), 1 / 16)

        # Highlight the first instance that is underneath the mouse
        if self._instances_under_mouse:
            instance: GITInstance = self._instances_under_mouse[0]

            painter.setBrush(QColor(255, 255, 255, 35))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(instance.position.x, instance.position.y), 1, 1)

            # If its a trigger or an encounter, this will draw the geometry stored inside it
            painter.setBrush(QColor(0, 220, 0, 50))
            painter.setPen(QPen(QColor(0, 255, 0, 75), 2 / self.camera.zoom()))
            painter.drawPath(self._build_instance_bounds(instance))

        # Highlight first geom point that is underneath the mouse
        if self._geom_points_under_mouse:
            gpoint: GeomPoint = self._geom_points_under_mouse[0]
            point = gpoint.instance.position + gpoint.point

            if not self.hide_geom_points:
                painter.setBrush(QColor(255, 255, 255, 200))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(point.x, point.y), 4 / self.camera.zoom(), 4 / self.camera.zoom())

        # Highlight selected instances
        for instance in self.instance_selection.all():
            painter.setBrush(QColor(255, 255, 255, 70))
            painter.setPen(QPen(QColor(255, 255, 255, 255), 1 / self.camera.zoom()))
            painter.drawEllipse(QPointF(instance.position.x, instance.position.y), 1, 1)

            # If its a trigger or an encounter, this will draw the geometry stored inside it
            painter.setBrush(QColor(0, 220, 0, 100))
            painter.setPen(QPen(QColor(0, 255, 0, 150), 2 / self.camera.zoom()))
            painter.drawPath(self._build_instance_bounds(instance))

            # If its a trigger or an encounter, this will draw the circles at the points making up the geometry
            if not self.hide_geom_points:
                painter.setBrush(QColor(0, 255, 0, 255))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawPath(self._build_instance_bounds_points(instance))

            # Draw an arrow representing the instance rotation (where applicable)
            instance_yaw_value: float | None = instance.yaw()
            if instance_yaw_value is not None:
                l1px: float = instance.position.x + math.cos(instance_yaw_value + math.pi / 2) * 1.1
                l1py: float = instance.position.y + math.sin(instance_yaw_value + math.pi / 2) * 1.1
                l2px: float = instance.position.x + math.cos(instance_yaw_value + math.pi / 2) * 1.3
                l2py: float = instance.position.y + math.sin(instance_yaw_value + math.pi / 2) * 1.3
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(QColor(255, 255, 255, 255), 0.15))
                painter.drawLine(QPointF(l1px, l1py), QPointF(l2px, l2py))

        # Highlight selected geometry points
        for geom_point in self.geometry_selection.all():
            point: Vector3 = geom_point.point + geom_point.instance.position
            painter.setBrush(QColor(255, 255, 255, 255))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(point.x, point.y), 4 / self.camera.zoom(), 4 / self.camera.zoom())

    def wheelEvent(self, e: QWheelEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        self.sig_mouse_scrolled.emit(Vector2(e.angleDelta().x(), e.angleDelta().y()), self._mouse_down, self._keys_down)

    def mouseMoveEvent(self, e: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        pos = e.pos() if qtpy.QT5 else e.position().toPoint()
        super().mouseMoveEvent(e)
        coords: Vector2 = Vector2(pos.x(), pos.y())
        coords_delta: Vector2 = Vector2(coords.x - self._mouse_prev.x, coords.y - self._mouse_prev.y)
        self.sig_mouse_moved.emit(coords, coords_delta, self._mouse_down, self._keys_down)
        self._mouse_prev = coords  # Always assign mouse_prev after emitting: allows signal handlers (e.g. ModuleDesigner, GITEditor) to handle cursor lock.

        self._instances_under_mouse: list[GITInstance] = []
        self._geom_points_under_mouse: list[GeomPoint] = []
        self._path_nodes_under_mouse: list[Vector2] = []

        world: Vector2 = Vector2.from_vector3(self.to_world_coords(coords.x, coords.y))  # Mouse pos in world

        if self._git is not None:
            instances: list[GITInstance] = self._git.instances()
            for instance in instances:
                position = Vector2(instance.position.x, instance.position.y)
                if position.distance(world) <= 1 and self.is_instance_visible(instance):
                    self.sig_instance_hovered.emit(instance)
                    self._instances_under_mouse.append(instance)

                if isinstance(instance, GITEncounter) or (isinstance(instance, GITTrigger) and instance in self.instance_selection.all()):
                    for point in instance.geometry:
                        pworld: Vector2 = Vector2.from_vector3(instance.position + point)
                        if pworld.distance(world) <= 0.5:  # noqa: PLR2004
                            self._geom_points_under_mouse.append(GeomPoint(instance, point))

        if self._pth is not None:
            for point in self._pth:
                if point.distance(world) <= self._path_node_size:
                    self._path_nodes_under_mouse.append(point)

    def focusOutEvent(self, e: QFocusEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        self._mouse_down.clear()
        self._keys_down.clear()
        super().focusOutEvent(e)

    def mousePressEvent(self, e: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        super().mousePressEvent(e)
        if e is None:
            return
        button = e.button()
        self._mouse_down.add(button)
        coords = Vector2(e.x(), e.y())
        self.sig_mouse_pressed.emit(coords, self._mouse_down, self._keys_down)

    def mouseReleaseEvent(self, e: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        super().mouseReleaseEvent(e)
        if e is None:
            return
        button = e.button()
        self._mouse_down.discard(button)
        coords = Vector2(e.x(), e.y())
        self.sig_mouse_released.emit(coords, self._mouse_down, self._keys_down)

    def keyPressEvent(self, e: QKeyEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        super().keyPressEvent(e)
        if e is None:
            return
        key = e.key()
        if e is None:
            return
        self._keys_down.add(key)
        if self.underMouse():
            self.sig_key_pressed.emit(self._mouse_down, self._keys_down)

    def keyReleaseEvent(self, e: QKeyEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        super().keyReleaseEvent(e)
        if e is None:
            return
        key = e.key()
        self._keys_down.discard(key)
        if self.underMouse():
            self.sig_key_released.emit(self._mouse_down, self._keys_down)

    # endregion
