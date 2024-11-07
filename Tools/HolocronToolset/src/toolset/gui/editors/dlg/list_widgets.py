from __future__ import annotations

import json
import weakref

from typing import TYPE_CHECKING, Any, ClassVar, Iterable, List, cast, overload

from PyQt6.QtWidgets import QWidget
from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy.QtCore import (
    QMimeData,
    QModelIndex,
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtWidgets import QListWidgetItem

from pykotor.resource.generics.dlg import DLGEntry, DLGLink
from toolset.gui.editors.dlg.constants import QT_STANDARD_ITEM_FORMAT, _DLG_MIME_DATA_ROLE, _EXTRA_DISPLAY_ROLE
from utility.ui_libraries.qt.widgets.itemviews.html_delegate import HTMLDelegate
from utility.ui_libraries.qt.widgets.itemviews.listwidget import RobustListWidget

if TYPE_CHECKING:
    import weakref

    from qtpy.QtCore import QModelIndex, QPersistentModelIndex, QPoint, QRect
    from qtpy.QtGui import QDropEvent, QFocusEvent, QMouseEvent
    from qtpy.QtWidgets import QAbstractItemDelegate, QAbstractItemView, QWidget
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
        self._data_cache: dict[int, Any] = {}
        self.is_orphaned = False

    def data(self, role: int = Qt.ItemDataRole.UserRole) -> Any:
        """Returns the data for the role. Uses cache if the item has been deleted."""
        if self.isDeleted():
            return self._data_cache.get(role)
        result = super().data(role)
        self._data_cache[role] = result  # Update cache
        return result

    def setData(self, role: int, value: Any,):
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


class DLGListWidget(RobustListWidget):
    itemDropped: ClassVar[Signal] = Signal(QMimeData, Qt.DropAction, name="itemDropped")  # pyright: ignore[reportPrivateImportUsage]

    def __init__(self, parent: DLGEditor):
        super().__init__(parent)
        self.editor: DLGEditor = parent
        self.dragged_item: DLGListWidgetItem | None = None
        self.currently_hovered_item: DLGListWidgetItem | None = None
        self.use_hover_text: bool = True

        self.itemPressed.connect(lambda: self.editor.jump_to_node(getattr(self.currentItem(), "link", None)))
        self.itemDoubleClicked.connect(lambda: self.editor.focus_on_node(getattr(self.currentItem(), "link", None)))
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(lambda pt: self.editor.on_list_context_menu(pt, self))
        self.setMouseTracking(True)

    def itemDelegate(self, index: QModelIndex | QPersistentModelIndex | None = None) -> HTMLDelegate | QAbstractItemDelegate:
        return super().itemDelegate()

    def mouseMoveEvent(self, event: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        super().mouseMoveEvent(event)
        if not self.use_hover_text:
            return
        item: DLGListWidgetItem | None = self.itemAt(event.pos())
        if item is None or item is self.currently_hovered_item:
            return
        # print(f"{self.__class__.__name__}.mouseMoveEvent: item hover change {self.currently_hovered_item} --> {item.__class__.__name__}")
        if self.currently_hovered_item is not None and not self.currently_hovered_item.isDeleted() and self.row(self.currently_hovered_item) != -1:
            # print("Reset old hover item")
            hover_display = self.currently_hovered_item.data(Qt.ItemDataRole.DisplayRole)
            default_display = self.currently_hovered_item.data(_EXTRA_DISPLAY_ROLE)
            # print("hover display:", hover_display, "default_display", default_display)
            self.currently_hovered_item.setData(Qt.ItemDataRole.DisplayRole, default_display)
            self.currently_hovered_item.setData(_EXTRA_DISPLAY_ROLE, hover_display)
        self.currently_hovered_item = item
        if self.currently_hovered_item is None:
            self.viewport().update()
            return
        # print("Set hover display text for newly hovered over item.")
        hover_display = self.currently_hovered_item.data(_EXTRA_DISPLAY_ROLE)
        default_display = self.currently_hovered_item.data(Qt.ItemDataRole.DisplayRole)
        # print("hover display:", hover_display, "default_display", default_display)
        self.currently_hovered_item.setData(Qt.ItemDataRole.DisplayRole, hover_display)
        self.currently_hovered_item.setData(_EXTRA_DISPLAY_ROLE, default_display)
        self.viewport().update()

    def isPersistentEditorOpen(self, item: DLGListWidgetItem) -> bool:  # type: ignore[override, misc]
        assert isinstance(item, DLGListWidgetItem)
        return super().isPersistentEditorOpen(item)

    def removeItemWidget(self, aItem: DLGListWidgetItem):  # type: ignore[override, misc]
        assert isinstance(aItem, DLGListWidgetItem)
        super().removeItemWidget(aItem)

    def itemFromIndex(self, index: QModelIndex) -> DLGListWidgetItem:
        item: QListWidgetItem | None = super().itemFromIndex(index)
        assert isinstance(item, DLGListWidgetItem)
        return item

    def indexFromItem(self, item: DLGListWidgetItem) -> QModelIndex:  # type: ignore[override, misc]
        assert isinstance(item, DLGListWidgetItem)
        return super().indexFromItem(item)

    def focusOutEvent(self, event: QFocusEvent):
        super().focusOutEvent(event)
        if self.currently_hovered_item is not None and not self.currently_hovered_item.isDeleted() and self.row(self.currently_hovered_item) != -1:
            # print("Reset old hover item")
            hover_display = self.currently_hovered_item.data(Qt.ItemDataRole.DisplayRole)
            default_display = self.currently_hovered_item.data(_EXTRA_DISPLAY_ROLE)
            # print("hover display:", hover_display, "default_display", default_display)
            self.currently_hovered_item.setData(Qt.ItemDataRole.DisplayRole, default_display)
            self.currently_hovered_item.setData(_EXTRA_DISPLAY_ROLE, hover_display)
        self.currently_hovered_item = None

    def update_item(self, item: DLGListWidgetItem, cached_paths: tuple[str, str, str] | None = None):
        """Refreshes the item text and formatting based on the node data."""
        assert self.editor is not None
        link_parent_path, link_partial_path, node_path = self.editor.get_item_dlg_paths(item) if cached_paths is None else cached_paths
        color: Literal["red", "blue"] = "red" if isinstance(item.link.node, DLGEntry) else "blue"
        if link_parent_path:
            link_parent_path += "\\"
        else:
            link_parent_path = ""
        hover_text_1: str = f"<span style='color:{color}; display:inline-block; vertical-align:top;'>{link_partial_path} --></span>"
        display_text_2 = f"<div class='link-hover-text' style='display:inline-block; vertical-align:top; color:{color}; text-align:center;'>{node_path}</div>"
        item.setData(Qt.ItemDataRole.DisplayRole, f"<div class='link-container' style='white-space: nowrap;'>{display_text_2}</div>")
        item.setData(_EXTRA_DISPLAY_ROLE, f"<div class='link-container' style='white-space: nowrap;'>{hover_text_1}{display_text_2}</div>")
        text = repr(item.link.node) if self.editor._installation is None else self.editor._installation.string(item.link.node.text)  # noqa: SLF001
        item.setToolTip(f"{text}<br><br><i>Right click for more options</i>")

    def dropEvent(self, event: QDropEvent):  # sourcery skip: extract-method
        print(f"DLGListWidget.dropEvent(event={event}(source={event.__class__.__name__} instance))")
        if event.mimeData().hasFormat(QT_STANDARD_ITEM_FORMAT):
            print("DLGListWidget.dropEvent: mime data has our format")
            assert self.editor is not None
            item_data: list[dict[Literal["row", "column", "roles"], Any]] = self.editor.ui.dialogTree.parse_mime_data(event.mimeData())
            link: DLGLink = DLGLink.from_dict(json.loads(item_data[0]["roles"][_DLG_MIME_DATA_ROLE]))
            new_item = DLGListWidgetItem(link=link)
            self.update_item(new_item)
            self.addItem(new_item)
            event.accept()
            self.itemDropped.emit(event.mimeData(), event.dropAction())
        else:
            print("DLGListWidget.dropEvent: invalid mime data")
            event.ignore()

    def mimeData(self, items: Iterable[DLGListWidgetItem]) -> QMimeData:  # type: ignore[override, misc]
        print(f"DLGListWidget.dropEvent: acquiring mime data for {len(list(items))} items")
        return super().mimeData(items)  # type: ignore[arg-type]

    def scrollToItem(self, item: DLGListWidgetItem, hint: QAbstractItemView.ScrollHint | None = None):  # type: ignore[override, misc]
        assert isinstance(item, DLGListWidgetItem)
        if hint is None:
            super().scrollToItem(item)
        else:
            super().scrollToItem(item, hint)

    def findItems(self, text: str, flags: Qt.MatchFlag) -> list[DLGListWidgetItem]:  # type: ignore[override, misc]
        return cast(List[DLGListWidgetItem], super().findItems(text, flags))

    def selectedItems(self) -> list[DLGListWidgetItem]:  # type: ignore[override, misc]
        return cast(List[DLGListWidgetItem], super().selectedItems())

    def closePersistentEditor(self, item: DLGListWidgetItem):  # type: ignore[override, misc]
        assert isinstance(item, DLGListWidgetItem)
        super().closePersistentEditor(item)

    def openPersistentEditor(self, item: DLGListWidgetItem | None = None):  # type: ignore[override, misc]
        assert isinstance(item, DLGListWidgetItem)
        super().openPersistentEditor(item)

    def editItem(self, item: DLGListWidgetItem | None = None):  # type: ignore[override, misc]
        assert isinstance(item, DLGListWidgetItem)
        super().editItem(item)

    def visualItemRect(self, item: DLGListWidgetItem) -> QRect:  # type: ignore[override, misc]
        assert isinstance(item, (DLGListWidgetItem, type(None)))
        return super().visualItemRect(item)

    def setItemWidget(self, item: DLGListWidgetItem, widget: QWidget):  # type: ignore[override, misc]
        assert isinstance(item, (DLGListWidgetItem))
        super().setItemWidget(item, widget)

    def itemWidget(self, item: DLGListWidgetItem) -> QWidget:  # type: ignore[override, misc]
        assert isinstance(item, (DLGListWidgetItem))
        item_widget: QWidget | None = super().itemWidget(item)
        assert item_widget is not None, "itemWidget returned None"
        return item_widget

    @overload
    def itemAt(self, p: QPoint) -> DLGListWidgetItem | None: ...
    @overload
    def itemAt(self, ax: int, ay: int) -> DLGListWidgetItem | None: ...
    def itemAt(self, *args) -> DLGListWidgetItem | None:  # type: ignore[override, misc]
        item: QListWidgetItem | None = super().itemAt(*args)
        assert isinstance(item, (DLGListWidgetItem, type(None)))
        return item

    def currentItem(self) -> DLGListWidgetItem:
        item: QListWidgetItem | None = super().currentItem()
        assert isinstance(item, DLGListWidgetItem)
        return item

    def takeItem(self, row: int) -> DLGListWidgetItem:
        item: QListWidgetItem | None = super().takeItem(row)
        assert isinstance(item, DLGListWidgetItem)
        return item

    def insertItem(
        self,
        row: int,
        item: DLGListWidgetItem | str,
    ):  # type: ignore[override, misc]
        if isinstance(item, DLGListWidgetItem):
            super().insertItem(row, item)
        elif isinstance(item, str):
            super().insertItem(row, item)
        else:
            raise TypeError("Incorrect args passed to insertItem")

    def row(
        self,
        item: DLGListWidgetItem,
    ) -> int:  # type: ignore[override, misc]
        assert isinstance(item, DLGListWidgetItem)
        return super().row(item)

    def item(self, row: int) -> DLGListWidgetItem:
        item: QListWidgetItem | None = super().item(row)
        assert isinstance(item, DLGListWidgetItem)
        return item
