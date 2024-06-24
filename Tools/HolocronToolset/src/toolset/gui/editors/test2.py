from __future__ import annotations

import pathlib
import random
import sys

from typing import TYPE_CHECKING

from qtpy.QtCore import QLineF
from qtpy.QtGui import QBrush, QColor, QPainter, QPen
from qtpy.QtWidgets import (
    QApplication,
    QGraphicsEllipseItem,
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
    from qtpy.QtCore import QPoint, QPointF

    from toolset.gui.editors.dlg import DLGNode, DLGStandardItemModel

# Initialize the application
app = QApplication([])

class GraphNode(QGraphicsEllipseItem):
    def __init__(self, node: DLGNode, x: float, y: float, radius: int = 20):
        super().__init__(-radius, -radius, 2 * radius, 2 * radius)
        self.setPos(x, y)
        self.node: DLGNode = node
        self.text_item = QGraphicsTextItem(str(node), self)
        self.text_item.setDefaultTextColor(QColor(255, 255, 255))
        self.text_item.setPos(-radius, radius)
        self.setBrush(QBrush(QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))))  # noqa: S311
        self.setPen(QPen(QColor(255, 255, 255)))

class GraphEdge(QGraphicsLineItem):
    def __init__(self, start_pos: QPointF | QPoint, end_pos: QPointF | QPoint):
        line: QLineF = QLineF(start_pos, end_pos)
        super().__init__(line)
        self.setPen(QPen(QColor(255, 255, 255), 2))

class GraphWidget(QGraphicsView):
    def __init__(self, model: DLGStandardItemModel):
        super().__init__()
        self.model: DLGStandardItemModel = model
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setBackgroundBrush(QBrush(QColor(0, 0, 0)))
        self.node_items = {}
        self.layout_graph()

    def layout_graph(self):
        starters = self.model.editor.core_dlg.starters
        for starter in starters:
            self._layout_node(starter.node)

    def _layout_node(
        self,
        node: DLGNode,
        level: int = 0,
        visited: set[DLGNode] | None = None,
    ):
        if visited is None:
            visited = set()
        if node in visited:
            return
        visited.add(node)

        # Scatterplot-like random placement
        x = random.uniform(-500, 500)  # noqa: S311
        y = random.uniform(-500, 500)  # noqa: S311

        node_item = GraphNode(node, x, y)
        self.scene.addItem(node_item)
        self.node_items[node] = node_item

        for link in node.links:
            self._layout_node(link.node, level + 1, visited)

            # Draw edge from this node to the child node
            if link.node in self.node_items:
                start_pos = node_item.scenePos()
                end_pos = self.node_items[link.node].scenePos()
                edge = GraphEdge(start_pos, end_pos)
                self.scene.addItem(edge)

class MainWindow(QMainWindow):
    def __init__(self, model: DLGStandardItemModel):
        super().__init__()
        self.graph_widget: GraphWidget = GraphWidget(model)
        self.setCentralWidget(self.graph_widget)

def main():
    # Initialize the editor and its components
    editor = DLGEditor(None, None)
    tree_view = editor.ui.dialogTree
    model = tree_view.model()

    # Use the create_complex_tree method to generate the DLG structure
    dlg = create_complex_tree()
    editor._loadDLG(dlg)  # Assuming _loadDLG method exists in DLGEditor to load a DLG instance  # noqa: SLF001

    window = MainWindow(model)
    window.show()

    sys.exit(app.exec_())

def create_complex_tree() -> DLG:
    # Create the DLG structure with entries and replies
    dlg = DLG(blank_node=False)
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
