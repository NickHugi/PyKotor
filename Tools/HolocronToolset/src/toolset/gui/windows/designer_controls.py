from __future__ import annotations

import time

from copy import deepcopy
from typing import TYPE_CHECKING

import qtpy

from qtpy import QtCore
from qtpy.QtCore import QPoint

if qtpy.API_NAME in ("PyQt5", "PySide2"):
    pass
elif qtpy.API_NAME in ("PyQt6", "PySide6"):
    pass
else:
    raise ValueError(f"Invalid QT_API: '{qtpy.API_NAME}'")

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy.QtCore import Qt

from pykotor.common.geometry import Vector2, Vector3, Vector4
from pykotor.resource.generics.git import GITCamera, GITCreature, GITDoor, GITPlaceable, GITStore, GITWaypoint
from toolset.data.misc import ControlItem
from toolset.gui.editors.git import DuplicateCommand, _GeometryMode, _InstanceMode, calculate_zoom_strength
from toolset.gui.widgets.settings.module_designer import ModuleDesignerSettings
from toolset.utils.misc import BUTTON_TO_INT

if TYPE_CHECKING:
    from pykotor.resource.generics.git import GITInstance
    from toolset.gui.editors.git import _SpawnMode
    from toolset.gui.widgets.renderer.module import ModuleRenderer
    from toolset.gui.widgets.renderer.walkmesh import WalkmeshRenderer
    from toolset.gui.windows.module_designer import ModuleDesigner


