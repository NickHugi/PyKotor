from __future__ import annotations

import json
import math
from abc import ABC, abstractmethod
from typing import Set, List, Union, Any, Optional

from jsmin import jsmin
from PyQt5 import QtCore
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QKeySequence
from pykotor.common.geometry import Vector2, Vector3
from pykotor.gl.scene import Camera
from pykotor.resource.generics.git import GITInstance

from gui.widgets.renderer.module import ModuleRenderer


def getMouseCode(string: str):
    MOUSE_MAP = {
        "LEFT": QtCore.Qt.LeftButton,
        "MIDDLE": QtCore.Qt.MiddleButton,
        "RIGHT": QtCore.Qt.RightButton
    }

    return MOUSE_MAP[string]


def getKeyCode(string: str):
    KEY_MAP = {
        "CTRL": QtCore.Qt.Key_Control,
        "ALT": QtCore.Qt.Key_Alt,
        "SHIFT": QtCore.Qt.Key_Shift
    }

    if string in KEY_MAP:
        return KEY_MAP[string]
    else:
        return QKeySequence(string)[0]


class ModuleEditorControls(ABC):
    def __init__(self, renderer: ModuleRenderer):
        self.renderer: ModuleRenderer = renderer
        self.cameraStyle: str = "UNFOCUSED"
        self.variables: List[DCVariable] = []

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

    def getValue(self, name: str) -> Any:
        for variable in self.variables:
            if variable.name() == name:
                return variable.get()

    def setValue(self, name: str, value: Any) -> Any:
        for variable in self.variables:
            if variable.name() == name:
                return variable.set(value)

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
        self.renderer.scene.camera.pitch = min(math.pi-0.000001, max(0.000001, self.renderer.scene.camera.pitch + pitch))

    def setCameraRotation(self, yaw: float, pitch: float) -> None:
        self.renderer.scene.camera.yaw = yaw
        self.renderer.scene.camera.pitch = pitch

    def selectObjectAtMouse(self) -> None:
        self.renderer.doSelect = True

    def openContextMenu(self) -> None:
        x, y = self.renderer.cursor().pos().x(), self.renderer.cursor().pos().y()
        self.renderer.customContextMenuRequested.emit(self.renderer.mapFromGlobal(QPoint(x, y)))

    def alterCameraZoom(self, amount: float):
        if isinstance(self.renderer.scene.camera, Camera):
            self.renderer.scene.camera.distance = max(0, self.renderer.scene.camera.distance + amount)


