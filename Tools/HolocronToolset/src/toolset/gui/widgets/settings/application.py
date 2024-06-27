from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import qtpy

from qtpy import QtCore
from qtpy.QtWidgets import QApplication, QCheckBox

from toolset.data.settings import Settings
from toolset.gui.widgets.settings.base import SettingsWidget

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget


class ApplicationSettingsWidget(SettingsWidget):
    editedSignal = QtCore.Signal()

    def __init__(self, parent: QWidget):
        """Initializes the Application settings widget.

        Args:
        ----
            parent (QWidget): The parent widget

        Processing Logic:
        ----------------
            - Calls the parent __init__ method
            - Initializes settings object
            - Creates UI programmatically
            - Connects reset buttons to methods
            - Calls setupValues method.
        """
        super().__init__(parent)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.widgets.settings.application import Ui_ApplicationSettingsWidget  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.widgets.settings.application import Ui_ApplicationSettingsWidget  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.widgets.settings.application import Ui_ApplicationSettingsWidget  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.widgets.settings.application import Ui_ApplicationSettingsWidget  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_ApplicationSettingsWidget()
        self.ui.setupUi(self)
        self.settings: ApplicationSettings = ApplicationSettings()
        self.populateAAGrpBox()
        self.setupValues()
        self.ui.resetAttributesButton.clicked.connect(self.resetAttributes)

    def populateAAGrpBox(self):
        """Populate the AA Settings group box with checkboxes."""
        aa_layout = self.ui.groupBoxAASettings.layout()
        for attr in dir(self.settings.__class__):
            if not attr.startswith("AA_"):
                continue
            if attr in self.settings.REQUIRES_RESTART:
                checkbox = QCheckBox(attr.replace("AA_", "").replace("_", " ") + " *")
                checkbox.setToolTip("Requires app restart!")
            else:
                checkbox = QCheckBox(attr.replace("AA_", "").replace("_", " "))
            checkBoxName = f"{attr}CheckBox"
            checkbox.setObjectName(checkBoxName)
            self._registercheckbox(checkbox, checkBoxName)
            aa_layout.addWidget(checkbox)  # type: ignore[arg-type]

    def setupValues(self):
        """Set up the initial values for the settings."""
        self._setupAttributes()

    def _setupAttributes(self):
        for attr_name in [widget for widget in dir(self.ui) if widget.endswith("CheckBox")]:
            checkbox: QCheckBox = getattr(self.ui, attr_name)
            setting_attr_name: str = attr_name.replace("CheckBox", "", 1)
            checkbox.setChecked(getattr(self.settings, setting_attr_name))
            checkbox.stateChanged.connect(lambda state, name=setting_attr_name: setattr(self.settings, name, bool(state)))

    def resetAttributes(self):
        for attr in [widget for widget in dir(self) if "CheckBox" in widget]:
            self._reset_and_get_default(attr[:-10])
        self._setupAttributes()

    def _registercheckbox(self, widget: QCheckBox, widgetName: str):
        attrName = widgetName.replace("CheckBox", "", 1)
        widget.setChecked(getattr(self.settings, attrName))
        widget.stateChanged.connect(lambda state, name=attrName: self.saveApplicationAttribute(state, name))

    def save(self):
        super().save()

    def saveApplicationAttribute(self, state: object, attr_name: str):
        if state not in (0, 2):
            print(f"Corrupted setting: {attr_name}, cannot set state of '{state}' ({state!r}) expected a bool instead.")
            return
        setattr(self.settings, attr_name, bool(state))
        app = QApplication.instance()
        assert isinstance(app, QApplication)
        attrToSet = getattr(QtCore.Qt.ApplicationAttribute, attr_name)
        app.setAttribute(attrToSet, bool(state))


