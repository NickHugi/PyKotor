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
    def __new__(cls, *args, **kwargs):
        # For PySide6 compatibility with multiple inheritance
        return QHeaderView.__new__(cls)

    @overload
    def __init__(self, orientation: Qt.Orientation | None = None, parent: QWidget | None = None, *args, should_call_qt_init: bool = True, **kwargs): ...
    @overload
    def __init__(self, parent: QWidget | None = None, *args, should_call_qt_init: bool = True, **kwargs): ...
    def __init__(
        self,
        *args,
        should_call_qt_init: bool = True,
        **kwargs,
    ):
        orientation, parent, rem_args, rem_kwargs = self._handle_args_kwargs(args, kwargs)
        if should_call_qt_init:
            QHeaderView.__init__(self, orientation, parent)
        RobustAbstractItemView.__init__(self, parent, *rem_args, **rem_kwargs)

    def _handle_args_kwargs(
        self,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> tuple[Qt.Orientation, QWidget | None, tuple[Any, ...], dict[str, Any]]:
        orientation = kwargs.pop("orientation", Qt.Orientation.Horizontal)
        parent = kwargs.pop("parent", None)
        remaining_args = list(args)

        if remaining_args:
            if isinstance(remaining_args[0], Qt.Orientation):
                orientation = remaining_args.pop(0)
            elif isinstance(remaining_args[0], QWidget):
                parent = remaining_args.pop(0)

        if remaining_args and isinstance(remaining_args[0], QWidget):
            parent = remaining_args.pop(0)

        if not isinstance(orientation, Qt.Orientation):
            if isinstance(orientation, QWidget):
                parent = orientation
            orientation = Qt.Orientation.Horizontal

        if not isinstance(parent, (QWidget, type(None))):
            raise TypeError(f"Expected QWidget or None for parent, got {parent}")

        return orientation, parent, tuple(remaining_args), kwargs

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
    sys.exit(app.exec())
