from __future__ import annotations

import json
import math

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, NoReturn

from jsmin import jsmin
from qtpy import QtCore
from qtpy.QtCore import QPoint
from qtpy.QtGui import QKeySequence

from pykotor.gl.scene import Camera
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from utility.common.geometry import Vector3
from utility.system.path import Path

if TYPE_CHECKING:
    from glm import vec3
    from qtpy.QtCore import QKeyCombination, Qt

    from pykotor.resource.generics.git import GITInstance
    from toolset.gui.widgets.renderer.module import ModuleRenderer
    from utility.common.geometry import Vector2


def get_mouse_code(string: str) -> QtCore.Qt.MouseButton:
    MOUSE_MAP: dict[str, Qt.MouseButton] = {
        "LEFT": QtCore.Qt.MouseButton.LeftButton,
        "MIDDLE": QtCore.Qt.MouseButton.MiddleButton,
        "RIGHT": QtCore.Qt.MouseButton.RightButton,
    }

    return MOUSE_MAP[string]


def get_key_code(
    string: str,
) -> QtCore.Qt.Key | QKeySequence | QKeyCombination:
    KEY_MAP: dict[str, Qt.Key] = {
        "CTRL": QtCore.Qt.Key.Key_Control,
        "ALT": QtCore.Qt.Key.Key_Alt,
        "SHIFT": QtCore.Qt.Key.Key_Shift,
    }

    return KEY_MAP[string] if string in KEY_MAP else QKeySequence(string)[0]


class ModuleEditorControls(ABC):
    def __init__(
        self,
        renderer: ModuleRenderer,
    ):
        self.renderer: ModuleRenderer = renderer
        self.camera_style: str = "UNFOCUSED"
        self.variables: list[DCVariable] = []

    @abstractmethod
    def on_mouse_moved(
        self,
        screen: Vector2,
        delta: Vector2,
        buttons: set[int],
        keys: set[int],
    ): ...

    @abstractmethod
    def on_mouse_scrolled(
        self,
        delta: Vector2,
        buttons: set[int],
        keys: set[int],
    ): ...

    @abstractmethod
    def on_mouse_pressed(
        self,
        screen: Vector2,
        buttons: set[int],
        keys: set[int],
    ): ...

    @abstractmethod
    def on_mouse_released(
        self,
        screen: Vector2,
        buttons: set[int],
        keys: set[int],
    ): ...

    @abstractmethod
    def on_key_pressed(
        self,
        buttons: set[int],
        keys: set[int],
    ): ...

    @abstractmethod
    def on_key_released(
        self,
        buttons: set[int],
        keys: set[int],
    ): ...

    def getValue(
        self,
        name: str,
    ) -> Any:
        return next(
            (variable.get() for variable in self.variables if variable.name() == name),
            None,
        )

    def setValue(
        self,
        name: str,
        value: Any,
    ) -> Any:
        return next(
            (variable.set(value) for variable in self.variables if variable.name() == name),
            None,
        )

    def wz(
        self,
        x: float,
        y: float,
        z: float,
    ) -> float:
        point: Vector3 = self.renderer.walkmesh_point(x, y, z)
        return z - point.z

    def translate_selected_objects(
        self,
        snap: bool,  # noqa: FBT001
        dx: float,
        dy: float,
        dz: float,
    ):
        """Translates selected objects.

        Args:
        ----
            snap: Snap objects to walkmesh
            dx: Translation amount on X axis
            dy: Translation amount on Y axis
            dz: Translation amount on Z axis

        Returns:
        -------
            None: Function does not return anything

        Translates selected objects by specified amounts on each axis.
            - Loops through each selected object
            - Calculates new position by adding translation amounts to current position
            - Checks if snap is enabled, and if so, snaps new position to walkmesh
            - Sets new position on object instance.
        """
        assert self.renderer.scene is not None
        for obj in self.renderer.scene.selection:
            x: float = obj.data.position.x + dx
            y: float = obj.data.position.y + dy
            z: float = obj.data.position.z

            point: Vector3 = Vector3(
                obj.data.position.x + dx,
                obj.data.position.y + dy,
                obj.data.position.z,
            )
            if snap:
                point = self.renderer.walkmesh_point(x, y, z)
            point.z += dz

            instance: GITInstance = obj.data
            instance.position = point

    def rotate_selected_objects(
        self,
        yaw: float,
        pitch: float,
    ):
        assert self.renderer.scene is not None
        for obj in self.renderer.scene.selection:
            instance: GITInstance = obj.data
            instance.rotate(yaw / 80, 0, 0)

    def alter_camera_position(
        self,
        dx: float,
        dy: float,
        dz: float,
    ):
        assert self.renderer.scene is not None
        self.renderer.scene.camera.x += dx
        self.renderer.scene.camera.y += dy
        self.renderer.scene.camera.z += dz

    def snap_camera_position(
        self,
        x: float | None = None,
        y: float | None = None,
        z: float | None = None,
    ):
        """Snap camera position to provided coordinates.

        Args:
        ----
            x: float | None - X coordinate of camera position
            y: float | None - Y coordinate of camera position
            z: float | None - Z coordinate of camera position
        """
        if x is not None:
            self.renderer.scene.camera.x = x
        if y is not None:
            self.renderer.scene.camera.y = y
        if z is not None:
            self.renderer.scene.camera.z = z

    def alter_camera_rotation(
        self,
        yaw: float,
        pitch: float,
    ):
        assert self.renderer.scene is not None
        self.renderer.scene.camera.yaw += yaw
        self.renderer.scene.camera.pitch = min(
            math.pi - 0.000001,
            max(0.000001, self.renderer.scene.camera.pitch + pitch),
        )

    def set_camera_rotation(
        self,
        yaw: float,
        pitch: float,
    ):
        assert self.renderer.scene is not None
        self.renderer.scene.camera.yaw = yaw
        self.renderer.scene.camera.pitch = pitch

    def select_object_at_mouse(self):
        self.renderer.do_select = True

    def open_context_menu(self):
        x, y = (
            self.renderer.cursor().pos().x(),
            self.renderer.cursor().pos().y(),
        )
        self.renderer.customContextMenuRequested.emit(
            self.renderer.mapFromGlobal(QPoint(x, y)),
        )

    def alter_camera_zoom(
        self,
        amount: float,
    ):
        assert self.renderer.scene is not None
        if isinstance(self.renderer.scene.camera, Camera):
            self.renderer.scene.camera.distance = max(0, self.renderer.scene.camera.distance + amount)


