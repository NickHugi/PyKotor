from __future__ import annotations

import logging
import struct

from copy import copy
from inspect import signature
from typing import TYPE_CHECKING, Any, NamedTuple, cast

from pykotor.common.script import DataType
from pykotor.common.scriptdefs import KOTOR_FUNCTIONS
from pykotor.resource.formats.ncs import NCSInstructionType
from utility.common.geometry import Vector3
from pykotor.common.misc import Game
from pykotor.resource.formats.ncs import NCSInstruction

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from collections.abc import Callable

    from pykotor.common.script import ScriptFunction
    from pykotor.resource.formats.ncs import NCS
    KOTOR_FUNCTIONS: list[ScriptFunction] = []
    TSL_FUNCTIONS: list[ScriptFunction] = []
else:
    from pykotor.common.scriptdefs import KOTOR_FUNCTIONS, TSL_FUNCTIONS


class Interpreter:
    """NCS bytecode interpreter for testing and debugging.
    
    Executes NCS bytecode instructions to test script behavior. Partially implemented
    for testing purposes, not used in the compilation process. Supports stack-based
    execution, function calls, and instruction limit protection.
    
    References:
    ----------
        vendor/KotOR.js/src/odyssey/controllers/ (Runtime script execution)
        vendor/reone/src/libs/script/format/ncsreader.cpp (NCS instruction reading)
        vendor/xoreos-tools/src/nwscript/decompiler.cpp (NCS instruction semantics)
        Note: Interpreter is PyKotor-specific for testing, not a full runtime implementation
    """

    # Default maximum instructions to prevent infinite loops
    # This is set to a high value to accommodate complex scripts while still providing protection
    DEFAULT_MAX_INSTRUCTIONS = 100_000

    def __init__(self, ncs: NCS, game: Game = Game.K1, max_instructions: int | None = None):
        self._ncs: NCS = ncs
        self._cursor: NCSInstruction | None = ncs.instructions[0]
        self._cursor_index: int = 0
        self._functions: list[ScriptFunction] = KOTOR_FUNCTIONS if game == Game.K1 else TSL_FUNCTIONS

        # Precompute instruction index lookup to avoid reliance on equality semantics
        self._instruction_indices: dict[int, int] = {id(instruction): idx for idx, instruction in enumerate(ncs.instructions)}

        self._stack: Stack = Stack()
        self._returns: list[tuple[NCSInstruction, int]] = []

        self._mocks: dict[str, Callable] = {}

        self.stack_snapshots: list[StackSnapshot] = []
        self.action_snapshots: list[ActionSnapshot] = []

        # Instruction execution limit
        self._max_instructions: int = max_instructions if max_instructions is not None else self.DEFAULT_MAX_INSTRUCTIONS
        self._instructions_executed: int = 0

    def run(self):
        """Execute the NCS script instructions.

        Raises:
        ------
            RuntimeError: If the instruction limit is exceeded (possible infinite loop detected).
        """
        while self._cursor is not None:
            # Check instruction limit to prevent infinite loops
            if self._instructions_executed >= self._max_instructions:
                log.error(
                    "Instruction limit exceeded: executed=%s, limit=%s, current_instruction=%s, cursor_index=%s",
                    self._instructions_executed,
                    self._max_instructions,
                    self._cursor.ins_type.name if self._cursor else "None",
                    self._cursor_index,
                )
                msg = (
                    f"Instruction limit exceeded: {self._instructions_executed} instructions executed "
                    f"(limit: {self._max_instructions}). Possible infinite loop detected at instruction "
                    f"index {self._cursor_index} ({self._cursor.ins_type.name if self._cursor else 'None'})"
                )
                raise RuntimeError(msg)

            self._instructions_executed += 1
            cursor = cast("NCSInstruction", self._cursor)
            index = self._cursor_index
            jump_value = None

            # print(str(index).ljust(3), str(self._cursor).ljust(40)[:40], str(self._stack.state()).ljust(30), f"BP={self._stack.base_pointer()//4}")

            if cursor.ins_type == NCSInstructionType.CONSTS:
                self._stack.add(DataType.STRING, cursor.args[0])

            elif cursor.ins_type == NCSInstructionType.CONSTI:
                self._stack.add(DataType.INT, cursor.args[0])

            elif cursor.ins_type == NCSInstructionType.CONSTF:
                self._stack.add(DataType.FLOAT, cursor.args[0])

            elif cursor.ins_type == NCSInstructionType.CONSTO:
                self._stack.add(DataType.OBJECT, cursor.args[0])

            elif cursor.ins_type == NCSInstructionType.CPTOPSP:
                self._stack.copy_to_top(cursor.args[0], cursor.args[1])

            elif cursor.ins_type == NCSInstructionType.CPDOWNSP:
                self._stack.copy_down(cursor.args[0], cursor.args[1])

            elif cursor.ins_type == NCSInstructionType.ACTION:
                self.do_action(
                    self._functions[cursor.args[0]],
                    cursor.args[1],
                )

            elif cursor.ins_type == NCSInstructionType.MOVSP:
                self._stack.move(cursor.args[0])

            elif cursor.ins_type in {
                NCSInstructionType.ADDII,
                NCSInstructionType.ADDIF,
                NCSInstructionType.ADDFF,
                NCSInstructionType.ADDFI,
                NCSInstructionType.ADDSS,
                NCSInstructionType.ADDVV,
            }:
                self._stack.addition_op()

            elif cursor.ins_type in {
                NCSInstructionType.SUBII,
                NCSInstructionType.SUBIF,
                NCSInstructionType.SUBFF,
                NCSInstructionType.SUBFI,
                NCSInstructionType.SUBVV,
            }:
                self._stack.subtraction_op()

            elif cursor.ins_type in {
                NCSInstructionType.MULII,
                NCSInstructionType.MULIF,
                NCSInstructionType.MULFF,
                NCSInstructionType.MULFI,
                NCSInstructionType.MULVF,
                NCSInstructionType.MULFV,
            }:
                self._stack.multiplication_op()

            elif cursor.ins_type in {
                NCSInstructionType.DIVII,
                NCSInstructionType.DIVIF,
                NCSInstructionType.DIVFF,
                NCSInstructionType.DIVFI,
                NCSInstructionType.DIVVF,
            }:
                self._stack.division_op()

            elif cursor.ins_type == NCSInstructionType.MODII:
                self._stack.modulus_op()

            elif cursor.ins_type in {
                NCSInstructionType.NEGI,
                NCSInstructionType.NEGF,
            }:
                self._stack.negation_op()

            elif cursor.ins_type == NCSInstructionType.COMPI:
                self._stack.bitwise_not_op()

            elif cursor.ins_type == NCSInstructionType.NOTI:
                self._stack.logical_not_op()

            elif cursor.ins_type == NCSInstructionType.LOGANDII:
                self._stack.logical_and_op()

            elif cursor.ins_type == NCSInstructionType.LOGORII:
                self._stack.logical_or_op()

            elif cursor.ins_type == NCSInstructionType.INCORII:
                self._stack.bitwise_or_op()

            elif cursor.ins_type == NCSInstructionType.EXCORII:
                self._stack.bitwise_xor_op()

            elif cursor.ins_type == NCSInstructionType.BOOLANDII:
                self._stack.bitwise_and_op()

            elif cursor.ins_type in {
                NCSInstructionType.EQUALII,
                NCSInstructionType.EQUALFF,
                NCSInstructionType.EQUALSS,
                NCSInstructionType.EQUALOO,
            }:
                self._stack.logical_equality_op()

            elif cursor.ins_type in {
                NCSInstructionType.NEQUALII,
                NCSInstructionType.NEQUALFF,
                NCSInstructionType.NEQUALSS,
                NCSInstructionType.NEQUALOO,
            }:
                self._stack.logical_inequality_op()

            elif cursor.ins_type in {
                NCSInstructionType.GTII,
                NCSInstructionType.GTFF,
            }:
                self._stack.compare_greaterthan_op()

            elif cursor.ins_type in {
                NCSInstructionType.GEQII,
                NCSInstructionType.GEQFF,
            }:
                self._stack.compare_greaterthanorequal_op()

            elif cursor.ins_type in {
                NCSInstructionType.LTII,
                NCSInstructionType.LTFF,
            }:
                self._stack.compare_lessthan_op()

            elif cursor.ins_type in {
                NCSInstructionType.LEQII,
                NCSInstructionType.LEQFF,
            }:
                self._stack.compare_lessthanorequal_op()

            elif cursor.ins_type == NCSInstructionType.SHLEFTII:
                self._stack.bitwise_leftshift_op()

            elif cursor.ins_type == NCSInstructionType.SHRIGHTII:
                self._stack.bitwise_rightshift_op()

            elif cursor.ins_type == NCSInstructionType.INCxBP:
                self._stack.increment_bp(cursor.args[0])

            elif cursor.ins_type == NCSInstructionType.DECxBP:
                self._stack.decrement_bp(cursor.args[0])

            elif cursor.ins_type == NCSInstructionType.INCxSP:
                self._stack.increment(cursor.args[0])

            elif cursor.ins_type == NCSInstructionType.DECxSP:
                self._stack.decrement(cursor.args[0])

            elif cursor.ins_type == NCSInstructionType.RSADDI:
                self._stack.add(DataType.INT, 0)

            elif cursor.ins_type == NCSInstructionType.RSADDF:
                self._stack.add(DataType.FLOAT, 0)

            elif cursor.ins_type == NCSInstructionType.RSADDS:
                self._stack.add(DataType.STRING, "")

            elif cursor.ins_type == NCSInstructionType.RSADDO:
                self._stack.add(DataType.OBJECT, 1)

            elif cursor.ins_type == NCSInstructionType.RSADDEFF:
                self._stack.add(DataType.EFFECT, 0)

            elif cursor.ins_type == NCSInstructionType.RSADDTAL:
                self._stack.add(DataType.TALENT, 0)

            elif cursor.ins_type == NCSInstructionType.RSADDLOC:
                self._stack.add(DataType.LOCATION, 0)

            elif cursor.ins_type == NCSInstructionType.RSADDEVT:
                self._stack.add(DataType.EVENT, 0)

            elif cursor.ins_type == NCSInstructionType.SAVEBP:
                self._stack.save_bp()

            elif cursor.ins_type == NCSInstructionType.RESTOREBP:
                self._stack.restore_bp()

            elif cursor.ins_type == NCSInstructionType.CPTOPBP:
                self._stack.copy_top_bp(cursor.args[0], cursor.args[1])

            elif cursor.ins_type == NCSInstructionType.CPDOWNBP:
                self._stack.copy_down_bp(cursor.args[0], cursor.args[1])

            elif cursor.ins_type == NCSInstructionType.NOP:
                # NOP is a no-operation instruction, do nothing
                pass

            elif cursor.ins_type == NCSInstructionType.JSR:
                index_return_to = index + 1
                return_to: NCSInstruction | None = self._ncs.instructions[index_return_to]
                self._returns.append((return_to, index_return_to))

            elif cursor.ins_type in {
                NCSInstructionType.JZ,
                NCSInstructionType.JNZ,
            }:
                jump_value = self._stack.pop()

            elif cursor.ins_type == NCSInstructionType.STORE_STATE:
                self.store_state(cursor)

            self.stack_snapshots.append(
                StackSnapshot(cursor, self._stack.state()),
            )

            # Control flow handling
            if cursor.ins_type == NCSInstructionType.RETN:
                return_info = self._returns.pop() if self._returns else None
                if return_info is None:
                    self._cursor = None
                    self._cursor_index = -1
                    break
                return_to, return_index = return_info
                if not isinstance(return_to, NCSInstruction):
                    msg = f"Return instruction RETN at index {index} has no return target"
                    raise RuntimeError(msg)
                self._set_cursor(return_to, return_index)
                continue

            if (
                cursor.ins_type == NCSInstructionType.JMP
                or (cursor.ins_type == NCSInstructionType.JZ and jump_value == 0)
                or (cursor.ins_type == NCSInstructionType.JNZ and jump_value != 0)
                or cursor.ins_type == NCSInstructionType.JSR
            ):
                if cursor.jump is None:
                    msg = f"Jump instruction {cursor.ins_type.name} at index {index} has no jump target"
                    raise RuntimeError(msg)
                jump_target = cursor.jump
                target_index = self._instruction_indices.get(id(jump_target))
                if target_index is None:
                    msg = f"Jump target for instruction {cursor.ins_type.name} not found in instruction table"
                    raise RuntimeError(msg)
                self._set_cursor(jump_target, target_index)
            else:
                # Move to next instruction
                if index + 1 >= len(self._ncs.instructions):
                    # End of program
                    break
                self._set_cursor(self._ncs.instructions[index + 1], index + 1)

    def store_state(self, cursor: NCSInstruction):
        self._stack.store_state()

        index = self._cursor_index
        tempcursor = self._ncs.instructions[index + 2]
        temp_index = index + 2

        block = []
        while tempcursor.ins_type != NCSInstructionType.RETN:
            block.append(tempcursor)
            temp_index += 1
            tempcursor = self._ncs.instructions[temp_index]

        self._stack.add(DataType.ACTION, ActionStackValue(block, self._stack.state()))

    def _set_cursor(self, instruction: NCSInstruction, index: int | None = None):
        """Set the current cursor and index, updating from precomputed lookup when needed."""
        if index is None:
            lookup_index = self._instruction_indices.get(id(instruction))
            if lookup_index is None:
                msg = "Instruction not present in current instruction table"
                raise RuntimeError(msg)
            index = lookup_index
        self._cursor = instruction
        self._cursor_index = index

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


