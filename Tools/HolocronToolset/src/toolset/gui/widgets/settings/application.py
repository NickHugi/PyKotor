from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, ClassVar

import qtpy

from qtpy import QtCore
from qtpy.QtGui import QCursor, QFont, QGuiApplication
from qtpy.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFontDialog,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidgetItem,
    QToolTip,
)

from toolset.data.settings import Settings
from toolset.gui.widgets.settings.base import SettingsWidget
from toolset.gui.widgets.settings.env_vars import ENV_VARS, EnvVariableDialog

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget


class ApplicationSettingsWidget(SettingsWidget):
    editedSignal = QtCore.Signal()  # pyright: ignore[reportPrivateImportUsage]

    def __init__(self, parent: QWidget):
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
        self.populateAll()
        self._setupAttributes()
        self.setupFontSettings()
        self.ui.resetAttributesButton.clicked.connect(self.resetAttributes)

        # Connect environment variables table buttons
        self.ui.addButton.clicked.connect(self.addEnvironmentVariable)
        self.ui.editButton.clicked.connect(self.editEnvironmentVariable)
        self.ui.removeButton.clicked.connect(self.removeEnvironmentVariable)

        # Populate the environment variables table
        self.ui.tableWidget.doubleClicked.connect(self.editEnvironmentVariable)
        self.setupAddMenu()

    def setupFontSettings(self):
        """Setup the font selection dialog and apply selected font globally."""
        self.ui.fontButton.clicked.connect(self.selectFont)
        self.updateFontLabel()

    def updateFontLabel(self):
        """Update the label to show the current font."""
        font_string = self.settings.settings.value("GlobalFont", "")
        if font_string:
            font = QFont()
            font.fromString(font_string)
            QApplication.setFont(font)
            self.ui.currentFontLabel.setText(f"Current Font: {font.family()}, {font.pointSize()} pt")
        else:
            self.ui.currentFontLabel.setText("Current Font: Default")

    def selectFont(self):
        """Open QFontDialog to select a font."""
        current_font = QApplication.font()
        font, ok = QFontDialog.getFont(current_font, self)
        if ok:
            QApplication.setFont(font)
            self.settings.settings.setValue("GlobalFont", font.toString())
            self.updateFontLabel()

    def populateAll(self):
        """Populate the AA Settings group box with checkboxes."""
        aa_layout = self.ui.groupBoxAASettings.layout()
        for attr in dir(self.settings.__class__):
            if attr.startswith("AA_") and hasattr(QtCore.Qt.ApplicationAttribute, attr):
                if attr in self.settings.REQUIRES_RESTART:
                    checkbox = QCheckBox(attr.replace("AA_", "").replace("_", " ") + " *")
                    checkbox.setToolTip("Requires app restart!")
                else:
                    checkbox = QCheckBox(attr.replace("AA_", "").replace("_", " "))
                checkBoxName = f"{attr}CheckBox"
                checkbox.setObjectName(checkBoxName)
                attrName = checkBoxName.replace("CheckBox", "", 1)
                checkbox.setChecked(getattr(self.settings, attrName))
                checkbox.stateChanged.connect(lambda state, name=attrName: self.saveApplicationAttribute(state, name))
                aa_layout.addWidget(checkbox)  # type: ignore[arg-type]

        for key, value in self.settings.EnvironmentVariables.items():
            row_position = self.ui.tableWidget.rowCount()
            self.ui.tableWidget.insertRow(row_position)
            self.ui.tableWidget.setItem(row_position, 0, QTableWidgetItem(key))  # pyright: ignore[reportArgumentType]
            self.ui.tableWidget.setItem(row_position, 1, QTableWidgetItem(value))  # pyright: ignore[reportArgumentType]
            self.ui.tableWidget.resizeColumnsToContents()

        misc_layout = self.ui.verticalLayout_misc
        for name, setting in self.settings.MISC_SETTINGS.items():
            cur_setting_val = self.settings.settings.value(name, setting.getter(), setting.setting_type)
            if setting.setting_type == bool:
                checkbox = QCheckBox(name.replace("_", " "))
                checkbox.setChecked(cur_setting_val)
                checkbox.stateChanged.connect(lambda state, name=name: self.settings.settings.setValue(name, bool(state)))
                misc_layout.addWidget(checkbox)  # pyright: ignore[reportCallIssue, reportArgumentType]

            elif setting.setting_type == int:
                spinbox = QSpinBox()
                spinbox.setRange(0, 10000)  # Adjust the range as necessary
                spinbox.setValue(cur_setting_val)
                spinbox.valueChanged.connect(lambda value, name=name: self.settings.settings.setValue(name, value))
                label = QLabel(name.replace("_", " "))
                layout = QHBoxLayout()
                layout.addWidget(label)
                layout.addWidget(spinbox)
                misc_layout.addLayout(layout)  # pyright: ignore[reportArgumentType]

        self.ui.groupBoxMiscSettings.setLayout(misc_layout)  # pyright: ignore[reportArgumentType]
        self.updateFontLabel()

    def _setupAttributes(self):
        for attr_name in [widget for widget in dir(self.ui) if widget.endswith("CheckBox")]:
            checkbox: QCheckBox = getattr(self.ui, attr_name)
            setting_attr_name: str = attr_name.replace("CheckBox", "", 1)
            checkbox.setChecked(getattr(self.settings, setting_attr_name))
            checkbox.stateChanged.connect(lambda state, name=setting_attr_name: setattr(self.settings, name, bool(state)))

    def saveEnvironmentVariable(self, key: str, value: str):
        """Save a single environment variable to QSettings."""
        environment_variables = self.settings.EnvironmentVariables
        environment_variables[key] = value
        self.settings.EnvironmentVariables = environment_variables

    def setToDefault(self, row: int):
        """Slot to reset the value in the specified row to the default."""
        key_item = self.ui.tableWidget.item(row, 0)
        assert key_item is not None
        key = key_item.text()

        # Assuming you have a method to get the default value based on the key
        env_var = next((var for var in ENV_VARS if var.name == key), None)
        if env_var:
            self.ui.tableWidget.setItem(row, 1, QTableWidgetItem(env_var.default))  # pyright: ignore[reportArgumentType]
            self.saveEnvironmentVariable(key, env_var.default)
            self.ui.tableWidget.resizeColumnsToContents()

    def setupAddMenu(self):
        """Sets up the 'Add' menu based on the groups of EnvVars."""
        self.add_menu = QMenu(self.ui.addButton)  # pyright: ignore[reportArgumentType, reportCallIssue]
        for group in sorted({var.group for var in ENV_VARS}):
            group_menu = self.add_menu.addMenu(group)
            for env_var in filter(lambda var: var.group == group, ENV_VARS):
                action = group_menu.addAction(env_var.name)
                action.setToolTip(env_var.description)
                action.hovered.connect(lambda act=action: QToolTip.showText(QCursor.pos(), act.toolTip()))

        self.ui.addButton.setMenu(self.add_menu)  # pyright: ignore[reportArgumentType]

    def addEnvironmentVariableFromMenu(self, key: str, value: str):
        """Add an environment variable directly from the menu."""
        row_position = self.ui.tableWidget.rowCount()
        self.ui.tableWidget.insertRow(row_position)
        self.ui.tableWidget.setItem(row_position, 0, QTableWidgetItem(key))  # pyright: ignore[reportArgumentType]
        self.ui.tableWidget.setItem(row_position, 1, QTableWidgetItem(value))  # pyright: ignore[reportArgumentType]
        self.ui.tableWidget.resizeColumnsToContents()
        self.saveEnvironmentVariable(key, value)
        self.editedSignal.emit()

    def addEnvironmentVariable(self):
        """Add a new environment variable."""
        dialog = EnvVariableDialog(self)

        if dialog.exec() == QDialog.Accepted:
            key, value = dialog.get_data()
            if not key or not value:
                return

            row_position = self.ui.tableWidget.rowCount()
            self.ui.tableWidget.insertRow(row_position)
            self.ui.tableWidget.setItem(row_position, 0, QTableWidgetItem(key))  # pyright: ignore[reportArgumentType]
            self.ui.tableWidget.setItem(row_position, 1, QTableWidgetItem(value))  # pyright: ignore[reportArgumentType]

            default_button = QPushButton("Default")
            default_button.clicked.connect(lambda: self.setToDefault(row_position))
            self.ui.tableWidget.setCellWidget(row_position, 2, default_button)  # pyright: ignore[reportArgumentType]
            self.ui.tableWidget.resizeColumnsToContents()

            self.saveEnvironmentVariable(key, value)
            self.editedSignal.emit()

    def editEnvironmentVariable(self):
        """Edit the selected environment variable."""
        selected_row = self.ui.tableWidget.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Edit Variable", "Please select a variable to edit.")
            return

        key_item = self.ui.tableWidget.item(selected_row, 0)
        value_item = self.ui.tableWidget.item(selected_row, 1)
        assert key_item is not None
        assert value_item is not None

        old_key = key_item.text()
        old_value = value_item.text()

        dialog = EnvVariableDialog(self)
        dialog.set_data(old_key, old_value)

        if dialog.exec() == QDialog.Accepted:
            new_key, new_value = dialog.get_data()
            if not new_key or not new_value:
                return

            if old_key != new_key:
                self.removeEnvironmentVariableFromSettings(old_key)
                self.ui.tableWidget.setItem(selected_row, 0, QTableWidgetItem(new_key))  # Update UI with new key  # pyright: ignore[reportArgumentType]
            self.ui.tableWidget.setItem(selected_row, 1, QTableWidgetItem(new_value))  # pyright: ignore[reportArgumentType]
            self.ui.tableWidget.resizeColumnsToContents()
            self.saveEnvironmentVariable(new_key, new_value)
            self.editedSignal.emit()

    def removeEnvironmentVariableFromSettings(self, key: str):
        """Remove a single environment variable from QSettings."""
        environment_variables = self.settings.EnvironmentVariables
        if key in environment_variables:
            del environment_variables[key]
        self.settings.EnvironmentVariables = environment_variables  # Trigger saving to QSettings

    def removeEnvironmentVariable(self):
        """Remove the selected environment variable."""
        selected_row = self.ui.tableWidget.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Remove Variable", "Please select a variable to remove.")
            return

        key_item = self.ui.tableWidget.item(selected_row, 0)
        assert key_item is not None
        key = key_item.text()
        self.ui.tableWidget.removeRow(selected_row)
        self.removeEnvironmentVariableFromSettings(key)
        self.editedSignal.emit()

    def resetAttributes(self):
        for attr in [widget for widget in dir(self) if "CheckBox" in widget]:
            self._reset_and_get_default(attr[:-10])
        for name, setting in self.settings.MISC_SETTINGS.items():
            default_value = self.settings.settings.value(name, setting.getter(), setting.setting_type)
            self.settings.settings.setValue(name, default_value)
            if isinstance(default_value, bool):
                checkbox = self.findChild(QCheckBox, name)
                if checkbox:
                    checkbox.setChecked(default_value)
            elif isinstance(default_value, int):
                spinbox = self.findChild(QSpinBox, name)
                if spinbox:
                    spinbox.setValue(default_value)
        self._setupAttributes()
        self.settings.settings.remove("GlobalFont")
        QApplication.setFont(QApplication.font())  # Reset to default font
        self.updateFontLabel()

    def saveApplicationAttribute(self, state: object, attr_name: str):
        if state not in (0, 2):
            print(f"Corrupted setting: {attr_name}, cannot set state of '{state}' ({state!r}) expected a bool instead.")
            return
        setattr(self.settings, attr_name, bool(state))
        app = QApplication.instance()
        assert isinstance(app, QApplication)
        attrToSet = getattr(QtCore.Qt.ApplicationAttribute, attr_name)
        app.setAttribute(attrToSet, bool(state))


