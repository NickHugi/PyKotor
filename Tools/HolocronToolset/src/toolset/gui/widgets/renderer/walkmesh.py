from __future__ import annotations

import math

from copy import copy
from typing import TYPE_CHECKING, Generic, NamedTuple, TypeVar

from qtpy import QtCore
from qtpy.QtCore import QPoint, QPointF, QRect, QRectF, QTimer
from qtpy.QtGui import (
    QColor,
    QCursor,
    QImage,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QTransform,
)
from qtpy.QtWidgets import QWidget

from pykotor.common.geometry import Vector2, Vector3
from pykotor.resource.formats.tpc import TPCTextureFormat
from pykotor.resource.generics.are import ARENorthAxis
from pykotor.resource.generics.git import (
    GITCamera,
    GITCreature,
    GITDoor,
    GITEncounter,
    GITPlaceable,
    GITSound,
    GITStore,
    GITTrigger,
    GITWaypoint,
)
from toolset.utils.misc import clamp
from utility.error_handling import assert_with_variable_trace

if TYPE_CHECKING:
    from qtpy.QtGui import (
        QFocusEvent,
        QKeyEvent,
        QMouseEvent,
        QPaintEvent,
        QWheelEvent,
    )

    from pykotor.common.geometry import SurfaceMaterial
    from pykotor.resource.formats.bwm import BWM, BWMFace
    from pykotor.resource.formats.tpc import TPC
    from pykotor.resource.generics.are import ARE
    from pykotor.resource.generics.git import (
        GIT,
        GITInstance,
    )
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

    def setPosition(self, x: float, y: float):
        self._position.x = x
        self._position.y = y

    def nudgePosition(self, x: float, y: float):
        self._position.x += x
        self._position.y += y

    def setRotation(self, rotation: float):
        self._rotation = rotation

    def nudgeRotation(self, rotation: float):
        self._rotation += rotation

    def setZoom(self, zoom: float):
        self._zoom = clamp(zoom, 0.1, 100)

    def nudgeZoom(self, zoomFactor: float):
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

    def select(self, elements: list[T], *, clearExisting: bool = True):
        if clearExisting:
            self._selection.clear()
        self._selection.extend(elements)


