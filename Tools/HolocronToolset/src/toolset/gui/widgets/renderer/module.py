from __future__ import annotations

import math

from copy import copy
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from PyQt5 import QtCore
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QOpenGLWidget

from pykotor.common.geometry import Vector2, Vector3
from pykotor.gl.scene import Scene
from pykotor.resource.formats.bwm.bwm_data import BWM
from pykotor.resource.generics.git import GITInstance
from pykotor.resource.type import ResourceType
from utility.error_handling import assert_with_variable_trace

if TYPE_CHECKING:
    from PyQt5.QtGui import QKeyEvent, QMouseEvent, QResizeEvent, QWheelEvent
    from PyQt5.QtWidgets import QWidget
    from glm import vec3

    from pykotor.common.module import Module
    from pykotor.resource.formats.bwm import BWMFace
    from toolset.data.installation import HTInstallation


class ModuleRenderer(QOpenGLWidget):  # noqa: PLR0904
    sceneInitalized = QtCore.pyqtSignal()
    """Signal emitted when scene has been initialized."""

    mouseMoved = QtCore.pyqtSignal(object, object, object, object, object)  # screen coords, screen delta, world/mouse pos, mouse, keys
    """Signal emitted when mouse is moved over the widget."""

    mouseScrolled = QtCore.pyqtSignal(object, object, object)  # screen delta, mouse, keys
    """Signal emitted when mouse is scrolled over the widget."""

    mouseReleased = QtCore.pyqtSignal(object, object, object)  # screen coords, mouse, keys
    """Signal emitted when a mouse button is released after being pressed on the widget."""

    mousePressed = QtCore.pyqtSignal(object, object, object)  # screen coords, mouse, keys
    """Signal emitted when a mouse button is pressed on the widget."""

    keyboardPressed = QtCore.pyqtSignal(object, object)  # mouse, keys

    keyboardReleased = QtCore.pyqtSignal(object, object)  # mouse, keys

    objectSelected = QtCore.pyqtSignal(object)
    """Signal emitted when an object has been selected through the renderer."""

    def __init__(self, parent: QWidget):
        """Initializes the ModuleDesigner widget.

        Args:
        ----
            parent: QWidget: The parent widget.

        Processing Logic:
        ----------------
            - Calls super().__init__() to initialize the base QWidget class
            - Initializes scene, settings and other member variables
            - Sets initial values for mouse, key states and camera properties
        """
        super().__init__(parent)

        from toolset.gui.windows.module_designer import ModuleDesignerSettings

        self.scene: Scene | None = None
        self.settings: ModuleDesignerSettings = ModuleDesignerSettings()
        self._module: Module | None = None
        self._installation: HTInstallation | None = None
        self._init = False

        self._renderTime: int = 0
        self._keysDown: set[int] = set()
        self._mouseDown: set[int] = set()
        self._mousePrev: Vector2 = Vector2(self.cursor().pos().x(), self.cursor().pos().y())
        self._mousePressTime: datetime = datetime.now(tz=timezone.utc).astimezone()

        self.doSelect: bool = False  # Set to true to select object at mouse pointer
        self.freeCam: bool = False  # Changes how screenDelta is calculated in mouseMoveEvent
        self.delta: float = 0.0333

    def init(self, installation: HTInstallation, module: Module):
        self._installation = installation
        self._module = module

        QTimer.singleShot(33, self.loop)

    def loop(self):
        """Repaints and checks for keyboard input on mouse press.

        Args:
        ----
            self: The object instance

        Processing Logic:
        ----------------
            - Calls repaint() to redraw the canvas
            - Checks if mouse is over object and keyboard keys are pressed
            - Emits keyboardPressed signal with mouse/key info
            - Schedules next loop call after delay to maintain ~30fps
        """
        self.repaint()
        if self.underMouse() and self.freeCam and len(self._keysDown) > 0:
            self.keyboardPressed.emit(self._mouseDown, self._keysDown)

        delay = max(0, 33 - self._renderTime)
        QTimer.singleShot(delay, self.loop)

    def walkmeshPoint(self, x: float, y: float, default_z: float = 0.0) -> Vector3:
        """Finds the face and z-height at a point on the walkmesh.

        Args:
        ----
            x: float - The x coordinate of the point
            y: float - The y coordinate of the point
            default_z: float = 0.0 - The default z height if no face is found

        Returns:
        -------
            Vector3 - The (x, y, z) position on the walkmesh

        Processing Logic:
        ----------------
            - Iterates through walkmesh resources to find the face at the given (x,y) coordinates
            - Checks if the found face is walkable, and overrides any previous less walkable face
            - Returns a Vector3 with the input x,y coords and either the face z height or default z if no face.
        """
        face: BWMFace | None = None
        for module_resource in self._module.resources.values():
            if module_resource.restype() != ResourceType.WOK:
                continue
            walkmesh_resource = module_resource.resource()
            if walkmesh_resource is None:
                continue
            assert isinstance(walkmesh_resource, BWM), assert_with_variable_trace(isinstance(walkmesh_resource, BWM))
            over: BWMFace | None = walkmesh_resource.faceAt(x, y)
            if over is None:
                continue
            if face is None:  # noqa: SIM114
                face = over
            elif not face.material.walkable() and over.material.walkable():
                face = over

        z: float = default_z if face is None else face.determine_z(x, y)
        return Vector3(x, y, z)

    def initializeGL(self):
        self.scene = Scene()

    def resetMouseButtons(self):
        self._mouseDown.clear()

    def paintGL(self):
        """Renders the scene and handles object selection.

        Args:
        ----
            self: The viewport widget

        Processing Logic:
        ----------------
            - Initializes painting if not already initialized
            - Handles object selection on mouse click
            - Sets cursor position based on mouse
            - Renders the scene
            - Records render time.
        """
        start = datetime.now(tz=timezone.utc).astimezone()
        if not self._init:
            self._initialize_paintGL()
        if self.doSelect:
            self.doSelect = False
            obj = self.scene.pick(self._mousePrev.x, self.height() - self._mousePrev.y)

            if obj is not None and isinstance(obj.data, GITInstance):
                self.objectSelected.emit(obj.data)
            else:
                self.scene.selection.clear()
                self.objectSelected.emit(None)

        screenCursor = self.mapFromGlobal(self.cursor().pos())
        worldCursor = self.scene.screenToWorld(screenCursor.x(), screenCursor.y())
        if screenCursor.x() < self.width() and screenCursor.x() >= 0 and screenCursor.y() < self.height() and screenCursor.y() >= 0:
            self.scene.cursor.set_position(worldCursor.x, worldCursor.y, worldCursor.z)

        self.scene.render()
        self._renderTime = int((datetime.now(tz=timezone.utc).astimezone() - start).total_seconds() * 1000)

    def _initialize_paintGL(self):
        self._init = True

        self.scene = Scene(installation=self._installation, module=self._module)
        self.scene.camera.fov = self.settings.fieldOfView
        self.scene.camera.width = self.width()
        self.scene.camera.height = self.height()

        self.sceneInitalized.emit()

    # region Accessors
    def keysDown(self) -> set[int]:
        return copy(self._keysDown)

    def mouseDown(self) -> set[int]:
        return copy(self._mouseDown)
    # endregion

    # region Camera Transformations
    def snapCameraToPoint(self, point: Vector3, distance: float = 6.0):
        camera = self.scene.camera
        camera.x, camera.y, camera.z = point.x, point.y, point.z + 1.0
        camera.distance = distance

    def panCamera(self, forward: float, right: float, up: float):
        """Moves the camera by the specified amount.

        The movement takes into account both the rotation and zoom of the
        camera on the x/y plane.

        Args:
        ----
            forward: Units to move forwards.
            right: Units to move to the right.
            up: Units to move upwards.
        """
        forward_vec: vec3 = forward * self.scene.camera.forward()
        sideward = right * self.scene.camera.sideward()

        self.scene.camera.x += (forward_vec.x + sideward.x)
        self.scene.camera.y += (forward_vec.y + sideward.y)
        self.scene.camera.z += up

    def moveCamera(self, forward: float, right: float, up: float):
        forward_vec: vec3 = forward * self.scene.camera.forward(False)
        sideward = right * self.scene.camera.sideward(False)
        upward = -up * self.scene.camera.upward(False)

        self.scene.camera.x += upward.x + sideward.x + forward_vec.x
        self.scene.camera.y += upward.y + sideward.y + forward_vec.y
        self.scene.camera.z += upward.z + sideward.z + forward_vec.z

    def rotateCamera(self, yaw: float, pitch: float, snapRotations: bool = True):
        """Rotates the camera by the angles (radians) specified.

        Args:
        ----
            yaw:
            pitch:
            snapRotations:
        """
        self.scene.camera.rotate(yaw, pitch)
        if self.scene.camera.pitch < math.pi / 2 and snapRotations:
            self.scene.camera.pitch = math.pi / 2
        if self.scene.camera.pitch > math.pi and snapRotations:
            self.scene.camera.pitch = math.pi

    def zoomCamera(self, distance: float):
        self.scene.camera.distance -= distance
        self.scene.camera.distance = max(self.scene.camera.distance, 0)
    # endregion

    # region Events
    def resizeEvent(self, e: QResizeEvent):
        super().resizeEvent(e)

        self.scene.camera.width = e.size().width()
        self.scene.camera.height = e.size().height()

    def wheelEvent(self, e: QWheelEvent):
        self.mouseScrolled.emit(Vector2(e.angleDelta().x(), e.angleDelta().y()), self._mouseDown, self._keysDown)

    def mouseMoveEvent(self, e: QMouseEvent):
        """Handles mouse move events.

        Args:
        ----
            e: QMouseEvent: Current mouse event.

        Processing Logic:
        ----------------
            1. Get current mouse position on screen
            2. Calculate delta from previous position or center of screen if free camera mode
            3. Get world position of cursor
            4. Emit signal with mouse data if time since press > threshold
        """
        screen = Vector2(e.x(), e.y())
        if self.freeCam:
            screenDelta = Vector2(screen.x - self.width() / 2, screen.y - self.height() / 2)
        else:
            screenDelta = Vector2(screen.x - self._mousePrev.x, screen.y - self._mousePrev.y)
        if self.scene is None:
            return

        world = self.scene.cursor.position()
        self._mousePrev = screen
        if datetime.now(tz=timezone.utc).astimezone() - self._mousePressTime > timedelta(milliseconds=60):
            self.mouseMoved.emit(screen, screenDelta, world, self._mouseDown, self._keysDown)

    def mousePressEvent(self, e: QMouseEvent):
        self._mousePressTime = datetime.now(tz=timezone.utc).astimezone()
        self._mouseDown.add(e.button())
        coords = Vector2(e.x(), e.y())
        self.mousePressed.emit(coords, self._mouseDown, self._keysDown)

    def mouseReleaseEvent(self, e: QMouseEvent):
        self._mouseDown.discard(e.button())

        coords = Vector2(e.x(), e.y())
        self.mouseReleased.emit(coords, e.buttons(), self._keysDown)

    def keyPressEvent(self, e: QKeyEvent, bubble: bool = True):
        self._keysDown.add(e.key())
        if self.underMouse() and not self.freeCam:
            self.keyboardPressed.emit(self._mouseDown, self._keysDown)

    def keyReleaseEvent(self, e: QKeyEvent, bubble: bool = True):
        self._keysDown.discard(e.key())
        if self.underMouse() and not self.freeCam:
            self.keyboardReleased.emit(self._mouseDown, self._keysDown)
    # endregion
