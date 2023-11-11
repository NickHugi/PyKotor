from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.twoda import TwoDA, TwoDARow


class Diff2DA:
    def __init__(self, old: TwoDA, new: TwoDA, log_func=print):
        self.old: TwoDA = old
        self.new: TwoDA = new
        self.log = log_func

    def compare_2da(self) -> bool:
        old_headers = set(self.old.get_headers())
        new_headers = set(self.new.get_headers())
        ret = True

        # Check for column header mismatches
        missing_headers = old_headers - new_headers
        extra_headers = new_headers - old_headers
        if missing_headers:
            self.log(f"Missing headers in new TwoDA: {', '.join(missing_headers)}")
            ret = False
        if extra_headers:
            self.log(f"Extra headers in new TwoDA: {', '.join(extra_headers)}")
            ret = False
        if not ret:
            return False

        # Common headers
        common_headers: set[str] = old_headers.intersection(new_headers)

        # Check for row mismatches
        old_indices: set[int | None] = {self.old.row_index(row) for row in self.old}
        new_indices: set[int | None] = {self.new.row_index(row) for row in self.new}
        missing_rows: set[int | None] = old_indices - new_indices
        extra_rows: set[int | None] = new_indices - old_indices
        if missing_rows:
            self.log(f"Missing rows in new TwoDA: {', '.join(map(str, missing_rows))}")
            ret = False
        if extra_rows:
            self.log(f"Extra rows in new TwoDA: {', '.join(map(str, extra_rows))}")
            ret = False

        # Check cell values for common rows
        for index in old_indices.intersection(new_indices):
            if index is None:
                self.log("Row mismatch")
                return False
            old_row: TwoDARow = self.old.get_row(index)
            new_row: TwoDARow = self.new.get_row(index)
            for header in common_headers:
                old_value: str = old_row.get_string(header)
                new_value: str = new_row.get_string(header)
                if old_value != new_value:
                    self.log(f"Cell mismatch at RowIndex '{index}' Header '{header}': '{old_value}' --> '{new_value}'")
                    ret = False

        return ret