class ObjectHeap:
    """Manages object references for non-primitive types in the NCS stack.

    This implements a handle-based object management system where non-primitive
    types (strings, objects, effects, events, locations, talents) are stored in
    a heap and referenced by 4-byte handles on the stack. This matches the
    behavior of the actual NWScript VM.

    Handle 0 is reserved for null/invalid references.
    Handles are allocated sequentially starting from 1.
    """

    def __init__(self):
        self._objects: dict[int, Any] = {}
        self._next_handle: int = 1
        self._handle_to_type: dict[int, DataType] = {}

    def allocate(self, value: Any, datatype: DataType) -> int:
        """Allocate a new object and return its handle.

        Args:
        ----
            value: The object value to store
            datatype: The type of the object

        Returns:
        -------
            int: Handle (4-byte unsigned integer) referencing the object
        """
        if value is None:
            return 0

        handle = self._next_handle
        self._next_handle += 1

        # Ensure handle doesn't overflow 32-bit unsigned integer
        if self._next_handle > 0xFFFFFFFF:
            msg = "Object heap handle overflow - too many objects allocated"
            raise OverflowError(msg)

        self._objects[handle] = value
        self._handle_to_type[handle] = datatype
        log.debug("ObjectHeap allocated handle=%s, datatype=%s, value=%s", handle, datatype.name, value)
        return handle

    def get(self, handle: int) -> Any:
        """Retrieve an object by its handle.

        Args:
        ----
            handle: The object handle

        Returns:
        -------
            Any: The stored object, or None if handle is 0 or invalid

        Raises:
        ------
            KeyError: If handle is not 0 and doesn't exist in heap
        """
        if handle == 0:
            return None

        if handle not in self._objects:
            log.error("ObjectHeap.get failed: invalid handle=%s", handle)
            msg = f"Invalid object handle: {handle}"
            raise KeyError(msg)

        value = self._objects[handle]
        log.debug("ObjectHeap retrieved handle=%s, value=%s", handle, value)
        return value

    def get_type(self, handle: int) -> DataType | None:
        """Get the type of an object by its handle.

        Args:
        ----
            handle: The object handle

        Returns:
        -------
            DataType | None: The object type, or None if handle is 0 or invalid
        """
        if handle == 0:
            return None
        return self._handle_to_type.get(handle)

    def release(self, handle: int):
        """Release an object handle and free its memory.

        Args:
        ----
            handle: The object handle to release
        """
        if handle == 0:
            return

        if handle in self._objects:
            value = self._objects.pop(handle)
            self._handle_to_type.pop(handle, None)
            log.debug("ObjectHeap released handle=%s, value=%s", handle, value)
        else:
            log.warning("ObjectHeap.release called on invalid handle=%s", handle)

    def clear(self):
        """Clear all objects from the heap."""
        count = len(self._objects)
        self._objects.clear()
        self._handle_to_type.clear()
        self._next_handle = 1
        log.debug("ObjectHeap cleared, released %s objects", count)

    def size(self) -> int:
        """Get the number of objects currently in the heap.

        Returns:
        -------
            int: Number of allocated objects
        """
        return len(self._objects)


