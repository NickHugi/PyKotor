from __future__ import annotations

from typing import TYPE_CHECKING

import qtpy

from qtpy import QtCore

from pykotor.common.misc import Color
from toolset.data.settings import Settings
from toolset.gui.common.filters import NoScrollEventFilter
from toolset.gui.widgets.settings.base import SettingsWidget
from toolset.utils.misc import QtKey, QtMouse

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget


class GITWidget(SettingsWidget):
    editedSignal = QtCore.Signal()

    def __init__(self, parent: QWidget):
        """Initializes the GIT settings widget.

        Args:
        ----
            parent (QWidget): The parent widget

        Processing Logic:
        ----------------
            - Calls the parent __init__ method
            - Initializes settings object
            - Loads UI from form
            - Sets alpha channel allowed for colour pickers
            - Connects reset buttons to methods
            - Calls setupValues method.
        """
        super().__init__(parent)

        self.settings: GITSettings = GITSettings()

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.widgets.settings.git import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.widgets.settings.git import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.widgets.settings.git import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.widgets.settings.git import Ui_Form  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_Form()
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

        self.ui.coloursResetButton.clicked.connect(self.resetColours)
        self.ui.controlsResetButton.clicked.connect(self.resetControls)

        self.setupValues()

        # Install the event filter on all child widgets
        self.noScrollEventFilter: NoScrollEventFilter = NoScrollEventFilter(self)
        self.installEventFilters(self, self.noScrollEventFilter)

    def _setupColourValues(self):
        for colorEdit in [widget for widget in dir(self.ui) if "ColourEdit" in widget]:
            self._registerColour(getattr(self.ui, colorEdit), colorEdit[:-4])

    def _setupBindValues(self):
        for bindEdit in [widget for widget in dir(self.ui) if "BindEdit" in widget]:
            self._registerBind(getattr(self.ui, bindEdit), bindEdit[:-4])

    def setupValues(self):
        self._setupColourValues()
        self._setupBindValues()

    def resetColours(self):
        self.settings.resetMaterialColors()
        self._setupColourValues()

    def resetControls(self):
        self.settings.resetControls()
        self._setupBindValues()


class GITSettings(Settings):
    def __init__(self):
        super().__init__("GITEditor")

    def resetMaterialColors(self):
        for setting in dir(self):
            if setting.endswith("Colour"):
                self.reset_setting(setting)

    def resetControls(self):
        for setting in dir(self):
            if setting.endswith("Bind"):
                self.reset_setting(setting)

    # region Strings (Instance Labels)
    creatureLabel = Settings.addSetting(
        "creatureLabel",
        "",
    )
    doorLabel = Settings.addSetting(
        "doorLabel",
        "",
    )
    placeableLabel = Settings.addSetting(
        "placeableLabel",
        "",
    )
    storeLabel = Settings.addSetting(
        "storeLabel",
        "",
    )
    soundLabel = Settings.addSetting(
        "soundLabel",
        "",
    )
    waypointLabel = Settings.addSetting(
        "waypointLabel",
        "",
    )
    cameraLabel = Settings.addSetting(
        "cameraLabel",
        "",
    )
    encounterLabel = Settings.addSetting(
        "encounterLabel",
        "",
    )
    triggerLabel = Settings.addSetting(
        "triggerLabel",
        "",
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

    # region Binds (Controls)
    moveCameraBind = Settings.addSetting(
        "moveCameraBind",
        ({QtKey.Key_Control}, {QtMouse.LeftButton}),
    )
    rotateCameraBind = Settings.addSetting(
        "rotateCameraBind",
        ({QtKey.Key_Control}, {QtMouse.MiddleButton}),
    )
    zoomCameraBind = Settings.addSetting(
        "zoomCameraBind",
        ({QtKey.Key_Control}, set()),
    )
    rotateSelectedToPointBind = Settings.addSetting(
        "rotateSelectedToPointBind",
        (set(), {QtMouse.MiddleButton}),
    )
    moveSelectedBind = Settings.addSetting(
        "moveSelectedBind",
        (set(), {QtMouse.LeftButton}),
    )
    selectUnderneathBind = Settings.addSetting(
        "selectUnderneathBind",
        (set(), {QtMouse.LeftButton}),
    )
    deleteSelectedBind = Settings.addSetting(
        "deleteSelectedBind",
        ({QtKey.Key_Delete}, None),
    )
    duplicateSelectedBind = Settings.addSetting(
        "duplicateSelectedBind",
        ({QtKey.Key_Alt}, {QtMouse.LeftButton}),
    )
    toggleLockInstancesBind = Settings.addSetting(
        "toggleLockInstancesBind",
        ({QtKey.Key_L}, set()),
    )
    # endregion