class DynamicModuleEditorControls(ModuleEditorControls):
    def __init__(
        self,
        renderer: ModuleRenderer,
        filepath: str | None = None,
    ):
        super().__init__(renderer)

        self.name: str = ""

        self.mouse_move_events: list[DCItem] = []
        self.mouse_press_events: list[DCItem] = []
        self.mouse_release_events: list[DCItem] = []
        self.mouse_scroll_events: list[DCItem] = []
        self.key_press_events: list[DCItem] = []
        self.key_release_events: list[DCItem] = []
        # self.keyHoldEvents: list[DCItem] = []

        if filepath is not None:
            self.load(filepath)

    def load(
        self,
        filepath: str,
    ):
        """Load a filepath into the editor.

        Args:
        ----
            filepath (str): Path to JSON file

        Loads data from JSON file:
            - Parses JSON file and extracts data
            - Initializes variables from JSON
            - Initializes control events from JSON
            - Raises errors for invalid data.
        """
        self.variables: list[DCVariable] = []
        self.mouse_move_events.clear()
        self.mouse_press_events.clear()
        self.mouse_release_events.clear()
        self.mouse_scroll_events.clear()
        self.key_press_events.clear()
        self.key_release_events.clear()

        r_filepath: Path = Path(filepath)
        data: bytes = r_filepath.read_bytes()
        rootJSON: dict[str, Any] = json.loads(jsmin(decode_bytes_with_fallbacks(data)))

        self.name = rootJSON["name"]
        self.camera_style = rootJSON["style"]

        for name, variableJSON in rootJSON["variables"].items():
            data_type: str = variableJSON["type"]
            default: Any = variableJSON["default"]

            var: DCVariable | None = None
            if data_type == "STRING":
                var = DCVariableString(name, default, variableJSON["allowed"])
            elif data_type == "INT":
                var = DCVariableInt(name, default)
            elif data_type == "FLOAT":
                var = DCVariableFloat(name, default)
            elif data_type == "BOOL":
                var = DCVariableBool(name, default)
            else:
                msg = f"Unknown data type '{data_type}'."
                raise ValueError(msg)

            self.variables.append(var)

        array: list[DCItem]
        for controlJSON in rootJSON["controls"]:
            if controlJSON["event"] == "MOUSE_MOVE":
                array = self.mouse_move_events
            elif controlJSON["event"] == "MOUSE_PRESS":
                array = self.mouse_press_events
            elif controlJSON["event"] == "MOUSE_RELEASE":
                array = self.mouse_release_events
            elif controlJSON["event"] == "MOUSE_SCROLL":
                array = self.mouse_scroll_events
            elif controlJSON["event"] == "KEY_PRESS":
                array = self.key_press_events
            elif controlJSON["event"] == "KEY_RELEASE":
                array = self.key_release_events
            else:
                msg = f"""Unknown event '{controlJSON["event"]}'."""
                raise ValueError(msg)

            if controlJSON["keys"] is None:
                keys = None
            else:
                keys: set[int | Qt.Key | QKeySequence] | None = set()
                for keyJSON in controlJSON["keys"]:
                    key: int | Qt.Key | QKeySequence = keyJSON if isinstance(keyJSON, int) else get_key_code(keyJSON)
                    keys.add(key)

            if controlJSON["mouse"] is None:
                mouse: set[int | Qt.MouseButton] | None = None
            else:
                mouse = set()
                for mouseJSON in controlJSON["mouse"]:
                    btn: int | Qt.MouseButton = mouseJSON if isinstance(mouseJSON, int) else get_mouse_code(mouseJSON)
                    mouse.add(btn)

            effects: list[DCEffect] = []
            for effectsJSON in controlJSON["effects"]:
                for effectJSON in effectsJSON:
                    args: list[Any] = effectsJSON[effectJSON]

                    if effectJSON not in DC_EFFECT_MAP:
                        msg: str = f"Unknown effect '{effectJSON}'."
                        raise ValueError(msg)
                    try:
                        effect: DCEffect = DC_EFFECT_MAP[effectJSON](*args)
                    except TypeError as e:
                        msg: str = f"Invalid number of arguments for '{effectJSON}'."
                        raise ValueError(msg) from e

                    effects.append(effect)

            mouse = set() if mouse is None else mouse
            array.append(
                DCItem(
                    keys,  # pyright: ignore[reportArgumentType]
                    mouse,
                    effects,
                ),
            )

    def on_mouse_moved(
        self,
        screen: Vector2,
        delta: Vector2,
        buttons: set[int],
        keys: set[int],
    ):
        for event in self.mouse_move_events:
            if (event.mouse == buttons or event.mouse is None) and (event.keys == keys or event.keys is None):
                for effect in event.effects:
                    effect.apply(self, delta.x, delta.y)

    def on_mouse_scrolled(
        self,
        delta: Vector2,
        buttons: set[int],
        keys: set[int],
    ):
        for event in self.mouse_scroll_events:
            if (event.mouse == buttons or event.mouse is None) and (event.keys == keys or event.keys is None):
                for effect in event.effects:
                    effect.apply(self, delta.x, delta.y)

    def on_mouse_pressed(
        self,
        screen: Vector2,
        buttons: set[int],
        keys: set[int],
    ):
        for event in self.mouse_press_events:
            if (event.mouse == buttons or event.mouse is None) and (event.keys == keys or event.keys is None):
                for effect in event.effects:
                    effect.apply(self, 0, 0)

    def on_mouse_released(
        self,
        screen: Vector2,
        buttons: set[int],
        keys: set[int],
    ):
        for event in self.mouse_release_events:
            if (event.mouse == buttons or event.mouse is None) and (event.keys == keys or event.keys is None):
                for effect in event.effects:
                    effect.apply(self, 0, 0)

    def on_key_pressed(
        self,
        buttons: set[int],
        keys: set[int],
    ):
        for event in self.key_press_events:
            if (event.mouse == buttons or event.mouse is None) and (event.keys == keys or event.keys is None):
                for effect in event.effects:
                    effect.apply(self, 0, 0)

    def on_key_released(
        self,
        buttons: set[int],
        keys: set[int],
    ):
        for event in self.key_release_events:
            if (event.mouse == buttons or event.mouse is None) and (event.keys == keys or event.keys is None):
                for effect in event.effects:
                    effect.apply(self, 0, 0)


