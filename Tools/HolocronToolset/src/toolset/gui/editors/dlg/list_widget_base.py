from __future__ import annotations

import json
import weakref

from typing import TYPE_CHECKING, Any

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QListWidget, QListWidgetItem, QWidget

from pykotor.resource.generics.dlg import DLGEntry, DLGLink
from toolset.gui.editors.dlg.constants import QT_STANDARD_ITEM_FORMAT, _DLG_MIME_DATA_ROLE, _EXTRA_DISPLAY_ROLE
from utility.ui_libraries.qt.widgets.itemviews.html_delegate import HTMLDelegate

if TYPE_CHECKING:
    import weakref

    from qtpy.QtCore import QMimeData
    from qtpy.QtGui import QFocusEvent, QMouseEvent
    from qtpy.QtWidgets import QAbstractItemDelegate, QWidget
    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from toolset.gui.editors.dlg.editor import DLGEditor
    from utility.ui_libraries.qt.widgets.itemviews.html_delegate import HTMLDelegate


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
        # self._link_ref: weakref.ref[DLGLink] = weakref.ref(link)  # Store a weak reference to the link
        self._data_cache: dict[int, Any] = {}
        self.is_orphaned = False

    def data(
        self,
        role: int = Qt.ItemDataRole.UserRole,
    ) -> Any:
        """Returns the data for the role. Uses cache if the item has been deleted."""
        if self.isDeleted():
            return self._data_cache.get(role)
        result = super().data(role)
        self._data_cache[role] = result  # Update cache
        return result

    def setData(
        self,
        role: int,
        value: Any,
    ) -> None:
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


class DLGListWidget(QListWidget):
    def __init__(
        self,
        parent: DLGEditor | None = None,
    ):
        super().__init__(parent)
        self.editor: DLGEditor | None = parent
        self.dragged_item: DLGListWidgetItem | None = None
        self.currently_hovered_item: DLGListWidgetItem | None = None
        self.use_hover_text: bool = True

        self.itemPressed.connect(lambda: None if self.editor is None else self.editor.jump_to_node(getattr(self.currentItem(), "link", None)))
        self.itemDoubleClicked.connect(lambda: None if self.editor is None else self.editor.focus_on_node(getattr(self.currentItem(), "link", None)))
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(lambda pt: None if self.editor is None else self.editor.on_list_context_menu(pt, self))
        self.setMouseTracking(True)

    def itemDelegate(self) -> HTMLDelegate | QAbstractItemDelegate | None:
        return super().itemDelegate()

    def dropMimeData(
        self,
        index: int,
        data: QMimeData,
        action: Qt.DropAction,
    ) -> bool:
        """Handle custom data dropping."""
        assert self.editor is not None
        if data.hasFormat(QT_STANDARD_ITEM_FORMAT):
            item_data: list[dict[Literal["row", "column", "roles"], Any]] = self.editor.ui.dialogTree.parse_mime_data(data)
            link: DLGLink[Any] = DLGLink.from_dict(json.loads(item_data[0]["roles"][_DLG_MIME_DATA_ROLE]))
            newItem = DLGListWidgetItem(link=link)
            self.update_item(newItem)
            self.addItem(newItem)
            return True
        return False

    def mouseMoveEvent(
        self,
        event: QMouseEvent,
    ) -> None:
        """Handle hover text display."""
        super().mouseMoveEvent(event)
        if not self.use_hover_text:
            return

        item: QListWidgetItem | None = self.itemAt(event.pos())
        if not isinstance(item, DLGListWidgetItem) or item is self.currently_hovered_item:
            return

        # Reset previous hover item
        if self.currently_hovered_item is not None and not self.currently_hovered_item.isDeleted() and self.row(self.currently_hovered_item) != -1:
            self._swap_display_text(self.currently_hovered_item)

        # Set new hover item
        self.currently_hovered_item = item
        self._swap_display_text(item)
        view_port: QWidget | None = self.viewport()
        if view_port is not None:
            view_port.update()
        self.update()

    def focusOutEvent(
        self,
        event: QFocusEvent,
    ):
        super().focusOutEvent(event)
        if self.currently_hovered_item is not None and not self.currently_hovered_item.isDeleted() and self.row(self.currently_hovered_item) != -1:
            # print("Reset old hover item")
            hover_display: str = self.currently_hovered_item.data(Qt.ItemDataRole.DisplayRole)
            default_display: str = self.currently_hovered_item.data(_EXTRA_DISPLAY_ROLE)
            # print("hover display:", hover_display, "default_display", default_display)
            self.currently_hovered_item.setData(Qt.ItemDataRole.DisplayRole, default_display)
            self.currently_hovered_item.setData(_EXTRA_DISPLAY_ROLE, hover_display)
        self.currently_hovered_item = None

    def update_item(
        self,
        item: DLGListWidgetItem,
        cached_paths: tuple[str, str, str] | None = None,
    ):
        """Refreshes the item text and formatting based on the node data."""
        assert self.editor is not None
        link_parent_path, link_partial_path, node_path = self.editor.get_item_dlg_paths(item) if cached_paths is None else cached_paths
        color: Literal["red", "blue"] = "red" if isinstance(item.link.node, DLGEntry) else "blue"
        if link_parent_path:
            link_parent_path += "\\"
        else:
            link_parent_path = ""
        hover_text_1: str = f"<span style='color:{color}; display:inline-block; vertical-align:top;'>{link_partial_path} --></span>"
        display_text_2: str = f"<div class='link-hover-text' style='display:inline-block; vertical-align:top; color:{color}; text-align:center;'>{node_path}</div>"
        item.setData(Qt.ItemDataRole.DisplayRole, f"<div class='link-container' style='white-space: nowrap;'>{display_text_2}</div>")
        item.setData(_EXTRA_DISPLAY_ROLE, f"<div class='link-container' style='white-space: nowrap;'>{hover_text_1}{display_text_2}</div>")
        text: str = repr(item.link.node) if self.editor._installation is None else self.editor._installation.string(item.link.node.text)  # noqa: SLF001
        item.setToolTip(f"{text}<br><br><i>Right click for more options</i>")

    def _swap_display_text(
        self,
        item: DLGListWidgetItem,
    ):
        """Helper to swap between hover and default display text."""
        hover_display: str = item.data(_EXTRA_DISPLAY_ROLE)
        default_display: str = item.data(Qt.ItemDataRole.DisplayRole)
        item.setData(Qt.ItemDataRole.DisplayRole, hover_display)
        item.setData(_EXTRA_DISPLAY_ROLE, default_display)
