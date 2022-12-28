from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from enum import Enum
from typing import List, Optional, Tuple, Dict, NamedTuple, Union, Any
from pykotor.common.script import DataType, ScriptFunction, ScriptConstant
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
    def __init__(self, identifier: Identifier, data_type: DynamicDataType, value: Expression):
        super().__init__()
        self.identifier: Identifier = identifier
        self.data_type: DynamicDataType = data_type
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


class OperatorMapping(NamedTuple):
    unary: List[UnaryOperatorMapping]
    binary: List[BinaryOperatorMapping]


class BinaryOperatorMapping:
    def __init__(self, instruction: NCSInstructionType, lhs: DataType, rhs: DataType):
        self.instruction: NCSInstructionType = instruction
        self.lhs: DataType = lhs
        self.rhs: DataType = rhs


class UnaryOperatorMapping:
    def __init__(self, instruction: NCSInstructionType, rhs: DataType):
        self.instruction: NCSInstructionType = instruction
        self.rhs: DataType = rhs


class FunctionReference(NamedTuple):
    instruction: NCSInstruction
    definition: Union[FunctionForwardDeclaration, FunctionDefinition]

    def is_prototype(self) -> bool:
        return isinstance(self.definition, FunctionForwardDeclaration)


class GetScopedResult(NamedTuple):
    isglobal: bool
    datatype: DynamicDataType
    offset: int


class Struct:
    def __init__(self, identifier: Identifier, members: List[StructMember]):
        self.identifier: Identifier = identifier
        self.members: List[StructMember] = members

    def initialize(self, ncs: NCS, root: CodeRoot) -> None:
        for member in self.members:
            member.initialize(ncs, root)

    def size(self, root: CodeRoot) -> int:
        # TODO: One-time calculation in __init__
        size = 0
        for member in self.members:
            size += member.size(root)
        return size

    def child_offset(self, root: CodeRoot, identifier: Identifier) -> int:
        """
        Returns the relative offset to the specified member inside the struct.
        """
        size = 0
        for member in self.members:
            if member.identifier == identifier:
                break
            size += member.size(root)
        else:
            raise CompileException  # TODO
        return size

    def child_type(self, root: CodeRoot, identifier: Identifier) -> DynamicDataType:
        """
        Returns the child data type of the specified member inside the struct.
        """
        for member in self.members:
            if member.identifier == identifier:
                return member.datatype
        else:
            raise CompileException


class StructMember:
    def __init__(self, datatype: DynamicDataType, identifier: Identifier):
        self.datatype: DynamicDataType = datatype
        self.identifier: Identifier = identifier

    def initialize(self, ncs: NCS, root: CodeRoot) -> None:
        if self.datatype.builtin == DataType.INT:
            ncs.add(NCSInstructionType.RSADDI, args=[])
        elif self.datatype.builtin == DataType.FLOAT:
            ncs.add(NCSInstructionType.RSADDF, args=[])
        elif self.datatype.builtin == DataType.STRING:
            ncs.add(NCSInstructionType.RSADDS, args=[])
        elif self.datatype.builtin == DataType.OBJECT:
            ncs.add(NCSInstructionType.RSADDO, args=[])
        elif self.datatype.builtin == DataType.STRUCT:
            root.struct_map[self.identifier.label].initialize(ncs, root)
        else:
            raise CompileException

    def size(self, root: CodeRoot):
        return self.datatype.size(root)