class HolocronModuleEditorControls(DynamicModuleEditorControls):
    def __init__(
        self,
        renderer: ModuleRenderer,
    ):
        """Initializes a camera controller.

        Args:
        ----
            renderer: ModuleRenderer - The renderer for the scene

        Processing Logic:
        ----------------
            - Defines camera sensitivity variables
            - Sets up mouse and key events to control camera position and rotation
            - Mouse events pan/rotate camera and select/manipulate objects
            - Key events directly set or incrementally change camera rotation
            - CTRL modifiers used to raise/lower camera along Z-axis.
        """
        super().__init__(renderer)

        self.variables: list[DCVariable] = [
            DCVariableFloat("panCamSensitivity", 0.033),
            DCVariableFloat("rotateCamSensitivity", 0.005),
            DCVariableFloat("raiseCamSensitivity", 0.025),
            DCVariableFloat("panObjSensitivity", 0.033),
            DCVariableFloat("rotateObjSensitivity", 0.005),
        ]

        self.mouse_move_events: list[DCItem] = [
            DCItem(
                {get_key_code("CTRL")},
                {get_mouse_code("LEFT")},
                [DCEffectAlterCameraPosition("panCamSensitivity", "cx", "cy", 0)],
            ),
            DCItem(
                {get_key_code("CTRL")},
                {get_mouse_code("MIDDLE")},
                [
                    DCEffectAlterCameraRotation("rotateCamSensitivity", "dx", "dy"),
                ],
            ),
            DCItem(
                set(),
                {get_mouse_code("LEFT")},
                [
                    DCEffectAlterObjectPosition("panObjSensitivity", True, "cx", "cy", 0),
                ],
            ),
            DCItem(
                set(),
                {get_mouse_code("MIDDLE")},
                [
                    DCEffectAlterObjectRotation("rotateObjSensitivity", "dx"),
                ],
            ),
        ]
        self.mouse_press_events: list[DCItem] = [
            DCItem(set(), {get_mouse_code("LEFT")}, [DCEffectSelectObjectAtMouse()]),
            DCItem(set(), {get_mouse_code("RIGHT")}, [DCEffectOpenContextMenu()]),
        ]
        self.mouse_release_events: list[DCItem] = []
        self.mouse_scroll_events: list[DCItem] = [
            DCItem(
                {get_key_code("CTRL")},
                set(),
                [DCEffectAlterCameraPosition("raiseCamSensitivity", 0, 0, "dy")],
            ),
        ]
        self.key_press_events: list[DCItem] = [
            DCItem({get_key_code("1")}, set(), [DCEffectSetCameraRotation(0, "crp")]),
            DCItem(
                {get_key_code("3")},
                set(),
                [
                    DCEffectSetCameraRotation(0, "crp"),
                    DCEffectAlterCameraRotation(None, math.pi / 2, 0),
                ],
            ),
            DCItem({get_key_code("7")}, set(), [DCEffectSetCameraRotation("cry", 0)]),
            DCItem({get_key_code("4")}, set(), [DCEffectAlterCameraRotation(None, math.pi / 8, 0)]),
            DCItem({get_key_code("6")}, set(), [DCEffectAlterCameraRotation(None, -math.pi / 8, 0)]),
            DCItem({get_key_code("8")}, set(), [DCEffectAlterCameraRotation(None, 0, math.pi / 8)]),
            DCItem({get_key_code("2")}, set(), [DCEffectAlterCameraRotation(None, 0, -math.pi / 8)]),
            DCItem({get_key_code("W")}, set(), [DCEffectAlterCameraRotation(None, 0, math.pi / 8)]),
            DCItem({get_key_code("A")}, set(), [DCEffectAlterCameraRotation(None, math.pi / 8, 0)]),
            DCItem({get_key_code("S")}, set(), [DCEffectAlterCameraRotation(None, 0, -math.pi / 8)]),
            DCItem({get_key_code("D")}, set(), [DCEffectAlterCameraRotation(None, -math.pi / 8, 0)]),
            DCItem({get_key_code("Q")}, set(), [DCEffectAlterCameraPosition(None, 0, 0, 1)]),
            DCItem({get_key_code("Z")}, set(), [DCEffectAlterCameraPosition(None, 0, 0, -1)]),
        ]
        self.key_release_events: list[DCItem] = []


