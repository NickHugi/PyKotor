from __future__ import annotations

import math
from copy import copy
from typing import (
    TYPE_CHECKING,
    Dict,
    Generic,
    List,
    NamedTuple,
    Optional,
    Set,
    TypeVar,
    Union,
)

from PyQt5 import QtCore
from PyQt5.QtCore import QPointF, QRectF, QTimer
from PyQt5.QtGui import (
    QColor,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPen,
    QPixmap,
    QTransform,
    QWheelEvent,
)
from PyQt5.QtWidgets import QWidget
from toolset.utils.misc import clamp

from pykotor.common.geometry import SurfaceMaterial, Vector2, Vector3
from pykotor.resource.generics.git import (
    GIT,
    GITCamera,
    GITCreature,
    GITDoor,
    GITEncounter,
    GITInstance,
    GITPlaceable,
    GITSound,
    GITStore,
    GITTrigger,
    GITWaypoint,
)

if TYPE_CHECKING:
    from pykotor.resource.formats.bwm import BWM, BWMFace

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

    def setPosition(self, x: float, y: float) -> None:
        self._position.x = x
        self._position.y = y

    def nudgePosition(self, x: float, y: float) -> None:
        self._position.x += x
        self._position.y += y

    def setRotation(self, rotation: float) -> None:
        self._rotation = rotation

    def nudgeRotation(self, rotation: float) -> None:
        self._rotation += rotation

    def setZoom(self, zoom: float) -> None:
        self._zoom = clamp(zoom, 0.1, 100)

    def nudgeZoom(self, zoom: float) -> None:
        self._zoom = clamp(self._zoom + zoom, 0.1, 100)


class WalkmeshSelection(Generic[T]):
    def __init__(self):
        self._selection: List[T] = []

    def remove(self, element: T) -> None:
        self._selection.remove(element)

    def last(self) -> Optional[T]:
        return self._selection[-1] if self._selection else None

    def count(self) -> int:
        return len(self._selection)

    def isEmpty(self) -> bool:
        return len(self._selection) == 0

    def all(self) -> List[T]:
        return copy(self._selection)

    def get(self, index: int) -> T:
        return self._selection[index]

    def clear(self) -> None:
        self._selection.clear()

    def select(self, elements: List[T], clearExisting: bool = True) -> None:
        if clearExisting:
            self._selection.clear()
        self._selection.extend(elements)


