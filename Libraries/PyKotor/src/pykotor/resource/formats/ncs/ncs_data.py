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
    DECISP = NCSInstructionTypeValue(NCSByteCode.DECxSP, NCSInstructionQualifier.Int)
    INCISP = NCSInstructionTypeValue(NCSByteCode.INCxSP, NCSInstructionQualifier.Int)
    JNZ = NCSInstructionTypeValue(NCSByteCode.JNZ, 0x00)
    CPDOWNBP = NCSInstructionTypeValue(NCSByteCode.CPDOWNBP, 0x01)
    CPTOPBP = NCSInstructionTypeValue(NCSByteCode.CPTOPBP, 0x01)
    DECIBP = NCSInstructionTypeValue(NCSByteCode.DECxBP, NCSInstructionQualifier.Int)
    INCIBP = NCSInstructionTypeValue(NCSByteCode.INCxBP, NCSInstructionQualifier.Int)
    SAVEBP = NCSInstructionTypeValue(NCSByteCode.SAVEBP, 0x00)
    RESTOREBP = NCSInstructionTypeValue(NCSByteCode.RESTOREBP, 0x00)
    STORE_STATE = NCSInstructionTypeValue(NCSByteCode.STORE_STATE, 0x10)
    NOP2 = NCSInstructionTypeValue(NCSByteCode.NOP2, 0x00)


class NCS(ComparableMixin):
    COMPARABLE_SEQUENCE_FIELDS = ("instructions",)

    def __init__(self):
        self.instructions: list[NCSInstruction] = []

    def __eq__(self, other):
        if not isinstance(other, NCS):
            return NotImplemented
        return self.instructions == other.instructions

    def __hash__(self):
        return hash(tuple(self.instructions))

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
                          NCSInstructionType.DECISP, NCSInstructionType.INCISP,
                          NCSInstructionType.DECIBP, NCSInstructionType.INCIBP}:
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
    """Initialize a NCS instruction object.

    Args:
    ----
        ins_type: NCS instruction type
        args: List of arguments
        jump: Jump target instruction

    Initializes a NCS instruction object with provided attributes:
        - Sets instruction type
        - Sets jump target if provided
        - Sets args list if provided.
    """

    COMPARABLE_FIELDS = ("ins_type", "args", "jump")

    def __init__(
        self,
        ins_type: NCSInstructionType = NCSInstructionType.NOP,
        args: list[Any] | None = None,
        jump: NCSInstruction | None = None,
    ):
        self.ins_type: NCSInstructionType = ins_type
        self.jump: NCSInstruction | None = jump
        self.args: list[Any] = [] if args is None else args

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
