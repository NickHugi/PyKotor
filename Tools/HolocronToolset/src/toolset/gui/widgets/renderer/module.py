from __future__ import annotations

from copy import copy, deepcopy
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

import qtpy

from loggerplus import RobustLogger
from qtpy import QtCore
from qtpy.QtCore import QMetaObject, QThread, QTimer, Qt
from qtpy.QtWidgets import (
    QApplication,
    QMessageBox,
    QOpenGLWidget,  # pyright: ignore[reportPrivateImportUsage]
)

from pykotor.common.geometry import Vector2, Vector3
from pykotor.gl.scene import Scene
from pykotor.resource.formats.bwm.bwm_data import BWM
from pykotor.resource.formats.lyt.lyt_data import LYT
from pykotor.resource.generics.git import GITInstance
from pykotor.resource.type import ResourceType
from utility.error_handling import assert_with_variable_trace

if TYPE_CHECKING:
    from glm import vec3
    from qtpy.QtCore import QPoint
    from qtpy.QtGui import QFocusEvent, QKeyEvent, QMouseEvent, QOpenGLContext, QResizeEvent, QWheelEvent
    from qtpy.QtWidgets import QWidget

    from pykotor.common.module import Module
    from pykotor.gl.scene import RenderObject
    from pykotor.resource.formats.bwm import BWMFace
    from pykotor.resource.formats.lyt.lyt_data import LYT, LYTDoorHook, LYTObstacle, LYTRoom, LYTTrack
    from toolset.data.installation import HTInstallation


