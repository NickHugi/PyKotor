import math
from copy import copy
from typing import List, Optional, Dict, Set, Tuple, NamedTuple

from PyQt5 import QtCore
from PyQt5.QtCore import QTimer, QPointF, QRectF
from PyQt5.QtGui import QPixmap, QPaintEvent, QPainter, QWheelEvent, QMouseEvent, QColor, QPainterPath, QPen, QBrush, \
    QKeyEvent, QTransform
from PyQt5.QtWidgets import QWidget
from pykotor.common.geometry import Vector3, Vector2, SurfaceMaterial
from pykotor.resource.formats.bwm import BWM, BWMFace
from pykotor.resource.generics.git import GIT, GITTrigger, GITInstance, GITEncounter, GITSound, GITCreature, GITDoor, \
    GITPlaceable, GITCamera, GITWaypoint, GITStore


class GeomPoint(NamedTuple):
    instance: GITInstance
    point: Vector3


class WalkmeshRenderer(QWidget):
    mouseMoved = QtCore.pyqtSignal(object, object, object, object)  # screen coords, screen delta, mouse, keys
    """Signal emitted when mouse is moved over the widget."""

    mouseScrolled = QtCore.pyqtSignal(object, object, object)  # screen delta, mouse, keys
    """Signal emitted when mouse is scrolled over the widget."""

    mouseReleased = QtCore.pyqtSignal(object, object, object)  # screen coords, mouse, keys
    """Signal emitted when a mouse button is released after being pressed on the widget."""

    mousePressed = QtCore.pyqtSignal(object, object, object)  # screen coords, mouse, keys
    """Signal emitted when a mouse button is pressed on the widget."""

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

        self._camPosition: Vector2 = Vector2.from_null()
        self._camRotation: float = 0.0
        self._camScale = 1.0

        self._mousePrev: Vector2 = Vector2(self.cursor().pos().x(), self.cursor().pos().y())
        self._walkmeshFaceCache: Optional[List[QPainterPath]] = None

        self.highlightOnHover: bool = False
        self.highlightBoundaries: bool = False

        self.hideWalkmeshEdges: bool = False

        self.hideGeomPoints: bool = True

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
        self._instancesSelected: List[GITInstance] = []
        self._geomPointsUnderMouse: List[GeomPoint] = []
        self._geomPointsSelected: List[GeomPoint] = []

        self._loop()

    def _loop(self) -> None:
        """
        The render loop.
        """
        self.repaint()
        QTimer.singleShot(33, self._loop)

    def setWalkmeshes(self, walkmeshes: List[BWM]) -> None:
        """
        Sets the list of walkmeshes to be rendered.

        Args:
            walkmeshes: The list of walkmeshes.
        """
        self._walkmeshes = walkmeshes

        self._bbmin = Vector3(1000000, 1000000, 1000000)
        self._bbmax = Vector3(-1000000, -1000000, -1000000)
        for i, walkmesh in enumerate(walkmeshes):
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
        self.setCameraZoom(1.0)

        # Erase the cache so it will be rebuilt
        self._walkmeshFaceCache = None

    def setGit(self, git: GIT) -> None:
        """
        Sets the GIT object used by the render to draw icons for the various git instances.

        Args:
            git: The GIT object.
        """
        self._git = git

    def toRenderCoords(self, x: float, y: float) -> Vector2:
        """
        Returns a screen-space coordinates coverted from the specified world-space coordinates. The origin of the
        screen-space coordinates is the top-left of the WalkmeshRenderer widget.

        Args:
            x: The world-space X value.
            y: The world-space Y value.

        Returns:
            A vector representing a point on the widget.
        """
        cos = math.cos(self._camRotation)
        sin = math.sin(self._camRotation)
        x -= self._camPosition.x
        y -= self._camPosition.y
        x2 = (x*cos - y*sin) * self._camScale + self.width() / 2
        y2 = (x*sin + y*cos) * self._camScale + self.height() / 2
        return Vector2(x2, y2)

    def toWorldCoords(self, x: float, y: float) -> Vector3:
        """
        Returns the world-space coordinates converted from the specified screen-space coordinates. The Z component
        is calculated using the X/Y components and the walkmesh face the mouse is over. If there is no face underneath
        the mouse, the Z component is set to zero.

        Args:
            x: The screen-space X value.
            y: The screen-space Y value.

        Returns:
            A vector representing a point in the world.
        """
        y = self.height() - y
        cos = math.cos(self._camRotation)
        sin = math.sin(self._camRotation)
        x = (x - self.width() / 2) / self._camScale
        y = (y - self.height() / 2) / self._camScale
        x2 = x*cos - y*sin + self._camPosition.x
        y2 = x*sin + y*cos + self._camPosition.y

        z = self.getZCoord(x2, y2)

        return Vector3(x2, y2, z)

    def toWorldDelta(self, x: float, y: float) -> Vector2:
        """
        Returns the coordinates representing a change in world-space. This is convereted from coordinates representing
        a change in screen-space, such as the delta paramater given in a mouseMove event.

        Args:
            x: The screen-space X value.
            y: The screen-space Y value.

        Returns:
            A vector representing a change in position in the world.
        """
        cos = math.cos(-self._camRotation)
        sin = math.sin(-self._camRotation)
        x = x / self._camScale
        y = y / self._camScale
        x2 = x*cos - y*sin
        y2 = x*sin + y*cos
        return Vector2(x2, -y2)

    def getZCoord(self, x: float, y: float) -> float:
        """
        Returns the Z coordinate based of walkmesh data for the specificied point. If there are overlapping faces, the
        walkable face will take priority.

        Args:
            x: The x coordinate.
            y: The y coordinate.

        Returns:
            The z coordinate.
        """
        # We need to find a face in the walkmesh thats underneath the mouse to find the Z
        # We also want to prioritize walkable faces
        # And if we cant find a face, then set the Z to 0.0
        face: Optional[BWMFace] = None
        for walkmesh in self._walkmeshes:
            if over := walkmesh.faceAt(x, y):
                if face is None:
                    face = over
                elif not face.material.walkable() and over.material.walkable():
                    face = over
        z = 0.0 if face is None else face.determine_z(x, y)
        return z

    def materialColor(self, material: SurfaceMaterial) -> QColor:
        """
        Returns the color for the specified material.

        The color returned is based off the dictionary stored within the renderer widget. The programmer can customize
        what color is returned for which material. If a material is missing from the dictionary this method will return
        a magenta color instead.

        Args:
            material: The surface material.

        Returns:
            The color that represents a particular material.
        """
        return self.materialColors[material] if material in self.materialColors else QColor(255, 0, 255)

    # region Instance
    def instancesUnderMouse(self) -> List[GITInstance]:
        return self._instancesUnderMouse

    def selectedInstances(self) -> List[GITInstance]:
        return self._instancesSelected

    def clearSelectedInstances(self) -> None:
        self._instancesSelected = []

    def selectInstances(self, instances: List[GITInstance], clearExisting: bool = True) -> None:
        if clearExisting:
            self.clearSelectedInstances()
        self._instancesSelected.extend(instances)

    def selectInstance(self, instance: GITInstance, clearExisting: bool = True) -> None:
        if clearExisting:
            self.clearSelectedInstances()
        self._instancesSelected.append(instance)

    def isInstanceVisible(self, instance: GITInstance) -> bool:
        if isinstance(instance, GITCreature):
            return not self.hideCreatures
        elif isinstance(instance, GITDoor):
            return not self.hideDoors
        elif isinstance(instance, GITPlaceable):
            return not self.hidePlaceables
        elif isinstance(instance, GITTrigger):
            return not self.hideTriggers
        elif isinstance(instance, GITCamera):
            return not self.hideCameras
        elif isinstance(instance, GITEncounter):
            return not self.hideEncounters
        elif isinstance(instance, GITSound):
            return not self.hideSounds
        elif isinstance(instance, GITWaypoint):
            return not self.hideWaypoints
        elif isinstance(instance, GITStore):
            return not self.hideStores

    def instancePixmap(self, instance: GITInstance) -> QPixmap:
        if isinstance(instance, GITCreature):
            return self._pixmapCreature
        elif isinstance(instance, GITDoor):
            return self._pixmapDoor
        elif isinstance(instance, GITPlaceable):
            return self._pixmapPlaceable
        elif isinstance(instance, GITTrigger):
            return self._pixmapTrigger
        elif isinstance(instance, GITCamera):
            return self._pixmapCamera
        elif isinstance(instance, GITEncounter):
            return self._pixmapEncounter
        elif isinstance(instance, GITSound):
            return self._pixmapSound
        elif isinstance(instance, GITWaypoint):
            return self._pixmapWaypoint
        elif isinstance(instance, GITStore):
            return self._pixmapMerchant
    # endregion

    # region GeomPoint
    def geomPointsUnderMouse(self) -> List[GeomPoint]:
        return self._geomPointsUnderMouse

    def selectedGeomPoints(self) -> List[GeomPoint]:
        return self._geomPointsSelected

    def clearSelectedGeomPoints(self) -> None:
        self._geomPointsSelected = []

    def selectGeomPoint(self, geomPoint: GeomPoint, clearExisting: bool = True) -> None:
        if clearExisting:
            self.clearSelectedGeomPoints()
        self._geomPointsSelected.append(geomPoint)
    # endregion

    # region Camera Transformations
    def cameraZoom(self) -> float:
        """
        Returns the current zoom value of the camera.

        Returns:
            The camera zoom value.
        """
        return self._camScale

    def setCameraZoom(self, zoom: float) -> None:
        """
        Sets the camera zoom to the specified value. Values smaller than 1.0 are clamped.

        Args:
            zoom: Zoom-in value.
        """
        self._camScale = max(zoom, 1.0)

    def zoomInCamera(self, zoom: float) -> None:
        """
        Changes the camera zoom value by the specified amount.

        This method is a wrapper for setCameraZoom().

        Args:
            zoom: The value to increase by.
        """
        self.setCameraZoom(self._camScale + zoom)

    def cameraPosition(self) -> Vector2:
        """
        Returns the position of the camera.

        Returns:
            The camera position vector.
        """
        return copy(self._camPosition)

    def setCameraPosition(self, x: float, y: float) -> None:
        """
        Sets the camera position to the specified values.

        Args:
            x: The new X value.
            y: The new Y value.
        """
        self._camPosition.x = x
        self._camPosition.y = y

    def panCamera(self, x: float, y: float) -> None:
        """
        Moves the camera by the specified amount. The movement takes into account both the rotation and zoom of the
        camera.

        Args:
            x: Units to move the x coordinate.
            y: Units to move the y coordinate.
        """
        self._camPosition.x += x
        self._camPosition.y += y

    def cameraRotation(self) -> float:
        """
        Returns the current angle of the camera in radians.

        Returns:
            The camera angle in radians.
        """
        return self._camRotation

    def setCameraRotation(self, radians: float) -> None:
        """
        Sets the camera rotation to the specified angle.

        Args:
            radians: The new camera angle.
        """
        self._camRotation = radians

    def rotateCamera(self, radians: float) -> None:
        """
        Rotates the camera by the angle specified.

        Args:
            radians: The angle of rotation to apply to the camera.
        """
        self._camRotation += radians

    def centerCamera(self) -> None:
        self._camPosition.x = (self._bbmin.x + self._bbmax.x) / 2
        self._camPosition.y = (self._bbmin.y + self._bbmax.y) / 2
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

        scale_w = screen_w / world_w
        scale_h = screen_h / world_h
        camScale = min(scale_w, scale_h)

        self._camScale = camScale

        self._camRotation = 0
    # endregion

    def _buildFace(self, face: BWMFace) -> QPainterPath:
        """
        Returns a QPainterPath for the specified face.

        Args:
            face: A face used in a walkmesh.

        Returns:
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
        if (isinstance(instance, GITTrigger) or isinstance(instance, GITEncounter)) and len(instance.geometry) > 0:
            path.moveTo(instance.position.x + instance.geometry[0].x, instance.position.y + instance.geometry[0].y)
            for point in instance.geometry[1:]:
                path.lineTo(instance.position.x + point.x, instance.position.y + point.y)
            path.lineTo(instance.position.x + instance.geometry[0].x, instance.position.y + instance.geometry[0].y)
        return path

    def _buildInstanceBoundsPoints(self, instance: GITInstance) -> QPainterPath:
        path = QPainterPath()
        if isinstance(instance, GITTrigger) or isinstance(instance, GITEncounter):
            for point in instance.geometry:
                size = 4 / self._camScale
                path.addEllipse(QPointF(instance.position.x + point.x, instance.position.y + point.y), size, size)
        return path

    def _drawImage(self, painter: QPainter, pixmap: QPixmap, x: float, y: float, rotation: float, scale: float):
        source = QRectF(0, 0, pixmap.width(), pixmap.height())
        trueWidth, trueHeight = pixmap.width()*scale, pixmap.height()*scale
        painter.save()
        painter.translate(x, y)
        painter.rotate(math.degrees(rotation))
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
        transform.rotate(math.degrees(self._camRotation))
        transform.scale(self._camScale, -self._camScale)
        transform.translate(-self._camPosition.x, -self._camPosition.y)

        # Fill the screen with black
        painter = QPainter(self)
        painter.setBrush(QColor(0))
        painter.drawRect(0, 0, self.width(), self.height())

        # Draw the faces of the walkmesh (cached).
        painter.setTransform(transform)
        painter.setPen(QPen(QColor(10, 10, 10, 120),
                            1 / self._camScale,
                            QtCore.Qt.SolidLine) if not self.hideWalkmeshEdges else QPen(QtCore.Qt.NoPen))
        for face, path in self._walkmeshFaceCache.items():
            painter.setBrush(self.materialColor(face.material))
            painter.drawPath(path)

        if self.highlightBoundaries:
            for walkmesh in self._walkmeshes:
                for face in walkmesh.walkable_faces():
                    painter.setPen(QPen(QColor(255, 0, 0), 3/self._camScale))
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
                self._drawImage(painter, self._pixmapCreature, creature.position.x, creature.position.y, 1.57-self._camRotation, 1/16)

            for door in self._git.doors if not self.hideDoors else []:
                self._drawImage(painter, self._pixmapDoor, door.position.x, door.position.y, -self._camRotation, 1/16)

            for placeable in self._git.placeables if not self.hidePlaceables else []:
                self._drawImage(painter, self._pixmapPlaceable, placeable.position.x, placeable.position.y, -self._camRotation, 1/16)

            for merchant in self._git.stores if not self.hideStores else []:
                self._drawImage(painter, self._pixmapMerchant, merchant.position.x, merchant.position.y, -self._camRotation, 1/16)

            for waypoint in self._git.waypoints if not self.hideWaypoints else []:
                self._drawImage(painter, self._pixmapWaypoint, waypoint.position.x, waypoint.position.y, -self._camRotation, 1/16)

            for sound in self._git.sounds if not self.hideSounds else []:
                self._drawImage(painter, self._pixmapSound, sound.position.x, sound.position.y, -self._camRotation, 1/16)

            for encounter in self._git.encounters if not self.hideEncounters else []:
                self._drawImage(painter, self._pixmapEncounter, encounter.position.x, encounter.position.y, -self._camRotation, 1/16)

            for trigger in self._git.triggers if not self.hideTriggers else []:
                self._drawImage(painter, self._pixmapTrigger, trigger.position.x, trigger.position.y, -self._camRotation, 1/16)

            for camera in self._git.cameras if not self.hideCameras else []:
                self._drawImage(painter, self._pixmapCamera, camera.position.x, camera.position.y, -self._camRotation, 1/16)

        # Highlight the first instance that is underneath the mouse
        if self._instancesUnderMouse:
            instance = self._instancesUnderMouse[0]

            painter.setBrush(QColor(255, 255, 255, 35))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(QPointF(instance.position.x, instance.position.y), 1, 1)

            # If its a trigger or an encounter, this will draw the geometry stored inside it
            painter.setBrush(QColor(0, 220, 0, 50))
            painter.setPen(QPen(QColor(0, 255, 0, 75), 2 / self._camScale))
            painter.drawPath(self._buildInstanceBounds(instance))

        # Highlight first geom point that is underneath the mouse
        if self._geomPointsUnderMouse:
            gpoint = self._geomPointsUnderMouse[0]
            point = gpoint.instance.position + gpoint.point

            if not self.hideGeomPoints:
                painter.setBrush(QColor(255, 255, 255, 200))
                painter.setPen(QtCore.Qt.NoPen)
                painter.drawEllipse(QPointF(point.x, point.y), 4 / self._camScale, 4 / self._camScale)

        # Highlight selected instances
        for instance in self._instancesSelected:
            painter.setBrush(QColor(255, 255, 255, 70))
            painter.setPen(QPen(QColor(255, 255, 255, 255), 1 / self._camScale))
            painter.drawEllipse(QPointF(instance.position.x, instance.position.y), 1, 1)

            # If its a trigger or an encounter, this will draw the geometry stored inside it
            painter.setBrush(QColor(0, 220, 0, 100))
            painter.setPen(QPen(QColor(0, 255, 0, 150), 2 / self._camScale))
            painter.drawPath(self._buildInstanceBounds(instance))

            # If its a trigger or an encounter, this will draw the circles at the points making up the geometry
            if not self.hideGeomPoints:
                painter.setBrush(QColor(0, 255, 0, 255))
                painter.setPen(QtCore.Qt.NoPen)
                painter.drawPath(self._buildInstanceBoundsPoints(instance))

        # Highlight selected geometry points
        for geomPoint in self._geomPointsSelected:
            point = geomPoint.point + geomPoint.instance.position
            painter.setBrush(QColor(255, 255, 255, 255))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(QPointF(point.x, point.y), 4 / self._camScale, 4 / self._camScale)

    def wheelEvent(self, e: QWheelEvent) -> None:
        self.mouseScrolled.emit(Vector2(e.angleDelta().x(), e.angleDelta().y()), e.buttons(), self._keysDown)

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
                if isinstance(instance, GITEncounter) or isinstance(instance, GITTrigger) and instance in self._instancesSelected:
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

    def keyReleaseEvent(self, e: QKeyEvent) -> None:
        self._keysDown.discard(e.key())
    # endregion
