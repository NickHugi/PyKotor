from __future__ import annotations

import ast

from typing import TYPE_CHECKING, Any, Callable

import qtpy

from qtpy.QtCore import QEvent, QModelIndex, QRect, QSettings, QTimer, Qt
from qtpy.QtGui import QColor, QStandardItem
from qtpy.QtWidgets import (
    QAbstractItemView,
    QAction,  # pyright: ignore[reportPrivateImportUsage]
    QActionGroup,  # pyright: ignore[reportPrivateImportUsage]
    QColorDialog,
    QHeaderView,
    QInputDialog,
    QMenu,
    QStyle,
    QStyleOptionViewItem,
    QTreeView,
    QWhatsThis,
)

from utility.ui_libraries.qt.widgets.itemviews.html_delegate import HTMLDelegate

if TYPE_CHECKING:
    from qtpy.QtCore import QAbstractItemModel, QItemSelectionModel, QObject, QPoint
    from qtpy.QtGui import QFont, QPainter, QResizeEvent, QStandardItemModel, QWheelEvent
    from qtpy.QtWidgets import (
        QScrollBar,
        QStyledItemDelegate,
        QWidget,
        _QMenu,
    )
    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]


class RobustTreeView(QTreeView):
    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        use_columns: bool = False,
        settings_name: str = "RobustTreeView",
    ):
        super().__init__(parent)
        self.settings: TreeSettings = TreeSettings(settings_name)
        self.branch_connectors_enabled: bool = False
        self.layoutChangedDebounceTimer: QTimer = QTimer(self)
        self.original_stylesheet: str = self.styleSheet()
        self.header_visible: bool = self.settings.get("headerVisible", False)
        self.setup_menu_extras()
        if not use_columns:
            self.toggle_header_visible(self.header_visible)

    def toggle_header_visible(
        self,
        enabled: bool,  # noqa: FBT001
    ):
        self.header_visible = enabled
        h: QHeaderView | None = self.header()
        if h is None:
            return
        if enabled:
            h.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            h.setStretchLastSection(True)
            h.show()
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        else:
            self.fix_horizontal_scroll_bar(h)
        self.settings.set("headerVisible", enabled)

    @staticmethod
    def fix_horizontal_scroll_bar(h: QHeaderView):
        h.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        h.setStretchLastSection(False)
        h.setMinimumSectionSize(h.geometry().width() * 5)
        h.setDefaultSectionSize(h.geometry().width() * 10)
        h.hide()
        # self.setColumnWidth(0, 2000)  # an alternative way to get the horizontal scrollbar, but not recommended, seemed to jerk around.

    def show_header_context_menu(
        self,
        pos: QPoint,
        menu: _QMenu | None = None,  # noqa: FBT001
    ):
        menu = self.header_menu if menu is None else menu
        h: QHeaderView | None = self.header()
        if h is None or menu is None:
            return
        menu.exec(h.mapToGlobal(pos))

    def set_text_size(
        self,
        size: int,  # noqa: FBT001
    ):
        delegate: HTMLDelegate | QStyledItemDelegate | None = self.itemDelegate()
        if isinstance(delegate, HTMLDelegate):
            text_size: int = max(1, size)
            model: QAbstractItemModel | None = self.model()
            assert model is not None
            delegate.set_text_size(text_size)
            for column in range(model.columnCount()):
                self.resizeColumnToContents(column)
        else:
            font = self.font()
            font.setPointSize(max(1, size))
            self.setFont(font)
            self.updateGeometry()
        self.debounce_layout_changed()

    def get_text_size(self) -> int:
        delegate: HTMLDelegate | QStyledItemDelegate | None = self.itemDelegate()
        return delegate.text_size if isinstance(delegate, HTMLDelegate) else self.font().pointSize()

    def emit_layout_changed(self):
        model: QAbstractItemModel | None = self.model()
        if model is not None:
            model.layoutChanged.emit()

    def debounce_layout_changed(
        self,
        timeout: int = 100,  # noqa: FBT001
        *,
        pre_change_emit: bool = False,  # noqa: FBT001
    ):
        viewport: QWidget | None = self.viewport()
        if viewport is not None:
            viewport.update()
        # self.update()
        if self.layoutChangedDebounceTimer.isActive():
            self.layoutChangedDebounceTimer.stop()
        elif pre_change_emit:
            model: QAbstractItemModel | None = self.model()
            if model is not None:
                model.layoutAboutToBeChanged.emit()
        self.layoutChangedDebounceTimer.start(timeout)

    def draw_circle(
        self,
        painter: QPainter,
        center_x: int,
        center_y: int,
        radius: int,
    ):
        circle_rect = QRect(center_x - radius, center_y - radius, 2 * radius, 2 * radius)
        painter.setBrush(Qt.GlobalColor.white)  # Fill the circle with white color
        painter.drawEllipse(circle_rect)

        # Draw useful information inside the circle
        random_number = 5
        font: QFont = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        painter.drawText(circle_rect, Qt.AlignmentFlag.AlignCenter, str(random_number))

    def eventFilter(
        self,
        obj: QObject,
        event: QEvent,
    ) -> bool:
        if event.type() in (QEvent.Type.Scroll, QEvent.Type.ScrollPrepare):
            return True  # block automated scroll events
        return super().eventFilter(obj, event)

    def itemDelegate(
        self,
        *args,  # noqa: ARG001
    ) -> HTMLDelegate | QStyledItemDelegate | None:
        return super().itemDelegate()

    def setItemDelegate(
        self,
        delegate: HTMLDelegate | QStyledItemDelegate,
    ):
        assert isinstance(delegate, HTMLDelegate)
        super().setItemDelegate(delegate)

    def resizeEvent(
        self,
        event: QResizeEvent,
    ):
        super().resizeEvent(event)
        self.debounce_layout_changed()

    def wheelEvent(
        self,
        event: QWheelEvent,
    ) -> None:
        modifiers: Qt.KeyboardModifier = event.modifiers()
        response: bool | None = None
        if bool(modifiers & Qt.KeyboardModifier.ShiftModifier) and bool(modifiers & Qt.KeyboardModifier.ControlModifier):
            response = self._wheel_changes_item_spacing(event)
        elif bool(modifiers & Qt.KeyboardModifier.ControlModifier):
            response = self._wheel_changes_text_size(event)
        elif bool(modifiers & Qt.KeyboardModifier.ShiftModifier):
            response = self._wheel_changes_horizontal_scroll(event)
        elif bool(modifiers & Qt.KeyboardModifier.AltModifier):
            response = self._wheel_changes_indent_size(event)
        elif (not int(modifiers or Qt.KeyboardModifier.NoModifier)) if qtpy.QT5 else (modifiers != Qt.KeyboardModifier.NoModifier):  # pyright: ignore[reportArgumentType]
            response = self._wheel_changes_vertical_scroll(event)
        if response is not True:
            super().wheelEvent(event)

    def _wheel_changes_text_size(
        self,
        event: QWheelEvent,
    ) -> bool:
        delta: int = event.angleDelta().y()
        if not delta:
            return False
        self.set_text_size(self.get_text_size() + (1 if delta > 0 else -1))
        return True

    def _wheel_changes_horizontal_scroll(
        self,
        event: QWheelEvent,
    ) -> bool:
        delta: int = event.angleDelta().y()
        if not delta:
            return True
        if self.horizontalScrollMode() == self.ScrollMode.ScrollPerItem:
            delta = self.indentation() * (1 if delta > 0 else -1)
        else:
            delta = -self.get_text_size() if delta > 0 else self.get_text_size()
        horizontal_scroll_bar: QScrollBar | None = self.horizontalScrollBar()
        if horizontal_scroll_bar is None:
            return True
        horizontal_scroll_bar.setValue(horizontal_scroll_bar.value() + delta)
        return True

    def _wheel_changes_vertical_scroll(
        self,
        event: QWheelEvent,
    ) -> bool:
        delta: int = event.angleDelta().y()
        # print("wheelVerticalScroll, delta: ", delta)
        if not delta:
            return True
        self.scroll_multiple_steps("up" if delta > 0 else "down")
        return True

    def set_scroll_step_size(
        self,
        value: int,  # noqa: FBT001
    ):
        """Set the number of items to scroll per wheel event."""
        print(f"scrollStepSize set to {value}")
        self.settings.set("scrollStepSize", value)

    def scroll_multiple_steps(
        self,
        direction: Literal["up", "down"],  # noqa: FBT001
    ):
        """Scroll multiple steps based on the user-defined setting.

        Determines what a 'step' is by checking `self.verticalScrollMode()`
        and multiplies it by the user-defined number of items to scroll.
        """
        vert_scroll_bar: QScrollBar | None = self.verticalScrollBar()
        if vert_scroll_bar is None:
            return
        step_size: int = self.settings.get("scrollStepSize", 1)

        if self.verticalScrollMode() == QAbstractItemView.ScrollMode.ScrollPerItem:
            if qtpy.QT5:
                action = vert_scroll_bar.SliderSingleStepSub if direction == "up" else vert_scroll_bar.SliderSingleStepAdd  # pyright: ignore[reportAttributeAccessIssue]
            else:
                action = vert_scroll_bar.SliderAction.SliderSingleStepSub if direction == "up" else vert_scroll_bar.SliderAction.SliderSingleStepAdd
            for _ in range(step_size):
                vert_scroll_bar.triggerAction(action)
        else:
            scroll_step: int = -self.get_text_size() if direction == "up" else self.get_text_size()
            vert_scroll_bar.setValue(vert_scroll_bar.value() + scroll_step * step_size)

    def _wheel_changes_item_spacing(
        self,
        event: QWheelEvent,
    ) -> bool:
        delta: int = event.angleDelta().y()
        if not delta:
            return False
        item_delegate: HTMLDelegate | QStyledItemDelegate | None = self.itemDelegate()
        if isinstance(item_delegate, HTMLDelegate):
            single_step: Literal[-1, 1] = 1 if delta > 0 else -1
            new_vertical_spacing: int = max(0, item_delegate.custom_vertical_spacing + single_step)
            item_delegate.setVerticalSpacing(new_vertical_spacing)
            self.emit_layout_changed()  # Requires immediate update
            return True
        return False

    def _wheel_changes_indent_size(
        self,
        event: QWheelEvent,
    ) -> bool:
        delta: int = event.angleDelta().x()  # Same as y() in the other funcs but returned in x() due to AltModifier I guess. Not in the documentation.
        # print(f"wheel changes indent delta: {delta}")
        if not delta:
            return False
        self.setIndentation(max(0, self.indentation() + (1 if delta > 0 else -1)))
        self.debounce_layout_changed()
        return True

    def model(self) -> QStandardItemModel | QAbstractItemModel | None:
        return super().model()

    def setup_menu_extras(self):
        # View Menu: Display settings related to the appearance and layout of the tree view
        header: QHeaderView | None = self.header()
        if header is not None:
            header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.header_menu: _QMenu | None = QMenu(self)
        self.view_menu: _QMenu | None = self.header_menu.addMenu("View")  # pyright: ignore[reportAttributeAccessIssue]
        self.settings_menu: _QMenu | None = self.header_menu.addMenu("Settings")  # pyright: ignore[reportAttributeAccessIssue]
        self.tools_menu: _QMenu | None = self.header_menu.addMenu("Tools")  # pyright: ignore[reportAttributeAccessIssue]

        # Common view settings
        self._add_menu_action(
            self.view_menu,
            "Uniform Row Heights",
            self.uniformRowHeights,
            self.setUniformRowHeights,
            settings_key="uniformRowHeights",
        )
        self._add_menu_action(
            self.view_menu,
            "Alternating Row Colors",
            self.alternatingRowColors,
            self.setAlternatingRowColors,
            settings_key="alternatingRowColors",
        )
        self._add_menu_action(
            self.view_menu,
            "Show/Hide Branch Connectors",
            self.branch_connectors_drawn,
            self.draw_connectors,
            settings_key="drawBranchConnectors",
        )
        self._add_menu_action(
            self.view_menu,
            "Expand Items on Double Click",
            self.expandsOnDoubleClick,
            self.setExpandsOnDoubleClick,
            settings_key="expandsOnDoubleClick",
        )
        self._add_menu_action(
            self.view_menu,
            "Tree Indentation",
            self.indentation,
            self.setIndentation,
            settings_key="indentation",
            param_type=int,
        )

        # Text and Icon Display Settings
        display_settings_menu: _QMenu | None = self.view_menu.addMenu("Display Settings")  # pyright: ignore[reportAttributeAccessIssue]
        self._add_menu_action(
            display_settings_menu,
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
            display_settings_menu,
            "Font Size",
            self.get_text_size,
            self.set_text_size,
            settings_key="fontSize",
            param_type=int,
        )
        self._add_menu_action(
            display_settings_menu,
            "Vertical Spacing",
            lambda: self.itemDelegate().custom_vertical_spacing,  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
            lambda x: self.itemDelegate().setVerticalSpacing(x),  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
            settings_key="verticalSpacing",
            param_type=int,
        )
        self._add_color_menu_action(
            display_settings_menu,
            "Set Text Color",
            lambda: QColor(self.settings.get("textColor", QColor(0, 0, 0))),
            settings_key="textColor",
        )

        # Focus and scrolling settings
        self._add_exclusive_menu_action(
            self.settings_menu,
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
        self._add_exclusive_menu_action(
            self.settings_menu,
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
            self.settings_menu,
            "Vertical Scroll Mode",
            self.verticalScrollMode,
            self.setVerticalScrollMode,
            options={
                "Scroll Per Item": QAbstractItemView.ScrollMode.ScrollPerItem,
                "Scroll Per Pixel": QAbstractItemView.ScrollMode.ScrollPerPixel,
            },
            settings_key="verticalScrollMode",
        )
        self._add_menu_action(
            self.settings_menu,
            "Auto Scroll",
            self.hasAutoScroll,
            self.setAutoScroll,
            settings_key="autoScroll",
        )
        self._add_menu_action(
            self.settings_menu,
            "Auto Fill Background",
            self.autoFillBackground,
            self.setAutoFillBackground,
            settings_key="autoFillBackground",
        )
        self._add_menu_action(
            self.settings_menu,
            "Expand All Root Item Children",
            lambda: self.settings.get("ExpandRootChildren", False),
            lambda value: self.settings.set("ExpandRootChildren", value),
            settings_key="ExpandRootChildren",
        )
        self._add_menu_action(
            self.settings_menu,
            "Items Scrolled Per Wheel",
            lambda: self.settings.get("scrollStepSize", 1),
            self.set_scroll_step_size,
            settings_key="scrollStepSize",
            param_type=int,
        )

        self._add_simple_action(self.tools_menu, "Repaint", self.repaint)
        self._add_simple_action(self.tools_menu, "Update", self.update)
        self._add_simple_action(self.tools_menu, "Resize Column To Contents", lambda: self.resizeColumnToContents(0))
        self._add_simple_action(self.tools_menu, "Update Geometries", self.updateGeometries)
        self._add_simple_action(self.tools_menu, "Reset", self.reset)

        # Help or Miscellaneous actions
        from toolset.gui.common.localization import translate as tr
        self.help_menu: _QMenu | None = self.header_menu.addMenu(tr("Help"))  # pyright: ignore[reportAttributeAccessIssue]
        whats_this_action = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarContextHelpButton), tr("What's This?"), self)  # pyright: ignore[reportOptionalMemberAccess]
        whats_this_action.triggered.connect(QWhatsThis.enterWhatsThisMode)
        whats_this_action.setToolTip(tr("Enter 'What's This?' mode."))
        self.help_menu.addAction(whats_this_action)  # pyright: ignore[reportOptionalMemberAccess]

        # Add the horizontal scrollbar toggle to the view menu
        self._add_menu_action(
            self.view_menu,
            "Show Horizontal Scrollbar",
            lambda: self.header_visible,
            self.toggle_header_visible,
            settings_key="headerVisible",
        )

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

    def _handle_color_action(
        self,
        get_func: Callable[[], Any],
        title: str,
        settings_key: str,
    ):
        color = QColorDialog.getColor(get_func(), self, title)
        if color.isValid():
            self.settings.set(settings_key, color.name())
            self.debounce_layout_changed(pre_change_emit=True)
            model: QStandardItemModel | QAbstractItemModel | None = self.model()
            if model is None:
                return
            for row in range(model.rowCount()):  # Corrected iteration over model
                item: QStandardItem | None = model.item(row)  # Get the item at the current row
                if item is None or item.isDeleted():
                    continue
                self.debounce_layout_changed()
            viewport: QWidget | None = self.viewport()
            if viewport is not None:
                viewport.update()
            self.update()

    def _add_simple_action(
        self,
        menu: _QMenu,
        title: str,
        func: Callable[[], Any],
    ):
        action = QAction(title, self)
        action.triggered.connect(func)
        menu.addAction(action)

    def _add_menu_action(  # noqa: PLR0913
        self,
        menu: _QMenu,
        title: str,
        current_state_func: Callable[[], Any],
        set_func: Callable[[Any], Any],
        settings_key: str,
        options: dict | None = None,
        param_type: type | None = None,
    ):
        action = QAction(title, self)

        # Infer param_type if not provided
        if param_type is None:
            param_type = bool if options is None else type(next(iter(options.values()))) if options else bool

        if param_type is bool:
            action.setCheckable(True)

            def convert_string_to_type(value: str | Any) -> Any:
                if not isinstance(value, str):
                    return value
                # Attempt to evaluate the string as a Python literal
                try:
                    return ast.literal_eval(value)
                except (ValueError, SyntaxError):
                    # If evaluation fails, return the string as-is
                    return value

            initial_value = convert_string_to_type(self.settings.get(settings_key, current_state_func()))
            action.setChecked(initial_value)
            set_func(initial_value)  # Apply the initial value from settings
            action.toggled.connect(lambda checked: [set_func(checked), self.settings.set(settings_key, checked)])
        elif param_type is int:
            action.triggered.connect(lambda: self._handle_int_action(set_func, title, settings_key))
        else:
            action.triggered.connect(lambda: self._handle_non_bool_action(set_func, title, options, settings_key))
        menu.addAction(action)

    def _add_exclusive_menu_action(  # noqa: PLR0913
        self,
        menu: _QMenu,
        title: str,
        current_state_func: Callable[[], Any],
        set_func: Callable[[Any], Any],
        options: dict[str, Any],
        settings_key: str,
    ):
        sub_menu = menu.addMenu(title)
        actionGroup = QActionGroup(self)
        actionGroup.setExclusive(True)
        initial_value = self.settings.get(settings_key, current_state_func())
        set_func(initial_value)  # Apply the initial value from settings
        for option_name, option_value in options.items():
            action = QAction(option_name, self)
            action.setCheckable(True)
            action.setChecked(initial_value == option_value)
            action.triggered.connect(lambda checked, val=option_value: [set_func(val), self.settings.set(settings_key, val)] if checked else None)
            sub_menu.addAction(action)  # pyright: ignore[reportOptionalMemberAccess]
            actionGroup.addAction(action)

    def _add_multi_select_menu_action(  # noqa: PLR0913
        self,
        menu: _QMenu,
        title: str,
        current_state_func: Callable[[], Any],
        set_func: Callable[[Any], Any],
        options: dict[str, Any],
        settings_key: str,
        zero_value: Any,
    ):
        sub_menu = menu.addMenu(title)
        initial_value = self.settings.get(settings_key, current_state_func())

        def apply_filters():
            combined_filter = zero_value.value if hasattr(zero_value, "value") else zero_value
            for action in sub_menu.actions():  # pyright: ignore[reportOptionalMemberAccess]
                if action.isChecked():
                    option_val = options[action.text()]
                    option_val = option_val.value if hasattr(option_val, "value") else option_val
                    combined_filter |= option_val
            set_func(combined_filter)
            self.settings.set(settings_key, combined_filter)

        for option_name, option_value in options.items():
            action = QAction(option_name, self)
            action.setCheckable(True)
            # Handle enum values for bitwise operations
            check_value = option_value.value if hasattr(option_value, "value") else option_value
            action.setChecked(bool(initial_value & check_value))
            action.triggered.connect(apply_filters)
            sub_menu.addAction(action)  # pyright: ignore[reportOptionalMemberAccess]

        # Apply the filters initially based on settings
        apply_filters()

    def _handle_int_action(
        self,
        func: Callable[[int], Any],
        title: str,
        settings_key: str,
    ):
        value, ok = QInputDialog.getInt(self, f"Set {title}", f"Enter {title}:", min=0)
        if ok:
            func(value)
            self.settings.set(settings_key, value)

    def _handle_non_bool_action(
        self,
        func: Callable[[Any], Any],
        title: str,
        options: dict,
        settings_key: str,
    ):
        items = list(options.keys())
        item, ok = QInputDialog.getItem(self, f"Select {title}", f"Select {title}:", items, 0, False)
        if ok and item:
            value = options[item]
            func(value)
            self.settings.set(settings_key, value)

    def styleOptionForIndex(
        self,
        index: QModelIndex,
    ) -> QStyleOptionViewItem:
        """Construct and configure a QStyleOptionViewItem for the given index."""
        option = QStyleOptionViewItem()
        if index.isValid():
            # Initialize style option from the widget
            option.initFrom(self)

            # Set state flags based on item's selection, focus, and enabled states
            selection_model: QItemSelectionModel | None = self.selectionModel()
            if selection_model is not None and selection_model.isSelected(index):
                option.state |= QStyle.StateFlag.State_Selected
            if index == self.currentIndex() and self.hasFocus():
                option.state |= QStyle.StateFlag.State_HasFocus
            if not self.isEnabled():
                option.state &= ~QStyle.StateFlag.State_Enabled
            if self.isExpanded(index):
                option.features |= QStyleOptionViewItem.ViewItemFeature.HasDecoration

            # Additional properties
            checkStateData = index.data(Qt.ItemDataRole.CheckStateRole)
            option.checkState = Qt.CheckState.Unchecked if checkStateData is None else checkStateData
            option.decorationPosition = QStyleOptionViewItem.Position.Top
            option.decorationAlignment = Qt.AlignmentFlag.AlignCenter
            option.displayAlignment = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            option.index = index
            option.locale = self.locale()
            option.showDecorationSelected = True
            option.text = index.data(Qt.ItemDataRole.DisplayRole)
            # option.backgroundBrush = QColor(Qt.GlobalColor.yellow)
            # option.decorationSize = QSize(32, 32)
            # option.font = QFont("Arial", 12, QFont.Weight.Bold)
            # option.icon = QIcon("/path/to/icon.png")  # Example path to an icon
            # option.textElideMode = Qt.TextElideMode.ElideMiddle
            # option.viewItemPosition = QStyleOptionViewItem.ViewItemPosition.Middle
            # if index.row() % 2 == 0:
            #    option.backgroundBrush = QColor(Qt.GlobalColor.lightGray)

        return option

    def get_identifying_text(
        self,
        index_or_item: QModelIndex | QStandardItem | None,
    ) -> str:
        if index_or_item is None:
            return "(None)"
        if isinstance(index_or_item, QStandardItem):
            try:
                index_or_item = index_or_item.index()
            except RuntimeError as e:  # wrapped C/C++ object of type x has been deleted
                return str(e)
        if not isinstance(index_or_item, QModelIndex):
            return f"(Unknown index/item: {index_or_item})"
        if not index_or_item.isValid():
            return f"(invalid index at row '{index_or_item.row()}', column '{index_or_item.column()}')"

        item = self.model().itemFromIndex(index_or_item)  # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue]
        if item is None:
            return f"(no item associated with index at row '{index_or_item.row()}', column '{index_or_item.column()}')"

        text = item.text().strip()
        parent_count = 0
        current_index = index_or_item.parent()
        while current_index.isValid():
            parent_count += 1
            current_index = current_index.parent()

        return f"Item/Index at Row: {index_or_item.row()}, Column: {index_or_item.column()}, Ancestors: {parent_count}\nText for above item: {text}\n"

    def branch_connectors_drawn(self) -> bool:
        return self.branch_connectors_enabled

    def draw_connectors(
        self,
        draw: bool,  # noqa: FBT001, FBT002
    ):
        if not draw:
            self.branch_connectors_enabled = False
            self.setStyleSheet(self.original_stylesheet)
        else:
            self.branch_connectors_enabled = True
            self.setStyleSheet("""
            QTreeView {
                alternate-background-color: yellow;
                show-decoration-selected: 1;
            }

            QTreeView::item {
                border: 1px solid #d9d9d9;
                border-top-color: transparent;
                border-bottom-color: transparent;
            }

            QTreeView::item:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #e7effd, stop: 1 #cbdaf1);
                border: 1px solid #bfcde4;
            }

            QTreeView::item:selected {
                border: 1px solid #567dbc;
            }

            QTreeView::item:selected:active {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #6ea1f1, stop: 1 #567dbc);
            }

            QTreeView::item:selected:!active {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #6b9be8, stop: 1 #577fbf);
            }

            QTreeView::branch {
                background: palette(base);
            }

            QTreeView::branch:has-siblings:!adjoins-item {
                border-image: url(:/images/common/stylesheet-vline.png) 0;
            }

            QTreeView::branch:has-siblings:adjoins-item {
                border-image: url(:/images/common/stylesheet-branch-more.png) 0;
            }

            QTreeView::branch:!has-children:!has-siblings:adjoins-item {
                border-image: url(:/images/common/stylesheet-branch-end.png) 0;
            }

            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings {
                border-image: none;
                image: url(:/images/common/stylesheet-branch-closed.png);
            }

            QTreeView::branch:open:has-children:!has-siblings,
            QTreeView::branch:open:has-children:has-siblings {
                border-image: none;
                image: url(:/images/common/stylesheet-branch-open.png);
            }
            """)