class DCItem:
    def __init__(
        self,
        keys: set[int] | set[Qt.Key | QKeySequence],
        mouse: set[int] | set[Qt.MouseButton] | set[int | Qt.MouseButton],
        effects: list[DCEffect],
    ):
        self.keys: set[int] | set[Qt.Key | QKeySequence] = keys
        self.mouse: set[int] | set[Qt.MouseButton] | set[int | Qt.MouseButton] = mouse
        self.effects: list[DCEffect] = effects


class DCVariable:
    def __init__(
        self,
        name: str,
    ):
        self._name: str = name

    def name(self) -> str:
        return self._name

    def get(self) -> Any:
        raise NotImplementedError

    def set(self, value: Any) -> NoReturn:
        raise NotImplementedError


# region Variable Classes
class DCVariableInt(DCVariable):
    def __init__(
        self,
        name: str,
        value: int,
    ):
        super().__init__(name)
        self._value: int = value

    def set(
        self,
        value: int,
    ):
        self._value = value

    def get(self) -> int:
        return self._value


class DCVariableFloat(DCVariable):
    def __init__(
        self,
        name: str,
        value: float,
    ):
        super().__init__(name)
        self._value: float = value

    def name(self) -> str:
        return self._name

    def set(
        self,
        value: float,
    ):
        self._value = value

    def get(self) -> float:
        return self._value


