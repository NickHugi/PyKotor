from __future__ import annotations

import ast

from contextlib import suppress
from typing import TYPE_CHECKING, Any, Callable, cast

import qtpy

from qtpy import QtCore
from qtpy.QtCore import QMargins, QMetaType, QModelIndex, QObject, QPoint, QSettings, QSize, QTimer, Qt
from qtpy.QtGui import QColor, QCursor, QPalette
from qtpy.QtWidgets import (
    QAbstractItemView,
    QAbstractScrollArea,
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
    QDoubleSpinBox,
    QFrame,
    QHeaderView,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStyle,
    QStyleOptionViewItem,
    QTimeEdit,
    QVBoxLayout,
    QWhatsThis,
    QWidget,
)

from utility.ui_libraries.qt.debug.print_qobject import format_qt_obj
from utility.ui_libraries.qt.widgets.itemviews.html_delegate import HTMLDelegate

if TYPE_CHECKING:
    from qtpy.QtCore import QAbstractItemModel
    from qtpy.QtGui import QResizeEvent, QWheelEvent
    from qtpy.QtWidgets import QAbstractItemDelegate, QStyledItemDelegate
    from typing_extensions import Literal


# sip does not support multiple inheritence structures like this.
# I have no idea why, but it doesn't work. Function calls would just say 'class x not supported for function y'.
# This is a nice workaround for getting type hints working, at least. It's assumed
# that the subclasses will inherit the real qt views before they call the function anyway.
class RobustBaseWidget(QWidget if TYPE_CHECKING else object):
    def __init__(self, parent: QWidget | None = None, *, settings_name: str | None = None):
        super().__init__(parent)
        self._settings_name: str = settings_name or self.__class__.__name__
        self._settings_cache: dict[str, QSettings] = {}
        self.original_stylesheet: str = self.styleSheet()

    def _get_settings(self, class_name: str) -> QSettings:
        if class_name not in self._settings_cache:
            self._settings_cache[class_name] = QSettings("QtCustomWidgets", class_name)
        return self._settings_cache[class_name]

    def get_setting(self, key: str, default: Any, val_type: type | None = None) -> Any:
        # First check settings for _settings_name
        settings = self._get_settings(self._settings_name)
        value = settings.value(key, default) if val_type is None else settings.value(key, default, val_type)
        if value is not None:
            return value

        # Then check the class hierarchy
        for cls in self.__class__.__mro__:
            if cls is QAbstractItemView:
                break
            if cls.__name__ == self._settings_name:
                continue  # Skip, as we've already checked this
            value = self._get_settings(cls.__name__).value(key, None)
            if value is not None:
                return value
        return default

    def set_setting(self, key: str, value: Any):
        settings = self._get_settings(self._settings_name)
        settings.setValue(key, value)

    def _init_setting(self, get_func: Callable[[], Any], set_func: Callable[[Any], Any], settings_key: str) -> Any:
        current_value = get_func()
        initial_value = self.get_setting(settings_key, current_value, current_value.__class__)
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
            settings_value = bool(setting_value)
            action.setChecked(settings_value)
            set_func(settings_value)  # Apply the initial value from settings
            action.toggled.connect(lambda checked: [set_func(checked), self.set_setting(settings_key, checked)])
        else:
            action.triggered.connect(lambda: self._handle_generic_action(get_func, set_func, title, settings_key, param_type))
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
    ):
        initial_value = self._init_setting(current_state_func, set_func, settings_key)
        sub_menu = menu.addMenu(title)
        action_group = QActionGroup(self)
        action_group.setExclusive(True)
        for option_name, option_value in options.items():
            action = QAction(option_name, self)
            action.setCheckable(True)
            action.setChecked(initial_value == option_value)
            action.triggered.connect(lambda checked, val=option_value: [set_func(val), self.set_setting(settings_key, val)] if checked else None)
            sub_menu.addAction(action)
            action_group.addAction(action)

    def _add_multi_option_menu_action(self, menu: QMenu, title: str, get_func: Callable[[], Any], set_func: Callable[[Any], Any], options: dict[str, Any], settings_key: str):  # noqa: PLR0913
        initial_value = self._init_setting(get_func, set_func, settings_key)
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
        elif param_type == QMargins:
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


