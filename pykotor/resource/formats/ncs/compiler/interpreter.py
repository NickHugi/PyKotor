from copy import copy
from typing import List, Any, NamedTuple

from pykotor.common.script import ScriptFunction, DataType
from pykotor.common.scriptdefs import KOTOR_FUNCTIONS
from pykotor.resource.formats.ncs import NCS, NCSInstruction, NCSInstructionType


class Interpreter:
    def __init__(self, ncs: NCS):
        self._ncs: NCS = ncs
        self._cursor: NCSInstruction = ncs.instructions[0]
        self._functions: List[ScriptFunction] = KOTOR_FUNCTIONS

        self._stack: Stack = Stack()

        self.stack_snapshots: List[List[StackObject]] = []
        self.action_snapshots: List[ActionSnapshot] = []

    def run(self):
        while True:
            index = self._ncs.instructions.index(self._cursor)

            if self._cursor.ins_type == NCSInstructionType.CONSTS:
                self._stack.add(DataType.STRING, self._cursor.args[0])
            elif self._cursor.ins_type == NCSInstructionType.CONSTI:
                self._stack.add(DataType.INT, self._cursor.args[0])
            elif self._cursor.ins_type == NCSInstructionType.CONSTF:
                self._stack.add(DataType.FLOAT, self._cursor.args[0])
            elif self._cursor.ins_type == NCSInstructionType.CONSTO:
                self._stack.add(DataType.OBJECT, self._cursor.args[0])
            elif self._cursor.ins_type == NCSInstructionType.CPTOPSP:
                self._stack.copy_to_top(self._cursor.args[0])
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

            self.stack_snapshots.append(self._stack.state())
            # print(self._cursor, "\n", self._stack.state(), "\n")

            if self._cursor.jump is not None:
                self._cursor = self._cursor.jump
            elif index < len(self._ncs.instructions)-1:
                self._cursor = self._ncs.instructions[index + 1]
            else:
                break

    def action(self, function: ScriptFunction, args: int):
        args_snap = []

        for i in range(args):
            args_snap.append(self._stack.pop())
        if function.returntype != DataType.VOID:
            self._stack.add(function.returntype, None)

        self.action_snapshots.append(ActionSnapshot(function.name, args_snap, None))


class Stack:
    def __init__(self):
        self._stack: List = []

    def state(self) -> List:
        return copy(self._stack)

    def add(self, data_type: DataType, value: Any) -> None:
        self._stack.append(StackObject(data_type, value))

    def copy_to_top(self, offset: int) -> None:
        self._stack.append(self._stack[offset // 4])

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
