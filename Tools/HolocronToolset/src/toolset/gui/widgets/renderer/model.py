from __future__ import annotations

import math

from typing import TYPE_CHECKING

from glm import vec3
from qtpy.QtCore import QPoint, QTimer
from qtpy.QtGui import QCursor
from qtpy.QtWidgets import QOpenGLWidget

from pykotor.common.geometry import Vector2
from pykotor.common.stream import BinaryReader
from pykotor.gl.models.read_mdl import gl_load_mdl
from pykotor.gl.scene import RenderObject, Scene
from pykotor.resource.generics.git import GIT, GITCreature
from toolset.data.misc import ControlItem
from toolset.gui.widgets.settings.module_designer import ModuleDesignerSettings
from utility.error_handling import assert_with_variable_trace
from utility.logger_util import RobustRootLogger

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
        self._modelToLoad: tuple[BinaryReader, BinaryReader] | None = None
        self._creatureToLoad: UTC | None = None

        self._keysDown: set[int] = set()
        self._mouseDown: set[int] = set()
        self._mousePrev: Vector2 = Vector2(0, 0)

    def loop(self):
        self.repaint()
        QTimer.singleShot(33, self.loop)

    @property
    def scene(self) -> Scene:
        if self._scene is None:
            raise ValueError("Scene must be constructed before this operation.")
        return self._scene

    def setInstallation(self, installation: Installation):
        self.installation = installation

    def initializeGL(self):
        self._scene = Scene(installation=self.installation)
        self.scene.camera.fov = ModuleDesignerSettings().fieldOfView
        self.scene.camera.distance = 0  # Set distance to 0

        self.scene.camera.yaw = math.pi / 2
        self.scene.camera.width = self.width()
        self.scene.camera.height = self.height()
        self.scene.show_cursor = False

        self.scene.git = GIT()

        QTimer.singleShot(33, self.loop)

    def paintGL(self):
        """Renders the scene.

        Args:
        ----
            self: The class instance

        Processing Logic:
        ----------------
            - Checks if scene is None and returns if so
            - Loads model if _modelToLoad is not None
            - Loads creature if _creatureToLoad is not None
            - Renders the scene.
        """
        if self.scene is None:
            return

        if self._modelToLoad is not None:
            self.scene.models["model"] = gl_load_mdl(self.scene, *self._modelToLoad)
            self.scene.objects["model"] = RenderObject("model")
            self.resetCamera()
            self._modelToLoad = None

        if self._creatureToLoad is not None:
            instance = GITCreature()
            utc = self._creatureToLoad

            self.scene.objects["model"] = self.scene.getCreatureRenderObject(instance, utc)
            self.resetCamera()
            self._creatureToLoad = None

        self.scene.render()

    def clearModel(self):
        if self._scene is not None and "model" in self.scene.objects:
            del self.scene.objects["model"]

    def setModel(self, data: bytes, data_ext: bytes):
        mdl = BinaryReader.from_auto(data, 12)
        mdx = BinaryReader.from_auto(data_ext)
        self._modelToLoad = mdl, mdx

    def setCreature(self, utc: UTC):
        self._creatureToLoad = utc

    def resetCamera(self):
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
    def focusOutEvent(self, e: QFocusEvent):
        self._mouseDown.clear()  # Clears the set when focus is lost
        self._keysDown.clear()  # Clears the set when focus is lost
        super().focusOutEvent(e)  # Ensures that the default handler is still executed
        RobustRootLogger().debug("ModelRenderer.focusOutEvent: clearing all keys/buttons held down.")

    def resizeEvent(self, e: QResizeEvent):
        super().resizeEvent(e)

        if self._scene is not None:
            self.scene.camera.width = e.size().width()
            self.scene.camera.height = e.size().height()

    def wheelEvent(self, e: QWheelEvent):
        if self.moveZCameraControl.satisfied(self._mouseDown, self._keysDown):
            strength: float = ModuleDesignerSettings().moveCameraSensitivity3d / 20000
            self.scene.camera.z -= -e.angleDelta().y() * strength
            return

        if self.zoomCameraControl.satisfied(self._mouseDown, self._keysDown):
            strength: float = ModuleDesignerSettings().zoomCameraSensitivity3d / 30000
            self.scene.camera.distance += -e.angleDelta().y() * strength

    def doCursorLock(self, mutableScreen: Vector2):
        """Reset the cursor to the center of the screen to prevent it from going off screen.

        Used with the FreeCam and drag camera movements and drag rotations.
        """
        global_old_pos = self.mapToGlobal(QPoint(int(self._mousePrev.x), int(self._mousePrev.y)))
        QCursor.setPos(global_old_pos)
        local_old_pos = self.mapFromGlobal(QPoint(global_old_pos.x(), global_old_pos.y()))
        mutableScreen.x = local_old_pos.x()
        mutableScreen.y = local_old_pos.y()

    def mouseMoveEvent(self, e: QMouseEvent):  # sourcery skip: extract-method
        screen = Vector2(e.x(), e.y())
        screenDelta = Vector2(screen.x - self._mousePrev.x, screen.y - self._mousePrev.y)

        if self.moveXYCameraControl.satisfied(self._mouseDown, self._keysDown):
            self.doCursorLock(screen)
            forward: vec3 = -screenDelta.y * self.scene.camera.forward()
            sideward: vec3 = screenDelta.x * self.scene.camera.sideward()
            strength = ModuleDesignerSettings().moveCameraSensitivity3d / 10000
            self.scene.camera.x -= (forward.x + sideward.x) * strength
            self.scene.camera.y -= (forward.y + sideward.y) * strength

        if self.rotateCameraControl.satisfied(self._mouseDown, self._keysDown):
            self.doCursorLock(screen)
            strength = ModuleDesignerSettings().moveCameraSensitivity3d / 10000
            self.scene.camera.rotate(-screenDelta.x * strength, screenDelta.y * strength, clamp=True)

        self._mousePrev = screen  # Always assign mousePrev after emitting, in order to do cursor lock properly.

    def mousePressEvent(self, e: QMouseEvent):
        button = e.button()
        self._mouseDown.add(button)
        #RobustRootLogger().debug(f"ModelRenderer.mousePressEvent: {self._mouseDown}, e.button() '{button}'")

    def mouseReleaseEvent(self, e: QMouseEvent):
        button = e.button()
        self._mouseDown.discard(button)
        #RobustRootLogger().debug(f"ModelRenderer.mouseReleaseEvent: {self._mouseDown}, e.button() '{button}'")

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

    def rotateObject(self, obj: RenderObject, pitch: float, yaw: float, roll: float):
        """Apply an incremental rotation to a RenderObject."""
        # I implore someone to explain why Z affects Yaw, and Y affects Roll...
        current_rotation = obj.rotation()
        new_rotation = vec3(
            current_rotation.x + pitch,
            current_rotation.y + roll,
            current_rotation.z + yaw
        )

        # Set the new rotation and recalculate the transformation
        obj.set_rotation(new_rotation.x, new_rotation.y, new_rotation.z)

    def keyPressEvent(self, e: QKeyEvent, bubble: bool = True):
        key: int = e.key()
        self._keysDown.add(key)

        rotateStrength = ModuleDesignerSettings().rotateCameraSensitivity3d / 1000
        if "model" in self.scene.objects:
            model = self.scene.objects["model"]
            if self.rotateCameraLeftControl.satisfied(self._mouseDown, self._keysDown):
                self.rotateObject(model, 0, math.pi / 4 * rotateStrength, 0)
            if self.rotateCameraRightControl.satisfied(self._mouseDown, self._keysDown):
                self.rotateObject(model, 0, -math.pi / 4 * rotateStrength, 0)
            if self.rotateCameraUpControl.satisfied(self._mouseDown, self._keysDown):
                self.rotateObject(model, math.pi / 4 * rotateStrength, 0, 0)
            if self.rotateCameraDownControl.satisfied(self._mouseDown, self._keysDown):
                self.rotateObject(model, -math.pi / 4 * rotateStrength, 0, 0)

        if self.moveCameraUpControl.satisfied(self._mouseDown, self._keysDown):
            self.scene.camera.z += (ModuleDesignerSettings().moveCameraSensitivity3d / 500)
        if self.moveCameraDownControl.satisfied(self._mouseDown, self._keysDown):
            self.scene.camera.z -= (ModuleDesignerSettings().moveCameraSensitivity3d / 500)
        if self.moveCameraLeftControl.satisfied(self._mouseDown, self._keysDown):
            self.panCamera(0, -(ModuleDesignerSettings().moveCameraSensitivity3d / 500), 0)
        if self.moveCameraRightControl.satisfied(self._mouseDown, self._keysDown):
            self.panCamera(0, (ModuleDesignerSettings().moveCameraSensitivity3d / 500), 0)
        if self.moveCameraForwardControl.satisfied(self._mouseDown, self._keysDown):
            self.panCamera((ModuleDesignerSettings().moveCameraSensitivity3d / 500), 0, 0)
        if self.moveCameraBackwardControl.satisfied(self._mouseDown, self._keysDown):
            self.panCamera(-(ModuleDesignerSettings().moveCameraSensitivity3d / 500), 0, 0)

        if self.zoomCameraInControl.satisfied(self._mouseDown, self._keysDown):
            self.scene.camera.distance += (ModuleDesignerSettings().zoomCameraSensitivity3d / 200)
        if self.zoomCameraOutControl.satisfied(self._mouseDown, self._keysDown):
            self.scene.camera.distance -= (ModuleDesignerSettings().zoomCameraSensitivity3d / 200)
        #key_name = getQtKeyStringLocalized(key)
        #RobustRootLogger().debug(f"ModelRenderer.keyPressEvent: {self._keysDown}, e.key() '{key_name}'")

    def keyReleaseEvent(self, e: QKeyEvent, bubble: bool = True):
        key: int = e.key()
        self._keysDown.discard(key)
        #key_name = getQtKeyStringLocalized(key)
        #RobustRootLogger().debug(f"ModelRenderer.keyReleaseEvent: {self._keysDown}, e.key() '{key_name}'")

    # endregion

    @property
    def moveXYCameraControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().moveCameraXY3dBind)

    @moveXYCameraControl.setter
    def moveXYCameraControl(self, value):
        pass

    @property
    def moveZCameraControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().moveCameraZ3dBind)

    @moveZCameraControl.setter
    def moveZCameraControl(self, value):
        pass

    @property
    def rotateCameraControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().rotateCamera3dBind)

    @rotateCameraControl.setter
    def rotateCameraControl(self, value):
        pass

    @property
    def zoomCameraControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().zoomCamera3dBind)
    @zoomCameraControl.setter
    def zoomCameraControl(self, value):
        pass

    @property
    def rotateCameraLeftControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().rotateCameraLeft3dBind)
    @rotateCameraLeftControl.setter
    def rotateCameraLeftControl(self, value):
        pass

    @property
    def rotateCameraRightControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().rotateCameraRight3dBind)
    @rotateCameraRightControl.setter
    def rotateCameraRightControl(self, value):
        pass

    @property
    def rotateCameraUpControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().rotateCameraUp3dBind)
    @rotateCameraUpControl.setter
    def rotateCameraUpControl(self, value):
        pass

    @property
    def rotateCameraDownControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().rotateCameraDown3dBind)
    @rotateCameraDownControl.setter
    def rotateCameraDownControl(self, value):
        pass

    @property
    def moveCameraUpControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().moveCameraUp3dBind)
    @moveCameraUpControl.setter
    def moveCameraUpControl(self, value):
        pass

    @property
    def moveCameraDownControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().moveCameraDown3dBind)
    @moveCameraDownControl.setter
    def moveCameraDownControl(self, value):
        pass

    @property
    def moveCameraForwardControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().moveCameraForward3dBind)
    @moveCameraForwardControl.setter
    def moveCameraForwardControl(self, value):
        pass

    @property
    def moveCameraBackwardControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().moveCameraBackward3dBind)
    @moveCameraBackwardControl.setter
    def moveCameraBackwardControl(self, value):
        pass

    @property
    def moveCameraLeftControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().moveCameraLeft3dBind)
    @moveCameraLeftControl.setter
    def moveCameraLeftControl(self, value):
        pass

    @property
    def moveCameraRightControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().moveCameraRight3dBind)
    @moveCameraRightControl.setter
    def moveCameraRightControl(self, value):
        pass

    @property
    def zoomCameraInControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().zoomCameraIn3dBind)
    @zoomCameraInControl.setter
    def zoomCameraInControl(self, value):
        pass

    @property
    def zoomCameraOutControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().zoomCameraOut3dBind)
    @zoomCameraOutControl.setter
    def zoomCameraOutControl(self, value):
        pass

    @property
    def toggleInstanceLockControl(self) -> ControlItem:
        return ControlItem(ModuleDesignerSettings().toggleLockInstancesBind)
    @toggleInstanceLockControl.setter
    def toggleInstanceLockControl(self, value):
        pass
