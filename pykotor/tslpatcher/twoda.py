"""
2DA Operations:
 - Add Row
 - Change Row
 - Copy Row
 - Add Column

"""

from abc import ABC
from copy import copy
from enum import IntEnum
from typing import Dict, List, Optional, Union, Tuple, Any

from pykotor.resource.formats.twoda import TwoDA, TwoDARow
from pykotor.tslpatcher.memory import PatcherMemory


class CriticalException(Exception):
    ...


class WarningException(Exception):
    ...


class TargetType(IntEnum):
    ROW_INDEX = 0
    ROW_LABEL = 1
    LABEL_COLUMN = 2


class Target:
    def __init__(self, target_type: TargetType, value: Union[str, int]):
        self.target_type: TargetType = target_type
        self.value: Union[str, int] = value

        if target_type == TargetType.ROW_INDEX and isinstance(value, str):
            raise ValueError("Target value must be int if type is row index.")

    def search(self, twoda: TwoDA) -> Optional[TwoDARow]:
        source_row = None
        if self.target_type == TargetType.ROW_INDEX:
            source_row = twoda.get_row(self.value)
        elif self.target_type == TargetType.ROW_LABEL:
            source_row = twoda.find_row(self.value)
        elif self.target_type == TargetType.LABEL_COLUMN:
            if self.value not in twoda:
                raise WarningException()
            for row in twoda:
                if row.get_string("label") == source_row:
                    source_row = row

        return source_row


class Modifications2DA:
    def __init__(self, filename: str):
        self.filename: str = filename
        self.rows: List[Manipulation2DA] = []

    def apply(self, twoda: TwoDA, memory: PatcherMemory) -> None:
        for row in self.rows:
            row.apply(twoda, memory)


class Manipulation2DA(ABC):
    def __init__(self):
        ...

    def _split_modifiers(self, modifiers: Dict[str, str]) -> Tuple[Dict[str, str], Dict[int, str], Optional[str], Optional[str]]:
        """
        This will split the modifiers dictionary into a tuple containing three values: The dictionary mapping column
        headers to new values, the 2DA memory values if not available, and the row label or None.
        """
        new_values = {}
        memory_values = {}
        row_label = None
        new_row_label = None

        for header, value in modifiers.items():
            if header.startswith("2DAMEMORY"):
                memory_index = int(header.replace("2DAMEMORY", ""))
                memory_values[memory_index] = value
            elif header == "RowLabel":
                row_label = value
            elif header == "NewRowLabel":
                new_row_label = value
            else:
                new_values[header] = value

        return new_values, memory_values, row_label, new_row_label

    def _check_memory(self, value: Any, memory: PatcherMemory) -> Any:
        if value.startswith("2DAMEMORY"):
            value = int(value.replace("2DAMEMORY", ""))
        return value

    def apply(self, twoda: TwoDA, memory: PatcherMemory) -> None:
        ...


class ChangeRow2DA(Manipulation2DA):
    """
    Changes an existing row.

    Target row can either be the Row Index, Row Label, or value under the "label" column where applicable.

    Attributes:
        target: The row to change.
        modifiers: For the row, sets a cell under column KEY to have the text VALUE.
    """
    def __init__(self):
        super().__init__()
        self.identifier: str = ""
        self.target: Target = ...
        self.modifiers: Dict[str, str] = {}

        self._row: Optional[TwoDARow] = None

    def apply(self, twoda: TwoDA, memory: PatcherMemory) -> None:
        source_row = self.target.search(twoda)

        if source_row is None:
            raise WarningException()

        new_values, memory_values, row_label, new_row_label = self._split_modifiers(self.modifiers)
        source_row.update_values(new_values)
        self._row = source_row

        for index, value in memory_values.items():
            if value == "RowIndex":
                value = twoda.row_index(source_row)
            elif value == "RowLabel":
                value = source_row.label()
            elif value in twoda.get_headers():
                value = source_row.get_string(value)
            elif value.startswith("StrRef"):
                token = int(value[:6])
                value = memory.memory_str[token]
            elif value.startswith("2DAMEMORY"):
                token = int(value[:9])
                value = memory.memory_2da[token]

            memory.memory_2da[index] = value


