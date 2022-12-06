from __future__ import annotations

from enum import IntEnum, Enum
from typing import NamedTuple, Optional, List


class NCSInstructionTypeValue(NamedTuple):
    byte_code: int
    qualifier: int


class NCSByteCode(IntEnum):
    NOP = 0
    CPDOWNSP = 0x01
    RSADDx = 0x02
    CPTOPSP = 0x03
    CONSTx = 0x04
    ACTION = 0x05
    LOGANDxx = 0x06
    LOGORxx = 0x07
    INCORxx = 0x08
    EXCORxx = 0x09
    BOOLANDxx = 0x0a
    EQUALxx = 0x0b
    NEQUALxx = 0x0c
    GEQxx = 0x0d
    GTxx = 0x0e
    LTxx = 0x0f
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
    COMPx = 0x1a
    MOVSP = 0x1b
    JMP = 0x1d
    JSR = 0x1e
    JZ = 0x1f
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
    SAVEBP = 0x2a
    RESTOREBP = 0x2b
    STORE_STATE = 0x2c
    NOP2 = 0x2d


class NCSInstructionQualifier(IntEnum):
    #NoQualifier = 0x00
    #Stack = 0x01
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
    VectorVector = 0x3a
    VectorFloat = 0x3b
    FloatVector = 0x3c


class NCSInstructionType(Enum):
    NOP = NCSInstructionTypeValue(NCSByteCode.NOP, 0x00)  # 0x0c)
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
        self.instructions: List[NCSInstruction] = []

    def print(self):
        for i, instruction in enumerate(self.instructions):
            if instruction.jump:
                jump_index = self.instructions.index(instruction.jump)
                print("{}:\t{}\t--> {}".format(i, instruction.ins_type.name.ljust(8), jump_index))
            else:
                print("{}:\t{} {}".format(i, instruction.ins_type.name.ljust(8), instruction.args))

    def add(self, instruction_type: NCSInstructionType, args=None, jump=None) -> NCSInstruction:
        instruction = NCSInstruction(instruction_type, args, jump)
        self.instructions.append(instruction)
        return instruction


class NCSInstruction:
    def __init__(self, ins_type: NCSInstructionType = NCSInstructionType.NOP, args: List = None, jump: Optional[NCSInstruction] = None):
        self.ins_type: NCSInstructionType = ins_type
        self.jump: Optional[NCSInstruction] = jump
        self.args: List = args if args is not None else []

    def __str__(self):
        if self.jump is None:
            return "Instruction: {} {}".format(self.ins_type.name, self.args)
        else:
            return "Instruction: {} jump to '{}'".format(self.ins_type.name, self.jump)

    def __repr__(self):
        return "NCSInstruction({}, {}, {})".format(self.ins_type, self.jump, self.args)
