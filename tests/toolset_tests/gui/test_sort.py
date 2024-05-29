# Running the updated sorting logic with extracted values and ensuring it works properly
from __future__ import annotations

# Simplifying the model and data types for efficient execution and analysis

class ERFResource:
    def __init__(self, name: str, res_type: str, size: int):
        self.name = name
        self.res_type = res_type
        self.size = size


class ERFSortFilterProxyModel:
    def __init__(self):
        self.data = []

    def add_data(self, resref, restype, size):
        resource = ERFResource(resref, restype, size)
        self.data.append(resource)

    def sort(self, column, order="ascending"):
        reverse = (order == "descending")

        # Extracting sort key based on the column index provided.
        if column == 0:
            key_func = lambda x: x.name
        elif column == 1:
            key_func = lambda x: x.res_type
        elif column == 2:
            key_func = lambda x: x.size
        else:
            raise ValueError("Invalid column index")

        # Apply sort; Python's sort is stable which maintains the relative order of records that compare equal
        self.data.sort(key=key_func, reverse=reverse)

    def get_data(self):
        return [(item.name, item.res_type, item.size) for item in self.data]

# Data and tests setup
data = [
    ("workbnch_tut", "DLG", int(135.13 * 1024)),
    ("3cfd", "DLG", int(97.3 * 1024)),
    ("intro", "DLG", int(49.58 * 1024)),
    ("seccon", "DLG", int(45.78 * 1024)),
    ("combat", "DLG", int(44.2 * 1024)),
    ("001ebo", "GIT", int(43.24 * 1024)),
    ("extra", "DLG", int(36.92 * 1024)),
    ("hyper", "DLG", int(25.38 * 1024)),
    ("001ebo", "PTH", int(19.32 * 1024)),
    ("001ebo", "ARE", int(4.75 * 1024)),
]

# Initialize and populate the sorter
sorter = ERFSortFilterProxyModel()
for resref, restype, size in data:
    sorter.add_data(resref, restype, size)

# Perform the primary sort by size in descending order
sorter.sort(2, "descending")
# Then apply a secondary sort by name in ascending order
sorter.sort(0, "ascending")

# Test the sorting
sorted_data = sorter.get_data()

# Get the sorted data
sorted_data = sorter.get_data()
test1 = ("001ebo", "GIT", int(43.24 * 1024))
test2 = ("001ebo", "PTH", int(19.32 * 1024))
test3 = ("001ebo", "ARE", int(4.75 * 1024))
test4 = ("3cfd", "DLG", int(97.3 * 1024))
assert sorted_data[0] == test1, f"{sorted_data[0]} != {test1}"
assert sorted_data[1] == test2, f"{sorted_data[1]} != {test2}"
assert sorted_data[2] == test3, f"{sorted_data[2]} != {test3}"
assert sorted_data[3] == test4, f"{sorted_data[3]} != {test4}"

sorter.sort(0, "descending")
sorted_data = sorter.get_data()
test5 = ("workbnch_tut", "DLG", int(135.13 * 1024))
test6 = ("seccon", "DLG", int(45.78 * 1024))
test7 = ("intro", "DLG", int(49.58 * 1024))
test8 = ("hyper", "DLG", int(25.38 * 1024))
assert sorted_data[0] == test5, f"{sorted_data[0]} != {test5}"
assert sorted_data[1] == test6, f"{sorted_data[1]} != {test6}"
assert sorted_data[2] == test7, f"{sorted_data[2]} != {test7}"
assert sorted_data[3] == test8, f"{sorted_data[3]} != {test8}"
