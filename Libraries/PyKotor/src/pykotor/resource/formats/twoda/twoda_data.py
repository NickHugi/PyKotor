"""This module handles classes related to reading, modifying and writing 2DA files.

2DA (Two-Dimensional Array) files store tabular game data in a spreadsheet-like format.
They contain configuration data for nearly all game systems: items, spells, creatures,
skills, feats, and many other game mechanics. The format uses column headers, row labels,
and string-based cells that are parsed as integers, floats, or other types as needed.

References:
----------
    vendor/TSLPatcher/lib/site/Bioware/TwoDA.pm:1-945 - Complete 2DA implementation
    vendor/Kotor.NET/Kotor.NET/Formats/Kotor2DA/TwoDABinaryStructure.cs:10-139 - Binary format
    vendor/KotOR_IO/KotOR_IO/File Formats/TwoDA.cs:20-288 - C# 2DA reader/writer
    vendor/KotOR-Bioware-Libs/TwoDA.pm - Perl 2DA library
    vendor/reone/include/reone/resource/2da.h:28-107 - C++ 2DA class
    vendor/xoreos/src/aurora/2dafile.cpp:38-376 - 2DA file handling
    vendor/KotOR.js/src/resource/TwoDAObject.ts:9-276 - TypeScript implementation
    vendor/sotor/core/src/formats/twoda/read.rs:13-127 - Rust 2DA reader

Binary Format (Version 2.b):
----------------------------
    Header (9 bytes):
        - 4 bytes: File Type ("2DA ")
        - 4 bytes: File Version ("V2.0" or "v2.b" for binary)
        - 1 byte: Line break ('\n')
    
    Column Headers (variable length):
        - Tab-separated column names
        - Terminated by null byte ('\0')
    
    Row Count:
        - 4 bytes: Number of rows (int32)
    
    Row Labels (variable length):
        - Tab-separated row labels/indices
        - One per row
    
    Cell Data Offsets:
        - 2 bytes per cell (uint16): offset into cell data string table
        - One offset for each cell (row_count * column_count)
    
    Cell Data Size:
        - 2 bytes (uint16): total size of cell data string table
    
    Cell Data String Table:
        - Null-terminated strings
        - Deduplicated (same string value shares offset)
        - Blank cells typically stored as empty string or "****"
        
    Reference: Kotor.NET:19-63, KotOR_IO:60-135, TSLPatcher/TwoDA.pm:200-350

ASCII Format (Version V2.0):
----------------------------
    Line 1: "2DA V2.0"
    Line 2: Blank line or DEFAULT: value
    Line 3: Tab-separated column headers
    Lines 4+: Row_label <tab> cell1 <tab> cell2...
    
    Blank cells represented as "****"
"""

from __future__ import annotations

import copy as copy_module
from contextlib import contextmanager, suppress
from copy import copy
from typing import TYPE_CHECKING, Any, TypeVar

from pykotor.resource.formats._base import ComparableMixin
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from collections.abc import Callable
    from enum import Enum

T = TypeVar("T")


