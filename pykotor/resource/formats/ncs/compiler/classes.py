from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional, Tuple, Dict, NamedTuple, Union
from pykotor.common.script import DataType, ScriptFunction
from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.ncs import NCS, NCSInstruction, NCSInstructionType


def get_logical_equality_instruction(type1: DataType, type2: DataType) -> NCSInstructionType:
    if type1 == DataType.INT and type2 == DataType.INT:
        return NCSInstructionType.EQUALII
    elif type1 == DataType.FLOAT and type2 == DataType.FLOAT:
        return NCSInstructionType.EQUALFF
    elif type1 == DataType.FLOAT and type2 == DataType.FLOAT:
        return NCSInstructionType.EQUALSS
    elif type1 == DataType.FLOAT and type2 == DataType.FLOAT:
        return NCSInstructionType.EQUALOO
    else:
        raise CompileException(f"Tried an unsupported comparision between '{type1}' '{type2}'.")


class CompileException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class TopLevelObject(ABC):
    @abstractmethod
    def compile(self, ncs: NCS, root: CodeRoot) -> None:
        ...


class GlobalVariableDeclaration(TopLevelObject):
    def __init__(self, identifier: Identifier, data_type: DataType, value: Expression):
        super().__init__()
        self.identifier: Identifier = identifier
        self.data_type: DataType = data_type
        self.expression: Expression = value

    def compile(self, ncs: NCS, root: CodeRoot) -> None:
        expression_type = self.expression.compile(ncs, root, None)
        if expression_type != self.data_type:
            raise CompileException(f"Tried to declare '{self.identifier}' a new variable with incorrect type '{expression_type}'.")
        root.add_scoped(self.identifier, self.data_type)


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
    RETURN = "return"


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


class FunctionReference(NamedTuple):
    instruction: NCSInstruction
    definition: Union[FunctionForwardDeclaration, FunctionDefinition]

    def is_prototype(self) -> bool:
        return isinstance(self.definition, FunctionForwardDeclaration)


class GetScopedResult(NamedTuple):
    isglobal: bool
    datatype: DataType
    offset: int


class CodeRoot:
    def __init__(self):
        self.objects: List[TopLevelObject] = []

        self.function_map: Dict[str, FunctionReference] = {}
        self._global_scope: List[ScopedValue] = []

    def compile(self, ncs: NCS):
        # nwnnsscomp processes the includes and global variable declarations before functions regardless if they are
        # placed before or after function defintions. We will replicate this behaviour.

        included = []
        while [obj for obj in self.objects if isinstance(obj, IncludeScript)]:
            includes = [obj for obj in self.objects if isinstance(obj, IncludeScript)]
            include = includes.pop()
            self.objects.remove(include)
            included.append(include)
            include.compile(ncs, self)

        globals = [obj for obj in self.objects if isinstance(obj, GlobalVariableDeclaration)]
        others = [obj for obj in self.objects if obj not in included and obj not in globals]

        if len(globals) > 0:
            for globaldef in globals:
                globaldef.compile(ncs, self)
            ncs.add(NCSInstructionType.SAVEBP, args=[])
        entry_index = len(ncs.instructions)

        for obj in others:
            obj.compile(ncs, self)

        if "main" in self.function_map:
            ncs.add(NCSInstructionType.RETN, args=[], index=entry_index)
            ncs.add(NCSInstructionType.JSR, jump=self.function_map["main"][0], index=entry_index)

    def compile_jsr(self, ncs: NCS, block: CodeBlock, name: str, *args: Expression) -> DataType:
        if name not in self.function_map:
            raise CompileException(f"Function '{name}' has not been defined.")

        start_instruction, definition = self.function_map[name]

        if definition.return_type == DataType.INT:
            ncs.add(NCSInstructionType.RSADDI, args=[])
        elif definition.return_type == DataType.FLOAT:
            ncs.add(NCSInstructionType.RSADDF, args=[])
        elif definition.return_type == DataType.STRING:
            ncs.add(NCSInstructionType.RSADDS, args=[])
        elif definition.return_type == DataType.VECTOR:
            raise NotImplementedError("Cannot define a function that returns Vector yet")  # TODO
        elif definition.return_type == DataType.OBJECT:
            ncs.add(NCSInstructionType.RSADDO, args=[])
        elif definition.return_type == DataType.VOID:
            ...
        else:
            raise NotImplementedError("Trying to return unsuppoted type?")  # TODO

        for arg in args:
            arg.compile(ncs, self, block)
        ncs.add(NCSInstructionType.JSR, jump=start_instruction)

        return definition.return_type

    def add_scoped(self, identifier: Identifier, datatype: DataType) -> None:
        self._global_scope.insert(0, ScopedValue(identifier, datatype))

    def get_scoped(self, identifier: Identifier) -> GetScopedResult:
        offset = 0
        for scoped in self._global_scope:
            offset -= scoped.data_type.size()
            if scoped.identifier == identifier:
                break
        else:
            raise CompileException(f"Could not find variable '{identifier}'.")
        return GetScopedResult(True, scoped.data_type, offset)

    def scope_size(self):
        offset = 0
        for scoped in self._global_scope:
            offset -= scoped.data_type.size()
        return offset


