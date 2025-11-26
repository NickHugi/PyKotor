from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple, cast

from pykotor.common.script import DataType
from pykotor.resource.formats.ncs import NCS, NCSInstruction, NCSInstructionType
from pykotor.tools.path import CaseAwarePath

if TYPE_CHECKING:
    from pykotor.common.script import ScriptConstant, ScriptFunction


def get_logical_equality_instruction(
    type1: DynamicDataType,
    type2: DynamicDataType,
) -> NCSInstructionType:
    if type1 == DataType.INT and type2 == DataType.INT:
        return NCSInstructionType.EQUALII
    if type1 == DataType.FLOAT and type2 == DataType.FLOAT:
        return NCSInstructionType.EQUALFF
    msg = f"Tried an unsupported comparison between '{type1}' '{type2}'."
    raise CompileError(msg)


class CompileError(Exception):
    """Base exception for NSS compilation errors.

    Provides detailed error messages to help debug script issues.

    References:
    ----------
        vendor/HoloLSP/server/src/nwscript-parser.ts (NSS parser error handling)
        vendor/xoreos-tools/src/nwscript/compiler.cpp (NSS compiler error handling)
        vendor/KotOR.js/src/nwscript/NWScriptCompiler.ts (TypeScript compiler errors)
    """

    def __init__(
        self, message: str, line_num: int | None = None, context: str | None = None
    ):
        full_message = message
        if line_num is not None:
            full_message = f"Line {line_num}: {message}"
        if context:
            full_message = f"{full_message}\n  Context: {context}"
        super().__init__(full_message)
        self.line_num = line_num
        self.context = context


class EntryPointError(CompileError):
    """Raised when script has no valid entry point (main or StartingConditional)."""


class MissingIncludeError(CompileError):
    """Raised when a #include file cannot be found."""


class TopLevelObject(ABC):
    @abstractmethod
    def compile(self, ncs: NCS, root: CodeRoot):  # noqa: A003
        ...


class GlobalVariableInitialization(TopLevelObject):
    def __init__(
        self,
        identifier: Identifier,
        data_type: DynamicDataType,
        value: Expression,
    ):
        super().__init__()
        self.identifier: Identifier = identifier
        self.data_type: DynamicDataType = data_type
        self.expression: Expression = value

    def compile(self, ncs: NCS, root: CodeRoot):
        # Allocate storage for the global variable (this also registers it in the global scope)
        declaration = GlobalVariableDeclaration(self.identifier, self.data_type)
        declaration.compile(ncs, root)

        block = CodeBlock()
        expression_type = self.expression.compile(ncs, root, block)
        if expression_type != self.data_type:
            msg = (
                f"Type mismatch in initialization of global variable '{self.identifier}'\n"
                f"  Declared type: {self.data_type.builtin.name}\n"
                f"  Initializer type: {expression_type.builtin.name}"
            )
            raise CompileError(msg)

        scoped = root.get_scoped(self.identifier, root)
        # Global storage resides on the stack before base pointer is saved, so use stack-pointer-relative copy.
        stack_index = scoped.offset - scoped.datatype.size(root)
        ncs.instructions.append(
            NCSInstruction(
                NCSInstructionType.CPDOWNSP, [stack_index, scoped.datatype.size(root)]
            ),
        )
        # Remove the initializer value from the stack
        ncs.add(NCSInstructionType.MOVSP, args=[-scoped.datatype.size(root)])


class GlobalVariableDeclaration(TopLevelObject):
    def __init__(self, identifier: Identifier, data_type: DynamicDataType):
        super().__init__()
        self.identifier: Identifier = identifier
        self.data_type: DynamicDataType = data_type

    def compile(self, ncs: NCS, root: CodeRoot):  # noqa: A003
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
        elif self.data_type.builtin == DataType.VECTOR:
            ncs.add(NCSInstructionType.RSADDF)
            ncs.add(NCSInstructionType.RSADDF)
            ncs.add(NCSInstructionType.RSADDF)
        elif self.data_type.builtin == DataType.STRUCT:
            struct_name = self.data_type._struct  # noqa: SLF001
            if struct_name is not None and struct_name in root.struct_map:
                root.struct_map[struct_name].initialize(ncs, root)
            else:
                msg = f"Unknown struct type for variable '{self.identifier}'"
                raise CompileError(msg)
        elif self.data_type.builtin == DataType.VOID:
            msg = (
                f"Cannot declare variable '{self.identifier}' with void type\n"
                f"  void can only be used as a function return type"
            )
            raise CompileError(msg)
        else:
            msg = (
                f"Unsupported type '{self.data_type.builtin.name}' for global variable '{self.identifier}'\n"
                f"  This may indicate a compiler bug or unsupported type"
            )
            raise CompileError(msg)

        root.add_scoped(self.identifier, self.data_type)


class Identifier:
    def __init__(self, label: str):
        self.label: str = label

    def __eq__(self, other: object) -> bool:
        # sourcery skip: assign-if-exp, reintroduce-else
        if self is other:
            return True
        if isinstance(other, Identifier):
            return self.label == other.label
        if isinstance(other, str):
            return self.label == other
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
    unary: list[UnaryOperatorMapping]
    binary: list[BinaryOperatorMapping]


class BinaryOperatorMapping:
    def __init__(
        self,
        instruction: NCSInstructionType,
        result: DataType,
        lhs: DataType,
        rhs: DataType,
    ):
        self.instruction: NCSInstructionType = instruction
        self.result: DataType = result
        self.lhs: DataType = lhs
        self.rhs: DataType = rhs

    def __repr__(self):
        return f"{self.__class__.__name__}(instruction={self.instruction!r}, result={self.result!r}, lhs={self.lhs!r}, rhs={self.rhs!r})"


class UnaryOperatorMapping:
    def __init__(self, instruction: NCSInstructionType, rhs: DataType):
        self.instruction: NCSInstructionType = instruction
        self.rhs: DataType = rhs


class FunctionReference(NamedTuple):
    instruction: NCSInstruction
    definition: FunctionForwardDeclaration | FunctionDefinition

    def is_prototype(self) -> bool:
        return isinstance(self.definition, FunctionForwardDeclaration)


class GetScopedResult(NamedTuple):
    is_global: bool
    datatype: DynamicDataType
    offset: int


class Struct:
    def __init__(self, identifier: Identifier, members: list[StructMember]):
        self.identifier: Identifier = identifier
        self.members: list[StructMember] = members
        self._cached_size: int | None = None  # Cache size for performance

    def initialize(self, ncs: NCS, root: CodeRoot):
        for member in self.members:
            member.initialize(ncs, root)

    def size(self, root: CodeRoot) -> int:
        """Calculate struct size with caching for performance."""
        if self._cached_size is None:
            self._cached_size = sum(member.size(root) for member in self.members)
        return self._cached_size

    def child_offset(self, root: CodeRoot, identifier: Identifier) -> int:
        size = 0
        for member in self.members:
            if member.identifier == identifier:
                break
            size += member.size(root)
        else:
            # Provide helpful error with available members
            available = [m.identifier.label for m in self.members]
            msg = (
                f"Unknown member '{identifier}' in struct '{self.identifier}'\n"
                f"  Available members: {', '.join(available)}"
            )
            raise CompileError(msg)
        return size

    def child_type(self, root: CodeRoot, identifier: Identifier) -> DynamicDataType:
        for member in self.members:
            if member.identifier == identifier:
                return member.datatype
        available = [m.identifier.label for m in self.members]
        msg = (
            f"Member '{identifier}' not found in struct '{self.identifier}'\n"
            f"  Available members: {', '.join(available)}"
        )
        raise CompileError(msg)


class StructMember:
    def __init__(self, datatype: DynamicDataType, identifier: Identifier):
        self.datatype: DynamicDataType = datatype
        self.identifier: Identifier = identifier

    def initialize(self, ncs: NCS, root: CodeRoot):
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
            msg = (
                f"Unsupported struct member type: {self.datatype.builtin.name}\n"
                f"  Member: {self.identifier}\n"
                f"  Supported types: int, float, string, object, event, effect, location, talent, struct"
            )
            raise CompileError(msg)

    def size(self, root: CodeRoot) -> int:
        return self.datatype.size(root)


