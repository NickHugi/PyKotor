from __future__ import annotations

import json
import uuid
import weakref

from collections import deque
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Generator, Iterable, List, Literal, Mapping, Sequence, cast

from loggerplus import RobustLogger  # type: ignore[import-untyped]  # pyright: ignore[reportMissingModuleSource]
from qtpy.QtCore import (
    QByteArray,
    QDataStream,
    QIODevice,
    QItemSelectionModel,
    QMimeData,
    QModelIndex,
    QTimer,
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QBrush, QColor, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QApplication, QStyle

from pykotor.extract.installation import SearchLocation  # type: ignore[import-untyped]  # pyright: ignore[reportMissingModuleSource]
from pykotor.resource.generics.dlg import DLGEntry, DLGLink, DLGNode, DLGReply  # type: ignore[import-untyped]  # pyright: ignore[reportMissingModuleSource]
from toolset.gui.editors.dlg.constants import QT_STANDARD_ITEM_FORMAT, _COPY_ROLE, _DLG_MIME_DATA_ROLE, _DUMMY_ITEM, _LINK_PARENT_NODE_PATH_ROLE, _MODEL_INSTANCE_ID_ROLE  # type: ignore[import-untyped]  # pyright: ignore[reportMissingModuleSource]
from toolset.gui.editors.dlg.list_widget_base import DLGListWidgetItem  # type: ignore[import-untyped]  # pyright: ignore[reportMissingModuleSource]
from utility.ui_libraries.qt.widgets.itemviews.html_delegate import ICONS_DATA_ROLE  # type: ignore[import-untyped]  # pyright: ignore[reportMissingModuleSource]

if TYPE_CHECKING:
    from typing import Callable, Literal

    from qtpy.QtCore import QPersistentModelIndex
    from qtpy.QtGui import QClipboard
    from qtpy.QtWidgets import QWidget
    from typing_extensions import Self  # pyright: ignore[reportMissingModuleSource]

    from pykotor.resource.generics.dlg import DLGNode
    from toolset.gui.editors.dlg.editor import DLGEditor  # type: ignore[import-untyped]  # pyright: ignore[reportMissingModuleSource]
    from toolset.gui.editors.dlg.tree_view import DLGTreeView  # type: ignore[import-untyped]  # pyright: ignore[reportMissingModuleSource]


class DLGStandardItem(QStandardItem):
    def __init__(
        self,
        *args,
        link: DLGLink,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.ref_to_link: weakref.ref[DLGLink] = weakref.ref(link)  # Store a weak reference to the link
        self._data_cache: dict[int, Any] = {}

    @property
    def link(self) -> DLGLink | None:
        """Return the link, or None if the reference is no longer valid.

        Weak references are used throughout to ensure that orphaned nodes will be automatically detected and added to the orphaned_nodes_list listwidget.

        IMPORTANT: Do NOT save or store this result to e.g. a lambda, otherwise that lambda provides a strong reference and due to the nature of
        lambdas, becomes very difficult to track down. To be safe, it's just best to never save this to a local
        variable. Just test `item.link is not None` whenever you need the link and send `item.link` directly to wherever you need it.
        """
        return self.ref_to_link()

    @link.setter
    def link(
        self,
        new_link: DLGLink,
    ):
        raise NotImplementedError("DLGStandardItem's cannot store strong references to DLGLink objects.")

    def parent(self) -> DLGStandardItem | None:  # type: ignore[override, misc]
        return super().parent()  # type: ignore[return-value]

    def __eq__(self, other):
        return self is other

    def __hash__(self) -> int:
        return id(self)

    def index(self) -> QModelIndex:
        result: QModelIndex = super().index()
        if result.isValid():
            return result
        model: DLGStandardItemModel | None = self.model()
        if model is None:
            return QModelIndex()
        return model.indexFromItem(self)

    def isDeleted(self) -> bool:
        """Determines if this object has been deleted.

        Not sure what the proper method of doing so is, but this works fine.
        """
        try:
            if self.model() is None:
                return True
            self.index()
        except RuntimeError:
            return True
        else:
            return False

    def model(self) -> DLGStandardItemModel | None:  # type: ignore[override]
        model: QStandardItemModel | None = super().model()
        if model is None:
            return None
        assert isinstance(model, DLGStandardItemModel), f"model was {model} of type {type(model).__name__}"
        return model

    def is_copy(self) -> bool:
        result: Any = self.data(_COPY_ROLE)
        if result is None:
            return False
        return result

    def is_loaded(self) -> bool:
        if not self.is_copy():
            return True
        if not self.hasChildren():
            return True
        item: QStandardItem | None = self.child(0, 0)
        if isinstance(item, DLGStandardItem):
            return True
        if item is None:
            return False
        dummy = item.data(_DUMMY_ITEM)
        assert dummy is True
        return False

    def appendRow(  # type: ignore[override, misc]
        self,
        item: QStandardItem | DLGStandardItem,
    ):
        assert isinstance(item, DLGStandardItem) or cast(QStandardItem, item).data(_DUMMY_ITEM)
        super().appendRow(item)
        model: DLGStandardItemModel | None = self.model()
        if (
            model is not None  # noqa: PLR2004
            and not model.ignoring_updates
            and isinstance(item, DLGStandardItem)
        ):
            model._process_link(self, item)  # noqa: SLF001

    def appendRows(  # type: ignore[override]
        self,
        items: Iterable[DLGStandardItem],
    ):
        for item in items:
            self.appendRow(item)

    def insertRow(  # type: ignore[override, misc]
        self,
        row: int,
        item: DLGStandardItem,
    ):
        assert isinstance(item, DLGStandardItem) or cast(QStandardItem, item).data(_DUMMY_ITEM)
        super().insertRow(row, item)
        model: DLGStandardItemModel | None = self.model()
        if (
            model is not None  # noqa: PLR2004
            and isinstance(item, DLGStandardItem)
            and not model.ignoring_updates
        ):
            model._process_link(self, item, row)  # noqa: SLF001

    def insertRows(  # type: ignore[override]
        self,
        row: int,
        items: Iterable[Self],
    ):
        assert not isinstance(items, int), "Second arg cannot be a `count` in this implementation."
        for i, item in enumerate(items):
            self.insertRow(row + i, item)

    def removeRow(  # type: ignore[override]
        self,
        row: int,
    ) -> list[DLGStandardItem] | None:
        items: list[QStandardItem] = super().takeRow(row)
        model: DLGStandardItemModel | None = self.model()
        if (
            model is not None  # noqa: PLR2004
            and items
            and not model.ignoring_updates
        ):
            for item in items:
                if not isinstance(item, DLGStandardItem):
                    continue
                model._remove_link_from_parent(self, item.link)  # noqa: SLF001
        return cast(List[DLGStandardItem], items)

    def removeRows(
        self,
        row: int,
        count: int,
    ):
        for _ in range(count):
            self.removeRow(row)

    def setChild(  # type: ignore[override]
        self,
        row: int,
        *args,
    ):
        super().setChild(row, *args)
        item: QStandardItem | DLGStandardItem | None = args[1] if len(args) == 3 else args[0]  # noqa: PLR2004
        assert isinstance(item, DLGStandardItem) or cast(QStandardItem, item).data(_DUMMY_ITEM)
        model: DLGStandardItemModel | None = self.model()
        if (
            model is not None  # noqa: PLR2004
            and isinstance(item, DLGStandardItem)
            and not model.ignoring_updates
        ):
            model._process_link(self, item)  # noqa: SLF001

    def takeChild(  # type: ignore[override]
        self,
        row: int,
        column: int = 0,
    ) -> Self | None:
        item: QStandardItem | None = super().takeChild(row, column)
        if item is None:
            return None
        assert isinstance(item, DLGStandardItem) or item.data(_DUMMY_ITEM)
        model: DLGStandardItemModel | None = self.model()
        if (
            model is not None  # noqa: PLR2004
            and isinstance(item, DLGStandardItem)
            and not model.ignoring_updates
        ):
            model._remove_link_from_parent(self, item.link)  # noqa: SLF001
        return cast("Self | None", item)

    def takeRow(  # type: ignore[override]
        self,
        row: int,
    ) -> list[DLGStandardItem]:
        items: list[QStandardItem] = super().takeRow(row)
        model: DLGStandardItemModel | None = self.model()
        if (
            model is not None  # noqa: PLR2004
            and items
            and not model.ignoring_updates
        ):
            for item in items:
                if not isinstance(item, DLGStandardItem):
                    continue
                model._remove_link_from_parent(self, item.link)  # noqa: SLF001
        return cast(List[DLGStandardItem], items)

    def data(
        self,
        role: int = Qt.ItemDataRole.UserRole,
    ) -> Any:
        """Returns the data for the role. Uses cache if the item has been deleted."""
        if self.isDeleted():
            return self._data_cache.get(role)
        result: Any = super().data(role)
        self._data_cache[role] = result
        return result

    def setData(
        self,
        value: Any,
        role: int = Qt.ItemDataRole.UserRole,
    ):
        """Sets the data for the role and updates the cache."""
        self._data_cache[role] = value  # Update cache
        super().setData(value, role)


class DLGStandardItemModel(QStandardItemModel):
    # Custom for this model.
    sig_core_dlg_item_data_changed: ClassVar[Signal] = Signal(QStandardItem)  # pyright: ignore[reportMissingModuleSource]

    def __init__(
        self,
        parent: DLGTreeView,
    ):
        self.editor: DLGEditor | None = None
        self.tree_view: DLGTreeView = parent
        self.link_to_items: weakref.WeakKeyDictionary[DLGLink, list[DLGStandardItem]] = weakref.WeakKeyDictionary()
        self.node_to_items: weakref.WeakKeyDictionary[DLGNode, list[DLGStandardItem]] = weakref.WeakKeyDictionary()
        self.orig_to_orphan_copy: dict[weakref.ReferenceType[DLGLink], DLGLink]
        super().__init__(self.tree_view)
        self.modelReset.connect(self.on_model_reset)
        self.sig_core_dlg_item_data_changed.connect(self.on_dialog_item_data_changed)
        self.ignoring_updates: bool = False

    def __iter__(self) -> Generator[DLGStandardItem, Any, None]:
        stack: deque[DLGStandardItem | QStandardItem | None] = deque([self.item(row, column) for row in range(self.rowCount()) for column in range(self.columnCount())])
        while stack:
            item: DLGStandardItem | QStandardItem | None = stack.popleft()
            if item is None or item is None or not isinstance(item, DLGStandardItem):
                continue
            yield item
            stack.extend([item.child(row, column) for row in range(item.rowCount()) for column in range(item.columnCount())])

    # region Model Overrides
    def insertRows(
        self,
        row: int,
        count: int,
        parent: QModelIndex | None = None,
    ) -> bool:
        if parent is None:
            parent = QModelIndex()
        self.beginInsertRows(parent, row, row + count - 1)
        result: bool = super().insertRows(row, count, parent)
        self.endInsertRows()
        return result

    def removeRows(
        self,
        row: int,
        count: int,
        parent: QModelIndex | None = None,
    ) -> bool:
        if row < 0 or count < 1:
            # Check for negative or invalid row index and count
            return False
        parent_item: DLGStandardItem | DLGStandardItemModel | None = (self.itemFromIndex(parent) or self) if parent is not None and parent.isValid() else None
        if parent_item is None:
            return False
        rows_available: int = parent_item.rowCount()
        if row + count > rows_available:
            return False

        item_selection: QItemSelectionModel | None = self.tree_view.selectionModel()
        assert item_selection is not None
        item_selection.clear()
        if parent is not None:
            links: list[DLGLink | None] = [item.link for item in (self.itemFromIndex(self.index(r, 0, parent)) for r in range(row, row + count)) if item is not None]
        else:
            links = [
                item.link  # pyright: ignore[reportAttributeAccessIssue]
                for item in (self.item(r, 0) for r in range(row, row + count))
                if isinstance(item, DLGStandardItem)
            ]
        self.beginRemoveRows(
            QModelIndex() if parent is None else parent,
            row,
            row + count - 1,
        )
        result: bool = super().removeRows(row, count, parent)  # type: ignore[arg-type]
        sel_model: QItemSelectionModel | None = self.tree_view.selectionModel()
        assert sel_model is not None
        sel_model.clear()
        self.endRemoveRows()
        if self.ignoring_updates:
            return result
        parent_item = None if parent is None else self.itemFromIndex(parent)
        for link in links:
            if link is None or parent_item is not None and not isinstance(parent_item, DLGStandardItem):
                continue
            self._remove_link_from_parent(parent_item, link)
        return result

    def appendRows(
        self,
        items: Iterable[DLGStandardItem],
        parent_index: QModelIndex | None = None,
    ):
        for item in items:
            self.appendRow(item, parent_index)  # type: ignore[call-overload]

    def removeRow(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        row: int,
        parent_index: QModelIndex | None = None,
    ) -> bool:
        if parent_index is not None and parent_index.isValid():
            return super().removeRow(row, parent_index)
        return super().removeRow(row)

    def item(  # type: ignore[override]  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        row: int,
        column: int,
    ) -> DLGStandardItem | QStandardItem:
        ret: QStandardItem | None = super().item(row, column)
        assert ret is not None
        return ret

    def insertRow(  # type: ignore[override, misc]
        self,
        row: int,
        to_insert: Iterable[QStandardItem] | QStandardItem | QModelIndex,
    ) -> bool | None:
        result: None | bool = super().insertRow(row, to_insert)
        if self.ignoring_updates:
            return result
        item_to_insert: QStandardItem | DLGStandardItem | None = None
        if isinstance(to_insert, Iterable):
            for item_to_insert in to_insert:
                if not isinstance(item_to_insert, DLGStandardItem):
                    continue
                if item_to_insert.link is None:
                    continue
                parent_item: DLGStandardItem | None = item_to_insert.parent()
                self._insert_link_to_parent(parent_item, item_to_insert, row)
        elif isinstance(to_insert, (QModelIndex, QStandardItem)):
            item_to_insert = to_insert if isinstance(to_insert, QStandardItem) else self.itemFromIndex(to_insert)
            if not isinstance(item_to_insert, DLGStandardItem):
                return result
            if item_to_insert.link is None:
                return result
            parent_item = item_to_insert.parent()
            self._insert_link_to_parent(parent_item, item_to_insert, row)
        else:
            raise TypeError("Incorrect args passed to insertRow")
        return result

    def takeItem(  # type: ignore[override]
        self,
        row: int,
        column: int = 0,
    ) -> DLGStandardItem:
        item: DLGStandardItem = cast(DLGStandardItem, super().takeItem(row, column))
        if not self.ignoring_updates:
            self._remove_link_from_parent(None, item.link)
        return item

    def takeRow(  # type: ignore[override]
        self,
        row: int,
    ) -> list[DLGStandardItem]:
        items: list[DLGStandardItem] = cast(List[DLGStandardItem], super().takeRow(row))
        if not items:
            return items
        if self.ignoring_updates:
            return items
        for item in items:
            if not isinstance(item, DLGStandardItem):
                continue
            self._remove_link_from_parent(
                None,
                item.link,
            )
        return items

    def appendRow(  # type: ignore[override, misc]
        self,
        *args,
    ):
        item_to_append: DLGStandardItem = args[0]
        super().appendRow(item_to_append)
        if not self.ignoring_updates:
            self._insert_link_to_parent(None, item_to_append, self.rowCount())

    # endregion

    # region drag&drop
    def supportedDropActions(self):  # type: ignore[override]
        return Qt.DropAction.CopyAction | Qt.DropAction.MoveAction

    def supportedDragActions(self):  # type: ignore[override]
        return Qt.DropAction.CopyAction | Qt.DropAction.MoveAction

    def flags(  # type: ignore[override]
        self,
        index: QModelIndex,
    ) -> Qt.ItemFlag:
        default_flags: Qt.ItemFlag = super().flags(index)  # type: ignore[assignment]
        if index.isValid():
            return Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsDropEnabled | default_flags  # type: ignore[return-value]
        return Qt.ItemFlag.ItemIsDropEnabled | default_flags  # type: ignore[return-value]

    def mimeTypes(self) -> list[str]:
        return [QT_STANDARD_ITEM_FORMAT]

    def mimeData(
        self,
        indexes: Iterable[QModelIndex],
    ) -> QMimeData:
        mime_data = QMimeData()
        data = QByteArray()
        stream = QDataStream(data, QIODevice.OpenModeFlag.WriteOnly)
        for index in indexes:
            assert index.isValid(), f"index is invalid: {index} ({index.row()}, {index.column()})"
            item: QStandardItem | None = self.itemFromIndex(index)  # pyright: ignore[reportArgumentType]
            assert item is not None, f"item is None for index {index} ({index.row()}, {index.column()})"
            assert isinstance(item, DLGStandardItem), f"item is {item.__class__.__name__}, {item} for index {index} ({index.row()}, {index.column()}) expected DLGStandardItem"
            assert item.link is not None, f"item.link is None for index {index} ({index.row()}, {index.column()})"
            stream.writeInt32(index.row())
            stream.writeInt32(index.column())
            stream.writeInt32(3)
            stream.writeInt32(int(Qt.ItemDataRole.DisplayRole))
            stream.writeQString(item.data(Qt.ItemDataRole.DisplayRole))
            stream.writeInt32(_DLG_MIME_DATA_ROLE)
            stream.writeQString(json.dumps(item.link.to_dict()))
            stream.writeInt32(_MODEL_INSTANCE_ID_ROLE)
            stream.writeInt64(id(self))
            # stream_listwidget.writeInt32(int(_LINK_PARENT_NODE_PATH_ROLE))
            # stream_listwidget.writeQString(item.data(_LINK_PARENT_NODE_PATH_ROLE))

        mime_data.setData(QT_STANDARD_ITEM_FORMAT, data)
        return mime_data

    def dropMimeData(  # type: ignore[override]
        self,
        data: QMimeData,
        action: Qt.DropAction,
        row: int,
        column: int,
        parent: QModelIndex | QPersistentModelIndex,
    ) -> bool:
        if not data.hasFormat(QT_STANDARD_ITEM_FORMAT):
            return False
        if action == Qt.DropAction.IgnoreAction:
            return True

        parent_item: DLGStandardItem | None = self.itemFromIndex(parent) if parent.isValid() else None
        try:
            parsed_mime_data: dict[Literal["row", "column", "roles"], Any] = self.tree_view.parse_mime_data(data)[0]
            dlg_nodes_json: str = parsed_mime_data["roles"][_DLG_MIME_DATA_ROLE]
            dlg_nodes_dict: dict[str | int, Any] = json.loads(dlg_nodes_json)
            deserialized_dlg_link: DLGLink = DLGLink.from_dict(dlg_nodes_dict)
        except Exception:  # noqa: BLE001
            return True
        else:
            self.paste_item(
                parent_item,
                deserialized_dlg_link,
                as_new_branches=parsed_mime_data["roles"][_MODEL_INSTANCE_ID_ROLE] == id(self),
            )

        return True

    # endregion

    # region Model Signals
    def on_model_reset(self):
        self.link_to_items.clear()
        self.node_to_items.clear()

    def reset_model(self):
        self.beginResetModel()
        self.clear()
        self.on_model_reset()
        self.endResetModel()

    def on_dialog_item_data_changed(
        self,
        item: DLGStandardItem,
    ):
        if item.link is None:
            # del self.orig_to_orphan_copy[item._link_ref]
            self.removeRow(item.row())
        else:
            # First take out and store the links/node
            # So we can update our instance objects, without breaking the whole DAG.
            internal_link: DLGLink = self.orig_to_orphan_copy[item.ref_to_link]
            internal_linked_node: DLGNode = internal_link.node
            assert internal_linked_node is not None
            del internal_link.__dict__["node"]
            temp_links: list[DLGLink] = internal_linked_node.links
            del internal_linked_node.__dict__["links"]
            # Call update, probably faster than assigning attrs manually.
            internal_link.__dict__.update(item.link.__dict__)
            internal_linked_node.__dict__.update(item.link.node.__dict__)
            internal_link.node = internal_linked_node
            internal_linked_node.links = temp_links
            self.update_item_display_text(item)

    def on_orphaned_node(
        self,
        shallow_link_copy: DLGLink,
        link_parent_path: str,
        *,
        immediate_check: bool = False,
    ):
        """Add a deleted node to the QListWidget in the left_dock_widget, if the passed link is the only reference."""
        if not shallow_link_copy.node or shallow_link_copy.list_index == -1 and shallow_link_copy.node.list_index == -1:
            return
        if not immediate_check:

            def on_orphan(*args):
                self.on_orphaned_node(shallow_link_copy, link_parent_path, immediate_check=True)

            QTimer.singleShot(0, on_orphan)
            return
        assert self.editor is not None
        item = DLGListWidgetItem(link=shallow_link_copy)
        item.is_orphaned = True
        self.editor.orphaned_nodes_list.update_item(item)
        self.editor.orphaned_nodes_list.addItem(item)

    # endregion

    def insert_link_to_parent_as_item(
        self,
        parent: DLGStandardItem | None,
        link: DLGLink,
        row: int | None = -1,
    ) -> DLGStandardItem:
        item = DLGStandardItem(link=link)
        item.setData(False, _COPY_ROLE)
        if parent is None:
            row = self.rowCount() if row in (-1, None) else row
            assert row is not None, "row cannot be None in insert_link_to_parent_as_item"
            self.insertRow(row, item)
        else:
            row = self.rowCount() if row in (-1, None) else row
            assert row is not None, "row cannot be None in insert_link_to_parent_as_item"
            parent.insertRow(row, item)
        return item

    def remove_link(
        self,
        item: DLGStandardItem,
    ):
        """Removes the link from the parent node."""
        parent: DLGStandardItem | None = item.parent()
        item_row: int = item.row()

        if parent is None:
            self.removeRow(item_row)
        else:
            assert isinstance(parent, DLGStandardItem)
            assert parent.link is not None
            parent.removeRow(item_row)
        self.layoutChanged.emit()

    def _insert_link_to_parent(
        self,
        parent: DLGStandardItem | None,
        items: Iterable[DLGStandardItem] | DLGStandardItem,
        row: int | None = -1,
    ):
        if row is None:
            row = -1
        if isinstance(items, Iterable):
            for i, item in enumerate(items):
                self._process_link(parent, item, row + i)
        else:
            self._process_link(parent, items, row)

    def _process_link(
        self,
        parent_item: DLGStandardItem | None,
        item: DLGStandardItem,
        row: int | None = -1,
    ):
        assert item.link is not None, "item.link cannot be None in _process_link"
        assert self.editor is not None, "self.editor cannot be None in _process_link"
        item_row: int | None = (parent_item or self).rowCount() if row in (-1, None) else row
        assert item_row is not None, "item_row cannot be None in _process_link"
        links_list: list[DLGLink] = self.editor.core_dlg.starters if parent_item is None else parent_item.link.node.links  # pyright: ignore[reportOptionalMemberAccess]  # type: ignore[union-attr]
        node_to_items: list[DLGStandardItem] = self.node_to_items.setdefault(item.link.node, [])
        if item not in node_to_items:
            node_to_items.append(item)
        link_to_items: list[DLGStandardItem] = self.link_to_items.setdefault(item.link, [])
        if item not in link_to_items:
            link_to_items.append(item)
        item_cur_row: int | None = {link: idx for idx, link in enumerate(links_list)}.get(item.link)
        if item_cur_row is not None:
            # Link already exists in the list, move it if needed
            if item_cur_row != item_row:
                links_list.pop(item_cur_row)
                if item_cur_row < item_row:
                    item_row -= 1
                links_list.insert(item_row, item.link)
        else:
            # Link is new, insert it at the specified position
            links_list.insert(item_row, item.link)
        for i, link in enumerate(links_list):
            link.list_index = i
        if isinstance(parent_item, DLGStandardItem):
            assert parent_item.link is not None, f"parent_item.link cannot be None. {parent_item.__class__.__name__}: {parent_item}"
            self.update_item_display_text(parent_item)
            self.sync_item_copies(parent_item.link, parent_item)
        if item.ref_to_link in self.orig_to_orphan_copy:
            return
        copied_link: DLGLink = DLGLink.from_dict(item.link.to_dict())
        self.orig_to_orphan_copy[item.ref_to_link] = copied_link  # noqa: SLF001
        self.register_deepcopies(item.link, copied_link)

    def _remove_link_from_parent(
        self,
        parent_item: DLGStandardItem | None,
        link: DLGLink | None,
    ):
        assert self.editor is not None
        if link is None:
            return
        links_list: list[DLGLink[DLGEntry]] = (
            self.editor.core_dlg.starters  # The items could be deleted by qt at this point, so we only use the python object.
            if parent_item is None
            else parent_item.link.node.links  # pyright: ignore[reportAssignmentType, reportOptionalMemberAccess]  # type: ignore[attr-defined, union-attr]
        )
        index: int = links_list.index(link)
        links_list.remove(link)
        for i in range(index, len(links_list)):
            links_list[i].list_index = i
        if isinstance(parent_item, DLGStandardItem):
            assert parent_item is not None
            assert parent_item.link is not None
            self.update_item_display_text(parent_item)
            self.sync_item_copies(parent_item.link, parent_item)

    def get_copy(
        self,
        original: DLGLink,
    ) -> DLGLink | None:
        """Retrieve the copy of the original object using the weak reference."""
        assert self.editor is not None
        return next(
            (copied_link for orig_ref, copied_link in self.orig_to_orphan_copy.items() if orig_ref() is original),
            None,
        )

    def register_deepcopies(
        self,
        orig_link: DLGLink,
        copy_link: DLGLink,
        seen_links: set[DLGLink] | None = None,
    ):
        """Recursively register deepcopies of nested links to avoid redundant deepcopies."""
        if seen_links is None:
            seen_links = set()
        if copy_link in seen_links:
            return
        seen_links.add(copy_link)
        assert orig_link is not copy_link
        self.orig_to_orphan_copy[weakref.ref(orig_link)] = copy_link
        for child_orig_link, child_copy_link in zip(
            orig_link.node.links,
            copy_link.node.links,
        ):
            self.register_deepcopies(
                child_orig_link,
                child_copy_link,
                seen_links,
            )

    def load_dlg_item_rec(
        self,
        item_to_load: DLGStandardItem,
        copied_link: DLGLink | None = None,
    ):
        assert item_to_load.link is not None
        assert self.editor is not None

        child_links_copy: Sequence[DLGLink | None] = [None]
        if copied_link is not None and item_to_load.ref_to_link not in self.orig_to_orphan_copy:
            self.orig_to_orphan_copy[item_to_load.ref_to_link] = copied_link
        elif copied_link is None:
            copied_link = self.orig_to_orphan_copy.get(item_to_load.ref_to_link)
        if copied_link is None:
            copied_link = DLGLink.from_dict(item_to_load.link.to_dict())
            self.register_deepcopies(item_to_load.link, copied_link)
        child_links_copy = copied_link.node.links

        assert item_to_load.link is not copied_link  # new copies should be made before load_dlg_item_rec to reduce complexity.
        parent_path: str = item_to_load.data(_LINK_PARENT_NODE_PATH_ROLE)
        if all(info.weakref() is not item_to_load.link.node for info in weakref.finalize._registry.values()):  # type: ignore[attr-defined]  # noqa: SLF001
            weakref.finalize(item_to_load.link.node, self.on_orphaned_node, copied_link, parent_path)

        already_listed: bool = item_to_load.link in self.link_to_items
        self.link_to_items.setdefault(item_to_load.link, []).append(item_to_load)
        self.node_to_items.setdefault(item_to_load.link.node, []).append(item_to_load)
        if not already_listed:
            parent_item: DLGStandardItem | None = item_to_load.parent()
            if parent_item is not None and parent_item.data(_COPY_ROLE):
                RobustLogger().error(
                    "Buggy code detected in the model: parent_item is a copy but item_to_load hasn't been seen.\n"
                    f"Parent item data: {parent_item.data(_COPY_ROLE)!r}\n"
                    f"Parent item link: {parent_item.link!r}\n"
                    f"Item to load link: {item_to_load.link!r}\n"
                    f"Already listed items for this link: {self.link_to_items.get(item_to_load.link, [])!r}"
                )
                raise AssertionError("Buggy code detected - see error log for details")
            item_to_load.setData(False, _COPY_ROLE)
            for child_link, child_link_copy in zip(item_to_load.link.node.links, child_links_copy):
                child_item = DLGStandardItem(link=child_link)
                child_item.setData(False, _COPY_ROLE)
                child_item.setData(item_to_load.link.node.path(), _LINK_PARENT_NODE_PATH_ROLE)
                item_to_load.appendRow(child_item)
                self.load_dlg_item_rec(child_item, child_link_copy)
        elif item_to_load.link.node.links:
            self.set_item_future_expand(item_to_load)
        else:
            orig_item: DLGStandardItem | None = next(
                (item for item in self.link_to_items[item_to_load.link] if not item.isDeleted() and item.data(_COPY_ROLE) is False),
                None,
            )
            item_to_load.setData(
                orig_item is item_to_load or orig_item is None,
                _COPY_ROLE,
            )
        self.update_item_display_text(item_to_load)

    def manage_links_list(
        self,
        node: DLGNode,
        link: DLGLink,
        *,
        add: bool = True,
    ):
        """Manage DLGLink.node.links and DLGLink.list_index."""
        if add:
            node.links.append(link)
            link.list_index = len(node.links) - 1

        elif link in node.links:
            link_list_index: int = node.links.index(link)  # Find the index of the link to be removed
            node.links.remove(link)
            # Update list_index for remaining links
            for i, child_link in enumerate(
                node.links[link_list_index:],
                start=link_list_index,
            ):
                child_link.list_index = i

    def set_item_future_expand(
        self,
        item: DLGStandardItem,
    ):
        """Creates a dummy item, with specific information that tells onItemExpanded how to expand when the user attempts to do so.

        This prevents infinite recursion while still giving the impression that multiple copies are in fact the same.
        """
        dummy_child: QStandardItem = QStandardItem("Click this text to load.")
        dummy_child.setData(True, _DUMMY_ITEM)
        item.appendRow(dummy_child)
        item.setData(True, _COPY_ROLE)
        index: QModelIndex = item.index()
        self.tree_view.collapse(index)

    def add_root_node(self):
        """Adds a root node to the dialog graph."""
        assert self.editor is not None
        new_node = DLGEntry()
        new_node.plot_index = -1
        new_link: DLGLink = DLGLink(new_node)
        new_link.node.list_index = self._get_new_node_list_index(new_link.node)
        new_item = DLGStandardItem(link=new_link)
        new_item.setData(False, _COPY_ROLE)
        self.appendRow(new_item)
        self.update_item_display_text(new_item)

    def add_child_to_item(
        self,
        parent_item: DLGStandardItem,
        link: DLGLink | None = None,
    ) -> DLGStandardItem:
        """Helper method to update the UI with the new link."""
        assert parent_item.link is not None
        if link is None:
            new_node: DLGReply | DLGEntry = DLGEntry() if isinstance(parent_item.link.node, DLGReply) else DLGReply()
            new_node.plot_index = -1
            new_node.list_index = self._get_new_node_list_index(new_node)
            link = DLGLink(new_node)
        new_item = DLGStandardItem(link=link)
        new_item.setData(False, _COPY_ROLE)
        parent_item.appendRow(new_item)
        self.update_item_display_text(new_item)
        self.update_item_display_text(parent_item)
        self.sync_item_copies(parent_item.link, parent_item)
        self.tree_view.expand(parent_item.index())
        return new_item

    def _link_core_nodes(
        self,
        target: DLGNode,
        source: DLGNode,
    ) -> DLGLink:
        """Helper method to add a source node to a target node."""
        new_link: DLGLink = DLGLink(source)
        new_link.list_index = len(target.links)
        target.links.append(new_link)
        return new_link

    def copy_link_and_node(
        self,
        link: DLGLink | None,
    ):
        if link is None:
            return
        q_app_clipboard: QClipboard | None = QApplication.clipboard()
        assert q_app_clipboard is not None
        q_app_clipboard.setText(json.dumps(link.to_dict()))

    def paste_item(
        self,
        parent_item: DLGStandardItem | Self | None,
        pasted_link: DLGLink | None = None,
        *,
        row: int | None = None,
        as_new_branches: bool = True,
    ):
        """Paste a node from the clipboard to the parent node."""
        assert self.editor is not None
        pasted_link = self.editor._copy if pasted_link is None else pasted_link  # noqa: SLF001
        assert pasted_link is not None

        # If this link was copied from this DLG, regardless of if its a deep copy or not, it must be pasted as a unique link.
        # Since the nested structure already has this exact instance, even after a deserialization, we do not
        # need to iterate here, since it'll always be the same object in the nested objects.
        # We just need to change `is_child` and the hash to represent a new link.
        pasted_link._hash_cache = hash(uuid.uuid4().hex)  # noqa: SLF001
        assert pasted_link not in self.link_to_items
        pasted_link.is_child = not isinstance(parent_item, DLGStandardItem)

        all_entries: set[int] = {entry.list_index for entry in self.editor.core_dlg.all_entries()}
        all_replies: set[int] = {reply.list_index for reply in self.editor.core_dlg.all_replies()}
        if as_new_branches:
            new_index: int = self._get_new_node_list_index(
                pasted_link.node,
                all_entries,
                all_replies,
            )
            pasted_link.node.list_index = new_index

        queue: deque[DLGNode] = deque([pasted_link.node])
        visited: set[DLGNode] = set()
        while queue:
            cur_node: DLGNode = queue.popleft()
            if cur_node in visited:
                continue
            visited.add(cur_node)
            if as_new_branches or cur_node not in self.node_to_items:
                new_index = self._get_new_node_list_index(cur_node, all_entries, all_replies)
                cur_node.list_index = new_index
            if as_new_branches:
                new_node_hash: int = hash(uuid.uuid4().hex)  # noqa: SLF001
                cur_node._hash_cache = new_node_hash  # noqa: SLF001

            queue.extend(link.node for link in cur_node.links)

        if parent_item is None:
            parent_item = self
        new_item = DLGStandardItem(link=pasted_link)
        new_item.setData(False, _COPY_ROLE)
        if row not in (-1, None, parent_item.rowCount()):
            parent_item.insertRow(row, new_item)  # type: ignore[arg-type]
        else:
            parent_item.appendRow(new_item)
        self.ignoring_updates = True
        self.load_dlg_item_rec(new_item)
        self.ignoring_updates = False
        if isinstance(parent_item, DLGStandardItem):
            assert parent_item.link is not None
            self.update_item_display_text(parent_item)
            self.sync_item_copies(parent_item.link, parent_item)

        def expand_item(new_item: DLGStandardItem):
            self.tree_view.expand(new_item.index())

        QTimer.singleShot(0, expand_item)
        self.layoutChanged.emit()
        viewport: QWidget | None = self.tree_view.viewport()
        assert viewport is not None
        viewport.update()
        self.tree_view.update()

    def _get_new_node_list_index(
        self,
        node: DLGNode,
        entry_indices: set[int] | None = None,
        reply_indices: set[int] | None = None,
    ) -> int:
        """Generate a new unique list index for the node."""
        assert self.editor is not None
        if isinstance(node, DLGEntry):
            indices: set[int] = {entry.list_index for entry in self.editor.core_dlg.all_entries()} if entry_indices is None else entry_indices
        elif isinstance(node, DLGReply):
            indices = {reply.list_index for reply in self.editor.core_dlg.all_replies()} if reply_indices is None else reply_indices
        else:
            raise TypeError(f"{node.__class__.__name__}: {node!r}")
        new_index: int = max(indices, default=-1) + 1

        while new_index in indices:
            new_index += 1
        indices.add(new_index)
        return new_index

    def itemFromIndex(  # type: ignore[override]
        self,
        index: QModelIndex | QPersistentModelIndex,
    ) -> DLGStandardItem | None:
        item: QStandardItem | None = super().itemFromIndex(index)  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]
        if item is None:
            return None
        if not isinstance(item, DLGStandardItem):
            # fix any future expands.
            parent_item: QStandardItem | None = item.parent()
            assert parent_item is not None
            parent_index: QModelIndex = parent_item.index()
            assert parent_index.isValid()
            self.tree_view.collapse(parent_index)
            self.tree_view.expand(parent_index)
        item = super().itemFromIndex(index)  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]
        assert isinstance(item, DLGStandardItem), f"item is {item.__class__.__name__}, {item} for index {index} ({index.row()}, {index.column()}) expected DLGStandardItem"
        return item

    def delete_node_everywhere(
        self,
        node: DLGNode,
    ):
        """Removes all occurrences of a node and all links to it from the model and self.editor.core_dlg."""
        assert self.editor is not None
        self.layoutAboutToBeChanged.emit()

        def remove_links_recursive(
            node_to_remove: DLGNode,
            parent_item: DLGStandardItem | DLGStandardItemModel,
        ):
            assert self.editor is not None
            for i in reversed(range(parent_item.rowCount())):
                child_item: QStandardItem | None = parent_item.child(i, 0) if isinstance(parent_item, DLGStandardItem) else parent_item.item(i, 0)
                if child_item is None:
                    continue
                if not isinstance(child_item, DLGStandardItem):
                    continue
                if child_item.link is None:
                    continue
                if child_item.data(_DUMMY_ITEM):
                    continue
                if child_item.isDeleted():
                    continue
                if child_item.link.node == node_to_remove:
                    remove_links_recursive(child_item.link.node, child_item)  # type: ignore[]
                    parent_item.removeRow(i)
                else:
                    remove_links_recursive(node_to_remove, child_item)

        remove_links_recursive(node, self)
        self.layoutChanged.emit()

    def delete_node(
        self,
        item: DLGStandardItem,
    ):
        """Deletes a node from the DLG and ui tree model."""
        parent_item: DLGStandardItem | None = item.parent()
        if parent_item is None:
            self.removeRow(item.row())
        else:
            parent_item.removeRow(item.row())
            assert parent_item.link is not None
            self.update_item_display_text(parent_item)
            self.sync_item_copies(parent_item.link, parent_item)

    def count_item_refs(
        self,
        link: DLGLink,
    ) -> int:
        """Counts the number of references to a node in the ui tree model."""
        return len(self.node_to_items[link.node])

    def update_item_display_text(  # noqa: C901, PLR0912, PLR0915
        self,
        item: DLGStandardItem,
        *,
        update_copies: bool = True,
    ):
        """Refreshes the item text and formatting based on the node data."""
        assert item.link is not None
        assert self.editor is not None
        color: QColor = QColor("#646464")
        prefix: Literal["E", "R", "N"] = "N"
        extra_node_info: str = ""
        if isinstance(item.link.node, DLGEntry):
            color = QColor("#FF0000") if not item.is_copy() else QColor("#D25A5A")
            prefix = "E"
        elif isinstance(item.link.node, DLGReply):
            color = QColor("#0000FF") if not item.is_copy() else QColor("#5A5AD2")
            prefix = "R"
            extra_node_info = " This means the player will not see this reply as a choice, and will (continue) to next entry."

        text: str = (
            str(item.link.node.text)
            if self.editor._installation is None  # noqa: SLF001
            else self.editor._installation.string(item.link.node.text, "")  # noqa: SLF001
        )
        if not item.link.node.links:
            end_dialog_color: str = QColor("#FF7F50").name()
            display_text: str = f"{text} <span style='color:{end_dialog_color};'><b>[End Dialog]</b></span>"
        elif not text and not text.strip():
            if item.link.node.text.stringref == -1:
                display_text = "(continue)"
                tooltip_text: str = (
                    f"<i>No text set.{extra_node_info}<br><br>"
                    "Change this behavior by:<br>"
                    "- <i>Right-click and select '<b>Edit Text</b>'</i><br>"
                    "- <i>Double-click to edit text</i>"
                )
            else:
                display_text = f"(invalid strref: {item.link.node.text.stringref})"
                tooltip_text = (
                    f"StrRef {item.link.node.text.stringref} not found in TLK.<br><br>"
                    "Fix this issue by:<br>"
                    "- <i>Right-click and select '<b>Edit Text</b>'</i><br>"
                    "- <i>Double-click to edit text</i>"
                )
            item.setToolTip(tooltip_text)
        else:
            display_text = text
        list_prefix: str = f"<b>{prefix}{item.link.node.list_index}:</b> "
        item.setData(
            f'<span style="color:{color.name()}; font-size:{self.tree_view.get_text_size()}pt;">{list_prefix}{display_text}</span>',
            Qt.ItemDataRole.DisplayRole,
        )

        has_conditional: bool = bool(item.link.active1 or item.link.active2)
        has_script: bool = bool(item.link.node.script1 or item.link.node.script2)
        has_animation: bool = item.link.node.camera_anim not in (-1, None) or bool(item.link.node.animations)
        has_sound: bool = bool(item.link.node.sound and item.link.node.sound_exists)
        has_voice: bool = bool(item.link.node.vo_resref)
        is_plot_or_quest_related: bool = bool(item.link.node.plot_index != -1 or item.link.node.quest_entry or item.link.node.quest)

        icons: list[tuple[QStyle.StandardPixmap | str, Callable | None, str]] = []
        if has_conditional:
            icons.append((QStyle.StandardPixmap.SP_FileIcon, None, f"Conditional: <code>{has_conditional}</code>"))
        if has_script:
            script_icon_path: str = f":/images/icons/k{int(self.editor._installation.tsl) + 1}/script.png"  # noqa: SLF001
            icons.append((script_icon_path, None, f"Script: {has_script}"))
        if has_animation:
            anim_icon_path: str = f":/images/icons/k{int(self.editor._installation.tsl) + 1}/walkmesh.png"  # noqa: SLF001
            icons.append((anim_icon_path, None, "Item has animation data"))
        if is_plot_or_quest_related:
            journal_icon_path: str = f":/images/icons/k{int(self.editor._installation.tsl) + 1}/journal.png"  # noqa: SLF001
            icons.append((journal_icon_path, None, "Item has plot/quest data"))
        if has_sound:
            sound_icon_path = ":/images/common/sound-icon.png"
            icons.append(
                (
                    sound_icon_path,
                    lambda: self.editor is not None
                    and item.link is not None
                    and self.editor.play_sound(str(item.link.node.sound), [SearchLocation.SOUND, SearchLocation.VOICE]),
                    "Item has Sound (click to play)",
                )
            )
        if has_voice:
            voice_icon_path = ":/images/common/voice-icon.png"
            icons.append(
                (
                    voice_icon_path,
                    lambda: self.editor is not None
                    and item.link is not None
                    and self.editor.play_sound(str(item.link.node.vo_resref), [SearchLocation.SOUND, SearchLocation.VOICE]),
                    "Item has VO (click to play)",
                )
            )

        def get_text_callable(*args) -> str:
            return str(self.count_item_refs(item.link) if item.link else 0)

        def get_tooltip_callable(*args) -> str:
            return f"{self.count_item_refs(item.link) if item.link else 0} references to this item"

        def get_action_callable(*args):
            if self.editor is None:
                return
            weakref_links: list[weakref.ref[DLGLink]] = [
                this_item.ref_to_link
                for link in self.link_to_items
                for this_item in self.link_to_items[link]
                if (this_item.link is not None and item.link in this_item.link.node.links)
            ]
            self.editor.show_reference_dialog(
                weakref_links,
                item.data(Qt.ItemDataRole.DisplayRole),
            )  # pyright: ignore[reportOptionalMemberAccess]

        icon_data: dict[str, Any] = {
            "icons": icons,
            "size": self.tree_view.get_text_size,
            "spacing": 5,
            "rows": len(icons),
            "columns": 1,
            "bottom_badge": {
                "text_callable": get_text_callable,
                "size_callable": self.tree_view.get_text_size,
                "tooltip_callable": get_tooltip_callable,
                "action": get_action_callable,
            },
        }
        item.setData(
            icon_data,
            ICONS_DATA_ROLE,
        )
        item.setForeground(QBrush(color))
        if not update_copies:
            return
        items: list[DLGStandardItem] = self.node_to_items[item.link.node]
        for copied_item in items:
            if copied_item is item or not isinstance(copied_item, DLGStandardItem):
                continue
            self.update_item_display_text(copied_item, update_copies=False)

    def is_copy(
        self,
        item: DLGStandardItem,
    ) -> bool:
        result = item.data(_COPY_ROLE)
        assert result is not None
        return result

    def is_loaded(
        self,
        item: DLGStandardItem,
    ) -> bool:
        if not item.is_copy():
            return True
        if not item.hasChildren():
            return True
        child: QStandardItem | None = item.child(0, 0)
        if child is None:
            return False
        if isinstance(child, DLGStandardItem):
            return True
        dummy: bool = child.data(_DUMMY_ITEM)
        assert dummy is True
        return False

    def delete_selected_node(self):
        """Deletes the currently selected node from the tree."""
        if not self.tree_view.selectedIndexes():
            return
        index: QModelIndex = self.tree_view.selectedIndexes()[0]
        item: DLGStandardItem | None = self.itemFromIndex(index)
        assert item is not None
        self.delete_node(item)

    def shift_item(
        self,
        item: DLGStandardItem,
        amount: int,
        *,
        no_selection_update: bool = False,
    ):
        """Shifts an item in the tree by a given amount."""
        old_row: int = item.row()
        item_parent: DLGStandardItem | None = item.parent()
        new_row: int = old_row + amount
        if new_row >= (item_parent or self).rowCount() or new_row < 0:
            return
        assert self.editor is not None, "self.editor is None in shift_item"
        assert item_parent is not None, "item_parent is None in shift_item"
        assert item_parent.link is not None, "item_parent.link is None in shift_item"
        assert item_parent.link.node is not None, "item_parent.link.node is None in shift_item"
        _temp_link: DLGLink = (
            self.editor.core_dlg.starters[old_row]
            if item_parent is None
            else item_parent.link.node.links[old_row]  # pyright: ignore[reportOptionalMemberAccess]
        )
        item_to_move: DLGStandardItem = (item_parent or self).takeRow(old_row)[0]
        (item_parent or self).insertRow(new_row, item_to_move)
        sel_model: QItemSelectionModel | None = self.tree_view.selectionModel()
        if sel_model is not None and not no_selection_update:
            sel_model.select(
                item_to_move.index(),
                QItemSelectionModel.SelectionFlag.ClearAndSelect,
            )

        item_parent = item_to_move.parent()
        if isinstance(item_parent, DLGStandardItem):
            assert item_parent.link is not None
            self.update_item_display_text(item_parent)
            self.sync_item_copies(item_parent.link, item_parent)

        self.layoutChanged.emit()

    def move_item_to_index(
        self,
        item: DLGStandardItem,
        new_index: int,
        target_parent_item: DLGStandardItem | None = None,
        *,
        no_selection_update: bool = False,
    ):
        """Move an item to a specific index within the model."""
        assert self.editor is not None
        source_parent_item: DLGStandardItem | None = item.parent()
        if target_parent_item is source_parent_item and new_index == item.row():
            self.editor.blink_window()
            return
        if (
            target_parent_item is not source_parent_item
            and target_parent_item is not None
            and source_parent_item is not None
            and target_parent_item.link is not None
            and source_parent_item.link is not None
            and target_parent_item.link.node == source_parent_item.link.node
        ):
            self.editor.blink_window()
            return
        if target_parent_item is not None and not target_parent_item.is_loaded():
            self.load_dlg_item_rec(target_parent_item)

        if new_index < 0 or new_index > (target_parent_item or self).rowCount():
            return
        old_row: int = item.row()
        if source_parent_item is target_parent_item and new_index > old_row:
            new_index -= 1
        assert self.editor is not None, "self.editor is None in move_item_to_index"
        assert source_parent_item is not None, "source_parent_item is None in move_item_to_index"
        assert source_parent_item.link is not None, "source_parent_item.link is None in move_item_to_index"
        assert source_parent_item.link.node is not None, "source_parent_item.link.node is None in move_item_to_index"
        _temp_link: DLGLink = (
            self.editor.core_dlg.starters[old_row] if source_parent_item is None else source_parent_item.link.node.links[old_row]  # pyright: ignore[reportOptionalMemberAccess]
        )
        item_to_move: DLGStandardItem = (source_parent_item or self).takeRow(old_row)[0]
        (target_parent_item or self).insertRow(new_index, item_to_move)
        sel_model: QItemSelectionModel | None = self.tree_view.selectionModel()
        if sel_model is None or no_selection_update:
            return
        sel_model.select(
            item_to_move.index(),
            QItemSelectionModel.SelectionFlag.ClearAndSelect,
        )

    def sync_item_copies(
        self,
        link: DLGLink,
        item_to_ignore: DLGStandardItem | None = None,
    ):
        items: list[DLGStandardItem] = self.node_to_items[link.node]

        for item in items:
            if item is item_to_ignore:
                continue
            if not item.is_loaded():
                continue
            assert item.link is not None
            link_to_cur_item: dict[DLGLink, DLGStandardItem | None] = {link: None for link in item.link.node.links}

            self.ignoring_updates = True
            while item.rowCount() > 0:
                child_row: list[DLGStandardItem] = item.takeRow(0)
                child_item: DLGStandardItem | None = child_row[0] if child_row else None
                if child_item is not None and child_item.link is not None:
                    link_to_cur_item[child_item.link] = child_item

            for iterated_link in item.link.node.links:
                child_item = link_to_cur_item[iterated_link]
                if child_item is None:
                    child_item = DLGStandardItem(link=iterated_link)
                    child_item.setData(False, _COPY_ROLE)
                    self.load_dlg_item_rec(child_item)
                item.appendRow(child_item)

            self.ignoring_updates = False


