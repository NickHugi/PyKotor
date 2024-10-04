from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QMainWindow
from qtpy.QtWidgets import QTreeWidget, QTreeWidgetItem

from utility.ui_libraries.qt.widgets.itemviews.treeview import RobustTreeView

if TYPE_CHECKING:
    from qtpy.QtWidgets import QMenu, QWidget


class RobustTreeWidget(QTreeWidget, RobustTreeView):
    """A tree widget that supports common features and settings."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *args,
        use_columns: bool = False,
        should_call_qt_init: bool = True,
        **kwargs,
    ):
        if should_call_qt_init:
            QTreeWidget.__init__(self, parent, *args, **kwargs)

        RobustTreeView.__init__(
            self,
            parent,
            *args,
            use_columns=use_columns,
            should_call_qt_init=False,  # QTreeView.__init__ should not be called since we already call QTreeWidget.__init__ and handle that argument.
            **kwargs,
        )

    def build_context_menu(self, parent: QWidget | None = None) -> QMenu:
        menu = super().build_context_menu(parent)

        tree_widget_menu = menu.addMenu("TreeWidget")
        advanced_menu = tree_widget_menu.addMenu("Advanced")

        # Tree-specific actions
        self._add_menu_action(
            tree_widget_menu,
            "Expand Current Item",
            lambda: self.isExpanded(self.currentIndex()),
            lambda x: self.expandItem(self.currentItem()) if x else self.collapseItem(self.currentItem()),
            "expandCurrentItem",
        )
        self._add_simple_action(tree_widget_menu, "Scroll to Current Item", lambda: self.scrollToItem(self.currentItem()))
        self._add_menu_action(
            tree_widget_menu,
            "Sort Items",
            self.isSortingEnabled,
            self.setSortingEnabled,
            "sortingEnabled",
        )
        self._add_menu_action(
            tree_widget_menu,
            "Column Count",
            self.columnCount,
            self.setColumnCount,
            "columnCount",
            param_type=int,
        )

        # Advanced actions
        self._add_menu_action(
            advanced_menu,
            "Header Hidden",
            self.isHeaderHidden,
            self.setHeaderHidden,
            "headerHidden",
        )
        self._add_menu_action(
            advanced_menu,
            "Root Is Decorated",
            self.rootIsDecorated,
            self.setRootIsDecorated,
            "rootIsDecorated",
        )
        self._add_menu_action(
            advanced_menu,
            "Items Expandable",
            self.itemsExpandable,
            self.setItemsExpandable,
            "itemsExpandable",
        )
        self._add_menu_action(
            advanced_menu,
            "Animated",
            self.isAnimated,
            self.setAnimated,
            "animated",
        )
        self._add_menu_action(
            advanced_menu,
            "Allow Expand on Single Click",
            self.allColumnsShowFocus,
            self.setAllColumnsShowFocus,
            "allColumnsShowFocus",
        )
        self._add_menu_action(
            advanced_menu,
            "Word Wrap",
            self.wordWrap,
            self.setWordWrap,
            "wordWrap",
        )

        # Item manipulation actions
        item_menu = tree_widget_menu.addMenu("Item Actions")
        self._add_simple_action(item_menu, "Add Top Level Item", lambda: self.addTopLevelItem(QTreeWidgetItem(["New Item"])))
        self._add_simple_action(item_menu, "Remove Current Item", lambda: self.takeTopLevelItem(self.indexOfTopLevelItem(self.currentItem())) if self.currentItem() else None)
        self._add_simple_action(item_menu, "Clear All Items", self.clear)
        self._add_simple_action(item_menu, "Edit Current Item", lambda: self.editItem(self.currentItem(), 0) if self.currentItem() else None)

        return menu


if __name__ == "__main__":
    import sys

    from qtpy.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget

    app = QApplication(sys.argv)

    # Create main window
    window = QMainWindow()
    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    layout = QVBoxLayout(central_widget)

    # Create RobustTreeWidget
    tree_widget = RobustTreeWidget()
    layout.addWidget(tree_widget)

    # Add some sample items
    for i in range(5):
        parent = QTreeWidgetItem(tree_widget, [f"Parent {i+1}"])
        for j in range(3):
            QTreeWidgetItem(parent, [f"Child {j+1} of Parent {i+1}"])

    # Add a button to show context menu
    def show_context_menu():
        menu = tree_widget.build_context_menu()
        menu.exec_(tree_widget.mapToGlobal(tree_widget.rect().center()))

    context_menu_button = QPushButton("Show Context Menu")
    context_menu_button.clicked.connect(show_context_menu)
    layout.addWidget(context_menu_button)

    window.setGeometry(100, 100, 400, 500)
    window.setWindowTitle("RobustTreeWidget Test")
    window.show()

    sys.exit(app.exec_())
