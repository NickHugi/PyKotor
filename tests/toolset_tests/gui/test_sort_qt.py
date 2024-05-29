from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import QSortFilterProxyModel, Qt
from qtpy.QtGui import QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QApplication, QTableView

from pykotor.common.misc import ResRef
from pykotor.resource.formats.erf.erf_data import ERFResource
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from qtpy import QtCore


def human_readable_size(byte_size: float) -> str:
    for unit in ["bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]:
        if byte_size < 1024:  # noqa: PLR2004
            return f"{round(byte_size, 2)} {unit}"
        byte_size /= 1024
    return str(byte_size)


class ERFSortFilterProxyModel(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()
        self.setDynamicSortFilter(True)

    def get_sort_value(self, index: QtCore.QModelIndex) -> int:
        """Return the sort value based on the column."""
        srcModel = self.sourceModel()
        assert isinstance(srcModel, QStandardItemModel)
        if index.column() == 2:
            resource: ERFResource = srcModel.item(index.row(), 0).data()
            return len(resource.data)
        return self.sourceModel().data(index)

    def lessThan(self, left: QtCore.QModelIndex, right: QtCore.QModelIndex) -> bool:
        srcModel = self.sourceModel()
        assert isinstance(srcModel, QStandardItemModel)
        left_data = self.get_sort_value(left)
        right_data = self.get_sort_value(right)

        return left_data < right_data

def create_model(init_colleciton) -> QStandardItemModel:
    model = QStandardItemModel()
    model.setHorizontalHeaderLabels(["Name", "Resource Type", "Size"])
    for resref, restype, data in init_colleciton:
        res = ERFResource(ResRef(resref), restype, data)
        row = [
            QStandardItem(resref),
            QStandardItem(res.restype.extension.upper()),
            QStandardItem(human_readable_size(len(data)))
        ]
        row[0].setData(res)
        row[1].setData(res)
        row[2].setData(res)
        model.appendRow(row)
    return model

def verify_sorting(proxy: ERFSortFilterProxyModel, expected_order):
    actual_order = [proxy.index(row, 0).data() for row in range(proxy.rowCount())]
    assert actual_order == expected_order, f"Actual order {actual_order} does not match expected {expected_order}"


# Application setup
if __name__ == "__main__":
    app = QApplication([])
    view = QTableView()

    data = [
        ("workbnch_tut", ResourceType.DLG, bytearray(int(135.13 * 1024))),
        ("3cfd", ResourceType.DLG, bytearray(int(97.3 * 1024))),
        ("intro", ResourceType.DLG, bytearray(int(49.58 * 1024))),
        ("seccon", ResourceType.DLG, bytearray(int(45.78 * 1024))),
        ("combat", ResourceType.DLG, bytearray(int(44.2 * 1024))),
        ("001ebo", ResourceType.GIT, bytearray(int(43.24 * 1024))),
        ("extra", ResourceType.DLG, bytearray(int(36.92 * 1024))),
        ("hyper", ResourceType.DLG, bytearray(int(25.38 * 1024))),
        ("001ebo", ResourceType.PTH, bytearray(int(19.32 * 1024))),
        ("001ebo", ResourceType.ARE, bytearray(int(4.75 * 1024))),
    ]

    model = create_model(data)
    proxy = ERFSortFilterProxyModel()
    proxy.setSourceModel(model)

    # Perform the primary sort by size in descending order
    proxy.sort(2, Qt.DescendingOrder)
    # Then apply a secondary sort by name in ascending order
    proxy.sort(0, Qt.AscendingOrder)

    # Test the sorting
    expected_order = ["001ebo", "001ebo", "001ebo", "3cfd", "combat", "extra", "hyper", "intro", "seccon", "workbnch_tut"]
    verify_sorting(proxy, expected_order)

    # Perform the sort by name in descending order
    proxy.sort(0, Qt.DescendingOrder)

    # Test the sorting
    expected_order = ["workbnch_tut", "seccon", "intro", "hyper", "extra", "combat", "3cfd", "001ebo", "001ebo", "001ebo"]
    verify_sorting(proxy, expected_order)

    view.setModel(proxy)
    view.setSortingEnabled(True)
    view.show()
    app.exec_()