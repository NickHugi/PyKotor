"""This module handles classes related to reading, modifying and writing 2DA files."""
from __future__ import annotations

from contextlib import suppress
from copy import copy
from typing import TYPE_CHECKING, Any

from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from enum import Enum


class TwoDA:
    """Represents a 2DA file."""

    BINARY_TYPE = ResourceType.TwoDA

    def __init__(
        self,
        headers: list[str] | None = None,
    ):
        self._rows: list[dict[str, str]] = []
        self._headers: list[str] = [] if headers is None else headers  # for columns
        self._labels: list[str] = []  # for rows

    def __iter__(
        self,
    ):
        """Iterates through each row yielding a new linked TwoDARow instance."""
        for i, row in enumerate(self._rows):
            yield TwoDARow(self.get_label(i), row)

    def get_headers(
        self,
    ) -> list[str]:
        """Returns a copy of the set of column headers.

        Returns
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

    def add_column(
        self,
        header: str,
    ) -> None:
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
    ) -> None:
        """Removes a column from the table with the specified column header. If no such column header exists it is ignored;
        no error is thrown.

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

        Returns
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

    def set_label(
        self,
        row_index: int,
        value: str,
    ) -> None:
        """Sets the row label at the given index.

        Args:
        ----
            row_index: The index of the row to change.
            value: The new row label.
        """
        self._labels[row_index] = value

    def get_row(
        self,
        row_index: int,
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
        return TwoDARow(self.get_label(row_index), self._rows[row_index])

    def find_row(
        self,
        row_label: str,
    ) -> TwoDARow | None:
        return next((row for row in self if row.label() == row_label), None)

    def row_index(
        self,
        row: TwoDARow,
    ) -> int | None:
        return next((i for i, searching in enumerate(self) if searching == row), None)

    def add_row(
        self,
        row_label: str | None = None,
        cells: dict[str, Any] | None = None,
    ) -> int:
        """Adds a new row to the end of the table. Headers specified in the cells parameter that do not exist in the table
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
        self._labels.append(str(len(self._rows)) if row_label is None else row_label)

        if cells is None:
            cells = {}

        for header in cells:
            cells[header] = str(cells[header])

        for header in self._headers:
            self._rows[-1][header] = cells.get(header, "")

        return len(self._rows) - 1

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
        self._labels.append(str(len(self._rows)) if row_label is None else row_label)

        if override_cells is None:
            override_cells = {}

        for header in override_cells:
            override_cells[header] = str(override_cells[header])

        for header in self._headers:
            self._rows[-1][header] = (
                override_cells[header]
                if header in override_cells
                else self.get_cell(source_index, header)
            )

        return len(self._rows) - 1

    def get_cell(
        self,
        row_index: int,
        column: str,
    ) -> str:
        """Returns the value of the cell at the specified row under the specified column.

        Args:
        ----
            row_index: The row index.
            column: The column header.

        Raises:
        ------
            KeyError: If the specified column does not exist.
            IndexError: If the specified row does not exist.

        Returns:
        -------
            The cell value.
        """
        return self._rows[row_index][column]

    def set_cell(
        self,
        row_index: int,
        column: str,
        value: Any,
    ) -> None:
        """Sets the value of a cell at the specified row under the specified column. If the value is none, it will output a
        blank string.

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

        Returns
        -------
            The number of rows.
        """
        return len(self._rows)

    def get_width(
        self,
    ) -> int:
        """Returns the number of columns in the table.

        Returns
        -------
            The number of columns.
        """
        return len(self._headers)

    def resize(
        self,
        row_count: int,
    ) -> None:
        """Sets the number of rows in the table. Use with caution; specifying a height less than the current height will
        result in a loss of data.

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
        else:
            # insert the new rows with each cell filled in blank
            for _ in range(row_count - current_height):
                self.add_row()

    def column_max(
        self,
        header: str,
    ) -> int:
        """Returns the highest numerical value underneath the specified column.

        Returns
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
        max_found = -1
        for label in self.get_labels():
            with suppress(ValueError):
                max_found = max(int(label), max_found)

        return max_found + 1


class TwoDARow:
    def __init__(
        self,
        row_label: str,
        row_data: dict[str, str],
    ):
        self._row_label: str = row_label
        self._data: dict[str, str] = row_data

    def __eq__(self, other: TwoDARow | object):
        if isinstance(other, TwoDARow):
            return (self._row_label == other._row_label) and (self._data == other._data)
        else:
            return NotImplemented

    def label(
        self,
    ) -> str:
        """Returns the row label.

        Returns
        -------
            The label for the row.
        """
        return self._row_label

    def update_values(
        self,
        values: dict[str, str],
    ):
        for column, cell in values.items():
            self.set_string(column, cell)

    def get_string(
        self,
        header: str,
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
            raise KeyError(msg)
        return self._data[header]

    def get_integer(
        self,
        header: str,
        default: int | None = None,
    ) -> int:
        """Returns the integer value for the cell under the specified header. If the value of the cell is an invalid
        integer then a default value is used instead.

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

        with suppress(ValueError):
            cell = self._data[header]
            return int(cell, 16) if cell.startswith("0x") else int(cell)

    def get_float(
        self,
        header: str,
        default: int | None = None,
    ) -> float:
        """Returns the float value for the cell under the specified header. If the value of the cell is an invalid float
        then a default value is used instead.

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

    def get_enum(
        self,
        header: str,
        enum_type: type[Enum],
        default: Enum | None,
    ) -> Enum | None:
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

        value = default
        if enum_type(self._data[header]) != "":
            value = enum_type(self._data[header])
        return value

    def set_string(
        self,
        header: str,
        value: str | None,
    ) -> None:
        """Sets the value of a cell under the specified header. If the value is none it will default to a empty string.

        Args:
        ----
            header: The column header for the cell.
            value: The new cell value.

        Raises:
        ------
            KeyError: If the specified header does not exist.
        """
        if header not in self._data:
            msg = f"The header '{header}' does not exist."
            raise KeyError(msg)

        value = "" if value is None else value
        self._data[header] = value

    def set_integer(
        self,
        header: str,
        value: int | None,
    ) -> None:
        """Sets the value of a cell under the specified header, converting the integer into a string. If the value is none
        it will default to a empty string.

        Args:
        ----
            header: The column header for the cell.
            value: The new cell value.

        Raises:
        ------
            KeyError: If the specified header does not exist.
        """
        if header not in self._data:
            msg = f"The header '{header}' does not exist."
            raise KeyError(msg)

        value = "" if value is None else value
        self._data[header] = str(value)

    def set_float(
        self,
        header: str,
        value: float | None,
    ) -> None:
        """Sets the value of a cell under the specified header, converting the float into a string. If the value is none
        it will default to a empty string.

        Args:
        ----
            header: The column header for the cell.
            value: The new cell value.

        Raises:
        ------
            KeyError: If the specified header does not exist.
        """
        if header not in self._data:
            msg = f"The header '{header}' does not exist."
            raise KeyError(msg)

        value = "" if value is None else value
        self._data[header] = str(value)

    def set_enum(
        self,
        header: str,
        value: Enum | None,
    ):
        """Sets the value of a cell under the specified header, converting the enum into a string. If the value is none
        it will default to a empty string.

        Args:
        ----
            header: The column header for the cell.
            value: The new cell value.

        Raises:
        ------
            KeyError: If the specified header does not exist.
        """
        if header not in self._data:
            msg = f"The header '{header}' does not exist."
            raise KeyError(msg)

        value = "" if value is None else value.value
        self._data[header] = value