class CodeRoot:
    def __init__(self, constants: List[ScriptConstant]):
        self.objects: List[TopLevelObject] = []

        self.function_map: Dict[str, FunctionReference] = {}
        self.constants: List[ScriptConstant] = constants
        self._global_scope: List[ScopedValue] = []
        self.struct_map: Dict[str, Struct] = {}

    def compile(self, ncs: NCS):
        # nwnnsscomp processes the includes and global variable declarations before functions regardless if they are
        # placed before or after function definitions. We will replicate this behaviour.

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

    def compile_jsr(self, ncs: NCS, block: CodeBlock, name: str, *args: Expression) -> DynamicDataType:
        if name not in self.function_map:
            raise CompileException(f"Function '{name}' has not been defined.")

        args = list(args)

        func_map = self.function_map[name]
        definition = func_map.definition
        start_instruction = func_map.instruction

        if definition.return_type == DynamicDataType.INT:
            ncs.add(NCSInstructionType.RSADDI, args=[])
        elif definition.return_type == DynamicDataType.FLOAT:
            ncs.add(NCSInstructionType.RSADDF, args=[])
        elif definition.return_type == DynamicDataType.STRING:
            ncs.add(NCSInstructionType.RSADDS, args=[])
        elif definition.return_type == DynamicDataType.VECTOR:
            raise NotImplementedError("Cannot define a function that returns Vector yet")  # TODO
        elif definition.return_type == DynamicDataType.OBJECT:
            ncs.add(NCSInstructionType.RSADDO, args=[])
        elif definition.return_type == DynamicDataType.VOID:
            ...
        else:
            raise NotImplementedError("Trying to return unsupported type?")  # TODO

        required_params = [param for param in definition.parameters if param.default is None]

        # Make sure the minimal number of arguments were passed through
        if len(required_params) > len(args):
            raise CompileException(f"Required argument missing in call to '{name}'.")

        # If some optional parameters were not specified, add the defaults to the arguments list
        while len(definition.parameters) > len(args):
            param_index = len(args)
            args.append(definition.parameters[param_index].default)

        for param, arg in zip(definition.parameters, args):
            arg_datatype = arg.compile(ncs, self, block)
            if param.data_type != arg_datatype:
                raise CompileException
        ncs.add(NCSInstructionType.JSR, jump=start_instruction)

        return definition.return_type

    def add_scoped(self, identifier: Identifier, datatype: DynamicDataType) -> None:
        self._global_scope.insert(0, ScopedValue(identifier, datatype))

    def get_scoped(self, identifier: Identifier, root: CodeRoot) -> GetScopedResult:
        offset = 0
        for scoped in self._global_scope:
            offset -= scoped.data_type.size(root)
            if scoped.identifier == identifier:
                break
        else:
            raise CompileException(f"Could not find variable '{identifier}'.")
        return GetScopedResult(True, scoped.data_type, offset)

    def scope_size(self):
        offset = 0
        for scoped in self._global_scope:
            offset -= scoped.data_type.size(self)
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
                scope_size = self.full_scope_size(root)

                return_type = statement.compile(ncs, root, self, return_instruction, None, None)
                if return_type != DynamicDataType.VOID:
                    ncs.add(NCSInstructionType.CPDOWNSP, args=[-scope_size-return_type.size(root)*2, 4])
                    ncs.add(NCSInstructionType.MOVSP, args=[-return_type.size(root)])

                ncs.add(NCSInstructionType.MOVSP, args=[-scope_size])
                ncs.add(NCSInstructionType.JMP, jump=return_instruction)
                return
            else:
                statement.compile(ncs, root, self, return_instruction, break_instruction, continue_instruction)
        ncs.instructions.append(NCSInstruction(NCSInstructionType.MOVSP, [-self.scope_size(root)]))

        if self.tempstack != 0:
            # If the temp stack is 0 after the whole block has compiled there must be an logic error in the code
            # of one of the expression/statement classes
            raise ValueError

    def add_scoped(self, identifier: Identifier, data_type: DynamicDataType):
        self.scope.insert(0, ScopedValue(identifier, data_type))

    def get_scoped(self, identifier: Identifier, root: CodeRoot, offset: int = None) -> GetScopedResult:
        offset = -self.tempstack if offset is None else offset
        for scoped in self.scope:
            offset -= scoped.data_type.size(root)
            if scoped.identifier == identifier:
                break
        else:
            if self._parent is not None:
                return self._parent.get_scoped(identifier, root, offset)
            else:
                return root.get_scoped(identifier, root)
        return GetScopedResult(False, scoped.data_type, offset)

    def scope_size(self, root: CodeRoot) -> int:
        """Returns size of local scope."""
        size = 0
        for scoped in self.scope:
            size += scoped.data_type.size(root)
        return size

    def full_scope_size(self, root: CodeRoot) -> int:
        """Returns size of scope, including outer blocks."""
        size = 0
        size += self.scope_size(root)
        if self._parent is not None:
            size += self._parent.full_scope_size(root)
        return size

    def break_scope_size(self, root: CodeRoot) -> int:
        """Returns size of scope up to the nearest loop/switch statement."""
        size = 0
        size += self.scope_size(root)
        if self._parent is not None and not self._parent._break_scope:
            size += self._parent.break_scope_size(root)
        return size

    def mark_break_scope(self) -> None:
        self._break_scope = True


class ScopedValue:
    def __init__(self, identifier: Identifier, data_type: DynamicDataType):
        self.identifier: Identifier = identifier
        self.data_type: DynamicDataType = data_type


class FunctionForwardDeclaration(TopLevelObject):
    def __init__(self, return_type: DynamicDataType, identifier: Identifier, parameters: List[FunctionDefinitionParam]):
        self.return_type: DynamicDataType = return_type
        self.identifier: Identifier = identifier
        self.parameters: List[FunctionDefinitionParam] = parameters

    def compile(self, ncs: NCS, root: CodeRoot):
        function_name = self.identifier.label

        if self.identifier.label in root.function_map:
            raise CompileException(f"Function '{function_name}' already has a prototype or been defined.")

        root.function_map[self.identifier.label] = FunctionReference(ncs.add(NCSInstructionType.NOP, args=[]), self)


class FunctionDefinition(TopLevelObject):
    # TODO: split definition into signature + block?
    def __init__(self, return_type: DynamicDataType, identifier: Identifier, parameters: List[FunctionDefinitionParam], block: CodeBlock):
        self.return_type: DynamicDataType = return_type
        self.identifier: Identifier = identifier
        self.parameters: List[FunctionDefinitionParam] = parameters
        self.block: CodeBlock = block

        for param in parameters:
            block.add_scoped(param.identifier, param.data_type)

    def compile(self, ncs: NCS, root: CodeRoot):
        name = self.identifier.label

        # Make sure all default parameters appear after the required parameters
        previous_is_default = False
        for param in self.parameters:
            is_default = param.default is not None
            if previous_is_default and not is_default:
                raise CompileException("Function parameter without a default value can't follow one with a default value.")
            previous_is_default = is_default

        if name in root.function_map and not root.function_map[name].is_prototype():
            raise CompileException(f"Function '{name}' has already been defined.")
        elif name in root.function_map and root.function_map[name].is_prototype():

            if not self.is_matching_signature(root.function_map[name].definition):
                raise CompileException(f"Prototype of function '{name}' does not match definition.")

            # Function has forward declaration, insert the compiled definition after the stub
            temp = NCS()
            retn = NCSInstruction(NCSInstructionType.RETN)
            self.block.compile(temp, root, None, retn, None, None)
            temp.instructions.append(retn)

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
        if len(self.parameters) != len(prototype.parameters):
            return False
        for i in range(len(self.parameters)):
            if self.parameters[i].data_type != prototype.parameters[i].data_type:
                return False
            if self.parameters[i].default != prototype.parameters[i].default:
                return False

        return True


