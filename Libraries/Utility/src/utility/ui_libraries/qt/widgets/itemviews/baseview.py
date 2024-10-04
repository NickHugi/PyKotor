from __future__ import annotations

import ast

from contextlib import suppress
from typing import TYPE_CHECKING, Any, Callable

import qtpy

from loggerplus import RobustLogger
from qtpy import QtCore
from qtpy.QtCore import QMargins, QMetaType, QSettings, QSize, QTimer, Qt
from qtpy.QtGui import QColor, QPalette, QSyntaxHighlighter, QTextCharFormat
from qtpy.QtWidgets import (
    QAbstractItemView,
    QAction,
    QActionGroup,
    QApplication,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QDockWidget,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTextEdit,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from utility.ui_libraries.qt.tools.debug.print_qobject import format_qt_obj
from utility.ui_libraries.qt.tools.parser import QtObjectParser
from utility.ui_libraries.qt.tools.qt_meta import get_qt_meta_type

if TYPE_CHECKING:
    from qtpy.QtCore import QObject
    from qtpy.QtGui import QTextDocument
    from qtpy.QtWidgets import QMenu


class StyleSheetHighlighter(QSyntaxHighlighter):
    def __init__(self, parent: QTextDocument | QObject):
        super().__init__(parent)
        self.highlighting_rules: list[tuple[str, QTextCharFormat]] = []

        palette = QApplication.palette()

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(palette.color(QPalette.ColorRole.Highlight))
        keywords = ["background-color", "color", "border", "margin", "padding", "font"]
        self.highlighting_rules.extend((rf"\b{w}\b", keyword_format) for w in keywords)

        property_format = QTextCharFormat()
        property_format.setForeground(palette.color(QPalette.ColorRole.Link))
        self.highlighting_rules.append((r"[^:]+(?=:)", property_format))

        value_format = QTextCharFormat()
        value_format.setForeground(palette.color(QPalette.ColorRole.Text))
        self.highlighting_rules.append((r":\s*([^;]+)", value_format))

        selector_format = QTextCharFormat()
        selector_format.setForeground(palette.color(QPalette.ColorRole.BrightText))
        self.highlighting_rules.append((r"^[^\{]+", selector_format))

    def highlightBlock(self, text: str):
        for pattern, fmt in self.highlighting_rules:
            expression = QtCore.QRegularExpression(pattern)
            it = expression.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)


