from __future__ import annotations

import math

from typing import TYPE_CHECKING

from qtpy.QtCore import QTimer
from qtpy.QtGui import QFocusEvent, QKeySequence
from qtpy.QtWidgets import QOpenGLWidget

from pykotor.common.geometry import Vector2
from pykotor.common.stream import BinaryReader
from pykotor.gl.models.read_mdl import gl_load_mdl
from pykotor.gl.scene import RenderObject, Scene
from pykotor.resource.generics.git import GIT, GITCreature
from toolset.data.misc import ControlItem
from toolset.gui.widgets.settings.module_designer import ModuleDesignerSettings
from toolset.utils.misc import QtKey
from utility.error_handling import assert_with_variable_trace
from utility.logger_util import RobustRootLogger

if TYPE_CHECKING:
    from glm import vec3
    from qtpy.QtGui import QKeyEvent, QMouseEvent, QResizeEvent, QWheelEvent
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

    @property
    def moveXYCamera(self):
        return ControlItem(ModuleDesignerSettings().moveCameraXY3dBind)

    @moveXYCamera.setter
    def moveXYCamera(self, value):
        pass

    @property
    def moveZCamera(self):
        return ControlItem(ModuleDesignerSettings().moveCameraZ3dBind)

    @moveZCamera.setter
    def moveZCamera(self, value):
        pass

    @property
    def rotateCamera(self):
        return ControlItem(ModuleDesignerSettings().rotateCamera3dBind)

    @rotateCamera.setter
    def rotateCamera(self, value):
        pass

    @property
    def zoomCamera(self):
        return ControlItem(ModuleDesignerSettings().zoomCamera3dBind)

    @zoomCamera.setter
    def zoomCamera(self, value):
        pass

    @property
    def rotateCameraLeft(self):
        return ControlItem(ModuleDesignerSettings().rotateCameraLeft3dBind)

    @rotateCameraLeft.setter
    def rotateCameraLeft(self, value):
        pass

    @property
    def rotateCameraRight(self):
        return ControlItem(ModuleDesignerSettings().rotateCameraRight3dBind)

    @rotateCameraRight.setter
    def rotateCameraRight(self, value):
        pass

    @property
    def rotateCameraUp(self):
        return ControlItem(ModuleDesignerSettings().rotateCameraUp3dBind)

    @rotateCameraUp.setter
    def rotateCameraUp(self, value):
        pass

    @property
    def rotateCameraDown(self):
        return ControlItem(ModuleDesignerSettings().rotateCameraDown3dBind)

    @rotateCameraDown.setter
    def rotateCameraDown(self, value):
        pass

    @property
    def moveCameraUp(self):
        return ControlItem(ModuleDesignerSettings().moveCameraUp3dBind)

    @moveCameraUp.setter
    def moveCameraUp(self, value):
        pass

    @property
    def moveCameraDown(self):
        return ControlItem(ModuleDesignerSettings().moveCameraDown3dBind)

    @moveCameraDown.setter
    def moveCameraDown(self, value):
        pass

    @property
    def moveCameraForward(self):
        return ControlItem(ModuleDesignerSettings().moveCameraForward3dBind)

    @moveCameraForward.setter
    def moveCameraForward(self, value):
        pass

    @property
    def moveCameraBackward(self):
        return ControlItem(ModuleDesignerSettings().moveCameraBackward3dBind)

    @moveCameraBackward.setter
    def moveCameraBackward(self, value):
        pass

    @property
    def moveCameraLeft(self):
        return ControlItem(ModuleDesignerSettings().moveCameraLeft3dBind)

    @moveCameraLeft.setter
    def moveCameraLeft(self, value):
        pass

    @property
    def moveCameraRight(self):
        return ControlItem(ModuleDesignerSettings().moveCameraRight3dBind)

    @moveCameraRight.setter
    def moveCameraRight(self, value):
        pass

    @property
    def zoomCameraIn(self):
        return ControlItem(ModuleDesignerSettings().zoomCameraIn3dBind)

    @zoomCameraIn.setter
    def zoomCameraIn(self, value):
        pass

    @property
    def zoomCameraOut(self):
        return ControlItem(ModuleDesignerSettings().zoomCameraOut3dBind)

    @zoomCameraOut.setter
    def zoomCameraOut(self, value):
        pass

    @property
    def toggleInstanceLock(self):
        return ControlItem(ModuleDesignerSettings().toggleLockInstancesBind)

    @toggleInstanceLock.setter
    def toggleInstanceLock(self, value):
        pass

    def loop(self):
        self.repaint()
        QTimer.singleShot(33, self.loop)

    @property
    def scene(self) -> Scene:
        if self._scene is None:
            raise ValueError("Scene must be constructed before this operation.")
        return self._scene

    def initializeGL(self):
        self._scene = Scene(installation=self.installation)
        self.scene.camera.fov = ModuleDesignerSettings().fieldOfView
        self.scene.camera.distance = 4
        self.scene.camera.z = 1.8
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
        if self.zoomCamera.satisfied(self._mouseDown, self._keysDown):
            strength: float = ModuleDesignerSettings().zoomCameraSensitivity3d / 20000
            self.scene.camera.distance += -e.angleDelta().y() * strength

        if self.moveZCamera.satisfied(self._mouseDown, self._keysDown):
            strength: float = ModuleDesignerSettings().moveCameraSensitivity3d / 20000
            self.scene.camera.z -= -e.angleDelta().y() * strength

    def mouseMoveEvent(self, e: QMouseEvent):
        screen = Vector2(e.x(), e.y())
        screenDelta = Vector2(screen.x - self._mousePrev.x, screen.y - self._mousePrev.y)
        self._mousePrev = screen

        if self.moveXYCamera.satisfied(self._mouseDown, self._keysDown):
            forward: vec3 = -screenDelta.y * self.scene.camera.forward()
            sideward: vec3 = screenDelta.x * self.scene.camera.sideward()
            strength = ModuleDesignerSettings().moveCameraSensitivity3d / 10000
            self.scene.camera.x -= (forward.x + sideward.x) * strength
            self.scene.camera.y -= (forward.y + sideward.y) * strength

        if self.rotateCamera.satisfied(self._mouseDown, self._keysDown):
            strength = ModuleDesignerSettings().moveCameraSensitivity3d / 10000
            self.scene.camera.rotate(-screenDelta.x * strength, screenDelta.y * strength, clamp=True)

    def mousePressEvent(self, e: QMouseEvent):
        button = e.button()
        self._mouseDown.add(button)
        #RobustRootLogger().debug(f"ModelRenderer.mousePressEvent: {self._mouseDown}, e.button() '{button}'")

    def mouseReleaseEvent(self, e: QMouseEvent):
        button = e.button()
        self._mouseDown.discard(button)
        #RobustRootLogger().debug(f"ModelRenderer.mouseReleaseEvent: {self._mouseDown}, e.button() '{button}'")

    def keyPressEvent(self, e: QKeyEvent, bubble: bool = True):
        key: int = e.key()
        self._keysDown.add(key)

        rotateStrength = ModuleDesignerSettings().rotateCameraSensitivity3d / 1000
        if self.rotateCameraLeft.satisfied(self._mouseDown, self._keysDown):  # TODO(th3w1zard1): ModuleDesignerSettings.rotateCameraSensitivity3d
            self.scene.camera.rotate(math.pi / 4 * rotateStrength, 0)
        if self.rotateCameraRight.satisfied(self._mouseDown, self._keysDown):
            self.scene.camera.rotate(-math.pi / 4 * rotateStrength, 0)
        if self.rotateCameraUp.satisfied(self._mouseDown, self._keysDown):
            self.scene.camera.rotate(0, math.pi / 4 * rotateStrength)
        if self.rotateCameraDown.satisfied(self._mouseDown, self._keysDown):
            self.scene.camera.rotate(0, -math.pi / 4 * rotateStrength)

        if self.moveCameraUp.satisfied(self._mouseDown, self._keysDown):
            self.scene.camera.z += (ModuleDesignerSettings().moveCameraSensitivity3d / 500)
        if self.moveCameraDown.satisfied(self._mouseDown, self._keysDown):
            self.scene.camera.z -= (ModuleDesignerSettings().moveCameraSensitivity3d / 500)
        if self.moveCameraLeft.satisfied(self._mouseDown, self._keysDown):
            self.scene.camera.x += (ModuleDesignerSettings().moveCameraSensitivity3d / 500)
        if self.moveCameraRight.satisfied(self._mouseDown, self._keysDown):
            self.scene.camera.x -= (ModuleDesignerSettings().moveCameraSensitivity3d / 500)
        if self.moveCameraForward.satisfied(self._mouseDown, self._keysDown):
            self.scene.camera.y -= (ModuleDesignerSettings().moveCameraSensitivity3d / 500)
        if self.moveCameraBackward.satisfied(self._mouseDown, self._keysDown):
            self.scene.camera.y += (ModuleDesignerSettings().moveCameraSensitivity3d / 500)

        if self.zoomCameraIn.satisfied(self._mouseDown, self._keysDown):
            self.scene.camera.distance += (ModuleDesignerSettings().zoomCameraSensitivity3d / 200)
        if self.zoomCameraOut.satisfied(self._mouseDown, self._keysDown):
            self.scene.camera.distance -= (ModuleDesignerSettings().zoomCameraSensitivity3d / 200)
        key_name = QKeySequence(key).toString()
        #RobustRootLogger().debug(f"ModelRenderer.keyPressEvent: {self._keysDown}, e.key() '{key_name}'")

    def keyReleaseEvent(self, e: QKeyEvent, bubble: bool = True):
        key: int = e.key()
        self._keysDown.discard(key)
        key_name = QKeySequence(key).toString()
        #RobustRootLogger().debug(f"ModelRenderer.keyReleaseEvent: {self._keysDown}, e.key() '{key_name}'")

    # endregion
