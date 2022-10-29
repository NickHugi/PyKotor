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
            if "label" not in twoda.get_headers():
                raise WarningException()
            if self.value not in twoda.get_column("label"):
                raise WarningException()
            for row in twoda:
                if row.get_string("label") == self.value:
                    source_row = row

        return source_row


class Modifications2DA:
    def __init__(self, filename: str):
        self.filename: str = filename
        self.rows: List[ManipulateRow2DA] = []

    def apply(self, twoda: TwoDA, memory: PatcherMemory) -> None:
        for row in self.rows:
            row.apply(twoda, memory)


class ManipulateRow2DA(ABC):
    def __init__(self):
        ...

    def _split_modifiers(
            self,
            modifiers: Dict[str, str],
            memory: PatcherMemory,
            twoda: TwoDA
    ) -> Tuple[Dict[str, str], Dict[int, str], Optional[str], Optional[str]]:
        """
        This will split the modifiers dictionary into a tuple containing three values: The dictionary mapping column
        headers to new values, the 2DA memory values if not available, and the row label or None.
        """
        new_values = {}
        memory_values = {}
        row_label = None
        new_row_label = None

        # Update special values
        for header, value in modifiers.items():
            if value.startswith("StrRef"):
                token_id = int(value[6:])
                modifiers[header] = str(memory.memory_str[token_id])
            elif value.startswith("2DAMEMORY"):
                token_id = int(value[9:])
                modifiers[header] = str(memory.memory_2da[token_id])
            elif value == "high()":
                modifiers[header] = str(twoda.column_max(header))

        # Break apart values into more managable categories
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

    def _check_memory(
            self,
            value: Any,
            memory: PatcherMemory
    ) -> Any:
        if value.startswith("2DAMEMORY"):
            value = int(value.replace("2DAMEMORY", ""))
        return value

    def apply(
            self,
            twoda: TwoDA,
            memory: PatcherMemory
    ) -> None:
        ...


class ChangeRow2DA(ManipulateRow2DA):
    """
    Changes an existing row.

    Target row can either be the Row Index, Row Label, or value under the "label" column where applicable.

    Attributes:
        target: The row to change.
        modifiers: For the row, sets a cell under column KEY to have the text VALUE.
    """
    def __init__(self, identifier: str, target: Target, modifiers: Dict[str, str]):
        super().__init__()
        self.identifier: str = identifier
        self.target: Target = target
        self.modifiers: Dict[str, str] = modifiers

        self._row: Optional[TwoDARow] = None

    def apply(self, twoda: TwoDA, memory: PatcherMemory) -> None:
        source_row = self.target.search(twoda)

        if source_row is None:
            raise WarningException()

        new_values, memory_values, row_label, new_row_label = self._split_modifiers(self.modifiers, memory, twoda)
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


class AddRow2DA(ManipulateRow2DA):
    """
    Adds a new row.

    Attributes:
        modifiers: For the row, sets a cell under column KEY to have the text VALUE.
    """
    def __init__(self, identifier: str, exclusive_column: Optional[str], modifiers: Dict[str, str]):
        super().__init__()
        self.identifier: str = identifier
        self.exclusive_column: Optional[str] = exclusive_column
        self.modifiers: Dict[str, str] = modifiers

        self._row: Optional[TwoDARow] = None

    def apply(self, twoda: TwoDA, memory: PatcherMemory) -> None:
        target_row = None
        self.exclusive_column = self.exclusive_column if self.exclusive_column != "" else None

        if self.exclusive_column is not None:
            if self.exclusive_column not in self.modifiers:
                raise WarningException("Exclusive column {} does not exists".format(self.exclusive_column))
            exclusive_value = self.modifiers[self.exclusive_column]
            for row in twoda:
                if row.get_string(self.exclusive_column) == exclusive_value:
                    target_row = row

        new_values, memory_values, row_label, new_row_label = self._split_modifiers(self.modifiers, memory, twoda)

        if target_row is None:
            index = twoda.add_row(row_label, new_values)
            self._row = target_row = twoda.get_row(index)
        else:
            target_row.update_values(new_values)

        for index, value in memory_values.items():
            if value == "RowIndex":
                value = twoda.row_index(target_row)
            elif value.startswith("StrRef"):
                token = int(value[:6])
                value = memory.memory_str[token]
            elif value.startswith("2DAMEMORY"):
                token = int(value[:9])
                value = memory.memory_2da[token]
            memory.memory_2da[index] = value


class CopyRow2DA(ManipulateRow2DA):
    """
    Copies the the row if the exclusive_column value doesn't already exist. If it does, then it simply modifies the
    existing line.

    Attributes:
        identifier:
        target: Which row to copy.
        exclusive_column: Modify existing line if the same value already exists at this column.
        modifiers: For the row, sets a cell under column KEY to have the text VALUE.
    """
    def __init__(self, identifier: str, target: Target, exclusive_column: Optional[str], modifiers: Dict[str, str]):
        super().__init__()
        self.identifier: str = identifier
        self.target: Target = target
        self.exclusive_column: Optional[str] = exclusive_column
        self.modifiers: Dict[str, str] = modifiers

        self._row: Optional[TwoDARow] = None

    def apply(self, twoda: TwoDA, memory: PatcherMemory) -> None:
        source_row = self.target.search(twoda)

        if source_row is None:
            raise WarningException()

        # Check if the row we want already exists.
        target_row = None
        self.exclusive_column = self.exclusive_column if self.exclusive_column != "" else None
        if self.exclusive_column is not None:
            if self.exclusive_column not in self.modifiers:
                raise WarningException("Exclusive column {} does not exists".format(self.exclusive_column))
            exclusive_value = self.modifiers[self.exclusive_column]
            for row in twoda:
                if row.get_string(self.exclusive_column) == exclusive_value:
                    target_row = row

        # Determine the row label for the copied row.
        # Has no effect if it updates an existing row instead.
        new_values, memory_values, row_label, new_row_label = self._split_modifiers(self.modifiers, memory, twoda)
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
            index = twoda.copy_row(source_row, row_label, new_values)
            self._row = target_row = twoda.get_row(index)

        for index, value in memory_values.items():
            if value == "RowIndex":
                value = twoda.row_index(target_row)
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


class AddColumn2DA(ManipulateRow2DA):
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

    def __init__(self, identifier: str, header: str, default: str, index_insert: Dict[int, str], label_insert: Dict[str, str], memory_saves: Dict[int, str]):
        super().__init__()
        self.identifier: str = identifier
        self.header: str = header
        self.default: str = default
        self.index_insert: Dict[int, str] = index_insert
        self.label_insert: Dict[str, str] = label_insert
        self.memory_saves: Dict[int, str] = memory_saves

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
