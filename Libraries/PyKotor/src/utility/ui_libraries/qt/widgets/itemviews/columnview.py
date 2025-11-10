from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtGui import QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QAbstractItemView, QApplication, QColumnView, QVBoxLayout, QWidget

from utility.ui_libraries.qt.widgets.itemviews.abstractview import RobustAbstractItemView

if TYPE_CHECKING:
    from qtpy.QtCore import QModelIndex
    from qtpy.QtWidgets import QMenu


class RobustColumnView(RobustAbstractItemView, QColumnView):
    def __new__(cls, *args, **kwargs):
        # For PySide6 compatibility with multiple inheritance
        return QColumnView.__new__(cls)

    def __init__(
        self,
        parent: QWidget | None = None,
        *args,
        should_call_qt_init: bool = True,
        **kwargs,
    ):
        if should_call_qt_init:
            QColumnView.__init__(self, parent)
        RobustAbstractItemView.__init__(self, parent, *args, **kwargs)

    def build_context_menu(self, parent: QWidget | None = None) -> QMenu:
        menu = RobustAbstractItemView.build_context_menu(self, parent)

        column_menu = menu.addMenu("ColumnView")

        self._add_menu_action(
            column_menu,
            "Resize Grips Visible",
            self.resizeGripsVisible,
            self.setResizeGripsVisible,
            "resizeGripsVisible"
        )
        self._add_menu_action(
            column_menu,
            "Column Widths",
            self.columnWidths,
            self.setColumnWidths,
            "columnWidths",
            param_type=list
        )
        self._add_menu_action(
            column_menu,
            "Preview Widget",
            self.previewWidget,
            self.setPreviewWidget,
            "previewWidget",
            param_type=QWidget
        )

        # Actions submenu
        actions_menu = column_menu.addMenu("Actions")
        self._add_simple_action(actions_menu, "Select All", self.selectAll)
        self._add_simple_action(actions_menu, "Update Preview Widget", lambda: self.updatePreviewWidget.emit())

        # View submenu
        view_menu = column_menu.addMenu("View")
        self._add_simple_action(view_menu, "Scroll To Current", lambda: self.scrollTo(self.currentIndex()))
        self._add_simple_action(view_menu, "Update Geometries", self.updateGeometries)

        return menu

    def createColumn(self, rootIndex: QModelIndex) -> QAbstractItemView:  # noqa: N803
        column = super().createColumn(rootIndex)
        if isinstance(column, QAbstractItemView):
            self.initializeColumn(column)
        return column

    def initializeColumn(self, column):
        if isinstance(column, RobustAbstractItemView):
            column.build_context_menu()

if __name__ == "__main__":
    import sys

    from qtpy.QtWidgets import QApplication, QVBoxLayout, QWidget
    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout()
    window.setLayout(layout)
    column_view = RobustColumnView()
    layout.addWidget(column_view)

    model = QStandardItemModel()
    standard_pixmaps = [
        QApplication.style().standardIcon(getattr(QApplication.style().StandardPixmap, attr))
        for attr in dir(QApplication.style().StandardPixmap)
        if not attr.startswith("_") and attr not in (
            "as_integer_ratio",
            "bit_length",
            "conjugate",
            "denominator",
            "from_bytes",
            "imag",
            "numerator",
            "real",
            "to_bytes",
        )
    ]

    root_item = model.invisibleRootItem()
    for i, icon in enumerate(standard_pixmaps):
        item = QStandardItem(icon, f"Item {i+1}")
        root_item.appendRow(item)
        for j in range(10):
            child_item = QStandardItem(f"Child {j+1} of Item {i+1}")
            item.appendRow(child_item)
            for k in range(12):
                child_item = QStandardItem(f"Child {k+1} of Item {j+1}")
                item.appendRow(child_item)

    column_view.setModel(model)
    column_view.setColumnWidths([200, 200, 200])
    column_view.setResizeGripsVisible(True)

    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
