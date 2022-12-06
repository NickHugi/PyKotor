from copy import copy
from inspect import signature
from typing import List, Any, NamedTuple, Callable, Dict

from pykotor.common.script import ScriptFunction, DataType
from pykotor.common.scriptdefs import KOTOR_FUNCTIONS
from pykotor.resource.formats.ncs import NCS, NCSInstruction, NCSInstructionType


class Interpreter:
    def __init__(self, ncs: NCS):
        self._ncs: NCS = ncs
        self._cursor: NCSInstruction = ncs.instructions[0]
        self._functions: List[ScriptFunction] = KOTOR_FUNCTIONS

        self._stack: Stack = Stack()
        self._returns: List[NCSInstruction] = [None]

        self._mocks: Dict[str, Callable] = {}

        self.stack_snapshots: List[StackSnapshot] = []
        self.action_snapshots: List[ActionSnapshot] = []

    def run(self):
        while self._cursor is not None:
            # print(self._cursor)
            index = self._ncs.instructions.index(self._cursor)
            jump_value = None

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
                self._stack.copy_down(self._cursor.args[0])

            elif self._cursor.ins_type == NCSInstructionType.ACTION:
                self.action(self._functions[self._cursor.args[0]], self._cursor.args[1])

            elif self._cursor.ins_type == NCSInstructionType.MOVSP:
                self._stack.move(self._cursor.args[0])

            elif self._cursor.ins_type in [NCSInstructionType.ADDII, NCSInstructionType.ADDIF,
                                           NCSInstructionType.ADDFF, NCSInstructionType.ADDFI,
                                           NCSInstructionType.ADDSS, NCSInstructionType.ADDVV]:
                self._stack.addition_op()

            elif self._cursor.ins_type in [NCSInstructionType.SUBII, NCSInstructionType.SUBIF,
                                           NCSInstructionType.SUBFF, NCSInstructionType.SUBFI,
                                           NCSInstructionType.SUBVV]:
                self._stack.subtraction_op()

            elif self._cursor.ins_type in [NCSInstructionType.MULII, NCSInstructionType.MULIF,
                                           NCSInstructionType.MULFF, NCSInstructionType.MULFI,
                                           NCSInstructionType.MULVF, NCSInstructionType.MULFV]:
                self._stack.multiplication_op()

            elif self._cursor.ins_type in [NCSInstructionType.DIVII, NCSInstructionType.DIVIF,
                                           NCSInstructionType.DIVFF, NCSInstructionType.DIVFI,
                                           NCSInstructionType.DIVVF]:
                self._stack.division_op()

            elif self._cursor.ins_type in [NCSInstructionType.MODII]:
                self._stack.modulus_op()

            elif self._cursor.ins_type in [NCSInstructionType.NEGI, NCSInstructionType.NEGF]:
                self._stack.negation_op()

            elif self._cursor.ins_type in [NCSInstructionType.COMPI]:
                self._stack.bitwise_not_op()

            elif self._cursor.ins_type in [NCSInstructionType.NOTI]:
                self._stack.logical_not_op()

            elif self._cursor.ins_type in [NCSInstructionType.LOGANDII]:
                self._stack.logical_and_op()

            elif self._cursor.ins_type in [NCSInstructionType.LOGORII]:
                self._stack.logical_or_op()

            elif self._cursor.ins_type in [NCSInstructionType.INCORII]:
                self._stack.bitwise_or_op()

            elif self._cursor.ins_type in [NCSInstructionType.EXCORII]:
                self._stack.bitwise_xor_op()

            elif self._cursor.ins_type in [NCSInstructionType.BOOLANDII]:
                self._stack.bitwise_and_op()

            elif self._cursor.ins_type in [NCSInstructionType.EQUALII, NCSInstructionType.EQUALFF,
                                           NCSInstructionType.EQUALSS, NCSInstructionType.EQUALOO]:
                self._stack.logical_equality_op()

            elif self._cursor.ins_type in [NCSInstructionType.NEQUALII, NCSInstructionType.NEQUALFF,
                                           NCSInstructionType.NEQUALSS, NCSInstructionType.NEQUALOO]:
                self._stack.logical_inequality_op()

            elif self._cursor.ins_type in [NCSInstructionType.GTII, NCSInstructionType.GTFF]:
                self._stack.compare_greaterthan_op()

            elif self._cursor.ins_type in [NCSInstructionType.GEQII, NCSInstructionType.GEQFF]:
                self._stack.compare_greaterthanorequal_op()

            elif self._cursor.ins_type in [NCSInstructionType.LTII, NCSInstructionType.LTFF]:
                self._stack.compare_lessthan_op()

            elif self._cursor.ins_type in [NCSInstructionType.LEQII, NCSInstructionType.LEQFF]:
                self._stack.compare_lessthanorequal_op()

            elif self._cursor.ins_type in [NCSInstructionType.SHLEFTII]:
                self._stack.bitwise_leftshift_op()

            elif self._cursor.ins_type in [NCSInstructionType.SHRIGHTII]:
                self._stack.bitwise_rightshift_op()

            elif self._cursor.ins_type in [NCSInstructionType.JSR]:
                index_return_to = self._ncs.instructions.index(self._cursor) + 1
                return_to = self._ncs.instructions[index_return_to]
                self._returns.append(return_to)

            elif self._cursor.ins_type in [NCSInstructionType.JZ, NCSInstructionType.JNZ]:
                jump_value = self._stack.pop()

            self.stack_snapshots.append(StackSnapshot(self._cursor, self._stack.state()))

            if self._cursor.ins_type in [NCSInstructionType.RETN]:
                return_to = self._returns.pop()
                self._cursor = return_to
                continue

            elif self._cursor.ins_type in [NCSInstructionType.JMP]:
                self._cursor = self._cursor.jump

            elif self._cursor.ins_type in [NCSInstructionType.JZ] and jump_value == 0:
                self._cursor = self._cursor.jump

            elif self._cursor.ins_type in [NCSInstructionType.JNZ] and jump_value != 0:
                self._cursor = self._cursor.jump

            elif self._cursor.ins_type in [NCSInstructionType.JSR]:
                self._cursor = self._cursor.jump

            else:
                self._cursor = self._ncs.instructions[index + 1]

    def action(self, function: ScriptFunction, args: int):
        args_snap = []

        for i in range(args):
            args_snap.append(self._stack.pop())

        if function.returntype != DataType.VOID:
            if function.name in self._mocks:
                # Execute and return the value back from the mock
                self._stack.add(function.returntype, self._mocks[function.name](*[arg.value for arg in args_snap]))
            else:
                # Return value of None if no relevant mock is found
                self._stack.add(function.returntype, None)

        self.action_snapshots.append(ActionSnapshot(function.name, args_snap, None))

    def print(self):
        for snap in self.stack_snapshots:
            print(snap.instruction, "\n", snap.stack, "\n")

    def set_mock(self, function_name: str, mock: Callable):
        function = next((function for function in self._functions if function.name == function_name), None)

        if function is None:
            raise ValueError(f"Function '{function_name}' does not exist.")

        mock_param_count = len(signature(mock).parameters)
        routine_param_count = len(function.params)
        if mock_param_count != routine_param_count:
            raise ValueError(f"Function '{function_name}' expects {routine_param_count} parameters not {mock_param_count}.")

        self._mocks[function_name] = mock

    def remove_mock(self, function_name: str):
        self._mocks.pop(function_name)