class CodeBlock:
    def __init__(self):
        self.scope: List[ScopedValue] = []
        self._parent: Optional[CodeBlock] = None
        self._statements: List[Statement] = []
        self._break_scope: bool = False
        self.tempstack: int = 0

    def add(self, statement: Statement):
        self._statements.append(statement)

    def compile(self, ncs: NCS, root: CodeRoot, block: Optional[CodeBlock], return_instruction: NCSInstruction, break_instruction: Optional[NCSInstruction], continue_instruction: Optional[NCSInstruction]):
        self._parent = block

        for statement in self._statements:
            if isinstance(statement, ReturnStatement):
                scope_size = self.full_scope_size()

                return_type = statement.compile(ncs, root, self, return_instruction, None, None)
                if return_type != DataType.VOID:
                    ncs.add(NCSInstructionType.CPDOWNSP, args=[-scope_size-return_type.size()*2, 4])
                    ncs.add(NCSInstructionType.MOVSP, args=[-return_type.size()])

                ncs.add(NCSInstructionType.MOVSP, args=[-scope_size])
                ncs.add(NCSInstructionType.JMP, jump=return_instruction)
                return
            else:
                statement.compile(ncs, root, self, return_instruction, break_instruction, continue_instruction)
        ncs.instructions.append(NCSInstruction(NCSInstructionType.MOVSP, [-self.scope_size()]))

        if self.tempstack != 0:
            # If the temp stack is 0 after the whole block has compiled there must be an logic error in the code
            # of one of the expression/statement classes
            raise ValueError

    def add_scoped(self, identifier: Identifier, data_type: DataType):
        self.scope.insert(0, ScopedValue(identifier, data_type))

    def get_scoped(self, identifier: Identifier, root: CodeRoot, offset: int = None) -> GetScopedResult:
        offset = -self.tempstack if offset is None else offset
        for scoped in self.scope:
            offset -= scoped.data_type.size()
            if scoped.identifier == identifier:
                break
        else:
            if self._parent is not None:
                return self._parent.get_scoped(identifier, root, offset)
            else:
                return root.get_scoped(identifier)
        return GetScopedResult(False, scoped.data_type, offset)

    def scope_size(self) -> int:
        """Returns size of local scope."""
        size = 0
        for scoped in self.scope:
            size += scoped.data_type.size()
        return size

    def full_scope_size(self) -> int:
        """Returns size of scope, including outer blocks."""
        size = 0
        size += self.scope_size()
        if self._parent is not None:
            size += self._parent.full_scope_size()
        return size

    def break_scope_size(self) -> int:
        """Returns size of scope up to the nearest loop/switch statement."""
        size = 0
        size += self.scope_size()
        if self._parent is not None and not self._parent._break_scope:
            size += self._parent.break_scope_size()
        return size

    def mark_break_scope(self) -> None:
        self._break_scope = True


class ScopedValue:
    def __init__(self, identifier: Identifier, data_type: DataType):
        self.identifier: Identifier = identifier
        self.data_type: DataType = data_type


class FunctionForwardDeclaration(TopLevelObject):
    def __init__(self, return_type: DataType, identifier: Identifier, parameters: List[FunctionDefinitionParam]):
        self.return_type: DataType = return_type
        self.identifier: Identifier = identifier
        self.paramaters: List[FunctionDefinitionParam] = parameters

    def compile(self, ncs: NCS, root: CodeRoot):
        function_name = self.identifier.label

        if self.identifier.label in root.function_map:
            raise CompileException(f"Function '{function_name}' already has a protype or been defined.")

        root.function_map[self.identifier.label] = FunctionReference(ncs.add(NCSInstructionType.NOP, args=[]), self)


class FunctionDefinition(TopLevelObject):
    # TODO: split definition into signature + block?
    def __init__(self, return_type: DataType, identifier: Identifier, parameters: List[FunctionDefinitionParam], block: CodeBlock):
        self.return_type: DataType = return_type
        self.identifier: Identifier = identifier
        self.parameters: List[FunctionDefinitionParam] = parameters
        self.block: CodeBlock = block

        for param in parameters:
            block.add_scoped(param.identifier, param.data_type)

    def compile(self, ncs: NCS, root: CodeRoot):
        name = self.identifier.label

        if name in root.function_map and not root.function_map[name].is_prototype():
            raise CompileException(f"Function '{name}' has already been defined.")
        elif name in root.function_map and root.function_map[name].is_prototype():

            if not self.is_matching_signature(root.function_map[name].definition):
                raise CompileException(f"Prototype of function '{name}' does not match definition.")

            # Function has forward declaration, insert the compiled definition after the stub
            temp = NCS()
            retn = NCSInstruction(NCSInstructionType.RETN)
            self.block.compile(temp, root, None, retn, None, None)
            temp.add(NCSInstructionType.RETN, args=[])

            stub_index = ncs.instructions.index(root.function_map[name].instruction)
            ncs.instructions[stub_index + 1:stub_index + 1] = temp.instructions
        else:
            retn = NCSInstruction(NCSInstructionType.RETN)

            function_start = ncs.add(NCSInstructionType.NOP, args=[])
            self.block.compile(ncs, root, None, retn, None, None)
            ncs.instructions.append(retn)

            root.function_map[name] = FunctionReference(function_start, self)

    def is_matching_signature(self, prototype: FunctionForwardDeclaration) -> bool:
        if self.return_type != prototype.return_type:
            return False
        if len(self.parameters) != len(prototype.paramaters):
            return False
        for i in range(len(self.parameters)):
            if self.parameters[i].data_type != prototype.paramaters[i].data_type:
                return False

        return True


class FunctionDefinitionParam:
    def __init__(self, data_type: DataType, identifier: Identifier):
        self.data_type: DataType = data_type
        self.identifier: Identifier = identifier


