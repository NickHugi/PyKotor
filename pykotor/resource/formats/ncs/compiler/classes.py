from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional
from pykotor.common.script import DataType, ScriptFunction
from pykotor.resource.formats.ncs import NCS, NCSInstruction, NCSInstructionType


class CompileException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class Identifier:
    def __init__(self, label: str):
        self.label: str = label

    def __eq__(self, other):
        if isinstance(other, Identifier):
            return self.label == other.label
        elif isinstance(other, str):
            return self.label == other
        else:
            return NotImplemented

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
        self._statements: List[Statement] = []
        self.tempstack: int = 0

    def add(self, statement: Statement):
        self._statements.append(statement)

    def compile(self, ncs: NCS):
        for statement in self._statements:
            statement.compile(ncs, self)

    def add_scoped(self, identifier: Identifier, data_type: DataType):
        self.scope.insert(0, ScopedValue(identifier, data_type))

    def get_scoped(self, identifier: Identifier):
        index = -self.tempstack
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
class Expression(ABC):
    ...

    @abstractmethod
    def compile(self, ncs: NCS, block: CodeBlock) -> int:
        ...

    @abstractmethod
    def data_type(self):
        ...


class IdentifierExpression(Expression):
    def __init__(self, value: Identifier):
        self.identifier: Identifier = value
        self._type: Optional[DataType] = None

    def compile(self, ncs: NCS, block: CodeBlock) -> int:
        self._type, stack_index = block.get_scoped(self.identifier)
        ncs.instructions.append(NCSInstruction(NCSInstructionType.CPTOPSP, [stack_index, self._type.size()]))
        return self._type.size()

    def data_type(self):
        if self._type is None:
            raise Exception("Expression has not been compiled yet.")
        return self._type


class StringExpression(Expression):
    def __init__(self, value: str):
        self.value: str = value

    def compile(self, ncs: NCS, block: CodeBlock) -> int:
        ncs.instructions.append(NCSInstruction(NCSInstructionType.CONSTS, [self.value]))
        return DataType.STRING.size()

    def data_type(self):
        return DataType.STRING


class IntExpression(Expression):
    def __init__(self, value: int):
        self.value: int = value

    def compile(self, ncs: NCS, block: CodeBlock) -> int:
        ncs.instructions.append(NCSInstruction(NCSInstructionType.CONSTI, [self.value]))
        return DataType.INT.size()

    def data_type(self):
        return DataType.INT


class FloatExpression(Expression):
    def __init__(self, value: float):
        self.value: float = value

    def compile(self, ncs: NCS, block: CodeBlock) -> int:
        ncs.instructions.append(NCSInstruction(NCSInstructionType.CONSTF, [self.value]))
        return DataType.FLOAT.size()

    def data_type(self):
        return DataType.FLOAT


class EngineCallExpression(Expression):
    def __init__(self, function: ScriptFunction, routine_id: int, data_type: DataType, args: List[Expression]):
        self._function: ScriptFunction = function
        self._routine_id: int = routine_id
        self._type: DataType = data_type
        self._args: List[Expression] = args

    def compile(self, ncs: NCS, block: CodeBlock):
        this_stack = 0
        for arg in reversed(self._args):
            added = arg.compile(ncs, block)
            block.tempstack += added
            this_stack += added
        for arg, param in zip(self._args, self._function.params):
            if arg.data_type() != param.datatype:
                raise CompileException(f"Tried to pass an argument of the incorrect type to {self._function.name}.")
        ncs.instructions.append(NCSInstruction(NCSInstructionType.ACTION, [self._routine_id, len(self._args)]))
        block.tempstack -= this_stack
        return self._type.size()

    def data_type(self):
        return self._type
# endregion


# region Statement Classes
class Statement(ABC):
    def __init__(self):
        self.linenum: Optional[None] = None

    @abstractmethod
    def compile(self, ncs: NCS, block: CodeBlock):
        ...


class DeclarationStatement(Statement):
    def __init__(self, identifier: Identifier, data_type: DataType, value: Expression):
        super().__init__()
        self.identifier: Identifier = identifier
        self.data_type: DataType = data_type
        self.expression: Expression = value

    def compile(self, ncs: NCS, block: CodeBlock):
        self.expression.compile(ncs, block)
        if self.expression.data_type() != self.data_type:
            raise CompileException(f"Tried to declare a new variable with incorrect type '{self.identifier}'.")
        block.add_scoped(self.identifier, self.data_type)


class AssignmentStatement(Statement):
    def __init__(self, identifier: Identifier, value: Expression):
        super().__init__()
        self.identifier: Identifier = identifier
        self.expression: Expression = value

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

