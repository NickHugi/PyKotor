import pytest
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QApplication

from toolset.gui.editors.dlg.editor_with_switcher import DLGEditorWithSwitcher
from pykotor.resource.generics.dlg import DLG, DLGEntry, DLGReply, DLGLink

def test_view_switching(qtbot):
    """Test that view switching works correctly."""
    editor = DLGEditorWithSwitcher()
    qtbot.addWidget(editor)
    
    # Check initial state
    assert editor.view_switcher.get_current_view() == "tree"
    
    # Switch to graph view
    editor.view_switcher.switch_view("graph")
    assert editor.view_switcher.get_current_view() == "graph"
    
    # Switch back to tree view
    editor.view_switcher.switch_view("tree")
    assert editor.view_switcher.get_current_view() == "tree"

def test_data_synchronization(qtbot):
    """Test that both views stay synchronized."""
    editor = DLGEditorWithSwitcher()
    qtbot.addWidget(editor)
    
    # Create test data
    dlg = DLG()
    entry = DLGEntry()
    entry.list_index = 0
    reply = DLGReply()
    reply.list_index = 0
    link = DLGLink(reply)
    entry.links.append(link)
    dlg.starters.append(DLGLink(entry))
    
    # Load data
    editor._load_dlg(dlg)
    
    # Check tree view
    tree_model = editor.ui.dialogTree.model()
    assert tree_model is not None, "Tree model should not be None"
    assert tree_model.rowCount() == 1, "Tree should have one root item"
    
    # Switch to graph view
    editor.view_switcher.switch_view("graph")
    
    # Check graph view
    graph_view = editor.view_switcher.get_graph_view()
    assert len(graph_view.nodes) == 2, "Graph should have Entry and Reply nodes"
    assert len(graph_view.connections) == 1, "Graph should have one connection"

def test_editor_integration(qtbot):
    """Test that the editor works with both views."""
    editor = DLGEditorWithSwitcher()
    qtbot.addWidget(editor)
    
    # Create test data
    dlg = DLG()
    entry = DLGEntry()
    entry.list_index = 0
    entry.speaker = "Test Speaker"  # DLGEntry has speaker attribute
    dlg.starters.append(DLGLink(entry))
    
    # Load data
    editor._load_dlg(dlg)
    
    # Test tree view editing
    tree_view = editor.ui.dialogTree
    tree_model = tree_view.model()
    assert tree_model is not None, "Tree model should not be None"
    
    index = tree_model.index(0, 0)
    assert index.isValid(), "Tree model index should be valid"
    tree_view.setCurrentIndex(index)
    
    # Switch to graph view
    editor.view_switcher.switch_view("graph")
    
    # Verify changes reflected in graph
    graph_view = editor.view_switcher.get_graph_view()
    assert len(graph_view.nodes) > 0, "Graph should have nodes"
    
    node = next(iter(graph_view.nodes.values()))
    assert node.dlg_node is not None, "Node should have dlg_node"
    assert isinstance(node.dlg_node, DLGEntry), "Node should be DLGEntry"
    assert node.dlg_node.speaker == "Test Speaker", "Speaker should match"

def test_node_creation(qtbot):
    """Test node creation in graph view."""
    editor = DLGEditorWithSwitcher()
    qtbot.addWidget(editor)
    
    # Create test data
    dlg = DLG()
    entry = DLGEntry()
    entry.list_index = 0
    dlg.starters.append(DLGLink(entry))
    
    # Load data and switch to graph view
    editor._load_dlg(dlg)
    editor.view_switcher.switch_view("graph")
    
    # Check node creation
    graph_view = editor.view_switcher.get_graph_view()
    assert len(graph_view.nodes) == 1, "Graph should have one node"
    
    node = next(iter(graph_view.nodes.values()))
    assert node.title.startswith("Entry"), "Node should be an Entry"
    assert node.dlg_node == entry, "Node should reference correct DLGEntry"