class WalkmeshRenderer(QWidget):
    mouseMoved = QtCore.pyqtSignal(object, object, object, object)  # screen coords, screen delta, mouse, keys
    """Signal emitted when mouse is moved over the widget."""

    mouseScrolled = QtCore.pyqtSignal(object, object, object)  # screen delta, mouse, keys
    """Signal emitted when mouse is scrolled over the widget."""

    mouseReleased = QtCore.pyqtSignal(object, object, object)  # screen coords, mouse, keys
    """Signal emitted when a mouse button is released after being pressed on the widget."""

    mousePressed = QtCore.pyqtSignal(object, object, object)  # screen coords, mouse, keys
    """Signal emitted when a mouse button is pressed on the widget."""

    keyPressed = QtCore.pyqtSignal(object, object)  # mouse keys

    keyReleased = QtCore.pyqtSignal(object, object)  # mouse keys

    instanceHovered = QtCore.pyqtSignal(object)  # instance

    instancePressed = QtCore.pyqtSignal(object)  # instance

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self._walkmeshes: List[BWM] = []
        self._git: Optional[GIT] = None

        # Min/Max points and lengths for each axis
        self._bbmin: Vector3 = Vector3.from_null()
        self._bbmax: Vector3 = Vector3.from_null()
        self._worldSize: Vector3 = Vector3.from_null()

        self.camera: WalkmeshCamera = WalkmeshCamera()
        self.instanceSelection: WalkmeshSelection[GITInstance] = WalkmeshSelection()
        self.geometrySelection: WalkmeshSelection[GeomPoint] = WalkmeshSelection()

        self._mousePrev: Vector2 = Vector2(self.cursor().pos().x(), self.cursor().pos().y())
        self._walkmeshFaceCache: Optional[List[QPainterPath]] = None

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

        self.materialColors: Dict[SurfaceMaterial, int] = {}

        self._keysDown: Set[int] = set()
        self._mouseDown: Set[int] = set()

        self._pixmapCreature: QPixmap = QPixmap(":/images/icons/k1/creature.png")
        self._pixmapDoor: QPixmap = QPixmap(":/images/icons/k1/door.png")
        self._pixmapPlaceable: QPixmap = QPixmap(":/images/icons/k1/placeable.png")
        self._pixmapMerchant: QPixmap = QPixmap(":/images/icons/k1/merchant.png")
        self._pixmapWaypoint: QPixmap = QPixmap(":/images/icons/k1/waypoint.png")
        self._pixmapSound: QPixmap = QPixmap(":/images/icons/k1/sound.png")
        self._pixmapTrigger: QPixmap = QPixmap(":/images/icons/k1/trigger.png")
        self._pixmapEncounter: QPixmap = QPixmap(":/images/icons/k1/encounter.png")
        self._pixmapCamera: QPixmap = QPixmap(":/images/icons/k1/camera.png")

        self._instancesUnderMouse: List[GITInstance] = []
        self._geomPointsUnderMouse: List[GeomPoint] = []

        self._loop()

    def _loop(self) -> None:
        """The render loop."""
        self.repaint()
        QTimer.singleShot(33, self._loop)

    def setWalkmeshes(self, walkmeshes: List[BWM]) -> None:
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

    def setGit(self, git: GIT) -> None:
        """Sets the GIT object used by the render to draw icons for the various git instances.

        Args:
        ----
            git: The GIT object.
        """
        self._git = git

    def snapCameraToPoint(self, point: Union[Vector2, Vector3], zoom: int = 8) -> None:
        self.camera.setPosition(point.x, point.y)
        self.camera.setZoom(zoom)

    def toRenderCoords(self, x: float, y: float) -> Vector2:
        """Returns a screen-space coordinates coverted from the specified world-space coordinates. The origin of the
        screen-space coordinates is the top-left of the WalkmeshRenderer widget.

        Args:
        ----
            x: The world-space X value.
            y: The world-space Y value.

        Returns:
        -------
            A vector representing a point on the widget.
        """
        cos = math.cos(self.camera.rotation())
        sin = math.sin(self.camera.rotation())
        x -= self.camera.position().x
        y -= self.camera.position().y
        x2 = (x*cos - y*sin) * self.camera.zoom() + self.width() / 2
        y2 = (x*sin + y*cos) * self.camera.zoom() + self.height() / 2
        return Vector2(x2, y2)

    def toWorldCoords(self, x: float, y: float) -> Vector3:
        """Returns the world-space coordinates converted from the specified screen-space coordinates. The Z component
        is calculated using the X/Y components and the walkmesh face the mouse is over. If there is no face underneath
        the mouse, the Z component is set to zero.

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
        x2 = x*cos - y*sin + self.camera.position().x
        y2 = x*sin + y*cos + self.camera.position().y

        z = self.getZCoord(x2, y2)

        return Vector3(x2, y2, z)

    def toWorldDelta(self, x: float, y: float) -> Vector2:
        """Returns the coordinates representing a change in world-space. This is convereted from coordinates representing
        a change in screen-space, such as the delta paramater given in a mouseMove event.

        Args:
        ----
            x: The screen-space X value.
            y: The screen-space Y value.

        Returns:
        -------
            A vector representing a change in position in the world.
        """
        cos = math.cos(-self.camera.rotation())
        sin = math.sin(-self.camera.rotation())
        x = x / self.camera.zoom()
        y = y / self.camera.zoom()
        x2 = x*cos - y*sin
        y2 = x*sin + y*cos
        return Vector2(x2, -y2)

    def getZCoord(self, x: float, y: float) -> float:
        """Returns the Z coordinate based of walkmesh data for the specified point. If there are overlapping faces, the
        walkable face will take priority.

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
        face: Optional[BWMFace] = None
        for walkmesh in self._walkmeshes:
            over = walkmesh.faceAt(x, y)
            if over and (
                face is None or (
                    not face.material.walkable()
                    and over.material.walkable()
                )
            ):
                face = over
        return 0.0 if face is None else face.determine_z(x, y)

    def materialColor(self, material: SurfaceMaterial) -> QColor:
        """Returns the color for the specified material.

        The color returned is based off the dictionary stored within the renderer widget. The programmer can customize
        what color is returned for which material. If a material is missing from the dictionary this method will return
        a magenta color instead.

        Args:
        ----
            m
        ----aterial: The surface material.

        Returns:
        -------
            The color that represents a particular material.
        """
        return self.materialColors[material] if material in self.materialColors else QColor(255, 0, 255)

    def instancesUnderMouse(self) -> List[GITInstance]:
        return self._instancesUnderMouse

    def isInstanceVisible(self, instance: GITInstance) -> bool | None:
        if isinstance(instance, GITCreature):
            return not self.hideCreatures
        if isinstance(instance, GITDoor):
            return not self.hideDoors
        if isinstance(instance, GITPlaceable):
            return not self.hidePlaceables
        if isinstance(instance, GITTrigger):
            return not self.hideTriggers
        if isinstance(instance, GITCamera):
            return not self.hideCameras
        if isinstance(instance, GITEncounter):
            return not self.hideEncounters
        if isinstance(instance, GITSound):
            return not self.hideSounds
        if isinstance(instance, GITWaypoint):
            return not self.hideWaypoints
        if isinstance(instance, GITStore):
            return not self.hideStores
        return None

    def instancePixmap(self, instance: GITInstance) -> QPixmap | None:
        if isinstance(instance, GITCreature):
            return self._pixmapCreature
        if isinstance(instance, GITDoor):
            return self._pixmapDoor
        if isinstance(instance, GITPlaceable):
            return self._pixmapPlaceable
        if isinstance(instance, GITTrigger):
            return self._pixmapTrigger
        if isinstance(instance, GITCamera):
            return self._pixmapCamera
        if isinstance(instance, GITEncounter):
            return self._pixmapEncounter
        if isinstance(instance, GITSound):
            return self._pixmapSound
        if isinstance(instance, GITWaypoint):
            return self._pixmapWaypoint
        if isinstance(instance, GITStore):
            return self._pixmapMerchant
        return None

    def geomPointsUnderMouse(self) -> List[GeomPoint]:
        return self._geomPointsUnderMouse

    def centerCamera(self) -> None:
        self.camera.setPosition((self._bbmin.x + self._bbmax.x) / 2, (self._bbmin.y + self._bbmax.y) / 2)
        world_w = self._worldSize.x
        world_h = self._worldSize.y

        # If the GIT is being loaded directly after the window opens the widget won't have appropriately resized itself,
        # so we check for this and set the sizes to what it should be by default.
        if self.width() == 100:
            screen_w = 520
            screen_h = 507
        else:
            screen_w = self.width()
            screen_h = self.height()

        scale_w = screen_w / world_w if world_w != 0 else 0
        scale_h = screen_h / world_h if world_h != 0 else 0
        camScale = min(scale_w, scale_h)

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
        path = QPainterPath()
        if (isinstance(instance, (GITEncounter, GITTrigger))) and len(instance.geometry) > 0:
            path.moveTo(instance.position.x + instance.geometry[0].x, instance.position.y + instance.geometry[0].y)
            for point in instance.geometry[1:]:
                path.lineTo(instance.position.x + point.x, instance.position.y + point.y)
            path.lineTo(instance.position.x + instance.geometry[0].x, instance.position.y + instance.geometry[0].y)
        return path

    def _buildInstanceBoundsPoints(self, instance: GITInstance) -> QPainterPath:
        path = QPainterPath()
        if isinstance(instance, (GITTrigger, GITEncounter)):
            for point in instance.geometry:
                size = 4 / self.camera.zoom()
                path.addEllipse(QPointF(instance.position.x + point.x, instance.position.y + point.y), size, size)
        return path

    def _drawImage(self, painter: QPainter, pixmap: QPixmap, x: float, y: float, rotation: float, scale: float):
        source = QRectF(0, 0, pixmap.width(), pixmap.height())
        trueWidth, trueHeight = pixmap.width()*scale, pixmap.height()*scale
        painter.save()
        painter.translate(x, y)
        painter.rotate(math.degrees(rotation))
        painter.scale(-1, 1)
        painter.drawPixmap(QRectF(-trueWidth/2, -trueHeight/2, trueWidth, trueHeight), pixmap, source)
        painter.restore()

    # region Events
    def paintEvent(self, e: QPaintEvent) -> None:
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
        painter.setPen(QPen(QColor(10, 10, 10, 120),
                            1 / self.camera.zoom(),
                            QtCore.Qt.SolidLine) if not self.hideWalkmeshEdges else QPen(QtCore.Qt.NoPen))
        for face, path in self._walkmeshFaceCache.items():
            painter.setBrush(self.materialColor(face.material))
            painter.drawPath(path)

        if self.highlightBoundaries:
            for walkmesh in self._walkmeshes:
                for face in walkmesh.walkable_faces():
                    painter.setPen(QPen(QColor(255, 0, 0), 3/self.camera.zoom()))
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

        # Draw the git instances (represented as icons)
        painter.setOpacity(0.6)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        if self._git is not None:
            for creature in self._git.creatures if not self.hideCreatures else []:
                if self.instanceFilter.lower() not in creature.resref.get().lower() and creature.resref.get() != "":
                    continue
                self._drawImage(painter, self._pixmapCreature, creature.position.x, creature.position.y, 3.142+self.camera.rotation(), 1/16)

            for door in self._git.doors if not self.hideDoors else []:
                if self.instanceFilter.lower() not in door.resref.get().lower() and door.resref.get() != "":
                    continue
                self._drawImage(painter, self._pixmapDoor, door.position.x, door.position.y, 3.142+self.camera.rotation(), 1/16)

            for placeable in self._git.placeables if not self.hidePlaceables else []:
                if self.instanceFilter.lower() not in placeable.resref.get().lower() and placeable.resref.get() != "":
                    continue
                self._drawImage(painter, self._pixmapPlaceable, placeable.position.x, placeable.position.y, 3.142+self.camera.rotation(), 1/16)

            for merchant in self._git.stores if not self.hideStores else []:
                if self.instanceFilter.lower() not in merchant.resref.get().lower() and merchant.resref.get() != "":
                    continue
                self._drawImage(painter, self._pixmapMerchant, merchant.position.x, merchant.position.y, 3.142+self.camera.rotation(), 1/16)

            for waypoint in self._git.waypoints if not self.hideWaypoints else []:
                if self.instanceFilter.lower() not in waypoint.resref.get().lower() and waypoint.resref.get() != "":
                    continue
                self._drawImage(painter, self._pixmapWaypoint, waypoint.position.x, waypoint.position.y, 3.142+self.camera.rotation(), 1/16)

            for sound in self._git.sounds if not self.hideSounds else []:
                if self.instanceFilter.lower() not in sound.resref.get().lower() and sound.resref.get() != "":
                    continue
                self._drawImage(painter, self._pixmapSound, sound.position.x, sound.position.y, 3.142+self.camera.rotation(), 1/16)

            for encounter in self._git.encounters if not self.hideEncounters else []:
                if self.instanceFilter.lower() not in encounter.resref.get().lower() and encounter.resref.get() != "":
                    continue
                self._drawImage(painter, self._pixmapEncounter, encounter.position.x, encounter.position.y, 3.142+self.camera.rotation(), 1/16)

            for trigger in self._git.triggers if not self.hideTriggers else []:
                if self.instanceFilter.lower() not in trigger.resref.get().lower() and trigger.resref.get() != "":
                    continue
                self._drawImage(painter, self._pixmapTrigger, trigger.position.x, trigger.position.y, 3.142+self.camera.rotation(), 1/16)

            for camera in self._git.cameras if not self.hideCameras else []:
                self._drawImage(painter, self._pixmapCamera, camera.position.x, camera.position.y, 3.142+self.camera.rotation(), 1/16)

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
            gpoint = self._geomPointsUnderMouse[0]
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
            if instance.yaw() is not None:
                l1px = instance.position.x + math.cos(instance.yaw() + math.pi/2) * 1.1
                l1py = instance.position.y + math.sin(instance.yaw() + math.pi/2) * 1.1
                l2px = instance.position.x + math.cos(instance.yaw() + math.pi/2) * 1.3
                l2py = instance.position.y + math.sin(instance.yaw() + math.pi/2) * 1.3
                painter.setBrush(QtCore.Qt.NoBrush)
                painter.setPen(QPen(QColor(255, 255, 255, 255), 0.15))
                painter.drawLine(QPointF(l1px, l1py), QPointF(l2px, l2py))

        # Highlight selected geometry points
        for geomPoint in self.geometrySelection.all():
            point = geomPoint.point + geomPoint.instance.position
            painter.setBrush(QColor(255, 255, 255, 255))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(QPointF(point.x, point.y), 4 / self.camera.zoom(), 4 / self.camera.zoom())

    def wheelEvent(self, e: QWheelEvent) -> None:
        self.mouseScrolled.emit(Vector2(e.angleDelta().x(), e.angleDelta().y()), self._mouseDown, self._keysDown)

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        coords = Vector2(e.x(), e.y())
        coordsDelta = Vector2(coords.x - self._mousePrev.x, coords.y - self._mousePrev.y)
        self._mousePrev = coords
        self.mouseMoved.emit(coords, coordsDelta, self._mouseDown, self._keysDown)

        self._instancesUnderMouse = []
        self._geomPointsUnderMouse = []
        if self._git is not None:
            instances = self._git.instances()
            world = Vector2.from_vector3(self.toWorldCoords(coords.x, coords.y))  # Mouse pos in world
            for instance in instances:
                position = Vector2(instance.position.x, instance.position.y)
                if position.distance(world) <= 1 and self.isInstanceVisible(instance):
                    self.instanceHovered.emit(instance)
                    self._instancesUnderMouse.append(instance)

                # Check if mouse is over vertex for encounter/trigger geometry
                if isinstance(instance, GITEncounter) or isinstance(instance, GITTrigger) and instance in self.instanceSelection.all():
                    for point in instance.geometry:
                        pworld = Vector2.from_vector3(instance.position + point)
                        if pworld.distance(world) <= 0.5:
                            self._geomPointsUnderMouse.append(GeomPoint(instance, point))

    def mousePressEvent(self, e: QMouseEvent) -> None:
        self._mouseDown.add(e.button())
        coords = Vector2(e.x(), e.y())
        self.mousePressed.emit(coords, self._mouseDown, self._keysDown)

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        self._mouseDown.discard(e.button())

        coords = Vector2(e.x(), e.y())
        self.mouseReleased.emit(coords, e.buttons(), self._keysDown)

    def keyPressEvent(self, e: QKeyEvent) -> None:
        self._keysDown.add(e.key())
        if self.underMouse():
            self.keyPressed.emit(self._mouseDown, self._keysDown)

    def keyReleaseEvent(self, e: QKeyEvent) -> None:
        self._keysDown.discard(e.key())
        if self.underMouse():
            self.keyReleased.emit(self._mouseDown, self._keysDown)
    # endregion