class ModuleRenderer(QOpenGLWidget):
    sig_renderer_initialized = QtCore.Signal()  # pyright: ignore[reportPrivateImportUsage]
    """Signal emitted when the context is being setup, the QMainWindow must be in an activated/unhidden state."""

    sig_scene_initialized = QtCore.Signal()  # pyright: ignore[reportPrivateImportUsage]
    """Signal emitted when scene has been initialized."""

    sig_mouse_moved = QtCore.Signal(object, object, object, object, object)  # screen coords, screen delta, world/mouse pos, mouse, keys  # pyright: ignore[reportPrivateImportUsage]  # noqa: E501
    """Signal emitted when mouse is moved over the widget."""

    sig_mouse_scrolled = QtCore.Signal(object, object, object)  # screen delta, mouse, keys  # pyright: ignore[reportPrivateImportUsage]
    """Signal emitted when mouse is scrolled over the widget."""

    sig_mouse_released = QtCore.Signal(object, object, object)  # screen coords, mouse, keys  # pyright: ignore[reportPrivateImportUsage]
    """Signal emitted when a mouse button is released after being pressed on the widget."""

    sig_mouse_pressed = QtCore.Signal(object, object, object)  # screen coords, mouse, keys  # pyright: ignore[reportPrivateImportUsage]
    """Signal emitted when a mouse button is pressed on the widget."""

    sig_keyboard_pressed = QtCore.Signal(object, object)  # mouse, keys  # pyright: ignore[reportPrivateImportUsage]

    sig_keyboard_released = QtCore.Signal(object, object)  # mouse, keys  # pyright: ignore[reportPrivateImportUsage]

    sig_object_selected = QtCore.Signal(object)  # pyright: ignore[reportPrivateImportUsage]
    """Signal emitted when an object has been selected through the renderer."""

    sig_lyt_updated = QtCore.Signal(object)  # pyright: ignore[reportPrivateImportUsage]
    """Signal emitted when the LYT data has been updated."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        from toolset.gui.windows.module_designer import (
            ModuleDesignerSettings,  # noqa: PLC0415  # pylint: disable=C0415
        )

        self._scene: Scene | None = None
        self.settings: ModuleDesignerSettings = ModuleDesignerSettings()
        self._module: Module | None = None
        self._installation: HTInstallation | None = None

        self.loop_timer: QTimer = QTimer(self)
        self.loop_timer.timeout.connect(self.loop)
        self.loop_interval: int = 33  # ms, approx 30 FPS

        self._render_time: int = 0
        self._keys_down: set[Qt.Key] = set()
        self._mouse_down: set[Qt.MouseButton] = set()
        self._mouse_prev: Vector2 = Vector2(self.cursor().pos().x(), self.cursor().pos().y())
        self._mouse_press_time: datetime = datetime.now(tz=timezone.utc).astimezone()

        self.do_select: bool = False  # Set to true to select object at mouse pointer
        self.free_cam: bool = False  # Changes how screenDelta is calculated in mouseMoveEvent
        self.delta: float = 0.0333

    @property
    def scene(self) -> Scene:
        if self._scene is None:
            instance: QtCore.QCoreApplication | None = QApplication.instance()
            assert instance is not None
            if QThread.currentThread() == instance.thread():
                self.show_scene_not_ready_message()
            else:
                QMetaObject.invokeMethod(self, "showSceneNotReadyMessage", Qt.ConnectionType.QueuedConnection)
            raise ValueError("Scene is not initialized.")
        assert self._scene is not None
        return self._scene

    def show_scene_not_ready_message(self):
        QMessageBox.warning(self, "Scene Not Ready", "The scene is not ready yet.")

    def isReady(self) -> bool:
        return bool(self._module and self._installation)

    def initialize_renderer(
        self,
        installation: HTInstallation,
        module: Module,
    ):
        RobustLogger().debug("Initialize ModuleRenderer")
        self.shutdown_renderer()
        self.show()
        QApplication.processEvents()  # Force the application to process all pending events
        self.sig_renderer_initialized.emit()  # Tell QMainWindow to show itself, required for a gl context to be created.

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
        self.sig_scene_initialized.emit()
        self.resume_render_loop()

    def initializeGL(self):
        RobustLogger().debug("ModuleRenderer.initializeGL called.")
        super().initializeGL()
        RobustLogger().debug("ModuleRenderer.initializeGL - opengl context setup.")

    def resizeEvent(self, e: QResizeEvent):
        RobustLogger().debug("ModuleRenderer resizeEvent called.")
        super().resizeEvent(e)

    def resizeGL(
        self,
        width: int,
        height: int,
    ):
        RobustLogger().debug("ModuleRenderer resizeGL called.")
        super().resizeGL(width, height)
        if not self._scene:
            RobustLogger().debug("ignoring scene camera width/height updates in ModuleRenderer resizeGL - the scene is not initialized yet.")
            return
        self.scene.camera.width = width
        self.scene.camera.height = height

    def resume_render_loop(self):
        """Resumes the rendering loop by starting the timer."""
        RobustLogger().debug("ModuleRenderer - resumeRenderLoop called.")
        if not self.loop_timer.isActive():
            self.loop_timer.start(self.loop_interval)
        self.scene.camera.width = self.width()
        self.scene.camera.height = self.height()

    def pause_render_loop(self):
        """Pauses the rendering loop by stopping the timer."""
        RobustLogger().debug("ModuleRenderer - pauseRenderLoop called.")
        if self.loop_timer.isActive():
            self.loop_timer.stop()

    def shutdown_renderer(self):
        """Stops the rendering loop, unloads the module and installation, and attempts to destroy the OpenGL context."""
        RobustLogger().debug("ModuleRenderer - shutdownRenderer called.")
        self.pause_render_loop()
        self._module = None
        self._installation = None

        # Attempt to destroy the OpenGL context
        gl_context: QOpenGLContext | None = self.context()
        if gl_context:
            gl_context.doneCurrent()  # Ensure the context is not current
            self.update()  # Trigger an update which will indirectly handle context recreation when needed

        self.hide()
        self._scene = None

    def paintGL(self):
        if not self.loop_timer.isActive():
            RobustLogger().debug("ModuleDesigner.paintGL - loop timer is paused or not started.")
            return
        if not self.isReady():
            RobustLogger().warning("ModuleDesigner.paintGL - not initialized.")
            return  # Do nothing if not initialized
        #get_root_logger().debug("ModuleDesigner.paintGL called.")
        super().paintGL()
        start: datetime = datetime.now(tz=timezone.utc).astimezone()
        if self.do_select:
            self.do_select = False
            obj: RenderObject | None = self.scene.pick(self._mouse_prev.x, self.height() - self._mouse_prev.y)

            if obj is not None and isinstance(obj.data, GITInstance):
                self.sig_object_selected.emit(obj.data)
            else:
                self.scene.selection.clear()
                self.sig_object_selected.emit(None)

        screen_cursor: QPoint = self.mapFromGlobal(self.cursor().pos())
        world_cursor: Vector3 = self.scene.screen_to_world(screen_cursor.x(), screen_cursor.y())
        if screen_cursor.x() < self.width() and screen_cursor.x() >= 0 and screen_cursor.y() < self.height() and screen_cursor.y() >= 0:
            self.scene.cursor.set_position(world_cursor.x, world_cursor.y, world_cursor.z)

        self.scene.render()
        self._render_time = int((datetime.now(tz=timezone.utc).astimezone() - start).total_seconds() * 1000)

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
        if self.underMouse() and self.free_cam and len(self._keys_down) > 0:
            self.sig_keyboard_pressed.emit(self._mouse_down, self._keys_down)

    def walkmesh_point(
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

    def reset_buttons_down(self):
        self._mouse_down.clear()

    def reset_keys_down(self):
        self._keys_down.clear()

    def reset_all_down(self):
        self._mouse_down.clear()
        self._keys_down.clear()

    # region Accessors
    def keys_down(self) -> set[Qt.Key]:
        return copy(self._keys_down)

    def mouse_down(self) -> set[Qt.MouseButton]:
        return copy(self._mouse_down)

    # endregion

    # region Camera Transformations
    def snap_camera_to_point(
        self,
        point: Vector3,
        distance: float = 6.0,
    ):
        camera = self.scene.camera
        camera.x, camera.y, camera.z = point.x, point.y, point.z + 1.0
        camera.distance = distance

    def pan_camera(
        self,
        forward: float,
        right: float,
        up: float,
    ):
        forward_vec: vec3 = forward * self.scene.camera.forward()
        sideways: vec3 = right * self.scene.camera.sideward()

        self.scene.camera.x += forward_vec.x + sideways.x
        self.scene.camera.y += forward_vec.y + sideways.y
        self.scene.camera.z += up

    def move_camera(
        self,
        forward: float,
        right: float,
        up: float,
    ):
        forward_vec: vec3 = forward * self.scene.camera.forward(ignore_z=False)
        sideways: vec3 = right * self.scene.camera.sideward(ignore_z=False)
        upward: vec3 = -up * self.scene.camera.upward(ignore_xy=False)

        self.scene.camera.x += upward.x + sideways.x + forward_vec.x
        self.scene.camera.y += upward.y + sideways.y + forward_vec.y
        self.scene.camera.z += upward.z + sideways.z + forward_vec.z

    def rotate_camera(
        self,
        yaw: float,
        pitch: float,
        *,
        clamp_rotations: bool = True,  # noqa: FBT001
    ):
        self.scene.camera.rotate(yaw, pitch, clamp=clamp_rotations)

    def zoom_camera(
        self,
        distance: float,
    ):
        self.scene.camera.distance -= distance
        self.scene.camera.distance = max(self.scene.camera.distance, 0)

    # endregion

    # region Events

    def focusOutEvent(self, e: QFocusEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        self._mouse_down.clear()  # Clears the set when focus is lost
        self._keys_down.clear()  # Clears the set when focus is lost
        super().focusOutEvent(e)  # Ensures that the default handler is still executed
        print("ModuleRenderer.focusOutEvent: clearing all keys/buttons held down.")

    def wheelEvent(self, e: QWheelEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        super().wheelEvent(e)
        if e is None:
            return
        self.sig_mouse_scrolled.emit(Vector2(e.angleDelta().x(), e.angleDelta().y()), self._mouse_down, self._keys_down)

    def mouseMoveEvent(self, e: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        #super().mouseMoveEvent(e)
        if e is None:
            return
        pos: QPoint = e.pos() if qtpy.QT5 else e.position().toPoint()
        screen: Vector2 = Vector2(pos.x(), pos.y())
        if self.free_cam:
            screenDelta = Vector2(screen.x - self.width() / 2, screen.y - self.height() / 2)
        else:
            screenDelta = Vector2(screen.x - self._mouse_prev.x, screen.y - self._mouse_prev.y)

        world = self.scene.cursor.position()
        if datetime.now(tz=timezone.utc).astimezone() - self._mouse_press_time > timedelta(milliseconds=60):
            self.sig_mouse_moved.emit(screen, screenDelta, world, self._mouse_down, self._keys_down)
        self._mouse_prev = screen  # Always assign mouse_prev after emitting: allows signal handlers (e.g. ModuleDesigner, GITEditor) to handle cursor lock.

    def mousePressEvent(self, e: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        super().mousePressEvent(e)
        self._mouse_press_time = datetime.now(tz=timezone.utc).astimezone()
        button: Qt.MouseButton = e.button()
        self._mouse_down.add(button)
        pos: QPoint = e.pos() if qtpy.QT5 else e.position().toPoint()
        coords: Vector2 = Vector2(pos.x(), pos.y())
        self.sig_mouse_pressed.emit(coords, self._mouse_down, self._keys_down)
        #RobustLogger().debug(f"ModuleRenderer.mousePressEvent: {self._mouse_down}, e.button() '{button}'")

    def mouseReleaseEvent(self, e: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        super().mouseReleaseEvent(e)
        button = e.button()
        self._mouse_down.discard(button)

        pos: QPoint = e.pos() if qtpy.QT5 else e.position().toPoint()
        coords: Vector2 = Vector2(pos.x(), pos.y())
        self.sig_mouse_released.emit(coords, self._mouse_down, self._keys_down)
        #RobustLogger().debug(f"ModuleRenderer.mouseReleaseEvent: {self._mouse_down}, e.button() '{button}'")

    def keyPressEvent(
        self,
        e: QKeyEvent | None,
        bubble: bool = True,  # noqa: FBT001, FBT002
    ):
        super().keyPressEvent(e)
        if e is None:
            return
        key = e.key()
        self._keys_down.add(key)  # pyright: ignore[reportArgumentType]
        if self.underMouse() and not self.free_cam:
            self.sig_keyboard_pressed.emit(self._mouse_down, self._keys_down)
        #key_name = get_qt_key_string_localized(key)
        #RobustLogger().debug(f"ModuleRenderer.keyPressEvent: {self._keys_down}, e.key() '{key_name}'")

    def keyReleaseEvent(
        self,
        e: QKeyEvent | None,
        bubble: bool = True,  # noqa: FBT002, FBT001
    ):
        super().keyReleaseEvent(e)
        if e is None:
            return
        key: Qt.Key | int = e.key()
        self._keys_down.discard(key)  # pyright: ignore[reportArgumentType]
        if self.underMouse() and not self.free_cam:
            self.sig_keyboard_released.emit(self._mouse_down, self._keys_down)
        # key_name = get_qt_key_string_localized(key)
        # RobustLogger().debug(f"ModuleRenderer.keyReleaseEvent: {self._keys_down}, e.key() '{key_name}'")

    # endregion


    def load_lyt(
        self,
        lyt: LYT,
    ):
        """Loads the LYT data into the renderer."""
        self._lyt: LYT = deepcopy(lyt)
        if self._lyt_editor is not None:
            self._lyt_editor._lyt = self._lyt
        self.sig_lyt_updated.emit(self._lyt)
        self.update()

    def get_lyt(self) -> LYT | None:
        """Returns the current LYT data."""
        return self._lyt

    def update_lyt(self, lyt: LYT):
        """Updates the LYT data, notifies listeners, and triggers a redraw."""
        self._lyt = deepcopy(lyt)
        self.sig_lyt_updated.emit(self._lyt)
        self.update()

    def add_room(
        self,
        room: LYTRoom,
    ):
        """Adds a new room to the LYT data and triggers a redraw."""
        if self._lyt is not None:
            self._lyt.rooms.append(room)
            self.sig_lyt_updated.emit(self._lyt)
            self.update()

    def add_track(
        self,
        track: LYTTrack,
    ):
        """Adds a new track to the LYT data and triggers a redraw."""
        if self._lyt is not None:
            self._lyt.tracks.append(track)
            self.sig_lyt_updated.emit(self._lyt)
            self.update()

    def add_obstacle(
        self,
        obstacle: LYTObstacle,
    ):
        """Adds a new obstacle to the LYT data and triggers a redraw."""
        if self._lyt is not None:
            self._lyt.obstacles.append(obstacle)
            self.sig_lyt_updated.emit(self._lyt)
            self.update()

    def add_door_hook(
        self,
        doorhook: LYTDoorHook,
    ):
        """Adds a new doorhook to the LYT data and triggers a redraw."""
        if self._lyt is not None:
            self._lyt.doorhooks.append(doorhook)
            self.sig_lyt_updated.emit(self._lyt)
            self.update()