class TreeSettings:
    def __init__(
        self,
        settings_name: str = "RobustTreeView",
    ):
        self.robust_tree_settings: QSettings = QSettings("HolocronToolsetV3", "RobustTreeView")
        self.settings: QSettings = self.robust_tree_settings if settings_name == "RobustTreeView" else QSettings("HolocronToolsetV3", settings_name)

    def get(
        self,
        key: str,
        default: Any,
    ) -> Any:
        # sourcery skip: assign-if-exp, reintroduce-else
        if qtpy.QT5:
            default_val = self.robust_tree_settings.value(key, default, default.__class__)
            return self.settings.value(
                key,
                default_val,
                default.__class__,
            )
        default_val = self.robust_tree_settings.value(key, default)
        result = self.settings.value(key, default_val)
        if result == "true":
            return True
        if result == "false":
            return False
        return result

    def set(
        self,
        key: str,
        value: Any,
    ):
        self.settings.setValue(key, value)

    def text_elide_mode(
        self,
        default: int,
    ) -> int:
        return self.get("textElideMode", default)

    def set_text_elide_mode(
        self,
        value: int,
    ):
        self.set("textElideMode", value)

    def focus_policy(
        self,
        default: int,
    ) -> int:
        return self.get("focusPolicy", default)

    def set_focus_policy(
        self,
        value: int,
    ):
        self.set("focusPolicy", value)

    def layout_direction(
        self,
        default: int,
    ) -> int:
        return self.get("layoutDirection", default)

    def set_layout_direction(
        self,
        value: int,
    ):  # noqa: FBT001
        self.set("layoutDirection", value)

    def vertical_scroll_mode(
        self,
        default: int,
    ) -> int:  # noqa: FBT001
        return self.get("verticalScrollMode", default)

    def set_vertical_scroll_mode(
        self,
        value: int,
    ):  # noqa: FBT001
        self.set("verticalScrollMode", value)

    def uniform_row_heights(
        self,
        default: bool,  # noqa: FBT001
    ) -> bool:
        return self.get("uniformRowHeights", default)

    def set_uniform_row_heights(
        self,
        value: bool,  # noqa: FBT001
    ):
        self.set("uniformRowHeights", value)

    def animations(
        self,
        default: bool,  # noqa: FBT001
    ) -> bool:
        return self.get("animations", default)

    def set_animations(
        self,
        value: bool,  # noqa: FBT001
    ):
        self.set("animations", value)

    def auto_scroll(
        self,
        default: bool,  # noqa: FBT001
    ) -> bool:
        return self.get("autoScroll", default)

    def set_auto_scroll(
        self,
        value: bool,  # noqa: FBT001
    ):
        self.set("autoScroll", value)

    def expands_on_double_click(
        self,
        default: bool,  # noqa: FBT001
    ) -> bool:
        return self.get("expandsOnDoubleClick", default)

    def set_expands_on_double_click(
        self,
        value: bool,  # noqa: FBT001
    ):
        self.set("expandsOnDoubleClick", value)

    def auto_fill_background(
        self,
        default: bool,  # noqa: FBT001
    ) -> bool:
        return self.get("autoFillBackground", default)

    def set_auto_fill_background(
        self,
        value: bool,  # noqa: FBT001
    ):
        self.set("autoFillBackground", value)

    def alternating_row_colors(
        self,
        default: bool,  # noqa: FBT001
    ) -> bool:
        return self.get("alternatingRowColors", default)

    def set_alternating_row_colors(
        self,
        value: bool,  # noqa: FBT001
    ):
        self.set("alternatingRowColors", value)

    def indentation(
        self,
        default: int,
    ) -> int:
        return self.get("indentation", default)

    def set_indentation(
        self,
        value: int,
    ):
        self.set("indentation", value)

    def font_size(
        self,
        default: int,
    ) -> int:
        return self.get("fontSize", default)

    def set_font_size(
        self,
        value: int,
    ):
        self.set("fontSize", value)