class IncludeScript(TopLevelObject):
    def __init__(self, file: StringExpression, library: Dict[str, str] = None):
        self.file: StringExpression = file
        self.library: Dict[str, str] = library if library is not None else {}

    def compile(self, ncs: NCS, root: CodeRoot) -> None:
        if self.file.value in self.library:
            source = self.library[self.file.value]
            # TODO try get file from drive
        else:
            raise CompileException(f"Could not find file '{self.file.value}.nss'.")

        from pykotor.resource.formats.ncs.compiler.parser import NssParser
        nssParser = NssParser()
        nssParser.library = self.library
        t: CodeRoot = nssParser.parser.parse(source, tracking=True)
        [root.objects.insert(0, obj) for obj in t.objects]

        '''imported = NCS()
        t.compile(imported)
        ncs.merge(imported)
        # TODO: throw error of function redefined
        root.function_map.update(t.function_map)'''


class Expression(ABC):
    @abstractmethod
    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        ...


class Statement(ABC):
    def __init__(self):
        self.linenum: Optional[None] = None

    @abstractmethod
    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock, return_instruction: NCSInstruction,
                break_instruction: Optional[NCSInstruction], continue_instruction: Optional[NCSInstruction]):
        ...


# region Expressions: Simple
class IdentifierExpression(Expression):
    def __init__(self, value: Identifier):
        super().__init__()
        self.identifier: Identifier = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        isglobal, datatype, stack_index = block.get_scoped(self.identifier, root)
        instruction_type = NCSInstructionType.CPTOPBP if isglobal else NCSInstructionType.CPTOPSP
        ncs.instructions.append(NCSInstruction(instruction_type, [stack_index, datatype.size()]))
        return datatype


class StringExpression(Expression):
    def __init__(self, value: str):
        super().__init__()
        self.value: str = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        ncs.instructions.append(NCSInstruction(NCSInstructionType.CONSTS, [self.value]))
        return DataType.STRING


class IntExpression(Expression):
    def __init__(self, value: int):
        super().__init__()
        self.value: int = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        ncs.instructions.append(NCSInstruction(NCSInstructionType.CONSTI, [self.value]))
        return DataType.INT


class FloatExpression(Expression):
    def __init__(self, value: float):
        super().__init__()
        self.value: float = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        ncs.instructions.append(NCSInstruction(NCSInstructionType.CONSTF, [self.value]))
        return DataType.FLOAT


class EngineCallExpression(Expression):
    def __init__(self, function: ScriptFunction, routine_id: int, data_type: DataType, args: List[Expression]):
        super().__init__()
        self._function: ScriptFunction = function
        self._routine_id: int = routine_id
        self._args: List[Expression] = args

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        arg_count = len(self._args)

        if arg_count > len(self._function.params):
            raise CompileException(f"Too many arguments passed to '{self._function.name}'.")

        for i, param in enumerate(self._function.params):
            if i >= arg_count:
                if param.default is None:
                    raise CompileException(f"Not enough arguments passed to '{self._function.name}'.")
                else:
                    if param.datatype == DataType.INT:
                        self._args.append(IntExpression(int(param.default)))
                    elif param.datatype == DataType.FLOAT:
                        self._args.append(FloatExpression(float(param.default)))
                    elif param.datatype == DataType.STRING:
                        self._args.append(StringExpression(param.default))
                    else:
                        raise CompileException(f"Unexpected compilation error at '{self._function.name}' call.")

        this_stack = 0
        for i, arg in enumerate(reversed(self._args)):
            param_type = self._function.params[-i - 1].datatype
            if param_type == DataType.ACTION:
                after_command = NCSInstruction()
                ncs.add(NCSInstructionType.STORE_STATE, args=[root.scope_size(), block.full_scope_size()])
                ncs.add(NCSInstructionType.JMP, jump=after_command)
                arg.compile(ncs, root, block)
                ncs.instructions.append(after_command)
            else:
                added = arg.compile(ncs, root, block)
                block.tempstack += added.size()
                this_stack += added.size()

                if added != param_type:
                    raise CompileException(f"Tried to pass an argument of the incorrect type to '{self._function.name}'.")

        ncs.instructions.append(NCSInstruction(NCSInstructionType.ACTION, [self._routine_id, len(self._args)]))
        block.tempstack -= this_stack
        return self._function.returntype


class FunctionCallExpression(Expression):
    def __init__(self, function: Identifier, args: List[Expression]):
        super().__init__()
        self._function: Identifier = function
        self._args: List[Expression] = args

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        return root.compile_jsr(ncs, block, self._function.label, *self._args)
# endregion


# region Expressions: Arithmetic
class AdditionExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        super().__init__()
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        type1 = self.expression1.compile(ncs, root, block)
        block.tempstack += 4
        type2 = self.expression2.compile(ncs, root, block)
        block.tempstack += 4

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
        return type1


class SubtractionExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        super().__init__()
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        type1 = self.expression1.compile(ncs, root, block)
        block.tempstack += 4
        type2 = self.expression2.compile(ncs, root, block)
        block.tempstack += 4

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
        return type1


class MultiplicationExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        super().__init__()
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        type1 = self.expression1.compile(ncs, root, block)
        block.tempstack += 4
        type2 = self.expression2.compile(ncs, root, block)
        block.tempstack += 4

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
        return type1


class DivisionExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        super().__init__()
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        type1 = self.expression1.compile(ncs, root, block)
        block.tempstack += 4
        type2 = self.expression2.compile(ncs, root, block)
        block.tempstack += 4

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
        return type1


class ModulusExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        super().__init__()
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        type1 = self.expression1.compile(ncs, root, block)
        block.tempstack += 4
        type2 = self.expression2.compile(ncs, root, block)
        block.tempstack += 4

        if type1 == DataType.INT and type1 == DataType.INT:
            ncs.add(NCSInstructionType.MODII)
        else:
            raise CompileException(f"Cannot get the modulus of {type1.name.lower()} and {type2.name.lower()}")

        block.tempstack -= 8
        return type1


