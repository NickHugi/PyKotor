from __future__ import annotations

from typing import TYPE_CHECKING

import qtpy

from qtpy import QtCore
from qtpy.QtWidgets import QCheckBox, QVBoxLayout

from toolset.data.settings import Settings
from toolset.gui.widgets.settings.base import SettingsWidget
from utility.system.path import Path

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
        self.ui.resetCacheSettingsButton.clicked.connect(self.resetCacheSettings)
        self.ui.resetEnvironmentVariablesButton.clicked.connect(self.resetEnvironmentVariables)
        self.ui.resetFilePathsButton.clicked.connect(self.resetFilePaths)
        self.ui.resetPerformanceSettingsButton.clicked.connect(self.resetPerformanceSettings)

    def populateAAGrpBox(self):
        """Populate the AA Settings group box with checkboxes."""
        aa_layout = self.ui.groupBoxAASettings.layout() or QVBoxLayout(self.ui.groupBoxAASettings)
        for attr, value in ApplicationSettings.__dict__.items():
            if attr.startswith("AA_"):
                checkbox = QCheckBox(attr.replace("AA_", "").replace("_", " "))
                checkbox.setObjectName(attr + "CheckBox")
                aa_layout.addWidget(checkbox)
                self._registercheckbox(checkbox, attr + "CheckBox")
        self.ui.groupBoxAASettings.setLayout(aa_layout)

    def setupValues(self):
        """Set up the initial values for the settings."""
        self._setupAttributes()
        self._setupCacheSettings()
        self._setupEnvironmentVariables()
        self._setupFilePaths()
        self._setupPerformanceSettings()

    def _setupAttributes(self):
        for attr in [widget for widget in dir(self.ui) if widget.endswith("CheckBox")]:
            checkbox: QCheckBox = getattr(self.ui, attr)
            setting_attr = attr.replace("CheckBox", "", 1)
            checkbox.setChecked(getattr(self.settings, setting_attr))
            checkbox.stateChanged.connect(lambda state, name=setting_attr: setattr(self.settings, name, bool(state)))

    def _setupCacheSettings(self):
        self.ui.cacheSizeSpinBox.setValue(self.settings.cacheSize)
        self.ui.cacheDirectoryLineEdit.setText(self.settings.cacheDirectory)

    def _setupEnvironmentVariables(self):
        self.ui.environmentVariablesListWidget.clear()
        for env_var in self.settings.customEnvVars:
            self.ui.environmentVariablesListWidget.addItem(env_var)

    def _setupFilePaths(self):
        self.ui.logFilePathLineEdit.setText(self.settings.logFilePath)
        self.ui.tempFilePathLineEdit.setText(self.settings.tempFilePath)

    def _setupPerformanceSettings(self):
        if hasattr(self.ui, "maxThreadsSpinBox") and hasattr(self.settings, "maxThreads"):
            self.ui.maxThreadsSpinBox.setValue(self.settings.maxThreads)

    def resetAttributes(self):
        for attr in [widget for widget in dir(self) if "CheckBox" in widget]:
            self.settings.reset_setting(attr[:-10])
        self._setupAttributes()

    def resetCacheSettings(self):
        self.settings.reset_setting("cacheSize")
        self.settings.reset_setting("cacheDirectory")
        self._setupCacheSettings()

    def resetEnvironmentVariables(self):
        self.settings.reset_setting("customEnvVars")
        self._setupEnvironmentVariables()

    def resetFilePaths(self):
        self.settings.reset_setting("logFilePath")
        self.settings.reset_setting("tempFilePath")
        self._setupFilePaths()

    def resetPerformanceSettings(self):
        if hasattr(self.settings, "maxThreads"):
            self.settings.reset_setting("maxThreads")
            self._setupPerformanceSettings()

    def _registercheckbox(self, widget: QCheckBox, attrName: str):
        widget.setChecked(getattr(self.settings, attrName.replace("CheckBox", "", 1)))
        widget.stateChanged.connect(lambda state, name=attrName: setattr(self.settings, name, bool(state)))

    def save(self):
        super().save()
        self.settings.cacheSize = self.ui.cacheSizeSpinBox.value()
        self.settings.cacheDirectory = self.ui.cacheDirectoryLineEdit.text()
        self.settings.customEnvVars = [self.ui.environmentVariablesListWidget.item(i).text() for i in range(self.ui.environmentVariablesListWidget.count())]
        self.settings.logFilePath = self.ui.logFilePathLineEdit.text()
        self.settings.tempFilePath = self.ui.tempFilePathLineEdit.text()
        if hasattr(self.ui, "maxThreadsSpinBox"):
            self.settings.maxThreads = self.ui.maxThreadsSpinBox.value()


