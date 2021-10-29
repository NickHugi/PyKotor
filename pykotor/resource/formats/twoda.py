"""
This module handles classes relating to editing 2DA files.
"""
from __future__ import annotations

from contextlib import suppress
from copy import copy
from enum import Enum
from typing import List, Dict, Optional, Type, Any


class TwoDA:
    """
    Represents the data of a 2DA file.
    """

    def __init__(self):
        self._rows: List[Dict[str, str]] = []
        self._headers: List[str] = []

    def get_headers(self) -> List[str]:
        """
        Returns a copy of the set of column headers.

        Returns:
            The column headers.
        """
        return copy(self._headers)

    def get_column(self, header: str) -> List[str]:
        """
        Returns every cell listed under the specified column header.

        Args:
            header: The column header.

        Raises:
            KeyError: If the specified column header does not exist.

        Returns:
            A list of cells.
        """
        if header not in self._headers:
            raise KeyError("The header '{}' does not exist.".format(header))

        return [self._rows[i][header] for i in range(self.get_height())]

    def add_column(self, header: str, cell: str = "") -> None:
        """
        Adds a new column header and sets the new cells values under the new header.

        Args:
            header: The header name of the new column.
            cell: The value of the new cells under the header.

        Raises:
            KeyError: If the specified column header already exists.
        """

        if header in self._headers:
            raise KeyError("The header '{}' already exists.".format(header))

        self._headers.append(header)
        for row in self._rows:
            row[header] = cell

    def remove_column(self, header: str) -> None:
        """
        Removes a column from the table with the specified column header if it exists.

        Args:
            header: The column header.
        """
        if header in self._headers:
            for row in self._rows:
                row.pop(header)

        self._headers.remove(header)

    def get_row(self, row_id: int) -> TwoDARow:
        """
        Returns the row at the specified row id.

        Args:
            row_id: The row id.

        Raises:
            IndexError: If the specified row does not exist.

        Returns:
            The corresponding TwoDARow object.
        """
        return TwoDARow(self._rows[row_id])

    def add_row(self, cells: Dict[str, Any] = None) -> int:
        """
        Adds a new row to the end of the table. Headers specified in the cells parameter that do not exist in the table
        itself will be ignored, headers that are not specified in the cells parameter but do exist in the table will
        default to being blank. All cells are converted to strings before being added into the 2DA.

        Args:
            cells: A dictionary representing the cells of the new row. A key is the header and value is the cell.

        Returns:
            The id of the new row.
        """
        self._rows.append({})

        if cells is None:
            cells = {}

        for header in cells:
            cells[header] = str(cells[header])

        for header in self._headers:
            self._rows[-1][header] = cells[header] if header in cells else ""

        return len(self._rows) - 1

    def get_cell(self, row_id, column: str) -> str:
        """
        Returns the value of the cell at the specified row under the specified column.

        Args:
            row_id: The row id.
            column: The column header.

        Raises:
            KeyError: If the specified column does not exist.
            IndexError: If the specified row does not exist.

        Returns:
            The cell value.
        """
        return self._rows[row_id][column]

    def set_cell(self, row_id: int, column: str, value: Any) -> None:
        """
        Sets the value of a cell at the specified row under the specified column. If the value is none, it will output a
        blank string.

        Args:
            row_id: The row id.
            column: The column header.
            value: The new value of the target cell.

        Raises:
            KeyError: If the specified column does not exist.
            IndexError: If the specified row does not exist.
        """
        value = "" if value is None else value
        self._rows[row_id][column] = str(value)

    def get_height(self) -> int:
        """
        Returns the number of rows in the table.

        Returns:
            The number of rows.
        """
        return len(self._rows)

    def set_height(self, height: int) -> None:
        """
        Sets the number of rows in the table. Use with caution; specifying a height less than the current height will
        result in a loss of data.

        Args:
            height: The number of rows to set.

        Raises:
            ValueError: If the height is negative.
        """

        if self.get_height() < 0:
            raise ValueError("The height of the table cannot be negative.")
        current_height = len(self._rows)

        if height < current_height:
            # trim the _rows list
            self._rows = self._rows[:height]
        else:
            # insert the new rows with each cell filled in blank
            for i in range(height-current_height):
                self.add_row()

    def get_width(self) -> int:
        """
        Returns the number of columns in the table.

        Returns:
            The number of columns.
        """
        return len(self._headers)


