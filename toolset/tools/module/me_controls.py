from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import Set, List, Union, Callable

from PyQt5 import QtCore
from pykotor.common.geometry import Vector2, Vector3
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
        self.renderer: ModuleRenderer = renderer
        self.alterCameraPositionSensitivity: float = 0.033
        self._raiseStrength: float = 0.02

        self.alterCameraRotationSensitivity: float = 1 / 200
        self.alterObjectPositionSensitivity: float = 1 / 40
        self.alterObjectRotationSensitivity: float = 1

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

    def wz(self, x: float, y: float, z: float) -> float:
        point = self.renderer.walkmeshPoint(x, y, z)
        return z - point.z

    def translateSelectedObjects(self, snap: bool, dx: float, dy: float, dz: float) -> None:
        for obj in self.renderer.scene.selection:
            x = obj.data.position.x + dx
            y = obj.data.position.y + dy
            z = obj.data.position.z

            point = Vector3(obj.data.position.x + dx, obj.data.position.y + dy, obj.data.position.z)
            if snap:
                point = self.renderer.walkmeshPoint(x, y, z)
            point.z += dz

            instance = obj.data
            instance.position = point

    def rotateSelectedObjects(self, yaw: float, pitch: float) -> None:
        for obj in self.renderer.scene.selection:
            instance: GITInstance = obj.data
            instance.rotate(yaw / 80, 0, 0)

    def alterCameraPosition(self, dx: float, dy: float, dz: float) -> None:
        self.renderer.scene.camera.x += dx
        self.renderer.scene.camera.y += dy
        self.renderer.scene.camera.z += dz

    def snapCameraPosition(self, x: float = None, y: float = None, z: float = None) -> None:
        if x is not None:
            self.renderer.scene.camera.x = x
        if y is not None:
            self.renderer.scene.camera.y = y
        if z is not None:
            self.renderer.scene.camera.z = z

    def alterCameraRotation(self, yaw: float, pitch: float) -> None:
        self.renderer.scene.camera.yaw += yaw
        self.renderer.scene.camera.pitch += pitch

    def setCameraRotation(self, yaw: float, pitch: float) -> None:
        self.renderer.scene.camera.yaw = yaw
        self.renderer.scene.camera.pitch = pitch

    def selectObjectAtMouse(self) -> None:
        self.renderer.doSelect = True


