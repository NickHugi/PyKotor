from __future__ import annotations

import json

from collections import deque
from enum import Enum
from typing import TYPE_CHECKING, Any, List, cast

import qtpy

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy.QtCore import QDataStream, QIODevice, QItemSelectionModel, QMimeData, QModelIndex, QPoint, QPointF, QRect, QTimer, Qt
from qtpy.QtGui import QBrush, QColor, QCursor, QDrag, QFont, QPainter, QPen, QPixmap, QRadialGradient, QStandardItemModel, QTextDocument
from qtpy.QtWidgets import QAbstractItemDelegate, QAbstractItemView, QStyledItemDelegate, QToolTip, QWidget

from pykotor.resource.generics.dlg import DLGEntry, DLGLink, DLGNode, DLGReply
from toolset.gui.editors.dlg.constants import QT_STANDARD_ITEM_FORMAT, _DLG_MIME_DATA_ROLE, _LINK_PARENT_NODE_PATH_ROLE, _MODEL_INSTANCE_ID_ROLE
from toolset.gui.editors.dlg.model import DLGStandardItem, DLGStandardItemModel
from utility.ui_libraries.qt.widgets.itemviews.html_delegate import HTMLDelegate
from utility.ui_libraries.qt.widgets.itemviews.treeview import RobustTreeView

if TYPE_CHECKING:
    from qtpy.QtCore import QAbstractItemModel, QByteArray, QMimeData
    from qtpy.QtGui import QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent, QHoverEvent, QKeyEvent, QMouseEvent, QPaintEvent
    from qtpy.QtWidgets import QAbstractItemDelegate, QStyleOptionViewItem, QStyledItemDelegate, QWidget
    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from pykotor.resource.generics.dlg import DLGNode
    from toolset.gui.editors.dlg.editor import DLGEditor


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
            return cls(
                QModelIndex(),
                -1,
                DropPosition.INVALID,
                QRect(),
            )

        curIndex: QModelIndex = view.indexAt(pos)
        if not curIndex.isValid() or curIndex.row() == -1:
            return cls(
                QModelIndex(),
                -1,
                DropPosition.INVALID,
                QRect(),
            )

        rect: QRect = view.visualRect(curIndex)
        item_height: int = rect.height()
        leniency_height: float = item_height * leniency
        upper_threshold: float = rect.top() + leniency_height
        lower_threshold: float = rect.bottom() - leniency_height

        if pos.y() <= upper_threshold:
            # Adjust for top edge of the index
            indicator_rect: QRect = QRect(rect.topLeft(), rect.topRight())
            return cls(curIndex.parent(), max(curIndex.row(), 0), DropPosition.ABOVE, indicator_rect)
        if pos.y() >= lower_threshold:
            # Adjust for bottom edge of the index
            indicator_rect: QRect = QRect(rect.bottomLeft(), rect.bottomRight())
            return cls(curIndex.parent(), curIndex.row() + 1, DropPosition.BELOW, indicator_rect)

        return cls(curIndex, curIndex.row(), DropPosition.ON_TOP_OF, rect)

    def is_valid_drop(self, dragged_link: DLGLink, view: DLGTreeView) -> bool:
        if self.position is DropPosition.INVALID or self.row == -1:
            return False

        view_model: DLGStandardItemModel | None = view.model()
        assert view_model is not None, "view_model cannot be None"

        if self.parent_index.isValid():
            root_item_index: QModelIndex | None = None
            parent_item: DLGStandardItem | None = view_model.itemFromIndex(self.parent_index)
        else:
            root_item_index = view_model.index(self.row, 0)
            if not root_item_index.isValid():
                if self.position is DropPosition.BELOW:
                    above_test_index: QModelIndex = view_model.index(min(0, self.row - 1), 0)
                    if above_test_index.isValid():
                        root_item_index = above_test_index
                else:
                    return False
            parent_item: DLGStandardItem | None = view_model.itemFromIndex(root_item_index)
        dragged_node: DLGNode = dragged_link.node
        assert parent_item is not None
        assert parent_item.link is not None
        node_types_match: bool = view.both_nodes_same_type(dragged_node, parent_item.link.node)
        if self.position is DropPosition.ON_TOP_OF:
            node_types_match = not node_types_match

        return ((self.position is DropPosition.ON_TOP_OF) == node_types_match) != (root_item_index is not None)


