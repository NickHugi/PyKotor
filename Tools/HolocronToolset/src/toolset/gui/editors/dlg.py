from __future__ import annotations

import json
import re
import tempfile

from collections import deque
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Iterable, cast, overload

import qtpy

from qtpy import QtMultimedia
from qtpy.QtCore import (
    QBuffer,
    QByteArray,
    QDataStream,
    QEvent,
    QIODevice,
    QItemSelection,
    QItemSelectionModel,
    QMimeData,
    QModelIndex,
    QPoint,
    QRect,
    QRectF,
    QSize,
    QSortFilterProxyModel,
    QStringListModel,
    QTimer,
    QUrl,
    Qt,
)
from qtpy.QtGui import (
    QBrush,
    QColor,
    QDrag,
    QFont,
    QFontMetrics,
    QHoverEvent,
    QIcon,
    QKeySequence,
    QPainter,
    QPalette,
    QPen,
    QPixmap,
    QRadialGradient,
    QStandardItem,
    QStandardItemModel,
    QTextDocument,
)
from qtpy.QtMultimedia import QMediaPlayer
from qtpy.QtWidgets import (
    QAbstractItemView,
    QAction,
    QApplication,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QListWidgetItem,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QStyle,
    QStyleOptionViewItem,
    QStyledItemDelegate,
    QToolTip,
    QTreeView,
    QUndoCommand,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from pykotor.common.misc import ResRef
from pykotor.extract.installation import SearchLocation
from pykotor.resource.generics.dlg import (
    DLG,
    DLGComputerType,
    DLGConversationType,
    DLGEntry,
    DLGLink,
    DLGNode,
    DLGReply,
    read_dlg,
    write_dlg,
)
from pykotor.resource.type import ResourceType
from toolset.data.installation import HTInstallation
from toolset.gui.dialogs.edit.dialog_animation import EditAnimationDialog
from toolset.gui.dialogs.edit.dialog_model import CutsceneModelDialog
from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog
from toolset.gui.dialogs.load_from_location_result import FileSelectionWindow, ResourceItems
from toolset.gui.editor import Editor
from toolset.gui.widgets.settings.installations import GlobalSettings
from toolset.utils.misc import QtKey, getQtKeyString
from toolset.utils.window import addWindow
from utility.logger_util import RobustRootLogger
from utility.system.os_helper import remove_any

if TYPE_CHECKING:
    import os

    from qtpy.QtCore import (
        QObject,
        QTemporaryFile,
    )
    from qtpy.QtGui import (
        QDragEnterEvent,
        QDragMoveEvent,
        QDropEvent,
        QFocusEvent,
        QKeyEvent,
        QMouseEvent,
        QPaintEvent,
        QResizeEvent,
        QWheelEvent,
    )
    from qtpy.QtWidgets import (
        QTextEdit,
    )
    from typing_extensions import Self

    from pykotor.common.language import LocalizedString
    from pykotor.extract.file import LocationResult, ResourceIdentifier
    from pykotor.resource.formats.twoda.twoda_data import TwoDA
    from pykotor.resource.generics.dlg import (
        DLGAnimation,
        DLGStunt,
    )
    from utility.system.path import PureWindowsPath

_FUTURE_EXPAND_ROLE = Qt.ItemDataRole.UserRole + 3

class TrieNode:
    """A node in the trie structure."""
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False

class Trie:
    """The trie object containing the whole data structure."""
    def __init__(self):
        self.root = TrieNode()

    def insert(self, text: str):
        node = self.root
        for char in text:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True  # This marks the end of a word

    def search(self, prefix: str) -> bool:
        node = self.root
        for char in prefix:
            if char not in node.children:
                return False
            node = node.children[char]
        return True  # The prefix is valid if we successfully traverse the Trie

    def rebuild(self, data_list):
        self.root = TrieNode()  # Reset the Trie
        for data in data_list:
            self.insert(data)

class FilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self.filter_text: str = ""
        self.filter_timer: QTimer = QTimer()
        self.filter_timer.setSingleShot(True)
        self.filter_timer.timeout.connect(self.invalidateFilter)
        self.debounce_delay = 300  # Milliseconds

    def setFilterText(self, text: str):
        self.filter_text = text.lower()
        if not self.filter_text:  # If filter text is empty, reset immediately
            self.invalidateFilter()
        else:
            self.filter_timer.stop()
            self.filter_timer.start(self.debounce_delay)  # Restart the timer on each input

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if source_row == 0:
            return True
        index = self.sourceModel().index(source_row, 0, source_parent)
        item_text = index.data(Qt.DisplayRole)
        return False if item_text is None else self.filter_text in item_text.lower()

    def rebuildTrie(self):
        # Ensure there is a source model before trying to rebuild the Trie
        if self.sourceModel() is not None:
            self.trie.rebuild(
                [
                    self.sourceModel().data(self.sourceModel().index(row, 0), Qt.DisplayRole).lower()
                    for row in range(1, self.sourceModel().rowCount())  # Start from 1 to skip placeholder
                ]
            )


class ButtonDelegate(QStyledItemDelegate):
    def __init__(self, button_text: str, button_callback: Callable[[int], Any], parent: QObject | None = None):
        super().__init__(parent)
        self.button_text: str = button_text
        self.button_callback: Callable[[int], Any] = button_callback
        self.buttons: dict[int, QPushButton] = {}

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        super().paint(painter, option, index)
        if index.row() not in self.buttons:
            button = QPushButton(self.button_text, parent=option.widget)
            button.clicked.connect(lambda _checked, idx=index: self.button_callback(self.get_item_text(idx)))
            self.buttons[index.row()] = button

        button = self.buttons[index.row()]
        fm = QFontMetrics(button.font())
        button_width = fm.width(self.button_text) + 10  # Adjust padding as necessary
        button_height = fm.height() + 10
        button_size = QSize(button_width, button_height)
        button.move(option.rect.right() - button_size.width(), option.rect.top())
        button.resize(button_size)
        button.show()

    def get_item_text(self, index: QModelIndex) -> str:
        return index.model().data(index, Qt.DisplayRole) if index.isValid() else ""

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        fm = QFontMetrics(option.font)
        text_width = fm.width(index.model().data(index, Qt.DisplayRole))  # Get text width
        text_height = fm.height()  # Get text height
        button_width = fm.width(self.button_text) + 10  # Include padding for the button
        # Calculate total width and set height based on the taller element (text or button)
        total_width = text_width + button_width + 5  # Additional padding between text and button
        button_height = fm.height()+10
        return QSize(total_width, max(text_height, button_height))

    def handleButtonClick(self, row):
        print(f"Button clicked for row {row}")
        # Handle the button click action here

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class FilterComboBox(QComboBox):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setEditable(True)
        self.original_model: QStringListModel = QStringListModel(self)
        self.items: list[str] = [""]
        self.proxy_model: FilterProxyModel = FilterProxyModel(self)

        self.setView(QListView(self))
        self.proxy_model.setSourceModel(self.original_model)
        self.setModel(self.proxy_model)
        self.original_model.setStringList(self.items)
        self.create_line_edit()

    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        # Ensure that the line edit is always focused when the widget is active
        if event.type() == QEvent.FocusIn and source is not self.line_edit:
            self.line_edit.setFocus()
            return True
        return super().eventFilter(source, event)

    def create_line_edit(self):
        self.line_edit = QLineEdit(self)
        self.line_edit.setPlaceholderText("Type to filter...")
        self.line_edit.setClearButtonEnabled(True)
        self.line_edit.textChanged.connect(self.filter_items)
        self.line_edit.hide()
        self.line_edit.setFocusPolicy(Qt.StrongFocus)
        self.line_edit.installEventFilter(self)  # Install event filter

    def showPopup(self):
        super().showPopup()
        try:
            self.view().setIndexWidget(self.proxy_model.index(0, 0), self.line_edit)
        except RuntimeError:  # wrapped C/C++ object of type QLineEdit has been deleted
            self.create_line_edit()
            self.view().setIndexWidget(self.proxy_model.index(0, 0), self.line_edit)
        self.line_edit.show()
        self.line_edit.setFocus()
        # Start with the current width of the ComboBox
        max_width = self.width()

        # Delegate for calculating sizeHint
        delegate = self.itemDelegate()

        # Get the maximum width of the first 20 items, or fewer if there are fewer items
        max_items_to_measure = 20
        num_items = min(self.model().rowCount(), max_items_to_measure)

        # Loop through the items to determine the maximum width
        for i in range(num_items):
            index = self.model().index(i, 0)
            option = QStyleOptionViewItem()
            # Get size hint from the delegate
            item_size = delegate.sizeHint(option, index)
            item_width = item_size.width()

            # Update the maximum width if the current item is wider
            if item_width > max_width:
                max_width = item_width

        # Set the width of the dropdown list
        self.view().setFixedWidth(max_width+25)
        super().showPopup()

    def populate_items(self, items):
        # Start from index 1 to leave the placeholder intact
        self.items = ["", *items]
        self.original_model.setStringList(self.items)

    def filter_items(self, text):
        self.proxy_model.setFilterText(text)
        self.proxy_model.invalidateFilter()

    def set_button_delegate(self, button_text: str, button_callback: Callable[[int], Any]):
        button_delegate = ButtonDelegate(button_text, button_callback, self.view())
        self.view().setItemDelegate(button_delegate)


class GFFFieldSpinBox(QSpinBox):
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        self._no_validate: bool = False
        super().__init__(*args, **kwargs)
        self.specialValueTextMapping: dict[int, str] = {0: "0", -1: "-1"}
        self.setSpecialValueText(self.specialValueTextMapping[-1])

    @property
    def min_value(self) -> int:
        return min(self.minimum(), *self.specialValueTextMapping.keys())

    @min_value.setter
    def min_value(self, value: int): ...

    @property
    def max_value(self) -> int:
        return max(self.maximum(), *self.specialValueTextMapping.keys())

    @max_value.setter
    def max_value(self, value: int): ...

    def fixup(self, text: str):
        if text.isdigit() or (text and text[0] == "-" and text[1:].isdigit()):
            value = int(text)
            if value < self.min_value:
                self.setValue(self.min_value)
            elif value > self.max_value:
                self.setValue(self.max_value)
        else:
            self.setValue(self.value())

    def stepBy(self, steps: int):
        current_value = self.value()
        if current_value in self.specialValueTextMapping and steps > 0:
            self.setValue(self.min_value)
        elif current_value == self.min_value and steps < 0:
            self.setValue(max(self.specialValueTextMapping.keys()))
        else:
            next_value = current_value + steps
            if self.min_value <= next_value <= self.max_value:
                super().stepBy(steps)
            elif next_value < self.min_value:
                self.setValue(-1)
            else:
                self.setValue(self.max_value)

    @classmethod
    def from_spinbox(
        cls,
        originalSpin: QSpinBox,
        min_value: int = 0,
        max_value: int = 100,
    ) -> GFFFieldSpinBox:
        """Is not perfect at realigning, but attempts to initialize a GFFFieldSpinBox from a pre-existing QSpinBox."""
        if not isinstance(originalSpin, QSpinBox):
            raise TypeError("The provided widget is not a QSpinBox.")

        layout = originalSpin.parentWidget().layout()
        row, role = None, None

        if isinstance(layout, QFormLayout):
            for r in range(layout.rowCount()):
                if layout.itemAt(r, QFormLayout.ItemRole.FieldRole) and layout.itemAt(r, QFormLayout.ItemRole.FieldRole).widget() == originalSpin:
                    row, role = r, QFormLayout.ItemRole.FieldRole

                    break
                if layout.itemAt(r, QFormLayout.ItemRole.LabelRole) and layout.itemAt(r, QFormLayout.ItemRole.LabelRole).widget() == originalSpin:
                    row, role = r, QFormLayout.ItemRole.LabelRole

                    break

        parent = originalSpin.parent()
        customSpin = cls(parent, min_value=min_value, max_value=max_value)

        for i in range(originalSpin.metaObject().propertyCount()):
            prop = originalSpin.metaObject().property(i)

            if prop.isReadable() and prop.isWritable():
                value = originalSpin.property(prop.name())
                customSpin.setProperty(prop.name(), value)

        if row is not None and role is not None:
            layout.setWidget(row, role, customSpin)

        originalSpin.deleteLater()

        return customSpin


class HTMLDelegate(QStyledItemDelegate):
    def __init__(self, parent: DLGTreeView | None = None):
        super().__init__(parent)
        self.dlgTreeView: DLGTreeView = parent
        self.text_size: int = 12
        self.max_height_percentage: float = 1.0  # 100%
        self.max_width_percentage: float = 1.0  # 100%
        self.verticalSpacing: int = 0  # Default vertical spacing between items
        self.nudgedModelIndexes: dict[QModelIndex, tuple[int, int]] = {}

    def setVerticalSpacing(self, spacing: int):
        print(f"<SDM> [setVerticalSpacing scope] set vertical spacing from {self.verticalSpacing} to {spacing}")
        self.verticalSpacing = spacing
        self.dlgTreeView.model().layoutChanged.emit()

    def setTextSize(self, size: int):
        print(f"<SDM> [setTextSize scope] set text size from {self.text_size} to {size}")
        self.text_size = size
        self.dlgTreeView.model().layoutChanged.emit()

    def nudgeItem(
        self,
        index: QModelIndex,
        x: int,
        y: int,
    ):
        """Manually set the nudge offset for an item."""
        self.nudgedModelIndexes[index] = (x, y)
        print("<SDM> [nudgeItem scope] self.nudgedModelIndexes[index]: ", self.nudgedModelIndexes[index])

    def updateHtmlSizeAndSpacing(self, html: str, size: int) -> str:
        #print("<SDM> [updateHtmlWithNewTextSize scope] original html: ", html)
        updatedHtml: str = re.sub(r"font-size:\d+pt;", f"font-size:{size}pt;", html)
        #print("<SDM> [updateHtmlWithNewTextSize scope] updated_html: ", updatedHtml)
        return updatedHtml

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ):
        #print(f"HTMLDelegate.paint({painter}, {option}, {index})")
        painter.save()

        # Apply any nudge offsets
        nudge_offset: tuple[int, int] = self.nudgedModelIndexes.get(index, (0, 0))
        painter.translate(nudge_offset[0], nudge_offset[1])

        doc = QTextDocument()
        display_data: str | None = index.data(Qt.DisplayRole)
        if display_data is None:
            painter.restore()
            return
        doc.setHtml(self.updateHtmlSizeAndSpacing(display_data, self.text_size))
        doc.setDefaultFont(option.font)  # Ensure the document uses the correct font settings

        ctx = QTextDocument().documentLayout().PaintContext()
        ctx.palette = option.palette

        # Handling selection highlighting
        if option.state & QStyle.State_Selected:
            highlight_color = option.palette.highlight().color()
            highlight_color.setAlpha(int(highlight_color.alpha() * 0.7))
            painter.fillRect(option.rect, highlight_color)
            ctx.palette.setColor(QPalette.Text, option.palette.highlightedText().color())
        else:
            ctx.palette.setColor(QPalette.Text, option.palette.text().color())

        # Draw the text in the adjusted rectangle
        ctx_rect = QRectF(option.rect)
        doc.setTextWidth(ctx_rect.width())  # Ensure the width matches the column width
        topleft = ctx_rect.topLeft()
        centerleft = QPoint(int(topleft.x()), int(topleft.y() + self.verticalSpacing))
        painter.translate(centerleft)  # Translate to start drawing at the top left of the rectangle
        doc.documentLayout().draw(painter, ctx)

        painter.restore()  # Restore the painter to its original state

    def sizeHint(
        self,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> QSize:
        option.textElideMode = Qt.ElideNone  # Disable text elision
        #print(f"HTMLDelegate.sizeHint({option}, {index})")
        if self.dlgTreeView:
            window_width = self.dlgTreeView.viewport().width()
            max_width = self.max_width_percentage * window_width
        else:
            max_width = 100  # Fallback width if dlgTreeView is not available

        html: str | None = index.data(Qt.DisplayRole)
        if html is None:
            return super().sizeHint(option, index)
        updated_html = self.updateHtmlSizeAndSpacing(html, self.text_size)

        doc = QTextDocument()
        doc.setHtml(updated_html)
        doc.setTextWidth(max_width)  # Set the text width to force wrapping at the specified width

        required_height = doc.size().height()

        # Include vertical spacing explicitly since QTextDocument may not account for margins
        vertical_padding = self.verticalSpacing * 2  # Since margin is added to both top and bottom
        total_required_height = required_height + vertical_padding

        if self.dlgTreeView:
            max_height = self.max_height_percentage * self.dlgTreeView.viewport().height()
        else:
            max_height = 200  # Fallback maximum height

        final_adjusted_height = min(total_required_height, max_height)

        return QSize(int(max_width), int(final_adjusted_height))


class RobustTreeView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.text_size: int = 12

        self.setUniformRowHeights(False)
        self.setMouseTracking(False)  # Disable hover events
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerItem)

    def itemDelegate(self, *args) -> HTMLDelegate:
        delegate = super().itemDelegate(*args)
        assert isinstance(delegate, HTMLDelegate)
        return delegate

    def setItemDelegate(self, delegate: HTMLDelegate):
        assert isinstance(delegate, HTMLDelegate)
        super().setItemDelegate(delegate)

    def calculateIndentWidth(self) -> int:
        for row in range(self.model().rowCount()):
            index = self.model().index(row, 0)
            if index.isValid():
                rect = self.visualRect(index)
                if rect.left() > 0:
                    return rect.left()
        return self.indentation()

    def wheelEvent(
        self,
        event: QWheelEvent,
    ) -> None:
        modifiers = event.modifiers()
        response = None
        if modifiers & Qt.ControlModifier:
            response = self._wheel_changes_text_size(event)
        if modifiers & Qt.ShiftModifier:
            response = self._wheel_changes_item_spacing(event)
        if response is not True:
            super().wheelEvent(event)

    def drawBranches(
        self,
        painter: QPainter,
        rect: QRect,
        index: QModelIndex,
    ):
        if self.itemDelegate():
            item_size = self.itemDelegate().sizeHint(QStyleOptionViewItem(), index)
            center_y = (
                rect.top()
                + (rect.height() - item_size.height()) // 2
                + item_size.height() / 2
                - rect.height() / 2
            )
            rect.moveTop(int(center_y))
        super().drawBranches(painter, rect, index)

    def _wheel_changes_text_size(self, event: QWheelEvent) -> bool:
        delta: int = event.angleDelta().y()
        if not delta:
            return False
        self.text_size = max(1, self.text_size + (1 if delta > 0 else -1))
        if self.itemDelegate() is not None:
            self.itemDelegate().setTextSize(self.text_size)
            self.viewport().update()
            return True
        return False

    def _wheel_changes_item_spacing(self, event: QWheelEvent) -> bool:
        delta: int = event.angleDelta().y()
        if not delta:
            return False
        if self.itemDelegate() is not None:
            new_spacing: int = max(0, self.itemDelegate().verticalSpacing + (1 if delta > 0 else -1))
            self.itemDelegate().setVerticalSpacing(new_spacing)
            self.viewport().update()
            return True
        return False

    def getItemDepth(self, index: QModelIndex) -> int:
        depth = 0
        while index.parent().isValid():
            index = index.parent()
            depth += 1
        return depth

    def getIdentifyingText(self, indexOrItem: QModelIndex | QStandardItem) -> str:
        if indexOrItem is None:
            return "(None)"
        if isinstance(indexOrItem, QStandardItem):
            try:
                indexOrItem = indexOrItem.index()
            except RuntimeError as e: # wrapped C/C++ object of type x has been deleted
                return str(e)
        if not isinstance(indexOrItem, QModelIndex):
            return f"(Unknown index/item: {indexOrItem})"
        if not indexOrItem.isValid():
            return f"(invalid index at row '{indexOrItem.row()}', column '{indexOrItem.column()}')"

        item = self.model().itemFromIndex(indexOrItem)
        if item is None:
            return f"(no item associated with index at row '{indexOrItem.row()}', column '{indexOrItem.column()}')"

        text = item.text().strip()
        parent_count = 0
        current_index = indexOrItem.parent()
        while current_index.isValid():
            parent_count += 1
            current_index = current_index.parent()

        return f"Item/Index at Row: {indexOrItem.row()}, Column: {indexOrItem.column()}, Ancestors: {parent_count}\nText for above item: {text}\n"


