import math
from abc import ABC, abstractmethod
from typing import Set

from PyQt5 import QtCore
from pykotor.common.geometry import Vector2
from pykotor.gl.scene import Scene
from pykotor.resource.generics.git import GITInstance

from tools.module.me_widgets import ModuleRenderer

MB_L = QtCore.Qt.LeftButton
MB_M = QtCore.Qt.MiddleButton
MB_R = QtCore.Qt.RightButton

KEY_CTRL = QtCore.Qt.Key_Control
KEY_Z = QtCore.Qt.Key_Z
KEY_Q = QtCore.Qt.Key_Q
KEY_W = QtCore.Qt.Key_W
KEY_A = QtCore.Qt.Key_A
KEY_S = QtCore.Qt.Key_S
KEY_D = QtCore.Qt.Key_D
KEY_0 = QtCore.Qt.Key_0
KEY_1 = QtCore.Qt.Key_1
KEY_2 = QtCore.Qt.Key_2
KEY_3 = QtCore.Qt.Key_3
KEY_4 = QtCore.Qt.Key_4
KEY_5 = QtCore.Qt.Key_5
KEY_6 = QtCore.Qt.Key_6
KEY_7 = QtCore.Qt.Key_7
KEY_8 = QtCore.Qt.Key_8
KEY_9 = QtCore.Qt.Key_9


class ModuleEditorControls(ABC):
    def __init__(self, renderer: ModuleRenderer):
        self._renderer: ModuleRenderer = renderer
        self._panStrength: float = 0.033
        self._raiseStrength: float = 0.02
        self._rotateStrength: float = 1 / 200

        self._zoomStrength: float = 0.0
        self._objectTranslateStrength: float = 1/40

    @abstractmethod
    def onMouseMoved(self, screen: Vector2, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        ...

    @abstractmethod
    def onMouseScrolled(self, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        ...

    @abstractmethod
    def onMousePressed(self, screen: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        ...

    @abstractmethod
    def onMouseReleased(self, screen: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        ...

    @abstractmethod
    def onKeyPressed(self, buttons: Set[int], keys: Set[int]) -> None:
        ...

    @abstractmethod
    def onKeyReleased(self, buttons: Set[int], keys: Set[int]) -> None:
        ...

    def translateSelectedObjects(self, dx: float, dy: float) -> None:
        for obj in self._renderer.scene.selection:
            forward = self._renderer.scene.camera.forward() * -dy
            sideward = self._renderer.scene.camera.sideward() * -dx

            x = obj.data.position.x + (forward.x + sideward.x) / 40
            y = obj.data.position.y + (forward.y + sideward.y) / 40

            instance: GITInstance = obj.data
            instance.position = self._renderer.walkmeshPoint(x, y, obj.data.position.z)
            
    def rotateSelectedObjects(self, dx: float, dy: float) -> None:
        for obj in self._renderer.scene.selection:
            instance: GITInstance = obj.data
            instance.rotate(dx / 80, 0, 0)

    def alterCameraPosition(self, dx: float, dy: float, dz: float) -> None:
        self._renderer.panCamera(dx, dy, dz)

    def snapCameraPosition(self, *, x: float = None, y: float = None, z: float = None) -> None:
        if x is not None:
            self._renderer.scene.camera.x = x
        if y is not None:
            self._renderer.scene.camera.y = y
        if z is not None:
            self._renderer.scene.camera.z = z

    def alterCameraRotation(self, pitch: float, yaw: float) -> None:
        self._renderer.rotateCamera(yaw, pitch)

    def snapCameraRotation(self, *, pitch: float = None, yaw: float = None) -> None:
        if pitch is not None:
            self._renderer.scene.camera.pitch = pitch
        if yaw is not None:
            self._renderer.scene.camera.yaw = yaw


class ModuleEditorControlsAurora(ModuleEditorControls):
    
    def onMouseMoved(self, screen: Vector2, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        if MB_L in buttons and KEY_CTRL in keys:
            self.alterCameraPosition(delta.x * self._panStrength, delta.y * self._panStrength, 0.0)
        elif MB_M in buttons and KEY_CTRL in keys:
            self.alterCameraRotation(delta.y * self._rotateStrength, delta.x * self._rotateStrength,)
        elif MB_L in buttons and KEY_CTRL not in keys:
            self.translateSelectedObjects(delta.x, delta.y)
        elif MB_M in buttons and KEY_CTRL in keys:
            self.rotateSelectedObjects(delta.x, delta.y)

    def onMouseScrolled(self, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        if MB_M in buttons and KEY_CTRL in keys:
            self.alterCameraPosition(0.0, 0.0, delta.y * self._raiseStrength)

    def onMousePressed(self, screen: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        if MB_L in buttons and KEY_CTRL not in keys:
            self._renderer.doSelect = True

    def onMouseReleased(self, screen: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        ...

    def onKeyPressed(self, buttons: Set[int], keys: Set[int]) -> None:
        if {KEY_9} & keys:
            self.snapCameraRotation(yaw=0)

        if {KEY_7} & keys:
            self.snapCameraRotation(pitch=0)

        if {KEY_4, KEY_A} & keys:
            self.alterCameraRotation(0, math.pi / 8)

        if {KEY_6, KEY_D} & keys:
            self.alterCameraRotation(0, -math.pi / 8)

        if {KEY_8, KEY_W} & keys:
            self.alterCameraRotation(math.pi / 8, 0)

        if {KEY_2, KEY_S} & keys:
            self.alterCameraRotation(-math.pi / 8, 0)

        if {KEY_Q} & keys:
            self.alterCameraPosition(0, 0, 1)

        if {KEY_Z} & keys:
            self.alterCameraPosition(0, 0, -1)

    def onKeyReleased(self, buttons: Set[int], keys: Set[int]) -> None:
        ...

