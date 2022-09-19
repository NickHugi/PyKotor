from typing import List, Any

from PyQt5 import QtCore
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QWidget

from data.misc import Bind
from gui.widgets.color_edit import ColorEdit
from gui.widgets.set_bind import SetBindWidget
from pykotor.common.misc import Color
from utils.misc import QtKey, QtMouse


class ModuleDesignerWidget(QWidget):
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
        self.ui.controls2dResetButton.clicked.connect(self.resetControls2d)
        self.ui.coloursResetButton.clicked.connect(self.resetColours)

        self.setupValues()

    def _setupControlValues(self) -> None:
        self.ui.moveCameraSensitivity3dEdit.setValue(self.settings.moveCameraSensitivity3d)
        self.ui.rotateCameraSensitivity3dEdit.setValue(self.settings.rotateCameraSensitivity3d)
        self.ui.zoomCameraSensitivity3dEdit.setValue(self.settings.zoomCameraSensitivity3d)

        for bindEdit in [widget for widget in dir(self.ui) if "BindEdit" in widget]:
            self._registerBind(getattr(self.ui, bindEdit), bindEdit[:-4])

        self.ui.moveCameraSensitivity2dEdit.setValue(self.settings.moveCameraSensitivity2d)
        self.ui.rotateCameraSensitivity2dEdit.setValue(self.settings.rotateCameraSensitivity2d)
        self.ui.zoomCameraSensitivity2dEdit.setValue(self.settings.zoomCameraSensitivity2d)

    def _setupColourValues(self) -> None:
        for colorEdit in [widget for widget in dir(self.ui) if "ColourEdit" in widget]:
            self._registerColour(getattr(self.ui, colorEdit), colorEdit[:-4])

    def _registerBind(self, widget: SetBindWidget, bindName: str) -> None:
        widget.setBind(getattr(self.settings, bindName))
        self.binds.append((widget, bindName))

    def _registerColour(self, widget: ColorEdit, colourName: str) -> None:
        widget.setColor(Color.from_rgba_integer(getattr(self.settings, colourName)))
        self.colours.append((widget, colourName))

    def setupValues(self) -> None:
        self.ui.fovSpin.setValue(self.settings.fieldOfView)
        self._setupControlValues()
        self._setupColourValues()

    def save(self) -> None:
        self.settings.fieldOfView = self.ui.fovSpin.value()

        for widget, bindName in self.binds:
            setattr(self.settings, bindName, widget.bind())
        for widget, colourName in self.colours:
            setattr(self.settings, colourName, widget.color().rgba_integer())

    def resetControls3d(self) -> None:
        self.settings.resetControls3d()
        self._setupControlValues()

    def resetControls2d(self) -> None:
        self.settings.resetControls2d()
        self._setupControlValues()

    def resetColours(self) -> None:
        self.settings.resetMaterialColors()
        self._setupColourValues()


