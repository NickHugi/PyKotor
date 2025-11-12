"""NWScript definitions and script-related classes.

References:
----------
    vendor/xoreos-tools/src/nwscript/ (NWScript definitions)
    vendor/xoreos-docs/specs/ (NWScript documentation)
    vendor/KotOR.js/src/nwscript/NWScriptDefK1.ts (K1 script definitions)
    vendor/KotOR.js/src/nwscript/NWScriptDefK2.ts (K2 script definitions)
    vendor/HoloLSP/server/src/nwscript/ (Language server NWScript definitions)
    Note: Script constants and parameters define function signatures for NWScript functions
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class ScriptConstant:
    def __init__(
        self,
        datatype: DataType,
        name: str,
        value: Any,
    ):
        self.datatype: DataType = DataType(datatype)
        self.name: str = name
        self.value: Any = value

        if self.datatype == DataType.INT and not isinstance(value, int):
            msg = "Script constant value argument does not match given datatype."
            raise ValueError(msg)
        if self.datatype == DataType.FLOAT and not isinstance(value, float):
            msg = "Script constant value argument does not match given datatype."
            raise ValueError(msg)
        if self.datatype == DataType.STRING and not isinstance(value, str):
            msg = "Script constant value argument does not match given datatype."
            raise ValueError(msg)

    def __repr__(
        self,
    ):
        return f'ScriptConstant("{self.datatype}", "{self.name}", "{self.value}")'

    def __str__(
        self,
    ):
        return f"{self.datatype} {self.name} = {self.value};"


class ScriptParam:
    def __init__(
        self,
        datatype: DataType,
        name: str,
        default: Any | None,
    ):
        self.datatype: DataType = DataType(datatype)
        self.name: str = name
        self.default: Any | None = default

    def __repr__(
        self,
    ):
        return f"ScriptParam({self.datatype!r}, {self.name!r}, {self.default!r})"

    def __str__(
        self,
    ):
        if self.default is not None:
            return f"{self.datatype} {self.name} = {self.default}"
        return f"{self.datatype} {self.name}"


class ScriptFunction:
    def __init__(
        self,
        returntype: DataType,
        name: str,
        params: list[ScriptParam],
        description: str,
        raw: str,
    ):
        self.returntype: DataType = DataType(returntype)
        self.name: str = name
        self.params: list[ScriptParam] = params
        self.description: str = description
        self.raw: str = raw

    def __repr__(
        self,
    ):
        return f"ScriptFunction({self.returntype!r}, {self.name!r}, {self.params!r}, {self.description!r}, {self.raw!r})"

    def __str__(
        self,
    ):
        param_str = ""
        for param in self.params:
            param_str += str(param)
            if param is not self.params[-1]:
                param_str += ", "
        return f"{self.returntype} {self.name}({param_str})"


class DataType(Enum):
    VOID = "void"
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    OBJECT = "object"
    VECTOR = "vector"
    LOCATION = "location"
    EVENT = "event"
    EFFECT = "effect"
    ITEMPROPERTY = "itemproperty"
    TALENT = "talent"
    ACTION = "action"
    STRUCT = "struct"

    def size(self) -> int:
        if self == DataType.VOID:
            return 0
        if self == DataType.VECTOR:
            return 12
        if self == DataType.STRUCT:
            raise ValueError("Structs are variable size")  # TODO(th3w1zard1): something needs to be done here
        return 4