class InsertCommand(QUndoCommand):
    def __init__(
        self,
        model: DLGStandardItemModel,
        parent: DLGLink | None,
        links: list[DLGLink],
        text: str = "Insert",
    ):
        super().__init__(text)
        self.model: DLGStandardItemModel = model
        self.parent: DLGLink | None = parent
        self.links: list[DLGLink] = links

    def redo(self) -> None:
        self.model._insertLinkToParent(self.parent, self.links, 0)

    def undo(self) -> None:
        for link in self.links:
            self.model._removeLinkFromParent(self.parent, link)


class MoveCommand(QUndoCommand):
    def __init__(
        self,
        model: DLGStandardItemModel,
        link: DLGLink,
        new_parent: DLGLink | None,
        old_parent: DLGLink | None,
        text: str = "Move",
    ):
        super().__init__(text)
        self.model: DLGStandardItemModel = model
        self.link: DLGLink = link
        self.new_parent: DLGLink | None = new_parent
        self.old_parent: DLGLink | None = old_parent

    def redo(self) -> None:
        if self.old_parent:
            self.model._removeLinkFromParent(self.old_parent, self.link)
        if self.new_parent:
            self.model._insertLinkToParent(self.new_parent, [self.link], 0)

    def undo(self) -> None:
        if self.new_parent:
            self.model._removeLinkFromParent(self.new_parent, self.link)
        if self.old_parent:
            self.model._insertLinkToParent(self.old_parent, [self.link], 0)


class RemoveCommand(QUndoCommand):
    def __init__(
        self,
        model: DLGStandardItemModel,
        parent: DLGLink | None,
        links: list[DLGLink],
        text: str = "Remove",
    ):
        super().__init__(text)
        self.model: DLGStandardItemModel = model
        self.parent: DLGLink | None = parent
        self.links: list[DLGLink] = links

    def redo(self) -> None:
        for link in self.links:
            self.model._removeLinkFromParent(self.parent, link)

    def undo(self) -> None:
        self.model._insertLinkToParent(self.parent, self.links, 0)


class DLGStandardItem(QStandardItem):
    def __init__(self, *args, link: DLGLink, **kwargs):
        super().__init__(*args, **kwargs)
        self.link: DLGLink = link

    def parent(self) -> Self | DLGStandardItemModel | None:
        return super().parent()

    def __eq__(self, other):
        if not isinstance(other, DLGStandardItem):
            return NotImplemented
        return id(self) == id(other)

    def __hash__(self) -> int:
        return id(self)

    def model(self) -> DLGStandardItemModel:
        model = super().model()
        if model is None:
            return None
        assert isinstance(model, DLGStandardItemModel), f"model was {model} of type {model.__class__.__name__}"
        return model

    def appendRow(self, item: DLGStandardItem | QStandardItem | Iterable[DLGStandardItem | QStandardItem]) -> None:
        if isinstance(item, Iterable):
            item = item[0]  # multiple columns are not supported (yet)
        assert isinstance(item, DLGStandardItem) or item.data(_FUTURE_EXPAND_ROLE)
        super().appendRow(item)
        if isinstance(item, DLGStandardItem) and self.model() and not self.model().signalsBlocked():
            self.model()._addLinkToParent(self, item)  # noqa: SLF001

    def appendRows(self, items: Iterable[DLGStandardItem]) -> None:
        for item in items:
            self.appendRow(item)

    def insertRow(self, row: int, item: DLGStandardItem | QStandardItem | Iterable) -> None:
        if isinstance(item, Iterable):
            item = item[0]  # multiple columns are not supported (yet)
        assert isinstance(item, DLGStandardItem) or item.data(_FUTURE_EXPAND_ROLE)
        super().insertRow(row, item)
        if isinstance(item, DLGStandardItem) and self.model() and not self.model().signalsBlocked():
            self.model()._insertLinkToParent(self, item, row)  # noqa: SLF001

    def insertRows(self, row: int, items: Iterable[Self]) -> None:
        for i, item in enumerate(items):
            self.insertRow(row + i, item)

    def removeRow(self, row: int) -> None:
        self.takeRow(row)[0]

    def removeRows(self, row: int, count: int) -> None:
        for _ in range(count):
            self.removeRow(row)

    def setChild(self, row: int, column: int, item: Self | QStandardItem) -> None:
        assert isinstance(item, DLGStandardItem) or item.data(_FUTURE_EXPAND_ROLE)
        super().setChild(row, column, item)
        if isinstance(item, DLGStandardItem) and self.model() and not self.model().signalsBlocked():
            self.model()._addLinkToParent(self, item, row)  # noqa: SLF001

    def takeChild(self, row: int, column: int = 0) -> Self:
        item = super().takeChild(row, column)
        assert isinstance(item, DLGStandardItem) or item.data(_FUTURE_EXPAND_ROLE)
        if isinstance(item, DLGStandardItem) and self.model() and not self.model().signalsBlocked():
            self.model()._removeLinkFromParent(self, item)  # noqa: SLF001
        return item

    def takeRow(self, row: int) -> list[Self | QStandardItem]:
        items = super().takeRow(row)
        if items and isinstance(items[0], DLGStandardItem) and self.model() and not self.model().signalsBlocked():
            for item in items:
                self.model()._removeLinkFromParent(self, item)  # noqa: SLF001
        return items

    def takeColumn(self, column: int) -> list[Self | QStandardItem]:
        raise NotImplementedError("takeColumn is not supported in this model.")
        #items = super().takeColumn(column)
        #if self.model() and not self.model().signalsBlocked():
        #    for item in items:
        #        self.model()._removeLinkFromParent(self, item)
        #return items

    def setData(self, value: Any, role: int = Qt.UserRole + 1) -> None:
        super().setData(value, role)
        if self.model():
            self.model().itemChanged.emit(self)

    def clearData(self) -> None:
        super().clearData()
        if self.model():
            self.model().itemChanged.emit(self)

    def emitDataChanged(self) -> None:
        if self.model() is None:
            super().emitDataChanged()
            return
        self.model().dataChanged.emit(self.index(), self.index())


