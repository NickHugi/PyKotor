from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Optional, cast

from qtpy.QtCore import QEasingCurve, QObject, QPointF, QPropertyAnimation, QRectF, QSizeF, Qt
from qtpy.QtGui import QBrush, QColor, QCursor, QKeySequence, QPainter, QPainterPath, QPalette, QPen
from qtpy.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QMenu,
    QShortcut,  # pyright: ignore[reportPrivateImportUsage]
)

from pykotor.resource.generics.dlg import DLGEntry, DLGLink, DLGNode
from toolset.gui.editors.dlg.editor import DLGEditor

if TYPE_CHECKING:
    from qtpy.QtGui import QAction, QWheelEvent
    from qtpy.QtWidgets import QGraphicsSceneContextMenuEvent, QGraphicsSceneHoverEvent, QGraphicsSceneMouseEvent, QStyleOptionGraphicsItem, QWidget
    from typing_extensions import Self  # pyright: ignore[reportMissingModuleSource]

    from pykotor.resource.generics.dlg import DLGLink, DLGNode
    from toolset.gui.editors.dlg.editor import DLGEditor


@dataclass
class NodeCopyData:
    """Data structure for storing node copy data."""

    title: str
    width: float
    height: float
    pos: QPointF
    dlg_node: DLGNode | None


class NodePort:
    def __init__(
        self,
        parent_node: Node,
        *,
        is_input: bool = True,
        label: str = "",
    ):
        self.parent_node: Node = parent_node
        self.is_input: bool = is_input
        self.label: str = label
        self.connections: list[Connection] = []
        self.pos: QPointF = QPointF()

    def get_scene_pos(
        self,
    ) -> QPointF:
        return self.parent_node.mapToScene(self.pos)


class Connection(QGraphicsPathItem):
    def __init__(
        self,
        start_port: NodePort,
        end_port: NodePort,
    ):
        super().__init__()
        self.start_port: NodePort = start_port
        self.end_port: NodePort = end_port
        assert isinstance(self, QObject)
        self.animation: QPropertyAnimation = QPropertyAnimation(self, b"path")
        self.animation.setDuration(200)

        # Visual style
        q_app_style: QApplication | None = cast(Optional[QApplication], QApplication.style())
        if q_app_style is None:
            raise RuntimeError("QApplication style is not available?")

        self.setPen(
            QPen(
                q_app_style.palette().color(QPalette.ColorRole.Text),
                2,
                Qt.PenStyle.SolidLine,
            )
        )
        self.setAcceptHoverEvents(True)

    def update_position(
        self,
    ):
        start_pos: QPointF = self.start_port.get_scene_pos()
        end_pos: QPointF = self.end_port.get_scene_pos()

        path: QPainterPath = QPainterPath()
        path.moveTo(start_pos)

        dx: float = end_pos.x() - start_pos.x()
        ctrl1: QPointF = QPointF(start_pos.x() + dx * 0.5, start_pos.y())
        ctrl2: QPointF = QPointF(end_pos.x() - dx * 0.5, end_pos.y())

        path.cubicTo(ctrl1, ctrl2, end_pos)
        self.setPath(path)

    def hoverEnterEvent(
        self,
        event: QGraphicsSceneHoverEvent,
    ):
        q_app_style: QApplication | None = cast(Optional[QApplication], QApplication.style())
        if q_app_style is None:
            raise RuntimeError("QApplication style is not available?")
        self.setPen(QPen(q_app_style.palette().color(QPalette.ColorRole.Highlight), 3, Qt.PenStyle.SolidLine))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(
        self,
        event: QGraphicsSceneHoverEvent,
    ):
        q_app_style: QApplication | None = cast(Optional[QApplication], QApplication.style())
        if q_app_style is None:
            raise RuntimeError("QApplication style is not available?")
        self.setPen(QPen(q_app_style.palette().color(QPalette.ColorRole.Text), 2, Qt.PenStyle.SolidLine))
        super().hoverLeaveEvent(event)

    def animate_path_update(
        self,
    ):
        """Animate connection path changes."""
        start_pos: QPointF = self.start_port.get_scene_pos()
        end_pos: QPointF = self.end_port.get_scene_pos()

        # Create path for animation
        path: QPainterPath = QPainterPath()
        path.moveTo(start_pos)

        # Calculate control points
        dx: float = end_pos.x() - start_pos.x()
        ctrl1: QPointF = QPointF(start_pos.x() + dx * 0.5, start_pos.y())
        ctrl2: QPointF = QPointF(end_pos.x() - dx * 0.5, end_pos.y())

        path.cubicTo(ctrl1, ctrl2, end_pos)

        # Animate to new path
        self.animation.setStartValue(self.path())
        self.animation.setEndValue(path)
        self.animation.start()