class TwoDARow:
    def __init__(self, row_data: Dict[str, str]):
        self._data: Dict[str, str] = row_data

    def get_integer(self, header: str, default: Optional[int] = None) -> Optional[int]:
        """
        Returns an integer for the cell under the specified header, if the value is not a valid integer than it returns
        the default value instead.

        Args:
            header: The header that the cell is under.
            default: The value returned in the event of a invalid integer.

        Raises:
            KeyError: If the specified header does not exist.

        Returns:
            An integer.
        """
        if header not in self._data:
            raise KeyError()

        value = default
        with suppress(Exception):
            cell = self._data[header]
            if cell.startswith("0x"):
                value = int(cell, 16)
            else:
                value = int(cell)
        return value

    def get_float(self, header: str, default: Optional[float] = None) -> Optional[float]:
        """
        Returns a float for the cell under the specified header, if the value is not a valid float than it returns
        the default value instead.

        Args:
            header: The header that the cell is under.
            default: The value returned in the event of a invalid float.

        Raises:
            KeyError: If the specified header does not exist.

        Returns:
            A float.
        """
        if header not in self._data:
            raise KeyError()

        value = default
        with suppress(Exception):
            cell = self._data[header]
            value = float(cell)
        return value

    def get_string(self, header: str, default: Optional[str] = None) -> Optional[str]:
        """
        Returns a string for the cell under the specified header, if the value is an empty string than it returns
        the default value instead.

        Args:
            header: The header that the cell is under.
            default: The value returned in the event of a blank string.

        Raises:
            KeyError: If the specified header does not exist.

        Returns:
            A string.
        """
        if header not in self._data:
            raise KeyError()

        return self._data[header] if self._data[header] != "" else default

    def get_enum(self, header: str, enum_type: Type[Enum], default: Optional[Enum] = None) -> Optional[Enum]:
        """
        Returns a enum for the cell under the specified header for the given enum. If the value does not match any
        existing enum entry then it returns the default value instead.

        Args:
            header: The header that the cell is under.
            enum_type: The enum class to look through.
            default: The value returned in the event of the value not existing in the given enum.

        Raises:
            KeyError: If the specified header does not exist.

        Returns:
            Returns an enum.
        """
        if header not in self._data:
            raise KeyError()

        value = default
        with suppress(Exception):
            value = enum_type(self._data[header])
        return value

    def set_integer(self, header: str, value: Optional[int]) -> None:
        """
        Sets the string value of a cell based of the given integer, if the integer is None then the string is blank.

        Args:
            header: The header that the cell is under.
            value: The value to be converted into the cell.

        Raises:
            KeyError: If the specified header does not exist.
        """
        if header not in self._data:
            raise KeyError()

        value = "" if value is None else value
        self._data[header] = str(value)

    def set_float(self, header: str, value: Optional[float]):
        """
        Sets the string value of a cell based of the given float, if the float is None then the string is blank.

        Args:
            header: The header that the cell is under.
            value: The value to be converted into the cell.

        Raises:
            KeyError: If the specified header does not exist.
        """
        if header not in self._data:
            raise KeyError()

        value = "" if value is None else value
        self._data[header] = str(value)

    def set_string(self, header: str, value: Optional[str]):
        """
        Sets the string value of a cell based of the given string, if the string is None then the cell string is blank.

        Args:
            header: The header that the cell is under.
            value: The value to be converted into the cell.

        Raises:
            KeyError: If the specified header does not exist.
        """

        if header not in self._data:
            raise KeyError()

        value = "" if value is None else value
        self._data[header] = value

    def set_enum(self, header: str, value: Optional[Enum]):
        """
        Sets the string value of a cell based of the given enum, if the enum is None then the string is blank.

        Args:
            header: The header that the cell is under.
            value: The value to be converted into the cell.

        Raises:
            KeyError: If the specified header does not exist.
        """
        if header not in self._data:
            raise KeyError()

        value = "" if value is None else value
        self._data[header] = str(value.value)