class CodeRoot:
    """Root compilation context for NSS compilation.

    Manages global scope, function definitions, constants, and compilation state.
    Provides symbol resolution and type checking during NSS to NCS compilation.

    References:
    ----------
        vendor/KotOR.js/src/nwscript/NWScriptCompiler.ts (TypeScript compiler architecture)
        vendor/xoreos-tools/src/nwscript/decompiler.cpp (NCS decompiler, reverse reference for compilation)
        vendor/HoloLSP/server/src/nwscript-parser.ts (NSS parser and AST generation)
        vendor/HoloLSP/server/src/nwscript-lexer.ts (NSS lexer/tokenizer)
        vendor/DeNCS/ (NCS decompiler, reverse reference for compilation)
    """

    def __init__(
        self,
        constants: list[ScriptConstant],
        functions: list[ScriptFunction],
        library_lookup: list[str] | list[Path] | list[Path | str] | str | Path | None,
        library: dict[str, bytes],
    ):
        self.objects: list[TopLevelObject] = []

        self.library: dict[str, bytes] = library
        self.functions: list[ScriptFunction] = functions
        self.constants: list[ScriptConstant] = constants
        self.library_lookup: list[Path] = []
        if library_lookup:
            if not isinstance(library_lookup, list):
                library_lookup = [library_lookup]
            normalized: list[Path] = []
            for item in library_lookup:
                path_obj = CaseAwarePath(item)
                normalized.append(path_obj)
            self.library_lookup = normalized

        self.function_map: dict[str, FunctionReference] = {}
        self._global_scope: list[ScopedValue] = []
        self.struct_map: dict[str, Struct] = {}

    def compile(self, ncs: NCS):  # noqa: A003
        # nwnnsscomp processes the includes and global variable declarations before functions regardless if they are
        # placed before or after function definitions. We will replicate this behavior.

        included: list[IncludeScript] = []
        while [obj for obj in self.objects if isinstance(obj, IncludeScript)]:
            includes: list[IncludeScript] = [
                obj for obj in self.objects if isinstance(obj, IncludeScript)
            ]
            include: IncludeScript = includes.pop()
            self.objects.remove(include)
            included.append(include)
            include.compile(ncs, self)

        script_globals: list[
            GlobalVariableDeclaration | GlobalVariableInitialization | StructDefinition
        ] = [
            obj
            for obj in self.objects
            if isinstance(
                obj,
                (
                    GlobalVariableDeclaration,
                    GlobalVariableInitialization,
                    StructDefinition,
                ),
            )
        ]
        others: list[TopLevelObject] = [
            obj
            for obj in self.objects
            if obj not in included and obj not in script_globals
        ]

        if script_globals:
            for global_def in script_globals:
                global_def.compile(ncs, self)
            ncs.add(NCSInstructionType.SAVEBP, args=[])
        entry_index: int = len(ncs.instructions)

        for obj in others:
            obj.compile(ncs, self)

        if "main" in self.function_map:
            ncs.add(NCSInstructionType.RETN, args=[], index=entry_index)
            ncs.add(
                NCSInstructionType.JSR,
                jump=self.function_map["main"][0],
                index=entry_index,
            )
        elif "StartingConditional" in self.function_map:
            ncs.add(NCSInstructionType.RETN, args=[], index=entry_index)
            ncs.add(
                NCSInstructionType.JSR,
                jump=self.function_map["StartingConditional"][0],
                index=entry_index,
            )
            ncs.add(NCSInstructionType.RSADDI, args=[], index=entry_index)
        else:
            msg = "This file has no entry point and cannot be compiled (Most likely an include file)."
            raise EntryPointError(msg)

    def compile_jsr(
        self,
        ncs: NCS,
        block: CodeBlock,
        name: str,
        *args: Expression,
    ) -> DynamicDataType:
        args_list = list(args)

        func_map: FunctionReference = self.function_map[name]
        definition: FunctionForwardDeclaration | FunctionDefinition = (
            func_map.definition
        )
        start_instruction: NCSInstruction = func_map.instruction

        if definition.return_type == DynamicDataType.INT:
            ncs.add(NCSInstructionType.RSADDI, args=[])
        elif definition.return_type == DynamicDataType.FLOAT:
            ncs.add(NCSInstructionType.RSADDF, args=[])
        elif definition.return_type == DynamicDataType.STRING:
            ncs.add(NCSInstructionType.RSADDS, args=[])
        elif definition.return_type == DynamicDataType.VECTOR:
            # Vectors are 3 floats (x, y, z components)
            # Reserve stack space for all 3 components
            ncs.add(NCSInstructionType.RSADDF, args=[])
            ncs.add(NCSInstructionType.RSADDF, args=[])
            ncs.add(NCSInstructionType.RSADDF, args=[])
        elif definition.return_type == DynamicDataType.OBJECT:
            ncs.add(NCSInstructionType.RSADDO, args=[])
        elif definition.return_type == DynamicDataType.TALENT:
            ncs.add(NCSInstructionType.RSADDTAL, args=[])
        elif definition.return_type == DynamicDataType.EVENT:
            ncs.add(NCSInstructionType.RSADDEVT, args=[])
        elif definition.return_type == DynamicDataType.LOCATION:
            ncs.add(NCSInstructionType.RSADDLOC, args=[])
        elif definition.return_type == DynamicDataType.EFFECT:
            ncs.add(NCSInstructionType.RSADDEFF, args=[])
        elif definition.return_type == DynamicDataType.VOID:
            ...
        elif definition.return_type.builtin == DataType.STRUCT:
            # For struct return types, initialize the struct on the stack
            struct_name = definition.return_type._struct  # noqa: SLF001
            if struct_name is not None and struct_name in self.struct_map:
                self.struct_map[struct_name].initialize(ncs, self)
            else:
                msg = "Unknown struct type for return value"
                raise CompileError(msg)
        else:
            msg = f"Trying to return unsupported type '{definition.return_type.builtin.name}'"
            raise CompileError(msg)

        required_params = [
            param for param in definition.parameters if param.default is None
        ]

        # Make sure the minimal number of arguments were passed through
        if len(required_params) > len(args_list):
            required_names = [p.identifier.label for p in required_params]
            msg = (
                f"Missing required parameters in call to '{name}'\n"
                f"  Required: {', '.join(required_names)}\n"
                f"  Provided {len(args_list)} of {len(definition.parameters)} parameters"
            )
            raise CompileError(msg)

        # If some optional parameters were not specified, add the defaults to the arguments list
        while len(definition.parameters) > len(args_list):
            param_index = len(args_list)
            default_expr = definition.parameters[param_index].default
            if default_expr is None:
                # Should not happen as required_params already checked, but be safe
                msg = f"Missing default value for parameter {param_index} in '{name}'"
                raise CompileError(msg)
            args_list.append(default_expr)

        offset = 0
        for param, arg in zip(definition.parameters, args_list):
            arg_datatype: DynamicDataType = arg.compile(ncs, self, block)
            offset += arg_datatype.size(self)
            block.temp_stack += arg_datatype.size(self)
            if param.data_type != arg_datatype:
                msg = (
                    f"Parameter type mismatch in call to '{definition.identifier}'\n"
                    f"  Parameter '{param.identifier}' expects: {param.data_type.builtin.name}\n"
                    f"  Got: {arg_datatype.builtin.name}"
                )
                raise CompileError(msg)
        block.temp_stack -= offset
        ncs.add(NCSInstructionType.JSR, jump=start_instruction)

        return definition.return_type

    def add_scoped(self, identifier: Identifier, datatype: DynamicDataType):
        self._global_scope.insert(0, ScopedValue(identifier, datatype))

    def get_scoped(self, identifier: Identifier, root: CodeRoot) -> GetScopedResult:
        offset = 0
        for scoped in self._global_scope:
            offset -= scoped.data_type.size(root)
            if scoped.identifier == identifier:
                break
        else:
            # Provide helpful error with available globals
            available = [
                s.identifier.label for s in self._global_scope[:10]
            ]  # Show first 10
            more = len(self._global_scope) - 10
            more_text = f" (and {more} more)" if more > 0 else ""
            msg = (
                f"Undefined variable '{identifier}'\n"
                f"  Available globals: {', '.join(available)}{more_text}"
            )
            raise CompileError(msg)
        return GetScopedResult(is_global=True, datatype=scoped.data_type, offset=offset)

    def scope_size(self):
        return 0 - sum(scoped.data_type.size(self) for scoped in self._global_scope)


class CodeBlock:
    def __init__(self):
        self.scope: list[ScopedValue] = []
        self._parent: CodeBlock | None = None
        self._statements: list[Statement] = []
        self._break_scope: bool = False
        self.temp_stack: int = 0

    def add(self, statement: Statement):
        self._statements.append(statement)

    def compile(  # noqa: A003
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock | None,
        return_instruction: NCSInstruction,
        break_instruction: NCSInstruction | None,
        continue_instruction: NCSInstruction | None,
    ):
        self._parent = block

        for statement in self._statements:
            if not isinstance(statement, ReturnStatement):
                statement.compile(
                    ncs,
                    root,
                    self,
                    return_instruction,
                    break_instruction,
                    continue_instruction,
                )
            else:
                scope_size = self.full_scope_size(root)

                return_type: DynamicDataType = statement.compile(
                    ncs,
                    root,
                    self,
                    return_instruction,
                    break_instruction=None,
                    continue_instruction=None,
                )
                if return_type != DynamicDataType.VOID:
                    ncs.add(
                        NCSInstructionType.CPDOWNSP,
                        args=[-scope_size - return_type.size(root) * 2, 4],
                    )
                    ncs.add(NCSInstructionType.MOVSP, args=[-return_type.size(root)])

                ncs.add(NCSInstructionType.MOVSP, args=[-scope_size])
                ncs.add(NCSInstructionType.JMP, jump=return_instruction)
                return
        ncs.instructions.append(
            NCSInstruction(NCSInstructionType.MOVSP, [-self.scope_size(root)]),
        )

        if self.temp_stack != 0:
            # If the temp stack is 0 after the whole block has compiled there must be a logic error
            # in the implementation of one of the expression/statement classes
            msg = (
                f"Internal compiler error: Temporary stack not cleared after block compilation\n"
                f"  Temp stack size: {self.temp_stack}\n"
                f"  This indicates a bug in one of the expression/statement compile methods"
            )
            raise ValueError(msg)

    def add_scoped(self, identifier: Identifier, data_type: DynamicDataType):
        self.scope.insert(0, ScopedValue(identifier, data_type))

    def get_scoped(
        self,
        identifier: Identifier,
        root: CodeRoot,
        offset: int | None = None,
    ) -> GetScopedResult:
        offset = -self.temp_stack if offset is None else offset - self.temp_stack
        for scoped in self.scope:
            offset -= scoped.data_type.size(root)
            if scoped.identifier == identifier:
                print(
                    f"[DEBUG] local lookup {identifier.label} temp_stack={self.temp_stack} offset={offset} scope_size={scoped.data_type.size(root)}"
                )
                break
        else:
            if self._parent is not None:
                return self._parent.get_scoped(identifier, root, offset)
            return root.get_scoped(identifier, root)
        return GetScopedResult(
            is_global=False, datatype=scoped.data_type, offset=offset
        )

    def scope_size(self, root: CodeRoot) -> int:
        """Returns size of local scope."""
        return sum(scoped.data_type.size(root) for scoped in self.scope)

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
        if self._parent is not None and not self._parent._break_scope:  # noqa: SLF001
            size += self._parent.break_scope_size(root)
        return size

    def mark_break_scope(self):
        self._break_scope = True