class DCVariableBool(DCVariable):
    def __init__(
        self,
        name: str,
        value: bool,  # noqa: FBT001
    ):
        super().__init__(name)
        self._value: bool = value

    def name(self) -> str:
        return self._name

    def set(
        self,
        value: bool,  # noqa: FBT001
    ):
        self._value = value

    def get(self) -> bool:
        return self._value


class DCVariableString(DCVariable):
    def __init__(
        self,
        name: str,
        value: str,
        allowed: list[str],
    ):
        super().__init__(name)
        self._value: str = value
        self._allowed: list[str] = allowed

    def name(self) -> str:
        return self._name

    def set(
        self,
        value: str,
    ):
        self._value = value

    def get(self) -> str:
        return self._value


class DCEffect(ABC):
    @abstractmethod
    def apply(
        self,
        controls: ModuleEditorControls,
        dx: float,
        dy: float,
    ): ...

    @staticmethod
    def determine_float(  # noqa: PLR0915, PLR0912, C901
        value: float | str,
        controls: ModuleEditorControls,
        dx: float,
        dy: float,
    ) -> float:
        """Determines a float value from a value or string.

        Args:
        ----
            value: {The value or string to determine the float from}
            controls: {Module editor controls object}
            dx: float - Camera delta x
            dy: float - Camera delta y

        Returns:
        -------
            float: {The determined float value}

        Processes Logic:
            - Checks if value is a string and extracts modifier
            - Maps string aliases like "dx" to appropriate values
            - Performs camera transformations on aliases like "cpdx"
            - Returns float value or 0 if not matched.
        """
        assert controls.renderer.scene is not None
        if not isinstance(value, str):
            return value if isinstance(value, (float, int)) else 0
        output: float = 0.0
        modifier: float = 1.0
        if value.startswith("-"):
            modifier = -1.0
            value = value[1:]

        if value == "dx":
            output = dx
        elif value == "dy":
            output = dy

        elif value == "cpdxFlat":
            forward: vec3 = -dy * controls.renderer.scene.camera.forward()
            sideward: vec3 = dx * controls.renderer.scene.camera.sideward()
            output: float = -(forward.x + sideward.x)
        elif value == "cpdyFlat":
            forward = -dy * controls.renderer.scene.camera.forward()
            sideward = dx * controls.renderer.scene.camera.sideward()
            output = -(forward.y + sideward.y)

        elif value == "cpdx":
            sideward = dx * controls.renderer.scene.camera.sideward(ignore_z=False)
            upward: vec3 = dy * controls.renderer.scene.camera.upward(ignore_xy=False)
            output = -(upward.x + sideward.x)
        elif value == "cpdy":
            sideward = dx * controls.renderer.scene.camera.sideward(ignore_z=False)
            upward = dy * controls.renderer.scene.camera.upward(ignore_xy=False)
            output = -(upward.y + sideward.y)
        elif value == "cpdz":
            sideward = dx * controls.renderer.scene.camera.sideward(ignore_z=False)
            upward = dy * controls.renderer.scene.camera.upward(ignore_xy=False)
            output = -(upward.z + sideward.z)

        elif value == "cpxFlat":
            forward = controls.renderer.scene.camera.forward()
            output = forward.x
        elif value == "cpyFlat":
            forward = controls.renderer.scene.camera.forward()
            output = forward.y

        elif value == "cpx":
            forward = controls.renderer.scene.camera.sideward(ignore_z=False)
            output = forward.x
        elif value == "cpy":
            forward = controls.renderer.scene.camera.sideward(ignore_z=False)
            output = forward.y
        elif value == "cpz":
            forward = controls.renderer.scene.camera.sideward(ignore_z=False)
            output = forward.z

        elif value == "cry":
            output = controls.renderer.scene.camera.yaw
        elif value == "crp":
            output = controls.renderer.scene.camera.pitch

        return output * modifier