class ModuleDesignerControls3d:
    def __init__(self, editor: ModuleDesigner, renderer: ModuleRenderer):
        self.editor: ModuleDesigner = editor
        self.renderer: ModuleRenderer = renderer
        self.renderer.setCursor(QtCore.Qt.CursorShape.ArrowCursor)
        if self.renderer._scene is not None:  # noqa: SLF001
            self.renderer._scene.show_cursor = True  # noqa: SLF001

    def on_mouse_scrolled(self, delta: Vector2, buttons: set[int], keys: set[int]):
        if self.zoom_camera.satisfied(buttons, keys):
            strength = self.settings.zoomCameraSensitivity3d / 10000
            self.renderer.scene.camera.distance += -delta.y * strength
        elif self.move_z_camera.satisfied(buttons, keys):
            strength = self.settings.moveCameraSensitivity3d / 10000
            self.renderer.scene.camera.z -= -delta.y * strength

    def on_mouse_moved(
        self,
        screen: Vector2,
        screen_delta: Vector2,
        world: Vector3,
        buttons: set[int],
        keys: set[int],
    ):
        # Handle mouse-specific cursor lock and plane movement
        move_xy_camera_satisfied = self.move_xy_camera.satisfied(buttons, keys)
        move_camera_plane_satisfied = self.move_camera_plane.satisfied(buttons, keys)
        rotate_camera_satisfied = self.rotate_camera.satisfied(buttons, keys)
        zoom_camera_satisfied = self.zoom_camera_mm.satisfied(buttons, keys)
        if move_xy_camera_satisfied or move_camera_plane_satisfied or rotate_camera_satisfied or zoom_camera_satisfied:
            self.editor.do_cursor_lock(mutable_screen=screen, center_mouse=False, do_rotations=False)
            move_strength = self.settings.moveCameraSensitivity3d / 1000
            if move_xy_camera_satisfied:
                forward = -screen_delta.y * self.renderer.scene.camera.forward()
                sideward = screen_delta.x * self.renderer.scene.camera.sideward()
                self.renderer.scene.camera.x -= (forward.x + sideward.x) * move_strength
                self.renderer.scene.camera.y -= (forward.y + sideward.y) * move_strength
            if move_camera_plane_satisfied:  # sourcery skip: extract-method
                upward = screen_delta.y * self.renderer.scene.camera.upward(ignore_xy=False)
                sideward = screen_delta.x * self.renderer.scene.camera.sideward()
                self.renderer.scene.camera.z -= (upward.z + sideward.z) * move_strength
                self.renderer.scene.camera.y -= (upward.y + sideward.y) * move_strength
                self.renderer.scene.camera.x -= (upward.x + sideward.x) * move_strength
            rotate_strength = self.settings.moveCameraSensitivity3d / 10000
            if rotate_camera_satisfied:
                self.renderer.rotate_camera(-screen_delta.x * rotate_strength, screen_delta.y * rotate_strength, clamp_rotations=True)
            if zoom_camera_satisfied:
                self.renderer.scene.camera.distance -= screen_delta.y * rotate_strength

        # Handle movement of selected instances.
        if self.editor.ui.lockInstancesCheck.isChecked():
            return
        if self.move_xy_selected.satisfied(buttons, keys):

            if not self.editor.is_drag_moving:
                self.editor.initial_positions = {instance: instance.position for instance in self.editor.selected_instances}
                self.editor.is_drag_moving = True
            for instance in self.editor.selected_instances:
                scene = self.renderer.scene
                assert scene is not None

                x = scene.cursor.position().x
                y = scene.cursor.position().y
                z = instance.position.z if isinstance(instance, GITCamera) else scene.cursor.position().z
                instance.position = Vector3(x, y, z)

        if self.move_z_selected.satisfied(buttons, keys):
            if self.editor.ui.lockInstancesCheck.isChecked():
                return
            if not self.editor.is_drag_moving:
                self.editor.initial_positions = {instance: instance.position for instance in self.editor.selected_instances}
                self.editor.is_drag_moving = True
            for instance in self.editor.selected_instances:
                instance.position.z -= screen_delta.y / 40

        if self.rotate_selected.satisfied(buttons, keys):
            if self.editor.ui.lockInstancesCheck.isChecked():
                return
            if not self.editor.is_drag_rotating:
                self.editor.is_drag_rotating = True
                for instance in self.editor.selected_instances:
                    if not isinstance(instance, (GITCamera, GITCreature, GITDoor, GITPlaceable, GITStore, GITWaypoint)):
                        continue  # doesn't support rotations.
                    self.editor.initial_rotations[instance] = Vector4(*instance.orientation) if isinstance(instance, GITCamera) else instance.bearing
            self.editor.rotate_selected(screen_delta.x, screen_delta.y)

    def on_mouse_pressed(self, screen: Vector2, buttons: set[int], keys: set[int]):
        if self.select_underneath.satisfied(buttons, keys):
            self.renderer.do_select = True  # auto-selects the instance under the mouse in the paint loop, and implicitly sets this back to False

        scene = self.renderer.scene
        assert scene is not None
        if (
            self.duplicate_selected.satisfied(buttons, keys)
            and self.editor.selected_instances
        ):
            self._duplicate_selected_instance()
        if self.open_context_menu.satisfied(buttons, keys):
            world = Vector3(*scene.cursor.position())
            self.editor.on_context_menu(world, self.renderer.mapToGlobal(QPoint(int(screen.x), int(screen.y))))

    def on_mouse_released(
        self,
        screen: Vector2,
        buttons: set[int],
        keys: set[int],
    ):
        self.editor.handle_undo_redo_from_long_action_finished()

    def on_keyboard_released(self, buttons: set[int], keys: set[int]):
        self.editor.handle_undo_redo_from_long_action_finished()

    def _duplicate_selected_instance(self):  # TODO(th3w1zard1): Seems the code throughout is designed for multi-selections, yet nothing uses it. Probably disabled due to a bug or planned for later.
        instance: GITInstance = deepcopy(self.editor.selected_instances[-1])
        if isinstance(instance, GITCamera):
            instance.camera_id = self.editor._module.git().resource().next_camera_id()
        self.editor.log.info(f"Duplicating {instance!r}")
        self.editor.undo_stack.push(DuplicateCommand(self.editor._module.git().resource(), [instance], self.editor))  # noqa: SLF001
        vect3 = self.renderer.scene.cursor.position()
        instance.position = Vector3(vect3.x, vect3.y, vect3.z)
        #self.editor.git().add(instance)  # Handled by the undoStack above.
        self.editor.rebuild_instance_list()
        self.editor.set_selection([instance])

    def on_keyboard_pressed(self, buttons: set[int], keys: set[int]):
        scene = self.renderer.scene
        assert scene is not None

        if self.toggle_free_cam.satisfied(buttons, keys):
            current_time = time.time()
            if current_time - self.editor.last_free_cam_time > 0.5:  # 0.5 seconds delay, prevents spamming
                self.editor.toggle_free_cam()
                self.editor.last_free_cam_time = current_time  # Update the last toggle time
            return

        # Check camera movement keys
        move_camera_keys = {
            "selected": self.move_camera_to_selected.satisfied(buttons, keys),
            "cursor": self.move_camera_to_cursor.satisfied(buttons, keys),
            "entry": self.move_camera_to_entry_point.satisfied(buttons, keys)
        }
        if any(move_camera_keys.values()):
            if move_camera_keys["selected"]:
                instance = next(iter(self.editor.selected_instances), None)
                if instance is not None:
                    self.renderer.snap_camera_to_point(instance.position)
            elif move_camera_keys["cursor"]:
                scene.camera.set_position(scene.cursor.position())
            elif move_camera_keys["entry"]:
                self.editor.snap_camera_to_entry_location()
            return
        if self.delete_selected.satisfied(buttons, keys):
            self.editor.delete_selected()
            return
        if self.duplicate_selected.satisfied(buttons, keys):
            self._duplicate_selected_instance()
            return
        if self.toggle_instance_lock.satisfied(buttons, keys):
            self.editor.ui.lockInstancesCheck.setChecked(not self.editor.ui.lockInstancesCheck.isChecked())

    @property
    def move_xy_camera(self):
        return ControlItem(self.settings.moveCameraXY3dBind)

    @property
    def move_z_camera(self):
        return ControlItem(self.settings.moveCameraZ3dBind)

    @property
    def move_camera_plane(self):
        return ControlItem(self.settings.moveCameraPlane3dBind)

    @property
    def rotate_camera(self):
        return ControlItem(self.settings.rotateCamera3dBind)

    @property
    def zoom_camera(self):
        return ControlItem(self.settings.zoomCamera3dBind)

    @property
    def zoom_camera_mm(self):
        return ControlItem(self.settings.zoomCameraMM3dBind)

    @property
    def rotate_selected(self):
        return ControlItem(self.settings.rotateSelected3dBind)

    @property
    def move_xy_selected(self):
        return ControlItem(self.settings.moveSelectedXY3dBind)

    @property
    def move_z_selected(self):
        return ControlItem(self.settings.moveSelectedZ3dBind)

    @property
    def select_underneath(self):
        return ControlItem(self.settings.selectObject3dBind)

    @property
    def move_camera_to_selected(self):
        return ControlItem(self.settings.moveCameraToSelected3dBind)

    @property
    def move_camera_to_cursor(self):
        return ControlItem(self.settings.moveCameraToCursor3dBind)

    @property
    def move_camera_to_entry_point(self):
        return ControlItem(self.settings.moveCameraToEntryPoint3dBind)

    @property
    def toggle_free_cam(self):
        return ControlItem(self.settings.toggleFreeCam3dBind)

    @property
    def delete_selected(self):
        return ControlItem(self.settings.deleteObject3dBind)

    @property
    def duplicate_selected(self):
        return ControlItem(self.settings.duplicateObject3dBind)

    @property
    def open_context_menu(self):
        return ControlItem((set(), {BUTTON_TO_INT[Qt.MouseButton.RightButton]}))

    @property
    def rotate_camera_left(self):
        return ControlItem(self.settings.rotateCameraLeft3dBind)

    @property
    def rotate_camera_right(self):
        return ControlItem(self.settings.rotateCameraRight3dBind)

    @property
    def rotate_camera_up(self):
        return ControlItem(self.settings.rotateCameraUp3dBind)

    @property
    def rotate_camera_down(self):
        return ControlItem(self.settings.rotateCameraDown3dBind)

    @property
    def move_camera_up(self):
        return ControlItem(self.settings.moveCameraUp3dBind)

    @property
    def move_camera_down(self):
        return ControlItem(self.settings.moveCameraDown3dBind)

    @property
    def move_camera_forward(self):
        return ControlItem(self.settings.moveCameraForward3dBind)

    @property
    def move_camera_backward(self):
        return ControlItem(self.settings.moveCameraBackward3dBind)

    @property
    def move_camera_left(self):
        return ControlItem(self.settings.moveCameraLeft3dBind)

    @property
    def move_camera_right(self):
        return ControlItem(self.settings.moveCameraRight3dBind)

    @property
    def zoom_camera_in(self):
        return ControlItem(self.settings.zoomCameraIn3dBind)

    @property
    def zoom_camera_out(self):
        return ControlItem(self.settings.zoomCameraOut3dBind)

    @property
    def toggle_instance_lock(self):
        return ControlItem(self.settings.toggleLockInstancesBind)

    @property
    def speed_boost_control(self):
        return ControlItem(self.settings.speedBoostCamera3dBind)

    @property
    def settings(self) -> ModuleDesignerSettings:
        return ModuleDesignerSettings()

    @property
    def lyt_grid_size(self):
        return self.settings.lytGridSize

    @property
    def lyt_snap_to_grid(self):
        return self.settings.lytSnapToGrid

    @property
    def lyt_show_grid(self):
        return self.settings.lytShowGrid


