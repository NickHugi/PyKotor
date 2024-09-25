from __future__ import annotations

from typing import TYPE_CHECKING, Any, overload

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QHeaderView, QWidget

from utility.ui_libraries.qt.widgets.itemviews.abstractview import (
    RobustAbstractItemView,
)

if TYPE_CHECKING:
    from qtpy.QtWidgets import QMenu


class RobustHeaderView(RobustAbstractItemView, QHeaderView):
    @overload
    def __init__(
        self,
        orientation: Qt.Orientation | None = None,
        parent: QWidget | None = None,
    ):
        ...
    @overload
    def __init__(
        self,
        parent: QWidget | None = None,
    ):
        ...
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        orientation, parent = self._handle_args_kwargs(args, kwargs)
        QHeaderView.__init__(self, orientation, parent)
        RobustAbstractItemView.__init__(self, parent, no_qt_init=True)

    def _handle_args_kwargs(
        self,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> tuple[Qt.Orientation, QWidget | None]:
        orientation = kwargs.pop("orientation", args[0] if args else Qt.Orientation.Horizontal)
        parent = kwargs.pop("parent", args[0] if args else None)
        if len(args) > 1:
            parent = args[1]
        if not isinstance(orientation, Qt.Orientation):
            if isinstance(orientation, QWidget):
                parent = orientation
            orientation = Qt.Orientation.Horizontal
        if not isinstance(parent, (QWidget, type(None))):
            raise TypeError(f"Expected QWidget or None for parent, got {parent}")
        return orientation, parent

    def build_context_menu(self, parent: QWidget | None = None) -> QMenu:
        menu = super().build_context_menu(parent)
        header_menu = menu.addMenu("HeaderView")

        self._add_menu_action(
            header_menu,
            "Sections Movable",
            self.sectionsMovable,
            self.setSectionsMovable,
            "sectionsMovable"
        )
        self._add_menu_action(
            header_menu,
            "Sections Clickable",
            self.sectionsClickable,
            self.setSectionsClickable,
            "sectionsClickable"
        )
        self._add_menu_action(
            header_menu,
            "Sort Indicator Shown",
            self.isSortIndicatorShown,
            self.setSortIndicatorShown,
            "sortIndicatorShown"
        )
        self._add_menu_action(
            header_menu,
            "Stretch Last Section",
            self.stretchLastSection,
            self.setStretchLastSection,
            "stretchLastSection"
        )
        self._add_menu_action(
            header_menu,
            "Cascading Section Resizes",
            self.cascadingSectionResizes,
            self.setCascadingSectionResizes,
            "cascadingSectionResizes"
        )

        return menu
# ... existing code ...

if __name__ == "__main__":
    import sys

    from qtpy.QtWidgets import QApplication, QTableWidget, QTableWidgetItem

    app = QApplication(sys.argv)

    # Create a QTableWidget to demonstrate the RobustHeaderView
    table = QTableWidget(5, 3)
    table.setHorizontalHeader(RobustHeaderView(Qt.Orientation.Horizontal, table))
    table.setVerticalHeader(RobustHeaderView(Qt.Orientation.Vertical, table))

    # Set some sample data
    for row in range(5):
        for col in range(3):
            table.setItem(row, col, QTableWidgetItem(f"Item {row},{col}"))

    # Set header labels
    table.setHorizontalHeaderLabels(["Column 1", "Column 2", "Column 3"])
    table.setVerticalHeaderLabels([f"Row {i+1}" for i in range(5)])

    # Show the table
    table.resize(400, 300)
    table.show()

    # Run the application
    sys.exit(app.exec_())