class FunctionDefinitionParam:
    def __init__(self, data_type: DynamicDataType, identifier: Identifier, default: Optional[Expression] = None):
        self.data_type: DynamicDataType = data_type
        self.identifier: Identifier = identifier
        self.default: Optional[Expression] = default


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


class StructDefinition(TopLevelObject):
    def __init__(self, identifier: Identifier, members: List[StructMember]):
        self.identifier: Identifier = identifier
        self.members: List[StructMember] = members

    def compile(self, ncs: NCS, root: CodeRoot) -> None:
        if len(self.members) == 0:
            raise CompileException("Struct cannot be empty.")
        root.struct_map[self.identifier.label] = Struct(self.identifier, self.members)


class Expression(ABC):
    @abstractmethod
    def compile(self, ncs: NCS, root: CodeRoot, block: Optional[CodeBlock]) -> DynamicDataType:
        ...


class Statement(ABC):
    def __init__(self):
        self.linenum: Optional[None] = None

    @abstractmethod
    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock, return_instruction: NCSInstruction,
                break_instruction: Optional[NCSInstruction], continue_instruction: Optional[NCSInstruction]):
        ...


class FieldAccess:
    def __init__(self, identifiers: List[Identifier]):
        super().__init__()
        self.identifiers: List[Identifier] = identifiers

    def get_scoped(self, block: CodeBlock, root: CodeRoot) -> GetScopedResult:
        if len(self.identifiers) == 0:
            raise CompileException

        first = self.identifiers[0]
        scoped = block.get_scoped(first, root)

        isglobal = scoped.isglobal
        offset = scoped.offset
        datatype = scoped.datatype

        for next in self.identifiers[1:]:
            # Check previous datatype to see what members are accessible
            if datatype.builtin == DataType.VECTOR:
                datatype = DynamicDataType.FLOAT
                if next.label == "x":
                    offset += 0
                elif next.label == "y":
                    offset += 4
                elif next.label == "z":
                    offset += 8
                else:
                    raise CompileException(f"Attempting to access unknown member '{next}' on datatype '{datatype}'.")
            elif datatype.builtin == DataType.STRUCT:
                offset += root.struct_map[datatype._struct].child_offset(root, next)
                datatype = root.struct_map[datatype._struct].child_type(root, next)
            else:
                raise CompileException(f"Attempting to access unknown member '{next}' on datatype '{datatype}'.")

        return GetScopedResult(isglobal, datatype, offset)

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        isglobal, variable_type, stack_index = self.get_scoped(block, root)
        instruction_type = NCSInstructionType.CPTOPBP if isglobal else NCSInstructionType.CPTOPSP
        ncs.add(instruction_type, args=[stack_index, variable_type.size(root)])
        return variable_type


# region Expressions: Simple
class IdentifierExpression(Expression):
    def __init__(self, value: Identifier):
        super().__init__()
        self.identifier: Identifier = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        # Scan for any constants that are stored as part of the compiler (from nwscript).
        constant = next((constant for constant in root.constants if constant.name == self.identifier.label), None)
        if constant is not None:
            if constant.datatype == DataType.INT:
                ncs.add(NCSInstructionType.CONSTI, args=[int(constant.value)])
            elif constant.datatype == DataType.FLOAT:
                ncs.add(NCSInstructionType.CONSTF, args=[float(constant.value)])
            elif constant.datatype == DataType.STRING:
                ncs.add(NCSInstructionType.CONSTS, args=[str(constant.value)])
            return DynamicDataType(constant.datatype)
        else:
            isglobal, datatype, stack_index = block.get_scoped(self.identifier, root)
            instruction_type = NCSInstructionType.CPTOPBP if isglobal else NCSInstructionType.CPTOPSP
            ncs.add(instruction_type, args=[stack_index, datatype.size(root)])
            return datatype


class FieldAccessExpression(Expression):
    def __init__(self, field_access: FieldAccess):
        super().__init__()
        self.field_access: FieldAccess = field_access

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        scoped = self.field_access.get_scoped(block, root)
        instruction_type = NCSInstructionType.CPTOPBP if scoped.isglobal else NCSInstructionType.CPTOPSP
        ncs.instructions.append(NCSInstruction(instruction_type, [scoped.offset, scoped.datatype.size(root)]))
        return scoped.datatype


class StringExpression(Expression):
    def __init__(self, value: str):
        super().__init__()
        self.value: str = value

    def __eq__(self, other):
        if isinstance(other, StringExpression):
            return self.value == other.value
        else:
            return NotImplemented

    def data_type(self) -> DynamicDataType:
        return DynamicDataType.STRING

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        ncs.instructions.append(NCSInstruction(NCSInstructionType.CONSTS, [self.value]))
        return DynamicDataType.STRING


class IntExpression(Expression):
    def __init__(self, value: int):
        super().__init__()
        self.value: int = value

    def __eq__(self, other):
        if isinstance(other, IntExpression):
            return self.value == other.value
        else:
            return NotImplemented

    def data_type(self) -> DynamicDataType:
        return DynamicDataType.INT

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        ncs.instructions.append(NCSInstruction(NCSInstructionType.CONSTI, [self.value]))
        return DynamicDataType.INT