class ScopedValue:
    def __init__(self, identifier: Identifier, data_type: DynamicDataType):
        self.identifier: Identifier = identifier
        self.data_type: DynamicDataType = data_type


class FunctionForwardDeclaration(TopLevelObject):
    def __init__(
        self,
        return_type: DynamicDataType,
        identifier: Identifier,
        parameters: list[FunctionDefinitionParam],
    ):
        self.return_type: DynamicDataType = return_type
        self.identifier: Identifier = identifier
        self.parameters: list[FunctionDefinitionParam] = parameters

    def compile(self, ncs: NCS, root: CodeRoot):  # noqa: A003
        function_name = self.identifier.label

        if self.identifier.label in root.function_map:
            msg = f"Function '{function_name}' already has a prototype or been defined."
            raise CompileError(msg)

        root.function_map[self.identifier.label] = FunctionReference(
            ncs.add(NCSInstructionType.NOP, args=[]),
            self,
        )


class FunctionDefinition(TopLevelObject):
    """Represents a function definition with implementation.

    Contains the function signature (return type, parameters) and the code block
    that implements the function body.

    Note: Signature and block are currently coupled in this class. Future refactoring
    could split these into separate FunctionSignature and CodeBlock for better reusability.
    """

    def __init__(
        self,
        return_type: DynamicDataType,
        identifier: Identifier,
        parameters: list[FunctionDefinitionParam],
        block: CodeBlock,
        line_num: int,
    ):
        self.return_type: DynamicDataType = return_type
        self.identifier: Identifier = identifier
        self.parameters: list[FunctionDefinitionParam] = parameters
        self.block: CodeBlock = block
        self.line_num: int = line_num

        for param in parameters:
            block.add_scoped(param.identifier, param.data_type)

    def compile(self, ncs: NCS, root: CodeRoot):  # noqa: A003
        name = self.identifier.label

        # Make sure all default parameters appear after the required parameters
        previous_is_default = False
        for param in self.parameters:
            is_default = param.default is not None
            if previous_is_default and not is_default:
                msg = "Function parameter without a default value can't follow one with a default value."
                raise CompileError(msg)
            previous_is_default = is_default

        # Make sure params are all constant values
        for param in self.parameters:
            if isinstance(
                param.default, IdentifierExpression
            ) and not param.default.is_constant(root):
                msg = f"Non-constant default value specified for function prototype parameter '{param.identifier}'."
                raise CompileError(msg)

        if name in root.function_map and not root.function_map[name].is_prototype():
            msg = (
                f"Function '{name}' is already defined\n"
                f"  Cannot redefine a function that already has an implementation"
            )
            raise CompileError(msg)
        if name in root.function_map and root.function_map[name].is_prototype():
            self._compile_function(root, name, ncs)
        else:
            retn = NCSInstruction(NCSInstructionType.RETN)

            function_start = ncs.add(NCSInstructionType.NOP, args=[])
            self.block.compile(ncs, root, None, retn, None, None)
            ncs.instructions.append(retn)

            root.function_map[name] = FunctionReference(function_start, self)

    def _compile_function(self, root: CodeRoot, name: str, ncs: NCS):  # noqa: D417
        if not self.is_matching_signature(root.function_map[name].definition):
            prototype = root.function_map[name].definition
            # Build detailed error message
            details = []
            if self.return_type != prototype.return_type:
                details.append(
                    f"Return type mismatch: prototype has {prototype.return_type.builtin.name}, "
                    f"definition has {self.return_type.builtin.name}"
                )
            if len(self.parameters) != len(prototype.parameters):
                details.append(
                    f"Parameter count mismatch: prototype has {len(prototype.parameters)}, "
                    f"definition has {len(self.parameters)}"
                )
            else:
                for i, (def_param, proto_param) in enumerate(
                    zip(self.parameters, prototype.parameters)
                ):
                    if def_param.data_type != proto_param.data_type:
                        details.append(
                            f"Parameter {i + 1} type mismatch: prototype has {proto_param.data_type.builtin.name}, "
                            f"definition has {def_param.data_type.builtin.name}"
                        )

            msg = (
                f"Function '{name}' definition does not match its prototype\n"
                f"  " + "\n  ".join(details)
            )
            raise CompileError(msg)

        # Function has forward declaration, insert the compiled definition after the stub
        temp = NCS()
        retn = NCSInstruction(NCSInstructionType.RETN)
        self.block.compile(temp, root, None, retn, None, None)
        temp.instructions.append(retn)

        stub_index: int = ncs.instructions.index(root.function_map[name].instruction)
        ncs.instructions[stub_index + 1 : stub_index + 1] = temp.instructions

    def is_matching_signature(
        self, prototype: FunctionForwardDeclaration | FunctionDefinition
    ) -> bool:
        if self.return_type != prototype.return_type:
            return False
        if len(self.parameters) != len(prototype.parameters):
            return False
        return all(
            these_parameters.data_type == prototype.parameters[i].data_type
            for i, these_parameters in enumerate(self.parameters)
        )


class FunctionDefinitionParam:
    def __init__(
        self,
        data_type: DynamicDataType,
        identifier: Identifier,
        default: Expression | None = None,
    ):
        self.data_type: DynamicDataType = data_type
        self.identifier: Identifier = identifier
        self.default: Expression | None = default


class IncludeScript(TopLevelObject):
    def __init__(
        self,
        file: StringExpression,
        library: dict[str, bytes] | None = None,
    ):
        self.file: StringExpression = file
        self.library: dict[str, bytes] = {} if library is None else library

    def compile(self, ncs: NCS, root: CodeRoot):  # noqa: A003
        """Compile an include script.

        FIXED: Only register symbols (functions, constants, structs) from the include
        for resolution. Do NOT add all objects from the include to root.objects, as this
        causes all include content to be compiled regardless of whether it's used.
        This matches nwnnsscomp behavior where only referenced symbols generate bytecode.

        The bug was: root.objects = t.objects + root.objects
        This dumped all include objects into compilation, causing incorrect string offsets.
        """
        from pykotor.resource.formats.ncs.compiler.parser import NssParser  # noqa: PLC0415

        lookup_paths = cast(
            list[str] | None,
            [str(path) for path in root.library_lookup]
            if root.library_lookup
            else None,
        )

        nss_parser = NssParser(
            root.functions,
            root.constants,
            root.library,
            lookup_paths,
        )
        nss_parser.library = self.library
        nss_parser.constants = root.constants
        source: str = self._get_script(root)
        t: CodeRoot = nss_parser.parser.parse(source, tracking=True)

        # FIXED: Only merge symbol tables (function_map, struct_map), not all objects.
        # This ensures only symbols are available for resolution, but they're only
        # compiled if actually referenced. This matches nwnnsscomp behavior.
        root.function_map.update(t.function_map)
        root.struct_map.update(t.struct_map)
        # Note: Constants are already shared via root.constants, so no need to merge

    def _get_script(self, root: CodeRoot) -> str:
        """Load included script from filesystem or library.

        Args:
        ----
            root: Code root containing library lookup paths

        Returns:
        -------
            str: Source code of the included script

        Raises:
        ------
            MissingIncludeError: If included file cannot be found
        """
        # Try to find in filesystem first
        for folder in root.library_lookup:
            filepath: Path = folder / f"{self.file.value}.nss"
            if filepath.is_file():
                try:
                    source_bytes = filepath.read_bytes()
                    source = source_bytes.decode(errors="ignore")
                    break
                except Exception as e:
                    msg = f"Failed to read include file '{filepath}': {e}"
                    raise MissingIncludeError(msg) from e
        else:
            # Not found in filesystem, try library
            case_sensitive: bool = not root.library_lookup or all(
                lookup_path
                for lookup_path in root.library_lookup
                if isinstance(lookup_path, Path)
            )
            include_filename: str = (
                self.file.value if case_sensitive else self.file.value.lower()
            )
            if include_filename in self.library:
                source = self.library[include_filename].decode(errors="ignore")
            else:
                # Build helpful error message with search paths
                search_paths = [str(folder) for folder in root.library_lookup]
                msg = (
                    f"Could not find included script '{include_filename}.nss'\n"
                    f"  Searched in {len(search_paths)} path(s): {', '.join(search_paths[:3])}"
                    f"{'...' if len(search_paths) > 3 else ''}\n"
                    f"  Also checked {len(self.library)} library file(s)"
                )
                raise MissingIncludeError(msg)
        return source


class StructDefinition(TopLevelObject):
    def __init__(self, identifier: Identifier, members: list[StructMember]):
        self.identifier: Identifier = identifier
        self.members: list[StructMember] = members

    def compile(self, ncs: NCS, root: CodeRoot):  # noqa: A003
        if len(self.members) == 0:
            msg = (
                f"Struct '{self.identifier}' cannot be empty\n"
                f"  Structs must have at least one member"
            )
            raise CompileError(msg)
        root.struct_map[self.identifier.label] = Struct(self.identifier, self.members)


