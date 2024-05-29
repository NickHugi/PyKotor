from __future__ import annotations

from typing import TYPE_CHECKING

import qtpy

from qtpy import QtCore

from pykotor.common.misc import Color
from toolset.data.settings import Settings, SettingsProperty
from toolset.gui.widgets.settings.base import SettingsWidget
from toolset.utils.misc import QtKey, QtMouse

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget

    from toolset.data.misc import Bind
    from toolset.gui.widgets.edit.color import ColorEdit
    from toolset.gui.widgets.set_bind import SetBindWidget


class ModuleDesignerWidget(SettingsWidget):
    editedSignal = QtCore.Signal()

    def __init__(self, parent: QWidget):
        """Initializes the Module Designer UI.

        Args:
        ----
            parent (QWidget): The parent widget

        Processing Logic:
        ----------------
            - Initializes settings and binds lists
            - Loads UI from module_designer
            - Sets alpha channel for material colour pickers
            - Connects reset buttons to reset methods.
        """
        super().__init__(parent)

        self.settings: ModuleDesignerSettings = ModuleDesignerSettings()

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.widgets.settings import module_designer  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.widgets.settings import module_designer  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.widgets.settings import module_designer  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.widgets.settings import module_designer  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = module_designer.Ui_Form()
        self.ui.setupUi(self)

        self.ui.undefinedMaterialColourEdit.allowAlpha = True
        self.ui.dirtMaterialColourEdit.allowAlpha = True
        self.ui.obscuringMaterialColourEdit.allowAlpha = True
        self.ui.grassMaterialColourEdit.allowAlpha = True
        self.ui.stoneMaterialColourEdit.allowAlpha = True
        self.ui.woodMaterialColourEdit.allowAlpha = True
        self.ui.waterMaterialColourEdit.allowAlpha = True
        self.ui.nonWalkMaterialColourEdit.allowAlpha = True
        self.ui.transparentMaterialColourEdit.allowAlpha = True
        self.ui.carpetMaterialColourEdit.allowAlpha = True
        self.ui.metalMaterialColourEdit.allowAlpha = True
        self.ui.puddlesMaterialColourEdit.allowAlpha = True
        self.ui.swampMaterialColourEdit.allowAlpha = True
        self.ui.mudMaterialColourEdit.allowAlpha = True
        self.ui.leavesMaterialColourEdit.allowAlpha = True
        self.ui.lavaMaterialColourEdit.allowAlpha = True
        self.ui.bottomlessPitMaterialColourEdit.allowAlpha = True
        self.ui.deepWaterMaterialColourEdit.allowAlpha = True
        self.ui.doorMaterialColourEdit.allowAlpha = True
        self.ui.nonWalkGrassMaterialColourEdit.allowAlpha = True

        self.ui.controls3dResetButton.clicked.connect(self.resetControls3d)
        self.ui.controlsFcResetButton.clicked.connect(self.resetControlsFc)
        self.ui.controls2dResetButton.clicked.connect(self.resetControls2d)
        self.ui.coloursResetButton.clicked.connect(self.resetColours)

        self.setupValues()

        # Install the event filter on all child widgets
        self.installEventFilters(self, self.noScrollEventFilter)
        #self.installEventFilters(self, self.hoverEventFilter, include_types=[QWidget])

    def _load3dBindValues(self):
        self.ui.moveCameraSensitivity3dEdit.setValue(self.settings.moveCameraSensitivity3d)
        self.ui.rotateCameraSensitivity3dEdit.setValue(self.settings.rotateCameraSensitivity3d)
        self.ui.zoomCameraSensitivity3dEdit.setValue(self.settings.zoomCameraSensitivity3d)
        self.ui.boostedMoveCameraSensitivity3dEdit.setValue(self.settings.boostedMoveCameraSensitivity3d)

        for bindEdit in [widget for widget in dir(self.ui) if "3dBindEdit" in widget]:
            bindWidget: SetBindWidget = getattr(self.ui, bindEdit)
            self._registerBind(bindWidget, bindEdit[:-4])

    def _loadFcBindValues(self):
        self.ui.flySpeedFcEdit.setValue(self.settings.flyCameraSpeedFC)
        self.ui.rotateCameraSensitivityFcEdit.setValue(self.settings.rotateCameraSensitivity3d)
        self.ui.boostedFlyCameraSpeedFCEdit.setValue(self.settings.boostedFlyCameraSpeedFC)

        for bindEdit in [widget for widget in dir(self.ui) if "FcBindEdit" in widget]:
            bindWidget: SetBindWidget = getattr(self.ui, bindEdit)
            self._registerBind(bindWidget, bindEdit[:-4])

    def _load2dBindValues(self):
        self.ui.moveCameraSensitivity2dEdit.setValue(self.settings.moveCameraSensitivity2d)
        self.ui.rotateCameraSensitivity2dEdit.setValue(self.settings.rotateCameraSensitivity2d)
        self.ui.zoomCameraSensitivity2dEdit.setValue(self.settings.zoomCameraSensitivity2d)

        for bindEdit in [widget for widget in dir(self.ui) if "2dBindEdit" in widget]:
            bindWidget: SetBindWidget = getattr(self.ui, bindEdit)
            self._registerBind(bindWidget, bindEdit[:-4])

    def _loadColourValues(self):
        for colorEdit in [widget for widget in dir(self.ui) if "ColourEdit" in widget]:
            colorWidget: ColorEdit = getattr(self.ui, colorEdit)
            self._registerColour(colorWidget, colorEdit[:-4])

    def setupValues(self):
        self.ui.fovSpin.setValue(self.settings.fieldOfView)
        self._load3dBindValues()
        self._loadFcBindValues()
        self._load2dBindValues()
        self._loadColourValues()

    def save(self):
        super().save()
        self.settings.fieldOfView = self.ui.fovSpin.value()
        self.settings.flyCameraSpeedFC = self.ui.flySpeedFcEdit.value()
        self.settings.boostedFlyCameraSpeedFC = self.ui.boostedFlyCameraSpeedFCEdit.value()

        self.settings.moveCameraSensitivity3d = self.ui.moveCameraSensitivity3dEdit.value()
        self.settings.rotateCameraSensitivity3d = self.ui.rotateCameraSensitivity3dEdit.value()
        self.settings.zoomCameraSensitivity3d = self.ui.zoomCameraSensitivity3dEdit.value()
        self.settings.boostedMoveCameraSensitivity3d = self.ui.boostedMoveCameraSensitivity3dEdit.value()

        self.settings.moveCameraSensitivity2d = self.ui.moveCameraSensitivity2dEdit.value()
        self.settings.rotateCameraSensitivity2d = self.ui.rotateCameraSensitivity2dEdit.value()
        self.settings.zoomCameraSensitivity2d = self.ui.zoomCameraSensitivity2dEdit.value()

    def resetControls3d(self):
        self.settings.resetControls3d()
        self._load3dBindValues()

    def resetControlsFc(self):
        self.settings.resetControlsFc()
        self._loadFcBindValues()

    def resetControls2d(self):
        self.settings.resetControls2d()
        self._load2dBindValues()

    def resetColours(self):
        self.settings.resetMaterialColors()
        self._loadColourValues()