class StackV2:
    """Byte-accurate stack implementation for NCS bytecode execution.

    This class simulates the NWScript VM stack using a bytearray to store
    values exactly as they would appear in the actual VM. Primitive types
    (int, float) are stored inline as 4-byte values. Non-primitive types
    (strings, objects, effects, etc.) are stored as 4-byte handles that
    reference objects in an ObjectHeap.
    """

    def __init__(self):
        self._stack: bytearray = bytearray()
        self._base_pointer: int = 0
        self._base_pointer_saved: list[int] = []
        self._object_heap: ObjectHeap = ObjectHeap()

    def state(self) -> bytearray:
        return copy(self._stack)

    def object_heap(self) -> ObjectHeap:
        """Get the object heap for this stack.

        Returns:
        -------
            ObjectHeap: The object heap managing non-primitive values
        """
        return self._object_heap

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

        Primitive types (int, float) are stored directly as 4-byte values.
        Non-primitive types are allocated in the object heap and their handle
        is stored on the stack.

        Args:
        ----
            datatype: The type of data being added
            value: The value to add

        Raises:
        ------
            ValueError: If value type doesn't match datatype
            TypeError: If datatype is not supported
            OverflowError: If object heap is full
        """
        if datatype == DataType.INT:
            if not isinstance(value, int):
                log.error("StackV2.add type mismatch: expected int, got %s, value=%s", type(value).__name__, value)
                msg = f"Expected int value for INT type, got {type(value).__name__}: {value}"
                raise ValueError(msg)
            self._stack.extend(struct.pack("i", value))
            log.debug("StackV2 added INT: %s (bytes: %s)", value, len(self._stack))

        elif datatype == DataType.FLOAT:
            if not isinstance(value, (int, float)):
                log.error("StackV2.add type mismatch: expected numeric, got %s, value=%s", type(value).__name__, value)
                msg = f"Expected numeric value for FLOAT type, got {type(value).__name__}: {value}"
                raise ValueError(msg)
            float_value = float(value)
            self._stack.extend(struct.pack("f", float_value))
            log.debug("StackV2 added FLOAT: %s (bytes: %s)", float_value, len(self._stack))

        elif datatype in {DataType.STRING, DataType.OBJECT, DataType.EFFECT,
                          DataType.EVENT, DataType.LOCATION, DataType.TALENT}:
            # Non-primitive types: allocate in object heap, store handle on stack
            handle = self._object_heap.allocate(value, datatype)
            self._stack.extend(struct.pack("I", handle))
            log.debug("StackV2 added %s: handle=%s, value=%s (bytes: %s)",
                     datatype.name, handle, value, len(self._stack))

        elif datatype == DataType.ACTION:
            # Actions are special non-primitive types used for delayed execution
            handle = self._object_heap.allocate(value, datatype)
            self._stack.extend(struct.pack("I", handle))
            log.debug("StackV2 added ACTION: handle=%s (bytes: %s)", handle, len(self._stack))

        elif datatype == DataType.VECTOR:
            # Vectors are stored as three consecutive floats (12 bytes)
            if not isinstance(value, (tuple, list, Vector3)):
                log.error("StackV2.add type mismatch: expected vector-like, got %s, value=%s",
                         type(value).__name__, value)
                msg = f"Expected vector-like value for VECTOR type, got {type(value).__name__}: {value}"
                raise ValueError(msg)

            # Extract x, y, z components
            if isinstance(value, Vector3):
                x, y, z = value.x, value.y, value.z
            else:
                if len(value) != 3:
                    log.error("StackV2.add vector length error: expected 3 components, got %s", len(value))
                    msg = f"VECTOR requires 3 components, got {len(value)}"
                    raise ValueError(msg)
                x, y, z = value[0], value[1], value[2]

            # Store as three floats
            self._stack.extend(struct.pack("fff", float(x), float(y), float(z)))
            log.debug("StackV2 added VECTOR: (%s, %s, %s) (bytes: %s)", x, y, z, len(self._stack))

        else:
            log.error("StackV2.add unsupported datatype: %s", datatype)
            msg = f"Unsupported datatype for StackV2: {datatype}"
            raise TypeError(msg)

    def pop(self, datatype: DataType) -> Any:
        """Pop a value from the stack with proper type handling.

        Args:
        ----
            datatype: The type of data being popped

        Returns:
        -------
            Any: The popped value

        Raises:
        ------
            IndexError: If stack underflow
            ValueError: If datatype is not supported
        """
        if datatype == DataType.INT:
            if len(self._stack) < 4:
                log.error("StackV2.pop stack underflow: INT requires 4 bytes, have %s", len(self._stack))
                msg = f"Stack underflow: INT requires 4 bytes, only {len(self._stack)} available"
                raise IndexError(msg)
            value_bytes = self._stack[-4:]
            self._stack = self._stack[:-4]
            value = struct.unpack("i", value_bytes)[0]
            log.debug("StackV2 popped INT: %s (bytes remaining: %s)", value, len(self._stack))
            return value

        if datatype == DataType.FLOAT:
            if len(self._stack) < 4:
                log.error("StackV2.pop stack underflow: FLOAT requires 4 bytes, have %s", len(self._stack))
                msg = f"Stack underflow: FLOAT requires 4 bytes, only {len(self._stack)} available"
                raise IndexError(msg)
            value_bytes = self._stack[-4:]
            self._stack = self._stack[:-4]
            value = struct.unpack("f", value_bytes)[0]
            log.debug("StackV2 popped FLOAT: %s (bytes remaining: %s)", value, len(self._stack))
            return value

        if datatype in {DataType.STRING, DataType.OBJECT, DataType.EFFECT,
                        DataType.EVENT, DataType.LOCATION, DataType.TALENT, DataType.ACTION}:
            if len(self._stack) < 4:
                log.error("StackV2.pop stack underflow: %s requires 4 bytes, have %s",
                         datatype.name, len(self._stack))
                msg = f"Stack underflow: {datatype.name} requires 4 bytes, only {len(self._stack)} available"
                raise IndexError(msg)
            handle_bytes = self._stack[-4:]
            self._stack = self._stack[:-4]
            handle = struct.unpack("I", handle_bytes)[0]
            value = self._object_heap.get(handle)
            log.debug("StackV2 popped %s: handle=%s, value=%s (bytes remaining: %s)",
                     datatype.name, handle, value, len(self._stack))
            return value

        if datatype == DataType.VECTOR:
            if len(self._stack) < 12:
                log.error("StackV2.pop stack underflow: VECTOR requires 12 bytes, have %s", len(self._stack))
                msg = f"Stack underflow: VECTOR requires 12 bytes, only {len(self._stack)} available"
                raise IndexError(msg)
            vector_bytes = self._stack[-12:]
            self._stack = self._stack[:-12]
            x, y, z = struct.unpack("fff", vector_bytes)
            value = Vector3(x, y, z)
            log.debug("StackV2 popped VECTOR: %s (bytes remaining: %s)", value, len(self._stack))
            return value

        log.error("StackV2.pop unsupported datatype: %s", datatype)
        msg = f"Unsupported datatype for StackV2.pop: {datatype}"
        raise ValueError(msg)

    def peek(self, datatype: DataType, offset: int = 0) -> Any:
        """Peek at a value on the stack without removing it.

        Args:
        ----
            datatype: The type of data to peek at
            offset: Byte offset from top of stack (0 = top, 4 = second value for 4-byte types)

        Returns:
        -------
            Any: The value at the specified offset

        Raises:
        ------
            IndexError: If offset is out of bounds
            ValueError: If datatype is not supported
        """
        type_size = datatype.size()
        start_pos = len(self._stack) - type_size - offset

        if start_pos < 0:
            log.error("StackV2.peek out of bounds: offset=%s, type_size=%s, stack_size=%s",
                     offset, type_size, len(self._stack))
            msg = f"Stack peek out of bounds: offset {offset}, type size {type_size}, stack size {len(self._stack)}"
            raise IndexError(msg)

        if datatype == DataType.INT:
            value_bytes = self._stack[start_pos:start_pos + 4]
            value = struct.unpack("i", value_bytes)[0]
            log.debug("StackV2 peeked INT at offset %s: %s", offset, value)
            return value

        if datatype == DataType.FLOAT:
            value_bytes = self._stack[start_pos:start_pos + 4]
            value = struct.unpack("f", value_bytes)[0]
            log.debug("StackV2 peeked FLOAT at offset %s: %s", offset, value)
            return value

        if datatype in {DataType.STRING, DataType.OBJECT, DataType.EFFECT,
                        DataType.EVENT, DataType.LOCATION, DataType.TALENT, DataType.ACTION}:
            handle_bytes = self._stack[start_pos:start_pos + 4]
            handle = struct.unpack("I", handle_bytes)[0]
            value = self._object_heap.get(handle)
            log.debug("StackV2 peeked %s at offset %s: handle=%s, value=%s",
                     datatype.name, offset, handle, value)
            return value

        if datatype == DataType.VECTOR:
            vector_bytes = self._stack[start_pos:start_pos + 12]
            x, y, z = struct.unpack("fff", vector_bytes)
            value = Vector3(x, y, z)
            log.debug("StackV2 peeked VECTOR at offset %s: %s", offset, value)
            return value

        log.error("StackV2.peek unsupported datatype: %s", datatype)
        msg = f"Unsupported datatype for StackV2.peek: {datatype}"
        raise ValueError(msg)

    def clear(self):
        """Clear the stack and object heap."""
        stack_size = len(self._stack)
        heap_size = self._object_heap.size()
        self._stack.clear()
        self._object_heap.clear()
        self._base_pointer = 0
        self._base_pointer_saved.clear()
        log.debug("StackV2 cleared: freed %s bytes, %s objects", stack_size, heap_size)


class Stack:
    def __init__(self):
        self._stack: list[StackObject] = []
        self._bp: int = 0
        self._bp_buffer: list[int] = []
        self._global_bp: int = 0  # BP value for accessing globals (set after global initialization)

    def state(self) -> list:
        return copy(self._stack)

    def add(self, data_type: DataType, value: Any):
        self._stack.append(StackObject(data_type, value))

    def _stack_index(self, offset: int) -> int:
        """Convert a stack offset to an actual list index.

        Args:
        ----
            offset: Stack offset measured in bytes from the stack top.
                Positive and negative values are both supported. A value of
                ``4`` or ``-4`` refers to the element at the top of the stack,
                ``8`` or ``-8`` to the next element down, and so on.

        Returns:
        -------
            int: Index of the target element within the underlying list.

        Raises:
        ------
            ValueError: If the offset is zero, not a multiple of four, or
                points outside the current stack contents.
        """
        if offset == 0:
            msg = "Stack offset of zero is not valid"
            raise ValueError(msg)
        if offset % 4 != 0:
            msg = f"Stack offset must be a multiple of 4 bytes, got {offset}"
            raise ValueError(msg)
        if not self._stack:
            msg = "Cannot resolve stack offset on an empty stack"
            raise ValueError(msg)

        remaining = abs(offset)
        index = -1  # Start from the top of the stack

        while True:
            if -index > len(self._stack):
                msg = f"Stack offset {offset} is out of range"
                raise ValueError(msg)

            element = self._stack[index]
            element_size = element.data_type.size()
            if element_size <= 0:
                msg = f"Unsupported element size {element_size} for {element.data_type}"
                raise ValueError(msg)

            if remaining <= element_size:
                return index

            remaining -= element_size
            index -= 1

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
        if size <= 0 or size % 4 != 0:
            msg = f"Size must be a positive multiple of 4, got {size}"
            raise ValueError(msg)
        if offset == 0 or offset % 4 != 0:
            msg = f"Offset must be a non-zero multiple of 4, got {offset}"
            raise ValueError(msg)
        if not self._stack:
            msg = "Cannot copy from an empty stack"
            raise IndexError(msg)

        offset_abs = abs(offset)
        total_bytes = sum(obj.data_type.size() for obj in self._stack)
        if offset_abs > total_bytes:
            msg = f"Offset {offset} exceeds stack size {total_bytes}"
            raise IndexError(msg)

        lower_bound = offset_abs - size

        copied: list[StackObject] = []
        accumulated = 0

        for index in range(len(self._stack) - 1, -1, -1):
            element = self._stack[index]
            accumulated += element.data_type.size()
            if accumulated <= lower_bound:
                continue
            if accumulated > offset_abs:
                break
            copied.append(copy(element))

        if not copied or sum(obj.data_type.size() for obj in copied) != size:
            msg = (
                f"Unable to copy block at offset {offset} with size {size}; "
                "stack contents do not align with requested segment"
            )
            raise IndexError(msg)

        copied.reverse()
        self._stack.extend(copied)

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
            ValueError: If offset is not a multiple of 4 bytes
        """
        if offset == 0:
            return

        if offset > 0:
            if offset % 4 != 0:
                msg = f"Stack growth offset must be multiple of 4, got {offset}"
                raise ValueError(msg)
            words = offset // 4
            for _ in range(words):
                self._stack.append(StackObject(DataType.INT, 0))
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
        prev_bp = self._bp
        # BP should point to the saved BP value, not after it
        # This allows negative offsets to correctly access globals and locals
        new_bp = self.stack_pointer()
        self._stack.append(StackObject(DataType.INT, prev_bp))
        self._bp_buffer.append(prev_bp)
        # If this is the first SAVEBP (entering main from global scope), save the global BP
        if self._global_bp == 0 and prev_bp == 0:
            self._global_bp = new_bp
        # BP points to where the saved BP is stored, not after it
        self._bp = new_bp

    def restore_bp(self):
        if not self._stack:
            msg = "Cannot restore base pointer from an empty stack"
            raise IndexError(msg)
        saved_bp = self._stack.pop()
        if saved_bp.data_type != DataType.INT:
            msg = (
                "Encountered non-integer value while restoring base pointer; "
                f"found {saved_bp.data_type}"
            )
            raise TypeError(msg)
        if not isinstance(saved_bp.value, int):
            msg = (
                "Base pointer restore requires integer value "
                f"but received {type(saved_bp.value)}"
            )
            raise TypeError(msg)
        self._bp = saved_bp.value
        if self._bp_buffer:
            self._bp_buffer.pop()

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
        if isinstance(value1.value, (int, float)) and isinstance(value2.value, (int, float)):
            result = value2.value + value1.value
            self._stack.pop()
            self._stack.pop()
            if value2.data_type == DataType.INT:
                self.add(DataType.INT, int(result))
            elif value2.data_type == DataType.FLOAT:
                self.add(DataType.FLOAT, float(result))
            else:
                self.add(DataType.FLOAT if isinstance(result, float) else DataType.INT, result)
            return
        if isinstance(value1.value, str) and isinstance(value2.value, str):
            result = value2.value + value1.value
            self._stack.pop()
            self._stack.pop()
            self.add(DataType.STRING, result)
            return
        msg = (
            "Addition requires numeric or string operands; got "
            f"{value2.data_type.name} and {value1.data_type.name}"
        )
        raise TypeError(msg)

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