class Expression(ABC):
    """Abstract base class for NSS expressions.

    Expressions compile to NCS bytecode instructions that evaluate to values.
    All expression types (literals, operators, function calls, etc.) inherit from this.

    References:
    ----------
        vendor/KotOR.js/src/nwscript/NWScriptCompiler.ts (Expression compilation)
        vendor/HoloLSP/server/src/nwscript-ast.ts (Expression AST nodes)
    """

    @abstractmethod
    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
    ) -> DynamicDataType: ...


class Statement(ABC):
    """Abstract base class for NSS statements.

    Statements compile to NCS bytecode instructions that perform actions (control flow,
    assignments, declarations, etc.). All statement types inherit from this.

    References:
    ----------
        vendor/KotOR.js/src/nwscript/NWScriptCompiler.ts (Statement compilation)
        vendor/HoloLSP/server/src/nwscript-ast.ts (Statement AST nodes)
    """

    def __init__(self):
        self.line_num: None = None

    @abstractmethod
    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        return_instruction: NCSInstruction,
        break_instruction: NCSInstruction | None,
        continue_instruction: NCSInstruction | None,
    ) -> object: ...


class FieldAccess:
    def __init__(self, identifiers: list[Identifier]):
        super().__init__()
        self.identifiers: list[Identifier] = identifiers

    def get_scoped(self, block: CodeBlock, root: CodeRoot) -> GetScopedResult:
        """Get scoped variable information for field access.

        Args:
        ----
            block: Current code block
            root: Code root context

        Returns:
        -------
            GetScopedResult: Variable scope information

        Raises:
        ------
            CompileError: If field access is invalid
        """
        if len(self.identifiers) == 0:
            msg = "Internal error: FieldAccess has no identifiers"
            raise CompileError(msg)

        first: Identifier = self.identifiers[0]
        scoped: GetScopedResult = block.get_scoped(first, root)

        is_global: bool = scoped.is_global
        offset: int = scoped.offset
        datatype: DynamicDataType = scoped.datatype

        for next_ident in self.identifiers[1:]:
            # Check previous datatype to see what members are accessible
            if datatype.builtin == DataType.VECTOR:
                datatype = DynamicDataType.FLOAT
                if next_ident.label == "x":
                    offset += 0
                elif next_ident.label == "y":
                    offset += 4
                elif next_ident.label == "z":
                    offset += 8
                else:
                    msg = f"Attempting to access unknown member '{next_ident}' on datatype '{datatype}'."
                    raise CompileError(msg)
            elif datatype.builtin == DataType.STRUCT:
                assert datatype._struct is not None, (
                    "datatype._struct cannot be None in FieldAccess.get_scoped()"
                )  # noqa: SLF001
                offset += root.struct_map[datatype._struct].child_offset(  # noqa: SLF001
                    root,
                    next_ident,
                )
                datatype = root.struct_map[datatype._struct].child_type(  # noqa: SLF001
                    root,
                    next_ident,
                )
            else:
                msg = f"Attempting to access unknown member '{next_ident}' on datatype '{datatype}'."
                raise CompileError(msg)

        return GetScopedResult(is_global, datatype, offset)

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:  # noqa: A003
        is_global, variable_type, stack_index = self.get_scoped(block, root)
        instruction_type = (
            NCSInstructionType.CPTOPBP if is_global else NCSInstructionType.CPTOPSP
        )
        ncs.add(instruction_type, args=[stack_index, variable_type.size(root)])
        return variable_type


# region Expressions: Simple
class IdentifierExpression(Expression):
    def __init__(self, value: Identifier):
        super().__init__()
        self.identifier: Identifier = value

    def __eq__(self, other: IdentifierExpression | object) -> bool:
        if self is other:
            return True
        if isinstance(other, IdentifierExpression):
            return self.identifier == other.identifier
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.identifier)

    def __repr__(self) -> str:
        return f"IdentifierExpression(identifier={self.identifier})"

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:  # noqa: A003
        # Scan for any constants that are stored as part of the compiler (from nwscript).
        constant: ScriptConstant | None = self.get_constant(root)
        if constant is not None:
            if constant.datatype == DataType.INT:
                ncs.add(NCSInstructionType.CONSTI, args=[int(constant.value)])
            elif constant.datatype == DataType.FLOAT:
                ncs.add(NCSInstructionType.CONSTF, args=[float(constant.value)])
            elif constant.datatype == DataType.STRING:
                ncs.add(NCSInstructionType.CONSTS, args=[str(constant.value)])
            return DynamicDataType(constant.datatype)

        is_global, datatype, stack_index = block.get_scoped(self.identifier, root)
        instruction_type = (
            NCSInstructionType.CPTOPBP if is_global else NCSInstructionType.CPTOPSP
        )
        ncs.add(instruction_type, args=[stack_index, datatype.size(root)])
        return datatype

    def get_constant(self, root: CodeRoot) -> ScriptConstant | None:
        return next(
            (
                constant
                for constant in root.constants
                if constant.name == self.identifier.label
            ),
            None,
        )

    def is_constant(self, root: CodeRoot) -> bool:
        return self.get_constant(root) is not None


class FieldAccessExpression(Expression):
    def __init__(self, field_access: FieldAccess):
        super().__init__()
        self.field_access: FieldAccess = field_access

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:  # noqa: A003
        scoped = self.field_access.get_scoped(block, root)
        instruction_type = (
            NCSInstructionType.CPTOPBP
            if scoped.is_global
            else NCSInstructionType.CPTOPSP
        )
        ncs.instructions.append(
            NCSInstruction(
                instruction_type,
                [scoped.offset, scoped.datatype.size(root)],
            ),
        )
        return scoped.datatype


class StringExpression(Expression):
    def __init__(self, value: str):
        super().__init__()
        self.value: str = value

    def __eq__(self, other: StringExpression | object):
        if self is other:
            return True
        if isinstance(other, StringExpression):
            return self.value == other.value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:
        return f"StringExpression(value={self.value})"

    def data_type(self) -> DynamicDataType:
        return DynamicDataType.STRING

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:  # noqa: A003
        ncs.instructions.append(NCSInstruction(NCSInstructionType.CONSTS, [self.value]))
        return DynamicDataType.STRING


class IntExpression(Expression):
    def __init__(self, value: int):
        super().__init__()
        self.value: int = value

    def __eq__(self, other: IntExpression | object):
        if self is other:
            return True
        if isinstance(other, IntExpression):
            return self.value == other.value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:
        return f"IntExpression(value={self.value})"

    def data_type(self) -> DynamicDataType:
        return DynamicDataType.INT

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:  # noqa: A003
        ncs.instructions.append(NCSInstruction(NCSInstructionType.CONSTI, [self.value]))
        return DynamicDataType.INT


class ObjectExpression(Expression):
    def __init__(self, value: int):
        super().__init__()
        self.value: int = value

    def __eq__(self, other: ObjectExpression | object):
        if self is other:
            return True
        if isinstance(other, ObjectExpression):
            return self.value == other.value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:
        return f"ObjectExpression(value={self.value})"

    def data_type(self) -> DynamicDataType:
        return DynamicDataType.OBJECT

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:  # noqa: A003
        ncs.instructions.append(NCSInstruction(NCSInstructionType.CONSTO, [self.value]))
        return DynamicDataType.OBJECT


class FloatExpression(Expression):
    def __init__(self, value: float):
        super().__init__()
        self.value: float = value

    def __eq__(self, other: FloatExpression | object):
        if self is other:
            return True
        if isinstance(other, FloatExpression):
            return self.value == other.value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:
        return f"FloatExpression(value={self.value})"

    def data_type(self) -> DynamicDataType:
        return DynamicDataType.FLOAT

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:  # noqa: A003
        ncs.instructions.append(NCSInstruction(NCSInstructionType.CONSTF, [self.value]))
        return DynamicDataType.FLOAT


class VectorExpression(Expression):
    def __init__(self, x: FloatExpression, y: FloatExpression, z: FloatExpression):
        super().__init__()
        self.x: FloatExpression = x
        self.y: FloatExpression = y
        self.z: FloatExpression = z

    def __eq__(self, other: VectorExpression | object):
        if self is other:
            return True
        if isinstance(other, VectorExpression):
            return self.x == other.x and self.y == other.y and self.z == other.z
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.x) ^ hash(self.y) ^ hash(self.z)

    def __repr__(self) -> str:
        return f"VectorExpression(x={self.x}, y={self.y}, z={self.z})"

    def data_type(self) -> DynamicDataType:
        return DynamicDataType.FLOAT

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:  # noqa: A003
        self.x.compile(ncs, root, block)
        self.y.compile(ncs, root, block)
        self.z.compile(ncs, root, block)
        return DynamicDataType.VECTOR


