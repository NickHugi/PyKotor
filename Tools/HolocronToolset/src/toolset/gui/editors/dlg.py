from __future__ import annotations

import gc
import inspect
import json
import random
import uuid
import weakref

from collections import deque
from copy import copy
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Generator, Iterable, List, Mapping, Sequence, cast, overload

import qtpy

from qtpy import QtCore
from qtpy.QtCore import (
    QByteArray,
    QDataStream,
    QIODevice,
    QItemSelectionModel,
    QMimeData,
    QModelIndex,
    QPoint,
    QPropertyAnimation,
    QRect,
    QSettings,
    QTimer,
    Qt,
)
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
    QRadialGradient,
    QStandardItem,
    QStandardItemModel,
    QTextDocument,
)
from qtpy.QtWidgets import (
    QAbstractItemView,
    QAction,
    QActionGroup,
    QApplication,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QDockWidget,
    QDoubleSpinBox,
    QHBoxLayout,
    QInputDialog,
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
    QToolTip,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)
from typing_extensions import Literal

from pykotor.common.misc import Game, ResRef
from pykotor.extract.installation import SearchLocation
from pykotor.resource.generics.dlg import (
    DLG,
    DLGComputerType,
    DLGConversationType,
    DLGEntry,
    DLGLink,
    DLGReply,
    read_dlg,
    write_dlg,
)
from pykotor.resource.type import ResourceType
from toolset.data.installation import HTInstallation
from toolset.gui.common.filters import NoScrollEventFilter
from toolset.gui.common.style.delegates import HTMLDelegate
from toolset.gui.common.widgets.tree import RobustTreeView
from toolset.gui.dialogs.edit.dialog_animation import EditAnimationDialog
from toolset.gui.dialogs.edit.dialog_model import CutsceneModelDialog
from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog
from toolset.gui.editor import Editor
from toolset.gui.widgets.edit.combobox_2da import ComboBox2DA
from toolset.gui.widgets.settings.installations import GlobalSettings
from toolset.utils.misc import QtKey, getQtKeyString
from utility.logger_util import RobustRootLogger

if qtpy.API_NAME in ("PyQt6", "PySide6"):
    from qtpy.QtGui import QUndoStack
else:
    from qtpy.QtWidgets import QUndoStack

if TYPE_CHECKING:

    import os

    from qtpy.QtCore import (
        QAbstractListModel,
        QItemSelection,
        QObject,
        QTemporaryFile,
    )
    from qtpy.QtGui import (
        QCloseEvent,
        QDragEnterEvent,
        QDragLeaveEvent,
        QDragMoveEvent,
        QDropEvent,
        QFocusEvent,
        QKeyEvent,
        QMouseEvent,
        QPaintEvent,
        QShowEvent,
    )
    from typing_extensions import Self

    from pykotor.resource.formats.twoda.twoda_data import TwoDA
    from pykotor.resource.generics.dlg import (
        DLGAnimation,
        DLGNode,
        DLGStunt,
    )
    from utility.system.path import PureWindowsPath

_LINK_PARENT_NODE_PATH_ROLE = Qt.ItemDataRole.UserRole + 1
_EXTRA_DISPLAY_ROLE = Qt.ItemDataRole.UserRole + 2
_FUTURE_EXPAND_ROLE = Qt.ItemDataRole.UserRole + 3
_DLG_MIME_DATA_ROLE = Qt.ItemDataRole.UserRole + 4
_MODEL_INSTANCE_ID_ROLE = Qt.ItemDataRole.UserRole + 5
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
        #self._link_ref: weakref.ref[DLGLink] = weakref.ref(link)  # Store a weak reference to the link
        self._data_cache: dict[int, Any] = {}
        self.is_orphaned = False

    #@property
    #def link(self) -> DLGLink | None:
    #    """Return the link, or None if the reference is no longer valid."""
    #    return self._link_ref()

    #@link.setter
    #def link(self, new_link: DLGLink) -> None:
    #    raise NotImplementedError("DLGStandardItem's cannot store strong references to DLGLink objects.")


    def data(self, role: int = Qt.UserRole) -> Any:
        """Returns the data for the role. Uses cache if the item has been deleted."""
        if self.isDeleted():
            return self._data_cache.get(role)
        result = super().data(role)
        self._data_cache[role] = result  # Update cache
        return result

    def setData(self, role: int, value: Any) -> None:
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
            RobustRootLogger.warning(f"isDeleted suppressed the following exception: {e.__class__.__name__}: {e}")
            return True
        else:
            return False


class DLGListWidget(QListWidget):
    itemSelectionChanged: ClassVar[QtCore.Signal]
    currentRowChanged: ClassVar[QtCore.Signal]
    currentTextChanged: ClassVar[QtCore.Signal]
    currentItemChanged: ClassVar[QtCore.Signal]
    itemChanged: ClassVar[QtCore.Signal]
    itemEntered: ClassVar[QtCore.Signal]
    itemActivated: ClassVar[QtCore.Signal]
    itemDoubleClicked: ClassVar[QtCore.Signal]
    itemClicked: ClassVar[QtCore.Signal]
    itemPressed: ClassVar[QtCore.Signal]
    itemDropped: ClassVar[QtCore.Signal] = QtCore.Signal(QMimeData, Qt.DropAction, name="itemDropped")

    def __init__(self, parent: DLGEditor):
        super().__init__(parent)
        self.editor: DLGEditor = parent
        self.draggedItem: DLGListWidgetItem | None = None
        self.currentlyHoveredItem: DLGListWidgetItem | None = None
        self.useHoverText: bool = True

        self.itemPressed.connect(lambda: self.editor.jumpToNode(getattr(self.currentItem(), "link", None)))
        self.itemDoubleClicked.connect(lambda: self.editor.focusOnNode(getattr(self.currentItem(), "link", None)))
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(lambda pt: self.editor.onListContextMenu(pt, self))
        self.setMouseTracking(True)

    def mouseMoveEvent(self, event: QMouseEvent):
        super().mouseMoveEvent(event)
        if not self.useHoverText:
            return
        item = self.itemAt(event.pos())
        if item is not self.currentlyHoveredItem:
            #print(f"{self.__class__.__name__}.mouseMoveEvent: item hover change {self.currentlyHoveredItem} --> {item.__class__.__name__}")
            if (
                self.currentlyHoveredItem is not None
                and not self.currentlyHoveredItem.isDeleted()
                and self.row(self.currentlyHoveredItem) != -1
            ):
                #print("Reset old hover item")
                hover_display = self.currentlyHoveredItem.data(Qt.ItemDataRole.DisplayRole)
                default_display = self.currentlyHoveredItem.data(_EXTRA_DISPLAY_ROLE)
                #print("hover display:", hover_display, "default_display", default_display)
                self.currentlyHoveredItem.setData(Qt.DisplayRole, default_display)
                self.currentlyHoveredItem.setData(_EXTRA_DISPLAY_ROLE, hover_display)
            self.currentlyHoveredItem = item
            if self.currentlyHoveredItem is None:
                self.viewport().update()
                self.update()
                return
            #print("Set hover display text for newly hovered over item.")
            hover_display = self.currentlyHoveredItem.data(_EXTRA_DISPLAY_ROLE)
            default_display = self.currentlyHoveredItem.data(Qt.ItemDataRole.DisplayRole)
            #print("hover display:", hover_display, "default_display", default_display)
            self.currentlyHoveredItem.setData(Qt.DisplayRole, hover_display)
            self.currentlyHoveredItem.setData(_EXTRA_DISPLAY_ROLE, default_display)
            self.viewport().update()
            self.update()

    def isPersistentEditorOpen(self, item: DLGListWidgetItem | None = None) -> bool:  # type: ignore[override, misc]
        assert isinstance(item, (DLGListWidgetItem, type(None)))
        return super().isPersistentEditorOpen(item)

    def removeItemWidget(self, aItem: DLGListWidgetItem | None = None) -> None:  # type: ignore[override, misc]
        assert isinstance(aItem, (DLGListWidgetItem, type(None)))
        super().removeItemWidget(aItem)

    def itemFromIndex(self, index: QModelIndex) -> DLGListWidgetItem | None:
        item = super().itemFromIndex(index)
        assert isinstance(item, (DLGListWidgetItem, type(None)))
        return item

    def indexFromItem(self, item: DLGListWidgetItem | None = None) -> QModelIndex:  # type: ignore[override, misc]
        assert isinstance(item, (DLGListWidgetItem, type(None)))
        return super().indexFromItem(item)

    def items(self, data: QMimeData) -> list[DLGListWidgetItem]:  # type: ignore[override, misc]
        return super().items(data)  # type: ignore[return-type]

    def supportedDropActions(self) -> Qt.DropActions:
        return super().supportedDropActions()

    def dropMimeData(self, index: int, data: QMimeData, action: Qt.DropAction) -> bool:
        print(f"DLGListWidget.dropMimeData(index={index}, data={data}, action={action})")
        return super().dropMimeData(index, data, action)

    def dragEnterEvent(self, event: QDragEnterEvent):
        #print(f"DLGListWidget.dragEnterEvent(event={event}(source={event.__class__.__name__} instance))")
        if event.mimeData().hasFormat(QT_STANDARD_ITEM_FORMAT):
            #print("DLGListWidget.dragEnterEvent: mime data has our format")
            event.accept()
            event.setAccepted(True)
            event.setDropAction(Qt.DropAction.CopyAction)
        else:
            #print("DLGListWidget.dragEnterEvent: invalid mime data")
            event.ignore()
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent):
        #print(f"DLGListWidget.dragEnterEvent(event={event}(source={event.__class__.__name__} instance))")
        if event.mimeData().hasFormat(QT_STANDARD_ITEM_FORMAT):
            #print("DLGListWidget.dragMoveEvent: mime data has our format")
            event.setDropAction(Qt.MoveAction)
            event.accept()
        else:
            #print("DLGListWidget.dragMoveEvent: invalid mime data")
            event.ignore()
        super().dragMoveEvent(event)

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        print(f"DLGListWidget.dragLeaveEvent(event={event}(source={event.__class__.__name__} instance))")
        event.accept()
        super().dragLeaveEvent(event)

    def focusOutEvent(self, event: QFocusEvent):
        super().focusOutEvent(event)
        if (
            self.currentlyHoveredItem is not None
            and not self.currentlyHoveredItem.isDeleted()
            and self.row(self.currentlyHoveredItem) != -1
        ):
            #print("Reset old hover item")
            hover_display = self.currentlyHoveredItem.data(Qt.ItemDataRole.DisplayRole)
            default_display = self.currentlyHoveredItem.data(_EXTRA_DISPLAY_ROLE)
            #print("hover display:", hover_display, "default_display", default_display)
            self.currentlyHoveredItem.setData(Qt.DisplayRole, default_display)
            self.currentlyHoveredItem.setData(_EXTRA_DISPLAY_ROLE, hover_display)
        self.currentlyHoveredItem = None

    def updateItem(self, item: DLGListWidgetItem, cached_paths: tuple[str, str, str] | None = None):
        """Refreshes the item text and formatting based on the node data."""
        assert self.editor is not None
        link_parent_path, link_partial_path, node_path = self.editor.get_item_dlg_paths(item) if cached_paths is None else cached_paths
        color = "red" if isinstance(item.link.node, DLGEntry) else "blue"
        if link_parent_path:
            link_parent_path += "\\"
        else:
            link_parent_path = ""
        hover_text_1 = f"<span style='color:{color};'> (taken from: {link_parent_path}{link_partial_path})</span>"
        display_text_2 = f"<div class='link-hover-text' style='color:{color};text-align:center;'>{node_path}</div>"

        default_display = f"<div class='link-container'>{display_text_2}</div>"
        hover_display = f"<div class='link-container'>{display_text_2}{hover_text_1}</div>"
        item.setData(Qt.ItemDataRole.DisplayRole, default_display)
        item.setData(_EXTRA_DISPLAY_ROLE, hover_display)
        text = repr(item.link.node) if self.editor._installation is None or item.link.node is None else self.editor._installation.string(item.link.node.text)  # noqa: SLF001
        item.setToolTip(text + "<br><br><i>Right click for more options</i>")

    def dropEvent(self, event: QDropEvent):
        print(f"DLGListWidget.dropEvent(event={event}(source={event.__class__.__name__} instance))")
        if event.mimeData().hasFormat(QT_STANDARD_ITEM_FORMAT):
            print("DLGListWidget.dropEvent: mime data has our format")
            assert self.editor is not None
            item_data = self.editor.ui.dialogTree.parseMimeData(event.mimeData())
            link: DLGLink = DLGLink.from_dict(json.loads(item_data[0]["roles"][_DLG_MIME_DATA_ROLE]))
            newItem = DLGListWidgetItem(link=link)
            self.updateItem(newItem)
            self.addItem(newItem)
            self.update()
            self.viewport().update()
            event.accept()
            self.itemDropped.emit(event.mimeData(), event.dropAction())
        else:
            print("DLGListWidget.dropEvent: invalid mime data")
            event.ignore()

    def mimeData(self, items: Iterable[DLGListWidgetItem]) -> QMimeData:  # type: ignore[override, misc]
        print(f"DLGListWidget.dropEvent: acquiring mime data for {len(list(items))} items")
        return super().mimeData(items)

    def scrollToItem(self, item: DLGListWidgetItem | None = None, *args) -> None:  # type: ignore[override, misc]
        assert isinstance(item, (DLGListWidgetItem, type(None)))
        super().scrollToItem(item, *args)

    def findItems(self, text: str, flags: Qt.MatchFlags) -> list[DLGListWidgetItem]:  # type: ignore[override, misc]
        return super().findItems(text, flags)

    def selectedItems(self) -> list[DLGListWidgetItem]:  # type: ignore[override, misc]
        return super().selectedItems()

    def closePersistentEditor(self, item: DLGListWidgetItem | None = None) -> None:  # type: ignore[override, misc]
        assert isinstance(item, (DLGListWidgetItem, type(None)))
        super().closePersistentEditor(item)

    def openPersistentEditor(self, item: DLGListWidgetItem | None = None) -> None:  # type: ignore[override, misc]
        assert isinstance(item, (DLGListWidgetItem, type(None)))
        super().openPersistentEditor(item)

    def editItem(self, item: DLGListWidgetItem | None = None) -> None:  # type: ignore[override, misc]
        assert isinstance(item, (DLGListWidgetItem, type(None)))
        super().editItem(item)

    def visualItemRect(self, item: DLGListWidgetItem | None = None) -> QRect:  # type: ignore[override, misc]
        assert isinstance(item, (DLGListWidgetItem, type(None)))
        return super().visualItemRect(item)

    def setItemWidget(self, item: DLGListWidgetItem | None, widget: QWidget) -> None:  # type: ignore[override, misc]
        assert isinstance(item, (DLGListWidgetItem, type(None)))
        super().setItemWidget(item, widget)

    def itemWidget(self, item: DLGListWidgetItem | None = None) -> QWidget | None:  # type: ignore[override, misc]
        assert isinstance(item, (DLGListWidgetItem, type(None)))
        return super().itemWidget(item)

    @overload
    def itemAt(self, p: QPoint) -> DLGListWidgetItem | None: ...
    @overload
    def itemAt(self, ax: int, ay: int) -> DLGListWidgetItem | None: ...
    def itemAt(self, *args) -> DLGListWidgetItem | None:  # type: ignore[override, misc]
        item = super().itemAt(*args)
        assert isinstance(item, (DLGListWidgetItem, type(None)))
        return item

    @overload
    def setCurrentItem(self, item: DLGListWidgetItem | None = None) -> None: ...
    @overload
    def setCurrentItem(
        self,
        item: DLGListWidgetItem | None,
        command: QtCore.QItemSelectionModel.SelectionFlags | QtCore.QItemSelectionModel.SelectionFlag | None,
    ) -> None: ...
    def setCurrentItem(
        self,
        item: DLGListWidgetItem | None = None,
        command: QtCore.QItemSelectionModel.SelectionFlags | QtCore.QItemSelectionModel.SelectionFlag | None = None,
    ) -> None:
        assert isinstance(item, (DLGListWidgetItem, type(None)))
        if command is None:
            super().setCurrentItem(item)
        else:
            super().setCurrentItem(item, command)

    def currentItem(self) -> DLGListWidgetItem | None:
        item = super().currentItem()
        assert isinstance(item, (DLGListWidgetItem, type(None)))
        return item

    def takeItem(self, row: int) -> DLGListWidgetItem | None:
        item = super().takeItem(row)
        assert isinstance(item, (DLGListWidgetItem, type(None)))
        return item

    @overload
    def addItem(self, aitem: DLGListWidgetItem | None = None) -> None: ...
    @overload
    def addItem(self, label: str | None = None) -> None: ...
    def addItem(self, item: DLGListWidgetItem | str | None = None) -> None:  # type: ignore[override, misc]
        if isinstance(item, (DLGListWidgetItem, type(None))):
            super().addItem(item)
        elif isinstance(item, (str, type(None))):
            super().addItem(item)
        else:
            raise TypeError("Incorrect args passed to addItem")

    @overload
    def insertItem(self, row: int, item: DLGListWidgetItem | None = None) -> None: ...
    @overload
    def insertItem(self, row: int, label: str) -> None: ...
    def insertItem(self, row: int, item: DLGListWidgetItem | str | None) -> None:  # type: ignore[override, misc]
        if isinstance(item, (DLGListWidgetItem, type(None))):
            super().insertItem(row, item)
        elif isinstance(item, str):
            super().insertItem(row, item)
        else:
            raise TypeError("Incorrect args passed to insertItem")

    def row(self, item: DLGListWidgetItem | None = None) -> int:  # type: ignore[override, misc]
        assert isinstance(item, (DLGListWidgetItem, type(None)))
        return super().row(item)

    def item(self, row: int) -> DLGListWidgetItem | None:
        item = super().item(row)
        assert isinstance(item, (DLGListWidgetItem, type(None)))
        return item

def find_strong_references(obj):
    """Find names and locations of root variables or class attributes holding references to the object.

    used temporarily to debug garbage collection of weakrefs
    """
    import objgraph
    objgraph.show_backrefs([obj], filename="object_backrefs.png")
    for referrer in gc.get_referrers(obj):
        if inspect.isfunction(referrer) and "<lambda>" in referrer.__name__:
            print(f"Lambda found: {referrer.__name__} in {referrer.__code__.co_filename} at line {referrer.__code__.co_firstlineno}")
            print("Closure variables:", [cell.cell_contents for cell in referrer.__closure__])

def debug_references(obj: Any):
    find_strong_references(obj)


class DLGStandardItem(QStandardItem):
    def __init__(self, *args, link: DLGLink, **kwargs):
        super().__init__(*args, **kwargs)
        self._link_ref: weakref.ref[DLGLink] = weakref.ref(link)  # Store a weak reference to the link
        self._data_cache: dict[int, Any] = {}

    @property
    def link(self) -> DLGLink | None:
        """Return the link, or None if the reference is no longer valid.

        Weak references are used throughout to ensure that orphaned nodes will be automatically detected and added to the orphanedNodesList listwidget.

        IMPORTANT: Do NOT save or store this result to e.g. a lambda, otherwise that lambda provides a strong reference and due to the nature of lambdas, becomes very difficult to track down.
        To be safe, it's just best to never save this to a local variable. Just test `item.link is not None` whenever you need the link and send `item.link` directly to wherever you need it.
        """
        return self._link_ref()

    @link.setter
    def link(self, new_link: DLGLink) -> None:
        raise NotImplementedError("DLGStandardItem's cannot store strong references to DLGLink objects.")

    def parent(self) -> DLGStandardItem | None:  # type: ignore[override, misc]
        return super().parent()  # type: ignore[return-value]

    def __eq__(self, other):
        return self is other

    def __hash__(self) -> int:
        return id(self)

    def isDeleted(self) -> bool:
        """Determines if this object has been deleted.

        Not sure what the proper method of doing so is, but this works fine.
        """
        try:
            self.model()
            self.index()
        except RuntimeError as e:  # RuntimeError: wrapped C/C++ object of type DLGStandardItem has been deleted
            RobustRootLogger.warning(f"isDeleted suppressed the following exception: {e.__class__.__name__}: {e}")
            return True
        else:
            return False

    def model(self) -> DLGStandardItemModel:
        model = super().model()
        if model is None:
            return None
        assert isinstance(model, DLGStandardItemModel), f"model was {model} of type {model.__class__.__name__}"
        return model

    def appendRow(self, item: DLGStandardItem) -> None:  # type: ignore[override, misc]
        #print(f"{self.__class__.__name__}.appendRow(item={item!r})")
        assert isinstance(item, DLGStandardItem) or cast(QStandardItem, item).data(_FUTURE_EXPAND_ROLE)
        assert isinstance(item, DLGStandardItem) or cast(QStandardItem, item).data(_FUTURE_EXPAND_ROLE)
        super().appendRow(item)
        if isinstance(item, DLGStandardItem) and self.model() and not self.model().signalsBlocked():
            self.model()._addLinkToParent(self, item)  # noqa: SLF001

    def appendRows(self, items: Iterable[DLGStandardItem]) -> None:  # type: ignore[override]
        print(f"{self.__class__.__name__}.appendRows(items={items!r})")
        for item in items:
            self.appendRow(item)

    def insertRow(self, row: int, item: DLGStandardItem) -> None:  # type: ignore[override, misc]
        print(f"{self.__class__.__name__}.insertRow(row={row}, item={item})")
        assert isinstance(item, DLGStandardItem) or cast(QStandardItem, item).data(_FUTURE_EXPAND_ROLE)
        super().insertRow(row, item)
        if isinstance(item, DLGStandardItem) and self.model() and not self.model().signalsBlocked():
            self.model()._insertLinkToParent(self, item, row)  # noqa: SLF001

    def insertRows(self, row: int, items: Iterable[Self]) -> None:  # type: ignore[override]
        print(f"{self.__class__.__name__}.insertRows(row={row}, items={items})")
        assert not isinstance(items, int), "Second arg cannot be a `count` in this implementation."
        for i, item in enumerate(items):
            self.insertRow(row + i, item)

    def removeRow(self, row: int) -> None:
        #print(f"{self.__class__.__name__}.removeRow(row={row})")
        self.takeRow(row)[0]

    def removeRows(self, row: int, count: int) -> None:
        print(f"{self.__class__.__name__}.removeRows(row={row}, count={count})")
        for _ in range(count):
            self.removeRow(row)

    def setChild(self, row: int, *args) -> None:
        print(f"{self.__class__.__name__}.setChild(row={row}, args={args!r})")
        if len(args) == 3:
            item = args[1]
        else:
            item = args[0]
        assert isinstance(item, DLGStandardItem) or cast(QStandardItem, item).data(_FUTURE_EXPAND_ROLE)
        super().setChild(row, *args)
        if (
            isinstance(item, DLGStandardItem)
            and self.model()
            and not self.model().signalsBlocked()
        ):
            self.model()._addLinkToParent(self, item)  # noqa: SLF001

    def takeChild(self, row: int, column: int = 0) -> Self:
        #print(f"{self.__class__.__name__}.takeChild(row={row}, column={column})")
        item = super().takeChild(row, column)
        assert isinstance(item, DLGStandardItem) or item.data(_FUTURE_EXPAND_ROLE)
        if (
            isinstance(item, DLGStandardItem)
            and self.model()
            and not self.model().signalsBlocked()
            and not self.model()._isMoving
        ):
            self.model()._removeLinkFromParent(self, item)  # noqa: SLF001
        return item

    def takeRow(self, row: int) -> list[DLGStandardItem]:  # type: ignore[override]
        #print(f"{self.__class__.__name__}.takeRow(row={row})")
        items = super().takeRow(row)
        if (
            items
            and isinstance(items[0], DLGStandardItem)
            and self.model()
            and not self.model().signalsBlocked()
            and not self.model()._isMoving
        ):
            for item in items:
                if not isinstance(item, DLGStandardItem):
                    continue
                self.model()._removeLinkFromParent(self, item)  # noqa: SLF001
        return items

    def takeColumn(self, column: int) -> list[DLGStandardItem]:  # type: ignore[override]
        raise NotImplementedError("takeColumn is not supported in this model.")
        #items = super().takeColumn(column)
        #if self.model() and not self.model().signalsBlocked():
        #    for item in items:
        #        self.model()._removeLinkFromParent(self, item)
        #return items

    def data(self, role: int = Qt.ItemDataRole.UserRole) -> Any:
        """Returns the data for the role. Uses cache if the item has been deleted."""
        if self.isDeleted():
            return self._data_cache.get(role)
        result = super().data(role)
        self._data_cache[role] = result  # Update cache
        #print(f"{self.__class__.__name__}.data(role={role}) --> {result}")
        return result

    def setData(self, value: Any, role: int = Qt.ItemDataRole.UserRole) -> None:
        """Sets the data for the role and updates the cache."""
        #print(f"{self.__class__.__name__}.setData(value={value}, role={role})")
        super().setData(value, role)
        self._data_cache[role] = value  # Update cache

        if self.model():
            self.model().itemChanged.emit(self)

    def clearData(self) -> None:
        print(f"{self.__class__.__name__}.clearData()")
        super().clearData()
        if self.model():
            self.model().itemChanged.emit(self)

    def emitDataChanged(self) -> None:
        print(f"{self.__class__.__name__}.emitDataChanged()")
        if self.model() is None:
            super().emitDataChanged()
            return
        self.model().dataChanged.emit(self.index(), self.index())


