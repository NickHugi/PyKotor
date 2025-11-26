"""This module handles NCS (NWScript Compiled Script) bytecode files for KotOR.

NCS files contain compiled NWScript bytecode instructions that are executed by the game engine.
The bytecode uses a stack-based virtual machine with instructions for arithmetic, logic, control flow,
function calls, and stack manipulation. Each instruction consists of a bytecode opcode and a qualifier
that specifies operand types.

References:
----------
    vendor/reone/include/reone/script/format/ncsreader.h:29-47 - NcsReader class
    vendor/reone/src/libs/script/format/ncsreader.cpp:28-190 - Complete NCS reading implementation
    vendor/xoreos/src/aurora/nwscript/ncsfile.h:86-280 - NCSFile class and instruction types
    vendor/xoreos/src/aurora/nwscript/ncsfile.cpp:49-1649 - Complete NCS execution engine
    vendor/Kotor.NET/Kotor.NET/Formats/KotorNCS/NCS.cs:9-799 - NCS instruction classes
    vendor/Kotor.NET/Kotor.NET/Formats/KotorNCS/NCSReader.cs:11-31 - NCS reader interface
    https://github.com/xoreos/xoreos-docs - Torlack's NCS specification (mirrored)
    
Binary Format:
-------------
    Header (9 bytes):
        Offset | Size | Type   | Description
        -------|------|--------|-------------
        0x00   | 4    | char[] | File Type ("NCS ")
        0x04   | 4    | char[] | File Version ("V1.0")
        0x08   | 1    | uint8  | First instruction bytecode
        
    Instructions (variable length):
        Each instruction consists of:
        - Bytecode (1 byte): Opcode identifying instruction type
        - Qualifier (1 byte): Type qualifier for operands (e.g., INT, FLOAT, INT_INT)
        - Arguments (variable): Instruction-specific arguments (offsets, constants, jump targets)
        
        Reference: reone/ncsreader.cpp:42-190, xoreos/ncsfile.cpp:194-1649
    
    Instruction Types:
    -----------------
        Stack Operations: CPDOWNSP, CPTOPSP, CPDOWNBP, CPTOPBP, MOVSP, RSADDx
        Constants: CONSTI, CONSTF, CONSTS, CONSTO
        Arithmetic: ADDxx, SUBxx, MULxx, DIVxx, MODxx, NEGx
        Comparison: EQUALxx, NEQUALxx, GTxx, GEQxx, LTxx, LEQxx
        Logic: LOGANDxx, LOGORxx, BOOLANDxx, NOTx
        Bitwise: INCORxx, EXCORxx, SHLEFTxx, SHRIGHTxx, USHRIGHTxx, COMPx
        Control Flow: JMP, JSR, JZ, JNZ, RETN
        Function Calls: ACTION
        Stack Management: SAVEBP, RESTOREBP, STORE_STATE, DESTRUCT
        Increment/Decrement: INCxSP, DECxSP, INCxBP, DECxBP
        
        Reference: reone/ncsreader.cpp:52-182, Kotor.NET/NCS.cs:725-798
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum, IntEnum
from typing import TYPE_CHECKING, Any, NamedTuple

from pykotor.resource.formats._base import ComparableMixin

if TYPE_CHECKING:
    import os

    from pykotor.common.misc import Game


class NCSInstructionTypeValue(NamedTuple):
    byte_code: int
    qualifier: int


class NCSByteCode(IntEnum):
    RESERVED = 0x00  # Reserved/unknown opcode found in some compiled scripts
    CPDOWNSP = 0x01
    RSADDx = 0x02
    CPTOPSP = 0x03
    CONSTx = 0x04
    ACTION = 0x05
    NOP = 0x2D
    LOGANDxx = 0x06
    LOGORxx = 0x07
    INCORxx = 0x08
    EXCORxx = 0x09
    BOOLANDxx = 0x0A
    EQUALxx = 0x0B
    NEQUALxx = 0x0C
    GEQxx = 0x0D
    GTxx = 0x0E
    LTxx = 0x0F
    LEQxx = 0x10
    SHLEFTxx = 0x11
    SHRIGHTxx = 0x12
    USHRIGHTxx = 0x13
    ADDxx = 0x14
    SUBxx = 0x15
    MULxx = 0x16
    DIVxx = 0x17
    MODxx = 0x18
    NEGx = 0x19
    COMPx = 0x1A
    MOVSP = 0x1B
    JMP = 0x1D
    JSR = 0x1E
    JZ = 0x1F
    RETN = 0x20
    DESTRUCT = 0x21
    NOTx = 0x22
    DECxSP = 0x23
    INCxSP = 0x24
    JNZ = 0x25
    CPDOWNBP = 0x26
    CPTOPBP = 0x27
    DECxBP = 0x28
    INCxBP = 0x29
    SAVEBP = 0x2A
    RESTOREBP = 0x2B
    STORE_STATE = 0x2C
    NOP2 = 0x2D


class NCSInstructionQualifier(IntEnum):
    Int = 0x03
    Float = 0x04
    String = 0x05
    Object = 0x06
    Effect = 0x10
    Event = 0x11
    Location = 0x12
    Talent = 0x13
    IntInt = 0x20
    FloatFloat = 0x21
    ObjectObject = 0x22
    StringString = 0x23
    StructStruct = 0x24
    IntFloat = 0x25
    FloatInt = 0x26
    EffectEffect = 0x30
    EventEvent = 0x31
    LocationLocation = 0x32
    TalentTalent = 0x33
    VectorVector = 0x3A
    VectorFloat = 0x3B
    FloatVector = 0x3C


class NCSInstructionType(Enum):
    RESERVED = NCSInstructionTypeValue(NCSByteCode.RESERVED, 0x00)  # Unknown/reserved instruction
    RESERVED_01 = NCSInstructionTypeValue(NCSByteCode.RESERVED, 0x01)  # Variant with qualifier 0x01
    NOP = NCSInstructionTypeValue(NCSByteCode.NOP, 0x00)
    CPDOWNSP = NCSInstructionTypeValue(NCSByteCode.CPDOWNSP, 0x01)
    RSADDI = NCSInstructionTypeValue(NCSByteCode.RSADDx, NCSInstructionQualifier.Int)
    RSADDF = NCSInstructionTypeValue(NCSByteCode.RSADDx, NCSInstructionQualifier.Float)
    RSADDS = NCSInstructionTypeValue(NCSByteCode.RSADDx, NCSInstructionQualifier.String)
    RSADDO = NCSInstructionTypeValue(NCSByteCode.RSADDx, NCSInstructionQualifier.Object)
    RSADDEFF = NCSInstructionTypeValue(NCSByteCode.RSADDx, NCSInstructionQualifier.Effect)
    RSADDEVT = NCSInstructionTypeValue(NCSByteCode.RSADDx, NCSInstructionQualifier.Event)
    RSADDLOC = NCSInstructionTypeValue(NCSByteCode.RSADDx, NCSInstructionQualifier.Location)
    RSADDTAL = NCSInstructionTypeValue(NCSByteCode.RSADDx, NCSInstructionQualifier.Talent)
    CPTOPSP = NCSInstructionTypeValue(NCSByteCode.CPTOPSP, 0x01)
    CONSTI = NCSInstructionTypeValue(NCSByteCode.CONSTx, NCSInstructionQualifier.Int)
    CONSTF = NCSInstructionTypeValue(NCSByteCode.CONSTx, NCSInstructionQualifier.Float)
    CONSTS = NCSInstructionTypeValue(NCSByteCode.CONSTx, NCSInstructionQualifier.String)
    CONSTO = NCSInstructionTypeValue(NCSByteCode.CONSTx, NCSInstructionQualifier.Object)
    ACTION = NCSInstructionTypeValue(NCSByteCode.ACTION, 0x00)
    LOGANDII = NCSInstructionTypeValue(NCSByteCode.LOGANDxx, NCSInstructionQualifier.IntInt)
    LOGORII = NCSInstructionTypeValue(NCSByteCode.LOGORxx, NCSInstructionQualifier.IntInt)
    INCORII = NCSInstructionTypeValue(NCSByteCode.INCORxx, NCSInstructionQualifier.IntInt)
    EXCORII = NCSInstructionTypeValue(NCSByteCode.EXCORxx, NCSInstructionQualifier.IntInt)
    BOOLANDII = NCSInstructionTypeValue(NCSByteCode.BOOLANDxx, NCSInstructionQualifier.IntInt)
    EQUALII = NCSInstructionTypeValue(NCSByteCode.EQUALxx, NCSInstructionQualifier.IntInt)
    EQUALFF = NCSInstructionTypeValue(NCSByteCode.EQUALxx, NCSInstructionQualifier.FloatFloat)
    EQUALSS = NCSInstructionTypeValue(NCSByteCode.EQUALxx, NCSInstructionQualifier.StringString)
    EQUALOO = NCSInstructionTypeValue(NCSByteCode.EQUALxx, NCSInstructionQualifier.ObjectObject)
    EQUALTT = NCSInstructionTypeValue(NCSByteCode.EQUALxx, NCSInstructionQualifier.StructStruct)
    EQUALEFFEFF = NCSInstructionTypeValue(NCSByteCode.EQUALxx, NCSInstructionQualifier.EffectEffect)
    EQUALEVTEVT = NCSInstructionTypeValue(NCSByteCode.EQUALxx, NCSInstructionQualifier.EventEvent)
    EQUALLOCLOC = NCSInstructionTypeValue(NCSByteCode.EQUALxx, NCSInstructionQualifier.LocationLocation)
    EQUALTALTAL = NCSInstructionTypeValue(NCSByteCode.EQUALxx, NCSInstructionQualifier.TalentTalent)
    NEQUALII = NCSInstructionTypeValue(NCSByteCode.NEQUALxx, NCSInstructionQualifier.IntInt)
    NEQUALFF = NCSInstructionTypeValue(NCSByteCode.NEQUALxx, NCSInstructionQualifier.FloatFloat)
    NEQUALSS = NCSInstructionTypeValue(NCSByteCode.NEQUALxx, NCSInstructionQualifier.StringString)
    NEQUALOO = NCSInstructionTypeValue(NCSByteCode.NEQUALxx, NCSInstructionQualifier.ObjectObject)
    NEQUALTT = NCSInstructionTypeValue(NCSByteCode.NEQUALxx, NCSInstructionQualifier.StructStruct)
    NEQUALEFFEFF = NCSInstructionTypeValue(NCSByteCode.NEQUALxx, NCSInstructionQualifier.EffectEffect)
    NEQUALEVTEVT = NCSInstructionTypeValue(NCSByteCode.NEQUALxx, NCSInstructionQualifier.EventEvent)
    NEQUALLOCLOC = NCSInstructionTypeValue(NCSByteCode.NEQUALxx, NCSInstructionQualifier.LocationLocation)
    NEQUALTALTAL = NCSInstructionTypeValue(NCSByteCode.NEQUALxx, NCSInstructionQualifier.TalentTalent)
    GEQII = NCSInstructionTypeValue(NCSByteCode.GEQxx, NCSInstructionQualifier.IntInt)
    GEQFF = NCSInstructionTypeValue(NCSByteCode.GEQxx, NCSInstructionQualifier.FloatFloat)
    GTII = NCSInstructionTypeValue(NCSByteCode.GTxx, NCSInstructionQualifier.IntInt)
    GTFF = NCSInstructionTypeValue(NCSByteCode.GTxx, NCSInstructionQualifier.FloatFloat)
    LTII = NCSInstructionTypeValue(NCSByteCode.LTxx, NCSInstructionQualifier.IntInt)
    LTFF = NCSInstructionTypeValue(NCSByteCode.LTxx, NCSInstructionQualifier.FloatFloat)
    LEQII = NCSInstructionTypeValue(NCSByteCode.LEQxx, NCSInstructionQualifier.IntInt)
    LEQFF = NCSInstructionTypeValue(NCSByteCode.LEQxx, NCSInstructionQualifier.FloatFloat)
    SHLEFTII = NCSInstructionTypeValue(NCSByteCode.SHLEFTxx, NCSInstructionQualifier.IntInt)
    SHRIGHTII = NCSInstructionTypeValue(NCSByteCode.SHRIGHTxx, NCSInstructionQualifier.IntInt)
    USHRIGHTII = NCSInstructionTypeValue(NCSByteCode.USHRIGHTxx, NCSInstructionQualifier.IntInt)
    ADDII = NCSInstructionTypeValue(NCSByteCode.ADDxx, NCSInstructionQualifier.IntInt)
    ADDIF = NCSInstructionTypeValue(NCSByteCode.ADDxx, NCSInstructionQualifier.IntFloat)
    ADDFI = NCSInstructionTypeValue(NCSByteCode.ADDxx, NCSInstructionQualifier.FloatInt)
    ADDFF = NCSInstructionTypeValue(NCSByteCode.ADDxx, NCSInstructionQualifier.FloatFloat)
    ADDSS = NCSInstructionTypeValue(NCSByteCode.ADDxx, NCSInstructionQualifier.StringString)
    ADDVV = NCSInstructionTypeValue(NCSByteCode.ADDxx, NCSInstructionQualifier.VectorVector)
    SUBII = NCSInstructionTypeValue(NCSByteCode.SUBxx, NCSInstructionQualifier.IntInt)
    SUBIF = NCSInstructionTypeValue(NCSByteCode.SUBxx, NCSInstructionQualifier.IntFloat)
    SUBFI = NCSInstructionTypeValue(NCSByteCode.SUBxx, NCSInstructionQualifier.FloatInt)
    SUBFF = NCSInstructionTypeValue(NCSByteCode.SUBxx, NCSInstructionQualifier.FloatFloat)
    SUBVV = NCSInstructionTypeValue(NCSByteCode.SUBxx, NCSInstructionQualifier.VectorVector)
    MULII = NCSInstructionTypeValue(NCSByteCode.MULxx, NCSInstructionQualifier.IntInt)
    MULIF = NCSInstructionTypeValue(NCSByteCode.MULxx, NCSInstructionQualifier.IntFloat)
    MULFI = NCSInstructionTypeValue(NCSByteCode.MULxx, NCSInstructionQualifier.FloatInt)
    MULFF = NCSInstructionTypeValue(NCSByteCode.MULxx, NCSInstructionQualifier.FloatFloat)
    MULVF = NCSInstructionTypeValue(NCSByteCode.MULxx, NCSInstructionQualifier.VectorFloat)
    MULFV = NCSInstructionTypeValue(NCSByteCode.MULxx, NCSInstructionQualifier.FloatVector)
    DIVII = NCSInstructionTypeValue(NCSByteCode.DIVxx, NCSInstructionQualifier.IntInt)
    DIVIF = NCSInstructionTypeValue(NCSByteCode.DIVxx, NCSInstructionQualifier.IntFloat)
    DIVFI = NCSInstructionTypeValue(NCSByteCode.DIVxx, NCSInstructionQualifier.FloatInt)
    DIVFF = NCSInstructionTypeValue(NCSByteCode.DIVxx, NCSInstructionQualifier.FloatFloat)
    DIVVF = NCSInstructionTypeValue(NCSByteCode.DIVxx, NCSInstructionQualifier.VectorFloat)
    DIVFV = NCSInstructionTypeValue(NCSByteCode.DIVxx, NCSInstructionQualifier.FloatVector)
    MODII = NCSInstructionTypeValue(NCSByteCode.MODxx, NCSInstructionQualifier.IntInt)
    NEGI = NCSInstructionTypeValue(NCSByteCode.NEGx, NCSInstructionQualifier.Int)
    NEGF = NCSInstructionTypeValue(NCSByteCode.NEGx, NCSInstructionQualifier.Float)
    COMPI = NCSInstructionTypeValue(NCSByteCode.COMPx, NCSInstructionQualifier.Int)
    MOVSP = NCSInstructionTypeValue(NCSByteCode.MOVSP, 0x00)
    JMP = NCSInstructionTypeValue(NCSByteCode.JMP, 0x00)
    JSR = NCSInstructionTypeValue(NCSByteCode.JSR, 0x00)
    JZ = NCSInstructionTypeValue(NCSByteCode.JZ, 0x00)
    RETN = NCSInstructionTypeValue(NCSByteCode.RETN, 0x00)
    DESTRUCT = NCSInstructionTypeValue(NCSByteCode.DESTRUCT, 0x01)
    NOTI = NCSInstructionTypeValue(NCSByteCode.NOTx, NCSInstructionQualifier.Int)
    DECxSP = NCSInstructionTypeValue(NCSByteCode.DECxSP, NCSInstructionQualifier.Int)
    INCxSP = NCSInstructionTypeValue(NCSByteCode.INCxSP, NCSInstructionQualifier.Int)
    JNZ = NCSInstructionTypeValue(NCSByteCode.JNZ, 0x00)
    CPDOWNBP = NCSInstructionTypeValue(NCSByteCode.CPDOWNBP, 0x01)
    CPTOPBP = NCSInstructionTypeValue(NCSByteCode.CPTOPBP, 0x01)
    DECxBP = NCSInstructionTypeValue(NCSByteCode.DECxBP, NCSInstructionQualifier.Int)
    INCxBP = NCSInstructionTypeValue(NCSByteCode.INCxBP, NCSInstructionQualifier.Int)
    SAVEBP = NCSInstructionTypeValue(NCSByteCode.SAVEBP, 0x00)
    RESTOREBP = NCSInstructionTypeValue(NCSByteCode.RESTOREBP, 0x00)
    STORE_STATE = NCSInstructionTypeValue(NCSByteCode.STORE_STATE, 0x10)
    NOP2 = NCSInstructionTypeValue(NCSByteCode.NOP2, 0x00)


class NCS(ComparableMixin):
    """Represents a compiled NWScript bytecode program.
    
    NCS contains a sequence of bytecode instructions that implement NWScript logic.
    Instructions are executed sequentially by a stack-based virtual machine, with
    control flow instructions (JMP, JSR, JZ, JNZ) allowing jumps to other instructions.
    
    References:
    ----------
        vendor/reone/include/reone/script/program.h - ScriptProgram class
        vendor/reone/src/libs/script/format/ncsreader.cpp:34-40 (program creation)
        vendor/xoreos/src/aurora/nwscript/ncsfile.h:86-280 - NCSFile class
        vendor/Kotor.NET/Kotor.NET/Formats/KotorNCS/NCS.cs:9-17 - NCS class
        
    Attributes:
    ----------
        instructions: List of NCSInstruction objects making up the program
            Reference: reone/script/program.h (instructions vector)
            Reference: reone/ncsreader.cpp:187 (_program->add instruction)
            Reference: xoreos/ncsfile.h:184 (_script stream, instructions parsed on-demand)
            Reference: Kotor.NET/NCS.cs:11 (Instructions List property)
            Instructions are executed sequentially, with jumps allowing control flow
            Each instruction has an offset, type, arguments, and optional jump target
    """
    COMPARABLE_SEQUENCE_FIELDS = ("instructions",)

    def __init__(self):
        # vendor/reone/src/libs/script/format/ncsreader.cpp:34
        # vendor/xoreos/src/aurora/nwscript/ncsfile.h:184
        # vendor/Kotor.NET/Kotor.NET/Formats/KotorNCS/NCS.cs:11
        # List of bytecode instructions making up the compiled script
        self.instructions: list[NCSInstruction] = []

    def __eq__(self, other):
        if not isinstance(other, NCS):
            return NotImplemented

        if len(self.instructions) != len(other.instructions):
            return False

        self_index_map = {id(instruction): idx for idx, instruction in enumerate(self.instructions)}
        other_index_map = {id(instruction): idx for idx, instruction in enumerate(other.instructions)}

        for instruction, other_instruction in zip(self.instructions, other.instructions):
            if instruction.ins_type != other_instruction.ins_type:
                return False

            if instruction.args != other_instruction.args:
                return False

            if (instruction.jump is None) != (other_instruction.jump is None):
                return False

            if instruction.jump is not None:
                jump_target = id(instruction.jump)
                other_jump_target = id(other_instruction.jump)

                if jump_target not in self_index_map or other_jump_target not in other_index_map:
                    return False

                if self_index_map[jump_target] != other_index_map[other_jump_target]:
                    return False

        return True

    def __hash__(self):
        index_map = {id(instruction): idx for idx, instruction in enumerate(self.instructions)}
        signature: list[tuple[Any, tuple[Any, ...], int | None]] = []
        for instruction in self.instructions:
            jump_index: int | None = None
            if instruction.jump is not None:
                jump_index = index_map.get(id(instruction.jump))
            signature.append(
                (
                    instruction.ins_type,
                    tuple(instruction.args),
                    jump_index,
                ),
            )
        return hash(tuple(signature))

    def __repr__(self) -> str:
        """Returns a detailed string representation of the NCS object."""
        if not self.instructions:
            return "NCS(instructions=[])"

        # Show first few instructions for compact representation
        max_preview: int = 3
        inst_reprs: list[str] = []
        for i, inst in enumerate(self.instructions[:max_preview]):
            jump_idx = self.instructions.index(inst.jump) if inst.jump else None
            jump_str = f"->#{jump_idx}" if jump_idx is not None else ""
            args_str = f"({', '.join(repr(arg) for arg in inst.args)})" if inst.args else ""
            inst_reprs.append(f"#{i}: {inst.ins_type.name}{args_str}{jump_str}")

        preview = "; ".join(inst_reprs)
        if len(self.instructions) > max_preview:
            preview += f"; ... ({len(self.instructions) - max_preview} more)"

        return f"NCS({preview})"

    def __str__(self) -> str:
        """Returns a human-readable string representation with all instructions."""
        if not self.instructions:
            return "NCS (empty - no instructions)"

        lines = [f"NCS with {len(self.instructions)} instructions:"]
        for i, inst in enumerate(self.instructions):
            # Find jump target index if present
            jump_idx: int | str | None = None
            if inst.jump:
                try:
                    jump_idx = self.instructions.index(inst.jump)
                except ValueError:
                    jump_idx = "?"

            # Format instruction
            inst_name = inst.ins_type.name.ljust(15)
            args_str = f"args={inst.args}" if inst.args else "no-args"
            jump_str = f" jump->#{jump_idx}" if jump_idx is not None else ""

            lines.append(f"  #{i:4d}: {inst_name} {args_str}{jump_str}")

        return "\n".join(lines)

    def print(self):
        for i, instruction in enumerate(self.instructions):
            if instruction.jump:
                jump_index = self.instructions.index(instruction.jump)
                print(f"{i}:\t{instruction.ins_type.name.ljust(8)}\t--> {jump_index}")
            else:
                print(f"{i}:\t{instruction.ins_type.name.ljust(8)} {instruction.args}")

    def add(
        self,
        instruction_type: NCSInstructionType,
        args: list[Any] | None = None,
        jump: NCSInstruction | None = None,
        index: int | None = None,
    ) -> NCSInstruction:
        """Adds an instruction to the program.

        Args:
        ----
            instruction_type: The type of instruction to add
            args: The arguments for the instruction
            jump: The jump target for this instruction
            index: The index to insert the instruction at.

        Returns:
        -------
            instruction: The added instruction

        Processing Logic:
        ----------------
            - Create a new NCSInstruction object from the parameters
            - Insert the instruction into the instructions list at the given index if provided
            - Otherwise append the instruction to the end of the list
            - Return the added instruction.
        """
        instruction = NCSInstruction(instruction_type, args, jump)
        if index is None:
            self.instructions.append(instruction)
        else:
            self.instructions.insert(index, instruction)
        return instruction

    def links_to(self, target: NCSInstruction) -> list[NCSInstruction]:
        """Get a list of all instructions which may jump to the target instructions."""
        return [inst for inst in self.instructions if inst.jump is target]

    def optimize(self, optimizers: list[NCSOptimizer]):
        """Optimize the model using the provided optimizers.

        Args:
        ----
            optimizers: List of optimizers to optimize the model

        Processing Logic:
        ----------------
            - Loop through each optimizer in the list
            - Call the optimize method on each optimizer passing the model
            - The optimizer will perform optimization on the model.
        """
        for optimizer in optimizers:
            optimizer.optimize(self)

    def merge(self, other: NCS):
        """Merge instructions from another NCS object into this one.

        Args:
        ----
            other: NCS object to merge instructions from.

        Processing Logic:
        ----------------
            - Extend self.instructions list with other.instructions list to combine instruction sets
            - Modifies instructions of the calling NCS object directly rather than returning new object
            - Other NCS object is not modified, only its instructions are copied over
            - Ensures all instructions from both NCS objects are now part of single combined set.
        """
        self.instructions.extend(other.instructions)

    def validate(self) -> list[str]:
        """Validate the NCS bytecode for common issues.

        Returns:
        -------
            list[str]: List of validation warnings/errors found
        """
        issues = []

        # Check for jumps to invalid targets
        for i, inst in enumerate(self.instructions):
            if inst.jump is not None and inst.jump not in self.instructions:
                issues.append(f"Instruction #{i} ({inst.ins_type.name}) jumps to instruction not in list")

        # Check for instructions that require jumps but don't have them
        jump_required = {
            NCSInstructionType.JMP,
            NCSInstructionType.JSR,
            NCSInstructionType.JZ,
            NCSInstructionType.JNZ,
        }
        for i, inst in enumerate(self.instructions):
            if inst.ins_type in jump_required and inst.jump is None:
                issues.append(f"Instruction #{i} ({inst.ins_type.name}) requires jump but has none")

        # Check for missing required arguments
        for i, inst in enumerate(self.instructions):
            expected_args = self._expected_arg_count(inst.ins_type)
            if expected_args is not None and len(inst.args) != expected_args:
                issues.append(
                    f"Instruction #{i} ({inst.ins_type.name}) has {len(inst.args)} args, expected {expected_args}"
                )

        return issues

    def get_instruction_at_index(self, index: int) -> NCSInstruction | None:
        """Get instruction at the specified index.

        Args:
        ----
            index: Instruction index

        Returns:
        -------
            NCSInstruction or None if index out of bounds
        """
        if 0 <= index < len(self.instructions):
            return self.instructions[index]
        return None

    def get_instruction_index(self, instruction: NCSInstruction) -> int:
        """Get the index of an instruction in the instruction list.

        Args:
        ----
            instruction: Instruction to find

        Returns:
        -------
            int: Index of instruction, or -1 if not found
        """
        try:
            return self.instructions.index(instruction)
        except ValueError:
            return -1

    def get_reachable_instructions(self) -> set[NCSInstruction]:
        """Get all instructions reachable from the entry point.

        Returns:
        -------
            set[NCSInstruction]: Set of reachable instructions
        """
        reachable: set[NCSInstruction] = set()
        if not self.instructions:
            return reachable

        # Start from first instruction (entry point)
        to_check = [self.instructions[0]]
        while to_check:
            inst = to_check.pop(0)
            if inst in reachable:
                continue
            reachable.add(inst)

            # Add next instruction
            inst_idx = self.get_instruction_index(inst)
            if inst_idx >= 0 and inst_idx + 1 < len(self.instructions):
                next_inst = self.instructions[inst_idx + 1]
                if next_inst not in reachable:
                    to_check.append(next_inst)

            # Add jump target if present
            if inst.jump and inst.jump not in reachable:
                to_check.append(inst.jump)

            # For conditional jumps, add fall-through
            if inst.ins_type in {NCSInstructionType.JZ, NCSInstructionType.JNZ}:
                inst_idx = self.get_instruction_index(inst)
                if inst_idx >= 0 and inst_idx + 1 < len(self.instructions):
                    next_inst = self.instructions[inst_idx + 1]
                    if next_inst not in reachable:
                        to_check.append(next_inst)

        return reachable

    def get_basic_blocks(self) -> list[list[NCSInstruction]]:
        """Partition instructions into basic blocks for decompilation.

        A basic block is a sequence of instructions with a single entry point
        and a single exit point (no jumps into the middle, no branches except at end).

        Returns:
        -------
            list[list[NCSInstruction]]: List of basic blocks
        """
        blocks: list[list[NCSInstruction]] = []
        if not self.instructions:
            return blocks

        current_block: list[NCSInstruction] = []
        jump_targets = {inst.jump for inst in self.instructions if inst.jump}

        for _i, inst in enumerate(self.instructions):
            # Start new block if this is a jump target
            if inst in jump_targets and current_block:
                blocks.append(current_block)
                current_block = [inst]
            else:
                current_block.append(inst)

            # End block if this instruction branches
            if inst.is_control_flow() and inst.ins_type != NCSInstructionType.JSR:
                blocks.append(current_block)
                current_block = []

        # Add final block
        if current_block:
            blocks.append(current_block)

        return blocks

    @staticmethod
    def _expected_arg_count(ins_type: NCSInstructionType) -> int | None:
        """Get expected argument count for instruction type, or None if variable/complex."""
        # Instructions with 2 args
        if ins_type in {NCSInstructionType.CPDOWNSP, NCSInstructionType.CPTOPSP,
                        NCSInstructionType.CPDOWNBP, NCSInstructionType.CPTOPBP,
                        NCSInstructionType.ACTION, NCSInstructionType.STORE_STATE}:
            return 2
        # Instructions with 1 arg
        if ins_type in {NCSInstructionType.CONSTI, NCSInstructionType.CONSTF,
                          NCSInstructionType.CONSTS, NCSInstructionType.CONSTO,
                          NCSInstructionType.MOVSP,
                          NCSInstructionType.DECxSP, NCSInstructionType.INCxSP,
                          NCSInstructionType.DECxBP, NCSInstructionType.INCxBP}:
            return 1
        # Instructions with 3 args
        if ins_type == NCSInstructionType.DESTRUCT:
            return 3
        # Most other instructions have 0 args
        if ins_type in {NCSInstructionType.RETN, NCSInstructionType.NOP,
                          NCSInstructionType.SAVEBP, NCSInstructionType.RESTOREBP,
                          NCSInstructionType.NOTI, NCSInstructionType.COMPI}:
            return 0
        # Complex/variable - return None
        return None


class NCSInstruction(ComparableMixin):
    """Represents a single NCS bytecode instruction.
    
    Each instruction consists of a bytecode opcode, a qualifier specifying operand types,
    optional arguments (offsets, constants, etc.), and an optional jump target for
    control flow instructions.
    
    References:
    ----------
        vendor/reone/include/reone/script/program.h - Instruction struct
        vendor/reone/src/libs/script/format/ncsreader.cpp:48-190 (instruction reading)
        vendor/xoreos/src/aurora/nwscript/ncsfile.h:131-177 (InstructionType enum)
        vendor/xoreos/src/aurora/nwscript/ncsfile.cpp:194-1649 (instruction execution)
        vendor/Kotor.NET/Kotor.NET/Formats/KotorNCS/NCS.cs:19-711 - NCSInstruction classes
        
    Attributes:
    ----------
        ins_type: Instruction type (opcode + qualifier combination)
            Reference: reone/ncsreader.cpp:50 (ins.type = R_INSTR_TYPE(byteCode, qualifier))
            Reference: xoreos/ncsfile.cpp:194-1649 (opcode dispatch table)
            Reference: Kotor.NET/NCS.cs:21-22 (Instruction and Qualifier properties)
            Combines bytecode opcode (e.g., ADDxx) with qualifier (e.g., INT_INT) to form complete instruction
            
        args: List of instruction arguments (offsets, constants, sizes, etc.)
            Reference: reone/ncsreader.cpp:57-105 (argument reading per instruction type)
            Reference: xoreos/ncsfile.cpp:194-1649 (argument handling in opcode handlers)
            Reference: Kotor.NET/NCS.cs:23 (Args property, varies by instruction type)
            Examples: CPDOWNSP has [offset, size], CONSTI has [int_value], ACTION has [routine_id, arg_count]
            
        jump: Optional jump target instruction for control flow (JMP, JSR, JZ, JNZ)
            Reference: reone/ncsreader.cpp:81-85 (jumpOffset reading for JMP/JSR/JZ/JNZ)
            Reference: xoreos/ncsfile.cpp:252-260 (jump instruction execution)
            Reference: Kotor.NET/NCS.cs:24 (JumpTo property, NCSInstruction?)
            Used by JMP (unconditional), JSR (subroutine call), JZ (jump if zero), JNZ (jump if not zero)
            Jump offset is stored as int32 in binary, converted to instruction reference in memory
            
        offset: Byte offset of instruction in NCS file (set during loading)
            Reference: reone/ncsreader.cpp:49 (ins.offset = static_cast<uint32_t>(offset))
            Reference: reone/ncsreader.cpp:185 (ins.nextOffset for following instruction)
            Used for jump target resolution and debugging
            Value -1 indicates offset not yet determined
    """

    COMPARABLE_FIELDS = ("ins_type", "args", "jump")

    def __init__(
        self,
        ins_type: NCSInstructionType = NCSInstructionType.NOP,
        args: list[Any] | None = None,
        jump: NCSInstruction | None = None,
    ):
        # vendor/reone/src/libs/script/format/ncsreader.cpp:50
        # vendor/xoreos/src/aurora/nwscript/ncsfile.cpp:194-1649
        # vendor/Kotor.NET/Kotor.NET/Formats/KotorNCS/NCS.cs:21-22
        # Instruction type (bytecode opcode + qualifier combination)
        self.ins_type: NCSInstructionType = ins_type
        
        # vendor/reone/src/libs/script/format/ncsreader.cpp:81-85
        # vendor/xoreos/src/aurora/nwscript/ncsfile.cpp:252-260
        # vendor/Kotor.NET/Kotor.NET/Formats/KotorNCS/NCS.cs:24
        # Optional jump target for control flow instructions (JMP, JSR, JZ, JNZ)
        self.jump: NCSInstruction | None = jump
        
        # vendor/reone/src/libs/script/format/ncsreader.cpp:57-105
        # vendor/xoreos/src/aurora/nwscript/ncsfile.cpp:194-1649
        # vendor/Kotor.NET/Kotor.NET/Formats/KotorNCS/NCS.cs:23
        # Instruction arguments (offsets, constants, sizes, etc., varies by instruction type)
        self.args: list[Any] = [] if args is None else args
        
        # vendor/reone/src/libs/script/format/ncsreader.cpp:49
        # Byte offset of instruction in NCS file (set during loading, -1 if not determined)
        self.offset: int = -1
        
        # Source line number for debugging (set during compilation, -1 if not tracked)
        # Used by debugger to map bytecode instructions back to source code lines
        self.line_number: int = -1

    def __str__(self):
        """Returns a human-readable string representation of the instruction."""
        args_str = f" args={self.args}" if self.args else ""
        jump_str = f" jump=<NCSInstruction#{id(self.jump)}>" if self.jump else ""
        return f"{self.ins_type.name}{args_str}{jump_str}"

    def __repr__(self):
        """Returns a detailed string representation avoiding circular references."""
        jump_repr = f"<jump#{id(self.jump)}>" if self.jump else "None"
        return f"NCSInstruction(type={self.ins_type.name}, args={self.args!r}, jump={jump_repr})"

    def __eq__(self, other):
        if not isinstance(other, NCSInstruction):
            return NotImplemented
        # Note: We compare jump by identity since it's a circular reference
        return (
            self.ins_type == other.ins_type
            and self.args == other.args
            and self.jump is other.jump
        )

    def __hash__(self):
        # Note: We use id() for jump since it's a circular reference
        return hash((self.ins_type, tuple(self.args), id(self.jump) if self.jump else None))

    def is_jump_instruction(self) -> bool:
        """Check if this instruction performs a jump/branch operation."""
        return self.ins_type in {
            NCSInstructionType.JMP,
            NCSInstructionType.JSR,
            NCSInstructionType.JZ,
            NCSInstructionType.JNZ,
        }

    def is_stack_operation(self) -> bool:
        """Check if this instruction operates on the stack."""
        return self.ins_type in {
            NCSInstructionType.CPDOWNSP,
            NCSInstructionType.CPTOPSP,
            NCSInstructionType.CPDOWNBP,
            NCSInstructionType.CPTOPBP,
            NCSInstructionType.MOVSP,
            NCSInstructionType.RSADDI,
            NCSInstructionType.RSADDF,
            NCSInstructionType.RSADDS,
            NCSInstructionType.RSADDO,
            NCSInstructionType.RSADDEFF,
            NCSInstructionType.RSADDEVT,
            NCSInstructionType.RSADDLOC,
            NCSInstructionType.RSADDTAL,
        }

    def is_constant(self) -> bool:
        """Check if this instruction loads a constant value."""
        return self.ins_type in {
            NCSInstructionType.CONSTI,
            NCSInstructionType.CONSTF,
            NCSInstructionType.CONSTS,
            NCSInstructionType.CONSTO,
        }

    def is_arithmetic(self) -> bool:
        """Check if this instruction performs arithmetic operations."""
        return self.ins_type in {
            NCSInstructionType.ADDII, NCSInstructionType.ADDIF, NCSInstructionType.ADDFI, NCSInstructionType.ADDFF,
            NCSInstructionType.ADDSS, NCSInstructionType.ADDVV,
            NCSInstructionType.SUBII, NCSInstructionType.SUBIF, NCSInstructionType.SUBFI, NCSInstructionType.SUBFF,
            NCSInstructionType.SUBVV,
            NCSInstructionType.MULII, NCSInstructionType.MULIF, NCSInstructionType.MULFI, NCSInstructionType.MULFF,
            NCSInstructionType.MULVF, NCSInstructionType.MULFV,
            NCSInstructionType.DIVII, NCSInstructionType.DIVIF, NCSInstructionType.DIVFI, NCSInstructionType.DIVFF,
            NCSInstructionType.DIVVF, NCSInstructionType.DIVFV,
            NCSInstructionType.MODII,
            NCSInstructionType.NEGI, NCSInstructionType.NEGF,
        }

    def is_comparison(self) -> bool:
        """Check if this instruction performs comparison operations."""
        return self.ins_type in {
            NCSInstructionType.EQUALII, NCSInstructionType.EQUALFF, NCSInstructionType.EQUALSS,
            NCSInstructionType.EQUALOO, NCSInstructionType.EQUALTT,
            NCSInstructionType.NEQUALII, NCSInstructionType.NEQUALFF, NCSInstructionType.NEQUALSS,
            NCSInstructionType.NEQUALOO, NCSInstructionType.NEQUALTT,
            NCSInstructionType.GTII, NCSInstructionType.GTFF,
            NCSInstructionType.GEQII, NCSInstructionType.GEQFF,
            NCSInstructionType.LTII, NCSInstructionType.LTFF,
            NCSInstructionType.LEQII, NCSInstructionType.LEQFF,
        }

    def is_logical(self) -> bool:
        """Check if this instruction performs logical operations."""
        return self.ins_type in {
            NCSInstructionType.LOGANDII,
            NCSInstructionType.LOGORII,
            NCSInstructionType.NOTI,
        }

    def is_bitwise(self) -> bool:
        """Check if this instruction performs bitwise operations."""
        return self.ins_type in {
            NCSInstructionType.BOOLANDII,
            NCSInstructionType.INCORII,
            NCSInstructionType.EXCORII,
            NCSInstructionType.COMPI,
            NCSInstructionType.SHLEFTII,
            NCSInstructionType.SHRIGHTII,
            NCSInstructionType.USHRIGHTII,
        }

    def is_control_flow(self) -> bool:
        """Check if this instruction affects control flow.

        Returns:
        -------
            bool: True if instruction affects program flow
        """
        return self.ins_type in {
            NCSInstructionType.JMP,
            NCSInstructionType.JSR,
            NCSInstructionType.JZ,
            NCSInstructionType.JNZ,
            NCSInstructionType.RETN,
        }

    def is_function_call(self) -> bool:
        """Check if this instruction calls a function.

        Returns:
        -------
            bool: True if instruction is a function call
        """
        return self.ins_type == NCSInstructionType.ACTION

    def get_operand_count(self) -> int:
        """Get the number of operands this instruction consumes from stack.

        Returns:
        -------
            int: Number of stack operands consumed (0, 1, or 2)
        """
        # Binary operations consume 2 operands
        if self.is_arithmetic() or self.is_comparison() or self.is_logical():
            if self.ins_type in {NCSInstructionType.NEGI, NCSInstructionType.NEGF, NCSInstructionType.NOTI, NCSInstructionType.COMPI}:
                return 1
            return 2
        # Unary operations consume 1 operand
        if self.ins_type in {NCSInstructionType.NEGI, NCSInstructionType.NEGF, NCSInstructionType.NOTI, NCSInstructionType.COMPI}:
            return 1
        # Constants produce 1 operand
        if self.is_constant():
            return 0  # Produces, doesn't consume
        # Function calls consume arguments (count in args)
        if self.is_function_call():
            return self.args[1] if len(self.args) >= 2 else 0
        return 0

    def get_result_count(self) -> int:
        """Get the number of results this instruction produces on stack.

        Returns:
        -------
            int: Number of stack results produced (typically 0 or 1)
        """
        # Most operations produce 1 result
        if self.is_arithmetic() or self.is_comparison() or self.is_logical():
            return 1
        if self.is_constant():
            return 1
        if self.is_function_call():
            return 1  # Functions return a value (void functions return 0)
        # Control flow doesn't produce results
        if self.is_control_flow():
            return 0
        # Stack operations may produce results depending on context
        if self.is_stack_operation():
            return 0  # Stack operations modify stack but don't produce values
        return 0


class NCSOptimizer(ABC):
    def __init__(self):
        self.instructions_cleared: int = 0

    @abstractmethod
    def optimize(self, ncs: NCS): ...

    def reset(self):
        """Reset stats counter."""
        self.instructions_cleared = 0


class NCSCompiler(ABC):
    @abstractmethod
    def compile_script(self, source_path: os.PathLike | str, output_path: os.PathLike | str, game: Game, optimizers: list[NCSOptimizer] | None = None, *, debug: bool = False):
        ...
