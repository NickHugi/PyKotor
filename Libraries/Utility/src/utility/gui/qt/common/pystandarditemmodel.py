from __future__ import annotations

import sys

from typing import TYPE_CHECKING, Any, Iterable, cast, overload

from qtpy.QtCore import QAbstractItemModel, QByteArray, QDataStream, QIODevice, QMimeData, QModelIndex, QVariant, Qt
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QAction, QApplication, QHBoxLayout, QInputDialog, QMainWindow, QMenu, QPushButton, QTreeView, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from qtpy.QtCore import QObject, QSize
    from qtpy.QtGui import QBrush, QFont
    from typing_extensions import Self


class PyQStandardItem:
    class ItemType(int):
        """An enumeration class used to define item types within the PyQStandardItem.

        The `ItemType` class is a simple integer-based enumeration that categorizes
        items in a model. The type of an item determines how it can be treated
        within the model-view architecture. This class provides two constants:

        - `Type` (value `0`): Represents a generic, standard item. This is the
            default type assigned to items created in the model. It's used when
            no specific item type is necessary.

        - `UserType` (value `1000`): Serves as a base value for user-defined item
            types. Developers can define custom item types starting from this value
            to avoid conflicts with the built-in types provided by the framework.
            Custom types are useful when you need to extend the functionality of items in a model.

        Example Usage:
        ```
        custom_type = PyQStandardItem.ItemType.UserType + 1
        item = PyQStandardItem()
        item.setType(custom_type)
        ```
        """
        Type = 0
        UserType = 1000

    Type = ItemType.Type
    UserType = ItemType.UserType

    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, text: str) -> None: ...
    @overload
    def __init__(self, icon: QIcon, text: str) -> None: ...
    @overload
    def __init__(self, rows: int, columns: int = 1) -> None: ...
    @overload
    def __init__(self, other: PyQStandardItem) -> None: ...

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ):
        self._data: dict[int, Any] = {}
        self._parent: PyQStandardItem | None = None
        self._children: list[tuple[PyQStandardItem | None, ...]] = []
        self._roleNames: dict[int, QByteArray | bytes | bytearray] = {}
        self._flags: Qt.ItemFlags | Qt.ItemFlag | int = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        self._model: QAbstractItemModel | None = None
        self._rows: int = 0
        self._columns: int = 0
        if args or kwargs:
            self._handle_init_overloads(*args, **kwargs)

    def _handle_init_overloads(  # noqa: PLR0912, C901
        self,
        *args: Any,
        text: str | None = None,
        icon: QIcon | None = None,
        rows: int | None = None,
        columns: int = 1,
        other: PyQStandardItem | None = None,
    ):
        if args:
            first_arg = args[0]
            if isinstance(first_arg, str):
                text = first_arg
            elif isinstance(first_arg, QIcon):
                icon = first_arg
            elif isinstance(first_arg, int):
                rows = first_arg
            elif isinstance(first_arg, PyQStandardItem):
                other = first_arg

        if len(args) > 1:
            second_arg = args[1]
            if isinstance(second_arg, str) and icon is not None:
                text = second_arg
            elif isinstance(second_arg, int) and rows is not None:
                columns = second_arg

        # Handle text and optional icon constructor
        if text is not None:
            self.setText(text)
            if icon is not None:
                self.setIcon(icon)
            return

        # Handle copy constructor
        if other is not None:
            self._data.clear()
            self._data.update(other._data)  # noqa: SLF001
            self._flags = other._flags  # noqa: SLF001
            for row in other._children:  # noqa: SLF001
                self.appendRow(tuple(None if child is None else child.clone() for child in row))
            return

        # Handle rows and columns constructor
        if rows:
            assert columns is not None, "`columns` must be provided when `rows` is passed."
            self.setRowCount(rows)
            self.setColumnCount(columns)
            return

        error_message = (
            "Invalid arguments for PyQStandardItem constructor.\n"
            "Expected one of the following combinations:\n"
            "  - No arguments (default constructor)\n"
            f"  - text: str ({text})\n"
            f"  - icon: QIcon ({icon}), text: str ({text})\n"
            f"  - rows: int ({rows}), columns: int ({columns})\n"
            f"  - other: PyQStandardItem ({other})\n"
            f"Received args: {args}"
        )
        raise TypeError(error_message)

    def _childIndex(self, row: int, column: int) -> int:
        if row < 0 or row >= self._rows or column < 0 or column >= self._columns:
            return -1
        return (row * self._columns) + column

    def _setChild(self, row: int, column: int, item: PyQStandardItem, *, emitChanged: bool = True):
        if item == self:
            raise ValueError("Cannot set an item as a child of itself.")
        if row < 0 or column < 0:
            return
        if self._rows <= row:
            self.setRowCount(row + 1)
        if self._columns <= column:
            self.setColumnCount(column + 1)
        index = self._childIndex(row, column)
        old_item = self._children[index]
        if item == old_item:
            return
        if item:
            if item._parent is not None:  # noqa: SLF001
                raise ValueError("Duplicate insertion of item.")
            item._parent = self  # noqa: SLF001
            item._model = self._model  # noqa: SLF001
        if old_item is not None:
            old_item._model = None  # noqa: SLF001
        self._children[index] = (item,)  # Wrap item in a tuple
        if self._model is not None and emitChanged:
            self._model.itemChanged(item)

    def __repr__(self) -> str:
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
                256: "UserRole"
            }
            formatted_cache = {}
            for k, v in cache.items():
                repr_v = repr(v)
                formatted_key = role_map.get(k, f"UserRole+{k - 256}" if k >= 256 else str(k))  # noqa: PLR2004
                formatted_cache[formatted_key] = f"{repr_v[:30]}..." if len(repr_v) > 30 else repr_v  # noqa: PLR2004
            return formatted_cache

        details = {
            "Text": repr(self._data.get(Qt.ItemDataRole.DisplayRole, QVariant())),
            "Children Count": str(self.childCount()),
            "Roles": str(format_cache(self._data))
        }
        if self._parent:
            details["Parent"] = f"Parent Row: {self.row()}"
        return f"{self.__class__.__name__}({', '.join(f'{key}: {value}' for key, value in details.items())})"

    def _position(self):
        if self._parent is None:
            return (-1, -1)
        idx = self._parent._childIndex(self)  # noqa: SLF001
        if idx == -1:
            return (-1, -1)
        column_count = self._parent.columnCount()
        return (idx // column_count, idx % column_count)

    def appendChild(self, child: PyQStandardItem):
        child._parent = self  # noqa: SLF001
        self._children.append(child)

    def child(self, row: int) -> PyQStandardItem | None:
        return self._children[row] if 0 <= row < len(self._children) else None

    def childCount(self) -> int:
        return len(self._children)

    def setColumnCount(self, columns: int) -> None:
        for child in self._children:
            if isinstance(child, PyQStandardItem):
                child.setColumnCount(columns)

    def data(self, role: Qt.ItemDataRole | int = Qt.ItemDataRole.DisplayRole) -> Any:
        return self._data.get(role, QVariant())

    def setData(self, value: Any, role: Qt.ItemDataRole | int = Qt.ItemDataRole.EditRole):
        if role == Qt.ItemDataRole.EditRole:
            role = Qt.ItemDataRole.DisplayRole
        self._data[role] = value
        self.emitDataChanged()

    def clearData(self):
        self._data.clear()

    def parent(self) -> PyQStandardItem | None:
        return self._parent

    def row(self) -> int:
        if self._parent:
            return self._parent._children.index(self)  # noqa: SLF001
        return 0

    def column(self) -> int:
        """Returns the column index of this item in its parent.
        If the item has no parent, this returns 0 (as in Qt's behavior).
        """
        if self._parent is None:
            return 0
        return self._parent._children.index(self) % self._parent.columnCount()  # noqa: SLF001

    def removeChild(self, row: int):
        if 0 <= row < len(self._children):
            self._children.pop(row)

    def setRoleNames(self, roleNames: dict[int, QByteArray | bytes | bytearray]):  # noqa: N803
        self._roleNames = roleNames

    def roleNames(self) -> dict[int, QByteArray | bytes | bytearray]:
        return self._roleNames

    def removeChildren(self):
        self._children.clear()

    @overload
    def insertRow(self, row: int, items: Iterable[PyQStandardItem]) -> None: ...
    @overload
    def insertRow(self, arow: int, aitem: PyQStandardItem) -> None: ...
    def insertRow(self, *args: Any, **kwargs: Any) -> None:
        row: int = args[0] if len(args) > 0 and isinstance(args[0], int) else kwargs.get("row", kwargs["arow"])
        items: Iterable[PyQStandardItem] = ([args[1]] if isinstance(args[1], PyQStandardItem) else args[1]) if len(args) > 1 else kwargs.get("items", [kwargs["aitem"]])
        for item in items:
            item._parent = self  # noqa: SLF001
            self._children.insert(row, item)

    @overload
    def appendRow(self, items: Iterable[PyQStandardItem]) -> None: ...
    @overload
    def appendRow(self, aitem: PyQStandardItem) -> None: ...
    def appendRow(self, *args: Any, **kwargs: Any) -> None:
        items: Iterable[PyQStandardItem] = args[0] if len(args) > 0 else kwargs.get("items", [kwargs["aitem"]])
        for item in items:
            self.appendChild(item)

    def takeChild(self, row: int) -> PyQStandardItem | None:
        if 0 <= row < len(self._children):
            return self._children.pop(row)
        return None

    def takeRow(self, row: int) -> list[PyQStandardItem | None]:
        if 0 <= row < len(self._children):
            return [self._children.pop(row)]
        return []

    @overload
    def insertRows(self, row: int, count: int) -> None: ...
    @overload
    def insertRows(self, row: int, items: Iterable[PyQStandardItem]) -> None: ...
    def insertRows(self, *args: Any, **kwargs: Any) -> None:
        row: int = kwargs.get("row", args[1] if kwargs.get("items") is None else args[0])
        _arg2: Iterable[PyQStandardItem] | int | None = kwargs.get("items", args[0] if "row" in kwargs else args[1])
        if isinstance(_arg2, Iterable):
            items: Iterable[PyQStandardItem] = _arg2
            count: int = len(tuple(_arg2))
        else:
            count = kwargs.get("count", args[0] if "row" in kwargs else args[1])
            items = [PyQStandardItem() for _ in range(count)]  # Generate the items
        for i, item in enumerate(items):
            self.insertRow(row + i, item)

    def removeRow(self, row: int) -> None:
        if 0 <= row < len(self._children):
            self._children.pop(row)
            self.emitDataChanged()

    @overload
    def removeRows(self, row: int, count: int) -> None: ...
    @overload
    def removeRows(self, row: int, items: Iterable[PyQStandardItem]) -> None: ...
    def removeRows(self, *args: Any, **kwargs: Any) -> None:
        row: int = kwargs.get("row", args[1] if kwargs.get("items") is None else args[0])
        _arg2: Iterable[PyQStandardItem] | int | None = kwargs.get("items", args[0] if "row" in kwargs else args[1])
        if isinstance(_arg2, Iterable):
            count: int = len(tuple(_arg2))
        else:
            count = kwargs.get("count", args[0] if "row" in kwargs else args[1])
        for _ in range(count):
            self.removeRow(row)

    def clone(self) -> Self:
        """Creates a copy of this item."""
        new_item = self.__class__()

        new_item._data = self._data.copy()  # noqa: SLF001
        new_item._flags = self._flags  # noqa: SLF001
        new_item._roleNames = self._roleNames.copy()  # noqa: SLF001
        new_item._model = self._model  # noqa: SLF001

        for row in self._children:
            cloned_row = tuple(child.clone() if child is not None else None for child in row)
            new_item._children.append(cloned_row)  # noqa: SLF001

        return new_item

    def setText(self, text: str) -> None:
        """Sets the display role data."""
        self.setData(text, Qt.ItemDataRole.DisplayRole)

    def text(self) -> str:
        """Returns the display role data as a string."""
        return self.data(Qt.ItemDataRole.DisplayRole)

    def setIcon(self, icon: QIcon) -> None:
        """Sets the decoration role data."""
        self.setData(icon, Qt.DecorationRole)

    def icon(self) -> QIcon | None:
        """Returns the decoration role data."""
        return self.data(Qt.DecorationRole)

    def setCheckable(self, checkable: bool) -> None:  # noqa: FBT001
        """Sets whether the item is checkable."""
        if checkable:
            self._flags |= Qt.ItemIsUserCheckable
            if not self.data(Qt.CheckStateRole).isValid():
                self.setData(Qt.Unchecked, Qt.CheckStateRole)
        else:
            self._flags = Qt.ItemFlags(self._flags & ~Qt.ItemIsUserCheckable)

    def isCheckable(self) -> bool:
        """Returns whether the item is checkable."""
        return self.data(Qt.ItemIsUserCheckable)

    def setCheckState(self, state: Qt.CheckState) -> None:
        """Sets the check state of the item."""
        self.setData(state, Qt.CheckStateRole)

    def checkState(self) -> Qt.CheckState:
        """Returns the check state of the item."""
        return self.data(Qt.CheckStateRole)

    def setFont(self, font: QFont) -> None:
        """Sets the font role data."""
        self.setData(font, Qt.FontRole)

    def font(self) -> QFont | None:
        """Returns the font role data."""
        return self.data(Qt.FontRole)

    def setBackground(self, brush: QBrush) -> None:
        """Sets the background role data."""
        self.setData(brush, Qt.BackgroundRole)

    def background(self) -> QBrush | None:
        """Returns the background role data."""
        return self.data(Qt.BackgroundRole)

    def setForeground(self, brush: QBrush) -> None:
        """Sets the foreground role data."""
        self.setData(brush, Qt.ForegroundRole)

    def foreground(self) -> QBrush | None:
        """Returns the foreground role data."""
        return self.data(Qt.ForegroundRole)

    def setEditable(self, editable: bool) -> None:  # noqa: FBT001
        """Sets whether the item is editable."""
        if editable:
            self._flags |= Qt.ItemIsEditable
        else:
            self._flags = Qt.ItemFlags(self._flags & ~Qt.ItemIsEditable)

    def isEditable(self) -> bool:
        """Returns whether the item is editable."""
        return bool(self._flags & Qt.ItemIsEditable)

    def setEnabled(self, enabled: bool) -> None:  # noqa: FBT001
        """Sets whether the item is enabled."""
        if enabled:
            self._flags |= Qt.ItemIsEnabled
        else:
            self._flags = Qt.ItemFlags(self._flags & ~Qt.ItemIsEnabled)

    def isEnabled(self) -> bool:
        """Returns whether the item is enabled."""
        return bool(self._flags & Qt.ItemIsEnabled)

    def setSelectable(self, selectable: bool) -> None:  # noqa: FBT001
        """Sets whether the item is selectable."""
        if selectable:
            self._flags |= Qt.ItemIsSelectable
        else:
            self._flags = Qt.ItemFlags(self._flags & ~Qt.ItemIsSelectable)

    def isSelectable(self) -> bool:
        """Returns whether the item is selectable."""
        return bool(self._flags & Qt.ItemIsSelectable)

    def setFlags(self, flags: Qt.ItemFlags) -> None:
        """Sets the item flags."""
        self._flags = flags

    def flags(self) -> Qt.ItemFlags | Qt.ItemFlag:
        """Returns the item flags."""
        return self._flags

    def model(self) -> QAbstractItemModel | None:
        """Returns the model associated with this item."""
        return self._model

    def setModel(self, model: QAbstractItemModel | None) -> None:
        """Sets the model associated with this item."""
        self._model = model
        for row in self._children:
            for child in row:
                if child is not None:
                    child.setModel(model)

    def index(self) -> QModelIndex:
        """Returns the QModelIndex corresponding to this item."""
        if self._model is None or self._parent is None:
            return QModelIndex()
        return self._model.index(self.row(), 0, self._parent.index())

    def isValid(self) -> bool:
        """Returns whether the item is associated with a model."""
        return self._model is not None

    def insertColumns(self, column: int, count: int) -> None:
        """Inserts columns into the item starting at the given column index.
        This will insert `count` columns into each child of this item.
        """
        for child in self._children:
            child.insertColumns(column, count)
        for _ in range(count):
            for child in self._children:
                child._children.insert(column, PyQStandardItem())  # noqa: SLF001

    def appendRows(self, items: Iterable[PyQStandardItem]) -> None:
        for item in items:
            self.appendRow(item)

    def appendColumn(self, items: Iterable[PyQStandardItem]) -> None:
        for i, item in enumerate(items):
            self.setChild(i, self.columnCount(), item)

    def removeColumn(self, column: int) -> None:
        for row in self._children:
            if row.child(column) is None:
                continue
            row.removeChild(column)

    def removeColumns(self, column: int, count: int) -> None:
        for _ in range(count):
            self.removeColumn(column)

    def takeRows(self, row: int, count: int) -> list[PyQStandardItem]:
        return [item for _ in range(count) for item in self.takeRow(row)]

    def takeColumn(self, column: int) -> list[PyQStandardItem]:
        return cast(
            "list[PyQStandardItem]",
            [
                row.takeChild(column)
                for row in self._children
                if row.child(column) is not None
            ]
        )

    def insertColumn(self, column: int, items: Iterable[PyQStandardItem]) -> None:
        for i, item in enumerate(items):
            self.setChild(i, column, item)

    @overload
    def setChild(self, row: int, column: int, item: PyQStandardItem) -> None: ...
    @overload
    def setChild(self, arow: int, aitem: PyQStandardItem) -> None: ...
    def setChild(self, *args: Any, **kwargs: Any) -> None:
        row: int = args[0] if len(args) > 0 and isinstance(args[0], int) else kwargs.get("row", kwargs["arow"])
        column: int = args[1] if len(args) > 1 and isinstance(args[1], int) else kwargs.get("column", 0)
        item: PyQStandardItem = args[2] if len(args) > 2 else kwargs.get("item", kwargs.get("aitem"))  # noqa: PLR2004
        if row < 0 or column < 0:
            return
        if row >= len(self._children):
            self.setRowCount(row + 1)
        self._children[row] = item
        item._parent = self
        self.emitDataChanged()

    def hasChildren(self) -> bool:
        return len(self._children) > 0

    def setRowCount(self, rows):
        currentRows = self.rowCount()
        if rows > currentRows:
            for _ in range(rows - currentRows):
                self.appendRow(PyQStandardItem())
        elif rows < currentRows:
            self.removeRows(rows, currentRows - rows)

    def rowCount(self) -> int:
        return len(self._children)

    def columnCount(self) -> int:
        """Returns the number of columns this item has.
        This is determined by the maximum number of columns any child has.
        """
        if not self._children:
            return 1  # Default to 1 column if there are no children

        # Determine the maximum column count among all children
        max_column_count = 1
        for child in self._children:
            child_column_count = len(child._children)  # noqa: SLF001
            max_column_count = max(child_column_count, max_column_count)

        return max_column_count

    def setTextAlignment(self, textAlignment: Qt.Alignment | Qt.AlignmentFlag) -> None:  # noqa: N803
        self.setData(textAlignment, Qt.ItemDataRole.TextAlignmentRole)

    def textAlignment(self) -> Qt.Alignment:
        return self.data(Qt.ItemDataRole.TextAlignmentRole)

    def setSizeHint(self, sizeHint: QSize) -> None:  # noqa: N803
        self.setData(sizeHint, Qt.ItemDataRole.SizeHintRole)

    def sizeHint(self) -> QSize:
        return self.data(Qt.ItemDataRole.SizeHintRole)

    def setWhatsThis(self, whatsThis: str) -> None:  # noqa: N803
        self.setData(whatsThis, Qt.ItemDataRole.WhatsThisRole)

    def whatsThis(self) -> str:
        return self.data(Qt.ItemDataRole.WhatsThisRole)

    def setStatusTip(self, statusTip: str) -> None:  # noqa: N803
        self.setData(statusTip, Qt.ItemDataRole.StatusTipRole)

    def statusTip(self) -> str:
        return self.data(Qt.ItemDataRole.StatusTipRole)

    def setToolTip(self, toolTip: str) -> None:  # noqa: N803
        self.setData(toolTip, Qt.ItemDataRole.ToolTipRole)

    def toolTip(self) -> str:
        return self.data(Qt.ItemDataRole.ToolTipRole)

    def accessibleDescription(self) -> str:
        return self.data(Qt.ItemDataRole.AccessibleDescriptionRole)

    def accessibleText(self) -> str:
        return self.data(Qt.ItemDataRole.AccessibleTextRole)

    def write(self, out: QDataStream) -> None:
        """Serializes the item data and writes it to the QDataStream."""
        out.writeInt32(len(self._data))
        for role, value in self._data.items():
            out.writeInt32(role)
            out.writeQVariant(value)
        out.writeInt32(int(self._flags))
        out.writeInt32(int(self._flags))

    def read(self, in_: QDataStream) -> None:
        """Deserializes the item data from the QDataStream."""
        self._data.clear()
        num_items = in_.readInt32()
        for _ in range(num_items):
            role = in_.readInt32()
            value = in_.readQVariant()
            self._data[role] = value
        self._flags = Qt.ItemFlags(in_.readInt32())

    def type(self) -> int:
        return self.Type

    def emitDataChanged(self) -> None:
        if self._model:
            self._model.dataChanged.emit(self.index(), self.index())
    def sortChildren(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder) -> None:
        self._children = sorted(
            [child for child in self._children if isinstance(child[0], PyQStandardItem)],
            key=lambda item: item[0].data(column),
            reverse=(order == Qt.DescendingOrder)
        )
        if self._model:
            self._model.layoutChanged.emit()

class PyQStandardItemModel(QAbstractItemModel):
    def __init__(
        self,
        rows: int = 0,
        columns: int = 1,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._rootItem: PyQStandardItem = PyQStandardItem()
        self._columnCount: int = columns
        self._horizontalHeaderItems: list[PyQStandardItem] = [PyQStandardItem() for _ in range(columns)]
        self._verticalHeaderItems: list[PyQStandardItem] = [PyQStandardItem() for _ in range(rows)]
        self._sortRole: int = Qt.ItemDataRole.DisplayRole

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        parent = QModelIndex() if parent is None else parent
        parentItem = self._getItem(parent)
        return parentItem.childCount()

    def columnCount(self, parent: QModelIndex | None = None) -> int:
        return self._columnCount

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return QVariant()
        item = self._getItem(index)
        return item.data(role)

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        if not index.isValid():
            return False
        item = self._getItem(index)
        item.setData(value, role)
        self.dataChanged.emit(index, index, [role])
        return True

    def flags(self, index: QModelIndex) -> Qt.ItemFlag | Qt.ItemFlags:
        if not index.isValid():
            return Qt.NoItemFlags
        return self._getItem(index).flags()

    def _getItem(self, index: QModelIndex) -> PyQStandardItem:
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item
        return self._rootItem

    def index(self, row: int, column: int, parent: QModelIndex | None = None) -> QModelIndex:
        parent = QModelIndex() if parent is None else parent
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        parentItem = self._getItem(parent)
        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        return QModelIndex()

    @overload
    def parent(self, child: QModelIndex) -> QModelIndex: ...
    @overload
    def parent(self) -> QModelIndex: ...
    def parent(self, *args: Any, **kwargs: Any) -> QModelIndex:
        child: QModelIndex = kwargs.get("child", args[0] if args else QModelIndex())
        if not child.isValid():
            return QModelIndex()
        childItem = self._getItem(child)
        parentItem = childItem._parent
        if parentItem == self._rootItem or not parentItem:
            return QModelIndex()
        return self.createIndex(parentItem.row(), 0, parentItem)

    @overload
    def insertRow(self, row: int, items: Iterable[PyQStandardItem]) -> None: ...
    @overload
    def insertRow(self, row: int, item: PyQStandardItem) -> None: ...
    @overload
    def insertRow(self, row: int, parent: QModelIndex | None = None) -> bool: ...
    def insertRow(
        self,
        row: int,
        *args: Any,
        items: Iterable[PyQStandardItem] | None = None,
        item: PyQStandardItem | None = None,
        parent: QModelIndex | None = None,
    ) -> bool | None:
        if isinstance(args[0], Iterable):
            assert parent is None
            items = args[0]
        elif isinstance(args[0], PyQStandardItem):
            assert parent is None
            items = [args[0]]
        else:
            parent = (args[0] if isinstance(args[0], QModelIndex) else QModelIndex()) if parent is None or not parent.isValid() else parent
            items = [PyQStandardItem()]
        item_parent_tuple: list[tuple[QModelIndex, PyQStandardItem]] = [(a.index().parent(), a) for a in items]
        self.beginInsertRows(
            QModelIndex() if parent is None or not parent.isValid() else parent,
            row,
            row + len(item_parent_tuple) - 1,
        )
        for i, (parent, item) in enumerate(item_parent_tuple):
            if not parent.isValid():
                super().insertRow(row + i, parent)
            else:
                parentItem = self._getItem(parent)
                parentItem.insertRow(row + i, item)
        self.endInsertRows()

    @overload
    def insertColumn(self, column: int, items: Iterable[PyQStandardItem]) -> None: ...
    @overload
    def insertColumn(self, column: int, parent: QModelIndex | None = None) -> bool: ...
    def insertColumn(self, column: int, *args: Any, **kwargs: Any) -> bool | None:
        items: Iterable[PyQStandardItem] | Any = kwargs.get("items", args[0])
        if isinstance(items, Iterable):
            parent = QModelIndex() if len(args) < 2 or args[1] is None else args[1]
            parentItem = self._getItem(parent)
            self.beginInsertColumns(parent, column, column)
            for item in items:
                parentItem.appendChild(item)
            self.endInsertColumns()
            return True
        parent: QModelIndex = kwargs.get("parent", QModelIndex() if args[0] is None else args[0])
        if isinstance(parent, QModelIndex) or parent is None:
            parentItem = self._getItem(parent)
            self.beginInsertColumns(parent, column, column)
            for child in parentItem._children:
                child.insertColumns(column, 1)
            self.endInsertColumns()
            return True
        return False

    def appendRow(self, *args: Any) -> None:
        if isinstance(args[0], Iterable):
            for item in args[0]:
                self.insertRow(self.rowCount(), item)
        else:
            self.insertRow(self.rowCount(), args[0])

    def appendColumn(self, *args: Any) -> None:
        if isinstance(args[0], Iterable):
            for item in args[0]:
                self.insertColumn(self.columnCount(), item)
        else:
            self.insertColumn(self.columnCount(), args[0])

    def clearItemData(self, index: QModelIndex) -> bool:
        if not index.isValid():
            return False
        item = self._getItem(index)
        item.clearData()
        self.dataChanged.emit(index, index, [])
        return True

    def setItemRoleNames(self, roleNames: dict[int, QByteArray | bytes | bytearray]) -> None:
        self._rootItem.setRoleNames(roleNames)

    def sibling(self, row: int, column: int, idx: QModelIndex) -> QModelIndex:
        if not idx.isValid():
            return QModelIndex()
        return self.index(row, column, self.parent(idx))

    def dropMimeData(self, data: QMimeData, action: Qt.DropAction, row: int, column: int, parent: QModelIndex | None = None) -> bool:
        if action == Qt.IgnoreAction:
            return False
        if not data.hasFormat("application/x-qabstractitemmodeldatalist"):
            return False

        encodedData = data.data("application/x-qabstractitemmodeldatalist")
        stream = QDataStream(encodedData, QIODevice.ReadOnly)
        newItems = []

        while not stream.atEnd():
            r = stream.readInt32()
            c = stream.readInt32()
            value = stream.readQString()
            newItem = PyQStandardItem()
            newItem.setData(value, Qt.ItemDataRole.DisplayRole)
            newItems.append(newItem)

        for i, item in enumerate(newItems):
            self.insertRow(row + i, item, parent)
        return True

    def mimeData(self, indexes: Iterable[QModelIndex]) -> QMimeData:
        mimeData = QMimeData()
        encodedData = QByteArray()
        stream = QDataStream(encodedData, QIODevice.WriteOnly)
        for index in indexes:
            if index.isValid():
                stream.writeInt32(index.row())
                stream.writeInt32(index.column())
                stream.writeString(self.data(index, Qt.ItemDataRole.DisplayRole))
        mimeData.setData("application/x-qabstractitemmodeldatalist", encodedData)
        return mimeData

    def mimeTypes(self) -> list[str]:
        return ["application/x-qabstractitemmodeldatalist"]

    def setSortRole(self, role: int) -> None:
        self._sortRole = role

    def sortRole(self) -> int:
        return self._sortRole

    def findItems(self, text: str, flags: Qt.MatchFlags | Qt.MatchFlag = Qt.MatchExactly, column: int = 0) -> list[PyQStandardItem]:
        matchedItems = []
        for i in range(self._rootItem.childCount()):
            item = self._rootItem.child(i)
            if item and item.data(Qt.ItemDataRole.DisplayRole) == text:
                matchedItems.append(item)
        return matchedItems

    def itemPrototype(self) -> PyQStandardItem:
        return PyQStandardItem()

    def setItemPrototype(self, item: PyQStandardItem) -> None:
        self._rootItem = item.clone()

    def takeVerticalHeaderItem(self, row: int) -> PyQStandardItem:
        return self._verticalHeaderItems.pop(row)

    def takeHorizontalHeaderItem(self, column: int) -> PyQStandardItem:
        return self._horizontalHeaderItems.pop(column)

    def takeColumn(self, column: int) -> list[PyQStandardItem]:
        removed_items = []
        for row in range(self._rootItem.childCount()):
            item = self._rootItem.child(row)
            assert item is not None, f"row {row} child item is None."
            removed_items.append(item.takeColumn(column))
        return removed_items

    def takeRow(self, row: int) -> list[PyQStandardItem]:
        return [self._rootItem.takeChild(row)]

    def takeItem(self, row: int, column: int = 0) -> PyQStandardItem:
        return self._rootItem.takeChild(row, column)

    def setRowCount(self, rows: int) -> None:
        currentRows = self.rowCount()
        if rows > currentRows:
            self.insertRows(currentRows, rows - currentRows)
        elif rows < currentRows:
            self.removeRows(rows, currentRows - rows)

    def setColumnCount(self, columns: int) -> None:
        self._columnCount = columns
        self.headerDataChanged.emit(Qt.Horizontal, 0, columns - 1)

    def setVerticalHeaderLabels(self, labels: Iterable[str]) -> None:
        for i, label in enumerate(labels):
            if i < self.rowCount():
                item = PyQStandardItem()
                item.setData(label, Qt.ItemDataRole.DisplayRole)
                self.setHorizontalHeaderItem(i, item)

    def setHorizontalHeaderLabels(self, labels: Iterable[str]) -> None:
        for i, label in enumerate(labels):
            if i < self.columnCount():
                item = PyQStandardItem()
                item.setData(label, Qt.ItemDataRole.DisplayRole)
                self.setHorizontalHeaderItem(i, item)

    def setVerticalHeaderItem(self, row: int, item: PyQStandardItem) -> None:
        if 0 <= row < self.rowCount():
            self._verticalHeaderItems[row] = item
            self.headerDataChanged.emit(Qt.Vertical, row, row)

    def verticalHeaderItem(self, row: int) -> PyQStandardItem:
        if 0 <= row < self.rowCount():
            return self._verticalHeaderItems[row]
        return PyQStandardItem()

    def setHorizontalHeaderItem(self, column: int, item: PyQStandardItem) -> None:
        if 0 <= column < self.columnCount():
            self._horizontalHeaderItems[column] = item
            self.headerDataChanged.emit(Qt.Horizontal, column, column)

    def horizontalHeaderItem(self, column: int) -> PyQStandardItem:
        if 0 <= column < self.columnCount():
            return self._horizontalHeaderItems[column]
        return PyQStandardItem()

    def invisibleRootItem(self) -> PyQStandardItem:
        return self._rootItem

    @overload
    def setItem(self, row: int, column: int, item: PyQStandardItem) -> None: ...
    @overload
    def setItem(self, row: int, item: PyQStandardItem) -> None: ...
    def setItem(self, *args: Any, **kwargs: Any) -> None:
        if len(args) == 3:
            row, column, item = args
            child = self._rootItem.child(row)
            assert child is not None
            child.setChild(column, item)
        elif len(args) == 2:
            row, item = args
            self._rootItem.setChild(row, item)

    def item(self, row: int, column: int = 0) -> PyQStandardItem:
        return self._rootItem.child(row, column)

    def indexFromItem(self, item: PyQStandardItem) -> QModelIndex:
        if item == self._rootItem:
            return QModelIndex()
        return self.createIndex(item.row(), item.column(), item)

    def itemFromIndex(self, index: QModelIndex) -> PyQStandardItem:
        return self._getItem(index)

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder) -> None:
        self.layoutAboutToBeChanged.emit()
        self._rootItem.sortChildren(column, order)
        self.layoutChanged.emit()

    def setItemData(self, index: QModelIndex, roles: Dict[int, Any]) -> bool:
        item = self._getItem(index)
        for role, value in roles.items():
            item.setData(value, role)
        self.dataChanged.emit(index, index, list(roles.keys()))
        return True

    def itemData(self, index: QModelIndex) -> Dict[int, Any]:
        return self._getItem(index).data()

    def supportedDropActions(self) -> Qt.DropActions:
        return Qt.CopyAction | Qt.MoveAction

    def clear(self) -> None:
        self.beginResetModel()
        self._rootItem.clearData()
        self.endResetModel()

    def removeColumns(self, column: int, count: int, parent: QModelIndex | None = None) -> bool:
        parent = QModelIndex() if parent is None else parent
        parentItem = self._getItem(parent)
        self.beginRemoveColumns(parent, column, column + count - 1)
        parentItem.removeColumns(column, count)
        self.endRemoveColumns()
        return True

    def removeRows(self, row: int, count: int, parent: QModelIndex | None = None) -> bool:
        parent = QModelIndex() if parent is None else parent
        parentItem = self._getItem(parent)
        self.beginRemoveRows(parent, row, row + count - 1)
        parentItem.removeRows(row, count)
        self.endRemoveRows()
        return True

    def insertColumns(self, column: int, count: int, parent: QModelIndex | None = None) -> bool:
        parent = QModelIndex() if parent is None else parent
        parentItem = self._getItem(parent)
        self.beginInsertColumns(parent, column, column + count - 1)
        for _ in range(count):
            parentItem.insertColumn(column, [PyQStandardItem()])
        self.endInsertColumns()
        return True

    def insertRows(self, row: int, count: int, parent: QModelIndex | None = None) -> bool:
        parent = QModelIndex() if parent is None else parent
        parentItem = self._getItem(parent)
        self.beginInsertRows(parent, row, row + count - 1)
        for _ in range(count):
            parentItem.insertRow(row, [PyQStandardItem()])
        self.endInsertRows()
        return True

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if role != Qt.ItemDataRole.DisplayRole:
            return QVariant()
        if orientation == Qt.Horizontal:
            return self._horizontalHeaderItems[section].data(role)
        if orientation == Qt.Vertical:
            return self._verticalHeaderItems[section].data(role)
        return QVariant()

    def setHeaderData(self, section: int, orientation: Qt.Orientation, value: Any, role: int = Qt.ItemDataRole.DisplayRole) -> bool:
        if role != Qt.ItemDataRole.DisplayRole:
            return False
        if orientation == Qt.Horizontal:
            self._horizontalHeaderItems[section].setData(value, role)
        elif orientation == Qt.Vertical:
            self._verticalHeaderItems[section].setData(value, role)
        self.headerDataChanged.emit(orientation, section, section)
        return True

    def hasChildren(self, parent: QModelIndex | None = None) -> bool:
        parent = QModelIndex() if parent is None else parent
        return self.rowCount(parent) > 0


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyQStandardItem Test Window")
        self.setGeometry(100, 100, 800, 600)

        # Main widget and layout
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # QTreeView setup
        self.tree_view: QTreeView = QTreeView(self)
        self.model: PyQStandardItemModel = PyQStandardItemModel(parent=self)
        self.tree_view.setModel(self.model)
        layout.addWidget(self.tree_view)

        # Buttons
        self.add_buttons(layout)

        # Context Menu
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)

    def add_buttons(self, layout: QHBoxLayout | QVBoxLayout):
        button_layout = QHBoxLayout()

        add_root_button = QPushButton("Add Root Item")
        add_root_button.clicked.connect(self.add_root_item)
        button_layout.addWidget(add_root_button)

        add_child_button = QPushButton("Add Child Item")
        add_child_button.clicked.connect(self.add_child_item)
        button_layout.addWidget(add_child_button)

        insert_above_button = QPushButton("Insert Item Above")
        insert_above_button.clicked.connect(self.insert_item_above)
        button_layout.addWidget(insert_above_button)

        insert_below_button = QPushButton("Insert Item Below")
        insert_below_button.clicked.connect(self.insert_item_below)
        button_layout.addWidget(insert_below_button)

        remove_item_button = QPushButton("Remove Item")
        remove_item_button.clicked.connect(self.remove_item)
        button_layout.addWidget(remove_item_button)

        set_text_button = QPushButton("Set Item Text")
        set_text_button.clicked.connect(self.set_item_text)
        button_layout.addWidget(set_text_button)

        set_icon_button = QPushButton("Set Item Icon")
        set_icon_button.clicked.connect(self.set_item_icon)
        button_layout.addWidget(set_icon_button)

        toggle_checkable_button = QPushButton("Toggle Item Checkable")
        toggle_checkable_button.clicked.connect(self.toggle_item_checkable)
        button_layout.addWidget(toggle_checkable_button)

        expand_all_button = QPushButton("Expand All")
        expand_all_button.clicked.connect(self.tree_view.expandAll)
        button_layout.addWidget(expand_all_button)

        collapse_all_button = QPushButton("Collapse All")
        collapse_all_button.clicked.connect(self.tree_view.collapseAll)
        button_layout.addWidget(collapse_all_button)

        layout.addLayout(button_layout)

    def add_root_item(self):
        item = PyQStandardItem("Root Item")
        self.model.appendRow(item)

    def add_child_item(self):
        index = self.tree_view.currentIndex()
        if index.isValid():
            parent_item = self.model.itemFromIndex(index)
            child_item = PyQStandardItem("Child Item")
            parent_item.appendChild(child_item)

    def insert_item_above(self):
        index = self.tree_view.currentIndex()
        if index.isValid():
            row = index.row()
            parent_index = self.model.parent(index)
            item = PyQStandardItem("Inserted Item Above")
            self.model.insertRow(row, item, parent_index)

    def insert_item_below(self):
        index = self.tree_view.currentIndex()
        if index.isValid():
            row = index.row() + 1
            parent_index = self.model.parent(index)
            item = PyQStandardItem("Inserted Item Below")
            self.model.insertRow(row, item, parent_index)

    def remove_item(self):
        index = self.tree_view.currentIndex()
        if index.isValid():
            self.model.removeRow(index.row(), self.model.parent(index))

    def set_item_text(self):
        index = self.tree_view.currentIndex()
        if index.isValid():
            item = self.model.itemFromIndex(index)
            new_text, ok = QInputDialog.getText(self, "Set Item Text", "Enter new text:")
            if ok and new_text:
                item.setText(new_text)

    def set_item_icon(self):
        index = self.tree_view.currentIndex()
        if index.isValid():
            item = self.model.itemFromIndex(index)
            icon = QIcon("path/to/icon.png")  # Replace with actual icon path
            item.setIcon(icon)

    def toggle_item_checkable(self):
        index = self.tree_view.currentIndex()
        if index.isValid():
            item = self.model.itemFromIndex(index)
            item.setCheckable(not item.isCheckable())

    def show_context_menu(self, position):
        menu = QMenu(self.tree_view)

        add_child_action = QAction("Add Child", self)
        add_child_action.triggered.connect(self.add_child_item)
        menu.addAction(add_child_action)

        insert_above_action = QAction("Insert Item Above", self)
        insert_above_action.triggered.connect(self.insert_item_above)
        menu.addAction(insert_above_action)

        insert_below_action = QAction("Insert Item Below", self)
        insert_below_action.triggered.connect(self.insert_item_below)
        menu.addAction(insert_below_action)

        remove_item_action = QAction("Remove Item", self)
        remove_item_action.triggered.connect(self.remove_item)
        menu.addAction(remove_item_action)

        print_details_action = QAction("Print Item Details", self)
        print_details_action.triggered.connect(self.print_item_details)
        menu.addAction(print_details_action)

        set_custom_role_action = QAction("Set Custom Role Data", self)
        set_custom_role_action.triggered.connect(self.set_custom_role_data)
        menu.addAction(set_custom_role_action)

        clone_item_action = QAction("Clone Item", self)
        clone_item_action.triggered.connect(self.clone_item)
        menu.addAction(clone_item_action)

        # Disable Add Child if no item is selected
        index = self.tree_view.currentIndex()
        if not index.isValid():
            add_child_action.setEnabled(False)

        menu.exec(self.tree_view.viewport().mapToGlobal(position))

    def print_item_details(self):
        index = self.tree_view.currentIndex()
        if index.isValid():
            item = self.model.itemFromIndex(index)
            print(f"Item Details: {item}")

    def set_custom_role_data(self):
        index = self.tree_view.currentIndex()
        if index.isValid():
            item = self.model.itemFromIndex(index)
            role, ok = QInputDialog.getInt(self, "Set Custom Role", "Enter role number (256+):")
            if ok:
                value, ok = QInputDialog.getText(self, "Set Custom Role Data", "Enter value:")
                if ok:
                    item.setData(value, role)

    def clone_item(self):
        index = self.tree_view.currentIndex()
        if index.isValid():
            item = self.model.itemFromIndex(index)
            cloned_item = item.clone()
            parent_index = self.model.parent(index)
            self.model.insertRow(index.row() + 1, cloned_item, parent_index)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())