class ApplicationSettings(Settings):
    def __init__(self):
        super().__init__("Application")

    REQUIRES_RESTART: ClassVar[dict[str, QtCore.Qt.ApplicationAttribute]] = {
        "AA_PluginApplication": QtCore.Qt.ApplicationAttribute.AA_PluginApplication,
        "AA_UseDesktopOpenGL": QtCore.Qt.ApplicationAttribute.AA_UseDesktopOpenGL,
        "AA_UseOpenGLES": QtCore.Qt.ApplicationAttribute.AA_UseOpenGLES,
        "AA_UseSoftwareOpenGL": QtCore.Qt.ApplicationAttribute.AA_UseSoftwareOpenGL,
        "AA_ShareOpenGLContexts": QtCore.Qt.ApplicationAttribute.AA_ShareOpenGLContexts,
        "AA_EnableHighDpiScaling": QtCore.Qt.ApplicationAttribute.AA_EnableHighDpiScaling,
        "AA_DisableHighDpiScaling": QtCore.Qt.ApplicationAttribute.AA_DisableHighDpiScaling,
    }

    # region Application Attributes
    AA_ImmediateWidgetCreation = Settings.addSetting(
        "AA_ImmediateWidgetCreation",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_ImmediateWidgetCreation),
    )
    AA_MSWindowsUseDirect3DByDefault = Settings.addSetting(
        "AA_MSWindowsUseDirect3DByDefault",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_MSWindowsUseDirect3DByDefault),
    )
    AA_DontShowIconsInMenus = Settings.addSetting(
        "AA_DontShowIconsInMenus",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_DontShowIconsInMenus),
    )
    AA_NativeWindows = Settings.addSetting(
        "AA_NativeWindows",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_NativeWindows),
    )
    AA_DontCreateNativeWidgetSiblings = Settings.addSetting(
        "AA_DontCreateNativeWidgetSiblings",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings),
    )
    AA_MacPluginApplication = Settings.addSetting(
        "AA_MacPluginApplication",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_MacPluginApplication),
    )
    AA_DontUseNativeMenuBar = Settings.addSetting(
        "AA_DontUseNativeMenuBar",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_DontUseNativeMenuBar),
    )
    AA_MacDontSwapCtrlAndMeta = Settings.addSetting(
        "AA_MacDontSwapCtrlAndMeta",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_MacDontSwapCtrlAndMeta),
    )
    AA_X11InitThreads = Settings.addSetting(
        "AA_X11InitThreads",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_X11InitThreads),
    )
    AA_Use96Dpi = Settings.addSetting(
        "AA_Use96Dpi",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_Use96Dpi),
    )
    AA_SynthesizeTouchForUnhandledMouseEvents = Settings.addSetting(
        "AA_SynthesizeTouchForUnhandledMouseEvents",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_SynthesizeTouchForUnhandledMouseEvents),
    )
    AA_SynthesizeMouseForUnhandledTouchEvents = Settings.addSetting(
        "AA_SynthesizeMouseForUnhandledTouchEvents",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_SynthesizeMouseForUnhandledTouchEvents),
    )
    AA_UseHighDpiPixmaps = Settings.addSetting(
        "AA_UseHighDpiPixmaps",
        True, #QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_UseHighDpiPixmaps),
    )
    AA_ForceRasterWidgets = Settings.addSetting(
        "AA_ForceRasterWidgets",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_ForceRasterWidgets),
    )
    AA_UseDesktopOpenGL = Settings.addSetting(
        "AA_UseDesktopOpenGL",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_UseDesktopOpenGL),
    )
    AA_UseOpenGLES = Settings.addSetting(
        "AA_UseOpenGLES",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_UseOpenGLES),
    )
    AA_UseSoftwareOpenGL = Settings.addSetting(
        "AA_UseSoftwareOpenGL",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_UseSoftwareOpenGL),
    )
    AA_ShareOpenGLContexts = Settings.addSetting(
        "AA_ShareOpenGLContexts",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_ShareOpenGLContexts),
    )
    AA_SetPalette = Settings.addSetting(
        "AA_SetPalette",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_SetPalette),
    )
    AA_EnableHighDpiScaling = Settings.addSetting(
        "AA_EnableHighDpiScaling",
        True,  # QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_EnableHighDpiScaling),
    )
    AA_DisableHighDpiScaling = Settings.addSetting(
        "AA_DisableHighDpiScaling",
        False, # QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_DisableHighDpiScaling),
    )
    AA_PluginApplication = Settings.addSetting(
        "AA_PluginApplication",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_PluginApplication),
    )
    AA_UseStyleSheetPropagationInWidgetStyles = Settings.addSetting(
        "AA_UseStyleSheetPropagationInWidgetStyles",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_UseStyleSheetPropagationInWidgetStyles),
    )
    AA_DontUseNativeDialogs = Settings.addSetting(
        "AA_DontUseNativeDialogs",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_DontUseNativeDialogs),
    )
    AA_SynthesizeMouseForUnhandledTabletEvents = Settings.addSetting(
        "AA_SynthesizeMouseForUnhandledTabletEvents",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_SynthesizeMouseForUnhandledTabletEvents),
    )
    AA_CompressHighFrequencyEvents = Settings.addSetting(
        "AA_CompressHighFrequencyEvents",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_CompressHighFrequencyEvents),
    )
    AA_DontCheckOpenGLContextThreadAffinity = Settings.addSetting(
        "AA_DontCheckOpenGLContextThreadAffinity",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_DontCheckOpenGLContextThreadAffinity),
    )
    AA_DisableShaderDiskCache = Settings.addSetting(
        "AA_DisableShaderDiskCache",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_DisableShaderDiskCache),
    )
    AA_DontShowShortcutsInContextMenus = Settings.addSetting(
        "AA_DontShowShortcutsInContextMenus",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_DontShowShortcutsInContextMenus),
    )
    AA_CompressTabletEvents = Settings.addSetting(
        "AA_CompressTabletEvents",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_CompressTabletEvents),
    )
    AA_DisableWindowContextHelpButton = Settings.addSetting(
        "AA_DisableWindowContextHelpButton",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_DisableWindowContextHelpButton),
    )
    AA_DisableSessionManager = Settings.addSetting(
        "AA_DisableSessionManager",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_DisableSessionManager),
    )
    AA_DisableNativeVirtualKeyboard = Settings.addSetting(
        "AA_DisableNativeVirtualKeyboard",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_DisableNativeVirtualKeyboard),
    )
    # endregion

    # region Cache Settings
    # endregion

    # region File Paths
    # endregion

    # region Performance Settings
    # endregion