class DLGStandardItemModel(QStandardItemModel):
    def __init__(self, parent: DLGTreeView):
        assert isinstance(parent, DLGTreeView)
        self.editor: DLGEditor | None = None
        self.treeView: DLGTreeView = parent
        self.linkToItems: dict[DLGLink, list[DLGStandardItem]] = {}
        self.nodeToItems: dict[DLGNode, list[DLGStandardItem]] = {}
        super().__init__(self.treeView)
        self.modelReset.connect(self.onModelReset)

    def createIndex(self, row, column, data=None):
        index = super().createIndex(row, column, data)
        assert index.isValid(), f"Invalid index created: row={row}, column={column}, data={data}"
        return index

    def insertRows(self, row: int, count: int, parent: QModelIndex | None = None) -> bool:
        if parent is None:
            parent = QModelIndex()
        self.beginInsertRows(parent, row, row + count - 1)
        result = super().insertRows(row, count, parent)
        self.endInsertRows()
        return result

    def removeRows(self, row: int, count: int, parent: QModelIndex | None = None) -> bool:
        self.beginRemoveRows(QModelIndex() if parent is None else parent, row, row + count - 1)
        if parent is not None:
            items = [self.itemFromIndex(self.index(r, 0, parent)) for r in range(row, row + count)]
        else:
            items = [self.itemFromIndex(self.index(r, 0)) for r in range(row, row + count)]
        result = super().removeRows(row, count, parent)
        self.endRemoveRows()
        if not self.signalsBlocked():
            for item in items:
                if item:
                    self._removeLinkFromParent(self if parent is None else self.itemFromIndex(parent), item)
        return result

    def removeRow(self, row: int, parent: QModelIndex | None = None) -> bool:
        self.beginRemoveRows(QModelIndex() if parent is None else parent, row, row)
        if parent is not None:
            result = super().removeRow(row, parent)  # internally will call self.removeRows
        else:
            result = super().removeRow(row)  # internally will call self.removeRows
        self.endRemoveRows()
        return result

    @overload
    def insertRow(self, row: int, items: Iterable[QStandardItem]) -> None: ...

    @overload
    def insertRow(self, arow: int, aitem: QStandardItem) -> None: ...

    @overload
    def insertRow(self, row: int, parent: QModelIndex = ...) -> bool: ...

    def insertRow(
        self,
        row: int,
        second_arg: Iterable[QStandardItem] | QStandardItem | QModelIndex,
    ) -> bool | None:
        if isinstance(second_arg, QModelIndex):
            result = super().insertRow(row, second_arg)
            if not self.signalsBlocked():
                parent_item = self.itemFromIndex(second_arg)
                self._insertLinkToParent(self, parent_item, row)
        elif isinstance(second_arg, (Iterable, QStandardItem)):
            result = super().insertRow(row, second_arg)
            if not self.signalsBlocked():
                self._insertLinkToParent(self, second_arg, row)
        else:
            raise TypeError("Incorrect args passed to insertRow")
        return result

    def takeItem(self, row: int, column: int) -> QStandardItem:
        item = super().takeItem(row, column)
        if not self.signalsBlocked():
            self._removeLinkFromParent(self, item)
        return item

    def takeRow(self, row: int) -> list[QStandardItem]:
        items = super().takeRow(row)
        if items and not self.signalsBlocked():
            for item in items:
                if item:
                    self._removeLinkFromParent(self, item)
                    #self._updateCopies(item.link)
        return items

    @overload
    def appendRow(self, items: Iterable[QStandardItem]) -> None: ...

    @overload
    def appendRow(self, aitem: QStandardItem) -> None: ...

    def appendRow(self, *args) -> None:
        super().appendRow(args[0])

    def appendRows(self, items: Iterable[DLGStandardItem], parent: QModelIndex | None = None) -> None:
        for item in items:
            self.appendRow(item, parent)

    def _addLinkToParent(self, parent: DLGStandardItem, item: DLGStandardItem) -> None:
        link = item.link
        node = parent.link.node
        node.links.append(link)
        link.list_index = len(node.links) - 1
        self.linkToItems.setdefault(link, []).append(item)
        self.nodeToItems.setdefault(node, []).append(item)

    def _insertLinkToParent(
        self,
        parent: DLGStandardItem | DLGStandardItemModel,
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
        parent: DLGStandardItem | DLGStandardItemModel,
        item: DLGStandardItem,
        row: int,
    ) -> None:
        print(f"SDM [_processLink scope] Adding #{item.link.node.list_index} to row {row}")
        if isinstance(parent, DLGStandardItemModel):
            links_list = parent.editor.core_dlg.starters
        else:
            links_list = parent.link.node.links
            nodeToItems = self.nodeToItems.setdefault(parent.link.node, [])
            if parent not in nodeToItems:
                nodeToItems.append(parent)
            linkToItems = self.linkToItems.setdefault(parent.link, [])
            if parent not in linkToItems:
                linkToItems.append(parent)
        nodeToItems = self.nodeToItems.setdefault(item.link.node, [])
        if item not in nodeToItems:
            nodeToItems.append(item)
        linkToItems = self.linkToItems.setdefault(item.link, [])
        if item not in linkToItems:
            linkToItems.append(item)
        links_list.insert(row, item.link)
        item.link.list_index = row
        for i in range(row + 1, len(links_list)):
            links_list[i].list_index = i

    def _removeLinkFromParent(
        self,
        parent: DLGStandardItem | DLGStandardItemModel | None,
        item: DLGStandardItem,
    ) -> None:
        if isinstance(parent, DLGStandardItemModel) or parent is None:
            links_list = self.editor.core_dlg.starters
        else:
            links_list = parent.link.node.links
        index = links_list.index(item.link)
        print(f"SDM [_removeLinkFromParent scope] Removing #{item.link.node.list_index} from row {index}")
        links_list.remove(item.link)
        for i in range(index, len(links_list)):
            links_list[i].list_index = i

    def onModelReset(self):
        print(f"{self.__class__.__name__}.onModelReset()")
        self.linkToItems.clear()
        self.nodeToItems.clear()

    def resetModel(self):
        print(f"{self.__class__.__name__}.resetModel()")
        self.beginResetModel()
        self.clear()
        self.linkToItems.clear()
        self.nodeToItems.clear()
        self.endResetModel()

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        print(f"{self.__class__.__name__}.onRowsRemoved(index={self.treeView.getIdentifyingText(index)}, value={value}, role={role})")
        item = self.itemFromIndex(index)
        if item is not None:
            item.setData(value, role)
            self.dataChanged.emit(index, index, [role])
            return True
        return False

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
        return ["application/x-qabstractitemmodeldatalist", "application/x-pykotor-dlgbranch"]

    def mimeData(self, indexes: Iterable[QModelIndex]) -> QMimeData:
        mimeData = QMimeData()
        encodedDlgNodeData = QByteArray()
        pykotorDlgStream = QDataStream(encodedDlgNodeData, QIODevice.OpenModeFlag.WriteOnly)
        pykotorDlgStream.writeInt64(id(self))
        for index in indexes:
            print("<SDM> [mimeData scope] index: ", self.treeView.getIdentifyingText(index))
            if not index.isValid():
                continue
            item = self.itemFromIndex(index)
            if item is None:
                continue
            pykotorDlgStream.writeString(json.dumps(item.link.to_dict()).encode())
        mimeData.setData("application/x-pykotor-dlgbranch", encodedDlgNodeData)
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
        if not data.hasFormat("application/x-pykotor-dlgbranch"):
            return False

        print("<SDM> [dropMimeData scope] action: ", action)
        if action == Qt.DropAction.IgnoreAction:
            print(f"{self.__class__.__name__}.dropMimeData: action set to Qt.DropAction.IgnoreAction")
            return True

        if not parent.isValid():
            parent = self.index(0, 0, QModelIndex())
            print("<SDM> [dropMimeData scope] fallback parent: ", self.treeView.getIdentifyingText(parent))
        if not parent.isValid():
            print("Fallback parent failed, exiting...")
            return False

        parentItem: DLGStandardItem | None = self.itemFromIndex(parent)
        if parentItem is None:
            return False

        try:
            stream = QDataStream(data.data("application/x-pykotor-dlgbranch"), QIODevice.ReadOnly)
            dlg_nodes_encoded: bytes = stream.readString()
            dlg_nodes_json: str = dlg_nodes_encoded.decode()
            print("<SDM> [dropMimeData scope] dlg_nodes_json: ", dlg_nodes_json)
            dlg_nodes_dict: dict[str, Any] = json.loads(dlg_nodes_json)
            print("<SDM> [dropMimeData scope] dlg_nodes_dict: ", dlg_nodes_dict)
            deserialized_dlg_link: DLGLink = DLGLink.from_dict(dlg_nodes_dict)
            print("<SDM> [dropMimeData scope] deserialized_dlg_link: ", deserialized_dlg_link)
        except Exception:
            RobustRootLogger.exception("Failed to deserialize dropped mime data of 'application/x-pykotor-dlgbranch' format.")
        else:
            self.pasteItem(parentItem, deserialized_dlg_link, asNewBranches=False)

        return True

    def itemFromIndex(self, index: QModelIndex) -> DLGStandardItem | None:
        # sourcery skip: assign-if-exp, reintroduce-else
        item: QStandardItem | DLGStandardItem = super().itemFromIndex(index)
        if item.__class__ is QStandardItem:
            return None
        return cast(DLGStandardItem, item)

    def isCopy(self, item: DLGStandardItem) -> bool:
        """Determine if the item is already loaded into the tree, or if it's collapsed until onItemExpanded is called."""
        if not item.hasChildren():
            return False
        return item.child(0, 0).data(_FUTURE_EXPAND_ROLE) is True

    def loadDLGItemRec(self, itemToLoad: DLGStandardItem):
        alreadyListed = itemToLoad.link in self.linkToItems or itemToLoad.link.node in self.nodeToItems
        self.linkToItems.setdefault(itemToLoad.link, []).append(itemToLoad)
        self.nodeToItems.setdefault(itemToLoad.link.node, []).append(itemToLoad)

        self.treeView.setItemDisplayData(itemToLoad)
        if not alreadyListed:
            for child_link in itemToLoad.link.node.links:
                child_item = DLGStandardItem(link=child_link)
                self.loadDLGItemRec(child_item)
                itemToLoad.appendRow(child_item)
        elif itemToLoad.link.node.links:
            self.setItemFutureExpand(itemToLoad)

        self.dataChanged.emit(itemToLoad.index(), itemToLoad.index())

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
        # item.appendRow([dummy_child, QStandardItem(), QStandardItem()])
        item.appendRow((dummy_child,))

    def addRootNode(self):
        """Adds a root node to the dialog graph."""
        self._coreAddNode(DLGEntry(), self.editor.core_dlg.starters, self)

    def _coreAddNode(
        self,
        source: DLGNode,
        targetLinks: list[DLGLink],
        item: QStandardItem | QStandardItemModel,
    ):
        newLink = DLGLink(source)
        print("<SDM> [_coreAddNode scope] newLink: ", newLink)

        newLink.list_index = len(targetLinks)
        print("<SDM> [_coreAddNode scope] newLink.list_index: ", newLink.list_index)

        targetLinks.append(newLink)
        self.addChildToItem(item, newLink)

    def addChildToItem(self, parentItem: DLGStandardItem, link: DLGLink) -> DLGStandardItem:
        """Helper method to update the UI with the new link."""
        newItem = DLGStandardItem(link=link)
        print("<SDM> [addChildToItem scope] newItem: ", newItem)

        self.treeView.setItemDisplayData(newItem)
        parentItem.appendRow(newItem)
        return newItem

    def _linkCoreNodes(self, target: DLGNode, source: DLGNode) -> DLGLink:
        """Helper method to add a source node to a target node."""
        newLink = DLGLink(source)
        print("<SDM> [_linkCoreNodes scope] newLink: ", newLink)

        newLink.list_index = len(target.links)
        print("<SDM> [_linkCoreNodes scope] newLink.list_index: ", newLink.list_index)

        target.links.append(newLink)
        return newLink

    def copyNode(self, node: DLGNode):
        QApplication.clipboard().setText(json.dumps(node.to_dict()))

    def pasteItem(
        self,
        parentItem: DLGStandardItem | QStandardItemModel,
        pastedNode: DLGNode | None = None,
        *,
        asNewBranches: bool = True,
    ):
        """Paste a node from the clipboard to the parent node."""
        link: DLGLink = parentItem.link
        parentNode: DLGNode = link.node
        pastedNode: DLGNode = self.editor._copy if pastedNode is None else pastedNode
        self.layoutAboutToBeChanged.emit()
        visited: set[int] = set()
        all_entries, all_replies = self._getAllIndices()
        if asNewBranches:
            new_index = self._getNewNodeListIndex(pastedNode, all_entries, all_replies)
            print(f"<SDM> [_integrateChildNodes scope] pastedNode.list_index: {pastedNode.list_index} --> {new_index}")
            pastedNode2 = DLGNode.from_dict(pastedNode.to_dict())
            assert pastedNode != pastedNode2
            pastedNode = pastedNode2
            pastedNode.list_index = new_index
        queue: list[DLGNode] = [pastedNode]
        while queue:
            curNode = queue.pop(0)
            nodeHash = hash(curNode)
            if nodeHash in visited:
                continue
            visited.add(nodeHash)
            if not asNewBranches and curNode not in self.nodeToItems:
                new_index = self._getNewNodeListIndex(curNode, all_entries, all_replies)
                print(f"<SDM> [_integrateChildNodes scope] curNode.list_index: {curNode.list_index} --> {new_index}")
                curNode.list_index = new_index

            queue.extend([link.node for link in curNode.links if hash(link.node) not in visited])
        newLink = self._linkCoreNodes(parentNode, pastedNode)
        # Update the model
        self.blockSignals(True)
        newItem = DLGStandardItem(link=newLink)
        parentItem.appendRow(newItem)
        self.treeView.setItemDisplayData(newItem)
        if pastedNode in self.nodeToItems:
            self.setItemFutureExpand(newItem)
        else:
            self.editor.model.loadDLGItemRec(newItem)
        if not isinstance(parentItem, DLGStandardItemModel):
            self.treeView.setItemDisplayData(parentItem)
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
        """Generate a new unique index for the node."""
        if isinstance(node, DLGEntry):
            indices = {entry.list_index for entry in self.editor.core_dlg.all_entries()} if entryIndices is None else entryIndices
            print("<SDM> [_getNewNodeListIndex scope] indices: ", indices)

            print("<SDM> [_getNewNodeListIndex scope] indices: ", indices)

        elif isinstance(node, DLGReply):
            indices = {reply.list_index for reply in self.editor.core_dlg.all_replies()} if replyIndices is None else replyIndices
            print("<SDM> [_getNewNodeListIndex scope] indices: ", indices)

            print("<SDM> [_getNewNodeListIndex scope] indices: ", indices)

        else:
            raise TypeError(node.__class__.__name__)
        new_index = max(indices, default=-1) + 1
        print("<SDM> [_getNewNodeListIndex scope] new_index: ", new_index)

        while new_index in indices:
            new_index += 1
        indices.add(new_index)
        return new_index

    def _getAllIndices(self) -> tuple[set[int], set[int]]:
        """Get all indices for entries and replies."""
        entryIndices = {entry.list_index for entry in self.editor.core_dlg.all_entries()}
        print("<SDM> [_getAllIndices scope] entryIndices: ", entryIndices)

        replyIndices = {reply.list_index for reply in self.editor.core_dlg.all_replies()}
        print("<SDM> [_getAllIndices scope] replyIndices: ", replyIndices)

        return entryIndices, replyIndices

    def deleteNodeEverywhere(self, node: DLGNode):
        """Removes all occurrences of a node and all links to it from the model and self.editor.core_dlg."""

        def removeNodeRecursive(item: DLGStandardItem, node_to_remove: DLGNode):
            for i in range(item.rowCount() - 1, -1, -1):
                child_item = item.child(i)
                #print("<SDM> [removeNodeRecursive scope] child_item index info: ", self.treeView.getIdentifyingText(child_item.index()))
                if child_item is not None:
                    if child_item.data(_FUTURE_EXPAND_ROLE) or not isinstance(child_item, DLGStandardItem):
                        continue
                    #print("<SDM> [removeNodeRecursive scope] child_item.link.node: ", child_item.link.node)

                    if child_item.link.node is node_to_remove:
                        item.removeRow(i)
                    else:
                        removeNodeRecursive(child_item, node_to_remove)

        def removeNodeFromModel(model: QStandardItemModel, node_to_remove: DLGNode):
            for i in range(model.rowCount() - 1, -1, -1):
                item = model.item(i)
                #print("<SDM> [removeNodeFromModel scope] item index info: ", self.treeView.getIdentifyingText(item.index()))

                if item is not None:
                    if item.data(_FUTURE_EXPAND_ROLE) or not isinstance(item, DLGStandardItem):
                        continue
                    lookupNode = item.link.node
                    #print("<SDM> [removeNodeFromModel scope] lookupNode: ", lookupNode)
                    if lookupNode == node_to_remove:
                        model.removeRow(i)
                    else:
                        removeNodeRecursive(item, node_to_remove)

        def removeLinksToNode(model: QStandardItemModel, node_to_remove: DLGNode):
            for i in range(model.rowCount()):
                item = model.item(i)
                #print("<SDM> [removeLinksToNode scope] item index info: ", self.treeView.getIdentifyingText(item.index()))

                removeLinksRecursive(item, node_to_remove)

        def removeLinksRecursive(item: DLGStandardItem, node_to_remove: DLGNode):
            for i in range(item.rowCount()):
                child_item = item.child(i)
                #if child_item.index().isValid():
                #    print(f"removeLinksRecursive: invalid child item at '{i}': ", self.treeView.getIdentifyingText(child_item.index()))
                #print("<SDM> [removeLinksRecursive scope] child_item index info: ", self.treeView.getIdentifyingText(child_item.index()))

                if child_item is not None:
                    if child_item.data(_FUTURE_EXPAND_ROLE) or not isinstance(child_item, DLGStandardItem):
                        continue
                    link: DLGLink | None = child_item.link

                    if link is None:
                        continue
                    if link.node is node_to_remove:
                        item.removeRow(i)
                    removeLinksRecursive(child_item, node_to_remove)

        removeNodeFromModel(self, node)
        removeLinksToNode(self, node)

        # Remove the node and any links to it from the _dlg.starters list
        self.editor.core_dlg.starters = [link for link in self.editor.core_dlg.starters if link.node is not node]
        for link in self.editor.core_dlg.starters:
            link.node.links = [child_link for child_link in link.node.links if child_link.node is not node]
        # Ensure all other links to this node are removed
        for dlg_node in self.editor.core_dlg.all_entries() + self.editor.core_dlg.all_replies():
            dlg_node.links = [child_link for child_link in dlg_node.links if child_link.node is not node]

    def deleteNode(self, item: DLGStandardItem):
        """Deletes a node from the DLG and ui tree model."""
        node = item.link.node
        print("<SDM> [deleteNode scope] node: ", node)

        parent: DLGStandardItem | DLGStandardItemModel | None = item.parent()
        if parent is None:
            self.removeRow(item.row())
        else:
            parentItem: DLGStandardItem | DLGStandardItemModel | None = parent
            parentItem.removeRow(item.row())

    def getNodeFromLinkItem(self, item: DLGStandardItem) -> DLGNode | None:
        link: DLGLink = item.link
        print("<SDM> [getNodeFromLinkItem scope] link: ", link)

        if link is None:
            return None

        print("<SDM> [getNodeFromLinkItem scope] link.node: ", link.node)

        assert link.node is not None
        return link.node

    def deleteSelectedNode(self):
        """Deletes the currently selected node from the tree."""
        if self.treeView.selectedIndexes():
            index: QModelIndex = self.treeView.selectedIndexes()[0]  # type: ignore[arg-type]
            print("<SDM> [deleteSelectedNode scope] self.treeView.selectedIndexes()[0]: ", index)

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
        itemParent: DLGStandardItem | None = item.parent()
        oldParent: QStandardItemModel | DLGStandardItem = self if itemParent is None else itemParent
        targetParent: QStandardItemModel | DLGStandardItem = targetParentItem or oldParent

        # Early return if the move operation doesn't make sense
        if targetParent == oldParent and new_index == item.row():
            RobustRootLogger.info("Attempted to move item to the same position. Operation aborted.")
            return
        if (
            targetParent != oldParent
            and not isinstance(targetParent, QStandardItemModel)
            and not isinstance(oldParent, QStandardItemModel)
            and targetParent.link.node == oldParent.link.node
        ):
            RobustRootLogger.warning("Cannot drag into a different copy, aborting.")
            return
        if (
            not isinstance(oldParent, QStandardItemModel)
            and oldParent.data(_FUTURE_EXPAND_ROLE)
            or not isinstance(targetParent, QStandardItemModel)
            and targetParent.data(_FUTURE_EXPAND_ROLE)
        ):
            RobustRootLogger.info("Cannot drag into a future expand dummy, aborting.")
            return

        # Ensure copies are expanded first.
        if (
            not isinstance(targetParent, QStandardItemModel)
            and targetParent.hasChildren()
            and targetParent.child(0, 0).data(_FUTURE_EXPAND_ROLE)
        ):
            if targetParent.index().isValid():
                self.treeView.expand(targetParent.index())
            else:
                self.editor._logger.error("targetParent '%s' at row %s is invalid, cannot move item.", targetParent.text(), targetParent.row())
                return

        if new_index < 0 or new_index > targetParent.rowCount():
            RobustRootLogger.info("New row index %d out of bounds. Cancelling operation.", new_index)
            return

        oldRow: int = item.row()
        if oldParent == targetParent and new_index > oldRow:
            new_index -= 1

        itemToMove = oldParent.takeRow(oldRow)[0]
        targetParent.insertRow(new_index, itemToMove)
        if not isinstance(targetParent, DLGStandardItemModel):
            self.treeView.setItemDisplayData(targetParent)
            self._updateCopies(targetParent.link, targetParent)

    def _updateCopies(self, link: DLGLink, itemToIgnore: DLGStandardItem | None = None):
        if link.node in self.nodeToItems:
            items = self.nodeToItems[link.node]
            print(f"Updating {len(items)} items containing node {link.node}")
            for item in items:
                if item is itemToIgnore:
                    continue
                self.treeView.setItemDisplayData(item)
                if item.hasChildren() and item.child(0, 0).data(_FUTURE_EXPAND_ROLE):
                    # Item has a future expand role, only update display data
                    continue
                self.blockSignals(True)
                item.removeRows(0, item.rowCount())
                self.blockSignals(False)
                self.setItemFutureExpand(item)
                self.treeView.collapse(item.index())

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


        parent = self if item.parent() is None else itemParent
        print("<SDM> [shiftItem scope] parent: ", parent)


        assert parent is not None
        newRow: int = oldRow + amount
        print("<SDM> [shiftItem scope] newRow: ", newRow)


        itemParentText = "" if itemParent is None else itemParent.text()

        print("Received item: '%s', row shift amount %s", itemText, amount)
        print("Attempting to change row index for '%s' from %s to %s in parent '%s'", itemText, oldRow, newRow, itemParentText)

        if newRow >= parent.rowCount() or newRow < 0:
            RobustRootLogger.info("New row index '%s' out of bounds. Already at the start/end of the branch. Cancelling operation.", newRow)
            return

        itemToMove = parent.takeRow(oldRow)[0]
        print("<SDM> [shiftItem scope] itemToMove: ", itemToMove)

        print("itemToMove '%s' taken from old position: '%s', moving to '%s'", itemToMove.text(), oldRow, newRow)
        parent.insertRow(newRow, itemToMove)
        selectionModel = self.treeView.selectionModel()
        if selectionModel is not None and not noSelectionUpdate:
            selectionModel.select(itemToMove.index(), QItemSelectionModel.ClearAndSelect)
            print("Selection updated to new index")

        itemParent = itemToMove.parent()
        print("<SDM> [shiftItem scope] itemParent: ", itemParent)
        print("Item new parent after move: '%s'", itemParent.text() if itemParent else "Root")
        if isinstance(itemParent, DLGStandardItem):
            self._updateCopies(itemParent.link, itemParent)

        RobustRootLogger.info("Moved link from %s to %s", oldRow, newRow)
        self.treeView.viewport().update()

    def removeLink(self, item: DLGStandardItem):
        """Removes the link from the parent node."""
        parent = item.parent()
        item_row = item.row()
        print("<SDM> [removeLink scope] item_row: %s", item_row)

        if parent is None:
            self.removeRow(item_row)
        else:
            print("<SDM> [removeLink scope] parent: %s", parent.text())
            parent.removeRow(item_row)
            self._updateCopies(parent.link, parent)


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
            print(f"ABOVE cur index: {view.getIdentifyingText(curIndex)}")
            return cls(curIndex.parent(), max(curIndex.row(), 0), DropPosition.ABOVE, indicator_rect)
        if pos.y() >= lower_threshold:
            # Adjust for bottom edge of the index
            indicator_rect = QRect(rect.bottomLeft(), rect.bottomRight())
            print(f"BELOW cur index: {view.getIdentifyingText(curIndex)}")
            return cls(curIndex.parent(), curIndex.row()+1, DropPosition.BELOW, indicator_rect)

        print(f"ON TOP OF cur index: {view.getIdentifyingText(curIndex)}")
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
                print(f"Root item at row '{self.row}' is invalid.")
                return False
            parentItem = view.model().itemFromIndex(rootItemIndex)
        dragged_node = dragged_link.node
        node_types_match = view.bothNodesSameType(dragged_node, parentItem.link.node)
        if self.position is DropPosition.ON_TOP_OF:
            node_types_match = not node_types_match

        if ((self.position is DropPosition.ON_TOP_OF) == node_types_match) == (rootItemIndex is not None):
            print(f"Drop operation invalid: {self.position.name} vs node type check.")
            return False

        print("Drop operation is valid.")
        return True