class WalkmeshRenderer(QWidget):
    mouseMoved = QtCore.Signal(object, object, object, object)  # screen coords, screen delta, mouse, keys
    """Signal emitted when mouse is moved over the widget."""

    mouseScrolled = QtCore.Signal(object, object, object)  # screen delta, mouse, keys
    """Signal emitted when mouse is scrolled over the widget."""

    mouseReleased = QtCore.Signal(object, object, object)  # screen coords, mouse, keys
    """Signal emitted when a mouse button is released after being pressed on the widget."""

    mousePressed = QtCore.Signal(object, object, object)  # screen coords, mouse, keys
    """Signal emitted when a mouse button is pressed on the widget."""

    keyPressed = QtCore.Signal(object, object)  # mouse keys
    keyReleased = QtCore.Signal(object, object)  # mouse keys
    instanceHovered = QtCore.Signal(object)  # instance
    instancePressed = QtCore.Signal(object)  # instance

    def __init__(self, parent: QWidget):
        """Initializes the WalkmeshViewer widget.

        Args:
        ----
            parent (QWidget): The parent widget

        Processing Logic:
        ----------------
            - Initializes variables and properties
            - Sets up camera
            - Sets up selection
            - Initializes mouse tracking
            - Loads icon pixmaps
            - Starts update loop.
        """
        super().__init__(parent)

        self._walkmeshes: list[BWM] = []
        self._git: GIT | None = None
        self._pth: PTH | None = None
        self._are: ARE | None = None
        self._minimapImage: QImage | None = None

        # Min/Max points and lengths for each axis
        self._bbmin: Vector3 = Vector3.from_null()
        self._bbmax: Vector3 = Vector3.from_null()
        self._worldSize: Vector3 = Vector3.from_null()

        self.camera: WalkmeshCamera = WalkmeshCamera()
        self.instanceSelection: WalkmeshSelection[GITInstance] = WalkmeshSelection()
        self.geometrySelection: WalkmeshSelection[GeomPoint] = WalkmeshSelection()

        self._mousePrev: Vector2 = Vector2(self.cursor().pos().x(), self.cursor().pos().y())
        self._walkmeshFaceCache: dict[BWMFace, QPainterPath] | None = None

        self.highlightOnHover: bool = False
        self.highlightBoundaries: bool = True
        self.hideWalkmeshEdges: bool = False
        self.hideGeomPoints: bool = True
        self.instanceFilter: str = ""
        self.hideCreatures: bool = True
        self.hidePlaceables: bool = True
        self.hideDoors: bool = True
        self.hideStores: bool = True
        self.hideSounds: bool = True
        self.hideTriggers: bool = True
        self.hideEncounters: bool = True
        self.hideWaypoints: bool = True
        self.hideCameras: bool = True

        self.materialColors: dict[SurfaceMaterial, QColor] = {}
        self.defaultMaterialColor: QColor = QColor(255, 0, 255)

        self._keysDown: set[int] = set()
        self._mouseDown: set[int] = set()

        self._pixmapCreature: QPixmap = QPixmap(":/images/icons/k1/creature.png")
        self._pixmapDoor: QPixmap = QPixmap(":/images/icons/k1/door.png")
        self._pixmapPlaceable: QPixmap = QPixmap(":/images/icons/k1/placeable.png")
        self._pixmapMerchant: QPixmap = QPixmap(":/images/icons/k1/merchant.png")
        self._pixmapWaypoint: QPixmap = QPixmap(":/images/icons/k1/waypoint.png")
        self._pixmapSound: QPixmap = QPixmap(":/images/icons/k1/sound.png")
        self._pixmapTrigger: QPixmap = QPixmap(":/images/icons/k1/trigger.png")
        self._pixmapEncounter: QPixmap = QPixmap(":/images/icons/k1/encounter.png")
        self._pixmapCamera: QPixmap = QPixmap(":/images/icons/k1/camera.png")

        self._instancesUnderMouse: list[GITInstance] = []
        self._geomPointsUnderMouse: list[GeomPoint] = []

        self._pathNodesUnderMouse: list[Vector2] = []
        self.pathSelection: WalkmeshSelection[Vector2] = WalkmeshSelection()
        self._pathNodeSize: float = 0.3
        self._pathEdgeWidth: float = 0.2

        self._loop()

    def keysDown(self):
        return self._keysDown

    def mouseDown(self):
        return self._mouseDown

    def _loop(self):
        """The render loop."""
        self.repaint()
        QTimer.singleShot(33, self._loop)

    def resetButtonsDown(self):
        self._mouseDown.clear()

    def resetKeysDown(self):
        self._keysDown.clear()

    def resetAllDown(self):
        self._mouseDown.clear()
        self._keysDown.clear()

    def setWalkmeshes(self, walkmeshes: list[BWM]):
        """Sets the list of walkmeshes to be rendered.

        Args:
        ----
            walkmeshes: The list of walkmeshes.
        """
        self._walkmeshes = walkmeshes

        self._bbmin = Vector3(1000000, 1000000, 1000000)
        self._bbmax = Vector3(-1000000, -1000000, -1000000)
        for walkmesh in walkmeshes:
            bbmin, bbmax = walkmesh.box()
            self._bbmin.x = min(bbmin.x, self._bbmin.x)
            self._bbmin.y = min(bbmin.y, self._bbmin.y)
            self._bbmin.z = min(bbmin.z, self._bbmin.z)
            self._bbmax.x = max(bbmax.x, self._bbmax.x)
            self._bbmax.y = max(bbmax.y, self._bbmax.y)
            self._bbmax.z = max(bbmax.z, self._bbmax.z)

        self._worldSize.x = math.fabs(self._bbmax.x - self._bbmin.x)
        self._worldSize.y = math.fabs(self._bbmax.y - self._bbmin.y)
        self._worldSize.z = math.fabs(self._bbmax.z - self._bbmin.z)

        # Reset camera
        self.camera.setZoom(1.0)

        # Erase the cache so it will be rebuilt
        self._walkmeshFaceCache = None

    def setGit(self, git: GIT):
        """Sets the GIT object used by the render to draw icons for the various git instances.

        Args:
        ----
            git: The GIT object.
        """
        self._git = git

    def setPth(self, pth: PTH):
        self._pth = pth

    def setMinimap(self, are: ARE, tpc: TPC):
        self._are = are

        tpc_rgb_data: bytearray = tpc.convert(TPCTextureFormat.RGB).data
        image = QImage(tpc_rgb_data, tpc.get().width, tpc.get().height, QImage.Format_RGB888)
        crop = QRect(0, 0, 435, 256)
        self._minimapImage = image.copy(crop)

    def snapCameraToPoint(self, point: Vector2 | Vector3, zoom: int = 8):
        self.camera.setPosition(point.x, point.y)
        self.camera.setZoom(zoom)

    def doCursorLock(self, mutableScreen: Vector2):
        """Reset the cursor to the center of the screen to prevent it from going off screen.

        Used with the FreeCam and drag camera movements and drag rotations.
        """
        global_old_pos = self.mapToGlobal(QPoint(int(self._mousePrev.x), int(self._mousePrev.y)))
        QCursor.setPos(global_old_pos)
        local_old_pos = self.mapFromGlobal(QPoint(global_old_pos.x(), global_old_pos.y()))
        mutableScreen.x = local_old_pos.x()
        mutableScreen.y = local_old_pos.y()

    def toRenderCoords(self, x: float, y: float) -> Vector2:
        """Returns a screen-space coordinates coverted from the specified world-space coordinates.

        The origin of the screen-space coordinates is the top-left of the WalkmeshRenderer widget.

        Args:
        ----
            x: The world-space X value.
            y: The world-space Y value.

        Returns:
        -------
            A vector representing a point on the widget.
        """
        cos: float = math.cos(self.camera.rotation())
        sin: float = math.sin(self.camera.rotation())
        x -= self.camera.position().x
        y -= self.camera.position().y
        x2: float = (x * cos - y * sin) * self.camera.zoom() + self.width() / 2
        y2: float = (x * sin + y * cos) * self.camera.zoom() + self.height() / 2
        return Vector2(x2, y2)

    def toWorldCoords(self, x: float, y: float) -> Vector3:
        """Returns the world-space coordinates converted from the specified screen-space coordinates.

        The Z component is calculated using the X/Y components and the walkmesh
        face the mouse is over. If there is no face underneath the mouse, the Z component is set to zero.

        Args:
        ----
            x: The screen-space X value.
            y: The screen-space Y value.

        Returns:
        -------
            A vector representing a point in the world.
        """
        y = self.height() - y
        cos = math.cos(self.camera.rotation())
        sin = math.sin(self.camera.rotation())
        x = (x - self.width() / 2) / self.camera.zoom()
        y = (y - self.height() / 2) / self.camera.zoom()
        x2 = x * cos - y * sin + self.camera.position().x
        y2 = x * sin + y * cos + self.camera.position().y

        z = self.getZCoord(x2, y2)

        return Vector3(x2, y2, z)

    def toWorldDelta(self, x: float, y: float) -> Vector2:
        """Returns the coordinates representing a change in world-space.

        This is convereted from coordinates representing a
        change in screen-space, such as the delta paramater given in a mouseMove event.

        Args:
        ----
            x: The screen-space X value.
            y: The screen-space Y value.

        Returns:
        -------
            A vector representing a change in position in the world.
        """
        cos: float = math.cos(-self.camera.rotation())
        sin: float = math.sin(-self.camera.rotation())
        x /= self.camera.zoom()
        y /= self.camera.zoom()
        x2: float = x * cos - y * sin
        y2: float = x * sin + y * cos
        return Vector2(x2, -y2)

    def getZCoord(self, x: float, y: float) -> float:
        """Returns the Z coordinate based of walkmesh data for the specified point.

        If there are overlapping faces, the walkable face will take priority.

        Args:
        ----
            x: The x coordinate.
            y: The y coordinate.

        Returns:
        -------
            The z coordinate.
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

    def materialColor(self, material: SurfaceMaterial) -> QColor:
        """Returns the color for the specified material.

        The color returned is based off the dictionary stored within the renderer widget. The programmer can customize
        what color is returned for which material. If a material is missing from the dictionary this method will return
        a magenta color instead.

        Args:
        ----
            material: The surface material.

        Returns:
        -------
            The color that represents a particular material.
        """
        return self.materialColors.get(material, self.defaultMaterialColor)

    def instancesUnderMouse(self) -> list[GITInstance]:
        """Returns a list of GITInstances under the mouse.

        Args:
        ----
            self: The current GITWindow instance

        Returns:
        -------
            list[GITInstance]: A list of GITInstance objects under the mouse
        """
        return self._instancesUnderMouse

    def pathNodesUnderMouse(self) -> list[Vector2]:
        return self._pathNodesUnderMouse

    def geomPointsUnderMouse(self) -> list[GeomPoint]:
        return self._geomPointsUnderMouse

    def isInstanceVisible(self, instance: GITInstance) -> bool | None:
        """Checks if an instance is visible based on hide settings.

        Args:
        ----
            instance (GITInstance): Instance to check visibility for.

        Returns:
        -------
            bool | None: True if visible, False if hidden, None if invalid type

        Processing Logic:
        ----------------
            - Check if instance is a valid subclass
            - Return True if type is not hidden in settings
            - Return None if type is invalid
        """
        retBool: bool | None = None
        if isinstance(instance, GITCamera):
            retBool = not self.hideCameras
        elif isinstance(instance, GITCreature):
            retBool = not self.hideCreatures
        elif isinstance(instance, GITDoor):
            retBool = not self.hideDoors
        elif isinstance(instance, GITEncounter):
            retBool = not self.hideEncounters
        elif isinstance(instance, GITPlaceable):
            retBool = not self.hidePlaceables
        elif isinstance(instance, GITSound):
            retBool = not self.hideSounds
        elif isinstance(instance, GITStore):
            retBool = not self.hideStores
        elif isinstance(instance, GITTrigger):
            retBool = not self.hideTriggers
        elif isinstance(instance, GITWaypoint):
            retBool = not self.hideWaypoints
        return retBool

    def instancePixmap(self, instance: GITInstance) -> QPixmap | None:
        retPixmap: QPixmap | None = None
        if isinstance(instance, GITCamera):
            retPixmap = self._pixmapCamera
        if isinstance(instance, GITCreature):
            retPixmap = self._pixmapCreature
        if isinstance(instance, GITDoor):
            retPixmap = self._pixmapDoor
        if isinstance(instance, GITEncounter):
            retPixmap = self._pixmapEncounter
        if isinstance(instance, GITPlaceable):
            retPixmap = self._pixmapPlaceable
        if isinstance(instance, GITTrigger):
            retPixmap = self._pixmapTrigger
        if isinstance(instance, GITSound):
            retPixmap = self._pixmapSound
        if isinstance(instance, GITStore):
            retPixmap = self._pixmapMerchant
        if isinstance(instance, GITWaypoint):
            retPixmap = self._pixmapWaypoint
        return retPixmap

    def centerCamera(self):
        """Centers the camera on the bounding box of the world.

        Args:
        ----
            self: The object calling the function

        Processing Logic:
        ----------------
            1. Sets the camera position to the center of the bounding box
            2. Calculates the world and screen sizes
            3. Calculates the scale factor to fit the world in the screen
            4. Sets the camera zoom and rotation based on the scale.
        """
        self.camera.setPosition((self._bbmin.x + self._bbmax.x) / 2, (self._bbmin.y + self._bbmax.y) / 2)
        world_w: float = self._worldSize.x
        world_h: float = self._worldSize.y

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

        self.camera.setZoom(camScale)
        self.camera.setRotation(0)

    def _buildFace(self, face: BWMFace) -> QPainterPath:
        """Returns a QPainterPath for the specified face.

        Args:
        ----
            face: A face used in a walkmesh.

        Returns:
        -------
            A QPainterPath object representing a BWMFace.
        """
        v1 = Vector2(face.v1.x, face.v1.y)
        v2 = Vector2(face.v2.x, face.v2.y)
        v3 = Vector2(face.v3.x, face.v3.y)

        path = QPainterPath()
        path.moveTo(v1.x, v1.y)
        path.lineTo(v2.x, v2.y)
        path.lineTo(v3.x, v3.y)
        path.lineTo(v1.x, v1.y)
        path.closeSubpath()

        return path

    def _buildInstanceBounds(self, instance: GITInstance) -> QPainterPath:
        """Builds a path for the instance geometry.

        Args:
        ----
            instance: The GITInstance object

        Returns:
        -------
            path: A QPainterPath representing the instance geometry.

        Processing Logic:
        ----------------
            - Checks if the instance is an encounter or trigger with geometry
            - Moves to the first point of the geometry
            - Draws lines between subsequent points
            - Closes the path by drawing a line to the first point
        """
        path = QPainterPath()
        if (isinstance(instance, (GITEncounter, GITTrigger))) and len(instance.geometry) > 0:
            path.moveTo(instance.position.x + instance.geometry[0].x, instance.position.y + instance.geometry[0].y)  # type: ignore[]
            for point in instance.geometry[1:]:
                path.lineTo(instance.position.x + point.x, instance.position.y + point.y)  # type: ignore[]
            path.lineTo(instance.position.x + instance.geometry[0].x, instance.position.y + instance.geometry[0].y)  # type: ignore[]
        return path

    def _buildInstanceBoundsPoints(self, instance: GITInstance) -> QPainterPath:
        path = QPainterPath()
        if isinstance(instance, (GITTrigger, GITEncounter)):
            for point in instance.geometry:
                size: float = 4 / self.camera.zoom()
                path.addEllipse(QPointF(instance.position.x + point.x, instance.position.y + point.y), size, size)
        return path

    def _drawImage(self, painter: QPainter, pixmap: QPixmap, x: float, y: float, rotation: float, scale: float):
        painter.save()
        painter.translate(x, y)
        painter.rotate(math.degrees(rotation))
        painter.scale(-1, 1)

        source = QRectF(0, 0, pixmap.width(), pixmap.height())
        trueWidth, trueHeight = pixmap.width() * scale, pixmap.height() * scale
        painter.drawPixmap(QRectF(-trueWidth / 2, -trueHeight / 2, trueWidth, trueHeight), pixmap, source)
        painter.restore()

    # region Events
    def paintEvent(self, e: QPaintEvent):
        """Renders the scene by drawing walkmesh faces, instances and selected objects.

        Args:
        ----
            e (QPaintEvent): The paint event

        Processing Logic:
        ----------------
            - Builds and caches walkmesh face geometry
            - Sets up camera transform
            - Fills background and draws walkmesh faces
            - Draws instances like creatures, doors as icons
            - Highlights first instance under mouse
            - Highlights first geom point under mouse
            - Highlights selected instances and geometry points
        """
        # Build walkmesh faces cache
        if self._walkmeshFaceCache is None:
            self._walkmeshFaceCache = {}
            for walkmesh in self._walkmeshes:
                # We want to draw walkable faces over the unwalkable ones
                for face in walkmesh.walkable_faces():
                    self._walkmeshFaceCache[face] = self._buildFace(face)
                for face in walkmesh.unwalkable_faces():
                    self._walkmeshFaceCache[face] = self._buildFace(face)

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
        if self._are and self._minimapImage:
            axis_to_rotation = {
                ARENorthAxis.PositiveY: 0,
                ARENorthAxis.PositiveX: 270,
                ARENorthAxis.NegativeY: 180,
                ARENorthAxis.NegativeX: 90,
            }
            rotation = axis_to_rotation[self._are.north_axis]
            rads = math.radians(-rotation)

            map_point_1_x = ((self._are.map_point_1.x - 0.5) * math.cos(rads)) - ((self._are.map_point_1.y - 0.5) * math.sin(rads)) + 0.5
            map_point_1_y = ((self._are.map_point_1.x - 0.5) * math.sin(rads)) + ((self._are.map_point_1.y - 0.5) * math.cos(rads)) + 0.5
            map_point_2_x = ((self._are.map_point_2.x - 0.5) * math.cos(rads)) - ((self._are.map_point_2.y - 0.5) * math.sin(rads)) + 0.5
            map_point_2_y = ((self._are.map_point_2.x - 0.5) * math.sin(rads)) + ((self._are.map_point_2.y - 0.5) * math.cos(rads)) + 0.5

            world_point_1_x = self._are.world_point_1.x
            world_point_1_y = self._are.world_point_1.y
            world_point_2_x = self._are.world_point_2.x
            world_point_2_y = self._are.world_point_2.y

            # X% of the width of the image
            widthPercent = abs(map_point_1_x - map_point_2_x)
            heightPercent = abs(map_point_1_y - map_point_2_y)
            # Takes up Y amount of WUs.
            widthWU = abs(world_point_1_x - world_point_2_x)
            heightWU = abs(world_point_1_y - world_point_2_y)

            # Here we determine how many world units the full texture covers
            # 100% of the image width/height covers X amount of world units
            fullWidthWU = widthWU / widthPercent
            fullHeightWU = heightWU / heightPercent

            # Now we can figure out where the X/Y coords of the image go
            # Remember world_point_1 not the corner of the image, but somewhere within the image, so we must calculate
            # where the corner of the image is in the world space.
            imageX = world_point_1_x - (fullWidthWU * map_point_1_x)
            imageY = world_point_1_y - (fullHeightWU * (1 - map_point_1_y))

            rotated: QImage = self._minimapImage.transformed(QTransform().rotate(rotation))

            targetRect = QRectF(QPointF(imageX, imageY), QPointF(imageX + fullWidthWU, imageY + fullHeightWU))
            painter.drawImage(targetRect, rotated)

        pen: QPen = QPen(QtCore.Qt.NoPen) if self.hideWalkmeshEdges else QPen(QColor(10, 10, 10, 120), 1 / self.camera.zoom(), QtCore.Qt.SolidLine)
        painter.setPen(pen)
        for face, path in self._walkmeshFaceCache.items():
            painter.setBrush(self.materialColor(face.material))
            painter.drawPath(path)

        if self.highlightBoundaries:
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
                painter.setPen(QPen(QColor(200, 200, 200, 255), self._pathEdgeWidth, QtCore.Qt.SolidLine))
                for j in self._pth.outgoing(i):
                    target: Vector2 | None = self._pth.get(j.target)
                    assert target is not None, assert_with_variable_trace(target is not None)
                    painter.drawLine(QPointF(source.x, source.y), QPointF(target.x, target.y))

            for point_2d in self._pth:
                painter.setPen(QColor(0, 0, 0, 0))
                painter.setBrush(QColor(200, 200, 200, 255))
                painter.drawEllipse(QPointF(point_2d.x, point_2d.y), self._pathNodeSize, self._pathNodeSize)

            for point_2d in self._pathNodesUnderMouse:
                painter.setPen(QColor(0, 0, 0, 0))
                painter.setBrush(QColor(255, 255, 255, 255))
                painter.drawEllipse(QPointF(point_2d.x, point_2d.y), self._pathNodeSize, self._pathNodeSize)

            for point_2d in self.pathSelection.all():
                painter.setPen(QColor(0, 0, 0, 0))
                painter.setBrush(QColor(0, 255, 0, 255))
                painter.drawEllipse(QPointF(point_2d.x, point_2d.y), self._pathNodeSize, self._pathNodeSize)

        # Draw the git instances (represented as icons)
        painter.setOpacity(0.6)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        lower_filter = self.instanceFilter.lower()
        if self._git is not None:
            for creature in [] if self.hideCreatures else self._git.creatures:
                if creature.resref and lower_filter not in str(creature.resref).lower():
                    continue
                self._drawImage(painter, self._pixmapCreature, creature.position.x, creature.position.y, math.pi + self.camera.rotation(), 1 / 16)

            for door in [] if self.hideDoors else self._git.doors:
                if door.resref and lower_filter not in str(door.resref).lower():
                    continue
                self._drawImage(painter, self._pixmapDoor, door.position.x, door.position.y, math.pi + self.camera.rotation(), 1 / 16)

            for placeable in [] if self.hidePlaceables else self._git.placeables:
                if placeable.resref and lower_filter not in str(placeable.resref).lower():
                    continue
                self._drawImage(painter, self._pixmapPlaceable, placeable.position.x, placeable.position.y, math.pi + self.camera.rotation(), 1 / 16)

            for merchant in [] if self.hideStores else self._git.stores:
                if merchant.resref and lower_filter not in str(merchant.resref).lower():
                    continue
                self._drawImage(painter, self._pixmapMerchant, merchant.position.x, merchant.position.y, math.pi + self.camera.rotation(), 1 / 16)

            for waypoint in [] if self.hideWaypoints else self._git.waypoints:
                if waypoint.resref and lower_filter not in str(waypoint.resref).lower():
                    continue
                self._drawImage(painter, self._pixmapWaypoint, waypoint.position.x, waypoint.position.y, math.pi + self.camera.rotation(), 1 / 16)

            for sound in [] if self.hideSounds else self._git.sounds:
                if sound.resref and lower_filter not in str(sound.resref).lower():
                    continue
                self._drawImage(painter, self._pixmapSound, sound.position.x, sound.position.y, math.pi + self.camera.rotation(), 1 / 16)

            for encounter in [] if self.hideEncounters else self._git.encounters:
                if encounter.resref and lower_filter not in str(encounter.resref).lower():
                    continue
                self._drawImage(painter, self._pixmapEncounter, encounter.position.x, encounter.position.y, math.pi + self.camera.rotation(), 1 / 16)

            for trigger in [] if self.hideTriggers else self._git.triggers:
                if trigger.resref and lower_filter not in str(trigger.resref).lower():
                    continue
                self._drawImage(painter, self._pixmapTrigger, trigger.position.x, trigger.position.y, math.pi + self.camera.rotation(), 1 / 16)

            for camera in [] if self.hideCameras else self._git.cameras:
                self._drawImage(painter, self._pixmapCamera, camera.position.x, camera.position.y, math.pi + self.camera.rotation(), 1 / 16)

        # Highlight the first instance that is underneath the mouse
        if self._instancesUnderMouse:
            instance = self._instancesUnderMouse[0]

            painter.setBrush(QColor(255, 255, 255, 35))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(QPointF(instance.position.x, instance.position.y), 1, 1)

            # If its a trigger or an encounter, this will draw the geometry stored inside it
            painter.setBrush(QColor(0, 220, 0, 50))
            painter.setPen(QPen(QColor(0, 255, 0, 75), 2 / self.camera.zoom()))
            painter.drawPath(self._buildInstanceBounds(instance))

        # Highlight first geom point that is underneath the mouse
        if self._geomPointsUnderMouse:
            gpoint: GeomPoint = self._geomPointsUnderMouse[0]
            point = gpoint.instance.position + gpoint.point

            if not self.hideGeomPoints:
                painter.setBrush(QColor(255, 255, 255, 200))
                painter.setPen(QtCore.Qt.NoPen)
                painter.drawEllipse(QPointF(point.x, point.y), 4 / self.camera.zoom(), 4 / self.camera.zoom())

        # Highlight selected instances
        for instance in self.instanceSelection.all():
            painter.setBrush(QColor(255, 255, 255, 70))
            painter.setPen(QPen(QColor(255, 255, 255, 255), 1 / self.camera.zoom()))
            painter.drawEllipse(QPointF(instance.position.x, instance.position.y), 1, 1)

            # If its a trigger or an encounter, this will draw the geometry stored inside it
            painter.setBrush(QColor(0, 220, 0, 100))
            painter.setPen(QPen(QColor(0, 255, 0, 150), 2 / self.camera.zoom()))
            painter.drawPath(self._buildInstanceBounds(instance))

            # If its a trigger or an encounter, this will draw the circles at the points making up the geometry
            if not self.hideGeomPoints:
                painter.setBrush(QColor(0, 255, 0, 255))
                painter.setPen(QtCore.Qt.NoPen)
                painter.drawPath(self._buildInstanceBoundsPoints(instance))

            # Draw an arrow representing the instance rotation (where applicable)
            instance_yaw_value: float | None = instance.yaw()
            if instance_yaw_value is not None:
                l1px = instance.position.x + math.cos(instance_yaw_value + math.pi / 2) * 1.1
                l1py = instance.position.y + math.sin(instance_yaw_value + math.pi / 2) * 1.1
                l2px = instance.position.x + math.cos(instance_yaw_value + math.pi / 2) * 1.3
                l2py = instance.position.y + math.sin(instance_yaw_value + math.pi / 2) * 1.3
                painter.setBrush(QtCore.Qt.NoBrush)
                painter.setPen(QPen(QColor(255, 255, 255, 255), 0.15))
                painter.drawLine(QPointF(l1px, l1py), QPointF(l2px, l2py))

        # Highlight selected geometry points
        for geomPoint in self.geometrySelection.all():
            point: Vector3 = geomPoint.point + geomPoint.instance.position
            painter.setBrush(QColor(255, 255, 255, 255))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(QPointF(point.x, point.y), 4 / self.camera.zoom(), 4 / self.camera.zoom())

    def wheelEvent(self, e: QWheelEvent):
        self.mouseScrolled.emit(Vector2(e.angleDelta().x(), e.angleDelta().y()), self._mouseDown, self._keysDown)

    def mouseMoveEvent(self, e: QMouseEvent):
        """Handles mouse move events.

        Args:
        ----
            e: QMouseEvent - Mouse event object

        Processes mouse movement:
            - Updates mouse position
            - Emits mouseMoved signal
            - Finds instances and geometry points under mouse.
        """
        super().mouseMoveEvent(e)
        coords = Vector2(e.x(), e.y())
        coordsDelta = Vector2(coords.x - self._mousePrev.x, coords.y - self._mousePrev.y)
        self.mouseMoved.emit(coords, coordsDelta, self._mouseDown, self._keysDown)
        self._mousePrev = coords  # Always assign mousePrev after emitting: allows signal handlers (e.g. ModuleDesigner, GITEditor) to handle cursor lock.

        self._instancesUnderMouse: list[GITInstance] = []
        self._geomPointsUnderMouse: list[GeomPoint] = []
        self._pathNodesUnderMouse: list[Vector2] = []

        world: Vector2 = Vector2.from_vector3(self.toWorldCoords(coords.x, coords.y))  # Mouse pos in world

        if self._git is not None:
            instances: list[GITInstance] = self._git.instances()
            for instance in instances:
                position = Vector2(instance.position.x, instance.position.y)
                if position.distance(world) <= 1 and self.isInstanceVisible(instance):
                    self.instanceHovered.emit(instance)
                    self._instancesUnderMouse.append(instance)

                # Check if mouse is over vertex for encounter/trigger geometry
                if isinstance(instance, GITEncounter) or (isinstance(instance, GITTrigger) and instance in self.instanceSelection.all()):
                    for point in instance.geometry:
                        pworld = Vector2.from_vector3(instance.position + point)
                        if pworld.distance(world) <= 0.5:
                            #RobustRootLogger().debug(f"pworld distance check, append GeomPoint({instance}, {point}), total geompoints: {len(self._geomPointsUnderMouse)+1}")
                            self._geomPointsUnderMouse.append(GeomPoint(instance, point))

        if self._pth is not None:
            for point in self._pth:
                if point.distance(world) <= self._pathNodeSize:
                    self._pathNodesUnderMouse.append(point)

    def focusOutEvent(self, e: QFocusEvent | None):
        self._mouseDown.clear()  # Clears the set when focus is lost
        self._keysDown.clear()  # Clears the set when focus is lost
        super().focusOutEvent(e)  # Ensures that the default handler is still executed
        #RobustRootLogger().debug("WalkmeshRenderer.focusOutEvent: clearing all keys/buttons held down.")

    def mousePressEvent(self, e: QMouseEvent | None):
        super().mousePressEvent(e)
        if e is None:
            return
        button = e.button()
        self._mouseDown.add(button)
        coords = Vector2(e.x(), e.y())
        self.mousePressed.emit(coords, self._mouseDown, self._keysDown)
        #RobustRootLogger().debug(f"WalkmeshRenderer.mousePressEvent: {self._mouseDown}, e.button() '{button}'")

    def mouseReleaseEvent(self, e: QMouseEvent | None):
        super().mouseReleaseEvent(e)
        if e is None:
            return
        button = e.button()
        self._mouseDown.discard(button)
        coords = Vector2(e.x(), e.y())
        self.mouseReleased.emit(coords, self._mouseDown, self._keysDown)
        #RobustRootLogger().debug(f"WalkmeshRenderer.mouseReleaseEvent: {self._mouseDown}, e.button() '{button}'")

    def keyPressEvent(self, e: QKeyEvent | None):
        super().keyPressEvent(e)
        if e is None:
            return
        key = e.key()
        if e is None:
            return
        self._keysDown.add(key)
        if self.underMouse():
            self.keyPressed.emit(self._mouseDown, self._keysDown)
        #key_name = getQtKeyStringLocalized(key)
        #RobustRootLogger().debug(f"WalkmeshRenderer.keyReleaseEvent: {self._keysDown}, e.key() '{key_name}'")

    def keyReleaseEvent(self, e: QKeyEvent | None):
        super().keyReleaseEvent(e)
        if e is None:
            return
        key = e.key()
        self._keysDown.discard(key)
        if self.underMouse():
            self.keyReleased.emit(self._mouseDown, self._keysDown)
        #key_name = getQtKeyStringLocalized(key)
        #RobustRootLogger().debug(f"WalkmeshRenderer.keyReleaseEvent: {self._keysDown}, e.key() '{key_name}'")

    # endregion