class TwoDA(ComparableMixin):
    """Two-Dimensional Array table for game configuration data.
    
    2DA files store tabular data used throughout the game engine. Each file contains
    a set of named columns (headers), numbered rows (labels), and string-valued cells.
    The game reads these files at startup and queries them during gameplay for various
    configuration values like item properties, spell effects, creature stats, etc.
    
    References:
    ----------
        vendor/TSLPatcher/lib/site/Bioware/TwoDA.pm:48-71 - get_cell() implementation
        vendor/Kotor.NET/Kotor.NET/Formats/Kotor2DA/TwoDABinaryStructure.cs:12-112 - FileRoot class
        vendor/KotOR_IO/KotOR_IO/File Formats/TwoDA.cs:20-152 - TwoDA class structure
        vendor/reone/include/reone/resource/2da.h:28-107 - TwoDA C++ class
        vendor/xoreos/src/aurora/2dafile.h:40-108 - 2DAFile class
        
    Attributes:
    ----------
        _rows: Internal list of row dictionaries mapping column headers to cell values
            Reference: TSLPatcher/TwoDA.pm:70 (table hash structure)
            Reference: KotOR_IO/TwoDA.cs:152 (Data dictionary)
            Reference: reone/2da.h:103 (_rows vector)
            Each row is a dict[str, str] where keys are column headers
            All cell values stored as strings regardless of actual type
            Empty/blank cells represented as "" (empty string)
            
        _headers: List of column header names
            Reference: TSLPatcher/TwoDA.pm:130 (columns array)
            Reference: Kotor.NET/TwoDABinaryStructure.cs:15 (ColumnHeaders list)
            Reference: KotOR_IO/TwoDA.cs:142 (Columns list)
            Reference: reone/2da.h:102 (_columns vector)
            Headers are case-sensitive strings (typically lowercase)
            Order matters for binary format cell offset calculation
            Common headers: "label", "name", "description", "icon", etc.
            
        _labels: List of row labels (typically numeric indices as strings)
            Reference: TSLPatcher/TwoDA.pm:133 (rows_array)
            Reference: Kotor.NET/TwoDABinaryStructure.cs:16 (RowHeaders list)
            Reference: KotOR_IO/TwoDA.cs:100 (generated index_list)
            Row labels are usually numeric ("0", "1", "2"...) but can be arbitrary strings
            Used for row identification and lookup
            Game typically accesses rows by integer index, labels are metadata
    """

    BINARY_TYPE = ResourceType.TwoDA
    COMPARABLE_SEQUENCE_FIELDS = ("_rows", "_headers", "_labels")

    def __init__(
        self,
        headers: list[str] | None = None,
    ):
        # vendor/Kotor.NET/Kotor.NET/Formats/Kotor2DA/TwoDABinaryStructure.cs:17
        # vendor/KotOR_IO/KotOR_IO/File Formats/TwoDA.cs:152
        # vendor/TSLPatcher/lib/site/Bioware/TwoDA.pm:70
        # Internal storage: list of dicts, each dict is a row mapping column headers to cell values
        self._rows: list[dict[str, str]] = []
        
        # vendor/Kotor.NET/Kotor.NET/Formats/Kotor2DA/TwoDABinaryStructure.cs:15
        # vendor/KotOR_IO/KotOR_IO/File Formats/TwoDA.cs:142
        # vendor/reone/include/reone/resource/2da.h:102
        # Column headers (case-sensitive, typically lowercase)
        self._headers: list[str] = [] if headers is None else headers  # for columns
        
        # vendor/Kotor.NET/Kotor.NET/Formats/Kotor2DA/TwoDABinaryStructure.cs:16
        # vendor/KotOR_IO/KotOR_IO/File Formats/TwoDA.cs:98-100
        # vendor/TSLPatcher/lib/site/Bioware/TwoDA.pm:133
        # Row labels (usually "0", "1", "2"... but can be arbitrary strings)
        self._labels: list[str] = []  # for rows
        
        # Performance optimization: O(1) lookup for row labels
        # Maps label string to row index for fast find_row() operations
        self._label_to_index: dict[str, int] = {}

    def __eq__(self, other):
        if not isinstance(other, TwoDA):
            return NotImplemented
        return (
            self._rows == other._rows
            and self._headers == other._headers
            and self._labels == other._labels
        )

    def __hash__(self):
        return hash((
            tuple(tuple(sorted(row.items())) for row in self._rows),
            tuple(self._headers),
            tuple(self._labels)
        ))

    def __repr__(
        self,
    ):
        return f"{self.__class__.__name__}(headers={self._headers!r}, labels={self._labels!r}, rows={self._rows!r})"

    def __iter__(
        self,
    ):
        """Iterates through each row yielding a new linked TwoDARow instance."""
        for i, row in enumerate(self._rows):
            yield TwoDARow(self.get_label(i), row)

    def __len__(
        self,
    ) -> int:
        """Returns the number of rows in the 2DA.

        Returns:
        -------
            The number of rows.
        """
        return self.get_height()

    def __contains__(
        self,
        label: str,
    ) -> bool:
        """Checks if a row label exists in the 2DA.

        Args:
        ----
            label: The row label to check.

        Returns:
        -------
            True if the label exists, False otherwise.
        """
        return label in self._label_to_index

    def __getitem__(
        self,
        key: int | str | slice,
    ) -> TwoDARow | list[TwoDARow]:
        """Pythonic access to rows by index, label, or slice.

        Args:
        ----
            key: Row index (int), label (str), or slice.

        Returns:
        -------
            TwoDARow for single access, list[TwoDARow] for slice.

        Raises:
        ------
            KeyError: If label not found.
            IndexError: If index out of range.
        """
        if isinstance(key, int):
            return self.get_row(key)
        if isinstance(key, str):
            result = self.find_row(key)
            if result is None:
                raise KeyError(f"Row label '{key}' not found")
            return result
        if isinstance(key, slice):
            indices = range(len(self._rows))[key]
            return [self.get_row(i) for i in indices]
        msg = f"Invalid key type: {type(key).__name__}. Expected int, str, or slice."
        raise TypeError(msg)

    @property
    def shape(
        self,
    ) -> tuple[int, int]:
        """Returns the dimensions of the 2DA as (rows, columns).

        Returns:
        -------
            Tuple of (row_count, column_count).
        """
        return (self.get_height(), self.get_width())

    @property
    def columns(
        self,
    ) -> list[str]:
        """Returns a copy of the column headers.

        Returns:
        -------
            List of column header names.
        """
        return copy(self._headers)

    @property
    def index(
        self,
    ) -> list[str]:
        """Returns a copy of the row labels.

        Returns:
        -------
            List of row labels.
        """
        return copy(self._labels)

    def get_headers(
        self,
    ) -> list[str]:
        """Returns a copy of the set of column headers.

        Returns:
        -------
            The column headers.
        """
        return copy(self._headers)

    def get_column(
        self,
        header: str,
    ) -> list[str]:
        """Returns every cell listed under the specified column header.

        Args:
        ----
            header: The column header.

        Raises:
        ------
            KeyError: If the specified column header does not exist.

        Returns:
        -------
            A list of cells.
        """
        if header not in self._headers:
            msg = f"The header '{header}' does not exist."
            raise KeyError(msg)

        return [self._rows[i][header] for i in range(self.get_height())]

    def get_columns(
        self,
    ) -> dict[str, list[str]]:
        """Returns all columns as a dictionary mapping header names to their column values.

        Returns:
        -------
            A dictionary where keys are column headers and values are lists of cells.
        """
        return {header: self.get_column(header) for header in self._headers}

    def add_column(
        self,
        header: str,
    ):
        """Adds a new column with the specified header and populates it with blank cells for each row.

        Args:
        ----
            header: The header for the new column.

        Raises:
        ------
            KeyError: If the specified column header already exists.
        """
        if header in self._headers:
            msg = f"The header '{header}' already exists."
            raise KeyError(msg)

        self._headers.append(header)
        for row in self._rows:
            row[header] = ""

    def remove_column(
        self,
        header: str,
    ):
        """Removes a column from the table with the specified column header.

        If no such column header exists it is ignored; no error is thrown.

        Args:
        ----
            header: The column header.
        """
        if header in self._headers:
            for row in self._rows:
                row.pop(header)

        self._headers.remove(header)

    def get_labels(
        self,
    ) -> list[str]:
        """Returns a copy of the set of row labels.

        Returns:
        -------
            The column headers.
        """
        return copy(self._labels)

    def get_label(
        self,
        row_index: int,
    ) -> str:
        """Returns the row label for the given row.

        Args:
        ----
            row_index: The index of the row.

        Returns:
        -------
            Returns the row label.
        """
        return self._labels[row_index]

    def get_row_label(
        self,
        row_index: int,
    ) -> str:
        """Returns the row label for the given row.

        Args:
        ----
            row_index: The index of the row.

        Returns:
        -------
            Returns the row label.
        """
        return self.get_label(row_index)

    def set_label(
        self,
        row_index: int,
        value: str,
    ):
        """Sets the row label at the given index.

        Updates the label lookup dictionary for O(1) find_row performance.

        Args:
        ----
            row_index: The index of the row to change.
            value: The new row label.
        """
        old_label = self._labels[row_index]
        self._labels[row_index] = value
        # Update lookup dictionary
        if old_label in self._label_to_index:
            del self._label_to_index[old_label]
        self._label_to_index[value] = row_index

    def _rebuild_label_lookup(self):
        """Rebuilds the label-to-index lookup dictionary.

        Should be called after bulk operations that modify labels.
        """
        self._label_to_index = {label: idx for idx, label in enumerate(self._labels)}

    def has_row(
        self,
        row_index: int,
    ) -> bool:
        """Checks if a row exists at the given index.

        Args:
        ----
            row_index: The row index to check.

        Returns:
        -------
            True if the row exists, False otherwise.
        """
        return 0 <= row_index < len(self._rows)

    def get_row(
        self,
        row_index: int,
        context: str | None = None,
    ) -> TwoDARow:
        """Returns a TwoDARow instance which can update and retrieve the values of the cells for the specified row.

        Args:
        ----
            row_index: The row index.

        Raises:
        ------
            IndexError: If the specified row does not exist.

        Returns:
        -------
            A new TwoDARow instance.
        """
        try:
            label_row = self.get_label(row_index)
        except IndexError as e:
            e.args = (f"Row index {row_index} not found in the 2DA." + (f" Context: {context}" if context is not None else ""),)
            raise
        return TwoDARow(label_row, self._rows[row_index])

    def find_row(
        self,
        row_label: str,
    ) -> TwoDARow | None:
        """Find a row in a 2D array by its label.

        Uses O(1) lookup via label_to_index dictionary for performance.

        Args:
        ----
            row_label: The label of the row to find

        Returns:
        -------
            row: The row object if found, else None

        Processing Logic:
        ----------------
            - Use O(1) lookup dictionary if available
            - Fallback to O(n) search for compatibility
        """
        # Use O(1) lookup if available, fallback to O(n) search for compatibility
        if row_label in self._label_to_index:
            row_index = self._label_to_index[row_label]
            return self.get_row(row_index)
        # Fallback for cases where lookup dict might be out of sync
        return next((row for row in self if row.label() == row_label), None)

    def row_index(
        self,
        row: TwoDARow,
    ) -> int | None:
        """Returns the index of a row in a 2D array if found.

        Args:
        ----
            row: The row to search for in the 2D array.

        Returns:
        -------
            int | None: The index of the row if found, else None.

        Processing Logic:
        ----------------
            - Iterate through the 2D array and enumerate the rows.
            - Check if the current row equals the searching row.
            - If a match is found, return the index i.
            - If no match is found after full iteration, return None.
        """
        return next((i for i, searching in enumerate(self) if searching == row), None)

    def add_row(
        self,
        row_label: str | None = None,
        cells: dict[str, Any] | None = None,
    ) -> int:
        """Adds a new row to the end of the table.

        Headers specified in the cells parameter that do not exist in the table
        itself will be ignored, headers that are not specified in the cells parameter but do exist in the table will
        default to being blank. All cells are converted to strings before being added into the 2DA.

        Args:
        ----
            row_label: The row label. If None then the row label will be its index.
            cells: A dictionary representing the cells of the new row. A key is the header and value is the cell.

        Returns:
        -------
            The id of the new row.
        """
        self._rows.append({})
        label = str(len(self._rows)) if row_label is None else row_label
        self._labels.append(label)
        
        # Update lookup dictionary for O(1) find_row performance
        row_index = len(self._rows) - 1
        self._label_to_index[label] = row_index

        if cells is None:
            cells = {}

        for header in cells:
            cells[header] = str(cells[header])

        for header in self._headers:
            self._rows[-1][header] = cells.get(header, "")

        return row_index

    def copy_row(
        self,
        source_row: TwoDARow,
        row_label: str | None = None,
        override_cells: dict[str, Any] | None = None,
    ) -> int:
        """Adds a new row to the end of the table with the same values as the source row.

        Args:
        ----
            row_label: The row label. If None then the row label will be its index.
            cells: A dictionary representing the cells of the new row. A key is the header and value is the cell.

        Returns:
        -------
            The id of the new row.
        """
        source_index = self.row_index(source_row)

        self._rows.append({})
        label = str(len(self._rows)) if row_label is None else row_label
        self._labels.append(label)
        
        # Update lookup dictionary for O(1) find_row performance
        row_index = len(self._rows) - 1
        self._label_to_index[label] = row_index

        if override_cells is None:
            override_cells = {}

        for header in override_cells:
            override_cells[header] = str(override_cells[header])

        for header in self._headers:
            self._rows[-1][header] = override_cells[header] if header in override_cells else self.get_cell(source_index, header)  # FIXME: source_index cannot be None

        return row_index

    def get_cell(
        self,
        row_index: int,
        column: str,
        context: str | None = None,
    ) -> str:
        """Returns the value of the cell at the specified row under the specified column.

        Args:
        ----
            row_index: The row index.
            column: The column header.
            context: Optional context string for better error messages.

        Raises:
        ------
            KeyError: If the specified column does not exist.
            IndexError: If the specified row does not exist.

        Returns:
        -------
            The cell value.
        """
        try:
            return self._rows[row_index][column]
        except KeyError as e:
            available = [h for h in self._headers if h in self._rows[row_index]]
            msg = f"Column '{column}' not found in row {row_index}."
            if available:
                msg += f" Available columns: {available}"
            if context:
                msg += f" | Context: {context}"
            raise KeyError(msg) from e
        except IndexError as e:
            msg = f"Row index {row_index} out of range [0, {len(self._rows)})"
            if context:
                msg += f" | Context: {context}"
            raise IndexError(msg) from e

    def get_cell_safe(
        self,
        row_index: int,
        column: str,
        default: str = "",
    ) -> str:
        """Safe cell access with default value - perfect for model loading and similar use cases.

        Args:
        ----
            row_index: The row index.
            column: The column header.
            default: Default value to return if row/column doesn't exist.

        Returns:
        -------
            The cell value, or default if row/column doesn't exist.
        """
        try:
            return self.get_cell(row_index, column)
        except (KeyError, IndexError):
            return default

    def set_cell(
        self,
        row_index: int,
        column: str,
        value: Any,
    ):
        """Sets the value of a cell at the specified row under the specified column. If the value is none, it will output a blank string.

        Args:
        ----
            row_index: The row index.
            column: The column header.
            value: The new value of the target cell.

        Raises:
        ------
            KeyError: If the specified column does not exist.
            IndexError: If the specified row does not exist.
        """
        value = "" if value is None else value
        self._rows[row_index][column] = str(value)

    def get_height(
        self,
    ) -> int:
        """Returns the number of rows in the table.

        Returns:
        -------
            The number of rows.
        """
        return len(self._rows)

    def get_width(
        self,
    ) -> int:
        """Returns the number of columns in the table.

        Returns:
        -------
            The number of columns.
        """
        return len(self._headers)

    def resize(
        self,
        row_count: int,
    ):
        """Sets the number of rows in the table.

        Use with caution; specifying a height less than the current height will result in a loss of data.

        Args:
        ----
            row_count: The number of rows to set.

        Raises:
        ------
            ValueError: If the height is negative.
        """
        if self.get_height() < 0:
            msg = "The height of the table cannot be negative."
            raise ValueError(msg)
        current_height = len(self._rows)

        if row_count < current_height:
            # trim the _rows list
            self._rows = self._rows[:row_count]
            self._labels = self._labels[:row_count]
            # Rebuild lookup dictionary after trimming
            self._rebuild_label_lookup()
        else:
            # insert the new rows with each cell filled in blank
            for _ in range(row_count - current_height):
                self.add_row()

    def column_max(
        self,
        header: str,
    ) -> int:
        """Returns the highest numerical value underneath the specified column.

        Returns:
        -------
            Highest numerical value underneath the column.
        """
        max_found = -1
        for cell in self.get_column(header):
            with suppress(ValueError):
                max_found = max(int(cell), max_found)

        return max_found + 1

    def label_max(
        self,
    ) -> int:
        """Finds the maximum label and returns the next integer.

        Args:
        ----
            self: The object containing labels.

        Returns:
        -------
            int: The next integer label.

        Processes labels:
        ----------------
            - Initialize max_found to -1
            - Iterate through labels
            - Try converting each label to int and update max_found
            - Return max_found + 1 to get the next integer label.
        """
        max_found = -1
        for label in self.get_labels():
            with suppress(ValueError):
                max_found = max(int(label), max_found)

        return max_found + 1

    def update_cells(
        self,
        updates: dict[tuple[int, str], Any],
    ):
        """Batch update multiple cells efficiently.

        Args:
        ----
            updates: Dictionary mapping (row_index, column) tuples to new values.

        Example:
        -------
            twoda.update_cells({
                (0, "name"): "New Name",
                (1, "value"): 42,
                (2, "description"): "Updated"
            })
        """
        for (row_idx, col), value in updates.items():
            self.set_cell(row_idx, col, value)

    def filter_rows(
        self,
        predicate: Callable[[TwoDARow], bool],
    ) -> TwoDA:
        """Return new TwoDA with filtered rows.

        Args:
        ----
            predicate: Function that takes a TwoDARow and returns True to keep it.

        Returns:
        -------
            New TwoDA instance with filtered rows.

        Example:
        -------
            filtered = twoda.filter_rows(lambda row: row.get_string("type") == "weapon")
        """
        result = TwoDA(self._headers)
        for row in self:
            if predicate(row):
                result.add_row(row.label(), row._data)
        return result

    @contextmanager
    def batch_update(self):
        """Context manager for batch updates with validation and rollback on error.

        If an exception occurs during the batch update, all changes are rolled back.

        Example:
        -------
            with twoda.batch_update():
                twoda.set_cell(0, "name", "new_value")
                twoda.add_row("new_label")
                # If any error occurs, all changes are rolled back
        """
        original_rows = copy_module.deepcopy(self._rows)
        original_labels = copy(self._labels)
        original_label_to_index = copy(self._label_to_index)
        try:
            yield self
        except Exception:
            # Rollback on error
            self._rows = original_rows
            self._labels = original_labels
            self._label_to_index = original_label_to_index
            raise

    def compare(
        self,
        other: TwoDA,
        log_func: Callable = print,
    ) -> bool:
        """Compares two TwoDA objects.

        Args:
        ----
            self: The first TwoDA object
            other: The second TwoDA object
            log_func: Function to log comparison results (default print)

        Returns:
        -------
            bool: True if the TwoDAs match, False otherwise

        Processing Logic:
        ----------------
            - Check for column header mismatches
            - Check for row mismatches
            - Check cell values for common rows
        """
        old_headers = set(self.get_headers())
        new_headers = set(other.get_headers())
        ret = True

        # Check for column header mismatches
        missing_headers: set[str] = old_headers - new_headers
        extra_headers: set[str] = new_headers - old_headers
        if missing_headers:
            log_func(f"Missing headers in new TwoDA: {', '.join(missing_headers)}")
            ret = False
        if extra_headers:
            log_func(f"Extra headers in new TwoDA: {', '.join(extra_headers)}")
            ret = False
        if not ret:
            return False

        # Common headers
        common_headers: set[str] = old_headers.intersection(new_headers)

        # Check for row mismatches
        old_indices: set[int | None] = {self.row_index(row) for row in self}
        new_indices: set[int | None] = {other.row_index(row) for row in other}
        missing_rows: set[int | None] = old_indices - new_indices
        extra_rows: set[int | None] = new_indices - old_indices
        if missing_rows:
            log_func(f"Missing rows in new TwoDA: {', '.join(map(str, missing_rows))}")
            ret = False
        if extra_rows:
            log_func(f"Extra rows in new TwoDA: {', '.join(map(str, extra_rows))}")
            ret = False

        # Check cell values for common rows
        for index in old_indices.intersection(new_indices):
            if index is None:
                log_func("Row mismatch")
                return False
            old_row: TwoDARow = self.get_row(index)
            new_row: TwoDARow = other.get_row(index)
            for header in common_headers:
                old_value: str = old_row.get_string(header)
                new_value: str = new_row.get_string(header)
                if old_value != new_value:
                    log_func(f"Cell mismatch at RowIndex '{index}' Header '{header}': '{old_value}' --> '{new_value}'")
                    ret = False

        return ret


