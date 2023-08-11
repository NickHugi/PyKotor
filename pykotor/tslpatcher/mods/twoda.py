from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Any

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
    def __init__(self, target_type: TargetType, value: str | int):
        self.target_type: TargetType = target_type
        self.value: str | int = value

        if target_type == TargetType.ROW_INDEX and isinstance(value, str):
            msg = "Target value must be int if type is row index."
            raise ValueError(msg)

    def search(self, twoda: TwoDA) -> TwoDARow | None:
        source_row: TwoDARow | None = None
        if self.target_type == TargetType.ROW_INDEX:
            source_row = twoda.get_row(int(self.value))
        elif self.target_type == TargetType.ROW_LABEL:
            source_row = twoda.find_row(str(self.value))
        elif self.target_type == TargetType.LABEL_COLUMN:
            if "label" not in twoda.get_headers():
                raise WarningException
            if self.value not in twoda.get_column("label"):
                raise WarningException
            for row in twoda:
                if row.get_string("label") == self.value:
                    source_row = row

        return source_row


class Modifications2DA:
    def __init__(self, filename: str):
        self.filename: str = filename
        self.modifiers: list[Modify2DA] = []

    def apply(self, twoda: TwoDA, memory: PatcherMemory) -> None:
        for row in self.modifiers:
            row.apply(twoda, memory)


# region Value Returners
class RowValue(ABC):
    @abstractmethod
    def value(self, memory: PatcherMemory, twoda: TwoDA, row: TwoDARow | None) -> str:
        ...


class RowValueConstant(RowValue):
    def __init__(self, string: str):
        self.string = string

    def value(self, memory: PatcherMemory, twoda: TwoDA, row: TwoDARow | None) -> str:
        return self.string


class RowValue2DAMemory(RowValue):
    def __init__(self, token_id: int):
        self.token_id = token_id

    def value(self, memory: PatcherMemory, twoda: TwoDA, row: TwoDARow | None) -> str:
        return memory.memory_2da[self.token_id]


class RowValueTLKMemory(RowValue):
    def __init__(self, token_id: int):
        self.token_id = token_id

    def value(self, memory: PatcherMemory, twoda: TwoDA, row: TwoDARow | None) -> str:
        return str(memory.memory_str[self.token_id])


class RowValueHigh(RowValue):
    """Attributes
    column: Column to get the max integer from. If None it takes it from the Row Label.
    """

    def __init__(self, column: str | None):
        self.column: str | None = column

    def value(self, memory: PatcherMemory, twoda: TwoDA, row: TwoDARow | None) -> str:
        return (
            str(twoda.column_max(self.column))
            if self.column is not None
            else str(twoda.label_max())
        )


class RowValueRowIndex(RowValue):
    def __init__(self):
        ...

    def value(self, memory: PatcherMemory, twoda: TwoDA, row: TwoDARow | None) -> str:
        return str(twoda.row_index(row)) if row is not None else ""


class RowValueRowLabel(RowValue):
    def __init__(self):
        ...

    def value(self, memory: PatcherMemory, twoda: TwoDA, row: TwoDARow | None) -> str:
        return row.label()


class RowValueRowCell(RowValue):
    def __init__(self, column: str):
        self.column: str = column

    def value(self, memory: PatcherMemory, twoda: TwoDA, row: TwoDARow | None) -> str:
        return row.get_string(self.column) if row is not None else ""


# endregion


