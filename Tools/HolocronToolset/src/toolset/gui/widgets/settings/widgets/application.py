from __future__ import annotations

import os

from typing import TYPE_CHECKING, Any, Callable, ClassVar

from qtpy import QtCore
from qtpy.QtCore import Qt
from qtpy.QtGui import QCursor, QFont, QGuiApplication
from qtpy.QtWidgets import QApplication, QCheckBox, QDialog, QFontDialog, QHBoxLayout, QLabel, QMenu, QMessageBox, QPushButton, QSpinBox, QTableWidgetItem, QToolTip

from toolset.data.settings import Settings
from toolset.gui.widgets.settings.widgets.base import SettingsWidget
from toolset.gui.widgets.settings.widgets.env_vars import ENV_VARS, EnvVariableDialog

if TYPE_CHECKING:
    from qtpy.QtWidgets import (
        QAction,  # pyright: ignore[reportPrivateImportUsage]
        QWidget,
    )

    from toolset.data.settings import SettingsProperty


class ApplicationSettingsWidget(SettingsWidget):
    sig_settings_edited = QtCore.Signal()  # pyright: ignore[reportPrivateImportUsage]

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        from toolset.uic.qtpy.widgets.settings.application import Ui_ApplicationSettingsWidget

        self.ui = Ui_ApplicationSettingsWidget()
        self.ui.setupUi(self)
        self.settings: ApplicationSettings = ApplicationSettings()
        self.populate_all()
        self._setup_attributes()
        self.setup_font_settings()
        self.ui.resetAttributesButton.clicked.connect(self.reset_attributes)

        # Connect environment variables table buttons
        self.ui.addButton.clicked.connect(self.add_environment_variable)
        self.ui.editButton.clicked.connect(self.edit_environment_variable)
        self.ui.removeButton.clicked.connect(self.remove_environment_variable)

        # Populate the environment variables table
        self.ui.tableWidget.doubleClicked.connect(self.edit_environment_variable)
        self.setup_add_menu()

    def setup_font_settings(self):
        """Setup the font selection dialog and apply selected font globally."""
        self.ui.fontButton.clicked.connect(self.select_font)
        self.update_font_label()

    def update_font_label(self):
        """Update the label to show the current font."""
        font_string = self.settings.settings.value("GlobalFont", "")
        if font_string:
            font = QFont()
            font.fromString(str(font_string))
            QApplication.setFont(font)
            self.ui.currentFontLabel.setText(f"Current Font: {font.family()}, {font.pointSize()} pt")
        else:
            self.ui.currentFontLabel.setText("Current Font: Default")

    def select_font(self):
        """Open QFontDialog to select a font."""
        current_font = QApplication.font()
        font, ok = QFontDialog.getFont(current_font, self)
        assert isinstance(font, QFont), f"expected {type(font).__name__} to be QFont"
        if ok:
            QApplication.setFont(font)
            self.settings.settings.setValue("GlobalFont", font.toString())
            self.update_font_label()

    def populate_all(self):
        """Populate the AA Settings group box with checkboxes."""
        aa_layout = self.ui.groupBoxAASettings.layout()
        for attr in dir(self.settings.__class__):
            if attr.startswith("AA_") and hasattr(Qt.ApplicationAttribute, attr):
                if attr in self.settings.REQUIRES_RESTART:
                    checkbox = QCheckBox(attr.replace("AA_", "").replace("_", " ") + " *")
                    checkbox.setToolTip("Requires app restart!")
                else:
                    checkbox = QCheckBox(attr.replace("AA_", "").replace("_", " "))
                checkBoxName = f"{attr}CheckBox"
                checkbox.setObjectName(checkBoxName)
                attrName = checkBoxName.replace("CheckBox", "", 1)
                checkbox.setChecked(getattr(self.settings, attrName))
                checkbox.stateChanged.connect(lambda state, name=attrName: self.save_applicatcion_attribute(state, name))
                aa_layout.addWidget(checkbox)  # type: ignore[arg-type]

        for key, value in self.settings.app_env_variables.items():
            row_position = self.ui.tableWidget.rowCount()
            self.ui.tableWidget.insertRow(row_position)
            self.ui.tableWidget.setItem(row_position, 0, QTableWidgetItem(key))  # pyright: ignore[reportArgumentType]
            self.ui.tableWidget.setItem(row_position, 1, QTableWidgetItem(value))  # pyright: ignore[reportArgumentType]
            self.ui.tableWidget.resizeColumnsToContents()

        misc_layout = self.ui.verticalLayout_misc
        for name, setting in self.settings.MISC_SETTINGS.items():
            cur_setting_val = self.settings.settings.value(name, setting.getter(), setting.setting_type)
            if setting.setting_type is bool:
                checkbox = QCheckBox(name.replace("_", " "))
                checkbox.setChecked(bool(cur_setting_val))
                checkbox.stateChanged.connect(lambda state, name=name: self.settings.settings.setValue(name, bool(state)))
                misc_layout.addWidget(checkbox)  # pyright: ignore[reportCallIssue, reportArgumentType]

            elif setting.setting_type is int:
                assert isinstance(cur_setting_val, int), f"expected {type(cur_setting_val).__name__} to be int"
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
        self.update_font_label()

    def _setup_attributes(self):
        for attr_name in [widget for widget in dir(self.ui) if widget.endswith("CheckBox")]:
            checkbox: QCheckBox = getattr(self.ui, attr_name)
            setting_attr_name: str = attr_name.replace("CheckBox", "", 1)
            checkbox.setChecked(getattr(self.settings, setting_attr_name))
            checkbox.stateChanged.connect(lambda state, name=setting_attr_name: setattr(self.settings, name, bool(state)))

    def save_environment_variable(self, key: str, value: str):
        """Save a single environment variable to QSettings."""
        environment_variables = self.settings.app_env_variables
        environment_variables[key] = value
        self.settings.app_env_variables = environment_variables

    def set_to_default(self, row: int):
        """Slot to reset the value in the specified row to the default."""
        key_item = self.ui.tableWidget.item(row, 0)
        assert key_item is not None
        key = key_item.text()

        # Assuming you have a method to get the default value based on the key
        env_var = next((var for var in ENV_VARS if var.name == key), None)
        if env_var:
            self.ui.tableWidget.setItem(row, 1, QTableWidgetItem(env_var.default))  # pyright: ignore[reportArgumentType]
            self.save_environment_variable(key, env_var.default)
            self.ui.tableWidget.resizeColumnsToContents()

    def setup_add_menu(self):
        """Sets up the 'Add' menu based on the groups of EnvVars."""
        self.add_menu = QMenu(self.ui.addButton)  # pyright: ignore[reportArgumentType, reportCallIssue]
        for group in sorted({var.group for var in ENV_VARS}):
            group_menu = self.add_menu.addMenu(group)
            for env_var in filter(lambda var: var.group == group, ENV_VARS):
                action = group_menu.addAction(env_var.name)
                action.setToolTip(env_var.description)

                def show_tooltip(act: QAction = action):
                    QToolTip.showText(QCursor.pos(), act.toolTip())

                action.hovered.connect(show_tooltip)
                action.triggered.connect(lambda _, ev=env_var: self.add_environment_variable_from_menu(ev.name, ev.default))

        self.ui.addButton.setMenu(self.add_menu)  # pyright: ignore[reportArgumentType]

    def add_environment_variable_from_menu(self, key: str, value: str):
        """Add an environment variable directly from the menu."""
        row_position = self.ui.tableWidget.rowCount()
        self.ui.tableWidget.insertRow(row_position)
        self.ui.tableWidget.setItem(row_position, 0, QTableWidgetItem(key))  # pyright: ignore[reportArgumentType]
        self.ui.tableWidget.setItem(row_position, 1, QTableWidgetItem(value))  # pyright: ignore[reportArgumentType]
        self.ui.tableWidget.resizeColumnsToContents()
        self.save_environment_variable(key, value)
        self.sig_settings_edited.emit()

    def add_environment_variable(self):
        """Add a new environment variable."""
        dialog = EnvVariableDialog(self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            key, value = dialog.get_data()
            if not key or not value:
                return

            row_position = self.ui.tableWidget.rowCount()
            self.ui.tableWidget.insertRow(row_position)
            self.ui.tableWidget.setItem(row_position, 0, QTableWidgetItem(key))  # pyright: ignore[reportArgumentType]
            self.ui.tableWidget.setItem(row_position, 1, QTableWidgetItem(value))  # pyright: ignore[reportArgumentType]

            default_button = QPushButton("Default")
            default_button.clicked.connect(lambda: self.set_to_default(row_position))
            self.ui.tableWidget.setCellWidget(row_position, 2, default_button)  # pyright: ignore[reportArgumentType]
            self.ui.tableWidget.resizeColumnsToContents()

            self.save_environment_variable(key, value)
            self.sig_settings_edited.emit()

    def edit_environment_variable(self):
        """Edit the selected environment variable."""
        selected_row = self.ui.tableWidget.currentRow()
        if selected_row < 0:
            selected_row = self.ui.tableWidget.rowCount()
            self.ui.tableWidget.insertRow(selected_row)
            key_item = QTableWidgetItem("")
            value_item = QTableWidgetItem("")
            self.ui.tableWidget.setItem(selected_row, 0, key_item)  # pyright: ignore[reportArgumentType]
            self.ui.tableWidget.setItem(selected_row, 1, value_item)  # pyright: ignore[reportArgumentType]
        else:
            key_item = self.ui.tableWidget.item(selected_row, 0)
            value_item = self.ui.tableWidget.item(selected_row, 1)
            assert key_item is not None
            assert value_item is not None

        old_key = key_item.text()
        old_value = value_item.text()

        dialog = EnvVariableDialog(self)
        dialog.set_data(old_key, old_value)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_key, new_value = dialog.get_data()
            if not new_key or not new_value:
                return

            if old_key != new_key:
                self.remove_environment_variable_from_settings(old_key)
                self.ui.tableWidget.setItem(selected_row, 0, QTableWidgetItem(new_key))  # Update UI with new key  # pyright: ignore[reportArgumentType]
            self.ui.tableWidget.setItem(selected_row, 1, QTableWidgetItem(new_value))  # pyright: ignore[reportArgumentType]
            self.ui.tableWidget.resizeColumnsToContents()
            self.save_environment_variable(new_key, new_value)
            self.sig_settings_edited.emit()

    def remove_environment_variable_from_settings(self, key: str):
        """Remove a single environment variable from QSettings."""
        if key in self.settings.app_env_variables:
            del self.settings.app_env_variables[key]
        self.settings.settings.sync()

    def remove_environment_variable(self):
        """Remove the selected environment variable."""
        selected_row = self.ui.tableWidget.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Remove Variable", "Please select a variable to remove.")
            return

        key_item = self.ui.tableWidget.item(selected_row, 0)
        assert key_item is not None
        key = key_item.text()
        self.ui.tableWidget.removeRow(selected_row)

        # Update the app_env_variables in settings
        environment_variables = self.settings.app_env_variables
        if key in environment_variables:
            del environment_variables[key]
            self.settings.app_env_variables = environment_variables

        self.sig_settings_edited.emit()

    def reset_attributes(self):
        for attr in [widget for widget in dir(self) if "CheckBox" in widget]:
            self._reset_and_get_default(attr[:-10])
        for name, setting in self.settings.MISC_SETTINGS.items():
            default_value = self.settings.settings.value(name, setting.getter(), setting.setting_type)
            self.settings.settings.setValue(name, default_value)
            if isinstance(default_value, bool):
                checkbox = self.findChild(QCheckBox, name)
                if isinstance(checkbox, QCheckBox):
                    checkbox.setChecked(default_value)
            elif isinstance(default_value, int):
                spinbox = self.findChild(QSpinBox, name)
                if isinstance(spinbox, QSpinBox):
                    spinbox.setValue(default_value)
        self._setup_attributes()
        self.settings.settings.remove("GlobalFont")
        QApplication.setFont(QApplication.font())  # Reset to default font
        self.update_font_label()

    def save_applicatcion_attribute(self, state: object, attr_name: str):
        if state not in (0, 2):
            print(f"Corrupted setting: {attr_name}, cannot set state of '{state}' ({state!r}) expected a bool instead.")
            return
        setattr(self.settings, attr_name, bool(state))
        app = QApplication.instance()
        assert isinstance(app, QApplication)
        attrToSet = getattr(Qt.ApplicationAttribute, attr_name)
        app.setAttribute(attrToSet, bool(state))


class MiscSetting:  # TODO(th3w1zard1): inherit from SettingsProperty, or absolve MiscSetting as a new feature of SettingsProperty.
    def __init__(
        self,
        getter: Callable[[], Any],
        setter: Callable[[Any], None],
        setting_type: type,
    ):
        self.getter: Callable[[], Any] = getter
        self.setter: Callable[[Any], None] = setter
        self.setting_type: type = setting_type


class ApplicationSettings(Settings):
    def __init__(self):
        super().__init__("Application")

    app_env_variables: SettingsProperty[dict[str, str]] = Settings.addSetting(
        "EnvironmentVariables", {"QT_MULTIMEDIA_PREFERRED_PLUGINS": (os.environ.get("QT_MULTIMEDIA_PREFERRED_PLUGINS", "windowsmediafoundation") if os.name == "nt" else "")}
    )

    MISC_SETTINGS: ClassVar[dict[str, MiscSetting]] = {
        "QuitOnLastWindowClosed": MiscSetting(QGuiApplication.quitOnLastWindowClosed, QGuiApplication.setQuitOnLastWindowClosed, bool),
        "WheelScrollLines": MiscSetting(QApplication.wheelScrollLines, QApplication.setWheelScrollLines, int),
        "DoubleClickInterval": MiscSetting(QApplication.doubleClickInterval, QApplication.setDoubleClickInterval, int),
        "CursorFlashTime": MiscSetting(QApplication.cursorFlashTime, QApplication.setCursorFlashTime, int),
        "KeyboardInputInterval": MiscSetting(QApplication.keyboardInputInterval, QApplication.setKeyboardInputInterval, int),
        "CompressHighFrequencyEvents": MiscSetting(QGuiApplication.isQuitLockEnabled, QGuiApplication.setQuitOnLastWindowClosed, bool),
    }

    # region Application Attributes
    REQUIRES_RESTART: ClassVar[dict[str, Qt.ApplicationAttribute | None]] = {
        "AA_PluginApplication": Qt.ApplicationAttribute.AA_PluginApplication,
        "AA_UseDesktopOpenGL": Qt.ApplicationAttribute.AA_UseDesktopOpenGL,
        "AA_UseOpenGLES": Qt.ApplicationAttribute.AA_UseOpenGLES,
        "AA_UseSoftwareOpenGL": Qt.ApplicationAttribute.AA_UseSoftwareOpenGL,
        "AA_ShareOpenGLContexts": Qt.ApplicationAttribute.AA_ShareOpenGLContexts,
        "AA_EnableHighDpiScaling": getattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling", None),
        "AA_DisableHighDpiScaling": getattr(Qt.ApplicationAttribute, "AA_DisableHighDpiScaling", None),
    }

    # Note: if you see hasattr, means it is only available on certain apis (i.e. pyqt5 vs pyqt6 vs pyside6 vs pyside2)
    AA_ImmediateWidgetCreation: SettingsProperty[bool] = Settings.addSetting(
        "AA_ImmediateWidgetCreation",
        (
            QApplication.testAttribute(Qt.ApplicationAttribute.AA_ImmediateWidgetCreation)  # pyright: ignore[reportAttributeAccessIssue]
            if hasattr(Qt.ApplicationAttribute, "AA_ImmediateWidgetCreation")
            else True
        ),
    )
    AA_MSWindowsUseDirect3DByDefault: SettingsProperty[bool] = Settings.addSetting(
        "AA_MSWindowsUseDirect3DByDefault",
        (
            QApplication.testAttribute(Qt.ApplicationAttribute.AA_MSWindowsUseDirect3DByDefault)  # pyright: ignore[reportAttributeAccessIssue]
            if hasattr(Qt.ApplicationAttribute, "AA_MSWindowsUseDirect3DByDefault")
            else False
        ),
    )
    AA_DontShowIconsInMenus: SettingsProperty[bool] = Settings.addSetting(
        "AA_DontShowIconsInMenus",
        (QApplication.testAttribute(Qt.ApplicationAttribute.AA_DontShowIconsInMenus) if hasattr(Qt.ApplicationAttribute, "AA_DontShowIconsInMenus") else False),
    )
    AA_NativeWindows: SettingsProperty[bool] = Settings.addSetting(
        "AA_NativeWindows",
        (QApplication.testAttribute(Qt.ApplicationAttribute.AA_NativeWindows) if hasattr(Qt.ApplicationAttribute, "AA_NativeWindows") else False),
    )
    AA_DontCreateNativeWidgetSiblings: SettingsProperty[bool] = Settings.addSetting(
        "AA_DontCreateNativeWidgetSiblings",
        (
            QApplication.testAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)
            if hasattr(Qt.ApplicationAttribute, "AA_DontCreateNativeWidgetSiblings")
            else False
        ),
    )
    AA_MacPluginApplication: SettingsProperty[bool] = Settings.addSetting(
        "AA_MacPluginApplication",
        (
            QApplication.testAttribute(Qt.ApplicationAttribute.AA_MacPluginApplication)  # pyright: ignore[reportAttributeAccessIssue]
            if hasattr(Qt.ApplicationAttribute, "AA_MacPluginApplication")
            else False
        ),
    )
    AA_DontUseNativeMenuBar: SettingsProperty[bool] = Settings.addSetting(
        "AA_DontUseNativeMenuBar",
        (QApplication.testAttribute(Qt.ApplicationAttribute.AA_DontUseNativeMenuBar) if hasattr(Qt.ApplicationAttribute, "AA_DontUseNativeMenuBar") else False),
    )
    AA_MacDontSwapCtrlAndMeta: SettingsProperty[bool] = Settings.addSetting(
        "AA_MacDontSwapCtrlAndMeta",
        (QApplication.testAttribute(Qt.ApplicationAttribute.AA_MacDontSwapCtrlAndMeta) if hasattr(Qt.ApplicationAttribute, "AA_MacDontSwapCtrlAndMeta") else False),
    )
    AA_X11InitThreads: SettingsProperty[bool] = Settings.addSetting(
        "AA_X11InitThreads",
        (
            QApplication.testAttribute(Qt.ApplicationAttribute.AA_X11InitThreads)  # pyright: ignore[reportAttributeAccessIssue]
            if hasattr(Qt.ApplicationAttribute, "AA_X11InitThreads")
            else False
        ),
    )
    AA_Use96Dpi: SettingsProperty[bool] = Settings.addSetting(
        "AA_Use96Dpi",
        (QApplication.testAttribute(Qt.ApplicationAttribute.AA_Use96Dpi) if hasattr(Qt.ApplicationAttribute, "AA_Use96Dpi") else False),
    )
    AA_SynthesizeTouchForUnhandledMouseEvents: SettingsProperty[bool] = Settings.addSetting(
        "AA_SynthesizeTouchForUnhandledMouseEvents",
        (
            QApplication.testAttribute(Qt.ApplicationAttribute.AA_SynthesizeTouchForUnhandledMouseEvents)
            if hasattr(Qt.ApplicationAttribute, "AA_SynthesizeTouchForUnhandledMouseEvents")
            else False
        ),
    )
    AA_SynthesizeMouseForUnhandledTouchEvents: SettingsProperty[bool] = Settings.addSetting(
        "AA_SynthesizeMouseForUnhandledTouchEvents",
        (
            QApplication.testAttribute(Qt.ApplicationAttribute.AA_SynthesizeMouseForUnhandledTouchEvents)
            if hasattr(Qt.ApplicationAttribute, "AA_SynthesizeMouseForUnhandledTouchEvents")
            else False
        ),
    )
    AA_UseHighDpiPixmaps: SettingsProperty[bool] = Settings.addSetting(
        "AA_UseHighDpiPixmaps",
        (
            QApplication.testAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)  # pyright: ignore[reportAttributeAccessIssue]
            if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps")
            else True
        ),
    )
    AA_ForceRasterWidgets: SettingsProperty[bool] = Settings.addSetting(
        "AA_ForceRasterWidgets",
        (QApplication.testAttribute(Qt.ApplicationAttribute.AA_ForceRasterWidgets) if hasattr(Qt.ApplicationAttribute, "AA_ForceRasterWidgets") else False),
    )
    AA_UseDesktopOpenGL: SettingsProperty[bool] = Settings.addSetting(
        "AA_UseDesktopOpenGL",
        (QApplication.testAttribute(Qt.ApplicationAttribute.AA_UseDesktopOpenGL) if hasattr(Qt.ApplicationAttribute, "AA_UseDesktopOpenGL") else False),
    )
    AA_UseOpenGLES: SettingsProperty[bool] = Settings.addSetting(
        "AA_UseOpenGLES",
        (QApplication.testAttribute(Qt.ApplicationAttribute.AA_UseOpenGLES) if hasattr(Qt.ApplicationAttribute, "AA_UseOpenGLES") else False),
    )
    AA_UseSoftwareOpenGL: SettingsProperty[bool] = Settings.addSetting(
        "AA_UseSoftwareOpenGL",
        (QApplication.testAttribute(Qt.ApplicationAttribute.AA_UseSoftwareOpenGL) if hasattr(Qt.ApplicationAttribute, "AA_UseSoftwareOpenGL") else False),
    )
    AA_ShareOpenGLContexts: SettingsProperty[bool] = Settings.addSetting(
        "AA_ShareOpenGLContexts",
        (QApplication.testAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts) if hasattr(Qt.ApplicationAttribute, "AA_ShareOpenGLContexts") else False),
    )
    AA_SetPalette: SettingsProperty[bool] = Settings.addSetting(
        "AA_SetPalette",
        (QApplication.testAttribute(Qt.ApplicationAttribute.AA_SetPalette) if hasattr(Qt.ApplicationAttribute, "AA_SetPalette") else False),
    )
    AA_EnableHighDpiScaling: SettingsProperty[bool] = Settings.addSetting(
        "AA_EnableHighDpiScaling",
        (
            QApplication.testAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)  # pyright: ignore[reportAttributeAccessIssue]
            if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling")
            else True
        ),
    )
    AA_DisableHighDpiScaling: SettingsProperty[bool] = Settings.addSetting(
        "AA_DisableHighDpiScaling",
        (
            QApplication.testAttribute(Qt.ApplicationAttribute.AA_DisableHighDpiScaling)  # pyright: ignore[reportAttributeAccessIssue]
            if hasattr(Qt.ApplicationAttribute, "AA_DisableHighDpiScaling")
            else False
        ),
    )
    AA_PluginApplication: SettingsProperty[bool] = Settings.addSetting(
        "AA_PluginApplication",
        (QApplication.testAttribute(Qt.ApplicationAttribute.AA_PluginApplication) if hasattr(Qt.ApplicationAttribute, "AA_PluginApplication") else False),
    )
    AA_UseStyleSheetPropagationInWidgetStyles: SettingsProperty[bool] = Settings.addSetting(
        "AA_UseStyleSheetPropagationInWidgetStyles",
        (
            QApplication.testAttribute(Qt.ApplicationAttribute.AA_UseStyleSheetPropagationInWidgetStyles)
            if hasattr(Qt.ApplicationAttribute, "AA_UseStyleSheetPropagationInWidgetStyles")
            else False
        ),
    )
    AA_DontUseNativeDialogs: SettingsProperty[bool] = Settings.addSetting(
        "AA_DontUseNativeDialogs",
        (QApplication.testAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs) if hasattr(Qt.ApplicationAttribute, "AA_DontUseNativeDialogs") else False),
    )
    AA_SynthesizeMouseForUnhandledTabletEvents: SettingsProperty[bool] = Settings.addSetting(
        "AA_SynthesizeMouseForUnhandledTabletEvents",
        (
            QApplication.testAttribute(Qt.ApplicationAttribute.AA_SynthesizeMouseForUnhandledTabletEvents)
            if hasattr(Qt.ApplicationAttribute, "AA_SynthesizeMouseForUnhandledTabletEvents")
            else False
        ),
    )
    AA_CompressHighFrequencyEvents: SettingsProperty[bool] = Settings.addSetting(
        "AA_CompressHighFrequencyEvents",
        (QApplication.testAttribute(Qt.ApplicationAttribute.AA_CompressHighFrequencyEvents) if hasattr(Qt.ApplicationAttribute, "AA_CompressHighFrequencyEvents") else False),
    )
    AA_DontCheckOpenGLContextThreadAffinity: SettingsProperty[bool] = Settings.addSetting(
        "AA_DontCheckOpenGLContextThreadAffinity",
        (
            QApplication.testAttribute(Qt.ApplicationAttribute.AA_DontCheckOpenGLContextThreadAffinity)
            if hasattr(Qt.ApplicationAttribute, "AA_DontCheckOpenGLContextThreadAffinity")
            else False
        ),
    )
    AA_DisableShaderDiskCache: SettingsProperty[bool] = Settings.addSetting(
        "AA_DisableShaderDiskCache",
        (QApplication.testAttribute(Qt.ApplicationAttribute.AA_DisableShaderDiskCache) if hasattr(Qt.ApplicationAttribute, "AA_DisableShaderDiskCache") else False),
    )
    AA_DontShowShortcutsInContextMenus: SettingsProperty[bool] = Settings.addSetting(
        "AA_DontShowShortcutsInContextMenus",
        (
            QApplication.testAttribute(Qt.ApplicationAttribute.AA_DontShowShortcutsInContextMenus)
            if hasattr(Qt.ApplicationAttribute, "AA_DontShowShortcutsInContextMenus")
            else False
        ),
    )
    AA_CompressTabletEvents: SettingsProperty[bool] = Settings.addSetting(
        "AA_CompressTabletEvents",
        (QApplication.testAttribute(Qt.ApplicationAttribute.AA_CompressTabletEvents) if hasattr(Qt.ApplicationAttribute, "AA_CompressTabletEvents") else False),
    )
    AA_DisableWindowContextHelpButton: SettingsProperty[bool] = Settings.addSetting(
        "AA_DisableWindowContextHelpButton",
        (
            QApplication.testAttribute(Qt.ApplicationAttribute.AA_DisableWindowContextHelpButton)  # pyright: ignore[reportAttributeAccessIssue]
            if hasattr(Qt.ApplicationAttribute, "AA_DisableWindowContextHelpButton")
            else False
        ),
    )
    AA_DisableSessionManager: SettingsProperty[bool] = Settings.addSetting(
        "AA_DisableSessionManager",
        (QApplication.testAttribute(Qt.ApplicationAttribute.AA_DisableSessionManager) if hasattr(Qt.ApplicationAttribute, "AA_DisableSessionManager") else False),
    )
    AA_DisableNativeVirtualKeyboard: SettingsProperty[bool] = Settings.addSetting(
        "AA_DisableNativeVirtualKeyboard",
        (
            QApplication.testAttribute(Qt.ApplicationAttribute.AA_DisableNativeVirtualKeyboard)
            if hasattr(Qt.ApplicationAttribute, "AA_DisableNativeVirtualKeyboard")
            else False
        ),
    )
    # endregion