class NegationExpression(Expression):
    def __init__(self, expression1: Expression):
        super().__init__()
        self.expression1: Expression = expression1

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        type1 = self.expression1.compile(ncs, root, block)
        block.tempstack += 4

        if type1 == DataType.INT:
            ncs.add(NCSInstructionType.NEGI)
        elif type1 == DataType.FLOAT:
            ncs.add(NCSInstructionType.NEGF)
        else:
            raise CompileException(f"Cannot negate {type1.name.lower()}")

        block.tempstack -= 4
        return type1
# endregion


# region Expressions: Logical
class LogicalNotExpression(Expression):
    def __init__(self, expression1: Expression):
        super().__init__()
        self.expression1: Expression = expression1

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        type1 = self.expression1.compile(ncs, root, block)
        block.tempstack += 4

        if type1 == DataType.INT:
            ncs.add(NCSInstructionType.NOTI)
        else:
            raise CompileException(f"Cannot get the logical NOT of {type1.name.lower()}")

        block.tempstack -= 4
        return DataType.INT


class LogicalAndExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        super().__init__()
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        type1 = self.expression1.compile(ncs, root, block)
        block.tempstack += 4
        type2 = self.expression2.compile(ncs, root, block)
        block.tempstack += 4

        if type1 == DataType.INT and type2 == DataType.INT:
            ncs.add(NCSInstructionType.LOGANDII)
        else:
            raise CompileException(f"Cannot get the logical AND of {type1.name.lower()} and {type2.name.lower()}")

        block.tempstack -= 8
        return DataType.INT


class LogicalOrExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        super().__init__()
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        type1 = self.expression1.compile(ncs, root, block)
        block.tempstack += 4
        type2 = self.expression2.compile(ncs, root, block)
        block.tempstack += 4

        if type1 == DataType.INT and type2 == DataType.INT:
            ncs.add(NCSInstructionType.LOGORII)
        else:
            raise CompileException(f"Cannot get the logical OR of {type1.name.lower()} and {type2.name.lower()}")

        block.tempstack -= 8
        return DataType.INT
# endregion


# region Expressions: Relational
class LogicalEqualityExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        super().__init__()
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        type1 = self.expression1.compile(ncs, root, block)
        block.tempstack += 4
        type2 = self.expression2.compile(ncs, root, block)
        block.tempstack += 4

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
        return DataType.INT


class LogicalInequalityExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        super().__init__()
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2
        self._type = None

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        type1 = self.expression1.compile(ncs, root, block)
        block.tempstack += 4
        type2 = self.expression2.compile(ncs, root, block)
        block.tempstack += 4

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
        return DataType.INT


class GreaterThanExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        super().__init__()
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        type1 = self.expression1.compile(ncs, root, block)
        block.tempstack += 4
        type2 = self.expression2.compile(ncs, root, block)
        block.tempstack += 4

        if type1 == DataType.INT and type2 == DataType.INT:
            ncs.add(NCSInstructionType.GTII)
        elif type1 == DataType.FLOAT and type2 == DataType.FLOAT:
            ncs.add(NCSInstructionType.GTFF)
        else:
            raise CompileException(f"Cannot test if {type1.name.lower()} is greater than {type2.name.lower()}")

        block.tempstack -= 8
        return DataType.INT


class GreaterThanOrEqualExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        super().__init__()
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2
        self._type = None

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        type1 = self.expression1.compile(ncs, root, block)
        block.tempstack += 4
        type2 = self.expression2.compile(ncs, root, block)
        block.tempstack += 4

        if type1 == DataType.INT and type2 == DataType.INT:
            ncs.add(NCSInstructionType.GEQII)
        elif type1 == DataType.FLOAT and type2 == DataType.FLOAT:
            ncs.add(NCSInstructionType.GEQFF)
        else:
            raise CompileException(f"Cannot test if {type1.name.lower()} is greater than or equal to {type2.name.lower()}")

        block.tempstack -= 8
        return DataType.INT


class LessThanExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        super().__init__()
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2
        self._type = None

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        type1 = self.expression1.compile(ncs, root, block)
        block.tempstack += 4
        type2 = self.expression2.compile(ncs, root, block)
        block.tempstack += 4

        if type1 == DataType.INT and type2 == DataType.INT:
            ncs.add(NCSInstructionType.LTII)
        elif type1 == DataType.FLOAT and type2 == DataType.FLOAT:
            ncs.add(NCSInstructionType.LTFF)
        else:
            raise CompileException(f"Cannot test if {type1.name.lower()} is less than {type2.name.lower()}")

        block.tempstack -= 8
        return DataType.INT


class LessThanOrEqualExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        super().__init__()
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2
        self._type = None

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        type1 = self.expression1.compile(ncs, root, block)
        block.tempstack += 4
        type2 = self.expression2.compile(ncs, root, block)
        block.tempstack += 4

        if type1 == DataType.INT and type2 == DataType.INT:
            ncs.add(NCSInstructionType.LEQII)
        elif type1 == DataType.FLOAT and type2 == DataType.FLOAT:
            ncs.add(NCSInstructionType.LEQFF)
        else:
            raise CompileException(f"Cannot test if {type1.name.lower()} is less than {type2.name.lower()}")

        block.tempstack -= 8
        return DataType.INT
# endregion


