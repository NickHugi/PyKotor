"""2DA modification algorithms for TSLPatcher/HoloPatcher.

This module implements 2DA modification logic for applying patches from changes.ini files.
Handles row/column additions, cell modifications, and memory token resolution.

References:
----------
    vendor/TSLPatcher/TSLPatcher.pl - Original Perl 2DA modification logic
    vendor/HoloPatcher.NET/src/TSLPatcher.Core/Mods/2DA/ - C# 2DA modification implementation
    vendor/Kotor.NET/Kotor.NET.Patcher/ - Incomplete C# patcher
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import IntEnum
from pathlib import PureWindowsPath
from typing import TYPE_CHECKING, Mapping

from loggerplus import RobustLogger

from pykotor.resource.formats.twoda import bytes_2da, read_2da
from pykotor.tslpatcher.mods.template import PatcherModifications
from utility.error_handling import universal_simplify_exception

if TYPE_CHECKING:
    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from pykotor.common.misc import Game
    from pykotor.resource.formats.twoda import TwoDA, TwoDARow
    from pykotor.resource.type import SOURCE_TYPES
    from pykotor.tslpatcher.logger import PatchLogger
    from pykotor.tslpatcher.memory import PatcherMemory


class CriticalError(Exception): ...


class WarningError(Exception): ...


class TargetType(IntEnum):
    ROW_INDEX = 0
    ROW_LABEL = 1
    LABEL_COLUMN = 2


class Target:
    def __init__(
        self,
        target_type: TargetType,
        value: str | int | RowValue2DAMemory | RowValueTLKMemory,
    ):
        self.target_type: TargetType = target_type
        self.value: str | int | RowValueTLKMemory | RowValue2DAMemory = value

        if target_type == TargetType.ROW_INDEX and isinstance(value, str):
            msg = "Target value must be int if type is row index."
            raise ValueError(msg)

    def __str__(self):
        value_str = str(self.value)
        class_name = self.value.__class__.__name__
        if class_name in ("RowValue2DAMemory", "RowValueTLKMemory"):
            value_str = repr(self.value)
        type_names = {
            TargetType.ROW_INDEX: "row index",
            TargetType.ROW_LABEL: "row label",
            TargetType.LABEL_COLUMN: "label column",
        }
        type_name = type_names.get(self.target_type, self.target_type.name)
        return f"Target({type_name}={value_str})"

    def __repr__(self):
        return f"{self.__class__.__name__}(target_type={self.target_type.__class__.__name__}.{self.target_type.name}, value={self.value!r})"

    def search(
        self,
        twoda: TwoDA,
        memory: PatcherMemory,
    ) -> TwoDARow | None:
        """Searches a TwoDA for a row matching the target.

        Args:
        ----
            twoda: TwoDA - The TwoDA to search
            memory: PatcherMemory - The memory context

        Returns:
        -------
            TwoDARow | None - The matching row if found, else None

        Processing Logic:
        ----------------
            - Checks target_type and searches twoda accordingly
            - For row index, gets row directly
            - For row label, finds row by label
            - For label column, checks for label column, then iterates rows to find match
            - Returns matching row or None.
        """
        value: str | int = (
            self.value.value(memory, twoda, None)
            if isinstance(self.value, (RowValueTLKMemory, RowValue2DAMemory))
            else self.value
        )
        source_row: TwoDARow | None = None
        if self.target_type == TargetType.ROW_INDEX:
            source_row = twoda.get_row(int(value))
        elif self.target_type == TargetType.ROW_LABEL:
            source_row = twoda.find_row(str(value))
        elif self.target_type == TargetType.LABEL_COLUMN:
            if "label" not in twoda.get_headers():
                msg = f"'label' could not be found in the twoda's headers: ({self.target_type.name}, {value})"
                raise WarningError(msg)
            if value not in twoda.get_column("label"):
                msg = f"The value '{value}' could not be found in the twoda's columns"
                raise WarningError(msg)
            for row in twoda:
                if row.get_string("label") == value:
                    source_row = row

        return source_row


# region Value Returners
class RowValue(ABC):
    def __str__(self):
        return f"{self.__class__.__name__}()"

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    @abstractmethod
    def value(self, memory: PatcherMemory, twoda: TwoDA, row: TwoDARow | None) -> str:
        """Returns the value of the row.

        Args:
        ----
            memory: PatcherMemory - The memory context
            twoda: TwoDA - The TwoDA to search
            row: TwoDARow | None - The row to search
        """


class RowValueConstant(RowValue):
    def __init__(self, string: str):
        self.string: str = string

    def __str__(self):
        return f"Constant('{self.string}')"

    def __repr__(self):
        return f"{self.__class__.__name__}(string='{self.string}')"

    def value(self, memory: PatcherMemory, twoda: TwoDA, row: TwoDARow | None) -> str:
        return self.string


class RowValue2DAMemory(RowValue):
    def __init__(self, token_id: int):
        self.token_id: int = token_id

    def __str__(self):
        return f"2DAMEMORY{self.token_id}"

    def __repr__(self):
        return f"{self.__class__.__name__}(token_id={self.token_id})"

    def value(self, memory: PatcherMemory, twoda: TwoDA, row: TwoDARow | None) -> str:
        memory_val: str | PureWindowsPath | None = memory.memory_2da.get(self.token_id)
        if memory_val is None:
            msg = f"2DAMEMORY{self.token_id} was not defined before use."
            raise KeyError(msg)
        if isinstance(memory_val, PureWindowsPath):
            msg = f"!FieldPath cannot be used in 2DAList patches, got '{memory_val}'"
            raise TypeError(msg)
        return memory_val


class RowValueTLKMemory(RowValue):
    def __init__(self, token_id: int):
        self.token_id: int = token_id

    def __str__(self):
        return f"StrRef{self.token_id}"

    def __repr__(self):
        return f"{self.__class__.__name__}(token_id={self.token_id})"

    def value(self, memory: PatcherMemory, twoda: TwoDA, row: TwoDARow | None) -> str:
        memory_val: int | None = memory.memory_str.get(self.token_id)
        if memory_val is None:
            msg = f"StrRef{self.token_id} was not defined before use."
            raise KeyError(msg)
        return str(memory_val)


class RowValueHigh(RowValue):
    """
    Attributes:
    ----------
    column: Column to get the max integer from. If None it takes it from the Row Label.
    """  # noqa: D212, D415

    def __init__(self, column: str | None):
        self.column: str | None = column

    def __str__(self):
        if self.column is None:
            return "High(label_max)"
        return f"High(column_max('{self.column}'))"

    def __repr__(self):
        return f"{self.__class__.__name__}(column='{self.column}')"

    def value(self, memory: PatcherMemory, twoda: TwoDA, row: TwoDARow | None) -> str:
        """Returns the maximum value in a column or overall label.

        Args:
        ----
            memory: PatcherMemory object
            twoda: TwoDA object
            row: TwoDARow object or None

        Returns:
        -------
            str: String representation of maximum value

        Processing Logic:
        ----------------
            - If column is not None, return maximum value in that column
            - Else return overall maximum label value.
        """
        return str(twoda.label_max()) if self.column is None else str(twoda.column_max(self.column))


class RowValueRowIndex(RowValue):
    """The row index of the row."""
    def __init__(self): ...

    def __str__(self):
        return "RowIndex()"

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def value(self, memory: PatcherMemory, twoda: TwoDA, row: TwoDARow | None) -> str:
        return "" if row is None else str(twoda.row_index(row))


class RowValueRowLabel(RowValue):
    """The row label of the row."""
    def __init__(self): ...

    def __str__(self):
        return "RowLabel()"

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def value(self, memory: PatcherMemory, twoda: TwoDA, row: TwoDARow | None) -> str:
        return "" if row is None else row.label()


class RowValueRowCell(RowValue):
    """The value of a cell in the row."""
    def __init__(self, column: str):
        self.column: str = column

    def __str__(self):
        return f"RowCell('{self.column}')"

    def __repr__(self):
        return f"{self.__class__.__name__}(column='{self.column}')"

    def value(self, memory: PatcherMemory, twoda: TwoDA, row: TwoDARow | None) -> str:
        """Returns the value of a cell in the row."""
        return "" if row is None else row.get_string(self.column)


# endregion


# region Modify 2DA
class Modify2DA(ABC):
    def __str__(self):
        return f"{self.__class__.__name__}()"

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    @abstractmethod
    def __init__(self): ...

    def _unpack(
        self,
        cells: dict[str, RowValue],
        memory: PatcherMemory,
        twoda: TwoDA,
        row: TwoDARow,
    ) -> dict[str, str]:
        return {column: value.value(memory, twoda, row) for column, value in cells.items()}

    @abstractmethod
    def apply(
        self,
        twoda: TwoDA,
        memory: PatcherMemory,
    ): ...


class ChangeRow2DA(Modify2DA):
    """Changes an existing row.

    Target row can either be the Row Index, Row Label, or value under the "label" column where applicable.

    Attributes:
    ----------
        target: The row to change.
        modifiers: For the row, sets a cell under column KEY to have the text VALUE.
    """

    def __init__(
        self,
        identifier: str,
        target: Target,
        cells: Mapping[str, RowValue],
        store_2da: dict[int, RowValue] | None = None,
        store_tlk: dict[int, RowValue] | None = None,
    ):
        self.identifier: str = identifier
        self.target: Target = target
        self.cells: dict[str, RowValue] = dict(cells)
        self.store_2da: dict[int, RowValue] = {} if store_2da is None else store_2da
        self.store_tlk: dict[int, RowValue] = {} if store_tlk is None else store_tlk

        self._row: TwoDARow | None = None

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(identifier={self.identifier!r}, "
            f"target={self.target!r}, cells={self.cells!r}, "
            f"store_2da={self.store_2da!r}, store_tlk={self.store_tlk!r})"
        )

    def apply(self, twoda: TwoDA, memory: PatcherMemory):
        """Applies a ChangeRow patch to a TwoDA.

        Args:
        ----
            twoda: TwoDA - The TwoDA to apply the patch to
            memory: PatcherMemory - The memory context

        Processing Logic:
        ----------------
            - Searches for the target row
            - Unpacks the cells and applies them to the target row
            - Stores any 2DA or TLK values in the memory context.
        """
        source_row: TwoDARow | None = self.target.search(twoda, memory)

        if source_row is None:
            msg = f"The source row was not found during the search: ({self.target.target_type.name}, {self.target.value})"
            raise WarningError(msg)

        cells: dict[str, str] = self._unpack(self.cells, memory, twoda, source_row)
        source_row.update_values(cells)

        for token_id, value in self.store_2da.items():
            memory.memory_2da[token_id] = value.value(memory, twoda, source_row)

        for token_id, value in self.store_tlk.items():
            memory.memory_str[token_id] = int(value.value(memory, twoda, source_row))


class AddRow2DA(Modify2DA):
    """Adds a new row.

    Attributes:
    ----------
        modifiers: For the row, sets a cell under column KEY to have the text VALUE.
    """

    def __init__(  # noqa: PLR0913
        self,
        identifier: str,
        exclusive_column: str | None,
        row_label: str | None,
        cells: Mapping[str, RowValue],
        store_2da: dict[int, RowValue] | None = None,
        store_tlk: dict[int, RowValue] | None = None,
    ):
        self.identifier: str = identifier
        self.exclusive_column: str | None = exclusive_column
        self.row_label: str | None = row_label
        self.cells: dict[str, RowValue] = dict(cells)
        self.store_2da: dict[int, RowValue] = {} if store_2da is None else store_2da
        self.store_tlk: dict[int, RowValue] = {} if store_tlk is None else store_tlk

        self._row: TwoDARow | None = None

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(identifier={self.identifier!r}, "
            f"exclusive_column={self.exclusive_column!r}, row_label={self.row_label!r}, "
            f"cells={self.cells!r}, store_2da={self.store_2da!r}, "
            f"store_tlk={self.store_tlk!r})"
        )

    def apply(self, twoda: TwoDA, memory: PatcherMemory):
        """Applies an AddRow patch to a TwoDA.

        Args:
        ----
            twoda: TwoDA - The Two Dimensional Array to apply the patch to.
            memory: PatcherMemory - The memory context.

        Processing Logic:
        ----------------
            - Finds the target row to apply the patch to based on an optional exclusive column
            - If no target row is found, a new row is added
            - The cells are unpacked and applied to the target row
            - Any stored values are updated in the memory context.
        """
        target_row: TwoDARow | None = None

        if self.exclusive_column:
            if self.exclusive_column not in self.cells:
                msg = f"Exclusive column {self.exclusive_column} does not exists"
                raise WarningError(msg)

            exclusive_value = self.cells[self.exclusive_column].value(
                memory,
                twoda,
                None,
            )
            for row in twoda:
                if row.get_string(self.exclusive_column) != exclusive_value:
                    continue
                target_row = row

        if target_row is None:
            row_label: str = str(twoda.get_height()) if self.row_label is None else self.row_label
            index: int = twoda.add_row(row_label, {})
            self._row = target_row = twoda.get_row(index)
            target_row.update_values(self._unpack(self.cells, memory, twoda, target_row))
        else:
            cells: dict[str, str] = self._unpack(self.cells, memory, twoda, target_row)
            target_row.update_values(cells)

        for token_id, value in self.store_2da.items():
            memory.memory_2da[token_id] = value.value(memory, twoda, target_row)

        for token_id, value in self.store_tlk.items():
            memory.memory_str[token_id] = int(value.value(memory, twoda, target_row))


class CopyRow2DA(Modify2DA):
    """Copies the the row if the exclusive_column value doesn't already exist. If the row already exists, it simply modifies the existing line.

    Attributes:
    ----------
        identifier:
        target: Which row to copy.
        exclusive_column: Modify existing line if the same value already exists at this column.
        modifiers: For the row, sets a cell under column KEY to have the text VALUE.
    """

    def __init__(  # noqa: PLR0913
        self,
        identifier: str,
        target: Target,
        exclusive_column: str | None,
        row_label: str | None,
        cells: dict[str, RowValue],
        store_2da: dict[int, RowValue] | None = None,
        store_tlk: dict[int, RowValue] | None = None,
    ):
        self.identifier: str = identifier
        self.target: Target = target
        self.exclusive_column: str | None = exclusive_column or None
        self.row_label: str | None = row_label
        self.cells: dict[str, RowValue] = cells
        self.store_2da: dict[int, RowValue] = {} if store_2da is None else store_2da
        self.store_tlk: dict[int, RowValue] = {} if store_tlk is None else store_tlk

        self._row: TwoDARow | None = None

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(identifier={self.identifier!r}, "
            f"target={self.target!r}, exclusive_column={self.exclusive_column!r}, "
            f"row_label={self.row_label!r}, cells={self.cells!r}, "
            f"store_2da={self.store_2da!r}, store_tlk={self.store_tlk!r})"
        )

    def apply(self, twoda: TwoDA, memory: PatcherMemory):
        """Applies a CopyRow patch to a TwoDA.

        Args:
        ----
            twoda: TwoDA - The TwoDA to apply the patch to
            memory: PatcherMemory - The memory context

        Processing Logic:
        ----------------
            1. Searches for the source row in the TwoDA
            2. Determines if an existing target row should be used or a new row added
            3. Unpacks the cell values and updates/adds the target row
            4. Stores any 2DA or TLK values in the memory context.
        """
        source_row: TwoDARow | None = self.target.search(twoda, memory)
        target_row: TwoDARow | None = None
        row_label = str(twoda.get_height()) if self.row_label is None else self.row_label

        if source_row is None:
            msg = f"Source row cannot be None. row_label was '{row_label}'"
            raise WarningError(msg)

        if self.exclusive_column is not None:
            if self.exclusive_column not in self.cells:
                msg = f"Exclusive column {self.exclusive_column} does not exists"
                raise WarningError(msg)

            exclusive_value: str = self.cells[self.exclusive_column].value(
                memory,
                twoda,
                None,
            )
            for row in twoda:
                if row.get_string(self.exclusive_column) != exclusive_value:
                    continue
                target_row = row

        if target_row is not None:
            # If the row already exists (based on exclusive_column) then we update the cells
            cells = self._unpack(self.cells, memory, twoda, target_row)
            target_row.update_values(cells)
            self._row = target_row
        else:
            # Otherwise, we add the new row instead.
            index: int = twoda.copy_row(source_row, row_label, {})
            self._row = target_row = twoda.get_row(index)
            cells = self._unpack(self.cells, memory, twoda, target_row)
            target_row.update_values(cells)

        for token_id, value in self.store_2da.items():
            memory.memory_2da[token_id] = value.value(memory, twoda, target_row)

        for token_id, value in self.store_tlk.items():
            memory.memory_str[token_id] = int(value.value(memory, twoda, target_row))


class AddColumn2DA(Modify2DA):
    """Adds a column.

    The new cells are either given a default value or can be given a
    value based on what the row index or row label is.

    Attributes:
    ----------
        identifier:
        header: Label for the name column.
        default: Default value of cells if no specific value was specified.
        index_insert: For the new column, if the row index is KEY then set cell to VALUE.
        label_insert: For the new column, if the row label is KEY then set cell to VALUE.
    """

    def __init__(  # noqa: PLR0913
        self,
        identifier: str,
        header: str,
        default: str,
        index_insert: dict[int, RowValue],
        label_insert: dict[str, RowValue],
        store_2da: dict[int, str] | None = None,
    ):
        self.identifier: str = identifier
        self.header: str = header
        self.default: str = default
        self.index_insert: dict[int, RowValue] = index_insert
        self.label_insert: dict[str, RowValue] = label_insert
        self.store_2da: dict[int, str] = {} if store_2da is None else store_2da

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(identifier={self.identifier!r}, "
            f"header={self.header!r}, default={self.default!r}, "
            f"index_insert={self.index_insert}, label_insert={self.label_insert}, "
            f"store_2da={self.store_2da})"
        )

    def apply(self, twoda: TwoDA, memory: PatcherMemory):
        """Applies a AddColumn patch to a TwoDA.

        Args:
        ----
            twoda: TwoDA - The TwoDA to apply the patcher to
            memory: PatcherMemory - The memory object to store values

        Processing Logic:
        ----------------
            - Adds a column to the TwoDA with the patcher header
            - Sets the default value for all rows in the new column
            - Sets values in the new column based on index/label lookups
            - Stores values from the TwoDA in the memory based on token IDs.
        """
        twoda.add_column(self.header)
        for row in twoda:
            row.set_string(self.header, self.default)

        for row_index, row_value in self.index_insert.items():
            index_str: str = row_value.value(memory, twoda, None)
            this_row: TwoDARow | None = twoda.get_row(row_index)
            if this_row:
                this_row.set_string(self.header, index_str)
            else:
                msg = f"Could not find row {row_index} in {self.header}"
                raise WarningError(msg)

        for row_label, row_value in self.label_insert.items():
            label_str: str = row_value.value(memory, twoda, None)
            this_row = twoda.find_row(row_label)
            if this_row:
                this_row.set_string(self.header, label_str)
            else:
                msg = f"Could not find row {row_label} in {self.header}"
                raise WarningError(msg)

        for token_id, value in self.store_2da.items():
            if value.startswith("I"):
                cell: str = twoda.get_row(int(value[1:])).get_string(self.header)
                memory.memory_2da[token_id] = cell
            elif value.startswith("L"):
                row = twoda.find_row(value[1:])
                if row is None:
                    msg = f"Could not find row {value[1:]} in {self.header}"
                    raise WarningError(msg)
                cell = row.get_string(self.header)
                memory.memory_2da[token_id] = cell
            else:
                msg = f"store_2da dict has an invalid value at {token_id}: '{value}'"
                raise WarningError(msg)


# endregion


class Modifications2DA(PatcherModifications):
    hardcapped_row_limits = {
        "placeables.2da": 256,
        "upcrystals.2da": 256,
        "upgrade.2da": 32,
    }
    def __init__(self, filename: str):
        super().__init__(filename)
        self.modifiers: list[Modify2DA] = []

    def patch_resource(
        self,
        source: SOURCE_TYPES,
        memory: PatcherMemory,
        logger: PatchLogger,
        game: Game,
    ) -> bytes | Literal[True]:
        twoda: TwoDA = read_2da(source)
        self.apply(twoda, memory, logger, game)
        return bytes_2da(twoda)

    def apply(
        self,
        mutable_data: TwoDA,
        memory: PatcherMemory,
        logger: PatchLogger,
        game: Game,
    ):
        for row in self.modifiers:
            try:
                row.apply(mutable_data, memory)
            except Exception as e:  # noqa: PERF203, BLE001
                msg = f"{universal_simplify_exception(e)} when patching the file '{self.saveas}'"
                RobustLogger().critical(str(e), exc_info=e)
                if isinstance(e, WarningError):
                    logger.add_warning(msg)
                    RobustLogger().debug(msg, exc_info=True)
                else:
                    logger.add_error(msg)
                    break
        if game.is_k2():  # k2 doesn't have hard limits?
            return

        # Exceeding row count maximums will break the game.
        twoda_row_limit = self.hardcapped_row_limits.get(self.saveas.lower())
        if twoda_row_limit is None:
            return
        cur_row_count = len(mutable_data._rows)
        rows_added = cur_row_count - twoda_row_limit
        if cur_row_count > twoda_row_limit:
            raise ValueError(f"{self.saveas} has a max row count of {twoda_row_limit}. Adding more will break the game. This mod attempted to add {rows_added} rows and have not been applied.")
