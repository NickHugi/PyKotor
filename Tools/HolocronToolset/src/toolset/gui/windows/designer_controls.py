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

from loggerplus import RobustLogger
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
        if self.renderer._scene is not None:
            self.renderer._scene.show_cursor = True

    def onMouseScrolled(self, delta: Vector2, buttons: set[int], keys: set[int]):
        if self.zoomCamera.satisfied(buttons, keys):
            strength = self.settings.zoomCameraSensitivity3d / 10000
            self.renderer.scene.camera.distance += -delta.y * strength
        elif self.moveZCamera.satisfied(buttons, keys):
            strength = self.settings.moveCameraSensitivity3d / 10000
            self.renderer.scene.camera.z -= -delta.y * strength

    def onMouseMoved(
        self,
        screen: Vector2,
        screenDelta: Vector2,
        world: Vector3,
        buttons: set[int],
        keys: set[int],
    ):
        # Handle mouse-specific cursor lock and plane movement
        moveXyCameraSatisfied = self.moveXYCamera.satisfied(buttons, keys)
        moveCameraPlaneSatisfied = self.moveCameraPlane.satisfied(buttons, keys)
        rotateCameraSatisfied = self.rotateCamera.satisfied(buttons, keys)
        zoomCameraSatisfied = self.zoomCameraMM.satisfied(buttons, keys)
        if moveXyCameraSatisfied or moveCameraPlaneSatisfied or rotateCameraSatisfied or zoomCameraSatisfied:
            self.editor.doCursorLock(mutableScreen=screen, centerMouse=False, doRotations=False)
            moveStrength = self.settings.moveCameraSensitivity3d / 1000
            if moveXyCameraSatisfied:
                forward = -screenDelta.y * self.renderer.scene.camera.forward()
                sideward = screenDelta.x * self.renderer.scene.camera.sideward()
                self.renderer.scene.camera.x -= (forward.x + sideward.x) * moveStrength
                self.renderer.scene.camera.y -= (forward.y + sideward.y) * moveStrength
            if moveCameraPlaneSatisfied:  # sourcery skip: extract-method
                upward = screenDelta.y * self.renderer.scene.camera.upward(ignore_xy=False)
                sideward = screenDelta.x * self.renderer.scene.camera.sideward()
                self.renderer.scene.camera.z -= (upward.z + sideward.z) * moveStrength
                self.renderer.scene.camera.y -= (upward.y + sideward.y) * moveStrength
                self.renderer.scene.camera.x -= (upward.x + sideward.x) * moveStrength
            rotateStrength = self.settings.moveCameraSensitivity3d / 10000
            if rotateCameraSatisfied:
                self.renderer.rotateCamera(-screenDelta.x * rotateStrength, screenDelta.y * rotateStrength, clampRotations=True)
            if zoomCameraSatisfied:
                self.renderer.scene.camera.distance -= screenDelta.y * rotateStrength

        # Handle movement of selected instances.
        if self.editor.ui.lockInstancesCheck.isChecked():
            return
        if self.moveXYSelected.satisfied(buttons, keys):

            if not self.editor.isDragMoving:
                self.editor.initialPositions = {instance: instance.position for instance in self.editor.selectedInstances}
                self.editor.isDragMoving = True
            for instance in self.editor.selectedInstances:
                scene = self.renderer.scene
                assert scene is not None

                x = scene.cursor.position().x
                y = scene.cursor.position().y
                z = instance.position.z if isinstance(instance, GITCamera) else scene.cursor.position().z
                instance.position = Vector3(x, y, z)

        if self.moveZSelected.satisfied(buttons, keys):
            if self.editor.ui.lockInstancesCheck.isChecked():
                return
            if not self.editor.isDragMoving:
                self.editor.initialPositions = {instance: instance.position for instance in self.editor.selectedInstances}
                self.editor.isDragMoving = True
            for instance in self.editor.selectedInstances:
                instance.position.z -= screenDelta.y / 40

        if self.rotateSelected.satisfied(buttons, keys):
            if self.editor.ui.lockInstancesCheck.isChecked():
                return
            if not self.editor.isDragRotating:
                self.editor.isDragRotating = True
                self.editor.log.debug("rotateSelected instance in 3d")
                for instance in self.editor.selectedInstances:
                    if not isinstance(instance, (GITCamera, GITCreature, GITDoor, GITPlaceable, GITStore, GITWaypoint)):
                        continue  # doesn't support rotations.
                    self.editor.initialRotations[instance] = Vector4(*instance.orientation) if isinstance(instance, GITCamera) else instance.bearing
                self.editor.log.debug("3d rotate set isDragRotating")
            self.editor.rotateSelected(screenDelta.x, screenDelta.y)

    def onMousePressed(self, screen: Vector2, buttons: set[int], keys: set[int]):
        if self.selectUnderneath.satisfied(buttons, keys):
            self.renderer.doSelect = True  # auto-selects the instance under the mouse in the paint loop, and implicitly sets this back to False

        scene = self.renderer.scene
        assert scene is not None
        if (
            self.duplicateSelected.satisfied(buttons, keys)
            and self.editor.selectedInstances
        ):
            self._duplicateSelectedInstance()
        if self.openContextMenu.satisfied(buttons, keys):
            world = Vector3(*scene.cursor.position())
            self.editor.onContextMenu(world, self.renderer.mapToGlobal(QPoint(int(screen.x), int(screen.y))))

    def onMouseReleased(
        self,
        screen: Vector2,
        buttons: set[int],
        keys: set[int],
    ):
        self.editor.handleUndoRedoFromLongActionFinished()

    def onKeyboardReleased(self, buttons: set[int], keys: set[int]):
        self.editor.handleUndoRedoFromLongActionFinished()

    def _duplicateSelectedInstance(self):  # TODO(th3w1zard1): Seems the code throughout is designed for multi-selections, yet nothing uses it. Probably disabled due to a bug or planned for later.
        instance: GITInstance = deepcopy(self.editor.selectedInstances[-1])
        if isinstance(instance, GITCamera):
            instance.camera_id = self.editor._module.git().resource()().next_camera_id()
        self.editor.log.info(f"Duplicating {instance!r}")
        self.editor.undoStack.push(DuplicateCommand(self.editor._module.git().resource()(), [instance], self.editor))  # noqa: SLF001
        vect3 = self.renderer.scene.cursor.position()
        instance.position = Vector3(vect3.x, vect3.y, vect3.z)
        #self.editor.git().add(instance)  # Handled by the undoStack above.
        self.editor.rebuildInstanceList()
        self.editor.setSelection([instance])

    def onKeyboardPressed(self, buttons: set[int], keys: set[int]):
        scene = self.renderer.scene
        assert scene is not None

        if self.toggleFreeCam.satisfied(buttons, keys):
            current_time = time.time()
            if current_time - self.editor.last_free_cam_time > 0.5:  # 0.5 seconds delay, prevents spamming
                self.editor.toggleFreeCam()
                self.editor.last_free_cam_time = current_time  # Update the last toggle time
            return

        # Check camera movement keys
        move_camera_keys = {
            "selected": self.moveCameraToSelected.satisfied(buttons, keys),
            "cursor": self.moveCameraToCursor.satisfied(buttons, keys),
            "entry": self.moveCameraToEntryPoint.satisfied(buttons, keys)
        }
        if any(move_camera_keys.values()):
            if move_camera_keys["selected"]:
                instance = next(iter(self.editor.selectedInstances), None)
                if instance is not None:
                    self.renderer.snapCameraToPoint(instance.position)
            elif move_camera_keys["cursor"]:
                scene.camera.set_position(scene.cursor.position())
            elif move_camera_keys["entry"]:
                self.editor.snapCameraToEntryLocation()
            return
        if self.deleteSelected.satisfied(buttons, keys):
            self.editor.deleteSelected()
            return
        if self.duplicateSelected.satisfied(buttons, keys):
            self._duplicateSelectedInstance()
            return
        if self.toggleInstanceLock.satisfied(buttons, keys):
            self.editor.ui.lockInstancesCheck.setChecked(not self.editor.ui.lockInstancesCheck.isChecked())

    @property
    def moveXYCamera(self):
        return ControlItem(self.settings.moveCameraXY3dBind)
    @moveXYCamera.setter
    def moveXYCamera(self, value): ...

    @property
    def moveZCamera(self):
        return ControlItem(self.settings.moveCameraZ3dBind)
    @moveZCamera.setter
    def moveZCamera(self, value): ...

    @property
    def moveCameraPlane(self):
        return ControlItem(self.settings.moveCameraPlane3dBind)
    @moveCameraPlane.setter
    def moveCameraPlane(self, value): ...

    @property
    def rotateCamera(self):
        return ControlItem(self.settings.rotateCamera3dBind)
    @rotateCamera.setter
    def rotateCamera(self, value): ...

    @property
    def zoomCamera(self):
        return ControlItem(self.settings.zoomCamera3dBind)
    @zoomCamera.setter
    def zoomCamera(self, value): ...

    @property
    def zoomCameraMM(self):
        return ControlItem(self.settings.zoomCameraMM3dBind)
    @zoomCameraMM.setter
    def zoomCameraMM(self, value): ...

    @property
    def rotateSelected(self):
        return ControlItem(self.settings.rotateSelected3dBind)
    @rotateSelected.setter
    def rotateSelected(self, value): ...

    @property
    def moveXYSelected(self):
        return ControlItem(self.settings.moveSelectedXY3dBind)
    @moveXYSelected.setter
    def moveXYSelected(self, value): ...

    @property
    def moveZSelected(self):
        return ControlItem(self.settings.moveSelectedZ3dBind)
    @moveZSelected.setter
    def moveZSelected(self, value): ...

    @property
    def selectUnderneath(self):
        return ControlItem(self.settings.selectObject3dBind)
    @selectUnderneath.setter
    def selectUnderneath(self, value): ...

    @property
    def moveCameraToSelected(self):
        return ControlItem(self.settings.moveCameraToSelected3dBind)
    @moveCameraToSelected.setter
    def moveCameraToSelected(self, value): ...

    @property
    def moveCameraToCursor(self):
        return ControlItem(self.settings.moveCameraToCursor3dBind)
    @moveCameraToCursor.setter
    def moveCameraToCursor(self, value): ...

    @property
    def moveCameraToEntryPoint(self):
        return ControlItem(self.settings.moveCameraToEntryPoint3dBind)
    @moveCameraToEntryPoint.setter
    def moveCameraToEntryPoint(self, value): ...

    @property
    def toggleFreeCam(self):
        return ControlItem(self.settings.toggleFreeCam3dBind)
    @toggleFreeCam.setter
    def toggleFreeCam(self, value): ...

    @property
    def deleteSelected(self):
        return ControlItem(self.settings.deleteObject3dBind)
    @deleteSelected.setter
    def deleteSelected(self, value): ...

    @property
    def duplicateSelected(self):
        return ControlItem(self.settings.duplicateObject3dBind)
    @duplicateSelected.setter
    def duplicateSelected(self, value): ...

    @property
    def openContextMenu(self):
        return ControlItem((set(), {BUTTON_TO_INT[Qt.MouseButton.RightButton]}))
    @openContextMenu.setter
    def openContextMenu(self, value): ...

    @property
    def rotateCameraLeft(self):
        return ControlItem(self.settings.rotateCameraLeft3dBind)
    @rotateCameraLeft.setter
    def rotateCameraLeft(self, value): ...

    @property
    def rotateCameraRight(self):
        return ControlItem(self.settings.rotateCameraRight3dBind)
    @rotateCameraRight.setter
    def rotateCameraRight(self, value): ...

    @property
    def rotateCameraUp(self):
        return ControlItem(self.settings.rotateCameraUp3dBind)
    @rotateCameraUp.setter
    def rotateCameraUp(self, value): ...

    @property
    def rotateCameraDown(self):
        return ControlItem(self.settings.rotateCameraDown3dBind)
    @rotateCameraDown.setter
    def rotateCameraDown(self, value): ...

    @property
    def moveCameraUp(self):
        return ControlItem(self.settings.moveCameraUp3dBind)
    @moveCameraUp.setter
    def moveCameraUp(self, value): ...

    @property
    def moveCameraDown(self):
        return ControlItem(self.settings.moveCameraDown3dBind)
    @moveCameraDown.setter
    def moveCameraDown(self, value): ...

    @property
    def moveCameraForward(self):
        return ControlItem(self.settings.moveCameraForward3dBind)
    @moveCameraForward.setter
    def moveCameraForward(self, value): ...

    @property
    def moveCameraBackward(self):
        return ControlItem(self.settings.moveCameraBackward3dBind)

    @moveCameraBackward.setter
    def moveCameraBackward(self, value): ...
    @property
    def moveCameraLeft(self):
        return ControlItem(self.settings.moveCameraLeft3dBind)

    @moveCameraLeft.setter
    def moveCameraLeft(self, value): ...

    @property
    def moveCameraRight(self):
        return ControlItem(self.settings.moveCameraRight3dBind)
    @moveCameraRight.setter
    def moveCameraRight(self, value): ...

    @property
    def zoomCameraIn(self):
        return ControlItem(self.settings.zoomCameraIn3dBind)

    @zoomCameraIn.setter
    def zoomCameraIn(self, value): ...
    @property
    def zoomCameraOut(self):
        return ControlItem(self.settings.zoomCameraOut3dBind)

    @zoomCameraOut.setter
    def zoomCameraOut(self, value): ...

    @property
    def toggleInstanceLock(self):
        return ControlItem(self.settings.toggleLockInstancesBind)
    @toggleInstanceLock.setter
    def toggleInstanceLock(self, value): ...

    @property
    def speedBoostControl(self):
        return ControlItem(self.settings.speedBoostCamera3dBind)
    @speedBoostControl.setter
    def speedBoostControl(self, value): ...

    @property
    def settings(self) -> ModuleDesignerSettings:
        return ModuleDesignerSettings()
    @settings.setter
    def settings(self, value): ...

    @property
    def lytGridSize(self):
        return self.settings.lytGridSize
    @lytGridSize.setter
    def lytGridSize(self, value):
        self.settings.lytGridSize = value
        if hasattr(self.editor, "lytEditor"):
            self.editor.lytEditor.setGridSize(value)

    @property
    def lytSnapToGrid(self):
        return self.settings.lytSnapToGrid
    @lytSnapToGrid.setter
    def lytSnapToGrid(self, value):
        self.settings.lytSnapToGrid = value
        if hasattr(self.editor, "lytEditor"):
            self.editor.lytEditor.setSnapToGrid(value)

    @property
    def lytShowGrid(self):
        return self.settings.lytShowGrid
    @lytShowGrid.setter
    def settings(self, value): ...


