#!/usr/bin/env python3
from __future__ import annotations

import json
import random
import re
import uuid
import weakref

from collections import deque
from contextlib import suppress
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Generator, Iterable, List, Sequence, Union, cast, overload

import qtpy

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy import QtCore
from qtpy.QtCore import QByteArray, QDataStream, QIODevice, QItemSelectionModel, QMimeData, QModelIndex, QPoint, QPointF, QPropertyAnimation, QRect, QSettings, QTimer, Qt
from qtpy.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QDrag,
    QFont,
    QHoverEvent,
    QKeySequence,
    QPainter,
    QPen,
    QPixmap,
    QPolygon,
    QRadialGradient,
    QStandardItem,
    QStandardItemModel,
    QTextDocument,
)
from qtpy.QtWidgets import (
    QAbstractItemView,
    QAction,  # pyright: ignore[reportPrivateImportUsage]
    QApplication,
    QCheckBox,
    QComboBox,
    QCompleter,
    QDialog,
    QDockWidget,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QStyle,
    QTextEdit,
    QToolTip,
    QVBoxLayout,
    QWhatsThis,
    QWidget,
    QWidgetAction,
)

from pykotor.common.misc import Game, ResRef
from pykotor.extract.installation import SearchLocation
from pykotor.resource.generics.dlg import DLG, DLGComputerType, DLGConversationType, DLGEntry, DLGLink, DLGReply, read_dlg, write_dlg
from pykotor.resource.type import ResourceType
from toolset.data.installation import HTInstallation
from toolset.gui.dialogs.edit.dialog_animation import EditAnimationDialog
from toolset.gui.dialogs.edit.dialog_model import CutsceneModelDialog
from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog
from toolset.gui.editor import Editor
from toolset.gui.widgets.settings.installations import GlobalSettings
from toolset.utils.misc import get_qt_key_string
from utility.ui_libraries.qt.adapters.itemmodels.filters import NoScrollEventFilter
from utility.ui_libraries.qt.widgets.itemviews.html_delegate import _ICONS_DATA_ROLE, HTMLDelegate
from utility.ui_libraries.qt.widgets.itemviews.treeview import RobustTreeView

if qtpy.API_NAME in ("PyQt6", "PySide6"):
    from qtpy.QtGui import QUndoStack
else:
    from qtpy.QtWidgets import QUndoStack  # type: ignore[assignment]

if TYPE_CHECKING:
    import os

    from pathlib import PureWindowsPath

    from qtpy.QtCore import QItemSelection, QObject, QPersistentModelIndex
    from qtpy.QtGui import QCloseEvent, QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent, QFocusEvent, QKeyEvent, QMouseEvent, QPaintEvent, QShowEvent
    from qtpy.QtWidgets import QAbstractItemDelegate
    from typing_extensions import Literal, Self

    from pykotor.resource.formats.twoda.twoda_data import TwoDA
    from pykotor.resource.generics.dlg import DLGAnimation, DLGNode, DLGStunt


_LINK_PARENT_NODE_PATH_ROLE = Qt.ItemDataRole.UserRole + 1
_EXTRA_DISPLAY_ROLE = Qt.ItemDataRole.UserRole + 2
_DUMMY_ITEM = Qt.ItemDataRole.UserRole + 3
_COPY_ROLE = Qt.ItemDataRole.UserRole + 4
_DLG_MIME_DATA_ROLE = Qt.ItemDataRole.UserRole + 5
_MODEL_INSTANCE_ID_ROLE = Qt.ItemDataRole.UserRole + 6
QT_STANDARD_ITEM_FORMAT = "application/x-qabstractitemmodeldatalist"


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

    def setData(self, role: int, value: Any):
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
    itemDropped: ClassVar[QtCore.Signal] = QtCore.Signal(QMimeData, Qt.DropAction, name="itemDropped")  # pyright: ignore[reportPrivateImportUsage]

    def __init__(self, parent: DLGEditor):
        super().__init__(parent)
        self.editor: DLGEditor = parent
        self.dragged_item: DLGListWidgetItem | None = None
        self.currentlyHoveredItem: DLGListWidgetItem | None = None
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
        if item is None or item is self.currentlyHoveredItem:
            return
        # print(f"{self.__class__.__name__}.mouseMoveEvent: item hover change {self.currentlyHoveredItem} --> {item.__class__.__name__}")
        if self.currentlyHoveredItem is not None and not self.currentlyHoveredItem.isDeleted() and self.row(self.currentlyHoveredItem) != -1:
            # print("Reset old hover item")
            hover_display = self.currentlyHoveredItem.data(Qt.ItemDataRole.DisplayRole)
            default_display = self.currentlyHoveredItem.data(_EXTRA_DISPLAY_ROLE)
            # print("hover display:", hover_display, "default_display", default_display)
            self.currentlyHoveredItem.setData(Qt.ItemDataRole.DisplayRole, default_display)
            self.currentlyHoveredItem.setData(_EXTRA_DISPLAY_ROLE, hover_display)
        self.currentlyHoveredItem = item
        if self.currentlyHoveredItem is None:
            self.viewport().update()
            return
        # print("Set hover display text for newly hovered over item.")
        hover_display = self.currentlyHoveredItem.data(_EXTRA_DISPLAY_ROLE)
        default_display = self.currentlyHoveredItem.data(Qt.ItemDataRole.DisplayRole)
        # print("hover display:", hover_display, "default_display", default_display)
        self.currentlyHoveredItem.setData(Qt.ItemDataRole.DisplayRole, hover_display)
        self.currentlyHoveredItem.setData(_EXTRA_DISPLAY_ROLE, default_display)
        self.viewport().update()

    def isPersistentEditorOpen(self, item: DLGListWidgetItem) -> bool:  # type: ignore[override, misc]
        assert isinstance(item, DLGListWidgetItem)
        return super().isPersistentEditorOpen(item)

    def removeItemWidget(self, aItem: DLGListWidgetItem):  # type: ignore[override, misc]
        assert isinstance(aItem, DLGListWidgetItem)
        super().removeItemWidget(aItem)

    def itemFromIndex(self, index: QModelIndex) -> DLGListWidgetItem:
        item: QListWidgetItem = super().itemFromIndex(index)
        assert isinstance(item, DLGListWidgetItem)
        return item

    def indexFromItem(self, item: DLGListWidgetItem) -> QModelIndex:  # type: ignore[override, misc]
        assert isinstance(item, DLGListWidgetItem)
        return super().indexFromItem(item)

    def focusOutEvent(self, event: QFocusEvent):
        super().focusOutEvent(event)
        if self.currentlyHoveredItem is not None and not self.currentlyHoveredItem.isDeleted() and self.row(self.currentlyHoveredItem) != -1:
            # print("Reset old hover item")
            hover_display = self.currentlyHoveredItem.data(Qt.ItemDataRole.DisplayRole)
            default_display = self.currentlyHoveredItem.data(_EXTRA_DISPLAY_ROLE)
            # print("hover display:", hover_display, "default_display", default_display)
            self.currentlyHoveredItem.setData(Qt.ItemDataRole.DisplayRole, default_display)
            self.currentlyHoveredItem.setData(_EXTRA_DISPLAY_ROLE, hover_display)
        self.currentlyHoveredItem = None

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
        if event.mime_data().hasFormat(QT_STANDARD_ITEM_FORMAT):
            print("DLGListWidget.dropEvent: mime data has our format")
            assert self.editor is not None
            item_data: list[dict[Literal["row", "column", "roles"], Any]] = self.editor.ui.dialogTree.parse_mime_data(event.mime_data())
            link: DLGLink = DLGLink.from_dict(json.loads(item_data[0]["roles"][_DLG_MIME_DATA_ROLE]))
            new_item = DLGListWidgetItem(link=link)
            self.update_item(new_item)
            self.addItem(new_item)
            event.accept()
            self.itemDropped.emit(event.mime_data(), event.dropAction())
        else:
            print("DLGListWidget.dropEvent: invalid mime data")
            event.ignore()

    def mime_data(self, items: Iterable[DLGListWidgetItem]) -> QMimeData:  # type: ignore[override, misc]
        print(f"DLGListWidget.dropEvent: acquiring mime data for {len(list(items))} items")
        return super().mime_data(items)  # type: ignore[arg-type]

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
        return super().itemWidget(item)

    @overload
    def itemAt(self, p: QPoint) -> DLGListWidgetItem | None: ...
    @overload
    def itemAt(self, ax: int, ay: int) -> DLGListWidgetItem | None: ...
    def itemAt(self, *args) -> DLGListWidgetItem | None:  # type: ignore[override, misc]
        item: QListWidgetItem = super().itemAt(*args)
        assert isinstance(item, (DLGListWidgetItem, type(None)))
        return item

    def currentItem(self) -> DLGListWidgetItem:
        item: QListWidgetItem = super().currentItem()
        assert isinstance(item, (DLGListWidgetItem, type(None)))
        return item

    def takeItem(self, row: int) -> DLGListWidgetItem:
        item: QListWidgetItem = super().takeItem(row)
        assert isinstance(item, (DLGListWidgetItem, type(None)))
        return item

    def insertItem(self, row: int, item: DLGListWidgetItem | str):  # type: ignore[override, misc]
        if isinstance(item, DLGListWidgetItem):
            super().insertItem(row, item)
        elif isinstance(item, str):
            super().insertItem(row, item)
        else:
            raise TypeError("Incorrect args passed to insertItem")

    def row(self, item: DLGListWidgetItem) -> int:  # type: ignore[override, misc]
        assert isinstance(item, (DLGListWidgetItem, type(None)))
        return super().row(item)

    def item(self, row: int) -> DLGListWidgetItem:
        item = super().item(row)
        assert isinstance(item, (DLGListWidgetItem, type(None)))
        return item


class DLGStandardItem(QStandardItem):
    def __init__(self, *args, link: DLGLink, **kwargs):
        super().__init__(*args, **kwargs)
        self.ref_to_link: weakref.ref[DLGLink] = weakref.ref(link)  # Store a weak reference to the link
        self._data_cache: dict[int, Any] = {}

    def __repr__(self) -> str:  # noqa: C901
        def format_repr(details: dict[str, Any]) -> str:
            return f"DLGStandardItem({', '.join(f'{key}: {value}' for key, value in details.items())})"

        def format_cache(cache: dict[int, Any]) -> dict[str, str]:
            role_map = {
                0: "DisplayRole",
                1: "DecorationRole",
                2: "EditRole",
                3: "ToolTipRole",
                4: "StatusTipRole",
                5: "WhatsThisRole",
                6: "FontRole",
                7: "TextAlignmentRole",
                8: "BackgroundRole",
                9: "ForegroundRole",
                10: "CheckStateRole",
                11: "AccessibleTextRole",
                12: "AccessibleDescriptionRole",
                13: "SizeHintRole",
                14: "InitialSortOrderRole",
                256: "UserRole",
            }

            formatted_cache = {}
            for k, v in cache.items():
                repr_v = repr(v)
                if k in role_map:
                    formatted_key = role_map[k]
                elif k >= 256:
                    formatted_key = f"UserRole+{k - 256}"
                else:
                    formatted_key = str(k)
                formatted_cache[formatted_key] = f"{repr_v[:30]}..." if len(repr_v) > 30 else repr_v
            return formatted_cache

        details: dict[str, str] = {"Roles": str(format_cache(self._data_cache))}
        try:
            if self.link:
                details["Link"] = repr(self.link)
            else:
                details["Link Ref"] = repr(self.ref_to_link)
        except Exception as e:  # noqa: BLE001
            details["Link Exception"] = f"{e.__class__.__name__}: {e}"

        try:
            text = self.text()
            details["Text"] = repr(f"{text[:50]}..." if len(text) > 50 else text)
        except Exception as e:  # noqa: BLE001
            details["Text Exception"] = f"{e.__class__.__name__}: {e}"

        try:
            parent_item = self.parent()
            details["Parent"] = "None" if parent_item is None else f"Parent Row: {parent_item.index().row()}"
            if parent_item is not None:
                with suppress(Exception):
                    parent_text = parent_item.text()
                    details["Parent Text"] = f"Parent Text: {f'{parent_text[:50]}...' if len(parent_text) > 50 else parent_text}"
        except Exception as e:  # noqa: BLE001
            details["Parent Exception"] = f"{e.__class__.__name__}: {e}"

        try:
            details["Children Count"] = str(self.rowCount())
        except Exception as e:  # noqa: BLE001
            details["Children Count Exception"] = f"{e.__class__.__name__}: {e}"

        try:
            model = self.model()
            if model is None:
                details["Model"] = "Not available"
                return format_repr(details)
        except Exception as e:  # noqa: BLE001
            details["Model Exception"] = f"{e.__class__.__name__}: {e}"
            return format_repr(details)

        # Index and model information
        try:
            index = self.index()
            if not index.isValid():
                details["Index"] = "Invalid"
                return format_repr(details)
            details["Row"] = str(index.row())
            details["Column"] = str(index.column())
        except Exception as e:  # noqa: BLE001
            details["Index Exception"] = f"{e.__class__.__name__}: {e}"
            return format_repr(details)

        # Ancestor count
        try:
            ancestors = 0
            parent_index = index.parent()
            while parent_index.isValid():
                ancestors += 1
                parent_index = parent_index.parent()
            details["Ancestors"] = str(ancestors)
        except Exception as e:  # noqa: BLE001
            details["Ancestor Exception"] = f"{e.__class__.__name__}: {e}"

        return format_repr(details)

    @property
    def link(self) -> DLGLink | None:
        """Return the link, or None if the reference is no longer valid.

        Weak references are used throughout to ensure that orphaned nodes will be automatically detected and added to the orphaned_nodes_list listwidget.

        IMPORTANT: Do NOT save or store this result to e.g. a lambda, otherwise that lambda provides a strong reference and due to the nature of lambdas, becomes very difficult to track down.
        To be safe, it's just best to never save this to a local variable. Just test `item.link is not None` whenever you need the link and send `item.link` directly to wherever you need it.
        """
        return self.ref_to_link()

    @link.setter
    def link(self, new_link: DLGLink):
        raise NotImplementedError("DLGStandardItem's cannot store strong references to DLGLink objects.")

    def parent(self) -> DLGStandardItem | None:  # type: ignore[override, misc]
        return super().parent()  # type: ignore[return-value]

    def __eq__(self, other):
        return self is other

    def __hash__(self) -> int:
        return id(self)

    def index(self) -> QModelIndex:
        result = super().index()
        if not result.isValid():
            model = self.model()
            if model:
                return model.indexFromItem(self)
        return result

    def isDeleted(self) -> bool:
        """Determines if this object has been deleted.

        Not sure what the proper method of doing so is, but this works fine.
        """
        try:
            self.model()
            self.index()
        except RuntimeError as e:  # RuntimeError: wrapped C/C++ object of type DLGStandardItem has been deleted
            RobustLogger().warning(f"isDeleted suppressed the following exception: {e.__class__.__name__}: {e}")
            return True
        else:
            return False

    def model(self) -> DLGStandardItemModel:
        model = super().model()
        assert isinstance(model, DLGStandardItemModel), f"model was {model} of type {model.__class__.__name__}"
        return model

    def is_copy(self) -> bool:
        result = self.data(_COPY_ROLE)
        assert result is not None
        return result

    def is_loaded(self) -> bool:
        if not self.is_copy():
            return True
        if not self.hasChildren():
            return True
        item = self.child(0, 0)
        if isinstance(item, DLGStandardItem):
            return True
        dummy = item.data(_DUMMY_ITEM)
        assert dummy is True
        return False

    def appendRow(self, item: DLGStandardItem):  # type: ignore[override, misc]
        # print(f"{self.__class__.__name__}.appendRow(item={item!r})")
        assert isinstance(item, DLGStandardItem) or cast(QStandardItem, item).data(_DUMMY_ITEM)
        super().appendRow(item)
        model = self.model()
        if model is not None and not model.ignoring_updates and isinstance(item, DLGStandardItem):
            model._processLink(self, item)  # noqa: SLF001

    def appendRows(self, items: Iterable[DLGStandardItem]):  # type: ignore[override]
        print(f"{self.__class__.__name__}.appendRows(items={items!r})")
        for item in items:
            self.appendRow(item)

    def insertRow(self, row: int, item: DLGStandardItem):  # type: ignore[override, misc]
        print(f"{self.__class__.__name__}.insertRow(row={row}, item={item})")
        assert isinstance(item, DLGStandardItem) or cast(QStandardItem, item).data(_DUMMY_ITEM)
        super().insertRow(row, item)
        model = self.model()
        if model is not None and isinstance(item, DLGStandardItem) and not model.ignoring_updates:
            model._processLink(self, item, row)  # noqa: SLF001

    def insertRows(self, row: int, items: Iterable[Self]):  # type: ignore[override]
        print(f"{self.__class__.__name__}.insertRows(row={row}, items={items})")
        assert not isinstance(items, int), "Second arg cannot be a `count` in this implementation."
        for i, item in enumerate(items):
            self.insertRow(row + i, item)

    def removeRow(self, row: int) -> list[DLGStandardItem] | None:  # type: ignore[override]
        # print(f"{self.__class__.__name__}.removeRow(row={row})")
        items = super().takeRow(row)
        model = self.model()
        if model is not None and items and not model.ignoring_updates:
            for item in items:
                if not isinstance(item, DLGStandardItem):
                    continue
                model._removeLinkFromParent(self, item.link)  # noqa: SLF001
        return cast(List[DLGStandardItem], items)

    def removeRows(self, row: int, count: int):
        print(f"{self.__class__.__name__}.removeRows(row={row}, count={count})")
        for _ in range(count):
            self.removeRow(row)

    def setChild(self, row: int, *args):
        print(f"{self.__class__.__name__}.setChild(row={row}, args={args!r})")
        super().setChild(row, *args)
        item = args[1] if len(args) == 3 else args[0]
        assert isinstance(item, DLGStandardItem) or cast(QStandardItem, item).data(_DUMMY_ITEM)
        model = self.model()
        if model is not None and isinstance(item, DLGStandardItem) and not model.ignoring_updates:
            model._processLink(self, item)  # noqa: SLF001

    def takeChild(self, row: int, column: int = 0) -> Self | None:  # type: ignore[override]
        # print(f"{self.__class__.__name__}.takeChild(row={row}, column={column})")
        item = cast(Union[QStandardItem, None], super().takeChild(row, column))
        if item is None:
            return None
        assert isinstance(item, DLGStandardItem) or item.data(_DUMMY_ITEM)
        model = self.model()
        if model is not None and isinstance(item, DLGStandardItem) and not model.ignoring_updates:
            model._removeLinkFromParent(self, item.link)  # noqa: SLF001
        return item  # pyright: ignore[reportReturnType]

    def takeRow(self, row: int) -> list[DLGStandardItem]:  # type: ignore[override]
        # print(f"{self.__class__.__name__}.takeRow(row={row})")
        items = super().takeRow(row)
        model = self.model()
        if model is not None and items and not model.ignoring_updates:
            for item in items:
                if not isinstance(item, DLGStandardItem):
                    continue
                model._removeLinkFromParent(self, item.link)  # noqa: SLF001
        return cast(List[DLGStandardItem], items)

    def takeColumn(self, column: int) -> list[DLGStandardItem]:  # type: ignore[override]
        raise NotImplementedError("takeColumn is not supported in this model.")
        # items = super().takeColumn(column)
        # if self.model() and not self.model().ignoring_updates:
        #    for item in items:
        #        self.model()._removeLinkFromParent(self, item.link)
        # return items

    def data(self, role: int = Qt.ItemDataRole.UserRole) -> Any:
        """Returns the data for the role. Uses cache if the item has been deleted."""
        if self.isDeleted():
            return self._data_cache.get(role)
        result = super().data(role)
        self._data_cache[role] = result
        # print(f"{self.__class__.__name__}.data(role={role}) --> {result}")
        return result

    def setData(self, value: Any, role: int = Qt.ItemDataRole.UserRole):
        """Sets the data for the role and updates the cache."""
        # print(f"{self.__class__.__name__}.setData(value={value}, role={role})")
        self._data_cache[role] = value  # Update cache
        super().setData(value, role)