class DLGStandardItemModel(QStandardItemModel):
    # Signal emitted when item data has changed
    #dataChanged: ClassVar[QtCore.Signal] = QtCore.Signal(QModelIndex, QModelIndex, list)  # list of roles changed

    # Signal emitted when header data has changed
    #headerDataChanged = QtCore.Signal(Qt.Orientation, int, int)  # orientation, first section, last section

    # Signals for layout changes
    #layoutChanged = QtCore.Signal(list, QStandardItemModel.LayoutChangeHint)  # list of parent indices, layout change hint
    #layoutAboutToBeChanged = QtCore.Signal(list, QStandardItemModel.LayoutChangeHint)  # list of parent indices, layout change hint

    # Signals for row operations
    #rowsInserted = QtCore.Signal(QModelIndex, int, int)  # parent index, start row, end row
    #rowsAboutToBeInserted = QtCore.Signal(QModelIndex, int, int)  # parent index, start row, end row
    #rowsRemoved = QtCore.Signal(QModelIndex, int, int)  # parent index, start row, end row
    #rowsAboutToBeRemoved = QtCore.Signal(QModelIndex, int, int)  # parent index, start row, end row
    #rowsMoved = QtCore.Signal(QModelIndex, int, int, QModelIndex, int)  # source parent, start row, end row, destination parent, destination row
    #rowsAboutToBeMoved = QtCore.Signal(QModelIndex, int, int, QModelIndex, int)  # source parent, start row, end row, destination parent, destination row

    # Signals for column operations
    #columnsInserted = QtCore.Signal(QModelIndex, int, int)  # parent index, start column, end column
    #columnsAboutToBeInserted = QtCore.Signal(QModelIndex, int, int)  # parent index, start column, end column
    #columnsRemoved = QtCore.Signal(QModelIndex, int, int)  # parent index, start column, end column
    #columnsAboutToBeRemoved = QtCore.Signal(QModelIndex, int, int)  # parent index, start column, end column
    #columnsMoved = QtCore.Signal(QModelIndex, int, int, QModelIndex, int)  # source parent, start column, end column, destination parent, destination column
    #columnsAboutToBeMoved: ClassVar[QtCore.Signal] = QtCore.Signal(QModelIndex, int, int, QModelIndex, int)  # source parent, start column, end column, destination parent, destination column

    # Signals for model reset
    #modelReset: ClassVar[QtCore.Signal] = QtCore.Signal()  # No parameters
    #modelAboutToBeReset: ClassVar[QtCore.Signal] = QtCore.Signal()  # No parameters

    # Custom for this model.
    coreDLGItemDataChanged: ClassVar[QtCore.Signal] = QtCore.Signal(QStandardItem)  # type: ignore[reportPrivateImportUsage]

    def __init__(self, parent: DLGTreeView):
        assert isinstance(parent, DLGTreeView)
        self.editor: DLGEditor | None = None
        self.treeView: DLGTreeView = parent
        self.linkToItems: weakref.WeakKeyDictionary[DLGLink, list[DLGStandardItem]] = weakref.WeakKeyDictionary()
        self.nodeToItems: weakref.WeakKeyDictionary[DLGNode, list[DLGStandardItem]] = weakref.WeakKeyDictionary()
        self.origToOrphanCopy: dict[weakref.ReferenceType[DLGLink], DLGLink]
        super().__init__(self.treeView)
        self.modelReset.connect(self.onModelReset)
        self.coreDLGItemDataChanged.connect(self.onDialogItemDataChanged)
        self._isMoving = False

    def __iter__(self) -> Generator[QStandardItem, Any, None]:
        stack: list[QStandardItem] = [
            self.item(row, column)
            for row in range(self.rowCount())
            for column in range(self.columnCount())
            if isinstance(self.item(row, column), DLGStandardItem)
        ]
        while stack:
            item = stack.pop()
            yield item
            for row in reversed(range(item.rowCount())):
                for column in range(item.columnCount()):
                    child = item.child(row, column)
                    if not isinstance(child, DLGStandardItem):
                        continue
                    stack.append(child)

    # region Model Overrides
    def insertRows(self, row: int, count: int, parentIndex: QModelIndex | None = None) -> bool:
        print(f"{self.__class__.__name__}.insertRows(row={row}, count={count}, parentIndex={parentIndex})")
        if parentIndex is None:
            parentIndex = QModelIndex()
        self.beginInsertRows(parentIndex, row, row + count - 1)
        result = super().insertRows(row, count, parentIndex)
        self.endInsertRows()
        return result

    def removeRows(self, row: int, count: int, parentIndex: QModelIndex | None = None) -> bool:
        print(f"{self.__class__.__name__}.removeRows(row={row}, count={count}, parentIndex={parentIndex})")
        if row < 0 or count < 1:
            # Check for negative or invalid row index and count
            print(f"Invalid row ({row}) or count ({count})")
            return False
        parent = (self.itemFromIndex(parentIndex) or self) if parentIndex and parentIndex.isValid() else self
        rowsAvailable = parent.rowCount()
        if row + count > rowsAvailable:
            # Check if the range exceeds the number of rows
            print(f"DEBUG(root): Request to remove {count} rows at index {row} exceeds model bounds ({rowsAvailable}).")
            return False

        self.treeView.selectionModel().clear()
        self.beginRemoveRows(QModelIndex() if parentIndex is None else parentIndex, row, row + count - 1)
        if parentIndex is not None:
            items = [self.itemFromIndex(self.index(r, 0, parentIndex)) for r in range(row, row + count)]
        else:
            items = [self.item(r, 0) for r in range(row, row + count)]
        result = super().removeRows(row, count, parentIndex)  # type: ignore[arg-type]
        self.treeView.selectionModel().clear()
        self.endRemoveRows()
        if not self.signalsBlocked() and not self._isMoving:
            for item in items:
                if not isinstance(item, DLGStandardItem):
                    continue
                parentItem = None
                if parentIndex is not None:
                    parentItem = self.itemFromIndex(parentIndex)
                if parentItem is not None and not isinstance(parentItem, DLGStandardItem):
                    continue
                self._removeLinkFromParent(parentItem, item)
        return result

    def appendRows(self, items: Iterable[DLGStandardItem], parentIndex: QModelIndex | None = None) -> None:
        print(f"{self.__class__.__name__}.appendRows(items={items}, parentIndex={parentIndex})")
        for item in items:
            self.appendRow(item, parentIndex)  # type: ignore[call-overload]

    def removeRow(self, row: int, parentIndex: QModelIndex | None = None) -> bool:
        print(f"{self.__class__.__name__}.removeRow(row={row}, parentIndex={parentIndex})")
        if parentIndex is not None and parentIndex.isValid():
            result = super().removeRow(row, parentIndex)  # internally will call self.removeRows
        else:
            result = super().removeRow(row)  # internally will call self.removeRows
        return result

    def item(self, row: int, column: int) -> DLGStandardItem:  # type: ignore[override]
        print(f"{self.__class__.__name__}.item(row={row}, column={column})")
        return super().item(row, column)

    @overload
    def insertRow(self, row: int, items: Iterable[QStandardItem]) -> None: ...
    @overload
    def insertRow(self, arow: int, aitem: QStandardItem) -> None: ...
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
            if not self.signalsBlocked():
                for itemToInsert in toInsert:
                    if not isinstance(itemToInsert, DLGStandardItem):
                        continue
                    if itemToInsert.link is None:
                        continue
                    parentItem = itemToInsert.parent()
                    self._insertLinkToParent(parentItem, itemToInsert, row)
        elif isinstance(toInsert, (QModelIndex, QStandardItem)):
            if not self.signalsBlocked():
                itemToInsert = toInsert if isinstance(toInsert, QStandardItem) else self.itemFromIndex(toInsert)
                if not isinstance(itemToInsert, DLGStandardItem):
                    return result
                if itemToInsert.link is None:
                    return result
                parentItem = itemToInsert.parent()
                self._insertLinkToParent(parentItem, itemToInsert, row)
        else:
            raise TypeError("Incorrect args passed to insertRow")
        return result

    def takeItem(self, row: int, column: int) -> DLGStandardItem:  # type: ignore[override]
        print(f"{self.__class__.__name__}.takeItem(row={row}, column={column})")
        item = cast(DLGStandardItem, super().takeItem(row, column))
        if not self.signalsBlocked() and not self._isMoving:
            self._removeLinkFromParent(None, item)
        return item

    def takeRow(self, row: int) -> list[DLGStandardItem]:  # type: ignore[override]
        print(f"{self.__class__.__name__}.takeRow(row={row})")
        items = cast(List[DLGStandardItem], super().takeRow(row))
        if not items:
            return items
        if self.signalsBlocked():
            return items
        if self._isMoving:
            return items
        for item in items:
            if not isinstance(item, DLGStandardItem):
                continue
            self._removeLinkFromParent(None, item)
            #self._updateCopies(item.link)
        return items

    @overload
    def appendRow(self, items: Iterable[DLGStandardItem]) -> None: ...
    @overload
    def appendRow(self, aitem: DLGStandardItem) -> None: ...
    def appendRow(self, *args) -> None:  # type: ignore[override, misc]
        #print(f"{self.__class__.__name__}.appendRow(args={args})")
        itemToAppend: DLGStandardItem = args[0]
        super().appendRow(itemToAppend)
        if not self.signalsBlocked():
            self._insertLinkToParent(None, itemToAppend, self.rowCount())

    def setHeaderData(self, section: int, orientation: Qt.Orientation, value: Any, role: int = Qt.EditRole) -> bool:
        if super().setHeaderData(section, orientation, value, role):
            self.headerDataChanged.emit(orientation, section, section)
            return True
        return False

    def insertColumns(self, column: int, count: int, parent: QModelIndex | None = None) -> bool:
        if parent is None:
            parent = QModelIndex()
        self.beginInsertColumns(parent, column, column + count - 1)
        result = super().insertColumns(column, count, parent)
        self.endInsertColumns()
        return result

    def removeColumns(self, column: int, count: int, parent: QModelIndex | None = None) -> bool:
        if parent is None:
            parent = QModelIndex()
        self.beginRemoveColumns(parent, column, column + count - 1)
        result = super().removeColumns(column, count, parent)
        self.endRemoveColumns()
        return result
    # endregion

    # region drag&drop
    def supportedDropActions(self) -> Qt.DropActions:
        return Qt.DropAction.CopyAction | Qt.DropAction.MoveAction
    def supportedDragActions(self) -> Qt.DropActions:
        return Qt.DropAction.CopyAction | Qt.DropAction.MoveAction

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        #print(f"DLGStandardItemModel.flags(index={index})\nindex details: {self.treeView.getIdentifyingTextForIndex(index)}")
        defaultFlags = super().flags(index)
        if index.isValid():
            return Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled | defaultFlags
        return Qt.ItemIsDropEnabled | defaultFlags

    def mimeTypes(self) -> list[str]:
        return [QT_STANDARD_ITEM_FORMAT]

    def mimeData(self, indexes: Iterable[QModelIndex]) -> QMimeData:
        mimeData = QMimeData()
        listwidget_data = QByteArray()

        stream_listwidget = QDataStream(listwidget_data, QIODevice.WriteOnly)
        for index in indexes:
            print("<SDM> [mimeData scope] index: ", self.treeView.getIdentifyingText(index))
            if not index.isValid():
                continue
            item = self.itemFromIndex(index)
            if item is None:
                continue
            stream_listwidget.writeInt32(index.row())
            stream_listwidget.writeInt32(index.column())
            stream_listwidget.writeInt32(3)
            stream_listwidget.writeInt32(int(Qt.ItemDataRole.DisplayRole))
            stream_listwidget.writeQString(item.data(Qt.ItemDataRole.DisplayRole))
            stream_listwidget.writeInt32(_DLG_MIME_DATA_ROLE)
            stream_listwidget.writeBytes(json.dumps(item.link.to_dict()).encode())
            stream_listwidget.writeInt32(_MODEL_INSTANCE_ID_ROLE)
            stream_listwidget.writeInt64(id(self))
            #stream_listwidget.writeInt32(int(_LINK_PARENT_NODE_PATH_ROLE))
            #stream_listwidget.writeQString(item.data(_LINK_PARENT_NODE_PATH_ROLE))

        mimeData.setData(QT_STANDARD_ITEM_FORMAT, listwidget_data)
        return mimeData

    def dropMimeData(  # noqa: PLR0913
        self,
        data: QMimeData,
        action: Qt.DropAction,
        row: int,
        column: int,
        parent: QModelIndex,
    ) -> bool:
        print(f"{self.__class__.__name__}.dropMimeData(data, action={action}, row={row}, column={column}, parent={parent})")
        if not data.hasFormat(QT_STANDARD_ITEM_FORMAT):
            return False
        if action == Qt.DropAction.IgnoreAction:
            print(f"{self.__class__.__name__}.dropMimeData: action set to Qt.DropAction.IgnoreAction")
            return True

        parentItem: DLGStandardItem | None = self.itemFromIndex(parent) if parent.isValid() else None
        try:
            parsedMimeData: dict[Literal["row", "column", "roles"], Any] = self.treeView.parseMimeData(data)[0]
            dlg_nodes_json: str = parsedMimeData["roles"][_DLG_MIME_DATA_ROLE]
            dlg_nodes_dict: dict[str | int, Any] = json.loads(dlg_nodes_json)
            deserialized_dlg_link: DLGLink = DLGLink.from_dict(dlg_nodes_dict)
            print("<SDM> [dropMimeData scope] deserialized_dlg_link: ", repr(deserialized_dlg_link))
        except Exception:  # noqa: BLE001
            RobustRootLogger().exception("Failed to deserialize dropped mime data of '_DLG_MIME_DATA_ROLE' format.")
            return True
        else:
            self.pasteItem(parentItem, deserialized_dlg_link, asNewBranches=parsedMimeData["roles"][_MODEL_INSTANCE_ID_ROLE] == id(self))

        return True
    # endregion


    # region Model Signals
    def onModelReset(self):
        print(f"{self.__class__.__name__}.onModelReset()")
        self.linkToItems.clear()
        self.nodeToItems.clear()

    def resetModel(self):
        print(f"{self.__class__.__name__}.resetModel()")
        self.beginResetModel()
        self.clear()
        self.onModelReset()
        self.endResetModel()

    def onDialogItemDataChanged(self, item: DLGStandardItem):
        print(f"onDialogItemDataChanged(item={item!r})")
        if item.link is None:
            #del self.origToOrphanCopy[item._link_ref]
            self.removeRow(item.row())
        else:
            print("onDialogItemDataChanged: link is valid")
            # First take out and store the links/node
            # So we can update our instance objects, without breaking the whole DAG.
            internalLink = self.origToOrphanCopy[item._link_ref]
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
            self.updateItemData(item)
            self._updateCopies(item.link, item)

    def onOrphanedNode(self, shallow_link_copy: DLGLink, link_parent_path: str, *, immediateCheck: bool = False):
        """Add a deleted node to the QListWidget in the leftDockWidget, if the passed link is the only reference."""
        if not shallow_link_copy.node or shallow_link_copy.list_index == -1 and shallow_link_copy.node.list_index == -1:
            print(f"ignoring unfinished node/link {shallow_link_copy!r}")
            return
        if not immediateCheck:
            QTimer.singleShot(200, lambda *args: self.onOrphanedNode(shallow_link_copy, link_parent_path, immediateCheck=True))
            return
        print(f"onOrphanedNode({shallow_link_copy}, {link_parent_path})")
        assert self.editor is not None
        assert shallow_link_copy.node is not None
        print(f"Deleted the only link ({shallow_link_copy}) to node ({shallow_link_copy.node}), setting up the orphan view.")
        item = DLGListWidgetItem(link=shallow_link_copy)
        item.is_orphaned = True

        # Build the HTML display
        color = "red" if isinstance(shallow_link_copy.node, DLGEntry) else "blue"
        link_path = ""
        if link_parent_path is not None:
            link_path += f"{link_parent_path}\\"
        link_path += shallow_link_copy.partial_path()
        node_path = shallow_link_copy.node.path()
        display_text_1 = f"<div class='link-text' style='color:{color};text-align:center;'>{link_path}</div>"
        display_text_2 = f"<div class='link-hover-text' style='color:{color};text-align:center;'>{node_path}</div>"
        combined_display = f"""
        <div class='link-container'>
            {display_text_1}
            {display_text_2}
        </div>
        """
        item.setData(Qt.ItemDataRole.DisplayRole, combined_display)
        item.setData(_LINK_PARENT_NODE_PATH_ROLE, link_parent_path)
        self.editor.orphanedNodesList.addItem(item)
    # endregion

    def insertLinkToParentAsItem(self, parent: DLGStandardItem | None, link: DLGLink, row: int = -1):
        item = DLGStandardItem(link=link)
        if parent is None:
            self.insertRow(self.rowCount() if row == -1 else row, item)
        else:
            parent.insertRow(self.rowCount() if row == -1 else row, item)
        self.updateItemData(item)
        return item

    def removeLink(self, item: DLGStandardItem):
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
            self.updateItemData(parent)
            self._updateCopies(parent.link, parent)
        self.layoutChanged.emit()

    def _addLinkToParent(self, parent: DLGStandardItem, item: DLGStandardItem) -> None:
        assert item.link is not None
        assert item.link.node is not None
        assert parent.link is not None
        assert parent.link.node is not None
        parent.link.node.links.append(item.link)
        item.link.list_index = len(parent.link.node.links) - 1
        linkToItems = self.linkToItems.setdefault(parent.link, [])
        if item not in linkToItems:
            linkToItems.append(item)
        linkToItems = self.linkToItems.setdefault(item.link, [])
        if item not in linkToItems:
            linkToItems.append(item)
        nodeToItems = self.nodeToItems.setdefault(parent.link.node, [])
        if item not in nodeToItems:
            nodeToItems.append(item)
        nodeToItems = self.nodeToItems.setdefault(item.link.node, [])
        if item not in nodeToItems:
            nodeToItems.append(item)

    def _insertLinkToParent(
        self,
        parent: DLGStandardItem | None,
        items: Iterable[DLGStandardItem] | DLGStandardItem,
        row: int,
    ) -> None:
        if isinstance(items, Iterable):
            for i, item in enumerate(items):
                self._processLink(parent, item, row + i)
        else:
            self._processLink(parent, items, row)

    def _processLink(
        self,
        parentItem: DLGStandardItem | None,
        item: DLGStandardItem,
        row: int | None = None,
    ) -> None:
        assert item.link is not None
        assert item.link.node is not None
        assert self.editor is not None
        index = (parentItem or self).rowCount() if row in (-1, None) else row
        print(f"SDM [_processLink scope] Adding #{item.link.node.list_index} to row {index}")
        links_list = self.editor.core_dlg.starters if parentItem is None else parentItem.link.node.links
        nodeToItems = self.nodeToItems.setdefault(item.link.node, [])
        if item not in nodeToItems:
            nodeToItems.append(item)
        linkToItems = self.linkToItems.setdefault(item.link, [])
        if item not in linkToItems:
            linkToItems.append(item)
        current_index = {link: idx for idx, link in enumerate(links_list)}.get(item.link)
        if current_index != index:
            if current_index is not None:
                links_list.pop(current_index)
                if current_index < index:
                    index -= 1
            links_list.insert(index, item.link)
        for i, link in enumerate(links_list):
            link.list_index = i
        copiedLink = self.origToOrphanCopy.get(item._link_ref)
        if copiedLink is not None:
            return
        RobustRootLogger().debug(f"Creating internal copy of {item.link!r} now.")
        copiedLink = DLGLink.from_dict(item.link.to_dict())
        self.origToOrphanCopy[item._link_ref] = copiedLink  # noqa: SLF001

        def register_deepcopies(origLink: DLGLink, copyLink: DLGLink, seenLinks: set[DLGLink] | None = None):
            """Recursively register deepcopies of nested links to avoid redundant deepcopies and register finalizers."""
            if seenLinks is None:
                seenLinks = set()
            if copyLink in seenLinks:
                return
            seenLinks.add(copyLink)
            assert origLink is not copyLink
            assert origLink.node is not None
            assert copyLink.node is not None
            self.origToOrphanCopy[weakref.ref(origLink)] = copyLink
            for childOrigLink, childCopyLink in zip(origLink.node.links, copyLink.node.links):
                register_deepcopies(childOrigLink, childCopyLink, seenLinks)
            if not any(info.weakref() is origLink.node for info in weakref.finalize._registry.values()):
                #print(f"_processLink: Creating finalizer for {potential_orphan!r}")
                weakref.finalize(origLink.node, self.onOrphanedNode, copyLink, origLink.node.path())

        register_deepcopies(item.link, copiedLink)

    def _removeLinkFromParent(
        self,
        parentItem: DLGStandardItem | None,
        item: DLGStandardItem,
    ) -> None:
        assert self.editor is not None
        assert item.link is not None
        assert item.link.node is not None
        # The items could be deleted by qt at this point, so we only use the python object.
        links_list = self.editor.core_dlg.starters if parentItem is None else parentItem.link.node.links
        index = links_list.index(item.link)
        RobustRootLogger().info(f"SDM [_removeLinkFromParent scope] Removing #{item.link.node.list_index} from row(link index) {index}")
        links_list.remove(item.link)
        for i in range(index, len(links_list)):
            links_list[i].list_index = i

    def get_copy(self, original: DLGLink) -> DLGLink | None:
        """Retrieve the copy of the original object using the weak reference."""
        assert self.editor is not None
        for orig_ref, copiedLink in self.origToOrphanCopy.items():
            if orig_ref() is not original:
                continue
            return copiedLink
        return None

    def loadDLGItemRec(self, itemToLoad: DLGStandardItem, copiedLink: DLGLink | None = None):
        """Loads a DLGLink recursively getting all its nested items integrated into the model.

        Do NOT emit itemChanged or dataChanged after this function runs: we handle all of that here.
        """
        assert itemToLoad.link is not None
        assert itemToLoad.link.node is not None
        assert self.editor is not None
        self.linkToItems.setdefault(itemToLoad.link, []).append(itemToLoad)
        self.nodeToItems.setdefault(itemToLoad.link.node, []).append(itemToLoad)

        def register_deepcopies(origLink: DLGLink, copyLink: DLGLink, seenLinks: set[DLGLink] | None = None) -> weakref.ref[DLGLink[Any]] | None:
            """Recursively register deepcopies of nested links to avoid redundant deepcopies."""
            if seenLinks is None:
                seenLinks = set()
            if copyLink in seenLinks:
                return None
            seenLinks.add(copyLink)
            assert origLink is not copyLink
            orig_link_ref = weakref.ref(origLink)
            self.origToOrphanCopy[orig_link_ref] = copyLink
            for childOrigLink, childCopyLink in zip(origLink.node.links, copyLink.node.links):
                register_deepcopies(childOrigLink, childCopyLink, seenLinks)
            return orig_link_ref

        child_links_copy: Sequence[DLGLink | None] = [None]
        if copiedLink is None:
            copiedLink = self.origToOrphanCopy.get(itemToLoad._link_ref)
            if copiedLink is None:
                RobustRootLogger().info(f"Creating new internal copy of {itemToLoad.link!r}")
                copiedLink = DLGLink.from_dict(itemToLoad.link.to_dict())
                register_deepcopies(itemToLoad.link, copiedLink)
            child_links_copy = [None] * len(itemToLoad.link.node.links)
        else:
            assert copiedLink.node is not None
            child_links_copy = copiedLink.node.links

        assert itemToLoad.link is not copiedLink  # new copies should be made before loadDLGItemRec to reduce complexity.
        parent_path = itemToLoad.data(_LINK_PARENT_NODE_PATH_ROLE)
        potential_orphan = itemToLoad.link.node

        # Ensure there is no existing finalizer for the potential orphan node
        finalize_registry = weakref.finalize._registry
        if not any(info.weakref() is potential_orphan for info in finalize_registry.values()):
            print(f"Creating finalizer for {potential_orphan!r}")
            weakref.finalize(potential_orphan, self.onOrphanedNode, copiedLink, parent_path)

        self.updateItemData(itemToLoad)
        alreadyListed = itemToLoad.link in self.linkToItems or itemToLoad.link.node in self.nodeToItems
        if not alreadyListed:
            for child_link, child_link_copy in zip(itemToLoad.link.node.links, child_links_copy):
                child_item = DLGStandardItem(link=child_link)
                self.loadDLGItemRec(child_item, child_link_copy)
                child_item.setData(itemToLoad.link.node.path(), _LINK_PARENT_NODE_PATH_ROLE)
                itemToLoad.appendRow(child_item)
        elif itemToLoad.link.node.links:
            self.setItemFutureExpand(itemToLoad)

    def manageLinksList(
        self,
        node: DLGNode,
        link: DLGLink,
        *,
        add: bool = True,
    ):
        """Manage DLGLink.node.links and DLGLink.list_index."""
        if add:
            node.links.append(link)
            print(f"<SDM> [manageLinksList scope] link.list_index: {link.list_index} --> {len(node.links) - 1}")
            link.list_index = len(node.links) - 1

        elif link in node.links:
            index = node.links.index(link)  # Find the index of the link to be removed
            node.links.remove(link)
            # Update list_index for remaining links
            for list_index, child_link in enumerate(node.links[index:], start=index):
                child_link.list_index = list_index
                print("<SDM> [manageLinksList scope] child_link.list_index: ", child_link.list_index)

    def setItemFutureExpand(self, item: DLGStandardItem):
        """Creates a dummy item, with specific information that tells onItemExpanded how to expand when the user attempts to do so.

        This prevents infinite recursion while still giving the impression that multiple copies are in fact the same.
        """
        dummy_child = QStandardItem("Loading...")
        dummy_child.setData(True, _FUTURE_EXPAND_ROLE)
        item.appendRow(dummy_child)
        self.treeView.collapse(item.index())
        self.treeView.expand(item.index())

    def addRootNode(self):
        """Adds a root node to the dialog graph."""
        assert self.editor is not None
        newLink: DLGLink = DLGLink(DLGEntry())
        newLink.node.list_index = self._getNewNodeListIndex(newLink.node)
        self.appendRow(DLGStandardItem(link=newLink))
        print("<SDM> [_coreAddNode scope] newLink: ", newLink)
        print("<SDM> [_coreAddNode scope] newLink.list_index: ", newLink.list_index)
        print("<SDM> [_coreAddNode scope] newLink.node.list_index: ", newLink.node.list_index)

    def addChildToItem(self, parentItem: DLGStandardItem, link: DLGLink | None = None) -> DLGStandardItem:
        """Helper method to update the UI with the new link."""
        if link is None:
            newNode = DLGEntry() if isinstance(parentItem.link.node, DLGReply) else DLGReply()
            newNode.list_index = self._getNewNodeListIndex(newNode)
            link = DLGLink(newNode)
        newItem = DLGStandardItem(link=link)
        self.updateItemData(newItem)
        parentItem.appendRow(newItem)
        return newItem

    def _linkCoreNodes(self, target: DLGNode, source: DLGNode) -> DLGLink:
        """Helper method to add a source node to a target node."""
        newLink: DLGLink = DLGLink(source)
        print("<SDM> [_linkCoreNodes scope] newLink: ", newLink)

        newLink.list_index = len(target.links)
        print("<SDM> [_linkCoreNodes scope] newLink.list_index: ", newLink.list_index)

        target.links.append(newLink)
        return newLink

    def copyLinkAndNode(self, link: DLGLink | None):
        if link is None:
            return
        QApplication.clipboard().setText(json.dumps(link.to_dict()))

    def pasteItem(
        self,
        parentItem: DLGStandardItem | Self | None,
        pastedLink: DLGLink | None = None,
        *,
        row: int | None = None,
        asNewBranches: bool = True,
    ):
        """Paste a node from the clipboard to the parent node."""
        assert self.editor is not None
        pastedLink = self.editor._copy if pastedLink is None else pastedLink  # noqa: SLF001
        assert pastedLink is not None
        assert pastedLink.node is not None

        self.layoutAboutToBeChanged.emit()
        all_entries: set[int] = {entry.list_index for entry in self.editor.core_dlg.all_entries()}
        all_replies: set[int] = {reply.list_index for reply in self.editor.core_dlg.all_replies()}
        if asNewBranches:
            new_index = self._getNewNodeListIndex(pastedLink.node, all_entries, all_replies)
            print(f"<SDM> [_integrateChildNodes scope] pastedNode.list_index: {pastedLink.node.list_index} --> {new_index}")
            pastedLink2 = DLGLink.from_dict(pastedLink.to_dict())
            assert pastedLink == pastedLink2
            assert id(pastedLink) != id(pastedLink2)
            pastedLink2._hash_cache = hash(uuid.uuid4().hex)  # noqa: SLF001
            assert pastedLink != pastedLink2
            pastedLink = pastedLink2
            assert pastedLink.node is not None
            pastedLink.node.list_index = new_index

        assert pastedLink.node is not None
        queue: list[DLGNode] = [pastedLink.node]
        visited: set[DLGNode] = set()
        while queue:
            curNode = queue.pop(0)
            if curNode in visited:
                continue
            visited.add(curNode)
            if asNewBranches or curNode not in self.nodeToItems:
                new_index = self._getNewNodeListIndex(curNode, all_entries, all_replies)
                print(f"<SDM> [_integrateChildNodes scope] curNode.list_index: {curNode.list_index} --> {new_index}")
                curNode.list_index = new_index

            queue.extend(
                [
                    link.node
                    for link in curNode.links
                    if link.node is not None
                ]
            )

        if asNewBranches:
            for node in list(visited):
                node._hash_cache = hash(uuid.uuid4().hex)  # noqa: SLF001

        if parentItem is None:
            parentItem = self
            parentLinksList = self.editor.core_dlg.starters
        else:
            parentLinksList = parentItem.link.node.links
        newItem = DLGStandardItem(link=pastedLink)
        if row not in (-1, None, parentItem.rowCount()):
            #parentLinksList.insert(row, pastedLink)
            parentItem.insertRow(row, newItem)
        else:
            #parentLinksList.append(pastedLink)
            parentItem.appendRow(newItem)
        self.blockSignals(True)
        self.updateItemData(newItem)
        if pastedLink in self.linkToItems:
            self.setItemFutureExpand(newItem)
        else:
            self.loadDLGItemRec(newItem)
        if isinstance(parentItem, DLGStandardItem):
            assert parentItem.link is not None
            self.updateItemData(parentItem)
            self._updateCopies(parentItem.link, parentItem)
        self.treeView.expand(newItem.index())
        self.blockSignals(False)
        self.layoutChanged.emit()
        self.treeView.viewport().update()
        self.treeView.update()

    def _getNewNodeListIndex(
        self,
        node: DLGNode,
        entryIndices: set[int] | None = None,
        replyIndices: set[int] | None = None,
    ) -> int:
        """Generate a new unique list index for the node."""
        assert self.editor is not None
        if isinstance(node, DLGEntry):
            indices = {entry.list_index for entry in self.editor.core_dlg.all_entries()} if entryIndices is None else entryIndices
        elif isinstance(node, DLGReply):
            indices = {reply.list_index for reply in self.editor.core_dlg.all_replies()} if replyIndices is None else replyIndices
        else:
            raise TypeError(node.__class__.__name__)
        new_index = max(indices, default=-1) + 1
        print("<SDM> [_getNewNodeListIndex scope] new_index: ", new_index)

        while new_index in indices:
            new_index += 1
        indices.add(new_index)
        return new_index

    def itemFromIndex(self, index: QModelIndex) -> DLGStandardItem | None:
        item = super().itemFromIndex(index)
        if item is None:
            return None
        assert isinstance(item, DLGStandardItem)
        return item

    def deleteNodeEverywhere(self, node: DLGNode):
        """Removes all occurrences of a node and all links to it from the model and self.editor.core_dlg."""
        assert self.editor is not None
        self.layoutAboutToBeChanged.emit()

        def removeLinksRecursive(node_to_remove: DLGNode, parentItem: DLGStandardItem | DLGStandardItemModel):
            assert self.editor is not None
            for i in reversed(range(parentItem.rowCount())):
                child_item = parentItem.child(i, 0) if isinstance(parentItem, DLGStandardItem) else parentItem.item(i, 0)
                if child_item is None:
                    continue
                if not isinstance(child_item, DLGStandardItem):
                    continue
                if child_item.link is None:
                    continue
                if child_item.data(_FUTURE_EXPAND_ROLE):
                    continue
                if child_item.isDeleted():
                    continue
                if child_item.link.node == node_to_remove:
                    removeLinksRecursive(child_item.link.node, child_item)  # type: ignore[]
                    parentItem.removeRow(i)
                else:
                    removeLinksRecursive(node_to_remove, child_item)

        removeLinksRecursive(node, self)
        self.layoutChanged.emit()

    def deleteNode(self, item: DLGStandardItem):
        """Deletes a node from the DLG and ui tree model."""
        parent: DLGStandardItem | None = item.parent()
        if parent is None:
            self.removeRow(item.row())
        else:
            parent.removeRow(item.row())
            assert parent.link is not None
            self._updateCopies(parent.link, parent)

    def updateItemData(self, item: DLGStandardItem):
        """Refreshes the item text and formatting based on the node data."""
        assert item.link is not None
        assert item.link.node is not None
        assert self.editor is not None
        color: QColor | None = None
        if isinstance(item.link.node, DLGEntry):
            color = QColor(self.editor.dlg_settings.get("entryTextColor", QColor(255, 0, 0)))  # if not _isCopy else QColor(210, 90, 90)
            prefix = "E"
        elif isinstance(item.link.node, DLGReply):
            color = QColor(self.editor.dlg_settings.get("replyTextColor", QColor(0, 0, 255)))  # if not _isCopy else QColor(90, 90, 210)
            prefix = "R"
        else:
            raise TypeError(f"Node must be DLGEntry/DLGReply, but was instead {item.link.node.__class__.__name__}")
        list_prefix = f"<b>{prefix}{item.link.node.list_index}:</b> "
        text = str(item.link.node.text) if self.editor._installation is None else self.editor._installation.string(item.link.node.text, "")  # noqa: SLF001
        if not item.link.node.links:
            display_text = f"{text} <span style='color:{QColor(255, 127, 80).name()};'><b>[End Dialog]</b></span>"
        elif not text and not text.strip():
            if item.link.node.text.stringref == -1:
                display_text = "(continue)"
                tooltip_text = (
                    "<i>No text set.<br><br>"
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
        assert color is not None
        item.setData(f'<span style="color:{color.name()}; font-size:{self.treeView.text_size}pt;">{list_prefix}{display_text}</span>', Qt.ItemDataRole.DisplayRole)
        item.setForeground(QBrush(color))

    def isCopy(self, item: DLGStandardItem) -> bool:
        """Determine if the item is already loaded into the tree, or if it's collapsed until onItemExpanded is called."""
        if not item.hasChildren():
            return False
        return item.child(0, 0).data(_FUTURE_EXPAND_ROLE) is True

    def deleteSelectedNode(self):
        """Deletes the currently selected node from the tree."""
        if self.treeView.selectedIndexes():
            index: QModelIndex = self.treeView.selectedIndexes()[0]
            print("<SDM> [deleteSelectedNode scope] self.treeView.selectedIndexes()[0]: ", index.row())

            item: DLGStandardItem | None = self.itemFromIndex(index)
            print("<SDM> [deleteSelectedNode scope] item: ", item)

            assert item is not None
            self.deleteNode(item)

    def moveItemToIndex(
        self,
        item: DLGStandardItem,
        new_index: int,
        targetParentItem: DLGStandardItem | None = None,
    ):
        """Move an item to a specific index within the model."""
        assert self.editor is not None
        sourceParentItem: DLGStandardItem | None = item.parent()

        # Early return if the move operation doesn't make sense
        if targetParentItem is sourceParentItem and new_index == item.row():
            self.editor.blinkWindow()
            RobustRootLogger().info("Attempted to move item to the same position. Operation aborted.")
            return
        if (
            targetParentItem is not sourceParentItem
            and targetParentItem is not None
            and sourceParentItem is not None
            and targetParentItem.link is not None
            and sourceParentItem.link is not None
            and targetParentItem.link.node == sourceParentItem.link.node
        ):
            self.editor.blinkWindow()
            RobustRootLogger().warning("Cannot drag into a different copy, aborting.")
            return

        # source and target items must be loaded.
        if (
            sourceParentItem is not None and sourceParentItem.data(_FUTURE_EXPAND_ROLE)
            or targetParentItem is not None and targetParentItem.data(_FUTURE_EXPAND_ROLE)
        ):
            self.editor.blinkWindow()
            RobustRootLogger().info("Cannot drag into a future expand dummy, aborting.")
            return

        # Ensure copies are expanded first.
        if (
            targetParentItem is not None
            and targetParentItem.hasChildren()
            and targetParentItem.child(0, 0).data(_FUTURE_EXPAND_ROLE)
        ):
            if targetParentItem.index().isValid():
                self.treeView.expand(targetParentItem.index())
            else:
                assert self.editor is not None
                self.editor._logger.error("targetParentItem at row %s is invalid, cannot move item.", targetParentItem.row())  # noqa: SLF001
                return

        if new_index < 0 or new_index > (targetParentItem or self).rowCount():
            RobustRootLogger().info("New row index %d out of bounds. Cancelling operation.", new_index)
            return

        oldRow: int = item.row()
        if sourceParentItem is targetParentItem and new_index > oldRow:
            new_index -= 1

        # don't call this, i've no idea why this crashes, perhaps it's made for some other widget.
        #self.beginMoveRows( QModelIndex() if oldParent is None else oldParent.index(), oldRow, oldRow, QModelIndex() if targetParentItem is None else targetParentItem.index(), new_index, )
        self._isMoving = True
        itemToMove = (sourceParentItem or self).takeRow(oldRow)[0]
        if targetParentItem is not None:
            assert targetParentItem.link is not None
            self.updateItemData(targetParentItem)
            targetParentItem.insertRow(new_index, itemToMove)
            self._updateCopies(targetParentItem.link, targetParentItem)
        else:
            self.insertRow(new_index, itemToMove)
        # don't call this, i've no idea why this crashes, perhaps it's made for some other widget.
        #self.endMoveRows()
        self._isMoving = False


    def _updateCopies(self, link: DLGLink, itemToIgnore: DLGStandardItem | None = None):
        if link.node is None:
            assert self.editor is not None
            self.editor.blinkWindow()
            return
        if link.node not in self.nodeToItems:
            return

        item = None
        items = self.nodeToItems[link.node]
        print(f"Updating {len(items)} total item(s) containing node {link.node}")
        for item in items:
            if item is itemToIgnore:
                continue
            self.blockSignals(True)
            self.updateItemData(item)
            if item.hasChildren() and item.child(0, 0).data(_FUTURE_EXPAND_ROLE):  # Item's children not loaded.
                continue
            item.removeRows(0, item.rowCount())
            self.blockSignals(False)
            self.setItemFutureExpand(item)

    def shiftItem(
        self,
        item: DLGStandardItem,
        amount: int,
        *,
        noSelectionUpdate: bool = False,
    ):
        """Shifts an item in the tree by a given amount."""
        itemText = item.text()
        print("<SDM> [shiftItem scope] itemText: ", itemText)

        oldRow: int = item.row()
        print("<SDM> [shiftItem scope] oldRow: ", oldRow)

        itemParent = item.parent()
        print("<SDM> [shiftItem scope] itemParent: ", itemParent)

        newRow: int = oldRow + amount
        print("<SDM> [shiftItem scope] newRow: ", newRow)

        itemParentText = "" if itemParent is None else itemParent.text()

        print("Received item: '%s', row shift amount %s", itemText, amount)
        print("Attempting to change row index for '%s' from %s to %s in parent '%s'", itemText, oldRow, newRow, itemParentText)

        if newRow >= (itemParent or self).rowCount() or newRow < 0:
            RobustRootLogger().info("New row index '%s' out of bounds. Already at the start/end of the branch. Cancelling operation.", newRow)
            return

        # don't call this, i've no idea why this crashes, perhaps it's made for some other widget.
        #self.beginMoveRows( QModelIndex() if itemParent is None else itemParent.index(), oldRow, oldRow, QModelIndex() if itemParent is None else itemParent.index(), newRow if newRow > oldRow else newRow + 1 )
        self._isMoving = True
        itemToMove = (itemParent or self).takeRow(oldRow)[0]
        print("<SDM> [shiftItem scope] itemToMove: ", itemToMove)

        print("itemToMove '%s' taken from old position: '%s', moving to '%s'", itemToMove.text(), oldRow, newRow)
        (itemParent or self).insertRow(newRow, itemToMove)
        # don't call this, i've no idea why this crashes, perhaps it's made for some other widget.
        #self.endMoveRows()
        self._isMoving = False
        selectionModel = self.treeView.selectionModel()
        if selectionModel is not None and not noSelectionUpdate:
            selectionModel.select(itemToMove.index(), QItemSelectionModel.ClearAndSelect)
            print("Selection updated to new index")

        itemParent = itemToMove.parent()
        print("<SDM> [shiftItem scope] itemParent: ", itemParent)
        print("Item new parent after move: '%s'", itemParent.text() if itemParent else "Root")
        if isinstance(itemParent, DLGStandardItem):
            assert itemParent.link is not None
            self._updateCopies(itemParent.link, itemParent)

        RobustRootLogger().info("Moved link from %s to %s", oldRow, newRow)
        self.layoutChanged.emit()


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
        self.parentIndex: QModelIndex = parent
        self.row: int = row
        self.position: DropPosition = position
        self.indicator_rect: QRect = QRect() if indicator_rect is None else indicator_rect

    @classmethod
    def determineDropTarget(
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
            #print(f"ABOVE cur index: {view.getIdentifyingText(curIndex)}")
            return cls(curIndex.parent(), max(curIndex.row(), 0), DropPosition.ABOVE, indicator_rect)
        if pos.y() >= lower_threshold:
            # Adjust for bottom edge of the index
            indicator_rect = QRect(rect.bottomLeft(), rect.bottomRight())
            #print(f"BELOW cur index: {view.getIdentifyingText(curIndex)}")
            return cls(curIndex.parent(), curIndex.row()+1, DropPosition.BELOW, indicator_rect)

        #print(f"ON TOP OF cur index: {view.getIdentifyingText(curIndex)}")
        return cls(curIndex, curIndex.row(), DropPosition.ON_TOP_OF, rect)

    def is_valid_drop(self, dragged_link: DLGLink, view: DLGTreeView) -> bool:
        if self.position is DropPosition.INVALID or self.row == -1:
            print("Drop operation invalid: target row is -1 or position is invalid.")
            return False

        if self.parentIndex.isValid():
            rootItemIndex = None
            parentItem = view.model().itemFromIndex(self.parentIndex)
        else:
            rootItemIndex = view.model().index(self.row, 0)
            if not rootItemIndex.isValid():
                if self.position is DropPosition.BELOW:
                    aboveTestIndex = view.model().index(min(0, self.row-1), 0)
                    if aboveTestIndex.isValid():
                        rootItemIndex = aboveTestIndex
                else:
                    print(f"Root item at row '{self.row}' is invalid.")
                    return False
            parentItem = view.model().itemFromIndex(rootItemIndex)
        dragged_node = dragged_link.node
        assert dragged_node is not None
        assert parentItem is not None
        assert parentItem.link is not None
        assert parentItem.link.node is not None
        node_types_match = view.bothNodesSameType(dragged_node, parentItem.link.node)
        if self.position is DropPosition.ON_TOP_OF:
            node_types_match = not node_types_match

        if ((self.position is DropPosition.ON_TOP_OF) == node_types_match) == (rootItemIndex is not None):
            print(f"Drop operation invalid: {self.position.name} vs node type check.")
            return False

        print("Drop operation is valid.")
        return True


def install_immediate_tooltip(widget: QWidget, tooltip_text: str):
    widget.setToolTip(tooltip_text)
    widget.setMouseTracking(True)
    widget.event = lambda event: QToolTip.showText(cast(QHoverEvent, event).pos(), widget.toolTip(), widget)  # type: ignore[method-assign]


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
        if init_dict is not None:
            if isinstance(init_dict, Mapping):
                for k, v in init_dict.items():
                    if isinstance(k, tuple):
                        k, v = k
                    self[k] = v
            else:
                for k, v in init_dict:
                    self[k] = v

    def __setitem__(self, key: DLGLink | weakref.ref[DLGLink], value: DLGLinkSync | DLGLink):
        if isinstance(key, weakref.ref):
            ref = key
            key = key()
            if key is None:
                raise ValueError("Ref passed to CopySyncDict is already garbage collected.")
            key_hash = hash(key)
        else:
            key_hash = hash(key)
            ref = weakref.ref(key, self._remove_key(key_hash))
        # doesn't seem to be needed
        #object.__setattr__(value, "__class__", DLGLinkSync)
        #object.__setattr__(value, "_syncer", self)
        self._storage[key_hash] = (ref, value)
        self._weak_key_map[key_hash] = ref

    def __getitem__(self, key: DLGLink) -> DLGLink[Any]:
        key_hash = hash(key)
        if key_hash in self._storage:
            return self._storage[key_hash][1]
        raise KeyError(key)

    def __delitem__(self, key: DLGLink):
        key_hash = hash(key)
        del super()[self._storage[key_hash][0]]
        del self._storage[key_hash]
        del self._weak_key_map[key_hash]

    def get(self, key: DLGLink, default: DLGLink = None) -> DLGLink:  # type: ignore[override]
        lookupOrig, lookupCopy = self._storage.get(hash(key), (None, None))
        if lookupOrig is None:
            return default  # copy would also be None
        lookup = lookupOrig()
        if lookup is None:
            if lookupCopy is None:
                return default
            return lookupCopy
        return default

    def _remove_key(self, key_hash: int) -> Callable[..., None]:
        def remove(_):
            del self[self._storage[key_hash][1]]
        return remove

    def values(self) -> Generator[Any, None, None]:
        return (item for _, item in self._storage.values())

    def items(self) -> Generator[tuple[weakref.ref[DLGLink], DLGLink], None, None]:
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
            RobustRootLogger().info(f"Creating deepcopy of {link!r}")
            self[link] = DLGLink.from_dict(link.to_dict())
        return self._weak_key_map[link_hash]


class DLGTreeView(RobustTreeView):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.override_drop_in_view: bool = True  # set to False to use the new logic (not recommended - untested)
        self.editor: DLGEditor | None = None
        self.dropIndicatorRect: QRect = QRect()
        self.maxDragTextSize: int = 40
        self.num_links: int = 0
        self.num_unique_nodes: int = 0
        self.draggedItem: DLGStandardItem | None = None
        self.draggedLink: DLGLink | None = None
        self.dropTarget: DropTarget | None = None
        self.startPos: QPoint = QPoint()
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDropIndicatorShown(False)  # We have our own.
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        #self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove | QAbstractItemView.DragDropMode.DragDrop)

    def model(self) -> DLGStandardItemModel | None:
        model = super().model()
        if model is None:
            return None
        assert isinstance(model, DLGStandardItemModel), f"model was {model} of type {model.__class__.__name__}"
        return model

    def paintEvent(self, event: QPaintEvent):
        super().paintEvent(event)
        if self.dropIndicatorRect.isNull():
            return

        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.Antialiasing)
        if self.dropIndicatorRect.topLeft().y() == self.dropIndicatorRect.bottomLeft().y():
            pen = QPen(Qt.black, 1, Qt.DashLine)
            painter.setPen(pen)
            painter.drawLine(self.dropIndicatorRect.topLeft(), self.dropIndicatorRect.topRight())
        else:
            highlight_color = QColor(200, 200, 200, 120)
            painter.fillRect(self.dropIndicatorRect, highlight_color)

        painter.end()

    def keyPressEvent(self, event: QKeyEvent):
        print("<SDM> [DLGTreeView.keyPressEvent scope] key: %s", getQtKeyString(event.key()))
        assert self.editor is not None
        self.editor.keyPressEvent(event, isTreeViewCall=True)
        super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if (
            event.button() == Qt.LeftButton
            and self.startPos.isNull()
        ):
            self.startPos = event.pos()
            print("<SDM> [mousePressEvent scope] self.startPos: ", self.startPos)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if (
            bool(event.buttons() & Qt.LeftButton)
            and not self.startPos.isNull()
            and (event.pos() - self.startPos).manhattanLength() >= QApplication.startDragDistance()
            and self.draggedItem is None
        ):
            # finally figured out how to get qt to do this part.
            # leave here in case we need again
            #if self.prepareDrag(self.indexAt(self.startPos)):
            #    print(f"{self.__class__.__name__}.mouseMoveEvent picked up a drag")
            #    self.performDrag()
            #else:
            #    self.resetDragState()
            super().mouseMoveEvent(event)
        super().mouseMoveEvent(event)


    # region Tree Drag&Drop
    def createDragPixmap(self, dragged_item: DLGStandardItem) -> QPixmap:
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
            link_list_display = "EntriesList" if isinstance(dragged_item.link.node, DLGEntry) else "RepliesList"
            node_list_display = "EntryList" if isinstance(dragged_item.link.node, DLGEntry) else "ReplyList"
        assert dragged_item.link is not None
        assert dragged_item.link.node is not None
        display_text = f"{link_list_display}\\{dragged_item.link.list_index} --> {node_list_display}\\{dragged_item.link.node.list_index}"

        html_content = f"""
        <div style="color: {color}; font-size: {self.text_size}pt;">
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
        gradient = QRadialGradient(center, radius)
        gradient.setColorAt(0, QColor(255, 255, 255, 200))
        gradient.setColorAt(0.5, color.lighter())
        gradient.setColorAt(1, color)
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, radius, radius)
        painter.setPen(QColor(0, 0, 0))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        text_rect = QRect(center.x() - radius, center.y() - radius, radius * 2, radius * 2)
        painter.drawText(text_rect, Qt.AlignCenter, text)
        print(f"{self.__class__.__name__}.draw_drag_icons: Drawing drag icon at {center} with text {text}")  # noqa: SLF001

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
            queue.extend(link.node for link in node.links if link.node is not None)

        self.num_unique_nodes = len(seen_nodes)
        print("<SDM> [calculate_links_and_nodes scope] self.num_unique_nodes: ", self.num_unique_nodes)
        return self.num_links, self.num_unique_nodes

    def performDrag(self):
        print("performDrag: Post-initiate drag operation, call drag.exec_()")
        assert self.draggedItem is not None
        draggedIndex = self.draggedItem.index()
        drag = QDrag(self)
        drag.setMimeData(self.model().mimeData([draggedIndex]))
        pixmap = self.createDragPixmap(self.draggedItem)
        drag.setPixmap(pixmap)
        item_top_left_global = self.mapToGlobal(self.visualRect(draggedIndex).topLeft())
        drag.setHotSpot(QPoint(pixmap.width() // 2, QCursor.pos().y() - item_top_left_global.y()))
        drag.exec_(self.model().supportedDragActions())
        print("\nperformDrag: completely done")

    def prepareDrag(self, index: QModelIndex | None = None, event: QDragEnterEvent | QDragMoveEvent | QDropEvent | None = None) -> bool:
        print(f"{self.__class__.__name__}.\nprepareDrag(index={index}, event={event})")
        if self.draggedItem is not None:
            return True

        if event:
            print("prepareDrag: check for mimeData")
            if not event.mimeData().hasFormat(QT_STANDARD_ITEM_FORMAT):
                print("prepareDrag: not our mimeData format.")
                return False
            if id(event.source()) == id(self.model()):
                print("drag is happening from exact QTreeView instance.")
                return True
            item_data = self.parseMimeData(event.mimeData())
            if item_data[0]["roles"][_MODEL_INSTANCE_ID_ROLE] != id(self.model()):
                print("prepareDrag: drag event started in another window.")
                return True
            print("prepareDrag: drag originated from some list widget.")
            deserialized_listwidget_link: DLGLink = DLGLink.from_dict(json.loads(item_data[0]["roles"][_DLG_MIME_DATA_ROLE]))
            temp_item = DLGStandardItem(link=deserialized_listwidget_link)
            self.model().updateItemData(temp_item)
            self.draggedItem = self.model().linkToItems.setdefault(deserialized_listwidget_link, [temp_item])[0]
            assert self.draggedItem.link is not None
            assert self.draggedItem.link.node is not None
            self.calculate_links_and_nodes(self.draggedItem.link.node)
            return True

        if index is None:
            index = self.currentIndex()

        dragged_item = self.model().itemFromIndex(index)
        assert isinstance(dragged_item, DLGStandardItem)
        if not dragged_item or not hasattr(dragged_item, "link") or dragged_item.link is None:
            print(f"{self.getIdentifyingText(index)}")
            print("Above item does not contain DLGLink information\n")
            return False

        self.draggedItem = dragged_item
        assert self.draggedItem.link is not None
        assert self.draggedItem.link.node is not None
        self.calculate_links_and_nodes(self.draggedItem.link.node)
        return True

    def startDrag(self, supportedActions: Qt.DropActions | Qt.DropAction):
        print("\nstartDrag: Initiate the drag operation, call self.prepareDrag")
        if not self.prepareDrag():
            print("startDrag called but prepareDrag returned False, resetting the drag state.")
            self.resetDragState()
            return
        mode = 2
        if mode == 1:
            super().startDrag(supportedActions)
        elif mode == 2:
            self.performDrag()
        print("startDrag done, call resetDragState")
        self.resetDragState()

    def dragEnterEvent(self, event: QDragEnterEvent):
        print(f"\ndragEnterEvent(event={event})")
        if not event.mimeData().hasFormat(QT_STANDARD_ITEM_FORMAT):
            print("dragEnterEvent mimeData does not match our format, invalidating.")
            self.setInvalidDragDrop(event)
            return
        if not self.draggedItem:
            RobustRootLogger().warning("dragEnterEvent called before prepareDrag, rectifying.")
            if not self.prepareDrag(event=event):
                print("dragEnterEvent: prepareDrag returned False, resetting the drag state.")
                self.setInvalidDragDrop(event)
                self.resetDragState()
                return
        self.setValidDragDrop(event)

    def dragMoveEvent(self, event: QDragMoveEvent):
        print(f"dragMoveEvent(event={event})")
        if not event.mimeData().hasFormat(QT_STANDARD_ITEM_FORMAT):
            self.setInvalidDragDrop(event)
            super().dragMoveEvent(event)
            return

        print("<SDM> [dragMoveEvent scope], event mimedata matches our format.")
        if self.draggedItem is not None:
            assert self.draggedItem.link is not None
            self.draggedLink = self.draggedItem.link
        elif self.draggedLink is None:
            RobustRootLogger().error("dragMoveEvent called before prepareDrag. This is an error/oversight: dragEnterEvent should have picked this up first. rectifying now....")
            if not self.prepareDrag(event=event):
                self.setInvalidDragDrop(event)
                super().dragMoveEvent(event)
                return
            self.draggedLink = self.getDraggedLinkFromMimeData(event.mimeData())
            if self.draggedLink is None:
                RobustRootLogger().error("Could not deserialize DLGLink from mime data despite it matching our format")
                self.setInvalidDragDrop(event)
                super().dragMoveEvent(event)
                return

        if self.dropTarget is not None:
            self.itemDelegate().nudgedModelIndexes.clear()

        pos: QPoint = event.pos()
        self.dropTarget = DropTarget.determineDropTarget(self, pos)
        self.dropIndicatorRect = self.dropTarget.indicator_rect
        if not self.dropTarget.is_valid_drop(self.draggedLink, self):
            print(f"{self.__class__.__name__}.dragMoveEvent: Target at mouse position is not valid.")
            self.setInvalidDragDrop(event)
            super().dragMoveEvent(event)
            return
        aboveIndex = self.model().index(self.dropTarget.row-1, 0, self.dropTarget.parentIndex)
        hoverOverIndex = self.model().index(self.dropTarget.row, 0, self.dropTarget.parentIndex)
        if (
            self.dropTarget.position in (DropPosition.ABOVE, DropPosition.BELOW)
            and self.draggedItem is not None
            and (
                self.draggedItem.isDeleted()
                or hoverOverIndex is not self.draggedItem.index()
            )
        ):
            self.itemDelegate().nudgeItem(hoverOverIndex, 0, int(self.itemDelegate().text_size/2))
            self.itemDelegate().nudgeItem(aboveIndex, 0, int(-self.itemDelegate().text_size/2))

        self.setValidDragDrop(event)
        super().dragMoveEvent(event)

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        self.itemDelegate().nudgedModelIndexes.clear()

    def dropEvent(self, event: QDropEvent):
        if self.override_drop_in_view:
            # Always set invalid so qt won't try to handle it past this function.
            self.setInvalidDragDrop(event)
        if not event.mimeData().hasFormat(QT_STANDARD_ITEM_FORMAT):
            print("<SDM> [dropEvent scope] event does not match our format")
            self.resetDragState()
            return
        if self.dropTarget is None:
            print("dropTarget is none in dropEvent")
            self.resetDragState()
            return

        self.itemDelegate().nudgedModelIndexes.clear()
        if self.dropTarget.parentIndex.isValid():
            dropParent = self.model().itemFromIndex(self.dropTarget.parentIndex)
        else:
            dropParent = None

        if not self.isItemFromCurrentModel(event):
            if self.override_drop_in_view:
                print("<SDM> [dropEvent scope] not self.isItemFromCurrentModel(event), calling pasteItem")
                dragged_link: DLGLink | None = self.getDraggedLinkFromMimeData(event.mimeData()) if self.draggedLink is None else self.draggedLink
                if dragged_link:
                    if not self.dropTarget.is_valid_drop(dragged_link, self):
                        print("dropEvent: dropTarget is not valid (for a pasteItem)")
                        self.resetDragState()
                        return
                    self.model().pasteItem(dropParent, dragged_link, row=self.dropTarget.row, asNewBranches=False)
                    super().dropEvent(event)
                else:
                    print("<SDM> [dropEvent scope] could not call pasteItem: dragged_node could not be deserialized from mime data.")
            super().dropEvent(event)
            self.resetDragState()
            return

        if not self.draggedItem:
            print("<SDM> [dropEvent scope] self.draggedItem is somehow None")
            self.resetDragState()
            return

        if not self.dropTarget.is_valid_drop(self.draggedItem.link, self):
            print("dropEvent: self.dropTarget is not valid (for a moveItemToIndex)")
            self.resetDragState()
            return
        #if self.override_drop_in_view:
        self.setInvalidDragDrop(event)
        new_index = self.dropTarget.row
        if self.dropTarget.position is DropPosition.ON_TOP_OF:
            new_index = 0
        # if uncommenting here, also uncomment in moveItemToIndex.
        # This was put here because this block might be needed instead of the droppedAtRow position check below.
        # if self.draggedItem.parent() is dropParent and new_index > self.draggedItem.row():
        #     new_index -= 1
        print("Dropping OUR TreeView item into another part of the treeview: call moveItemToIndex")
        self.model().moveItemToIndex(self.draggedItem, new_index, dropParent)
        super().dropEvent(event)
        parentIndexOfDrop, droppedAtRow = self.dropTarget.parentIndex, self.dropTarget.row
        if self.dropTarget.position is DropPosition.BELOW:
            droppedAtRow = min(droppedAtRow - 1, 0)
        self.resetDragState()
        self.setAutoScroll(False)
        #self.setSelectionOnDrop(droppedAtRow, parentIndexOfDrop)
        QTimer.singleShot(0, lambda: self.setSelectionOnDrop(droppedAtRow, parentIndexOfDrop))

    def setSelectionOnDrop(self, row: int, parentIndex: QModelIndex):
        print(f"setSelectionOnDrop(row={row})")
        self.clearSelection()
        if not parentIndex.isValid():
            print("setSelectionOnDrop: root item selected")
            droppedIndex = self.model().index(row, 0)
        else:
            droppedIndex = self.model().index(row, 0, parentIndex)
        if not droppedIndex.isValid():
            print("setSelectionOnDrop droppedIndex invalid")
            return
        self.selectionModel().setCurrentIndex(droppedIndex, QItemSelectionModel.Select | QItemSelectionModel.Rows)
        self.update()
        self.viewport().update()
        self.setState(QAbstractItemView.State.DragSelectingState)
        QTimer.singleShot(0, lambda: self.setState(QAbstractItemView.State.NoState))
        QTimer.singleShot(0, lambda: self.viewport().update())

    def getDraggedLinkFromMimeData(self, mimeData: QMimeData) -> DLGLink | None:
        try:
            return DLGLink.from_dict(json.loads(self.parseMimeData(mimeData)[0]["roles"][_DLG_MIME_DATA_ROLE]))
        except Exception:  # noqa: BLE001
            RobustRootLogger().exception("Failed to deserialize mime data node.")
        return None

    def isItemFromCurrentModel(self, event: QDropEvent) -> bool:
        if not isinstance(event.source(), DLGTreeView):
            print(f"isItemFromCurrentModel: Not our drag, QDropEvent.source() was of type '{event.source().__class__.__name__}'")
            return False
        return self.parseMimeData(event.mimeData())[0]["roles"][_MODEL_INSTANCE_ID_ROLE] == id(self.model())

    @staticmethod
    def parseMimeData(mimeData: QMimeData) -> list[dict[Literal["row", "column", "roles"], Any]]:
        items: list[dict[Literal["row", "column", "roles"], Any]] = []
        if mimeData.hasFormat(QT_STANDARD_ITEM_FORMAT):
            encoded_data = mimeData.data(QT_STANDARD_ITEM_FORMAT)
            stream = QDataStream(encoded_data, QIODevice.ReadOnly)

            while not stream.atEnd():
                item_data: dict[Literal["row", "column", "roles"], Any] = {}
                item_data["row"] = stream.readInt32()
                item_data["column"] = stream.readInt32()
                numRoles = stream.readInt32()

                roles: dict[int, Any] = {}
                for _ in range(numRoles):
                    role = stream.readInt32()
                    if role == Qt.DisplayRole:
                        roles[role] = stream.readQString()
                    elif role == _DLG_MIME_DATA_ROLE:
                        roles[role] = stream.readBytes().decode()
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
    def bothNodesSameType(dragged_node: DLGNode, target_node: DLGNode) -> bool:
        return (
            isinstance(dragged_node, DLGReply) and isinstance(target_node, DLGReply)
            or isinstance(dragged_node, DLGEntry) and isinstance(target_node, DLGEntry)
        )

    def resetDragState(self):
        print("<SDM> [resetDragState scope]")
        self.startPos = QPoint()
        self.draggedItem = None
        self.draggedLink = None
        self.dropIndicatorRect = QRect()
        self.dropTarget = None
        self.unsetCursor()
        self.viewport().update()

    def setInvalidDragDrop(
        self,
        event: QDropEvent | QDragEnterEvent | QDragMoveEvent,
    ):
        print("<SDM> [setInvalidDragDrop scope]")
        event.acceptProposedAction()
        event.setDropAction(Qt.DropAction.IgnoreAction)
        self.setCursor(Qt.CursorShape.ForbiddenCursor)
        self.viewport().update()
        QTimer.singleShot(0, lambda *args: self.setDragEnabled(True))

    def setValidDragDrop(
        self,
        event: QDropEvent | QDragEnterEvent | QDragMoveEvent,
    ):
        print("<SDM> [setValidDragDrop scope]")
        event.accept()
        event.setDropAction(Qt.DropAction.MoveAction if self.isItemFromCurrentModel(event) else Qt.DropAction.CopyAction)  # DropAction's are unused currently: the view is handling the drop.
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
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowTitleHint |
            Qt.WindowMinMaxButtonsHint |
            Qt.WindowCloseButtonHint
        )
        self._installation: HTInstallation

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.editors.dlg import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415  # type: ignore[assignment]
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.editors.dlg import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415  # type: ignore[assignment]
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.editors.dlg import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415  # type: ignore[assignment]
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.editors.dlg import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415  # type: ignore[assignment]
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self._copy: DLGLink | None = None
        self._focused: bool = False
        self.undoStack: QUndoStack = QUndoStack()

        self.ui: Ui_MainWindow = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setupDLGTreeMVC()
        self.dlg_settings: DLGSettings = DLGSettings()
        self.whatsThisToggle: bool = False
        self.original_tooltips: dict[QWidget, str] = {}
        self.ui.dialogTree.text_size = self.dlg_settings.fontSize(self.ui.dialogTree.text_size)

        self._setupSignals()
        self.setupPostUIElements()
        if installation:
            self._setupInstallation(installation)

        self.tips: list[str] = [
            "Use the 'View' and 'Settings' menu to customize dlg editor settings. All of your changes will be saved for next time you load the editor.",
            "Tip: Drag and Drop is supported, even between different DLGs!",
            "Tip: Accidentally closed something? Right click the Menu to reopen the dock panels.",
            "Tip: All Entry nodes must contain at least one Reply node, even a blank one is required to end the dialog."
            "Tip: Hold CTRL and scroll to change the text size.",
            "Tip: Hold ALT and scroll to change the indentation.",
            "Tip: Hold CTRL+SHIFT and scroll to change the vertical spacing.",
            "Tip: 'Delete all references' will delete all EntriesList/RepliesList/StartingList links to the node, leaving it orphaned.",
            "Tip: Drag any tree item to the left dockpanel to pin it for easy access",
            "Tip: Orphaned Nodes will automatically be added to the top left list and can be easily reintegrated by dragging back in."
        ]
        self.tipLabel: QLabel = QLabel()
        self.tipLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        font = self.tipLabel.font()
        font.setPointSize(10)
        self.tipLabel.setFont(font)
        self.tipsStartFromRightSide: bool = True
        self.statusBar().addPermanentWidget(self.tipLabel, 1)
        self.timer: QTimer = QTimer(self)
        self.timer.timeout.connect(self.showScrollingTip)
        self.timer.start(15000)

        self.voIdEditTimer: QTimer = QTimer(self)
        self.core_dlg: DLG = DLG(blank_node=False)

        self.tempFile: QTemporaryFile | None = None
        self.dialog_references = None
        self.reference_history: list[tuple[list[weakref.ref[DLGLink]], str]] = []
        self.current_reference_index = -1
        self._setupMenus()

        self.nodeLoadedIntoUI: bool = False
        self.keysDown: set[int] = set()

        # Debounce timer to delay a cpu-intensive task.
        self.voIdEditTimer.setSingleShot(True)
        self.voIdEditTimer.setInterval(500)  # 500 milliseconds delay
        self.voIdEditTimer.timeout.connect(self.populateComboboxOnVoIdEditFinished)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAllWhatsThis()
        self.setupExtraTooltipMode()
        self.new()

    def setupExtraTooltipMode(self, widget: QWidget | None = None):
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

    def revertTooltips(self):
        for widget, original_tooltip in self.original_tooltips.items():
            widget.setToolTip(original_tooltip)
        self.original_tooltips.clear()

    def showEvent(self, event: QShowEvent):
        super().showEvent(event)
        #QTimer.singleShot(50, lambda *args: self.setSecondaryWidgetPosition(self.ui.rightDockWidget, "right"))  # type: ignore[arg-type]
        QTimer.singleShot(0, lambda *args: self.showScrollingTip())
        self.resize(self.width()+200, self.height())

    def showScrollingTip(self):
        tip = random.choice(self.tips)  # noqa: S311
        self.tipLabel.setText(tip)
        self.tipLabel.adjustSize()
        self.startTooltipUIAnimation()

    def startTooltipUIAnimation(self):
        if self.tipsStartFromRightSide:
            start_x = -self.tipLabel.width()
            end_x = self.statusBar().width()
        else:
            start_x = self.statusBar().width()
            end_x = -self.tipLabel.width()

        self.tipLabel.setGeometry(start_x, 0, self.tipLabel.width(), self.statusBar().height())
        self.statusbar_animation = QPropertyAnimation(self.tipLabel, b"geometry")
        self.statusbar_animation.setDuration(15000)
        self.statusbar_animation.setStartValue(QRect(start_x, 0, self.tipLabel.width(), self.statusBar().height()))
        self.statusbar_animation.setEndValue(QRect(end_x, 0, self.tipLabel.width(), self.statusBar().height()))
        #self.statusbar_animation.finished.connect(self.toggleScrollbarTipDirection)
        self.statusbar_animation.start()

    def toggleScrollbarTipDirection(self):
        self.tipsStartFromRightSide = not self.tipsStartFromRightSide
        self.statusbar_animation.disconnect()
        self.startTooltipUIAnimation()

    def setupDLGTreeMVC(self):
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

    def _setupSignals(self):  # noqa: PLR0915
        """Connects UI signals to update node/link on change."""
        scriptTextEntryTooltip = """
A ResRef to a script, where the entry point is its <code>main()</code> function.
<br><br>
<i>Right-click for more options</i>
"""
        self.ui.script1Label.setToolTip(scriptTextEntryTooltip)
        self.ui.script2Label.setToolTip(scriptTextEntryTooltip)
        self.ui.script1ResrefEdit.setToolTip(scriptTextEntryTooltip)
        self.ui.script2ResrefEdit.setToolTip(scriptTextEntryTooltip)
        self.ui.script1ResrefEdit.currentTextChanged.connect(self.onNodeUpdate)
        self.ui.script2ResrefEdit.currentTextChanged.connect(self.onNodeUpdate)

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
        self.ui.condition1ResrefEdit.currentTextChanged.connect(self.onNodeUpdate)
        self.ui.condition2ResrefEdit.currentTextChanged.connect(self.onNodeUpdate)

        self.ui.soundComboBox.currentTextChanged.connect(self.onNodeUpdate)
        self.ui.voiceComboBox.currentTextChanged.connect(self.onNodeUpdate)

        self.ui.soundButton.clicked.connect(lambda: self.playSound(self.ui.soundComboBox.currentText()) and None or None)
        self.ui.voiceButton.clicked.connect(lambda: self.playSound(self.ui.voiceComboBox.currentText()) and None or None)

        self.ui.soundComboBox.set_button_delegate("Play", lambda text: self.playSound(text))
        self.ui.voiceComboBox.set_button_delegate("Play", lambda text: self.playSound(text))

        self.ui.speakerEdit.textEdited.connect(self.onNodeUpdate)
        self.ui.listenerEdit.textEdited.connect(self.onNodeUpdate)
        self.ui.script1Param1Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.script1Param2Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.script1Param3Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.script1Param4Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.script1Param5Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.script1Param6Edit.textEdited.connect(self.onNodeUpdate)
        self.ui.script2Param1Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.script2Param2Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.script2Param3Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.script2Param4Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.script2Param5Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.script2Param6Edit.textEdited.connect(self.onNodeUpdate)
        self.ui.condition1Param1Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.condition1Param2Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.condition1Param3Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.condition1Param4Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.condition1Param5Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.condition1Param6Edit.textEdited.connect(self.onNodeUpdate)
        self.ui.condition1NotCheckbox.stateChanged.connect(self.onNodeUpdate)
        self.ui.condition2Param1Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.condition2Param2Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.condition2Param3Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.condition2Param4Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.condition2Param5Spin.valueChanged.connect(self.onNodeUpdate)
        self.ui.condition2Param6Edit.textEdited.connect(self.onNodeUpdate)
        self.ui.condition2NotCheckbox.stateChanged.connect(self.onNodeUpdate)
        self.ui.emotionSelect.currentIndexChanged.connect(self.onNodeUpdate)
        self.ui.expressionSelect.currentIndexChanged.connect(self.onNodeUpdate)
        self.ui.soundCheckbox.toggled.connect(self.onNodeUpdate)
        self.ui.soundCheckbox.toggled.connect(self.handleSoundChecked)
        self.ui.plotIndexCombo.currentIndexChanged.connect(self.onNodeUpdate)
        self.ui.plotXpSpin.valueChanged.connect(self.onNodeUpdate)
        self.ui.questEdit.textEdited.connect(self.onNodeUpdate)
        self.ui.questEntrySpin.valueChanged.connect(self.onNodeUpdate)
        self.ui.cameraIdSpin.valueChanged.connect(self.onNodeUpdate)
        self.ui.cameraAngleSelect.currentIndexChanged.connect(self.onNodeUpdate)
        self.ui.cameraEffectSelect.currentIndexChanged.connect(self.onNodeUpdate)
        self.ui.nodeUnskippableCheckbox.toggled.connect(self.onNodeUpdate)
        self.ui.nodeIdSpin.valueChanged.connect(self.onNodeUpdate)
        self.ui.alienRaceNodeSpin.valueChanged.connect(self.onNodeUpdate)
        self.ui.postProcSpin.valueChanged.connect(self.onNodeUpdate)
        self.ui.delaySpin.valueChanged.connect(self.onNodeUpdate)
        self.ui.logicSpin.valueChanged.connect(self.onNodeUpdate)
        self.ui.waitFlagSpin.valueChanged.connect(self.onNodeUpdate)
        self.ui.fadeTypeSpin.valueChanged.connect(self.onNodeUpdate)
        self.ui.commentsEdit.textChanged.connect(self.onNodeUpdate)

        self.ui.dialogTree.expanded.connect(self.onItemExpanded)
        self.ui.dialogTree.customContextMenuRequested.connect(self.onTreeContextMenu)
        self.ui.dialogTree.doubleClicked.connect(lambda _e: self.editText(indexes=self.ui.dialogTree.selectionModel().selectedIndexes()))
        self.ui.dialogTree.selectionModel().selectionChanged.connect(self.onSelectionChanged)

        self.ui.actionReloadTree.triggered.connect(lambda: self._loadDLG(self.core_dlg))
        self.ui.cameraAnimSpin.setMinimum(1200)
        self.ui.cameraAnimSpin.setMaximum(65535)

        self.ui.addStuntButton.clicked.connect(self.onAddStuntClicked)
        self.ui.removeStuntButton.clicked.connect(self.onRemoveStuntClicked)
        self.ui.editStuntButton.clicked.connect(self.onEditStuntClicked)

        self.ui.addAnimButton.clicked.connect(self.onAddAnimClicked)
        self.ui.removeAnimButton.clicked.connect(self.onRemoveAnimClicked)
        self.ui.editAnimButton.clicked.connect(self.onEditAnimClicked)

    def setupPostUIElements(self):
        self.setupLeftDockWidget()
        self._setupViewMenu()
        self.noScrollEventFilter = NoScrollEventFilter(self)
        self.noScrollEventFilter.setup_filter()

        # Go-to bar
        self.go_to_bar = QWidget(self)
        self.go_to_bar.setVisible(False)
        self.go_to_layout = QHBoxLayout(self.go_to_bar)
        self.go_to_input = QLineEdit(self.go_to_bar)
        self.go_to_button = QPushButton("Go", self.go_to_bar)
        self.go_to_layout.addWidget(self.go_to_input)
        self.go_to_layout.addWidget(self.go_to_button)
        self.ui.verticalLayout_main.insertWidget(0, self.go_to_bar)

        # Find bar
        self.find_bar = QWidget(self)
        self.find_bar.setVisible(False)
        self.find_layout = QHBoxLayout(self.find_bar)
        self.find_input = QLineEdit(self.find_bar)
        self.find_button = QPushButton("Find Next", self.find_bar)
        self.results_label = QLabel(self.find_bar)
        self.find_layout.addWidget(self.find_input)
        self.find_layout.addWidget(self.find_button)
        self.find_layout.addWidget(self.results_label)
        self.ui.verticalLayout_main.insertWidget(0, self.find_bar)

        # Connect buttons
        self.go_to_button.clicked.connect(self.handle_go_to)
        self.find_button.clicked.connect(self.handle_find)

        self.search_results = []
        self.current_result_index = 0

        # Connect buttons
        self.go_to_button.clicked.connect(self.handle_go_to)
        self.find_button.clicked.connect(self.handle_find)

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

    def custom_go_to_function(self, input_text: str):
        ...  # TODO(th3w1zard1): allow quick jumps to EntryList/ReplyList nodes.

    def find_item_matching_display_text(self, input_text: str) -> list[DLGStandardItem]:
        current_index: QModelIndex = self.ui.dialogTree.currentIndex()
        if not current_index.isValid():
            return []
        current_item: QStandardItem | None = self.model.itemFromIndex(current_index)
        if current_item is None:
            return []

        matching_items: list[DLGStandardItem | QStandardItem] = []
        input_text = input_text.lower()

        def search_item(item: QStandardItem):
            if input_text in item.text().lower():
                matching_items.append(item)
            for row in range(item.rowCount()):
                search_item(item.child(row))

        root = self.model.invisibleRootItem()
        for row in range(root.rowCount()):
            childItem = root.child(row)
            if not isinstance(childItem, DLGStandardItem):
                continue
            search_item(childItem)
        if not matching_items:
            return []

        current_row = current_index.row()
        current_parent = current_item.parent()
        next_item = None
        for item in matching_items:
            if not isinstance(item, DLGStandardItem):
                continue
            item_index = self.model.indexFromItem(item)
            if not item_index.isValid():
                continue
            item_parent = item.parent()
            if item_parent == current_parent and item_index.row() > current_row:
                next_item = item
                break
            if item_parent is None and current_parent is None and item_index.row() > current_row:
                next_item = item
                break
        if not next_item:
            next_item = matching_items[0]
        if not isinstance(next_item, DLGStandardItem):
            return []
        return [next_item]

    def highlight_result(self, item: QStandardItem):
        index = self.model.indexFromItem(item)
        parent = index.parent()
        while parent.isValid():
            self.ui.dialogTree.expand(parent)
            parent = parent.parent()
        self.ui.dialogTree.setCurrentIndex(index)
        self.ui.dialogTree.setFocus()
        selection_model = self.ui.dialogTree.selectionModel()
        selection_model.select(index, QItemSelectionModel.Select | QItemSelectionModel.Rows)
        self.ui.dialogTree.scrollTo(index, QAbstractItemView.PositionAtCenter)

    def update_results_label(self):
        self.results_label.setText(f"{self.current_result_index + 1} / {len(self.search_results)}")

    def setupLeftDockWidget(self):
        self.leftDockWidget = QDockWidget("Orphaned Nodes and Pinned Items", self)
        self.leftDockWidgetContainer = QWidget()
        self.leftDockLayout = QVBoxLayout(self.leftDockWidgetContainer)

        # Orphaned Nodes List
        self.orphanedNodesList = DLGListWidget(self)
        self.orphanedNodesList.useHoverText = False
        self.orphanedNodesList.setWordWrap(True)
        self.orphanedNodesList.setItemDelegate(HTMLDelegate(self.orphanedNodesList))
        # orphans is drag only. Someone please explain why there's a billion functions that need to be called to disable/enable drag/drop.
        self.orphanedNodesList.setDragEnabled(True)
        self.orphanedNodesList.setAcceptDrops(False)
        self.orphanedNodesList.viewport().setAcceptDrops(False)
        self.orphanedNodesList.setDropIndicatorShown(False)
        self.orphanedNodesList.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)

        # Pinned Items List
        self.pinnedItemsList = DLGListWidget(self)
        self.pinnedItemsList.setWordWrap(True)
        self.pinnedItemsList.setItemDelegate(HTMLDelegate(self.pinnedItemsList))
        self.pinnedItemsList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.pinnedItemsList.setAcceptDrops(True)
        self.pinnedItemsList.viewport().setAcceptDrops(True)
        self.pinnedItemsList.setDragEnabled(True)
        self.pinnedItemsList.setDropIndicatorShown(True)
        self.pinnedItemsList.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)

        # Add both lists to the layout
        self.leftDockLayout.addWidget(QLabel("Orphaned Nodes"))
        self.leftDockLayout.addWidget(self.orphanedNodesList)
        self.leftDockLayout.addWidget(QLabel("Pinned Items"))
        self.leftDockLayout.addWidget(self.pinnedItemsList)

        # Set the container as the widget for the dock
        self.leftDockWidget.setWidget(self.leftDockWidgetContainer)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.leftDockWidget)
        self.setStyleSheet(self.get_stylesheet())

        def mimeData(items: Iterable[DLGListWidgetItem], listWidget: DLGListWidget) -> QMimeData:
            mimeData = QMimeData()
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
                stream_listwidget.writeBytes(json.dumps(item.link.to_dict()).encode())
                stream_listwidget.writeInt32(_MODEL_INSTANCE_ID_ROLE)
                stream_listwidget.writeInt64(id(self))

            mimeData.setData(QT_STANDARD_ITEM_FORMAT, listwidget_data)
            return mimeData

        def leftDockWidgetStartDrag(supportedActions: Qt.DropActions, sourceWidget: DLGListWidget):
            selected_items: list[DLGListWidgetItem] = sourceWidget.selectedItems()
            if not selected_items:
                print("No selected items being dragged? (probably means someone JUST dropped into list)")
                return

            drag = QDrag(sourceWidget)
            drag.setMimeData(mimeData(selected_items, sourceWidget))
            drag.exec_(supportedActions)

        self.orphanedNodesList.startDrag = lambda supportedActions: leftDockWidgetStartDrag(supportedActions, self.orphanedNodesList)
        self.pinnedItemsList.startDrag = lambda supportedActions: leftDockWidgetStartDrag(supportedActions, self.pinnedItemsList)

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

    def restoreOrphanedNode(self, link: DLGLink):
        print(f"restoreOrphanedNodes(link={link})")
        selectedOrphanItem = self.orphanedNodesList.currentItem()
        if selectedOrphanItem is None:
            print("restoreOrphanedNodes: No leftDockWidget selected item.")
            self.blinkWindow()
            return
        selectedTreeIndexes = self.ui.dialogTree.selectedIndexes()
        if not selectedTreeIndexes or not selectedTreeIndexes[0]:
            QMessageBox(QMessageBox.Icon.Information, "No target specified", "Select a position in the tree to insert this orphan at then try again.")
            return
        selectedTreeItem: DLGStandardItem | None = cast(DLGStandardItem, self.model.itemFromIndex(selectedTreeIndexes[0]))
        if selectedTreeItem is None:
            print("restoreOrphanedNodes: selected index was not a standard item.")
            self.blinkWindow()
            return
        oldLinkToCurrentOrphan: DLGLink = selectedOrphanItem.link
        oldLinkPath = selectedOrphanItem.data(_LINK_PARENT_NODE_PATH_ROLE)
        if isinstance(oldLinkToCurrentOrphan.node, type(selectedTreeItem.link.node)):
            targetParent = selectedTreeItem.parent()
            intendedLinkListIndexRow = selectedTreeItem.row()
        else:
            targetParent = selectedTreeItem
            intendedLinkListIndexRow = 0
        new_link_path = f"StartingList\\{intendedLinkListIndexRow}" if targetParent is None else targetParent.link.node.path()
        link_parent_path, link_partial_path, linked_to_path = self.get_item_dlg_paths(selectedOrphanItem)
        link_full_path = link_partial_path if link_parent_path is None else f"{link_parent_path}\\{link_partial_path}"
        confirm_message = f"The orphan '{linked_to_path}' (originally linked from {link_full_path}) will be newly linked from {new_link_path} with this action. Continue?"
        reply = QMessageBox.question(self, "Restore Orphaned Node", confirm_message, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            print(f"orphan '{linked_to_path}' (originally linked from {oldLinkPath}) is to be linked from {new_link_path}")
            item = self.model.insertLinkToParentAsItem(targetParent, DLGLink.from_dict(oldLinkToCurrentOrphan.to_dict()), intendedLinkListIndexRow)
            self.model.loadDLGItemRec(item)

            intendedLinkListIndexRow = self.orphanedNodesList.row(selectedOrphanItem)
            self.orphanedNodesList.takeItem(intendedLinkListIndexRow)

    def deleteOrphanedNodePermanently(self, link: DLGLink):
        print(f"deleteOrphanedNodePermanently(link={link})")
        selectedOrphanItem: DLGListWidgetItem | None = self.orphanedNodesList.currentItem()
        if selectedOrphanItem is None:
            print("deleteOrphanedNodePermanently: No leftDockWidget selected item.")
            self.blinkWindow()
            return
        self.orphanedNodesList.takeItem(self.orphanedNodesList.row(selectedOrphanItem))

    def _setupViewMenu(self):
        viewMenu = self.ui.menubar.addMenu("View")
        settingsMenu = self.ui.menubar.addMenu("Settings")

        # View Menu: Display-related settings
        self._addExclusiveMenuAction(
            viewMenu,
            "Text Elide Mode",
            self.ui.dialogTree.textElideMode,
            self.ui.dialogTree.setTextElideMode,
            options={
                "Elide Left": Qt.TextElideMode.ElideLeft,
                "Elide Right": Qt.TextElideMode.ElideRight,
                "Elide Middle": Qt.TextElideMode.ElideMiddle,
                "Elide None": Qt.TextElideMode.ElideNone,
            },
            settings_key="textElideMode",
        )

        self._addExclusiveMenuAction(
            viewMenu,
            "Layout Direction",
            self.ui.dialogTree.layoutDirection,
            self.ui.dialogTree.setLayoutDirection,
            options={
                "Left to Right": Qt.LayoutDirection.LeftToRight,
                "Right to Left": Qt.LayoutDirection.RightToLeft,
            },
            settings_key="layoutDirection",
        )

        self._addMenuAction(
            viewMenu,
            "Uniform Row Heights",
            self.ui.dialogTree.uniformRowHeights,
            self.ui.dialogTree.setUniformRowHeights,
            settings_key="uniformRowHeights",
        )

        self._addMenuAction(
            viewMenu,
            "Show/Hide Branch Connectors",
            self.ui.dialogTree.branchConnectorsDrawn,
            self.ui.dialogTree.drawConnectors,
            settings_key="drawBranchConnectors",
        )

        self._addMenuAction(
            viewMenu,
            "Animations",
            self.ui.dialogTree.isAnimated,
            self.ui.dialogTree.setAnimated,
            settings_key="animations",
        )

        self._addMenuAction(
            viewMenu,
            "Expand Items on Double Click",
            self.ui.dialogTree.expandsOnDoubleClick,
            self.ui.dialogTree.setExpandsOnDoubleClick,
            settings_key="expandsOnDoubleClick",
        )

        self._addMenuAction(
            viewMenu,
            "Alternating Row Colors",
            self.ui.dialogTree.alternatingRowColors,
            self.ui.dialogTree.setAlternatingRowColors,
            settings_key="alternatingRowColors",
        )

        self._addMenuAction(viewMenu, "Tree Indentation",
                            self.ui.dialogTree.indentation,
                            self.ui.dialogTree.setIndentation,
                            settings_key="indentation",
                            param_type=int)

        self._addColorMenuAction(
            viewMenu,
            "Set Entry Text Color",
            lambda: QColor(
                self.dlg_settings.get("entryTextColor", QColor(255, 0, 0))
            ),
            settings_key="entryTextColor",
        )

        self._addColorMenuAction(
            viewMenu,
            "Set Reply Text Color",
            lambda: QColor(
                self.dlg_settings.get("replyTextColor", QColor(0, 0, 255))
            ),
            settings_key="replyTextColor",
        )

        # Settings Menu: Configuration settings
        self._addExclusiveMenuAction(
            settingsMenu,
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

        self._addExclusiveMenuAction(
            settingsMenu,
            "Horizontal Scroll Mode",
            self.ui.dialogTree.horizontalScrollMode,
            self.ui.dialogTree.setHorizontalScrollMode,
            options={
                "Scroll Per Item": QAbstractItemView.ScrollMode.ScrollPerItem,
                "Scroll Per Pixel": QAbstractItemView.ScrollMode.ScrollPerPixel,
            },
            settings_key="horizontalScrollMode",
        )

        self._addExclusiveMenuAction(
            settingsMenu,
            "Vertical Scroll Mode",
            self.ui.dialogTree.verticalScrollMode,
            self.ui.dialogTree.setVerticalScrollMode,
            options={
                "Scroll Per Item": QAbstractItemView.ScrollMode.ScrollPerItem,
                "Scroll Per Pixel": QAbstractItemView.ScrollMode.ScrollPerPixel,
            },
            settings_key="verticalScrollMode",
        )

        self._addMenuAction(settingsMenu, "Auto Scroll (internal)",
                            self.ui.dialogTree.hasAutoScroll,
                            self.ui.dialogTree.setAutoScroll,
                            settings_key="autoScroll")

        self._addMenuAction(settingsMenu, "Auto Fill Background",
                            self.ui.dialogTree.autoFillBackground,
                            self.ui.dialogTree.setAutoFillBackground,
                            settings_key="autoFillBackground")

        self._addMenuAction(settingsMenu, "Expand All Root Item Children",
                            lambda: self.dlg_settings.get("ExpandRootChildren", False),
                            lambda value: self.dlg_settings.set("ExpandRootChildren", value),
                            settings_key="ExpandRootChildren")

        self._addMenuAction(settingsMenu, "Font Size",
                            lambda: self.ui.dialogTree.text_size,
                            lambda x: setattr(self.ui.dialogTree, "text_size", x),
                            settings_key="fontSize",
                            param_type=int)

        self._addMenuAction(settingsMenu, "Vertical Spacing",
                            lambda: self.ui.dialogTree.itemDelegate().customVerticalSpacing,
                            lambda x: self.ui.dialogTree.itemDelegate().setVerticalSpacing(x),
                            settings_key="verticalSpacing",
                            param_type=int)

        self._addExclusiveMenuAction(
            settingsMenu,
            "TSL Widget Handling",
            lambda: "Default",
            self.setTSLWidgetHandling,
            options={
                "Enable": "Enable",
                "Disable": "Disable",
                "Show": "Show",
                "Hide": "Hide",
                "Default": "Default",
            },
            settings_key="TSLWidgetHandling",
        )

        self._addMenuAction(settingsMenu, "Show/Hide Extra ToolTips on Hover",
                            lambda: self.whatsThisToggle,
                            lambda _value: self.setupExtraTooltipMode(),
                            settings_key="showVerboseHoverHints",
                            param_type=bool)

        # Advanced Menu: Miscellaneous advanced settings
        advancedMenu = viewMenu.addMenu("Advanced")
        refreshMenu = advancedMenu.addMenu("Refresh")
        treeMenu = refreshMenu.addMenu("TreeView")
        self._addSimpleAction(treeMenu, "Repaint", self.ui.dialogTree.repaint)
        self._addSimpleAction(treeMenu, "Update", self.ui.dialogTree.update)
        self._addSimpleAction(treeMenu, "Resize Column To Contents", lambda: self.ui.dialogTree.resizeColumnToContents(0))
        self._addSimpleAction(treeMenu, "Update Geometries", self.ui.dialogTree.updateGeometries)
        self._addSimpleAction(treeMenu, "Reset", self.ui.dialogTree.reset)

        listWidgetMenu = refreshMenu.addMenu("ListWidget")
        self._addSimpleAction(listWidgetMenu, "Repaint", self.pinnedItemsList.repaint)
        self._addSimpleAction(listWidgetMenu, "Update", self.pinnedItemsList.update)
        self._addSimpleAction(listWidgetMenu, "Reset Horizontal Scroll Mode", lambda: self.pinnedItemsList.resetHorizontalScrollMode())
        self._addSimpleAction(listWidgetMenu, "Reset Vertical Scroll Mode", lambda: self.pinnedItemsList.resetVerticalScrollMode())
        self._addSimpleAction(listWidgetMenu, "Update Geometries", self.pinnedItemsList.updateGeometries)
        self._addSimpleAction(listWidgetMenu, "Reset", self.pinnedItemsList.reset)
        self._addSimpleAction(listWidgetMenu, "layoutChanged", lambda: self.pinnedItemsList.model().layoutChanged.emit())

        viewportMenu = refreshMenu.addMenu("Viewport")
        self._addSimpleAction(viewportMenu, "Repaint", self.ui.dialogTree.viewport().repaint)
        self._addSimpleAction(viewportMenu, "Update", self.ui.dialogTree.viewport().repaint)  # Corrected redundant action

        modelMenu = refreshMenu.addMenu("Model")
        self._addSimpleAction(modelMenu, "Emit Layout Changed", lambda: self.ui.dialogTree.model().layoutChanged.emit())

        windowMenu = refreshMenu.addMenu("Window")
        self._addSimpleAction(windowMenu, "Repaint", lambda: self.repaint)

        #self.dlg_settings.loadAll(self)


    def setTSLWidgetHandling(self, state: str):
        self.dlg_settings.set("TSLWidgetHandling", state)
        widgets_to_handle = [
            self.ui.script1Param1Spin, self.ui.script1Param2Spin, self.ui.script1Param3Spin, self.ui.script1Param4Spin,
            self.ui.script1Param5Spin, self.ui.script1Param6Edit, self.ui.script2ResrefEdit, self.ui.script2Param1Spin,
            self.ui.script2Param2Spin, self.ui.script2Param3Spin, self.ui.script2Param4Spin, self.ui.script2Param5Spin,
            self.ui.script2Param6Edit, self.ui.condition1Param1Spin, self.ui.condition1Param2Spin, self.ui.condition1Param3Spin,
            self.ui.condition1Param4Spin, self.ui.condition1Param5Spin, self.ui.condition1Param6Edit, self.ui.condition1NotCheckbox,
            self.ui.condition2ResrefEdit, self.ui.condition2Param1Spin, self.ui.condition2Param2Spin, self.ui.condition2Param3Spin,
            self.ui.condition2Param4Spin, self.ui.condition2Param5Spin, self.ui.condition2Param6Edit, self.ui.condition2NotCheckbox,
            self.ui.emotionSelect, self.ui.expressionSelect, self.ui.nodeUnskippableCheckbox, self.ui.nodeIdSpin,
            self.ui.alienRaceNodeSpin, self.ui.postProcSpin, self.ui.logicSpin,
            # labels
            self.ui.script2Label, self.ui.conditional2Label, self.ui.emotionLabel,
            self.ui.expressionLabel, self.ui.nodeIdLabel, self.ui.alienRaceNodeLabel, self.ui.postProcNodeLabel, self.ui.logicLabel
        ]
        for widget in widgets_to_handle:
            self.handleWidgetWithTSL(widget, state)

    def handleWidgetWithTSL(self, widget: QWidget | QLabel, state: str):
        """Customizes widget behavior based on TSL state."""
        widget.show()
        widget.setEnabled(True)
        if state == "Enable":
            widget.setEnabled(True)
        elif state == "Disable":
            widget.setEnabled(False)
            widget.setToolTip("This widget is only available in KOTOR II.")
        elif state == "Show":
            widget.show()
        elif state == "Hide":
            widget.hide()
        elif state == "Default":
            widget.setEnabled(self._installation.tsl)
            if not self._installation.tsl:
                widget.setToolTip("This widget is only available in KOTOR II.")
            else:
                widget.setToolTip("")

    def _addColorMenuAction(
        self,
        menu: QMenu,
        title: str,
        current_color_func: Callable[[], QColor],
        settings_key: str,
    ):
        action = QAction(title, self)
        action.triggered.connect(lambda: self._handleColorAction(current_color_func, title, settings_key))
        menu.addAction(action)

    def _handleColorAction(
        self,
        get_func: Callable[[], Any],
        title: str,
        settings_key: str,
    ):
        color = QColorDialog.getColor(get_func(), self, title)
        if color.isValid():
            self.dlg_settings.set(settings_key, color.name())
            #self.model.layoutAboutToBeChanged.emit()
            for item in self.model:
                if not isinstance(item, DLGStandardItem):
                    continue
                if item.isDeleted():
                    continue
                self.model.updateItemData(item)
            #self.model.layoutChanged.emit()
            self.ui.dialogTree.viewport().update()
            self.ui.dialogTree.update()

    def _addSimpleAction(self, menu: QMenu, title: str, func: Callable[[], Any]):
        action = QAction(title, self)
        action.triggered.connect(func)
        menu.addAction(action)

    def _addMenuAction(  # noqa: PLR0913
        self,
        menu: QMenu,
        title: str,
        current_state_func: Callable[[], Any],
        set_func: Callable[[Any], Any],
        settings_key: str,
        options: dict | None = None,
        param_type: type = bool,
    ):
        action = QAction(title, self)
        if param_type is bool:
            action.setCheckable(True)
            initial_value = self.dlg_settings.get(settings_key, current_state_func())
            action.setChecked(initial_value)
            set_func(initial_value)  # Apply the initial value from settings
            action.toggled.connect(lambda checked: [set_func(checked), self.dlg_settings.set(settings_key, checked)])
        elif param_type is int:
            action.triggered.connect(lambda: self._handleIntAction(set_func, title, settings_key))
        else:
            action.triggered.connect(lambda: self._handleNonBoolAction(set_func, title, options, settings_key))
        menu.addAction(action)

    def _addExclusiveMenuAction(  # noqa: PLR0913
        self,
        menu: QMenu,
        title: str,
        current_state_func: Callable[[], Any],
        set_func: Callable[[Any], Any],
        options: dict,
        settings_key: str,
    ):
        subMenu = menu.addMenu(title)
        actionGroup = QActionGroup(self)
        actionGroup.setExclusive(True)
        initial_value = self.dlg_settings.get(settings_key, current_state_func())
        set_func(initial_value)  # Apply the initial value from settings
        for option_name, option_value in options.items():
            action = QAction(option_name, self)
            action.setCheckable(True)
            action.setChecked(initial_value == option_value)
            action.triggered.connect(lambda checked, val=option_value: [set_func(val), self.dlg_settings.set(settings_key, val)] if checked else None)
            subMenu.addAction(action)
            actionGroup.addAction(action)

    def _handleIntAction(self, func: Callable[[int], Any], title: str, settings_key: str):
        value, ok = QInputDialog.getInt(self, f"Set {title}", f"Enter {title}:", min=0)
        if ok:
            func(value)
            self.dlg_settings.set(settings_key, value)

    def _handleNonBoolAction(self, func: Callable[[Any], Any], title: str, options: dict, settings_key: str):
        items = list(options.keys())
        item, ok = QInputDialog.getItem(self, f"Select {title}", f"Select {title}:", items, 0, False)
        if ok and item:
            value = options[item]
            func(value)
            self.dlg_settings.set(settings_key, value)

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
        self.orphanedNodesList.clear()
        self._loadDLG(dlg)
        self.refreshStuntList()
        self.ui.onAbortCombo.setComboBoxText(str(dlg.on_abort))
        self.ui.onEndEdit.setComboBoxText(str(dlg.on_end))
        self.ui.voIdEdit.setText(dlg.vo_id)
        self.ui.voIdEdit.textChanged.connect(self.restartVoIdEditTimer)
        self.ui.ambientTrackCombo.setComboBoxText(str(dlg.ambient_track))
        self.ui.cameraModelSelect.setComboBoxText(str(dlg.camera_model))
        self.ui.conversationSelect.setCurrentIndex(dlg.conversation_type.value)
        self.ui.computerSelect.setCurrentIndex(dlg.computer_type.value)
        self.ui.skippableCheckbox.setChecked(dlg.skippable)
        self.ui.skippableCheckbox.setToolTip("Should the user be allowed to skip dialog lines/cutscenes in this file?")
        self.ui.animatedCutCheckbox.setChecked(bool(dlg.animated_cut))
        self.ui.oldHitCheckbox.setChecked(dlg.old_hit_check)
        self.ui.unequipHandsCheckbox.setChecked(dlg.unequip_hands)
        self.ui.unequipAllCheckbox.setChecked(dlg.unequip_items)
        self.ui.entryDelaySpin.setValue(dlg.delay_entry)
        self.ui.replyDelaySpin.setValue(dlg.delay_reply)
        relevant_script_resnames = sorted(
            {
                res.resname().lower()
                for res in self._installation.getRelevantResources(ResourceType.NCS, self._filepath)
            }
        )
        self.ui.script2ResrefEdit.populateComboBox(relevant_script_resnames)
        self.ui.condition2ResrefEdit.populateComboBox(relevant_script_resnames)
        self.ui.script1ResrefEdit.populateComboBox(relevant_script_resnames)
        self.ui.condition1ResrefEdit.populateComboBox(relevant_script_resnames)
        self.ui.onEndEdit.populateComboBox(relevant_script_resnames)
        self.ui.onAbortCombo.populateComboBox(relevant_script_resnames)
        relevant_model_resnames = sorted(
            {
                res.resname().lower()
                for res in self._installation.getRelevantResources(ResourceType.MDL, self._filepath)
            }
        )
        self.ui.cameraModelSelect.populateComboBox(relevant_model_resnames)

    def restartVoIdEditTimer(self):
        """Restarts the timer whenever text is changed."""
        self.voIdEditTimer.stop()
        self.voIdEditTimer.start()

    def populateComboboxOnVoIdEditFinished(self):
        """Slot to be called when text editing is finished.

        The editors the game devs themselves used probably did something like this
        """
        if not hasattr(self, "all_voices"):
            self.blinkWindow()
            return
        print("voIdEditTimer debounce finished, populate voiceComboBox with new VO_ID filter...")
        vo_id_lower = self.ui.voIdEdit.text().strip().lower()
        if vo_id_lower:
            filtered_voices = [voice for voice in self.all_voices if vo_id_lower in voice.lower()]
            print(f"filtered {len(self.all_voices)} voices to {len(filtered_voices)} by substring vo_id '{vo_id_lower}'")
        else:
            filtered_voices = self.all_voices
        self.ui.voiceComboBox.populateComboBox(filtered_voices)

    def _loadDLG(self, dlg: DLG):
        """Loads a dialog tree into the UI view."""
        print("<SDM> [_loadDLG scope] GlobalSettings().selectedTheme: ", GlobalSettings().selectedTheme)
        if "(Light)" in GlobalSettings().selectedTheme:
            self.ui.dialogTree.setStyleSheet("")
        self._focused = False
        self.core_dlg = dlg
        self.model.origToOrphanCopy = {
            weakref.ref(origLink): copiedLink
            for origLink, copiedLink in zip(dlg.starters, [DLGLink.from_dict(link.to_dict()) for link in dlg.starters])
        }
        self.populateComboboxOnVoIdEditFinished()

        self.model.resetModel()
        assert self.model.rowCount() == 0 and self.model.columnCount() == 0, "Model is not empty after resetModel() call!"  # noqa: PT018
        self.model.blockSignals(True)
        for start in dlg.starters:  # descending order - matches what the game does.
            item = DLGStandardItem(link=start)
            self.model.loadDLGItemRec(item)
            self.model.appendRow(item)
        self.orphanedNodesList.reset()
        self.orphanedNodesList.clear()
        self.orphanedNodesList.model().layoutChanged.emit()
        self.model.blockSignals(False)
        assert self.model.rowCount() != 0, "Model is empty after _loadDLG(dlg: DLG) call!"  # noqa: PT018
        assert self.model.linkToItems, "linkToItems is empty in the model somehow!"
        assert self.model.nodeToItems, "nodeToItems is empty in the model somehow!"

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
        if gameToUse.is_k1() and self.dlg_settings.get("TSLWidgetHandling", "Default") == "Enabled":
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle("Save TSL Fields?")
            msg_box.setText("You have TSLWidgetHandling set to 'Enabled', but your loaded installation set to K1. Would you like to save TSL fields?")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            response = msg_box.exec()
            if response == QMessageBox.Yes:
                gameToUse = Game.K2

        write_dlg(self.core_dlg, data, gameToUse)
        # dismantle_dlg(self.editor.core_dlg).compare(read_gff(data), log_func=print)  # use for debugging (don't forget to import)

        return data, b""

    def new(self):
        super().new()
        self.orphanedNodesList.clear()
        self._loadDLG(DLG())

    def _setupInstallation(self, installation: HTInstallation):
        """Sets up the installation for the UI."""
        self._installation = installation
        print("<SDM> [_setupInstallation scope] self._installation: ", self._installation)

        installation.setupFileContextMenu(self.ui.script1ResrefEdit, [ResourceType.NSS, ResourceType.NCS])
        if installation.game().is_k1():
            required: list[str] = [HTInstallation.TwoDA_VIDEO_EFFECTS, HTInstallation.TwoDA_DIALOG_ANIMS]

        else:
            required = [
                HTInstallation.TwoDA_EMOTIONS,
                HTInstallation.TwoDA_EXPRESSIONS,
                HTInstallation.TwoDA_VIDEO_EFFECTS,
                HTInstallation.TwoDA_DIALOG_ANIMS,
            ]

        self.all_voices = sorted({res.resname() for res in installation._streamwaves}, key=str.lower)  # noqa: SLF001
        self.all_sounds = sorted({res.resname() for res in installation._streamsounds}, key=str.lower)  # noqa: SLF001
        self.all_music = sorted({res.resname() for res in installation._streammusic}, key=str.lower)  # noqa: SLF001
        installation.htBatchCache2DA(required)
        self._setupTslInstallDefs(installation)
        self.ui.soundComboBox.populateComboBox(self.all_sounds)  # noqa: SLF001
        self.ui.ambientTrackCombo.populateComboBox(self.all_music)
        self.ui.ambientTrackCombo.set_button_delegate("Play", lambda text: self.playSound(text))
        installation.setupFileContextMenu(self.ui.cameraModelSelect, [ResourceType.MDL], [SearchLocation.CHITIN, SearchLocation.OVERRIDE])
        installation.setupFileContextMenu(self.ui.ambientTrackCombo, [ResourceType.WAV, ResourceType.MP3], [SearchLocation.MUSIC])
        installation.setupFileContextMenu(self.ui.soundComboBox, [ResourceType.WAV, ResourceType.MP3], [SearchLocation.SOUND])
        installation.setupFileContextMenu(self.ui.voiceComboBox, [ResourceType.WAV, ResourceType.MP3], [SearchLocation.VOICE])
        installation.setupFileContextMenu(self.ui.condition1ResrefEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setupFileContextMenu(self.ui.onEndEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setupFileContextMenu(self.ui.onAbortCombo, [ResourceType.NSS, ResourceType.NCS])

        videoEffects: TwoDA | None = installation.htGetCache2DA(HTInstallation.TwoDA_VIDEO_EFFECTS)
        if videoEffects:
            self.ui.cameraEffectSelect.clear()
            self.ui.cameraEffectSelect.setPlaceholderText("[None]")
            self.ui.cameraEffectSelect.setItems(
                [
                    label.replace("VIDEO_EFFECT_", "").replace("_", " ").title()
                    for label in videoEffects.get_column("label")
                ],
                cleanupStrings=False,
                ignoreBlanks=True,
            )
            self.ui.cameraEffectSelect.setContext(videoEffects, installation, HTInstallation.TwoDA_VIDEO_EFFECTS)

        plot2DA: TwoDA | None = installation.htGetCache2DA(HTInstallation.TwoDA_PLOT)
        if plot2DA:
            self.ui.plotIndexCombo.clear()
            self.ui.plotIndexCombo.setPlaceholderText("[None]")
            self.ui.plotIndexCombo.setItems(
                [cell.title() for cell in plot2DA.get_column("label")],
                cleanupStrings=True,
            )
            self.ui.plotIndexCombo.setContext(plot2DA, installation, HTInstallation.TwoDA_PLOT)
        animations_2da: TwoDA | None = self._installation.htGetCache2DA(HTInstallation.TwoDA_DIALOG_ANIMS)
        fakeObj = cast(ComboBox2DA, self.ui.animsList)
        fakeObj._this2DA = animations_2da  # noqa: SLF001
        fakeObj._installation = installation  # noqa: SLF001
        fakeObj._resname = HTInstallation.TwoDA_DIALOG_ANIMS  # noqa: SLF001
        def onAnimsListContextMenu(point: QPoint):
            menu = QMenu(self.ui.animsList)
            menu.addAction(f"Open {HTInstallation.TwoDA_DIALOG_ANIMS}.2da in Editor").triggered.connect(lambda *args: ComboBox2DA.openIn2DAEditor(fakeObj))
            menu.exec_(point)
        self.ui.animsList.customContextMenuRequested.connect(onAnimsListContextMenu)

    def _setupTslInstallDefs(self, installation: HTInstallation):
        """Set up UI elements for TSL installation selection."""
        emotions: TwoDA | None = installation.htGetCache2DA(HTInstallation.TwoDA_EMOTIONS)
        if emotions:
            self.ui.emotionSelect.clear()
            self.ui.emotionSelect.setItems(emotions.get_column("label"))
            self.ui.emotionSelect.setContext(emotions, installation, HTInstallation.TwoDA_EMOTIONS)

        expressions: TwoDA | None = installation.htGetCache2DA(HTInstallation.TwoDA_EXPRESSIONS)
        if expressions:
            self.ui.expressionSelect.clear()
            self.ui.expressionSelect.setItems(expressions.get_column("label"))
            self.ui.expressionSelect.setContext(expressions, installation, HTInstallation.TwoDA_EXPRESSIONS)

        installation.setupFileContextMenu(self.ui.script2ResrefEdit, [ResourceType.NSS, ResourceType.NCS])
        installation.setupFileContextMenu(self.ui.condition2ResrefEdit, [ResourceType.NSS, ResourceType.NCS])

    def editText(self, e: QMouseEvent | None = None, indexes: list[QModelIndex] | None = None):  # TODO(th3w1zard1): send the sourceWidget here so we can determine which listwidget to get the DLGListWidgetItem from.
        """Edits the text of the selected dialog node."""
        if not indexes:
            self.blinkWindow()
            return
        modelToUse: DLGStandardItemModel | QAbstractListModel = indexes[0].model()
        if not isinstance(modelToUse, QStandardItemModel):
            self.blinkWindow()
            return
        item = modelToUse.itemFromIndex(indexes[0])
        assert item is not None, "modelToUse.itemFromIndex(indexes[0]) should not return None here in editText"
        assert isinstance(item, (DLGStandardItem, DLGListWidgetItem))

        dialog = LocalizedStringDialog(self, self._installation, item.link.node.text)
        if dialog.exec_():
            item.link.node.text = dialog.locstring
            print("<SDM> [editText scope] item.link.node.text: ", item.link.node.text)

            self.model.updateItemData(item)

    def copyPath(self, node_or_link: DLGNode | DLGLink | None):
        """Copies the node path to the user's clipboard."""
        if node_or_link is None:
            return
        paths: list[PureWindowsPath] = self.core_dlg.find_paths(node_or_link)

        if not paths:
            print("No paths available.")
            self.blinkWindow()
            return

        if len(paths) == 1:
            path = str(paths[0])
            print("<SDM> [copyPath scope] path: ", path)

        else:
            path = "\n".join(f"  {i + 1}. {p}" for i, p in enumerate(paths))

        QApplication.clipboard().setText(path)

    def _checkClipboardForJsonNode(self):
        clipboard_text = QApplication.clipboard().text()

        try:
            node_data = json.loads(clipboard_text)
            if isinstance(node_data, dict) and "type" in node_data:
                self._copy = DLGLink.from_dict(node_data)
        except json.JSONDecodeError:
            ...
        except Exception:
            self._logger.exception("Invalid JSON node on clipboard.")

    def expandToRoot(self, item: DLGStandardItem):
        parent: DLGStandardItem | None = item.parent()
        while parent is not None:
            self.ui.dialogTree.expand(parent.index())
            parent = parent.parent()
            #print("<SDM> [expandToRoot scope] parent: ", parent)

    def jumpToOriginal(self, copiedItem: DLGStandardItem):
        """Jumps to the original node of a copied item."""
        sourceNode: DLGNode = copiedItem.link.node
        items: list[DLGStandardItem | None] = [self.model.item(i, 0) for i in range(self.model.rowCount())]

        while items:
            item: DLGStandardItem | None = items.pop()
            assert item is not None

            if item.link is None:
                continue
            print("<SDM> [jumpToOriginal scope] item.link.node: ", item.link.node)
            if item.link.node == sourceNode:
                self.expandToRoot(item)
                self.ui.dialogTree.setCurrentIndex(item.index())
                break
            items.extend([item.child(i, 0) for i in range(item.rowCount())])
        else:
            self._logger.error(f"Failed to find original node for node {sourceNode!r}")

    def focusOnNode(self, link: DLGLink | None) -> DLGStandardItem | None:
        """Focuses the dialog tree on a specific link node."""
        if link is None:
            return None
        if "(Light)" in GlobalSettings().selectedTheme:
            self.ui.dialogTree.setStyleSheet("QTreeView { background: #FFFFEE; }")
        self.model.clear()
        self._focused = True

        item = DLGStandardItem(link=link)
        print("<SDM> [focusOnNode scope] item: ", item.text())

        self.model.layoutAboutToBeChanged.emit()
        self.model.blockSignals(True)
        self.model.loadDLGItemRec(item)
        self.model.appendRow(item)
        self.model.blockSignals(False)
        self.model.layoutChanged.emit()
        return item

    def saveExpandedItems(self) -> list[QModelIndex]:
        expanded_items: list[QModelIndex] = []

        def saveItemsRecursively(index: QModelIndex):
            if not index.isValid():
                self.blinkWindow()
                return
            if self.ui.dialogTree.isExpanded(index):
                expanded_items.append(index)
            for i in range(self.model.rowCount(index)):
                saveItemsRecursively(index.child(i, 0))

        saveItemsRecursively(self.ui.dialogTree.rootIndex())
        return expanded_items

    def saveScrollPosition(self) -> int:
        return self.ui.dialogTree.verticalScrollBar().value()

    def saveSelectedItem(self) -> QModelIndex | None:
        selection_model: QItemSelectionModel = self.ui.dialogTree.selectionModel()
        if selection_model.hasSelection():
            return selection_model.currentIndex()
        return None

    def restoreExpandedItems(self, expandedItems: list[QModelIndex]):
        for index in expandedItems:
            self.ui.dialogTree.setExpanded(index, True)

    def restoreScrollPosition(self, scrollPosition: int):
        self.ui.dialogTree.verticalScrollBar().setValue(scrollPosition)

    def restoreSelectedItem(self, selectedIndex: QModelIndex):
        if selectedIndex and selectedIndex.isValid():
            self.ui.dialogTree.setCurrentIndex(selectedIndex)
            self.ui.dialogTree.scrollTo(selectedIndex)

    def updateTreeView(self):
        expanded_items = self.saveExpandedItems()
        print("<SDM> [updateTreeView scope] expanded_items: %s", len(expanded_items))
        scroll_position = self.saveScrollPosition()
        selected_index = self.saveSelectedItem()
        self.ui.dialogTree.reset()

        self.restoreExpandedItems(expanded_items)
        self.restoreScrollPosition(scroll_position)
        self.restoreSelectedItem(selected_index)

    def onListContextMenu(self, point: QPoint, sourceWidget: DLGListWidget):
        """Displays context menu for tree items."""
        item: DLGListWidgetItem | None = sourceWidget.itemAt(point)
        if item is not None:
            menu = self._getLinkContextMenu(sourceWidget, item)
            if isinstance(sourceWidget, DLGListWidget):
                menu.addAction("Remove from List").triggered.connect(lambda *args: sourceWidget.takeItem(sourceWidget.indexFromItem(item).row()))
        else:
            menu = QMenu(sourceWidget)
        if sourceWidget is self.orphanedNodesList:
            if item is not None:
                restoreAction = menu.addAction("Insert Orphaned at Selected Point")
                restoreAction.triggered.connect(lambda: self.restoreOrphanedNode(item.link))
                menu.addSeparator()
            menu.addAction("Clear orphans list.").triggered.connect(sourceWidget.clear)
        elif item is None and isinstance(sourceWidget, DLGListWidget):
            menu.addAction("Clear List").triggered.connect(sourceWidget.clear)

        menu.popup(sourceWidget.viewport().mapToGlobal(point))

    def onTreeContextMenu(self, point: QPoint):
        """Displays context menu for tree items."""
        index: QModelIndex = self.ui.dialogTree.indexAt(point)
        item: DLGStandardItem | None = self.model.itemFromIndex(index)
        if item is not None:
            menu = self._getLinkContextMenu(self.ui.dialogTree, item)
        else:
            menu = QMenu(self)
            if not self._focused:
                menu.addAction("Add Entry").triggered.connect(self.model.addRootNode)
            else:
                menu.addAction("Reset Tree").triggered.connect(lambda: self._loadDLG(self.core_dlg))
        menu.popup(self.ui.dialogTree.viewport().mapToGlobal(point))

    def setExpandRecursively(  # noqa: PLR0913
        self,
        item: DLGStandardItem,
        seenNodes: set[DLGNode],
        *,
        expand: bool,
        maxdepth: int = 6,
        depth: int = 0,
        isRoot: bool = True,
    ):
        """Recursively expand/collapse all children of the given item."""
        if depth > maxdepth >= 0:
            return
        itemIndex: QModelIndex = item.index()
        if not itemIndex.isValid():
            return
        if not isinstance(item, DLGStandardItem):
            return  # future expand dummy
        if item.link is None or item.link.node is None:
            return
        link: DLGLink = item.link
        assert link.node is not None
        if link.node in seenNodes:
            return
        seenNodes.add(link.node)
        if expand:
            self.ui.dialogTree.expand(itemIndex)
        elif not isRoot:
            self.ui.dialogTree.collapse(itemIndex)
        for row in range(item.rowCount()):
            childItem: DLGStandardItem = item.child(row)
            if childItem is None:
                continue
            childIndex: QModelIndex = childItem.index()
            if not childIndex.isValid():
                continue
            self.setExpandRecursively(childItem, seenNodes, expand=expand, maxdepth=maxdepth, depth=depth + 1, isRoot=False)

    def _getLinkContextMenu(
        self,
        sourceWidget: DLGListWidget | DLGTreeView,
        item: DLGStandardItem | DLGListWidgetItem,
    ) -> QMenu:
        """Sets context menu actions for a dialog tree item."""
        self._checkClipboardForJsonNode()
        notAnOrphan = sourceWidget is not self.orphanedNodesList
        isListWidgetMenu = isinstance(sourceWidget, DLGListWidget)
        assert item.link is not None
        assert item.link.node is not None
        node_type = "Entry" if isinstance(item.link.node, DLGEntry) else "Reply"

        menu = QMenu(sourceWidget)
        editTextAction = menu.addAction("Edit Text")
        editTextAction.triggered.connect(lambda *args: self.editText(indexes=sourceWidget.selectedIndexes()))
        editTextAction.setShortcut(QKeySequence(QtKey.Key_Enter | QtKey.Key_Return))
        focusAction = menu.addAction("Focus")

        focusAction.triggered.connect(lambda: self.focusOnNode(item.link))
        focusAction.setShortcut(QKeySequence(QtKey.Key_F))
        if not item.link.node.links:
            focusAction.setEnabled(False)
        focusAction.setVisible(notAnOrphan)

        findReferencesAction = menu.addAction("Find References")
        findReferencesAction.triggered.connect(lambda: self.findReferences(item))
        findReferencesAction.setVisible(notAnOrphan)

        # Expand/Collapse All Children Action (non copies)
        menu.addSeparator()
        expandAllChildrenAction = menu.addAction("Expand All Children")
        expandAllChildrenAction.triggered.connect(lambda: self.setExpandRecursively(item, set(), expand=True))
        expandAllChildrenAction.setShortcut(QKeySequence(Qt.ShiftModifier | QtKey.Key_Return))
        expandAllChildrenAction.setVisible(not isListWidgetMenu)
        collapseAllChildrenAction = menu.addAction("Collapse All Children")
        collapseAllChildrenAction.triggered.connect(lambda: self.setExpandRecursively(item, set(), expand=False))
        collapseAllChildrenAction.setShortcut(QKeySequence(Qt.ShiftModifier | Qt.AltModifier | Qt.Key_Return))
        collapseAllChildrenAction.setVisible(not isListWidgetMenu)
        if not isListWidgetMenu:
            menu.addSeparator()

        # Play Actions
        playMenu = menu.addMenu("Play")
        playMenu.mousePressEvent = lambda event: (print("playMenu.mousePressEvent"), self._playNodeSound(item.link.node), QMenu.mousePressEvent(playMenu, event))  # type: ignore[method-assign]
        playSoundAction = playMenu.addAction("Play Sound")
        playSoundAction.triggered.connect(lambda: self.playSound("" if item.link is None or item.link.node is None else str(item.link.node.sound)) and None or None)
        playVoiceAction = playMenu.addAction("Play Voice")
        playVoiceAction.triggered.connect(lambda: self.playSound("" if item.link is None or item.link.node is None else str(item.link.node.vo_resref)) and None or None)
        if not self.ui.soundComboBox.currentText().strip():
            playSoundAction.setEnabled(False)
        if not self.ui.voiceComboBox.currentText().strip():
            playVoiceAction.setEnabled(False)
        if not self.ui.soundComboBox.currentText().strip() and not self.ui.voiceComboBox.currentText().strip():
            playMenu.setEnabled(False)
        menu.addSeparator()

        # Copy Actions
        copyNodeAction = menu.addAction(f"Copy {node_type} to Clipboard")
        copyNodeAction.triggered.connect(lambda: self.model.copyLinkAndNode(item.link))
        copyNodeAction.setShortcut(QKeySequence(Qt.ControlModifier | QtKey.Key_C))
        copyGffPathAction = menu.addAction("Copy GFF Path")
        copyGffPathAction.triggered.connect(lambda: self.copyPath(None if item.link is None else item.link.node))
        copyGffPathAction.setShortcut(QKeySequence(Qt.ControlModifier | Qt.AltModifier | QtKey.Key_C))
        copyGffPathAction.setVisible(notAnOrphan)
        menu.addSeparator()

        # Paste Actions
        pasteLinkAction = menu.addAction("Paste from Clipboard as Link")
        pasteNewAction = menu.addAction("Paste from Clipboard as Deep Copy")
        if self._copy is not None:
            if isinstance(self._copy.node, DLGEntry) and isinstance(item.link.node, DLGReply):
                pasteLinkAction.setText("Paste Entry from Clipboard as Link")
                pasteNewAction.setText("Paste Entry from Clipboard as Deep Copy")
            elif isinstance(self._copy.node, DLGReply) and isinstance(item.link.node, DLGEntry):
                pasteLinkAction.setText("Paste Reply from Clipboard as Link")
                pasteNewAction.setText("Paste Reply from Clipboard as Deep Copy")
        else:
            pasteLinkAction.setEnabled(False)
            pasteNewAction.setEnabled(False)
        pasteLinkAction.setShortcut(QKeySequence(Qt.ControlModifier | QtKey.Key_V))
        pasteLinkAction.triggered.connect(lambda: self.model.pasteItem(item, asNewBranches=False))
        pasteLinkAction.setVisible(not isListWidgetMenu)
        pasteNewAction.setShortcut(QKeySequence(Qt.ControlModifier | Qt.ShiftModifier | QtKey.Key_V))
        pasteNewAction.triggered.connect(lambda: self.model.pasteItem(item, asNewBranches=True))
        pasteNewAction.setVisible(not isListWidgetMenu)
        menu.addSeparator()

        # Add/Insert Actions
        addNodeAction = menu.addAction(f"Add {node_type}")
        addNodeAction.triggered.connect(lambda: self.model.addChildToItem(item))
        addNodeAction.setShortcut(QtKey.Key_Insert)
        addNodeAction.setVisible(not isListWidgetMenu)
        if not isListWidgetMenu:
            menu.addSeparator()
        moveUpAction = menu.addAction("Move Up")
        moveUpAction.triggered.connect(lambda: self.model.shiftItem(item, -1))
        moveUpAction.setShortcut(QKeySequence(Qt.ShiftModifier | QtKey.Key_Up))
        moveUpAction.setVisible(not isListWidgetMenu)
        moveDownAction = menu.addAction("Move Down")
        moveDownAction.triggered.connect(lambda: self.model.shiftItem(item, 1))
        moveDownAction.setShortcut(QKeySequence(Qt.ShiftModifier | QtKey.Key_Down))
        moveDownAction.setVisible(not isListWidgetMenu)
        menu.addSeparator()

        # Remove/Delete Actions
        removeLinkAction = menu.addAction(f"Remove {node_type}")
        removeLinkAction.setShortcut(QtKey.Key_Delete)
        removeLinkAction.triggered.connect(lambda: self.model.removeLink(item))
        removeLinkAction.setVisible(not isListWidgetMenu)
        menu.addSeparator()

        useLargeDeleteButton = False  # seems to have broken the context menu after we introduced global QFont sizes.
        if useLargeDeleteButton:
            # Create a custom styled action for "Delete ALL References"
            deleteAllReferencesAction = QWidgetAction(self)
            deleteAllReferencesWidget = QWidget()
            layout = QHBoxLayout()
            deleteAllReferencesLabel = QLabel(f"Delete ALL References to {node_type}")
            deleteAllReferencesLabel.setStyleSheet("""
                QLabel {
                    color: red;
                    font-weight: bold;
                    font-size: 14px;
                }
                QLabel:hover {
                    background-color: #d3d3d3;
                }
            """)
            layout.addWidget(deleteAllReferencesLabel)
            layout.setContentsMargins(35, 10, 35, 10)
            deleteAllReferencesWidget.setLayout(layout)
            deleteAllReferencesAction.setDefaultWidget(deleteAllReferencesWidget)
        else:
            deleteAllReferencesAction = QAction(f"Delete ALL References to {node_type}", menu)  # type: ignore[assignment]
        deleteAllReferencesAction.triggered.connect(lambda: self.model.deleteNodeEverywhere(item.link.node))
        deleteAllReferencesAction.setShortcut(QKeySequence(Qt.ControlModifier | Qt.ShiftModifier | Qt.Key_Delete))
        deleteAllReferencesAction.setVisible(notAnOrphan)
        menu.addAction(deleteAllReferencesAction)

        return menu

    def _playNodeSound(self, node: DLGEntry | DLGReply):
        if str(node.sound).strip():
            self.playSound(str(node.sound).strip())
        elif str(node.vo_resref).strip():
            self.playSound(str(node.vo_resref).strip())
        else:
            self.blinkWindow()

    def get_link_ref(self, link: DLGLink):
        for ref, copiedLink in self.model.origToOrphanCopy.items():
            if copiedLink == link:
                return ref
        raise KeyError(repr(link))

    def findReferences(self, item: DLGStandardItem | DLGListWidgetItem):
        assert item.link is not None
        assert item.link.node is not None
        node = item.link.node
        self.reference_history = self.reference_history[:self.current_reference_index + 1]
        item_html = item.data(Qt.ItemDataRole.DisplayRole)
        self.current_reference_index += 1
        references = [self.get_link_ref(link) for link in self.core_dlg.getAllNodeReferences(node)]
        self.reference_history.append((references, item_html))
        self.show_reference_dialog(references, item_html)

    def get_item_dlg_paths(self, item: DLGStandardItem | DLGListWidgetItem) -> tuple[str, str, str]:
        link_parent_path = item.data(_LINK_PARENT_NODE_PATH_ROLE)
        link_path = item.link.partial_path()
        linked_to_path = item.link.node.path()
        return link_parent_path, link_path, linked_to_path

    def build_link_display_html(self, path: str, node_info: str, color: str) -> str:
        display_text_1 = f"<div class='link-text' style='color:{color};text-align:center;'>{path}</div>"
        display_text_2 = f"<div class='link-hover-text' style='color:{color};text-align:center;'>{node_info}</div>"
        combined_display = f"""
        <div class='link-container'>
            {display_text_1}
            {display_text_2}
        </div>
        """
        return combined_display

    def show_reference_dialog(self, references: list[weakref.ref[DLGLink]], item_html: str):
        if self.dialog_references is None:
            self.dialog_references = ReferenceChooserDialog(references, self, item_html)
            self.dialog_references.itemChosen.connect(self.onReferenceChosen)
        else:
            self.dialog_references.update_references(references, item_html)
        if self.dialog_references.isHidden():
            self.dialog_references.show()

    def onReferenceChosen(self, item: DLGListWidgetItem):
        link = item.link
        self.jumpToNode(link)

    def jumpToNode(self, link: DLGLink | None):
        if link is None:
            RobustRootLogger().error(f"{link!r} has already been deleted from the tree.")
            return
        if link not in self.model.linkToItems:
            print("Nowhere to jump - orphaned node has no existing links in the tree.")
            return
        item = self.model.linkToItems[link][0]
        index = item.index()
        self.expandToRoot(item)
        self.ui.dialogTree.setCurrentIndex(item.index())
        self.ui.dialogTree.setFocus()  # Set focus to the dialog tree

        # Select the item to highlight it
        selection_model = self.ui.dialogTree.selectionModel()
        selection_model.select(index, QItemSelectionModel.Select | QItemSelectionModel.Rows)

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
    def focusOutEvent(self, e: QFocusEvent):
        self.keysDown.clear()  # Clears the set when focus is lost
        super().focusOutEvent(e)  # Ensures that the default handler is still executed
        print("dlgedit.focusOutEvent: clearing all keys/buttons held down.")

    def closeEvent(self, event: QCloseEvent):
        super().closeEvent(event)
        self.player.stop()
        if self.ui.rightDockWidget.isVisible():
            self.ui.rightDockWidget.close()
        if self.ui.topDockWidget.isVisible():
            self.ui.topDockWidget.close()
        #self.saveWidgetStates()

    def saveWidgetStates(self):
        """Iterates over child widgets and saves their geometry and state."""
        for widget in self.findChildren(QWidget):
            self.setWidgetGeometry(widget)

    def _handleShiftItemKeybind(self, selectedIndex: QModelIndex, selectedItem: DLGStandardItem, key: QtKey):
        aboveIndex = self.ui.dialogTree.indexAbove(selectedIndex)
        belowIndex = self.ui.dialogTree.indexBelow(selectedIndex)
        if self.keysDown in (
            {QtKey.Key_Shift, QtKey.Key_Up},
            {QtKey.Key_Shift, QtKey.Key_Up, QtKey.Key_Alt},
        ):
            print("<SDM> [_handleShiftItemKeybind scope] aboveIndex: %s", aboveIndex)

            if aboveIndex.isValid():
                self.ui.dialogTree.setCurrentIndex(aboveIndex)
            self.model.shiftItem(selectedItem, -1, noSelectionUpdate=True)
        elif self.keysDown in (
            {QtKey.Key_Shift, QtKey.Key_Down},
            {QtKey.Key_Shift, QtKey.Key_Down, QtKey.Key_Alt},
        ):
            belowIndex = self.ui.dialogTree.indexBelow(selectedIndex)
            print("<SDM> [_handleShiftItemKeybind scope] belowIndex: %s", belowIndex)

            if belowIndex.isValid():
                self.ui.dialogTree.setCurrentIndex(belowIndex)
            self.model.shiftItem(selectedItem, 1, noSelectionUpdate=True)
        elif aboveIndex.isValid() and key in (QtKey.Key_Up,) and not self.ui.dialogTree.visualRect(aboveIndex).contains(self.ui.dialogTree.viewport().rect()):
            self.ui.dialogTree.scrollSingleStep("up")
        elif belowIndex.isValid() and key in (QtKey.Key_Down,) and not self.ui.dialogTree.visualRect(belowIndex).contains(self.ui.dialogTree.viewport().rect()):
            self.ui.dialogTree.scrollSingleStep("down")

    def keyPressEvent(
        self,
        event: QKeyEvent,
        *,
        isTreeViewCall: bool = False,
    ):  # sourcery skip: extract-duplicate-method
        if not isTreeViewCall:
            if not self.ui.dialogTree.hasFocus():
                print(f"<SDM> [DLGEditor.keyPressEvent scope] passthrough key {getQtKeyString(event.key())}: dialogTree does not have focus.")
                super().keyPressEvent(event)
                return
            self.ui.dialogTree.keyPressEvent(event)  # this'll call us back immediately, just ensures we don't get called twice for the same event.
            return
        super().keyPressEvent(event)
        key = event.key()
        print("<SDM> [DLGEditor.keyPressEvent scope] key: ", getQtKeyString(event.key()), f"held: {'+'.join([getQtKeyString(k) for k in iter(self.keysDown)])}")
        selectedIndex: QModelIndex = self.ui.dialogTree.currentIndex()
        if not selectedIndex.isValid():
            return

        selectedItem: DLGStandardItem | None = self.model.itemFromIndex(selectedIndex)
        if selectedItem is None:
            if key == QtKey.Key_Insert:
                print("<SDM> [keyPressEvent scope insert1] key: ", key)
                self.model.addRootNode()
            return

        if event.isAutoRepeat() or key in self.keysDown:
            print("DLGEditor.keyPressEvent: event is auto repeat and/or key already in keysDown set.")
            if key in (QtKey.Key_Up, QtKey.Key_Down):
                self.keysDown.add(key)
                self._handleShiftItemKeybind(selectedIndex, selectedItem, key)
            return  # Ignore auto-repeat events and prevent multiple executions on single key
        print(f"DLGEditor.keyPressEvent: {getQtKeyString(key)}, held: {'+'.join([getQtKeyString(k) for k in iter(self.keysDown)])}")
        assert selectedItem.link is not None
        if selectedItem.link.node is None:
            self.blinkWindow()
            return
        print("<SDM> [keyPressEvent scope] item.link.node: ", selectedItem.link.node)

        if not self.keysDown:
            self.keysDown.add(key)
            if key in (QtKey.Key_Delete, QtKey.Key_Backspace):
                self.model.removeLink(selectedItem)
            elif key in (QtKey.Key_Enter, QtKey.Key_Return):
                self.editText(indexes=self.ui.dialogTree.selectedIndexes())
            elif key == QtKey.Key_F:
                self.focusOnNode(selectedItem.link)
            elif key == QtKey.Key_Insert:
                print("<SDM> [keyPressEvent insert2 scope] key: ", key)

                self.model.addChildToItem(selectedItem)
            elif key == QtKey.Key_P:
                print("<SDM> [keyPressEvent play scope] key: ", key)

                sound_resname = self.ui.soundComboBox.currentText().strip()
                voice_resname = self.ui.voiceComboBox.currentText().strip()
                if sound_resname:
                    self.playSound(sound_resname)
                elif voice_resname:
                    self.playSound(voice_resname)
                else:
                    self.blinkWindow()
            return

        self.keysDown.add(key)
        self._handleShiftItemKeybind(selectedIndex, selectedItem, key)
        if self.keysDown in (
            {QtKey.Key_Shift, QtKey.Key_Return},
            {QtKey.Key_Shift, QtKey.Key_Enter},
        ):
            self.setExpandRecursively(selectedItem, set(), expand=True)
        elif self.keysDown in (
            {QtKey.Key_Shift, QtKey.Key_Return, QtKey.Key_Alt},
            {QtKey.Key_Shift, QtKey.Key_Enter, QtKey.Key_Alt},
        ):
            self.setExpandRecursively(selectedItem, set(), expand=False, maxdepth=-1)
        elif QtKey.Key_Control in self.keysDown or event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_G:
                self.show_go_to_bar()
            elif event.key() == Qt.Key_F:
                self.show_find_bar()
            elif QtKey.Key_C in self.keysDown:
                if QtKey.Key_Alt in self.keysDown:
                    self.copyPath(selectedItem.link.node)
                else:
                    self.model.copyLinkAndNode(selectedItem.link)
            elif QtKey.Key_Enter in self.keysDown or QtKey.Key_Return in self.keysDown:
                self.jumpToOriginal(selectedItem)
            elif QtKey.Key_V in self.keysDown:
                self._checkClipboardForJsonNode()
                if not self._copy:
                    print("No node/link copy in memory or on clipboard.")
                    self.blinkWindow()
                    return
                if self._copy.node.__class__ is selectedItem.link.node.__class__:
                    print("Cannot paste link/node here.")
                    self.blinkWindow()
                    return
                if QtKey.Key_Alt in self.keysDown:
                    self.model.pasteItem(selectedItem, asNewBranches=True)
                else:
                    self.model.pasteItem(selectedItem, asNewBranches=False)
            elif QtKey.Key_Delete in self.keysDown:
                if QtKey.Key_Shift in self.keysDown:
                    self.model.deleteNodeEverywhere(selectedItem.link.node)
                else:
                    self.model.deleteSelectedNode()

    def keyReleaseEvent(self, event: QKeyEvent):
        super().keyReleaseEvent(event)
        key = event.key()
        print("<SDM> [keyReleaseEvent scope] key: %s", key)

        if key in self.keysDown:
            self.keysDown.remove(key)
        print(f"DLGEditor.keyReleaseEvent: {getQtKeyString(key)}, held: {'+'.join([getQtKeyString(k) for k in iter(self.keysDown)])}")

    def onSelectionChanged(self, selection: QItemSelection):
        """Updates UI fields based on selected dialog node."""
        self.nodeLoadedIntoUI = False
        selectionIndices = selection.indexes()
        print("<SDM> [onSelectionChanged scope] selectionIndices:\n", ",\n".join([self.model.itemFromIndex(index).text() for index in selectionIndices if self.model.itemFromIndex(index) is not None]))
        if not selectionIndices:
            return
        item: DLGStandardItem | None = self.model.itemFromIndex(selectionIndices[0])
        if item is None:
            return

        assert item.link is not None
        assert item.link.node is not None
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

        self.ui.script1ResrefEdit.setComboBoxText(str(item.link.node.script1))
        self.ui.script1Param1Spin.setValue(item.link.node.script1_param1)
        self.ui.script1Param2Spin.setValue(item.link.node.script1_param2)
        self.ui.script1Param3Spin.setValue(item.link.node.script1_param3)
        self.ui.script1Param4Spin.setValue(item.link.node.script1_param4)
        self.ui.script1Param5Spin.setValue(item.link.node.script1_param5)
        self.ui.script1Param6Edit.setText(item.link.node.script1_param6)

        self.ui.script2ResrefEdit.setComboBoxText(str(item.link.node.script2))
        self.ui.script2Param1Spin.setValue(item.link.node.script2_param1)
        self.ui.script2Param2Spin.setValue(item.link.node.script2_param2)
        self.ui.script2Param3Spin.setValue(item.link.node.script2_param3)
        self.ui.script2Param4Spin.setValue(item.link.node.script2_param4)
        self.ui.script2Param5Spin.setValue(item.link.node.script2_param5)
        self.ui.script2Param6Edit.setText(item.link.node.script2_param6)

        self.ui.condition1ResrefEdit.setComboBoxText(str(item.link.active1))
        self.ui.condition1Param1Spin.setValue(item.link.active1_param1)
        self.ui.condition1Param2Spin.setValue(item.link.active1_param2)
        self.ui.condition1Param3Spin.setValue(item.link.active1_param3)
        self.ui.condition1Param4Spin.setValue(item.link.active1_param4)
        self.ui.condition1Param5Spin.setValue(item.link.active1_param5)
        self.ui.condition1Param6Edit.setText(item.link.active1_param6)
        self.ui.condition1NotCheckbox.setChecked(item.link.active1_not)
        self.ui.condition2ResrefEdit.setComboBoxText(str(item.link.active2))
        self.ui.condition2Param1Spin.setValue(item.link.active2_param1)
        self.ui.condition2Param2Spin.setValue(item.link.active2_param2)
        self.ui.condition2Param3Spin.setValue(item.link.active2_param3)
        self.ui.condition2Param4Spin.setValue(item.link.active2_param4)
        self.ui.condition2Param5Spin.setValue(item.link.active2_param5)
        self.ui.condition2Param6Edit.setText(item.link.active2_param6)
        self.ui.condition2NotCheckbox.setChecked(item.link.active2_not)

        self.refreshAnimList()
        self.ui.emotionSelect.setCurrentIndex(item.link.node.emotion_id)
        self.ui.expressionSelect.setCurrentIndex(item.link.node.facial_id)
        self.ui.soundComboBox.setComboBoxText(str(item.link.node.sound))
        self.ui.soundCheckbox.setChecked(item.link.node.sound_exists)
        self.ui.voiceComboBox.setComboBoxText(str(item.link.node.vo_resref))

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
        self.updateLabels()
        self.nodeLoadedIntoUI = True
        self.handleSoundChecked()

    def updateLabels(self):
        def updateLabel(label: QLabel, widget: QWidget, default_value: int | str | tuple[int | str, ...]):
            def is_default(value, default):
                if isinstance(default, tuple):
                    return value in default
                return value == default
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
                font.setWeight(65)
            else:
                label.setText(original_text)
                font.setWeight(QFont.Weight.Normal)
            label.setFont(font)
        updateLabel(self.ui.speakerEditLabel, self.ui.speakerEdit, "")
        updateLabel(self.ui.questLabel, self.ui.questEdit, "")
        updateLabel(self.ui.plotXpPercentLabel, self.ui.plotXpSpin, 1)
        updateLabel(self.ui.plotIndexLabel, self.ui.plotIndexCombo, -1)
        updateLabel(self.ui.questEntryLabel, self.ui.questEntrySpin, 0)
        updateLabel(self.ui.listenerTagLabel, self.ui.listenerEdit, "")
        updateLabel(self.ui.script1Label, self.ui.script1ResrefEdit, "")
        updateLabel(self.ui.script2Label, self.ui.script2ResrefEdit, "")
        updateLabel(self.ui.conditional1Label, self.ui.condition1ResrefEdit, "")
        updateLabel(self.ui.conditional2Label, self.ui.condition2ResrefEdit, "")
        updateLabel(self.ui.emotionLabel, self.ui.emotionSelect, "[Modded Entry #0]")
        updateLabel(self.ui.expressionLabel, self.ui.expressionSelect, "[Modded Entry #0]")
        updateLabel(self.ui.soundLabel, self.ui.soundComboBox, "")
        updateLabel(self.ui.voiceLabel, self.ui.voiceComboBox, "")
        updateLabel(self.ui.cameraIdLabel, self.ui.cameraIdSpin, -1)
        updateLabel(self.ui.cameraAnimLabel, self.ui.cameraAnimSpin, (0, -1))
        updateLabel(self.ui.cameraVidEffectLabel, self.ui.cameraEffectSelect, -1)
        updateLabel(self.ui.cameraAngleLabel, self.ui.cameraAngleSelect, "Auto")
        updateLabel(self.ui.nodeIdLabel, self.ui.nodeIdSpin, (0, -1))
        updateLabel(self.ui.alienRaceNodeLabel, self.ui.alienRaceNodeSpin, 0)
        updateLabel(self.ui.postProcNodeLabel, self.ui.postProcSpin, 0)
        updateLabel(self.ui.delayNodeLabel, self.ui.delaySpin, (0, -1))
        updateLabel(self.ui.logicLabel, self.ui.logicSpin, 0)
        updateLabel(self.ui.waitFlagsLabel, self.ui.waitFlagSpin, 0)
        updateLabel(self.ui.fadeTypeLabel, self.ui.fadeTypeSpin, 0)

    def handleSoundChecked(self, *args):
        if not self.nodeLoadedIntoUI:
            return
        if not self.ui.soundCheckbox.isChecked():
            # self.ui.soundComboBox.setDisabled(True)
            # self.ui.voiceComboBox.setDisabled(True)
            self.ui.soundButton.setDisabled(True)
            self.ui.soundButton.setToolTip("Exists must be checked.")
            #self.ui.soundComboBox.setToolTip("Exists must be checked.")
            #self.ui.voiceComboBox.setToolTip("Exists must be checked.")
        else:
            # self.ui.soundComboBox.setEnabled(True)
            # self.ui.voiceComboBox.setEnabled(True)
            self.ui.voiceButton.setEnabled(True)
            self.ui.voiceButton.setToolTip("")
            #self.ui.soundComboBox.setToolTip("")
            #self.ui.voiceComboBox.setToolTip("")

    def setAllWhatsThis(self):
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
        self.ui.stuntList.setWhatsThis("List of stunts")
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

    def onNodeUpdate(self):
        """Updates node properties based on UI selections."""
        selectedIndices = self.ui.dialogTree.selectedIndexes()
        if not selectedIndices:
            print("onNodeUpdate: no selected indices, early return")
            return
        if not self.nodeLoadedIntoUI:
            print("nodeLoadedIntoUI is False, not running `onNodeUpdate`...")
            return
        index: QModelIndex = selectedIndices[0]
        if not index.isValid():
            RobustRootLogger().warning("onNodeUpdate: index invalid, early return")
            return
        item: DLGStandardItem | None = self.model.itemFromIndex(index)
        if item is None or item.isDeleted():
            RobustRootLogger().warning("onNodeUpdate: no item for this selected index, or item was deleted.")
            return
        print("onNodeUpdate")
        print("<SDM> [onNodeUpdate scope] selectedIndices: %s", [self.ui.dialogTree.getIdentifyingText(indx) for indx in selectedIndices])
        assert item.link is not None
        assert item.link.node is not None
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
        self.updateLabels()
        self.handleSoundChecked()
        self.model._updateCopies(item.link, item)  # noqa: SLF001

    def onItemExpanded(self, index: QModelIndex):
        #self.ui.dialogTree.model().layoutAboutToBeChanged.emit()  # emitting this causes annoying ui jitter as it resizes.
        item = self.model.itemFromIndex(index)
        assert item is not None
        if item.hasChildren() and item.child(0, 0).data(_FUTURE_EXPAND_ROLE):
            self._fullyLoadFutureExpandItem(item, index)
        if self.dlg_settings.get("ExpandRootChildren", False) and item.parent() is None:
            self.setExpandRecursively(item, set(), expand=True)
        self.ui.dialogTree.debounceLayoutChanged(preChangeEmit=False)

    def _fullyLoadFutureExpandItem(self, item: DLGStandardItem, sourceIndex: QModelIndex):
        item.removeRow(0)  # Remove the placeholder
        self.model.blockSignals(True)
        assert item.link is not None
        assert item.link.node is not None
        self.model.beginInsertRows(sourceIndex, 0, len(item.link.node.links)-1)
        for child_link in item.link.node.links:
            child_item = DLGStandardItem(link=child_link)
            self.model.loadDLGItemRec(child_item)
            item.appendRow(child_item)
        self.model.endInsertRows()
        self.model.blockSignals(False)

    def onAddStuntClicked(self):
        dialog = CutsceneModelDialog(self)
        print("<SDM> [onAddStuntClicked scope] dialog: ", dialog)

        if dialog.exec_():
            self.core_dlg.stunts.append(dialog.stunt())
            self.refreshStuntList()

    def onRemoveStuntClicked(self):
        selectedTreeIndexes = self.ui.dialogTree.selectedIndexes()
        if not selectedTreeIndexes:
            QMessageBox(QMessageBox.Icon.Information, "No nodes selected", "Select an item from the tree first.").exec_()
            return
        selectedStuntItems = self.ui.stuntList.selectedItems()
        if not selectedStuntItems:
            QMessageBox(QMessageBox.Icon.Information, "No stunts selected", "Select an existing stunt from the above list first, or create one.").exec_()
            return
        print("<SDM> [onRemoveStuntClicked scope] selectedStuntItems: ", selectedStuntItems, "len: ", len(selectedStuntItems))
        print("<SDM> [onRemoveStuntClicked scope] selectedTreeIndexes: ", selectedTreeIndexes, "len: ", len(selectedTreeIndexes))
        stunt: DLGStunt = selectedStuntItems[0].data(Qt.ItemDataRole.UserRole)
        print("<SDM> [onRemoveStuntClicked scope] DLGStunt: ", repr(stunt))
        self.core_dlg.stunts.remove(stunt)
        self.refreshStuntList()

    def onEditStuntClicked(self):
        selectedTreeIndexes = self.ui.dialogTree.selectedIndexes()
        if not selectedTreeIndexes:
            QMessageBox(QMessageBox.Icon.Information, "No nodes selected", "Select an item from the tree first.").exec_()
            return
        selectedStuntItems = self.ui.stuntList.selectedItems()
        if not selectedStuntItems:
            QMessageBox(QMessageBox.Icon.Information, "No stunts selected", "Select an existing stunt from the above list first, or create one.").exec_()
            return
        print("<SDM> [onEditStuntClicked scope] selectedStuntItems: ", selectedStuntItems, "len: ", len(selectedStuntItems))
        print("<SDM> [onEditStuntClicked scope] selectedTreeIndexes: ", selectedTreeIndexes, "len: ", len(selectedTreeIndexes))
        stunt: DLGStunt = selectedStuntItems[0].data(Qt.ItemDataRole.UserRole)
        print("<SDM> [onEditStuntClicked scope] DLGStunt: ", repr(stunt))

        dialog = CutsceneModelDialog(self, stunt)
        if dialog.exec_():
            stunt.stunt_model = dialog.stunt().stunt_model
            print("<SDM> [onEditStuntClicked scope] stunt.stunt_model: ", stunt.stunt_model)

            stunt.participant = dialog.stunt().participant
            print("<SDM> [onEditStuntClicked scope] stunt.participant: ", stunt.participant)

            self.refreshStuntList()

    def refreshStuntList(self):
        self.ui.stuntList.clear()
        for stunt in self.core_dlg.stunts:
            text = f"{stunt.stunt_model} ({stunt.participant})"
            print("<SDM> [refreshStuntList scope] text: ", text)

            item = QListWidgetItem(text)
            print("<SDM> [refreshStuntList scope] item: ", item)

            item.setData(Qt.ItemDataRole.UserRole, stunt)
            self.ui.stuntList.addItem(item)

    def onAddAnimClicked(self):
        selectedIndexes = self.ui.dialogTree.selectedIndexes()
        if not selectedIndexes:
            QMessageBox(QMessageBox.Icon.Information, "No nodes selected", "Select an item from the tree first.").exec_()
            return
        index: QModelIndex = self.ui.dialogTree.selectedIndexes()[0]
        print("<SDM> [onAddAnimClicked scope] QModelIndex: ", self.ui.dialogTree.getIdentifyingText(index))
        item: DLGStandardItem | None = self.model.itemFromIndex(index)
        dialog = EditAnimationDialog(self, self._installation)
        if dialog.exec_():
            assert item.link is not None
            assert item.link.node is not None
            item.link.node.animations.append(dialog.animation())
            self.refreshAnimList()

    def onRemoveAnimClicked(self):
        selectedTreeIndexes = self.ui.dialogTree.selectedIndexes()
        if not selectedTreeIndexes:
            QMessageBox(QMessageBox.Icon.Information, "No nodes selected", "Select an item from the tree first.").exec_()
            return
        selectedAnimItems = self.ui.animsList.selectedItems()
        if not selectedAnimItems:
            QMessageBox(QMessageBox.Icon.Information, "No animations selected", "Select an existing animation from the above list first, or create one.").exec_()
            return
        index: QModelIndex = selectedTreeIndexes[0]
        print("<SDM> [onAddAnimClicked scope] QModelIndex: ", self.ui.dialogTree.getIdentifyingText(index))
        item: DLGStandardItem | None = self.model.itemFromIndex(index)
        if item is None:
            print("onRemoveAnimClicked: itemFromIndex returned None")
            self.blinkWindow()
            return
        animItem: QListWidgetItem = selectedAnimItems[0]  # type: ignore[arg-type]
        anim: DLGAnimation = animItem.data(Qt.ItemDataRole.UserRole)
        assert item.link is not None
        assert item.link.node is not None
        item.link.node.animations.remove(anim)
        self.refreshAnimList()

    def onEditAnimClicked(self):
        selectedTreeIndexes = self.ui.dialogTree.selectedIndexes()
        if not selectedTreeIndexes:
            QMessageBox(QMessageBox.Icon.Information, "No nodes selected", "Select an item from the tree first.").exec_()
            return
        selectedAnimItems = self.ui.animsList.selectedItems()
        if not selectedAnimItems:
            QMessageBox(QMessageBox.Icon.Information, "No animations selected", "Select an existing animation from the above list first.").exec_()
            return
        animItem: QListWidgetItem = selectedAnimItems[0]  # type: ignore[arg-type]
        anim: DLGAnimation = animItem.data(Qt.ItemDataRole.UserRole)
        dialog = EditAnimationDialog(self, self._installation, anim)
        if dialog.exec_():
            anim.animation_id = dialog.animation().animation_id
            print("<SDM> [onEditAnimClicked scope] anim.animation_id: ", anim.animation_id)

            anim.participant = dialog.animation().participant
            print("<SDM> [onEditAnimClicked scope] anim.participant: ", anim.participant)

            self.refreshAnimList()

    def refreshAnimList(self):
        """Refreshes the animations list."""
        self.ui.animsList.clear()
        animations_2da: TwoDA | None= self._installation.htGetCache2DA(HTInstallation.TwoDA_DIALOG_ANIMS)
        if animations_2da is None:
            print(f"refreshAnimList: {HTInstallation.TwoDA_DIALOG_ANIMS}.2da not found.")

        for index in self.ui.dialogTree.selectedIndexes():
            print("<SDM> [onAddAnimClicked scope] QModelIndex: ", self.ui.dialogTree.getIdentifyingText(index))
            if not index.isValid():
                continue
            item: DLGStandardItem | None = self.model.itemFromIndex(index)
            if item is None or item.link is None or item.link.node is None:
                continue
            for anim in item.link.node.animations:
                name: str = str(anim.animation_id)
                if animations_2da.get_height() > anim.animation_id:
                    name = animations_2da.get_cell(anim.animation_id, "name")
                    print("<SDM> [refreshAnimList scope] name: ", name)

                text: str = f"{name} ({anim.participant})"
                animItem = QListWidgetItem(text)
                print("<SDM> [refreshAnimList scope] item: ", text)

                animItem.setData(Qt.ItemDataRole.UserRole, anim)
                self.ui.animsList.addItem(animItem)


class ReferenceChooserDialog(QDialog):
    itemChosen: ClassVar[QtCore.Signal] = QtCore.Signal()

    def __init__(self, references: list[weakref.ref[DLGLink]], parent: DLGEditor, item_text: str):
        assert isinstance(parent, DLGEditor)
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowFlags(QtCore.Qt.WindowCloseButtonHint & ~QtCore.Qt.WindowContextHelpButtonHint))
        self.setWindowTitle("Node References")

        layout = QVBoxLayout(self)
        self.label = QLabel()
        self.editor: DLGEditor = parent
        self.label.setTextFormat(Qt.TextFormat.RichText)
        self.listWidget = DLGListWidget(parent)  # HACK: fix later (set editor attr properly in listWidget)
        self.listWidget.useHoverText = False
        self.listWidget.setParent(self)
        self.listWidget.setItemDelegate(HTMLDelegate(self.listWidget))
        layout.addWidget(self.listWidget)

        max_width = 0
        for linkref in references:
            link = linkref()
            if link is None:
                continue
            item = DLGListWidgetItem(link=link, ref=linkref)
            link_parent_path, link_partial_path, node_path = self.editor.get_item_dlg_paths(item)
            if link_parent_path:
                link_parent_path += "\\"
            else:
                link_parent_path = ""

            # Build the HTML display
            self.listWidget.updateItem(item)
            self.listWidget.addItem(item)
            max_width = max(max_width, self.calculate_html_width(item.data(Qt.ItemDataRole.DisplayRole)))

        buttonLayout = QHBoxLayout()
        self.backButton = QPushButton()
        self.backButton.setIcon(self.style().standardIcon(QStyle.SP_ArrowBack))
        self.forwardButton = QPushButton()
        self.forwardButton.setIcon(self.style().standardIcon(QStyle.SP_ArrowForward))
        okButton = QPushButton("OK")
        cancelButton = QPushButton("Cancel")
        buttonLayout.addWidget(self.backButton)
        buttonLayout.addWidget(self.forwardButton)
        buttonLayout.addWidget(okButton)
        buttonLayout.addWidget(cancelButton)

        layout.addLayout(buttonLayout)

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
        parent = super().parent()
        assert isinstance(parent, DLGEditor)
        return parent

    def update_item_sizes(self):
        for i in range(self.listWidget.count()):
            item: DLGListWidgetItem | None = self.listWidget.item(i)
            if item is None:
                RobustRootLogger().warning(f"ReferenceChooser.update_item_sizes({i}): Item was None unexpectedly.")
                continue
            item.setSizeHint(self.listWidget.itemDelegate().sizeHint(self.listWidget.viewOptions(), self.listWidget.indexFromItem(item)))

    def calculate_html_width(self, html: str) -> int:
        doc = QTextDocument()
        doc.setHtml(html)
        return int(doc.idealWidth())

    def get_stylesheet(self) -> str:
        font_size = self.parent().ui.dialogTree.text_size
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
        selectedItem = self.listWidget.currentItem()
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
        self.listWidget.clear()
        node_path = ""
        for linkref in referenceItems:
            link = linkref()
            if link is None:
                continue
            if link.node is None:
                continue
            link_partial_path, node_path = link.partial_path(), link.node.path()
            color = "red" if isinstance(link.node, DLGEntry) else "blue"
            display_text_1 = f"<div class='link-text' style='color:{color};text-align:center;'>{link_partial_path}</div>"
            display_text_2 = f"<div class='link-hover-text' style='color:{color};text-align:center;'>{node_path}</div>"
            combined_display = f"""
            <div class='link-container'>
                {display_text_1}
                {display_text_2}
            </div>
            """
            listItem = DLGListWidgetItem(link=link, ref=linkref)
            listItem.setData(Qt.ItemDataRole.DisplayRole, combined_display)
            self.listWidget.addItem(listItem)
        self.update_item_sizes()
        self.adjustSize()
        self.setWindowTitle(f"Node References: {node_path}")
        self.update_button_states()

    def update_button_states(self):
        parent = self.parent()
        self.backButton.setEnabled(parent.current_reference_index > 0)
        self.forwardButton.setEnabled(parent.current_reference_index < len(parent.reference_history) - 1)


