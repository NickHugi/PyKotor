from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, cast

from loggerplus import RobustLogger
from qtpy import QtCore
from qtpy.QtCore import QAbstractItemModel, QSortFilterProxyModel, QTimer, Qt
from qtpy.QtGui import QCursor
from qtpy.QtWidgets import QAbstractItemDelegate, QAbstractItemView, QAbstractScrollArea, QFrame, QMenu, QStyle, QStyleOptionViewItem

from utility.ui_libraries.qt.widgets.itemviews.baseview import RobustBaseWidget
from utility.ui_libraries.qt.widgets.itemviews.html_delegate import HTMLDelegate

if TYPE_CHECKING:
    from qtpy.QtCore import QAbstractItemModel, QItemSelectionModel, QMargins, QModelIndex, QPoint
    from qtpy.QtGui import QFont, QResizeEvent, QWheelEvent
    from qtpy.QtWidgets import QAbstractItemDelegate, QMenu, QScrollBar, QWidget
    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]


class RobustAbstractItemView(RobustBaseWidget, QAbstractItemView if TYPE_CHECKING else object):
    def __init__(
        self,
        parent: QWidget | None = None,
        *args,
        **kwargs,
    ):
        RobustBaseWidget.__init__(self, parent, *args, **kwargs)
        self._layout_changed_debounce_timer: QTimer = QTimer(self)
        self._fix_drawer_button()

    def _create_drawer_button(self):
        super()._create_drawer_button()
        self._robust_drawer.clicked.connect(lambda _: self.show_header_context_menu())

    def debounce_layout_changed(
        self,
        timeout: int = 100,
        *,
        pre_change_emit: bool = False,
    ):
        view_port: QWidget | None = self.viewport()
        assert view_port is not None
        view_port.update()
        if self._layout_changed_debounce_timer.isActive():
            self._layout_changed_debounce_timer.stop()
        elif pre_change_emit:
            view_model: QAbstractItemModel | None = self.model()
            assert view_model is not None
            view_model.layoutAboutToBeChanged.emit()
        self._layout_changed_debounce_timer.start(timeout)

    def setParent(
        self,
        parent: QWidget,
        f: Qt.WindowType | None = None,
    ) -> None:
        super().setParent(parent) if f is None else super().setParent(parent, f)

    def _fix_drawer_button(self):
        if not hasattr(self, "_robust_drawer"):
            self._create_drawer_button()
            self._robust_drawer.show()
        vert_scroll_bar: QScrollBar | None = self.verticalScrollBar()
        assert vert_scroll_bar is not None
        if vert_scroll_bar.isVisible():
            self._robust_drawer.move(
                self.width() - self._robust_drawer.width() - vert_scroll_bar.width(),
                0,
            )
        else:
            self._robust_drawer.move(self.width() - self._robust_drawer.width(), 0)

    def show_header_context_menu(
        self,
        pos: QPoint | None = None,
        parent: QWidget | None = None,
    ):
        menu = self.build_context_menu()
        menu.exec(QCursor.pos())

    def selected_source_indexes(self) -> list[QModelIndex]:
        """Same as QAbstractItemView.selectedIndexes, but returns the source indexes instead of the proxy model indexes."""
        indexes: list[QModelIndex] = []
        current_model: QAbstractItemModel | None = self.model()
        for index in self.selectedIndexes():
            sourceIndex: QModelIndex = (
                current_model.mapToSource(index)  # pyright: ignore[reportArgumentType]
                if isinstance(current_model, QSortFilterProxyModel)
                else index
            )
            if not sourceIndex.isValid():
                RobustLogger().warning("Invalid source index for row %d", index.row())
                continue
            indexes.append(sourceIndex)
        return indexes

    def resizeEvent(
        self,
        event: QResizeEvent,
    ):
        super().resizeEvent(event)
        self.debounce_layout_changed()
        self._fix_drawer_button()

    def wheelEvent(
        self,
        event: QWheelEvent,
    ) -> None:
        modifiers: Qt.KeyboardModifier = event.modifiers()
        handled: bool = False

        if bool(modifiers & Qt.KeyboardModifier.ShiftModifier) and bool(modifiers & Qt.KeyboardModifier.ControlModifier):
            handled = self._wheel_changes_item_spacing(event)
        elif bool(modifiers & Qt.KeyboardModifier.ControlModifier):
            handled = self._wheel_changes_text_size(event)

        if not handled:
            super().wheelEvent(event)

    def _wheel_changes_item_spacing(
        self,
        event: QWheelEvent,
    ) -> bool:
        delta: int = event.angleDelta().y()
        if not delta:
            return False
        item_delegate: QAbstractItemDelegate | None = self.itemDelegate()
        if isinstance(item_delegate, HTMLDelegate):
            single_step: Literal[-1, 1] = 1 if delta > 0 else -1
            new_vertical_spacing: int = max(0, item_delegate.custom_vertical_spacing + single_step)
            item_delegate.setVerticalSpacing(new_vertical_spacing)
            self.emit_layout_changed()  # Requires immediate update
            return True
        return False

    def _wheel_changes_text_size(
        self,
        event: QWheelEvent,
    ) -> bool:
        delta: int = event.angleDelta().y()
        if not delta:
            return False
        self.set_text_size(self.get_text_size() + (1 if delta > 0 else -1))
        return True

    def _handle_color_action(
        self,
        get_func: Callable[[], Any],
        title: str,
        settings_key: str,
    ):
        super()._handle_color_action(get_func, title, settings_key)
        self.debounce_layout_changed()
        view_port: QWidget | None = self.viewport()
        assert view_port is not None
        view_port.update()

    def set_text_size(self, size: int):
        delegate: QAbstractItemDelegate | None = self.itemDelegate()
        if isinstance(delegate, HTMLDelegate):
            text_size: int = max(1, size)
            model: QAbstractItemModel | None = self.model()
            assert model is not None
            delegate.set_text_size(text_size)
            self.update_columns_after_text_size_change()
        else:
            font: QFont = self.font()
            font.setPointSize(max(1, size))
            self.setFont(font)
            self.updateGeometry()
        self.debounce_layout_changed()

    def get_text_size(self) -> int:
        delegate: QAbstractItemDelegate | None = self.itemDelegate()
        return delegate.text_size if isinstance(delegate, HTMLDelegate) else self.font().pointSize()

    def update_columns_after_text_size_change(self):
        """This method should be implemented by subclasses if needed."""

    def emit_layout_changed(self):
        model: QAbstractItemModel | None = self.model()
        if model is None:
            return
        model.layoutChanged.emit()

    def styleOptionForIndex(
        self,
        index: QModelIndex,
    ) -> QStyleOptionViewItem:
        """Construct and configure a QStyleOptionViewItem for the given index.

        Required for non-pyqt5 versions of Qt.
        """
        option = QStyleOptionViewItem()
        if index.isValid():
            # Initialize style option from the widget
            option.initFrom(self)

            # Set state flags based on item's selection, focus, and enabled states
            sel_model: QItemSelectionModel | None = self.selectionModel()
            assert sel_model is not None
            if sel_model.isSelected(index):
                option.state |= QStyle.StateFlag.State_Selected
            if index == self.currentIndex() and self.hasFocus():
                option.state |= QStyle.StateFlag.State_HasFocus
            if not self.isEnabled():
                option.state = cast(QStyle.StateFlag, option.state & ~QStyle.StateFlag.State_Enabled)

            # Additional properties
            check_state_data: Any = index.data(Qt.ItemDataRole.CheckStateRole)
            option.checkState = Qt.CheckState.Unchecked if check_state_data is None else check_state_data
            option.decorationPosition = QStyleOptionViewItem.Position.Top
            option.decorationAlignment = Qt.AlignmentFlag.AlignCenter
            option.displayAlignment = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            option.index = index
            option.locale = self.locale()
            option.showDecorationSelected = True
            option.text = index.data(Qt.ItemDataRole.DisplayRole)
            #option.backgroundBrush = QColor(Qt.GlobalColor.yellow)
            #option.decorationSize = QSize(32, 32)
            #option.font = QFont("Arial", 12, QFont.Weight.Bold)
            #option.icon = QIcon("/path/to/icon.png")  # Example path to an icon
            #option.textElideMode = Qt.TextElideMode.ElideMiddle
            #option.viewItemPosition = QStyleOptionViewItem.ViewItemPosition.Middle
            #if index.row() % 2 == 0:
            #    option.backgroundBrush = QColor(Qt.GlobalColor.lightGray)

        return option

    def build_context_menu(
        self,
        parent: QWidget | None = None,
    ) -> QMenu:
        print(f"{self.__class__.__name__}.build_context_menu")
        menu: QMenu | None = super().build_context_menu(parent)
        assert menu is not None
        context_menu: QMenu | None = menu.addMenu("QAbstractItemView")
        assert context_menu is not None
        advanced_menu: QMenu | None = context_menu.addMenu("Advanced")
        assert advanced_menu is not None
        # Display menu
        display_menu: QMenu | None = context_menu.addMenu("Display")
        assert display_menu is not None
        self._add_menu_action(
            display_menu,
            "Alternating Row Colors",
            self.alternatingRowColors,
            self.setAlternatingRowColors,
            settings_key="alternatingRowColors",
        )

        # Advanced submenu for Display
        display_advanced_menu: QMenu | None = display_menu.addMenu("Advanced")
        assert display_advanced_menu is not None
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
        drag_drop_menu: QMenu | None = advanced_menu.addMenu("Drag and Drop")
        assert drag_drop_menu is not None
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
        behavior_menu: QMenu | None = context_menu.addMenu("Behavior")
        assert behavior_menu is not None
        behavior_frame_menu: QMenu | None = behavior_menu.addMenu("Frame")
        assert behavior_frame_menu is not None
        self._add_exclusive_menu_action(
            behavior_frame_menu,
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
            behavior_frame_menu,
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
            "Tab Key Navigation",
            self.tabKeyNavigation,
            self.setTabKeyNavigation,
            settings_key="tabKeyNavigation",
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
        scroll_advanced_menu: QMenu | None = behavior_menu.addMenu("Advanced")
        assert scroll_advanced_menu is not None

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
        self._add_exclusive_menu_action(  # QAbstractScrollArea
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
        def set_viewport_margins(m: QMargins):
            if isinstance(m, (tuple, list)):
                self.setViewportMargins(*m)
            elif isinstance(m, QtCore.QMargins):
                self.setViewportMargins(m.left(), m.top(), m.right(), m.bottom())
            else:
                self.setViewportMargins(0, 0, 0, 0)  # Default values if neither tuple/list nor QMargins

        viewport_menu: QMenu | None = context_menu.addMenu("Viewport")
        assert viewport_menu is not None
        self._add_menu_action(
            viewport_menu,
            "Viewport Margins",
            self.viewportMargins,  # QAbstractScrollArea
            set_viewport_margins,
            settings_key="viewportMargins",
            param_type=tuple,
        )

        # Actions menu
        refresh_menu: QMenu | None = context_menu.addMenu("Refresh...")
        assert refresh_menu is not None

        self._add_simple_action(refresh_menu, "Update Geometries", self.updateGeometries)
        self._add_simple_action(refresh_menu, "Reset View", self.reset)
        self._add_simple_action(refresh_menu, "Clear Selection", self.clearSelection)
        self._add_simple_action(refresh_menu, "Select All", self.selectAll)
        self._add_simple_action(refresh_menu, "Emit Layout Changed", self.emit_layout_changed)
        return menu