class DLGStandardItemModel(QStandardItemModel):
    # Signal emitted when item data has changed
    # dataChanged: ClassVar[QtCore.Signal] = QtCore.Signal(QModelIndex, QModelIndex, list)  # list of roles changed

    # Signal emitted when header data has changed
    # headerDataChanged = QtCore.Signal(Qt.Orientation, int, int)  # orientation, first section, last section

    # Signals for layout changes
    # layoutChanged = QtCore.Signal(list, QStandardItemModel.LayoutChangeHint)  # list of parent indices, layout change hint
    # layoutAboutToBeChanged = QtCore.Signal(list, QStandardItemModel.LayoutChangeHint)  # list of parent indices, layout change hint

    # Signals for row operations
    # rowsInserted = QtCore.Signal(QModelIndex, int, int)  # parent index, start row, end row
    # rowsAboutToBeInserted = QtCore.Signal(QModelIndex, int, int)  # parent index, start row, end row
    # rowsRemoved = QtCore.Signal(QModelIndex, int, int)  # parent index, start row, end row
    # rowsAboutToBeRemoved = QtCore.Signal(QModelIndex, int, int)  # parent index, start row, end row
    # rowsMoved = QtCore.Signal(QModelIndex, int, int, QModelIndex, int)  # source parent, start row, end row, destination parent, destination row
    # rowsAboutToBeMoved = QtCore.Signal(QModelIndex, int, int, QModelIndex, int)  # source parent, start row, end row, destination parent, destination row

    # Signals for column operations
    # columnsInserted = QtCore.Signal(QModelIndex, int, int)  # parent index, start column, end column
    # columnsAboutToBeInserted = QtCore.Signal(QModelIndex, int, int)  # parent index, start column, end column
    # columnsRemoved = QtCore.Signal(QModelIndex, int, int)  # parent index, start column, end column
    # columnsAboutToBeRemoved = QtCore.Signal(QModelIndex, int, int)  # parent index, start column, end column
    # columnsMoved = QtCore.Signal(QModelIndex, int, int, QModelIndex, int)  # source parent, start column, end column, destination parent, destination column
    # columnsAboutToBeMoved: ClassVar[QtCore.Signal] = QtCore.Signal(QModelIndex, int, int, QModelIndex, int)  # source parent, start column, end column, destination parent, destination column

    # Signals for model reset
    # modelReset: ClassVar[QtCore.Signal] = QtCore.Signal()  # No parameters
    # modelAboutToBeReset: ClassVar[QtCore.Signal] = QtCore.Signal()  # No parameters

    # Custom for this model.
    sig_core_dlg_item_data_changed: ClassVar[QtCore.Signal] = QtCore.Signal(QStandardItem)  # pyright: ignore[reportPrivateImportUsage]

    def __init__(self, parent: DLGTreeView):
        # assert isinstance(parent, DLGTreeView), f"Expected DLGTreeView, got {type(parent)} ({parent.__class__.__name__})"
        self.editor: DLGEditor | None = None
        self.tree_view: DLGTreeView = parent
        self.link_to_items: weakref.WeakKeyDictionary[DLGLink, list[DLGStandardItem]] = weakref.WeakKeyDictionary()
        self.node_to_items: weakref.WeakKeyDictionary[DLGNode, list[DLGStandardItem]] = weakref.WeakKeyDictionary()
        self.orig_to_orphan_copy: dict[weakref.ReferenceType[DLGLink], DLGLink]
        super().__init__(self.tree_view)
        self.modelReset.connect(self.onModelReset)
        self.sig_core_dlg_item_data_changed.connect(self.on_dialog_item_data_changed)
        self.ignoring_updates: bool = False

    def __iter__(self) -> Generator[DLGStandardItem, Any, None]:
        stack: deque[DLGStandardItem | QStandardItem] = deque([self.item(row, column) for row in range(self.rowCount()) for column in range(self.columnCount())])
        while stack:
            item: DLGStandardItem | QStandardItem = stack.popleft()
            if not isinstance(item, DLGStandardItem):
                continue
            yield item
            stack.extend([item.child(row, column) for row in range(item.rowCount()) for column in range(item.columnCount())])

    # region Model Overrides
    def insertRows(self, row: int, count: int, parent: QModelIndex | None = None) -> bool:
        print(f"{self.__class__.__name__}.insertRows(row={row}, count={count}, parent_index={parent})")
        if parent is None:
            parent = QModelIndex()
        self.beginInsertRows(parent, row, row + count - 1)
        result = super().insertRows(row, count, parent)
        self.endInsertRows()
        return result

    def removeRows(self, row: int, count: int, parent: QModelIndex | None = None) -> bool:
        print(f"{self.__class__.__name__}.removeRows(row={row}, count={count}, parent_index={parent})")
        if row < 0 or count < 1:
            # Check for negative or invalid row index and count
            print(f"Invalid row ({row}) or count ({count})")
            return False
        parent = (self.itemFromIndex(parent) or self) if parent is not None and parent.isValid() else self
        rows_available = parent.rowCount()
        if row + count > rows_available:
            # Check if the range exceeds the number of rows
            print(f"DEBUG(root): Request to remove {count} rows at index {row} exceeds model bounds ({rows_available}).")
            return False

        self.tree_view.selectionModel().clear()
        if parent is not None:
            links = [item.link for item in (self.itemFromIndex(self.index(r, 0, parent)) for r in range(row, row + count)) if item is not None]
        else:
            links = [item.link for item in (self.item(r, 0) for r in range(row, row + count))]  # pyright: ignore[reportAttributeAccessIssue]
        self.beginRemoveRows(QModelIndex() if parent is None else parent, row, row + count - 1)
        result = super().removeRows(row, count, parent)  # type: ignore[arg-type]
        self.tree_view.selectionModel().clear()
        self.endRemoveRows()
        if not self.ignoring_updates:
            parent_item = None if parent is None else self.itemFromIndex(parent)
            for link in links:
                if link is None or parent_item is not None and not isinstance(parent_item, DLGStandardItem):
                    continue
                self._removeLinkFromParent(parent_item, link)
        return result

    def appendRows(self, items: Iterable[DLGStandardItem], parent_index: QModelIndex | None = None):
        print(f"{self.__class__.__name__}.appendRows(items={items}, parent_index={parent_index})")
        for item in items:
            self.appendRow(item, parent_index)  # type: ignore[call-overload]

    def removeRow(self, row: int, parent_index: QModelIndex | None = None) -> bool:
        print(f"{self.__class__.__name__}.removeRow(row={row}, parent_index={parent_index})")
        if parent_index is not None and parent_index.isValid():
            return super().removeRow(row, parent_index)
        return super().removeRow(row)

    def item(self, row: int, column: int) -> DLGStandardItem | QStandardItem:  # type: ignore[override]
        print(f"{self.__class__.__name__}.item(row={row}, column={column})")
        return super().item(row, column)

    @overload
    def insertRow(self, row: int, items: Iterable[QStandardItem]): ...
    @overload
    def insertRow(self, arow: int, aitem: QStandardItem): ...
    @overload
    def insertRow(self, row: int, parent: QModelIndex = ...) -> bool: ...
    def insertRow(  # type: ignore[override, misc]
        self,
        row: int,
        toInsert: Iterable[QStandardItem] | QStandardItem | QModelIndex,
    ) -> bool | None:
        print(f"{self.__class__.__name__}.insertRow(row={row}, toInsert={toInsert})")
        result = super().insertRow(row, toInsert)
        if isinstance(toInsert, Iterable):
            if not self.ignoring_updates:
                for itemToInsert in toInsert:
                    if not isinstance(itemToInsert, DLGStandardItem):
                        continue
                    if itemToInsert.link is None:
                        continue
                    parent_item = itemToInsert.parent()
                    self._insertLinkToParent(parent_item, itemToInsert, row)
        elif isinstance(toInsert, (QModelIndex, QStandardItem)):
            if not self.ignoring_updates:
                itemToInsert = toInsert if isinstance(toInsert, QStandardItem) else self.itemFromIndex(toInsert)
                if not isinstance(itemToInsert, DLGStandardItem):
                    return result
                if itemToInsert.link is None:
                    return result
                parent_item = itemToInsert.parent()
                self._insertLinkToParent(parent_item, itemToInsert, row)
        else:
            raise TypeError("Incorrect args passed to insertRow")
        return result

    def takeItem(self, row: int, column: int) -> DLGStandardItem:  # type: ignore[override]
        print(f"{self.__class__.__name__}.takeItem(row={row}, column={column})")
        item = cast(DLGStandardItem, super().takeItem(row, column))
        if not self.ignoring_updates:
            self._removeLinkFromParent(None, item.link)
        return item

    def takeRow(self, row: int) -> list[DLGStandardItem]:  # type: ignore[override]
        print(f"{self.__class__.__name__}.takeRow(row={row})")
        items = cast(List[DLGStandardItem], super().takeRow(row))
        if not items:
            return items
        if self.ignoring_updates:
            return items
        for item in items:
            if not isinstance(item, DLGStandardItem):
                continue
            self._removeLinkFromParent(None, item.link)
        return items

    @overload
    def appendRow(self, items: Iterable[DLGStandardItem]): ...
    @overload
    def appendRow(self, aitem: DLGStandardItem): ...
    def appendRow(self, *args):  # type: ignore[override, misc]
        # print(f"{self.__class__.__name__}.appendRow(args={args})")
        itemToAppend: DLGStandardItem = args[0]
        super().appendRow(itemToAppend)
        if not self.ignoring_updates:
            self._insertLinkToParent(None, itemToAppend, self.rowCount())

    # endregion

    # region drag&drop
    def supportedDropActions(self) -> Qt.DropAction:
        return Qt.DropAction.CopyAction | Qt.DropAction.MoveAction

    def supportedDragActions(self) -> Qt.DropAction:
        return Qt.DropAction.CopyAction | Qt.DropAction.MoveAction

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        # print(f"DLGStandardItemModel.flags(index={index})\nindex details: {self.tree_view.getIdentifyingTextForIndex(index)}")
        defaultFlags = super().flags(index)
        if index.isValid():
            return Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsDropEnabled | defaultFlags
        return Qt.ItemFlag.ItemIsDropEnabled | defaultFlags

    def mimeTypes(self) -> list[str]:
        return [QT_STANDARD_ITEM_FORMAT]

    def get_identifying_text(self, indexOrItem: QModelIndex | QStandardItem | None) -> str:  # noqa: N803, C901, PLR0911
        if indexOrItem is None:
            return "(None)"
        if isinstance(indexOrItem, QStandardItem):
            try:
                indexOrItem = indexOrItem.index()
            except RuntimeError as e:  # wrapped C/C++ object of type x has been deleted
                return str(e)
        if not isinstance(indexOrItem, QModelIndex):
            return f"(Unknown index/item: {indexOrItem})"
        if not indexOrItem.isValid():
            return f"(invalid index at row '{indexOrItem.row()}', column '{indexOrItem.column()}')"

        if isinstance(self, QStandardItemModel):
            item = self.itemFromIndex(indexOrItem)
            if item is None:
                return f"(no item associated with index at row '{indexOrItem.row()}', column '{indexOrItem.column()}')"
            text = item.text().strip()
        parent_count = 0
        current_index = indexOrItem.parent()
        while current_index.isValid():
            parent_count += 1
            current_index = current_index.parent()

        return f"Item/Index at Row: {indexOrItem.row()}, Column: {indexOrItem.column()}, Ancestors: {parent_count}\nText for above item: {text}\n"

    def mime_data(self, indexes: Iterable[QModelIndex]) -> QMimeData:
        mime_data = QMimeData()
        data = QByteArray()
        stream = QDataStream(data, QIODevice.WriteOnly)
        for index in indexes:
            print("<SDM> [mime_data scope] index: ", self.get_identifying_text(index))
            assert index.isValid()
            item = self.itemFromIndex(index)
            assert item is not None
            assert item.link is not None
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

    def dropMimeData(  # noqa: PLR0913
        self,
        data: QMimeData,
        action: Qt.DropAction,
        row: int,
        column: int,
        parent: QModelIndex | QPersistentModelIndex,
    ) -> bool:
        print(f"{self.__class__.__name__}.dropMimeData(data, action={action}, row={row}, column={column}, parent={parent})")
        if not data.hasFormat(QT_STANDARD_ITEM_FORMAT):
            return False
        if action == Qt.DropAction.IgnoreAction:
            print(f"{self.__class__.__name__}.dropMimeData: action set to Qt.DropAction.IgnoreAction")
            return True

        parent_item: DLGStandardItem | None = self.itemFromIndex(parent) if parent.isValid() else None
        try:
            parsed_mime_data: dict[Literal["row", "column", "roles"], Any] = self.tree_view.parse_mime_data(data)[0]
            dlg_nodes_json: str = parsed_mime_data["roles"][_DLG_MIME_DATA_ROLE]
            dlg_nodes_dict: dict[str | int, Any] = json.loads(dlg_nodes_json)
            deserialized_dlg_link: DLGLink = DLGLink.from_dict(dlg_nodes_dict)
            print("<SDM> [dropMimeData scope] deserialized_dlg_link: ", repr(deserialized_dlg_link))
        except Exception:  # noqa: BLE001
            RobustLogger().exception("Failed to deserialize dropped mime data of '_DLG_MIME_DATA_ROLE' format.")
            return True
        else:
            self.paste_item(parent_item, deserialized_dlg_link, as_new_branches=parsed_mime_data["roles"][_MODEL_INSTANCE_ID_ROLE] == id(self))

        return True

    # endregion

    # region Model Signals
    def onModelReset(self):
        print(f"{self.__class__.__name__}.onModelReset()")
        self.link_to_items.clear()
        self.node_to_items.clear()

    def reset_model(self):
        print(f"{self.__class__.__name__}.resetModel()")
        self.beginResetModel()
        self.clear()
        self.onModelReset()
        self.endResetModel()

    def on_dialog_item_data_changed(self, item: DLGStandardItem):
        print(f"on_dialog_item_data_changed(item={item!r})")
        if item.link is None:
            # del self.orig_to_orphan_copy[item._link_ref]
            self.removeRow(item.row())
        else:
            print("on_dialog_item_data_changed: link is valid")
            # First take out and store the links/node
            # So we can update our instance objects, without breaking the whole DAG.
            internalLink = self.orig_to_orphan_copy[item.ref_to_link]
            internalLinkedNode = internalLink.node
            assert internalLinkedNode is not None
            del internalLink.__dict__["node"]
            tempLinks = internalLinkedNode.links
            del internalLinkedNode.__dict__["links"]
            # Call update, probably faster than assigning attrs manually.
            internalLink.__dict__.update(item.link.__dict__)
            internalLinkedNode.__dict__.update(item.link.node.__dict__)
            internalLink.node = internalLinkedNode
            internalLinkedNode.links = tempLinks
            self.update_item_display_text(item)

    def onOrphanedNode(self, shallow_link_copy: DLGLink, link_parent_path: str, *, immediateCheck: bool = False):
        """Add a deleted node to the QListWidget in the left_dock_widget, if the passed link is the only reference."""
        if not shallow_link_copy.node or shallow_link_copy.list_index == -1 and shallow_link_copy.node.list_index == -1:
            print(f"ignoring unfinished node/link {shallow_link_copy!r}")
            return
        if not immediateCheck:
            QTimer.singleShot(200, lambda *args: self.onOrphanedNode(shallow_link_copy, link_parent_path, immediateCheck=True))
            return
        print(f"onOrphanedNode({shallow_link_copy}, {link_parent_path})")
        assert self.editor is not None
        print(f"Deleted the only link ({shallow_link_copy}) to node ({shallow_link_copy.node}), setting up the orphan view.")
        item = DLGListWidgetItem(link=shallow_link_copy)
        item.is_orphaned = True
        self.editor.orphaned_nodes_list.update_item(item)
        self.editor.orphaned_nodes_list.addItem(item)

    # endregion

    def insertLinkToParentAsItem(
        self,
        parent: DLGStandardItem | None,
        link: DLGLink,
        row: int | None = -1,
    ) -> DLGStandardItem:
        item = DLGStandardItem(link=link)
        if parent is None:
            self.insertRow(self.rowCount() if row in (-1, None) else row, item)
        else:
            parent.insertRow(self.rowCount() if row in (-1, None) else row, item)
        return item

    def remove_link(self, item: DLGStandardItem):
        """Removes the link from the parent node."""
        parent = item.parent()
        item_row = item.row()
        print("<SDM> [removeLink scope] item_row: %s", item_row)

        if parent is None:
            self.removeRow(item_row)
        else:
            assert isinstance(parent, DLGStandardItem)
            assert parent.link is not None
            print("<SDM> [removeLink scope] parent: %s", parent.text())
            parent.removeRow(item_row)
        self.layoutChanged.emit()

    def _insertLinkToParent(
        self,
        parent: DLGStandardItem | None,
        items: Iterable[DLGStandardItem] | DLGStandardItem,
        row: int | None = -1,
    ):
        if row is None:
            row = -1
        if isinstance(items, Iterable):
            for i, item in enumerate(items):
                self._processLink(parent, item, row + i)
        else:
            self._processLink(parent, items, row)

    def _processLink(
        self,
        parent_item: DLGStandardItem | None,
        item: DLGStandardItem,
        row: int | None = -1,
    ):
        assert item.link is not None, "item.link cannot be None in _processLink"
        assert self.editor is not None, "self.editor cannot be None in _processLink"
        index = (parent_item or self).rowCount() if row in (-1, None) else row
        RobustLogger().info(f"SDM [_processLink scope] Adding #{item.link.node.list_index} to row {index}")
        links_list = self.editor.core_dlg.starters if parent_item is None else parent_item.link.node.links
        node_to_items = self.node_to_items.setdefault(item.link.node, [])
        if item not in node_to_items:
            node_to_items.append(item)
        link_to_items = self.link_to_items.setdefault(item.link, [])
        if item not in link_to_items:
            link_to_items.append(item)
        current_index = {link: idx for idx, link in enumerate(links_list)}.get(item.link)
        if current_index != index:
            if current_index is not None:
                links_list.pop(current_index)
                if current_index < index:
                    index -= 1
            links_list.insert(index, item.link)
        for i, link in enumerate(links_list):
            link.list_index = i
        if isinstance(parent_item, DLGStandardItem):
            assert parent_item.link is not None, f"parent_item.link cannot be None. {parent_item.__class__.__name__}: {parent_item}"
            self.update_item_display_text(parent_item)
            self.sync_item_copies(parent_item.link, parent_item)
        if item.ref_to_link in self.orig_to_orphan_copy:
            return
        RobustLogger().debug(f"Creating internal copy of item: {item!r}")
        copiedLink = DLGLink.from_dict(item.link.to_dict())
        self.orig_to_orphan_copy[item.ref_to_link] = copiedLink  # noqa: SLF001
        self.register_deepcopies(item.link, copiedLink)

    def _removeLinkFromParent(
        self,
        parent_item: DLGStandardItem | None,
        link: DLGLink | None,
    ):
        assert self.editor is not None
        if link is None:
            return
        # The items could be deleted by qt at this point, so we only use the python object.
        links_list = self.editor.core_dlg.starters if parent_item is None else parent_item.link.node.links
        index = links_list.index(link)
        RobustLogger().info(f"SDM [_removeLinkFromParent scope] Removing #{link.node.list_index} from row(link index) {index}")
        links_list.remove(link)
        for i in range(index, len(links_list)):
            links_list[i].list_index = i
        if isinstance(parent_item, DLGStandardItem):
            assert parent_item is not None
            assert parent_item.link is not None
            self.update_item_display_text(parent_item)
            self.sync_item_copies(parent_item.link, parent_item)

    def get_copy(self, original: DLGLink) -> DLGLink | None:
        """Retrieve the copy of the original object using the weak reference."""
        assert self.editor is not None
        return next(
            (copiedLink for orig_ref, copiedLink in self.orig_to_orphan_copy.items() if orig_ref() is original),
            None,
        )

    def register_deepcopies(
        self,
        origLink: DLGLink,
        copyLink: DLGLink,
        seenLinks: set[DLGLink] | None = None,
    ):
        """Recursively register deepcopies of nested links to avoid redundant deepcopies."""
        if seenLinks is None:
            seenLinks = set()
        if copyLink in seenLinks:
            return
        seenLinks.add(copyLink)
        assert origLink is not copyLink
        self.orig_to_orphan_copy[weakref.ref(origLink)] = copyLink
        for childOrigLink, childCopyLink in zip(origLink.node.links, copyLink.node.links):
            self.register_deepcopies(childOrigLink, childCopyLink, seenLinks)

    def load_dlg_item_rec(self, itemToLoad: DLGStandardItem, copiedLink: DLGLink | None = None):
        """Loads a DLGLink recursively getting all its nested items integrated into the model.

        If `itemToLoad.link` already exists in the model, this will set it as a copy, which means it'll
        have _COPY_ROLE assigned and will only be loaded in `onItemExpanded`.
        """
        assert itemToLoad.link is not None
        assert self.editor is not None

        child_links_copy: Sequence[DLGLink | None] = [None]
        if copiedLink is not None and itemToLoad.ref_to_link not in self.orig_to_orphan_copy:
            self.orig_to_orphan_copy[itemToLoad.ref_to_link] = copiedLink
        elif copiedLink is None:
            copiedLink = self.orig_to_orphan_copy.get(itemToLoad.ref_to_link)
        if copiedLink is None:
            RobustLogger().info(f"Creating new internal copy of {itemToLoad.link!r}")
            copiedLink = DLGLink.from_dict(itemToLoad.link.to_dict())
            self.register_deepcopies(itemToLoad.link, copiedLink)
        child_links_copy = copiedLink.node.links

        assert itemToLoad.link is not copiedLink  # new copies should be made before load_dlg_item_rec to reduce complexity.
        parent_path = itemToLoad.data(_LINK_PARENT_NODE_PATH_ROLE)
        if all(info.weakref() is not itemToLoad.link.node for info in weakref.finalize._registry.values()):  # noqa: SLF001  # type: ignore[]
            weakref.finalize(itemToLoad.link.node, self.onOrphanedNode, copiedLink, parent_path)

        alreadyListed = itemToLoad.link in self.link_to_items
        self.link_to_items.setdefault(itemToLoad.link, []).append(itemToLoad)
        self.node_to_items.setdefault(itemToLoad.link.node, []).append(itemToLoad)
        if not alreadyListed:
            parent_item = itemToLoad.parent()
            assert parent_item is None or not parent_item.data(_COPY_ROLE), "Buggy code detected in the model: how can parent_item be a copy if itemToLoad hasn't been seen?"
            itemToLoad.setData(False, _COPY_ROLE)
            for child_link, child_link_copy in zip(itemToLoad.link.node.links, child_links_copy):
                child_item = DLGStandardItem(link=child_link)
                child_item.setData(itemToLoad.link.node.path(), _LINK_PARENT_NODE_PATH_ROLE)
                itemToLoad.appendRow(child_item)
                self.load_dlg_item_rec(child_item, child_link_copy)
        elif itemToLoad.link.node.links:
            self.set_item_future_expand(itemToLoad)
        else:
            orig = next(
                (item for item in self.link_to_items[itemToLoad.link] if not item.isDeleted() and item.data(_COPY_ROLE) is False),
                None,
            )
            itemToLoad.setData(orig is itemToLoad or orig is None, _COPY_ROLE)
        self.update_item_display_text(itemToLoad)

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
            print(f"<SDM> [manage_links_list scope] link.list_index: {link.list_index} --> {len(node.links) - 1}")
            link.list_index = len(node.links) - 1

        elif link in node.links:
            index = node.links.index(link)  # Find the index of the link to be removed
            node.links.remove(link)
            # Update list_index for remaining links
            for list_index, child_link in enumerate(node.links[index:], start=index):
                child_link.list_index = list_index
                print("<SDM> [manage_links_list scope] child_link.list_index: ", child_link.list_index)

    def set_item_future_expand(self, item: DLGStandardItem):
        """Creates a dummy item, with specific information that tells onItemExpanded how to expand when the user attempts to do so.

        This prevents infinite recursion while still giving the impression that multiple copies are in fact the same.
        """
        dummy_child = QStandardItem("Click this text to load.")
        dummy_child.setData(True, _DUMMY_ITEM)
        item.appendRow(dummy_child)  # pyright: ignore[reportArgumentType]
        item.setData(True, _COPY_ROLE)
        index = item.index()
        self.tree_view.collapse(index)

    def add_root_node(self):
        """Adds a root node to the dialog graph."""
        assert self.editor is not None
        new_node = DLGEntry()
        new_node.plot_index = -1
        new_link: DLGLink = DLGLink(new_node)
        new_link.node.list_index = self._get_new_node_list_index(new_link.node)
        new_item = DLGStandardItem(link=new_link)
        self.appendRow(new_item)
        self.update_item_display_text(new_item)
        print("<SDM> [_core_add_node scope] new_link: ", new_link)
        print("<SDM> [_core_add_node scope] new_link.list_index: ", new_link.list_index)
        print("<SDM> [_core_add_node scope] new_link.node.list_index: ", new_link.node.list_index)

    def add_child_to_item(self, parent_item: DLGStandardItem, link: DLGLink | None = None) -> DLGStandardItem:
        """Helper method to update the UI with the new link."""
        assert parent_item.link is not None
        if link is None:
            new_node = DLGEntry() if isinstance(parent_item.link.node, DLGReply) else DLGReply()
            new_node.plot_index = -1
            new_node.list_index = self._get_new_node_list_index(new_node)
            link = DLGLink(new_node)
        new_item = DLGStandardItem(link=link)
        parent_item.appendRow(new_item)
        self.update_item_display_text(new_item)
        self.update_item_display_text(parent_item)
        self.sync_item_copies(parent_item.link, parent_item)
        self.tree_view.expand(parent_item.index())
        return new_item

    def _link_core_nodes(self, target: DLGNode, source: DLGNode) -> DLGLink:
        """Helper method to add a source node to a target node."""
        new_link: DLGLink = DLGLink(source)
        print("<SDM> [_link_core_nodes scope] new_link: ", new_link)

        new_link.list_index = len(target.links)
        print("<SDM> [_link_core_nodes scope] new_link.list_index: ", new_link.list_index)

        target.links.append(new_link)
        return new_link

    def copy_link_and_node(self, link: DLGLink | None):
        if link is None:
            print("copy_link_and_node: no link passed to the function, nothing to copy.")
            return
        QApplication.clipboard().setText(json.dumps(link.to_dict()))

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
            new_index = self._get_new_node_list_index(pasted_link.node, all_entries, all_replies)
            print(f"<SDM> [_integrate_child_nodes scope] pastedNode.list_index: {pasted_link.node.list_index} --> {new_index}")
            pasted_link.node.list_index = new_index

        queue: deque[DLGNode] = deque([pasted_link.node])
        visited: set[DLGNode] = set()
        while queue:
            cur_node = queue.popleft()
            if cur_node in visited:
                continue
            visited.add(cur_node)
            if as_new_branches or cur_node not in self.node_to_items:
                new_index = self._get_new_node_list_index(cur_node, all_entries, all_replies)
                print(f"<SDM> [_integrate_child_nodes scope] cur_node.list_index: {cur_node.list_index} --> {new_index}")
                cur_node.list_index = new_index
            if as_new_branches:
                new_node_hash = hash(uuid.uuid4().hex)  # noqa: SLF001
                print(f"<SDM> [_integrate_child_nodes scope] cur_node._hash_cache: {cur_node._hash_cache} --> {new_node_hash}")  # noqa: SLF001
                cur_node._hash_cache = new_node_hash  # noqa: SLF001

            queue.extend([link.node for link in cur_node.links])

        if parent_item is None:
            parent_item = self
        new_item = DLGStandardItem(link=pasted_link)
        if row not in (-1, None, parent_item.rowCount()):
            parent_item.insertRow(row, new_item)
        else:
            parent_item.appendRow(new_item)
        self.ignoring_updates = True
        self.load_dlg_item_rec(new_item)
        self.ignoring_updates = False
        if isinstance(parent_item, DLGStandardItem):
            assert parent_item.link is not None
            self.update_item_display_text(parent_item)
            self.sync_item_copies(parent_item.link, parent_item)
        QTimer.singleShot(0, lambda *args: self.tree_view.expand(new_item.index()))
        self.layoutChanged.emit()
        self.tree_view.viewport().update()
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
            indices = {entry.list_index for entry in self.editor.core_dlg.all_entries()} if entry_indices is None else entry_indices
        elif isinstance(node, DLGReply):
            indices = {reply.list_index for reply in self.editor.core_dlg.all_replies()} if reply_indices is None else reply_indices
        else:
            raise TypeError(node.__class__.__name__)
        new_index = max(indices, default=-1) + 1
        print("<SDM> [_get_new_node_list_index scope] new_index: ", new_index)

        while new_index in indices:
            new_index += 1
        indices.add(new_index)
        return new_index

    def itemFromIndex(self, index: QModelIndex | QPersistentModelIndex) -> DLGStandardItem | None:
        item = super().itemFromIndex(index)
        if item is None:
            return None
        if not isinstance(item, DLGStandardItem):
            parent_item = item.parent()
            assert parent_item is not None
            self.tree_view.collapse(parent_item.index())
            self.tree_view.expand(parent_item.index())
        item = super().itemFromIndex(index)
        if item is None:
            return None
        assert isinstance(item, DLGStandardItem)
        return item

    def delete_node_everywhere(self, node: DLGNode):
        """Removes all occurrences of a node and all links to it from the model and self.editor.core_dlg."""
        assert self.editor is not None
        self.layoutAboutToBeChanged.emit()

        def remove_links_recursive(node_to_remove: DLGNode, parent_item: DLGStandardItem | DLGStandardItemModel):
            assert self.editor is not None
            for i in reversed(range(parent_item.rowCount())):
                child_item = parent_item.child(i, 0) if isinstance(parent_item, DLGStandardItem) else parent_item.item(i, 0)
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

    def delete_node(self, item: DLGStandardItem):
        """Deletes a node from the DLG and ui tree model."""
        parent_item: DLGStandardItem | None = item.parent()
        if parent_item is None:
            self.removeRow(item.row())
        else:
            parent_item.removeRow(item.row())
            assert parent_item.link is not None
            self.update_item_display_text(parent_item)
            self.sync_item_copies(parent_item.link, parent_item)

    def countItemRefs(self, link: DLGLink) -> int:
        """Counts the number of references to a node in the ui tree model."""
        return len(self.node_to_items[link.node])

    def update_item_display_text(self, item: DLGStandardItem, *, update_copies: bool = True):
        """Refreshes the item text and formatting based on the node data."""
        assert item.link is not None
        assert self.editor is not None
        color: QColor = QColor(100, 100, 100)
        prefix: Literal["E", "R", "N"] = "N"
        if isinstance(item.link.node, DLGEntry):
            color = QColor(255, 0, 0)  # if not item.is_copy() else QColor(210, 90, 90)
            prefix = "E"
            extra_node_info = ""
        elif isinstance(item.link.node, DLGReply):
            color = QColor(0, 0, 255)  # if not item.is_copy() else QColor(90, 90, 210)
            prefix = "R"
            extra_node_info = " This means the player will not see this reply as a choice, and will (continue) to next entry."

        text = str(item.link.node.text) if self.editor._installation is None else self.editor._installation.string(item.link.node.text, "")  # noqa: SLF001
        if not item.link.node.links:
            display_text = f"{text} <span style='color:{QColor(255, 127, 80).name()};'><b>[End Dialog]</b></span>"
        elif not text and not text.strip():
            if item.link.node.text.stringref == -1:
                display_text = "(continue)"
                tooltip_text = (
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
        list_prefix = f"<b>{prefix}{item.link.node.list_index}:</b> "
        item.setData(f'<span style="color:{color.name()}; font-size:{self.tree_view.get_text_size()}pt;">{list_prefix}{display_text}</span>', Qt.ItemDataRole.DisplayRole)

        hasConditional = item.link.active1 or item.link.active2
        hasScript = item.link.node.script1 or item.link.node.script2
        hasAnimation = item.link.node.camera_anim not in (-1, None) or bool(item.link.node.animations)
        hasSound = item.link.node.sound and item.link.node.sound_exists
        hasVoice = item.link.node.vo_resref
        isPlotOrQuestRelated = item.link.node.plot_index != -1 or item.link.node.quest_entry or item.link.node.quest

        icons: list[tuple[QStyle.StandardPixmap | str, Callable | None, str]] = []
        if hasConditional:
            icons.append((QStyle.StandardPixmap.SP_FileIcon, None, f"Conditional: <code>{hasConditional}</code>"))
        if hasScript:
            scriptIconPath = f":/images/icons/k{int(self.editor._installation.tsl) + 1}/script.png"  # noqa: SLF001
            icons.append((scriptIconPath, None, f"Script: {hasScript}"))
        if hasAnimation:
            animIconPath = f":/images/icons/k{int(self.editor._installation.tsl) + 1}/walkmesh.png"  # noqa: SLF001
            icons.append((animIconPath, None, "Item has animation data"))
        if isPlotOrQuestRelated:
            journalIconPath = f":/images/icons/k{int(self.editor._installation.tsl) + 1}/journal.png"  # noqa: SLF001
            icons.append((journalIconPath, None, "Item has plot/quest data"))
        if hasSound:
            soundIconPath = ":/images/common/sound-icon.png"
            icons.append(
                (
                    soundIconPath,
                    lambda: self.editor is not None
                    and item.link is not None
                    and self.editor.play_sound(str(item.link.node.sound), [SearchLocation.SOUND, SearchLocation.VOICE]),
                    "Item has Sound (click to play)",
                )
            )
        if hasVoice:
            voiceIconPath = ":/images/common/voice-icon.png"
            icons.append(
                (
                    voiceIconPath,
                    lambda: self.editor is not None
                    and item.link is not None
                    and self.editor.play_sound(str(item.link.node.vo_resref), [SearchLocation.SOUND, SearchLocation.VOICE]),
                    "Item has VO (click to play)",
                )
            )

        icon_data = {
            "icons": icons,
            "size": self.tree_view.get_text_size,
            "spacing": 5,
            "rows": len(icons),
            "columns": 1,
            "bottom_badge": {
                "text_callable": lambda *args: str(self.countItemRefs(item.link) if item.link else 0),
                "size_callable": self.tree_view.get_text_size,
                "tooltip_callable": lambda *args: f"{self.countItemRefs(item.link) if item.link else 0} references to this item",
                "action": lambda *args: self.editor is not None
                and self.editor.show_reference_dialog(
                    [this_item.ref_to_link for link in self.link_to_items for this_item in self.link_to_items[link] if item.link in this_item.link.node.links],
                    item.data(Qt.ItemDataRole.DisplayRole),
                ),  # pyright: ignore[reportOptionalMemberAccess]
            },
        }
        item.setData(icon_data, _ICONS_DATA_ROLE)
        item.setForeground(QBrush(color))
        if update_copies:
            items = self.node_to_items[item.link.node]
            for copiedItem in items:
                if copiedItem is item or not isinstance(copiedItem, DLGStandardItem):
                    continue
                self.update_item_display_text(copiedItem, update_copies=False)

    def is_copy(self, item: DLGStandardItem) -> bool:
        result = item.data(_COPY_ROLE)
        assert result is not None
        return result

    def is_loaded(self, item: DLGStandardItem) -> bool:
        if not item.is_copy():
            return True
        if not item.hasChildren():
            return True
        child = item.child(0, 0)
        if isinstance(child, DLGStandardItem):
            return True
        dummy = child.data(_DUMMY_ITEM)
        assert dummy is True
        return False

    def delete_selected_node(self):
        """Deletes the currently selected node from the tree."""
        if self.tree_view.selectedIndexes():
            index: QModelIndex = self.tree_view.selectedIndexes()[0]
            print(
                "<SDM> [delete_selected_node scope] self.tree_view.selectedIndexes()[0]: ",
                index,
                "row:",
                index.row(),
                "col:",
                index.column(),
            )

            item: DLGStandardItem | None = self.itemFromIndex(index)
            print(
                "<SDM> [delete_selected_node scope] item: ",
                item,
                "row:",
                "item is None" if item is None else item.row(),
                "col:",
                "item is None" if item is None else item.column(),
            )

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
        oldRow: int = item.row()
        print("<SDM> [shift_item scope] oldRow: ", oldRow)

        item_parent = item.parent()
        print("<SDM> [shift_item scope] item_parent: ", repr(item_parent))

        newRow: int = oldRow + amount
        print("<SDM> [shift_item scope] newRow: ", newRow)

        itemParentText = "" if item_parent is None else item_parent.text()

        print("Received item: '%s', row shift amount %s", repr(item), amount)
        print("Attempting to change row index for '%s' from %s to %s in parent '%s'", repr(item), oldRow, newRow, itemParentText)

        if newRow >= (item_parent or self).rowCount() or newRow < 0:
            RobustLogger().info("New row index '%s' out of bounds. Already at the start/end of the branch. Cancelling operation.", newRow)
            return

        # Get a strong reference so takeRow doesn't assume it's now orphaned.
        # It is expected this variable to be unused.
        if self.editor is None:
            raise RuntimeError("self.editor cannot be None in shift_item")
        _tempLink = self.editor.core_dlg.starters[oldRow] if item_parent is None else item_parent.link.node.links[oldRow]  # pyright: ignore[reportOptionalMemberAccess]
        item_to_move = (item_parent or self).takeRow(oldRow)[0]
        print("itemToMove '%s' taken from old position: '%s', moving to '%s'", repr(item_to_move), oldRow, newRow)
        (item_parent or self).insertRow(newRow, item_to_move)
        selection_model = self.tree_view.selectionModel()
        if selection_model is not None and not no_selection_update:
            selection_model.select(item_to_move.index(), QItemSelectionModel.SelectionFlag.ClearAndSelect)
            print("Selection updated to new index")

        item_parent = item_to_move.parent()
        print("<SDM> [shift_item scope] item_parent: ", item_parent)
        print("Item new parent after move: '%s'", item_parent.text() if item_parent else "Root")
        if isinstance(item_parent, DLGStandardItem):
            assert item_parent.link is not None
            self.update_item_display_text(item_parent)
            self.sync_item_copies(item_parent.link, item_parent)

        RobustLogger().info("Moved link from %s to %s", oldRow, newRow)
        self.layoutChanged.emit()

    def move_item_to_index(
        self,
        item: DLGStandardItem,
        new_index: int,
        target_parent_item: DLGStandardItem | None = None,
        *,
        noSelectionUpdate: bool = False,
    ):
        """Move an item to a specific index within the model."""
        assert self.editor is not None
        source_parent_item: DLGStandardItem | None = item.parent()
        if target_parent_item is source_parent_item and new_index == item.row():
            self.editor.blink_window()
            RobustLogger().info("Attempted to move item to the same position. Operation aborted.")
            return
        if (
            target_parent_item is not source_parent_item
            and target_parent_item is not None
            and source_parent_item is not None
            and target_parent_item.link is not None
            and source_parent_item.link is not None
            and target_parent_item.link.node == source_parent_item.link.node
        ):
            RobustLogger().warning("Cannot drag into a different copy.")
            self.editor.blink_window()
            return
        if target_parent_item is not None and not target_parent_item.is_loaded():
            self.load_dlg_item_rec(target_parent_item)

        if new_index < 0 or new_index > (target_parent_item or self).rowCount():
            RobustLogger().info("New row index %d out of bounds. Cancelling operation.", new_index)
            return
        oldRow: int = item.row()
        if source_parent_item is target_parent_item and new_index > oldRow:
            new_index -= 1
        _tempLink = self.editor.core_dlg.starters[oldRow] if source_parent_item is None else source_parent_item.link.node.links[oldRow]  # pyright: ignore[reportOptionalMemberAccess]
        itemToMove = (source_parent_item or self).takeRow(oldRow)[0]
        (target_parent_item or self).insertRow(new_index, itemToMove)
        selection_model = self.tree_view.selectionModel()
        if selection_model is not None and not noSelectionUpdate:
            selection_model.select(itemToMove.index(), QItemSelectionModel.SelectionFlag.ClearAndSelect)
            print("Selection updated to new index")

    def sync_item_copies(self, link: DLGLink, item_to_ignore: DLGStandardItem | None = None):
        items = self.node_to_items[link.node]
        print(f"Updating {len(items)} total item(s) containing node {link.node}")

        for item in items:
            if item is item_to_ignore:
                continue
            if not item.is_loaded():
                continue
            assert item.link is not None
            link_to_cur_item: dict[DLGLink, DLGStandardItem | None] = {link: None for link in item.link.node.links}

            self.ignoring_updates = True
            while item.rowCount() > 0:
                child_row = item.takeRow(0)
                child_item = child_row[0] if child_row else None
                if child_item is not None and child_item.link is not None:
                    link_to_cur_item[child_item.link] = child_item

            for iterated_link in item.link.node.links:
                child_item = link_to_cur_item[iterated_link]
                if child_item is None:
                    child_item = DLGStandardItem(link=iterated_link)
                    self.load_dlg_item_rec(child_item)
                item.appendRow(child_item)

            self.ignoring_updates = False


class DropPosition(Enum):
    ABOVE = "above"
    BELOW = "below"
    ON_TOP_OF = "on_top_of"
    INVALID = "invalid"


class DropTarget:
    def __init__(
        self,
        parent: QModelIndex,
        row: int,
        position: DropPosition,
        indicator_rect: QRect | None = None,
    ):
        self.parent_index: QModelIndex = parent
        self.row: int = row
        self.position: DropPosition = position
        self.indicator_rect: QRect = QRect() if indicator_rect is None else indicator_rect

    @classmethod
    def determine_drop_target(
        cls,
        view: DLGTreeView,
        pos: QPoint,
        leniency: float = 0.2,
    ) -> DropTarget:
        if pos.isNull():
            return cls(QModelIndex(), -1, DropPosition.INVALID, QRect())

        curIndex = view.indexAt(pos)
        if not curIndex.isValid() or curIndex.row() == -1:
            return cls(QModelIndex(), -1, DropPosition.INVALID, QRect())

        rect = view.visualRect(curIndex)
        item_height = rect.height()
        leniency_height = item_height * leniency
        upper_threshold = rect.top() + leniency_height
        lower_threshold = rect.bottom() - leniency_height

        if pos.y() <= upper_threshold:
            # Adjust for top edge of the index
            indicator_rect = QRect(rect.topLeft(), rect.topRight())
            # print(f"ABOVE cur index: {view.model().get_identifying_text(curIndex)}")
            return cls(curIndex.parent(), max(curIndex.row(), 0), DropPosition.ABOVE, indicator_rect)
        if pos.y() >= lower_threshold:
            # Adjust for bottom edge of the index
            indicator_rect = QRect(rect.bottomLeft(), rect.bottomRight())
            # print(f"BELOW cur index: {view.model().get_identifying_text(curIndex)}")
            return cls(curIndex.parent(), curIndex.row() + 1, DropPosition.BELOW, indicator_rect)

        # print(f"ON TOP OF cur index: {view.model().get_identifying_text(curIndex)}")
        return cls(curIndex, curIndex.row(), DropPosition.ON_TOP_OF, rect)

    def is_valid_drop(self, dragged_link: DLGLink, view: DLGTreeView) -> bool:
        if self.position is DropPosition.INVALID or self.row == -1:
            print("Drop operation invalid: target row is -1 or position is invalid.")
            return False

        view_model = view.model()
        assert view_model is not None, "view_model cannot be None"

        if self.parent_index.isValid():
            root_item_index = None
            parent_item = view_model.itemFromIndex(self.parent_index)
        else:
            root_item_index = view_model.index(self.row, 0)
            if not root_item_index.isValid():
                if self.position is DropPosition.BELOW:
                    above_test_index = view_model.index(min(0, self.row - 1), 0)
                    if above_test_index.isValid():
                        root_item_index = above_test_index
                else:
                    print(f"Root item at row '{self.row}' is invalid.")
                    return False
            parent_item = view_model.itemFromIndex(root_item_index)
        dragged_node = dragged_link.node
        assert parent_item is not None
        assert parent_item.link is not None
        node_types_match = view.both_nodes_same_type(dragged_node, parent_item.link.node)
        if self.position is DropPosition.ON_TOP_OF:
            node_types_match = not node_types_match

        if ((self.position is DropPosition.ON_TOP_OF) == node_types_match) == (root_item_index is not None):
            print(f"Drop operation invalid: {self.position.name} vs node type check.")
            return False

        print("Drop operation is valid.")
        return True


def install_immediate_tooltip(widget: QWidget, tooltip_text: str):
    widget.setToolTip(tooltip_text)
    widget.setMouseTracking(True)
    widget.event = lambda event: QToolTip.showText(cast(QHoverEvent, event).pos(), widget.toolTip(), widget)  # type: ignore[method-assign]


class DLGTreeView(RobustTreeView):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.setAnimated(True)
        self.setAutoExpandDelay(2000)
        self.setAutoScroll(False)
        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        self.setIndentation(20)
        self.setWordWrap(True)
        self.setAlternatingRowColors(False)
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.setAutoFillBackground(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.override_drop_in_view: bool = True  # set to False to use the new logic (not recommended - untested)
        self.editor: DLGEditor | None = None
        self.drop_indicator_rect: QRect = QRect()
        self.maxDragTextSize: int = 40
        self.num_links: int = 0
        self.num_unique_nodes: int = 0
        self.dragged_item: DLGStandardItem | None = None
        self.dragged_link: DLGLink | None = None
        self.drop_target: DropTarget | None = None
        self.start_pos: QPoint = QPoint()
        self.setMouseTracking(True)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDropIndicatorShown(False)  # We have our own.
        self.setDefaultDropAction(Qt.DropAction.MoveAction)

    def set_text_size(self, size: int):
        super().set_text_size(size)

    def emit_layout_changed(self):  # sourcery skip: remove-unreachable-code
        super().emit_layout_changed()

    def model(self) -> DLGStandardItemModel | None:
        model = super().model()
        if model is None:
            return None
        assert isinstance(model, DLGStandardItemModel), f"model was {model} of type {model.__class__.__name__}, expected DLGStandardItemModel"
        return model

    def paintEvent(self, event: QPaintEvent):
        super().paintEvent(event)
        if self.drop_indicator_rect.isNull():
            return

        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.drop_indicator_rect.topLeft().y() == self.drop_indicator_rect.bottomLeft().y():
            pen = QPen(Qt.GlobalColor.black, 1, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawLine(self.drop_indicator_rect.topLeft(), self.drop_indicator_rect.topRight())
        else:
            highlight_color = QColor(200, 200, 200, 120)
            painter.fillRect(self.drop_indicator_rect, highlight_color)

        painter.end()

    def drawBranchesOld(self, painter: QPainter, rect: QRect, index: QModelIndex):
        if not index.isValid():
            return
        ourModel = self.model()
        if ourModel is None:
            return
        item = ourModel.itemFromIndex(index)
        if item is None or item.link is None or self.editor is None:
            return

        depth, parent_index = 1, index.parent()
        while parent_index.isValid():
            depth += 1
            parent_index = parent_index.parent()

        indent_adjustment_amount = self.indentation() * depth - (self.indentation() / 2)
        start_x = int(rect.left() + indent_adjustment_amount)

        center = QPoint(start_x, rect.center().y())
        if not index.model().hasChildren(index):
            return

        arrow = QPolygon()

        if self.isExpanded(index):
            arrow.append(QPoint(center.x() - self.get_text_size() // 2, center.y() - self.get_text_size() // 3))
            arrow.append(QPoint(center.x() + self.get_text_size() // 2, center.y() - self.get_text_size() // 3))
            arrow.append(QPoint(center.x(), center.y() + self.get_text_size() // 2))
        else:
            arrow.append(QPoint(center.x() - self.get_text_size() // 3, center.y() - self.get_text_size() // 2))
            arrow.append(QPoint(center.x() + self.get_text_size() // 2, center.y()))
            arrow.append(QPoint(center.x() - self.get_text_size() // 3, center.y() + self.get_text_size() // 2))

        painter.save()
        try:  # sourcery skip: extract-method
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(50, 50, 50, 50))
            shadow_offset = 2
            shadow_poly = QPolygon([pt + QPoint(shadow_offset, shadow_offset) for pt in arrow])
            painter.drawPolygon(shadow_poly)
            painter.setBrush(QColor(80, 80, 80))
            painter.drawPolygon(arrow)
        finally:
            painter.restore()

    def keyPressEvent(self, event: QKeyEvent):
        print("<SDM> [DLGTreeView.keyPressEvent scope] key: %s", get_qt_key_string(event.key()))
        assert self.editor is not None
        self.editor.keyPressEvent(event, is_tree_view_call=True)
        super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.start_pos.isNull():
            self.start_pos = event.pos()
            print("<SDM> [mousePressEvent scope] self.start_pos: ", self.start_pos)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if (
            bool(event.buttons() & Qt.MouseButton.LeftButton)
            and not self.start_pos.isNull()
            and (event.pos() - self.start_pos).manhattanLength() >= QApplication.startDragDistance()
            and self.dragged_item is None
        ):
            ...
            # finally figured out how to get qt to do this part.
            # leave here in case we need again
            # if self.prepare_drag(self.indexAt(self.start_pos)):
            #    print(f"{self.__class__.__name__}.mouseMoveEvent picked up a drag")
            #    self.perform_drag()
            # else:
            #    self.resetDragState()
        super().mouseMoveEvent(event)
        index = self.indexAt(event.pos())
        if not index.isValid():
            return

        option = self.viewOptions() if qtpy.QT5 else self.styleOptionForIndex(index)
        option.rect = self.visualRect(index)

        delegate = self.itemDelegate(index)
        if isinstance(delegate, HTMLDelegate) and delegate.handleIconTooltips(event, option, index):
            return

    # region Tree Drag&Drop
    def create_drag_pixmap(self, dragged_item: DLGStandardItem) -> QPixmap:
        pixmap = QPixmap(250, 70)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(255, 255, 255, 200))
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawRoundedRect(QRect(0, 0, pixmap.width(), pixmap.height()), 10, 10)
        self.draw_drag_icons(painter, QPoint(30, 25), 15, QColor(255, 0, 0), f"{self.num_links}")
        self.draw_drag_icons(painter, QPoint(pixmap.width() - 30, 25), 15, QColor(0, 0, 255), f"{self.num_unique_nodes}")
        font = QFont("Arial", 11)
        painter.setFont(font)
        doc = QTextDocument()
        if not dragged_item.index().parent().isValid():
            color = "red"
            link_list_display = "StartingList"
            node_list_display = "EntryList"
        else:
            color = "blue"
            assert dragged_item.link is not None
            link_list_display: Literal["EntriesList", "RepliesList"] = "EntriesList" if isinstance(dragged_item.link.node, DLGEntry) else "RepliesList"
            node_list_display: Literal["EntryList", "ReplyList"] = "EntryList" if isinstance(dragged_item.link.node, DLGEntry) else "ReplyList"
        assert dragged_item.link is not None
        display_text: str = f"{link_list_display}\\{dragged_item.link.list_index} --> {node_list_display}\\{dragged_item.link.node.list_index}"

        html_content: str = f"""
        <div style="color: {color}; font-size: 12pt;">
            {display_text}
        </div>
        """
        doc.setHtml(html_content)
        doc.setDefaultFont(font)
        doc.setTextWidth(pixmap.width() - 20)
        painter.translate(10, 50)
        doc.drawContents(painter)
        painter.end()

        return pixmap

    def draw_drag_icons(
        self,
        painter: QPainter,
        center: QPoint,
        radius: int,
        color: QColor,
        text: str,
    ):
        gradient = QRadialGradient(center, radius) if qtpy.QT5 else QRadialGradient(QPointF(center), radius, QPointF(center))
        gradient.setColorAt(0, QColor(255, 255, 255, 200))
        gradient.setColorAt(0.5, color.lighter())
        gradient.setColorAt(1, color)
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, radius, radius)
        painter.setPen(QColor(0, 0, 0))
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        text_rect = QRect(center.x() - radius, center.y() - radius, radius * 2, radius * 2)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)

    def calculate_links_and_nodes(self, root_node: DLGNode) -> tuple[int, int]:
        queue: deque[DLGNode] = deque([root_node])
        seen_nodes: set[DLGNode] = set()
        self.num_links = 0
        self.num_unique_nodes = 0

        while queue:
            node: DLGNode = queue.popleft()
            assert node is not None
            if node in seen_nodes:
                continue
            seen_nodes.add(node)
            self.num_links += len(node.links)
            queue.extend(link.node for link in node.links)

        self.num_unique_nodes = len(seen_nodes)
        print("<SDM> [calculate_links_and_nodes scope] self.num_unique_nodes: ", self.num_unique_nodes)
        return self.num_links, self.num_unique_nodes

    def perform_drag(self):
        print("perform_drag: Post-initiate drag operation, call drag.exec()")
        assert self.dragged_item is not None
        dragged_index: QModelIndex = self.dragged_item.index()
        drag = QDrag(self)
        model: DLGStandardItemModel | None = self.model()
        assert model is not None
        drag.setMimeData(model.mime_data([dragged_index]))
        pixmap: QPixmap = self.create_drag_pixmap(self.dragged_item)
        drag.setPixmap(pixmap)
        item_top_left_global: QPoint = self.mapToGlobal(self.visualRect(dragged_index).topLeft())
        drag.setHotSpot(QPoint(pixmap.width() // 2, QCursor.pos().y() - item_top_left_global.y()))
        drag.exec(model.supportedDragActions())
        print("\nperformDrag: completely done")

    def prepare_drag(self, index: QModelIndex | None = None, event: QDragEnterEvent | QDragMoveEvent | QDropEvent | None = None) -> bool:
        print(f"{self.__class__.__name__}.\nprepareDrag(index={index}, event={event})")
        if self.dragged_item is not None:
            return True

        if event:
            return self._handle_drag_prepare_in_event(event)
        index = self.currentIndex() if index is None else index
        model: DLGStandardItemModel | None = self.model()
        assert isinstance(model, QStandardItemModel), f"model was not QStandardItemModel, was instead {model.__class__.__name__}: {model}"
        self.dragged_item = model.itemFromIndex(index)
        assert isinstance(
            self.dragged_item, DLGStandardItem
        ), f"model.itemFromIndex({index}(row={index.row()}, col={index.column()}) did not return a DLGStandardItem, was instead {self.dragged_item.__class__.__name__}: {self.dragged_item}"
        if not self.dragged_item or getattr(self.dragged_item, "link", None) is None:
            RobustLogger().warning(f"Ignoring dragged item: {self.dragged_item!r}")
            RobustLogger().warning("Above item does not contain DLGLink information\n")
            return False

        assert self.dragged_item is not None
        assert self.dragged_item.link is not None
        assert self.dragged_item.link.node is not None
        self.calculate_links_and_nodes(self.dragged_item.link.node)
        return True

    def _handle_drag_prepare_in_event(self, event: QDragEnterEvent | QDragMoveEvent | QDropEvent) -> bool:
        print("prepare_drag: check for mime_data")
        if not event.mime_data().hasFormat(QT_STANDARD_ITEM_FORMAT):
            print("prepare_drag: not our mime_data format.")
            return False
        model: DLGStandardItemModel | None = self.model()
        assert model is not None
        if id(event.source()) == id(model):
            print("drag is happening from exact QTreeView instance.")
            return True
        item_data: List[dict[Literal["row", "column", "roles"], Any]] = self.parse_mime_data(event.mime_data())
        if item_data[0]["roles"][_MODEL_INSTANCE_ID_ROLE] != id(model):
            print("prepare_drag: drag event started in another window.")
            return True
        print("prepare_drag: drag originated from some list widget.")
        deserialized_listwidget_link: DLGLink = DLGLink.from_dict(json.loads(item_data[0]["roles"][_DLG_MIME_DATA_ROLE]))
        temp_item = DLGStandardItem(link=deserialized_listwidget_link)
        # FIXME: the above QStandardItem is somehow deleted by qt BEFORE the next line?
        model.update_item_display_text(temp_item)
        self.dragged_item = model.link_to_items.setdefault(deserialized_listwidget_link, [temp_item])[0]
        assert self.dragged_item is not None
        assert self.dragged_item.link is not None
        self.calculate_links_and_nodes(self.dragged_item.link.node)
        return True

    def startDrag(self, supportedActions: Qt.DropAction):
        print("\nstartDrag: Initiate the drag operation, call self.prepare_drag")
        if not self.prepare_drag():
            print("startDrag called but prepare_drag returned False, resetting the drag state.")
            self.reset_drag_state()
            return
        mode = 2
        if mode == 1:
            super().startDrag(supportedActions)
        elif mode == 2:  # noqa: PLR2004
            self.perform_drag()
        print("startDrag done, call resetDragState")
        self.reset_drag_state()

    def dragEnterEvent(self, event: QDragEnterEvent):
        print(f"\ndragEnterEvent(event={event})")
        if not event.mime_data().hasFormat(QT_STANDARD_ITEM_FORMAT):
            print("dragEnterEvent mime_data does not match our format, invalidating.")
            self.set_invalid_drag_drop(event)
            return
        if not self.dragged_item:
            RobustLogger().warning("dragEnterEvent called before prepare_drag, rectifying.")
            if not self.prepare_drag(event=event):
                print("dragEnterEvent: prepare_drag returned False, resetting the drag state.")
                self.set_invalid_drag_drop(event)
                self.reset_drag_state()
                return
        self.set_valid_drag_drop(event)

    def dragMoveEvent(self, event: QDragMoveEvent):
        print(f"dragMoveEvent(event={event})")
        if not event.mime_data().hasFormat(QT_STANDARD_ITEM_FORMAT):
            self.set_invalid_drag_drop(event)
            super().dragMoveEvent(event)
            return

        print("<SDM> [dragMoveEvent scope], event mimedata matches our format.")
        if self.dragged_item is not None:
            assert self.dragged_item.link is not None
            self.dragged_link = self.dragged_item.link
        elif self.dragged_link is None:
            RobustLogger().error("dragMoveEvent called before prepare_drag. This is an error/oversight: dragEnterEvent should have picked this up first. rectifying now....")
            if not self.prepare_drag(event=event):
                self.set_invalid_drag_drop(event)
                super().dragMoveEvent(event)
                return
            self.dragged_link = self.get_dragged_link_from_mime_data(event.mime_data())
            if self.dragged_link is None:
                RobustLogger().error("Could not deserialize DLGLink from mime data despite it matching our format")
                self.set_invalid_drag_drop(event)
                super().dragMoveEvent(event)
                return

        delegate = self.itemDelegate()
        assert isinstance(delegate, HTMLDelegate), f"`delegate = self.itemDelegate()` {delegate.__class__.__name__}: {delegate}"
        if self.drop_target is not None:
            delegate.nudged_model_indexes.clear()

        pos: QPoint = event.pos()
        self.drop_target = DropTarget.determine_drop_target(self, pos)
        self.drop_indicator_rect = self.drop_target.indicator_rect
        if not self.drop_target.is_valid_drop(self.dragged_link, self):
            print(f"{self.__class__.__name__}.dragMoveEvent: Target at mouse position is not valid.")
            self.set_invalid_drag_drop(event)
            super().dragMoveEvent(event)
            self.unset_cursor()
            return
        model = self.model()
        assert model is not None, f"model = self.model() {model.__class__.__name__}: {model}"
        above_index = model.index(self.drop_target.row - 1, 0, self.drop_target.parent_index)
        hover_over_index = model.index(self.drop_target.row, 0, self.drop_target.parent_index)
        if (
            self.drop_target.position in (DropPosition.ABOVE, DropPosition.BELOW)
            and self.dragged_item is not None
            and (self.dragged_item.isDeleted() or hover_over_index is not self.dragged_item.index())
        ):
            delegate.nudgeItem(hover_over_index, 0, int(delegate.text_size / 2))
            delegate.nudgeItem(above_index, 0, int(-delegate.text_size / 2))

        self.set_valid_drag_drop(event)
        super().dragMoveEvent(event)

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        delegate = self.itemDelegate()
        assert isinstance(delegate, HTMLDelegate), f"`delegate = self.itemDelegate()` {delegate.__class__.__name__}: {delegate}"
        delegate.nudged_model_indexes.clear()
        self.unset_cursor()

    def dropEvent(self, event: QDropEvent):
        if self.override_drop_in_view:
            # Always set invalid so qt won't try to handle it past this function.
            self.set_invalid_drag_drop(event)
        if not event.mime_data().hasFormat(QT_STANDARD_ITEM_FORMAT):
            print("<SDM> [dropEvent scope] event does not match our format")
            self.reset_drag_state()
            return
        if self.drop_target is None:
            print("drop_target is None in dropEvent")
            self.reset_drag_state()
            return

        delegate = self.itemDelegate()
        assert isinstance(delegate, HTMLDelegate), f"`delegate = self.itemDelegate()` {delegate.__class__.__name__}: {delegate}"
        delegate.nudged_model_indexes.clear()
        model: DLGStandardItemModel | None = self.model()
        assert model is not None
        if self.drop_target.parent_index.isValid():
            dropParent: DLGStandardItem | None = model.itemFromIndex(self.drop_target.parent_index)
        else:
            dropParent = None

        if not self.is_item_from_current_model(event):
            if self.override_drop_in_view:
                print("<SDM> [dropEvent scope] not self.isItemFromCurrentModel(event), calling paste_item")
                dragged_link: DLGLink | None = self.get_dragged_link_from_mime_data(event.mime_data()) if self.dragged_link is None else self.dragged_link
                if dragged_link:
                    if not self.drop_target.is_valid_drop(dragged_link, self):
                        print("dropEvent: drop_target is not valid (for a paste_item)")
                        self.reset_drag_state()
                        return
                    new_index = self.drop_target.row
                    if self.drop_target.position is DropPosition.ON_TOP_OF:
                        new_index = 0
                    model.paste_item(dropParent, dragged_link, row=new_index, as_new_branches=False)
                    super().dropEvent(event)
                else:
                    print("<SDM> [dropEvent scope] could not call paste_item: dragged_node could not be deserialized from mime data.")
            super().dropEvent(event)
            self.reset_drag_state()
            return

        if not self.dragged_item:
            print("<SDM> [dropEvent scope] self.dragged_item is somehow None")
            self.reset_drag_state()
            return

        if not self.dragged_item.link:
            print("<SDM> [dropEvent scope] self.dragged_item.link reference is gone")
            self.reset_drag_state()
            return

        if not self.drop_target.is_valid_drop(self.dragged_item.link, self):
            print("dropEvent: self.drop_target is not valid (for a move_item_to_index)")
            self.reset_drag_state()
            return
        self.set_invalid_drag_drop(event)
        new_index = self.drop_target.row
        if self.drop_target.position is DropPosition.ON_TOP_OF:
            new_index = 0
        print("Dropping OUR TreeView item into another part of the treeview: call move_item_to_index")
        model.move_item_to_index(self.dragged_item, new_index, dropParent)
        super().dropEvent(event)
        parent_index_of_drop, dropped_at_row = self.drop_target.parent_index, self.drop_target.row
        if self.drop_target.position is DropPosition.BELOW:
            dropped_at_row = min(dropped_at_row - 1, 0)
        self.reset_drag_state()
        self.setAutoScroll(False)
        # self.setSelectionOnDrop(droppedAtRow, parentIndexOfDrop)
        QTimer.singleShot(0, lambda: self.set_selection_on_drop(dropped_at_row, parent_index_of_drop))

    def set_selection_on_drop(self, row: int, parent_index: QModelIndex):
        print(f"setSelectionOnDrop(row={row})")
        self.clearSelection()
        model = self.model()
        assert model is not None
        if not parent_index.isValid():
            print("setSelectionOnDrop: root item selected")
            droppedIndex = model.index(row, 0)
        else:
            droppedIndex = model.index(row, 0, parent_index)
        if not droppedIndex.isValid():
            print("setSelectionOnDrop droppedIndex invalid")
            return
        self.selectionModel().setCurrentIndex(droppedIndex, QItemSelectionModel.Select | QItemSelectionModel.Rows)
        self.viewport().update()
        self.setState(QAbstractItemView.State.DragSelectingState)
        QTimer.singleShot(0, lambda: self.setState(QAbstractItemView.State.NoState))
        QTimer.singleShot(0, lambda: self.viewport().update())

    def get_dragged_link_from_mime_data(self, mime_data: QMimeData) -> DLGLink | None:
        try:
            return DLGLink.from_dict(json.loads(self.parse_mime_data(mime_data)[0]["roles"][_DLG_MIME_DATA_ROLE]))
        except Exception:  # noqa: BLE001
            RobustLogger().exception("Failed to deserialize mime data node.")
        return None

    def is_item_from_current_model(self, event: QDropEvent) -> bool:
        if not isinstance(event.source(), DLGTreeView):
            print(f"isItemFromCurrentModel: Not our drag, QDropEvent.source() was of type '{event.source().__class__.__name__}'")
            return False
        return self.parse_mime_data(event.mime_data())[0]["roles"][_MODEL_INSTANCE_ID_ROLE] == id(self.model())

    @staticmethod
    def parse_mime_data(mime_data: QMimeData) -> list[dict[Literal["row", "column", "roles"], Any]]:
        items: list[dict[Literal["row", "column", "roles"], Any]] = []
        if mime_data.hasFormat(QT_STANDARD_ITEM_FORMAT):
            encoded_data: QByteArray = mime_data.data(QT_STANDARD_ITEM_FORMAT)
            stream = QDataStream(encoded_data, QIODevice.OpenModeFlag.ReadOnly)

            while not stream.atEnd():
                item_data: dict[Literal["row", "column", "roles"], Any] = {
                    "row": stream.readInt32(),
                    "column": stream.readInt32(),
                }
                roles: dict[int, Any] = {}
                for _ in range(stream.readInt32()):
                    role = stream.readInt32()
                    if role == Qt.ItemDataRole.DisplayRole:  # sourcery skip: merge-duplicate-blocks, remove-redundant-if
                        roles[role] = stream.readQString()
                    elif role == _DLG_MIME_DATA_ROLE:
                        roles[role] = stream.readQString()
                    elif role == _MODEL_INSTANCE_ID_ROLE:
                        roles[role] = stream.readInt64()
                    elif role == _LINK_PARENT_NODE_PATH_ROLE:
                        roles[role] = stream.readQString()
                    else:  # unknown role
                        roles[role] = stream.readQVariant()
                item_data["roles"] = roles
                items.append(item_data)

        return items

    @staticmethod
    def both_nodes_same_type(dragged_node: DLGNode, target_node: DLGNode) -> bool:
        return isinstance(dragged_node, DLGReply) and isinstance(target_node, DLGReply) or isinstance(dragged_node, DLGEntry) and isinstance(target_node, DLGEntry)

    def reset_drag_state(self):
        print("<SDM> [resetDragState scope]")
        self.start_pos = QPoint()
        self.dragged_item = None
        self.dragged_link = None
        self.drop_indicator_rect = QRect()
        self.drop_target = None
        self.unset_cursor()
        self.viewport().update()

    def set_invalid_drag_drop(
        self,
        event: QDropEvent | QDragEnterEvent | QDragMoveEvent,
    ):
        print("<SDM> [setInvalidDragDrop scope]")
        event.acceptProposedAction()
        event.setDropAction(Qt.DropAction.IgnoreAction)
        self.setCursor(Qt.CursorShape.ForbiddenCursor)
        self.viewport().update()
        QTimer.singleShot(0, lambda *args: self.setDragEnabled(True))

    def set_valid_drag_drop(
        self,
        event: QDropEvent | QDragEnterEvent | QDragMoveEvent,
    ):
        print("<SDM> [setValidDragDrop scope]")
        event.accept()
        event.setDropAction(
            Qt.DropAction.MoveAction if self.is_item_from_current_model(event) else Qt.DropAction.CopyAction
        )  # DropAction's are unused currently: the view is handling the drop.
        self.setCursor(Qt.CursorShape.ArrowCursor)

    # endregion


class DLGEditor(Editor):
    @property
    def editor(self) -> Self:
        return self

    @editor.setter
    def editor(self, value): ...
    def __init__(
        self,
        parent: QWidget | None = None,
        installation: HTInstallation | None = None,
    ):
        """Initializes the Dialog Editor window."""
        supported: list[ResourceType] = [ResourceType.DLG]
        super().__init__(parent, "Dialog Editor", "dialog", supported, supported, installation)
        self._installation: HTInstallation

        from toolset.uic.qtpy.editors.dlg import Ui_MainWindow

        self._copy: DLGLink | None = None
        self._focused: bool = False
        self._node_loaded_into_ui: bool = True
        self.core_dlg: DLG = DLG()
        self.undo_stack: QUndoStack = QUndoStack()  # TODO(th3w1zard1): move _processLink and _removeLinkFromItem logic to QUndoCommand classes once stable.

        self.ui: Ui_MainWindow = Ui_MainWindow()
        self.ui.setupUi(self)
        self.original_tooltips: dict[QWidget, str] = {}
        self.search_results: list[DLGStandardItem] = []
        self.current_result_index: int = 0
        self.whats_this_toggle: bool = False

        # Status Bar
        self.status_bar_anim_timer: QTimer = QTimer(self)
        self.tip_label: QLabel = QLabel()
        font = self.tip_label.font()
        font.setPointSize(10)
        self.tip_label.setFont(font)
        self.tips_start_from_right_side: bool = True
        self.statusBar().addWidget(self.tip_label)
        self.vo_id_edit_timer: QTimer = QTimer(self)

        self.setup_dlg_tree_mvc()
        self.setup_extra_widgets()
        self._setup_signals()
        self._setup_menus()
        if installation:
            self._setup_installation(installation)

        self.dialog_references = None
        self.reference_history: list[tuple[list[weakref.ref[DLGLink]], str]] = []
        self.current_reference_index = -1

        self.keys_down: set[int] = set()
        self.no_scroll_event_filter = NoScrollEventFilter(self)
        self.no_scroll_event_filter.setup_filter()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.tips: list[str] = [
            "Use the 'View' and 'Settings' menu to customize dlg editor settings. All of your changes will be saved for next time you load the editor.",
            "Tip: Drag and Drop is supported, even between different DLGs!",
            "Tip: Accidentally closed a side widget? Right click the Menu to reopen the dock panels.",
            "Tip: Hold CTRL and scroll to change the text size.",
            "Tip: Hold ALT and scroll to change the indentation.",
            "Tip: Hold CTRL+SHIFT and scroll to change the vertical spacing.",
            "Tip: 'Delete all references' will delete all EntriesList/RepliesList/StartingList links to the node, leaving it orphaned.",
            "Tip: Drag any item to the left dockpanel to pin it for easy access",
            "Tip: Orphaned Nodes will automatically be added to the top left list, drag back in to reintegrate.",
            "Tip: Use ':' after an attribute name in the search bar to filter items by specific properties, e.g., 'is_child:1'.",
            "Tip: Combine keywords with AND/OR in the search bar to refine your search results, such as 'script1:k_swg AND listener:PLAYER'",
            "Tip: Use double quotes to search for exact phrases in item descriptions, such as '\"urgent task\"'.",
            "Tip: Search for attributes without a value after ':' to find items where any non-null property exists, e.g., 'assigned:'.",
            "TIp: Double-click me to view all tips.",
        ]
        self.status_bar_anim_timer.start(30000)

        self.set_all_whats_this()
        self.setup_extra_tooltip_mode()
        self.new()

    def revert_tooltips(self):
        for widget, original_tooltip in self.original_tooltips.items():
            widget.setToolTip(original_tooltip)
        self.original_tooltips.clear()

    def showEvent(self, event: QShowEvent):
        super().showEvent(event)
        QTimer.singleShot(0, lambda *args: self.show_scrolling_tip())
        self.resize(self.width() + 200, self.height())
        self.resizeDocks(
            [
                self.ui.rightDockWidget,  # type: ignore[arg-type]
                self.left_dock_widget,
            ],
            [
                self.ui.rightDockWidget.minimumSizeHint().width(),
                self.left_dock_widget.minimumSizeHint().width(),
            ],
            Qt.Orientation.Horizontal,
        )
        self.resizeDocks(
            [
                self.ui.topDockWidget,  # type: ignore[arg-type]
            ],
            [
                self.ui.topDockWidget.minimumSizeHint().height(),
            ],
            Qt.Orientation.Vertical,
        )

    def show_scrolling_tip(self):
        tip = random.choice(self.tips)  # noqa: S311
        self.tip_label.setText(tip)
        self.tip_label.adjustSize()
        self.start_tooltip_ui_animation()

    def start_tooltip_ui_animation(self):
        if self.tips_start_from_right_side:
            start_x = -self.tip_label.width()
            end_x = self.statusBar().width()
        else:
            start_x = self.statusBar().width()
            end_x = -self.tip_label.width()

        self.tip_label.setGeometry(start_x, 0, self.tip_label.width(), 10)
        self.statusbar_animation = QPropertyAnimation(self.tip_label, b"geometry")
        self.statusbar_animation.setDuration(30000)
        self.statusbar_animation.setStartValue(QRect(start_x, 0, self.tip_label.width(), 10))
        self.statusbar_animation.setEndValue(QRect(end_x, 0, self.tip_label.width(), 10))
        if qtpy.API_NAME != "PySide6":  # disconnect() seems to have a different signature
            self.statusbar_animation.finished.connect(self.toggle_scrollbar_tip_direction)
        self.statusbar_animation.start()

    def toggle_scrollbar_tip_direction(self):
        self.tips_start_from_right_side = not self.tips_start_from_right_side
        self.statusbar_animation.disconnect()
        self.start_tooltip_ui_animation()

    def show_all_tips(self, checked: bool = False):  # noqa: FBT001, FBT002
        dialog = QDialog(self)
        dialog.setWindowTitle("All Tips")
        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit(dialog)
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Arial", 10))
        text_edit.setHtml("<ul>" + "".join(f"<li>{tip}</li>" for tip in self.tips) + "</ul>")
        layout.addWidget(text_edit)

        close_button = QPushButton("Close", dialog)
        close_button.clicked.connect(dialog.accept)
        close_button.setFont(QFont("Arial", 10))
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        fixed_width = 800  # Adjust this value as needed
        dialog.setFixedWidth(fixed_width)
        dialog.setSizeGripEnabled(True)
        dialog.exec()

    def setup_dlg_tree_mvc(self):
        self.model: DLGStandardItemModel = DLGStandardItemModel(self.ui.dialogTree)
        self.model.editor = self
        self.ui.dialogTree.editor = self
        self.ui.dialogTree.setModel(self.model)
        self.ui.dialogTree.setItemDelegate(HTMLDelegate(self.ui.dialogTree))
        self.verify_hierarchy(self.ui.dialogTree)
        self.verify_hierarchy(self.model)

    def verify_hierarchy(self, widget: QObject, level: int = 0):
        parent: QObject = widget
        while parent is not None:
            print(f"Level {level}: Checking parent {parent.__class__.__name__} with name {parent.objectName()}")
            if isinstance(parent, DLGEditor):
                print("DLGEditor found in the hierarchy.")
                return
            parent = parent.parent()
            level += 1
        raise RuntimeError(f"DLGEditor is not in the parent hierarchy, attempted {level} levels.")

    def _setup_signals(self):  # noqa: PLR0915
        """Connects UI signals to update node/link on change."""
        self.ui.actionReloadTree.triggered.connect(lambda: self._load_dlg(self.core_dlg))
        self.ui.dialogTree.expanded.connect(self.on_item_expanded)
        self.ui.dialogTree.customContextMenuRequested.connect(self.onTreeContextMenu)
        self.ui.dialogTree.doubleClicked.connect(
            lambda _e: self.editText(
                indexes=self.ui.dialogTree.selectionModel().selectedIndexes(),
                source_widget=self.ui.dialogTree,
            )
        )
        self.ui.dialogTree.selectionModel().selectionChanged.connect(self.on_selection_changed)

        self.go_to_button.clicked.connect(self.handle_go_to)
        self.find_button.clicked.connect(self.handle_find)
        self.back_button.clicked.connect(self.handle_back)
        self.find_input.returnPressed.connect(self.handle_find)

        # Debounce timer to delay a cpu-intensive task.
        self.vo_id_edit_timer.setSingleShot(True)
        self.vo_id_edit_timer.setInterval(500)
        self.vo_id_edit_timer.timeout.connect(self.populate_combobox_on_void_edit_finished)

        self.tip_label.mouseDoubleClickEvent = self.show_all_tips  # type: ignore[arg]
        self.tip_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tip_label.customContextMenuRequested.connect(self.show_all_tips)
        self.status_bar_anim_timer.timeout.connect(self.show_scrolling_tip)

        scriptTextEntryTooltip = """
A ResRef to a script, where the entry point is its <code>main()</code> function.
<br><br>
<i>Right-click for more options</i>
"""
        self.ui.script1Label.setToolTip(scriptTextEntryTooltip)
        self.ui.script2Label.setToolTip(scriptTextEntryTooltip)
        self.ui.script1ResrefEdit.setToolTip(scriptTextEntryTooltip)
        self.ui.script2ResrefEdit.setToolTip(scriptTextEntryTooltip)
        self.ui.script1ResrefEdit.currentTextChanged.connect(self.on_node_update)
        self.ui.script2ResrefEdit.currentTextChanged.connect(self.on_node_update)

        conditionalTextEntryTooltip = """
A ResRef to a script that defines the conditional function <code>int StartingConditional()</code>.
<br><br>
Should return 1 or 0, representing a boolean.
<br><br>
<i>Right-click for more options</i>
"""
        self.ui.conditional1Label.setToolTip(conditionalTextEntryTooltip)
        self.ui.conditional2Label.setToolTip(conditionalTextEntryTooltip)
        self.ui.condition1ResrefEdit.setToolTip(conditionalTextEntryTooltip)
        self.ui.condition2ResrefEdit.setToolTip(conditionalTextEntryTooltip)
        self.ui.condition1ResrefEdit.currentTextChanged.connect(self.on_node_update)
        self.ui.condition2ResrefEdit.currentTextChanged.connect(self.on_node_update)

        self.ui.soundComboBox.currentTextChanged.connect(self.on_node_update)
        self.ui.voiceComboBox.currentTextChanged.connect(self.on_node_update)

        self.ui.soundButton.clicked.connect(lambda: self.play_sound(self.ui.soundComboBox.currentText(), [SearchLocation.SOUND, SearchLocation.VOICE]) and None or None)
        self.ui.voiceButton.clicked.connect(lambda: self.play_sound(self.ui.voiceComboBox.currentText(), [SearchLocation.VOICE]) and None or None)

        self.ui.soundComboBox.set_button_delegate("Play", lambda text: self.play_sound(text, [SearchLocation.SOUND, SearchLocation.VOICE]))
        self.ui.voiceComboBox.set_button_delegate("Play", lambda text: self.play_sound(text, [SearchLocation.VOICE]))

        self.ui.speakerEdit.textEdited.connect(self.on_node_update)
        self.ui.listenerEdit.textEdited.connect(self.on_node_update)
        self.ui.script1Param1Spin.valueChanged.connect(self.on_node_update)
        self.ui.script1Param2Spin.valueChanged.connect(self.on_node_update)
        self.ui.script1Param3Spin.valueChanged.connect(self.on_node_update)
        self.ui.script1Param4Spin.valueChanged.connect(self.on_node_update)
        self.ui.script1Param5Spin.valueChanged.connect(self.on_node_update)
        self.ui.script1Param6Edit.textEdited.connect(self.on_node_update)
        self.ui.script2Param1Spin.valueChanged.connect(self.on_node_update)
        self.ui.script2Param2Spin.valueChanged.connect(self.on_node_update)
        self.ui.script2Param3Spin.valueChanged.connect(self.on_node_update)
        self.ui.script2Param4Spin.valueChanged.connect(self.on_node_update)
        self.ui.script2Param5Spin.valueChanged.connect(self.on_node_update)
        self.ui.script2Param6Edit.textEdited.connect(self.on_node_update)
        self.ui.condition1Param1Spin.valueChanged.connect(self.on_node_update)
        self.ui.condition1Param2Spin.valueChanged.connect(self.on_node_update)
        self.ui.condition1Param3Spin.valueChanged.connect(self.on_node_update)
        self.ui.condition1Param4Spin.valueChanged.connect(self.on_node_update)
        self.ui.condition1Param5Spin.valueChanged.connect(self.on_node_update)
        self.ui.condition1Param6Edit.textEdited.connect(self.on_node_update)
        self.ui.condition1NotCheckbox.stateChanged.connect(self.on_node_update)
        self.ui.condition2Param1Spin.valueChanged.connect(self.on_node_update)
        self.ui.condition2Param2Spin.valueChanged.connect(self.on_node_update)
        self.ui.condition2Param3Spin.valueChanged.connect(self.on_node_update)
        self.ui.condition2Param4Spin.valueChanged.connect(self.on_node_update)
        self.ui.condition2Param5Spin.valueChanged.connect(self.on_node_update)
        self.ui.condition2Param6Edit.textEdited.connect(self.on_node_update)
        self.ui.condition2NotCheckbox.stateChanged.connect(self.on_node_update)
        self.ui.emotionSelect.currentIndexChanged.connect(self.on_node_update)
        self.ui.expressionSelect.currentIndexChanged.connect(self.on_node_update)
        self.ui.soundCheckbox.toggled.connect(self.on_node_update)
        self.ui.soundCheckbox.toggled.connect(self.handle_sound_checked)
        self.ui.plotIndexCombo.currentIndexChanged.connect(self.on_node_update)
        self.ui.plotXpSpin.valueChanged.connect(self.on_node_update)
        self.ui.questEdit.textEdited.connect(self.on_node_update)
        self.ui.questEntrySpin.valueChanged.connect(self.on_node_update)
        self.ui.cameraIdSpin.valueChanged.connect(self.on_node_update)
        self.ui.cameraAngleSelect.currentIndexChanged.connect(self.on_node_update)
        self.ui.cameraEffectSelect.currentIndexChanged.connect(self.on_node_update)
        self.ui.nodeUnskippableCheckbox.toggled.connect(self.on_node_update)
        self.ui.nodeIdSpin.valueChanged.connect(self.on_node_update)
        self.ui.alienRaceNodeSpin.valueChanged.connect(self.on_node_update)
        self.ui.postProcSpin.valueChanged.connect(self.on_node_update)
        self.ui.delaySpin.valueChanged.connect(self.on_node_update)
        self.ui.logicSpin.valueChanged.connect(self.on_node_update)
        self.ui.waitFlagSpin.valueChanged.connect(self.on_node_update)
        self.ui.fadeTypeSpin.valueChanged.connect(self.on_node_update)
        self.ui.commentsEdit.textChanged.connect(self.on_node_update)

        self.ui.cameraAnimSpin.valueChanged.connect(self.on_node_update)
        self.ui.cameraAnimSpin.setMinimum(1200)
        self.ui.cameraAnimSpin.setMaximum(65535)

        self.ui.addStuntButton.clicked.connect(self.on_add_stunt_clicked)
        self.ui.removeStuntButton.clicked.connect(self.on_remove_stunt_clicked)
        self.ui.editStuntButton.clicked.connect(self.on_edit_stunt_clicked)

        self.ui.addAnimButton.clicked.connect(self.on_add_anim_clicked)
        self.ui.removeAnimButton.clicked.connect(self.on_remove_anim_clicked)
        self.ui.editAnimButton.clicked.connect(self.on_edit_anim_clicked)

        self.ui.cameraModelSelect.activated.connect(self.on_node_update)

    def setup_extra_widgets(self):
        self.setup_left_dock_widget()
        self.setup_menu_extras()

        # Go-to bar
        self.go_to_bar = QWidget(self)
        self.go_to_bar.setVisible(False)
        self.go_to_layout = QHBoxLayout(self.go_to_bar)
        self.go_to_input = QLineEdit(self.go_to_bar)
        self.go_to_button = QPushButton("Go", self.go_to_bar)
        self.go_to_layout.addWidget(self.go_to_input)
        self.go_to_layout.addWidget(self.go_to_button)
        self.ui.verticalLayout_main.insertWidget(0, self.go_to_bar)  # type: ignore[arg-type]

        # Find bar
        self.find_bar = QWidget(self)
        self.find_bar.setVisible(False)
        self.find_layout = QHBoxLayout(self.find_bar)
        self.find_input = QLineEdit(self.find_bar)
        self.find_button = QPushButton("", self.find_bar)
        self.find_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward))
        self.back_button = QPushButton("", self.find_bar)
        self.back_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack))
        self.results_label = QLabel(self.find_bar)
        self.find_layout.addWidget(self.find_input)
        self.find_layout.addWidget(self.back_button)
        self.find_layout.addWidget(self.find_button)
        self.find_layout.addWidget(self.results_label)
        self.ui.verticalLayout_main.insertWidget(0, self.find_bar)  # type: ignore[arg-type]
        self.setup_completer()

    def setup_completer(self):
        temp_entry = DLGEntry()
        temp_link = DLGLink(temp_entry)
        entry_attributes: set[str] = {
            attr[0] for attr in temp_entry.__dict__.items() if not attr[0].startswith("_") and not callable(attr[1]) and not isinstance(attr[1], list)
        }
        link_attributes: set[str] = {
            attr[0] for attr in temp_link.__dict__.items() if not attr[0].startswith("_") and not callable(attr[1]) and not isinstance(attr[1], (DLGEntry, DLGReply))
        }
        suggestions: list[str] = [f"{key}:" for key in [*entry_attributes, *link_attributes, "stringref", "strref"]]

        self.find_input_completer = QCompleter(suggestions, self.find_input)
        self.find_input_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.find_input_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.find_input_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.find_input_completer.setMaxVisibleItems(10)
        self.find_input.setCompleter(self.find_input_completer)

    def show_go_to_bar(self):
        self.go_to_bar.setVisible(True)
        self.go_to_input.setFocus()

    def show_find_bar(self):
        self.find_bar.setVisible(True)
        self.find_input.setFocus()

    def handle_go_to(self):
        input_text = self.go_to_input.text()
        self.custom_go_to_function(input_text)
        self.go_to_bar.setVisible(False)

    def handle_find(self):
        input_text = self.find_input.text()
        if not self.search_results or input_text != self.current_search_text:
            self.search_results = self.find_item_matching_display_text(input_text)
            self.current_search_text = input_text
            self.current_result_index = 0
        if not self.search_results:
            self.results_label.setText("No results found")
            return
        self.current_result_index = (self.current_result_index + 1) % len(self.search_results)
        self.highlight_result(self.search_results[self.current_result_index])
        self.update_results_label()

    def handle_back(self):
        if not self.search_results:
            return
        self.current_result_index = (self.current_result_index - 1 + len(self.search_results)) % len(self.search_results)
        self.highlight_result(self.search_results[self.current_result_index])
        self.update_results_label()

    def custom_go_to_function(self, input_text: str): ...  # TODO(th3w1zard1): allow quick jumps to EntryList/ReplyList nodes.

    def parse_query(self, input_text: str) -> list[tuple[str, str | None, Literal["AND", "OR", None]]]:
        pattern = r'("[^"]*"|\S+)'
        tokens: list[str] = re.findall(pattern, input_text)
        normalized_tokens: list[str] = []

        for token in tokens:
            if token.startswith('"') and token.endswith('"'):
                normalized_tokens.append(token[1:-1])
            else:
                normalized_tokens.extend(re.split(r"\s+", token))

        conditions: list[tuple[str, str | None, Literal["AND", "OR", None]]] = []
        operator: Literal["AND", "OR", None] = None
        i = 0

        while i < len(normalized_tokens):
            token = normalized_tokens[i].upper()
            if token in ("AND", "OR"):
                operator = token
                i += 1
                continue

            next_index = i + 1 if i + 1 < len(normalized_tokens) else None
            if ":" in normalized_tokens[i]:
                try:
                    key, sep, value = normalized_tokens[i].partition(":")
                    if value == "":
                        conditions.append((key.strip().lower(), None, operator))
                    else:
                        conditions.append((key.strip().lower(), value.strip().lower() if value else None, operator))
                finally:
                    operator = None
            elif next_index and normalized_tokens[next_index].upper() in ("AND", "OR"):
                conditions.append((normalized_tokens[i], "", operator))
                operator = None
            elif not next_index:
                conditions.append((normalized_tokens[i], "", operator))
                operator = None

            i += 1

        return conditions

    def find_item_matching_display_text(self, input_text: str) -> list[DLGStandardItem]:  # noqa: C901
        conditions = self.parse_query(input_text)
        matching_items: list[DLGStandardItem] = []

        def condition_matches(condition: tuple[str, str | None, Literal["AND", "OR", None]], item: DLGStandardItem) -> bool:  # noqa: C901
            key, value, operator = condition
            if not isinstance(item, DLGStandardItem) or item.link is None:
                return False
            sentinel = object()
            link_value = getattr(item.link, key, sentinel)
            node_value = getattr(item.link.node, key, sentinel)

            def check_value(attr_value: Any, search_value: str | None) -> bool:  # noqa: PLR0911
                if attr_value is sentinel:
                    return False
                if search_value is None:  # This indicates a truthiness check
                    return bool(attr_value) and attr_value not in (0xFFFFFFFF, -1)
                if isinstance(attr_value, int):
                    try:
                        return attr_value == int(search_value)
                    except ValueError:
                        return False
                elif isinstance(attr_value, bool):
                    if search_value.lower() in ["true", "1"]:
                        return attr_value is True
                    if search_value.lower() in ["false", "0"]:
                        return attr_value is False
                return search_value.lower() in str(attr_value).lower()

            if check_value(link_value, value) or check_value(node_value, value):
                return True
            if key in ("strref", "stringref"):
                if value is not None:
                    try:
                        return int(value.strip()) in item.link.node.text._substrings  # noqa: SLF001
                    except ValueError:
                        return False
                return bool(item.link.node.text)
            return False

        def evaluate_conditions(item: DLGStandardItem) -> bool:
            item_text = item.text().lower()
            if input_text.lower() in item_text:
                return True
            result = not conditions
            for condition in conditions:
                if condition[2] == "AND":
                    result = result and condition_matches(condition, item)
                elif condition[2] == "OR":
                    result = result or condition_matches(condition, item)
                else:
                    result = condition_matches(condition, item)
            return result

        def search_item(item: DLGStandardItem):
            if evaluate_conditions(item):
                matching_items.append(item)
            for row in range(item.rowCount()):
                child_item = cast(DLGStandardItem, item.child(row))
                if child_item:
                    search_item(child_item)

        def search_children(parent_item: DLGStandardItem):
            for row in range(parent_item.rowCount()):
                child_item = cast(DLGStandardItem, parent_item.child(row))
                search_item(child_item)
                search_children(child_item)

        search_children(cast(DLGStandardItem, self.model.invisibleRootItem()))
        return list({*matching_items})

    def highlight_result(self, item: DLGStandardItem):
        index = self.model.indexFromItem(item)
        parent = index.parent()
        while parent.isValid():
            self.ui.dialogTree.expand(parent)
            parent = parent.parent()
        self.ui.dialogTree.setCurrentIndex(index)
        self.ui.dialogTree.setFocus()
        selection_model = self.ui.dialogTree.selectionModel()
        selection_model.select(index, QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows)
        self.ui.dialogTree.scrollTo(index, QAbstractItemView.ScrollHint.PositionAtCenter)

    def update_results_label(self):
        self.results_label.setText(f"{self.current_result_index + 1} / {len(self.search_results)}")

    def setup_left_dock_widget(self):  # noqa: PLR0915
        self.left_dock_widget = QDockWidget("Orphaned Nodes and Pinned Items", self)
        self.leftDockWidgetContainer = QWidget()
        self.left_dock_layout = QVBoxLayout(self.leftDockWidgetContainer)

        # Orphaned Nodes List
        self.orphaned_nodes_list = DLGListWidget(self)
        self.orphaned_nodes_list.use_hover_text = False
        self.orphaned_nodes_list.setWordWrap(True)
        self.orphaned_nodes_list.setItemDelegate(HTMLDelegate(self.orphaned_nodes_list))
        # orphans is drag only. Someone please explain why there's a billion functions that need to be called to disable/enable drag/drop.
        self.orphaned_nodes_list.setDragEnabled(True)
        self.orphaned_nodes_list.setAcceptDrops(False)
        self.orphaned_nodes_list.viewport().setAcceptDrops(False)
        self.orphaned_nodes_list.setDropIndicatorShown(False)
        self.orphaned_nodes_list.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)

        # Pinned Items List
        self.pinned_items_list = DLGListWidget(self)
        self.pinned_items_list.setWordWrap(True)
        self.pinned_items_list.setItemDelegate(HTMLDelegate(self.pinned_items_list))
        self.pinned_items_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.pinned_items_list.setAcceptDrops(True)
        self.pinned_items_list.viewport().setAcceptDrops(True)
        self.pinned_items_list.setDragEnabled(True)
        self.pinned_items_list.setDropIndicatorShown(True)
        self.pinned_items_list.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)

        # Add both lists to the layout
        self.left_dock_layout.addWidget(QLabel("Orphaned Nodes"))
        self.left_dock_layout.addWidget(self.orphaned_nodes_list)
        self.left_dock_layout.addWidget(QLabel("Pinned Items"))
        self.left_dock_layout.addWidget(self.pinned_items_list)

        # Set the container as the widget for the dock
        self.left_dock_widget.setWidget(self.leftDockWidgetContainer)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.left_dock_widget)
        self.setStyleSheet(self.get_stylesheet())

        def mime_data(items: Iterable[DLGListWidgetItem], listWidget: DLGListWidget) -> QMimeData:
            mime_data = QMimeData()
            listwidget_data = QByteArray()

            stream_listwidget = QDataStream(listwidget_data, QIODevice.OpenModeFlag.WriteOnly)
            for item in items:
                index = listWidget.indexFromItem(item)
                stream_listwidget.writeInt32(index.row())
                stream_listwidget.writeInt32(index.column())
                stream_listwidget.writeInt32(3)
                stream_listwidget.writeInt32(int(Qt.ItemDataRole.DisplayRole))
                stream_listwidget.writeQString(item.data(Qt.ItemDataRole.DisplayRole))
                stream_listwidget.writeInt32(_DLG_MIME_DATA_ROLE)
                stream_listwidget.writeQString(json.dumps(item.link.to_dict()))
                stream_listwidget.writeInt32(_MODEL_INSTANCE_ID_ROLE)
                stream_listwidget.writeInt64(id(self))
                # stream_listwidget.writeInt32(int(_LINK_PARENT_NODE_PATH_ROLE))
                # stream_listwidget.writeQString(item.data(_LINK_PARENT_NODE_PATH_ROLE))

            mime_data.setData(QT_STANDARD_ITEM_FORMAT, listwidget_data)
            return mime_data

        def left_dock_widget_start_drag(supportedActions: Qt.DropAction, source_widget: DLGListWidget):
            selected_items: list[DLGListWidgetItem] = source_widget.selectedItems()
            if not selected_items:
                print("No selected items being dragged? (probably means someone JUST dropped into list)")
                return

            drag = QDrag(source_widget)
            drag.setMimeData(mime_data(selected_items, source_widget))
            drag.exec(supportedActions)

        self.orphaned_nodes_list.startDrag = lambda supportedActions: left_dock_widget_start_drag(supportedActions, self.orphaned_nodes_list)  # pyright: ignore[reportArgumentType]
        self.pinned_items_list.startDrag = lambda supportedActions: left_dock_widget_start_drag(supportedActions, self.pinned_items_list)  # pyright: ignore[reportArgumentType]

    def get_stylesheet(self) -> str:
        return """
        .link-container:hover .link-hover-text {
            display: block;
        }
        .link-container:hover .link-text {
            display: none;
        }
        .link-hover-text {
            display: none;
        }
        """

    def restore_orphaned_node(self, link: DLGLink):
        print(f"restoreOrphanedNodes(link={link})")
        selected_orphan_item = self.orphaned_nodes_list.currentItem()
        if selected_orphan_item is None:
            print("restoreOrphanedNodes: No left_dock_widget selected item.")
            self.blink_window()
            return
        selected_tree_indexes = self.ui.dialogTree.selectedIndexes()
        if not selected_tree_indexes or not selected_tree_indexes[0]:
            QMessageBox(QMessageBox.Icon.Information, "No target specified", "Select a position in the tree to insert this orphan at then try again.")
            return
        selected_tree_item: DLGStandardItem | None = cast(DLGStandardItem, self.model.itemFromIndex(selected_tree_indexes[0]))
        if selected_tree_item is None:
            print("restoreOrphanedNodes: selected index was not a standard item.")
            self.blink_window()
            return
        old_link_to_current_orphan: DLGLink = selected_orphan_item.link
        old_link_path = selected_orphan_item.data(_LINK_PARENT_NODE_PATH_ROLE)
        if isinstance(old_link_to_current_orphan.node, type(selected_tree_item.link.node)):  # pyright: ignore[reportOptionalMemberAccess]
            targetParent = selected_tree_item.parent()
            intended_link_list_index_row = selected_tree_item.row()
        else:
            targetParent = selected_tree_item
            intended_link_list_index_row = 0
        new_link_path = f"StartingList\\{intended_link_list_index_row}" if targetParent is None else targetParent.link.node.path()  # pyright: ignore[reportOptionalMemberAccess]
        link_parent_path, link_partial_path, linked_to_path = self.get_item_dlg_paths(selected_orphan_item)
        link_full_path = link_partial_path if link_parent_path is None else f"{link_parent_path}\\{link_partial_path}"
        confirm_message = f"The orphan '{linked_to_path}' (originally linked from {link_full_path}) will be newly linked from {new_link_path} with this action. Continue?"
        reply = QMessageBox.question(
            self, "Restore Orphaned Node", confirm_message, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            print(f"orphan '{linked_to_path}' (originally linked from {old_link_path}) is to be linked from {new_link_path}")
            item = self.model.insertLinkToParentAsItem(targetParent, DLGLink.from_dict(old_link_to_current_orphan.to_dict()), intended_link_list_index_row)
            self.model.load_dlg_item_rec(item)

            intended_link_list_index_row = self.orphaned_nodes_list.row(selected_orphan_item)
            self.orphaned_nodes_list.takeItem(intended_link_list_index_row)

    def delete_orphaned_node_permanently(self, link: DLGLink):
        print(f"delete_orphaned_node_permanently(link={link})")
        selected_orphan_item: DLGListWidgetItem | None = self.orphaned_nodes_list.currentItem()
        if selected_orphan_item is None:
            print("delete_orphaned_node_permanently: No left_dock_widget selected item.")
            self.blink_window()
            return
        self.orphaned_nodes_list.takeItem(self.orphaned_nodes_list.row(selected_orphan_item))

    def setup_menu_extras(self):
        self.viewMenu: QMenu = self.ui.menubar.addMenu("View")  # type: ignore[arg-type]
        self.settingsMenu: QMenu = self.ui.menubar.addMenu("Settings")  # type: ignore[arg-type]
        self.advancedMenu = self.viewMenu.addMenu("Advanced")
        self.refreshMenu = self.advancedMenu.addMenu("Refresh")
        self.treeMenu = self.refreshMenu.addMenu("TreeView")

        self.ui.menubar.addAction("Help").triggered.connect(self.show_all_tips)
        whats_this_action = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarContextHelpButton), "", self)
        whats_this_action.triggered.connect(QWhatsThis.enterWhatsThisMode)
        whats_this_action.setToolTip("Enter WhatsThis? mode.")
        self.ui.menubar.addAction(whats_this_action)  # pyright: ignore[reportArgumentType, reportCallIssue]

        # Common view settings
        self.ui.dialogTree._add_menu_action(
            self.viewMenu,
            "Uniform Row Heights",
            self.ui.dialogTree.uniformRowHeights,
            self.ui.dialogTree.setUniformRowHeights,
            settings_key="uniformRowHeights",
        )
        self.ui.dialogTree._add_menu_action(
            self.viewMenu,
            "Alternating Row Colors",
            self.ui.dialogTree.alternatingRowColors,
            self.ui.dialogTree.setAlternatingRowColors,
            settings_key="alternatingRowColors",
        )
        self.ui.dialogTree._add_menu_action(
            self.viewMenu,
            "Show/Hide Branch Connectors",
            self.ui.dialogTree.branch_connectors_drawn,
            self.ui.dialogTree.draw_connectors,
            settings_key="drawBranchConnectors",
        )
        self.ui.dialogTree._add_menu_action(
            self.viewMenu,
            "Expand Items on Double Click",
            self.ui.dialogTree.expandsOnDoubleClick,
            self.ui.dialogTree.setExpandsOnDoubleClick,
            settings_key="expandsOnDoubleClick",
        )
        self.ui.dialogTree._add_menu_action(
            self.viewMenu,
            "Tree Indentation",
            self.ui.dialogTree.indentation,
            self.ui.dialogTree.setIndentation,
            settings_key="indentation",
            param_type=int,
        )

        # Text and Icon Display Settings
        display_settings_menu = self.viewMenu.addMenu("Display Settings")
        self.ui.dialogTree._add_exclusive_menu_action(
            display_settings_menu,
            "Text Elide Mode",
            self.ui.dialogTree.textElideMode,
            lambda x: self.ui.dialogTree.setTextElideMode(Qt.TextElideMode(x)),
            options={
                "Elide Left": Qt.TextElideMode.ElideLeft,
                "Elide Right": Qt.TextElideMode.ElideRight,
                "Elide Middle": Qt.TextElideMode.ElideMiddle,
                "Elide None": Qt.TextElideMode.ElideNone,
            },
            settings_key="textElideMode",
        )
        self.ui.dialogTree._add_menu_action(
            display_settings_menu,
            "Font Size",
            self.ui.dialogTree.get_text_size,
            self.ui.dialogTree.set_text_size,
            settings_key="fontSize",
            param_type=int,
        )
        self.ui.dialogTree._add_menu_action(
            display_settings_menu,
            "Vertical Spacing",
            lambda: self.ui.dialogTree.itemDelegate().customVerticalSpacing,
            lambda x: self.ui.dialogTree.itemDelegate().setVerticalSpacing(x),
            settings_key="verticalSpacing",
            param_type=int,
        )

        # Focus and scrolling settings
        self.ui.dialogTree._add_exclusive_menu_action(
            self.settingsMenu,
            "Focus Policy",
            self.ui.dialogTree.focusPolicy,
            self.ui.dialogTree.setFocusPolicy,
            options={
                "No Focus": Qt.FocusPolicy.NoFocus,
                "Tab Focus": Qt.FocusPolicy.TabFocus,
                "Click Focus": Qt.FocusPolicy.ClickFocus,
                "Strong Focus": Qt.FocusPolicy.StrongFocus,
                "Wheel Focus": Qt.FocusPolicy.WheelFocus,
            },
            settings_key="focusPolicy",
        )
        self.ui.dialogTree._add_exclusive_menu_action(
            self.settingsMenu,
            "Horizontal Scroll Mode",
            self.ui.dialogTree.horizontalScrollMode,
            self.ui.dialogTree.setHorizontalScrollMode,
            options={
                "Scroll Per Item": QAbstractItemView.ScrollMode.ScrollPerItem,
                "Scroll Per Pixel": QAbstractItemView.ScrollMode.ScrollPerPixel,
            },
            settings_key="horizontalScrollMode",
        )
        self.ui.dialogTree._add_exclusive_menu_action(
            self.settingsMenu,
            "Vertical Scroll Mode",
            self.ui.dialogTree.verticalScrollMode,
            self.ui.dialogTree.setVerticalScrollMode,
            options={
                "Scroll Per Item": QAbstractItemView.ScrollMode.ScrollPerItem,
                "Scroll Per Pixel": QAbstractItemView.ScrollMode.ScrollPerPixel,
            },
            settings_key="verticalScrollMode",
        )
        self.ui.dialogTree._add_menu_action(
            self.settingsMenu,
            "Auto Scroll",
            self.ui.dialogTree.hasAutoScroll,
            self.ui.dialogTree.setAutoScroll,
            settings_key="autoScroll",
        )
        self.ui.dialogTree._add_menu_action(
            self.settingsMenu,
            "Auto Fill Background",
            self.autoFillBackground,
            self.setAutoFillBackground,
            settings_key="autoFillBackground",
        )

        self.ui.dialogTree._add_simple_action(self.advancedMenu, "Repaint", self.repaint)
        self.ui.dialogTree._add_simple_action(self.advancedMenu, "Update", self.update)
        self.ui.dialogTree._add_simple_action(self.advancedMenu, "Resize Column To Contents", lambda: self.ui.dialogTree.resizeColumnToContents(0))
        self.ui.dialogTree._add_simple_action(self.advancedMenu, "Update Geometries", self.ui.dialogTree.updateGeometries)
        self.ui.dialogTree._add_simple_action(self.advancedMenu, "Reset", self.ui.dialogTree.reset)

        self.ui.dialogTree._add_exclusive_menu_action(
            self.settingsMenu,
            "TSL Widget Handling",
            lambda: "Default",
            self.set_tsl_widget_handling,
            options={
                "Enable": "Enable",
                "Disable": "Disable",
                "Show": "Show",
                "Hide": "Hide",
                "Default": "Default",
            },
            settings_key="tsl_widget_handling",
        )

        # FIXME(th3w1zard1):
        # self._add_menu_action(settingsMenu, "Show/Hide Extra ToolTips on Hover",
        #                    lambda: self.whats_this_toggle,
        #                    lambda _value: self.setupExtraTooltipMode(),
        #                    settings_key="showVerboseHoverHints",
        #                    param_type=bool)

        # Advanced Menu: Miscellaneous advanced settings
        self.ui.dialogTree._add_simple_action(self.treeMenu, "Repaint", self.ui.dialogTree.repaint)
        self.ui.dialogTree._add_simple_action(self.treeMenu, "Update", self.ui.dialogTree.update)
        self.ui.dialogTree._add_simple_action(self.treeMenu, "Resize Column To Contents", lambda: self.ui.dialogTree.resizeColumnToContents(0))
        self.ui.dialogTree._add_simple_action(self.treeMenu, "Update Geometries", self.ui.dialogTree.updateGeometries)
        self.ui.dialogTree._add_simple_action(self.treeMenu, "Reset", self.ui.dialogTree.reset)

        listWidgetMenu = self.refreshMenu.addMenu("ListWidget")
        self.ui.dialogTree._add_simple_action(listWidgetMenu, "Repaint", self.pinned_items_list.repaint)
        self.ui.dialogTree._add_simple_action(listWidgetMenu, "Update", self.pinned_items_list.update)
        self.ui.dialogTree._add_simple_action(listWidgetMenu, "Reset Horizontal Scroll Mode", lambda: self.pinned_items_list.resetHorizontalScrollMode())
        self.ui.dialogTree._add_simple_action(listWidgetMenu, "Reset Vertical Scroll Mode", lambda: self.pinned_items_list.resetVerticalScrollMode())
        self.ui.dialogTree._add_simple_action(listWidgetMenu, "Update Geometries", self.pinned_items_list.updateGeometries)
        self.ui.dialogTree._add_simple_action(listWidgetMenu, "Reset", self.pinned_items_list.reset)
        self.ui.dialogTree._add_simple_action(listWidgetMenu, "layoutChanged", lambda: self.pinned_items_list.model().layoutChanged.emit())

        viewportMenu = self.refreshMenu.addMenu("Viewport")
        self.ui.dialogTree._add_simple_action(viewportMenu, "Repaint", self.ui.dialogTree.viewport().repaint)
        self.ui.dialogTree._add_simple_action(viewportMenu, "Update", self.ui.dialogTree.viewport().update)

        modelMenu = self.refreshMenu.addMenu("Model")
        self.ui.dialogTree._add_simple_action(modelMenu, "Emit Layout Changed", lambda: self.ui.dialogTree.model().layoutChanged.emit())  # pyright: ignore[reportOptionalMemberAccess]

        windowMenu = self.refreshMenu.addMenu("Window")
        self.ui.dialogTree._add_simple_action(windowMenu, "Repaint", lambda: self.repaint)

    def set_tsl_widget_handling(self, state: str):
        self.ui.dialogTree.set_setting("tsl_widget_handling", state)
        widgets_to_handle = [
            self.ui.script1Param1Spin,
            self.ui.script1Param2Spin,
            self.ui.script1Param3Spin,
            self.ui.script1Param4Spin,
            self.ui.script1Param5Spin,
            self.ui.script1Param6Edit,
            self.ui.script2ResrefEdit,
            self.ui.script2Param1Spin,
            self.ui.script2Param2Spin,
            self.ui.script2Param3Spin,
            self.ui.script2Param4Spin,
            self.ui.script2Param5Spin,
            self.ui.script2Param6Edit,
            self.ui.condition1Param1Spin,
            self.ui.condition1Param2Spin,
            self.ui.condition1Param3Spin,
            self.ui.condition1Param4Spin,
            self.ui.condition1Param5Spin,
            self.ui.condition1Param6Edit,
            self.ui.condition1NotCheckbox,
            self.ui.condition2ResrefEdit,
            self.ui.condition2Param1Spin,
            self.ui.condition2Param2Spin,
            self.ui.condition2Param3Spin,
            self.ui.condition2Param4Spin,
            self.ui.condition2Param5Spin,
            self.ui.condition2Param6Edit,
            self.ui.condition2NotCheckbox,
            self.ui.emotionSelect,
            self.ui.expressionSelect,
            self.ui.nodeUnskippableCheckbox,
            self.ui.nodeIdSpin,
            self.ui.alienRaceNodeSpin,
            self.ui.postProcSpin,
            self.ui.logicSpin,
            # labels
            self.ui.script2Label,
            self.ui.conditional2Label,
            self.ui.emotionLabel,
            self.ui.expressionLabel,
            self.ui.nodeIdLabel,
            self.ui.alienRaceNodeLabel,
            self.ui.postProcNodeLabel,
            self.ui.logicLabel,
        ]
        for widget in widgets_to_handle:
            self.handle_widget_with_tsl(widget, state)

    def handle_widget_with_tsl(self, widget: QWidget | QLabel, state: str):
        """Customizes widget behavior based on TSL state."""
        widget.show()
        widget.setEnabled(True)
        if state == "Default":
            widget.setEnabled(self._installation.tsl)
            if self._installation.tsl:
                widget.setToolTip("")
            else:
                widget.setToolTip("This widget is only available in KOTOR II.")
        elif state == "Disable":
            widget.setEnabled(False)
            widget.setToolTip("This widget is only available in KOTOR II.")
        elif state == "Enable":
            widget.setEnabled(True)
        elif state == "Hide":
            widget.hide()
        elif state == "Show":
            widget.show()

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        """Loads a dialogue file."""
        super().load(filepath, resref, restype, data)
        dlg: DLG = read_dlg(data)
        self._load_dlg(dlg)
        self.refresh_stunt_list()
        self.ui.onAbortCombo.set_combo_box_text(str(dlg.on_abort))
        self.ui.onEndEdit.set_combo_box_text(str(dlg.on_end))
        self.ui.voIdEdit.setText(dlg.vo_id)
        self.ui.voIdEdit.textChanged.connect(self.restart_void_edit_timer)
        self.ui.ambientTrackCombo.set_combo_box_text(str(dlg.ambient_track))
        self.ui.cameraModelSelect.set_combo_box_text(str(dlg.camera_model))
        self.ui.conversationSelect.setCurrentIndex(dlg.conversation_type.value)
        self.ui.computerSelect.setCurrentIndex(dlg.computer_type.value)
        self.ui.skippableCheckbox.setChecked(dlg.skippable)
        self.ui.skippableCheckbox.setToolTip("Should the user be allowed to skip dialog lines/cutscenes in this file?")
        self.ui.animatedCutCheckbox.setChecked(bool(dlg.animated_cut))
        self.ui.oldHitCheckbox.setChecked(dlg.old_hit_check)
        self.ui.oldHitCheckbox.setToolTip("It is likely OldHitCheck is a deprecated remnant of a previous game.")
        self.ui.unequipHandsCheckbox.setChecked(dlg.unequip_hands)
        self.ui.unequipAllCheckbox.setChecked(dlg.unequip_items)
        self.ui.entryDelaySpin.setValue(dlg.delay_entry)
        self.ui.replyDelaySpin.setValue(dlg.delay_reply)
        relevant_script_resnames = sorted({res.resname().lower() for res in self._installation.get_relevant_resources(ResourceType.NCS, self._filepath)})
        self.ui.script2ResrefEdit.populate_combo_box(relevant_script_resnames)
        self.ui.condition2ResrefEdit.populate_combo_box(relevant_script_resnames)
        self.ui.script1ResrefEdit.populate_combo_box(relevant_script_resnames)
        self.ui.condition1ResrefEdit.populate_combo_box(relevant_script_resnames)
        self.ui.onEndEdit.populate_combo_box(relevant_script_resnames)
        self.ui.onAbortCombo.populate_combo_box(relevant_script_resnames)
        relevant_model_resnames = sorted({res.resname().lower() for res in self._installation.get_relevant_resources(ResourceType.MDL, self._filepath)})
        self.ui.cameraModelSelect.populate_combo_box(relevant_model_resnames)

    def restart_void_edit_timer(self):
        """Restarts the timer whenever text is changed."""
        self.vo_id_edit_timer.stop()
        self.vo_id_edit_timer.start()

    def populate_combobox_on_void_edit_finished(self):
        """Slot to be called when text editing is finished.

        The editors the game devs themselves used probably did something like this
        """
        if not hasattr(self, "all_voices"):
            self.blink_window()
            return
        print("vo_id_edit_timer debounce finished, populate voiceComboBox with new VO_ID filter...")
        vo_id_lower = self.ui.voIdEdit.text().strip().lower()
        if vo_id_lower:
            filtered_voices = [voice for voice in self.all_voices if vo_id_lower in voice.lower()]
            print(f"filtered {len(self.all_voices)} voices to {len(filtered_voices)} by substring vo_id '{vo_id_lower}'")
        else:
            filtered_voices = self.all_voices
        self.ui.voiceComboBox.populate_combo_box(filtered_voices)

    def _load_dlg(self, dlg: DLG):
        """Loads a dialog tree into the UI view."""
        print("<SDM> [_load_dlg scope] GlobalSettings().selectedTheme: ", GlobalSettings().selectedTheme)
        if "(Light)" in GlobalSettings().selectedTheme or GlobalSettings().selectedTheme == "Native":
            self.ui.dialogTree.setStyleSheet("")
        self.orphaned_nodes_list.clear()
        self._focused = False
        self.core_dlg = dlg
        self.model.orig_to_orphan_copy = {
            weakref.ref(orig_link): copied_link
            for orig_link, copied_link in zip(
                dlg.starters,
                [DLGLink.from_dict(link.to_dict()) for link in dlg.starters],
            )
        }
        self.populate_combobox_on_void_edit_finished()

        self.model.reset_model()
        assert self.model.rowCount() == 0 and self.model.columnCount() == 0, "Model is not empty after resetModel() call!"  # noqa: PT018
        self.model.ignoring_updates = True
        for start in dlg.starters:  # descending order - matches what the game does.
            item = DLGStandardItem(link=start)
            self.model.appendRow(item)
            self.model.load_dlg_item_rec(item)
        self.orphaned_nodes_list.reset()
        self.orphaned_nodes_list.clear()
        self.orphaned_nodes_list.model().layoutChanged.emit()
        self.model.ignoring_updates = False
        assert self.model.rowCount() != 0 or not dlg.starters, "Model is empty after _load_dlg(dlg: DLG) call!"  # noqa: PT018
        assert self.model.node_to_items or not dlg.starters, "node_to_items is empty in the model somehow!"
        assert self.model.link_to_items or not dlg.starters, "link_to_items is empty in the model somehow!"

    def build(self) -> tuple[bytes, bytes]:
        """Builds a dialogue from UI components."""
        self.core_dlg.on_abort = ResRef(self.ui.onAbortCombo.currentText())
        print("<SDM> [build scope] self.editor.core_dlg.on_abort: ", self.core_dlg.on_abort)

        self.core_dlg.on_end = ResRef(self.ui.onEndEdit.currentText())
        print("<SDM> [build scope] self.editor.core_dlg.on_end: ", self.core_dlg.on_end)

        self.core_dlg.vo_id = self.ui.voIdEdit.text()
        print("<SDM> [build scope] self.editor.core_dlg.vo_id: ", self.core_dlg.vo_id)

        self.core_dlg.ambient_track = ResRef(self.ui.ambientTrackCombo.currentText())
        print("<SDM> [build scope] self.editor.core_dlg.ambient_track: ", self.core_dlg.ambient_track)

        self.core_dlg.camera_model = ResRef(self.ui.cameraModelSelect.currentText())
        print("<SDM> [build scope] self.editor.core_dlg.camera_model: ", self.core_dlg.camera_model)

        self.core_dlg.conversation_type = DLGConversationType(self.ui.conversationSelect.currentIndex())
        print("<SDM> [build scope] self.editor.core_dlg.conversation_type: ", self.core_dlg.conversation_type)

        self.core_dlg.computer_type = DLGComputerType(self.ui.computerSelect.currentIndex())
        print("<SDM> [build scope] self.editor.core_dlg.computer_type: ", self.core_dlg.computer_type)

        self.core_dlg.skippable = self.ui.skippableCheckbox.isChecked()
        print("<SDM> [build scope] self.editor.core_dlg.skippable: ", self.core_dlg.skippable)

        self.core_dlg.animated_cut = self.ui.animatedCutCheckbox.isChecked()
        print("<SDM> [build scope] self.editor.core_dlg.animated_cut: ", self.core_dlg.animated_cut)

        self.core_dlg.old_hit_check = self.ui.oldHitCheckbox.isChecked()
        print("<SDM> [build scope] self.editor.core_dlg.old_hit_check: ", self.core_dlg.old_hit_check)

        self.core_dlg.unequip_hands = self.ui.unequipHandsCheckbox.isChecked()
        print("<SDM> [build scope] self.editor.core_dlg.unequip_hands: ", self.core_dlg.unequip_hands)

        self.core_dlg.unequip_items = self.ui.unequipAllCheckbox.isChecked()
        print("<SDM> [build scope] self.editor.core_dlg.unequip_items: ", self.core_dlg.unequip_items)

        self.core_dlg.delay_entry = self.ui.entryDelaySpin.value()
        print("<SDM> [build scope] self.editor.core_dlg.delay_entry: ", self.core_dlg.delay_entry)

        self.core_dlg.delay_reply = self.ui.replyDelaySpin.value()
        print("<SDM> [build scope] self.editor.core_dlg.delay_reply: ", self.core_dlg.delay_reply)

        data = bytearray()
        gameToUse = self._installation.game()
        tsl_widget_handling_setting = DLGSettings().tsl_widget_handling("Default")
        if gameToUse.is_k1() and tsl_widget_handling_setting == "Enable":
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowTitle("Save TSL Fields?")
            msg_box.setText("You have tsl_widget_handling set to 'Enable', but your loaded installation set to K1. Would you like to save TSL fields?")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            response = msg_box.exec()
            if response == QMessageBox.StandardButton.Yes:
                gameToUse = Game.K2

        write_dlg(self.core_dlg, data, gameToUse)
        # dismantle_dlg(self.editor.core_dlg).compare(read_gff(data), log_func=print)  # use for debugging (don't forget to import)

        return data, b""

    def new(self):
        super().new()
        self._load_dlg(DLG())

    def _setup_installation(self, installation: HTInstallation):
        """Sets up the installation for the UI."""
        self._installation = installation
        print("<SDM> [_setup_installation scope] self._installation: ", self._installation)

        installation.setup_file_context_menu(self.ui.script1ResrefEdit, [ResourceType.NSS, ResourceType.NCS])
        if installation.game().is_k1():
            required: list[str] = [HTInstallation.TwoDA_VIDEO_EFFECTS, HTInstallation.TwoDA_DIALOG_ANIMS]

        else:
            required = [
                HTInstallation.TwoDA_EMOTIONS,
                HTInstallation.TwoDA_EXPRESSIONS,
                HTInstallation.TwoDA_VIDEO_EFFECTS,
                HTInstallation.TwoDA_DIALOG_ANIMS,
            ]
        installation.ht_batch_cache_2da(required)

        self.all_voices = sorted({res.resname() for res in installation._streamwaves}, key=str.lower)  # noqa: SLF001
        self.all_sounds = sorted({res.resname() for res in [*installation._streamwaves, *installation._streamsounds]}, key=str.lower)  # noqa: SLF001
        self.all_music = sorted({res.resname() for res in installation._streammusic}, key=str.lower)  # noqa: SLF001
        self._setupTSLEmotionsAndExpressions(installation)
        self.ui.soundComboBox.populate_combo_box(self.all_sounds)  # noqa: SLF001
        self.ui.ambientTrackCombo.populate_combo_box(self.all_music)
        self.ui.ambientTrackCombo.set_button_delegate("Play", lambda text: self.play_sound(text))
        installation.setup_file_context_menu(self.ui.cameraModelSelect, [ResourceType.MDL], [SearchLocation.CHITIN, SearchLocation.OVERRIDE])
        installation.setup_file_context_menu(self.ui.ambientTrackCombo, [ResourceType.WAV, ResourceType.MP3], [SearchLocation.MUSIC])
        installation.setup_file_context_menu(self.ui.soundComboBox, [ResourceType.WAV, ResourceType.MP3], [SearchLocation.SOUND, SearchLocation.VOICE])
        installation.setup_file_context_menu(self.ui.voiceComboBox, [ResourceType.WAV, ResourceType.MP3], [SearchLocation.VOICE])
        installation.setup_file_context_menu(self.ui.condition1ResrefEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onEndEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onAbortCombo, [ResourceType.NSS, ResourceType.NCS])

        videoEffects: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_VIDEO_EFFECTS)
        if videoEffects:
            self.ui.cameraEffectSelect.clear()
            self.ui.cameraEffectSelect.setPlaceholderText("[Unset]")
            self.ui.cameraEffectSelect.set_items(
                [label.replace("VIDEO_EFFECT_", "").replace("_", " ").title() for label in videoEffects.get_column("label")],
                cleanup_strings=False,
                ignore_blanks=True,
            )
            self.ui.cameraEffectSelect.set_context(videoEffects, installation, HTInstallation.TwoDA_VIDEO_EFFECTS)

        plot2DA: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_PLOT)
        if plot2DA:
            self.ui.plotIndexCombo.clear()
            self.ui.plotIndexCombo.addItem("[None]", -1)
            self.ui.plotIndexCombo.set_items(
                [cell.title() for cell in plot2DA.get_column("label")],
                cleanup_strings=True,
            )
            self.ui.plotIndexCombo.set_context(plot2DA, installation, HTInstallation.TwoDA_PLOT)

    def _setupTSLEmotionsAndExpressions(self, installation: HTInstallation):
        """Set up UI elements for TSL installation selection."""
        emotions: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_EMOTIONS)
        if emotions:
            self.ui.emotionSelect.clear()
            self.ui.emotionSelect.set_items(emotions.get_column("label"))
            self.ui.emotionSelect.set_context(emotions, installation, HTInstallation.TwoDA_EMOTIONS)

        expressions: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_EXPRESSIONS)
        if expressions:
            self.ui.expressionSelect.clear()
            self.ui.expressionSelect.set_items(expressions.get_column("label"))
            self.ui.expressionSelect.set_context(expressions, installation, HTInstallation.TwoDA_EXPRESSIONS)

        installation.setup_file_context_menu(self.ui.script2ResrefEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.condition2ResrefEdit, [ResourceType.NSS, ResourceType.NCS])

    def editText(
        self,
        e: QMouseEvent | QKeyEvent | None = None,
        indexes: list[QModelIndex] | None = None,
        source_widget: DLGListWidget | DLGTreeView | None = None,
    ):
        """Edits the text of the selected dialog node."""
        if not indexes:
            self.blink_window()
            return
        for index in indexes:
            model_to_use = source_widget if isinstance(source_widget, DLGListWidget) else index.model()
            assert isinstance(
                model_to_use,
                (DLGStandardItemModel, QStandardItemModel),
            ), f"`modelToUse = source_widget if isinstance(source_widget, DLGListWidget) else index.model()` {model_to_use.__class__}: {model_to_use} cannot be None."
            item: DLGStandardItem | QStandardItem | None = model_to_use.itemFromIndex(index)
            assert item is not None, "modelToUse.itemFromIndex(index) should not return None here in editText"
            assert isinstance(item, (DLGStandardItem, DLGListWidgetItem))
            if item.link is None:
                continue

            dialog = LocalizedStringDialog(self, self._installation, item.link.node.text)
            if dialog.exec():
                item.link.node.text = dialog.locstring
                if isinstance(item, DLGStandardItem):
                    self.model.update_item_display_text(item)
                elif isinstance(source_widget, DLGListWidget):
                    source_widget.update_item(item)

    def copy_path(self, node_or_link: DLGNode | DLGLink | None):
        """Copies the node path to the user's clipboard."""
        if node_or_link is None:
            return
        paths: list[PureWindowsPath] = self.core_dlg.find_paths(node_or_link)  # pyright: ignore[reportArgumentType]

        if not paths:
            print("No paths available.")
            self.blink_window()
            return

        if len(paths) == 1:
            path = str(paths[0])
            print("<SDM> [copyPath scope] path: ", path)

        else:
            path = "\n".join(f"  {i + 1}. {p}" for i, p in enumerate(paths))

        QApplication.clipboard().setText(path)

    def _check_clipboard_for_json_node(self):
        clipboard_text = QApplication.clipboard().text()

        try:
            node_data = json.loads(clipboard_text)
            if isinstance(node_data, dict) and "type" in node_data:
                self._copy = DLGLink.from_dict(node_data)
        except json.JSONDecodeError:
            ...
        except Exception:
            self._logger.exception("Invalid JSON node on clipboard.")

    def expand_to_root(self, item: DLGStandardItem):
        parent: DLGStandardItem | None = item.parent()
        while parent is not None:
            self.ui.dialogTree.expand(parent.index())
            parent = parent.parent()
            # print("<SDM> [expandToRoot scope] parent: ", parent)

    def jump_to_original(self, copied_item: DLGStandardItem):
        """Jumps to the original node of a copied item."""
        assert copied_item.link is not None
        source_node: DLGNode = copied_item.link.node
        items: deque[DLGStandardItem | QStandardItem | None] = deque([self.model.item(i, 0) for i in range(self.model.rowCount())])

        while items:
            item: DLGStandardItem | QStandardItem | None = items.popleft()
            if not isinstance(item, DLGStandardItem):
                continue
            if item.link is None:
                continue
            if item.link.node == source_node:
                self.expand_to_root(item)
                self.ui.dialogTree.setCurrentIndex(item.index())
                break
            items.extend([item.child(i, 0) for i in range(item.rowCount())])
        else:
            self._logger.error(f"Failed to find original node for node {source_node!r}")

    def focus_on_node(self, link: DLGLink | None) -> DLGStandardItem | None:
        """Focuses the dialog tree on a specific link node."""
        if link is None:
            return None
        if "(Light)" in GlobalSettings().selectedTheme or GlobalSettings().selectedTheme == "Native":
            self.ui.dialogTree.setStyleSheet("QTreeView { background: #FFFFEE; }")
        self.model.clear()
        self._focused = True

        item = DLGStandardItem(link=link)
        print("<SDM> [focus_on_node scope] item: ", item.text())

        self.model.layoutAboutToBeChanged.emit()
        self.model.ignoring_updates = True
        self.model.appendRow(item)
        self.model.load_dlg_item_rec(item)
        self.model.ignoring_updates = False
        self.model.layoutChanged.emit()
        return item

    def save_expanded_items(self) -> list[QModelIndex]:
        expanded_items: list[QModelIndex] = []

        def save_items_recursively(index: QModelIndex):
            if not index.isValid():
                self.blink_window()
                return
            if self.ui.dialogTree.isExpanded(index):
                expanded_items.append(index)
            for i in range(self.model.rowCount(index)):
                save_items_recursively(self.model.itemFromIndex(index).child(i, 0))

        save_items_recursively(self.ui.dialogTree.rootIndex())
        return expanded_items

    def save_scroll_position(self) -> int:
        return self.ui.dialogTree.verticalScrollBar().value()

    def save_selected_item(self) -> QModelIndex | None:
        selection_model: QItemSelectionModel = self.ui.dialogTree.selectionModel()
        if selection_model.hasSelection():
            return selection_model.currentIndex()
        return None

    def restore_expanded_items(self, expanded_items: list[QModelIndex]):
        for index in expanded_items:
            self.ui.dialogTree.setExpanded(index, True)

    def restore_scroll_position(self, scroll_position: int):
        self.ui.dialogTree.verticalScrollBar().setValue(scroll_position)

    def restore_selected_items(self, selected_index: QModelIndex):
        if selected_index and selected_index.isValid():
            self.ui.dialogTree.setCurrentIndex(selected_index)
            self.ui.dialogTree.scrollTo(selected_index)

    def update_tree_view(self):
        expanded_items: list[QModelIndex] = self.save_expanded_items()
        print("<SDM> [update_tree_view scope] expanded_items: %s", len(expanded_items))
        scroll_position = self.save_scroll_position()
        selected_index: QModelIndex | None = self.save_selected_item()
        self.ui.dialogTree.reset()

        self.restore_expanded_items(expanded_items)
        self.restore_scroll_position(scroll_position)
        self.restore_selected_items(selected_index)  # pyright: ignore[reportArgumentType]

    def on_list_context_menu(self, point: QPoint, source_widget: DLGListWidget):
        """Displays context menu for tree items."""
        item: DLGListWidgetItem | None = source_widget.itemAt(point)
        if item is not None:
            menu = self._get_link_context_menu(source_widget, item)
            menu.addSeparator()
            menu.addAction("Jump to in Tree").triggered.connect(lambda *args: self.jump_to_node(item.link))
            if source_widget is self.orphaned_nodes_list and self.ui.dialogTree.selectionModel().selectedIndexes():
                restore_action: QAction = menu.addAction("Insert Orphan at Selected Point")
                restore_action.triggered.connect(lambda: self.restore_orphaned_node(item.link))
                menu.addSeparator()
        else:
            menu = QMenu(source_widget)
        menu.addAction("Unpin").triggered.connect(lambda *args, item=item: source_widget.takeItem(source_widget.indexFromItem(item).row()))
        menu.addSeparator()
        menu.addAction("Clear List").triggered.connect(source_widget.clear)

        menu.popup(source_widget.viewport().mapToGlobal(point))

    def onTreeContextMenu(self, point: QPoint):
        """Displays context menu for tree items."""
        index: QModelIndex = self.ui.dialogTree.indexAt(point)
        item: DLGStandardItem | None = self.model.itemFromIndex(index)
        if item is not None:
            menu = self._get_link_context_menu(self.ui.dialogTree, item)
        else:
            menu = QMenu(self)
            if not self._focused:
                menu.addAction("Add Entry").triggered.connect(self.model.add_root_node)
            else:
                menu.addAction("Reset Tree").triggered.connect(lambda: self._load_dlg(self.core_dlg))
        menu.popup(self.ui.dialogTree.viewport().mapToGlobal(point))

    def set_expand_recursively(  # noqa: PLR0913
        self,
        item: DLGStandardItem,
        seen_nodes: set[DLGNode],
        *,
        expand: bool,
        maxdepth: int = 11,
        depth: int = 0,
        is_root: bool = True,
    ):
        """Recursively expand/collapse all children of the given item."""
        if depth > maxdepth >= 0:
            return
        item_index: QModelIndex = item.index()
        if not item_index.isValid():
            return
        if not isinstance(item, DLGStandardItem):
            return  # future expand dummy
        if item.link is None:
            return
        link: DLGLink = item.link
        if link.node in seen_nodes:
            return
        seen_nodes.add(link.node)
        if expand:
            self.ui.dialogTree.expand(item_index)
        elif not is_root:
            self.ui.dialogTree.collapse(item_index)
        for row in range(item.rowCount()):
            child_item: DLGStandardItem = cast(DLGStandardItem, item.child(row))
            if child_item is None:
                continue
            child_index: QModelIndex = child_item.index()
            if not child_index.isValid():
                continue
            self.set_expand_recursively(child_item, seen_nodes, expand=expand, maxdepth=maxdepth, depth=depth + 1, is_root=False)

    def _get_link_context_menu(
        self,
        source_widget: DLGListWidget | DLGTreeView,
        item: DLGStandardItem | DLGListWidgetItem,
    ) -> QMenu:
        """Sets context menu actions for a dialog tree item."""
        self._check_clipboard_for_json_node()
        not_an_orphan = source_widget is not self.orphaned_nodes_list
        is_list_widget_menu = isinstance(source_widget, DLGListWidget)
        assert item.link is not None
        node_type: Literal["Entry", "Reply"] = "Entry" if isinstance(item.link.node, DLGEntry) else "Reply"
        other_node_type: Literal["Entry", "Reply"] = "Reply" if isinstance(item.link.node, DLGEntry) else "Entry"

        menu = QMenu(source_widget)
        edit_text_action = menu.addAction("Edit Text")
        edit_text_action.triggered.connect(lambda *args: self.editText(indexes=source_widget.selectedIndexes(), source_widget=source_widget))
        edit_text_action.setShortcut(QKeySequence(Qt.Key.Key_Enter | Qt.Key.Key_Return) if qtpy.QT5 else QKeySequence(Qt.Key.Key_Enter, Qt.Key.Key_Return))
        focus_action = menu.addAction("Focus")

        focus_action.triggered.connect(lambda: self.focus_on_node(item.link))
        focus_action.setShortcut(QKeySequence(Qt.Key.Key_F))
        if not item.link.node.links:
            focus_action.setEnabled(False)
        focus_action.setVisible(not_an_orphan)

        # FIXME: current implementation requires all items to be loaded in order to find references, which is obviously impossible
        find_references_action = menu.addAction("Find References")
        find_references_action.triggered.connect(lambda: self.find_references(item))
        find_references_action.setVisible(not_an_orphan)

        # Expand/Collapse All Children Action (non copies)
        menu.addSeparator()
        expand_all_children_action: QAction = menu.addAction("Expand All Children")
        expand_all_children_action.triggered.connect(lambda: self.set_expand_recursively(item, set(), expand=True))  # pyright: ignore[reportArgumentType]
        expand_all_children_action.setShortcut(
            QKeySequence(Qt.Key.Key_Shift | Qt.Key.Key_Return)
            if qtpy.QT5
            else QKeySequence(
                Qt.Key.Key_Shift,
                Qt.Key.Key_Return,
            )
        )
        expand_all_children_action.setVisible(not is_list_widget_menu)
        collapse_all_children_action: QAction = menu.addAction("Collapse All Children")
        collapse_all_children_action.triggered.connect(lambda: self.set_expand_recursively(item, set(), expand=False))  # pyright: ignore[reportArgumentType]
        collapse_all_children_action.setShortcut(
            QKeySequence(Qt.Key.Key_Shift | Qt.Key.Key_Alt | Qt.Key.Key_Return)
            if qtpy.QT5
            else QKeySequence(
                Qt.Key.Key_Shift,
                Qt.Key.Key_Alt,
                Qt.Key.Key_Return,
            )
        )
        collapse_all_children_action.setVisible(not is_list_widget_menu)
        if not is_list_widget_menu:
            menu.addSeparator()

        # Play Actions
        play_menu: QMenu = menu.addMenu("Play")
        play_menu.mousePressEvent = lambda event: (print("play_menu.mousePressEvent"), self._play_node_sound(item.link.node), QMenu.mousePressEvent(play_menu, event))  # type: ignore[method-assign]
        play_sound_action: QAction = play_menu.addAction("Play Sound")
        play_sound_action.triggered.connect(lambda: self.play_sound("" if item.link is None else str(item.link.node.sound)) and None or None)
        play_voice_action: QAction = play_menu.addAction("Play Voice")
        play_voice_action.triggered.connect(lambda: self.play_sound("" if item.link is None else str(item.link.node.vo_resref)) and None or None)
        if not self.ui.soundComboBox.currentText().strip():
            play_sound_action.setEnabled(False)
        if not self.ui.voiceComboBox.currentText().strip():
            play_voice_action.setEnabled(False)
        if not self.ui.soundComboBox.currentText().strip() and not self.ui.voiceComboBox.currentText().strip():
            play_menu.setEnabled(False)
        menu.addSeparator()

        # Copy Actions
        copy_node_action: QAction = menu.addAction(f"Copy {node_type} to Clipboard")
        copy_node_action.triggered.connect(lambda: self.model.copy_link_and_node(item.link))
        copy_node_action.setShortcut(QKeySequence(Qt.Key.Key_Control | Qt.Key.Key_C) if qtpy.QT5 else QKeySequence(Qt.Key.Key_Control, Qt.Key.Key_C))
        copy_gff_path_action: QAction = menu.addAction("Copy GFF Path")
        copy_gff_path_action.triggered.connect(lambda: self.copy_path(None if item.link is None else item.link.node))
        copy_gff_path_action.setShortcut(
            QKeySequence(Qt.Key.Key_Control | Qt.Key.Key_Alt | Qt.Key.Key_C) if qtpy.QT5 else QKeySequence(Qt.Key.Key_Control, Qt.Key.Key_Alt, Qt.Key.Key_C)
        )
        copy_gff_path_action.setVisible(not_an_orphan)
        menu.addSeparator()

        # Paste Actions
        paste_link_action = menu.addAction(f"Paste {other_node_type} from Clipboard as Link")
        paste_new_action = menu.addAction(f"Paste {other_node_type} from Clipboard as Deep Copy")
        if self._copy is None:
            paste_link_action.setEnabled(False)
            paste_new_action.setEnabled(False)
        else:
            copied_node_type: Literal["Entry", "Reply"] = "Entry" if isinstance(self._copy.node, DLGEntry) else "Reply"
            paste_link_action.setText(f"Paste {copied_node_type} from Clipboard as Link")
            paste_new_action.setText(f"Paste {copied_node_type} from Clipboard as Deep Copy")
            if node_type == copied_node_type:
                paste_link_action.setEnabled(False)
                paste_new_action.setEnabled(False)

        paste_link_action.setShortcut(QKeySequence(Qt.KeyboardModifier.ControlModifier | Qt.Key.Key_V) if qtpy.QT5 else QKeySequence(Qt.Key.Key_Control, Qt.Key.Key_V))
        paste_link_action.triggered.connect(lambda: self.model.paste_item(item, as_new_branches=False))  # pyright: ignore[reportArgumentType]
        paste_link_action.setVisible(not is_list_widget_menu)
        paste_new_action.setShortcut(QKeySequence(Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier | Qt.Key.Key_V))
        paste_new_action.triggered.connect(
            lambda: self.model.paste_item(item, as_new_branches=True) if qtpy.QT5 else QKeySequence(Qt.Key.Key_Control, Qt.Key.Key_Alt, Qt.Key.Key_V)
        )  # pyright: ignore[reportArgumentType, reportCallIssue]
        paste_new_action.setVisible(not is_list_widget_menu)
        menu.addSeparator()

        # Add/Insert Actions
        add_node_action = menu.addAction(f"Add {other_node_type}")
        add_node_action.triggered.connect(lambda: self.model.add_child_to_item(item))  # pyright: ignore[reportArgumentType]
        add_node_action.setShortcut(Qt.Key.Key_Insert)
        add_node_action.setVisible(not is_list_widget_menu)
        if not is_list_widget_menu:
            menu.addSeparator()
        move_up_action = menu.addAction("Move Up")
        move_up_action.triggered.connect(lambda: self.model.shift_item(item, -1))  # pyright: ignore[reportArgumentType]
        move_up_action.setShortcut(QKeySequence(Qt.KeyboardModifier.ShiftModifier | Qt.Key.Key_Up))
        move_up_action.setVisible(not is_list_widget_menu)
        move_down_action = menu.addAction("Move Down")
        move_down_action.triggered.connect(lambda: self.model.shift_item(item, 1))  # pyright: ignore[reportArgumentType]
        move_down_action.setShortcut(QKeySequence(Qt.KeyboardModifier.ShiftModifier | Qt.Key.Key_Down))
        move_down_action.setVisible(not is_list_widget_menu)
        menu.addSeparator()

        # Remove/Delete Actions
        remove_link_action = menu.addAction(f"Remove {node_type}")
        remove_link_action.setShortcut(Qt.Key.Key_Delete)
        remove_link_action.triggered.connect(lambda: self.model.remove_link(item))  # pyright: ignore[reportArgumentType]
        remove_link_action.setVisible(not is_list_widget_menu)
        menu.addSeparator()

        use_large_delete_button = False  # seems to have broken the context menu after we introduced global QFont sizes.
        if use_large_delete_button:
            # Create a custom styled action for "Delete ALL References"
            delete_all_references_action = QWidgetAction(self)
            delete_all_references_widget = QWidget()
            layout = QHBoxLayout()
            delete_all_references_label = QLabel(f"Delete ALL References to {node_type}")
            delete_all_references_label.setStyleSheet("""
                QLabel {
                    color: red;
                    font-weight: bold;
                    font-size: 14px;
                }
                QLabel:hover {
                    background-color: #d3d3d3;
                }
            """)
            layout.addWidget(delete_all_references_label)
            layout.setContentsMargins(35, 10, 35, 10)
            delete_all_references_widget.setLayout(layout)
            delete_all_references_action.setDefaultWidget(delete_all_references_widget)
        else:
            delete_all_references_action = QAction(f"Delete ALL References to {node_type}", menu)  # type: ignore[assignment]
        delete_all_references_action.triggered.connect(lambda: self.model.delete_node_everywhere(item.link.node))  # pyright: ignore[reportOptionalMemberAccess]
        delete_all_references_action.setShortcut(QKeySequence(Qt.Key.Key_Control | Qt.KeyboardModifier.ShiftModifier | Qt.KeyboardModifier.Key_Delete))
        delete_all_references_action.setVisible(not_an_orphan)
        menu.addAction(delete_all_references_action)

        return menu

    def _play_node_sound(self, node: DLGEntry | DLGReply):
        if str(node.sound).strip():
            self.play_sound(str(node.sound).strip(), [SearchLocation.SOUND, SearchLocation.VOICE])
        elif str(node.vo_resref).strip():
            self.play_sound(str(node.vo_resref).strip(), [SearchLocation.VOICE])
        else:
            self.blink_window()

    def find_references(self, item: DLGStandardItem | DLGListWidgetItem):
        assert item.link is not None
        self.reference_history = self.reference_history[: self.current_reference_index + 1]
        item_html = item.data(Qt.ItemDataRole.DisplayRole)
        self.current_reference_index += 1
        references = [
            this_item.ref_to_link
            for link in self.model.link_to_items
            for this_item in self.model.link_to_items[link]
            if this_item.link is not None and item.link in this_item.link.node.links
        ]
        self.reference_history.append((references, item_html))
        self.show_reference_dialog(references, item_html)

    def get_item_dlg_paths(self, item: DLGStandardItem | DLGListWidgetItem) -> tuple[str, str, str]:
        link_parent_path = item.data(_LINK_PARENT_NODE_PATH_ROLE)
        assert item.link is not None
        link_path = item.link.partial_path(is_starter=item.link in self.core_dlg.starters)
        linked_to_path = item.link.node.path()
        return link_parent_path, link_path, linked_to_path

    def show_reference_dialog(self, references: list[weakref.ref[DLGLink]], item_html: str):
        if self.dialog_references is None:
            self.dialog_references = ReferenceChooserDialog(references, self, item_html)
            self.dialog_references.itemChosen.connect(self.on_reference_chosen)
        else:
            self.dialog_references.update_references(references, item_html)
        if self.dialog_references.isHidden():
            self.dialog_references.show()

    def on_reference_chosen(self, item: DLGListWidgetItem):
        link = item.link
        self.jump_to_node(link)

    def jump_to_node(self, link: DLGLink | None):
        if link is None:
            RobustLogger().error(f"{link!r} has already been deleted from the tree.")
            return
        if link not in self.model.link_to_items:
            RobustLogger().warning(f"Nowhere to jump - Either an orphan, or not loaded: {link}")
            return
        item: DLGStandardItem = self.model.link_to_items[link][0]
        self.highlight_result(item)

    def navigate_back(self):
        if self.current_reference_index > 0:
            self.current_reference_index -= 1
            references, item_html = self.reference_history[self.current_reference_index]
            self.show_reference_dialog(references, item_html)

    def navigate_forward(self):
        if self.current_reference_index < len(self.reference_history) - 1:
            self.current_reference_index += 1
            references, item_html = self.reference_history[self.current_reference_index]
            self.show_reference_dialog(references, item_html)

    # region Events
    def focusOutEvent(self, e: QFocusEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        self.keys_down.clear()  # Clears the set when focus is lost
        super().focusOutEvent(e)  # Ensures that the default handler is still executed
        print("dlgedit.focusOutEvent: clearing all keys/buttons held down.")

    def closeEvent(self, event: QCloseEvent):
        super().closeEvent(event)
        self.media_player.player.stop()
        if self.ui.rightDockWidget.isVisible():
            self.ui.rightDockWidget.close()
        if self.ui.topDockWidget.isVisible():
            self.ui.topDockWidget.close()
        # self.save_widget_states()

    def save_widget_states(self):
        """Iterates over child widgets and saves their geometry and state."""

    def _handle_shift_item_keybind(self, selected_index: QModelIndex, selected_item: DLGStandardItem, key: Qt.Key | int):
        # sourcery skip: extract-duplicate-method
        above_index: QModelIndex = self.ui.dialogTree.indexAbove(selected_index)
        below_index: QModelIndex = self.ui.dialogTree.indexBelow(selected_index)
        if self.keys_down in (
            {Qt.Key.Key_Shift, Qt.Key.Key_Up},
            {Qt.Key.Key_Shift, Qt.Key.Key_Up, Qt.Key.Key_Alt},
        ):
            print("<SDM> [_handle_shift_item_keybind scope] above_index: %s", above_index)

            if above_index.isValid():
                self.ui.dialogTree.setCurrentIndex(above_index)
            self.model.shift_item(selected_item, -1, no_selection_update=True)
        elif self.keys_down in (
            {Qt.Key.Key_Shift, Qt.Key.Key_Down},
            {Qt.Key.Key_Shift, Qt.Key.Key_Down, Qt.Key.Key_Alt},
        ):
            below_index: QModelIndex = self.ui.dialogTree.indexBelow(selected_index)

            if below_index.isValid():
                self.ui.dialogTree.setCurrentIndex(below_index)
            self.model.shift_item(selected_item, 1, no_selection_update=True)
        elif above_index.isValid() and key in (Qt.Key.Key_Up,) and not self.ui.dialogTree.visualRect(above_index).contains(self.ui.dialogTree.viewport().rect()):
            self.ui.dialogTree.scrollTo(above_index)
        elif below_index.isValid() and key in (Qt.Key.Key_Down,) and not self.ui.dialogTree.visualRect(below_index).contains(self.ui.dialogTree.viewport().rect()):
            self.ui.dialogTree.scrollTo(below_index)

    def keyPressEvent(
        self,
        event: QKeyEvent,
        *,
        is_tree_view_call: bool = False,
    ):  # sourcery skip: extract-duplicate-method
        if not is_tree_view_call:
            if not self.ui.dialogTree.hasFocus():
                print(f"<SDM> [DLGEditor.keyPressEvent scope] passthrough key {get_qt_key_string(event.key())}: dialogTree does not have focus.")
                super().keyPressEvent(event)
                return
            self.ui.dialogTree.keyPressEvent(event)  # this'll call us back immediately, just ensures we don't get called twice for the same event.
            return
        super().keyPressEvent(event)
        key = event.key()
        print("<SDM> [DLGEditor.keyPressEvent scope] key: ", get_qt_key_string(event.key()), f"held: {'+'.join([get_qt_key_string(k) for k in iter(self.keys_down)])}")
        selected_index: QModelIndex = self.ui.dialogTree.currentIndex()
        if not selected_index.isValid():
            return

        selected_item: DLGStandardItem | None = self.model.itemFromIndex(selected_index)
        if selected_item is None:
            if key == Qt.Key.Key_Insert:
                print("<SDM> [keyPressEvent scope insert1] key: ", key)
                self.model.add_root_node()
            return

        if event.isAutoRepeat() or key in self.keys_down:
            print("DLGEditor.keyPressEvent: event is auto repeat and/or key already in keys_down set.")
            if key in (Qt.Key.Key_Up, Qt.Key.Key_Down):
                self.keys_down.add(key)
                self._handle_shift_item_keybind(selected_index, selected_item, key)
            return  # Ignore auto-repeat events and prevent multiple executions on single key
        print(f"DLGEditor.keyPressEvent: {get_qt_key_string(key)}, held: {'+'.join([get_qt_key_string(k) for k in iter(self.keys_down)])}")
        assert selected_item.link is not None
        print("<SDM> [keyPressEvent scope] item.link.node: ", selected_item.link.node)

        if not self.keys_down:
            self.keys_down.add(key)
            if key in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
                self.model.remove_link(selected_item)
            elif key in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
                if self.ui.dialogTree.hasFocus():
                    self.editText(event, self.ui.dialogTree.selectedIndexes(), self.ui.dialogTree)
                elif self.orphaned_nodes_list.hasFocus():
                    self.editText(event, self.orphaned_nodes_list.selectedIndexes(), self.orphaned_nodes_list)
                elif self.pinned_items_list.hasFocus():
                    self.editText(event, self.pinned_items_list.selectedIndexes(), self.pinned_items_list)
                elif self.find_bar.hasFocus() or self.find_input.hasFocus():
                    self.handle_find()
            elif key == Qt.Key.Key_F:
                self.focus_on_node(selected_item.link)
            elif key == Qt.Key.Key_Insert:
                print("<SDM> [keyPressEvent insert2 scope] key: ", key)

                self.model.add_child_to_item(selected_item)
            elif key == Qt.Key.Key_P:
                print("<SDM> [keyPressEvent play scope] key: ", key)

                sound_resname = self.ui.soundComboBox.currentText().strip()
                voice_resname = self.ui.voiceComboBox.currentText().strip()
                if sound_resname:
                    self.play_sound(sound_resname, [SearchLocation.SOUND, SearchLocation.VOICE])
                elif voice_resname:
                    self.play_sound(voice_resname, [SearchLocation.VOICE])
                else:
                    self.blink_window()
            return

        self.keys_down.add(key)
        self._handle_shift_item_keybind(selected_index, selected_item, key)
        if self.keys_down in (
            {Qt.Key.Key_Shift, Qt.Key.Key_Return},
            {Qt.Key.Key_Shift, Qt.Key.Key_Enter},
        ):
            self.set_expand_recursively(selected_item, set(), expand=True)
        elif self.keys_down in (
            {Qt.Key.Key_Shift, Qt.Key.Key_Return, Qt.Key.Key_Alt},
            {Qt.Key.Key_Shift, Qt.Key.Key_Enter, Qt.Key.Key_Alt},
        ):
            self.set_expand_recursively(selected_item, set(), expand=False, maxdepth=-1)
        elif Qt.Key.Key_Control in self.keys_down or bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            if key == Qt.Key.Key_G:
                ...
                # self.show_go_to_bar()
            elif key == Qt.Key.Key_F:
                self.show_find_bar()
            elif Qt.Key.Key_C in self.keys_down:
                if Qt.Key.Key_Alt in self.keys_down:
                    self.copy_path(selected_item.link.node)
                else:
                    self.model.copy_link_and_node(selected_item.link)
            elif Qt.Key.Key_Enter in self.keys_down or Qt.Key.Key_Return in self.keys_down:
                if self.find_bar.hasFocus() or self.find_input.hasFocus():
                    self.handle_find()
                else:
                    self.jump_to_original(selected_item)
            elif Qt.Key.Key_V in self.keys_down:
                self._check_clipboard_for_json_node()
                if not self._copy:
                    print("No node/link copy in memory or on clipboard.")
                    self.blink_window()
                    return
                if self._copy.node.__class__ is selected_item.link.node.__class__:
                    print("Cannot paste link/node here.")
                    self.blink_window()
                    return
                if Qt.Key.Key_Alt in self.keys_down:
                    self.model.paste_item(selected_item, as_new_branches=True)
                else:
                    self.model.paste_item(selected_item, as_new_branches=False)
            elif Qt.Key.Key_Delete in self.keys_down:
                if Qt.Key.Key_Shift in self.keys_down:
                    self.model.delete_node_everywhere(selected_item.link.node)
                else:
                    self.model.delete_selected_node()

    def keyReleaseEvent(self, event: QKeyEvent):
        super().keyReleaseEvent(event)
        key = event.key()
        print("<SDM> [keyReleaseEvent scope] key: %s", key)

        if key in self.keys_down:
            self.keys_down.remove(key)
        print(f"DLGEditor.keyReleaseEvent: {get_qt_key_string(key)}, held: {'+'.join([get_qt_key_string(k) for k in iter(self.keys_down)])}")

    def update_labels(self):
        def update_label(label: QLabel, widget: QWidget, default_value: int | str | tuple[int | str, ...]):
            def is_default(value, default):
                return value in default if isinstance(default, tuple) else value == default

            font = label.font()
            if isinstance(widget, QCheckBox):
                is_default_value = is_default(widget.isChecked(), default_value)
            elif isinstance(widget, QLineEdit):
                is_default_value = is_default(widget.text(), default_value)
            elif isinstance(widget, QPlainTextEdit):
                is_default_value = is_default(widget.toPlainText(), default_value)
            elif isinstance(widget, QComboBox):
                if isinstance(default_value, tuple):
                    # Iterate through the tuple to check both currentText and currentIndex based on the type of each element in the tuple
                    is_default_value = False
                    for d in default_value:
                        if isinstance(d, int) and is_default(widget.currentIndex(), d):
                            is_default_value = True
                            break
                        if isinstance(d, str) and is_default(widget.currentText(), d):
                            is_default_value = True
                            break
                elif isinstance(default_value, int):
                    is_default_value = is_default(widget.currentIndex(), default_value)
                elif isinstance(default_value, str):
                    is_default_value = is_default(widget.currentText(), default_value)
                else:
                    is_default_value = False
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                is_default_value = is_default(widget.value(), default_value)
            else:
                is_default_value = False
            original_text = label.text().replace("* ", "", 1)  # Remove any existing asterisk
            if not is_default_value:
                label.setText(f"* {original_text}")
                font.setWeight(QFont.Weight.Bold if qtpy.QT6 else 65)  # pyright: ignore[reportArgumentType]
            else:
                label.setText(original_text)
                font.setWeight(QFont.Weight.Normal)
            label.setFont(font)

        update_label(self.ui.speakerEditLabel, self.ui.speakerEdit, "")  # type: ignore[arg-type]
        update_label(self.ui.questLabel, self.ui.questEdit, "")  # type: ignore[arg-type]
        update_label(self.ui.plotXpPercentLabel, self.ui.plotXpSpin, 1)  # type: ignore[arg-type]
        update_label(self.ui.plotIndexLabel, self.ui.plotIndexCombo, -1)  # type: ignore[arg-type]
        update_label(self.ui.questEntryLabel, self.ui.questEntrySpin, 0)  # type: ignore[arg-type]
        update_label(self.ui.listenerTagLabel, self.ui.listenerEdit, "")  # type: ignore[arg-type]
        update_label(self.ui.script1Label, self.ui.script1ResrefEdit, "")  # type: ignore[arg-type]
        update_label(self.ui.script2Label, self.ui.script2ResrefEdit, "")  # type: ignore[arg-type]
        update_label(self.ui.conditional1Label, self.ui.condition1ResrefEdit, "")  # type: ignore[arg-type]
        update_label(self.ui.conditional2Label, self.ui.condition2ResrefEdit, "")  # type: ignore[arg-type]
        update_label(self.ui.emotionLabel, self.ui.emotionSelect, "[Modded Entry #0]")  # type: ignore[arg-type]
        update_label(self.ui.expressionLabel, self.ui.expressionSelect, "[Modded Entry #0]")  # type: ignore[arg-type]
        update_label(self.ui.soundLabel, self.ui.soundComboBox, "")  # type: ignore[arg-type]
        update_label(self.ui.voiceLabel, self.ui.voiceComboBox, "")  # type: ignore[arg-type]
        update_label(self.ui.cameraIdLabel, self.ui.cameraIdSpin, -1)  # type: ignore[arg-type]
        update_label(self.ui.cameraAnimLabel, self.ui.cameraAnimSpin, (0, -1))  # type: ignore[arg-type]
        update_label(self.ui.cameraVidEffectLabel, self.ui.cameraEffectSelect, -1)  # type: ignore[arg-type]
        update_label(self.ui.cameraAngleLabel, self.ui.cameraAngleSelect, "Auto")  # type: ignore[arg-type]
        update_label(self.ui.nodeIdLabel, self.ui.nodeIdSpin, (0, -1))  # type: ignore[arg-type]
        update_label(self.ui.alienRaceNodeLabel, self.ui.alienRaceNodeSpin, 0)  # type: ignore[arg-type]
        update_label(self.ui.postProcNodeLabel, self.ui.postProcSpin, 0)  # type: ignore[arg-type]
        update_label(self.ui.delayNodeLabel, self.ui.delaySpin, (0, -1))  # type: ignore[arg-type]
        update_label(self.ui.logicLabel, self.ui.logicSpin, 0)  # type: ignore[arg-type]
        update_label(self.ui.waitFlagsLabel, self.ui.waitFlagSpin, 0)  # type: ignore[arg-type]
        update_label(self.ui.fadeTypeLabel, self.ui.fadeTypeSpin, 0)  # type: ignore[arg-type]

    def handle_sound_checked(self, *args):
        if not self._node_loaded_into_ui:
            return
        if not self.ui.soundCheckbox.isChecked():
            # self.ui.soundComboBox.setDisabled(True)
            # self.ui.voiceComboBox.setDisabled(True)
            self.ui.soundButton.setDisabled(True)
            self.ui.soundButton.setToolTip("Exists must be checked.")
            # self.ui.soundComboBox.setToolTip("Exists must be checked.")
            # self.ui.voiceComboBox.setToolTip("Exists must be checked.")
        else:
            # self.ui.soundComboBox.setEnabled(True)
            # self.ui.voiceComboBox.setEnabled(True)
            self.ui.voiceButton.setEnabled(True)
            self.ui.voiceButton.setToolTip("")
            # self.ui.soundComboBox.setToolTip("")
            # self.ui.voiceComboBox.setToolTip("")

    def set_all_whats_this(self):
        self.ui.actionNew.setWhatsThis("Create a new dialogue file")
        self.ui.actionOpen.setWhatsThis("Open an existing dialogue file")
        self.ui.actionSave.setWhatsThis("Save the current dialogue file")
        self.ui.actionSaveAs.setWhatsThis("Save the current dialogue file with a new name")
        self.ui.actionRevert.setWhatsThis("Revert changes to the last saved state")
        self.ui.actionExit.setWhatsThis("Exit the application")
        self.ui.actionReloadTree.setWhatsThis("Reload the dialogue tree")
        self.ui.actionUnfocus.setWhatsThis("Unfocus the current selection")

        self.ui.questEdit.setWhatsThis("Field: Quest\nType: String")
        self.ui.plotXpSpin.setWhatsThis("Field: PlotXPPercentage\nType: Float")
        self.ui.questEntryLabel.setWhatsThis("Label for Quest Entry field")
        self.ui.questLabel.setWhatsThis("Label for Quest field")
        self.ui.listenerEdit.setWhatsThis("Field: Listener\nType: String")
        self.ui.listenerTagLabel.setWhatsThis("Label for Listener Tag field")
        self.ui.speakerEdit.setWhatsThis("Field: Speaker\nType: String")
        self.ui.questEntrySpin.setWhatsThis("Field: QuestEntry\nType: Int32")
        self.ui.speakerEditLabel.setWhatsThis("Label for Speaker Tag field")
        self.ui.plotXpPercentLabel.setWhatsThis("Label for Plot XP Percentage field")
        self.ui.plotIndexLabel.setWhatsThis("Label for Plot Index field")
        self.ui.plotIndexCombo.setWhatsThis("Field: PlotIndex\nType: Int32")
        self.ui.commentsEdit.setWhatsThis("Field: Comment\nType: String")

        self.ui.script1Label.setWhatsThis("Field: Script1\nType: ResRef")
        self.ui.script2Label.setWhatsThis("Field: Script2\nType: ResRef")
        self.ui.script1ResrefEdit.setWhatsThis("Field: Script1\nType: ResRef")
        self.ui.script2ResrefEdit.setWhatsThis("Field: Script2\nType: ResRef")
        self.ui.script1Param1Spin.setWhatsThis("Field: ActionParam1\nType: Int32")
        self.ui.script1Param2Spin.setWhatsThis("Field: ActionParam2\nType: Int32")
        self.ui.script1Param3Spin.setWhatsThis("Field: ActionParam3\nType: Int32")
        self.ui.script1Param4Spin.setWhatsThis("Field: ActionParam4\nType: Int32")
        self.ui.script1Param5Spin.setWhatsThis("Field: ActionParam5\nType: Int32")
        self.ui.script1Param6Edit.setWhatsThis("Field: ActionParamStrA\nType: String")
        self.ui.script2Param1Spin.setWhatsThis("Field: ActionParam1b\nType: Int32")
        self.ui.script2Param2Spin.setWhatsThis("Field: ActionParam2b\nType: Int32")
        self.ui.script2Param3Spin.setWhatsThis("Field: ActionParam3b\nType: Int32")
        self.ui.script2Param4Spin.setWhatsThis("Field: ActionParam4b\nType: Int32")
        self.ui.script2Param5Spin.setWhatsThis("Field: ActionParam5b\nType: Int32")
        self.ui.script2Param6Edit.setWhatsThis("Field: ActionParamStrB\nType: String")
        self.ui.condition1ResrefEdit.setWhatsThis("Field: Active\nType: ResRef")
        self.ui.condition2ResrefEdit.setWhatsThis("Field: Active2\nType: ResRef")
        self.ui.condition1Param1Spin.setWhatsThis("Field: Param1\nType: Int32")
        self.ui.condition1Param2Spin.setWhatsThis("Field: Param2\nType: Int32")
        self.ui.condition1Param3Spin.setWhatsThis("Field: Param3\nType: Int32")
        self.ui.condition1Param4Spin.setWhatsThis("Field: Param4\nType: Int32")
        self.ui.condition1Param5Spin.setWhatsThis("Field: Param5\nType: Int32")
        self.ui.condition1Param6Edit.setWhatsThis("Field: ParamStrA\nType: String")
        self.ui.condition2Param1Spin.setWhatsThis("Field: Param1b\nType: Int32")
        self.ui.condition2Param2Spin.setWhatsThis("Field: Param2b\nType: Int32")
        self.ui.condition2Param3Spin.setWhatsThis("Field: Param3b\nType: Int32")
        self.ui.condition2Param4Spin.setWhatsThis("Field: Param4b\nType: Int32")
        self.ui.condition2Param5Spin.setWhatsThis("Field: Param5b\nType: Int32")
        self.ui.condition2Param6Edit.setWhatsThis("Field: ParamStrB\nType: String")
        self.ui.condition1NotCheckbox.setWhatsThis("Field: Not\nType: UInt8 (boolean)")
        self.ui.condition2NotCheckbox.setWhatsThis("Field: Not2\nType: UInt8 (boolean)")
        self.ui.emotionSelect.setWhatsThis("Field: Emotion\nType: Int32")
        self.ui.expressionSelect.setWhatsThis("Field: FacialAnim\nType: Int32")
        self.ui.nodeIdSpin.setWhatsThis("Field: NodeID\nType: Int32")
        self.ui.nodeUnskippableCheckbox.setWhatsThis("Field: NodeUnskippable\nType: UInt8 (boolean)")
        self.ui.postProcSpin.setWhatsThis("Field: PostProcNode\nType: Int32")
        self.ui.alienRaceNodeSpin.setWhatsThis("Field: AlienRaceNode\nType: Int32")
        self.ui.delaySpin.setWhatsThis("Field: Delay\nType: Int32")
        self.ui.logicSpin.setWhatsThis("Field: Logic\nType: Int32")
        self.ui.waitFlagSpin.setWhatsThis("Field: WaitFlags\nType: Int32")
        self.ui.fadeTypeSpin.setWhatsThis("Field: FadeType\nType: Int32")
        self.ui.soundCheckbox.setWhatsThis("Field: SoundExists\nType: UInt8 (boolean)")
        self.ui.soundComboBox.setWhatsThis("Field: Sound\nType: ResRef")
        self.ui.soundButton.setWhatsThis("Play the selected sound")
        self.ui.voiceComboBox.setWhatsThis("Field: VO_ResRef\nType: ResRef")
        self.ui.voiceButton.setWhatsThis("Play the selected voice")
        self.ui.addAnimButton.setWhatsThis("Add a new animation")
        self.ui.removeAnimButton.setWhatsThis("Remove the selected animation")
        self.ui.editAnimButton.setWhatsThis("Edit the selected animation")
        self.ui.animsList.setWhatsThis("List of current animations")
        self.ui.cameraIdSpin.setWhatsThis("Field: CameraID\nType: Int32")
        self.ui.cameraAnimSpin.setWhatsThis("Field: CameraAnimation\nType: Int32")
        self.ui.cameraAngleSelect.setWhatsThis("Field: CameraAngle\nType: Int32")
        self.ui.cameraEffectSelect.setWhatsThis("Field: CamVidEffect\nType: Int32")
        self.ui.cutsceneModelLabel.setWhatsThis("Label for Cutscene Model field")
        self.ui.addStuntButton.setWhatsThis("Add a new stunt")
        self.ui.removeStuntButton.setWhatsThis("Remove the selected stunt")
        self.ui.editStuntButton.setWhatsThis("Edit the selected stunt")
        self.ui.cameraModelSelect.setWhatsThis("Field: CameraModel\nType: ResRef")
        self.ui.oldHitCheckbox.setWhatsThis("Field: OldHitCheck\nType: UInt8 (boolean)")

        self.ui.ambientTrackCombo.setWhatsThis("Field: AmbientTrack\nType: ResRef")
        self.ui.voiceOverIDLabel.setWhatsThis("Label for Voiceover ID field")
        self.ui.computerTypeLabel.setWhatsThis("Label for Computer Type field")
        self.ui.conversationSelect.setWhatsThis("Field: ConversationType\nType: Int32")
        self.ui.computerSelect.setWhatsThis("Field: ComputerType\nType: Int32")
        self.ui.onAbortCombo.setWhatsThis("Field: EndConverAbort\nType: ResRef")
        self.ui.convoEndsScriptLabel.setWhatsThis("Label for Conversation Ends script")
        self.ui.convoTypeLabel.setWhatsThis("Label for Conversation Type field\nBIF dialogs use Type 3.")
        self.ui.ambientTrackLabel.setWhatsThis("Label for Ambient Track field")
        self.ui.convoAbortsScriptLabel.setWhatsThis("Label for Conversation Aborts script")
        self.ui.voIdEdit.setWhatsThis("Field: VO_ID\nType: String")
        self.ui.onEndEdit.setWhatsThis("Field: EndConversation\nType: ResRef")
        self.ui.delayEntryLabel.setWhatsThis("Label for Delay Entry field")
        self.ui.replyDelaySpin.setWhatsThis("Field: DelayReply\nType: Int32")
        self.ui.delayReplyLabel.setWhatsThis("Label for Delay Reply field")
        self.ui.entryDelaySpin.setWhatsThis("Field: DelayEntry\nType: Int32")
        self.ui.skippableCheckbox.setWhatsThis("Field: Skippable\nType: UInt8 (boolean)")
        self.ui.unequipHandsCheckbox.setWhatsThis("Field: UnequipHItem\nType: UInt8 (boolean)")
        self.ui.unequipAllCheckbox.setWhatsThis("Field: UnequipItems\nType: UInt8 (boolean)")
        self.ui.animatedCutCheckbox.setWhatsThis("Field: AnimatedCut\nType: Int32")

    def setup_extra_tooltip_mode(self, widget: QWidget | None = None):
        if widget is None:
            widget = self
        for child in widget.findChildren(QWidget):
            whats_this_text = child.whatsThis()
            if not whats_this_text or not whats_this_text.strip():
                continue
            if "<br>" in child.toolTip():  # FIXME: existing html tooltips for some reason become plaintext when setToolTip is called more than once.
                continue
            if child not in self.original_tooltips:
                self.original_tooltips[child] = child.toolTip()
            original_tooltip = self.original_tooltips[child]
            new_tooltip = whats_this_text
            if original_tooltip and original_tooltip.strip():
                new_tooltip += f"\n\n{original_tooltip}"

            child.setToolTip(new_tooltip)

    def on_selection_changed(self, selection: QItemSelection):
        """Updates UI fields based on selected dialog node."""
        if self.model.ignoring_updates:
            return
        self._node_loaded_into_ui = False
        selection_indices = selection.indexes()
        print(
            "<SDM> [onSelectionChanged scope] selectionIndices:\n",
            ",\n".join([self.model.itemFromIndex(index).text() for index in selection_indices if self.model.itemFromIndex(index) is not None]),
        )  # pyright: ignore[reportOptionalMemberAccess]
        if not selection_indices:
            return
        for index in selection_indices:
            item: DLGStandardItem | None = self.model.itemFromIndex(index)

            assert item is not None
            assert item.link is not None
            self.ui.condition1ResrefEdit.set_combo_box_text(str(item.link.active1))
            self.ui.condition1Param1Spin.setValue(item.link.active1_param1)
            self.ui.condition1Param2Spin.setValue(item.link.active1_param2)
            self.ui.condition1Param3Spin.setValue(item.link.active1_param3)
            self.ui.condition1Param4Spin.setValue(item.link.active1_param4)
            self.ui.condition1Param5Spin.setValue(item.link.active1_param5)
            self.ui.condition1Param6Edit.setText(item.link.active1_param6)
            self.ui.condition1NotCheckbox.setChecked(item.link.active1_not)
            self.ui.condition2ResrefEdit.set_combo_box_text(str(item.link.active2))
            self.ui.condition2Param1Spin.setValue(item.link.active2_param1)
            self.ui.condition2Param2Spin.setValue(item.link.active2_param2)
            self.ui.condition2Param3Spin.setValue(item.link.active2_param3)
            self.ui.condition2Param4Spin.setValue(item.link.active2_param4)
            self.ui.condition2Param5Spin.setValue(item.link.active2_param5)
            self.ui.condition2Param6Edit.setText(item.link.active2_param6)
            self.ui.condition2NotCheckbox.setChecked(item.link.active2_not)

            if isinstance(item.link.node, DLGEntry):
                self.ui.speakerEditLabel.setVisible(True)
                self.ui.speakerEdit.setVisible(True)
                self.ui.speakerEdit.setText(item.link.node.speaker)
            elif isinstance(item.link.node, DLGReply):
                self.ui.speakerEditLabel.setVisible(False)
                self.ui.speakerEdit.setVisible(False)
            else:
                raise TypeError(f"Node was type {item.link.node.__class__.__name__} ({item.link.node}), expected DLGEntry/DLGReply")

            self.ui.listenerEdit.setText(item.link.node.listener)

            self.ui.script1ResrefEdit.set_combo_box_text(str(item.link.node.script1))
            self.ui.script1Param1Spin.setValue(item.link.node.script1_param1)
            self.ui.script1Param2Spin.setValue(item.link.node.script1_param2)
            self.ui.script1Param3Spin.setValue(item.link.node.script1_param3)
            self.ui.script1Param4Spin.setValue(item.link.node.script1_param4)
            self.ui.script1Param5Spin.setValue(item.link.node.script1_param5)
            self.ui.script1Param6Edit.setText(item.link.node.script1_param6)
            self.ui.script2ResrefEdit.set_combo_box_text(str(item.link.node.script2))
            self.ui.script2Param1Spin.setValue(item.link.node.script2_param1)
            self.ui.script2Param2Spin.setValue(item.link.node.script2_param2)
            self.ui.script2Param3Spin.setValue(item.link.node.script2_param3)
            self.ui.script2Param4Spin.setValue(item.link.node.script2_param4)
            self.ui.script2Param5Spin.setValue(item.link.node.script2_param5)
            self.ui.script2Param6Edit.setText(item.link.node.script2_param6)

            self.refresh_anim_list()
            self.ui.emotionSelect.setCurrentIndex(item.link.node.emotion_id)
            self.ui.expressionSelect.setCurrentIndex(item.link.node.facial_id)
            self.ui.soundCheckbox.setChecked(bool(item.link.node.sound_exists))
            self.ui.soundComboBox.set_combo_box_text(str(item.link.node.sound))
            self.ui.voiceComboBox.set_combo_box_text(str(item.link.node.vo_resref))

            self.ui.plotIndexCombo.setCurrentIndex(item.link.node.plot_index)
            self.ui.plotXpSpin.setValue(item.link.node.plot_xp_percentage)
            self.ui.questEdit.setText(item.link.node.quest)
            self.ui.questEntrySpin.setValue(item.link.node.quest_entry or 0)

            self.ui.cameraIdSpin.setValue(-1 if item.link.node.camera_id is None else item.link.node.camera_id)
            self.ui.cameraAnimSpin.setValue(-1 if item.link.node.camera_anim is None else item.link.node.camera_anim)

            self.ui.cameraAngleSelect.setCurrentIndex(0 if item.link.node.camera_angle is None else item.link.node.camera_angle)
            self.ui.cameraEffectSelect.setCurrentIndex(-1 if item.link.node.camera_effect is None else item.link.node.camera_effect)

            self.ui.nodeUnskippableCheckbox.setChecked(item.link.node.unskippable)
            self.ui.nodeIdSpin.setValue(item.link.node.node_id)
            self.ui.alienRaceNodeSpin.setValue(item.link.node.alien_race_node)
            self.ui.postProcSpin.setValue(item.link.node.post_proc_node)
            self.ui.delaySpin.setValue(item.link.node.delay)
            self.ui.logicSpin.setValue(item.link.logic)
            self.ui.waitFlagSpin.setValue(item.link.node.wait_flags)
            self.ui.fadeTypeSpin.setValue(item.link.node.fade_type)

            self.ui.commentsEdit.setPlainText(item.link.node.comment)
            self.update_labels()
            self.handle_sound_checked()
        self._node_loaded_into_ui = True

    def on_node_update(self, *args, **kwargs):
        """Updates node properties based on UI selections."""
        if not self._node_loaded_into_ui:
            return
        selected_indices = self.ui.dialogTree.selectedIndexes()
        if not selected_indices:
            print("onNodeUpdate: no selected indices, early return")
            return
        for index in selected_indices:
            if not index.isValid():
                RobustLogger().warning("onNodeUpdate: index invalid")
                continue
            item: DLGStandardItem | None = self.model.itemFromIndex(index)
            if item is None or item.isDeleted():
                RobustLogger().warning("onNodeUpdate: no item for this selected index, or item was deleted.")
                continue
            assert item.link is not None, "onNodeUpdate: item.link was None"
            print(f"onNodeUpdate iterating item: {item!r}")

            item.link.active1 = ResRef(self.ui.condition1ResrefEdit.currentText())
            item.link.active1_param1 = self.ui.condition1Param1Spin.value()
            item.link.active1_param2 = self.ui.condition1Param2Spin.value()
            item.link.active1_param3 = self.ui.condition1Param3Spin.value()
            item.link.active1_param4 = self.ui.condition1Param4Spin.value()
            item.link.active1_param5 = self.ui.condition1Param5Spin.value()
            item.link.active1_param6 = self.ui.condition1Param6Edit.text()
            item.link.active1_not = self.ui.condition1NotCheckbox.isChecked()
            item.link.active2 = ResRef(self.ui.condition2ResrefEdit.currentText())
            item.link.active2_param1 = self.ui.condition2Param1Spin.value()
            item.link.active2_param2 = self.ui.condition2Param2Spin.value()
            item.link.active2_param3 = self.ui.condition2Param3Spin.value()
            item.link.active2_param4 = self.ui.condition2Param4Spin.value()
            item.link.active2_param5 = self.ui.condition2Param5Spin.value()
            item.link.active2_param6 = self.ui.condition2Param6Edit.text()
            item.link.active2_not = self.ui.condition2NotCheckbox.isChecked()
            item.link.logic = bool(self.ui.logicSpin.value())

            item.link.node.listener = self.ui.listenerEdit.text()
            if isinstance(item.link.node, DLGEntry):
                item.link.node.speaker = self.ui.speakerEdit.text()
            item.link.node.script1 = ResRef(self.ui.script1ResrefEdit.currentText())
            item.link.node.script1_param1 = self.ui.script1Param1Spin.value()
            item.link.node.script1_param2 = self.ui.script1Param2Spin.value()
            item.link.node.script1_param3 = self.ui.script1Param3Spin.value()
            item.link.node.script1_param4 = self.ui.script1Param4Spin.value()
            item.link.node.script1_param5 = self.ui.script1Param5Spin.value()
            item.link.node.script1_param6 = self.ui.script1Param6Edit.text()
            item.link.node.script2 = ResRef(self.ui.script2ResrefEdit.currentText())
            item.link.node.script2_param1 = self.ui.script2Param1Spin.value()
            item.link.node.script2_param2 = self.ui.script2Param2Spin.value()
            item.link.node.script2_param3 = self.ui.script2Param3Spin.value()
            item.link.node.script2_param4 = self.ui.script2Param4Spin.value()
            item.link.node.script2_param5 = self.ui.script2Param5Spin.value()
            item.link.node.script2_param6 = self.ui.script2Param6Edit.text()

            item.link.node.emotion_id = self.ui.emotionSelect.currentIndex()
            item.link.node.facial_id = self.ui.expressionSelect.currentIndex()
            item.link.node.sound = ResRef(self.ui.soundComboBox.currentText())
            item.link.node.sound_exists = self.ui.soundCheckbox.isChecked()
            item.link.node.vo_resref = ResRef(self.ui.voiceComboBox.currentText())

            item.link.node.plot_index = self.ui.plotIndexCombo.currentIndex()
            item.link.node.plot_xp_percentage = self.ui.plotXpSpin.value()
            item.link.node.quest = self.ui.questEdit.text()
            item.link.node.quest_entry = self.ui.questEntrySpin.value()

            item.link.node.camera_id = self.ui.cameraIdSpin.value()
            item.link.node.camera_anim = self.ui.cameraAnimSpin.value()
            item.link.node.camera_angle = self.ui.cameraAngleSelect.currentIndex()
            item.link.node.camera_effect = self.ui.cameraEffectSelect.currentData()

            if item.link.node.camera_id >= 0 and item.link.node.camera_angle == 0:
                self.ui.cameraAngleSelect.setCurrentIndex(6)
            elif item.link.node.camera_id == -1 and item.link.node.camera_angle == 7:
                self.ui.cameraAngleSelect.setCurrentIndex(0)

            item.link.node.unskippable = self.ui.nodeUnskippableCheckbox.isChecked()
            item.link.node.node_id = self.ui.nodeIdSpin.value()
            item.link.node.alien_race_node = self.ui.alienRaceNodeSpin.value()
            item.link.node.post_proc_node = self.ui.postProcSpin.value()
            item.link.node.delay = self.ui.delaySpin.value()
            item.link.node.wait_flags = self.ui.waitFlagSpin.value()
            item.link.node.fade_type = self.ui.fadeTypeSpin.value()
            item.link.node.comment = self.ui.commentsEdit.toPlainText()
            self.update_labels()
            self.handle_sound_checked()
            self.model.sig_core_dlg_item_data_changed.emit(item)
            if not self.ui.cameraModelSelect.currentText() or not self.ui.cameraModelSelect.currentText().strip():
                self.ui.cameraAnimSpin.blockSignals(True)
                self.ui.cameraAnimSpin.setValue(-1)
                self.ui.cameraAnimSpin.blockSignals(False)
                self.ui.cameraAnimSpin.setDisabled(True)
                self.ui.cameraAnimSpin.setToolTip("You must setup your custom `CameraModel` first (in the 'File Globals' dockpanel at the top.)")
            elif self.ui.cameraAngleSelect.currentText() != "Animated Camera":
                self.ui.cameraAnimSpin.blockSignals(True)
                self.ui.cameraAnimSpin.setValue(-1)
                self.ui.cameraAnimSpin.blockSignals(False)
                self.ui.cameraAnimSpin.setDisabled(True)
                self.ui.cameraAnimSpin.setToolTip("CameraAngle must be set to 'Animated' to use this feature.")
            else:
                self.ui.cameraAnimSpin.setDisabled(False)
                self.ui.cameraAnimSpin.setToolTip("")

            if self.ui.cameraIdSpin.value() == -1 and self.ui.cameraAngleSelect.currentText() == "Static Camera":
                self.ui.cameraIdSpin.setStyleSheet("QSpinBox { color: red; }")
                self.ui.cameraIdLabel.setStyleSheet("QLabel { color: red; }")
                self.ui.cameraAngleSelect.setStyleSheet("QComboBox { color: red; }")
                self.ui.cameraAngleLabel.setStyleSheet("QLabel { color: red; }")
                self.ui.cameraIdSpin.setToolTip("A Camera ID must be defined for Static Cameras.")
                self.ui.cameraAngleSelect.setToolTip("A Camera ID must be defined for Static Cameras.")
            else:
                self.ui.cameraIdSpin.setStyleSheet("")
                self.ui.cameraAngleSelect.setStyleSheet("")
                self.ui.cameraAngleLabel.setStyleSheet("")
                self.ui.cameraIdLabel.setStyleSheet("")
                self.ui.cameraIdSpin.setToolTip("")
                self.ui.cameraAngleSelect.setToolTip("")

    def on_item_expanded(self, index: QModelIndex):
        # self.ui.dialogTree.model().layoutAboutToBeChanged.emit()  # emitting this causes annoying ui jitter as it resizes.
        item = self.model.itemFromIndex(index)
        assert item is not None
        if not item.is_loaded():
            self._fully_load_future_expand_item(item)
        self.ui.dialogTree.debounce_layout_changed(pre_change_emit=False)

    def _fully_load_future_expand_item(self, item: DLGStandardItem):
        self.model.ignoring_updates = True
        item.removeRow(0)  # Remove the placeholder dummy
        assert item.link is not None
        for child_link in item.link.node.links:
            child_item = DLGStandardItem(link=child_link)
            item.appendRow(child_item)
            self.model.load_dlg_item_rec(child_item)
        self.model.ignoring_updates = False

    def on_add_stunt_clicked(self):
        dialog = CutsceneModelDialog(self)
        print("<SDM> [onAddStuntClicked scope] dialog: ", dialog)

        if dialog.exec():
            self.core_dlg.stunts.append(dialog.stunt())
            self.refresh_stunt_list()

    def on_remove_stunt_clicked(self):
        selectedStuntItems = self.ui.stuntList.selectedItems()
        if not selectedStuntItems:
            QMessageBox(QMessageBox.Icon.Information, "No stunts selected", "Select an existing stunt from the above list first, or create one.").exec()
            return
        print("<SDM> [onRemoveStuntClicked scope] selectedStuntItems: ", selectedStuntItems, "len: ", len(selectedStuntItems))
        stunt: DLGStunt = selectedStuntItems[0].data(Qt.ItemDataRole.UserRole)
        print("<SDM> [onRemoveStuntClicked scope] DLGStunt: ", repr(stunt))
        self.core_dlg.stunts.remove(stunt)
        self.refresh_stunt_list()

    def on_edit_stunt_clicked(self):
        selected_stunt_items = self.ui.stuntList.selectedItems()
        if not selected_stunt_items:
            QMessageBox(QMessageBox.Icon.Information, "No stunts selected", "Select an existing stunt from the above list first, or create one.").exec()
            return
        print("<SDM> [onEditStuntClicked scope] selectedStuntItems: ", selected_stunt_items, "len: ", len(selected_stunt_items))
        stunt: DLGStunt = selected_stunt_items[0].data(Qt.ItemDataRole.UserRole)
        print("<SDM> [onEditStuntClicked scope] DLGStunt: ", repr(stunt))

        dialog = CutsceneModelDialog(self, stunt)
        if dialog.exec():
            stunt.stunt_model = dialog.stunt().stunt_model
            print("<SDM> [onEditStuntClicked scope] stunt.stunt_model: ", stunt.stunt_model)

            stunt.participant = dialog.stunt().participant
            print("<SDM> [onEditStuntClicked scope] stunt.participant: ", stunt.participant)

            self.refresh_stunt_list()

    def refresh_stunt_list(self):
        self.ui.stuntList.clear()
        for stunt in self.core_dlg.stunts:
            text = f"{stunt.stunt_model} ({stunt.participant})"
            print("<SDM> [refreshStuntList scope] text: ", text)

            item = QListWidgetItem(text)
            print("<SDM> [refreshStuntList scope] item: ", item)

            item.setData(Qt.ItemDataRole.UserRole, stunt)
            self.ui.stuntList.addItem(item)  # pyright: ignore[reportArgumentType, reportCallIssue]

    def on_add_anim_clicked(self):
        selectedIndexes = self.ui.dialogTree.selectedIndexes()
        if not selectedIndexes:
            QMessageBox(QMessageBox.Icon.Information, "No nodes selected", "Select an item from the tree first.").exec()
            return
        index: QModelIndex = self.ui.dialogTree.selectedIndexes()[0]
        print("<SDM> [onAddAnimClicked scope] QModelIndex: ", self.ui.dialogTree.model().get_identifying_text(index))
        item: DLGStandardItem | None = self.model.itemFromIndex(index)
        dialog = EditAnimationDialog(self, self._installation)
        if dialog.exec():
            assert item is not None
            assert item.link is not None
            item.link.node.animations.append(dialog.animation())
            self.refresh_anim_list()

    def on_remove_anim_clicked(self):
        selected_tree_indexes = self.ui.dialogTree.selectedIndexes()
        if not selected_tree_indexes:
            QMessageBox(QMessageBox.Icon.Information, "No nodes selected", "Select an item from the tree first.").exec()
            return
        selected_anim_items = self.ui.animsList.selectedItems()
        if not selected_anim_items:
            QMessageBox(QMessageBox.Icon.Information, "No animations selected", "Select an existing animation from the above list first, or create one.").exec()
            return
        index: QModelIndex = selected_tree_indexes[0]
        print("<SDM> [onRemoveAnimClicked scope] QModelIndex: ", self.ui.dialogTree.model().get_identifying_text(index))
        item: DLGStandardItem | None = self.model.itemFromIndex(index)
        if item is None:
            print("onRemoveAnimClicked: itemFromIndex returned None")
            self.blink_window()
            return
        anim_item: QListWidgetItem = selected_anim_items[0]  # type: ignore[arg-type]
        anim: DLGAnimation = anim_item.data(Qt.ItemDataRole.UserRole)
        assert item.link is not None
        item.link.node.animations.remove(anim)
        self.refresh_anim_list()

    def on_edit_anim_clicked(self):
        selected_tree_indexes = self.ui.dialogTree.selectedIndexes()
        if not selected_tree_indexes:
            QMessageBox(QMessageBox.Icon.Information, "No nodes selected", "Select an item from the tree first.").exec()
            return
        selected_anim_items = self.ui.animsList.selectedItems()
        if not selected_anim_items:
            QMessageBox(QMessageBox.Icon.Information, "No animations selected", "Select an existing animation from the above list first.").exec()
            return
        anim_item: QListWidgetItem = selected_anim_items[0]  # type: ignore[arg-type]
        anim: DLGAnimation = anim_item.data(Qt.ItemDataRole.UserRole)
        dialog = EditAnimationDialog(self, self._installation, anim)
        if dialog.exec():
            anim.animation_id = dialog.animation().animation_id
            print("<SDM> [onEditAnimClicked scope] anim.animation_id: ", anim.animation_id)

            anim.participant = dialog.animation().participant
            print("<SDM> [onEditAnimClicked scope] anim.participant: ", anim.participant)

            self.refresh_anim_list()

    def refresh_anim_list(self):
        """Refreshes the animations list."""
        self.ui.animsList.clear()
        animations_2da: TwoDA | None = self._installation.ht_get_cache_2da(HTInstallation.TwoDA_DIALOG_ANIMS)
        if animations_2da is None:
            RobustLogger().error(f"refreshAnimList: {HTInstallation.TwoDA_DIALOG_ANIMS}.2da not found, the Animation List will not function!!")
            return

        for index in self.ui.dialogTree.selectedIndexes():
            print("<SDM> [refreshAnimList scope] QModelIndex: ", self.ui.dialogTree.model().get_identifying_text(index))
            if not index.isValid():
                continue
            item: DLGStandardItem | None = self.model.itemFromIndex(index)
            if item is None or item.link is None:
                continue
            for anim in item.link.node.animations:
                name: str = str(anim.animation_id)
                if animations_2da.get_height() > anim.animation_id:
                    name = animations_2da.get_cell(anim.animation_id, "name")
                    print("<SDM> [refreshAnimList scope] name: ", name)

                text: str = f"{name} ({anim.participant})"
                animItem = QListWidgetItem(text)
                animItem.setData(Qt.ItemDataRole.UserRole, anim)
                self.ui.animsList.addItem(animItem)  # pyright: ignore[reportArgumentType, reportCallIssue]


class ReferenceChooserDialog(QDialog):
    itemChosen: ClassVar[QtCore.Signal] = QtCore.Signal()  # pyright: ignore[reportPrivateImportUsage]

    def __init__(self, references: list[weakref.ref[DLGLink]], parent: DLGEditor, item_text: str):
        assert isinstance(parent, DLGEditor)
        super().__init__(parent)
        qt_constructor = QtCore.Qt.WindowFlags if qtpy.API == "QT5" else QtCore.Qt.WindowType  # pyright: ignore[reportAttributeAccessIssue]
        self.setWindowFlags(QtCore.Qt.Dialog | qt_constructor(QtCore.Qt.WindowCloseButtonHint & ~QtCore.Qt.WindowContextHelpButtonHint))  # pyright: ignore[reportAttributeAccessIssue]
        self.setWindowTitle("Node References")

        layout = QVBoxLayout(self)
        self.label = QLabel()
        self.editor: DLGEditor = parent
        self.label.setTextFormat(Qt.TextFormat.RichText)
        self.list_widget = DLGListWidget(parent)  # HACK: fix later (set editor attr properly in listWidget)
        self.list_widget.use_hover_text = True
        self.list_widget.setParent(self)
        self.list_widget.setItemDelegate(HTMLDelegate(self.list_widget))
        layout.addWidget(self.list_widget)

        max_width = 0
        for linkref in references:
            link = linkref()
            if link is None:
                continue
            item = DLGListWidgetItem(link=link, ref=linkref)

            # Build the HTML display
            self.list_widget.update_item(item)
            self.list_widget.addItem(item)
            max_width = max(max_width, self.calculate_html_width(item.data(Qt.ItemDataRole.DisplayRole)))

        button_layout = QHBoxLayout()
        self.backButton = QPushButton()
        self.backButton.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack))  # pyright: ignore[reportOptionalMemberAccess]
        self.forwardButton = QPushButton()
        self.forwardButton.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward))  # pyright: ignore[reportOptionalMemberAccess]
        okButton = QPushButton("OK")
        cancelButton = QPushButton("Cancel")
        button_layout.addWidget(self.backButton)
        button_layout.addWidget(self.forwardButton)
        button_layout.addWidget(okButton)
        button_layout.addWidget(cancelButton)

        layout.addLayout(button_layout)

        okButton.clicked.connect(self.accept)
        cancelButton.clicked.connect(self.reject)
        self.backButton.clicked.connect(self.go_back)
        self.forwardButton.clicked.connect(self.go_forward)

        self.setStyleSheet(self.get_stylesheet())
        self.adjustSize()
        self.setMinimumSize(self.height(), self.width() + 50)
        self.forwardButton.setEnabled(False)
        self.update_item_sizes()
        self.update_references(references, item_text)

    def parent(self) -> DLGEditor:
        parent: QtCore.QObject = super().parent()
        assert isinstance(parent, DLGEditor)
        return parent

    def update_item_sizes(self):
        for i in range(self.list_widget.count()):
            item: DLGListWidgetItem | None = self.list_widget.item(i)
            if item is None:
                RobustLogger().warning(f"ReferenceChooser.update_item_sizes({i}): Item was None unexpectedly.")
                continue
            options = self.list_widget.viewOptions() if qtpy.QT5 else self.list_widget.styleOptionForIndex(item.index())  # pyright: ignore[reportAttributeAccessIssue]
            item.setSizeHint(self.list_widget.itemDelegate().sizeHint(options, self.list_widget.indexFromItem(item)))

    def calculate_html_width(self, html: str) -> int:
        doc = QTextDocument()
        doc.setHtml(html)
        return int(doc.idealWidth())

    def get_stylesheet(self) -> str:
        font_size = 12
        return f"""
        QListWidget {{
            font-size: {font_size}pt;
            margin: 10px;
        }}
        QPushButton {{
            font-size: {font_size}pt;
            padding: 5px 10px;
        }}
        QDialog {{
            background-color: #f0f0f0;
        }}
        .link-container:hover .link-hover-text {{
            display: block;
        }}
        .link-container:hover .link-text {{
            display: none;
        }}
        .link-hover-text {{
            display: none;
        }}
        """

    def accept(self):
        selectedItem = self.list_widget.currentItem()
        if selectedItem:
            self.itemChosen.emit(selectedItem)
        super().accept()

    def go_back(self):
        self.parent().navigate_back()
        self.update_button_states()

    def go_forward(self):
        self.parent().navigate_forward()
        self.update_button_states()

    def update_references(self, referenceItems: list[weakref.ref[DLGLink]], item_text: str):
        self.label.setText(item_text)
        self.list_widget.clear()
        node_path = ""
        for linkref in referenceItems:
            link = linkref()
            if link is None:
                continue
            listItem = DLGListWidgetItem(link=link, ref=linkref)
            self.list_widget.update_item(listItem)
            self.list_widget.addItem(listItem)
        self.update_item_sizes()
        self.adjustSize()
        self.setWindowTitle(f"Node References: {node_path}")
        self.update_button_states()

    def update_button_states(self):
        parent = self.parent()
        self.backButton.setEnabled(parent.current_reference_index > 0)
        self.forwardButton.setEnabled(parent.current_reference_index < len(parent.reference_history) - 1)


class DLGSettings:
    def __init__(self, settings_name: str = "RobustTreeView"):
        self.settings: QSettings = QSettings("HolocronToolsetV3", settings_name)

    def get(self, key: str, default: Any) -> Any:
        # sourcery skip: assign-if-exp, reintroduce-else
        if qtpy.API_NAME in ("PyQt5", "PySide2"):
            return self.settings.value(
                key,
                default,
                default.__class__,
            )
        result = self.settings.value(key, default)
        if result == "true":
            return True
        if result == "false":
            return False
        return result

    def set(self, key: str, value: Any):
        self.settings.setValue(key, value)

    def tsl_widget_handling(self, default: str) -> str:
        return self.get("tsl_widget_handling", default)

    def set_tsl_widget_handling(self, value: str):
        self.set("tsl_widget_handling", value)