class Node(QGraphicsRectItem):
    def __init__(
        self,
        title: str,
        width: float = 200,
        height: float = 120,
        dlg_node: DLGNode | None = None,
    ):
        super().__init__()
        self.dlg_node: DLGNode | None = dlg_node
        self.title: str = title
        self.input_ports: list[NodePort] = []
        self.output_ports: list[NodePort] = []
        self.is_selected: bool = False

        # Visual setup
        self.setRect(0, 0, width, height)
        graphics_scene: QGraphicsScene | None = self.scene()
        if graphics_scene is None:
            raise RuntimeError("Node must be added to a scene before setting visual properties")

        # Get palette from view
        palette: QPalette = graphics_scene.views()[0].palette()

        # Use palette colors instead of hardcoded values
        self.bg_color: QColor = palette.color(QPalette.ColorRole.Base)
        self.header_color: QColor = palette.color(QPalette.ColorRole.Button)
        self.border_color: QColor = palette.color(QPalette.ColorRole.Text)
        self.text_color: QColor = palette.color(QPalette.ColorRole.Text)

        # Create background path with rounded corners
        self.bg_path: QPainterPath = QPainterPath()
        self.bg_path.addRoundedRect(self.rect(), 10, 10)

        # Create header path
        self.header_path: QPainterPath = QPainterPath()
        header_rect: QRectF = QRectF(0, 0, width, 30)
        self.header_path.addRoundedRect(header_rect, 10, 10)

        # Set brushes and pens
        self.bg_brush: QBrush = QBrush(self.bg_color)
        self.header_brush: QBrush = QBrush(self.header_color)
        self.setPen(QPen(self.border_color, 1))

        # Set flags
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)

        # Add title
        self.title_item: QGraphicsTextItem = QGraphicsTextItem(self)
        self.title_item.setDefaultTextColor(self.text_color)
        self.title_item.setPlainText(title)
        self.title_item.setPos(10, 5)

        # Add new attributes
        self.resize_handle_size: int = 10
        self.is_resizing: bool = False
        self.resize_edge: Literal["topleft", "topright", "bottomleft", "bottomright", "left", "right", "top", "bottom"] | None = None
        self.min_size: QSizeF = QSizeF(100, 60)
        assert isinstance(self, QObject)
        self.animation: QPropertyAnimation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(200)

        # Add resize cursors
        self.edge_cursors: dict[Literal["topleft", "topright", "bottomleft", "bottomright", "left", "right", "top", "bottom"], Qt.CursorShape] = {
            "top": Qt.CursorShape.SizeVerCursor,
            "bottom": Qt.CursorShape.SizeVerCursor,
            "left": Qt.CursorShape.SizeHorCursor,
            "right": Qt.CursorShape.SizeHorCursor,
            "topright": Qt.CursorShape.SizeBDiagCursor,
            "bottomleft": Qt.CursorShape.SizeBDiagCursor,
            "topleft": Qt.CursorShape.SizeFDiagCursor,
            "bottomright": Qt.CursorShape.SizeFDiagCursor,
        }

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ):
        graphics_scene: QGraphicsScene | None = self.scene()
        if graphics_scene is None:
            raise RuntimeError("Node must be added to a scene before painting")

        palette: QPalette = graphics_scene.views()[0].palette()

        # Draw background
        painter.fillPath(self.bg_path, QBrush(palette.color(QPalette.ColorRole.Base)))

        # Draw header
        painter.fillPath(self.header_path, QBrush(palette.color(QPalette.ColorRole.Button)))

        # Draw outline
        if self.isSelected():
            painter.setPen(QPen(palette.color(QPalette.ColorRole.Highlight), 2))
        else:
            painter.setPen(QPen(palette.color(QPalette.ColorRole.Mid), 1))
        painter.drawPath(self.bg_path)

        # Draw ports
        painter.setPen(QPen(palette.color(QPalette.ColorRole.Light), 2))
        painter.setBrush(QBrush(palette.color(QPalette.ColorRole.Dark)))

        for port in (*self.input_ports, *self.output_ports):
            painter.drawEllipse(port.pos, 5, 5)

            # Draw port label if any
            if not port.label or not port.label.strip():
                continue
            text_pos: QPointF = QPointF(port.pos)
            text_pos.setX(text_pos.x() + (10 if port.is_input else -40))
            text_pos.setY(text_pos.y() - 10)
            painter.setPen(QPen(palette.color(QPalette.ColorRole.Text)))
            painter.drawText(text_pos, port.label)

        # Add resize handles
        if self.isSelected():
            palette: QPalette = graphics_scene.views()[0].palette()
            painter.setPen(QPen(palette.color(QPalette.ColorRole.Highlight), 1))
            painter.setBrush(QBrush(palette.color(QPalette.ColorRole.Highlight)))

            for x in [
                self.rect().left(),
                self.rect().right() - self.resize_handle_size,
            ]:
                for y in [
                    self.rect().top(),
                    self.rect().bottom() - self.resize_handle_size,
                ]:
                    painter.drawRect(
                        QRectF(
                            x,
                            y,
                            self.resize_handle_size,
                            self.resize_handle_size,
                        )
                    )

    def contextMenuEvent(
        self,
        event: QGraphicsSceneContextMenuEvent,
    ):
        menu = QMenu()

        duplicate_action: QAction | None = menu.addAction("Duplicate")
        assert duplicate_action is not None
        duplicate_action.triggered.connect(self.duplicate)

        # Add separator
        menu.addSeparator()

        # Add port actions
        add_input: QAction | None = menu.addAction("Add Input Port")
        assert add_input is not None
        add_input.triggered.connect(self.add_input_port)

        add_output: QAction | None = menu.addAction("Add Output Port")
        assert add_output is not None
        add_output.triggered.connect(self.add_output_port)

        menu.exec(event.pos().toPoint())

    def hoverEnterEvent(
        self,
        event: QGraphicsSceneHoverEvent,
    ):
        self.setBrush(self.bg_color.lighter(110))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(
        self,
        event: QGraphicsSceneHoverEvent,
    ):
        self.setBrush(self.bg_color)
        super().hoverLeaveEvent(event)

    def mousePressEvent(
        self,
        event: QGraphicsSceneMouseEvent,
    ):
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        edge: Literal["topleft", "topright", "bottomleft", "bottomright", "left", "right", "top", "bottom"] | None = self.get_resize_edge(event.pos())
        if edge is None:
            super().mousePressEvent(event)
            return
        self.is_resizing = True
        self.resize_edge: Literal["topleft", "topright", "bottomleft", "bottomright", "left", "right", "top", "bottom"] | None = edge
        event.accept()
        super().mousePressEvent(event)

    def mouseReleaseEvent(
        self,
        event: QGraphicsSceneMouseEvent,
    ):
        if event.button() == Qt.MouseButton.LeftButton and self.is_resizing:
            self.is_resizing = False
            self.resize_edge = None
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(
        self,
        event: QGraphicsSceneMouseEvent,
    ):
        if self.is_resizing:
            self.handle_resize(event.pos())
            event.accept()
            return

        # Update cursor based on edge
        edge: Literal["topleft", "topright", "bottomleft", "bottomright", "left", "right", "top", "bottom"] | None = self.get_resize_edge(event.pos())
        if edge is not None and edge in self.edge_cursors:
            self.setCursor(self.edge_cursors[edge])
        else:
            self.unsetCursor()

        super().mouseMoveEvent(event)

    def duplicate(
        self,
    ) -> Node:
        """Create a copy of this node."""
        new_node: Self = self.__class__(
            self.title,
            self.rect().width(),
            self.rect().height(),
            self.dlg_node,
        )
        new_node.setPos(self.pos() + QPointF(20, 20))
        gr_scene: QGraphicsScene | None = self.scene()
        if gr_scene is None:
            raise RuntimeError("Node must be added to a scene before duplicating")
        gr_scene.addItem(new_node)
        return new_node

    def add_input_port(
        self,
    ):
        """Add a new input port to the node."""
        port: NodePort = NodePort(self, is_input=True, label=f"In {len(self.input_ports)}")
        y_offset: int = 40 + len(self.input_ports) * 20
        port.pos = QPointF(0, y_offset)
        self.input_ports.append(port)
        self.update()

    def add_output_port(
        self,
    ):
        """Add a new output port to the node."""
        port: NodePort = NodePort(
            self,
            is_input=False,
            label=f"Out {len(self.output_ports)}",
        )
        y_offset: int = 40 + len(self.output_ports) * 20
        port.pos = QPointF(self.rect().width(), y_offset)
        self.output_ports.append(port)
        self.update()

    def delete(
        self,
    ):
        """Delete this node and its connections."""
        # Remove all connections
        for port in (*self.input_ports, *self.output_ports):
            for conn in port.connections[:]:
                conn_scene: QGraphicsScene | None = conn.scene()
                if conn_scene is None:
                    continue
                conn_scene.removeItem(conn)
                port.connections.remove(conn)

        # Remove from scene
        gr_scene: QGraphicsScene | None = self.scene()
        if gr_scene is None:
            return
        gr_scene.removeItem(self)

    def get_resize_edge(  # noqa: PLR0911
        self,
        pos: QPointF,
    ) -> Literal["topleft", "topright", "bottomleft", "bottomright", "left", "right", "top", "bottom"] | None:
        rect: QRectF = self.rect()
        margin: int = self.resize_handle_size

        edge_checks: dict[str, bool] = {
            "topleft": QRectF(rect.topLeft(), QSizeF(margin, margin)).contains(pos),
            "topright": QRectF(rect.topRight().x() - margin, rect.top(), margin, margin).contains(pos),
            "bottomleft": QRectF(rect.bottomLeft().x(), rect.bottom() - margin, margin, margin).contains(pos),
            "bottomright": QRectF(rect.bottomRight().x() - margin, rect.bottom() - margin, margin, margin).contains(pos),
            "left": pos.x() <= rect.left() + margin,
            "right": pos.x() >= rect.right() - margin,
            "top": pos.y() <= rect.top() + margin,
            "bottom": pos.y() >= rect.bottom() - margin,
        }

        return next(  # pyright: ignore[reportReturnType]
            (edge for edge, check in edge_checks.items() if check),
            None,
        )

    def handle_resize(
        self,
        pos: QPointF,
    ):
        if not self.resize_edge:
            return

        rect: QRectF = self.rect()
        new_rect: QRectF = QRectF(rect)

        if "left" in self.resize_edge:
            new_rect.setLeft(min(pos.x(), rect.right() - self.min_size.width()))
        if "right" in self.resize_edge:
            new_rect.setRight(max(pos.x(), rect.left() + self.min_size.width()))
        if "top" in self.resize_edge:
            new_rect.setTop(min(pos.y(), rect.bottom() - self.min_size.height()))
        if "bottom" in self.resize_edge:
            new_rect.setBottom(max(pos.y(), rect.top() + self.min_size.height()))

        self.setRect(new_rect)
        self.update_port_positions()

    def update_port_positions(
        self,
    ):
        """Update port positions after resize."""
        rect: QRectF = self.rect()

        # Update input ports
        for i, port in enumerate(self.input_ports):
            y_offset: int = 40 + i * 20
            port.pos = QPointF(0, min(y_offset, rect.height() - 20))

        # Update output ports
        for i, port in enumerate(self.output_ports):
            y_offset: int = 40 + i * 20
            port.pos = QPointF(rect.width(), min(y_offset, rect.height() - 20))

    def animate_to_pos(
        self,
        pos: QPointF,
    ):
        """Animate node movement to new position."""
        assert isinstance(self, QObject)
        animation: QPropertyAnimation = QPropertyAnimation(self, b"pos")
        animation.setDuration(200)
        animation.setStartValue(self.pos())
        animation.setEndValue(pos)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start()

    def highlight(
        self,
    ):
        """Temporarily highlight the node."""
        effect: QGraphicsDropShadowEffect = QGraphicsDropShadowEffect()
        effect.setColor(QColor(255, 255, 0))
        effect.setBlurRadius(20)
        effect.setOffset(0)
        self.setGraphicsEffect(effect)

        # Animate the effect
        animation: QPropertyAnimation = QPropertyAnimation(effect, b"color")
        animation.setDuration(500)
        animation.setStartValue(QColor(255, 255, 0))
        animation.setEndValue(QColor(0, 0, 0, 0))
        animation.finished.connect(lambda: self.setGraphicsEffect(None))
        animation.start()


