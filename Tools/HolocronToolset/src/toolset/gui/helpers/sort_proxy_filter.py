from __future__ import annotations

from abc import abstractmethod
from contextlib import suppress
from typing import TYPE_CHECKING, Any

from qtpy.QtCore import QSortFilterProxyModel, Qt
from qtpy.QtGui import QStandardItemModel

if TYPE_CHECKING:
    from qtpy.QtCore import QModelIndex, QObject


class TemplateFilterProxyModel(QSortFilterProxyModel):
    @abstractmethod
    def get_sort_value(self, index: QModelIndex) -> Any:
        ...


class RobustSortFilterProxyModel(TemplateFilterProxyModel):
    def __init__(
        self,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self.setDynamicSortFilter(True)
        self._sort_states: dict[int, int] = {}

    def toggle_sort(self, column: int):
        if column not in self._sort_states:
            self._sort_states[column] = 0
        self._sort_states[column] = (self._sort_states[column] + 1) % 3

        if self._sort_states[column] == 0:
            self.reset_sort()
        elif self._sort_states[column] == 1:
            self.sort(column, Qt.AscendingOrder)
        elif self._sort_states[column] == 2:
            self.sort(column, Qt.DescendingOrder)

    def reset_sort(self):
        self.sort(-1)  # Reset sorting
        self.invalidate()  # Force a refresh
        self._sort_states = {}

    def get_sort_value(self, index: QModelIndex) -> Any:
        """Return the sort value based on the column."""
        srcModel = self.sourceModel()
        assert isinstance(srcModel, QStandardItemModel)
        return self.sourceModel().data(index)

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        left_data = self.get_sort_value(left)
        right_data = self.get_sort_value(right)

        with suppress(Exception):
            if type(left_data) is type(right_data) and hasattr(left_data, "__lt__"):
                return left_data < right_data
        return super().lessThan(left, right)
