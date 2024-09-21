from __future__ import annotations

from typing import TYPE_CHECKING, cast

import qtpy

from qtpy.QtCore import QAbstractItemModel, QTimer, Qt
from qtpy.QtGui import QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QHeaderView, QMenu, QPushButton, QStyle, QStyleOptionViewItem, QTreeView, QVBoxLayout

from utility.ui_libraries.qt.widgets.itemviews.abstractview import RobustAbstractItemView
from utility.ui_libraries.qt.widgets.itemviews.html_delegate import HTMLDelegate

if TYPE_CHECKING:
    from qtpy.QtCore import QModelIndex
    from qtpy.QtGui import QResizeEvent, QWheelEvent
    from qtpy.QtWidgets import QAbstractItemDelegate, QStyledItemDelegate, QWidget


class RobustTreeView(RobustAbstractItemView, QTreeView):
    """A tree view that supports common features and settings."""
    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        use_columns: bool = False,
        settings_name: str | None = None,
    ):
        self.branch_connectors_enabled: bool = False
        self.header_visible: bool = False
        super().__init__(parent, settings_name=settings_name)
        self.layout_changed_debounce_timer: QTimer = QTimer(self)
        self.original_stylesheet: str = self.styleSheet()
        self.header_visible: bool = self.get_setting("horizontalScrollBarVisible", False)  # noqa: FBT003
        self.header().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.header().customContextMenuRequested.connect(lambda pos: self.show_header_context_menu(pos, self.header()))
        if not use_columns:
            self.set_horizontal_scrollbar(state=False)

    def build_context_menu(self, parent: QWidget | None = None) -> QMenu:
        print(f"{self.__class__.__name__}.build_context_menu")
        menu = super().build_context_menu(parent)

        tree_view_menu = menu.addMenu("TreeView")
        advanced_menu = tree_view_menu.addMenu("Advanced")

        # Actions submenu items
        self._add_simple_action(
            tree_view_menu,
            "Resize Column To Contents",
            lambda: None if self.model() is None else (self.resizeColumnToContents(i) for i in range(cast(QAbstractItemModel, self.model()).columnCount())),
        )
        self._add_simple_action(tree_view_menu, "Expand All", self.expandAll)
        self._add_simple_action(tree_view_menu, "Collapse All", self.collapseAll)
        self._add_simple_action(tree_view_menu, "Expand To Depth", lambda: self.expandToDepth(3))  # Default depth of 3
        self._add_simple_action(tree_view_menu, "Reset Indentation", self.resetIndentation)
        self._add_simple_action(tree_view_menu, "Select All", self.selectAll)

        # Settings submenu items
        self._add_menu_action(advanced_menu, "Uniform Row Heights", self.uniformRowHeights, self.setUniformRowHeights, "uniformRowHeights")
        self._add_menu_action(tree_view_menu, "Show/Hide Branch Connectors", self.branch_connectors_drawn, self.draw_connectors, "drawBranchConnectors")
        self._add_menu_action(tree_view_menu, "Expand Items on Double Click", self.expandsOnDoubleClick, self.setExpandsOnDoubleClick, "expandsOnDoubleClick")
        self._add_menu_action(tree_view_menu, "Tree Indentation", self.indentation, self.setIndentation, "indentation", param_type=int)
        self._add_menu_action(tree_view_menu, "Show Horizontal Scrollbar", lambda: self.header_visible, self.set_horizontal_scrollbar, "horizontalScrollBarVisible")
        self._add_menu_action(tree_view_menu, "Vertical Spacing",
                            lambda: getattr(self.itemDelegate(), "customVerticalSpacing", 0),
                            lambda x: getattr(self.itemDelegate(), "setVerticalSpacing", lambda _: None)(x),
                            "verticalSpacing", param_type=int)
        self._add_menu_action(
            tree_view_menu,
            "Expand All Root Item Children",
            lambda: self.get_setting("ExpandRootChildren", False),  # noqa: FBT003
            lambda value: self.set_setting("ExpandRootChildren", value),
            settings_key="ExpandRootChildren",
        )
        self._add_menu_action(tree_view_menu, "Word Wrap", self.wordWrap, self.setWordWrap, "wordWrap")
        self._add_menu_action(advanced_menu, "All Columns Show Focus", self.allColumnsShowFocus, self.setAllColumnsShowFocus, "allColumnsShowFocus")
        self._add_menu_action(tree_view_menu, "Animated", self.isAnimated, self.setAnimated, "animated")
        self._add_menu_action(tree_view_menu, "Sorting Enabled", self.isSortingEnabled, self.setSortingEnabled, "sortingEnabled")
        self._add_menu_action(advanced_menu, "Items Expandable", self.itemsExpandable, self.setItemsExpandable, "itemsExpandable")
        self._add_menu_action(advanced_menu, "Root Is Decorated", self.rootIsDecorated, self.setRootIsDecorated, "rootIsDecorated")
        self._add_menu_action(advanced_menu, "Header Hidden", self.isHeaderHidden, self.setHeaderHidden, "headerHidden")
        self._add_menu_action(tree_view_menu, "Auto Expand Delay", self.autoExpandDelay, self.setAutoExpandDelay, "autoExpandDelay", param_type=int)
        self._add_menu_action(advanced_menu, "Tree Position", self.treePosition, self.setTreePosition, "treePosition", param_type=int)

        return menu

    def build_header_context_menu(self, parent: QWidget | None = None) -> QMenu:
        """Subclass should override this to add header-specific actions."""
        header_menu = QMenu("Header", self if parent is None else parent)
        self._add_simple_action(header_menu, "Toggle Visibility", lambda: self.header().setVisible(not self.header().isVisible()))
        self._add_simple_action(header_menu, "Toggle First Section Movable", lambda: self.header().setFirstSectionMovable(not self.header().isFirstSectionMovable()))
        self._add_simple_action(header_menu, "Toggle Sections Movable", lambda: self.header().setSectionsMovable(not self.header().sectionsMovable()))
        self._add_simple_action(header_menu, "Toggle Sections Clickable", lambda: self.header().setSectionsClickable(not self.header().sectionsClickable()))
        self._add_simple_action(header_menu, "Toggle Stretch Last Section", lambda: self.header().setStretchLastSection(not self.header().stretchLastSection()))
        self._add_simple_action(header_menu, "Toggle Cascading Section Resizes", lambda: self.header().setCascadingSectionResizes(not self.header().cascadingSectionResizes()))
        self._add_simple_action(header_menu, "Toggle Highlight Sections", lambda: self.header().setHighlightSections(not self.header().highlightSections()))

        # Resize modes submenu
        resize_mode_menu = header_menu.addMenu("Resize Mode")
        model: QAbstractItemModel | None = self.model()
        if model is not None:
            for i in range(self.header().count()):
                section_name = model.headerData(i, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
            self._add_exclusive_menu_action(
                resize_mode_menu,
                f"[{i}] {section_name}",
                lambda idx=i: self.header().sectionResizeMode(idx),
                (lambda mode, idx=i: self.header().setSectionResizeMode(idx, mode)) if qtpy.QT5 else (lambda mode, idx=i: self.header().setSectionResizeMode(idx, QHeaderView.ResizeMode(mode))),
                options={
                    "Interactive": QHeaderView.ResizeMode.Interactive,
                    "Fixed": QHeaderView.ResizeMode.Fixed,
                    "Stretch": QHeaderView.ResizeMode.Stretch,
                    "Resize to Contents": QHeaderView.ResizeMode.ResizeToContents
                },
                settings_key=f"headerResizeMode_{i}"
            )

        # Sizing options
        sizing_menu = header_menu.addMenu("Sizing")
        self._add_simple_action(sizing_menu, "Reset Default Section Size", self.header().resetDefaultSectionSize)
        self._add_menu_action(sizing_menu, "Auto-fit Columns", lambda: self.get_setting("autoResizeEnabled", True, bool), self.set_auto_resize_enabled, "autoResizeEnabled")  # noqa: FBT003
        self._add_menu_action(sizing_menu, "Set Maximum Section Size", self.header().maximumSectionSize, self.header().setMaximumSectionSize, "maximumSectionSize", param_type=int)  # noqa: E501
        self._add_menu_action(sizing_menu, "Set Minimum Section Size", self.header().minimumSectionSize, self.header().setMinimumSectionSize, "minimumSectionSize", param_type=int)  # noqa: E501
        self._add_menu_action(sizing_menu, "Set Default Section Size", self.header().defaultSectionSize, self.header().setDefaultSectionSize, "defaultSectionSize", param_type=int)  # noqa: E501
        self._add_menu_action(sizing_menu, "Set Resize Contents Precision", self.header().resizeContentsPrecision, self.header().setResizeContentsPrecision, "resizeContentsPrecision", param_type=int)  # noqa: E501

        # Alignment and stretching
        self._add_exclusive_menu_action(
            header_menu,
            "Alignment",
            self.header().defaultAlignment,
            self.header().setDefaultAlignment,
            options={
                "Left": Qt.AlignmentFlag.AlignLeft,
                "Center": Qt.AlignmentFlag.AlignCenter,
                "Right": Qt.AlignmentFlag.AlignRight
            },
            settings_key="headerDefaultAlignment",
            param_type=Qt.AlignmentFlag,
        )

        # Sorting
        sorting_menu = header_menu.addMenu("Sorting")
        self._add_simple_action(sorting_menu, "Toggle Sort Indicator", lambda: self.header().setSortIndicatorShown(not self.header().isSortIndicatorShown()))
        sort_order_menu = sorting_menu.addMenu("Sort Order")
        self._add_exclusive_menu_action(
            sort_order_menu,
            "Sort Order",
            self.header().sortIndicatorOrder,
            lambda order: self.header().setSortIndicator(self.header().sortIndicatorSection(), order),
            options={
                "Ascending": Qt.SortOrder.AscendingOrder,
                "Descending": Qt.SortOrder.DescendingOrder
            },
            settings_key="headerSortOrder",
            param_type=Qt.SortOrder,
        )

        # Miscellaneous
        self._add_simple_action(header_menu, "Toggle Highlight Sections", lambda: self.header().setHighlightSections(not self.header().highlightSections()))
        self._add_menu_action(
            header_menu,
            "Set Offset",
            lambda: self.header().offset(),
            lambda x: self.header().setOffset(x),
            settings_key="headerOffset",
            param_type=int
        )
        self._add_simple_action(header_menu, "Set Offset to Last Section", self.header().setOffsetToLastSection)
        self._add_menu_action(
            header_menu,
            "Set Offset to Section Position",
            lambda: self.header().offset(),
            lambda x: self.header().setOffsetToSectionPosition(x),
            settings_key="headerOffsetToSectionPosition",
            param_type=int
        )

        # Section-specific actions
        section_menu = header_menu.addMenu("Sections")
        for i in range(self.header().count()):
            section_submenu = section_menu.addMenu(f"Section {i}")
            self._add_simple_action(section_submenu, "Hide/Show", lambda idx=i: self.header().setSectionHidden(idx, not self.header().isSectionHidden(idx)))
            self._add_menu_action(
                section_submenu,
                "Resize",
                lambda idx=i: self.header().sectionSize(idx),
                lambda size, idx=i: self.header().resizeSection(idx, size),
                settings_key=f"headerSectionSize_{i}",
                param_type=int
            )
            self._add_menu_action(
                section_submenu,
                "Move",
                lambda idx=i: self.header().visualIndex(idx),
                lambda new_idx, idx=i: self.header().moveSection(idx, new_idx),
                settings_key=f"headerSectionPosition_{i}",
                param_type=int
            )

        return header_menu

    def _enable_horizontal_scrollbar_when_header_single_column_and_hidden(self, *, use_deprecated_method: bool = False):
        """Fixes the horizontal scrollbar when the header is single column and hidden.

        This solution was pulled from stackoverflow <insert link here>
        """
        # This is an alternate strat but it causes weird behavior such as when you're scrolling near the end of the tree the
        # amount scrolled becomes larger than the other parts of the tree
        if use_deprecated_method:
            self.setColumnWidth(0, 2000)
            return
        h: QHeaderView = self.header()
        h.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        h.setStretchLastSection(False)
        h.setMinimumSectionSize(self.geometry().width() * 5)
        h.setDefaultSectionSize(self.geometry().width() * 10)
        h.hide()
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def _disable_horizontal_scrollbar_when_header_single_column_and_hidden(self):
        """Disables the horizontal scrollbar when the header is single column and hidden.

        This solution is a custom inverse of the solution pulled from stackoverflow <insert link here>
        """
        h: QHeaderView = self.header()
        h.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        h.setStretchLastSection(True)
        h.setMinimumSectionSize(0)  # Reset to default
        h.setDefaultSectionSize(0)  # Reset to default
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def set_horizontal_scrollbar(self, state: bool):  # noqa: FBT001
        model = self.model()
        if (model is None or model.columnCount() == 1) and self.header().isHidden():
            if not state:
                self._enable_horizontal_scrollbar_when_header_single_column_and_hidden()
            else:
                self._disable_horizontal_scrollbar_when_header_single_column_and_hidden()
        elif not state:
            self.horizontalScrollBar().hide()
        else:
            self.horizontalScrollBar().show()
        self.set_setting("horizontalScrollBarVisible", state)

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

    def _wheel_changes_indent_size(self, event: QWheelEvent) -> bool:
        delta: int = event.angleDelta().x()  # Same as y() in the other funcs but returned in x() due to AltModifier I guess. Not in the documentation.
        #print(f"wheel changes indent delta: {delta}")
        if not delta:
            return False
        self.setIndentation(max(0, self.indentation() + (1 if delta > 0 else -1)))
        self.debounce_layout_changed()
        return True

    def _wheel_changes_horizontal_scroll(self, event: QWheelEvent) -> bool:
        delta: int = event.angleDelta().y()
        if not delta:
            return True
        if self.horizontalScrollMode() == self.ScrollMode.ScrollPerItem:
            delta = self.indentation() * (1 if delta > 0 else -1)
        else:
            delta = -self.get_text_size() if delta > 0 else self.get_text_size()
        self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + delta)
        return True

    def update_columns_after_text_size_change(self):
        model: QAbstractItemModel | None = self.model()
        assert model is not None
        for column in range(model.columnCount()):
            self.resizeColumnToContents(column)

    def branch_connectors_drawn(self) -> bool:
        return self.branch_connectors_enabled

    def resize_all_columns_to_fit(self):
        header: QHeaderView = self.header()
        assert header is not None, "Header is None in autoFitColumns"
        for col in range(header.count()):
            self.resizeColumnToContents(col)

    def reset_column_widths(self):
        header: QHeaderView = self.header()
        assert header is not None, "Header is None in resetColumnWidths"
        for col in range(header.count()):
            header.resizeSection(col, header.defaultSectionSize())

    def set_auto_resize_enabled(self, state: bool):  # noqa: FBT001
        self.set_setting("autoResizeEnabled", state)
        if self.get_setting("autoResizeEnabled", True, bool):  # noqa: FBT003
            self.resize_all_columns_to_fit()
        else:
            self.reset_column_widths()

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

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.debounce_layout_changed()

    def wheelEvent(
        self,
        event: QWheelEvent,
    ) -> None:
        modifiers = event.modifiers()
        handled: bool | None = None
        if bool(modifiers & Qt.KeyboardModifier.ShiftModifier):
            handled = self._wheel_changes_horizontal_scroll(event)
        elif bool(modifiers & Qt.KeyboardModifier.AltModifier):
            handled = self._wheel_changes_indent_size(event)
        if handled is not True:
            super().wheelEvent(event)

    def itemDelegate(self, *args) -> HTMLDelegate | QStyledItemDelegate | QAbstractItemDelegate:
        return super().itemDelegate()

    def setItemDelegate(self, delegate: HTMLDelegate | QStyledItemDelegate):
        assert isinstance(delegate, HTMLDelegate)
        super().setItemDelegate(delegate)

    def model(self) -> QStandardItemModel | QAbstractItemModel | None:
        return super().model()

    def styleOptionForIndex(self, index: QModelIndex) -> QStyleOptionViewItem:
        """Construct and configure a QStyleOptionViewItem for the given index.

        Required for non-pyqt5 versions of Qt.
        """
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
                option.state = cast(QStyle.StateFlag, option.state & ~QStyle.StateFlag.State_Enabled)
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


