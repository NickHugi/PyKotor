from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum, IntEnum
import os
from typing import TYPE_CHECKING, Any, NamedTuple

if TYPE_CHECKING:
    import os

    from pykotor.common.misc import Game


class NCSInstructionTypeValue(NamedTuple):
    byte_code: int
    qualifier: int


class NCSByteCode(IntEnum):
    NOP = 0x2D
    CPDOWNSP = 0x01
    RSADDx = 0x02
    CPTOPSP = 0x03
    CONSTx = 0x04
    ACTION = 0x05
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


class NCS:
    def __init__(self):
        self.instructions: list[NCSInstruction] = []

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
        self.instructions.insert(
            index,
            instruction,
        ) if index is not None else self.instructions.append(instruction)
        return instruction

    def links_to(self, target: NCSInstruction) -> list[NCSInstruction]:
        """Get a list of all instructions which may jump to the target instructions."""
        return [
            inst
            for inst in self.instructions
            if inst.jump is target
        ]

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


class NCSInstruction:
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

    def __init__(
        self,
        ins_type: NCSInstructionType = NCSInstructionType.NOP,
        args: list[Any] | None = None,
        jump: NCSInstruction | None = None,
    ):
        self.ins_type: NCSInstructionType = ins_type
        self.jump: NCSInstruction | None = jump
        self.args: list[Any] = args if args is not None else []

    def __str__(self):
        if self.jump is None:
            return f"Instruction: {self.ins_type.name} {self.args}"
        return f"Instruction: {self.ins_type.name} jump to '{self.jump}'"

    def __repr__(self):
        return f"NCSInstruction({self.ins_type}, {self.jump}, {self.args})"


class NCSOptimizer(ABC):
    def __init__(self):
        self.instructions_cleared: int = 0

    @abstractmethod
    def optimize(self, ncs: NCS):
        ...

    def reset(self):
        """Reset stats counter."""
        self.instructions_cleared = 0


class NCSCompiler(ABC):
    @abstractmethod
    def compile_script(self, source_filepath: os.PathLike | str, output_filepath: os.PathLike | str, game: Game, *, debug: bool):
        ...