class AddRow2DA(Manipulation2DA):
    """
    Adds a new row.

    Attributes:
        modifiers: For the row, sets a cell under column KEY to have the text VALUE.
    """
    def __init__(self):
        super().__init__()
        self.identifier: str = ""
        self.exclusive_column: Optional[str] = ""
        self.modifiers: Dict[str, str] = {}

        self._row: Optional[TwoDARow] = None

    def apply(self, twoda: TwoDA, memory: PatcherMemory) -> None:
        target_row = None

        if self.exclusive_column is not None:
            exclusive_value = self.modifiers[self.exclusive_column]
            for row in twoda:
                if row.get_string(self.exclusive_column) == exclusive_value:
                    target_row = row

        new_values, memory_values, row_label, new_row_label = self._split_modifiers(self.modifiers)

        if target_row is None:
            index = twoda.add_row(row_label, new_values)
            self._row = twoda.get_row(index)
        else:
            target_row.update_values(new_values)

        for index, value in memory_values.items():
            if value == "RowIndex":
                value = index
            elif value.startswith("StrRef"):
                token = int(value[:6])
                value = memory.memory_str[token]
            elif value.startswith("2DAMEMORY"):
                token = int(value[:9])
                value = memory.memory_2da[token]
            memory.memory_2da[index] = value


class CopyRow2DA(Manipulation2DA):
    """
    Copies the the row if the exclusive_column value doesn't already exist. If it does, then it simply modifies the
    existing line.

    Attributes:
        identifier:
        target: Which row to copy.
        exclusive_column: Modify existing line if the same value already exists at this column.
        modifiers: For the row, sets a cell under column KEY to have the text VALUE.
    """
    def __init__(self):
        super().__init__()
        self.identifier: str = ""
        self.target: Target = ...
        self.exclusive_column: Optional[str] = ""
        self.modifiers: Dict[str, str] = {}

        self._row: Optional[TwoDARow] = None

    def apply(self, twoda: TwoDA, memory: PatcherMemory) -> None:
        source_row = self.target.search(twoda)

        #if self.exclusive_column is not None and self.exclusive_column not in twoda:
        #    raise ValueError()

        # Check if the row we want already exists.
        exclusive_value = self.modifiers[self.exclusive_column]
        target_row = None
        for row in twoda:
            if row.get_string(self.exclusive_column) == exclusive_value:
                target_row = row

        # Determine the the row label for the copied row.
        # Has no effect if it updates an existing row instead.
        new_values, memory_values, row_label, new_row_label = self._split_modifiers(self.modifiers)
        if row_label is None:
            row_label = str(twoda.get_height())
        if new_row_label is not None:
            row_label = new_row_label

        if target_row is not None:
            # If the row already exists (based on exclusive_column) then we update the cells
            target_row.update_values(new_values)
            self._row = target_row
        else:
            # Otherwise we add the a new row instead.
            index = twoda.add_row(row_label, new_values)
            self._row = twoda.get_row(index)

        for index, value in memory_values.items():
            if value == "RowIndex":
                value = twoda.row_index(source_row)
            elif value == "RowLabel":
                value = source_row.label()
            elif value in twoda.get_headers():
                value = source_row.get_string(value)
            elif value.startswith("StrRef"):
                token = int(value[:6])
                value = memory.memory_str[token]
            elif value.startswith("2DAMEMORY"):
                token = int(value[:9])
                value = memory.memory_2da[token]
            memory.memory_2da[index] = value


class AddColumn2DA(Manipulation2DA):
    """
    Adds a column. The new cells are either given a default value or can be given a value based on what the row index
    or row label is.

    Attributes:
        identifier:
        header: Label for the name column.
        default: Default value of cells if no specific value was specified.
        index_insert: For the new column, if the row index is KEY then set cell to VALUE.
        label_insert: For the new column, if the row label is KEY then set cell to VALUE.
    """

    def __init__(self):
        super().__init__()
        self.identifier: str = ""
        self.header: str = ""
        self.default: str = ""
        self.index_insert: Dict[int, str] = {}
        self.label_insert: Dict[str, str] = {}
        self.memory_saves: Dict[int, str] = {}

    def apply(self, twoda: TwoDA, memory: PatcherMemory) -> None:
        twoda.add_column(self.header)
        for row in twoda:
            row.set_string(self.header, self.default)

        for row_index, value in self.index_insert.items():
            value = self._check_memory(value, memory)
            twoda.get_row(row_index).set_string(self.header, value)

        for row_label, value in self.label_insert.items():
            value = self._check_memory(value, memory)
            twoda.find_row(row_label).set_string(self.header, value)

        for memory_index, value in self.memory_saves.items():
            if value.startswith("StrRef"):
                token = int(value[:6])
                value = memory.memory_str[token]
            elif value.startswith("2DAMEMORY"):
                token = int(value[:9])
                value = memory.memory_2da[token]

            if value.startswith("I"):
                # TODO: Exception handling
                cell = twoda.get_row(int(value[1:])).get_string(self.header)
                memory.memory_2da[memory_index] = cell
            elif value.startswith("L"):
                cell = twoda.find_row(value[1:]).get_string(self.header)
                memory.memory_2da[memory_index] = cell
            else:
                raise WarningException()
