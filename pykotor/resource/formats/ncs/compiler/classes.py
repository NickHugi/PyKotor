from abc import ABC
from enum import Enum
from typing import List


class Identifier:
    def __init__(self, label: str):
        self.label: str = label


class ControlKeyword(Enum):
    BREAK = "break"
    CASE = "control"
    DEFAULT = "default"
    DO = "do"
    ELSE = "else"
    SWITCH = "switch"
    WHILE = "while"
    FOR = "for"


class CodeBlock:
    def __init__(self):
        self.statements: List[Statement] = []


# region Value Classes
from pykotor.common.script import DataType


class Value(ABC):
    ...


class IdentifierValue(Value):
    def __init__(self, value: str):
        self.value: str = value


class StringValue(Value):
    def __init__(self, value: str):
        self.value: str = value


class IntValue(Value):
    def __init__(self, value: int):
        self.value: int = value


class FloatValue(Value):
    def __init__(self, value: float):
        self.value: float = value
# endregion


# region Statement Classes
class Statement(ABC):
    ...


class DeclarationStatement(Statement):
    def __init__(self, identifier: Identifier, data_type: DataType, value: Value):
        self.identifier: Identifier = identifier
        self.data_type: DataType = data_type
        self.value: Value = value
# endregion