# endregion


# region Effect Classes
# alter_camera_position
class DCEffectAlterCameraPosition(DCEffect):
    def __init__(
        self,
        sensitivity_var: str | None,
        x: float | str,
        y: float | str,
        z: float | str,
    ):
        self.sensitivity_var: str | None = sensitivity_var
        self.x: float | str = x
        self.y: float | str = y
        self.z: float | str = z

    def apply(
        self,
        controls: ModuleEditorControls,
        dx: float,
        dy: float,
    ):
        x: float = super().determine_float(self.x, controls, dx, dy)
        y: float = super().determine_float(self.y, controls, dx, dy)
        z: float = super().determine_float(self.z, controls, dx, dy)
        sensitivity: float = 1.0 if self.sensitivity_var is None else controls.getValue(self.sensitivity_var)
        controls.alter_camera_position(x * sensitivity, y * sensitivity, z * sensitivity)


# set_camera_position
class DCEffectSetCameraPosition(DCEffect):
    def __init__(
        self,
        x: float | str,
        y: float | str,
        z: float | str,
    ):
        self.x: float | str = x
        self.y: float | str = y
        self.z: float | str = z

    def apply(
        self,
        controls: ModuleEditorControls,
        dx: float,
        dy: float,
    ):
        x: float = super().determine_float(self.x, controls, dx, dy)
        y: float = super().determine_float(self.y, controls, dx, dy)
        z: float = super().determine_float(self.z, controls, dx, dy)
        controls.alter_camera_position(x, y, z)


# alter_camera_rotation
class DCEffectAlterCameraRotation(DCEffect):
    def __init__(
        self,
        sensitivity_var: str | None,
        yaw: float | str,
        pitch: float | str,
    ):
        self.sensitivity_var: str | None = sensitivity_var
        self.yaw: float | str = yaw
        self.pitch: float | str = pitch

    def apply(
        self,
        controls: ModuleEditorControls,
        dx: float,
        dy: float,
    ):
        pitch: float = super().determine_float(self.pitch, controls, dx, dy)
        yaw: float = super().determine_float(self.yaw, controls, dx, dy)
        sensitivity: float = 1.0 if self.sensitivity_var is None else controls.getValue(self.sensitivity_var)
        controls.alter_camera_rotation(yaw * sensitivity, pitch * sensitivity)


# set_camera_rotation
class DCEffectSetCameraRotation(DCEffect):
    def __init__(
        self,
        yaw: float | str,
        pitch: float | str,
    ):
        self.yaw: float | str = yaw
        self.pitch: float | str = pitch

    def apply(
        self,
        controls: ModuleEditorControls,
        dx: float,
        dy: float,
    ):
        yaw: float = super().determine_float(self.yaw, controls, dx, dy)
        pitch: float = super().determine_float(self.pitch, controls, dx, dy)
        controls.set_camera_rotation(yaw, pitch)


# alter_camera_zoom
class DCEffectAlterCameraZoom(DCEffect):
    def __init__(
        self,
        sensitivity_var: str | None,
        amount: float | str,
    ):
        self.sensitivity_var: str | None = sensitivity_var
        self.amount: float | str = amount

    def apply(
        self,
        controls: ModuleEditorControls,
        dx: float,
        dy: float,
    ):
        amount: float = super().determine_float(self.amount, controls, dx, dy)
        sensitivity: float = 1.0 if self.sensitivity_var is None else controls.getValue(self.sensitivity_var)
        controls.alter_camera_zoom(amount * sensitivity)


