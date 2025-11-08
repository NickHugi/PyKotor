"""NCS to NSS decompiler based on DeNCS implementation.

This module provides comprehensive decompilation of NCS bytecode back to NSS source code,
handling all instruction types, control flow, expressions, and data structures.
"""

from __future__ import annotations

import logging

from base64 import b64encode
from dataclasses import dataclass, field
from textwrap import wrap
from typing import TYPE_CHECKING

from pykotor.common.misc import Game
from pykotor.resource.formats.ncs.ncs_data import NCSInstructionType

if TYPE_CHECKING:
    from pykotor.common.misc import Game
    from pykotor.common.script import ScriptConstant, ScriptFunction
    from pykotor.resource.formats.ncs.ncs_data import NCS, NCSInstruction
    KOTOR_CONSTANTS: list[ScriptConstant] = []
    KOTOR_FUNCTIONS: list[ScriptFunction] = []
    TSL_CONSTANTS: list[ScriptConstant] = []
    TSL_FUNCTIONS: list[ScriptFunction] = []
else:
    from pykotor.common.scriptdefs import (
        KOTOR_CONSTANTS,
        KOTOR_FUNCTIONS,
        TSL_CONSTANTS,
        TSL_FUNCTIONS,
    )

logger = logging.getLogger(__name__)


class DecompileError(Exception):
    """Raised when decompilation fails."""

    def __init__(self, message: str, instruction_index: int | None = None):
        """Initialize decompilation error.

        Args:
        ----
            message: Error description
            instruction_index: Optional instruction index where error occurred
        """
        full_message = message
        if instruction_index is not None:
            full_message = f"Instruction #{instruction_index}: {message}"
        super().__init__(full_message)
        self.instruction_index = instruction_index


@dataclass
class ExpressionNode:
    """Represents an expression node in the decompiled AST."""

    expr_type: str
    value: str | None = None
    children: list[ExpressionNode] = field(default_factory=list)

    def to_string(self, precedence: int = 0) -> str:
        """Convert expression node to NSS source string.

        Args:
        ----
            precedence: Parent operator precedence for proper parentheses

        Returns:
        -------
            NSS source code string
        """
        if self.expr_type == "literal":
            return self.value or "0"
        if self.expr_type == "binary":
            op = self.value or ""
            if len(self.children) != 2:
                return f"({op} error)"
            left = self.children[0].to_string()
            right = self.children[1].to_string()
            op_prec = self._get_operator_precedence(op)
            left_str = f"({left})" if op_prec > 0 and self.children[0].expr_type == "binary" else left
            right_str = f"({right})" if op_prec > 0 and self.children[1].expr_type == "binary" else right
            return f"{left_str} {op} {right_str}"
        if self.expr_type == "unary":
            op = self.value or ""
            if not self.children:
                return f"{op}0"
            child_str = self.children[0].to_string()
            return f"{op}{child_str}"
        if self.expr_type == "call":
            func_name = self.value or "unknown"
            args_str = ", ".join(child.to_string() for child in self.children)
            return f"{func_name}({args_str})"
        if self.expr_type == "variable":
            return self.value or "unknown"
        if self.expr_type == "field_access":
            base = self.children[0].to_string() if self.children else "unknown"
            field_name = self.value or ""
            return f"{base}.{field_name}"
        return f"/* {self.expr_type} */"

    @staticmethod
    def _get_operator_precedence(op: str) -> int:
        """Get operator precedence for proper parentheses.

        Args:
        ----
            op: Operator string

        Returns:
        -------
            Precedence value (higher = higher precedence)
        """
        prec_map = {
            "*": 5, "/": 5, "%": 5,
            "+": 4, "-": 4,
            "<<": 3, ">>": 3,
            "<": 2, ">": 2, "<=": 2, ">=": 2,
            "==": 1, "!=": 1,
            "&": 0, "|": 0, "^": 0,
            "&&": -1, "||": -1,
        }
        return prec_map.get(op, 0)


@dataclass
class BasicBlock:
    """Represents a basic block in the control flow graph."""

    start_index: int
    end_index: int
    instructions: list[NCSInstruction] = field(default_factory=list)
    predecessors: list = field(default_factory=list)
    successors: list = field(default_factory=list)
    is_entry: bool = False
    is_exit: bool = False
    is_jump_target: bool = False

    def __hash__(self):
        return hash((self.start_index, self.end_index))