# region Modify 2DA
class Modify2DA(ABC):
    def __init__(self):
        ...

    def _unpack(
        self,
        cells: dict[str, RowValue],
        memory: PatcherMemory,
        twoda: TwoDA,
        row: TwoDARow,
    ) -> dict[str, str]:
        return {
            column: value.value(memory, twoda, row) for column, value in cells.items()
        }

    def _split_modifiers(
        self,
        modifiers: dict[str, str],
        memory: PatcherMemory,
        twoda: TwoDA,
    ) -> tuple[dict[str, str], dict[int, str], str | None, str | None]:
        """This will split the modifiers dictionary into a tuple containing three values: The dictionary mapping column
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

        # Break apart values into more manageable categories
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
        memory: PatcherMemory,
    ) -> Any:
        if value.startswith("2DAMEMORY"):
            value = int(value.replace("2DAMEMORY", ""))
        return value

    def apply(
        self,
        twoda: TwoDA,
        memory: PatcherMemory,
    ) -> None:
        ...


class ChangeRow2DA(Modify2DA):
    """Changes an existing row.

    Target row can either be the Row Index, Row Label, or value under the "label" column where applicable.

    Attributes
    ----------
        target: The row to change.
        modifiers: For the row, sets a cell under column KEY to have the text VALUE.
    """

    def __init__(
        self,
        identifier: str,
        target: Target,
        cells: dict[str, RowValue],
        store_2da: dict[int, RowValue] | None = None,
        store_tlk: dict[int, RowValue] | None = None,
    ):
        super().__init__()
        self.identifier: str = identifier
        self.target: Target = target
        self.cells: dict[str, RowValue] = cells
        self.store_2da: dict[int, RowValue] = {} if store_2da is None else store_2da
        self.store_tlk: dict[int, RowValue] = {} if store_tlk is None else store_tlk

        self._row: TwoDARow | None = None

    def apply(self, twoda: TwoDA, memory: PatcherMemory) -> None:
        source_row = self.target.search(twoda)

        if source_row is None:
            raise WarningException

        cells = self._unpack(self.cells, memory, twoda, source_row)
        source_row.update_values(cells)

        for token_id, value in self.store_2da.items():
            memory.memory_2da[token_id] = value.value(memory, twoda, source_row)

        for token_id, value in self.store_tlk.items():
            memory.memory_str[token_id] = int(value.value(memory, twoda, source_row))


class AddRow2DA(Modify2DA):
    """Adds a new row.

    Attributes
    ----------
        modifiers: For the row, sets a cell under column KEY to have the text VALUE.
    """

    def __init__(
        self,
        identifier: str,
        exclusive_column: str | None,
        row_label: str | None,
        cells: dict[str, RowValue],
        store_2da: dict[int, RowValue] | None = None,
        store_tlk: dict[int, RowValue] | None = None,
    ):
        super().__init__()
        self.identifier: str = identifier
        self.exclusive_column: str | None = (
            exclusive_column if exclusive_column != "" else None
        )
        self.row_label: str | None = row_label
        self.cells: dict[str, RowValue] = cells
        self.store_2da: dict[int, RowValue] = {} if store_2da is None else store_2da
        self.store_tlk: dict[int, RowValue] = {} if store_tlk is None else store_tlk

        self._row: TwoDARow | None = None

    def apply(self, twoda: TwoDA, memory: PatcherMemory) -> None:
        target_row = None

        if self.exclusive_column is not None:
            if self.exclusive_column not in self.cells:
                msg = f"Exclusive column {self.exclusive_column} does not exists"
                raise WarningException(
                    msg,
                )

            exclusive_value = self.cells[self.exclusive_column].value(
                memory, twoda, None
            )
            for row in twoda:
                if row.get_string(self.exclusive_column) == exclusive_value:
                    target_row = row

        if target_row is None:
            row_label = (
                str(twoda.get_height()) if self.row_label is None else self.row_label
            )
            index = twoda.add_row(row_label, {})
            self._row = target_row = twoda.get_row(index)
            target_row.update_values(
                self._unpack(self.cells, memory, twoda, target_row)
            )
        else:
            cells = self._unpack(self.cells, memory, twoda, target_row)
            target_row.update_values(cells)

        for token_id, value in self.store_2da.items():
            memory.memory_2da[token_id] = value.value(memory, twoda, target_row)

        for token_id, value in self.store_tlk.items():
            memory.memory_str[token_id] = int(value.value(memory, twoda, target_row))


class CopyRow2DA(Modify2DA):
    """Copies the the row if the exclusive_column value doesn't already exist. If it does, then it simply modifies the
    existing line.

    Attributes
    ----------
        identifier:
        target: Which row to copy.
        exclusive_column: Modify existing line if the same value already exists at this column.
        modifiers: For the row, sets a cell under column KEY to have the text VALUE.
    """

    def __init__(
        self,
        identifier: str,
        target: Target,
        exclusive_column: str | None,
        row_label: str | None,
        cells: dict[str, RowValue],
        store_2da: dict[int, RowValue] | None = None,
        store_tlk: dict[int, RowValue] | None = None,
    ):
        super().__init__()
        self.identifier: str = identifier
        self.target: Target = target
        self.exclusive_column: str | None = (
            exclusive_column if exclusive_column != "" else None
        )
        self.row_label: str | None = row_label
        self.cells: dict[str, RowValue] = cells
        self.store_2da: dict[int, RowValue] = {} if store_2da is None else store_2da
        self.store_tlk: dict[int, RowValue] = {} if store_tlk is None else store_tlk

        self._row: TwoDARow | None = None

    def apply(self, twoda: TwoDA, memory: PatcherMemory) -> None:
        source_row = self.target.search(twoda)
        target_row = None
        row_label = (
            str(twoda.get_height()) if self.row_label is None else self.row_label
        )

        if source_row is None:
            raise WarningException

        if self.exclusive_column is not None:
            if self.exclusive_column not in self.cells:
                msg = f"Exclusive column {self.exclusive_column} does not exists"
                raise WarningException(
                    msg,
                )

            exclusive_value = self.cells[self.exclusive_column].value(
                memory, twoda, None
            )
            for row in twoda:
                if row.get_string(self.exclusive_column) == exclusive_value:
                    target_row = row

        if target_row is not None:
            # If the row already exists (based on exclusive_column) then we update the cells
            cells = self._unpack(self.cells, memory, twoda, target_row)
            target_row.update_values(cells)
            self._row = target_row
        else:
            # Otherwise, we add the new row instead.
            index = twoda.copy_row(source_row, row_label, {})
            self._row = target_row = twoda.get_row(index)
            cells = self._unpack(self.cells, memory, twoda, target_row)
            target_row.update_values(cells)

        for token_id, value in self.store_2da.items():
            memory.memory_2da[token_id] = value.value(memory, twoda, target_row)

        for token_id, value in self.store_tlk.items():
            memory.memory_str[token_id] = int(value.value(memory, twoda, target_row))


class AddColumn2DA(Modify2DA):
    """Adds a column. The new cells are either given a default value or can be given a value based on what the row index
    or row label is.

    Attributes
    ----------
        identifier:
        header: Label for the name column.
        default: Default value of cells if no specific value was specified.
        index_insert: For the new column, if the row index is KEY then set cell to VALUE.
        label_insert: For the new column, if the row label is KEY then set cell to VALUE.
    """

    def __init__(
        self,
        identifier: str,
        header: str,
        default: str,
        index_insert: dict[int, RowValue],
        label_insert: dict[str, RowValue],
        store_2da: dict[int, str] | None = None,
    ):
        super().__init__()
        self.identifier: str = identifier
        self.header: str = header
        self.default: str = default
        self.index_insert: dict[int, RowValue] = index_insert
        self.label_insert: dict[str, RowValue] = label_insert
        self.store_2da: dict[int, str] = {} if store_2da is None else store_2da

    def apply(self, twoda: TwoDA, memory: PatcherMemory) -> None:
        twoda.add_column(self.header)
        for row in twoda:
            row.set_string(self.header, self.default)

        for row_index, value in self.index_insert.items():
            index_str: str = value.value(memory, twoda, None)
            this_row = twoda.get_row(row_index)
            if this_row:
                this_row.set_string(self.header, index_str)
            else:
                msg = f"Could not find row {row_index} in {self.header}"
                raise WarningException(msg)

        for row_label, value in self.label_insert.items():
            label_str: str = value.value(memory, twoda, None)
            this_row = twoda.find_row(row_label)
            if this_row:
                this_row.set_string(self.header, label_str)
            else:
                msg = f"Could not find row {row_label} in {self.header}"
                raise WarningException(msg)

        for token_id, value in self.store_2da.items():
            # TODO: Exception handling
            if value.startswith("I"):
                cell = twoda.get_row(int(value[1:])).get_string(self.header)
                memory.memory_2da[token_id] = cell
            elif value.startswith("L"):
                cell = twoda.find_row(value[1:]).get_string(self.header)
                memory.memory_2da[token_id] = cell
            else:
                raise WarningException


# endregion