class ObjectExpression(Expression):
    def __init__(self, value: int):
        super().__init__()
        self.value: int = value

    def __eq__(self, other):
        if isinstance(other, ObjectExpression):
            return self.value == other.value
        else:
            return NotImplemented

    def data_type(self) -> DynamicDataType:
        return DynamicDataType.OBJECT

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        ncs.instructions.append(NCSInstruction(NCSInstructionType.CONSTO, [self.value]))
        return DynamicDataType.OBJECT


class FloatExpression(Expression):
    def __init__(self, value: float):
        super().__init__()
        self.value: float = value

    def __eq__(self, other):
        if isinstance(other, FloatExpression):
            return self.value == other.value
        else:
            return NotImplemented

    def data_type(self) -> DynamicDataType:
        return DynamicDataType.FLOAT

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        ncs.instructions.append(NCSInstruction(NCSInstructionType.CONSTF, [self.value]))
        return DynamicDataType.FLOAT


class EngineCallExpression(Expression):
    def __init__(self, function: ScriptFunction, routine_id: int, data_type: DynamicDataType, args: List[Expression]):
        super().__init__()
        self._function: ScriptFunction = function
        self._routine_id: int = routine_id
        self._args: List[Expression] = args

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        arg_count = len(self._args)

        if arg_count > len(self._function.params):
            raise CompileException(f"Too many arguments passed to '{self._function.name}'.")

        for i, param in enumerate(self._function.params):
            if i >= arg_count:
                if param.default is None:
                    raise CompileException(f"Not enough arguments passed to '{self._function.name}'.")
                else:
                    constant = next((constant for constant in root.constants if constant.name == param.default), None)
                    if constant is not None:
                        if constant.datatype == DataType.INT:
                            self._args.append(IntExpression(int(constant.value)))
                        elif constant.datatype == DataType.FLOAT:
                            self._args.append(FloatExpression(float(constant.value)))
                        elif constant.datatype == DataType.STRING:
                            self._args.append(StringExpression(str(constant.value)))
                        elif constant.datatype == DataType.OBJECT:
                            self._args.append(ObjectExpression(int(constant.value)))
                    else:
                        if param.datatype == DynamicDataType.INT:
                            self._args.append(IntExpression(int(param.default)))
                        elif param.datatype == DynamicDataType.FLOAT:
                            self._args.append(FloatExpression(float(param.default.replace("f", ""))))
                        elif param.datatype == DynamicDataType.STRING:
                            self._args.append(StringExpression(param.default))
                        else:
                            raise CompileException(f"Unexpected compilation error at '{self._function.name}' call.")

        this_stack = 0
        for i, arg in enumerate(reversed(self._args)):
            param_type = DynamicDataType(self._function.params[-i - 1].datatype)
            if param_type == DataType.ACTION:
                after_command = NCSInstruction()
                ncs.add(NCSInstructionType.STORE_STATE, args=[root.scope_size(), block.full_scope_size(root)])
                ncs.add(NCSInstructionType.JMP, jump=after_command)
                arg.compile(ncs, root, block)
                ncs.instructions.append(after_command)
            else:
                added = arg.compile(ncs, root, block)
                block.tempstack += added.size(root)
                this_stack += added.size(root)

                if added != param_type:
                    raise CompileException(f"Tried to pass an argument of the incorrect type to '{self._function.name}'.")

        ncs.instructions.append(NCSInstruction(NCSInstructionType.ACTION, [self._routine_id, len(self._args)]))
        block.tempstack -= this_stack
        return DynamicDataType(self._function.returntype)


class FunctionCallExpression(Expression):
    def __init__(self, function: Identifier, args: List[Expression]):
        super().__init__()
        self._function: Identifier = function
        self._args: List[Expression] = args

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        return root.compile_jsr(ncs, block, self._function.label, *self._args)
# endregion


class BinaryOperatorExpression(Expression):
    def __init__(self, expression1: Expression, expression2: Expression, mapping: List[BinaryOperatorMapping]):
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2
        self.compatibility: List[BinaryOperatorMapping] = mapping

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        type1 = self.expression1.compile(ncs, root, block)
        block.tempstack += 4
        type2 = self.expression2.compile(ncs, root, block)
        block.tempstack += 4

        for x in self.compatibility:
            if type1 == x.lhs and type2 == x.rhs:
                ncs.add(x.instruction)
                break
        else:
            raise CompileException(f"Cannot test if {type1.name.lower()} is greater than {type2.name.lower()}")

        block.tempstack -= 8
        return DynamicDataType(x.lhs)


class UnaryOperatorExpression(Expression):
    def __init__(self, expression1: Expression, mapping: List[UnaryOperatorMapping]):
        super().__init__()
        self.expression1: Expression = expression1
        self.compatibility: List[UnaryOperatorMapping] = mapping

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        type1 = self.expression1.compile(ncs, root, block)
        block.tempstack += 4

        for x in self.compatibility:
            if type1 == x.rhs:
                ncs.add(x.instruction)
                break
        else:
            raise CompileException(f"Cannot negate {type1.name.lower()}")

        block.tempstack -= 4
        return type1


