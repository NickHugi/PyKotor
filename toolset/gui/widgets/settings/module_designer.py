from typing import List, Any

from PyQt5 import QtCore
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QWidget

from data.misc import Bind
from data.settings import Settings
from gui.widgets.color_edit import ColorEdit
from gui.widgets.set_bind import SetBindWidget
from gui.widgets.settings.base import SettingsWidget
from pykotor.common.misc import Color
from utils.misc import QtKey, QtMouse


class ModuleDesignerWidget(SettingsWidget):
    editedSignal = QtCore.pyqtSignal()

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.settings: ModuleDesignerSettings = ModuleDesignerSettings()
        self.binds: List = []
        self.colours: List = []

        from toolset.uic.widgets.settings import module_designer
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

    def _load3dBindValues(self) -> None:
        self.ui.moveCameraSensitivity3dEdit.setValue(self.settings.moveCameraSensitivity3d)
        self.ui.rotateCameraSensitivity3dEdit.setValue(self.settings.rotateCameraSensitivity3d)
        self.ui.zoomCameraSensitivity3dEdit.setValue(self.settings.zoomCameraSensitivity3d)

        for bindEdit in [widget for widget in dir(self.ui) if "3dBindEdit" in widget]:
            self._registerBind(getattr(self.ui, bindEdit), bindEdit[:-4])

    def _loadFcBindValues(self) -> None:
        self.ui.flySpeedFcEdit.setValue(self.settings.flyCameraSpeedFC)
        self.ui.rotateCameraSensitivityFcEdit.setValue(self.settings.rotateCameraSensitivity3d)

        for bindEdit in [widget for widget in dir(self.ui) if "FcBindEdit" in widget]:
            self._registerBind(getattr(self.ui, bindEdit), bindEdit[:-4])

    def _load2dBindValues(self) -> None:
        self.ui.moveCameraSensitivity2dEdit.setValue(self.settings.moveCameraSensitivity2d)
        self.ui.rotateCameraSensitivity2dEdit.setValue(self.settings.rotateCameraSensitivity2d)
        self.ui.zoomCameraSensitivity2dEdit.setValue(self.settings.zoomCameraSensitivity2d)

        for bindEdit in [widget for widget in dir(self.ui) if "2dBindEdit" in widget]:
            self._registerBind(getattr(self.ui, bindEdit), bindEdit[:-4])

    def _loadColourValues(self) -> None:
        for colorEdit in [widget for widget in dir(self.ui) if "ColourEdit" in widget]:
            self._registerColour(getattr(self.ui, colorEdit), colorEdit[:-4])

    def setupValues(self) -> None:
        self.ui.fovSpin.setValue(self.settings.fieldOfView)
        self._load3dBindValues()
        self._loadFcBindValues()
        self._load2dBindValues()
        self._loadColourValues()

    def save(self) -> None:
        self.settings.fieldOfView = self.ui.fovSpin.value()

        for widget, bindName in self.binds:
            setattr(self.settings, bindName, widget.bind())
        for widget, colourName in self.colours:
            setattr(self.settings, colourName, widget.color().rgba_integer())

    def resetControls3d(self) -> None:
        self.settings.resetControls3d()
        self._load3dBindValues()

    def resetControlsFc(self) -> None:
        self.settings.resetControlsFc()
        self._loadFcBindValues()

    def resetControls2d(self) -> None:
        self.settings.resetControls2d()
        self._load2dBindValues()

    def resetColours(self) -> None:
        self.settings.resetMaterialColors()
        self._loadColourValues()


