from __future__ import annotations

import math

from typing import TYPE_CHECKING

from qtpy.QtCore import QTimer
from qtpy.QtWidgets import QOpenGLWidget

from pykotor.common.geometry import Vector2
from pykotor.common.stream import BinaryReader
from pykotor.gl.models.read_mdl import gl_load_mdl
from pykotor.gl.scene import RenderObject, Scene
from pykotor.resource.generics.git import GIT, GITCreature
from toolset.data.misc import ControlItem
from toolset.gui.widgets.settings.module_designer import ModuleDesignerSettings
from utility.error_handling import assert_with_variable_trace

if TYPE_CHECKING:
    from glm import vec3
    from qtpy.QtGui import QKeyEvent, QMouseEvent, QResizeEvent, QWheelEvent
    from qtpy.QtWidgets import QWidget

    from pykotor.extract.installation import Installation
    from pykotor.resource.generics.utc import UTC


class ModelRenderer(QOpenGLWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.scene: Scene | None = None
        self.installation: Installation | None = None
        self._modelToLoad: tuple[BinaryReader, BinaryReader] | None = None
        self._creatureToLoad: UTC | None = None

        self._keysDown: set[int] = set()
        self._mouseDown: set[int] = set()
        self._mousePrev: Vector2 = Vector2(0, 0)

        self.settings: ModuleDesignerSettings = ModuleDesignerSettings()
        self.moveXYCamera: ControlItem = ControlItem(self.settings.moveCameraXY3dBind)
        self.moveZCamera: ControlItem = ControlItem(self.settings.moveCameraZ3dBind)
        self.rotateCamera: ControlItem = ControlItem(self.settings.rotateCamera3dBind)
        self.zoomCamera: ControlItem = ControlItem(self.settings.zoomCamera3dBind)
        self.rotateCameraLeft: ControlItem = ControlItem(self.settings.rotateCameraLeft3dBind)
        self.rotateCameraRight: ControlItem = ControlItem(self.settings.rotateCameraRight3dBind)
        self.rotateCameraUp: ControlItem = ControlItem(self.settings.rotateCameraUp3dBind)
        self.rotateCameraDown: ControlItem = ControlItem(self.settings.rotateCameraDown3dBind)
        self.moveCameraUp: ControlItem = ControlItem(self.settings.moveCameraUp3dBind)
        self.moveCameraDown: ControlItem = ControlItem(self.settings.moveCameraDown3dBind)
        self.moveCameraForward: ControlItem = ControlItem(self.settings.moveCameraForward3dBind)
        self.moveCameraBackward: ControlItem = ControlItem(self.settings.moveCameraBackward3dBind)
        self.moveCameraLeft: ControlItem = ControlItem(self.settings.moveCameraLeft3dBind)
        self.moveCameraRight: ControlItem = ControlItem(self.settings.moveCameraRight3dBind)
        self.zoomCameraIn: ControlItem = ControlItem(self.settings.zoomCameraIn3dBind)
        self.zoomCameraOut: ControlItem = ControlItem(self.settings.zoomCameraOut3dBind)
        self.toggleInstanceLock: ControlItem = ControlItem(self.settings.toggleLockInstancesBind)

    def loop(self):
        self.repaint()
        QTimer.singleShot(33, self.loop)

    def initializeGL(self):
        self.scene = Scene(installation=self.installation)
        self.scene.camera.fov = 70
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
        if self.scene is not None and "model" in self.scene.objects:
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
    def resizeEvent(self, e: QResizeEvent):
        super().resizeEvent(e)

        if self.scene is not None:
            self.scene.camera.width = e.size().width()
            self.scene.camera.height = e.size().height()

    def wheelEvent(self, e: QWheelEvent):
        if self.zoomCamera.satisfied(self._mouseDown, self._keysDown):
            strength: float = self.settings.zoomCameraSensitivity3d / 2000
            self.scene.camera.distance += -e.angleDelta().y() * strength

        if self.moveZCamera.satisfied(self._mouseDown, self._keysDown):
            strength: float = self.settings.moveCameraSensitivity3d / 10000
            self.scene.camera.z -= -e.angleDelta().y() * strength

    def mouseMoveEvent(self, e: QMouseEvent):
        screen = Vector2(e.x(), e.y())
        screenDelta = Vector2(screen.x - self._mousePrev.x, screen.y - self._mousePrev.y)
        self._mousePrev = screen

        if self.moveXYCamera.satisfied(self._mouseDown, self._keysDown):
            forward: vec3 = -screenDelta.y * self.scene.camera.forward()
            sideward: vec3 = screenDelta.x * self.scene.camera.sideward()
            strength = self.settings.moveCameraSensitivity3d / 10000
            self.scene.camera.x -= (forward.x + sideward.x) * strength
            self.scene.camera.y -= (forward.y + sideward.y) * strength

        if self.rotateCamera.satisfied(self._mouseDown, self._keysDown):
            strength = self.settings.moveCameraSensitivity3d / 10000
            self.scene.camera.rotate(-screenDelta.x * strength, screenDelta.y * strength)

    def mousePressEvent(self, e: QMouseEvent):
        self._mouseDown.add(e.button())

    def mouseReleaseEvent(self, e: QMouseEvent):
        self._mouseDown.discard(e.button())

    def keyPressEvent(self, e: QKeyEvent, bubble: bool = True):
        # FIXME: these values are wrong but there's an issue elsewhere i cbf fixing.

        self._keysDown.add(e.key())

        if self.rotateCameraLeft.satisfied(self._mouseDown, self._keysDown):
            self.scene.camera.rotate(math.pi / 4, 0)
        if self.rotateCameraRight.satisfied(self._mouseDown, self._keysDown):
            self.scene.camera.rotate(-math.pi / 4, 0)
        if self.rotateCameraUp.satisfied(self._mouseDown, self._keysDown):
            self.scene.camera.rotate(0, math.pi / 4)
        if self.rotateCameraDown.satisfied(self._mouseDown, self._keysDown):
            self.scene.camera.rotate(0, -math.pi / 4)

        if self.moveCameraUp.satisfied(self._mouseDown, self._keysDown):
            self.scene.camera.y += 1
        if self.moveCameraDown.satisfied(self._mouseDown, self._keysDown):
            self.scene.camera.y -= 1
        if self.moveCameraLeft.satisfied(self._mouseDown, self._keysDown):
            self.scene.camera.x += 1
        if self.moveCameraRight.satisfied(self._mouseDown, self._keysDown):
            self.scene.camera.x -= 1
        if self.moveCameraForward.satisfied(self._mouseDown, self._keysDown):
            self.scene.camera.z += 1
        if self.moveCameraBackward.satisfied(self._mouseDown, self._keysDown):
            self.scene.camera.z -= 1

        if self.zoomCameraIn.satisfied(self._mouseDown, self._keysDown):
            self.scene.camera.distance += 1
        if self.zoomCameraOut.satisfied(self._mouseDown, self._keysDown):
            self.scene.camera.distance -= 1

    def keyReleaseEvent(self, e: QKeyEvent, bubble: bool = True):
        self._keysDown.discard(e.key())

    # endregion
