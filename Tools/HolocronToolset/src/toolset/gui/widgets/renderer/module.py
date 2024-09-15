from __future__ import annotations

from copy import copy, deepcopy
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from loggerplus import RobustLogger
from qtpy import QtCore
from qtpy.QtCore import QMetaObject, QThread, QTimer, Qt
from qtpy.QtGui import QPainter
from qtpy.QtWidgets import QApplication, QMessageBox, QOpenGLWidget

from pykotor.common.geometry import Vector2, Vector3
from pykotor.gl.scene import Scene
from pykotor.resource.formats.bwm.bwm_data import BWM
from pykotor.resource.generics.git import GITInstance
from pykotor.resource.type import ResourceType
from toolset.gui.widgets.renderer.lyt_editor import LYTEditor
from toolset.gui.widgets.renderer.texture_browser import TextureBrowser
from utility.error_handling import assert_with_variable_trace

if TYPE_CHECKING:
    from glm import vec3
    from qtpy.QtGui import QFocusEvent, QKeyEvent, QMouseEvent, QResizeEvent, QWheelEvent
    from qtpy.QtWidgets import QWidget

    from pykotor.common.module import Module
    from pykotor.resource.formats.bwm import BWMFace
    from pykotor.resource.formats.lyt.lyt_data import LYT, LYTDoorHook, LYTObstacle, LYTRoom, LYTRoomTemplate, LYTTrack
    from pykotor.resource.formats.tpc.tpc_data import TPC
    from toolset.data.installation import HTInstallation