class ModuleDesignerControlsFreeCam:
    def __init__(self, editor: ModuleDesigner, renderer: ModuleRenderer):
        self.editor: ModuleDesigner = editor
        self.renderer: ModuleRenderer = renderer
        self.renderer.keys_down().clear()
        self.controls3d_distance = self.renderer.scene.camera.distance
        self.renderer.scene.camera.distance = 0
        self.renderer.setCursor(QtCore.Qt.CursorShape.BlankCursor)
        self.renderer.scene.show_cursor = False


    def on_mouse_scrolled(self, delta: Vector2, buttons: set[int], keys: set[int]): ...

    def on_mouse_moved(self, screen: Vector2, screen_delta: Vector2, world: Vector3, buttons: set[int], keys: set[int]):  # noqa: PLR0913
        self.editor.do_cursor_lock(screen)

    def on_mouse_pressed(self, screen: Vector2, buttons: set[int], keys: set[int]):
        ...

    def on_mouse_released(self, screen: Vector2, buttons: set[int], keys: set[int]): ...

    def on_keyboard_pressed(self, buttons: set[int], keys: set[int]):
        current_time = time.time()
        if self.toggle_free_cam.satisfied(buttons, keys) and (current_time - self.editor.last_free_cam_time > 0.5):  # 0.5 seconds delay, prevents spamming
            #self.renderer.scene.camera.distance = self.controls3d_distance
            self.editor.toggle_free_cam()
            self.editor.last_free_cam_time = current_time  # Update the last toggle time

    def on_keyboard_released(self, buttons: set[int], keys: set[int]): ...

    @property
    def toggle_free_cam(self):
        return ControlItem(self.settings.toggleFreeCam3dBind)

    @property
    def move_camera_up(self):
        return ControlItem(self.settings.moveCameraUpFcBind)

    @property
    def move_camera_down(self):
        return ControlItem(self.settings.moveCameraDownFcBind)

    @property
    def move_camera_forward(self):
        return ControlItem(self.settings.moveCameraForwardFcBind)

    @property
    def move_camera_backward(self):
        return ControlItem(self.settings.moveCameraBackwardFcBind)

    @property
    def move_camera_left(self):
        return ControlItem(self.settings.moveCameraLeftFcBind)

    @property
    def move_camera_right(self):
        return ControlItem(self.settings.moveCameraRightFcBind)

    @property
    def rotate_camera_left(self):
        return ControlItem(self.settings.rotateCameraLeftFcBind)

    @property
    def rotate_camera_right(self):
        return ControlItem(self.settings.rotateCameraRightFcBind)

    @property
    def rotate_camera_up(self):
        return ControlItem(self.settings.rotateCameraUpFcBind)

    @property
    def rotate_camera_down(self):
        return ControlItem(self.settings.rotateCameraDownFcBind)

    @property
    def zoom_camera_in(self):
        return ControlItem(self.settings.zoomCameraInFcBind)

    @property
    def zoom_camera_out(self):
        return ControlItem(self.settings.zoomCameraOutFcBind)

    @property
    def speed_boost_control(self):
        return ControlItem(self.settings.speedBoostCameraFcBind)

    @property
    def settings(self) -> ModuleDesignerSettings:
        return ModuleDesignerSettings()