class DLGTreeView(RobustTreeView):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.editor: DLGEditor | None = None
        self.dropIndicatorRect: QRect = QRect()
        self.maxDragTextSize: int = 40
        self.num_links: int = 0
        self.num_unique_nodes: int = 0
        self.draggedItem: DLGStandardItem | None = None
        self.dropTarget: DropTarget | None = None
        self.startPos: QPoint = QPoint()
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDropIndicatorShown(False)  # We have our own.
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        #self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove | QAbstractItemView.DragDropMode.DragDrop)
        self.setUniformRowHeights(False)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.viewport().update()  # call our html delegate to recalc item sizing/spacing.

    def setItemDisplayData(self, item: DLGStandardItem):
        """Refreshes the item text and formatting based on the node data."""
        node: DLGNode = item.link.node
        #print("<SDM> [setItemDisplayData scope] DLGNode: ", node)

        color: QColor | None = None
        if GlobalSettings().selectedTheme == "Default (Light)":
            if isinstance(node, DLGEntry):
                color = QColor(255, 0, 0)  # if not _isCopy else QColor(210, 90, 90)
                prefix = "E"
            elif isinstance(node, DLGReply):
                color = QColor(0, 0, 255)  # if not _isCopy else QColor(90, 90, 210)
                prefix = "R"
            else:
                raise ValueError(f"node must be DLGEntry/DLGReply, but was instead {node.__class__.__name__}")
        elif isinstance(node, DLGEntry):
            color = QColor(255, 64, 64)  # if not _isCopy else QColor(255, 128, 128)
            prefix = "E"
        elif isinstance(node, DLGReply):
            color = QColor(64, 180, 255)  # if not _isCopy else QColor(128, 200, 255)
            prefix = "R"
        else:
            raise ValueError(f"node must be DLGEntry/DLGReply, but was instead {node.__class__.__name__}")

        color_hex = color.name() if color else "#000000"
        list_prefix = f"<b>{prefix}{node.list_index}:</b> "
        text = str(node.text) if self.editor._installation is None else self.editor._installation.string(node.text, "")

        if not node.links:
            display_text = f"{text} <span style='color:{QColor(255, 127, 80).name()};'><b>[End Dialog]</b></span>"
        else:
            display_text = text if text.strip() else "(continue)"

        # Add CSS styles for better spacing and appearance
        formatted_text = f'<span style="color:{color_hex}; font-size:{self.text_size}pt; line-height:120%;">{list_prefix}{display_text}</span>'
        item.setData(formatted_text, Qt.DisplayRole)

        if color:
            item.setForeground(QBrush(color))

    def draw_drag_icons(
        self,
        painter: QPainter,
        center: QPoint,
        radius: int,
        color: QColor,
        text: str,
    ):
        gradient = QRadialGradient(center, radius)
        print("<SDM> [draw_drag_icons scope] gradient: ", gradient)

        gradient.setColorAt(0, QColor(255, 255, 255, 200))
        gradient.setColorAt(0.5, color.lighter())
        gradient.setColorAt(1, color)
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, radius, radius)

        painter.setPen(QColor(0, 0, 0))
        font = QFont("Arial", 10, QFont.Bold)
        print("<SDM> [draw_drag_icons scope] font: ", font)

        painter.setFont(font)
        text_rect = QRect(center.x() - radius, center.y() - radius, radius * 2, radius * 2)
        print("<SDM> [draw_drag_icons scope] text_rect: ", text_rect)

        painter.drawText(text_rect, Qt.AlignCenter, text)

        print(f"{self.__class__.__name__}.draw_drag_icons: Drawing drag icon at {center} with text {text}")  # noqa: SLF001

    def calculate_links_and_nodes(self, root_node: DLGNode) -> tuple[int, int]:
        queue: deque[DLGNode] = deque([root_node])
        print("<SDM> [calculate_links_and_nodes scope] deque[DLGNode]: ", queue)

        seen_nodes: set[DLGNode] = set()
        print("<SDM> [calculate_links_and_nodes scope] seen_nodes: ", seen_nodes)

        self.num_links = 0
        self.num_unique_nodes = 0

        while queue:
            node: DLGNode = queue.popleft()
            if node in seen_nodes:
                continue
            seen_nodes.add(node)
            self.num_links += len(node.links)
            queue.extend(link.node for link in node.links)

        self.num_unique_nodes = len(seen_nodes)
        print("<SDM> [calculate_links_and_nodes scope] self.num_unique_nodes: ", self.num_unique_nodes)

    def paintEvent(self, event: QPaintEvent):
        super().paintEvent(event)
        if self.dropIndicatorRect.isNull():
            return

        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.Antialiasing)  # For smoother edges

        # Check if the rect is a line or should act as a highlight area
        if self.dropIndicatorRect.topLeft().y() == self.dropIndicatorRect.bottomLeft().y():
            # It's more of a line, draw it with a dashed pen
            pen = QPen(Qt.black, 1, Qt.DashLine)
            painter.setPen(pen)
            painter.drawLine(self.dropIndicatorRect.topLeft(), self.dropIndicatorRect.topRight())
        else:
            # It's an area, fill it with a light grey highlight without a border
            highlight_color = QColor(200, 200, 200, 120)  # Light grey with alpha transparency
            painter.fillRect(self.dropIndicatorRect, highlight_color)

        painter.end()

    def initStyleOption(self, option: QStyleOptionViewItem, index: QModelIndex):
        """Initialize style option for the given index."""
        option.initFrom(self)
        option.rect = self.visualRect(index)
        option.state = self.viewOptions().state
        option.state |= QStyle.State_Active
        option.features = QStyleOptionViewItem.ViewItemFeature.HasDisplay
        option.widget = self
        option.text = index.data(Qt.DisplayRole)

        icon = index.data(Qt.DecorationRole)
        option.icon = icon if icon is not None else QIcon()

    def keyPressEvent(self, event: QKeyEvent):
        print("<SDM> [DLGTreeView.keyPressEvent scope] key: %s", event.key())
        self.editor.keyPressEvent(event, isTreeViewCall=True)
        super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if (
            event.button() == Qt.LeftButton
            and self.startPos.isNull()
        ):
            self.startPos = event.pos()
            print("<SDM> [mousePressEvent scope] self.startPos: ", self.startPos)

            print(f"DLGTreeView: set self.startPos to  ({self.startPos.x()}, {self.startPos.y()})")
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if (
            event.buttons() & Qt.LeftButton
            and not self.startPos.isNull()
            and (event.pos() - self.startPos).manhattanLength() >= QApplication.startDragDistance()
            and self.draggedItem is None
        ):
            #if self.prepareDrag(self.indexAt(self.startPos)):
            #    print(f"{self.__class__.__name__}.mouseMoveEvent picked up a drag")
            #    self.performDrag()
            #else:
            #    self.resetDragState()
            super().mouseMoveEvent(event)
        super().mouseMoveEvent(event)

    def createDragPixmap(self, dragged_item: DLGStandardItem) -> QPixmap:
        pixmap = QPixmap(250, 90)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(255, 255, 255, 200))
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawRoundedRect(QRect(0, 0, pixmap.width(), pixmap.height()), 10, 10)
        self.draw_drag_icons(painter, QPoint(30, 25), 15, QColor(255, 0, 0), f"{self.num_links}")
        self.draw_drag_icons(painter, QPoint(100, 25), 15, QColor(0, 0, 255), f"{self.num_unique_nodes}")
        font = QFont("Arial", 11)
        painter.setFont(font)
        text = dragged_item.text()[:40] + ("..." if len(dragged_item.text()) > 40 else "")
        painter.setPen(QColor(50, 50, 50))
        painter.drawText(QRect(10, 50, 230, 40), Qt.AlignCenter, text)
        painter.end()
        return pixmap

    def performDrag(self):
        print("startDrag: Post-initiate drag operation, call drag.exec_()")
        drag = QDrag(self)
        mimeData = QMimeData()
        encoded_data = QByteArray()
        stream = QDataStream(encoded_data, QIODevice.WriteOnly)
        stream.writeInt64(id(self.model()))
        stream.writeString(json.dumps(self.draggedItem.link.to_dict()))
        mimeData.setData("application/x-pykotor-dlgbranch", encoded_data)
        drag.setMimeData(mimeData)
        drag.setPixmap(self.createDragPixmap(self.draggedItem))
        drag.setHotSpot(self.mapFromGlobal(self.startPos))
        drag.exec_(self.model().supportedDragActions())
        print("\nstartDrag: completely done")

    def prepareDrag(self, index: QModelIndex | None = None, event: QDragEnterEvent | QDragMoveEvent | QDropEvent = None) -> bool:
        print(f"{self.__class__.__name__}.\nprepareDrag(index={index}, event={event})")
        if self.draggedItem is not None:
            return True

        if event:
            mimeData = event.mimeData()
            if mimeData.hasFormat("application/x-pykotor-dlgbranch"):
                stream = QDataStream(mimeData.data("application/x-pykotor-dlgbranch"), QIODevice.ReadOnly)
                if stream.readInt64() == id(self.model()):
                    self.draggedItem = DLGLink.from_dict(json.loads(stream.readString().decode()))
                    self.calculate_links_and_nodes(self.draggedItem.link.node)
                    return True
                #return False
                return True

        if index is None:
            index = self.currentIndex()

        dragged_item = self.model().itemFromIndex(index)
        if not dragged_item or not hasattr(dragged_item, "link") or dragged_item.link is None:
            print(f"{self.getIdentifyingText(index)}")
            print("Above item does not contain DLGLink information\n")
            return False

        self.draggedItem = dragged_item
        self.calculate_links_and_nodes(self.draggedItem.link.node)
        return True

    def startDrag(self, supportedActions: Qt.DropActions | Qt.DropAction):
        print("\nstartDrag: Initiate the drag operation, call self.prepareDrag")
        if not self.prepareDrag():
            print("startDrag called but prepareDrag returned False, resetting the drag state.")
            self.resetDragState()
            return
        super().startDrag(supportedActions)
        print("startDrag done, call resetDragState")
        self.resetDragState()

    def dragEnterEvent(self, event: QDragEnterEvent):
        print(f"\ndragEnterEvent(event={event})")
        if not event.mimeData().hasFormat("application/x-pykotor-dlgbranch"):
            print("dragEnterEvent mimeData does not match our format, invalidating.")
            self.setInvalidDragDrop(event)
            return
        if not self.draggedItem:
            RobustRootLogger.warning("dragEnterEvent called before prepareDrag, rectifying.")
            if not self.prepareDrag():
                print("dragEnterEvent: prepareDrag returned False, resetting the drag state.")
                self.setInvalidDragDrop(event)
                self.resetDragState(event)
                return
        self.setValidDragDrop(event)

    def dragMoveEvent(self, event: QDragMoveEvent):
        print(f"dragMoveEvent(event={event})")
        if not event.mimeData().hasFormat("application/x-pykotor-dlgbranch"):
            self.setInvalidDragDrop(event)
            super().dragMoveEvent(event)
            return

        print("<SDM> [dragMoveEvent scope], event mimedata matches our format.")
        if self.draggedItem is None:
            RobustRootLogger.warning("dragMoveEvent called before prepareDrag, rectifying now....")
            if not self.prepareDrag():
                self.setInvalidDragDrop(event)
                self.resetDragState()
                return

        pos: QPoint = event.pos()
        self.dropTarget = DropTarget.determineDropTarget(self, pos)
        self.dropIndicatorRect = self.dropTarget.indicator_rect
        if not self.dropTarget.is_valid_drop(self.draggedItem.link, self):
            print(f"{self.__class__.__name__}.dragMoveEvent: Target at mouse position is not valid.")
            self.setInvalidDragDrop(event)
            super().dragMoveEvent(event)
            return

        self.setValidDragDrop(event)
        super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent):
        self.setInvalidDragDrop(event)  # always set invalid so qt won't try to handle it past this function
        if not event.mimeData().hasFormat("application/x-pykotor-dlgbranch"):
            print("<SDM> [dropEvent scope] event does not match our format")
            self.resetDragState()
            return

        if self.dropTarget.parentIndex.isValid():
            dropParent = self.model().itemFromIndex(self.dropTarget.parentIndex)
        else:
            dropParent = self.model()

        if not self.isItemFromCurrentModel(event):
            print("<SDM> [dropEvent scope] not self.isItemFromCurrentModel(event), calling pasteItem")
            dragged_link: DLGLink | None = self.getDraggedNodeFromMimeData(event.mimeData())
            if dragged_link:
                if not self.dropTarget.is_valid_drop(dragged_link, self):
                    print("dropEvent: dropTarget is not valid (for a pasteItem)")
                    self.resetDragState()
                    return
                self.model().pasteItem(dropParent, dragged_link.node, asNewBranches=False)
                super().dropEvent(event)
            else:
                print("<SDM> [dropEvent scope] could not call pasteItem: dragged_node could not be deserialized from mime data.")
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
        new_index = self.dropTarget.row
        if self.dropTarget.position is DropPosition.ON_TOP_OF:
            new_index = 0
        self.model().moveItemToIndex(self.draggedItem, new_index, dropParent)
        super().dropEvent(event)
        parentIndexOfDrop = self.dropTarget.parentIndex
        droppedAtRow = self.dropTarget.row
        self.resetDragState()
        #self.selectionModel().setCurrentIndex(self.model().index(droppedAtRow, 0, parentIndexOfDrop), QItemSelectionModel.ClearAndSelect)

    def getDraggedNodeFromMimeData(self, mimeData: QMimeData) -> DLGLink | None:
        try:
            encoded_data = mimeData.data("application/x-pykotor-dlgbranch")
            stream = QDataStream(encoded_data, QIODevice.ReadOnly)
            _model_id = stream.readInt64()
            link_variant = stream.readString().decode()
            return DLGLink.from_dict(json.loads(link_variant))
        except Exception:  # noqa: BLE001
            RobustRootLogger.exception("Failed to deserialize mime data node.")
            return None

    @staticmethod
    def bothNodesSameType(dragged_node: DLGNode, target_node: DLGNode) -> bool:
        return (
            isinstance(dragged_node, DLGReply) and isinstance(target_node, DLGReply)
            or isinstance(dragged_node, DLGEntry) and isinstance(target_node, DLGEntry)
        )

    def isItemFromCurrentModel(self, event: QDropEvent) -> bool:
        source = event.source()
        if not isinstance(source, QTreeView):
            print("isItemFromCurrentModel: Not our drag.")
            return False
        return source.model() == self.model()

    def resetDragState(self):
        print("<SDM> [resetDragState scope]")
        self.startPos = QPoint()
        self.draggedItem = None
        self.dropIndicatorRect = QRect()
        self.dropTarget = None
        self.unsetCursor()
        QTimer.singleShot(0, self.viewport().update)

    def setInvalidDragDrop(
        self,
        event: QDropEvent | QDragEnterEvent | QDragMoveEvent,
    ):
        print("<SDM> [setInvalidDragDrop scope]")
        event.accept()
        event.setDropAction(Qt.DropAction.IgnoreAction)
        self.setCursor(Qt.CursorShape.ForbiddenCursor)
        QTimer.singleShot(0, self.viewport().update)

    def setValidDragDrop(
        self,
        event: QDropEvent | QDragEnterEvent | QDragMoveEvent,
    ):
        print("<SDM> [setValidDragDrop scope]")
        event.accept()
        event.setDropAction(Qt.DropAction.MoveAction if self.isItemFromCurrentModel(event) else Qt.DropAction.CopyAction)
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def _selectDragOverIndex(self, curIndex: QModelIndex):
        self.selectionModel().clearSelection()
        self.isSelecting = True
        selection: QItemSelection = QItemSelection()
        drag_item = self.draggedItem
        print("<SDM> [_selectDragOverIndex scope] drag_item: ", drag_item)

        cur_item = self.model().itemFromIndex(curIndex)
        print("<SDM> [_selectDragOverIndex scope] cur_item: ", cur_item)

        selection.select(curIndex, curIndex)
        selection.select(self.draggedItem.index(), self.draggedItem.index())

        drag_item_text = drag_item.text() if drag_item is not None else "(None)"
        cur_item_text = cur_item.text() if cur_item is not None else "(None)"

        print("<SDM> [_selectDragOverIndex scope] [drag_item, cur_item] selection: [%s]", f"{drag_item_text}, {cur_item_text}")
        self.selectionModel().select(selection, QItemSelectionModel.Select)
        self.isSelecting = False