# region Expression: Bitwise
class BitwiseOrExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        super().__init__()
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        type1 = self.expression1.compile(ncs, root, block)
        block.tempstack += 4
        type2 = self.expression2.compile(ncs, root, block)
        block.tempstack += 4

        if type1 == DataType.INT and type2 == DataType.INT:
            ncs.add(NCSInstructionType.INCORII)
        else:
            raise CompileException(f"Cannot get the bitwise OR of {type1.name.lower()} and {type2.name.lower()}")

        block.tempstack -= 8
        return type1


class BitwiseXorExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        super().__init__()
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        type1 = self.expression1.compile(ncs, root, block)
        block.tempstack += 4
        type2 = self.expression2.compile(ncs, root, block)
        block.tempstack += 4

        if type1 == DataType.INT and type2 == DataType.INT:
            ncs.add(NCSInstructionType.EXCORII)
        else:
            raise CompileException(f"Cannot get the bitwise XOR of {type1.name.lower()} and {type2.name.lower()}")

        block.tempstack -= 8
        return type1


class BitwiseAndExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        super().__init__()
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        type1 = self.expression1.compile(ncs, root, block)
        block.tempstack += 4
        type2 = self.expression2.compile(ncs, root, block)
        block.tempstack += 4

        if type1 == DataType.INT and type2 == DataType.INT:
            ncs.add(NCSInstructionType.BOOLANDII)
        else:
            raise CompileException(f"Cannot get the bitwise AND of {type1.name.lower()} and {type2.name.lower()}")

        block.tempstack -= 8
        return type1


class BitwiseNotExpression(Expression):
    def __init__(self, expression1: Expression):
        super().__init__()
        self.expression1: Expression = expression1

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        type1 = self.expression1.compile(ncs, root, block)
        block.tempstack += 4

        if type1 == DataType.INT:
            ncs.add(NCSInstructionType.COMPI)
        else:
            raise CompileException(f"Cannot get one's complement of {type1.name.lower()}")

        block.tempstack -= 4
        return type1


class BitwiseLeftShiftExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        super().__init__()
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        type1 = self.expression1.compile(ncs, root, block)
        block.tempstack += 4
        type2 = self.expression2.compile(ncs, root, block)
        block.tempstack += 4

        if type1 == DataType.INT and type2 == DataType.INT:
            ncs.add(NCSInstructionType.SHLEFTII)
        else:
            raise CompileException(f"Cannot bitshift {type1.name.lower()} with {type2.name.lower()}")

        block.tempstack -= 8
        return type1


class BitwiseRightShiftExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression):
        super().__init__()
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        type1 = self.expression1.compile(ncs, root, block)
        block.tempstack += 4
        type2 = self.expression2.compile(ncs, root, block)
        block.tempstack += 4

        if type1 == DataType.INT and type2 == DataType.INT:
            ncs.add(NCSInstructionType.SHRIGHTII)
        else:
            raise CompileException(f"Cannot bitshift {type1.name.lower()} with {type2.name.lower()}")

        block.tempstack -= 8
        return type1
# endregion


# region Expressions: Assignment
class Assignment(Expression):
    def __init__(self, identifier: Identifier, value: Expression):
        super().__init__()
        self.identifier: Identifier = identifier
        self.expression: Expression = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        variable_type = self.expression.compile(ncs, root, block)

        isglobal, expression_type, stack_index = block.get_scoped(self.identifier, root)
        instruction_type = NCSInstructionType.CPDOWNBP if isglobal else NCSInstructionType.CPDOWNSP
        stack_index -= variable_type.size()

        if variable_type != expression_type:
            raise CompileException(f"Wrong type was assigned to symbol {self.identifier}.")

        # Copy the value that the expression has already been placed on the stack to where the identifiers position is
        ncs.instructions.append(NCSInstruction(instruction_type, [stack_index, expression_type.size()]))
        # Remove the temporary value from the stack that the expression created
        ncs.instructions.append(NCSInstruction(NCSInstructionType.MOVSP, [-expression_type.size()]))

        return variable_type


class AdditionAssignment(Expression):
    def __init__(self, identifier: Identifier, value: Expression):
        super().__init__()
        self.identifier: Identifier = identifier
        self.expression: Expression = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        # Copy the variable to the top of the stack
        isglobal, variable_type, stack_index = block.get_scoped(self.identifier, root)
        instruction_type = NCSInstructionType.CPTOPBP if isglobal else NCSInstructionType.CPTOPSP
        ncs.add(instruction_type, args=[stack_index, variable_type.size()])

        # Add the result of the expression to the stack
        expresion_type = self.expression.compile(ncs, root, block)
        block.tempstack += expresion_type.size()

        # Determine what instruction to apply to the two values
        if variable_type == DataType.INT and expresion_type == DataType.INT:
            arthimetic_instruction = NCSInstructionType.ADDII
        elif variable_type == DataType.INT and expresion_type == DataType.FLOAT:
            arthimetic_instruction = NCSInstructionType.ADDIF
        elif variable_type == DataType.FLOAT and expresion_type == DataType.FLOAT:
            arthimetic_instruction = NCSInstructionType.ADDFF
        elif variable_type == DataType.FLOAT and expresion_type == DataType.INT:
            arthimetic_instruction = NCSInstructionType.ADDFI
        elif variable_type == DataType.STRING and expresion_type == DataType.STRING:
            arthimetic_instruction = NCSInstructionType.ADDSS
        else:
            raise CompileException(f"Wrong type was assigned to symbol {self.identifier}.")

        # Add the expression and our temp variable copy together
        ncs.add(arthimetic_instruction)
        # Copy the result to the original variable in the stack
        ncs.add(NCSInstructionType.CPDOWNSP, args=[stack_index - expresion_type.size(), variable_type.size()])
        # Pop the temp variable
        ncs.add(NCSInstructionType.MOVSP, args=[-variable_type.size()])

        block.tempstack -= expresion_type.size()
        return expresion_type