class EngineCallExpression(Expression):
    def __init__(
        self,
        function: ScriptFunction,
        routine_id: int,
        data_type: DynamicDataType,
        args: list[Expression],
    ):
        super().__init__()
        self._function: ScriptFunction = function
        self._routine_id: int = routine_id
        self._args: list[Expression] = args

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
    ) -> DynamicDataType:  # noqa: A003
        arg_count = len(self._args)

        if arg_count > len(self._function.params):
            msg = (
                f"Too many arguments for '{self._function.name}'\n"
                f"  Expected: {len(self._function.params)}, Got: {arg_count}"
            )
            raise CompileError(msg)

        for i, param in enumerate(self._function.params):
            if i >= arg_count:
                if param.default is None:
                    required_params = [
                        p.name for p in self._function.params if p.default is None
                    ]
                    msg = (
                        f"Missing required arguments for '{self._function.name}'\n"
                        f"  Required parameters: {', '.join(required_params)}\n"
                        f"  Provided: {arg_count} argument(s)"
                    )
                    raise CompileError(msg)
                constant: ScriptConstant | None = next(
                    (
                        constant
                        for constant in root.constants
                        if constant.name == param.default
                    ),
                    None,
                )
                if constant is None:
                    if param.datatype == DataType.INT:
                        self._args.append(IntExpression(int(param.default)))
                    elif param.datatype == DataType.FLOAT:
                        self._args.append(FloatExpression(float(param.default)))
                    elif param.datatype == DataType.STRING:
                        self._args.append(StringExpression(param.default))
                    elif param.datatype == DataType.VECTOR:
                        x = FloatExpression(param.default.x)
                        y = FloatExpression(param.default.y)
                        z = FloatExpression(param.default.z)
                        self._args.append(VectorExpression(x, y, z))
                    elif param.datatype == DataType.OBJECT:
                        self._args.append(ObjectExpression(int(param.default)))
                    else:
                        msg = (
                            f"Unsupported default parameter type '{param.datatype.name}' for '{param.name}' in '{self._function.name}'\n"
                            f"  This may indicate a compiler limitation"
                        )
                        raise CompileError(msg)

                elif constant.datatype == DataType.INT:
                    self._args.append(IntExpression(int(constant.value)))
                elif constant.datatype == DataType.FLOAT:
                    self._args.append(FloatExpression(float(constant.value)))
                elif constant.datatype == DataType.STRING:
                    self._args.append(StringExpression(str(constant.value)))
                elif constant.datatype == DataType.OBJECT:
                    self._args.append(ObjectExpression(int(constant.value)))
        this_stack = 0
        for i, arg in enumerate(reversed(self._args)):
            param_type = DynamicDataType(self._function.params[-i - 1].datatype)
            if param_type == DataType.ACTION:
                after_command = NCSInstruction()
                ncs.add(
                    NCSInstructionType.STORE_STATE,
                    args=[-root.scope_size(), block.full_scope_size(root)],
                )
                ncs.add(NCSInstructionType.JMP, jump=after_command)
                arg.compile(ncs, root, block)
                ncs.add(NCSInstructionType.RETN)

                ncs.instructions.append(after_command)
            else:
                added = arg.compile(ncs, root, block)
                block.temp_stack += added.size(root)
                this_stack += added.size(root)

                if added != param_type:
                    param = self._function.params[-i - 1]
                    # Get type names safely
                    if isinstance(param_type, DataType):
                        param_type_name = param_type.name
                    else:
                        param_type_name = str(param_type)
                    msg = (
                        f"Type mismatch for parameter '{param.name}' in call to '{self._function.name}'\n"
                        f"  Expected: {param_type_name.lower()}\n"
                        f"  Got: {added.builtin.name.lower()}"
                    )
                    raise CompileError(msg)

        ncs.instructions.append(
            NCSInstruction(
                NCSInstructionType.ACTION,
                [self._routine_id, len(self._args)],
            ),
        )
        block.temp_stack -= this_stack
        return DynamicDataType(self._function.returntype)


class FunctionCallExpression(Expression):
    def __init__(self, function: Identifier, args: list[Expression]):
        super().__init__()
        self._function: Identifier = function
        self._args: list[Expression] = args

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        if self._function.label not in root.function_map:
            # Provide helpful error with similar function names
            available_funcs = list(root.function_map.keys())[:10]
            msg = (
                f"Undefined function '{self._function.label}'\n"
                f"  Available functions: {', '.join(available_funcs)}"
                f"{'...' if len(root.function_map) > 10 else ''}"
            )
            raise CompileError(msg)

        func_def = root.function_map[self._function.label].definition
        block.temp_stack += func_def.return_type.size(root)
        x = root.compile_jsr(ncs, block, self._function.label, *self._args)
        block.temp_stack -= func_def.return_type.size(root)
        return x


# endregion


class BinaryOperatorExpression(Expression):
    def __init__(
        self,
        expression1: Expression,
        expression2: Expression,
        mapping: list[BinaryOperatorMapping],
    ):
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2
        self.compatibility: list[BinaryOperatorMapping] = mapping

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:  # noqa: A003
        type1 = self.expression1.compile(ncs, root, block)
        block.temp_stack += 4
        type2 = self.expression2.compile(ncs, root, block)
        block.temp_stack += 4

        for x in self.compatibility:
            if type1 == x.lhs and type2 == x.rhs:
                ncs.add(x.instruction)
                break
        else:
            # Build helpful error showing what operations are supported
            supported = [
                f"{m.lhs.name.lower()} {m.instruction.name} {m.rhs.name.lower()}"
                for m in self.compatibility[:3]
            ]
            msg = (
                f"Incompatible types for binary operation: {type1.builtin.name.lower()} and {type2.builtin.name.lower()}\n"
                f"  Supported combinations: {', '.join(supported)}"
                f"{'...' if len(self.compatibility) > 3 else ''}"
            )
            raise CompileError(msg)

        block.temp_stack -= 8
        return DynamicDataType(x.result)


class UnaryOperatorExpression(Expression):
    def __init__(self, expression1: Expression, mapping: list[UnaryOperatorMapping]):
        super().__init__()
        self.expression1: Expression = expression1
        self.compatibility: list[UnaryOperatorMapping] = mapping

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:  # noqa: A003
        type1 = self.expression1.compile(ncs, root, block)

        block.temp_stack += 4

        for x in self.compatibility:
            if type1 == x.rhs:
                ncs.add(x.instruction)
                break
        else:
            supported_types = [m.rhs.name.lower() for m in self.compatibility]
            msg = (
                f"Incompatible type for unary operation: {type1.builtin.name.lower()}\n"
                f"  Supported types: {', '.join(supported_types)}"
            )
            raise CompileError(msg)

        block.temp_stack -= 4
        return type1


class LogicalNotExpression(Expression):
    def __init__(self, expression1: Expression):
        super().__init__()
        self.expression1: Expression = expression1

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        type1 = self.expression1.compile(ncs, root, block)
        block.temp_stack += 4

        if type1 == DynamicDataType.INT:
            ncs.add(NCSInstructionType.NOTI)
        else:
            msg = (
                f"Logical NOT requires integer operand, got {type1.builtin.name.lower()}\n"
                f"  Note: In NWScript, only int types can be used in logical operations"
            )
            raise CompileError(msg)

        block.temp_stack -= 4
        return DynamicDataType.INT


class BitwiseNotExpression(Expression):
    def __init__(self, expression1: Expression):
        super().__init__()
        self.expression1: Expression = expression1

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        type1 = self.expression1.compile(ncs, root, block)
        block.temp_stack += 4

        if type1 == DynamicDataType.INT:
            ncs.add(NCSInstructionType.COMPI)
        else:
            msg = (
                f"Bitwise NOT (~) requires integer operand, got {type1.builtin.name.lower()}\n"
                f"  Note: Bitwise operations only work on int types"
            )
            raise CompileError(msg)

        block.temp_stack -= 4
        return type1


# region Expressions: Assignment
class Assignment(Expression):
    def __init__(self, field_access: FieldAccess, value: Expression):
        super().__init__()
        self.field_access: FieldAccess = field_access
        self.expression: Expression = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        variable_type = self.expression.compile(ncs, root, block)
        is_global, expression_type, stack_index = self.field_access.get_scoped(
            block,
            root,
        )
        instruction_type = (
            NCSInstructionType.CPDOWNBP if is_global else NCSInstructionType.CPDOWNSP
        )
        stack_index -= 0 if is_global else variable_type.size(root)

        # Track the value pushed onto the stack by the expression (after resolving scope)
        block.temp_stack += variable_type.size(root)

        if variable_type != expression_type:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = (
                f"Type mismatch in assignment to '{var_name}'\n"
                f"  Variable type: {expression_type.builtin.name}\n"
                f"  Expression type: {variable_type.builtin.name}"
            )
            raise CompileError(msg)

        # Copy the value that the expression has already been placed on the stack to where the identifiers position is
        ncs.instructions.append(
            NCSInstruction(instruction_type, [stack_index, expression_type.size(root)]),
        )

        block.temp_stack -= variable_type.size(root)

        return variable_type


class AdditionAssignment(Expression):
    def __init__(self, field_access: FieldAccess, value: Expression):
        super().__init__()
        self.field_access: FieldAccess = field_access
        self.expression: Expression = value

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
    ) -> DynamicDataType:
        # Copy the variable to the top of the stack
        is_global, variable_type, stack_index = self.field_access.get_scoped(
            block,
            root,
        )
        instruction_type = (
            NCSInstructionType.CPTOPBP if is_global else NCSInstructionType.CPTOPSP
        )
        ncs.add(instruction_type, args=[stack_index, variable_type.size(root)])
        block.temp_stack += variable_type.size(root)

        # Add the result of the expression to the stack
        expresion_type = self.expression.compile(ncs, root, block)
        block.temp_stack += expresion_type.size(root)

        # Determine what instruction to apply to the two values
        if (
            variable_type == DynamicDataType.INT
            and expresion_type == DynamicDataType.INT
        ):
            arthimetic_instruction = NCSInstructionType.ADDII
        elif (
            variable_type == DynamicDataType.INT
            and expresion_type == DynamicDataType.FLOAT
        ):
            arthimetic_instruction = NCSInstructionType.ADDIF
        elif (
            variable_type == DynamicDataType.FLOAT
            and expresion_type == DynamicDataType.FLOAT
        ):
            arthimetic_instruction = NCSInstructionType.ADDFF
        elif (
            variable_type == DynamicDataType.FLOAT
            and expresion_type == DynamicDataType.INT
        ):
            arthimetic_instruction = NCSInstructionType.ADDFI
        elif (
            variable_type == DynamicDataType.STRING
            and expresion_type == DynamicDataType.STRING
        ):
            arthimetic_instruction = NCSInstructionType.ADDSS
        else:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = (
                f"Type mismatch in += operation on '{var_name}'\n"
                f"  Variable type: {variable_type.builtin.name}\n"
                f"  Expression type: {expresion_type.builtin.name}\n"
                f"  Supported: int+=int, float+=float/int, string+=string"
            )
            raise CompileError(msg)

        # Add the expression and our temp variable copy together
        ncs.add(arthimetic_instruction, args=[])

        # Copy the result to the original variable in the stack
        ins_cpdown = (
            NCSInstructionType.CPDOWNBP if is_global else NCSInstructionType.CPDOWNSP
        )
        offset_cpdown = (
            stack_index if is_global else stack_index - expresion_type.size(root)
        )
        ncs.add(ins_cpdown, args=[offset_cpdown, variable_type.size(root)])

        block.temp_stack -= variable_type.size(root)
        block.temp_stack -= expresion_type.size(root)
        return expresion_type