class ModuleDesignerControls2d:
    def __init__(self, editor: ModuleDesigner, renderer: WalkmeshRenderer):
        self.editor: ModuleDesigner = editor
        self.renderer: WalkmeshRenderer = renderer
        self.settings: ModuleDesignerSettings = ModuleDesignerSettings()
        self._mode: _InstanceMode | _GeometryMode | _SpawnMode

    def on_mouse_scrolled(self, delta: Vector2, buttons: set[int], keys: set[int]):
        if self.zoom_camera.satisfied(buttons, keys):
            if not delta.y:
                return
            sens_setting = ModuleDesignerSettings().zoomCameraSensitivity2d
            zoom_factor = calculate_zoom_strength(delta.y, sens_setting)
            self.renderer.camera.nudge_zoom(zoom_factor)

    def on_mouse_moved(self, screen: Vector2, screen_delta: Vector2, world: Vector2, world_delta: Vector2, buttons: set[int], keys: set[int]):
        should_move_camera = self.move_camera.satisfied(buttons, keys)
        should_rotate_camera = self.rotate_camera.satisfied(buttons, keys)
        adjusted_world_delta = world_delta
        if should_move_camera or should_rotate_camera:
            self.renderer.do_cursor_lock(screen)
            adjusted_world_delta = Vector2(-world_delta.x, -world_delta.y)
        if should_move_camera:
            strength = self.settings.moveCameraSensitivity2d / 100
            self.renderer.camera.nudge_position(-world_delta.x * strength, -world_delta.y * strength)
        if should_rotate_camera:
            strength = self.settings.rotateCameraSensitivity2d / 100 / 50
            self.renderer.camera.nudge_rotation(screen_delta.x * strength)

        if self.editor.ui.lockInstancesCheck.isChecked():
            return
        if self.move_selected.satisfied(buttons, keys):
            if isinstance(self._mode, _GeometryMode):
                RobustLogger().debug("Move geometry point %s, %s", world_delta.x, world_delta.y)
                self._mode.move_selected(adjusted_world_delta.x, adjusted_world_delta.y)
                return

            # handle undo/redo for move_selected.
            if not self.editor.is_drag_moving:
                RobustLogger().debug("move_selected instance in 2d")
                self.editor.initial_positions = {instance: instance.position for instance in self.editor.selected_instances}
                self.editor.is_drag_moving = True
            self.editor.move_selected(adjusted_world_delta.x, adjusted_world_delta.y, no_undo_stack=True, no_z_coord=True)

        if self.rotate_selected.satisfied(buttons, keys) and isinstance(self._mode, _InstanceMode):
            if not self.editor.is_drag_rotating:
                self.editor.is_drag_rotating = True
                self.editor.log.debug("rotateSelected instance in 2d")
                selection: list[GITInstance] = self.editor.selected_instances  # noqa: SLF001
                for instance in selection:
                    if not isinstance(instance, (GITCamera, GITCreature, GITDoor, GITPlaceable, GITStore, GITWaypoint)):
                        continue  # doesn't support rotations.
                    self.editor.initial_rotations[instance] = (
                        Vector4(*instance.orientation)
                        if isinstance(instance, GITCamera)
                        else instance.bearing
                    )
            self._mode.rotate_selected_to_point(world.x, world.y)

    def on_mouse_pressed(self, screen: Vector2, buttons: set[int], keys: set[int]):
        world: Vector3 = self.renderer.to_world_coords(screen.x, screen.y)
        if (
            self.duplicate_selected.satisfied(buttons, keys)
            and self.editor.selected_instances
            and isinstance(self._mode, _InstanceMode)
        ):
            self._mode.duplicate_selected(world)
        if self.open_context_menu.satisfied(buttons, keys):
            self.editor.on_context_menu(world, self.renderer.mapToGlobal(QPoint(int(screen.x), int(screen.y))))

        if self.select_underneath.satisfied(buttons, keys):
            if isinstance(self._mode, _GeometryMode):
                RobustLogger().debug("select_underneath_geometry?")
                self._mode.select_underneath()
            elif self.renderer.instances_under_mouse():
                RobustLogger().debug("on_mouse_pressed, select_underneath found one or more instances under mouse.")
                self.editor.set_selection([self.renderer.instances_under_mouse()[-1]])
            else:
                RobustLogger().debug("on_mouse_pressed, select_underneath did not find any instances.")
                self.editor.set_selection([])

    def on_keyboard_pressed(self, buttons: set[int], keys: set[int]):
        if self.delete_selected.satisfied(buttons, keys):
            if isinstance(self._mode, _GeometryMode):
                self._mode.delete_selected()
            else:
                self.editor.delete_selected()
            return

        if self.snap_camera_to_selected.satisfied(buttons, keys):
            for instance in self.editor.selected_instances:
                self.renderer.snap_camera_to_point(instance.position)
                break

        if self.toggle_instance_lock.satisfied(buttons, keys):
            self.editor.ui.lockInstancesCheck.setChecked(not self.editor.ui.lockInstancesCheck.isChecked())

    def on_mouse_released(self, screen: Vector2, buttons: set[int], keys: set[int]):
        self.editor.handle_undo_redo_from_long_action_finished()

    def on_keyboard_released(self, buttons: set[int], keys: set[int]):
        self.editor.handle_undo_redo_from_long_action_finished()

    @property
    def move_camera(self):
        return ControlItem(self.settings.moveCamera2dBind)

    @property
    def rotate_camera(self):
        return ControlItem(self.settings.rotateCamera2dBind)

    @property
    def zoom_camera(self):
        return ControlItem(self.settings.zoomCamera2dBind)

    @property
    def rotate_selected(self):
        return ControlItem(self.settings.rotateObject2dBind)

    @property
    def move_selected(self):
        return ControlItem(self.settings.moveObject2dBind)

    @property
    def select_underneath(self):
        return ControlItem(self.settings.selectObject2dBind)

    @property
    def delete_selected(self):
        return ControlItem(self.settings.deleteObject2dBind)

    @property
    def duplicate_selected(self):
        return ControlItem(self.settings.duplicateObject2dBind)

    @property
    def snap_camera_to_selected(self):
        return ControlItem(self.settings.moveCameraToSelected2dBind)

    @property
    def open_context_menu(self):
        return ControlItem((set(), {Qt.MouseButton.RightButton}))

    @property
    def toggle_instance_lock(self):
        return ControlItem(self.settings.toggleLockInstancesBind)

    @property
    def lyt_grid_size(self):
        return self.settings.lytGridSize

    @property
    def lyt_snap_to_grid(self):
        return self.settings.lytSnapToGrid

    @property
    def lyt_show_grid(self):
        return self.settings.lytShowGrid