from abc import ABC
from enum import Enum


# region Value Classes
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


class ControlKeyword(Enum):
    BREAK = "break"
    CASE = "control"
    DEFAULT = "default"
    DO = "do"
    ELSE = "else"
    SWITCH = "switch"
    WHILE = "while"
    FOR = "for"