# sip does not support multiple inheritence structures like this.
# I have no idea why, but it doesn't work. Function calls would just say 'class x not supported for function y'.
# This is a nice workaround for getting type hints working, at least. It's assumed
# that the subclasses will inherit the real qt views before they call the function anyway.
class RobustBaseWidget(QWidget if TYPE_CHECKING else object):
    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        settings_name: str | None = None,
    ):
        self._settings_name: str = settings_name and settings_name.strip() or getattr(self, "objectName", lambda: self.__class__.__name__)()

        self._settings_cache: dict[str, QSettings] = {}
        self.original_stylesheet: str = self.styleSheet()
        self._layout_changed_debounce_timer: QTimer = QTimer(self)
        self._initialized: bool = False

    def _bold_if_changed(self, action: QAction, settings_key: str, current_value: Any):
        default_value = self.get_setting(settings_key, None)
        if current_value != default_value:
            font = action.font()
            font.setBold(True)
            action.setFont(font)
    def _update_recently_changed(self, settings_key: str):
        recent_settings = self.get_setting("recently_changed", [])
        if settings_key not in recent_settings:
            recent_settings.append(settings_key)
        self.set_setting("recently_changed", recent_settings)
    def _add_reset_actions(self, menu: QMenu):
        action_qt_defaults = QAction("Qt Defaults", self)
        action_qt_defaults.triggered.connect(self._reset_to_qt_defaults)
        menu.addAction(action_qt_defaults)
        action_subclass_defaults = QAction("Subclass Defaults", self)
        action_subclass_defaults.triggered.connect(self._reset_to_subclass_defaults)
        menu.addAction(action_subclass_defaults)
        action_all_defaults = QAction(f"Reset All Defaults for {self._settings_name}", self)
        action_all_defaults.triggered.connect(self._reset_all_defaults)
        menu.addAction(action_all_defaults)
    def _reset_to_qt_defaults(self):
        self.set_setting("customStylesheet", "")
        self.setStyleSheet("")
        self.update()
        # TODO(th3w1zard1): determine what was specifically set in the subclass's `__init__`.
    def _reset_to_subclass_defaults(self):
        self.restore_state()
    def _reset_all_defaults(self):
        self._settings_cache = {}
        self.restore_state()
        self.update()

    def _all_settings(
        self,
        settings_group: str,
    ) -> QSettings:
        if settings_group not in self._settings_cache:
            self._settings_cache[settings_group] = QSettings(f"QtCustomWidgets{qtpy.API_NAME}", settings_group)
        return self._settings_cache[settings_group]

    def get_setting(
        self,
        key: str,
        default: Any,
        val_type: type | None = None,
    ) -> Any:
        # First check settings for _settings_name
        settings = self._all_settings(self._settings_name)
        try:
            value = settings.value(key, default) if val_type is None else settings.value(key, default, val_type)
        except Exception as e:  # noqa: BLE001
            RobustLogger().warning(f"Error getting setting {key}: {e}")
            settings.setValue(key, default)
            return default
        else:
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

    def set_setting(
        self,
        key: str,
        value: Any,
    ):
        settings = self._all_settings(self._settings_name)
        settings.setValue(key, value)

    def _init_setting(
        self,
        get_func: Callable[[], Any],
        set_func: Callable[[Any], Any],
        settings_key: str,
        param_type: type | None = None,
    ) -> Any:
        """Acquires the current setting, or initializes if it is not already set to this widget's lifetime.

        Widgets should manage `self._initialized` if they require a different behavior.
        Default behavior is to run the menus and actions to set the initial value. If _initialized is False, the menu will not be shown.
        """
        current_value = get_func()

        # QT6 does not like the 3rd argument to QSettings.value for some reason.
        initial_value = (
            self.get_setting(settings_key, current_value)
            if qtpy.QT6
            else self.get_setting(
                settings_key,
                current_value,
                current_value.__class__ if param_type is None else param_type,
            )
        )
        if not self._initialized:
            print("First time initializing setting:", settings_key, "with value:", repr(initial_value))
            set_func(initial_value)
        return initial_value

    def emit_layout_changed(self):
        model = self.model()
        if model is not None:
            model.layoutChanged.emit()

    def debounce_layout_changed(
        self,
        timeout: int = 100,
        *,
        pre_change_emit: bool = False,
    ):
        if self._layout_changed_debounce_timer.isActive():
            self._layout_changed_debounce_timer.stop()
        elif pre_change_emit:
            self.model().layoutAboutToBeChanged.emit()
        self._layout_changed_debounce_timer.start(timeout)

    def _add_menu_action(  # noqa: PLR0913
        self,
        menu: QMenu,
        title: str,
        get_func: Callable[[], Any],
        set_func: Callable[[Any], Any],
        settings_key: str,
        param_type: type = bool,
    ):
        if title == "Edit Stylesheet":
            action = QAction(title, self)
            action.triggered.connect(lambda: self._show_stylesheet_editor(get_func, set_func, settings_key))
            menu.addAction(action)
            return
        current_value = self.get_setting(settings_key, get_func())
        action_title = f"{title}: {format_qt_obj(current_value)[:10]}" if param_type is not bool else title
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
        self._bold_if_changed(action, settings_key, get_func())
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
            action.triggered.connect(
                lambda checked, val=option_value: [
                    set_func(val),
                    self.set_setting(settings_key, val),
                ]
            )
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

    def _handle_checkable_action(
        self,
        checked: bool,
        setter: Callable[[Any], None],
        settings_key: str,
        param_type: type | None = None,
    ) -> None:  # noqa: FBT001
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

    def _handle_generic_action(
        self,
        get_func: Callable[[], Any],
        set_func: Callable[[Any], Any],
        title: str,
        settings_key: str,
        param_type: type,
    ):
        current_value = self.get_setting(settings_key, get_func(), get_func().__class__)

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Set {title}")
        layout = QVBoxLayout(dialog)

        input_widget = QtObjectParser.create_input_widget(param_type, current_value)
        layout.addWidget(input_widget)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            new_value = self._get_new_value(input_widget, param_type)
        except (ValueError, TypeError):
            QMessageBox.warning(self, "Invalid Input", f"Invalid input for {title}. Please enter a valid {param_type.__name__}.")
            return

        try:
            set_func(new_value)
        except TypeError:
            RobustLogger().error(f"Error setting {title} to {new_value}", exc_info=True)
            return
        self.set_setting(settings_key, new_value)
        self._update_action_text(title, new_value)

    def _create_input_widget(self, param_type: type, current_value: Any) -> QWidget:
        meta_type = get_qt_meta_type(param_type, current_value)

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
            value_str = value_str[:10]  # Limit to 10 characters
            action.setText(f"{title}: {value_str}")

    def show_stylesheet_editor(self):
        if not hasattr(self, "_stylesheet_editor"):
            self._stylesheet_editor = QDockWidget("Stylesheet Editor", self)
            editor_widget = QWidget()
            editor_layout = QVBoxLayout(editor_widget)

            splitter = QSplitter(Qt.Orientation.Vertical)

            preview_widget = QWidget()
            preview_layout = QVBoxLayout(preview_widget)
            preview_label = QLabel("Preview:")
            self._preview_area = QWidget()
            self._preview_area.setStyleSheet(self.styleSheet())
            preview_layout.addWidget(preview_label)
            preview_layout.addWidget(self._preview_area)

            self._stylesheet_text_edit = QTextEdit()
            self._stylesheet_text_edit.setPlainText(self.styleSheet())
            self._stylesheet_text_edit.textChanged.connect(self._update_stylesheet_preview)

            splitter.addWidget(preview_widget)
            splitter.addWidget(self._stylesheet_text_edit)

            button_layout = QHBoxLayout()
            apply_button = QPushButton("Apply")
            apply_button.clicked.connect(self._apply_stylesheet)
            reset_button = QPushButton("Reset")
            reset_button.clicked.connect(self._reset_stylesheet)
            button_layout.addWidget(apply_button)
            button_layout.addWidget(reset_button)

            editor_layout.addWidget(splitter)
            editor_layout.addLayout(button_layout)

            self._stylesheet_editor.setWidget(editor_widget)
            self._stylesheet_editor.setFloating(True)
            self._stylesheet_editor.resize(400, 600)

        self._stylesheet_editor.show()

    def _show_stylesheet_editor(
        self,
        get_func: Callable[[], Any],
        set_func: Callable[[Any], Any],
        settings_key: str,
    ):
        if not hasattr(self, "_stylesheet_editor"):
            self._stylesheet_editor = QDockWidget("Stylesheet Editor", self)
            editor_widget = QWidget()
            editor_layout = QVBoxLayout(editor_widget)

            splitter = QSplitter(Qt.Orientation.Vertical)

            # Preview area
            preview_widget = QWidget()
            preview_layout = QVBoxLayout(preview_widget)
            preview_label = QLabel("Preview:")
            self._preview_area = QWidget()
            self._preview_area.setStyleSheet(get_func())
            preview_layout.addWidget(preview_label)
            preview_layout.addWidget(self._preview_area)

            # Text editor
            self._stylesheet_text_edit = QTextEdit()
            self._stylesheet_text_edit.setPlainText(get_func())
            self._stylesheet_text_edit.textChanged.connect(lambda: self._update_stylesheet_preview())

            # Syntax highlighter
            self._highlighter = StyleSheetHighlighter(self._stylesheet_text_edit.document())

            splitter.addWidget(preview_widget)
            splitter.addWidget(self._stylesheet_text_edit)

            # Buttons
            button_layout = QHBoxLayout()
            apply_button = QPushButton("Apply")
            apply_button.clicked.connect(lambda: self._apply_stylesheet(set_func, settings_key))
            reset_button = QPushButton("Reset")
            reset_button.clicked.connect(lambda: self._reset_stylesheet(get_func))
            color_picker_button = QPushButton("Color Picker")
            color_picker_button.clicked.connect(self._show_color_picker)
            button_layout.addWidget(apply_button)
            button_layout.addWidget(reset_button)
            button_layout.addWidget(color_picker_button)

            editor_layout.addWidget(splitter)
            editor_layout.addLayout(button_layout)

            self._stylesheet_editor.setWidget(editor_widget)
            self._stylesheet_editor.setFloating(True)
            self._stylesheet_editor.resize(600, 800)

        self._stylesheet_editor.show()

    def _update_stylesheet_preview(self):
        if hasattr(self, "_preview_area"):
            self._preview_area.setStyleSheet(self._stylesheet_text_edit.toPlainText())

    def _apply_stylesheet(self, set_func: Callable[[Any], Any], settings_key: str):
        new_stylesheet = self._stylesheet_text_edit.toPlainText()
        set_func(new_stylesheet)
        self.set_setting(settings_key, new_stylesheet)
        if hasattr(self, "_preview_area"):
            self._preview_area.setStyleSheet(new_stylesheet)

    def _reset_stylesheet(self, get_func: Callable[[], Any]):
        self._stylesheet_text_edit.setPlainText(get_func())
        if hasattr(self, "_preview_area"):
            self._preview_area.setStyleSheet(get_func())

    def _show_color_picker(self):
        color = QColorDialog.getColor(parent=self)
        if color.isValid():
            cursor = self._stylesheet_text_edit.textCursor()
            cursor.insertText(color.name())

    def setStyleSheet(self, sheet: str) -> None:
        super().setStyleSheet(sheet)
        self.set_setting("customStylesheet", sheet)

    def styleSheet(self) -> str:
        return self.get_setting("customStylesheet", super().styleSheet())