class SubtractionAssignment(Expression):
    def __init__(self, field_access: FieldAccess, value: Expression):
        super().__init__()
        self.field_access: FieldAccess = field_access
        self.expression: Expression = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        # Copy the variable to the top of the stack
        isglobal, variable_type, stack_index = self.field_access.get_scoped(block, root)
        instruction_type = (
            NCSInstructionType.CPTOPBP if isglobal else NCSInstructionType.CPTOPSP
        )
        ncs.add(instruction_type, args=[stack_index, variable_type.size(root)])
        block.temp_stack += variable_type.size(root)

        # Add the result of the expression to the stack
        expresion_type = self.expression.compile(ncs, root, block)
        block.temp_stack += expresion_type.size(root)

        # Determine what instruction to apply to the two values
        if (
            variable_type == DynamicDataType.INT
            and expresion_type == DynamicDataType.INT
        ):
            arthimetic_instruction = NCSInstructionType.SUBII
        elif (
            variable_type == DynamicDataType.INT
            and expresion_type == DynamicDataType.FLOAT
        ):
            arthimetic_instruction = NCSInstructionType.SUBIF
        elif (
            variable_type == DynamicDataType.FLOAT
            and expresion_type == DynamicDataType.FLOAT
        ):
            arthimetic_instruction = NCSInstructionType.SUBFF
        elif (
            variable_type == DynamicDataType.FLOAT
            and expresion_type == DynamicDataType.INT
        ):
            arthimetic_instruction = NCSInstructionType.SUBFI
        else:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = (
                f"Type mismatch in -= operation on '{var_name}'\n"
                f"  Variable type: {variable_type.builtin.name}\n"
                f"  Expression type: {expresion_type.builtin.name}\n"
                f"  Supported: int-=int, float-=float/int"
            )
            raise CompileError(msg)

        # Add the expression and our temp variable copy together
        ncs.add(arthimetic_instruction)

        # Copy the result to the original variable in the stack
        ins_cpdown = (
            NCSInstructionType.CPDOWNBP if isglobal else NCSInstructionType.CPDOWNSP
        )
        offset_cpdown = (
            stack_index if isglobal else stack_index - expresion_type.size(root)
        )
        ncs.add(ins_cpdown, args=[offset_cpdown, variable_type.size(root)])

        block.temp_stack -= expresion_type.size(root)
        block.temp_stack -= variable_type.size(root)
        return expresion_type


class MultiplicationAssignment(Expression):
    def __init__(self, field_access: FieldAccess, value: Expression):
        super().__init__()
        self.field_access: FieldAccess = field_access
        self.expression: Expression = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        # Copy the variable to the top of the stack
        isglobal, variable_type, stack_index = self.field_access.get_scoped(block, root)
        instruction_type = (
            NCSInstructionType.CPTOPBP if isglobal else NCSInstructionType.CPTOPSP
        )
        ncs.add(instruction_type, args=[stack_index, variable_type.size(root)])
        block.temp_stack += variable_type.size(root)

        # Add the result of the expression to the stack
        expresion_type = self.expression.compile(ncs, root, block)
        block.temp_stack += expresion_type.size(root)

        # Determine what instruction to apply to the two values
        if (
            variable_type == DynamicDataType.INT
            and expresion_type == DynamicDataType.INT
        ):
            arthimetic_instruction = NCSInstructionType.MULII
        elif (
            variable_type == DynamicDataType.INT
            and expresion_type == DynamicDataType.FLOAT
        ):
            arthimetic_instruction = NCSInstructionType.MULIF
        elif (
            variable_type == DynamicDataType.FLOAT
            and expresion_type == DynamicDataType.FLOAT
        ):
            arthimetic_instruction = NCSInstructionType.MULFF
        elif (
            variable_type == DynamicDataType.FLOAT
            and expresion_type == DynamicDataType.INT
        ):
            arthimetic_instruction = NCSInstructionType.MULFI
        else:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = (
                f"Type mismatch in *= operation on '{var_name}'\n"
                f"  Variable type: {variable_type.builtin.name}\n"
                f"  Expression type: {expresion_type.builtin.name}\n"
                f"  Supported: int*=int, float*=float/int"
            )
            raise CompileError(msg)

        # Add the expression and our temp variable copy together
        ncs.add(arthimetic_instruction)

        # Copy the result to the original variable in the stack
        ins_cpdown = (
            NCSInstructionType.CPDOWNBP if isglobal else NCSInstructionType.CPDOWNSP
        )
        offset_cpdown = (
            stack_index if isglobal else stack_index - expresion_type.size(root)
        )
        ncs.add(ins_cpdown, args=[offset_cpdown, variable_type.size(root)])

        block.temp_stack -= expresion_type.size(root)
        block.temp_stack -= variable_type.size(root)
        return expresion_type


class DivisionAssignment(Expression):
    def __init__(self, field_access: FieldAccess, value: Expression):
        super().__init__()
        self.field_access: FieldAccess = field_access
        self.expression: Expression = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        # Copy the variable to the top of the stack
        isglobal, variable_type, stack_index = self.field_access.get_scoped(block, root)
        instruction_type = (
            NCSInstructionType.CPTOPBP if isglobal else NCSInstructionType.CPTOPSP
        )
        ncs.add(instruction_type, args=[stack_index, variable_type.size(root)])
        block.temp_stack += variable_type.size(root)

        # Add the result of the expression to the stack
        expresion_type = self.expression.compile(ncs, root, block)
        block.temp_stack += expresion_type.size(root)

        # Determine what instruction to apply to the two values
        if (
            variable_type == DynamicDataType.INT
            and expresion_type == DynamicDataType.INT
        ):
            arthimetic_instruction = NCSInstructionType.DIVII
        elif (
            variable_type == DynamicDataType.INT
            and expresion_type == DynamicDataType.FLOAT
        ):
            arthimetic_instruction = NCSInstructionType.DIVIF
        elif (
            variable_type == DynamicDataType.FLOAT
            and expresion_type == DynamicDataType.FLOAT
        ):
            arthimetic_instruction = NCSInstructionType.DIVFF
        elif (
            variable_type == DynamicDataType.FLOAT
            and expresion_type == DynamicDataType.INT
        ):
            arthimetic_instruction = NCSInstructionType.DIVFI
        else:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = (
                f"Type mismatch in /= operation on '{var_name}'\n"
                f"  Variable type: {variable_type.builtin.name}\n"
                f"  Expression type: {expresion_type.builtin.name}\n"
                f"  Supported: int/=int, float/=float/int"
            )
            raise CompileError(msg)

        # Add the expression and our temp variable copy together
        ncs.add(arthimetic_instruction)

        # Copy the result to the original variable in the stack
        ins_cpdown = (
            NCSInstructionType.CPDOWNBP if isglobal else NCSInstructionType.CPDOWNSP
        )
        offset_cpdown = (
            stack_index if isglobal else stack_index - expresion_type.size(root)
        )
        ncs.add(ins_cpdown, args=[offset_cpdown, variable_type.size(root)])

        block.temp_stack -= expresion_type.size(root)
        block.temp_stack -= variable_type.size(root)
        return expresion_type


# endregion


# region Statements
class EmptyStatement(Statement):
    def __init__(self):
        super().__init__()

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        return_instruction: NCSInstruction,
        break_instruction: NCSInstruction | None,
        continue_instruction: NCSInstruction | None,
    ) -> DynamicDataType:
        return DynamicDataType.VOID


class NopStatement(Statement):
    def __init__(self, string: str):
        super().__init__()
        self.string = string

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        return_instruction: NCSInstruction,
        break_instruction: NCSInstruction | None,
        continue_instruction: NCSInstruction | None,
    ) -> DynamicDataType:
        ncs.add(NCSInstructionType.NOP, args=[self.string])
        return DynamicDataType.VOID


class ExpressionStatement(Statement):
    def __init__(self, expression: Expression):
        super().__init__()
        self.expression: Expression = expression

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        return_instruction: NCSInstruction,
        break_instruction: NCSInstruction | None,
        continue_instruction: NCSInstruction | None,
    ):
        expression_type = self.expression.compile(ncs, root, block)
        ncs.add(NCSInstructionType.MOVSP, args=[-expression_type.size(root)])


class DeclarationStatement(Statement):
    def __init__(
        self,
        data_type: DynamicDataType,
        declarators: list[VariableDeclarator],
    ):
        super().__init__()
        self.data_type: DynamicDataType = data_type
        self.declarators: list[VariableDeclarator] = declarators

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        return_instruction: NCSInstruction,
        break_instruction: NCSInstruction | None,
        continue_instruction: NCSInstruction | None,
    ):
        for declarator in self.declarators:
            declarator.compile(ncs, root, block, self.data_type)