class ModuleDesignerSettings(Settings):
    def __init__(self):
        super().__init__("ModuleDesigner")

    def resetControls3d(self):
        for setting in dir(self):
            if not setting.endswith(("3d", "3dBind")):
                continue
            attr_value = getattr(self.__class__, setting)
            if isinstance(attr_value, SettingsProperty):
                attr_value.reset_to_default(self)
        self.get_property("toggleLockInstancesBind").reset_to_default(self)

    def resetControls2d(self):
        for setting in dir(self):
            if not setting.endswith(("2d", "2dBind")):
                continue
            attr_value = getattr(self.__class__, setting)
            if isinstance(attr_value, SettingsProperty):
                attr_value.reset_to_default(self)

    def resetControlsFc(self):
        for setting in dir(self):
            if not setting.endswith(("FC", "FcBind")):
                continue
            attr_value = getattr(self.__class__, setting)
            if isinstance(attr_value, SettingsProperty):
                attr_value.reset_to_default(self)

    def resetMaterialColors(self):
        for setting in dir(self):
            if not setting.endswith("Colour"):
                continue
            attr_value = getattr(self.__class__, setting)
            if isinstance(attr_value, SettingsProperty):
                attr_value.reset_to_default(self)

    # region Ints/Binds (Controls - 3D)
    moveCameraSensitivity3d: SettingsProperty[int] = Settings.addSetting(
        "moveCameraSensitivity3d",
        100,
    )
    rotateCameraSensitivity3d: SettingsProperty[int] = Settings.addSetting(
        "rotateCameraSensitivity3d",
        100,
    )
    zoomCameraSensitivity3d: SettingsProperty[int] = Settings.addSetting(
        "zoomCameraSensitivity3d",
        100,
    )
    boostedMoveCameraSensitivity3d: SettingsProperty[int] = Settings.addSetting(
        "boostedMoveCameraSensitivity3d",
        250,
    )
    speedBoostCamera3dBind: SettingsProperty[Bind] = Settings.addSetting(
        "speedBoostCamera3dBind",
        ({QtKey.Key_Shift}, set()),
    )
    moveCameraXY3dBind: SettingsProperty[Bind] = Settings.addSetting(
        "moveCameraXY3dBind",
        ({QtKey.Key_Control}, {QtMouse.LeftButton}),
    )
    moveCameraZ3dBind: SettingsProperty[Bind] = Settings.addSetting(
        "moveCameraZ3dBind",
        ({QtKey.Key_Control}, set()),
    )
    moveCameraPlane3dBind: SettingsProperty[Bind] = Settings.addSetting(
        "moveCameraPlane3dBind",
        ({QtKey.Key_Control, QtKey.Key_Alt}, {QtMouse.LeftButton}),
    )
    rotateCamera3dBind: SettingsProperty[Bind] = Settings.addSetting(
        "rotateCamera3dBind",
        ({QtKey.Key_Control}, {QtMouse.MiddleButton}),
    )
    zoomCamera3dBind: SettingsProperty[Bind] = Settings.addSetting(
        "zoomCamera3dBind",
        (set(), None),
    )
    zoomCameraMM3dBind: SettingsProperty[Bind] = Settings.addSetting(
        "zoomCameraMM3dBind",
        ({QtKey.Key_Control}, {QtMouse.RightButton}),
    )
    rotateSelected3dBind: SettingsProperty[Bind] = Settings.addSetting(
        "rotateSelected3dBind",
        (set(), {QtMouse.MiddleButton}),
    )
    moveSelectedXY3dBind: SettingsProperty[Bind] = Settings.addSetting(
        "moveSelectedXY3dBind",
        (set(), {QtMouse.LeftButton}),
    )
    moveSelectedZ3dBind: SettingsProperty[Bind] = Settings.addSetting(
        "moveSelectedZ3dBind",
        ({QtKey.Key_Shift}, {QtMouse.LeftButton}),
    )
    rotateObject3dBind: SettingsProperty[Bind] = Settings.addSetting(
        "rotateObject3dBind",
        ({QtKey.Key_Alt}, {QtMouse.LeftButton}),
    )
    selectObject3dBind: SettingsProperty[Bind] = Settings.addSetting(
        "selectObject3dBind",
        (set(), {QtMouse.LeftButton}),
    )
    toggleFreeCam3dBind: SettingsProperty[Bind] = Settings.addSetting(
        "toggleFreeCam3dBind",
        ({QtKey.Key_F}, set()),
    )
    deleteObject3dBind: SettingsProperty[Bind] = Settings.addSetting(
        "deleteObject3dBind",
        ({QtKey.Key_Delete}, None),
    )
    moveCameraToSelected3dBind: SettingsProperty[Bind] = Settings.addSetting(
        "moveCameraToSelected3dBind",
        ({QtKey.Key_Z}, None),
    )
    moveCameraToCursor3dBind: SettingsProperty[Bind] = Settings.addSetting(
        "moveCameraToCursor3dBind",
        ({QtKey.Key_X}, None),
    )
    moveCameraToEntryPoint3dBind = Settings.addSetting(
        "moveCameraToEntryPoint3dBind",
        ({QtKey.Key_C}, None),
    )
    rotateCameraLeft3dBind: SettingsProperty[Bind] = Settings.addSetting(
        "rotateCameraLeft3dBind",
        ({QtKey.Key_7}, None),
    )
    rotateCameraRight3dBind: SettingsProperty[Bind] = Settings.addSetting(
        "rotateCameraRight3dBind",
        ({QtKey.Key_9}, None),
    )
    rotateCameraUp3dBind: SettingsProperty[Bind] = Settings.addSetting(
        "rotateCameraUp3dBind",
        ({QtKey.Key_1}, None),
    )
    rotateCameraDown3dBind: SettingsProperty[Bind] = Settings.addSetting(
        "rotateCameraDown3dBind",
        ({QtKey.Key_3}, None),
    )
    moveCameraBackward3dBind: SettingsProperty[Bind] = Settings.addSetting(
        "moveCameraBackward3dBind",
        ({QtKey.Key_2}, None),
    )
    moveCameraForward3dBind: SettingsProperty[Bind] = Settings.addSetting(
        "moveCameraForward3dBind",
        ({QtKey.Key_8}, None),
    )
    moveCameraLeft3dBind: SettingsProperty[Bind] = Settings.addSetting(
        "moveCameraLeft3dBind",
        ({QtKey.Key_4}, None),
    )
    moveCameraRight3dBind: SettingsProperty[Bind] = Settings.addSetting(
        "moveCameraRight3dBind",
        ({QtKey.Key_6}, None),
    )
    moveCameraUp3dBind: SettingsProperty[Bind] = Settings.addSetting(
        "moveCameraUp3dBind",
        ({QtKey.Key_Q}, None),
    )
    moveCameraDown3dBind: SettingsProperty[Bind] = Settings.addSetting(
        "moveCameraDown3dBind",
        ({QtKey.Key_E}, None),
    )
    zoomCameraIn3dBind: SettingsProperty[Bind] = Settings.addSetting(
        "zoomCameraIn3dBind",
        ({QtKey.Key_Plus}, None),
    )
    zoomCameraOut3dBind: SettingsProperty[Bind] = Settings.addSetting(
        "zoomCameraOut3dBind",
        ({QtKey.Key_Minus}, None),
    )
    duplicateObject3dBind: SettingsProperty[Bind] = Settings.addSetting(
        "duplicateObject3dBind",
        ({QtKey.Key_Alt}, {QtMouse.LeftButton}),
    )
    # endregion

    # region Int/Binds (Controls - 3D FreeCam)
    rotateCameraSensitivityFC = Settings.addSetting(
        "rotateCameraSensitivityFC",
        100,
    )
    flyCameraSpeedFC = Settings.addSetting(
        "flyCameraSpeedFC",
        100,
    )
    boostedFlyCameraSpeedFC = Settings.addSetting(
        "boostedFlyCameraSpeedFC",
        250,
    )

    speedBoostCameraFcBind: SettingsProperty[Bind] = Settings.addSetting(
        "speedBoostCameraFcBind",
        ({QtKey.Key_Shift}, set()),
    )
    moveCameraForwardFcBind: SettingsProperty[Bind] = Settings.addSetting(
        "moveCameraForwardFcBind",
        ({QtKey.Key_W}, set()),
    )
    moveCameraBackwardFcBind: SettingsProperty[Bind] = Settings.addSetting(
        "moveCameraBackwardFcBind",
        ({QtKey.Key_S}, set()),
    )
    moveCameraLeftFcBind: SettingsProperty[Bind] = Settings.addSetting(
        "moveCameraLeftFcBind",
        ({QtKey.Key_A}, set()),
    )
    moveCameraRightFcBind: SettingsProperty[Bind] = Settings.addSetting(
        "moveCameraRightFcBind",
        ({QtKey.Key_D}, set()),
    )
    moveCameraUpFcBind: SettingsProperty[Bind] = Settings.addSetting(
        "moveCameraUpFcBind",
        ({QtKey.Key_Q}, set()),
    )
    moveCameraDownFcBind: SettingsProperty[Bind] = Settings.addSetting(
        "moveCameraDownFcBind",
        ({QtKey.Key_E}, set()),
    )
    rotateCameraLeftFcBind: SettingsProperty[Bind] = Settings.addSetting(
        "rotateCameraLeftFcBind",
        ({QtKey.Key_7}, None),
    )
    rotateCameraRightFcBind: SettingsProperty[Bind] = Settings.addSetting(
        "rotateCameraRightFcBind",
        ({QtKey.Key_9}, None),
    )
    rotateCameraUpFcBind: SettingsProperty[Bind] = Settings.addSetting(
        "rotateCameraUpFcBind",
        ({QtKey.Key_1}, None),
    )
    rotateCameraDownFcBind: SettingsProperty[Bind] = Settings.addSetting(
        "rotateCameraDownFcBind",
        ({QtKey.Key_3}, None),
    )
    zoomCameraInFcBind: SettingsProperty[Bind] = Settings.addSetting(
        "zoomCameraInFcBind",
        ({QtKey.Key_Plus}, None),
    )
    zoomCameraOutFcBind: SettingsProperty[Bind] = Settings.addSetting(
        "zoomCameraOutFcBind",
        ({QtKey.Key_Minus}, None),
    )
    moveCameraToEntryPointFcBind = Settings.addSetting(
        "moveCameraToEntryPointFcBind",
        ({QtKey.Key_C}, None),
    )
    moveCameraToCursorFcBind: SettingsProperty[Bind] = Settings.addSetting(
        "moveCameraToCursorFcBind",
        ({QtKey.Key_X}, None),
    )
    # endregion

    # region Int/Binds (Controls - 2D)
    moveCameraSensitivity2d: SettingsProperty[int] = Settings.addSetting(
        "moveCameraSensitivity2d",
        100,
    )
    rotateCameraSensitivity2d: SettingsProperty[int] = Settings.addSetting(
        "rotateCameraSensitivity2d",
        100,
    )
    zoomCameraSensitivity2d: SettingsProperty[int] = Settings.addSetting(
        "zoomCameraSensitivity2d",
        100,
    )

    moveCamera2dBind: SettingsProperty[Bind] = Settings.addSetting(
        "moveCamera2dBind",
        ({QtKey.Key_Control}, {QtMouse.LeftButton}),
    )
    zoomCamera2dBind: SettingsProperty[Bind] = Settings.addSetting(
        "zoomCamera2dBind",
        ({QtKey.Key_Control}, set()),
    )
    rotateCamera2dBind: SettingsProperty[Bind] = Settings.addSetting(
        "rotateCamera2dBind",
        ({QtKey.Key_Control}, {QtMouse.MiddleButton}),
    )
    selectObject2dBind: SettingsProperty[Bind] = Settings.addSetting(
        "selectObject2dBind",
        (set(), {QtMouse.LeftButton}),
    )
    moveObject2dBind: SettingsProperty[Bind] = Settings.addSetting(
        "moveObject2dBind",
        (set(), {QtMouse.LeftButton}),
    )
    rotateObject2dBind: SettingsProperty[Bind] = Settings.addSetting(
        "rotateObject2dBind",
        (set(), {QtMouse.MiddleButton}),
    )
    deleteObject2dBind: SettingsProperty[Bind] = Settings.addSetting(
        "deleteObject2dBind",
        ({QtKey.Key_Delete}, set()),
    )
    moveCameraToSelected2dBind: SettingsProperty[Bind] = Settings.addSetting(
        "snapCameraToSelected2dBind",
        ({QtKey.Key_Z}, set()),
    )
    duplicateObject2dBind: SettingsProperty[Bind] = Settings.addSetting(
        "duplicateObject2dBind",
        ({QtKey.Key_Alt}, {QtMouse.LeftButton}),
    )
    # endregion

    # region Binds (Controls - Both)
    toggleLockInstancesBind: SettingsProperty[Bind] = Settings.addSetting(
        "toggleLockInstancesBind",
        ({QtKey.Key_L}, set()),
    )
    # endregion

    # region Ints (Material Colours)
    undefinedMaterialColour = Settings.addSetting(
        "undefinedMaterialColour",
        Color(0.400, 0.400, 0.400, 0.5).rgba_integer(),
    )
    dirtMaterialColour = Settings.addSetting(
        "dirtMaterialColour",
        Color(0.610, 0.235, 0.050, 0.5).rgba_integer(),
    )
    obscuringMaterialColour = Settings.addSetting(
        "obscuringMaterialColour",
        Color(0.100, 0.100, 0.100, 0.5).rgba_integer(),
    )
    grassMaterialColour = Settings.addSetting(
        "grassMaterialColour",
        Color(0.000, 0.600, 0.000, 0.5).rgba_integer(),
    )
    stoneMaterialColour = Settings.addSetting(
        "stoneMaterialColour",
        Color(0.162, 0.216, 0.279, 0.5).rgba_integer(),
    )
    woodMaterialColour = Settings.addSetting(
        "woodMaterialColour",
        Color(0.258, 0.059, 0.007, 0.5).rgba_integer(),
    )
    waterMaterialColour = Settings.addSetting(
        "waterMaterialColour",
        Color(0.000, 0.000, 1.000, 0.5).rgba_integer(),
    )
    nonWalkMaterialColour = Settings.addSetting(
        "nonWalkMaterialColour",
        Color(1.000, 0.000, 0.000, 0.5).rgba_integer(),
    )
    transparentMaterialColour = Settings.addSetting(
        "transparentMaterialColour",
        Color(1.000, 1.000, 1.000, 0.5).rgba_integer(),
    )
    carpetMaterialColour = Settings.addSetting(
        "carpetMaterialColour",
        Color(1.000, 0.000, 1.000, 0.5).rgba_integer(),
    )
    metalMaterialColour = Settings.addSetting(
        "metalMaterialColour",
        Color(0.434, 0.552, 0.730, 0.5).rgba_integer(),
    )
    puddlesMaterialColour = Settings.addSetting(
        "puddlesMaterialColour",
        Color(0.509, 0.474, 0.147, 0.5).rgba_integer(),
    )
    swampMaterialColour = Settings.addSetting(
        "swampMaterialColour",
        Color(0.216, 0.216, 0.000, 0.5).rgba_integer(),
    )
    mudMaterialColour = Settings.addSetting(
        "mudMaterialColour",
        Color(0.091, 0.147, 0.028, 0.5).rgba_integer(),
    )
    leavesMaterialColour = Settings.addSetting(
        "leavesMaterialColour",
        Color(0.000, 0.000, 0.216, 0.5).rgba_integer(),
    )
    doorMaterialColour = Settings.addSetting(
        "doorMaterialColour",
        Color(0.000, 0.000, 0.000, 0.5).rgba_integer(),
    )
    lavaMaterialColour = Settings.addSetting(
        "lavaMaterialColour",
        Color(0.300, 0.000, 0.000, 0.5).rgba_integer(),
    )
    bottomlessPitMaterialColour = Settings.addSetting(
        "bottomlessPitMaterialColour",
        Color(0.000, 0.000, 0.000, 0.5).rgba_integer(),
    )
    deepWaterMaterialColour = Settings.addSetting(
        "deepWaterMaterialColour",
        Color(0.000, 0.000, 0.216, 0.5).rgba_integer(),
    )
    nonWalkGrassMaterialColour = Settings.addSetting(
        "nonWalkGrassMaterialColour",
        Color(0.000, 0.600, 0.000, 0.5).rgba_integer(),
    )
    # endregion

    # region Ints
    fieldOfView = Settings.addSetting(
        "fieldOfView",
        70,
    )
    # endregion