class DynamicModuleEditorControls(ModuleEditorControls):

    def __init__(self, renderer: ModuleRenderer, filepath: str = None):
        super().__init__(renderer)

        self.name: str = ""

        self.mouseMoveEvents: List[DCItem] = []
        self.mousePressEvents: List[DCItem] = []
        self.mouseReleaseEvents: List[DCItem] = []
        self.mouseScrollEvents: List[DCItem] = []
        self.keyPressEvents: List[DCItem] = []
        self.keyReleaseEvents: List[DCItem] = []
        # self.keyHoldEvents: List[DCItem] = []

        if filepath is not None:
            self.load(filepath)

    def load(self, filepath: str) -> None:
        self.variables: List[DCVariable] = []
        self.mouseMoveEvents = []
        self.mousePressEvents = []
        self.mouseReleaseEvents = []
        self.mouseScrollEvents = []
        self.keyPressEvents = []
        self.keyReleaseEvents = []

        f = open(filepath, "rb")
        rootJSON = json.loads(jsmin(f.read().decode()))

        self.name = rootJSON["name"]
        self.cameraStyle = rootJSON["style"]

        for name, variableJSON in rootJSON["variables"].items():
            data_type = variableJSON["type"]
            default = variableJSON["default"]

            var = None
            if data_type == "STRING":
                var = DCVariableString(name, default, variableJSON["allowed"])
            elif data_type == "INT":
                var = DCVariableInt(name, default)
            elif data_type == "FLOAT":
                var = DCVariableFloat(name, default)
            elif data_type == "BOOL":
                var = DCVariableBool(name, default)
            else:
                ValueError("Unknown data type '{}'.".format(data_type))

            self.variables.append(var)

        for controlJSON in rootJSON["controls"]:
            if controlJSON["event"] == "MOUSE_MOVE":
                array = self.mouseMoveEvents
            elif controlJSON["event"] == "MOUSE_PRESS":
                array = self.mousePressEvents
            elif controlJSON["event"] == "MOUSE_RELEASE":
                array = self.mouseReleaseEvents
            elif controlJSON["event"] == "MOUSE_SCROLL":
                array = self.mouseScrollEvents
            elif controlJSON["event"] == "KEY_PRESS":
                array = self.keyPressEvents
            elif controlJSON["event"] == "KEY_RELEASE":
                array = self.keyReleaseEvents
            else:
                raise ValueError("Unknown event '{}'.".format(controlJSON["event"]))

            if controlJSON["keys"] is None:
                keys = None
            else:
                keys = set()
                for keyJSON in controlJSON["keys"]:
                    key = keyJSON if isinstance(keyJSON, int) else getKeyCode(keyJSON)
                    keys.add(key)

            if controlJSON["mouse"] is None:
                mouse = None
            else:
                mouse = set()
                for mouseJSON in controlJSON["mouse"]:
                    key = mouseJSON if isinstance(mouseJSON, int) else getMouseCode(mouseJSON)
                    mouse.add(key)

            effects = []
            for effectsJSON in controlJSON["effects"]:
                for effectJSON in effectsJSON:
                    args = effectsJSON[effectJSON]

                    if effectJSON in DC_EFFECT_MAP.keys():
                        try:
                            effect = DC_EFFECT_MAP[effectJSON](*args)
                        except TypeError:
                            raise ValueError("Invalid number of arguments for '{}'.".format(effectJSON))
                    else:
                        raise ValueError("Unknown effect '{}'.".format(effectJSON))

                    effects.append(effect)

            array.append(DCItem(keys, mouse, effects))

    def onMouseMoved(self, screen: Vector2, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        ...

        for event in self.mouseMoveEvents:
            if (event.mouse == buttons or event.mouse is None) and (event.keys == keys or event.keys is None):
                for effect in event.effects:
                    effect.apply(self, delta.x, delta.y)

    def onMouseScrolled(self, delta: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        for event in self.mouseScrollEvents:
            if (event.mouse == buttons or event.mouse is None) and (event.keys == keys or event.keys is None):
                for effect in event.effects:
                    effect.apply(self, delta.x, delta.y)

    def onMousePressed(self, screen: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        for event in self.mousePressEvents:
            if (event.mouse == buttons or event.mouse is None) and (event.keys == keys or event.keys is None):
                for effect in event.effects:
                    effect.apply(self, 0, 0)

    def onMouseReleased(self, screen: Vector2, buttons: Set[int], keys: Set[int]) -> None:
        for event in self.mouseReleaseEvents:
            if (event.mouse == buttons or event.mouse is None) and (event.keys == keys or event.keys is None):
                for effect in event.effects:
                    effect.apply(self, 0, 0)

    def onKeyPressed(self, buttons: Set[int], keys: Set[int]) -> None:
        for event in self.keyPressEvents:
            if (event.mouse == buttons or event.mouse is None) and (event.keys == keys or event.keys is None):
                for effect in event.effects:
                    effect.apply(self, 0, 0)

    def onKeyReleased(self, buttons: Set[int], keys: Set[int]) -> None:
        for event in self.keyReleaseEvents:
            if (event.mouse == buttons or event.mouse is None) and (event.keys == keys or event.keys is None):
                for effect in event.effects:
                    effect.apply(self, 0, 0)


class HolocronModuleEditorControls(DynamicModuleEditorControls):

    def __init__(self, renderer: ModuleRenderer):
        super().__init__(renderer)

        self.variables: List[DCVariable] = [
            DCVariableFloat("panCamSensitivity", 0.033),
            DCVariableFloat("rotateCamSensitivity", 0.005),
            DCVariableFloat("raiseCamSensitivity", 0.025),
            DCVariableFloat("panObjSensitivity", 0.033),
            DCVariableFloat("rotateObjSensitivity", 0.005)
        ]

        self.mouseMoveEvents: List[DCItem] = [
            DCItem({getKeyCode("CTRL")}, {getMouseCode("LEFT")}, [DCEffectAlterCameraPosition("panCamSensitivity", "cx", "cy", 0)]),
            DCItem({getKeyCode("CTRL")}, {getMouseCode("MIDDLE")}, [DCEffectAlterCameraRotation("rotateCamSensitivity", "dx", "dy")]),
            DCItem(set(),      {getMouseCode("LEFT")}, [DCEffectAlterObjectPosition("panObjSensitivity", True, "cx", "cy", 0)]),
            DCItem(set(),      {getMouseCode("MIDDLE")}, [DCEffectAlterObjectRotation("rotateObjSensitivity", "dx")])
        ]
        self.mousePressEvents: List[DCItem] = [
            DCItem(set(), {getMouseCode("LEFT")}, [DCEffectSelectObjectAtMouse()]),
            DCItem(set(), {getMouseCode("RIGHT")}, [DCEffectOpenContextMenu()])
        ]
        self.mouseReleaseEvents: List[DCItem] = []
        self.mouseScrollEvents: List[DCItem] = [
            DCItem({getKeyCode("CTRL")}, set(), [DCEffectAlterCameraPosition("raiseCamSensitivity", 0, 0, "dy")])
        ]
        self.keyPressEvents: List[DCItem] = [
            DCItem({getKeyCode("1")}, set(), [DCEffectSetCameraRotation(0, "crp")]),
            DCItem({getKeyCode("3")}, set(), [DCEffectSetCameraRotation(0, "crp"), DCEffectAlterCameraRotation(None, math.pi/2, 0)]),
            DCItem({getKeyCode("7")}, set(), [DCEffectSetCameraRotation("cry", 0)]),
            DCItem({getKeyCode("4")}, set(), [DCEffectAlterCameraRotation(None, math.pi/8, 0)]),
            DCItem({getKeyCode("6")}, set(), [DCEffectAlterCameraRotation(None, -math.pi/8, 0)]),
            DCItem({getKeyCode("8")}, set(), [DCEffectAlterCameraRotation(None, 0, math.pi/8)]),
            DCItem({getKeyCode("2")}, set(), [DCEffectAlterCameraRotation(None, 0, -math.pi/8)]),
            DCItem({getKeyCode("W")}, set(), [DCEffectAlterCameraRotation(None, 0, math.pi/8)]),
            DCItem({getKeyCode("A")}, set(), [DCEffectAlterCameraRotation(None, math.pi/8, 0)]),
            DCItem({getKeyCode("S")}, set(), [DCEffectAlterCameraRotation(None, 0, -math.pi/8)]),
            DCItem({getKeyCode("D")}, set(), [DCEffectAlterCameraRotation(None, -math.pi/8, 0)]),
            DCItem({getKeyCode("Q")}, set(), [DCEffectAlterCameraPosition(None, 0, 0, 1)]),
            DCItem({getKeyCode("Z")}, set(), [DCEffectAlterCameraPosition(None, 0, 0, -1)])
        ]
        self.keyReleaseEvents: List[DCItem] = []


class DCItem:
    def __init__(self, keys: Set[int], mouse: Set[int], effects: List[DCEffect]):
        self.keys: Set[int] = keys
        self.mouse: Set[int] = mouse
        self.effects: List[DCEffect] = effects


class DCVariable:
    def __init__(self, name: str):
        self._name = name

    def name(self) -> str:
        return self._name

    def get(self) -> Any:
        raise NotImplementedError()

    def set(self, value: Any):
        raise NotImplementedError()


# region Variable Classes
class DCVariableInt(DCVariable):
    def __init__(self, name: str, value: int):
        super().__init__(name)
        self._value: int = value

    def set(self, value: int) -> None:
        self._value = value

    def get(self) -> int:
        return self._value


class DCVariableFloat(DCVariable):
    def __init__(self, name: str, value: float):
        super().__init__(name)
        self._value: float = value

    def name(self) -> str:
        return self._name

    def set(self, value: float) -> None:
        self._value = value

    def get(self) -> float:
        return self._value


class DCVariableBool(DCVariable):
    def __init__(self, name: str, value: bool):
        super().__init__(name)
        self._value: bool = value

    def name(self) -> str:
        return self._name

    def set(self, value: bool) -> None:
        self._value = value

    def get(self) -> bool:
        return self._value


class DCVariableString(DCVariable):
    def __init__(self, name: str, value: str, allowed: List[str]):
        super().__init__(name)
        self._value: str = value
        self._allowed: List[str] = allowed

    def name(self) -> str:
        return self._name

    def set(self, value: str) -> None:
        self._value = value

    def get(self) -> str:
        return self._value


class DCEffect(ABC):
    @abstractmethod
    def apply(self, controls: ModuleEditorControls, dx: float, dy: float) -> None:
        ...

    @staticmethod
    def determineFloat(value: Union[float, str], controls: ModuleEditorControls, dx: float, dy: float) -> float:
        if isinstance(value, str):
            output = 0.0
            modifier = 1.0
            if value.startswith("-"):
                modifier = -1.0
                value = value[1:]

            if value == "dx":
                output = dx
            elif value == "dy":
                output = dy

            elif value == "cpdxFlat":
                forward = -dy * controls.renderer.scene.camera.forward()
                sideward = dx * controls.renderer.scene.camera.sideward()
                output = -(forward.x + sideward.x)
            elif value == "cpdyFlat":
                forward = -dy * controls.renderer.scene.camera.forward()
                sideward = dx * controls.renderer.scene.camera.sideward()
                output = -(forward.y + sideward.y)

            elif value == "cpdx":
                sideward = dx * controls.renderer.scene.camera.sideward(False)
                upward = dy * controls.renderer.scene.camera.upward(False)
                output = -(upward.x + sideward.x)
            elif value == "cpdy":
                sideward = dx * controls.renderer.scene.camera.sideward(False)
                upward = dy * controls.renderer.scene.camera.upward(False)
                output = -(upward.y + sideward.y)
            elif value == "cpdz":
                sideward = dx * controls.renderer.scene.camera.sideward(False)
                upward = dy * controls.renderer.scene.camera.upward(False)
                output = -(upward.z + sideward.z)

            elif value == "cpxFlat":
                forward = controls.renderer.scene.camera.forward()
                output = forward.x
            elif value == "cpyFlat":
                forward = controls.renderer.scene.camera.forward()
                output = forward.y

            elif value == "cpx":
                forward = controls.renderer.scene.camera.sideward(False)
                output = forward.x
            elif value == "cpy":
                forward = controls.renderer.scene.camera.sideward(False)
                output = forward.y
            elif value == "cpz":
                forward = controls.renderer.scene.camera.sideward(False)
                output = forward.z

            elif value == "cry":
                output = controls.renderer.scene.camera.yaw
            elif value == "crp":
                output = controls.renderer.scene.camera.pitch

            return output * modifier
        elif isinstance(value, float) or isinstance(value, int):
            return value
        else:
            return 0
# endregion


# region Effect Classes
# alterCameraPosition
class DCEffectAlterCameraPosition(DCEffect):
    def __init__(self, sensitivityVar: Optional[str], x: Union[float, str], y: Union[float, str], z: Union[float, str]):
        self.sensitivityVar: Optional[str] = sensitivityVar
        self.x: Union[float, str] = x
        self.y: Union[float, str] = y
        self.z: Union[float, str] = z

    def apply(self, controls: ModuleEditorControls, dx: float, dy: float) -> None:
        x = super().determineFloat(self.x, controls, dx, dy)
        y = super().determineFloat(self.y, controls, dx, dy)
        z = super().determineFloat(self.z, controls, dx, dy)
        sensitivity = controls.getValue(self.sensitivityVar) if self.sensitivityVar is not None else 1.0
        controls.alterCameraPosition(x * sensitivity, y * sensitivity, z * sensitivity)


# setCameraPosition
class DCEffectSetCameraPosition(DCEffect):
    def __init__(self, x: Union[float, str], y: Union[float, str], z: Union[float, str]):
        self.x: Union[float, str] = x
        self.y: Union[float, str] = y
        self.z: Union[float, str] = z

    def apply(self, controls: ModuleEditorControls, dx: float, dy: float) -> None:
        x = super().determineFloat(self.x, controls, dx, dy)
        y = super().determineFloat(self.y, controls, dx, dy)
        z = super().determineFloat(self.z, controls, dx, dy)
        controls.alterCameraPosition(x, y, z)


# alterCameraRotation
class DCEffectAlterCameraRotation(DCEffect):
    def __init__(self, sensitivityVar: Optional[str], yaw: Union[float, str], pitch: Union[float, str]):
        self.sensitivityVar: Optional[str] = sensitivityVar
        self.yaw: Union[float, str] = yaw
        self.pitch: Union[float, str] = pitch

    def apply(self, controls: ModuleEditorControls, dx: float, dy: float) -> None:
        pitch = super().determineFloat(self.pitch, controls, dx, dy)
        yaw = super().determineFloat(self.yaw, controls, dx, dy)
        sensitivity = controls.getValue(self.sensitivityVar) if self.sensitivityVar is not None else 1.0
        controls.alterCameraRotation(yaw * sensitivity, pitch * sensitivity)


# setCameraRotation
class DCEffectSetCameraRotation(DCEffect):
    def __init__(self, yaw: Union[float, str], pitch: Union[float, str]):
        self.yaw: Union[float, str] = yaw
        self.pitch: Union[float, str] = pitch

    def apply(self, controls: ModuleEditorControls, dx: float, dy: float) -> None:
        yaw = super().determineFloat(self.yaw, controls, dx, dy)
        pitch = super().determineFloat(self.pitch, controls, dx, dy)
        controls.setCameraRotation(yaw, pitch)


# alterCameraZoom
class DCEffectAlterCameraZoom(DCEffect):
    def __init__(self, sensitivityVar: Optional[str], amount: Union[float, str]):
        self.sensitivityVar: Optional[str] = sensitivityVar
        self.amount: Union[float, str] = amount

    def apply(self, controls: ModuleEditorControls, dx: float, dy: float) -> None:
        amount = super().determineFloat(self.amount, controls, dx, dy)
        sensitivity = controls.getValue(self.sensitivityVar) if self.sensitivityVar is not None else 1.0
        controls.alterCameraZoom(amount * sensitivity)


# alterObjectPosition
class DCEffectAlterObjectPosition(DCEffect):
    def __init__(self, sensitivityVar: Optional[str], snapToWalkmesh: bool, x: Union[float, str], y: Union[float, str], z: Union[float, str]):
        self.sensitivityVar: Optional[str] = sensitivityVar
        self.snapToWalkmesh: bool = snapToWalkmesh
        self.x: Union[float, str] = x
        self.y: Union[float, str] = y
        self.z: Union[float, str] = z

    def apply(self, controls: ModuleEditorControls, dx: float, dy: float) -> None:
        x = super().determineFloat(self.x, controls, dx, dy)
        y = super().determineFloat(self.y, controls, dx, dy)
        z = super().determineFloat(self.z, controls, dx, dy)
        sensitivity = controls.getValue(self.sensitivityVar) if self.sensitivityVar is not None else 1.0
        controls.translateSelectedObjects(self.snapToWalkmesh, -x * sensitivity, -y * sensitivity, z * sensitivity)


# alterObjectRotation
class DCEffectAlterObjectRotation(DCEffect):
    def __init__(self, sensitivityVar: Optional[str], yaw: Union[float, str]):
        self.sensitivityVar: Optional[str] = sensitivityVar
        self.yaw: Union[float, str] = yaw

    def apply(self, controls: ModuleEditorControls, dx: float, dy: float) -> None:
        yaw = super().determineFloat(self.yaw, controls, dx, dy)
        sensitivity = controls.getValue(self.sensitivityVar) if self.sensitivityVar is not None else 1.0
        controls.rotateSelectedObjects(yaw * sensitivity, 0.0)


# selectObjectAtMouse
class DCEffectSelectObjectAtMouse(DCEffect):
    def __init__(self):
        ...

    def apply(self, controls: ModuleEditorControls, dx: float, dy: float) -> None:
        controls.selectObjectAtMouse()


# openContextMenu
class DCEffectOpenContextMenu(DCEffect):
    def __init__(self):
        ...

    def apply(self, controls: ModuleEditorControls, dx: float, dy: float) -> None:
        controls.openContextMenu()


# setVariable
class DCEffectSetVariable(DCEffect):
    def __init__(self, name: str, value: Any):
        self.name: str = name
        self.value: Any = value

    def apply(self, controls: ModuleEditorControls, dx: float, dy: float) -> None:
        controls.setValue(self.name, self.value)


# changeCameraFocus
class DCEffectChangeCameraFocus(DCEffect):
    def __init__(self, focus: Optional[bool]):
        self.focus: Optional[bool] = focus

    def apply(self, controls: ModuleEditorControls, dx: float, dy: float) -> None:
        ...


# snapCameraToObject
class DCEffectSnapCameraToObject(DCEffect):
    def __init__(self, distance: float):
        self.distance: float = distance

    def apply(self, controls: ModuleEditorControls, dx: float, dy: float) -> None:
        if controls.renderer.scene.selection:
            controls.renderer.snapCameraToPoint(controls.renderer.scene.selection[0].position(), self.distance)

# endregion


DC_EFFECT_MAP = {
    "alterCameraPosition": DCEffectAlterCameraPosition,
    "alterCameraRotation": DCEffectAlterCameraRotation,
    "alterCameraZoom": DCEffectAlterCameraZoom,
    "setCameraPosition": DCEffectSetCameraPosition,
    "setCameraRotation": DCEffectSetCameraRotation,
    "alterObjectPosition": DCEffectAlterObjectPosition,
    "alterObjectRotation": DCEffectAlterObjectRotation,
    "selectObjectAtMouse": DCEffectSelectObjectAtMouse,
    "openContextMenu": DCEffectOpenContextMenu,
    "setVariable": DCEffectSetVariable,
    "changeCameraFocus": DCEffectChangeCameraFocus,
    "snapCameraToObject": DCEffectSnapCameraToObject
}