class DLGSettings:
    def __init__(self):
        self.settings = QSettings("HolocronToolsetV3", "DLGEditor")

    def get(self, key: str, default: Any) -> Any:
        return self.settings.value(key, default, default.__class__)

    def set(self, key: str, value: Any):
        self.settings.setValue(key, value)

    def textElideMode(self, default: int) -> int:
        return self.get("textElideMode", default)

    def setTextElideMode(self, value: int):
        self.set("textElideMode", value)

    def focusPolicy(self, default: int) -> int:
        return self.get("focusPolicy", default)

    def setFocusPolicy(self, value: int):
        self.set("focusPolicy", value)

    def layoutDirection(self, default: int) -> int:
        return self.get("layoutDirection", default)

    def setLayoutDirection(self, value: int):  # noqa: FBT001
        self.set("layoutDirection", value)

    def verticalScrollMode(self, default: int) -> int:  # noqa: FBT001
        return self.get("verticalScrollMode", default)

    def setVerticalScrollMode(self, value: int):  # noqa: FBT001
        self.set("verticalScrollMode", value)

    def uniformRowHeights(self, default: bool) -> bool:  # noqa: FBT001
        return self.get("uniformRowHeights", default)

    def setUniformRowHeights(self, value: bool):  # noqa: FBT001
        self.set("uniformRowHeights", value)

    def animations(self, default: bool) -> bool:  # noqa: FBT001
        return self.get("animations", default)

    def setAnimations(self, value: bool):  # noqa: FBT001
        self.set("animations", value)

    def autoScroll(self, default: bool) -> bool:  # noqa: FBT001
        return self.get("autoScroll", default)

    def setAutoScroll(self, value: bool):  # noqa: FBT001
        self.set("autoScroll", value)

    def expandsOnDoubleClick(self, default: bool) -> bool:  # noqa: FBT001
        return self.get("expandsOnDoubleClick", default)

    def setExpandsOnDoubleClick(self, value: bool):  # noqa: FBT001
        self.set("expandsOnDoubleClick", value)

    def autoFillBackground(self, default: bool) -> bool:  # noqa: FBT001
        return self.get("autoFillBackground", default)

    def setAutoFillBackground(self, value: bool):  # noqa: FBT001
        self.set("autoFillBackground", value)

    def alternatingRowColors(self, default: bool) -> bool:  # noqa: FBT001
        return self.get("alternatingRowColors", default)

    def setAlternatingRowColors(self, value: bool):  # noqa: FBT001
        self.set("alternatingRowColors", value)

    def indentation(self, default: int) -> int:
        return self.get("indentation", default)

    def setIndentation(self, value: int):
        self.set("indentation", value)

    def fontSize(self, default: int) -> int:
        return self.get("fontSize", default)

    def setFontSize(self, value: int):
        self.set("fontSize", value)

    def showVerboseHoverHints(self, default: bool) -> bool:
        return self.get("showVerboseHoverHints", default)

    def setShowVerboseHoverHints(self, value: bool):
        self.set("showVerboseHoverHints", value)

    def tslWidgetHandling(self, default: str) -> str:
        return self.get("TSLWidgetHandling", default)

    def setTslWidgetHandling(self, value: str):
        self.set("TSLWidgetHandling", value)

    def loadAll(self, editor: DLGEditor):
        editor.ui.dialogTree.setTextElideMode(self.get("textElideMode", editor.ui.dialogTree.textElideMode()))
        editor.ui.dialogTree.setFocusPolicy(self.get("focusPolicy", editor.ui.dialogTree.focusPolicy()))
        editor.ui.dialogTree.setLayoutDirection(self.get("layoutDirection", editor.ui.dialogTree.layoutDirection()))
        editor.ui.dialogTree.setVerticalScrollMode(self.get("verticalScrollMode", editor.ui.dialogTree.verticalScrollMode()))
        editor.ui.dialogTree.setUniformRowHeights(self.get("uniformRowHeights", editor.ui.dialogTree.uniformRowHeights()))
        editor.ui.dialogTree.setAnimated(self.get("animations", editor.ui.dialogTree.isAnimated()))
        editor.ui.dialogTree.setAutoScroll(self.get("autoScroll", editor.ui.dialogTree.hasAutoScroll()))
        editor.ui.dialogTree.setExpandsOnDoubleClick(self.get("expandsOnDoubleClick", editor.ui.dialogTree.expandsOnDoubleClick()))
        editor.ui.dialogTree.setAutoFillBackground(self.get("autoFillBackground", editor.ui.dialogTree.autoFillBackground()))
        editor.ui.dialogTree.setAlternatingRowColors(self.get("alternatingRowColors", editor.ui.dialogTree.alternatingRowColors()))
        editor.ui.dialogTree.setIndentation(self.get("indentation", editor.ui.dialogTree.indentation()))
        editor.ui.dialogTree.text_size = self.get("fontSize", editor.ui.dialogTree.text_size)
        editor.ui.dialogTree.itemDelegate().setVerticalSpacing(self.get("verticalSpacing", editor.ui.dialogTree.itemDelegate().customVerticalSpacing))
        self.setTslWidgetHandling(self.get("TSLWidgetHandling", "Default"))
        if self.get("showVerboseHoverHints", False):
            editor.setupExtraTooltipMode()
