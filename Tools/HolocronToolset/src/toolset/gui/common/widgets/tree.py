from __future__ import annotations

import ast

from typing import TYPE_CHECKING, Any, Callable

import qtpy

from qtpy.QtCore import (
    QEvent,
    QModelIndex,
    QRect,
    QSettings,
    QTimer,
    Qt,
)
from qtpy.QtGui import (
    QColor,
    QStandardItem,
)
from qtpy.QtWidgets import (
    QAbstractItemView,
    QAction,
    QActionGroup,
    QColorDialog,
    QHeaderView,
    QInputDialog,
    QMenu,
    QStyle,
    QStyleOptionViewItem,
    QTreeView,
    QWhatsThis,
)

from toolset.gui.common.style.delegates import HTMLDelegate

if TYPE_CHECKING:

    from qtpy.QtCore import (
        QAbstractItemModel,
        QObject,
        QPoint,
    )
    from qtpy.QtGui import (
        QPainter,
        QResizeEvent,
        QStandardItemModel,
        QWheelEvent,
    )
    from qtpy.QtWidgets import (
        QStyledItemDelegate,
        QWidget,
    )
    from typing_extensions import Literal



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
        self.setupMenuExtras()
        h: QHeaderView = self.header()
        if not use_columns:
            self.toggle_header_visible(self.header_visible)

    def toggle_header_visible(self, enabled: bool):
        self.header_visible = enabled
        h: QHeaderView = self.header()
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
        #self.setColumnWidth(0, 2000)  # an alternative way to get the horizontal scrollbar, but not recommended, seemed to jerk around.


    def showHeaderContextMenu(self, pos: QPoint, menu: QMenu | None = None):
        menu = self.headerMenu if menu is None else menu
        menu.exec_(self.header().mapToGlobal(pos))

    def setTextSize(self, size: int):
        delegate = self.itemDelegate()
        if isinstance(delegate, HTMLDelegate):
            text_size = max(1, size)
            model: QAbstractItemModel | None = self.model()
            assert model is not None
            delegate.setTextSize(text_size)
            for column in range(model.columnCount()):
                self.resizeColumnToContents(column)
        else:
            font = self.font()
            font.setPointSize(max(1, size))
            self.setFont(font)
            self.updateGeometry()
        self.debounceLayoutChanged()

    def getTextSize(self) -> int:
        delegate = self.itemDelegate()
        return delegate.text_size if isinstance(delegate, HTMLDelegate) else self.font().pointSize()

    def emitLayoutChanged(self):
        model = self.model()
        if model is not None:
            model.layoutChanged.emit()

    def debounceLayoutChanged(self, timeout: int = 100, *, preChangeEmit: bool = False):
        self.viewport().update()
        #self.update()
        if self.layoutChangedDebounceTimer.isActive():
            self.layoutChangedDebounceTimer.stop()
        elif preChangeEmit:
            self.model().layoutAboutToBeChanged.emit()
        self.layoutChangedDebounceTimer.start(timeout)

    def drawCircle(self, painter: QPainter, center_x: int, center_y: int, radius: int):
        circle_rect = QRect(center_x - radius, center_y - radius, 2 * radius, 2 * radius)
        painter.setBrush(Qt.GlobalColor.white)  # Fill the circle with white color
        painter.drawEllipse(circle_rect)

        # Draw useful information inside the circle
        random_number = 5
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        painter.drawText(circle_rect, Qt.AlignmentFlag.AlignCenter, str(random_number))

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() in (QEvent.Type.Scroll, QEvent.Type.ScrollPrepare):
            return True  # block automated scroll events
        return super().eventFilter(obj, event)

    def itemDelegate(self, *args) -> HTMLDelegate | QStyledItemDelegate:
        return super().itemDelegate()

    def setItemDelegate(self, delegate: HTMLDelegate | QStyledItemDelegate):
        assert isinstance(delegate, HTMLDelegate)
        super().setItemDelegate(delegate)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.debounceLayoutChanged()

    def wheelEvent(
        self,
        event: QWheelEvent,
    ) -> None:
        modifiers = event.modifiers()
        response = None
        if bool(modifiers & Qt.KeyboardModifier.ShiftModifier) and bool(modifiers & Qt.KeyboardModifier.ControlModifier):
            response = self._wheel_changes_item_spacing(event)
        elif bool(modifiers & Qt.KeyboardModifier.ControlModifier):
            response = self._wheel_changes_text_size(event)
        elif bool(modifiers & Qt.KeyboardModifier.ShiftModifier):
            response = self._wheel_changes_horizontal_scroll(event)
        elif bool(modifiers & Qt.KeyboardModifier.AltModifier):
            response = self._wheel_changes_indent_size(event)
        elif ((not int(modifiers)) if qtpy.QT5 else (modifiers != Qt.KeyboardModifier.NoModifier)):
            response = self._wheel_changes_vertical_scroll(event)
        if response is not True:
            super().wheelEvent(event)

    def _wheel_changes_text_size(self, event: QWheelEvent) -> bool:
        delta: int = event.angleDelta().y()
        if not delta:
            return False
        self.setTextSize(self.getTextSize() + (1 if delta > 0 else -1))
        return True

    def _wheel_changes_horizontal_scroll(self, event: QWheelEvent) -> bool:
        delta: int = event.angleDelta().y()
        if not delta:
            return True
        if self.horizontalScrollMode() == self.ScrollMode.ScrollPerItem:
            delta = self.indentation() * (1 if delta > 0 else -1)
        else:
            delta = -self.getTextSize() if delta > 0 else self.getTextSize()
        self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + delta)
        return True

    def _wheel_changes_vertical_scroll(self, event: QWheelEvent) -> bool:
        delta: int = event.angleDelta().y()
        #print("wheelVerticalScroll, delta: ", delta)
        if not delta:
            return True
        self.scrollMultipleSteps("up" if delta > 0 else "down")
        return True

    def setScrollStepSize(self, value: int):
        """Set the number of items to scroll per wheel event."""
        print(f"scrollStepSize set to {value}")
        self.settings.set("scrollStepSize", value)

    def scrollMultipleSteps(self, direction: Literal["up", "down"]):
        """Scroll multiple steps based on the user-defined setting.

        Determines what a 'step' is by checking `self.verticalScrollMode()`
        and multiplies it by the user-defined number of items to scroll.
        """
        vertScrollBar = self.verticalScrollBar()
        assert vertScrollBar is not None
        step_size = self.settings.get("scrollStepSize", 1)

        if self.verticalScrollMode() == QAbstractItemView.ScrollMode.ScrollPerItem:
            if qtpy.QT5:
                action = vertScrollBar.SliderSingleStepSub if direction == "up" else vertScrollBar.SliderSingleStepAdd
            else:
                action = vertScrollBar.SliderAction.SliderSingleStepSub if direction == "up" else vertScrollBar.SliderAction.SliderSingleStepAdd
            for _ in range(step_size):
                vertScrollBar.triggerAction(action)
        else:
            scrollStep = -self.getTextSize() if direction == "up" else self.getTextSize()
            vertScrollBar.setValue(vertScrollBar.value() + scrollStep * step_size)

    def _wheel_changes_item_spacing(self, event: QWheelEvent) -> bool:
        delta: int = event.angleDelta().y()
        if not delta:
            return False
        item_delegate: HTMLDelegate | QStyledItemDelegate | None = self.itemDelegate()
        if isinstance(item_delegate, HTMLDelegate):
            single_step: Literal[-1, 1] = (1 if delta > 0 else -1)
            newVerticalSpacing: int = max(0, item_delegate.customVerticalSpacing + single_step)
            item_delegate.setVerticalSpacing(newVerticalSpacing)
            self.emitLayoutChanged()  # Requires immediate update
            return True
        return False

    def _wheel_changes_indent_size(self, event: QWheelEvent) -> bool:
        delta: int = event.angleDelta().x()  # Same as y() in the other funcs but returned in x() due to AltModifier I guess. Not in the documentation.
        #print(f"wheel changes indent delta: {delta}")
        if not delta:
            return False
        self.setIndentation(max(0, self.indentation() + (1 if delta > 0 else -1)))
        self.debounceLayoutChanged()
        return True

    def model(self) -> QStandardItemModel | QAbstractItemModel | None:
        return super().model()

    def setupMenuExtras(self):
        # View Menu: Display settings related to the appearance and layout of the tree view
        self.header().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.headerMenu = QMenu(self)
        self.viewMenu = self.headerMenu.addMenu("View")
        self.settingsMenu = self.headerMenu.addMenu("Settings")
        self.toolsMenu = self.headerMenu.addMenu("Tools")

        # Common view settings
        self._addMenuAction(
            self.viewMenu,
            "Uniform Row Heights",
            self.uniformRowHeights,
            self.setUniformRowHeights,
            settings_key="uniformRowHeights",
        )
        self._addMenuAction(
            self.viewMenu,
            "Alternating Row Colors",
            self.alternatingRowColors,
            self.setAlternatingRowColors,
            settings_key="alternatingRowColors",
        )
        self._addMenuAction(
            self.viewMenu,
            "Show/Hide Branch Connectors",
            self.branchConnectorsDrawn,
            self.drawConnectors,
            settings_key="drawBranchConnectors",
        )
        self._addMenuAction(
            self.viewMenu,
            "Expand Items on Double Click",
            self.expandsOnDoubleClick,
            self.setExpandsOnDoubleClick,
            settings_key="expandsOnDoubleClick",
        )
        self._addMenuAction(
            self.viewMenu,
            "Tree Indentation",
            self.indentation,
            self.setIndentation,
            settings_key="indentation",
            param_type=int,
        )

        # Text and Icon Display Settings
        displaySettingsMenu = self.viewMenu.addMenu("Display Settings")
        self._addMenuAction(
            displaySettingsMenu,
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
        self._addMenuAction(
            displaySettingsMenu,
            "Font Size",
            self.getTextSize,
            self.setTextSize,
            settings_key="fontSize",
            param_type=int,
        )
        self._addMenuAction(
            displaySettingsMenu,
            "Vertical Spacing",
            lambda: self.itemDelegate().customVerticalSpacing,
            lambda x: self.itemDelegate().setVerticalSpacing(x),
            settings_key="verticalSpacing",
            param_type=int,
        )
        self._addColorMenuAction(
            displaySettingsMenu,
            "Set Text Color",
            lambda: QColor(
                self.settings.get("textColor", QColor(0, 0, 0))
            ),
            settings_key="textColor",
        )

        # Focus and scrolling settings
        self._addExclusiveMenuAction(
            self.settingsMenu,
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
        self._addExclusiveMenuAction(
            self.settingsMenu,
            "Horizontal Scroll Mode",
            self.horizontalScrollMode,
            self.setHorizontalScrollMode,
            options={
                "Scroll Per Item": QAbstractItemView.ScrollMode.ScrollPerItem,
                "Scroll Per Pixel": QAbstractItemView.ScrollMode.ScrollPerPixel,
            },
            settings_key="horizontalScrollMode",
        )
        self._addExclusiveMenuAction(
            self.settingsMenu,
            "Vertical Scroll Mode",
            self.verticalScrollMode,
            self.setVerticalScrollMode,
            options={
                "Scroll Per Item": QAbstractItemView.ScrollMode.ScrollPerItem,
                "Scroll Per Pixel": QAbstractItemView.ScrollMode.ScrollPerPixel,
            },
            settings_key="verticalScrollMode",
        )
        self._addMenuAction(
            self.settingsMenu,
            "Auto Scroll",
            self.hasAutoScroll,
            self.setAutoScroll,
            settings_key="autoScroll",
        )
        self._addMenuAction(
            self.settingsMenu,
            "Auto Fill Background",
            self.autoFillBackground,
            self.setAutoFillBackground,
            settings_key="autoFillBackground",
        )
        self._addMenuAction(
            self.settingsMenu,
            "Expand All Root Item Children",
            lambda: self.settings.get("ExpandRootChildren", False),
            lambda value: self.settings.set("ExpandRootChildren", value),
            settings_key="ExpandRootChildren",
        )
        self._addMenuAction(
            self.settingsMenu,
            "Items Scrolled Per Wheel",
            lambda: self.settings.get("scrollStepSize", 1),
            self.setScrollStepSize,
            settings_key="scrollStepSize",
            param_type=int,
        )

        self._addSimpleAction(self.toolsMenu, "Repaint", self.repaint)
        self._addSimpleAction(self.toolsMenu, "Update", self.update)
        self._addSimpleAction(self.toolsMenu, "Resize Column To Contents", lambda: self.resizeColumnToContents(0))
        self._addSimpleAction(self.toolsMenu, "Update Geometries", self.updateGeometries)
        self._addSimpleAction(self.toolsMenu, "Reset", self.reset)

        # Help or Miscellaneous actions
        self.helpMenu = self.headerMenu.addMenu("Help")
        whats_this_action = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarContextHelpButton), "What's This?", self)
        whats_this_action.triggered.connect(QWhatsThis.enterWhatsThisMode)
        whats_this_action.setToolTip("Enter 'What's This?' mode.")
        self.helpMenu.addAction(whats_this_action)

        # Add the horizontal scrollbar toggle to the view menu
        self._addMenuAction(
            self.viewMenu,
            "Show Horizontal Scrollbar",
            lambda: self.header_visible,
            self.toggle_header_visible,
            settings_key="headerVisible",
        )

    def _addColorMenuAction(
        self,
        menu: QMenu,
        title: str,
        current_color_func: Callable[[], QColor],
        settings_key: str,
    ):
        action = QAction(title, self)
        action.triggered.connect(lambda: self._handleColorAction(current_color_func, title, settings_key))
        menu.addAction(action)

    def _handleColorAction(
        self,
        get_func: Callable[[], Any],
        title: str,
        settings_key: str,
    ):
        color = QColorDialog.getColor(get_func(), self, title)
        if color.isValid():
            self.settings.set(settings_key, color.name())
            self.debounceLayoutChanged(preChangeEmit=True)
            for item in self.model():
                if item is None:
                    continue
                if item.isDeleted():
                    continue
                self.debounceLayoutChanged()
            self.viewport().update()
            self.update()

    def _addSimpleAction(self, menu: QMenu, title: str, func: Callable[[], Any]):
        action = QAction(title, self)
        action.triggered.connect(func)
        menu.addAction(action)

    def _addMenuAction(  # noqa: PLR0913
        self,
        menu: QMenu,
        title: str,
        current_state_func: Callable[[], Any],
        set_func: Callable[[Any], Any],
        settings_key: str,
        options: dict | None = None,
        param_type: type = bool,
    ):
        action = QAction(title, self)
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
            action.triggered.connect(lambda: self._handleIntAction(set_func, title, settings_key))
        else:
            action.triggered.connect(lambda: self._handleNonBoolAction(set_func, title, options, settings_key))
        menu.addAction(action)

    def _addExclusiveMenuAction(  # noqa: PLR0913
        self,
        menu: QMenu,
        title: str,
        current_state_func: Callable[[], Any],
        set_func: Callable[[Any], Any],
        options: dict[str, Any],
        settings_key: str,
    ):
        subMenu = menu.addMenu(title)
        actionGroup = QActionGroup(self)
        actionGroup.setExclusive(True)
        initial_value = self.settings.get(settings_key, current_state_func())
        set_func(initial_value)  # Apply the initial value from settings
        for option_name, option_value in options.items():
            action = QAction(option_name, self)
            action.setCheckable(True)
            action.setChecked(initial_value == option_value)
            action.triggered.connect(lambda checked, val=option_value: [set_func(val), self.settings.set(settings_key, val)] if checked else None)
            subMenu.addAction(action)
            actionGroup.addAction(action)

    def _addMultiSelectMenuAction(  # noqa: PLR0913
        self,
        menu: QMenu,
        title: str,
        current_state_func: Callable[[], Any],
        set_func: Callable[[Any], Any],
        options: dict[str, Any],
        settings_key: str,
        zero_value: Any,
    ):
        subMenu = menu.addMenu(title)
        initial_value = self.settings.get(settings_key, current_state_func())
        selected_filters = initial_value

        def apply_filters():
            combined_filter = zero_value
            for action in subMenu.actions():
                if action.isChecked():
                    combined_filter |= options[action.text()]
            set_func(combined_filter)
            self.settings.set(settings_key, combined_filter)

        for option_name, option_value in options.items():
            action = QAction(option_name, self)
            action.setCheckable(True)
            action.setChecked(bool(initial_value & option_value))
            action.triggered.connect(apply_filters)
            subMenu.addAction(action)

        # Apply the filters initially based on settings
        apply_filters()

    def _handleIntAction(self, func: Callable[[int], Any], title: str, settings_key: str):
        value, ok = QInputDialog.getInt(self, f"Set {title}", f"Enter {title}:", min=0)
        if ok:
            func(value)
            self.settings.set(settings_key, value)

    def _handleNonBoolAction(self, func: Callable[[Any], Any], title: str, options: dict, settings_key: str):
        items = list(options.keys())
        item, ok = QInputDialog.getItem(self, f"Select {title}", f"Select {title}:", items, 0, False)
        if ok and item:
            value = options[item]
            func(value)
            self.settings.set(settings_key, value)

    def styleOptionForIndex(self, index: QModelIndex) -> QStyleOptionViewItem:
        """Construct and configure a QStyleOptionViewItem for the given index."""
        option = QStyleOptionViewItem()
        if index.isValid():
            # Initialize style option from the widget
            option.initFrom(self)

            # Set state flags based on item's selection, focus, and enabled states
            if self.selectionModel().isSelected(index):
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
            #option.backgroundBrush = QColor(Qt.GlobalColor.yellow)
            #option.decorationSize = QSize(32, 32)
            #option.font = QFont("Arial", 12, QFont.Weight.Bold)
            #option.icon = QIcon("/path/to/icon.png")  # Example path to an icon
            #option.textElideMode = Qt.TextElideMode.ElideMiddle
            #option.viewItemPosition = QStyleOptionViewItem.ViewItemPosition.Middle
            #if index.row() % 2 == 0:
            #    option.backgroundBrush = QColor(Qt.GlobalColor.lightGray)

        return option

    def getIdentifyingText(self, indexOrItem: QModelIndex | QStandardItem | None) -> str:
        if indexOrItem is None:
            return "(None)"
        if isinstance(indexOrItem, QStandardItem):
            try:
                indexOrItem = indexOrItem.index()
            except RuntimeError as e: # wrapped C/C++ object of type x has been deleted
                return str(e)
        if not isinstance(indexOrItem, QModelIndex):
            return f"(Unknown index/item: {indexOrItem})"
        if not indexOrItem.isValid():
            return f"(invalid index at row '{indexOrItem.row()}', column '{indexOrItem.column()}')"

        item = self.model().itemFromIndex(indexOrItem)
        if item is None:
            return f"(no item associated with index at row '{indexOrItem.row()}', column '{indexOrItem.column()}')"

        text = item.text().strip()
        parent_count = 0
        current_index = indexOrItem.parent()
        while current_index.isValid():
            parent_count += 1
            current_index = current_index.parent()

        return f"Item/Index at Row: {indexOrItem.row()}, Column: {indexOrItem.column()}, Ancestors: {parent_count}\nText for above item: {text}\n"

    def branchConnectorsDrawn(self) -> bool:
        return self.branch_connectors_enabled

    def drawConnectors(
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
    def __init__(self, settings_name: str = "RobustTreeView"):
        self.robust_tree_settings: QSettings = QSettings("HolocronToolsetV3", "RobustTreeView")
        self.settings: QSettings = self.robust_tree_settings if settings_name == "RobustTreeView" else QSettings("HolocronToolsetV3", settings_name)

    def get(self, key: str, default: Any) -> Any:
        # sourcery skip: assign-if-exp, reintroduce-else
        if qtpy.API_NAME in ("PyQt5", "PySide2"):
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

    def set(self, key: str, value: Any):
        self.settings.setValue(key, value)

    def textElideMode(self, default: int) -> int:
        return self.get("textElideMode", default)

    def setTextElideMode(self, value: int):
        self.set("textElideMode", value)

    def focusPolicy(self, default: int) -> int:
        return self.get("focusPolicy", default)

    def setFocusPolicy(self, value: int):
        self.set("focusPolicy", value)

    def layoutDirection(self, default: int) -> int:
        return self.get("layoutDirection", default)

    def setLayoutDirection(self, value: int):  # noqa: FBT001
        self.set("layoutDirection", value)

    def verticalScrollMode(self, default: int) -> int:  # noqa: FBT001
        return self.get("verticalScrollMode", default)

    def setVerticalScrollMode(self, value: int):  # noqa: FBT001
        self.set("verticalScrollMode", value)

    def uniformRowHeights(self, default: bool) -> bool:  # noqa: FBT001
        return self.get("uniformRowHeights", default)

    def setUniformRowHeights(self, value: bool):  # noqa: FBT001
        self.set("uniformRowHeights", value)

    def animations(self, default: bool) -> bool:  # noqa: FBT001
        return self.get("animations", default)

    def setAnimations(self, value: bool):  # noqa: FBT001
        self.set("animations", value)

    def autoScroll(self, default: bool) -> bool:  # noqa: FBT001
        return self.get("autoScroll", default)

    def setAutoScroll(self, value: bool):  # noqa: FBT001
        self.set("autoScroll", value)

    def expandsOnDoubleClick(self, default: bool) -> bool:  # noqa: FBT001
        return self.get("expandsOnDoubleClick", default)

    def setExpandsOnDoubleClick(self, value: bool):  # noqa: FBT001
        self.set("expandsOnDoubleClick", value)

    def autoFillBackground(self, default: bool) -> bool:  # noqa: FBT001
        return self.get("autoFillBackground", default)

    def setAutoFillBackground(self, value: bool):  # noqa: FBT001
        self.set("autoFillBackground", value)

    def alternatingRowColors(self, default: bool) -> bool:  # noqa: FBT001
        return self.get("alternatingRowColors", default)

    def setAlternatingRowColors(self, value: bool):  # noqa: FBT001
        self.set("alternatingRowColors", value)

    def indentation(self, default: int) -> int:
        return self.get("indentation", default)

    def setIndentation(self, value: int):
        self.set("indentation", value)

    def fontSize(self, default: int) -> int:
        return self.get("fontSize", default)

    def setFontSize(self, value: int):
        self.set("fontSize", value)