class DLGLinkSync(DLGLink):
    """Keeps a DLGLink object in sync with a copy just in case we devs forgot to call another endless required 'update' function somewhere.

    Not perfect, e.g. if you store `node = link.node`, this class's __setattr__ won't be called for that node on the copied link.
    """
    def __init__(self, *args, **kwargs):
        self._syncer: CopySyncDict  # purely here for type hinting purposes.
        raise RuntimeError("__init__ is not supported, __class__ must be set directly.")

    def __getattr__(self, attr: str):
        if attr == "_syncer":
            return object.__getattribute__(self, "_syncer")
        other = self._syncer.get(self)
        if other is None:
            return object.__getattribute__(self, "_syncer")
        return getattr(other, attr)

    def __setattr__(self, attr: str, value: Any):
        object.__setattr__(self, attr, value)
        if attr == "_syncer":
            return
        other = self._syncer.get(self)
        if other is None:
            return
        object.__setattr__(other, attr, value)

    def __delattr__(self, attr):
        other = self._syncer.get(self)
        delattr(other, attr)


class CopySyncDict(weakref.WeakKeyDictionary):
    """Implements weakkeydictionary in order to keep the keys and their values in sync, as perfect copies, treating them like the same object and providing more hash usability.

    If someone is reading this, to save you some time, this class is wildly unnecessary.
    It was added simply as a fallback in case we forgot to call an update function somewhere. This makes certain our copies have the same data.
    Feel free to replace origToOrphanCopies with a regular dict.
    """
    def __init__(
        self,
        init_dict: Mapping[weakref.ref[DLGLink], DLGLink] | Iterable[tuple[weakref.ref[DLGLink], DLGLink]] | None = None,
        *args,
    ):
        self._storage: dict[int, tuple[weakref.ref[DLGLink], DLGLink]] = {}
        self._weak_key_map: dict[int, weakref.ref[DLGLink]] = {}
        if init_dict is None:
            super().__init__(None)
            return
        if isinstance(init_dict, Mapping):
            for k, v in init_dict.items():
                if isinstance(k, tuple):
                    k, v = k
                self[k] = v
        else:
            for k, v in init_dict:
                self[k] = v
        super().__init__(None)

    def __setitem__(self, key: DLGLink | weakref.ref[DLGLink], value: DLGLinkSync | DLGLink):
        if isinstance(key, weakref.ref):
            ref = key
            key = key()  # pyright: ignore[reportAssignmentType]
            if key is None:
                raise ValueError("Ref passed to CopySyncDict is already garbage collected.")
            key_hash = hash(key)
        else:
            key_hash = hash(key)
            ref = weakref.ref(key, self._remove_key(key_hash))
        self._storage[key_hash] = (ref, value)
        self._weak_key_map[key_hash] = ref

    def __getitem__(self, key: DLGLink) -> DLGLink[Any]:
        key_hash = hash(key)
        if key_hash in self._storage:
            return self._storage[key_hash][1]
        raise KeyError(key)

    def __delitem__(self, key: DLGLink):  # type: ignore[reportIncompatibleMethodOverride]
        key_hash = hash(key)
        del super()[self._storage[key_hash][0]]
        del self._storage[key_hash]
        del self._weak_key_map[key_hash]

    def get(self, key: DLGLink, default: DLGLink = None) -> DLGLink:  # type: ignore[override]
        lookupOrig, lookupCopy = self._storage.get(hash(key), (None, None))
        return default if lookupCopy is None else lookupCopy

    def _remove_key(self, key_hash: int):
        def remove(_):
            del self[self._storage[key_hash][1]]
        return remove

    def values(self) -> Generator[DLGLink, None, None]:  # type: ignore[override]
        return (item for _, item in self._storage.values())

    def items(self) -> Generator[tuple[weakref.ref[DLGLink], DLGLink], None, None]:  # type: ignore[override]
        yield from self._storage.values()

    def replaceCopy(self, link: DLGLink):
        linkHash = link._hash_cache  # noqa: SLF001
        self._storage[linkHash] = (self._weak_key_map[linkHash], link)

    def get_original(self, key: DLGLink) -> weakref.ref[DLGLink]:
        return self._storage[hash(key)][0]

    def get_link_ref(self, link: DLGLink) -> weakref.ref[DLGLink]:
        """Takes a DLGLink object and returns the weak reference for it from the CopySyncDict.

        Args:
        ----
            sync_dict (CopySyncDict): The instance of CopySyncDict.
            link (DLGLink): The DLGLink object to find the weak reference for.

        Returns:
        -------
            weakref.ref[DLGLink]: The weak reference of the DLGLink object.
        """
        link_hash = hash(link)
        if link_hash not in self._weak_key_map:
            RobustLogger().info(f"Creating deepcopy of {link!r}")
            self[link] = DLGLink.from_dict(link.to_dict())
        return self._weak_key_map[link_hash]