if __name__ == "__main__":
    import sys

    from qtpy.QtGui import QStandardItem, QStandardItemModel
    from qtpy.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QPushButton, QVBoxLayout, QWidget

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("RobustTreeView Demo")
            self.setGeometry(100, 100, 800, 600)

            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            layout = QVBoxLayout(central_widget)

            self.tree_view: RobustTreeView = RobustTreeView(use_columns=True)
            layout.addWidget(self.tree_view)

            # Create a model and set it to the tree view
            self.model: QStandardItemModel = QStandardItemModel()
            self.model.setHorizontalHeaderLabels(["Name", "Value"])
            self.tree_view.setModel(self.model)

            # Add some dummy items
            self.add_dummy_items()

            # Add buttons for interaction
            button_layout = QHBoxLayout()
            add_button: QPushButton = QPushButton("Add Item")
            add_button.clicked.connect(self.add_item)
            delete_button: QPushButton = QPushButton("Delete Selected")
            delete_button.clicked.connect(self.delete_selected)
            button_layout.addWidget(add_button)
            button_layout.addWidget(delete_button)
            layout.addLayout(button_layout)

            # Enable drag and drop
            self.tree_view.setDragEnabled(True)
            self.tree_view.setAcceptDrops(True)
            self.tree_view.setDropIndicatorShown(True)
            self.tree_view.setDragDropMode(QTreeView.DragDropMode.InternalMove)

        def add_dummy_items(self):
            root = self.model.invisibleRootItem()
            for i in range(3):
                parent = QStandardItem(f"Parent {i+1}")
                value = QStandardItem(f"Value {i+1}")
                root.appendRow([parent, value])
                for j in range(2):
                    child = QStandardItem(f"Child {i+1}-{j+1}")
                    child_value = QStandardItem(f"Child Value {i+1}-{j+1}")
                    parent.appendRow([child, child_value])

        def add_item(self):
            selected = self.tree_view.selectedIndexes()
            if selected:
                parent = self.model.itemFromIndex(selected[0])
            else:
                parent = self.model.invisibleRootItem()
            new_item = QStandardItem("New Item")
            new_value = QStandardItem("New Value")
            parent.appendRow([new_item, new_value])

        def delete_selected(self):
            selected = self.tree_view.selectedIndexes()
            if selected:
                self.model.removeRow(selected[0].row(), selected[0].parent())

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
