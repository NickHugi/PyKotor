from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional
from pykotor.common.script import DataType
from pykotor.resource.formats.ncs import NCS, NCSInstruction, NCSInstructionType


class CompileException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class Identifier:
    def __init__(self, label: str):
        self.label: str = label

    def __eq__(self, other):
        return self.label == other.label

    def __str__(self):
        return self.label


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
        self.scope: List[ScopedValue] = []

    def add_scoped(self, identifier: Identifier, data_type: DataType):
        self.scope.insert(0, ScopedValue(identifier, data_type))

    def get_scoped(self, identifier: Identifier):
        index = 0
        for scoped in self.scope:
            index -= scoped.data_type.size()
            if scoped.identifier == identifier:
                break
        else:
            raise CompileException(f"Could not find symbol {identifier}.")
        return scoped.data_type, index


class ScopedValue:
    def __init__(self, identifier: Identifier, data_type: DataType):
        self.identifier: Identifier = identifier
        self.data_type: DataType = data_type


# region Value Classes
class Value(ABC):
    ...

    @abstractmethod
    def compile(self, ncs: NCS, block: CodeBlock):
        ...

    @abstractmethod
    def data_type(self):
        ...


class IdentifierValue(Value):
    def __init__(self, value: Identifier):
        self.identifier: Identifier = value
        self._type: Optional[DataType] = None

    def compile(self, ncs: NCS, block: CodeBlock):
        self._type, stack_index = block.get_scoped(self.identifier)
        ncs.instructions.append(NCSInstruction(NCSInstructionType.CPTOPSP, [stack_index, self._type.size()]))

    def data_type(self):
        if self._type is None:
            raise Exception("Expression has not been compiled yet.")
        return self._type


class StringValue(Value):
    def __init__(self, value: str):
        self.value: str = value

    def compile(self, ncs: NCS, block: CodeBlock):
        ncs.instructions.append(NCSInstruction(NCSInstructionType.CONSTS, [self.value]))

    def data_type(self):
        return DataType.STRING


class IntValue(Value):
    def __init__(self, value: int):
        self.value: int = value

    def compile(self, ncs: NCS, block: CodeBlock):
        ncs.instructions.append(NCSInstruction(NCSInstructionType.CONSTI, [self.value]))

    def data_type(self):
        return DataType.INT


class FloatValue(Value):
    def __init__(self, value: float):
        self.value: float = value

    def compile(self, ncs: NCS, block: CodeBlock):
        ncs.instructions.append(NCSInstruction(NCSInstructionType.CONSTF, [self.value]))

    def data_type(self):
        return DataType.FLOAT
# endregion


# region Statement Classes
class Statement(ABC):
    @abstractmethod
    def compile(self, ncs: NCS, block: CodeBlock):
        ...


class DeclarationStatement(Statement):
    def __init__(self, identifier: Identifier, data_type: DataType, value: Value):
        self.identifier: Identifier = identifier
        self.data_type: DataType = data_type
        self.expression: Value = value

    def compile(self, ncs: NCS, block: CodeBlock):
        self.expression.compile(ncs, block)
        block.add_scoped(self.identifier, self.data_type)


class AssignmentStatement(Statement):
    def __init__(self, identifier: Identifier, value: Value):
        self.identifier: Identifier = identifier
        self.expression: Value = value

    def compile(self, ncs: NCS, block: CodeBlock):
        self.expression.compile(ncs, block)

        data_type, stack_index = block.get_scoped(self.identifier)
        stack_index -= data_type.size()

        if self.expression.data_type() != data_type:
            raise CompileException(f"Wrong type was assigned to symbol {self.identifier}.")

        # Copy the value that the expression has already been placed on the stack to where the identifiers position is
        ncs.instructions.append(NCSInstruction(NCSInstructionType.CPDOWNSP, [stack_index, data_type.size()]))
        # Remove the temporary value from the stack that the expression created
        ncs.instructions.append(NCSInstruction(NCSInstructionType.MOVSP, [-data_type.size()]))
# endregion