class ModuleRenderer(QOpenGLWidget):
    rendererInitialized = QtCore.Signal()  # pyright: ignore[reportPrivateImportUsage]
    """Signal emitted when the context is being setup, the QMainWindow must be in an activated/unhidden state."""

    sceneInitialized = QtCore.Signal()  # pyright: ignore[reportPrivateImportUsage]
    """Signal emitted when scene has been initialized."""

    mouseMoved = QtCore.Signal(object, object, object, object, object)  # screen coords, screen delta, world/mouse pos, mouse, keys  # pyright: ignore[reportPrivateImportUsage]  # noqa: E501
    """Signal emitted when mouse is moved over the widget."""

    mouseScrolled = QtCore.Signal(object, object, object)  # screen delta, mouse, keys  # pyright: ignore[reportPrivateImportUsage]
    """Signal emitted when mouse is scrolled over the widget."""

    mouseReleased = QtCore.Signal(object, object, object)  # screen coords, mouse, keys  # pyright: ignore[reportPrivateImportUsage]
    """Signal emitted when a mouse button is released after being pressed on the widget."""

    mousePressed = QtCore.Signal(object, object, object)  # screen coords, mouse, keys  # pyright: ignore[reportPrivateImportUsage]
    """Signal emitted when a mouse button is pressed on the widget."""

    keyboardPressed = QtCore.Signal(object, object)  # mouse, keys  # pyright: ignore[reportPrivateImportUsage]

    keyboardReleased = QtCore.Signal(object, object)  # mouse, keys  # pyright: ignore[reportPrivateImportUsage]

    objectSelected = QtCore.Signal(object)  # pyright: ignore[reportPrivateImportUsage]
    """Signal emitted when an object has been selected through the renderer."""

    lytUpdated = QtCore.Signal(object)  # Signal to notify when LYT data is updated
    """Signal emitted when LYT data is updated."""
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

        from toolset.gui.windows.module_designer import ModuleDesignerSettings  # noqa: PLC0415  # pylint: disable=C0415

        self._scene: Scene | None = None
        self.settings: ModuleDesignerSettings = ModuleDesignerSettings()
        self._module: Module | None = None
        self._installation: HTInstallation | None = None
        self._lyt_editor: LYTEditor | None = None
        self._lyt: LYT | None = None

        self.loopTimer: QTimer = QTimer(self)
        self.loopTimer.timeout.connect(self.loop)
        self.loopInterval: int = 33  # ms, approx 30 FPS

        self._renderTime: int = 0
        self._keysDown: set[int] = set()
        self._mouseDown: set[int] = set()
        self._mousePrev: Vector2 = Vector2(self.cursor().pos().x(), self.cursor().pos().y())
        self._mousePressTime: datetime = datetime.now(tz=timezone.utc).astimezone()

        self.doSelect: bool = False  # Set to true to select object at mouse pointer
        self.freeCam: bool = False  # Changes how screenDelta is calculated in mouseMoveEvent
        self.delta: float = 0.0333

        self.lyt: LYT | None = None
        self.textureBrowser: TextureBrowser = TextureBrowser()
        self.lytEditor: LYTEditor = LYTEditor(self)
        self.initLYTEditor()

    def initLYTEditor(self):
        self.lytEditor.setVisible(False)
        self.lytEditor.roomPlaced.connect(self.onRoomPlaced)
        self.lytEditor.roomMoved.connect(self.onRoomMoved)
        self.lytEditor.roomResized.connect(self.onRoomResized)
        self.lytEditor.roomRotated.connect(self.onRoomRotated)
        self.lytEditor.doorHookPlaced.connect(self.onDoorHookPlaced)
        self.lytEditor.textureChanged.connect(self.onTextureChanged)

    def loadLYT(self, lyt: LYT):
        self.lyt = lyt
        self.lytEditor.setLYT(lyt)
        self.lytEditor.setVisible(True)

    def saveLYT(self):
        if self.lyt:
            self._module.setLYT(self.lyt)
            self._module.save()

    def onRoomPlaced(self, room: LYTRoom):
        self.lyt.addRoom(room)
        self.update()

    def onRoomMoved(self, room: LYTRoom, position: Vector2):
        room.setPosition(position)
        self.update()

    def onRoomResized(self, room: LYTRoom, size: Vector2):
        room.setSize(size)
        self.update()

    def onRoomRotated(self, room: LYTRoom, angle: float):
        room.setRotation(angle)
        self.update()

    def onDoorHookPlaced(self, doorHook: LYTDoorHook):
        self.lyt.addDoorHook(doorHook)
        self.update()

    def onTextureChanged(self, texture: TPC):
        self.lyt.setTexture(texture)
        self.update()

    @property
    def scene(self) -> Scene:
        if self._scene is None:
            instance = QApplication.instance()
            assert instance is not None
            if QThread.currentThread() == instance.thread():
                self.showSceneNotReadyMessage()
            else:
                QMetaObject.invokeMethod(self, "showSceneNotReadyMessage", Qt.QueuedConnection)
            raise ValueError("Scene is not initialized.")
        assert self._scene is not None
        return self._scene

    def showSceneNotReadyMessage(self):
        QMessageBox.warning(self, "Scene Not Ready", "The scene is not ready yet.")

    def isReady(self) -> bool:
        return bool(self._module and self._installation)

    def initializeRenderer(self, installation: HTInstallation, module: Module):
        RobustLogger().debug("Initialize ModuleRenderer")
        self.shutdownRenderer()
        self.show()
        QApplication.processEvents()  # Force the application to process all pending events
        self.rendererInitialized.emit()  # Tell QMainWindow to show itself, required for a gl context to be created.

        # Check if the widget and its top-level window are visible
        if not self.isVisible() or (self.window() and not self.window().isVisible()):
            RobustLogger().error("Widget or its window is not visible; OpenGL context may not be initialized.")
            raise RuntimeError("The OpenGL context is not available because the widget or its parent window is not visible.")

        # After ensuring visibility, finally check if a context is available.
        if not self.context():
            RobustLogger().error("initializeGL was not called or did not complete successfully.")
            raise RuntimeError("Failed to initialize OpenGL context. Ensure that the widget is visible and properly integrated into the application's window.")

        self._installation = installation
        self._module = module
        self._scene = Scene(installation=installation, module=module)
        self.scene.camera.fov = self.settings.fieldOfView
        self.scene.camera.width = self.width()
        self.scene.camera.height = self.height()
        self.sceneInitialized.emit()

        self._lyt_editor = LYTEditor(self)
        self._lyt_editor.lytUpdated.connect(self.updateLYT)
        self.resumeRenderLoop()

    def initializeGL(self):
        RobustLogger().debug("ModuleRenderer.initializeGL called.")
        super().initializeGL()
        RobustLogger().debug("ModuleRenderer.initializeGL - opengl context setup.")

    def resizeEvent(self, e: QResizeEvent):
        RobustLogger().debug("ModuleRenderer resizeEvent called.")
        super().resizeEvent(e)

    def resizeGL(self, width: int, height: int):
        RobustLogger().debug("ModuleRenderer resizeGL called.")
        super().resizeGL(width, height)
        if not self._scene:
            RobustLogger().debug("ignoring scene camera width/height updates in ModuleRenderer resizeGL - the scene is not initialized yet.")
            return
        self.scene.camera.width = width
        self.scene.camera.height = height

    def resumeRenderLoop(self):
        """Resumes the rendering loop by starting the timer."""
        RobustLogger().debug("ModuleRenderer - resumeRenderLoop called.")
        if not self.loopTimer.isActive():
            self.loopTimer.start(self.loopInterval)
        self.scene.camera.width = self.width()
        self.scene.camera.height = self.height()

    def pauseRenderLoop(self):
        """Pauses the rendering loop by stopping the timer."""
        RobustLogger().debug("ModuleRenderer - pauseRenderLoop called.")
        if self.loopTimer.isActive():
            self.loopTimer.stop()

    def shutdownRenderer(self):
        """Stops the rendering loop, unloads the module and installation, and attempts to destroy the OpenGL context."""
        RobustLogger().debug("ModuleRenderer - shutdownRenderer called.")
        self.pauseRenderLoop()
        self._module = None
        self._installation = None

        # Attempt to destroy the OpenGL context
        glContext = self.context()
        if glContext:
            glContext.doneCurrent()  # Ensure the context is not current
            self.update()  # Trigger an update which will indirectly handle context recreation when needed

        self.hide()
        self._scene = None

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
        if not self.loopTimer.isActive():
            RobustLogger().debug("ModuleDesigner.paintGL - loop timer is paused or not started.")
            return
        if not self.isReady():
            RobustLogger().warning("ModuleDesigner.paintGL - not initialized.")
            return  # Do nothing if not initialized
        #get_root_logger().debug("ModuleDesigner.paintGL called.")
        super().paintGL()
        start = datetime.now(tz=timezone.utc).astimezone()
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
        if self.lyt:
            self.lytEditor.render()
        self._renderTime = int((datetime.now(tz=timezone.utc).astimezone() - start).total_seconds() * 1000)

        if self.is_lyt_mode and self._lyt_editor:
            painter = QPainter(self)
            self._lyt_editor.render(painter)
            painter.end()

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

    def walkmeshPoint(
        self,
        x: float,
        y: float,
        default_z: float = 0.0,
    ) -> Vector3:
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
        assert self._module is not None
        for module_resource in self._module.resources.values():
            if module_resource.restype() is not ResourceType.WOK:
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

    def resetButtonsDown(self):
        self._mouseDown.clear()

    def resetKeysDown(self):
        self._keysDown.clear()

    def resetAllDown(self):
        self._mouseDown.clear()
        self._keysDown.clear()

    def setLYTMode(self, enabled: bool):
        self.is_lyt_mode = enabled
        if enabled and self._lyt_editor:
            self._lyt_editor.setLYT(self._lyt)
        self.update()

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
        sideways = right * self.scene.camera.sideward()

        self.scene.camera.x += forward_vec.x + sideways.x
        self.scene.camera.y += forward_vec.y + sideways.y
        self.scene.camera.z += up

    def moveCamera(self, forward: float, right: float, up: float):
        forward_vec: vec3 = forward * self.scene.camera.forward(ignore_z=False)
        sideways = right * self.scene.camera.sideward(ignore_z=False)
        upward = -up * self.scene.camera.upward(ignore_xy=False)

        self.scene.camera.x += upward.x + sideways.x + forward_vec.x
        self.scene.camera.y += upward.y + sideways.y + forward_vec.y
        self.scene.camera.z += upward.z + sideways.z + forward_vec.z

    def rotateCamera(self, yaw: float, pitch: float, *, clampRotations: bool = True):
        """Rotates the camera by the angles (radians) specified.

        Args:
        ----
            yaw:
            pitch:
            snapRotations:
        """
        self.scene.camera.rotate(yaw, pitch, clamp=clampRotations)

    def zoomCamera(self, distance: float):
        self.scene.camera.distance -= distance
        self.scene.camera.distance = max(self.scene.camera.distance, 0)

    # endregion

    # region Events

    def focusOutEvent(self, e: QFocusEvent):
        self._mouseDown.clear()  # Clears the set when focus is lost
        self._keysDown.clear()  # Clears the set when focus is lost
        super().focusOutEvent(e)  # Ensures that the default handler is still executed
        print("ModuleRenderer.focusOutEvent: clearing all keys/buttons held down.")

    def wheelEvent(self, e: QWheelEvent):
        super().wheelEvent(e)
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
        #super().mouseMoveEvent(e)
        screen = Vector2(e.x(), e.y())
        if self.freeCam:
            screenDelta = Vector2(screen.x - self.width() / 2, screen.y - self.height() / 2)
        else:
            screenDelta = Vector2(screen.x - self._mousePrev.x, screen.y - self._mousePrev.y)

        world = self.scene.cursor.position()
        if datetime.now(tz=timezone.utc).astimezone() - self._mousePressTime > timedelta(milliseconds=60):
            self.mouseMoved.emit(screen, screenDelta, world, self._mouseDown, self._keysDown)
        self._mousePrev = screen  # Always assign mousePrev after emitting: allows signal handlers (e.g. ModuleDesigner, GITEditor) to handle cursor lock.

    def mousePressEvent(self, e: QMouseEvent):
        super().mousePressEvent(e)
        self._mousePressTime = datetime.now(tz=timezone.utc).astimezone()
        button = e.button()
        self._mouseDown.add(button)
        coords = Vector2(e.x(), e.y())
        self.mousePressed.emit(coords, self._mouseDown, self._keysDown)
        if self.lytEditor.isVisible():
            self.lytEditor.handleMousePress(e)
        #RobustLogger().debug(f"ModuleRenderer.mousePressEvent: {self._mouseDown}, e.button() '{button}'")

    def mouseReleaseEvent(self, e: QMouseEvent):
        super().mouseReleaseEvent(e)
        button = e.button()
        self._mouseDown.discard(button)

        coords = Vector2(e.x(), e.y())
        self.mouseReleased.emit(coords, self._mouseDown, self._keysDown)
        if self.lytEditor.isVisible():
            self.lytEditor.handleMouseRelease(e)
        #RobustLogger().debug(f"ModuleRenderer.mouseReleaseEvent: {self._mouseDown}, e.button() '{button}'")

    def keyPressEvent(self, e: QKeyEvent, bubble: bool = True):
        super().keyPressEvent(e)
        key = e.key()
        self._keysDown.add(key)
        if self.underMouse() and not self.freeCam:
            self.keyboardPressed.emit(self._mouseDown, self._keysDown)
        if self.lytEditor.isVisible():
            self.lytEditor.handleKeyPress(e)
        #key_name = getQtKeyStringLocalized(key)
        #RobustLogger().debug(f"ModuleRenderer.keyPressEvent: {self._keysDown}, e.key() '{key_name}'")

    def keyReleaseEvent(self, e: QKeyEvent, bubble: bool = True):
        super().keyReleaseEvent(e)
        key = e.key()
        self._keysDown.discard(key)
        if self.underMouse() and not self.freeCam:
            self.keyboardReleased.emit(self._mouseDown, self._keysDown)
        if self.lytEditor.isVisible():
            self.lytEditor.handleKeyRelease(e)
        # key_name = getQtKeyStringLocalized(key)
        # RobustLogger().debug(f"ModuleRenderer.keyReleaseEvent: {self._keysDown}, e.key() '{key_name}'")

    # endregion

    def loadLYT(self, lyt: LYT):
        """Loads the LYT data into the renderer."""
        self._lyt = deepcopy(lyt)
        if self._lyt_editor:
            self._lyt_editor.setLYT(self._lyt)
        self.lytUpdated.emit(self._lyt)
        self.update()

    def getLYT(self) -> LYT | None:
        """Returns the current LYT data."""
        return self._lyt

    def updateLYT(self, lyt: LYT):
        """Updates the LYT data, notifies listeners, and triggers a redraw."""
        self._lyt = deepcopy(lyt)
        self.lytUpdated.emit(self._lyt)
        self.update()

    def addRoom(self, room: LYTRoom):
        """Adds a new room to the LYT data and triggers a redraw."""
        if self._lyt:
            self._lyt.rooms.append(room)
            self.lytUpdated.emit(self._lyt)
            self.update()

    def addTrack(self, track: LYTTrack):
        """Adds a new track to the LYT data and triggers a redraw."""
        if self._lyt:
            self._lyt.tracks.append(track)
            self.lytUpdated.emit(self._lyt)
            self.update()

    def addObstacle(self, obstacle: LYTObstacle):
        """Adds a new obstacle to the LYT data and triggers a redraw."""
        if self._lyt:
            self._lyt.obstacles.append(obstacle)
            self.lytUpdated.emit(self._lyt)
            self.update()

    def addDoorHook(self, doorhook: LYTDoorHook):
        """Adds a new doorhook to the LYT data and triggers a redraw."""
        if self._lyt:
            self._lyt.doorhooks.append(doorhook)
            self.lytUpdated.emit(self._lyt)
            self.update()

    def getLYTRoomTemplates(self) -> list[LYTRoomTemplate]:
        """Returns a list of available room templates."""
        # Implement logic to return room templates
        return []

    def getLYTTrackTemplates(self) -> list[LYTTrackTemplate]:
        """Returns a list of available track templates."""
        # Implement logic to return track templates
        return []

    def getLYTObstacleTemplates(self) -> list[LYTObstacleTemplate]:
        """Returns a list of available obstacle templates."""
        # Implement logic to return obstacle templates
        return []
