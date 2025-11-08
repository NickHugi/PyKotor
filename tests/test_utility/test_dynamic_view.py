from __future__ import annotations

import sys
import unittest

from typing import cast
from unittest.mock import Mock

from qtpy.QtCore import QRect, QSize, QTimer
from qtpy.QtWidgets import QApplication

from utility.ui_libraries.qt.widgets.widgets.stacked_view import DynamicStackedView


class TestIsSizeSuitableForView(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app: QApplication = cast(QApplication, QApplication.instance() or QApplication(sys.argv))

    @classmethod
    def tearDownClass(cls):
        cls.app.quit()

    def setUp(self):
        self.view_manager: DynamicStackedView = DynamicStackedView()
        self.current_view: Mock = Mock()
        self.viewport: Mock = Mock()
        self.model: Mock = Mock()

        self.current_view.viewport.return_value = self.viewport
        self.current_view.model.return_value = self.model

    def test_is_size_suitable_for_view(self):
        self.viewport.size.return_value = QSize(1000, 800)
        self.current_view.visualRect.return_value = QRect(0, 0, 100, 80)

        result: bool = self.view_manager.is_size_suitable_for_view(12)
        assert result, "The size should be suitable for the view"

        self.current_view.visualRect.return_value = QRect(0, 0, 300, 240)
        result = self.view_manager.is_size_suitable_for_view(12)
        assert not result, "The size should not be suitable for the view"

    def test_is_size_suitable_for_view_custom_max_percent(self):
        self.viewport.size.return_value = QSize(1000, 800)
        self.current_view.visualRect.return_value = QRect(0, 0, 200, 160)

        result = self.view_manager.is_size_suitable_for_view(12)
        assert result

        result = self.view_manager.is_size_suitable_for_view(12)
        assert not result


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