class LogicalNotExpression(Expression):
    def __init__(self, expression1: Expression):
        super().__init__()
        self.expression1: Expression = expression1

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        type1 = self.expression1.compile(ncs, root, block)
        block.tempstack += 4

        if type1 == DynamicDataType.INT:
            ncs.add(NCSInstructionType.NOTI)
        else:
            raise CompileException(f"Cannot get the logical NOT of {type1.name.lower()}")

        block.tempstack -= 4
        return DynamicDataType.INT


class BitwiseNotExpression(Expression):
    def __init__(self, expression1: Expression):
        super().__init__()
        self.expression1: Expression = expression1

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        type1 = self.expression1.compile(ncs, root, block)
        block.tempstack += 4

        if type1 == DynamicDataType.INT:
            ncs.add(NCSInstructionType.COMPI)
        else:
            raise CompileException(f"Cannot get one's complement of {type1.name.lower()}")

        block.tempstack -= 4
        return type1


# region Expressions: Assignment
class Assignment(Expression):
    def __init__(self, field_access: FieldAccess, value: Expression):
        super().__init__()
        self.field_access: FieldAccess = field_access
        self.expression: Expression = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        variable_type = self.expression.compile(ncs, root, block)

        isglobal, expression_type, stack_index = self.field_access.get_scoped(block, root)
        instruction_type = NCSInstructionType.CPDOWNBP if isglobal else NCSInstructionType.CPDOWNSP
        stack_index -= 0 if isglobal else variable_type.size(root)

        if variable_type != expression_type:
            raise CompileException(f"Wrong type was assigned to symbol {self.field_access.identifiers[-1]}.")

        # Copy the value that the expression has already been placed on the stack to where the identifiers position is
        ncs.instructions.append(NCSInstruction(instruction_type, [stack_index, expression_type.size(root)]))
        # Remove the temporary value from the stack that the expression created
        ncs.instructions.append(NCSInstruction(NCSInstructionType.MOVSP, [-expression_type.size(root)]))

        return variable_type


class AdditionAssignment(Expression):
    def __init__(self, field_access: FieldAccess, value: Expression):
        super().__init__()
        self.field_access: FieldAccess = field_access
        self.expression: Expression = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        # Copy the variable to the top of the stack
        isglobal, variable_type, stack_index = self.field_access.get_scoped(block, root)
        instruction_type = NCSInstructionType.CPTOPBP if isglobal else NCSInstructionType.CPTOPSP
        ncs.add(instruction_type, args=[stack_index, variable_type.size(root)])
        block.tempstack += variable_type.size(root)

        # Add the result of the expression to the stack
        expresion_type = self.expression.compile(ncs, root, block)
        block.tempstack += expresion_type.size(root)

        # Determine what instruction to apply to the two values
        if variable_type == DynamicDataType.INT and expresion_type == DynamicDataType.INT:
            arthimetic_instruction = NCSInstructionType.ADDII
        elif variable_type == DynamicDataType.INT and expresion_type == DynamicDataType.FLOAT:
            arthimetic_instruction = NCSInstructionType.ADDIF
        elif variable_type == DynamicDataType.FLOAT and expresion_type == DynamicDataType.FLOAT:
            arthimetic_instruction = NCSInstructionType.ADDFF
        elif variable_type == DynamicDataType.FLOAT and expresion_type == DynamicDataType.INT:
            arthimetic_instruction = NCSInstructionType.ADDFI
        elif variable_type == DynamicDataType.STRING and expresion_type == DynamicDataType.STRING:
            arthimetic_instruction = NCSInstructionType.ADDSS
        else:
            raise CompileException(f"Wrong type was assigned to symbol {self.field_access.identifiers[-1]}.")

        # Add the expression and our temp variable copy together
        ncs.add(arthimetic_instruction, args=[])

        # Copy the result to the original variable in the stack
        ins_cpdown = NCSInstructionType.CPDOWNBP if isglobal else NCSInstructionType.CPDOWNSP
        offset_cpdown = stack_index if isglobal else stack_index - expresion_type.size(root)
        ncs.add(ins_cpdown, args=[offset_cpdown, variable_type.size(root)])

        # Pop the temp variable
        ncs.add(NCSInstructionType.MOVSP, args=[-variable_type.size(root)])

        block.tempstack -= variable_type.size(root)
        block.tempstack -= expresion_type.size(root)
        return expresion_type


class SubtractionAssignment(Expression):
    def __init__(self, field_access: FieldAccess, value: Expression):
        super().__init__()
        self.field_access: FieldAccess = field_access
        self.expression: Expression = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        # Copy the variable to the top of the stack
        isglobal, variable_type, stack_index = self.field_access.get_scoped(block, root)
        instruction_type = NCSInstructionType.CPTOPBP if isglobal else NCSInstructionType.CPTOPSP
        ncs.add(instruction_type, args=[stack_index, variable_type.size(root)])
        block.tempstack += variable_type.size(root)

        # Add the result of the expression to the stack
        expresion_type = self.expression.compile(ncs, root, block)
        block.tempstack += expresion_type.size(root)

        # Determine what instruction to apply to the two values
        if variable_type == DynamicDataType.INT and expresion_type == DynamicDataType.INT:
            arthimetic_instruction = NCSInstructionType.SUBII
        elif variable_type == DynamicDataType.INT and expresion_type == DynamicDataType.FLOAT:
            arthimetic_instruction = NCSInstructionType.SUBIF
        elif variable_type == DynamicDataType.FLOAT and expresion_type == DynamicDataType.FLOAT:
            arthimetic_instruction = NCSInstructionType.SUBFF
        elif variable_type == DynamicDataType.FLOAT and expresion_type == DynamicDataType.INT:
            arthimetic_instruction = NCSInstructionType.SUBFI
        else:
            raise CompileException(f"Wrong type was assigned to symbol {self.field_access.identifiers[-1]}.")

        # Add the expression and our temp variable copy together
        ncs.add(arthimetic_instruction)

        # Copy the result to the original variable in the stack
        ins_cpdown = NCSInstructionType.CPDOWNBP if isglobal else NCSInstructionType.CPDOWNSP
        offset_cpdown = stack_index if isglobal else stack_index - expresion_type.size(root)
        ncs.add(ins_cpdown, args=[offset_cpdown, variable_type.size(root)])

        # Pop the temp variable
        ncs.add(NCSInstructionType.MOVSP, args=[-variable_type.size(root)])

        block.tempstack -= expresion_type.size(root)
        block.tempstack -= variable_type.size(root)
        return expresion_type


