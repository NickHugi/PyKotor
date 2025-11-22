from __future__ import annotations

import math

from typing import TYPE_CHECKING

import qtpy

from loggerplus import RobustLogger
from qtpy.QtCore import QPoint, QTimer
from qtpy.QtGui import QCloseEvent, QCursor
from qtpy.QtWidgets import QOpenGLWidget  # pyright: ignore[reportPrivateImportUsage]

from pykotor.gl import vec3
from pykotor.gl.models.read_mdl import gl_load_mdl
from pykotor.gl.scene import RenderObject, Scene
from pykotor.resource.generics.git import GIT
from toolset.data.misc import ControlItem
from toolset.gui.widgets.settings.widgets.module_designer import ModuleDesignerSettings
from utility.common.geometry import Vector2
from utility.error_handling import assert_with_variable_trace

if TYPE_CHECKING:
    from qtpy.QtGui import QFocusEvent, QKeyEvent, QMouseEvent, QResizeEvent, QWheelEvent
    from qtpy.QtWidgets import QWidget

    from pykotor.extract.installation import Installation
    from pykotor.resource.generics.utc import UTC


class ModelRenderer(QOpenGLWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self._scene: Scene | None = None
        self.installation: Installation | None = None
        self._model_to_load: tuple[bytes, bytes] | None = None
        self._creature_to_load: UTC | None = None

        self._keys_down: set[int] = set()
        self._mouse_down: set[int] = set()
        self._mouse_prev: Vector2 = Vector2(0, 0)
        self._controls = ModelRendererControls()

        self._loop_timer: QTimer = QTimer(self)
        self._loop_timer.setInterval(33)
        self._loop_timer.setSingleShot(False)
        self._loop_timer.timeout.connect(self._render_loop)

    def _render_loop(self):
        if not self.isVisible() or self._scene is None:
            return
        self.update()

    @property
    def scene(self) -> Scene:
        if self._scene is None:
            raise ValueError("Scene must be constructed before this operation.")
        return self._scene

    def set_installation(self, installation: Installation):
        self.installation = installation

    def initializeGL(self):
        # Ensure OpenGL context is current
        self.makeCurrent()

        self._scene = Scene(installation=self.installation)
        self.scene.camera.fov = self._controls.fieldOfView
        self.scene.camera.distance = 0  # Set distance to 0

        self.scene.camera.yaw = math.pi / 2
        self.scene.camera.width = self.width()
        self.scene.camera.height = self.height()
        self.scene.show_cursor = False

        self.scene.git = GIT()

        self._loop_timer.start()

    def paintGL(self):
        if self._scene is None:
            return

        ctx = self.context()
        if ctx is None or not ctx.isValid():
            return

        if self._model_to_load is not None:
            self.scene.models["model"] = gl_load_mdl(self.scene, *self._model_to_load)
            self.scene.objects["model"] = RenderObject("model")
            self._model_to_load = None
            self.reset_camera()

        elif self._creature_to_load is not None:
            self.scene.objects["model"] = self.scene.get_creature_render_object(None, self._creature_to_load)
            self._creature_to_load = None
            self.reset_camera()

        self.scene.render()

    def closeEvent(self, event: QCloseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        self.shutdown_renderer()
        super().closeEvent(event)

    def shutdown_renderer(self):
        if self._loop_timer.isActive():
            self._loop_timer.stop()

        if self._scene is not None:
            scene = self._scene
            self._scene = None
            del scene

    def clear_model(self):
        if self._scene is not None and "model" in self.scene.objects:
            del self.scene.objects["model"]

    def set_model(
        self,
        data: bytes,
        data_ext: bytes,
    ):
        self._model_to_load = (data[12:], data_ext)

    def set_creature(self, utc: UTC):
        self._creature_to_load = utc

    def reset_camera(self):
        scene: Scene | None = self.scene
        assert scene is not None, assert_with_variable_trace(scene is not None)
        if "model" in scene.objects:
            model: RenderObject = scene.objects["model"]
            scene.camera.x = 0
            scene.camera.y = 0
            scene.camera.z = (model.cube(scene).max_point.z - model.cube(scene).min_point.z) / 2
            scene.camera.pitch = math.pi / 16 * 9
            scene.camera.yaw = math.pi / 16 * 7
            scene.camera.distance = model.radius(scene) + 2

    # region Events
    def focusOutEvent(self, e: QFocusEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        self._mouse_down.clear()  # Clears the set when focus is lost
        self._keys_down.clear()  # Clears the set when focus is lost
        super().focusOutEvent(e)  # Ensures that the default handler is still executed
        RobustLogger().debug("ModelRenderer.focusOutEvent: clearing all keys/buttons held down.")

    def resizeEvent(self, e: QResizeEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        super().resizeEvent(e)

        if self._scene is not None:
            self.scene.camera.width = e.size().width()
            self.scene.camera.height = e.size().height()

    def wheelEvent(self, e: QWheelEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        if self._controls.moveZCameraControl.satisfied(self._mouse_down, self._keys_down):
            strength: float = self._controls.moveCameraSensitivity3d / 20000
            self.scene.camera.z -= -e.angleDelta().y() * strength
            return

        if self._controls.zoomCameraControl.satisfied(self._mouse_down, self._keys_down):
            strength: float = self._controls.zoomCameraSensitivity3d / 30000
            self.scene.camera.distance += -e.angleDelta().y() * strength

    def do_cursor_lock(self, mut_scr: Vector2):
        """Reset the cursor to the center of the screen to prevent it from going off screen.

        Used with the FreeCam and drag camera movements and drag rotations.
        """
        global_old_pos = self.mapToGlobal(QPoint(int(self._mouse_prev.x), int(self._mouse_prev.y)))
        QCursor.setPos(global_old_pos)
        local_old_pos = self.mapFromGlobal(QPoint(global_old_pos.x(), global_old_pos.y()))
        mut_scr.x = local_old_pos.x()
        mut_scr.y = local_old_pos.y()

    def mouseMoveEvent(self, e: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        screen = Vector2(e.x(), e.y()) if qtpy.QT5 else Vector2(e.position().toPoint().x(), e.position().toPoint().y())
        screen_delta = Vector2(screen.x - self._mouse_prev.x, screen.y - self._mouse_prev.y)

        if self._controls.moveXYCameraControl.satisfied(self._mouse_down, self._keys_down):
            self.do_cursor_lock(screen)
            forward: vec3 = -screen_delta.y * self.scene.camera.forward()
            sideward: vec3 = screen_delta.x * self.scene.camera.sideward()
            strength = self._controls.moveCameraSensitivity3d / 10000
            self.scene.camera.x -= (forward.x + sideward.x) * strength
            self.scene.camera.y -= (forward.y + sideward.y) * strength

        if self._controls.rotateCameraControl.satisfied(self._mouse_down, self._keys_down):
            self.do_cursor_lock(screen)
            strength = self._controls.rotateCameraSensitivity3d / 10000
            self.scene.camera.rotate(-screen_delta.x * strength, screen_delta.y * strength, clamp=True)

        self._mouse_prev = screen  # Always assign mouse_prev after emitting, in order to do cursor lock properly.

    def mousePressEvent(self, e: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        button = e.button()
        self._mouse_down.add(button)
        # RobustLogger().debug(f"ModelRenderer.mousePressEvent: {self._mouse_down}, e.button() '{button}'")

    def mouseReleaseEvent(self, e: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        button = e.button()
        self._mouse_down.discard(button)
        # RobustLogger().debug(f"ModelRenderer.mouseReleaseEvent: {self._mouse_down}, e.button() '{button}'")

    def pan_camera(self, forward: float, right: float, up: float):
        """Moves the camera by the specified amount.

        The movement takes into account both the rotation and zoom of the
        camera on the x/y plane.

        Args:
        ----
            forward: Units to move forwards.
            right: Units to move to the right.
            up: Units to move upwards.
        """
        forward_vec = forward * self.scene.camera.forward()
        sideways = right * self.scene.camera.sideward()

        self.scene.camera.x += forward_vec.x + sideways.x
        self.scene.camera.y += forward_vec.y + sideways.y
        self.scene.camera.z += up

    def move_camera(
        self,
        forward: float,
        right: float,
        up: float,
    ):
        forward_vec = forward * self.scene.camera.forward(ignore_z=False)
        sideways = right * self.scene.camera.sideward(ignore_z=False)
        upward = -up * self.scene.camera.upward(ignore_xy=False)

        self.scene.camera.x += upward.x + sideways.x + forward_vec.x
        self.scene.camera.y += upward.y + sideways.y + forward_vec.y
        self.scene.camera.z += upward.z + sideways.z + forward_vec.z

    def rotate_object(self, obj: RenderObject, pitch: float, yaw: float, roll: float):
        """Apply an incremental rotation to a RenderObject."""
        # I implore someone to explain why Z affects Yaw, and Y affects Roll...
        current_rotation = obj.rotation()
        new_rotation = vec3(current_rotation.x + pitch, current_rotation.y + roll, current_rotation.z + yaw)
        obj.set_rotation(new_rotation.x, new_rotation.y, new_rotation.z)

    def keyPressEvent(self, e: QKeyEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        key: int = e.key()
        self._keys_down.add(key)

        rotate_strength = self._controls.rotateCameraSensitivity3d / 1000
        if "model" in self.scene.objects:
            model = self.scene.objects["model"]
            if self._controls.rotateCameraLeftControl.satisfied(self._mouse_down, self._keys_down):
                self.rotate_object(model, 0, math.pi / 4 * rotate_strength, 0)
            if self._controls.rotateCameraRightControl.satisfied(self._mouse_down, self._keys_down):
                self.rotate_object(model, 0, -math.pi / 4 * rotate_strength, 0)
            if self._controls.rotateCameraUpControl.satisfied(self._mouse_down, self._keys_down):
                self.rotate_object(model, math.pi / 4 * rotate_strength, 0, 0)
            if self._controls.rotateCameraDownControl.satisfied(self._mouse_down, self._keys_down):
                self.rotate_object(model, -math.pi / 4 * rotate_strength, 0, 0)

        if self._controls.moveCameraUpControl.satisfied(self._mouse_down, self._keys_down):
            self.scene.camera.z += self._controls.moveCameraSensitivity3d / 500
        if self._controls.moveCameraDownControl.satisfied(self._mouse_down, self._keys_down):
            self.scene.camera.z -= self._controls.moveCameraSensitivity3d / 500
        if self._controls.moveCameraLeftControl.satisfied(self._mouse_down, self._keys_down):
            self.pan_camera(0, -(self._controls.moveCameraSensitivity3d / 500), 0)
        if self._controls.moveCameraRightControl.satisfied(self._mouse_down, self._keys_down):
            self.pan_camera(0, (self._controls.moveCameraSensitivity3d / 500), 0)
        if self._controls.moveCameraForwardControl.satisfied(self._mouse_down, self._keys_down):
            self.pan_camera((self._controls.moveCameraSensitivity3d / 500), 0, 0)
        if self._controls.moveCameraBackwardControl.satisfied(self._mouse_down, self._keys_down):
            self.pan_camera(-(self._controls.moveCameraSensitivity3d / 500), 0, 0)

        if self._controls.zoomCameraControl.satisfied(self._mouse_down, self._keys_down):
            self.scene.camera.distance += self._controls.zoomCameraSensitivity3d / 200
        if self._controls.zoomCameraOutControl.satisfied(self._mouse_down, self._keys_down):
            self.scene.camera.distance -= self._controls.zoomCameraSensitivity3d / 200
        # key_name = get_qt_key_string_localized(key)
        # RobustLogger().debug(f"ModelRenderer.keyPressEvent: {self._keys_down}, e.key() '{key_name}'")

    def keyReleaseEvent(self, e: QKeyEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        key: int = e.key()
        self._keys_down.discard(key)
        # key_name = get_qt_key_string_localized(key)
        # RobustLogger().debug(f"ModelRenderer.keyReleaseEvent: {self._keys_down}, e.key() '{key_name}'")

    # endregion


class ModelRendererControls:
    @property
    def moveCameraSensitivity3d(self) -> float:
        return ModuleDesignerSettings().moveCameraSensitivity3d

    @moveCameraSensitivity3d.setter
    def moveCameraSensitivity3d(self, value: float): ...
    @property
    def zoomCameraSensitivity3d(self) -> float:
        return ModuleDesignerSettings().zoomCameraSensitivity3d

    @zoomCameraSensitivity3d.setter
    def zoomCameraSensitivity3d(self, value: float): ...
    @property
    def rotateCameraSensitivity3d(self) -> float:
        return ModuleDesignerSettings().rotateCameraSensitivity3d

    @rotateCameraSensitivity3d.setter
    def rotateCameraSensitivity3d(self, value: float): ...
    @property
    def fieldOfView(self) -> float:
        return ModuleDesignerSettings().fieldOfView

    @fieldOfView.setter
    def fieldOfView(self, value: float): ...

    @property
    def moveXYCameraControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().moveCameraXY3dBind)

    @moveXYCameraControl.setter
    def moveXYCameraControl(self, value): ...

    @property
    def moveZCameraControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().moveCameraZ3dBind)

    @moveZCameraControl.setter
    def moveZCameraControl(self, value): ...

    @property
    def rotate_cameraControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().rotateCamera3dBind)

    @rotate_cameraControl.setter
    def rotate_cameraControl(self, value): ...

    @property
    def zoomCameraControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().zoomCamera3dBind)

    @zoomCameraControl.setter
    def zoomCameraControl(self, value): ...

    @property
    def rotateCameraLeftControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().rotateCameraLeft3dBind)

    @rotateCameraLeftControl.setter
    def rotateCameraLeftControl(self, value): ...

    @property
    def rotateCameraRightControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().rotateCameraRight3dBind)

    @rotateCameraRightControl.setter
    def rotateCameraRightControl(self, value): ...

    @property
    def rotateCameraUpControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().rotateCameraUp3dBind)

    @rotateCameraUpControl.setter
    def rotateCameraUpControl(self, value): ...

    @property
    def rotateCameraDownControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().rotateCameraDown3dBind)

    @rotateCameraDownControl.setter
    def rotateCameraDownControl(self, value): ...

    @property
    def moveCameraUpControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().moveCameraUp3dBind)

    @moveCameraUpControl.setter
    def moveCameraUpControl(self, value): ...

    @property
    def moveCameraDownControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().moveCameraDown3dBind)

    @moveCameraDownControl.setter
    def moveCameraDownControl(self, value): ...

    @property
    def moveCameraForwardControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().moveCameraForward3dBind)

    @moveCameraForwardControl.setter
    def moveCameraForwardControl(self, value): ...

    @property
    def moveCameraBackwardControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().moveCameraBackward3dBind)

    @moveCameraBackwardControl.setter
    def moveCameraBackwardControl(self, value): ...

    @property
    def moveCameraLeftControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().moveCameraLeft3dBind)

    @moveCameraLeftControl.setter
    def moveCameraLeftControl(self, value): ...

    @property
    def moveCameraRightControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().moveCameraRight3dBind)

    @moveCameraRightControl.setter
    def moveCameraRightControl(self, value): ...

    @property
    def zoomCameraInControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().zoomCameraIn3dBind)

    @zoomCameraInControl.setter
    def zoomCameraInControl(self, value): ...

    @property
    def zoomCameraOutControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().zoomCameraOut3dBind)

    @zoomCameraOutControl.setter
    def zoomCameraOutControl(self, value): ...

    @property
    def toggleInstanceLockControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().toggleLockInstancesBind)

    @toggleInstanceLockControl.setter
    def toggleInstanceLockControl(self, value): ...


    @property
    def rotateCameraControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().rotateCamera3dBind)

    @rotateCameraControl.setter
    def rotateCameraControl(self, value): ...

