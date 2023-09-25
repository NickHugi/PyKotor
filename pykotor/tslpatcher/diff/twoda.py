from pykotor.resource.formats.twoda import TwoDA


class Diff2DA:
    def __init__(self, old: TwoDA, new: TwoDA):
        self.old: TwoDA = old
        self.new: TwoDA = new

    def is_same(self) -> bool:
        old_columns = set(self.old.get_headers())
        new_columns = set(self.new.get_headers())

        if old_columns != new_columns:
            print("Columns match")
            return False

        for old_row in self.old:
            index = self.old.row_index(old_row)
            if index is None:
                msg = "Row mismatch"
                raise ValueError(msg)
            if index >= len(self.new._labels) or index < 0:
                print(f"New index {index} outside of the TwoDA length: {len(self.new._labels)}")
                return False
            new_row = self.new.get_row(index)

            for header in old_columns:
                old_value = old_row.get_string(header)
                new_value = new_row.get_string(header)
                if old_value != new_value:
                    print("Cell mismatch:", index, header)
                    return False

        return True