class StartNode(Node):
    def __init__(
        self,
        node_id: str,
    ):
        super().__init__(f"ID {node_id}", width=150, height=60)

        graphics_scene: QGraphicsScene | None = self.scene()
        if graphics_scene is None:
            raise RuntimeError("Node must be added to a scene before setting visual properties")

        palette: QPalette = graphics_scene.views()[0].palette()

        # Use darker variants of palette colors
        self.bg_color = palette.color(QPalette.ColorRole.Base).darker(150)
        self.header_color = palette.color(QPalette.ColorRole.Button).darker(150)
        self.bg_brush = QBrush(self.bg_color)
        self.header_brush = QBrush(self.header_color)

        # Add START label with palette text color
        self.start_label: QGraphicsTextItem = QGraphicsTextItem(self)
        self.start_label.setDefaultTextColor(palette.color(QPalette.ColorRole.Text))
        self.start_label.setPlainText("START")
        self.start_label.setPos(10, 35)

        # Single output port
        output_port: NodePort = NodePort(self, is_input=False)
        output_port.pos = QPointF(150, 30)
        self.output_ports.append(output_port)


class DialogueNode(Node):
    def __init__(
        self,
        speaker: str,
        text: str,
        dlg_node: DLGNode | None = None,
    ):
        super().__init__(speaker, width=200, height=120, dlg_node=dlg_node)

        graphics_scene: QGraphicsScene | None = self.scene()
        if graphics_scene is None:
            raise RuntimeError("Node must be added to a scene before setting visual properties")

        palette: QPalette = graphics_scene.views()[0].palette()

        # Use accent color with variations for dialogue nodes
        accent_color: QColor = palette.color(QPalette.ColorRole.Highlight)
        self.bg_color: QColor = accent_color.darker(150)
        self.header_color: QColor = accent_color.darker(120)
        self.bg_brush: QBrush = QBrush(self.bg_color)
        self.header_brush: QBrush = QBrush(self.header_color)

        # Add dialogue text
        self.text_item: QGraphicsTextItem = QGraphicsTextItem(self)
        self.text_item.setDefaultTextColor(palette.color(QPalette.ColorRole.Text))
        if len(text) > 50:  # Truncate long text  # noqa: PLR2004
            text = text[:47] + "..."
        self.text_item.setPlainText(text)
        self.text_item.setPos(10, 35)

        # Add ports
        input_port: NodePort = NodePort(self, is_input=True)
        input_port.pos = QPointF(0, 60)
        self.input_ports.append(input_port)

        output_port: NodePort = NodePort(self, is_input=False)
        output_port.pos = QPointF(200, 60)
        self.output_ports.append(output_port)