class ModuleDesignerSettings:
    def __init__(self):
        self.settings = QSettings('HolocronToolset', 'ModuleDesigner')

    def resetControls3d(self) -> None:
        for setting in dir(self):
            if setting.endswith("3d"):
                self.settings.remove(setting)

    def resetControls2d(self) -> None:
        for setting in dir(self):
            if setting.endswith("2d"):
                self.settings.remove(setting)

    def resetMaterialColors(self) -> None:
        for setting in dir(self):
            if setting.endswith("Colour"):
                self.settings.remove(setting)

    @staticmethod
    def _addSetting(name: str, default: Any):
        prop = property(
            lambda this: this.settings.value(name, default),
            lambda this, val: this.settings.setValue(name, val)
        )
        return prop

    # region Ints/Binds (Controls - 3D)
    moveCameraSensitivity3d = _addSetting.__get__(object, property)(
        "moveCameraSensitivity3d",
        100
    )
    rotateCameraSensitivity3d = _addSetting.__get__(object, property)(
        "rotateCameraSensitivity3d",
        100
    )
    zoomCameraSensitivity3d = _addSetting.__get__(object, property)(
        "zoomCameraSensitivity3d",
        100
    )
    moveCameraXY3dBind = _addSetting.__get__(object, property)(
        "moveCameraXY3dBind",
        ({QtKey.Key_Control}, {QtMouse.LeftButton})
    )
    moveCameraZ3dBind = _addSetting.__get__(object, property)(
        "moveCameraZ3dBind",
        ({QtKey.Key_Control}, set())
    )
    rotateCamera3dBind = _addSetting.__get__(object, property)(
        "rotateCamera3dBind",
        ({QtKey.Key_Control}, {QtMouse.MiddleButton})
    )
    zoomCamera3dBind = _addSetting.__get__(object, property)(
        "zoomCamera3dBind",
        (set(), None)
    )
    zoomCameraMM3dBind = _addSetting.__get__(object, property)(
        "zoomCameraMM3dBind",
        ({QtKey.Key_Control}, {QtMouse.RightButton})
    )
    rotateSelected3dBind = _addSetting.__get__(object, property)(
        "rotateSelected3dBind",
        (set(), {QtMouse.MiddleButton})
    )
    moveSelectedXY3dBind = _addSetting.__get__(object, property)(
        "moveSelectedXY3dBind",
        (set(), {QtMouse.LeftButton})
    )
    moveSelectedZ3dBind = _addSetting.__get__(object, property)(
        "moveSelectedZ3dBind",
        ({QtKey.Key_Shift}, {QtMouse.LeftButton})
    )
    rotateObject3dBind = _addSetting.__get__(object, property)(
        "rotateObject3dBind",
        ({QtKey.Key_Alt}, {QtMouse.LeftButton})
    )
    selectObject3dBind = _addSetting.__get__(object, property)(
        "selectObject3dBind",
        (set(), {QtMouse.LeftButton})
    )
    moveCameraToSelected3dBind = _addSetting.__get__(object, property)(
        "moveCameraToSelected3dBind",
        ({QtKey.Key_Z}, None)
    )
    deleteObject3dBind = _addSetting.__get__(object, property)(
        "deleteObject3dBind",
        ({QtKey.Key_Delete}, None)
    )
    rotateCameraLeft3dBind = _addSetting.__get__(object, property)(
        "rotateCameraLeft3dBind",
        ({QtKey.Key_7}, None)
    )
    rotateCameraRight3dBind = _addSetting.__get__(object, property)(
        "rotateCameraRight3dBind",
        ({QtKey.Key_9}, None)
    )
    rotateCameraUp3dBind = _addSetting.__get__(object, property)(
        "rotateCameraUp3dBind",
        ({QtKey.Key_1}, None)
    )
    rotateCameraDown3dBind = _addSetting.__get__(object, property)(
        "rotateCameraDown3dBind",
        ({QtKey.Key_3}, None)
    )
    moveCameraBackward3dBind = _addSetting.__get__(object, property)(
        "moveCameraBackward3dBind",
        ({QtKey.Key_2}, None)
    )
    moveCameraForward3dBind = _addSetting.__get__(object, property)(
        "moveCameraForward3dBind",
        ({QtKey.Key_8}, None)
    )
    moveCameraLeft3dBind = _addSetting.__get__(object, property)(
        "moveCameraLeft3dBind",
        ({QtKey.Key_4}, None)
    )
    moveCameraRight3dBind = _addSetting.__get__(object, property)(
        "moveCameraRight3dBind",
        ({QtKey.Key_6}, None)
    )
    moveCameraUp3dBind = _addSetting.__get__(object, property)(
        "moveCameraUp3dBind",
        ({QtKey.Key_Q}, None)
    )
    moveCameraDown3dBind = _addSetting.__get__(object, property)(
        "moveCameraDown3dBind",
        ({QtKey.Key_E}, None)
    )
    zoomCameraIn3dBind = _addSetting.__get__(object, property)(
        "zoomCameraIn3dBind",
        ({QtKey.Key_Plus}, None)
    )
    zoomCameraOut3dBind = _addSetting.__get__(object, property)(
        "zoomCameraOut3dBind",
        ({QtKey.Key_Minus}, None)
    )
    # endregion

    # region Int/Binds (Controls - 2D)
    moveCameraSensitivity2d = _addSetting.__get__(object, property)(
        "moveCameraSensitivity2d",
        100
    )
    rotateCameraSensitivity2d = _addSetting.__get__(object, property)(
        "rotateCameraSensitivity2d",
        100
    )
    zoomCameraSensitivity2d = _addSetting.__get__(object, property)(
        "zoomCameraSensitivity2d",
        100
    )

    moveCamera2dBind = _addSetting.__get__(object, property)(
        "moveCamera2dBind",
        ({QtKey.Key_Control}, {QtMouse.LeftButton})
    )
    zoomCamera2dBind = _addSetting.__get__(object, property)(
        "zoomCamera2dBind",
        ({QtKey.Key_Control}, set())
    )
    rotateCamera2dBind = _addSetting.__get__(object, property)(
        "rotateCamera2dBind",
        ({QtKey.Key_Control}, {QtMouse.MiddleButton})
    )
    selectObject2dBind = _addSetting.__get__(object, property)(
        "selectObject2dBind",
        (set(), {QtMouse.LeftButton})
    )
    moveObject2dBind = _addSetting.__get__(object, property)(
        "moveObject2dBind",
        (set(), {QtMouse.LeftButton})
    )
    rotateObject2dBind = _addSetting.__get__(object, property)(
        "rotateObject2dBind",
        (set(), {QtMouse.MiddleButton})
    )
    deleteObject2dBind = _addSetting.__get__(object, property)(
        "deleteObject2dBind",
        ({QtKey.Key_Delete}, set())
    )
    snapCameraToSelected2dBind = _addSetting.__get__(object, property)(
        "snapCameraToSelected2dBind",
        ({QtKey.Key_Z}, set())
    )
    # endregion

    # region Ints (Material Colours)
    undefinedMaterialColour = _addSetting.__get__(object, property)(
        "undefinedMaterialColour",
        671088895
    )
    dirtMaterialColour = _addSetting.__get__(object, property)(
        "undefinedMaterialColour",
        4281084972
    )
    obscuringMaterialColour = _addSetting.__get__(object, property)(
        "obscuringMaterialColour",
        671088895
    )
    grassMaterialColour = _addSetting.__get__(object, property)(
        "grassMaterialColour",
        4281084972
    )
    stoneMaterialColour = _addSetting.__get__(object, property)(
        "stoneMaterialColour",
        4281084972
    )
    woodMaterialColour = _addSetting.__get__(object, property)(
        "woodMaterialColour",
        4281084972
    )
    waterMaterialColour = _addSetting.__get__(object, property)(
        "waterMaterialColour",
        4281084972
    )
    nonWalkMaterialColour = _addSetting.__get__(object, property)(
        "nonWalkMaterialColour",
        671088895
    )
    transparentMaterialColour = _addSetting.__get__(object, property)(
        "transparentMaterialColour",
        671088895
    )
    carpetMaterialColour = _addSetting.__get__(object, property)(
        "carpetMaterialColour",
        4281084972
    )
    metalMaterialColour = _addSetting.__get__(object, property)(
        "metalMaterialColour",
        4281084972
    )
    puddlesMaterialColour = _addSetting.__get__(object, property)(
        "puddlesMaterialColour",
        4281084972
    )
    swampMaterialColour = _addSetting.__get__(object, property)(
        "swampMaterialColour",
        4281084972
    )
    mudMaterialColour = _addSetting.__get__(object, property)(
        "mudMaterialColour",
        4281084972
    )
    leavesMaterialColour = _addSetting.__get__(object, property)(
        "leavesMaterialColour",
        4281084972
    )
    doorMaterialColour = _addSetting.__get__(object, property)(
        "doorMaterialColour",
        4281084972
    )
    lavaMaterialColour = _addSetting.__get__(object, property)(
        "lavaMaterialColour",
        671088895
    )
    bottomlessPitMaterialColour = _addSetting.__get__(object, property)(
        "bottomlessPitMaterialColour",
        671088895
    )
    deepWaterMaterialColour = _addSetting.__get__(object, property)(
        "deepWaterMaterialColour",
        671088895
    )
    nonWalkGrassMaterialColour = _addSetting.__get__(object, property)(
        "nonWalkGrassMaterialColour",
        671088895
    )
    # endregion

    # region Ints
    fieldOfView = _addSetting.__get__(object, property)(
        "fieldOfView",
        70
    )
    # endregion