class MiscSetting:  # TODO(th3w1zard1): inherit from SettingsProperty, or absolve MiscSetting as a new feature of SettingsProperty.
    def __init__(self, getter: Callable[[], Any], setter: Callable[[Any], None], setting_type: type):
        self.getter: Callable[[], Any] = getter
        self.setter: Callable[[Any], None] = setter
        self.setting_type: type = setting_type


class ApplicationSettings(Settings):
    def __init__(self):
        super().__init__("Application")

    EnvironmentVariables = Settings.addSetting("EnvironmentVariables", {})

    MISC_SETTINGS: ClassVar[dict[str, MiscSetting]] = {
        "QuitOnLastWindowClosed": MiscSetting(QGuiApplication.quitOnLastWindowClosed, QGuiApplication.setQuitOnLastWindowClosed, bool),
        "WheelScrollLines": MiscSetting(QApplication.wheelScrollLines, QApplication.setWheelScrollLines, int),
        "DoubleClickInterval": MiscSetting(QApplication.doubleClickInterval, QApplication.setDoubleClickInterval, int),
        "CursorFlashTime": MiscSetting(QApplication.cursorFlashTime, QApplication.setCursorFlashTime, int),
        "KeyboardInputInterval": MiscSetting(QApplication.keyboardInputInterval, QApplication.setKeyboardInputInterval, int),
        "CompressHighFrequencyEvents": MiscSetting(QGuiApplication.isQuitLockEnabled, QGuiApplication.setQuitOnLastWindowClosed, bool),
    }

    # region Application Attributes
    REQUIRES_RESTART: ClassVar[dict[str, QtCore.Qt.ApplicationAttribute | None]] = {
        "AA_PluginApplication": QtCore.Qt.ApplicationAttribute.AA_PluginApplication,
        "AA_UseDesktopOpenGL": QtCore.Qt.ApplicationAttribute.AA_UseDesktopOpenGL,
        "AA_UseOpenGLES": QtCore.Qt.ApplicationAttribute.AA_UseOpenGLES,
        "AA_UseSoftwareOpenGL": QtCore.Qt.ApplicationAttribute.AA_UseSoftwareOpenGL,
        "AA_ShareOpenGLContexts": QtCore.Qt.ApplicationAttribute.AA_ShareOpenGLContexts,
        "AA_EnableHighDpiScaling": getattr(QtCore.Qt.ApplicationAttribute, "AA_EnableHighDpiScaling", None),
        "AA_DisableHighDpiScaling": getattr(QtCore.Qt.ApplicationAttribute, "AA_DisableHighDpiScaling", None),
    }

    # Note: if you see hasattr, means it is only available on certain apis (i.e. pyqt5 vs pyqt6 vs pyside6 vs pyside2)
    AA_ImmediateWidgetCreation = Settings.addSetting(
        "AA_ImmediateWidgetCreation",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_ImmediateWidgetCreation) if hasattr(QtCore.Qt.ApplicationAttribute, "AA_ImmediateWidgetCreation") else True,
    )
    AA_MSWindowsUseDirect3DByDefault = Settings.addSetting(
        "AA_MSWindowsUseDirect3DByDefault",
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_MSWindowsUseDirect3DByDefault) if hasattr(QtCore.Qt.ApplicationAttribute, "AA_MSWindowsUseDirect3DByDefault") else False,
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
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_MacPluginApplication) if hasattr(QtCore.Qt.ApplicationAttribute, "AA_MSWindowsUseDirect3DByDefault") else False,
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
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_X11InitThreads) if hasattr(QtCore.Qt.ApplicationAttribute, "AA_X11InitThreads") else False,
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
        QApplication.testAttribute(QtCore.Qt.ApplicationAttribute.AA_DisableWindowContextHelpButton) if hasattr(QtCore.Qt.ApplicationAttribute, "AA_DisableWindowContextHelpButton") else False,
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
