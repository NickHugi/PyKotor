from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loggerplus import RobustLogger
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QListWidgetItem

if TYPE_CHECKING:
    import weakref

    from pykotor.resource.generics.dlg import DLGLink


class DLGListWidgetItem(QListWidgetItem):
    def __init__(
        self,
        *args,
        link: DLGLink,
        ref: weakref.ref[DLGLink] | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.link: DLGLink = link
        self._link_ref: weakref.ref[DLGLink] | None = ref
        self._data_cache: dict[int, Any] = {}
        self.is_orphaned: bool = False

    def data(
        self,
        role: int = Qt.ItemDataRole.UserRole,
    ) -> Any:
        """Returns the data for the role. Uses cache if the item has been deleted."""
        if self.isDeleted():
            return self._data_cache.get(role)
        result: Any = super().data(role)
        self._data_cache[role] = result  # Update cache
        return result

    def setData(
        self,
        role: int,
        value: Any,
    ):
        """Sets the data for the role and updates the cache."""
        self._data_cache[role] = value  # Update cache
        super().setData(role, value)

    def isDeleted(self) -> bool:
        """Determines if this object has been deleted.

        Not sure what the proper method of doing so is, but this works fine.
        """
        try:
            self.isHidden()
            self.flags()
            self.isSelected()
        except RuntimeError as e:  # RuntimeError: wrapped C/C++ object of type DLGStandardItem has been deleted
            RobustLogger().warning(f"isDeleted suppressed the following exception: {e.__class__.__name__}: {e}")
            return True
        else:
            return False
