from __future__ import annotations

import struct

from copy import copy
from inspect import signature
from typing import TYPE_CHECKING, Any, NamedTuple

from pykotor.common.geometry import Vector3
from pykotor.common.script import DataType
from pykotor.common.scriptdefs import KOTOR_FUNCTIONS
from pykotor.resource.formats.ncs import NCSInstruction, NCSInstructionType

if TYPE_CHECKING:
    from collections.abc import Callable

    from pykotor.common.script import ScriptFunction
    from pykotor.resource.formats.ncs import NCS


class Interpreter:
    """This class is not used in the compiling process. This is only partially implemented, mostly for testing purposes."""

    def __init__(self, ncs: NCS):
        self._ncs: NCS = ncs
        self._cursor: NCSInstruction = ncs.instructions[0]
        self._functions: list[ScriptFunction] = KOTOR_FUNCTIONS

        self._stack: Stack = Stack()
        self._returns: list[NCSInstruction | None] = [None]

        self._mocks: dict[str, Callable] = {}

        self.stack_snapshots: list[StackSnapshot] = []
        self.action_snapshots: list[ActionSnapshot] = []

    def run(self):
        # TODO - limit how many instructions can be run before raising an error
        while self._cursor is not None:
            index = self._ncs.instructions.index(self._cursor)
            jump_value = None

            # print(str(index).ljust(3), str(self._cursor).ljust(40)[:40], str(self._stack.state()).ljust(30), f"BP={self._stack.base_pointer()//4}")

            if self._cursor.ins_type == NCSInstructionType.CONSTS:
                self._stack.add(DataType.STRING, self._cursor.args[0])

            elif self._cursor.ins_type == NCSInstructionType.CONSTI:
                self._stack.add(DataType.INT, self._cursor.args[0])

            elif self._cursor.ins_type == NCSInstructionType.CONSTF:
                self._stack.add(DataType.FLOAT, self._cursor.args[0])

            elif self._cursor.ins_type == NCSInstructionType.CONSTO:
                self._stack.add(DataType.OBJECT, self._cursor.args[0])

            elif self._cursor.ins_type == NCSInstructionType.CPTOPSP:
                self._stack.copy_to_top(self._cursor.args[0], self._cursor.args[1])

            elif self._cursor.ins_type == NCSInstructionType.CPDOWNSP:
                self._stack.copy_down(self._cursor.args[0], self._cursor.args[1])

            elif self._cursor.ins_type == NCSInstructionType.ACTION:
                self.do_action(
                    self._functions[self._cursor.args[0]],
                    self._cursor.args[1],
                )

            elif self._cursor.ins_type == NCSInstructionType.MOVSP:
                self._stack.move(self._cursor.args[0])

            elif self._cursor.ins_type in {
                NCSInstructionType.ADDII,
                NCSInstructionType.ADDIF,
                NCSInstructionType.ADDFF,
                NCSInstructionType.ADDFI,
                NCSInstructionType.ADDSS,
                NCSInstructionType.ADDVV,
            }:
                self._stack.addition_op()

            elif self._cursor.ins_type in {
                NCSInstructionType.SUBII,
                NCSInstructionType.SUBIF,
                NCSInstructionType.SUBFF,
                NCSInstructionType.SUBFI,
                NCSInstructionType.SUBVV,
            }:
                self._stack.subtraction_op()

            elif self._cursor.ins_type in {
                NCSInstructionType.MULII,
                NCSInstructionType.MULIF,
                NCSInstructionType.MULFF,
                NCSInstructionType.MULFI,
                NCSInstructionType.MULVF,
                NCSInstructionType.MULFV,
            }:
                self._stack.multiplication_op()

            elif self._cursor.ins_type in {
                NCSInstructionType.DIVII,
                NCSInstructionType.DIVIF,
                NCSInstructionType.DIVFF,
                NCSInstructionType.DIVFI,
                NCSInstructionType.DIVVF,
            }:
                self._stack.division_op()

            elif self._cursor.ins_type == NCSInstructionType.MODII:
                self._stack.modulus_op()

            elif self._cursor.ins_type in {
                NCSInstructionType.NEGI,
                NCSInstructionType.NEGF,
            }:
                self._stack.negation_op()

            elif self._cursor.ins_type == NCSInstructionType.COMPI:
                self._stack.bitwise_not_op()

            elif self._cursor.ins_type == NCSInstructionType.NOTI:
                self._stack.logical_not_op()

            elif self._cursor.ins_type == NCSInstructionType.LOGANDII:
                self._stack.logical_and_op()

            elif self._cursor.ins_type == NCSInstructionType.LOGORII:
                self._stack.logical_or_op()

            elif self._cursor.ins_type == NCSInstructionType.INCORII:
                self._stack.bitwise_or_op()

            elif self._cursor.ins_type == NCSInstructionType.EXCORII:
                self._stack.bitwise_xor_op()

            elif self._cursor.ins_type == NCSInstructionType.BOOLANDII:
                self._stack.bitwise_and_op()

            elif self._cursor.ins_type in {
                NCSInstructionType.EQUALII,
                NCSInstructionType.EQUALFF,
                NCSInstructionType.EQUALSS,
                NCSInstructionType.EQUALOO,
            }:
                self._stack.logical_equality_op()

            elif self._cursor.ins_type in {
                NCSInstructionType.NEQUALII,
                NCSInstructionType.NEQUALFF,
                NCSInstructionType.NEQUALSS,
                NCSInstructionType.NEQUALOO,
            }:
                self._stack.logical_inequality_op()

            elif self._cursor.ins_type in {
                NCSInstructionType.GTII,
                NCSInstructionType.GTFF,
            }:
                self._stack.compare_greaterthan_op()

            elif self._cursor.ins_type in {
                NCSInstructionType.GEQII,
                NCSInstructionType.GEQFF,
            }:
                self._stack.compare_greaterthanorequal_op()

            elif self._cursor.ins_type in {
                NCSInstructionType.LTII,
                NCSInstructionType.LTFF,
            }:
                self._stack.compare_lessthan_op()

            elif self._cursor.ins_type in {
                NCSInstructionType.LEQII,
                NCSInstructionType.LEQFF,
            }:
                self._stack.compare_lessthanorequal_op()

            elif self._cursor.ins_type == NCSInstructionType.SHLEFTII:
                self._stack.bitwise_leftshift_op()

            elif self._cursor.ins_type == NCSInstructionType.SHRIGHTII:
                self._stack.bitwise_rightshift_op()

            elif self._cursor.ins_type == NCSInstructionType.INCIBP:
                self._stack.increment_bp(self._cursor.args[0])

            elif self._cursor.ins_type == NCSInstructionType.DECIBP:
                self._stack.decrement_bp(self._cursor.args[0])

            elif self._cursor.ins_type == NCSInstructionType.INCISP:
                self._stack.increment(self._cursor.args[0])

            elif self._cursor.ins_type == NCSInstructionType.DECISP:
                self._stack.decrement(self._cursor.args[0])

            elif self._cursor.ins_type == NCSInstructionType.RSADDI:
                self._stack.add(DataType.INT, 0)

            elif self._cursor.ins_type == NCSInstructionType.RSADDF:
                self._stack.add(DataType.FLOAT, 0)

            elif self._cursor.ins_type == NCSInstructionType.RSADDS:
                self._stack.add(DataType.STRING, "")

            elif self._cursor.ins_type == NCSInstructionType.RSADDO:
                self._stack.add(DataType.OBJECT, 1)

            elif self._cursor.ins_type == NCSInstructionType.RSADDEFF:
                self._stack.add(DataType.EFFECT, 0)

            elif self._cursor.ins_type == NCSInstructionType.RSADDTAL:
                self._stack.add(DataType.TALENT, 0)

            elif self._cursor.ins_type == NCSInstructionType.RSADDLOC:
                self._stack.add(DataType.LOCATION, 0)

            elif self._cursor.ins_type == NCSInstructionType.RSADDEVT:
                self._stack.add(DataType.EVENT, 0)

            elif self._cursor.ins_type == NCSInstructionType.SAVEBP:
                self._stack.save_bp()

            elif self._cursor.ins_type == NCSInstructionType.RESTOREBP:
                self._stack.restore_bp()

            elif self._cursor.ins_type == NCSInstructionType.CPTOPBP:
                self._stack.copy_top_bp(self._cursor.args[0], self._cursor.args[1])

            elif self._cursor.ins_type == NCSInstructionType.CPDOWNBP:
                self._stack.copy_down_bp(self._cursor.args[0], self._cursor.args[1])

            elif self._cursor.ins_type == NCSInstructionType.JSR:
                index_return_to = self._ncs.instructions.index(self._cursor) + 1
                return_to: NCSInstruction | None = self._ncs.instructions[index_return_to]
                self._returns.append(return_to)

            elif self._cursor.ins_type in {
                NCSInstructionType.JZ,
                NCSInstructionType.JNZ,
            }:
                jump_value = self._stack.pop()

            elif self._cursor.ins_type == NCSInstructionType.STORE_STATE:
                self.store_state()

            self.stack_snapshots.append(
                StackSnapshot(self._cursor, self._stack.state()),
            )

            # Control flow handling
            if self._cursor.ins_type == NCSInstructionType.RETN:
                return_to = self._returns.pop()
                if return_to is None:
                    msg = f"Return instruction RETN at index {index} has no return target"
                    raise RuntimeError(msg)
                if not isinstance(return_to, NCSInstruction):
                    msg = f"Return instruction RETN at index {index} has no return target"
                    raise RuntimeError(msg)
                self._cursor = return_to
                continue

            if (
                self._cursor.ins_type == NCSInstructionType.JMP
                or (self._cursor.ins_type == NCSInstructionType.JZ and jump_value == 0)
                or (self._cursor.ins_type == NCSInstructionType.JNZ and jump_value != 0)
                or self._cursor.ins_type == NCSInstructionType.JSR
            ):
                if self._cursor.jump is None:
                    msg = f"Jump instruction {self._cursor.ins_type.name} at index {index} has no jump target"
                    raise RuntimeError(msg)
                self._cursor = self._cursor.jump
            else:
                # Move to next instruction
                if index + 1 >= len(self._ncs.instructions):
                    # End of program
                    break
                self._cursor = self._ncs.instructions[index + 1]

    def store_state(self):
        self._stack.store_state()

        index = self._ncs.instructions.index(self._cursor)
        tempcursor = self._ncs.instructions[index + 2]

        block = []
        while tempcursor.ins_type != NCSInstructionType.RETN:
            block.append(tempcursor)
            index = self._ncs.instructions.index(tempcursor)
            tempcursor = self._ncs.instructions[index + 1]

        self._stack.add(DataType.ACTION, ActionStackValue(block, self._stack.state()))

    def do_action(self, function: ScriptFunction, args: int):  # noqa: C901, PLR0912
        """Execute an engine action/function call.

        Args:
        ----
            function: The script function being called
            args: Number of arguments being passed

        Raises:
        ------
            ValueError: If argument count or types don't match function signature
        """
        if args != len(function.params):
            msg = (
                f"Action '{function.name}' called with {args} arguments "
                f"but expects {len(function.params)} parameters"
            )
            raise ValueError(msg)

        args_snap = []

        # Pop arguments from stack in reverse order (last param popped first)
        for i in range(args):
            param_index = args - 1 - i  # Reverse order
            if param_index >= len(function.params):
                msg = f"Action '{function.name}' parameter index {param_index} out of range"
                raise ValueError(msg)

            if function.params[param_index].datatype == DataType.VECTOR:
                # Vectors are three floats on stack (z, y, x order when popping)
                try:
                    z = self._stack.pop().value
                    y = self._stack.pop().value
                    x = self._stack.pop().value
                except IndexError as e:
                    msg = f"Stack underflow while popping vector for '{function.name}'"
                    raise RuntimeError(msg) from e

                vector_object = StackObject(
                    DataType.VECTOR,
                    Vector3(x, y, z),
                )
                args_snap.append(vector_object)
            else:
                try:
                    args_snap.append(self._stack.pop())
                except IndexError as e:
                    msg = f"Stack underflow while popping argument for '{function.name}'"
                    raise RuntimeError(msg) from e

        # Validate argument types
        for i in range(args):
            if function.params[i].datatype != args_snap[i].data_type:
                msg = (
                    f"Action '{function.name}' parameter '{function.params[i].name}' "
                    f"expects type {function.params[i].datatype.name} but got "
                    f"{args_snap[i].data_type.name} with value '{args_snap[i].value}'"
                )
                raise ValueError(msg)

        if function.returntype != DataType.VOID:
            if function.name in self._mocks:
                # Execute and return the value back from the mock
                value = self._mocks[function.name](*[arg.value for arg in args_snap])
            else:
                # Return value of None if no relevant mock is found
                value = None

            if function.returntype == DataType.VECTOR:
                if value is None:
                    self._stack.add(DataType.FLOAT, 0.0)
                    self._stack.add(DataType.FLOAT, 0.0)
                    self._stack.add(DataType.FLOAT, 0.0)
                else:
                    self._stack.add(DataType.FLOAT, value[0])
                    self._stack.add(DataType.FLOAT, value[1])
                    self._stack.add(DataType.FLOAT, value[2])
            else:
                self._stack.add(function.returntype, value)

        self.action_snapshots.append(ActionSnapshot(function.name, args_snap, None))

    def print(self):
        for snap in self.stack_snapshots:
            print(snap.instruction, "\n", snap.stack, "\n")

    def set_mock(self, function_name: str, mock: Callable):
        function = next(
            (
                function
                for function in self._functions
                if function.name == function_name
            ),
            None,
        )

        if function is None:
            msg = f"Function '{function_name}' does not exist."
            raise ValueError(msg)

        mock_param_count = len(signature(mock).parameters)
        routine_param_count = len(function.params)
        if mock_param_count != routine_param_count:
            msg = f"Function '{function_name}' expects {routine_param_count} parameters not {mock_param_count}."
            raise ValueError(msg)

        self._mocks[function_name] = mock

    def remove_mock(self, function_name: str):
        self._mocks.pop(function_name)


