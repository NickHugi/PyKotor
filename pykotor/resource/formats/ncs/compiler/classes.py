from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional, Tuple
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

    def __hash__(self):
        return hash(self.label)


class ControlKeyword(Enum):
    BREAK = "break"
    CASE = "control"
    DEFAULT = "default"
    DO = "do"
    ELSE = "else"
    SWITCH = "switch"
    WHILE = "while"
    FOR = "for"
    IF = "if"


class Operator(Enum):
    ADDITION = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    MODULUS = "%"
    NOT = "!"
    EQUAL = "=="
    NOT_EQUAL = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN_OR_EQUAL = "<="
    AND = "&&"
    OR = "||"
    BITWISE_AND = "&"
    BITWISE_OR = "|"
    BITWISE_XOR = "^"
    BITWISE_LEFT = "<<"
    BITWISE_RIGHT = ">>"
    ONES_COMPLEMENT = "~"


class CodeRoot:
    def __init__(self):
        self.functions: List[FunctionDefinition] = []

    def compile(self, ncs: NCS):
        function_map = {}
        for function in self.functions:
            start_index = len(ncs.instructions)
            function.compile(ncs)
            function_map[function.identifier.label] = ncs.instructions[start_index]

        ncs.instructions.insert(0, NCSInstruction(NCSInstructionType.JSR, None, function_map["main"]))


class CodeBlock:
    def __init__(self):
        self.scope: List[ScopedValue] = []
        self.parent: Optional[CodeBlock] = None
        self._statements: List[Statement] = []
        self.jump_buffer: Optional[Tuple[NCSInstruction, int]] = None
        self.tempstack: int = 0

    def add(self, statement: Statement):
        self._statements.append(statement)

    def compile(self, ncs: NCS):
        for statement in self._statements:
            if self.jump_buffer is None:
                statement.compile(ncs, self)
            else:
                statement.compile(ncs, self)
                inst, index = self.jump_buffer
                inst.jump = ncs.instructions[index]
        ncs.instructions.append(NCSInstruction(NCSInstructionType.MOVSP, [-self.scope_size()]))

    def add_scoped(self, identifier: Identifier, data_type: DataType):
        self.scope.insert(0, ScopedValue(identifier, data_type))

    def get_scoped(self, identifier: Identifier):
        index = -self.tempstack
        for scoped in self.scope:
            index -= scoped.data_type.size()
            if scoped.identifier == identifier:
                break
        else:
            if self.parent is not None:
                return self.parent.get_scoped(identifier)
            else:
                raise CompileException(f"Could not find symbol {identifier}.")
        return scoped.data_type, index

    def scope_size(self):
        return abs(self.get_scoped(self.scope[-1].identifier)[-1]) if self.scope else 0

    def build_parents(self):
        # need a better way of implementing this
        for statement in self._statements:
            if hasattr(statement, "block"):
                statement.block.parent = self
                statement.block.build_parents()


class ScopedValue:
    def __init__(self, identifier: Identifier, data_type: DataType):
        self.identifier: Identifier = identifier
        self.data_type: DataType = data_type


class FunctionDefinition:
    def __init__(self, return_type: DataType, identifier: Identifier, parameters: List[FunctionDefinitionParam], block: CodeBlock):
        self.return_type: DataType = return_type
        self.identifier: Identifier = identifier
        self.parameters: List[FunctionDefinitionParam] = parameters
        self.block: CodeBlock = block

    def compile(self, ncs: NCS):
        self.block.compile(ncs)


class FunctionDefinitionParam:
    def __init__(self, data_type: DataType, identifier: Identifier):
        self.data_type: DataType = data_type
        self.identifier: Identifier = identifier


# region Expression Classes
class Expression(ABC):
    ...

    @abstractmethod
    def compile(self, ncs: NCS, block: CodeBlock) -> int:
        ...

    @abstractmethod
    def data_type(self) -> DataType:
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


class AdditionExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2
        self._type = None

    def compile(self, ncs: NCS, block: CodeBlock) -> int:
        self.expression1.compile(ncs, block)
        block.tempstack += 4
        self.expression2.compile(ncs, block)
        block.tempstack += 4

        type1 = self.expression1.data_type()
        type2 = self.expression2.data_type()

        if type1 == DataType.INT and type1 == DataType.INT:
            ncs.add(NCSInstructionType.ADDII)
        elif type1 == DataType.INT and type1 == DataType.FLOAT:
            ncs.add(NCSInstructionType.ADDIF)
        elif type1 == DataType.FLOAT and type1 == DataType.FLOAT:
            ncs.add(NCSInstructionType.ADDFF)
        elif type1 == DataType.FLOAT and type1 == DataType.INT:
            ncs.add(NCSInstructionType.ADDFI)
        elif type1 == DataType.STRING and type1 == DataType.STRING:
            ncs.add(NCSInstructionType.ADDSS)
        elif type1 == DataType.VECTOR and type1 == DataType.VECTOR:
            ncs.add(NCSInstructionType.ADDVV)
        else:
            raise CompileException(f"Cannot add {type1.name.lower()} to {type2.name.lower()}")

        block.tempstack -= 8
        self._type = type1
        return type1.size()

    def data_type(self) -> DataType:
        if self._type is None:
            raise Exception("Expression has not been compiled yet.")
        return self._type


class SubtractionExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2
        self._type = None

    def compile(self, ncs: NCS, block: CodeBlock) -> int:
        self.expression1.compile(ncs, block)
        block.tempstack += 4
        self.expression2.compile(ncs, block)
        block.tempstack += 4

        type1 = self.expression1.data_type()
        type2 = self.expression2.data_type()

        if type1 == DataType.INT and type1 == DataType.INT:
            ncs.add(NCSInstructionType.SUBII)
        elif type1 == DataType.INT and type1 == DataType.FLOAT:
            ncs.add(NCSInstructionType.SUBIF)
        elif type1 == DataType.FLOAT and type1 == DataType.FLOAT:
            ncs.add(NCSInstructionType.SUBFF)
        elif type1 == DataType.FLOAT and type1 == DataType.INT:
            ncs.add(NCSInstructionType.SUBFI)
        elif type1 == DataType.VECTOR and type1 == DataType.VECTOR:
            ncs.add(NCSInstructionType.SUBVV)
        else:
            raise CompileException(f"Cannot subtract {type2.name.lower()} from {type1.name.lower()}")

        block.tempstack -= 8
        self._type = type1
        return type1.size()

    def data_type(self) -> DataType:
        if self._type is None:
            raise Exception("Expression has not been compiled yet.")
        return self._type


class MultiplicationExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2
        self._type = None

    def compile(self, ncs: NCS, block: CodeBlock) -> int:
        self.expression1.compile(ncs, block)
        block.tempstack += 4
        self.expression2.compile(ncs, block)
        block.tempstack += 4

        type1 = self.expression1.data_type()
        type2 = self.expression2.data_type()

        if type1 == DataType.INT and type1 == DataType.INT:
            ncs.add(NCSInstructionType.MULII)
        elif type1 == DataType.INT and type1 == DataType.FLOAT:
            ncs.add(NCSInstructionType.MULIF)
        elif type1 == DataType.FLOAT and type1 == DataType.FLOAT:
            ncs.add(NCSInstructionType.MULFF)
        elif type1 == DataType.FLOAT and type1 == DataType.INT:
            ncs.add(NCSInstructionType.MULFI)
        elif type1 == DataType.VECTOR and type1 == DataType.FLOAT:
            ncs.add(NCSInstructionType.MULVF)
        elif type1 == DataType.FLOAT and type1 == DataType.VECTOR:
            ncs.add(NCSInstructionType.MULFV)
        else:
            raise CompileException(f"Cannot multiply {type1.name.lower()} to {type2.name.lower()}")

        block.tempstack -= 8
        block.tempstack -= 8
        self._type = type1
        return type1.size()

    def data_type(self) -> DataType:
        if self._type is None:
            raise Exception("Expression has not been compiled yet.")
        return self._type


class DivisionExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2
        self._type = None

    def compile(self, ncs: NCS, block: CodeBlock) -> int:
        self.expression1.compile(ncs, block)
        block.tempstack += 4
        self.expression2.compile(ncs, block)
        block.tempstack += 4

        type1 = self.expression1.data_type()
        type2 = self.expression2.data_type()

        if type1 == DataType.INT and type1 == DataType.INT:
            ncs.add(NCSInstructionType.DIVII)
        elif type1 == DataType.INT and type1 == DataType.FLOAT:
            ncs.add(NCSInstructionType.DIVIF)
        elif type1 == DataType.FLOAT and type1 == DataType.FLOAT:
            ncs.add(NCSInstructionType.DIVFF)
        elif type1 == DataType.FLOAT and type1 == DataType.INT:
            ncs.add(NCSInstructionType.DIVFI)
        elif type1 == DataType.VECTOR and type1 == DataType.FLOAT:
            ncs.add(NCSInstructionType.DIVVF)
        else:
            raise CompileException(f"Cannot divide {type1.name.lower()} by {type2.name.lower()}")

        block.tempstack -= 8
        self._type = type1
        return type1.size()

    def data_type(self) -> DataType:
        if self._type is None:
            raise Exception("Expression has not been compiled yet.")
        return self._type


class ModulusExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2
        self._type = None

    def compile(self, ncs: NCS, block: CodeBlock) -> int:
        self.expression1.compile(ncs, block)
        block.tempstack += 4
        self.expression2.compile(ncs, block)
        block.tempstack += 4

        type1 = self.expression1.data_type()
        type2 = self.expression2.data_type()

        if type1 == DataType.INT and type1 == DataType.INT:
            ncs.add(NCSInstructionType.MODII)
        else:
            raise CompileException(f"Cannot get the modulus of {type1.name.lower()} and {type2.name.lower()}")

        block.tempstack -= 8
        self._type = type1
        return type1.size()

    def data_type(self) -> DataType:
        if self._type is None:
            raise Exception("Expression has not been compiled yet.")
        return self._type


class NegationExpression(Expression):
    def __init__(self, expression1: Expression):
        self.expression1: Expression = expression1
        self._type = None

    def compile(self, ncs: NCS, block: CodeBlock) -> int:
        self.expression1.compile(ncs, block)
        block.tempstack += 4

        type1 = self.expression1.data_type()

        if type1 == DataType.INT:
            ncs.add(NCSInstructionType.NEGI)
        elif type1 == DataType.FLOAT:
            ncs.add(NCSInstructionType.NEGF)
        else:
            raise CompileException(f"Cannot negate {type1.name.lower()}")

        block.tempstack -= 4
        self._type = type1
        return type1.size()

    def data_type(self) -> DataType:
        if self._type is None:
            raise Exception("Expression has not been compiled yet.")
        return self._type


class LogicalNotExpression(Expression):
    def __init__(self, expression1: Expression):
        self.expression1: Expression = expression1
        self._type = None

    def compile(self, ncs: NCS, block: CodeBlock) -> int:
        self.expression1.compile(ncs, block)
        block.tempstack += 4

        type1 = self.expression1.data_type()

        if type1 == DataType.INT:
            ncs.add(NCSInstructionType.NOTI)
        else:
            raise CompileException(f"Cannot get the logical NOT of {type1.name.lower()}")

        block.tempstack -= 4
        self._type = type1
        return type1.size()

    def data_type(self) -> DataType:
        if self._type is None:
            raise Exception("Expression has not been compiled yet.")
        return self._type


class LogicalAndExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2
        self._type = None

    def compile(self, ncs: NCS, block: CodeBlock) -> int:
        self.expression1.compile(ncs, block)
        block.tempstack += 4
        self.expression2.compile(ncs, block)
        block.tempstack += 4

        type1 = self.expression1.data_type()
        type2 = self.expression2.data_type()

        if type1 == DataType.INT and type2 == DataType.INT:
            ncs.add(NCSInstructionType.LOGANDII)
        else:
            raise CompileException(f"Cannot get the logical AND of {type1.name.lower()} and {type2.name.lower()}")

        block.tempstack -= 8
        self._type = type1
        return type1.size()

    def data_type(self) -> DataType:
        if self._type is None:
            raise Exception("Expression has not been compiled yet.")
        return self._type


class LogicalOrExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2
        self._type = None

    def compile(self, ncs: NCS, block: CodeBlock) -> int:
        self.expression1.compile(ncs, block)
        block.tempstack += 4
        self.expression2.compile(ncs, block)
        block.tempstack += 4

        type1 = self.expression1.data_type()
        type2 = self.expression2.data_type()

        if type1 == DataType.INT and type2 == DataType.INT:
            ncs.add(NCSInstructionType.LOGORII)
        else:
            raise CompileException(f"Cannot get the logical OR of {type1.name.lower()} and {type2.name.lower()}")

        block.tempstack -= 8
        self._type = type1
        return type1.size()

    def data_type(self) -> DataType:
        if self._type is None:
            raise Exception("Expression has not been compiled yet.")
        return self._type


class LogicalEqualityExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2
        self._type = None

    def compile(self, ncs: NCS, block: CodeBlock) -> int:
        self.expression1.compile(ncs, block)
        block.tempstack += 4
        self.expression2.compile(ncs, block)
        block.tempstack += 4

        type1 = self.expression1.data_type()
        type2 = self.expression2.data_type()

        if type1 == DataType.INT and type2 == DataType.INT:
            ncs.add(NCSInstructionType.EQUALII)
        elif type1 == DataType.FLOAT and type2 == DataType.FLOAT:
            ncs.add(NCSInstructionType.EQUALFF)
        elif type1 == DataType.STRING and type2 == DataType.STRING:
            ncs.add(NCSInstructionType.EQUALSS)
        elif type1 == DataType.OBJECT and type2 == DataType.OBJECT:
            ncs.add(NCSInstructionType.EQUALOO)
        else:
            raise CompileException(f"Cannot test the equality of {type1.name.lower()} and {type2.name.lower()}")

        block.tempstack -= 8
        self._type = type1
        return type1.size()

    def data_type(self) -> DataType:
        if self._type is None:
            raise Exception("Expression has not been compiled yet.")
        return self._type


class LogicalInequalityExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2
        self._type = None

    def compile(self, ncs: NCS, block: CodeBlock) -> int:
        self.expression1.compile(ncs, block)
        block.tempstack += 4
        self.expression2.compile(ncs, block)
        block.tempstack += 4

        type1 = self.expression1.data_type()
        type2 = self.expression2.data_type()

        if type1 == DataType.INT and type2 == DataType.INT:
            ncs.add(NCSInstructionType.NEQUALII)
        elif type1 == DataType.FLOAT and type2 == DataType.FLOAT:
            ncs.add(NCSInstructionType.NEQUALFF)
        elif type1 == DataType.STRING and type2 == DataType.STRING:
            ncs.add(NCSInstructionType.NEQUALSS)
        elif type1 == DataType.OBJECT and type2 == DataType.OBJECT:
            ncs.add(NCSInstructionType.NEQUALOO)
        else:
            raise CompileException(f"Cannot test the equality of {type1.name.lower()} and {type2.name.lower()}")

        block.tempstack -= 8
        self._type = type1
        return type1.size()

    def data_type(self) -> DataType:
        if self._type is None:
            raise Exception("Expression has not been compiled yet.")
        return self._type


class GreaterThanExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2
        self._type = None

    def compile(self, ncs: NCS, block: CodeBlock) -> int:
        self.expression1.compile(ncs, block)
        block.tempstack += 4
        self.expression2.compile(ncs, block)
        block.tempstack += 4

        type1 = self.expression1.data_type()
        type2 = self.expression2.data_type()

        if type1 == DataType.INT and type2 == DataType.INT:
            ncs.add(NCSInstructionType.GTII)
        elif type1 == DataType.FLOAT and type2 == DataType.FLOAT:
            ncs.add(NCSInstructionType.GTFF)
        else:
            raise CompileException(f"Cannot test if {type1.name.lower()} is greater than {type2.name.lower()}")

        block.tempstack -= 8
        self._type = type1
        return type1.size()

    def data_type(self) -> DataType:
        if self._type is None:
            raise Exception("Expression has not been compiled yet.")
        return self._type


class GreaterThanOrEqualExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2
        self._type = None

    def compile(self, ncs: NCS, block: CodeBlock) -> int:
        self.expression1.compile(ncs, block)
        block.tempstack += 4
        self.expression2.compile(ncs, block)
        block.tempstack += 4

        type1 = self.expression1.data_type()
        type2 = self.expression2.data_type()

        if type1 == DataType.INT and type2 == DataType.INT:
            ncs.add(NCSInstructionType.GEQII)
        elif type1 == DataType.FLOAT and type2 == DataType.FLOAT:
            ncs.add(NCSInstructionType.GEQFF)
        else:
            raise CompileException(f"Cannot test if {type1.name.lower()} is greater than or equal to {type2.name.lower()}")

        block.tempstack -= 8
        self._type = type1
        return type1.size()

    def data_type(self) -> DataType:
        if self._type is None:
            raise Exception("Expression has not been compiled yet.")
        return self._type


class LessThanExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2
        self._type = None

    def compile(self, ncs: NCS, block: CodeBlock) -> int:
        self.expression1.compile(ncs, block)
        block.tempstack += 4
        self.expression2.compile(ncs, block)
        block.tempstack += 4

        type1 = self.expression1.data_type()
        type2 = self.expression2.data_type()

        if type1 == DataType.INT and type2 == DataType.INT:
            ncs.add(NCSInstructionType.LTII)
        elif type1 == DataType.FLOAT and type2 == DataType.FLOAT:
            ncs.add(NCSInstructionType.LTFF)
        else:
            raise CompileException(f"Cannot test if {type1.name.lower()} is less than {type2.name.lower()}")

        block.tempstack -= 8
        self._type = type1
        return type1.size()

    def data_type(self) -> DataType:
        if self._type is None:
            raise Exception("Expression has not been compiled yet.")
        return self._type


class LessThanOrEqualExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2
        self._type = None

    def compile(self, ncs: NCS, block: CodeBlock) -> int:
        self.expression1.compile(ncs, block)
        block.tempstack += 4
        self.expression2.compile(ncs, block)
        block.tempstack += 4

        type1 = self.expression1.data_type()
        type2 = self.expression2.data_type()

        if type1 == DataType.INT and type2 == DataType.INT:
            ncs.add(NCSInstructionType.LEQII)
        elif type1 == DataType.FLOAT and type2 == DataType.FLOAT:
            ncs.add(NCSInstructionType.LEQFF)
        else:
            raise CompileException(f"Cannot test if {type1.name.lower()} is less than {type2.name.lower()}")

        block.tempstack -= 8
        self._type = type1
        return type1.size()

    def data_type(self) -> DataType:
        if self._type is None:
            raise Exception("Expression has not been compiled yet.")
        return self._type


class BitwiseOrExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2
        self._type = None

    def compile(self, ncs: NCS, block: CodeBlock) -> int:
        self.expression1.compile(ncs, block)
        block.tempstack += 4
        self.expression2.compile(ncs, block)
        block.tempstack += 4

        type1 = self.expression1.data_type()
        type2 = self.expression2.data_type()

        if type1 == DataType.INT and type2 == DataType.INT:
            ncs.add(NCSInstructionType.INCORII)
        else:
            raise CompileException(f"Cannot get the bitwise OR of {type1.name.lower()} and {type2.name.lower()}")

        block.tempstack -= 8
        self._type = type1
        return type1.size()

    def data_type(self) -> DataType:
        if self._type is None:
            raise Exception("Expression has not been compiled yet.")
        return self._type


class BitwiseXorExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2
        self._type = None

    def compile(self, ncs: NCS, block: CodeBlock) -> int:
        self.expression1.compile(ncs, block)
        block.tempstack += 4
        self.expression2.compile(ncs, block)
        block.tempstack += 4

        type1 = self.expression1.data_type()
        type2 = self.expression2.data_type()

        if type1 == DataType.INT and type2 == DataType.INT:
            ncs.add(NCSInstructionType.EXCORII)
        else:
            raise CompileException(f"Cannot get the bitwise XOR of {type1.name.lower()} and {type2.name.lower()}")

        block.tempstack -= 8
        self._type = type1
        return type1.size()

    def data_type(self) -> DataType:
        if self._type is None:
            raise Exception("Expression has not been compiled yet.")
        return self._type


class BitwiseAndExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2
        self._type = None

    def compile(self, ncs: NCS, block: CodeBlock) -> int:
        self.expression1.compile(ncs, block)
        block.tempstack += 4
        self.expression2.compile(ncs, block)
        block.tempstack += 4

        type1 = self.expression1.data_type()
        type2 = self.expression2.data_type()

        if type1 == DataType.INT and type2 == DataType.INT:
            ncs.add(NCSInstructionType.BOOLANDII)
        else:
            raise CompileException(f"Cannot get the bitwise AND of {type1.name.lower()} and {type2.name.lower()}")

        block.tempstack -= 8
        self._type = type1
        return type1.size()

    def data_type(self) -> DataType:
        if self._type is None:
            raise Exception("Expression has not been compiled yet.")
        return self._type


class BitwiseNotExpression(Expression):
    def __init__(self, expression1: Expression):
        self.expression1: Expression = expression1
        self._type = None

    def compile(self, ncs: NCS, block: CodeBlock) -> int:
        self.expression1.compile(ncs, block)
        block.tempstack += 4

        type1 = self.expression1.data_type()

        if type1 == DataType.INT:
            ncs.add(NCSInstructionType.COMPI)
        else:
            raise CompileException(f"Cannot get one's complement of {type1.name.lower()}")

        block.tempstack -= 4
        self._type = type1
        return type1.size()

    def data_type(self) -> DataType:
        if self._type is None:
            raise Exception("Expression has not been compiled yet.")
        return self._type


class BitwiseLeftShiftExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2
        self._type = None

    def compile(self, ncs: NCS, block: CodeBlock) -> int:
        self.expression1.compile(ncs, block)
        block.tempstack += 4
        self.expression2.compile(ncs, block)
        block.tempstack += 4

        type1 = self.expression1.data_type()
        type2 = self.expression2.data_type()

        if type1 == DataType.INT and type2 == DataType.INT:
            ncs.add(NCSInstructionType.SHLEFTII)
        else:
            raise CompileException(f"Cannot bitshift {type1.name.lower()} with {type2.name.lower()}")

        block.tempstack -= 8
        self._type = type1
        return type1.size()

    def data_type(self) -> DataType:
        if self._type is None:
            raise Exception("Expression has not been compiled yet.")
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
            raise CompileException(f"Tried to declare '{self.identifier}' a new variable with incorrect type '{self.expression.data_type()}'.")
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


class ConditionalStatement(Statement):
    def __init__(self, condition: Expression, block: CodeBlock):
        super().__init__()
        self.condition: Expression = condition
        self.block: CodeBlock = block

    def compile(self, ncs: NCS, block: CodeBlock):
        self.condition.compile(ncs, block)

        jump = NCSInstruction(NCSInstructionType.JZ, [])
        ncs.instructions.append(jump)

        self.block.compile(ncs)
        block.jump_buffer = (jump, len(ncs.instructions))
# endregion