class SubtractionAssignment(Expression):
    def __init__(self, identifier: Identifier, value: Expression):
        super().__init__()
        self.identifier: Identifier = identifier
        self.expression: Expression = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        # Copy the variable to the top of the stack
        isglobal, variable_type, stack_index = block.get_scoped(self.identifier, root)
        instruction_type = NCSInstructionType.CPTOPBP if isglobal else NCSInstructionType.CPTOPSP
        ncs.add(instruction_type, args=[stack_index, variable_type.size()])

        # Add the result of the expression to the stack
        expresion_type = self.expression.compile(ncs, root, block)
        block.tempstack += expresion_type.size()

        # Determine what instruction to apply to the two values
        if variable_type == DataType.INT and expresion_type == DataType.INT:
            arthimetic_instruction = NCSInstructionType.SUBII
        elif variable_type == DataType.INT and expresion_type == DataType.FLOAT:
            arthimetic_instruction = NCSInstructionType.SUBIF
        elif variable_type == DataType.FLOAT and expresion_type == DataType.FLOAT:
            arthimetic_instruction = NCSInstructionType.SUBFF
        elif variable_type == DataType.FLOAT and expresion_type == DataType.INT:
            arthimetic_instruction = NCSInstructionType.SUBFI
        else:
            raise CompileException(f"Wrong type was assigned to symbol {self.identifier}.")

        # Add the expression and our temp variable copy together
        ncs.add(arthimetic_instruction)
        # Copy the result to the original variable in the stack
        ncs.add(NCSInstructionType.CPDOWNSP, args=[stack_index - expresion_type.size(), variable_type.size()])
        # Pop the temp variable
        ncs.add(NCSInstructionType.MOVSP, args=[-variable_type.size()])

        block.tempstack -= expresion_type.size()
        return expresion_type


class MultiplicationAssignment(Expression):
    def __init__(self, identifier: Identifier, value: Expression):
        super().__init__()
        self.identifier: Identifier = identifier
        self.expression: Expression = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        # Copy the variable to the top of the stack
        isglobal, variable_type, stack_index = block.get_scoped(self.identifier, root)
        instruction_type = NCSInstructionType.CPTOPBP if isglobal else NCSInstructionType.CPTOPSP
        ncs.add(instruction_type, args=[stack_index, variable_type.size()])

        # Add the result of the expression to the stack
        expresion_type = self.expression.compile(ncs, root, block)
        block.tempstack += expresion_type.size()

        # Determine what instruction to apply to the two values
        if variable_type == DataType.INT and expresion_type == DataType.INT:
            arthimetic_instruction = NCSInstructionType.MULII
        elif variable_type == DataType.INT and expresion_type == DataType.FLOAT:
            arthimetic_instruction = NCSInstructionType.MULIF
        elif variable_type == DataType.FLOAT and expresion_type == DataType.FLOAT:
            arthimetic_instruction = NCSInstructionType.MULFF
        elif variable_type == DataType.FLOAT and expresion_type == DataType.INT:
            arthimetic_instruction = NCSInstructionType.MULFI
        else:
            raise CompileException(f"Wrong type was assigned to symbol {self.identifier}.")

        # Add the expression and our temp variable copy together
        ncs.add(arthimetic_instruction)
        # Copy the result to the original variable in the stack
        ncs.add(NCSInstructionType.CPDOWNSP, args=[stack_index - expresion_type.size(), variable_type.size()])
        # Pop the temp variable
        ncs.add(NCSInstructionType.MOVSP, args=[-variable_type.size()])

        block.tempstack -= expresion_type.size()
        return expresion_type


class DivisionAssignment(Expression):
    def __init__(self, identifier: Identifier, value: Expression):
        super().__init__()
        self.identifier: Identifier = identifier
        self.expression: Expression = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DataType:
        # Copy the variable to the top of the stack
        isglobal, variable_type, stack_index = block.get_scoped(self.identifier, root)
        instruction_type = NCSInstructionType.CPTOPBP if isglobal else NCSInstructionType.CPTOPSP
        ncs.add(instruction_type, args=[stack_index, variable_type.size()])

        # Add the result of the expression to the stack
        expresion_type = self.expression.compile(ncs, root, block)
        block.tempstack += expresion_type.size()

        # Determine what instruction to apply to the two values
        if variable_type == DataType.INT and expresion_type == DataType.INT:
            arthimetic_instruction = NCSInstructionType.DIVII
        elif variable_type == DataType.INT and expresion_type == DataType.FLOAT:
            arthimetic_instruction = NCSInstructionType.DIVIF
        elif variable_type == DataType.FLOAT and expresion_type == DataType.FLOAT:
            arthimetic_instruction = NCSInstructionType.DIVFF
        elif variable_type == DataType.FLOAT and expresion_type == DataType.INT:
            arthimetic_instruction = NCSInstructionType.DIVFI
        else:
            raise CompileException(f"Wrong type was assigned to symbol {self.identifier}.")

        # Add the expression and our temp variable copy together
        ncs.add(arthimetic_instruction)
        # Copy the result to the original variable in the stack
        ncs.add(NCSInstructionType.CPDOWNSP, args=[stack_index - expresion_type.size(), variable_type.size()])
        # Pop the temp variable
        ncs.add(NCSInstructionType.MOVSP, args=[-variable_type.size()])

        block.tempstack -= expresion_type.size()
        return expresion_type