class MultiplicationAssignment(Expression):
    def __init__(self, field_access: FieldAccess, value: Expression):
        super().__init__()
        self.field_access: FieldAccess = field_access
        self.expression: Expression = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        # Copy the variable to the top of the stack
        isglobal, variable_type, stack_index = self.field_access.get_scoped(block, root)
        instruction_type = NCSInstructionType.CPTOPBP if isglobal else NCSInstructionType.CPTOPSP
        ncs.add(instruction_type, args=[stack_index, variable_type.size(root)])
        block.tempstack += variable_type.size(root)

        # Add the result of the expression to the stack
        expresion_type = self.expression.compile(ncs, root, block)
        block.tempstack += expresion_type.size(root)

        # Determine what instruction to apply to the two values
        if variable_type == DynamicDataType.INT and expresion_type == DynamicDataType.INT:
            arthimetic_instruction = NCSInstructionType.MULII
        elif variable_type == DynamicDataType.INT and expresion_type == DynamicDataType.FLOAT:
            arthimetic_instruction = NCSInstructionType.MULIF
        elif variable_type == DynamicDataType.FLOAT and expresion_type == DynamicDataType.FLOAT:
            arthimetic_instruction = NCSInstructionType.MULFF
        elif variable_type == DynamicDataType.FLOAT and expresion_type == DynamicDataType.INT:
            arthimetic_instruction = NCSInstructionType.MULFI
        else:
            raise CompileException(f"Wrong type was assigned to symbol {self.field_access.identifiers[-1]}.")

        # Add the expression and our temp variable copy together
        ncs.add(arthimetic_instruction)

        # Copy the result to the original variable in the stack
        ins_cpdown = NCSInstructionType.CPDOWNBP if isglobal else NCSInstructionType.CPDOWNSP
        offset_cpdown = stack_index if isglobal else stack_index - expresion_type.size(root)
        ncs.add(ins_cpdown, args=[offset_cpdown, variable_type.size(root)])

        # Pop the temp variable
        ncs.add(NCSInstructionType.MOVSP, args=[-variable_type.size(root)])

        block.tempstack -= expresion_type.size(root)
        block.tempstack -= variable_type.size(root)
        return expresion_type


class DivisionAssignment(Expression):
    def __init__(self, field_access: FieldAccess, value: Expression):
        super().__init__()
        self.field_access: FieldAccess = field_access
        self.expression: Expression = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        # Copy the variable to the top of the stack
        isglobal, variable_type, stack_index = self.field_access.get_scoped(block, root)
        instruction_type = NCSInstructionType.CPTOPBP if isglobal else NCSInstructionType.CPTOPSP
        ncs.add(instruction_type, args=[stack_index, variable_type.size(root)])
        block.tempstack += variable_type.size(root)

        # Add the result of the expression to the stack
        expresion_type = self.expression.compile(ncs, root, block)
        block.tempstack += expresion_type.size(root)

        # Determine what instruction to apply to the two values
        if variable_type == DynamicDataType.INT and expresion_type == DynamicDataType.INT:
            arthimetic_instruction = NCSInstructionType.DIVII
        elif variable_type == DynamicDataType.INT and expresion_type == DynamicDataType.FLOAT:
            arthimetic_instruction = NCSInstructionType.DIVIF
        elif variable_type == DynamicDataType.FLOAT and expresion_type == DynamicDataType.FLOAT:
            arthimetic_instruction = NCSInstructionType.DIVFF
        elif variable_type == DynamicDataType.FLOAT and expresion_type == DynamicDataType.INT:
            arthimetic_instruction = NCSInstructionType.DIVFI
        else:
            raise CompileException(f"Wrong type was assigned to symbol {self.field_access.identifiers[-1]}.")

        # Add the expression and our temp variable copy together
        ncs.add(arthimetic_instruction)

        # Copy the result to the original variable in the stack
        ins_cpdown = NCSInstructionType.CPDOWNBP if isglobal else NCSInstructionType.CPDOWNSP
        offset_cpdown = stack_index if isglobal else stack_index - expresion_type.size(root)
        ncs.add(ins_cpdown, args=[offset_cpdown, variable_type.size(root)])

        # Pop the temp variable
        ncs.add(NCSInstructionType.MOVSP, args=[-variable_type.size(root)])

        block.tempstack -= expresion_type.size(root)
        block.tempstack -= variable_type.size(root)
        return expresion_type
# endregion


