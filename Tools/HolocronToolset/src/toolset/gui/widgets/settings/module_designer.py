from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy import QtCore

from toolset.data.settings import Settings
from toolset.gui.widgets.settings.base import SettingsWidget
from toolset.utils.misc import QtKey, QtMouse

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget


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
        self.binds: list = []
        self.colours: list = []

        from toolset.uic.pyqt5.widgets.settings import module_designer

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

    def _load3dBindValues(self):
        self.ui.moveCameraSensitivity3dEdit.setValue(self.settings.moveCameraSensitivity3d)
        self.ui.rotateCameraSensitivity3dEdit.setValue(self.settings.rotateCameraSensitivity3d)
        self.ui.zoomCameraSensitivity3dEdit.setValue(self.settings.zoomCameraSensitivity3d)

        for bindEdit in [widget for widget in dir(self.ui) if "3dBindEdit" in widget]:
            self._registerBind(getattr(self.ui, bindEdit), bindEdit[:-4])

    def _loadFcBindValues(self):
        self.ui.flySpeedFcEdit.setValue(self.settings.flyCameraSpeedFC)
        self.ui.rotateCameraSensitivityFcEdit.setValue(self.settings.rotateCameraSensitivity3d)

        for bindEdit in [widget for widget in dir(self.ui) if "FcBindEdit" in widget]:
            self._registerBind(getattr(self.ui, bindEdit), bindEdit[:-4])

    def _load2dBindValues(self):
        self.ui.moveCameraSensitivity2dEdit.setValue(self.settings.moveCameraSensitivity2d)
        self.ui.rotateCameraSensitivity2dEdit.setValue(self.settings.rotateCameraSensitivity2d)
        self.ui.zoomCameraSensitivity2dEdit.setValue(self.settings.zoomCameraSensitivity2d)

        for bindEdit in [widget for widget in dir(self.ui) if "2dBindEdit" in widget]:
            self._registerBind(getattr(self.ui, bindEdit), bindEdit[:-4])

    def _loadColourValues(self):
        for colorEdit in [widget for widget in dir(self.ui) if "ColourEdit" in widget]:
            self._registerColour(getattr(self.ui, colorEdit), colorEdit[:-4])

    def setupValues(self):
        self.ui.fovSpin.setValue(self.settings.fieldOfView)
        self._load3dBindValues()
        self._loadFcBindValues()
        self._load2dBindValues()
        self._loadColourValues()

    def save(self):
        self.settings.fieldOfView = self.ui.fovSpin.value()
        self.settings.zoomCameraSensitivity3d = self.ui.moveCameraSensitivity3dEdit.value()
        self.settings.rotateCameraSensitivity3d = self.ui.rotateCameraSensitivity3dEdit.value()
        self.settings.zoomCameraSensitivity3d = self.ui.zoomCameraSensitivity3dEdit.value()

        self.settings.zoomCameraSensitivity2d = self.ui.moveCameraSensitivity2dEdit.value()
        self.settings.rotateCameraSensitivity2d = self.ui.rotateCameraSensitivity2dEdit.value()
        self.settings.zoomCameraSensitivity2d = self.ui.zoomCameraSensitivity2dEdit.value()

        for widget, bindName in self.binds:
            setattr(self.settings, bindName, widget.bind())
        for widget, colourName in self.colours:
            setattr(self.settings, colourName, widget.color().rgba_integer())

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
            if setting.endswith("3d"):
                self.settings.remove(setting)
        self.settings.remove("toggleLockInstancesBind")

    def resetControlsFc(self):
        for setting in dir(self):
            if setting.endswith("Fc"):
                self.settings.remove(setting)

    def resetControls2d(self):
        for setting in dir(self):
            if setting.endswith("2d"):
                self.settings.remove(setting)

    def resetMaterialColors(self):
        for setting in dir(self):
            if setting.endswith("Colour"):
                self.settings.remove(setting)

    # region Ints/Binds (Controls - 3D)
    moveCameraSensitivity3d = Settings.addSetting(
        "moveCameraSensitivity3d",
        100,
    )
    rotateCameraSensitivity3d = Settings.addSetting(
        "rotateCameraSensitivity3d",
        100,
    )
    zoomCameraSensitivity3d = Settings.addSetting(
        "zoomCameraSensitivity3d",
        100,
    )
    moveCameraXY3dBind = Settings.addSetting(
        "moveCameraXY3dBind",
        ({QtKey.Key_Control}, {QtMouse.LeftButton}),
    )
    moveCameraZ3dBind = Settings.addSetting(
        "moveCameraZ3dBind",
        ({QtKey.Key_Control}, set()),
    )
    moveCameraPlane3dBind = Settings.addSetting(
        "moveCameraPlane3dBind",
        ({QtKey.Key_Control, QtKey.Key_Alt}, {QtMouse.LeftButton}),
    )
    rotateCamera3dBind = Settings.addSetting(
        "rotateCamera3dBind",
        ({QtKey.Key_Control}, {QtMouse.MiddleButton}),
    )
    zoomCamera3dBind = Settings.addSetting(
        "zoomCamera3dBind",
        (set(), None),
    )
    zoomCameraMM3dBind = Settings.addSetting(
        "zoomCameraMM3dBind",
        ({QtKey.Key_Control}, {QtMouse.RightButton}),
    )
    rotateSelected3dBind = Settings.addSetting(
        "rotateSelected3dBind",
        (set(), {QtMouse.MiddleButton}),
    )
    moveSelectedXY3dBind = Settings.addSetting(
        "moveSelectedXY3dBind",
        (set(), {QtMouse.LeftButton}),
    )
    moveSelectedZ3dBind = Settings.addSetting(
        "moveSelectedZ3dBind",
        ({QtKey.Key_Shift}, {QtMouse.LeftButton}),
    )
    rotateObject3dBind = Settings.addSetting(
        "rotateObject3dBind",
        ({QtKey.Key_Alt}, {QtMouse.LeftButton}),
    )
    selectObject3dBind = Settings.addSetting(
        "selectObject3dBind",
        (set(), {QtMouse.LeftButton}),
    )
    toggleFreeCam3dBind = Settings.addSetting(
        "toggleFreeCam3dBind",
        ({QtKey.Key_F}, set()),
    )
    deleteObject3dBind = Settings.addSetting(
        "deleteObject3dBind",
        ({QtKey.Key_Delete}, None),
    )
    moveCameraToSelected3dBind = Settings.addSetting(
        "moveCameraToSelected3dBind",
        ({QtKey.Key_Z}, None),
    )
    moveCameraToCursor3dBind = Settings.addSetting(
        "moveCameraToCursor3dBind",
        ({QtKey.Key_X}, None),
    )
    moveCameraToEntryPoint3dBind = Settings.addSetting(
        "moveCameraToEntryPoint3dBind",
        ({QtKey.Key_C}, None),
    )
    rotateCameraLeft3dBind = Settings.addSetting(
        "rotateCameraLeft3dBind",
        ({QtKey.Key_7}, None),
    )
    rotateCameraRight3dBind = Settings.addSetting(
        "rotateCameraRight3dBind",
        ({QtKey.Key_9}, None),
    )
    rotateCameraUp3dBind = Settings.addSetting(
        "rotateCameraUp3dBind",
        ({QtKey.Key_1}, None),
    )
    rotateCameraDown3dBind = Settings.addSetting(
        "rotateCameraDown3dBind",
        ({QtKey.Key_3}, None),
    )
    moveCameraBackward3dBind = Settings.addSetting(
        "moveCameraBackward3dBind",
        ({QtKey.Key_2}, None),
    )
    moveCameraForward3dBind = Settings.addSetting(
        "moveCameraForward3dBind",
        ({QtKey.Key_8}, None),
    )
    moveCameraLeft3dBind = Settings.addSetting(
        "moveCameraLeft3dBind",
        ({QtKey.Key_4}, None),
    )
    moveCameraRight3dBind = Settings.addSetting(
        "moveCameraRight3dBind",
        ({QtKey.Key_6}, None),
    )
    moveCameraUp3dBind = Settings.addSetting(
        "moveCameraUp3dBind",
        ({QtKey.Key_Q}, None),
    )
    moveCameraDown3dBind = Settings.addSetting(
        "moveCameraDown3dBind",
        ({QtKey.Key_E}, None),
    )
    zoomCameraIn3dBind = Settings.addSetting(
        "zoomCameraIn3dBind",
        ({QtKey.Key_Plus}, None),
    )
    zoomCameraOut3dBind = Settings.addSetting(
        "zoomCameraOut3dBind",
        ({QtKey.Key_Minus}, None),
    )
    duplicateObject3dBind = Settings.addSetting(
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
        100,
    )

    moveCameraForwardFcBind = Settings.addSetting(
        "moveCameraForwardFcBind",
        ({QtKey.Key_W}, set()),
    )
    moveCameraBackwardFcBind = Settings.addSetting(
        "moveCameraBackwardFcBind",
        ({QtKey.Key_S}, set()),
    )
    moveCameraLeftFcBind = Settings.addSetting(
        "moveCameraLeftFcBind",
        ({QtKey.Key_A}, set()),
    )
    moveCameraRightFcBind = Settings.addSetting(
        "moveCameraRightFcBind",
        ({QtKey.Key_D}, set()),
    )
    moveCameraUpFcBind = Settings.addSetting(
        "moveCameraUpFcBind",
        ({QtKey.Key_Q}, set()),
    )
    moveCameraDownFcBind = Settings.addSetting(
        "moveCameraDownFcBind",
        ({QtKey.Key_E}, set()),
    )
    boostCameraFcBind = Settings.addSetting(
        "boostCameraFcBind",
        ({QtKey.Key_Shift}, set()),
    )
    # endregion

    # region Int/Binds (Controls - 2D)
    moveCameraSensitivity2d = Settings.addSetting(
        "moveCameraSensitivity2d",
        100,
    )
    rotateCameraSensitivity2d = Settings.addSetting(
        "rotateCameraSensitivity2d",
        100,
    )
    zoomCameraSensitivity2d = Settings.addSetting(
        "zoomCameraSensitivity2d",
        100,
    )

    moveCamera2dBind = Settings.addSetting(
        "moveCamera2dBind",
        ({QtKey.Key_Control}, {QtMouse.LeftButton}),
    )
    zoomCamera2dBind = Settings.addSetting(
        "zoomCamera2dBind",
        ({QtKey.Key_Control}, set()),
    )
    rotateCamera2dBind = Settings.addSetting(
        "rotateCamera2dBind",
        ({QtKey.Key_Control}, {QtMouse.MiddleButton}),
    )
    selectObject2dBind = Settings.addSetting(
        "selectObject2dBind",
        (set(), {QtMouse.LeftButton}),
    )
    moveObject2dBind = Settings.addSetting(
        "moveObject2dBind",
        (set(), {QtMouse.LeftButton}),
    )
    rotateObject2dBind = Settings.addSetting(
        "rotateObject2dBind",
        (set(), {QtMouse.MiddleButton}),
    )
    deleteObject2dBind = Settings.addSetting(
        "deleteObject2dBind",
        ({QtKey.Key_Delete}, set()),
    )
    moveCameraToSelected2dBind = Settings.addSetting(
        "snapCameraToSelected2dBind",
        ({QtKey.Key_Z}, set()),
    )
    duplicateObject2dBind = Settings.addSetting(
        "duplicateObject2dBind",
        ({QtKey.Key_Alt}, {QtMouse.LeftButton}),
    )
    # endregion

    # region Binds (Controls - Both)
    toggleLockInstancesBind = Settings.addSetting(
        "toggleLockInstancesBind",
        ({QtKey.Key_L}, set()),
    )
    # endregion

    # region Ints (Material Colours)
    undefinedMaterialColour = Settings.addSetting(
        "undefinedMaterialColour",
        671088895,
    )
    dirtMaterialColour = Settings.addSetting(
        "dirtMaterialColour",
        4281084972,
    )
    obscuringMaterialColour = Settings.addSetting(
        "obscuringMaterialColour",
        671088895,
    )
    grassMaterialColour = Settings.addSetting(
        "grassMaterialColour",
        4281084972,
    )
    stoneMaterialColour = Settings.addSetting(
        "stoneMaterialColour",
        4281084972,
    )
    woodMaterialColour = Settings.addSetting(
        "woodMaterialColour",
        4281084972,
    )
    waterMaterialColour = Settings.addSetting(
        "waterMaterialColour",
        4281084972,
    )
    nonWalkMaterialColour = Settings.addSetting(
        "nonWalkMaterialColour",
        671088895,
    )
    transparentMaterialColour = Settings.addSetting(
        "transparentMaterialColour",
        671088895,
    )
    carpetMaterialColour = Settings.addSetting(
        "carpetMaterialColour",
        4281084972,
    )
    metalMaterialColour = Settings.addSetting(
        "metalMaterialColour",
        4281084972,
    )
    puddlesMaterialColour = Settings.addSetting(
        "puddlesMaterialColour",
        4281084972,
    )
    swampMaterialColour = Settings.addSetting(
        "swampMaterialColour",
        4281084972,
    )
    mudMaterialColour = Settings.addSetting(
        "mudMaterialColour",
        4281084972,
    )
    leavesMaterialColour = Settings.addSetting(
        "leavesMaterialColour",
        4281084972,
    )
    doorMaterialColour = Settings.addSetting(
        "doorMaterialColour",
        4281084972,
    )
    lavaMaterialColour = Settings.addSetting(
        "lavaMaterialColour",
        671088895,
    )
    bottomlessPitMaterialColour = Settings.addSetting(
        "bottomlessPitMaterialColour",
        671088895,
    )
    deepWaterMaterialColour = Settings.addSetting(
        "deepWaterMaterialColour",
        671088895,
    )
    nonWalkGrassMaterialColour = Settings.addSetting(
        "nonWalkGrassMaterialColour",
        671088895,
    )
    # endregion

    # region Ints
    fieldOfView = Settings.addSetting(
        "fieldOfView",
        70,
    )
    # endregion
