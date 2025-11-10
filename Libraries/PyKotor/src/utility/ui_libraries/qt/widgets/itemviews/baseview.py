from __future__ import annotations

import sys

from typing import TYPE_CHECKING, Any, Callable, Literal

import qtpy

from loggerplus import RobustLogger
from qtpy.QtCore import QLocale, QMargins, QMetaType, QRect, QRegularExpression, QSize, Qt
from qtpy.QtGui import QColor, QCursor, QFont, QIcon, QPalette, QRegion, QSyntaxHighlighter, QTextCharFormat
from qtpy.QtWidgets import (
    QAction,  # pyright: ignore[reportPrivateImportUsage]
    QActionGroup,  # pyright: ignore[reportPrivateImportUsage]
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
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStyle,
    QTextEdit,
    QTimeEdit,
    QVBoxLayout,
    QWhatsThis,
    QWidget,
)

from utility.ui_libraries.qt.tools.qt_meta import get_qt_meta_type

if TYPE_CHECKING:
    from qtpy.QtCore import QObject, QRegularExpressionMatch, QRegularExpressionMatchIterator, QSettings
    from qtpy.QtGui import QTextCursor, QTextDocument


class StyleSheetHighlighter(QSyntaxHighlighter):
    def __init__(self, parent: QTextDocument | QObject):
        super().__init__(parent)
        self.highlighting_rules: list[tuple[str, QTextCharFormat]] = []

        palette: QPalette = QApplication.palette()

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(palette.color(QPalette.ColorRole.Highlight))
        keywords: list[str] = ["background-color", "color", "border", "margin", "padding", "font"]
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

    def highlightBlock(
        self,
        text: str,
    ):
        for pattern, fmt in self.highlighting_rules:
            expression: QRegularExpression = QRegularExpression(pattern)
            it: QRegularExpressionMatchIterator = expression.globalMatch(text)
            while it.hasNext():
                match: QRegularExpressionMatch = it.next()
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
        def get_object_name():
            return self.__class__.__name__
        self._settings_name: str = (
            settings_name
            and settings_name.strip()
            or getattr(self, "objectName", get_object_name)()
        )

        self._settings_cache: dict[str, QSettings] = {}
        self.original_stylesheet: str = self.styleSheet()
        self._initialized: bool = False

    def _create_drawer_button(self):
        self._robust_drawer: QPushButton = QPushButton(self)
        self._robust_drawer.setObjectName("_robust_drawer")
        self._robust_drawer.setToolTip("Show context menu")
        q_app_style: QStyle | None = QApplication.style()
        assert q_app_style is not None
        icon: QIcon = QIcon(q_app_style.standardIcon(QStyle.StandardPixmap.SP_ToolBarHorizontalExtensionButton))
        self._robust_drawer.setIcon(icon)

    def build_context_menu(
        self,
        parent: QWidget | None = None,
    ) -> QMenu:
        q_app_style: QStyle | None = QApplication.style()
        assert q_app_style is not None

        self.menu = QMenu(None)
        widget_menu: QMenu | None = self.menu.addMenu("QWidget")
        assert widget_menu is not None

        # Window properties
        window_menu: QMenu | None = widget_menu.addMenu("Window")
        assert window_menu is not None
        self._add_menu_action(window_menu, "Set Window Title", self.windowTitle, self.setWindowTitle, "windowTitle", param_type=str)
        self._add_menu_action(window_menu, "Set Window Icon", self.windowIcon, self.setWindowIcon, "windowIcon", param_type=QIcon)
        self._add_menu_action(window_menu, "Set Window Icon Text", self.windowIconText, self.setWindowIconText, "windowIconText", param_type=str)
        self._add_menu_action(window_menu, "Set Window Opacity", self.windowOpacity, self.setWindowOpacity, "windowOpacity", param_type=float)
        self._add_menu_action(window_menu, "Set Window Modified", self.isWindowModified, self.setWindowModified, "windowModified")
        self._add_menu_action(window_menu, "Set Window Role", self.windowRole, self.setWindowRole, "windowRole", param_type=str)
        self._add_menu_action(window_menu, "Set Window FilePath", self.windowFilePath, self.setWindowFilePath, "windowFilePath", param_type=str)
        self._add_exclusive_menu_action(window_menu, "Set Window State", self.windowState, self.setWindowState, {
            "Normal": Qt.WindowState.WindowNoState,
            "Minimized": Qt.WindowState.WindowMinimized,
            "Maximized": Qt.WindowState.WindowMaximized,
            "FullScreen": Qt.WindowState.WindowFullScreen,
        }, "windowState", param_type=Qt.WindowState)
        self._add_exclusive_menu_action(window_menu, "Set Window Modality", self.windowModality, self.setWindowModality, {
            "Non Modal": Qt.WindowModality.NonModal,
            "Window Modal": Qt.WindowModality.WindowModal,
            "Application Modal": Qt.WindowModality.ApplicationModal,
        }, "windowModality", param_type=Qt.WindowModality)

        # Geometry and layout
        geometry_menu: QMenu | None = widget_menu.addMenu("Geometry")
        assert geometry_menu is not None
        self._add_menu_action(geometry_menu, "Set Geometry", self.geometry, self.setGeometry, "geometry", param_type=QRect)
        self._add_menu_action(geometry_menu, "Set Fixed Size", self.size, self.setFixedSize, "fixedSize", param_type=QSize)
        self._add_menu_action(geometry_menu, "Set Minimum Size", self.minimumSize, self.setMinimumSize, "minimumSize", param_type=QSize)
        self._add_menu_action(geometry_menu, "Set Maximum Size", self.maximumSize, self.setMaximumSize, "maximumSize", param_type=QSize)
        self._add_menu_action(geometry_menu, "Set Base Size", self.baseSize, self.setBaseSize, "baseSize", param_type=QSize)
        self._add_menu_action(geometry_menu, "Set Size Increment", self.sizeIncrement, self.setSizeIncrement, "sizeIncrement", param_type=QSize)
        self._add_menu_action(geometry_menu, "Set Minimum Width", self.minimumWidth, self.setMinimumWidth, "minimumWidth", param_type=int)
        self._add_menu_action(geometry_menu, "Set Minimum Height", self.minimumHeight, self.setMinimumHeight, "minimumHeight", param_type=int)
        self._add_menu_action(geometry_menu, "Set Maximum Width", self.maximumWidth, self.setMaximumWidth, "maximumWidth", param_type=int)
        self._add_menu_action(geometry_menu, "Set Maximum Height", self.maximumHeight, self.setMaximumHeight, "maximumHeight", param_type=int)
        self._add_menu_action(geometry_menu, "Set Fixed Width", self.width, self.setFixedWidth, "fixedWidth", param_type=int)
        self._add_menu_action(geometry_menu, "Set Fixed Height", self.height, self.setFixedHeight, "fixedHeight", param_type=int)
        self._add_menu_action(geometry_menu, "Set Contents Margins", self.contentsMargins, self.setContentsMargins, "contentsMargins", param_type=QMargins)

        # Appearance
        appearance_menu: QMenu | None = widget_menu.addMenu("Appearance")
        assert appearance_menu is not None
        self._add_menu_action(appearance_menu, "Set Style Sheet", self.styleSheet, self.setStyleSheet, "styleSheet", param_type=str)
        self._add_menu_action(appearance_menu, "Set Font", self.font, self.setFont, "font", param_type=QFont)
        self._add_menu_action(appearance_menu, "Set Cursor", self.cursor, self.setCursor, "cursor", param_type=QCursor)
        self._add_menu_action(appearance_menu, "Set Mask", self.mask, self.setMask, "mask", param_type=QRegion)
        self._add_menu_action(appearance_menu, "Set Palette", self.palette, self.setPalette, "palette", param_type=QPalette)
        self._add_exclusive_menu_action(
            appearance_menu,
            "Set Background Role",
            self.backgroundRole,
            self.setBackgroundRole,
            {
                attr_name: role
                for attr_name, role in QPalette.ColorRole.__dict__.items()
                if not attr_name.startswith("_")
            },
            "backgroundRole",
            param_type=QPalette.ColorRole,
        )
        self._add_exclusive_menu_action(
            appearance_menu,
            "Set Foreground Role",
            self.foregroundRole,
            self.setForegroundRole,
            {
                attr_name: role
                for attr_name, role in QPalette.ColorRole.__dict__.items()
                if not attr_name.startswith("_")
            },
            "foregroundRole",
            param_type=QPalette.ColorRole,
        )
        self._add_menu_action(appearance_menu, "Set Auto Fill Background", self.autoFillBackground, self.setAutoFillBackground, "autoFillBackground")

        self._add_menu_action(
            appearance_menu,
            "Edit Stylesheet",
            self.styleSheet,
            self.setStyleSheet,
            "customStylesheet",
            param_type=str,
        )

        # Behavior
        behavior_menu: QMenu | None = widget_menu.addMenu("Behavior")
        assert behavior_menu is not None
        self._add_menu_action(
            behavior_menu,
            "Auto Fill Background",
            self.autoFillBackground,
            self.setAutoFillBackground,
            settings_key="autoFillBackground",
        )

        # Help menu
        whats_this_action: QAction | None = QAction(
            q_app_style.standardIcon(
                QStyle.StandardPixmap.SP_TitleBarContextHelpButton
            ),
            "What's This?",
            self,
        )
        assert whats_this_action is not None
        self._add_menu_action(behavior_menu, "Set Enabled", self.isEnabled, self.setEnabled, "enabled")
        self._add_menu_action(behavior_menu, "Set Visible", self.isVisible, self.setVisible, "visible")
        self._add_menu_action(behavior_menu, "Set Hidden", self.isHidden, self.setHidden, "hidden")
        self._add_menu_action(behavior_menu, "Set Mouse Tracking", self.hasMouseTracking, self.setMouseTracking, "mouseTracking")
        self._add_menu_action(behavior_menu, "Set Tablet Tracking", self.hasTabletTracking, self.setTabletTracking, "tabletTracking")
        self._add_menu_action(behavior_menu, "Set Updates Enabled", self.updatesEnabled, self.setUpdatesEnabled, "updatesEnabled")
        behavior_advanced_menu: QMenu | None = behavior_menu.addMenu("Advanced")
        assert behavior_advanced_menu is not None
        self._add_exclusive_menu_action(
            behavior_advanced_menu,
            "Focus Policy",
            self.focusPolicy,
            self.setFocusPolicy,
            options={
                "No Focus": Qt.FocusPolicy.NoFocus,
                "Tab Focus": Qt.FocusPolicy.TabFocus,
                "Click Focus": Qt.FocusPolicy.ClickFocus,
                "Strong Focus": Qt.FocusPolicy.StrongFocus,
                "Wheel Focus": Qt.FocusPolicy.WheelFocus,
            },
            settings_key="focusPolicy",
            param_type=Qt.FocusPolicy,
        )
        self._add_exclusive_menu_action(
            behavior_advanced_menu,
            "Set Context Menu Policy",
            self.contextMenuPolicy,
            self.setContextMenuPolicy,
            {
                "No Context Menu": Qt.ContextMenuPolicy.NoContextMenu,
                "Default Context Menu": Qt.ContextMenuPolicy.DefaultContextMenu,
                "Actions Context Menu": Qt.ContextMenuPolicy.ActionsContextMenu,
                "Custom Context Menu": Qt.ContextMenuPolicy.CustomContextMenu,
                "Prevent Context Menu": Qt.ContextMenuPolicy.PreventContextMenu,
            },
            "contextMenuPolicy",
            param_type=Qt.ContextMenuPolicy,
        )
        self._add_menu_action(behavior_menu, "Set Accept Drops", self.acceptDrops, self.setAcceptDrops, "acceptDrops")
        self._add_exclusive_menu_action(behavior_menu, "Set Layout Direction", self.layoutDirection, self.setLayoutDirection, {
            "Left to Right": Qt.LayoutDirection.LeftToRight,
            "Right to Left": Qt.LayoutDirection.RightToLeft,
            "Auto": Qt.LayoutDirection.LayoutDirectionAuto,
        }, "layoutDirection", param_type=Qt.LayoutDirection)

        # Accessibility
        accessibility_menu: QMenu | None = widget_menu.addMenu("Accessibility")
        assert accessibility_menu is not None
        self._add_menu_action(accessibility_menu, "Set Accessible Name", self.accessibleName, self.setAccessibleName, "accessibleName", param_type=str)
        self._add_menu_action(accessibility_menu, "Set Accessible Description", self.accessibleDescription, self.setAccessibleDescription, "accessibleDescription", param_type=str)

        # Locale
        locale_menu: QMenu | None = widget_menu.addMenu("Locale")
        assert locale_menu is not None
        self._add_menu_action(locale_menu, "Set Locale", self.locale, self.setLocale, "locale", param_type=QLocale)

        # Actions
        actions_menu: QMenu | None = widget_menu.addMenu("Actions")
        assert actions_menu is not None

        # Actions menu
        refresh_menu: QMenu | None = widget_menu.addMenu("Refresh...")
        assert refresh_menu is not None
        self._add_simple_action(refresh_menu, "Update", self.update)
        self._add_simple_action(refresh_menu, "Repaint", self.repaint)
        self._add_simple_action(actions_menu, "Raise", self.raise_)
        self._add_simple_action(actions_menu, "Lower", self.lower)
        self._add_simple_action(actions_menu, "Stack Under", lambda: self.stackUnder(self.parentWidget()))
        self._add_simple_action(actions_menu, "Move", lambda: self.move(self.x(), self.y()))
        self._add_simple_action(actions_menu, "Resize", lambda: self.resize(self.width(), self.height()))
        self._add_simple_action(actions_menu, "Adjust Size", self.adjustSize)
        self._add_simple_action(actions_menu, "Update Geometry", self.updateGeometry)
        self._add_simple_action(actions_menu, "Update", self.update)
        self._add_simple_action(actions_menu, "Repaint", self.repaint)
        self._add_simple_action(actions_menu, "Set Focus", self.setFocus)
        self._add_simple_action(actions_menu, "Clear Focus", self.clearFocus)
        self._add_simple_action(actions_menu, "Activate Window", self.activateWindow)
        self._add_simple_action(actions_menu, "Show Normal", self.showNormal)
        self._add_simple_action(actions_menu, "Show Minimized", self.showMinimized)
        self._add_simple_action(actions_menu, "Show Maximized", self.showMaximized)
        self._add_simple_action(actions_menu, "Show Full Screen", self.showFullScreen)
        self._add_simple_action(actions_menu, "Show", self.show)
        self._add_simple_action(actions_menu, "Hide", self.hide)
        self._add_simple_action(actions_menu, "Close", self.close)

        # Advanced
        advanced_menu: QMenu | None = widget_menu.addMenu("Advanced")
        assert advanced_menu is not None
        widget_attributes_menu: QMenu | None = advanced_menu.addMenu("Widget Attributes")
        assert widget_attributes_menu is not None
        for attr_name, attr_value in Qt.WidgetAttribute.__dict__.items():
            if not attr_name.startswith("WA_"):
                continue
            self._add_menu_action(
                widget_attributes_menu,
                attr_name,
                lambda v=attr_value: self.testAttribute(v),  # Example getter
                lambda b, v=attr_value: self.setAttribute(v, b),
                "setAttribute",
                param_type=bool
            )

        #meta_enum = QMetaEnum.fromType(Qt.WindowType)
        #window_type_options = {meta_enum.valueToKey(i): i for i in range(meta_enum.keyCount())}
        #self._add_multi_option_menu_action(
        #    advanced_menu,
        #    "Set Window Flag",
        #    self.windowFlags,
        #    self.setWindowFlags,
        #    {flag.name: flag for flag in Qt.WindowType},
        #    "setWindowFlag",
        #    param_type=Qt.WindowType
        #)
        if qtpy.QT5:
            self._add_menu_action(
                advanced_menu,
                "Set Input Method Hints",
                self.inputMethodHints,
                self.setInputMethodHints,
                "inputMethodHints",
                param_type=Qt.InputMethodHint,
            )
        self._add_menu_action(
            advanced_menu,
            "Set Tool Tip Duration",
            self.toolTipDuration,
            self.setToolTipDuration,
            "toolTipDuration",
            param_type=int,
        )

        assert whats_this_action is not None
        whats_this_action.triggered.connect(QWhatsThis.enterWhatsThisMode)
        whats_this_action.setToolTip("Enter 'What's This?' mode.")
        self.menu.addAction(whats_this_action)
        return self.menu

    def _add_menu_action(  # noqa: PLR0913
        self,
        menu: QMenu,
        title: str,
        get_func: Callable[[], Any],
        set_func: Callable[[Any], Any],
        settings_key: str,
        param_type: type = bool,
    ):
        current_value: Any = get_func()
        if title == "Edit Stylesheet":
            action: QAction | None = QAction(title, self)
            assert action is not None
            def on_toggled(checked: bool):
                set_func(checked)
            action.toggled.connect(on_toggled)
            menu.addAction(action)
            return
        action_title: str = title
        action = QAction(action_title, self)

        if param_type is bool:
            action.setCheckable(True)
            action.setChecked(current_value)
            def on_toggled(checked: bool):  # noqa: FBT001
                set_func(checked)
            action.toggled.connect(on_toggled)
        else:

            def on_triggered():
                self._handle_generic_action(
                    get_func,
                    set_func,
                    title,
                    settings_key,
                    param_type,
                )

            action.triggered.connect(on_triggered)
        menu.addAction(action)

    def _add_simple_action(
        self,
        menu: QMenu,
        title: str,
        func: Callable[[], Any],
    ):
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
        current_value = current_state_func()
        sub_menu: QMenu | None = menu.addMenu(title)
        assert sub_menu is not None

        action_group = QActionGroup(sub_menu)
        action_group.setExclusive(True)
        for option_name, option_value in options.items():
            action = QAction(option_name, self)
            action.setCheckable(True)
            action.setChecked(current_value == option_value)
            def on_triggered(_checked, val=option_value):
                set_func(val)
                self._update_action_text(title, val)
            action.triggered.connect(on_triggered)
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
        initial_value: Any = get_func()
        sub_menu: QMenu | None = menu.addMenu(title)
        assert sub_menu is not None

        def update_state(
            menu: QMenu = sub_menu,
        ):
            current_state = 0
            for action in menu.actions():
                if action.isChecked():
                    current_state |= options[action.text()]
            if (
                initial_value is not None
                and not isinstance(current_state, initial_value.__class__)
            ):
                current_state: Any = initial_value.__class__(current_state)
            set_func(current_state)

        if not self._initialized:
            for option_name, option_value in options.items():
                action = QAction(option_name, self)
                action.setCheckable(True)
                action.setChecked(bool(initial_value & option_value))
                action.triggered.connect(update_state)
                sub_menu.addAction(action)

    def _handle_color_action(
        self,
        get_func: Callable[[], Any],
        title: str,
        settings_key: str,
    ):
        color: QColor = QColorDialog.getColor(get_func(), self, title)
        if color.isValid():
            self.update()

    def _handle_generic_action(
        self,
        get_func: Callable[[], Any],
        set_func: Callable[[Any], Any],
        title: str,
        settings_key: str,
        param_type: type,
    ):
        get_result: Any = get_func()
        current_value: Any = get_result

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Set {title}")
        layout = QVBoxLayout(dialog)

        input_widget: QWidget = self._create_input_widget(param_type, current_value)
        layout.addWidget(input_widget)

        button_box: QDialogButtonBox | None = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        assert button_box is not None
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            new_value: Any = self._get_new_value(input_widget, param_type)
        except (ValueError, TypeError):
            QMessageBox.warning(
                self,
                "Invalid Input",
                f"Invalid input for {title}. Please enter a valid {param_type.__name__}.",
            )
            return

        try:
            set_func(new_value)
        except TypeError:
            RobustLogger().error(f"Error setting {title} to {new_value}", exc_info=True)
            return
        self._update_action_text(title, new_value)

    def _create_input_widget(
        self,
        param_type: type,
        current_value: Any,
    ) -> QWidget:
        meta_type: QMetaType.Type = get_qt_meta_type(param_type, current_value)

        if meta_type in (
            QMetaType.Type.Int,
            QMetaType.Type.Long,
            QMetaType.Type.LongLong,
        ):
            widget: QWidget = QSpinBox()
            assert widget is not None

            widget.setMinimum(-0x80000000)
            widget.setMaximum(0x7FFFFFFF)
            widget.setValue(int(current_value))  # pyright: ignore[reportArgumentType]
        elif meta_type in (QMetaType.Type.Float, QMetaType.Type.Double):
            widget = QDoubleSpinBox()
            assert widget is not None
            widget.setMinimum(-0x80000000)
            widget.setMaximum(0x7FFFFFFF)
            widget.setValue(float(current_value))  # pyright: ignore[reportArgumentType]
        elif meta_type == QMetaType.Type.Bool:
            widget = QCheckBox()
            assert widget is not None
            widget.setChecked(bool(current_value))
        elif meta_type == QMetaType.Type.QString:
            widget = QLineEdit(str(current_value))
            assert widget is not None
        elif meta_type == QMetaType.Type.QColor:
            widget = QLineEdit(current_value.name() if isinstance(current_value, QColor) else str(current_value))
        elif meta_type == QMetaType.Type.QDate:
            widget = QDateEdit(current_value)  # pyright: ignore[reportArgumentType, reportCallIssue]
            assert widget is not None
        elif meta_type == QMetaType.Type.QTime:
            widget = QTimeEdit(current_value)  # pyright: ignore[reportArgumentType, reportCallIssue]
            assert widget is not None
        elif meta_type == QMetaType.Type.QDateTime:
            widget = QDateTimeEdit(current_value)  # pyright: ignore[reportArgumentType, reportCallIssue]
            assert widget is not None
        elif meta_type == QMetaType.Type.QSize:
            if isinstance(current_value, QSize):
                widget = QLineEdit(f"{current_value.width()},{current_value.height()}")
                assert widget is not None
            else:
                widget = QLineEdit()
                assert widget is not None
        elif meta_type == QMargins and isinstance(current_value, QMargins):
            widget = QLineEdit(f"{current_value.left()},{current_value.top()},{current_value.right()},{current_value.bottom()}")
        elif hasattr(param_type, "__members__"):  # Enum type
            widget = QComboBox()
            assert widget is not None
            widget.addItems(param_type.__members__.keys())
            widget.setCurrentText(current_value.name if hasattr(current_value, "name") else str(current_value))
        else:
            widget = QLineEdit(str(current_value))
            assert widget is not None

        return widget

    def _get_new_value(
        self,
        input_widget: QWidget,
        param_type: type,
    ) -> Any:
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

    def _update_action_text(
        self,
        title: str,
        new_value: Any,
    ):
        action: QObject | None = self.sender()
        if isinstance(action, QAction):
            if isinstance(new_value, QMargins):
                value_str: str = f"{new_value.left()},{new_value.top()},{new_value.right()},{new_value.bottom()}"
            else:
                value_str = str(new_value)
            value_str = value_str[:10]  # Limit to 10 characters
            action.setText(f"{title}: {value_str}")

    def show_stylesheet_editor(self,):
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
            text_doc: QTextDocument | None = self._stylesheet_text_edit.document()
            assert text_doc is not None

            self._highlighter: StyleSheetHighlighter | None = StyleSheetHighlighter(text_doc)
            assert self._highlighter is not None

            splitter.addWidget(preview_widget)
            splitter.addWidget(self._stylesheet_text_edit)

            # Buttons
            button_layout: QHBoxLayout | None = QHBoxLayout()
            assert button_layout is not None

            apply_button: QPushButton | None = QPushButton("Apply")
            assert apply_button is not None

            apply_button.clicked.connect(lambda: self._apply_stylesheet(set_func, settings_key))
            reset_button: QPushButton | None = QPushButton("Reset")

            assert reset_button is not None
            reset_button.clicked.connect(lambda: self._reset_stylesheet(get_func))
            color_picker_button: QPushButton | None = QPushButton("Color Picker")
            assert color_picker_button is not None
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

    def _update_stylesheet_preview(self,):
        if hasattr(self, "_preview_area"):
            self._preview_area.setStyleSheet(self._stylesheet_text_edit.toPlainText())

    def _apply_stylesheet(
        self,
        set_func: Callable[[Any], Any],
        settings_key: str,
    ):
        new_stylesheet: str = self._stylesheet_text_edit.toPlainText()
        set_func(new_stylesheet)
        if hasattr(self, "_preview_area"):
            self._preview_area.setStyleSheet(new_stylesheet)

    def _reset_stylesheet(
        self,
        get_func: Callable[[], Any],
    ):
        self._stylesheet_text_edit.setPlainText(get_func())
        if hasattr(self, "_preview_area"):
            self._preview_area.setStyleSheet(get_func())

    def _show_color_picker(self):
        color: QColor = QColorDialog.getColor(parent=self)
        if color.isValid():
            cursor: QTextCursor = self._stylesheet_text_edit.textCursor()
            cursor.insertText(color.name())


