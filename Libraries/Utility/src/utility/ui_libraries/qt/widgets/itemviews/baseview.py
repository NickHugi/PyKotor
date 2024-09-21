from __future__ import annotations

import ast

from contextlib import suppress
from typing import TYPE_CHECKING, Any, Callable

import qtpy

from loggerplus import RobustLogger
from qtpy.QtCore import QMargins, QMetaType, QObject, QSettings, QSize
from qtpy.QtGui import QColor
from qtpy.QtWidgets import (
    QAbstractItemView,
    QAction,
    QActionGroup,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from utility.ui_libraries.qt.debug.print_qobject import format_qt_obj

if TYPE_CHECKING:
    from qtpy.QtWidgets import QMenu


# sip does not support multiple inheritence structures like this.
# I have no idea why, but it doesn't work. Function calls would just say 'class x not supported for function y'.
# This is a nice workaround for getting type hints working, at least. It's assumed
# that the subclasses will inherit the real qt views before they call the function anyway.
class RobustBaseWidget(QWidget if TYPE_CHECKING else object):
    def __init__(self, parent: QWidget | None = None, *, settings_name: str | None = None, no_qt_init: bool = False):
        if not no_qt_init:
            super().__init__(parent)
        self._settings_name: str = settings_name and settings_name.strip() or getattr(self, "objectName", lambda: self.__class__.__name__)()

        self._settings_cache: dict[str, QSettings] = {}
        self.original_stylesheet: str = self.styleSheet()
        self._initialized: bool = False

    def _all_settings(self, settings_group: str) -> QSettings:
        if settings_group not in self._settings_cache:
            self._settings_cache[settings_group] = QSettings(f"QtCustomWidgets{qtpy.API_NAME}", settings_group)
        return self._settings_cache[settings_group]

    def get_setting(self, key: str, default: Any, val_type: type | None = None) -> Any:
        # First check settings for _settings_name
        settings = self._all_settings(self._settings_name)
        try:
            if val_type is None:
                value = settings.value(key, default)
            else:
                value = settings.value(key, default, val_type)
        except Exception as e:  # noqa: BLE001
            RobustLogger().warning(f"Error getting setting {key}: {e}")
            settings.setValue(key, default)
            return default
        if value is not None:
            return value

        # Then check the class hierarchy
        for cls in self.__class__.__mro__:
            if cls is QAbstractItemView:
                break
            if cls.__name__ == self._settings_name:
                continue  # Skip, as we've already checked this
            value = (
                self._all_settings(cls.__name__).value(key, None)
                if val_type is None
                else self._all_settings(cls.__name__).value(key, None, val_type)
            )
            if value is not None:
                return value
        return default

    def set_setting(self, key: str, value: Any):
        print("key:", key, "value:", value)
        settings = self._all_settings(self._settings_name)
        settings.setValue(key, value)

    def _init_setting(
        self,
        get_func: Callable[[], Any],
        set_func: Callable[[Any], Any],
        settings_key: str,
        param_type: type | None = None,
    ) -> Any:
        current_value = get_func()
        initial_value = self.get_setting(settings_key, current_value, current_value.__class__ if param_type is None else param_type)
        if not self._initialized:
            print("Initializing setting:", settings_key, "with value:", initial_value)
            set_func(initial_value)
        return initial_value

    def _add_menu_action(  # noqa: PLR0913
        self,
        menu: QMenu,
        title: str,
        get_func: Callable[[], Any],
        set_func: Callable[[Any], Any],
        settings_key: str,
        param_type: type = bool,
    ):
        current_value = self.get_setting(settings_key, get_func())
        action_title = f"{title}: {format_qt_obj(current_value)}" if param_type is not bool else title
        action = QAction(action_title, self)

        if param_type is bool:
            action.setCheckable(True)
            setting_value = self.get_setting(settings_key, current_value)
            if isinstance(setting_value, str):
                with suppress(ValueError, SyntaxError):
                    setting_value = ast.literal_eval(setting_value)
            settings_value = False if setting_value == "false" else bool(setting_value)
            action.setChecked(settings_value)
            set_func(settings_value)  # Apply the initial value from settings
            def on_toggled(checked: bool):  # noqa: FBT001
                set_func(checked)
                self.set_setting(settings_key, checked)
            action.toggled.connect(on_toggled)
        else:
            def on_triggered():
                self._handle_generic_action(get_func, set_func, title, settings_key, param_type)
            action.triggered.connect(on_triggered)
        menu.addAction(action)

    def _add_color_menu_action(
        self,
        menu: QMenu,
        title: str,
        current_color_func: Callable[[], QColor],
        settings_key: str,
    ):
        action = QAction(title, self)
        action.triggered.connect(lambda: self._handle_color_action(current_color_func, title, settings_key))
        menu.addAction(action)

    def _add_simple_action(self, menu: QMenu, title: str, func: Callable[[], Any]):
        action = QAction(title, self)
        action.triggered.connect(lambda random_arg_qt_is_sending: func())  # noqa: ARG005
        menu.addAction(action)

    def _add_exclusive_menu_action(  # noqa: PLR0913
        self,
        menu: QMenu,
        title: str,
        current_state_func: Callable[[], Any],
        set_func: Callable[[Any], Any],
        options: dict[str, Any],
        settings_key: str,
        param_type: type = bool,
    ):
        initial_value = self._init_setting(current_state_func, set_func, settings_key, param_type)
        sub_menu = menu.addMenu(title)
        action_group = QActionGroup(self)
        action_group.setExclusive(True)
        for option_name, option_value in options.items():
            action = QAction(option_name, self)
            action.setCheckable(True)
            action.setChecked(initial_value == option_value)
            action.triggered.connect(lambda checked, val=option_value: [set_func(val), self.set_setting(settings_key, val)])
            sub_menu.addAction(action)
            action_group.addAction(action)

    def _add_multi_option_menu_action(  # noqa: PLR0913
        self,
        menu: QMenu,
        title: str,
        get_func: Callable[[], Any],
        set_func: Callable[[Any], Any],
        options: dict[str, Any],
        settings_key: str,
        param_type: type | None = None,
    ):  # noqa: PLR0913
        initial_value = self._init_setting(get_func, set_func, settings_key, param_type)
        sub_menu = menu.addMenu(title)
        def update_state():
            current_state = 0
            for action in sub_menu.actions():
                if action.isChecked():
                    current_state |= options[action.text()]
            if not isinstance(current_state, initial_value.__class__) and initial_value is not None:
                current_state = initial_value.__class__(current_state)
            set_func(current_state)
            self.set_setting(settings_key, current_state)

        for option_name, option_value in options.items():
            action = QAction(option_name, self)
            action.setCheckable(True)
            action.setChecked(bool(initial_value & option_value))
            action.triggered.connect(update_state)
            sub_menu.addAction(action)

    def _handle_checkable_action(self, checked: bool, setter: Callable[[Any], None], settings_key: str, param_type: type | None = None) -> None:  # noqa: FBT001
        value = checked if param_type is None else param_type(checked)
        setter(value)
        self.set_setting(settings_key, value)

    def _handle_color_action(
        self,
        get_func: Callable[[], Any],
        title: str,
        settings_key: str,
    ):
        color = QColorDialog.getColor(get_func(), self, title)
        if color.isValid():
            self.set_setting(settings_key, color.name())
            self.update()

    def _handle_generic_action(self, get_func: Callable[[], Any], set_func: Callable[[Any], Any], title: str, settings_key: str, param_type: type):
        current_value = self.get_setting(settings_key, get_func(), get_func().__class__)

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Set {title}")
        layout = QVBoxLayout(dialog)

        input_widget = self._create_input_widget(param_type, current_value)
        layout.addWidget(input_widget)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        if dialog.exec() != QDialog.Accepted:
            return

        try:
            new_value = self._get_new_value(input_widget, param_type)
        except (ValueError, TypeError):
            QMessageBox.warning(self, "Invalid Input", f"Invalid input for {title}. Please enter a valid {param_type.__name__}.")
            return

        set_func(new_value)
        self.set_setting(settings_key, new_value)
        self._update_action_text(title, new_value)

    def _create_input_widget(self, param_type: type, current_value: Any) -> QWidget:
        if isinstance(current_value, QObject):
            meta_type = current_value.metaObject().userProperty().userType()
        else:
            meta_type = QMetaType.type(param_type.__name__)

        if meta_type in (QMetaType.Int, QMetaType.Long, QMetaType.LongLong):
            widget = QSpinBox()
            widget.setValue(int(current_value))  # pyright: ignore[reportArgumentType]
        elif meta_type in (QMetaType.Float, QMetaType.Double):
            widget = QDoubleSpinBox()
            widget.setValue(float(current_value))  # pyright: ignore[reportArgumentType]
        elif meta_type == QMetaType.Bool:
            widget = QCheckBox()
            widget.setChecked(bool(current_value))
        elif meta_type == QMetaType.QString:
            widget = QLineEdit(str(current_value))
        elif meta_type == QMetaType.QColor:
            widget = QLineEdit(current_value.name() if isinstance(current_value, QColor) else str(current_value))
        elif meta_type == QMetaType.QDate:
            widget = QDateEdit(current_value)  # pyright: ignore[reportArgumentType, reportCallIssue]
        elif meta_type == QMetaType.QTime:
            widget = QTimeEdit(current_value)  # pyright: ignore[reportArgumentType, reportCallIssue]
        elif meta_type == QMetaType.QDateTime:
            widget = QDateTimeEdit(current_value)  # pyright: ignore[reportArgumentType, reportCallIssue]
        elif meta_type == QMetaType.QSize:
            if isinstance(current_value, QSize):
                widget = QLineEdit(f"{current_value.width()},{current_value.height()}")
            else:
                widget = QLineEdit()
        elif param_type == QMargins and isinstance(current_value, QMargins):
            widget = QLineEdit(f"{current_value.left()},{current_value.top()},{current_value.right()},{current_value.bottom()}")
        elif hasattr(param_type, "__members__"):  # Enum type
            widget = QComboBox()
            widget.addItems(param_type.__members__.keys())
            widget.setCurrentText(current_value.name if hasattr(current_value, "name") else str(current_value))
        else:
            widget = QLineEdit(str(current_value))

        return widget

    def _get_new_value(self, input_widget: QWidget, param_type: type) -> Any:
        if isinstance(input_widget, QSpinBox):
            return input_widget.value()
        if isinstance(input_widget, QDoubleSpinBox):
            return input_widget.value()
        if isinstance(input_widget, QCheckBox):
            return input_widget.isChecked()
        if isinstance(input_widget, QComboBox):
            return param_type.__members__[input_widget.currentText()]
        if isinstance(input_widget, QDateTimeEdit):
            return input_widget.dateTime().toPyDateTime()
        if isinstance(input_widget, QDateEdit):
            return input_widget.date().toPyDate()
        if isinstance(input_widget, QTimeEdit):
            return input_widget.time().toPyTime()
        if isinstance(input_widget, QLineEdit):
            if param_type == QColor:
                return QColor(input_widget.text())
            if param_type == QSize:
                width, height = map(int, input_widget.text().split(","))
                return QSize(width, height)
            if param_type == QMargins:
                left, top, right, bottom = map(int, input_widget.text().split(","))
                return QMargins(left, top, right, bottom)
            return param_type(input_widget.text())
        raise ValueError(f"Unsupported input widget type: {type(input_widget)}")

    def _update_action_text(self, title: str, new_value: Any):
        action = self.sender()
        if isinstance(action, QAction):
            if isinstance(new_value, QMargins):
                value_str = f"{new_value.left()},{new_value.top()},{new_value.right()},{new_value.bottom()}"
            else:
                value_str = format_qt_obj(new_value)
            action.setText(f"{title}: {value_str}")
