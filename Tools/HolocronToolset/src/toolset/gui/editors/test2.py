from __future__ import annotations

import math
import pathlib
import random
import sys

from typing import TYPE_CHECKING

from qtpy.QtCore import QLineF, Qt
from qtpy.QtGui import QBrush, QColor, QPainter, QPen
from qtpy.QtWidgets import (
    QApplication,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QMainWindow,
)


def update_sys_path(path: pathlib.Path):
    working_dir = str(path)
    if working_dir not in sys.path:
        sys.path.append(working_dir)

file_absolute_path = pathlib.Path(__file__).resolve()
utility_path = file_absolute_path.parents[6] / "Libraries" / "Utility" / "src"
if utility_path.exists():
    update_sys_path(utility_path)
pykotor_path = file_absolute_path.parents[6] / "Libraries" / "PyKotor" / "src"
if pykotor_path.exists():
    update_sys_path(pykotor_path)

from utility.system.path import Path  # noqa: E402

# Working dir should always be 'toolset' when running this script.
TOOLSET_DIR = Path(file_absolute_path.parents[3])
if TOOLSET_DIR.joinpath("toolset").exists():
    update_sys_path(TOOLSET_DIR)

from pykotor.common.language import LocalizedString  # noqa: E402
from pykotor.resource.generics.dlg import DLG  # noqa: E402
from toolset.gui.editors.dlg import DLGEditor, DLGEntry, DLGLink, DLGReply  # noqa: E402

if TYPE_CHECKING:

    from toolset.gui.editors.dlg import DLGNode, DLGStandardItemModel

app = QApplication([])

class GraphNode(QGraphicsEllipseItem):
    def __init__(self, node: DLGNode, x: int, y: int, radius: int = 20):
        super().__init__(-radius, -radius, 2*radius, 2*radius)
        self.setPos(x, y)
        self.node: DLGNode = node
        if isinstance(node, DLGEntry):
            color = QColor(255, 0, 0)  # Red for DLGEntry
        elif isinstance(node, DLGReply):
            color = QColor(0, 0, 255)  # Blue for DLGReply
        else:
            raise TypeError(node)
        self.setBrush(QBrush(color))
        self.setPen(QPen(QColor(255, 255, 255)))  # White border
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.edges: list[GraphEdge] = []
        self.text_item: QGraphicsTextItem = QGraphicsTextItem(str(node), self)
        self.text_item.setDefaultTextColor(QColor(255, 255, 255))
        self.text_item.setPos(-radius, -radius / 2)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            for edge in self.edges:
                edge.adjust()
        return super().itemChange(change, value)

class GraphEdge(QGraphicsLineItem):
    def __init__(self, start_item: GraphNode, end_item: GraphNode):
        super().__init__()
        self.start_item: GraphNode = start_item
        self.end_item: GraphNode = end_item
        self.start_item.edges.append(self)
        self.end_item.edges.append(self)
        self.setPen(QPen(QColor(0, 255, 0), 2))

        self.adjust()

    def adjust(self):
        """Adjust the line to connect the centers of start and end items."""
        start_pos = self.start_item.scenePos()
        end_pos = self.end_item.scenePos()
        line = QLineF(start_pos, end_pos)
        self.setLine(line)

class GraphWidget(QGraphicsView):
    def __init__(self, model: DLGStandardItemModel):
        super().__init__()
        self.model = model
        self._scene = QGraphicsScene()
        self.setScene(self._scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setBackgroundBrush(QBrush(QColor(0, 0, 0)))
        self.node_items = {}
        self.layout_graph()

    def wheelEvent(self, event):
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            zoomInFactor = 1.25
            zoomOutFactor = 1 / zoomInFactor
            self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
            if event.angleDelta().y() > 0:
                self.scale(zoomInFactor, zoomInFactor)
            else:
                self.scale(zoomOutFactor, zoomOutFactor)
        else:
            super().wheelEvent(event)

    def layout_graph(self):
        starters = self.model.editor.core_dlg.starters
        radius = 200
        center_x, center_y = 0, 0
        angle_step = 2 * math.pi / len(starters)

        for i, starter in enumerate(starters):
            assert starter.node is not None
            angle = i * angle_step
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            self._layout_node(starter.node, x, y, {starter.node})

    def _layout_node(self, node: DLGNode, x: int, y: int, visited: set[DLGNode]):
        if node in self.node_items:
            return

        node_item = GraphNode(node, x, y)
        self._scene.addItem(node_item)
        self.node_items[node] = node_item

        child_radius = 100
        for link in node.links:
            assert link.node is not None
            if link.node in visited:
                continue
            visited.add(link.node)
            angle = random.uniform(0, 360)  # noqa: S311
            child_x = x + child_radius * math.cos(math.radians(angle))
            child_y = y + child_radius * math.sin(math.radians(angle))

            self._layout_node(link.node, child_x, child_y, visited)
            edge = GraphEdge(node_item, self.node_items[link.node])
            self._scene.addItem(edge)

    def _is_overlapping(self, x, y, other_pos):
        """Check if the proposed position overlaps with an existing node."""
        min_distance = 50  # Minimum distance to consider non-overlapping
        return (x - other_pos.x())**2 + (y - other_pos.y())**2 < min_distance**2

class MainWindow(QMainWindow):
    def __init__(self, model: DLGStandardItemModel):
        super().__init__()
        self.graph_widget: GraphWidget = GraphWidget(model)
        self.setCentralWidget(self.graph_widget)

def main():
    editor = DLGEditor(None, None)
    tree_view = editor.ui.dialogTree
    model = tree_view.model()

    # Use the create_complex_tree method to generate the DLG structure
    dlg = create_complex_tree()
    editor._loadDLG(dlg)

    window = MainWindow(model)
    window.show()

    sys.exit(app.exec_())

def create_complex_tree() -> DLG:
    # Create the DLG structure with entries and replies
    dlg = DLG()
    entries = [DLGEntry(comment=f"E{i}") for i in range(5)]
    replies = [DLGReply(text=LocalizedString.from_english(f"R{i}")) for i in range(5, 10)]

    # Create a nested structure
    def add_links(parent_node: DLGNode, children: list[DLGNode]):
        for i, child in enumerate(children):
            link = DLGLink(node=child, list_index=i)
            parent_node.links.append(link)

    add_links(entries[0], [replies[0]])
    add_links(replies[0], [entries[1]])
    add_links(entries[1], [replies[1]])
    add_links(replies[1], [entries[2]])
    add_links(entries[2], [replies[2]])
    add_links(replies[2], [entries[3]])
    add_links(entries[3], [replies[3]])
    add_links(replies[3], [entries[4]])

    # Reuse nodes/links
    entries[2].links.append(DLGLink(node=entries[4], list_index=1))  # reuse E4
    replies[0].links.append(DLGLink(node=replies[1], list_index=1))  # reuse R7

    # Set starters
    dlg.starters.append(DLGLink(node=entries[0], list_index=0))  # Start with the first entry

    # Manually update list_index
    def update_list_index(links: list[DLGLink]):
        for i, link in enumerate(links):
            link.list_index = i
            if link.node:
                update_list_index(link.node.links)

    update_list_index(dlg.starters)

    return dlg

if __name__ == "__main__":
    main()