class StackV2:
    def __init__(self):
        self._stack: bytearray = bytearray()
        self._base_pointer: int = 0
        self._base_pointer_saved: list[int] = []
        self._stack_types: list[DataType] = []

    def state(self) -> bytearray:
        return copy(self._stack)

    def copy_down(self, offset: int, size: int):
        stacksize = len(self._stack)
        copied = self._stack[stacksize - size : stacksize]
        self._stack[stacksize - offset : stacksize - offset + size] = copied

    def copy_to_top(self, offset: int, size: int):
        stacksize = len(self._stack)
        copied = self._stack[stacksize - offset : stacksize - offset + size]
        self._stack.extend(copied)

    def add(self, datatype: DataType, value: float | str | object):
        """Add a value to the stack with proper type handling.

        Args:
        ----
            datatype: The type of data being added
            value: The value to add

        Raises:
        ------
            ValueError: If value type doesn't match datatype
            NotImplementedError: If datatype is not supported
        """
        if datatype == DataType.INT:
            if not isinstance(value, int):
                msg = f"Expected int value, got {type(value)}"
                raise ValueError(msg)
            self._stack.extend(struct.pack("i", value))
        elif datatype == DataType.FLOAT:
            if not isinstance(value, (int, float)):
                msg = f"Expected numeric value, got {type(value)}"
                raise ValueError(msg)
            self._stack.extend(struct.pack("f", float(value)))
        elif datatype in {DataType.STRING, DataType.OBJECT, DataType.EFFECT,
                          DataType.EVENT, DataType.LOCATION, DataType.TALENT}:
            # For non-primitive types, store as 4-byte reference/handle
            # In a real implementation these would be object references
            # For StackV2 byte-based simulation, store as int
            handle = 0 if value is None else hash(value) & 0xFFFFFFFF
            self._stack.extend(struct.pack("I", handle))
        else:
            msg = f"Unsupported datatype for StackV2: {datatype}"
            raise NotImplementedError(msg)