class ModuleDesignerControlsFreeCam:
    def __init__(self, editor: ModuleDesigner, renderer: ModuleRenderer):
        self.editor: ModuleDesigner = editor
        self.renderer: ModuleRenderer = renderer
        self.renderer.keysDown().clear()
        self.controls3d_distance = self.renderer.scene.camera.distance
        self.renderer.scene.camera.distance = 0
        self.renderer.setCursor(QtCore.Qt.CursorShape.BlankCursor)
        self.renderer.scene.show_cursor = False


    def onMouseScrolled(self, delta: Vector2, buttons: set[int], keys: set[int]): ...

    def onMouseMoved(self, screen: Vector2, screenDelta: Vector2, world: Vector3, buttons: set[int], keys: set[int]):  # noqa: PLR0913
        self.editor.doCursorLock(screen)

    def onMousePressed(self, screen: Vector2, buttons: set[int], keys: set[int]):
        ...

    def onMouseReleased(self, screen: Vector2, buttons: set[int], keys: set[int]): ...

    def onKeyboardPressed(self, buttons: set[int], keys: set[int]):
        current_time = time.time()
        if self.toggleFreeCam.satisfied(buttons, keys) and (current_time - self.editor.last_free_cam_time > 0.5):  # 0.5 seconds delay, prevents spamming
            #self.renderer.scene.camera.distance = self.controls3d_distance
            self.editor.toggleFreeCam()
            self.editor.last_free_cam_time = current_time  # Update the last toggle time

    def onKeyboardReleased(self, buttons: set[int], keys: set[int]): ...

    @property
    def toggleFreeCam(self):
        return ControlItem(self.settings.toggleFreeCam3dBind)
    @toggleFreeCam.setter
    def toggleFreeCam(self, value): ...

    @property
    def moveCameraUp(self):
        return ControlItem(self.settings.moveCameraUpFcBind)
    @moveCameraUp.setter
    def moveCameraUp(self, value): ...

    @property
    def moveCameraDown(self):
        return ControlItem(self.settings.moveCameraDownFcBind)
    @moveCameraDown.setter
    def moveCameraDown(self, value): ...

    @property
    def moveCameraForward(self):
        return ControlItem(self.settings.moveCameraForwardFcBind)
    @moveCameraForward.setter
    def moveCameraForward(self, value): ...

    @property
    def moveCameraBackward(self):
        return ControlItem(self.settings.moveCameraBackwardFcBind)
    @moveCameraBackward.setter
    def moveCameraBackward(self, value): ...

    @property
    def moveCameraLeft(self):
        return ControlItem(self.settings.moveCameraLeftFcBind)
    @moveCameraLeft.setter
    def moveCameraLeft(self, value): ...

    @property
    def moveCameraRight(self):
        return ControlItem(self.settings.moveCameraRightFcBind)
    @moveCameraRight.setter
    def moveCameraRight(self, value): ...

    @property
    def rotateCameraLeft(self):
        return ControlItem(self.settings.rotateCameraLeftFcBind)
    @rotateCameraLeft.setter
    def rotateCameraLeft(self, value): ...

    @property
    def rotateCameraRight(self):
        return ControlItem(self.settings.rotateCameraRightFcBind)
    @rotateCameraRight.setter
    def rotateCameraRight(self, value): ...

    @property
    def rotateCameraUp(self):
        return ControlItem(self.settings.rotateCameraUpFcBind)
    @rotateCameraUp.setter
    def rotateCameraUp(self, value): ...

    @property
    def rotateCameraDown(self):
        return ControlItem(self.settings.rotateCameraDownFcBind)
    @rotateCameraDown.setter
    def rotateCameraDown(self, value): ...

    @property
    def zoomCameraIn(self):
        return ControlItem(self.settings.zoomCameraInFcBind)

    @zoomCameraIn.setter
    def zoomCameraIn(self, value): ...
    @property
    def zoomCameraOut(self):
        return ControlItem(self.settings.zoomCameraOutFcBind)

    @zoomCameraOut.setter
    def zoomCameraOut(self, value): ...

    @property
    def speedBoostControl(self):
        return ControlItem(self.settings.speedBoostCameraFcBind)
    @speedBoostControl.setter
    def speedBoostControl(self, value): ...

    @property
    def settings(self) -> ModuleDesignerSettings:
        return ModuleDesignerSettings()
    @settings.setter
    def settings(self, value): ...


