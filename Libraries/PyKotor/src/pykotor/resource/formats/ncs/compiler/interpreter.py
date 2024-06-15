from __future__ import annotations

import struct

from copy import copy
from inspect import signature
from typing import TYPE_CHECKING, Any, NamedTuple

from pykotor.common.geometry import Vector3
from pykotor.common.script import DataType
from pykotor.common.scriptdefs import KOTOR_FUNCTIONS
from pykotor.resource.formats.ncs import NCSInstructionType

if TYPE_CHECKING:
    from collections.abc import Callable

    from pykotor.common.script import ScriptFunction
    from pykotor.resource.formats.ncs import NCS, NCSInstruction


class Interpreter:
    """This class is not used in the compiling process. This is only partially implemented, mostly for testing purposes."""

    def __init__(self, ncs: NCS):
        self._ncs: NCS = ncs
        self._cursor: NCSInstruction = ncs.instructions[0]
        self._functions: list[ScriptFunction] = KOTOR_FUNCTIONS

        self._stack: Stack = Stack()
        self._returns: list[NCSInstruction] = [None]

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
                return_to = self._ncs.instructions[index_return_to]
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

            # Control flow
            if self._cursor.ins_type == NCSInstructionType.RETN:
                return_to = self._returns.pop()
                self._cursor = return_to
                continue

            if (
                self._cursor.ins_type == NCSInstructionType.JMP
                or (self._cursor.ins_type == NCSInstructionType.JZ and jump_value == 0)
                or (self._cursor.ins_type == NCSInstructionType.JNZ and jump_value != 0)
                or self._cursor.ins_type == NCSInstructionType.JSR
            ):
                self._cursor = self._cursor.jump
            else:
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

    def do_action(self, function: ScriptFunction, args: int):
        args_snap = []

        for i in range(args):
            if function.params[i].datatype == DataType.VECTOR:
                vector_object = StackObject(
                    DataType.VECTOR,
                    Vector3(
                        self._stack.pop().value,
                        self._stack.pop().value,
                        self._stack.pop().value,
                    ),
                )
                args_snap.append(vector_object)
            else:
                args_snap.append(self._stack.pop())

        for i in range(args):
            if function.params[i].datatype != args_snap[i].data_type:
                msg = f"Invoked action '{function.name}' received the wrong data type for parameter '{function.params[i].name}' valued at '{args_snap[i]}'."
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
            (function for function in self._functions if function.name == function_name),
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
        self._stack_types: list = []

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

    # TODO: refactor
    def add(self, datatype: DataType, value: float | int):  # noqa: PYI041,RUF100
        if datatype not in {DataType.INT, DataType.FLOAT}:
            raise NotImplementedError
        if not isinstance(value, int):
            raise ValueError
        self._stack.extend(struct.pack("i", value))


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
        if offset >= 0:
            raise ValueError
        offset = abs(offset)
        index = 0
        while offset > 0:
            element_size = self._stack[index].data_type.size()
            offset -= element_size
            index -= 1
        return index

    def _stack_index_bp(self, offset: int) -> int:
        if offset >= 0:
            raise ValueError
        bp_index = self._bp // 4
        relative_index = abs(offset) // 4
        absolute_index = bp_index - relative_index
        if absolute_index < 0:
            raise ValueError
        return bp_index - relative_index

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
        return self._stack.pop()

    def move(self, offset: int):
        if offset > 0:
            raise ValueError
        if offset == 0:
            return
        remove_to = self._stack_index(offset)
        self._stack = self._stack[:remove_to]

    def copy_down_bp(self, offset: int, size: int):
        # Copy from the top of the stack down to the bp adjusted w/ offset?
        top_value = self._stack[-1]
        to_index = self._stack_index_bp(offset)
        self._stack[to_index] = top_value

    def copy_top_bp(self, offset: int, size: int):
        # Copy value relative to base pointer to the top of the stack
        copy_index = self._stack_index_bp(offset)
        top_value = self._stack[copy_index]
        self._stack.append(top_value)

    def save_bp(self):
        self._bp_buffer.append(self.base_pointer())
        self._bp = self.stack_pointer()

    def restore_bp(self):
        self._bp = self._bp_buffer.pop()

    def increment(self, offset: int):
        index = self._stack_index(offset)
        self._stack[index] = copy(self._stack[index])
        self._stack[index].value += 1

    def decrement(self, offset: int):
        index = self._stack_index(offset)
        self._stack[index] = copy(self._stack[index])
        self._stack[index].value -= 1

    def increment_bp(self, offset: int):
        index = self._stack_index_bp(offset)
        self._stack[index] = copy(self._stack[index])
        self._stack[index].value += 1

    def decrement_bp(self, offset: int):
        index = self._stack_index_bp(offset)
        self._stack[index] = copy(self._stack[index])
        self._stack[index].value -= 1

    def addition_op(self):
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        self.add(value2.data_type, value2.value + value1.value)

    def subtraction_op(self):
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        self.add(value2.data_type, value2.value - value1.value)

    def multiplication_op(self):
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        self.add(value1.data_type, value2.value * value1.value)

    def division_op(self):
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        self.add(value1.data_type, value2.value / value1.value)

    def modulus_op(self):
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        self.add(value1.data_type, value2.value % value1.value)

    def negation_op(self):
        value1 = self._stack.pop()
        self.add(value1.data_type, -value1.value)

    def logical_not_op(self):
        value1 = self._stack.pop()
        self.add(value1.data_type, not value1.value)

    def logical_and_op(self):
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        self.add(value1.data_type, value1.value and value2.value)

    def logical_or_op(self):
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        self.add(value1.data_type, value1.value or value2.value)

    def logical_equality_op(self):
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        self.add(value1.data_type, value1.value == value2.value)

    def logical_inequality_op(self):
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        self.add(value1.data_type, value1.value != value2.value)

    def bitwise_not_op(self):
        value1 = self._stack.pop()
        self.add(value1.data_type, ~value1.value)

    def bitwise_or_op(self):
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        self.add(value1.data_type, value1.value | value2.value)

    def bitwise_xor_op(self):
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        self.add(value1.data_type, value1.value ^ value2.value)

    def bitwise_and_op(self):
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        self.add(value1.data_type, value1.value & value2.value)

    def bitwise_leftshift_op(self):
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        self.add(value1.data_type, value2.value << value1.value)

    def bitwise_rightshift_op(self):
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        self.add(value1.data_type, value2.value >> value1.value)

    def compare_greaterthan_op(self):
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        self.add(value1.data_type, int(value2.value > value1.value))

    def compare_greaterthanorequal_op(self):
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        self.add(value1.data_type, int(value2.value >= value1.value))

    def compare_lessthan_op(self):
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        self.add(value1.data_type, int(value2.value < value1.value))

    def compare_lessthanorequal_op(self):
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        self.add(value1.data_type, int(value2.value <= value1.value))

    def store_state(self): ...


class StackObject:
    def __init__(self, data_type: DataType, value: Any):
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