class ApplicationSettings(Settings):
    def __init__(self):
        super().__init__("Application")

    # region Application Attributes
    AA_ImmediateWidgetCreation = Settings.addSetting(
        "AA_ImmediateWidgetCreation",
        False,
    )
    AA_MSWindowsUseDirect3DByDefault = Settings.addSetting(
        "AA_MSWindowsUseDirect3DByDefault",
        False,
    )
    AA_DontShowIconsInMenus = Settings.addSetting(
        "AA_DontShowIconsInMenus",
        False,
    )
    AA_NativeWindows = Settings.addSetting(
        "AA_NativeWindows",
        False,
    )
    AA_DontCreateNativeWidgetSiblings = Settings.addSetting(
        "AA_DontCreateNativeWidgetSiblings",
        False,
    )
    AA_MacPluginApplication = Settings.addSetting(
        "AA_MacPluginApplication",
        False,
    )
    AA_DontUseNativeMenuBar = Settings.addSetting(
        "AA_DontUseNativeMenuBar",
        False,
    )
    AA_MacDontSwapCtrlAndMeta = Settings.addSetting(
        "AA_MacDontSwapCtrlAndMeta",
        False,
    )
    AA_X11InitThreads = Settings.addSetting(
        "AA_X11InitThreads",
        False,
    )
    AA_Use96Dpi = Settings.addSetting(
        "AA_Use96Dpi",
        False,
    )
    AA_SynthesizeTouchForUnhandledMouseEvents = Settings.addSetting(
        "AA_SynthesizeTouchForUnhandledMouseEvents",
        False,
    )
    AA_SynthesizeMouseForUnhandledTouchEvents = Settings.addSetting(
        "AA_SynthesizeMouseForUnhandledTouchEvents",
        False,
    )
    AA_UseHighDpiPixmaps = Settings.addSetting(
        "AA_UseHighDpiPixmaps",
        False,
    )
    AA_ForceRasterWidgets = Settings.addSetting(
        "AA_ForceRasterWidgets",
        False,
    )
    AA_UseDesktopOpenGL = Settings.addSetting(
        "AA_UseDesktopOpenGL",
        False,
    )
    AA_UseOpenGLES = Settings.addSetting(
        "AA_UseOpenGLES",
        False,
    )
    AA_UseSoftwareOpenGL = Settings.addSetting(
        "AA_UseSoftwareOpenGL",
        False,
    )
    AA_ShareOpenGLContexts = Settings.addSetting(
        "AA_ShareOpenGLContexts",
        False,
    )
    AA_SetPalette = Settings.addSetting(
        "AA_SetPalette",
        False,
    )
    AA_EnableHighDpiScaling = Settings.addSetting(
        "AA_EnableHighDpiScaling",
        False,
    )
    AA_DisableHighDpiScaling = Settings.addSetting(
        "AA_DisableHighDpiScaling",
        False,
    )
    AA_PluginApplication = Settings.addSetting(
        "AA_PluginApplication",
        False,
    )
    AA_UseStyleSheetPropagationInWidgetStyles = Settings.addSetting(
        "AA_UseStyleSheetPropagationInWidgetStyles",
        False,
    )
    AA_DontUseNativeDialogs = Settings.addSetting(
        "AA_DontUseNativeDialogs",
        False,
    )
    AA_SynthesizeMouseForUnhandledTabletEvents = Settings.addSetting(
        "AA_SynthesizeMouseForUnhandledTabletEvents",
        False,
    )
    AA_CompressHighFrequencyEvents = Settings.addSetting(
        "AA_CompressHighFrequencyEvents",
        False,
    )
    AA_DontCheckOpenGLContextThreadAffinity = Settings.addSetting(
        "AA_DontCheckOpenGLContextThreadAffinity",
        False,
    )
    AA_DisableShaderDiskCache = Settings.addSetting(
        "AA_DisableShaderDiskCache",
        False,
    )
    AA_DontShowShortcutsInContextMenus = Settings.addSetting(
        "AA_DontShowShortcutsInContextMenus",
        False,
    )
    AA_CompressTabletEvents = Settings.addSetting(
        "AA_CompressTabletEvents",
        False,
    )
    AA_DisableWindowContextHelpButton = Settings.addSetting(
        "AA_DisableWindowContextHelpButton",
        False,
    )
    AA_DisableSessionManager = Settings.addSetting(
        "AA_DisableSessionManager",
        False,
    )
    AA_DisableNativeVirtualKeyboard = Settings.addSetting(
        "AA_DisableNativeVirtualKeyboard",
        False,
    )
    # endregion

    # region Cache Settings
    cacheSize = Settings.addSetting(
        "cacheSize",
        1024 * 1024 * 100,  # 100 MB
    )
    cacheDirectory = Settings.addSetting(
        "cacheDirectory",
        str(Path.home() / ".myapp" / "cache"),
    )
    # endregion

    # region Environment Variables
    customEnvVars = Settings.addSetting(
        "customEnvVars",
        {},
    )
    # endregion

    # region File Paths
    logFilePath = Settings.addSetting(
        "logFilePath",
        str(Path.home() / ".myapp" / "logs" / "app.log"),
    )
    tempFilePath = Settings.addSetting(
        "tempFilePath",
        str(Path.home() / ".myapp" / "temp"),
    )
    # endregion

    # region Performance Settings
    # endregion