if __name__ == "__main__":
    import sys

    from qtpy.QtCore import Qt
    from qtpy.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget

    class TestWidget(RobustBaseWidget, QWidget):
        def __init__(
            self,
            parent: QWidget | None = None,
            flags: Qt.WindowFlags | Qt.WindowType | None = None,
            *args,
            should_call_qt_init: bool = True,
            **kwargs,
        ):
            if should_call_qt_init:
                if flags is None:
                    QWidget.__init__(self, parent)
                else:
                    QWidget.__init__(self, parent, flags)
            RobustBaseWidget.__init__(self, parent, *args, **kwargs)
            layout = QVBoxLayout(self)

            # Add widgets to test various features
            self.label = QLabel("Test Widget")
            self.button = QPushButton("Click Me")
            self.text_edit = QTextEdit()

            # Add buttons to test menu actions
            action_layout = QHBoxLayout()
            self.test_color_action = QPushButton("Test Color Action")
            self.test_generic_action = QPushButton("Test Generic Action")
            action_layout.addWidget(self.test_color_action)
            action_layout.addWidget(self.test_generic_action)

            layout.addWidget(self.label)
            layout.addWidget(self.button)
            layout.addWidget(self.text_edit)
            layout.addLayout(action_layout)

            # Connect buttons to test methods
            self.button.clicked.connect(self.on_button_click)
            self.test_color_action.clicked.connect(self.test_color_action_method)
            self.test_generic_action.clicked.connect(self.test_generic_action_method)

        def on_button_click(self):
            self.label.setText("Button Clicked!")

        def test_color_action_method(self):
            self._handle_color_action(lambda: Qt.red, "Test Color", "testColorSetting")

        def test_generic_action_method(self):
            self._handle_generic_action(lambda: 10, lambda x: self.text_edit.setText(f"New value: {x}"), "Test Generic", "testGenericSetting", int)

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setCentralWidget(TestWidget(self))
            self.setGeometry(100, 100, 400, 300)
            self.setWindowTitle("RobustBaseWidget Test")

    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