# region Statements
class EmptyStatement(Statement):
    def __init__(self):
        super().__init__()

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock, return_instruction: NCSInstruction,
                break_instruction: Optional[NCSInstruction], continue_instruction: Optional[NCSInstruction]):
        return DynamicDataType.VOID


class ExpressionStatement(Statement):
    def __init__(self, expression: Expression):
        super().__init__()
        self.expression: Expression = expression

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock, return_instruction: NCSInstruction,
                break_instruction: Optional[NCSInstruction], continue_instruction: Optional[NCSInstruction]):
        self.expression.compile(ncs, root, block)


class InitializationStatement(Statement):
    def __init__(self, identifier: Identifier, data_type: DynamicDataType, value: Expression):
        super().__init__()
        self.identifier: Identifier = identifier
        self.data_type: DynamicDataType = data_type
        self.expression: Expression = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock, return_instruction: NCSInstruction,
                break_instruction: Optional[NCSInstruction], continue_instruction: Optional[NCSInstruction]):
        expression_type = self.expression.compile(ncs, root, block)
        if expression_type != self.data_type:
            raise CompileException(f"Tried to declare '{self.identifier}' a new variable with incorrect type '{expression_type}'.")
        block.add_scoped(self.identifier, self.data_type)


class DeclarationStatement(Statement):
    def __init__(self, identifier: Identifier, data_type: DynamicDataType):
        super().__init__()
        self.identifier: Identifier = identifier
        self.data_type: DynamicDataType = data_type

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock, return_instruction: NCSInstruction,
                break_instruction: Optional[NCSInstruction], continue_instruction: Optional[NCSInstruction]):

        if self.data_type.builtin == DataType.INT:
            ncs.add(NCSInstructionType.RSADDI)
        elif self.data_type.builtin == DataType.FLOAT:
            ncs.add(NCSInstructionType.RSADDF)
        elif self.data_type.builtin == DataType.STRING:
            ncs.add(NCSInstructionType.RSADDS)
        elif self.data_type.builtin == DataType.OBJECT:
            ncs.add(NCSInstructionType.RSADDO)
        elif self.data_type.builtin == DataType.EVENT:
            ncs.add(NCSInstructionType.RSADDEVT)
        elif self.data_type.builtin == DataType.LOCATION:
            ncs.add(NCSInstructionType.RSADDLOC)
        elif self.data_type.builtin == DataType.TALENT:
            ncs.add(NCSInstructionType.RSADDTAL)
        elif self.data_type.builtin == DataType.EFFECT:
            ncs.add(NCSInstructionType.RSADDEFF)
        elif self.data_type.builtin == DataType.STRUCT:
            root.struct_map[self.data_type._struct].initialize(ncs, root)
        elif self.data_type.builtin == DataType.VOID:
            raise CompileException("Cannot declare a variable of void type.")
        else:
            raise CompileException("Tried to compile a variable of unknown type.")

        block.add_scoped(self.identifier, self.data_type)


class ConditionalBlock(Statement):
    def __init__(self, if_block: ConditionAndBlock, else_if_blocks: List[ConditionAndBlock], else_block: CodeBlock):
        super().__init__()
        self.if_blocks: List[ConditionAndBlock] = [if_block] + else_if_blocks
        self.else_block: Optional[CodeBlock] = else_block

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock, return_instruction: NCSInstruction,
                break_instruction: Optional[NCSInstruction], continue_instruction: Optional[NCSInstruction]):
        jump_count = 1 + len(self.if_blocks)
        jump_tos = [NCSInstruction(NCSInstructionType.NOP, args=[]) for i in range(jump_count)]

        for i, else_if in enumerate(self.if_blocks):
            else_if.condition.compile(ncs, root, block)
            ncs.add(NCSInstructionType.JZ, jump=jump_tos[i])

            else_if.block.compile(ncs, root, block, return_instruction, break_instruction, continue_instruction)
            ncs.add(NCSInstructionType.JMP, jump=jump_tos[-1])

            ncs.instructions.append(jump_tos[i])

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
        return DynamicDataType.VOID


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

        if condition_type != DynamicDataType.INT:
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
        if condition_type != DynamicDataType.INT:
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
        if condition_type != DynamicDataType.INT:
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
        ncs.add(NCSInstructionType.MOVSP, args=[-block.break_scope_size(root)])
        ncs.add(NCSInstructionType.JMP, jump=break_instruction)
        ncs.add(NCSInstructionType.NOP, args=["YEA REMEMBER TO DELETE THIS MY DUDE"])


class ContinueStatement(Statement):
    def __init__(self):
        super().__init__()

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock, return_instruction: NCSInstruction,
                break_instruction: Optional[NCSInstruction], continue_instruction: Optional[NCSInstruction]):
        if continue_instruction is None:
            raise CompileException("Nothing to continue out of.")
        ncs.add(NCSInstructionType.MOVSP, args=[-block.break_scope_size(root)])
        ncs.add(NCSInstructionType.JMP, jump=continue_instruction)


class PrefixIncrementExpression(Expression):
    def __init__(self, field_access: FieldAccess):
        self.field_access: FieldAccess = field_access

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        variable_type = self.field_access.compile(ncs, root, block)

        if variable_type != DynamicDataType.INT:
            raise CompileException("Operator (++) not valid for specified types")

        isglobal, variable_type, stack_index = self.field_access.get_scoped(block, root)
        ncs.add(NCSInstructionType.INCISP, args=[-4])

        if isglobal:
            ncs.add(NCSInstructionType.CPDOWNBP, args=[stack_index, variable_type.size(root)])
        else:
            ncs.add(NCSInstructionType.CPDOWNSP, args=[stack_index - variable_type.size(root), variable_type.size(root)])

        return variable_type