class ModuleDesignerControls2d:
    def __init__(self, editor: ModuleDesigner, renderer: WalkmeshRenderer):
        self.editor: ModuleDesigner = editor
        self.renderer: WalkmeshRenderer = renderer
        self.settings: ModuleDesignerSettings = ModuleDesignerSettings()
        self._mode: _InstanceMode | _GeometryMode | _SpawnMode

    def onMouseScrolled(self, delta: Vector2, buttons: set[int], keys: set[int]):
        if self.zoomCamera.satisfied(buttons, keys):
            if not delta.y:
                return
            sensSetting = ModuleDesignerSettings().zoomCameraSensitivity2d
            zoom_factor = calculate_zoom_strength(delta.y, sensSetting)
            self.renderer.camera.nudgeZoom(zoom_factor)

    def onMouseMoved(self, screen: Vector2, screenDelta: Vector2, world: Vector2, worldDelta: Vector2, buttons: set[int], keys: set[int]):
        shouldMoveCamera = self.moveCamera.satisfied(buttons, keys)
        shouldRotateCamera = self.rotateCamera.satisfied(buttons, keys)
        adjustedWorldDelta = worldDelta
        if shouldMoveCamera or shouldRotateCamera:
            self.renderer.doCursorLock(screen)
            adjustedWorldDelta = Vector2(-worldDelta.x, -worldDelta.y)
        if shouldMoveCamera:
            strength = self.settings.moveCameraSensitivity2d / 100
            self.renderer.camera.nudgePosition(-worldDelta.x * strength, -worldDelta.y * strength)
        if shouldRotateCamera:
            strength = self.settings.rotateCameraSensitivity2d / 100 / 50
            self.renderer.camera.nudgeRotation(screenDelta.x * strength)

        if self.editor.ui.lockInstancesCheck.isChecked():
            return
        if self.moveSelected.satisfied(buttons, keys):
            if isinstance(self._mode, _GeometryMode):
                RobustLogger().debug("Move geometry point %s, %s", worldDelta.x, worldDelta.y)
                self._mode.moveSelected(adjustedWorldDelta.x, adjustedWorldDelta.y)
                return

            # handle undo/redo for moveSelected.
            if not self.editor.isDragMoving:
                RobustLogger().debug("moveSelected instance in 2d")
                self.editor.initialPositions = {instance: instance.position for instance in self.editor.selectedInstances}
                self.editor.isDragMoving = True
            self.editor.moveSelected(adjustedWorldDelta.x, adjustedWorldDelta.y, noUndoStack=True, noZCoord=True)

        if self.rotateSelected.satisfied(buttons, keys) and isinstance(self._mode, _InstanceMode):
            if not self.editor.isDragRotating:
                self.editor.isDragRotating = True
                self.editor.log.debug("rotateSelected instance in 2d")
                selection: list[GITInstance] = self.editor.selectedInstances  # noqa: SLF001
                for instance in selection:
                    if not isinstance(instance, (GITCamera, GITCreature, GITDoor, GITPlaceable, GITStore, GITWaypoint)):
                        continue  # doesn't support rotations.
                    self.editor.initialRotations[instance] = Vector4(*instance.orientation) if isinstance(instance, GITCamera) else instance.bearing
            self._mode.rotateSelectedToPoint(world.x, world.y)

    def onMousePressed(self, screen: Vector2, buttons: set[int], keys: set[int]):
        world: Vector3 = self.renderer.toWorldCoords(screen.x, screen.y)
        if (
            self.duplicateSelected.satisfied(buttons, keys)
            and self.editor.selectedInstances
            and isinstance(self._mode, _InstanceMode)
        ):
            self._mode.duplicateSelected(world)
        if self.openContextMenu.satisfied(buttons, keys):
            self.editor.onContextMenu(world, self.renderer.mapToGlobal(QPoint(int(screen.x), int(screen.y))), isFlatRendererCall=True)

        if self.selectUnderneath.satisfied(buttons, keys):
            if isinstance(self._mode, _GeometryMode):
                RobustLogger().debug("selectUnderneathGeometry?")
                self._mode.selectUnderneath()
            elif self.renderer.instancesUnderMouse():
                RobustLogger().debug("onMousePressed, selectUnderneath found one or more instances under mouse.")
                self.editor.setSelection([self.renderer.instancesUnderMouse()[-1]])
            else:
                RobustLogger().debug("onMousePressed, selectUnderneath did not find any instances.")
                self.editor.setSelection([])

    def onKeyboardPressed(self, buttons: set[int], keys: set[int]):
        if self.deleteSelected.satisfied(buttons, keys):
            if isinstance(self._mode, _GeometryMode):
                self._mode.deleteSelected()
            else:
                self.editor.deleteSelected()
            return

        if self.snapCameraToSelected.satisfied(buttons, keys):
            for instance in self.editor.selectedInstances:
                self.renderer.snapCameraToPoint(instance.position)
                break

        if self.toggleInstanceLock.satisfied(buttons, keys):
            self.editor.ui.lockInstancesCheck.setChecked(not self.editor.ui.lockInstancesCheck.isChecked())

    def onMouseReleased(self, screen: Vector2, buttons: set[int], keys: set[int]):
        self.editor.handleUndoRedoFromLongActionFinished()

    def onKeyboardReleased(self, buttons: set[int], keys: set[int]):
        self.editor.handleUndoRedoFromLongActionFinished()

    @property
    def moveCamera(self):
        return ControlItem(self.settings.moveCamera2dBind)

    @moveCamera.setter
    def moveCamera(self, value): ...

    @property
    def rotateCamera(self):
        return ControlItem(self.settings.rotateCamera2dBind)
    @rotateCamera.setter
    def rotateCamera(self, value): ...

    @property
    def zoomCamera(self):
        return ControlItem(self.settings.zoomCamera2dBind)
    @zoomCamera.setter
    def zoomCamera(self, value): ...

    @property
    def rotateSelected(self):
        return ControlItem(self.settings.rotateObject2dBind)
    @rotateSelected.setter
    def rotateSelected(self, value): ...

    @property
    def moveSelected(self):
        return ControlItem(self.settings.moveObject2dBind)
    @moveSelected.setter
    def moveSelected(self, value): ...

    @property
    def selectUnderneath(self):
        return ControlItem(self.settings.selectObject2dBind)
    @selectUnderneath.setter
    def selectUnderneath(self, value): ...

    @property
    def deleteSelected(self):
        return ControlItem(self.settings.deleteObject2dBind)
    @deleteSelected.setter
    def deleteSelected(self, value): ...

    @property
    def duplicateSelected(self):
        return ControlItem(self.settings.duplicateObject2dBind)
    @duplicateSelected.setter
    def duplicateSelected(self, value): ...

    @property
    def snapCameraToSelected(self):
        return ControlItem(self.settings.moveCameraToSelected2dBind)
    @snapCameraToSelected.setter
    def snapCameraToSelected(self, value): ...

    @property
    def openContextMenu(self):
        return ControlItem((set(), {Qt.MouseButton.RightButton}))
    @openContextMenu.setter
    def openContextMenu(self, value): ...

    @property
    def toggleInstanceLock(self):
        return ControlItem(self.settings.toggleLockInstancesBind)
    @toggleInstanceLock.setter
    def toggleInstanceLock(self, value): ...

    @property
    def lytGridSize(self):
        return self.settings.lytGridSize
    @lytGridSize.setter
    def lytGridSize(self, value):
        self.settings.lytGridSize = value
        if hasattr(self.editor, "lytEditor"):
            self.editor.lytEditor.setGridSize(value)

    @property
    def lytSnapToGrid(self):
        return self.settings.lytSnapToGrid
    @lytSnapToGrid.setter
    def lytSnapToGrid(self, value):
        self.settings.lytSnapToGrid = value
        if hasattr(self.editor, "lytEditor"):
            self.editor.lytEditor.setSnapToGrid(value)

    @property
    def lytShowGrid(self):
        return self.settings.lytShowGrid
    @lytShowGrid.setter
    def lytShowGrid(self, value): ...