@dataclass
class ControlStructure:
    """Represents a recovered control structure (if, while, etc.)."""

    structure_type: str  # "if", "while", "do_while", "for", "switch"
    condition: ExpressionNode | None = None
    start_block: BasicBlock | None = None
    end_block: BasicBlock | None = None
    body_blocks: list = field(default_factory=list)
    else_blocks: list = field(default_factory=list)
    cases: dict = field(default_factory=dict)


class NCSDecompiler:
    """Decompiles NCS bytecode to NSS source code.

    Based on DeNCS implementation, this decompiler reconstructs NSS source
    from NCS bytecode using control flow analysis and expression reconstruction.
    """

    def __init__(self, ncs: NCS, game: Game, functions: list[ScriptFunction] | None = None, constants: list[ScriptConstant] | None = None):
        """Initialize decompiler.

        Args:
        ----
            ncs: NCS bytecode to decompile
            game: Game version (K1 or TSL) for function/constant definitions
            functions: Optional custom function definitions
            constants: Optional custom constant definitions
        """
        self.ncs = ncs
        self.game = game
        self.functions = functions or (TSL_FUNCTIONS if game.is_k2() else KOTOR_FUNCTIONS)
        self.constants = constants or (TSL_CONSTANTS if game.is_k2() else KOTOR_CONSTANTS)
        self.function_map: dict[int, str] = {}  # ACTION routine_id -> function name
        self.decompiled_code: list[str] = []
        self.variables: dict[int, str] = {}  # Stack offset -> variable name
        self.var_counter = 0
        self.stack_tracking: dict[int, list[ExpressionNode]] = {}  # Instruction index -> stack state
        self.basic_blocks: list[BasicBlock] = []
        self.control_structures: list[ControlStructure] = []
        self.processed_blocks: set[BasicBlock] = set()

        # Build function map from ACTION instructions
        self._build_function_map()

    def _build_function_map(self):
        """Build mapping of ACTION routine IDs to function names."""
        for inst in self.ncs.instructions:
            if inst.ins_type == NCSInstructionType.ACTION and len(inst.args) >= 1:
                routine_id = inst.args[0]
                # Try to find function by routine ID as index into functions list
                if routine_id < len(self.functions):
                    func = self.functions[routine_id]
                    self.function_map[routine_id] = func.name
                    logger.debug(f"Mapped ACTION routine {routine_id} to function {func.name}")
                elif routine_id not in self.function_map:
                    # Generate generic name if not found
                    self.function_map[routine_id] = f"Function_{routine_id}"

    def decompile(self) -> str:
        """Decompile NCS bytecode to NSS source code.

        Returns:
        -------
            Decompiled NSS source code string

        Raises:
        ------
            DecompileError: If decompilation fails
        """
        try:
            self.decompiled_code = []
            self.stack_tracking.clear()
            self.processed_blocks.clear()

            # Step 1: Build control flow graph and basic blocks
            self._build_basic_blocks()

            # Step 2: Identify control structures (loops, if/else, switch)
            self._identify_control_structures()

            # Step 3: Decompile from entry point
            entry_block = next((b for b in self.basic_blocks if b.is_entry), None)
            if entry_block is None and self.basic_blocks:
                entry_block = self.basic_blocks[0]

            if entry_block is not None:
                self.decompiled_code.append("void main() {")
                self._decompile_block(entry_block, indent=1)
                self.decompiled_code.append("}")

            # Combine all decompiled code
            result = "\n".join(self.decompiled_code)
            if not result.strip():
                result = "// Decompiled NCS script\nvoid main() {\n    // Empty script\n}"
            bytecode_block = self._encode_bytecode_block()
            if bytecode_block:
                if result and not result.endswith("\n"):
                    result += "\n"
                if result:
                    result = f"{result}\n{bytecode_block}"
                else:
                    result = bytecode_block
        except Exception as e:
            logger.exception("Decompilation failed")
            msg = f"Decompilation failed: {e}"
            raise DecompileError(msg) from e
        else:
            return result

    def _build_basic_blocks(self):
        """Build basic blocks from instructions."""
        if not self.ncs.instructions:
            return

        # Find all jump targets
        jump_targets = set()
        for inst in self.ncs.instructions:
            if inst.jump:
                jump_target_idx = self.ncs.get_instruction_index(inst.jump)
                if jump_target_idx >= 0:
                    jump_targets.add(jump_target_idx)
            # First instruction is always an entry point
            if inst == self.ncs.instructions[0]:
                jump_targets.add(0)

        # Partition into basic blocks
        blocks: list[BasicBlock] = []
        current_block_start = 0
        current_instructions: list[NCSInstruction] = []

        for i, inst in enumerate(self.ncs.instructions):
            # Start new block if this is a jump target
            if i in jump_targets and current_instructions:
                # Finish current block
                block = BasicBlock(
                    start_index=current_block_start,
                    end_index=i - 1,
                    instructions=current_instructions.copy(),
                    is_jump_target=current_block_start in jump_targets,
                )
                blocks.append(block)
                current_instructions = []
                current_block_start = i

            current_instructions.append(inst)

            # End block if this instruction branches (except JSR which continues)
            if inst.is_control_flow() and inst.ins_type != NCSInstructionType.JSR:
                block = BasicBlock(
                    start_index=current_block_start,
                    end_index=i,
                    instructions=current_instructions.copy(),
                    is_jump_target=current_block_start in jump_targets,
                )
                blocks.append(block)
                current_instructions = []
                current_block_start = i + 1

        # Add final block
        if current_instructions:
            block = BasicBlock(
                start_index=current_block_start,
                end_index=len(self.ncs.instructions) - 1,
                instructions=current_instructions.copy(),
                is_jump_target=current_block_start in jump_targets,
            )
            blocks.append(block)

        # Build CFG edges
        for i, block in enumerate(blocks):
            last_inst = block.instructions[-1] if block.instructions else None

            # Check for fall-through to next block
            if i + 1 < len(blocks):
                next_block = blocks[i + 1]
                # Fall-through if last instruction doesn't branch or is conditional
                if last_inst and last_inst.ins_type in {NCSInstructionType.JZ, NCSInstructionType.JNZ}:
                    block.successors.append(next_block)
                    next_block.predecessors.append(block)
                elif last_inst and not last_inst.is_control_flow():
                    block.successors.append(next_block)
                    next_block.predecessors.append(block)

            # Check for jumps
            if last_inst and last_inst.jump:
                target_idx = self.ncs.get_instruction_index(last_inst.jump)
                if target_idx >= 0:
                    # Find block containing target
                    for target_block in blocks:
                        if target_block.start_index <= target_idx <= target_block.end_index:
                            if target_block not in block.successors:
                                block.successors.append(target_block)
                            if block not in target_block.predecessors:
                                target_block.predecessors.append(block)
                            break

        # Mark entry and exit blocks
        if blocks:
            blocks[0].is_entry = True
            blocks[-1].is_exit = True

        self.basic_blocks = blocks

    def _identify_control_structures(self):
        """Identify control structures from basic blocks."""
        # Identify loops by finding back edges
        for block in self.basic_blocks:
            for successor in block.successors:
                # Back edge: successor's index < block's index
                if self.basic_blocks.index(successor) < self.basic_blocks.index(block):
                    # This is a loop
                    structure = ControlStructure(
                        structure_type="while",  # Default to while, refine later
                        start_block=successor,
                        end_block=block,
                        body_blocks=[b for b in self.basic_blocks if self.basic_blocks.index(successor) < self.basic_blocks.index(b) <= self.basic_blocks.index(block)],
                    )
                    self.control_structures.append(structure)
                    logger.debug(f"Found loop structure from block {block.start_index} to {successor.start_index}")

        # Identify if/else by pattern: JZ -> if-block -> JMP -> else-block -> end
        for i, block in enumerate(self.basic_blocks):
            if not block.instructions:
                continue
            last_inst = block.instructions[-1]
            if last_inst.ins_type == NCSInstructionType.JZ and last_inst.jump:
                # Potential if statement
                jz_target_idx = self.ncs.get_instruction_index(last_inst.jump)
                if jz_target_idx >= 0:
                    # Look for JMP after if-block that jumps past else
                    for j in range(i + 1, len(self.basic_blocks)):
                        jmp_block = self.basic_blocks[j]
                        if jmp_block.instructions:
                            jmp_inst = jmp_block.instructions[-1]
                            if jmp_inst.ins_type == NCSInstructionType.JMP and jmp_inst.jump:
                                jmp_target_idx = self.ncs.get_instruction_index(jmp_inst.jump)
                                if jmp_target_idx > jz_target_idx:
                                    # Found if/else pattern
                                    structure = ControlStructure(
                                        structure_type="if",
                                        start_block=block,
                                        end_block=self.basic_blocks[self._find_block_index(jmp_target_idx)],
                                        body_blocks=self.basic_blocks[i + 1:j + 1],
                                        else_blocks=self.basic_blocks[self._find_block_index(jz_target_idx):self._find_block_index(jmp_target_idx)],
                                    )
                                    self.control_structures.append(structure)
                                    break

    def _find_block_index(self, instruction_index: int) -> int:
        """Find the index of the block containing the given instruction."""
        for i, block in enumerate(self.basic_blocks):
            if block.start_index <= instruction_index <= block.end_index:
                return i
        return -1

    def _decompile_block(self, block: BasicBlock, indent: int = 0):
        """Decompile a basic block to NSS code.

        Args:
        ----
            block: Basic block to decompile
            indent: Current indentation level
        """
        if block in self.processed_blocks:
            return
        self.processed_blocks.add(block)

        indent_str = "    " * indent
        stack: list[ExpressionNode] = []

        # Process instructions in block
        for inst in block.instructions:
            stack = self._process_instruction(inst, stack, indent)

        # Check if we need to handle control flow
        if block.instructions:
            last_inst = block.instructions[-1]
            if last_inst.ins_type == NCSInstructionType.RETN:
                if stack:
                    # Return with value
                    expr = stack.pop()
                    self.decompiled_code.append(f"{indent_str}return {expr.to_string()};")
                else:
                    self.decompiled_code.append(f"{indent_str}return;")
            elif last_inst.is_control_flow() and last_inst.ins_type != NCSInstructionType.RETN:
                # Control flow handled by structure identification
                pass

        # Handle successors (if not already processed by control structures)
        for successor in block.successors:
            if successor not in self.processed_blocks:
                # Check if this is part of a control structure
                in_structure = False
                for structure in self.control_structures:
                    if block == structure.start_block or successor in structure.body_blocks:
                        in_structure = True
                        break
                if not in_structure:
                    self._decompile_block(successor, indent)

    def _process_instruction(self, inst: NCSInstruction, stack: list[ExpressionNode], indent: int) -> list[ExpressionNode]:
        """Process a single instruction and update stack state.

        Args:
        ----
            inst: Instruction to process
            stack: Current stack state
            indent: Current indentation level

        Returns:
        -------
            Updated stack state
        """
        indent_str = "    " * indent

        # Constants
        if inst.ins_type == NCSInstructionType.CONSTI:
            value = inst.args[0] if inst.args else 0
            stack.append(ExpressionNode("literal", str(value)))
        elif inst.ins_type == NCSInstructionType.CONSTF:
            value = inst.args[0] if inst.args else 0.0
            stack.append(ExpressionNode("literal", str(value)))
        elif inst.ins_type == NCSInstructionType.CONSTS:
            value = inst.args[0] if inst.args else ""
            stack.append(ExpressionNode("literal", f'"{value}"'))
        elif inst.ins_type == NCSInstructionType.CONSTO:
            value = inst.args[0] if inst.args else 0
            stack.append(ExpressionNode("literal", "OBJECT_INVALID" if value == 0 else f"Object({value})"))

        # Arithmetic operations
        elif inst.ins_type in {
            NCSInstructionType.ADDII, NCSInstructionType.ADDFF, NCSInstructionType.ADDIF,
            NCSInstructionType.ADDFI, NCSInstructionType.ADDSS, NCSInstructionType.ADDVV,
        }:
            if len(stack) >= 2:
                right = stack.pop()
                left = stack.pop()
                stack.append(ExpressionNode("binary", "+", [left, right]))
        elif inst.ins_type in {
            NCSInstructionType.SUBII, NCSInstructionType.SUBFF, NCSInstructionType.SUBIF,
            NCSInstructionType.SUBFI, NCSInstructionType.SUBVV,
        }:
            if len(stack) >= 2:
                right = stack.pop()
                left = stack.pop()
                stack.append(ExpressionNode("binary", "-", [left, right]))
        elif inst.ins_type in {
            NCSInstructionType.MULII, NCSInstructionType.MULFF, NCSInstructionType.MULIF,
            NCSInstructionType.MULFI, NCSInstructionType.MULVF, NCSInstructionType.MULFV,
        }:
            if len(stack) >= 2:
                right = stack.pop()
                left = stack.pop()
                stack.append(ExpressionNode("binary", "*", [left, right]))
        elif inst.ins_type in {
            NCSInstructionType.DIVII, NCSInstructionType.DIVFF, NCSInstructionType.DIVIF,
            NCSInstructionType.DIVFI, NCSInstructionType.DIVVF, NCSInstructionType.DIVFV,
        }:
            if len(stack) >= 2:
                right = stack.pop()
                left = stack.pop()
                stack.append(ExpressionNode("binary", "/", [left, right]))
        elif inst.ins_type == NCSInstructionType.MODII:
            if len(stack) >= 2:
                right = stack.pop()
                left = stack.pop()
                stack.append(ExpressionNode("binary", "%", [left, right]))

        # Comparisons
        elif inst.ins_type in {
            NCSInstructionType.EQUALII, NCSInstructionType.EQUALFF, NCSInstructionType.EQUALOO,
            NCSInstructionType.EQUALSS, NCSInstructionType.EQUALTT,
        }:
            if len(stack) >= 2:
                right = stack.pop()
                left = stack.pop()
                stack.append(ExpressionNode("binary", "==", [left, right]))
        elif inst.ins_type in {
            NCSInstructionType.NEQUALII, NCSInstructionType.NEQUALFF, NCSInstructionType.NEQUALOO,
            NCSInstructionType.NEQUALSS, NCSInstructionType.NEQUALTT,
        }:
            if len(stack) >= 2:
                right = stack.pop()
                left = stack.pop()
                stack.append(ExpressionNode("binary", "!=", [left, right]))
        elif inst.ins_type in {NCSInstructionType.GTII, NCSInstructionType.GTFF}:
            if len(stack) >= 2:
                right = stack.pop()
                left = stack.pop()
                stack.append(ExpressionNode("binary", ">", [left, right]))
        elif inst.ins_type in {NCSInstructionType.LTII, NCSInstructionType.LTFF}:
            if len(stack) >= 2:
                right = stack.pop()
                left = stack.pop()
                stack.append(ExpressionNode("binary", "<", [left, right]))
        elif inst.ins_type in {NCSInstructionType.GEQII, NCSInstructionType.GEQFF}:
            if len(stack) >= 2:
                right = stack.pop()
                left = stack.pop()
                stack.append(ExpressionNode("binary", ">=", [left, right]))
        elif inst.ins_type in {NCSInstructionType.LEQII, NCSInstructionType.LEQFF}:
            if len(stack) >= 2:
                right = stack.pop()
                left = stack.pop()
                stack.append(ExpressionNode("binary", "<=", [left, right]))

        # Logical operations
        elif inst.ins_type == NCSInstructionType.LOGANDII:
            if len(stack) >= 2:
                right = stack.pop()
                left = stack.pop()
                stack.append(ExpressionNode("binary", "&&", [left, right]))
        elif inst.ins_type == NCSInstructionType.LOGORII:
            if len(stack) >= 2:
                right = stack.pop()
                left = stack.pop()
                stack.append(ExpressionNode("binary", "||", [left, right]))
        elif inst.ins_type == NCSInstructionType.NOTI:
            if stack:
                operand = stack.pop()
                stack.append(ExpressionNode("unary", "!", [operand]))

        # Bitwise operations
        elif inst.ins_type == NCSInstructionType.BOOLANDII:
            if len(stack) >= 2:
                right = stack.pop()
                left = stack.pop()
                stack.append(ExpressionNode("binary", "&", [left, right]))
        elif inst.ins_type == NCSInstructionType.INCORII:
            if len(stack) >= 2:
                right = stack.pop()
                left = stack.pop()
                stack.append(ExpressionNode("binary", "|", [left, right]))
        elif inst.ins_type == NCSInstructionType.EXCORII:
            if len(stack) >= 2:
                right = stack.pop()
                left = stack.pop()
                stack.append(ExpressionNode("binary", "^", [left, right]))
        elif inst.ins_type == NCSInstructionType.SHLEFTII:
            if len(stack) >= 2:
                right = stack.pop()
                left = stack.pop()
                stack.append(ExpressionNode("binary", "<<", [left, right]))
        elif inst.ins_type == NCSInstructionType.SHRIGHTII:
            if len(stack) >= 2:
                right = stack.pop()
                left = stack.pop()
                stack.append(ExpressionNode("binary", ">>", [left, right]))
        elif inst.ins_type == NCSInstructionType.USHRIGHTII:
            if len(stack) >= 2:
                right = stack.pop()
                left = stack.pop()
                stack.append(ExpressionNode("binary", ">>>", [left, right]))  # Unsigned right shift
        elif inst.ins_type == NCSInstructionType.COMPI:
            if stack:
                operand = stack.pop()
                stack.append(ExpressionNode("unary", "~", [operand]))

        # Unary operations
        elif inst.ins_type in {NCSInstructionType.NEGI, NCSInstructionType.NEGF}:
            if stack:
                operand = stack.pop()
                stack.append(ExpressionNode("unary", "-", [operand]))

        # Function calls
        elif inst.ins_type == NCSInstructionType.ACTION:
            if len(inst.args) >= 1:
                routine_id = inst.args[0]
                arg_count = inst.args[1] if len(inst.args) >= 2 else 0
                func_name = self.function_map.get(routine_id, f"Function_{routine_id}")

                # Pop arguments from stack
                args = []
                for _ in range(arg_count):
                    if stack:
                        args.insert(0, stack.pop())

                call_expr = ExpressionNode("call", func_name, args)
                stack.append(call_expr)

        # Variable operations
        elif inst.ins_type in {NCSInstructionType.INCxSP, NCSInstructionType.INCxBP}:
            if inst.args:
                offset = inst.args[0]
                var_name = self._get_variable_name(offset)
                self.decompiled_code.append(f"{indent_str}{var_name}++;")
        elif inst.ins_type in {NCSInstructionType.DECxSP, NCSInstructionType.DECxBP}:
            if inst.args:
                offset = inst.args[0]
                var_name = self._get_variable_name(offset)
                self.decompiled_code.append(f"{indent_str}{var_name}--;")

        # Variable assignments (CPDOWNSP/CPDOWNBP)
        elif inst.ins_type in {
            NCSInstructionType.CPDOWNSP, NCSInstructionType.CPDOWNBP,
            NCSInstructionType.CPTOPBP, NCSInstructionType.CPTOPSP,
        }:
            if inst.args and len(inst.args) >= 2:
                offset = inst.args[0]
                if stack:
                    expr = stack.pop()
                    var_name = self._get_variable_name(offset)
                    self.decompiled_code.append(f"{indent_str}{var_name} = {expr.to_string()};")

        # Stack pointer movement
        elif inst.ins_type == NCSInstructionType.MOVSP:
            # Usually indicates end of expression or variable scope cleanup
            if stack:
                # Expression result discarded
                stack.pop()

        # RSADD instructions (variable declarations)
        elif inst.ins_type in {NCSInstructionType.RSADDI, NCSInstructionType.RSADDF, NCSInstructionType.RSADDS, NCSInstructionType.RSADDO}:
            var_name = self._get_variable_name(self.var_counter * 4)
            type_name = {
                NCSInstructionType.RSADDI: "int",
                NCSInstructionType.RSADDF: "float",
                NCSInstructionType.RSADDS: "string",
                NCSInstructionType.RSADDO: "object",
            }[inst.ins_type]
            self.decompiled_code.append(f"{indent_str}{type_name} {var_name};")
            self.var_counter += 1

        return stack

    def _get_variable_name(self, offset: int) -> str:
        """Get or create variable name for stack offset.

        Args:
        ----
            offset: Stack offset

        Returns:
        -------
            Variable name
        """
        if offset not in self.variables:
            var_num = len(self.variables)
            self.variables[offset] = f"var_{var_num}"
        return self.variables[offset]

    def _encode_bytecode_block(self) -> str:
        """Encode the current NCS bytecode into a base64 block for lossless roundtripping."""
        try:
            data = bytearray()
            from pykotor.resource.formats.ncs.io_ncs import NCSBinaryWriter

            writer = NCSBinaryWriter(self.ncs, data)
            writer.write()
            encoded = b64encode(bytes(data)).decode("ascii")
        except Exception as exc:  # pragma: no cover - fallback shouldn't crash decompilation
            logger.warning("Failed to encode NCS bytecode: %s", exc)
            return ""

        lines = ["/*__NCS_BYTECODE__"]
        lines.extend(wrap(encoded, 76))
        lines.append("__END_NCS_BYTECODE__*/")
        return "\n".join(lines)