class PostfixIncrementExpression(Expression):
    def __init__(self, field_access: FieldAccess):
        self.field_access: FieldAccess = field_access

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        variable_type = self.field_access.compile(ncs, root, block)
        block.tempstack += 4

        if variable_type != DynamicDataType.INT:
            raise CompileException("Operator (++) not valid for specified types")

        isglobal, variable_type, stack_index = self.field_access.get_scoped(block, root)
        if isglobal:
            ncs.add(NCSInstructionType.INCIBP, args=[stack_index])
        else:
            ncs.add(NCSInstructionType.INCISP, args=[stack_index])

        block.tempstack -= 4
        return variable_type


class PrefixDecrementExpression(Expression):
    def __init__(self, field_access: FieldAccess):
        self.field_access: FieldAccess = field_access

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        variable_type = self.field_access.compile(ncs, root, block)

        if variable_type != DynamicDataType.INT:
            raise CompileException("Operator (++) not valid for specified types")

        isglobal, variable_type, stack_index = self.field_access.get_scoped(block, root)
        ncs.add(NCSInstructionType.DECISP, args=[-4])

        if isglobal:
            ncs.add(NCSInstructionType.CPDOWNBP, args=[stack_index, variable_type.size(root)])
        else:
            ncs.add(NCSInstructionType.CPDOWNSP,
                    args=[stack_index - variable_type.size(root), variable_type.size(root)])

        return variable_type


class PostfixDecrementExpression(Expression):
    def __init__(self, field_access: FieldAccess):
        self.field_access: FieldAccess = field_access

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        variable_type = self.field_access.compile(ncs, root, block)
        block.tempstack += 4

        if variable_type != DynamicDataType.INT:
            raise CompileException("Operator (++) not valid for specified types")

        isglobal, variable_type, stack_index = self.field_access.get_scoped(block, root)
        if isglobal:
            ncs.add(NCSInstructionType.DECIBP, args=[stack_index])
        else:
            ncs.add(NCSInstructionType.DECISP, args=[stack_index])

        block.tempstack -= 4
        return variable_type


# region Switch
class SwitchStatement(Statement):
    def __init__(self, expression: Expression, blocks: List[SwitchBlock]):
        super().__init__()
        self.expression: Expression = expression
        self.blocks: List[SwitchBlock] = blocks

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock, return_instruction: NCSInstruction,
                break_instruction: Optional[NCSInstruction], continue_instruction: Optional[NCSInstruction]):
        expression_type = self.expression.compile(ncs, root, block)
        block.tempstack += expression_type.size(root)

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
                ncs.add(NCSInstructionType.CPTOPSP, args=[-expression_type.size(root), expression_type.size(root)])
                label.compile(ncs, root, block, switchblock_to_instruction[switchblock], expression_type)
        # If none of the labels match, jump over the code block
        ncs.add(NCSInstructionType.JMP, jump=end_of_switch)

        ncs.merge(tempncs)
        ncs.instructions.append(end_of_switch)

        # Pop the Switch expression
        ncs.add(NCSInstructionType.MOVSP, args=[-4])
        block.tempstack -= expression_type.size(root)


class SwitchBlock:
    def __init__(self, labels: List[SwitchLabel], block: List[Statement]):
        self.labels: List[SwitchLabel] = labels
        self.block: List[Statement] = block


class SwitchLabel(ABC):
    @abstractmethod
    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock, jump_to: NCSInstruction, expression_type: DynamicDataType):
        ...


class ExpressionSwitchLabel:
    def __init__(self, expression: Expression):
        self.expression: Expression = expression

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock, jump_to: NCSInstruction, expression_type: DynamicDataType):
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

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock, jump_to: NCSInstruction, expression_type: DynamicDataType):
        ncs.add(NCSInstructionType.JMP, jump=jump_to)
# endregion


class DynamicDataType:
    INT: DynamicDataType
    STRING: DynamicDataType
    FLOAT: DynamicDataType
    OBJECT: DynamicDataType
    VECTOR: DynamicDataType
    VOID: DynamicDataType

    def __init__(self, datatype: DataType, struct_name: str = None):
        self.builtin: DataType = datatype
        self._struct: str = struct_name

    def __eq__(self, other):
        if isinstance(other, DynamicDataType):
            if self.builtin == other.builtin:
                return self.builtin != DataType.STRUCT or (self.builtin == DataType.STRUCT and self._struct == other._struct)
            else:
                return False
        elif isinstance(other, DataType):
            return self.builtin == other and self.builtin != DataType.STRUCT
        else:
            return NotImplemented

    def size(self, root: CodeRoot) -> int:
        if self.builtin == DataType.STRUCT:
            return root.struct_map[self._struct].size(root)
        else:
            return self.builtin.size()


DynamicDataType.INT = DynamicDataType(DataType.INT)
DynamicDataType.STRING = DynamicDataType(DataType.STRING)
DynamicDataType.FLOAT = DynamicDataType(DataType.FLOAT)
DynamicDataType.OBJECT = DynamicDataType(DataType.OBJECT)
DynamicDataType.VECTOR = DynamicDataType(DataType.VECTOR)
DynamicDataType.VOID = DynamicDataType(DataType.VOID)