class ModuleDesignerSettings(Settings):
    def __init__(self):
        super().__init__("ModuleDesigner")

    def resetControls3d(self) -> None:
        for setting in dir(self):
            if setting.endswith("3d"):
                self.settings.remove(setting)
        self.settings.remove("toggleLockInstancesBind")

    def resetControlsFc(self) -> None:
        for setting in dir(self):
            if setting.endswith("Fc"):
                self.settings.remove(setting)

    def resetControls2d(self) -> None:
        for setting in dir(self):
            if setting.endswith("2d"):
                self.settings.remove(setting)

    def resetMaterialColors(self) -> None:
        for setting in dir(self):
            if setting.endswith("Colour"):
                self.settings.remove(setting)

    # region Ints/Binds (Controls - 3D)
    moveCameraSensitivity3d = Settings._addSetting(
        "moveCameraSensitivity3d",
        100
    )
    rotateCameraSensitivity3d = Settings._addSetting(
        "rotateCameraSensitivity3d",
        100
    )
    zoomCameraSensitivity3d = Settings._addSetting(
        "zoomCameraSensitivity3d",
        100
    )
    moveCameraXY3dBind = Settings._addSetting(
        "moveCameraXY3dBind",
        ({QtKey.Key_Control}, {QtMouse.LeftButton})
    )
    moveCameraZ3dBind = Settings._addSetting(
        "moveCameraZ3dBind",
        ({QtKey.Key_Control}, set())
    )
    moveCameraPlane3dBind = Settings._addSetting(
        "moveCameraPlane3dBind",
        ({QtKey.Key_Control, QtKey.Key_Alt}, {QtMouse.LeftButton})
    )
    rotateCamera3dBind = Settings._addSetting(
        "rotateCamera3dBind",
        ({QtKey.Key_Control}, {QtMouse.MiddleButton})
    )
    zoomCamera3dBind = Settings._addSetting(
        "zoomCamera3dBind",
        (set(), None)
    )
    zoomCameraMM3dBind = Settings._addSetting(
        "zoomCameraMM3dBind",
        ({QtKey.Key_Control}, {QtMouse.RightButton})
    )
    rotateSelected3dBind = Settings._addSetting(
        "rotateSelected3dBind",
        (set(), {QtMouse.MiddleButton})
    )
    moveSelectedXY3dBind = Settings._addSetting(
        "moveSelectedXY3dBind",
        (set(), {QtMouse.LeftButton})
    )
    moveSelectedZ3dBind = Settings._addSetting(
        "moveSelectedZ3dBind",
        ({QtKey.Key_Shift}, {QtMouse.LeftButton})
    )
    rotateObject3dBind = Settings._addSetting(
        "rotateObject3dBind",
        ({QtKey.Key_Alt}, {QtMouse.LeftButton})
    )
    selectObject3dBind = Settings._addSetting(
        "selectObject3dBind",
        (set(), {QtMouse.LeftButton})
    )
    toggleFreeCam3dBind = Settings._addSetting(
        "toggleFreeCam3dBind",
        ({QtKey.Key_F}, set())
    )
    deleteObject3dBind = Settings._addSetting(
        "deleteObject3dBind",
        ({QtKey.Key_Delete}, None)
    )
    moveCameraToSelected3dBind = Settings._addSetting(
        "moveCameraToSelected3dBind",
        ({QtKey.Key_Z}, None)
    )
    moveCameraToCursor3dBind = Settings._addSetting(
        "moveCameraToCursor3dBind",
        ({QtKey.Key_X}, None)
    )
    rotateCameraLeft3dBind = Settings._addSetting(
        "rotateCameraLeft3dBind",
        ({QtKey.Key_7}, None)
    )
    rotateCameraRight3dBind = Settings._addSetting(
        "rotateCameraRight3dBind",
        ({QtKey.Key_9}, None)
    )
    rotateCameraUp3dBind = Settings._addSetting(
        "rotateCameraUp3dBind",
        ({QtKey.Key_1}, None)
    )
    rotateCameraDown3dBind = Settings._addSetting(
        "rotateCameraDown3dBind",
        ({QtKey.Key_3}, None)
    )
    moveCameraBackward3dBind = Settings._addSetting(
        "moveCameraBackward3dBind",
        ({QtKey.Key_2}, None)
    )
    moveCameraForward3dBind = Settings._addSetting(
        "moveCameraForward3dBind",
        ({QtKey.Key_8}, None)
    )
    moveCameraLeft3dBind = Settings._addSetting(
        "moveCameraLeft3dBind",
        ({QtKey.Key_4}, None)
    )
    moveCameraRight3dBind = Settings._addSetting(
        "moveCameraRight3dBind",
        ({QtKey.Key_6}, None)
    )
    moveCameraUp3dBind = Settings._addSetting(
        "moveCameraUp3dBind",
        ({QtKey.Key_Q}, None)
    )
    moveCameraDown3dBind = Settings._addSetting(
        "moveCameraDown3dBind",
        ({QtKey.Key_E}, None)
    )
    zoomCameraIn3dBind = Settings._addSetting(
        "zoomCameraIn3dBind",
        ({QtKey.Key_Plus}, None)
    )
    zoomCameraOut3dBind = Settings._addSetting(
        "zoomCameraOut3dBind",
        ({QtKey.Key_Minus}, None)
    )
    duplicateObject3dBind = Settings._addSetting(
        "duplicateObject3dBind",
        ({QtKey.Key_Alt}, {QtMouse.LeftButton})
    )
    # endregion

    # region Int/Binds (Controls - 3D FreeCam)
    rotateCameraSensitivityFC = Settings._addSetting(
        "rotateCameraSensitivityFC",
        100
    )
    flyCameraSpeedFC = Settings._addSetting(
        "flyCameraSpeedFC",
        100
    )
    boostedFlyCameraSpeedFC = Settings._addSetting(
        "boostedFlyCameraSpeedFC",
        100
    )

    moveCameraForwardFcBind = Settings._addSetting(
        "moveCameraForwardFcBind",
        ({QtKey.Key_W}, set())
    )
    moveCameraBackwardFcBind = Settings._addSetting(
        "moveCameraBackwardFcBind",
        ({QtKey.Key_S}, set())
    )
    moveCameraLeftFcBind = Settings._addSetting(
        "moveCameraLeftFcBind",
        ({QtKey.Key_A}, set())
    )
    moveCameraRightFcBind = Settings._addSetting(
        "moveCameraRightFcBind",
        ({QtKey.Key_D}, set())
    )
    moveCameraUpFcBind = Settings._addSetting(
        "moveCameraUpFcBind",
        ({QtKey.Key_Q}, set())
    )
    moveCameraDownFcBind = Settings._addSetting(
        "moveCameraDownFcBind",
        ({QtKey.Key_E}, set())
    )
    boostCameraFcBind = Settings._addSetting(
        "boostCameraFcBind",
        ({QtKey.Key_Shift}, set())
    )
    # endregion

    # region Int/Binds (Controls - 2D)
    moveCameraSensitivity2d = Settings._addSetting(
        "moveCameraSensitivity2d",
        100
    )
    rotateCameraSensitivity2d = Settings._addSetting(
        "rotateCameraSensitivity2d",
        100
    )
    zoomCameraSensitivity2d = Settings._addSetting(
        "zoomCameraSensitivity2d",
        100
    )

    moveCamera2dBind = Settings._addSetting(
        "moveCamera2dBind",
        ({QtKey.Key_Control}, {QtMouse.LeftButton})
    )
    zoomCamera2dBind = Settings._addSetting(
        "zoomCamera2dBind",
        ({QtKey.Key_Control}, set())
    )
    rotateCamera2dBind = Settings._addSetting(
        "rotateCamera2dBind",
        ({QtKey.Key_Control}, {QtMouse.MiddleButton})
    )
    selectObject2dBind = Settings._addSetting(
        "selectObject2dBind",
        (set(), {QtMouse.LeftButton})
    )
    moveObject2dBind = Settings._addSetting(
        "moveObject2dBind",
        (set(), {QtMouse.LeftButton})
    )
    rotateObject2dBind = Settings._addSetting(
        "rotateObject2dBind",
        (set(), {QtMouse.MiddleButton})
    )
    deleteObject2dBind = Settings._addSetting(
        "deleteObject2dBind",
        ({QtKey.Key_Delete}, set())
    )
    moveCameraToSelected2dBind = Settings._addSetting(
        "snapCameraToSelected2dBind",
        ({QtKey.Key_Z}, set())
    )
    duplicateObject2dBind = Settings._addSetting(
        "duplicateObject2dBind",
        ({QtKey.Key_Alt}, {QtMouse.LeftButton})
    )
    # endregion

    # region Binds (Controls - Both)
    toggleLockInstancesBind = Settings._addSetting(
        "toggleLockInstancesBind",
        ({QtKey.Key_L}, set())
    )
    # endregion

    # region Ints (Material Colours)
    undefinedMaterialColour = Settings._addSetting(
        "undefinedMaterialColour",
        671088895
    )
    dirtMaterialColour = Settings._addSetting(
        "dirtMaterialColour",
        4281084972
    )
    obscuringMaterialColour = Settings._addSetting(
        "obscuringMaterialColour",
        671088895
    )
    grassMaterialColour = Settings._addSetting(
        "grassMaterialColour",
        4281084972
    )
    stoneMaterialColour = Settings._addSetting(
        "stoneMaterialColour",
        4281084972
    )
    woodMaterialColour = Settings._addSetting(
        "woodMaterialColour",
        4281084972
    )
    waterMaterialColour = Settings._addSetting(
        "waterMaterialColour",
        4281084972
    )
    nonWalkMaterialColour = Settings._addSetting(
        "nonWalkMaterialColour",
        671088895
    )
    transparentMaterialColour = Settings._addSetting(
        "transparentMaterialColour",
        671088895
    )
    carpetMaterialColour = Settings._addSetting(
        "carpetMaterialColour",
        4281084972
    )
    metalMaterialColour = Settings._addSetting(
        "metalMaterialColour",
        4281084972
    )
    puddlesMaterialColour = Settings._addSetting(
        "puddlesMaterialColour",
        4281084972
    )
    swampMaterialColour = Settings._addSetting(
        "swampMaterialColour",
        4281084972
    )
    mudMaterialColour = Settings._addSetting(
        "mudMaterialColour",
        4281084972
    )
    leavesMaterialColour = Settings._addSetting(
        "leavesMaterialColour",
        4281084972
    )
    doorMaterialColour = Settings._addSetting(
        "doorMaterialColour",
        4281084972
    )
    lavaMaterialColour = Settings._addSetting(
        "lavaMaterialColour",
        671088895
    )
    bottomlessPitMaterialColour = Settings._addSetting(
        "bottomlessPitMaterialColour",
        671088895
    )
    deepWaterMaterialColour = Settings._addSetting(
        "deepWaterMaterialColour",
        671088895
    )
    nonWalkGrassMaterialColour = Settings._addSetting(
        "nonWalkGrassMaterialColour",
        671088895
    )
    # endregion

    # region Ints
    fieldOfView = Settings._addSetting(
        "fieldOfView",
        70
    )
    # endregion