# alterObjectPosition
class DCEffectAlterObjectPosition(DCEffect):
    def __init__(
        self,
        sensitivity_var: str | None,
        snap_to_walkmesh: bool,  # noqa: FBT001
        x: float | str,
        y: float | str,
        z: float | str,
    ):
        self.sensitivity_var: str | None = sensitivity_var
        self.snap_to_walkmesh: bool = snap_to_walkmesh
        self.x: float | str = x
        self.y: float | str = y
        self.z: float | str = z

    def apply(
        self,
        controls: ModuleEditorControls,
        dx: float,
        dy: float,
    ):
        x: float = super().determine_float(self.x, controls, dx, dy)
        y: float = super().determine_float(self.y, controls, dx, dy)
        z: float = super().determine_float(self.z, controls, dx, dy)
        sensitivity: float = 1.0 if self.sensitivity_var is None else controls.getValue(self.sensitivity_var)
        controls.translate_selected_objects(self.snap_to_walkmesh, -x * sensitivity, -y * sensitivity, z * sensitivity)


# alterObjectRotation
class DCEffectAlterObjectRotation(DCEffect):
    def __init__(
        self,
        sensitivity_var: str | None,
        yaw: float | str,
    ):
        self.sensitivity_var: str | None = sensitivity_var
        self.yaw: float | str = yaw

    def apply(
        self,
        controls: ModuleEditorControls,
        dx: float,
        dy: float,
    ):
        yaw: float = super().determine_float(self.yaw, controls, dx, dy)
        sensitivity: float = 1.0 if self.sensitivity_var is None else controls.getValue(self.sensitivity_var)
        controls.rotate_selected_objects(yaw * sensitivity, 0.0)


# select_object_at_mouse
class DCEffectSelectObjectAtMouse(DCEffect):
    def __init__(self): ...

    def apply(
        self,
        controls: ModuleEditorControls,
        dx: float,
        dy: float,
    ):
        controls.select_object_at_mouse()


# open_context_menu
class DCEffectOpenContextMenu(DCEffect):
    def __init__(self): ...

    def apply(
        self,
        controls: ModuleEditorControls,
        dx: float,
        dy: float,
    ):
        controls.open_context_menu()


# setVariable
class DCEffectSetVariable(DCEffect):
    def __init__(self, name: str, value: Any):
        self.name: str = name
        self.value: Any = value

    def apply(
        self,
        controls: ModuleEditorControls,
        dx: float,
        dy: float,
    ):
        controls.setValue(self.name, self.value)


# changeCameraFocus
class DCEffectChangeCameraFocus(DCEffect):
    def __init__(
        self,
        focus: bool | None = None,
    ):
        self.focus: bool | None = focus

    def apply(
        self,
        controls: ModuleEditorControls,
        dx: float,
        dy: float,
    ): ...


# snapCameraToObject
class DCEffectSnapCameraToObject(DCEffect):
    def __init__(
        self,
        distance: float,
    ):
        self.distance: float = distance

    def apply(
        self,
        controls: ModuleEditorControls,
        dx: float,
        dy: float,
    ):
        if controls.renderer.scene.selection:
            controls.renderer.snap_camera_to_point(
                Vector3(*controls.renderer.scene.selection[0].position()),
                self.distance,
            )


# endregion


DC_EFFECT_MAP: dict[str, type[DCEffect]] = {
    "alter_camera_position": DCEffectAlterCameraPosition,
    "alter_camera_rotation": DCEffectAlterCameraRotation,
    "alter_camera_zoom": DCEffectAlterCameraZoom,
    "set_camera_position": DCEffectSetCameraPosition,
    "set_camera_rotation": DCEffectSetCameraRotation,
    "alterObjectPosition": DCEffectAlterObjectPosition,
    "alterObjectRotation": DCEffectAlterObjectRotation,
    "select_object_at_mouse": DCEffectSelectObjectAtMouse,
    "open_context_menu": DCEffectOpenContextMenu,
    "setVariable": DCEffectSetVariable,
    "changeCameraFocus": DCEffectChangeCameraFocus,
    "snapCameraToObject": DCEffectSnapCameraToObject,
}