class ConditionNode(Node):
    def __init__(
        self,
        condition: str,
        params: list[str | int] | None = None,
    ):
        super().__init__(condition, width=180, height=100)
        self.bg_color: QColor = QColor(60, 60, 20)  # Dark yellow
        self.header_color: QColor = QColor(80, 80, 20)  # Darker yellow
        self.bg_brush: QBrush = QBrush(self.bg_color)
        self.header_brush: QBrush = QBrush(self.header_color)

        # Add parameters if any
        if params:
            param_text: QGraphicsTextItem = QGraphicsTextItem(self)
            param_text.setDefaultTextColor(QColor(200, 200, 200))
            param_text.setPlainText(" ".join(str(p) for p in params))
            param_text.setPos(10, 35)

        # Add ports with labels
        input_port: NodePort = NodePort(self, is_input=True)
        input_port.pos = QPointF(0, 50)
        self.input_ports.append(input_port)

        true_port: NodePort = NodePort(self, is_input=False, label="True")
        true_port.pos = QPointF(180, 30)
        self.output_ports.append(true_port)

        false_port: NodePort = NodePort(self, is_input=False, label="False")
        false_port.pos = QPointF(180, 70)
        self.output_ports.append(false_port)


class SignalNode(Node):
    def __init__(
        self,
        signal: str,
        params: list[str | int] | None = None,
    ):
        super().__init__(signal, width=160, height=60)
        self.bg_color: QColor = QColor(20, 60, 20)  # Dark green
        self.header_color: QColor = QColor(20, 80, 20)  # Darker green
        self.bg_brush: QBrush = QBrush(self.bg_color)
        self.header_brush: QBrush = QBrush(self.header_color)

        # Add parameters if any
        if params:
            param_text: QGraphicsTextItem = QGraphicsTextItem(self)
            param_text.setDefaultTextColor(QColor(200, 200, 200))
            param_text.setPlainText(" ".join(str(p) for p in params))
            param_text.setPos(10, 35)

        # Add ports
        input_port: NodePort = NodePort(self, is_input=True)
        input_port.pos = QPointF(0, 30)
        self.input_ports.append(input_port)

        output_port: NodePort = NodePort(self, is_input=False)
        output_port.pos = QPointF(160, 30)
        self.output_ports.append(output_port)