class DLGTreeView(RobustTreeView):
    def __init__(self, parent: QWidget | None = None):
        self.override_drop_in_view: bool = True  # set to False to use the new logic (not recommended - untested)
        self.editor: DLGEditor | None = None
        self.drop_indicator_rect: QRect = QRect()
        self.num_links: int = 0
        self.num_unique_nodes: int = 0
        self.dragged_item: DLGStandardItem | None = None
        self.dragged_link: DLGLink | None = None
        self.drop_target: DropTarget | None = None
        self.start_pos: QPoint = QPoint()
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
        self.setMouseTracking(True)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        our_viewport: QWidget | None = self.viewport()
        assert our_viewport is not None
        our_viewport.setAcceptDrops(True)
        self.setDropIndicatorShown(False)  # We have our own.
        self.setDefaultDropAction(Qt.DropAction.MoveAction)

    def set_text_size(self, size: int):
        super().set_text_size(size)

    def emit_layout_changed(self):  # sourcery skip: remove-unreachable-code
        super().emit_layout_changed()

    def model(self) -> DLGStandardItemModel | None:
        model: QAbstractItemModel | None = super().model()
        if model is None:
            return None
        assert isinstance(model, DLGStandardItemModel), f"model was {model} of type {model.__class__.__name__}, expected DLGStandardItemModel"
        return model

    def paintEvent(
        self,
        event: QPaintEvent,
    ):
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

    def keyPressEvent(
        self,
        event: QKeyEvent,
    ):
        assert self.editor is not None
        self.editor.keyPressEvent(event, is_tree_view_call=True)
        super().keyPressEvent(event)

    def mousePressEvent(
        self,
        event: QMouseEvent,
    ):
        if event.button() == Qt.MouseButton.LeftButton and self.start_pos.isNull():
            self.start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(
        self,
        event: QMouseEvent,
    ):
        super().mouseMoveEvent(event)
        index: QModelIndex = self.indexAt(event.pos())
        if not index.isValid():
            return

        # FIXME(th3w1zard1): the below code only works with QTreeView. viewOptions() for qt5, styleOptionForIndex is qt6.  # noqa: TD003
        # We know the above is true, but what we don't know is the QListView equivalent to get a QStyleOptionViewItem? Replace these when that's determined.
        option: QStyleOptionViewItem = self.viewOptions() if qtpy.QT5 else self.styleOptionForIndex(index)  # pyright: ignore[reportAttributeAccessIssue]
        option.rect = self.visualRect(index)

        delegate: HTMLDelegate | QStyledItemDelegate | QAbstractItemDelegate = self.itemDelegate(index)
        if isinstance(delegate, HTMLDelegate) and delegate.handleIconTooltips(event, option, index):
            return

    # region Tree Drag&Drop
    def create_drag_pixmap(
        self,
        dragged_item: DLGStandardItem,
    ) -> QPixmap:
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
            link_list_display: Literal["EntriesList", "RepliesList", "StartingList"] = "EntriesList" if isinstance(dragged_item.link.node, DLGEntry) else "RepliesList"
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
        gradient: QRadialGradient = QRadialGradient(QPointF(center), radius) if qtpy.QT5 else QRadialGradient(QPointF(center), radius, QPointF(center))
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

    def calculate_links_and_nodes(
        self,
        root_node: DLGNode,
    ) -> tuple[int, int]:
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
        return self.num_links, self.num_unique_nodes

    def perform_drag(self):
        assert self.dragged_item is not None
        dragged_index: QModelIndex = self.dragged_item.index()
        drag = QDrag(self)
        model: DLGStandardItemModel | None = self.model()
        assert model is not None
        drag.setMimeData(model.mimeData([dragged_index]))
        pixmap: QPixmap = self.create_drag_pixmap(self.dragged_item)
        drag.setPixmap(pixmap)
        item_top_left_global: QPoint = self.mapToGlobal(self.visualRect(dragged_index).topLeft())
        drag.setHotSpot(QPoint(pixmap.width() // 2, QCursor.pos().y() - item_top_left_global.y()))
        drag.exec(model.supportedDragActions())

    def prepare_drag(
        self,
        index: QModelIndex | None = None,
        event: QDragEnterEvent | QDragMoveEvent | QDropEvent | None = None,
    ) -> bool:
        if self.dragged_item is not None:
            return True

        if event:
            return self._handle_drag_prepare_in_event(event)
        index = self.currentIndex() if index is None else index
        model: DLGStandardItemModel | None = self.model()
        assert isinstance(model, QStandardItemModel), f"model was not QStandardItemModel, was instead {model.__class__.__name__}: {model}"
        dragged_item: DLGStandardItem | None = model.itemFromIndex(index)
        assert isinstance(
            dragged_item, DLGStandardItem
        ), f"model.itemFromIndex({index}(row={index.row()}, col={index.column()}) did not return a DLGStandardItem, was instead {self.dragged_item.__class__.__name__}: {self.dragged_item}"  # noqa: E501
        self.dragged_item = dragged_item
        if not self.dragged_item or getattr(self.dragged_item, "link", None) is None:
            return False

        assert self.dragged_item is not None
        assert self.dragged_item.link is not None
        assert self.dragged_item.link.node is not None
        self.calculate_links_and_nodes(self.dragged_item.link.node)
        return True

    def _handle_drag_prepare_in_event(
        self,
        event: QDragEnterEvent | QDragMoveEvent | QDropEvent,
    ) -> bool:
        mime_data: QMimeData | None = event.mimeData()
        assert mime_data is not None, "mimedata is None"
        if not mime_data.hasFormat(QT_STANDARD_ITEM_FORMAT):
            return False
        model: DLGStandardItemModel | None = self.model()
        assert model is not None
        if id(event.source()) == id(model):
            return True
        item_data: List[dict[Literal["row", "column", "roles"], Any]] = self.parse_mime_data(mime_data)
        if item_data[0]["roles"][_MODEL_INSTANCE_ID_ROLE] != id(model):
            return True
        deserialized_listwidget_link: DLGLink = DLGLink.from_dict(json.loads(item_data[0]["roles"][_DLG_MIME_DATA_ROLE]))
        temp_item: DLGStandardItem = DLGStandardItem(link=deserialized_listwidget_link)
        # FIXME(th3w1zard1): the above QStandardItem is somehow deleted by qt BEFORE the next line?  # noqa: TD003
        model.update_item_display_text(temp_item)
        self.dragged_item = model.link_to_items.setdefault(deserialized_listwidget_link, [temp_item])[0]
        assert self.dragged_item is not None
        assert self.dragged_item.link is not None
        self.calculate_links_and_nodes(self.dragged_item.link.node)
        return True

    def startDrag(
        self,
        supportedActions: Qt.DropAction,
    ):
        if not self.prepare_drag():
            self.reset_drag_state()
            return
        mode = 2
        if mode == 1:
            super().startDrag(supportedActions)
        elif mode == 2:  # noqa: PLR2004
            self.perform_drag()
        self.reset_drag_state()

    def dragEnterEvent(
        self,
        event: QDragEnterEvent,
    ):
        mime_data: QMimeData | None = event.mimeData()
        assert mime_data is not None, "mime_data is None"
        if not mime_data.hasFormat(QT_STANDARD_ITEM_FORMAT):
            self.set_invalid_drag_drop(event)
            return
        if not self.dragged_item and not self.prepare_drag(event=event):
            self.set_invalid_drag_drop(event)
            self.reset_drag_state()
            return
        self.set_valid_drag_drop(event)

    def dragMoveEvent(
        self,
        event: QDragMoveEvent,
    ):
        mime_data = event.mimeData()
        assert mime_data is not None, "mime_data is None"
        if not mime_data.hasFormat(QT_STANDARD_ITEM_FORMAT):
            self.set_invalid_drag_drop(event)
            super().dragMoveEvent(event)
            return

        if self.dragged_item is not None:
            assert self.dragged_item.link is not None
            self.dragged_link = self.dragged_item.link
        elif self.dragged_link is None:
            if not self.prepare_drag(event=event):
                self.set_invalid_drag_drop(event)
                super().dragMoveEvent(event)
                return
            mime_data: QMimeData | None = event.mimeData()
            assert mime_data is not None, "mime_data is None"
            self.dragged_link = self.get_dragged_link_from_mime_data(mime_data)
            if self.dragged_link is None:
                self.set_invalid_drag_drop(event)
                super().dragMoveEvent(event)
                return

        delegate: HTMLDelegate | QStyledItemDelegate | QAbstractItemDelegate = self.itemDelegate()
        assert isinstance(delegate, HTMLDelegate), f"`delegate = self.itemDelegate()` {delegate.__class__.__name__}: {delegate}"
        if self.drop_target is not None:
            delegate.nudged_model_indexes.clear()

        pos: QPoint | QPointF = event.pos() if qtpy.QT5 else event.position()  # pyright: ignore[reportAttributeAccessIssue]
        if isinstance(pos, QPointF):
            pos = pos.toPoint()
        self.drop_target = DropTarget.determine_drop_target(self, pos)
        self.drop_indicator_rect = self.drop_target.indicator_rect
        if not self.drop_target.is_valid_drop(self.dragged_link, self):
            self.set_invalid_drag_drop(event)
            super().dragMoveEvent(event)
            self.unsetCursor()
            return
        model: DLGStandardItemModel | None = self.model()
        assert model is not None, f"model = self.model() {model.__class__.__name__}: {model}"
        above_index: QModelIndex = model.index(self.drop_target.row - 1, 0, self.drop_target.parent_index)
        hover_over_index: QModelIndex = model.index(self.drop_target.row, 0, self.drop_target.parent_index)
        if (
            self.drop_target.position in (DropPosition.ABOVE, DropPosition.BELOW)
            and self.dragged_item is not None
            and (self.dragged_item.isDeleted() or hover_over_index is not self.dragged_item.index())
        ):
            delegate.nudge_item(hover_over_index, 0, int(delegate.text_size / 2))
            delegate.nudge_item(above_index, 0, int(-delegate.text_size / 2))

        self.set_valid_drag_drop(event)
        super().dragMoveEvent(event)

    def dragLeaveEvent(
        self,
        event: QDragLeaveEvent,
    ):
        delegate: HTMLDelegate | QStyledItemDelegate | QAbstractItemDelegate = self.itemDelegate()
        assert isinstance(delegate, HTMLDelegate), f"`delegate = self.itemDelegate()` {delegate.__class__.__name__}: {delegate}"
        delegate.nudged_model_indexes.clear()
        self.unsetCursor()

    def dropEvent(
        self,
        event: QDropEvent,
    ):  # noqa: C901, PLR0912, PLR0911
        if self.override_drop_in_view:
            # Always set invalid so qt won't try to handle it past this function.
            self.set_invalid_drag_drop(event)
        mime_data = event.mimeData()
        assert mime_data is not None, "mime_data is None"
        if not mime_data.hasFormat(QT_STANDARD_ITEM_FORMAT):
            self.reset_drag_state()
            return
        if self.drop_target is None:
            self.reset_drag_state()
            return

        delegate: HTMLDelegate | QStyledItemDelegate | QAbstractItemDelegate = self.itemDelegate()
        assert isinstance(delegate, HTMLDelegate), f"`delegate = self.itemDelegate()` {delegate.__class__.__name__}: {delegate}"
        delegate.nudged_model_indexes.clear()
        model: DLGStandardItemModel | None = self.model()
        assert model is not None
        if self.drop_target.parent_index.isValid():
            drop_parent: DLGStandardItem | None = model.itemFromIndex(self.drop_target.parent_index)
        else:
            drop_parent = None

        if not self.is_item_from_current_model(event):
            if self.override_drop_in_view:
                mime_data: QMimeData | None = event.mimeData()
                assert mime_data is not None, "mime_data is None"
                dragged_link: DLGLink | None = self.get_dragged_link_from_mime_data(mime_data) if self.dragged_link is None else self.dragged_link
                if dragged_link is not None:
                    if not self.drop_target.is_valid_drop(dragged_link, self):
                        self.reset_drag_state()
                        return
                    new_index: int = self.drop_target.row
                    if self.drop_target.position is DropPosition.ON_TOP_OF:
                        new_index = 0
                    model.paste_item(drop_parent, dragged_link, row=new_index, as_new_branches=False)
                    super().dropEvent(event)
            super().dropEvent(event)
            self.reset_drag_state()
            return

        if self.dragged_item is None:
            self.reset_drag_state()
            return

        if self.dragged_item.link is None:
            self.reset_drag_state()
            return

        if not self.drop_target.is_valid_drop(self.dragged_item.link, self):
            self.reset_drag_state()
            return
        self.set_invalid_drag_drop(event)
        new_index: int = self.drop_target.row
        if self.drop_target.position is DropPosition.ON_TOP_OF:
            new_index = 0
        model.move_item_to_index(self.dragged_item, new_index, drop_parent)
        super().dropEvent(event)
        parent_index_of_drop: QModelIndex = self.drop_target.parent_index
        dropped_at_row: int = self.drop_target.row
        if self.drop_target.position is DropPosition.BELOW:
            dropped_at_row = min(dropped_at_row - 1, 0)
        self.reset_drag_state()
        self.setAutoScroll(False)
        # self.setSelectionOnDrop(droppedAtRow, parentIndexOfDrop)
        QTimer.singleShot(0, lambda: self.set_selection_on_drop(dropped_at_row, parent_index_of_drop))

    def set_selection_on_drop(
        self,
        row: int,
        parent_index: QModelIndex,
    ):
        self.clearSelection()
        model: DLGStandardItemModel | None = self.model()
        assert model is not None
        if not parent_index.isValid():
            drop_index: QModelIndex = model.index(row, 0)
        else:
            drop_index = model.index(row, 0, parent_index)
        if drop_index is None or not drop_index.isValid():
            return
        selection_model: QItemSelectionModel | None = self.selectionModel()
        assert selection_model is not None
        selection_model.setCurrentIndex(
            drop_index,
            QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows,
        )
        viewport: QWidget | None = self.viewport()
        assert viewport is not None
        viewport.update()
        self.setState(QAbstractItemView.State.DragSelectingState)
        QTimer.singleShot(0, lambda: self.setState(QAbstractItemView.State.NoState))
        QTimer.singleShot(0, lambda: viewport.update())

    def get_dragged_link_from_mime_data(
        self,
        mime_data: QMimeData,
    ) -> DLGLink | None:
        try:
            return DLGLink.from_dict(json.loads(self.parse_mime_data(mime_data)[0]["roles"][_DLG_MIME_DATA_ROLE]))
        except Exception:  # noqa: BLE001
            RobustLogger().exception("Failed to deserialize mime data node.")
        return None

    def is_item_from_current_model(
        self,
        event: QDropEvent,
    ) -> bool:
        if not isinstance(event.source(), DLGTreeView):
            return False

        cur_model_id: int = id(self.model())
        mime_data: QMimeData | None = event.mimeData()
        assert mime_data is not None
        parsed_mime_data: list[dict[Literal["row", "column", "roles"], Any]] = self.parse_mime_data(mime_data)
        mime_data_model_id_raw: Any = parsed_mime_data[0]["roles"][_MODEL_INSTANCE_ID_ROLE]
        model_id_from_mime_data: int = int(mime_data_model_id_raw)
        return model_id_from_mime_data == cur_model_id

    @staticmethod
    def parse_mime_data(
        mime_data: QMimeData,
    ) -> list[dict[Literal["row", "column", "roles"], Any]]:
        items: list[dict[Literal["row", "column", "roles"], Any]] = []
        if not mime_data.hasFormat(QT_STANDARD_ITEM_FORMAT):
            return items

        encoded_data: QByteArray = mime_data.data(QT_STANDARD_ITEM_FORMAT)
        stream = QDataStream(encoded_data, QIODevice.OpenModeFlag.ReadOnly)
        while not stream.atEnd():
            item_data: dict[Literal["row", "column", "roles"], Any] = {
                "row": stream.readInt32(),
                "column": stream.readInt32(),
            }
            roles: dict[int, Any] = {}
            for _ in range(stream.readInt32()):
                role: int = stream.readInt32()
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
    def both_nodes_same_type(
        dragged_node: DLGNode,
        target_node: DLGNode,
    ) -> bool:
        return (
            isinstance(dragged_node, DLGReply)  # pyright: ignore[reportOptionalMemberAccess]
            and isinstance(target_node, DLGReply)
        ) or (
            isinstance(dragged_node, DLGEntry)
            and isinstance(target_node, DLGEntry)
        )

    def reset_drag_state(self):
        self.start_pos = QPoint()
        self.dragged_item = None
        self.dragged_link = None
        self.drop_indicator_rect = QRect()
        self.drop_target = None
        self.unsetCursor()
        view_port: QWidget | None = self.viewport()
        assert view_port is not None
        view_port.update()

    def set_invalid_drag_drop(
        self,
        event: QDropEvent | QDragEnterEvent | QDragMoveEvent,
    ):
        event.acceptProposedAction()
        event.setDropAction(Qt.DropAction.IgnoreAction)
        self.setCursor(Qt.CursorShape.ForbiddenCursor)
        view_port: QWidget | None = self.viewport()
        assert view_port is not None
        view_port.update()
        QTimer.singleShot(0, lambda *args: self.setDragEnabled(True))

    def set_valid_drag_drop(
        self,
        event: QDropEvent | QDragEnterEvent | QDragMoveEvent,
    ):
        event.accept()
        event.setDropAction(
            Qt.DropAction.MoveAction if self.is_item_from_current_model(event) else Qt.DropAction.CopyAction
        )  # DropAction's are unused currently: the view is handling the drop.
        self.setCursor(Qt.CursorShape.ArrowCursor)


def install_immediate_tooltip(widget: QWidget, tooltip_text: str):
    widget.setToolTip(tooltip_text)
    widget.setMouseTracking(True)
    widget.event = lambda event: QToolTip.showText(cast("QHoverEvent", event).pos(), widget.toolTip(), widget)  # type: ignore[method-assign]