class Stack:
    def __init__(self):
        self._stack: list[StackObject] = []
        self._bp: int = 0
        self._bp_buffer: list[int] = []

    def state(self) -> list:
        return copy(self._stack)

    def add(self, data_type: DataType, value: Any):
        self._stack.append(StackObject(data_type, value))

    def _stack_index(self, offset: int) -> int:
        """Convert a stack offset to an actual list index.

        Args:
        ----
            offset: Stack offset (must be negative, relative to stack top)

        Returns:
        -------
            int: Actual index in the stack list

        Raises:
        ------
            ValueError: If offset is invalid
        """
        if offset >= 0:
            msg = f"Stack offset must be negative, got {offset}"
            raise ValueError(msg)

        offset = abs(offset)
        index = 0
        while offset > 0:
            if abs(index) > len(self._stack):
                msg = f"Stack offset out of range: {offset}"
                raise ValueError(msg)
            element_size = self._stack[index].data_type.size()
            offset -= element_size
            index -= 1
        return index

    def _stack_index_bp(self, offset: int) -> int:
        """Convert a base-pointer-relative offset to an actual list index.

        Args:
        ----
            offset: Offset relative to base pointer (must be negative)

        Returns:
        -------
            int: Actual index in the stack list

        Raises:
        ------
            ValueError: If offset is invalid or out of range
        """
        if offset >= 0:
            msg = f"BP-relative offset must be negative, got {offset}"
            raise ValueError(msg)

        bp_index = self._bp // 4
        relative_index = abs(offset) // 4
        absolute_index = bp_index - relative_index

        if absolute_index < 0 or absolute_index >= len(self._stack):
            msg = f"BP-relative offset {offset} results in invalid index {absolute_index}"
            raise ValueError(msg)

        return absolute_index

    def stack_pointer(self) -> int:
        return len(self._stack) * 4

    def base_pointer(self) -> int:
        return self._bp

    def peek(self, offset: int) -> Any:
        real_index = self._stack_index(offset)
        return self._stack[real_index]

    def copy_to_top(self, offset: int, size: int):
        for _i in range(size // 4):
            self._stack.append(self.peek(offset))

    def copy_down(self, offset: int, size: int):
        if size % 4 != 0:
            msg = "Size must be divisible by 4"
            raise ValueError(msg)

        num_elements = size // 4

        if num_elements > len(self._stack):
            msg = "Size exceeds the current stack size"
            raise IndexError(msg)

        # Let's find the target indices first
        target_indices = []
        temp_offset = offset

        for _ in range(num_elements):
            target_index = self._stack_index(temp_offset)
            target_indices.append(target_index)
            temp_offset += 4  # Move to the next position

        # Now copy the elements down the stack
        for i in range(num_elements):
            source_index = -1 - i  # Counting from the end of the list
            target_index = target_indices[-1 - i]  # The last target index corresponds to the first source index
            self._stack[target_index] = self._stack[source_index]

    def pop(self) -> Any:
        """Pop and return the top stack element.

        Returns:
        -------
            StackObject: The popped stack element

        Raises:
        ------
            IndexError: If stack is empty
        """
        if not self._stack:
            msg = "Cannot pop from empty stack"
            raise IndexError(msg)
        return self._stack.pop()

    def move(self, offset: int):
        """Move the stack pointer by offset (shrink or grow stack).

        Args:
        ----
            offset: Number of bytes to move (negative shrinks, positive grows)

        Raises:
        ------
            ValueError: If offset is positive (stack growth not supported via move)
        """
        if offset > 0:
            msg = f"Stack growth via MOVSP not supported (offset={offset})"
            raise ValueError(msg)
        if offset == 0:
            return
        remove_to = self._stack_index(offset)
        self._stack = self._stack[:remove_to]

    def copy_down_bp(self, offset: int, size: int):
        """Copy value from stack top down to base-pointer-relative location.

        Args:
        ----
            offset: Offset relative to base pointer (negative)
            size: Size in bytes to copy (typically 4)

        Raises:
        ------
            IndexError: If stack is empty
            ValueError: If offset/size is invalid
        """
        if not self._stack:
            msg = "Cannot copy from empty stack"
            raise IndexError(msg)

        if size % 4 != 0:
            msg = f"Size must be multiple of 4, got {size}"
            raise ValueError(msg)

        # For now, simple implementation copying single element
        # Full implementation would handle multi-element copies
        top_value = self._stack[-1]
        to_index = self._stack_index_bp(offset)
        self._stack[to_index] = top_value

    def copy_top_bp(self, offset: int, size: int):
        """Copy value from base-pointer-relative location to stack top.

        Args:
        ----
            offset: Offset relative to base pointer (negative)
            size: Size in bytes to copy (typically 4)

        Raises:
        ------
            ValueError: If offset/size is invalid
        """
        if size % 4 != 0:
            msg = f"Size must be multiple of 4, got {size}"
            raise ValueError(msg)

        copy_index = self._stack_index_bp(offset)
        top_value = self._stack[copy_index]
        self._stack.append(top_value)

    def save_bp(self):
        self._bp_buffer.append(self.base_pointer())
        self._bp = self.stack_pointer()

    def restore_bp(self):
        self._bp = self._bp_buffer.pop()

    def increment(self, offset: int):
        """Increment value at stack offset.

        Args:
        ----
            offset: Stack offset (negative, relative to top)

        Raises:
        ------
            ValueError: If value at offset is not numeric
        """
        index = self._stack_index(offset)
        new_value: StackObject = copy(self._stack[index])
        if isinstance(new_value.value, int):
            new_value.value += 1
        elif isinstance(new_value.value, float):
            new_value.value += 1.0
        else:
            msg = f"Cannot increment non-numeric type {new_value.data_type}"
            raise TypeError(msg)
        self._stack[index] = new_value

    def decrement(self, offset: int):
        """Decrement value at stack offset.

        Args:
        ----
            offset: Stack offset (negative, relative to top)

        Raises:
        ------
            ValueError: If value at offset is not numeric
        """
        index = self._stack_index(offset)
        new_value: StackObject = copy(self._stack[index])
        if isinstance(new_value.value, int):
            new_value.value -= 1
        elif isinstance(new_value.value, float):
            new_value.value -= 1.0
        else:
            msg = f"Cannot decrement non-numeric type {new_value.data_type}"
            raise TypeError(msg)
        self._stack[index] = new_value

    def increment_bp(self, offset: int):
        """Increment value at base-pointer-relative offset.

        Args:
        ----
            offset: Offset relative to base pointer (negative)

        Raises:
        ------
            ValueError: If value at offset is not numeric
        """
        index = self._stack_index_bp(offset)
        new_value: StackObject = copy(self._stack[index])
        if isinstance(new_value.value, int):
            new_value.value += 1
        elif isinstance(new_value.value, float):
            new_value.value += 1.0
        else:
            msg = f"Cannot increment non-numeric type {new_value.data_type}"
            raise TypeError(msg)
        self._stack[index] = new_value


    def decrement_bp(self, offset: int):
        """Decrement value at base-pointer-relative offset.

        Args:
        ----
            offset: Offset relative to base pointer (negative)

        Raises:
        ------
            ValueError: If value at offset is not numeric
        """
        index = self._stack_index_bp(offset)
        new_value: StackObject = copy(self._stack[index])
        if isinstance(new_value.value, int):
            new_value.value -= 1
        elif isinstance(new_value.value, float):
            new_value.value -= 1.0
        else:
            msg = f"Cannot decrement non-numeric type {new_value.data_type}"
            raise TypeError(msg)
        self._stack[index] = new_value

    def addition_op(self):
        """Perform addition operation on top two stack values."""
        if len(self._stack) < 2:
            msg = "Stack underflow in addition operation"
            raise IndexError(msg)
        index1 = -1  # top of stack
        index2 = -2  # second from top
        value1 = copy(self._stack[index1])
        value2 = copy(self._stack[index2])
        if not isinstance(value1.value, (int, float)) or not isinstance(value2.value, (int, float)):
            msg = "Addition requires numeric operands"
            raise TypeError(msg)
        result = value2.value + value1.value
        self._stack.pop()
        self._stack.pop()
        self.add(value2.data_type, result)

    def subtraction_op(self):
        """Perform subtraction operation on top two stack values."""
        if len(self._stack) < 2:
            msg = "Stack underflow in subtraction operation"
            raise IndexError(msg)
        index1 = -1
        index2 = -2
        value1 = copy(self._stack[index1])
        value2 = copy(self._stack[index2])
        if not isinstance(value1.value, (int, float)) or not isinstance(value2.value, (int, float)):
            msg = "Subtraction requires numeric operands"
            raise TypeError(msg)
        result = value2.value - value1.value
        self._stack.pop()
        self._stack.pop()
        self.add(value2.data_type, result)

    def multiplication_op(self):
        """Perform multiplication operation on top two stack values."""
        if len(self._stack) < 2:
            msg = "Stack underflow in multiplication operation"
            raise IndexError(msg)
        index1 = -1
        index2 = -2
        value1 = copy(self._stack[index1])
        value2 = copy(self._stack[index2])
        if not isinstance(value1.value, (int, float)) or not isinstance(value2.value, (int, float)):
            msg = "Multiplication requires numeric operands"
            raise TypeError(msg)
        result = value2.value * value1.value
        self._stack.pop()
        self._stack.pop()
        self.add(value2.data_type, result)

    def division_op(self):
        """Perform division operation on top two stack values."""
        if len(self._stack) < 2:
            msg = "Stack underflow in division operation"
            raise IndexError(msg)
        index1 = -1
        index2 = -2
        value1 = copy(self._stack[index1])
        value2 = copy(self._stack[index2])
        if not isinstance(value1.value, (int, float)) or not isinstance(value2.value, (int, float)):
            msg = "Division requires numeric operands"
            raise TypeError(msg)
        if value1.value == 0:
            msg = "Division by zero in NCS interpreter"
            raise ZeroDivisionError(msg)
        result = float(value2.value) / float(value1.value)
        self._stack.pop()
        self._stack.pop()
        self.add(value2.data_type, result)

    def modulus_op(self):
        """Perform modulus operation on top two stack values."""
        if len(self._stack) < 2:
            msg = "Stack underflow in modulus operation"
            raise IndexError(msg)
        index1 = -1
        index2 = -2
        value1 = copy(self._stack[index1])
        value2 = copy(self._stack[index2])
        if not isinstance(value1.value, (int, float)) or not isinstance(value2.value, (int, float)):
            msg = "Modulus requires numeric operands"
            raise TypeError(msg)
        if value1.value == 0:
            msg = "Modulus by zero in NCS interpreter"
            raise ZeroDivisionError(msg)
        result = value2.value % value1.value
        self._stack.pop()
        self._stack.pop()
        self.add(value2.data_type, result)

    def negation_op(self):
        """Perform unary negation on top stack value."""
        if not self._stack:
            msg = "Stack underflow in negation operation"
            raise IndexError(msg)
        index = -1
        value1 = copy(self._stack[index])
        if not isinstance(value1.value, (int, float)):
            msg = f"Cannot negate non-numeric type {value1.data_type}"
            raise TypeError(msg)
        result = -value1.value
        self._stack.pop()
        self.add(value1.data_type, result)


    def logical_not_op(self):
        """Perform logical NOT on top stack value."""
        if not self._stack:
            msg = "Stack underflow in logical NOT operation"
            raise IndexError(msg)
        value1 = self._stack.pop()
        # Convert to boolean for logical NOT
        result = 0 if value1.value else 1
        self.add(value1.data_type, result)

    def logical_and_op(self):
        """Perform logical AND on top two stack values."""
        if len(self._stack) < 2:
            msg = "Stack underflow in logical AND operation"
            raise IndexError(msg)
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        # Logical AND: both must be non-zero
        result = 1 if (value1.value and value2.value) else 0
        self.add(value1.data_type, result)

    def logical_or_op(self):
        """Perform logical OR on top two stack values."""
        if len(self._stack) < 2:
            msg = "Stack underflow in logical OR operation"
            raise IndexError(msg)
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        # Logical OR: at least one must be non-zero
        result = 1 if (value1.value or value2.value) else 0
        self.add(value1.data_type, result)

    def logical_equality_op(self):
        """Perform equality comparison on top two stack values."""
        if len(self._stack) < 2:
            msg = "Stack underflow in equality comparison"
            raise IndexError(msg)
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        result = 1 if value1.value == value2.value else 0
        self.add(value1.data_type, result)

    def logical_inequality_op(self):
        """Perform inequality comparison on top two stack values."""
        if len(self._stack) < 2:
            msg = "Stack underflow in inequality comparison"
            raise IndexError(msg)
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        result = 1 if value1.value != value2.value else 0
        self.add(value1.data_type, result)

    def bitwise_not_op(self):
        """Perform bitwise NOT on top stack value."""
        if not self._stack:
            msg = "Stack underflow in bitwise NOT operation"
            raise IndexError(msg)
        value1 = self._stack.pop()
        if not isinstance(value1.value, int):
            msg = f"Cannot perform bitwise NOT on non-integer type {value1.data_type}"
            raise TypeError(msg)
        self.add(value1.data_type, ~value1.value)

    def bitwise_or_op(self):
        """Perform bitwise OR on top two stack values."""
        if len(self._stack) < 2:
            msg = "Stack underflow in bitwise OR operation"
            raise IndexError(msg)
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        if not isinstance(value1.value, int) or not isinstance(value2.value, int):
            msg = "Bitwise OR requires integer operands"
            raise TypeError(msg)
        self.add(value1.data_type, value1.value | value2.value)

    def bitwise_xor_op(self):
        """Perform bitwise XOR on top two stack values."""
        if len(self._stack) < 2:
            msg = "Stack underflow in bitwise XOR operation"
            raise IndexError(msg)
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        if not isinstance(value1.value, int) or not isinstance(value2.value, int):
            msg = "Bitwise XOR requires integer operands"
            raise TypeError(msg)
        self.add(value1.data_type, value1.value ^ value2.value)

    def bitwise_and_op(self):
        """Perform bitwise AND on top two stack values."""
        if len(self._stack) < 2:
            msg = "Stack underflow in bitwise AND operation"
            raise IndexError(msg)
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        if not isinstance(value1.value, int) or not isinstance(value2.value, int):
            msg = "Bitwise AND requires integer operands"
            raise TypeError(msg)
        self.add(value1.data_type, value1.value & value2.value)

    def bitwise_leftshift_op(self):
        """Perform bitwise left shift on top two stack values."""
        if len(self._stack) < 2:
            msg = "Stack underflow in left shift operation"
            raise IndexError(msg)
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        if not isinstance(value1.value, int) or not isinstance(value2.value, int):
            msg = "Bitwise shift requires integer operands"
            raise TypeError(msg)
        self.add(value1.data_type, value2.value << value1.value)

    def bitwise_rightshift_op(self):
        """Perform bitwise right shift on top two stack values."""
        if len(self._stack) < 2:
            msg = "Stack underflow in right shift operation"
            raise IndexError(msg)
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        if not isinstance(value1.value, int) or not isinstance(value2.value, int):
            msg = "Bitwise shift requires integer operands"
            raise TypeError(msg)
        self.add(value1.data_type, value2.value >> value1.value)

    def compare_greaterthan_op(self):
        """Perform greater-than comparison on top two stack values."""
        if len(self._stack) < 2:
            msg = "Stack underflow in greater-than comparison"
            raise IndexError(msg)
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        if not isinstance(value2.value, (int, float)) or not isinstance(value1.value, (int, float)):
            msg = "Comparison requires numeric operands"
            raise TypeError(msg)
        result = 1 if value2.value > value1.value else 0
        self.add(value1.data_type, result)

    def compare_greaterthanorequal_op(self):
        """Perform greater-than-or-equal comparison on top two stack values."""
        if len(self._stack) < 2:
            msg = "Stack underflow in greater-than-or-equal comparison"
            raise IndexError(msg)
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        if not isinstance(value2.value, (int, float)) or not isinstance(value1.value, (int, float)):
            msg = "Comparison requires numeric operands"
            raise TypeError(msg)
        result = 1 if value2.value >= value1.value else 0
        self.add(value1.data_type, result)

    def compare_lessthan_op(self):
        """Perform less-than comparison on top two stack values."""
        if len(self._stack) < 2:
            msg = "Stack underflow in less-than comparison"
            raise IndexError(msg)
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        if not isinstance(value2.value, (int, float)) or not isinstance(value1.value, (int, float)):
            msg = "Comparison requires numeric operands"
            raise TypeError(msg)
        result = 1 if value2.value < value1.value else 0
        self.add(value1.data_type, result)

    def compare_lessthanorequal_op(self):
        """Perform less-than-or-equal comparison on top two stack values."""
        if len(self._stack) < 2:  # noqa: PLR2004
            msg = "Stack underflow in less-than-or-equal comparison"
            raise IndexError(msg)
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        if not isinstance(value2.value, (int, float)) or not isinstance(value1.value, (int, float)):
            msg = "Comparison requires numeric operands"
            raise TypeError(msg)
        result = 1 if value2.value <= value1.value else 0
        self.add(value1.data_type, result)

    def store_state(self): ...


class StackObject:
    def __init__(self, data_type: DataType, value: float | str | bool | object):  # noqa: FBT001
        self.data_type: DataType = data_type
        self.value = value

    def __repr__(self):
        return f"{self.data_type.name}={self.value}"

    def __eq__(self, other: StackObject | object):
        if self is other:
            return True
        if isinstance(other, StackObject):
            return self.value == other.value
        return self.value == other

    def __hash__(self):
        return hash((self.data_type, id(self.value)))


class ActionStackValue(NamedTuple):
    block: list[NCSInstruction]
    stack: list[StackObject]


class ActionSnapshot(NamedTuple):
    function_name: str
    arg_values: list
    return_value: Any


class StackSnapshot(NamedTuple):
    instruction: NCSInstruction
    stack: list[StackObject]


class EngineRoutineMock:
    def __init__(self, function: ScriptFunction, mock: Callable):
        self.function: ScriptFunction = function
        self.mock: Callable = mock