# endregion


# region Statements
class EmptyStatement(Statement):
    def __init__(self):
        super().__init__()

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock, return_instruction: NCSInstruction,
                break_instruction: Optional[NCSInstruction], continue_instruction: Optional[NCSInstruction]):
        return DataType.VOID


class ExpressionStatement(Statement):
    def __init__(self, expression: Expression):
        super().__init__()
        self.expression: Expression = expression

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock, return_instruction: NCSInstruction,
                break_instruction: Optional[NCSInstruction], continue_instruction: Optional[NCSInstruction]):
        self.expression.compile(ncs, root, block)


class DeclarationStatement(Statement):
    def __init__(self, identifier: Identifier, data_type: DataType, value: Expression):
        super().__init__()
        self.identifier: Identifier = identifier
        self.data_type: DataType = data_type
        self.expression: Expression = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock, return_instruction: NCSInstruction,
                break_instruction: Optional[NCSInstruction], continue_instruction: Optional[NCSInstruction]):
        expression_type = self.expression.compile(ncs, root, block)
        if expression_type != self.data_type:
            raise CompileException(f"Tried to declare '{self.identifier}' a new variable with incorrect type '{expression_type}'.")
        block.add_scoped(self.identifier, self.data_type)


class ConditionalBlock(Statement):
    def __init__(self, if_block: ConditionAndBlock, else_if_blocks: List[ConditionAndBlock], else_block: CodeBlock):
        super().__init__()
        self.if_block: ConditionAndBlock = if_block
        self.else_if_blocks: List[ConditionAndBlock] = else_if_blocks
        self.else_block: Optional[CodeBlock] = else_block

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock, return_instruction: NCSInstruction,
                break_instruction: Optional[NCSInstruction], continue_instruction: Optional[NCSInstruction]):

        jump_count = 1 + 1 + len(self.else_if_blocks)
        jump_tos = [NCSInstruction(NCSInstructionType.NOP, args=[]) for i in range(jump_count)]

        self.if_block.condition.compile(ncs, root, block)
        ncs.add(NCSInstructionType.JZ, jump=jump_tos[0])

        self.if_block.block.compile(ncs, root, block, return_instruction, break_instruction, continue_instruction)
        ncs.add(NCSInstructionType.JMP, jump=jump_tos[-1])

        ncs.instructions.append(jump_tos[0])

        for i, else_if in enumerate(self.else_if_blocks):
            else_if.condition.compile(ncs, root, block)
            ncs.add(NCSInstructionType.JZ, jump=jump_tos[i + 1])

            else_if.block.compile(ncs, root, block, return_instruction, break_instruction, continue_instruction)
            ncs.add(NCSInstructionType.JMP, jump=jump_tos[-1])

            ncs.instructions.append(jump_tos[i + 1])

        if self.else_block is not None:
            self.else_block.compile(ncs, root, block, return_instruction, break_instruction, continue_instruction)

        ncs.instructions.append(jump_tos[-1])

        '''self.condition.compile(ncs, root, block)
        jz = ncs.add(NCSInstructionType.JZ, jump=None)
        self.if_block.compile(ncs, root, block, return_instruction, break_instruction, continue_instruction)
        block_end = ncs.add(NCSInstructionType.NOP, args=[])

        # Set the Jump If Zero instruction to jump to the end of the block
        jz.jump = block_end'''


class ConditionAndBlock:
    def __init__(self, condition: Expression, block: CodeBlock):
        self.condition: Expression = condition
        self.block: CodeBlock = block


class ReturnStatement(Statement):
    def __init__(self, expression: Optional[Expression] = None):
        super().__init__()
        self.expression: Optional[Expression] = expression

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock, return_instruction: NCSInstruction,
                break_instruction: Optional[NCSInstruction], continue_instruction: Optional[NCSInstruction]):
        if self.expression is not None:
            return self.expression.compile(ncs, root, block)
        return DataType.VOID


class WhileLoopBlock(Statement):
    def __init__(self, condition: Expression, block: CodeBlock):
        super().__init__()
        self.condition: Expression = condition
        self.block: CodeBlock = block

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock, return_instruction: NCSInstruction,
                break_instruction: Optional[NCSInstruction], continue_instruction: Optional[NCSInstruction]):
        # Tell break/continue statements to stop here when getting scope size
        block.mark_break_scope()

        loopstart = ncs.add(NCSInstructionType.NOP, args=[])
        loopend = NCSInstruction(NCSInstructionType.NOP, args=[])
        condition_type = self.condition.compile(ncs, root, block)

        if condition_type != DataType.INT:
            raise CompileException("Condition must be int type.")

        ncs.add(NCSInstructionType.JZ, jump=loopend)
        self.block.compile(ncs, root, block, return_instruction, loopend, loopstart)
        ncs.add(NCSInstructionType.JMP, jump=loopstart)

        ncs.instructions.append(loopend)


class DoWhileLoopBlock(Statement):
    def __init__(self, condition: Expression, block: CodeBlock):
        super().__init__()
        self.condition: Expression = condition
        self.block: CodeBlock = block

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock, return_instruction: NCSInstruction,
                break_instruction: Optional[NCSInstruction], continue_instruction: Optional[NCSInstruction]):
        # Tell break/continue statements to stop here when getting scope size
        block.mark_break_scope()

        loopstart = ncs.add(NCSInstructionType.NOP, args=[])
        conditionstart = NCSInstruction(NCSInstructionType.NOP, args=[])
        loopend = NCSInstruction(NCSInstructionType.NOP, args=[])

        self.block.compile(ncs, root, block, return_instruction, loopend, conditionstart)

        ncs.instructions.append(conditionstart)
        condition_type = self.condition.compile(ncs, root, block)
        if condition_type != DataType.INT:
            raise CompileException("Condition must be int type.")

        ncs.add(NCSInstructionType.JZ, jump=loopend)
        ncs.add(NCSInstructionType.JMP, jump=loopstart)
        ncs.instructions.append(loopend)