class DynamicModuleEditorControls(ModuleEditorControls):

    def __init__(self, renderer: ModuleRenderer):
        super().__init__(renderer)

        self.mouseMoveEvents: List[DCItem] = []
        self.mousePressEvents: List[DCItem] = []
        self.mouseReleaseEvents: List[DCItem] = []
        self.mouseScrollEvents: List[DCItem] = []
        self.keyPressEvents: List[DCItem] = []
        self.keyReleaseEvents: List[DCItem] = []

    def onMouseMoved(self, screen: Vector2, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        for event in self.mouseMoveEvents:
            if event.mouse == buttons and event.keys == keys:
                for effect in event.effects:
                    effect.apply(self, delta.x, delta.y)

    def onMouseScrolled(self, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        for event in self.mouseScrollEvents:
            if event.mouse == buttons and event.keys == keys:
                for effect in event.effects:
                    effect.apply(self, delta.x, delta.y)

    def onMousePressed(self, screen: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        for event in self.mousePressEvents:
            if event.mouse == buttons and event.keys == keys:
                for effect in event.effects:
                    effect.apply(self, 0, 0)

    def onMouseReleased(self, screen: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        for event in self.mouseReleaseEvents:
            if event.mouse == buttons and event.keys == keys:
                for effect in event.effects:
                    effect.apply(self, 0, 0)

    def onKeyPressed(self, buttons: Set[int], keys: Set[int]) -> None:
        for event in self.keyPressEvents:
            if event.mouse == buttons and event.keys == keys:
                for effect in event.effects:
                    effect.apply(self, 0, 0)

    def onKeyReleased(self, buttons: Set[int], keys: Set[int]) -> None:
        for event in self.keyReleaseEvents:
            if event.mouse == buttons and event.keys == keys:
                for effect in event.effects:
                    effect.apply(self, 0, 0)


class AuroraModuleEditorControls(DynamicModuleEditorControls):

    def __init__(self, renderer: ModuleRenderer):
        super().__init__(renderer)

        self.mouseMoveEvents: List[DCItem] = [
            DCItem({KEY_CTRL}, {MB_L}, [DCEffectAlterCameraPosition(True, "cx", "cy", 0)]),
            DCItem({KEY_CTRL}, {MB_M}, [DCEffectAlterCameraRotation(True, "dx", "dy")]),
            DCItem(set(),      {MB_L}, [DCEffectAlterObjectPosition(True, True, "cx", "cy", 0)]),
            DCItem(set(),      {MB_M}, [DCEffectAlterObjectRotation(True, "dx")])
        ]
        self.mousePressEvents: List[DCItem] = [
            DCItem(set(), {MB_L}, [DCEffectSelectObjectAtMouse()])
        ]
        self.mouseReleaseEvents: List[DCItem] = []
        self.mouseScrollEvents: List[DCItem] = [
            DCItem({KEY_CTRL}, set(), [DCEffectAlterCameraPosition(True, 0, 0, "dy")])
        ]
        self.keyPressEvents: List[DCItem] = [
            DCItem({KEY_1}, set(), [DCEffectSetCameraRotation(0, "crp")]),
            DCItem({KEY_3}, set(), [DCEffectSetCameraRotation(0, "crp"), DCEffectSetCameraRotation(math.pi/2, 0)]),
            DCItem({KEY_7}, set(), [DCEffectSetCameraRotation("cry", 0)]),
            DCItem({KEY_9}, set(), [DCEffectSetCameraRotation("cry", math.pi/2)]),
            DCItem({KEY_4}, set(), [DCEffectAlterCameraRotation(False, math.pi/8, 0)]),
            DCItem({KEY_6}, set(), [DCEffectAlterCameraRotation(False, -math.pi/8, 0)]),
            DCItem({KEY_8}, set(), [DCEffectAlterCameraRotation(False, 0, math.pi/8)]),
            DCItem({KEY_2}, set(), [DCEffectAlterCameraRotation(False, 0, -math.pi/8)])
        ]
        self.keyReleaseEvents: List[DCItem] = []


class DCItem:
    def __init__(self, keys: Set[int], mouse: Set[int], effects: List[DCEffect]):
        self.keys: Set[int] = keys
        self.mouse: Set[int] = mouse
        self.effects: List[DCEffect] = effects


class DCEffect(ABC):
    @abstractmethod
    def apply(self, controls: ModuleEditorControls, dx: float, dy: float) -> None:
        ...

    @staticmethod
    def determineFloat(value: Union[float, str], controls: ModuleEditorControls, dx: float, dy: float) -> float:
        if isinstance(value, str):
            if value == "dx":
                return dx
            elif value == "dy":
                return dy
            elif value == "cx":
                forward = dy * controls.renderer.scene.camera.forward()
                sideward = dx * controls.renderer.scene.camera.sideward()
                return forward.x + sideward.x
            elif value == "cy":
                forward = dy * controls.renderer.scene.camera.forward()
                sideward = dx * controls.renderer.scene.camera.sideward()
                return forward.y + sideward.y
            elif value == "cz":
                ...
            elif value == "cry":
                return controls.renderer.scene.camera.yaw
            elif value == "crp":
                return controls.renderer.scene.camera.pitch
            else:
                return 0
        elif isinstance(value, float) or isinstance(value, int):
            return value
        else:
            return 0


class DCEffectAlterCameraPosition(DCEffect):
    def __init__(self, applySensitivity: bool, x: Union[float, str], y: Union[float, str], z: Union[float, str]):
        self.applySensitivity: bool = applySensitivity
        self.x: Union[float, str] = x
        self.y: Union[float, str] = y
        self.z: Union[float, str] = z

    def apply(self, controls: ModuleEditorControls, dx: float, dy: float) -> None:
        x = super().determineFloat(self.x, controls, dx, dy)
        y = super().determineFloat(self.y, controls, dx, dy)
        z = super().determineFloat(self.z, controls, dx, dy)
        sensitivity = controls.alterCameraPositionSensitivity if self.applySensitivity else 1.0
        controls.alterCameraPosition(x * sensitivity, y * sensitivity, z * sensitivity)


class DCEffectAlterCameraRotation(DCEffect):
    def __init__(self, applySensitivity: bool, yaw: Union[float, str], pitch: Union[float, str]):
        self.applySensitivity: bool = applySensitivity
        self.yaw: Union[float, str] = yaw
        self.pitch: Union[float, str] = pitch

    def apply(self, controls: ModuleEditorControls, dx: float, dy: float) -> None:
        pitch = super().determineFloat(self.pitch, controls, dx, dy)
        yaw = super().determineFloat(self.yaw, controls, dx, dy)
        sensitivity = controls.alterCameraRotationSensitivity if self.applySensitivity else 1.0
        controls.alterCameraRotation(yaw * sensitivity, pitch * sensitivity)


class DCEffectSetCameraRotation(DCEffect):
    def __init__(self, yaw: Union[float, str], pitch: Union[float, str]):
        self.yaw: Union[float, str] = yaw
        self.pitch: Union[float, str] = pitch

    def apply(self, controls: ModuleEditorControls, dx: float, dy: float) -> None:
        yaw = super().determineFloat(self.yaw, controls, dx, dy)
        pitch = super().determineFloat(self.pitch, controls, dx, dy)
        controls.setCameraRotation(yaw, pitch)


class DCEffectAlterObjectPosition(DCEffect):
    def __init__(self, applySensitivity: bool, snapToWalkmesh: bool, x: Union[float, str], y: Union[float, str], z: Union[float, str]):
        self.applySensitivity: bool = applySensitivity
        self.snapToWalkmesh: bool = snapToWalkmesh
        self.x: Union[float, str] = x
        self.y: Union[float, str] = y
        self.z: Union[float, str] = z

    def apply(self, controls: ModuleEditorControls, dx: float, dy: float) -> None:
        x = super().determineFloat(self.x, controls, dx, dy)
        y = super().determineFloat(self.y, controls, dx, dy)
        z = super().determineFloat(self.z, controls, dx, dy)
        sensitivity = controls.alterObjectPositionSensitivity if self.applySensitivity else 1.0
        controls.translateSelectedObjects(self.snapToWalkmesh, -x * sensitivity, -y * sensitivity, z * sensitivity)


class DCEffectAlterObjectRotation(DCEffect):
    def __init__(self, applySensitivity: bool, yaw: Union[float, str]):
        self.applySensitivity: bool = applySensitivity
        self.yaw: Union[float, str] = yaw

    def apply(self, controls: ModuleEditorControls, dx: float, dy: float) -> None:
        yaw = super().determineFloat(self.yaw, controls, dx, dy)
        sensitivity = controls.alterCameraRotationSensitivity if self.applySensitivity else 1.0
        controls.rotateSelectedObjects(yaw * sensitivity, 0.0)


class DCEffectSelectObjectAtMouse(DCEffect):
    def __init__(self):
        ...

    def apply(self, controls: ModuleEditorControls, dx: float, dy: float) -> None:
        controls.selectObjectAtMouse()