class VariableDeclarator:
    def __init__(self, identifier: Identifier):
        self.identifier: Identifier = identifier

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        data_type: DynamicDataType,
    ):
        if data_type.builtin == DataType.INT:
            ncs.add(NCSInstructionType.RSADDI)
        elif data_type.builtin == DataType.FLOAT:
            ncs.add(NCSInstructionType.RSADDF)
        elif data_type.builtin == DataType.STRING:
            ncs.add(NCSInstructionType.RSADDS)
        elif data_type.builtin == DataType.OBJECT:
            ncs.add(NCSInstructionType.RSADDO)
        elif data_type.builtin == DataType.EVENT:
            ncs.add(NCSInstructionType.RSADDEVT)
        elif data_type.builtin == DataType.LOCATION:
            ncs.add(NCSInstructionType.RSADDLOC)
        elif data_type.builtin == DataType.TALENT:
            ncs.add(NCSInstructionType.RSADDTAL)
        elif data_type.builtin == DataType.EFFECT:
            ncs.add(NCSInstructionType.RSADDEFF)
        elif data_type.builtin == DataType.VECTOR:
            ncs.add(NCSInstructionType.RSADDF)
            ncs.add(NCSInstructionType.RSADDF)
            ncs.add(NCSInstructionType.RSADDF)
        elif data_type.builtin == DataType.STRUCT:
            struct_name = data_type._struct  # noqa: SLF001
            if struct_name is not None and struct_name in root.struct_map:
                root.struct_map[struct_name].initialize(ncs, root)
            else:
                msg = f"Unknown struct type for variable '{self.identifier}'"
                raise CompileError(msg)
        elif data_type.builtin == DataType.VOID:
            msg = (
                f"Cannot declare variable '{self.identifier}' with void type\n"
                f"  void can only be used as a function return type"
            )
            raise CompileError(msg)
        else:
            msg = (
                f"Unsupported type '{data_type.builtin.name}' for variable '{self.identifier}'\n"
                f"  Supported types: int, float, string, object, vector, effect, event, location, talent, struct"
            )
            raise CompileError(msg)

        block.add_scoped(self.identifier, data_type)


class VariableInitializer:
    def __init__(self, identifier: Identifier, expression: Expression):
        self.identifier: Identifier = identifier
        self.expression: Expression = expression

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        data_type: DynamicDataType,
    ):
        initial_temp_stack = block.temp_stack

        # Reuse existing declarator logic for allocation
        declarator = VariableDeclarator(self.identifier)
        declarator.compile(ncs, root, block, data_type)

        # Emit assignment using existing machinery (keeps stack bookkeeping consistent)
        assignment = Assignment(FieldAccess([self.identifier]), self.expression)
        result_type = assignment.compile(ncs, root, block)

        # Remove the temporary expression result left on the stack by the assignment
        ncs.add(NCSInstructionType.MOVSP, args=[-result_type.size(root)])

        # Restore temporary stack tracking to its pre-initializer state
        block.temp_stack = initial_temp_stack


class ConditionalBlock(Statement):
    def __init__(
        self,
        if_block: ConditionAndBlock,
        else_if_blocks: list[ConditionAndBlock],
        else_block: CodeBlock,
    ):
        super().__init__()
        self.if_blocks: list[ConditionAndBlock] = [if_block, *else_if_blocks]
        self.else_block: CodeBlock | None = else_block

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        return_instruction: NCSInstruction,
        break_instruction: NCSInstruction | None,
        continue_instruction: NCSInstruction | None,
    ):
        jump_count: int = 1 + len(self.if_blocks)
        jump_tos: list[NCSInstruction] = [
            NCSInstruction(NCSInstructionType.NOP, args=[]) for _ in range(jump_count)
        ]

        for i, else_if in enumerate(self.if_blocks):
            else_if.condition.compile(ncs, root, block)
            ncs.add(NCSInstructionType.JZ, jump=jump_tos[i])

            else_if.block.compile(
                ncs,
                root,
                block,
                return_instruction,
                break_instruction,
                continue_instruction,
            )
            ncs.add(NCSInstructionType.JMP, jump=jump_tos[-1])

            ncs.instructions.append(jump_tos[i])

        if self.else_block is not None:
            self.else_block.compile(
                ncs,
                root,
                block,
                return_instruction,
                break_instruction,
                continue_instruction,
            )

        ncs.instructions.append(jump_tos[-1])


class ConditionAndBlock:
    def __init__(self, condition: Expression, block: CodeBlock):
        self.condition: Expression = condition
        self.block: CodeBlock = block


class ReturnStatement(Statement):
    def __init__(self, expression: Expression | None = None):
        super().__init__()
        self.expression: Expression | None = expression

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        return_instruction: NCSInstruction,
        break_instruction: NCSInstruction | None,
        continue_instruction: NCSInstruction | None,
    ) -> DynamicDataType:
        if self.expression is not None:
            return self.expression.compile(ncs, root, block)
        return DynamicDataType.VOID


class WhileLoopBlock(Statement):
    def __init__(self, condition: Expression, block: CodeBlock):
        super().__init__()
        self.condition: Expression = condition
        self.block: CodeBlock = block

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        return_instruction: NCSInstruction,
        break_instruction: NCSInstruction | None,
        continue_instruction: NCSInstruction | None,
    ):
        # Tell break/continue statements to stop here when getting scope size
        block.mark_break_scope()

        loopstart = ncs.add(NCSInstructionType.NOP, args=[])
        loopend = NCSInstruction(NCSInstructionType.NOP, args=[])
        condition_type = self.condition.compile(ncs, root, block)

        if condition_type != DynamicDataType.INT:
            msg = (
                f"Loop condition must be integer type, got {condition_type.builtin.name.lower()}\n"
                f"  Note: Conditions must evaluate to int (0 = false, non-zero = true)"
            )
            raise CompileError(msg)

        ncs.add(NCSInstructionType.JZ, jump=loopend)
        self.block.compile(ncs, root, block, return_instruction, loopend, loopstart)
        ncs.add(NCSInstructionType.JMP, jump=loopstart)

        ncs.instructions.append(loopend)


class DoWhileLoopBlock(Statement):
    def __init__(self, condition: Expression, block: CodeBlock):
        super().__init__()
        self.condition: Expression = condition
        self.block: CodeBlock = block

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        return_instruction: NCSInstruction,
        break_instruction: NCSInstruction | None,
        continue_instruction: NCSInstruction | None,
    ):
        # Tell break/continue statements to stop here when getting scope size
        block.mark_break_scope()

        loopstart = ncs.add(NCSInstructionType.NOP, args=[])
        conditionstart = NCSInstruction(NCSInstructionType.NOP, args=[])
        loopend = NCSInstruction(NCSInstructionType.NOP, args=[])

        self.block.compile(
            ncs,
            root,
            block,
            return_instruction,
            loopend,
            conditionstart,
        )

        ncs.instructions.append(conditionstart)
        condition_type = self.condition.compile(ncs, root, block)
        if condition_type != DynamicDataType.INT:
            msg = (
                f"do-while condition must be integer type, got {condition_type.builtin.name.lower()}\n"
                f"  Note: Conditions must evaluate to int (0 = false, non-zero = true)"
            )
            raise CompileError(msg)

        ncs.add(NCSInstructionType.JZ, jump=loopend)
        ncs.add(NCSInstructionType.JMP, jump=loopstart)
        ncs.instructions.append(loopend)


class ForLoopBlock(Statement):
    def __init__(
        self,
        initial: Expression,
        condition: Expression,
        iteration: Expression,
        block: CodeBlock,
    ):
        super().__init__()
        self.initial: Expression = initial
        self.condition: Expression = condition
        self.iteration: Expression = iteration
        self.block: CodeBlock = block

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        return_instruction: NCSInstruction,
        break_instruction: NCSInstruction | None,
        continue_instruction: NCSInstruction | None,
    ):
        # Tell break/continue statements to stop here when getting scope size
        block.mark_break_scope()

        initial_type = self.initial.compile(ncs, root, block)
        ncs.add(NCSInstructionType.MOVSP, args=[-initial_type.size(root)])

        loopstart = ncs.add(NCSInstructionType.NOP, args=[])
        updatestart = NCSInstruction(NCSInstructionType.NOP, args=[])
        loopend = NCSInstruction(NCSInstructionType.NOP, args=[])

        condition_type = self.condition.compile(ncs, root, block)
        if condition_type != DynamicDataType.INT:
            msg = (
                f"for loop condition must be integer type, got {condition_type.builtin.name.lower()}\n"
                f"  Note: Conditions must evaluate to int (0 = false, non-zero = true)"
            )
            raise CompileError(msg)

        ncs.add(NCSInstructionType.JZ, jump=loopend)
        self.block.compile(ncs, root, block, return_instruction, loopend, updatestart)

        ncs.instructions.append(updatestart)
        iteration_type = self.iteration.compile(ncs, root, block)
        ncs.add(NCSInstructionType.MOVSP, args=[-iteration_type.size(root)])

        ncs.add(NCSInstructionType.JMP, jump=loopstart)
        ncs.instructions.append(loopend)


class ScopedBlock(Statement):
    def __init__(self, block: CodeBlock):
        super().__init__()
        self.block: CodeBlock = block

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        return_instruction: NCSInstruction,
        break_instruction: NCSInstruction | None,
        continue_instruction: NCSInstruction | None,
    ):
        self.block.compile(
            ncs,
            root,
            block,
            return_instruction,
            break_instruction,
            continue_instruction,
        )


# endregion