class RobustAbstractItemView(RobustBaseWidget, QAbstractItemView if TYPE_CHECKING else object):
    def __init__(self, parent: QWidget | None = None, *, settings_name: str | None = None):
        super().__init__(parent, settings_name=settings_name)
        self.layout_changed_debounce_timer: QTimer = QTimer(self)
        self.setup_backup_menu_when_header_hidden()

    def setup_backup_menu_when_header_hidden(self):
        corner_button = QPushButton("☰", self)
        corner_button.setFixedSize(20, 20)
        corner_button.clicked.connect(lambda _some_bool_qt_is_sending: self.show_header_context_menu())
        corner_button.setToolTip("Show context menu")
        layout = QVBoxLayout(self)
        layout.addWidget(corner_button, alignment=Qt.AlignTop | Qt.AlignRight)
        layout.setContentsMargins(0, 0, 0, 0)
        self.__class__.setLayout(self, layout)

    def show_header_context_menu(self, pos: QPoint | None = None):
        menu = self.build_context_menu()
        header = getattr(self, "header", None)
        if header is not None and callable(header):
            pos = cast(QHeaderView, header).mapToGlobal(QPoint(0, cast(QHeaderView, header).height()))
        elif pos is None:
            pos = QCursor.pos()
        menu.exec_(pos)

    def itemDelegate(self) -> HTMLDelegate | QStyledItemDelegate | QAbstractItemDelegate:
        return super().itemDelegate()

    def setItemDelegate(self, delegate: HTMLDelegate | QStyledItemDelegate):
        assert isinstance(delegate, HTMLDelegate)
        super().setItemDelegate(delegate)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.debounce_layout_changed()

    def wheelEvent(
        self,
        event: QWheelEvent,
    ) -> None:
        modifiers = event.modifiers()
        handled = False

        if bool(modifiers & Qt.KeyboardModifier.ShiftModifier) and bool(modifiers & Qt.KeyboardModifier.ControlModifier):
            handled = self._wheel_changes_item_spacing(event)
        elif bool(modifiers & Qt.KeyboardModifier.ControlModifier):
            handled = self._wheel_changes_text_size(event)
        elif (not int(modifiers)) if qtpy.QT5 else (modifiers != Qt.KeyboardModifier.NoModifier):
            handled = self._wheel_changes_vertical_scroll(event)

        if not handled:
            super().wheelEvent(event)

    def _wheel_changes_item_spacing(self, event: QWheelEvent) -> bool:
        delta: int = event.angleDelta().y()
        if not delta:
            return False
        item_delegate: HTMLDelegate | QStyledItemDelegate | QAbstractItemDelegate = self.itemDelegate()
        if isinstance(item_delegate, HTMLDelegate):
            single_step: Literal[-1, 1] = 1 if delta > 0 else -1
            new_vertical_spacing: int = max(0, item_delegate.customVerticalSpacing + single_step)
            item_delegate.setVerticalSpacing(new_vertical_spacing)
            self.emit_layout_changed()  # Requires immediate update
            return True
        return False

    def _wheel_changes_text_size(self, event: QWheelEvent) -> bool:
        delta: int = event.angleDelta().y()
        if not delta:
            return False
        self.set_text_size(self.get_text_size() + (1 if delta > 0 else -1))
        return True

    def _wheel_changes_vertical_scroll(self, event: QWheelEvent) -> bool:
        delta: int = event.angleDelta().y()
        # print("wheelVerticalScroll, delta: ", delta)
        if not delta:
            return True
        self.scroll_multiple_steps("up" if delta > 0 else "down")
        return True

    def _handle_color_action(self, get_func: Callable[[], Any], title: str, settings_key: str):
        super()._handle_color_action(get_func, title, settings_key)
        self.debounce_layout_changed()
        self.viewport().update()

    def build_header_context_menu(self) -> QMenu:
        """Subclass should override this to add header-specific actions."""
        header_menu = QMenu("Header")
        return header_menu

    def build_context_menu(self) -> QMenu:
        context_menu = QMenu(self)
        advanced_menu = context_menu.addMenu("Advanced")
        context_menu.insertMenu(context_menu.actions()[0], self.build_header_context_menu())

        # Display menu
        display_menu = context_menu.addMenu("Display")
        self._add_menu_action(
            display_menu,
            "Alternating Row Colors",
            self.alternatingRowColors,
            self.setAlternatingRowColors,
            settings_key="alternatingRowColors",
        )

        # Advanced submenu for Display
        display_advanced_menu = display_menu.addMenu("Advanced")
        self._add_exclusive_menu_action(
            display_advanced_menu,
            "Text Elide Mode",
            self.textElideMode,
            lambda x: self.setTextElideMode(Qt.TextElideMode(x)),
            options={
                "Elide Left": Qt.TextElideMode.ElideLeft,
                "Elide Right": Qt.TextElideMode.ElideRight,
                "Elide Middle": Qt.TextElideMode.ElideMiddle,
                "Elide None": Qt.TextElideMode.ElideNone,
            },
            settings_key="textElideMode",
        )

        self._add_menu_action(
            display_menu,
            "Font Size",
            self.get_text_size,
            self.set_text_size,
            settings_key="fontSize",
            param_type=int,
        )
        self._add_color_menu_action(
            display_menu,
            "Text Color",
            lambda: QColor(self.get_setting("textColor", QApplication.palette().color(QPalette.ColorRole.Text))),
            settings_key="textColor",
        )
        self._add_menu_action(
            display_menu,
            "Icon Size",
            self.iconSize,
            self.setIconSize,
            settings_key="iconSize",
            param_type=QtCore.QSize,
        )
        self._add_menu_action(
            display_menu,
            "Show Drop Indicator",
            self.showDropIndicator,
            self.setDropIndicatorShown,
            settings_key="showDropIndicator",
        )

        self._add_exclusive_menu_action(
            advanced_menu,
            "Edit Triggers",
            self.editTriggers,
            self.setEditTriggers,
            options={
                "No Edit Triggers": QAbstractItemView.EditTrigger.NoEditTriggers,
                "Current Changed": QAbstractItemView.EditTrigger.CurrentChanged,
                "Double Clicked": QAbstractItemView.EditTrigger.DoubleClicked,
                "Selected Clicked": QAbstractItemView.EditTrigger.SelectedClicked,
                "Edit Key Pressed": QAbstractItemView.EditTrigger.EditKeyPressed,
                "Any Key Pressed": QAbstractItemView.EditTrigger.AnyKeyPressed,
                "All Edit Triggers": QAbstractItemView.EditTrigger.AllEditTriggers,
            },
            settings_key="editTriggers",
        )

        # Drag and Drop menu
        self._add_exclusive_menu_action(
            advanced_menu,
            "Selection Mode",
            self.selectionMode,
            self.setSelectionMode,
            options={
                "No Selection": QAbstractItemView.SelectionMode.NoSelection,
                "Single Selection": QAbstractItemView.SelectionMode.SingleSelection,
                "Multi Selection": QAbstractItemView.SelectionMode.MultiSelection,
                "Extended Selection": QAbstractItemView.SelectionMode.ExtendedSelection,
                "Contiguous Selection": QAbstractItemView.SelectionMode.ContiguousSelection,
            },
            settings_key="selectionMode",
        )
        self._add_exclusive_menu_action(
            advanced_menu,
            "Selection Behavior",
            self.selectionBehavior,
            self.setSelectionBehavior,
            options={
                "Select Items": QAbstractItemView.SelectionBehavior.SelectItems,
                "Select Rows": QAbstractItemView.SelectionBehavior.SelectRows,
                "Select Columns": QAbstractItemView.SelectionBehavior.SelectColumns,
            },
            settings_key="selectionBehavior",
        )
        drag_drop_menu = advanced_menu.addMenu("Drag and Drop")
        self._add_exclusive_menu_action(
            drag_drop_menu,
            "Drag Drop Mode",
            self.dragDropMode,
            self.setDragDropMode,
            options={
                "No Drag Drop": QAbstractItemView.DragDropMode.NoDragDrop,
                "Drag Only": QAbstractItemView.DragDropMode.DragOnly,
                "Drop Only": QAbstractItemView.DragDropMode.DropOnly,
                "Drag Drop": QAbstractItemView.DragDropMode.DragDrop,
                "Internal Move": QAbstractItemView.DragDropMode.InternalMove,
            },
            settings_key="dragDropMode",
        )
        self._add_menu_action(
            drag_drop_menu,
            "Drag Enabled",
            self.dragEnabled,
            self.setDragEnabled,
            settings_key="dragEnabled",
        )
        self._add_menu_action(
            drag_drop_menu,
            "Drag Drop Overwrite Mode",
            self.dragDropOverwriteMode,
            self.setDragDropOverwriteMode,
            settings_key="dragDropOverwriteMode",
        )
        self._add_exclusive_menu_action(
            drag_drop_menu,
            "Default Drop Action",
            self.defaultDropAction,
            self.setDefaultDropAction,
            options={
                "Copy Action": Qt.DropAction.CopyAction,
                "Move Action": Qt.DropAction.MoveAction,
                "Link Action": Qt.DropAction.LinkAction,
                "Ignore Action": Qt.DropAction.IgnoreAction,
            },
            settings_key="defaultDropAction",
        )

        # Behavior menu
        behavior_menu = context_menu.addMenu("Behavior")
        self._add_menu_action(
            behavior_menu,
            "Tab Key Navigation",
            self.tabKeyNavigation,
            self.setTabKeyNavigation,
            settings_key="tabKeyNavigation",
        )
        behavior_advanced_menu = behavior_menu.addMenu("Advanced")
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
        )
        self._add_menu_action(
            behavior_menu,
            "Auto Fill Background",
            self.autoFillBackground,
            self.setAutoFillBackground,
            settings_key="autoFillBackground",
        )
        self._add_exclusive_menu_action(
            behavior_advanced_menu,
            "Frame Shape",
            self.frameShape,
            self.setFrameShape,
            options={
                "No Frame": QFrame.Shape.NoFrame,
                "Box": QFrame.Shape.Box,
                "Panel": QFrame.Shape.Panel,
                "Win Panel": QFrame.Shape.WinPanel,
                "HLine": QFrame.Shape.HLine,
                "VLine": QFrame.Shape.VLine,
                "StyledPanel": QFrame.Shape.StyledPanel,
            },
            settings_key="frameShape",
        )
        self._add_exclusive_menu_action(
            behavior_advanced_menu,
            "Frame Shadow",
            self.frameShadow,
            self.setFrameShadow,
            options={
                "Plain": QFrame.Shadow.Plain,
                "Raised": QFrame.Shadow.Raised,
                "Sunken": QFrame.Shadow.Sunken,
            },
            settings_key="frameShadow",
        )
        self._add_menu_action(
            behavior_menu,
            "Line Width",
            self.lineWidth,
            self.setLineWidth,
            settings_key="lineWidth",
            param_type=int,
        )
        self._add_menu_action(
            behavior_menu,
            "Mid Line Width",
            self.midLineWidth,
            self.setMidLineWidth,
            settings_key="midLineWidth",
            param_type=int,
        )

        # Scroll menu
        behavior_menu.addSeparator()
        self._add_menu_action(
            behavior_menu,
            "Scroll Step Size",
            lambda: self.get_setting("scrollStepSize", QApplication.wheelScrollLines()),
            self.set_scroll_step_size,
            settings_key="scrollStepSize",
            param_type=int,
        )
        self._add_exclusive_menu_action(
            behavior_menu,
            "Horizontal Scroll Mode",
            self.horizontalScrollMode,
            self.setHorizontalScrollMode,
            options={
                "Scroll Per Item": QAbstractItemView.ScrollMode.ScrollPerItem,
                "Scroll Per Pixel": QAbstractItemView.ScrollMode.ScrollPerPixel,
            },
            settings_key="horizontalScrollMode",
        )
        self._add_exclusive_menu_action(
            behavior_menu,
            "Vertical Scroll Mode",
            self.verticalScrollMode,
            self.setVerticalScrollMode,
            options={
                "Scroll Per Item": QAbstractItemView.ScrollMode.ScrollPerItem,
                "Scroll Per Pixel": QAbstractItemView.ScrollMode.ScrollPerPixel,
            },
            settings_key="verticalScrollMode",
        )
        scroll_advanced_menu = behavior_menu.addMenu("Advanced")
        self._add_menu_action(
            scroll_advanced_menu,
            "Auto Scroll",
            self.hasAutoScroll,
            self.setAutoScroll,
            settings_key="autoScroll",
        )
        self._add_menu_action(
            scroll_advanced_menu,
            "Auto Scroll Margin",
            self.autoScrollMargin,
            self.setAutoScrollMargin,
            settings_key="autoScrollMargin",
            param_type=int,
        )

        # Size Adjustment menu
        self._add_exclusive_menu_action(
            advanced_menu,
            "Size Adjust Policy",
            self.sizeAdjustPolicy,
            self.setSizeAdjustPolicy,
            options={
                "Adjust Ignored": QAbstractScrollArea.SizeAdjustPolicy.AdjustIgnored,
                "Adjust To Contents On First Show": QAbstractScrollArea.SizeAdjustPolicy.AdjustToContentsOnFirstShow,
                "Adjust To Contents": QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents,
            },
            settings_key="sizeAdjustPolicy",
        )

        # Viewport menu
        viewport_menu = context_menu.addMenu("Viewport")
        self._add_menu_action(
            viewport_menu,
            "Viewport Margins",
            self.viewportMargins,
            lambda m: self.setViewportMargins(
                cast(QtCore.QMargins, m).left(), cast(QtCore.QMargins, m).top(), cast(QtCore.QMargins, m).right(), cast(QtCore.QMargins, m).bottom()
            ),
            settings_key="viewportMargins",
            param_type=QtCore.QMargins,
        )
        self._add_menu_action(
            viewport_menu,
            "Auto Fill Background",
            self.autoFillBackground,
            self.setAutoFillBackground,
            settings_key="autoFillBackground",
        )

        # Actions menu
        refresh_menu = context_menu.addMenu("Refresh...")
        self._add_simple_action(refresh_menu, "Update", self.update)
        self._add_simple_action(refresh_menu, "Repaint", self.repaint)
        self._add_simple_action(refresh_menu, "Update Geometries", self.updateGeometries)
        self._add_simple_action(refresh_menu, "Reset View", self.reset)
        self._add_simple_action(refresh_menu, "Clear Selection", self.clearSelection)
        self._add_simple_action(refresh_menu, "Select All", self.selectAll)

        # Help menu
        whats_this_action = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarContextHelpButton), "What's This?", self)
        whats_this_action.triggered.connect(QWhatsThis.enterWhatsThisMode)
        whats_this_action.setToolTip("Enter 'What's This?' mode.")
        context_menu.addAction(whats_this_action)

        return context_menu

    def set_text_size(self, size: int):
        delegate = self.itemDelegate()
        if isinstance(delegate, HTMLDelegate):
            text_size = max(1, size)
            model: QAbstractItemModel | None = self.model()
            assert model is not None
            delegate.set_text_size(text_size)
            self.update_columns_after_text_size_change()
        else:
            font = self.font()
            font.setPointSize(max(1, size))
            self.setFont(font)
            self.updateGeometry()
        self.debounce_layout_changed()

    def get_text_size(self) -> int:
        delegate = self.itemDelegate()
        return delegate.text_size if isinstance(delegate, HTMLDelegate) else self.font().pointSize()

    def update_columns_after_text_size_change(self):
        """This method should be implemented by subclasses if needed."""

    def emit_layout_changed(self):
        model = self.model()
        if model is not None:
            model.layoutChanged.emit()

    def debounce_layout_changed(self, timeout: int = 100, *, pre_change_emit: bool = False):
        self.viewport().update()
        # self.update()
        if self.layout_changed_debounce_timer.isActive():
            self.layout_changed_debounce_timer.stop()
        elif pre_change_emit:
            self.model().layoutAboutToBeChanged.emit()
        self.layout_changed_debounce_timer.start(timeout)

    def set_scroll_step_size(self, value: int):
        """Set the number of items to scroll per wheel event."""
        print(f"scrollStepSize set to {value}")
        self.set_setting("scrollStepSize", value)

    def scroll_multiple_steps(self, direction: Literal["up", "down"]):
        """Scroll multiple steps based on the user-defined setting.

        Determines what a 'step' is by checking `self.verticalScrollMode()`
        and multiplies it by the user-defined number of items to scroll.
        """
        vertScrollBar = self.verticalScrollBar()
        assert vertScrollBar is not None
        step_size = self.get_setting("scrollStepSize", 1)

        if self.verticalScrollMode() == QAbstractItemView.ScrollMode.ScrollPerItem:
            if qtpy.QT5:
                action = vertScrollBar.SliderSingleStepSub if direction == "up" else vertScrollBar.SliderSingleStepAdd
            else:
                action = vertScrollBar.SliderAction.SliderSingleStepSub if direction == "up" else vertScrollBar.SliderAction.SliderSingleStepAdd
            for _ in range(step_size):
                vertScrollBar.triggerAction(action)
        else:
            scrollStep = -self.get_text_size() if direction == "up" else self.get_text_size()
            vertScrollBar.setValue(vertScrollBar.value() + scrollStep * step_size)

    def styleOptionForIndex(self, index: QModelIndex) -> QStyleOptionViewItem:
        option = QStyleOptionViewItem()
        if index.isValid():
            option.initFrom(self)
            if self.selectionModel().isSelected(index):
                option.state |= QStyle.StateFlag.State_Selected
            if index == self.currentIndex() and self.hasFocus():
                option.state |= QStyle.StateFlag.State_HasFocus
            if not self.isEnabled():
                option.state = cast(QStyle.StateFlag, option.state & ~QStyle.StateFlag.State_Enabled)
            checkStateData = index.data(Qt.ItemDataRole.CheckStateRole)
            option.checkState = Qt.CheckState.Unchecked if checkStateData is None else checkStateData
            option.displayAlignment = Qt.AlignLeft | Qt.AlignVCenter
            option.index = index
            option.text = index.data(Qt.ItemDataRole.DisplayRole)
        return option

    def get_identifying_text(self, index_or_item: QModelIndex | None) -> str:  # noqa: N803
        if index_or_item is None:
            return "(None)"
        if not isinstance(index_or_item, QModelIndex):
            return f"(Unknown index/item: {index_or_item})"
        if not index_or_item.isValid():
            return f"(invalid index at row '{index_or_item.row()}', column '{index_or_item.column()}')"

        text = index_or_item.data(Qt.ItemDataRole.DisplayRole)
        if isinstance(text, str):
            text = text.strip()
        else:
            text = str(text)
        parent_count = 0
        current_index = index_or_item.parent()
        while current_index.isValid():
            parent_count += 1
            current_index = current_index.parent()

        return f"Item/Index at Row: {index_or_item.row()}, Column: {index_or_item.column()}, Ancestors: {parent_count}\nText for above item: {text}\n"