class ForLoopBlock(Statement):
    def __init__(self, initial: Expression, condition: Expression, iteration: Expression, block: CodeBlock):
        super().__init__()
        self.initial: Expression = initial
        self.condition: Expression = condition
        self.iteration: Expression = iteration
        self.block: CodeBlock = block

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock, return_instruction: NCSInstruction,
                break_instruction: Optional[NCSInstruction], continue_instruction: Optional[NCSInstruction]):
        # Tell break/continue statements to stop here when getting scope size
        block.mark_break_scope()

        self.initial.compile(ncs, root, block)

        loopstart = ncs.add(NCSInstructionType.NOP, args=[])
        updatestart = NCSInstruction(NCSInstructionType.NOP, args=[])
        loopend = NCSInstruction(NCSInstructionType.NOP, args=[])

        condition_type = self.condition.compile(ncs, root, block)
        if condition_type != DataType.INT:
            raise CompileException("Condition must be int type.")

        ncs.add(NCSInstructionType.JZ, jump=loopend)
        self.block.compile(ncs, root, block, return_instruction, loopend, updatestart)

        ncs.instructions.append(updatestart)
        self.iteration.compile(ncs, root, block)
        ncs.add(NCSInstructionType.JMP, jump=loopstart)
        ncs.instructions.append(loopend)
# endregion


class BreakStatement(Statement):
    def __init__(self):
        super().__init__()

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock, return_instruction: NCSInstruction,
                break_instruction: Optional[NCSInstruction], continue_instruction: Optional[NCSInstruction]):
        if break_instruction is None:
            raise CompileException("Nothing to break out of.")
        ncs.add(NCSInstructionType.MOVSP, args=[-block.break_scope_size()])
        ncs.add(NCSInstructionType.JMP, jump=break_instruction)
        ncs.add(NCSInstructionType.NOP, args=["YEA REMEMBER TO DELETE THIS MY DUDE"])


class ContinueStatement(Statement):
    def __init__(self):
        super().__init__()

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock, return_instruction: NCSInstruction,
                break_instruction: Optional[NCSInstruction], continue_instruction: Optional[NCSInstruction]):
        if continue_instruction is None:
            raise CompileException("Nothing to continue out of.")
        ncs.add(NCSInstructionType.MOVSP, args=[-block.break_scope_size()])
        ncs.add(NCSInstructionType.JMP, jump=continue_instruction)


# region Switch
class SwitchStatement(Statement):
    def __init__(self, expression: Expression, blocks: List[SwitchBlock]):
        super().__init__()
        self.expression: Expression = expression
        self.blocks: List[SwitchBlock] = blocks

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock, return_instruction: NCSInstruction,
                break_instruction: Optional[NCSInstruction], continue_instruction: Optional[NCSInstruction]):
        expression_type = self.expression.compile(ncs, root, block)
        block.tempstack += expression_type.size()

        end_of_switch = NCSInstruction(NCSInstructionType.NOP, args=[])

        tempncs = NCS()
        switchblock_to_instruction = {}
        for switchblock in self.blocks:
            switchblock_start = tempncs.add(NCSInstructionType.NOP, args=[])
            switchblock_to_instruction[switchblock] = switchblock_start
            for statement in switchblock.block:
                statement.compile(tempncs, root, block, return_instruction, end_of_switch, None)

        for switchblock in self.blocks:
            for label in switchblock.labels:
                # Do not want to run switch expression multiple times, execute it once and copy it to the top
                ncs.add(NCSInstructionType.CPTOPSP, args=[-expression_type.size(), expression_type.size()])
                label.compile(ncs, root, block, switchblock_to_instruction[switchblock], expression_type)
        # If none of the labels match, jump over the code block
        ncs.add(NCSInstructionType.JMP, jump=end_of_switch)

        ncs.merge(tempncs)
        ncs.instructions.append(end_of_switch)

        # Pop the Switch expression
        ncs.add(NCSInstructionType.MOVSP, args=[-4])
        block.tempstack -= expression_type.size()


class SwitchBlock:
    def __init__(self, labels: List[SwitchLabel], block: List[Statement]):
        self.labels: List[SwitchLabel] = labels
        self.block: List[Statement] = block


class SwitchLabel(ABC):
    @abstractmethod
    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock, jump_to: NCSInstruction, expression_type: DataType):
        ...


class ExpressionSwitchLabel:
    def __init__(self, expression: Expression):
        self.expression: Expression = expression

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock, jump_to: NCSInstruction, expression_type: DataType):
        # Compare the copied Switch expression to the Label expression
        label_type = self.expression.compile(ncs, root, block)
        equality_instruction = get_logical_equality_instruction(expression_type, label_type)
        ncs.add(equality_instruction, args=[])

        # If the expressions match, then we jump to the appropriate place, otherwise continue trying the
        # other Labels
        ncs.add(NCSInstructionType.JNZ, jump=jump_to)


class DefaultSwitchLabel:
    def __init__(self):
        ...

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock, jump_to: NCSInstruction, expression_type: DataType):
        ncs.add(NCSInstructionType.JMP, jump=jump_to)
# endregion
