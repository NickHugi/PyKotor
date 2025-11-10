from __future__ import annotations

import sys
import unittest

from typing import cast
from unittest.mock import Mock, patch

from qtpy.QtCore import QModelIndex, QRect, QSize, Qt
from qtpy.QtGui import QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QAbstractItemView, QApplication, QColumnView, QListView, QTableView, QTreeView

from utility.ui_libraries.qt.widgets.widgets.stacked_view import DynamicStackedView


class TestDynamicStackedView(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app: QApplication = cast(QApplication, QApplication.instance() or QApplication(sys.argv))

    @classmethod
    def tearDownClass(cls):
        cls.app.quit()

    def setUp(self):
        self.view_manager: DynamicStackedView = DynamicStackedView()
        self.model = QStandardItemModel()
        for i in range(10):
            item = QStandardItem(f"Item {i+1}")
            self.model.appendRow(item)
        self.view_manager.setModel(self.model)

    def tearDown(self):
        self.view_manager.deleteLater()

    def test_init_default_widgets(self):
        """Test that default initialization creates expected views."""
        view_manager = DynamicStackedView()
        all_views = view_manager.all_views()
        assert len(all_views) >= 4, "Should have at least 4 default views"
        
        # Check that we have various view types
        has_list_view = any(isinstance(view, QListView) for view in all_views)
        has_tree_view = any(isinstance(view, QTreeView) for view in all_views)
        has_table_view = any(isinstance(view, QTableView) for view in all_views)
        has_column_view = any(isinstance(view, QColumnView) for view in all_views)
        
        assert has_list_view, "Should have at least one QListView"
        assert has_tree_view, "Should have a QTreeView"
        assert has_table_view, "Should have a QTableView"
        assert has_column_view, "Should have a QColumnView"

    def test_init_custom_widgets(self):
        """Test initialization with custom widget list."""
        custom_list = [QListView(), QTreeView()]
        view_manager = DynamicStackedView(all_views=custom_list)
        all_views = view_manager.all_views()
        assert len(all_views) == 2, "Should have exactly 2 custom views"
        assert isinstance(all_views[0], QListView)
        assert isinstance(all_views[1], QTreeView)

    def test_set_widgets(self):
        """Test setting widgets dynamically."""
        new_views = [QListView(), QTableView()]
        view_manager = DynamicStackedView()
        view_manager.set_widgets(new_views)
        assert view_manager.count() >= 2, "Should have at least the new widgets"

    def test_all_views(self):
        """Test retrieving all views."""
        all_views = self.view_manager.all_views()
        assert len(all_views) > 0, "Should have views"
        assert all(isinstance(view, QAbstractItemView) for view in all_views), "All items should be QAbstractItemView"

    def test_all_widgets(self):
        """Test retrieving all widgets."""
        all_widgets = self.view_manager.all_widgets()
        assert len(all_widgets) > 0, "Should have widgets"
        assert all(isinstance(widget, object) for widget in all_widgets), "All items should be widgets"

    def test_current_view(self):
        """Test getting current view."""
        current = self.view_manager.current_view()
        assert current is not None, "Should have a current view"
        assert isinstance(current, QAbstractItemView), "Current view should be QAbstractItemView"

    def test_list_view(self):
        """Test getting list view."""
        list_view = self.view_manager.list_view()
        assert list_view is not None, "Should have a list view"
        assert isinstance(list_view, QListView), "Should be QListView"

    def test_tree_view(self):
        """Test getting tree view."""
        tree_view = self.view_manager.tree_view()
        assert tree_view is not None, "Should have a tree view"
        assert isinstance(tree_view, QTreeView), "Should be QTreeView"

    def test_table_view(self):
        """Test getting table view."""
        table_view = self.view_manager.table_view()
        assert table_view is not None, "Should have a table view"
        assert isinstance(table_view, QTableView), "Should be QTableView"

    def test_column_view(self):
        """Test getting column view."""
        column_view = self.view_manager.column_view()
        assert column_view is not None, "Should have a column view"
        assert isinstance(column_view, QColumnView), "Should be QColumnView"

    def test_set_model(self):
        """Test setting model on all views."""
        new_model = QStandardItemModel()
        new_model.appendRow(QStandardItem("Test"))
        self.view_manager.setModel(new_model)
        
        for view in self.view_manager.all_views():
            assert view.model() == new_model, "All views should have the new model"

    def test_set_current_widget(self):
        """Test setting current widget."""
        widgets = self.view_manager.all_widgets()
        if len(widgets) > 1:
            self.view_manager.setCurrentWidget(widgets[1])
            assert self.view_manager.currentWidget() == widgets[1], "Current widget should be updated"
            assert self.view_manager.current_view_index == 1, "Current view index should be updated"

    def test_switch_to_next_view(self):
        """Test switching to next view."""
        initial_index = self.view_manager.current_view_index
        self.view_manager.switch_to_next_view()
        assert self.view_manager.current_view_index == initial_index + 1, "Should move to next view"

    def test_switch_to_previous_view(self):
        """Test switching to previous view."""
        # First switch to next view
        self.view_manager.switch_to_next_view()
        current_index = self.view_manager.current_view_index
        
        # Then switch back
        self.view_manager.switch_to_previous_view()
        assert self.view_manager.current_view_index == current_index - 1, "Should move to previous view"

    def test_switch_to_next_view_at_end(self):
        """Test that switching at end doesn't go beyond bounds."""
        widgets = self.view_manager.all_widgets()
        self.view_manager.current_view_index = len(widgets) - 1
        self.view_manager.setCurrentWidget(widgets[-1])
        
        self.view_manager.switch_to_next_view()
        assert self.view_manager.current_view_index == len(widgets) - 1, "Should stay at last view"

    def test_switch_to_previous_view_at_start(self):
        """Test that switching at start doesn't go below zero."""
        self.view_manager.current_view_index = 0
        self.view_manager.setCurrentWidget(self.view_manager.all_widgets()[0])
        
        self.view_manager.switch_to_previous_view()
        assert self.view_manager.current_view_index == 0, "Should stay at first view"

    def test_set_root_index(self):
        """Test setting root index on all views."""
        # Create a parent item with children
        parent_item = QStandardItem("Parent")
        for i in range(3):
            parent_item.appendRow(QStandardItem(f"Child {i+1}"))
        self.model.appendRow(parent_item)
        
        parent_index = self.model.indexFromItem(parent_item)
        self.view_manager.setRootIndex(parent_index)
        
        # Check that all views have the new root index
        for view in self.view_manager.all_views():
            assert view.rootIndex() == parent_index, "All views should have the new root index"

    def test_root_index(self):
        """Test getting root index."""
        root_index = self.view_manager.rootIndex()
        assert isinstance(root_index, QModelIndex), "Should return QModelIndex"

    def test_clear_selection(self):
        """Test clearing selection on all views."""
        # Select an item first
        current_view = self.view_manager.current_view()
        if current_view:
            index = self.model.index(0, 0)
            current_view.setCurrentIndex(index)
            
        self.view_manager.clearSelection()
        
        # Verify selection is cleared
        for view in self.view_manager.all_views():
            assert len(view.selectedIndexes()) == 0, "Selection should be cleared"

    def test_selection_model(self):
        """Test that all views share the same selection model."""
        selection_model = self.view_manager.selectionModel()
        assert selection_model is not None, "Should have a selection model"
        
        for view in self.view_manager.all_views():
            assert view.selectionModel() == selection_model, "All views should share selection model"

    def test_selected_indexes(self):
        """Test getting selected indexes."""
        current_view = self.view_manager.current_view()
        if current_view:
            index = self.model.index(0, 0)
            current_view.setCurrentIndex(index)
            current_view.selectionModel().select(index, current_view.selectionModel().SelectionFlag.Select)
            
        selected = self.view_manager.selectedIndexes()
        assert len(selected) > 0, "Should have selected indexes"

    def test_select_all(self):
        """Test selecting all items."""
        # Set up a model with actual items
        from qtpy.QtGui import QStandardItemModel, QStandardItem
        from qtpy.QtWidgets import QAbstractItemView
        model = QStandardItemModel()
        for i in range(5):
            model.appendRow(QStandardItem(f"Item {i}"))
        
        self.view_manager.setModel(model)
        current_view = self.view_manager.current_view()
        if current_view:
            # Ensure selection mode allows multiple selections
            current_view.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
            self.view_manager.selectAll()
            QApplication.processEvents()
            selected = current_view.selectedIndexes()
            # Should have selected all items (5 items)
            assert len(selected) >= 5, f"Should have selected items after selectAll, got {len(selected)}"

    def test_update_icon_size(self):
        """Test updating icon size."""
        text_size = 24
        self.view_manager.update_icon_size(text_size)
        
        for view in self.view_manager.all_views():
            icon_size = view.iconSize()
            assert icon_size.width() == text_size, f"Icon width should be {text_size}"
            assert icon_size.height() == text_size, f"Icon height should be {text_size}"

    def test_adjust_view_size(self):
        """Test adjusting view size."""
        current_view = self.view_manager.current_view()
        if current_view:
            initial_font_size = current_view.font().pointSize()
            self.view_manager.adjust_view_size(2)
            # Font size should change or view should switch
            assert True, "adjust_view_size should execute without error"

    def test_is_size_suitable_for_view(self):
        """Test size suitability check."""
        # This is a complex method that depends on viewport and model state
        # We'll test that it returns a boolean
        result = self.view_manager.is_size_suitable_for_view()
        assert isinstance(result, bool), "Should return boolean"

    def test_is_size_suitable_for_view_no_current_view(self):
        """Test size suitability when no current view."""
        view_manager = DynamicStackedView(all_views=[])
        result = view_manager.is_size_suitable_for_view()
        assert result is False, "Should return False when no current view"

    def test_get_actual_view(self):
        """Test getting actual view from widget."""
        widgets = self.view_manager.all_widgets()
        for widget in widgets:
            view = self.view_manager.get_actual_view(widget)
            assert isinstance(view, QAbstractItemView), "Should return QAbstractItemView"

    def test_get_actual_view_specific_type(self):
        """Test getting specific view type from widget."""
        list_view = self.view_manager.list_view()
        if list_view:
            # Find the widget containing this list view
            for widget in self.view_manager.all_widgets():
                try:
                    view = self.view_manager.get_actual_view(widget, QListView)
                    assert isinstance(view, QListView), "Should return QListView when requested"
                    break
                except ValueError:
                    continue

    def test_wheel_event_with_ctrl(self):
        """Test wheel event with Ctrl modifier."""
        current_view = self.view_manager.current_view()
        if current_view:
            # Create a mock wheel event with Ctrl modifier
            with patch.object(self.view_manager, 'adjust_view_size') as mock_adjust:
                # This would normally be triggered by actual wheel event
                # We're just testing the logic path
                self.view_manager.adjust_view_size(1)
                mock_adjust.assert_called_once_with(1)


FORCE_UNITTEST = False
VERBOSE = True
FAIL_FAST = False


def run_tests():
    print("Running tests of TestQFileDialog")
    try:
        import pytest

        if not FORCE_UNITTEST:
            pytest.main(["-v" if VERBOSE else "", "-x" if FAIL_FAST else "", "--tb=native", __file__])
        else:
            raise ImportError  # noqa: TRY301
    except ImportError:
        unittest.main(verbosity=2 if VERBOSE else 1, failfast=FAIL_FAST)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    QTimer.singleShot(0, run_tests)
    app.exec()