class Stack:
    def __init__(self):
        self._stack: List = []

    def state(self) -> List:
        return copy(self._stack)

    def add(self, data_type: DataType, value: Any) -> None:
        self._stack.append(StackObject(data_type, value))

    def _stack_index(self, offset: int) -> int:
        if offset == 0:
            raise ValueError
        return offset // 4

    def peek(self, offset: int) -> Any:
        real_index = self._stack_index(offset)
        return self._stack[real_index]

    def copy_to_top(self, offset: int, size: int) -> None:
        self._stack.append(self.peek(offset))

    def copy_down(self, offset: int) -> None:
        top_value = self._stack[-1]
        self._stack[self._stack_index(offset)] = top_value

    def pop(self) -> Any:
        return self._stack.pop()

    def move(self, offset: int) -> None:
        for i in range(abs(offset // 4)):
            self._stack.pop()

    def addition_op(self):
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        self.add(value1.data_type, value2.value + value1.value)

    def subtraction_op(self):
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        self.add(value1.data_type, value2.value - value1.value)

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
        self.add(value1.data_type, int(value1.value > value2.value))

    def compare_greaterthanorequal_op(self):
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        self.add(value1.data_type, int(value1.value >= value2.value))

    def compare_lessthan_op(self):
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        self.add(value1.data_type, int(value1.value < value2.value))

    def compare_lessthanorequal_op(self):
        value1 = self._stack.pop()
        value2 = self._stack.pop()
        self.add(value1.data_type, int(value1.value <= value2.value))


class StackObject:
    def __init__(self, data_type: DataType, value: Any):
        self.data_type: DataType = data_type
        self.value = value

    def __repr__(self):
        return f"{self.data_type.name}={self.value}"

    def __eq__(self, other):
        if isinstance(other, StackObject):
            return self.value == other.value
        else:
            return self.value == other


class ActionSnapshot(NamedTuple):
    function_name: str
    arg_values: List
    return_value: Any


class StackSnapshot(NamedTuple):
    instruction: NCSInstruction
    stack: List[StackObject]


class EngineRoutineMock:
    def __init__(self, function: ScriptFunction, mock: Callable):
        self.function: ScriptFunction = function
        self.mock: Callable = mock