def install_immediate_tooltip(widget: QWidget, tooltip_text: str):
    widget.setToolTip(tooltip_text)
    widget.setMouseTracking(True)
    widget.event = lambda event: QToolTip.showText(cast(QHoverEvent, event).pos(), widget.toolTip(), widget)


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

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.editors.dlg import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.editors.dlg import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.editors.dlg import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.editors.dlg import Ui_MainWindow  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setupDLGTreeMVC()

        self._setupMenus()
        self._setupSignals()
        self._installation = installation
        if installation:
            self._setupInstallation(installation)

        self._focused: bool = False
        self.core_dlg: DLG = DLG()
        self._copy: DLGNode | None = None

        self.ui.textEdit.mouseDoubleClickEvent = self.editText
        install_immediate_tooltip(self.ui.textEdit, "Double click to edit.")
        if GlobalSettings().selectedTheme != "Default (Light)":
            self.ui.textEdit.setStyleSheet(f"{self.ui.textEdit.styleSheet()} QPlainTextEdit {{color: black;}}")

        self.buffer: QBuffer = QBuffer()
        self.player: QMediaPlayer = QMediaPlayer(self)
        self.tempFile: QTemporaryFile | None = None

        self.acceptUpdates: bool = False
        self.ui.splitter.setSizes([99999999, 1])
        self.new()
        self.keysDown: set[int] = set()

        # Debounce timer to delay a cpu-intensive task.
        self.voIdEditTimer = QTimer(self)
        self.voIdEditTimer.setSingleShot(True)
        self.voIdEditTimer.setInterval(500)  # 500 milliseconds delay
        self.voIdEditTimer.timeout.connect(self.onVoIdEditFinished)

    def setupDLGTreeMVC(self):
        # self.model.setHorizontalHeaderLabels(["Dialog", "Children", "Copies"])
        self.treeView: DLGTreeView = self.ui.dialogTree
        self.model: DLGStandardItemModel = DLGStandardItemModel(self.ui.dialogTree)
        self.model.editor = self
        self.treeView.editor = self
        self.treeView.setModel(self.model)
        self.treeView.setItemDelegate(HTMLDelegate(self.treeView))
        # self.ui.dialogTree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        # self.ui.dialogTree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        # self.ui.dialogTree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)

        self.verify_hierarchy(self.treeView)
        self.verify_hierarchy(self.model)

    def verify_hierarchy(self, widget: QWidget, level: int = 0):
        parent: QWidget = widget
        while parent is not None:
            print(f"Level {level}: Checking parent {parent.__class__.__name__} with name {parent.objectName()}")
            if isinstance(parent, DLGEditor):
                print("DLGEditor found in the hierarchy.")
                return
            parent = parent.parent()
            level += 1
        raise RuntimeError(f"DLGEditor is not in the parent hierarchy, attempted {level} levels.")

    def _openDetails(self, locations: list[LocationResult]):
        selectionWindow = FileSelectionWindow(locations, self._installation)
        print("<SDM> [_openDetails scope] selectionWindow: %s", selectionWindow)

        addWindow(selectionWindow)
        selectionWindow.activateWindow()

    def _connectContextMenu(
        self,
        widget: QPlainTextEdit | QLineEdit | QComboBox,
        resref_type: list[ResourceType] | list[ResourceIdentifier],
        order: list[SearchLocation] | None = None,
    ):
        def extendContextMenu(pos):
            if isinstance(widget, QComboBox):
                rootMenu = QMenu(widget)
                widgetText = widget.currentText().strip()
                firstAction = None
            else:
                rootMenu = widget.createStandardContextMenu()
                widgetText = (widget.text() if isinstance(widget, QLineEdit) else widget.toPlainText()).strip()
                firstAction = rootMenu.actions()[0] if rootMenu.actions() else None

            print("<SDM> [extendContextMenu scope] rootMenu: ", rootMenu)
            print("<SDM> [extendContextMenu scope] widgetText: ", widgetText)

            if widgetText:
                fileMenu = QMenu("File...", widget)
                print("<SDM> [extendContextMenu scope] fileMenu: ", fileMenu)

                if firstAction:
                    rootMenu.insertMenu(firstAction, fileMenu)
                    rootMenu.insertSeparator(firstAction)
                else:
                    rootMenu.addMenu(fileMenu)

                rootMenu.insertMenu(firstAction, fileMenu)
                rootMenu.insertSeparator(firstAction)
                search_order = order or [
                    SearchLocation.CHITIN,
                    SearchLocation.OVERRIDE,
                    SearchLocation.MODULES,
                    SearchLocation.RIMS,
                ]
                print("<SDM> [extendContextMenu scope] search_order: ", search_order)

                locations = self._installation.locations(([widgetText], resref_type if isinstance(resref_type[1], ResourceType) else resref_type), search_order)
                print("<SDM> [extendContextMenu scope] locations: ", locations)

                flatLocations = [item for sublist in locations.values() for item in sublist] if isinstance(locations, dict) else locations
                print("<SDM> [extendContextMenu scope] flatLocations: ", flatLocations)

                if flatLocations:
                    for location in flatLocations:
                        displayPath = location.filepath.relative_to(self._installation.path())
                        if location.as_file_resource().inside_bif:
                            displayPath /= location.as_file_resource().filename()
                        displayPathStr = str(displayPath)
                        print("<SDM> [extendContextMenu scope] displayPathStr: ", displayPathStr)

                        locationMenu = fileMenu.addMenu(displayPathStr)
                        print("<SDM> [extendContextMenu scope] locationMenu: ", locationMenu)

                        resourceMenuBuilder = ResourceItems(resources=[location])
                        print("<SDM> [extendContextMenu scope] resourceMenuBuilder: ", resourceMenuBuilder)

                        resourceMenuBuilder.build_menu(locationMenu, self._installation)

                    detailsAction = QAction("Details...", fileMenu)
                    print("<SDM> [extendContextMenu scope] detailsAction: ", detailsAction)

                    detailsAction.triggered.connect(lambda: self._openDetails(flatLocations))
                    fileMenu.addAction(detailsAction)
                else:
                    fileMenu.setDisabled(True)
                for action in rootMenu.actions():
                    if action.text() == "File...":
                        action.setText(f"{len(flatLocations)} file(s) located")
                        break

            rootMenu.exec_(widget.mapToGlobal(pos))

        widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        widget.customContextMenuRequested.connect(extendContextMenu)

    def _setupSignals(self):
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
        self._connectContextMenu(self.ui.script1ResrefEdit, [ResourceType.NSS, ResourceType.NCS])
        self._connectContextMenu(self.ui.script2ResrefEdit, [ResourceType.NSS, ResourceType.NCS])

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
        self._connectContextMenu(self.ui.condition1ResrefEdit, [ResourceType.NSS, ResourceType.NCS])
        self._connectContextMenu(self.ui.condition2ResrefEdit, [ResourceType.NSS, ResourceType.NCS])

        self.ui.soundComboBox.currentTextChanged.connect(self.onNodeUpdate)
        self._connectContextMenu(
            self.ui.soundComboBox,
            [ResourceType.WAV, ResourceType.MP3],
            [SearchLocation.SOUND, SearchLocation.VOICE],
        )
        self.ui.voiceComboBox.currentTextChanged.connect(self.onNodeUpdate)
        self._connectContextMenu(
            self.ui.voiceComboBox,
            [ResourceType.WAV, ResourceType.MP3],
            [SearchLocation.SOUND, SearchLocation.VOICE],
        )

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
        self.ui.plotIndexSpin.valueChanged.connect(self.onNodeUpdate)
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
        self.ui.dialogTree.selectionModel().selectionChanged.connect(self.onSelectionChanged)

        self.ui.actionReloadTree.triggered.connect(lambda: self._loadDLG(self.core_dlg))

        self.ui.addStuntButton.clicked.connect(self.onAddStuntClicked)
        self.ui.removeStuntButton.clicked.connect(self.onRemoveStuntClicked)
        self.ui.editStuntButton.clicked.connect(self.onEditStuntClicked)

        self.ui.addAnimButton.clicked.connect(self.onAddAnimClicked)
        self.ui.removeAnimButton.clicked.connect(self.onRemoveAnimClicked)
        self.ui.editAnimButton.clicked.connect(self.onEditAnimClicked)

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
        print("<SDM> [load scope] dlg: ", dlg)

        self._loadDLG(dlg)
        self.refreshStuntList()

        self.ui.onAbortEdit.setText(str(dlg.on_abort))
        self.ui.onEndEdit.setText(str(dlg.on_end))
        self.ui.voIdEdit.setText(dlg.vo_id)
        self.ui.voIdEdit.textChanged.connect(self.restartVoIdEditTimer)
        self.ui.ambientTrackEdit.setText(str(dlg.ambient_track))
        self.ui.cameraModelEdit.setText(str(dlg.camera_model))
        self.ui.conversationSelect.setCurrentIndex(dlg.conversation_type.value)
        self.ui.computerSelect.setCurrentIndex(dlg.computer_type.value)
        self.ui.skippableCheckbox.setChecked(dlg.skippable)
        self.ui.animatedCutCheckbox.setChecked(bool(dlg.animated_cut))
        self.ui.oldHitCheckbox.setChecked(dlg.old_hit_check)
        self.ui.unequipHandsCheckbox.setChecked(dlg.unequip_hands)
        self.ui.unequipAllCheckbox.setChecked(dlg.unequip_items)
        self.ui.entryDelaySpin.setValue(dlg.delay_entry)
        self.ui.replyDelaySpin.setValue(dlg.delay_reply)

    def restartVoIdEditTimer(self):
        """Restarts the timer whenever text is changed."""
        self.voIdEditTimer.stop()
        self.voIdEditTimer.start()

    def onVoIdEditFinished(self):
        """Slot to be called when text editing is finished.

        The editors the game devs themselves used probably did something like this
        """
        print("voIdEditTimer debounce finished, populate voiceComboBox with new VO_ID filter...")
        vo_id = self.core_dlg.vo_id
        if vo_id and vo_id.strip():
            vo_id_lower = vo_id.lower()
            filtered_voices = [voice for voice in self.all_voices if vo_id_lower in voice.lower()]
            print(f"filtered {len(self.all_voices)} voices to {len(filtered_voices)} by substring vo_id '{vo_id_lower}'")
        else:
            filtered_voices = self.all_voices
        self.populateComboBox(self.ui.voiceComboBox, filtered_voices)

    def _loadDLG(self, dlg: DLG):
        """Loads a dialog tree into the UI view."""
        print("<SDM> [_loadDLG scope] GlobalSettings().selectedTheme: ", GlobalSettings().selectedTheme)
        if GlobalSettings().selectedTheme == "Default (Light)":
            self.ui.dialogTree.setStyleSheet("")
        self._focused = False
        self.core_dlg = dlg
        self.onVoIdEditFinished()
        self.model.resetModel()
        assert self.model.rowCount() == 0 and self.model.columnCount() == 0, "Model is not empty after resetModel"  # noqa: PT018
        self.model.blockSignals(True)
        self.model.layoutAboutToBeChanged.emit()
        for start in dlg.starters:  # descending order - matches what the game does.
            item = DLGStandardItem(link=start)
            self.model.loadDLGItemRec(item)
            self.model.appendRow(item)
        self.model.layoutChanged.emit()
        assert self.model.rowCount() != 0, "Model is empty after _loadDLG!"  # noqa: PT018
        self.model.blockSignals(False)

    def build(self) -> tuple[bytes, bytes]:
        """Builds a dialogue from UI components."""
        self.core_dlg.on_abort = ResRef(self.ui.onAbortEdit.text())
        print("<SDM> [build scope] self.editor.core_dlg.on_abort: ", self.core_dlg.on_abort)

        self.core_dlg.on_end = ResRef(self.ui.onEndEdit.text())
        print("<SDM> [build scope] self.editor.core_dlg.on_end: ", self.core_dlg.on_end)

        self.core_dlg.vo_id = self.ui.voIdEdit.text()
        print("<SDM> [build scope] self.editor.core_dlg.vo_id: ", self.core_dlg.vo_id)

        self.core_dlg.ambient_track = ResRef(self.ui.ambientTrackEdit.text())
        print("<SDM> [build scope] self.editor.core_dlg.ambient_track: ", self.core_dlg.ambient_track)

        self.core_dlg.camera_model = ResRef(self.ui.cameraModelEdit.text())
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
        write_dlg(self.core_dlg, data, self._installation.game())
        # dismantle_dlg(self.editor.core_dlg).compare(read_gff(data), log_func=print)

        return data, b""

    def new(self):
        super().new()
        self._loadDLG(DLG())

    def handleWidgetWithTSL(self, widget: QWidget, installation: HTInstallation):
        widget.setEnabled(installation.tsl)
        if not installation.tsl:
            widget.setToolTip("This widget is only available in KOTOR II.")

    def _setupInstallation(self, installation: HTInstallation):
        """Sets up the installation for the UI."""
        self._installation = installation
        print("<SDM> [_setupInstallation scope] self._installation: ", self._installation)

        self.handleWidgetWithTSL(self.ui.script1Param1Spin, installation)
        self.handleWidgetWithTSL(self.ui.script1Param2Spin, installation)
        self.handleWidgetWithTSL(self.ui.script1Param3Spin, installation)
        self.handleWidgetWithTSL(self.ui.script1Param4Spin, installation)
        self.handleWidgetWithTSL(self.ui.script1Param5Spin, installation)
        self.handleWidgetWithTSL(self.ui.script1Param6Edit, installation)

        self.handleWidgetWithTSL(self.ui.script2ResrefEdit, installation)
        self.handleWidgetWithTSL(self.ui.script2Param1Spin, installation)
        self.handleWidgetWithTSL(self.ui.script2Param2Spin, installation)
        self.handleWidgetWithTSL(self.ui.script2Param3Spin, installation)
        self.handleWidgetWithTSL(self.ui.script2Param4Spin, installation)
        self.handleWidgetWithTSL(self.ui.script2Param5Spin, installation)
        self.handleWidgetWithTSL(self.ui.script2Param6Edit, installation)

        self.handleWidgetWithTSL(self.ui.condition1Param1Spin, installation)
        self.handleWidgetWithTSL(self.ui.condition1Param2Spin, installation)
        self.handleWidgetWithTSL(self.ui.condition1Param3Spin, installation)
        self.handleWidgetWithTSL(self.ui.condition1Param4Spin, installation)
        self.handleWidgetWithTSL(self.ui.condition1Param5Spin, installation)
        self.handleWidgetWithTSL(self.ui.condition1Param6Edit, installation)
        self.handleWidgetWithTSL(self.ui.condition1NotCheckbox, installation)

        self.handleWidgetWithTSL(self.ui.condition2ResrefEdit, installation)
        self.handleWidgetWithTSL(self.ui.condition2Param1Spin, installation)
        self.handleWidgetWithTSL(self.ui.condition2Param2Spin, installation)
        self.handleWidgetWithTSL(self.ui.condition2Param3Spin, installation)
        self.handleWidgetWithTSL(self.ui.condition2Param4Spin, installation)
        self.handleWidgetWithTSL(self.ui.condition2Param5Spin, installation)
        self.handleWidgetWithTSL(self.ui.condition2Param6Edit, installation)
        self.handleWidgetWithTSL(self.ui.condition2NotCheckbox, installation)

        self.handleWidgetWithTSL(self.ui.emotionSelect, installation)
        self.handleWidgetWithTSL(self.ui.expressionSelect, installation)

        self.handleWidgetWithTSL(self.ui.nodeUnskippableCheckbox, installation)
        self.handleWidgetWithTSL(self.ui.nodeIdSpin, installation)
        self.handleWidgetWithTSL(self.ui.alienRaceNodeSpin, installation)
        self.handleWidgetWithTSL(self.ui.postProcSpin, installation)
        self.handleWidgetWithTSL(self.ui.logicSpin, installation)

        if installation.game().is_k1():
            required: list[str] = [HTInstallation.TwoDA_VIDEO_EFFECTS, HTInstallation.TwoDA_DIALOG_ANIMS]

        else:
            required = [
                HTInstallation.TwoDA_EMOTIONS,
                HTInstallation.TwoDA_EXPRESSIONS,
                HTInstallation.TwoDA_VIDEO_EFFECTS,
                HTInstallation.TwoDA_DIALOG_ANIMS,
            ]

        installation.htBatchCache2DA(required)

        all_installation_script_resnames = sorted(
            {res.resname() for res in self._installation if res.restype() is ResourceType.NCS},
            key=str.lower
        )
        if installation.tsl:
            self._setupTslInstallDefs(installation)
            self.populateComboBox(self.ui.script2ResrefEdit, all_installation_script_resnames)
            self.populateComboBox(self.ui.condition2ResrefEdit, all_installation_script_resnames)
        self.ui.cameraEffectSelect.clear()
        self.ui.cameraEffectSelect.addItem("[None]", None)
        self.all_voices = sorted({res.resname() for res in self._installation._streamwaves}, key=str.lower)
        all_streamsounds = sorted({res.resname() for res in self._installation._streamsounds}, key=str.lower)
        self.populateComboBox(self.ui.soundComboBox, all_streamsounds)
        self.populateComboBox(self.ui.script1ResrefEdit, all_installation_script_resnames)
        self.populateComboBox(self.ui.condition1ResrefEdit, all_installation_script_resnames)


        videoEffects: TwoDA | None = installation.htGetCache2DA(HTInstallation.TwoDA_VIDEO_EFFECTS)
        for i, label in enumerate(videoEffects.get_column("label")):
            self.ui.cameraEffectSelect.addItem(label.replace("VIDEO_EFFECT_", "").replace("_", " ").title(), i)

    def populateComboBox(self, comboBox: QComboBox | FilterComboBox, resnames: list[str]):
        comboBox.clear()
        if isinstance(comboBox, FilterComboBox):
            comboBox.populate_items(resnames)
        else:
            comboBox.addItems(resnames)

    def _setupTslInstallDefs(self, installation: HTInstallation):
        """Set up UI elements for TSL installation selection."""
        expressions: TwoDA = installation.htGetCache2DA(HTInstallation.TwoDA_EXPRESSIONS)
        emotions: TwoDA = installation.htGetCache2DA(HTInstallation.TwoDA_EMOTIONS)
        self.ui.emotionSelect.clear()
        self.ui.emotionSelect.setItems(emotions.get_column("label"))
        self.ui.emotionSelect.setContext(emotions, self._installation, HTInstallation.TwoDA_EMOTIONS)

        self.ui.expressionSelect.clear()
        self.ui.expressionSelect.setItems(expressions.get_column("label"))
        self.ui.expressionSelect.setContext(expressions, self._installation, HTInstallation.TwoDA_EXPRESSIONS)

    def editText(self, e: QMouseEvent | None = None):
        """Edits the text of the selected dialog node."""
        indexes: list[QModelIndex] = self.ui.dialogTree.selectionModel().selectedIndexes()

        if indexes:
            item: DLGStandardItem | None = self.model.itemFromIndex(indexes[0])
            link: DLGLink = item.link
            node: DLGNode | None = link.node

            dialog = LocalizedStringDialog(self, self._installation, node.text)
            print("<SDM> [editText scope] dialog: ", dialog)

            if dialog.exec_():
                node.text = dialog.locstring
                print("<SDM> [editText scope] node.text: ", node.text)

                item.setText(self._installation.string(node.text, "(continue)"))
                self._loadLocstring(self.ui.textEdit, node.text)

    def _loadLocstring(self, textbox: QPlainTextEdit | QTextEdit, locstring: LocalizedString):
        setText: Callable[[str], None] = textbox.setPlainText if isinstance(textbox, QPlainTextEdit) else textbox.setText

        className = "QLineEdit" if isinstance(textbox, QLineEdit) else "QPlainTextEdit"

        textbox.locstring = locstring  # type: ignore[reportAttributeAccessIssue]
        print("<SDM> [_loadLocstring scope] textbox.locstring: ", textbox.locstring)

        theme = GlobalSettings().selectedTheme
        print("<SDM> [_loadLocstring scope] theme: ", theme)

        print("<SDM> [_loadLocstring scope] locstring.stringref: ", locstring.stringref)
        if locstring.stringref == -1:
            text = str(locstring)
            print("<SDM> [_loadLocstring scope] text: ", text)

            setText(text if text != "-1" else "")
            # Check theme condition for setting stylesheet
            if theme == "Default (Light)":
                textbox.setStyleSheet(f"{textbox.styleSheet()} {className} {{background-color: white;}}")
            else:
                textbox.setStyleSheet(f"{textbox.styleSheet()} {className} {{background-color: white; color: black;}}")
        else:
            setText(self._installation.talktable().string(locstring.stringref))
            # Check theme condition for setting stylesheet
            if theme == "Default (Light)":
                textbox.setStyleSheet(f"{textbox.styleSheet()} {className} {{background-color: #fffded;}}")
            else:
                textbox.setStyleSheet(f"{textbox.styleSheet()} {className} {{background-color: #fffded; color: black;}}")

    def copyPath(self, node_or_link: DLGNode | DLGLink):
        """Copies the node path to the user's clipboard."""
        paths: list[PureWindowsPath] = self.core_dlg.find_paths(node_or_link)

        if not paths:
            return

        if len(paths) == 1:
            path = str(paths[0])
            print("<SDM> [copyPath scope] path: ", path)

        else:
            path = "\n".join(f"  {i + 1}. {p}" for i, p in enumerate(paths))

        QApplication.clipboard().setText(path)

    def _checkClipboardForJsonNode(self):
        clipboard_text = QApplication.clipboard().text()
        print("<SDM> [_checkClipboardForJsonNode scope] clipboard_text: ", clipboard_text)

        try:
            node_data = json.loads(clipboard_text)
            print("<SDM> [_checkClipboardForJsonNode scope] node_data: ", node_data)

            if isinstance(node_data, dict) and "type" in node_data:
                self._copy = DLGNode.from_dict(node_data)
                print("<SDM> [_checkClipboardForJsonNode scope] self._copy: ", self._copy)

        except json.JSONDecodeError:
            ...
        except Exception:
            self._logger.exception("Invalid JSON node on clipboard.")

    def expandToRoot(self, item: DLGStandardItem):
        parent: DLGStandardItem | None = item.parent()
        while parent is not None:
            self.ui.dialogTree.expand(parent.index())  # type: ignore[arg-type]
            parent = parent.parent()
            #print("<SDM> [expandToRoot scope] parent: ", parent)

    def jumpToOriginal(self, copiedItem: DLGStandardItem):
        """Jumps to the original node of a copied item."""
        sourceNode: DLGNode = copiedItem.link.node
        #print("<SDM> [jumpToOriginal scope] DLGNode: ", DLGNode)

        items: list[DLGStandardItem | None] = [self.model.item(i, 0) for i in range(self.model.rowCount())]

        while items:
            item: DLGStandardItem | None = items.pop()

            assert item is not None
            link: DLGLink | None = item.link

            if link is None:
                continue
            print("<SDM> [jumpToOriginal scope] link.node: ", link.node)
            if link.node == sourceNode:
                self.expandToRoot(item)
                self.ui.dialogTree.setCurrentIndex(item.index())
                break
            items.extend([item.child(i, 0) for i in range(item.rowCount())])
        else:
            self._logger.error(f"Failed to find original node for node {sourceNode!r}")

    def blinkWindow(self):
        self.setWindowOpacity(0.7)
        QTimer.singleShot(125, lambda: self.setWindowOpacity(1))

    def playSound(self, resname: str) -> bool:
        """Plays a sound resource."""
        if qtpy.API_NAME in ["PyQt5", "PySide2"]:
            from qtpy.QtMultimedia import QMediaContent

            def set_media(data: bytes | None) -> bool:
                if data:
                    self.buffer = QBuffer(self)
                    print("<SDM> [set_media scope] self.buffer: ", self.buffer)

                    self.buffer.setData(data)
                    self.buffer.open(QIODevice.OpenModeFlag.ReadOnly)
                    self.player.setMedia(QMediaContent(), self.buffer)
                    QTimer.singleShot(0, self.player.play)
                else:
                    self.blinkWindow()
                    return False
                return True

        elif qtpy.API_NAME in ["PyQt6", "PySide6"]:

            def set_media(data: bytes | None) -> bool:
                if data:
                    tempFile = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                    print("<SDM> [set_media scope] tempFile: ", tempFile)

                    tempFile.write(data)
                    tempFile.flush()
                    tempFile.seek(0)
                    tempFile.close()

                    audioOutput = QtMultimedia.QAudioOutput(self)
                    print("<SDM> [set_media scope] audioOutput: ", audioOutput)

                    self.player.setAudioOutput(audioOutput)
                    self.player.setSource(QUrl.fromLocalFile(tempFile.name))
                    audioOutput.setVolume(1)
                    self.player.play()
                    self.player.mediaStatusChanged.connect(lambda status, file_name=tempFile.name: self.removeTempAudioFile(status, file_name))

                else:
                    self.blinkWindow()
                    return False
                return True
        else:
            raise ValueError(f"Unsupported QT_API value: {qtpy.API_NAME}")

        self.player.stop()

        data: bytes | None = self._installation.sound(
            resname,
            [
                SearchLocation.VOICE,
                SearchLocation.SOUND,
                SearchLocation.OVERRIDE,
                SearchLocation.CHITIN,
            ],
        )
        return set_media(data)

    def removeTempAudioFile(
        self,
        status: QtMultimedia.QMediaPlayer.MediaStatus,
        filePathStr: str,
    ):
        print("<SDM> [removeTempAudioFile scope] status: ", status)
        if status == QtMultimedia.QMediaPlayer.MediaStatus.EndOfMedia:
            try:
                self.player.stop()
                QTimer.singleShot(33, lambda: remove_any(filePathStr))
            except OSError:
                self._logger.exception(f"Error removing temporary file {filePathStr}")

    def focusOnNode(self, link: DLGLink) -> DLGStandardItem:
        """Focuses the dialog tree on a specific link node."""
        if GlobalSettings().selectedTheme == "Default (Light)":
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
                return
            if self.ui.dialogTree.isExpanded(index):
                expanded_items.append(index)
            for i in range(self.model.rowCount(index)):
                saveItemsRecursively(index.child(i, 0))

        saveItemsRecursively(self.ui.dialogTree.rootIndex())
        return expanded_items

    def saveScrollPosition(self) -> int:
        return self.ui.dialogTree.verticalScrollBar().value()

    def saveSelectedItem(self) -> QModelIndex:
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
        print("<SDM> [updateTreeView scope] expanded_items: %s", expanded_items)

        scroll_position = self.saveScrollPosition()
        print("<SDM> [updateTreeView scope] scroll_position: %s", scroll_position)

        selected_index = self.saveSelectedItem()
        print("<SDM> [updateTreeView scope] selected_index: %s", selected_index)

        self.ui.dialogTree.reset()

        self.restoreExpandedItems(expanded_items)
        self.restoreScrollPosition(scroll_position)
        self.restoreSelectedItem(selected_index)

    def onTreeContextMenu(self, point: QPoint):
        """Displays context menu for tree items."""
        index: QModelIndex = self.ui.dialogTree.indexAt(point)
        item: DLGStandardItem | None = self.model.itemFromIndex(index)
        if item is not None:
            self._setContextMenuActions(item, point)
        elif not self._focused:
            menu = QMenu(self)
            print("<SDM> [onTreeContextMenu scope] menu: ", menu)

            menu.addAction("Add Entry").triggered.connect(self.model.addRootNode)
            menu.popup(self.ui.dialogTree.viewport().mapToGlobal(point))

    def setExpandRecursively(
        self,
        item: DLGStandardItem,
        seenNodes: set[DLGNode],
        *,
        expand: bool,
    ):
        """Recursively expand/collapse all children of the given item."""
        itemIndex: QModelIndex = item.index()
        if not itemIndex.isValid():
            return
        if not isinstance(item, DLGStandardItem):
            return  # future expand dummy
        link: DLGLink = item.link
        if link.node in seenNodes:
            return
        seenNodes.add(link.node)
        if expand:
            self.ui.dialogTree.expand(itemIndex)
        else:
            self.ui.dialogTree.collapse(itemIndex)
        for row in range(item.rowCount()):
            childItem: DLGStandardItem = item.child(row)
            if childItem is None:
                continue
            childIndex: QModelIndex = childItem.index()
            if childIndex is None:
                continue
            if not childIndex.isValid():
                continue
            self.setExpandRecursively(childItem, seenNodes, expand=expand)

    def _setContextMenuActions(self, item: DLGStandardItem, point: QPoint):
        """Sets context menu actions for a dialog tree item."""
        self._checkClipboardForJsonNode()
        link: DLGLink = item.link
        node: DLGNode = link.node
        node_type = "Entry" if isinstance(node, DLGEntry) else "Reply"

        menu = QMenu(self)
        focusAction = menu.addAction("Focus")

        focusAction.triggered.connect(lambda: self.focusOnNode(link))
        focusAction.setShortcut(QKeySequence(QtKey.Key_Enter | QtKey.Key_Return))
        if not node.links:
            focusAction.setEnabled(False)
        # Expand/Collapse All Children Action (non copies)
        menu.addSeparator()
        expandAllChildrenAction = menu.addAction("Expand All Children")
        expandAllChildrenAction.triggered.connect(lambda: self.setExpandRecursively(item, set(), expand=True))
        expandAllChildrenAction.setShortcut(QKeySequence(Qt.ShiftModifier | QtKey.Key_Return))
        collapseAllChildrenAction = menu.addAction("Collapse All Children")
        collapseAllChildrenAction.triggered.connect(lambda: self.setExpandRecursively(item, set(), expand=False))
        collapseAllChildrenAction.setShortcut(QKeySequence(Qt.ShiftModifier | Qt.AltModifier | Qt.Key_Return))
        menu.addSeparator()

        # Play Actions
        playMenu = menu.addMenu("Play")
        # Hook into the mousePressEvent of the QMenu
        playMenu.mousePressEvent = lambda event: (self._playNodeSound(node), QMenu.mousePressEvent(playMenu, event))
        playSoundAction = playMenu.addAction("Play Sound")
        playSoundAction.triggered.connect(lambda: self.playSound(str(node.sound)) and None or None)
        playVoiceAction = playMenu.addAction("Play Voice")
        playVoiceAction.triggered.connect(lambda: self.playSound(str(node.vo_resref)) and None or None)
        if not self.ui.soundComboBox.currentText().strip():
            playSoundAction.setEnabled(False)
        if not self.ui.voiceComboBox.currentText().strip():
            playVoiceAction.setEnabled(False)
        if not self.ui.soundComboBox.currentText().strip() and not self.ui.voiceComboBox.currentText().strip():
            playMenu.setEnabled(False)
        menu.addSeparator()

        # Copy Actions
        copyNodeAction = menu.addAction(f"Copy {node_type} to Clipboard")
        copyNodeAction.triggered.connect(lambda: self.model.copyNode(node))
        copyNodeAction.setShortcut(QKeySequence(Qt.ControlModifier | QtKey.Key_C))
        copyGffPathAction = menu.addAction("Copy GFF Path")
        copyGffPathAction.triggered.connect(lambda: self.copyPath(node))
        copyGffPathAction.setShortcut(QKeySequence(Qt.ControlModifier | Qt.AltModifier | QtKey.Key_C))
        menu.addSeparator()

        # Paste Actions
        pasteLinkAction = menu.addAction("Paste from Clipboard as Link")
        pasteNewAction = menu.addAction("Paste from Clipboard as Deep Copy")
        if isinstance(self._copy, DLGEntry) and isinstance(node, DLGReply):
            pasteLinkAction.setText("Paste Entry from Clipboard as Link")
            pasteNewAction.setText("Paste Entry from Clipboard as Deep Copy")
        elif isinstance(self._copy, DLGReply) and isinstance(node, DLGEntry):
            pasteLinkAction.setText("Paste Reply from Clipboard as Link")
            pasteNewAction.setText("Paste Reply from Clipboard as Deep Copy")
        else:
            pasteLinkAction.setEnabled(False)
            pasteNewAction.setEnabled(False)
        pasteLinkAction.setShortcut(QKeySequence(Qt.ControlModifier | QtKey.Key_V))
        pasteLinkAction.triggered.connect(lambda: self.model.pasteItem(item, asNewBranches=False))
        pasteNewAction.setShortcut(QKeySequence(Qt.ControlModifier | Qt.ShiftModifier | QtKey.Key_V))
        pasteNewAction.triggered.connect(lambda: self.model.pasteItem(item, asNewBranches=True))
        menu.addSeparator()

        # Add/Insert Actions
        addNodeAction = menu.addAction(f"Add {node_type}")
        addNodeAction.triggered.connect(lambda: self.model.addChildToItem(item))
        addNodeAction.setShortcut(QtKey.Key_Insert)
        menu.addSeparator()
        moveUpAction = menu.addAction("Move Up")
        moveUpAction.triggered.connect(lambda: self.model.shiftItem(item, -1))
        moveUpAction.setShortcut(QKeySequence(Qt.ShiftModifier | QtKey.Key_Up))
        moveDownAction = menu.addAction("Move Down")
        moveDownAction.triggered.connect(lambda: self.model.shiftItem(item, 1))
        moveDownAction.setShortcut(QKeySequence(Qt.ShiftModifier | QtKey.Key_Down))
        menu.addSeparator()

        # Remove/Delete Actions
        removeLinkAction = menu.addAction(f"Remove Simple Link to {node_type}")
        removeLinkAction.setShortcut(QtKey.Key_Delete)
        removeLinkAction.triggered.connect(lambda: self.model.removeLink(item))
        deleteItemAction = menu.addAction("Delete Selected")
        deleteItemAction.triggered.connect(lambda: self.model.deleteNode(item))
        deleteItemAction.setShortcut(QKeySequence(Qt.ShiftModifier | QtKey.Key_Delete))
        menu.addSeparator()

        # Create a custom styled action for "Delete ALL References"
        deleteAllReferencesAction = QWidgetAction(self)
        deleteAllReferencesWidget = QWidget()
        layout = QHBoxLayout()
        deleteAllReferencesLabel = QLabel(f"Delete ALL References to {node_type}")
        deleteAllReferencesLabel.setStyleSheet("""
            QLabel {
                color: red;
                font-weight: bold;
                padding: 4px;
                text-align: center;
            }
            QLabel:hover {
                background-color: #d3d3d3;
            }
        """)
        layout.addWidget(deleteAllReferencesLabel)
        layout.setContentsMargins(0, 0, 0, 0)
        deleteAllReferencesWidget.setLayout(layout)
        deleteAllReferencesAction.setDefaultWidget(deleteAllReferencesWidget)
        deleteAllReferencesAction.triggered.connect(lambda: self.model.deleteNodeEverywhere(node))
        deleteAllReferencesAction.setShortcut(QKeySequence(Qt.ControlModifier | Qt.ShiftModifier | Qt.Key_Delete))
        menu.addAction(deleteAllReferencesAction)

        menu.popup(self.ui.dialogTree.viewport().mapToGlobal(point))

    def _playNodeSound(self, node: DLGEntry | DLGReply):
        if str(node.sound).strip():
            self.playSound(str(node.sound).strip())
        elif str(node.vo_resref).strip():
            self.playSound(str(node.vo_resref).strip())
        else:
            self.blinkWindow()

    # region Events
    def focusOutEvent(self, e: QFocusEvent):
        self.keysDown.clear()  # Clears the set when focus is lost
        super().focusOutEvent(e)  # Ensures that the default handler is still executed
        # print("dlgedit.focusOutEvent: clearing all keys/buttons held down.")

    def keyPressEvent(
        self,
        event: QKeyEvent,
        *,
        isTreeViewCall: bool = False,
    ):
        if not isTreeViewCall:
            self.ui.dialogTree.keyPressEvent(event)
            return
        super().keyPressEvent(event)
        key = event.key()
        print("<SDM> [DLGEditor.keyPressEvent scope] key: %s", key)

        if event.isAutoRepeat() or key in self.keysDown:
            return  # Ignore auto-repeat events and prevent multiple executions on single key
        selectedItem: QModelIndex = self.ui.dialogTree.currentIndex()
        if not selectedItem.isValid():
            return

        item: DLGStandardItem | None = self.model.itemFromIndex(selectedItem)
        if item is None:
            if key == QtKey.Key_Insert:
                print("<SDM> [keyPressEvent scope insert1] key: %s", key)
                self.model.addRootNode()
            return
        print(
            f"DLGEditor.keyPressEvent: {getQtKeyString(key)} held: {'+'.join([getQtKeyString(k) for k in iter(self.keysDown)])}"
        )
        link: DLGLink = item.link
        node = item.link.node
        print("<SDM> [keyPressEvent scope] node: %s", node)
        if node is None:
            return

        if not self.keysDown:
            self.keysDown.add(key)
            if key in (QtKey.Key_Insert,):
                self.model.addChildToItem(item, node)
            elif key in (QtKey.Key_Delete, QtKey.Key_Backspace):
                self.model.removeLink(item)
            elif key in (QtKey.Key_Enter, QtKey.Key_Return):
                self.focusOnNode(link)
            elif key == QtKey.Key_Insert:
                print("<SDM> [keyPressEvent insert2 scope] key: %s", key)

                self.model.addChildToItem(item)
            elif key == QtKey.Key_P:
                print("<SDM> [keyPressEvent play scope] key: %s", key)

                if self.ui.soundComboBox.currentText().strip():
                    self.playSound(self.ui.soundComboBox.currentText().strip())
                elif self.ui.voiceComboBox.currentText().strip():
                    self.playSound(self.ui.voiceComboBox.currentText().strip())
                else:
                    self.blinkWindow()
            return

        self.keysDown.add(key)
        if {QtKey.Key_Shift, QtKey.Key_Up} == self.keysDown:
            newIndex = self.ui.dialogTree.indexAbove(selectedItem)
            print("<SDM> [keyPressEvent scope] newIndex: %s", newIndex)

            if newIndex.isValid():
                self.ui.dialogTree.setCurrentIndex(newIndex)
            self.model.shiftItem(item, -1, noSelectionUpdate=True)
        elif {QtKey.Key_Shift, QtKey.Key_Down} == self.keysDown:
            newIndex = self.ui.dialogTree.indexBelow(selectedItem)
            print("<SDM> [keyPressEvent scope] newIndex: %s", newIndex)

            if newIndex.isValid():
                self.ui.dialogTree.setCurrentIndex(newIndex)
            self.model.shiftItem(item, 1, noSelectionUpdate=True)
        elif QtKey.Key_Control in self.keysDown:
            if QtKey.Key_C in self.keysDown:
                if QtKey.Key_Alt in self.keysDown:
                    self.copyPath(node)
                else:
                    self.model.copyNode(node)
            elif QtKey.Key_Enter in self.keysDown or QtKey.Key_Return in self.keysDown:
                self.jumpToOriginal(item)
            elif QtKey.Key_V in self.keysDown:
                if QtKey.Key_Alt in self.keysDown:
                    self.model.pasteItem(item, asNewBranches=True)
                else:
                    self.model.pasteItem(item, asNewBranches=False)
            elif QtKey.Key_Delete in self.keysDown:
                if QtKey.Key_Shift in self.keysDown:
                    self.model.deleteNodeEverywhere(node)
                else:
                    self.model.deleteSelectedNode()

    def keyReleaseEvent(self, event: QKeyEvent):
        super().keyReleaseEvent(event)
        key = event.key()
        print("<SDM> [keyReleaseEvent scope] key: %s", key)

        if key in self.keysDown:
            self.keysDown.remove(key)
        print(f"DLGEditor.keyReleaseEvent: {getQtKeyString(key)}, held: {'+'.join([getQtKeyString(k) for k in iter(self.keysDown)])}")

    def mouseDoubleClickEvent(self, event: QMouseEvent | QModelIndex):
        if not self.ui.dialogTree.underMouse():
            return
        index: QModelIndex = event if isinstance(event, QModelIndex) else self.ui.dialogTree.indexAt(event.pos())
        if index.isValid():
            self.ui.dialogTree.expand(index)

    @staticmethod
    def setComboBoxText(comboBox: QComboBox, text: str, *, alwaysOnTop: bool = True):
        index = comboBox.findText(text)
        if alwaysOnTop:
            if index != -1:  # Text found
                comboBox.removeItem(index)
            newIndex = 1 if isinstance(comboBox, FilterComboBox) else 0
            comboBox.insertItem(newIndex, text)  # Insert at the top
            comboBox.setCurrentIndex(newIndex)  # Set the current index to the top item
        else:
            if index == -1:  # Text not found
                comboBox.addItem(text)
                index = comboBox.findText(text)
            comboBox.setCurrentIndex(index)

    def onSelectionChanged(self, selection: QItemSelection):
        """Updates UI fields based on selected dialog node."""
        if self.ui.dialogTree.draggedItem:
            print("dialogTree drag operation happening.")
            return
        self.acceptUpdates = False
        selectionIndices = selection.indexes()
        print("<SDM> [onSelectionChanged scope] selectionIndices: ", ",\n".join([self.model.itemFromIndex(index).text() for index in selectionIndices if self.model.itemFromIndex(index) is not None]))
        if selectionIndices:
            item: DLGStandardItem | None = self.model.itemFromIndex(selectionIndices[0])
            link: DLGLink = item.link
            node: DLGNode | None = link.node

            if isinstance(node, DLGEntry):
                self.ui.speakerEdit.setEnabled(True)
                self.ui.speakerEdit.setText(node.speaker)
            elif isinstance(node, DLGReply):
                self.ui.speakerEdit.setEnabled(False)
                self.ui.speakerEdit.setText("")

            self.ui.listenerEdit.setText(node.listener)
            self._loadLocstring(self.ui.textEdit, node.text)

            self.setComboBoxText(self.ui.script1ResrefEdit, str(node.script1))
            self.ui.script1Param1Spin.setValue(node.script1_param1)
            self.ui.script1Param2Spin.setValue(node.script1_param2)
            self.ui.script1Param3Spin.setValue(node.script1_param3)
            self.ui.script1Param4Spin.setValue(node.script1_param4)
            self.ui.script1Param5Spin.setValue(node.script1_param5)
            self.ui.script1Param6Edit.setText(node.script1_param6)

            self.setComboBoxText(self.ui.script2ResrefEdit, str(node.script2))
            self.ui.script2Param1Spin.setValue(node.script2_param1)
            self.ui.script2Param2Spin.setValue(node.script2_param2)
            self.ui.script2Param3Spin.setValue(node.script2_param3)
            self.ui.script2Param4Spin.setValue(node.script2_param4)
            self.ui.script2Param5Spin.setValue(node.script2_param5)
            self.ui.script2Param6Edit.setText(node.script2_param6)

            self.setComboBoxText(self.ui.condition1ResrefEdit, str(link.active1))
            self.ui.condition1Param1Spin.setValue(link.active1_param1)
            self.ui.condition1Param2Spin.setValue(link.active1_param2)
            self.ui.condition1Param3Spin.setValue(link.active1_param3)
            self.ui.condition1Param4Spin.setValue(link.active1_param4)
            self.ui.condition1Param5Spin.setValue(link.active1_param5)
            self.ui.condition1Param6Edit.setText(link.active1_param6)
            self.ui.condition1NotCheckbox.setChecked(link.active1_not)
            self.setComboBoxText(self.ui.condition2ResrefEdit, str(link.active2))
            self.ui.condition2Param1Spin.setValue(link.active2_param1)
            self.ui.condition2Param2Spin.setValue(link.active2_param2)
            self.ui.condition2Param3Spin.setValue(link.active2_param3)
            self.ui.condition2Param4Spin.setValue(link.active2_param4)
            self.ui.condition2Param5Spin.setValue(link.active2_param5)
            self.ui.condition2Param6Edit.setText(link.active2_param6)
            self.ui.condition2NotCheckbox.setChecked(link.active2_not)

            self.refreshAnimList()
            self.ui.emotionSelect.setCurrentIndex(node.emotion_id)
            self.ui.expressionSelect.setCurrentIndex(node.facial_id)
            self.setComboBoxText(self.ui.soundComboBox, str(node.sound))
            self.ui.soundCheckbox.setChecked(node.sound_exists)
            self.setComboBoxText(self.ui.voiceComboBox, str(node.vo_resref))

            self.ui.plotIndexSpin.setValue(node.plot_index)
            self.ui.plotXpSpin.setValue(node.plot_xp_percentage)
            self.ui.questEdit.setText(node.quest)
            self.ui.questEntrySpin.setValue(node.quest_entry or 0)

            self.ui.cameraIdSpin.setValue(-1 if node.camera_id is None else node.camera_id)

            self.ui.cameraAnimSpin.min_value = 1200
            self.ui.cameraAnimSpin.max_value = 65534
            self.ui.cameraAnimSpin.setValue(-1 if node.camera_anim is None else node.camera_anim)

            self.ui.cameraAngleSelect.setCurrentIndex(0 if node.camera_angle is None else node.camera_angle)
            self.ui.cameraEffectSelect.setCurrentIndex(0 if node.camera_effect is None else int(node.camera_effect) + 1)

            self.ui.nodeUnskippableCheckbox.setChecked(node.unskippable)
            self.ui.nodeIdSpin.setValue(node.node_id)
            self.ui.alienRaceNodeSpin.setValue(node.alien_race_node)
            self.ui.postProcSpin.setValue(node.post_proc_node)
            self.ui.delaySpin.setValue(node.delay)
            self.ui.logicSpin.setValue(link.logic)
            self.ui.waitFlagSpin.setValue(node.wait_flags)
            self.ui.fadeTypeSpin.setValue(node.fade_type)

            self.ui.commentsEdit.setPlainText(node.comment)
            self.model._updateCopies(link, item)
        self.acceptUpdates = True

    def onNodeUpdate(self):
        """Updates node properties based on UI selections."""
        selectedIndices = self.ui.dialogTree.selectedIndexes()
        if not selectedIndices:
            return
        if not self.acceptUpdates:
            return
        print("<SDM> [onNodeUpdate scope] selectedIndices: %s", selectedIndices)
        index: QModelIndex = selectedIndices[0]
        item: DLGStandardItem | None = self.model.itemFromIndex(index)
        link: DLGLink = item.link
        node: DLGNode | None = link.node
        node.listener = self.ui.listenerEdit.text()
        if isinstance(node, DLGEntry):
            node.speaker = self.ui.speakerEdit.text()
        node.script1 = ResRef(self.ui.script1ResrefEdit.currentText())
        node.script1_param1 = self.ui.script1Param1Spin.value()
        node.script1_param2 = self.ui.script1Param2Spin.value()
        node.script1_param3 = self.ui.script1Param3Spin.value()
        node.script1_param4 = self.ui.script1Param4Spin.value()
        node.script1_param5 = self.ui.script1Param5Spin.value()
        node.script1_param6 = self.ui.script1Param6Edit.text()
        node.script2 = ResRef(self.ui.script2ResrefEdit.currentText())
        node.script2_param1 = self.ui.script2Param1Spin.value()
        node.script2_param2 = self.ui.script2Param2Spin.value()
        node.script2_param3 = self.ui.script2Param3Spin.value()
        node.script2_param4 = self.ui.script2Param4Spin.value()
        node.script2_param5 = self.ui.script2Param5Spin.value()
        node.script2_param6 = self.ui.script2Param6Edit.text()

        link.active1 = ResRef(self.ui.condition1ResrefEdit.currentText())
        link.active1_param1 = self.ui.condition1Param1Spin.value()
        link.active1_param2 = self.ui.condition1Param2Spin.value()
        link.active1_param3 = self.ui.condition1Param3Spin.value()
        link.active1_param4 = self.ui.condition1Param4Spin.value()
        link.active1_param5 = self.ui.condition1Param5Spin.value()
        link.active1_param6 = self.ui.condition1Param6Edit.text()
        link.active1_not = self.ui.condition1NotCheckbox.isChecked()
        link.active2 = ResRef(self.ui.condition2ResrefEdit.currentText())
        link.active2_param1 = self.ui.condition2Param1Spin.value()
        link.active2_param2 = self.ui.condition2Param2Spin.value()
        link.active2_param3 = self.ui.condition2Param3Spin.value()
        link.active2_param4 = self.ui.condition2Param4Spin.value()
        link.active2_param5 = self.ui.condition2Param5Spin.value()
        link.active2_param6 = self.ui.condition2Param6Edit.text()
        link.active2_not = self.ui.condition2NotCheckbox.isChecked()
        link.logic = bool(self.ui.logicSpin.value())

        node.emotion_id = self.ui.emotionSelect.currentIndex()
        node.facial_id = self.ui.expressionSelect.currentIndex()
        node.sound = ResRef(self.ui.soundComboBox.currentText())
        node.sound_exists = self.ui.soundCheckbox.isChecked()
        node.vo_resref = ResRef(self.ui.voiceComboBox.currentText())

        node.plot_index = self.ui.plotIndexSpin.value()
        node.plot_xp_percentage = self.ui.plotXpSpin.value()
        node.quest = self.ui.questEdit.text()
        node.quest_entry = self.ui.questEntrySpin.value()

        node.camera_id = self.ui.cameraIdSpin.value()
        node.camera_anim = self.ui.cameraAnimSpin.value()
        node.camera_angle = self.ui.cameraAngleSelect.currentIndex()
        node.camera_effect = self.ui.cameraEffectSelect.currentData()
        if node.camera_id >= 0 and node.camera_angle == 0:
            self.ui.cameraAngleSelect.setCurrentIndex(6)
        elif node.camera_id == -1 and node.camera_angle == 7:
            self.ui.cameraAngleSelect.setCurrentIndex(0)

        node.unskippable = self.ui.nodeUnskippableCheckbox.isChecked()
        node.node_id = self.ui.nodeIdSpin.value()
        node.alien_race_node = self.ui.alienRaceNodeSpin.value()
        node.post_proc_node = self.ui.postProcSpin.value()
        node.delay = self.ui.delaySpin.value()
        node.wait_flags = self.ui.waitFlagSpin.value()
        node.fade_type = self.ui.fadeTypeSpin.value()
        node.comment = self.ui.commentsEdit.toPlainText()

    def onItemExpanded(self, index: QModelIndex):
        item = self.model.itemFromIndex(index)
        if item.hasChildren() and item.child(0, 0).data(_FUTURE_EXPAND_ROLE):
            self._fullyLoadFutureExpandItem(item, index)
        if item.parent() is None:
            self.setExpandRecursively(item, set(), expand=True)
        # Refresh the model by emitting dataChanged.
        index = self.model.indexFromItem(item)
        self.model.dataChanged.emit(index, index)

    def _fullyLoadFutureExpandItem(self, item: DLGStandardItem, sourceIndex: QModelIndex):
        item.removeRow(0)  # Remove the placeholder
        link: DLGLink | None = item.link
        node: DLGNode = link.node
        self.model.blockSignals(True)
        self.model.beginInsertRows(sourceIndex, 0, len(node.links)-1)
        for child_link in node.links:
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
        selected = self.ui.stuntList.selectedItems()
        print("<SDM> [onRemoveStuntClicked scope] selected: ", selected)

        if selected:
            item: QListWidgetItem = selected[0]
            print("<SDM> [onRemoveStuntClicked scope] selectedItem: ", item)

            stunt: DLGStunt = item.data(Qt.ItemDataRole.UserRole)
            print("<SDM> [onRemoveStuntClicked scope] DLGStunt: ", stunt)
            self.core_dlg.stunts.remove(stunt)
            self.refreshStuntList()

    def onEditStuntClicked(self):
        selected = self.ui.stuntList.selectedItems()
        print("<SDM> [onEditStuntClicked scope] selected: ", selected)

        if selected:
            item: QListWidgetItem = selected[0]
            print("<SDM> [onEditStuntClicked scope] QListWidgetItem: ", item)

            stunt: DLGStunt = item.data(Qt.ItemDataRole.UserRole)
            print("<SDM> [onEditStuntClicked scope] DLGStunt: ", stunt)

            dialog = CutsceneModelDialog(self, stunt)
            print("<SDM> [onEditStuntClicked scope] dialog: ", dialog)

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
        if self.ui.dialogTree.selectedIndexes():
            index: QModelIndex = self.ui.dialogTree.selectedIndexes()[0]
            print("<SDM> [onAddAnimClicked scope] QModelIndex: ", self.ui.dialogTree.getIdentifyingText(index))

            item: DLGStandardItem | None = self.model.itemFromIndex(index)
            node: DLGNode = cast(DLGLink, item.link).node

            dialog = EditAnimationDialog(self, self._installation)
            print("<SDM> [onAddAnimClicked scope] dialog: ", dialog)

            if dialog.exec_():
                node.animations.append(dialog.animation())
                self.refreshAnimList()

    def onRemoveAnimClicked(self):
        if self.ui.animsList.selectedItems():
            index: QModelIndex = self.ui.dialogTree.selectedIndexes()[0]
            print("<SDM> [onAddAnimClicked scope] QModelIndex: ", self.ui.dialogTree.getIdentifyingText(index))
            item: DLGStandardItem | None = self.model.itemFromIndex(index)
            node: DLGNode = cast(DLGLink, item.link).node

            animItem: QListWidgetItem = self.ui.animsList.selectedItems()[0]
            anim: DLGAnimation = animItem.data(Qt.ItemDataRole.UserRole)
            node.animations.remove(anim)
            self.refreshAnimList()

    def onEditAnimClicked(self):
        if self.ui.animsList.selectedItems():
            animItem: QListWidgetItem = self.ui.animsList.selectedItems()[0]
            anim: DLGAnimation = animItem.data(Qt.ItemDataRole.UserRole)
            dialog = EditAnimationDialog(self, self._installation, anim)
            print("<SDM> [onEditAnimClicked scope] dialog: ", dialog)

            if dialog.exec_():
                anim.animation_id = dialog.animation().animation_id
                print("<SDM> [onEditAnimClicked scope] anim.animation_id: ", anim.animation_id)

                anim.participant = dialog.animation().participant
                print("<SDM> [onEditAnimClicked scope] anim.participant: ", anim.participant)

                self.refreshAnimList()

    def refreshAnimList(self):
        """Refreshes the animations list."""
        self.ui.animsList.clear()

        if self.ui.dialogTree.selectedIndexes():
            index: QModelIndex = self.ui.dialogTree.selectedIndexes()[0]
            print("<SDM> [onAddAnimClicked scope] QModelIndex: ", self.ui.dialogTree.getIdentifyingText(index))
            item: DLGStandardItem | None = self.model.itemFromIndex(index)
            link: DLGLink = item.link
            node: DLGNode = link.node

            animations_2da: TwoDA = self._installation.htGetCache2DA(HTInstallation.TwoDA_DIALOG_ANIMS)
            for anim in node.animations:
                name: str = str(anim.animation_id)
                if animations_2da.get_height() > anim.animation_id:
                    name = animations_2da.get_cell(anim.animation_id, "name")
                    print("<SDM> [refreshAnimList scope] name: ", name)

                text: str = f"{name} ({anim.participant})"
                item = QListWidgetItem(text)
                print("<SDM> [refreshAnimList scope] item: ", item)

                item.setData(Qt.ItemDataRole.UserRole, anim)
                self.ui.animsList.addItem(item)

if __name__ == "__main__":
    app = QApplication([])
    window = QWidget()
    layout = QVBoxLayout(window)

    combo_box = FilterComboBox()
    combo_box.populate_items(["item1", "item2", "item3", "item4", "nm35aabast06005_", "nbtn14stun01003_", "nbtn14stun01004_", "nbtn14stun01005_", "nstn57c01001009_", "nstn57c01001014_", "nglobebeast06890"])
    layout.addWidget(combo_box)
    combo_box.set_button_delegate("Play", lambda x: x)

    window.setLayout(layout)
    window.show()
    app.exec_()
