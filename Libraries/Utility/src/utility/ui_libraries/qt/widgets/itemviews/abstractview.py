from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, cast

import qtpy

from qtpy import QtCore
from qtpy.QtCore import QModelIndex, QPoint, QTimer, Qt
from qtpy.QtGui import QColor, QCursor, QPalette
from qtpy.QtWidgets import (
    QAbstractItemView,
    QAbstractScrollArea,
    QAction,
    QApplication,
    QFrame,
    QMenu,
    QPushButton,
    QStyle,
    QStyleOptionViewItem,
    QStyledItemDelegate,
    QWhatsThis,
)

from utility.ui_libraries.qt.widgets.itemviews.baseview import RobustBaseWidget
from utility.ui_libraries.qt.widgets.itemviews.html_delegate import HTMLDelegate

if TYPE_CHECKING:
    from qtpy.QtCore import QAbstractItemModel
    from qtpy.QtGui import QResizeEvent, QWheelEvent
    from qtpy.QtWidgets import (
        QAbstractItemDelegate,
        QWidget,
    )
    from typing_extensions import Literal


class RobustAbstractItemView(RobustBaseWidget, QAbstractItemView if TYPE_CHECKING else object):
    def __init__(self, parent: QWidget | None = None, *, settings_name: str | None = None):
        super().__init__(parent, settings_name=settings_name)
        self.layout_changed_debounce_timer: QTimer = QTimer(self)
        self.setup_backup_menu_when_header_hidden()

    def setup_backup_menu_when_header_hidden(self):
        self.corner_button = QPushButton("☰", self)
        self.corner_button.setFixedSize(20, 20)
        self.corner_button.clicked.connect(lambda _some_bool_qt_is_sending: self.show_header_context_menu())
        self.corner_button.setToolTip("Show context menu")
        if self.verticalScrollBar().isVisible():
            self.corner_button.move(self.width() - self.corner_button.width() - self.verticalScrollBar().width(), 0)
        else:
            self.corner_button.move(self.width() - self.corner_button.width(), 0)
        self.corner_button.show()

    def show_header_context_menu(self, pos: QPoint | None = None, parent: QWidget | None = None):
        print(f"{self.__class__.__name__}.show_header_context_menu")
        menu = self.build_context_menu(parent)
        if parent is not None:
            pos = parent.mapToGlobal(QPoint(0, parent.height()))
        elif pos is None:
            pos = QCursor.pos()
        menu.exec_(pos)

    def itemDelegate(self) -> QStyledItemDelegate:
        return super().itemDelegate()  # pyright: ignore[reportReturnType]

    def setItemDelegate(self, delegate: QStyledItemDelegate):
        assert isinstance(delegate, QStyledItemDelegate), f"Expected QStyledItemDelegate, got {type(delegate).__name__}."
        super().setItemDelegate(delegate)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.debounce_layout_changed()
        if self.verticalScrollBar().isVisible():
            self.corner_button.move(self.width() - self.corner_button.width() - self.verticalScrollBar().width(), 0)
        else:
            self.corner_button.move(self.width() - self.corner_button.width(), 0)
        self.corner_button.show()

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

    def build_header_context_menu(self, parent: QWidget | None = None) -> QMenu:
        """Subclass should override this to add header-specific actions."""
        return QMenu("Header", self if parent is None else parent)

    def build_context_menu(self, parent: QWidget | None = None) -> QMenu:
        print(f"{self.__class__.__name__}.build_context_menu")
        parent = self if parent is None else parent
        context_menu = QMenu(parent)
        advanced_menu = context_menu.addMenu("Advanced")
        context_menu.insertMenu(context_menu.actions()[0], self.build_header_context_menu(parent))

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
            param_type=QAbstractItemView.EditTrigger,
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
            param_type=QAbstractItemView.SelectionMode,
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
            param_type=QAbstractItemView.SelectionBehavior,
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
            param_type=QAbstractItemView.DragDropMode,
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
            param_type=Qt.DropAction,
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
            param_type=Qt.FocusPolicy,
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
            param_type=QFrame.Shape,
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
            param_type=QFrame.Shadow,
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
            param_type=QAbstractItemView.ScrollMode,
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
            param_type=QAbstractItemView.ScrollMode,
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
            param_type=QAbstractScrollArea.SizeAdjustPolicy,
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