class TwoDARow(ComparableMixin):
    """A single row in a 2DA table with accessor methods for typed cell values.
    
    TwoDARow provides a convenient interface for accessing and modifying cell values
    in a specific row, with automatic type conversion for integers, floats, and enums.
    This class is typically returned by TwoDA.get_row() and provides a pythonic interface
    to the underlying string-based storage.
    
    References:
    ----------
        vendor/TSLPatcher/lib/site/Bioware/TwoDA.pm:48-71 - Cell access by row/column
        vendor/KotOR_IO/KotOR_IO/File Formats/TwoDA.cs:162-200 - Indexer for cell access
        vendor/reone/src/libs/resource/2da.cpp:36-84 - Type conversion methods
        
    Attributes:
    ----------
        _row_label: The label/identifier for this row
            Reference: TSLPatcher/TwoDA.pm:133 (rows_array)
            Reference: Kotor.NET/TwoDABinaryStructure.cs:35-36 (row label reading)
            Usually numeric ("0", "1"...) but can be arbitrary string
            
        _data: Dictionary mapping column headers to cell string values
            Reference: TSLPatcher/TwoDA.pm:70 (table->{row}{column} structure)
            Reference: KotOR_IO/TwoDA.cs:152 (Data[columnLabel][rowIndex])
            All values stored as strings, converted on access
            Empty cells are "" (empty string), not null/None
    """
    
    COMPARABLE_FIELDS = ("_row_label", "_data")
    def __init__(
        self,
        row_label: str,
        row_data: dict[str, str],
    ):
        # vendor/Kotor.NET/Kotor.NET/Formats/Kotor2DA/TwoDABinaryStructure.cs:35-36
        # vendor/TSLPatcher/lib/site/Bioware/TwoDA.pm:133
        # Row label (typically numeric index as string)
        self._row_label: str = row_label
        
        # vendor/KotOR_IO/KotOR_IO/File Formats/TwoDA.cs:152
        # vendor/TSLPatcher/lib/site/Bioware/TwoDA.pm:70
        # Cell data: column_header -> cell_value (all strings)
        self._data: dict[str, str] = row_data

    def __repr__(
        self,
    ):
        return f"{self.__class__.__name__}(row_label={self._row_label}, row_data={self._data})"

    def __eq__(self, other: TwoDARow | object):
        if self is other:
            return True
        if isinstance(other, TwoDARow):
            return self._row_label == other._row_label and self._data == other._data
        return NotImplemented

    def __hash__(self):
        return hash((self._row_label, tuple(sorted(self._data.items()))))

    def label(
        self,
    ) -> str:
        """Returns the row label.

        Returns:
        -------
            The label for the row.
        """
        return self._row_label

    def has_string(
        self,
        header: str,
    ) -> bool:
        """Checks if a header exists in this row.

        Args:
        ----
            header: The column header to check.

        Returns:
        -------
            True if the header exists, False otherwise.
        """
        return header in self._data

    def update_values(
        self,
        values: dict[str, str],
    ):
        """Updates cell values in the table.

        Args:
        ----
            values: dict[str, str]: A dictionary of column names and cell values

        Updates each cell value:
            - Loops through the values dictionary
            - Gets the column name and cell value
            - Calls set_string to update the cell with the value
            - Repeats for each key-value pair in values
        """
        for column, cell in values.items():
            self.set_string(column, cell)

    def get_string(
        self,
        header: str,
        context: str | None = None,
    ) -> str:
        """Returns the string value for the cell under the specified header.

        Args:
        ----
            header: The column header for the cell.

        Raises:
        ------
            KeyError: If the specified header does not exist.

        Returns:
        -------
            The cell value.
        """
        if header not in self._data:
            msg = f"The header '{header}' does not exist."
            if context is not None:
                msg += f"Context: {context}"
            raise KeyError(msg)
        return self._data[header]

    def get_integer(
        self,
        header: str,
        default: int | T = None,
    ) -> int | T:
        """Returns the integer value for the cell under the specified header. If the value of the cell is an invalid integer then a default value is used instead.

        Args:
        ----
            header: The column header for the cell.
            default: The default value.

        Raises:
        ------
            KeyError: If the specified header does not exist.

        Returns:
        -------
            The cell value as an integer or a default value.
        """
        if header not in self._data:
            msg = f"The header '{header}' does not exist."
            raise KeyError(msg)

        value: int | T = default
        with suppress(ValueError):
            cell = self._data[header]
            return int(cell, 16) if cell.startswith("0x") else int(cell)
        return value

    def get_float(
        self,
        header: str,
        default: int | T = None,
    ) -> float | T:
        """Returns the float value for the cell under the specified header. If the value of the cell is an invalid float then a default value is used instead.

        Args:
        ----
            header: The column header for the cell.
            default: The default value.

        Raises:
        ------
            KeyError: If the specified header does not exist.

        Returns:
        -------
            The cell value as a float or default value.
        """
        if header not in self._data:
            msg = f"The header '{header}' does not exist."
            raise KeyError(msg)

        with suppress(ValueError):
            cell = self._data[header]
            return float(cell)
        return default

    def get_enum(
        self,
        header: str,
        enum_type: type[Enum],
        default: Enum | T = None,
    ) -> Enum | T:
        """Returns the enum value for the cell under the specified header.

        Args:
        ----
            header: The column header for the cell.
            enum_type: The enum class to try parse the cell value with.
            default: The default value.

        Raises:
        ------
            KeyError: If the specified header does not exist.

        Returns:
        -------
            The cell value as a enum or default value.
        """
        if header not in self._data:
            msg = f"The header '{header}' does not exist."
            raise KeyError(msg)

        value: Enum | T = default
        if enum_type(self._data[header]):
            value = enum_type(self._data[header])
        return value

    def set_string(
        self,
        header: str,
        value: str | None,
    ):
        """Sets the value of a cell under the specified header. If the value is None it will default to a empty string.

        Args:
        ----
            header: The column header for the cell.
            value: The new cell value.

        Raises:
        ------
            KeyError: If the specified header does not exist.
        """
        self._set_value(header, value)

    def set_integer(
        self,
        header: str,
        value: int | None,
    ):
        """Sets the value of a cell under the specified header, converting the integer into a string. If the value is None it will default to a empty string.

        Args:
        ----
            header: The column header for the cell.
            value: The new cell value.

        Raises:
        ------
            KeyError: If the specified header does not exist.
        """
        self._set_value(header, value)

    def set_float(
        self,
        header: str,
        value: float | None,
    ):
        """Sets the value of a cell under the specified header, converting the float into a string. If the value is None it will default to a empty string.

        Args:
        ----
            header: The column header for the cell.
            value: The new cell value.

        Raises:
        ------
            KeyError: If the specified header does not exist.
        """
        self._set_value(header, value)

    def set_enum(
        self,
        header: str,
        value: Enum | None,
    ):
        """Sets the value of a cell under the specified header, converting the enum into a string. If the value is None it will default to a empty string.

        Args:
        ----
            header: The column header for the cell.
            value: The new cell value.

        Raises:
        ------
            KeyError: If the specified header does not exist.
        """
        self._set_value(header, None if value is None else value.value)

    def _set_value(self, header: str, value: Enum | float | str | None):
        if header not in self._data:
            msg = f"The header '{header}' does not exist."
            raise KeyError(msg)
        value_str = "" if value is None else str(value)
        self._data[header] = value_str