class BreakStatement(Statement):
    def __init__(self):
        super().__init__()

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        return_instruction: NCSInstruction,
        break_instruction: NCSInstruction | None,
        continue_instruction: NCSInstruction | None,
    ):
        if break_instruction is None:
            msg = (
                "break statement not inside loop or switch\n"
                "  break can only be used inside while, do-while, for, or switch statements"
            )
            raise CompileError(msg)
        ncs.add(NCSInstructionType.MOVSP, args=[-block.break_scope_size(root)])
        ncs.add(NCSInstructionType.JMP, jump=break_instruction)


class ContinueStatement(Statement):
    def __init__(self):
        super().__init__()

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        return_instruction: NCSInstruction,
        break_instruction: NCSInstruction | None,
        continue_instruction: NCSInstruction | None,
    ):
        if continue_instruction is None:
            msg = (
                "continue statement not inside loop\n"
                "  continue can only be used inside while, do-while, or for loops"
            )
            raise CompileError(msg)
        ncs.add(NCSInstructionType.MOVSP, args=[-block.break_scope_size(root)])
        ncs.add(NCSInstructionType.JMP, jump=continue_instruction)


class PrefixIncrementExpression(Expression):
    def __init__(self, field_access: FieldAccess):
        self.field_access: FieldAccess = field_access

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        variable_type = self.field_access.compile(ncs, root, block)

        if variable_type != DynamicDataType.INT:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = (
                f"Increment operator (++) requires integer variable, got {variable_type.builtin.name.lower()}\n"
                f"  Variable: {var_name}"
            )
            raise CompileError(msg)

        isglobal, variable_type, stack_index = self.field_access.get_scoped(block, root)
        ncs.add(NCSInstructionType.INCxSP, args=[-4])

        if isglobal:
            ncs.add(
                NCSInstructionType.CPDOWNBP,
                args=[stack_index, variable_type.size(root)],
            )
        else:
            ncs.add(
                NCSInstructionType.CPDOWNSP,
                args=[stack_index - variable_type.size(root), variable_type.size(root)],
            )

        return variable_type


class PostfixIncrementExpression(Expression):
    def __init__(self, field_access: FieldAccess):
        self.field_access: FieldAccess = field_access

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        variable_type = self.field_access.compile(ncs, root, block)
        block.temp_stack += 4

        if variable_type != DynamicDataType.INT:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = (
                f"Increment operator (++) requires integer variable, got {variable_type.builtin.name.lower()}\n"
                f"  Variable: {var_name}"
            )
            raise CompileError(msg)

        isglobal, variable_type, stack_index = self.field_access.get_scoped(block, root)
        if isglobal:
            ncs.add(NCSInstructionType.INCxBP, args=[stack_index])
        else:
            ncs.add(NCSInstructionType.INCxSP, args=[stack_index])

        block.temp_stack -= 4
        return variable_type


class PrefixDecrementExpression(Expression):
    def __init__(self, field_access: FieldAccess):
        self.field_access: FieldAccess = field_access

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        variable_type = self.field_access.compile(ncs, root, block)

        if variable_type != DynamicDataType.INT:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = (
                f"Decrement operator (--) requires integer variable, got {variable_type.builtin.name.lower()}\n"
                f"  Variable: {var_name}"
            )
            raise CompileError(msg)

        isglobal, variable_type, stack_index = self.field_access.get_scoped(block, root)
        ncs.add(NCSInstructionType.DECxSP, args=[-4])

        if isglobal:
            ncs.add(
                NCSInstructionType.CPDOWNBP,
                args=[stack_index, variable_type.size(root)],
            )
        else:
            ncs.add(
                NCSInstructionType.CPDOWNSP,
                args=[stack_index - variable_type.size(root), variable_type.size(root)],
            )

        return variable_type


class PostfixDecrementExpression(Expression):
    def __init__(self, field_access: FieldAccess):
        self.field_access: FieldAccess = field_access

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        variable_type = self.field_access.compile(ncs, root, block)
        block.temp_stack += 4

        if variable_type != DynamicDataType.INT:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = (
                f"Decrement operator (--) requires integer variable, got {variable_type.builtin.name.lower()}\n"
                f"  Variable: {var_name}"
            )
            raise CompileError(msg)

        isglobal, variable_type, stack_index = self.field_access.get_scoped(block, root)
        if isglobal:
            ncs.add(NCSInstructionType.DECxBP, args=[stack_index])
        else:
            ncs.add(NCSInstructionType.DECxSP, args=[stack_index])

        block.temp_stack -= 4
        return variable_type


# region Switch
class SwitchStatement(Statement):
    def __init__(self, expression: Expression, blocks: list[SwitchBlock]):
        super().__init__()
        self.expression: Expression = expression
        self.blocks: list[SwitchBlock] = blocks

        self.real_block: CodeBlock = CodeBlock()

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        return_instruction: NCSInstruction,
        break_instruction: NCSInstruction | None,
        continue_instruction: NCSInstruction | None,
    ):
        self.real_block._parent = block  # noqa: SLF001
        block.mark_break_scope()

        block = self.real_block

        expression_type = self.expression.compile(ncs, root, block)
        block.temp_stack += expression_type.size(root)

        end_of_switch = NCSInstruction(NCSInstructionType.NOP, args=[])

        tempncs = NCS()
        switchblock_to_instruction = {}
        for switchblock in self.blocks:
            switchblock_start = tempncs.add(NCSInstructionType.NOP, args=[])
            switchblock_to_instruction[switchblock] = switchblock_start
            for statement in switchblock.block:
                statement.compile(
                    tempncs,
                    root,
                    block,
                    return_instruction,
                    end_of_switch,
                    None,
                )

        for switchblock in self.blocks:
            for label in switchblock.labels:
                # Do not want to run switch expression multiple times, execute it once and copy it to the top
                ncs.add(
                    NCSInstructionType.CPTOPSP,
                    args=[-expression_type.size(root), expression_type.size(root)],
                )
                label.compile(
                    ncs,
                    root,
                    block,
                    switchblock_to_instruction[switchblock],
                    expression_type,
                )
        # If none of the labels match, jump over the code block
        ncs.add(NCSInstructionType.JMP, jump=end_of_switch)

        ncs.merge(tempncs)
        ncs.instructions.append(end_of_switch)

        # Pop the Switch expression
        ncs.add(NCSInstructionType.MOVSP, args=[-4])
        block.temp_stack -= expression_type.size(root)


class SwitchBlock:
    def __init__(self, labels: list[SwitchLabel], block: list[Statement]):
        self.labels: list[SwitchLabel] = labels
        self.block: list[Statement] = block


class SwitchLabel(ABC):
    @abstractmethod
    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        jump_to: NCSInstruction,
        expression_type: DynamicDataType,
    ): ...


class ExpressionSwitchLabel:
    def __init__(self, expression: Expression):
        self.expression: Expression = expression

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        jump_to: NCSInstruction,
        expression_type: DynamicDataType,
    ):
        # Compare the copied Switch expression to the Label expression
        label_type = self.expression.compile(ncs, root, block)
        equality_instruction = get_logical_equality_instruction(
            expression_type,
            label_type,
        )
        ncs.add(equality_instruction, args=[])

        # If the expressions match, then we jump to the appropriate place, otherwise continue trying the
        # other Labels
        ncs.add(NCSInstructionType.JNZ, jump=jump_to)


class DefaultSwitchLabel:
    def __init__(self): ...

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        jump_to: NCSInstruction,
        expression_type: DynamicDataType,
    ):
        ncs.add(NCSInstructionType.JMP, jump=jump_to)


# endregion


class DynamicDataType:
    INT: DynamicDataType
    STRING: DynamicDataType
    FLOAT: DynamicDataType
    OBJECT: DynamicDataType
    VECTOR: DynamicDataType
    EVENT: DynamicDataType
    TALENT: DynamicDataType
    LOCATION: DynamicDataType
    EFFECT: DynamicDataType
    VOID: DynamicDataType

    def __init__(self, datatype: DataType, struct_name: str | None = None):
        self.builtin: DataType = datatype
        self._struct: str | None = struct_name

    def __eq__(self, other: DynamicDataType | DataType | object) -> bool:
        if self is other:
            return True
        if isinstance(other, DynamicDataType):
            if self.builtin == other.builtin:
                return self.builtin != DataType.STRUCT or (
                    self.builtin == DataType.STRUCT and self._struct == other._struct
                )
            return False
        if isinstance(other, DataType):
            return self.builtin == other and self.builtin != DataType.STRUCT
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.builtin) ^ hash(self._struct)

    def __repr__(self) -> str:
        return f"DynamicDataType(builtin={self.builtin}({self.builtin.name.lower()}), struct={self._struct})"

    def size(self, root: CodeRoot) -> int:
        if self.builtin == DataType.STRUCT:
            if self._struct is None:
                raise CompileError("Struct type has no name")  # noqa: B904
            return root.struct_map[self._struct].size(root)
        return self.builtin.size()


DynamicDataType.INT = DynamicDataType(DataType.INT)
DynamicDataType.STRING = DynamicDataType(DataType.STRING)
DynamicDataType.FLOAT = DynamicDataType(DataType.FLOAT)
DynamicDataType.OBJECT = DynamicDataType(DataType.OBJECT)
DynamicDataType.VECTOR = DynamicDataType(DataType.VECTOR)
DynamicDataType.VOID = DynamicDataType(DataType.VOID)
DynamicDataType.EVENT = DynamicDataType(DataType.EVENT)
DynamicDataType.TALENT = DynamicDataType(DataType.TALENT)
DynamicDataType.LOCATION = DynamicDataType(DataType.LOCATION)
DynamicDataType.EFFECT = DynamicDataType(DataType.EFFECT)
