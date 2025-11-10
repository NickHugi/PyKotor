from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from qtpy.QtCore import QSize, Qt
from qtpy.QtGui import QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QApplication, QListView, QVBoxLayout, QWidget

from utility.ui_libraries.qt.widgets.itemviews.abstractview import RobustAbstractItemView

if TYPE_CHECKING:
    from qtpy.QtWidgets import _QMenu


class RobustListView(RobustAbstractItemView, QListView):
    QT_WIDGET: ClassVar[type] = QListView

    def __new__(cls, *args, **kwargs):
        # For PySide6 compatibility with multiple inheritance
        return QListView.__new__(cls)

    def __init__(
        self,
        parent: QWidget | None = None,
        *args,
        should_call_qt_init: bool = True,
        **kwargs,
    ):
        if should_call_qt_init:
            QListView.__init__(self, parent, *args, **kwargs)
        RobustAbstractItemView.__init__(self, parent, *args, **kwargs)

    def build_context_menu(
        self,
        parent: QWidget | None = None,
    ) -> _QMenu:
        menu = super().build_context_menu(parent)

        list_menu = menu.addMenu("ListView")
        assert list_menu is not None
        settings_menu = list_menu.addMenu("Settings")
        assert settings_menu is not None
        actions_menu = list_menu.addMenu("Actions")
        assert actions_menu is not None

        self._add_exclusive_menu_action(
            settings_menu,
            "View Mode",
            self.viewMode,
            self.setViewMode,
            options={
                "List Mode": QListView.ViewMode.ListMode,
                "Icon Mode": QListView.ViewMode.IconMode
            },
            settings_key="viewMode"
        )

        self._add_menu_action(
            settings_menu,
            "Spacing",
            self.spacing,
            self.setSpacing,
            "spacing",
            param_type=int
        )
        self._add_menu_action(
            settings_menu,
            "Batch Size",
            self.batchSize,
            self.setBatchSize,
            "batchSize",
            param_type=int
        )
        self._add_exclusive_menu_action(
            settings_menu,
            "Layout Mode",
            self.layoutMode,
            self.setLayoutMode,
            options={
                "Single Pass": QListView.LayoutMode.SinglePass,
                "Batched": QListView.LayoutMode.Batched
            },
            settings_key="layoutMode"
        )
        self._add_menu_action(
            settings_menu,
            "Model Column",
            self.modelColumn,
            self.setModelColumn,
            "modelColumn",
            param_type=int
        )
        self._add_menu_action(
            settings_menu,
            "Uniform Item Sizes",
            self.uniformItemSizes,
            self.setUniformItemSizes,
            "uniformItemSizes"
        )
        self._add_menu_action(
            settings_menu,
            "Word Wrap",
            self.wordWrap,
            self.setWordWrap,
            "wordWrap"
        )
        self._add_menu_action(
            settings_menu,
            "Selection Rectangle Visible",
            self.isSelectionRectVisible,
            self.setSelectionRectVisible,
            "selectionRectVisible"
        )
        self._add_menu_action(
            settings_menu,
            "Item Alignment",
            self.itemAlignment,
            self.setItemAlignment,
            "itemAlignment",
            param_type=Qt.AlignmentFlag
        )
        self._add_exclusive_menu_action(
            settings_menu,
            "Flow",
            self.flow,
            self.setFlow,
            options={
                "Left to Right": QListView.Flow.LeftToRight,
                "Top to Bottom": QListView.Flow.TopToBottom
            },
            settings_key="flow"
        )
        self._add_menu_action(
            settings_menu,
            "Grid Size",
            self.gridSize,
            self.setGridSize,
            "gridSize",
            param_type=QSize
        )
        self._add_exclusive_menu_action(
            settings_menu,
            "Resize Mode",
            self.resizeMode,
            self.setResizeMode,
            options={
                "Fixed": QListView.ResizeMode.Fixed,
                "Adjust": QListView.ResizeMode.Adjust
            },
            settings_key="resizeMode"
        )
        self._add_exclusive_menu_action(
            settings_menu,
            "Movement",
            self.movement,
            self.setMovement,
            options={
                "Static": QListView.Movement.Static,
                "Free": QListView.Movement.Free,
                "Snap": QListView.Movement.Snap
            },
            settings_key="movement"
        )
        self._add_menu_action(
            settings_menu,
            "Wrapping",
            self.isWrapping,
            self.setWrapping,
            "wrapping"
        )

        self._add_simple_action(actions_menu, "Clear Selection", self.clearSelection)
        self._add_simple_action(actions_menu, "Select All", self.selectAll)
        self._add_simple_action(actions_menu, "Scroll to Top", lambda: self.scrollTo(self.model().index(0, 0), QListView.ScrollHint.PositionAtTop))  # pyright: ignore[reportOptionalMemberAccess]
        self._add_simple_action(actions_menu, "Scroll to Bottom", lambda: self.scrollTo(self.model().index(self.model().rowCount() - 1, 0), QListView.ScrollHint.PositionAtBottom))  # pyright: ignore[reportOptionalMemberAccess]
        self._add_simple_action(actions_menu, "Reset", self.reset)
        self._add_simple_action(actions_menu, "Clear Property Flags", self.clearPropertyFlags)
        self._add_simple_action(actions_menu, "Update Geometries", self.updateGeometries)

        row_visibility_menu = settings_menu.addMenu("Row Visibility")
        model = self.model()
        if model is not None:
            for row in range(model.rowCount()):
                self._add_menu_action(
                    row_visibility_menu,
                    f"Row {row}",
                    lambda r=row: self.isRowHidden(r),
                    lambda hide, r=row: self.setRowHidden(r, hide),
                    f"rowHidden_{row}"
                )

        return menu


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout(window)
    list_view = RobustListView()
    layout.addWidget(list_view)

    model = QStandardItemModel()
    q_app_style = QApplication.style()
    assert q_app_style is not None
    standard_pixmaps = [
        q_app_style.standardIcon(getattr(q_app_style.StandardPixmap, attr))
        for attr in dir(q_app_style.StandardPixmap)
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

    used_icons = standard_pixmaps

    for i, icon in enumerate(used_icons):
        item = QStandardItem(icon, f"Item {i}")
        model.appendRow(item)

    list_view.setModel(model)
    list_view.setViewMode(QListView.ViewMode.IconMode)
    list_view.setGridSize(QSize(100, 100))
    list_view.setResizeMode(QListView.ResizeMode.Adjust)

    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