class SetNode(Node):
    def __init__(
        self,
        variable: str,
        value: str,
    ):
        super().__init__(variable, width=160, height=80)
        self.bg_color: QColor = QColor(20, 20, 60)  # Dark blue
        self.header_color: QColor = QColor(20, 20, 80)  # Darker blue
        self.bg_brush: QBrush = QBrush(self.bg_color)
        self.header_brush: QBrush = QBrush(self.header_color)

        # Add value text
        self.value_item: QGraphicsTextItem = QGraphicsTextItem(self)
        self.value_item.setDefaultTextColor(QColor(200, 200, 200))
        self.value_item.setPlainText(f"= {value}")
        self.value_item.setPos(10, 35)

        # Add ports
        input_port: NodePort = NodePort(self, is_input=True)
        input_port.pos = QPointF(0, 40)
        self.input_ports.append(input_port)

        output_port: NodePort = NodePort(self, is_input=False)
        output_port.pos = QPointF(160, 40)
        self.output_ports.append(output_port)


class DialogueNodeEditor(QGraphicsView):
    def __init__(
        self,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        # Editor reference
        self._editor: DLGEditor | None = None

        # Create and set scene
        self._scene: QGraphicsScene = QGraphicsScene(self)
        self.setScene(self._scene)

        # Visual setup
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

        # Setup shortcuts
        self.setup_shortcuts()

        # Setup context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # Node tracking
        self.nodes: dict[DLGNode, Node] = {}
        self.connections: set[Connection] = set()

        # Setup grid
        self.setup_grid()

    @property
    def scene(self) -> QGraphicsScene:
        return self._scene

    @property
    def editor(self) -> DLGEditor | None:
        return self._editor

    @editor.setter
    def editor(
        self,
        value: DLGEditor | None,
    ):
        self._editor = value

    def setup_grid(
        self,
    ):
        # Create a dark background with grid using palette colors
        palette: QPalette = self.palette()
        dark_color: QColor = palette.color(QPalette.ColorRole.Window).darker(150)
        self.setBackgroundBrush(QBrush(dark_color))

        # Grid size
        self.grid_size: int = 20

        # Create grid lines with palette colors
        pen_color: QColor = palette.color(QPalette.ColorRole.WindowText).lighter(150)
        pen: QPen = QPen(pen_color)
        pen.setWidth(1)
        pen.setStyle(Qt.PenStyle.DotLine)  # Make grid dotted

        # Draw grid lines...

    def parse_condition(
        self,
        link: DLGLink,
    ) -> tuple[str, list[str | int]]:
        """Parse condition from link's active fields."""
        condition: str = str(link.active1 or link.active2 or "")
        params: list[str | int] = []
        if link.active1:
            params = [
                link.active1_param1,
                link.active1_param2,
                link.active1_param3,
                link.active1_param4,
                link.active1_param5,
                link.active1_param6,
            ]
        elif link.active2:
            params = [
                link.active2_param1,
                link.active2_param2,
                link.active2_param3,
                link.active2_param4,
                link.active2_param5,
                link.active2_param6,
            ]
        return condition, [p for p in params if p]

    def parse_script(
        self,
        node: DLGNode,
    ) -> tuple[str, list[str | int]]:
        """Parse script from node's script fields."""
        script: str = str(node.script1 or node.script2 or "")
        params: list[str | int] = []
        if node.script1:
            params = [
                node.script1_param1,
                node.script1_param2,
                node.script1_param3,
                node.script1_param4,
                node.script1_param5,
                node.script1_param6,
            ]
        elif node.script2:
            params = [
                node.script2_param1,
                node.script2_param2,
                node.script2_param3,
                node.script2_param4,
                node.script2_param5,
                node.script2_param6,
            ]
        return script, [p for p in params if p]

    def add_node_from_dlg(
        self,
        dlg_node: DLGNode,
        pos: QPointF,
        link: DLGLink | None = None,
    ) -> Node:
        # Check for conditions first
        if link and (link.active1 or link.active2):
            condition, params = self.parse_condition(link)
            node = ConditionNode(condition, params)
            node.setPos(pos)
            self._scene.addItem(node)

            # Create true/false paths
            true_pos = QPointF(pos.x() + 250, pos.y() - 50)
            false_pos = QPointF(pos.x() + 250, pos.y() + 50)

            # Create dialogue nodes for each path
            true_node: DialogueNode = DialogueNode("Clara", "You sure about that?", dlg_node)
            true_node.setPos(true_pos)
            self._scene.addItem(true_node)

            false_node: DialogueNode = DialogueNode("Greg", "Thank you for buying!", dlg_node)
            false_node.setPos(false_pos)
            self._scene.addItem(false_node)

            # Connect condition to true/false nodes
            self.add_connection(node, true_node, port_index=0)  # True port
            self.add_connection(node, false_node, port_index=1)  # False port

            return node

        # Check for scripts/actions
        if dlg_node and (dlg_node.script1 or dlg_node.script2):
            script, params = self.parse_script(dlg_node)
            node = SignalNode(script, params)
            node.setPos(pos)
            self._scene.addItem(node)

            # Create set node for variable
            set_pos: QPointF = QPointF(pos.x() + 200, pos.y())
            set_node: SetNode = SetNode("COINS", "5")
            set_node.setPos(set_pos)
            self._scene.addItem(set_node)

            # Connect signal to set node
            self.add_connection(node, set_node)

            return node

        # Default to dialogue node
        if isinstance(dlg_node, DLGEntry):
            node = DialogueNode("Greg", str(dlg_node.text), dlg_node)
        else:
            node = DialogueNode("Clara", str(dlg_node.text), dlg_node)
        node.setPos(pos)

        # Add to scene and tracking
        self._scene.addItem(node)
        self.nodes[dlg_node] = node

        return node

    def add_connection(
        self,
        start_node: Node,
        end_node: Node,
        port_index: int = 0,
    ):
        # Create connection between output of start node and input of end node
        conn: Connection = Connection(
            start_node.output_ports[port_index],
            end_node.input_ports[0],
        )

        # Add to scene and tracking
        self._scene.addItem(conn)
        self.connections.add(conn)

        # Update port connections
        start_node.output_ports[port_index].connections.append(conn)
        end_node.input_ports[0].connections.append(conn)

    def build_from_dlg(
        self,
        dlg_links: list[DLGLink],
    ):
        """Build the node graph from DLG links."""
        # Clear existing
        self._scene.clear()
        self.nodes.clear()
        self.connections.clear()

        # Track processed nodes to avoid duplicates
        processed_nodes: set[DLGNode] = set()

        def process_node(
            node: DLGNode,
            pos: QPointF,
            incoming_link: DLGLink | None = None,
        ):
            if node in processed_nodes:
                return

            # Add this node
            visual_node: Node = self.add_node_from_dlg(
                node,
                pos,
                incoming_link,
            )
            processed_nodes.add(node)

            # Process child nodes
            child_x: float = pos.x() + 250
            child_y: float = pos.y()
            for link in node.links:
                child_pos: QPointF = QPointF(child_x, child_y)
                child_node: Node = self.add_node_from_dlg(
                    link.node,
                    child_pos,
                    link,
                )
                self.add_connection(visual_node, child_node)
                child_y += 150

                # Recursively process children
                process_node(link.node, child_pos, link)

        # Start with root nodes
        start_x = 100
        start_y = 100
        for i, link in enumerate(dlg_links):
            # Add start node
            start_node: StartNode = StartNode(str(i + 1))
            start_node.setPos(QPointF(start_x - 200, start_y))
            self._scene.addItem(start_node)

            # Add first dialogue node
            first_node: Node = self.add_node_from_dlg(
                link.node,
                QPointF(start_x, start_y),
                link,
            )
            self.add_connection(start_node, first_node)

            # Process rest of dialogue
            process_node(link.node, QPointF(start_x, start_y), link)
            start_y += 150

    def wheelEvent(
        self,
        event: QWheelEvent,
    ):
        # Handle zooming
        zoom_factor: float = 1.15
        if event.angleDelta().y() > 0:
            self.scale(zoom_factor, zoom_factor)
        else:
            self.scale(1 / zoom_factor, 1 / zoom_factor)

    def setup_shortcuts(
        self,
    ):
        QShortcut(QKeySequence.StandardKey.Delete, self).activated.connect(self.delete_selected)
        QShortcut(QKeySequence.StandardKey.Copy, self).activated.connect(self.copy_selected)
        QShortcut(QKeySequence.StandardKey.Paste, self).activated.connect(self.paste)
        QShortcut(QKeySequence.StandardKey.Undo, self).activated.connect(self.undo)
        QShortcut(QKeySequence.StandardKey.Redo, self).activated.connect(self.redo)

    def show_context_menu(
        self,
        pos: QPointF,
    ):
        menu = QMenu(self)

        # Add node creation actions
        add_menu: QMenu | None = menu.addMenu("Add Node")
        assert add_menu is not None
        add_menu.addAction("Dialog Node", lambda: self.add_node("dialog"))
        add_menu.addAction("Condition Node", lambda: self.add_node("condition"))
        add_menu.addAction("Script Node", lambda: self.add_node("script"))

        # Add layout actions
        layout_menu: QMenu | None = menu.addMenu("Layout")
        assert layout_menu is not None
        layout_menu.addAction("Auto Layout", self.auto_layout)
        layout_menu.addAction("Align Horizontally", self.align_horizontal)
        layout_menu.addAction("Align Vertically", self.align_vertical)

        # Add view actions
        view_menu: QMenu | None = menu.addMenu("View")
        assert view_menu is not None
        view_menu.addAction("Zoom to Fit", self.zoom_to_fit)
        view_menu.addAction("Reset View", self.reset_view)

        menu.exec(self.mapToGlobal(pos.toPoint()))

    def delete_selected(self):
        """Delete all selected nodes."""
        for item in self.scene.selectedItems():
            if not isinstance(item, Node):
                continue
            item.delete()

    def copy_selected(self):
        """Copy selected nodes to clipboard."""
        if not self.editor:
            return

        selected: list[Node] = [item for item in self.scene.selectedItems() if isinstance(item, Node)]
        if not selected:
            return

        # Store node data for pasting
        self.copy_data: list[NodeCopyData] = []
        for node in selected:
            self.copy_data.append(
                NodeCopyData(
                    title=node.title,
                    width=node.rect().width(),
                    height=node.rect().height(),
                    pos=node.pos(),
                    dlg_node=node.dlg_node,
                )
            )

    def paste(self):
        """Paste copied nodes."""
        if not hasattr(self, "copy_data"):
            return

        offset = QPointF(20, 20)
        for data in self.copy_data:
            node: Node = Node(
                data.title,
                data.width,
                data.height,
                data.dlg_node,
            )
            node.setPos(data.pos + offset)
            self.scene.addItem(node)

    def add_node(
        self,
        node_type: str,
    ) -> Node | None:
        """Add a new node of the specified type."""
        pos: QPointF = self.mapToScene(self.mapFromGlobal(QCursor.pos()))

        if node_type == "dialog":
            node: Node = DialogueNode("New Dialog", "Enter text...", None)
        elif node_type == "condition":
            node = ConditionNode("New Condition")
        elif node_type == "script":
            node = SignalNode("New Script")
        else:
            return None

        node.setPos(pos)
        self.scene.addItem(node)
        return node

    def auto_layout(self):
        """Automatically layout nodes in a tree structure."""
        nodes: list[Node] = [item for item in self.scene.items() if isinstance(item, Node)]
        if not nodes:
            return

        # Simple hierarchical layout
        x_spacing = 250
        y_spacing = 150

        # Group nodes by their input connections
        levels: list[list[Node]] = self._group_nodes_by_level(nodes)

        # Position nodes level by level
        for level, level_nodes in enumerate(levels):
            x: int = level * x_spacing
            for i, node in enumerate(level_nodes):
                y: int = i * y_spacing
                node.setPos(x, y)

    def _group_nodes_by_level(
        self,
        nodes: list[Node],
    ) -> list[list[Node]]:
        """Group nodes into levels based on connections."""
        levels: list[list[Node]] = []
        processed = set()

        # Find root nodes (no inputs)
        roots: list[Node] = [node for node in nodes if not node.input_ports[0].connections]
        if roots:
            levels.append(roots)
            processed.update(roots)

        while True:
            next_level: list[Node] = []
            for node in nodes:
                if node in processed:
                    continue

                # Check if all input nodes are processed
                input_nodes: list[Node] = self._get_input_nodes(node)
                all_inputs_processed: bool = all(n in processed for n in input_nodes)
                if all_inputs_processed:
                    next_level.append(node)
                    processed.add(node)

            if not next_level:
                break

            levels.append(next_level)

        return levels

    def _get_input_nodes(
        self,
        node: Node,
    ) -> list[Node]:
        """Get all nodes connected to this node's inputs."""
        return [conn.start_port.parent_node for port in node.input_ports for conn in port.connections if conn.start_port.parent_node != node]

    def align_horizontal(self):
        """Align selected nodes horizontally."""
        selected: list[Node] = [item for item in self.scene.selectedItems() if isinstance(item, Node)]
        if not selected:
            return

        # Align to average y position
        avg_y: float = sum(node.pos().y() for node in selected) / len(selected)
        for node in selected:
            node.setPos(node.pos().x(), avg_y)

    def align_vertical(self):
        """Align selected nodes vertically."""
        selected: list[Node] = [item for item in self.scene.selectedItems() if isinstance(item, Node)]
        if not selected:
            return

        # Align to average x position
        avg_x: float = sum(node.pos().x() for node in selected) / len(selected)
        for node in selected:
            node.setPos(avg_x, node.pos().y())

    def zoom_to_fit(self):
        """Zoom view to fit all nodes."""
        rect: QRectF = self.scene.itemsBoundingRect()
        self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)

    def reset_view(self):
        """Reset view transformation."""
        self.resetTransform()
        self.centerOn(0, 0)

    def undo(self):
        """Undo last action."""
        if self.editor is None:
            return
        if self.editor.undo_stack is None:
            return
        self.editor.undo_stack.undo()

    def redo(self):
        """Redo last undone action."""
        if self.editor is None:
            return
        if self.editor.undo_stack is None:
            return
        self.editor.undo_stack.redo()