if __name__ == "__main__":
    class TestWidget(RobustBaseWidget, QWidget):
        def __init__(
            self,
            parent: QWidget | None = None,
            flags: Qt.WindowType | None = None,
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
            self.label: QLabel = QLabel("Test Widget")
            self.button: QPushButton = QPushButton("Click Me")
            self.text_edit: QTextEdit = QTextEdit()

            # Add buttons to test menu actions
            action_layout: QHBoxLayout | None = QHBoxLayout()
            assert action_layout is not None
            self.test_color_action: QPushButton | None = QPushButton("Test Color Action")
            assert self.test_color_action is not None
            self.test_generic_action: QPushButton | None = QPushButton("Test Generic Action")
            assert self.test_generic_action is not None
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
            self.build_context_menu().exec()

        def test_color_action_method(self):
            def get_color() -> Qt.GlobalColor:
                return Qt.GlobalColor.red
            self._handle_color_action(get_color, "Test Color", "testColorSetting")

        def test_generic_action_method(self):
            def new_value() -> Literal[10]:
                return 10
            def update_text(x):
                self.text_edit.setText(f"New value: {x}")
            self._handle_generic_action(new_value, update_text, "Test Generic", "testGenericSetting", param_type=int)

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setCentralWidget(TestWidget(self))
            self.setGeometry(100, 100, 400, 300)
            self.setWindowTitle("RobustBaseWidget Test")

    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
