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
from typing import Dict, List, Optional, Union

from pykotor.resource.formats.twoda import TwoDA, TwoDARow


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
    def __init__(self, twoda: TwoDA):
        self.twoda: TwoDA = twoda
        self.rows: List[Manipulation2DA] = []

    def apply(self) -> None:
        for row in self.rows:
            row.apply(self.twoda)


class Manipulation2DA(ABC):
    def __init__(self):
        ...

    def apply(self, twoda: TwoDA):
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

    def apply(self, twoda: TwoDA):
        source_row = self.target.search(twoda)

        if source_row is None:
            raise ValueError()

        source_row.update_values(self.modifiers)
        self._row = source_row


class AddRow2DA(Manipulation2DA):
    """
    Adds a new row.

    Attributes:
        modifiers: For the row, sets a cell under column KEY to have the text VALUE.
    """
    def __init__(self):
        super().__init__()
        self.identifier: str = ""
        self.modifiers: Dict[str, str] = {}

        self._row: Optional[TwoDARow] = None

    def apply(self, twoda: TwoDA):
        modifiers = copy(self.modifiers)
        row_label = str(twoda.get_height())
        if "RowLabel" in modifiers:
            row_label = modifiers["RowLabel"]
            modifiers.pop("RowLabel")

        index = twoda.add_row(row_label, modifiers)
        self._row = twoda.get_row(index)


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

    def apply(self, twoda: TwoDA):
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
        modifiers = copy(self.modifiers)
        row_label = str(twoda.get_height())
        if "NewRowLabel" in modifiers:
            row_label = modifiers["NewRowLabel"]
            modifiers.pop("NewRewLabel")

        if target_row is not None:
            # If the row already exists (based on exclusive_column) then we update the cells
            target_row.update_values(modifiers)
            self._row = target_row
        else:
            # Otherwise we add the a new row instead.
            index = twoda.add_row(row_label, modifiers)
            self._row = twoda.get_row(index)


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

    def apply(self, twoda: TwoDA) -> None:
        twoda.add_column(self.header)
        for row in twoda:
            row.set_string(self.header, self.default)

        for row_index, value in self.index_insert.items():
            twoda.get_row(row_index).set_string(self.header, value)

        for row_label, value in self.label_insert.items():
            twoda.find_row(row_label).set_string(self.header, value)

